from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Use top level .env file (one level above ./backend/) to add one-liner:
    # MONGODB_URL="yourconnectionstring"
    # REDIS_URL="redis://localhost:6379/0"
    model_config = SettingsConfigDict(env_file="../../.env", env_file_encoding="utf-8")
    mongodb_url: str | None = None
    redis_url: str = "redis://localhost:6379/0"
    
    db_name: str = "spotify-clone"
    
    # Cache TTL time (SECS)
    cache_ttl_aggregation: int = 600
    cache_ttl_list: int = 300
    cache_ttl_single: int = 1800