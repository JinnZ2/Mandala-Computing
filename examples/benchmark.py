"""
benchmark.py
Classical vs Quantum comparison across all search methods.

Runs the same factorization problem through every available algorithm
and reports time-to-solution, final energy, and whether factors were found.
"""

import sys
import os
import time

# Add parent directory to path so we can import the main engines
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mandala_computer import MandalaComputer
from quantum_mandala import QuantumMandalaComputer

import numpy as np


def benchmark_factorization(N: int = 15):
    """
    Benchmark all methods on factorizing N.

    N=15 (3x5) is small enough for quantum to handle exactly.
    """
    print("=" * 70)
    print(f"BENCHMARK: Factor N={N} across all methods")
    print("=" * 70)

    results = {}

    # ---- Classical: Metropolis relaxation ----
    print("\n--- Classical: Metropolis Relaxation ---")
    mc = MandalaComputer(golden_depth=4, sacred_geometry=8, temperature=0.5)
    mc.encode_factorization(N)
    t0 = time.time()
    r = mc.relax_to_ground_state(max_steps=5000)
    dt = time.time() - t0
    results["metropolis"] = {
        "energy": r["final_energy"],
        "time": dt,
        "factors": r["solution"]["factors"],
        "verified": r["solution"]["verified"],
        "telemetry_count": len(mc.telemetry),
    }

    # ---- Classical: Simulated Annealing (exponential) ----
    print("\n--- Classical: Simulated Annealing (exponential) ---")
    mc2 = MandalaComputer(golden_depth=4, sacred_geometry=8)
    mc2.encode_factorization(N)
    t0 = time.time()
    r = mc2.simulated_annealing(max_steps=5000, T_start=3.0, T_end=0.01, schedule="exponential")
    dt = time.time() - t0
    results["annealing_exp"] = {
        "energy": r["final_energy"],
        "time": dt,
        "factors": r["solution"]["factors"],
        "verified": r["solution"]["verified"],
    }

    # ---- Classical: Simulated Annealing (boltzmann) ----
    print("\n--- Classical: Simulated Annealing (boltzmann) ---")
    mc3 = MandalaComputer(golden_depth=4, sacred_geometry=8)
    mc3.encode_factorization(N)
    t0 = time.time()
    r = mc3.simulated_annealing(max_steps=5000, T_start=3.0, T_end=0.01, schedule="boltzmann")
    dt = time.time() - t0
    results["annealing_boltz"] = {
        "energy": r["final_energy"],
        "time": dt,
        "factors": r["solution"]["factors"],
        "verified": r["solution"]["verified"],
    }

    # ---- Classical: Parallel Tempering ----
    print("\n--- Classical: Parallel Tempering ---")
    mc4 = MandalaComputer(golden_depth=4, sacred_geometry=8)
    mc4.encode_factorization(N)
    t0 = time.time()
    r = mc4.parallel_tempering(num_replicas=4, T_min=0.1, T_max=5.0, max_steps=5000)
    dt = time.time() - t0
    results["parallel_tempering"] = {
        "energy": r["final_energy"],
        "time": dt,
        "factors": r["solution"]["factors"],
        "verified": r["solution"]["verified"],
        "swaps": r["swaps"],
    }

    # ---- Classical: Landscape Scan ----
    print("\n--- Classical: Landscape Scan ---")
    mc5 = MandalaComputer(golden_depth=4, sacred_geometry=8)
    mc5.encode_factorization(N)
    t0 = time.time()
    r = mc5.landscape_scan(num_samples=1000)
    dt = time.time() - t0
    results["landscape_scan"] = {
        "energy": r["min_energy"],
        "time": dt,
        "factors": [],
        "verified": False,
        "mean_energy": r["mean_energy"],
        "std_energy": r["std_energy"],
    }

    # ---- Quantum: Annealing (2-cell) ----
    print("\n--- Quantum: Annealing (2-cell, 64-dim) ---")
    qc = QuantumMandalaComputer(golden_depth=2, sacred_geometry=8, entanglement_strength=0.1)
    t0 = time.time()
    r = qc.quantum_annealing("factorization", {"N": N}, num_steps=100)
    dt = time.time() - t0
    results["quantum_annealing"] = {
        "energy": r["final_energy"],
        "time": dt,
        "factors": r["solution"]["factors"],
        "verified": r["solution"]["correct"],
    }

    # ---- Quantum: QAOA (Nelder-Mead) ----
    print("\n--- Quantum: QAOA (Nelder-Mead, 64-dim) ---")
    qc2 = QuantumMandalaComputer(golden_depth=2, sacred_geometry=8, entanglement_strength=0.1)
    qc2.bloom_quantum_mandala()
    t0 = time.time()
    r = qc2.qaoa("factorization", {"N": N}, num_layers=4, optimize=True)
    dt = time.time() - t0
    results["qaoa"] = {
        "energy": r["final_energy"],
        "time": dt,
        "factors": r["solution"]["factors"],
        "verified": r["solution"]["correct"],
    }

    # ---- Quantum: Entangled Annealing (2-cell, 64-dim) ----
    print("\n--- Quantum: Entangled Annealing (2-cell, 64-dim) ---")
    qc3 = QuantumMandalaComputer(golden_depth=2, sacred_geometry=8, entanglement_strength=0.5)
    t0 = time.time()
    r = qc3.entangled_annealing("factorization", {"N": N}, num_cells=2, num_steps=100)
    dt = time.time() - t0
    results["entangled_annealing"] = {
        "energy": r["final_energy"],
        "time": dt,
        "factors": r["solution"]["factors"],
        "verified": r["solution"]["correct"],
        "cell_states": r["cell_states"],
    }

    # ---- Summary ----
    print("\n" + "=" * 70)
    print(f"RESULTS SUMMARY: N={N}")
    print("=" * 70)
    print(f"{'Method':<25s} {'Energy':>10s} {'Time(s)':>10s} {'Factors':<15s} {'Correct':>8s}")
    print("-" * 70)
    for name, data in results.items():
        factors_str = str(data.get("factors", []))[:14]
        verified = data.get("verified", False)
        print(f"{name:<25s} {data['energy']:>10.4f} {data['time']:>10.4f} {factors_str:<15s} {'YES' if verified else 'no':>8s}")
    print("-" * 70)

    # Count wins
    correct_methods = [k for k, v in results.items() if v.get("verified")]
    print(f"\nMethods that found correct factors: {len(correct_methods)}/{len(results)}")
    for m in correct_methods:
        print(f"   {m}: {results[m]['factors']}")

    if correct_methods:
        fastest = min(correct_methods, key=lambda k: results[k]["time"])
        print(f"\nFastest correct method: {fastest} ({results[fastest]['time']:.4f}s)")

    return results


def benchmark_scaling():
    """Test how methods scale with problem size."""
    print("\n" + "=" * 70)
    print("SCALING BENCHMARK")
    print("=" * 70)

    test_numbers = [15, 21, 35, 77, 143]

    print(f"{'N':<8s} {'Annealing':>12s} {'Tempering':>12s} {'Q-Anneal':>12s} {'QAOA':>12s}")
    print("-" * 58)

    for N in test_numbers:
        times = {}

        # Classical annealing
        mc = MandalaComputer(golden_depth=4, sacred_geometry=8)
        mc.encode_factorization(N)
        t0 = time.time()
        mc.simulated_annealing(max_steps=3000, T_start=3.0, T_end=0.01)
        times["anneal"] = time.time() - t0

        # Parallel tempering
        mc2 = MandalaComputer(golden_depth=4, sacred_geometry=8)
        mc2.encode_factorization(N)
        t0 = time.time()
        mc2.parallel_tempering(num_replicas=4, max_steps=3000)
        times["temper"] = time.time() - t0

        # Quantum annealing
        qc = QuantumMandalaComputer(golden_depth=2, sacred_geometry=8)
        t0 = time.time()
        qc.quantum_annealing("factorization", {"N": N}, num_steps=60)
        times["q_anneal"] = time.time() - t0

        # QAOA
        qc2 = QuantumMandalaComputer(golden_depth=2, sacred_geometry=8)
        qc2.bloom_quantum_mandala()
        t0 = time.time()
        qc2.qaoa("factorization", {"N": N}, num_layers=3, optimize=True)
        times["qaoa"] = time.time() - t0

        print(f"{N:<8d} {times['anneal']:>12.4f} {times['temper']:>12.4f} {times['q_anneal']:>12.4f} {times['qaoa']:>12.4f}")


if __name__ == "__main__":
    results = benchmark_factorization(N=15)
    benchmark_scaling()
    print("\nBenchmark complete.")
