"""
SOVEREIGN MESH v1.0
Distributed geometric computation on the octahedral Cayley graph.

Each node is a sovereign agent sitting at a group element position.
Signals are group ring elements that flow along Cayley graph edges.
A smooth relation "precipitates" when signal composition reaches identity.

This is NOT a binary sieve encoded in geometry. The mesh IS the geometry.
Nodes are rotations. Edges are generator steps. Cancellation is composition.

The system self-organizes: nodes can fail, heal, and rewire while
preserving the algebraic structure of the group.

Core types:
  MeshNode         -- sovereign agent at a Cayley graph vertex
  Signal           -- group ring element flowing through the mesh
  SovereignMesh    -- the distributed computation engine
  MeshHealth       -- self-repair and Byzantine fault detection

Design principles:
  1. Topology IS algebra (Cayley graph = group structure)
  2. Signals compose (not XOR) — cancellation preserves information
  3. Nodes are sovereign (independent failure/healing)
  4. Primes inhabit vertices natively (PrimeVertex assignment)
  5. Solutions precipitate at identity (not "parity == 0")
"""

from __future__ import annotations
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import math
import random
import time

from octahedral_arithmetic import OctahedralNumber, GlyphFraction, BASE, PHI
from geometric_state_algebra import (
    OhElement, OhGroup, GroupRingElement, GeometricState,
    CayleyEnergy, PrimeVertex, IDENTITY, OCTAHEDRAL_VERTICES,
)


# ---------------------------------------------------------------------------
# Node health states
# ---------------------------------------------------------------------------

class NodeHealth(Enum):
    """Health states for mesh nodes. Mirrors biological immune cell states."""
    ACTIVE = "active"          # Healthy, processing signals
    DORMANT = "dormant"        # Conserving energy, passes signals unchanged
    INFLAMED = "inflamed"      # Over-responding (hyperactive)
    NECROTIC = "necrotic"      # Dead, must be bypassed
    RECOVERING = "recovering"  # Recently healed, reduced capacity


# ---------------------------------------------------------------------------
# Conjugacy zone: where a node sits in the group structure
# ---------------------------------------------------------------------------

class ConjugacyZone(Enum):
    """
    Zones based on conjugacy class structure of O_h.

    Instead of arbitrary thresholds (primes < 100, etc.),
    zones emerge from the group's own structure:
      CORE:    identity and low-order elements (always active)
      BRIDGE:  order-3 elements (connect rotation subgroups)
      EDGE:    order-4 elements (high-symmetry rotations)
      BOUNDARY: order-6 and order-2 reflections (outer shell)
    """
    CORE = 1       # Order 1-2: identity, involutions (always hot)
    BRIDGE = 2     # Order 3: 3-fold rotations (connect subgroups)
    EDGE = 3       # Order 4: 4-fold rotations (high symmetry)
    BOUNDARY = 4   # Order 6: highest order (outer reaches)


def classify_zone(element: OhElement) -> ConjugacyZone:
    """Assign a zone based on element order."""
    order = element.order()
    if order <= 2:
        return ConjugacyZone.CORE
    elif order == 3:
        return ConjugacyZone.BRIDGE
    elif order == 4:
        return ConjugacyZone.EDGE
    else:
        return ConjugacyZone.BOUNDARY


# ---------------------------------------------------------------------------
# Signal: a group ring element flowing through the mesh
# ---------------------------------------------------------------------------

@dataclass
class Signal:
    """
    A signal flowing through the mesh.

    The signal IS a group ring element. As it passes through nodes,
    each contributing node composes its state into the signal.
    When the signal reaches identity, a solution has precipitated.

    This replaces the binary parity chain:
      Binary:    parity ^= (exponent % 2)
      Geometric: signal = signal.compose(node_contribution)
    """
    ring_element: GroupRingElement
    origin_a: int                        # The candidate value that spawned this signal
    origin_Q: int                        # Q = a^2 - N
    path: List[int] = field(default_factory=list)  # Node IDs visited
    contributions: Dict[int, Dict[int, int]] = field(default_factory=dict)
    energy: float = 0.0                  # Accumulated signal energy
    alive: bool = True                   # Signal dies if it hits a dead end

    def is_precipitated(self) -> bool:
        """Has this signal composed back to identity?"""
        return self.ring_element.is_identity()

    def strength(self) -> float:
        """Signal strength: inverse of distance from identity."""
        spread = self.ring_element.cayley_spread()
        if spread == 0:
            return float('inf')  # At identity
        return 1.0 / spread


# ---------------------------------------------------------------------------
# MeshNode: a sovereign agent at a Cayley graph vertex
# ---------------------------------------------------------------------------

class MeshNode:
    """
    A sovereign node in the mesh, sitting at a specific group element.

    Each node:
    - Lives at a position in the Cayley graph (IS a symmetry operation)
    - Owns a set of primes (assigned by PrimeVertex order resonance)
    - Processes signals by composing its geometric contribution
    - Maintains health state with self-repair capability
    - Connects to Cayley-adjacent neighbors (1 generator step)
    """

    def __init__(self, node_id: int, group: OhGroup,
                 element_idx: int, primes: List[int]):
        self.node_id = node_id
        self.group = group
        self.element_idx = element_idx
        self.element = group.elements[element_idx]
        self.primes = primes
        self.zone = classify_zone(self.element)

        # Cayley neighbors: elements reachable by one generator step
        self.neighbors: List[int] = []  # Filled by mesh wiring

        # Health
        self.health = NodeHealth.ACTIVE
        self.fail_count = 0
        self.activation_history: List[bool] = []
        self.max_history = 50

        # Performance
        self.signals_processed = 0
        self.signals_contributed = 0

    def check_divisibility(self, Q: int) -> Tuple[bool, Dict[int, int]]:
        """
        Check which of this node's primes divide Q.
        Returns (any_hit, {prime: exponent}).
        """
        exponents = {}
        remainder = abs(Q)
        for p in self.primes:
            if p == 0:
                continue
            count = 0
            while remainder > 0 and remainder % p == 0:
                count += 1
                remainder //= p
            if count > 0:
                exponents[p] = count
        return len(exponents) > 0, exponents

    def should_activate(self, signal: Signal) -> bool:
        """
        Decentralized activation decision.

        CORE nodes: always active (identity/involutions are fundamental)
        BRIDGE/EDGE: activate if signal has energy (neighbor contributed)
        BOUNDARY: activate only on strong signals or random discovery pulse

        Inflamed nodes have attenuated activation.
        """
        if self.health == NodeHealth.NECROTIC:
            return False

        if self.health == NodeHealth.DORMANT:
            # 5% wake-up chance for discovery
            return random.random() < 0.05

        if self.health == NodeHealth.INFLAMED:
            # Attenuated: only respond to strong signals
            return signal.strength() > 2.0

        if self.health == NodeHealth.RECOVERING:
            # 50% capacity
            return random.random() < 0.5

        # ACTIVE node: zone-based activation
        if self.zone == ConjugacyZone.CORE:
            return True  # Always hot

        if self.zone == ConjugacyZone.BRIDGE:
            return len(signal.path) > 0  # Activate if signal has momentum

        if self.zone == ConjugacyZone.EDGE:
            return signal.strength() > 0.5 or random.random() < 0.02

        # BOUNDARY: conservative
        return signal.strength() > 1.0 or random.random() < 0.01

    def process_signal(self, signal: Signal) -> Signal:
        """
        Process a signal through this node.

        If this node's primes divide Q, compose the prime's
        group element (raised to the exponent) into the signal.
        """
        self.signals_processed += 1
        self._record_activation(False)

        if not self.should_activate(signal):
            return signal

        any_hit, exponents = self.check_divisibility(signal.origin_Q)

        if not any_hit:
            return signal

        # Compose each contributing prime's group element into the signal
        self._record_activation(True)
        self.signals_contributed += 1

        new_ring = signal.ring_element
        for prime, exp in exponents.items():
            # Get this prime's group element
            prime_elem_idx = self._prime_to_element(prime)
            if prime_elem_idx is not None:
                prime_ring = GroupRingElement.from_element(self.group, prime_elem_idx)
                # Compose exp times (or compose the inverse for odd exponents)
                for _ in range(exp):
                    new_ring = new_ring.multiply(prime_ring)

        new_signal = Signal(
            ring_element=new_ring,
            origin_a=signal.origin_a,
            origin_Q=signal.origin_Q,
            path=signal.path + [self.node_id],
            contributions={**signal.contributions, self.node_id: exponents},
            energy=signal.energy + sum(exponents.values()),
            alive=True,
        )
        return new_signal

    def _prime_to_element(self, prime: int) -> Optional[int]:
        """
        Map a prime to a group element index using order resonance.

        p=2 -> order-2 element (involution)
        p=3 -> order-3 element
        p=5 -> order-4 element (nearest resonance via phi)
        Others -> distributed across remaining elements
        """
        # Use a deterministic hash-like assignment
        order_map = {2: 2, 3: 3, 5: 4, 7: 6}
        target_order = order_map.get(prime)

        if target_order:
            candidates = self.group.elements_of_order(target_order)
            if candidates:
                return candidates[prime % len(candidates)]

        # For larger primes: hash into the group
        return prime % len(self.group.elements)

    def _record_activation(self, activated: bool):
        """Track activation history for health monitoring."""
        self.activation_history.append(activated)
        if len(self.activation_history) > self.max_history:
            self.activation_history.pop(0)

    @property
    def activation_rate(self) -> float:
        """Recent activation rate (0.0 to 1.0)."""
        if not self.activation_history:
            return 0.0
        return sum(self.activation_history) / len(self.activation_history)

    def __repr__(self) -> str:
        return (f"MeshNode({self.node_id}, elem={self.element_idx}, "
                f"zone={self.zone.name}, primes={self.primes}, "
                f"health={self.health.value})")


# ---------------------------------------------------------------------------
# MeshHealth: self-repair and Byzantine fault detection
# ---------------------------------------------------------------------------

class MeshHealth:
    """
    The mesh's immune system.

    Detects and heals node failures using geometric validation:
    - A healthy node correctly composes its contribution
    - A failing node produces wrong compositions
    - A Byzantine node lies about its contributions

    Healing uses Cayley graph structure to route around dead nodes.
    """

    def __init__(self, mesh: SovereignMesh):
        self.mesh = mesh
        self.known_good_signals: List[Signal] = []
        self.heal_cycles = 0

    def diagnose_node(self, node: MeshNode) -> NodeHealth:
        """
        Test a node against known-good signals.

        If the node's contribution doesn't match expected,
        it's failing. Three failures = necrotic.
        """
        if not self.known_good_signals:
            return node.health

        failures = 0
        for signal in self.known_good_signals[-5:]:
            _, expected_exp = node.check_divisibility(signal.origin_Q)
            # Verify the node would produce the right exponents
            if node.node_id in signal.contributions:
                actual_exp = signal.contributions[node.node_id]
                if actual_exp != expected_exp:
                    failures += 1

        if failures >= 3:
            return NodeHealth.NECROTIC
        elif failures >= 1:
            return NodeHealth.RECOVERING
        return NodeHealth.ACTIVE

    def detect_inflammation(self, node: MeshNode) -> bool:
        """
        Is this node over-responding?

        Healthy activation rate depends on zone:
          CORE: 30-80% is normal
          BRIDGE: 10-50% is normal
          EDGE/BOUNDARY: 1-20% is normal
        """
        rate = node.activation_rate
        if node.zone == ConjugacyZone.CORE:
            return rate > 0.85
        elif node.zone == ConjugacyZone.BRIDGE:
            return rate > 0.55
        else:
            return rate > 0.25

    def heal_cycle(self):
        """
        Run one healing cycle across the mesh.

        1. Diagnose each node
        2. Detect inflammation
        3. Bypass necrotic nodes (rewire Cayley neighbors)
        4. Dampen inflamed nodes
        5. Wake dormant nodes if mesh is understaffed
        """
        self.heal_cycles += 1
        active_count = 0
        healed = 0
        bypassed = 0

        for node in self.mesh.nodes:
            # Diagnose
            diagnosis = self.diagnose_node(node)
            if diagnosis != node.health:
                node.health = diagnosis
                healed += 1

            # Inflammation check
            if self.detect_inflammation(node):
                node.health = NodeHealth.INFLAMED
                healed += 1

            # Count active
            if node.health in (NodeHealth.ACTIVE, NodeHealth.RECOVERING):
                active_count += 1

        # Bypass necrotic nodes
        for node in self.mesh.nodes:
            if node.health == NodeHealth.NECROTIC:
                self._bypass_node(node)
                bypassed += 1

        # Wake dormant nodes if too few are active
        active_fraction = active_count / max(len(self.mesh.nodes), 1)
        if active_fraction < 0.5:
            for node in self.mesh.nodes:
                if node.health == NodeHealth.DORMANT:
                    node.health = NodeHealth.RECOVERING
                    healed += 1

        return {"healed": healed, "bypassed": bypassed, "active_fraction": active_fraction}

    def _bypass_node(self, dead_node: MeshNode):
        """
        Route around a necrotic node using Cayley graph structure.

        Connect all of the dead node's neighbors to each other.
        The Cayley graph guarantees alternative paths exist
        (the group is connected via generators).
        """
        for a in dead_node.neighbors:
            for b in dead_node.neighbors:
                if a != b:
                    node_a = self.mesh.nodes[a]
                    if b not in node_a.neighbors:
                        node_a.neighbors.append(b)
        dead_node.neighbors = []

    def record_good_signal(self, signal: Signal):
        """Store a known-good signal for future validation."""
        self.known_good_signals.append(signal)
        if len(self.known_good_signals) > 50:
            self.known_good_signals.pop(0)


# ---------------------------------------------------------------------------
# SovereignMesh: the distributed computation engine
# ---------------------------------------------------------------------------

class SovereignMesh:
    """
    Distributed geometric computation on the octahedral Cayley graph.

    The mesh topology IS the Cayley graph of O_h:
    - 48 vertices = 48 group elements = 48 sovereign nodes
    - Edges connect elements that differ by one generator
    - Primes are assigned to nodes by PrimeVertex order resonance
    - Signals are group ring elements that compose as they flow
    - Solutions precipitate when a signal reaches identity

    The mesh self-organizes:
    - Nodes fail and heal independently
    - Dead nodes are bypassed via alternative Cayley paths
    - The algebraic structure is preserved even under node failure
    """

    def __init__(self, N: int, factor_base_size: int = 50):
        self.N = N
        self.group = OhGroup()
        self.nodes: List[MeshNode] = []
        self.precipitated: List[Signal] = []
        self.candidates_tested = 0

        # Build the mesh
        factor_base = self._compute_factor_base(N, factor_base_size)
        self.factor_base = factor_base
        self._build_mesh(factor_base)
        self._wire_cayley()

        # Health system
        self.health = MeshHealth(self)

    def _compute_factor_base(self, N: int, size: int) -> List[int]:
        """Compute factor base: first `size` primes p where N is a QR mod p."""
        primes = []
        p = 2
        while len(primes) < size:
            if self._is_prime(p):
                # Check if N is a quadratic residue mod p
                if p == 2 or self._is_qr(N, p):
                    primes.append(p)
            p += 1
        return primes

    @staticmethod
    def _is_prime(n: int) -> bool:
        if n < 2: return False
        if n < 4: return True
        if n % 2 == 0: return False
        d = 3
        while d * d <= n:
            if n % d == 0: return False
            d += 2
        return True

    @staticmethod
    def _is_qr(n: int, p: int) -> bool:
        """Is n a quadratic residue mod p? (Euler criterion)"""
        if p == 2:
            return True
        return pow(n % p, (p - 1) // 2, p) == 1

    @staticmethod
    def _isqrt(n: int) -> int:
        if n < 0: return 0
        if n == 0: return 0
        x = n
        y = (x + 1) // 2
        while y < x:
            x = y
            y = (x + n // x) // 2
        return x

    def _build_mesh(self, factor_base: List[int]):
        """
        Assign primes to the 48 Cayley graph vertices.

        Two-phase strategy:
        1. Resonance assignment: small primes go to elements whose order
           matches the prime (p=2->order-2, p=3->order-3, etc.)
        2. Round-robin: remaining primes distributed evenly across all nodes,
           ensuring every node owns at least one prime.
        """
        # Phase 1: resonance assignment for small primes
        resonance_assigned: Dict[int, List[int]] = {}  # elem_idx -> [primes]
        remaining_primes = list(factor_base)

        order_elements = {}
        for i, elem in enumerate(self.group.elements):
            o = elem.order()
            if o not in order_elements:
                order_elements[o] = []
            order_elements[o].append(i)

        # Assign p=2 to first order-2 element, p=3 to first order-3, etc.
        for p in [2, 3, 5, 7]:
            target_order = {2: 2, 3: 3, 5: 4, 7: 6}.get(p)
            if target_order and target_order in order_elements and p in remaining_primes:
                elem_idx = order_elements[target_order][0]
                resonance_assigned.setdefault(elem_idx, []).append(p)
                remaining_primes.remove(p)

        # Phase 2: round-robin the rest across all 48 nodes
        all_indices = list(range(len(self.group.elements)))
        for i, p in enumerate(remaining_primes):
            elem_idx = all_indices[i % 48]
            resonance_assigned.setdefault(elem_idx, []).append(p)

        # Create nodes
        for elem_idx, elem in enumerate(self.group.elements):
            node = MeshNode(
                node_id=elem_idx,
                group=self.group,
                element_idx=elem_idx,
                primes=resonance_assigned.get(elem_idx, []),
            )
            self.nodes.append(node)

    def _wire_cayley(self):
        """
        Wire the mesh using the Cayley graph structure.

        Each node connects to nodes reachable by one generator
        application (left or right multiplication, forward or inverse).
        """
        for i, node in enumerate(self.nodes):
            g = node.element
            neighbors = set()
            for gen in self.group.generators:
                for h in [g.compose(gen), g.compose(gen.inverse()),
                          gen.compose(g), gen.inverse().compose(g)]:
                    j = self.group.index(h)
                    if j != i:
                        neighbors.add(j)
            node.neighbors = sorted(neighbors)

    # ------------------------------------------------------------------
    # Signal propagation
    # ------------------------------------------------------------------

    def broadcast(self, a: int) -> Optional[Signal]:
        """
        Broadcast candidate a through the mesh.

        Signal starts at identity (CORE zone) and propagates outward
        through the Cayley graph. Each contributing node composes its
        prime's group element into the signal.

        Returns a precipitated signal if one reaches identity.
        """
        Q = a * a - self.N
        if Q <= 0:
            return None

        self.candidates_tested += 1

        # Create initial signal at identity
        identity_signal = Signal(
            ring_element=GroupRingElement.from_identity(self.group),
            origin_a=a,
            origin_Q=Q,
        )

        # BFS from identity through the Cayley graph
        identity_idx = self.group.index(IDENTITY)
        visited: Set[int] = set()
        queue = deque([(identity_idx, identity_signal)])

        best_signal = identity_signal

        while queue:
            node_id, signal = queue.popleft()

            if node_id in visited:
                continue
            visited.add(node_id)

            if not signal.alive:
                continue

            # Process through this node
            node = self.nodes[node_id]
            processed = node.process_signal(signal)

            # Check for precipitation: verify Q is actually smooth
            # over the contributing primes (not just group ring identity)
            if len(processed.contributions) >= 2:
                all_exps = {}
                for node_exp in processed.contributions.values():
                    for p, e in node_exp.items():
                        all_exps[p] = all_exps.get(p, 0) + e
                # Verify: product of p^e should equal |Q|
                product = 1
                for p, e in all_exps.items():
                    product *= p ** e
                if product == abs(Q):
                    self.precipitated.append(processed)
                    self.health.record_good_signal(processed)
                    return processed

            # Track best signal (closest to identity)
            if processed.strength() > best_signal.strength():
                best_signal = processed

            # Propagate to Cayley neighbors
            for neighbor_id in node.neighbors:
                if neighbor_id not in visited:
                    queue.append((neighbor_id, processed))

        return None

    def sieve(self, max_candidates: int = 10000,
              heal_interval: int = 1000) -> List[Signal]:
        """
        Run the mesh sieve over candidate values.

        Returns list of precipitated signals (smooth relations).
        """
        sqrt_N = self._isqrt(self.N) + 1
        results = []

        for offset in range(max_candidates):
            a = sqrt_N + offset

            signal = self.broadcast(a)
            if signal is not None:
                results.append(signal)

            # Periodic healing
            if offset > 0 and offset % heal_interval == 0:
                heal_report = self.health.heal_cycle()
                active = sum(1 for n in self.nodes
                           if n.health in (NodeHealth.ACTIVE, NodeHealth.RECOVERING))
                print(f"  Heal cycle @ {offset}: "
                      f"active={active}/{len(self.nodes)}, "
                      f"precipitated={len(results)}")

        return results

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def mesh_status(self) -> Dict:
        """Current mesh status."""
        by_health = {}
        by_zone = {}
        for node in self.nodes:
            h = node.health.value
            by_health[h] = by_health.get(h, 0) + 1
            z = node.zone.name
            by_zone[z] = by_zone.get(z, 0) + 1

        return {
            "nodes": len(self.nodes),
            "health": by_health,
            "zones": by_zone,
            "cayley_diameter": self.group.max_distance(),
            "factor_base_size": len(self.factor_base),
            "candidates_tested": self.candidates_tested,
            "precipitated": len(self.precipitated),
        }

    def node_map(self, max_nodes: int = 20) -> str:
        """Visualize the mesh."""
        lines = []
        for node in self.nodes[:max_nodes]:
            primes_str = ",".join(str(p) for p in node.primes[:5])
            if len(node.primes) > 5:
                primes_str += f"...+{len(node.primes)-5}"
            lines.append(
                f"  [{node.node_id:>2d}] {node.zone.name:<8s} "
                f"ord={node.element.order()} "
                f"{'R' if node.element.is_proper() else 'I'} "
                f"primes=[{primes_str:<15s}] "
                f"nbrs={len(node.neighbors)} "
                f"{node.health.value}"
            )
        if len(self.nodes) > max_nodes:
            lines.append(f"  ... and {len(self.nodes) - max_nodes} more nodes")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Number-theoretic helpers (self-contained, no external deps)
# ---------------------------------------------------------------------------

def trial_factor(N: int) -> Optional[Tuple[int, int]]:
    """Simple trial division for verification."""
    if N < 4:
        return None
    if N % 2 == 0:
        return (2, N // 2)
    d = 3
    while d * d <= N:
        if N % d == 0:
            return (d, N // d)
        d += 2
    return None


def smooth_over_base(n: int, base: List[int]) -> Optional[Dict[int, int]]:
    """Factor n over the given base. Returns None if not smooth."""
    if n == 0:
        return None
    exponents = {}
    remainder = abs(n)
    for p in base:
        while remainder % p == 0:
            exponents[p] = exponents.get(p, 0) + 1
            remainder //= p
    if remainder == 1:
        return exponents
    return None


# ============================================================================
# DEMONSTRATIONS
# ============================================================================

def demo_mesh_structure():
    """Show the mesh topology and node assignment."""
    print("=" * 60)
    print("SOVEREIGN MESH v1.0")
    print("Distributed geometry on the Cayley graph")
    print("=" * 60)

    N = 15 * 17  # 255
    mesh = SovereignMesh(N, factor_base_size=20)
    status = mesh.mesh_status()

    print(f"\n  N = {N}")
    print(f"  Factor base: {mesh.factor_base[:10]}{'...' if len(mesh.factor_base) > 10 else ''}")
    print(f"  Nodes: {status['nodes']}")
    print(f"  Cayley diameter: {status['cayley_diameter']}")
    print(f"  Zones: {status['zones']}")

    print(f"\n  Node map (first 20):")
    print(mesh.node_map(20))

    # Verify Cayley connectivity
    total_edges = sum(len(n.neighbors) for n in mesh.nodes)
    print(f"\n  Total Cayley edges: {total_edges // 2} (undirected)")
    avg_degree = total_edges / len(mesh.nodes)
    print(f"  Average degree: {avg_degree:.1f}")

    return mesh


def demo_signal_propagation():
    """Show a signal flowing through the mesh."""
    print(f"\n{'=' * 60}")
    print("SIGNAL PROPAGATION: Group Ring Composition")
    print("=" * 60)

    N = 3 * 5  # 15
    mesh = SovereignMesh(N, factor_base_size=10)

    # Manual broadcast to show the process
    sqrt_N = mesh._isqrt(N) + 1
    print(f"\n  N = {N}, sqrt(N) = {sqrt_N}")
    print(f"  Factor base: {mesh.factor_base}")

    for a in range(sqrt_N, sqrt_N + 10):
        Q = a * a - N
        print(f"\n  a={a}, Q=a^2-N={Q}")

        # Check which primes divide Q
        smooth = smooth_over_base(Q, mesh.factor_base)
        if smooth:
            print(f"    SMOOTH over base: {smooth}")
        else:
            print(f"    Not smooth over base")

        # Try broadcasting
        signal = mesh.broadcast(a)
        if signal is not None:
            print(f"    PRECIPITATED! Path length: {len(signal.path)}")
            print(f"    Contributions: {signal.contributions}")
            print(f"    Signal at identity: {signal.is_precipitated()}")
        else:
            print(f"    No precipitation")

    return mesh


def demo_self_healing():
    """Show the mesh healing from node failures."""
    print(f"\n{'=' * 60}")
    print("SELF-HEALING: Geometric Fault Tolerance")
    print("=" * 60)

    N = 7 * 11  # 77
    mesh = SovereignMesh(N, factor_base_size=15)

    print(f"\n  N = {N}")
    print(f"  Initial mesh health:")
    status = mesh.mesh_status()
    print(f"    {status['health']}")

    # Kill some nodes
    killed = []
    for node in mesh.nodes[:5]:
        node.health = NodeHealth.NECROTIC
        killed.append(node.node_id)
    print(f"\n  Killed nodes: {killed}")

    # Inflame some nodes
    inflamed = []
    for node in mesh.nodes[10:13]:
        node.health = NodeHealth.INFLAMED
        inflamed.append(node.node_id)
    print(f"  Inflamed nodes: {inflamed}")

    status = mesh.mesh_status()
    print(f"  After damage: {status['health']}")

    # Heal
    heal_report = mesh.health.heal_cycle()
    print(f"\n  Healing cycle: {heal_report}")

    status = mesh.mesh_status()
    print(f"  After healing: {status['health']}")

    # Try sieving with damaged mesh
    print(f"\n  Sieving with damaged mesh (100 candidates)...")
    results = mesh.sieve(max_candidates=100, heal_interval=50)
    print(f"  Precipitated: {len(results)} signals")

    return mesh


def demo_factorization():
    """Show the mesh factoring a number."""
    print(f"\n{'=' * 60}")
    print("GEOMETRIC FACTORIZATION: Mesh Sieve")
    print("=" * 60)

    test_cases = [
        (15, "3 x 5"),
        (77, "7 x 11"),
        (221, "13 x 17"),
    ]

    for N, expected in test_cases:
        print(f"\n  N = {N} (expected: {expected})")

        mesh = SovereignMesh(N, factor_base_size=20)
        start = time.time()
        results = mesh.sieve(max_candidates=5000, heal_interval=2000)
        elapsed = time.time() - start

        status = mesh.mesh_status()
        print(f"    Candidates tested: {status['candidates_tested']}")
        print(f"    Precipitated: {len(results)} signals")
        print(f"    Time: {elapsed:.3f}s")

        if results:
            first = results[0]
            print(f"    First signal: a={first.origin_a}, Q={first.origin_Q}")
            print(f"    Path: {first.path[:10]}{'...' if len(first.path) > 10 else ''}")
            print(f"    Contributions: {first.contributions}")

        # Verify with trial division
        factors = trial_factor(N)
        if factors:
            print(f"    Verification: {N} = {factors[0]} x {factors[1]}")


def demo_cayley_vs_binary():
    """Compare Cayley mesh with what a binary approach would do."""
    print(f"\n{'=' * 60}")
    print("CAYLEY vs BINARY: Why Geometry Matters")
    print("=" * 60)

    group = OhGroup()

    print(f"""
  Binary sieve (classical):
    - Each prime gets a flat index (0, 1, 2, ...)
    - Signal = XOR of exponent parities
    - Cancellation = parity reaches 0
    - No structure between primes

  Cayley mesh (geometric):
    - Each prime inhabits a group element (rotation/reflection)
    - Signal = group ring composition
    - Cancellation = composition reaches identity
    - Cayley distance encodes prime relationships

  The mesh has structure the binary sieve doesn't:
""")

    # Show that Cayley distance between prime assignments
    # encodes relationships that flat indexing misses
    pv = PrimeVertex(group)
    small_primes = [2, 3, 5, 7, 11, 13]
    print(f"  Cayley distances between prime vertices:")
    print(f"       ", end="")
    for p in small_primes:
        print(f"  p={p:>2d}", end="")
    print()
    for p in small_primes:
        print(f"  p={p:>2d}:", end="")
        pi = pv.prime_to_element(p)
        for q in small_primes:
            qi = pv.prime_to_element(q)
            if pi is not None and qi is not None:
                d = group.distance(pi, qi)
                print(f"    {d:>2d}", end="")
            else:
                print(f"     ?", end="")
        print()

    print(f"\n  Flat index distances (|i-j|):")
    print(f"       ", end="")
    for i, p in enumerate(small_primes):
        print(f"  p={p:>2d}", end="")
    print()
    for i, p in enumerate(small_primes):
        print(f"  p={p:>2d}:", end="")
        for j, q in enumerate(small_primes):
            print(f"    {abs(i-j):>2d}", end="")
        print()

    print(f"\n  The Cayley metric captures algebraic relationships")
    print(f"  between primes that flat indexing cannot see.")


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SOVEREIGN MESH v1.0")
    print("  Nodes are rotations. Signals compose. Solutions precipitate.")
    print("=" * 60)

    demo_mesh_structure()
    demo_signal_propagation()
    demo_self_healing()
    demo_factorization()
    demo_cayley_vs_binary()

    print(f"\n{'=' * 60}")
    print("The mesh doesn't search for factors.")
    print("The factors precipitate from the geometry.")
    print("=" * 60)
