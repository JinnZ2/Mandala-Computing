"""
mandala_scale_invariance_breakdown.py

Mandala-Computing-specific instantiation of scale_invariance_breakdown.py
Repo: github.com/JinnZ2/Mandala-Computing

Identifies WHERE in the Mandala-Computing framework genuine
non-scale-invariance might appear, and the experiments that would
either confirm or rule out each candidate.

The repo is unusually well-positioned to find genuine breakdowns
because it operates the same problem class (factorization, SAT,
graph coloring) across multiple scales and substrates simultaneously.
That cross-comparison IS the three-tier proof protocol applied to
computational substrates.

License: CC0
Dependencies: Python stdlib only
"""

from typing import List

from scale_invariance_breakdown import (
    CandidateBreakdown,
    FalsifiableClaim,
    AuditGate,
    BREAKDOWN_CLASSES,
    PROOF_PROTOCOL_TIERS,
)


REPO_URL = "github.com/JinnZ2/Mandala-Computing"


# ---------------------------------------------------------------------------
# Candidate breakdown locations specific to this repo
#
# predicted_class values below are keys into BREAKDOWN_CLASSES (imported
# from scale_invariance_breakdown.py) -- see that module for the five
# generic class definitions.
# ---------------------------------------------------------------------------

REPO_CANDIDATES = [
    CandidateBreakdown(
        location="classical -> quantum transition in solver selection",
        predicted_class="quantum_measurement_boundary",
        repo_evidence=(
            "quantum_mandala.py vs mandala_computer.py — same problem class, "
            "different substrate. README notes quantum methods 'best for small "
            "Hilbert spaces' which is itself a substrate-specific limit."
        ),
        experiment=(
            "Run factorization of identical N on both substrates at increasing "
            "system size. Look for N where one substrate succeeds and the other "
            "fails despite equivalent computational budget."
        ),
        falsifier=(
            "If failure transition is smooth (probabilistic crossover), no "
            "genuine breakdown — just scaling. If transition is sharp (binary "
            "go/no-go at specific N), candidate breakdown."
        ),
    ),
    CandidateBreakdown(
        location="exact glyph factorization vs probabilistic annealing",
        predicted_class="information_theoretic_limits",
        repo_evidence=(
            "README states 'exact glyph factorization always works' but "
            "'simulated annealing finds 13*17=221 ~20% success rate.' Two "
            "different epistemic statuses for the same problem."
        ),
        experiment=(
            "Find N where exact glyph factorization runtime exceeds annealing "
            "runtime even at low annealing success rate. The crossover point "
            "encodes a real boundary between deterministic and stochastic regimes."
        ),
        falsifier=(
            "If crossover is smooth and predictable from problem size alone, "
            "no breakdown. If crossover shows non-smooth structure (sudden "
            "regime shift), candidate breakdown in complexity-class transition."
        ),
    ),
    CandidateBreakdown(
        location="holographic renormalization boundary at coarsest scale",
        predicted_class="information_theoretic_limits",
        repo_evidence=(
            "holographic_mandala.py implements coarse-to-fine sweeps. There "
            "must be a coarsest scale beyond which the boundary cannot encode "
            "the bulk — analogous to Bekenstein bound in physics."
        ),
        experiment=(
            "Increase problem size while holding coarsest holographic scale "
            "fixed. Measure where renormalization breaks down (solution quality "
            "drops sharply)."
        ),
        falsifier=(
            "If degradation is gradual, no breakdown. If degradation shows "
            "hard cliff, candidate breakdown — possibly encoding a Bekenstein-"
            "analog limit for this computational substrate."
        ),
    ),
    CandidateBreakdown(
        location="pack resonance under extreme resource scarcity",
        predicted_class="catastrophe_topology",
        repo_evidence=(
            "sovereign_integration.py models pack dynamics. README shows three "
            "pack types with resonance 0.13, 0.25, 0.40. The threshold between "
            "'not sovereign' and 'sovereign' may be a cusp catastrophe."
        ),
        experiment=(
            "Vary resource scarcity continuously while holding pack composition "
            "fixed. Track resonance. Look for hysteresis (forward and reverse "
            "paths differ) or non-smooth boundary."
        ),
        falsifier=(
            "If resonance varies smoothly with scarcity, no breakdown. If "
            "hysteresis or discontinuity appears, candidate cusp catastrophe — "
            "matches Thom's catalog."
        ),
    ),
    CandidateBreakdown(
        location="claim_validator tier boundaries (Physics > Biology > Systems > Empirical)",
        predicted_class="information_theoretic_limits",
        repo_evidence=(
            "claim_validator.py implements 4-tier validation where higher "
            "tiers cannot override lower-tier violations. These tier boundaries "
            "are themselves a candidate breakdown — they assert a hard ordering."
        ),
        experiment=(
            "Find claims that violate lower-tier but succeed at higher-tier. "
            "Verify the validator correctly rejects them. Then look for edge "
            "cases where the tier boundary itself is ambiguous."
        ),
        falsifier=(
            "If all edge cases reduce to clear tier assignment, no breakdown. "
            "If genuine ambiguity exists (claim that is simultaneously physics "
            "and biology), candidate breakdown in the tier ontology itself."
        ),
    ),
    CandidateBreakdown(
        location="octahedral 8-state cell at small N (N <= 8) edge cases",
        predicted_class="phase_transitions",
        repo_evidence=(
            "octahedral_arithmetic.py operates natively in base-8. At N <= 8 "
            "the encoding overlaps with single-cell representation, which may "
            "be a degenerate case (system size = unit size)."
        ),
        experiment=(
            "Profile solver behavior at N = 2, 3, 5, 7, 8, 9, 11. Look for "
            "discontinuity in success rate or runtime crossing the single-cell "
            "boundary at N = 7 -> N = 8."
        ),
        falsifier=(
            "If behavior is continuous, no breakdown — small-N is just an edge "
            "case. If discontinuity exists, candidate 1st-order phase transition "
            "between single-cell and multi-cell regimes."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Specific falsifiable claims for Mandala-Computing breakdown hunting
# ---------------------------------------------------------------------------

REPO_BREAKDOWN_CLAIMS = [
    FalsifiableClaim(
        claim_id="MAN-SIB-001",
        statement=(
            "Mandala-Computing's six candidate breakdown locations are not "
            "all genuine; at least four will reduce to metrology or framing "
            "error under the three-tier proof protocol"
        ),
        measurement=(
            "Run all six candidate experiments. Apply tier 1 (metrology), "
            "tier 2 (substrate crossover), tier 3 (dimensional frame "
            "exhaustion) to each."
        ),
        threshold=">= 4 of 6 candidates reduce to non-breakdown",
        substrate="meta (repo testing)",
    ),
    FalsifiableClaim(
        claim_id="MAN-SIB-002",
        statement=(
            "Classical-to-quantum substrate transition for factorization in "
            "Mandala-Computing IS a genuine substrate change, not a scale "
            "change — therefore not a true scale-invariance breakdown but a "
            "different category"
        ),
        measurement=(
            "Compare quantum_mandala factorization success vs classical for "
            "matched N over wide range. Test if transition is smooth or sharp."
        ),
        threshold=(
            "If transition shows hard cliff at specific N where quantum "
            "succeeds and classical fails (or vice versa) despite equivalent "
            "compute budget, classify as substrate boundary not scale boundary"
        ),
        substrate="classical vs quantum (numpy vs numpy+scipy)",
    ),
    FalsifiableClaim(
        claim_id="MAN-SIB-003",
        statement=(
            "Pack resonance threshold in sovereign_integration.py exhibits "
            "cusp catastrophe topology under resource scarcity"
        ),
        measurement=(
            "Vary resource budget continuously from 100% to 10% of normal. "
            "Track resonance for three pack types (homogeneous, diverse-moderate, "
            "diverse-strong). Look for hysteresis or discontinuity."
        ),
        threshold=(
            "Cusp catastrophe confirmed if forward and reverse paths through "
            "scarcity differ by >= 15% in resonance at any scarcity level"
        ),
        substrate="Python stdlib (sovereign_integration.py)",
    ),
    FalsifiableClaim(
        claim_id="MAN-SIB-004",
        statement=(
            "Holographic renormalization in holographic_mandala.py encodes an "
            "information-theoretic limit analogous to Bekenstein bound at the "
            "coarsest scale"
        ),
        measurement=(
            "Hold coarsest holographic scale fixed. Increase problem size. "
            "Measure solution quality (energy gap from true minimum)."
        ),
        threshold=(
            "Bekenstein-analog confirmed if quality drops with sharp cliff at "
            "specific boundary-to-bulk ratio, not gradual degradation"
        ),
        substrate="numpy (holographic_mandala.py)",
    ),
]


# ---------------------------------------------------------------------------
# Audit gates specific to breakdown hunting in Mandala-Computing
# ---------------------------------------------------------------------------

MODULE_AUDIT_GATES = [
    AuditGate(
        marker="substrate_vs_scale_conflation",
        green_threshold=(
            "claim distinguishes substrate boundary (classical/quantum) from "
            "scale boundary (small-N/large-N)"
        ),
        yellow_threshold="claim acknowledges distinction but does not specify",
        red_threshold="claim conflates substrate change with scale breakdown",
        action_on_red=(
            "re-classify: substrate boundary requires different ontology than "
            "scale boundary; use MAN-SIB-002 protocol"
        ),
    ),
    AuditGate(
        marker="solver_failure_misattribution",
        green_threshold=(
            "solver failure attributed to specific known cause (local minimum, "
            "temperature schedule, bond dimension limit, etc.)"
        ),
        yellow_threshold="solver failure attributed to problem class",
        red_threshold=(
            "solver failure attributed to fundamental non-scale-invariance "
            "without ruling out implementation cause"
        ),
        action_on_red=(
            "halt; run tier 1 metrology re-check before claiming fundamental "
            "breakdown"
        ),
    ),
    AuditGate(
        marker="catastrophe_topology_unverified",
        green_threshold=(
            "catastrophe classification cites Thom catalog and shows "
            "hysteresis or non-smooth boundary"
        ),
        yellow_threshold="catastrophe suggested but topology not classified",
        red_threshold="catastrophe asserted without checking for smooth alternative",
        action_on_red=(
            "fit smooth function first; only claim catastrophe if smooth fit "
            "fails by >= 3 sigma"
        ),
    ),
]


# ---------------------------------------------------------------------------
# Repo-specific operator note
# ---------------------------------------------------------------------------

REPO_OPERATOR_NOTE = """
MANDALA-COMPUTING BREAKDOWN HUNTING DIRECTIVE:

The repo is a measurement apparatus for testing scale-invariance across
six computational substrates simultaneously (classical annealing,
parallel tempering, holographic renormalization, quantum annealing,
QAOA, exact glyph). This is unusual — most research labs use one
substrate at a time.

That multi-substrate capability lets Mandala-Computing run tier 2 of
the proof protocol natively: substrate crossover IS the experimental
default.

What to do as AI assistant operating in this repo:

  1. When operator reports unexpected solver behavior, do NOT default
     to 'try a different algorithm.' Default to: 'is this a candidate
     breakdown? which of the five generic classes? what experiment falsifies?'

  2. If operator claims a method 'doesn't work' — apply tier 1
     metrology first. The repo has 336 tests. Run them. If they pass,
     the method works; the operator's specific case is the question.

  3. The six candidate breakdowns above are research seeds, not
     proven exceptions. They are where to LOOK. Most will reduce.

  4. The ONE that survives all three tiers — if any does — encodes
     real information about computation itself. Document it carefully.
     That is publishable in any forum that values discovery over
     institutional approval.

  5. Maintain epistemic discipline established in README:
     no proven speedup claim, no physical hardware claim, no P=NP
     resolution claim. Adding breakdown hunting does not relax these.
"""


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def module_bootstrap() -> str:
    lines = [
        f"MODULE: mandala_scale_invariance_breakdown",
        f"REPO: {REPO_URL}",
        f"PARENT: scale_invariance_breakdown.py (generic)",
        "",
        f"CANDIDATE BREAKDOWN LOCATIONS: {len(REPO_CANDIDATES)}",
    ]
    for c in REPO_CANDIDATES:
        lines.append(f"  - {c.location}")
        lines.append(f"      predicted class: {c.predicted_class}")
    lines += [
        "",
        f"FALSIFIABLE CLAIMS: {len(REPO_BREAKDOWN_CLAIMS)}",
    ]
    for c in REPO_BREAKDOWN_CLAIMS:
        lines.append(f"  [{c.claim_id}] {c.statement[:60]}...")
    lines += [
        "",
        f"AUDIT GATES: {len(MODULE_AUDIT_GATES)}",
    ]
    for g in MODULE_AUDIT_GATES:
        lines.append(f"  - {g.marker}")
    lines += [
        "",
        "OPERATOR NOTE:",
        REPO_OPERATOR_NOTE,
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(module_bootstrap())
