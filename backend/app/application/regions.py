"""Read-only Region Pack application boundary for versioned API routes."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


class RegionReadApplicationService:
    """Expose active-region readiness and public summaries without HTTP concerns."""

    def __init__(self, registry: Callable[[], Any]) -> None:
        self._registry = registry

    def readiness(self, region_code: str) -> tuple[bool, int]:
        active = self._registry().active()
        return any(region.code == region_code for region in active), len(active)

    def public_summaries(self) -> list[Mapping[str, Any]]:
        return self._registry().public_summaries(active_only=True)
