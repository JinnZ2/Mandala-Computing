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
├── kt_annealer.py             # KT phase annealer + symmetry detector (~430 loc)
├── mandala_runtime.py         # substrate-agnostic sensor fusion binding (~1900 loc)
├── membrane.py                # boundary computation primitive (~470 loc)
├── claim_validator.py         # epistemological claim validation (~500 loc)
├── glyph_convert.py           # human decimal-to-glyph converter (~355 loc)
├── mandala_simulator.py       # lightweight symbolic simulator (~250 loc)
├── ONBOARDING.md              # agent learning path from Rosetta-Shape-Core
├── .fieldlink.json            # ecosystem metadata (v3.0, bidirectional)
├── .gitignore                 # excludes __pycache__/, *.pyc, .env, etc.
├── requirements.txt           # numpy, scipy
├── README.md                  # project overview
├── PROJECTS.md                # connected repos
├── LICENSE                    # MIT
├── examples/                  # 20 runnable example scripts + benchmark
├── tests/test_core.py         # 319-test suite
└── [17 .md files]             # theory, hardware, integration, proofs, notes
```

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

**key classes:** `OhElement`, `OhGroup`, `CayleyGraph`, `GroupRingElement`,
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

**key classes:** `OctahedralSessionCache`

### osl (`osl.py`)

Octahedral Symbolic Language v1.0 — a compact token language for expressing
octahedral geometry operations. Includes a registry of vertex glyphs and animal
macros, a tokenizer, parity verifier, macro expander, transpiler (OSL to Python),
and a bridge mapping OSL trajectories to O_h group elements.

**key classes:** `OSLRegistry`, `OSLTokenizer`, `OSLParityVerifier`,
`OSLMacroExpander`, `OSLTranspiler`, `OSLGroupBridge`

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

Test suite: `python tests/test_core.py` (319 tests across all modules).
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
```

Or run modules directly: `python mandala_computer.py`

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
```

### verify-your-environment

```bash
pip install numpy scipy          # only external deps
python tests/test_core.py        # should report 297 passed, 0 failed
python mandala_computer.py       # runs all classical demos
python mandala_runtime.py        # runs sensor fusion + LID demos
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
- **test suite:** `python tests/test_core.py` runs 319 tests across all modules
- **`.gitignore`** excludes `__pycache__/`, `.pyc`, `.env`, `.pytest_cache/`, etc.
- **`requirements.txt`** at repo root lists numpy and scipy
- **flat layout:** all code at root level, no package hierarchy
- **research code:** not production software — expect exploratory patterns
- **`PHI`** is defined in `octahedral_arithmetic.py` and imported by most modules.
  `mandala_computer.py` loads from atlas JSON. `quantum_mandala.py` and `geis.py`
  define independently for standalone operation

