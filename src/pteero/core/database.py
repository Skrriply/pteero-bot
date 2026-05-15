from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import aiosqlite

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DashboardRecord:
    """Domain model representing a Pterodactyl server dashboard."""

    server_id: str
    channel_id: int
    message_id: int


class DatabaseManager:
    """Manages asynchronous SQLite database connections and operations."""

    def __init__(self, database: Path) -> None:
        """Initializes the class.

        Args:
            database: The file path to the SQLite database.
        """
        self.database: Path = database
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Establishes the database connection and ensures tables exist."""
        if self._connection:
            logger.debug("Database connection already established. Skipping...")
            return

        self._connection = await aiosqlite.connect(self.database)
        self._connection.row_factory = aiosqlite.Row
        logger.info(f"Connected to SQLite database at '{self.database}'.")

        await self._setup_tables()

    async def close(self) -> None:
        """Closes the database connection safely."""
        if not self._connection:
            logger.debug("No active database connection to close. Skipping...")
            return

        await self._connection.close()
        self._connection = None
        logger.info("Closed SQLite database connection.")

    async def _setup_tables(self) -> None:
        """Creates the necessary schema if it does not exist.

        Raises:
            RuntimeError: If the database connection has not been initialized.
        """
        if not self._connection:
            logger.error(
                "Failed to set up tables. Database connection is not initialized."
            )
            raise RuntimeError("Database connection is not initialized.")

        await self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS dashboards (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                server_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await self._connection.commit()
        logger.info("Database tables verified and created successfully.")

    async def _execute(self, query: str, parameters: tuple[Any, ...] = ()) -> None:
        """Executes a single query that modifies data (INSERT, UPDATE, DELETE).

        Args:
            query: The SQL query string to execute.
            parameters: A tuple of parameters to bind to the query.

        Raises:
            RuntimeError: If the database connection has not been initialized.
        """
        if not self._connection:
            logger.error(
                "Failed to execute query. Database connection is not initialized."
            )
            raise RuntimeError("Database connection is not initialized.")

        try:
            async with self._connection.execute(query, parameters):
                await self._connection.commit()
        except aiosqlite.Error as e:
            logger.error(
                f"Failed to execute query: {query!r}. Parameters: {parameters}. Error: {e}"
            )
            return None

    async def _fetch_all(
        self, query: str, parameters: tuple[Any, ...] = ()
    ) -> Iterable[aiosqlite.Row]:
        """Fetches all matching rows for a given query.

        Args:
            query: The SQL query string to execute.
            parameters: A tuple of parameters to bind to the query.

        Returns:
            An iterable of `aiosqlite.Row` objects matching the query. Returns an
            empty list if a database error occurs.

        Raises:
            RuntimeError: If the database connection has not been initialized.
        """
        if not self._connection:
            logger.error(
                "Failed to fetch data. Database connection is not initialized."
            )
            raise RuntimeError("Database connection is not initialized.")

        try:
            async with self._connection.execute(query, parameters) as cursor:
                return await cursor.fetchall()
        except aiosqlite.Error as e:
            logger.error(
                f"Failed to execute query: {query!r}. Parameters: {parameters}. Error: {e}"
            )
            return []

    async def get_all_dashboards(self) -> list[DashboardRecord]:
        """Retrieves all dashboard records from the database.

        Returns:
            A list of `DashboardRecord` objects.
        """
        query = "SELECT server_id, channel_id, message_id FROM dashboards"
        rows = await self._fetch_all(query)

        return [
            DashboardRecord(
                server_id=row["server_id"],
                channel_id=row["channel_id"],
                message_id=row["message_id"],
            )
            for row in rows
        ]

    async def add_dashboard(self, record: DashboardRecord) -> None:
        """Saves a new dashboard record to the database.

        Args:
            record: The `DashboardRecord` instance.
        """
        await self._execute(
            "INSERT INTO dashboards (server_id, channel_id, message_id) VALUES (?, ?, ?)",
            (record.server_id, record.channel_id, record.message_id),
        )

    async def remove_dashboard(self, message_id: int) -> None:
        """Removes a dashboard record from the database by its message ID.

        Args:
            message_id: The message ID of the dashboard to remove.
        """
        await self._execute(
            "DELETE FROM dashboards WHERE message_id = ?", (message_id,)
        )
