from __future__ import annotations

from dataclasses import dataclass
from os import environ as process_environ
from typing import Mapping


class ConfigurationError(RuntimeError):
    """Raised when security-sensitive application configuration is invalid."""


PLACEHOLDER_MARKERS = (
    "change-in-production",
    "changeme",
    "example",
    "placeholder",
    "replace_me",
    "your-",
    "your_",
)

TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}


def _read_bool(values: Mapping[str, str], name: str, default: bool = False) -> bool:
    raw = values.get(name)
    if raw is None or raw.strip() == "":
        return default
    normalized = raw.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ConfigurationError(f"{name} must be one of: true, false, 1, 0, yes, no, on, off.")


def _read_int(
    values: Mapping[str, str],
    name: str,
    default: int,
    *,
    minimum: int = 1,
    maximum: int | None = None,
) -> int:
    raw = values.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer.") from exc
    if parsed < minimum or (maximum is not None and parsed > maximum):
        bounds = f">= {minimum}" if maximum is None else f"between {minimum} and {maximum}"
        raise ConfigurationError(f"{name} must be {bounds}.")
    return parsed


def _is_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return any(marker in lowered for marker in PLACEHOLDER_MARKERS)


def _require_secret(values: Mapping[str, str], name: str) -> str:
    value = values.get(name, "").strip()
    if not value:
        raise ConfigurationError(f"{name} is required. Generate a unique value before starting the backend.")
    if len(value) < 32:
        raise ConfigurationError(f"{name} must be at least 32 characters.")
    if _is_placeholder(value):
        raise ConfigurationError(f"{name} still contains a placeholder value.")
    return value


def _read_origins(values: Mapping[str, str]) -> tuple[str, ...]:
    raw = values.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    origins = tuple(origin.strip() for origin in raw.split(",") if origin.strip())
    if not origins:
        raise ConfigurationError("CORS_ORIGINS must contain at least one origin.")
    return origins


@dataclass(frozen=True)
class Settings:
    environment: str
    debug: bool
    secret_key: str
    jwt_secret_key: str
    jwt_access_token_expires: int
    database_url: str
    cors_origins: tuple[str, ...]
    cors_supports_credentials: bool
    allow_demo_data: bool
    demo_admin_password: str | None
    demo_user_password: str | None
    allow_public_registration: bool
    openai_api_key: str | None
    telegram_bot_token: str | None
    telegram_user_id: str | None
    host: str
    port: int

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def telegram_configured(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_user_id)


def load_settings(values: Mapping[str, str] | None = None) -> Settings:
    source = process_environ if values is None else values
    environment = source.get("FLASK_ENV", "development").strip().lower()
    if environment not in {"development", "testing", "production"}:
        raise ConfigurationError("FLASK_ENV must be development, testing, or production.")

    secret_key = _require_secret(source, "SECRET_KEY")
    jwt_secret_key = _require_secret(source, "JWT_SECRET_KEY")
    cors_origins = _read_origins(source)
    cors_supports_credentials = _read_bool(source, "CORS_SUPPORTS_CREDENTIALS", default=False)

    if "*" in cors_origins:
        if environment == "production":
            raise ConfigurationError("Wildcard CORS origins are not allowed in production.")
        if cors_supports_credentials:
            raise ConfigurationError("Wildcard CORS origins cannot be combined with credentials.")

    allow_demo_data = _read_bool(source, "ALLOW_DEMO_DATA", default=False)
    demo_admin_password = source.get("DEMO_ADMIN_PASSWORD", "").strip() or None
    demo_user_password = source.get("DEMO_USER_PASSWORD", "").strip() or None
    if allow_demo_data:
        if environment == "production":
            raise ConfigurationError("ALLOW_DEMO_DATA cannot be enabled in production.")
        for name, value in (
            ("DEMO_ADMIN_PASSWORD", demo_admin_password),
            ("DEMO_USER_PASSWORD", demo_user_password),
        ):
            if value is None or len(value) < 12 or _is_placeholder(value):
                raise ConfigurationError(f"{name} must be a non-placeholder value of at least 12 characters.")

    telegram_bot_token = source.get("TELEGRAM_BOT_TOKEN", "").strip() or None
    telegram_user_id = source.get("TELEGRAM_USER_ID", "").strip() or None
    if bool(telegram_bot_token) != bool(telegram_user_id):
        raise ConfigurationError("TELEGRAM_BOT_TOKEN and TELEGRAM_USER_ID must be configured together.")

    return Settings(
        environment=environment,
        debug=_read_bool(source, "FLASK_DEBUG", default=environment == "development"),
        secret_key=secret_key,
        jwt_secret_key=jwt_secret_key,
        jwt_access_token_expires=_read_int(
            source,
            "JWT_ACCESS_TOKEN_EXPIRES",
            3600,
            minimum=300,
            maximum=86400,
        ),
        database_url=source.get("DATABASE_URL", "sqlite:///ai_agent_system.db").strip(),
        cors_origins=cors_origins,
        cors_supports_credentials=cors_supports_credentials,
        allow_demo_data=allow_demo_data,
        demo_admin_password=demo_admin_password,
        demo_user_password=demo_user_password,
        allow_public_registration=_read_bool(source, "ALLOW_PUBLIC_REGISTRATION", default=False),
        openai_api_key=source.get("OPENAI_API_KEY", "").strip() or None,
        telegram_bot_token=telegram_bot_token,
        telegram_user_id=telegram_user_id,
        host=source.get("HOST", "127.0.0.1").strip(),
        port=_read_int(source, "PORT", 5000, minimum=1, maximum=65535),
    )
