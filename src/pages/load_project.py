"""Load existing project page."""

from shiny import ui


def load_project_page() -> ui.Tag:
    return ui.tags.section(
        ui.div(
            ui.span("PROJECT WORKSPACE", class_="eyebrow"),
            ui.h1("Load project"),
            ui.p(
                "Select an existing project folder containing project.db. "
                "The workspace will be validated before it is opened.",
                class_="lead",
            ),
            ui.div(
                ui.input_text(
                    "load_workspace_path",
                    "Project folder",
                    placeholder="Path to an existing project workspace",
                ),
                ui.div(
                    ui.input_action_button(
                        "browse_load_workspace",
                        "Browse",
                        class_="btn btn-secondary",
                    ),
                    ui.input_action_button(
                        "load_workspace",
                        "Load project",
                        class_="btn btn-primary",
                    ),
                    ui.a(
                        "Back",
                        href="/",
                        class_="btn btn-link",
                    ),
                    class_="workspace-actions",
                ),
                ui.output_ui("load_workspace_status"),
                class_="workspace-form",
            ),
            class_="workspace-card",
        ),
        class_="page-section page-load-project",
    )
