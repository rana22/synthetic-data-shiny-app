"""Welcome page."""

from shiny import ui


def welcome_page() -> ui.Tag:
    return ui.tags.section(
        ui.div(
            ui.span("PROJECT WORKSPACE", class_="eyebrow"),
            ui.h1("Welcome"),
            ui.p(
                "Create a local project workspace or load an existing one to "
                "work with data, queries, metadata, and synthetic generation.",
                class_="lead",
            ),
            ui.div(
                ui.a(
                    "Create project",
                    href="/create-project/",
                    class_="btn btn-primary",
                ),
                ui.a(
                    "Load project",
                    href="/load-project/",
                    class_="btn btn-secondary",
                ),
                class_="welcome-actions",
            ),
            ui.div(id="recent-workspace", class_="recent-workspace"),
            class_="welcome-card",
        ),
        ui.tags.script(
            """
            (function () {
                const value = localStorage.getItem('synthetic-data-workspace');
                const target = document.getElementById('recent-workspace');
                if (!target || !value) return;
                try {
                    const item = JSON.parse(value);
                    if (!item.path) return;
                    target.innerHTML =
                        '<div class="recent-workspace-label">Recent workspace</div>' +
                        '<code>' + item.path.replace(/[&<>\"]/g, function (c) {' +
                        'return {"&":"&amp;","<":"&lt;",">":"&gt;",\"":"&quot;"}[c];' +
                        '}) + '</code>';
                } catch (_) {}
            })();
            """
        ),
        class_="page-section page-welcome",
    )
