"""Imported-files UI components."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from shiny import ui


SUPPORTED_FILE_TYPES = [
    ".csv",
    ".xlsx",
    ".xls",
    ".parquet",
    ".json",
]


def format_file_size(size_bytes: int) -> str:
    """Format a byte count for display."""

    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024**2:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024**3:
        return f"{size_bytes / 1024**2:.1f} MB"
    return f"{size_bytes / 1024**3:.1f} GB"


def format_file_datetime(value: Any) -> str:
    """Format an imported-file timestamp for display."""

    return value.strftime("%b %-d, %Y")


def imported_file_choice(file: Any) -> ui.Tag:
    """Render the display label used by one imported-file radio option."""

    return ui.div(
        ui.span(
            file.name,
            class_="imported-file-name",
            title=file.name,
        ),
        ui.span(
            file.extension.lstrip(".").upper(),
            class_="imported-file-type",
        ),
        ui.span(
            format_file_size(file.size_bytes),
            class_="imported-file-size",
        ),
        ui.span(
            format_file_datetime(file.modified_at),
            class_="imported-file-date",
        ),
        class_="imported-file-choice",
    )


def imported_files_selector(
    files,
    *,
    input_id: str,
    view_button_id: str,
) -> ui.Tag:
    """Render imported files as a selectable radio list."""

    choices = {
        file.name: file.name
        for file in files
    }

    return ui.div(
        ui.input_radio_buttons(
            input_id,
            None,
            choices=choices,
            selected=None,
        ),

        ui.input_action_button(
            view_button_id,
            "View selected file",
            class_="btn btn-secondary imported-files-view-file",
        ),
         ui.input_action_button(
            "analyze_imported_file",
            "Analyze",
            class_="btn btn-primary imported-files-analyze",
        ),

        class_="imported-files-selector",
    )


def imported_files_ui() -> ui.Tag:
    """Render the imported-files summary on the project overview."""

    return ui.tags.section(
        ui.div(
            ui.div(
                ui.h2(
                    "Imported Files",
                    class_="imported-files-title",
                ),
                ui.p(
                    "Files available as source data for "
                    "synthetic data generation.",
                    class_="imported-files-description",
                ),
                class_="imported-files-heading",
            ),
            ui.input_action_button(
                "view_imported_files",
                "View all",
                class_="btn btn-ghost imported-files-view-all",
            ),
            class_="imported-files-header",
        ),
        ui.output_ui("imported_files_summary"),
        ui.div(
            ui.input_action_button(
                "import_files",
                "+ Import files",
                class_="btn btn-ghost imported-files-import",
            ),
            class_="imported-files-actions",
        ),
        class_="imported-files-card",
    )


def imported_files_modal(files) -> ui.Tag:
    """Render all imported files in a selectable modal."""

    return ui.modal(
        imported_files_selector(
            files,
            input_id="selected_imported_file_modal",
            view_button_id="view_imported_file_modal",
        ),
        title=f"Imported Files ({len(files)})",
        easy_close=True,
        size="l",
    )


def import_files_modal() -> ui.Tag:
    """Render the data-file import dialog."""

    return ui.modal(
        ui.div(
            ui.p(
                "Add local data files to this project. "
                "Imported files will be copied into the "
                "workspace data/imported directory.",
                class_="import-files-description",
            ),
            ui.input_file(
                "import_data_files",
                "Choose files",
                multiple=True,
                accept=SUPPORTED_FILE_TYPES,
            ),
            ui.output_ui("import_files_selection"),
            class_="import-files-modal-content",
        ),
        title="Import data files",
        footer=ui.div(
            ui.input_action_button(
                "cancel_import_files",
                "Cancel",
                class_="btn btn-secondary",
            ),
            ui.input_action_button(
                "confirm_import_files",
                "Import",
                class_="btn btn-primary",
            ),
            class_="import-files-modal-actions",
        ),
        easy_close=False,
        size="l",
    )


def data_preview_modal(
    file_name: str,
    node_choices: list[str],
) -> ui.Tag:
    """Render imported data separated by node."""

    selected = node_choices[0] if node_choices else None

    return ui.modal(
        ui.div(
            ui.input_select(
                "selected_preview_node",
                "Select node",
                choices=node_choices,
                selected=selected,
            ),
            ui.output_ui("data_preview_summary"),
            ui.output_data_frame("imported_file_preview"),
            class_="imported-file-preview",
        ),
        title=f"Data preview — {file_name}",
        easy_close=True,
        size="xl",
    )
