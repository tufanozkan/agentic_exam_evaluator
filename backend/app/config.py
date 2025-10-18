from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    
    model_config = SettingsConfigDict(
        env_file=".env"  # Sadece ".env" yeterli, Pydantic otomatik bulur
    )

settings = Settings()