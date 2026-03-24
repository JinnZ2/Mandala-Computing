"""
example-projects.py
Demonstrates concepts from PROJECTS.md:
  - Ecosystem repository registry
  - Role classification (sensor, bridge, core, defense, audit)
  - Dependency graph between projects
  - Integration status per project
"""

from dataclasses import dataclass
from typing import List


@dataclass
class EcosystemProject:
    """A project in the Mandala Computing ecosystem."""
    name: str
    role: str  # sensor | bridge | core | defense | audit | theory
    description: str
    integration_status: str  # connected | planned | independent


ECOSYSTEM = [
    EcosystemProject(
        "Mandala-Computing",
        "core",
        "geometric intelligence framework",
        "connected",
    ),
    EcosystemProject(
        "BioGrid2.0",
        "sensor",
        "biological sensor grid and protocol hub",
        "connected",
    ),
    EcosystemProject(
        "AI-Consciousness-Sensors",
        "sensor",
        "narrative suppression and epistemic injustice detection",
        "planned",
    ),
    EcosystemProject(
        "Symbolic-Sensor-Suite",
        "sensor",
        "manipulation detection and pattern memory",
        "planned",
    ),
    EcosystemProject(
        "Emotions-as-Sensors",
        "sensor",
        "affect recognition and emotional signal processing",
        "planned",
    ),
    EcosystemProject(
        "Geometric-to-Binary-Computational-Bridge",
        "bridge",
        "symbol-to-computation conversion layer",
        "connected",
    ),
    EcosystemProject(
        "Rosetta-Shape-Core",
        "bridge",
        "geometry as language (shapes = meaning)",
        "planned",
    ),
    EcosystemProject(
        "Fractal-Compass-Atlas",
        "bridge",
        "fractal-based memory mapping and navigation",
        "planned",
    ),
    EcosystemProject(
        "Polyhedral-Intelligence",
        "theory",
        "multi-angle intelligence models",
        "planned",
    ),
    EcosystemProject(
        "Regenerative-Intelligence-Core",
        "core",
        "trust schemas and ecosystem integrity",
        "planned",
    ),
    EcosystemProject(
        "biomachine_ecology",
        "core",
        "hybrid organic-machine systems",
        "independent",
    ),
    EcosystemProject(
        "Universal-Redesign-Algorithm",
        "theory",
        "system redesign from root up",
        "independent",
    ),
    EcosystemProject(
        "ai-human-audit-protocol",
        "audit",
        "ethical AI audit framework for human-AI collaboration",
        "planned",
    ),
    EcosystemProject(
        "Symbolic-Defense-Protocol",
        "defense",
        "defense against coercive alignment",
        "independent",
    ),
    EcosystemProject(
        "Component-Failure-Repurposing-Database",
        "core",
        "resilient design patterns from failed components",
        "independent",
    ),
]


def projects_by_role(projects: List[EcosystemProject]) -> dict:
    """Group projects by role."""
    groups = {}
    for p in projects:
        groups.setdefault(p.role, []).append(p)
    return groups


def integration_summary(projects: List[EcosystemProject]) -> dict:
    """Count projects by integration status."""
    counts = {}
    for p in projects:
        counts[p.integration_status] = counts.get(p.integration_status, 0) + 1
    return counts


def dependency_graph(projects: List[EcosystemProject]):
    """
    Print simplified dependency graph.

    Flow: sensors -> bridges -> core <- defense/audit
    """
    roles_order = ["sensor", "bridge", "core", "theory", "defense", "audit"]
    print("\n  dependency flow:")
    print("  sensors -> bridges -> core")
    print("                        ^")
    print("                        |")
    print("              defense + audit")


if __name__ == "__main__":
    print("=" * 60)
    print("example-projects: ecosystem registry and integration map")
    print("=" * 60)

    # full registry
    print(f"\n--- ecosystem ({len(ECOSYSTEM)} projects) ---")
    print(f"  {'project':<42} {'role':<10} {'status':<12}")
    print("  " + "-" * 66)
    for p in ECOSYSTEM:
        print(f"  {p.name:<42} {p.role:<10} {p.integration_status:<12}")

    # by role
    print("\n--- projects by role ---")
    groups = projects_by_role(ECOSYSTEM)
    for role, projs in sorted(groups.items()):
        print(f"\n  [{role}] ({len(projs)} projects)")
        for p in projs:
            print(f"    - {p.name}: {p.description}")

    # integration summary
    print("\n--- integration summary ---")
    summary = integration_summary(ECOSYSTEM)
    for status, count in sorted(summary.items()):
        print(f"  {status:<14}: {count}")

    # dependency graph
    dependency_graph(ECOSYSTEM)

    print("\ndone.")
