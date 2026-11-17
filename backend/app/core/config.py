from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "GarageMind"
    app_env: str = "development"
    debug: bool = False
    database_url: str
    database_connect_timeout: int = 3

    # Cloudflare Turnstile. Domyślne klucze to publiczne klucze testowe (zawsze przechodzą).
    captcha_enabled: bool = False
    turnstile_site_key: str = "1x00000000000000000000AA"
    turnstile_secret_key: SecretStr = SecretStr("1x0000000000000000000000000000000AA")

    # Canarytokens: konto-pułapka. Pusty URL = brak wywołania sieciowego.
    canary_trap_login: str = "svc_backup"
    canary_trap_url: str = ""

    # Per-IP failed login limit (password spraying), sliding window.
    ip_login_max_failures: int = 20
    ip_login_window_minutes: int = 15

    # Wymagane tylko przez scripts/seed.py.
    admin_initial_password: SecretStr | None = None
    seed_user_password: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
