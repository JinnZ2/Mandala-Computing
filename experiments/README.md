# experiments/

Playgrounds — exploratory notebooks-as-scripts that surface candidate
real-world experiments by routing through the core Mandala engine
(`mandala_computer.py`, `quantum_mandala.py`, `holographic_mandala.py`)
instead of standing alone with their own throwaway solver code. That's
the same falsifiability posture as `claim_validator.py` /
`mandala_scale_invariance_breakdown.py`, applied to hypothesis
generation instead of hypothesis checking.

**Status: all three playgrounds below are now wired to the engine.**
The section below is kept as a record of the wiring, not a to-do list —
useful when extending any of the three or adding a new playground in
the same spirit.

Do not delete files in here for being "unused" without checking this file
first — that's exactly what happened to `constant_swapping_simulator.py`
before (it got dumped into a misnamed `Organize.md` at the repo root and
nearly triaged as cruft).

---

## inventory

| file | what it does | wired to core engine? |
|------|---------------|------------------------|
| `constant_swapping_simulator.py` | Swaps a physical constant in a known equation and searches for an operating point where the swapped equation's output is experimentally detectable | Yes — `run_self_consistency_search()` hands a self-consistency cost function to `MandalaComputer.encode_optimization()` |
| `../geometric_computation_selector.py` | Picks the best Mandala solver strategy for a given problem type/size, learning from real benchmark runs | Yes — `_run_solver()` actually runs `mandala_computer.py`/`holographic_mandala.py`/`quantum_mandala.py` solvers and records real wall-clock time |
| `../mandala_computing_explorer.py` | Ising model explorer: transverse-field annealing, Trotter-Suzuki QMC, parameter sweeps, Qiskit export | Yes — UI/plotting only; solvers live in `QuantumMandalaComputer.transverse_field_ising_anneal()` / `.trotter_suzuki_qmc()` |

(The latter two live at the repo root, not in `experiments/`, because they're
closer to production-shaped — this table tracks all three together since
the integration story was the same for each.)

---

## how each one is wired

### 1. `mandala_computing_explorer.py` → `quantum_mandala.py`

`MandalaExplorerV4` no longer builds `H_ising`/evolves it by hand with
`scipy.linalg.expm`. Three new methods live on `QuantumMandalaComputer`
instead:

- `transverse_field_ising_anneal(J, h, ...)` — real-time adiabatic
  annealing over the native `2^n` qubit Hilbert space. (The octahedral
  Hamiltonian builders already in `quantum_mandala.py` operate on
  `8^num_cells` space, the wrong dimensionality for a 2-level spin-glass
  model, so this needed a new method rather than reuse of
  `_build_hamiltonian`.)
- `trotter_suzuki_qmc(J, h, ...)` — imaginary-time path-integral QMC,
  the natural sibling of the above (same physical system, alternate
  solver) — replaces the bespoke `TrotterSuzukiQMC` class.
- `export_ising_qiskit(J, h, ...)` — module-level OpenQASM generation,
  moved out of the explorer since it's pure physics code generation.

The explorer is now UI/plotting only: `ProblemEncoder` builds the `J`/`h`
matrices, `MandalaExplorerV4` calls the engine methods and renders results.

### 2. `geometric_computation_selector.py` → `mandala_computer.py` / `holographic_mandala.py` / `quantum_mandala.py`

The `METHODS` registry no longer lists a hypothetical numerical-algorithm
menu (LLL, Gröbner, FFT convolution, ...) with no counterpart in this
repo. It now lists the engine's real solver strategies:
`relax_to_ground_state`, `simulated_annealing`, `parallel_tempering`,
`sovereign_tempering` (`mandala_computer.py`), `holographic_solve`
(`holographic_mandala.py`), and `quantum_annealing`/`qaoa`
(`quantum_mandala.py`). `ProblemType` is re-exported from
`mandala_computer.py` instead of a separately maintained enum, so problem
types can't drift out of sync with what the engine actually supports.

`BenchmarkCollector.run_benchmark()` builds a synthetic instance of the
requested problem type/size via the engine's own `encode_*()` methods and
actually executes the chosen solver, recording real wall-clock time and
`get_convergence_rate()`. `AdaptiveScorer` blends that real data with a
heuristic prior instead of parsing theoretical big-O strings.

`BloomCube3D` (the octahedral-state Bloom filter) is the one piece with
no existing engine counterpart — left as-is, a plausible candidate for a
future dedup strategy inside `geometric_state_algebra.py`'s null-space
search rather than folded into the selector.

### 3. `constant_swapping_simulator.py` → `mandala_computer.py` (`encode_optimization`)

The "find experiments to run in the outside world" file. A constant swap
doesn't have a "correct answer" to converge to, so `generate_experiment()`
asks a different, falsifiable question instead of writing a narrative:
does there exist an operating point (a value of the equation's free
variable) where the swapped equation's output falls in a plausible
detectable range?

`run_self_consistency_search()` encodes that as a cost function — zero
exactly when the output lands in the detectable band, log-distance to the
nearest edge otherwise — and hands it to
`MandalaComputer.encode_optimization(cost_fn, num_variables)`. The
ground-state energy `relax_to_ground_state()` converges to is the
"distance from a falsifiable experiment" score. Swaps that land at energy
0 report the specific `(free_var value, predicted output)` pair as a
concrete numeric prediction; swaps that don't report that no operating
point in the searched 12-decade range is detectable with the listed
apparatus. That gives `claim_validator.py` something concrete to check: a
claim of the form "swapping X for Y in equation Z has a self-consistent
solution at scale S" is falsifiable in exactly the way the validator
expects.
