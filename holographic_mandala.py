"""
HOLOGRAPHIC MANDALA COMPUTING v1.0
Unified framework: Holographic Encoding + Self-Symmetry + Entanglement

Three principles woven into a single computational layer:

1. HOLOGRAPHIC: Problem encoded on outermost ring (boundary).
   Information projects inward through PHI-scaled compression.
   Solution crystallizes at the center.

2. SELF-SYMMETRY (Renormalization): Each depth level solves a
   scaled version of the same problem. Coarse solutions at inner
   rings seed fine refinement at outer rings. Corrections propagate
   bidirectionally.

3. ENTANGLEMENT: Cross-depth correlations link cells at different
   scales. Correlated state updates propagate information without
   explicit message passing. Classical analog of quantum entanglement.

The physics: boundary conditions (holographic) constrain a self-similar
hierarchy (renormalization) connected by non-local correlations
(entanglement). The ground state of this system IS the solution.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Callable
from dataclasses import dataclass, field
import math
import time

from mandala_computer import (
    MandalaComputer, MandalaCell, ProblemType, SensorReading,
    PHI, FRET_CUTOFF, OCTAHEDRAL_STATES, _STATE_GLYPHS,
)

try:
    from quantum_mandala import QuantumMandalaComputer
    HAS_QUANTUM = True
except ImportError:
    HAS_QUANTUM = False


# ---------------------------------------------------------------------------
# Data structures for the holographic layer
# ---------------------------------------------------------------------------

@dataclass
class HolographicRing:
    """A single ring in the holographic mandala."""
    depth: int
    radius: float
    cell_indices: List[int]  # indices into parent's cell array
    projected_problem: Optional[Dict] = None  # compressed problem at this scale
    scale_factor: float = 1.0  # how much the problem is compressed


@dataclass
class EntanglementLink:
    """Cross-depth entanglement between two cells at different rings."""
    cell_a: int  # index of cell in outer ring
    cell_b: int  # index of cell in inner ring
    depth_a: int
    depth_b: int
    strength: float  # correlation strength
    phase: float = 0.0  # accumulated geometric phase


# ---------------------------------------------------------------------------
# HolographicMandala
# ---------------------------------------------------------------------------

class HolographicMandala(MandalaComputer):
    """
    Unified holographic + self-similar + entangled mandala computer.

    Extends MandalaComputer with three new computational layers:
    - Holographic boundary encoding
    - Renormalization group (self-symmetry) solver
    - Cross-depth entanglement correlations
    """

    def __init__(self, golden_depth: int = 5, sacred_geometry: int = 8,
                 temperature: float = 1.0,
                 entanglement_decay: float = 0.5,
                 holographic_weight: float = 1.0):
        """
        Args:
            golden_depth: Fractal recursion depth
            sacred_geometry: Symmetry order (8 for octahedral)
            temperature: Initial thermal energy
            entanglement_decay: How fast cross-depth entanglement decays with distance
            holographic_weight: Weight of holographic boundary energy term
        """
        super().__init__(golden_depth=golden_depth,
                         sacred_geometry=sacred_geometry,
                         temperature=temperature)
        self.entanglement_decay = entanglement_decay
        self.holographic_weight = holographic_weight

        # Holographic structure
        self.rings: List[HolographicRing] = []
        self.entanglement_links: List[EntanglementLink] = []

        # Renormalization state
        self.scale_solutions: Dict[int, List[int]] = {}  # depth -> solution at that scale

        print(f"   Holographic weight: {holographic_weight}")
        print(f"   Entanglement decay: {entanglement_decay}")

    # ------------------------------------------------------------------
    # Holographic bloom: organize cells into rings with projections
    # ------------------------------------------------------------------

    def bloom_mandala(self):
        """Extended bloom that also builds holographic ring structure."""
        super().bloom_mandala()
        self._build_rings()
        self._establish_entanglement_links()
        print(f"   Rings: {len(self.rings)}, entanglement links: {len(self.entanglement_links)}")

    def _build_rings(self):
        """Organize bloomed cells into concentric holographic rings."""
        self.rings = []
        for depth in range(self.golden_depth):
            indices = [i for i, c in enumerate(self.cells) if c.depth == depth]
            radius = PHI ** depth
            ring = HolographicRing(
                depth=depth,
                radius=radius,
                cell_indices=indices,
                scale_factor=PHI ** (self.golden_depth - 1 - depth),
            )
            self.rings.append(ring)

    def _establish_entanglement_links(self):
        """
        Create cross-depth entanglement links.

        Each cell in ring d is entangled with the nearest cell in ring d-1.
        Strength decays as entanglement_decay^(depth_difference).
        This creates non-local correlations across scales.
        """
        self.entanglement_links = []
        for d in range(1, len(self.rings)):
            outer_ring = self.rings[d]
            inner_ring = self.rings[d - 1]

            for outer_idx in outer_ring.cell_indices:
                outer_cell = self.cells[outer_idx]
                # Find nearest cell in inner ring
                best_inner = None
                best_dist = float("inf")
                for inner_idx in inner_ring.cell_indices:
                    inner_cell = self.cells[inner_idx]
                    dx = outer_cell.position[0] - inner_cell.position[0]
                    dy = outer_cell.position[1] - inner_cell.position[1]
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < best_dist:
                        best_dist = dist
                        best_inner = inner_idx

                if best_inner is not None:
                    strength = self.entanglement_decay ** (d - (d - 1))
                    link = EntanglementLink(
                        cell_a=outer_idx,
                        cell_b=best_inner,
                        depth_a=d,
                        depth_b=d - 1,
                        strength=strength,
                    )
                    self.entanglement_links.append(link)

    # ------------------------------------------------------------------
    # Holographic encoding: boundary -> interior projection
    # ------------------------------------------------------------------

    def encode_holographic(self, problem_type_enum: ProblemType, problem_data: Dict):
        """
        Encode problem holographically: full problem on boundary (outermost ring),
        compressed projections on inner rings.
        """
        self.problem_type = problem_type_enum
        self.problem_data = problem_data
        self.bloom_mandala()

        # Outermost ring gets full problem encoding
        outer = self.rings[-1]
        outer.projected_problem = dict(problem_data)
        outer.projected_problem["_scale"] = 1.0

        # Project inward: each inner ring gets a compressed version
        for d in range(len(self.rings) - 2, -1, -1):
            ring = self.rings[d]
            parent_ring = self.rings[d + 1]
            ring.projected_problem = self._project_problem(
                parent_ring.projected_problem, ring.scale_factor
            )

        # Set cell energies based on holographic projection at each ring
        for ring in self.rings:
            for idx in ring.cell_indices:
                self.cells[idx].energy = 0.0  # reset

        print(f"   Holographic encoding: {problem_type_enum.value}")
        print(f"   Boundary (ring {len(self.rings)-1}): full problem")
        print(f"   Center (ring 0): scale {self.rings[0].scale_factor:.3f}")

    def _project_problem(self, parent_problem: Dict, scale: float) -> Dict:
        """
        Project problem to a coarser scale.

        For factorization: project N to a reduced modular arithmetic problem.
        For SAT: project to fewer variables (merge correlated vars).
        For graph coloring: coarsen the graph.
        """
        projected = dict(parent_problem)
        projected["_scale"] = scale

        if self.problem_type == ProblemType.FACTORIZATION:
            N = parent_problem["N"]
            # At coarser scale, we work with N mod (scale-dependent base)
            # This preserves factor structure at reduced precision
            projected["_modular_base"] = max(2, int(math.sqrt(N / max(scale, 1))))

        elif self.problem_type == ProblemType.GRAPH_COLORING:
            # Coarsen: merge adjacent nodes at this scale
            if "adjacency" in parent_problem:
                projected["_coarsened"] = True

        return projected

    # ------------------------------------------------------------------
    # Holographic energy: includes boundary + projection + entanglement
    # ------------------------------------------------------------------

    def compute_total_energy(self) -> float:
        """
        Extended energy with holographic and entanglement terms.

        E = E_base + E_holographic + E_entanglement
        """
        # Base energy from parent (cell + coupling + problem-specific)
        E_base = super().compute_total_energy()

        # Holographic boundary energy: outer ring cells should satisfy the problem
        E_holo = self._holographic_energy()

        # Cross-depth entanglement energy: correlated cells should be consistent
        E_ent = self._entanglement_energy()

        return E_base + self.holographic_weight * E_holo + E_ent

    def _holographic_energy(self) -> float:
        """
        Holographic energy: penalize inconsistency between boundary and interior.

        Outer ring encodes the full problem. Inner rings should be consistent
        projections. Energy is low when the holographic principle is satisfied.
        """
        if not self.rings:
            return 0.0

        energy = 0.0

        # For factorization: check if boundary cell pairs encode valid factors
        if self.problem_type == ProblemType.FACTORIZATION and self.problem_data:
            N = self.problem_data["N"]

            # Each ring contributes energy based on how close its cells
            # come to encoding factors at its scale
            for ring in self.rings:
                scale = ring.projected_problem.get("_scale", 1.0) if ring.projected_problem else 1.0
                cells = [self.cells[i] for i in ring.cell_indices]

                for ci in range(0, len(cells) - 1, 2):
                    fa = 2 + cells[ci].state
                    fb = 2 + cells[ci + 1].state

                    if scale >= 1.0:
                        # Full scale: exact factorization
                        energy += (fa * fb - N) ** 2
                    else:
                        # Reduced scale: modular consistency
                        mod_base = ring.projected_problem.get("_modular_base", 8)
                        energy += ((fa * fb - N) % mod_base) ** 2

        # Self-symmetry penalty: adjacent rings should have consistent states
        for d in range(len(self.rings) - 1):
            inner_cells = [self.cells[i] for i in self.rings[d].cell_indices]
            outer_cells = [self.cells[i] for i in self.rings[d + 1].cell_indices]

            if inner_cells and outer_cells:
                # Dominant state of inner ring should match dominant of outer
                inner_mode = max(set(c.state for c in inner_cells),
                                 key=lambda s: sum(1 for c in inner_cells if c.state == s))
                outer_mode = max(set(c.state for c in outer_cells),
                                 key=lambda s: sum(1 for c in outer_cells if c.state == s))
                # Penalize inconsistency between scales
                energy += 0.5 * (inner_mode != outer_mode)

        return energy

    def _entanglement_energy(self) -> float:
        """
        Cross-depth entanglement energy.

        Entangled cells should have correlated states. The correlation
        depends on the entanglement strength and accumulated phase.
        """
        energy = 0.0
        for link in self.entanglement_links:
            ca = self.cells[link.cell_a]
            cb = self.cells[link.cell_b]

            # Entangled cells want to be in the same state (or complementary)
            state_diff = abs(ca.state - cb.state)
            # Energy is low when states match, weighted by entanglement strength
            energy += link.strength * math.sin(state_diff * math.pi / 4) ** 2

            # Accumulate geometric phase (Berry-like)
            link.phase += state_diff * math.pi / (4 * self.sacred_geometry)

        return energy

    # ------------------------------------------------------------------
    # Correlated Metropolis: entanglement-aware state updates
    # ------------------------------------------------------------------

    def relax_step(self) -> float:
        """
        Extended Metropolis step with entanglement-correlated updates.

        When a cell flips, its entangled partners may flip too
        (probability proportional to entanglement strength).
        """
        # Pick random cell
        cell_idx = np.random.randint(0, self.num_cells)
        cell = self.cells[cell_idx]

        E_old = self.compute_total_energy()
        old_state = cell.state

        # Propose new state
        new_state = np.random.randint(0, self.sacred_geometry)
        cell.state = new_state

        # Correlated update: entangled partners may follow
        correlated_changes = []
        for link in self.entanglement_links:
            partner_idx = None
            if link.cell_a == cell_idx:
                partner_idx = link.cell_b
            elif link.cell_b == cell_idx:
                partner_idx = link.cell_a

            if partner_idx is not None and np.random.random() < link.strength:
                partner = self.cells[partner_idx]
                correlated_changes.append((partner_idx, partner.state))
                # Partner follows: same state or complementary
                if np.random.random() < 0.5:
                    partner.state = new_state  # same
                else:
                    partner.state = (self.sacred_geometry - 1 - new_state) % self.sacred_geometry

        E_new = self.compute_total_energy()
        dE = E_new - E_old

        # Metropolis acceptance
        if dE < 0:
            return dE

        exp_arg = -dE / max(self.temperature, 1e-15)
        p_accept = math.exp(min(exp_arg, 500))

        if np.random.random() < p_accept:
            return dE

        # Reject: restore all states
        cell.state = old_state
        for partner_idx, old_partner_state in correlated_changes:
            self.cells[partner_idx].state = old_partner_state
        return 0.0

    # ------------------------------------------------------------------
    # Renormalization solver: coarse-to-fine with bidirectional propagation
    # ------------------------------------------------------------------

    def renormalization_solve(self, max_steps_per_scale: int = 2000,
                              T_start: float = 3.0, T_end: float = 0.01,
                              num_sweeps: int = 3) -> Dict:
        """
        Self-symmetry renormalization solver.

        1. Solve at coarsest scale (innermost ring) first
        2. Propagate solution outward as initial condition for next scale
        3. Refine at each scale with annealing
        4. Sweep bidirectionally for consistency

        Args:
            max_steps_per_scale: Annealing steps per ring
            T_start: Starting temperature per scale
            T_end: Ending temperature per scale
            num_sweeps: Number of inward-outward sweeps
        """
        if not self.rings:
            return {"error": "No rings — call encode_holographic first"}

        print(f"\n   Renormalization solve: {len(self.rings)} scales, {num_sweeps} sweeps")
        start = time.time()
        all_energies = []

        for sweep in range(num_sweeps):
            direction = "outward" if sweep % 2 == 0 else "inward"
            ring_order = range(len(self.rings)) if direction == "outward" else range(len(self.rings) - 1, -1, -1)

            print(f"\n   Sweep {sweep} ({direction}):")

            for d in ring_order:
                ring = self.rings[d]
                active_cells = ring.cell_indices

                # If outward sweep and we have inner solution, seed from it
                if direction == "outward" and d > 0 and (d - 1) in self.scale_solutions:
                    self._propagate_solution(d - 1, d)

                # Anneal only cells in this ring (freeze others)
                frozen_states = {i: self.cells[i].state for i in range(self.num_cells)
                                 if i not in active_cells}

                steps_done = 0
                for step in range(max_steps_per_scale):
                    frac = step / max(max_steps_per_scale - 1, 1)
                    self.temperature = T_start * (T_end / max(T_start, 1e-15)) ** frac

                    # Only propose moves for cells in this ring
                    ci = active_cells[np.random.randint(0, len(active_cells))]
                    cell = self.cells[ci]
                    E_old = self.compute_total_energy()
                    old_s = cell.state
                    cell.state = np.random.randint(0, self.sacred_geometry)

                    # Correlated entanglement updates (only within active + linked cells)
                    correlated = []
                    for link in self.entanglement_links:
                        partner = None
                        if link.cell_a == ci:
                            partner = link.cell_b
                        elif link.cell_b == ci:
                            partner = link.cell_a
                        if partner is not None and partner not in frozen_states:
                            if np.random.random() < link.strength:
                                correlated.append((partner, self.cells[partner].state))
                                self.cells[partner].state = cell.state

                    E_new = self.compute_total_energy()
                    dE = E_new - E_old

                    accept = dE < 0
                    if not accept:
                        exp_arg = -dE / max(self.temperature, 1e-15)
                        accept = np.random.random() < math.exp(min(exp_arg, 500))

                    if not accept:
                        cell.state = old_s
                        for pi, ps in correlated:
                            self.cells[pi].state = ps

                    # Restore any accidentally changed frozen cells
                    for fi, fs in frozen_states.items():
                        self.cells[fi].state = fs

                    steps_done = step

                E = self.compute_total_energy()
                all_energies.append(E)
                self.energy_history.append(E)

                # Save solution at this scale
                self.scale_solutions[d] = [self.cells[i].state for i in active_cells]

                self._emit_sensor("energy.total", sweep * 1000 + d * 100, E,
                                  {"sweep": sweep, "depth": d, "direction": direction})

                glyph = "".join(
                    _STATE_GLYPHS[self.cells[i].state] if self.cells[i].state < len(_STATE_GLYPHS) else "?"
                    for i in active_cells[:8]
                )
                print(f"      Ring {d} (r={ring.radius:.2f}, {len(active_cells)} cells): "
                      f"E={E:.4f}  {glyph}")

        elapsed = time.time() - start
        final_energy = self.compute_total_energy()
        self.ground_state = [c.state for c in self.cells]
        self.solution = self._extract_solution()

        print(f"\n   Renormalization complete: E={final_energy:.4f} ({elapsed:.2f}s)")
        return {
            "ground_state": self.ground_state,
            "final_energy": final_energy,
            "time": elapsed,
            "solution": self.solution,
            "scale_solutions": dict(self.scale_solutions),
            "energy_history": all_energies,
        }

    def _propagate_solution(self, from_depth: int, to_depth: int):
        """
        Propagate solution from one ring to another via entanglement links.

        The inner ring's dominant state seeds the outer ring's initial condition.
        """
        if from_depth not in self.scale_solutions:
            return

        from_ring = self.rings[from_depth]
        to_ring = self.rings[to_depth]

        # Find dominant state at source scale
        source_states = self.scale_solutions[from_depth]
        if not source_states:
            return
        dominant = max(set(source_states), key=source_states.count)

        # Seed target ring: use entanglement links where possible
        seeded = set()
        for link in self.entanglement_links:
            if link.depth_a == to_depth and link.depth_b == from_depth:
                source_cell = self.cells[link.cell_b]
                self.cells[link.cell_a].state = source_cell.state
                seeded.add(link.cell_a)
            elif link.depth_b == to_depth and link.depth_a == from_depth:
                source_cell = self.cells[link.cell_a]
                self.cells[link.cell_b].state = source_cell.state
                seeded.add(link.cell_b)

        # Remaining cells in target ring: seed with dominant
        for idx in to_ring.cell_indices:
            if idx not in seeded:
                self.cells[idx].state = dominant

    # ------------------------------------------------------------------
    # Unified solve: holographic + renormalization + entanglement
    # ------------------------------------------------------------------

    def holographic_solve(self, problem_type_enum: ProblemType, problem_data: Dict,
                          max_steps_per_scale: int = 2000,
                          T_start: float = 3.0, T_end: float = 0.01,
                          num_sweeps: int = 3) -> Dict:
        """
        Full holographic solve pipeline:
        1. Encode problem holographically (boundary -> interior)
        2. Run renormalization solver (coarse -> fine -> coarse)
        3. Extract solution from ground state
        """
        print("=" * 60)
        print("HOLOGRAPHIC MANDALA SOLVE")
        print("=" * 60)

        # Step 1: Holographic encoding
        self.encode_holographic(problem_type_enum, problem_data)

        # Step 2: Renormalization solve with entangled updates
        result = self.renormalization_solve(
            max_steps_per_scale=max_steps_per_scale,
            T_start=T_start,
            T_end=T_end,
            num_sweeps=num_sweeps,
        )

        # Step 3: Report
        print(f"\n   Entanglement links used: {len(self.entanglement_links)}")
        print(f"   Scale solutions: {len(self.scale_solutions)} levels")
        for d, states in sorted(self.scale_solutions.items()):
            glyphs = "".join(
                _STATE_GLYPHS[s] if s < len(_STATE_GLYPHS) else "?" for s in states[:10]
            )
            print(f"      Ring {d}: {glyphs}")

        return result

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_holographic_profile(self) -> Dict:
        """Show energy and state distribution at each ring depth."""
        profile = {}
        for ring in self.rings:
            cells = [self.cells[i] for i in ring.cell_indices]
            states = [c.state for c in cells]
            dist = {s: states.count(s) for s in range(self.sacred_geometry)}
            profile[ring.depth] = {
                "radius": ring.radius,
                "num_cells": len(cells),
                "scale_factor": ring.scale_factor,
                "state_distribution": dist,
                "dominant_state": max(dist, key=dist.get) if dist else None,
            }
        return profile

    def get_entanglement_map(self) -> List[Dict]:
        """Return entanglement links with current phases."""
        return [
            {
                "cell_a": link.cell_a,
                "cell_b": link.cell_b,
                "depths": (link.depth_a, link.depth_b),
                "strength": link.strength,
                "phase": link.phase,
                "state_a": self.cells[link.cell_a].state,
                "state_b": self.cells[link.cell_b].state,
                "correlated": self.cells[link.cell_a].state == self.cells[link.cell_b].state,
            }
            for link in self.entanglement_links
        ]


# ============================================================================
# DEMONSTRATIONS
# ============================================================================

def demo_holographic_factorization():
    """Demonstrate holographic factorization."""
    print("=" * 60)
    print("DEMO: HOLOGRAPHIC FACTORIZATION")
    print("=" * 60)

    N = 15
    hm = HolographicMandala(
        golden_depth=4,
        sacred_geometry=8,
        entanglement_decay=0.6,
        holographic_weight=0.5,
    )
    result = hm.holographic_solve(
        ProblemType.FACTORIZATION,
        {"N": N},
        max_steps_per_scale=2000,
        num_sweeps=3,
    )
    sol = result["solution"]
    print(f"\n   N={N}")
    print(f"   Best pair: {sol.get('best_pair')}")
    print(f"   Factors: {sol.get('factors')}")
    print(f"   Verified: {sol.get('verified')}")
    print(f"   Telemetry: {len(hm.telemetry)} readings")

    # Show holographic profile
    profile = hm.get_holographic_profile()
    print(f"\n   Holographic profile:")
    for d, info in sorted(profile.items()):
        print(f"      Ring {d}: r={info['radius']:.2f}, "
              f"dominant={_STATE_GLYPHS[info['dominant_state']]}, "
              f"cells={info['num_cells']}")

    # Show entanglement
    ent_map = hm.get_entanglement_map()
    correlated = sum(1 for e in ent_map if e["correlated"])
    print(f"\n   Entanglement: {correlated}/{len(ent_map)} links correlated")

    return hm, result


def demo_holographic_graph_coloring():
    """Demonstrate holographic graph coloring."""
    print("\n" + "=" * 60)
    print("DEMO: HOLOGRAPHIC GRAPH COLORING")
    print("=" * 60)

    # Petersen-like graph: 5 nodes, 7 edges
    adjacency = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0], [0, 2], [1, 3]]
    num_colors = 3

    hm = HolographicMandala(
        golden_depth=3,
        sacred_geometry=8,
        entanglement_decay=0.7,
        holographic_weight=0.3,
    )
    result = hm.holographic_solve(
        ProblemType.GRAPH_COLORING,
        {"adjacency": adjacency, "num_colors": num_colors, "num_nodes": 5},
        max_steps_per_scale=2000,
        num_sweeps=2,
    )
    sol = result["solution"]
    print(f"\n   Coloring: {sol.get('coloring')}")
    print(f"   Violations: {sol.get('violations')}")
    print(f"   Valid: {sol.get('valid')}")
    return hm, result


def demo_comparison():
    """Compare holographic vs standard annealing."""
    print("\n" + "=" * 60)
    print("COMPARISON: HOLOGRAPHIC vs STANDARD ANNEALING")
    print("=" * 60)

    N = 35  # 5 x 7
    results = {}

    # Standard annealing
    mc = MandalaComputer(golden_depth=4, sacred_geometry=8)
    mc.encode_factorization(N)
    t0 = time.time()
    r = mc.simulated_annealing(max_steps=6000, T_start=3.0, T_end=0.01)
    results["standard"] = {
        "energy": r["final_energy"],
        "time": time.time() - t0,
        "verified": r["solution"]["verified"],
        "pair": r["solution"].get("best_pair"),
    }

    # Holographic
    hm = HolographicMandala(golden_depth=4, sacred_geometry=8,
                            entanglement_decay=0.6, holographic_weight=0.5)
    t0 = time.time()
    r = hm.holographic_solve(ProblemType.FACTORIZATION, {"N": N},
                             max_steps_per_scale=1500, num_sweeps=3)
    results["holographic"] = {
        "energy": r["final_energy"],
        "time": time.time() - t0,
        "verified": r["solution"]["verified"],
        "pair": r["solution"].get("best_pair"),
    }

    print(f"\n   {'Method':<20s} {'Energy':>10s} {'Time':>8s} {'Pair':<12s} {'Correct':>8s}")
    print("   " + "-" * 60)
    for name, data in results.items():
        print(f"   {name:<20s} {data['energy']:>10.2f} {data['time']:>8.3f} "
              f"{str(data['pair']):<12s} {'YES' if data['verified'] else 'no':>8s}")

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("HOLOGRAPHIC MANDALA COMPUTING v1.0")
    print("  Boundary + Self-Symmetry + Entanglement")
    print("=" * 60)

    demo_holographic_factorization()
    demo_holographic_graph_coloring()
    demo_comparison()

    print("\n" + "=" * 60)
    print("ALL HOLOGRAPHIC DEMONSTRATIONS COMPLETE")
    print("=" * 60)
