"""Imported-files server behavior."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import shutil

import pandas as pd
from shiny import reactive, render, ui

from src.workspace.models import Workspace
from .ui import (
    data_preview_modal,
    format_file_size,
    import_files_modal,
    imported_files_modal,
    imported_files_selector,
)


SUPPORTED_DATA_FILES = {
    ".csv",
    ".xlsx",
    ".xls",
    ".parquet",
    ".json",
}

import json

def _load_json_data(
    path: Path,
) -> dict[str, pd.DataFrame]:
    """Load JSON records into separate DataFrames by node type."""

    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError as exc:
        raise InvalidDataFileError(
            f"{path.name} contains invalid JSON: "
            f"{exc.msg} at line {exc.lineno}, "
            f"column {exc.colno}."
        ) from exc

    except OSError as exc:
        raise InvalidDataFileError(
            f"Could not read {path.name}: {exc}"
        ) from exc

    if not isinstance(data, list):
        raise InvalidDataFileError(
            f"{path.name} must contain a JSON array."
        )

    if not all(
        isinstance(record, dict)
        for record in data
    ):
        raise InvalidDataFileError(
            f"{path.name} must contain an array of objects."
        )

    # Group RAW records before creating any DataFrame.
    grouped_records: dict[str, list[dict]] = {}

    for record in data:
        node_type = record.get("type")

        if node_type is None:
            node_type = record.get("type_")

        if node_type is None:
            raise InvalidDataFileError(
                "Each JSON record must contain either "
                "'type' or 'type_'."
            )

        # Keep only properties for this individual node record.
        node_record = {
            key: value
            for key, value in record.items()
            if key not in {"type", "type_"}
        }

        grouped_records.setdefault(
            str(node_type),
            [],
        ).append(node_record)

    # Create DataFrames only AFTER records have been grouped.
    return {
        node_type: pd.DataFrame(records)
        for node_type, records in grouped_records.items()
    }

class InvalidDataFileError(ValueError):
    """Raised when an imported file cannot be read as supported data."""


@dataclass(frozen=True)
class ImportedFile:
    """Metadata for one file stored in the workspace imported-data folder."""

    name: str
    path: Path
    extension: str
    size_bytes: int
    modified_at: datetime


def validate_data_file(path: Path) -> None:
    """Validate that a file exists and uses a supported data-file type."""

    if not path.exists():
        raise InvalidDataFileError("The selected file does not exist.")

    if not path.is_file():
        raise InvalidDataFileError("The selected path is not a file.")

    extension = path.suffix.lower()

    if extension not in SUPPORTED_DATA_FILES:
        raise InvalidDataFileError(
            f"Unsupported file type: {extension or 'unknown'}"
        )


def load_data_file(path: Path) -> pd.DataFrame:
    """Load a supported data file into a pandas DataFrame."""

    validate_data_file(path)
    extension = path.suffix.lower()

    try:
        if extension == ".csv":
            return pd.read_csv(path)
        if extension in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        if extension == ".parquet":
            return pd.read_parquet(path)
        if extension == ".json":
            return _load_json_data(path)
    except Exception as exc:
        raise InvalidDataFileError(
            f"Could not read {path.name}: {exc}"
        ) from exc

    raise InvalidDataFileError(f"Unsupported file type: {extension}")


def list_imported_files(workspace: Workspace) -> list[ImportedFile]:
    """Return files currently imported into the workspace."""

    imported_dir = workspace.data_dir / "imported"
    imported_dir.mkdir(parents=True, exist_ok=True)

    files: list[ImportedFile] = []

    for path in imported_dir.iterdir():
        if not path.is_file():
            continue

        stat = path.stat()
        files.append(
            ImportedFile(
                name=path.name,
                path=path,
                extension=path.suffix.lower(),
                size_bytes=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime),
            )
        )

    return sorted(
        files,
        key=lambda item: item.modified_at,
        reverse=True,
    )

def group_data_by_node(
    data: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Split data by node type and keep only properties used by each node."""

    # Support either node-type column name.
    node_column = next(
        (
            column
            for column in ("type", "type_")
            if column in data.columns
        ),
        None,
    )

    if node_column is None:
        raise InvalidDataFileError(
            "Imported data must contain either a "
            "'type' or 'type_' column."
        )

    # Node type is required.
    if data[node_column].isna().any():
        raise InvalidDataFileError(
            f"Some records are missing '{node_column}'."
        )

    grouped_data: dict[str, pd.DataFrame] = {}

    for node_type, node_data in data.groupby(
        node_column,
        sort=False,
    ):
        # Remove the node-type discriminator.
        node_data = node_data.drop(columns=[node_column])

        # IMPORTANT:
        # Remove properties that do not belong to this node.
        #
        # Since the combined source DataFrame contains the union of
        # properties from all node types, properties belonging only
        # to other nodes will be completely empty for this node.
        node_data = node_data.dropna(
            axis=1,
            how="all",
        )

        grouped_data[str(node_type)] = (
            node_data.reset_index(drop=True)
        )

    return grouped_data


def imported_files_server(
    input,
    output,
    session,
    *,
    app_state,
):
    """Manage imported files for the active workspace."""

    # All DataFrames separated by node type.
    # Example:
    # {
    #     "study": DataFrame(...),
    #     "publication": DataFrame(...),
    # }
    preview_node_data = reactive.value({})

    # The filesystem is not reactive. Increment this value whenever this
    # component changes data/imported so dependent outputs rescan the folder.
    files_version = reactive.value(0)

    def refresh_files() -> None:
        files_version.set(files_version.get() + 1)

    def get_imported_files() -> list[ImportedFile]:
        """Read the current imported files for the active workspace."""

        files_version.get()

        workspace = app_state.active_workspace
        if workspace is None:
            return []

        return list_imported_files(workspace)

    def show_file_preview(selected: str | None) -> None:
        """Load an imported file and display its data by node."""

        workspace = app_state.active_workspace
        if workspace is None:
            return

        if not selected:
            ui.notification_show(
                "Select a file first.",
                type="warning",
            )
            return

        file_path = workspace.data_dir / "imported" / selected

        try:
            data = load_data_file(file_path)
            grouped_data = group_data_by_node(data)

        except InvalidDataFileError as exc:
            ui.notification_show(
                str(exc),
                type="error",
            )
            return

        preview_node_data.set(grouped_data)

        ui.modal_show(
            data_preview_modal(
                file_name=selected,
                node_choices=list(grouped_data.keys()),
            )
        )

    # ------------------------------------------------------------------
    # Imported-file summary and selection
    # ------------------------------------------------------------------

    @render.ui
    def imported_files_summary():
        files = get_imported_files()

        if not files:
            return ui.div(
                "No files have been imported.",
                class_="imported-files-empty",
            )

        return imported_files_selector(
            files[:5],
            input_id="selected_imported_file",
            view_button_id="view_imported_file",
        )

    @reactive.effect
    @reactive.event(input.view_imported_file)
    def _view_imported_file():
        show_file_preview(input.selected_imported_file())

    @reactive.effect
    @reactive.event(input.analyze_imported_file)
    async def _analyze_imported_file():
        workspace = app_state.active_workspace

        if workspace is None:
            return

        selected = input.selected_imported_file()

        if not selected:
            ui.notification_show(
                "Select a file first.",
                type="warning",
            )
            return

        file_path = (
            workspace.data_dir
            / "imported"
            / selected
        )

        try:
            grouped_data = load_data_file(file_path)
        except InvalidDataFileError as exc:
            ui.notification_show(
                str(exc),
                type="error",
            )
            return

        app_state.selected_dataset = file_path
        app_state.node_dataframes = grouped_data
        print("_analyze_imported_file")
        print("grouped_data type:", type(grouped_data))

        if isinstance(grouped_data, dict):
            print("nodes:", grouped_data.keys())

            for node_name, df in grouped_data.items():
                print(
                    node_name,
                    df.shape,
                    list(df.columns),
                )

        await session.send_custom_message(
            "navigate",
            {
                "url": "/project/analysis/",
            },
        )

    # ------------------------------------------------------------------
    # View-all modal
    # ------------------------------------------------------------------

    @reactive.effect
    @reactive.event(input.view_imported_files)
    def _view_all_imported_files():
        ui.modal_show(imported_files_modal(get_imported_files()))

    @reactive.effect
    @reactive.event(input.view_imported_file_modal)
    def _view_imported_file_modal():
        show_file_preview(input.selected_imported_file_modal())

    # ------------------------------------------------------------------
    # Import modal
    # ------------------------------------------------------------------

    @reactive.effect
    @reactive.event(input.import_files)
    def _show_import_dialog():
        if app_state.active_workspace is None:
            return

        ui.modal_show(import_files_modal())

    @reactive.effect
    @reactive.event(input.cancel_import_files)
    def _cancel_import():
        ui.modal_remove()

    

    @render.ui
    def import_files_selection():
        files = input.import_data_files()

        if not files:
            return ui.div(
                "No files selected.",
                class_="import-files-empty",
            )

        return ui.div(
            ui.div(
                f"{len(files)} file"
                if len(files) == 1
                else f"{len(files)} files",
                class_="import-files-selection-count",
            ),
            *[
                ui.div(
                    ui.span(
                        file["name"],
                        class_="import-file-name",
                    ),
                    ui.span(
                        format_file_size(file["size"]),
                        class_="import-file-size",
                    ),
                    class_="import-file-row",
                )
                for file in files
            ],
            class_="import-files-selection",
        )

    @reactive.effect
    @reactive.event(input.confirm_import_files)
    def _import_selected_files():
        workspace = app_state.active_workspace
        if workspace is None:
            return

        files = input.import_data_files()
        if not files:
            ui.notification_show(
                "Choose at least one file to import.",
                type="warning",
            )
            return

        imported_dir = workspace.data_dir / "imported"
        imported_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            source = Path(file["datapath"])
            destination = imported_dir / file["name"]
            shutil.copy2(source, destination)

        # Notify the reactive UI that the filesystem contents changed.
        refresh_files()
        ui.modal_remove()

    # ------------------------------------------------------------------
    # Data preview
    # ------------------------------------------------------------------

    @render.ui
    def data_preview_summary():
        grouped_data = preview_node_data.get()

        if not grouped_data:
            return None

        selected_node = input.selected_preview_node()

        if not selected_node:
            return None

        data = grouped_data.get(selected_node)

        if data is None:
            return None

        return ui.div(
            ui.span(
                f"{len(data):,} rows",
                class_="data-preview-stat",
            ),
            ui.span(
                f"{len(data.columns):,} properties",
                class_="data-preview-stat",
            ),
            ui.span(
                "Showing first 100 rows",
                class_="data-preview-note",
            ),
            class_="data-preview-summary",
        )

    @render.data_frame
    def imported_file_preview():
        grouped_data = preview_node_data.get()

        if not grouped_data:
            return render.DataGrid([])

        selected_node = input.selected_preview_node()

        if not selected_node:
            return render.DataGrid([])

        data = grouped_data.get(selected_node)

        if data is None:
            return render.DataGrid([])

        return render.DataGrid(
            data.head(100),
            width="100%",
            height="500px",
        )
