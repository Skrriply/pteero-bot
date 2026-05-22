from __future__ import annotations

from typing import TYPE_CHECKING

import disnake

from pteero.bot.utils import check_permission
from pteero.core.repositories.permissions import PermissionAction
from pteero.services.pterodactyl.schemas import PowerSignal

if TYPE_CHECKING:
    from pteero.bot.bot import PteeroBot

POWER_ACTIONS: dict[PowerSignal, tuple[PermissionAction, str, str]] = {
    PowerSignal.START: (PermissionAction.START, "▶️", "Запустити"),
    PowerSignal.RESTART: (PermissionAction.RESTART, "🔄", "Перезапустити"),
    PowerSignal.STOP: (PermissionAction.STOP, "⏹️", "Зупинити"),
    PowerSignal.KILL: (PermissionAction.KILL, "☠️", "Примусово зупинити"),
}


class PowerButton(disnake.ui.Button):
    """Button for handling Pterodactyl power actions."""

    def __init__(self, signal: PowerSignal) -> None:
        """Initializes the class.

        Args:
            signal: The power signal configuration determining the button's behavior.
        """
        self.signal: PowerSignal = signal
        self.permission, emoji, label = POWER_ACTIONS[signal]
        super().__init__(
            label=label,
            emoji=emoji,
            style=disnake.ButtonStyle.secondary,
            custom_id=f"ptero_{self.signal.value}",
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        """Handles the button click interaction.

        Args:
            interaction: The interaction context from the button press.
        """
        if not await check_permission(
            self.view.bot, interaction.author, self.view.server_id, self.permission
        ):
            embed = disnake.Embed(
                title="⚠️ Помилка",
                description="У вас немає необхідних дозволів, щоби виконати цю дію.",
                color=disnake.Color.yellow(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.send_message(
            f"⏳ Надсилаю сигнал `{self.signal.value}`...", ephemeral=True
        )
        success = await self.view.bot.ptero.send_power_signal(
            self.view.server_id, self.signal
        )

        await interaction.edit_original_response(
            f"✅ Команду `{self.signal.value}` успішно виконано!"
            if success
            else f"❌ Не вдалося виконати команду `{self.signal.value}`!"
        )


class DashboardView(disnake.ui.View):
    """A dashboard view for a Pterodactyl server."""

    def __init__(self, bot: PteeroBot, server_id: str) -> None:
        """Initializes the class.

        Args:
            bot: The Discord bot instance.
            server_id: The unique identifier of the Pterodactyl server to control.
        """
        super().__init__(timeout=None)
        self.bot: PteeroBot = bot
        self.server_id: str = server_id

        for key in POWER_ACTIONS:
            self.add_item(PowerButton(key))
