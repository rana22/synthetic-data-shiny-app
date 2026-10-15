"""SQLite initialization for local project workspaces."""

from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    config_json TEXT NOT NULL DEFAULT '{}',
    credential_ref TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    language TEXT NOT NULL,
    query_text TEXT NOT NULL,
    data_source_id INTEGER,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (data_source_id) REFERENCES data_sources(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    format TEXT NOT NULL,
    row_count INTEGER,
    schema_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS generation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generator_type TEXT NOT NULL,
    configuration_json TEXT NOT NULL DEFAULT '{}',
    output_dataset_id INTEGER,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY (output_dataset_id) REFERENCES datasets(id) ON DELETE SET NULL
);
"""


def initialize_database(db_path: Path, project_name: str) -> None:
    """Create the project database and seed its singleton project record."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    import datetime as dt

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.execute(
            """
            INSERT INTO project (id, name, description, created_at, updated_at)
            VALUES (1, ?, NULL, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                updated_at = excluded.updated_at
            """,
            (project_name, now, now),
        )
        conn.commit()
