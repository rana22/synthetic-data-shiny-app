from __future__ import annotations

import re

from shiny import ui

from src.disease import (
    DiseaseNodeStatus,
    DiseaseNodeSupport,
    DiseaseSupportStatus,
    DiseaseSupportSummary,
)

def disease_select_button_id(
    disease: str,
) -> str:
    """Return the action button ID for one disease."""

    return (
        "select_disease_"
        f"{_input_slug(disease)}"
    )

# ---------------------------------------------------------------------------
# Input IDs
# ---------------------------------------------------------------------------


def _input_slug(value: str) -> str:
    """Return a safe fragment for a Shiny input ID."""

    return re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        value.strip().lower(),
    ).strip("_")


def disease_node_input_id(
    disease: str,
    node_name: str,
) -> str:
    """Return the Shiny input ID for one disease/node checkbox."""

    return (
        "disease_node_"
        f"{_input_slug(disease)}_"
        f"{_input_slug(node_name)}"
    )


# ---------------------------------------------------------------------------
# Modal
# ---------------------------------------------------------------------------


def disease_support_modal(
    source_name: str,
) -> ui.Tag:
    """Render the disease-support browser."""

    return ui.modal(
        ui.div(
            # ----------------------------------------------------------
            # Close button
            # ----------------------------------------------------------
            ui.tags.button(
                type="button",
                class_="btn-close disease-support__close",
                aria_label="Close",
                data_bs_dismiss="modal",
            ),

            # ----------------------------------------------------------
            # Introduction
            # ----------------------------------------------------------
            ui.div(
                ui.h2(
                    "Disease-specific source data",
                    class_="disease-support-title",
                ),

                ui.p(
                    "Review which disease terms have validated "
                    "source data available for analysis and "
                    "synthetic data generation.",
                    class_="disease-support-description",
                ),

                class_="disease-support-heading",
            ),

            # ----------------------------------------------------------
            # Search
            # ----------------------------------------------------------
            ui.div(
                ui.input_text(
                    "disease_support_search",
                    None,
                    placeholder="Search disease terms...",
                ),

                class_="disease-support__search",
            ),

            # ----------------------------------------------------------
            # Dynamic results
            # ----------------------------------------------------------
            ui.output_ui(
                "disease_support_content",
            ),

            class_=(
                "disease-support "
                "disease-support-content "
                "position-relative"
            ),
        ),

        title=f"Disease support — {source_name}",
        easy_close=True,
        size="xl",
    )


# ---------------------------------------------------------------------------
# Complete result
# ---------------------------------------------------------------------------


def disease_support_results(
    summaries: tuple[DiseaseSupportSummary, ...],
    *,
    visible_summaries: (
        tuple[DiseaseSupportSummary, ...]
        | None
    ) = None,
) -> ui.Tag:
    """Render the complete disease-support result."""

    if visible_summaries is None:
        visible_summaries = summaries

    visible_count = len(visible_summaries)
    total_count = len(summaries)

    return ui.div(
        disease_support_summary_cards(
            summaries
        ),

        disease_support_result_count(
            visible_count=visible_count,
            total_count=total_count,
        ),

        disease_support_accordion(
            visible_summaries
        ),

        ui.div(
            ui.h4(
                "Selected for analysis",
                class_="h6 fw-semibold mb-1",
            ),

            ui.p(
                "Choose the nodes in a disease accordion and click "
                "Select for analysis. Then load those records.",
                class_="small text-secondary mb-3",
            ),

            ui.output_ui(
                "selected_disease_summary",
            ),

            ui.div(
                ui.input_action_button(
                    "load_selected_disease_data",
                    "Load selected data",
                    class_="btn btn-secondary",
                ),

                ui.input_action_button(
                    "view_selected_disease_data",
                    "View loaded data",
                    class_="btn btn-secondary",
                ),

                ui.input_action_button(
                    "use_disease_data_for_analysis",
                    "Use for analysis",
                    class_="btn btn-primary",
                ),

                class_="d-flex gap-2 flex-wrap mt-3",
            ),

            ui.output_ui(
                "disease_data_load_status",
            ),

            # ----------------------------------------------------------
            # Inline loaded-data viewer
            # ----------------------------------------------------------

            ui.output_ui(
                "selected_disease_data_viewer",
            ),

            class_=(
                "border rounded-3 p-3 mt-4 "
                "disease-support__analysis-actions"
            ),
        ),

        class_="disease-support-results",
    )


# ---------------------------------------------------------------------------
# Result count
# ---------------------------------------------------------------------------


def disease_support_result_count(
    *,
    visible_count: int,
    total_count: int,
) -> ui.Tag:
    """Render the number of currently visible disease terms."""

    if visible_count == total_count:
        message = (
            f"{total_count:,} disease "
            f"{'term' if total_count == 1 else 'terms'}"
        )
    else:
        message = (
            f"{visible_count:,} of {total_count:,} disease "
            f"{'term' if total_count == 1 else 'terms'}"
        )

    return ui.div(
        ui.span(
            message,
            class_="small text-secondary fw-semibold",
        ),

        class_="d-flex align-items-center my-3",
    )


# ---------------------------------------------------------------------------
# Summary cards
# ---------------------------------------------------------------------------


def disease_support_summary_cards(
    summaries: tuple[DiseaseSupportSummary, ...],
) -> ui.Tag:
    """Render disease-level support totals."""

    supported = sum(
        summary.status
        == DiseaseSupportStatus.SUPPORTED
        for summary in summaries
    )

    limited = sum(
        summary.status
        == DiseaseSupportStatus.LIMITED
        for summary in summaries
    )

    unsupported = sum(
        summary.status
        == DiseaseSupportStatus.UNSUPPORTED
        for summary in summaries
    )

    return ui.div(
        _summary_card(
            len(summaries),
            "Disease terms found",
            modifier="total",
        ),

        _summary_card(
            supported,
            "Supported",
            modifier="supported",
        ),

        _summary_card(
            limited,
            "Limited",
            modifier="limited",
        ),

        _summary_card(
            unsupported,
            "Unsupported",
            modifier="unsupported",
        ),

        class_="row g-3 disease-support__metrics",
    )


def _summary_card(
    value: int,
    label: str,
    *,
    modifier: str,
) -> ui.Tag:
    """Render one disease-support summary metric."""

    icon = {
        "total": "●",
        "supported": "✓",
        "limited": "!",
        "unsupported": "×",
    }[modifier]

    return ui.div(
        ui.div(
            ui.div(
                ui.div(
                    ui.div(
                        icon,
                        class_=(
                            "disease-support__metric-icon "
                            f"disease-support__metric-icon--{modifier}"
                        ),
                    ),

                    ui.div(
                        ui.div(
                            f"{value:,}",
                            class_="disease-support__metric-value",
                        ),

                        ui.div(
                            label,
                            class_="disease-support__metric-label",
                        ),

                        class_="disease-support__metric-copy",
                    ),

                    class_="d-flex align-items-center gap-3",
                ),

                class_="card-body",
            ),

            class_=(
                "card h-100 "
                "disease-support__metric "
                f"disease-support__metric--{modifier}"
            ),
        ),

        class_="col-12 col-sm-6 col-xl-3",
    )


# ---------------------------------------------------------------------------
# Accordion
# ---------------------------------------------------------------------------


def disease_support_accordion(
    summaries: tuple[DiseaseSupportSummary, ...],
) -> ui.Tag:
    """Render disease support as accordion panels."""

    panels = [
        disease_support_panel(
            summary
        )
        for summary in summaries
    ]

    return ui.accordion(
        *panels,
        id="disease_support_accordion",
        multiple=False,
        open=False,
        class_="disease-support-accordion",
    )


def disease_support_panel(
    summary: DiseaseSupportSummary,
) -> ui.Tag:
    """Render one disease-support accordion panel."""

    status_label = {
        DiseaseSupportStatus.SUPPORTED:
            "Supported",

        DiseaseSupportStatus.LIMITED:
            "Limited",

        DiseaseSupportStatus.UNSUPPORTED:
            "Unsupported",
    }[summary.status]

    status_badge_class = {
        DiseaseSupportStatus.SUPPORTED:
            "text-bg-success",

        DiseaseSupportStatus.LIMITED:
            "text-bg-warning",

        DiseaseSupportStatus.UNSUPPORTED:
            "text-bg-danger",
    }[summary.status]

    ready_nodes = tuple(
        node
        for node in summary.generation_nodes
        if node.status
        == DiseaseNodeStatus.READY
    )

    support_header = ui.div(
        ui.span(
            status_label,
            class_=(
                "badge rounded-pill "
                f"{status_badge_class}"
            ),
        ),

        ui.span(
            (
                f"{len(ready_nodes)} ready generation nodes "
                f"· {summary.usable_row_count:,} usable rows"
            ),
            class_="small text-secondary",
        ),

        class_=(
            "d-flex align-items-center "
            "gap-2 flex-wrap mb-3"
        ),
    )

    unsupported_notice = None

    if (
        summary.status
        == DiseaseSupportStatus.UNSUPPORTED
    ):
        unsupported_notice = ui.div(
            "This disease exists in the reference source "
            "but is not part of the validated disease vocabulary.",
            class_="alert alert-danger py-2 mb-3",
            role="alert",
        )

    return ui.accordion_panel(
        summary.disease,

        ui.div(
            support_header,
            unsupported_notice,

            disease_node_selection_table(
                summary
            ),
            ui.div(
                ui.input_action_button(
                    disease_select_button_id(
                        summary.disease
                    ),
                    "Select for analysis",
                    class_="btn btn-primary",
                ),

                class_="d-flex justify-content-end mt-3",
            ),
            class_="disease-support__panel-content",
        ),
    )


# ---------------------------------------------------------------------------
# Node-selection table
# ---------------------------------------------------------------------------


def disease_node_selection_table(
    summary: DiseaseSupportSummary,
) -> ui.Tag:
    """Render selectable disease nodes in one table."""

    nodes = (
        summary.generation_nodes
        + summary.context_nodes
    )

    return ui.div(
        ui.div(
            ui.h4(
                "Nodes for analysis",
                class_="h6 fw-semibold mb-1",
            ),

            ui.p(
                "Ready nodes are selected by default. "
                "Additional nodes can be selected if needed.",
                class_="small text-secondary mb-3",
            ),
        ),

        ui.tags.div(
            ui.tags.table(
                ui.tags.thead(
                    ui.tags.tr(
                        ui.tags.th(
                            "",
                            scope="col",
                            class_="disease-support__select-column",
                        ),

                        ui.tags.th(
                            "Node type",
                            scope="col",
                        ),

                        ui.tags.th(
                            "Rows",
                            scope="col",
                            class_="text-end",
                        ),

                        ui.tags.th(
                            "Status",
                            scope="col",
                            class_="text-end",
                        ),
                    )
                ),

                ui.tags.tbody(
                    *[
                        disease_node_selection_row(
                            summary.disease,
                            node,
                        )
                        for node in nodes
                    ]
                ),

                class_=(
                    "table table-sm align-middle mb-0 "
                    "disease-support__table"
                ),
            ),

            class_="table-responsive",
        ),

        class_=(
            "disease-support__node-section "
            "border rounded-3 p-3"
        ),
    )


def disease_node_selection_row(
    disease: str,
    node: DiseaseNodeSupport,
) -> ui.Tag:
    """Render one selectable node row."""

    checked = (
        node.status
        == DiseaseNodeStatus.READY
    )

    status_label = {
        DiseaseNodeStatus.READY:
            "Ready",

        DiseaseNodeStatus.INSUFFICIENT_DATA:
            "Insufficient",

        DiseaseNodeStatus.NO_DATA:
            "No data",

        DiseaseNodeStatus.UNSCOPABLE:
            "Unavailable",

        DiseaseNodeStatus.NOT_APPLICABLE:
            "Not applicable",
    }[node.status]

    badge_class = {
        DiseaseNodeStatus.READY:
            "text-bg-success",

        DiseaseNodeStatus.INSUFFICIENT_DATA:
            "text-bg-warning",

        DiseaseNodeStatus.NO_DATA:
            "text-bg-danger",

        DiseaseNodeStatus.UNSCOPABLE:
            "text-bg-danger",

        DiseaseNodeStatus.NOT_APPLICABLE:
            "text-bg-secondary",
    }[node.status]

    display_name = (
        node.node_name
        .replace("_", " ")
        .strip()
        .capitalize()
    )

    checkbox_id = disease_node_input_id(
        disease,
        node.node_name,
    )

    return ui.tags.tr(
        ui.tags.td(
            ui.input_checkbox(
                checkbox_id,
                None,
                value=checked,
            ),

            class_="disease-support__select-column",
        ),

        ui.tags.td(
            display_name,
            class_="fw-medium",
        ),

        ui.tags.td(
            f"{node.row_count:,}",
            class_="text-end font-monospace",
        ),

        ui.tags.td(
            ui.span(
                status_label,
                class_=(
                    "badge rounded-pill "
                    f"{badge_class}"
                ),
            ),

            class_="text-end",
        ),
    )

def disease_dataframe_modal(
    disease: str,
    node_dataframes: dict,
) -> ui.Tag:
    """Render loaded disease-specific DataFrames."""

    node_choices = {
        node_name: (
            f"{node_name.replace('_', ' ').title()} "
            f"({len(dataframe):,} rows)"
        )
        for node_name, dataframe
        in sorted(node_dataframes.items())
    }

    first_node = next(
        iter(node_choices),
        None,
    )

    return ui.modal(
        ui.div(
            ui.div(
                ui.h3(
                    disease,
                    class_="h5 fw-semibold mb-1",
                ),

                ui.p(
                    (
                        f"{len(node_dataframes):,} "
                        "loaded node types"
                    ),
                    class_="small text-secondary mb-3",
                ),
            ),

            ui.input_select(
                "disease_dataframe_node",
                "Node type",
                choices=node_choices,
                selected=first_node,
            ),

            ui.output_ui(
                "disease_dataframe_summary",
            ),

            ui.output_data_frame(
                "disease_dataframe_table",
            ),

            class_="disease-dataframe-viewer",
        ),

        title="Loaded disease data",
        easy_close=True,
        size="xl",
    )