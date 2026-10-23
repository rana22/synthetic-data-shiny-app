"""Project data-source server behavior."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from uuid import uuid4

import pandas as pd
from shiny import reactive, render, ui

from src.connectors.neo4j import Neo4jClient
from src.disease import get_disease_generation_config, build_disease_support
from src.workspace.loader import load_project_metadata
from src.workspace.metadata import save_project_metadata
from src.workspace.models import DataSourceConfig

from .ui import (
    data_source_row,
    neo4j_configuration_modal,
    disease_source_data_modal,
)


def _upsert_data_source(
    sources: tuple[DataSourceConfig, ...],
    source: DataSourceConfig,
) -> tuple[DataSourceConfig, ...]:
    """Add a data source or replace an existing source with the same ID."""

    updated = [
        existing
        for existing in sources
        if existing.id != source.id
    ]
    updated.append(source)
    return tuple(updated)


def data_sources_server(
    input,
    output,
    session,
    *,
    app_state,
):
    """Manage project reference data and prepare disease data for analysis."""

    analysis_state = app_state.analysis

    refresh_version = reactive.value(0)
    connection_status = reactive.value("")
    connection_status_type = reactive.value("")
    disease_terms = reactive.value(None)
    disease_support = reactive.value(())
    runtime_password = reactive.value(None)

    def refresh() -> None:
        refresh_version.set(refresh_version.get() + 1)

    def get_metadata():
        refresh_version.get()
        workspace = app_state.active_workspace
        if workspace is None:
            return None
        return load_project_metadata(workspace.root)

    def get_enabled_neo4j_source():
        workspace = app_state.active_workspace
        if workspace is None or workspace.metadata is None:
            return None

        return next(
            (
                source
                for source in workspace.metadata.data_sources
                if source.source_type.casefold() == "neo4j"
                and source.enabled
            ),
            None,
        )

    def read_connection_form() -> dict[str, str | None]:
        return {
            "name": (input.data_source_name() or "").strip(),
            "uri": (input.neo4j_uri() or "").strip(),
            "database": (input.neo4j_database() or "").strip() or None,
            "username": (input.neo4j_username() or "").strip(),
            "password": input.neo4j_password() or "",
        }

    def validate_form(values: dict[str, str | None]) -> str | None:
        if not values["name"]:
            return "Enter a connection name."
        if not values["uri"]:
            return "Enter the Neo4j URI."
        if not values["username"]:
            return "Enter the Neo4j username."
        if not values["password"]:
            return "Enter the Neo4j password."
        return None

    @render.ui
    def data_sources_summary():
        metadata = get_metadata()
        if metadata is None:
            return None

        if not metadata.data_sources:
            return ui.div(
                ui.p(
                    "No reference data sources have been configured "
                    "for this project."
                ),
                class_="data-sources-empty",
            )

        return ui.div(
            *[
                data_source_row(source)
                for source in metadata.data_sources
            ],
            class_="data-sources-list",
        )

    @reactive.effect
    @reactive.event(input.configure_data_source)
    def _configure():
        if app_state.active_workspace is None:
            return

        connection_status.set("")
        connection_status_type.set("")
        ui.modal_show(neo4j_configuration_modal())

    @reactive.effect
    @reactive.event(input.test_neo4j_connection)
    def _test_connection():
        values = read_connection_form()
        error = validate_form(values)

        if error:
            connection_status.set(error)
            connection_status_type.set("error")
            return

        client = None
        try:
            client = Neo4jClient(
                uri=str(values["uri"]),
                username=str(values["username"]),
                password=str(values["password"]),
                database=(
                    str(values["database"])
                    if values["database"]
                    else None
                ),
            )
            client.verify_connectivity()
        except Exception as exc:
            runtime_password.set(None)
            connection_status.set(f"Connection failed: {exc}")
            connection_status_type.set("error")
            return
        finally:
            if client is not None:
                client.close()

        runtime_password.set(str(values["password"]))
        connection_status.set("Connection successful.")
        connection_status_type.set("success")

    @reactive.effect
    @reactive.event(input.save_neo4j_configuration)
    def _save_configuration():
        workspace = app_state.active_workspace
        if workspace is None or workspace.metadata is None:
            ui.notification_show(
                "Project metadata is unavailable.",
                type="error",
            )
            return

        values = read_connection_form()
        error = validate_form(values)
        if error:
            connection_status.set(error)
            connection_status_type.set("error")
            return

        source = DataSourceConfig(
            id=str(uuid4()),
            name=str(values["name"]),
            source_type="neo4j",
            uri=str(values["uri"]),
            database=(
                str(values["database"])
                if values["database"]
                else None
            ),
            username=str(values["username"]),
            password_encrypted=None,
            enabled=True,
        )

        updated_metadata = replace(
            workspace.metadata,
            data_sources=_upsert_data_source(
                workspace.metadata.data_sources,
                source,
            ),
            updated_at=datetime.now().astimezone().isoformat(),
        )
        updated_workspace = replace(
            workspace,
            metadata=updated_metadata,
        )

        try:
            save_project_metadata(updated_workspace)
        except (OSError, ValueError) as exc:
            connection_status.set(
                f"Could not save data source: {exc}"
            )
            connection_status_type.set("error")
            return

        app_state.active_workspace = updated_workspace
        runtime_password.set(str(values["password"]))
        refresh()
        ui.modal_remove()
        ui.notification_show(
            "Neo4j configuration saved.",
            type="message",
        )

    @render.ui
    def neo4j_connection_status():
        message = connection_status.get()
        if not message:
            return None

        return ui.div(
            message,
            class_=(
                "data-source-connection-status "
                f"is-{connection_status_type.get()}"
            ),
        )

    @render.ui
    def neo4j_disease_terms():
        """Render available diseases and their node-count summaries."""

        data = disease_terms.get()

        if data is None:
            return ui.div(
                "Loading source data...",
                class_="data-source-preview-loading",
            )

        if data.empty:
            return ui.div(
                "No disease data was returned.",
                class_="data-source-preview-empty",
            )

        required_columns = {"disease", "node_type", "count"}
        if not required_columns.issubset(data.columns):
            return ui.div(
                "The Neo4j query did not return the expected "
                "disease, node_type, and count columns.",
                class_="data-source-preview-empty",
            )

        disease_names = [
            str(disease)
            for disease in sorted(
                data["disease"].dropna().unique()
            )
        ]

        disease_selector = ui.input_radio_buttons(
            "selected_source_disease",
            "Disease for analysis",
            choices={disease: disease for disease in disease_names},
            selected=(
                analysis_state.selected_disease_term
                if analysis_state.selected_disease_term in disease_names
                else None
            ),
        )

        panels = []

        for disease, disease_data in data.groupby("disease", sort=True):
            disease_data = disease_data.sort_values("node_type")
            node_type_count = len(disease_data)
            total_nodes = int(disease_data["count"].sum())

            rows = []
            for _, row in disease_data.iterrows():
                node_type = str(row["node_type"])
                display_name = (
                    node_type.replace("_", " ").strip().capitalize()
                )

                rows.append(
                    ui.div(
                        ui.span(
                            display_name,
                            class_="disease-node-name",
                        ),
                        ui.span(
                            f'{int(row["count"]):,}',
                            class_="disease-node-count",
                        ),
                        class_="disease-node-row",
                    )
                )

            panels.append(
                ui.accordion_panel(
                    str(disease),
                    ui.div(
                        ui.span(
                            f"{node_type_count} node types",
                            class_="disease-summary-item",
                        ),
                        ui.span(
                            "·",
                            class_="disease-summary-separator",
                        ),
                        ui.span(
                            f"{total_nodes:,} related nodes",
                            class_="disease-summary-item",
                        ),
                        class_="disease-accordion-summary",
                    ),
                    ui.div(
                        ui.span("Node type"),
                        ui.span("Records"),
                        class_=(
                            "disease-node-row "
                            "disease-node-table-header"
                        ),
                    ),
                    ui.div(
                        *rows,
                        class_="disease-node-list",
                    ),
                )
            )

        return ui.div(
            disease_selector,
            ui.accordion(
                *panels,
                id="disease_source_accordion",
                multiple=False,
                open=False,
                class_="disease-source-accordion",
            ),
            class_="disease-source-browser",
        )

    @reactive.effect
    @reactive.event(input.view_neo4j_source_data)
    def _view_neo4j_source_data():
        """Load available disease terms and node-count summaries."""

        source = get_enabled_neo4j_source()
        if source is None:
            ui.notification_show(
                "No enabled Neo4j data source is configured.",
                type="warning",
            )
            return

        password = runtime_password.get() or "password"
        if not password:
            ui.notification_show(
                "The Neo4j password is not available in this session.",
                type="warning",
            )
            return

        disease_count_query = """
            MATCH (d)
            WHERE d.disease_term IS NOT NULL
            AND trim(toString(d.disease_term)) <> ''

            WITH d, trim(toString(d.disease_term)) AS disease
            OPTIONAL MATCH (d)-[*1..4]-(related)

            WITH
                disease,
                collect(DISTINCT d) + collect(DISTINCT related) AS nodes

            UNWIND nodes AS node
            WITH disease, node, labels(node) AS node_labels
            UNWIND node_labels AS node_type

            RETURN
                disease,
                node_type,
                count(DISTINCT node) AS count

            ORDER BY disease, node_type
        """

        vocabulary_query = """
            MATCH (n:diagnosis)
            WHERE n.disease_term IS NOT NULL
            AND trim(toString(n.disease_term)) <> ''

            RETURN DISTINCT
                trim(toString(n.disease_term)) AS disease

            ORDER BY disease
        """

        client = None
        try:
            client = Neo4jClient(
                uri=source.uri,
                username=source.username or "",
                password=password,
                database=source.database,
            )

            result = client.run_query(disease_count_query)
            vocabulary_result = client.run_query(vocabulary_query)

            supported_terms = (
                tuple(
                    str(value).strip()
                    for value in vocabulary_result["disease"]
                    .dropna()
                    .tolist()
                    if str(value).strip()
                )
                if not vocabulary_result.empty
                else ()
            )

            scope_config = get_disease_generation_config("ICDC")
            if scope_config is None:
                ui.notification_show(
                    "Disease generation configuration was not found for ICDC.",
                    type="error",
                )
                return

            support_summaries = build_disease_support(
                disease_node_counts=result,
                supported_terms=supported_terms,
                scope_config=scope_config,
            )

        except Exception as exc:
            disease_terms.set(None)
            disease_support.set(())
            ui.notification_show(
                f"Could not retrieve disease data: {exc}",
                type="error",
            )
            return
        finally:
            if client is not None:
                client.close()

        disease_terms.set(result)
        disease_support.set(tuple(support_summaries))
        ui.modal_show(disease_source_data_modal(source.name))

    # @reactive.effect
    # @reactive.event(input.selected_source_disease)
    # def _select_disease():
    #     """Store the selected disease and clear stale analysis data."""

    #     selected_disease = (
    #         input.selected_source_disease() or ""
    #     ).strip()

    #     if not selected_disease:
    #         return

    #     if analysis_state.selected_disease_term == selected_disease:
    #         return

    #     analysis_state.selected_disease_term = selected_disease
    #     analysis_state.disease_node_dataframes = {}
    #     analysis_state.supported_node_dataframes = {}
    #     analysis_state.node_schemas = {}
    #     analysis_state.node_relationships = pd.DataFrame()
    #     analysis_state.node_tree = pd.DataFrame()
    #     analysis_state.join_paths = pd.DataFrame()
    #     analysis_state.intra_node_results = {}
    #     analysis_state.inter_node_results = pd.DataFrame()

    # @reactive.effect
    # @reactive.event(input.analyze_selected_disease)
    # async def _analyze_selected_disease():
    #     """Load selected-disease data and open inter-node analysis."""

    #     selected_disease = (
    #         input.selected_source_disease()
    #         or analysis_state.selected_disease_term
    #         or ""
    #     ).strip()

    #     if not selected_disease:
    #         ui.notification_show(
    #             "Select a disease for analysis.",
    #             type="warning",
    #         )
    #         return

    #     analysis_state.selected_disease_term = selected_disease

    #     source = get_enabled_neo4j_source()
    #     if source is None:
    #         ui.notification_show(
    #             "No enabled Neo4j data source is configured.",
    #             type="warning",
    #         )
    #         return

    #     selected_summary = next(
    #         (
    #             summary
    #             for summary in disease_support.get()
    #             if summary.disease == selected_disease
    #         ),
    #         None,
    #     )

    #     if selected_summary is None:
    #         ui.notification_show(
    #             "Disease support information is not available.",
    #             type="warning",
    #         )
    #         return

    #     password = runtime_password.get() or "password"
    #     if not password:
    #         ui.notification_show(
    #             "The Neo4j password is not available in this session.",
    #             type="warning",
    #         )
    #         return

    #     disease_literal = selected_disease.replace("'", "\\'")

    #     disease_query = f"""
    #         MATCH (d)
    #         WHERE d.disease_term IS NOT NULL
    #         AND trim(toString(d.disease_term)) = '{disease_literal}'

    #         OPTIONAL MATCH (d)-[*1..4]-(related)

    #         WITH
    #             collect(DISTINCT d) + collect(DISTINCT related) AS nodes

    #         UNWIND nodes AS node
    #         WITH DISTINCT node, labels(node) AS node_labels
    #         WHERE size(node_labels) > 0

    #         RETURN
    #             node_labels[0] AS node_type,
    #             properties(node) AS properties

    #         ORDER BY node_type
    #     """

    #     client = None
    #     try:
    #         client = Neo4jClient(
    #             uri=source.uri,
    #             username=source.username or "",
    #             password=password,
    #             database=source.database,
    #         )
    #         disease_records = client.run_query(disease_query)
    #     except Exception as exc:
    #         ui.notification_show(
    #             f"Could not load disease data: {exc}",
    #             type="error",
    #         )
    #         return
    #     finally:
    #         if client is not None:
    #             client.close()

    #     disease_node_dataframes: dict[str, pd.DataFrame] = {}

    #     if not disease_records.empty:
    #         for node_name, node_rows in disease_records.groupby(
    #             "node_type",
    #             sort=True,
    #         ):
    #             records = [
    #                 properties
    #                 for properties in node_rows["properties"].tolist()
    #                 if isinstance(properties, dict)
    #             ]
    #             disease_node_dataframes[str(node_name)] = pd.DataFrame(
    #                 records
    #             )

    #     supported_node_names = {
    #         node.node_name
    #         for node in selected_summary.generation_nodes
    #     }

    #     analysis_state.disease_node_dataframes = disease_node_dataframes
    #     analysis_state.supported_node_dataframes = {
    #         node_name: dataframe
    #         for node_name, dataframe in disease_node_dataframes.items()
    #         if node_name in supported_node_names
    #     }

    #     # Compatibility for existing consumers during migration.
    #     app_state.selected_disease_term = selected_disease
    #     app_state.selected_disease_nodes = tuple(
    #         sorted(supported_node_names)
    #     )

    #     ui.modal_remove()

    #     await session.send_custom_message(
    #         "navigate",
    #         {"url": "/project/analysis/inter-node/"},
    #     )

    @reactive.effect
    @reactive.event(input.analyze_selected_disease)
    async def _analyze_selected_disease():
        print("_analyze_selected_disease")
        print("_analyze_selected_disease")
        print("_analyze_selected_disease")
        print("_analyze_selected_disease")
        """Load the full selected-disease dataset and open inter-node analysis."""

        selected_disease = (
            input.selected_source_disease()
            or analysis_state.selected_disease_term
            or ""
        ).strip()

        if not selected_disease:
            ui.notification_show(
                "Select a disease for analysis.",
                type="warning",
            )
            return

        analysis_state.selected_disease_term = (
            selected_disease
        )

        source = get_enabled_neo4j_source()

        if source is None:
            ui.notification_show(
                "No enabled Neo4j data source is configured.",
                type="warning",
            )
            return

        # --------------------------------------------------------------
        # Disease support
        # --------------------------------------------------------------

        selected_summary = next(
            (
                summary
                for summary in disease_support.get()
                if summary.disease == selected_disease
            ),
            None,
        )

        if selected_summary is None:
            ui.notification_show(
                "Disease support information is not available.",
                type="warning",
            )
            return

        # --------------------------------------------------------------
        # Supported nodes
        #
        # These are the Ready / generation nodes.
        # --------------------------------------------------------------

        supported_node_names = {
            node.node_name
            for node in selected_summary.generation_nodes
        }

        # --------------------------------------------------------------
        # Full disease node set
        #
        # Use the SAME disease/node table that was already displayed
        # to the user. This includes Ready and Not Applicable nodes.
        # --------------------------------------------------------------

        disease_table = disease_terms.get()

        if (
            disease_table is None
            or disease_table.empty
        ):
            ui.notification_show(
                "Disease node information is not available.",
                type="warning",
            )
            return

        disease_rows = disease_table[
            disease_table["disease"]
            .astype(str)
            .str.strip()
            .eq(selected_disease)
        ]

        disease_node_names = {
            str(node_name)
            for node_name
            in disease_rows["node_type"]
            .dropna()
            .tolist()
        }

        if not disease_node_names:
            ui.notification_show(
                "No nodes are available for the selected disease.",
                type="warning",
            )
            return

        # Supported nodes must always be part of the full disease set.
        disease_node_names.update(
            supported_node_names
        )

        # --------------------------------------------------------------
        # Neo4j connection
        # --------------------------------------------------------------

        password = (
            runtime_password.get()
            or "password"
        )

        if not password:
            ui.notification_show(
                "The Neo4j password is not available in this session.",
                type="warning",
            )
            return

        # --------------------------------------------------------------
        # Load all nodes belonging to the disease graph.
        #
        # Important:
        # disease_node_names comes from the full table displayed in
        # Nodes for analysis, not just the supported generation nodes.
        # --------------------------------------------------------------

        disease_query = """
            MATCH (d)
            WHERE d.disease_term IS NOT NULL
            AND trim(toString(d.disease_term)) = $disease

            OPTIONAL MATCH (d)-[*1..4]-(related)

            WITH
                collect(DISTINCT d)
                + collect(DISTINCT related)
                AS nodes

            UNWIND nodes AS node

            WITH DISTINCT
                node,
                labels(node) AS node_labels

            UNWIND node_labels AS node_type

            WHERE node_type IN $disease_nodes

            RETURN
                node_type,
                properties(node) AS properties

            ORDER BY node_type
        """

        disease_query = """
            MATCH (d)
            WHERE d.disease_term IS NOT NULL
            AND trim(toString(d.disease_term)) = $disease

            MATCH path = (d)-[*0..4]-(node)

            WITH DISTINCT
                node,
                labels(node) AS node_labels

            UNWIND node_labels AS node_type

            WHERE node_type IN $disease_nodes

            RETURN
                node_type,
                properties(node) AS properties

            ORDER BY node_type
        """

        client = None

        try:
            client = Neo4jClient(
                uri=source.uri,
                username=source.username or "",
                password=password,
                database=source.database,
            )

            disease_records = client.run_query(
                disease_query,
                {
                    "disease": selected_disease,
                    "disease_nodes": sorted(
                        disease_node_names
                    ),
                },
            )

        except Exception as exc:
            ui.notification_show(
                f"Could not load disease data: {exc}",
                type="error",
            )
            return

        finally:
            if client is not None:
                client.close()

        # --------------------------------------------------------------
        # Convert Neo4j rows into node DataFrames
        # --------------------------------------------------------------

        disease_node_dataframes: dict[
            str,
            pd.DataFrame,
        ] = {}

        if not disease_records.empty:
            for (
                node_name,
                node_rows,
            ) in disease_records.groupby(
                "node_type",
                sort=True,
            ):
                records = [
                    properties
                    for properties
                    in node_rows[
                        "properties"
                    ].tolist()
                    if isinstance(
                        properties,
                        dict,
                    )
                ]

                disease_node_dataframes[
                    str(node_name)
                ] = pd.DataFrame(
                    records
                )

        # --------------------------------------------------------------
        # AnalysisState
        #
        # disease_node_dataframes
        #     = ALL disease-associated nodes
        #
        # supported_node_dataframes
        #     = Ready / generation subset
        # --------------------------------------------------------------

        analysis_state.disease_node_dataframes = (
            disease_node_dataframes
        )

        analysis_state.supported_node_dataframes = {
            node_name: dataframe
            for node_name, dataframe
            in disease_node_dataframes.items()
            if node_name in supported_node_names
        }

        # --------------------------------------------------------------
        # Compatibility for existing consumers during migration
        # --------------------------------------------------------------

        app_state.selected_disease_term = (
            selected_disease
        )

        app_state.selected_disease_nodes = tuple(
            sorted(
                supported_node_names
            )
        )

        print(
            "REQUESTED DISEASE NODES:",
            sorted(disease_node_names),
            flush=True,
        )

        print(
            "RETURNED NODE TYPES:",
            sorted(
                disease_records["node_type"]
                .dropna()
                .unique()
                .tolist()
            )
            if not disease_records.empty
            else [],
            flush=True,
        )

        # --------------------------------------------------------------
        # Navigate
        # --------------------------------------------------------------

        ui.modal_remove()

        await session.send_custom_message(
            "navigate",
            {
                "url": (
                    "/project/analysis/inter-node/"
                )
            },
        )
