from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


DEFAULT_MISSING_DISEASE_TERMS = frozenset({
    "",
    "unknown",
    "not reported",
    "not applicable",
    "na",
    "n/a",
    "none",
    "null",
    "nan",
})


@dataclass(frozen=True)
class DiseaseGenerationConfig:
    """Configuration for disease-specific analysis and generation."""

    project_key: str
    source_label: str

    vocabulary_node: str
    vocabulary_property: str

    generation_nodes: frozenset[str]
    direct_scope_properties: Mapping[str, str]

    minimum_node_rows: int = 5

    missing_terms: frozenset[str] = (
        DEFAULT_MISSING_DISEASE_TERMS
    )

    request_label: str = "Disease or disease area"

    def __post_init__(self) -> None:
        generation_nodes = frozenset(
            str(node).strip().casefold()
            for node in self.generation_nodes
            if str(node).strip()
        )

        scope_properties = {
            str(node).strip().casefold():
            str(property_name).strip()
            for node, property_name
            in self.direct_scope_properties.items()
        }

        missing_scope = (
            generation_nodes
            - set(scope_properties)
        )

        if missing_scope:
            raise ValueError(
                "Generation nodes are missing disease "
                "scope properties: "
                + ", ".join(sorted(missing_scope))
            )

        object.__setattr__(
            self,
            "generation_nodes",
            generation_nodes,
        )

        object.__setattr__(
            self,
            "direct_scope_properties",
            MappingProxyType(
                scope_properties
            ),
        )

        object.__setattr__(
            self,
            "minimum_node_rows",
            max(1, int(self.minimum_node_rows)),
        )

    def is_generation_node(
        self,
        node_name: str,
    ) -> bool:
        return (
            str(node_name)
            .strip()
            .casefold()
            in self.generation_nodes
        )

    def scope_property_for_node(
        self,
        node_name: str,
    ) -> str | None:
        return self.direct_scope_properties.get(
            str(node_name)
            .strip()
            .casefold()
        )


ICDC_DISEASE_CONFIG = DiseaseGenerationConfig(
    project_key="ICDC",
    source_label="ICDC",

    vocabulary_node="diagnosis",
    vocabulary_property="disease_term",

    generation_nodes=frozenset({
        "case",
        "demographic",
        "diagnosis",
        "enrollment",
        "file",
        "registration",
        "sample",
    }),

    direct_scope_properties={
        "case": "disease_term",
        "demographic": "disease_term",
        "diagnosis": "disease_term",
        "enrollment": "disease_term",
        "file": "disease_term",
        "registration": "disease_term",
        "sample": "disease_term",
    },

    minimum_node_rows=5,
)


DISEASE_GENERATION_CONFIGS = {
    "ICDC": ICDC_DISEASE_CONFIG,
}


def get_disease_generation_config(
    project_key: str | None,
) -> DiseaseGenerationConfig | None:

    if not project_key:
        return None

    return DISEASE_GENERATION_CONFIGS.get(
        project_key.strip().upper()
    )