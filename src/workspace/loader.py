"""Workspace validation and loading."""

from __future__ import annotations

import sqlite3
from pathlib import Path
import json
from datetime import datetime, timezone
from .models import Workspace, ProjectMetadata


def load_project_metadata(
    workspace_path: str | Path,
) -> ProjectMetadata:
    """Load and validate project_metadata.json."""

    root = Path(workspace_path).expanduser().resolve()
    metadata_path = root / "project_metadata.json"
    now = datetime.now()
    if not metadata_path.exists():
        print(f"now = {now} path = {metadata_path}")
        raise ValueError(
            "The selected folder is not a valid project workspace. "
            "project_metadata.json was not found."
        )

    try:
        print(f"[metadata] path: {metadata_path}", flush=True)
        print(f"[metadata] exists: {metadata_path.exists()}", flush=True)
        print(f"[metadata] is_file: {metadata_path.is_file()}", flush=True)

        print("[metadata] reading file...", flush=True)

        raw = metadata_path.read_text(encoding="utf-8")

        print(f"[metadata] raw content: {raw!r}", flush=True)
        print("[metadata] parsing JSON...", flush=True)

        data = json.loads(raw)

        print(f"[metadata] parsed: {data!r}", flush=True)
        data = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            "project_metadata.json is not valid JSON."
        ) from exc

    required = {
        "project_name",
        "created_at",
        "updated_at",
        "workspace_version",
        "project_database",
    }

    missing = required - data.keys()

    if missing:
        raise ValueError(
            "Project metadata is missing required fields: "
            + ", ".join(sorted(missing))
        )

    metadata = ProjectMetadata(
        project_name=data["project_name"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        workspace_version=data["workspace_version"],
        project_database=data["project_database"],

        node_model_url=data.get(
            "node_model_url",
            "",
        ),
        property_model_url=data.get(
            "property_model_url",
            "",
        ),
    )
    return metadata

def load_workspace(
    root: str | Path,
) -> Workspace:
    """Load and validate an existing project workspace."""

    root_path = Path(root).expanduser().resolve()
    print(f"root_path = {root_path}")

    if not root_path.exists():
        raise ValueError("Workspace folder does not exist.")

    if not root_path.is_dir():
        raise ValueError("Workspace path is not a directory.")

    metadata = load_project_metadata(root_path)

    db_path = root_path / metadata.project_database

    if not db_path.exists():
        raise ValueError(
            f"Project database was not found: "
            f"{metadata.project_database}"
        )

    data_dir = root_path / "data"

    return Workspace(
        root=root_path,
        project_db=db_path,
        data_dir=data_dir,
        project_name=metadata.project_name,
        metadata=metadata,
    )
