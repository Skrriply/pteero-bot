from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import disnake
from disnake.ext import commands

if TYPE_CHECKING:
    from pathlib import Path

    from pteero.features import RepositoryContainer
    from pteero.features.dashboards.repository import DashboardRepository
    from pteero.features.permissions.repository import PermissionRepository
    from pteero.integrations.pterodactyl.client import PterodactylClient

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

        if not cogs_dir.exists() or not cogs_dir.is_dir():
            logger.info("The directory doesn't exist! Skipping loading...")
            return

        for cog_file in cogs_dir.rglob("cog.py"):
            feature_name = cog_file.parent.name

            try:
                self.load_extension(f"pteero.features.{feature_name}.cog")
                logger.info(f"Cog '{feature_name}' has been loaded!")
            except commands.ExtensionError as e:
                logger.error(f"Failed to load the cog: '{cog_file}'. Error: {e}")
