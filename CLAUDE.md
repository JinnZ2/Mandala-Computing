# CLAUDE.md

## Project Overview

Mandala Computing is a research framework for solving hard computational problems (NP-complete, factorization, optimization) through **geometric intelligence** — using nested geometric structures with octahedral symmetry and golden ratio optimization. Instead of algorithmic search, computation works by relaxing physical/simulated systems to their ground state.

**License:** MIT (JinnZ2)
**Status:** Research/conceptual phase with working simulators

## Repository Structure

```
Mandala-Computing/
├── mandala_computer.py      # Core simulator (~600 lines) — classical octahedral relaxation
├── quantum_mandala.py       # Quantum extension (~600 lines) — 8D Hilbert space, annealing
├── mandala_simulator.py     # Lightweight symbolic simulator (~115 lines)
├── .fieldlink.json          # Ecosystem metadata (links to BioGrid2.0, multilingual layers)
├── README.md                # Project overview and architecture
├── PROJECTS.md              # Connected ecosystem repositories
├── LICENSE                  # MIT License
└── [12 other .md files]     # Theory, hardware specs, integration docs, math proofs
```

**No subdirectories** — all source and documentation lives at the root level.

## Languages and Dependencies

**Language:** Python 3

**Required dependencies (not pinned — no requirements.txt exists):**
- `numpy` — numerical arrays, linear algebra
- `scipy` — eigenvalue decomposition (`scipy.linalg.eigh`)

**Standard library imports:** `dataclasses`, `enum`, `typing`, `time`, `math`, `random`

**Optional:** `matplotlib` (referenced in README for visualization, not imported in code)

## Key Modules

### mandala_computer.py
Core computation engine. Classes: `OctahedralState`, `MandalaCell`, `ProblemType` (enum), `MandalaComputer`. Encodes problems (factorization, SAT, TSP, graph coloring) into geometric configurations and solves via Metropolis-Hastings relaxation.

### quantum_mandala.py
Quantum extension using 8-dimensional Hilbert space. Classes: `QuantumMandalaCell`, `QuantumMandalaComputer`. Adds quantum annealing, Grover search, and entanglement-based coupling.

### mandala_simulator.py
Simplified symbolic simulator for quick experiments and educational demos. Separate `MandalaComputer` class (lighter than the one in `mandala_computer.py`).

## Coding Conventions

- **Classes:** PascalCase (`MandalaComputer`, `OctahedralState`)
- **Functions/methods:** snake_case (`relax_to_ground_state`, `bloom_mandala`)
- **Constants:** UPPER_SNAKE_CASE (`PHI`, `OCTAHEDRAL_ANGLES`)
- **Type hints:** Used extensively in function signatures
- **Dataclasses:** Used for structured data (`@dataclass`)
- **Enums:** Used for categorical types (`class ProblemType(Enum)`)
- **Docstrings:** Standard Python format with descriptions, Args, Returns
- **Design philosophy:** Code structure mirrors physics concepts (cells, states, energy, relaxation)

## Build, Test, and Run

**No formal build system, test framework, CI/CD, or linting is configured.**

### Running demos

Each module has demo functions that serve as informal tests:

```bash
# mandala_computer.py demos
python -c "from mandala_computer import demo_factorization; demo_factorization()"
python -c "from mandala_computer import demo_sat; demo_sat()"
python -c "from mandala_computer import demo_tsp; demo_tsp()"
python -c "from mandala_computer import demo_graph_coloring; demo_graph_coloring()"

# quantum_mandala.py demos
python -c "from quantum_mandala import demo_quantum_factorization; demo_quantum_factorization()"
python -c "from quantum_mandala import demo_grover_search; demo_grover_search()"

# mandala_simulator.py tests
python -c "from mandala_simulator import test_p_equals_np; test_p_equals_np()"
python -c "from mandala_simulator import test_unified_field; test_unified_field()"
```

Or run modules directly: `python mandala_computer.py`

## Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview, architecture, applications |
| `PROJECTS.md` | Connected ecosystem repositories |
| `Math.md` | Rigorous factorization analysis, eigenvalue proofs |
| `P=np-hypothesis.md` | Geometric approach to P vs NP |
| `Quantum_integration.md` | Quantum mandala extension details |
| `Hardware.md` | Octahedral silicon substrate control spec |
| `Physical-computer.md` | Physical substrate simulation |
| `Bridge-substrate.md` | Geometric-to-octahedral adapter |
| `Consumer-hardware.md` | Optimization for regular computers |
| `Integration.md` | Integration package status |
| `Mandala-octahedral.md` | Mandala-to-physical-substrate mapping |
| `Mandala_integration.md` | Bridge-to-substrate adapter details |
| `Questions.md` | Limitations and open research questions |
| `Checklist.md` | Integration verification checklist |

## Related Ecosystem

This project connects to a larger set of repositories by JinnZ2, including BioGrid2.0, Geometric-to-Binary-Computational-Bridge, Rosetta-Shape-Core, Polyhedral-Intelligence, and others listed in `PROJECTS.md` and `.fieldlink.json`.

## Notes for AI Assistants

- All code is at the root level — no package hierarchy
- There are **two different classes both named `MandalaComputer`** in separate files (`mandala_computer.py` and `mandala_simulator.py`) — be careful with imports
- No automated tests exist; demo functions are the closest equivalent
- No `.gitignore` exists — be careful not to commit generated files or caches
- The project is research-quality code, not production software
- When adding dependencies, note there is no `requirements.txt` to update (consider creating one if adding new deps)
- Golden ratio constant `PHI = (1 + sqrt(5)) / 2` is central to the mathematical framework
