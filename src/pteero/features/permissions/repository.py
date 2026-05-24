from __future__ import annotations

import logging
from enum import IntFlag, auto
from typing import TYPE_CHECKING, Any, Literal

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
            CREATE TABLE IF NOT EXISTS server_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                entity_type TEXT NOT NULL CHECK(entity_type IN ('user', 'role')),
                server_id TEXT NOT NULL,
                allows INTEGER DEFAULT 0,
                denies INTEGER DEFAULT 0,
                UNIQUE(entity_id, server_id)
            );
            """
        )
        logger.info("Permissions schema verified.")

    async def get_raw_permissions(
        self, entity_id: int, server_id: str
    ) -> tuple[PermissionAction, PermissionAction]:
        """Returns explicit local allows and denies masks for a single entity record.

        Args:
            entity_id: The Discord ID of the user or role.
            server_id: The unique identifier of the Pterodactyl server or "ALL".

        Returns:
            A tuple of `PermissionAction` bitmasks formatted as (allows, denies).
        """
        rows = await self._database_manager.fetch_all(
            "SELECT allows, denies FROM server_permissions WHERE entity_id = ? AND server_id = ?",
            (entity_id, server_id),
        )

        if not rows:
            return PermissionAction.NONE, PermissionAction.NONE

        return PermissionAction(rows[0]["allows"]), PermissionAction(rows[0]["denies"])  # pyright: ignore[reportIndexIssue]

    async def has_server_permission(
        self,
        user_id: int,
        permission: PermissionAction,
        server_id: str,
        role_ids: set[int] = set(),
    ) -> bool:
        """Evaluates if a user (or any of their roles) is authorized for a specific action.

        Args:
            user_id: The Discord ID of the user.
            permission: The specific `PermissionAction` flag to verify.
            server_id: The unique identifier of the Pterodactyl server or "ALL".
            role_ids (optional): A set of Discord role IDs held by the user. Defaults to empty set.

        Returns:
            `True` if the user or one of their roles has the requested permission, `False` otherwise.
        """
        entity_ids = [user_id, *role_ids]
        placeholders = ",".join("?" for _ in entity_ids)

        rows = await self._database_manager.fetch_all(
            f"""
            SELECT entity_id, server_id, allows, denies
            FROM server_permissions
            WHERE server_id IN (?, 'ALL') AND entity_id IN ({placeholders})
            """,
            (server_id, *entity_ids),
        )
        data = {
            (row["entity_id"], row["server_id"]): (row["allows"], row["denies"])
            for row in rows
        }

        evaluation_levels = [
            ([user_id], server_id),  # 1. User -> Local
            ([user_id], "ALL"),  # 2. User -> Global
            (role_ids, server_id),  # 3. Roles -> Local
            (role_ids, "ALL"),  # 4. Roles -> Global
        ]

        for entities, scope in evaluation_levels:
            allow_flag = False
            deny_flag = False

            for entity_id in entities:
                allow, deny = data.get((entity_id, scope), (0, 0))
                if allow & permission.value:
                    allow_flag = True
                if deny & permission.value:
                    deny_flag = True

            if allow_flag:
                return True
            if deny_flag:
                return False

        return False

    async def get_permission_sources(
        self, entity_id: int, server_id: str, role_ids: set[int] = set()
    ) -> list[dict[str, Any]]:
        """Fetches all layout database rule sets contributing to an entity's permission state.

        Args:
            user_id: The Discord ID of the user or role.
            server_id: The unique identifier of the Pterodactyl server or "ALL".
            role_ids (optional): A set of Discord role IDs held by the user. Defaults to empty set.

        Returns:
            A list of dictionary raw record rows.
        """
        entity_ids = {entity_id, *role_ids}
        placeholders = ",".join("?" for _ in entity_ids)

        rows = await self._database_manager.fetch_all(
            f"""
            SELECT entity_id, entity_type, server_id, allows, denies
            FROM server_permissions
            WHERE server_id IN (?, 'ALL') AND entity_id IN ({placeholders})
            """,
            (server_id, *entity_ids),
        )
        return [dict(row) for row in rows]

    async def set_permission(
        self,
        entity_id: int,
        entity_type: Literal["user", "role"],
        allowed: PermissionAction,
        denied: PermissionAction,
        server_id: str,
    ) -> None:
        """Sets the permissions for a user or role for a specific server.

        Args:
            entity_id: The Discord ID of the user or role.
            entity_type: The type of entity ("user" or "role").
            server_id: The unique identifier of the Pterodactyl server or "ALL".
            allows: Granted bitwise permission values to update.
            denies: Restricted bitwise permission values to update.
        """
        await self._database_manager.execute(
            """
            INSERT INTO server_permissions
            (entity_id, entity_type, server_id, allows, denies)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(entity_id, server_id) DO UPDATE SET
                allows = excluded.allows,
                denies = excluded.denies
            """,
            (entity_id, entity_type, server_id, allowed.value, denied.value),
        )
