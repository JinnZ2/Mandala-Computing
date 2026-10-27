#!/usr/bin/env python3
"""EDG_006: what in the derived coarse formula carries the multilevel gain?

CC0. Co-authored. MEASURED on the EDG_001 instance set (seed 2026, clause
ratio 4.26, n = 12..60, 20 satisfiable instances per size, budget 60000
energy calls, first-hit scoring). Nothing here is a statement about SAT in
general; it is about this engine at these sizes.

EDG_001 found that random-pair multilevel beats plain annealing about as much
as co-occurrence multilevel does, so block locality is not what helps. Two
mechanisms were left, and this script separates them by removing one at a
time, with every other step identical to ml_random:

  ml_random          control, rerun here: random pairs, tautology sign rule,
                     each V-cycle's coarsest level starts from the projection
                     of the current fine assignment
  ml_random_sign     random pairs, sign drawn at random (+1 / -1). Removes the
                     rule that picks the tie making shared clauses tautological
  ml_random_restart  random pairs, tautology sign rule, coarsest level started
                     from a fresh random assignment every cycle. Removes the
                     projection, keeps the restart

The pipeline is imported from edge4_multilevel.py, not copied. The only new
code is the sign choice and the start-state choice, each one switch.

Not blind: the EDG_001 ml_random column (9/20 at n=60) was seen before this
pre-registration. Recorded in the gate declaration.

Usage:
  python experiments/edge4_mechanism.py [--quick] [--simulators PATH]
"""
import argparse
import json
import math
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import edge4_multilevel as ml  # noqa: E402
from edge4_sat_scaling import random_3sat, dpll, satisfies  # noqa: E402

ARMS = ("ml_random", "ml_random_sign", "ml_random_restart")


def coarsen_random(clauses, nvars, rng, sign_mode):
    """Random pairing (as ml.coarsen_once mode='random'), with the sign either
    by the tautology rule ('rule') or drawn at random ('random')."""
    same, opp = ml._cooccurrence(clauses)
    vs = list(range(1, nvars + 1))
    rng.shuffle(vs)
    pairs = [(min(vs[i], vs[i + 1]), max(vs[i], vs[i + 1]))
             for i in range(0, len(vs) - 1, 2)]
    ties = []
    for a, b in pairs:
        if sign_mode == "rule":
            s = -1 if same.get((a, b), 0) >= opp.get((a, b), 0) and \
                same.get((a, b), 0) > 0 else 1
        else:
            s = rng.choice((1, -1))
        ties.append((a, b, s))
    if not ties:
        return None
    rep = {v: (v, 1) for v in range(1, nvars + 1)}
    for a, b, s in ties:
        rep[b] = (a, s)
    reps = sorted({r for r, _ in rep.values()})
    renum = {r: i + 1 for i, r in enumerate(reps)}
    mapping = {v: (renum[r], s) for v, (r, s) in rep.items()}
    out, seen, dropped = [], set(), 0
    for c in clauses:
        lits = set()
        for lit in c:
            cv, s = mapping[abs(lit)]
            lits.add(cv * s * (1 if lit > 0 else -1))
        if any(-x in lits for x in lits):
            dropped += 1
            continue
        key = tuple(sorted(lits))
        if key not in seen:
            seen.add(key)
            out.append(list(key))
    return out, len(reps), mapping, dropped


def hierarchy(clauses, n, rng, sign_mode, floor=8):
    levels = [(clauses, n, None)]
    taut = 0
    while levels[-1][1] > floor:
        r = coarsen_random(levels[-1][0], levels[-1][1], rng, sign_mode)
        if r is None or r[1] >= levels[-1][1]:
            break
        levels.append(r[:3])
        taut += r[3]
    return levels, taut


def run_arm(clauses, n, budget, seed, arm, steps_per_var=50):
    """ml.run_multilevel with two switches. With arm == 'ml_random' this is the
    same computation as EDG_001's ml_random; check_control() asserts that."""
    rng = random.Random(seed)
    sign_mode = "random" if arm == "ml_random_sign" else "rule"
    levels, taut = hierarchy(clauses, n, rng, sign_mode)
    counter = [0, None]
    fine, cycle = None, 0
    while counter[0] < budget and counter[1] is None:
        start = None
        if fine is not None and arm != "ml_random_restart":
            a = fine
            for k in range(1, len(levels)):
                a = ml.project(a, levels[k][2], levels[k][1])
            start = a
        f, nv, _ = levels[-1]
        a = ml.anneal_level(f, nv, start, steps_per_var * nv * 2, 2.0, 0.01,
                            counter, budget, seed + 1000 * cycle)
        if counter[1] is not None or counter[0] >= budget:
            break
        for k in range(len(levels) - 1, 0, -1):
            a = ml.expand(a, levels[k][2], levels[k - 1][1])
            f, nv, _ = levels[k - 1]
            a = ml.anneal_level(f, nv, a, steps_per_var * nv, 0.5, 0.01,
                                counter, budget, seed + 1000 * cycle + k)
            if counter[1] is not None or counter[0] >= budget:
                break
        fine = a
        cycle += 1
    hit = counter[0] if counter[1] is not None else None
    if hit is not None and len(levels) == 1:
        assert satisfies(clauses, counter[1])
    return hit, len(levels), taut, cycle


def gate_preregister(sim_path, outdir):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "rg_gate", os.path.join(sim_path, "reasoning-gate", "gate.py"))
    gm = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.join(sim_path, "reasoning-gate"))
    spec.loader.exec_module(gm)
    g = gm.Gate("EDG_006-MECHANISM", strict=False, log_dir=outdir)
    g.pre(
        question="with random blocks, does the multilevel gain survive (a) a "
                 "random tie sign instead of the tautology rule, (b) a random "
                 "restart of the coarsest level instead of projection",
        statistic="first-hit solved count per n (20 instances, budget 60000), "
                  "median evaluations over solved runs with solved fraction "
                  "beside it; same instances and seeds as EDG_001. Not blind: "
                  "EDG_001's ml_random column (9/20 at n=60) was seen first",
        discriminates="each arm differs from ml_random by one switch, so a "
                      "gap names that switch; ml_random is rerun here as the "
                      "control and must reproduce EDG_001's column exactly",
        expected="a switch CARRIES the gain if its arm solves >= 3/20 fewer "
                 "than ml_random at n=60, or at n=52 and n=60 both by >= 2. "
                 "Falsifier (EDG_006 as written): both arms within 2/20 of "
                 "ml_random at every n >= 44, leaving the smaller coarse "
                 "variable count as the remaining candidate. Prior lean, "
                 "stated so it can be wrong: the sign rule carries more than "
                 "projection, because random pairs share a clause often at "
                 "these densities and the rule then removes clauses",
        resolution=[gm.Resolution("instances vs gap read", instrument=1,
                                  feature=3, margin=2.0)],
        controls=[gm.Control("ml_random rerun equals EDG_001 ml_random",
                             predicted="identical first-hit evals, every n")],
    )
    return g


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--quick", action="store_true")
    p.add_argument("--prereg-only", action="store_true")
    p.add_argument("--simulators", default=os.environ.get("SIMULATORS_PATH", ""))
    a = p.parse_args()
    outdir = os.path.join(HERE, "edge4_mechanism_out")
    os.makedirs(outdir, exist_ok=True)
    gate = None
    if a.simulators and os.path.isdir(a.simulators):
        gate = gate_preregister(a.simulators, outdir)
    if a.prereg_only:
        print("pre-registered:", "gate on" if gate else "gate NOT_REACHED")
        return
    sizes = [12, 20] if a.quick else [12, 20, 28, 36, 44, 52, 60]
    k = 4 if a.quick else 20
    budget = 30000 if a.quick else 60000
    stored = {}
    if not a.quick:
        with open(os.path.join(HERE, "edge4_multilevel_results.json")) as f:
            for r in json.load(f)["rows"]:
                stored[r["n"]] = r["first_hit_evals"]["ml_random"]
    rng = random.Random(2026)  # same draw order as edge4_multilevel.main
    rows, control_ok = [], True
    print(f"EDG_006: sizes={sizes} k={k} budget={budget} "
          f"gate={'on' if gate else 'NOT_REACHED'}")
    print(f"{'n':>3} " + " ".join(f"{x:>18}" for x in ARMS) + "  taut_drop(rule/rand)")
    for n in sizes:
        inst = []
        while len(inst) < k:
            cl = random_3sat(n, rng)
            if dpll([list(c) for c in cl], {}, [0]) is not None:
                inst.append(cl)
        res = {x: [] for x in ARMS}
        taut = {x: [] for x in ARMS}
        cyc = {x: [] for x in ARMS}
        for i, cl in enumerate(inst):
            s = 2026 + i
            for arm in ARMS:
                h, L, t, c = run_arm(cl, n, budget, s, arm)
                res[arm].append(h)
                taut[arm].append(t)
                cyc[arm].append(c)
        if n in stored and res["ml_random"] != stored[n]:
            control_ok = False
        solved = {x: sum(v is not None for v in res[x]) for x in ARMS}
        med = {x: (statistics.median([v for v in res[x] if v is not None])
                   if solved[x] else None) for x in ARMS}
        cell = lambda x: f"{solved[x]}/{k} @{None if med[x] is None else int(med[x])}"
        print(f"{n:>3} " + " ".join(f"{cell(x):>18}" for x in ARMS)
              + f"  {statistics.median(taut['ml_random'])}/"
                f"{statistics.median(taut['ml_random_sign'])}", flush=True)
        rows.append({"n": n, "solved": solved, "median_evals_solved": med,
                     "first_hit_evals": res,
                     "tautologies_dropped_median": {x: statistics.median(v)
                                                    for x, v in taut.items()},
                     "vcycles_median": {x: statistics.median(v)
                                        for x, v in cyc.items()}})
    print("control (ml_random reproduces EDG_001):",
          control_ok if stored else "NOT_RUN (quick)")
    out = {"status": "MEASURED (seeded random 3-SAT)", "date": "2026-10-27",
           "budget_evals": budget, "k": k, "rows": rows,
           "control_reproduces_edg001": control_ok if stored else None,
           "interpretation": "unassigned"}
    if gate:
        g = gate
        g.control_result("ml_random rerun equals EDG_001 ml_random",
                         "identical" if control_ok else "DIFFERS")
        obj = "multilevel SAT solve on MandalaComputer (code), first-hit"
        for r in rows:
            for x, v in r["solved"].items():
                g.record("%s_n%d" % (x, r["n"]), v, layer="generator",
                         object_of=obj, note="out of %d" % k)
        nmax = rows[-1]["n"]
        for arm in ("ml_random_sign", "ml_random_restart"):
            d = rows[-1]["solved"][arm] - rows[-1]["solved"]["ml_random"]
            g.claim("%s - ml_random at n=%d = %+d/%d" % (arm, nmax, d, k),
                    supported_by=["%s_n%d" % (arm, nmax), "ml_random_n%d" % nmax],
                    scope="generator")
        g.close(observed="see edge4_mechanism_results.json", diverged=None)
        out["gate_claims"] = [{"text": c["text"], "status": c["status"]}
                              for c in g.claims]
    if not a.quick:
        with open(os.path.join(HERE, "edge4_mechanism_results.json"), "w",
                  encoding="utf-8") as f:
            json.dump(out, f, indent=1)
    if gate:
        for c in out["gate_claims"]:
            print("  gate:", c["status"], "|", c["text"])


if __name__ == "__main__":
    main()
