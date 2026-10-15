# """Feature weights server."""

# from shiny import reactive, render, ui

# from ...features.weights import (
#     node_category_weights,
#     node_substring_weights,
#     node_cluster_weights,
#     cross_node_fuzzy,
# )

# def _slider_id(
#     feature_name: str,
#     node_name: str,
#     weight_name: str,
# ) -> str:
#     """Create a stable Shiny input ID for a feature weight."""

#     return (
#         f"weight__"
#         f"{feature_name}__"
#         f"{node_name}__"
#         f"{weight_name}"
#     )


# def _weight_slider(
#     feature_name: str,
#     node_name: str,
#     weight_name: str,
#     value: float,
# ) -> ui.Tag:
#     """Render one feature-weight slider."""

#     return ui.input_slider(
#         _slider_id(
#             feature_name,
#             node_name,
#             weight_name,
#         ),
#         weight_name
#         .replace("_", " ")
#         .title(),
#         min=0,
#         max=1,
#         value=value,
#         step=0.01,
#     )

# def _weight_list(
#     weights: dict[str, float],
# ) -> ui.Tag:
#     """Render one set of feature weights."""

#     return ui.tags.ul(
#         *[
#             ui.tags.li(
#                 f"{name.replace('_', ' ').title()}: "
#                 f"{value:.3f}"
#             )
#             for name, value in weights.items()
#         ],
#         class_="feature-weight-list",
#     )


# def _node_weights(
#     node_weights: dict[str, dict[str, float]],
# ) -> ui.Tag:
#     """Render weights grouped by node."""

#     return ui.div(
#         *[
#             ui.div(
#                 ui.h5(
#                     node_name
#                     .replace("_", " ")
#                     .title()
#                 ),
#                 _weight_list(weights),
#                 class_="feature-weight-node",
#             )
#             for node_name, weights
#             in node_weights.items()
#         ]
#     )


# # def feature_weights_server(
# #     input,
# #     output,
# #     session,
# #     *,
# #     analysis_state,
# # ):
# #     """Display configured analysis feature weights."""

# #     @render.ui
# #     def feature_weights_content():
# #         return ui.div(
# #             # Categorical
# #             ui.div(
# #                 ui.h4("Categorical"),
# #                 ui.p(
# #                     "Weights used for categorical "
# #                     "property relationship analysis.",
# #                     class_="data-analysis-section-description",
# #                 ),
# #                 _node_weights(
# #                     node_category_weights
# #                 ),
# #                 class_="feature-weight-group",
# #             ),

# #             # Substring
# #             ui.div(
# #                 ui.h4("Substring"),
# #                 ui.p(
# #                     "Weights used for substring "
# #                     "property relationship analysis.",
# #                     class_="data-analysis-section-description",
# #                 ),
# #                 _node_weights(
# #                     node_substring_weights
# #                 ),
# #                 class_="feature-weight-group",
# #             ),

# #             # Cluster
# #             ui.div(
# #                 ui.h4("Cluster"),
# #                 ui.p(
# #                     "Weights used for numeric range "
# #                     "and clustering analysis.",
# #                     class_="data-analysis-section-description",
# #                 ),
# #                 _node_weights(
# #                     node_cluster_weights
# #                 ),
# #                 class_="feature-weight-group",
# #             ),

# #             # Fuzzy
# #             ui.div(
# #                 ui.h4("Cross-node Fuzzy"),
# #                 ui.p(
# #                     "Weights used for fuzzy property "
# #                     "matching across nodes.",
# #                     class_="data-analysis-section-description",
# #                 ),
# #                 _weight_list(
# #                     cross_node_fuzzy
# #                 ),
# #                 class_="feature-weight-group",
# #             ),
# #         )


# def feature_weights_server(
#     input,
#     output,
#     session,
#     *,
#     analysis_state,
#     update_weight,
# ):
#     """Display and update analysis feature weights."""

#     @render.ui
#     def feature_weights_content():
#         weights = analysis_state.feature_weights

#         sections = []

#         for feature_name, feature_config in weights.items():

#             # Fuzzy is structured differently:
#             # it is one cross-node weight configuration,
#             # not node -> weights.
#             if feature_name == "cross_node_fuzzy":
#                 sections.append(
#                     ui.div(
#                         ui.h4("Cross-node Fuzzy"),

#                         *[
#                             _weight_slider(
#                                 feature_name,
#                                 "cross_node",
#                                 weight_name,
#                                 value,
#                             )
#                             for weight_name, value
#                             in feature_config.items()
#                         ],

#                         class_="feature-weight-group",
#                     )
#                 )

#                 continue

#             node_sections = []

#             for node_name, node_weights in (
#                 feature_config.items()
#             ):
#                 node_sections.append(
#                     ui.div(
#                         ui.h5(
#                             node_name
#                             .replace("_", " ")
#                             .title()
#                         ),

#                         *[
#                             _weight_slider(
#                                 feature_name,
#                                 node_name,
#                                 weight_name,
#                                 value,
#                             )
#                             for weight_name, value
#                             in node_weights.items()
#                         ],

#                         class_="feature-weight-node",
#                     )
#                 )

#             sections.append(
#                 ui.div(
#                     ui.h4(
#                         feature_name
#                         .replace("_", " ")
#                         .title()
#                     ),

#                     *node_sections,

#                     class_="feature-weight-group",
#                 )
#             )

#         return ui.div(*sections)


"""Feature weights server."""

from shiny import reactive, render, ui


def _slider_id(
    feature_name: str,
    node_name: str,
    weight_name: str,
) -> str:
    return (
        f"weight__{feature_name}"
        f"__{node_name}"
        f"__{weight_name}"
    )

def _weight_slider(
    feature_name: str,
    node_name: str,
    weight_name: str,
    value: float,
) -> ui.Tag:
    return ui.div(
        ui.input_slider(
            _slider_id(
                feature_name,
                node_name,
                weight_name,
            ),
            None,
            min=0,
            max=1,
            value=value,
            step=0.01,
        ),
        class_="feature-weight-slider",
    )


def _node_weight_row(
    feature_name: str,
    node_name: str,
    node_weights: dict[str, float],
) -> ui.Tag:
    return ui.div(
        ui.div(
            node_name.replace("_", " ").title(),
            class_="feature-weight-node-name",
        ),

        *[
            ui.div(
                ui.input_slider(
                    _slider_id(
                        feature_name,
                        node_name,
                        weight_name,
                    ),
                    None,
                    min=0,
                    max=1,
                    value=value,
                    step=0.01,
                ),
                class_="feature-weight-slider",
            )
            for weight_name, value
            in node_weights.items()
        ],

        class_="feature-weight-row",
        style=f"--weight-count: {len(node_weights)};",
    )

def _weight_header(
    weight_names,
) -> ui.Tag:
    weight_names = list(weight_names)

    return ui.div(
        ui.div(
            "Node",
            class_="feature-weight-node-name",
        ),

        *[
            ui.div(
                name.replace("_", " ").title(),
                class_="feature-weight-column-name",
            )
            for name in weight_names
        ],

        class_="feature-weight-row feature-weight-header",
        style=f"--weight-count: {len(weight_names)};",
    )
def feature_weights_server(
    input,
    output,
    session,
    *,
    analysis_state,
    update_weight,
):
    """Display and update feature weights."""

    @render.ui
    def feature_weights_content():
        weights = analysis_state.feature_weights

        panels = []

        for feature_name in (
            "categorical",
            "substring",
            "cluster",
        ):
            feature_config = weights.get(
                feature_name,
                {}
            )

            if not feature_config:
                continue

            first_node_weights = next(
                iter(feature_config.values())
            )

            panels.append(
                ui.accordion_panel(
                    feature_name
                    .replace("_", " ")
                    .title(),

                    _weight_header(
                        first_node_weights.keys()
                    ),

                    *[
                        _node_weight_row(
                            feature_name,
                            node_name,
                            node_weights,
                        )
                        for node_name, node_weights
                        in feature_config.items()
                    ],
                )
            )

        # Cross-node fuzzy
        fuzzy = weights.get(
            "cross_node_fuzzy",
            {}
        )

        if fuzzy:
            panels.append(
                ui.accordion_panel(
                    "Cross-node Fuzzy",

                    ui.div(
                        *[
                            ui.div(
                                ui.div(
                                    weight_name
                                    .replace("_", " ")
                                    .title(),
                                    class_="feature-weight-column-name",
                                ),

                                _weight_slider(
                                    "cross_node_fuzzy",
                                    "cross_node",
                                    weight_name,
                                    value,
                                ),

                                class_="feature-weight-fuzzy-item",
                            )
                            for weight_name, value
                            in fuzzy.items()
                        ],

                        class_="feature-weight-fuzzy-row",
                    ),
                )
            )

        return ui.accordion(
            *panels,
            open=False,
            multiple=True,
        )
    # --------------------------------------------------
    # Register node-specific slider changes
    # --------------------------------------------------

    for feature_name, feature_config in (
        analysis_state.feature_weights.items()
    ):
        if feature_name == "cross_node_fuzzy":
            continue

        for node_name, node_weights in (
            feature_config.items()
        ):
            for weight_name in node_weights:

                slider_id = _slider_id(
                    feature_name,
                    node_name,
                    weight_name,
                )

                def register_weight_effect(
                    slider_id=slider_id,
                    feature_name=feature_name,
                    node_name=node_name,
                    weight_name=weight_name,
                ):
                    @reactive.effect
                    @reactive.event(
                        input[slider_id]
                    )
                    def _update():
                        value = input[slider_id]()

                        print(
                            "SLIDER CHANGED:",
                            slider_id,
                            value,
                        )

                        update_weight(
                            feature_name=feature_name,
                            node_name=node_name,
                            weight_name=weight_name,
                            value=value,
                        )

                register_weight_effect()

    # --------------------------------------------------
    # Register fuzzy slider changes
    # --------------------------------------------------

    fuzzy_weights = (
        analysis_state.feature_weights.get(
            "cross_node_fuzzy",
            {},
        )
    )

    for weight_name in fuzzy_weights:

        slider_id = _slider_id(
            "cross_node_fuzzy",
            "cross_node",
            weight_name,
        )

        def register_fuzzy_effect(
            slider_id=slider_id,
            weight_name=weight_name,
        ):
            @reactive.effect
            @reactive.event(
                input[slider_id]
            )
            def _update():
                value = input[slider_id]()

                print(
                    "FUZZY SLIDER CHANGED:",
                    slider_id,
                    value,
                )

                update_weight(
                    feature_name="cross_node_fuzzy",
                    node_name=None,
                    weight_name=weight_name,
                    value=value,
                )

        register_fuzzy_effect()