"""
Example: Octahedral Session Cache v1.0

Demonstrates cache coherence with geometric validation:
  1. Basic put/get with constraint snapshots
  2. Cascade invalidation along octahedral edges
  3. Persist and restore with live revalidation
  4. Distance metrics (L-inf, L2, phi-weighted)
  5. Invalidation graph structure

Run: python examples/example-session-cache.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from octahedral_session_cache import (
    demo_basic_cache, demo_cascade_invalidation,
    demo_persistence, demo_distance_metrics,
    demo_graph_structure,
)


if __name__ == "__main__":
    print()
    print("OCTAHEDRAL SESSION CACHE v1.0")
    print("Geometric coherence caching")
    print()

    demo_basic_cache()
    demo_cascade_invalidation()
    demo_persistence()
    demo_distance_metrics()
    demo_graph_structure()

    print()
    print("=" * 60)
    print("Session cache demo complete.")
    print("=" * 60)
