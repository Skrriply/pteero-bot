from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration class for the bot settings."""

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
