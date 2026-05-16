from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

import disnake
from disnake.ext import commands

if TYPE_CHECKING:
    from pathlib import Path

    from pteero.core.repositories import RepositoryContainer
    from pteero.core.repositories.dashboard import DashboardRepository
    from pteero.core.repositories.permissions import PermissionRepository
    from pteero.services.pterodactyl import PterodactylClient

logger = logging.getLogger(__name__)


class PteeroBot(commands.InteractionBot):
    """Discord Bot class."""

    def __init__(
        self,
        repositories: RepositoryContainer,
        pterodactyl_client: PterodactylClient,
        owner_id: int | None = None,
        intents: disnake.Intents | None = None,
    ) -> None:
        """Initializes the class.

        Args:
            pterodactyl_client: The initialized client for the Pterodactyl.
            owner_id: The Discord ID of the bot owner. Used for owner-only commands.
            intents: The specific Discord gateway intents.
        """
        super().__init__(owner_id=owner_id, intents=intents)
        self.permissions: PermissionRepository = repositories.permissions
        self.dashboards: DashboardRepository = repositories.dashboards
        self.ptero: PterodactylClient = pterodactyl_client

    async def on_ready(self) -> None:
        """Event triggered when the bot successfully connects to Discord."""
        logger.info(f"Bot authorized as '{self.user}' (ID: {self.user.id}).")

    def load_cogs(self, cogs_dir: Path) -> None:
        """
        Discovers and loads all cogs from a directory.

        Args:
            cogs_dir: The absolute path to the cogs directory.
        """
        logger.info(f"Loading cogs from '{cogs_dir}'...")

        if not cogs_dir.exists():
            logger.info("The directory doesn't exist! Skipping loading...")
            return

        for filename in cogs_dir.iterdir():
            if not filename.name.endswith(".py") or filename.name.startswith("_"):
                continue

            try:
                cog_name = filename.name[:-3]
                logger.info(f"Cog '{cog_name}' has been loaded!")
                self.load_extension(f"pteero.bot.cogs.{cog_name}")
            except commands.ExtensionError as e:
                logger.error(f"Failed to load the cog: '{filename}'. Error: {e}")

    @override
    async def close(self) -> None:
        """Overrides the default close method to close all API HTTP sessions."""
        logger.info("Closing API HTTP sessions...")
        await self.ptero.close()
        await super().close()
