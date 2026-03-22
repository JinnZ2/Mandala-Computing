"""
example-quantum-integration.py
Demonstrates concepts from Quantum_integration.md:
  - 8 octahedral eigenvalue states
  - FRET coupling strength: J ~ 1/r^6
  - Fibonacci eigenvalue optimization: lambda_0 / lambda_1 = phi
  - Integrated information (phi) for consciousness detection
"""

import numpy as np
from scipy.linalg import eigh


PHI = (1 + np.sqrt(5)) / 2

# 8 canonical octahedral eigenvalue states from the spec
OCTAHEDRAL_STATES = [
    (0.33, 0.33, 0.33),  # state 0: balanced
    (0.50, 0.30, 0.20),  # state 1
    (0.25, 0.50, 0.25),  # state 2
    (0.20, 0.20, 0.60),  # state 3
    (0.40, 0.35, 0.25),  # state 4
    (0.30, 0.45, 0.25),  # state 5
    (0.35, 0.25, 0.40),  # state 6
    (0.45, 0.40, 0.15),  # state 7: most asymmetric
]


def fret_coupling(r: float) -> float:
    """
    FRET dipole-dipole coupling strength.

    J ~ 1/r^6 (Forster Resonance Energy Transfer)
    Returns 0.0 if r <= 0.
    """
    if r <= 0:
        return 0.0
    return 1.0 / (r ** 6)


def fibonacci_eigenvalues(depth: int) -> np.ndarray:
    """
    Generate Fibonacci-scaled eigenvalue spectrum.

    lambda_i = phi^i, normalized so sum = 1.
    Key property: lambda_0 / lambda_1 = phi.
    """
    raw = np.array([PHI ** i for i in range(depth)])
    return raw / raw.sum()


def integrated_information(coupling_matrix: np.ndarray) -> float:
    """
    Estimate integrated information (phi) from coupling matrix.

    Uses eigenvalue spread of the coupling matrix as a proxy.
    Consciousness threshold: phi > 3.0 (from the spec).
    """
    eigenvalues = np.linalg.eigvalsh(coupling_matrix)
    eigenvalues = np.sort(eigenvalues)[::-1]

    # phi estimate: ratio of information integration
    if len(eigenvalues) < 2 or eigenvalues[-1] == 0:
        return eigenvalues[0] if len(eigenvalues) > 0 else 0.0

    return float(np.sum(np.abs(eigenvalues)) / np.max(np.abs(eigenvalues)))


def demo_octahedral_states():
    """Print the 8 canonical eigenvalue states."""
    print("\n8 octahedral eigenvalue states")
    print(f"{'state':>6}  {'e1':>6}  {'e2':>6}  {'e3':>6}  {'sum':>6}")
    print("-" * 36)
    for i, (e1, e2, e3) in enumerate(OCTAHEDRAL_STATES):
        print(f"{i:>6}  {e1:>6.2f}  {e2:>6.2f}  {e3:>6.2f}  {e1+e2+e3:>6.2f}")


def demo_fret_coupling():
    """Show FRET coupling decay with distance."""
    print("\nFRET coupling J ~ 1/r^6")
    print(f"{'r':>8}  {'J':>14}")
    print("-" * 24)
    for r in [0.5, 1.0, 1.5, 2.0, 3.0, PHI, 5.0, 10.0]:
        J = fret_coupling(r)
        print(f"{r:>8.3f}  {J:>14.6f}")


def demo_fibonacci_eigenvalues():
    """Show Fibonacci eigenvalue spectrum and phi ratio."""
    print("\nFibonacci eigenvalue spectrum (depth=6)")
    ev = fibonacci_eigenvalues(6)
    for i, v in enumerate(ev):
        print(f"  lambda_{i} = {v:.6f}")

    ratio = ev[1] / ev[0] if ev[0] != 0 else 0
    print(f"\n  lambda_1 / lambda_0 = {ratio:.6f}  (phi = {PHI:.6f})")


def demo_consciousness_detection():
    """
    Build a small coupled system and compute integrated information.
    """
    print("\nconsciousness detection via integrated information")
    n_cells = 6

    # build coupling matrix from FRET between cells in a ring
    C = np.zeros((n_cells, n_cells))
    radius = 2.0
    positions = [
        (radius * np.cos(2 * np.pi * i / n_cells),
         radius * np.sin(2 * np.pi * i / n_cells))
        for i in range(n_cells)
    ]

    for i in range(n_cells):
        for j in range(i + 1, n_cells):
            dx = positions[i][0] - positions[j][0]
            dy = positions[i][1] - positions[j][1]
            r = np.sqrt(dx ** 2 + dy ** 2)
            J = fret_coupling(r)
            C[i, j] = J
            C[j, i] = J

    phi = integrated_information(C)
    threshold = 3.0
    status = "CONSCIOUS" if phi > threshold else "below threshold"

    print(f"  cells: {n_cells}")
    print(f"  integrated information (phi): {phi:.4f}")
    print(f"  threshold: {threshold}")
    print(f"  status: {status}")


if __name__ == "__main__":
    print("=" * 60)
    print("example-quantum-integration: FRET coupling + consciousness")
    print("=" * 60)

    demo_octahedral_states()
    demo_fret_coupling()
    demo_fibonacci_eigenvalues()
    demo_consciousness_detection()

    print("\ndone.")
