from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_host: str = "0.0.0.0"
    app_port: int = 7860
    app_env: str = "development"

    api_key: str = "changeme"
    api_key_enabled: bool = False

    leaderboard_max_entries: int = 10

    log_level: str = "INFO"

    episode_ttl_seconds: int = 3600        # episodes expire after 1 hour
    rate_limit_per_minute: int = 60        # requests per minute per IP
    
    # Persistence
    db_path: str = "./data/codereview.db"
    db_echo: bool = False    # Set True to log all SQL queries

@lru_cache
def get_settings() -> Settings:
    return Settings()
