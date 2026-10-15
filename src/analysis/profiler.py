"""Basic dataset profiling.

This module intentionally contains no Shiny code.

The existing synthetic-data analysis implementation can later be migrated
behind this boundary without coupling that logic to the UI.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .models import DatasetAnalysis, NodeTypeSummary


TYPE_COLUMN_NAMES = (
    "type",
    "type_",
    "_type",
    "node_type",
    "node_type_",
)


def find_type_column(
    columns: list[str],
) -> str | None:
    """Find the most likely node-type column.

    Exact/common type-column names are preferred. If none exists and exactly
    one column contains the word ``type``, that column is used.
    """

    normalized = {
        str(column).lower(): str(column)
        for column in columns
    }

    # Prefer known names.
    for candidate in TYPE_COLUMN_NAMES:
        if candidate in normalized:
            return normalized[candidate]

    # Fall back to a single column containing "type".
    matches = [
        str(column)
        for column in columns
        if "type" in str(column).lower()
    ]

    if len(matches) == 1:
        return matches[0]

    return None


def get_node_type_counts(
    data: pd.DataFrame,
    type_column: str | None,
) -> tuple[NodeTypeSummary, ...]:
    """Return node types represented by the detected type column."""

    if type_column is None:
        return ()

    counts = (
        data[type_column]
        .dropna()
        .astype(str)
        .str.strip()
    )

    # Ignore empty type values.
    counts = counts[counts != ""]

    value_counts = counts.value_counts()

    return tuple(
        NodeTypeSummary(
            value=str(value),
            count=int(count),
        )
        for value, count in value_counts.items()
    )


def analyze_dataset(
    *,
    file_path: Path,
    data: pd.DataFrame,
) -> DatasetAnalysis:
    """Build the basic structural profile for a dataset."""

    type_column = find_type_column(
        [str(column) for column in data.columns]
    )

    return DatasetAnalysis(
        file_name=file_path.name,
        file_format=(
            file_path.suffix
            .lstrip(".")
            .upper()
            or "Unknown"
        ),
        row_count=len(data),
        column_count=len(data.columns),
        type_column=type_column,
        node_types=get_node_type_counts(
            data,
            type_column,
        ),
    )