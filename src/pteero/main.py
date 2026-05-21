import asyncio
from pathlib import Path

import disnake

from pteero.bot.bot import PteeroBot
from pteero.core.config import settings
from pteero.core.database import DatabaseManager
from pteero.core.http import AsyncHTTPClient
from pteero.core.logger import setup_logging
from pteero.core.repositories import RepositoryContainer
from pteero.core.repositories.dashboard import DashboardRepository
from pteero.core.repositories.permissions import PermissionRepository
from pteero.services.pterodactyl.client import PterodactylClient

BASE_DIR: Path = Path(__file__).resolve().parent
COGS_PATH: Path = BASE_DIR / "bot" / "cogs"
DATABASE_PATH: Path = BASE_DIR / "data" / "pteero.db"


async def main() -> None:
    """Main entry point for the bot."""
    setup_logging()

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Initializes services
    http_client = AsyncHTTPClient()
    database = DatabaseManager(DATABASE_PATH)
    repositories = RepositoryContainer(
        permissions=PermissionRepository(database),
        dashboards=DashboardRepository(database),
    )
    pterodactl_client = PterodactylClient(
        http_client,
        settings.pterodactyl_url,
        settings.pterodactyl_api_key.get_secret_value(),
        verify_ssl=settings.pterodactyl_verify_ssl,
    )

    # Initializes the bot
    intents = disnake.Intents.none()
    bot = PteeroBot(
        repositories,
        pterodactl_client,
        owner_id=settings.discord_owner_id,
        intents=intents,
    )

    try:
        await http_client.connect()
        await database.connect()
        await repositories.setup_schemas()
        bot.load_cogs(COGS_PATH)
        await bot.start(settings.discord_token.get_secret_value())
    finally:
        await http_client.close()
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
