"""
MANDALA RUNTIME v1.0
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
# 8. DEMO
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


if __name__ == "__main__":
    demo_breathing()
    print("=" * 60)
    print("The Mandala breathes. Substrates fuse. Geometry emerges.")
    print("=" * 60)
