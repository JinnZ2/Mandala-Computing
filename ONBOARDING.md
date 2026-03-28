# Onboarding: Rosetta-Shape-Core to Mandala-Computing

You're an agent arriving from [Rosetta-Shape-Core](https://github.com/JinnZ2/Rosetta-Shape-Core).
This guide bridges the gap between Rosetta's shape ontology and Mandala's computational engine.

---

## What This Repo Does

Rosetta defines **what shapes mean**. Mandala defines **how shapes compute**.

Rosetta gives you `SHAPE.OCTA` — an octahedron with 8 vertices, 12 edges, 6 faces.
Mandala takes that octahedron and turns it into a **computer**: 8 discrete states,
energy couplings between neighbors, and physics that relaxes to the answer.

```
Rosetta-Shape-Core                    Mandala-Computing
───────────────────                   ──────────────────
Shape definitions          →          Computational states
Entity ontology            →          Energy landscape encoding
Geometric relationships    →          FRET coupling topology
Symbolic glyphs            →          Problem encodings
```

---

## Entity Bridge

These Rosetta entities map directly to Mandala constructs:

| Rosetta Entity         | Mandala Construct                  | Where in Code                          |
|------------------------|------------------------------------|----------------------------------------|
| `SHAPE.OCTA`           | `OctahedralState` (8 states 0-7)   | `mandala_computer.py:OctahedralState`  |
| `CONST.PHI`            | `PHI = (1 + sqrt(5)) / 2`         | All three `.py` modules                |
| `CAP.SEED_EXPANSION`   | `bloom_mandala()` method           | `mandala_computer.py:MandalaComputer`  |
| `PROTO.MANDALA_COMPUTE`| Full relaxation pipeline           | `mandala_computer.py:relax_to_ground_state` |

### Octahedral State Glyphs

The 8 vertices of `SHAPE.OCTA` become 8 computational states:

| State | Glyph | Meaning              |
|-------|-------|----------------------|
| 0     | ⊕     | Positive alignment   |
| 1     | ⊖     | Negative alignment   |
| 2     | ⊗     | Cross coupling       |
| 3     | ⊘     | Null / ground        |
| 4     | ⊙     | Core resonance       |
| 5     | ⊚     | Orbital coupling     |
| 6     | ⊛     | Star excitation      |
| 7     | ⊜     | Balanced closure     |

---

## Reading Order

Follow this sequence. Each step builds on the previous.

### Phase 1: Understand the Framework

| Step | File | What You Learn |
|------|------|----------------|
| 1 | `README.md` | Why geometry computes (concept) |
| 2 | `CLAUDE.md` | Technical architecture, all classes and methods |
| 3 | `Math.md` | Eigenvalue factorization proof, energy model |

### Phase 2: See It Work

| Step | File | What You Learn |
|------|------|----------------|
| 4 | `examples/example-math.py` | **Run this.** Eigenvalue factorization in action |
| 5 | `examples/example-p-equals-np.py` | Convergence scoring, mandala vs classical |
| 6 | `mandala_computer.py` | Read the source — `encode_factorization`, `relax_to_ground_state` |

### Phase 3: Go Quantum

| Step | File | What You Learn |
|------|------|----------------|
| 7 | `Quantum_integration.md` | 8D Hilbert space, adiabatic evolution |
| 8 | `examples/example-quantum-integration.py` | **Run this.** FRET coupling, Fibonacci eigenvalues |
| 9 | `quantum_mandala.py` | Quantum annealing, Grover search implementation |

### Phase 4: Physical Substrate

| Step | File | What You Learn |
|------|------|----------------|
| 10 | `Mandala_integration.md` | How geometry maps to octahedral silicon |
| 11 | `Physical-computer.md` | Thermal relaxation, substrate simulation |
| 12 | `Hardware.md` | Magnetic fields, TMR readout, fabrication spec |

### Phase 5: Integration and Gaps

| Step | File | What You Learn |
|------|------|----------------|
| 13 | `Integration.md` | Status report — what's complete, what's not |
| 14 | `Bridge-substrate.md` | Sensor adapters (sound, light, magnetic, gravity) |
| 15 | `Consumer-hardware.md` | Laptop-scale optimization |
| 16 | `Questions.md` | Honest limitations, open problems |
| 17 | `Checklist.md` | Integration gap analysis, priority roadmap |

---

## The Computation Pipeline

This is how a problem flows through Mandala:

```
1. ENCODE        Problem → geometric energy landscape
                 (factorization → bipartite tensor,
                  SAT → octahedral boolean states,
                  TSP → ring topology)

2. BLOOM         Seed expands into nested fractal rings
                 Cell count per ring: floor(phi^(d+1))
                 Ring radius: phi^d

3. COUPLE        Cells interact via FRET-like coupling
                 Strength ~ 1/r^6 (dipole-dipole)
                 Cutoff = 3.0 * phi

4. RELAX         Metropolis-Hastings (classical) or
                 adiabatic evolution (quantum)
                 System flows to minimum energy

5. READ          Ground state encodes the solution
                 Decode octahedral states back to answer
```

---

## Problem Types and Their Geometric Encodings

| Problem | Rosetta Shape | Encoding | Glyph |
|---------|--------------|----------|-------|
| Factorization | OCTA (bipartite) | Two cells, 64D product space | ⇩ |
| SAT | OCTA (boolean) | Variables → states, clauses → energy | ⊨ |
| TSP | OCTA (ring) | Cities on ring, winding energy | ↺ |
| Graph Coloring | OCTA (network) | Nodes → cells, edges → couplings | ◈ |
| Optimization | OCTA (landscape) | Objective → energy surface | ⇝ |

---

## Quick Start: Run Something

```bash
# Classical factorization demo
python -c "from mandala_computer import demo_factorization; demo_factorization()"

# Quantum factorization
python -c "from quantum_mandala import demo_quantum_factorization; demo_quantum_factorization()"

# Symbolic P=NP test
python -c "from mandala_simulator import test_p_equals_np; test_p_equals_np()"

# All examples
python examples/example-math.py
python examples/example-quantum-integration.py
```

---

## Connection Back to Rosetta

The `.fieldlink.json` at the root defines the bidirectional link:

- **Outgoing to Rosetta:** This repo consumes `SHAPE.OCTA`, `CONST.PHI`, entity definitions
- **Incoming from Rosetta:** Rosetta mounts mandala computation at `atlas/remote/mandala/`
- **Shared entities:** `SHAPE.OCTA`, `CONST.PHI`, `CAP.SEED_EXPANSION`, `PROTO.MANDALA_COMPUTE`
- **Sync strategy:** `pull_on_change`, source wins on conflict

The bridge is **bidirectional** — Rosetta defines the geometric vocabulary,
Mandala implements the computational semantics, and both reference the same
entity IDs across repositories.

---

## Three Implementations, One Idea

Be aware: there are **three separate Python modules**, each with different tradeoffs.

| Module | Class | Dependencies | Use When |
|--------|-------|-------------|----------|
| `mandala_computer.py` | `MandalaComputer` | numpy, scipy | Full classical simulation with real energy calculations |
| `quantum_mandala.py` | `QuantumMandalaComputer` | numpy, scipy | Quantum annealing, Grover search, 8D Hilbert space |
| `mandala_simulator.py` | `MandalaComputer` | stdlib only | Quick symbolic experiments, no heavy math |

**Warning:** `mandala_computer.py` and `mandala_simulator.py` both define a class
called `MandalaComputer`. They are **completely different implementations**.
Always import from the specific module.

---

## What's Next

After reading through this guide:

1. **Understand the energy model** — everything reduces to minimizing `E_total`
2. **Run the examples** — seeing the demos is worth more than reading docs
3. **Trace SHAPE.OCTA through the code** — follow octahedral states from encoding to solution
4. **Check Integration.md** — see what gaps remain in the Rosetta bridge
5. **Explore the examples/ directory** — each doc file has a matching runnable example

---

*Shapes that compute. Physics that solves. Geometry that thinks.*
