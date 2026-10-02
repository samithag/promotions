from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict

# Offer validity dates are Sri Lankan calendar dates.
LOCAL_TZ = ZoneInfo("Asia/Colombo")


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables (or a `.env` file)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./promotions.db"

    # Scraping
    scrape_interval_minutes: int = 60
    user_agent: str = (
        "PromotionsBot/1.0 (+https://github.com/samithag/promotions; collects public card offers)"
    )
    request_timeout_seconds: float = 30.0
    # Pause between requests to the same site, to stay polite.
    request_delay_seconds: float = 1.0
    raw_dir: Path = Path("data/raw")
    raw_keep_per_bank: int = 24

    # POST /api/v1/scrape-runs is disabled unless this is set.
    admin_token: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
