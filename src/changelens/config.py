from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "changelens"
    app_env: str = "development"
    debug: bool = False
    secret_key: str = Field(..., min_length=32)

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    webhook_secret_github_actions: str = ""
    webhook_secret_alertmanager: str = ""

    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "changelens"

    log_level: str = "INFO"


settings = Settings()
