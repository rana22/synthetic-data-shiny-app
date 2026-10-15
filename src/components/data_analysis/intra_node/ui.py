"""Intra-node analysis UI."""

from shiny import ui



def intra_node_ui() -> ui.Tag:
    """Render intra-node property relationship analysis."""

    return ui.div(
        ui.div(
            ui.h2("Intra-node Analysis"),

            ui.p(
                "Analyze relationships between properties "
                "within the selected node.",
                class_="text-muted",
            ),

            ui.input_action_button(
                "run_intra_node_analysis",
                "Run Analysis",
                class_="btn btn-primary",
            ),

            class_="intra-node-header",
        ),

        ui.output_ui(
            "intra_node_results_summary"
        ),

        ui.output_data_frame(
            "intra_node_results"
        ),

        class_="data-analysis-section intra-node-analysis",
    )