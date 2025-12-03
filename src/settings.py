"""Application settings loaded from environment using Pydantic Settings."""
import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Enriched Items API", alias="APP_NAME")
    environment: str = Field(default="local", alias="APP_ENV")
    version: str = "0.1.0"

    meli_base_url: str = Field(default="https://api.mercadolibre.com", alias="MELI_BASE_URL")
    meli_access_token: str | None = Field(default=None, alias="MELI_ACCESS_TOKEN")
    meli_refresh_token: str | None = Field(default=None, alias="MELI_REFRESH_TOKEN")
    meli_client_id: str | None = Field(default=None, alias="MELI_CLIENT_ID")
    meli_client_secret: str | None = Field(default=None, alias="MELI_CLIENT_SECRET")
    meli_redirect_uri: str | None = Field(default=None, alias="MELI_REDIRECT_URI")

    use_meli_mock: bool = True

    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")
    db_path: str = Field(default="data/app.db", alias="APP_DB_PATH")

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    def __init__(self, **data):
        # allow fallback to GOOGLE_API_KEY if GEMINI_API_KEY not set
        if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" in os.environ:
            os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
        super().__init__(**data)


settings = Settings()
