from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./cardvault.db"
    ebay_results_count: int = 10
    price_refresh_interval_hours: int = 24
    playwright_headless: bool = True


settings = Settings()
