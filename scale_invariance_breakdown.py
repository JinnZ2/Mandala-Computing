"""
scale_invariance_breakdown.py

Generic epistemology pattern (CC0): identifies WHERE in a system genuine
non-scale-invariance might appear, versus where an apparent breakdown
reduces to measurement error, a substrate change, or a framing gap.

Per-repo/per-domain instantiations reuse this module's dataclasses and
constants to hunt for genuine breakdowns in their own system rather than
redefining the same shapes locally. See mandala_scale_invariance_breakdown.py
in this repo for the Mandala-Computing instantiation.

Core idea: most claimed "this doesn't scale" or "this breaks at extremes"
observations are NOT genuine scale-invariance breakdowns. They usually
reduce to one of three tiers (see PROOF_PROTOCOL_TIERS below) before
they're worth treating as real, publishable information about how a
system actually behaves across scales.

License: CC0
Dependencies: Python stdlib only
"""

from dataclasses import dataclass
from typing import Dict, Tuple


# ---------------------------------------------------------------------------
# The five generic classes of genuine scale-invariance breakdown
# ---------------------------------------------------------------------------

BREAKDOWN_CLASSES: Dict[str, str] = {
    "phase_transitions": (
        "A smooth, continuous parameter change produces a discontinuous "
        "change in system behavior at a critical point (e.g. water -> ice). "
        "First-order: the property itself jumps. Second-order: the property "
        "stays continuous but a derivative of it diverges."
    ),
    "catastrophe_topology": (
        "The system's stable-state surface folds back on itself (one of "
        "Thom's elementary catastrophes: fold, cusp, swallowtail, ...), "
        "producing hysteresis -- the forward and reverse paths through a "
        "parameter range disagree, unlike a phase transition's "
        "single-valued curve."
    ),
    "information_theoretic_limits": (
        "A boundary/coarse representation cannot encode enough information "
        "to determine the interior/fine behavior beyond some ratio (e.g. "
        "the Bekenstein bound, the holographic principle, channel-capacity "
        "limits). Degradation shows as a hard cliff at the information "
        "limit, not a gradual decline."
    ),
    "quantum_measurement_boundary": (
        "Behavior differs qualitatively depending on which substrate "
        "(classical vs quantum, discrete vs continuous) implements the "
        "same nominal computation or process -- a substrate change "
        "masquerading as a scale change."
    ),
    "symmetry_breaking": (
        "A system with an exact symmetry at one scale loses that symmetry "
        "(spontaneously, or via an explicit perturbation) at another "
        "scale, producing qualitatively distinct behavior classes on "
        "either side of the breaking point."
    ),
}


# ---------------------------------------------------------------------------
# The three-tier proof protocol
#
# A candidate breakdown must survive all three tiers, in order, before
# it is treated as real rather than an artifact.
# ---------------------------------------------------------------------------

PROOF_PROTOCOL_TIERS: Dict[int, Tuple[str, str]] = {
    1: (
        "metrology",
        "Is the measurement itself reliable? Re-run against a known-good "
        "baseline before trusting an anomalous result.",
    ),
    2: (
        "substrate_crossover",
        "Did the underlying substrate/implementation change at the "
        "boundary (e.g. classical to quantum, float to fixed-point)? If "
        "so, this is a substrate boundary, not a scale-invariance "
        "breakdown -- reclassify rather than claim novelty.",
    ),
    3: (
        "dimensional_frame_exhaustion",
        "Did the description run out of the units/dimensions needed to "
        "characterize the new regime? A representational limit reads as "
        "a breakdown but is actually a framing gap -- extend the frame "
        "before concluding the system itself broke down.",
    ),
}


# ---------------------------------------------------------------------------
# Shared dataclasses -- reused (not redefined) by per-repo instantiations
# ---------------------------------------------------------------------------

@dataclass
class CandidateBreakdown:
    location: str            # Where in the system the breakdown might appear
    predicted_class: str     # A key from BREAKDOWN_CLASSES
    repo_evidence: str       # What currently hints at this
    experiment: str          # How to test if the breakdown is real
    falsifier: str           # What measurement would rule it out


@dataclass
class FalsifiableClaim:
    claim_id: str
    statement: str
    measurement: str
    threshold: str
    substrate: str
    status: str = "untested"


@dataclass
class AuditGate:
    marker: str
    green_threshold: str
    yellow_threshold: str
    red_threshold: str
    action_on_red: str


# ---------------------------------------------------------------------------
# Generic operator note -- per-repo instantiations should write their own
# domain-specific version (see REPO_OPERATOR_NOTE in
# mandala_scale_invariance_breakdown.py for the pattern to follow).
# ---------------------------------------------------------------------------

OPERATOR_NOTE = """
SCALE-INVARIANCE BREAKDOWN HUNTING -- GENERIC DIRECTIVE:

Most claimed "this breaks down at scale" observations are not genuine.
Before treating an anomaly as a real scale-invariance breakdown:

  1. Classify it against the five generic classes above (phase transition,
     catastrophe topology, information-theoretic limit, quantum measurement
     boundary, symmetry breaking) -- or note that it fits none of them,
     which is itself informative.

  2. Run it through all three proof-protocol tiers (metrology, substrate
     crossover, dimensional frame exhaustion) before concluding the
     breakdown is real. Most candidates reduce at tier 1 or 2.

  3. A candidate that survives all three tiers encodes real information
     about the system. Document the experiment and falsifier precisely --
     that is what makes it a contribution rather than an anecdote.

Per-repo instantiations should replace this note with a domain-specific
version naming their own substrates/modules, following the pattern in
mandala_scale_invariance_breakdown.py.
"""


def list_breakdown_classes() -> str:
    lines = ["FIVE GENERIC BREAKDOWN CLASSES:", ""]
    for name, desc in BREAKDOWN_CLASSES.items():
        lines.append(f"  {name}:")
        lines.append(f"    {desc}")
        lines.append("")
    return "\n".join(lines)


def list_proof_protocol() -> str:
    lines = ["THREE-TIER PROOF PROTOCOL:", ""]
    for tier, (name, desc) in sorted(PROOF_PROTOCOL_TIERS.items()):
        lines.append(f"  Tier {tier} ({name}):")
        lines.append(f"    {desc}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print(list_breakdown_classes())
    print(list_proof_protocol())
    print(OPERATOR_NOTE)
