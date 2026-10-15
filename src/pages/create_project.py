"""Create project page."""

from shiny import ui


def create_project_page() -> ui.Tag:
    return ui.tags.section(
        ui.div(
            ui.span("PROJECT WORKSPACE", class_="eyebrow"),
            ui.h1("Create project"),
            ui.p(
                "Choose a local folder. The application will create the project "
                "database and data directories inside it.",
                class_="lead",
            ),
            ui.div(
                ui.div(
                    ui.input_text(
                        "workspace_path",
                        "Workspace folder",
                        placeholder="Choose a local workspace folder",
                    ),
                    ui.input_action_button(
                        "browse_workspace",
                        "Browse",
                        class_="btn btn-secondary",
                    ),
                    class_="workspace-picker-row",
                ),
                ui.input_text(
                    "project_name",
                    "Project name",
                    placeholder="My synthetic data project",
                ),
                ui.div(
                    ui.input_action_button(
                        "create_workspace",
                        "Create workspace",
                        class_="btn btn-primary",
                    ),
                    ui.a(
                        "Back",
                        href="/",
                        class_="btn btn-link",
                    ),
                    class_="workspace-actions",
                ),
                ui.output_ui("workspace_status"),
                class_="workspace-form",
            ),
            class_="workspace-card",
        ),
        class_="page-section page-create-project",
    )
