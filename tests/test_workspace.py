from pathlib import Path

from src.workspace.manager import create_workspace


def test_create_workspace(tmp_path: Path):
    workspace = create_workspace(tmp_path / "demo", "Demo Project")

    assert workspace.project_db.exists()
    assert (workspace.root / "data" / "imported").is_dir()
    assert (workspace.root / "data" / "generated").is_dir()
    assert (workspace.root / "data" / "cache").is_dir()
    assert (workspace.root / "exports").is_dir()
