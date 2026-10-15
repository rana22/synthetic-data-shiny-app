"""Load-project page server."""

from shiny import reactive, render, ui
import json
from pathlib import Path
from src.services.create_project_server import _local_folder_dialog
from src.workspace.loader import load_workspace

def normalize_workspace_path(path: str) -> str:
    return str(
        Path(path)
        .expanduser()
        .resolve()
    )

# def load_project_server(
#     input,
#     output,
#     session,
#     *,
#     app_state,
# ):
#     """Wire local workspace selection and validation."""
#     status = reactive.value("")

#     def get_workspace(path: str):
#         """Return a cached workspace or load and cache it."""

#         cache_key = normalize_workspace_path(path)

#         # Check cache first
#         cached_workspace = app_state.workspace_cache.get(
#             cache_key
#         )

#         if cached_workspace is not None:
#             return cached_workspace, True

#         # Not cached, so load from disk
#         workspace = load_workspace(cache_key)

#         # Cache for future use
#         app_state.workspace_cache[cache_key] = workspace

#         return workspace, False

#     @reactive.effect
#     @reactive.event(input.browse_load_workspace)
#     def _browse():
#         selected = _local_folder_dialog()
#         if selected:
#             ui.update_text("load_workspace_path", value=selected)
#             status.set("Folder selected.")

#     @reactive.effect
#     @reactive.event(input.load_workspace)
#     async def _load():
#         path = (input.load_workspace_path() or "").strip()

#         if not path:
#             status.set("Choose a project folder first.")
#             return

#         try:
#             # workspace = load_workspace(path)
#             workspace, from_cache = get_workspace(path)
#         except Exception as exc:
#             status.set(
#                 f"Could not load workspace: {exc}"
#             )
#             return

#         app_state.active_workspace = workspace
#         if not hasattr(app_state, "workspace_cache"):
#             app_state.workspace_cache = {}
            
#         status.set(
#             f"Loaded project: "
#             f"{workspace.project_name} ({workspace.root})"
#         )

#         await session.send_custom_message(
#             "navigate",
#             {"url": "/project/"},
#         )


#     @render.ui
#     def load_workspace_status():
#         message = status.get()

#         if not message:
#             return None

#         return ui.div(
#             message,
#             class_="workspace-status",
#         )

def load_project_server(
    input,
    output,
    session,
    *,
    app_state,
):
    status = reactive.value("")

    @reactive.effect
    def _restore_workspace_path():
        workspace = app_state.active_workspace

        if workspace is None:
            return

        ui.update_text(
            "load_workspace_path",
            value=str(workspace.root),
        )

    @reactive.effect
    @reactive.event(input.browse_load_workspace)
    def _browse():
        selected = _local_folder_dialog()

        if selected:
            ui.update_text(
                "load_workspace_path",
                value=selected,
            )
            status.set("Folder selected.")

    @reactive.effect
    @reactive.event(input.load_workspace)
    async def _load():
        path = (
            input.load_workspace_path() or ""
        ).strip()

        if not path:
            status.set(
                "Choose a project folder first."
            )
            return

        try:
            cached_workspace = (
                app_state.workspace_cache.get(path)
            )

            if cached_workspace is not None:
                workspace = cached_workspace
            else:
                workspace = load_workspace(path)

                app_state.workspace_cache[path] = (
                    workspace
                )

        except Exception as exc:
            status.set(
                f"Could not load workspace: {exc}"
            )
            return

        app_state.active_workspace = workspace

        status.set(
            f"Loaded project: "
            f"{workspace.project_name} "
            f"({workspace.root})"
        )

        await session.send_custom_message(
            "navigate",
            {"url": "/project/"},
        )

    @render.ui
    def load_workspace_status():
        message = status.get()

        if not message:
            return None

        return ui.div(
            message,
            class_="workspace-status",
        )