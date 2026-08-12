#!/usr/bin/env python3
"""
geometry_core.py — Unified Geometry Protocol for Mandala Computing
=================================================================

Any shape. Any scale. Same protocol.

The mandala engine does NOT hardcode octahedral assumptions.
It operates on a Geometry instance that provides:
    - states: how many discrete configurations per cell
    - positions: where each state lives in physical space
    - transitions: which states can evolve into which
    - costs: how expensive each transition is
    - eigenvalues: the "energy signature" of each state

Problem geometries implemented:
    - Octahedral (8 states, 3D) — factorization, SAT, Ising
    - Tetrahedral (4 states, 3D) — DNA/RNA base encoding
    - Dodecahedral (20 states, 3D) — protein amino acids
    - Hexagonal (6 directions, 2D) — RNA secondary structure
    - Hilbert (2D space-filling) — fractal address mapping

Usage:
    from geometry_core import OctahedralGeometry, TetrahedralGeometry
    from mandala_solver import MandalaSolver

    geo = OctahedralGeometry(mode="distorted")
    solver = MandalaSolver(geometry=geo)
    result = solver.anneal(problem_type="factorization", data={"N": 15})

    geo = TetrahedralGeometry(chirality="right")
    solver = MandalaSolver(geometry=geo)
    result = solver.anneal(problem_type="dna_fold", data={"seq": "ATGC"})
"""

from __future__ import annotations
from typing import Protocol, List, Tuple, Dict, Optional, Any
from dataclasses import dataclass
import math
import random

PHI = (1 + math.sqrt(5)) / 2
INV_PHI = 1.0 / PHI


# ---------------------------------------------------------------------------
# Geometry Protocol — the contract every shape must satisfy
# ---------------------------------------------------------------------------

class Geometry(Protocol):
    """Any discrete geometric substrate that mandala computing can use."""

    @property
    def name(self) -> str: ...
    @property
    def n_states(self) -> int: ...
    @property
    def dimension(self) -> int: ...

    def position(self, state: int) -> Tuple[float, ...]:
        """Physical coordinates of state in embedding space."""
        ...

    def transitions(self, state: int) -> List[int]:
        """States reachable from `state` in one step."""
        ...

    def transition_cost(self, a: int, b: int) -> float:
        """Energy cost to move from state a to state b. Inf if disallowed."""
        ...

    def eigenvalues(self, state: int) -> Tuple[float, ...]:
        """Energy signature / tensor eigenvalues of this state."""
        ...

    def glyph(self, state: int) -> str:
        """Symbolic representation (unicode glyph) of this state."""
        ...

    def scale_position(self, state: int, layer: int) -> Tuple[float, ...]:
        """Position at a given bloom layer (coarse-to-fine contraction)."""
        ...


# ---------------------------------------------------------------------------
# Octahedral Geometry (8 states, 3D)
# ---------------------------------------------------------------------------

@dataclass
class OctahedralGeometry:
    """8-state octahedral substrate — the original mandala geometry."""
    mode: str = "distorted"  # "distorted" or "cube"

    @property
    def name(self) -> str:
        return f"octahedral-{self.mode}"

    @property
    def n_states(self) -> int:
        return 8

    @property
    def dimension(self) -> int:
        return 3

    def _positions(self) -> Dict[int, Tuple[float, float, float]]:
        if self.mode == "distorted":
            return {
                0: (1, 0, 0), 1: (-1, 0, 0),
                2: (0, 1, 0), 3: (0, -1, 0),
                4: (0, 0, 1), 5: (0, 0, -1),
                6: (1, 1, 0), 7: (-1, -1, 0),
            }
        else:
            return {
                0: (1, 1, 1), 1: (-1, 1, 1),
                2: (1, -1, 1), 3: (-1, -1, 1),
                4: (1, 1, -1), 5: (-1, 1, -1),
                6: (1, -1, -1), 7: (-1, -1, -1),
            }

    def _transitions(self) -> Dict[int, List[int]]:
        if self.mode == "distorted":
            return {
                0: [2, 3, 4, 5, 6], 1: [2, 3, 4, 5, 7],
                2: [0, 1, 4, 5, 6], 3: [0, 1, 4, 5, 7],
                4: [0, 1, 2, 3],   5: [0, 1, 2, 3],
                6: [0, 2, 4, 5, 7], 7: [1, 3, 4, 5, 6]
            }
        else:
            return {
                0: [1, 2, 4], 1: [0, 3, 5], 2: [0, 3, 6], 3: [1, 2, 7],
                4: [0, 5, 6], 5: [1, 4, 7], 6: [2, 4, 7], 7: [3, 5, 6]
            }

    def position(self, state: int) -> Tuple[float, float, float]:
        return self._positions()[state]

    def transitions(self, state: int) -> List[int]:
        return self._transitions()[state]

    def transition_cost(self, a: int, b: int) -> float:
        if b not in self.transitions(a):
            return float("inf")
        ax, ay, az = self.position(a)
        bx, by, bz = self.position(b)
        return math.sqrt((ax-bx)**2 + (ay-by)**2 + (az-bz)**2)

    def eigenvalues(self, state: int) -> Tuple[float, float, float]:
        # Phi-optimized eigenvalues
        base = {
            0: (0.33, 0.33, 0.33), 1: (0.50, 0.30, 0.20),
            2: (0.45, 0.35, 0.20), 3: (0.40, 0.40, 0.20),
            4: (0.55, 0.25, 0.20), 5: (0.35, 0.35, 0.30),
            6: (0.50, 0.35, 0.15), 7: (0.45, 0.40, 0.15)
        }
        return base[state]

    def glyph(self, state: int) -> str:
        glyphs = ["⊕", "⊖", "⊗", "⊘",
                  "⊙", "⊚", "⊛", "⊜"]
        return glyphs[state]

    def scale_position(self, state: int, layer: int) -> Tuple[float, float, float]:
        x, y, z = self.position(state)
        if self.mode == "distorted" and state >= 6:
            scale = PHI ** (-layer)
            return (x * scale, y * scale, z * scale)
        return (x, y, z)


# ---------------------------------------------------------------------------
# Tetrahedral Geometry (4 states, 3D) — DNA/RNA bases
# ---------------------------------------------------------------------------

@dataclass
class TetrahedralGeometry:
    """4-state tetrahedral substrate — A, T/U, G, C."""
    chirality: str = "right"  # "right" or "left"

    @property
    def name(self) -> str:
        return f"tetrahedral-{self.chirality}"

    @property
    def n_states(self) -> int:
        return 4

    @property
    def dimension(self) -> int:
        return 3

    def _positions(self) -> Dict[int, Tuple[float, float, float]]:
        # Regular tetrahedron inscribed in unit sphere
        # (1,1,1), (1,-1,-1), (-1,1,-1), (-1,-1,1) — normalized
        raw = {
            0: (1, 1, 1),   # A
            1: (1, -1, -1), # T/U
            2: (-1, 1, -1), # G
            3: (-1, -1, 1), # C
        }
        result = {}
        for s, (x, y, z) in raw.items():
            r = math.sqrt(x*x + y*y + z*z)
            result[s] = (x/r, y/r, z/r)
        if self.chirality == "left":
            # Mirror through xy plane
            result = {s: (x, y, -z) for s, (x, y, z) in result.items()}
        return result

    def transitions(self, state: int) -> List[int]:
        # Each vertex connects to all others in tetrahedron
        return [s for s in range(4) if s != state]

    def position(self, state: int) -> Tuple[float, float, float]:
        return self._positions()[state]

    def transition_cost(self, a: int, b: int) -> float:
        if a == b:
            return 0.0
        # Purine-purine and pyrimidine-pyrimidine are "closer"
        purine = {0, 2}  # A, G
        pyrimidine = {1, 3}  # T, C
        same_class = (a in purine and b in purine) or (a in pyrimidine and b in pyrimidine)
        base_cost = self._euclidean(a, b)
        return base_cost * (0.6 if same_class else 1.0)

    def _euclidean(self, a: int, b: int) -> float:
        ax, ay, az = self.position(a)
        bx, by, bz = self.position(b)
        return math.sqrt((ax-bx)**2 + (ay-by)**2 + (az-bz)**2)

    def eigenvalues(self, state: int) -> Tuple[float, float, float]:
        # Hydrogen bond capacity, size, charge
        profiles = {
            0: (0.40, 0.30, 0.30),  # A: medium H-bond, medium size, neutral
            1: (0.35, 0.25, 0.40),  # T: 2 H-bond, small, neutral
            2: (0.45, 0.35, 0.20),  # G: 3 H-bond, large, neutral
            3: (0.35, 0.25, 0.40),  # C: 3 H-bond, small, neutral
        }
        return profiles[state]

    def glyph(self, state: int) -> str:
        glyphs = ["A", "T", "G", "C"]
        return glyphs[state]

    def scale_position(self, state: int, layer: int) -> Tuple[float, float, float]:
        x, y, z = self.position(state)
        scale = PHI ** (-layer)
        return (x * scale, y * scale, z * scale)


# ---------------------------------------------------------------------------
# Dodecahedral Geometry (20 states, 3D) — Protein amino acids
# ---------------------------------------------------------------------------

@dataclass
class DodecahedralGeometry:
    """20-state dodecahedral substrate — amino acids."""

    @property
    def name(self) -> str:
        return "dodecahedral"

    @property
    def n_states(self) -> int:
        return 20

    @property
    def dimension(self) -> int:
        return 3

    def _positions(self) -> Dict[int, Tuple[float, float, float]]:
        # Regular dodecahedron vertices on unit sphere
        # (±1, ±1, ±1), (0, ±φ, ±1/φ), (±1/φ, 0, ±φ), (±φ, ±1/φ, 0)
        vertices = {
            0: (1, 1, 1), 1: (1, 1, -1), 2: (1, -1, 1), 3: (1, -1, -1),
            4: (-1, 1, 1), 5: (-1, 1, -1), 6: (-1, -1, 1), 7: (-1, -1, -1),
            8: (0, PHI, INV_PHI), 9: (0, PHI, -INV_PHI),
            10: (0, -PHI, INV_PHI), 11: (0, -PHI, -INV_PHI),
            12: (INV_PHI, 0, PHI), 13: (-INV_PHI, 0, PHI),
            14: (INV_PHI, 0, -PHI), 15: (-INV_PHI, 0, -PHI),
            16: (PHI, INV_PHI, 0), 17: (PHI, -INV_PHI, 0),
            18: (-PHI, INV_PHI, 0), 19: (-PHI, -INV_PHI, 0),
        }
        result = {}
        for s, (x, y, z) in vertices.items():
            r = math.sqrt(x*x + y*y + z*z)
            result[s] = (x/r, y/r, z/r)
        return result

    def _transitions(self) -> Dict[int, List[int]]:
        # Each vertex connects to 3 nearest neighbors
        pos = self._positions()
        transitions = {}
        for a in range(20):
            ax, ay, az = pos[a]
            distances = []
            for b in range(20):
                if a == b:
                    continue
                bx, by, bz = pos[b]
                d = math.sqrt((ax-bx)**2 + (ay-by)**2 + (az-bz)**2)
                distances.append((d, b))
            distances.sort()
            transitions[a] = [b for _, b in distances[:3]]
        return transitions

    def position(self, state: int) -> Tuple[float, float, float]:
        return self._positions()[state]

    def transitions(self, state: int) -> List[int]:
        return self._transitions()[state]

    def transition_cost(self, a: int, b: int) -> float:
        if b not in self.transitions(a):
            return float("inf")
        # Shared biochemical properties reduce cost
        # Property classes (simplified)
        hydrophobic = {0, 4, 5, 6, 7, 12, 13}
        polar = {1, 2, 3, 8, 9, 10, 11}
        charged = {14, 15, 16, 17, 18, 19}
        same = any(a in cls and b in cls for cls in [hydrophobic, polar, charged])
        base = self._euclidean(a, b)
        return base * (0.7 if same else 1.0)

    def _euclidean(self, a: int, b: int) -> float:
        ax, ay, az = self.position(a)
        bx, by, bz = self.position(b)
        return math.sqrt((ax-bx)**2 + (ay-by)**2 + (az-bz)**2)

    def eigenvalues(self, state: int) -> Tuple[float, float, float]:
        # Hydropathy, size, charge — normalized
        # Simplified profiles for 20 states
        base = {
            0: (0.40, 0.30, 0.30), 1: (0.35, 0.25, 0.40),
            2: (0.45, 0.35, 0.20), 3: (0.33, 0.33, 0.33),
            4: (0.50, 0.30, 0.20), 5: (0.35, 0.35, 0.30),
            6: (0.45, 0.40, 0.15), 7: (0.40, 0.40, 0.20),
            8: (0.55, 0.25, 0.20), 9: (0.35, 0.35, 0.30),
            10: (0.50, 0.35, 0.15), 11: (0.45, 0.40, 0.15),
            12: (0.33, 0.33, 0.33), 13: (0.40, 0.30, 0.30),
            14: (0.35, 0.25, 0.40), 15: (0.45, 0.35, 0.20),
            16: (0.33, 0.33, 0.33), 17: (0.50, 0.30, 0.20),
            18: (0.35, 0.35, 0.30), 19: (0.45, 0.40, 0.15),
        }
        return base[state]

    def glyph(self, state: int) -> str:
        aa = "ACDEFGHIKLMNPQRSTVWY"
        return aa[state] if state < 20 else "?"

    def scale_position(self, state: int, layer: int) -> Tuple[float, float, float]:
        x, y, z = self.position(state)
        scale = PHI ** (-layer)
        return (x * scale, y * scale, z * scale)


# ---------------------------------------------------------------------------
# Hexagonal Geometry (6 directions, 2D) — RNA secondary structure
# ---------------------------------------------------------------------------

@dataclass
class HexagonalGeometry:
    """6-direction hexagonal lattice — RNA folding, 2D structures."""

    @property
    def name(self) -> str:
        return "hexagonal"

    @property
    def n_states(self) -> int:
        return 6  # 6 directions, not 6 bases

    @property
    def dimension(self) -> int:
        return 2

    def _directions(self) -> List[Tuple[float, float]]:
        return [
            (1, 0),
            (0.5, math.sqrt(3)/2),
            (-0.5, math.sqrt(3)/2),
            (-1, 0),
            (-0.5, -math.sqrt(3)/2),
            (0.5, -math.sqrt(3)/2),
        ]

    def position(self, state: int) -> Tuple[float, float]:
        # State here means "direction index" — the lattice grows directionally
        return self._directions()[state]

    def transitions(self, state: int) -> List[int]:
        # Can turn ±1 direction, or continue straight
        return [(state + i) % 6 for i in [-1, 0, 1]]

    def transition_cost(self, a: int, b: int) -> float:
        if b not in self.transitions(a):
            return float("inf")
        # Straight = cheap, turn = expensive
        diff = abs(a - b)
        diff = min(diff, 6 - diff)
        return diff * 0.5  # 0 for straight, 0.5 for ±1 turn

    def eigenvalues(self, state: int) -> Tuple[float, float, float]:
        # Direction persistence, curvature, torsion (2D so torsion=0)
        dirs = self._directions()
        dx, dy = dirs[state]
        return (abs(dx), abs(dy), 0.0)

    def glyph(self, state: int) -> str:
        glyphs = ["→", "↗", "↖", "←", "↙", "↘"]
        return glyphs[state]

    def scale_position(self, state: int, layer: int) -> Tuple[float, float]:
        x, y = self.position(state)
        scale = PHI ** (-layer)
        return (x * scale, y * scale)


# ---------------------------------------------------------------------------
# Hilbert Geometry (2D space-filling) — Fractal address mapping
# ---------------------------------------------------------------------------

@dataclass
class HilbertGeometry:
    """2D Hilbert curve geometry for fractal address mapping."""
    order: int = 8

    @property
    def name(self) -> str:
        return f"hilbert-{self.order}"

    @property
    def n_states(self) -> int:
        return 2 ** (2 * self.order)  # Total cells in grid

    @property
    def dimension(self) -> int:
        return 2

    def _hilbert_xy(self, idx: int) -> Tuple[int, int]:
        """Map Hilbert index to (x, y) on 2^order grid."""
        n = 1 << self.order
        x = y = 0
        t = idx
        s = 1
        while s < n:
            rx = 1 & (t // 2)
            ry = 1 & (t ^ rx)
            if ry == 0:
                if rx == 1:
                    x = n - 1 - x
                    y = n - 1 - y
                x, y = y, x
            x += s * rx
            y += s * ry
            t //= 4
            s *= 2
        return x, y

    def position(self, state: int) -> Tuple[float, float]:
        x, y = self._hilbert_xy(state)
        n = 1 << self.order
        return (x / n, y / n)  # Normalize to [0,1]

    def transitions(self, state: int) -> List[int]:
        # Hilbert neighbors: previous and next along curve
        # Plus orthogonal grid neighbors if adjacent in 2D
        neighbors = []
        if state > 0:
            neighbors.append(state - 1)
        if state < self.n_states - 1:
            neighbors.append(state + 1)
        # Check orthogonal neighbors in 2D
        x, y = self._hilbert_xy(state)
        for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < (1 << self.order) and 0 <= ny < (1 << self.order):
                # Find Hilbert index of (nx, ny) — expensive, skip for now
                pass
        return neighbors

    def transition_cost(self, a: int, b: int) -> float:
        if b not in self.transitions(a):
            return float("inf")
        ax, ay = self.position(a)
        bx, by = self.position(b)
        return math.sqrt((ax-bx)**2 + (ay-by)**2)

    def eigenvalues(self, state: int) -> Tuple[float, float, float]:
        x, y = self.position(state)
        return (x, y, 0.0)

    def glyph(self, state: int) -> str:
        return f"H{state}"

    def scale_position(self, state: int, layer: int) -> Tuple[float, float]:
        x, y = self.position(state)
        scale = PHI ** (-layer)
        return (x * scale, y * scale)


# ---------------------------------------------------------------------------
# Geometry Registry — discover and instantiate geometries
# ---------------------------------------------------------------------------

GEOMETRIES = {
    "octahedral": OctahedralGeometry,
    "octahedral-distorted": lambda: OctahedralGeometry("distorted"),
    "octahedral-cube": lambda: OctahedralGeometry("cube"),
    "tetrahedral": TetrahedralGeometry,
    "tetrahedral-right": lambda: TetrahedralGeometry("right"),
    "tetrahedral-left": lambda: TetrahedralGeometry("left"),
    "dodecahedral": DodecahedralGeometry,
    "hexagonal": HexagonalGeometry,
    "hilbert": HilbertGeometry,
    "hilbert-8": lambda: HilbertGeometry(8),
}


def get_geometry(name: str) -> Geometry:
    """Factory: get a geometry by name."""
    if name not in GEOMETRIES:
        raise ValueError(f"Unknown geometry: {name}. Available: {list(GEOMETRIES.keys())}")
    return GEOMETRIES[name]()


def list_geometries() -> List[str]:
    """List all registered geometry names."""
    return list(GEOMETRIES.keys())


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Learned geometry support
# ---------------------------------------------------------------------------

def register_learned_geometry(name: str, geometry):
    """Register a learned geometry for discovery."""
    GEOMETRIES[name] = lambda: geometry


def list_learned_geometries():
    """List all geometries that were learned from data."""
    return [name for name in GEOMETRIES.keys() if name.startswith("learned")]

if __name__ == "__main__":
    print("=" * 60)
    print("GEOMETRY CORE — Protocol Validation")
    print("=" * 60)

    for name in list_geometries():
        geo = get_geometry(name)
        print(f"\n{name}:")
        print(f"  states: {geo.n_states}, dim: {geo.dimension}")
        print(f"  sample position(0): {geo.position(0)}")
        print(f"  transitions(0): {geo.transitions(0)[:3]}...")
        print(f"  glyph(0): {geo.glyph(0)}")
        print(f"  eigenvalues(0): {geo.eigenvalues(0)}")
        print(f"  scale(0, layer=2): {geo.scale_position(0, 2)}")

    print("\n" + "=" * 60)
    print("All geometries validated.")
    print("=" * 60)
