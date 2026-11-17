from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.main import app
from app.models import LoginFailure
from app.services.login_ip_limit import prune_old_failures, record_login_failure
from tests.conftest import LOGIN_FAILED, PASSWORD

pytestmark = pytest.mark.db

LIMIT = 3


@pytest.fixture
def limited(client: TestClient) -> None:
    app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={
            "captcha_enabled": False,
            "ip_login_max_failures": LIMIT,
            "ip_login_window_minutes": 15,
        }
    )


def _login(client: TestClient, login: str = "redaktor", password: str = "wrong-password-xyz"):
    return client.post("/api/auth/login", json={"login": login, "password": password})


def test_blocks_ip_regardless_of_username(client: TestClient, limited: None) -> None:
    response = client.post(
        "/api/auth/login", json={"login": "redaktor", "password": PASSWORD, "website": "spam"}
    )
    assert response.json() == LOGIN_FAILED
    for login in ("czytelnik", "nobody"):
        assert _login(client, login).status_code == 401

    response = _login(client, "redaktor", PASSWORD)

    assert response.status_code == 429
    assert response.json()["code"] == "too_many_attempts"


def test_window_expiry_unblocks(client: TestClient, limited: None, db_session: Session) -> None:
    for _ in range(LIMIT):
        _login(client)
    assert _login(client).status_code == 429

    db_session.execute(
        update(LoginFailure).values(created_at=datetime.now(UTC) - timedelta(hours=1))
    )

    assert _login(client, password=PASSWORD).status_code == 200


def test_prune_removes_expired_rows(db_session: Session) -> None:
    record_login_failure(db_session, "10.0.0.1", 15)
    record_login_failure(db_session, "10.0.0.9", 15)
    db_session.execute(
        update(LoginFailure)
        .where(LoginFailure.ip == "10.0.0.9")
        .values(created_at=datetime.now(UTC) - timedelta(hours=2))
    )

    prune_old_failures(db_session, 15)

    assert db_session.scalars(select(LoginFailure.ip)).all() == ["10.0.0.1"]
