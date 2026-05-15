from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import aiosqlite

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages asynchronous SQLite database connections and operations."""

    def __init__(self, database: Path) -> None:
        """Initializes the database manager.

        Args:
            db_path: The file path to the SQLite database.
        """
        self.database: Path = database
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Establishes the database connection and ensures tables exist."""
        if self._connection:
            return

        self._connection = await aiosqlite.connect(self.database)
        self._connection.row_factory = aiosqlite.Row
        logger.info(f"Connected to SQLite database at {self.database}.")

        await self._setup_tables()

    async def close(self) -> None:
        """Closes the database connection safely."""
        if not self._connection:
            return

        await self._connection.close()
        self._connection = None
        logger.info("Closed SQLite database connection.")

    async def _setup_tables(self) -> None:
        """Creates the necessary schema if it does not exist."""
        if not self._connection:
            raise RuntimeError("Database connection is not initialized.")

        # Table for tracking active live-updating dashboards
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
        logger.info("Database tables verified and created.")

    async def execute(self, query: str, parameters: tuple[Any, ...] = ()) -> None:
        """Executes a single query that modifies data (INSERT, UPDATE, DELETE)."""
        if not self._connection:
            raise RuntimeError("Database connection is not initialized.")

        async with self._connection.execute(query, parameters):
            await self._connection.commit()

    async def fetch_all(
        self, query: str, parameters: tuple[Any, ...] = ()
    ) -> Iterable[aiosqlite.Row]:
        """Fetches all matching rows for a given query."""
        if not self._connection:
            raise RuntimeError("Database connection is not initialized.")

        try:
            async with self._connection.execute(query, parameters) as cursor:
                return await cursor.fetchall()
        except aiosqlite.Error:
            return []

    async def fetch_one(
        self, query: str, parameters: tuple[Any, ...] = ()
    ) -> aiosqlite.Row | None:
        """Fetches a single row for a given query."""
        if not self._connection:
            raise RuntimeError("Database connection is not initialized.")

        try:
            async with self._connection.execute(query, parameters) as cursor:
                return await cursor.fetchone()
        except aiosqlite.Error:
            return None
