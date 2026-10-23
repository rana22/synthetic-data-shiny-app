"""Inter-node analysis server."""

from __future__ import annotations

import pandas as pd

from shiny import render, ui, reactive

from src.services.schema_builder import (
    build_relation_schemas,
)
from .weights import (
    inter_node_weights_server,
)
from src.components.data_analysis.shared.feature_weights import feature_weights_server
from src.services.schema import json_to_node_schema
from .analysis import (
    run_cross_analysis,
    compute_cross_node_analysis,
    combined_analysis_to_dataframe,
)
from ..synthetic_generation import (
    synthetic_generation_server,
)    

def _node_summary_dataframe(
    node_dataframes: dict[str, pd.DataFrame],
    *,
    role: str | None = None,
) -> pd.DataFrame:
    """Build a node/row-count summary."""

    rows = []

    for node_name, dataframe in sorted(
        node_dataframes.items()
    ):
        row = {
            "Node type": (
                node_name
                .replace("_", " ")
                .title()
            ),
            "Rows": (
                len(dataframe)
                if dataframe is not None
                else 0
            ),
        }

        if role is not None:
            row["Role"] = role

        rows.append(row)

    return pd.DataFrame(rows)


def inter_node_server(
    input,
    output,
    session,
    *,
    app_state,
):
    """Manage the inter-node analysis page."""

    analysis_state = app_state.analysis
    results_state = reactive.value(pd.DataFrame())
    combined_results_state = reactive.value({})
    def update_feature_weight(
            *,
            feature_name: str,
            node_name: str | None,
            weight_name: str,
            value: float,
        ):
            """Update a feature weight in AnalysisState."""
    
            if feature_name == "cross_node_fuzzy":
                analysis_state.feature_weights[
                    feature_name
                ][weight_name] = value
    
                return
    
            if node_name is None:
                return
    
            analysis_state.feature_weights[
                feature_name
            ][node_name][weight_name] = value

    feature_weights_server(
        input,
        output,
        session,
        analysis_state=analysis_state,
        update_weight=update_feature_weight,
    )

    # ----------------------------------------------------------
    # Synthetic data generation
    # ----------------------------------------------------------
    
    synthetic_generation_server(
        input,
        output,
        session,
        analysis_state=analysis_state,
        combined_results_state=combined_results_state,
    )

    # --------------------------------------------------------------
    # Project metadata
    # --------------------------------------------------------------

    workspace = app_state.active_workspace

    if (
        workspace is not None
        and workspace.metadata is not None
    ):
        metadata = workspace.metadata

        node_url = (
            metadata.node_model_url or ""
        ).strip()

        property_url = (
            metadata.property_model_url or ""
        ).strip()

        # All nodes available for the selected disease.
        node_list = list(
            analysis_state
            .disease_node_dataframes
            .keys()
        )

        # ----------------------------------------------------------
        # Build schema / graph information
        # ----------------------------------------------------------

        if (
            node_url
            and property_url
            and node_list
        ):
            (
                node_schemas,
                node_relationships,
                status,
                node_tree,
                join_paths,
            ) = build_relation_schemas(
                node_list_state=node_list,
                node_model_url=node_url,
                property_model_url=property_url,
            )

            analysis_state.node_schemas = {
                node_name: json_to_node_schema(schema_data)
                for node_name, schema_data in node_schemas.items()
            }

            analysis_state.node_relationships = (
                node_relationships
            )

            analysis_state.node_tree = (
                node_tree
            )

            analysis_state.join_paths = (
                join_paths
            )

    # --------------------------------------------------------------
    # Analysis migration: original Gradio sequence
    # --------------------------------------------------------------

    @reactive.effect
    @reactive.event(input.run_inter_node_analysis_btn)
    def _run_inter_node_analysis():
        node_data_state = (
            analysis_state.disease_node_dataframes
            or {}
        )
        selected_nodes = list(
            (analysis_state.supported_node_dataframes or {}).keys()
        )
        node_relationships = analysis_state.node_relationships
        schema_state = analysis_state.node_schemas or {}

        if len(selected_nodes) < 2:
            ui.notification_show(
                "At least two supported nodes are required for analysis.",
                type="warning",
            )
            return

        if not node_data_state:
            ui.notification_show(
                "Disease data is not available.",
                type="warning",
            )
            return

        if (
            node_relationships is None
            or not isinstance(node_relationships, pd.DataFrame)
            or node_relationships.empty
        ):
            ui.notification_show(
                "Node relationship data is not available.",
                type="warning",
            )
            return

        try:
            print(
                "\n========== INTER-NODE ANALYSIS ==========",
                flush=True,
            )

            print(
                "feature_weights:",
                analysis_state.feature_weights,
                flush=True,
            )

            print(
                "cross_node_fuzzy:",
                analysis_state.feature_weights.get(
                    "cross_node_fuzzy"
                ),
                flush=True,
            )

            print(
                "Starting cross-node analysis...",
                flush=True,
            )
            # Stage 1: original run_cross_analysis().
            cross_results = run_cross_analysis(
                weights_state=analysis_state.feature_weights,
                node_data_state=node_data_state,
                node_relationships=node_relationships,
                selected_nodes=selected_nodes,
            )

            # Stage 2: original compute_cross_node_analysis().
            # node_tree is the relationship/edge DataFrame produced by
            # build_relation_schemas and corresponds to edges_out.
            full_analysis = compute_cross_node_analysis(
                weights_state=analysis_state.feature_weights,
                schema_state=schema_state,
                node_data_state=node_data_state,
                cross_node_analysis_dfs=cross_results,
                edges_out=analysis_state.node_tree,
            )

            display_results = combined_analysis_to_dataframe(
                full_analysis
            )

        except Exception as exc:
            import traceback

            print(
                "\n========== ANALYSIS ERROR ==========",
                flush=True,
            )

            print(
                "Error:",
                repr(exc),
                flush=True,
            )

            traceback.print_exc()

            print(
                "====================================\n",
                flush=True,
            )

            ui.notification_show(
                f"Inter-node analysis failed: {exc}",
                type="error",
            )
            return

        # Raw cross-node output from the first Gradio stage.
        analysis_state.inter_node_results = cross_results

        # Preserve the original full_analysis dict for downstream generation.
        combined_results_state.set(full_analysis)
        results_state.set(display_results)

        if display_results.empty:
            ui.notification_show(
                "No combined node analysis was produced.",
                type="warning",
            )
            return

        ui.notification_show(
            f"Analysis completed: {len(display_results):,} relationships found.",
            type="message",
        )

    @render.ui
    def inter_node_results_summary():
        results = results_state.get()
        if results.empty:
            return None

        full_analysis = combined_results_state.get()
        populated_nodes = sum(
            1
            for frame in full_analysis.values()
            if isinstance(frame, pd.DataFrame) and not frame.empty
        )

        return ui.div(
            ui.strong(
                f"{len(results):,} relationships across "
                f"{populated_nodes:,} analyzed nodes"
            ),
            class_="inter-node-results-summary mb-3",
        )

    @render.data_frame
    def inter_node_results():
        results = results_state.get()

        if results.empty:
            return render.DataGrid(pd.DataFrame())

        return render.DataGrid(
            results,
            width="100%",
            height="600px",
            filters=True,
        )

    inter_node_weights_server(
        input,
        output,
        session,
        analysis_state=analysis_state,
    )

    @reactive.effect
    @reactive.event(
        input.view_inter_node_schema
    )
    def _view_inter_node_schema():
        schemas = (
            analysis_state.node_schemas
            or {}
        )

        if not schemas:
            ui.notification_show(
                "Schema is not available.",
                type="warning",
            )
            return

        ui.modal_show(
            ui.modal(
                ui.output_ui(
                    "inter_node_schema_content"
                ),
                title="Schema",
                size="xl",
                easy_close=True,
            )
        )

    @reactive.effect
    @reactive.event(
        input.view_inter_node_tree
    )
    def _view_inter_node_tree():
        node_tree = analysis_state.node_tree

        if (
            node_tree is None
            or node_tree.empty
        ):
            ui.notification_show(
                "Node tree is not available.",
                type="warning",
            )
            return

        ui.modal_show(
            ui.modal(
                ui.output_ui(
                    "inter_node_tree_view"
                ),
                title="Node Tree",
                size="xl",
                easy_close=True,
            )
        )

    # --------------------------------------------------------------
    # Dataset overview
    # --------------------------------------------------------------

    @render.ui
    def inter_node_dataset_overview():
        disease = (
            analysis_state.selected_disease_term
            or "Not selected"
        )

        supported_data = (
            analysis_state.supported_node_dataframes
            or {}
        )

        disease_data = (
            analysis_state.disease_node_dataframes
            or {}
        )

        supported_rows = sum(
            len(frame)
            for frame in supported_data.values()
            if frame is not None
        )

        disease_rows = sum(
            len(frame)
            for frame in disease_data.values()
            if frame is not None
        )

        return ui.div(
            ui.div(
                ui.span(
                    "Disease",
                    class_="small text-secondary",
                ),
                ui.strong(
                    disease,
                    class_="d-block",
                ),
                class_="col",
            ),

            ui.div(
                ui.span(
                    "Supported nodes",
                    class_="small text-secondary",
                ),
                ui.strong(
                    f"{len(supported_data):,}",
                    class_="d-block",
                ),
                class_="col",
            ),

            ui.div(
                ui.span(
                    "Supported rows",
                    class_="small text-secondary",
                ),
                ui.strong(
                    f"{supported_rows:,}",
                    class_="d-block",
                ),
                class_="col",
            ),

            ui.div(
                ui.span(
                    "Disease nodes",
                    class_="small text-secondary",
                ),
                ui.strong(
                    f"{len(disease_data):,}",
                    class_="d-block",
                ),
                class_="col",
            ),

            ui.div(
                ui.span(
                    "Disease rows",
                    class_="small text-secondary",
                ),
                ui.strong(
                    f"{disease_rows:,}",
                    class_="d-block",
                ),
                class_="col",
            ),

            class_=(
                "row g-3 border rounded-3 "
                "p-3 mb-4"
            ),
        )

    # --------------------------------------------------------------
    # Supported node data
    # --------------------------------------------------------------

    @render.data_frame
    def inter_node_supported_nodes():
        node_dataframes = (
            analysis_state.supported_node_dataframes
            or {}
        )

        summary = _node_summary_dataframe(
            node_dataframes,
            role="Supported",
        )

        return render.DataGrid(
            summary,
            width="100%",
            filters=False,
        )

    @render.ui
    def inter_node_schema_summary():
        schemas = (
            analysis_state.node_schemas
            or {}
        )

        if not schemas:
            return ui.div(
                "Schema is not available.",
                class_="small text-secondary mt-3",
            )

        property_count = sum(
            len(
                getattr(
                    schema,
                    "properties",
                    {},
                )
            )
            if not isinstance(schema, dict)
            else len(
                schema.get(
                    "properties",
                    {}
                )
            )
            for schema in schemas.values()
        )

        return ui.div(
            ui.span(
                f"{len(schemas):,} nodes",
            ),

            ui.span(
                " · ",
                class_="mx-2 text-secondary",
            ),

            ui.span(
                f"{property_count:,} properties",
            ),

            class_="small mt-3",
        )

    # --------------------------------------------------------------
    # Full disease dataset summary
    # --------------------------------------------------------------

    @render.data_frame
    def inter_node_disease_nodes():
        node_dataframes = (
            analysis_state.disease_node_dataframes
            or {}
        )

        summary = _node_summary_dataframe(
            node_dataframes
        )

        return render.DataGrid(
            summary,
            width="100%",
            filters=False,
        )

    # --------------------------------------------------------------
    # Schema
    # --------------------------------------------------------------

    @render.ui
    def inter_node_schema_summary():
        return None

    @render.data_frame
    def inter_node_schema():
        return render.DataGrid(
            pd.DataFrame()
        )

    # --------------------------------------------------------------
    # Graph
    # --------------------------------------------------------------

    @render.ui
    def inter_node_graph():
        return ui.div(
            "Schema graph will appear here.",
            class_="text-secondary",
        )


    @render.ui
    def inter_node_schema_content():
        schemas = (
            analysis_state.node_schemas
            or {}
        )

        sections = []

        for node_name, schema in sorted(
            schemas.items()
        ):
            if isinstance(schema, dict):
                properties = schema.get(
                    "properties",
                    {}
                )

                description = schema.get(
                    "description",
                    "",
                )

            else:
                properties = (
                    schema.properties
                )

                description = (
                    schema.description
                )

            property_rows = []

            for property_name, prop in properties.items():

                if isinstance(prop, dict):
                    property_type = (
                        prop.get("Type")
                        or prop.get("type")
                        or ""
                    )
                else:
                    property_type = (
                        prop.type or ""
                    )

                property_rows.append(
                    ui.tags.li(
                        ui.strong(
                            property_name
                        ),
                        (
                            f" — {property_type}"
                            if property_type
                            else ""
                        ),
                    )
                )

            sections.append(
                ui.div(
                    ui.h4(
                        node_name
                        .replace("_", " ")
                        .title()
                    ),

                    (
                        ui.p(
                            description,
                            class_="text-secondary",
                        )
                        if description
                        else None
                    ),

                    ui.tags.ul(
                        *property_rows
                    ),

                    class_="mb-4",
                )
            )

        return ui.div(
            *sections
        )

    @render.ui
    def inter_node_tree_summary():
        node_tree = analysis_state.node_tree

        if (
            node_tree is None
            or not isinstance(node_tree, pd.DataFrame)
            or node_tree.empty
        ):
            return ui.div(
                "Node relationship data is not available.",
                class_="small text-secondary mt-3",
            )

        node_names = set()

        if "parent" in node_tree.columns:
            node_names.update(
                node_tree["parent"]
                .dropna()
                .astype(str)
                .tolist()
            )

        if "child" in node_tree.columns:
            node_names.update(
                node_tree["child"]
                .dropna()
                .astype(str)
                .tolist()
            )

        return ui.div(
            ui.span(
                f"{len(node_names):,} nodes"
            ),

            ui.span(
                " · ",
                class_="mx-2 text-secondary",
            ),

            ui.span(
                f"{len(node_tree):,} relationships"
            ),

            class_="small mt-3",
        )

    @render.ui
    def inter_node_tree_view():
        node_tree = analysis_state.node_tree

        if (
            node_tree is None
            or node_tree.empty
        ):
            return ui.p(
                "Node tree is not available.",
                class_="text-secondary",
            )

        relationships = (
            node_tree[
                ["parent", "child"]
            ]
            .dropna()
            .drop_duplicates()
        )

        rows = []

        for _, relationship in relationships.iterrows():
            parent = str(
                relationship["parent"]
            )

            child = str(
                relationship["child"]
            )

            rows.append(
                ui.div(
                    ui.span(
                        parent
                        .replace("_", " ")
                        .title(),
                        class_=(
                            "badge text-bg-light "
                            "border px-3 py-2"
                        ),
                    ),

                    ui.span(
                        "→",
                        class_="text-secondary px-2",
                    ),

                    ui.span(
                        child
                        .replace("_", " ")
                        .title(),
                        class_=(
                            "badge text-bg-light "
                            "border px-3 py-2"
                        ),
                    ),

                    class_=(
                        "d-flex align-items-center "
                        "mb-2"
                    ),
                )
            )

        return ui.div(
            *rows,
            class_="inter-node-tree-view",
        )

    # --------------------------------------------------------------
    # Cross-node feature weights
    # --------------------------------------------------------------

    @render.ui
    def inter_node_feature_weights():
        weights = (
            analysis_state
            .feature_weights
            .get(
                "cross_node_fuzzy",
                {},
            )
        )

        if not weights:
            return ui.div(
                "Cross-node feature weights are not available.",
                class_="small text-secondary",
            )

        return ui.div(
            *[
                ui.div(
                    ui.div(
                        ui.span(
                            weight_name
                            .replace("_", " ")
                            .title(),
                            class_="small fw-semibold",
                        ),

                        ui.span(
                            f"{float(value):.2f}",
                            class_="small text-secondary",
                        ),

                        class_=(
                            "d-flex justify-content-between "
                            "align-items-center mb-1"
                        ),
                    ),

                    ui.input_slider(
                        f"inter_node_weight_{weight_name}",
                        None,
                        min=0.0,
                        max=1.0,
                        value=float(value),
                        step=0.01,
                    ),

                    class_="mb-3",
                )
                for weight_name, value
                in weights.items()
            ],
            class_="inter-node-feature-weights",
        )

    