"""Dataset analysis models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NodeTypeSummary:
    """Count for one node type represented in a dataset."""

    value: str
    count: int


@dataclass(frozen=True)
class DatasetAnalysis:
    """Basic structural analysis for an imported dataset."""

    file_name: str
    file_format: str

    row_count: int
    column_count: int

    type_column: str | None
    node_types: tuple[NodeTypeSummary, ...]