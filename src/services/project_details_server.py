# """Project-details page server."""

# from __future__ import annotations

# from dataclasses import replace
# import json
# from pathlib import Path
# from datetime import datetime
# from shiny import render, ui, reactive

# from src.workspace.loader import load_workspace
# from ..workspace.models import Workspace
# from src.components.imported_files.server import imported_files_server

# ACTIVE_WORKSPACE_FILE = (
#     Path.home()
#     / ".synthetic-data-generator"
#     / "active_workspace.json"
# )


# def _get_active_workspace_path() -> Path | None:
#     """Return the remembered active workspace path."""

#     if not ACTIVE_WORKSPACE_FILE.is_file():
#         return None

#     try:
#         payload = json.loads(
#             ACTIVE_WORKSPACE_FILE.read_text(
#                 encoding="utf-8"
#             )
#         )
#     except (OSError, json.JSONDecodeError):
#         return None

#     if not isinstance(payload, dict):
#         return None

#     path = payload.get("path")

#     if not isinstance(path, str) or not path.strip():
#         return None

#     workspace_path = (
#         Path(path)
#         .expanduser()
#         .resolve()
#     )

#     if not workspace_path.is_dir():
#         return None

#     return workspace_path


# def format_project_datetime(value: str) -> str:
#     """Format an ISO project timestamp for display."""

#     try:
#         timestamp = datetime.fromisoformat(value)
#     except (TypeError, ValueError):
#         return value

#     return timestamp.strftime("%B %-d, %Y at %-I:%M %p %Z")

# def project_details_server(
#     input,
#     output,
#     session,
#     *,
#     app_state,
# ):

#     """Render details for the active workspace."""

#     # Register Imported Files component behavior.
#     imported_files_server(
#         input,
#         output,
#         session,
#         app_state=app_state,
#     )

#     """Render details for the active workspace."""

#     @reactive.effect
#     @reactive.event(input.save_project_details)
#     def _save_project_details():
#         workspace = app_state.active_workspace

#         if workspace is None:
#             return

#         metadata = workspace.metadata

#         if metadata is None:
#             return

#         project_name = (
#             input.project_name() or ""
#         ).strip()

#         project_database = (
#             input.project_database() or ""
#         ).strip()

#         node_url = (
#             input.node_model_url() or ""
#         ).strip()

#         property_url = (
#             input.property_model_url() or ""
#         ).strip()

#         if not project_name:
#             ui.notification_show(
#                 "Project name is required.",
#                 type="warning",
#             )
#             return

#         updated_metadata = replace(
#             metadata,

#             project_name=project_name,
#             project_database=project_database,

#             node_model_url=node_url,
#             property_model_url=property_url,

#             # System managed
#             updated_at=datetime.now()
#             .astimezone()
#             .isoformat(),
#         )

#         updated_workspace = replace(
#             workspace,
#             project_name=project_name,
#             metadata=updated_metadata,
#         )

#         app_state.active_workspace = (
#             updated_workspace
#         )

#         ui.notification_show(
#             "Project details updated.",
#             type="message",
#         )

#     @render.ui
#     def project_details_content():
#         workspace = app_state.active_workspace

#         if workspace is None:
#             return ui.div(
#                 ui.p(
#                     "No project is currently loaded."
#                 ),
#                 ui.a(
#                     "Load project",
#                     href="/load-project/",
#                     class_="btn btn-primary",
#                 ),
#                 class_="workspace-status",
#             )

#         metadata = workspace.metadata

#         if metadata is None:
#             return ui.div(
#                 ui.p(
#                     "Project metadata is unavailable."
#                 ),
#                 class_="workspace-status workspace-status-error",
#             )

#         rows = (
#             (
#                 "Project name",
#                 metadata.project_name,
#             ),
#             (
#                 "Workspace version",
#                 metadata.workspace_version,
#             ),
#             (
#                 "Created: ",
#                 format_project_datetime(metadata.created_at),
#             ),
#             (
#                 "Updated: ",
#                 format_project_datetime(metadata.updated_at),
#             ),
#             (
#                 "Database",
#                 metadata.project_database,
#             ),
#             (
#                 "Workspace",
#                 str(workspace.root),
#             ),
#         )

#         return ui.div(
#             *[
#                 ui.div(
#                     ui.span(
#                         label,
#                         class_="project-details-label",
#                     ),
#                     ui.span(
#                         str(value),
#                         class_="project-details-value",
#                     ),
#                     class_="project-details-row",
#                 )
#                 for label, value in rows
#             ],
#             ui.div(
#                 ui.a(
#                     "Load another project",
#                     href="/load-project/",
#                     class_="btn btn-secondary",
#                 ),
#                 class_="workspace-actions",
#             ),
#             class_="project-details",
#         )

"""Project-details page server."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime
import json
from pathlib import Path

from shiny import reactive, render, ui

from src.components.imported_files.server import (
    imported_files_server,
)
from src.workspace.models import Workspace


ACTIVE_WORKSPACE_FILE = (
    Path.home()
    / ".synthetic-data-generator"
    / "active_workspace.json"
)


def _get_active_workspace_path() -> Path | None:
    """Return the remembered active workspace path."""

    if not ACTIVE_WORKSPACE_FILE.is_file():
        return None

    try:
        payload = json.loads(
            ACTIVE_WORKSPACE_FILE.read_text(
                encoding="utf-8"
            )
        )
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    path = payload.get("path")

    if not isinstance(path, str) or not path.strip():
        return None

    workspace_path = (
        Path(path)
        .expanduser()
        .resolve()
    )

    if not workspace_path.is_dir():
        return None

    return workspace_path


def format_project_datetime(value: str) -> str:
    """Format an ISO project timestamp for display."""

    try:
        timestamp = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return value

    return timestamp.strftime(
        "%B %-d, %Y at %-I:%M %p %Z"
    )


def _save_project_metadata(
    workspace: Workspace,
) -> None:
    """Persist the workspace project metadata to disk."""

    metadata = workspace.metadata

    if metadata is None:
        raise ValueError(
            "Project metadata is unavailable."
        )

    metadata_path = (
        workspace.root
        / "project_metadata.json"
    )

    payload = asdict(metadata)

    metadata_path.write_text(
        json.dumps(
            payload,
            indent=2,
        ),
        encoding="utf-8",
    )


def project_details_server(
    input,
    output,
    session,
    *,
    app_state,
):
    """Render and update details for the active workspace."""

    # --------------------------------------------------------------
    # Imported Files component
    # --------------------------------------------------------------

    imported_files_server(
        input,
        output,
        session,
        app_state=app_state,
    )

    # --------------------------------------------------------------
    # Populate editable project fields
    # --------------------------------------------------------------

    @reactive.effect
    def _populate_project_details():
        """Populate inputs from the active project metadata."""

        workspace = app_state.active_workspace

        if workspace is None:
            return

        metadata = workspace.metadata

        if metadata is None:
            return

        ui.update_text(
            "project_name",
            value=metadata.project_name,
        )

        ui.update_text(
            "project_database",
            value=metadata.project_database,
        )

        ui.update_text(
            "node_model_url",
            value=getattr(
                metadata,
                "node_model_url",
                "",
            ) or "",
        )

        ui.update_text(
            "property_model_url",
            value=getattr(
                metadata,
                "property_model_url",
                "",
            ) or "",
        )

    # --------------------------------------------------------------
    # Update project metadata
    # --------------------------------------------------------------

    @reactive.effect
    @reactive.event(
        input.save_project_details
    )
    def _save_project_details():
        """Validate and persist editable project metadata."""

        workspace = app_state.active_workspace

        if workspace is None:
            ui.notification_show(
                "No project is currently loaded.",
                type="warning",
            )
            return

        metadata = workspace.metadata

        if metadata is None:
            ui.notification_show(
                "Project metadata is unavailable.",
                type="error",
            )
            return

        # ----------------------------------------------------------
        # Read inputs
        # ----------------------------------------------------------

        project_name = (
            input.project_name() or ""
        ).strip()

        project_database = (
            input.project_database() or ""
        ).strip()

        node_model_url = (
            input.node_model_url() or ""
        ).strip()

        property_model_url = (
            input.property_model_url() or ""
        ).strip()

        # ----------------------------------------------------------
        # Validation
        # ----------------------------------------------------------

        if not project_name:
            ui.notification_show(
                "Project name is required.",
                type="warning",
            )
            return

        if not project_database:
            ui.notification_show(
                "Database is required.",
                type="warning",
            )
            return

        # The model URLs can remain blank until the user
        # configures Data Analysis.
        if bool(node_model_url) != bool(property_model_url):
            ui.notification_show(
                "Provide both the Node YAML URL and "
                "Properties YAML URL, or leave both blank.",
                type="warning",
            )
            return

        # ----------------------------------------------------------
        # Create updated immutable metadata
        # ----------------------------------------------------------

        updated_metadata = replace(
            metadata,
            project_name=project_name,
            project_database=project_database,
            node_model_url=node_model_url,
            property_model_url=property_model_url,
            updated_at=(
                datetime.now()
                .astimezone()
                .isoformat()
            ),
        )

        # Workspace is also immutable.
        updated_workspace = replace(
            workspace,
            project_name=project_name,
            metadata=updated_metadata,
        )

        # ----------------------------------------------------------
        # Persist before updating runtime state
        # ----------------------------------------------------------

        try:
            _save_project_metadata(
                updated_workspace
            )
        except (OSError, ValueError) as exc:
            ui.notification_show(
                f"Could not update project metadata: {exc}",
                type="error",
            )
            return

        # ----------------------------------------------------------
        # Update application state
        # ----------------------------------------------------------

        app_state.active_workspace = (
            updated_workspace
        )

        # If this workspace is cached, update the cached
        # Workspace object as well.
        workspace_cache = getattr(
            app_state,
            "workspace_cache",
            None,
        )

        if isinstance(workspace_cache, dict):
            root_key = str(workspace.root)

            if root_key in workspace_cache:
                workspace_cache[root_key] = (
                    updated_workspace
                )

        ui.notification_show(
            "Project details updated.",
            type="message",
        )

    # --------------------------------------------------------------
    # Current project metadata
    # --------------------------------------------------------------

    @render.ui
    def project_details_content():
        """Display current project metadata."""

        workspace = app_state.active_workspace

        if workspace is None:
            return ui.div(
                ui.p(
                    "No project is currently loaded."
                ),
                ui.a(
                    "Load project",
                    href="/load-project/",
                    class_="btn btn-primary",
                ),
                class_="workspace-status",
            )

        metadata = workspace.metadata

        if metadata is None:
            return ui.div(
                ui.p(
                    "Project metadata is unavailable."
                ),
                class_=(
                    "workspace-status "
                    "workspace-status-error"
                ),
            )

        rows = (
            (
                "Project name",
                metadata.project_name,
            ),
            (
                "Workspace version",
                metadata.workspace_version,
            ),
            (
                "Created",
                format_project_datetime(
                    metadata.created_at
                ),
            ),
            (
                "Updated",
                format_project_datetime(
                    metadata.updated_at
                ),
            ),
            (
                "Database",
                metadata.project_database,
            ),
            (
                "Node model",
                getattr(
                    metadata,
                    "node_model_url",
                    "",
                ) or "Not configured",
            ),
            (
                "Property model",
                getattr(
                    metadata,
                    "property_model_url",
                    "",
                ) or "Not configured",
            ),
            (
                "Workspace",
                str(workspace.root),
            ),
        )

        return ui.div(
            *[
                ui.div(
                    ui.span(
                        label,
                        class_="project-details-label",
                    ),
                    ui.span(
                        str(value),
                        class_="project-details-value",
                    ),
                    class_="project-details-row",
                )
                for label, value in rows
            ],

            class_="project-details",
        )

    @reactive.effect
    def _initialize_project_details():
        workspace = app_state.active_workspace

        if workspace is None:
            return

        metadata = workspace.metadata

        if metadata is None:
            return

        ui.update_text(
            "project_name",
            value=metadata.project_name,
        )

        ui.update_text(
            "project_database",
            value=metadata.project_database,
        )

        ui.update_text(
            "node_model_url",
            value=getattr(
                metadata,
                "node_model_url",
                "",
            ) or "",
        )

        ui.update_text(
            "property_model_url",
            value=getattr(
                metadata,
                "property_model_url",
                "",
            ) or "",
        )