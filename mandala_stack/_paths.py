"""
_paths.py — import bootstrap for the mandala_stack folder.

The stack modules import each other flat (``from geometry_core import ...``),
matching the repo's own flat layout. This module puts both directories on
``sys.path`` so a stack module resolves:

    geometry_core, mandala_solver, geodesic_memory, ...   -> mandala_stack/
    quantum_mandala, octahedral_arithmetic, ...           -> repo root

That is the whole "connect" story: one namespace, two directories, no
duplicated copies of the modules the repo already owns.

``bootstrap()`` is idempotent and safe to call from any entry point
(``__init__.py``, ``stack_cli.py``, ``stack_bridge.py``, tests).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)


def bootstrap() -> None:
    """Put mandala_stack/ and the repo root on sys.path (front, in that order)."""
    for path in (REPO_ROOT, HERE):
        if path not in sys.path:
            sys.path.insert(0, path)
