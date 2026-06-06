from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the root-level .env regardless of where the process is launched from.
# In Docker the file won't exist (vars come from compose `environment:`), which
# pydantic-settings silently ignores.
_ROOT_ENV = Path(__file__).parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ROOT_ENV), extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/workoutwiz"
    secret_key: str = "changeme-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    log_level: str = "INFO"
    anthropic_api_key: str = ""
    router_model: str = "claude-haiku-4-5-20251001"
    coach_model: str = "claude-haiku-4-5-20251001"
    generator_model: str = "claude-haiku-4-5-20251001"
    logger_model: str = "claude-haiku-4-5-20251001"


settings = Settings()
