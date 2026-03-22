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
├── mandala_computer.py        # core classical simulator (~600 loc)
├── quantum_mandala.py         # quantum extension (~600 loc)
├── mandala_simulator.py       # lightweight symbolic simulator (~115 loc)
├── .fieldlink.json            # ecosystem metadata
├── README.md                  # project overview
├── PROJECTS.md                # connected repos
├── LICENSE                    # MIT
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

---

## key-modules

### mandala-computer (`mandala_computer.py`)

Core classical engine. Encodes problems into geometric configurations and solves
via Metropolis-Hastings relaxation.

**classes:**

| class              | role                                              |
|--------------------|---------------------------------------------------|
| `OctahedralState`  | single cell in octahedral configuration (dataclass)|
| `MandalaCell`      | computational cell with position, state, neighbors (dataclass) |
| `ProblemType`      | enum: `FACTORIZATION`, `SAT`, `TSP`, `GRAPH_COLORING`, `OPTIMIZATION` |
| `MandalaComputer`  | main computation engine                           |

**key methods on `MandalaComputer`:**

| method                     | purpose                                         |
|----------------------------|------------------------------------------------|
| `bloom_mandala()`          | expand symbol core into nested fractal rings    |
| `encode_factorization(N)`  | bipartite tensor encoding for integer factoring |
| `encode_sat(clauses)`      | boolean satisfiability encoding                 |
| `encode_tsp(cities)`       | traveling salesman ring topology                |
| `relax_step()`             | single Metropolis-Hastings step                 |
| `relax_to_ground_state()`  | iterative minimization to solution              |
| `compute_total_energy()`   | sum of cell + coupling energies                 |

### quantum-mandala (`quantum_mandala.py`)

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
| `quantum_annealing()`           | adiabatic optimization                    |
| `grover_search()`               | quantum search algorithm                  |
| `_build_hamiltonian()`          | problem-specific energy operator          |
| `_build_octahedral_rotation()`  | 8x8 unitary rotation gates               |
| `_extract_quantum_solution()`   | measure and decode solution               |

### mandala-simulator (`mandala_simulator.py`)

Lightweight symbolic simulator for quick experiments and demos. Contains a
**separate** `MandalaComputer` class (not the same as in `mandala_computer.py`).

---

## mathematical-framework

### constants

```
phi = (1 + sqrt(5)) / 2    # golden ratio, central to all energy scaling
```

Defined as `PHI` in all three modules.

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

For two-cell system (64-dimensional space):

```
H[i*8+j, i*8+j] = -1.0   if (2+i) * (2+j) == N
                 = +1.0   otherwise
```

Ground state eigenvalue encodes the factor pair.

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
| `example-questions.py`              | encoding complexity, thermal limits, encodability scoring | stdlib only |
| `example-checklist.py`              | integration gap analysis, priority ordering, test matrix | stdlib only |
| `example-projects.py`               | ecosystem registry, role classification, dependency graph | stdlib only |

---

## related-ecosystem

Connected repositories by JinnZ2 (listed in `PROJECTS.md` and `.fieldlink.json`):

- BioGrid2.0
- Geometric-to-Binary-Computational-Bridge
- Rosetta-Shape-Core
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
