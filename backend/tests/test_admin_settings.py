from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import SESSION_COOKIE, get_security_settings
from app.services.sessions import create_session, find_session
from tests.conftest import PASSWORD
from tests.test_admin_users import _sign_in_as, _user

pytestmark = pytest.mark.db

DEFAULTS = {
    "min_password_length": 15,
    "date_rule_enabled": False,
    "password_validity_days": 0,
    "idle_timeout_minutes": 15,
    "max_failed_logins": 5,
}


@pytest.fixture
def admin_client(client: TestClient, db_session: Session) -> TestClient:
    _sign_in_as(client, db_session, "Administrator")
    return client


def _put(client: TestClient, **changes: object) -> None:
    response = client.put("/api/admin/settings", json=DEFAULTS | changes)
    assert response.status_code == 200


def test_raised_min_length_applies_to_next_password_change(admin_client: TestClient) -> None:
    _put(admin_client, min_password_length=16)

    admin_client.post("/api/auth/login", json={"login": "redaktor", "password": PASSWORD})
    response = admin_client.post(
        "/api/auth/change-password",
        json={
            "old_password": PASSWORD,
            "new_password": "kot-pies-chomik",
            "new_password_confirm": "kot-pies-chomik",
        },
    )

    assert response.status_code == 422
    assert [v["code"] for v in response.json()["violations"]] == ["too_short"]


def test_lowered_idle_timeout_expires_open_session(
    admin_client: TestClient, db_session: Session
) -> None:
    token = create_session(db_session, _user(db_session, "redaktor").id)
    db_session.flush()
    find_session(db_session, token).last_activity_at = datetime.now(UTC) - timedelta(minutes=2)
    db_session.flush()

    _put(admin_client, idle_timeout_minutes=1)
    admin_client.cookies.set(SESSION_COOKIE, token)
    response = admin_client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == "session_expired"


def test_invalid_settings_are_rejected(admin_client: TestClient, db_session: Session) -> None:
    invalid = {
        "min_password_length": 14,
        "password_validity_days": -1,
        "idle_timeout_minutes": 121,
        "max_failed_logins": 0,
    }

    response = admin_client.put("/api/admin/settings", json=DEFAULTS | invalid)

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Invalid request data"
    assert {v["code"] for v in body["violations"]} == {
        "invalid_min_password_length",
        "invalid_password_validity_days",
        "invalid_idle_timeout",
        "invalid_max_failed_logins",
    }
    assert get_security_settings(db_session).idle_timeout_minutes == 15
