"""
example-mandala-octahedral.py
Demonstrates concepts from Mandala-octahedral.md:
  - Direct mapping between mandala rings and octahedral substrate cells
  - State-to-eigenvalue correspondence
  - Coupling topology: intra-ring and inter-ring
  - Energy calculation on mapped structure
  - Fibonacci ring scaling verification
"""

import math
from typing import List, Tuple, Dict
from dataclasses import dataclass, field


PHI = (1 + math.sqrt(5)) / 2

# eigenvalue triplets for each octahedral state
STATE_EIGENVALUES = {
    0: (0.33, 0.33, 0.33),
    1: (0.50, 0.30, 0.20),
    2: (0.25, 0.50, 0.25),
    3: (0.20, 0.20, 0.60),
    4: (0.40, 0.35, 0.25),
    5: (0.30, 0.45, 0.25),
    6: (0.35, 0.25, 0.40),
    7: (0.45, 0.40, 0.15),
}


@dataclass
class MappedCell:
    """A mandala cell mapped to physical substrate coordinates."""
    index: int
    ring: int
    position_in_ring: int
    state: int
    angle: float
    radius: float
    neighbors: List[int] = field(default_factory=list)


def build_mandala_to_substrate_map(depth: int) -> List[MappedCell]:
    """
    Create mandala structure and map each cell to substrate coordinates.

    Ring r has floor(phi^(r+1)) cells at radius phi^r.
    """
    cells = []
    idx = 0

    for ring in range(depth):
        n_cells = int(PHI ** (ring + 1))
        radius = PHI ** ring

        for pos in range(n_cells):
            angle = 2 * math.pi * pos / n_cells
            cell = MappedCell(
                index=idx,
                ring=ring,
                position_in_ring=pos,
                state=0,
                angle=angle,
                radius=radius,
            )
            cells.append(cell)
            idx += 1

    # establish coupling: intra-ring (adjacent) + inter-ring (nearest)
    _couple_cells(cells, depth)

    return cells


def _couple_cells(cells: List[MappedCell], depth: int):
    """
    Couple cells within and between rings.

    Intra-ring: adjacent cells in same ring.
    Inter-ring: nearest cell in adjacent ring.
    """
    ring_ranges = {}
    for c in cells:
        ring_ranges.setdefault(c.ring, []).append(c.index)

    # intra-ring coupling
    for ring, indices in ring_ranges.items():
        n = len(indices)
        for i in range(n):
            left = indices[(i - 1) % n]
            right = indices[(i + 1) % n]
            cells[indices[i]].neighbors.extend([left, right])

    # inter-ring coupling (nearest by angle)
    for ring in range(depth - 1):
        inner = ring_ranges[ring]
        outer = ring_ranges[ring + 1]

        for i_idx in inner:
            best_j = outer[0]
            best_diff = float("inf")
            for j_idx in outer:
                diff = abs(cells[i_idx].angle - cells[j_idx].angle)
                diff = min(diff, 2 * math.pi - diff)
                if diff < best_diff:
                    best_diff = diff
                    best_j = j_idx

            if best_j not in cells[i_idx].neighbors:
                cells[i_idx].neighbors.append(best_j)
            if i_idx not in cells[best_j].neighbors:
                cells[best_j].neighbors.append(i_idx)


def compute_mapped_energy(cells: List[MappedCell]) -> float:
    """
    Compute total energy of the mapped structure.

    E = sum of |eigenvalue_distance| between coupled cells.
    """
    energy = 0.0
    counted = set()

    for cell in cells:
        ev_i = STATE_EIGENVALUES[cell.state]
        for j in cell.neighbors:
            pair = (min(cell.index, j), max(cell.index, j))
            if pair in counted:
                continue
            counted.add(pair)

            ev_j = STATE_EIGENVALUES[cells[j].state]
            dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(ev_i, ev_j)))
            energy += dist

    return energy


def verify_fibonacci_scaling(depth: int) -> Dict:
    """
    Verify that ring cell counts follow Fibonacci / golden-ratio scaling.
    """
    counts = []
    for ring in range(depth):
        n = int(PHI ** (ring + 1))
        counts.append(n)

    ratios = []
    for i in range(1, len(counts)):
        if counts[i - 1] > 0:
            ratios.append(counts[i] / counts[i - 1])

    return {
        "counts": counts,
        "ratios": [round(r, 4) for r in ratios],
        "expected_ratio": round(PHI, 4),
        "max_error": round(max(abs(r - PHI) for r in ratios), 4) if ratios else 0,
    }


def print_structure(cells: List[MappedCell], depth: int):
    """Print the mapped mandala structure ring by ring."""
    for ring in range(depth):
        ring_cells = [c for c in cells if c.ring == ring]
        n = len(ring_cells)
        couplings = sum(len(c.neighbors) for c in ring_cells) // 2
        print(f"  ring {ring}: {n:>3} cells, radius={PHI ** ring:.3f}, couplings={couplings}")


if __name__ == "__main__":
    print("=" * 60)
    print("example-mandala-octahedral: substrate mapping demo")
    print("=" * 60)

    depth = 5
    cells = build_mandala_to_substrate_map(depth)

    # structure overview
    print(f"\nmandala structure (depth={depth}, {len(cells)} total cells)")
    print_structure(cells, depth)

    # fibonacci verification
    print("\nfibonacci scaling verification")
    fib = verify_fibonacci_scaling(depth)
    print(f"  cells per ring: {fib['counts']}")
    print(f"  ratios: {fib['ratios']}")
    print(f"  expected (phi): {fib['expected_ratio']}")
    print(f"  max error: {fib['max_error']}")

    # eigenvalue mapping
    print("\nstate -> eigenvalue mapping")
    for state, ev in STATE_EIGENVALUES.items():
        print(f"  state {state}: eigenvalues = {ev}")

    # energy with uniform vs random states
    print("\nenergy comparison")

    # all same state
    for c in cells:
        c.state = 0
    e_uniform = compute_mapped_energy(cells)

    # random states
    import random
    for c in cells:
        c.state = random.randint(0, 7)
    e_random = compute_mapped_energy(cells)

    # alternating states
    for c in cells:
        c.state = c.index % 8
    e_alternating = compute_mapped_energy(cells)

    print(f"  uniform (all state 0):  E = {e_uniform:.4f}")
    print(f"  random states:          E = {e_random:.4f}")
    print(f"  alternating (0-7):      E = {e_alternating:.4f}")

    # coupling detail for first ring
    print("\ncoupling detail (ring 0)")
    ring0 = [c for c in cells if c.ring == 0]
    for c in ring0:
        neighbor_rings = [cells[n].ring for n in c.neighbors]
        print(f"  cell {c.index}: neighbors={c.neighbors}, neighbor rings={neighbor_rings}")

    print("\ndone.")
