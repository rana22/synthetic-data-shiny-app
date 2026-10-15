# Synthetic Data Workspace

A fresh Shiny for Python application for local synthetic-data projects.

## Current workflow

The application is intentionally small at the beginning:

- `/` — Welcome page
- `/create-project` — create a local workspace

Each path is a real Starlette route that mounts its own Shiny application. This means ordinary links such as `href="/create-project"` are real HTTP routes rather than relying on a request-aware UI callback to masquerade as a router.

## Workspace layout

Creating a project creates:

```text
project-folder/
├── project.db
├── data/
│   ├── imported/
│   ├── generated/
│   └── cache/
└── exports/
```

`project.db` stores project metadata and control-plane information. The database schema already includes tables for project metadata, external data sources, Cypher/GraphQL queries, datasets, and generation runs.

Large retrieved or generated datasets are intended to remain files under `data/`, with SQLite storing their metadata and location.

## External data

Authentication is intentionally not implemented in this first version. The placeholder `ExternalDataClient` is the boundary for a future Cypher/GraphQL connector.

## Local folder picker

The `Browse` button uses a native `tkinter` directory picker when the application is running locally on a desktop with a graphical environment. A hosted deployment cannot safely expose arbitrary client filesystem paths to server-side Python; hosted deployment will need a different workspace-storage model.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
shiny run --reload app.py --port 8301
```

Open `http://127.0.0.1:8301/`.
