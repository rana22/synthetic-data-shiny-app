from shiny import ui

from .shared.node_data.ui import node_data_ui
from .intra_node.ui import intra_node_ui
from .inter_node.ui import inter_node_ui
from .shared.model_view.ui import model_view_ui
from .shared.feature_weights import (
    feature_weights_ui,
)

def data_analysis_ui() -> ui.Tag:
    """Render the data-analysis page."""

    return ui.div(
        ui.output_ui(
            "data_analysis_heading"
        ),

        node_data_ui(),

        # Data-model relationships
        model_view_ui(),

        feature_weights_ui(),

        # ui.output_ui(
        #     "analysis_state_debug"
        # ),

        # Analysis workflows.
        intra_node_ui(),

        inter_node_ui(),

        class_="data-analysis-content",
    )