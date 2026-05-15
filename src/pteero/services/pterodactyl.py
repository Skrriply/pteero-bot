from __future__ import annotations

import asyncio
import logging
import time
from http import HTTPMethod
from typing import TYPE_CHECKING

import aiohttp
from pydantic import ValidationError

from pteero.services.base import BaseAPIClient
from pteero.services.schemas.pterodactyl import (
    PowerSignal,
    ServerResourceResponse,
    ServerState,
)

if TYPE_CHECKING:
    from pydantic import HttpUrl

logger = logging.getLogger(__name__)


class PterodactylClient(BaseAPIClient):
    """Client for interacting with the Pterodactyl Client API."""

    def __init__(
        self, api_url: str | HttpUrl, api_key: str, verify_ssl: bool = True
    ) -> None:
        """Initializes the class."""
        headers: dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        super().__init__(api_url, headers=headers)
        self.verify_ssl: bool = verify_ssl

    async def _wait_until_state(
        self,
        server_id: str,
        target_state: ServerState,
        poll_interval: float = 5.0,
        timeout_seconds: int = 300,
    ) -> bool:
        """Polls the API until the game server reaches the target state or times out.

        Args:
            server_id: The ID of the server.
            target_state: The desired state to wait for.
            poll_interval (optional): Time inn seconds between state checks. Defaults to `5.0`.
            timeout (optional): Maximum time in seconds to wait. Defaults to `300`.

        Returns:
            `True` if target state is reached within timeout, otherwise `False`.
        """
        timeout = time.monotonic() + timeout_seconds

        while time.monotonic() < timeout:
            data = await self.get_server_resources(server_id)

            if data and data.attributes.current_state == target_state:
                logger.info(
                    f"Server {server_id} successfully reached state: {target_state.value}."
                )
                return True

            sleep_duration = min(poll_interval, timeout - time.monotonic())
            if sleep_duration > 0:
                await asyncio.sleep(sleep_duration)

        logger.warning(
            f"Timeout ({timeout_seconds}s) reached while waiting for server {server_id} to become {target_state.value}."
        )
        return False

    async def get_server_resources(
        self, server_id: str
    ) -> ServerResourceResponse | None:
        """Fetches the current resource usage and state of a specific server.

        Args:
            server_id: The ID of the server.

        Returns:
            `ServerResourceResponse` if successfull, otherwise `None`.
        """
        endpoint = f"/api/client/servers/{server_id}/resources"

        try:
            response = await self._http.request(
                HTTPMethod.GET, endpoint, ssl=self.verify_ssl
            )

            if not response:
                return None

            return ServerResourceResponse.model_validate(response)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(
                f"Network error fetching resources for server {server_id}: {e}"
            )
        except ValidationError as e:
            logger.error(
                f"Data validation failed for server {server_id} resources: {e}"
            )

        return None

    async def send_power_signal(self, server_id: str, signal: PowerSignal) -> bool:
        """Sends a power signal to a specific server.

        Args:
            server_id: The short alphanumeric ID of the server.
            signal: The power signal to send.

        Returns:
            `True` if the action was successfull, `False` otherwise.
        """
        endpoint = f"/api/client/servers/{server_id}/power"
        payload = {"signal": signal.value}

        try:
            await self._http.request(
                HTTPMethod.POST, endpoint, json=payload, ssl=self.verify_ssl
            )
            return await self._wait_until_state(
                server_id,
                ServerState.RUNNING
                if signal in {PowerSignal.START, PowerSignal.RESTART}
                else ServerState.OFFLINE,
            )
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(
                f"Failed to send '{signal.value}' signal to server {server_id}: {e}"
            )

        return False
