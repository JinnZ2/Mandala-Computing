"""
holo_tool_audit.py — the JinnZ2/Simulators instrument box applied to the
holographic solver's 3-SAT failure.

CC0. Co-authored. Stdlib only. Reads the Simulators tools; changes nothing
in them. Needs a checkout of https://github.com/JinnZ2/Simulators:

    python experiments/holo_tool_audit.py --simulators /path/to/Simulators

If the path is missing, every tool section reports NOT_REACHED and nothing
else runs (breathing degrades, never fails).

Tool selection (TSP-1), logged before running. FIT = runs; REJECT = reason kept.

  reasoning-gate      FIT     re-declares the two edge-4 runs: the gate checks
                              pre-registration, layer tags, and ratios across
                              unlike objects (G-DIM) - the shape of the
                              final-state vs first-hit asymmetry found by hand
  category-weld       FIT     "renormalization" is one label over components
                              that do not travel together in this code
  constraint-assembly FIT     is the holographic solve an assembly, or does
                              one component do all the work?
  scope-bound-shapes  FIT     coarse-grain-then-refine is a shape with a
                              physics binding (Kadanoff block spins); what
                              does the SAT binding leave undeclared?
  null-harness        REJECT  its controls are signal-detection generators
                              (noise, poles, Fisher matrices); a SAT solver
                              is not a detector. The null control needed here
                              (random guessing at the same budget) is already
                              in edge4_sat_scaling as the brute-force column.
  presented-binary    REJECT  no binary was presented; the hypothesis offers a
                              mechanism, not an either/or
  reasoning-dial      REJECT  no knee or saturating curve is being read
  falsifier-audit     REJECT  for this question: it extracts claim/falsifier
                              pairs from prose; the claims here are already
                              written with falsifiers in P=np-hypothesis.md
"""

import argparse
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "experiments")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(path))
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# 1. reasoning-gate: re-declare both runs
# ---------------------------------------------------------------------------

def gate_section(sim, log_dir):
    gm = load_module(os.path.join(sim, "reasoning-gate", "gate.py"), "rg_gate")
    Gate, Resolution, Control = gm.Gate, gm.Resolution, gm.Control
    out = {}

    # --- run 1: the scaling run, declared the way it was actually run ------
    g1 = Gate("EDGE4-SCALING-AS-RUN", strict=False, log_dir=log_dir)
    try:
        g1.pre(
            question="does the holographic coarse-to-fine path change the growth "
                     "rate of 3-SAT search cost",
            statistic="median cost to success per n, log-linear growth fit",
            discriminates="growth per added variable separates a shortcut "
                          "(lower base) from a constant-factor change",
            expected="",          # nothing was pre-registered for the holo column
            resolution=[Resolution("instances per size vs effect size",
                                   instrument=10, feature=10, margin=1.0)],
            controls=[],          # no named control with a predicted value
        )
    except gm.GateError as e:
        out["scaling_pre_denied"] = str(e)
    # the comparison as reported: two different measurands
    try:
        g1.record("holo_solved_n28", 1, layer="instrument",
                  object_of="final state of a fixed-cost holographic run")
        g1.record("anneal_solved_n28", 7, layer="instrument",
                  object_of="trajectory of an annealing run (first hit)")
        r = g1.ratio("holo_vs_anneal", "holo_solved_n28", "anneal_solved_n28")
        out["scaling_ratio"] = r
        out["scaling_voided"] = g1.voided
    except gm.GateError as e:
        out["scaling_mid_denied"] = str(e)

    # --- run 1b: the same comparison, retro-declared so it can run --------
    g1b = Gate("EDGE4-SCALING-RETRO", strict=False, log_dir=log_dir)
    g1b.pre(
        question="is the holographic solver worse than plain annealing at n=28",
        statistic="solved count out of 10",
        discriminates="a solved-count gap of 3 or more separates the solvers "
                      "if both are scored the same way",
        expected="holographic below plain annealing",
        resolution=[Resolution("instances vs gap read", instrument=1, feature=3,
                               margin=2.0)],
        controls=[Control("brute-force expected cost", predicted="grows ~2x per variable")],
    )
    g1b.control_result("brute-force expected cost", "x1.92 per variable")
    g1b.record("holo_solved_n28", 1, layer="instrument",
               object_of="final state of a fixed-cost holographic run")
    g1b.record("anneal_solved_n28", 7, layer="instrument",
               object_of="trajectory of an annealing run (first hit)")
    out["retro_ratio"] = g1b.ratio("holo_vs_anneal", "holo_solved_n28",
                                   "anneal_solved_n28")
    out["retro_voided"] = g1b.voided

    # --- run 2: the diagnosis, declared before reading its numbers ---------
    res_path = os.path.join(EXP, "edge4_holo_diagnosis_results.json")
    if not os.path.exists(res_path):
        out["diagnosis"] = "NOT_REACHED: run edge4_holo_diagnosis.py first"
        return out
    with open(res_path, encoding="utf-8") as f:
        diag = json.load(f)
    rows = {r["n"]: r for r in diag["rows"]}
    k = len(next(iter(rows.values()))["first_hit_evals"]["base"])
    g2 = Gate("EDGE4-HOLO-DIAGNOSIS", strict=False, log_dir=log_dir)
    g2.pre(
        question="which mechanism makes the holographic solver fail as n grows",
        statistic="first-hit success count per condition, same budget",
        discriminates="each condition removes one mechanism; the condition "
                      "that restores success to the plain-anneal level names "
                      "the mechanism; first-hit scoring is applied to every "
                      "condition, so the comparison is one measurand",
        expected="if the ring schedule (M2/M5) is the cause: whole_anneal ~ "
                 "plain, and no_M3/no_M4 stay near base. If the extra energy "
                 "terms (M4) are the cause: no_M4 recovers",
        resolution=[Resolution("instances per size vs smallest gap read",
                               instrument=1, feature=3, margin=2.0,
                               note="a gap of 3/10 or more is read; 1-2 is noise")],
        controls=[Control("plain anneal, n=20", predicted=">= 8/10 (scaling run: 9/10)"),
                  Control("base, n=12", predicted=">= 8/10 under first-hit scoring")],
    )
    g2.control_result("plain anneal, n=20", "%d/%d" % (rows[20]["solved"]["plain"], k))
    g2.control_result("base, n=12", "%d/%d" % (rows[12]["solved"]["base"], k))
    obj = "HolographicMandala SAT solve (code), first-hit success"
    for n, row in sorted(rows.items()):
        for cond, v in row["solved"].items():
            g2.record("%s_n%d" % (cond, n), v, layer="generator",
                      object_of=obj if cond != "plain" else obj.replace(
                          "HolographicMandala", "MandalaComputer"),
                      note="out of %d instances" % k)
    nmax = max(rows)
    g2.claim("the ring-by-ring schedule is the dominant cause of the falloff; "
             "the extra energy terms are a secondary cause that appears at "
             "n=%d; propagation seeding has no measurable effect" % nmax,
             supported_by=["base_n%d" % nmax, "whole_anneal_n%d" % nmax,
                           "no_M4_n%d" % nmax, "no_M3_n%d" % nmax,
                           "plain_n%d" % nmax],
             scope="generator")
    g2.claim("the holographic method cannot shorten SAT search",
             supported_by=["base_n%d" % nmax], scope="physical")
    rep = g2.close(observed="see edge4_holo_diagnosis_results.json", diverged=None)
    out["diagnosis_claims"] = [
        {"text": c["text"], "status": c["status"],
         "note": c.get("layer_note", "")} for c in g2.claims]
    out["diagnosis_controls"] = g2.declaration["controls"]
    return out


# ---------------------------------------------------------------------------
# 2. category-weld
# ---------------------------------------------------------------------------

WELD = {
    "term": "renormalization (holographic SAT solve)",
    "domain": "Mandala-Computing holographic_mandala.py, SAT path",
    "tracked_by_label": "scale_level",
    "note": "The solver is described as coarse-to-fine renormalization. In the "
            "SAT path the label rides on ring index; the components that make "
            "renormalization work in physics are tracked by nothing.",
    "components": [
        {"id": "scale_level", "name": "ring index (bloom depth)", "unit": "ring"},
        {"id": "coarse_problem", "name": "clauses the coarse scale actually optimises", "unit": "clauses"},
        {"id": "block_locality", "name": "whether a block groups interacting variables", "unit": "co-occurring clause pairs inside block / total"},
        {"id": "proposal_share", "name": "Metropolis proposals each variable receives per pass", "unit": "proposals"},
        {"id": "success", "name": "first-hit success under fixed budget", "unit": "instances solved"},
    ],
    "divergences": [
        {"id": "coarse-is-not-coarse",
         "note": "_project_problem builds _coarsened_clauses for SAT, but no "
                 "energy term reads it. Every scale optimises the full clause "
                 "set; the coarse problem the label promises does not exist.",
         "readings": {"scale_level": {"before": 5, "after": 1,
                                      "unit": "ring count from finest to coarsest scale",
                                      "source": "_build_rings, golden_depth 5"},
                      "coarse_problem": {"before": 102, "after": 102,
                                         "unit": "clauses at finest vs coarsest scale, n=24",
                                         "source": "holographic_mandala.py _holographic_energy (reads projected_problem only for FACTORIZATION)"}}},
        {"id": "budget-by-ring-not-by-variable",
         "note": "max_steps_per_scale is spent per ring. With rings of 1, 2, 4, "
                 "6, 11 cells (golden_depth 5), variable 1 receives every "
                 "proposal in ring 0 and each outer variable 1/11 of ring 4's.",
         "readings": {"scale_level": {"before": 5, "after": 1,
                                      "unit": "ring count from finest to coarsest scale",
                                      "source": "_build_rings, golden_depth 5"},
                      "proposal_share": {"before": 91, "after": 1000,
                                         "unit": "proposals per variable per pass, ring 4 (finest) vs ring 0 (coarsest), 1000 steps/ring",
                                         "source": "renormalization_solve loop, golden_depth 5"}}},
    ],
}


def weld_section(sim, tmpdir):
    wm = load_module(os.path.join(sim, "category-weld", "weld.py"), "cw_weld")
    s = wm.score(dict(WELD))
    path = os.path.join(tmpdir, "renormalization_holographic_sat.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(WELD, f, indent=1)
    return {"weld_file": os.path.relpath(path, ROOT), "score": s}


# ---------------------------------------------------------------------------
# 3. constraint-assembly
# ---------------------------------------------------------------------------

ASSEMBLY = {
    "case": "holographic-sat-solve",
    "description": "Is the holographic 3-SAT solve a composition of components "
                   "each insufficient alone, or does one component carry it?",
    "components": [
        {"name": "full-problem SAT energy + Metropolis moves over all cells",
         "constraint_class": "invariant",
         "law": "annealing on the clause-count energy; measured: plain anneal "
                "and whole-system anneal on the same energy solve at the "
                "plain-anneal rate",
         "sufficient_alone": True, "used": True, "partial_use_destroys": False},
        {"name": "ring-by-ring block schedule (others frozen)",
         "constraint_class": "soft",
         "law": "blocks are bloom-depth index groups, not interaction groups; "
                "does not hold under load as n grows",
         "sufficient_alone": False, "used": True, "partial_use_destroys": False},
        {"name": "propagation seeding (copy inner ring states outward)",
         "constraint_class": "soft",
         "law": "low-diversity starting assignments; removing it changes little",
         "sufficient_alone": False, "used": True, "partial_use_destroys": False},
        {"name": "ring mode-matching + link entanglement energy",
         "constraint_class": "soft",
         "law": "rewards linked variables for equal states, unrelated to clauses",
         "sufficient_alone": False, "used": True, "partial_use_destroys": False},
    ],
    "rejected": [
        {"option": "coarse problem built from the fine one",
         "ruled_out_by": "not rejected by evidence: built but never read for SAT "
                         "(dead data in _project_problem)"},
    ],
    "budget_terms": ["energy evaluations", "steps per ring"],
    "diagnostic": {"cause_known": True, "deferred": False,
                   "note": "ablations in edge4_holo_diagnosis.py"},
    "source_class": "measured - seeded random 3-SAT, this repo",
    "open": ["a coarsener that merges variables by clause co-occurrence has "
             "not been built; until then edge 4 is untested, not refuted"],
}


def assembly_section(sim):
    am = load_module(os.path.join(sim, "constraint-assembly", "assemble.py"), "ca_assemble")
    return am.score(ASSEMBLY)


# ---------------------------------------------------------------------------
# 4. scope-bound-shapes
# ---------------------------------------------------------------------------

def scope_section(sim):
    sm = load_module(os.path.join(sim, "scope-bound-shapes", "scope.py"), "sb_scope")
    shape = sm.Shape(
        "coarse-grain then refine",
        ["partition variables into blocks", "build a coarse problem over blocks",
         "solve the coarse problem", "project the solution to the fine scale",
         "refine at the fine scale"],
        "the coarse solution is a good start only if blocks group strongly "
        "interacting variables and the coarse problem is derived from the fine one")
    kadanoff = shape.bind(sm.Binding(
        "kadanoff_block_spin",
        live=["block size", "temperature", "coupling strength"],
        frozen=["blocks group interacting variables (spatial locality)",
                "coarse problem derived from fine (decimation)"],
        declared_by="Kadanoff 1966 block spins; multigrid restriction operators"))
    mandala_fact = shape.bind(sm.Binding(
        "mandala_factorization",
        live=["steps per scale", "sweeps", "temperature schedule"],
        frozen=["coarse problem derived from fine (decimation)",
                "block membership by bloom depth (variable index)"],
        declared_by="holographic_mandala.py: modular residues per ring are "
                    "read by _holographic_energy"))
    mandala_sat = shape.bind(sm.Binding(
        "mandala_sat",
        live=["steps per scale", "sweeps", "temperature schedule",
              "holographic weight", "entanglement decay"],
        frozen=["block membership by bloom depth (variable index)"],
        declared_by="holographic_mandala.py SAT path, as executed"))
    out = {}
    for a, b in ((kadanoff, mandala_sat), (kadanoff, mandala_fact),
                 (mandala_fact, mandala_sat)):
        r = sm.compare(a, b)
        out["%s__vs__%s" % (a.name, b.name)] = {
            k: r[k] for k in ("verdict", "collisions", "undeclared_in_a",
                              "undeclared_in_b")}
    out["infer_frozen_refusal"] = sm.infer_frozen(mandala_sat, kadanoff)
    return out


# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--simulators", default=os.environ.get("SIMULATORS_PATH", ""))
    a = p.parse_args()
    sim = a.simulators
    report = {"date": "2026-10-27", "status": "co-authored audit; interpretation "
              "per tool output, no aggregate verdict"}
    if not sim or not os.path.isdir(sim):
        for s in ("reasoning-gate", "category-weld", "constraint-assembly",
                  "scope-bound-shapes"):
            report[s] = "NOT_REACHED: Simulators checkout not found"
        print(json.dumps(report, indent=1))
        return
    outdir = os.path.join(EXP, "holo_tool_audit_out")
    os.makedirs(outdir, exist_ok=True)
    report["reasoning-gate"] = gate_section(sim, outdir)
    report["category-weld"] = weld_section(sim, outdir)
    report["constraint-assembly"] = assembly_section(sim)
    report["scope-bound-shapes"] = scope_section(sim)
    path = os.path.join(outdir, "holo_tool_audit_report.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, default=str)
    print(json.dumps(report, indent=1, default=str))


if __name__ == "__main__":
    main()
