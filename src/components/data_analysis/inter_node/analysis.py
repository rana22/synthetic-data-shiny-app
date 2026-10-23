"""Inter-node analysis migrated from the original Gradio workflow."""

from __future__ import annotations

from collections import deque
from typing import Any

import pandas as pd

from ..features.base import FeatureBase
from ..features.categorical import normalize_value
from ..features.fuzzy import FuzzyFeatureAnalyzer, looks_like_date_column
from ..intra_node.analysis import PairwiseRelationshipEvaluator


class _NullDocAlignmentModel:
    def score(self, a: str, b: str) -> float:
        return 0.0


class _CrossNodeSchema:
    name = "cross_node_match"


def _sample_values(values, max_n: int = 40) -> list[str]:
    values = (
        pd.Series(values)
        .dropna()
        .astype(str)
        .str.lower()
        .drop_duplicates()
    )
    if len(values) > max_n:
        values = values.sample(n=max_n, random_state=0)
    return values.tolist()


def infer_cardinality(
    parent_df: pd.DataFrame,
    child_df: pd.DataFrame,
    a: str,
    b: str,
) -> str:
    try:
        parent_unique = parent_df[a].nunique()
        child_unique = child_df[b].nunique()

        if parent_unique == len(parent_df) and child_unique > parent_unique:
            return "one_to_many"
        if parent_unique == 1 and child_unique == 1:
            return "one_to_one"
        if parent_unique > 1 and child_unique > 1:
            return "many_to_many"
        return "unknown"
    except Exception:
        return "unknown"


def find_selected_edges(
    relationships: pd.DataFrame,
    selected_nodes: list[str],
) -> list[tuple[str, str]]:
    """Migrate graph.BFS.find_selected_edges for the relationship DataFrame."""
    if relationships is None or relationships.empty:
        return []

    selected = set(selected_nodes or [])
    if not selected:
        return []

    required = {"parent", "child"}
    if not required.issubset(relationships.columns):
        return []

    edges: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for _, row in relationships.iterrows():
        edge = (str(row["parent"]), str(row["child"]))
        if edge[0] not in selected or edge[1] not in selected:
            continue
        if edge in seen:
            continue
        seen.add(edge)
        edges.append(edge)

    return edges


class CrossNodeRelationshipEvaluator(FeatureBase):
    """Original cross-node fuzzy evaluator adapted to local imports/state."""

    def __init__(
        self,
        weights: dict[str, float] | None = None,
    ):
        self.weights = weights or {}
        self.fuzzy = FuzzyFeatureAnalyzer(
            node_schema=_CrossNodeSchema(),
            doc_model=_NullDocAlignmentModel(),
            all_weights={
                "cross_node_match": self.weights,
            },
        )

    def analyze(
        self,
        node_dfs: dict[str, pd.DataFrame],
        edges: list[tuple[str, str]],
    ) -> pd.DataFrame:
        results: list[dict[str, Any]] = []
        seen_edges: set[tuple[str, str]] = set()

        for parent_node, child_node in edges:
            edge_key = (parent_node, child_node)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)

            parent_df = node_dfs.get(parent_node)
            child_df = node_dfs.get(child_node)

            if (
                parent_df is None
                or child_df is None
                or parent_df.empty
                or child_df.empty
            ):
                continue

            results.extend(
                self._evaluate_pair(
                    parent_node=parent_node,
                    child_node=child_node,
                    parent_df=parent_df,
                    child_df=child_df,
                )
            )

        result_df = pd.DataFrame(results)
        if result_df.empty:
            return result_df

        sort_columns = [
            column
            for column in ("strength", "support")
            if column in result_df.columns
        ]
        if sort_columns:
            result_df = result_df.sort_values(
                sort_columns,
                ascending=False,
            ).reset_index(drop=True)

        return result_df

    def _evaluate_pair(
        self,
        *,
        parent_node: str,
        child_node: str,
        parent_df: pd.DataFrame,
        child_df: pd.DataFrame,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        threshold = 0.80

        parent_cols = [
            column
            for column in parent_df.columns
            if not looks_like_date_column(parent_df[column])
        ]
        child_cols = [
            column
            for column in child_df.columns
            if not looks_like_date_column(child_df[column])
        ]

        for a in parent_cols:
            found_strong = False
            parent_values = _sample_values(parent_df[a], 40)
            if not parent_values:
                continue

            for b in child_cols:
                child_values = _sample_values(child_df[b], 40)
                if not child_values:
                    continue

                col_a = a
                col_b = b
                if a == b:
                    col_a = f"{a}_{parent_node}"
                    col_b = f"{b}_{child_node}"

                pair_rows: list[dict[str, Any]] = []
                for av in parent_values:
                    for cv in child_values:
                        pair_rows.append(
                            {
                                col_a: normalize_value(av),
                                col_b: normalize_value(cv),
                                "type": "cross_node_match",
                                "name": "cross_node_match",
                            }
                        )
                        if len(pair_rows) >= 1000:
                            break
                    if len(pair_rows) >= 1000:
                        break

                if not pair_rows:
                    continue

                result = self.fuzzy.analyze(
                    pd.DataFrame(pair_rows),
                    col_a,
                    col_b,
                )
                if result is None:
                    continue

                strength = float(result.get("strength", 0.0))
                relation_type = infer_cardinality(
                    parent_df,
                    child_df,
                    a,
                    b,
                )

                result.update(
                    {
                        "parent_node": parent_node,
                        "child_node": child_node,
                        "A": f"{parent_node}.{a}",
                        "B": f"{child_node}.{b}",
                        "feature_type": "cross_node_fuzzy",
                        "relation_type": relation_type,
                    }
                )
                results.append(result)

                if (
                    strength >= threshold
                    and relation_type in ("one_to_many", "one_to_one")
                ):
                    found_strong = True
                    break

            if found_strong:
                break

        return results


def run_cross_analysis(
    *,
    weights_state: dict,
    node_data_state: dict[str, pd.DataFrame],
    node_relationships: pd.DataFrame,
    selected_nodes: list[str],
) -> pd.DataFrame:
    """Shiny migration of the original run_cross_analysis analysis step."""
    if not node_data_state:
        return pd.DataFrame()
    if not selected_nodes or len(selected_nodes) < 2:
        return pd.DataFrame()

    missing_nodes = [
        node
        for node in selected_nodes
        if node not in node_data_state
    ]
    if missing_nodes:
        raise ValueError(
            "Missing data for selected nodes: "
            + ", ".join(missing_nodes)
        )

    edges = find_selected_edges(
        node_relationships,
        selected_nodes,
    )
    if not edges:
        return pd.DataFrame()

    fuzzy_weights = weights_state.get(
        "cross_node_fuzzy",
        {},
    )

    evaluator = CrossNodeRelationshipEvaluator(
        weights=fuzzy_weights,
    )
    return evaluator.analyze(
        node_dfs=node_data_state,
        edges=edges,
    )


def compute_cross_node_analysis(
    *,
    weights_state: dict,
    schema_state: dict,
    node_data_state: dict[str, pd.DataFrame],
    cross_node_analysis_dfs: pd.DataFrame,
    edges_out: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Migrate the original per-child intra + cross combination unchanged."""
    full_analysis: dict[str, pd.DataFrame] = {}

    if (
        cross_node_analysis_dfs is not None
        and not cross_node_analysis_dfs.empty
        and "classification" in cross_node_analysis_dfs.columns
    ):
        filtered_analysis_df = cross_node_analysis_dfs[
            cross_node_analysis_dfs["classification"]
            .astype(str)
            .str.lower()
            .isin(["functional", "strong", "conditional"])
        ].copy()
    else:
        filtered_analysis_df = pd.DataFrame()

    if edges_out is None or edges_out.empty:
        return full_analysis

    processed_children: set[str] = set()

    for _, row in edges_out.iterrows():
        child = str(row["child"])

        # The original loop can encounter the same child on multiple rows.
        # Its final dict value is equivalent to evaluating that child once.
        if child in processed_children:
            continue
        processed_children.add(child)

        df = node_data_state.get(child)
        results = pd.DataFrame()
        cross_node_validation = pd.DataFrame()

        if df is not None and not df.empty:
            schema = schema_state.get(child)

            if schema is not None:
                engine = PairwiseRelationshipEvaluator(
                    schema,
                    weights_state,
                )
                results = engine.evaluate_all_pairs(df)

        if not filtered_analysis_df.empty and "B" in filtered_analysis_df.columns:
            mask = (
                filtered_analysis_df["B"]
                .astype(str)
                .str.lower()
                .str.startswith(child.lower() + ".")
            )
            cross_node_validation = (
                filtered_analysis_df[mask]
                .copy()
                .reset_index(drop=True)
            )

        if not results.empty or not cross_node_validation.empty:
            combined = pd.concat(
                [results, cross_node_validation],
                ignore_index=True,
                sort=False,
            )
        else:
            combined = pd.DataFrame()

        full_analysis[child] = combined

    return full_analysis


def combined_analysis_to_dataframe(
    full_analysis: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Flatten the original per-node analysis dict for Shiny display only."""
    frames: list[pd.DataFrame] = []

    for node_name, frame in full_analysis.items():
        if frame is None or frame.empty:
            continue

        display_frame = frame.copy()
        display_frame.insert(0, "node", node_name)
        frames.append(display_frame)

    if not frames:
        return pd.DataFrame()

    return pd.concat(
        frames,
        ignore_index=True,
        sort=False,
    )
