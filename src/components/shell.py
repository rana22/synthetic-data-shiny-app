"""Shared application shell."""

from __future__ import annotations

from shiny import ui


def global_header() -> ui.Tag:
    """Render global application chrome shared by every page."""
    return ui.tags.header(
        ui.div(
            ui.div(
                ui.span("Synthetic Data", class_="app-header-product"),
                ui.span("Workspace", class_="app-header-product-muted"),
                class_="app-header-brand",
            ),
            class_="app-header",
        )
    )


def page_shell(content: ui.Tag) -> ui.Tag:
    """Wrap routed page content in the shared document shell."""
    return ui.page_fluid(
        ui.tags.head(
            ui.tags.link(rel="stylesheet", href="css/global.css"),
            ui.tags.link(rel="stylesheet", href="css/shell.css"),
            ui.tags.link(rel="stylesheet", href="css/pages.css"),
            ui.tags.script(
               """
                (function () {
                    if (
                        typeof Shiny === "undefined" ||
                        !Shiny.addCustomMessageHandler
                    ) {
                        return;
                    }

                    Shiny.addCustomMessageHandler(
                        "navigate",
                        function (message) {
                            if (
                                message &&
                                typeof message.url === "string"
                            ) {
                                window.location.href = message.url;
                            }
                        }
                    );

                    Shiny.addCustomMessageHandler(
                        "remember-workspace",
                        function (message) {
                            try {
                                localStorage.setItem(
                                    "synthetic-data-workspace",
                                    JSON.stringify(message)
                                );
                            } catch (_) {
                                // localStorage is convenience state only.
                            }
                        }
                    );
                })();
                """

            ),
        ),
        global_header(),
        ui.tags.main(content, class_="app-main"),
        class_="app-page",
        title="Synthetic Data Workspace",
    )
