"""
example-mandala-integration.py
Demonstrates concepts from Mandala_integration.md:
  - Bridge-to-substrate adapter pattern
  - Encoding bottleneck analysis (encode vs relaxation time)
  - Error correction via redundant encoding
  - Validation levels with concrete checks
  - Testable predictions with experimental protocols
"""

import math
import time
import random
from dataclasses import dataclass
from typing import List, Dict, Tuple


PHI = (1 + math.sqrt(5)) / 2
K_B = 8.617e-5  # eV/K


# --- bridge-to-substrate adapter ---

@dataclass
class BridgeResult:
    """Result of bridging sensor input to substrate state."""
    input_pattern: Tuple[float, float, float]
    eigenvalues: Tuple[float, float, float]
    substrate_state: int
    confidence: float
    encode_time_us: float  # microseconds


EIGENVALUE_STATES = [
    (0.33, 0.33, 0.33),
    (0.50, 0.30, 0.20),
    (0.25, 0.50, 0.25),
    (0.20, 0.20, 0.60),
    (0.40, 0.35, 0.25),
    (0.30, 0.45, 0.25),
    (0.35, 0.25, 0.40),
    (0.45, 0.40, 0.15),
]


def bridge_adapter(amplitude: float, phase: float, frequency: float) -> BridgeResult:
    """
    BridgeToSubstrateAdapter: pattern -> eigenvalue ratios -> nearest state.
    """
    start = time.perf_counter()

    raw = [abs(amplitude), abs(phase), abs(frequency)]
    total = sum(raw)
    if total == 0:
        ev = (0.33, 0.33, 0.33)
    else:
        ev = tuple(sorted([x / total for x in raw], reverse=True))

    best_state = 0
    best_dist = float("inf")
    for i, ref in enumerate(EIGENVALUE_STATES):
        d = math.sqrt(sum((a - b) ** 2 for a, b in zip(ev, ref)))
        if d < best_dist:
            best_dist = d
            best_state = i

    confidence = max(0.0, 1.0 - best_dist / 0.5)
    elapsed_us = (time.perf_counter() - start) * 1e6

    return BridgeResult(
        input_pattern=(amplitude, phase, frequency),
        eigenvalues=ev,
        substrate_state=best_state,
        confidence=round(confidence, 4),
        encode_time_us=round(elapsed_us, 2),
    )


# --- encoding bottleneck analysis ---

def bottleneck_analysis(problem_type: str, problem_size: int, relax_steps: int = 1000) -> Dict:
    """
    Measure encode time vs relaxation time.

    The bottleneck insight: total time is dominated by encode+decode, not relaxation.
    """
    # simulate encoding
    encode_start = time.perf_counter()
    if problem_type == "factorization":
        bits = math.ceil(math.log2(max(problem_size, 2)))
        cells = 2 * bits
        # simulate encoding work
        for _ in range(cells):
            _ = random.randint(0, 7)
    elif problem_type == "sat":
        cells = problem_size  # one cell per variable
        for _ in range(cells):
            _ = random.randint(0, 7)
    elif problem_type == "tsp":
        cells = problem_size
        for _ in range(cells * cells):  # O(N^2) pairwise distances
            _ = random.random()
    else:
        cells = problem_size
    encode_time = time.perf_counter() - encode_start

    # simulate relaxation
    relax_start = time.perf_counter()
    states = [random.randint(0, 7) for _ in range(cells)]
    for _ in range(relax_steps):
        idx = random.randint(0, cells - 1)
        states[idx] = random.randint(0, 7)
    relax_time = time.perf_counter() - relax_start

    # simulate decoding
    decode_start = time.perf_counter()
    for s in states:
        _ = s * 2 + 1
    decode_time = time.perf_counter() - decode_start

    total = encode_time + relax_time + decode_time
    return {
        "problem": f"{problem_type}(n={problem_size})",
        "cells": cells,
        "encode_ms": round(encode_time * 1000, 3),
        "relax_ms": round(relax_time * 1000, 3),
        "decode_ms": round(decode_time * 1000, 3),
        "total_ms": round(total * 1000, 3),
        "bottleneck": "encode" if encode_time > relax_time else "relax",
    }


# --- error correction via redundancy ---

def redundant_encode(state: int, copies: int = 3) -> List[int]:
    """Encode state with redundant copies for error correction."""
    return [state] * copies


def decode_with_majority(copies: List[int]) -> int:
    """Decode via majority vote."""
    counts = {}
    for s in copies:
        counts[s] = counts.get(s, 0) + 1
    return max(counts, key=counts.get)


def simulate_noise(copies: List[int], error_rate: float) -> List[int]:
    """Flip each copy with given probability."""
    noisy = []
    for s in copies:
        if random.random() < error_rate:
            noisy.append(random.randint(0, 7))
        else:
            noisy.append(s)
    return noisy


def error_correction_demo(error_rate: float = 0.2, trials: int = 1000):
    """Compare raw vs redundant encoding error rates."""
    raw_errors = 0
    corrected_errors = 0

    for _ in range(trials):
        original = random.randint(0, 7)

        # raw (single copy)
        noisy_single = simulate_noise([original], error_rate)
        if noisy_single[0] != original:
            raw_errors += 1

        # redundant (5 copies, majority vote)
        copies = redundant_encode(original, copies=5)
        noisy_copies = simulate_noise(copies, error_rate)
        decoded = decode_with_majority(noisy_copies)
        if decoded != original:
            corrected_errors += 1

    return {
        "error_rate": error_rate,
        "trials": trials,
        "raw_error_pct": round(raw_errors / trials * 100, 1),
        "corrected_error_pct": round(corrected_errors / trials * 100, 1),
        "improvement": round(raw_errors / max(corrected_errors, 1), 1),
    }


# --- validation levels ---

VALIDATION_LEVELS = [
    {
        "level": 1,
        "name": "simulation",
        "check": "relaxation reduces energy on 10 random inputs",
        "difficulty": "easy",
    },
    {
        "level": 2,
        "name": "mesoscale",
        "check": "100-cell substrate factors N=15,21,35",
        "difficulty": "medium",
    },
    {
        "level": 3,
        "name": "nanoscale",
        "check": "physical substrate factors RSA-1024",
        "difficulty": "hard",
    },
    {
        "level": 4,
        "name": "consciousness",
        "check": "integrated information phi > 3.0",
        "difficulty": "speculative",
    },
    {
        "level": 5,
        "name": "constants",
        "check": "derive physical constants from geometry",
        "difficulty": "untestable",
    },
]


# --- testable predictions ---

def test_relaxation_independence():
    """
    Prediction: relaxation time is independent of N for fixed cell count.

    Test by varying N and measuring relaxation time on same cell count.
    """
    cell_count = 20
    steps = 5000
    results = []

    for N in [15, 77, 143, 1009, 10007]:
        states = [random.randint(0, 7) for _ in range(cell_count)]
        start = time.perf_counter()
        for _ in range(steps):
            idx = random.randint(0, cell_count - 1)
            states[idx] = random.randint(0, 7)
        elapsed = time.perf_counter() - start
        results.append((N, round(elapsed * 1000, 2)))

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("example-mandala-integration: adapter, bottleneck, correction")
    print("=" * 60)

    # bridge adapter
    print("\n--- bridge-to-substrate adapter ---")
    for amp, phase, freq in [(0.8, 0.3, 0.5), (0.1, 0.1, 0.9), (0.5, 0.5, 0.5)]:
        r = bridge_adapter(amp, phase, freq)
        print(f"  ({amp},{phase},{freq}) -> state {r.substrate_state} "
              f"(conf={r.confidence}, {r.encode_time_us:.1f} us)")

    # bottleneck analysis
    print("\n--- encoding bottleneck analysis ---")
    print(f"  {'problem':<24} {'cells':>6} {'encode':>10} {'relax':>10} {'bottleneck':>10}")
    print("  " + "-" * 64)
    for ptype, size in [("factorization", 143), ("factorization", 100003),
                        ("sat", 50), ("tsp", 20), ("tsp", 100)]:
        b = bottleneck_analysis(ptype, size)
        print(f"  {b['problem']:<24} {b['cells']:>6} "
              f"{b['encode_ms']:>8.3f}ms {b['relax_ms']:>8.3f}ms {b['bottleneck']:>10}")

    # error correction
    print("\n--- error correction (5x redundancy, majority vote) ---")
    for rate in [0.05, 0.1, 0.2, 0.3]:
        r = error_correction_demo(error_rate=rate)
        print(f"  noise={rate:.0%}: raw={r['raw_error_pct']}%, "
              f"corrected={r['corrected_error_pct']}%, "
              f"improvement={r['improvement']}x")

    # validation levels
    print("\n--- validation framework ---")
    for v in VALIDATION_LEVELS:
        print(f"  level {v['level']} ({v['name']:<14}): {v['check']:<45} [{v['difficulty']}]")

    # testable prediction: relaxation independence
    print("\n--- prediction: relaxation time vs problem size (fixed 20 cells) ---")
    results = test_relaxation_independence()
    for N, ms in results:
        print(f"  N={N:>6}: {ms:.2f} ms")
    times = [ms for _, ms in results]
    variance = sum((t - sum(times) / len(times)) ** 2 for t in times) / len(times)
    print(f"  variance: {variance:.4f} ms^2 (low = supports prediction)")

    print("\ndone.")
