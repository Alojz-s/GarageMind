from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import SESSION_COOKIE
from app.core.database import get_db
from app.main import app
from app.models import Band, Role, User
from app.services.sessions import create_session
from scripts.seed import seed

pytestmark = pytest.mark.db

BAND_PAYLOAD = {"name": "New band", "bio": "Band bio text"}


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    seed(db_session, "haslo-startowe-admina-testy", "haslo-uzytkownikow-testowych")
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    ("role", "method", "path", "expected_status"),
    [
        ("Administrator", "GET", "/api/bands", 200),
        ("Administrator", "POST", "/api/bands", 403),
        ("Administrator", "PUT", "/api/bands/{band_id}", 403),
        ("Administrator", "GET", "/api/admin/users", 200),
        ("Administrator", "GET", "/api/admin/settings", 200),
        ("Audytor", "GET", "/api/bands", 200),
        ("Audytor", "POST", "/api/bands", 403),
        ("Audytor", "PUT", "/api/bands/{band_id}", 403),
        ("Audytor", "GET", "/api/admin/users", 403),
        ("Audytor", "GET", "/api/admin/settings", 403),
        ("Redaktor", "GET", "/api/bands", 200),
        ("Redaktor", "POST", "/api/bands", 200),
        ("Redaktor", "PUT", "/api/bands/{band_id}", 200),
        ("Redaktor", "GET", "/api/admin/users", 403),
        ("Redaktor", "GET", "/api/admin/settings", 403),
        ("Czytelnik", "GET", "/api/bands", 200),
        ("Czytelnik", "POST", "/api/bands", 403),
        ("Czytelnik", "PUT", "/api/bands/{band_id}", 403),
        ("Czytelnik", "GET", "/api/admin/users", 403),
        ("Czytelnik", "GET", "/api/admin/settings", 403),
    ],
)
def test_role_permissions(
    client: TestClient,
    db_session: Session,
    role: str,
    method: str,
    path: str,
    expected_status: int,
) -> None:
    user = User(
        login=f"test-{role}", role=db_session.scalars(select(Role).filter_by(name=role)).one()
    )
    band = Band(**BAND_PAYLOAD)
    db_session.add_all([user, band])
    db_session.flush()
    client.cookies.set(SESSION_COOKIE, create_session(db_session, user.id))
    db_session.flush()

    response = client.request(
        method,
        path.format(band_id=band.id),
        json=BAND_PAYLOAD if method in ("POST", "PUT") else None,
    )

    assert response.status_code == expected_status
    if expected_status == 403:
        assert response.json()["code"] == "forbidden"
