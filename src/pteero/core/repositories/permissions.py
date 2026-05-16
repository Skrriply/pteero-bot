from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import IntFlag, auto
from typing import TYPE_CHECKING, Literal, Self

if TYPE_CHECKING:
    from pteero.core.database import DatabaseManager

logger = logging.getLogger(__name__)


class PermissionAction(IntFlag):
    """Bitmask flags representing discrete server permissions."""

    NONE = 0
    START = auto()  # 1
    STOP = auto()  # 2
    RESTART = auto()  # 4
    KILL = auto()  # 8
    SPAWN_DASHBOARDS = auto()  # 16

    @classmethod
    def from_booleans(
        cls: type[Self],
        start: bool,
        stop: bool,
        restart: bool,
        kill: bool,
        spawn_dashboards: bool,
    ) -> PermissionAction:
        """Constructs a bitmask from boolean flags.

        Args:
            start: Whether the user can start the server.
            stop: Whether the user can stop the server.
            restart: Whether the user can restart the server.
            kill: Whether the user can forcibly kill the server.
            spawn_dashboards: Whether the user can spawn new control dashboards.

        Returns:
            A combined `PermissionAction` flag representing all truthy inputs.
        """
        mask = cls.NONE
        if start:
            mask |= cls.START
        if stop:
            mask |= cls.STOP
        if restart:
            mask |= cls.RESTART
        if kill:
            mask |= cls.KILL
        if spawn_dashboards:
            mask |= cls.SPAWN_DASHBOARDS

        return mask


@dataclass(frozen=True, slots=True)
class PermissionRecord:
    """Domain model representing a set of permissions for a specific Discord entity."""

    entity_id: int
    entity_type: Literal["user", "role"]
    server_id: str
    permissions: PermissionAction


class PermissionRepository:
    """Handles all database operations related to user and role permissions."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initializes the class.

        Args:
            database_manager: The database manager instance.
        """
        self._database_manager = db_manager

    async def setup_schema(self) -> None:
        """Creates the necessary schema if it does not exist.

        Raises:
            RuntimeError: If the database connection has not been initialized.
        """
        await self._database_manager.executescript(
            """
            CREATE TABLE IF NOT EXISTS global_admins (
                discord_id INTEGER PRIMARY KEY
            );

            CREATE TABLE IF NOT EXISTS server_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_entity_id INTEGER NOT NULL,
                entity_type TEXT NOT NULL CHECK(entity_type IN ('user', 'role')),
                server_id TEXT NOT NULL,
                permissions INTEGER DEFAULT 0,
                UNIQUE(discord_entity_id, server_id)
            );
            """
        )
        logger.info("Permissions schema verified.")

    async def is_global_admin(self, discord_id: int) -> bool:
        """Checks if a Discord user possesses global administrator privileges.

        Args:
            discord_id: The Discord ID of the user to check.

        Returns:
            `True` if the user is a global administrator, `False` otherwise.
        """
        rows = await self._database_manager.fetch_all(
            "SELECT 1 FROM global_admins WHERE discord_id = ?", (discord_id,)
        )
        return True if rows else False

    async def has_server_permission(
        self,
        user_id: int,
        role_ids: list[int],
        server_id: str,
        action: PermissionAction,
    ) -> bool:
        """Evaluates if a user (or any of their roles) is authorized for a specific action.

        Args:
            user_id: The Discord ID of the user.
            role_ids: A list of Discord Role IDs currently held by the user.
            server_id: The Pterodactyl server ID being targeted.
            action: The specific `PermissionAction` flag to verify.

        Returns:
            `True` if the user or one of their roles has the requested permission,
            `False` otherwise.
        """
        if await self.is_global_admin(user_id):
            return True

        entity_ids = [user_id] + role_ids
        placeholders = ",".join("?" for _ in entity_ids)

        rows = await self._database_manager.fetch_all(
            f"""
                SELECT permissions FROM server_permissions
                WHERE server_id = ? AND discord_entity_id IN ({placeholders})
            """,
            (server_id, *entity_ids),
        )

        return any((row["permissions"] & action.value) == action.value for row in rows)

    async def set_permission(
        self,
        entity_id: int,
        entity_type: Literal["user", "role"],
        server_id: str,
        permissions: PermissionAction,
    ) -> None:
        """Sets the permissions for a user or role for a specific server.

        Args:
            entity_id: The Discord ID of the user or role.
            entity_type: The type of entity ("user" or "role").
            server_id: The Pterodactyl server ID being targeted.
            permissions: The specific `PermissionAction` bitmask to apply.
        """
        await self._database_manager.execute(
            """
                INSERT INTO server_permissions
                (discord_entity_id, entity_type, server_id, permissions)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(discord_entity_id, server_id) DO UPDATE SET
                    permissions = excluded.permissions
            """,
            (
                entity_id,
                entity_type,
                server_id,
                permissions.value,
            ),
        )
        logger.info(
            f"Updated permissions for {entity_type} '{entity_id}' for server '{server_id}'."
        )
