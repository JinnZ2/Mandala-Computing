"""
edge4_sat_scaling.py — does the coarse-to-fine (holographic) path change the
GROWTH RATE of search cost on 3-SAT, or only the constant?

CC0. Co-authored. Measured, not illustrative: every number this script prints
comes from running the solvers below on seeded random instances.

Edge 4 of the P=NP hypothesis glyph (see P=np-hypothesis.md, Note 2026-10-27):
self-similar coarse->fine structure as a shortcut through the landscape.
This script measures it the only way growth can be measured: cost per
problem size, across sizes, with classical references run the same way.

Problem: uniform random 3-SAT at clause/variable ratio 4.26 (near the
satisfiability threshold, where random instances are hardest), filtered to
satisfiable instances by an exact DPLL solver.

Cost unit: one candidate-assignment evaluation.
  - brute force   : expected evaluations in random enumeration order,
                    (2^n + 1) / (S + 1), S = exact solution count
  - DPLL          : search nodes (decisions + propagations) to first solution
  - WalkSAT       : flips to first solution (p = 0.5 noise)
  - mandala anneal: MandalaComputer.compute_total_energy() calls until the
                    first satisfying state (engine's own Metropolis moves)
  - holographic   : HolographicMandala.compute_total_energy() calls for one
                    full holographic_solve(); success = final state satisfies

Scope (stated so the readout is not over-read):
  - n <= 28 (brute-force counting n <= 24) because the engine's cell count is fixed by golden_depth
    (depth 5 = 24 cells, depth 6 = 41) and cost per energy call grows with m.
  - Variable i maps to cell i-1; extra cells exist but do not enter the
    clause check (engine behavior, recorded not changed).
  - Small n can only show growth TRENDS. It cannot establish asymptotic
    complexity. A changed slope would be a candidate for larger runs, not a
    result about P vs NP.

Run:  python experiments/edge4_sat_scaling.py [--quick]
Writes experiments/edge4_sat_scaling_results.json
"""

import contextlib
import io
import json
import math
import os
import random
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402

from mandala_computer import MandalaComputer, ProblemType  # noqa: E402
from holographic_mandala import HolographicMandala  # noqa: E402

ALPHA = 4.26
BRUTE_MAX_N = 24  # exact solution counting gets slow past this


# --------------------------------------------------------------------------
# instances
# --------------------------------------------------------------------------

def random_3sat(n, rng):
    m = int(round(ALPHA * n))
    clauses = []
    for _ in range(m):
        vs = rng.sample(range(1, n + 1), 3)
        clauses.append([v if rng.random() < 0.5 else -v for v in vs])
    return clauses


def satisfies(clauses, assign):
    """assign: dict var -> bool"""
    for c in clauses:
        if not any((lit > 0) == assign[abs(lit)] for lit in c):
            return False
    return True


def unsat_count(clauses, assign):
    return sum(1 for c in clauses if not any((lit > 0) == assign[abs(lit)] for lit in c))


# --------------------------------------------------------------------------
# DPLL (first solution, node count) and #SAT (exact count)
# --------------------------------------------------------------------------

def _simplify(clauses, lit):
    out = []
    for c in clauses:
        if lit in c:
            continue
        if -lit in c:
            c = [x for x in c if x != -lit]
            if not c:
                return None
        out.append(c)
    return out


def dpll(clauses, assign, counter):
    # unit propagation
    while True:
        unit = next((c[0] for c in clauses if len(c) == 1), None)
        if unit is None:
            break
        counter[0] += 1
        assign = dict(assign)
        assign[abs(unit)] = unit > 0
        clauses = _simplify(clauses, unit)
        if clauses is None:
            return None
    if not clauses:
        return assign
    # branch on most frequent variable
    freq = {}
    for c in clauses:
        for x in c:
            freq[abs(x)] = freq.get(abs(x), 0) + 1
    v = max(freq, key=freq.get)
    for lit in (v, -v):
        counter[0] += 1
        sub = _simplify(clauses, lit)
        if sub is None:
            continue
        a = dict(assign)
        a[v] = lit > 0
        r = dpll(sub, a, counter)
        if r is not None:
            return r
    return None


def count_solutions(clauses, n):
    def rec(cl, free):
        if cl is None:
            return 0
        if not cl:
            return 2 ** free
        v = abs(cl[0][0])
        return rec(_simplify(cl, v), free - 1) + rec(_simplify(cl, -v), free - 1)
    return rec([list(c) for c in clauses], n)


# --------------------------------------------------------------------------
# WalkSAT
# --------------------------------------------------------------------------

def walksat(clauses, n, rng, max_flips, p=0.5):
    assign = {v: rng.random() < 0.5 for v in range(1, n + 1)}
    for flips in range(max_flips):
        unsat = [c for c in clauses if not any((lit > 0) == assign[abs(lit)] for lit in c)]
        if not unsat:
            return flips
        c = rng.choice(unsat)
        if rng.random() < p:
            v = abs(rng.choice(c))
        else:
            best, v = None, None
            for lit in c:
                x = abs(lit)
                assign[x] = not assign[x]
                b = unsat_count(clauses, assign)
                assign[x] = not assign[x]
                if best is None or b < best:
                    best, v = b, x
        assign[v] = not assign[v]
    return None


# --------------------------------------------------------------------------
# Mandala engine runs (instrumented, quiet)
# --------------------------------------------------------------------------

def depth_for(n):
    d = 1
    while True:
        with contextlib.redirect_stdout(io.StringIO()):
            mc = MandalaComputer(golden_depth=d)
            mc.bloom_mandala()
        if mc.num_cells >= n:
            return d
        d += 1


def _cells_assign(engine, n):
    return {v: engine.cells[v - 1].state >= 4 for v in range(1, n + 1)}


def mandala_anneal(clauses, n, depth, budget, seed):
    """Engine's own Metropolis moves under an exponential schedule; cost =
    energy evaluations until the first satisfying state (first hit)."""
    np.random.seed(seed)
    with contextlib.redirect_stdout(io.StringIO()):
        mc = MandalaComputer(golden_depth=depth)
        mc.encode_sat(clauses)
    calls = [0]
    orig = mc.compute_total_energy

    def counted():
        calls[0] += 1
        return orig()
    mc.compute_total_energy = counted
    steps = budget // 2  # relax_step evaluates energy twice
    T0, T1 = 2.0, 0.01
    for s in range(steps):
        mc.temperature = T0 * (T1 / T0) ** (s / max(steps - 1, 1))
        mc.relax_step()
        if satisfies(clauses, _cells_assign(mc, n)):
            return calls[0]
    return None


def holographic(clauses, n, depth, steps_per_scale, seed):
    np.random.seed(seed)
    with contextlib.redirect_stdout(io.StringIO()):
        hm = HolographicMandala(golden_depth=depth)
    calls = [0]
    orig = hm.compute_total_energy

    def counted():
        calls[0] += 1
        return orig()
    hm.compute_total_energy = counted
    with contextlib.redirect_stdout(io.StringIO()):
        hm.holographic_solve(ProblemType.SAT, {"clauses": clauses, "num_vars": n},
                             max_steps_per_scale=steps_per_scale, num_sweeps=2)
    ok = satisfies(clauses, _cells_assign(hm, n))
    return ok, calls[0]


HOLO_LADDER = (100, 300, 1000, 3000)


def holographic_ladder(clauses, n, depth, seed, budget):
    """Cost-to-success for a fixed-cost solver: rerun with a larger
    steps_per_scale until a run ends satisfied; cost = CUMULATIVE energy
    evaluations over all rungs (failed rungs count). None if the ladder or
    the budget runs out first."""
    total = 0
    for steps in HOLO_LADDER:
        ok, cost = holographic(clauses, n, depth, steps, seed)
        total += cost
        if ok:
            return total
        if total >= budget:
            return None
    return None


# --------------------------------------------------------------------------
# experiment
# --------------------------------------------------------------------------

def median_or_none(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def slope_log2(sizes, values):
    pts = [(n, math.log2(v)) for n, v in zip(sizes, values) if v]
    if len(pts) < 2:
        return None
    xs, ys = zip(*pts)
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den


def run(sizes, k, budget, holo_steps, seed=2026):
    rng = random.Random(seed)
    rows = []
    for n in sizes:
        depth = depth_for(n)
        inst = []
        while len(inst) < k:
            cl = random_3sat(n, rng)
            if dpll([list(c) for c in cl], {}, [0]) is not None:
                inst.append(cl)
        rec = {"n": n, "m": len(inst[0]), "golden_depth": depth, "instances": k,
               "brute": [], "dpll": [], "walksat": [], "anneal": [],
               "holo_success": 0, "holo_cost": [], "holo_ladder": []}
        t0 = time.time()
        for i, cl in enumerate(inst):
            if n <= BRUTE_MAX_N:
                S = count_solutions(cl, n)
                rec["brute"].append((2 ** n + 1) / (S + 1))
            c = [0]
            dpll([list(x) for x in cl], {}, c)
            rec["dpll"].append(c[0])
            rec["walksat"].append(walksat(cl, n, random.Random(seed + i), budget))
            rec["anneal"].append(mandala_anneal(cl, n, depth, budget, seed + i))
            ok, cost = holographic(cl, n, depth, holo_steps, seed + i)
            rec["holo_success"] += int(ok)
            rec["holo_cost"].append(cost)
            rec["holo_ladder"].append(holographic_ladder(cl, n, depth, seed + i, budget))
        rec["seconds"] = round(time.time() - t0, 1)
        summ = {
            "n": n,
            "brute_median": median_or_none(rec["brute"]),
            "dpll_median": median_or_none(rec["dpll"]),
            "walksat_median": median_or_none(rec["walksat"]),
            "walksat_solved": sum(x is not None for x in rec["walksat"]),
            "anneal_median_solved": median_or_none(rec["anneal"]),
            "anneal_solved": sum(x is not None for x in rec["anneal"]),
            "holo_solved": rec["holo_success"],
            "holo_cost_median": median_or_none(rec["holo_cost"]),
            "holo_ladder_median_solved": median_or_none(rec["holo_ladder"]),
            "holo_ladder_solved": sum(x is not None for x in rec["holo_ladder"]),
        }
        rec["summary"] = summ
        rows.append(rec)
        print(f"n={n:>2} m={rec['m']:>3} depth={depth} "
              f"brute={summ['brute_median']} dpll={summ['dpll_median']} "
              f"walksat={summ['walksat_median']} ({summ['walksat_solved']}/{k}) "
              f"anneal={summ['anneal_median_solved']} ({summ['anneal_solved']}/{k}) "
              f"holo={summ['holo_solved']}/{k} @ {summ['holo_cost_median']} evals "
              f"holo_ladder={summ['holo_ladder_median_solved']} ({summ['holo_ladder_solved']}/{k}) "
              f"[{rec['seconds']}s]", flush=True)
    return rows


def main():
    quick = "--quick" in sys.argv
    sizes = [8, 12, 16] if quick else [8, 12, 16, 20, 24, 28]
    k = 4 if quick else 10
    budget = 20000 if quick else 100000
    holo_steps = 300 if quick else 1000
    print(f"edge-4 3-SAT scaling: alpha={ALPHA} sizes={sizes} k={k} "
          f"budget={budget} evals holo_steps_per_scale={holo_steps}")
    rows = run(sizes, k, budget, holo_steps)
    S = [r["n"] for r in rows]
    fits = {}
    for key in ("brute_median", "dpll_median", "walksat_median",
                "anneal_median_solved", "holo_ladder_median_solved"):
        vals = [r["summary"][key] for r in rows]
        s = slope_log2(S, vals)
        fits[key] = None if s is None else {"log2_slope_per_var": round(s, 3),
                                            "growth_base_per_var": round(2 ** s, 3)}
    out = {
        "status": "MEASURED (synthetic random 3-SAT instances, seeded)",
        "date": "2026-10-27",
        "alpha": ALPHA, "sizes": S, "instances_per_size": k,
        "budget_evals": budget, "holo_steps_per_scale": holo_steps,
        "rows": rows, "growth_fits": fits,
        "scope": ["n <= 24: trends only, not asymptotics",
                  "anneal/walksat medians are over solved runs only; unsolved runs "
                  "are censored at the budget",
                  "holographic: holo_cost = one fixed-cost run; holo_ladder = cumulative "
                  "cost over steps_per_scale 100/300/1000/3000 until a run ends satisfied",
                  "growth fits use medians of solved runs; heavy censoring biases a fit low"],
        "interpretation": "unassigned",
    }
    path = os.path.join(ROOT, "experiments",
                        "edge4_sat_scaling_results_quick.json" if quick
                        else "edge4_sat_scaling_results.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=float)
    print("growth fits (log2 cost per added variable):")
    for k_, v in fits.items():
        print(f"  {k_:>22}: {v}")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
