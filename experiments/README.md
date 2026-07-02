# experiments/

Playgrounds — exploratory notebooks-as-scripts that are **not yet wired to
the core Mandala engine** (`mandala_computer.py`, `quantum_mandala.py`,
`holographic_mandala.py`). Each one stands alone today: it has its own
throwaway solver code (exact diagonalization, ad-hoc Monte Carlo, simulated
runtimes) instead of calling into the engine that the rest of the repo is
built around.

The intended end state is different: these are meant to become front ends
onto the octahedral energy-landscape engine, so that "playing" with a
parameter sweep or a constant swap surfaces a **candidate real-world
experiment** — something concrete enough to falsify — rather than just a
plot. That's the same falsifiability posture as `claim_validator.py` /
`mandala_scale_invariance_breakdown.py`, applied to hypothesis generation
instead of hypothesis checking.

Do not delete files in here for being "unused" without checking this file
first — that's exactly what happened to `constant_swapping_simulator.py`
before (it got dumped into a misnamed `Organize.md` at the repo root and
nearly triaged as cruft).

---

## inventory

| file | what it does today | wired to core engine? |
|------|---------------------|------------------------|
| `constant_swapping_simulator.py` | Swaps a physical constant in a known equation (e.g. Planck's constant in place of Boltzmann's) and generates a plot + text narrative proposing why the swap might be physically interesting | No — narrative is a text-template heuristic, not a search |
| `../geometric_computation_selector.py` | Picks the best of ~11 numerical methods (GF(2) Gauss, LLL, Bloom cube, etc.) for a problem via theoretical complexity + a learned-from-benchmarks score | No — benchmarks come from `_simulate_runtime()`, a complexity-formula stub, not real solves |
| `../mandala_computing_explorer.py` | Ising model explorer: exact-diagonalization annealing, Trotter-Suzuki QMC, parameter sweeps, Qiskit export | Partially — it's Ising/octahedral-flavored (uses `GLYPHS`, base-8 states) but reimplements its own Hamiltonian and evolution instead of calling `quantum_mandala.py` |

(The latter two live at the repo root, not in `experiments/`, because they're
closer to production-shaped — this table tracks all three together since
the integration story is the same for each.)

---

## integration plan

Each playground already has a natural landing spot in the existing engine.
None of this is implemented yet — this is the plan, to be picked up as
follow-up work.

### 1. `mandala_computing_explorer.py` → `quantum_mandala.py`

Closest to done. Its `MandalaExplorerV4.run()` builds `H_ising` and evolves
it by hand with `scipy.linalg.expm` — that's exactly what
`QuantumMandalaComputer.quantum_annealing()` and `.qaoa()` already do, with
telemetry, entanglement entropy, and glyph tracing built in.

- Replace the hand-rolled `H_ising`/`build_field`/`expm` loop in `run()`
  with `QuantumMandalaComputer.bloom_quantum_mandala()` +
  `.quantum_annealing()`, passing the existing `J`/`h` matrices through
  `encode_optimization`-style problem setup.
- `TrotterSuzukiQMC` becomes a second solver option next to
  `parallel_tempering()` / `sovereign_tempering()` in
  `mandala_computer.py` rather than a bespoke class — same Metropolis
  structure, just registered as a named solver.
- `ParameterSweep` stops re-deriving `H_ising` per grid point and instead
  sweeps `MandalaComputer`/`QuantumMandalaComputer` constructor args,
  reusing `get_convergence_rate()` for the sweep's scoring instead of
  hand-computed `prob_ground`.
- Payoff: every problem type the core engine already supports
  (factorization, SAT, TSP, graph coloring) gets Qiskit export and
  parameter sweeps for free, instead of those features being Ising-only.

### 2. `geometric_computation_selector.py` → `mandala_computer.py` / `holographic_mandala.py`

Currently a meta-optimizer over a *hypothetical* method menu (LLL, Gröbner,
FFT convolution, ...) that doesn't exist in this repo, scored by invented
runtimes. The genuinely useful shape of this file is "which solver strategy
should I use for this problem" — which the repo already has real strategies
for.

- Swap the `METHODS` registry entries for the mandala engine's actual
  solver menu: `simulated_annealing`, `parallel_tempering`,
  `sovereign_tempering`, `holographic_solve` (`holographic_mandala.py`),
  `quantum_annealing`/`qaoa` (`quantum_mandala.py`).
- Replace `BenchmarkCollector.add_benchmark` / `_simulate_runtime` with
  real timing: run the candidate solver against a synthetic problem of the
  requested `ProblemType`/size via `MandalaComputer.encode_*()`, and record
  wall-clock time + `get_convergence_rate()` as the benchmark.
- `AdaptiveScorer` then learns, from real relaxation runs, which solver
  wins at which problem size/sparsity — turning this into a genuine
  meta-annealer over Mandala's own solver space instead of a disconnected
  dispatcher.
- `BloomCube3D` (the octahedral-state Bloom filter) is the one piece with
  no existing counterpart — it's a plausible candidate for a new dedup
  strategy inside `geometric_state_algebra.py`'s null-space search, worth
  prototyping there rather than folding into the selector itself.

### 3. `constant_swapping_simulator.py` → `mandala_computer.py` (`encode_optimization`)

The one furthest from the engine, and the most interesting target: this is
the "find experiments to run in the outside world" file.

- Today `generate_experiment()`/`generate_narrative()` produce a *text*
  heuristic for why a constant swap might be interesting — there's no
  actual search.
- Proposed wiring: for a swapped equation, define a cost function that is
  zero exactly when the swapped equation is self-consistent (dimensionally
  and numerically) over some parameter range, and hand it to
  `MandalaComputer.encode_optimization(cost_fn, num_variables)`. The
  ground-state energy `relax_to_ground_state()` converges to becomes a
  quantitative "distance from physical self-consistency" score for that
  swap, instead of a template-generated paragraph.
- Swaps whose relaxed energy lands near zero are the surfaced candidates —
  those become the "experiment to run in the outside world" this file is
  meant to produce: a specific, falsifiable numeric prediction (parameter
  range + expected deviation) rather than a narrative suggestion.
- This also gives `claim_validator.py` something concrete to check: a
  claim of the form "swapping X for Y in equation Z has a self-consistent
  solution at scale S" is falsifiable in exactly the way the validator
  already expects.
