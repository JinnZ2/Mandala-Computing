# mandala_hook.py — ExpandableMultiLedger with guided dimension expansion
# Sits BESIDE electron_accounting.py (sibling ledger repo), reuses Ledger grammar.
# CC0 1.0 Universal. No rights reserved.
#
# Requires: numpy (for vector operations). phone-buildable with numpy installed.
#
# The "Mandala" configuration provides a pre-defined lattice of possible
# dimensions and how they branch. When the ledger detects a persistent
# residual, it consults the mandala to decide which dimension to expand into
# next. This replaces blind expansion with a structured, holistic map — the
# idea described years ago as "mandala computing."
#
# Core principle: every conservation violation is a transfer into an
# unmonitored dimension. The ledger self-repairs by absorbing past imbalance
# into a new "environment" account, then resuming normal closure.

import math
import time
import numpy as np
from typing import Optional, List, Dict, Any, Tuple


# ---------------------------------------------------------------
# Residual monitor
# ---------------------------------------------------------------
class ResidualMonitor:
    """Watches the stream of window residuals for two distinct signatures:

    - LEAK: the exponentially weighted moving average (EWMA) of the relative
      residual sits above a floor — a steady, ongoing imbalance.
    - PHASE: a CUSUM statistic accumulates persistent one-sided drift past a
      threshold — the imbalance is not a fluctuation but a regime. This is
      the signal that an unmonitored dimension exists, and it is what
      licenses the ledger to expand.

    Both detectors are per-sample (one feed per window close), so the time
    constant tau is measured in windows, not seconds. Wall-clock timestamps
    are recorded on events but do not enter the smoothing — successive
    windows may close microseconds apart.
    """

    def __init__(self, tau: float = 10.0, threshold: float = 1.0,
                 cusum_threshold: float = 4.0, reference: float = 0.02):
        self.tau = tau
        self.threshold = threshold
        self.cusum_threshold = cusum_threshold
        # reference: relative residual regarded as "quiet". EWMA above
        # threshold*reference raises leak events; CUSUM accumulates the
        # excess of rel_residual over reference.
        self.reference = reference

        self.ewma = 0.0
        self.cusum = 0.0
        self.n_fed = 0
        self.events: List[Dict[str, Any]] = []

    def feed(self, t: float, rel_residual: float,
             n_e_net: float) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Ingest one window's residual summary.

        Returns (leaky_event, phase_event) — each an event dict or None."""
        self.n_fed += 1
        alpha = 1.0 - math.exp(-1.0 / self.tau)
        if self.n_fed == 1:
            self.ewma = rel_residual
        else:
            self.ewma += alpha * (rel_residual - self.ewma)

        # One-sided CUSUM: accumulate drift above the quiet reference.
        self.cusum = max(0.0, self.cusum + (rel_residual - self.reference))

        leaky_event = None
        if self.ewma > self.threshold * self.reference:
            leaky_event = {
                "t": t, "type": "leak",
                "ewma": self.ewma, "rel_residual": rel_residual,
                "n_e_net": n_e_net,
            }
            self.events.append(leaky_event)

        phase_event = None
        if self.cusum > self.cusum_threshold:
            phase_event = {
                "t": t, "type": "phase",
                "cusum": self.cusum, "windows_fed": self.n_fed,
                "n_e_net": n_e_net,
            }
            self.events.append(phase_event)
            self.cusum = 0.0  # re-arm after firing

        return leaky_event, phase_event


# ---------------------------------------------------------------
# Mandala configuration
# ---------------------------------------------------------------
class MandalaConfig:
    """Defines the known dimensions and their hierarchical relationships.
    The ledger expands according to this lattice, not arbitrarily.
    You can think of it as a pre-defined cosmic map of conserved quantities.
    """

    def __init__(self, root_dim: str = "charge", branches: Optional[Dict] = None):
        # branches: dict of parent_dim -> list of child_dims
        # e.g. {"charge": ["spin", "valley"], "spin": ["spin_x", "spin_y", "spin_z"]}
        self.root = root_dim
        self.branches = branches if branches is not None else {}
        # Keep a reverse lookup: child -> parent
        self.parent: Dict[str, str] = {}
        for parent, children in self.branches.items():
            for child in children:
                self.parent[child] = parent
        # Provenance of the most recent expand_dimension decision
        self.last_decision: Dict[str, Any] = {}

    def get_children(self, dim: str) -> List[str]:
        return self.branches.get(dim, [])

    def get_parent(self, dim: str) -> Optional[str]:
        return self.parent.get(dim, None)

    def expand_dimension(self, current_labels: List[str], residual_vector: np.ndarray,
                         monitor_events: List[Dict]) -> Optional[str]:
        """Given the current set of dimension labels and a persistent residual,
        decide which new dimension to add next.

        Strategy, in order:
        1. RESIDUAL-GUIDED: rank the currently monitored dimensions by the
           magnitude of their residual component and drill into the first
           unexplored child of the leakiest one. The leak tells you where
           the hidden degree of freedom hangs off the lattice.
        2. BREADTH-FIRST fallback: if no leaky dimension has unexplored
           children, take the first missing child walking out from the root.

        The reasoning behind the choice is recorded in self.last_decision.
        Returns the label of the new dimension, or None if no expansion is
        possible."""
        # --- 1. residual-guided drill into the leakiest branch ---
        if residual_vector is not None and len(residual_vector) == len(current_labels):
            ranked = sorted(range(len(current_labels)),
                            key=lambda i: -abs(float(residual_vector[i])))
            for i in ranked:
                component = float(residual_vector[i])
                if component == 0.0:
                    break  # remaining components carry no signal
                label = current_labels[i]
                for child in self.get_children(label):
                    if child not in current_labels:
                        self.last_decision = {
                            "strategy": "residual_guided",
                            "guided_by": label,
                            "component_index": i,
                            "component_residual": component,
                        }
                        return child

        # --- 2. breadth-first fallback from the root ---
        frontier = [self.root]
        while frontier:
            parent = frontier.pop(0)
            for child in self.get_children(parent):
                if child not in current_labels:
                    self.last_decision = {
                        "strategy": "breadth_first",
                        "guided_by": parent,
                    }
                    return child
                else:
                    frontier.append(child)
        self.last_decision = {"strategy": "exhausted"}
        return None  # no more dimensions known to mandala


# ---------------------------------------------------------------
# Symmetry-grounded mandala: lattice derived from the O_h group
# ---------------------------------------------------------------

# Standard crystallographic names for the 10 conjugacy classes of O_h,
# keyed by conjugacy_signature() = (determinant, trace, order, fixed_vertices).
_OH_CLASS_NAMES: Dict[Tuple[int, int, int, int], str] = {
    (1, 3, 1, 6):   "E",        # identity
    (1, 1, 4, 2):   "C4",       # 6 x 90-degree rotations (face axes)
    (1, -1, 2, 2):  "C4^2",     # 3 x 180-degree rotations (face axes)
    (1, 0, 3, 0):   "C3",       # 8 x 120-degree rotations (body diagonals)
    (1, -1, 2, 0):  "C2",       # 6 x 180-degree rotations (edge axes)
    (-1, -3, 2, 0): "i",        # spatial inversion
    (-1, -1, 4, 0): "S4",       # 6 x improper 90-degree rotations
    (-1, 1, 2, 4):  "sigma_h",  # 3 x horizontal mirror planes
    (-1, 0, 6, 0):  "S6",       # 8 x improper 60-degree rotations
    (-1, 1, 2, 2):  "sigma_d",  # 6 x diagonal mirror planes
}


def _class_name(sig: Tuple[int, int, int, int]) -> str:
    if sig in _OH_CLASS_NAMES:
        return _OH_CLASS_NAMES[sig]
    kind = "C" if sig[0] == 1 else "S"
    return f"{kind}{sig[2]}_t{sig[1]}f{sig[3]}"


class SymmetryMandalaConfig(MandalaConfig):
    """Mandala lattice derived from the O_h octahedral symmetry group
    (geometric_state_algebra.OhGroup) instead of hand-written branching rules.

    Noether-flavoured reading: each conserved quantity corresponds to a
    symmetry channel. The lattice is the conjugacy-class structure of O_h:

        root (identity class E — the always-monitored quantity)
        ├── C4^2 ── sigma_h     (each proper rotation class branches to
        ├── C2   ── sigma_d      its parity partner: the improper class
        ├── C3   ── S6           obtained by composing with inversion,
        ├── C4   ── S4           i . C)
        └── i                   (inversion itself: parity partner of E)

    That gives root + 9 channels = 10 dimensions, one per conjugacy class.
    Level 1 = rotational symmetry channels; level 2 = their parity-inverted
    partners — you only look for parity violation in a channel after the
    rotational channel itself failed to close the books.

    class_members maps each dimension label to the O_h element indices in
    its class (root maps to the identity class), so an expansion can be
    traced back to concrete group elements.
    """

    def __init__(self, root_dim: str = "charge", group=None):
        from geometric_state_algebra import OhGroup, GENERATOR_INV

        self.group = group if group is not None else OhGroup()
        inv_idx = self.group.index(GENERATOR_INV)

        identity_sig = (1, 3, 1, 6)
        sigs = list(self.group.conjugacy_classes.keys())
        proper_sigs = [s for s in sigs if s[0] == 1 and s != identity_sig]
        # Deterministic order: cheapest symmetry channels first
        # (low element order, then more fixed vertices).
        proper_sigs.sort(key=lambda s: (s[2], -s[3]))

        branches: Dict[str, List[str]] = {root_dim: []}
        self.class_members: Dict[str, List[int]] = {
            root_dim: list(self.group.conjugacy_classes[identity_sig]),
        }
        for sig in proper_sigs:
            name = _class_name(sig)
            branches[root_dim].append(name)
            self.class_members[name] = list(self.group.conjugacy_classes[sig])
            # Parity partner: class of (inversion . representative)
            rep = self.group.conjugacy_classes[sig][0]
            partner_idx = self.group.multiply(inv_idx, rep)
            partner_sig = self.group.elements[partner_idx].conjugacy_signature()
            partner = _class_name(partner_sig)
            branches[name] = [partner]
            self.class_members[partner] = list(
                self.group.conjugacy_classes[partner_sig])
        # Inversion class: parity partner of the identity, child of root
        inv_sig = self.group.elements[inv_idx].conjugacy_signature()
        inv_name = _class_name(inv_sig)
        branches[root_dim].append(inv_name)
        self.class_members[inv_name] = list(self.group.conjugacy_classes[inv_sig])

        self._distance_cache: Dict[Tuple[str, str], int] = {}
        super().__init__(root_dim=root_dim, branches=branches)

    def class_distance(self, label_a: str, label_b: str) -> int:
        """Cayley-graph distance between two dimension channels: the minimum
        generator-word distance between any element of class A and any element
        of class B. This is the group's own metric on the lattice — e.g. every
        parity partner i.C sits exactly one step (one inversion) from C."""
        if label_a == label_b:
            return 0
        key = (label_a, label_b) if label_a < label_b else (label_b, label_a)
        if key not in self._distance_cache:
            self._distance_cache[key] = min(
                self.group.distance(i, j)
                for i in self.class_members[label_a]
                for j in self.class_members[label_b])
        return self._distance_cache[key]

    def expand_dimension(self, current_labels: List[str], residual_vector: np.ndarray,
                         monitor_events: List[Dict]) -> Optional[str]:
        """Cayley-guided expansion: candidates are the unexplored children of
        every monitored dimension, and the winner is the one whose conjugacy
        class is NEAREST (in the Cayley graph) to the class of the leakiest
        dimension. The group metric — not component magnitude alone — steers
        the drill: a leak in a symmetry channel points to the degrees of
        freedom a single generator step away.

        Ties break toward the leaky dimension's own children (candidates are
        enumerated in descending residual order), so a parity partner at
        distance 1 beats a sibling class at distance 1. Falls back to the
        base residual-guided / breadth-first strategy when there is no usable
        residual signal."""
        usable = (residual_vector is not None
                  and len(residual_vector) == len(current_labels)
                  and float(np.max(np.abs(residual_vector))) > 0.0)
        if not usable:
            return super().expand_dimension(current_labels, residual_vector,
                                            monitor_events)

        ranked = sorted(range(len(current_labels)),
                        key=lambda i: -abs(float(residual_vector[i])))
        dominant = current_labels[ranked[0]]
        if dominant not in self.class_members:
            return super().expand_dimension(current_labels, residual_vector,
                                            monitor_events)

        # Frontier: unexplored children of monitored dims, leakiest dims first
        candidates: List[str] = []
        for i in ranked:
            for child in self.get_children(current_labels[i]):
                if child not in current_labels and child not in candidates:
                    candidates.append(child)
        if not candidates:
            return super().expand_dimension(current_labels, residual_vector,
                                            monitor_events)

        scored = [(self.class_distance(dominant, c), idx, c)
                  for idx, c in enumerate(candidates)]
        dist, _, choice = min(scored)
        self.last_decision = {
            "strategy": "cayley_guided",
            "guided_by": dominant,
            "component_residual": float(residual_vector[ranked[0]]),
            "cayley_distance": dist,
            "candidate_distances": {c: d for d, _, c in sorted(scored)},
        }
        return choice


# ---------------------------------------------------------------
# ExpandableMultiLedger
# ---------------------------------------------------------------
class ExpandableMultiLedger:
    """Ledger whose dimension set can grow automatically when a persistent
    residual is detected. Uses a MandalaConfig for guided expansion.

    The key idea: every conservation violation is just a transfer into an
    unmonitored dimension. The ledger self-repairs by absorbing past imbalance
    into a new "environment" account, then resuming normal closure.
    """

    def __init__(self,
                 mandala: Optional[MandalaConfig] = None,
                 initial_dim: int = 1,
                 chi2_thresh: float = 11.07,
                 tau_expand: float = 10.0,   # time constant for residual monitor
                 cusum_thresh: float = 4.0,
                 tolerance: float = 1e-9,
                 ):
        self.mandala = mandala if mandala is not None else MandalaConfig()
        self.dim = initial_dim
        self.chi2_thresh = chi2_thresh
        self.tolerance = tolerance

        # Dimension labels (ordered, length = dim)
        self.labels = [self.mandala.root]  # start with root dimension

        # Residual monitor for expansion trigger
        self.monitor = ResidualMonitor(tau=tau_expand, threshold=1.0,
                                       cusum_threshold=cusum_thresh)

        # Ledger entries: each entry is a dict with 'c' (vector of length dim),
        # 'dir', 'src', 't'
        self.entries: List[Dict[str, Any]] = []
        self.residual_trajectory: List[Dict[str, Any]] = []

        # An "environment bin" vector that accumulates past leakage.
        # At expansion, this is cleared and its content moved to a new dimension.
        self.env_balance = np.zeros(self.dim)  # always matches current dim

    def post(self, direction: str, c_vector: List[float], source: str,
             t: Optional[float] = None):
        """Post a vector entry. c_vector length must equal current dim."""
        if len(c_vector) != self.dim:
            raise ValueError(f"c_vector length {len(c_vector)} != dim {self.dim}")
        if direction not in ("in", "out", "store"):
            raise ValueError(f"direction must be 'in', 'out' or 'store', got {direction!r}")
        self.entries.append({
            "dir": direction,
            "c": np.array(c_vector, dtype=float),
            "src": source,
            "t": t if t is not None else time.time(),
        })

    def close_window(self) -> Dict:
        """Close current window, check conservation, attempt expansion if needed."""
        if not self.entries:
            return {"t": time.time(), "residual": np.zeros(self.dim).tolist(),
                    "closes": True, "expanded": False}

        s_in = np.zeros(self.dim)
        s_out = np.zeros(self.dim)
        s_sto = np.zeros(self.dim)
        for e in self.entries:
            c = e["c"]
            if e["dir"] == "in":
                s_in += c
            elif e["dir"] == "out":
                s_out += c
            else:
                s_sto += c

        residual = s_in - s_out - s_sto + self.env_balance  # account for past leakage
        # Total counts for precision — include the env content that entered
        # the residual, BEFORE resetting it.
        total_counts = (np.abs(s_in) + np.abs(s_out) + np.abs(s_sto)
                        + np.abs(self.env_balance))
        self.env_balance = np.zeros(self.dim)  # reset after absorbing

        precision = np.diag(1.0 / (total_counts + 1e-12))
        mahalanobis_sq = float(residual @ precision @ residual)
        closes = mahalanobis_sq <= self.chi2_thresh

        record = {
            "t": time.time(),
            "residual": residual.tolist(),
            "mahalanobis_sq": mahalanobis_sq,
            "closes": closes,
            "dim": self.dim,
            "labels": self.labels.copy(),
        }

        # Feed monitor with net residual (scalar proxy: norm of the residual
        # relative to the norm of total activity).
        rel_residual = np.linalg.norm(residual) / (np.linalg.norm(total_counts) + 1e-12)
        leaky_event, phase_event = self.monitor.feed(
            t=record["t"],
            rel_residual=rel_residual,
            n_e_net=float(np.linalg.norm(residual)),
        )

        if phase_event is not None and not closes:
            # Attempt expansion guided by mandala
            new_dim_label = self.mandala.expand_dimension(self.labels, residual,
                                                          self.monitor.events)
            if new_dim_label is not None:
                self._expand(new_dim_label, residual)
                record["expanded"] = True
                record["new_dimension"] = new_dim_label
                record["expansion_reason"] = dict(self.mandala.last_decision)
            else:
                record["expanded"] = False
        else:
            record["expanded"] = False

        self.residual_trajectory.append(record)
        self.entries.clear()
        return record

    def _expand(self, new_label: str, residual: np.ndarray):
        """Add a new dimension and retroactively absorb the residual into it.

        The residual is treated as a transfer OUT of the old space and INTO
        the new dimension. For overall conservation (total sum = 0) the new
        dimension's opening balance is minus the total old imbalance:

            env_balance_new = [old env (zeros), -sum(residual_old)]

        On the next close_window, this debt is added to the residual. When the
        newly instrumented channel reports the recovered leakage (an audit
        inflow of +sum(residual_old) in the new component), the two cancel and
        the expanded window closes.
        """
        old_dim = self.dim
        # Extend dimension
        self.dim += 1
        self.labels.append(new_label)

        new_env = np.zeros(self.dim)
        new_env[:old_dim] = self.env_balance  # should be zeros but be safe
        new_env[-1] = -np.sum(residual)  # absorb total old imbalance into new dim
        self.env_balance = new_env

        # Reset the residual monitor for the new dimensionality
        self.monitor = ResidualMonitor(tau=self.monitor.tau,
                                       threshold=self.monitor.threshold,
                                       cusum_threshold=self.monitor.cusum_threshold,
                                       reference=self.monitor.reference)


# ---------------------------------------------------------------
# Self-test: charge-only ledger meets a spin-leaking device
# ---------------------------------------------------------------
def run_self_test(verbose: bool = True) -> bool:
    """Start with charge only, feed a spin-leaking sequence, and watch the
    ledger add a 'spin' dimension and then close the window.

    Scenario: a device injects 100 units of charge per window but the drain
    only collects 50 — the other 50 leave via a spin-flip channel nobody is
    monitoring. The charge-only ledger sees a gross, persistent residual.
    After enough windows the CUSUM phase detector fires, the mandala lattice
    says the first unexplored child of 'charge' is 'spin', and the ledger
    expands. A reconciliation window then audits the newly visible spin
    reservoir, recovers the historical leak, and closes exactly.
    """
    def log(msg):
        if verbose:
            print(msg)

    mandala = MandalaConfig(
        root_dim="charge",
        branches={
            "charge": ["spin", "valley"],
            "spin": ["spin_x", "spin_y", "spin_z"],
        },
    )
    ledger = ExpandableMultiLedger(mandala=mandala, initial_dim=1)

    log("=" * 64)
    log("ExpandableMultiLedger self-test: spin-leaking device")
    log("=" * 64)
    log(f"start: dim={ledger.dim} labels={ledger.labels}")

    # --- Phase 1: charge-only windows with a hidden spin leak -----------
    expansion_record = None
    max_windows = 30
    for w in range(1, max_windows + 1):
        ledger.post("in", [100.0], "injector")
        ledger.post("out", [50.0], "drain")   # 50 units vanish each window
        rec = ledger.close_window()
        log(f"window {w:2d}: residual={rec['residual']}"
            f"  chi2={rec['mahalanobis_sq']:.2f}"
            f"  closes={rec['closes']}  expanded={rec['expanded']}")
        assert not rec["closes"], "leaking window should NOT close"
        if rec["expanded"]:
            expansion_record = rec
            break

    assert expansion_record is not None, \
        f"ledger failed to expand within {max_windows} windows"
    assert expansion_record["new_dimension"] == "spin", \
        f"mandala should propose 'spin' first, got {expansion_record['new_dimension']}"
    assert ledger.dim == 2 and ledger.labels == ["charge", "spin"]
    log(f"\n>>> EXPANSION: added dimension '{expansion_record['new_dimension']}'"
        f" -> labels={ledger.labels}")
    log(f"    env_balance carries retro-debt: {ledger.env_balance.tolist()}")

    # --- Phase 2: reconciliation window in the expanded space -----------
    # The spin-flip channel is now instrumented: the 50 leaked charge units
    # are measured leaving, and an audit of the spin reservoir recovers the
    # 50 units of historical leakage the env account owes.
    ledger.post("in", [100.0, 0.0], "injector")
    ledger.post("out", [50.0, 0.0], "drain")
    ledger.post("out", [50.0, 0.0], "spin_flip_channel")   # leak, now visible
    ledger.post("in", [0.0, 50.0], "spin_reservoir_audit")  # historical leak found
    rec = ledger.close_window()
    log(f"\nreconciliation window: residual={rec['residual']}"
        f"  chi2={rec['mahalanobis_sq']:.4f}  closes={rec['closes']}")
    assert rec["closes"], "reconciliation window should close"
    assert rec["dim"] == 2
    assert max(abs(r) for r in rec["residual"]) < 1e-9, \
        "reconciliation should cancel the retro-debt exactly"

    # --- Phase 3: steady state, fully instrumented ----------------------
    ledger.post("in", [100.0, 0.0], "injector")
    ledger.post("out", [50.0, 0.0], "drain")
    ledger.post("out", [50.0, 0.0], "spin_flip_channel")
    rec = ledger.close_window()
    log(f"steady-state window:   residual={rec['residual']}"
        f"  chi2={rec['mahalanobis_sq']:.4f}  closes={rec['closes']}")
    assert rec["closes"], "fully instrumented window should close"
    assert not rec["expanded"], "no further expansion should be needed"

    # --- Sanity: mandala BFS order and exhaustion ------------------------
    nxt = mandala.expand_dimension(ledger.labels, np.zeros(2), [])
    assert nxt == "valley", f"next BFS candidate should be 'valley', got {nxt}"
    all_dims = ["charge", "spin", "valley", "spin_x", "spin_y", "spin_z"]
    assert mandala.expand_dimension(all_dims, np.zeros(6), []) is None, \
        "exhausted mandala should return None"

    log("\nALL CHECKS PASSED — ledger leaked, expanded into 'spin', and closed.")
    return True


def run_guided_drill_test(verbose: bool = True) -> bool:
    """Residual-guided selection: when the leak shows up in a specific
    component, the mandala drills into THAT branch instead of walking
    breadth-first.

    After the first expansion (charge -> spin), the spin channel itself
    starts leaking: 40 units of spin enter per window and never come out
    (they decohere into an unmonitored spin_x sub-channel). Breadth-first
    would propose 'valley' next; residual guidance must propose 'spin_x',
    because the residual lives in the spin component.
    """
    def log(msg):
        if verbose:
            print(msg)

    mandala = MandalaConfig(
        root_dim="charge",
        branches={
            "charge": ["spin", "valley"],
            "spin": ["spin_x", "spin_y", "spin_z"],
        },
    )
    ledger = ExpandableMultiLedger(mandala=mandala, initial_dim=1)

    log("=" * 64)
    log("Guided-drill test: leak concentrated in the spin component")
    log("=" * 64)

    # Stage 1: reach ['charge', 'spin'] via the charge-leak scenario.
    for _ in range(30):
        ledger.post("in", [100.0], "injector")
        ledger.post("out", [50.0], "drain")
        rec = ledger.close_window()
        if rec["expanded"]:
            break
    assert ledger.labels == ["charge", "spin"], f"stage 1 failed: {ledger.labels}"
    # Reconcile so the retro-debt doesn't pollute stage 2.
    ledger.post("in", [100.0, 0.0], "injector")
    ledger.post("out", [50.0, 0.0], "drain")
    ledger.post("out", [50.0, 0.0], "spin_flip_channel")
    ledger.post("in", [0.0, 50.0], "spin_reservoir_audit")
    rec = ledger.close_window()
    assert rec["closes"]
    log(f"stage 1: expanded to {ledger.labels}, reconciled")

    # Stage 2: charge balances, spin leaks — residual = [0, 40] per window.
    expansion_record = None
    for w in range(1, 40):
        ledger.post("in", [100.0, 40.0], "injector")
        ledger.post("out", [50.0, 0.0], "drain")
        ledger.post("out", [50.0, 0.0], "spin_flip_channel")
        rec = ledger.close_window()
        assert not rec["closes"], "spin-leaking window should NOT close"
        if rec["expanded"]:
            expansion_record = rec
            log(f"stage 2: window {w} residual={rec['residual']}"
                f" -> expanded into '{rec['new_dimension']}'")
            break

    assert expansion_record is not None, "stage 2 never expanded"
    assert expansion_record["new_dimension"] == "spin_x", \
        (f"guided expansion should drill into 'spin_x' (leak is in spin), "
         f"got {expansion_record['new_dimension']}")
    reason = expansion_record["expansion_reason"]
    assert reason["strategy"] == "residual_guided", reason
    assert reason["guided_by"] == "spin", reason
    log(f"decision provenance: {reason}")
    log("\nGUIDED DRILL PASSED — mandala followed the leak into spin_x,"
        " not breadth-first valley.")
    return True


def run_symmetry_mandala_test(verbose: bool = True) -> bool:
    """SymmetryMandalaConfig: the lattice is derived from the O_h group's
    conjugacy-class structure, not hand-written. Checks the Noether-style
    shape (proper rotation classes under the root, parity partners below
    them), then runs a leaky ledger over it and watches expansion walk
    the group lattice until exhaustion.
    """
    def log(msg):
        if verbose:
            print(msg)

    mandala = SymmetryMandalaConfig(root_dim="charge")

    log("=" * 64)
    log("Symmetry mandala test: lattice from O_h conjugacy classes")
    log("=" * 64)

    # Structure: root + 9 channels = 10 conjugacy classes.
    all_dims = [mandala.root] + [d for kids in mandala.branches.values()
                                 for d in kids]
    assert len(all_dims) == 10, f"expected 10 dimensions, got {len(all_dims)}"
    assert set(mandala.branches[mandala.root]) == {"C4^2", "C2", "C3", "C4", "i"}
    # Parity partners: i . C for each proper rotation class.
    partners = {"C4": "S4", "C4^2": "sigma_h", "C3": "S6", "C2": "sigma_d"}
    for proper, improper in partners.items():
        assert mandala.branches[proper] == [improper], \
            f"parity partner of {proper} should be {improper}"
    # Class members cover the whole group: 48 elements across 10 classes.
    covered = sum(len(v) for v in mandala.class_members.values())
    assert covered == 48, f"class members cover {covered} of 48 elements"
    log(f"lattice: root '{mandala.root}' -> {mandala.branches[mandala.root]}")
    log(f"parity partners: {partners}")
    log(f"class members cover all {covered} O_h elements")

    # Cayley metric sanity: every parity partner is exactly one inversion
    # step from its proper class.
    for proper, improper in partners.items():
        d = mandala.class_distance(proper, improper)
        assert d == 1, f"d({proper},{improper}) should be 1, got {d}"
    log("Cayley metric: every parity partner i.C sits at distance 1 from C")

    # Run a leaky ledger over the group lattice. Expansion is CAYLEY-GUIDED:
    # the winner is the frontier class nearest (in the Cayley graph) to the
    # class of the leaking dimension. From the root (identity class E) the
    # nearest channels are the generators themselves: C4 and i at distance 1.
    # C4 is enumerated first, so the drill goes there — NOT to list-order
    # C4^2, which sits two generator steps away.
    ledger = ExpandableMultiLedger(mandala=mandala, initial_dim=1)
    expansion_record = None
    for _ in range(30):
        ledger.post("in", [100.0], "injector")
        ledger.post("out", [50.0], "drain")
        rec = ledger.close_window()
        if rec["expanded"]:
            expansion_record = rec
            break
    assert expansion_record is not None, "symmetry ledger never expanded"
    assert expansion_record["new_dimension"] == "C4", \
        f"nearest channel to E is C4 (distance 1), got {expansion_record['new_dimension']}"
    reason = expansion_record["expansion_reason"]
    assert reason["strategy"] == "cayley_guided" and reason["cayley_distance"] == 1
    assert ledger.labels == ["charge", "C4"]
    log(f"\nroot leak -> expanded into '{expansion_record['new_dimension']}'"
        f" (Cayley distance 1 from E)")
    log(f"candidate distances: {reason['candidate_distances']}")

    # Reconcile, then leak in the C4 channel itself. Ties at distance 1
    # (S4, C4^2, C3) break toward the leaky dimension's own child: the
    # parity partner S4 — one inversion away from C4.
    ledger.post("in", [100.0, 0.0], "injector")
    ledger.post("out", [50.0, 0.0], "drain")
    ledger.post("out", [50.0, 0.0], "c4_channel")
    ledger.post("in", [0.0, 50.0], "c4_reservoir_audit")
    assert ledger.close_window()["closes"], "symmetry reconciliation failed"

    expansion_record = None
    for _ in range(40):
        ledger.post("in", [100.0, 40.0], "injector")
        ledger.post("out", [50.0, 0.0], "drain")
        ledger.post("out", [50.0, 0.0], "c4_channel")
        rec = ledger.close_window()
        if rec["expanded"]:
            expansion_record = rec
            break
    assert expansion_record is not None, "C4-leak never expanded"
    assert expansion_record["new_dimension"] == "S4", \
        f"C4 leak should drill into parity partner S4, got {expansion_record['new_dimension']}"
    reason = expansion_record["expansion_reason"]
    assert reason["guided_by"] == "C4" and reason["cayley_distance"] == 1
    log(f"C4 leak -> expanded into parity partner"
        f" '{expansion_record['new_dimension']}' (one inversion step)")

    # Exhaustion: once every class channel is monitored, the mandala is done.
    every_dim = list(all_dims)
    assert mandala.expand_dimension(every_dim, np.zeros(len(every_dim)), []) is None
    log("exhaustion check passed: full lattice -> no further expansion")
    log("\nSYMMETRY MANDALA PASSED — branching derived from O_h and the"
        " drill steered by its Cayley metric.")
    return True


if __name__ == "__main__":
    run_self_test()
    print()
    run_guided_drill_test()
    print()
    run_symmetry_mandala_test()
