"""
example-geometric-state-algebra.py
Demonstrates concepts from the Geometric State Algebra:
  - Full octahedral symmetry group O_h (48 elements)
  - Group ring Z[O_h] replacing GF(2)
  - States as symmetry operations, not flat integers
  - Geometric cancellation (composition to identity)
  - Cayley graph distance as coupling metric
  - Prime-to-vertex native mapping
  - Scent trail energy descent on the group manifold
  - Geometric Metropolis-Hastings relaxation

Requires: stdlib only (no numpy/scipy)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
from geometric_state_algebra import (
    OhElement, OhGroup, GroupRingElement, GeometricState,
    CayleyEnergy, PrimeVertex, GeometricNullSpace, ScentTrail,
    GeometricMandalaAdapter, IDENTITY, GENERATOR_RZ90, GENERATOR_RX90,
    GENERATOR_INV, OCTAHEDRAL_VERTICES,
)

PHI = (1 + math.sqrt(5)) / 2


# ---------------------------------------------------------------------------
# 1. Group Structure
# ---------------------------------------------------------------------------

def demo_group():
    """The 48-element octahedral symmetry group."""
    print("=" * 60)
    print("[1] OCTAHEDRAL SYMMETRY GROUP O_h")
    print("=" * 60)

    group = OhGroup()
    print(f"\n  Elements: {len(group.elements)}")
    print(f"  Proper rotations: {len(group.proper_rotations())}")
    print(f"  Improper (reflections): {len(group.improper_elements())}")
    print(f"  Cayley diameter: {group.max_distance()}")
    print(f"  Conjugacy classes: {len(group.conjugacy_classes)}")

    # Element orders
    orders = {}
    for e in group.elements:
        o = e.order()
        orders[o] = orders.get(o, 0) + 1
    print(f"\n  Element orders:")
    for o in sorted(orders):
        print(f"    Order {o}: {orders[o]} elements")

    # Stabilizers
    print(f"\n  Vertex stabilizers (elements fixing a vertex):")
    for v in OCTAHEDRAL_VERTICES[:3]:
        stab = group.stabilizer(v)
        print(f"    {v}: {len(stab)} elements (|O_h|/|orbit| = 48/6 = 8)")

    return group


# ---------------------------------------------------------------------------
# 2. Binary vs Geometric Cancellation
# ---------------------------------------------------------------------------

def demo_cancellation(group):
    """Show how geometric cancellation differs from XOR."""
    print(f"\n{'=' * 60}")
    print("[2] CANCELLATION: XOR vs GROUP COMPOSITION")
    print("=" * 60)

    print(f"\n  Binary (GF(2)):")
    print(f"    state XOR state = 0  (all information lost)")
    print(f"    5 ^ 5 = 0            (which 5? what kind of 5?)")

    print(f"\n  Geometric (Z[O_h]):")
    for classical in [0, 2, 4, 7]:
        gs = GeometricState.from_classical_state(group, classical)
        gs_inv = gs.geometric_inverse()
        composed = gs.compose(gs_inv)

        dominant = gs.ring_element.dominant_element()
        elem = group.elements[dominant]
        ref = (1, 0, 0)
        image = elem.act_on_vertex(ref)

        print(f"    state {classical}: {ref} -> {image} (order {elem.order()}, "
              f"{'rot' if elem.is_proper() else 'ref'})")
        print(f"      * inverse = identity: {composed.ring_element.is_identity()}")
        print(f"      The cancellation KNOWS it undid a specific rotation.")


# ---------------------------------------------------------------------------
# 3. Cayley Distance Matrix
# ---------------------------------------------------------------------------

def demo_cayley_metric(group):
    """Cayley graph distance replaces |s_i - s_j|."""
    print(f"\n{'=' * 60}")
    print("[3] CAYLEY DISTANCE METRIC")
    print("=" * 60)

    print(f"\n  Classical metric: |s_i - s_j|  (flat, no structure)")
    print(f"  Cayley metric: min generators to go from g_i to g_j\n")

    # Build 8x8 distance matrix for classical states
    print(f"  Cayley distances between classical states 0-7:")
    print(f"        ", end="")
    for j in range(8):
        print(f"  s{j}", end="")
    print()

    for i in range(8):
        si = GeometricState.from_classical_state(group, i)
        print(f"    s{i}: ", end="")
        for j in range(8):
            sj = GeometricState.from_classical_state(group, j)
            d = si.cayley_distance_to(sj)
            print(f"  {d:.0f} ", end="")
        print()

    # Compare with flat metric
    print(f"\n  Flat |i-j| metric:")
    print(f"        ", end="")
    for j in range(8):
        print(f"  s{j}", end="")
    print()
    for i in range(8):
        print(f"    s{i}: ", end="")
        for j in range(8):
            print(f"  {abs(i-j)} ", end="")
        print()

    print(f"\n  Key difference: Cayley metric respects the geometry.")
    print(f"  States 0,2 are Cayley-adjacent (1 generator apart)")
    print(f"  but |0-2|=2 in the flat metric. The geometry knows better.")


# ---------------------------------------------------------------------------
# 4. Group Ring Arithmetic
# ---------------------------------------------------------------------------

def demo_group_ring(group):
    """Z[O_h] formal sums — richer than GF(2) vectors."""
    print(f"\n{'=' * 60}")
    print("[4] GROUP RING Z[O_h]")
    print("=" * 60)

    # Create elements
    e = GroupRingElement.from_identity(group)
    g5 = GroupRingElement.from_element(group, 5)
    g10 = GroupRingElement.from_element(group, 10)

    print(f"\n  Identity: {e}")
    print(f"  g5: {g5}")
    print(f"  g10: {g10}")

    # Superposition
    sup = g5 + g10
    print(f"\n  Superposition g5 + g10: support={sup.support_size()}")
    print(f"    Entropy: {sup.geometric_entropy():.3f}")
    print(f"    Cayley spread: {sup.cayley_spread():.2f}")

    # Convolution (non-commutative multiplication)
    prod_ab = g5 * g10
    prod_ba = g10 * g5
    print(f"\n  g5 * g10 = {prod_ab}")
    print(f"  g10 * g5 = {prod_ba}")
    print(f"  Commutative? {prod_ab == prod_ba}")

    # Norm
    big = g5 + g10 + GroupRingElement.from_element(group, 20)
    print(f"\n  ||g5 + g10 + g20||^2 = {big.norm_squared()}")

    # Conjugacy class element (central — commutes with everything)
    for sig in list(group.conjugacy_classes.keys())[:2]:
        cc = GroupRingElement.from_conjugacy_class(group, sig)
        print(f"\n  Conjugacy class {sig}:")
        print(f"    Support: {cc.support_size()} elements")
        print(f"    Entropy: {cc.geometric_entropy():.3f}")


# ---------------------------------------------------------------------------
# 5. Prime Vertices
# ---------------------------------------------------------------------------

def demo_primes(group):
    """Primes inhabit octahedral vertices by order resonance."""
    print(f"\n{'=' * 60}")
    print("[5] PRIME VERTEX MAPPING")
    print("=" * 60)

    pv = PrimeVertex(group)

    print(f"\n  Prime -> group element (by order resonance):")
    for p in [2, 3, 5, 7, 11, 13]:
        idx = pv.prime_to_element(p)
        if idx is not None:
            elem = group.elements[idx]
            print(f"    {p:>3d} -> element {idx:>2d}: order={elem.order()}, "
                  f"{'proper' if elem.is_proper() else 'improper'}")

    print(f"\n  Geometric factorization:")
    for N in [15, 21, 35, 77]:
        result = pv.factor_pair_geometric(N)
        if result:
            a, b = result
            print(f"    {N} = compose({a}, {b})")


# ---------------------------------------------------------------------------
# 6. Scent Trail
# ---------------------------------------------------------------------------

def demo_scent_trail(group):
    """Energy descent on the Cayley graph."""
    print(f"\n{'=' * 60}")
    print("[6] SCENT TRAIL: CAYLEY GRAPH DESCENT")
    print("=" * 60)

    e_idx = group.index(IDENTITY)

    def energy_fn(state):
        d = state.ring_element.dominant_element()
        return float(group.distance(e_idx, d)) if d is not None else 999.0

    # Start from maximally distant element
    start_idx = max(range(48), key=lambda i: group.distance(e_idx, i))
    start = GeometricState.from_pure_rotation(group, start_idx)

    trail = ScentTrail(group, energy_fn)
    result = trail.descend(start, max_steps=20, temperature=0.1)

    print(f"\n  Target: identity element")
    print(f"  Start: element {start_idx} (distance {group.distance(e_idx, start_idx)})")
    print(f"  {trail.trail_summary()}")
    print(f"  Reached identity: {result.ring_element.is_identity()}")

    # Show the path
    if trail.trail:
        print(f"\n  Descent path:")
        for step, (elem_idx, energy) in enumerate(trail.trail):
            elem = group.elements[elem_idx]
            print(f"    step {step}: element {elem_idx:>2d}, energy={energy:.0f}  "
                  f"(order {elem.order()}, {'rot' if elem.is_proper() else 'ref'})")


# ---------------------------------------------------------------------------
# 7. Geometric Relaxation
# ---------------------------------------------------------------------------

def demo_relaxation(group):
    """Metropolis-Hastings on the Cayley graph."""
    print(f"\n{'=' * 60}")
    print("[7] GEOMETRIC RELAXATION (CAYLEY ANNEALING)")
    print("=" * 60)

    import random
    random.seed(42)

    for n_cells in [4, 8]:
        adapter = GeometricMandalaAdapter(group, num_cells=n_cells)

        # Ring topology
        neighbors = [(i, (i+1) % n_cells) for i in range(n_cells)]

        # Random initial states
        for i in range(n_cells):
            adapter.states[i] = GeometricState.from_pure_rotation(
                group, random.randrange(48))

        e_before = adapter.geometric_energy(neighbors)
        classical_before = adapter.get_classical_states()

        history = adapter.geometric_relax(neighbors, steps=300, temperature=2.0)

        e_after = adapter.geometric_energy(neighbors)
        classical_after = adapter.get_classical_states()
        reduction = (e_before - e_after) / max(e_before, 1e-12) * 100

        print(f"\n  {n_cells}-cell ring:")
        print(f"    Before: states={classical_before}, E={e_before:.4f}")
        print(f"    After:  states={classical_after}, E={e_after:.4f}")
        print(f"    Reduction: {reduction:.1f}%")


# ---------------------------------------------------------------------------
# 8. The Key Insight
# ---------------------------------------------------------------------------

def demo_insight():
    """Why this matters for scaling."""
    print(f"\n{'=' * 60}")
    print("[8] WHY Z[O_h] SCALES BEYOND GF(2)")
    print("=" * 60)

    group = OhGroup()

    print(f"""
  GF(2) state space:  2^n states for n bits
  Z[O_h] state space: 48^n states for n cells

  But it's not just more states. The structure is richer:

  GF(2):
    - States are bit strings (no geometry)
    - XOR cancellation: a ^ a = 0 (information destroyed)
    - Null space is a flat vector space
    - Distance is Hamming (count differing bits)

  Z[O_h]:
    - States are symmetry operations (geometry preserved)
    - Cancellation: g * g^-1 = e (knows WHICH rotation cancelled)
    - Null space is a Z[O_h]-module (richer structure)
    - Distance is Cayley (counts generator steps on the group)

  Concrete numbers for this group:
    Cayley diameter: {group.max_distance()}
    Conjugacy classes: {len(group.conjugacy_classes)}
    Max element order: {max(e.order() for e in group.elements)}

  The scent trails follow energy gradients on a 48-element
  Cayley graph instead of searching a flat binary space.
  Each step is a geometric rotation, not a bit flip.
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("GEOMETRIC STATE ALGEBRA — Example Script")
    print("  States are symmetries. The group ring is the algebra.")
    print("=" * 60)

    group = demo_group()
    demo_cancellation(group)
    demo_cayley_metric(group)
    demo_group_ring(group)
    demo_primes(group)
    demo_scent_trail(group)
    demo_relaxation(group)
    demo_insight()

    print("=" * 60)
    print("The octahedron doesn't encode into binary.")
    print("It IS the computation.")
    print("=" * 60)
