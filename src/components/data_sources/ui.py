"""Project data-source UI components."""

from __future__ import annotations

from shiny import ui


from src.workspace.models import DataSourceConfig


def data_sources_ui() -> ui.Tag:
    """Render the project data-source summary."""

    return ui.tags.section(
        # --------------------------------------------------------------
        # Header
        # --------------------------------------------------------------
        ui.div(
            ui.div(
                ui.h2(
                    "Data Sources",
                    class_="data-sources-title",
                ),
                ui.p(
                    "Configure reference data sources used by "
                    "this project.",
                    class_="data-sources-description",
                ),
                class_="data-sources-heading",
            ),

            ui.input_action_button(
                "view_disease_support",
                "Disease support",
                class_="btn btn-primary disease-support-view",
            ),

            ui.input_action_button(
                "configure_data_source",
                "+ Configure",
                class_="btn btn-ghost data-sources-configure",
            ),

            class_="data-sources-header",
        ),

        # --------------------------------------------------------------
        # Configured sources
        # --------------------------------------------------------------
        ui.output_ui(
            "data_sources_summary",
        ),

        class_="data-sources-card",
    )


def neo4j_configuration_modal() -> ui.Tag:
    """Render the Neo4j connection configuration dialog."""

    return ui.modal(
        ui.div(
            ui.input_text(
                "data_source_name",
                "Connection name",
                placeholder="Canine Data Commons",
            ),

            ui.input_text(
                "neo4j_uri",
                "Neo4j URI",
                placeholder="bolt://localhost:7687",
            ),

            ui.input_text(
                "neo4j_database",
                "Database",
                value="neo4j",
            ),

            ui.input_text(
                "neo4j_username",
                "Username",
                placeholder="neo4j",
            ),

            ui.input_password(
                "neo4j_password",
                "Password",
                placeholder="Enter password",
            ),

            # Test-connection feedback.
            ui.output_ui(
                "neo4j_connection_status",
            ),

            class_="data-source-config-form",
        ),

        title="Configure Neo4j",

        footer=ui.div(
            ui.input_action_button(
                "test_neo4j_connection",
                "Test connection",
                class_="btn btn-secondary",
            ),

            ui.input_action_button(
                "save_neo4j_configuration",
                "Save configuration",
                class_="btn btn-primary",
            ),

            class_="data-source-config-actions",
        ),

        easy_close=True,
        size="l",
    )

def data_source_row(
    source: DataSourceConfig,
) -> ui.Tag:
    """Render one configured project data source."""

    return ui.div(
        ui.div(
            ui.div(
                ui.span(
                    source.name,
                    class_="data-source-name",
                ),
                ui.span(
                    source.source_type.upper(),
                    class_="data-source-type",
                ),
                class_="data-source-primary",
            ),

            ui.span(
                "Enabled"
                if source.enabled
                else "Disabled",
                class_=(
                    "data-source-status "
                    + (
                        "is-enabled"
                        if source.enabled
                        else "is-disabled"
                    )
                ),
            ),

            class_="data-source-row-header",
        ),

        ui.div(
            ui.span(
                source.uri,
                class_="data-source-uri",
            ),

            (
                ui.span(
                    source.database,
                    class_="data-source-database",
                )
                if source.database
                else None
            ),

            class_="data-source-details",
        ),

        ui.div(
            ui.input_action_button(
                "view_neo4j_source_data",
                "View source data",
                class_="btn btn-secondary data-source-view",
            ),

            class_="data-source-actions",
        ),

        class_="data-source-row",
    )

def disease_source_data_modal(
    source_name: str,
) -> ui.Tag:
    """Display disease terms retrieved from a reference source."""

    return ui.modal(
        ui.div(
            ui.p(
                "Disease terms available from the "
                "configured reference data source.",
                class_="data-source-preview-description",
            ),

            ui.output_ui(
                "neo4j_disease_terms",
            ),

            class_="data-source-preview",
        ),

        title=f"Source data — {source_name}",

        footer=ui.div(
            ui.input_action_button(
                "analyze_selected_disease",
                "Analyze",
                class_="btn btn-primary",
            ),
            class_="data-source-preview-actions",
        ),

        easy_close=True,
        size="l",
    )

