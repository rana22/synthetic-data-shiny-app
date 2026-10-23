"""Inter-node analysis UI."""

from shiny import ui
from .weights import inter_node_weights_ui
from src.components.data_analysis.shared.feature_weights import (
    feature_weights_ui,
)
from ..synthetic_generation import (
    synthetic_generation_ui,
)
def inter_node_ui() -> ui.Tag:
    """Render the inter-node analysis workspace."""

    return ui.div(
        # ----------------------------------------------------------
        # Header
        # ----------------------------------------------------------

        ui.div(
            ui.div(
                ui.a(
                    "← Project Details",
                    href="/project/",
                    class_="small text-decoration-none",
                ),

                ui.h1(
                    "Inter-node Analysis",
                    class_="mt-2 mb-1",
                ),

                ui.p(
                    "Review the disease dataset, supported nodes, "
                    "schema, and graph relationships before "
                    "analyzing relationships across nodes.",
                    class_="text-secondary mb-0",
                ),
            ),

            class_="mb-4",
        ),

        # ----------------------------------------------------------
        # Overview
        # ----------------------------------------------------------

        ui.output_ui(
            "inter_node_dataset_overview"
        ),

        # ----------------------------------------------------------
        # Supported data
        # ----------------------------------------------------------

        ui.div(
            ui.h2(
                "Supported data",
                class_="h5 mb-1",
            ),

            ui.p(
                "Nodes supported for focused analysis "
                "and synthetic data generation.",
                class_="small text-secondary mb-3",
            ),

            ui.output_data_frame(
                "inter_node_supported_nodes"
            ),

            class_="card card-body mb-4",
        ),

        # ----------------------------------------------------------
        # Disease dataset
        # ----------------------------------------------------------

        ui.div(
            ui.h2(
                "Disease dataset",
                class_="h5 mb-1",
            ),

            ui.p(
                "All node types associated with the selected "
                "disease. Only node and row counts are shown.",
                class_="small text-secondary mb-3",
            ),

            ui.output_data_frame(
                "inter_node_disease_nodes"
            ),

            class_="card card-body mb-4",
        ),

        # ----------------------------------------------------------
        # Schema
        # ----------------------------------------------------------

        ui.div(
            ui.div(
                ui.div(
                    ui.h2(
                        "Schema",
                        class_="h5 mb-1",
                    ),

                    ui.p(
                        "Schema nodes and properties available "
                        "for the disease dataset.",
                        class_="small text-secondary mb-0",
                    ),
                ),

                ui.input_action_button(
                    "view_inter_node_schema",
                    "View Schema",
                    class_="btn btn-secondary",
                ),

                class_="d-flex justify-content-between "
                    "align-items-center",
            ),

            ui.output_ui(
                "inter_node_schema_summary"
            ),

            class_="card card-body mb-4",
        ),

        # ----------------------------------------------------------
        # Node tree
        # ----------------------------------------------------------

        ui.div(
            ui.div(
                ui.div(
                    ui.h2(
                        "Node Tree",
                        class_="h5 mb-1",
                    ),

                    ui.p(
                        "Parent and child relationships between "
                        "nodes in the disease data model.",
                        class_="small text-secondary mb-0",
                    ),
                ),

                ui.input_action_button(
                    "view_inter_node_tree",
                    "View Nodes",
                    class_="btn btn-secondary",
                ),

                class_=(
                    "d-flex justify-content-between "
                    "align-items-center"
                ),
            ),

            ui.output_ui(
                "inter_node_tree_summary"
            ),

            class_="card card-body mb-4",
        ),
        # ----------------------------------------------------------
        # Feature weights
        # ----------------------------------------------------------

        feature_weights_ui(),


        # ----------------------------------------------------------
        # Analysis
        # ----------------------------------------------------------

        ui.div(
            ui.div(
                ui.div(
                    ui.h2(
                        "Inter-node Analysis",
                        class_="h5 mb-1",
                    ),
                    ui.p(
                        "Run the migrated cross-node analysis, then combine "
                        "the applicable cross-node relationships with each "
                        "child node's intra-node analysis.",
                        class_="small text-secondary mb-0",
                    ),
                ),
                ui.input_action_button(
                    "run_inter_node_analysis_btn",
                    "Run Inter-node Analysis",
                    class_="btn btn-primary",
                ),
                class_=(
                    "d-flex justify-content-between "
                    "align-items-center mb-3"
                ),
            ),
            ui.output_ui(
                "inter_node_results_summary"
            ),
            ui.output_data_frame(
                "inter_node_results"
            ),
            class_="card card-body mb-4",
        ),

        # ----------------------------------------------------------
        # Synthetic data generation
        # ----------------------------------------------------------

        ui.output_ui(
            "synthetic_generation_section"
        ),
        class_=(
            "container-fluid "
            "inter-node-analysis"
        ),

        
    )