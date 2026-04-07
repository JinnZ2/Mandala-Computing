"""
Example: Octahedral Resilience v1.0

Demonstrates the full self-healing infrastructure:
  1. Health monitoring and failover clustering
  2. Seed compression and threshold secret sharing
  3. Safe reconfiguration with circuit breakers
  4. Merkle-based partition sync
  5. Priority scheduling
  6. Signed audit trail
  7. Full system status

Run: python examples/example-resilience.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from octahedral_resilience import (
    demo_health_monitoring, demo_seed_dispersal,
    demo_safe_reconfig, demo_merkle_sync,
    demo_priority_scheduling, demo_audit_trail,
    demo_system_status,
)


if __name__ == "__main__":
    print()
    print("OCTAHEDRAL RESILIENCE v1.0")
    print("Self-healing distributed infrastructure")
    print()

    demo_health_monitoring()
    demo_seed_dispersal()
    demo_safe_reconfig()
    demo_merkle_sync()
    demo_priority_scheduling()
    demo_audit_trail()
    demo_system_status()

    print()
    print("=" * 60)
    print("Resilience demo complete.")
    print("=" * 60)
