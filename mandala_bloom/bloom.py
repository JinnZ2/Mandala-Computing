"""
bloom.py — two-level mandala bloom over the concept atlas.

    level 0 (parent)  each Atlas entry is a point u_i in R^d, laid out so that
                      instrument-measured distance matches concept/glyph
                      dissimilarity
    level 1 (child)   each entry's concept path is a *curve* on its own child
                      manifold, whose geometry is generated from u_i by a
                      hypernetwork

The two levels are tied by a cross-scale term: the metric the parent sees at
u_i should match the average metric along that entry's child curve. That
coupling is the reason this is a bloom rather than two independent fits — the
position of an entry in the large space and the shape of its own small space
are one object.

The hypernetwork gradient path
------------------------------
The obvious way to build a generated network is to make an `nn.Linear` and
assign `layer.weight.data = W`. It runs, trains, prints falling losses — and
the hypernetwork receives **exactly zero gradient**, because `.data`
assignment detaches from the graph. The generation is then decorative: child
geometries are produced but never learned, and the cross-scale coupling is
inert.

`_ChildManifold` instead applies the generated tensors with
`torch.func.functional_call` against a parameterless template. The child stays
a real function of `u_i`, `jacrev`/`vmap` still work on it, and gradient flows
back to the hypernetwork. `tests/test_core.py` asserts the gradient is
non-zero, so this cannot silently regress.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import torch
import torch.nn as nn
from torch.func import functional_call, jacrev, vmap

try:
    from ._paths import bootstrap
except ImportError:  # executed as a plain script
    from _paths import bootstrap
bootstrap()

import concept_atlas as atlas
from bases import (
    AttunementField, CalibrationField, InstrumentField, KnowingField,
    UnknownField, attunement_coherence, calibration_smoothness,
    instrument_stress, metric_curvature, mode_alignment, pullback_metric,
    unknown_mass,
)


__all__ = [
    "BloomConfig", "BloomResult", "MandalaBloom", "EntryEncoder",
    "ContinuousManifold", "Hypernetwork", "ConceptEmbedder",
]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class BloomConfig:
    """Everything tunable, in one place."""
    parent_dim: int = 2         # intrinsic dimension of the parent chart
    ambient_dim: int = 3        # embedding dimension the metric is pulled from
    child_dim: int = 2          # intrinsic dimension of each child chart
    child_hidden: int = 6
    hidden: int = 16
    concept_weight: float = 0.6
    epochs: int = 2000
    lr: float = 0.02
    seed: Optional[int] = 0

    #: Which bases are active. Turning them all off leaves plain stress
    #: majorisation — the ablation the README reports against.
    use_instruments: bool = True
    use_metrology: bool = True
    use_knowing: bool = True
    use_unknowns: bool = True
    use_attunement: bool = True

    weights: Dict[str, float] = field(default_factory=lambda: {
        "stress": 1.0,
        "curvature": 0.01,
        "calibration": 0.1,
        "unknowns": 0.1,
        "knowing": 0.05,
        "attunement": 0.2,
        "child_curvature": 0.5,
        "cross_scale": 0.2,
    })


@dataclass
class BloomResult:
    """A trained bloom, reduced to plain data.

    Deliberately torch-free — `positions` is a list of tuples, not a tensor —
    so it can be pickled, written to JSON, and consumed by
    `bloom_bridge.geometry_from_bloom()` on a machine without PyTorch.
    """
    entry_ids: List[str]
    names: List[str]
    positions: List[Tuple[float, ...]]
    instrument: List[List[List[float]]]
    calibration: List[float]
    unknowns: List[float]
    attunement: List[float]
    modes: List[str]
    loss_history: List[float]
    term_history: Dict[str, List[float]]
    config: BloomConfig

    def position_of(self, entry_id: str) -> Tuple[float, ...]:
        return self.positions[self.entry_ids.index(entry_id)]

    def report(self) -> str:
        lines = ["=" * 76,
                 "MANDALA BLOOM — parent chart with the seven bases",
                 "=" * 76]
        for i, name in enumerate(self.names):
            x, y = self.positions[i][0], self.positions[i][1]
            inst = self.instrument[i]
            det = inst[0][0] * inst[1][1] - inst[0][1] * inst[1][0]
            lines.append(
                f"{name:34s} ({x:+.3f},{y:+.3f})  "
                f"omega={self.attunement[i]:.3f}  kappa={self.unknowns[i]:.3f}  "
                f"mu={self.calibration[i]:+.3f}  |I|={det:.3f}  {self.modes[i]}"
            )
        lines.append("")
        lines.append(f"final loss {self.loss_history[-1]:.4f} "
                     f"(from {self.loss_history[0]:.4f})")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Level 0 — parent
# ---------------------------------------------------------------------------

class EntryEncoder(nn.Module):
    """(glyph multi-hot, concept multi-hot) -> parent coordinate u in R^d."""

    def __init__(self, glyph_dim: int, concept_dim: int, d: int = 2,
                 hidden: int = 16):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(glyph_dim + concept_dim, hidden), nn.Tanh(),
            nn.Linear(hidden, d),
        )

    def forward(self, glyphs: torch.Tensor, concepts: torch.Tensor) -> torch.Tensor:
        return self.net(torch.cat([glyphs, concepts], dim=-1))


class ContinuousManifold(nn.Module):
    """Smooth embedding R^d -> R^D. The metric is its pullback."""

    def __init__(self, d: int = 2, D: int = 3, hidden: int = 12):
        super().__init__()
        self.embed = nn.Sequential(
            nn.Linear(d, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, D),
        )

    def forward(self, u: torch.Tensor) -> torch.Tensor:
        return self.embed(u)


# ---------------------------------------------------------------------------
# Level 1 — children, generated from the parent point
# ---------------------------------------------------------------------------

class _ChildManifold:
    """A child embedding whose weights are tensors produced by the hypernetwork.

    Callable like a module, but holds no parameters of its own — the weights
    are graph-connected activations, so `jacrev`/`vmap` differentiate through
    them and back into the hypernetwork.
    """

    __slots__ = ("template", "params")

    def __init__(self, template: nn.Module, params: Dict[str, torch.Tensor]):
        self.template = template
        self.params = params

    def __call__(self, u: torch.Tensor) -> torch.Tensor:
        return functional_call(self.template, self.params, (u,))

    # jacrev/vmap accept any callable; this alias keeps the module-ish feel
    forward = __call__


class Hypernetwork(nn.Module):
    """u_entry -> the weights of that entry's child manifold."""

    def __init__(self, d_entry: int = 2, child_d: int = 2,
                 child_hidden: int = 6, child_D: int = 3, hidden: int = 32):
        super().__init__()
        self.child_d = child_d
        self.child_hidden = child_hidden
        self.child_D = child_D

        self.shapes = {
            "0.weight": (child_hidden, child_d),   # nn.Linear stores (out, in)
            "0.bias": (child_hidden,),
            "2.weight": (child_D, child_hidden),
            "2.bias": (child_D,),
        }
        self.n_params = sum(int(torch.tensor(s).prod()) for s in self.shapes.values())

        self.fc = nn.Sequential(
            nn.Linear(d_entry, hidden), nn.Tanh(),
            nn.Linear(hidden, self.n_params),
        )
        # Parameterless stencil defining the child architecture.
        template = nn.Sequential(
            nn.Linear(child_d, child_hidden), nn.Tanh(),
            nn.Linear(child_hidden, child_D),
        )
        for p in template.parameters():
            p.requires_grad_(False)
        self.template = template
        # Scale down the raw output so children start near-isometric.
        nn.init.zeros_(self.fc[-1].bias)
        nn.init.normal_(self.fc[-1].weight, std=0.1)

    def forward(self, u_entry: torch.Tensor) -> List[_ChildManifold]:
        flat = self.fc(u_entry)                       # (N, n_params)
        children: List[_ChildManifold] = []
        for row in range(flat.shape[0]):
            vec = flat[row]
            params: Dict[str, torch.Tensor] = {}
            offset = 0
            for name, shape in self.shapes.items():
                size = 1
                for dim in shape:
                    size *= dim
                params[name] = vec[offset:offset + size].reshape(shape)
                offset += size
            children.append(_ChildManifold(self.template, params))
        return children


class ConceptEmbedder(nn.Module):
    """Concept index -> intrinsic coordinate on a child chart."""

    def __init__(self, num_concepts: int, d: int = 2):
        super().__init__()
        self.embed = nn.Embedding(num_concepts, d)

    def forward(self, path: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        mask = path >= 0
        return self.embed(path.clamp(min=0)), mask


# ---------------------------------------------------------------------------
# Child-level energy
# ---------------------------------------------------------------------------

def curve_curvature(child: _ChildManifold, points: torch.Tensor) -> torch.Tensor:
    """Squared curvature of a concept path, arc-length normalised.

    A straight path in concept space means the entry's story unfolds without
    reversals; a sharply bent one means it turns back on itself.
    """
    if points.shape[0] < 3:
        return points.new_zeros(())
    delta = points[1:] - points[:-1]
    second = delta[1:] - delta[:-1]

    midpoints = (points[:-1] + points[1:]) / 2
    metric = pullback_metric(child, midpoints)
    arc2 = torch.einsum('bi,bij,bj->b', delta, metric, delta)
    arc = torch.sqrt(arc2.clamp(min=1e-8))
    arc_mid = (arc[:-1] + arc[1:]) / 2 + 1e-6
    return ((second / arc_mid.unsqueeze(1)) ** 2).sum(1).mean()


def cross_scale_mismatch(parent: ContinuousManifold, u_parent: torch.Tensor,
                         child: _ChildManifold,
                         points: torch.Tensor) -> torch.Tensor:
    """||g_parent(u_i) - mean g_child along the path||^2 — the level coupling."""
    if points.shape[0] == 0:
        return u_parent.new_zeros(())
    g_parent = pullback_metric(parent, u_parent)
    g_child = pullback_metric(child, points).mean(dim=0)
    return ((g_parent - g_child) ** 2).mean()


# ---------------------------------------------------------------------------
# The bloom
# ---------------------------------------------------------------------------

class MandalaBloom(nn.Module):
    """The whole two-level model plus the seven bases."""

    def __init__(self, config: Optional[BloomConfig] = None,
                 entries: Sequence[atlas.AtlasEntry] = atlas.ENTRIES):
        super().__init__()
        self.config = config or BloomConfig()
        self.entries = tuple(entries)
        cfg = self.config

        if cfg.seed is not None:
            torch.manual_seed(cfg.seed)

        glyphs = torch.tensor(atlas.glyph_matrix(self.entries), dtype=torch.float32)
        concepts = torch.tensor(atlas.concept_matrix(self.entries), dtype=torch.float32)
        paths = torch.tensor(atlas.concept_paths(self.entries), dtype=torch.long)
        target = torch.tensor(
            atlas.target_distance(self.entries, cfg.concept_weight),
            dtype=torch.float32)
        modes = torch.tensor([e.mode_id for e in self.entries], dtype=torch.long)

        self.register_buffer("glyphs", glyphs)
        self.register_buffer("concepts", concepts)
        self.register_buffer("paths", paths)
        self.register_buffer("target", target)
        self.register_buffer("modes", modes)

        self.encoder = EntryEncoder(glyphs.shape[1], concepts.shape[1],
                                    d=cfg.parent_dim, hidden=cfg.hidden)
        self.manifold = ContinuousManifold(d=cfg.parent_dim, D=cfg.ambient_dim)
        self.hypernet = Hypernetwork(d_entry=cfg.parent_dim, child_d=cfg.child_dim,
                                     child_hidden=cfg.child_hidden,
                                     child_D=cfg.ambient_dim)
        self.concept_embed = ConceptEmbedder(atlas.NUM_CONCEPTS, d=cfg.child_dim)

        self.instrument = InstrumentField(d=cfg.parent_dim) if cfg.use_instruments else None
        self.calibration = CalibrationField(d=cfg.parent_dim) if cfg.use_metrology else None
        self.unknown = UnknownField(d=cfg.parent_dim) if cfg.use_unknowns else None
        self.knowing = (KnowingField(d=cfg.parent_dim, num_modes=atlas.NUM_MODES)
                        if cfg.use_knowing else None)
        self.attunement = AttunementField(d=cfg.parent_dim) if cfg.use_attunement else None

    # -- forward pieces -----------------------------------------------------

    def coordinates(self) -> torch.Tensor:
        return self.encoder(self.glyphs, self.concepts)

    def energy(self, u: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, float]]:
        """The full energy functional. Returns (total, per-term readout)."""
        cfg = self.config
        w = cfg.weights
        terms: Dict[str, float] = {}

        if self.instrument is not None:
            stress = instrument_stress(u, self.target, self.instrument,
                                       self.attunement)
        else:
            off = ~torch.eye(u.shape[0], dtype=torch.bool, device=u.device)
            stress = ((torch.cdist(u, u) - self.target)[off] ** 2).mean()
        total = w["stress"] * stress
        terms["stress"] = float(stress.detach())

        curvature = metric_curvature(self.manifold, u, self.unknown)
        total = total + w["curvature"] * curvature
        terms["curvature"] = float(curvature.detach())

        if self.calibration is not None:
            cal = calibration_smoothness(self.calibration, u)
            total = total + w["calibration"] * cal
            terms["calibration"] = float(cal.detach())

        if self.unknown is not None:
            unk = unknown_mass(self.unknown, u)
            total = total + w["unknowns"] * unk
            terms["unknowns"] = float(unk.detach())

        if self.knowing is not None:
            align = mode_alignment(self.knowing, u, self.modes)
            total = total + w["knowing"] * align
            terms["knowing"] = float(align.detach())

        if self.attunement is not None and self.unknown is not None:
            coh = attunement_coherence(self.attunement, self.unknown, u)
            total = total + w["attunement"] * coh
            terms["attunement"] = float(coh.detach())

        child_curv = u.new_zeros(())
        cross = u.new_zeros(())
        children = self.hypernet(u)
        for i, child in enumerate(children):
            embedded, mask = self.concept_embed(self.paths[i].unsqueeze(0))
            points = embedded.squeeze(0)[mask.squeeze(0)]
            child_curv = child_curv + curve_curvature(child, points)
            cross = cross + cross_scale_mismatch(self.manifold, u[i], child, points)
        n = max(len(children), 1)
        total = total + w["child_curvature"] * child_curv / n
        total = total + w["cross_scale"] * cross / n
        terms["child_curvature"] = float((child_curv / n).detach())
        terms["cross_scale"] = float((cross / n).detach())

        return total, terms

    # -- training -----------------------------------------------------------

    def fit(self, verbose: bool = True, log_every: int = 500) -> BloomResult:
        cfg = self.config
        opt = torch.optim.Adam(self.parameters(), lr=cfg.lr)
        history: List[float] = []
        term_history: Dict[str, List[float]] = {}

        for epoch in range(cfg.epochs):
            opt.zero_grad()
            u = self.coordinates()
            loss, terms = self.energy(u)
            loss.backward()
            opt.step()

            history.append(float(loss.detach()))
            for key, value in terms.items():
                term_history.setdefault(key, []).append(value)

            if verbose and (epoch % log_every == 0 or epoch == cfg.epochs - 1):
                detail = "  ".join(f"{k}={v:.3f}" for k, v in terms.items())
                print(f"  epoch {epoch:5d}  loss {float(loss.detach()):8.4f}   {detail}")

        return self._result(history, term_history)

    def _result(self, history, term_history) -> BloomResult:
        with torch.no_grad():
            u = self.coordinates()
            n = u.shape[0]
            inst = (self.instrument(u) if self.instrument is not None
                    else torch.eye(2).expand(n, 2, 2))
            cal = (self.calibration(u) if self.calibration is not None
                   else torch.zeros(n))
            unk = (self.unknown(u) if self.unknown is not None
                   else torch.zeros(n))
            att = (self.attunement(u) if self.attunement is not None
                   else torch.zeros(n))

        return BloomResult(
            entry_ids=[e.entry_id for e in self.entries],
            names=[e.name for e in self.entries],
            positions=[tuple(float(v) for v in row) for row in u],
            instrument=[[[float(v) for v in row] for row in mat] for mat in inst],
            calibration=[float(v) for v in cal],
            unknowns=[float(v) for v in unk],
            attunement=[float(v) for v in att],
            modes=[e.mode for e in self.entries],
            loss_history=history,
            term_history=term_history,
            config=self.config,
        )


def bloom(config: Optional[BloomConfig] = None, verbose: bool = True) -> BloomResult:
    """Train a bloom over the default atlas and return plain data."""
    return MandalaBloom(config).fit(verbose=verbose)


if __name__ == "__main__":
    print("=" * 76)
    print("MANDALA BLOOM — two levels, seven bases")
    print("=" * 76)
    result = bloom(BloomConfig(epochs=1500))
    print()
    print(result.report())
