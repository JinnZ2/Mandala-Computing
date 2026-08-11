"""
concept_atlas.py — the data layer for the bloom: glyphs, concepts, similarity.

Deliberately **stdlib + numpy only**. No torch. Everything here — the emoji
concept map, the Atlas entries, the multi-hot encodings and the blended
similarity matrix — is available whether or not a training backend is
installed, so `mandala_bloom.bloom_bridge` can turn a saved bloom into a
`mandala_stack` geometry on a machine that has never seen PyTorch.

The split matters: the *semantics* (what a glyph means, which entries are
alike) are repo data. The *optimiser* (gradient flow over a learned metric)
is one way to act on them, not the only one.
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

try:
    import numpy as np
except ImportError:  # pragma: no cover - numpy is a repo dependency
    np = None


# ---------------------------------------------------------------------------
# The concept vocabulary
# ---------------------------------------------------------------------------

#: Emoji -> plain-language meaning. This is the concept alphabet the bloom
#: organises. Order is not meaningful; `CONCEPTS` fixes a stable index.
EMOJI_MAP: Dict[str, str] = {
    "∞": "continuity",
    "↻": "recursion",
    "⚖️": "balance",
    "🧭": "navigation",
    "🌱": "growth",
    "⏳": "time shift",
    "🕸️": "interconnection",
    "🪞": "reflection",
    "💥": "rupture",
    "🪐": "cycles within cycles",
    "📡": "resonance detection",
    "🧬": "inheritance and evolution",
    "🔥": "transformation",
    "💧": "purification or essence",
    "🪨": "grounding and memory",
    "🦋": "emergent change",
    "🦂": "edge behavior or toxicity",
    "🦉": "wisdom during collapse",
    "🧠": "logic seed",
    "💤": "dormancy",
    "🛡️": "protection",
    "🪶": "lightness or ancestral presence",
}

#: Stable, sorted concept ordering. Index into this, never into a dict.
CONCEPTS: Tuple[str, ...] = tuple(sorted(EMOJI_MAP))
CONCEPT_INDEX: Dict[str, int] = {emoji: i for i, emoji in enumerate(CONCEPTS)}
NUM_CONCEPTS = len(CONCEPTS)


def concept_id(emoji: str) -> int:
    """Index of a concept emoji, with a readable error for typos.

    The original scripts guarded one emoji and indexed another
    (`concept_to_idx["🔄"] if "↻" in concept_to_idx`), which raises a bare
    KeyError naming a character that is hard to tell apart from the intended
    one. This says which symbol is missing and what is available.
    """
    try:
        return CONCEPT_INDEX[emoji]
    except KeyError:
        raise KeyError(
            f"{emoji!r} is not in the concept map. "
            f"Did you mean one of: {' '.join(CONCEPTS)}"
        ) from None


# ---------------------------------------------------------------------------
# Ways of knowing (base 4) — the traversal modes
# ---------------------------------------------------------------------------

#: Mode index -> name. Defined once so the training labels and the report
#: labels cannot drift apart (in the pasted scripts the comment said
#: "1 = analogy, 2 = intuition" while the printout said the reverse).
KNOWING_MODES: Tuple[str, ...] = ("logic", "analogy", "intuition")
MODE_INDEX: Dict[str, int] = {name: i for i, name in enumerate(KNOWING_MODES)}
NUM_MODES = len(KNOWING_MODES)


# ---------------------------------------------------------------------------
# Atlas entries
# ---------------------------------------------------------------------------

class AtlasEntry:
    """One Atlas entry: a glyph string, a concept path, and a way of knowing.

    `concept_path` is an ordered sequence — the story the entry tells. Order
    is load-bearing: the child manifold treats it as a *curve*, and curvature
    along that curve is part of the energy.
    """

    __slots__ = ("entry_id", "name", "glyphs", "concept_path", "mode")

    def __init__(self, entry_id: str, name: str, glyphs: str,
                 concept_path: Sequence[str], mode: str):
        self.entry_id = entry_id
        self.name = name
        self.glyphs = glyphs
        self.concept_path = tuple(concept_path)
        if mode not in MODE_INDEX:
            raise ValueError(f"unknown way of knowing {mode!r}; "
                             f"expected one of {KNOWING_MODES}")
        self.mode = mode

    @property
    def concept_ids(self) -> Tuple[int, ...]:
        return tuple(concept_id(c) for c in self.concept_path)

    @property
    def mode_id(self) -> int:
        return MODE_INDEX[self.mode]

    def story(self) -> str:
        """The concept path as readable prose."""
        return " → ".join(f"{c} ({EMOJI_MAP[c]})" for c in self.concept_path)

    def __repr__(self) -> str:
        return f"AtlasEntry({self.entry_id} {self.name!r}, {len(self.concept_path)} concepts)"


#: The four entries the bloom was built around.
ENTRIES: Tuple[AtlasEntry, ...] = (
    AtlasEntry(
        "0001", "Resonant Honeycomb Infrastructure",
        "◇⚙➝〰〰〰⬡ᘯᘰ⇑◧",
        ["🪨", "🛡️", "🧭", "🕸️", "∞", "📡", "⚖️"],
        mode="logic",
    ),
    AtlasEntry(
        "0002", "Echolocating Autonomy",
        "⋮⋯⋮▁▃▅∿◉∙∙●🦇🐬ᘯᘰ⇑◧",
        ["🧠", "📡", "🌱", "🧬", "🦉", "🦋"],
        mode="intuition",
    ),
    AtlasEntry(
        "0003", "Family Node Manufacturing",
        "⚙➝⬡⟳⒮⇑◉ᘯᘰ▁▃▅∿◧",
        ["🪨", "🔥", "🕸️", "↻", "🧬", "🛡️", "⚖️"],
        mode="logic",
    ),
    AtlasEntry(
        "0011", "Coral Reef Symbiotic Resonance",
        "◇⒮⬡⇑〰〰〰△≈ᘯᘰ∞◧",
        ["🪨", "💧", "🧬", "🕸️", "∞", "📡", "💥", "⚖️"],
        mode="analogy",
    ),
)


# ---------------------------------------------------------------------------
# Encodings
# ---------------------------------------------------------------------------

def glyph_alphabet(entries: Sequence[AtlasEntry] = ENTRIES) -> Tuple[str, ...]:
    """Every distinct glyph character across the entries, sorted."""
    return tuple(sorted({ch for e in entries for ch in e.glyphs}))


def glyph_matrix(entries: Sequence[AtlasEntry] = ENTRIES):
    """(N, G) multi-hot glyph presence matrix."""
    alphabet = glyph_alphabet(entries)
    index = {ch: i for i, ch in enumerate(alphabet)}
    matrix = np.zeros((len(entries), len(alphabet)), dtype=np.float64)
    for row, entry in enumerate(entries):
        for ch in entry.glyphs:
            matrix[row, index[ch]] = 1.0
    return matrix


def concept_matrix(entries: Sequence[AtlasEntry] = ENTRIES):
    """(N, C) multi-hot concept presence matrix."""
    matrix = np.zeros((len(entries), NUM_CONCEPTS), dtype=np.float64)
    for row, entry in enumerate(entries):
        for cid in entry.concept_ids:
            matrix[row, cid] = 1.0
    return matrix


def concept_paths(entries: Sequence[AtlasEntry] = ENTRIES):
    """(N, L) padded concept-path matrix. Pad value is -1."""
    paths = [list(e.concept_ids) for e in entries]
    width = max(len(p) for p in paths)
    padded = np.full((len(paths), width), -1, dtype=np.int64)
    for row, path in enumerate(paths):
        padded[row, :len(path)] = path
    return padded


def jaccard(matrix):
    """Pairwise Jaccard similarity of multi-hot rows."""
    inter = matrix @ matrix.T
    counts = matrix.sum(axis=1)
    union = counts[None, :] + counts[:, None] - inter
    return inter / (union + 1e-8)


def similarity(entries: Sequence[AtlasEntry] = ENTRIES,
               concept_weight: float = 0.6):
    """Blended concept/glyph similarity — the target the parent stress fits.

    `concept_weight` splits between meaning (concept overlap) and surface
    form (glyph overlap). The default leans on meaning, since two entries can
    share the ᘯᘰ⇑◧ tail without being about the same thing.
    """
    if not 0.0 <= concept_weight <= 1.0:
        raise ValueError("concept_weight must be in [0, 1]")
    sim_concept = jaccard(concept_matrix(entries))
    sim_glyph = jaccard(glyph_matrix(entries))
    return concept_weight * sim_concept + (1.0 - concept_weight) * sim_glyph


def target_distance(entries: Sequence[AtlasEntry] = ENTRIES,
                    concept_weight: float = 0.6):
    """`1 - similarity` — what the parent embedding tries to realise as
    geometric distance. This is the same shape of contract as the
    `dist_fn` that `mandala_stack.GeometryLearner.learn()` consumes."""
    return 1.0 - similarity(entries, concept_weight)


def entry_distance_fn(entries: Sequence[AtlasEntry] = ENTRIES,
                      concept_weight: float = 0.6):
    """A callable `(entry, entry) -> float` over `AtlasEntry` objects.

    This is the hand-off point to the rest of the repo: it is exactly the
    signature `mandala_stack.GeometryLearner.learn(items, dist_fn)` wants, so
    the Atlas can be embedded by the stack's learner with no bloom training
    at all. `bloom_bridge.learn_atlas_geometry()` does precisely that.
    """
    order = {entry.entry_id: i for i, entry in enumerate(entries)}
    matrix = target_distance(entries, concept_weight)

    def distance(a: AtlasEntry, b: AtlasEntry) -> float:
        return float(matrix[order[a.entry_id], order[b.entry_id]])

    return distance


def summary() -> str:
    """Human-readable description of the loaded atlas."""
    lines = [
        f"Atlas: {len(ENTRIES)} entries, {NUM_CONCEPTS} concepts, "
        f"{len(glyph_alphabet())} distinct glyphs",
    ]
    for entry in ENTRIES:
        lines.append(f"  {entry.entry_id}  {entry.name}")
        lines.append(f"        glyphs: {entry.glyphs}")
        lines.append(f"        mode:   {entry.mode}")
        lines.append(f"        path:   {' → '.join(entry.concept_path)}")
    return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 68)
    print("CONCEPT ATLAS")
    print("=" * 68)
    print(summary())

    print("\nBlended similarity (0.6 concept / 0.4 glyph):")
    sim = similarity()
    header = "".join(f"{e.entry_id:>9s}" for e in ENTRIES)
    print(f"{'':>10s}{header}")
    for i, entry in enumerate(ENTRIES):
        row = "".join(f"{sim[i, j]:9.3f}" for j in range(len(ENTRIES)))
        print(f"{entry.entry_id:>10s}{row}")

    print("\nClosest pair, and furthest:")
    best = (None, -1.0)
    worst = (None, 2.0)
    for i in range(len(ENTRIES)):
        for j in range(i + 1, len(ENTRIES)):
            pair = (ENTRIES[i].name, ENTRIES[j].name)
            if sim[i, j] > best[1]:
                best = (pair, sim[i, j])
            if sim[i, j] < worst[1]:
                worst = (pair, sim[i, j])
    print(f"  closest:  {best[0][0]} <-> {best[0][1]}  ({best[1]:.3f})")
    print(f"  furthest: {worst[0][0]} <-> {worst[0][1]}  ({worst[1]:.3f})")
