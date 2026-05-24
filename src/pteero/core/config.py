from pathlib import Path

from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR: Path = Path(__file__).resolve().parent.parent
LOCALES_PATH: Path = BASE_DIR / "locales"
COGS_PATH: Path = BASE_DIR / "features"
DATABASE_PATH: Path = BASE_DIR / "data" / "pteero.db"


class Settings(BaseSettings):
    """Configuration class for the bot settings."""

    # General
    language: str = "en"

    # Discord
    discord_token: SecretStr
    discord_owner_id: int

    # Pterodactyl
    pterodactyl_url: HttpUrl
    pterodactyl_api_key: SecretStr
    pterodactyl_verify_ssl: bool

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()  # pyright: ignore [reportCallIssue]
