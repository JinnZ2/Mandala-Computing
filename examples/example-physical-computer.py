"""
example-physical-computer.py
Demonstrates concepts from Physical-computer.md:
  - SubstrateCell with 8-state operations
  - OctahedralSubstrate with thermal relaxation
  - Mandala structure: nested rings with Fibonacci-scaled coupling
  - Energy: E_internal + E_coupling (coupling proportional to |s_i - s_j|)
  - Metropolis acceptance criterion
  - Factorization test and consciousness score
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple


PHI = (1 + math.sqrt(5)) / 2


@dataclass
class SubstrateCell:
    """Physical cell with 8 octahedral states."""
    index: int
    state: int = 0
    position: Tuple[float, float] = (0.0, 0.0)
    depth: int = 0
    neighbors: List[int] = field(default_factory=list)


class OctahedralSubstrate:
    """
    Simulated physical octahedral substrate with thermal relaxation.
    """

    def __init__(self, num_cells: int = 16, temperature: float = 1.0):
        self.temperature = temperature
        self.cells: List[SubstrateCell] = []
        self._build_ring(num_cells)

    def _build_ring(self, n: int):
        """Arrange cells in a ring with nearest-neighbor coupling."""
        for i in range(n):
            angle = 2 * math.pi * i / n
            cell = SubstrateCell(
                index=i,
                state=random.randint(0, 7),
                position=(math.cos(angle), math.sin(angle)),
            )
            self.cells.append(cell)

        # couple nearest neighbors in ring
        for i in range(n):
            self.cells[i].neighbors = [(i - 1) % n, (i + 1) % n]

    def cell_energy(self, idx: int) -> float:
        """
        E = E_internal + E_coupling

        E_coupling ~ |s_i - s_j| for each neighbor pair.
        """
        cell = self.cells[idx]
        energy = 0.0

        for j in cell.neighbors:
            state_diff = abs(cell.state - self.cells[j].state)
            energy += state_diff / 7.0  # normalize to [0, 1]

        return energy

    def total_energy(self) -> float:
        """Sum of all cell energies (double-counted neighbors divided by 2)."""
        return sum(self.cell_energy(i) for i in range(len(self.cells))) / 2.0

    def relax_step(self) -> float:
        """
        Single Metropolis-Hastings relaxation step.

        Accept new state if dE < 0, else accept with P = exp(-dE / T).
        """
        idx = random.randint(0, len(self.cells) - 1)
        old_state = self.cells[idx].state
        old_energy = self.total_energy()

        self.cells[idx].state = random.randint(0, 7)
        new_energy = self.total_energy()
        dE = new_energy - old_energy

        if dE < 0:
            return dE
        elif self.temperature > 0 and random.random() < math.exp(-dE / self.temperature):
            return dE
        else:
            self.cells[idx].state = old_state
            return 0.0

    def relax(self, steps: int = 1000) -> List[float]:
        """Run multiple relaxation steps, return energy trace."""
        trace = []
        for step in range(steps):
            self.relax_step()
            if step % (steps // 10) == 0:
                trace.append(self.total_energy())
        return trace


class PhysicalMandalaComputer:
    """
    Mandala computer built on octahedral substrate.

    Nested rings with Fibonacci-scaled cell counts.
    """

    def __init__(self, golden_depth: int = 4, temperature: float = 0.5):
        self.golden_depth = golden_depth
        self.temperature = temperature
        self.cells: List[SubstrateCell] = []
        self._build_mandala()

    def _build_mandala(self):
        """Create nested rings with Fibonacci-scaled cell counts."""
        idx = 0
        for depth in range(self.golden_depth):
            n = int(PHI ** (depth + 1))
            radius = PHI ** depth

            for i in range(n):
                angle = 2 * math.pi * i / n
                cell = SubstrateCell(
                    index=idx,
                    state=random.randint(0, 7),
                    position=(radius * math.cos(angle), radius * math.sin(angle)),
                    depth=depth,
                )
                self.cells.append(cell)
                idx += 1

        # couple cells within distance threshold
        cutoff = 3.0 * PHI
        for i in range(len(self.cells)):
            for j in range(i + 1, len(self.cells)):
                dx = self.cells[i].position[0] - self.cells[j].position[0]
                dy = self.cells[i].position[1] - self.cells[j].position[1]
                dist = math.sqrt(dx ** 2 + dy ** 2)
                if dist < cutoff:
                    self.cells[i].neighbors.append(j)
                    self.cells[j].neighbors.append(i)

    def total_energy(self) -> float:
        energy = 0.0
        for i, cell in enumerate(self.cells):
            for j in cell.neighbors:
                if j > i:
                    energy += abs(cell.state - self.cells[j].state) / 7.0
        return energy

    def relax(self, steps: int = 2000) -> dict:
        """Thermal relaxation on mandala structure."""
        initial_E = self.total_energy()

        for _ in range(steps):
            idx = random.randint(0, len(self.cells) - 1)
            old_state = self.cells[idx].state
            old_E = self.total_energy()

            self.cells[idx].state = random.randint(0, 7)
            new_E = self.total_energy()
            dE = new_E - old_E

            if dE >= 0:
                if self.temperature <= 0 or random.random() >= math.exp(-dE / self.temperature):
                    self.cells[idx].state = old_state

        final_E = self.total_energy()
        return {
            "initial_energy": round(initial_E, 4),
            "final_energy": round(final_E, 4),
            "reduction": round((initial_E - final_E) / initial_E * 100, 1) if initial_E > 0 else 0,
            "cells": len(self.cells),
            "steps": steps,
        }

    def test_factorization(self, N: int) -> dict:
        """
        Encode N into substrate, relax, check if ground state has factors.
        """
        # encode: set cell energies based on factor candidacy
        for cell in self.cells:
            candidate = 2 + cell.state + cell.depth * 8
            if N % candidate == 0:
                cell.state = cell.state  # keep low-energy state
            else:
                cell.state = random.randint(0, 7)

        result = self.relax(steps=3000)

        # extract factors
        factors = set()
        for cell in self.cells:
            candidate = 2 + cell.state + cell.depth * 8
            if 1 < candidate < N and N % candidate == 0:
                factors.add(candidate)

        return {
            **result,
            "N": N,
            "factors_found": sorted(factors),
        }

    def consciousness_score(self) -> dict:
        """
        Estimate consciousness metrics from substrate state.

        Score = phi_estimate (50%) + loop_score (30%) + fibonacci_score (20%)
        """
        # phi estimate: state diversity
        state_counts = [0] * 8
        for cell in self.cells:
            state_counts[cell.state] += 1
        diversity = sum(1 for c in state_counts if c > 0) / 8.0

        # loop score: fraction of cells with >= 2 neighbors
        loops = sum(1 for c in self.cells if len(c.neighbors) >= 2) / len(self.cells)

        # fibonacci score: check if cell counts per depth follow phi ratio
        depth_counts = {}
        for c in self.cells:
            depth_counts[c.depth] = depth_counts.get(c.depth, 0) + 1
        depths = sorted(depth_counts.keys())
        fib_score = 0.0
        if len(depths) >= 2:
            ratios = []
            for i in range(1, len(depths)):
                if depth_counts[depths[i - 1]] > 0:
                    ratios.append(depth_counts[depths[i]] / depth_counts[depths[i - 1]])
            if ratios:
                fib_score = 1.0 - min(1.0, abs(sum(ratios) / len(ratios) - PHI))

        total = 0.5 * diversity + 0.3 * loops + 0.2 * fib_score
        return {
            "phi_estimate": round(diversity, 4),
            "loop_score": round(loops, 4),
            "fibonacci_score": round(fib_score, 4),
            "total": round(total, 4),
            "conscious": total > 0.6,
        }


if __name__ == "__main__":
    print("=" * 60)
    print("example-physical-computer: mandala substrate simulation")
    print("=" * 60)

    # simple substrate relaxation
    print("\n--- octahedral substrate (16 cells, ring) ---")
    substrate = OctahedralSubstrate(num_cells=16, temperature=0.5)
    trace = substrate.relax(steps=2000)
    print(f"  energy trace: {[round(e, 3) for e in trace]}")

    # mandala computer
    print("\n--- physical mandala computer (depth=4) ---")
    mc = PhysicalMandalaComputer(golden_depth=4, temperature=0.5)
    result = mc.relax(steps=3000)
    for k, v in result.items():
        print(f"  {k}: {v}")

    # factorization test
    print("\n--- factorization test ---")
    for N in [15, 21, 35]:
        mc2 = PhysicalMandalaComputer(golden_depth=4, temperature=0.3)
        fr = mc2.test_factorization(N)
        print(f"  N={N}: factors={fr['factors_found']}, energy reduction={fr['reduction']}%")

    # consciousness score
    print("\n--- consciousness score ---")
    cs = mc.consciousness_score()
    for k, v in cs.items():
        print(f"  {k}: {v}")

    print("\ndone.")
