# Changelog

High-level history of Mandala Computing, grouped by theme rather than strict semantic
versioning (individual modules carry their own informal `v1.0`/`v2.0` markers in their
docstrings — this file is the repo-wide narrative those numbers don't capture on their
own). Dates are when each capability landed, derived from git history.

## 2026-07 — Expandable multi-ledger (mandala hook)

- Added `mandala_hook.py` (CC0): an `ExpandableMultiLedger` whose dimension set
  grows when conservation persistently fails to close. Window closure is a
  chi-squared Mahalanobis test on vector residuals; a `ResidualMonitor` CUSUM
  distinguishes persistent leaks (phase events) from fluctuations; on a phase
  event the ledger consults a `MandalaConfig` lattice of conserved-quantity
  dimensions, expands into the chosen one, and absorbs the historical imbalance
  into a retroactive environment balance so the expanded space closes.
- Branch selection is residual-guided: the mandala drills into the first
  unexplored child of the leakiest currently monitored dimension (breadth-first
  from the root as fallback), and records decision provenance on the window
  record.
- `SymmetryMandalaConfig` derives the lattice from the O_h group in
  `geometric_state_algebra.py` instead of hand-written rules: one dimension per
  conjugacy class (10 total) — proper rotation classes under the root, each
  branching to its parity partner `i.C`.
- Three in-file self-test scenarios (`python mandala_hook.py`) plus 11 suite
  tests (336 -> 347).

## 2026-07 — Playground integration, repo audit

- Wired the three `experiments/`-style playgrounds to the core engine instead of
  standalone throwaway solver code: `mandala_computing_explorer.py` now calls
  `QuantumMandalaComputer.transverse_field_ising_anneal()` / `.trotter_suzuki_qmc()`
  instead of reimplementing exact diagonalization inline;
  `geometric_computation_selector.py` selects among the engine's real solver
  strategies (`simulated_annealing`, `parallel_tempering`, `holographic_solve`,
  `quantum_annealing`/`qaoa`, ...) benchmarked with real timed runs instead of a
  hypothetical method menu; `experiments/constant_swapping_simulator.py` searches
  for falsifiable operating points via `MandalaComputer.encode_optimization()`
  instead of a text-template narrative generator.
- Cleaned up stray/orphaned files accumulated across earlier sessions (a
  misnamed Python script masquerading as a `.md` file, a duplicate glyph JSON,
  two near-duplicate copies of the same script concatenated into one file).
- Full repository review (`REVIEW.md`): inconsistencies, markdown gaps, code
  audit, organizational suggestions, limitations checklist, discoverability —
  see that file for details, and this changelog's later entries for the fixes
  that came out of it.

## 2026-06 — Curiosity engine

- Added `curiosity_engine.py`, a wonder-based constraint-interrogation module.

## 2026-05 — Epistemology & schema modules, fabrication constraints

- Added `claim_schema.py` (compressed, binary-serializable claim format —
  `CLAIM_TABLE.json` / `mandala.claims` / `mandala.claims.bin`), the
  cross-model self-description module `mandala_computing_module.py`, and the
  scale-invariance-breakdown-hunting module `mandala_scale_invariance_breakdown.py`.
- Enforced the thermodynamic tier hierarchy in `claim_validator.py` (physics
  concern floors the overall score) and added fabrication constraints.
- Wired the Living-Intelligence-Database (LID) bridge into `mandala_runtime.py`:
  `DynamicsProjector` pattern, provenance tracking, cross-domain RESONATE
  synthesis, real projectors for animal/crystal substrates.

## 2026-04 — Runtime, GEIS, KT annealer, resilience infrastructure

- Added `mandala_runtime.py` (substrate-agnostic sensor fusion: `Substrate`,
  `Basin`, `Manifest`, intersection rules for sound/gravity/electric domains).
- Added `geis.py` (Geometric Information Encoding System bridge), `kt_annealer.py`
  (Kosterlitz-Thouless phase annealer + symmetry detector, ported from the
  Bridge repo), `octahedral_session_cache.py`, and `octahedral_resilience.py`
  (heartbeat monitoring, Shamir secret sharing, circuit breakers, Merkle sync).
- Added `geometric_state_algebra.py`: the full O_h symmetry group, Cayley
  graph, and group ring algebra, replacing flat integer cell states.
- Added `sovereign_mesh.py` (Cayley-wired distributed factorization),
  `osl.py` (Octahedral Symbolic Language v1.0), FRET dipolar coupling and
  Lindblad noise channels in `quantum_mandala.py`.
- Added `membrane.py` (coarse/fine solver boundary primitive) and
  `sovereign_tempering()` in `mandala_computer.py`.
- SIMD vectorization of the classical engine's energy computation.

## 2025-12 to 2026-01 — Holographic solver, glyph arithmetic, exploration algorithms

- Added `holographic_mandala.py` (boundary encoding, coarse-to-fine
  renormalization, cross-depth entanglement, hybrid classical/quantum solve).
- Added `octahedral_arithmetic.py` (native base-8 glyph arithmetic, no decimal
  bottleneck) and `glyph_convert.py` (human decimal bridge).
- Broke the `[2..9]` factor ceiling with multi-cell positional encoding.
- Expanded `mandala_computer.py` with parallel tempering, landscape scanning,
  and sensor telemetry; added `quantum_mandala.py` (annealing, Grover search,
  QAOA with Nelder-Mead optimization).
- Added `constraint_agent.py` (geometric agent framework) and
  `sovereign_integration.py` (Living-Intelligence + Inversion pack-dynamics
  bridge).
- Grew the test suite from an initial 26-test suite toward the current count
  (`tests/test_core.py` currently has 336 tests).

## 2025-11 — Initial framework and documentation

- Initial commit of the core theory documents (`Math.md`, `Questions.md`,
  `Consumer-hardware.md`, `Bridge-substrate.md`, `Physical-computer.md`,
  `Hardware.md`, `Checklist.md`, `Integration.md`, `Mandala-octahedral.md`)
  and `mandala_computer.py`'s first classical engine implementation.
- `CLAUDE.md` added as the technical architecture reference for AI assistants
  working in this repo.
- `.fieldlink.json` added and made bidirectional for cross-repo ecosystem
  linkage (Rosetta-Shape-Core and others).
