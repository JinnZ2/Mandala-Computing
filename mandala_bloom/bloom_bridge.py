"""
bloom_bridge.py — connect the bloom to mandala_stack/ and the repo root.

The bloom produces a layout of Atlas entries under a *learned, position-
dependent* metric. `mandala_stack` already has a protocol for "a shape you can
solve on" (`Geometry`) and a learner that produces one from a distance
function (`GeometryLearner`). This module is the seam between them:

    bloom result      -> stack Geometry      geometry_from_bloom()
    atlas distances   -> stack Geometry      learn_atlas_geometry()   [no torch]
    stack Geometry    -> solver              any MandalaSolver call
    concept path      -> root glyph math     path_to_glyphs()
    bloom vs learner  -> comparison          compare_embeddings()

Two of these need no PyTorch at all. `learn_atlas_geometry()` hands the same
concept/glyph dissimilarity the bloom fits to the stack's existing learner, so
the Atlas is embeddable on a numpy-only machine — and it doubles as the
control the bloom has to beat. `geometry_from_bloom()` consumes a
`BloomResult`, which is plain floats, so a bloom trained elsewhere can be
loaded and solved on without a training backend present.

That split is the point: the repo does not acquire a hard torch dependency.
Torch buys you the seven bases and the two-level coupling; without it the
Atlas still embeds, still becomes a geometry, and still solves.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

try:
    from ._paths import bootstrap
except ImportError:  # executed as a plain script
    from _paths import bootstrap
bootstrap()

import concept_atlas as atlas

# stack side (numpy only)
from geometry_core import PHI, GEOMETRIES, register_learned_geometry
from geometry_learner import GeometryLearner, LearnedGeometry
from mandala_solver import MandalaSolver

# root side (stdlib)
import octahedral_arithmetic as _oct


__all__ = [
    "BloomGeometry",
    "geometry_from_bloom",
    "learn_atlas_geometry",
    "register_bloom_geometry",
    "path_to_glyphs",
    "path_to_number",
    "compare_embeddings",
    "solve_on_atlas",
]


# ---------------------------------------------------------------------------
# A bloom result, wearing the stack's Geometry protocol
# ---------------------------------------------------------------------------

class BloomGeometry:
    """A trained bloom exposed as a `mandala_stack` Geometry.

    States are Atlas entries. Distance is measured with the bloom's learned
    **instrument tensor**, not plain Euclidean:

        d(a,b)^2 = (u_a - u_b)^T  I_avg  (u_a - u_b),   I_avg = (I_a + I_b)/2

    That is the one thing this geometry has that `LearnedGeometry` does not.
    `LearnedGeometry._distance` is Euclidean in the embedding, so the metric is
    isotropic everywhere; here sensitivity varies from point to point, which is
    exactly base 2 of the seven.

    Needs no torch — it reads the floats out of a `BloomResult`.
    """

    def __init__(self, positions: Sequence[Sequence[float]],
                 labels: Sequence[str],
                 instrument: Optional[Sequence[Sequence[Sequence[float]]]] = None,
                 glyphs: Optional[Sequence[str]] = None,
                 n_neighbors: int = 2,
                 name: str = "bloom"):
        if len(positions) != len(labels):
            raise ValueError("positions and labels must be the same length")
        self.positions = [tuple(float(v) for v in p) for p in positions]
        self.labels = list(labels)
        self.instrument = ([[list(map(float, row)) for row in mat]
                            for mat in instrument] if instrument else None)
        self._glyphs = list(glyphs) if glyphs else None
        self.n_neighbors = max(1, min(n_neighbors, len(self.positions) - 1))
        self._name = name
        self._transitions = self._build_transitions()

    # -- protocol -----------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    @property
    def n_states(self) -> int:
        return len(self.positions)

    @property
    def dimension(self) -> int:
        return len(self.positions[0])

    def position(self, state: int) -> Tuple[float, ...]:
        return self.positions[state]

    def transitions(self, state: int) -> List[int]:
        return self._transitions[state]

    def transition_cost(self, a: int, b: int) -> float:
        if b not in self._transitions[a]:
            return float("inf")
        return self._distance(a, b)

    def eigenvalues(self, state: int) -> Tuple[float, ...]:
        """Normalised |position| components — the state's energy signature."""
        pos = self.position(state)
        total = sum(abs(v) for v in pos) + 1e-10
        return tuple(abs(v) / total for v in pos)

    def glyph(self, state: int) -> str:
        if self._glyphs is not None:
            return self._glyphs[state]
        return _oct.GLYPHS[state % len(_oct.GLYPHS)]

    def scale_position(self, state: int, layer: int) -> Tuple[float, ...]:
        scale = PHI ** (-layer)
        return tuple(v * scale for v in self.position(state))

    # -- the instrument-modulated metric ------------------------------------

    def _distance(self, a: int, b: int) -> float:
        pa, pb = self.positions[a], self.positions[b]
        diff = [x - y for x, y in zip(pa, pb)]
        if self.instrument is None:
            return math.sqrt(sum(v * v for v in diff))
        ia, ib = self.instrument[a], self.instrument[b]
        dim = len(ia)
        quad = 0.0
        for i in range(dim):
            for j in range(dim):
                avg = 0.5 * (ia[i][j] + ib[i][j])
                quad += diff[i] * avg * diff[j]
        return math.sqrt(max(quad, 0.0))

    def _build_transitions(self) -> Dict[int, List[int]]:
        result: Dict[int, List[int]] = {}
        for a in range(len(self.positions)):
            ranked = sorted(
                (self._distance(a, b), b)
                for b in range(len(self.positions)) if b != a
            )
            result[a] = [b for _, b in ranked[:self.n_neighbors]]
        return result

    def label(self, state: int) -> str:
        return self.labels[state]

    def distance_matrix(self) -> List[List[float]]:
        n = len(self.positions)
        return [[self._distance(i, j) for j in range(n)] for i in range(n)]


# ---------------------------------------------------------------------------
# Constructors
# ---------------------------------------------------------------------------

def geometry_from_bloom(result, use_instrument: bool = True,
                        n_neighbors: int = 2) -> BloomGeometry:
    """Turn a `BloomResult` into a solvable stack Geometry.

    Set `use_instrument=False` to drop base 2 and fall back to Euclidean
    distance in the learned embedding — the ablation that isolates what the
    instrument tensor is doing.
    """
    return BloomGeometry(
        positions=result.positions,
        labels=result.names,
        instrument=result.instrument if use_instrument else None,
        n_neighbors=n_neighbors,
        name="bloom-instrument" if use_instrument else "bloom-euclidean",
    )


def learn_atlas_geometry(method: str = "force_directed", dim: int = 2,
                         concept_weight: float = 0.6,
                         seed: Optional[int] = 42,
                         entries: Sequence[atlas.AtlasEntry] = atlas.ENTRIES
                         ) -> LearnedGeometry:
    """Embed the Atlas with the stack's own learner. **No torch required.**

    Same dissimilarity the bloom fits, run through
    `mandala_stack.GeometryLearner`. Two jobs:

    1. it makes the concept atlas usable on a numpy-only install, and
    2. it is the control. The bloom claims a learned position-dependent metric
       buys something; the honest way to check is against the repo's existing
       learner on identical input.
    """
    items = list(entries)
    distance = atlas.entry_distance_fn(entries, concept_weight)
    return GeometryLearner(method=method, dim=dim, seed=seed).learn(items, distance)


def register_bloom_geometry(geometry, name: Optional[str] = None) -> str:
    """Add a bloom geometry to the stack registry so `get_geometry()` sees it."""
    key = name or geometry.name
    register_learned_geometry(key, geometry)
    return key


# ---------------------------------------------------------------------------
# Concept paths -> root glyph arithmetic
# ---------------------------------------------------------------------------

def path_to_glyphs(entry: atlas.AtlasEntry) -> str:
    """Render an entry's concept path in the root octahedral glyph alphabet.

    Concept ids are taken mod 8 onto the octahedral states, which is lossy —
    22 concepts do not fit in 8 states. It is a projection for display and for
    feeding glyph-space arithmetic, not an encoding you can invert.
    """
    n = len(_oct.GLYPHS)
    return "".join(_oct.GLYPHS[cid % n] for cid in entry.concept_ids)


def path_to_number(entry: atlas.AtlasEntry, offset: int = 2):
    """An entry's concept path as an exact base-8 `OctahedralNumber`.

    Same lossy mod-8 projection as `path_to_glyphs`. What it buys is that a
    concept story becomes a number the root's exact glyph arithmetic can add,
    multiply and factor.
    """
    states = [cid % len(_oct.GLYPHS) for cid in entry.concept_ids]
    return _oct.states_to_number(states, offset=offset)


# ---------------------------------------------------------------------------
# Comparison — does the bloom beat the plain learner?
# ---------------------------------------------------------------------------

def _correlation(xs: Sequence[float], ys: Sequence[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


def _offdiag(matrix, n: int) -> List[float]:
    return [float(matrix[i][j]) for i in range(n) for j in range(n) if i != j]


def compare_embeddings(bloom_geometry: Optional[BloomGeometry] = None,
                       concept_weight: float = 0.6,
                       seed: Optional[int] = 42) -> Dict[str, float]:
    """Correlate each embedding's distances against the target dissimilarity.

    Returns Pearson r per method. Higher is better: it means the layout
    actually realises the concept/glyph dissimilarity as geometry.

    This is the falsifiable part. The bloom is a much larger model than the
    stack's learner; if it does not score better on the thing both are fitting,
    the extra machinery is not earning its place, and that belongs in the
    README as a measured result rather than being quietly omitted.
    """
    entries = atlas.ENTRIES
    n = len(entries)
    target = atlas.target_distance(entries, concept_weight)
    target_flat = _offdiag(target, n)

    scores: Dict[str, float] = {}

    learned = learn_atlas_geometry(concept_weight=concept_weight, seed=seed)
    learned_flat = [learned._distance(entries[i], entries[j])
                    for i in range(n) for j in range(n) if i != j]
    scores["stack_learner"] = _correlation(target_flat, learned_flat)

    if bloom_geometry is not None:
        matrix = bloom_geometry.distance_matrix()
        scores["bloom"] = _correlation(target_flat, _offdiag(matrix, n))

        euclidean = BloomGeometry(bloom_geometry.positions, bloom_geometry.labels,
                                  instrument=None, name="bloom-euclidean")
        scores["bloom_no_instrument"] = _correlation(
            target_flat, _offdiag(euclidean.distance_matrix(), n))

    return scores


def solve_on_atlas(geometry, problem: str = "random_landscape",
                   data: Optional[Dict[str, Any]] = None,
                   steps: int = 200, seed: int = 7):
    """Run the stack's shape-agnostic solver on an Atlas geometry.

    Proof that the bloom output is a first-class shape: the same
    `MandalaSolver` that anneals octahedra anneals the concept atlas, with no
    changes on either side.
    """
    solver = MandalaSolver(geometry=geometry, seed=seed)
    return solver.anneal(problem, data or {"seed": 42}, steps=steps)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _self_test() -> None:
    print("=" * 76)
    print("BLOOM BRIDGE — concept atlas <-> mandala_stack <-> root engine")
    print("=" * 76)

    print("\n--- 1. Atlas through the stack's own learner (no torch) ---")
    learned = learn_atlas_geometry()
    print(f"  {learned.name}: {learned.n_states} states, dim={learned.dimension}")
    for i, entry in enumerate(atlas.ENTRIES):
        pos = tuple(round(float(v), 3) for v in learned.position(i))
        print(f"    {entry.name:34s} {pos}")

    print("\n--- 2. The same geometry, solved on ---")
    result = solve_on_atlas(learned)
    winner = atlas.ENTRIES[result.best_state]
    print(f"  anneal -> state {result.best_state} ({winner.name}), "
          f"E={result.best_energy:.4f}")

    print("\n--- 3. Concept paths in root glyph space ---")
    for entry in atlas.ENTRIES:
        number = path_to_number(entry)
        print(f"  {entry.entry_id}  {path_to_glyphs(entry)}  "
              f"-> {number.to_glyphs()} = {number.to_decimal()}")

    print("\n--- 4. Does a trained bloom beat the plain learner? ---")
    try:
        from bloom import bloom as train_bloom, BloomConfig

        trained = train_bloom(BloomConfig(epochs=800), verbose=False)
        geometry = geometry_from_bloom(trained)
        register_bloom_geometry(geometry, "atlas-bloom")
        print(f"  registered '{geometry.name}' "
              f"({geometry.n_states} states, dim={geometry.dimension})")
        scores = compare_embeddings(geometry)
        for method, r in sorted(scores.items(), key=lambda kv: -kv[1]):
            print(f"    {method:22s} r = {r:+.4f}")
        print("  (r against the concept/glyph dissimilarity both are fitting)")
    except ImportError as exc:
        print(f"  skipped — PyTorch not installed ({exc}).")
        print("  Everything above this line still works: the bloom is optional,")
        print("  the atlas and its geometry are not.")

    print("\n" + "=" * 76)
    print("Bridge self-test complete.")
    print("=" * 76)


if __name__ == "__main__":
    _self_test()
