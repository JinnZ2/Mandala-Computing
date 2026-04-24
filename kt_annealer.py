"""
KOSTERLITZ-THOULESS ANNEALER v1.0
Phase-based optimization via topological defect dynamics.

Ported from Geometric-to-Binary-Computational-Bridge/Engine and adapted
for the Mandala Computing framework.

The KT annealer operates on continuous phase degrees of freedom using
XY-model energy.  Below the KT transition temperature, vortex-antivortex
pairs bind and the system orders — the physics finds the solution.

This module provides:

  KTConfig          — annealing parameters (J, temperatures, schedule)
  AnnealStep        — snapshot of state at one temperature
  KTAnnealer        — core XY-model annealer with vortex detection
  SymmetryDetector  — reflective / rotational symmetry finder for 3-D sources
  kt_anneal_mandala — bridge: run KT annealing on a MandalaComputer

Key insight: octahedral states 0-7 map to phases s*pi/4 on the unit circle.
The KT annealer optimises in continuous phase space then quantises back to
the nearest octahedral state, giving access to vortex dynamics and phase
coherence that discrete Metropolis cannot see.
"""

from __future__ import annotations

import math
import numpy as np
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from octahedral_arithmetic import PHI


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class KTConfig:
    """Parameters for the KT annealer."""
    J: float = PHI
    T_start: float = 4.0
    T_final: float = 0.4
    n_steps: int = 1000
    n_sweeps_per_step: int = 1
    max_delta: float = math.pi
    seed: Optional[int] = None

    @property
    def T_KT(self) -> float:
        """Kosterlitz-Thouless critical temperature: T_KT = pi*J / 2."""
        return math.pi * self.J / 2.0


# ---------------------------------------------------------------------------
# Anneal step snapshot
# ---------------------------------------------------------------------------

@dataclass
class AnnealStep:
    """Snapshot of the annealer state at one temperature."""
    step: int
    temperature: float
    energy: float
    phase_coherence: float
    vortex_count: int
    acceptance_rate: float


# ---------------------------------------------------------------------------
# KT Annealer
# ---------------------------------------------------------------------------

class KTAnnealer:
    """
    Kosterlitz-Thouless annealer for phase optimisation on a lattice.

    Operates on continuous phase variables (0..2*pi) with XY-model energy:
        E = -J * sum_{<i,j>} cos(theta_i - theta_j)

    Below T_KT, vortex-antivortex pairs bind and the system orders.
    """

    def __init__(self, phases: np.ndarray, adjacency: List[List[int]],
                 config: Optional[KTConfig] = None) -> None:
        self.phases = phases.copy().astype(float) % (2 * math.pi)
        self.adj = adjacency
        self.cfg = config or KTConfig()
        self._rng = np.random.default_rng(self.cfg.seed)
        self.history: List[AnnealStep] = []

    def _edge_energy(self, phases: np.ndarray) -> float:
        """Total XY-model energy: E = -J sum cos(theta_i - theta_j)."""
        J = self.cfg.J
        total = 0.0
        seen: set = set()
        for i, neighbors in enumerate(self.adj):
            for j in neighbors:
                edge = (min(i, j), max(i, j))
                if edge not in seen:
                    seen.add(edge)
                    total -= J * math.cos(phases[i] - phases[j])
        return total

    def _node_delta_energy(self, i: int, old_phase: float,
                           new_phase: float) -> float:
        J = self.cfg.J
        dE = 0.0
        for j in self.adj[i]:
            dE += J * math.cos(old_phase - self.phases[j])
            dE -= J * math.cos(new_phase - self.phases[j])
        return dE

    def _phase_coherence(self, phases: np.ndarray) -> float:
        """Order parameter |<e^{i*theta}>| in [0, 1]."""
        if len(phases) == 0:
            return 0.0
        return float(abs(np.mean(np.exp(1j * phases))))

    def _count_vortices(self, phases: np.ndarray) -> int:
        """Count topological defects on triangular plaquettes."""
        count = 0
        n = len(phases)
        for i in range(n):
            nbrs_i = set(self.adj[i])
            for j in self.adj[i]:
                if j <= i:
                    continue
                for k in self.adj[j]:
                    if k <= j or k not in nbrs_i:
                        continue
                    w = ((phases[j] - phases[i])
                         + (phases[k] - phases[j])
                         + (phases[i] - phases[k]))
                    w = (w + math.pi) % (2 * math.pi) - math.pi
                    if abs(w) > 0.5 * math.pi:
                        count += 1
        return count

    def _metropolis_sweep(self, T: float) -> float:
        T_KT = self.cfg.T_KT
        max_delta = self.cfg.max_delta * min(1.0, T / T_KT)
        accepted = 0
        n = len(self.phases)
        for i in self._rng.permutation(n):
            old = self.phases[i]
            delta = self._rng.uniform(-max_delta, max_delta)
            new = (old + delta) % (2 * math.pi)
            dE = self._node_delta_energy(i, old, new)
            if dE <= 0.0 or self._rng.random() < math.exp(-dE / max(T, 1e-12)):
                self.phases[i] = new
                accepted += 1
        return accepted / max(1, n)

    def anneal(self) -> np.ndarray:
        """Run KT annealing from T_start -> T_final (exponential cooling)."""
        cfg = self.cfg
        T = cfg.T_start
        N = max(1, cfg.n_steps - 1)
        ratio = (cfg.T_final / cfg.T_start) ** (1.0 / N)

        for step in range(cfg.n_steps):
            accept_rate = 0.0
            for _ in range(cfg.n_sweeps_per_step):
                accept_rate = self._metropolis_sweep(T)
            self.history.append(AnnealStep(
                step=step, temperature=T,
                energy=self._edge_energy(self.phases),
                phase_coherence=self._phase_coherence(self.phases),
                vortex_count=self._count_vortices(self.phases),
                acceptance_rate=accept_rate,
            ))
            T *= ratio
        return self.phases.copy()

    def final_coherence(self) -> float:
        return self._phase_coherence(self.phases)

    def final_vortex_count(self) -> int:
        return self._count_vortices(self.phases)

    def kt_transition_step(self) -> Optional[int]:
        """Step with largest single-step drop in vortex count."""
        if len(self.history) < 4:
            return None
        counts = [s.vortex_count for s in self.history]
        drops = [counts[i] - counts[i + 1] for i in range(len(counts) - 1)]
        if not drops or max(drops) <= 0:
            return None
        return drops.index(max(drops))

    def summary(self) -> Dict[str, Any]:
        if not self.history:
            return {}
        start, end = self.history[0], self.history[-1]
        kt_step = self.kt_transition_step()
        return {
            "T_KT": self.cfg.T_KT,
            "T_start": start.temperature,
            "T_final": end.temperature,
            "n_steps": len(self.history),
            "energy_start": start.energy,
            "energy_final": end.energy,
            "energy_improvement": start.energy - end.energy,
            "coherence_start": start.phase_coherence,
            "coherence_final": end.phase_coherence,
            "vortices_start": start.vortex_count,
            "vortices_final": end.vortex_count,
            "kt_transition_step": kt_step,
            "kt_transition_T": (self.history[kt_step].temperature
                                if kt_step is not None else None),
        }


# ---------------------------------------------------------------------------
# Symmetry Detector
# ---------------------------------------------------------------------------

class SymmetryDetector:
    """
    Detect exploitable symmetries in 3-D source configurations.

    Finds reflective (mirror) and rotational (n-fold) symmetries that
    can reduce redundant field or energy calculations.
    """

    def __init__(self, position_tol: float = 1e-4,
                 magnitude_tol: float = 1e-4) -> None:
        self.position_tol = position_tol
        self.magnitude_tol = magnitude_tol

    def find_symmetries(self, positions: np.ndarray,
                        strengths: Optional[np.ndarray] = None) -> List[Dict]:
        """
        Detect symmetries in a set of 3-D positions.

        Returns list of symmetry dicts with 'type', 'axis'/'plane',
        and 'reduction_factor'.
        """
        if len(positions) < 2:
            return []

        positions = np.asarray(positions, dtype=float)
        if strengths is None:
            strengths = np.ones(len(positions))
        else:
            strengths = np.asarray(strengths, dtype=float)

        centroid = np.mean(positions, axis=0)
        symmetries: List[Dict] = []

        for axis_idx, axis_name in enumerate(("x", "y", "z")):
            if self._check_reflection(positions, strengths, centroid, axis_idx):
                symmetries.append({
                    "type": "reflective", "plane": axis_name,
                    "center": centroid.tolist(), "reduction_factor": 2.0,
                })

        for axis_idx, axis_name in enumerate(("x", "y", "z")):
            axis_vec = np.zeros(3)
            axis_vec[axis_idx] = 1.0
            for n_fold in (2, 3, 4, 6):
                if self._check_rotation(positions, strengths, centroid,
                                        axis_vec, n_fold):
                    symmetries.append({
                        "type": "rotational", "axis": axis_name,
                        "center": centroid.tolist(), "n_fold": n_fold,
                        "reduction_factor": float(n_fold),
                    })
                    break
        return symmetries

    def reduction_factor(self, symmetries: List[Dict]) -> float:
        if not symmetries:
            return 1.0
        return max(s["reduction_factor"] for s in symmetries)

    def _check_reflection(self, positions, strengths, center, axis_idx):
        reflected = positions.copy()
        reflected[:, axis_idx] = 2 * center[axis_idx] - reflected[:, axis_idx]
        return self._configs_match(positions, strengths, reflected, strengths)

    def _check_rotation(self, positions, strengths, center, axis, n_fold):
        angle = 2 * np.pi / n_fold
        rotated = self._rotate(positions - center, axis, angle) + center
        return self._configs_match(positions, strengths, rotated, strengths)

    @staticmethod
    def _rotate(points, axis, angle):
        axis = axis / np.linalg.norm(axis)
        c, s = np.cos(angle), np.sin(angle)
        K = np.array([[0, -axis[2], axis[1]],
                      [axis[2], 0, -axis[0]],
                      [-axis[1], axis[0], 0]])
        R = np.eye(3) + s * K + (1 - c) * (K @ K)
        return (R @ points.T).T

    def _configs_match(self, pos_a, str_a, pos_b, str_b):
        n = len(pos_a)
        if n != len(pos_b):
            return False
        matched = [False] * n
        for i in range(n):
            for j in range(n):
                if matched[j]:
                    continue
                dist = np.linalg.norm(pos_a[i] - pos_b[j])
                mag_max = max(abs(str_a[i]), abs(str_b[j]), 1e-30)
                if (dist < self.position_tol
                        and abs(str_a[i] - str_b[j]) / mag_max < self.magnitude_tol):
                    matched[j] = True
                    break
            else:
                return False
        return True


# ---------------------------------------------------------------------------
# Mandala bridge: octahedral states <-> continuous phases
# ---------------------------------------------------------------------------

OCTAHEDRAL_PHASE_STEP = math.pi / 4  # 8 states -> 8 phase sectors


def states_to_phases(states: List[int]) -> np.ndarray:
    """Map octahedral states (0-7) to phases (0..2*pi)."""
    return np.array([s * OCTAHEDRAL_PHASE_STEP for s in states])


def phases_to_states(phases: np.ndarray, num_states: int = 8) -> List[int]:
    """Quantise continuous phases back to nearest octahedral state."""
    step = 2 * math.pi / num_states
    return [int(round(p / step)) % num_states for p in phases]


def mandala_adjacency(cells) -> List[List[int]]:
    """Extract adjacency list from MandalaComputer cells."""
    return [list(c.neighbors) for c in cells]


def kt_anneal_mandala(mc, config: Optional[KTConfig] = None) -> Dict:
    """
    Run KT annealing on a MandalaComputer's current configuration.

    Maps cell states to continuous phases, anneals with XY-model energy
    and vortex dynamics, then quantises back to octahedral states.

    Args:
        mc: a MandalaComputer instance (must have bloomed cells)
        config: KTConfig (defaults to phi-lattice settings)

    Returns:
        dict with ground_state, final_energy, coherence, vortices, summary
    """
    if not mc.cells:
        raise ValueError("MandalaComputer has no cells — call bloom_mandala() first")

    states = [c.state for c in mc.cells]
    phases = states_to_phases(states)
    adj = mandala_adjacency(mc.cells)

    cfg = config or KTConfig(
        J=PHI, T_start=4.0, T_final=0.3,
        n_steps=500, seed=None,
    )

    annealer = KTAnnealer(phases, adj, cfg)
    optimised = annealer.anneal()

    new_states = phases_to_states(optimised, mc.sacred_geometry)
    for i, c in enumerate(mc.cells):
        c.state = new_states[i]

    final_energy = mc.compute_total_energy()
    mc.ground_state = new_states
    mc.solution = mc._extract_solution()

    return {
        "ground_state": new_states,
        "final_energy": final_energy,
        "coherence": annealer.final_coherence(),
        "vortices_final": annealer.final_vortex_count(),
        "solution": mc.solution,
        "summary": annealer.summary(),
        "history": annealer.history,
    }


def detect_mandala_symmetries(mc) -> List[Dict]:
    """
    Detect spatial symmetries in a MandalaComputer's cell layout.

    Returns list of symmetry dicts (reflective, rotational).
    """
    if not mc.cells:
        return []
    positions = np.array([list(c.position) + [0.0] if len(c.position) == 2
                          else list(c.position) for c in mc.cells])
    if positions.shape[1] == 2:
        positions = np.column_stack([positions, np.zeros(len(positions))])
    detector = SymmetryDetector()
    return detector.find_symmetries(positions)


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def anneal_network_phases(phases: np.ndarray, adjacency: List[List[int]],
                          config: Optional[KTConfig] = None,
                          ) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Anneal phase array and return (optimised_phases, summary_dict)."""
    annealer = KTAnnealer(phases, adjacency, config)
    optimised = annealer.anneal()
    return optimised, annealer.summary()


# ---------------------------------------------------------------------------
# Demos
# ---------------------------------------------------------------------------

def demo_kt_annealing():
    """Demonstrate KT annealing on a 4x4 torus lattice."""
    print("=" * 60)
    print("KT Annealer Demo — phi-lattice (J = phi)")
    print(f"  T_KT = pi*phi/2 = {math.pi * PHI / 2:.4f}")
    print("=" * 60)

    rng = np.random.default_rng(42)
    N = 16
    adj: List[List[int]] = []
    for row in range(4):
        for col in range(4):
            adj.append([
                row * 4 + (col + 1) % 4,
                row * 4 + (col - 1) % 4,
                ((row + 1) % 4) * 4 + col,
                ((row - 1) % 4) * 4 + col,
            ])

    phases_init = rng.uniform(0, 2 * math.pi, N)
    cfg = KTConfig(J=PHI, T_start=5.0, T_final=0.3, n_steps=500, seed=42)
    ann = KTAnnealer(phases_init.copy(), adj, cfg)
    ann.anneal()

    s = ann.summary()
    print(f"\n  Energy:    {s['energy_start']:+.3f} -> {s['energy_final']:+.3f}"
          f"  (delta={s['energy_improvement']:+.3f})")
    print(f"  Coherence: {s['coherence_start']:.3f} -> {s['coherence_final']:.3f}")
    print(f"  Vortices:  {s['vortices_start']} -> {s['vortices_final']}")
    if s["kt_transition_step"] is not None:
        print(f"  KT step:   {s['kt_transition_step']}  "
              f"(T = {s['kt_transition_T']:.3f}, T_KT = {s['T_KT']:.3f})")
    print()


def demo_symmetry_detection():
    """Demonstrate symmetry detection on geometric configurations."""
    print("=" * 60)
    print("Symmetry Detector Demo")
    print("=" * 60)

    detector = SymmetryDetector()

    # Cube vertices — should have full octahedral symmetry
    cube = np.array([
        [1, 1, 1], [1, 1, -1], [1, -1, 1], [1, -1, -1],
        [-1, 1, 1], [-1, 1, -1], [-1, -1, 1], [-1, -1, -1],
    ], dtype=float)
    syms = detector.find_symmetries(cube)
    print(f"\n  Cube vertices: {len(syms)} symmetries found")
    for sym in syms:
        print(f"    {sym['type']:12s}  {sym.get('plane', sym.get('axis', ''))}"
              f"  reduction={sym['reduction_factor']:.0f}x")

    # Random points — should have no symmetries
    rng = np.random.default_rng(99)
    random_pts = rng.standard_normal((6, 3))
    syms2 = detector.find_symmetries(random_pts)
    print(f"\n  Random points: {len(syms2)} symmetries (expected 0)")
    print()


def demo_mandala_bridge():
    """Demonstrate KT annealing on a MandalaComputer."""
    print("=" * 60)
    print("KT Annealer — Mandala Bridge Demo")
    print("=" * 60)
    try:
        from mandala_computer import MandalaComputer
    except ImportError:
        print("  mandala_computer not available")
        return

    mc = MandalaComputer(golden_depth=3, sacred_geometry=8, temperature=1.0)
    mc.bloom_mandala()
    mc.encode_factorization(15)

    # Standard annealing for comparison
    import copy
    mc_copy = copy.deepcopy(mc)
    r_std = mc_copy.simulated_annealing(max_steps=2000, T_start=3.0, T_end=0.01)

    # KT annealing
    cfg = KTConfig(J=PHI, T_start=4.0, T_final=0.3, n_steps=500, seed=42)
    r_kt = kt_anneal_mandala(mc, config=cfg)

    print(f"\n  Standard annealing: E={r_std['final_energy']:.4f}")
    print(f"  KT annealing:      E={r_kt['final_energy']:.4f}  "
          f"coherence={r_kt['coherence']:.3f}  "
          f"vortices={r_kt['vortices_final']}")

    syms = detect_mandala_symmetries(mc)
    print(f"  Cell symmetries:   {len(syms)} found")
    print()


if __name__ == "__main__":
    demo_kt_annealing()
    demo_symmetry_detection()
    demo_mandala_bridge()
    print("=" * 60)
    print("Vortices bind. Phases lock. Geometry solves.")
    print("=" * 60)
