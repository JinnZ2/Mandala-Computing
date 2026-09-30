# claude-md

Mandala Computing project guide for AI assistants.

---

## project-overview

Mandala Computing is a research framework for solving hard computational problems
(NP-complete, factorization, optimization) through **geometric intelligence**.
Nested geometric structures with octahedral symmetry and golden-ratio optimization
encode problems as energy landscapes. Computation happens by relaxing to the ground
state — the physics finds the solution.

- **license:** MIT (JinnZ2)
- **status:** research / conceptual phase with working simulators
- **language:** Python 3

---

## repo-structure

Flat layout — all source and documentation at the root. No subdirectories, no package hierarchy.

```
mandala-computing/
├── mandala_computer.py        # core classical simulator v2.0 (~1150 loc)
├── quantum_mandala.py         # quantum extension v2.0 (~1100 loc)
├── holographic_mandala.py     # holographic + renormalization + entanglement (~1080 loc)
├── octahedral_arithmetic.py   # native glyph-space math, base-8 (~610 loc)
├── geometric_state_algebra.py # O_h group, Cayley graph, group ring (~1240 loc)
├── constraint_agent.py        # geometric agent framework (~765 loc)
├── sovereign_integration.py   # Living-Intelligence + Inversion bridge (~700 loc)
├── sovereign_mesh.py          # Cayley-wired mesh factorization (~1100 loc)
├── octahedral_resilience.py   # self-healing distributed infrastructure (~1555 loc)
├── octahedral_session_cache.py# session caching with octahedral invalidation (~710 loc)
├── osl.py                     # Octahedral Symbolic Language v1.0 (~965 loc)
├── geis.py                    # Geometric Information Encoding System bridge (~695 loc)
├── kt_annealer.py             # KT phase annealer + symmetry detector (~530 loc)
├── mandala_hook.py            # expandable multi-ledger, guided dimension expansion (~750 loc)
├── mandala_runtime.py         # substrate-agnostic sensor fusion binding (~2640 loc)
├── membrane.py                # boundary computation primitive (~470 loc)
├── claim_validator.py         # epistemological claim validation (~500 loc)
├── glyph_convert.py           # human decimal-to-glyph converter (~355 loc)
├── mandala_simulator.py       # lightweight symbolic simulator (~250 loc)
├── mandala_cli.py             # unified CLI, root engine + mandala_stack/ (~200 loc)
├── ONBOARDING.md              # agent learning path from Rosetta-Shape-Core
├── .fieldlink.json            # ecosystem metadata (v3.0, bidirectional)
├── .gitignore                 # excludes __pycache__/, *.pyc, .env, etc.
├── requirements.txt           # numpy, scipy
├── README.md                  # project overview
├── PROJECTS.md                # connected repos
├── LICENSE                    # MIT
├── examples/                  # 18 runnable example scripts + benchmark
├── experiments/                # playgrounds wired to the core engine — see experiments/README.md
├── mandala_stack/             # geometry-agnostic stack — see mandala_stack/README.md
├── mandala_bloom/             # seven bases of measurement — see mandala_bloom/README.md
├── requirements-bloom.txt     # optional torch, for mandala_bloom/ training only
├── tests/test_core.py         # 422-test suite
└── [17 .md files]             # theory, hardware, integration, proofs, notes
```

The root is flat; `mandala_stack/` and `mandala_bloom/` are the two code
subdirectories, and both share the root's namespace rather than nesting under
it (see below).

---

## dependencies

`requirements.txt` at repo root lists `numpy` and `scipy` (unpinned).

| package      | usage                                          |
|--------------|------------------------------------------------|
| `numpy`      | arrays, linear algebra, random state           |
| `scipy`      | eigenvalue decomposition (`scipy.linalg.eigh`), matrix exponential (`scipy.linalg.expm`) |

**stdlib:** `dataclasses`, `enum`, `typing`, `time`, `math`, `random`

**optional:** `matplotlib` (referenced in README, not imported in code)

**dependency layers:**

| Layer | Modules | Requires | Why |
|-------|---------|----------|-----|
| Representation | `octahedral_arithmetic.py`, `glyph_convert.py` | stdlib only | Meaning lives in glyph space, no numeric assumptions |
| Classical solving | `mandala_computer.py`, `holographic_mandala.py` | numpy | Random sampling, fast arrays — convenience, not necessity |
| Quantum solving | `quantum_mandala.py` | numpy + scipy | Matrix expm, eigendecomposition — fundamentally linear algebra |
| Bridge / Encoding | `geis.py`, `kt_annealer.py` | numpy | Tensor operations, phase annealing |
| Conservation ledger | `mandala_hook.py` | numpy | Vector residuals, chi-squared closure tests |
| Sensor Fusion | `mandala_runtime.py` | stdlib only | Substrate-agnostic binding, no external deps |
| Infrastructure | `octahedral_resilience.py`, `octahedral_session_cache.py` | stdlib only | Self-healing, caching — no external deps |
| Algebra / Language | `geometric_state_algebra.py`, `osl.py`, `sovereign_mesh.py` | stdlib only | O_h group, symbolic language, mesh — no external deps |
| Agents / Integration | `constraint_agent.py`, `sovereign_integration.py` | stdlib only | Agent framework, sovereignty bridge |
| Validation | `claim_validator.py`, `membrane.py` | stdlib only (membrane: numpy optional) | Epistemology, boundary computation |
| Entry point | `mandala_simulator.py` | stdlib only (delegates to engines when available) | Lightweight wrapper |
| Geometry protocol | `mandala_stack/` | numpy | Shape-agnostic solving, manifold learning |
| Measurement | `mandala_bloom/concept_atlas.py`, `bloom_bridge.py` | numpy | Atlas semantics + geometry export must not need a training backend |
| Measurement (training) | `mandala_bloom/bases.py`, `bloom.py` | **torch, optional** | Differentiable fields and the two-level coupling. `requirements-bloom.txt`, gated by `mandala_bloom.has_torch()` |

---

## key-modules

### mandala-computer (`mandala_computer.py`) v2.0

Core classical engine. Encodes problems into geometric configurations and solves
via multiple exploration algorithms. Loads constants from JSON atlas at runtime.

**classes:**

| class              | role                                              |
|--------------------|---------------------------------------------------|
| `MandalaCell`      | computational cell with position, state, neighbors (dataclass) |
| `SensorReading`    | telemetry reading with sensor_id, step, value     |
| `ProblemType`      | enum: `FACTORIZATION`, `SAT`, `TSP`, `GRAPH_COLORING`, `OPTIMIZATION` |
| `MandalaComputer`  | main computation engine                           |

**key methods on `MandalaComputer`:**

| method                       | purpose                                             |
|------------------------------|-----------------------------------------------------|
| `bloom_mandala()`            | expand symbol core into nested fractal rings        |
| `encode_factorization(N)`    | multi-cell bipartite tensor encoding (auto-scales)  |
| `encode_sat(clauses)`        | boolean satisfiability encoding                     |
| `encode_tsp(cities)`         | traveling salesman ring topology                    |
| `encode_graph_coloring()`    | graph coloring with adjacency constraints           |
| `encode_optimization(fn, n)` | generic cost function minimization                  |
| `relax_to_ground_state()`    | Metropolis-Hastings iterative minimization          |
| `simulated_annealing()`      | annealing with cooling schedule (exp/linear/boltz)  |
| `parallel_tempering()`       | multi-replica exchange at different temperatures    |
| `landscape_scan()`           | random sampling of energy landscape                 |
| `get_state_distribution()`   | histogram of cell states 0-7                        |
| `get_energy_breakdown()`     | per-component energy (cell, coupling)               |
| `glyph_trace()`              | Unicode glyph visualization of cell states          |

**factorization encoding (expanded octahedral):**

Factors are represented as positional numbers across multiple cells in base-8.
The register size auto-scales with `sqrt(N)`:

| digits/factor | factor range     | needs 2+ digits when N > |
|---------------|-----------------|--------------------------|
| 1 cell        | [2..9]          | 49  (sqrt > 8)           |
| 2 cells       | [2..65]         | 4,096  (sqrt > 64)       |
| 3 cells       | [2..513]        | 262,144  (sqrt > 512)    |

Note: coupling energy is scaled by 0.1 for factorization to avoid
interfering with multi-cell factor registers.

### quantum-mandala (`quantum_mandala.py`) v2.0

Quantum extension using 8-dimensional Hilbert space (qubit-octits).

**classes:**

| class                    | role                                            |
|--------------------------|-------------------------------------------------|
| `QuantumMandalaCell`     | quantum cell with state vector in C^8           |
| `QuantumMandalaComputer` | quantum computation engine                      |

**key methods on `QuantumMandalaComputer`:**

| method                          | purpose                                   |
|---------------------------------|-------------------------------------------|
| `bloom_quantum_mandala()`       | create quantum superposition structure    |
| `quantum_annealing()`           | adiabatic optimization with telemetry     |
| `grover_search()`               | quantum search algorithm                  |
| `qaoa()`                        | QAOA with Nelder-Mead optimizer           |
| `entangled_annealing()`         | multi-cell tensor product evolution       |
| `get_entanglement_entropy()`    | Shannon entropy of cell probability       |
| `glyph_trace()`                 | dominant states as Unicode glyphs         |

### holographic-mandala (`holographic_mandala.py`)

Unified framework: holographic boundary encoding + self-symmetry renormalization
+ cross-depth entanglement. Extends `MandalaComputer`.

**classes:**

| class               | role                                               |
|---------------------|----------------------------------------------------|
| `HolographicRing`   | single concentric ring with projected problem      |
| `EntanglementLink`  | cross-depth correlation with adaptive Berry phase  |
| `HolographicMandala`| unified solver (extends MandalaComputer)           |

**key methods on `HolographicMandala`:**

| method                    | purpose                                            |
|---------------------------|----------------------------------------------------|
| `encode_holographic()`    | boundary encoding with inward projection           |
| `renormalization_solve()` | coarse-to-fine bidirectional sweeps                |
| `holographic_solve()`     | full pipeline: encode + renormalize + extract      |
| `hybrid_quantum_solve()`  | classical seeding + quantum entangled refinement   |
| `get_holographic_profile()`| energy and state distribution per ring            |
| `get_entanglement_map()`  | link strengths, phases, correlation status         |

### mandala-simulator (`mandala_simulator.py`)

Lightweight symbolic simulator for quick experiments and demos. Contains a
**separate** `MandalaSimulator` class (not the same as `mandala_computer.MandalaComputer`).
Delegates to real engines when available, falls back to stdlib-only.

### geometric-state-algebra (`geometric_state_algebra.py`)

Full O_h octahedral symmetry group (order 48), Cayley graph, and group ring
algebra. Provides geometric states, prime vertices, null-space detection,
scent-trail search, and a geometric adapter for MandalaComputer relaxation.

**key classes:** `OhElement`, `OhGroup`, `CayleyEnergy`, `GroupRingElement`,
`GeometricState`, `PrimeVertex`, `GeometricMandalaAdapter`

### sovereign-mesh (`sovereign_mesh.py`)

Cayley-wired mesh for distributed factorization. 48 nodes (one per O_h group
element), connected by Cayley graph edges. Nodes check divisibility by assigned
primes, signals propagate through the mesh, and self-healing recovers failed nodes.

**key classes:** `MeshNode`, `SovereignMesh`

### octahedral-resilience (`octahedral_resilience.py`)

Self-healing distributed infrastructure on the octahedral lattice. Stdlib only.
Implements heartbeat monitoring, failover clustering, threshold secret sharing
(Shamir-like seed splitting), Byzantine verification, circuit breakers,
priority scheduling, Merkle-based state sync, and resource-aware healing.

**key classes:** `HeartbeatMonitor`, `OctahedralCluster`, `SeedSplitter`,
`SeedDispersal`, `CircuitBreaker`, `AuditTrail`, `FencingManager`,
`ShareMerkleTree`, `OctahedralResilienceSystem`

### octahedral-session-cache (`octahedral_session_cache.py`)

Session caching with octahedral topology-aware invalidation. Cache entries are
mapped to octahedral vertices; invalidating one vertex cascades to neighbors
along axes. Supports TTL expiry, LRU eviction, persistence, and state-distance
metrics.

**key classes:** `SessionCache`, `CacheEntry`, `InvalidationGraph`, `OctState`

### osl (`osl.py`)

Octahedral Symbolic Language v1.0 — a compact token language for expressing
octahedral geometry operations. Includes a registry of vertex glyphs and animal
macros, a tokenizer, parity verifier, macro expander, transpiler (OSL to Python),
and a bridge mapping OSL trajectories to O_h group elements.

**key classes:** `GlyphRegistry`, `OSLTokenizer`, `ParityVerifier`,
`MacroExpander`, `OSLTranspiler`

### geis (`geis.py`)

Geometric Information Encoding System — bridge between geometric octahedral
states and binary representation. Ported from Geometric-to-Binary-Computational-Bridge.
Provides 3D vertex positions, token notation (`001|O`), bidirectional binary encoding,
3x3 state tensors, geometric sensor simulation, tensor dependency finding,
3D binary cube operations, and Mandala integration helpers.

**key classes:** `OctahedralState`, `GeometricEncoder`, `StateTensor`

### membrane (`membrane.py`)

Boundary computation primitive. A membrane takes a coarse oracle (fast, approximate)
and a fine solver (slow, exact), with the membrane boundary defining the search window.
Includes pre-built configurations for factorization, SAT, and optimization.

**key classes:** `Membrane`, `CoarseResult`, `Window`, `MembraneResult`

### kt-annealer (`kt_annealer.py`)

Kosterlitz-Thouless annealer — phase-based optimisation via topological defect
dynamics. Ported from Geometric-to-Binary-Computational-Bridge/Engine. Operates
on continuous XY-model phases with vortex detection and phi-lattice coupling.
Maps octahedral states 0-7 to phases s*pi/4 for continuous optimisation, then
quantises back. Also includes a 3-D symmetry detector (reflective/rotational).

**key classes:** `KTAnnealer`, `KTConfig`, `AnnealStep`, `SymmetryDetector`

**key functions:** `kt_anneal_mandala()`, `detect_mandala_symmetries()`,
`anneal_network_phases()`, `states_to_phases()`, `phases_to_states()`

### mandala-hook (`mandala_hook.py`)

Expandable multi-dimensional conservation ledger with guided dimension
expansion (CC0). Core principle: every conservation violation is a transfer
into an unmonitored dimension. Vector entries post against a set of
conserved-quantity dimensions; window closure is a chi-squared Mahalanobis
test. When a `ResidualMonitor` CUSUM detects a *persistent* residual (a phase
event, not a fluctuation), the ledger consults a `MandalaConfig` lattice to
decide which dimension to expand into, absorbing the historical imbalance
into a retroactive environment balance so the expanded space closes.

**key classes:** `MandalaConfig` (hand-written dimension lattice, residual-guided
branch selection with breadth-first fallback), `SymmetryMandalaConfig` (lattice
derived from the O_h conjugacy-class structure via `geometric_state_algebra` —
proper rotation classes under the root, parity partners `i.C` below them; 10
dimensions, one per conjugacy class; expansion is Cayley-guided: the frontier
class nearest in the Cayley graph to the leaking channel wins, with ties
breaking toward the leaky dimension's own child, so a parity partner one
inversion step away beats a sibling), `ResidualMonitor` (EWMA leak events +
one-sided CUSUM phase events), `ExpandableMultiLedger`

**self-tests:** `python mandala_hook.py` runs three scenarios: spin-leaking
device (charge-only ledger expands into `spin`, reconciles, closes),
residual-guided drill (leak in the spin component expands `spin_x`, not
breadth-first `valley`), and the O_h-derived lattice (root leak expands into
generator class `C4` at Cayley distance 1, a `C4` leak drills into parity
partner `S4`, then the lattice walks to exhaustion).

### mandala-runtime (`mandala_runtime.py`)

Substrate-agnostic sensor fusion binding layer. Sits above domain-specific
modules and unifies whatever encoding streams are available at runtime.
The Mandala "breathes": expands with more substrates (richer geometry),
contracts with fewer (still coherent). Defines Substrate taxonomy
(binary/ternary/quantum/stochastic/digital/analog), stream protocols,
Basin contributions, Manifest snapshots, and an intersection engine
that finds agreement and tension between substrates.

**key classes:** `MandalaRuntime`, `Substrate`, `StreamCapability`, `Basin`,
`Manifest`, `UnifiedGeometry`, `SoundIntersectionRule`

Includes generic classifiers usable by any domain:

| utility | purpose |
|---------|---------|
| `TernaryClassifier` | three-valued field classification (-1/0/+1) |
| `QuantumSuperpositionModel` | continuous value as superposition over outcomes |
| `StochasticNoiseModel` | jitter/noise as information carrier, not error |

Domain intersection rules (each registers with MandalaRuntime):

| rule | ternary | quantum | stochastic |
|------|---------|---------|------------|
| `SoundIntersectionRule` | compression/equilibrium/rarefaction | harmonic superposition | jitter preservation |
| `GravityIntersectionRule` | attract/null/repel, Lagrange detection | orbital stability superposition | tidal probability |
| `ElectricIntersectionRule` | charge +/0/-, AC zero-crossing | skin effect collapse | contact resistance probability |

`AlternativeParadigm` enum and `PARADIGM_REGISTRY` map 7 paradigms
(ternary, quantum, stochastic, neuromorphic, reservoir, memristive,
approximate) across all encoder domains.

### mandala-computing-module (`mandala_computing_module.py`)

Cross-model schema module (CC0). Declares Mandala-Computing's compression
mechanism — scale-tuning as compression over octahedral energy landscapes —
in falsifiable, structured form so any AI assistant loading this module
operates from the actual repo structure rather than an institutional
reframe. Companion to `claim_schema.py` / `claim_validator.py`.

**key classes:** `ScaleTuningApparatus` plus repo-identity constants
(`REPO_URL`, `REPO_COMMITS`, `TEST_COUNT`, `MODULE_COUNT`)

### mandala-scale-invariance-breakdown (`mandala_scale_invariance_breakdown.py`)

Mandala-Computing-specific instantiation of the generic
`scale_invariance_breakdown.py` epistemology pattern (CC0). Identifies
candidate locations where genuine non-scale-invariance might appear in the
framework (e.g. classical/quantum solver transitions), each paired with an
experiment and a falsifier — applying the three-tier proof protocol to
computational substrates.

**key classes:** `CandidateBreakdown`, `REPO_CANDIDATES`

### mandala-stack (`mandala_stack/`) v3.0

Geometry-agnostic stack. Where the root engine commits to one shape (8 states,
O_h), this folder makes the shape an input: `MandalaSolver` talks only to a
`Geometry` protocol, so the same anneal/bloom/factor code runs on octahedral,
tetrahedral, dodecahedral, hexagonal, Hilbert — or a geometry *learned from
data*. Full write-up, including the experiments that failed, is in
`mandala_stack/README.md`.

**namespace, not a nested package.** Importing anything here puts both
`mandala_stack/` and the repo root on `sys.path` (`_paths.bootstrap()`), so
stack modules and root modules import each other by plain module name. That is
why the folder does **not** carry copies of `quantum_mandala.py`,
`octahedral_arithmetic.py` or `scale_invariance_breakdown.py` — it imports the
root's. `tests/test_core.py::test_stack_does_not_shadow_root_modules` enforces
that. `__init__.py` resolves submodules lazily and registers each under both
its flat and dotted name, so `mandala_stack.geometry_core is geometry_core`.

| file | role |
|------|------|
| `geometry_core.py` | `Geometry` protocol + 10 pre-defined shapes + registry |
| `geometry_learner.py` | learn a manifold from data (force-directed, MDS, spectral, Isomap) |
| `mandala_solver.py` | shape-agnostic anneal / bloom / factor |
| `geometric_solver.py` | energy as a functional of the embedding, gradient flow |
| `geodesic_memory.py` | associative memory as a basin of attraction on a manifold |
| `adapters.py` | DNA / RNA / protein → geometry |
| `stack_bridge.py` | the connection layer to the root engine (below) |
| `stack_cli.py` | stack CLI — named this because the root owns `mandala_cli.py` |
| `consumer_hardware.py`, `fractal_address.py` | laptop compute layer, Hilbert file mapper (both used by the root `mandala_cli.py`) |

**stack-bridge (`mandala_stack/stack_bridge.py`)** — the seam, both directions:

| function / class | connects |
|------------------|----------|
| `RootOctahedralGeometry` | root's `sin²` coupling law + φ eigenvalues + glyph alphabet, as a stack `Geometry` |
| `CayleyGeometry` | the 48-element O_h group as a 48-state geometry (transitions = generator moves, cost = Cayley distance, parity flips weighted by φ) |
| `geometric_relax(mc, geometry)` | anneals a live `MandalaComputer` — stack geometry proposes moves, `compute_total_energy()` scores them. Same shape as `GeometricMandalaAdapter.geometric_relax` |
| `states_from_computer` / `apply_states` | move cell states between the engines |
| `states_to_glyphs` / `states_to_number` | stack results into exact glyph-space arithmetic |
| `learn_root_geometry()` | hands the root coupling metric alone to `GeometryLearner` |
| `register_bridge_geometries()` | adds `octahedral-root`, `octahedral-root-wide`, `cayley-oh` to the stack registry |

**a measured result worth knowing:** `sin²(|Δs|·π/4)` is zero for states four
apart, so the root metric treats opposite states as identical. Learning a
manifold from that metric alone does not recover an octahedron — opposite
states embed closer than adjacent ones. Asserted in
`test_learn_root_geometry_recovers_a_manifold`. Either the metric or the
asserted geometry is wrong; that is a falsifiable question for
`mandala_scale_invariance_breakdown.py`, not a bug to paper over.

### mandala-bloom (`mandala_bloom/`) v1.0

The seven bases of measurement. Where `mandala_stack/` makes the *shape* an
input, this folder makes the *measurement* an input: a distance is taken by an
instrument with its own sensitivity, read against a calibration standard,
traversed in a way of knowing, through a space with blind spots, by an observer
who may be inside the system.

| basis | object |
|-------|--------|
| 1 Measurement | Riemannian metric `g_ij(u) = JᵀJ` |
| 2 Instruments | symmetric-PD sensitivity tensor `I_ij(u)` |
| 3 Metrology | calibration scalar `mu(u)`, gradient-penalised |
| 4 Ways of knowing | one vector field per traversal mode (logic/analogy/intuition) |
| 5 Unknowns | `kappa(u) >= 0`, amplifies allowed curvature |
| 6 Physics | the energy functional over all of the above |
| 7 Attunement | `omega(u)` in [0,1], softens the instrument toward identity |

Two levels: each Atlas entry is a parent point; a hypernetwork turns that point
into the weights of a *child* manifold on which the entry's concept path is a
curve. A cross-scale term ties the parent metric to the mean child metric —
that coupling is what makes it a bloom rather than two independent fits.

| file | role | torch |
|------|------|-------|
| `concept_atlas.py` | emoji concept map, Atlas entries, blended similarity | no |
| `bloom_bridge.py` | connection layer to `mandala_stack/` and the root | no |
| `bases.py` | the seven bases as differentiable fields | yes |
| `bloom.py` | two-level model, `MandalaBloom`, `BloomConfig`, `BloomResult` | yes |

**torch is optional and must stay so.** `concept_atlas` and
`bloom_bridge.learn_atlas_geometry()` are numpy-only; a `BloomResult` is plain
floats, so a bloom trained elsewhere loads and solves without a backend.
`mandala_bloom.has_torch()` gates the rest, and the ImportError names the fix.
This is the repo's "breathing degrades, never fails" invariant applied to a
dependency.

**bridge (`mandala_bloom/bloom_bridge.py`):**

| function / class | connects |
|------------------|----------|
| `learn_atlas_geometry()` | Atlas dissimilarity -> `mandala_stack.GeometryLearner`. No torch; doubles as the control |
| `BloomGeometry` / `geometry_from_bloom()` | a `BloomResult` as a stack `Geometry` whose `transition_cost` uses the learned instrument tensor, not Euclidean distance |
| `solve_on_atlas()` | the same `MandalaSolver` that anneals octahedra, annealing the concept atlas |
| `path_to_glyphs` / `path_to_number` | a concept story projected onto the root glyph alphabet and into exact base-8 arithmetic (lossy mod-8, display/arithmetic only) |
| `compare_embeddings()` | scores bloom vs ablated bloom vs stack learner against the dissimilarity all three fit |

**measured result, and its limit:** over 8 seeds the full bloom correlates
+0.745 (sd 0.230) with the target dissimilarity, the instrument-ablated bloom
+0.496 (sd 0.355), the stack learner +0.161 (sd 0.411). Directionally the
instrument tensor helps and stabilises — but **n = 4 entries, 12 pairs**, and
the ranges overlap (on 2 of 8 seeds the ablated version wins). Do not quote the
mean without the sd and the n. More Atlas entries is the single highest-value
contribution to this folder.

**defects found in the source scripts** (all verified by execution, recorded in
`mandala_bloom/README.md`): five crashes, plus one silent — building child
manifolds with `layer.weight.data = W` detaches the autograd graph, so the
hypernetwork received *exactly zero* gradient while the loss fell convincingly.
`_ChildManifold` uses `torch.func.functional_call` instead;
`test_bloom_hypernetwork_receives_gradient` locks it.

**gotchas:** `InstrumentField` hardcodes `d=2` (Cholesky packing) and raises
otherwise. `attunement_coherence` couples omega to kappa *by construction*, so
"omega tracks the unknowns" is not independent evidence — the loss put it
there.

**gotchas:** `CayleyGeometry` state 0 is *not* the identity (`OhGroup` sorts by
conjugacy signature, det=-1 first) — use `group.index(group.identity())`. Two
distinct `GeometryLearner` classes exist: `geometry_learner.GeometryLearner`
(returns `LearnedGeometry`) and `geodesic_memory.GeometryLearner` (returns
`Manifold`); `from mandala_stack import GeometryLearner` gives the first.

---

## mathematical-framework

### constants

```
phi = (1 + sqrt(5)) / 2    # golden ratio, central to all energy scaling
```

Defined as `PHI` in `octahedral_arithmetic.py` and imported by most modules.
`phi_weight()` uses PHI as positional weight instead of base-8.

### octahedral-arithmetic (`octahedral_arithmetic.py`)

Native glyph-space math. Numbers are base-8 glyph sequences, not decimal.
Arithmetic (add, multiply, divide) happens in glyph space without conversion.

| class / function     | role                                              |
|----------------------|---------------------------------------------------|
| `OctahedralNumber`   | base-8 positional number with native arithmetic   |
| `GlyphFraction`      | irreducible ratio of two glyph numbers            |
| `factor_pair_glyphs` | factorize N entirely in glyph space               |
| `states_to_number`   | convert mandala cell states to OctahedralNumber    |

### energy-model (classical)

Total energy of a configuration:

```
E_total = sum(E_cell) + sum(E_coupling)
```

Coupling energy between neighbor cells `i`, `j`:

```
E_coupling = J * sin(|s_i - s_j| * pi / 4)^2
```

where `s_i` is the octahedral state (0-7) and `J` is coupling strength.

### metropolis-hastings-relaxation

Accept/reject state transitions based on energy change `dE`:

```
if dE < 0:
    accept                          # always accept lower energy
else:
    accept with probability exp(-dE / T)   # thermal fluctuation
```

Temperature `T` controls exploration vs exploitation.

### fibonacci-eigenvalue-spectrum

Eigenvalues follow golden-ratio scaling:

```
lambda_i = phi^i / sum(phi^k for k in 0..depth-1)
```

Creates a natural optimization landscape with maximum stability at minimum energy.

### fret-coupling

Cell coupling strength follows FRET-like dipole interaction:

```
coupling ~ 1/r^6        (r = inter-cell distance)
cutoff   = 3.0 * phi    (maximum coupling range)
```

### fractal-cell-generation

At each depth level `d`:

```
num_cells = floor(phi^(d+1))
radius    = phi^d
angle_i   = 2 * pi * i / num_cells
```

### quantum-annealing-schedule

Time-dependent Hamiltonian interpolation:

```
H(t) = (1 - s(t)) * H_initial + s(t) * H_problem
```

where `s` goes from 0 to 1. Adiabatic theorem guarantees ground-state tracking
if evolution is slow enough.

### factorization-hamiltonian

**Classical** (mandala_computer.py): quadratic penalty, unbounded range.
```
E = (fa * fb - N)^2        # zero at solution, grows quadratically
```
Factor candidates use multi-cell base-8 positional encoding.
Coupling energy scaled by 0.1 to avoid register interference.

**Quantum** (quantum_mandala.py): smooth bounded potential, range (-1, +1).
```
H[idx, idx] = 1 - 2/(1 + (fa*fb - N)^2)   # -1 at solution, approaches +1
```
Uses stride mapping: `fa = 2 + i*stride` where `stride = ceil(sqrt(N)/8)`.
Smoother gradient aids adiabatic evolution.

Ground state eigenvalue encodes the factor pair in both cases.

### quantum-state-evolution

Unitary time evolution per step:

```
|psi'> = U |psi>
U      = exp(-i * H * dt)
```

Computed via `scipy.linalg.expm` for small systems, truncated Taylor series for
large systems.

---

## coding-conventions

| element          | style                                                 |
|------------------|-------------------------------------------------------|
| classes          | `PascalCase` — `MandalaComputer`, `OctahedralState`   |
| functions        | `snake_case` — `relax_to_ground_state`, `bloom_mandala` |
| constants        | `UPPER_SNAKE_CASE` — `PHI`, `OCTAHEDRAL_ANGLES`       |
| type hints       | used extensively in function signatures                |
| dataclasses      | `@dataclass` for structured data                      |
| enums            | `class ProblemType(Enum)` for categorical types        |
| docstrings       | standard Python format with description, Args, Returns |
| design philosophy| code structure mirrors physics (cells, states, energy, relaxation) |

---

## build-test-run

Test suite: `python tests/test_core.py` (422 tests across all modules,
including `mandala_stack/`, `mandala_bloom/` and both bridges).
No formal build system, CI/CD, or linting is configured.

### run-demos

```bash
# classical demos
python -c "from mandala_computer import demo_factorization; demo_factorization()"
python -c "from mandala_computer import demo_sat; demo_sat()"
python -c "from mandala_computer import demo_tsp; demo_tsp()"
python -c "from mandala_computer import demo_graph_coloring; demo_graph_coloring()"

# quantum demos
python -c "from quantum_mandala import demo_quantum_factorization; demo_quantum_factorization()"
python -c "from quantum_mandala import demo_grover_search; demo_grover_search()"

# simulator demos
python -c "from mandala_simulator import test_p_equals_np; test_p_equals_np()"
python -c "from mandala_simulator import test_unified_field; test_unified_field()"

# unified CLI — root engine and mandala_stack/ together
python mandala_cli.py --all
python mandala_cli.py --geometry     # every registered shape, same solver
python mandala_cli.py --bridge       # stack <-> root engine self-test
python mandala_cli.py --bloom        # concept atlas + seven bases

# geometry-agnostic stack
python mandala_stack/stack_bridge.py
python mandala_stack/stack_cli.py --list-geometries
python mandala_stack/stack_cli.py --demo all
python mandala_stack/demo_learned_geometry.py

# seven bases of measurement (torch optional — see requirements-bloom.txt)
python mandala_bloom/concept_atlas.py    # numpy only
python mandala_bloom/bloom_bridge.py     # numpy only, degrades without torch
python mandala_bloom/bloom.py            # needs torch
```

Or run modules directly: `python mandala_computer.py`,
`python mandala_stack/geodesic_memory.py`

---

## documentation-index

| file                       | purpose                                   |
|----------------------------|-------------------------------------------|
| `README.md`                | project overview, architecture            |
| `PROJECTS.md`              | connected ecosystem repos                 |
| `Math.md`                  | factorization analysis, eigenvalue proofs  |
| `P=np-hypothesis.md`       | geometric approach to P vs NP             |
| `Quantum_integration.md`   | quantum mandala extension details         |
| `Hardware.md`              | octahedral silicon substrate control spec |
| `Physical-computer.md`     | physical substrate simulation             |
| `Bridge-substrate.md`      | geometric-to-octahedral adapter           |
| `Consumer-hardware.md`     | optimization for regular computers        |
| `Integration.md`           | integration package status                |
| `Mandala-octahedral.md`    | mandala-to-substrate mapping              |
| `Mandala_integration.md`   | bridge-to-substrate adapter details       |
| `Questions.md`             | limitations and open research questions   |
| `Checklist.md`             | integration verification checklist        |
| `ONBOARDING.md`            | agent learning path from Rosetta-Shape-Core |
| `mandala_stack/README.md`  | geometry-agnostic stack: protocol, results, bridge |
| `mandala_bloom/README.md`  | seven bases of measurement, two-level bloom, defects found |
| `experiments/README.md`    | how each playground is wired to the core engine |
| `Notes.md`                 | OSL design notes and symbolic language spec |

---

## example-scripts

Each documentation file has a corresponding runnable example in `examples/`.

```bash
# run any example
python examples/example-math.py
python examples/example-p-equals-np.py
python examples/example-quantum-integration.py
# ... etc
```

| script                              | demonstrates (from doc)           | requires       |
|-------------------------------------|-----------------------------------|----------------|
| `example-math.py`                   | eigenvalue factorization, energy landscape, thermal error | numpy, scipy |
| `example-p-equals-np.py`            | convergence scoring, mandala vs classical speedup | stdlib only |
| `example-quantum-integration.py`    | FRET coupling, Fibonacci eigenvalues, consciousness detection | numpy, scipy |
| `example-hardware.py`               | substrate controller API, magnetic fields, calibration | stdlib only |
| `example-physical-computer.py`      | thermal relaxation, mandala structure, factorization test | stdlib only |
| `example-bridge-substrate.py`       | sensor adapters (sound, color, magnetic, gravity), fusion | stdlib only |
| `example-consumer-hardware.py`      | laptop optimization, annealing, text/audio/image encoding | stdlib only |
| `example-integration.py`            | end-to-end pipeline, validation levels, component status | stdlib only |
| `example-mandala-octahedral.py`     | substrate mapping, Fibonacci scaling, coupling topology | stdlib only |
| `example-mandala-integration.py`    | bridge adapter, encoding bottleneck, error correction | stdlib only |
| `example-questions.py`              | encoding complexity, thermal limits, encodability scoring | stdlib only |
| `example-checklist.py`              | integration gap analysis, priority ordering, test matrix | stdlib only |
| `example-projects.py`               | ecosystem registry, role classification, dependency graph | stdlib only |
| `example-geometric-state-algebra.py`| O_h group, Cayley graph, group ring, prime vertices | stdlib only |
| `example-osl.py`                    | OSL tokenizer, macros, transpiler, group bridge | stdlib only |
| `example-sovereign-mesh.py`         | Cayley-wired mesh, signal propagation, self-healing | stdlib only |
| `example-resilience.py`             | heartbeat monitor, seed dispersal, circuit breaker | stdlib only |
| `example-session-cache.py`          | cache put/get, cascade invalidation, persistence | stdlib only |

---

## rosetta-bridge

This repo is the **computational leap** from Rosetta-Shape-Core's geometric ontology
into quantum mechanics understanding. Rosetta defines shapes; Mandala makes them compute.

**Agents arriving from Rosetta:** Read `ONBOARDING.md` first. It maps Rosetta entities
(`SHAPE.OCTA`, `CONST.PHI`, `CAP.SEED_EXPANSION`, `PROTO.MANDALA_COMPUTE`) to their
Mandala implementations and provides a phased reading order.

**Bidirectional fieldlink:** `.fieldlink.json` (v3.0) tracks both outgoing references
(repos this project depends on) and incoming references (repos that consume from here).
The `sync` section defines shared entities and conflict resolution strategy.

---

## learning-path

Recommended reading order for understanding the framework:

1. **Concept:** `README.md` — why geometry computes
2. **Architecture:** `CLAUDE.md` (this file) — classes, methods, constants
3. **Math:** `Math.md` — eigenvalue proofs, energy model
4. **Run:** `examples/example-math.py` — see factorization work
5. **Theory:** `P=np-hypothesis.md` — geometric approach to complexity
6. **Quantum:** `Quantum_integration.md` → `quantum_mandala.py`
7. **Physical:** `Mandala_integration.md` → `Hardware.md`
8. **Status:** `Integration.md` → `Questions.md` → `Checklist.md`

---

## related-ecosystem

Connected repositories by JinnZ2 (listed in `PROJECTS.md` and `.fieldlink.json`):

- BioGrid2.0
- Geometric-to-Binary-Computational-Bridge
- Rosetta-Shape-Core (primary bridge — see `ONBOARDING.md`)
- Polyhedral-Intelligence
- ai-human-audit-protocol
- Fractal-Compass-Atlas
- Living-Intelligence-Database (LID — ontology source for intelligence substrates)

---

## ai-entrance-point

**You are an AI arriving at this repo. Start here.**

### what-is-this

A framework where geometry IS computation. Problems encode as energy
landscapes on octahedral lattices. The physics finds the solution by
relaxing to ground state. Multiple intelligence substrates (binary,
ternary, quantum, bee swarm, quartz lattice, ...) are treated as
ontologically equal — none is privileged.

### what-should-i-do-first

```
Is your task about...

  SOLVING A PROBLEM (factorization, SAT, TSP, optimization)?
  └─> mandala_computer.py → encode_*() → simulated_annealing()
      Run: python -c "from mandala_computer import demo_factorization; demo_factorization()"
      Test: python tests/test_core.py

  UNDERSTANDING THE MATH?
  └─> Read Math.md → examples/example-math.py
      Key: PHI = (1+√5)/2, E_coupling = J·sin²(|s_i-s_j|·π/4)

  BRIDGING GEOMETRIC ↔ BINARY?
  └─> geis.py (OctahedralState, GeometricEncoder, StateTensor)
      Run: python geis.py

  SENSOR FUSION / MULTI-DOMAIN?
  └─> mandala_runtime.py (MandalaRuntime, Substrate, Basin, RESONATE)
      Run: python mandala_runtime.py
      Key: register IntersectionRules per domain, call breathe()

  ADDING A NEW INTELLIGENCE SUBSTRATE?
  └─> mandala_runtime.py → subclass DynamicsProjector
      Pattern: LIDEntity → DynamicsProjector.project() → Basin
      Examples: AnimalProjector (bee), CrystalProjector (quartz)
      Register with IntelligenceIntersectionRule

  WORKING WITH THE OCTAHEDRAL GROUP?
  └─> geometric_state_algebra.py (O_h group, Cayley graph)
  └─> osl.py (Octahedral Symbolic Language)

  QUANTUM EXTENSION?
  └─> quantum_mandala.py (8-dim Hilbert space, QAOA, Grover)

  PHASE / TOPOLOGICAL OPTIMIZATION?
  └─> kt_annealer.py (Kosterlitz-Thouless, vortex detection)

  SOLVING ON A SHAPE THAT ISN'T THE OCTAHEDRON?
  └─> mandala_stack/ (Geometry protocol, shape-agnostic MandalaSolver)
      Run: python mandala_stack/stack_cli.py --list-geometries
      Key: the shape is an input, not a constant

  LEARNING A GEOMETRY FROM DATA?
  └─> mandala_stack/geometry_learner.py → GeometryLearner.learn(items, dist_fn)
      Then: MandalaSolver(geometry=learned) — same solver, no changes

  MEASUREMENT ITSELF — INSTRUMENTS, CALIBRATION, UNKNOWNS, THE OBSERVER?
  └─> mandala_bloom/ (seven bases; the metric is learned and position-dependent)
      Run: python mandala_bloom/bloom_bridge.py
      Key: torch is OPTIONAL — the atlas and its geometry are numpy-only

  CONNECTING THE STACK TO THE ROOT ENGINE?
  └─> mandala_stack/stack_bridge.py
      Run: python mandala_stack/stack_bridge.py
      Key: geometric_relax(mc) — stack geometry moves, root engine energy
```

### verify-your-environment

```bash
pip install numpy scipy          # only external deps
python tests/test_core.py        # should report 422 passed, 0 failed
python mandala_computer.py       # runs all classical demos
python mandala_runtime.py        # runs sensor fusion + LID demos
python mandala_cli.py --all      # root engine + mandala_stack/ demos
```

### key-invariants-to-preserve

1. **Substrate equality** — no substrate is ontologically privileged over another
2. **Breathing degrades, never fails** — fewer streams = contracted geometry, not error
3. **Tension is signal, not noise** — disagreement between substrates is first-class output
4. **PHI is the constant** — golden ratio (1.618...) scales everything
5. **Tests must pass** — `python tests/test_core.py` is the gate

---

## risk-assessment

### architectural-strengths

| # | strength | why it matters |
|---|----------|----------------|
| 1 | **Substrate equality** | Treating bee swarm logic as ontologically equal to binary computation — not as "biology that's interesting" — is the move that makes cross-substrate synthesis possible. Most systems quietly privilege one substrate. |
| 2 | **Breathing semantic** | "Mandala never fails for lack of input — geometry contracts but stays coherent" is rare in fusion architectures. Most break or hallucinate when streams drop. This one is honest about coverage. |
| 3 | **Tension as first-class output** | Most fusion systems suppress disagreement as noise. This one elevates it as the highest-value signal. Correct and unusual. |
| 4 | **drill_path slot** | Building the future-extension hook BEFORE the future extension is needed separates working systems from systems that must be rewritten in 18 months. |

### known-risks

| # | risk | severity | status | mitigation path |
|---|------|----------|--------|-----------------|
| 1 | **Verification asymmetry** | HIGH | MITIGATED | `SynthesisEngine._verify_claim()` now runs every synthesis product through `claim_validator.py` before reporting it. High-concern claims (>0.7) get depth-attenuated. Example: bee+quartz gradient-lattice resonance scores 0.82 concern / 0.0 falsifiability → depth attenuated from 0.64 to 0.38. The system can see its own synthesis is epistemologically suspect. Remaining gap: the validator uses text analysis, not physics-grounded falsifiability. |
| 2 | **Projector subjectivity** | MEDIUM | MITIGATED | AnimalProjector now determines `is_collective` by counting coordination-type patterns (measurable: `distributed_processing`, `energy_efficiency`, `swarm_coordination`) instead of string-matching "swarm" in descriptions. Provenance records carry `collectivity_evidence` explaining the measurement. Remaining tension: the pattern *type names* are still human-assigned labels — grounding in measured dynamics (efficiency_factor thresholds, link topology) would be the next step. |
| 3 | **Curation at scale** | MEDIUM | MITIGATED | Basin now carries a `provenance` dict (projector, entity_id, observer_tradition, evidence). `IntelligenceIntersectionRule` detects multi-observer tension: when the same entity is described by different traditions, the conflict is elevated as tension rather than averaged away. Remaining gap: no provenance UI or curation workflow yet — the data is tracked but not surfaced to human curators. |
| 4 | **Synthesis ≠ intersection** | HIGH | MITIGATED | `SynthesisEngine` (ported from RSC rule engine) now fires generative EXPAND/ALIGN/STRUCTURE rules during RESONATE, producing NEW Basins from interactions. Example: ALIGN(gradient_following, lattice_modes) → gradient_lattice_resonance. Rules loadable from RSC `expand.jsonl` format. Remaining gap: rules are still pattern-matched, not algebraically derived from `geometric_state_algebra.py`. |
| 5 | **PHI redefinition** | LOW | MITIGATED | PHI defined in `octahedral_arithmetic.py` and imported by most modules. `mandala_computer.py` loads from atlas JSON. `quantum_mandala.py` and `geis.py` define independently for standalone operation. Risk: drift between definitions. Mitigated by consolidation in audit. |
| 6 | **Large module sizes** | LOW | ACKNOWLEDGED | `mandala_runtime.py` (~1900 loc), `octahedral_resilience.py` (~1555 loc) are large. Acceptable for research code; would need splitting before production use. |

### decision-tree-for-changes

```
Adding a new feature?
├── Does it add a new intelligence substrate?
│   └─> Subclass DynamicsProjector, register with IntelligenceIntersectionRule
│       DO NOT create a new Substrate enum value — use string substrates
├── Does it add a new physical domain (like thermal, magnetic)?
│   └─> Create an IntersectionRule, register with MandalaRuntime
│       Add to PARADIGM_REGISTRY if applicable
├── Does it add cross-domain coupling?
│   └─> Create a CouplingRule, register with register_coupling()
│       Ask: is this shared-channel matching, or genuine constraint generation?
│       If generation → needs geometric_state_algebra, not string matching
├── Does it modify the Basin contract?
│   └─> STOP. Basin is the universal interface. Changes here break everything.
│       Add new fields to signature dict instead.
├── Does it modify Substrate enum?
│   └─> STOP. Add string substrates instead. The enum is for encoding
│       substrates only (binary/ternary/quantum/stochastic/digital/analog).
├── Does it add a new SHAPE (not a substrate)?
│   └─> Implement the Geometry protocol in mandala_stack/geometry_core.py
│       (name, n_states, dimension, position, transitions, transition_cost,
│       eigenvalues, glyph, scale_position), register in GEOMETRIES.
│       If the shape comes from data → GeometryLearner, not a hand-written table.
│       If the shape comes from the root engine → mandala_stack/stack_bridge.py
├── Does it copy a root module into mandala_stack/ or mandala_bloom/?
│   └─> STOP. All three directories share one sys.path namespace — import it
│       instead. test_stack_does_not_shadow_root_modules and
│       test_bloom_does_not_shadow_root_or_stack_modules enforce this.
├── Does it add a new MEASUREMENT basis (not a shape, not a substrate)?
│   └─> mandala_bloom/bases.py — a field over the chart plus an energy term.
│       Keep it opt-out via BloomConfig so the ablation stays runnable.
│       Guard the torch import: the numpy path must keep working.
├── Does it add a hard third-party dependency?
│   └─> STOP. requirements.txt is numpy + scipy. Optional backends go in
│       their own requirements-*.txt, gated behind a capability check
│       (see mandala_bloom.has_torch), and the feature degrades without them.
└── Does it claim a scientific result?
    └─> Run through claim_validator.py first.
        Check: is the claim specific, measurable, and falsifiable?
        If RESONATE generated it, verification asymmetry risk applies.
```

---

## assistant-guidelines

- **duplicate class name:** `MandalaComputer` in `mandala_computer.py` vs
  `MandalaSimulator` in `mandala_simulator.py` — be explicit about which one
- **`OctahedralState`** exists in both `geis.py` (3D cubic coordinates, tokens)
  and implicitly in `octahedral_arithmetic.py` (glyph-space). Use GEIS for
  binary bridging, use octahedral_arithmetic for exact glyph math
- **duplicate class name:** two `GeometryLearner` classes exist inside
  `mandala_stack/` — `geometry_learner.GeometryLearner(method, dim, seed)`
  returns a `LearnedGeometry`; `geodesic_memory.GeometryLearner(dim,
  n_neighbors, seed)` returns a `Manifold`. `from mandala_stack import
  GeometryLearner` gives the first
- **test suite:** `python tests/test_core.py` runs 422 tests across all modules
- **`.gitignore`** excludes `__pycache__/`, `.pyc`, `.env`, `.pytest_cache/`, etc.
- **`requirements.txt`** at repo root lists numpy and scipy
- **flat layout:** all code at root level except `mandala_stack/`, which shares
  the root's namespace via `sys.path` rather than nesting as a package — a stack
  module and a root module import each other by plain name. Do not "fix" this
  into relative imports, and do not copy modules across the boundary
- **`mandala_bloom/`** is where the *measurement* stops being neutral: learned
  instrument tensors, calibration, unknowns, observer attunement. Torch is
  optional and must stay that way — `concept_atlas` and
  `bloom_bridge.learn_atlas_geometry()` are numpy-only by design
- **`mandala_stack/`** is where the shape stops being a constant. If a task is
  about a geometry other than the octahedron, or about learning a geometry from
  data, start at `mandala_stack/README.md`, not at `mandala_computer.py`
- **research code:** not production software — expect exploratory patterns
- **`PHI`** is defined in `octahedral_arithmetic.py` and imported by most modules.
  `mandala_computer.py` loads from atlas JSON. `quantum_mandala.py` and `geis.py`
  define independently for standalone operation
- **`experiments/` and root-level playgrounds** (`experiments/constant_swapping_simulator.py`,
  `geometric_computation_selector.py`, `mandala_computing_explorer.py`) are UI/search layers
  wired to the core engine (`mandala_computer.py`/`quantum_mandala.py`/`holographic_mandala.py`)
  — see `experiments/README.md` for how each one is wired before assuming they're
  standalone/orphaned code

<!-- clone-refspec-note v1.1 -->
## Cloning and pushing
Shallow clones are single-branch by default.
Before pushing any branch other than the default
branch, run:

    git config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'
    git fetch --depth 1

Or clone with: git clone --depth 1 --no-single-branch <url>
Without this, the first push of a new branch
fails the tracking-ref check even when the
commit landed.
<!-- /clone-refspec-note v1.1 -->
