"""Synthetic Data Workspace application entry point."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from dataclasses import dataclass, field
import pandas as pd
from shiny import App, reactive, ui
from starlette.applications import Starlette
from starlette.routing import Mount

from src.components.shell import page_shell
from src.pages.create_project import create_project_page
from src.pages.welcome import welcome_page
from src.pages.load_project import load_project_page
from src.pages.project_details import project_details_page
from src.services.create_project_server import create_project_server
from src.services.empty_server import empty_server
from src.services.load_project_server import load_project_server
from src.services.project_details_server import project_details_server
from src.workspace.models import Workspace
from src.pages.data_analysis import (
    data_analysis_page,
)
from src.components.data_analysis.ui import (
    data_analysis_ui
)

from src.components.data_analysis.server import (
    data_analysis_server,
)
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "src" / "www"


PageFactory = Callable[[], ui.Tag]

@dataclass
class ApplicationState:
    """Application-level runtime state shared by routed pages."""

    active_workspace: Workspace | None = None
    workspace_cache: dict[str, Workspace] = field(
        default_factory=dict
    )
    selected_dataset: Path | None = None
    node_dataframes: dict[str, pd.DataFrame] | None = None
application_state = ApplicationState()

# ---------------------------------------------------------------------------
# Shared application state
# ---------------------------------------------------------------------------
#
# This represents the workspace currently being used by the application.
# It is the runtime source of truth.
#
# active_workspace: reactive.Value[Workspace | None] = reactive.value(None)

def make_shiny_app(page_factory: PageFactory, server_factory) -> App:
    """Build one small Shiny application for a routed page."""
    def server(input, output, session):
        return server_factory(
            input,
            output,
            session,
            app_state=application_state,
        )
    return App(
        page_shell(page_factory()),
        server,
        static_assets=str(STATIC_DIR),
    )


# Each application owns a real HTTP route. This avoids relying on a UI
# callback to act as an HTTP router and makes ordinary href navigation work.
ROUTES: dict[str, App] = {
    "/create-project": make_shiny_app(create_project_page, create_project_server),
    "/load-project": make_shiny_app(load_project_page, load_project_server),
    "/project/analysis/": make_shiny_app(
        data_analysis_ui,
        data_analysis_server,
    ),
    "/project/": make_shiny_app(
        project_details_page,
        project_details_server,
    ),
    "/": make_shiny_app(welcome_page, empty_server),
}


app = Starlette(
    routes=[
        Mount(path, app=shiny_app)
        for path, shiny_app in ROUTES.items()
    ]
)
