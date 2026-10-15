"""Workspace creation and validation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from .database import initialize_database
from .models import Workspace

REQUIRED_DIRS = (
    "data/imported",
    "data/generated",
    "data/cache",
    "exports",
)


def create_workspace(root: str | Path, project_name: str) -> Workspace:
    """Create a workspace directory tree and initialize project metadata/database."""

    root_path = Path(root).expanduser().resolve()
    project_name = project_name.strip()

    if not project_name:
        raise ValueError("Project name is required.")

    # Create workspace directories.
    root_path.mkdir(parents=True, exist_ok=True)

    for rel in REQUIRED_DIRS:
        (root_path / rel).mkdir(parents=True, exist_ok=True)

    # Create the SQLite database if it does not already exist.
    db_path = root_path / "project.db"
    initialize_database(db_path, project_name)

    # Create project metadata if it does not already exist.
    metadata_path = root_path / "project_metadata.json"
    now = datetime.now()
    print(f"time {now} path = {metadata_path}")
    if not metadata_path.exists():
        metadata = {
            "project_name": project_name,
            "created_at": now,
            "updated_at": now,
            "workspace_version": "1.0",
            "project_database": "project.db",
        }
        print(f"{json.dumps(metadata, indent=2)}")
        raise ValueError(
            "The selected folder is not a valid project workspace. "
            "project_metadata.json was not found."
        )

    if not metadata_path.exists():
        now = datetime.now(timezone.utc).isoformat()

        metadata = {
            "project_name": project_name,
            "created_at": now,
            "updated_at": now,
            "workspace_version": "1.0",
            "project_database": "project.db",
        }

        metadata_path.write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )

    return Workspace(
        root=root_path,
        project_db=db_path,
        data_dir=root_path / "data",
        project_name=project_name,
    )