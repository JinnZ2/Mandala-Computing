# Changelog

High-level history of Mandala Computing, grouped by theme rather than strict semantic
versioning (individual modules carry their own informal `v1.0`/`v2.0` markers in their
docstrings — this file is the repo-wide narrative those numbers don't capture on their
own). Dates are when each capability landed, derived from git history.

## 2026-08 — Seven bases of measurement (`mandala_bloom/`)

- Added `mandala_bloom/`. Where `mandala_stack/` made the *shape* an input,
  this makes the *measurement* an input: a distance is taken by an instrument
  with its own sensitivity `I_ij(u)`, read against a calibration standard
  `mu(u)`, traversed along one of several ways of knowing, through a space
  carrying an explicit unknown density `kappa(u)`, by an observer whose
  participation `omega(u)` softens the instrument toward the identity. Those,
  with the Riemannian metric and the energy functional binding them, are the
  seven bases.
- Two levels, coupled. Each Atlas entry is a parent point; a hypernetwork turns
  that point into the weights of a child manifold on which the entry's concept
  path (🪨 → 🛡️ → 🧭 → 🕸️ → ∞ → 📡 → ⚖️) is a curve. A cross-scale term ties the
  parent metric to the mean child metric, so where an entry sits in the large
  space and what shape its own small space has are learned as one object.
- **Torch is optional and stays that way.** `concept_atlas.py` (the semantics)
  and `bloom_bridge.learn_atlas_geometry()` (embedding via the stack's own
  learner) are numpy-only; `BloomResult` is plain floats, so a bloom trained
  elsewhere loads and solves with no backend present. `mandala_bloom.has_torch()`
  gates the rest and the ImportError names the fix. `requirements.txt` is
  unchanged — the backend lives in `requirements-bloom.txt`.
- `bloom_bridge.py` connects four ways: Atlas dissimilarity into
  `mandala_stack.GeometryLearner`; a trained bloom into a stack `Geometry`
  whose `transition_cost` uses the learned instrument tensor rather than
  Euclidean distance; the concept atlas into the shape-agnostic `MandalaSolver`
  unchanged; and concept paths into the root's exact base-8 glyph arithmetic.
- Measured, with its limit stated. Over 8 seeds the full bloom correlates
  +0.745 (sd 0.230) with the concept/glyph dissimilarity, the
  instrument-ablated bloom +0.496 (sd 0.355), the stack learner +0.161
  (sd 0.411). The instrument tensor appears to help and to stabilise — but
  n = 4 entries is 12 pairs against thousands of parameters, and on 2 of 8
  seeds the ablated version wins. Recorded in `mandala_bloom/README.md` as a
  direction, not a result.
- Six defects found in the source scripts, all verified by running them rather
  than by reading. Five crash: an undefined `curvature_loss_manifold`; a
  positional-after-keyword call that stops the file parsing; a guard testing
  `↻` while indexing `🔄`; hypernetwork weights unpacked `(in, out)` when
  `nn.Linear` stores `(out, in)`; and `jacrev` on a batched point giving a
  rank-4 tensor that was then transposed. The sixth is silent and was the one
  that mattered — building child manifolds with `layer.weight.data = W`
  detaches the autograd graph, so the hypernetwork received exactly zero
  gradient while the loss fell convincingly, leaving the parent→child
  generation decorative and the cross-scale coupling inert. `_ChildManifold`
  now applies generated tensors through `torch.func.functional_call`;
  `test_bloom_hypernetwork_receives_gradient` fails if that regresses.
- Three quieter fixes: `calibration_smoothness` called `requires_grad_(True)`
  on a non-leaf tensor (a no-op, so the term differentiated the wrong thing);
  `mode_alignment` masked a grad-carrying `cdist` diagonal with `inf`,
  propagating NaN backward; and the traversal-mode labels disagreed between the
  comment and the printout, now single-sourced from
  `concept_atlas.KNOWING_MODES`.
- `mandala_cli.py --bloom` runs the whole thing. Test suite 387 -> 422.

## 2026-08 — Geometry-agnostic stack (`mandala_stack/`)

- Added `mandala_stack/`, the repo's first code subdirectory. Where the root
  engine commits to one shape — 8 states, O_h symmetry — the stack makes the
  shape an input: `MandalaSolver` talks only to a `Geometry` protocol, so the
  same anneal / bloom / factor code runs on octahedral, tetrahedral,
  dodecahedral, hexagonal and Hilbert geometries, or on a manifold learned from
  data by `GeometryLearner`. Also carries `GeometricSolver` (energy as a
  functional of the embedding, relaxed by gradient flow rather than random walk)
  and `GeodesicMemory` (associative memory as a basin of attraction).
- The folder shares the root's namespace rather than nesting under it:
  `_paths.bootstrap()` puts both directories on `sys.path`, so stack and root
  modules import each other by plain module name. `quantum_mandala.py`,
  `octahedral_arithmetic.py` and `scale_invariance_breakdown.py` arrived with
  the stack byte-identical to the repo's copies and were not duplicated — they
  are imported from the root, and a test enforces that no module is copied
  across the boundary.
- Added `mandala_stack/stack_bridge.py`, the connection layer, working both
  directions. Root → stack: `RootOctahedralGeometry` exposes the engine's
  `sin²` coupling law, φ-scaled Fibonacci eigenvalues and glyph alphabet as a
  `Geometry`; `CayleyGeometry` turns the 48-element O_h group into a 48-state
  geometry with generator moves and Cayley-distance costs. Stack → root:
  `geometric_relax()` anneals a live `MandalaComputer` with the stack's geometry
  proposing moves and the engine's own `compute_total_energy()` scoring them —
  the same shape as `GeometricMandalaAdapter.geometric_relax`. Plus
  `states_to_glyphs()` / `states_to_number()` into exact glyph-space arithmetic.
- `learn_root_geometry()` hands the root coupling metric *alone* to the stack's
  learner and asks what manifold it implies. Because `sin²(|Δs|·π/4)` vanishes
  for states four apart, the metric treats opposite states as identical and the
  learned embedding is not the octahedron the repo asserts. Recorded as a
  measured result with a test, not smoothed over — either the metric or the
  asserted geometry is wrong, and that is a question for
  `mandala_scale_invariance_breakdown.py`.
- `mandala_cli.py` now spans both halves: its existing `--consumer` and
  `--fractal-map` flags resolve for the first time (`consumer_hardware.py` and
  `fractal_address.py` live in the stack), and `--geometry` / `--bridge` were
  added. The stack's own CLI is `mandala_stack/stack_cli.py`, renamed from
  `mandala_cli.py` to keep the root's entry point.
- Fixed on the way in: `fractal_address.py` did not import at all (a stray
  filename line above the shebang, and unquoted prose after `main()` — the prose
  is preserved as `USAGE_NOTES`); `LearnedGeometry` was missing the `dimension`
  property the `Geometry` protocol requires.
- Test suite grew from 350 to 387: protocol conformance for every registered
  geometry, solver determinism and shape-agnosticism, Cayley graph connectivity
  and parity weighting, state round-trips through a live `MandalaComputer`, and
  the learned-geometry result above.

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
- Expansion over the symmetry lattice is Cayley-guided: `SymmetryMandalaConfig`
  scores every frontier channel by `class_distance` — the minimum
  generator-word distance between conjugacy classes in the O_h Cayley graph —
  and drills into the class nearest the leaking channel (ties break toward the
  leaky dimension's own child). Physically: every parity partner `i.C` sits
  exactly one inversion step from `C`, and the nearest channels to the
  identity are the generator classes themselves, so a root leak expands into
  `C4` and a `C4` leak into `S4`.
- Three in-file self-test scenarios (`python mandala_hook.py`) plus 14 suite
  tests (336 -> 350).

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
