from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

import disnake
from disnake.ext import commands

if TYPE_CHECKING:
    from pteero.services.pterodactyl import PterodactylClient

logger = logging.getLogger(__name__)


class PteeroBot(commands.InteractionBot):
    """Discord Bot class."""

    def __init__(
        self,
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
        self.ptero: PterodactylClient = pterodactyl_client

    async def on_ready(self) -> None:
        """Event triggered when the bot successfully connects to Discord."""
        logger.info(f"Bot authorized as '{self.user}' (ID: {self.user.id}).")

    @override
    async def close(self) -> None:
        """Overrides the default close method to close all API HTTP sessions."""
        logger.info("Closing API HTTP sessions...")
        await self.ptero.close()

        await super().close()
