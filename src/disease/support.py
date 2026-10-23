# Neo4j counts
# +
# supported vocabulary
# +
# DiseaseGenerationConfig
#             ↓
# build_disease_support()
#             ↓
# DiseaseSupportSummary[]

"""Disease and node support classification.

This module converts disease/node availability information into domain-level
support results used by the UI, analysis workflow, and eventually the
synthetic-data generation gate.

It intentionally contains no Shiny or Neo4j-specific code.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import pandas as pd

from .config import DiseaseGenerationConfig
from .models import (
    DiseaseNodeStatus,
    DiseaseNodeSupport,
    DiseaseSupportStatus,
    DiseaseSupportSummary,
)
from .vocabulary import (
    clean_disease_term,
    normalize_disease_term,
)


def _normalize_node_name(
    value: Any,
) -> str:
    """Return a normalized node name for matching."""

    return (
        " ".join(str(value).split())
        .casefold()
    )


def _canonical_supported_terms(
    supported_terms: Iterable[str],
    scope_config: DiseaseGenerationConfig,
) -> dict[str, str]:
    """Map normalized disease terms to canonical display terms."""

    canonical: dict[str, str] = {}

    for term in supported_terms:
        display = clean_disease_term(term)

        if not display:
            continue

        key = normalize_disease_term(
            display,
            scope_config,
        )

        if not key:
            continue

        canonical.setdefault(
            key,
            display,
        )

    return canonical


def _node_support(
    *,
    node_name: str,
    row_count: int,
    scope_config: DiseaseGenerationConfig,
) -> DiseaseNodeSupport:
    """Classify support for one node."""

    normalized_node = _normalize_node_name(
        node_name
    )

    # --------------------------------------------------------------
    # Context / metadata node
    #
    # A node not explicitly configured for disease generation is
    # intentionally not subject to the minimum-row requirement.
    # --------------------------------------------------------------

    if not scope_config.is_generation_node(
        normalized_node
    ):
        return DiseaseNodeSupport(
            node_name=node_name,
            row_count=row_count,
            status=(
                DiseaseNodeStatus.NOT_APPLICABLE
            ),
            minimum_rows=None,
            message=(
                "This node is not used for "
                "disease-specific generation."
            ),
        )

    # --------------------------------------------------------------
    # Disease-scoping configuration
    # --------------------------------------------------------------

    scope_property = (
        scope_config.scope_property_for_node(
            normalized_node
        )
    )

    if not scope_property:
        return DiseaseNodeSupport(
            node_name=node_name,
            row_count=row_count,
            status=(
                DiseaseNodeStatus.UNSCOPABLE
            ),
            minimum_rows=(
                scope_config.minimum_node_rows
            ),
            message=(
                "No reliable disease-scoping property "
                "is configured for this node."
            ),
        )

    # --------------------------------------------------------------
    # No source data
    # --------------------------------------------------------------

    if row_count <= 0:
        return DiseaseNodeSupport(
            node_name=node_name,
            row_count=0,
            status=(
                DiseaseNodeStatus.NO_DATA
            ),
            minimum_rows=(
                scope_config.minimum_node_rows
            ),
            message=(
                "No disease-specific source rows "
                "are available for this node."
            ),
        )

    # --------------------------------------------------------------
    # Insufficient source data
    # --------------------------------------------------------------

    minimum = max(
        1,
        int(scope_config.minimum_node_rows),
    )

    if row_count < minimum:
        return DiseaseNodeSupport(
            node_name=node_name,
            row_count=row_count,
            status=(
                DiseaseNodeStatus.INSUFFICIENT_DATA
            ),
            minimum_rows=minimum,
            message=(
                f"At least {minimum} disease-specific "
                "source rows are required."
            ),
        )

    # --------------------------------------------------------------
    # Ready
    # --------------------------------------------------------------

    return DiseaseNodeSupport(
        node_name=node_name,
        row_count=row_count,
        status=DiseaseNodeStatus.READY,
        minimum_rows=minimum,
        message=(
            "Sufficient disease-specific source "
            "data is available."
        ),
    )


def _disease_status(
    *,
    is_supported_disease: bool,
    generation_nodes: tuple[
        DiseaseNodeSupport,
        ...,
    ],
) -> DiseaseSupportStatus:
    """Determine the overall support status for one disease."""

    # Disease exists in source data but is not part of the
    # validated supported vocabulary.
    if not is_supported_disease:
        return DiseaseSupportStatus.UNSUPPORTED

    # A configured disease with no generation nodes available
    # should not be presented as fully supported.
    if not generation_nodes:
        return DiseaseSupportStatus.LIMITED

    # Fully supported only when every applicable generation node
    # is ready.
    if all(
        node.status == DiseaseNodeStatus.READY
        for node in generation_nodes
    ):
        return DiseaseSupportStatus.SUPPORTED

    return DiseaseSupportStatus.LIMITED


def build_disease_support(
    disease_node_counts: pd.DataFrame,
    supported_terms: Iterable[str],
    scope_config: DiseaseGenerationConfig,
) -> tuple[DiseaseSupportSummary, ...]:
    """Build support summaries from disease/node counts.

    Expected DataFrame columns:

        disease
        node_type
        count

    Example:

        disease          node_type       count
        Glioma           case               81
        Glioma           sample            373
        Glioma           study               1
        Bladder Cancer   case              168

    ``supported_terms`` represents the validated disease vocabulary.

    Nodes explicitly configured in ``scope_config.generation_nodes`` are
    evaluated against the configured minimum row requirement.

    All other nodes are classified as NOT_APPLICABLE and therefore do not
    cause a disease to become LIMITED.
    """

    required_columns = {
        "disease",
        "node_type",
        "count",
    }

    missing_columns = (
        required_columns
        - set(disease_node_counts.columns)
    )

    if missing_columns:
        raise ValueError(
            "Disease node counts are missing required "
            "columns: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

    if disease_node_counts.empty:
        return ()

    canonical_terms = (
        _canonical_supported_terms(
            supported_terms,
            scope_config,
        )
    )

    summaries: list[
        DiseaseSupportSummary
    ] = []

    # --------------------------------------------------------------
    # Process each disease independently.
    # --------------------------------------------------------------

    for raw_disease, disease_rows in (
        disease_node_counts.groupby(
            "disease",
            sort=True,
            dropna=False,
        )
    ):
        disease_display = clean_disease_term(
            raw_disease
        )

        if not disease_display:
            continue

        disease_key = normalize_disease_term(
            disease_display,
            scope_config,
        )

        if not disease_key:
            continue

        canonical_disease = (
            canonical_terms.get(
                disease_key
            )
        )

        is_supported_disease = (
            canonical_disease is not None
        )

        display_disease = (
            canonical_disease
            or disease_display
        )

        # ----------------------------------------------------------
        # Neo4j should normally return one row per node type.
        #
        # Group again defensively in case the query returns duplicate
        # rows for a disease/node combination.
        # ----------------------------------------------------------

        counts_by_node: dict[str, int] = {}

        for _, row in disease_rows.iterrows():
            node_name = clean_disease_term(
                row["node_type"]
            )

            if not node_name:
                continue

            normalized_node = (
                _normalize_node_name(
                    node_name
                )
            )

            try:
                row_count = int(
                    row["count"]
                )
            except (
                TypeError,
                ValueError,
                OverflowError,
            ):
                row_count = 0

            # Do not double-count duplicate rows returned for
            # the same node type. Keep the largest reported
            # distinct-node count.
            counts_by_node[
                normalized_node
            ] = max(
                counts_by_node.get(
                    normalized_node,
                    0,
                ),
                max(0, row_count),
            )

        # ----------------------------------------------------------
        # Ensure configured generation nodes appear even if Neo4j
        # returned no rows for them.
        #
        # This allows the UI to distinguish:
        #
        #     sample  0  No data
        #
        # from a node silently disappearing from the support table.
        # ----------------------------------------------------------

        for node_name in (
            scope_config.generation_nodes
        ):
            counts_by_node.setdefault(
                node_name,
                0,
            )

        generation_support: list[
            DiseaseNodeSupport
        ] = []

        context_support: list[
            DiseaseNodeSupport
        ] = []

        for normalized_node in sorted(
            counts_by_node
        ):
            count = counts_by_node[
                normalized_node
            ]

            support = _node_support(
                node_name=normalized_node,
                row_count=count,
                scope_config=scope_config,
            )

            if scope_config.is_generation_node(
                normalized_node
            ):
                generation_support.append(
                    support
                )
            else:
                context_support.append(
                    support
                )

        generation_nodes = tuple(
            generation_support
        )

        context_nodes = tuple(
            context_support
        )

        status = _disease_status(
            is_supported_disease=(
                is_supported_disease
            ),
            generation_nodes=(
                generation_nodes
            ),
        )

        summaries.append(
            DiseaseSupportSummary(
                disease=display_disease,
                status=status,
                generation_nodes=(
                    generation_nodes
                ),
                context_nodes=(
                    context_nodes
                ),
            )
        )

    return tuple(
        sorted(
            summaries,
            key=lambda item: (
                item.disease.casefold(),
                item.disease,
            ),
        )
    )


def summarize_support_counts(
    summaries: Iterable[
        DiseaseSupportSummary
    ],
) -> Mapping[
    DiseaseSupportStatus,
    int,
]:
    """Count diseases by support status."""

    counts = {
        DiseaseSupportStatus.SUPPORTED: 0,
        DiseaseSupportStatus.LIMITED: 0,
        DiseaseSupportStatus.UNSUPPORTED: 0,
    }

    for summary in summaries:
        counts[summary.status] += 1

    return counts