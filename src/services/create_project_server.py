from __future__ import annotations

import subprocess
from pathlib import Path

from shiny import reactive, render, ui

from src.workspace.manager import create_workspace


def _local_folder_dialog() -> str | None:
    """Open the native macOS folder picker."""

    script = """
    POSIX path of (choose folder with prompt "Choose workspace folder")
    """

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        print(
            f"[folder-dialog] could not launch osascript: {exc}",
            flush=True,
        )
        return None

    if result.returncode != 0:
        print(
            f"[folder-dialog] cancelled or failed: "
            f"{result.stderr.strip()}",
            flush=True,
        )
        return None

    selected = result.stdout.strip()

    print(
        f"[folder-dialog] selected folder: {selected!r}",
        flush=True,
    )

    return selected or None


def create_project_server(
    input,
    output,
    session,
    *,
    app_state,
):
    """Wire local workspace selection and creation."""

    status = reactive.value("")

    @reactive.effect
    @reactive.event(input.browse_workspace)
    def _browse_workspace():
        print("[browse-workspace] button clicked", flush=True)

        selected = _local_folder_dialog()

        print(
            f"[browse-workspace] selected={selected!r}",
            flush=True,
        )

        if not selected:
            status.set("No folder was selected.")
            return

        ui.update_text(
            "workspace_path",
            value=selected,
        )

        status.set("Folder selected.")

    @reactive.effect
    @reactive.event(input.create_workspace)
    def _create_workspace():
        path = (input.workspace_path() or "").strip()
        name = (input.project_name() or "").strip()

        if not path:
            status.set("Choose a workspace folder first.")
            return

        if not name:
            status.set("Enter a project name first.")
            return

        try:
            workspace = create_workspace(
                Path(path),
                name,
            )
        except Exception as exc:
            status.set(
                f"Could not create workspace: {exc}"
            )
            return
        # --------------------------------------------------------------
        # Set application-level active workspace.
        # --------------------------------------------------------------
        app_state.active_workspace = workspace
        status.set(
            f"Workspace created: {workspace.root} | "
            f"Database: {workspace.project_db}"
        )

    @render.ui
    def workspace_status():
        message = status.get()

        if not message:
            return None

        return ui.div(
            message,
            class_="workspace-status",
        )
