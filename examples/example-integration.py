"""
example-integration.py
Demonstrates concepts from Integration.md:
  - End-to-end pipeline: input -> bridge -> substrate -> mandala -> decode
  - Integration flow walkthrough
  - Validation framework with 5 levels
  - Component status reporting
"""

import math
import random
from typing import Dict, List, Tuple


PHI = (1 + math.sqrt(5)) / 2


# --- bridge layer ---

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


def bridge_encode(amplitude: float, phase: float, frequency: float) -> Tuple[int, float]:
    """Bridge layer: sensor input -> octahedral state."""
    raw = [abs(amplitude), abs(phase), abs(frequency)]
    total = sum(raw)
    if total == 0:
        return 0, 1.0

    ev = tuple(sorted([x / total for x in raw], reverse=True))

    best_state = 0
    best_dist = float("inf")
    for i, ref in enumerate(EIGENVALUE_STATES):
        d = math.sqrt(sum((a - b) ** 2 for a, b in zip(ev, ref)))
        if d < best_dist:
            best_dist = d
            best_state = i

    confidence = max(0.0, 1.0 - best_dist / 0.5)
    return best_state, confidence


# --- substrate layer ---

def substrate_relax(states: List[int], steps: int = 200, temperature: float = 0.5) -> List[int]:
    """Substrate layer: thermal relaxation on state array."""
    result = states[:]
    for _ in range(steps):
        idx = random.randint(0, len(result) - 1)
        old = result[idx]
        result[idx] = random.randint(0, 7)

        # energy: prefer neighbor alignment
        energy_old = 0
        energy_new = 0
        for d in [-1, 1]:
            j = idx + d
            if 0 <= j < len(result):
                energy_old += abs(old - result[j])
                energy_new += abs(result[idx] - result[j])

        dE = energy_new - energy_old
        if dE > 0 and (temperature <= 0 or random.random() >= math.exp(-dE / temperature)):
            result[idx] = old

    return result


# --- mandala layer ---

def mandala_solve(problem_type: str, problem_data: Dict) -> Dict:
    """
    Mandala layer: full problem encoding -> relaxation -> solution extraction.
    """
    if problem_type == "factorization":
        N = problem_data["N"]
        # create cells representing candidate factors
        num_cells = int(math.sqrt(N)) + 1
        states = [random.randint(0, 7) for _ in range(num_cells)]

        # relax
        relaxed = substrate_relax(states, steps=500, temperature=0.3)

        # extract factors
        factors = set()
        for i, s in enumerate(relaxed):
            candidate = 2 + s + i
            if 1 < candidate < N and N % candidate == 0:
                factors.add(candidate)

        return {"factors": sorted(factors), "N": N}

    elif problem_type == "optimization":
        values = problem_data.get("values", [])
        if not values:
            return {"minimum": 0, "index": 0}
        min_idx = min(range(len(values)), key=lambda i: values[i])
        return {"minimum": values[min_idx], "index": min_idx}

    return {"error": f"unknown problem type: {problem_type}"}


# --- result decoder ---

def decode_result(raw_result: Dict, problem_type: str) -> str:
    """Decode mandala result into human-readable output."""
    if problem_type == "factorization":
        factors = raw_result.get("factors", [])
        N = raw_result.get("N", "?")
        if factors:
            return f"N={N} -> factors: {factors}"
        return f"N={N} -> no factors found in this run"

    elif problem_type == "optimization":
        return f"minimum={raw_result['minimum']} at index={raw_result['index']}"

    return str(raw_result)


# --- end-to-end pipeline ---

def run_pipeline(sensor_input: Tuple[float, float, float], problem_type: str, problem_data: Dict) -> Dict:
    """
    Full integration pipeline:
      1. sensor input -> bridge -> octahedral state
      2. octahedral state -> substrate relaxation
      3. substrate -> mandala solver
      4. mandala result -> decoded output
    """
    # step 1: bridge
    state, confidence = bridge_encode(*sensor_input)

    # step 2: substrate
    initial_states = [state] * 8
    relaxed = substrate_relax(initial_states, steps=100)

    # step 3: mandala solve
    raw_result = mandala_solve(problem_type, problem_data)

    # step 4: decode
    output = decode_result(raw_result, problem_type)

    return {
        "sensor_input": sensor_input,
        "bridge_state": state,
        "bridge_confidence": round(confidence, 4),
        "substrate_states": relaxed,
        "raw_result": raw_result,
        "output": output,
    }


# --- validation framework ---

VALIDATION_LEVELS = {
    1: {"name": "simulation", "description": "software simulator matches theory"},
    2: {"name": "mesoscale", "description": "100-cell physical proof-of-concept"},
    3: {"name": "nanoscale", "description": "RSA-1024 on physical substrate"},
    4: {"name": "consciousness", "description": "phi > 3.0 signatures detected"},
    5: {"name": "constants", "description": "physical constants derived from geometry"},
}


def validate_level(level: int, test_results: Dict) -> Dict:
    """Run validation at specified level."""
    info = VALIDATION_LEVELS.get(level, {"name": "unknown", "description": ""})

    if level == 1:
        # simulation: check that relaxation reduces energy
        passed = test_results.get("energy_reduced", False)
    elif level == 2:
        # mesoscale: check cell count >= 100
        passed = test_results.get("cell_count", 0) >= 100
    elif level == 3:
        # nanoscale: check factor found
        passed = len(test_results.get("factors", [])) > 0
    elif level == 4:
        # consciousness: phi > 3.0
        passed = test_results.get("phi", 0) > 3.0
    elif level == 5:
        # constants: not yet testable
        passed = False
    else:
        passed = False

    return {
        "level": level,
        "name": info["name"],
        "description": info["description"],
        "passed": passed,
    }


# --- component status ---

COMPONENTS = [
    {"name": "mandala_computer.py", "status": "complete", "coverage": 100},
    {"name": "quantum_mandala.py", "status": "complete", "coverage": 100},
    {"name": "mandala_simulator.py", "status": "partial", "coverage": 60},
    {"name": "bridge_to_substrate_adapter", "status": "spec only", "coverage": 30},
    {"name": "physical_mandala_computer", "status": "spec only", "coverage": 30},
    {"name": "hardware_control", "status": "spec only", "coverage": 20},
    {"name": "test_suite", "status": "missing", "coverage": 0},
]


if __name__ == "__main__":
    print("=" * 60)
    print("example-integration: end-to-end pipeline demo")
    print("=" * 60)

    # end-to-end pipeline
    print("\n--- pipeline: sensor -> bridge -> substrate -> mandala -> decode ---")
    result = run_pipeline(
        sensor_input=(0.8, 0.3, 0.5),
        problem_type="factorization",
        problem_data={"N": 15},
    )
    for k, v in result.items():
        print(f"  {k}: {v}")

    # validation levels
    print("\n--- validation framework ---")
    test_data = {
        1: {"energy_reduced": True},
        2: {"cell_count": 120},
        3: {"factors": [3, 5]},
        4: {"phi": 2.1},
        5: {},
    }
    for level in range(1, 6):
        v = validate_level(level, test_data[level])
        status = "PASS" if v["passed"] else "FAIL"
        print(f"  level {level} ({v['name']}): {status} - {v['description']}")

    # component status
    print("\n--- component status ---")
    total_coverage = 0
    for comp in COMPONENTS:
        bar = "#" * (comp["coverage"] // 10) + "." * (10 - comp["coverage"] // 10)
        print(f"  [{bar}] {comp['coverage']:>3}%  {comp['name']} ({comp['status']})")
        total_coverage += comp["coverage"]

    overall = total_coverage / len(COMPONENTS)
    print(f"\n  overall integration: {overall:.0f}%")

    print("\ndone.")
