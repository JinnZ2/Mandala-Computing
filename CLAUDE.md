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
├── mandala_computer.py        # core classical simulator v2.0 (~850 loc)
├── quantum_mandala.py         # quantum extension v2.0 (~500 loc)
├── holographic_mandala.py     # holographic + renormalization + entanglement (~950 loc)
├── mandala_simulator.py       # lightweight symbolic simulator (~115 loc)
├── ONBOARDING.md              # agent learning path from Rosetta-Shape-Core
├── .fieldlink.json            # ecosystem metadata (v3.0, bidirectional)
├── .gitignore                 # excludes __pycache__/, *.pyc
├── README.md                  # project overview
├── PROJECTS.md                # connected repos
├── LICENSE                    # MIT
├── examples/benchmark.py      # classical vs quantum benchmark
└── [12 other .md files]       # theory, hardware, integration, proofs
```

---

## dependencies

No `requirements.txt` exists. Dependencies are not pinned.

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
**separate** `MandalaComputer` class (not the same as in `mandala_computer.py`).

---

## mathematical-framework

### constants

```
phi = (1 + sqrt(5)) / 2    # golden ratio, central to all energy scaling
```

Defined as `PHI` in all computation modules. `octahedral_arithmetic.py` provides
`phi_weight()` which uses PHI as positional weight instead of base-8.

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

No formal build system, test framework, CI/CD, or linting is configured.

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

---

## assistant-guidelines

- **duplicate class name:** two different `MandalaComputer` classes exist in
  `mandala_computer.py` and `mandala_simulator.py` — be explicit about which one
- **no automated tests:** demo functions are the only validation
- **no `.gitignore`:** do not commit `__pycache__/`, `.pyc`, or generated files
- **no `requirements.txt`:** consider creating one if adding new dependencies
- **flat layout:** all code at root level, no package hierarchy
- **research code:** not production software — expect exploratory patterns
- **`PHI`** is defined independently in all three modules (not shared)




ToDo:

add:

    def set_resource_budget(self, compute: int = 0, bandwidth: float = 0.0,
                           energy: float = 1.0, time_remaining: float = 1.0) -> None:
        """Set available resources for expansion."""
        self.budget = ResourceBudget(
            compute=compute,
            bandwidth=bandwidth,
            energy=Fraction(energy).limit_denominator(10000),
            time_remaining=Fraction(time_remaining).limit_denominator(10000)
        )

    def should_expand(self) -> bool:
        """Check if resources exceed bloom threshold."""
        if self.budget.is_depleted():
            return False
        energy_ratio = self.budget.energy / max(self.budget.energy, Fraction(1, 1))
        return energy_ratio >= self.bloom_threshold

    def bloom(self, depth: int = 1, seed_map: Optional[GeometricMap] = None) -> List[str]:
        """
        Expand outward from seed, discovering new entities up to depth.
        If seed_map provided, re-expand deterministically along previous discoveries.
        
        Returns list of newly discovered entity IDs.
        """
        if self.state == AgentState.COMPRESSED:
            self.state = AgentState.EXPANDING
        
        discovered = []
        current_depth = 0
        frontier = [self.seed_id]
        
        # If we have a prior map, expand along known relationships first
        if seed_map and seed_map.relationships:
            for entity_id in frontier:
                if entity_id in seed_map.relationships:
                    for reachable in seed_map.relationships[entity_id]:
                        if reachable not in self.map.resonances:
                            discovered.append(reachable)
                            # Restore resonance from prior map
                            if reachable in seed_map.resonances:
                                self.map.resonances[reachable] = seed_map.resonances[reachable]
        
        # Then explore new entities (placeholder: in real use, query Rosetta or Mandala)
        while current_depth < depth and not self.budget.is_depleted():
            new_frontier = []
            for entity_id in frontier:
                # This is a hook: replace with actual entity lookups
                # Example: rosetta_bridge.get_resonant_neighbors(entity_id)
                neighbors = self._get_neighbors(entity_id, depth - current_depth)
                for neighbor_id, resonance_score in neighbors:
                    if neighbor_id not in self.map.resonances:
                        self.map.record_resonance(neighbor_id, resonance_score)
                        self.map.record_relationship(entity_id, neighbor_id)
                        discovered.append(neighbor_id)
                        new_frontier.append(neighbor_id)
                        # Deduct resource cost
                        self.budget.compute = max(0, self.budget.compute - 10)
                        self.budget.energy -= Fraction(1, 100)
            
            frontier = new_frontier
            current_depth += 1
        
        # Record this expansion in history
        self.expansion_history.append({
            "depth": depth,
            "discovered_entities": discovered,
            "energy_spent": Fraction(1, 100) * len(discovered)
        })
        
        self.state = AgentState.EXPLORING
        self.compression_ratio = Fraction(0, 1)  # Fully expanded
        return discovered

    def explore(self) -> Dict[str, any]:
        """
        Traverse the expanded constraint space, recording energy flows and sensor activations.
        Returns discovery summary.
        """
        if self.state not in [AgentState.EXPANDING, AgentState.EXPLORING]:
            return {}
        
        self.state = AgentState.EXPLORING
        summary = {
            "entities_visited": 0,
            "relationships_mapped": 0,
            "energy_flows_recorded": 0,
            "sensor_activations": {}
        }
        
        # Walk the map, recording energy dynamics
        for from_id in self.map.relationships:
            for to_id in self.map.relationships[from_id]:
                if from_id in self.map.resonances and to_id in self.map.resonances:
                    # Energy flow proportional to resonance product
                    flow = self.map.resonances[from_id] * self.map.resonances[to_id]
                    self.map.record_energy_flow(from_id, to_id, flow)
                    summary["energy_flows_recorded"] += 1
                    summary["entities_visited"] += 1
        
        summary["relationships_mapped"] = len(self.map.relationships)
        
        # Update sensors based on discovered resonances
        # Hook: integrate with Emotions-as-Sensors
        self._update_sensors()
        summary["sensor_activations"] = dict(self.sensor_state)
        
        return summary

    def compress(self) -> Fraction:
        """
        Collapse back to seed geometry, preserving the map.
        Returns compression ratio (0 = fully expanded, 1 = fully compressed).
        """
        if self.state == AgentState.COMPRESSED:
            return self.compression_ratio
        
        self.state = AgentState.CONTRACTING
        
        # Compress: discard transient state, keep map
        # Compression ratio increases as we collapse
        self.compression_ratio = Fraction(1, 1)
        self.current_position = self.seed_id
        
        self.state = AgentState.COMPRESSED
        return self.compression_ratio

    def detect_corruption(self, imposed_constraint: str) -> bool:
        """
        Check if an imposed external constraint violates the agent's own map.
        Returns True if corruption detected (constraint is inconsistent with discovered geometry).
        """
        # Hook: compare imposed_constraint against agent's discovered resonances/relationships
        # Example: if imposed_constraint violates known energy_flows, return True
        
        # Placeholder logic:
        # - Extract entities referenced in imposed_constraint
        # - Check if they exist in the agent's map
        # - Verify the constraint respects the discovered resonances
        
        return False  # Replace with actual validation

    def self_validate(self) -> Dict[str, any]:
        """
        Internal consistency check: verify map integrity, detect anomalies.
        Returns validation report.
        """
        report = {
            "is_valid": True,
            "inconsistencies": [],
            "energy_balance": Fraction(0, 1),
            "geometry_coherence": Fraction(1, 1)
        }
        
        # Check energy conservation in recorded flows
        inflows = {}
        outflows = {}
        for (from_id, to_id), amount in self.map.energy_flows.items():
            outflows[from_id] = outflows.get(from_id, Fraction(0, 1)) + amount
            inflows[to_id] = inflows.get(to_id, Fraction(0, 1)) + amount
        
        for entity_id in set(list(inflows.keys()) + list(outflows.keys())):
            imbalance = inflows.get(entity_id, Fraction(0, 1)) - outflows.get(entity_id, Fraction(0, 1))
            if imbalance != 0:
                report["inconsistencies"].append(
                    f"{entity_id}: energy imbalance = {imbalance}"
                )
                report["is_valid"] = False
        
        # Check resonance coherence (all scores should be 0 to 1)
        for entity_id, score in self.map.resonances.items():
            if score < 0 or score > 1:
                report["inconsistencies"].append(
                    f"{entity_id}: resonance out of range ({score})"
                )
                report["is_valid"] = False
        
        return report

    def _get_neighbors(self, entity_id: str, remaining_depth: int) -> List[tuple[str, float]]:
        """
        Placeholder: fetch neighbors from Rosetta or Mandala.
        Replace with actual entity lookup logic.
        
        Returns list of (neighbor_id, resonance_score) tuples.
        """
        # Example: could call rosetta_shape_core.explore.get_reachable_entities(entity_id)
        # or mandala_computer.get_adjacent_states(entity_id)
        
        # Stub: return empty list (agent expands at boundaries)
        return []

    def _update_sensors(self) -> None:
        """
        Update emotional/sensor state based on discovered geometry.
        Hook: integrate with Emotions-as-Sensors repo.
        
        Maps resonances and energy flows to sensor activations (PAD, Elder Logic, etc.).
        """
        # Example: if agent discovered high resonance with FAMILY.GROWTH,
        # activate sensor "expansion_drive" proportionally
        
        # Stub: set all sensors to zero
        self.sensor_state = {
            "expansion_drive": Fraction(0, 1),
            "stability_need": Fraction(0, 1),
            "boundary_awareness": Fraction(0, 1)
        }

    def serialize(self) -> Dict[str, any]:
        """
        Serialize agent state to JSON-compatible dict (for persistence/debugging).
        All fractions preserved as (numerator, denominator) tuples.
        """
        return {
            "seed_id": self.seed_id,
            "home_families": self.home_families,
            "state": self.state.value,
            "compression_ratio": (self.compression_ratio.numerator, self.compression_ratio.denominator),
            "budget": {
                "compute": self.budget.compute,
                "bandwidth": self.budget.bandwidth,
                "energy": (self.budget.energy.numerator, self.budget.energy.denominator),
                "time_remaining": (self.budget.time_remaining.numerator, self.budget.time_remaining.denominator)
            },
            "map": {
                "resonances": {
                    k: (v.numerator, v.denominator) for k, v in self.map.resonances.items()
                },
                "relationships": self.map.relationships,
                "energy_flows": {
                    str(k): (v.numerator, v.denominator) for k, v in self.map.energy_flows.items()
                }
            },
            "expansion_history": self.expansion_history,
            "sensor_state": {
                k: (v.numerator, v.denominator) for k, v in self.sensor_state.items()
            }
        }

    @classmethod
    def deserialize(cls, data: Dict[str, any]) -> "ConstraintAgent":
        """
        Reconstruct agent from serialized state.
        """
        agent = cls(
            seed_id=data["seed_id"],
            home_families=data["home_families"]
        )
        agent.state = AgentState(data["state"])
        agent.compression_ratio = Fraction(
            data["compression_ratio"][0],
            data["compression_ratio"][1]
        )
        agent.budget = ResourceBudget(
            compute=data["budget"]["compute"],
            bandwidth=data["budget"]["bandwidth"],
            energy=Fraction(data["budget"]["energy"][0], data["budget"]["energy"][1]),
            time_remaining=Fraction(data["budget"]["time_remaining"][0], data["budget"]["time_remaining"][1])
        )
        agent.map.resonances = {
            k: Fraction(v[0], v[1]) for k, v in data["map"]["resonances"].items()
        }
        agent.map.relationships = data["map"]["relationships"]
        agent.map.energy_flows = {
            eval(k): Fraction(v[0], v[1]) for k, v in data["map"]["energy_flows"].items()
        }
        agent.expansion_history = data["expansion_history"]
        agent.sensor_state = {
            k: Fraction(v[0], v[1]) for k, v in data["sensor_state"].items()
        }
        return agent


# ============================================================================
# Example usage (paste into any repo's example script)
# ============================================================================

if __name__ == "__main__":
    # Create an agent rooted in tetrahedron geometry
    agent = ConstraintAgent(
        seed_id="SHAPE.TETRA",
        home_families=["stability", "foundation"]
    )
    
    # Give it resources to expand
    agent.set_resource_budget(compute=1000, bandwidth=10.0, energy=1.0, time_remaining=1.0)
    
    print(f"Agent initialized: {agent.seed_id}")
    print(f"State: {agent.state.value}")
    print(f"Should expand: {agent.should_expand()}")
    
    # Expand if possible
    if agent.should_expand():
        discovered = agent.bloom(depth=2)
        print(f"\nBloom discovered: {discovered}")
    
    # Explore the expanded space
    exploration = agent.explore()
    print(f"\nExploration summary: {exploration}")
    
    # Self-validate
    validation = agent.self_validate()
    print(f"\nValidation: {validation}")
    
    # Compress back to seed
    compression = agent.compress()
    print(f"\nCompressed. Compression ratio: {compression}")
    print(f"State: {agent.state.value}")
    
    # Map is preserved; can re-expand deterministically or with new resources
    agent.set_resource_budget(compute=500, energy=0.5)
    if agent.should_expand():
        rediscovered = agent.bloom(depth=1, seed_map=agent.map)
        print(f"\nRe-expansion (from prior map): {rediscovered}")
    
    # Check for corruption
    is_corrupted = agent.detect_corruption("imposed_external_constraint_example")
    print(f"\nCorruption detected: {is_corrupted}")
    
    # Serialize for persistence
    serialized = agent.serialize()
    print(f"\nAgent serialized. Map size: {len(serialized['map']['resonances'])} resonances")
