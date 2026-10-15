from shiny import ui


def model_view_ui() -> ui.Tag:
    """Render the data-model viewer action."""

    return ui.div(
        ui.div(
            ui.h2("Data Model"),

            ui.p(
                "View the parent and child relationships "
                "for nodes in the imported dataset.",
                class_="data-analysis-section-description",
            ),

            ui.div(
                ui.input_action_button(
                    "view_schema",
                    "View Schema",
                    class_="btn btn-secondary",
                ),

                ui.input_action_button(
                    "view_data_model",
                    "View Nodes",
                    class_="btn btn-secondary",
                ),

                class_="data-analysis-actions",
            ),

            class_="data-analysis-section-header",
        ),

        class_="data-analysis-section",
    )


def schema_view_modal() -> ui.Tag:
    """Render the schema viewer."""

    return ui.modal(
        ui.output_ui(
            "schema_view_content"
        ),
        title="Schema View",
        size="xl",
        easy_close=True,
    )


def model_view_modal() -> ui.Tag:
    """Render the node relationship table."""

    return ui.modal(
        ui.output_data_frame(
            "data_model_tree"
        ),

        title="Data Model",
        size="xl",
        easy_close=True,
    )