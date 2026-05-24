from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import disnake

if TYPE_CHECKING:
    from pteero.bot.bot import PteeroBot
    from pteero.core.repositories.permissions import PermissionAction
    from pteero.integrations.pterodactyl.schemas import ServerListResponse

logger = logging.getLogger(__name__)


def extract_role_ids(entity: disnake.User | disnake.Member | disnake.Role) -> set[int]:
    """Safely extracts role IDs and the @everyone (guild ID) role from an entity.

    Args:
        entity: The Discord user, member or role.

    Returns:
        A set of unique role identifiers associated with the entity.
    """
    role_ids: set[int] = set()

    if isinstance(entity, disnake.Member):
        role_ids = {role.id for role in filter(None, entity.roles)}
        role_ids.add(entity.guild.id)

    return role_ids


async def check_permission(
    bot: PteeroBot,
    user: disnake.User | disnake.Member,
    server_id: str,
    permission: PermissionAction,
) -> bool:
    """Evaluates whether the interacting user has the specified permission.

    Args:
        bot: The Discord bot instance.
        user: The Discord user or member to evaluate.
        server_id: The Pterodactyl server ID.
        permission: The specific `PermissionAction` flag to verify.

    Returns:
        `True` if the user is authorized, `False` otherwise.
    """
    if await bot.is_owner(user):
        return True

    return await bot.permissions.has_server_permission(
        user.id,
        permission,
        server_id,
        role_ids=extract_role_ids(user),
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
