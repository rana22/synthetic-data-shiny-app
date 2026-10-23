# """Data-analysis page server."""

# from __future__ import annotations

# from pathlib import Path

# import pandas as pd
# from shiny import render, ui


# def _metric_card(
#     label: str,
#     value: str,
# ) -> ui.Tag:
#     """Render one dataset metric."""

#     return ui.div(
#         ui.span(
#             label,
#             class_="data-analysis-metric-label",
#         ),
#         ui.span(
#             value,
#             class_="data-analysis-metric-value",
#         ),
#         class_="data-analysis-metric",
#     )


# def _format_count(value: int) -> str:
#     """Format an integer count for display."""

#     return f"{value:,}"


# def _node_selector(node_dataframes: dict[str, pd.DataFrame]) -> ui.Tag:
#     """Render a selector for the node DataFrames available for analysis."""

#     node_names = list(node_dataframes.keys())

#     if not node_names:
#         return ui.div(
#             ui.div(
#                 ui.h2("Node types"),
#                 ui.p(
#                     "No node data is available for this dataset.",
#                     class_="data-analysis-section-description",
#                 ),
#                 class_="data-analysis-section-header",
#             ),
#             class_="data-analysis-section",
#         )

#     return ui.div(
#         ui.div(
#             ui.h2("Node type"),
#             ui.p(
#                 "Select a node to preview and analyze its properties.",
#                 class_="data-analysis-section-description",
#             ),
#             class_="data-analysis-section-header",
#         ),
#         ui.input_select(
#             "data_analysis_node",
#             "Select node",
#             choices=node_names,
#             selected=node_names[0],
#         ),
#         class_="data-analysis-section",
#     )


# def data_analysis_server(
#     input,
#     output,
#     session,
#     *,
#     app_state,
# ):
#     """Analyze and display the selected imported dataset by node type."""

#     # ------------------------------------------------------------------
#     # Resolve selected dataset and grouped node data
#     # ------------------------------------------------------------------

#     def get_selected_dataset() -> Path | None:
#         """Return the source file selected for analysis."""

#         workspace = app_state.active_workspace
#         selected = app_state.selected_dataset

#         if workspace is None or selected is None:
#             return None

#         return selected

#     def get_node_dataframes() -> dict[str, pd.DataFrame]:
#         """Return node DataFrames stored for the selected dataset."""

#         node_dfs = getattr(
#             app_state,
#             "node_dataframes",
#             None,
#         )

#         if node_dfs is None:
#             return {}

#         if isinstance(node_dfs, pd.DataFrame):
#             return {}

#         if not isinstance(node_dfs, dict):
#             return {}

#         return node_dfs

#     def get_selected_node_dataframe() -> tuple[str | None, pd.DataFrame | None]:
#         """Return the currently selected node name and its DataFrame."""

#         node_dataframes = get_node_dataframes()
#         if not node_dataframes:
#             return None, None

#         selected_node = input.data_analysis_node()
#         if not selected_node:
#             return None, None

#         return selected_node, node_dataframes.get(selected_node)

#     # ------------------------------------------------------------------
#     # Heading
#     # ------------------------------------------------------------------

#     @render.ui
#     def data_analysis_heading():
#         file_path = get_selected_dataset()

#         if file_path is None:
#             return ui.div(
#                 ui.h1("Data analysis"),
#                 ui.p(
#                     "No dataset is currently selected.",
#                     class_="lead",
#                 ),
#             )

#         return ui.div(
#             ui.h1(file_path.name),
#             ui.p(
#                 "Review and analyze the imported data by node type.",
#                 class_="lead",
#             ),
#         )

#     # ------------------------------------------------------------------
#     # Analysis page content
#     # ------------------------------------------------------------------

#     @render.ui
#     def data_analysis_content():
#         file_path = get_selected_dataset()

#         if file_path is None:
#             return ui.div(
#                 ui.p(
#                     "Select an imported file before opening Data Analysis."
#                 ),
#                 ui.a(
#                     "Return to project",
#                     href="/project/",
#                     class_="btn btn-primary",
#                 ),
#                 class_="data-analysis-empty",
#             )

#         node_dataframes = get_node_dataframes()

#         if not node_dataframes:
#             return ui.div(
#                 ui.h3("Unable to analyze dataset"),
#                 ui.p(
#                     "No grouped node data is available. Return to the project "
#                     "and select Analyze for the imported file again."
#                 ),
#                 ui.a(
#                     "Return to project",
#                     href="/project/",
#                     class_="btn btn-primary",
#                 ),
#                 class_="workspace-status workspace-status-error",
#             )

#         return ui.div(
#             _node_selector(node_dataframes),

#             # ----------------------------------------------------------
#             # Selected-node metrics
#             # ----------------------------------------------------------
#             ui.output_ui("data_analysis_node_summary"),

#             # ----------------------------------------------------------
#             # Selected-node dataset preview
#             # ----------------------------------------------------------
#             ui.div(
#                 ui.div(
#                     ui.h2("Dataset"),
#                     ui.output_ui("data_analysis_preview_description"),
#                     class_="data-analysis-section-header",
#                 ),
#                 ui.output_data_frame("data_analysis_preview"),
#                 class_="data-analysis-section",
#             ),

#             # ----------------------------------------------------------
#             # Future migrated analysis
#             # ----------------------------------------------------------
#             ui.div(
#                 ui.h2("Analysis"),
#                 ui.p(
#                     "The existing synthetic-data analysis workflow "
#                     "will be integrated here for the selected node.",
#                     class_="data-analysis-placeholder",
#                 ),
#                 class_="data-analysis-section",
#             ),

#             class_="data-analysis-content",
#         )

#     # ------------------------------------------------------------------
#     # Selected-node summary
#     # ------------------------------------------------------------------

#     @render.ui
#     def data_analysis_node_summary():
#         selected_node, data = get_selected_node_dataframe()

#         if selected_node is None or data is None:
#             return None

#         return ui.div(
#             _metric_card(
#                 "Rows",
#                 _format_count(len(data)),
#             ),
#             _metric_card(
#                 "Properties",
#                 _format_count(len(data.columns)),
#             ),
#             _metric_card(
#                 "Node type",
#                 selected_node,
#             ),
#             class_="data-analysis-metrics",
#         )

#     @render.ui
#     def data_analysis_preview_description():
#         selected_node, data = get_selected_node_dataframe()

#         if selected_node is None or data is None:
#             return ui.p(
#                 "Select a node to preview its data.",
#                 class_="data-analysis-section-description",
#             )

#         return ui.p(
#             f'Preview of the first 100 rows for node "{selected_node}".',
#             class_="data-analysis-section-description",
#         )

#     # ------------------------------------------------------------------
#     # Selected-node data preview
#     # ------------------------------------------------------------------

#     @render.data_frame
#     def data_analysis_preview():
#         _selected_node, data = get_selected_node_dataframe()

#         if data is None:
#             return render.DataGrid([])

#         return render.DataGrid(
#             data.head(100),
#             width="100%",
#             height="500px",
#         )
from shiny import ui, render, reactive
import json
from .state import AnalysisState
from .shared.node_data.server import node_data_server
from .shared.model_view.server import model_view_server
from .intra_node.server import intra_node_server
from .inter_node.server import inter_node_server
from .shared.feature_weights import (
    feature_weights_server,
)



def data_analysis_server(
    input,
    output,
    session,
    *,
    app_state,
):
    """Coordinate the data-analysis workflow."""
    weights_changed = reactive.value(0)
   
    analysis_state = app_state.analysis

    print("\n--- ANALYSIS STATE ---")
    print("analysis_state:", analysis_state)
    print(
        "node_dataframes type:",
        type(analysis_state.supported_node_dataframes),
    )
    print(
        "nodes:",
        list(analysis_state.supported_node_dataframes.keys()),
    )

    def update_feature_weight(
        *,
        feature_name: str,
        node_name: str | None,
        weight_name: str,
        value: float,
    ):
        """Update a feature weight in AnalysisState."""

        if feature_name == "cross_node_fuzzy":
            analysis_state.feature_weights[
                feature_name
            ][weight_name] = value

            return

        if node_name is None:
            return

        analysis_state.feature_weights[
            feature_name
        ][node_name][weight_name] = value
        

    for node_name, df in analysis_state.supported_node_dataframes.items():
        print(
            f"{node_name}: "
            f"type={type(df)}, "
            f"shape={df.shape}"
        )

    node_data_server(
        input,
        output,
        session,
        analysis_state=analysis_state,
    )

    model_view_server(
        input,
        output,
        session,
        app_state=app_state,
        analysis_state=analysis_state,
    )

    feature_weights_server(
        input,
        output,
        session,
        analysis_state=analysis_state,
        update_weight=update_feature_weight,
    )

    intra_node_server(
        input,
        output,
        session,
        analysis_state=analysis_state,
    )

    inter_node_server(
        input,
        output,
        session,
        app_state=app_state,
    )

    # @render.ui
    # def analysis_state_debug():
    #     """Temporary view of parent AnalysisState weights."""

    #     weights_changed.get()

    #     return ui.div(
    #         ui.h4("Analysis State Debug"),

    #         ui.tags.pre(
    #             json.dumps(
    #                 analysis_state.feature_weights,
    #                 indent=2,
    #             )
    #         ),

    #         class_="data-analysis-section",
    #     )