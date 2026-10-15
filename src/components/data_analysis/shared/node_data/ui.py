from shiny import ui


def metric_card(
    label: str,
    value: str,
) -> ui.Tag:
    return ui.div(
        ui.span(
            label,
            class_="data-analysis-metric-label",
        ),
        ui.span(
            value,
            class_="data-analysis-metric-value",
        ),
        class_="data-analysis-metric",
    )


def node_selector_ui(
    node_names: list[str],
) -> ui.Tag:

    if not node_names:
        return ui.div(
            ui.h2("Node types"),
            ui.p(
                "No node data is available.",
                class_="data-analysis-section-description",
            ),
            class_="data-analysis-section",
        )

    return ui.div(
        ui.div(
            ui.h2("Node type"),
            ui.p(
                "Select a node to preview and analyze "
                "its properties.",
                class_="data-analysis-section-description",
            ),
            class_="data-analysis-section-header",
        ),
        ui.input_select(
            "data_analysis_node",
            "Select node",
            choices=node_names,
            selected=node_names[0],
        ),
        class_="data-analysis-section",
    )


def node_summary_ui(
    *,
    node_name: str,
    row_count: int,
    property_count: int,
) -> ui.Tag:
    return ui.div(
        metric_card(
            "Rows: ",
            f"{row_count:,}",
        ),
        metric_card(
            "Properties: ",
            f"{property_count:,}",
        ),
        metric_card(
            "Node type: ",
            node_name,
        ),
        class_="data-analysis-metrics",
    )


def preview_description_ui(
    *,
    selected_node: str | None,
    has_data: bool,
) -> ui.Tag:

    if not selected_node or not has_data:
        return ui.p(
            "Select a node to preview its data.",
            class_="data-analysis-section-description",
        )

    return ui.p(
        f'Preview of the first 100 rows for '
        f'node "{selected_node}".',
        class_="data-analysis-section-description",
    )

def node_data_ui() -> ui.Tag:
    """Render node selection and data preview."""

    return ui.div(
        ui.div(
            ui.div(
                ui.h2("Node type"),
                ui.p(
                    "Select a node to preview and analyze "
                    "its properties.",
                    class_="data-analysis-section-description",
                ),
                class_="data-analysis-section-header",
            ),

            ui.input_select(
                "data_analysis_node",
                "Select node",
                choices=[],
            ),

            class_="data-analysis-section",
        ),

        ui.output_ui(
            "data_analysis_node_summary"
        ),

        ui.div(
            ui.div(
                ui.h2("Dataset"),

                ui.output_ui(
                    "data_analysis_preview_description"
                ),

                class_="data-analysis-section-header",
            ),

            ui.output_data_frame(
                "data_analysis_preview"
            ),

            class_="data-analysis-section",
        ),
    )