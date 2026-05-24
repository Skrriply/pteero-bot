from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import disnake

from pteero.features.permissions.repository import PermissionAction
from pteero.features.permissions.views.formatters import (
    PERMISSIONS_LABELS,
    build_permissions_embed,
)
from pteero.features.utils import extract_role_ids

if TYPE_CHECKING:
    from pteero.bot import PteeroBot


class PermissionButton(disnake.ui.Button["PermissionManageView"]):
    """Button for handling permission actions."""

    def __init__(
        self, permission: PermissionAction, is_allowed: bool, is_denied: bool
    ) -> None:
        """Initializes the class.

        Args:
            permission: The permission controlled by this button.
            is_allowed: Whether the permission is allowed locally.
            is_denied: Whether the permission is denied locally.
        """
        style = (
            disnake.ButtonStyle.success
            if is_allowed
            else disnake.ButtonStyle.danger
            if is_denied
            else disnake.ButtonStyle.secondary
        )
        emoji, label = PERMISSIONS_LABELS[permission]

        super().__init__(
            style=style,
            label=label,
            emoji=emoji,
            custom_id=f"permission_{permission.name}",
        )
        self.permission: PermissionAction = permission

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        """Handles the button click interaction.

        Args:
            interaction: The interaction context from the button press.
        """
        self.view.toggle_permission(self.permission)
        await self.view.bot.permissions.set_permission(
            self.view.entity.id,
            self.view.entity_type,
            self.view.allowed,
            self.view.denied,
            self.view.server_id,
        )

        embed = await self.view.get_embed()
        await interaction.response.edit_message(embed=embed, view=self.view)


class PermissionManageView(disnake.ui.View):
    """A permissions view."""

    def __init__(
        self,
        bot: PteeroBot,
        entity: disnake.User | disnake.Member | disnake.Role,
        server_id: str,
    ) -> None:
        """Initializes the class.

        Args:
            bot: The Discord bot instance.
            entity: The target Discord user, member, or role to modify.
            server_id: The unique identifier of the Pterodactyl server or "ALL".
        """
        super().__init__(timeout=180)
        self.bot: PteeroBot = bot
        self.entity: disnake.User | disnake.Member | disnake.Role = entity
        self.entity_type: Literal["user", "role"] = (
            "role" if isinstance(entity, disnake.Role) else "user"
        )
        self.server_id: str = server_id
        self.allowed: PermissionAction = PermissionAction.NONE
        self.denied: PermissionAction = PermissionAction.NONE

    def _add_buttons(self) -> None:
        """Rebuilds the interactive button menu layout."""
        self.clear_items()

        for permission in PermissionAction:
            if permission != PermissionAction.NONE:
                self.add_item(
                    PermissionButton(
                        permission,
                        permission in self.allowed,
                        permission in self.denied,
                    )
                )

    async def load_state(self) -> None:
        """Loads raw bitwise permissions for the entity from the database."""
        self.allowed, self.denied = await self.bot.permissions.get_raw_permissions(
            self.entity.id, self.server_id
        )

    def toggle_permission(self, permission: PermissionAction) -> None:
        """Toggles permission state through Allowed -> Denied -> Not set.

        Args:
            permission: The targeted permission to switch.
        """
        if permission in self.allowed:
            self.allowed &= ~permission
            self.denied |= permission
        elif permission in self.denied:
            self.denied &= ~permission
        else:
            self.allowed |= permission

    async def get_embed(self) -> disnake.Embed:
        """Refreshes the button layout and creates the embed.

        Returns:
            A `disnake.Embed` object.
        """
        self._add_buttons()

        role_ids: set[int] = extract_role_ids(self.entity)
        sources = await self.bot.permissions.get_permission_sources(
            self.entity.id, self.server_id, role_ids=role_ids
        )
        is_owner = (
            False
            if isinstance(self.entity, disnake.Role)
            else await self.bot.is_owner(self.entity)
        )
        server_info = await self.bot.ptero.get_server_info(self.server_id)

        embed = build_permissions_embed(
            self.entity,
            self.server_id,
            self.allowed,
            self.denied,
            sources,
            is_owner,
            server_info.name if server_info else None,
        )

        return embed
