from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # .env dosyasından OPENAI_API_KEY değişkenini okur.
    OPENAI_API_KEY: str

    # .env dosyasının konumunu belirtir.
    model_config = SettingsConfigDict(env_file="../.env")

# Kullanmak için bu nesneyi import edeceğiz
settings = Settings()