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
        """Initializes the class.

        Args:
            database: The file path to the SQLite database.
        """
        self._database: Path = database
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Establishes the database connection and ensures tables exist."""
        if self._connection:
            logger.debug("Database connection already established. Skipping...")
            return

        self._connection = await aiosqlite.connect(self._database)
        self._connection.row_factory = aiosqlite.Row
        logger.info(f"Connected to SQLite database at '{self._database}'.")

    async def close(self) -> None:
        """Closes the database connection safely."""
        if not self._connection:
            logger.debug("No active database connection to close. Skipping...")
            return

        await self._connection.close()
        self._connection = None
        logger.info("Closed SQLite database connection.")

    async def execute(self, query: str, parameters: tuple[Any, ...] = ()) -> None:
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

    async def fetch_all(
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
