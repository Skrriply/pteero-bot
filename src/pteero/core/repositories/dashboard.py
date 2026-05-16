from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pteero.core.database import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DashboardRecord:
    """Domain model representing a Pterodactyl server dashboard."""

    server_id: str
    channel_id: int
    message_id: int


class DashboardRepository:
    """Handles all database operations related to server dashboards."""

    def __init__(self, database_manager: DatabaseManager) -> None:
        """Initializes the repository with the main database manager."""
        self._database_manager = database_manager

    async def setup_schema(self) -> None:
        """Creates the necessary schema if it does not exist.

        Raises:
            RuntimeError: If the database connection has not been initialized.
        """
        await self._database_manager.execute(
            """
            CREATE TABLE IF NOT EXISTS dashboards (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                server_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        logger.info("Dashboards schema verified.")

    async def get_all(self) -> list[DashboardRecord]:
        """Retrieves all dashboard records from the database.

        Returns:
            A list of `DashboardRecord` objects.
        """
        rows = await self._database_manager.fetch_all(
            "SELECT server_id, channel_id, message_id FROM dashboards"
        )

        return [
            DashboardRecord(
                server_id=row["server_id"],
                channel_id=row["channel_id"],
                message_id=row["message_id"],
            )
            for row in rows
        ]

    async def add(self, server_id: str, channel_id: int, message_id: int) -> None:
        """Saves a new dashboard record to the database.

        Args:
            server_id: The Pterodactyl server ID.
            channel_id: The channel ID where the dashboard is sended.
            message_id: The message ID of the dashboard to add.
        """
        await self._database_manager.execute(
            "INSERT INTO dashboards (server_id, channel_id, message_id) VALUES (?, ?, ?)",
            (server_id, channel_id, message_id),
        )

    async def remove(self, message_id: int) -> None:
        """Removes a dashboard record from the database by its message ID.

        Args:
            message_id: The message ID of the dashboard to remove.
        """
        await self._database_manager.execute(
            "DELETE FROM dashboards WHERE message_id = ?", (message_id,)
        )
