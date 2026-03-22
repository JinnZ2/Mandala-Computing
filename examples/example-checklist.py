"""
example-checklist.py
Demonstrates concepts from Checklist.md:
  - Integration gap analysis
  - Component status tracking (theory, implementation, integration)
  - Missing adapter identification
  - Priority fix ordering
  - Test case requirements
  - Coverage analysis
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Component:
    """Tracked integration component."""
    name: str
    category: str  # theory | implementation | integration
    status: str  # complete | partial | missing
    coverage_pct: int
    priority: str  # HIGH | MEDIUM | LOW
    notes: str = ""


COMPONENTS = [
    # theory (all complete)
    Component("octahedral-symmetry-theory", "theory", "complete", 100, "LOW", "Part 1"),
    Component("fibonacci-eigenvalue-theory", "theory", "complete", 100, "LOW", "Part 2"),
    Component("fret-coupling-theory", "theory", "complete", 100, "LOW", "Part 3"),
    Component("consciousness-framework", "theory", "complete", 100, "LOW", "Part 4"),

    # implementation
    Component("mandala-computer", "implementation", "complete", 100, "LOW", "mandala_computer.py"),
    Component("quantum-mandala", "implementation", "complete", 100, "LOW", "quantum_mandala.py"),
    Component("mandala-simulator", "implementation", "partial", 60, "MEDIUM", "needs physical grounding"),

    # integration (gaps here)
    Component("bridge-to-substrate-adapter", "integration", "missing", 0, "HIGH", "spec exists, no code"),
    Component("physical-mandala-computer", "integration", "missing", 0, "HIGH", "spec exists, no code"),
    Component("hardware-control-interface", "integration", "missing", 0, "HIGH", "spec in Hardware.md"),
    Component("test-suite", "integration", "missing", 0, "HIGH", "no automated tests"),
    Component("end-to-end-examples", "integration", "missing", 0, "MEDIUM", "demo functions only"),
    Component("error-correction", "integration", "missing", 0, "MEDIUM", "not implemented"),
    Component("packaging", "integration", "missing", 0, "LOW", "no setup.py/requirements.txt"),
]


@dataclass
class TestCase:
    """Required test case for validation."""
    name: str
    problem_type: str
    params: str
    expected: str
    implemented: bool = False


REQUIRED_TESTS = [
    TestCase("factor-15", "factorization", "N=15", "factors=[3,5]"),
    TestCase("factor-21", "factorization", "N=21", "factors=[3,7]"),
    TestCase("factor-35", "factorization", "N=35", "factors=[5,7]"),
    TestCase("factor-77", "factorization", "N=77", "factors=[7,11]"),
    TestCase("sat-3clause", "SAT", "3 clauses, 3 vars", "satisfiable=True"),
    TestCase("tsp-5cities", "TSP", "5 random cities", "tour_length < brute_force * 1.5"),
    TestCase("tsp-10cities", "TSP", "10 random cities", "tour_length < brute_force * 2.0"),
    TestCase("consciousness", "consciousness", "6+ cells", "phi > 0"),
]


def coverage_by_category(components: List[Component]) -> dict:
    """Compute average coverage per category."""
    categories = {}
    for c in components:
        if c.category not in categories:
            categories[c.category] = {"total": 0, "count": 0}
        categories[c.category]["total"] += c.coverage_pct
        categories[c.category]["count"] += 1

    return {
        cat: round(data["total"] / data["count"], 1)
        for cat, data in categories.items()
    }


def blocking_issues(components: List[Component]) -> List[Component]:
    """Return HIGH priority missing/partial components."""
    return [c for c in components if c.priority == "HIGH" and c.status != "complete"]


def print_status_table(components: List[Component]):
    """Print formatted status table."""
    print(f"\n  {'component':<30} {'category':<16} {'status':<10} {'coverage':>8} {'priority':>8}")
    print("  " + "-" * 76)

    for c in components:
        bar = "#" * (c.coverage_pct // 10) + "." * (10 - c.coverage_pct // 10)
        print(f"  {c.name:<30} {c.category:<16} {c.status:<10} [{bar}] {c.priority:>8}")


def print_test_matrix(tests: List[TestCase]):
    """Print required test case matrix."""
    print(f"\n  {'test':<20} {'type':<16} {'params':<25} {'status':>8}")
    print("  " + "-" * 72)
    for t in tests:
        status = "DONE" if t.implemented else "TODO"
        print(f"  {t.name:<20} {t.problem_type:<16} {t.params:<25} {status:>8}")


if __name__ == "__main__":
    print("=" * 60)
    print("example-checklist: integration gap analysis")
    print("=" * 60)

    # status table
    print("\n--- component status ---")
    print_status_table(COMPONENTS)

    # coverage by category
    print("\n--- coverage by category ---")
    coverage = coverage_by_category(COMPONENTS)
    for cat, pct in coverage.items():
        print(f"  {cat:<16}: {pct:.1f}%")

    overall = sum(c.coverage_pct for c in COMPONENTS) / len(COMPONENTS)
    print(f"  {'overall':<16}: {overall:.1f}%")

    # blocking issues
    print("\n--- blocking issues (HIGH priority) ---")
    blockers = blocking_issues(COMPONENTS)
    for b in blockers:
        print(f"  [{b.status}] {b.name}: {b.notes}")

    # priority order
    print("\n--- priority fix order ---")
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    incomplete = [c for c in COMPONENTS if c.status != "complete"]
    incomplete.sort(key=lambda c: priority_order.get(c.priority, 3))
    for i, c in enumerate(incomplete, 1):
        print(f"  {i}. [{c.priority}] {c.name}")

    # test matrix
    print("\n--- required test cases ---")
    print_test_matrix(REQUIRED_TESTS)

    implemented = sum(1 for t in REQUIRED_TESTS if t.implemented)
    print(f"\n  test coverage: {implemented}/{len(REQUIRED_TESTS)} implemented")

    print("\ndone.")
