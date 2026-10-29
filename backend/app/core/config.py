from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "dev-insecure-secret-change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "helloPadelDashboard"
    environment: Literal["development", "test", "production"] = "development"

    database_url: str = "postgresql+asyncpg://hellopadel:hellopadel@localhost:5432/hellopadel"

    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    refresh_cookie_name: str = "hp_refresh"
    cookie_secure: bool = False

    # Orígenes separados por comas; vacío desactiva CORS.
    cors_origins: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def _check_production_secret(self) -> "Settings":
        if self.environment == "production" and (
            self.jwt_secret == DEFAULT_JWT_SECRET or len(self.jwt_secret) < 32
        ):
            raise ValueError("JWT_SECRET debe tener al menos 32 caracteres en producción")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
