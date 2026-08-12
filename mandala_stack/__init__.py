"""
mandala_stack — geometry-agnostic mandala computing stack.

The root repo hardcodes octahedral geometry (8 states, O_h symmetry). This
folder generalises it: the solver talks to a ``Geometry`` protocol, so the
same annealing / bloom / factorization code runs on octahedral, tetrahedral,
dodecahedral, hexagonal, Hilbert — or a geometry *learned from data*.

See ``README.md`` in this folder for the hypothesis, the experimental results
(including the failures), and the API.

Connecting to the root repo
---------------------------
Importing this package puts both this folder and the repo root on
``sys.path``, so stack modules and root modules share one flat namespace::

    import mandala_stack                       # bootstraps paths
    from mandala_stack import MandalaSolver    # this folder
    from octahedral_arithmetic import PHI      # repo root

The stack deliberately does NOT carry its own copies of
``quantum_mandala.py``, ``octahedral_arithmetic.py`` or
``scale_invariance_breakdown.py`` — those live at the repo root and are
imported from there, so there is exactly one version of each.

For explicit two-way conversion between stack geometries and the root
engine's cells/states, use ``mandala_stack.stack_bridge``.

Lazy access
-----------
Submodules and the headline classes are resolved on first attribute access,
so ``import mandala_stack`` stays cheap (no numpy import until you ask for a
solver). Each submodule is registered under both its flat name and its
dotted name, so ``mandala_stack.geometry_core is geometry_core``.
"""

import importlib
import sys

from ._paths import HERE, REPO_ROOT, bootstrap

bootstrap()

__version__ = "3.0"

#: Modules that live in this folder.
SUBMODULES = (
    "geometry_core",
    "geometry_learner",
    "mandala_solver",
    "geometric_solver",
    "geodesic_memory",
    "adapters",
    "consumer_hardware",
    "fractal_address",
    "stack_bridge",
    "stack_cli",
    "compare_solvers",
    "demo_learned_geometry",
)

#: Headline symbols, mapped to the submodule that defines them.
_EXPORTS = {
    "PHI": "geometry_core",
    "Geometry": "geometry_core",
    "OctahedralGeometry": "geometry_core",
    "TetrahedralGeometry": "geometry_core",
    "DodecahedralGeometry": "geometry_core",
    "HexagonalGeometry": "geometry_core",
    "HilbertGeometry": "geometry_core",
    "get_geometry": "geometry_core",
    "list_geometries": "geometry_core",
    "register_learned_geometry": "geometry_core",
    "GeometryLearner": "geometry_learner",
    "LearnedGeometry": "geometry_learner",
    "MandalaSolver": "mandala_solver",
    "AnnealResult": "mandala_solver",
    "BloomResult": "mandala_solver",
    "FactorResult": "mandala_solver",
    "GeometricSolver": "geometric_solver",
    "GeometricEnergy": "geometric_solver",
    "ManifoldGradient": "geometric_solver",
    "GeodesicMemory": "geodesic_memory",
    "DNAAdapter": "adapters",
    "RNAAdapter": "adapters",
    "ProteinAdapter": "adapters",
    "UniversalAdapter": "adapters",
    "ConsumerGeometricComputer": "consumer_hardware",
}

__all__ = tuple(SUBMODULES) + tuple(_EXPORTS) + ("bootstrap", "HERE", "REPO_ROOT")


def _load(name: str):
    """Import a stack submodule and alias it under the package namespace."""
    module = importlib.import_module(name)
    sys.modules[f"{__name__}.{name}"] = module
    globals()[name] = module
    return module


def __getattr__(name: str):
    if name in SUBMODULES:
        return _load(name)
    if name in _EXPORTS:
        return getattr(_load(_EXPORTS[name]), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(__all__))
