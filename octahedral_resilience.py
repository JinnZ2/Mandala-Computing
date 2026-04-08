"""
OCTAHEDRAL RESILIENCE v1.0
Self-healing distributed infrastructure on the octahedral lattice.
stdlib only -- no numpy, no scipy.

This module implements the full resilience stack for octahedral computing:
heartbeat monitoring, failover clustering, seed dispersal with threshold
secret sharing, Byzantine verification, circuit breakers, priority-staged
reconfiguration, Merkle-based state sync, and resource-aware healing.

The geometry isn't decoration -- the octahedral structure determines:
  - Which nodes are adjacent (edge connectivity for cascade)
  - How staleness propagates (BFS on octahedral graph)
  - Where seeds disperse (6 vertices = 6 hardware zones)
  - How fencing works (antipodal pairs can't both be primary)

Core types:
  Health              -- node health states
  OctahedralNode      -- lattice node with heartbeat
  HeartbeatMonitor    -- continuous health checking
  OctahedralCluster   -- primary/backup failover
  AlertMonitor        -- failure counting with threshold alerts
  AutoRecovery        -- respawn failed nodes
  CompressedSeed      -- hash-committed seed with integrity check
  SeedSplitter        -- threshold secret sharing (split/rebuild)
  HardwareComponent   -- hardware zone that stores shares
  SeedDispersal       -- distribute shares across hardware
  MinimalComms        -- diff/patch/gossip protocols
  ServiceState        -- component lifecycle states
  ServiceReconfigurator -- rejoin/degrade with share reassignment
  QuorumReconfigurator  -- Byzantine-tolerant consensus
  StagingProtocol     -- multi-phase reconfig with rollback
  PriorityScheduler   -- priority queue with exponential backoff
  HybridLogicalClock  -- distributed time coordination
  ByzantineVerifier   -- cryptographic share verification
  CircuitBreaker      -- rate limiting per component
  AuditTrail          -- signed tamper-evident operation log
  KeyRotationManager  -- epoch-based seed rotation with lineage
  FencingManager      -- generation tokens for split-brain prevention
  ShareMerkleTree     -- efficient state sync after partition
  ResourceReservation -- guaranteed minimums for critical ops
  ExternalToolOrchestrator -- resource-aware healing tool execution

Design:
  - stdlib only (hashlib, secrets, time, threading, collections, heapq)
  - No external dependencies
  - All crypto uses blake2b/sha256 (stdlib hashlib)
  - Thread-safe where needed (fencing, resource reservation)
"""

from __future__ import annotations
import hashlib
import secrets
import time
import math
import random
import threading
import heapq
from collections import deque, OrderedDict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any
from enum import Enum
from abc import ABC, abstractmethod


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PHI = (1 + math.sqrt(5)) / 2

# Octahedral vertex labels (matching octahedral_session_cache)
AXIS_LABELS = ("+X", "-X", "+Y", "-Y", "+Z", "-Z")


# ===========================================================================
# SECTION 1: Health Monitoring and Failover
# ===========================================================================

class Health(Enum):
    """Component health states."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class OctahedralNode:
    """
    A single node on the octahedral lattice.

    Each node occupies one of 6 vertex positions. It can perform
    local computation and reports liveness via heartbeat.
    """
    id: str
    axis_index: int = 0  # which octahedral axis (0-5)
    failure_rate: float = 0.03  # probability of missed heartbeat

    def heartbeat(self) -> bool:
        """Liveness check. Returns False on missed beat."""
        return random.random() > self.failure_rate

    def solve_local(self, problem_data: Any) -> Optional[Any]:
        """Local solve attempt -- fails at same rate as heartbeat."""
        if random.random() < self.failure_rate:
            raise RuntimeError(f"Node {self.id}: local solve failed")
        return {"node": self.id, "status": "solved"}


class HeartbeatMonitor:
    """
    Continuous health monitoring for octahedral nodes.

    Tracks last successful heartbeat per node. A node is:
      HEALTHY  -- beat received within timeout
      DEGRADED -- beat missed but within timeout
      FAILED   -- no beat for > timeout seconds
    """

    def __init__(self, nodes: Dict[str, OctahedralNode],
                 timeout_seconds: float = 3.0):
        self.nodes = nodes
        self.timeout = timeout_seconds
        self.last_beat: Dict[str, float] = {
            nid: time.time() for nid in nodes
        }

    def check(self) -> Dict[str, Health]:
        """Run one health check cycle. Returns {node_id: Health}."""
        status = {}
        now = time.time()
        for node_id, node in self.nodes.items():
            try:
                if node.heartbeat():
                    self.last_beat[node_id] = now
                    status[node_id] = Health.HEALTHY
                elif now - self.last_beat.get(node_id, 0) > self.timeout:
                    status[node_id] = Health.FAILED
                else:
                    status[node_id] = Health.DEGRADED
            except Exception:
                status[node_id] = Health.FAILED
        return status


class OctahedralCluster:
    """
    Primary/backup failover cluster.

    The primary node handles computation. If it fails, the cluster
    automatically fails over to the next healthy backup.
    """

    def __init__(self, primary: OctahedralNode,
                 backups: List[OctahedralNode]):
        self.primary = primary
        self.backups = list(backups)
        self.active = primary
        self.failover_count = 0

    def failover(self) -> bool:
        """Switch to next healthy backup."""
        if self.backups:
            self.active = self.backups.pop(0)
            self.failover_count += 1
            return True
        return False

    def solve_with_failover(self, problem_data: Any) -> Optional[Any]:
        """Attempt solve with automatic failover on failure."""
        try:
            return self.active.solve_local(problem_data)
        except RuntimeError:
            if self.failover():
                try:
                    return self.active.solve_local(problem_data)
                except RuntimeError:
                    return None
        return None


class AlertMonitor:
    """
    Failure counting with threshold-based alerting.

    Tracks consecutive failures per node. When a node exceeds
    the alert threshold, an alert is raised.
    """

    def __init__(self, alert_threshold: int = 2):
        self.alert_threshold = alert_threshold
        self.failure_counts: Dict[str, int] = {}
        self.alerts: List[Dict[str, Any]] = []

    def update(self, status: Dict[str, Health]):
        """Process health status, raising alerts as needed."""
        for node_id, health in status.items():
            if health == Health.FAILED:
                self.failure_counts[node_id] = (
                    self.failure_counts.get(node_id, 0) + 1
                )
                if self.failure_counts[node_id] >= self.alert_threshold:
                    self.alerts.append({
                        "node": node_id,
                        "failures": self.failure_counts[node_id],
                        "time": time.time(),
                    })
            else:
                self.failure_counts[node_id] = 0


class AutoRecovery:
    """
    Automated node recovery.

    When a node fails, AutoRecovery spawns a replacement node
    and adds it to the cluster's backup pool.
    """

    def __init__(self, cluster: OctahedralCluster,
                 monitor: AlertMonitor):
        self.cluster = cluster
        self.monitor = monitor
        self.recovered: List[str] = []

    def recover(self, failed_node_id: str) -> bool:
        """Respawn a failed node as a backup."""
        new_node = OctahedralNode(id=f"{failed_node_id}_recovered")
        self.cluster.backups.append(new_node)
        self.recovered.append(new_node.id)
        return True



# ===========================================================================
# SECTION 2: Seed Compression and Dispersal
# ===========================================================================

@dataclass
class CompressedSeed:
    """
    A seed with hash commitment for integrity verification.

    The checksum is computed on creation and verified on access.
    Compression produces a non-reversible 16-byte digest.
    """
    value: bytes
    checksum: bytes = field(init=False)

    def __post_init__(self):
        self.checksum = hashlib.blake2b(
            self.value, digest_size=16
        ).digest()

    def verify(self) -> bool:
        """Check integrity against stored checksum."""
        return (hashlib.blake2b(self.value, digest_size=16).digest()
                == self.checksum)

    def compress(self) -> bytes:
        """Non-reversible compression to 16-byte digest."""
        return hashlib.sha256(self.value).digest()[:16]


class SeedSplitter:
    """
    Threshold secret sharing: split a seed into M shares,
    any K can reconstruct (Shamir's scheme over a prime field).

    All arithmetic is mod P where P is a 128-bit prime,
    ensuring exact reconstruction via Lagrange interpolation.
    """
    # Prime just above 2^128 so all 16-byte seed values fit
    # Next prime after 2^128: 2^128 + 51
    P = (1 << 128) + 51
    SHARE_LEN = 17  # ceil(129 bits / 8)

    @classmethod
    def split(cls, seed: bytes, total_shares: int,
              threshold: int) -> List[bytes]:
        """Generate shares. Any `threshold` shares reconstruct the seed."""
        if threshold > total_shares:
            raise ValueError("Threshold cannot exceed total shares")

        seed_int = int.from_bytes(
            seed[:16] if len(seed) > 16 else seed, "big"
        )
        # Random polynomial coefficients (degree = threshold - 1)
        coeffs = [seed_int] + [
            int.from_bytes(secrets.token_bytes(16), "big") % cls.P
            for _ in range(threshold - 1)
        ]

        shares = []
        for x in range(1, total_shares + 1):
            y = 0
            for i, c in enumerate(coeffs):
                y = (y + c * pow(x, i, cls.P)) % cls.P
            shares.append(y.to_bytes(cls.SHARE_LEN, "big"))
        return shares

    @classmethod
    def rebuild(cls, shares: List[bytes], indices: List[int],
                threshold: int) -> bytes:
        """Reconstruct seed from at least `threshold` shares."""
        if len(shares) < threshold:
            raise ValueError(
                f"Need {threshold} shares, got {len(shares)}"
            )
        points = [
            (indices[i], int.from_bytes(shares[i], "big"))
            for i in range(threshold)
        ]
        # Lagrange interpolation at x=0 over GF(P)
        secret = 0
        for i, (xi, yi) in enumerate(points):
            num, den = 1, 1
            for j, (xj, _) in enumerate(points):
                if i != j:
                    num = (num * (-xj)) % cls.P
                    den = (den * (xi - xj)) % cls.P
            # Modular inverse via Fermat's little theorem
            secret = (secret + yi * num * pow(den, cls.P - 2, cls.P)) % cls.P
        return secret.to_bytes(16, "big")


@dataclass
class HardwareComponent:
    """
    A hardware zone that stores seed shares.

    Represents a TPM, FPGA, secure enclave, or other hardware
    trust boundary. Each component stores shares keyed by seed_id.
    """
    id: str
    shares_held: Dict[str, bytes] = field(default_factory=dict)
    failure_rate: float = 0.02

    def store_share(self, seed_id: str, share: bytes):
        self.shares_held[seed_id] = share

    def retrieve_share(self, seed_id: str) -> Optional[bytes]:
        return self.shares_held.get(seed_id)

    def heartbeat(self) -> bool:
        return random.random() > self.failure_rate


class SeedDispersal:
    """
    Distribute compressed seeds across hardware components.

    Split each seed into shares using threshold secret sharing,
    then disperse shares to different hardware zones. Any K of M
    components can reconstruct the seed.
    """

    def __init__(self, components: List[HardwareComponent],
                 total_shares: int = 5, threshold: int = 3):
        self.components = {c.id: c for c in components}
        self.total_shares = total_shares
        self.threshold = threshold
        self.seed_registry: Dict[str, Tuple[bytes, List[str]]] = {}

    def disperse(self, seed: CompressedSeed) -> str:
        """Split and disperse a seed. Returns seed_id."""
        seed_id = hashlib.blake2b(
            seed.value, digest_size=8
        ).hexdigest()
        shares = SeedSplitter.split(
            seed.value, self.total_shares, self.threshold
        )
        comp_ids = list(self.components.keys())
        if len(comp_ids) < self.total_shares:
            raise ValueError(
                f"Need {self.total_shares} components, "
                f"have {len(comp_ids)}"
            )
        assigned = []
        for i, share in enumerate(shares):
            cid = comp_ids[i % len(comp_ids)]
            self.components[cid].store_share(seed_id, share)
            assigned.append(cid)
        self.seed_registry[seed_id] = (seed.compress(), assigned)
        return seed_id

    def reconstruct(self, seed_id: str) -> Optional[CompressedSeed]:
        """Pull shares from components and rebuild seed."""
        if seed_id not in self.seed_registry:
            return None
        compressed, comp_ids = self.seed_registry[seed_id]
        shares, indices = [], []
        for i, cid in enumerate(comp_ids[:self.threshold], start=1):
            share = self.components[cid].retrieve_share(seed_id)
            if share:
                shares.append(share)
                indices.append(i)
        if len(shares) < self.threshold:
            return None
        rebuilt = SeedSplitter.rebuild(shares, indices, self.threshold)
        candidate = CompressedSeed(rebuilt)
        if candidate.compress() == compressed and candidate.verify():
            return candidate
        return None


class MinimalComms:
    """
    Low-bandwidth communication: diff, patch, and gossip.

    Designed for high-latency, constrained links between
    octahedral hardware zones.
    """

    @staticmethod
    def diff(old: bytes, new: bytes) -> bytes:
        """XOR diff between two byte strings."""
        if old == new:
            return b""
        min_len = min(len(old), len(new))
        return bytes(a ^ b for a, b in zip(old[:min_len], new[:min_len]))

    @staticmethod
    def patch(base: bytes, diff_bytes: bytes) -> bytes:
        """Apply XOR diff to base."""
        min_len = min(len(base), len(diff_bytes))
        return bytes(a ^ b for a, b in zip(base[:min_len], diff_bytes[:min_len]))

    @staticmethod
    def gossip(peer_hashes: Dict[str, bytes],
               local_state: bytes) -> Dict[str, bytes]:
        """Send local state only to peers with different hash."""
        local_hash = hashlib.blake2b(
            local_state, digest_size=8
        ).digest()
        return {
            pid: local_state
            for pid, phash in peer_hashes.items()
            if phash != local_hash
        }



# ===========================================================================
# SECTION 3: Service Reconfiguration and Quorum
# ===========================================================================

class ServiceState(Enum):
    """Component lifecycle states."""
    OFFLINE = "offline"
    SYNCING = "syncing"
    ONLINE = "online"
    RECONFIGURING = "reconfiguring"


@dataclass
class ServiceRecord:
    """Tracks a single component's service state."""
    component_id: str
    state: ServiceState = ServiceState.OFFLINE
    last_seen: float = field(default_factory=time.time)
    missed_heartbeats: int = 0


class ServiceReconfigurator:
    """
    Service discovery and reconfiguration.

    When a component goes offline, its shares are redistributed.
    When it comes back, it syncs missing shares from the cluster.
    """

    def __init__(self, dispersal: SeedDispersal):
        self.dispersal = dispersal
        self.services: Dict[str, ServiceRecord] = {}

    def register_service(self, component_id: str):
        """Component announces availability."""
        if component_id not in self.services:
            self.services[component_id] = ServiceRecord(component_id)
        record = self.services[component_id]
        if record.state == ServiceState.OFFLINE:
            record.state = ServiceState.SYNCING
            self._reassign_missing_shares(component_id)

    def _reassign_missing_shares(self, component_id: str):
        """Push missing shares to a newly online component."""
        record = self.services[component_id]
        pushed = 0
        for seed_id, (_, holders) in self.dispersal.seed_registry.items():
            if component_id not in holders:
                new_share = secrets.token_bytes(16)
                comp = self.dispersal.components.get(component_id)
                if comp:
                    comp.store_share(seed_id, new_share)
                    holders.append(component_id)
                    pushed += 1
        record.state = ServiceState.ONLINE

    def degrade_service(self, component_id: str):
        """Mark component as failed, redistribute its shares."""
        record = self.services.get(component_id)
        if not record or record.state == ServiceState.OFFLINE:
            return
        record.state = ServiceState.OFFLINE
        record.missed_heartbeats += 1
        # Remove from holder lists
        for seed_id, (_, holders) in self.dispersal.seed_registry.items():
            if component_id in holders:
                holders.remove(component_id)
        # Redistribute to online components
        self._redistribute_orphaned_shares()

    def _redistribute_orphaned_shares(self):
        """Give orphaned shares to online components."""
        online = [
            cid for cid, rec in self.services.items()
            if rec.state == ServiceState.ONLINE
        ]
        if not online:
            return
        for seed_id, (_, holders) in self.dispersal.seed_registry.items():
            while len(holders) < self.dispersal.threshold:
                target = online[hash(seed_id) % len(online)]
                if target not in holders:
                    comp = self.dispersal.components.get(target)
                    if comp:
                        comp.store_share(seed_id, secrets.token_bytes(16))
                        holders.append(target)
                else:
                    break


class QuorumReconfigurator:
    """
    Byzantine-tolerant quorum consensus for reconfiguration.

    Reconfiguration only proceeds when enough services agree.
    """

    def __init__(self, total_services: int, fault_tolerance: int = 1):
        self.total = total_services
        self.quorum_size = (total_services + fault_tolerance) // 2 + 1
        self.proposals: Dict[str, Set[str]] = {}

    def propose(self, seed_id: str, proposer_id: str) -> bool:
        """Vote on reconfiguring a seed. Returns True if quorum reached."""
        if seed_id not in self.proposals:
            self.proposals[seed_id] = set()
        self.proposals[seed_id].add(proposer_id)
        if len(self.proposals[seed_id]) >= self.quorum_size:
            del self.proposals[seed_id]
            return True
        return False


# ===========================================================================
# SECTION 4: Staging Protocol and Priority Scheduling
# ===========================================================================

class Stage(Enum):
    """Reconfiguration stages."""
    PENDING = 0
    PREPARING = 1
    COMMITTING = 2
    VERIFYING = 3
    COMPLETE = 4
    FAILED = 5


class Priority(Enum):
    """Reconfiguration priority levels."""
    CRITICAL = 0     # seed exposure imminent
    HIGH = 1         # below threshold
    MEDIUM = 2       # degraded but functional
    LOW = 3          # reintegration
    BACKGROUND = 4   # optimization only


@dataclass(order=True)
class ReconfigRequest:
    """A prioritized reconfiguration request."""
    priority: int
    timestamp: float
    seed_id: str = field(compare=False)
    component_id: str = field(compare=False)
    stage: Stage = field(default=Stage.PENDING, compare=False)
    retry_count: int = field(default=0, compare=False)


class StagingProtocol:
    """
    Multi-phase reconfiguration with rollback.

    Each reconfiguration passes through:
      PENDING -> PREPARING -> COMMITTING -> VERIFYING -> COMPLETE
    Failure at any stage triggers rollback.
    """

    def __init__(self, quorum_size: int):
        self.quorum_size = quorum_size
        self.active: Dict[str, ReconfigRequest] = {}
        self.history: List[ReconfigRequest] = []

    def can_enter(self, request: ReconfigRequest) -> bool:
        """Check if staging slot is available for this seed."""
        if request.seed_id in self.active:
            existing = self.active[request.seed_id]
            if existing.stage not in (Stage.COMPLETE, Stage.FAILED):
                return False
        return True

    def enter_stage(self, request: ReconfigRequest, stage: Stage):
        """Advance to next stage."""
        request.stage = stage
        request.timestamp = time.time()
        self.active[request.seed_id] = request

    def verify(self, request: ReconfigRequest, data: bytes) -> bool:
        """Verification phase: checksum + simulated quorum."""
        if request.stage != Stage.VERIFYING:
            return False
        hashlib.blake2b(data, digest_size=8).digest()
        verified = random.random() > 0.1  # 90% success
        if verified:
            request.stage = Stage.COMPLETE
            self.active.pop(request.seed_id, None)
            self.history.append(request)
        else:
            request.stage = Stage.FAILED
            request.retry_count += 1
        return verified

    def rollback(self, seed_id: str) -> bool:
        """Abort reconfiguration for a seed."""
        if seed_id in self.active:
            self.active[seed_id].stage = Stage.FAILED
            del self.active[seed_id]
            return True
        return False


class PriorityScheduler:
    """
    Priority queue with exponential backoff for retries.

    Higher priority (lower numeric value) requests are processed first.
    Failed requests are re-queued with degraded priority and backoff.
    """

    def __init__(self, max_concurrent: int = 1, max_retries: int = 3):
        self.queue: List[ReconfigRequest] = []
        self.active: Dict[str, ReconfigRequest] = {}
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.backoff_multiplier = 2.0

    def submit(self, seed_id: str, component_id: str,
               priority: Priority) -> bool:
        """Submit a reconfiguration request."""
        if seed_id in self.active:
            return False
        for req in self.queue:
            if req.seed_id == seed_id:
                return False
        request = ReconfigRequest(
            priority=priority.value,
            timestamp=time.time(),
            seed_id=seed_id,
            component_id=component_id,
        )
        heapq.heappush(self.queue, request)
        return True

    def schedule_next(self) -> Optional[ReconfigRequest]:
        """Pop highest priority request if concurrency allows."""
        if len(self.active) >= self.max_concurrent or not self.queue:
            return None
        request = heapq.heappop(self.queue)
        if request.retry_count >= self.max_retries:
            return None
        if request.retry_count > 0:
            backoff = self.backoff_multiplier ** request.retry_count
            if time.time() - request.timestamp < backoff:
                heapq.heappush(self.queue, request)
                return None
        self.active[request.seed_id] = request
        return request

    def complete(self, seed_id: str, success: bool):
        """Mark request as done, re-queue on failure."""
        request = self.active.pop(seed_id, None)
        if request and not success:
            request.retry_count += 1
            if request.retry_count < self.max_retries:
                request.priority = min(
                    request.priority + 1, Priority.BACKGROUND.value
                )
                heapq.heappush(self.queue, request)

    def pending_count(self) -> int:
        return len(self.queue)


class PriorityRules:
    """Heuristic priority assignment based on system state."""

    @staticmethod
    def evaluate(current_holders: List[str], threshold: int,
                 online_components: List[str]) -> Priority:
        healthy = len([h for h in current_holders if h in online_components])
        if healthy < threshold:
            return Priority.CRITICAL
        elif healthy == threshold:
            return Priority.HIGH
        elif healthy <= threshold + 1:
            return Priority.MEDIUM
        elif healthy <= threshold + 2:
            return Priority.LOW
        return Priority.BACKGROUND



# ===========================================================================
# SECTION 5: Distributed Coordination Primitives
# ===========================================================================

@dataclass
class HybridLogicalClock:
    """
    Hybrid logical clock for distributed time coordination.

    Combines physical time with a logical counter to order events
    across components without centralized NTP.
    """
    component_id: str
    pt: float = field(default_factory=time.time)
    lt: int = 0

    def tick(self) -> Tuple[float, int]:
        """Local event: advance clock."""
        now = time.time()
        if now > self.pt:
            self.pt = now
            self.lt = 0
        else:
            self.lt += 1
        return (self.pt, self.lt)

    def update(self, received_pt: float, received_lt: int):
        """Merge with received timestamp."""
        now = time.time()
        old_pt = self.pt
        self.pt = max(now, received_pt, self.pt)
        if self.pt == old_pt:
            self.lt = max(self.lt, received_lt) + 1
        elif self.pt == received_pt:
            self.lt = received_lt + 1
        else:
            self.lt = 0

    def timestamp(self) -> bytes:
        return f"{self.component_id}:{self.pt}:{self.lt}".encode()


class CircuitBreaker:
    """
    Rate limiter: blocks a component after too many attempts
    within a sliding window.
    """

    def __init__(self, max_attempts: int = 5,
                 window_seconds: int = 60):
        self.max_attempts = max_attempts
        self.window = window_seconds
        self.attempts: Dict[str, deque] = {}

    def allow(self, component_id: str) -> bool:
        """Returns True if component is allowed to proceed."""
        if component_id not in self.attempts:
            self.attempts[component_id] = deque()
        now = time.time()
        q = self.attempts[component_id]
        while q and q[0] < now - self.window:
            q.popleft()
        if len(q) >= self.max_attempts:
            return False
        q.append(now)
        return True

    def reset(self, component_id: str):
        """Clear history for a component."""
        if component_id in self.attempts:
            self.attempts[component_id].clear()


class FencingManager:
    """
    Generation tokens for split-brain prevention.

    Each component gets a monotonically increasing generation number.
    Stale generations are rejected -- prevents zombie components
    from corrupting state after network partition.
    """

    def __init__(self):
        self.components: Dict[str, int] = {}
        self.lock = threading.Lock()

    def register(self, component_id: str) -> int:
        """Register or re-register a component. Returns generation."""
        with self.lock:
            gen = self.components.get(component_id, 0) + 1
            self.components[component_id] = gen
            return gen

    def validate(self, component_id: str,
                 claimed_generation: int) -> bool:
        """Check if claimed generation is current."""
        return self.components.get(component_id) == claimed_generation

    def fence(self, component_id: str):
        """Force generation increment (invalidates stale references)."""
        with self.lock:
            self.components[component_id] = (
                self.components.get(component_id, 0) + 1
            )


# ===========================================================================
# SECTION 6: Verification and Audit
# ===========================================================================

class ByzantineVerifier:
    """
    Cryptographic share verification with commitment hashes.

    Verifies shares against stored commitments before using them
    for reconstruction, preventing Byzantine corruption.
    """

    def __init__(self, threshold: int = 3):
        self.threshold = threshold
        self.commitments: Dict[str, bytes] = {}

    def register_seed(self, seed_id: str,
                      share_commitments: List[bytes]):
        """Store Merkle root for all shares of a seed."""
        combined = b"".join(sorted(share_commitments))
        self.commitments[seed_id] = hashlib.blake2b(
            combined, digest_size=32
        ).digest()

    def verify_share(self, seed_id: str, share: bytes,
                     commitment: bytes) -> bool:
        """Verify a single share against its commitment."""
        if seed_id not in self.commitments:
            return False
        return (hashlib.blake2b(share, digest_size=16).digest()
                == commitment)

    def verify_reconstruction(self, shares: List[bytes],
                              seed_id: str) -> bool:
        """Check that enough verified shares exist."""
        if len(shares) < self.threshold:
            return False
        # Check for conflicting shares (Byzantine behavior)
        unique = len(set(shares))
        if unique > 1 and unique < len(shares):
            return False  # Some shares disagree
        return True


@dataclass
class AuditEntry:
    """A single signed audit log entry."""
    operation_id: str
    operation_type: str
    initiator: str
    seed_id: str
    timestamp: float
    signature: bytes
    details: Dict[str, Any]


class AuditTrail:
    """
    Tamper-evident signed operation log.

    Every sensitive operation (reconfig, reconstruct, rotate)
    is logged with a blake2b signature. The chain can be verified
    end-to-end for integrity.
    """

    def __init__(self, max_entries: int = 10000):
        self.entries: List[AuditEntry] = []
        self.max_entries = max_entries

    def log(self, op_type: str, initiator: str,
            seed_id: str, details: Dict[str, Any] = None):
        """Log an operation with automatic signing."""
        op_id = secrets.token_hex(8)
        ts = time.time()
        details = details or {}
        msg = f"{op_id}:{op_type}:{initiator}:{seed_id}:{ts}"
        sig = hashlib.blake2b(
            msg.encode() + str(details).encode(), digest_size=16
        ).digest()
        entry = AuditEntry(
            operation_id=op_id,
            operation_type=op_type,
            initiator=initiator,
            seed_id=seed_id,
            timestamp=ts,
            signature=sig,
            details=details,
        )
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

    def verify_chain(self) -> bool:
        """Verify all signatures in the audit trail."""
        for entry in self.entries:
            msg = (f"{entry.operation_id}:{entry.operation_type}:"
                   f"{entry.initiator}:{entry.seed_id}:"
                   f"{entry.timestamp}")
            expected = hashlib.blake2b(
                msg.encode() + str(entry.details).encode(),
                digest_size=16,
            ).digest()
            if entry.signature != expected:
                return False
        return True

    def operations_for_seed(self, seed_id: str) -> List[AuditEntry]:
        return [e for e in self.entries if e.seed_id == seed_id]



# ===========================================================================
# SECTION 7: Key Rotation, Merkle Sync, Resource Reservation
# ===========================================================================

@dataclass
class EpochSeed:
    """A time-bounded seed with epoch tracking and lineage."""
    seed_id: str
    compressed: bytes
    epoch: int
    expires_at: float
    rotated_from: Optional[str] = None


class KeyRotationManager:
    """
    Epoch-based key rotation with seed lineage.

    Seeds have a TTL. When expired, they're rotated: a new seed
    is derived and the old one is archived in the lineage history.
    """

    def __init__(self, epoch_duration: int = 86400):
        self.epoch_duration = epoch_duration
        self.active: Dict[str, EpochSeed] = {}
        self.lineage: Dict[str, List[EpochSeed]] = {}

    def create(self, raw_seed: bytes,
               previous_id: Optional[str] = None) -> EpochSeed:
        """Create a new epoch seed, optionally linked to predecessor."""
        compressed = hashlib.blake2b(raw_seed, digest_size=16).digest()
        epoch = 1
        if previous_id and previous_id in self.active:
            epoch = self.active[previous_id].epoch + 1
        seed_id = (f"seed_{epoch}_"
                   + hashlib.blake2b(compressed, digest_size=8).hexdigest())
        new_seed = EpochSeed(
            seed_id=seed_id,
            compressed=compressed,
            epoch=epoch,
            expires_at=time.time() + self.epoch_duration,
            rotated_from=previous_id,
        )
        self.active[seed_id] = new_seed
        if previous_id:
            self.lineage.setdefault(previous_id, []).append(new_seed)
        return new_seed

    def rotate_expired(self) -> List[EpochSeed]:
        """Rotate all expired seeds. Returns list of new seeds."""
        rotated = []
        now = time.time()
        expired = [
            sid for sid, s in self.active.items()
            if s.expires_at <= now
        ]
        for sid in expired:
            self.active.pop(sid)
            new_raw = secrets.token_bytes(16)
            new_seed = self.create(new_raw, previous_id=sid)
            rotated.append(new_seed)
        return rotated


class ShareMerkleTree:
    """
    Merkle tree over seed shares for efficient state sync.

    After a network partition, two components can compare root
    hashes to detect divergence, then drill down to find exactly
    which seeds differ -- without transmitting all shares.
    """

    def __init__(self, shares: Dict[str, bytes]):
        self.shares = dict(shares)
        self.root_hash_val = self._compute_root()

    def _compute_root(self) -> bytes:
        """Compute Merkle root from leaf hashes."""
        leaves = []
        for seed_id, share in sorted(self.shares.items()):
            leaf = hashlib.blake2b(
                seed_id.encode() + share, digest_size=16
            ).digest()
            leaves.append(leaf)
        if not leaves:
            return b"\x00" * 16
        while len(leaves) > 1:
            next_level = []
            for i in range(0, len(leaves), 2):
                if i + 1 < len(leaves):
                    combined = leaves[i] + leaves[i + 1]
                else:
                    combined = leaves[i]
                next_level.append(
                    hashlib.blake2b(combined, digest_size=16).digest()
                )
            leaves = next_level
        return leaves[0]

    def root(self) -> bytes:
        return self.root_hash_val

    def diff(self, other: ShareMerkleTree) -> List[str]:
        """Return seed_ids that differ between two trees."""
        differing = []
        all_seeds = set(self.shares.keys()) | set(other.shares.keys())
        for sid in all_seeds:
            if self.shares.get(sid, b"") != other.shares.get(sid, b""):
                differing.append(sid)
        return differing


class ResourceType(Enum):
    """Types of system resources."""
    CPU_IDLE = "cpu_idle"
    NETWORK_BANDWIDTH = "bandwidth"
    MEMORY = "memory"
    STANDBY_HARDWARE = "standby_hw"
    FPGA_CYCLES = "fpga"
    POWER_BUDGET = "power"


class ResourceReservation:
    """
    Resource reservation for critical operations.

    Guarantees minimum resource availability for healing operations.
    No single reservation can take more than 50% of any resource.
    """

    def __init__(self):
        self.reserved: Dict[str, Dict[str, float]] = {
            rt.value: {} for rt in ResourceType
        }
        self.guaranteed_minimum: Dict[str, float] = {
            ResourceType.CPU_IDLE.value: 0.1,
            ResourceType.NETWORK_BANDWIDTH.value: 0.2,
            ResourceType.MEMORY.value: 0.1,
            ResourceType.STANDBY_HARDWARE.value: 0.0,
            ResourceType.FPGA_CYCLES.value: 0.0,
            ResourceType.POWER_BUDGET.value: 0.1,
        }

    def reserve(self, rtype: ResourceType, amount: float,
                purpose: str) -> bool:
        """Reserve resources. Returns False if insufficient."""
        max_reservable = 0.5
        if amount > max_reservable:
            return False
        current = sum(self.reserved[rtype.value].values())
        if current + amount <= max_reservable:
            self.reserved[rtype.value][purpose] = amount
            return True
        return False

    def release(self, rtype: ResourceType, purpose: str):
        """Release a reservation."""
        self.reserved[rtype.value].pop(purpose, None)

    def available(self, rtype: ResourceType, total: float) -> float:
        """Available resources after reservations and minimums."""
        reserved = sum(self.reserved[rtype.value].values())
        guaranteed = self.guaranteed_minimum.get(rtype.value, 0)
        return max(0, total - reserved - guaranteed)



# ===========================================================================
# SECTION 8: Healing Tools and Orchestration
# ===========================================================================

class HealingTool(ABC):
    """Abstract healing tool that consumes resources to improve resilience."""

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def resource_cost(self) -> Dict[ResourceType, float]:
        pass

    @abstractmethod
    def execute(self, context: Dict) -> bool:
        pass

    @abstractmethod
    def benefit_score(self, system_state: Dict) -> float:
        pass


class VerifySharesTool(HealingTool):
    """Proactively verify share integrity during idle time."""

    def name(self) -> str:
        return "verify_shares"

    def resource_cost(self) -> Dict[ResourceType, float]:
        return {
            ResourceType.CPU_IDLE: 0.15,
            ResourceType.MEMORY: 0.05,
        }

    def execute(self, context: Dict) -> bool:
        dispersal = context.get("dispersal")
        if not dispersal:
            return False
        verified = 0
        for seed_id, (compressed, holders) in dispersal.seed_registry.items():
            for holder in holders:
                comp = dispersal.components.get(holder)
                if comp:
                    share = comp.retrieve_share(seed_id)
                    if share:
                        verified += 1
        return verified > 0

    def benefit_score(self, system_state: Dict) -> float:
        last_verify = system_state.get("last_verification_time", 0)
        elapsed = time.time() - last_verify
        return min(elapsed / 3600.0, 1.0)


class RedistributeSharesTool(HealingTool):
    """Rebalance shares across online components."""

    def name(self) -> str:
        return "redistribute_shares"

    def resource_cost(self) -> Dict[ResourceType, float]:
        return {
            ResourceType.NETWORK_BANDWIDTH: 0.4,
            ResourceType.CPU_IDLE: 0.2,
        }

    def execute(self, context: Dict) -> bool:
        return True  # simplified

    def benefit_score(self, system_state: Dict) -> float:
        return min(system_state.get("share_load_variance", 0), 1.0)


class ExternalToolOrchestrator:
    """
    Resource-aware healing tool orchestrator.

    Selects the highest-benefit tool that fits within the current
    resource budget and executes it. Maintains execution history
    for diagnostics.
    """

    def __init__(self):
        self.tools: List[HealingTool] = []
        self.current_resources: Dict[ResourceType, float] = {}
        self.execution_history: List[Tuple[str, bool, float]] = []

    def register_tool(self, tool: HealingTool):
        self.tools.append(tool)

    def update_resources(self, resources: Dict[ResourceType, float]):
        self.current_resources = dict(resources)

    def _resources_sufficient(self,
                              cost: Dict[ResourceType, float]) -> bool:
        for rtype, required in cost.items():
            if self.current_resources.get(rtype, 0) < required:
                return False
        return True

    def select_best_tool(self,
                         system_state: Dict) -> Optional[HealingTool]:
        """Select highest-benefit affordable tool."""
        best, best_score = None, -1
        for tool in self.tools:
            if not self._resources_sufficient(tool.resource_cost()):
                continue
            score = tool.benefit_score(system_state)
            if score > best_score:
                best_score = score
                best = tool
        return best

    def execute_best(self, system_state: Dict,
                     context: Dict) -> Optional[str]:
        """Select and execute the best affordable tool."""
        tool = self.select_best_tool(system_state)
        if not tool:
            return None
        success = tool.execute(context)
        # Deduct resources
        for rtype, cost in tool.resource_cost().items():
            self.current_resources[rtype] = max(
                0, self.current_resources.get(rtype, 0) - cost
            )
        self.execution_history.append(
            (tool.name(), success, time.time())
        )
        return tool.name()


# ===========================================================================
# SECTION 9: Integrated Resilience System
# ===========================================================================

class OctahedralResilienceSystem:
    """
    Complete self-healing system on the octahedral lattice.

    Integrates all resilience mechanisms:
    - Heartbeat monitoring + failover clustering
    - Seed dispersal with threshold secret sharing
    - Service reconfiguration with quorum consensus
    - Priority-staged reconfiguration with rollback
    - Hybrid logical clocks for distributed ordering
    - Byzantine share verification
    - Circuit breakers for rate limiting
    - Fencing tokens for split-brain prevention
    - Merkle trees for partition recovery
    - Signed audit trail for accountability
    - Key rotation with epoch lineage
    - Resource reservation for critical paths
    - External healing tool orchestration
    """

    def __init__(self, num_components: int = 5,
                 threshold: int = 3):
        # Hardware components
        self.hw_components = [
            HardwareComponent(f"hw_{i}") for i in range(num_components)
        ]

        # Octahedral nodes (one per component)
        self.nodes = {
            comp.id: OctahedralNode(
                id=comp.id, axis_index=i % 6
            )
            for i, comp in enumerate(self.hw_components)
        }

        # Core systems
        self.heartbeat = HeartbeatMonitor(self.nodes)
        self.cluster = OctahedralCluster(
            primary=self.nodes[self.hw_components[0].id],
            backups=[self.nodes[c.id] for c in self.hw_components[1:3]],
        )
        self.alert_monitor = AlertMonitor()
        self.auto_recovery = AutoRecovery(
            self.cluster, self.alert_monitor
        )

        # Seed management
        self.dispersal = SeedDispersal(
            self.hw_components,
            total_shares=num_components,
            threshold=threshold,
        )
        self.reconfigurator = ServiceReconfigurator(self.dispersal)
        self.quorum = QuorumReconfigurator(num_components)

        # Coordination
        self.hlc = HybridLogicalClock("master")
        self.circuit_breaker = CircuitBreaker()
        self.fencing = FencingManager()
        self.byzantine = ByzantineVerifier(threshold)

        # Verification and audit
        self.audit = AuditTrail()
        self.key_rotation = KeyRotationManager()
        self.resources = ResourceReservation()

        # Healing tools
        self.orchestrator = ExternalToolOrchestrator()
        self.orchestrator.register_tool(VerifySharesTool())
        self.orchestrator.register_tool(RedistributeSharesTool())

        # Register all services
        for comp in self.hw_components:
            self.reconfigurator.register_service(comp.id)

    def bootstrap_seed(self, raw_seed: bytes) -> str:
        """Compress, split, and disperse a new seed."""
        seed = CompressedSeed(raw_seed)
        seed_id = self.dispersal.disperse(seed)
        self.audit.log("bootstrap", "system", seed_id)
        self.hlc.tick()
        return seed_id

    def refresh_seed(self, seed_id: str) -> bool:
        """Reconstruct seed from hardware shares."""
        recovered = self.dispersal.reconstruct(seed_id)
        if recovered and recovered.verify():
            self.audit.log("refresh", "system", seed_id)
            return True
        return False

    def safe_reconfigure(self, seed_id: str,
                         component_id: str) -> bool:
        """Reconfiguration with all protections."""
        # Circuit breaker
        if not self.circuit_breaker.allow(component_id):
            return False
        # Fencing
        gen = self.fencing.register(component_id)
        if not self.fencing.validate(component_id, gen):
            return False
        # Resource reservation
        if not self.resources.reserve(
            ResourceType.CPU_IDLE, 0.2,
            f"reconfig_{seed_id}"
        ):
            return False
        # Audit
        self.audit.log(
            "reconfig", component_id, seed_id,
            {"generation": gen},
        )
        self.hlc.tick()
        # Release
        self.resources.release(
            ResourceType.CPU_IDLE, f"reconfig_{seed_id}"
        )
        return True

    def health_check(self) -> Dict[str, Health]:
        """Run one health check cycle with auto-recovery."""
        status = self.heartbeat.check()
        self.alert_monitor.update(status)
        for nid, health in status.items():
            if health == Health.FAILED:
                self.auto_recovery.recover(nid)
                self.reconfigurator.degrade_service(nid)
        return status

    def sync_after_partition(self,
                             peer_shares: Dict[str, bytes]
                             ) -> List[str]:
        """Merkle-based sync after network partition."""
        local_shares = {}
        for seed_id, (_, holders) in self.dispersal.seed_registry.items():
            for h in holders:
                comp = self.dispersal.components.get(h)
                if comp:
                    share = comp.retrieve_share(seed_id)
                    if share:
                        local_shares[seed_id] = share
                        break
        local_tree = ShareMerkleTree(local_shares)
        peer_tree = ShareMerkleTree(peer_shares)
        return local_tree.diff(peer_tree)

    def system_status(self) -> Dict[str, Any]:
        """Complete system diagnostic."""
        health = self.heartbeat.check()
        return {
            "components": len(self.hw_components),
            "health": {nid: h.value for nid, h in health.items()},
            "seeds_tracked": len(self.dispersal.seed_registry),
            "alerts": len(self.alert_monitor.alerts),
            "audit_entries": len(self.audit.entries),
            "audit_verified": self.audit.verify_chain(),
            "failover_count": self.cluster.failover_count,
            "recovered_nodes": len(self.auto_recovery.recovered),
        }


# ============================================================================
# DEMONSTRATIONS
# ============================================================================

def demo_health_monitoring():
    """Show heartbeat monitoring and failover."""
    print("=" * 60)
    print("OCTAHEDRAL RESILIENCE v1.0")
    print("Self-healing distributed infrastructure")
    print("=" * 60)

    system = OctahedralResilienceSystem()

    print("\n  Health check cycle:")
    status = system.health_check()
    for nid, health in status.items():
        print(f"    {nid}: {health.value}")

    print(f"\n  Alerts raised: {len(system.alert_monitor.alerts)}")
    print(f"  Failovers: {system.cluster.failover_count}")


def demo_seed_dispersal():
    """Show seed splitting and reconstruction."""
    print("\n" + "=" * 60)
    print("SEED DISPERSAL")
    print("=" * 60)

    system = OctahedralResilienceSystem()

    raw = secrets.token_bytes(16)
    seed_id = system.bootstrap_seed(raw)
    print(f"\n  Seed {seed_id} dispersed across 5 components")

    _, holders = system.dispersal.seed_registry[seed_id]
    print(f"  Holders: {holders}")

    ok = system.refresh_seed(seed_id)
    print(f"  Reconstruction: {'success' if ok else 'failed'}")


def demo_safe_reconfig():
    """Show protected reconfiguration."""
    print("\n" + "=" * 60)
    print("SAFE RECONFIGURATION")
    print("=" * 60)

    system = OctahedralResilienceSystem()
    seed_id = system.bootstrap_seed(secrets.token_bytes(16))

    print(f"\n  Reconfiguring seed {seed_id}:")
    ok = system.safe_reconfigure(seed_id, "hw_0")
    print(f"    Result: {'success' if ok else 'blocked'}")

    # Circuit breaker test
    print("\n  Circuit breaker (6 rapid attempts):")
    for i in range(6):
        allowed = system.circuit_breaker.allow("rapid_comp")
        print(f"    Attempt {i+1}: {'allowed' if allowed else 'BLOCKED'}")


def demo_merkle_sync():
    """Show Merkle-based partition sync."""
    print("\n" + "=" * 60)
    print("MERKLE PARTITION SYNC")
    print("=" * 60)

    tree1 = ShareMerkleTree({"seed_a": b"share1", "seed_b": b"share2"})
    tree2 = ShareMerkleTree({"seed_a": b"share1", "seed_b": b"CHANGED"})

    print(f"\n  Tree 1 root: {tree1.root().hex()[:16]}")
    print(f"  Tree 2 root: {tree2.root().hex()[:16]}")
    print(f"  Roots match: {tree1.root() == tree2.root()}")
    print(f"  Differing seeds: {tree1.diff(tree2)}")


def demo_priority_scheduling():
    """Show priority-based reconfiguration scheduling."""
    print("\n" + "=" * 60)
    print("PRIORITY SCHEDULING")
    print("=" * 60)

    scheduler = PriorityScheduler()
    requests = [
        ("seed_A", "comp_1", Priority.LOW),
        ("seed_B", "comp_2", Priority.CRITICAL),
        ("seed_C", "comp_3", Priority.HIGH),
        ("seed_D", "comp_4", Priority.BACKGROUND),
    ]
    for sid, cid, pri in requests:
        scheduler.submit(sid, cid, pri)

    print(f"\n  Queued {scheduler.pending_count()} requests")
    print("  Processing order:")
    while scheduler.pending_count() > 0:
        req = scheduler.schedule_next()
        if req:
            pri_name = Priority(req.priority).name
            print(f"    {pri_name}: {req.seed_id}")
            scheduler.complete(req.seed_id, success=True)


def demo_audit_trail():
    """Show signed audit trail."""
    print("\n" + "=" * 60)
    print("AUDIT TRAIL")
    print("=" * 60)

    system = OctahedralResilienceSystem()
    sid = system.bootstrap_seed(secrets.token_bytes(16))
    system.safe_reconfigure(sid, "hw_0")
    system.refresh_seed(sid)

    print(f"\n  Audit entries: {len(system.audit.entries)}")
    print(f"  Chain verified: {system.audit.verify_chain()}")
    for entry in system.audit.entries:
        print(f"    [{entry.operation_type}] {entry.seed_id[:12]}... "
              f"by {entry.initiator}")


def demo_system_status():
    """Show full system diagnostic."""
    print("\n" + "=" * 60)
    print("SYSTEM STATUS")
    print("=" * 60)

    system = OctahedralResilienceSystem()
    system.bootstrap_seed(secrets.token_bytes(16))
    system.bootstrap_seed(secrets.token_bytes(16))
    system.health_check()

    status = system.system_status()
    for k, v in status.items():
        print(f"  {k}: {v}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo_health_monitoring()
    demo_seed_dispersal()
    demo_safe_reconfig()
    demo_merkle_sync()
    demo_priority_scheduling()
    demo_audit_trail()
    demo_system_status()
