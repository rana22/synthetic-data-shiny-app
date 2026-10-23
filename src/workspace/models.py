"""Workspace data models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataSourceConfig:
    """External/reference data source configured for a project."""

    id: str
    name: str
    source_type: str

    uri: str
    database: str | None
    username: str | None

    # This is encrypted content only.
    # Never place a plaintext password in this field.
    password_encrypted: str | None = None

    enabled: bool = True

@dataclass(frozen=True)
class ProjectMetadata:
    """Metadata stored in project_metadata.json."""

    project_name: str
    created_at: str
    updated_at: str
    workspace_version: str
    project_database: str

    data_sources: tuple[DataSourceConfig, ...] = ()

    node_model_url: str = ""
    property_model_url: str = ""

@dataclass(frozen=True)
class Workspace:
    """Resolved local project workspace."""

    root: Path
    project_db: Path
    data_dir: Path
    project_name: str
    metadata: ProjectMetadata | None = None
