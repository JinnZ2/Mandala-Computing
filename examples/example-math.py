"""
example-math.py
Demonstrates concepts from Math.md:
  - Hamiltonian construction for factorization: H = (X1 * X2 - N)^2
  - Eigenvalue decomposition to find ground state
  - Energy landscape analysis
  - Thermal error probability
"""

try:
    import numpy as np
    from scipy.linalg import eigh
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("note: numpy/scipy not installed — eigenvalue demo will be skipped")
    print("install with: pip install numpy scipy\n")

import math


PHI = (1 + math.sqrt(5)) / 2


def auto_dim(N: int) -> int:
    """Choose Hamiltonian dimension large enough to contain all factors of N.

    Factors range from 2 to 2+dim-1, so dim must be >= (largest_factor - 1).
    Largest possible factor is N//2, so dim = N//2 covers everything.
    """
    return max(8, N // 2)


def build_factorization_hamiltonian(N: int, dim: int = 8) -> np.ndarray:
    """
    Build Hamiltonian encoding factorization of N.

    H[i*dim+j, i*dim+j] = (factor_a * factor_b - N)^2

    Ground state (minimum eigenvalue) corresponds to valid factor pair.
    """
    size = dim * dim
    H = np.zeros((size, size))

    for i in range(dim):
        for j in range(dim):
            factor_a = 2 + i
            factor_b = 2 + j
            idx = i * dim + j
            H[idx, idx] = (factor_a * factor_b - N) ** 2

    return H


def find_factors_via_eigenvalues(N: int, dim: int = 8):
    """
    Solve factorization by finding the ground state eigenvalue of H.
    """
    H = build_factorization_hamiltonian(N, dim)
    eigenvalues, eigenvectors = eigh(H)

    ground_energy = eigenvalues[0]
    ground_state = eigenvectors[:, 0]

    # find which basis state has largest amplitude
    max_idx = np.argmax(np.abs(ground_state))
    factor_a = 2 + max_idx // dim
    factor_b = 2 + max_idx % dim

    return {
        "N": N,
        "ground_energy": ground_energy,
        "factor_a": factor_a,
        "factor_b": factor_b,
        "product": factor_a * factor_b,
        "verified": factor_a * factor_b == N,
    }


def energy_landscape(N: int, max_factor: int = 10):
    """
    Print the energy landscape E(x,y) = (xy - N)^2 for candidate factors.
    """
    print(f"\nenergy landscape for N = {N}")
    print(f"E(x,y) = (x * y - N)^2\n")

    header = "     " + "".join(f"{y:>8}" for y in range(2, max_factor))
    print(header)
    print("     " + "-" * (8 * (max_factor - 2)))

    for x in range(2, max_factor):
        row = f"{x:>3} |"
        for y in range(2, max_factor):
            energy = (x * y - N) ** 2
            marker = " *" if energy == 0 else ""
            row += f"{energy:>6}{marker:2s}"
        print(row)


def thermal_error_probability(delta_E: float, temperature_K: float) -> float:
    """
    Boltzmann error probability: P_error = exp(-delta_E / kT)

    Args:
        delta_E: energy gap in eV
        temperature_K: temperature in Kelvin
    """
    k_B = 8.617e-5  # eV/K
    kT = k_B * temperature_K
    if kT == 0:
        return 0.0
    return math.exp(-delta_E / kT)


def demo_thermal_errors():
    """Show how thermal noise affects solution accuracy at various temperatures."""
    print("\nthermal error probability P_error = exp(-dE / kT)")
    print(f"{'dE (eV)':>10}  {'4 K':>12}  {'77 K':>12}  {'300 K':>12}")
    print("-" * 50)

    for dE in [0.001, 0.01, 0.1, 0.5, 1.0]:
        p4 = thermal_error_probability(dE, 4.0)
        p77 = thermal_error_probability(dE, 77.0)
        p300 = thermal_error_probability(dE, 300.0)
        print(f"{dE:>10.3f}  {p4:>12.6e}  {p77:>12.6e}  {p300:>12.6e}")


if __name__ == "__main__":
    print("=" * 60)
    print("example-math: factorization via eigenvalue decomposition")
    print("=" * 60)

    if HAS_NUMPY:
        # factorize small numbers (auto_dim ensures factors are in range)
        for N in [15, 21, 35, 77, 143]:
            dim = auto_dim(N)
            result = find_factors_via_eigenvalues(N, dim=dim)
            status = "ok" if result["verified"] else "MISS"
            print(
                f"  N={N:>4}  ->  {result['factor_a']} x {result['factor_b']} "
                f"= {result['product']}  [{status}]  "
                f"E0={result['ground_energy']:.4f}  (dim={dim})"
            )
    else:
        print("  (skipped — numpy/scipy required)")

    energy_landscape(15, max_factor=8)
    demo_thermal_errors()

    # --- Bridge to main engine ---
    print("\n" + "=" * 60)
    print("comparison: eigenvalue vs geometric relaxation")
    print("=" * 60)
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from mandala_computer import MandalaComputer

        for N in [15, 21, 35]:
            # Eigenvalue method (exact)
            dim = auto_dim(N)
            ev_result = find_factors_via_eigenvalues(N, dim=dim)

            # Geometric relaxation (simulated annealing)
            mc = MandalaComputer(golden_depth=4, sacred_geometry=8)
            mc.encode_factorization(N)
            sa_result = mc.simulated_annealing(max_steps=3000, T_start=3.0, T_end=0.01)

            ev_ok = "ok" if ev_result["verified"] else "MISS"
            sa_ok = "ok" if sa_result["solution"]["verified"] else "MISS"
            print(f"  N={N:>4}  eigenvalue: {ev_result['factor_a']}x{ev_result['factor_b']} [{ev_ok}]"
                  f"  annealing: {sa_result['solution'].get('best_pair', '?')} [{sa_ok}]"
                  f"  E={sa_result['final_energy']:.2f}")
    except Exception as e:
        print(f"  (engine comparison skipped: {e})")

    print("\ndone.")
