from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import disnake

from pteero.bot.utils import check_permission
from pteero.core.repositories.permissions import PermissionAction
from pteero.services.pterodactyl.schemas import PowerSignal

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

    async def _require_permission(
        self, interaction: disnake.MessageInteraction, action: PermissionAction
    ) -> bool:
        """Validates permissions and sends a UI error if unauthorized."""
        is_authorized = await check_permission(
            self.bot, interaction.author, self.server_id, action
        )

        if not is_authorized:
            embed = disnake.Embed(
                title="⚠️ Помилка",
                description="У вас немає необхідних прав, щоб виконати цю дію.",
                color=disnake.Color.yellow(),
            )
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            return False

        return True

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
            interaction: The interaction context from the button press.
        """
        if not await self._require_permission(interaction, PermissionAction.START):
            return

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
            interaction: The interaction context from the button press.
        """
        if not await self._require_permission(interaction, PermissionAction.RESTART):
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
            interaction: The interaction context from the button press.
        """
        if not await self._require_permission(interaction, PermissionAction.STOP):
            return

        await self._handle_power_action(interaction, PowerSignal.STOP)

    @disnake.ui.button(
        label="☠️ Примусово зупинити",
        style=disnake.ButtonStyle.secondary,
        custom_id="ptero_kill",
    )
    async def kill_button(
        self, _: disnake.ui.Button, interaction: disnake.MessageInteraction
    ) -> None:
        """Handles the stop button interaction.

        Args:
            _: The button instance (unused).
            interaction: The interaction context from the button press.
        """
        if not await self._require_permission(interaction, PermissionAction.KILL):
            return

        await self._handle_power_action(interaction, PowerSignal.KILL)
