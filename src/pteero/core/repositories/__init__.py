from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pteero.core.repositories.dashboard import DashboardRepository


@dataclass(frozen=True, slots=True)
class RepositoryContainer:
    """Holds initialized database repositories for dependency injection."""

    dashboards: DashboardRepository
