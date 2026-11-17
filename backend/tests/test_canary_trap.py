import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_canary_trigger
from app.core.config import get_settings
from app.main import app
from app.models import User
from tests.conftest import LOGIN_FAILED, PASSWORD

pytestmark = pytest.mark.db

TRAP_URL = "https://canary.example/trap"


@pytest.fixture
def calls(client: TestClient) -> list[str]:
    recorded: list[str] = []
    app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={
            "captcha_enabled": False,
            "ip_login_max_failures": 1000,
            "canary_trap_url": TRAP_URL,
        }
    )
    app.dependency_overrides[get_canary_trigger] = lambda: recorded.append
    return recorded


def _login(client: TestClient, login: str, password: str = "whatever-password-123"):
    return client.post("/api/auth/login", json={"login": login, "password": password})


def test_trap_login_fires_alert_and_returns_generic_401(
    client: TestClient, db_session: Session, calls: list[str]
) -> None:
    trap_login = get_settings().canary_trap_login

    for _ in range(6):
        response = _login(client, trap_login)
        assert response.status_code == 401
        assert response.json() == LOGIN_FAILED
    assert _login(client, "redaktor", PASSWORD).status_code == 200

    assert calls == [TRAP_URL] * 6
    # Konto-pułapka nie może się zablokować, bo kolejne próby przestałyby wywoływać alert.
    trap_user = db_session.scalars(select(User).where(User.login == trap_login)).one()
    assert trap_user.locked_until is None


def test_trigger_failure_is_swallowed(client: TestClient, calls: list[str]) -> None:
    def failing(url: str) -> None:
        raise RuntimeError("network down")

    app.dependency_overrides[get_canary_trigger] = lambda: failing

    response = _login(client, get_settings().canary_trap_login)

    assert response.status_code == 401
    assert response.json() == LOGIN_FAILED
