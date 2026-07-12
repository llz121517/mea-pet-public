#!/usr/bin/env python3
"""MeaPet setup wizard entry (compat)."""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from wizard.app import main, SetupWizard  # noqa: F401
from wizard.platform_info import PLATFORM, detect_platform, platform_checklist  # noqa: F401

if __name__ == "__main__":
    main()
