#!/usr/bin/env python3
"""MeaPet desktop entry (compat). Prefer: python -m meapet.desktop.app"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from meapet.desktop.app import main

if __name__ == "__main__":
    raise SystemExit(main() or 0)
