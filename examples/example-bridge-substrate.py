"""
example-bridge-substrate.py
Demonstrates concepts from Bridge-substrate.md:
  - Universal pattern-to-octahedral-state mapping
  - Feature extraction: amplitude, phase, frequency -> eigenvalue ratios
  - Euclidean distance matching in eigenvalue space
  - Confidence scoring and Fibonacci alignment
  - Specialized adapters: sound, light/color, magnetic, gravity
  - Multi-modal fusion
"""

import math
import random
from typing import Tuple, List


PHI = (1 + math.sqrt(5)) / 2

# 8 canonical eigenvalue states (from spec)
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


def euclidean_distance(a: Tuple[float, ...], b: Tuple[float, ...]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def match_to_state(eigenvalues: Tuple[float, float, float]) -> Tuple[int, float]:
    """
    Find nearest octahedral state by Euclidean distance in eigenvalue space.

    Returns (state_index, confidence).
    Confidence = 1.0 - (distance / 0.5), clamped to [0, 1].
    """
    best_state = 0
    best_dist = float("inf")

    for i, ev in enumerate(EIGENVALUE_STATES):
        d = euclidean_distance(eigenvalues, ev)
        if d < best_dist:
            best_dist = d
            best_state = i

    confidence = max(0.0, 1.0 - best_dist / 0.5)
    return best_state, confidence


def fibonacci_alignment(eigenvalues: Tuple[float, float, float]) -> float:
    """
    Measure how well eigenvalue ratios follow golden ratio phi.

    Returns score in [0, 1] where 1.0 = perfect phi alignment.
    """
    sorted_ev = sorted(eigenvalues, reverse=True)
    if sorted_ev[1] == 0:
        return 0.0

    ratio = sorted_ev[0] / sorted_ev[1]
    error = abs(ratio - PHI) / PHI
    return max(0.0, 1.0 - error)


def extract_features(amplitude: float, phase: float, frequency: float) -> Tuple[float, float, float]:
    """
    Convert raw sensor readings to normalized eigenvalue ratios.

    Ratios are normalized to [0, 1] and sorted descending.
    """
    raw = [amplitude, phase, frequency]
    total = sum(abs(x) for x in raw)
    if total == 0:
        return (0.33, 0.33, 0.33)

    normalized = sorted([abs(x) / total for x in raw], reverse=True)
    return (normalized[0], normalized[1], normalized[2])


# --- specialized adapters ---

def sound_to_state(frequency_hz: float, amplitude_db: float, phase_rad: float) -> dict:
    """
    SoundToSubstrate adapter.

    Maps audio features (dominant frequency, amplitude, phase) to octahedral state.
    """
    ev = extract_features(amplitude_db / 100.0, phase_rad / math.pi, frequency_hz / 20000.0)
    state, confidence = match_to_state(ev)
    fib = fibonacci_alignment(ev)

    return {
        "input": {"frequency_hz": frequency_hz, "amplitude_db": amplitude_db, "phase_rad": phase_rad},
        "eigenvalues": ev,
        "state": state,
        "confidence": round(confidence, 4),
        "fibonacci_alignment": round(fib, 4),
    }


def color_to_state(r: int, g: int, b: int) -> dict:
    """
    LightToSubstrate adapter.

    Maps RGB color values to octahedral state by treating channels as eigenvalue ratios.
    """
    total = r + g + b
    if total == 0:
        ev = (0.33, 0.33, 0.33)
    else:
        ev = tuple(sorted([r / total, g / total, b / total], reverse=True))

    state, confidence = match_to_state(ev)
    fib = fibonacci_alignment(ev)

    return {
        "input": {"r": r, "g": g, "b": b},
        "eigenvalues": tuple(round(x, 4) for x in ev),
        "state": state,
        "confidence": round(confidence, 4),
        "fibonacci_alignment": round(fib, 4),
    }


def magnetic_to_state(bx: float, by: float, bz: float) -> dict:
    """
    MagneticToSubstrate adapter.

    Maps 3-axis magnetic field readings to octahedral state.
    """
    ev = extract_features(bx, by, bz)
    state, confidence = match_to_state(ev)

    return {
        "input": {"bx": bx, "by": by, "bz": bz},
        "eigenvalues": ev,
        "state": state,
        "confidence": round(confidence, 4),
    }


def gravity_to_state(gx: float, gy: float, gz: float) -> dict:
    """
    GravityToSubstrate adapter.

    Maps accelerometer readings to octahedral state.
    """
    ev = extract_features(gx, gy, gz)
    state, confidence = match_to_state(ev)

    return {
        "input": {"gx": gx, "gy": gy, "gz": gz},
        "eigenvalues": ev,
        "state": state,
        "confidence": round(confidence, 4),
    }


def fuse_multimodal(readings: List[Tuple[float, float, float]], weights: List[float] = None) -> dict:
    """
    Multi-modal fusion: weighted average of eigenvalues, then match.
    """
    if weights is None:
        weights = [1.0] * len(readings)

    total_weight = sum(weights)
    fused = [0.0, 0.0, 0.0]

    for (e1, e2, e3), w in zip(readings, weights):
        fused[0] += e1 * w / total_weight
        fused[1] += e2 * w / total_weight
        fused[2] += e3 * w / total_weight

    ev = tuple(fused)
    state, confidence = match_to_state(ev)

    return {
        "fused_eigenvalues": tuple(round(x, 4) for x in ev),
        "state": state,
        "confidence": round(confidence, 4),
    }


if __name__ == "__main__":
    print("=" * 60)
    print("example-bridge-substrate: sensor-to-octahedral adapters")
    print("=" * 60)

    # eigenvalue state table
    print("\ncanonical eigenvalue states")
    for i, (e1, e2, e3) in enumerate(EIGENVALUE_STATES):
        fib = fibonacci_alignment((e1, e2, e3))
        print(f"  state {i}: ({e1:.2f}, {e2:.2f}, {e3:.2f})  fib={fib:.3f}")

    # sound adapter
    print("\n--- sound adapter ---")
    for freq, amp, phase in [(440, 80, 0.5), (1000, 60, 1.2), (8000, 40, 2.8)]:
        r = sound_to_state(freq, amp, phase)
        print(f"  {freq:>5} Hz, {amp} dB -> state {r['state']} (conf={r['confidence']}, fib={r['fibonacci_alignment']})")

    # color adapter
    print("\n--- color adapter ---")
    for r, g, b in [(255, 0, 0), (0, 255, 0), (0, 0, 255), (128, 128, 128), (200, 100, 50)]:
        result = color_to_state(r, g, b)
        print(f"  RGB({r:>3},{g:>3},{b:>3}) -> state {result['state']} (conf={result['confidence']})")

    # magnetic adapter
    print("\n--- magnetic adapter ---")
    for bx, by, bz in [(50.0, 0.0, 0.0), (25.0, 25.0, 0.0), (10.0, 10.0, 10.0)]:
        result = magnetic_to_state(bx, by, bz)
        print(f"  B=({bx:.0f},{by:.0f},{bz:.0f}) -> state {result['state']} (conf={result['confidence']})")

    # multi-modal fusion
    print("\n--- multi-modal fusion ---")
    sound_ev = extract_features(0.8, 0.5, 0.2)
    color_ev = (0.5, 0.3, 0.2)
    mag_ev = extract_features(30.0, 15.0, 5.0)

    fused = fuse_multimodal([sound_ev, color_ev, mag_ev], weights=[1.0, 0.5, 0.8])
    print(f"  sound={sound_ev}, color={color_ev}, magnetic={mag_ev}")
    print(f"  fused -> state {fused['state']} (conf={fused['confidence']})")

    print("\ndone.")
