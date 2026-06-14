from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

logger = logging.getLogger(__name__)


class PteeroBot(commands.InteractionBot):
    """Discord Bot class."""

    def __init__(
        self, owner_id: int | None = None, intents: disnake.Intents | None = None
    ) -> None:
        """Initializes the class.

        Args:
            owner_id: The Discord ID of the bot owner. Used for owner-only commands.
            intents: The specific Discord gateway intents.
        """
        super().__init__(owner_id=owner_id, intents=intents)

    async def on_ready(self) -> None:
        """Event triggered when the bot successfully connects to Discord."""
        logger.info(f"Bot authorized as '{self.user}' (ID: {self.user.id}).")
