"""Project metadata persistence helpers."""

from __future__ import annotations

import json
from dataclasses import asdict

from .models import Workspace


def save_project_metadata(workspace: Workspace) -> None:
    """Persist the workspace metadata to project_metadata.json."""

    metadata = workspace.metadata
    if metadata is None:
        raise ValueError("Project metadata is unavailable.")

    metadata_path = workspace.root / "project_metadata.json"
    metadata_path.write_text(
        json.dumps(asdict(metadata), indent=2) + "\n",
        encoding="utf-8",
    )
