from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import disnake
from disnake.ext import commands

from pteero.bot.utils import get_server_suggestions
from pteero.core.repositories.permissions import PermissionAction

if TYPE_CHECKING:
    from pteero.bot.bot import PteeroBot

logger = logging.getLogger(__name__)


class PermissionsCog(commands.Cog):
    """Cog for managing bot and server access permissions."""

    def __init__(self, bot: PteeroBot) -> None:
        """Initializes the class.

        Args:
            bot: The Discord bot instance.
        """
        self.bot: PteeroBot = bot

    @commands.is_owner()
    @commands.slash_command(name="permissions")
    async def permissions_base(self, _: disnake.ApplicationCommandInteraction) -> None:
        """Base slash command for managing server permissions. (Bot owner only)"""
        pass

    @permissions_base.sub_command(
        name="grant",
        description="🛡️ Надає користувачу або ролі права доступу.",
    )
    async def grant_permission(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        entity: disnake.User | disnake.Role,
        server_id: str,
        can_start: bool = False,
        can_stop: bool = False,
        can_restart: bool = False,
        can_kill: bool = False,
        can_spawn_dashboards: bool = False,
    ) -> None:
        """Grants or updates server permissions for a specific user or role.

        Args:
            interaction: The interaction context from the slash command.
            entity: The Discord user or role receiving the permissions.
            server_id: The Pterodactyl server ID being targeted.
            can_start: Grants permission to start the server.
            can_stop: Grants permission to stop the server.
            can_restart: Grants permission to restart the server.
            can_kill: Grants permission to forcefully kill the server.
            can_spawn_dashboards: Grants permission to generate server dashboards.
        """
        await interaction.response.defer(ephemeral=True)

        logger.info(
            f"User '{interaction.author}' ({interaction.author.id}) is updating permissions "
            f"for entity '{entity}' ({entity.id}) for server '{server_id}'."
        )

        entity_type = "role" if isinstance(entity, disnake.Role) else "user"
        action_mask = PermissionAction.from_booleans(
            can_start, can_stop, can_restart, can_kill, can_spawn_dashboards
        )

        try:
            await self.bot.permissions.set_permission(
                entity.id, entity_type, server_id, action_mask
            )

            states = {
                "▶️ Запуск": can_start,
                "⏹️ Зупинка": can_stop,
                "🔄 Перезапуск": can_restart,
                "☠️ Примусова зупинка": can_kill,
                "📊 Створення панелей керування": can_spawn_dashboards,
            }
            perms_text = "\n".join(
                f"{name}: {'✅' if has_perm else '❌'}"
                for name, has_perm in states.items()
            )

            embed = disnake.Embed(
                title="🛡️ Права оновлено",
                description=f"Права для {entity.mention} на сервері `{server_id}` були успішно збережені.",
                color=disnake.Color.green(),
            )
            embed.add_field(name="Поточні дозволи:", value=perms_text)

            await interaction.followup.send(embed=embed)
        except disnake.HTTPException as e:
            logger.error(
                f"Failed to set permissions for entity '{entity.id}' for server {server_id}: {e}"
            )
            embed = disnake.Embed(
                title="⚠️ Помилка",
                description=f"Не надати права для {entity.mention}.",
                color=disnake.Color.yellow(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @grant_permission.autocomplete("server_id")
    async def grant_permission_autocomp(
        self, _: disnake.ApplicationCommandInteraction, current: str
    ) -> dict[str, str]:
        """
        Autocomplete for the `server_id` argument of the `grant` command.

        Args:
            _: The Discord interaction object (unused).
            current: The string the user is currently typing.

        Returns:
            A dictionary of autocomplete suggestions.
        """
        servers = await self.bot.ptero.get_servers()

        if not servers:
            return {}

        return await get_server_suggestions(servers, current)


def setup(bot: PteeroBot) -> None:
    """Loads the `PermissionsCog` into the bot.

    Args:
        bot: The Discord bot instance.
    """
    bot.add_cog(PermissionsCog(bot))
