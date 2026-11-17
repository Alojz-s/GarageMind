from app.services.passwords import hash_password, verify_password

PASSWORD = "długie-hasło-testowe-bez-roku"


def test_hash_is_salted_argon2id() -> None:
    first, second = hash_password(PASSWORD), hash_password(PASSWORD)

    assert first.startswith("$argon2id$")
    assert PASSWORD not in first
    assert first != second


def test_verify_password() -> None:
    password_hash = hash_password(PASSWORD)

    assert verify_password(PASSWORD, password_hash) is True
    assert verify_password("inne-długie-hasło-testowe", password_hash) is False
    assert verify_password(PASSWORD, "to-nie-jest-hash") is False
