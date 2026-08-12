"""
_paths.py — import bootstrap for the mandala_bloom folder.

The bloom modules import each other flat (``from geometry_core import ...``),
matching the repo's own flat layout. This module puts both directories on
``sys.path`` so a bloom module resolves:

    concept_atlas, bases, bloom, bloom_bridge, ...        -> mandala_bloom/
    geometry_core, geometry_learner, mandala_solver       -> mandala_stack/
    octahedral_arithmetic, osl, ...                       -> repo root

That is the whole "connect" story: one namespace, three directories, no
duplicated copies of the modules the repo already owns.

``bootstrap()`` is idempotent and safe to call from any entry point
(``__init__.py``, ``bloom.py``, ``bloom_bridge.py``, tests).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
STACK = os.path.join(REPO_ROOT, "mandala_stack")


def bootstrap() -> None:
    """Put the repo root, mandala_stack/ and this folder on sys.path."""
    for path in (REPO_ROOT, STACK, HERE):
        if path not in sys.path:
            sys.path.insert(0, path)
