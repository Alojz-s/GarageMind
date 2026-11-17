import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_canary_trigger, get_turnstile_verifier
from app.core.config import get_settings
from app.main import app
from app.models import User
from app.services.passwords import verify_password
from scripts.seed import seed
from tests.conftest import ADMIN_PASSWORD, LOGIN_FAILED, PASSWORD

pytestmark = pytest.mark.db

LOGIN_URL = "/api/auth/login"
TRAP_LOGIN = "honey_user"
TRAP_URL = "https://canary.example/trap"


def _configure(url: str = TRAP_URL, captcha: bool = False) -> None:
    app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={
            "captcha_enabled": captcha,
            "canary_trap_login": TRAP_LOGIN,
            "canary_trap_url": url,
        }
    )


@pytest.fixture
def calls(client: TestClient) -> list[str]:
    recorded: list[str] = []
    _configure()
    app.dependency_overrides[get_canary_trigger] = lambda: recorded.append
    return recorded


def _login(client: TestClient, login: str, password: str = "whatever-password-123") -> object:
    return client.post(LOGIN_URL, json={"login": login, "password": password})


def test_trap_login_returns_generic_401(client: TestClient, calls: list[str]) -> None:
    response = _login(client, TRAP_LOGIN)

    assert response.status_code == 401
    assert response.json() == LOGIN_FAILED


def test_trap_login_fires_trigger_once(client: TestClient, calls: list[str]) -> None:
    _login(client, TRAP_LOGIN)

    assert calls == [TRAP_URL]


def test_non_trap_login_does_not_fire(client: TestClient, calls: list[str]) -> None:
    assert _login(client, "redaktor", PASSWORD).status_code == 200
    assert _login(client, "nobody").status_code == 401

    assert calls == []


def test_empty_url_does_not_fire(
    client: TestClient, calls: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    _configure(url="")

    with caplog.at_level(logging.INFO, logger="app.services.canary_trap"):
        response = _login(client, TRAP_LOGIN)

    assert response.status_code == 401
    assert response.json() == LOGIN_FAILED
    assert calls == []
    assert "no alert sent" in caplog.text


def test_trigger_failure_is_swallowed(client: TestClient, calls: list[str]) -> None:
    def failing(url: str) -> None:
        raise RuntimeError("network down")

    app.dependency_overrides[get_canary_trigger] = lambda: failing

    response = _login(client, TRAP_LOGIN)

    assert response.status_code == 401
    assert response.json() == LOGIN_FAILED


def test_trap_works_with_captcha_off(client: TestClient, calls: list[str]) -> None:
    _configure(captcha=False)

    assert _login(client, TRAP_LOGIN).status_code == 401
    assert calls == [TRAP_URL]


def test_trap_runs_after_captcha(client: TestClient, calls: list[str]) -> None:
    _configure(captcha=True)
    app.dependency_overrides[get_turnstile_verifier] = lambda: lambda token, ip: False

    response = _login(client, TRAP_LOGIN)

    assert response.status_code == 400
    assert response.json()["code"] == "captcha_failed"
    assert calls == []


def test_trap_does_not_touch_failed_login_counter(
    client: TestClient, db_session: Session, calls: list[str]
) -> None:
    default_trap = get_settings().canary_trap_login
    _configure()
    app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={
            "captcha_enabled": False,
            "canary_trap_login": default_trap,
            "canary_trap_url": TRAP_URL,
        }
    )

    for _ in range(10):
        assert _login(client, default_trap).status_code == 401

    user = db_session.scalars(select(User).where(User.login == default_trap)).one()
    assert user.failed_login_count == 0
    assert user.locked_until is None
    assert calls == [TRAP_URL] * 10


def test_seed_creates_trap_user_idempotently(db_session: Session) -> None:
    login = get_settings().canary_trap_login

    seed(db_session, ADMIN_PASSWORD, PASSWORD)
    first = db_session.scalars(select(User).where(User.login == login)).one()
    first_hash = first.password_hash
    seed(db_session, ADMIN_PASSWORD, PASSWORD)
    second = db_session.scalars(select(User).where(User.login == login)).one()

    assert second.role.name == "Czytelnik"
    assert second.password_hash == first_hash
    assert first_hash is not None
    assert not verify_password(PASSWORD, first_hash)
