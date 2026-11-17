from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import SESSION_COOKIE
from app.models import ADMIN_LOGIN, Role, User, UserSession
from app.services.sessions import create_session
from tests.conftest import LOGIN_FAILED, PASSWORD
from tests.test_one_time_passwords import ONE_TIME_PASSWORD_PATTERN

pytestmark = pytest.mark.db

ADMIN_ENDPOINTS = [
    ("GET", "/api/admin/roles", None),
    ("GET", "/api/admin/users", None),
    ("POST", "/api/admin/users", {"login": "nowy", "role_id": 1}),
    ("PATCH", "/api/admin/users/{id}", {"role_id": 1}),
    ("POST", "/api/admin/users/{id}/block", None),
    ("POST", "/api/admin/users/{id}/unblock", None),
    ("DELETE", "/api/admin/users/{id}", None),
    ("POST", "/api/admin/users/{id}/reset-password", None),
    ("GET", "/api/admin/settings", None),
    ("PUT", "/api/admin/settings", {}),
]


def _role(db_session: Session, name: str) -> Role:
    return db_session.scalars(select(Role).filter_by(name=name)).one()


def _user(db_session: Session, login: str) -> User:
    return db_session.scalars(select(User).filter_by(login=login)).one()


def _sign_in_as(client: TestClient, db_session: Session, role: str) -> None:
    user = User(login=f"test-{role}", role=_role(db_session, role))
    db_session.add(user)
    db_session.flush()
    client.cookies.set(SESSION_COOKIE, create_session(db_session, user.id))
    db_session.flush()


def _session_count(db_session: Session, user_id: int) -> int:
    return db_session.scalar(
        select(func.count()).select_from(UserSession).where(UserSession.user_id == user_id)
    )


def _login_redaktor(client: TestClient):
    return client.post("/api/auth/login", json={"login": "redaktor", "password": PASSWORD})


@pytest.fixture
def admin_client(client: TestClient, db_session: Session) -> TestClient:
    _sign_in_as(client, db_session, "Administrator")
    return client


def test_admin_endpoints_are_forbidden_for_auditor(client: TestClient, db_session: Session) -> None:
    _sign_in_as(client, db_session, "Audytor")
    target = _user(db_session, "czytelnik")

    for method, path, body in ADMIN_ENDPOINTS:
        response = client.request(method, path.format(id=target.id), json=body)
        assert response.status_code == 403, (method, path)
        assert response.json()["code"] == "forbidden"

    assert target.is_blocked is False
    assert target.deleted_at is None


def test_admin_account_is_protected(admin_client: TestClient, db_session: Session) -> None:
    admin = _user(db_session, ADMIN_LOGIN)
    role_id = _role(db_session, "Czytelnik").id

    for method, suffix, body in [
        ("PATCH", "", {"role_id": role_id}),
        ("POST", "/block", None),
        ("DELETE", "", None),
        ("POST", "/reset-password", None),
    ]:
        response = admin_client.request(method, f"/api/admin/users/{admin.id}{suffix}", json=body)
        assert response.status_code == 409
        assert response.json()["code"] == "admin_account_protected"

    db_session.refresh(admin)
    assert admin.role.name == "Administrator"
    assert admin.is_blocked is False
    assert admin.deleted_at is None
    assert admin.password_hash is not None


def test_created_user_logs_in_with_one_time_password(
    admin_client: TestClient, db_session: Session
) -> None:
    role_id = _role(db_session, "Redaktor").id

    response = admin_client.post("/api/admin/users", json={"login": "nowak", "role_id": role_id})

    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "Redaktor"
    assert ONE_TIME_PASSWORD_PATTERN.fullmatch(body["one_time_password"])
    assert _user(db_session, "nowak").password_hash is None

    response = admin_client.post(
        "/api/auth/login", json={"login": "nowak", "password": body["one_time_password"]}
    )
    assert response.status_code == 200
    assert response.json()["must_change_password"] is True


def test_update_changes_role(admin_client: TestClient, db_session: Session) -> None:
    target = _user(db_session, "czytelnik")
    role_id = _role(db_session, "Redaktor").id

    response = admin_client.patch(f"/api/admin/users/{target.id}", json={"role_id": role_id})

    assert response.status_code == 200
    assert response.json()["role"] == "Redaktor"


def test_block_closes_sessions_and_unblock_clears_lock(
    admin_client: TestClient, db_session: Session
) -> None:
    target = _user(db_session, "redaktor")
    create_session(db_session, target.id)
    db_session.flush()

    response = admin_client.post(f"/api/admin/users/{target.id}/block")

    assert response.status_code == 200
    assert _session_count(db_session, target.id) == 0
    assert _login_redaktor(admin_client).json() == LOGIN_FAILED

    target.locked_until = datetime.now(UTC) + timedelta(minutes=10)
    db_session.flush()
    assert admin_client.post(f"/api/admin/users/{target.id}/unblock").status_code == 200
    assert _login_redaktor(admin_client).status_code == 200


def test_delete_hides_user_and_keeps_login_taken(
    admin_client: TestClient, db_session: Session
) -> None:
    target = _user(db_session, "czytelnik")
    create_session(db_session, target.id)
    db_session.flush()

    response = admin_client.delete(f"/api/admin/users/{target.id}")

    assert response.status_code == 204
    assert _session_count(db_session, target.id) == 0
    logins = [u["login"] for u in admin_client.get("/api/admin/users").json()]
    assert "czytelnik" not in logins
    response = admin_client.post(
        "/api/admin/users", json={"login": "czytelnik", "role_id": target.role_id}
    )
    assert response.status_code == 409
    assert response.json()["code"] == "login_taken"


def test_reset_invalidates_password_and_closes_sessions(
    admin_client: TestClient, db_session: Session
) -> None:
    target = _user(db_session, "redaktor")
    create_session(db_session, target.id)
    db_session.flush()

    response = admin_client.post(f"/api/admin/users/{target.id}/reset-password")

    assert response.status_code == 200
    assert ONE_TIME_PASSWORD_PATTERN.fullmatch(response.json()["one_time_password"])
    assert _session_count(db_session, target.id) == 0
    assert _login_redaktor(admin_client).json() == LOGIN_FAILED
