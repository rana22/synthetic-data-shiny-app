"""Inter-node feature-weight server."""

from __future__ import annotations

from shiny import reactive, render, ui


def inter_node_weights_server(
    input,
    output,
    session,
    *,
    analysis_state,
):
    """Manage cross-node fuzzy feature weights."""

    @render.ui
    def inter_node_weights_controls():
        weights = (
            analysis_state
            .feature_weights
            .get(
                "cross_node_fuzzy",
                {},
            )
        )

        if not weights:
            return ui.p(
                "Cross-node fuzzy weights are not available.",
                class_="small text-secondary",
            )

        from .ui import fuzzy_weight_slider

        return ui.div(
            *[
                fuzzy_weight_slider(
                    weight_name,
                    float(value),
                )
                for weight_name, value
                in weights.items()
            ],
            class_="inter-node-weight-controls",
        )

    # --------------------------------------------------------------
    # Weight changes
    # --------------------------------------------------------------

    weights = (
        analysis_state
        .feature_weights
        .get(
            "cross_node_fuzzy",
            {},
        )
    )

    for weight_name in weights:

        def register_weight_effect(
            name=weight_name,
        ):
            input_name = (
                f"inter_node_weight_{name}"
            )

            @reactive.effect
            def _update_weight():
                value = getattr(
                    input,
                    input_name,
                )()

                if value is None:
                    return

                analysis_state.feature_weights[
                    "cross_node_fuzzy"
                ][name] = float(value)

        register_weight_effect()