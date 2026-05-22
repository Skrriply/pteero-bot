from collections import defaultdict
from typing import Any

import disnake

from pteero.core.repositories.permissions import PermissionAction

ACTION_LABELS: dict[PermissionAction, tuple[str, str]] = {
    PermissionAction.START: ("▶️", "Запустити"),
    PermissionAction.RESTART: ("🔄", "Перезапустити"),
    PermissionAction.STOP: ("⏹️", "Зупинити"),
    PermissionAction.KILL: ("☠️", "Примусово зупинити"),
    PermissionAction.SPAWN_DASHBOARDS: ("📊", "Створення панелей"),
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
        "**Усі сервери**"
        if server_id == "ALL"
        else (f"{server_name}(`{server_id}`)" if server_name else f"`{server_id}`")
    )

    embed = disnake.Embed(
        title="🛡️ Керування дозволами",
        description=f"Налаштування дозволів для {entity.mention} до {server_display}.",
        color=disnake.Color.blurple(),
    )

    if is_owner:
        embed.add_field(
            name="👑 Ви є власником бота",
            value="Ви маєте безумовний і повний доступ до всіх дій.",
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
                "особистого глобального правила"
                if isinstance(entity, (disnake.User, disnake.Member))
                else "глобального правила цієї ролі"
            )
        else:
            role_repr = (
                "@everyone"
                if row["entity_id"] == guild_id
                else f"<@&{row['entity_id']}>"
            )
            src_name = f"дозволів ролі {role_repr}"

            if is_global:
                src_name += " для всіх серверів"

        row_allows = PermissionAction(row["allows"])
        row_denies = PermissionAction(row["denies"])

        for permission in ACTION_LABELS:
            if permission in row_allows:
                allow_sources[permission].append(src_name)
            if permission in row_denies:
                deny_sources[permission].append(src_name)

    perms_text: list[str] = []
    for action, (emoji, text) in ACTION_LABELS.items():
        if action in allowed:
            status = "✅ Дозволено"
        elif action in denied:
            status = "❌ Заборонено"
        elif action_allow_srcs := allow_sources.get(action):
            sources_str = ", ".join(dict.fromkeys(action_allow_srcs))
            status = f"✅ Дозволено *(успадковано від {sources_str})*"
        elif action_deny_srcs := deny_sources.get(action):
            sources_str = ", ".join(dict.fromkeys(action_deny_srcs))
            status = f"❌ Заборонено *(успадковано від {sources_str})*"
        else:
            status = "❔Не задано"

        perms_text.append(f"{emoji} **{text}** - {status}")

    embed.add_field(name="Дозволи:", value="\n".join(perms_text), inline=False)
    embed.set_footer(text="✅ Дозволено • ❌ Заборонено • ❔ Не задано")

    return embed
