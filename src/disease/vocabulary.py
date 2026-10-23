"""Disease vocabulary normalization and lookup utilities."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

import pandas as pd

from .config import DiseaseGenerationConfig


def clean_disease_term(value: Any) -> str:
    """Return display text with surrounding/repeated whitespace removed."""

    if value is None:
        return ""

    try:
        if (
            pd.api.types.is_scalar(value)
            and bool(pd.isna(value))
        ):
            return ""
    except (TypeError, ValueError):
        pass

    return " ".join(
        str(value).split()
    )


def normalize_disease_term(
    value: Any,
    scope_config: DiseaseGenerationConfig,
) -> str:
    """Return a conservative exact-match key for a disease term."""

    cleaned = clean_disease_term(value)
    normalized = cleaned.casefold()

    if normalized in scope_config.missing_terms:
        return ""

    return normalized


def _get_node_frame(
    data_state: Mapping[str, pd.DataFrame] | None,
    node_name: str | None,
) -> pd.DataFrame | None:
    """Find a node DataFrame using a case-insensitive node name."""

    if not data_state or not node_name:
        return None

    requested_key = (
        str(node_name)
        .strip()
        .casefold()
    )

    for key, frame in data_state.items():
        if (
            str(key)
            .strip()
            .casefold()
            == requested_key
        ):
            return (
                frame
                if isinstance(frame, pd.DataFrame)
                else None
            )

    return None


def extract_supported_diseases(
    data_state: Mapping[str, pd.DataFrame] | None,
    scope_config: DiseaseGenerationConfig | None,
) -> tuple[str, ...]:
    """Extract deterministic canonical terms from the vocabulary node."""

    if scope_config is None:
        return ()

    vocabulary_df = _get_node_frame(
        data_state,
        scope_config.vocabulary_node,
    )

    vocabulary_property = (
        scope_config.vocabulary_property
    )

    if (
        vocabulary_df is None
        or vocabulary_df.empty
        or vocabulary_property
        not in vocabulary_df.columns
    ):
        return ()

    variants_by_key: dict[
        str,
        Counter[str],
    ] = {}

    for value in vocabulary_df[
        vocabulary_property
    ]:
        normalized = normalize_disease_term(
            value,
            scope_config,
        )

        if not normalized:
            continue

        display = clean_disease_term(
            value
        )

        variants_by_key.setdefault(
            normalized,
            Counter(),
        )[display] += 1

    canonical_terms: list[str] = []

    for variants in variants_by_key.values():
        canonical = sorted(
            variants.items(),
            key=lambda item: (
                -item[1],
                item[0].casefold(),
                item[0],
            ),
        )[0][0]

        canonical_terms.append(
            canonical
        )

    return tuple(
        sorted(
            canonical_terms,
            key=lambda term: (
                term.casefold(),
                term,
            ),
        )
    )


def resolve_supported_disease(
    requested_disease: Any,
    supported_terms: tuple[str, ...],
    scope_config: DiseaseGenerationConfig,
) -> str | None:
    """Resolve a requested disease to its canonical supported term."""

    requested_key = normalize_disease_term(
        requested_disease,
        scope_config,
    )

    if not requested_key:
        return None

    return next(
        (
            term
            for term in supported_terms
            if normalize_disease_term(
                term,
                scope_config,
            )
            == requested_key
        ),
        None,
    )