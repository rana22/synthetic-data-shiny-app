"""Placeholder external API client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ExternalDataClient:
    """Placeholder for an external data/source client."""

    endpoint: str | None = None

    def execute_query(self, query: str, *, language: str = "cypher") -> list[dict[str, Any]]:
        """Execute a future Cypher/GraphQL query.

        The implementation intentionally raises until a real data connector
        is selected for the project.
        """
        raise NotImplementedError(
            f"No external data connector is configured for {language} queries."
        )
