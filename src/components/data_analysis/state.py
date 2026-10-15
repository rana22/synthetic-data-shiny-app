from dataclasses import dataclass, field
import copy
import pandas as pd
from .features.weights import node_features_2_weight


@dataclass
class AnalysisState:
    """State owned by the data-analysis workflow."""

    node_dataframes: dict[str, pd.DataFrame] = field(
        default_factory=dict
    )

    node_schemas: dict = field(
        default_factory=dict
    )

    node_relationships: pd.DataFrame = field(
        default_factory=pd.DataFrame
    )

    node_tree: pd.DataFrame = field(
        default_factory=pd.DataFrame
    )

    join_paths: pd.DataFrame = field(
        default_factory=pd.DataFrame
    )

    selected_node: str | None = None

    intra_node_results: dict = field(
        default_factory=dict
    )

    inter_node_results: dict = field(
        default_factory=dict
    )

    feature_weights: dict = field(
        default_factory=lambda: copy.deepcopy(
            node_features_2_weight
        )
    )
    normalized_weights: dict = field(
        default_factory=dict
    )