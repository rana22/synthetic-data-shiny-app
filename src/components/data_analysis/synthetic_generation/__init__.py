"""Synthetic data generation component."""

from .ui import synthetic_generation_ui
from .server import synthetic_generation_server


__all__ = [
    "synthetic_generation_ui",
    "synthetic_generation_server",
]