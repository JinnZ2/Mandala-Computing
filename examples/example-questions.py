"""
example-questions.py
Demonstrates concepts from Questions.md / Mandala_integration.md:
  - Encoding complexity analysis: factorization O(log N), SAT O(K+V), TSP O(N^2)
  - Thermal noise limits at various temperatures
  - Decoherence time comparison
  - Problem encodability scoring
  - Intellectual honesty categories: PROVEN -> UNTESTABLE
  - Testable predictions
"""

import math
from dataclasses import dataclass
from typing import Dict, List


PHI = (1 + math.sqrt(5)) / 2
K_B = 8.617e-5  # Boltzmann constant in eV/K


# --- encoding complexity ---

def encoding_complexity(problem_type: str, problem_params: Dict) -> Dict:
    """
    Analyze encoding complexity for different problem types.
    """
    if problem_type == "factorization":
        N = problem_params["N"]
        bits = math.ceil(math.log2(N)) if N > 1 else 1
        encode_steps = bits  # O(log N)
        cells_needed = 2 * bits
        return {
            "problem": f"factor({N})",
            "encoding": f"O(log N) = O({bits})",
            "cells": cells_needed,
            "encode_steps": encode_steps,
        }

    elif problem_type == "sat":
        clauses = problem_params["clauses"]
        variables = problem_params["variables"]
        encode_steps = clauses + variables  # O(K + V)
        cells_needed = variables
        return {
            "problem": f"SAT({variables} vars, {clauses} clauses)",
            "encoding": f"O(K+V) = O({clauses}+{variables})",
            "cells": cells_needed,
            "encode_steps": encode_steps,
        }

    elif problem_type == "tsp":
        cities = problem_params["cities"]
        encode_steps = cities ** 2  # O(N^2)
        cells_needed = cities
        return {
            "problem": f"TSP({cities} cities)",
            "encoding": f"O(N^2) = O({cities ** 2})",
            "cells": cells_needed,
            "encode_steps": encode_steps,
        }

    return {"problem": problem_type, "encoding": "unknown"}


# --- thermal noise ---

def thermal_error_rate(delta_E_eV: float, temperature_K: float) -> float:
    """
    P_error = exp(-delta_E / kT)
    """
    kT = K_B * temperature_K
    if kT == 0:
        return 0.0
    return math.exp(-delta_E_eV / kT)


def bits_per_cell(temperature_K: float) -> float:
    """
    Estimate usable bits per cell at given temperature.

    At 300K: ~3-4 bits; at 4K: ~10 bits (from spec).
    """
    kT = K_B * temperature_K
    if kT == 0:
        return float("inf")
    # bits ~ -log2(P_error) for typical energy gap
    typical_gap = 0.1  # eV
    p_err = math.exp(-typical_gap / kT)
    if p_err >= 1.0:
        return 0.0
    return -math.log2(p_err) if p_err > 0 else float("inf")


# --- decoherence ---

@dataclass
class DecoherenceSpec:
    """Decoherence time for a quantum technology."""
    technology: str
    t2_seconds: float  # T2 coherence time

    @property
    def t2_label(self) -> str:
        if self.t2_seconds >= 1e-3:
            return f"{self.t2_seconds * 1e3:.1f} ms"
        elif self.t2_seconds >= 1e-6:
            return f"{self.t2_seconds * 1e6:.0f} us"
        else:
            return f"{self.t2_seconds * 1e9:.0f} ns"


DECOHERENCE_SPECS = [
    DecoherenceSpec("superconducting qubit", 100e-6),
    DecoherenceSpec("trapped ion", 1e-3),
    DecoherenceSpec("quantum dot", 1e-6),
    DecoherenceSpec("molecular spin", 1e-9),
]


# --- problem encodability scoring ---

def encodability_score(
    constraint_locality: float,
    symmetry_exploitability: float,
    landscape_uniqueness: float,
    state_continuity: float,
    adversarial_resistance: float,
) -> Dict:
    """
    Score how well a problem maps to geometric encoding.

    Each factor is 0-1. Total is weighted average.
    """
    weights = {
        "constraint_locality": 0.25,
        "symmetry_exploitability": 0.25,
        "landscape_uniqueness": 0.20,
        "state_continuity": 0.15,
        "adversarial_resistance": 0.15,
    }

    scores = {
        "constraint_locality": constraint_locality,
        "symmetry_exploitability": symmetry_exploitability,
        "landscape_uniqueness": landscape_uniqueness,
        "state_continuity": state_continuity,
        "adversarial_resistance": adversarial_resistance,
    }

    total = sum(scores[k] * weights[k] for k in weights)

    return {
        "scores": scores,
        "total": round(total, 4),
        "encodable": total > 0.6,
    }


# --- intellectual honesty categories ---

HONESTY_CATEGORIES = {
    "PROVEN": [
        "Eigenvalue decomposition converges for Hermitian matrices",
        "Metropolis-Hastings satisfies detailed balance",
        "Octahedral group has 48 symmetry elements",
    ],
    "STRONGLY_SUPPORTED": [
        "FRET coupling scales as 1/r^6",
        "Fibonacci eigenvalues optimize energy landscape",
        "Thermal relaxation finds local minima",
    ],
    "PLAUSIBLE": [
        "Geometric encoding captures NP-hard structure",
        "Octahedral symmetry provides computational advantage",
        "Ground state corresponds to problem solution",
    ],
    "SPECULATIVE": [
        "P=NP via geometric collapse",
        "Consciousness emergence at phi > 3.0",
        "Physical constants from geometry",
    ],
    "UNTESTABLE": [
        "Reality manipulation via geometric transformation",
        "Consciousness as fundamental geometric property",
    ],
}


# --- testable predictions ---

PREDICTIONS = [
    {
        "prediction": "relaxation time independent of problem size for fixed cell count",
        "test": "vary N in factorization, measure wall-clock time",
        "falsifiable": True,
    },
    {
        "prediction": "energy gap scales as 1/sqrt(N) for factorization",
        "test": "compute gap for N=15,21,35,77,143 and fit",
        "falsifiable": True,
    },
    {
        "prediction": "octahedral (8-state) outperforms cubic (6-state)",
        "test": "compare convergence rates for same problem",
        "falsifiable": True,
    },
    {
        "prediction": "Fibonacci cell counts reduce error vs uniform counts",
        "test": "compare error rates with and without phi scaling",
        "falsifiable": True,
    },
]


if __name__ == "__main__":
    print("=" * 60)
    print("example-questions: limits, validation, and honest assessment")
    print("=" * 60)

    # encoding complexity
    print("\n--- encoding complexity ---")
    problems = [
        ("factorization", {"N": 143}),
        ("factorization", {"N": 1000003}),
        ("sat", {"clauses": 50, "variables": 20}),
        ("tsp", {"cities": 10}),
        ("tsp", {"cities": 100}),
    ]
    for ptype, params in problems:
        result = encoding_complexity(ptype, params)
        print(f"  {result['problem']:>30}: {result['encoding']:>20}, cells={result.get('cells', '?')}")

    # thermal limits
    print("\n--- thermal noise limits ---")
    print(f"  {'temp (K)':>10}  {'P_error (dE=0.1eV)':>20}  {'bits/cell':>10}")
    print("  " + "-" * 44)
    for T in [4.0, 20.0, 77.0, 150.0, 300.0]:
        p = thermal_error_rate(0.1, T)
        bits = bits_per_cell(T)
        print(f"  {T:>10.0f}  {p:>20.6e}  {bits:>10.1f}")

    # decoherence comparison
    print("\n--- decoherence times ---")
    for spec in DECOHERENCE_SPECS:
        print(f"  {spec.technology:>25}: T2 = {spec.t2_label}")

    # encodability scoring
    print("\n--- problem encodability scores ---")
    problems_enc = {
        "factorization": (0.9, 0.8, 0.9, 0.7, 0.6),
        "3-SAT": (0.6, 0.5, 0.7, 0.4, 0.3),
        "TSP": (0.7, 0.6, 0.5, 0.8, 0.5),
        "graph coloring": (0.8, 0.7, 0.6, 0.6, 0.4),
    }
    for name, params in problems_enc.items():
        result = encodability_score(*params)
        status = "YES" if result["encodable"] else "NO"
        print(f"  {name:>16}: score={result['total']:.3f}  encodable={status}")

    # intellectual honesty
    print("\n--- intellectual honesty assessment ---")
    for category, claims in HONESTY_CATEGORIES.items():
        print(f"\n  [{category}]")
        for claim in claims:
            print(f"    - {claim}")

    # testable predictions
    print("\n--- testable predictions ---")
    for i, pred in enumerate(PREDICTIONS, 1):
        print(f"  {i}. {pred['prediction']}")
        print(f"     test: {pred['test']}")

    print("\ndone.")
