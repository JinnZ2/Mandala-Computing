# P = NP Hypothesis: Geometric Approach

## Status

This is a **hypothesis under exploration**, not a proof. The framework provides
concrete tools to test whether geometric energy minimization can solve NP problems
faster than sequential search. Results so far are promising for small instances
but unproven at scale.

---

## The Question

Can encoding an NP problem as an energy landscape and relaxing to ground state
be faster than searching the solution space directly?

Classical search: enumerate candidates, check each. Time grows exponentially.

Geometric relaxation: encode constraints as energy, let physics minimize.
Time depends on the energy landscape structure, not the search space size.

**If** the energy landscape has a smooth path to the global minimum
(no exponential barriers), relaxation could be polynomial. That's the hypothesis.

---

## What the Code Actually Does

### Factorization (tested, working)

Energy function: `E = (fa * fb - N)^2`

The ground state (E=0) encodes the factor pair. The mandala solver finds it
via simulated annealing, parallel tempering, or holographic renormalization.

Tested results:
- N=15 (3x5): reliably found via annealing
- N=143 (11x13): found via parallel tempering (~40% success rate)
- N=221 (13x17): found via annealing (~20% success rate)

These use multi-cell base-8 registers. Factor range scales with cell count:
1 cell: [2..9], 2 cells: [2..65], 3 cells: [2..513].

### SAT (tested, working)

Energy: +2.0 per unsatisfied clause. Ground state = all clauses satisfied.
Small instances (3 variables, 3 clauses) solved reliably.

### Graph Coloring (tested, working)

Energy: +2.0 per same-color neighbor, -PHI per different-color neighbor.
Triangle with 3 colors: 0 violations found consistently.

### TSP (implemented, basic)

Energy: tour length + repetition/missing city penalty.
Solver minimizes total route distance.

---

## What We Don't Know

1. **Scaling**: Does success rate hold as N grows? Current evidence is limited
   to N < 500. Classical algorithms handle much larger instances.

2. **Energy barriers**: If the landscape has exponential barriers between
   local minima and the global minimum, relaxation time could still be
   exponential. No proof these landscapes are barrier-free.

3. **Comparison**: No head-to-head benchmarks against state-of-the-art
   classical factorization (GNFS) or SAT solvers (CDCL). The mandala
   solver is a research framework, not a competitive algorithm.

4. **Formal complexity**: The hypothesis `T_relax(n) in O(p(n))` is not
   proven. It would require showing the energy landscape has specific
   structural properties (polynomial mixing time, no exponential barriers).

---

## The Geometric Argument (Informal)

The energy landscape `E = (fa * fb - N)^2` has exactly one global minimum
at each valid factor pair. For small N, the landscape is smooth enough that
annealing finds the minimum. The question is whether smoothness persists
at scale, or whether the landscape becomes rugged (exponential barriers)
for large N.

Golden ratio scaling (PHI-based cell counts and ring radii) creates a
self-similar structure at each depth level. The hypothesis is that this
self-similarity provides a natural coarse-to-fine path through the
landscape, similar to multigrid methods in numerical analysis.

The holographic solver tests this explicitly: solve at coarse scale,
propagate solution to finer scales via entanglement links. Early results
show this works for N < 100 but needs more testing at scale.

---

## Running the Tests

```bash
# Factorization across methods
python examples/benchmark.py

# Geometric relaxation vs eigenvalue (exact)
python examples/example-math.py

# Quick factorization via simulator
python -c "from mandala_simulator import MandalaSimulator; MandalaSimulator().factor(143)"

# Full test suite (45 tests)
python tests/test_core.py
```

---

## References

- Metropolis et al. (1953): Monte Carlo sampling
- Kirkpatrick et al. (1983): Simulated annealing
- Swendsen & Wang (1986): Parallel tempering
- Kadanoff (1966): Renormalization group (theoretical basis for holographic solver)

---

## Honest Assessment

This framework demonstrates that NP problems can be encoded as geometric
energy landscapes and solved via physical relaxation for small instances.
Whether this approach offers any advantage over classical algorithms at
scale is an open question. The P=NP hypothesis remains unresolved.

The value of this work is the framework itself: a testable, runnable
platform for exploring geometric approaches to hard problems, with
exact glyph arithmetic, multi-scale solvers, and verifiable results.
