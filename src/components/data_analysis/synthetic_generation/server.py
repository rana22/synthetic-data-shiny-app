# """Synthetic data generation server."""

# from __future__ import annotations

# from shiny import render, ui

# from .ui import synthetic_generation_ui


# def synthetic_generation_server(
#     input,
#     output,
#     session,
#     *,
#     analysis_state,
#     combined_analysis_state,
# ):
#     """Manage synthetic data generation."""

#     # --------------------------------------------------------------
#     # Generation section
#     #
#     # Only display after analysis has produced the per-node
#     # combined analysis required by SyntheticDataGenerator.
#     # --------------------------------------------------------------

#     @render.ui
#     def synthetic_generation_section():
#         combined_analysis = (
#             combined_analysis_state.get()
#         )

#         if not combined_analysis:
#             return None

#         supported_nodes = (
#             analysis_state
#             .supported_node_dataframes
#             or {}
#         )

#         if not supported_nodes:
#             return None

#         return synthetic_generation_ui()

#     # --------------------------------------------------------------
#     # Per-node row controls
#     # --------------------------------------------------------------

#     @render.ui
#     def synthetic_generation_node_inputs():
#         combined_analysis = (
#             combined_analysis_state.get()
#         )

#         supported_nodes = (
#             analysis_state
#             .supported_node_dataframes
#             or {}
#         )

#         if (
#             not combined_analysis
#             or not supported_nodes
#         ):
#             return None

#         rows = []

#         for node_name in sorted(
#             supported_nodes.keys()
#         ):
#             # Only show nodes that actually have completed
#             # analysis available for generation.
#             if node_name not in combined_analysis:
#                 continue

#             dataframe = supported_nodes[
#                 node_name
#             ]

#             source_rows = (
#                 len(dataframe)
#                 if dataframe is not None
#                 else 0
#             )

#             display_name = (
#                 node_name
#                 .replace("_", " ")
#                 .title()
#             )

#             rows.append(
#                 ui.div(
#                     ui.div(
#                         ui.strong(
#                             display_name
#                         ),

#                         ui.div(
#                             f"{source_rows:,} source rows",
#                             class_="small text-secondary",
#                         ),

#                         class_="col",
#                     ),

#                     ui.div(
#                         ui.input_numeric(
#                             f"synthetic_rows_{node_name}",
#                             None,
#                             value=50,
#                             min=1,
#                             step=1,
#                         ),

#                         class_="col-3",
#                     ),

#                     class_=(
#                         "row align-items-center "
#                         "border-bottom py-2"
#                     ),
#                 )
#             )

#         if not rows:
#             return None

#         return ui.div(
#             ui.div(
#                 ui.div(
#                     "Node",
#                     class_=(
#                         "col small fw-semibold "
#                         "text-secondary"
#                     ),
#                 ),

#                 ui.div(
#                     "Synthetic rows",
#                     class_=(
#                         "col-3 small fw-semibold "
#                         "text-secondary"
#                     ),
#                 ),

#                 class_=(
#                     "row align-items-center "
#                     "border-bottom pb-2"
#                 ),
#             ),

#             *rows,
#         )

"""Synthetic data generation server."""

from __future__ import annotations

import pandas as pd

from shiny import reactive, render, ui

from .ui import synthetic_generation_ui
from .generator import SyntheticDataGenerator

def _generation_order(
    node_tree: pd.DataFrame,
    supported_nodes: dict[str, pd.DataFrame],
) -> list[str]:
    """
    Return supported nodes in parent-to-child graph order.

    Context nodes participate in traversal but are not returned
    unless they are supported generation nodes.
    """

    supported = set(
        supported_nodes.keys()
    )

    if (
        node_tree is None
        or node_tree.empty
        or "parent" not in node_tree.columns
        or "child" not in node_tree.columns
    ):
        return sorted(supported)

    # ----------------------------------------------------------
    # Build graph
    # ----------------------------------------------------------

    graph: dict[str, list[str]] = {}
    indegree: dict[str, int] = {}

    for _, relationship in (
        node_tree[
            ["parent", "child"]
        ]
        .dropna()
        .drop_duplicates()
        .iterrows()
    ):
        parent = str(
            relationship["parent"]
        )

        child = str(
            relationship["child"]
        )

        graph.setdefault(
            parent,
            [],
        ).append(child)

        graph.setdefault(
            child,
            [],
        )

        indegree.setdefault(
            parent,
            0,
        )

        indegree[child] = (
            indegree.get(child, 0)
            + 1
        )

    # ----------------------------------------------------------
    # Topological traversal
    #
    # Traverse ALL graph nodes, including context nodes.
    # ----------------------------------------------------------

    queue = [
        node
        for node in graph
        if indegree.get(node, 0) == 0
    ]

    ordered_graph_nodes: list[str] = []

    while queue:
        node = queue.pop(0)

        ordered_graph_nodes.append(
            node
        )

        for child in graph.get(
            node,
            [],
        ):
            indegree[child] -= 1

            if indegree[child] == 0:
                queue.append(child)

    # ----------------------------------------------------------
    # Generation targets
    #
    # Keep graph ordering but only return supported nodes.
    # ----------------------------------------------------------

    generation_nodes = [
        node
        for node in ordered_graph_nodes
        if node in supported
    ]

    # A supported node may not have appeared in node_tree.
    # Append it so it is not silently skipped.
    for node in sorted(supported):
        if node not in generation_nodes:
            generation_nodes.append(
                node
            )

    return generation_nodes

def synthetic_generation_server(
    input,
    output,
    session,
    *,
    analysis_state,
    combined_results_state,
):
    """Manage synthetic data generation."""

    # Generated data for each supported node.
    generated_results_state = reactive.value({})

    # Invalid rows retained for validation/debugging.
    invalid_results_state = reactive.value({})

    # --------------------------------------------------------------
    # Generation section
    # --------------------------------------------------------------

    @render.ui
    def synthetic_generation_section():
        combined_analysis = (
            combined_results_state.get()
        )

        if not combined_analysis:
            return None

        supported_nodes = (
            analysis_state
            .supported_node_dataframes
            or {}
        )

        if not supported_nodes:
            return None

        return synthetic_generation_ui()

    # --------------------------------------------------------------
    # Per-node row controls
    # --------------------------------------------------------------

    @render.ui
    def synthetic_generation_node_inputs():
        combined_analysis = (
            combined_results_state.get()
        )

        supported_nodes = (
            analysis_state
            .supported_node_dataframes
            or {}
        )

        if (
            not combined_analysis
            or not supported_nodes
        ):
            return None

        rows = []

        for node_name in sorted(
            supported_nodes.keys()
        ):
            # Generate only supported nodes that have
            # completed analysis.
            if node_name not in combined_analysis:
                continue

            dataframe = supported_nodes[
                node_name
            ]

            source_rows = (
                len(dataframe)
                if dataframe is not None
                else 0
            )

            display_name = (
                node_name
                .replace("_", " ")
                .title()
            )

            rows.append(
                ui.div(
                    ui.div(
                        ui.strong(
                            display_name
                        ),

                        ui.div(
                            f"{source_rows:,} source rows",
                            class_="small text-secondary",
                        ),

                        class_="col",
                    ),

                    ui.div(
                        ui.input_numeric(
                            f"synthetic_rows_{node_name}",
                            None,
                            value=50,
                            min=1,
                            step=1,
                        ),

                        class_="col-3",
                    ),

                    class_=(
                        "row align-items-center "
                        "border-bottom py-2"
                    ),
                )
            )

        if not rows:
            return None

        return ui.div(
            ui.div(
                ui.div(
                    "Node",
                    class_=(
                        "col small fw-semibold "
                        "text-secondary"
                    ),
                ),

                ui.div(
                    "Synthetic rows",
                    class_=(
                        "col-3 small fw-semibold "
                        "text-secondary"
                    ),
                ),

                class_=(
                    "row align-items-center "
                    "border-bottom pb-2"
                ),
            ),

            *rows,
        )

    # --------------------------------------------------------------
    # Generate synthetic data
    # --------------------------------------------------------------

    @reactive.effect
    @reactive.event(
        input.generate_synthetic_data
    )
    def _generate_synthetic_data():
        combined_analysis = (
            combined_results_state.get()
        )

        supported_nodes = (
            analysis_state
            .supported_node_dataframes
            or {}
        )

        node_schemas = (
            analysis_state.node_schemas
            or {}
        )

        if not combined_analysis:
            ui.notification_show(
                "Analysis is not available.",
                type="warning",
            )
            return

        if not supported_nodes:
            ui.notification_show(
                "No supported nodes are available "
                "for generation.",
                type="warning",
            )
            return

        generated_data: dict[
            str,
            pd.DataFrame,
        ] = {}

        invalid_data: dict[
            str,
            pd.DataFrame,
        ] = {}

        # ----------------------------------------------------------
        # Generate supported nodes only
        # ----------------------------------------------------------
        node_tree = (
            analysis_state.node_tree
        )

        generation_order = _generation_order(
            node_tree,
            supported_nodes,
        )

        print(
            "Synthetic generation order:",
            generation_order,
            flush=True,
        )

        for node_name in generation_order:

            if node_name not in combined_analysis:
                continue

            real_df = supported_nodes.get(
                node_name
            )

            if (
                real_df is None
                or real_df.empty
            ):
                continue

            node_schema = node_schemas.get(
                node_name
            )

            if node_schema is None:
                continue

            node_analysis = (
                combined_analysis.get(
                    node_name
                )
            )

            if node_analysis is None:
                continue

            # ------------------------------------------------------
            # Requested number of rows
            # ------------------------------------------------------

            input_id = (
                f"synthetic_rows_{node_name}"
            )

            requested_rows = getattr(
                input,
                input_id,
            )()

            if requested_rows is None:
                requested_rows = 50

            requested_rows = int(
                requested_rows
            )

            if requested_rows <= 0:
                continue

            # ------------------------------------------------------
            # Generate
            # ------------------------------------------------------

            try:
                generator = (
                    SyntheticDataGenerator(
                        real_rows=real_df,
                        relationships=node_analysis,
                        schema=node_schema,

                        # Preserve original behavior:
                        # previously generated node data is
                        # available to later nodes.
                        synth_df=generated_data,
                    )
                )

                print(
                    f"\nGENERATED NODE: {node_name}",
                    flush=True,
                )

                print(
                    "requested rows:",
                    requested_rows,
                    flush=True,
                )


                generated_df = (
                    generator.generate(
                        requested_rows
                    )
                )


                print(
                    "generated shape:",
                    generated_df.shape,
                    flush=True,
                )

                print(
                    generated_df.head(),
                    flush=True,
                )

                # --------------------------------------------------
                # Validate complete generated rows
                # --------------------------------------------------

                valid_df, invalid_df = (
                    generator.validate_rows(
                        generated_df
                    )
                )

            except Exception as exc:
                ui.notification_show(
                    (
                        "Synthetic generation failed "
                        f"for '{node_name}': {exc}"
                    ),
                    type="error",
                )
                return

            generated_data[
                node_name
            ] = valid_df

            invalid_data[
                node_name
            ] = invalid_df

        # ----------------------------------------------------------
        # Store generation results
        # ----------------------------------------------------------

        generated_results_state.set(
            generated_data
        )

        invalid_results_state.set(
            invalid_data
        )

        # ----------------------------------------------------------
        # Status
        # ----------------------------------------------------------

        if not generated_data:
            ui.notification_show(
                "No synthetic data was generated.",
                type="warning",
            )
            return

        valid_rows = sum(
            len(dataframe)
            for dataframe
            in generated_data.values()
        )

        invalid_rows = sum(
            len(dataframe)
            for dataframe
            in invalid_data.values()
        )

        ui.notification_show(
            (
                f"Generated {valid_rows:,} valid "
                f"synthetic rows across "
                f"{len(generated_data):,} nodes. "
                f"{invalid_rows:,} invalid rows."
            ),
            type="message",
        )

    @render.ui
    def synthetic_generation_summary():
        generated_data = (
            generated_results_state.get()
        )

        if not generated_data:
            return None

        invalid_data = (
            invalid_results_state.get()
        )

        valid_rows = sum(
            len(df)
            for df in generated_data.values()
            if df is not None
        )

        invalid_rows = sum(
            len(df)
            for df in invalid_data.values()
            if df is not None
        )

        return ui.div(
            ui.strong(
                f"{len(generated_data):,} nodes generated"
            ),

            ui.span(
                " · ",
                class_="mx-2 text-secondary",
            ),

            ui.span(
                f"{valid_rows:,} valid rows"
            ),

            ui.span(
                " · ",
                class_="mx-2 text-secondary",
            ),

            ui.span(
                f"{invalid_rows:,} invalid rows"
            ),

            class_="small mt-4 mb-3",
        )

    @render.ui
    def synthetic_generation_results_controls():
        generated_data = (
            generated_results_state.get()
        )

        if not generated_data:
            return None

        choices = {
            node_name: (
                node_name
                .replace("_", " ")
                .title()
            )
            for node_name in generated_data
        }

        first_node = next(
            iter(generated_data),
            None,
        )

        return ui.input_select(
            "synthetic_generation_result_node",
            "View generated node",
            choices=choices,
            selected=first_node,
        )

    @render.data_frame
    def synthetic_generation_results():
        generated_data = (
            generated_results_state.get()
        )

        if not generated_data:
            return render.DataGrid(
                pd.DataFrame()
            )

        selected_node = (
            input.synthetic_generation_result_node()
        )

        if not selected_node:
            return render.DataGrid(
                pd.DataFrame()
            )

        dataframe = generated_data.get(
            selected_node
        )

        if (
            dataframe is None
            or dataframe.empty
        ):
            return render.DataGrid(
                pd.DataFrame()
            )

        return render.DataGrid(
            dataframe,
            width="100%",
            height="600px",
            filters=True,
        )