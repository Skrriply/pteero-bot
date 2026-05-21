from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import disnake

if TYPE_CHECKING:
    from pteero.bot.bot import PteeroBot
    from pteero.core.repositories.permissions import PermissionAction
    from pteero.services.pterodactyl.schemas import ServerListResponse

logger = logging.getLogger(__name__)


async def check_permission(
    bot: PteeroBot,
    user: disnake.User | disnake.Member,
    server_id: str,
    action: PermissionAction,
) -> bool:
    """Evaluates whether the interacting user has the specified permission.

    Args:
        bot: The Discord bot instance.
        user: The Discord user or member to evaluate.
        server_id: The Pterodactyl server ID.
        action: The specific `PermissionAction` flag to verify.

    Returns:
        `True` if the user is authorized, `False` otherwise.
    """
    if await bot.is_owner(user):
        return True

    role_ids = [role.id for role in filter(None, getattr(user, "roles", []))]

    return await bot.permissions.has_server_permission(
        user_id=user.id,
        role_ids=role_ids,
        server_id=server_id,
        action=action,
    )


async def get_server_suggestions(
    servers: ServerListResponse, current: str
) -> dict[str, str]:
    """Provides autocomplete suggestions for Pterodactyl servers.

    Args:
        bot: The Discord bot instance.
        current: The string the user is currently typing.

    Returns:
        A dictionary mapping the formatted server name to its ID, limited to 25.
    """
    matches: dict[str, str] = {}
    current_lower = current.lower()

    for entry in servers.data:
        if (
            current_lower in entry.attributes.name.lower()
            or current_lower in entry.attributes.identifier
        ):
            label = f"{entry.attributes.name[:50]} ({entry.attributes.identifier})"
            matches[label] = entry.attributes.identifier

            if len(matches) >= 25:
                break

    return matches
