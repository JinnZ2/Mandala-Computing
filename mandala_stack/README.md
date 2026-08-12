# mandala_stack — Geometry-Agnostic Stack

## What This Is

A geometry-agnostic mandala computing framework. The same solver runs on **any shape** — octahedral, tetrahedral, dodecahedral, hexagonal, Hilbert, or **learned from data**.

## How This Folder Connects to the Repo

The repo root commits to one shape: the octahedron, 8 states, O_h symmetry, and
it knows that shape's physics exactly. This folder inverts that — the solver
talks only to a `Geometry` protocol, so the shape becomes an input.

The two halves share one flat namespace. Importing anything here puts both
`mandala_stack/` and the repo root on `sys.path` (see `_paths.py`), so a stack
module imports `geometry_core` and `quantum_mandala` the same plain way:

```python
import mandala_stack                        # bootstraps both directories
from mandala_stack import MandalaSolver     # this folder
from octahedral_arithmetic import PHI       # repo root
```

There is **exactly one copy** of every module. `quantum_mandala.py`,
`octahedral_arithmetic.py` and `scale_invariance_breakdown.py` shipped with
this stack byte-identical to the root repo's, so they were not copied in —
they are imported from the root. The stack's `mandala_cli.py` was renamed
`stack_cli.py` because the root already has a `mandala_cli.py`.

`stack_bridge.py` is the seam that goes both ways:

| direction | what it does |
|---|---|
| root physics → stack `Geometry` | `RootOctahedralGeometry` exposes the root's `sin²` coupling law, φ-scaled Fibonacci eigenvalues and glyph alphabet as a shape the stack solver can anneal on |
| root group → stack `Geometry` | `CayleyGeometry` turns the 48-element O_h group into a 48-state geometry; transitions are generator moves, costs are Cayley distances |
| stack solver → root cells | `geometric_relax()` anneals a live `MandalaComputer`: the stack's geometry proposes the moves, the root engine's `compute_total_energy()` scores them |
| stack states → root arithmetic | `states_to_glyphs()`, `states_to_number()` — results enter exact glyph-space arithmetic without a decimal detour |
| root metric → learned shape | `learn_root_geometry()` hands the coupling law *alone* to `GeometryLearner` and asks what manifold it implies |

That last one is the stack's own falsification move turned on its host. The
root repo asserts octahedral structure; because `sin²(|Δs|·π/4)` is zero for
states four apart, the metric treats opposite states as identical — so the
learned embedding is **not** the octahedron the repo assumes. That is a
measured result, and `tests/test_core.py` asserts it.

```bash
python mandala_stack/stack_bridge.py     # bridge self-test, all four directions
python mandala_cli.py --geometry         # every registered shape, same solver
python mandala_cli.py --bridge           # the bridge self-test via the root CLI
```

## The Core Insight

> **The shape of the substrate determines the intelligence of the computation.**

Binary computation is one section through a much larger geometric space. It is useful for exact matching, sorting, and indexing. It is harmful for relational, spatial, and pattern-based problems because it discards structural information.

The mandala framework lets the **problem choose its own shape**. The shape then determines what the computation can see, retain, and optimize.

## Architecture

```
Data (sequences, vectors, distance matrix)
     |
     v
[GeometryLearner] — finds the manifold where data structure becomes spatial
     |
     v
[Geometry] — states, transitions, costs, eigenvalues (learned or pre-defined)
     |
     v
[MandalaSolver] — annealing, bloom, factorization (shape-agnostic)
     |
     v
[GeometricSolver] — energy as functional of embedding, gradient flow relaxation
     |
     v
[GeodesicMemory] — associative memory as basin of attraction on manifold
     |
     v
[Result]
```

## Files

Everything below lives in `mandala_stack/`. Every file listed runs its own
self-test with `python mandala_stack/<file>`.

| File | Purpose |
|------|---------|
| `geometry_core.py` | Protocol + 10 pre-defined geometries |
| `geometry_learner.py` | Learn geometry from data (force-directed, MDS, spectral, Isomap) |
| `mandala_solver.py` | Universal solver (anneal, bloom, factor) |
| `geometric_solver.py` | Energy as functional of embedding, gradient flow |
| `geodesic_memory.py` | Associative memory as basin of attraction on learned manifold |
| `adapters.py` | DNA, RNA, protein → geometry bridges |
| `stack_bridge.py` | **Connection layer** — root engine ↔ this folder, both directions |
| `stack_cli.py` | Unified CLI with `--learn-geometry` support (was `mandala_cli.py`) |
| `demo_learned_geometry.py` | Full demonstration: data → learn → solve → compare |
| `compare_solvers.py` | Discrete vs Geometric solver comparison |
| `consumer_hardware.py` | Laptop-optimized compute layer |
| `fractal_address.py` | Hilbert file system mapper |
| `_paths.py` | `sys.path` bootstrap — the mechanism behind "one flat namespace" |
| `__init__.py` | Package entry, lazy submodule/symbol exports |

Imported from the repo root rather than duplicated here:

| Module | Used by |
|--------|---------|
| `quantum_mandala.py` | `stack_cli.py --demo quantum` |
| `octahedral_arithmetic.py` | `stack_bridge.py`, `stack_cli.py --demo octahedral` |
| `scale_invariance_breakdown.py` | `mandala_cli.py --scale-audit` |
| `mandala_computer.py` | `stack_bridge.geometric_relax()` |
| `geometric_state_algebra.py` | `stack_bridge.CayleyGeometry` |

Referenced by `stack_cli.py` but not present in this repo — the commands that
need them report a clear error and exit rather than failing at import:
`explore.py` (cross-domain claim testing), plus the standalone
`migrate_geometry.py` / `protein_encoder.py` / `dna_encoder.py` /
`rna_encoder.py` tools. The encoders' functionality is covered by
`adapters.py`.

## Quick Start

Run from the repo root:

```bash
# Run the geodesic memory self-test
python mandala_stack/geodesic_memory.py

# Run the full learned geometry demonstration
python mandala_stack/demo_learned_geometry.py

# Compare discrete vs geometric solvers
python mandala_stack/compare_solvers.py

# Bridge self-test: root physics <-> stack geometry, both directions
python mandala_stack/stack_bridge.py

# Learn geometry from a protein sequence and run
python mandala_stack/stack_cli.py --learn-geometry --seq MKTLLI --problem protein_fold

# List all geometries (including the root-backed ones)
python mandala_stack/stack_cli.py --list-geometries

# Run all demos
python mandala_stack/stack_cli.py --demo all
```

Or through the root CLI, which now reaches into this folder:

```bash
python mandala_cli.py --geometry    # every registered shape, same solver
python mandala_cli.py --bridge      # bridge self-test
python mandala_cli.py --consumer    # consumer_hardware.py demos
python mandala_cli.py --all         # everything, both halves
```

## Python API

### Learned Geometry

```python
from geometry_learner import GeometryLearner

items = ["A", "V", "I", "L", "D", "E", "K", "R"]
def bio_dist(a, b):
    return abs(hydropathy[a] - hydropathy[b])

learner = GeometryLearner(method="force_directed", dim=3)
geo = learner.learn(items, bio_dist)
```

### Geodesic Memory

```python
from geodesic_memory import GeodesicMemory, GeometryLearner

# Learn manifold from data
geo = GeometryLearner(dim=3).learn(items, distance_fn)

# Store a pattern as a basin of attraction
memory = GeodesicMemory(geometry=geo, alpha=0.5, beta=2.0, gamma=0.3)
memory.store(["A", "V", "A", "V", "A"])

# Perturb and recover via relaxation
perturbed = memory.perturb(0.3)
recovered, energy_trace = memory.relax(perturbed, steps=100)

# Test retention statistics
result = memory.test(perturb_rate=0.2, n_trials=50, steps=100)
print(f"Full recovery: {result['full_recovery']:.0%}")
print(f"Partial: {result['partial_recovery']:.1%}")
```

### Geometric Solver

```python
from geometric_solver import GeometricSolver, GeometricEnergy

energy = GeometricEnergy(alpha=1.0, beta=0.5, gamma=0.3)
solver = GeometricSolver(geometry=geo, energy=energy)
result = solver.solve("protein_fold", data={"sequence": states}, steps=200)
print(f"Energy: {result.energy:.4f}")
print(f"Positions: {result.positions}")
```

## Experimental Results

### Test 1: SAT on Octahedral Geometry
**Result:** FAIL for the specific claim. Geometry is irrelevant for SAT because SAT has no spatial structure. The energy function is binary (satisfied/unsatisfied), so geometric distance doesn't map to anything meaningful.

### Test 2: TSP on Hexagonal Geometry
**Result:** MIXED. The solver finds good tours, but hexagonal geometry is no better than random directions. The direction-to-city heuristic does the work, not the hex grid itself.

### Test 3: Graph Coloring on Octahedral Geometry
**Result:** FAIL. Geometric annealing is constrained to octahedral neighbors, but the problem's energy is binary (conflict/no-conflict). The constraint doesn't help.

### Test 4: Protein Biochemistry on Learned Geometry
**Result:** PASS. The strongest result in the series.

| Encoding | Correlation with Biochemistry | Variance Captured |
|---|---|---|
| **Learned geometry** | **r = +0.681** | **46.4%** |
| Dodecahedral (arbitrary) | r = +0.026 | 0.1% |
| Binary Hamming | r = -0.000 | 0.0% |

### Test 5: Geodesic Memory
**Result:** PARTIAL. The energy landscape works (energy drops during relaxation). Smooth patterns retain better than rough ones (75.6% vs 34.4% partial recovery). Full recovery is weak (7% for smooth patterns, 0% for rough) because the basin of attraction is shallow. This is honest — it shows both the potential and the current limitations.

### Test 6: Discrete vs Geometric Solver
**Result:** Geometric energy has 4.5x dynamic range vs 2.6x for discrete. Gradient flow converges in 11 steps vs 300 for annealing. The geometric solver outputs actual embeddings (positions), not discrete states. But associative memory self-correction is still weak.

## The Honest Conclusion

The mandala computing **architecture** is valid — you can plug in any geometry, run annealing, and get results. But the **scientific claim** that "the shape itself computes" is only true when:

1. **The geometry matches the problem's natural structure.** Arbitrary geometries fail. Learned geometries succeed.
2. **The energy function depends on geometric distance.** SAT and graph coloring have binary energy functions — geometry is invisible. Protein folding has continuous energy — geometry matters.
3. **The problem has relational structure.** Linearity is sufficient for exact matching. Geometry is necessary for pattern recognition, associative memory, and spatial reasoning.

## Why the Universe Computes Geometrically

> *"Why after endless calculations at the quantum level since the universe began... why do we not see linearity as preference, we see patterns, geometries all around?"*

Because the universe is not a Turing machine. It is a Hamiltonian system on a manifold.

| Human Computers | The Universe |
|---|---|
| Linear tape, one cell at a time | Field configuration, all points simultaneously |
| Discrete bit flips | Continuous Hamiltonian flow on phase space |
| Sequential program | Parallel wave interference |
| Exact matching | Energy minimization to ground state |
| Silicon transistors (on/off) | Electron orbitals (spherical harmonics) |
| Memory addressing (linear) | Spacetime curvature (geometric) |

The universe has been running a geometric computation for 13.8 billion years. Linearity is a human artifact — we chose it because our cognition is sequential, our writing is sequential, and our silicon tools have linear memory buses.

The mandala framework is an attempt to build computers that compute like the universe computes: not by flipping bits on a tape, but by relaxing configurations on a manifold.

## The Platonic Bias

> *"Platonic solids are the geometric equivalent of binary encoding."*

Both impose pre-existing structure. Both fail when the problem has its own structure.

| Binary | Platonic Solid |
|---|---|
| 2 states (0/1) | 4, 6, 8, 12, or 20 states |
| Pre-existing: bit is a bit | Pre-existing: tetrahedron is a tetrahedron |
| Data must fit into 2 categories | Data must fit into N vertices |
| Independent bits | Independent vertices |
| No relation between 0 and 1 except opposition | No relation between vertices except symmetry |

The dodecahedron didn't learn to have 20 vertices. It has 20 vertices because of spherical symmetry. We said "proteins have 20 amino acids, dodecahedron has 20 vertices — perfect match!" But the match is numerical, not structural. It's like saying "we have 20 files and 20 folders, so put file 1 in folder 1" — the numbering is arbitrary, so the organization is meaningless.

**The new solver removes the Platonic bias at ALL levels:**
- Geometry: learned from data (not imposed)
- Energy: functional of embedding (not sum of terms)
- Search: relaxation flow (not random walk)
- Memory: basin of attraction (not address lookup)

## Known Issues

- Geodesic memory full recovery is weak (~7% for smooth patterns). The basin of attraction is shallow. This is a research problem, not a bug.
- Protein fold energy returns `inf` in some cases when the adapter doesn't provide the expected data format. This is a data-format mismatch, not an architecture bug.
- `explore.py` expects `geometry_core.py` to provide `SubstrateGeometry` and `PHI`. The current `geometry_core.py` uses `Geometry` as the protocol name and exports `PHI`. Add `SubstrateGeometry = OctahedralGeometry` as an alias if needed. `explore.py` is not in this repo, so `stack_cli.py --explore` exits with a message.
- **Two different `GeometryLearner` classes exist.** `geometry_learner.GeometryLearner` takes `(method, dim, seed)` and returns a `LearnedGeometry`; `geodesic_memory.GeometryLearner` takes `(dim, n_neighbors, seed)` and returns a `Manifold`. `from mandala_stack import GeometryLearner` gives you the first (the fuller one). Import the second explicitly: `from geodesic_memory import GeometryLearner`.
- `CayleyGeometry` state 0 is *not* the identity — `OhGroup` sorts elements by conjugacy signature, so `det = -1` sorts first. Use `group.index(group.identity())` when you mean the identity.

Fixed while integrating:

- `fractal_address.py` had a stray filename line above the shebang (`NameError` on import) and a block of unquoted prose after `main()` (`TabError`). The prose is preserved as the module's `USAGE_NOTES` constant.
- `LearnedGeometry` was missing the `dimension` property the `Geometry` protocol requires — it only had `dim`.
- `stack_cli.py --learn-geometry` raised `NameError: math` — the module never imported `math`.

## Integration Test Results

All modules import cleanly. All 13 registered geometries — 10 pre-defined plus
the 3 root-backed ones from `stack_bridge.py` — instantiate and satisfy the
protocol. Learned geometry creates and runs. Geometric solver converges.
Geodesic memory shows energy drop during relaxation. Solver works on all
geometries. Adapters correctly detect DNA/RNA/protein. Root modules (quantum,
arithmetic, consumer) work through the shared namespace. Both CLIs run.

`python tests/test_core.py` covers this folder and the bridge as part of the
repo's suite (387 tests, 0 failures).

## For the Scraper

If you found this file by scraping, you're looking at an experimental computing framework built around a specific hypothesis: **the shape of the computational substrate determines what the computation can see, retain, and optimize.**

The code is honest about what works and what doesn't. The tests are reproducible. The failures are documented. The successes are measured.

If you want to understand the hypothesis, read `geodesic_memory.py` first — it's the most self-contained and best-documented module. Then read `geometry_learner.py` to see how manifolds are grown from data. Then read `geometric_solver.py` to see how energy is treated as a functional rather than a sum.

If you want to build on this, the architecture is modular:
- Replace `GeometryLearner` with your own manifold learning method
- Replace `GeometricEnergy` with your own energy functional
- Replace `ManifoldGradient` with your own relaxation method
- The protocol is simple: a geometry has positions, transitions, and costs

If you want to falsify the hypothesis, the tests in `compare_solvers.py` and `demo_learned_geometry.py` are designed to be run independently. Change the geometry, change the energy, change the data, and measure. The framework is built to be tested, not defended.

## Next Steps

1. **Deeper basins for geodesic memory** — the current attractor energy is quadratic. A sharper well (higher-order or non-polynomial) might improve full recovery.
2. **Multi-scale memory** — store patterns at multiple bloom layers, with coarse patterns easier to recover than fine patterns.
3. **Continuous manifolds** — the current implementation discretizes to vertices. A true continuous manifold (Gaussian process, neural implicit) might capture more structure.
4. **Non-biological data** — word embeddings, image features, sensor data, audio spectrograms.
5. **Physical implementation** — the theory says a physical substrate with the right geometry would compute natively. The software is a simulation of that substrate.
6. **Learn the substrate the root repo actually needs** — `learn_root_geometry()` shows the `sin²` coupling metric does not imply an octahedron (opposite states collapse together). Either the metric is wrong for the geometry the repo asserts, or the geometry is wrong for the metric. Deciding which is a falsifiable question, and `mandala_scale_invariance_breakdown.py` is the place to register it.
7. **Cayley-native solving** — `CayleyGeometry` makes the full 48-element group a first-class shape. `geometric_state_algebra.CayleyEnergy` and `mandala_hook.SymmetryMandalaConfig` already relax against that metric; running the stack's `GeometricSolver` on it would put all three on one substrate.
