
"""Project details page."""

from __future__ import annotations

from shiny import ui

from src.components.imported_files import imported_files_ui
from src.components.data_sources import data_sources_ui

def project_details_page() -> ui.Tag:
    """Render the project details / overview page."""

    return ui.tags.section(
        ui.div(
            ui.span(
                "PROJECT WORKSPACE",
                class_="eyebrow",
            ),

            ui.h1("Project details"),

            ui.p(
                "Review and update the active local workspace "
                "and project metadata.",
                class_="lead",
            ),

            # ----------------------------------------------------------
            # Current project metadata
            # ----------------------------------------------------------
            ui.output_ui(
                "project_details_content",
            ),

            # ----------------------------------------------------------
            # Editable project configuration
            # ----------------------------------------------------------
            ui.div(
                ui.h2("Project Configuration"),

                ui.p(
                    "Update the project metadata and data model "
                    "configuration.",
                    class_="project-details-description",
                ),

                ui.input_text(
                    "project_name",
                    "Project name",
                ),

                ui.input_text(
                    "project_database",
                    "Database",
                ),

                ui.input_text(
                    "node_model_url",
                    "Node YAML URL",
                    placeholder="https://...",
                ),

                ui.input_text(
                    "property_model_url",
                    "Properties YAML URL",
                    placeholder="https://...",
                ),

                ui.input_action_button(
                    "save_project_details",
                    "Update project details",
                    class_="btn btn-primary",
                ),

                class_="project-data-model",
            ),

            # Neo4j / reference database configuration
            data_sources_ui(),

            # ----------------------------------------------------------
            # Imported files
            # ----------------------------------------------------------
            imported_files_ui(),

            # ----------------------------------------------------------
            # Workspace actions
            # ----------------------------------------------------------
            ui.div(
                ui.a(
                    "Load another project",
                    href="/load-project/",
                    class_="btn btn-secondary",
                ),
                class_="workspace-actions",
            ),

            class_="workspace-card",
        ),

        class_="page-section page-project-details",
    )