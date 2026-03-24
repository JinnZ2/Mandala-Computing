"""
example-consumer-hardware.py
Demonstrates concepts from Consumer-hardware.md:
  - ConsumerLimits: typical laptop specs (8-core, 3GHz, 16GB)
  - OptimalConfig: max 1000 cells, max 5 layers, float32 precision
  - Pre-computed eigenvalue lookup tables
  - Fast encoding: audio via FFT, images via color analysis, text via char frequency
  - Simulated annealing within time budget
  - Progressive refinement
  - Mobile optimization profile
"""

import math
import time
import random
from dataclasses import dataclass
from typing import List, Dict


PHI = (1 + math.sqrt(5)) / 2


@dataclass
class ConsumerLimits:
    """Typical consumer laptop constraints."""
    cpu_cores: int = 8
    clock_ghz: float = 3.0
    ram_gb: int = 16
    label: str = "laptop"


@dataclass
class OptimalConfig:
    """Optimized config for consumer hardware."""
    max_cells: int = 1000
    max_layers: int = 5
    precision: str = "float32"
    time_budget_sec: float = 5.0


MOBILE_CONFIG = OptimalConfig(
    max_cells=100,
    max_layers=3,
    precision="float32",
    time_budget_sec=2.0,
)


def build_eigenvalue_lookup(levels: int = 256) -> List[float]:
    """
    Pre-compute eigenvalue lookup table.

    Avoids repeated phi^i calculations at runtime.
    """
    return [PHI ** (i / levels) for i in range(levels)]


def encode_text(text: str, max_states: int = 8) -> List[int]:
    """
    Fast text encoding via character frequency analysis.

    Maps character frequency distribution to octahedral states.
    """
    if not text:
        return []

    freq = {}
    for ch in text.lower():
        if ch.isalpha():
            freq[ch] = freq.get(ch, 0) + 1

    if not freq:
        return [0]

    total = sum(freq.values())
    sorted_chars = sorted(freq.items(), key=lambda x: -x[1])

    states = []
    for ch, count in sorted_chars[:max_states]:
        ratio = count / total
        state = min(7, int(ratio * max_states * 2))
        states.append(state)

    return states


def encode_audio_fft(samples: List[float], sample_rate: int = 44100) -> List[int]:
    """
    Fast audio encoding via simplified FFT.

    Extracts top-3 frequency bins and maps to octahedral states.
    """
    n = len(samples)
    if n == 0:
        return [0]

    # simplified DFT for top frequencies (not full FFT, just magnitude estimate)
    magnitudes = []
    for k in range(min(n // 2, 64)):
        real_sum = sum(samples[i] * math.cos(2 * math.pi * k * i / n) for i in range(n))
        imag_sum = sum(samples[i] * math.sin(2 * math.pi * k * i / n) for i in range(n))
        magnitudes.append(math.sqrt(real_sum ** 2 + imag_sum ** 2))

    # top 3 bins
    indexed = sorted(enumerate(magnitudes), key=lambda x: -x[1])[:3]
    states = [min(7, int(mag / (max(magnitudes) + 1e-9) * 8)) for _, mag in indexed]

    return states


def encode_image_color(pixels_rgb: List[tuple]) -> List[int]:
    """
    Fast image encoding via mean color analysis.

    Compute mean R, G, B and map to octahedral state.
    """
    if not pixels_rgb:
        return [0]

    n = len(pixels_rgb)
    mean_r = sum(p[0] for p in pixels_rgb) / n
    mean_g = sum(p[1] for p in pixels_rgb) / n
    mean_b = sum(p[2] for p in pixels_rgb) / n

    total = mean_r + mean_g + mean_b
    if total == 0:
        return [0]

    ratios = sorted([mean_r / total, mean_g / total, mean_b / total], reverse=True)

    # map dominant ratio to state
    state = min(7, int(ratios[0] * 16))
    return [state]


def simulated_annealing(
    num_cells: int,
    steps: int = 100,
    initial_temp: float = 1.0,
) -> Dict:
    """
    Lightweight simulated annealing for consumer hardware.

    100 steps with random state exploration (from spec).
    """
    states = [random.randint(0, 7) for _ in range(num_cells)]

    def energy():
        e = 0.0
        for i in range(len(states) - 1):
            e += abs(states[i] - states[i + 1]) / 7.0
        return e

    best_energy = energy()
    best_states = states[:]

    for step in range(steps):
        temp = initial_temp * (1.0 - step / steps)
        idx = random.randint(0, num_cells - 1)
        old = states[idx]
        states[idx] = random.randint(0, 7)
        new_e = energy()

        dE = new_e - best_energy
        if dE < 0 or (temp > 0 and random.random() < math.exp(-dE / max(temp, 1e-9))):
            if new_e < best_energy:
                best_energy = new_e
                best_states = states[:]
        else:
            states[idx] = old

    return {
        "best_energy": round(best_energy, 4),
        "best_states": best_states,
        "steps": steps,
    }


def progressive_refinement(
    num_cells: int,
    time_budget_sec: float = 5.0,
) -> Dict:
    """
    Improve result within a time budget.

    Runs successive annealing rounds until time runs out.
    """
    start = time.time()
    rounds = 0
    best = simulated_annealing(num_cells, steps=50)

    while time.time() - start < time_budget_sec:
        candidate = simulated_annealing(num_cells, steps=50)
        rounds += 1
        if candidate["best_energy"] < best["best_energy"]:
            best = candidate

    elapsed = time.time() - start
    return {
        **best,
        "rounds": rounds,
        "elapsed_sec": round(elapsed, 3),
    }


if __name__ == "__main__":
    print("=" * 60)
    print("example-consumer-hardware: optimized geometric computing")
    print("=" * 60)

    # hardware profiles
    laptop = ConsumerLimits()
    print(f"\nhardware: {laptop.label} ({laptop.cpu_cores} cores, {laptop.clock_ghz} GHz, {laptop.ram_gb} GB)")

    desktop_config = OptimalConfig()
    print(f"config: max_cells={desktop_config.max_cells}, layers={desktop_config.max_layers}, budget={desktop_config.time_budget_sec}s")
    print(f"mobile: max_cells={MOBILE_CONFIG.max_cells}, layers={MOBILE_CONFIG.max_layers}, budget={MOBILE_CONFIG.time_budget_sec}s")

    # lookup table
    print("\n--- eigenvalue lookup table (first 10 of 256) ---")
    lut = build_eigenvalue_lookup(256)
    for i in range(0, 10):
        print(f"  [{i:>3}] = {lut[i]:.6f}")

    # text encoding
    print("\n--- text encoding ---")
    for text in ["hello world", "mandala computing", "octahedral symmetry"]:
        states = encode_text(text)
        print(f"  '{text}' -> {states}")

    # audio encoding
    print("\n--- audio encoding (synthetic sine wave) ---")
    sr = 1000
    samples = [math.sin(2 * math.pi * 100 * t / sr) + 0.5 * math.sin(2 * math.pi * 250 * t / sr) for t in range(256)]
    audio_states = encode_audio_fft(samples, sr)
    print(f"  sine(100Hz) + 0.5*sine(250Hz) -> {audio_states}")

    # image encoding
    print("\n--- image encoding ---")
    red_pixels = [(200, 50, 50)] * 100
    green_pixels = [(50, 200, 50)] * 100
    mixed_pixels = [(150, 100, 80)] * 100
    for label, px in [("red", red_pixels), ("green", green_pixels), ("mixed", mixed_pixels)]:
        img_states = encode_image_color(px)
        print(f"  {label} image -> {img_states}")

    # simulated annealing
    print("\n--- simulated annealing (20 cells, 100 steps) ---")
    result = simulated_annealing(20, steps=100)
    print(f"  best energy: {result['best_energy']}")
    print(f"  states: {result['best_states']}")

    # progressive refinement
    print("\n--- progressive refinement (20 cells, 2s budget) ---")
    result = progressive_refinement(20, time_budget_sec=2.0)
    print(f"  best energy: {result['best_energy']}")
    print(f"  rounds: {result['rounds']}")
    print(f"  elapsed: {result['elapsed_sec']}s")

    print("\ndone.")
