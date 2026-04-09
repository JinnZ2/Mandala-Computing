"""
OCTAHEDRAL SESSION CACHE v1.0
Session caching framework for octahedral constraint OS.
CC0 -- stdlib only

Cache coherence is geometric: a cached result is valid if and only if
all 6 octahedral constraint axes remain within tolerance of the snapshot.
Staleness propagates along the octahedral edge graph (12 edges connecting
6 vertices), so a drift on one axis cascades to invalidate coupled axes.

ARCHITECTURE:
  +Z ---- constraint_5       Cache valid IFF all 6 axes
  +Y ---- constraint_3       within tolerance of snapshot.
  +X ---- constraint_1
  -X ---- constraint_2       Invalidation cascades along
  -Y ---- constraint_4       octahedral edges (12 edges,
  -Z ---- constraint_6       6 vertices).

PROTOCOLS:
  1. SNAPSHOT   -- freeze constraint state -> cache key
  2. VALIDATE   -- compare live state to cached snapshot
  3. INVALIDATE -- propagate staleness along edges
  4. EVICT      -- LRU within constraint-coherent groups
  5. PERSIST    -- serialize to disk for session resume
  6. RESTORE    -- reload + revalidate on reconnect

Core types:
  OctState          -- 6-axis constraint snapshot
  CacheEntry        -- cached payload with TTL and dependencies
  InvalidationGraph -- octahedral edge topology for cascade
  SessionCache      -- the coherence-aware cache engine

Design:
  - stdlib only (no numpy, no scipy)
  - Cache keys are SHA-256 of constraint state
  - L-inf norm measures constraint drift
  - LRU eviction within capacity limit
  - JSON persistence for session resume
"""

from __future__ import annotations
import hashlib
import json
import time
import math
import os
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any, Tuple, Set
from collections import OrderedDict
from pathlib import Path

from octahedral_arithmetic import PHI


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The 6 octahedral axes, matching OCTAHEDRAL_VERTICES from geometric_state_algebra
AXIS_LABELS = ("+X", "-X", "+Y", "-Y", "+Z", "-Z")
AXIS_VECTORS = (
    ( 1,  0,  0),
    (-1,  0,  0),
    ( 0,  1,  0),
    ( 0, -1,  0),
    ( 0,  0,  1),
    ( 0,  0, -1),
)


# ---------------------------------------------------------------------------
# OctState: 6-axis constraint snapshot
# ---------------------------------------------------------------------------

@dataclass
class OctState:
    """
    6-axis constraint snapshot on the octahedral lattice.

    Each axis represents a constraint dimension:
      axes[0] = +X constraint (e.g., forward momentum)
      axes[1] = -X constraint (e.g., backward drag)
      axes[2] = +Y constraint (e.g., lateral expansion)
      axes[3] = -Y constraint (e.g., lateral contraction)
      axes[4] = +Z constraint (e.g., upward potential)
      axes[5] = -Z constraint (e.g., downward gravity)

    The state is valid when all 6 axes are within tolerance
    of their snapshot values. Drift on any axis triggers
    cascade invalidation along octahedral edges.
    """
    axes: Tuple[float, float, float, float, float, float]
    timestamp: float = field(default_factory=time.time)
    source_repo: str = ""

    def key(self) -> str:
        """SHA-256 hash of constraint state, truncated to 16 hex chars."""
        raw = f"{self.axes}:{self.source_repo}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def distance(self, other: OctState) -> float:
        """L-inf norm across axes: max single-axis drift."""
        return max(abs(a - b) for a, b in zip(self.axes, other.axes))

    def l2_distance(self, other: OctState) -> float:
        """L2 (Euclidean) distance across axes."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(self.axes, other.axes)))

    def phi_weighted_distance(self, other: OctState) -> float:
        """
        Golden-ratio weighted distance: earlier axes (more fundamental
        constraints) contribute more to the distance metric.
        """
        total = 0.0
        for i, (a, b) in enumerate(zip(self.axes, other.axes)):
            weight = PHI ** (5 - i)  # axis 0 has highest weight
            total += weight * (a - b) ** 2
        return math.sqrt(total)

    def antipodal_balance(self) -> Tuple[float, float, float]:
        """
        Balance between antipodal axis pairs: (+X,-X), (+Y,-Y), (+Z,-Z).
        Returns 3 balance ratios. Perfect balance = 0.0 on each.
        """
        return (
            self.axes[0] + self.axes[1],  # X balance
            self.axes[2] + self.axes[3],  # Y balance
            self.axes[4] + self.axes[5],  # Z balance
        )

    def to_dict(self) -> dict:
        return {
            "axes": list(self.axes),
            "timestamp": self.timestamp,
            "source_repo": self.source_repo,
        }

    @classmethod
    def from_dict(cls, d: dict) -> OctState:
        return cls(
            axes=tuple(d["axes"]),
            timestamp=d["timestamp"],
            source_repo=d.get("source_repo", ""),
        )


# ---------------------------------------------------------------------------
# CacheEntry
# ---------------------------------------------------------------------------

@dataclass
class CacheEntry:
    """
    A single cached payload with its constraint snapshot.

    The entry is valid if:
    1. TTL hasn't expired
    2. The constraint state hasn't drifted beyond tolerance
    3. No dependency has been invalidated
    """
    state_snapshot: OctState
    payload: Any
    created: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    ttl_seconds: float = 3600.0  # default 1 hour
    dependencies: List[str] = field(default_factory=list)

    @property
    def expired(self) -> bool:
        return (time.time() - self.created) > self.ttl_seconds

    @property
    def age(self) -> float:
        return time.time() - self.created

    def touch(self):
        self.last_accessed = time.time()
        self.access_count += 1


# ---------------------------------------------------------------------------
# InvalidationGraph: octahedral edge topology
# ---------------------------------------------------------------------------

class InvalidationGraph:
    """
    Octahedral edge topology for cascade invalidation.

    The octahedron has 6 vertices and 12 edges. Each vertex is connected
    to 4 others (all except its antipode). When a constraint axis drifts,
    staleness propagates along edges to coupled axes.

    Edge connectivity (each vertex connects to 4 non-antipodal neighbors):
      +X (0) <-> +Y(2), -Y(3), +Z(4), -Z(5)
      -X (1) <-> +Y(2), -Y(3), +Z(4), -Z(5)
      +Y (2) <-> +X(0), -X(1), +Z(4), -Z(5)
      -Y (3) <-> +X(0), -X(1), +Z(4), -Z(5)
      +Z (4) <-> +X(0), -X(1), +Y(2), -Y(3)
      -Z (5) <-> +X(0), -X(1), +Y(2), -Y(3)

    Note: antipodal pairs (+X/-X, +Y/-Y, +Z/-Z) are NOT directly
    connected -- they couple only through their shared neighbors.
    This matches the actual octahedral geometry.
    """

    # 12 edges of the octahedron (vertex index pairs)
    EDGES = [
        (0, 2), (0, 3), (0, 4), (0, 5),  # +X connects to +Y,-Y,+Z,-Z
        (1, 2), (1, 3), (1, 4), (1, 5),  # -X connects to +Y,-Y,+Z,-Z
        (2, 4), (2, 5),                    # +Y connects to +Z,-Z
        (3, 4), (3, 5),                    # -Y connects to +Z,-Z
    ]

    def __init__(self):
        self.adjacency: Dict[int, List[int]] = {i: [] for i in range(6)}
        for a, b in self.EDGES:
            self.adjacency[a].append(b)
            self.adjacency[b].append(a)

    def neighbors(self, axis: int) -> List[int]:
        """Direct neighbors of an axis in the octahedral graph."""
        return list(self.adjacency.get(axis, []))

    def affected_axes(self, changed_axis: int, depth: int = -1) -> List[int]:
        """
        BFS from changed_axis: return all axes reachable within depth.
        depth=-1 means full cascade (all reachable, which is all 6).
        depth=1 means direct neighbors only.
        """
        visited: Set[int] = set()
        queue = [(changed_axis, 0)]
        while queue:
            ax, d = queue.pop(0)
            if ax in visited:
                continue
            if depth >= 0 and d > depth:
                continue
            visited.add(ax)
            for neighbor in self.adjacency.get(ax, []):
                if neighbor not in visited:
                    queue.append((neighbor, d + 1))
        return sorted(visited)

    def is_antipodal(self, a: int, b: int) -> bool:
        """Check if two axes are antipodal (opposite faces)."""
        return abs(a - b) == 1 and min(a, b) % 2 == 0

    def shortest_path(self, a: int, b: int) -> int:
        """Shortest path length between two axes in the octahedral graph."""
        if a == b:
            return 0
        if b in self.adjacency.get(a, []):
            return 1
        return 2  # antipodal pairs are always distance 2


# ---------------------------------------------------------------------------
# SessionCache: the coherence-aware cache engine
# ---------------------------------------------------------------------------

class SessionCache:
    """
    Session cache with octahedral coherence validation.

    A cached result is valid if and only if the live constraint state
    is within tolerance of the snapshot on all 6 axes. When any axis
    drifts, staleness cascades along the octahedral edge graph.

    PROTOCOL SUMMARY:
      SNAPSHOT   -- state -> key, store payload
      GET        -- key -> validate -> return or miss
      VALIDATE   -- live_state.distance(snapshot) < tolerance
      INVALIDATE -- cascade along octahedral edge graph
      EVICT      -- LRU within capacity
      PERSIST    -- JSON dump to disk
      RESTORE    -- load + bulk revalidate
    """

    def __init__(self, max_entries: int = 256,
                 tolerance: float = 0.05,
                 persist_dir: str = ".oct_cache"):
        self.store: OrderedDict[str, CacheEntry] = OrderedDict()
        self.max_entries = max_entries
        self.tolerance = tolerance
        self.persist_dir = Path(persist_dir)
        self.graph = InvalidationGraph()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "evictions": 0,
            "persists": 0,
            "restores": 0,
        }

    # ------------------------------------------------------------------
    # Protocol 1: SNAPSHOT
    # ------------------------------------------------------------------

    def put(self, state: OctState, payload: Any,
            ttl: float = 3600.0,
            deps: List[str] = None) -> str:
        """
        Cache a payload keyed by its constraint state snapshot.

        Returns the cache key (SHA-256 hash of state).
        """
        key = state.key()
        entry = CacheEntry(
            state_snapshot=state,
            payload=payload,
            ttl_seconds=ttl,
            dependencies=deps or [],
        )
        self.store[key] = entry
        self.store.move_to_end(key)
        self._enforce_capacity()
        return key

    # ------------------------------------------------------------------
    # Protocol 2: GET + VALIDATE
    # ------------------------------------------------------------------

    def get(self, key: str,
            live_state: Optional[OctState] = None) -> Optional[Any]:
        """
        Retrieve a cached payload with optional live validation.

        Returns None on miss, TTL expiry, or constraint drift.
        """
        entry = self.store.get(key)
        if entry is None:
            self.stats["misses"] += 1
            return None

        # TTL check
        if entry.expired:
            self._evict(key, reason="ttl")
            self.stats["misses"] += 1
            return None

        # Constraint coherence check
        if live_state and not self._validate(entry, live_state):
            self._evict(key, reason="drift")
            self.stats["misses"] += 1
            return None

        entry.touch()
        self.store.move_to_end(key)
        self.stats["hits"] += 1
        return entry.payload

    def contains(self, key: str) -> bool:
        """Check if key exists (without touching or validating)."""
        return key in self.store

    # ------------------------------------------------------------------
    # Protocol 3: VALIDATE
    # ------------------------------------------------------------------

    def _validate(self, entry: CacheEntry, live: OctState) -> bool:
        """Check if cached state is within tolerance of live state."""
        drift = entry.state_snapshot.distance(live)
        return drift <= self.tolerance

    def validate_all(self, live_state: OctState) -> Dict[str, bool]:
        """Validate all entries against a live state. Returns {key: valid}."""
        return {
            key: self._validate(entry, live_state)
            for key, entry in self.store.items()
        }

    # ------------------------------------------------------------------
    # Protocol 4: INVALIDATE (cascade)
    # ------------------------------------------------------------------

    def invalidate_axis(self, axis_index: int,
                        live_state: OctState,
                        cascade_depth: int = -1):
        """
        Invalidate entries affected by drift on a specific axis.

        Staleness cascades along the octahedral edge graph:
        depth=-1 cascades to all reachable axes (full octahedron),
        depth=1 only invalidates direct neighbors.
        """
        affected = self.graph.affected_axes(axis_index, depth=cascade_depth)
        to_remove = []
        for key, entry in self.store.items():
            snap = entry.state_snapshot
            for ax in affected:
                if abs(snap.axes[ax] - live_state.axes[ax]) > self.tolerance:
                    to_remove.append(key)
                    break
        for key in to_remove:
            self._evict(key, reason="cascade")
        self.stats["invalidations"] += len(to_remove)

    def invalidate_repo(self, repo_name: str):
        """Invalidate all entries from a specific source repo."""
        to_remove = [
            k for k, v in self.store.items()
            if v.state_snapshot.source_repo == repo_name
        ]
        for key in to_remove:
            self._evict(key, reason="repo_invalidate")
        self.stats["invalidations"] += len(to_remove)

    def invalidate_deps(self, dep_key: str):
        """Invalidate all entries that depend on a given key."""
        to_remove = [
            k for k, v in self.store.items()
            if dep_key in v.dependencies
        ]
        for key in to_remove:
            self._evict(key, reason="dep_invalidate")
        self.stats["invalidations"] += len(to_remove)

    # ------------------------------------------------------------------
    # Protocol 5: EVICT
    # ------------------------------------------------------------------

    def _evict(self, key: str, reason: str = "lru"):
        """Remove an entry from the cache."""
        self.store.pop(key, None)
        self.stats["evictions"] += 1

    def _enforce_capacity(self):
        """Evict oldest entries to stay within capacity."""
        while len(self.store) > self.max_entries:
            oldest_key = next(iter(self.store))
            self._evict(oldest_key, reason="capacity")

    def clear(self):
        """Clear all entries."""
        count = len(self.store)
        self.store.clear()
        self.stats["evictions"] += count

    # ------------------------------------------------------------------
    # Protocol 6: PERSIST
    # ------------------------------------------------------------------

    def persist(self, session_id: str = "default") -> str:
        """
        Serialize cache to disk as JSON.

        Only JSON-serializable payloads are persisted.
        Non-serializable payloads are converted to their string repr.
        """
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        path = self.persist_dir / f"{session_id}.json"
        data = {
            "session_id": session_id,
            "persisted_at": time.time(),
            "tolerance": self.tolerance,
            "stats": self.stats,
            "entries": {},
        }
        for k, v in self.store.items():
            # Safely serialize payload
            payload = v.payload
            if not isinstance(payload, (dict, list, str, int, float, bool, type(None))):
                payload = str(payload)
            data["entries"][k] = {
                "state": v.state_snapshot.to_dict(),
                "payload": payload,
                "created": v.created,
                "ttl": v.ttl_seconds,
                "deps": v.dependencies,
                "access_count": v.access_count,
            }
        path.write_text(json.dumps(data, indent=2))
        self.stats["persists"] += 1
        return str(path)

    # ------------------------------------------------------------------
    # Protocol 7: RESTORE + REVALIDATE
    # ------------------------------------------------------------------

    def restore(self, session_id: str = "default",
                live_state: Optional[OctState] = None) -> int:
        """
        Reload cache from disk, revalidating against live state.

        Returns number of entries successfully restored.
        Stale or expired entries are silently dropped.
        """
        path = self.persist_dir / f"{session_id}.json"
        if not path.exists():
            return 0
        data = json.loads(path.read_text())
        loaded = 0
        for key, entry_data in data.get("entries", {}).items():
            state = OctState.from_dict(entry_data["state"])
            # Skip if stale relative to live state
            if live_state and state.distance(live_state) > self.tolerance:
                continue
            entry = CacheEntry(
                state_snapshot=state,
                payload=entry_data["payload"],
                created=entry_data["created"],
                ttl_seconds=entry_data["ttl"],
                dependencies=entry_data.get("deps", []),
                access_count=entry_data.get("access_count", 0),
            )
            if not entry.expired:
                self.store[key] = entry
                loaded += 1
        self.stats["restores"] += 1
        return loaded

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def status(self) -> dict:
        """Current cache status and statistics."""
        ages = [e.age for e in self.store.values()]
        return {
            "entries": len(self.store),
            "capacity": self.max_entries,
            "utilization": len(self.store) / max(self.max_entries, 1),
            "stats": dict(self.stats),
            "oldest_age": max(ages) if ages else None,
            "newest_age": min(ages) if ages else None,
            "hit_rate": (
                self.stats["hits"] / max(self.stats["hits"] + self.stats["misses"], 1)
            ),
        }

    def entries_by_repo(self) -> Dict[str, int]:
        """Count of entries grouped by source repo."""
        counts: Dict[str, int] = {}
        for entry in self.store.values():
            repo = entry.state_snapshot.source_repo or "(none)"
            counts[repo] = counts.get(repo, 0) + 1
        return counts


# ============================================================================
# DEMONSTRATIONS
# ============================================================================

def demo_basic_cache():
    """Show the basic put/get/validate cycle."""
    print("=" * 60)
    print("SESSION CACHE v1.0")
    print("Octahedral coherence caching")
    print("=" * 60)

    cache = SessionCache(tolerance=0.05)

    # Snapshot a constraint state
    state = OctState(
        axes=(1.0, -0.3, 0.7, -0.7, 0.3, -1.0),
        source_repo="earth-systems-physics",
    )
    key = cache.put(state, payload={"cascade_result": [0.1, 0.2, 0.3]}, ttl=1800)
    print(f"\n  Cached: key={key}")
    print(f"  State: {state.axes}")
    print(f"  Antipodal balance: {state.antipodal_balance()}")

    # Retrieve with slight drift (within tolerance)
    live = OctState(axes=(1.01, -0.31, 0.69, -0.71, 0.31, -0.99))
    result = cache.get(key, live_state=live)
    drift = state.distance(live)
    print(f"\n  Live drift: {drift:.3f} (tolerance: {cache.tolerance})")
    print(f"  Cache hit: {result is not None}")

    # Retrieve with large drift (exceeds tolerance)
    drifted = OctState(axes=(1.5, -0.3, 0.7, -0.7, 0.3, -1.0))
    result = cache.get(key, live_state=drifted)
    drift = state.distance(drifted)
    print(f"\n  Large drift: {drift:.3f}")
    print(f"  Cache hit: {result is not None}")


def demo_cascade_invalidation():
    """Show cascade invalidation along octahedral edges."""
    print("\n" + "=" * 60)
    print("CASCADE INVALIDATION")
    print("=" * 60)

    cache = SessionCache(tolerance=0.1)
    graph = cache.graph

    # Show adjacency structure
    print("\n  Octahedral edge graph:")
    for i in range(6):
        neighbors = [AXIS_LABELS[n] for n in graph.neighbors(i)]
        print(f"    {AXIS_LABELS[i]}: neighbors = {neighbors}")

    # Cache multiple entries
    states = [
        OctState(axes=(1.0, -0.3, 0.7, -0.7, 0.3, -1.0), source_repo="repo_a"),
        OctState(axes=(0.5, -0.5, 0.5, -0.5, 0.5, -0.5), source_repo="repo_b"),
        OctState(axes=(0.9, -0.1, 0.8, -0.8, 0.2, -0.9), source_repo="repo_a"),
    ]
    keys = [cache.put(s, payload=f"result_{i}") for i, s in enumerate(states)]
    print(f"\n  Cached {len(keys)} entries")

    # Drift on +X axis (index 0)
    drifted = OctState(axes=(2.0, -0.3, 0.7, -0.7, 0.3, -1.0))
    affected = graph.affected_axes(0, depth=1)
    print(f"  +X drift -> affects: {[AXIS_LABELS[a] for a in affected]}")

    cache.invalidate_axis(0, drifted, cascade_depth=1)
    print(f"  After invalidation: {len(cache.store)} entries remain")
    print(f"  Stats: {cache.stats}")


def demo_persistence():
    """Show persist and restore with revalidation."""
    print("\n" + "=" * 60)
    print("PERSISTENCE + RESTORE")
    print("=" * 60)

    import tempfile
    tmpdir = tempfile.mkdtemp()

    # Session 1: cache and persist
    cache1 = SessionCache(tolerance=0.05, persist_dir=tmpdir)
    state = OctState(
        axes=(0.5, -0.5, 0.5, -0.5, 0.5, -0.5),
        source_repo="mandala-computing",
    )
    cache1.put(state, payload={"energy": -3.14, "cells": [0, 1, 2]})
    cache1.put(
        OctState(axes=(0.6, -0.4, 0.6, -0.4, 0.6, -0.4), source_repo="rosetta"),
        payload={"shape": "TETRA"},
    )
    path = cache1.persist("demo_session")
    print(f"\n  Persisted {len(cache1.store)} entries to {path}")

    # Session 2: restore with live validation
    cache2 = SessionCache(tolerance=0.05, persist_dir=tmpdir)
    live = OctState(axes=(0.51, -0.49, 0.51, -0.49, 0.51, -0.49))
    loaded = cache2.restore("demo_session", live_state=live)
    print(f"  Restored {loaded} valid entries (live drift applied)")
    print(f"  Status: {cache2.status()}")

    # Cleanup
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


def demo_distance_metrics():
    """Compare distance metrics on OctState."""
    print("\n" + "=" * 60)
    print("DISTANCE METRICS")
    print("=" * 60)

    base = OctState(axes=(1.0, -1.0, 0.5, -0.5, 0.0, 0.0))
    variants = [
        ("slight drift",    OctState(axes=(1.02, -0.98, 0.51, -0.49, 0.01, -0.01))),
        ("X-axis shift",    OctState(axes=(0.5,  -1.0,  0.5,  -0.5,  0.0,   0.0))),
        ("all-axis shift",  OctState(axes=(0.8,  -0.8,  0.3,  -0.3, -0.2,   0.2))),
        ("antipodal flip",  OctState(axes=(-1.0,  1.0, -0.5,  0.5,   0.0,   0.0))),
    ]

    print(f"\n  Base state: {base.axes}")
    for name, var in variants:
        d_inf = base.distance(var)
        d_l2 = base.l2_distance(var)
        d_phi = base.phi_weighted_distance(var)
        print(f"  {name:>18s}: L-inf={d_inf:.3f}  L2={d_l2:.3f}  phi={d_phi:.3f}")


def demo_graph_structure():
    """Show the invalidation graph properties."""
    print("\n" + "=" * 60)
    print("INVALIDATION GRAPH")
    print("=" * 60)

    graph = InvalidationGraph()

    print("\n  Octahedral properties:")
    print(f"    Vertices: 6")
    print(f"    Edges: {len(graph.EDGES)}")

    # Each vertex has 4 neighbors
    for i in range(6):
        nbrs = graph.neighbors(i)
        print(f"    {AXIS_LABELS[i]}: {len(nbrs)} neighbors, "
              f"antipodal to {AXIS_LABELS[i ^ 1]}, "
              f"path to antipode = {graph.shortest_path(i, i ^ 1)}")

    # Cascade reach at different depths
    print("\n  Cascade reach from +X (axis 0):")
    for depth in range(3):
        reached = graph.affected_axes(0, depth=depth)
        labels = [AXIS_LABELS[a] for a in reached]
        print(f"    depth {depth}: {labels}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo_basic_cache()
    demo_cascade_invalidation()
    demo_persistence()
    demo_distance_metrics()
    demo_graph_structure()
