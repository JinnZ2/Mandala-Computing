#!/usr/bin/env python3
"""
stack_bridge.py — connect the geometry-agnostic stack to the root repo engine
=============================================================================

The stack (``mandala_stack/``) is shape-agnostic: its solver only knows the
``Geometry`` protocol. The root repo (``mandala_computer.py``,
``geometric_state_algebra.py``, ``octahedral_arithmetic.py``) is the opposite —
it commits hard to one shape, the octahedron, and knows its physics exactly.

This module is the seam between them. It goes both ways:

    root physics  ->  stack Geometry
        RootOctahedralGeometry   root's sin^2 coupling law + Fibonacci
                                 eigenvalues + glyph alphabet, exposed as a
                                 Geometry the stack solver can anneal on
        CayleyGeometry           the full 48-element O_h group as a 48-state
                                 geometry, transitions = generator moves,
                                 cost = Cayley graph distance

    stack solver  ->  root cells
        geometric_relax()        anneal a live MandalaComputer using the
                                 stack's geometry-constrained moves while
                                 scoring with the root's own total energy
        states_from_computer()   read cell states out
        apply_states()           write cell states back

    root arithmetic  <-  stack states
        states_to_glyphs()       stack states as the root's octahedral glyphs
        states_to_number()       stack states as an exact OctahedralNumber

    root physics  ->  learned geometry
        learn_root_geometry()    hand the root's coupling law to the stack's
                                 GeometryLearner and see what manifold it
                                 recovers. The root repo *asserts* octahedral
                                 structure; this measures whether the metric
                                 it uses actually implies that structure.

Nothing here duplicates code that already exists on either side — it only
translates. Run ``python mandala_stack/stack_bridge.py`` for a self-test.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

try:  # imported as part of the package
    from ._paths import bootstrap
except ImportError:  # executed as a plain script from inside the folder
    from _paths import bootstrap

bootstrap()

# stack side
from geometry_core import PHI, GEOMETRIES, register_learned_geometry
from mandala_solver import MandalaSolver

# root side
import octahedral_arithmetic as _oct


__all__ = [
    "RootOctahedralGeometry",
    "CayleyGeometry",
    "register_bridge_geometries",
    "states_from_computer",
    "apply_states",
    "geometric_relax",
    "states_to_glyphs",
    "states_to_number",
    "learn_root_geometry",
    "root_coupling_energy",
]


# ---------------------------------------------------------------------------
# The root repo's coupling law, as a plain function
# ---------------------------------------------------------------------------

def root_coupling_energy(a: int, b: int, coupling_strength: float = 1.0,
                         num_states: int = 8) -> float:
    """
    The root engine's coupling energy between two octahedral states.

        E_coupling = J * sin(|s_i - s_j| * pi / 4)^2

    This is the exact law used by ``MandalaComputer.compute_total_energy``.
    Keeping one implementation here means the bridge geometries and the root
    engine cannot drift apart.
    """
    half = num_states / 2.0
    return coupling_strength * math.sin(abs(a - b) * math.pi / half) ** 2


# ---------------------------------------------------------------------------
# Geometry 1: the root octahedron, exposed through the stack's protocol
# ---------------------------------------------------------------------------

class RootOctahedralGeometry:
    """
    The root repo's octahedral substrate as a stack ``Geometry``.

    Differences from ``geometry_core.OctahedralGeometry``, which is a
    hand-written table:

    * ``transition_cost`` is the root engine's sin^2 coupling law, not
      Euclidean distance between hand-placed vertices.
    * ``eigenvalues`` come from ``MandalaComputer._generate_fibonacci_eigenvalues``
      (phi^i normalised), not a literal dict.
    * ``glyph`` is the root glyph alphabet from ``octahedral_arithmetic``,
      so a stack trace and a root ``glyph_trace()`` print the same symbols.

    Transitions are the states reachable in one step. ``ring_width`` controls
    how far a single move may travel around the 8-state ring; the default of 1
    matches the root engine's nearest-neighbour proposals.
    """

    def __init__(self, coupling_strength: float = 1.0, ring_width: int = 1,
                 depth: int = 5, num_states: int = 8):
        self.coupling_strength = coupling_strength
        self.ring_width = max(1, int(ring_width))
        self.depth = depth
        self._n = int(num_states)
        self._eigen = self._fibonacci_eigenvalues(depth)

    # -- protocol -----------------------------------------------------------

    @property
    def name(self) -> str:
        return f"octahedral-root-w{self.ring_width}"

    @property
    def n_states(self) -> int:
        return self._n

    @property
    def dimension(self) -> int:
        return 3

    def position(self, state: int) -> Tuple[float, float, float]:
        """
        Position on the octahedral ring embedded in 3-space.

        States sit at angle ``state * 2pi / n`` on the equator; the z axis
        carries the parity split so opposite states are genuinely opposite.
        """
        angle = 2.0 * math.pi * state / self._n
        return (math.cos(angle), math.sin(angle), 1.0 if state % 2 == 0 else -1.0)

    def transitions(self, state: int) -> List[int]:
        return sorted(
            (state + d) % self._n
            for d in range(-self.ring_width, self.ring_width + 1)
            if d != 0
        )

    def transition_cost(self, a: int, b: int) -> float:
        if b not in self.transitions(a):
            return float("inf")
        return root_coupling_energy(a, b, self.coupling_strength, self._n)

    def eigenvalues(self, state: int) -> Tuple[float, ...]:
        """Three consecutive Fibonacci/phi eigenvalues starting at `state`."""
        n = len(self._eigen)
        return tuple(self._eigen[(state + k) % n] for k in range(3))

    def glyph(self, state: int) -> str:
        return _oct.GLYPHS[state % len(_oct.GLYPHS)]

    def scale_position(self, state: int, layer: int) -> Tuple[float, float, float]:
        x, y, z = self.position(state)
        scale = PHI ** (-layer)
        return (x * scale, y * scale, z * scale)

    # -- internals ----------------------------------------------------------

    @staticmethod
    def _fibonacci_eigenvalues(depth: int) -> List[float]:
        """lambda_i = phi^i / sum_k phi^k — the root engine's spectrum."""
        raw = [PHI ** i for i in range(max(depth, 3))]
        total = sum(raw)
        return [v / total for v in raw]


# ---------------------------------------------------------------------------
# Geometry 2: the full O_h group as a 48-state geometry
# ---------------------------------------------------------------------------

class CayleyGeometry:
    """
    The 48-element octahedral group O_h as a stack ``Geometry``.

    This is the widest shape the root repo actually owns. Where
    ``RootOctahedralGeometry`` has 8 states (one per cell value), this has one
    state per *symmetry operation*, with the Cayley graph as its transition
    structure — the same metric ``geometric_state_algebra.CayleyEnergy`` and
    ``mandala_hook.SymmetryMandalaConfig`` already relax against.

    * ``transitions(g)`` — the elements one generator step from ``g``
    * ``transition_cost`` — Cayley graph distance (always 1 for neighbours,
      scaled by ``PHI`` when the move changes parity, since an inversion is a
      structurally larger move than a rotation)
    * ``position(g)`` — where ``g`` sends a reference vertex, in R^3
    * ``eigenvalues(g)`` — (det, trace, order) signature, normalised

    Requires ``geometric_state_algebra`` from the repo root (stdlib only).
    """

    def __init__(self, reference_vertex: Tuple[int, int, int] = (1, 0, 0),
                 parity_weight: float = PHI, group=None):
        from geometric_state_algebra import OhGroup  # root repo, lazy

        self.group = group if group is not None else OhGroup()
        self.reference_vertex = reference_vertex
        self.parity_weight = parity_weight
        self._neighbors: Dict[int, List[int]] = {}

    @property
    def name(self) -> str:
        return "cayley-oh"

    @property
    def n_states(self) -> int:
        return len(self.group.elements)

    @property
    def dimension(self) -> int:
        return 3

    def position(self, state: int) -> Tuple[float, float, float]:
        """Image of the reference vertex under element `state`, plus a
        parity offset so proper and improper elements are separated."""
        g = self.group.elements[state]
        x, y, z = g.act_on_vertex(self.reference_vertex)
        parity = 0.0 if g.is_proper() else 1.0
        return (float(x), float(y), float(z) + parity * 0.5)

    def transitions(self, state: int) -> List[int]:
        cached = self._neighbors.get(state)
        if cached is not None:
            return cached
        g = self.group.elements[state]
        found = set()
        for gen in self.group.generators:
            for h in (g.compose(gen), g.compose(gen.inverse())):
                idx = self.group.index(h)
                if idx != state:
                    found.add(idx)
        result = sorted(found)
        self._neighbors[state] = result
        return result

    def transition_cost(self, a: int, b: int) -> float:
        if b not in self.transitions(a):
            return float("inf")
        ga, gb = self.group.elements[a], self.group.elements[b]
        cost = float(self.group.distance(a, b))
        if ga.is_proper() != gb.is_proper():
            cost *= self.parity_weight
        return cost

    def eigenvalues(self, state: int) -> Tuple[float, float, float]:
        g = self.group.elements[state]
        det = float(g.determinant())            # +-1
        trace = g.trace() / 3.0                 # in [-1, 1]
        order = g.order() / 6.0                 # max order in O_h is 6
        return (det, trace, order)

    def glyph(self, state: int) -> str:
        """Reuse the 8 root glyphs, subscripted by conjugacy parity."""
        g = self.group.elements[state]
        base = _oct.GLYPHS[state % len(_oct.GLYPHS)]
        return base if g.is_proper() else base.lower() if base.isalpha() else base + "̄"

    def scale_position(self, state: int, layer: int) -> Tuple[float, float, float]:
        x, y, z = self.position(state)
        scale = PHI ** (-layer)
        return (x * scale, y * scale, z * scale)


# ---------------------------------------------------------------------------
# Registry wiring
# ---------------------------------------------------------------------------

def register_bridge_geometries() -> List[str]:
    """
    Add the root-backed geometries to the stack's geometry registry so
    ``get_geometry("octahedral-root")`` and ``list_geometries()`` see them.

    Returns the names that were registered. Idempotent.
    """
    GEOMETRIES["octahedral-root"] = RootOctahedralGeometry
    GEOMETRIES["octahedral-root-wide"] = lambda: RootOctahedralGeometry(ring_width=2)
    GEOMETRIES["cayley-oh"] = CayleyGeometry
    return ["octahedral-root", "octahedral-root-wide", "cayley-oh"]


# ---------------------------------------------------------------------------
# Moving states between the two engines
# ---------------------------------------------------------------------------

def states_from_computer(mc) -> List[int]:
    """Read the cell states out of a root ``MandalaComputer``."""
    return [cell.state for cell in mc.cells]


def apply_states(mc, states: Sequence[int]) -> None:
    """
    Write states back into a root ``MandalaComputer``.

    Keeps the engine's SIMD mirror in sync when one is present, so the next
    ``compute_total_energy()`` sees the new configuration.
    """
    if len(states) != len(mc.cells):
        raise ValueError(
            f"state count {len(states)} does not match {len(mc.cells)} cells"
        )
    n = mc.sacred_geometry
    for cell, state in zip(mc.cells, states):
        cell.state = int(state) % n
    sync = getattr(mc, "_sync_states_to_array", None)
    if callable(sync):
        sync()


def geometric_relax(mc, geometry=None, steps: int = 500,
                    T_start: float = 2.0, T_end: float = 0.01,
                    seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Anneal a live ``MandalaComputer`` using the stack's geometry.

    Moves are proposed by ``geometry.transitions()`` — so the shape decides
    what a legal step is — while the accept/reject test scores with the root
    engine's own ``compute_total_energy()``. Neither half is simulated: the
    geometry is the stack's, the physics is the repo's.

    This mirrors ``geometric_state_algebra.GeometricMandalaAdapter.geometric_relax``,
    which does the same thing with Cayley moves and Cayley energy.

    Args:
        mc: an encoded ``MandalaComputer`` (call an ``encode_*`` method first)
        geometry: any stack Geometry with at least ``mc.sacred_geometry``
            states. Defaults to ``RootOctahedralGeometry``.
        steps: number of proposals
        T_start, T_end: geometric cooling schedule
        seed: RNG seed for reproducibility

    Returns:
        dict with ``initial_energy``, ``final_energy``, ``best_energy``,
        ``best_states``, ``energy_history``, ``accepted``, ``geometry``.
    """
    import random

    if geometry is None:
        geometry = RootOctahedralGeometry(
            coupling_strength=getattr(mc, "coupling_strength", 1.0),
            depth=getattr(mc, "golden_depth", 5),
            num_states=mc.sacred_geometry,
        )
    if geometry.n_states < mc.sacred_geometry:
        raise ValueError(
            f"geometry {geometry.name} has {geometry.n_states} states, "
            f"computer needs {mc.sacred_geometry}"
        )
    if not mc.cells:
        raise ValueError("computer has no cells — call bloom_mandala()/encode_*() first")

    rng = random.Random(seed)
    energy = mc.compute_total_energy()
    initial_energy = energy
    best_energy = energy
    best_states = states_from_computer(mc)
    history = [energy]
    accepted = 0

    for step in range(steps):
        frac = step / max(steps - 1, 1)
        T = max(T_start * (T_end / T_start) ** frac, 1e-15)

        idx = rng.randrange(len(mc.cells))
        cell = mc.cells[idx]
        old_state = cell.state

        candidates = [s for s in geometry.transitions(old_state)
                      if s < mc.sacred_geometry]
        if not candidates:
            history.append(energy)
            continue
        cell.state = rng.choice(candidates)

        sync = getattr(mc, "_sync_states_to_array", None)
        if callable(sync):
            sync()
        new_energy = mc.compute_total_energy()
        dE = new_energy - energy

        if dE < 0 or rng.random() < math.exp(-dE / T):
            energy = new_energy
            accepted += 1
            if energy < best_energy:
                best_energy = energy
                best_states = states_from_computer(mc)
        else:
            cell.state = old_state
            if callable(sync):
                sync()

        history.append(energy)

    apply_states(mc, best_states)
    return {
        "initial_energy": initial_energy,
        "final_energy": energy,
        "best_energy": best_energy,
        "best_states": best_states,
        "energy_history": history,
        "accepted": accepted,
        "acceptance_rate": accepted / max(steps, 1),
        "geometry": geometry.name,
        "steps": steps,
    }


# ---------------------------------------------------------------------------
# Stack states -> root arithmetic
# ---------------------------------------------------------------------------

def states_to_glyphs(states: Sequence[int]) -> str:
    """Render stack states with the root repo's octahedral glyph alphabet."""
    n = len(_oct.GLYPHS)
    return "".join(_oct.GLYPHS[int(s) % n] for s in states)


def states_to_number(states: Sequence[int], offset: int = 2):
    """
    Read stack states as an exact base-8 ``OctahedralNumber``.

    Thin pass-through to ``octahedral_arithmetic.states_to_number`` so stack
    results can enter glyph-space arithmetic without conversion to decimal.
    """
    return _oct.states_to_number(list(int(s) for s in states), offset=offset)


# ---------------------------------------------------------------------------
# Root physics -> learned geometry
# ---------------------------------------------------------------------------

def learn_root_geometry(num_states: int = 8, method: str = "force_directed",
                        dim: int = 3, coupling_strength: float = 1.0,
                        seed: Optional[int] = 42, register_as: Optional[str] = None):
    """
    Learn a manifold from the root engine's coupling law.

    The root repo *asserts* that its 8 states are octahedral. This hands the
    coupling metric — and nothing else — to the stack's ``GeometryLearner``
    and asks what shape the metric actually implies. It is the stack's own
    falsification move (README: "arbitrary geometries fail, learned
    geometries succeed") turned on the repo that hosts it.

    Args:
        num_states: size of the state space to embed
        method: ``force_directed`` | ``classical_mds`` | ``spectral`` | ``isomap``
        dim: embedding dimension
        coupling_strength: J in the sin^2 law
        seed: RNG seed
        register_as: if given, register the result under this name in the
            stack geometry registry

    Returns:
        a ``LearnedGeometry`` over the integer states ``0..num_states-1``.
    """
    from geometry_learner import GeometryLearner

    items = list(range(num_states))

    def distance_fn(a: int, b: int) -> float:
        return root_coupling_energy(a, b, coupling_strength, num_states)

    learner = GeometryLearner(method=method, dim=dim, seed=seed)
    geo = learner.learn(items, distance_fn)
    if register_as:
        register_learned_geometry(register_as, geo)
    return geo


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _self_test() -> None:
    print("=" * 64)
    print("STACK BRIDGE — root engine <-> geometry-agnostic stack")
    print("=" * 64)

    names = register_bridge_geometries()
    print(f"\nRegistered bridge geometries: {names}")

    # 1. Root octahedron through the stack protocol
    print("\n--- 1. RootOctahedralGeometry (root physics, stack protocol) ---")
    geo = RootOctahedralGeometry()
    print(f"  name={geo.name} states={geo.n_states} dim={geo.dimension}")
    print(f"  glyphs: {''.join(geo.glyph(s) for s in range(geo.n_states))}")
    print(f"  transitions(0) = {geo.transitions(0)}")
    print(f"  cost(0->1) = {geo.transition_cost(0, 1):.6f}  "
          f"(sin^2 law, expected {math.sin(math.pi / 4) ** 2:.6f})")
    print(f"  eigenvalues(0) = {tuple(round(v, 4) for v in geo.eigenvalues(0))}")

    solver = MandalaSolver(geometry=geo, seed=7)
    result = solver.anneal("factorization", {"N": 143}, steps=200)
    print(f"  stack anneal on root geometry: state={result.best_state} "
          f"E={result.best_energy:.4f}")

    # 2. The O_h group as a 48-state geometry
    print("\n--- 2. CayleyGeometry (48-element O_h group) ---")
    cayley = CayleyGeometry()
    print(f"  name={cayley.name} states={cayley.n_states} dim={cayley.dimension}")
    print(f"  transitions(0) = {cayley.transitions(0)}")
    print(f"  cost(0->{cayley.transitions(0)[0]}) = "
          f"{cayley.transition_cost(0, cayley.transitions(0)[0]):.4f}")
    identity = cayley.group.index(cayley.group.identity())
    bloom = MandalaSolver(geometry=cayley, seed=7).bloom(center_state=identity,
                                                         expansion_layers=3)
    print(f"  bloom from identity (element {identity}): "
          f"{[layer['n_states'] for layer in bloom.layers]} states per shell "
          f"({bloom.total_cells} cells)")

    # 3. Annealing a real MandalaComputer with stack moves
    print("\n--- 3. geometric_relax on a live MandalaComputer ---")
    try:
        from mandala_computer import MandalaComputer

        mc = MandalaComputer(golden_depth=3, temperature=1.0)
        mc.encode_factorization(143)
        out = geometric_relax(mc, steps=400, seed=7)
        print(f"  geometry: {out['geometry']}")
        print(f"  energy {out['initial_energy']:.4f} -> {out['best_energy']:.4f} "
              f"(accepted {out['acceptance_rate']:.0%})")
        print(f"  glyphs: {states_to_glyphs(out['best_states'][:12])}")
        print(f"  as OctahedralNumber: "
              f"{states_to_number(out['best_states'][:4]).to_glyphs()}")
    except Exception as exc:  # numpy missing, atlas unreadable, ...
        print(f"  skipped: {exc}")

    # 4. Learn the shape the root metric implies
    print("\n--- 4. learn_root_geometry (what shape is the coupling law?) ---")
    try:
        learned = learn_root_geometry(register_as="learned-root-coupling")
        print(f"  learned: {learned.name}, {learned.n_states} states, "
              f"dim={learned.dimension}")
        print(f"  position(0) = "
              f"{tuple(round(v, 3) for v in learned.position(0))}")
        print(f"  transitions(0) = {learned.transitions(0)}")
        print("  note: the root repo asserts octahedral structure; this is "
              "what its metric alone implies.")
    except Exception as exc:  # numpy missing
        print(f"  skipped: {exc}")

    print("\n" + "=" * 64)
    print("Bridge self-test complete.")
    print("=" * 64)


if __name__ == "__main__":
    _self_test()
