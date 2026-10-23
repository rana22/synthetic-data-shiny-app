from __future__ import annotations

import pandas as pd

from shiny import reactive, render, ui

from src.connectors.neo4j import (
    Neo4jClient,
)

from src.disease import (
    DiseaseSupportSummary,
    build_disease_support,
    get_disease_generation_config,
)

from .ui import (
    disease_node_input_id,
    disease_select_button_id,
    disease_support_modal,
    disease_support_results,
    disease_dataframe_modal
)


def disease_source_server(
    input,
    output,
    session,
    *,
    app_state,
):
    """Manage disease-specific source-data support."""
    analysis_state = app_state.analysis
    # ------------------------------------------------------------------
    # Component state
    # ------------------------------------------------------------------

    support_summaries = reactive.value(
        None
    )

    load_status = reactive.value(
        ""
    )

    show_data_viewer = reactive.value(False)

    selected_disease_state = reactive.value(
        app_state.selected_disease_term
    )

    selected_nodes_state = reactive.value(
        app_state.selected_disease_nodes
    )

    registered_disease_handlers: set[str] = set()

    disease_node_dataframes: dict[str, pd.DataFrame] = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_enabled_neo4j_source():
        """Return the active project's enabled Neo4j source."""

        workspace = (
            app_state.active_workspace
        )

        if (
            workspace is None
            or workspace.metadata is None
        ):
            return None

        return next(
            (
                source
                for source
                in workspace.metadata.data_sources
                if (
                    source.source_type.casefold()
                    == "neo4j"
                    and source.enabled
                )
            ),
            None,
        )

    def get_summary(
        disease: str,
    ) -> DiseaseSupportSummary | None:
        """Return the support summary for a disease."""

        summaries = (
            support_summaries.get()
        )

        if not summaries:
            return None

        disease_key = (
            disease.strip().casefold()
        )

        return next(
            (
                summary
                for summary in summaries
                if (
                    summary.disease
                    .strip()
                    .casefold()
                    == disease_key
                )
            ),
            None,
        )

    def get_selected_nodes(
        summary: DiseaseSupportSummary,
    ) -> tuple[str, ...]:
        """Return checked nodes for one disease."""

        selected: list[str] = []

        nodes = (
            summary.generation_nodes
            + summary.context_nodes
        )

        for node in nodes:
            input_id = (
                disease_node_input_id(
                    summary.disease,
                    node.node_name,
                )
            )

            try:
                checked = bool(
                    input[input_id]()
                )
            except Exception:
                checked = False

            if checked:
                selected.append(
                    node.node_name
                )

        return tuple(
            selected
        )
    
    def register_disease_selection_handler(
        summary: DiseaseSupportSummary,
    ) -> None:
        """Register the Select for analysis event for one disease."""

        button_id = disease_select_button_id(
            summary.disease
        )

        if button_id in registered_disease_handlers:
            return

        registered_disease_handlers.add(
            button_id
        )

        @reactive.effect
        @reactive.event(
            input[button_id]
        )
        def _select_disease(
            summary=summary,
        ):
            selected_nodes = get_selected_nodes(
                summary
            )

            if not selected_nodes:
                ui.notification_show(
                    "Select at least one node.",
                    type="warning",
                )
                return

            app_state.selected_disease_term = (
                summary.disease
            )

            app_state.selected_disease_nodes = (
                selected_nodes
            )

            selected_disease_state.set(
                summary.disease
            )

            selected_nodes_state.set(
                selected_nodes
            )

            # Loaded data belongs to the previous selection.
            app_state.node_dataframes = None
            show_data_viewer.set(False)

            load_status.set("")

            ui.notification_show(
                (
                    f"Selected {summary.disease} "
                    f"with {len(selected_nodes)} nodes."
                ),
                type="message",
            )

    # ------------------------------------------------------------------
    # Open Disease Support
    # ------------------------------------------------------------------

    @reactive.effect
    @reactive.event(
        input.view_disease_support
    )
    def _view_disease_support():
        """Retrieve and evaluate disease support from Neo4j."""

        workspace = (
            app_state.active_workspace
        )

        if workspace is None:
            ui.notification_show(
                "No project is currently loaded.",
                type="warning",
            )
            return

        metadata = (
            workspace.metadata
        )

        if metadata is None:
            ui.notification_show(
                "Project metadata is unavailable.",
                type="error",
            )
            return

        source = (
            get_enabled_neo4j_source()
        )

        if source is None:
            ui.notification_show(
                "No enabled Neo4j data source is configured.",
                type="warning",
            )
            return

        # --------------------------------------------------------------
        # Keep the existing working development credential behavior.
        # --------------------------------------------------------------

        password = "password"

        # --------------------------------------------------------------
        # Disease configuration
        # --------------------------------------------------------------

        scope_config = (
            get_disease_generation_config(
                "ICDC"
            )
        )

        if scope_config is None:
            ui.notification_show(
                "Disease generation configuration "
                "was not found for ICDC.",
                type="error",
            )
            return

        # --------------------------------------------------------------
        # Disease/node counts
        # --------------------------------------------------------------

        counts_query = """
            MATCH (d)
            WHERE d.disease_term IS NOT NULL
              AND trim(toString(d.disease_term)) <> ''

            WITH
                d,
                trim(
                    toString(d.disease_term)
                ) AS disease

            OPTIONAL MATCH
                (d)-[*1..4]-(related)

            WITH
                disease,
                collect(DISTINCT d)
                + collect(DISTINCT related)
                AS nodes

            UNWIND nodes AS node

            WITH
                disease,
                node,
                labels(node) AS node_labels

            UNWIND node_labels AS node_type

            RETURN
                disease,
                node_type,
                count(DISTINCT node) AS count

            ORDER BY
                disease,
                node_type
        """

        # --------------------------------------------------------------
        # Validated disease vocabulary
        # --------------------------------------------------------------

        vocabulary_query = """
            MATCH (n:diagnosis)
            WHERE n.disease_term IS NOT NULL
              AND trim(
                    toString(n.disease_term)
                  ) <> ''

            RETURN DISTINCT
                trim(
                    toString(n.disease_term)
                ) AS disease

            ORDER BY disease
        """

        client = None

        try:
            client = Neo4jClient(
                uri=source.uri,
                username=(
                    source.username
                    or ""
                ),
                password=password,
                database=source.database,
            )

            disease_node_counts = (
                client.run_query(
                    counts_query
                )
            )

            vocabulary_result = (
                client.run_query(
                    vocabulary_query
                )
            )

        except Exception as exc:
            support_summaries.set(
                None
            )

            ui.notification_show(
                (
                    "Could not retrieve disease "
                    f"support data: {exc}"
                ),
                type="error",
            )
            return

        finally:
            if client is not None:
                client.close()

        # --------------------------------------------------------------
        # Supported vocabulary
        # --------------------------------------------------------------

        if vocabulary_result.empty:
            supported_terms: tuple[
                str,
                ...,
            ] = ()

        else:
            supported_terms = tuple(
                str(value).strip()
                for value
                in vocabulary_result[
                    "disease"
                ]
                .dropna()
                .tolist()
                if str(value).strip()
            )

        # --------------------------------------------------------------
        # Apply disease support rules
        # --------------------------------------------------------------

        try:
            summaries = (
                build_disease_support(
                    disease_node_counts=(
                        disease_node_counts
                    ),
                    supported_terms=(
                        supported_terms
                    ),
                    scope_config=(
                        scope_config
                    ),
                )
            )

        except ValueError as exc:
            support_summaries.set(
                None
            )

            ui.notification_show(
                (
                    "Could not evaluate disease "
                    f"support: {exc}"
                ),
                type="error",
            )
            return

        support_summaries.set(
            summaries
        )

        for summary in summaries:
            register_disease_selection_handler(
                summary
            )

        load_status.set(
            ""
        )

        ui.modal_show(
            disease_support_modal(
                source.name
            )
        )

    # ------------------------------------------------------------------
    # Disease Support UI
    # ------------------------------------------------------------------

    @render.ui
    def disease_support_content():
        """Render disease support with search filtering."""

        summaries = (
            support_summaries.get()
        )

        if summaries is None:
            return ui.div(
                "Loading disease support...",
                class_="disease-support-loading",
            )

        if not summaries:
            return ui.div(
                "No disease support information is available.",
                class_="disease-support-empty",
            )

        search_text = (
            input.disease_support_search()
            or ""
        ).strip().casefold()

        if search_text:
            filtered_summaries = tuple(
                summary
                for summary in summaries
                if (
                    search_text
                    in summary.disease.casefold()
                )
            )
        else:
            filtered_summaries = (
                summaries
            )

        if not filtered_summaries:
            return ui.div(
                ui.p(
                    "No disease terms match your search."
                ),

                ui.p(
                    (
                        'Search: "'
                        f'{input.disease_support_search()}'
                        '"'
                    ),
                    class_="disease-support-search-query",
                ),

                class_="disease-support-empty",
            )

        return disease_support_results(
            summaries,
            visible_summaries=(
                filtered_summaries
            ),
        )

    # ------------------------------------------------------------------
    # Load selected disease data
    # ------------------------------------------------------------------

    @reactive.effect
    @reactive.event(
        input.load_selected_disease_data
    )
    def _load_selected_disease_data():
        """Load selected disease nodes into application state."""

        # --------------------------------------------------------------
        # Selection was already captured by Select for analysis.
        # --------------------------------------------------------------

        disease = (
            app_state.selected_disease_term
            or ""
        ).strip()

        selected_nodes = tuple(
            app_state.selected_disease_nodes
            or ()
        )

        if not disease:
            ui.notification_show(
                "Select a disease for analysis first.",
                type="warning",
            )
            return

        if not selected_nodes:
            ui.notification_show(
                "Select at least one node for analysis.",
                type="warning",
            )
            return

        source = get_enabled_neo4j_source()

        if source is None:
            ui.notification_show(
                "No enabled Neo4j data source is configured.",
                type="warning",
            )
            return

        # Keep the same credential mechanism as the currently
        # working Disease Support query.
        password = "password"

        # --------------------------------------------------------------
        # IMPORTANT:
        #
        # This deliberately follows the same graph traversal used by
        # the support/count query.
        #
        # We retrieve all nodes connected to the selected disease and
        # filter to the selected labels in Cypher.
        # --------------------------------------------------------------

        query = """
            MATCH (d)
            WHERE d.disease_term IS NOT NULL
            AND toLower(
                    trim(
                        toString(d.disease_term)
                    )
                )
                =
                toLower(
                    trim($disease)
                )

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

            RETURN
                node_type,
                properties(node) AS row

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

            result = client.run_query(
                query,
                {
                    "disease": disease,
                    "selected_nodes": list(
                        selected_nodes
                    ),
                },
            )

        except Exception as exc:
            load_status.set(
                f"Could not load disease data: {exc}"
            )

            ui.notification_show(
                f"Could not load disease data: {exc}",
                type="error",
            )
            return

        finally:
            if client is not None:
                client.close()

        # --------------------------------------------------------------
        # Validate result
        # --------------------------------------------------------------

        if result.empty:
            load_status.set(
                "No rows were returned for the selected disease and nodes."
            )

            ui.notification_show(
                "No rows were returned for the selected disease and nodes.",
                type="warning",
            )
            return

        required_columns = {
            "node_type",
            "row",
        }

        if not required_columns.issubset(
            result.columns
        ):
            load_status.set(
                "Neo4j did not return node_type and row."
            )

            ui.notification_show(
                "Neo4j returned an unexpected result.",
                type="error",
            )
            return

        # --------------------------------------------------------------
        # Convert:
        #
        # node_type | row
        # ----------+--------------------
        # case      | {...}
        # case      | {...}
        # sample    | {...}
        #
        # into:
        #
        # {
        #     "case": DataFrame,
        #     "sample": DataFrame,
        # }
        # --------------------------------------------------------------

        node_dataframes: dict[
            str,
            pd.DataFrame,
        ] = {}

        for node_name, group in result.groupby(
            "node_type",
            sort=True,
        ):
            rows = [
                value
                for value in group["row"]
                if isinstance(value, dict)
            ]

            if not rows:
                continue

            node_dataframes[
                str(node_name)
            ] = pd.DataFrame(
                rows
            )

            disease_node_dataframes[
                str(node_name)
            ] = pd.DataFrame(rows)

        if not node_dataframes:
            load_status.set(
                "Neo4j returned nodes, but no node properties could be loaded."
            )

            ui.notification_show(
                "No usable node rows were returned.",
                type="warning",
            )
            return

        # --------------------------------------------------------------
        # IMPORTANT:
        #
        # Store only nodes that actually loaded.
        # --------------------------------------------------------------

        loaded_nodes = tuple(
            node_name
            for node_name in selected_nodes
            if node_name in node_dataframes
        )

        app_state.selected_disease_term = (
            disease
        )

        app_state.selected_disease_nodes = (
            loaded_nodes
        )

        app_state.node_dataframes = (
            node_dataframes
        )
        show_data_viewer.set(True)

        # --------------------------------------------------------------
        # Status
        # --------------------------------------------------------------

        total_rows = sum(
            len(frame)
            for frame in node_dataframes.values()
        )

        missing_nodes = tuple(
            node_name
            for node_name in selected_nodes
            if node_name not in node_dataframes
        )

        message = (
            f"Loaded {len(node_dataframes)} node types "
            f"and {total_rows:,} rows for {disease}."
        )

        if missing_nodes:
            message += (
                " No rows were returned for: "
                + ", ".join(missing_nodes)
                + "."
            )

        load_status.set(
            message
        )

        analysis_state.selected_disease_term = (
            disease
        )

        supported_node_dataframes = {
            node_name: dataframe
            for node_name, dataframe
            in disease_node_dataframes.items()
            if node_name in selected_nodes
        }

        analysis_state.supported_node_dataframes = (
            supported_node_dataframes
        )

        analysis_state.disease_node_dataframes = (
            disease_node_dataframes     
        )

        ui.notification_show(
            (
                f"Loaded {len(node_dataframes)} "
                f"node types for {disease}."
            ),
            type="message",
        )


    # @reactive.effect
    # @reactive.event(
    #     input.load_selected_disease_data
    # )
    # def _load_selected_disease_data():
    #     """Load selected disease/node records into application state."""

    #     disease = (
    #         app_state.selected_disease_term
    #         or ""
    #     ).strip()

    #     selected_nodes = (
    #         app_state.selected_disease_nodes
    #     )

    #     if not disease:
    #         ui.notification_show(
    #             "Select a disease for analysis first.",
    #             type="warning",
    #         )
    #         return

    #     if not selected_nodes:
    #         ui.notification_show(
    #             "Select at least one node for analysis.",
    #             type="warning",
    #         )
    #         return

    #     source = (
    #         get_enabled_neo4j_source()
    #     )

    #     if source is None:
    #         ui.notification_show(
    #             "No enabled Neo4j data source is configured.",
    #             type="warning",
    #         )
    #         return

    #     # --------------------------------------------------------------
    #     # Keep the same credential behavior as the existing working
    #     # Disease Support query.
    #     # --------------------------------------------------------------

    #     password = "password"

    #     node_dataframes: dict[
    #         str,
    #         pd.DataFrame,
    #     ] = {}

    #     client = None

    #     try:
    #         client = Neo4jClient(
    #             uri=source.uri,
    #             username=(
    #                 source.username
    #                 or ""
    #             ),
    #             password=password,
    #             database=source.database,
    #         )

    #         for node_name in selected_nodes:
    #             # ------------------------------------------------------
    #             # The label comes from Neo4j's own support-query result.
    #             # Escape backticks before using it as a Cypher label.
    #             # ------------------------------------------------------

    #             label = (
    #                 node_name.replace(
    #                     "`",
    #                     "``",
    #                 )
    #             )

    #             # ------------------------------------------------------
    #             # Start from nodes carrying the selected disease and
    #             # traverse the same bounded graph used by the support
    #             # count query.
    #             #
    #             # This also allows manually-selected context nodes such
    #             # as study/publication to be loaded even when those nodes
    #             # do not themselves carry disease_term.
    #             # ------------------------------------------------------

    #             query = f"""
    #                 MATCH (d)
    #                 WHERE d.disease_term IS NOT NULL
    #                   AND toLower(
    #                         trim(
    #                             toString(
    #                                 d.disease_term
    #                             )
    #                         )
    #                       )
    #                       =
    #                       toLower(
    #                         trim($disease)
    #                       )

    #                 MATCH (d)-[*0..4]-(n:`{label}`)

    #                 WITH DISTINCT n

    #                 RETURN
    #                     properties(n) AS row
    #             """

    #             result = (
    #                 client.run_query(
    #                     query,
    #                     {
    #                         "disease": disease,
    #                     },
    #                 )
    #             )

    #             if result.empty:
    #                 continue

    #             if (
    #                 "row"
    #                 not in result.columns
    #             ):
    #                 continue

    #             rows = [
    #                 value
    #                 for value
    #                 in result["row"]
    #                 if isinstance(
    #                     value,
    #                     dict,
    #                 )
    #             ]

    #             if not rows:
    #                 continue

    #             node_dataframes[
    #                 node_name
    #             ] = pd.DataFrame(
    #                 rows
    #             )

    #     except Exception as exc:
    #         load_status.set(
    #             (
    #                 "Could not load disease "
    #                 f"data: {exc}"
    #             )
    #         )

    #         ui.notification_show(
    #             (
    #                 "Could not load disease "
    #                 f"data: {exc}"
    #             ),
    #             type="error",
    #         )
    #         return

    #     finally:
    #         if client is not None:
    #             client.close()

    #     if not node_dataframes:
    #         load_status.set(
    #             (
    #                 "No rows were loaded for "
    #                 "the selected nodes."
    #             )
    #         )

    #         ui.notification_show(
    #             "No rows were loaded for the selected nodes.",
    #             type="warning",
    #         )
    #         return

    #     # --------------------------------------------------------------
    #     # Save application state
    #     # --------------------------------------------------------------

    #     app_state.selected_disease_term = (
    #         disease
    #     )

    #     app_state.selected_disease_nodes = (
    #         selected_nodes
    #     )

    #     app_state.node_dataframes = (
    #         node_dataframes
    #     )

    #     total_rows = sum(
    #         len(frame)
    #         for frame
    #         in node_dataframes.values()
    #     )

    #     load_status.set(
    #         (
    #             f"Loaded {len(node_dataframes)} "
    #             f"node types and {total_rows:,} "
    #             f"rows for {disease}."
    #         )
    #     )

    #     ui.notification_show(
    #         (
    #             f"Loaded disease data for "
    #             f"{disease}."
    #         ),
    #         type="message",
    #     )

    # ------------------------------------------------------------------
    # Load status
    # ------------------------------------------------------------------

    @render.ui
    def disease_data_load_status():
        """Render disease-data loading status."""

        message = (
            load_status.get()
        )

        if not message:
            return None

        return ui.div(
            message,
            class_="small text-secondary mt-3",
        )

    # ------------------------------------------------------------------
    # Use loaded disease data for analysis
    # ------------------------------------------------------------------

    @reactive.effect
    @reactive.event(
        input.use_disease_data_for_analysis
    )
    async def _use_disease_data_for_analysis():
        """Navigate loaded disease data to the analysis workflow."""

        # --------------------------------------------------------------
        # Selected disease
        # --------------------------------------------------------------

        disease = (
            app_state.selected_disease_term
            or ""
        ).strip()

        if not disease:
            ui.notification_show(
                "Select a disease for analysis first.",
                type="warning",
            )
            return

        # --------------------------------------------------------------
        # Selected nodes
        # --------------------------------------------------------------

        selected_nodes = (
            app_state.selected_disease_nodes
        )

        if not selected_nodes:
            ui.notification_show(
                "Select at least one node for analysis.",
                type="warning",
            )
            return

        # --------------------------------------------------------------
        # Loaded DataFrames
        # --------------------------------------------------------------

        node_dataframes = (
            app_state.node_dataframes
        )

        if not node_dataframes:
            ui.notification_show(
                "Load the selected disease data first.",
                type="warning",
            )
            return

        # --------------------------------------------------------------
        # Verify selected nodes were actually loaded.
        # --------------------------------------------------------------

        missing_nodes = tuple(
            node
            for node in selected_nodes
            if node not in node_dataframes
        )

        if missing_nodes:
            ui.notification_show(
                (
                    "Data was not loaded for the following "
                    "selected nodes: "
                    + ", ".join(missing_nodes)
                ),
                type="warning",
            )
            return

        # --------------------------------------------------------------
        # Remove empty DataFrames defensively.
        # --------------------------------------------------------------

        empty_nodes = tuple(
            node
            for node in selected_nodes
            if (
                node in node_dataframes
                and node_dataframes[node].empty
            )
        )

        if empty_nodes:
            ui.notification_show(
                (
                    "The following selected nodes contain no rows: "
                    + ", ".join(empty_nodes)
                ),
                type="warning",
            )
            return

        # --------------------------------------------------------------
        # Everything is ready.
        #
        # The analysis page will read:
        #
        # app_state.selected_disease_term
        # app_state.selected_disease_nodes
        # app_state.node_dataframes
        # --------------------------------------------------------------

        await session.send_custom_message(
            "navigate",
            {
                "url": "/project/analysis/inter-node/",
            },
        )

    @render.ui
    def selected_disease_summary():
        """Display the disease/nodes currently selected for analysis."""

        disease = (
            selected_disease_state.get()
            or ""
        )

        nodes = (
            selected_nodes_state.get()
        )

        if not disease or not nodes:
            return ui.div(
                "No disease has been selected.",
                class_="text-secondary small",
            )

        return ui.div(
            ui.div(
                ui.strong(
                    disease,
                    class_="d-block",
                ),

                ui.span(
                    (
                        f"{len(nodes)} "
                        f"{'node' if len(nodes) == 1 else 'nodes'} selected"
                    ),
                    class_="small text-secondary",
                ),
            ),

            ui.div(
                *[
                    ui.span(
                        node
                        .replace("_", " ")
                        .title(),

                        class_=(
                            "badge text-bg-light "
                            "border me-1 mb-1"
                        ),
                    )
                    for node in nodes
                ],

                class_="mt-2",
            ),
        )

    @reactive.effect
    @reactive.event(
        input.view_selected_disease_data
    )
    def _view_selected_disease_data():
        """Open the loaded disease DataFrame viewer."""

        node_dataframes = (
            app_state.node_dataframes
        )

        if not node_dataframes:
            ui.notification_show(
                "Load the selected disease data first.",
                type="warning",
            )
            return

        show_data_viewer.set(
            not show_data_viewer.get()
        )

    @render.data_frame
    def disease_dataframe_table():
        """Render the currently selected loaded node DataFrame."""

        node_name = (
            input.disease_dataframe_node()
            or ""
        ).strip()

        if not node_name:
            return render.DataGrid(
                pd.DataFrame()
            )

        node_dataframes = (
            app_state.node_dataframes
            or {}
        )

        dataframe = node_dataframes.get(
            node_name
        )

        if dataframe is None:
            return render.DataGrid(
                pd.DataFrame()
            )

        return render.DataGrid(
            dataframe,
            filters=True,
            selection_mode="rows",
            height="500px",
        )

    @render.ui
    def disease_dataframe_summary():
        """Show dimensions for the selected node DataFrame."""

        node_name = (
            input.disease_dataframe_node()
            or ""
        ).strip()

        node_dataframes = (
            app_state.node_dataframes
            or {}
        )

        dataframe = node_dataframes.get(
            node_name
        )

        if dataframe is None:
            return None

        return ui.div(
            ui.span(
                f"{len(dataframe):,} rows",
                class_="badge text-bg-light border",
            ),

            ui.span(
                f"{len(dataframe.columns):,} columns",
                class_="badge text-bg-light border",
            ),

            class_="d-flex gap-2 mb-3",
        )

    @render.ui
    def selected_disease_data_viewer():
        """Render the loaded disease data below the action buttons."""

        if not show_data_viewer.get():
            return None

        disease = (
            app_state.selected_disease_term
            or ""
        ).strip()

        node_dataframes = (
            app_state.node_dataframes
            or {}
        )

        if not disease or not node_dataframes:
            return None

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

        return ui.div(
            ui.div(
                ui.div(
                    ui.h5(
                        f"Loaded data — {disease}",
                        class_="mb-1",
                    ),

                    ui.p(
                        (
                            f"{len(node_dataframes):,} "
                            "node types loaded"
                        ),
                        class_="small text-secondary mb-0",
                    ),
                ),

                class_="mb-3",
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

            class_=(
                "disease-support__data-viewer "
                "border rounded-3 p-3 mt-3"
            ),
        )

    @render.ui
    def disease_dataframe_summary():
        """Show dimensions of the selected node DataFrame."""

        if not show_data_viewer.get():
            return None

        node_name = (
            input.disease_dataframe_node()
            or ""
        ).strip()

        if not node_name:
            return None

        node_dataframes = (
            app_state.node_dataframes
            or {}
        )

        dataframe = node_dataframes.get(
            node_name
        )

        if dataframe is None:
            return None

        return ui.div(
            ui.span(
                f"{len(dataframe):,} rows",
                class_="badge text-bg-light border",
            ),

            ui.span(
                f"{len(dataframe.columns):,} columns",
                class_="badge text-bg-light border",
            ),

            class_="d-flex gap-2 mb-3",
        )

    @render.data_frame
    def disease_dataframe_table():
        """Render the selected loaded node DataFrame."""

        if not show_data_viewer.get():
            return render.DataGrid(
                pd.DataFrame()
            )

        node_name = (
            input.disease_dataframe_node()
            or ""
        ).strip()

        if not node_name:
            return render.DataGrid(
                pd.DataFrame()
            )

        node_dataframes = (
            app_state.node_dataframes
            or {}
        )

        dataframe = node_dataframes.get(
            node_name
        )

        if dataframe is None:
            return render.DataGrid(
                pd.DataFrame()
            )

        return render.DataGrid(
            dataframe,
            filters=True,
            selection_mode="none",
            height="500px",
        )