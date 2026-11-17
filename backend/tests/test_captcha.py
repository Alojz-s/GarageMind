from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_turnstile_verifier
from app.core.config import Settings, get_settings
from app.main import app
from app.models import User
from tests.conftest import LOGIN_FAILED, NEW_PASSWORD, PASSWORD

pytestmark = pytest.mark.db

LOGIN_URL = "/api/auth/login"


@pytest.fixture
def captcha_on(client: TestClient) -> Iterator[list[tuple[str, str | None]]]:
    """Włącza CAPTCHA; weryfikator akceptuje tylko token "good" i zapisuje wywołania."""
    calls: list[tuple[str, str | None]] = []

    def verifier(token: str, remote_ip: str | None) -> bool:
        calls.append((token, remote_ip))
        return token == "good"

    app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={"captcha_enabled": True}
    )
    app.dependency_overrides[get_turnstile_verifier] = lambda: verifier
    yield calls


def _login(client: TestClient, **extra: object) -> object:
    payload = {"login": "redaktor", "password": PASSWORD, **extra}
    return client.post(LOGIN_URL, json=payload)


def test_captcha_config_disabled(client: TestClient) -> None:
    response = client.get("/api/auth/captcha-config")

    assert response.status_code == 200
    assert response.json() == {"enabled": False, "site_key": None}


def test_captcha_config_enabled(client: TestClient, captcha_on: list) -> None:
    body = client.get("/api/auth/captcha-config").json()

    assert body["enabled"] is True
    assert body["site_key"] == Settings.model_fields["turnstile_site_key"].default


def test_login_without_token_rejected(client: TestClient, captcha_on: list) -> None:
    response = _login(client)

    assert response.status_code == 400
    assert response.json()["code"] == "captcha_failed"
    assert captcha_on == []


def test_login_with_rejected_token(client: TestClient, captcha_on: list) -> None:
    response = _login(client, captcha_token="bad")

    assert response.status_code == 400
    assert response.json()["code"] == "captcha_failed"


def test_login_with_valid_token(client: TestClient, captcha_on: list) -> None:
    response = _login(client, captcha_token="good")

    assert response.status_code == 200
    assert captcha_on == [("good", "testclient")]


def test_honeypot_returns_generic_failure(client: TestClient, captcha_on: list) -> None:
    response = _login(client, website="http://spam.example")

    assert response.status_code == 401
    assert response.json() == LOGIN_FAILED
    assert captcha_on == []


def test_honeypot_with_captcha_disabled(client: TestClient) -> None:
    response = _login(client, website="x")

    assert response.status_code == 401
    assert response.json() == LOGIN_FAILED


def test_whitespace_only_honeypot_is_treated_as_empty(client: TestClient) -> None:
    assert _login(client, website="   ").status_code == 200


def test_login_without_captcha_when_disabled(client: TestClient) -> None:
    assert _login(client).status_code == 200


def test_lockout_still_works_with_valid_captcha(
    client: TestClient, db_session: Session, captcha_on: list
) -> None:
    for _ in range(5):
        _login(client, password="zle-haslo-ale-wystarczajaco-dlugie", captcha_token="good")

    response = _login(client, captcha_token="good")

    assert response.status_code == 423
    assert response.json()["code"] == "account_locked"
    assert db_session.scalars(select(User).where(User.login == "redaktor")).one().locked_until


def _change(client: TestClient, **extra: object) -> object:
    return client.post(
        "/api/auth/change-password",
        json={
            "old_password": PASSWORD,
            "new_password": NEW_PASSWORD,
            "new_password_confirm": NEW_PASSWORD,
            **extra,
        },
    )


@pytest.fixture
def logged_in(client: TestClient) -> TestClient:
    assert _login(client).status_code == 200
    return client


def test_change_password_without_captcha_when_disabled(logged_in: TestClient) -> None:
    assert _change(logged_in).status_code == 204


@pytest.mark.parametrize("extra", [{}, {"captcha_token": "bad"}], ids=["missing", "bad"])
def test_change_password_bad_captcha(
    client: TestClient, captcha_on: list, extra: dict, db_session: Session
) -> None:
    assert _login(client, captcha_token="good").status_code == 200

    response = _change(client, **extra)

    assert response.status_code == 400
    assert response.json()["code"] == "captcha_failed"


def test_change_password_valid_captcha(client: TestClient, captcha_on: list) -> None:
    assert _login(client, captcha_token="good").status_code == 200

    assert _change(client, captcha_token="good").status_code == 204


def test_verify_turnstile_token_uses_siteverify(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    from app.services.turnstile import SITEVERIFY_URL, verify_turnstile_token

    seen: dict = {}

    def fake_post(url: str, data: dict, timeout: float) -> httpx.Response:
        seen.update(url=url, data=data)
        return httpx.Response(200, json={"success": True}, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    settings = Settings(database_url="postgresql+psycopg://x/x")

    assert verify_turnstile_token(settings, "tok", "1.2.3.4") is True
    assert seen["url"] == SITEVERIFY_URL
    assert seen["data"]["response"] == "tok"
    assert seen["data"]["remoteip"] == "1.2.3.4"
