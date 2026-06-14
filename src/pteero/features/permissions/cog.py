from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import disnake
from disnake.ext import commands

from pteero.core.i18n import _
from pteero.features.permissions.views.view import PermissionManageView
from pteero.features.utils import get_server_suggestions

if TYPE_CHECKING:
    from pteero.bot import PteeroBot
    from pteero.features.permissions.repository import PermissionRepository
    from pteero.integrations.pterodactyl.client import PterodactylClient

logger = logging.getLogger(__name__)


class PermissionsCog(commands.Cog):
    """Cog for managing users permissions."""

    def __init__(
        self,
        bot: PteeroBot,
        permissions_repository: PermissionRepository,
        pterodactyl_client: PterodactylClient,
    ) -> None:
        """Initializes the class.

        Args:
            bot: The Discord bot instance.
            permissions_repository: The database repository for managing permissions.
            pterodactyl_client: The initialized client for the Pterodactyl.
        """
        self.bot: PteeroBot = bot
        self.permissions: PermissionRepository = permissions_repository
        self.ptero: PterodactylClient = pterodactyl_client

    @commands.is_owner()
    @commands.slash_command(name="permissions", description=_("cmd_perm_base_desc"))
    async def permissions_base(self, _: disnake.ApplicationCommandInteraction) -> None:
        """
        Base slash command for managing server permissions.

        Args:
            _: The interaction context from the slash command (unused).
        """
        pass

    @permissions_base.sub_command(name="manage", description=_("cmd_perm_manage_desc"))
    async def manage_permission(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        entity: disnake.User | disnake.Member | disnake.Role,
        server_id: str,
    ) -> None:
        """Sends an interactive dashboard to manage permissions.

        Args:
            interaction: The interaction context from the slash command.
            entity: The Discord user, member or role receiving the permissions.
            server_id: The Pterodactyl server ID being targeted.
        """
        await interaction.response.defer(ephemeral=True)

        server_info = await self.ptero.get_server_info(server_id)
        if not server_info and server_id != "ALL":
            embed = disnake.Embed(
                title=_("error_title"),
                description=_("error_connect"),
                color=disnake.Color.yellow(),
            )
            await interaction.followup.send(embed=embed)
            return

        view = PermissionManageView(
            self.bot, self.permissions, self.ptero, entity, server_id
        )
        await view.load_state()

        embed = await view.get_embed()
        await interaction.followup.send(embed=embed, view=view)

    @manage_permission.autocomplete("server_id")
    async def manage_permission_autocomp(
        self, interaction: disnake.ApplicationCommandInteraction, current: str
    ) -> dict[str, str]:
        """
        Autocomplete for the `server_id` argument of the `manage` command.

        Args:
            interaction: The Discord interaction object (unused).
            current: The string the user is currently typing.

        Returns:
            A dictionary of autocomplete suggestions.
        """
        servers = await self.ptero.get_servers()
        suggestions: dict[str, str] = {}

        if not servers:
            return suggestions

        global_label = _("autocomplete_all_servers")
        current_lower = current.lower()

        if current_lower in global_label.lower() or current_lower in "all":
            suggestions[global_label] = "ALL"

        api_suggestions = await get_server_suggestions(servers, current)
        suggestions.update(api_suggestions)

        return dict(list(suggestions.items())[:25])
