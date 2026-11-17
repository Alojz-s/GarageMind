"""Bot simulation against your OWN local GarageMind instance (HTTP only, no TestClient).

Runs automated-attack scenarios against POST /api/auth/login and prints a table showing
which protections worked.

Usage (backend and DB running, migrated and seeded):
    cd backend && python scripts/bot_simulation.py [--base-url URL] [--scenario NAME]

Scenarios (default order): captcha_missing, honeypot, trap_account, brute_force,
password_spraying. Run one with --scenario, e.g. for report screenshots.

Notes:
- CAPTCHA_ENABLED=true must be set in .env (and uvicorn restarted) for the captcha_missing
  row; otherwise it is SKIPPED. With CAPTCHA enabled the other scenarios send --captcha-token
  (default: dummy token accepted only by Turnstile's public test secret key); if the server
  rejects it, those rows are SKIPPED (CAPTCHA stopped the bot first).
- The brute force scenario locks the target account for 15 minutes; the spraying scenario
  fills the per-IP limit window (IP_LOGIN_WINDOW_MINUTES). Behind Vite/localhost all clients
  share the IP 127.0.0.1, so the IP limit is effectively global. Re-runs within the window
  may report NO for earlier scenarios because the IP is already limited (429).
- Trap login defaults to env CANARY_TRAP_LOGIN or "svc_backup". If CANARY_TRAP_URL is set
  on the server, the Canarytoken alert is verified manually on canarytokens.org.
- Exit code: 0 if every non-skipped scenario worked, 1 otherwise, 2 on usage/connection error.

Only run this against an application you own. Remote hosts are refused unless --allow-remote.
"""

import argparse
import os
import sys
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
GENERIC_DETAIL = "Incorrect username or password"
SCENARIOS = ["captcha_missing", "honeypot", "trap_account", "brute_force", "password_spraying"]


@dataclass
class Result:
    scenario: str
    protection: str
    expected: str
    status: str
    code: str
    worked: str  # YES / NO / SKIPPED
    note: str = ""


class Bot:
    def __init__(self, client: httpx.Client, args: argparse.Namespace, captcha_enabled: bool):
        self.client = client
        self.args = args
        self.captcha_enabled = captcha_enabled

    def login(self, login: str, password: str, **extra: object) -> tuple[int, dict]:
        payload: dict[str, object] = {"login": login, "password": password, **extra}
        if self.captcha_enabled and self.args.captcha_token and "captcha_token" not in payload:
            payload["captcha_token"] = self.args.captcha_token
        response = self.client.post("/api/auth/login", json=payload)
        try:
            body = response.json()
        except ValueError:
            body = {}
        return response.status_code, body if isinstance(body, dict) else {}


def _code(body: dict) -> str:
    return str(body.get("code") or "-")


def captcha_missing(bot: Bot) -> Result:
    protection, expected = "CAPTCHA (Turnstile)", "400 captcha_failed"
    if not bot.captcha_enabled:
        return Result(
            "captcha_missing", protection, expected, "-", "-", "SKIPPED",
            "CAPTCHA disabled (set CAPTCHA_ENABLED=true)",
        )  # fmt: skip
    status, body = _send_without_token(bot)
    ok = status == 400 and body.get("code") == "captcha_failed"
    return Result("captcha_missing", protection, expected, str(status), _code(body), _yn(ok))


def _send_without_token(bot: Bot) -> tuple[int, dict]:
    response = bot.client.post(
        "/api/auth/login", json={"login": bot.args.target_user, "password": bot.args.wrong_password}
    )
    try:
        return response.status_code, response.json()
    except ValueError:
        return response.status_code, {}


def honeypot(bot: Bot) -> Result:
    status, body = bot.login(
        bot.args.target_user, bot.args.wrong_password, website="https://spam.example"
    )
    ok = status == 401 and body.get("detail") == GENERIC_DETAIL
    return Result(
        "honeypot", "Honeypot field", "401 generic failure", str(status), _code(body), _yn(ok)
    )


def trap_account(bot: Bot) -> Result:
    status, body = bot.login(bot.args.trap_login, bot.args.wrong_password)
    ok = status == 401 and body.get("detail") == GENERIC_DETAIL
    return Result(
        "trap_account", "Canary trap account", "401 generic failure", str(status), _code(body),
        _yn(ok), "Check canarytokens.org for the alert if CANARY_TRAP_URL is set",
    )  # fmt: skip


def brute_force(bot: Bot) -> Result:
    protection, expected = "Account lockout", "401 ... then 423 account_locked"
    last: tuple[int, dict] = (0, {})
    for _ in range(bot.args.lockout_attempts):
        last = bot.login(bot.args.target_user, bot.args.wrong_password)
        if last[0] != 401:
            break
    status, body = last
    ok = status == 423 and body.get("code") == "account_locked" and "locked_seconds" in body
    note = f"locked_seconds={body['locked_seconds']}" if ok else ""
    return Result("brute_force", protection, expected, str(status), _code(body), _yn(ok), note)


def password_spraying(bot: Bot) -> Result:
    protection, expected = "Per-IP limit", "429 too_many_attempts"
    names = ["redaktor", "czytelnik"] + [f"user{i}" for i in range(1, bot.args.ip_limit_attempts)]
    last: tuple[int, dict] = (0, {})
    for name in names[: bot.args.ip_limit_attempts]:
        last = bot.login(name, bot.args.wrong_password)
        if last[0] == 429:
            break
    status, body = last
    ok = status == 429 and body.get("code") == "too_many_attempts"
    return Result("password_spraying", protection, expected, str(status), _code(body), _yn(ok))


def _yn(ok: bool) -> str:
    return "YES" if ok else "NO"


RUNNERS = {
    "captcha_missing": captcha_missing,
    "honeypot": honeypot,
    "trap_account": trap_account,
    "brute_force": brute_force,
    "password_spraying": password_spraying,
}


def _skip_if_captcha_blocked(result: Result) -> Result:
    if result.scenario != "captcha_missing" and result.code == "captcha_failed":
        result.worked = "SKIPPED"
        result.note = (
            "Blocked by CAPTCHA first; pass a valid --captcha-token or set CAPTCHA_ENABLED=false"
        )
    return result


def print_table(results: list[Result]) -> None:
    headers = ["Scenario", "Protection", "Expected", "HTTP status", "Response code", "Worked"]
    rows = [[r.scenario, r.protection, r.expected, r.status, r.code, r.worked] for r in results]
    widths = [max(len(row[i]) for row in [headers, *rows]) for i in range(len(headers))]
    line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def fmt(row: list[str]) -> str:
        return "| " + " | ".join(cell.ljust(w) for cell, w in zip(row, widths, strict=True)) + " |"

    print(line)
    print(fmt(headers))
    print(line)
    for row in rows:
        print(fmt(row))
    print(line)
    ran = [r for r in results if r.worked != "SKIPPED"]
    worked = sum(r.worked == "YES" for r in ran)
    print(f"Protections that worked: {worked}/{len(ran)} ({len(results) - len(ran)} skipped)")
    for r in results:
        if r.note:
            print(f"  [{r.scenario}] {r.note}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Bot simulation against your own GarageMind instance.")
    p.add_argument("--base-url", default="http://127.0.0.1:8000")
    p.add_argument("--target-user", default="redaktor", help="Account for brute force/honeypot")
    p.add_argument("--trap-login", default=os.environ.get("CANARY_TRAP_LOGIN", "svc_backup"))
    p.add_argument("--wrong-password", default="definitely-wrong-password-123")
    p.add_argument(
        "--captcha-token",
        default=os.environ.get("BOT_CAPTCHA_TOKEN", "XXXX.DUMMY.TOKEN.XXXX"),
        help="Token sent in non-CAPTCHA scenarios (default is Turnstile's test-key dummy token)",
    )
    p.add_argument("--lockout-attempts", type=int, default=6, help="Max brute force attempts")
    p.add_argument("--ip-limit-attempts", type=int, default=40, help="Max spraying attempts")
    p.add_argument("--scenario", choices=SCENARIOS, help="Run a single scenario")
    p.add_argument(
        "--allow-remote",
        action="store_true",
        help="DANGEROUS: permit non-local hosts. Only use on systems you own; discouraged.",
    )
    return p.parse_args()


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    args = parse_args()

    host = urlparse(args.base_url).hostname or ""
    if host not in LOCAL_HOSTS and not args.allow_remote:
        print(f"Refusing to target non-local host '{host}' (use --allow-remote at own risk).")
        return 2

    print("Note: behind Vite/localhost all clients share IP 127.0.0.1, so the IP limit is global.")
    try:
        with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=10) as client:
            config = client.get("/api/auth/captcha-config").json()
            bot = Bot(client, args, bool(config.get("enabled")))
            print(f"Target: {args.base_url} | CAPTCHA enabled: {bot.captcha_enabled}")
            names = [args.scenario] if args.scenario else SCENARIOS
            results = []
            for name in names:
                print(f"Running scenario: {name}")
                results.append(_skip_if_captcha_blocked(RUNNERS[name](bot)))
    except httpx.HTTPError as exc:
        print(f"Cannot reach the application at {args.base_url}: {exc}")
        return 2

    print()
    print_table(results)
    return 0 if all(r.worked != "NO" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
