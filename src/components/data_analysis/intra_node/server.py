"""Intra-node analysis server."""

from __future__ import annotations

import pandas as pd

from shiny import reactive, render, ui

from .analysis import PairwiseRelationshipEvaluator


def intra_node_server(
    input,
    output,
    session,
    *,
    analysis_state,
):
    """Manage intra-node property analysis."""
    results_state = reactive.value(
        pd.DataFrame()
    )

    @reactive.effect
    @reactive.event(input.run_intra_node_analysis)
    def _run_analysis():
        selected_node = input.data_analysis_node()

        if not selected_node:
            ui.notification_show(
                "Select a node first.",
                type="warning",
            )
            return

        node_data = analysis_state.node_dataframes.get(
            selected_node
        )

        if node_data is None or node_data.empty:
            ui.notification_show(
                f"No data is available for "
                f"'{selected_node}'.",
                type="warning",
            )
            return

        node_schema = analysis_state.node_schemas.get(
            selected_node
        )

        if node_schema is None:
            ui.notification_show(
                f"No schema is available for "
                f"'{selected_node}'.",
                type="warning",
            )
            return

        try:
            evaluator = PairwiseRelationshipEvaluator(
                node_schema=node_schema,
                weights=analysis_state.feature_weights,
            )

            results = evaluator.evaluate_all_pairs(
                node_data
            )

        except Exception as exc:
            ui.notification_show(
                f"Intra-node analysis failed: {exc}",
                type="error",
            )
            return

        analysis_state.intra_node_results[
            selected_node
        ] = results


        results_state.set(
            results
        )

        ui.notification_show(
            f"Intra-node analysis completed for "
            f"'{selected_node}'.",
            type="message",
        )

    @render.data_frame
    def intra_node_results():
        selected_node = input.data_analysis_node()

        if not selected_node:
            return render.DataGrid(
                pd.DataFrame()
            )

        results = analysis_state.intra_node_results.get(
            selected_node
        )

        if results is None or results.empty:
            return render.DataGrid(
                pd.DataFrame()
            )

        return render.DataGrid(
            results,
            width="100%",
            height="600px",
            filters=True,
        )

    @render.ui
    def intra_node_results_summary():
        results = results_state.get()

        if results.empty:
            return None

        return ui.div(
            ui.strong(
                f"{len(results):,} relationships found"
            ),
            class_="intra-node-results-summary",
        )

    @render.data_frame
    def intra_node_results():
        results = results_state.get()

        if results.empty:
            return render.DataGrid(
                pd.DataFrame()
            )

        return render.DataGrid(
            results,
            width="100%",
            height="600px",
            filters=True,
        )