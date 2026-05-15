import asyncio
from pathlib import Path

import disnake

from pteero.bot.bot import PteeroBot
from pteero.core.config import settings
from pteero.core.database import DatabaseManager
from pteero.core.logger import setup_logging
from pteero.services.pterodactyl import PterodactylClient

BASE_DIR: Path = Path(__file__).resolve().parent
COGS_PATH: Path = BASE_DIR / "bot" / "cogs"
DATABASE_PATH: Path = BASE_DIR / "data" / "pteero.db"


async def main() -> None:
    """Main entry point for the bot."""
    setup_logging()

    # Initializes services
    database = DatabaseManager(DATABASE_PATH)
    pterodactl_client = PterodactylClient(
        settings.pterodactyl_url,
        settings.pterodactyl_api_key.get_secret_value(),
        verify_ssl=settings.pterodactyl_verify_ssl,
    )

    # Initializes the bot
    intents = disnake.Intents.none()
    bot = PteeroBot(
        database, pterodactl_client, owner_id=settings.discord_owner_id, intents=intents
    )

    try:
        await database.connect()
        await pterodactl_client.connect()
        bot.load_cogs(COGS_PATH)
        await bot.start(settings.discord_token.get_secret_value())
    finally:
        await pterodactl_client.close()
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
