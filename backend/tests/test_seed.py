import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import Base
from app.models import Band, Permission, Role, SecuritySettings, User
from app.services.passwords import verify_password
from scripts.seed import ADMIN_LOGIN, seed
from tests.conftest import ADMIN_PASSWORD, PASSWORD

pytestmark = pytest.mark.db


def _count(db: Session, model: type[Base]) -> int:
    return db.scalar(select(func.count()).select_from(model)) or 0


def _user(db: Session, login: str) -> User:
    return db.scalars(select(User).where(User.login == login)).one()


def test_seed_is_idempotent_and_keeps_passwords(db_session: Session) -> None:
    models = [User, Role, Permission, Band, SecuritySettings]

    seed(db_session, ADMIN_PASSWORD, PASSWORD)
    counts = {model: _count(db_session, model) for model in models}
    seed(db_session, "inne-haslo-startowe-admina", PASSWORD)

    assert {model: _count(db_session, model) for model in models} == counts
    assert counts == {User: 4, Role: 4, Permission: 4, Band: 3, SecuritySettings: 1}
    assert verify_password(ADMIN_PASSWORD, _user(db_session, ADMIN_LOGIN).password_hash)


def test_seed_users(db_session: Session) -> None:
    seed(db_session, ADMIN_PASSWORD, PASSWORD)

    admin = _user(db_session, ADMIN_LOGIN)
    assert admin.role.name == "Administrator"
    assert admin.must_change_password is True
    assert verify_password(ADMIN_PASSWORD, admin.password_hash)

    for login, role_name in [("redaktor", "Redaktor"), ("czytelnik", "Czytelnik")]:
        user = _user(db_session, login)
        assert user.role.name == role_name
        assert user.must_change_password is False
        assert verify_password(PASSWORD, user.password_hash)

    trap = _user(db_session, get_settings().canary_trap_login)
    assert trap.role.name == "Czytelnik"
    assert not verify_password(PASSWORD, trap.password_hash)
