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