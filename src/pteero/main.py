import asyncio

import disnake

from pteero.bot import PteeroBot
from pteero.core.cache import CacheManager
from pteero.core.config import DATABASE_PATH, settings
from pteero.core.database import DatabaseManager
from pteero.core.http import AsyncHTTPClient
from pteero.core.logger import setup_logging
from pteero.features import RepositoryContainer
from pteero.features.dashboards.cog import DashboardCog
from pteero.features.dashboards.repository import DashboardRepository
from pteero.features.permissions.cog import PermissionsCog
from pteero.features.permissions.repository import PermissionRepository
from pteero.integrations.pterodactyl.client import PterodactylClient


async def main() -> None:
    """Main entry point for the bot."""
    setup_logging()

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Initializes services
    http_client = AsyncHTTPClient()
    cache_manager = CacheManager()
    database = DatabaseManager(DATABASE_PATH)
    repositories = RepositoryContainer(
        permissions=PermissionRepository(database),
        dashboards=DashboardRepository(database),
    )
    pterodactyl_client = PterodactylClient(
        http_client,
        cache_manager,
        settings.pterodactyl_url,
        settings.pterodactyl_api_key.get_secret_value(),
        verify_ssl=settings.pterodactyl_verify_ssl,
    )

    # Initializes the bot
    intents = disnake.Intents.none()
    intents.guilds = True
    bot = PteeroBot(owner_id=settings.discord_owner_id, intents=intents)

    bot.add_cog(
        DashboardCog(
            bot, repositories.dashboards, repositories.permissions, pterodactyl_client
        )
    )
    bot.add_cog(PermissionsCog(bot, repositories.permissions, pterodactyl_client))

    try:
        await http_client.connect()
        await database.connect()
        await repositories.setup_schemas()
        await bot.start(settings.discord_token.get_secret_value())
    finally:
        await http_client.close()
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
