from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Use top level .env file (one level above ./backend/) to add one-liner:
    # MONGODB_URL="yourconnectionstring"
    model_config = SettingsConfigDict(env_file='../.env', env_file_encoding='utf-8')

    db_name: str = "spotify-clone"
    
settings = Settings()