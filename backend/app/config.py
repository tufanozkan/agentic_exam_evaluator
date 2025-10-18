#backend/app/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    
    model_config = SettingsConfigDict(
        env_file=".env"
    )

settings = Settings()