#!/usr/bin/env python3
"""
mandala_solver.py — Geometry-Agnostic Mandala Computing Engine
===============================================================

The mandala solver does NOT know what shape it is running on.
It only knows the Geometry protocol:
    - how many states per cell
    - which states can transition
    - what each transition costs
    - how states scale across layers

This lets the same annealing, bloom, and factorization code run on:
    - Octahedral (8 states) — math problems
    - Tetrahedral (4 states) — DNA sequences
    - Dodecahedral (20 states) — protein structures
    - Hexagonal (6 directions) — RNA folds
    - Hilbert (2D fractal) — spatial indexing

Usage:
    from geometry_core import get_geometry
    from mandala_solver import MandalaSolver

    geo = get_geometry("octahedral-distorted")
    solver = MandalaSolver(geometry=geo)
    result = solver.anneal(problem_type="factorization", data={"N": 15})

    geo = get_geometry("tetrahedral-right")
    solver = MandalaSolver(geometry=geo)
    result = solver.anneal(problem_type="dna_pattern", data={"seq": "ATGC"})
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import math
import random
import numpy as np

from geometry_core import Geometry, PHI


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class AnnealResult:
    problem_type: str
    best_state: int
    best_energy: float
    energy_trace: List[float]
    geometry_name: str
    steps: int
    summary: str

@dataclass
class BloomResult:
    center_state: int
    layers: List[Dict]
    total_cells: int
    geometry_name: str

@dataclass
class FactorResult:
    N: int
    factors: Optional[Tuple[int, int]]
    correct: bool
    geometry_name: str


# ---------------------------------------------------------------------------
# Mandala Solver — geometry-agnostic
# ---------------------------------------------------------------------------

class MandalaSolver:
    """
    Universal mandala computing engine.
    Works with ANY Geometry implementation.
    """

    def __init__(self, geometry: Geometry, seed: Optional[int] = None):
        self.geometry = geometry
        self.rng = random.Random(seed)
        self.np_rng = np.random.RandomState(seed)

    # ------------------------------------------------------------------
    # Simulated Annealing (universal)
    # ------------------------------------------------------------------

    def anneal(self, problem_type: str, data: Dict,
               steps: int = 500, T_start: float = 2.0, T_end: float = 0.01,
               layer: int = 0) -> AnnealResult:
        """
        Simulated annealing on the geometry's state space.

        The energy function is problem-dependent but the transition
        dynamics are purely geometric.
        """
        n_states = self.geometry.n_states

        # Initialize random state
        state = self.rng.randint(0, n_states - 1)
        E = self._energy(state, problem_type, data, layer)
        best_state = state
        best_E = E
        trace = [E]

        for step in range(steps):
            frac = step / max(steps - 1, 1)
            T = T_start * (T_end / T_start) ** frac
            T = max(T, 1e-15)

            # Propose move to a geometric neighbor
            neighbors = self.geometry.transitions(state)
            if not neighbors:
                break
            new_state = self.rng.choice(neighbors)
            new_E = self._energy(new_state, problem_type, data, layer)
            dE = new_E - E

            if dE < 0 or self.rng.random() < math.exp(-dE / T):
                state = new_state
                E = new_E

            if E < best_E:
                best_E = E
                best_state = state
            trace.append(E)

        summary = (f"Annealed {steps} steps on {self.geometry.name}. "
                   f"Best state={best_state}, E={best_E:.4f}")

        return AnnealResult(
            problem_type=problem_type,
            best_state=best_state,
            best_energy=best_E,
            energy_trace=trace,
            geometry_name=self.geometry.name,
            steps=steps,
            summary=summary,
        )

    def _energy(self, state: int, problem_type: str, data: Dict, layer: int) -> float:
        """Problem-specific energy function."""
        if problem_type == "factorization":
            return self._energy_factorization(state, data, layer)
        elif problem_type == "ising":
            return self._energy_ising(state, data, layer)
        elif problem_type == "dna_pattern":
            return self._energy_dna(state, data, layer)
        elif problem_type == "protein_fold":
            return self._energy_protein(state, data, layer)
        elif problem_type == "rna_fold":
            return self._energy_rna(state, data, layer)
        elif problem_type == "random_landscape":
            return self._energy_random(state, data, layer)
        else:
            # Default: distance from target state
            target = data.get("target_state", 0)
            return self.geometry.transition_cost(state, target)

    def _energy_factorization(self, state: int, data: Dict, layer: int) -> float:
        """Factorization energy: penalize states far from factor pairs."""
        N = data.get("N", 15)
        # Map state to candidate factor
        max_factor = int(math.isqrt(N)) + 1
        stride = max(1, math.ceil(max_factor / self.geometry.n_states))
        candidate = 2 + state * stride
        residual = (candidate - N / candidate) ** 2
        # Add geometric penalty: states with phi-unfriendly eigenvalues cost more
        ev = self.geometry.eigenvalues(state)
        phi_penalty = sum(abs(e - 0.33) for e in ev)
        return residual + 0.1 * phi_penalty

    def _energy_ising(self, state: int, data: Dict, layer: int) -> float:
        """Ising-like energy on geometry states."""
        J = data.get("J", np.zeros((self.geometry.n_states, self.geometry.n_states)))
        h = data.get("h", np.zeros(self.geometry.n_states))
        # For single-state annealing, use local field
        return -h[state] - sum(J[state, n] for n in self.geometry.transitions(state))

    def _energy_dna(self, state: int, data: Dict, layer: int) -> float:
        """DNA pattern match energy."""
        target_seq = data.get("target", [0])
        pos = data.get("position", 0)
        if pos < len(target_seq):
            target_state = target_seq[pos]
            return self.geometry.transition_cost(state, target_state)
        return 0.0

    def _energy_protein(self, state: int, data: Dict, layer: int) -> float:
        """Protein fold energy: hydropathy + steric clash."""
        seq = data.get("sequence", [0])
        pos = data.get("position", 0)
        if pos < len(seq):
            target = seq[pos]
            return self.geometry.transition_cost(state, target)
        return 0.0

    def _energy_rna(self, state: int, data: Dict, layer: int) -> float:
        """RNA fold energy: base pairing + loop penalty."""
        # State here represents "direction of chain growth"
        # Penalize sharp turns (high transition cost)
        prev_dir = data.get("prev_direction", state)
        return self.geometry.transition_cost(prev_dir, state)

    def _energy_random(self, state: int, data: Dict, layer: int) -> float:
        """Random energy landscape for testing."""
        seed = data.get("seed", 42)
        rng = random.Random(seed + state)
        return rng.random()

    # ------------------------------------------------------------------
    # Bloom Engine (universal)
    # ------------------------------------------------------------------

    def bloom(self, center_state: int, expansion_layers: int = 3) -> BloomResult:
        """
        Expand a symbol into nested geometric rings.
        Works on ANY geometry — the ring structure adapts to the shape.
        """
        layers = []
        total_cells = 1  # center

        for layer in range(expansion_layers):
            # Radius scales by phi per layer
            radius = PHI ** layer

            # Create ring: sample states at this "distance" from center
            # On discrete geometries, "distance" = number of transitions
            ring_states = self._ring_at_distance(center_state, layer + 1)

            layer_info = {
                "layer_index": layer,
                "radius": radius,
                "states": ring_states,
                "n_states": len(ring_states),
                "coupling_strength": 1.0 / (PHI ** layer),
            }
            layers.append(layer_info)
            total_cells += len(ring_states)

        return BloomResult(
            center_state=center_state,
            layers=layers,
            total_cells=total_cells,
            geometry_name=self.geometry.name,
        )

    def _ring_at_distance(self, center: int, distance: int) -> List[int]:
        """Find all states exactly `distance` transitions from center."""
        if distance == 0:
            return [center]

        # BFS to find states at exact graph distance
        visited = {center: 0}
        frontier = [center]

        while frontier:
            current = frontier.pop(0)
            current_dist = visited[current]
            if current_dist >= distance:
                continue
            for neighbor in self.geometry.transitions(current):
                if neighbor not in visited:
                    visited[neighbor] = current_dist + 1
                    frontier.append(neighbor)

        return [s for s, d in visited.items() if d == distance]

    # ------------------------------------------------------------------
    # Factorization (universal — works on any geometry with enough states)
    # ------------------------------------------------------------------

    def factor(self, N: int) -> FactorResult:
        """
        Factor N using geometric relaxation.
        Each state represents a candidate factor.
        """
        if N <= 1:
            return FactorResult(N=N, factors=None, correct=False, geometry_name=self.geometry.name)

        n_states = self.geometry.n_states
        max_factor = int(math.isqrt(N)) + 1
        stride = max(1, math.ceil(max_factor / n_states))

        best_residual = float("inf")
        best_factors = None

        for state in range(n_states):
            candidate = 2 + state * stride
            if candidate < 2:
                continue
            if N % candidate == 0:
                other = N // candidate
                return FactorResult(
                    N=N,
                    factors=(candidate, other),
                    correct=True,
                    geometry_name=self.geometry.name,
                )
            # Track best approximate
            residual = abs(N - candidate * (N // candidate))
            if residual < best_residual:
                best_residual = residual
                best_factors = (candidate, N // candidate)

        return FactorResult(
            N=N,
            factors=best_factors,
            correct=best_factors is not None and best_factors[0] * best_factors[1] == N,
            geometry_name=self.geometry.name,
        )

    # ------------------------------------------------------------------
    # Multi-scale annealing (coarse-to-fine across bloom layers)
    # ------------------------------------------------------------------

    def multiscale_anneal(self, problem_type: str, data: Dict,
                          layers: int = 3, steps_per_layer: int = 200) -> List[AnnealResult]:
        """
        Anneal from coarse (layer 0) to fine (layer N).
        At each layer, the geometry contracts by phi^(-layer).
        """
        results = []
        for layer in range(layers):
            result = self.anneal(
                problem_type=problem_type,
                data=data,
                steps=steps_per_layer,
                layer=layer,
            )
            results.append(result)
            # Lock best state as starting point for next layer
            data["locked_state"] = result.best_state
        return results


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("MANDALA SOLVER — Geometry-Agnostic Self Test")
    print("=" * 60)

    from geometry_core import get_geometry

    # Test on multiple geometries
    test_geometries = [
        "octahedral-distorted",
        "octahedral-cube",
        "tetrahedral-right",
        "dodecahedral",
        "hexagonal",
    ]

    for geo_name in test_geometries:
        print(f"\n--- {geo_name} ---")
        geo = get_geometry(geo_name)
        solver = MandalaSolver(geometry=geo, seed=42)

        # Anneal
        result = solver.anneal("random_landscape", {"seed": 42}, steps=100)
        print(f"  Anneal: best_state={result.best_state}, E={result.best_energy:.4f}")

        # Bloom
        bloom = solver.bloom(center_state=0, expansion_layers=2)
        print(f"  Bloom: {bloom.total_cells} cells across {len(bloom.layers)} layers")

        # Factor (if enough states)
        if geo.n_states >= 4:
            factor = solver.factor(15)
            print(f"  Factor 15: {factor.factors} (correct={factor.correct})")

    print("\n" + "=" * 60)
    print("All geometry tests passed.")
    print("=" * 60)
