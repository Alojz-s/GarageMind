from collections.abc import Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.auth import get_turnstile_verifier
from app.core.config import Settings, get_settings
from app.main import app
from app.services.turnstile import SITEVERIFY_URL, verify_turnstile_token
from tests.conftest import LOGIN_FAILED, NEW_PASSWORD, PASSWORD

pytestmark = pytest.mark.db

CAPTCHA_CASES = pytest.mark.parametrize(
    ("extra", "status"),
    [({}, 400), ({"captcha_token": "bad"}, 400), ({"captcha_token": "good"}, None)],
    ids=["missing", "bad", "good"],
)


@pytest.fixture
def captcha_on(client: TestClient) -> Iterator[list[tuple[str, str | None]]]:
    calls: list[tuple[str, str | None]] = []

    def verifier(token: str, remote_ip: str | None) -> bool:
        calls.append((token, remote_ip))
        return token == "good"

    app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={"captcha_enabled": True}
    )
    app.dependency_overrides[get_turnstile_verifier] = lambda: verifier
    yield calls


def _login(client: TestClient, **extra: object):
    payload = {"login": "redaktor", "password": PASSWORD, **extra}
    return client.post("/api/auth/login", json=payload)


def test_captcha_config(client: TestClient, captcha_on: list) -> None:
    response = client.get("/api/auth/captcha-config")

    assert response.json() == {"enabled": True, "site_key": get_settings().turnstile_site_key}


@CAPTCHA_CASES
def test_login_requires_valid_captcha(
    client: TestClient, captcha_on: list, extra: dict, status: int | None
) -> None:
    response = _login(client, **extra)

    assert response.status_code == (status or 200)
    if status:
        assert response.json()["code"] == "captcha_failed"


@CAPTCHA_CASES
def test_change_password_requires_valid_captcha(
    client: TestClient, captcha_on: list, extra: dict, status: int | None
) -> None:
    assert _login(client, captcha_token="good").status_code == 200

    response = client.post(
        "/api/auth/change-password",
        json={
            "old_password": PASSWORD,
            "new_password": NEW_PASSWORD,
            "new_password_confirm": NEW_PASSWORD,
            **extra,
        },
    )

    assert response.status_code == (status or 204)
    if status:
        assert response.json()["code"] == "captcha_failed"


def test_honeypot_returns_generic_failure(client: TestClient, captcha_on: list) -> None:
    response = _login(client, website="http://spam.example", captcha_token="good")

    assert response.status_code == 401
    assert response.json() == LOGIN_FAILED
    assert captcha_on == []


def test_verify_turnstile_token_uses_siteverify(monkeypatch: pytest.MonkeyPatch) -> None:
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
