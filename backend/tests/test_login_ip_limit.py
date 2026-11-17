from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.main import app
from app.models import LoginFailure
from app.services.login_ip_limit import (
    count_failures_in_window,
    is_ip_rate_limited,
    prune_old_failures,
    record_login_failure,
)
from tests.conftest import LOGIN_FAILED, PASSWORD

pytestmark = pytest.mark.db

LOGIN_URL = "/api/auth/login"
LIMIT = 3
# All requests from TestClient share one client address (like 127.0.0.1 behind Vite).
TEST_IP = "testclient"


@pytest.fixture
def limited(client: TestClient) -> None:
    app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={
            "captcha_enabled": False,
            "ip_login_max_failures": LIMIT,
            "ip_login_window_minutes": 15,
            "canary_trap_login": "honey_user",
        }
    )


def _login(client: TestClient, login: str = "redaktor", password: str = "wrong-password-xyz"):
    return client.post(LOGIN_URL, json={"login": login, "password": password})


def _count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(LoginFailure)) or 0


def test_blocks_after_threshold(client: TestClient, limited: None, db_session: Session) -> None:
    for _ in range(LIMIT):
        response = _login(client)
        assert response.status_code == 401
        assert response.json() == LOGIN_FAILED

    response = _login(client)

    assert response.status_code == 429
    assert response.json()["code"] == "too_many_attempts"
    assert _count(db_session) == LIMIT  # 429 itself is not recorded


def test_limit_applies_regardless_of_username(
    client: TestClient, limited: None, db_session: Session
) -> None:
    for login in ("redaktor", "czytelnik", "nobody"):
        assert _login(client, login).status_code == 401

    for login in ("redaktor", "czytelnik", "nobody", "admin"):
        response = _login(client, login, PASSWORD)
        assert response.status_code == 429
        assert response.json()["code"] == "too_many_attempts"


def test_honeypot_records_failure(client: TestClient, limited: None, db_session: Session) -> None:
    response = client.post(
        LOGIN_URL, json={"login": "redaktor", "password": PASSWORD, "website": "spam"}
    )

    assert response.status_code == 401
    assert response.json() == LOGIN_FAILED
    assert db_session.scalars(select(LoginFailure.ip)).all() == [TEST_IP]


def test_canary_trap_records_failure(
    client: TestClient, limited: None, db_session: Session
) -> None:
    assert _login(client, "honey_user").status_code == 401

    assert _count(db_session) == 1


def test_success_does_not_record(client: TestClient, limited: None, db_session: Session) -> None:
    for _ in range(LIMIT + 2):
        assert _login(client, password=PASSWORD).status_code == 200

    assert _count(db_session) == 0
    assert not is_ip_rate_limited(db_session, get_settings(), TEST_IP)


def test_locked_account_does_not_record(
    client: TestClient, limited: None, db_session: Session
) -> None:
    app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={"captcha_enabled": False, "ip_login_max_failures": 1000}
    )
    for _ in range(5):
        _login(client)
    recorded = _count(db_session)

    assert _login(client, password=PASSWORD).status_code == 423
    assert _count(db_session) == recorded


def test_old_rows_excluded_from_count(client: TestClient, db_session: Session) -> None:
    for _ in range(4):
        record_login_failure(db_session, TEST_IP, 15)
    db_session.execute(
        update(LoginFailure)
        .where(LoginFailure.id.in_(select(LoginFailure.id).limit(3)))
        .values(created_at=datetime.now(UTC) - timedelta(minutes=30))
    )

    assert count_failures_in_window(db_session, TEST_IP, 15) == 1
    assert count_failures_in_window(db_session, "10.0.0.9", 15) == 0


def test_prune_removes_expired_rows(db_session: Session) -> None:
    record_login_failure(db_session, TEST_IP, 15)
    record_login_failure(db_session, "10.0.0.9", 15)
    db_session.execute(
        update(LoginFailure)
        .where(LoginFailure.ip == "10.0.0.9")
        .values(created_at=datetime.now(UTC) - timedelta(hours=2))
    )

    prune_old_failures(db_session, 15)

    assert db_session.scalars(select(LoginFailure.ip)).all() == [TEST_IP]


def test_window_expiry_unblocks(client: TestClient, limited: None, db_session: Session) -> None:
    for _ in range(LIMIT):
        _login(client)
    assert _login(client).status_code == 429

    db_session.execute(
        update(LoginFailure).values(created_at=datetime.now(UTC) - timedelta(hours=1))
    )

    assert _login(client, password=PASSWORD).status_code == 200
