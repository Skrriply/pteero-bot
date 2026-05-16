from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import disnake

if TYPE_CHECKING:
    from pteero.bot.bot import PteeroBot
    from pteero.core.repositories.permissions import PermissionAction

logger = logging.getLogger(__name__)


async def check_permission(
    bot: PteeroBot,
    interaction: disnake.Interaction,
    server_id: str,
    action: PermissionAction,
) -> bool:
    """Evaluates whether the interacting user has the specified permission.

    Args:
        bot: The Discord bot instance.
        interaction: The interaction context.
        server_id: The Pterodactyl server ID.
        action: The specific `PermissionAction` flag to verify.

    Returns:
        `True` if the user is authorized, `False` otherwise.
    """
    if await bot.is_owner(interaction.author):
        return True

    role_ids = [
        role.id for role in filter(None, getattr(interaction.author, "roles", []))
    ]

    is_authorized = await bot.permissions.has_server_permission(
        user_id=interaction.author.id,
        role_ids=role_ids,
        server_id=server_id,
        action=action,
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
