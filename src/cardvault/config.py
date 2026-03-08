from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./cardvault.db"
    ebay_app_id: str = ""
    ebay_client_secret: str = ""
    ebay_results_count: int = 20


settings = Settings()
