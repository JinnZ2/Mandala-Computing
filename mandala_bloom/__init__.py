"""
mandala_bloom — a two-level bloom over the Atlas concept map, with the seven
bases of measurement built into the geometry.

Where `mandala_stack/` makes the *shape* an input, this folder makes the
*measurement* an input. A distance here is never bare: it is taken by an
instrument with its own sensitivity, read against a calibration standard,
traversed in a particular way of knowing, through a space with acknowledged
blind spots, by an observer who may be inside the system.

    1. Measurement      Riemannian metric g_ij(u)
    2. Instruments      sensitivity tensor I_ij(u), symmetric positive-definite
    3. Metrology        calibration mu(u), penalised for drifting
    4. Ways of knowing  one vector field per traversal mode
    5. Unknowns         kappa(u) >= 0, where the map runs out
    6. Physics          the energy functional over all of the above
    7. Attunement       omega(u) in [0,1], observer participation

Torch is optional
-----------------
`concept_atlas` (the data) and `bloom_bridge.learn_atlas_geometry` (embedding
via the stack's own learner) are numpy-only and always available. `bases` and
`bloom` need PyTorch; importing them without it raises normally, and
`bloom_bridge`'s self-test degrades to the numpy path with a message. The repo
does not take a hard torch dependency — see `requirements-bloom.txt`.

This follows the repo's own invariant: breathing degrades, never fails.

Connecting
----------
Importing this package puts the repo root, `mandala_stack/` and this folder on
`sys.path`, so all three share one flat namespace::

    import mandala_bloom
    from mandala_bloom import learn_atlas_geometry     # this folder, no torch
    from mandala_solver import MandalaSolver           # mandala_stack/
    from octahedral_arithmetic import PHI              # repo root
"""

import importlib
import importlib.util
import sys

from ._paths import HERE, REPO_ROOT, STACK, bootstrap

bootstrap()

__version__ = "1.0"

#: Submodules that need no training backend.
NUMPY_SUBMODULES = ("concept_atlas", "bloom_bridge")

#: Submodules that require PyTorch.
TORCH_SUBMODULES = ("bases", "bloom")

SUBMODULES = NUMPY_SUBMODULES + TORCH_SUBMODULES

_EXPORTS = {
    # concept_atlas — always available
    "EMOJI_MAP": "concept_atlas",
    "CONCEPTS": "concept_atlas",
    "NUM_CONCEPTS": "concept_atlas",
    "KNOWING_MODES": "concept_atlas",
    "AtlasEntry": "concept_atlas",
    "ENTRIES": "concept_atlas",
    "concept_id": "concept_atlas",
    "similarity": "concept_atlas",
    "target_distance": "concept_atlas",
    "entry_distance_fn": "concept_atlas",
    # bloom_bridge — always available
    "BloomGeometry": "bloom_bridge",
    "geometry_from_bloom": "bloom_bridge",
    "learn_atlas_geometry": "bloom_bridge",
    "register_bloom_geometry": "bloom_bridge",
    "path_to_glyphs": "bloom_bridge",
    "path_to_number": "bloom_bridge",
    "compare_embeddings": "bloom_bridge",
    "solve_on_atlas": "bloom_bridge",
    # bases / bloom — need torch
    "InstrumentField": "bases",
    "CalibrationField": "bases",
    "UnknownField": "bases",
    "KnowingField": "bases",
    "AttunementField": "bases",
    "pullback_metric": "bases",
    "BloomConfig": "bloom",
    "BloomResult": "bloom",
    "MandalaBloom": "bloom",
    "bloom": "bloom",
}

__all__ = tuple(SUBMODULES) + tuple(_EXPORTS) + (
    "bootstrap", "HERE", "REPO_ROOT", "STACK", "has_torch",
)


def has_torch() -> bool:
    """Whether a training backend is present. Cheap — does not import torch."""
    return importlib.util.find_spec("torch") is not None


def _load(name: str):
    if name in TORCH_SUBMODULES and not has_torch():
        raise ImportError(
            f"mandala_bloom.{name} requires PyTorch, which is not installed. "
            f"Install it with `pip install -r requirements-bloom.txt`. "
            f"The numpy-only path — concept_atlas and "
            f"bloom_bridge.learn_atlas_geometry() — works without it."
        )
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
