import logging
import threading
from collections.abc import Callable

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)

CANARY_TIMEOUT_SECONDS = 2.0

# (url) -> None. Fires the Canarytoken; replaced in tests (no network).
CanaryTrigger = Callable[[str], None]


def _call_canary(url: str) -> None:
    try:
        httpx.get(url, timeout=CANARY_TIMEOUT_SECONDS)
    except Exception:  # noqa: BLE001 - an alert failure must never affect the login response
        logger.warning("Canarytoken request failed")


def trigger_canary_in_background(url: str) -> None:
    """Calls the Canarytoken URL in a daemon thread; the caller never waits or sees errors."""
    threading.Thread(target=_call_canary, args=(url,), daemon=True).start()


def is_trap_login(settings: Settings, login: str) -> bool:
    return bool(settings.canary_trap_login) and login == settings.canary_trap_login


def fire_trap(settings: Settings, trigger: CanaryTrigger) -> None:
    """Handles an attempt on the trap account.

    With a non-empty CANARY_TRAP_URL the trigger is invoked; with an empty URL no HTTP
    call is made and the attempt is only logged. Errors from the trigger are swallowed.
    """
    url = settings.canary_trap_url.strip()
    if not url:
        logger.info("Login attempt on trap account (CANARY_TRAP_URL empty, no alert sent)")
        return
    logger.warning("Login attempt on trap account, firing Canarytoken")
    try:
        trigger(url)
    except Exception:  # noqa: BLE001
        logger.warning("Canarytoken trigger failed")
