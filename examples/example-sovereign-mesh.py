"""
example-sovereign-mesh.py
Demonstrates the Sovereign Mesh Signaling Protocol:
  - Distributed factorization on the octahedral Cayley graph
  - 48 sovereign nodes (one per O_h group element)
  - Signal propagation via group ring composition
  - Self-healing: Byzantine fault tolerance via geometric validation
  - Smooth relation precipitation (not binary parity checking)

Requires: stdlib only (no numpy/scipy)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from sovereign_mesh import (
    SovereignMesh, NodeHealth, ConjugacyZone,
    smooth_over_base, trial_factor,
)


def demo_mesh_anatomy():
    """Show the mesh structure: nodes, zones, Cayley wiring."""
    print("=" * 60)
    print("[1] MESH ANATOMY")
    print("=" * 60)

    N = 3 * 17  # 51
    mesh = SovereignMesh(N, factor_base_size=25)
    status = mesh.mesh_status()

    print(f"\n  N = {N}")
    print(f"  Factor base ({len(mesh.factor_base)} primes): {mesh.factor_base[:8]}...")
    print(f"  Nodes: {status['nodes']} (one per O_h group element)")
    print(f"  Cayley diameter: {status['cayley_diameter']}")
    print(f"\n  Zone distribution:")
    for zone, count in sorted(status['zones'].items()):
        print(f"    {zone:<10s}: {count} nodes")

    # Show connectivity
    degrees = [len(n.neighbors) for n in mesh.nodes]
    print(f"\n  Connectivity:")
    print(f"    Min degree: {min(degrees)}")
    print(f"    Max degree: {max(degrees)}")
    print(f"    Avg degree: {sum(degrees)/len(degrees):.1f}")

    # Prime coverage
    assigned = sum(1 for n in mesh.nodes if n.primes)
    print(f"\n  Prime coverage: {assigned}/{len(mesh.nodes)} nodes have primes")


def demo_signal_flow():
    """Trace a signal through the mesh step by step."""
    print(f"\n{'=' * 60}")
    print("[2] SIGNAL FLOW: Tracing Precipitation")
    print("=" * 60)

    N = 77  # 7 x 11
    mesh = SovereignMesh(N, factor_base_size=20)
    sqrt_N = mesh._isqrt(N) + 1

    print(f"\n  N = {N}, sqrt(N)+1 = {sqrt_N}")
    print(f"  Factor base: {mesh.factor_base[:10]}")

    found = 0
    for a in range(sqrt_N, sqrt_N + 50):
        Q = a * a - N
        smooth = smooth_over_base(Q, mesh.factor_base)
        signal = mesh.broadcast(a)

        if smooth or signal:
            status = ""
            if smooth:
                status += f"smooth={smooth}"
            if signal:
                status += f" PRECIPITATED(path={signal.path}, contribs={signal.contributions})"
                found += 1
            print(f"  a={a:>3d}, Q={Q:>5d}: {status}")

        if found >= 3:
            break

    if found == 0:
        print(f"  (No precipitations in first 50 candidates)")


def demo_fault_tolerance():
    """Demonstrate mesh resilience under node failure."""
    print(f"\n{'=' * 60}")
    print("[3] FAULT TOLERANCE: Healing Under Damage")
    print("=" * 60)

    N = 221  # 13 x 17
    mesh = SovereignMesh(N, factor_base_size=25)

    # Baseline: sieve healthy mesh
    results_healthy = mesh.sieve(max_candidates=2000, heal_interval=5000)
    print(f"\n  Healthy mesh: {len(results_healthy)} precipitations in 2000 candidates")

    # Damage: kill 10 nodes, inflame 5
    for i in range(10):
        mesh.nodes[i].health = NodeHealth.NECROTIC
    for i in range(10, 15):
        mesh.nodes[i].health = NodeHealth.INFLAMED

    status = mesh.mesh_status()
    print(f"  After damage: {status['health']}")

    # Heal
    heal_result = mesh.health.heal_cycle()
    print(f"  After healing: bypassed={heal_result['bypassed']}, "
          f"active={heal_result['active_fraction']:.0%}")

    # Sieve damaged mesh
    mesh.candidates_tested = 0
    mesh.precipitated = []
    results_damaged = mesh.sieve(max_candidates=2000, heal_interval=5000)
    print(f"  Damaged mesh: {len(results_damaged)} precipitations in 2000 candidates")

    if results_damaged:
        print(f"  Mesh survived! Solutions still precipitate around dead nodes.")
    else:
        print(f"  Mesh degraded but structure preserved for recovery.")


def demo_factorization_suite():
    """Factor several numbers via the mesh."""
    print(f"\n{'=' * 60}")
    print("[4] FACTORIZATION SUITE")
    print("=" * 60)

    test_cases = [
        (15, "3 x 5"),
        (35, "5 x 7"),
        (77, "7 x 11"),
        (143, "11 x 13"),
        (221, "13 x 17"),
        (323, "17 x 19"),
    ]

    print(f"\n  {'N':>5s}  {'Expected':>10s}  {'Precip':>6s}  {'Candidates':>10s}  {'Time':>6s}")
    print(f"  {'-'*45}")

    for N, expected in test_cases:
        mesh = SovereignMesh(N, factor_base_size=30)
        start = time.time()
        results = mesh.sieve(max_candidates=5000, heal_interval=10000)
        elapsed = time.time() - start

        print(f"  {N:>5d}  {expected:>10s}  {len(results):>6d}  "
              f"{mesh.candidates_tested:>10d}  {elapsed:>5.2f}s")


def demo_why_geometry():
    """Explain why the geometric mesh matters."""
    print(f"\n{'=' * 60}")
    print("[5] WHY GEOMETRY")
    print("=" * 60)

    print(f"""
  The Sovereign Mesh is NOT a quadratic sieve with extra steps.
  The geometry changes what's computable:

  1. TOPOLOGY = ALGEBRA
     Binary sieve: nodes are array indices. Edges are iteration order.
     Cayley mesh: nodes ARE group elements. Edges ARE generator relations.
     The topology encodes algebraic structure that flat arrays cannot.

  2. SIGNALS COMPOSE (not XOR)
     Binary: parity ^= (exp % 2)     — destroys information
     Cayley: signal *= prime_rotation — preserves which rotation cancelled
     The signal carries more information through the mesh.

  3. SELF-HEALING IS ALGEBRAIC
     Binary: dead node = missing index. Requires central coordination.
     Cayley: dead node = missing vertex. Cayley graph guarantees
     alternative paths through the same algebraic structure.

  4. PRIMES HAVE GEOMETRIC POSITION
     Binary: prime p gets index i. No relationship between indices.
     Cayley: prime p gets a rotation of order resonating with p.
     Primes 2 and 5 are Cayley-distance 1 (geometrically adjacent).
     Primes 3 and 7 are Cayley-distance 5 (maximally separated).
     This encodes number-theoretic relationships in the mesh wiring.
""")


if __name__ == "__main__":
    print("=" * 60)
    print("SOVEREIGN MESH — Example Script")
    print("  Nodes are rotations. Solutions precipitate.")
    print("=" * 60)

    demo_mesh_anatomy()
    demo_signal_flow()
    demo_fault_tolerance()
    demo_factorization_suite()
    demo_why_geometry()

    print("=" * 60)
    print("The mesh doesn't search for factors.")
    print("The factors precipitate from the geometry.")
    print("=" * 60)
