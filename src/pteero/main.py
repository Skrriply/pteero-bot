import asyncio

import disnake

from pteero.bot.bot import PteeroBot
from pteero.core.config import settings
from pteero.core.logger import setup_logging
from pteero.services.pterodactyl import PterodactylClient


async def main() -> None:
    """Main entry point for the bot."""
    setup_logging()

    # Initializes services
    pterodactl_client = PterodactylClient(
        settings.pterodactyl_url,
        settings.pterodactyl_api_key.get_secret_value(),
        verify_ssl=settings.pterodactyl_verify_ssl,
    )

    # Initializes and starts the bot
    intents = disnake.Intents.none()
    bot = PteeroBot(
        pterodactl_client, owner_id=settings.discord_owner_id, intents=intents
    )
    await bot.start(settings.discord_token.get_secret_value())


if __name__ == "__main__":
    asyncio.run(main())
