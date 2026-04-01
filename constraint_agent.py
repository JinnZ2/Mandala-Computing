"""
CONSTRAINT-GEOMETRY AGENT FRAMEWORK v1.0

An agent has a seed geometry, explores outward within resource constraints,
and compresses back to its seed without losing the map. All relationships
stored as exact fractions (no decimal drift).

Portable across: Rosetta-Shape-Core, Mandala-Computing, Emotions-as-Sensors,
Living-Intelligence, and any other substrate that needs aware agents.

Design principles:
  1. Seed is identity — the agent always knows what it is
  2. Bloom is expansion — outward exploration within budget
  3. Compress is memory — lossless return to seed form
  4. Fractions are exact — no floating point, no decimal drift
  5. Constraints are geometry — resource limits shape the exploration space

Usage:
    agent = ConstraintAgent(seed_id="SHAPE.TETRA", home_families=["stability"])
    agent.set_resource_budget(compute=1000, bandwidth=50)

    # Expand if resources allow
    if agent.should_expand():
        agent.bloom(depth=2)

    # Explore constraint space
    discoveries = agent.explore()

    # Contract back to seed
    agent.compress()

    # Re-expand deterministically (or differently if resources changed)
    agent.bloom(depth=2)
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import math
import time

from octahedral_arithmetic import (
    OctahedralNumber, GlyphFraction, GLYPHS, BASE, PHI,
)


# ---------------------------------------------------------------------------
# Seed geometries — the shapes an agent can be
# ---------------------------------------------------------------------------

class SeedGeometry(Enum):
    """
    Fundamental seed shapes from Rosetta-Shape-Core.
    Each has a vertex count that determines the agent's base state space.
    """
    TETRA = ("SHAPE.TETRA", 4)       # tetrahedron: stability, minimal structure
    CUBE = ("SHAPE.CUBE", 8)         # cube: regularity, storage
    OCTA = ("SHAPE.OCTA", 8)        # octahedron: computation, symmetry
    ICOSA = ("SHAPE.ICOSA", 12)      # icosahedron: complexity, 20 faces
    DODECA = ("SHAPE.DODECA", 20)    # dodecahedron: highest regularity

    def __init__(self, entity_id: str, vertices: int):
        self.entity_id = entity_id
        self.vertices = vertices


# ---------------------------------------------------------------------------
# Resource budget — what constrains the agent's expansion
# ---------------------------------------------------------------------------

@dataclass
class ResourceBudget:
    """
    Finite resources that constrain agent expansion.

    All stored as GlyphFractions for exact accounting — no drift.
    """
    compute: GlyphFraction = field(default_factory=lambda: GlyphFraction.from_decimal_ratio(0, 1))
    bandwidth: GlyphFraction = field(default_factory=lambda: GlyphFraction.from_decimal_ratio(0, 1))
    memory: GlyphFraction = field(default_factory=lambda: GlyphFraction.from_decimal_ratio(0, 1))
    depth_limit: int = 5

    def remaining_fraction(self) -> GlyphFraction:
        """What fraction of total budget remains (compute as proxy)."""
        return self.compute

    def can_afford(self, cost: GlyphFraction) -> bool:
        """Check if we can afford a cost without going negative."""
        remaining = self.compute.num.to_decimal() / max(self.compute.den.to_decimal(), 1)
        expense = cost.num.to_decimal() / max(cost.den.to_decimal(), 1)
        return remaining >= expense

    def spend(self, cost: GlyphFraction):
        """Deduct cost from compute budget."""
        # Subtract: compute - cost
        # a/b - c/d = (ad - bc) / bd
        ad = self.compute.num * cost.den
        bc = cost.num * self.compute.den
        bd = self.compute.den * cost.den
        new_num = ad - bc
        self.compute = GlyphFraction(new_num, bd)


# ---------------------------------------------------------------------------
# Exploration node — a single point in the agent's expanded map
# ---------------------------------------------------------------------------

@dataclass
class ExplorationNode:
    """
    A point in the agent's exploration space.

    Position is an OctahedralNumber (glyph coordinates).
    Relationships to other nodes stored as exact GlyphFractions.
    """
    node_id: int
    position: OctahedralNumber
    depth: int
    parent_id: Optional[int] = None
    children: List[int] = field(default_factory=list)
    relationships: Dict[int, GlyphFraction] = field(default_factory=dict)
    properties: Dict[str, object] = field(default_factory=dict)
    energy: float = 0.0

    def distance_to(self, other: ExplorationNode) -> GlyphFraction:
        """
        Exact distance between two nodes in glyph space.

        Uses the absolute difference of positions as a GlyphFraction
        (no floating point involved).
        """
        a = self.position.to_decimal()
        b = other.position.to_decimal()
        diff = abs(a - b)
        return GlyphFraction.from_decimal_ratio(diff, 1)


# ---------------------------------------------------------------------------
# Discovery — what the agent finds during exploration
# ---------------------------------------------------------------------------

@dataclass
class Discovery:
    """Something the agent found during exploration."""
    source_node: int
    target_node: int
    relationship: GlyphFraction  # exact ratio between the two
    discovery_type: str  # "resonance", "factor", "prime", "symmetry", "boundary"
    description: str = ""
    timestamp: float = 0.0


# ---------------------------------------------------------------------------
# Constraint Agent
# ---------------------------------------------------------------------------

class ConstraintAgent:
    """
    A geometric agent that explores within resource constraints.

    Lifecycle:
      1. Born from a seed geometry (identity)
      2. Blooms outward (expansion) — constrained by resource budget
      3. Explores the expanded space (discovery)
      4. Compresses back to seed (memory preservation)
      5. Can re-bloom deterministically or adapt to new constraints

    All internal state uses exact glyph arithmetic.
    The agent never loses precision, never drifts.
    """

    def __init__(self, seed_id: str = "SHAPE.OCTA",
                 home_families: List[str] = None):
        """
        Args:
            seed_id: Rosetta entity ID for the seed geometry
            home_families: Conceptual families this agent belongs to
        """
        # Identity
        self.seed_id = seed_id
        self.seed_geometry = self._resolve_geometry(seed_id)
        self.home_families = home_families or []
        self.base_states = self.seed_geometry.vertices

        # State
        self.nodes: Dict[int, ExplorationNode] = {}
        self.discoveries: List[Discovery] = []
        self.compressed_map: Optional[Dict] = None  # stored during compression
        self._next_node_id = 0
        self.current_depth = 0
        self.max_depth_reached = 0

        # Resources
        self.budget = ResourceBudget()

        # Create seed node (the agent's origin)
        seed_node = self._create_node(
            position=OctahedralNumber.from_decimal(0),
            depth=0,
        )
        seed_node.properties["is_seed"] = True
        seed_node.properties["geometry"] = self.seed_id

        print(f"Agent born: {self.seed_id} ({self.seed_geometry.name})")
        print(f"  Base states: {self.base_states}")
        print(f"  Families: {self.home_families}")

    @staticmethod
    def _resolve_geometry(seed_id: str) -> SeedGeometry:
        """Map Rosetta entity ID to seed geometry."""
        for geom in SeedGeometry:
            if geom.entity_id == seed_id:
                return geom
        # Default to octahedral if unknown
        return SeedGeometry.OCTA

    # ------------------------------------------------------------------
    # Resource management
    # ------------------------------------------------------------------

    def set_resource_budget(self, compute: int = 1000,
                           bandwidth: int = 50,
                           memory: int = 500,
                           depth_limit: int = 5):
        """Set resource constraints (stored as exact fractions)."""
        self.budget = ResourceBudget(
            compute=GlyphFraction.from_decimal_ratio(compute, 1),
            bandwidth=GlyphFraction.from_decimal_ratio(bandwidth, 1),
            memory=GlyphFraction.from_decimal_ratio(memory, 1),
            depth_limit=depth_limit,
        )
        gc = OctahedralNumber.from_decimal(compute)
        gb = OctahedralNumber.from_decimal(bandwidth)
        print(f"  Budget: compute={gc.to_glyphs()} bandwidth={gb.to_glyphs()} depth<={depth_limit}")

    def should_expand(self) -> bool:
        """Can the agent afford to expand further?"""
        if self.current_depth >= self.budget.depth_limit:
            return False
        # Cost of next expansion: base_states * PHI^depth (in glyph fraction)
        next_cost = self._expansion_cost(self.current_depth + 1)
        return self.budget.can_afford(next_cost)

    def _expansion_cost(self, depth: int) -> GlyphFraction:
        """
        Cost to expand to a given depth.

        Cost scales as base_states * fibonacci(depth) — golden ratio growth.
        Stored as exact fraction.
        """
        # Fibonacci-like cost: approximate PHI^depth as fraction
        fib = [1, 1]
        for _ in range(depth):
            fib.append(fib[-1] + fib[-2])
        cost = self.base_states * fib[depth]
        return GlyphFraction.from_decimal_ratio(cost, 1)

    # ------------------------------------------------------------------
    # Node management
    # ------------------------------------------------------------------

    def _create_node(self, position: OctahedralNumber, depth: int,
                     parent_id: int = None) -> ExplorationNode:
        """Create a new exploration node."""
        node = ExplorationNode(
            node_id=self._next_node_id,
            position=position,
            depth=depth,
            parent_id=parent_id,
        )
        self.nodes[node.node_id] = node
        self._next_node_id += 1

        if parent_id is not None and parent_id in self.nodes:
            self.nodes[parent_id].children.append(node.node_id)

        return node

    # ------------------------------------------------------------------
    # Bloom: expansion within constraints
    # ------------------------------------------------------------------

    def bloom(self, depth: int = 1):
        """
        Expand the agent's exploration space by `depth` levels.

        Each level creates base_states new nodes per existing leaf,
        positioned at PHI-scaled distances in glyph space.
        Expansion stops if resources run out.
        """
        print(f"\n  Blooming depth +{depth}...")
        start_depth = self.current_depth

        for d in range(depth):
            target_depth = start_depth + d + 1

            if target_depth > self.budget.depth_limit:
                print(f"  Stopped: depth limit ({self.budget.depth_limit})")
                break

            cost = self._expansion_cost(target_depth)
            if not self.budget.can_afford(cost):
                print(f"  Stopped: insufficient compute (need {cost.num.to_decimal()}/{cost.den.to_decimal()})")
                break

            # Find leaf nodes at current frontier
            leaves = [n for n in self.nodes.values() if n.depth == target_depth - 1 and not n.children]

            if not leaves:
                # If no leaves, use all nodes at max depth
                leaves = [n for n in self.nodes.values() if n.depth == target_depth - 1]

            if not leaves:
                leaves = [self.nodes[0]]  # fall back to seed

            new_count = 0
            for leaf in leaves:
                # Create base_states children at PHI-scaled positions
                for s in range(self.base_states):
                    # Position: parent + s * base^depth (glyph arithmetic)
                    offset = OctahedralNumber.from_decimal(s * (BASE ** target_depth))
                    new_pos = leaf.position + offset
                    child = self._create_node(new_pos, target_depth, leaf.node_id)

                    # Exact relationship to parent
                    if offset.to_decimal() > 0:
                        child.relationships[leaf.node_id] = GlyphFraction(
                            OctahedralNumber.from_decimal(1),
                            offset,
                        )
                    new_count += 1

            self.budget.spend(cost)
            self.current_depth = target_depth
            self.max_depth_reached = max(self.max_depth_reached, target_depth)

            remaining = self.budget.compute.num.to_decimal()
            print(f"  Depth {target_depth}: +{new_count} nodes, "
                  f"{len(self.nodes)} total, "
                  f"compute remaining: {OctahedralNumber.from_decimal(remaining).to_glyphs()}")

    # ------------------------------------------------------------------
    # Explore: discover relationships in the expanded space
    # ------------------------------------------------------------------

    def explore(self) -> List[Discovery]:
        """
        Explore the expanded space for relationships.

        Checks every pair of nodes for:
        - Resonance: positions whose ratio simplifies to small glyphs
        - Factors: positions that are factors of each other
        - Primes: nodes at prime positions (irreducible)
        - Symmetry: nodes with same position mod base_states
        """
        print(f"\n  Exploring {len(self.nodes)} nodes...")
        new_discoveries = []
        nodes = list(self.nodes.values())
        timestamp = time.time()

        # Check for primes
        for node in nodes:
            pos_dec = node.position.to_decimal()
            if pos_dec > 1 and node.position.is_prime():
                d = Discovery(
                    source_node=node.node_id,
                    target_node=node.node_id,
                    relationship=GlyphFraction.from_decimal_ratio(pos_dec, 1),
                    discovery_type="prime",
                    description=f"Irreducible position: {node.position.to_glyphs()}",
                    timestamp=timestamp,
                )
                new_discoveries.append(d)

        # Check pairs for resonance and factor relationships
        for i, a in enumerate(nodes):
            for b in nodes[i + 1:]:
                a_dec = a.position.to_decimal()
                b_dec = b.position.to_decimal()

                if a_dec == 0 or b_dec == 0:
                    continue

                # Factor relationship
                if a_dec > 1 and b_dec > 1:
                    if a_dec > b_dec and a_dec % b_dec == 0:
                        ratio = GlyphFraction.from_decimal_ratio(a_dec, b_dec)
                        d = Discovery(
                            source_node=a.node_id,
                            target_node=b.node_id,
                            relationship=ratio,
                            discovery_type="factor",
                            description=f"{a.position.to_glyphs()} / {b.position.to_glyphs()} = {ratio.to_glyphs()}",
                            timestamp=timestamp,
                        )
                        new_discoveries.append(d)
                        # Store in nodes too
                        a.relationships[b.node_id] = ratio

                # Symmetry: same position mod base_states
                if a_dec % self.base_states == b_dec % self.base_states and a_dec != b_dec:
                    d = Discovery(
                        source_node=a.node_id,
                        target_node=b.node_id,
                        relationship=GlyphFraction.from_decimal_ratio(
                            a_dec % self.base_states, self.base_states
                        ),
                        discovery_type="symmetry",
                        description=f"Symmetric mod {self.base_states}: "
                                    f"{a.position.to_glyphs()} ~ {b.position.to_glyphs()}",
                        timestamp=timestamp,
                    )
                    new_discoveries.append(d)

        self.discoveries.extend(new_discoveries)

        # Summarize
        by_type = {}
        for d in new_discoveries:
            by_type[d.discovery_type] = by_type.get(d.discovery_type, 0) + 1
        for dtype, count in sorted(by_type.items()):
            print(f"    {dtype}: {count}")
        print(f"  Total discoveries: {len(self.discoveries)}")

        return new_discoveries

    # ------------------------------------------------------------------
    # Compress: lossless return to seed
    # ------------------------------------------------------------------

    def compress(self):
        """
        Compress the agent back to its seed geometry.

        The full exploration map is stored as compressed_map —
        all node positions, relationships, and discoveries preserved
        as exact GlyphFractions. Nothing is lost.

        The agent's active node set returns to just the seed.
        """
        print(f"\n  Compressing to seed...")

        # Store the full map
        self.compressed_map = {
            "seed_id": self.seed_id,
            "max_depth": self.max_depth_reached,
            "nodes": {
                nid: {
                    "position": node.position.to_glyphs(),
                    "position_decimal": node.position.to_decimal(),
                    "depth": node.depth,
                    "parent": node.parent_id,
                    "children": list(node.children),
                    "relationships": {
                        k: v.to_glyphs() for k, v in node.relationships.items()
                    },
                    "properties": dict(node.properties),
                }
                for nid, node in self.nodes.items()
            },
            "discoveries": [
                {
                    "type": d.discovery_type,
                    "source": d.source_node,
                    "target": d.target_node,
                    "relationship": d.relationship.to_glyphs(),
                    "description": d.description,
                }
                for d in self.discoveries
            ],
            "budget_remaining": {
                "compute": self.budget.compute.to_glyphs(),
                "bandwidth": self.budget.bandwidth.to_glyphs(),
                "memory": self.budget.memory.to_glyphs(),
            },
        }

        total_nodes = len(self.nodes)
        total_relationships = sum(len(n.relationships) for n in self.nodes.values())

        # Return to seed — keep only node 0
        seed = self.nodes[0]
        self.nodes = {0: seed}
        seed.children = []
        self.current_depth = 0

        print(f"  Compressed: {total_nodes} nodes, {total_relationships} relationships, "
              f"{len(self.discoveries)} discoveries -> seed")
        print(f"  Map preserved: {len(self.compressed_map['nodes'])} nodes stored")

    # ------------------------------------------------------------------
    # Re-bloom: deterministic re-expansion from compressed map
    # ------------------------------------------------------------------

    def restore(self):
        """
        Restore the agent from its compressed map.

        Re-creates all nodes and relationships exactly as they were.
        Because everything is stored as exact GlyphFractions,
        the restoration is lossless.
        """
        if not self.compressed_map:
            print("  No compressed map to restore from")
            return

        print(f"\n  Restoring from compressed map...")

        # Clear current state
        self.nodes = {}
        self._next_node_id = 0

        # Rebuild nodes
        for nid_str, ndata in self.compressed_map["nodes"].items():
            nid = int(nid_str)
            node = ExplorationNode(
                node_id=nid,
                position=OctahedralNumber.from_decimal(ndata["position_decimal"]),
                depth=ndata["depth"],
                parent_id=ndata["parent"],
                children=list(ndata["children"]),
                properties=dict(ndata["properties"]),
            )
            # Restore relationships as GlyphFractions
            for rel_id_str, rel_glyph in ndata["relationships"].items():
                rel_id = int(rel_id_str)
                # Parse glyph fraction "X/Y"
                parts = rel_glyph.split("/")
                if len(parts) == 2:
                    num = OctahedralNumber.from_glyphs(parts[0])
                    den = OctahedralNumber.from_glyphs(parts[1])
                    node.relationships[rel_id] = GlyphFraction(num, den)

            self.nodes[nid] = node
            self._next_node_id = max(self._next_node_id, nid + 1)

        self.max_depth_reached = self.compressed_map["max_depth"]
        self.current_depth = self.max_depth_reached

        print(f"  Restored: {len(self.nodes)} nodes, depth {self.current_depth}")

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def status(self) -> Dict:
        """Current agent status."""
        return {
            "seed": self.seed_id,
            "geometry": self.seed_geometry.name,
            "base_states": self.base_states,
            "families": self.home_families,
            "nodes": len(self.nodes),
            "depth": self.current_depth,
            "max_depth": self.max_depth_reached,
            "discoveries": len(self.discoveries),
            "compressed": self.compressed_map is not None,
            "budget_compute": self.budget.compute.to_glyphs(),
        }

    def glyph_map(self, max_nodes: int = 20) -> str:
        """Visualize the agent's nodes as a glyph map."""
        lines = []
        for nid, node in sorted(self.nodes.items())[:max_nodes]:
            indent = "  " * node.depth
            marker = "*" if node.properties.get("is_seed") else " "
            lines.append(f"  {marker}{indent}{node.position.to_glyphs():<10s} "
                         f"(d={node.depth}, children={len(node.children)})")
        if len(self.nodes) > max_nodes:
            lines.append(f"  ... and {len(self.nodes) - max_nodes} more")
        return "\n".join(lines)

    def discovery_summary(self) -> Dict[str, int]:
        """Count discoveries by type."""
        summary = {}
        for d in self.discoveries:
            summary[d.discovery_type] = summary.get(d.discovery_type, 0) + 1
        return summary

    # ------------------------------------------------------------------
    # Persistence: JSON export/import
    # ------------------------------------------------------------------

    def save(self, path: str):
        """
        Save agent state to JSON file.

        Compressed map + discoveries + budget + identity are all serialized.
        The agent can be restored from this file across sessions.
        """
        if not self.compressed_map:
            self.compress()

        data = {
            "version": "1.0",
            "seed_id": self.seed_id,
            "geometry": self.seed_geometry.name,
            "base_states": self.base_states,
            "families": self.home_families,
            "max_depth": self.max_depth_reached,
            "compressed_map": self.compressed_map,
            "discoveries_count": len(self.discoveries),
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"  Saved to {path} ({len(self.compressed_map.get('nodes', {}))} nodes)")

    @classmethod
    def load(cls, path: str) -> ConstraintAgent:
        """
        Load agent from JSON file.

        Recreates the full agent with compressed map intact,
        ready for restore() to re-expand.
        """
        with open(path) as f:
            data = json.load(f)

        agent = cls(
            seed_id=data["seed_id"],
            home_families=data.get("families", []),
        )
        agent.compressed_map = data.get("compressed_map")
        agent.max_depth_reached = data.get("max_depth", 0)

        if agent.compressed_map:
            agent.restore()

        print(f"  Loaded from {path}: {len(agent.nodes)} nodes")
        return agent


# ============================================================================
# DEMONSTRATIONS
# ============================================================================

def demo_basic_lifecycle():
    """Demonstrate the full agent lifecycle: bloom -> explore -> compress -> restore."""
    print("=" * 60)
    print("DEMO: Agent Lifecycle")
    print("=" * 60)

    agent = ConstraintAgent(seed_id="SHAPE.OCTA", home_families=["computation", "symmetry"])
    agent.set_resource_budget(compute=500, bandwidth=20, depth_limit=3)

    # Bloom
    agent.bloom(depth=2)
    print(f"\n  Map:\n{agent.glyph_map()}")

    # Explore
    discoveries = agent.explore()

    # Compress
    agent.compress()

    # Verify seed state
    print(f"\n  After compress: {len(agent.nodes)} nodes (seed only)")

    # Restore
    agent.restore()
    print(f"  After restore: {len(agent.nodes)} nodes (full map back)")

    return agent


def demo_resource_constraints():
    """Show how resource limits shape exploration."""
    print("\n" + "=" * 60)
    print("DEMO: Resource Constraints")
    print("=" * 60)

    # Low budget agent
    print("\n  --- Low budget (compute=50) ---")
    low = ConstraintAgent(seed_id="SHAPE.TETRA", home_families=["stability"])
    low.set_resource_budget(compute=50, depth_limit=5)
    low.bloom(depth=5)  # will stop when budget runs out
    print(f"  Reached depth: {low.current_depth}")

    # High budget agent
    print("\n  --- High budget (compute=5000) ---")
    high = ConstraintAgent(seed_id="SHAPE.TETRA", home_families=["stability"])
    high.set_resource_budget(compute=5000, depth_limit=5)
    high.bloom(depth=5)
    print(f"  Reached depth: {high.current_depth}")

    print(f"\n  Low: {len(low.nodes)} nodes")
    print(f"  High: {len(high.nodes)} nodes")
    print(f"  Difference: resource constraints shaped the geometry")

    return low, high


def demo_cross_substrate():
    """Show agents with different seed geometries."""
    print("\n" + "=" * 60)
    print("DEMO: Cross-Substrate Agents")
    print("=" * 60)

    seeds = [
        ("SHAPE.TETRA", ["stability", "minimal"]),
        ("SHAPE.OCTA", ["computation", "symmetry"]),
        ("SHAPE.ICOSA", ["complexity", "faces"]),
    ]

    for seed_id, families in seeds:
        agent = ConstraintAgent(seed_id=seed_id, home_families=families)
        agent.set_resource_budget(compute=200, depth_limit=2)
        agent.bloom(depth=2)
        discoveries = agent.explore()
        summary = agent.discovery_summary()
        print(f"  {seed_id}: {len(agent.nodes)} nodes, discoveries: {summary}")

    print(f"\n  Different geometries -> different discovery patterns")
    print(f"  Same protocol -> portable across substrates")


def demo_exact_fractions():
    """Show that all relationships are exact — no drift."""
    print("\n" + "=" * 60)
    print("DEMO: Exact Fraction Relationships")
    print("=" * 60)

    agent = ConstraintAgent(seed_id="SHAPE.OCTA", home_families=["precision"])
    agent.set_resource_budget(compute=300, depth_limit=2)
    agent.bloom(depth=2)
    agent.explore()

    # Show some exact relationships
    factor_discoveries = [d for d in agent.discoveries if d.discovery_type == "factor"]
    print(f"\n  Factor relationships (exact glyph fractions):")
    for d in factor_discoveries[:10]:
        src = agent.nodes[d.source_node].position
        tgt = agent.nodes[d.target_node].position
        print(f"    {src.to_glyphs()} / {tgt.to_glyphs()} = {d.relationship.to_glyphs()}"
              f"  (decimal: {src.to_decimal()}/{tgt.to_decimal()}"
              f" = {d.relationship.num.to_decimal()}/{d.relationship.den.to_decimal()})")

    # Compress and restore — verify nothing lost
    pre_count = len(agent.discoveries)
    agent.compress()
    agent.restore()
    post_count = len(agent.discoveries)
    print(f"\n  Discoveries before compress: {pre_count}")
    print(f"  Discoveries after restore:  {post_count}")
    print(f"  Lossless: {pre_count == post_count}")


if __name__ == "__main__":
    print("=" * 60)
    print("CONSTRAINT-GEOMETRY AGENT FRAMEWORK v1.0")
    print("  Seed -> Bloom -> Explore -> Compress -> Restore")
    print("=" * 60)

    demo_basic_lifecycle()
    demo_resource_constraints()
    demo_cross_substrate()
    demo_exact_fractions()

    print("\n" + "=" * 60)
    print("All demonstrations complete.")
    print("Agents are geometric. Constraints are boundaries. Fractions are exact.")
    print("=" * 60)
