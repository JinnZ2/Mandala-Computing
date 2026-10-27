# EDGE4_RESEARCH_GAPS.md

Open questions on edge 4 of the P=NP hypothesis glyph: does a coarse-to-fine path shorten SAT search on the mandala engine? Written 2026-10-27 (co-authored) from `edge4_sat_scaling.py`, `edge4_holo_diagnosis.py` and `holo_tool_audit.py`. Format follows JinnZ2/Simulators `RESEARCH_RENDER.md` §3. Knowledge states come from its §5. Ids are permanent and are never renumbered.

Five gaps. The count is what the record has, not a quota.

---

### EDG_001. INSTRUMENTAL — A coarsener that builds blocks from clause structure

**Gap:** the shipped holographic solver never coarsens a SAT problem. Its blocks are groups of variables by index, and its projected coarse problem is never read. Coarse-to-fine has therefore not been tried on this engine. It has not failed either.

**Knowledge state:** `NOT_STUDIED` (on this engine). Multilevel SAT local search exists in the literature (Walshaw's multilevel refinement, 2002–2004), which makes the method recognised, not new.

**Research question:** given the same budget and the same annealing moves, does building blocks from clause co-occurrence, and deriving each coarse formula from the finer one by substitution, solve more instances than (a) annealing the full formula and (b) the identical coarsening with **random** pairing?

**Disciplines:** combinatorial optimisation, statistical physics (renormalisation, block spins), SAT solving.

**Data sources:**
  YOUR OWN DATA: seeded random 3-SAT at clause ratio 4.26, generated and filtered by `edge4_sat_scaling.py`.

**Method:**
1. Coarsen: pair variables by co-occurrence weight. Tie `b := s·a`, choosing the sign that makes the most shared clauses tautological. Substitute, drop tautologies, repeat until ≤ 8 variables.
2. Solve the coarsest formula on the engine (`encode_optimization`, clause-count cost).
3. Uncoarsen level by level: expand the assignment, then refine at a lower starting temperature.
4. Control: the identical pipeline with random pairs. This is the removal test for "blocks group interacting variables".
5. Same budget, first-hit scoring, 10 instances per size. Pre-register the expected result in `reasoning-gate`.

**Expected deliverable:** `experiments/edge4_multilevel.py` and a results table beside the scaling baseline.

**Falsifier:** co-occurrence multilevel solves no more instances than random-pairing multilevel at any tested n. Locality would then not be what helps.

**What it opens:** if locality helps, EDG_004 (does it change the growth rate, not just the constant). If it doesn't, the coarse-to-fine path for SAT needs a block rule other than locality, and the scope binding's frozen variable is the wrong one.

---

### EDG_002. EMPIRICAL — Budget per variable vs block locality, separated

**Gap:** the diagnosis showed the ring schedule is the dominant cause, but the schedule bundles two mechanisms: arbitrary blocks (M2) and an equal step budget per ring regardless of size (M5). No run separates them.

**Knowledge state:** `UNMEASURED`

**Research question:** with the ring schedule kept and each ring's steps scaled to its number of variables, how much of the gap to whole-system annealing closes?

**Disciplines:** Monte Carlo methods (block Gibbs sampling, sweep scheduling).

**Data sources:**
  YOUR OWN DATA: the diagnosis instance set (seed 2026, n = 12, 20, 28).

**Method:**
1. Copy the `renormalization_solve` loop into the experiment, unchanged except steps per ring = total × (ring size / n).
2. Run it beside `base` and `whole_anneal` with the same first-hit scoring.

**Expected deliverable:** one more column in the diagnosis table.

**Falsifier:** proportional budget reaches the `whole_anneal` success rate, which would make M5 the full cause. Or it does not move from `base`, which would make M2 the full cause.

**What it opens:** whether a ring schedule over structure-aware blocks (EDG_001) needs a budget rule as well, or only a block rule.

---

### EDG_003. METHODOLOGICAL — When do extra energy terms move the minimum off the solutions?

**Gap:** at n ≥ 20, in 4 of 10 runs the holographic energy rated an unsatisfying state below a satisfying one. There is no procedure for deciding, before running, whether an added energy term preserves the problem's ground states.

**Knowledge state:** `UNDEFINED`

**Research question:** for a clause penalty of weight w per unsatisfied clause, what bound on the extra terms' total range guarantees that every global minimum satisfies all clauses?

**Disciplines:** penalty methods in optimisation; QUBO/Ising embedding, where penalty weights for constraints are a known design problem.

**Data sources:**
  YOUR OWN DATA: the `objective` records in `edge4_holo_diagnosis_results.json`.
  EXISTING RECORD: the QUBO penalty-weight literature (constraint penalties chosen larger than the objective's range).

**Method:**
1. Compute each extra term's maximum range over the cells (mode-matching: 0.5 per ring pair; entanglement: the sum of link strengths).
2. State the sufficient condition (range of extra terms < w) and check the shipped weights against it.
3. Rerun the mismatch count with the weights rescaled to meet the condition.

**Expected deliverable:** a stated condition plus a check function. The condition is about the weights, not about any particular run.

**Falsifier:** with the condition met, the mismatch count stays above 0.

**What it opens:** a design rule for any extra term added to an engine energy (holographic, entanglement, Berry phase). It also tells whether the terms can be kept, if useful for something else, without costing correctness.

---

### EDG_004. EMPIRICAL — Growth rate past n = 28

**Gap:** every measurement so far is at n ≤ 28. That shows trends, not asymptotics. Cost per energy call grows with the clause count, because the engine recomputes the whole energy on every move, so larger n has been unaffordable.

**Knowledge state:** `UNMEASURED`

**Research question:** does any coarse-to-fine variant change the growth exponent per added variable relative to WalkSAT (×1.16) and plain annealing (×1.20), measured over n up to at least 100?

**Disciplines:** algorithm engineering, empirical complexity.

**Data sources:**
  YOUR OWN DATA: seeded instances at n = 28 … 100+.

**Method:**
1. INSTRUMENTAL prerequisite: incremental energy, recomputing only the clauses that touch the flipped variable. Cost per move becomes O(clause degree) instead of O(m).
2. Fit log₂(median cost) vs n per method, with a bootstrap interval on the slope. Report the solved fraction beside every median (censoring).

**Expected deliverable:** a growth table with intervals.

**Falsifier:** the slopes overlap within their intervals. Any difference would then be a constant factor, not a growth rate.

**What it opens:** a measured growth exponent is the only result from this engine that bears on edge 3, the P vs NP edge. Even then it bears only on growth within the tested range, never on asymptotics.

---

### EDG_005. EMPIRICAL — Outcome of the October 2026 ETH claims

**Gap:** OpenAI (Oct 26) and an Anthropic Claude model (Hexagon preprint 2610.00577) each claim a subexponential algorithm for #3-SAT. Both claims are unrefereed and under working-group review.

**Knowledge state:** `UNDER_STUDY`

**Research question:** does the working group certify the formalised statement, the paper's stronger bound, or neither? Does the certified algorithm work by structural decomposition (the coarse-to-fine shape), or by something else?

**Disciplines:** computational complexity, formal verification.

**Data sources:**
  EXISTING RECORD: working-group statements, AGMAI, Palomar registry entries, the two Lean developments.

**Method:**
1. Log each statement as it arrives, with its date and what it certifies. Never edit an earlier entry.
2. If an algorithm is certified, read its decomposition and record whether it fits the coarse-grain-then-refine shape. Use `scope-bound-shapes`, declaring only what the paper declares.

**Expected deliverable:** a dated status log, plus at most one scope-binding comparison.

**Falsifier:** withdrawal or refutation of both claims. ETH then stands, and edge 3 returns to "no known shortcut".

**What it opens:** if certified and structural, an existence proof that the shape this hypothesis proposes can beat brute force on 3-SAT, at subexponential scale and not polynomial. That points EDG_001's builds at the specific decomposition the proof uses.

---

## Note 2026-10-27, later: EDG_001 run

EDG_001's falsifier **fired**: co-occurrence pairing did not beat random pairing (n ≤ 60, 20 instances per size). Both multilevel arms beat plain annealing, so the derived coarse formula carries the gain and the block rule does not. Results are in `P=np-hypothesis.md` and `edge4_multilevel_results.json`. Following EDG_001's own "What it opens", the next node is EDG_006.

### EDG_006. EMPIRICAL — What in the derived coarse formula does the work?

**Gap:** the multilevel gain survives random blocks. Two candidate mechanisms remain, and they are not separated: (a) the sign rule picks the tie that makes shared clauses tautological, so each coarse level is a smaller formula with some clauses satisfied by construction; (b) V-cycling itself, meaning restarts from the projection of the current assignment at a fresh temperature.

**Knowledge state:** `UNMEASURED`

**Research question:** with blocks random, does the gain persist when the sign is chosen at random instead of by the tautology rule, and when the V-cycle restarts from a random assignment instead of a projection?

**Disciplines:** combinatorial optimisation (multilevel refinement), Monte Carlo restarts.

**Data sources:**
  YOUR OWN DATA: the EDG_001 instance set (seed 2026).

**Method:**
1. Arm `ml_random_sign`: random pairs plus a random sign.
2. Arm `ml_random_restart`: random pairs, tautology sign, coarsest level restarted from a random assignment each cycle.
3. Same budget and scoring. Pre-register before running.

**Expected deliverable:** two more columns beside the EDG_001 table.

**Falsifier:** both arms match `ml_random`. Neither mechanism alone would then carry the gain, and the remaining candidate is the coarse level's smaller variable count.

**What it opens:** a named mechanism for why derived coarse-to-fine helps here. That is the first thing worth testing for a growth-rate change (EDG_004), because a constant-factor mechanism and a growth mechanism predict different slopes.

---

## Note 2026-10-27, later: EDG_006 run

Falsifier fired (results and table in `P=np-hypothesis.md`). The sign rule does not carry the gain. The restart arm was underpowered by construction: projection is exercised on at most 2 runs per size, below the pre-registered gap of 3. The record keeps that as a limit of the arm, not as a result about projection.

### EDG_007. EMPIRICAL — Smaller coarse problem, or just the cycle schedule?

**Gap:** every multilevel arm differs from plain annealing in two ways at once: (a) it anneals reduced formulas over fewer variables, and (b) it splits the budget into many short anneals with fresh high-temperature starts. EDG_006 ruled out the two finer mechanisms. These two have not been separated.

**Knowledge state:** `UNMEASURED`

**Research question:** with the same budget, does plain annealing on the full formula, restarted on the multilevel cycle schedule (same steps per cycle, same temperature profile), reach the multilevel solve counts?

**Disciplines:** Monte Carlo restarts, multilevel refinement.

**Data sources:**
  YOUR OWN DATA: the EDG_001 instance set (seed 2026).

**Method:**
1. Arm `plain_cycled`: full formula only, with the cycle structure and per-cycle step counts copied from `run_arm`. Each cycle starts from the previous cycle's end state (the analogue of projection) at T = 2.0.
2. Arm `plain_cycled_random`: the same, but each cycle starts from a fresh random state.
3. Pre-register. The power check comes first this time: count the runs where the arm and its comparison can differ, and confirm that count exceeds the gap threshold before running.

**Expected deliverable:** two columns beside the EDG_006 table.

**Falsifier:** `plain_cycled` reaches `ml_random` (within 2/20 at n >= 44). The gain would then be the cycle schedule, and coarse-to-fine would add nothing on this engine.

**What it opens:** if the coarse problem carries the gain, EDG_004 (does it change the growth rate?) becomes the test worth paying for. If the schedule carries it, edge 4 has no evidence on this engine, and the multilevel result reduces to a restart effect.

---

## Held, to return to (2026-10-27)

Marked by the operator as questions to return to, not started:

- **Literature for EDG_006/EDG_007.** Multilevel SAT local search (Walshaw and successors): has anyone ablated the coarsening against matched restarts? Does multilevel change the growth rate or only the constant? A prior answer would sharpen EDG_007's falsifier before it runs.
- **EDG_005 status.** The October 2026 subexponential #3-SAT claims. Has the working group certified the formal statement, the stronger bound, or neither? EDG_005's method stays the one to use: append-only log, earlier entries never edited.
