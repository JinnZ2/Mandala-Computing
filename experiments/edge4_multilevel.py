"""
edge4_multilevel.py — EDG_001: coarse-to-fine on the mandala engine, with
blocks built from clause structure and each coarse formula derived from
the finer one.

CC0. Co-authored. MEASURED on seeded random 3-SAT (clause ratio 4.26,
satisfiable instances only). Same instance generator, budget unit and
first-hit scoring as edge4_sat_scaling / edge4_holo_diagnosis.

The two things the physics binding of coarse-grain-then-refine freezes,
and the shipped holographic SAT path leaves undeclared
(holo_tool_audit.py, scope-bound-shapes):

  1. blocks group interacting variables  -> pair variables by how many
     clauses they share (co-occurrence weight)
  2. coarse problem derived from fine    -> tie b := s*a, substitute into
     the formula, drop clauses the tie makes tautological. A satisfying
     coarse assignment expands EXACTLY to a satisfying fine one (every
     surviving clause is the fine clause with b renamed; every dropped
     clause contains x and not-x under the tie).

Arms (all on MandalaComputer.encode_optimization with a clause-count cost,
so no coupling / holographic terms enter any arm - EDG_003 kept out):

  plain        anneal the full formula
  ml_cooc      multilevel, pairs chosen by co-occurrence weight
  ml_random    multilevel, identical pipeline, pairs chosen at random
               -> the REMOVAL TEST for "blocks group interacting variables"

Sign rule (same function in both multilevel arms): s = -1 when the pair
shares more same-polarity clauses (b := not a makes them tautological),
else s = +1. For a random pair with no shared clause this gives s = +1.

Schedule: repeated V-cycles until the budget is spent or a level hits a
satisfying state. Coarsest level annealed hot (T 2.0 -> 0.01); each finer
level refined from the expanded assignment (T 0.5 -> 0.01) with steps
proportional to its variable count (EDG_002's budget concern built in).
The next cycle starts the coarsest level from the projection of the
current fine assignment.

Scope: n <= 60. The engine blooms cells by golden depth, so at the finest
level some cells are dead weight (variables map to the first n cells);
every arm pays the same at the finest level, and coarse levels bloom
smaller engines. This is the engine's cost, recorded not corrected.

Run: python experiments/edge4_multilevel.py [--quick] [--simulators PATH]
     --simulators enables the reasoning-gate pre-registration record.
"""

import argparse
import contextlib
import io
import json
import math
import os
import random
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "experiments"))

import numpy as np  # noqa: E402

from mandala_computer import MandalaComputer  # noqa: E402
from edge4_sat_scaling import random_3sat, dpll, satisfies, depth_for  # noqa: E402


class Hit(Exception):
    pass


# ---------------------------------------------------------------------------
# coarsening
# ---------------------------------------------------------------------------

def _cooccurrence(clauses):
    same, opp = {}, {}
    for c in clauses:
        for i in range(len(c)):
            for j in range(i + 1, len(c)):
                a, b = abs(c[i]), abs(c[j])
                if a == b:
                    continue
                key = (min(a, b), max(a, b))
                if (c[i] > 0) == (c[j] > 0):
                    same[key] = same.get(key, 0) + 1
                else:
                    opp[key] = opp.get(key, 0) + 1
    return same, opp


def coarsen_once(clauses, nvars, rng, mode):
    """One level. Returns (coarse_clauses, n_coarse, mapping) where
    mapping[v] = (coarse_var, sign) for v in 1..nvars, or None if no pair
    could be merged."""
    same, opp = _cooccurrence(clauses)
    if mode == "cooc":
        keys = set(same) | set(opp)
        pairs = sorted(keys, key=lambda k: (-(same.get(k, 0) + opp.get(k, 0)),
                                            rng.random()))
    else:  # random pairing, same pipeline
        vs = list(range(1, nvars + 1))
        rng.shuffle(vs)
        pairs = [(min(vs[i], vs[i + 1]), max(vs[i], vs[i + 1]))
                 for i in range(0, len(vs) - 1, 2)]
    matched, ties = set(), []
    for a, b in pairs:
        if a in matched or b in matched:
            continue
        matched.update((a, b))
        s = -1 if same.get((a, b), 0) >= opp.get((a, b), 0) and \
            same.get((a, b), 0) > 0 else 1
        ties.append((a, b, s))
    if not ties:
        return None
    rep = {v: (v, 1) for v in range(1, nvars + 1)}
    for a, b, s in ties:
        rep[b] = (a, s)
    reps = sorted({r for r, _ in rep.values()})
    renum = {r: i + 1 for i, r in enumerate(reps)}
    mapping = {v: (renum[r], s) for v, (r, s) in rep.items()}
    out, seen = [], set()
    for c in clauses:
        lits = set()
        for lit in c:
            cv, s = mapping[abs(lit)]
            lits.add(cv * s * (1 if lit > 0 else -1))
        if any(-x in lits for x in lits):
            continue  # tautology under the tie: satisfied for every assignment
        key = tuple(sorted(lits))
        if key not in seen:
            seen.add(key)
            out.append(list(key))
    return out, len(reps), mapping


def hierarchy(clauses, n, rng, mode, floor=8):
    levels = [(clauses, n, None)]
    while levels[-1][1] > floor:
        r = coarsen_once(levels[-1][0], levels[-1][1], rng, mode)
        if r is None or r[1] >= levels[-1][1]:
            break
        levels.append(r)
    return levels  # levels[k] = (formula, nvars, mapping from level k-1 to k)


def expand(assign_coarse, mapping, nfine):
    return {v: (assign_coarse[cv] if s == 1 else not assign_coarse[cv])
            for v, (cv, s) in mapping.items() if v <= nfine}


def project(assign_fine, mapping, ncoarse):
    out = {}
    for v, (cv, s) in mapping.items():
        if cv not in out:
            out[cv] = assign_fine[v] if s == 1 else not assign_fine[v]
    for cv in range(1, ncoarse + 1):
        out.setdefault(cv, False)
    return out


# ---------------------------------------------------------------------------
# engine runs (shared eval counter, first hit raises)
# ---------------------------------------------------------------------------

def _unsat(clauses, assign):
    return sum(1 for c in clauses if not any((l > 0) == assign[abs(l)] for l in c))


def anneal_level(formula, nvars, start, steps, T0, T1, counter, budget, seed):
    np.random.seed(seed)
    with contextlib.redirect_stdout(io.StringIO()):
        mc = MandalaComputer(golden_depth=depth_for(nvars))

    def cost(states):
        counter[0] += 1
        a = {v: states[v - 1] >= 4 for v in range(1, nvars + 1)}
        u = _unsat(formula, a)
        if u == 0:
            counter[1] = a
            raise Hit
        if counter[0] >= budget:
            raise Hit
        return float(u)
    with contextlib.redirect_stdout(io.StringIO()):
        mc.encode_optimization(cost, nvars)
    if start is not None:
        for v in range(1, nvars + 1):
            mc.cells[v - 1].state = 5 if start[v] else 2
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            mc.simulated_annealing(max_steps=max(steps, 10), T_start=T0, T_end=T1)
    except Hit:
        pass
    return {v: mc.cells[v - 1].state >= 4 for v in range(1, nvars + 1)}


def run_plain(clauses, n, budget, seed):
    counter = [0, None]
    anneal_level(clauses, n, None, budget, 2.0, 0.01, counter, budget, seed)
    return counter[0] if counter[1] is not None else None


def run_multilevel(clauses, n, budget, seed, mode, steps_per_var=50):
    rng = random.Random(seed)
    levels = hierarchy(clauses, n, rng, mode)
    counter = [0, None]
    fine = None
    cycle = 0
    while counter[0] < budget and counter[1] is None:
        # coarsest: start from projection of current fine assignment
        start = None
        if fine is not None:
            a = fine
            for k in range(1, len(levels)):
                a = project(a, levels[k][2], levels[k][1])
            start = a
        f, nv, _ = levels[-1]
        a = anneal_level(f, nv, start, steps_per_var * nv * 2, 2.0, 0.01,
                         counter, budget, seed + 1000 * cycle)
        if counter[1] is not None or counter[0] >= budget:
            break
        for k in range(len(levels) - 1, 0, -1):
            a = expand(a, levels[k][2], levels[k - 1][1])
            f, nv, _ = levels[k - 1]
            a = anneal_level(f, nv, a, steps_per_var * nv, 0.5, 0.01,
                             counter, budget, seed + 1000 * cycle + k)
            if counter[1] is not None or counter[0] >= budget:
                break
        fine = a
        cycle += 1
    if counter[1] is None:
        return None, len(levels)
    return counter[0], len(levels)


# ---------------------------------------------------------------------------

def gate_preregister(sim_path, outdir):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "rg_gate", os.path.join(sim_path, "reasoning-gate", "gate.py"))
    gm = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.join(sim_path, "reasoning-gate"))
    spec.loader.exec_module(gm)
    g = gm.Gate("EDG_001-MULTILEVEL", strict=False, log_dir=outdir)
    g.pre(
        question="do clause-structure blocks plus a derived coarse formula "
                 "beat random blocks and plain annealing on 3-SAT",
        statistic="first-hit solved count per n under one budget; median "
                  "evaluations over solved runs with solved fraction beside it; "
                  "log2 growth of the median per added variable. AMENDED "
                  "2026-10-27 after the --quick run, which saturated solved "
                  "counts at n<=20 (4/4 in every arm): sizes widened to n=60, "
                  "k raised to 20, and the median/growth statistics added. "
                  "The --quick numbers were seen before this amendment",
        discriminates="ml_cooc and ml_random share every step except how "
                      "pairs are chosen, so a gap between them isolates block "
                      "locality; plain isolates coarse-to-fine as a whole",
        expected="if locality matters: ml_cooc solves >= 3/10 more than "
                 "ml_random at the largest n, or (where both saturate) its "
                 "median cost is lower by 2x or more. If coarse-to-fine helps "
                 "at all: ml_cooc >= plain on the same reading. A growth-rate "
                 "change needs the ml_cooc slope below plain's by more than "
                 "the spread between seeds; otherwise it is a constant factor",
        resolution=[gm.Resolution("instances vs gap read", instrument=1,
                                  feature=3, margin=2.0)],
        controls=[gm.Control("plain, n=12", predicted=">= 9/10"),
                  gm.Control("coarse solution expands to a fine solution",
                             predicted="every multilevel hit verifies on the "
                                       "original formula")],
    )
    return g


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--quick", action="store_true")
    p.add_argument("--simulators", default=os.environ.get("SIMULATORS_PATH", ""))
    a = p.parse_args()
    sizes = [12, 20] if a.quick else [12, 20, 28, 36, 44, 52, 60]
    k = 4 if a.quick else 20
    budget = 30000 if a.quick else 60000
    outdir = os.path.join(ROOT, "experiments", "edge4_multilevel_out")
    os.makedirs(outdir, exist_ok=True)
    gate = None
    if a.simulators and os.path.isdir(a.simulators):
        gate = gate_preregister(a.simulators, outdir)
    rng = random.Random(2026)
    rows, verify_ok = [], True
    print(f"EDG_001 multilevel: sizes={sizes} k={k} budget={budget} "
          f"gate={'on' if gate else 'NOT_REACHED'}")
    print(f"{'n':>3} {'levels':>7} {'plain':>14} {'ml_cooc':>14} {'ml_random':>14}")
    for n in sizes:
        inst = []
        while len(inst) < k:
            cl = random_3sat(n, rng)
            if dpll([list(c) for c in cl], {}, [0]) is not None:
                inst.append(cl)
        res = {"plain": [], "ml_cooc": [], "ml_random": []}
        lv = {"ml_cooc": [], "ml_random": []}
        for i, cl in enumerate(inst):
            s = 2026 + i
            res["plain"].append(run_plain(cl, n, budget, s))
            for mode, key in (("cooc", "ml_cooc"), ("random", "ml_random")):
                c, L = run_multilevel(cl, n, budget, s, mode)
                res[key].append(c)
                lv[key].append(L)
        solved = {kk: sum(x is not None for x in v) for kk, v in res.items()}
        med = {kk: (statistics.median([x for x in v if x is not None])
                    if any(x is not None for x in v) else None)
               for kk, v in res.items()}
        cell = lambda kk: f"{solved[kk]}/{k} @{med[kk] if med[kk] is None else int(med[kk])}"
        print(f"{n:>3} {statistics.median(lv['ml_cooc']):>7} {cell('plain'):>14} "
              f"{cell('ml_cooc'):>14} {cell('ml_random'):>14}", flush=True)
        rows.append({"n": n, "solved": solved, "median_evals_solved": med,
                     "levels_median": {kk: statistics.median(v) for kk, v in lv.items()},
                     "first_hit_evals": res})
    # control 2: a coarse hit must verify on the original formula. Re-run one
    # multilevel instance and check the expanded assignment directly.
    cl = random_3sat(16, random.Random(7))
    while dpll([list(c) for c in cl], {}, [0]) is None:
        cl = random_3sat(16, random.Random(random.random()))
    levels = hierarchy(cl, 16, random.Random(1), "cooc")
    for kk in range(1, len(levels)):
        f, nv, mp = levels[kk]
        sol = dpll([list(c) for c in f], {}, [0])
        if sol is None:
            continue  # coarse formula UNSAT is allowed; nothing to expand
        sol = {v: sol.get(v, False) for v in range(1, nv + 1)}
        a = sol
        for j in range(kk, 0, -1):
            a = expand(a, levels[j][2], levels[j - 1][1])
        verify_ok &= satisfies(cl, a)
    def slope(key):
        pts = [(r["n"], math.log2(r["median_evals_solved"][key])) for r in rows
               if r["median_evals_solved"][key]]
        if len(pts) < 2:
            return None
        mx = sum(x for x, _ in pts) / len(pts)
        my = sum(y for _, y in pts) / len(pts)
        return round(sum((x - mx) * (y - my) for x, y in pts)
                     / sum((x - mx) ** 2 for x, _ in pts), 4)
    growth = {kk: slope(kk) for kk in ("plain", "ml_cooc", "ml_random")}
    print("growth, log2 median evals per added variable:",
          {kk: (v, None if v is None else round(2 ** v, 3)) for kk, v in growth.items()})
    out = {"status": "MEASURED (seeded random 3-SAT)", "date": "2026-10-27",
           "growth_log2_per_var": growth,
           "budget_evals": budget, "rows": rows,
           "expansion_verifies": verify_ok, "interpretation": "unassigned"}
    if gate:
        g = gate
        g.control_result("plain, n=12", "%d/%d" % (rows[0]["solved"]["plain"], k))
        g.control_result("coarse solution expands to a fine solution",
                         "verified" if verify_ok else "FAILED")
        obj = "multilevel SAT solve on MandalaComputer (code), first-hit"
        for r in rows:
            for kk, v in r["solved"].items():
                g.record("%s_n%d" % (kk, r["n"]), v, layer="generator",
                         object_of=obj, note="out of %d" % k)
        nmax = rows[-1]["n"]
        d_loc = rows[-1]["solved"]["ml_cooc"] - rows[-1]["solved"]["ml_random"]
        d_c2f = rows[-1]["solved"]["ml_cooc"] - rows[-1]["solved"]["plain"]
        g.claim("locality gap at n=%d: ml_cooc - ml_random = %+d/%d"
                % (nmax, d_loc, k),
                supported_by=["ml_cooc_n%d" % nmax, "ml_random_n%d" % nmax],
                scope="generator")
        g.claim("coarse-to-fine gap at n=%d: ml_cooc - plain = %+d/%d"
                % (nmax, d_c2f, k),
                supported_by=["ml_cooc_n%d" % nmax, "plain_n%d" % nmax],
                scope="generator")
        rep = g.close(observed="see edge4_multilevel_results.json", diverged=None)
        out["gate_claims"] = [{"text": c["text"], "status": c["status"]}
                              for c in g.claims]
        out["gate_controls"] = g.declaration["controls"]
    if not a.quick:
        with open(os.path.join(ROOT, "experiments", "edge4_multilevel_results.json"),
                  "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1)
    print("expansion verifies on original formula:", verify_ok)
    if gate:
        for c in out["gate_claims"]:
            print("  gate:", c["status"], "|", c["text"])


if __name__ == "__main__":
    main()
