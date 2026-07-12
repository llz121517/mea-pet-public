"""Project root and path helpers."""
from __future__ import annotations

import os
from pathlib import Path

# meapet/ is inside project root
PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent


def project_root() -> str:
    return str(PROJECT_ROOT)


def project_path(*parts: str) -> str:
    return str(PROJECT_ROOT.joinpath(*parts))
