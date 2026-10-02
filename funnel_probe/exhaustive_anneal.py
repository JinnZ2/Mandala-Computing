#!/usr/bin/env python3
"""
exhaustive_anneal.py -- every initial state of a 1-cell-per-factor factorization
(N = 15, 21) through the classical annealer at three cooling rates.

LABEL: discrete state space; the cooling rate (open-loop, reads the step
counter) stands in for eps.  quantum_mandala.py is EXCLUDED.

Construction (PREREGISTRATION.md): MandalaComputer(golden_depth=2) -> 3 cells
(one register pair + one FRET-coupled spectator); all 512 initial states
enumerated; exact landscape from compute_total_energy; simulated_annealing
(max_steps M in {50, 200, 800}, T 2.0 -> 0.01, exponential), 20 seeds per
(start, M); success = final energy == exact minimum.  Random landscape_scan
(1000 samples, seeds 0..4) compared with the exhaustive map by replaying its
RNG stream (same np.random.randint calls, same order) and checking that the
replay reproduces the scan's own min_energy and best_config.

No root module is edited; the engine's stdout is discarded.
"""
import contextlib
import io
import itertools
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from mandala_computer import MandalaComputer  # noqa: E402

NS = [15, 21]
M_LIST = [50, 200, 800]
T_START, T_END = 2.0, 0.01
SEEDS = 20
CONFIGS = list(itertools.product(range(8), repeat=3))


def quiet():
    return contextlib.redirect_stdout(io.StringIO())


def build(N):
    with quiet():
        mc = MandalaComputer(golden_depth=2, temperature=1.0)
        mc.encode_factorization(N)
    assert mc.num_cells == 3, mc.num_cells
    assert mc.problem_data["digits_per_factor"] == 1 and mc.problem_data["cells_per_pair"] == 2
    return mc


def set_states(mc, cfg):
    for c, s in zip(mc.cells, cfg):
        c.state = int(s)


def exact_landscape(mc):
    E = np.empty(len(CONFIGS))
    for k, cfg in enumerate(CONFIGS):
        set_states(mc, cfg)
        E[k] = mc.compute_total_energy()
    return E


def cooling_rate(M):
    return float(np.log(T_START / T_END) / (M - 1))


def anneal_chunk(args):
    N, M_idx, cfg_lo, cfg_hi = args
    M = M_LIST[M_idx]
    mc = build(N)
    E = exact_landscape(mc)
    emin = E.min()
    out = []
    for cfg_idx in range(cfg_lo, cfg_hi):
        succ = 0
        for k in range(SEEDS):
            seed = N * 10 ** 6 + M_idx * 10 ** 5 + cfg_idx * 32 + k
            set_states(mc, CONFIGS[cfg_idx])
            np.random.seed(seed)
            with quiet():
                r = mc.simulated_annealing(max_steps=M, T_start=T_START, T_end=T_END, schedule="exponential")
            succ += abs(r["final_energy"] - emin) < 1e-9
        out.append(succ / SEEDS)
    return (N, M_idx, cfg_lo, out)


def greedy_endpoint(E, idx):
    """Best-single-flip descent on the exact landscape; returns the endpoint index."""
    cur = idx
    while True:
        cfg = CONFIGS[cur]
        best, bestE = cur, E[cur]
        for pos in range(3):
            for s in range(8):
                if s == cfg[pos]:
                    continue
                c2 = list(cfg); c2[pos] = s
                j = c2[0] * 64 + c2[1] * 8 + c2[2]
                if E[j] < bestE - 1e-12:
                    best, bestE = j, E[j]
        if best == cur:
            return cur
        cur = best


def random_scan(mc, E, seed, n=1000):
    """Replay landscape_scan's RNG stream, then run the real one and check agreement."""
    np.random.seed(seed)
    visited = []
    for _ in range(n):
        cfg = tuple(int(np.random.randint(0, 8)) for _ in mc.cells)
        visited.append(cfg)
    np.random.seed(seed)
    with quiet():
        r = mc.landscape_scan(num_samples=n)
    idx = [c[0] * 64 + c[1] * 8 + c[2] for c in visited]
    emin = E.min()
    ground = set(np.where(np.abs(E - emin) < 1e-9)[0].tolist())
    replay_min = float(E[idx].min())
    replay_best = CONFIGS[idx[int(np.argmin(E[idx]))]]
    return {"seed": seed,
            "scan_min_energy": r["min_energy"], "scan_best_config": list(r["best_config"]),
            "replay_min_energy": replay_min, "replay_best_config": list(replay_best),
            "replay_matches_scan": abs(r["min_energy"] - replay_min) < 1e-9 and list(r["best_config"]) == list(replay_best),
            "found_exact_min": abs(r["min_energy"] - emin) < 1e-9,
            "distinct_ground_found": len(ground & set(idx)), "ground_total": len(ground),
            "configs_unvisited": 512 - len(set(idx)),
            "energy_levels_unseen": int(len(set(np.round(E, 9))) - len(set(np.round(E[idx], 9))))}


def main(argv):
    quick = "--quick" in argv
    workers = 3
    t0 = time.time()
    out = {"label": "DISCRETE state space; cooling rate is an OPEN-LOOP slow drive standing in for eps",
           "M_list": M_LIST, "cooling_rates": [cooling_rate(M) for M in M_LIST], "seeds": SEEDS, "N": {}}
    for N in NS:
        mc = build(N)
        E = exact_landscape(mc)
        emin = float(E.min())
        ground = np.where(np.abs(E - emin) < 1e-9)[0]
        gcfg = [CONFIGS[g] for g in ground]
        pairs = sorted(set((c[0] + 2, c[1] + 2) for c in gcfg))
        print("N=%d: 3 cells, exact landscape over 512 states; E_min = %.4f at %d ground states; register pairs %s;"
              " distinct energy levels %d" % (N, emin, len(ground), pairs, len(set(np.round(E, 9)))))
        ends = np.array([greedy_endpoint(E, i) for i in range(512)])
        greedy_ok = np.isin(ends, ground)
        print("   greedy single-flip descent reaches the ground set from %d of 512 starts" % greedy_ok.sum())
        rec = {"E_min": emin, "n_ground": int(len(ground)), "ground_configs": [list(c) for c in gcfg],
               "factor_pairs": pairs, "E_all": E.tolist(), "greedy_reaches_ground": greedy_ok.tolist(),
               "n_energy_levels": int(len(set(np.round(E, 9))))}
        # random landscape_scan vs exhaustive
        scans = [random_scan(mc, E, s) for s in range(5)]
        rec["random_scans"] = scans
        print("   landscape_scan(1000) x 5 seeds: replay matches scan %s; exact min found %d/5;"
              " distinct ground states found %s of %d; configs unvisited %s; energy levels unseen %s" % (
                  all(s["replay_matches_scan"] for s in scans), sum(s["found_exact_min"] for s in scans),
                  [s["distinct_ground_found"] for s in scans], len(ground),
                  [s["configs_unvisited"] for s in scans], [s["energy_levels_unseen"] for s in scans]))
        # exhaustive anneal map
        n_cfg = 64 if quick else 512
        step = 32
        jobs = [(N, mi, lo, min(lo + step, n_cfg)) for mi in range(len(M_LIST)) for lo in range(0, n_cfg, step)]
        P = np.zeros((len(M_LIST), n_cfg))
        with Pool(workers) as pool:
            for (n_, mi, lo, vals) in pool.imap_unordered(anneal_chunk, jobs):
                P[mi, lo:lo + len(vals)] = vals
        rec["P_ground"] = P.tolist()
        print("   %-6s %-10s %-9s %-7s %-10s %-14s %s" % ("M", "rate", "meanP", "|F|", "minP", "meanP greedy-ok", "meanP greedy-fails"))
        for mi, M in enumerate(M_LIST):
            F = np.where(P[mi] < 0.5)[0]
            gk = greedy_ok[:n_cfg]
            print("   %-6d %-10.5f %-9.3f %-7d %-10.3f %-14.3f %.3f" % (
                M, cooling_rate(M), P[mi].mean(), len(F), P[mi].min(),
                P[mi][gk].mean() if gk.any() else float("nan"),
                P[mi][~gk].mean() if (~gk).any() else float("nan")))
            rec.setdefault("F_size", []).append(int(len(F)))
            rec.setdefault("meanP", []).append(float(P[mi].mean()))
        out["N"][N] = rec
    # pre-registered predictions
    preds = {}
    r15, r21 = out["N"][15], out["N"][21]
    preds["Q1 ground sets: N=15 -> 16 states at E=0.2; N=21 -> 4 states at E=0"] = (
        r15["n_ground"] == 16 and abs(r15["E_min"] - 0.2) < 1e-9 and r21["n_ground"] == 4 and abs(r21["E_min"]) < 1e-9)
    for N in NS:
        r = out["N"][N]
        mp, fs = r["meanP"], r["F_size"]
        preds["Q2 N=%d mean P_ground rises as the rate falls: %s" % (N, ["%.3f" % v for v in mp])] = all(mp[i + 1] >= mp[i] for i in range(len(mp) - 1))
        preds["Q3 N=%d |F| non-increasing as the rate falls: %s" % (N, fs)] = all(fs[i + 1] <= fs[i] for i in range(len(fs) - 1))
        preds["Q4 N=%d |F| > 0 at the slowest rate" % N] = fs[-1] > 0
        P0 = np.array(r["P_ground"][0]); gk = np.array(r["greedy_reaches_ground"][:len(P0)])
        preds["Q6 N=%d at the fastest rate, greedy-fails starts have lower mean P_ground than greedy-ok starts" % N] = (
            bool((~gk).any()) and P0[~gk].mean() < P0[gk].mean())
    s15 = r15["random_scans"]
    preds["Q5 landscape_scan misses >= 1 ground state in >= 1 of 5 seeds (N=15) and finds E_min in 5/5 for both N"] = (
        any(s["distinct_ground_found"] < s["ground_total"] for s in s15)
        and all(s["found_exact_min"] for s in s15 + r21["random_scans"]))
    print("\nPRE-REGISTERED PREDICTIONS")
    for k, v in preds.items():
        print("  %s %s" % ("HELD  " if v else "FAILED", k))
    out["predictions"] = preds
    outcomes = {}
    for N in NS:
        fs = out["N"][N]["F_size"]
        if all(f == 0 for f in fs):
            outcomes[N] = "NOT_FOUND_IN_RANGE (failure set empty at every rate %s)" % [round(cooling_rate(M), 5) for M in M_LIST]
        elif fs[-1] > 0 and all(fs[i + 1] <= fs[i] for i in range(len(fs) - 1)):
            outcomes[N] = "FUNNEL_FOUND (discrete analog; failure set narrows with slower cooling and persists)"
        else:
            outcomes[N] = "NOT_FOUND_IN_RANGE (failure set %s over rates %s: not narrowing-and-persisting)" % (
                fs, [round(cooling_rate(M), 5) for M in M_LIST])
        print("OUTCOME N=%d: %s" % (N, outcomes[N]))
    out["outcomes"] = outcomes
    print("scope: stochastic (Metropolis annealer, fixed seeds); M in %s, T %.2f -> %.2f exponential; DISCRETE"
          " state space, open-loop slow drive; %.0f s" % (M_LIST, T_START, T_END, time.time() - t0))
    out["predictions"] = {k: bool(v) for k, v in preds.items()}
    json.dump(out, open("exhaustive_anneal_results.json", "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
