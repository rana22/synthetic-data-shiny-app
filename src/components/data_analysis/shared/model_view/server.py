# from shiny import reactive, render, ui
# import pandas as pd
# from src.services.schema_builder import (
#     build_relation_schemas,
# )
# from .ui import (
#     model_view_modal,
#     schema_view_modal
# )

# def model_view_server(
#     input,
#     output,
#     session,
#     *,
#     app_state,
#     analysis_state,
# ):
#     """Load and display data-model relationships."""
#     @reactive.effect
#     @reactive.event(input.view_data_model)
#     def _view_data_model():
#         workspace = app_state.active_workspace

#         if workspace is None:
#             return

#         metadata = workspace.metadata

#         if metadata is None:
#             return

#         node_url = metadata.node_model_url
#         property_url = metadata.property_model_url

#         if not node_url or not property_url:
#             ui.notification_show(
#                 "Configure the Node YAML URL and "
#                 "Properties YAML URL in Project Details.",
#                 type="warning",
#             )
#             return

#         node_list = list(
#             analysis_state.node_dataframes.keys()
#         )

#         try:
#             (
#                 node_schemas,
#                 relation_df,
#                 error,
#                 node_tree_df,
#                 join_df,
#             ) = build_relation_schemas(
#                 node_list_state=node_list,
#                 node_model_url=node_url,
#                 property_model_url=property_url,
#             )

#         except Exception as exc:
#             ui.notification_show(
#                 f"Could not load data model: {exc}",
#                 type="error",
#             )
#             return

#         if error:
#             ui.notification_show(
#                 error,
#                 type="error",
#             )
#             return

#         analysis_state.node_schemas = node_schemas
#         analysis_state.node_relationships = relation_df
#         analysis_state.node_tree = node_tree_df
#         analysis_state.join_paths = join_df

#         ui.modal_show(
#             model_view_modal()
#         )

#     @reactive.effect
#     @reactive.event(input.view_schema)
#     def _view_schema():
#         schemas = analysis_state.node_schemas

#         if not schemas:
#             ui.notification_show(
#                 "Load the data model first.",
#                 type="warning",
#             )
#             return

#         ui.modal_show(
#             schema_view_modal()
#         )
  

#     @render.ui
#     def data_model_summary():
#         tree = analysis_state.node_tree

#         if tree.empty:
#             return None

#         return ui.p(
#             f"{len(tree):,} node relationships found.",
#             class_="data-analysis-section-description",
#         )

#     @render.data_frame
#     def data_model_tree():
#         tree = analysis_state.node_tree

#         if tree is None or tree.empty:
#             return render.DataGrid(
#                 pd.DataFrame()
#             )


#         columns = [
#             column
#             for column in (
#                 "parent",
#                 "child",
#                 "type",
#                 "relation",
#                 "parent_prop",
#                 "child_prop",
#             )
#             if column in tree.columns
#         ]

#         return render.DataGrid(
#             tree[columns],
#             width="100%",
#             height="450px",
#             filters=True,
#         )

#     @render.ui
#     def schema_view_content():
#         schemas = analysis_state.node_schemas

#         if not schemas:
#             return ui.p(
#                 "No schema is available."
#             )

#         sections = []

#         for node_name, schema in schemas.items():
#             properties = schema.get(
#                 "properties",
#                 {}
#             )

#             sections.append(
#                 ui.div(
#                     ui.h3(node_name),

#                     ui.p(
#                         schema.get(
#                             "description",
#                             "",
#                         )
#                     ),

#                     ui.tags.ul(
#                         *[
#                             ui.tags.li(
#                                 ui.strong(prop_name),
#                                 (
#                                     f" — {prop.get('Type', '')}"
#                                     if prop.get("Type")
#                                     else ""
#                                 ),
#                             )
#                             for prop_name, prop
#                             in properties.items()
#                         ]
#                     ),

#                     class_="schema-node",
#                 )
#             )

#         return ui.div(
#             *sections,
#             class_="schema-view",
#         )

import pandas as pd

from shiny import reactive, render, ui

from src.services.schema_builder import (
    build_relation_schemas,
)
from src.services.schema import json_to_node_schema

from .ui import (
    model_view_modal,
    schema_view_modal,
)


def model_view_server(
    input,
    output,
    session,
    *,
    app_state,
    analysis_state,
):
    """Load and display schema and node relationships."""

    # ----------------------------------------------------------
    # Load model/schema when Analysis page initializes
    # ----------------------------------------------------------

    workspace = app_state.active_workspace

    if workspace is not None and workspace.metadata is not None:
        metadata = workspace.metadata

        node_url = (
            metadata.node_model_url or ""
        ).strip()

        property_url = (
            metadata.property_model_url or ""
        ).strip()

        if node_url and property_url:
            try:
                node_list = list(
                    analysis_state.node_dataframes.keys()
                )

                (
                    node_schemas,
                    relation_df,
                    error,
                    node_tree_df,
                    join_df,
                ) = build_relation_schemas(
                    node_list_state=node_list,
                    node_model_url=node_url,
                    property_model_url=property_url,
                )

                if not error:
                    # analysis_state.node_schemas = (
                    #     node_schemas
                    # )
                    analysis_state.node_schemas = {
                        node_name: json_to_node_schema(
                            schema_data
                        )
                        for node_name, schema_data
                        in node_schemas.items()
                    }
                    analysis_state.node_relationships = (
                        relation_df
                    )
                    analysis_state.node_tree = (
                        node_tree_df
                    )
                    analysis_state.join_paths = (
                        join_df
                    )

            except Exception as exc:
                print(
                    f"Could not load data model: {exc}"
                )

    # ----------------------------------------------------------
    # View schema
    # ----------------------------------------------------------

    @reactive.effect
    @reactive.event(input.view_schema)
    def _view_schema():
        workspace = app_state.active_workspace

        if (
            workspace is None
            or workspace.metadata is None
        ):
            return

        metadata = workspace.metadata

        if (
            not metadata.node_model_url
            or not metadata.property_model_url
        ):
            ui.notification_show(
                "Valid Node YAML and Properties YAML "
                "URLs must be provided in Project Details.",
                type="warning",
            )
            return

        if not analysis_state.node_schemas:
            ui.notification_show(
                "The data model could not be loaded. "
                "Verify the configured YAML URLs.",
                type="warning",
            )
            return

        ui.modal_show(
            schema_view_modal()
        )

    # ----------------------------------------------------------
    # View node relationships
    # ----------------------------------------------------------

    @reactive.effect
    @reactive.event(input.view_data_model)
    def _view_data_model():
        workspace = app_state.active_workspace

        if (
            workspace is None
            or workspace.metadata is None
        ):
            return

        metadata = workspace.metadata

        if (
            not metadata.node_model_url
            or not metadata.property_model_url
        ):
            ui.notification_show(
                "Valid Node YAML and Properties YAML "
                "URLs must be provided in Project Details.",
                type="warning",
            )
            return

        if (
            analysis_state.node_tree is None
            or analysis_state.node_tree.empty
        ):
            ui.notification_show(
                "The data model could not be loaded. "
                "Verify the configured YAML URLs.",
                type="warning",
            )
            return

        ui.modal_show(
            model_view_modal()
        )

    # ----------------------------------------------------------
    # Schema content
    # ----------------------------------------------------------

    @render.ui
    def schema_view_content():
        schemas = analysis_state.node_schemas

        if not schemas:
            return ui.p(
                "No schema is available."
            )

        sections = []

        for node_name, schema in schemas.items():
            sections.append(
                ui.div(
                    ui.h3(
                        schema.name
                    ),

                    ui.p(
                        schema.description
                    ) if schema.description else None,

                    ui.tags.ul(
                        *[
                            ui.tags.li(
                                ui.strong(
                                    property_name
                                ),
                                (
                                    f" — {property_schema.type}"
                                    if property_schema.type
                                    else ""
                                ),
                            )
                            for property_name, property_schema
                            in schema.properties.items()
                        ]
                    ),

                    class_="schema-node",
                )
            )

        return ui.div(
            *sections,
            class_="schema-view",
        )

    # ----------------------------------------------------------
    # Node relationship table
    # ----------------------------------------------------------

    @render.data_frame
    def data_model_tree():
        tree = analysis_state.node_tree

        if tree is None or tree.empty:
            return render.DataGrid(
                pd.DataFrame()
            )

        return render.DataGrid(
            tree,
            width="100%",
            height="500px",
            filters=True,
        )