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

    def get_children(self, dim: str) -> List[str]:
        return self.branches.get(dim, [])

    def get_parent(self, dim: str) -> Optional[str]:
        return self.parent.get(dim, None)

    def expand_dimension(self, current_labels: List[str], residual_vector: np.ndarray,
                         monitor_events: List[Dict]) -> Optional[str]:
        """Given the current set of dimension labels and a persistent residual,
        decide which new dimension to add next. Default strategy:
        start at the root and expand breadth-first. If a phase change is detected
        in a particular component, follow that path.

        Returns the label of the new dimension, or None if no expansion is possible."""
        # Take the first missing child of the root or its descendants,
        # breadth-first. A more sophisticated version would use the residual
        # vector's largest component to pick which branch to follow.
        frontier = [self.root]
        while frontier:
            parent = frontier.pop(0)
            for child in self.get_children(parent):
                if child not in current_labels:
                    return child
                else:
                    frontier.append(child)
        return None  # no more dimensions known to mandala


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


if __name__ == "__main__":
    run_self_test()
