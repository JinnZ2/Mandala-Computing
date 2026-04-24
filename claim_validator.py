"""
CLAIM VALIDATOR v1.0
Multi-epistemological validation for natural language claims.

Ported from Inversion's validation_framework.py into Mandala-Computing.
Stdlib only — no external dependencies.

Five validation dimensions:
  1. Information Entropy — character/word Shannon entropy, compressibility
  2. Falsifiability — quantifier specificity, temporal grounding, measurability
  3. Internal Consistency — relation extraction, contradiction detection
  4. Citation Analysis — source diversity, age, authority concentration
  5. Cross-Domain Aggregation — weighted concern score with multi-domain boost

Tier hierarchy (from Inversion's fieldlink.py):
  Tier 1: Physics / Thermodynamics — hardest constraints
  Tier 2: Biology / Evolution — grounded in physical reality
  Tier 3: Systems Dynamics — emergent from Tiers 1-2
  Tier 4: Empirical Observation — evidence and measurement

Higher tiers cannot violate lower tiers. A systems claim that
contradicts thermodynamics fails at Tier 1, regardless of Tier 3 score.

Usage:
    from claim_validator import validate_claim, print_report
    report = validate_claim("This system increases efficiency by 300%.")
    print_report(report)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
import math
import re
import string
import zlib


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

_PUNCT_TABLE = str.maketrans("", "", string.punctuation)


def tokenize(text: str) -> list:
    return [w for w in text.lower().translate(_PUNCT_TABLE).split() if w]


def sentencize(text: str) -> list:
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in parts if s.strip()]


# ---------------------------------------------------------------------------
# Metric 1: Information Entropy
# ---------------------------------------------------------------------------

def char_entropy(text: str) -> float:
    """Shannon entropy over characters (bits)."""
    if not text:
        return 0.0
    counts = Counter(text.lower())
    total = len(text)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def word_entropy(tokens: list) -> float:
    """Shannon entropy over words (bits)."""
    if not tokens:
        return 0.0
    counts = Counter(tokens)
    total = len(tokens)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def compressibility(text: str) -> float:
    """Compression ratio (zlib proxy for Kolmogorov complexity)."""
    if not text:
        return 0.0
    original = text.encode("utf-8")
    compressed = zlib.compress(original, 9)
    return 1.0 - len(compressed) / len(original)


@dataclass
class EntropyResult:
    char_entropy_bits: float
    word_entropy_bits: float
    compressibility_ratio: float
    interpretation: str


def analyze_entropy(text: str, tokens: list) -> EntropyResult:
    h_char = char_entropy(text)
    h_word = word_entropy(tokens)
    comp = compressibility(text)
    issues = []
    if h_char < 3.0:
        issues.append("very low character entropy (highly repetitive)")
    if h_char > 4.8:
        issues.append("unusually high character entropy (possibly random/encoded)")
    if comp > 0.7:
        issues.append(f"high compressibility ({comp:.0%}) -- low information density")
    return EntropyResult(
        round(h_char, 4), round(h_word, 4), round(comp, 4),
        "; ".join(issues) if issues else "entropy within normal range",
    )


# ---------------------------------------------------------------------------
# Metric 2: Falsifiability (Popper 1959)
# ---------------------------------------------------------------------------

SPECIFIC_QUANTIFIERS = re.compile(
    r"\b\d+\.?\d*\s*%|\b\d+\.?\d*\b(?:\s*(?:times|fold|percent|kg|km|m|cm|mm|"
    r"hours?|days?|years?|months?|seconds?|million|billion|thousand))\b|"
    r"\bbetween\s+\d+\s+and\s+\d+\b|\bby\s+\d{4}\b|\bin\s+\d{4}\b",
    re.IGNORECASE,
)
VAGUE_QUANTIFIERS = re.compile(
    r"\b(many|most|some|various|significant|numerous|several|"
    r"few|substantial|considerable|a lot|a number of)\b",
    re.IGNORECASE,
)
TEMPORAL_SPECIFIC = re.compile(
    r"\b(in\s+\d{4}|by\s+\d{4}|within\s+\d+\s+\w+|"
    r"\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}|"
    r"between\s+\d{4}\s+and\s+\d{4}|from\s+\d{4}\s+to\s+\d{4}|"
    r"since\s+\d{4}|after\s+\d{4}|before\s+\d{4}|"
    r"next\s+\d+\s+\w+|over\s+\d+\s+\w+)\b",
    re.IGNORECASE,
)
TEMPORAL_VAGUE = re.compile(
    r"\b(always|never|inherently|by nature|eternally|"
    r"fundamentally|inevitably|permanently)\b",
    re.IGNORECASE,
)
MEASURABILITY_WORDS = re.compile(
    r"\b(measured|observed|counted|rate of|percentage|"
    r"correlation|statistically|empirically|quantified|"
    r"data shows|experiment|sample size|p-value|confidence interval)\b",
    re.IGNORECASE,
)
UNFALSIFIABLE_FRAMING = re.compile(
    r"\b(essentially|in principle|fundamentally|by definition|"
    r"it is known that|self-evidently|axiomatically|"
    r"it goes without saying|needless to say)\b",
    re.IGNORECASE,
)


@dataclass
class FalsifiabilityResult:
    score: float
    quantifier_specificity: float
    temporal_specificity: float
    measurability: float
    interpretation: str
    details: dict = field(default_factory=dict)


def analyze_falsifiability(text: str) -> FalsifiabilityResult:
    n_spec_q = len(SPECIFIC_QUANTIFIERS.findall(text))
    n_vague_q = len(VAGUE_QUANTIFIERS.findall(text))
    q_spec = n_spec_q / (n_spec_q + n_vague_q + 1)

    n_t_spec = len(TEMPORAL_SPECIFIC.findall(text))
    n_t_vague = len(TEMPORAL_VAGUE.findall(text))
    t_spec = n_t_spec / (n_t_spec + n_t_vague + 1)

    n_meas = len(MEASURABILITY_WORDS.findall(text))
    n_unfals = len(UNFALSIFIABLE_FRAMING.findall(text))
    meas = n_meas / (n_meas + n_unfals + 1)

    score = 0.40 * q_spec + 0.30 * meas + 0.30 * t_spec

    if score >= 0.40:
        interp = "FALSIFIABLE -- specific, testable elements"
    elif score >= 0.20:
        interp = "PARTIALLY FALSIFIABLE -- some specificity"
    else:
        interp = "LOW FALSIFIABILITY -- vague, hard to test"

    return FalsifiabilityResult(
        round(score, 4), round(q_spec, 4), round(t_spec, 4), round(meas, 4), interp,
        {"specific_q": n_spec_q, "vague_q": n_vague_q,
         "temporal_spec": n_t_spec, "temporal_vague": n_t_vague,
         "measurable": n_meas, "unfalsifiable": n_unfals},
    )


# ---------------------------------------------------------------------------
# Metric 3: Internal Consistency
# ---------------------------------------------------------------------------

POSITIVE_PRED = re.compile(
    r"\b(increases?|causes?|leads?\s+to|improves?|promotes?|"
    r"enables?|produces?|creates?|enhances?|strengthens?)\b",
    re.IGNORECASE,
)
NEGATIVE_PRED = re.compile(
    r"\b(decreases?|reduces?|prevents?|harms?|inhibits?|"
    r"destroys?|weakens?|eliminates?|undermines?|blocks?)\b",
    re.IGNORECASE,
)


@dataclass
class Relation:
    subject: str
    direction: int  # +1 or -1
    obj: str
    sentence_idx: int


@dataclass
class ConsistencyResult:
    score: float
    relations_found: int
    contradictions: list
    interpretation: str


def extract_relations(sentences: list) -> list:
    relations = []
    for idx, sent in enumerate(sentences):
        for pattern, direction in [(POSITIVE_PRED, 1), (NEGATIVE_PRED, -1)]:
            for m in pattern.finditer(sent):
                before = sent[:m.start()].strip().split()[-3:]
                after = sent[m.end():].strip().split()[:3]
                if before and after:
                    relations.append(Relation(
                        " ".join(before).lower().strip(string.punctuation),
                        direction,
                        " ".join(after).lower().strip(string.punctuation),
                        idx,
                    ))
    return relations


def check_consistency(sentences: list) -> ConsistencyResult:
    relations = extract_relations(sentences)
    if not relations:
        return ConsistencyResult(1.0, 0, [], "No extractable relations")

    pairs = {}
    for r in relations:
        pairs.setdefault((r.subject, r.obj), []).append(r)

    contradictions = []
    for (subj, obj), rels in pairs.items():
        directions = {r.direction for r in rels}
        if len(directions) > 1:
            s1 = sentences[rels[0].sentence_idx][:80]
            s2 = next(sentences[r.sentence_idx][:80] for r in rels if r.direction != rels[0].direction)
            contradictions.append((s1, s2))

    score = 1.0 - len(contradictions) / max(len(pairs), 1)

    if not contradictions:
        interp = "CONSISTENT -- no contradictions"
    elif len(contradictions) <= 2:
        interp = f"MINOR INCONSISTENCY -- {len(contradictions)} contradiction(s)"
    else:
        interp = f"INCONSISTENT -- {len(contradictions)} contradictions"

    return ConsistencyResult(round(max(0.0, score), 4), len(relations), contradictions, interp)


# ---------------------------------------------------------------------------
# Metric 4: Citation Analysis
# ---------------------------------------------------------------------------

CITATION_AUTHOR = re.compile(r"\(([A-Z][a-z]+(?:\s+(?:et\s+al|&\s+[A-Z][a-z]+))?)[.,]?\s*(\d{4})\)")


@dataclass
class CitationResult:
    citation_count: int
    unique_authors: int
    author_entropy: float
    mean_citation_age: float
    cite_sentence_ratio: float
    interpretation: str


def analyze_citations(text: str, sentences: list, current_year: int = 2026) -> CitationResult:
    author_matches = CITATION_AUTHOR.findall(text)
    authors = [a[0].lower() for a in author_matches]
    years = [int(a[1]) for a in author_matches]
    bracket_cites = re.findall(r"\[\d+\]", text)

    total = len(authors) + len(bracket_cites)
    unique = len(set(authors))

    if authors:
        counts = Counter(authors)
        n = len(authors)
        a_entropy = -sum((c / n) * math.log2(c / n) for c in counts.values())
    else:
        a_entropy = 0.0

    mean_age = sum(current_year - y for y in years) / len(years) if years else 0.0
    ratio = total / max(len(sentences), 1)

    issues = []
    if total == 0:
        issues.append("no citations found")
    elif unique > 0 and a_entropy < 1.0:
        issues.append("low author diversity")
    if mean_age > 20:
        issues.append(f"mean citation age {mean_age:.0f} years -- may be outdated")
    if ratio < 0.05 and len(sentences) > 5:
        issues.append("very low citation density")

    return CitationResult(
        total, unique, round(a_entropy, 4), round(mean_age, 1), round(ratio, 4),
        "; ".join(issues) if issues else "citation profile normal",
    )


# ---------------------------------------------------------------------------
# Cross-Domain Aggregation (Tier Hierarchy)
# ---------------------------------------------------------------------------

@dataclass
class DomainScore:
    name: str
    tier: int     # 1=Physics, 2=Biology, 3=Systems, 4=Empirical
    score: float  # [0,1] — higher = more concern
    interpretation: str


@dataclass
class ValidationReport:
    claim: str
    entropy: EntropyResult
    falsifiability: FalsifiabilityResult
    consistency: ConsistencyResult
    citations: CitationResult
    domain_scores: list
    overall_concern: float
    interpretation: str


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def validate_claim(text: str) -> ValidationReport:
    """
    Full multi-epistemological validation.

    Returns concern scores across four tiers:
      T1 Physics — falsifiability + compressibility
      T2 Biology — falsifiability + temporal grounding
      T3 Systems — consistency + information density
      T4 Empirical — citations + measurability

    Higher tiers cannot override lower tier violations.
    """
    tokens = tokenize(text)
    sentences = sentencize(text)

    entropy = analyze_entropy(text, tokens)
    falsifiability = analyze_falsifiability(text)
    consistency = check_consistency(sentences)
    citations = analyze_citations(text, sentences)

    domains = []

    # Tier 1: Physics / Thermodynamics
    phys = (
        0.5 * (1.0 - _clamp(falsifiability.score / 0.4))
        + 0.5 * _clamp(entropy.compressibility_ratio / 0.6)
    )
    domains.append(DomainScore("Physics / Thermodynamics", 1, round(phys, 4),
                               "Testability and information density"))

    # Tier 2: Biology / Evolution
    bio = (
        0.6 * (1.0 - _clamp(falsifiability.score / 0.4))
        + 0.4 * (1.0 - _clamp(falsifiability.temporal_specificity / 0.3))
    )
    domains.append(DomainScore("Biology / Evolution", 2, round(bio, 4),
                               "Temporal grounding and testability"))

    # Tier 3: Systems Dynamics
    sys_c = (
        0.5 * (1.0 - _clamp(consistency.score))
        + 0.5 * _clamp(entropy.compressibility_ratio / 0.5)
    )
    domains.append(DomainScore("Systems Dynamics", 3, round(sys_c, 4),
                               "Consistency and information density"))

    # Tier 4: Empirical Observation
    emp = (
        0.4 * (1.0 - _clamp(citations.cite_sentence_ratio / 0.1))
        + 0.3 * (1.0 - _clamp(falsifiability.measurability / 0.3))
        + 0.3 * (1.0 - _clamp(citations.author_entropy / 2.0))
    )
    domains.append(DomainScore("Empirical Observation", 4, round(emp, 4),
                               "Evidence base and measurement"))

    # Aggregate: tier hierarchy — lower tiers DOMINATE higher tiers.
    # T1 (physics/thermo) concern floors the overall score.
    # If T1 fails, the claim fails regardless of T3/T4 success.
    tier_weights = {1: 0.40, 2: 0.25, 3: 0.20, 4: 0.15}
    weighted_score = sum(
        tier_weights.get(d.tier, 0.1) * d.score for d in domains
    )
    n_flagged = sum(1 for d in domains if d.score > 0.5)
    multi_boost = 0.1 * max(0, n_flagged - 2)

    # T1 floor: if physics/thermo concern > 0.6, it becomes the minimum
    t1_score = next((d.score for d in domains if d.tier == 1), 0)
    if t1_score > 0.6:
        weighted_score = max(weighted_score, t1_score)

    overall = round(_clamp(weighted_score + multi_boost), 4)

    if overall < 0.25:
        interp = "LOW CONCERN -- epistemically sound"
    elif overall < 0.50:
        interp = "MODERATE CONCERN -- structural weaknesses"
    elif overall < 0.70:
        interp = "HIGH CONCERN -- multiple red flags"
    else:
        interp = "VERY HIGH CONCERN -- fails multiple dimensions"

    return ValidationReport(
        text, entropy, falsifiability, consistency, citations,
        domains, overall, interp,
    )


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def print_report(report: ValidationReport):
    print("=" * 70)
    print("  EPISTEMOLOGICAL VALIDATION REPORT")
    print("=" * 70)

    claim = report.claim[:200] + "..." if len(report.claim) > 200 else report.claim
    print(f"\n  Claim: \"{claim}\"\n")

    e = report.entropy
    print(f"  [1] Entropy: char={e.char_entropy_bits:.2f}b  word={e.word_entropy_bits:.2f}b"
          f"  compress={e.compressibility_ratio:.2f}")
    print(f"      {e.interpretation}")

    f = report.falsifiability
    print(f"\n  [2] Falsifiability: {f.score:.4f}  (quantifier={f.quantifier_specificity:.2f}"
          f"  temporal={f.temporal_specificity:.2f}  measurable={f.measurability:.2f})")
    print(f"      {f.interpretation}")

    c = report.consistency
    print(f"\n  [3] Consistency: {c.score:.4f}  ({c.relations_found} relations,"
          f" {len(c.contradictions)} contradictions)")
    print(f"      {c.interpretation}")

    ci = report.citations
    print(f"\n  [4] Citations: {ci.citation_count} total, {ci.unique_authors} unique,"
          f" entropy={ci.author_entropy:.2f}b, age={ci.mean_citation_age:.0f}y")
    print(f"      {ci.interpretation}")

    print(f"\n  [5] Tier Scores:")
    for d in report.domain_scores:
        bar = "#" * int(d.score * 20) + "." * (20 - int(d.score * 20))
        print(f"      T{d.tier} [{bar}] {d.score:.4f}  {d.name}")

    print(f"\n  {'=' * 70}")
    print(f"  OVERALL: {report.overall_concern:.4f}  --  {report.interpretation}")
    print(f"  {'=' * 70}")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo():
    print("=" * 70)
    print("CLAIM VALIDATOR: Epistemological Validation")
    print("=" * 70)

    claims = [
        # Good claim — specific, testable, cited
        "Solar panel efficiency increased by 23% between 2020 and 2024 "
        "(Green et al. 2024), with a measured degradation rate of 0.5% per year "
        "observed across 1200 installations in 15 countries.",

        # Vague claim — no specifics, unfalsifiable
        "This technology fundamentally transforms everything and is essentially "
        "the most significant breakthrough in principle for many important applications.",

        # Mixed claim — some specifics but inconsistent
        "The system increases efficiency by 300%. The system reduces output "
        "significantly. Many experts agree this is substantial.",
    ]

    for i, claim in enumerate(claims):
        print(f"\n  --- Claim {i + 1} ---")
        report = validate_claim(claim)
        print_report(report)


if __name__ == "__main__":
    demo()
