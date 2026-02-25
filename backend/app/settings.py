from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None)

    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str
    sec_user_agent: str
    fred_api_key: str | None = None
    coingecko_api_key: str | None = None
    openfigi_api_key: str | None = None

settings = Settings()
