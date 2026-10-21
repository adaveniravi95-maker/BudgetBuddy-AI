from pydantic_settings import BaseSettings
from functools import lru_cache

DEV_SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./db.sqlite3"
    SECRET_KEY: str = DEV_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000"

    model_config = {"env_file": ".env"}

    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        return url

    @property
    def is_sqlite(self) -> bool:
        return self.sqlalchemy_database_url.startswith("sqlite")

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    def check_production_safety(self) -> None:
        if not self.is_sqlite and self.SECRET_KEY == DEV_SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY must be set to a unique value in production. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./budgetbuddy.db"

    jwt_secret_key: str = "change-this-development-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    frontend_url: str = "http://localhost:5173"

    environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()


if settings.environment.lower() == "production":
    if settings.jwt_secret_key == "change-this-development-secret":
        raise RuntimeError(
            "Production JWT_SECRET_KEY must be configured."
        )

    if len(settings.jwt_secret_key) < 32:
        raise RuntimeError(
            "Production JWT_SECRET_KEY must contain at least 32 characters."
        )
