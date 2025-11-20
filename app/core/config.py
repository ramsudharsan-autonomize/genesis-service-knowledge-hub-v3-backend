from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGO_URL: str
    DB_NAME: str

    # Storage configuration
    STORAGE_TYPE: str
    STORAGE_ACCOUNT: str
    STORAGE_CONTAINER: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
