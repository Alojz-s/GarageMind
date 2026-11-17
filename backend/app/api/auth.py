from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    SESSION_COOKIE,
    ApiError,
    CurrentUser,
    get_security_settings,
    password_change_required,
    reject_restricted_session,
)
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.models import PasswordHistory, User
from app.schemas.auth import (
    CaptchaConfigResponse,
    ChangePasswordRequest,
    LoginRequest,
    MeResponse,
    PasswordPolicyErrorResponse,
    PasswordPolicyResponse,
    PolicyViolation,
)
from app.services.canary_trap import (
    CanaryTrigger,
    fire_trap,
    is_trap_login,
    trigger_canary_in_background,
)
from app.services.login_lockout import locked_seconds, register_failed_login, reset_lockout
from app.services.one_time_passwords import (
    try_login_with_one_time_password,
    verify_used_one_time_password,
)
from app.services.password_policy import MAX_PASSWORD_LENGTH, describe_policy, validate_password
from app.services.passwords import DUMMY_PASSWORD_HASH, hash_password, verify_password
from app.services.sessions import create_session, delete_session
from app.services.turnstile import TurnstileVerifier, check_captcha, verify_turnstile_token

LOGIN_FAILED = "Incorrect username or password"

router = APIRouter(prefix="/auth", tags=["auth"])


def _me(db: Session, user: User) -> MeResponse:
    settings = get_security_settings(db)
    return MeResponse(
        id=user.id,
        login=user.login,
        role=user.role.name,
        permissions=sorted(p.name for p in user.role.permissions),
        must_change_password=password_change_required(user, settings),
        idle_timeout_minutes=settings.idle_timeout_minutes,
    )


def get_turnstile_verifier(
    settings: Annotated[Settings, Depends(get_settings)],
) -> TurnstileVerifier:
    """Dependency overridden in tests (no network)."""
    return lambda token, remote_ip: verify_turnstile_token(settings, token, remote_ip)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _require_captcha(
    settings: Settings,
    verifier: TurnstileVerifier,
    token: str | None,
    request: Request,
) -> None:
    if not check_captcha(settings, verifier, token, _client_ip(request)):
        raise ApiError(status.HTTP_400_BAD_REQUEST, "CAPTCHA verification failed", "captcha_failed")


def _check_honeypot(body: LoginRequest) -> None:
    if body.website.strip():
        # TODO(M2-D): record the attempt in login_failures.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, LOGIN_FAILED)


def _check_ip_limit(request: Request, db: Session) -> None:
    """M2-D: per-IP failed login limit (429 too_many_attempts). No-op for now."""


def get_canary_trigger() -> CanaryTrigger:
    """Dependency overridden in tests (no network)."""
    return trigger_canary_in_background


def _check_canary_trap(body: LoginRequest, settings: Settings, trigger: CanaryTrigger) -> None:
    """Trap account (CANARY_TRAP_LOGIN): fires the Canarytoken and ends in the usual 401.

    Exits before the user lookup, so no failed-login counter is touched.
    """
    if is_trap_login(settings, body.login):
        fire_trap(settings, trigger)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, LOGIN_FAILED)


def _check_account_lock(user: User | None) -> None:
    if user is None:
        return
    remaining = locked_seconds(user)
    if remaining > 0:
        raise ApiError(
            status.HTTP_423_LOCKED,
            "Account temporarily locked due to too many failed login attempts",
            "account_locked",
            locked_seconds=remaining,
        )


@router.get("/captcha-config")
def captcha_config(settings: Annotated[Settings, Depends(get_settings)]) -> CaptchaConfigResponse:
    return CaptchaConfigResponse(
        enabled=settings.captcha_enabled,
        site_key=settings.turnstile_site_key if settings.captcha_enabled else None,
    )


@router.post("/login")
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    verifier: Annotated[TurnstileVerifier, Depends(get_turnstile_verifier)],
    canary_trigger: Annotated[CanaryTrigger, Depends(get_canary_trigger)],
) -> MeResponse:
    _check_honeypot(body)  # 1
    _check_ip_limit(request, db)  # 2 (M2-D)
    _require_captcha(settings, verifier, body.captcha_token, request)  # 3
    _check_canary_trap(body, settings, canary_trigger)  # 4 (M2-C)

    user = db.scalar(select(User).where(User.login == body.login))
    if user is not None and (user.is_blocked or user.deleted_at is not None):
        user = None
    _check_account_lock(user)  # 5
    # 6: password, one-time password, failed-login counter
    password_hash = user.password_hash if user and user.password_hash else DUMMY_PASSWORD_HASH
    password_ok = verify_password(body.password, password_hash)
    otp_ok = not password_ok and try_login_with_one_time_password(db, user, body.password)
    if user is None or not (password_ok or otp_ok):
        if user is not None:
            register_failed_login(user, get_security_settings(db).max_failed_logins)
            db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, LOGIN_FAILED)

    reset_lockout(user)
    if password_change_required(user, get_security_settings(db)):
        user.must_change_password = True
    token = create_session(db, user.id)
    db.commit()
    response.set_cookie(SESSION_COOKIE, token, path="/", httponly=True, samesite="strict")
    return _me(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> None:
    if token:
        delete_session(db, token)
        db.commit()
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="strict")


@router.get("/me")
def me(user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> MeResponse:
    return _me(db, user)


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={422: {"model": PasswordPolicyErrorResponse}},
)
def change_password(
    body: ChangePasswordRequest,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    verifier: Annotated[TurnstileVerifier, Depends(get_turnstile_verifier)],
) -> Response:
    _require_captcha(settings, verifier, body.captcha_token, request)
    if body.new_password != body.new_password_confirm:
        raise ApiError(
            status.HTTP_400_BAD_REQUEST,
            "New password confirmation does not match",
            "password_mismatch",
        )
    if user.password_hash is None:
        old_password_ok = verify_used_one_time_password(db, user.id, body.old_password)
    else:
        old_password_ok = verify_password(body.old_password, user.password_hash)
    if not old_password_ok:
        raise ApiError(
            status.HTTP_400_BAD_REQUEST, "Current password is incorrect", "invalid_old_password"
        )
    violations = validate_password(
        body.new_password, db=db, settings=get_security_settings(db), user_id=user.id
    )
    if violations:
        error = PasswordPolicyErrorResponse(
            detail="New password does not meet the password policy",
            violations=[PolicyViolation(code=v.code, message=v.message) for v in violations],
        )
        return JSONResponse(error.model_dump(), status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)

    if user.password_hash is not None:
        db.add(PasswordHistory(user_id=user.id, password_hash=user.password_hash))
    user.password_hash = hash_password(body.new_password)
    user.password_changed_at = datetime.now(UTC)
    user.must_change_password = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/password-policy", dependencies=[Depends(reject_restricted_session)])
def password_policy(db: Annotated[Session, Depends(get_db)]) -> PasswordPolicyResponse:
    settings = get_security_settings(db)
    return PasswordPolicyResponse(
        min_password_length=settings.min_password_length,
        max_password_length=MAX_PASSWORD_LENGTH,
        date_rule_enabled=settings.date_rule_enabled,
        requirements=describe_policy(settings),
    )
