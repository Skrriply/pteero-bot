from enum import Enum

from pydantic import BaseModel


class PowerSignal(str, Enum):
    """Pterodactyl power signals."""

    START = "start"
    STOP = "stop"
    RESTART = "restart"
    KILL = "kill"


class ServerState(str, Enum):
    """Pterodactyl server states."""

    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class ResourceUsage(BaseModel):
    """Pterodactyl server resource usage metrics."""

    memory_bytes: int = 0
    cpu_absolute: float = 0.0
    disk_bytes: int = 0
    network_rx_bytes: int = 0
    network_tx_bytes: int = 0
    uptime: int = 0


class ServerAttributes(BaseModel):
    """Pterodactyl server state attributes."""

    current_state: ServerState = ServerState.UNKNOWN
    is_suspended: bool = False
    resources: ResourceUsage | None = None


class ServerResourceResponse(BaseModel):
    """Pterodactyl server resource API response."""

    object: str = "stats"
    attributes: ServerAttributes
