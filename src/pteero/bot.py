from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import disnake
from disnake.ext import commands

if TYPE_CHECKING:
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
