from __future__ import annotations

from typing import TYPE_CHECKING

from pteero.core.http import AsyncHTTPClient

if TYPE_CHECKING:
    from pydantic import HttpUrl


class BaseAPIClient:
    """A base client for interacting with the APIs."""

    def __init__(
        self, url: str | HttpUrl, headers: dict[str, str] | None = None
    ) -> None:
        """
        Initializes the class.

        Args:
            base_url: The base URL for all requests.
            headers (optional): Default headers to include in every request. Defaults to `None`.
        """
        self._http: AsyncHTTPClient = AsyncHTTPClient(url, headers=headers)

    async def connect(self) -> None:
        """Initializes the underlying HTTP session."""
        await self._http.connect()

    async def close(self) -> None:
        """Closes the underlying HTTP session."""
        await self._http.close()
