from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Use top level .env file (one level above ./backend/)
    model_config = SettingsConfigDict(env_file='../.env', env_file_encoding='utf-8')

settings = Settings()