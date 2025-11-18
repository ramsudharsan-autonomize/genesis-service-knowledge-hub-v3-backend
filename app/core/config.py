from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MONGO_URL: str
    DB_NAME: str
    PORT: int

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()