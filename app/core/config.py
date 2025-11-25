from pydantic_settings import BaseSettings, SettingsConfigDict

from genesis_common_utility.config.app_config import AppConfig


class Settings(BaseSettings):
    APP_NAME: str
    TELEMETRY_ENDPOINT: str
    ENVIRONMENT: str
    LOG_DESTINATION: str

    # MongoDB Configuration
    MONGO_URL: str
    DB_NAME: str

    # Storage Configuration
    STORAGE_TYPE: str
    STORAGE_ACCOUNT: str
    STORAGE_CONTAINER: str

    # Flexstore Service Configuration
    FLEXSTORE_SERVICE_BASE_URL: str

    # Pipeline Configuration (LangFlow)
    PIPELINE_API_KEY: str
    PIPELINE_BASE_URL: str
    PIPELINE_RUN_TIMEOUT_SECONDS: int = 300  # Default 5 minutes

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

# Config registration for genesis common utility
AppConfig.register_configs(
    {
        "FLEXSTORE_SERVICE_BASE_URL": AppConfig.validators.non_empty_string,
    }
)
