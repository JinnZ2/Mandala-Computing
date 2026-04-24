"""
MANDALA RUNTIME v2.0
Substrate-Agnostic Sensor Fusion

A binding layer that sits ABOVE domain-specific alternative-compute
modules and unifies whatever encoding streams happen to be available
at runtime.

CORE GEOMETRY
    Every physical phenomenon can be sensed through multiple encoding
    substrates simultaneously:

        sound  ->  binary     (discrete event detection)
               ->  ternary    (silence/onset/sustain as null/attract/repel)
               ->  quantum    (phase coherence near classification boundary)
               ->  stochastic (probabilistic envelope)

    Each substrate carries information the others compress away.
    Binary alone is a SHADOW of the field.  Ternary + quantum +
    stochastic + binary together approach the field's actual geometry.

THE MANDALA BREATHES
    More substrates available  ->  richer geometry, expanded representation
    Fewer substrates available ->  contracted but still coherent geometry
    The shape adapts; the underlying constraint structure stays consistent.

This module does NOT implement any single domain.  It is the BINDING
that lets domain modules compose without knowing about each other.

Core types:
    Substrate          -- encoding substrate taxonomy
    StreamCapability   -- what an input stream can provide
    SensorStream       -- protocol for any input source
    Basin              -- geometric constraint contribution from one stream
    Manifest           -- runtime registry of available basins
    UnifiedGeometry    -- output of intersecting basins for a domain
    IntersectionRule   -- protocol for domain-specific basin combination
    Mandala            -- the breathing composition layer
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, Iterable, Optional, Any, Callable
from collections.abc import Mapping


# =========================================================================
# 1. SUBSTRATE TAXONOMY
# =========================================================================

class Substrate(Enum):
    """
    Encoding substrates a sensor stream can speak.

    Each substrate is a different lossy projection of an underlying
    physical field.  The Mandala's job is to combine projections to
    recover what any single one destroyed.
    """
    BINARY     = "binary"
    TERNARY    = "ternary"
    QUANTUM    = "quantum"
    STOCHASTIC = "stochastic"
    DIGITAL    = "digital"
    ANALOG     = "analog"


# =========================================================================
# 2. STREAM PROTOCOL
# =========================================================================

@dataclass(frozen=True)
class StreamCapability:
    """
    Declares what a single input stream can provide.

    A stream is PARTIAL by default.  It may cover only part of the
    field, only part of the time window, only one substrate.
    The Mandala assumes nothing -- every stream advertises its
    coverage explicitly.
    """
    domain: str
    substrate: Substrate
    coverage_fraction: float
    confidence: float
    sample_rate: Optional[float] = None
    spatial_extent: Optional[tuple] = None


class SensorStream(Protocol):
    """
    Minimum contract for any input source feeding the Mandala.

    A stream MUST expose:
      - what it can do (capability)
      - the actual encoded data (read)
      - how to interpret that data geometrically (project_to_basin)

    A stream MUST NOT assume:
      - other streams exist
      - any consumer cares about a specific substrate
      - its data is ground truth
    """
    @property
    def capability(self) -> StreamCapability: ...
    def read(self) -> Any: ...
    def project_to_basin(self) -> Basin: ...


# =========================================================================
# 3. BASIN -- the geometric unit each stream contributes
# =========================================================================

@dataclass
class Basin:
    """
    A constraint-geometry contribution from a single stream.

    A Basin says: "given my substrate's view of the field, here is
    the SHAPE of the constraint surface I can vouch for."

    Basins are SHALLOW (low confidence, broad coverage) or DEEP
    (high confidence, narrow coverage).  The Mandala's breathing
    expands toward shallow basins when many streams agree, contracts
    toward deep basins when streams conflict.

    Fields:
        support   -- region descriptor (depends on domain)
        depth     -- 0.0 = shallow/broad, 1.0 = deep/narrow
        signature -- substrate-native constraint payload
    """
    domain: str
    substrate: Substrate
    support: Any
    depth: float
    signature: Any
    source_capability: StreamCapability = field(repr=False)


# =========================================================================
# 4. MANIFEST -- runtime registry of available basins
# =========================================================================

@dataclass
class Manifest:
    """
    Snapshot of every basin available to the Mandala at this instant.

    Rebuilt every breath cycle because streams come and go (sensor
    dropout, network partition, new domain module loaded mid-session).
    """
    basins: list

    @property
    def basins_by_domain(self) -> dict:
        out: dict = {}
        for b in self.basins:
            out.setdefault(b.domain, []).append(b)
        return out

    @property
    def basins_by_substrate(self) -> dict:
        out: dict = {}
        for b in self.basins:
            out.setdefault(b.substrate, []).append(b)
        return out

    @property
    def domain_coverage(self) -> dict:
        """For each domain, which substrates are present."""
        out: dict = {}
        for b in self.basins:
            out.setdefault(b.domain, set()).add(b.substrate)
        return out

    @property
    def total_information_axes(self) -> int:
        """Count of (domain, substrate) pairs -- the Mandala's reach."""
        return sum(len(s) for s in self.domain_coverage.values())


def build_manifest(streams: Iterable) -> Manifest:
    """Snapshot every currently-readable stream into a Manifest."""
    basins = []
    for stream in streams:
        try:
            basins.append(stream.project_to_basin())
        except Exception:
            continue
    return Manifest(basins=basins)


# =========================================================================
# 5. INTERSECTION ENGINE -- combine basins into unified geometry
# =========================================================================

@dataclass
class UnifiedGeometry:
    """
    The output of intersecting all available basins for a given domain.

    Key properties:
        agreement_regions  -- where multiple substrates corroborate
        tension_regions    -- where substrates disagree (information-rich!)
        uncovered_regions  -- where no stream had visibility
        confidence_field   -- per-region confidence after fusion

    The TENSION regions are the most valuable output.  Disagreement
    between substrates is not noise -- it tells the Mandala where
    the field is doing something binary alone cannot capture.
    """
    domain: str
    substrates_used: set
    agreement_regions: list
    tension_regions: list
    uncovered_regions: list
    confidence_field: dict


class IntersectionRule(Protocol):
    """
    Domain-specific rule for combining basins of the same domain.

    The Mandala does NOT know how to intersect sound basins or
    gravity basins specifically -- that knowledge lives in domain
    modules.  Each domain registers an IntersectionRule.
    """
    domain: str
    def intersect(self, basins: list) -> UnifiedGeometry: ...


# =========================================================================
# 6. MANDALA -- the breathing composition layer
# =========================================================================

@dataclass
class MandalaRuntime:
    """
    The breathing umbrella that composes whatever is available.

    Lifecycle per breath:
      1. INHALE   -- build manifest from current streams
      2. EXPAND   -- intersect basins per domain into unified geometries
      3. RESONATE -- cross-domain coupling (gravity x sound, etc.)
      4. EXHALE   -- emit composite state; release transient basins

    The Mandala expands when many substrates per domain are present
    (rich projection set -> confident reconstruction) and contracts
    when few are present (sparse projection -> conservative claims).

    Critically: the Mandala NEVER fails for lack of input.  With one
    binary stream it produces a binary-quality geometry.  With ternary
    + quantum + stochastic added, the SAME interface produces a
    richer geometry.  The contract doesn't change -- only the depth.
    """
    rules: dict = field(default_factory=dict)

    def register(self, rule) -> None:
        """Register a domain-specific intersection rule."""
        self.rules[rule.domain] = rule

    def breathe(self, streams: Iterable) -> dict:
        """
        One breath cycle: inhale streams, expand basins, exhale geometries.

        Returns dict mapping domain -> UnifiedGeometry.
        """
        manifest = build_manifest(streams)
        geometries: dict = {}
        for domain, basins in manifest.basins_by_domain.items():
            rule = self.rules.get(domain)
            if rule is None:
                continue
            geometries[domain] = rule.intersect(basins)
        return geometries

    def breathe_with_manifest(self, streams: Iterable) -> tuple:
        """Like breathe(), but also returns the manifest for inspection."""
        manifest = build_manifest(streams)
        geometries: dict = {}
        for domain, basins in manifest.basins_by_domain.items():
            rule = self.rules.get(domain)
            if rule is None:
                continue
            geometries[domain] = rule.intersect(basins)
        return geometries, manifest


# =========================================================================
# 7. WORKED EXAMPLE -- sound fusion (binary + ternary + digital)
# =========================================================================

@dataclass
class _ToyStream:
    """Minimal stream stub for the worked example."""
    _capability: StreamCapability
    _data: Any
    _projector: Callable

    @property
    def capability(self) -> StreamCapability:
        return self._capability

    def read(self) -> Any:
        return self._data

    def project_to_basin(self) -> Basin:
        return self._projector(self._data, self._capability)


def _project_sound_binary(data, cap):
    onset_count = sum(1 for x in data if x)
    return Basin(
        domain=cap.domain, substrate=cap.substrate,
        support=("temporal", 0, len(data)), depth=0.3,
        signature={"onsets": onset_count, "frames": len(data)},
        source_capability=cap,
    )


def _project_sound_ternary(data, cap):
    silences = sum(1 for x in data if x == 0)
    attacks = sum(1 for x in data if x == +1)
    decays = sum(1 for x in data if x == -1)
    return Basin(
        domain=cap.domain, substrate=cap.substrate,
        support=("temporal", 0, len(data)), depth=0.6,
        signature={"silences": silences, "attacks": attacks, "decays": decays},
        source_capability=cap,
    )


def _project_sound_digital(data, cap):
    if not data:
        peak, mean = 0, 0
    else:
        peak = max(abs(x) for x in data)
        mean = sum(abs(x) for x in data) / len(data)
    return Basin(
        domain=cap.domain, substrate=cap.substrate,
        support=("temporal", 0, len(data)), depth=0.9,
        signature={"peak": peak, "mean_abs": mean, "samples": len(data)},
        source_capability=cap,
    )


@dataclass
class SoundIntersectionRule:
    """
    Domain rule: how to fuse sound basins across substrates.

    Strategy:
      AGREEMENT -- substrates that locate energy in the same temporal
                   region corroborate each other
      TENSION   -- binary says "onset" but digital shows no peak ->
                   the binary threshold lied
      UNCOVERED -- regions outside any basin's support
    """
    domain: str = "sound"

    def intersect(self, basins: list) -> UnifiedGeometry:
        substrates = {b.substrate for b in basins}

        binary = next((b for b in basins if b.substrate == Substrate.BINARY), None)
        ternary = next((b for b in basins if b.substrate == Substrate.TERNARY), None)
        digital = next((b for b in basins if b.substrate == Substrate.DIGITAL), None)

        agreement: list = []
        tension: list = []

        if binary and ternary:
            b_onsets = binary.signature.get("onsets", 0)
            t_attacks = ternary.signature.get("attacks", 0)
            if abs(b_onsets - t_attacks) <= max(1, 0.1 * max(b_onsets, t_attacks)):
                agreement.append(("event_count_corroborated", b_onsets, t_attacks))
            else:
                tension.append(("event_count_mismatch", b_onsets, t_attacks))

        if binary and digital:
            if (binary.signature.get("onsets", 0) > 0
                    and digital.signature.get("peak", 0) < 1):
                tension.append(("binary_threshold_artifact",
                                binary.signature, digital.signature))

        confidence = {}
        for b in basins:
            confidence[b.substrate.value] = b.depth * b.source_capability.confidence
        if agreement:
            for k in confidence:
                confidence[k] = min(1.0, confidence[k] * (1.0 + 0.1 * len(agreement)))

        uncovered = [] if basins else [("entire_field",)]

        return UnifiedGeometry(
            domain=self.domain,
            substrates_used=substrates,
            agreement_regions=agreement,
            tension_regions=tension,
            uncovered_regions=uncovered,
            confidence_field=confidence,
        )


# =========================================================================
# 8. GENERIC TERNARY / QUANTUM / STOCHASTIC CLASSIFIERS
# =========================================================================

import math


class TernaryClassifier:
    """
    Generic three-valued classifier for any physical field.

    Binary encoding collapses continuous values to {0, 1}.
    Ternary preserves the physically distinct ZERO/EQUILIBRIUM state
    that binary erases.

    Domains map naturally:
      sound   : compression / equilibrium / rarefaction
      gravity : attract / null (Lagrange) / repel
      electric: forward / zero-crossing / reverse
      thermal : heating / equilibrium / cooling
      magnetic: aligned / demagnetised / anti-aligned
    """

    def __init__(self, null_threshold: float = 1e-6,
                 positive_label: str = "+1",
                 null_label: str = "0",
                 negative_label: str = "-1"):
        self.null_threshold = null_threshold
        self.labels = (negative_label, null_label, positive_label)

    def classify(self, value: float) -> int:
        """Return -1, 0, or +1."""
        if abs(value) < self.null_threshold:
            return 0
        return 1 if value > 0 else -1

    def classify_vector(self, vector: list, component: int = -1) -> int:
        """Classify a vector by magnitude (component=-1) or a specific axis."""
        if component >= 0 and component < len(vector):
            return self.classify(vector[component])
        mag = math.sqrt(sum(x * x for x in vector))
        if mag < self.null_threshold:
            return 0
        return 1 if vector[min(1, len(vector) - 1)] > 0 else -1

    def distribution(self, values: list) -> dict:
        """Classify a sequence and return counts + fractions."""
        states = [self.classify(v) for v in values]
        n = len(states)
        counts = {-1: 0, 0: 0, 1: 0}
        for s in states:
            counts[s] += 1
        fracs = {k: v / max(n, 1) for k, v in counts.items()}
        symmetry = 1.0 - abs(counts[1] - counts[-1]) / max(counts[1] + counts[-1], 1)
        return {
            "counts": counts, "fractions": fracs,
            "symmetry": symmetry, "null_fraction": fracs[0],
            "total": n,
        }

    def label(self, state: int) -> str:
        return self.labels[state + 1]


class QuantumSuperpositionModel:
    """
    Model a continuous measurement as quantum-like superposition.

    Before measurement (thresholding), a value exists in superposition
    over possible outcomes. The binary threshold is a measurement collapse.

    Useful for: orbital stability, harmonic content, skin effect, etc.
    """

    def __init__(self, threshold: float = 0.5,
                 uncertainty: float = 0.1):
        self.threshold = threshold
        self.uncertainty = uncertainty

    def classify(self, value: float) -> dict:
        """
        Return superposition state with probabilities.

        Instead of binary collapse, returns:
          p_above: probability of being above threshold
          p_below: probability of being below threshold
          state: 'above', 'below', or 'indeterminate'
        """
        if self.uncertainty <= 0:
            above = value >= self.threshold
            return {"p_above": float(above), "p_below": float(not above),
                    "state": "above" if above else "below", "value": value}
        z = (value - self.threshold) / self.uncertainty
        p_above = 0.5 * (1 + math.erf(z / math.sqrt(2)))
        if p_above > 0.95:
            state = "above"
        elif p_above < 0.05:
            state = "below"
        else:
            state = "indeterminate"
        return {"p_above": p_above, "p_below": 1 - p_above,
                "state": state, "value": value, "z_score": z}

    def superposition_entropy(self, values: list) -> float:
        """Shannon entropy of the above/below/indeterminate distribution."""
        classes = [self.classify(v)["state"] for v in values]
        n = len(classes)
        if n == 0:
            return 0.0
        counts = {}
        for c in classes:
            counts[c] = counts.get(c, 0) + 1
        return -sum((c / n) * math.log2(c / n) for c in counts.values() if c > 0)

    def indeterminate_fraction(self, values: list) -> float:
        """Fraction of values in the indeterminate zone near threshold."""
        if not values:
            return 0.0
        return sum(1 for v in values
                   if abs(v - self.threshold) < self.uncertainty) / len(values)


class StochasticNoiseModel:
    """
    Model measurement noise as information carrier, not error.

    Binary systems filter jitter. This model preserves it as:
      - Thermal state indicator (k_B*T)
      - Component aging signature
      - Environmental coupling signal

    Applicable to: phase jitter, amplitude noise, contact resistance, tidal.
    """

    def __init__(self, values: list):
        self.values = list(values)
        self.jitter_rms = 0.0
        self.jitter_entropy = 0.0
        self.information_loss = 0.0
        if len(values) >= 2:
            self._compute()

    def _compute(self):
        diffs = [self.values[i] - self.values[i - 1]
                 for i in range(1, len(self.values))]
        if not diffs:
            return
        mean_diff = sum(diffs) / len(diffs)
        self.jitter_rms = math.sqrt(
            sum((d - mean_diff) ** 2 for d in diffs) / len(diffs))
        if self.jitter_rms > 0:
            self.jitter_entropy = 0.5 * math.log2(
                2 * math.pi * math.e * self.jitter_rms ** 2)
            self.information_loss = min(1.0, max(0.0, self.jitter_entropy / 8.0))

    def summary(self) -> dict:
        return {
            "jitter_rms": self.jitter_rms,
            "jitter_entropy_bits": self.jitter_entropy,
            "information_loss_if_filtered": self.information_loss,
            "samples": len(self.values),
        }


# =========================================================================
# 9. GRAVITY INTERSECTION RULE
# =========================================================================

@dataclass
class GravityIntersectionRule:
    """
    Domain rule: fuse gravity basins across substrates.

    Ternary  -> Attract/Null/Repel classification; Lagrange point detection
    Quantum  -> Orbital stability as superposition over stable/unstable
    Stochastic -> Tidal acceleration as probability distribution

    Agreement: ternary null points corroborated by quantum indeterminate zones
    Tension: binary says "stable" but quantum says "indeterminate"
    """
    domain: str = "gravity"

    def intersect(self, basins: list) -> UnifiedGeometry:
        substrates = {b.substrate for b in basins}
        ternary = next((b for b in basins if b.substrate == Substrate.TERNARY), None)
        quantum = next((b for b in basins if b.substrate == Substrate.QUANTUM), None)
        binary = next((b for b in basins if b.substrate == Substrate.BINARY), None)
        stochastic = next((b for b in basins if b.substrate == Substrate.STOCHASTIC), None)

        agreement: list = []
        tension: list = []

        if ternary and quantum:
            null_frac = ternary.signature.get("null_fraction", 0)
            indet_frac = quantum.signature.get("indeterminate_fraction", 0)
            if null_frac > 0.05 and indet_frac > 0.05:
                agreement.append(("lagrange_corroborated",
                                  f"null={null_frac:.1%}", f"indet={indet_frac:.1%}"))

        if binary and quantum:
            binary_stable = binary.signature.get("stable_fraction", 0)
            indet_frac = quantum.signature.get("indeterminate_fraction", 0)
            if binary_stable > 0.8 and indet_frac > 0.2:
                tension.append(("stability_overclaimed",
                                f"binary_stable={binary_stable:.1%}",
                                f"quantum_indet={indet_frac:.1%}"))

        if ternary and stochastic:
            null_frac = ternary.signature.get("null_fraction", 0)
            disruption = stochastic.signature.get("disruption_probability", 0)
            if null_frac > 0.1 and disruption > 0.1:
                tension.append(("null_region_tidal_risk",
                                f"null={null_frac:.1%}",
                                f"disruption={disruption:.1%}"))

        confidence = {}
        for b in basins:
            confidence[b.substrate.value] = b.depth * b.source_capability.confidence
        if agreement:
            for k in confidence:
                confidence[k] = min(1.0, confidence[k] * (1.0 + 0.1 * len(agreement)))

        uncovered = [] if basins else [("entire_field",)]
        return UnifiedGeometry(
            domain=self.domain, substrates_used=substrates,
            agreement_regions=agreement, tension_regions=tension,
            uncovered_regions=uncovered, confidence_field=confidence,
        )


# =========================================================================
# 10. ELECTRIC INTERSECTION RULE
# =========================================================================

@dataclass
class ElectricIntersectionRule:
    """
    Domain rule: fuse electric basins across substrates.

    Ternary  -> Charge (+/0/-), current (forward/zero/reverse), AC zero-crossing
    Quantum  -> Skin effect as conduction path superposition
    Stochastic -> Contact resistance as probability (Johnson-Nyquist noise)

    Agreement: ternary zero-crossings corroborate quantum skin depth collapse
    Tension: binary says "conducting" but stochastic gives P < 0.6
    """
    domain: str = "electric"

    def intersect(self, basins: list) -> UnifiedGeometry:
        substrates = {b.substrate for b in basins}
        ternary = next((b for b in basins if b.substrate == Substrate.TERNARY), None)
        quantum = next((b for b in basins if b.substrate == Substrate.QUANTUM), None)
        binary = next((b for b in basins if b.substrate == Substrate.BINARY), None)
        stochastic = next((b for b in basins if b.substrate == Substrate.STOCHASTIC), None)

        agreement: list = []
        tension: list = []

        if ternary and quantum:
            zero_frac = ternary.signature.get("zero_fraction", 0)
            collapse_frac = quantum.signature.get("collapse_fraction", 0)
            if zero_frac > 0.01 and collapse_frac > 0.5:
                agreement.append(("zero_crossing_skin_corroboration",
                                  f"zero={zero_frac:.1%}",
                                  f"collapse={collapse_frac:.1%}"))

        if binary and stochastic:
            binary_conducting = binary.signature.get("conducting", False)
            p_conducting = stochastic.signature.get("conducting_probability", 1.0)
            if binary_conducting and p_conducting < 0.6:
                tension.append(("conducting_overclaimed",
                                f"binary=conducting",
                                f"P(conducting)={p_conducting:.1%}"))
            if not binary_conducting and p_conducting > 0.4:
                tension.append(("non_conducting_overclaimed",
                                f"binary=non-conducting",
                                f"P(conducting)={p_conducting:.1%}"))

        if ternary and binary:
            zero_frac = ternary.signature.get("zero_fraction", 0)
            if zero_frac > 0.1:
                tension.append(("zero_state_erased",
                                f"ternary_zero={zero_frac:.1%}",
                                "binary cannot represent zero-crossing"))

        confidence = {}
        for b in basins:
            confidence[b.substrate.value] = b.depth * b.source_capability.confidence
        if agreement:
            for k in confidence:
                confidence[k] = min(1.0, confidence[k] * (1.0 + 0.1 * len(agreement)))

        uncovered = [] if basins else [("entire_field",)]
        return UnifiedGeometry(
            domain=self.domain, substrates_used=substrates,
            agreement_regions=agreement, tension_regions=tension,
            uncovered_regions=uncovered, confidence_field=confidence,
        )


# =========================================================================
# 11. UNIFIED ALTERNATIVE PARADIGM REGISTRY
# =========================================================================

class AlternativeParadigm(Enum):
    """Alternative computing paradigms beyond binary."""
    TERNARY = "ternary"
    QUANTUM = "quantum"
    STOCHASTIC = "stochastic"
    NEUROMORPHIC = "neuromorphic"
    RESERVOIR = "reservoir"
    MEMRISTIVE = "memristive"
    APPROXIMATE = "approximate"


@dataclass
class ParadigmMapping:
    """Maps a paradigm to the domains and substrates where it applies."""
    paradigm: AlternativeParadigm
    applicable_domains: list
    substrate: Substrate
    what_it_recovers: str
    axis: str


PARADIGM_REGISTRY: list = [
    ParadigmMapping(
        AlternativeParadigm.TERNARY,
        ["sound", "gravity", "electric", "thermal", "magnetic"],
        Substrate.TERNARY,
        "Binary sign bits erase the physically distinct ZERO/EQUILIBRIUM state",
        "State Representation (binary -> ternary)",
    ),
    ParadigmMapping(
        AlternativeParadigm.QUANTUM,
        ["sound", "gravity", "electric"],
        Substrate.QUANTUM,
        "Binary thresholding collapses continuous superpositions into false dichotomies",
        "State Representation (ternary -> quantum amplitude)",
    ),
    ParadigmMapping(
        AlternativeParadigm.STOCHASTIC,
        ["sound", "electric", "gravity", "thermal"],
        Substrate.STOCHASTIC,
        "Binary declares probability distributions as point estimates",
        "State Representation (probabilistic)",
    ),
    ParadigmMapping(
        AlternativeParadigm.NEUROMORPHIC,
        ["sound", "electric"],
        Substrate.DIGITAL,
        "Binary treats time-series as independent frames; spikes carry temporal structure",
        "Execution Model (parallel -> event-driven)",
    ),
    ParadigmMapping(
        AlternativeParadigm.RESERVOIR,
        ["sound", "gravity", "electric", "thermal", "magnetic"],
        Substrate.ANALOG,
        "Binary processes domains independently; reservoir couples all dynamics",
        "Execution Model (event-driven -> dynamical)",
    ),
    ParadigmMapping(
        AlternativeParadigm.MEMRISTIVE,
        ["electric"],
        Substrate.ANALOG,
        "Binary reads instantaneous state; memristor state IS its history",
        "Memory Coupling (co-located -> intrinsic)",
    ),
    ParadigmMapping(
        AlternativeParadigm.APPROXIMATE,
        ["electric", "thermal", "gravity"],
        Substrate.STOCHASTIC,
        "Binary demands exact thresholds; approximate gives confidence intervals",
        "State Representation (continuous)",
    ),
]


def get_paradigms_for_domain(domain: str) -> list:
    """Get all alternative paradigms applicable to a domain."""
    return [p for p in PARADIGM_REGISTRY if domain in p.applicable_domains]


def get_paradigm_matrix() -> dict:
    """Return paradigm x domain applicability matrix."""
    domains = sorted({d for p in PARADIGM_REGISTRY for d in p.applicable_domains})
    matrix = {}
    for p in PARADIGM_REGISTRY:
        matrix[p.paradigm.value] = {d: d in p.applicable_domains for d in domains}
    return matrix


# =========================================================================
# 12. DEMO
# =========================================================================

def demo_breathing():
    """Show the Mandala breathing across three substrate availability scenarios."""
    print("=" * 60)
    print("MANDALA RUNTIME — Substrate-Agnostic Sensor Fusion")
    print("=" * 60)

    mandala = MandalaRuntime()
    mandala.register(SoundIntersectionRule())

    binary_stream = _ToyStream(
        _capability=StreamCapability("sound", Substrate.BINARY, 0.7, 0.6, 44100),
        _data=[1, 0, 0, 1, 0, 1, 0, 0],
        _projector=_project_sound_binary,
    )
    ternary_stream = _ToyStream(
        _capability=StreamCapability("sound", Substrate.TERNARY, 0.7, 0.8, 44100),
        _data=[+1, -1, 0, +1, -1, +1, -1, 0],
        _projector=_project_sound_ternary,
    )
    digital_stream = _ToyStream(
        _capability=StreamCapability("sound", Substrate.DIGITAL, 0.9, 0.95, 44100),
        _data=[12000, -8000, 100, 15000, -9000, 14000, -7500, 200],
        _projector=_project_sound_digital,
    )

    scenarios = [
        ("A — binary only (contracted)", [binary_stream]),
        ("B — binary + ternary (partial)", [binary_stream, ternary_stream]),
        ("C — binary + ternary + digital (expanded)", [binary_stream, ternary_stream, digital_stream]),
    ]

    for label, streams in scenarios:
        print(f"\n  Breath: {label}")
        result, manifest = mandala.breathe_with_manifest(streams)
        print(f"    information axes: {manifest.total_information_axes}")
        for domain, geom in result.items():
            print(f"    domain={domain}")
            print(f"    substrates={[s.value for s in geom.substrates_used]}")
            print(f"    agreement={geom.agreement_regions}")
            print(f"    tension={geom.tension_regions}")
            print(f"    confidence={geom.confidence_field}")
    print()


def demo_classifiers():
    """Show generic ternary / quantum / stochastic classifiers."""
    print("=" * 60)
    print("Generic Classifiers — Ternary / Quantum / Stochastic")
    print("=" * 60)

    tc = TernaryClassifier(null_threshold=0.5,
                           positive_label="attract", null_label="null",
                           negative_label="repel")
    values = [9.81, -1.62, 0.0, 0.3, -0.1, 0.0]
    dist = tc.distribution(values)
    print(f"\n  Gravity ternary: {dist['counts']}")
    print(f"    null fraction: {dist['null_fraction']:.1%}")
    print(f"    symmetry: {dist['symmetry']:.2f}")

    qm = QuantumSuperpositionModel(threshold=0.5, uncertainty=0.1)
    stabilities = [0.9, 0.3, 0.55, 0.48, 0.51, 0.47]
    print(f"\n  Orbital stability superposition:")
    for s in stabilities:
        r = qm.classify(s)
        print(f"    s={s:.2f} -> {r['state']:13s}  P(above)={r['p_above']:.1%}")
    print(f"    indeterminate fraction: {qm.indeterminate_fraction(stabilities):.1%}")
    print(f"    superposition entropy: {qm.superposition_entropy(stabilities):.2f} bits")

    phases = [0.3, 1.8, 3.5, 0.8, 2.1, 4.2, 1.5, 3.0]
    nm = StochasticNoiseModel(phases)
    s = nm.summary()
    print(f"\n  Phase jitter: rms={s['jitter_rms']:.4f}")
    print(f"    entropy: {s['jitter_entropy_bits']:.2f} bits")
    print(f"    info loss if filtered: {s['information_loss_if_filtered']:.1%}")
    print()


def demo_multi_domain():
    """Show multi-domain breathing with sound + gravity + electric."""
    print("=" * 60)
    print("Multi-Domain Breathing — Sound + Gravity + Electric")
    print("=" * 60)

    mandala = MandalaRuntime()
    mandala.register(SoundIntersectionRule())
    mandala.register(GravityIntersectionRule())
    mandala.register(ElectricIntersectionRule())

    def _proj_grav_ternary(data, cap):
        tc = TernaryClassifier(null_threshold=0.5)
        dist = tc.distribution(data)
        return Basin(domain=cap.domain, substrate=cap.substrate,
                     support=("spatial", 0, len(data)), depth=0.6,
                     signature={"null_fraction": dist["null_fraction"],
                                "symmetry": dist["symmetry"]},
                     source_capability=cap)

    def _proj_grav_quantum(data, cap):
        qm = QuantumSuperpositionModel(threshold=0.5, uncertainty=0.1)
        return Basin(domain=cap.domain, substrate=cap.substrate,
                     support=("orbital", 0, len(data)), depth=0.7,
                     signature={"indeterminate_fraction": qm.indeterminate_fraction(data),
                                "entropy": qm.superposition_entropy(data)},
                     source_capability=cap)

    def _proj_elec_ternary(data, cap):
        tc = TernaryClassifier(null_threshold=0.001)
        dist = tc.distribution(data)
        return Basin(domain=cap.domain, substrate=cap.substrate,
                     support=("temporal", 0, len(data)), depth=0.6,
                     signature={"zero_fraction": dist["null_fraction"],
                                "symmetry": dist["symmetry"]},
                     source_capability=cap)

    def _proj_elec_stochastic(data, cap):
        return Basin(domain=cap.domain, substrate=cap.substrate,
                     support=("contact", 0, len(data)), depth=0.5,
                     signature={"conducting_probability": 0.55,
                                "noise_floor": 1e-7},
                     source_capability=cap)

    def _proj_elec_binary(data, cap):
        return Basin(domain=cap.domain, substrate=cap.substrate,
                     support=("circuit", 0, len(data)), depth=0.3,
                     signature={"conducting": True},
                     source_capability=cap)

    streams = [
        _ToyStream(StreamCapability("sound", Substrate.BINARY, 0.7, 0.6),
                    [1, 0, 0, 1, 0, 1], _project_sound_binary),
        _ToyStream(StreamCapability("sound", Substrate.TERNARY, 0.7, 0.8),
                    [+1, -1, 0, +1, -1, +1], _project_sound_ternary),
        _ToyStream(StreamCapability("gravity", Substrate.TERNARY, 0.8, 0.7),
                    [9.81, -1.62, 0.0, 0.3, -0.1, 0.0], _proj_grav_ternary),
        _ToyStream(StreamCapability("gravity", Substrate.QUANTUM, 0.6, 0.8),
                    [0.9, 0.3, 0.55, 0.48, 0.51, 0.47], _proj_grav_quantum),
        _ToyStream(StreamCapability("electric", Substrate.TERNARY, 0.7, 0.7),
                    [0.5, -0.02, 0.0, 10.0, -5.0, 0.001], _proj_elec_ternary),
        _ToyStream(StreamCapability("electric", Substrate.STOCHASTIC, 0.5, 0.6),
                    [5.96e7, 1e-8, 1e-6], _proj_elec_stochastic),
        _ToyStream(StreamCapability("electric", Substrate.BINARY, 0.7, 0.5),
                    [1, 0, 1, 1, 0, 1], _proj_elec_binary),
    ]

    result, manifest = mandala.breathe_with_manifest(streams)
    print(f"\n  Total information axes: {manifest.total_information_axes}")
    print(f"  Domains: {list(manifest.domain_coverage.keys())}")
    for d, subs in manifest.domain_coverage.items():
        print(f"    {d}: {[s.value for s in subs]}")

    for domain, geom in sorted(result.items()):
        print(f"\n  [{domain}]")
        print(f"    substrates: {[s.value for s in geom.substrates_used]}")
        print(f"    agreement: {geom.agreement_regions}")
        print(f"    tension: {geom.tension_regions}")
        print(f"    confidence: {geom.confidence_field}")
    print()


def demo_paradigm_registry():
    """Show the unified alternative paradigm registry."""
    print("=" * 60)
    print("Unified Alternative Paradigm Registry")
    print("=" * 60)
    matrix = get_paradigm_matrix()
    domains = sorted({d for row in matrix.values() for d in row})
    header = f"  {'paradigm':<14s}" + "".join(f"{d:<10s}" for d in domains)
    print(f"\n{header}")
    print("  " + "-" * (14 + 10 * len(domains)))
    for paradigm, row in matrix.items():
        cells = "".join(("  yes     " if row[d] else "  .       ") for d in domains)
        print(f"  {paradigm:<14s}{cells}")
    print()


if __name__ == "__main__":
    demo_breathing()
    demo_classifiers()
    demo_multi_domain()
    demo_paradigm_registry()
    print("=" * 60)
    print("The Mandala breathes. Substrates fuse. Geometry emerges.")
    print("=" * 60)
