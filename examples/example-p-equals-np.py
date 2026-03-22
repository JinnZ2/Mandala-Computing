"""
example-p-equals-np.py
Demonstrates concepts from P=np-hypothesis.md:
  - Golden-ratio memory amplification: A = phi^(depth * fold)
  - P=NP convergence factor: A / log(problem_size)
  - Mandala step count vs classical step count
  - Fractal depth scaling analysis
"""

import math


PHI = (1 + math.sqrt(5)) / 2


def memory_amplification(golden_depth: int, dimensional_fold: int) -> float:
    """
    Compute memory amplification factor.

    A = phi^(golden_depth * dimensional_fold)
    """
    return PHI ** (golden_depth * dimensional_fold)


def pnp_convergence_factor(amplification: float, problem_size: int) -> float:
    """
    P=NP convergence score.

    score = amplification / log(problem_size)

    When score > 1000, polynomial-time behavior is symbolically observed.
    """
    return amplification / math.log(problem_size)


def mandala_vs_classical_steps(problem_size: int) -> dict:
    """
    Compare classical O(n^2) steps with mandala O(log_phi(n)) steps.
    """
    classical = problem_size ** 2
    mandala = math.log(problem_size) / math.log(PHI)
    speedup = classical / mandala if mandala > 0 else float("inf")

    return {
        "problem_size": problem_size,
        "classical_steps": classical,
        "mandala_steps": round(mandala, 2),
        "speedup": round(speedup, 1),
    }


def scan_depth_and_fold():
    """
    Show how golden_depth and dimensional_fold affect convergence score.
    """
    print("\nconvergence score (problem_size=1000)")
    print(f"{'depth':>6} {'fold':>6} {'amplification':>16} {'score':>14} {'status':>10}")
    print("-" * 56)

    for depth in [3, 5, 7, 10]:
        for fold in [2, 3, 5, 7]:
            amp = memory_amplification(depth, fold)
            score = pnp_convergence_factor(amp, 1000)
            status = "CONVERGE" if score > 1000 else "below"
            print(f"{depth:>6} {fold:>6} {amp:>16.2f} {score:>14.2f} {status:>10}")


def speedup_table():
    """
    Show mandala vs classical step counts for various problem sizes.
    """
    print("\nmandala vs classical steps")
    print(f"{'n':>10} {'classical':>14} {'mandala':>10} {'speedup':>12}")
    print("-" * 50)

    for n in [10, 100, 1000, 10_000, 100_000, 1_000_000]:
        r = mandala_vs_classical_steps(n)
        print(
            f"{r['problem_size']:>10,} "
            f"{r['classical_steps']:>14,} "
            f"{r['mandala_steps']:>10} "
            f"{r['speedup']:>12,.1f}x"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("example-p-equals-np: convergence scoring and speedup analysis")
    print("=" * 60)

    scan_depth_and_fold()
    speedup_table()

    # single demo
    depth, fold = 5, 3
    amp = memory_amplification(depth, fold)
    score = pnp_convergence_factor(amp, 1000)
    print(f"\ndemo: depth={depth}, fold={fold}")
    print(f"  amplification = phi^{depth * fold} = {amp:.4f}")
    print(f"  convergence score = {score:.4f}")
    print(f"  symbolic P=NP: {'yes' if score > 1000 else 'no'}")

    print("\ndone.")
