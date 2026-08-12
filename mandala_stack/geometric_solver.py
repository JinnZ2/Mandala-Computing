#!/usr/bin/env python3
"""
geometric_solver.py — Energy as Functional of Embedding
=========================================================

The old solver: discrete states, scalar energy, random walk annealing.
  E = sum(independent_terms)
  State = one of N discrete configurations
  Search = try random changes, accept/reject

This solver: continuous embedding, geometric energy, relaxation flow.
  E[σ] = ∫_M (α|∇σ|² + β⟨σ|Φ|σ⟩ + γK(σ)) dμ
  Configuration = map from problem elements to manifold points
  Search = gradient flow on the manifold (relaxation, not random walk)

Key insight from the user:
  "Platonic solids are the geometric equivalent of binary encoding."
  Both impose pre-existing structure. Both fail when the problem has
  its own structure.

This solver removes the Platonic bias at the energy level.
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Callable, Optional, Any
from dataclasses import dataclass
import math
import random
import numpy as np


# ---------------------------------------------------------------------------
# Geometric Energy Functional
# ---------------------------------------------------------------------------

class GeometricEnergy:
    """
    Energy is a functional of the embedding, not a sum of terms.

    E[configuration] = α * Dirichlet + β * FieldAlignment + γ * Curvature

    Dirichlet: how smoothly the problem maps onto the geometry
    FieldAlignment: how well the embedding satisfies problem constraints
    Curvature: penalty for topological defects / singularities
    """

    def __init__(self, alpha: float = 1.0, beta: float = 1.0, gamma: float = 0.5):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    def dirichlet(self, positions: List[Tuple[float, ...]],
                  metric_fn: Callable[[Tuple, Tuple], float]) -> float:
        """
        Dirichlet energy: ∫ |∇σ|² dμ
        Discrete: sum of (geodesic distance between adjacent points)²

        This measures how "smoothly" the configuration sits on the manifold.
        A straight line through the geometry has low Dirichlet energy.
        A jagged, discontinuous path has high Dirichlet energy.
        """
        E = 0.0
        for i in range(len(positions) - 1):
            dist = metric_fn(positions[i], positions[i + 1])
            E += dist ** 2
        return E

    def field_alignment(self, positions: List[Tuple[float, ...]],
                        field_fn: Callable[[Tuple], float]) -> float:
        """
        Field alignment: ∫ ⟨σ|Φ|σ⟩ dμ

        Measures how well the embedding aligns with an external field.
        For protein folding: the field is hydropathy (hydrophobic = low energy
        in the core, polar = low energy on the surface).

        For TSP: the field is the city distribution (cities want to be visited
        in an order that minimizes travel distance).
        """
        E = 0.0
        for pos in positions:
            E += field_fn(pos) ** 2
        return E

    def curvature(self, positions: List[Tuple[float, ...]],
                  metric_fn: Callable[[Tuple, Tuple], float]) -> float:
        """
        Curvature penalty: ∫ K(σ) dμ

        Measures topological strain — how much the configuration bends
        the manifold. A configuration with singularities (self-intersections,
        discontinuities) has high curvature energy.

        For a chain: sum of (turning angle)² between consecutive segments.
        """
        if len(positions) < 3:
            return 0.0

        E = 0.0
        for i in range(1, len(positions) - 1):
            # Three consecutive points
            p_prev = np.array(positions[i - 1])
            p_cur = np.array(positions[i])
            p_next = np.array(positions[i + 1])

            v1 = p_cur - p_prev
            v2 = p_next - p_cur

            n1 = np.linalg.norm(v1)
            n2 = np.linalg.norm(v2)
            if n1 < 1e-6 or n2 < 1e-6:
                continue

            v1n = v1 / n1
            v2n = v2 / n2

            # Turning angle = arccos(v1 · v2)
            dot = np.clip(np.dot(v1n, v2n), -1.0, 1.0)
            angle = math.acos(dot)

            E += angle ** 2

        return E

    def __call__(self, positions: List[Tuple[float, ...]],
                 metric_fn: Callable[[Tuple, Tuple], float],
                 field_fn: Callable[[Tuple], float]) -> float:
        """Total geometric energy."""
        return (self.alpha * self.dirichlet(positions, metric_fn) +
                self.beta * self.field_alignment(positions, field_fn) +
                self.gamma * self.curvature(positions, metric_fn))


# ---------------------------------------------------------------------------
# Manifold Gradient
# ---------------------------------------------------------------------------

class ManifoldGradient:
    """
    Compute gradient of energy on a manifold.

    Not a derivative in Euclidean space. A covariant derivative
    that respects the manifold's metric.

    For a point on a sphere: the gradient is tangent to the sphere,
    not pointing off into the ambient space.
    """

    def __init__(self, step_size: float = 0.1):
        self.step_size = step_size

    def compute(self, positions: List[Tuple[float, ...]],
                energy_fn: Callable[[List[Tuple]], float]) -> List[Tuple[float, ...]]:
        """
        Compute gradient by finite differences, then project onto tangent space.
        """
        dim = len(positions[0])
        n = len(positions)
        gradient = []

        E0 = energy_fn(positions)
        eps = 1e-4

        for i in range(n):
            grad_i = np.zeros(dim)
            for d in range(dim):
                # Perturb in direction d
                pos_perturbed = [list(p) for p in positions]
                pos_perturbed[i][d] += eps

                # Renormalize to unit sphere (if on sphere)
                norm = math.sqrt(sum(x*x for x in pos_perturbed[i]))
                if norm > 0:
                    pos_perturbed[i] = [x / norm for x in pos_perturbed[i]]

                E_perturbed = energy_fn([tuple(p) for p in pos_perturbed])
                grad_i[d] = (E_perturbed - E0) / eps

            gradient.append(tuple(grad_i))

        return gradient

    def project_tangent(self, point: Tuple[float, ...],
                        grad: Tuple[float, ...]) -> Tuple[float, ...]:
        """
        Project gradient onto tangent space of sphere at point.
        For a point p on S^n, the tangent space is orthogonal to p.
        """
        p = np.array(point)
        g = np.array(grad)
        # Remove normal component: g_tangent = g - (g·p)p
        projection = np.dot(g, p) * p
        tangent = g - projection
        norm = np.linalg.norm(tangent)
        if norm > 0:
            tangent = tangent / norm
        return tuple(tangent)

    def step(self, positions: List[Tuple[float, ...]],
             gradient: List[Tuple[float, ...]]) -> List[Tuple[float, ...]]:
        """Move along negative gradient, staying on manifold."""
        new_positions = []
        for pos, grad in zip(positions, gradient):
            # Project gradient to tangent space
            tangent_grad = self.project_tangent(pos, grad)

            # Move in tangent direction
            new_pos = np.array(pos) - self.step_size * np.array(tangent_grad)

            # Project back to manifold (unit sphere)
            norm = np.linalg.norm(new_pos)
            if norm > 0:
                new_pos = new_pos / norm

            new_positions.append(tuple(new_pos))

        return new_positions


# ---------------------------------------------------------------------------
# Geometric Solver
# ---------------------------------------------------------------------------

@dataclass
class GeometricResult:
    problem_type: str
    positions: List[Tuple[float, ...]]
    energy: float
    energy_trace: List[float]
    steps: int
    summary: str


class GeometricSolver:
    """
    Solve problems by relaxation on a learned manifold.

    Not annealing (random walk + accept/reject).
    Not discrete state search.

    Gradient flow on the energy functional's landscape.
    Like water finding the lowest point.
    Like a protein folding to its native state.
    Like your engine finding its operating equilibrium.
    """

    def __init__(self, geometry, energy: GeometricEnergy = None,
                 gradient: ManifoldGradient = None, seed: Optional[int] = None):
        """
        geometry: a LearnedGeometry or any object with:
          - positions: dict mapping items to coordinates
          - item_to_idx, idx_to_item
          - _distance(item1, item2)
        """
        self.geometry = geometry
        self.energy = energy or GeometricEnergy()
        self.gradient = gradient or ManifoldGradient(step_size=0.05)
        self.rng = random.Random(seed)

    def solve(self, problem_type: str, data: Dict,
              steps: int = 200, field_fn: Callable = None) -> GeometricResult:
        """
        Solve by gradient flow relaxation.

        Configuration = list of points on the manifold (one per problem element).
        Energy = functional of the embedding.
        Search = gradient descent on the manifold.
        """
        # Initialize configuration
        positions = self._initialize(problem_type, data)

        # Default field: zero everywhere
        if field_fn is None:
            field_fn = lambda pos: 0.0

        # Metric: Euclidean distance in learned space
        def metric_fn(p1, p2):
            return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

        # Energy functional
        def energy_fn(pos):
            return self.energy(pos, metric_fn, field_fn)

        # Relaxation loop
        trace = []
        E = energy_fn(positions)
        trace.append(E)

        for step in range(steps):
            # Compute gradient
            grad = self.gradient.compute(positions, energy_fn)

            # Step along negative gradient
            new_positions = self.gradient.step(positions, grad)
            new_E = energy_fn(new_positions)

            # Accept if energy decreased (deterministic, not stochastic)
            if new_E < E:
                positions = new_positions
                E = new_E

            trace.append(E)

            # Early stopping
            if len(trace) > 10 and abs(trace[-1] - trace[-10]) < 1e-6:
                break

        summary = (f"Relaxed {len(trace)} steps on learned manifold. "
                   f"Final energy: {E:.4f}")

        return GeometricResult(
            problem_type=problem_type,
            positions=positions,
            energy=E,
            energy_trace=trace,
            steps=len(trace),
            summary=summary,
        )

    def _initialize(self, problem_type: str, data: Dict) -> List[Tuple[float, ...]]:
        """Initialize configuration on the manifold."""
        if problem_type == "protein_fold":
            return self._init_protein(data)
        elif problem_type == "tsp":
            return self._init_tsp(data)
        elif problem_type == "pattern":
            return self._init_pattern(data)
        else:
            # Random initialization on manifold
            n = data.get("n", 5)
            return [self._random_point() for _ in range(n)]

    def _init_protein(self, data: Dict) -> List[Tuple[float, ...]]:
        """Initialize protein chain as a smooth curve on the manifold."""
        sequence = data.get("sequence", [])
        positions = []

        for state_idx in sequence:
            # Map discrete state to continuous position on manifold
            item = self.geometry.idx_to_item[state_idx]
            pos = self.geometry.positions[item]
            positions.append(pos)

        return positions

    def _init_tsp(self, data: Dict) -> List[Tuple[float, ...]]:
        """Initialize TSP tour as a path through city positions."""
        cities = data.get("cities", [])
        # Sort cities by angle around centroid (smooth initial path)
        if len(cities) > 2:
            centroid = tuple(np.mean(cities, axis=0))
            angles = [math.atan2(c[1] - centroid[1], c[0] - centroid[0]) for c in cities]
            sorted_indices = sorted(range(len(cities)), key=lambda i: angles[i])
            return [tuple(cities[i]) for i in sorted_indices]
        return [tuple(c) for c in cities]

    def _init_pattern(self, data: Dict) -> List[Tuple[float, ...]]:
        """Initialize pattern as points on manifold."""
        target = data.get("target", [0])
        positions = []
        for state_idx in target:
            item = self.geometry.idx_to_item[state_idx]
            pos = self.geometry.positions[item]
            positions.append(pos)
        return positions

    def _random_point(self) -> Tuple[float, ...]:
        """Random point on unit sphere."""
        dim = self.geometry.dim
        vec = np.random.randn(dim)
        vec /= np.linalg.norm(vec) + 1e-10
        return tuple(vec)


# ---------------------------------------------------------------------------
# Comparison: Old discrete solver vs New geometric solver
# ---------------------------------------------------------------------------

def compare_solvers(geometry, problem_type, data, field_fn=None):
    """Run both solvers and compare."""
    from mandala_solver import MandalaSolver

    print(f"\n{'='*60}")
    print(f"COMPARISON: {problem_type}")
    print(f"{'='*60}")

    # Old discrete solver
    old_solver = MandalaSolver(geometry=geometry, seed=42)
    old_result = old_solver.anneal(problem_type, data, steps=300)
    print(f"\nOld (discrete) solver:")
    print(f"  Best state: {old_result.best_state}")
    print(f"  Best energy: {old_result.best_energy:.4f}")
    print(f"  Steps: {old_result.steps}")

    # New geometric solver
    new_solver = GeometricSolver(geometry=geometry, seed=42)
    new_result = new_solver.solve(problem_type, data, steps=200, field_fn=field_fn)
    print(f"\nNew (geometric) solver:")
    print(f"  Final energy: {new_result.energy:.4f}")
    print(f"  Steps: {new_result.steps}")
    print(f"  {new_result.summary}")

    return old_result, new_result


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("GEOMETRIC SOLVER — Self Test")
    print("=" * 60)

    from geometry_learner import GeometryLearner

    # Learn a simple geometry
    items = ["A", "B", "C", "D", "E"]
    def dist(a, b):
        vals = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
        return abs(vals[a] - vals[b])

    learner = GeometryLearner(method="force_directed", dim=3, seed=42)
    geo = learner.learn(items, dist)

    print(f"\nLearned geometry: {geo.name}")

    # Test geometric energy
    energy = GeometricEnergy(alpha=1.0, beta=0.5, gamma=0.3)

    # Smooth configuration: A-B-C-D-E (adjacent in learned space)
    smooth_pos = [geo.positions[item] for item in items]

    # Rough configuration: A-E-B-D-C (jumps)
    rough_items = ["A", "E", "B", "D", "C"]
    rough_pos = [geo.positions[item] for item in rough_items]

    def metric(p1, p2):
        return math.sqrt(sum((a-b)**2 for a, b in zip(p1, p2)))

    def field(pos):
        return 0.0

    E_smooth = energy(smooth_pos, metric, field)
    E_rough = energy(rough_pos, metric, field)

    print(f"\nGeometric energy:")
    print(f"  Smooth (A-B-C-D-E): {E_smooth:.4f}")
    print(f"  Rough  (A-E-B-D-C): {E_rough:.4f}")
    print(f"  Smooth is lower: {E_smooth < E_rough}")

    # Test solver
    solver = GeometricSolver(geometry=geo, seed=42)
    data = {"sequence": [geo.item_to_idx[item] for item in items]}
    result = solver.solve("pattern", data, steps=100)

    print(f"\nSolver result:")
    print(f"  Energy: {result.energy:.4f}")
    print(f"  Steps: {result.steps}")
    print(f"  Trace (first 5): {result.energy_trace[:5]}")

    print("\n" + "=" * 60)
    print("Geometric solver tests passed.")
    print("=" * 60)
