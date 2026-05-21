from enum import Enum

from pydantic import BaseModel


class PowerSignal(str, Enum):
    """Power actions that can be sent to a server."""

    START = "start"
    STOP = "stop"
    RESTART = "restart"
    KILL = "kill"


class ServerState(str, Enum):
    """Runtime state of a server."""

    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class ResourceUsage(BaseModel):
    """Hardware and network utilization metrics."""

    memory_bytes: int = 0
    cpu_absolute: float = 0.0
    disk_bytes: int = 0
    network_rx_bytes: int = 0
    network_tx_bytes: int = 0
    uptime: int = 0


class ServerAttributes(BaseModel):
    """State details and resource metrics for a server."""

    current_state: ServerState = ServerState.UNKNOWN
    is_suspended: bool = False
    resources: ResourceUsage | None = None


class ServerResourceResponse(BaseModel):
    """API response container for server statistics."""

    object: str = "stats"
    attributes: ServerAttributes


class ServerMetaAttributes(BaseModel):
    """Identifying metadata for a server."""

    identifier: str
    name: str
    uuid: str


class ServerMetaEntry(BaseModel):
    """A single server object wrapped inside a list response."""

    object: str
    attributes: ServerMetaAttributes


class ServerListResponse(BaseModel):
    """API response containing an array of servers."""

    object: str = "list"
    data: list[ServerMetaEntry]
