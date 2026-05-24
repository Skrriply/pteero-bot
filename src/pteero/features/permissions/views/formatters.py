from collections import defaultdict
from typing import Any

import disnake

from pteero.core.i18n import _
from pteero.features.permissions.repository import PermissionAction

PERMISSIONS_LABELS: dict[PermissionAction, tuple[str, str]] = {
    PermissionAction.START: (
        _("emoji_action_start"),
        _("action_start"),
    ),
    PermissionAction.RESTART: (
        _("emoji_action_restart"),
        _("action_restart"),
    ),
    PermissionAction.STOP: (
        _("emoji_action_stop"),
        _("action_stop"),
    ),
    PermissionAction.KILL: (
        _("emoji_action_kill"),
        _("action_kill"),
    ),
    PermissionAction.SPAWN_DASHBOARDS: (
        _("emoji_action_spawn"),
        _("action_spawn_dashboards"),
    ),
}


def build_permissions_embed(
    entity: disnake.User | disnake.Member | disnake.Role,
    server_id: str,
    allowed: PermissionAction,
    denied: PermissionAction,
    sources: list[dict[str, Any]],
    is_owner: bool = False,
    server_name: str | None = None,
) -> disnake.Embed:
    """Builds a permissions embed.

    Args:
        entity: The Discord user, member or role.
        server_id: The unique identifier for the Pterodactyl server or "ALL".
        allowed: Local bitwise flags for explicitly allowed actions.
        denied: Local bitwise flags for explicitly denied actions.
        sources: Raw database rows indicating parent/inherited rules.
        is_owner (optional): Whether the target user is an owner. Defaults to `False`.
        server_name (optional): The human-readable name of the server. Defaults to `None`.

    Returns:
        A `disnake.Embed` object.
    """
    server_display = (
        _("perm_display_all")
        if server_id == "ALL"
        else (f"{server_name}(`{server_id}`)" if server_name else f"`{server_id}`")
    )

    embed = disnake.Embed(
        title=_("perm_embed_title"),
        description=_(
            "perm_embed_desc", entity=entity.mention, server_name=server_display
        ),
        color=disnake.Color.blurple(),
    )

    if is_owner:
        embed.add_field(
            name=_("perm_embed_owner_name"),
            value=_("perm_embed_owner_value"),
            inline=False,
        )
        return embed

    guild_id = (
        entity.guild.id if isinstance(entity, (disnake.Member, disnake.Role)) else None
    )
    allow_sources: dict[PermissionAction, list[str]] = defaultdict(list)
    deny_sources: dict[PermissionAction, list[str]] = defaultdict(list)

    for row in sources:
        is_local = row["server_id"] == server_id
        is_self = row["entity_id"] == entity.id
        is_global = row["server_id"] == "ALL"

        if is_local and is_self:
            continue

        if is_self:
            src_name = (
                _("perm_src_personal_global")
                if isinstance(entity, (disnake.User, disnake.Member))
                else _("perm_src_role_global")
            )
        else:
            role_mention = (
                "@everyone"
                if row["entity_id"] == guild_id
                else f"<@&{row['entity_id']}>"
            )
            src_name = _("perm_src_role_local", role=role_mention)

            if is_global:
                src_name += _("perm_src_for_all")

        row_allows = PermissionAction(row["allows"])
        row_denies = PermissionAction(row["denies"])

        for permission in PERMISSIONS_LABELS:
            if permission in row_allows:
                allow_sources[permission].append(src_name)
            if permission in row_denies:
                deny_sources[permission].append(src_name)

    perms_text: list[str] = []
    for action, (emoji, text) in PERMISSIONS_LABELS.items():
        if action in allowed:
            status = _("perm_status_allowed")
        elif action in denied:
            status = _("perm_status_denied")
        elif action_allow_srcs := allow_sources.get(action):
            sources_str = ", ".join(dict.fromkeys(action_allow_srcs))
            status = _("perm_status_allowed_inherited", sources=sources_str)
        elif action_deny_srcs := deny_sources.get(action):
            sources_str = ", ".join(dict.fromkeys(action_deny_srcs))
            status = _("perm_status_denied_inherited", sources=sources_str)
        else:
            status = _("perm_status_not_set")

        perms_text.append(f"{emoji} **{text}** - {status}")

    embed.add_field(
        name=_("perm_embed_field_name"), value="\n".join(perms_text), inline=False
    )
    embed.set_footer(text=_("perm_embed_footer"))

    return embed
