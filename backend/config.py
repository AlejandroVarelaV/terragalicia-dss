from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "TerraGalicia DSS Backend"
    app_env: str = "development"
    app_debug: bool = True
    app_base_url: str = "http://localhost:8000"

    api_prefix: str = "/api/v1"

    jwt_secret_key: str = "change-me-access"
    jwt_refresh_secret_key: str = "change-me-refresh"
    jwt_access_ttl_min: int = 30
    jwt_refresh_ttl_days: int = 7
    jwt_algorithm: str = "HS256"

    auth_demo_users_json: str = (
        '{"farmer1": {"password": "farmer123", "roles": ["farmer"]}, '
        '"coop1": {"password": "coop123", "roles": ["cooperative"]}}'
    )

    database_url_postgis: str = "postgresql://postgres:postgres@postgres:5432/terragalicia"
    redis_url: str = "redis://redis:6379/0"

    orion_base_url: str = "http://orion:1026"
    orion_service: str = "terragalicia"
    orion_servicepath: str = "/"

    quantumleap_base_url: str = "http://quantumleap:8668"

    ml_service_url: str = "http://ml-service:8010"
    llm_service_url: str = "http://llm-service:11434"

    meteogalicia_base_url: str = "https://servizos.meteogalicia.gal"
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"
    openweather_api_key: str | None = None

    request_timeout_seconds: float = 10.0

    suitability_cache_ttl_seconds: int = 6 * 60 * 60
    weather_cache_ttl_seconds: int = 30 * 60

    seed_data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[1] / "data" / "seed")


@lru_cache
def get_settings() -> Settings:
    return Settings()
