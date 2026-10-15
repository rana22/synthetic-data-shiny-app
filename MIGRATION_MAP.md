# Architecture map

## Routing

```text
Starlette
├── /                  -> Welcome Shiny app
└── /create-project    -> Create Project Shiny app
```

The route registry is in `app.py`. Each route is a real ASGI mount.

## Shell

`src/components/shell.py` owns the global header and document assets.

## Workspace

`src/workspace/manager.py` creates the local project folder tree.

`src/workspace/database.py` owns SQLite schema creation.

`src/workspace/models.py` contains the workspace model.

## Data

`src/api/client.py` is a placeholder external data boundary. It deliberately does not embed credentials or authentication logic.

## Future pages

Planned routes can be added as additional mounted Shiny apps:

```text
/project
/project/data-sources
/project/data
/project/queries
/project/generate
/project/history
/project/settings
```
