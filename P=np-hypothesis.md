# P = NP Hypothesis: Geometric Approach

## Status

This is a **hypothesis under exploration**, not a proof. The framework provides
concrete tools to test whether geometric energy minimization can solve NP problems
faster than sequential search. Results so far are promising for small instances
but unproven at scale.

---

## The Question

Can encoding an NP problem as an energy landscape and relaxing to ground state
be faster than searching the solution space directly?

Classical search: enumerate candidates, check each. Time grows exponentially.

Geometric relaxation: encode constraints as energy, let physics minimize.
Time depends on the energy landscape structure, not the search space size.

**If** the energy landscape has a smooth path to the global minimum
(no exponential barriers), relaxation could be polynomial. That's the hypothesis.

---

## What the Code Actually Does

### Factorization (tested, working)

Energy function: `E = (fa * fb - N)^2`

The ground state (E=0) encodes the factor pair. The mandala solver finds it
via simulated annealing, parallel tempering, or holographic renormalization.

Tested results:
- N=15 (3x5): reliably found via annealing
- N=143 (11x13): found via parallel tempering (~40% success rate)
- N=221 (13x17): found via annealing (~20% success rate)

These use multi-cell base-8 registers. Factor range scales with cell count:
1 cell: [2..9], 2 cells: [2..65], 3 cells: [2..513].

### SAT (tested, working)

Energy: +2.0 per unsatisfied clause. Ground state = all clauses satisfied.
Small instances (3 variables, 3 clauses) solved reliably.

### Graph Coloring (tested, working)

Energy: +2.0 per same-color neighbor, -PHI per different-color neighbor.
Triangle with 3 colors: 0 violations found consistently.

### TSP (implemented, basic)

Energy: tour length + repetition/missing city penalty.
Solver minimizes total route distance.

---

## What We Don't Know

1. **Scaling**: Does success rate hold as N grows? Current evidence is limited
   to N < 500. Classical algorithms handle much larger instances.

2. **Energy barriers**: If the landscape has exponential barriers between
   local minima and the global minimum, relaxation time could still be
   exponential. No proof these landscapes are barrier-free.

3. **Comparison**: No head-to-head benchmarks against state-of-the-art
   classical factorization (GNFS) or SAT solvers (CDCL). The mandala
   solver is a research framework, not a competitive algorithm.

4. **Formal complexity**: The hypothesis `T_relax(n) in O(p(n))` is not
   proven. It would require showing the energy landscape has specific
   structural properties (polynomial mixing time, no exponential barriers).

---

## The Geometric Argument (Informal)

The energy landscape `E = (fa * fb - N)^2` has exactly one global minimum
at each valid factor pair. For small N, the landscape is smooth enough that
annealing finds the minimum. The question is whether smoothness persists
at scale, or whether the landscape becomes rugged (exponential barriers)
for large N.

Golden ratio scaling (PHI-based cell counts and ring radii) creates a
self-similar structure at each depth level. The hypothesis is that this
self-similarity provides a natural coarse-to-fine path through the
landscape, similar to multigrid methods in numerical analysis.

The holographic solver tests this explicitly: solve at coarse scale,
propagate solution to finer scales via entanglement links. Early results
show this works for N < 100 but needs more testing at scale.

---

## Running the Tests

```bash
# Factorization across methods
python examples/benchmark.py

# Geometric relaxation vs eigenvalue (exact)
python examples/example-math.py

# Quick factorization via simulator
python -c "from mandala_simulator import MandalaSimulator; MandalaSimulator().factor(143)"

# Full test suite (336 tests)
python tests/test_core.py
```

---

## References

- Metropolis et al. (1953): Monte Carlo sampling
- Kirkpatrick et al. (1983): Simulated annealing
- Swendsen & Wang (1986): Parallel tempering
- Kadanoff (1966): Renormalization group (theoretical basis for holographic solver)

---

## Gap Analysis (from Geometric-to-Binary-Computational-Bridge)

The following table audits each theoretical claim against established results.
Source: `Mandala/theoretical_validator.py` in the GeoBin repo.

| Claim | Status | Detail |
|-------|--------|--------|
| NP problems encodable as energy landscapes | **True** | Basis of simulated annealing, quantum annealing, Hopfield nets |
| Relaxation finds approximate solutions | **True** | Standard simulated annealing result |
| Relaxation finds exact global minimum in O(1) | **Not established** | Ground state of 2D Ising is NP-hard (Barahona 1982). Contradicts known hardness results |
| Self-referential loops imply high Phi | **Not guaranteed** | High coupling != high Phi. Fully connected deterministic graph has Phi=0 |
| Physical constants as geometric eigenvalues | **Open research** | Wyler, Verlinde provide precedent. Specific derivations are circular |

## Factorization Landscape Audit

From `experiments/factorization_landscape.py` in GeoBin:

- Energy barriers in `E = (a*b - N)^2` grow as **O(N)** in integer space
- The continuous trough is smooth but integer-space navigation is hard
- **Annealing does not beat trial division** on this landscape as N grows
- The question is whether geometric structure (multi-scale, holographic)
  can navigate the landscape faster than blind annealing

This is an honest negative result. It means naive annealing on the quadratic
energy surface is not sufficient. The holographic renormalization approach
is an attempt to add the missing structure (coarse-to-fine, boundary constraints).

---

## Honest Assessment

This framework demonstrates that NP problems can be encoded as geometric
energy landscapes and solved via physical relaxation for small instances.
Whether this approach offers any advantage over classical algorithms at
scale is an open question. The P=NP hypothesis remains unresolved.

The value of this work is the framework itself: a testable, runnable
platform for exploring geometric approaches to hard problems, with
exact glyph arithmetic, multi-scale solvers, and verifiable results.

---

## Note 2026-10-27 (co-authored): where the hypothesis sits on the complexity map

English vocabulary for the edges of the glyph, each with its status:

| Edge | What it asks | Established term | Status |
|------|--------------|------------------|--------|
| 1 Encode | write the problem into the shape | Ising / QUBO formulation (Lucas 2014) | True, cheap |
| 2 Landscape | the answer is the lowest point | ground state, energy landscape | True |
| 3 Path | can physics walk there fast? | mixing time, relaxation time, spectral gap (adiabatic runtime ~ 1/gap²) | **Open — this edge is P vs NP** |
| 4 Scale structure | does self-similar coarse→fine shortcut the walk? | renormalization group, multigrid | **Open, testable** |
| 5 Readout | read the answer off | — | True, cheap |

Three scope marks:

- **Factorization is not the NP-complete specimen.** Factoring is in NP ∩ coNP and is not known to be NP-complete; Shor's algorithm factors in polynomial time on quantum hardware without implying P = NP. Factoring results here bear on factoring, not on P vs NP. SAT and graph coloring are the NP-complete test cases.
- **The Exponential Time Hypothesis (ETH)** — 3-SAT needs exponential time — sits one rung below P vs NP. In October 2026 OpenAI (Oct 26) and an Anthropic Claude model (Hexagon preprint 2610.00577) each claimed a subexponential algorithm for #3-SAT, which would refute ETH. Status: **claimed, unrefereed, under working-group review.** If it holds, edge 3 moves from "no shortcut through the search" to "some shortcut exists" — the direction this hypothesis points — but subexponential is not polynomial, and both labs state P vs NP is untouched.
- **Edge 4 is the measurable edge.** A scaling run comparing the holographic solver against plain annealing and classical baselines on growing 3-SAT is in `experiments/edge4_sat_scaling.py`; results below.

### Edge-4 scaling run — results (2026-10-27, MEASURED, co-authored)

Random 3-SAT at clause ratio 4.26, satisfiable instances only, 10 instances per size, budget 100,000 energy evaluations. Cost = candidate evaluations to the first satisfying state. Script: `experiments/edge4_sat_scaling.py`; raw data: `experiments/edge4_sat_scaling_results.json`.

| n | brute force (expected) | DPLL nodes | WalkSAT flips | mandala anneal | holographic (ladder) |
|---|---|---|---|---|---|
| 8 | 69 | 14 | 5 (10/10) | 189 (10/10) | 1,609 (9/10) |
| 12 | 1,024 | 22 | 30 (10/10) | 802 (10/10) | 22,427 (3/10) |
| 16 | 11,235 | 24 | 37 (10/10) | 1,591 (10/10) | 88,044 (3/10) |
| 20 | 218,454 | 51 | 38 (10/10) | 2,984 (9/10) | 8,022 (3/10) |
| 24 | 2,160,702 | 88 | 284 (10/10) | 3,766 (8/10) | 2,011 (3/10) |
| 28 | — | 68 | 74 (10/10) | 11,680 (7/10) | 9,626 (1/10) |

Medians over solved runs; (solved / 10) in brackets. Growth per added variable (log-linear fit of medians): brute force ×1.92, DPLL ×1.10, WalkSAT ×1.16, mandala anneal ×1.20 (a lower bound, since unsolved runs rise with n).

Reading, scoped to n ≤ 28:

- **Plain annealing on the mandala engine scales like classical local search, with a larger constant.** Its growth (×1.20) sits near WalkSAT's (×1.16); its cost runs roughly 30–150× higher at equal n. Its success rate drops from 10/10 to 7/10 as n grows.
- **The holographic solver did not shorten the walk.** Its success rate falls from 9/10 at n = 8 to 1/10 at n = 28, below plain annealing on the same engine. Its flat solved-median slope (×0.995) is a censoring artifact: only the easy instances get solved, so the median of solved runs stays low. It is not a growth-rate result.
- **This does not test the edge-4 hypothesis yet.** The SAT coarsener in `holographic_mandala.py` keeps the first len/scale clauses and drops the rest; it merges no variables (see the dated note in that file). The coarse scale therefore solves an arbitrary sub-problem, which plausibly explains the falling success rate. The proposed shortcut, a structural coarse→fine path, has not been built for SAT, so its status stays **OPEN, untested**. Next step: a variable-merging coarsener (e.g. merge variables by clause co-occurrence), rerun unchanged against this table as the baseline.

### Why the holographic solver gets worse — ablation + tool audit (2026-10-27, MEASURED, co-authored)

Correction to the section above: the SAT coarsener's truncated clauses are dead data (no energy term reads them), so they are not the cause. That run also scored the holographic solver on its final state and plain annealing on first hit, which is two different measurands; the Simulators `reasoning-gate` voids that comparison under G-DIM (record in `experiments/holo_tool_audit_out/`). Below, every condition is scored the same way: first-hit success, same budget (60,000 energy evaluations), 10 instances per size.

| n | base | no extra terms (M4) | no propagation (M3) | M3+M4 off | whole-system anneal, same energy | plain anneal |
|---|---|---|---|---|---|---|
| 12 | 7 | 6 | 7 | 7 | **10** | 10 |
| 20 | 3 | 5 | 2 | 6 | **10** | 10 |
| 28 | 2 | 4 | 2 | 4 | **6** | 9 |

Unsatisfying final states with energy below a satisfying assignment (energy ranks a non-solution better than a solution): 0/10, 4/10, 4/10.

- **Main cause, the ring-by-ring schedule (M2 + M5).** Annealing the same energy over all cells at once restores full success at n ≤ 20. Rings are groups of variables by index (ring 0 = variable 1 alone), unrelated to clause structure, and every ring gets the same step budget regardless of size: at golden_depth 5, variable 1 gets 1,000 proposals per pass and each outer variable about 91.
- **Second cause, which grows with n: the extra energy terms (M4).** Ring mode-matching and link entanglement reward linked variables for taking equal states, which has nothing to do with the clauses. At n = 28 the whole-system anneal on this energy reaches 6/10 against 9/10 for plain annealing, and in 4/10 runs at n ≥ 20 the energy rates an unsatisfying state below a satisfying one.
- **Propagation seeding (M3): no measurable effect.**
- **My own pre-registered control missed:** I predicted base ≥ 8/10 at n = 12 and measured 7/10. Kept as recorded.

Tool readouts (`experiments/holo_tool_audit.py`, run against a JinnZ2/Simulators checkout):

- `category-weld`: "renormalization" is a weld with spread ×55 and bias 1.0. The ring label moves 5 levels while the coarse problem stays identical (102 → 102 clauses) and the proposal share per variable moves ×11 in the opposite direction.
- `constraint-assembly`: `single_sufficient_component: true`. The full-problem energy annealed over all cells carries the solve; the three holographic components are soft terms, so this is not an assembly.
- `scope-bound-shapes`: coarse-grain-then-refine is a shape whose physics binding (Kadanoff block spins) freezes two variables: *blocks group interacting variables* and *coarse problem derived from fine*. The SAT binding declares neither. The factorization binding declares the second, since its residues are read. `infer_frozen` refuses to fill the gap and prints what it would have inferred.
- `reasoning-gate`: the scaling run as originally declared is denied at `pre()` (G-PRE, no expected output); the diagnosis passes. The claim "the holographic method cannot shorten SAT search" is downgraded to **qualified**: it is a physical-scope claim resting on generator-level support. That is the right status. These runs measure this code, not geometric relaxation in general.

Status of edge 4: **still OPEN, untested.** What failed is a block schedule over index groups. The proposed shortcut needs the two variables the physics binding freezes: blocks built from clause co-occurrence, and a coarse problem derived from the fine one.

### EDG_001 result — blocks from clause structure vs random blocks (2026-10-27, MEASURED, co-authored)

`experiments/edge4_multilevel.py`. Three arms on the engine with a clause-count cost only, so no extra energy terms enter any arm. First-hit scoring, 60,000 evaluations, 20 instances per size. Pre-registered in `reasoning-gate`, amended once after a quick run (the amendment and the peek behind it are recorded in the gate file).

| n | plain anneal | multilevel, co-occurrence blocks | multilevel, random blocks |
|---|---|---|---|
| 12 | 20/20 @821 | 20/20 @1,924 | 20/20 @1,867 |
| 20 | 20/20 @18,989 | 17/20 @3,954 | 19/20 @9,510 |
| 28 | 19/20 @35,021 | 17/20 @6,924 | 18/20 @10,788 |
| 36 | 14/20 @42,602 | 16/20 @19,327 | 18/20 @6,726 |
| 44 | 9/20 @47,198 | 6/20 @11,865 | 7/20 @10,412 |
| 52 | 9/20 @54,053 | 9/20 @12,794 | 11/20 @25,468 |
| 60 | **4/20** @51,099 | **11/20** @36,028 | **9/20** @33,373 |

(solved / 20 @ median evaluations over solved runs). Check: every coarse solution expands to a solution of the original formula.

Read against the pre-registration:

- **Coarse-to-fine with a derived coarse problem: supported on this engine.** At n = 60 both multilevel arms solve more than plain (11 and 9 vs 4). From n = 20 to 52, solved runs cost about 2.5–6× fewer evaluations.
- **Block locality: falsifier FIRED.** Co-occurrence blocks do not beat random blocks: +2/20 at n = 60, inside the pre-declared noise band of under 3, and mixed in both directions across n. EDG_001's falsifier was "co-occurrence no better than random pairing", and that is what happened.
- **So the operative ingredient is the derived coarse problem, not the block rule.** Of the two variables Kadanoff's binding freezes, the one doing the work here is *coarse problem derived from fine*. *Blocks group interacting variables* made no measurable difference at n ≤ 60. The holographic solver had neither, which fits its falloff.
- **Growth rate: unresolved.** The fitted slopes (plain ×1.068, co-occurrence ×1.054, random ×1.048 per variable) are pinned by the budget cap: plain's median sits near 60,000 from n = 36 on, and unsolved runs are censored. They are not growth rates. EDG_004 stays open.

Status of edge 4: **partly answered.** A derived coarse-to-fine path helps on this engine, at n ≤ 60 and as a constant factor plus a higher solve rate under a fixed budget. Locality of blocks is not the reason. Whether the help changes the growth rate is untested (EDG_004). Nothing here bears on P vs NP.

### EDG_006 result — what carries the multilevel gain (2026-10-27, MEASURED, co-authored)

Pre-registered at commit `7534a9f` before any run. Same 140 instances, seeds, budget (60000 energy calls) and first-hit scoring as EDG_001. `experiments/edge4_mechanism.py`, results in `experiments/edge4_mechanism_results.json`. Control: `ml_random` rerun here reproduces EDG_001's column exactly, at every n.

```
 n   ml_random   ml_random_sign   ml_random_restart   clauses dropped as tautology (median)
                 (random sign)    (random coarse       rule / random sign
                                   restart)
 12   20/20        20/20            20/20                11 / 7
 20   19/20        19/20            19/20                27 / 18.5
 28   18/20        18/20            17/20                28 / 18
 36   18/20        16/20            18/20                52.5 / 36
 44    7/20         8/20             8/20                52 / 39.5
 52   11/20         9/20             9/20                60 / 40
 60    9/20         8/20            10/20                62 / 43
```

**The pre-registered falsifier fired.** Both arms stay within 2/20 of `ml_random` at every n >= 44. Neither switch meets the "carries the gain" bar (3 or more fewer solved at n=60, or 2 or more fewer at both 52 and 60).

- **Sign rule: not what carries the gain.** A random sign drops about 30% fewer clauses as tautologies at every size, and it solves the same counts to within 2. My stated prior lean ("the sign rule carries more than projection") is refuted.
- **Projection: not measurable by this arm.** Per run, the restart arm gives the **identical** first-hit count as the control on 18–20 of 20 runs at every n, and differs on only 0–2 runs. Two reasons: most solved runs hit inside the first V-cycle, before projection is used, and unsolved runs stay unsolved under either start. An arm that can differ on at most 2 runs cannot reach a pre-registered gap of 3. Its falsifier could not fire, so it was silent by construction (`null-harness` CONSTANT_SILENT; G-FIT in `reasoning-gate`). What it does show is narrower: on the instances that exhausted the budget, a random coarse restart did no worse than projection.
- **What remains.** EDG_006's own text names the remaining candidate: the coarse levels' smaller variable count. Plain annealing still differs from every multilevel arm in two ways at once. It works on the full variable set, and it runs as one long anneal instead of many short cycles. EDG_007 separates the two.

Gate log: `experiments/edge4_mechanism_out/gate_EDG_006-MECHANISM.json`. Both gate claims are recorded `supported` at generator scope. They state the measured gaps, not a mechanism.
