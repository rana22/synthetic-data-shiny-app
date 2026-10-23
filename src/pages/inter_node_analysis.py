"""Inter-node analysis page."""

from shiny import ui

from src.components.data_analysis.inter_node import (
    inter_node_ui,
)


def inter_node_analysis_page() -> ui.Tag:
    """Render the inter-node analysis page."""

    return ui.div(
        inter_node_ui(),
        class_="inter-node-analysis-page",
    )