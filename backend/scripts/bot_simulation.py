"""Symulacja bota przeciw własnej, lokalnej instancji GarageMind (przez HTTP).

Wysyła zautomatyzowane próby na POST /api/auth/login i wypisuje tabelę z zabezpieczeniami,
które zadziałały. Wymaga uruchomionego backendu ze zmigrowaną i zaseedowaną bazą.

Uruchamianie: cd backend && python scripts/bot_simulation.py [--base-url URL] [--scenario NAZWA]

- Wiersz captcha_missing wymaga CAPTCHA_ENABLED=true; inaczej jest SKIPPED. Pozostałe scenariusze
  wysyłają --captcha-token (domyślnie token testowy Turnstile); jeśli serwer go odrzuci, są
  SKIPPED, bo bota zatrzymała już CAPTCHA.
- brute_force blokuje konto docelowe na 15 minut, a password_spraying wyczerpuje limit IP.
  Lokalnie wszyscy klienci mają IP 127.0.0.1, więc ponowne uruchomienie w oknie limitu może dać
  NO dla wcześniejszych scenariuszy (429).
- Alert Canarytokens dla konta-pułapki sprawdza się ręcznie na canarytokens.org.
- Kod wyjścia: 0 gdy każdy wykonany scenariusz zadziałał, 1 w przeciwnym razie, 2 przy błędzie
  połączenia lub argumentów. Hosty inne niż lokalne wymagają --allow-remote.
"""

import argparse
import os
import sys
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
GENERIC_DETAIL = "Incorrect username or password"


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

    def login(
        self, login: str, password: str, with_captcha: bool = True, **extra: object
    ) -> tuple[int, dict]:
        payload: dict[str, object] = {"login": login, "password": password, **extra}
        if with_captcha and self.captcha_enabled and self.args.captcha_token:
            payload["captcha_token"] = self.args.captcha_token
        response = self.client.post("/api/auth/login", json=payload)
        try:
            body = response.json()
        except ValueError:
            body = {}
        return response.status_code, body if isinstance(body, dict) else {}


def _code(body: dict) -> str:
    return str(body.get("code") or "-")


def _yn(ok: bool) -> str:
    return "YES" if ok else "NO"


def captcha_missing(bot: Bot) -> Result:
    protection, expected = "CAPTCHA (Turnstile)", "400 captcha_failed"
    if not bot.captcha_enabled:
        return Result(
            "captcha_missing",
            protection,
            expected,
            "-",
            "-",
            "SKIPPED",
            "CAPTCHA disabled (set CAPTCHA_ENABLED=true)",
        )
    status, body = bot.login(bot.args.target_user, bot.args.wrong_password, with_captcha=False)
    ok = status == 400 and body.get("code") == "captcha_failed"
    return Result("captcha_missing", protection, expected, str(status), _code(body), _yn(ok))


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
        "trap_account",
        "Canary trap account",
        "401 generic failure",
        str(status),
        _code(body),
        _yn(ok),
        "Check canarytokens.org for the alert if CANARY_TRAP_URL is set",
    )


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
        help="Token sent in non-CAPTCHA scenarios (default: Turnstile test-key dummy token)",
    )
    p.add_argument("--lockout-attempts", type=int, default=6, help="Max brute force attempts")
    p.add_argument("--ip-limit-attempts", type=int, default=40, help="Max spraying attempts")
    p.add_argument("--scenario", choices=RUNNERS, help="Run a single scenario")
    p.add_argument("--allow-remote", action="store_true", help="Allow non-local hosts")
    return p.parse_args()


def main() -> int:
    # Na Windowsie wyjście do potoku (np. Git Bash) domyślnie używa cp1250 zamiast UTF-8.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    args = parse_args()

    host = urlparse(args.base_url).hostname or ""
    if host not in LOCAL_HOSTS and not args.allow_remote:
        print(f"Refusing to target non-local host '{host}' (use --allow-remote).")
        return 2

    print("Note: behind Vite/localhost all clients share IP 127.0.0.1, so the IP limit is global.")
    try:
        with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=10) as client:
            config = client.get("/api/auth/captcha-config").json()
            bot = Bot(client, args, bool(config.get("enabled")))
            print(f"Target: {args.base_url} | CAPTCHA enabled: {bot.captcha_enabled}")
            results = []
            for name in [args.scenario] if args.scenario else RUNNERS:
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
