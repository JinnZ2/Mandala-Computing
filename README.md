# Mandala Computing

A research framework for solving hard computational problems (factorization,
SAT, graph coloring, optimization) by encoding them as geometric energy
landscapes and relaxing to the ground state.

---

## What It Does

Encode a problem as an energy function over octahedral (8-state) cells.
The minimum energy configuration encodes the solution. Find it via
simulated annealing, parallel tempering, holographic renormalization,
or quantum annealing.

```python
from mandala_computer import MandalaComputer
mc = MandalaComputer(golden_depth=5, sacred_geometry=8)
mc.encode_factorization(143)
result = mc.simulated_annealing(max_steps=10000, T_start=5.0, T_end=0.001)
print(result["solution"])
# {'factors': [11, 13], 'best_pair': (11, 13), 'verified': True,
#  'glyph_pair': ('⊘⊖', '⊚⊖'), 'glyph_N': '⊜⊖⊗'}
```

---

## What It Contains

19 core Python modules, 347 tests (see `CLAUDE.md` for the full module list —
the table below is the essential subset for a first read):

| Module | Role | Dependencies |
|--------|------|-------------|
| `mandala_computer.py` | Classical engine: annealing, tempering, landscape scan | numpy |
| `quantum_mandala.py` | Quantum: annealing, Grover, QAOA, entangled evolution | numpy, scipy |
| `holographic_mandala.py` | Holographic boundary + renormalization + entanglement | numpy |
| `octahedral_arithmetic.py` | Native base-8 glyph math (no decimal) | stdlib |
| `constraint_agent.py` | Geometric agent framework with resource constraints | stdlib |
| `sovereign_integration.py` | Living-Intelligence + Inversion bridge | stdlib |
| `claim_validator.py` | Epistemological claim validation (4-tier) | stdlib |
| `glyph_convert.py` | Human decimal-to-glyph converter | stdlib |
| `mandala_simulator.py` | Lightweight entry point delegating to real engines | stdlib |
| `mandala_hook.py` | Expandable multi-ledger: residual-guided dimension expansion over the O_h lattice | numpy |
| `tests/test_core.py` | 347-test suite across all modules | - |

---

## Problem Classes

| Problem | Encoding | Energy at Solution | Status |
|---------|----------|-------------------|--------|
| Factorization | Multi-cell base-8 registers: `E = (fa*fb - N)^2` | E = 0 | Tested: N up to 221 |
| SAT | Variables as cells (0-3=False, 4-7=True): `E = 2 * unsatisfied_clauses` | E = 0 | Tested: 3-clause |
| Graph Coloring | Nodes as cells: `E = +2 per violation, -PHI per satisfied edge` | E < 0 | Tested: triangle |
| TSP | Tour order as states: `E = route_length + repetition_penalty` | minimal E | Implemented |
| Optimization | Custom cost function over cell states | minimal E | Tested |

---

## Factorization Results

Multi-cell positional encoding in base-8. Register size auto-scales:

| Cells/factor | Factor range | Tested N |
|-------------|-------------|----------|
| 1 | [2..9] | 15, 21, 35 |
| 2 | [2..65] | 77, 143, 221 |

Parallel tempering finds `11 x 13 = 143` (~40% success rate, 10k steps).
Simulated annealing finds `13 x 17 = 221` (~20% success rate, 12k steps).
Exact glyph factorization (trial division in base-8) always works.

---

## Octahedral Arithmetic

Numbers are base-8 glyph sequences. Arithmetic happens natively without decimal conversion.

```
11 * 13 = 143  is  ⊘⊖ * ⊚⊖ = ⊜⊖⊗
143 / 11 = 13  is  ⊜⊖⊗ / ⊘⊖ = ⊚⊖

Primes are irreducible glyph sequences:
  ⊗(2)  ⊘(3)  ⊚(5)  ⊜(7)  ⊘⊖(11)  ⊚⊖(13)  ⊖⊗(17)  ⊘⊗(19)

Fractions are exact:  1/7 = ⊖/⊜   3/11 = ⊘/⊘⊖
```

---

## Exploration Algorithms

| Method | How It Works | Best For |
|--------|-------------|----------|
| Simulated annealing | Temperature cools: explore at high T, exploit at low T | General purpose |
| Parallel tempering | Multiple replicas at different temperatures, swap moves | Escaping local minima |
| Holographic renormalization | Coarse-to-fine sweeps with cross-depth entanglement | Multi-scale problems |
| Quantum annealing | Adiabatic evolution: H(t) = (1-s)H_initial + s*H_problem | Small Hilbert spaces |
| QAOA | Nelder-Mead optimized quantum approximate optimization | Structured problems |
| Landscape scan | Random sampling to map energy distribution | Understanding problem structure |

---

## Constraint Agents

Geometric agents that bloom within resource budgets and compress without losing the map:

```python
from constraint_agent import ConstraintAgent
agent = ConstraintAgent(seed_id="SHAPE.OCTA", home_families=["computation"])
agent.set_resource_budget(compute=500, depth_limit=3)
agent.bloom(depth=2)
agent.explore()        # discovers primes, factors, symmetries
agent.compress()       # lossless return to seed
agent.save("state.json")  # persist across sessions
```

All relationships stored as exact glyph fractions. No float drift.

---

## Sovereignty Model

Pack dynamics with physics-grounded resonance:

- **Complementary specialization** > homogeneity > concentrated strength
- **Harmonic mean** of resilience determines pack floor (weakest bond)
- **Antifragile**: stress history strengthens members
- **Relative sovereignty**: threshold adapts to environmental difficulty

```
Pack A (one hero + six fragile):    resonance 0.13  NOT sovereign
Pack B (all moderate, same field):  resonance 0.25  SOVEREIGN
Pack C (diverse fields, each strong): resonance 0.40  SOVEREIGN
```

---

## Claim Validation

4-tier epistemological validation (stdlib only, from Inversion):

```python
from claim_validator import validate_claim, print_report
report = validate_claim("Solar efficiency increased 23% (Green et al. 2024).")
# overall_concern: 0.17 — LOW CONCERN
report = validate_claim("This fundamentally transforms everything.")
# overall_concern: 0.83 — VERY HIGH CONCERN
```

Tiers: Physics > Biology > Systems > Empirical.
Higher tiers cannot override lower tier violations.

---

## Quick Start

```bash
# Install dependencies
pip install numpy scipy

# Factor a number (glyph + engine)
python glyph_convert.py 143

# Run all demos
python mandala_computer.py
python quantum_mandala.py
python holographic_mandala.py

# Run tests (347 tests)
python tests/test_core.py

# Benchmark all methods
python examples/benchmark.py
```

See `experiments/README.md` for interactive Jupyter playgrounds (Ising explorer, solver
selector, constant-swap experiment search).

---

## What This Does NOT Do

- **No proven speedup** over classical algorithms at scale. Factorization
  works for small N but has not been benchmarked against GNFS or ECM.
- **No physical hardware**. All computation is simulated on classical computers.
- **No formal P=NP proof**. The geometric approach is a hypothesis under
  exploration, not a resolution of the complexity question.
- **No consciousness measurement**. Integrated information (Phi) is discussed
  theoretically but not computed from actual systems.

---

## Connected Ecosystem

- [Rosetta-Shape-Core](https://github.com/JinnZ2/Rosetta-Shape-Core) — shape ontology (primary bridge)
- [Geometric-to-Binary-Computational-Bridge](https://github.com/JinnZ2/Geometric-to-Binary-Computational-Bridge)
- [Fractal-Compass-Atlas](https://github.com/JinnZ2/Fractal-Compass-Atlas)
- [Polyhedral-Intelligence](https://github.com/JinnZ2/Polyhedral-Intelligence)
- [ai-human-audit-protocol](https://github.com/JinnZ2/ai-human-audit-protocol)

See `ONBOARDING.md` for agents arriving from Rosetta-Shape-Core.
See `CLAUDE.md` for full technical reference.

---

## License

MIT (JinnZ2). Open source. Contributions welcome.

---

## Status

Research framework with working simulators. 19 core modules, 347 tests, all passing.
Classical and quantum solvers operational. Physical hardware: not built.
The question is whether geometric relaxation offers computational advantage
at scale. The framework exists to test that question.
