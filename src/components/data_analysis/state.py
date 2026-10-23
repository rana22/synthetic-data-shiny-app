from dataclasses import dataclass, field
import copy
import pandas as pd
from .features.weights import node_features_2_weight


@dataclass
class AnalysisState:
    """State owned by the data-analysis workflow."""

    # --------------------------------------------------------------
    # Source data
    # --------------------------------------------------------------

    # Complete disease-specific dataset.
    #
    # Includes generation nodes AND context/linkage nodes such as
    # study, publication, program, etc.
    #
    # Used by inter-node analysis.
    # All node data associated with the selected disease.
    disease_node_dataframes: dict[str, pd.DataFrame] = field(
        default_factory=dict
    )

    # Supported nodes used for focused analysis / generation.
    # Subset of disease_node_dataframes.
    supported_node_dataframes: dict[str, pd.DataFrame] = field(
        default_factory=dict
    )

    # Disease associated with the loaded dataset.
    selected_disease_term: str | None = None

    # --------------------------------------------------------------
    # Schema
    # --------------------------------------------------------------

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

    # --------------------------------------------------------------
    # Current UI selection
    # --------------------------------------------------------------

    selected_node: str | None = None

    # --------------------------------------------------------------
    # Analysis results
    # --------------------------------------------------------------

    intra_node_results: dict[str, pd.DataFrame] = field(
        default_factory=dict
    )

    inter_node_results: pd.DataFrame = field(
        default_factory=pd.DataFrame
    )

    # --------------------------------------------------------------
    # Feature configuration
    # --------------------------------------------------------------

    feature_weights: dict = field(
        default_factory=lambda: copy.deepcopy(
            node_features_2_weight
        )
    )

    normalized_weights: dict = field(
        default_factory=dict
    )