"""Small provider-neutral catalogue types for Earth Lab observations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class EvidenceQuery:
    bounds: tuple[float, float, float, float]
    crs: str
    datetime_range: str
    evidence_types: tuple[str, ...]


@dataclass(frozen=True)
class Observation:
    provider: str
    product_id: str
    acquired_at: str
    source_crs: str
    assets: dict[str, dict[str, Any]] = field(default_factory=dict)
    properties: dict[str, Any] = field(default_factory=dict)


class ObservationProvider(Protocol):
    def query(self, request: EvidenceQuery) -> list[Observation]: ...


class EvidenceCatalogue:
    """Minimal provider registry; 005B intentionally does not build a global platform."""

    def __init__(self) -> None:
        self._providers: dict[str, ObservationProvider] = {}

    def register(self, name: str, provider: ObservationProvider) -> None:
        if name in self._providers:
            raise ValueError(f"Provider {name!r} is already registered")
        self._providers[name] = provider

    def query(self, name: str, request: EvidenceQuery) -> list[Observation]:
        if name not in self._providers:
            raise KeyError(f"Unknown evidence provider {name!r}")
        return self._providers[name].query(request)
