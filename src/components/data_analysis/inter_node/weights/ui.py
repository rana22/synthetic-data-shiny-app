"""Inter-node feature-weight UI."""

from __future__ import annotations

from shiny import ui


_WEIGHT_LABELS = {
    "support": "Support",
    "ratio": "Ratio",
    "partial_ratio": "Partial Ratio",
    "token_sort_ratio": "Token Sort Ratio",
    "token_set_ratio": "Token Set Ratio",
    "doc_alignment": "Doc Alignment",
}


def inter_node_weights_ui() -> ui.Tag:
    """Render editable cross-node fuzzy feature weights."""

    return ui.div(
        ui.div(
            ui.h2(
                "Feature Weights",
                class_="h5 mb-1",
            ),

            ui.p(
                "Adjust the weights used for cross-node "
                "fuzzy relationship analysis.",
                class_="small text-secondary mb-0",
            ),

            class_="mb-3",
        ),

        ui.output_ui(
            "inter_node_weights_controls"
        ),

        class_="card card-body mb-4",
    )


def fuzzy_weight_slider(
    weight_name: str,
    value: float,
) -> ui.Tag:
    """Render one cross-node fuzzy weight."""

    label = _WEIGHT_LABELS.get(
        weight_name,
        weight_name.replace("_", " ").title(),
    )

    return ui.div(
        ui.div(
            ui.span(
                label,
                class_="fw-semibold",
            ),

            ui.span(
                f"{value:.2f}",
                id=f"inter_node_weight_value_{weight_name}",
                class_="small text-secondary",
            ),

            class_=(
                "d-flex justify-content-between "
                "align-items-center"
            ),
        ),

        ui.input_slider(
            f"inter_node_weight_{weight_name}",
            None,
            min=0.0,
            max=1.0,
            value=value,
            step=0.01,
        ),

        class_="mb-3",
    )