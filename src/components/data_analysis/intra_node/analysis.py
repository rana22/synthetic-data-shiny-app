"""Intra-node property relationship analysis."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.services.schema import NodeSchema

from ..features.base import FeatureBase
from ..features.categorical import CategoricalFeatureAnalyzer
from ..features.substring import SubstringFeatureAnalyzer
from ..features.cluster import ClusteringFeatureAnalyzer
from ..features.doc_alignment import DocAlignmentModel

class PairwiseRelationshipEvaluator(FeatureBase):
    """Evaluate relationships between properties within one node."""

    def __init__(
        self,
        node_schema: NodeSchema,
        weights: dict[str, Any] | None = None,
    ):
        self.node_schema = node_schema
        self.weights = weights or {}

        # Document alignment is not currently enabled.
        self.doc_model = DocAlignmentModel().fit(
            node_schema
        )

        self.categorical = CategoricalFeatureAnalyzer(
            node_schema=self.node_schema,
            doc_model=self.doc_model,
            all_weights=self.weights.get(
                "categorical"
            ),
        )

        self.substring = SubstringFeatureAnalyzer(
            node_schema=self.node_schema,
            doc_model=self.doc_model,
            all_weights=self.weights.get(
                "substring"
            ),
        )

        self.cluster = ClusteringFeatureAnalyzer(
            node_schema=self.node_schema,
            doc_model=self.doc_model,
            all_weights=self.weights.get(
                "cluster"
            ),
        )

    def get_model_columns(
        self,
        df: pd.DataFrame,
    ) -> list[str]:
        """Return schema properties available in the node data."""

        schema_columns = list(
            getattr(
                self.node_schema,
                "properties",
                {},
            ).keys()
        )

        return [
            column
            for column in schema_columns
            if (
                column in df.columns
                and not self.should_skip(
                    column,
                    self.node_schema,
                )
            )
        ]

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Evaluate all eligible property pairs."""

        return self.evaluate_all_pairs(df)

    def evaluate_all_pairs(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Run feature analyzers against all property pairs."""

        results: list[dict[str, Any]] = []

        columns = self.get_model_columns(df)

        for property_a in columns:
            for property_b in columns:
                if property_a == property_b:
                    continue

                # --------------------------------------------------
                # Categorical
                # --------------------------------------------------

                categorical_result = (
                    self.categorical.analyze(
                        df,
                        property_a,
                        property_b,
                    )
                )

                if categorical_result is not None:
                    results.append(
                        categorical_result
                    )

                # --------------------------------------------------
                # Substring
                # --------------------------------------------------

                substring_result = (
                    self.substring.analyze(
                        df,
                        property_a,
                        property_b,
                    )
                )

                if substring_result is not None:
                    results.append(
                        substring_result
                    )

                # --------------------------------------------------
                # Cluster
                # --------------------------------------------------

                cluster_result = (
                    self.cluster.analyze(
                        df,
                        property_a,
                        property_b,
                    )
                )

                if cluster_result is not None:
                    results.append(
                        cluster_result
                    )

        results_df = pd.DataFrame(
            results
        )

        if results_df.empty:
            return results_df

        # ----------------------------------------------------------
        # Sort strongest relationships first
        # ----------------------------------------------------------

        sort_columns = [
            column
            for column in (
                "strength",
                "predictive_strength",
                "support",
            )
            if column in results_df.columns
        ]

        if sort_columns:
            results_df = (
                results_df
                .sort_values(
                    by=sort_columns,
                    ascending=False,
                )
                .reset_index(
                    drop=True
                )
            )

        return results_df