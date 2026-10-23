from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DiseaseSupportStatus(str, Enum):
    SUPPORTED = "supported"
    LIMITED = "limited"
    UNSUPPORTED = "unsupported"


class DiseaseNodeStatus(str, Enum):
    READY = "ready"
    INSUFFICIENT_DATA = "insufficient_data"
    NO_DATA = "no_data"
    UNSCOPABLE = "unscopable"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class DiseaseNodeSupport:
    node_name: str
    row_count: int

    status: DiseaseNodeStatus

    minimum_rows: int | None = None
    message: str = ""


@dataclass(frozen=True)
class DiseaseSupportSummary:
    disease: str

    status: DiseaseSupportStatus

    generation_nodes: tuple[
        DiseaseNodeSupport,
        ...
    ]

    context_nodes: tuple[
        DiseaseNodeSupport,
        ...
    ]

    @property
    def usable_row_count(self) -> int:
        return sum(
            node.row_count
            for node in self.generation_nodes
            if node.status
            == DiseaseNodeStatus.READY
        )

    @property
    def ready_node_count(self) -> int:
        return sum(
            node.status
            == DiseaseNodeStatus.READY
            for node in self.generation_nodes
        )