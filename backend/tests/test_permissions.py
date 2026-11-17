import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Band
from tests.test_admin_users import _sign_in_as

pytestmark = pytest.mark.db

BAND_PAYLOAD = {"name": "New band", "bio": "Band bio text"}


@pytest.mark.parametrize(
    ("role", "can_write_bands", "can_manage"),
    [
        ("Administrator", False, True),
        ("Audytor", False, False),
        ("Redaktor", True, False),
        ("Czytelnik", False, False),
    ],
)
def test_role_permissions(
    client: TestClient, db_session: Session, role: str, can_write_bands: bool, can_manage: bool
) -> None:
    band = Band(**BAND_PAYLOAD)
    db_session.add(band)
    _sign_in_as(client, db_session, role)
    write = 200 if can_write_bands else 403
    manage = 200 if can_manage else 403

    for method, path, expected in [
        ("GET", "/api/bands", 200),
        ("POST", "/api/bands", write),
        ("PUT", f"/api/bands/{band.id}", write),
        ("GET", "/api/admin/users", manage),
        ("GET", "/api/admin/settings", manage),
    ]:
        body = BAND_PAYLOAD if method in ("POST", "PUT") else None
        response = client.request(method, path, json=body)
        assert response.status_code == expected, (method, path)
        if expected == 403:
            assert response.json()["code"] == "forbidden"
