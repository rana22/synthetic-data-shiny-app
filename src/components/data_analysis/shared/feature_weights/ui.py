"""Feature weights UI."""

from shiny import ui


def feature_weights_ui() -> ui.Tag:
    """Render configurable feature weights."""

    return ui.div(
        ui.div(
            ui.h2("Feature Weights"),
            ui.p(
                "Configure the weights used for property "
                "relationship analysis.",
                class_="text-muted",
            ),
        ),

        ui.output_ui(
            "feature_weights_content"
        ),

        class_="data-analysis-section feature-weights",
    )