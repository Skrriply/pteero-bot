from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import disnake

from pteero.services.schemas.pterodactyl import PowerSignal

if TYPE_CHECKING:
    from pteero.bot.bot import PteeroBot

logger = logging.getLogger(__name__)


class DashboardView(disnake.ui.View):
    """An interactive view for controlling a Pterodactyl server."""

    def __init__(self, bot: PteeroBot, server_id: str) -> None:
        """Initializes the DashboardView.

        Args:
            bot: The Discord bot instance.
            server_id: The unique identifier of the Pterodactyl server to control.
        """
        super().__init__(timeout=None)
        self.bot: PteeroBot = bot
        self.server_id: str = server_id

    async def _is_owner(self, interaction: disnake.MessageInteraction) -> bool:
        """Checks if the user interacting with the view is the owner of the bot.

        Args:
            interaction: The interaction context from the slash command.

        Returns:
            `True` if the user is the bot owner, `False` otherwise.
        """
        if await self.bot.is_owner(interaction.author):
            return True

        await interaction.response.send_message(
            "⛔ У вас немає необхідних прав, щоб виконати цю дію.", ephemeral=True
        )
        return False

    async def _handle_power_action(
        self, interaction: disnake.MessageInteraction, signal: PowerSignal
    ) -> None:
        """Helper method to process power button presses.

        Args:
            interaction: The interaction context from the slash command.
            signal: The power signal to send to the server.
        """
        await interaction.response.send_message(
            f"⏳ Надсилаю сигнал `{signal.value}` на сервер...", ephemeral=True
        )

        success = await self.bot.ptero.send_power_signal(self.server_id, signal)

        await interaction.edit_original_response(
            f"✅ Команду `{signal.value}` успішно виконано!"
            if success
            else f"❌ Не вдалося виконати команду `{signal.value}`!"
        )

    @disnake.ui.button(
        label="▶️ Запустити",
        style=disnake.ButtonStyle.secondary,
        custom_id="ptero_start",
    )
    async def start_button(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:
        """Handles the start button interaction.

        Args:
            _: The button instance (unused).
            interaction: The interaction context from the slash command.
        """
        await self._handle_power_action(interaction, PowerSignal.START)

    @disnake.ui.button(
        label="🔄 Перезапустити",
        style=disnake.ButtonStyle.secondary,
        custom_id="ptero_restart",
    )
    async def restart_button(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:
        """Handles the restart button interaction.

        Args:
            _: The button instance (unused).
            interaction: The interaction context from the slash command.
        """
        if not await self._is_owner(interaction):
            return

        await self._handle_power_action(interaction, PowerSignal.RESTART)

    @disnake.ui.button(
        label="⏹️ Зупинити", style=disnake.ButtonStyle.secondary, custom_id="ptero_stop"
    )
    async def stop_button(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:
        """Handles the stop button interaction.

        Args:
            _: The button instance (unused).
            interaction: The interaction context from the slash command.
        """
        if not await self._is_owner(interaction):
            return

        await self._handle_power_action(interaction, PowerSignal.STOP)
