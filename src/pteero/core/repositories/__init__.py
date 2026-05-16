from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pteero.core.repositories.dashboard import DashboardRepository
    from pteero.core.repositories.permissions import PermissionRepository


@dataclass(frozen=True, slots=True)
class RepositoryContainer:
    """Holds initialized database repositories for dependency injection."""

    permissions: PermissionRepository
    dashboards: DashboardRepository

    async def setup_schemas(self) -> None:
        await self.permissions.setup_schema()
        await self.dashboards.setup_schema()
