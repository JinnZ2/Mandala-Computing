"""
edge4_holo_diagnosis.py — why does the holographic solver get worse with n?

CC0. Co-authored. MEASURED on seeded random 3-SAT (alpha 4.26, satisfiable).

edge4_sat_scaling.py found HolographicMandala's success rate falling from
9/10 (n=8) to 1/10 (n=28). Reading the code gives five candidate
mechanisms. Each is tested here by switching it off, one at a time, and
measuring FIRST-HIT success under the same budget (a satisfying state seen
at any point in the run counts, for every condition, so the comparison is
like with like; edge4_sat_scaling scored the holographic solver on its
final state only, which is a stricter test than the one applied to plain
annealing).

Candidate mechanisms (from reading holographic_mandala.py):

  M1 projection unused   _project_problem builds _coarsened_clauses for SAT,
                         but no energy term reads them. The coarse scales see
                         the full problem; there is no coarse problem.
  M2 index-based rings   rings are cells grouped by bloom depth, i.e. by
                         variable INDEX (ring 0 = variable 1 alone). A ring is
                         an arbitrary block of variables, unrelated to clause
                         structure. Renormalization = block-coordinate
                         annealing over arbitrary blocks with the rest frozen.
  M3 propagation seeding _propagate_solution overwrites ring d with copies of
                         ring d-1 states (or its dominant state) at the start
                         of each outward pass: correlated, low-diversity
                         starting assignments.
  M4 extra energy terms  ring mode-matching penalty (holographic_weight) and
                         link entanglement energy reward linked variables for
                         taking the SAME state, which has nothing to do with
                         the clauses; the energy minimum need not satisfy SAT.
  M5 budget per ring     max_steps_per_scale is spent per RING regardless of
                         ring size: ring 0 (1 variable) gets as many moves as
                         the outer ring (11+ variables).

Conditions:
  base          HolographicMandala.holographic_solve as shipped
  no_M4         holographic_weight = 0 and entanglement energy = 0
  no_M3         _propagate_solution disabled
  no_M3_M4      both
  whole_anneal  same HolographicMandala energy, but annealed over ALL cells at
                once (parent simulated_annealing loop with holo relax_step) -
                removes M2 and M5, keeps M4
  plain         MandalaComputer annealing (no holographic terms) - reference

Run: python experiments/edge4_holo_diagnosis.py [--quick]
"""

import contextlib
import io
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "experiments"))

import numpy as np  # noqa: E402

from mandala_computer import MandalaComputer, ProblemType  # noqa: E402
from holographic_mandala import HolographicMandala  # noqa: E402
from edge4_sat_scaling import (random_3sat, dpll, satisfies,  # noqa: E402
                               depth_for, _cells_assign)


class FirstHit(Exception):
    pass


def _instrument(engine, clauses, n, budget):
    """Wrap compute_total_energy: count calls, stop at the first satisfying
    state or when the budget is spent. Returns the counter list."""
    calls = [0, None]  # [count, first_hit_call]
    orig = engine.compute_total_energy

    def counted():
        calls[0] += 1
        if calls[1] is None and satisfies(clauses, _cells_assign(engine, n)):
            calls[1] = calls[0]
            raise FirstHit
        if calls[0] >= budget:
            raise FirstHit
        return orig()
    engine.compute_total_energy = counted
    return calls


def run_holo(clauses, n, depth, seed, budget, steps, no_m3=False, no_m4=False,
             whole=False):
    np.random.seed(seed)
    with contextlib.redirect_stdout(io.StringIO()):
        hm = HolographicMandala(golden_depth=depth,
                                holographic_weight=0.0 if no_m4 else 1.0)
        if no_m4:
            hm._entanglement_energy = lambda: 0.0
        if no_m3:
            hm._propagate_solution = lambda a, b: None
        hm.encode_holographic(ProblemType.SAT, {"clauses": clauses, "num_vars": n})
    calls = _instrument(hm, clauses, n, budget)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            if whole:
                hm.simulated_annealing(max_steps=budget, T_start=3.0, T_end=0.01)
            else:
                # loop the shipped solver until the budget is spent
                while True:
                    hm.renormalization_solve(max_steps_per_scale=steps, num_sweeps=2)
    except FirstHit:
        pass
    return calls[1]


def run_plain(clauses, n, depth, seed, budget):
    np.random.seed(seed)
    with contextlib.redirect_stdout(io.StringIO()):
        mc = MandalaComputer(golden_depth=depth)
        mc.encode_sat(clauses)
    calls = _instrument(mc, clauses, n, budget)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            mc.simulated_annealing(max_steps=budget, T_start=2.0, T_end=0.01)
    except FirstHit:
        pass
    return calls[1]


def objective_mismatch(clauses, n, depth, seed):
    """Does the holographic energy rank a satisfying assignment below the
    states the solver settles in? Compare E(satisfying) with E(final)."""
    np.random.seed(seed)
    with contextlib.redirect_stdout(io.StringIO()):
        hm = HolographicMandala(golden_depth=depth)
        hm.encode_holographic(ProblemType.SAT, {"clauses": clauses, "num_vars": n})
        hm.renormalization_solve(max_steps_per_scale=1000, num_sweeps=2)
    final_states = [c.state for c in hm.cells]
    E_final = hm.compute_total_energy()
    final_sat = satisfies(clauses, _cells_assign(hm, n))
    sol = dpll([list(c) for c in clauses], {}, [0])
    # best satisfying embedding: true -> 4, false -> 0 (the pair minimises
    # coupling disagreement only partly; try both encodings and keep lower)
    best = None
    for t_state, f_state in ((4, 0), (7, 3), (4, 3), (7, 0)):
        for v in range(1, n + 1):
            hm.cells[v - 1].state = t_state if sol.get(v, False) else f_state
        E = hm.compute_total_energy()
        best = E if best is None else min(best, E)
    for c, s in zip(hm.cells, final_states):
        c.state = s
    return {"E_final": round(E_final, 3), "final_satisfies": final_sat,
            "E_satisfying_best_of_4": round(best, 3),
            "mismatch": (not final_sat) and E_final < best}


CONDITIONS = ("base", "no_M4", "no_M3", "no_M3_M4", "whole_anneal", "plain")


def main():
    quick = "--quick" in sys.argv
    sizes = [12, 20] if quick else [12, 20, 28]
    k = 4 if quick else 10
    budget = 30000 if quick else 60000
    steps = 1000
    rng = random.Random(2026)
    out = {"status": "MEASURED (seeded random 3-SAT)", "date": "2026-10-27",
           "budget_evals": budget, "steps_per_scale": steps, "rows": [],
           "interpretation": "unassigned"}
    print(f"holographic diagnosis: sizes={sizes} k={k} budget={budget}")
    print(f"{'n':>3} " + " ".join(f"{c:>13}" for c in CONDITIONS) + "   objective-mismatch")
    for n in sizes:
        depth = depth_for(n)
        inst = []
        while len(inst) < k:
            cl = random_3sat(n, rng)
            if dpll([list(c) for c in cl], {}, [0]) is not None:
                inst.append(cl)
        res = {c: [] for c in CONDITIONS}
        mism = []
        for i, cl in enumerate(inst):
            s = 2026 + i
            res["base"].append(run_holo(cl, n, depth, s, budget, steps))
            res["no_M4"].append(run_holo(cl, n, depth, s, budget, steps, no_m4=True))
            res["no_M3"].append(run_holo(cl, n, depth, s, budget, steps, no_m3=True))
            res["no_M3_M4"].append(run_holo(cl, n, depth, s, budget, steps, no_m3=True, no_m4=True))
            res["whole_anneal"].append(run_holo(cl, n, depth, s, budget, steps, whole=True))
            res["plain"].append(run_plain(cl, n, depth, s, budget))
            mism.append(objective_mismatch(cl, n, depth, s))
        solved = {c: sum(x is not None for x in v) for c, v in res.items()}
        nm = sum(m["mismatch"] for m in mism)
        print(f"{n:>3} " + " ".join(f"{solved[c]:>10}/{k:<2}" for c in CONDITIONS)
              + f"   {nm}/{k} unsat finals sit BELOW a satisfying state", flush=True)
        out["rows"].append({"n": n, "golden_depth": depth, "solved": solved,
                            "first_hit_evals": res, "objective": mism})
    path = os.path.join(ROOT, "experiments", "edge4_holo_diagnosis_results.json")
    if not quick:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
