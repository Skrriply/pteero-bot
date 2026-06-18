from __future__ import annotations

from typing import TYPE_CHECKING

import disnake

from pteero.core.i18n import _
from pteero.features.permissions.repository import PermissionAction
from pteero.features.utils import check_permission
from pteero.integrations.pterodactyl.schemas import PowerSignal

if TYPE_CHECKING:
    from pteero.integrations.pterodactyl.client import PterodactylClient

POWER_ACTIONS: dict[PowerSignal, tuple[PermissionAction, str, str]] = {
    PowerSignal.START: (
        PermissionAction.START,
        _("emoji_action_start"),
        _("action_start"),
    ),
    PowerSignal.RESTART: (
        PermissionAction.RESTART,
        _("emoji_action_restart"),
        _("action_restart"),
    ),
    PowerSignal.STOP: (
        PermissionAction.STOP,
        _("emoji_action_stop"),
        _("action_stop"),
    ),
    PowerSignal.KILL: (
        PermissionAction.KILL,
        _("emoji_action_kill"),
        _("action_kill"),
    ),
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
            self.view.bot,
            self.view.permissions,
            interaction.author,
            self.view.server_id,
            self.permission,
        ):
            embed = disnake.Embed(
                title=_("error_title"),
                description=_("error_no_permission"),
                color=disnake.Color.yellow(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.send_message(
            _("signal_sending", signal=self.signal.value), ephemeral=True
        )
        success = await self.view.ptero.send_power_signal(
            self.view.server_id, self.signal
        )

        await interaction.edit_original_response(
            _("signal_success", signal=self.signal.value)
            if success
            else _("signal_error", signal=self.signal.value)
        )


class DashboardView(disnake.ui.View):
    """A dashboard view for a Pterodactyl server."""

    def __init__(self, pterodactyl_client: PterodactylClient, server_id: str) -> None:
        """Initializes the class.

        Args:
            pterodactyl_client: The client for the Pterodactyl.
            server_id: The unique identifier of the Pterodactyl server to control.
        """
        super().__init__(timeout=None)
        self.ptero: PterodactylClient = pterodactyl_client
        self.server_id: str = server_id

        for key in POWER_ACTIONS:
            self.add_item(PowerButton(key))
