"""Data-analysis page."""

from __future__ import annotations

from shiny import ui


def data_analysis_page() -> ui.Tag:
    """Render the selected-dataset analysis page."""

    return ui.tags.section(
        # --------------------------------------------------------------
        # Page navigation
        # --------------------------------------------------------------
        ui.div(
            ui.a(
                "← Project details",
                href="/project/",
                class_="btn btn-ghost data-analysis-back",
            ),
            class_="data-analysis-navigation",
        ),

        # --------------------------------------------------------------
        # Page heading
        # --------------------------------------------------------------
        ui.div(
            ui.span(
                "DATA ANALYSIS",
                class_="eyebrow",
            ),

            ui.output_ui(
                "data_analysis_heading",
            ),

            class_="data-analysis-heading",
        ),

        # --------------------------------------------------------------
        # Analysis content
        # --------------------------------------------------------------
        ui.output_ui(
            "data_analysis_content",
        ),

        class_="page-section page-data-analysis",
    )