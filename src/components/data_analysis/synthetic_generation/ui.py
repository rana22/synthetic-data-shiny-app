"""Synthetic data generation UI."""

from __future__ import annotations

from shiny import ui


def synthetic_generation_ui() -> ui.Tag:
    """Render synthetic data generation controls and results."""

    return ui.div(
        # ----------------------------------------------------------
        # Header
        # ----------------------------------------------------------

        ui.div(
            ui.h2(
                "Synthetic Data Generation",
                class_="h5 mb-1",
            ),

            ui.p(
                "Configure the number of synthetic rows "
                "to generate for each supported node.",
                class_="small text-secondary mb-0",
            ),

            class_="mb-4",
        ),

        # ----------------------------------------------------------
        # Per-node row configuration
        # ----------------------------------------------------------

        ui.output_ui(
            "synthetic_generation_node_inputs"
        ),

        # ----------------------------------------------------------
        # Generate
        # ----------------------------------------------------------

        ui.div(
            ui.input_action_button(
                "generate_synthetic_data",
                "Generate Synthetic Data",
                class_="btn btn-primary",
            ),

            class_=(
                "d-flex justify-content-end mt-3"
            ),
        ),

        # ----------------------------------------------------------
        # Generation summary
        # ----------------------------------------------------------

        ui.output_ui(
            "synthetic_generation_summary"
        ),

        # ----------------------------------------------------------
        # Generated node selector
        # ----------------------------------------------------------

        ui.output_ui(
            "synthetic_generation_results_controls"
        ),

        # ----------------------------------------------------------
        # Valid generated rows
        # ----------------------------------------------------------

        ui.output_data_frame(
            "synthetic_generation_results"
        ),

        class_="card card-body mb-4",
    )