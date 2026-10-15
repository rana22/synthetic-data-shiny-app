import pandas as pd
from shiny import reactive, render, ui

from .ui import (
    node_summary_ui,
    preview_description_ui,
)


def node_data_server(
    input,
    output,
    session,
    *,
    analysis_state,
):
    """Manage node selection and node-data preview."""

    @reactive.effect
    def _initialize_node_selector():
        node_names = list(
            analysis_state.node_dataframes.keys()
        )

        if not node_names:
            return

        ui.update_select(
            "data_analysis_node",
            choices=node_names,
            selected=node_names[0],
        )

    def get_selected_node_dataframe(
    ) -> tuple[str | None, pd.DataFrame | None]:

        selected_node = input.data_analysis_node()

        if not selected_node:
            return None, None

        data = analysis_state.node_dataframes.get(
            selected_node
        )

        if data is None:
            return None, None

        analysis_state.selected_node = selected_node

        return selected_node, data

    @render.ui
    def data_analysis_node_summary():
        selected_node, data = (
            get_selected_node_dataframe()
        )

        if selected_node is None or data is None:
            return None

        return node_summary_ui(
            node_name=selected_node,
            row_count=len(data),
            property_count=len(data.columns),
        )

    @render.ui
    def data_analysis_preview_description():
        selected_node, data = (
            get_selected_node_dataframe()
        )

        return preview_description_ui(
            selected_node=selected_node,
            has_data=data is not None,
        )

    @render.data_frame
    def data_analysis_preview():
        _selected_node, data = (
            get_selected_node_dataframe()
        )

        if data is None:
            return render.DataGrid([])

        return render.DataGrid(
            data.head(100),
            width="100%",
            height="500px",
        )