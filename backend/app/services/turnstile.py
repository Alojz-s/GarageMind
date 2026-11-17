from collections.abc import Callable

import httpx

from app.core.config import Settings

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
SITEVERIFY_TIMEOUT_SECONDS = 5.0

# (token, remote_ip) -> czy token jest poprawny. Podmieniane w testach.
TurnstileVerifier = Callable[[str, str | None], bool]


def verify_turnstile_token(settings: Settings, token: str, remote_ip: str | None = None) -> bool:
    """Weryfikuje token przez siteverify. Błąd sieci lub odpowiedzi = odrzucenie."""
    data = {"secret": settings.turnstile_secret_key.get_secret_value(), "response": token}
    if remote_ip:
        data["remoteip"] = remote_ip
    try:
        response = httpx.post(SITEVERIFY_URL, data=data, timeout=SITEVERIFY_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json().get("success") is True
    except httpx.HTTPError, ValueError:
        return False


def check_captcha(
    settings: Settings,
    verifier: TurnstileVerifier,
    token: str | None,
    remote_ip: str | None,
) -> bool:
    """Gdy CAPTCHA wyłączona – zawsze true, bez sieci i bez wymagania tokenu."""
    if not settings.captcha_enabled:
        return True
    if not token:
        return False
    return verifier(token, remote_ip)
