from __future__ import annotations

import asyncio
import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import aiohttp

if TYPE_CHECKING:
    from http import HTTPMethod

logger = logging.getLogger(__name__)


class AsyncHTTPClient:
    """An asynchronous HTTP client wrapper around `aiohttp.ClientSession`."""

    def __init__(self, base_url: str, headers: dict[str, str] | None = None):
        """Initializes the class.

        Args:
            base_url: The base URL for all requests.
            headers (optional): Default headers to include in every request. Defaults to `None`.
        """
        self.base_url: str = base_url.rstrip("/")
        self.headers: dict[str, str] = headers or {}

        self._session: aiohttp.ClientSession | None = None

    async def connect(self) -> None:
        """Initializes the `aiohttp.ClientSession`."""
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self.headers)

    async def close(self) -> None:
        """Closes the `aiohttp.ClientSession`."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def request(self, method: HTTPMethod, endpoint: str, **kwargs: Any) -> Any:
        """Executes an asynchronous HTTP request.

        Args:
            method: The HTTP method (e.g., `HTTPMethod.GET`, `HTTPMethod.POST`).
            endpoint: The URL endpoint to append to the `base_url`.
            **kwargs: Additional arguments to pass to the `aiohttp.ClientSession.request` method.

        Returns:
            The parsed response body. Can be a dict for JSON, a string for text,
            bytes for binary data, or `None`.

        Raises:
            RuntimeError: If the HTTP session is not initialized.
            aiohttp.ClientResponseError: If the server returns an HTTP error status.
            asyncio.TimeoutError: If the request times out.
            aiohttp.ClientError: For any underlying connection issues.
        """
        if not self._session:
            raise RuntimeError("HTTP Client session is not initialized.")

        url = f"{self.base_url}{endpoint}"

        try:
            async with self._session.request(method.value, url, **kwargs) as response:
                response.raise_for_status()

                if response.status == HTTPStatus.NO_CONTENT:
                    return None

                content = await response.read()

                if not content:
                    return None

                content_type = response.headers.get("Content-Type", "")

                if "application/json" in content_type:
                    return await response.json()
                elif "text/" in content_type:
                    return await response.text()

                return content
        except aiohttp.ClientResponseError as e:
            logger.error(f"API Error {e.status} | {method} {url} | {e.message}")
            raise
        except asyncio.TimeoutError:
            logger.error(f"Timeout Error | {method} {url}")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Connection Error | {method} {url} | {e}")
            raise
