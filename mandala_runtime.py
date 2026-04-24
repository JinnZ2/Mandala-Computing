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

    These are the WELL-KNOWN substrates for physical-domain encoding.
    For intelligence substrates (Layer 3), use string values directly
    in StreamCapability/Basin — the Mandala accepts any hashable
    substrate, not just this enum.
    """
    BINARY     = "binary"
    TERNARY    = "ternary"
    QUANTUM    = "quantum"
    STOCHASTIC = "stochastic"
    DIGITAL    = "digital"
    ANALOG     = "analog"


def substrate_key(s) -> str:
    """Extract string key from a Substrate enum or a raw string."""
    return s.value if isinstance(s, Substrate) else str(s)


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
        support    -- region descriptor (depends on domain)
        depth      -- 0.0 = shallow/broad, 1.0 = deep/narrow
        signature  -- substrate-native constraint payload
        provenance -- who created this basin, when, under what tradition
    """
    domain: str
    substrate: Any
    support: Any
    depth: float
    signature: Any
    source_capability: Any = field(default=None, repr=False)
    provenance: Optional[dict] = None


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


@dataclass
class ResonanceResult:
    """
    Output of the RESONATE phase: cross-domain coupling analysis.

    This is what makes the Mandala more than N independent wrappers.
    Resonance detects physics that spans domains — a gravity null
    co-located with an acoustic equilibrium is a stasis point that
    neither domain could identify alone.

    Fields:
        domains_coupled           -- which domains participated
        cross_domain_agreements   -- where domains corroborate each other
        cross_domain_tensions     -- where domains conflict (information-rich!)
        confidence_boosts         -- per-domain confidence adjustments
        coupling_strength         -- 0-1 scalar: how strongly domains couple
        synthesis_products        -- NEW Basins generated by rule engine
    """
    domains_coupled: list
    cross_domain_agreements: list
    cross_domain_tensions: list
    confidence_boosts: dict
    coupling_strength: float
    synthesis_products: list = field(default_factory=list)


class CouplingRule(Protocol):
    """
    Domain-pair-specific coupling rule for the RESONATE phase.

    Registered with MandalaRuntime.register_coupling(). Called during
    breathing when both domains are present. Returns agreements,
    tensions, and confidence boosts specific to the domain pair.
    """
    domains: tuple  # (domain_a, domain_b)
    def couple(self, geom_a: UnifiedGeometry,
               geom_b: UnifiedGeometry) -> dict: ...


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
    couplings: list = field(default_factory=list)
    synthesis: Optional[Any] = field(default=None)

    def register(self, rule) -> None:
        """Register a domain-specific intersection rule."""
        self.rules[rule.domain] = rule

    def register_coupling(self, coupling) -> None:
        """Register a cross-domain coupling rule."""
        self.couplings.append(coupling)

    def enable_synthesis(self, engine=None) -> None:
        """Enable generative synthesis in the RESONATE phase."""
        self.synthesis = engine or SynthesisEngine()

    def breathe(self, streams: Iterable) -> dict:
        """
        One breath cycle: inhale, expand, resonate, exhale.

        Returns dict mapping domain -> UnifiedGeometry, plus
        '_resonance' key with cross-domain coupling results.
        """
        manifest = build_manifest(streams)
        geometries: dict = {}
        for domain, basins in manifest.basins_by_domain.items():
            rule = self.rules.get(domain)
            if rule is None:
                continue
            geometries[domain] = rule.intersect(basins)
        resonance = self._resonate(geometries, manifest)
        if resonance.cross_domain_agreements or resonance.cross_domain_tensions:
            geometries["_resonance"] = resonance
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
        resonance = self._resonate(geometries, manifest)
        if resonance.cross_domain_agreements or resonance.cross_domain_tensions:
            geometries["_resonance"] = resonance
        return geometries, manifest

    def _resonate(self, geometries: dict, manifest: Manifest) -> "ResonanceResult":
        """
        RESONATE phase: cross-domain coupling.

        After each domain has been independently intersected, RESONATE
        looks for agreement and tension BETWEEN domains.  This is where
        the Mandala becomes more than N independent domain wrappers —
        it detects cross-domain physics that no single domain can see.

        Built-in heuristics:
          1. Null-state correlation: domains sharing null/zero/equilibrium
             at similar support regions corroborate a physical stasis point.
          2. Tension amplification: domains that both show internal tension
             may share a common instability source.
          3. Confidence boost: domains that agree boost each other's
             confidence; domains that disagree flag cross-domain tension.

        Registered CouplingRules run after the heuristics for
        domain-pair-specific physics (e.g. electromagnetic-acoustic).
        """
        agreements: list = []
        tensions: list = []
        confidence_boosts: dict = {}

        domain_keys = [k for k in geometries if not k.startswith("_")]

        # --- Heuristic 1: null-state correlation ---
        null_domains = []
        for d in domain_keys:
            geom = geometries[d]
            cf = geom.confidence_field
            for sk, conf in cf.items():
                if sk == "ternary" and conf > 0:
                    null_domains.append(d)
                    break
        if len(null_domains) >= 2:
            agreements.append(("null_state_cross_domain",
                               null_domains,
                               "Multiple domains have ternary coverage — "
                               "null/equilibrium states can be corroborated"))

        # --- Heuristic 2: tension amplification ---
        tense_domains = []
        for d in domain_keys:
            geom = geometries[d]
            if geom.tension_regions:
                tense_domains.append((d, len(geom.tension_regions)))
        if len(tense_domains) >= 2:
            tensions.append(("multi_domain_tension",
                             [(d, n) for d, n in tense_domains],
                             "Multiple domains show internal tension — "
                             "possible shared instability source"))

        # --- Heuristic 3: agreement correlation ---
        agreeing_domains = []
        for d in domain_keys:
            geom = geometries[d]
            if geom.agreement_regions:
                agreeing_domains.append((d, len(geom.agreement_regions)))
        if len(agreeing_domains) >= 2:
            agreements.append(("cross_domain_corroboration",
                               [(d, n) for d, n in agreeing_domains],
                               "Multiple domains have internal agreement — "
                               "strengthens overall confidence"))
            for d, _ in agreeing_domains:
                confidence_boosts[d] = 0.1

        # --- Heuristic 4: substrate overlap ---
        substrate_domains: dict = {}
        for d in domain_keys:
            for s in geometries[d].substrates_used:
                substrate_domains.setdefault(s, []).append(d)
        shared_substrates = {s: ds for s, ds in substrate_domains.items()
                             if len(ds) >= 2}
        if shared_substrates:
            for s, ds in shared_substrates.items():
                agreements.append(("shared_substrate",
                                   {"substrate": substrate_key(s), "domains": ds},
                                   f"Substrate '{substrate_key(s)}' spans domains {ds} — "
                                   f"enables direct cross-domain comparison"))

        # --- Registered coupling rules ---
        for coupling in self.couplings:
            d_a, d_b = coupling.domains
            if d_a in geometries and d_b in geometries:
                result = coupling.couple(geometries[d_a], geometries[d_b])
                if result.get("agreements"):
                    agreements.extend(result["agreements"])
                if result.get("tensions"):
                    tensions.extend(result["tensions"])
                if result.get("confidence_boosts"):
                    for d, boost in result["confidence_boosts"].items():
                        confidence_boosts[d] = confidence_boosts.get(d, 0) + boost

        # --- Generative synthesis (RSC rule engine) ---
        synthesis_products: list = []
        if self.synthesis is not None:
            all_basins = []
            for domain_basins in manifest.basins_by_domain.values():
                all_basins.extend(domain_basins)
            synthesis_products = self.synthesis.synthesize(all_basins, geometries)
            for sp in synthesis_products:
                agreements.append(("SYNTHESIS",
                                   sp.operation, sp.product, sp.why))

        return ResonanceResult(
            domains_coupled=domain_keys,
            cross_domain_agreements=agreements,
            cross_domain_tensions=tensions,
            confidence_boosts=confidence_boosts,
            coupling_strength=len(agreements) / max(len(domain_keys), 1),
            synthesis_products=synthesis_products,
        )


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
            confidence[substrate_key(b.substrate)] = b.depth * b.source_capability.confidence
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
            confidence[substrate_key(b.substrate)] = b.depth * b.source_capability.confidence
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
            confidence[substrate_key(b.substrate)] = b.depth * b.source_capability.confidence
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
# 11. REAL GRAVITY PROJECTORS (physics-backed)
# =========================================================================

def project_gravity_ternary(vectors: list, null_threshold: float = 0.5) -> Basin:
    """
    Project gravity vector field data to a ternary basin.

    Uses TernaryClassifier on the y-component (conventional downward axis).
    Null states correspond to Lagrange points / equipotential surfaces.
    """
    tc = TernaryClassifier(null_threshold=null_threshold)
    y_vals = [v[1] if len(v) > 1 else v[0] for v in vectors]
    dist = tc.distribution(y_vals)
    cap = StreamCapability("gravity", Substrate.TERNARY,
                           coverage_fraction=0.8, confidence=0.7)
    return Basin(
        domain="gravity", substrate=Substrate.TERNARY,
        support=("spatial", 0, len(vectors)), depth=0.6,
        signature={
            "null_fraction": dist["null_fraction"],
            "attract_fraction": dist["fractions"].get(-1, 0),
            "repel_fraction": dist["fractions"].get(1, 0),
            "symmetry": dist["symmetry"],
            "null_count": dist["counts"][0],
            "total": dist["total"],
        },
        source_capability=cap,
    )


def project_gravity_quantum(stability_metrics: list,
                            uncertainty: float = 0.1) -> Basin:
    """
    Project orbital stability data to a quantum superposition basin.

    Each stability value exists in superposition over stable/unstable
    until measured (integrated).  The indeterminate fraction quantifies
    how much binary classification would lie.
    """
    qm = QuantumSuperpositionModel(threshold=0.5, uncertainty=uncertainty)
    indet = qm.indeterminate_fraction(stability_metrics)
    entropy = qm.superposition_entropy(stability_metrics)
    cap = StreamCapability("gravity", Substrate.QUANTUM,
                           coverage_fraction=0.6, confidence=0.8)
    return Basin(
        domain="gravity", substrate=Substrate.QUANTUM,
        support=("orbital", 0, len(stability_metrics)), depth=0.7,
        signature={
            "indeterminate_fraction": indet,
            "entropy": entropy,
            "n_orbits": len(stability_metrics),
        },
        source_capability=cap,
    )


def project_gravity_stochastic(tidal_values: list) -> Basin:
    """
    Project tidal acceleration data to a stochastic basin.

    Tidal acceleration depends on internal structure (rigidity),
    which is a probability distribution, not a deterministic scalar.
    """
    nm = StochasticNoiseModel(tidal_values)
    summary = nm.summary()
    cap = StreamCapability("gravity", Substrate.STOCHASTIC,
                           coverage_fraction=0.5, confidence=0.6)
    return Basin(
        domain="gravity", substrate=Substrate.STOCHASTIC,
        support=("tidal", 0, len(tidal_values)), depth=0.5,
        signature={
            "jitter_rms": summary["jitter_rms"],
            "jitter_entropy": summary["jitter_entropy_bits"],
            "disruption_probability": min(1.0, summary["jitter_rms"] * 0.1),
        },
        source_capability=cap,
    )


# =========================================================================
# 12. CONCRETE COUPLING RULES
# =========================================================================

@dataclass
class GravitySoundCoupling:
    """
    Cross-domain coupling: gravity x sound.

    Physics: acoustic waves propagate differently in gravitational fields.
    A gravity null (Lagrange point) where sound is in equilibrium indicates
    a true stasis point. Gravity tension + sound tension may indicate
    seismic-gravitational coupling.
    """
    domains: tuple = ("gravity", "sound")

    def couple(self, geom_grav: UnifiedGeometry,
               geom_sound: UnifiedGeometry) -> dict:
        agreements = []
        tensions = []
        boosts = {}

        grav_has_null = any(
            "lagrange" in str(a).lower() or "null" in str(a).lower()
            for a in geom_grav.agreement_regions
        )
        sound_has_agreement = len(geom_sound.agreement_regions) > 0

        if grav_has_null and sound_has_agreement:
            agreements.append(("gravitoacoustic_stasis",
                               "gravity null + sound agreement",
                               "Possible physical stasis point: gravitational "
                               "equilibrium co-located with acoustic corroboration"))
            boosts["gravity"] = 0.15
            boosts["sound"] = 0.1

        if geom_grav.tension_regions and geom_sound.tension_regions:
            tensions.append(("seismic_gravitational_coupling",
                             f"gravity_tensions={len(geom_grav.tension_regions)}",
                             f"sound_tensions={len(geom_sound.tension_regions)}",
                             "Both domains show instability — possible coupled source"))

        return {"agreements": agreements, "tensions": tensions,
                "confidence_boosts": boosts}


@dataclass
class ElectricSoundCoupling:
    """
    Cross-domain coupling: electric x sound.

    Physics: electromagnetic-acoustic transduction (piezoelectric,
    magnetostrictive). Electric zero-crossings and sound equilibrium
    may correlate in electromechanical systems.
    """
    domains: tuple = ("electric", "sound")

    def couple(self, geom_elec: UnifiedGeometry,
               geom_sound: UnifiedGeometry) -> dict:
        agreements = []
        tensions = []
        boosts = {}

        elec_zero = any("zero" in str(t).lower()
                        for t in geom_elec.tension_regions)
        sound_agree = len(geom_sound.agreement_regions) > 0

        if elec_zero and sound_agree:
            agreements.append(("electromechanical_correlation",
                               "electric zero-crossing + sound agreement",
                               "Possible piezoelectric or magnetostrictive coupling"))
            boosts["electric"] = 0.05
            boosts["sound"] = 0.05

        return {"agreements": agreements, "tensions": tensions,
                "confidence_boosts": boosts}


@dataclass
class GravityElectricCoupling:
    """
    Cross-domain coupling: gravity x electric.

    Physics: gravitoelectric effects, charged particle orbits in
    gravitational fields. Shared tension indicates coupled instability.
    """
    domains: tuple = ("gravity", "electric")

    def couple(self, geom_grav: UnifiedGeometry,
               geom_elec: UnifiedGeometry) -> dict:
        agreements = []
        tensions = []
        boosts = {}

        if geom_grav.tension_regions and geom_elec.tension_regions:
            tensions.append(("gravitoelectric_instability",
                             f"gravity_tensions={len(geom_grav.tension_regions)}",
                             f"electric_tensions={len(geom_elec.tension_regions)}",
                             "Both domains unstable — possible charged particle "
                             "dynamics in gravitational field"))
        return {"agreements": agreements, "tensions": tensions,
                "confidence_boosts": boosts}


# =========================================================================
# 13. THERMAL AND MAGNETIC INTERSECTION RULES
# =========================================================================

@dataclass
class ThermalIntersectionRule:
    """
    Domain rule: fuse thermal basins across substrates.

    Ternary  -> heating / equilibrium / cooling
    Stochastic -> Boltzmann distribution, thermal fluctuation
    """
    domain: str = "thermal"

    def intersect(self, basins: list) -> UnifiedGeometry:
        substrates = {b.substrate for b in basins}
        ternary = next((b for b in basins if b.substrate == Substrate.TERNARY), None)
        stochastic = next((b for b in basins if b.substrate == Substrate.STOCHASTIC), None)
        binary = next((b for b in basins if b.substrate == Substrate.BINARY), None)

        agreement: list = []
        tension: list = []

        if ternary and stochastic:
            equil_frac = ternary.signature.get("equilibrium_fraction", 0)
            jitter = stochastic.signature.get("jitter_rms", 0)
            if equil_frac > 0.3 and jitter < 0.1:
                agreement.append(("thermal_equilibrium_confirmed",
                                  f"equilibrium={equil_frac:.1%}",
                                  f"jitter={jitter:.4f}"))
            if equil_frac < 0.1 and jitter > 0.5:
                tension.append(("thermal_instability",
                                f"equilibrium={equil_frac:.1%}",
                                f"jitter={jitter:.4f}"))

        if binary and ternary:
            equil_frac = ternary.signature.get("equilibrium_fraction", 0)
            if equil_frac > 0.2:
                tension.append(("thermal_equilibrium_erased",
                                f"equilibrium={equil_frac:.1%}",
                                "binary cannot represent thermal equilibrium"))

        confidence = {}
        for b in basins:
            confidence[substrate_key(b.substrate)] = b.depth * b.source_capability.confidence
        if agreement:
            for k in confidence:
                confidence[k] = min(1.0, confidence[k] * 1.1)

        uncovered = [] if basins else [("entire_field",)]
        return UnifiedGeometry(
            domain=self.domain, substrates_used=substrates,
            agreement_regions=agreement, tension_regions=tension,
            uncovered_regions=uncovered, confidence_field=confidence,
        )


@dataclass
class MagneticIntersectionRule:
    """
    Domain rule: fuse magnetic basins across substrates.

    Ternary  -> aligned / demagnetised / anti-aligned
    Quantum  -> spin superposition (up/down/mixed)
    Stochastic -> Barkhausen noise as domain wall dynamics
    """
    domain: str = "magnetic"

    def intersect(self, basins: list) -> UnifiedGeometry:
        substrates = {b.substrate for b in basins}
        ternary = next((b for b in basins if b.substrate == Substrate.TERNARY), None)
        quantum = next((b for b in basins if b.substrate == Substrate.QUANTUM), None)
        stochastic = next((b for b in basins if b.substrate == Substrate.STOCHASTIC), None)

        agreement: list = []
        tension: list = []

        if ternary and quantum:
            demag_frac = ternary.signature.get("demagnetised_fraction", 0)
            indet_frac = quantum.signature.get("indeterminate_fraction", 0)
            if demag_frac > 0.1 and indet_frac > 0.1:
                agreement.append(("demagnetised_spin_mixed",
                                  f"demagnetised={demag_frac:.1%}",
                                  f"spin_mixed={indet_frac:.1%}"))

        if ternary and stochastic:
            demag_frac = ternary.signature.get("demagnetised_fraction", 0)
            jitter = stochastic.signature.get("jitter_rms", 0)
            if demag_frac < 0.05 and jitter > 0.3:
                tension.append(("barkhausen_noise_during_alignment",
                                f"demagnetised={demag_frac:.1%}",
                                f"jitter={jitter:.4f}",
                                "Domain walls moving despite apparent alignment"))

        confidence = {}
        for b in basins:
            confidence[substrate_key(b.substrate)] = b.depth * b.source_capability.confidence
        if agreement:
            for k in confidence:
                confidence[k] = min(1.0, confidence[k] * 1.1)

        uncovered = [] if basins else [("entire_field",)]
        return UnifiedGeometry(
            domain=self.domain, substrates_used=substrates,
            agreement_regions=agreement, tension_regions=tension,
            uncovered_regions=uncovered, confidence_field=confidence,
        )


# =========================================================================
# 13b. GENERATIVE SYNTHESIS ENGINE (from Rosetta-Shape-Core rule patterns)
# =========================================================================
#
# The RSC rule engine has three generative operations:
#   EXPAND    — entity grows into a new capability/shape
#   ALIGN     — two entities align to produce an emergent capability
#   STRUCTURE — entity + structure → new capability
#
# These are GENERATIVE — they produce NEW constraints from interactions.
# This is the piece that makes RESONATE more than set-intersection.
#
# Rule format (JSONL, compatible with RSC rules/expand.jsonl):
#   {"when": {"op": "ALIGN", "args": ["X", "Y"]}, "then": "NEW_THING",
#    "priority": 5, "guard": {"requires": ["CAP"]}, "why": "reason"}
# =========================================================================


@dataclass
class SynthesisRule:
    """
    A generative rule that fires when Basin conditions are met,
    producing a NEW Basin that neither input carried alone.
    """
    op: str
    args: list
    then: str
    priority: int = 0
    guard_requires: list = field(default_factory=list)
    why: str = ""
    provenance: dict = field(default_factory=dict)

    @classmethod
    def from_jsonl_line(cls, line: str) -> SynthesisRule:
        d = json.loads(line)
        w = d.get("when", {})
        guard = d.get("guard", {})
        return cls(
            op=w.get("op", ""),
            args=w.get("args", []),
            then=d.get("then", ""),
            priority=d.get("priority", 0),
            guard_requires=guard.get("requires", []),
            why=d.get("why", ""),
            provenance=d.get("provenance", {}),
        )

    def to_dict(self) -> dict:
        d = {
            "when": {"op": self.op, "args": self.args},
            "then": self.then,
            "priority": self.priority,
            "why": self.why,
        }
        if self.guard_requires:
            d["guard"] = {"requires": self.guard_requires}
        if self.provenance:
            d["provenance"] = self.provenance
        return d


def load_synthesis_rules(path: str) -> list:
    """Load JSONL synthesis rules (RSC expand.jsonl format)."""
    p = pathlib.Path(path)
    if not p.exists():
        return []
    rules = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rules.append(SynthesisRule.from_jsonl_line(line))
    return sorted(rules, key=lambda r: -r.priority)


@dataclass
class SynthesisResult:
    """Output of a generative synthesis: the NEW constraint that emerged."""
    source_basins: list
    operation: str
    product: str
    why: str
    new_basin: Optional[Any] = None
    verification: Optional[dict] = None


class SynthesisEngine:
    """
    Generative synthesis engine for the RESONATE phase.

    Instead of just detecting shared channels (set intersection),
    this engine fires rules that PRODUCE new Basins from the
    interaction of existing ones.

    Three operations (from Rosetta-Shape-Core):
      EXPAND    — a single basin grows into a new capability
      ALIGN     — two basins align to produce an emergent property
      STRUCTURE — a basin + a structural pattern → new capability

    Rules can be loaded from JSONL files (RSC format) or registered
    programmatically.
    """

    def __init__(self):
        self.rules: list = []
        self._built_in_rules()

    def _built_in_rules(self):
        self.rules.extend([
            SynthesisRule(
                op="ALIGN", args=["swarm", "lattice"],
                then="acoustic_bridge",
                priority=7,
                why="Swarm acoustic signals couple to crystal piezoelectric "
                    "response — new constraint neither substrate carries alone",
            ),
            SynthesisRule(
                op="ALIGN", args=["swarm", "thermal"],
                then="collective_thermoregulation",
                priority=6,
                why="Swarm thermoregulation + thermal domain = active thermal "
                    "management geometry (bee cluster breathing)",
            ),
            SynthesisRule(
                op="ALIGN", args=["gradient_following", "lattice_modes"],
                then="gradient_lattice_resonance",
                priority=8,
                why="Gradient-following intelligence navigating a lattice "
                    "produces resonance at defect sites — neither substrate "
                    "alone predicts WHERE the gradient concentrates",
            ),
            SynthesisRule(
                op="STRUCTURE", args=["piezoelectric", "acoustic"],
                then="electromechanical_transduction",
                priority=7,
                why="Piezoelectric coupling + acoustic field = bidirectional "
                    "energy transduction (sound -> voltage -> sound)",
            ),
            SynthesisRule(
                op="EXPAND", args=["octahedral_state"],
                then="geometric_encoding",
                priority=9,
                why="Octahedron's 6 vertices encode 8 states (3 bits) — "
                    "the geometric-to-binary encoding basis",
            ),
            SynthesisRule(
                op="ALIGN", args=["ternary", "quantum"],
                then="three_valued_superposition",
                priority=6,
                why="Ternary null state + quantum indeterminate zone "
                    "= same phenomenon from two substrates. "
                    "New constraint: the null IS the superposition.",
            ),
        ])
        self.rules.sort(key=lambda r: -r.priority)

    def load_rules(self, path: str):
        """Load additional rules from a JSONL file."""
        self.rules.extend(load_synthesis_rules(path))
        self.rules.sort(key=lambda r: -r.priority)

    def add_rule(self, rule: SynthesisRule):
        self.rules.append(rule)
        self.rules.sort(key=lambda r: -r.priority)

    def synthesize(self, basins: list, geometries: dict) -> list:
        """
        Run all synthesis rules against available basins and geometries.

        For each rule that fires, produces a SynthesisResult with a
        generated Basin carrying the emergent property.  This is
        constraint GENERATION: the output Basin exists because of
        the interaction, not because either input carried it.
        """
        results: list = []
        all_tags = self._collect_tags(basins, geometries)

        for rule in self.rules:
            if rule.op == "ALIGN" and len(rule.args) == 2:
                a, b_arg = rule.args
                if self._tag_matches(a, all_tags) and self._tag_matches(b_arg, all_tags):
                    if rule.guard_requires and not all(
                            self._tag_matches(r, all_tags) for r in rule.guard_requires):
                        continue
                    source = [b for b in basins
                              if self._basin_matches(b, a) or self._basin_matches(b, b_arg)]
                    results.append(self._fire(rule, source))

            elif rule.op == "EXPAND" and len(rule.args) == 1:
                if self._tag_matches(rule.args[0], all_tags):
                    source = [b for b in basins if self._basin_matches(b, rule.args[0])]
                    results.append(self._fire(rule, source))

            elif rule.op == "STRUCTURE" and len(rule.args) == 2:
                entity, structure = rule.args
                if self._tag_matches(entity, all_tags) and self._tag_matches(structure, all_tags):
                    source = [b for b in basins
                              if self._basin_matches(b, entity) or self._basin_matches(b, structure)]
                    results.append(self._fire(rule, source))

        return results

    @staticmethod
    def _collect_tags(basins, geometries):
        tags = set()
        for b in basins:
            tags.add(substrate_key(b.substrate).lower())
            tags.add(b.domain.lower())
            if isinstance(b.signature, dict):
                mode = b.signature.get("mode", "")
                if mode:
                    tags.add(mode.lower())
                for c in b.signature.get("field_couplings", []):
                    tags.add(c.lower())
                for a in b.signature.get("applications", []):
                    tags.add(a.lower())
        for domain, geom in geometries.items():
            if domain.startswith("_"):
                continue
            if hasattr(geom, "substrates_used"):
                for s in geom.substrates_used:
                    tags.add(substrate_key(s).lower())
        return tags

    @staticmethod
    def _tag_matches(tag: str, tags: set) -> bool:
        tag_lower = tag.lower()
        return any(tag_lower in t for t in tags)

    @staticmethod
    def _basin_matches(basin, tag: str) -> bool:
        tag_lower = tag.lower()
        if tag_lower in substrate_key(basin.substrate).lower():
            return True
        if isinstance(basin.signature, dict):
            mode = basin.signature.get("mode", "").lower()
            if tag_lower in mode:
                return True
        return tag_lower in basin.domain.lower()

    def _fire(self, rule: SynthesisRule, source_basins: list) -> SynthesisResult:
        max_depth = max((b.depth for b in source_basins), default=0.5)
        new_depth = min(1.0, max_depth * 0.8)

        # Epistemological verification: validate the synthesis claim
        verification = self._verify_claim(rule.why)
        if verification and verification["concern"] > 0.7:
            new_depth *= (1.0 - verification["concern"] * 0.5)

        cap = StreamCapability(
            domain="synthesis", substrate=f"emergent.{rule.then}",
            coverage_fraction=0.5, confidence=new_depth,
        )
        new_basin = Basin(
            domain="synthesis", substrate=f"emergent.{rule.then}",
            support=("generated", rule.op, rule.args),
            depth=new_depth,
            signature={
                "mode": "synthesis", "product": rule.then,
                "operation": rule.op,
                "source_substrates": [substrate_key(b.substrate) for b in source_basins],
                "why": rule.why, "priority": rule.priority,
                "verified": verification is not None,
                "concern": verification["concern"] if verification else None,
            },
            source_capability=cap,
        )
        return SynthesisResult(
            source_basins=source_basins,
            operation=f"{rule.op}({', '.join(rule.args)})",
            product=rule.then, why=rule.why, new_basin=new_basin,
            verification=verification,
        )

    @staticmethod
    def _verify_claim(claim_text: str) -> Optional[dict]:
        """Run claim through epistemological validator if available."""
        try:
            from claim_validator import validate_claim
            report = validate_claim(claim_text)
            return {
                "concern": report.overall_concern,
                "interpretation": report.interpretation,
                "falsifiability": report.falsifiability.score,
                "tier_scores": {d.name: d.score for d in report.domain_scores},
            }
        except ImportError:
            return None


# =========================================================================
# 14. UNIFIED ALTERNATIVE PARADIGM REGISTRY
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
# 15. LAYER 3 → LAYER 4: LIVING INTELLIGENCE DESCRIPTORS
# =========================================================================
#
#  LAYER 4  DYNAMICS / RELATIONSHIPS / ENVIRONMENT
#           (IntersectionRule consumes these)
#                       ▲  emits Basin
#  LAYER 3  INTELLIGENCE PROFILE ← the substrate
#           bee swarm / quartz lattice / mycelial flow / etc.
#           each one is its OWN substrate, not a flavor of binary
#                       ▲  composed of
#  LAYER 2  BIOLOGY / CHEMISTRY / PHYSICS  (future drill-down)
#  LAYER 1  ATOMIC / SUB-ATOMIC            (future drill-down)
#
#  The flow: LID entity (JSON) → DynamicsProjector → Basin
# =========================================================================

import json
import time as _time
import pathlib


@dataclass
class LIDEntity:
    """
    Living Intelligence Descriptor — a Layer 3 intelligence profile.

    Describes an intelligence substrate (bee swarm, quartz lattice,
    mycelial network, plasma topology, etc.) in enough detail for a
    DynamicsProjector to emit constraint-geometry Basins.

    Can be loaded from JSON (ontology_index.json) or constructed
    programmatically.
    """
    entity_id: str
    name: str
    substrate_type: str
    category: str
    dynamics: dict = field(default_factory=dict)
    environment: dict = field(default_factory=dict)
    physics_couplings: list = field(default_factory=list)
    spatial_extent: Optional[tuple] = None
    temporal_scale_s: Optional[float] = None
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> LIDEntity:
        return cls(
            entity_id=d["entity_id"],
            name=d["name"],
            substrate_type=d["substrate_type"],
            category=d.get("category", "unknown"),
            dynamics=d.get("dynamics", {}),
            environment=d.get("environment", {}),
            physics_couplings=d.get("physics_couplings", []),
            spatial_extent=tuple(d["spatial_extent"]) if d.get("spatial_extent") else None,
            temporal_scale_s=d.get("temporal_scale_s"),
            metadata=d.get("metadata", {}),
        )

    @classmethod
    def from_lid_json(cls, entity: dict) -> LIDEntity:
        """
        Construct from an actual Living-Intelligence-Database entity JSON.

        LID schema: id, name, ontology, description, patterns (list of
        {name, type, efficiency_factor, geometry, applications}),
        links (list of {relation, target}), core_attributes, etc.
        """
        eid = entity.get("id", "UNKNOWN")
        name = entity.get("name", eid)
        ontology = entity.get("ontology", "unknown")
        desc = entity.get("description", "")

        patterns = entity.get("patterns", [])
        links = entity.get("links", [])
        core = entity.get("core_attributes", {})

        dynamics = {}
        if patterns:
            dynamics["patterns"] = patterns
        if core:
            dynamics["core_attributes"] = core

        physics_couplings = []
        for link in links:
            rel = link.get("relation", "")
            if rel in ("energy_coupling", "resonance", "geometry_link"):
                physics_couplings.append(link.get("target", ""))

        return cls(
            entity_id=eid,
            name=name,
            substrate_type=f"{ontology}.{name.lower().replace(' ', '_')}",
            category=f"{ontology}_intelligence",
            dynamics=dynamics,
            environment={},
            physics_couplings=physics_couplings,
            metadata={
                "description": desc,
                "links": links,
                "symbolic_code": entity.get("symbolic_code", ""),
                "emoji": entity.get("emoji", ""),
            },
        )

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "substrate_type": self.substrate_type,
            "category": self.category,
            "dynamics": self.dynamics,
            "environment": self.environment,
            "physics_couplings": self.physics_couplings,
            "spatial_extent": list(self.spatial_extent) if self.spatial_extent else None,
            "temporal_scale_s": self.temporal_scale_s,
            "metadata": self.metadata,
        }


def load_ontology_index(path: str,
                        max_staleness_days: float = 30.0) -> list:
    """
    Load LID entities from an ontology_index.json file.

    Includes a staleness check — if the file was last modified more
    than max_staleness_days ago, a warning is printed (but data is
    still returned).
    """
    p = pathlib.Path(path)
    if not p.exists():
        return []

    mtime = p.stat().st_mtime
    age_days = (_time.time() - mtime) / 86400
    if age_days > max_staleness_days:
        print(f"  WARNING: {path} is {age_days:.0f} days old "
              f"(staleness threshold: {max_staleness_days:.0f})")

    with open(p) as f:
        data = json.load(f)

    entities_raw = data if isinstance(data, list) else data.get("entities", [])
    return [LIDEntity.from_dict(e) for e in entities_raw]


class DynamicsProjector:
    """
    Base class: reads an LID entity + environment and emits Basins.

    Layer 4 — the DynamicsProjector translates an intelligence profile's
    dynamics, physics couplings, and environmental context into
    constraint-geometry Basins that the Mandala can breathe.

    Subclass this for each intelligence category:
      AnimalProjector  → swarm dynamics, neural architecture
      CrystalProjector → lattice modes, piezoelectric coupling
      MycelialProjector → network topology, chemical signaling
      PlasmaProjector  → MHD modes, magnetic confinement
    """

    def project(self, entity: LIDEntity,
                environment: Optional[dict] = None) -> list:
        """
        Emit one or more Basins from an LID entity.

        Subclasses override this to implement domain-specific projection.
        The base implementation emits a single generic basin.
        """
        env = environment or entity.environment
        cap = StreamCapability(
            domain=entity.category,
            substrate=entity.substrate_type,
            coverage_fraction=0.5,
            confidence=0.5,
        )
        return [Basin(
            domain=entity.category,
            substrate=entity.substrate_type,
            support=entity.spatial_extent or ("generic", 0, 1),
            depth=0.5,
            signature={
                "entity_id": entity.entity_id,
                "dynamics": entity.dynamics,
                "environment": env,
            },
            source_capability=cap,
            provenance=self._make_provenance(entity),
        )]

    @staticmethod
    def _make_provenance(entity: LIDEntity) -> dict:
        """Build provenance record for a projected Basin."""
        return {
            "projector": "DynamicsProjector",
            "entity_id": entity.entity_id,
            "entity_name": entity.name,
            "substrate_type": entity.substrate_type,
            "source": entity.metadata.get("description", "")[:100] if entity.metadata else "",
            "observer_tradition": entity.metadata.get("observer_tradition", "default"),
        }


class AnimalProjector(DynamicsProjector):
    """
    Project animal intelligence profiles into Basins.

    Reads swarm dynamics (gradient following, trajectory geometry,
    communication bandwidth), neural architecture (distributed vs
    centralised), and environmental coupling (thermal, chemical,
    acoustic, magnetic).
    """

    def project(self, entity: LIDEntity,
                environment: Optional[dict] = None) -> list:
        env = environment or entity.environment
        dyn = entity.dynamics
        basins = []

        gradient_field = dyn.get("gradient_field", {})
        if gradient_field:
            strength = gradient_field.get("strength", 0.5)
            cap = StreamCapability(
                domain=entity.category,
                substrate=entity.substrate_type,
                coverage_fraction=gradient_field.get("coverage", 0.7),
                confidence=gradient_field.get("confidence", 0.6),
            )
            basins.append(Basin(
                domain=entity.category,
                substrate=entity.substrate_type,
                support=entity.spatial_extent or ("swarm_volume", 0, 1),
                depth=min(1.0, strength),
                signature={
                    "mode": "gradient_following",
                    "gradient_strength": strength,
                    "gradient_direction": gradient_field.get("direction", [0, 0, 1]),
                    "swarm_size": dyn.get("swarm_size", 1),
                    "communication_bandwidth": dyn.get("communication_bandwidth", 0),
                },
                source_capability=cap,
            ))

        trajectory = dyn.get("trajectory_geometry", {})
        if trajectory:
            cap = StreamCapability(
                domain=entity.category,
                substrate=entity.substrate_type,
                coverage_fraction=0.6,
                confidence=0.7,
            )
            basins.append(Basin(
                domain=entity.category,
                substrate=entity.substrate_type,
                support=entity.spatial_extent or ("trajectory_space", 0, 1),
                depth=0.7,
                signature={
                    "mode": "trajectory_geometry",
                    "pattern": trajectory.get("pattern", "random_walk"),
                    "persistence_length": trajectory.get("persistence_length", 0),
                    "dimensionality": trajectory.get("dimensionality", 3),
                },
                source_capability=cap,
            ))

        # LID real-schema path: read from dynamics["patterns"] list
        lid_patterns = dyn.get("patterns", [])
        if not basins and lid_patterns:
            for pat in lid_patterns:
                if not isinstance(pat, dict):
                    continue
                eff = pat.get("efficiency_factor", 0.5)
                cap = StreamCapability(
                    domain=entity.category,
                    substrate=entity.substrate_type,
                    coverage_fraction=0.7,
                    confidence=min(1.0, eff),
                )
                basins.append(Basin(
                    domain=entity.category,
                    substrate=entity.substrate_type,
                    support=entity.spatial_extent or ("pattern_space", 0, 1),
                    depth=min(1.0, eff),
                    signature={
                        "mode": pat.get("type", pat.get("name", "unknown")),
                        "pattern_name": pat.get("name", ""),
                        "geometry": pat.get("geometry", ""),
                        "efficiency": eff,
                        "applications": pat.get("applications", []),
                    },
                    source_capability=cap,
                ))

        if not basins:
            return super().project(entity, environment)
        prov = self._make_provenance(entity)
        prov["projector"] = "AnimalProjector"
        # Measurable collectivity: multiple patterns with coordination/swarm types
        coordination_patterns = [p for p in (dyn.get("patterns", []))
                                 if isinstance(p, dict)
                                 and p.get("type", "") in ("distributed_processing",
                                     "energy_efficiency", "swarm_coordination")]
        prov["is_collective"] = len(coordination_patterns) >= 1
        prov["collectivity_evidence"] = (f"{len(coordination_patterns)} coordination "
                                         f"patterns (measured, not string-matched)")
        for b in basins:
            b.provenance = prov
        return basins


class CrystalProjector(DynamicsProjector):
    """
    Project crystal/mineral intelligence profiles into Basins.

    Reads lattice structure (symmetry group, phonon modes),
    piezoelectric coupling, defect dynamics, and thermal response.
    """

    def project(self, entity: LIDEntity,
                environment: Optional[dict] = None) -> list:
        env = environment or entity.environment
        dyn = entity.dynamics
        basins = []

        lattice = dyn.get("lattice", {})
        if lattice:
            cap = StreamCapability(
                domain=entity.category,
                substrate=entity.substrate_type,
                coverage_fraction=lattice.get("coverage", 0.9),
                confidence=lattice.get("confidence", 0.8),
            )
            basins.append(Basin(
                domain=entity.category,
                substrate=entity.substrate_type,
                support=entity.spatial_extent or ("crystal_volume", 0, 1),
                depth=0.8,
                signature={
                    "mode": "lattice_modes",
                    "symmetry_group": lattice.get("symmetry_group", "unknown"),
                    "phonon_modes": lattice.get("phonon_modes", 0),
                    "defect_density": lattice.get("defect_density", 0),
                    "temperature_K": env.get("temperature_K", 293),
                },
                source_capability=cap,
            ))

        piezo = dyn.get("piezoelectric", {})
        if piezo:
            cap = StreamCapability(
                domain=entity.category,
                substrate=entity.substrate_type,
                coverage_fraction=0.7,
                confidence=piezo.get("confidence", 0.7),
            )
            basins.append(Basin(
                domain=entity.category,
                substrate=entity.substrate_type,
                support=entity.spatial_extent or ("crystal_surface", 0, 1),
                depth=0.6,
                signature={
                    "mode": "piezoelectric_coupling",
                    "d33_pC_N": piezo.get("d33_pC_N", 0),
                    "resonant_freq_Hz": piezo.get("resonant_freq_Hz", 0),
                    "coupling_factor": piezo.get("coupling_factor", 0),
                },
                source_capability=cap,
            ))

        if not basins:
            return super().project(entity, environment)
        prov = self._make_provenance(entity)
        prov["projector"] = "CrystalProjector"
        for b in basins:
            b.provenance = prov
        return basins


# --- Built-in LID entities for demo / testing ---

BEE_SWARM_LID = LIDEntity(
    entity_id="LID.ANIMAL.BEE_SWARM",
    name="Honeybee Swarm",
    substrate_type="swarm.bee",
    category="animal_intelligence",
    dynamics={
        "gradient_field": {
            "strength": 0.8,
            "direction": [0, 0, 1],
            "coverage": 0.7,
            "confidence": 0.6,
        },
        "trajectory_geometry": {
            "pattern": "waggle_dance",
            "persistence_length": 0.3,
            "dimensionality": 3,
        },
        "swarm_size": 10000,
        "communication_bandwidth": 0.1,
    },
    environment={"temperature_K": 308, "humidity": 0.6},
    physics_couplings=["thermal", "chemical", "acoustic", "magnetic"],
    spatial_extent=(0, 100),
    temporal_scale_s=60,
)

QUARTZ_LATTICE_LID = LIDEntity(
    entity_id="LID.CRYSTAL.QUARTZ",
    name="Quartz Crystal Lattice",
    substrate_type="crystal.quartz",
    category="crystal_intelligence",
    dynamics={
        "lattice": {
            "symmetry_group": "D3",
            "phonon_modes": 18,
            "defect_density": 1e-6,
            "coverage": 0.95,
            "confidence": 0.9,
        },
        "piezoelectric": {
            "d33_pC_N": 2.3,
            "resonant_freq_Hz": 32768,
            "coupling_factor": 0.1,
            "confidence": 0.85,
        },
    },
    environment={"temperature_K": 293, "pressure_Pa": 101325},
    physics_couplings=["electric", "acoustic", "thermal"],
    spatial_extent=(0, 0.01),
    temporal_scale_s=3e-5,
)


@dataclass
class AnimalCrystalCoupling:
    """
    Cross-domain coupling: animal intelligence x crystal intelligence.

    Physics: bees sense magnetic fields via magnetite crystals.
    Crystal piezoelectric response couples to acoustic swarm signals.
    Shared thermal environment affects both substrates.
    """
    domains: tuple = ("animal_intelligence", "crystal_intelligence")

    def couple(self, geom_animal: UnifiedGeometry,
               geom_crystal: UnifiedGeometry) -> dict:
        agreements = []
        tensions = []
        boosts = {}

        animal_sigs = []
        for a in (geom_animal.agreement_regions + geom_animal.tension_regions):
            animal_sigs.append(str(a).lower())
        crystal_sigs = []
        for c in (geom_crystal.agreement_regions + geom_crystal.tension_regions):
            crystal_sigs.append(str(c).lower())

        animal_text = " ".join(animal_sigs)
        crystal_text = " ".join(crystal_sigs)

        if "acoustic" in animal_text or "acoustic" in crystal_text:
            agreements.append(("bioacoustic_crystal_coupling",
                               "Swarm acoustic signals may couple to "
                               "crystal piezoelectric response"))
            boosts["animal_intelligence"] = 0.1
            boosts["crystal_intelligence"] = 0.1

        if geom_animal.substrates_used and geom_crystal.substrates_used:
            agreements.append(("cross_substrate_intelligence",
                               f"animal={[substrate_key(s) for s in geom_animal.substrates_used]}",
                               f"crystal={[substrate_key(s) for s in geom_crystal.substrates_used]}",
                               "Two distinct intelligence substrates composing "
                               "through the Mandala"))

        return {"agreements": agreements, "tensions": tensions,
                "confidence_boosts": boosts}


@dataclass
class IntelligenceIntersectionRule:
    """
    Generic intersection rule for any intelligence domain.

    Since intelligence substrates are open-ended (not enum-constrained),
    this rule handles any domain by looking for common basin signature
    patterns: gradient fields, trajectory geometry, lattice modes, etc.
    """
    domain: str = "intelligence"

    def __init__(self, domain: str = "intelligence"):
        self.domain = domain

    def intersect(self, basins: list) -> UnifiedGeometry:
        substrates = {b.substrate for b in basins}
        agreement: list = []
        tension: list = []

        modes = [b.signature.get("mode", "") for b in basins if isinstance(b.signature, dict)]
        if len(set(modes)) > 1:
            agreement.append(("multi_mode_intelligence",
                               f"modes={list(set(modes))}",
                               "Multiple intelligence modes active simultaneously"))

        grad_basins = [b for b in basins
                       if isinstance(b.signature, dict)
                       and b.signature.get("mode") == "gradient_following"]
        lattice_basins = [b for b in basins
                          if isinstance(b.signature, dict)
                          and b.signature.get("mode") == "lattice_modes"]
        if grad_basins and lattice_basins:
            agreement.append(("gradient_lattice_coupling",
                               "Gradient-following intelligence meets lattice structure"))

        # Multi-observer tension: same entity described differently
        entities_seen: dict = {}
        for b in basins:
            if b.provenance:
                eid = b.provenance.get("entity_id", "")
                tradition = b.provenance.get("observer_tradition", "default")
                if eid:
                    entities_seen.setdefault(eid, set()).add(tradition)
        for eid, traditions in entities_seen.items():
            if len(traditions) > 1:
                tension.append(("multi_observer_tension",
                                f"entity={eid}",
                                f"traditions={sorted(traditions)}",
                                "Same intelligence described by different observer "
                                "traditions — descriptions may conflict"))

        confidence = {}
        for b in basins:
            cap = b.source_capability
            conf = cap.confidence if cap else 0.5
            confidence[substrate_key(b.substrate)] = b.depth * conf
        if agreement:
            for k in confidence:
                confidence[k] = min(1.0, confidence[k] * 1.1)

        uncovered = [] if basins else [("entire_field",)]
        return UnifiedGeometry(
            domain=self.domain, substrates_used=substrates,
            agreement_regions=agreement, tension_regions=tension,
            uncovered_regions=uncovered, confidence_field=confidence,
        )


# =========================================================================
# 16. DEMO
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
            print(f"    substrates={[substrate_key(s) for s in geom.substrates_used]}")
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
    mandala.register_coupling(GravitySoundCoupling())
    mandala.register_coupling(ElectricSoundCoupling())
    mandala.register_coupling(GravityElectricCoupling())

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
        print(f"    {d}: {[substrate_key(s) for s in subs]}")

    for domain, geom in sorted(result.items()):
        if domain == "_resonance":
            print(f"\n  [RESONANCE — cross-domain coupling]")
            print(f"    domains: {geom.domains_coupled}")
            print(f"    agreements: {geom.cross_domain_agreements}")
            print(f"    tensions: {geom.cross_domain_tensions}")
            print(f"    boosts: {geom.confidence_boosts}")
            print(f"    coupling strength: {geom.coupling_strength:.2f}")
        else:
            print(f"\n  [{domain}]")
            print(f"    substrates: {[substrate_key(s) for s in geom.substrates_used]}")
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


def demo_lid_synthesis():
    """Bee swarm + quartz lattice breathe through the Mandala with RESONATE."""
    print("=" * 60)
    print("LID Synthesis — Bee Swarm + Quartz Lattice")
    print("=" * 60)

    bee_proj = AnimalProjector()
    quartz_proj = CrystalProjector()

    bee_basins = bee_proj.project(BEE_SWARM_LID)
    quartz_basins = quartz_proj.project(QUARTZ_LATTICE_LID)

    print(f"\n  Bee basins:    {len(bee_basins)}")
    for b in bee_basins:
        print(f"    substrate={substrate_key(b.substrate):20s}  "
              f"depth={b.depth:.2f}  mode={b.signature.get('mode', '?')}")

    print(f"\n  Quartz basins: {len(quartz_basins)}")
    for b in quartz_basins:
        print(f"    substrate={substrate_key(b.substrate):20s}  "
              f"depth={b.depth:.2f}  mode={b.signature.get('mode', '?')}")

    mandala = MandalaRuntime()
    mandala.register(IntelligenceIntersectionRule(domain="animal_intelligence"))
    mandala.register(IntelligenceIntersectionRule(domain="crystal_intelligence"))
    mandala.register_coupling(AnimalCrystalCoupling())
    mandala.enable_synthesis()

    all_basins = bee_basins + quartz_basins

    class _BasinStream:
        def __init__(self, basin):
            self._basin = basin
        @property
        def capability(self):
            return self._basin.source_capability
        def read(self):
            return self._basin.signature
        def project_to_basin(self):
            return self._basin

    streams = [_BasinStream(b) for b in all_basins]
    result, manifest = mandala.breathe_with_manifest(streams)

    print(f"\n  Information axes: {manifest.total_information_axes}")
    print(f"  Domains: {list(manifest.domain_coverage.keys())}")

    for domain, geom in sorted(result.items()):
        if domain == "_resonance":
            print(f"\n  [RESONANCE — cross-domain coupling]")
            print(f"    domains: {geom.domains_coupled}")
            for a in geom.cross_domain_agreements:
                print(f"    AGREE: {a[0]}")
            for t in geom.cross_domain_tensions:
                print(f"    TENSION: {t[0]}")
            print(f"    boosts: {geom.confidence_boosts}")
            print(f"    coupling strength: {geom.coupling_strength:.2f}")
            if geom.synthesis_products:
                print(f"    SYNTHESIS ({len(geom.synthesis_products)} new basins generated):")
                for sp in geom.synthesis_products:
                    print(f"      {sp.operation} -> {sp.product}")
                    print(f"        why: {sp.why}")
        else:
            print(f"\n  [{domain}]")
            print(f"    substrates: {[substrate_key(s) for s in geom.substrates_used]}")
            if geom.agreement_regions:
                for a in geom.agreement_regions:
                    print(f"    AGREE: {a[0]}")
            print(f"    confidence: {geom.confidence_field}")

    # Drill-down preview
    print(f"\n  Drill-down preview (future-proof):")
    bee_sub = bee_basins[0].substrate if isinstance(bee_basins[0].substrate, str) else bee_basins[0].substrate
    if isinstance(bee_sub, str):
        print(f"    {bee_sub} -> (string substrates support drill via naming)")
    else:
        print(f"    {bee_sub} (substrate is enum or string)")
    print()


if __name__ == "__main__":
    demo_breathing()
    demo_classifiers()
    demo_multi_domain()
    demo_paradigm_registry()
    demo_lid_synthesis()
    print("=" * 60)
    print("The Mandala breathes. Substrates fuse. Geometry emerges.")
    print("=" * 60)
