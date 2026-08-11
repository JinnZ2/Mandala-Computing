"""
bases.py — the seven bases of measurement, as differentiable fields.

    1. Measurement      Riemannian metric        g_ij(u) = J^T J
    2. Instruments      sensitivity tensor       I_ij(u), symmetric positive-definite
    3. Metrology        calibration              mu(u) scalar, smoothness-penalised
    4. Ways of knowing   traversal modes          V^a_i(u), one vector field per mode
    5. Unknowns         blind spots              kappa(u) >= 0, amplifies curvature
    6. Physics          the energy functional    the sum of the terms below
    7. Attunement       observer participation   omega(u) in [0,1]

The first is what the manifold already has: a metric pulled back from the
embedding. The rest modulate it. The claim being encoded is that a distance
is never bare — it is always measured *by something*, *calibrated against
something*, *traversed in some way*, with *gaps*, by *someone who may be
inside the system*.

Requires PyTorch. `mandala_bloom.concept_atlas` deliberately does not, so the
semantics stay reachable without a training backend.
"""

from __future__ import annotations

from typing import Optional

import torch
import torch.nn as nn
from torch.func import jacrev, vmap


__all__ = [
    "InstrumentField", "CalibrationField", "UnknownField",
    "KnowingField", "AttunementField",
    "instrument_stress", "calibration_smoothness", "unknown_mass",
    "mode_alignment", "attunement_coherence", "metric_curvature",
    "pullback_metric",
]


def _mlp(d_in: int, hidden: int, d_out: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(d_in, hidden), nn.Tanh(),
        nn.Linear(hidden, d_out),
    )


# ---------------------------------------------------------------------------
# Base 2 — Instruments
# ---------------------------------------------------------------------------

class InstrumentField(nn.Module):
    """Anisotropic sensitivity I_ij(u): what the measurement can feel.

    Emitted as a Cholesky factor L, so `I = L L^T + eps*Id` is symmetric
    positive-definite by construction — a sensitivity that could invert the
    sign of a distance would not be an instrument.

    An instrument with a large determinant resolves finely in every direction;
    an elongated one is sharp along one axis and blind across it.
    """

    def __init__(self, d: int = 2, hidden: int = 12, floor: float = 0.1):
        super().__init__()
        if d != 2:
            raise NotImplementedError("InstrumentField currently assumes d=2")
        self.d = d
        self.floor = floor
        self.net = _mlp(d, hidden, 3)   # lower-triangular entries of L

    def forward(self, u: torch.Tensor) -> torch.Tensor:
        raw = self.net(u)
        batch = u.shape[0]
        L = u.new_zeros(batch, 2, 2)
        # index_put via stacking keeps the graph intact (no in-place on a leaf)
        L = torch.stack([
            torch.stack([raw[:, 0], torch.zeros_like(raw[:, 0])], dim=-1),
            torch.stack([raw[:, 1], raw[:, 2]], dim=-1),
        ], dim=-2)
        eye = torch.eye(2, dtype=u.dtype, device=u.device).unsqueeze(0)
        return L @ L.transpose(1, 2) + self.floor * eye


# ---------------------------------------------------------------------------
# Base 3 — Metrology
# ---------------------------------------------------------------------------

class CalibrationField(nn.Module):
    """Scalar calibration mu(u): the local standard a measurement is read against.

    Only differences in mu matter, so the field is free up to a constant. What
    is penalised is its *gradient*: a calibration that lurches from place to
    place means two neighbouring measurements are not comparable.
    """

    def __init__(self, d: int = 2, hidden: int = 12):
        super().__init__()
        self.net = _mlp(d, hidden, 1)

    def forward(self, u: torch.Tensor) -> torch.Tensor:
        return self.net(u).squeeze(-1)


# ---------------------------------------------------------------------------
# Base 5 — Unknowns
# ---------------------------------------------------------------------------

class UnknownField(nn.Module):
    """Non-negative unknown density kappa(u) >= 0: where the map runs out.

    Softplus keeps it non-negative — an unknown cannot be a *negative* amount
    of ignorance. It is regularised toward zero but never forced there: the
    point of carrying it is that some regions honestly are less known, and
    flattening that to zero would be a lie the geometry then has to absorb.
    """

    def __init__(self, d: int = 2, hidden: int = 12):
        super().__init__()
        self.net = _mlp(d, hidden, 1)

    def forward(self, u: torch.Tensor) -> torch.Tensor:
        return nn.functional.softplus(self.net(u)).squeeze(-1)


# ---------------------------------------------------------------------------
# Base 4 — Ways of knowing
# ---------------------------------------------------------------------------

class KnowingField(nn.Module):
    """K vector fields V^a(u): preferred directions of traversal per mode.

    Logic, analogy and intuition do not move through concept space the same
    way. Each mode gets its own field; an entry known by one mode should find
    its neighbours lying along that mode's direction.
    """

    def __init__(self, d: int = 2, num_modes: int = 3, hidden: int = 12):
        super().__init__()
        self.d = d
        self.num_modes = num_modes
        self.net = _mlp(d, hidden, d * num_modes)

    def forward(self, u: torch.Tensor) -> torch.Tensor:
        return self.net(u).reshape(u.shape[0], self.num_modes, self.d)


# ---------------------------------------------------------------------------
# Base 7 — Attunement
# ---------------------------------------------------------------------------

class AttunementField(nn.Module):
    """Observer participation omega(u) in [0,1]: am I inside what I measure?

    At omega = 0 the instrument is applied as-is — the detached stance, where
    the observer's presence is assumed not to matter. As omega rises the
    instrument is softened toward the identity: the more you are part of the
    system, the less your apparatus imposes its own shape on what you find.
    """

    def __init__(self, d: int = 2, hidden: int = 12):
        super().__init__()
        self.net = _mlp(d, hidden, 1)

    def forward(self, u: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(self.net(u)).squeeze(-1)


# ---------------------------------------------------------------------------
# Base 1 — Measurement: the pullback metric
# ---------------------------------------------------------------------------

def pullback_metric(manifold, u: torch.Tensor) -> torch.Tensor:
    """g(u) = J^T J for an embedding `manifold: R^d -> R^D`.

    Accepts `u` of shape (d,) for a single point or (N, d) for a batch, and
    returns (d, d) or (N, d, d). The pasted code called
    `jacrev(f)(u.unsqueeze(0)).squeeze(0)`, which yields a rank-4 tensor whose
    `.T` is meaningless; routing single points through un-batched `jacrev` and
    batches through `vmap` keeps the ranks honest.
    """
    if u.dim() == 1:
        J = jacrev(manifold)(u)             # (D, d)
        return J.transpose(-2, -1) @ J
    J = vmap(jacrev(manifold))(u)           # (N, D, d)
    return torch.einsum('nij,nik->njk', J, J)


# ---------------------------------------------------------------------------
# Base 6 — Physics: the energy terms
# ---------------------------------------------------------------------------

def instrument_stress(u: torch.Tensor, target_distance: torch.Tensor,
                      instrument: InstrumentField,
                      attunement: Optional[AttunementField] = None,
                      softening: float = 0.5) -> torch.Tensor:
    """Stress majorisation under an instrument-modulated, attunement-softened
    metric.

    Plain stress asks that Euclidean distance match the target. This asks that
    the distance *as the instrument measures it* match — so where the
    instrument is anisotropic, the layout may stretch without penalty along
    the blind axis.
    """
    inst = instrument(u)                                   # (N, 2, 2)
    if attunement is not None:
        omega = attunement(u).unsqueeze(-1).unsqueeze(-1)   # (N, 1, 1)
        eye = torch.eye(inst.shape[-1], dtype=u.dtype, device=u.device)
        # Interpolate toward the identity rather than scaling toward zero:
        # a fully attuned observer still measures, just without imposing.
        inst = (1.0 - softening * omega) * inst + softening * omega * eye

    pair = 0.5 * (inst.unsqueeze(1) + inst.unsqueeze(0))    # (N, N, 2, 2)
    diff = u.unsqueeze(1) - u.unsqueeze(0)                  # (N, N, 2)
    quad = torch.einsum('...i,...ij,...j->...', diff, pair, diff)
    dist = torch.sqrt(quad.clamp(min=1e-12))

    off_diagonal = ~torch.eye(u.shape[0], dtype=torch.bool, device=u.device)
    return ((dist - target_distance)[off_diagonal] ** 2).mean()


def calibration_smoothness(calibration: CalibrationField,
                           u: torch.Tensor) -> torch.Tensor:
    """|grad mu|^2 — how fast the measurement standard drifts.

    Computed with `torch.func.jacrev` rather than `u.requires_grad_(True)` +
    `autograd.grad`. In the training loop `u` is a non-leaf tensor produced by
    the encoder; calling `requires_grad_` on it is a silent no-op that leaves
    the term differentiating the wrong thing.
    """
    grad = vmap(jacrev(lambda p: calibration(p.unsqueeze(0)).squeeze(0)))(u)
    return (grad ** 2).sum(-1).mean()


def unknown_mass(unknown: UnknownField, u: torch.Tensor) -> torch.Tensor:
    """Total unknown density. Regularised down, never to zero."""
    return unknown(u).mean()


def mode_alignment(knowing: KnowingField, u: torch.Tensor,
                   mode_labels: torch.Tensor) -> torch.Tensor:
    """1 - cos(V_mode(u), direction to nearest neighbour).

    The nearest-neighbour search is done on a detached copy: masking the
    diagonal with `inf` on a tensor that carries gradient (as the original did
    via `fill_diagonal_`) propagates NaN through the backward pass.
    """
    vectors = knowing(u)
    modes = vectors[torch.arange(u.shape[0], device=u.device), mode_labels]

    with torch.no_grad():
        dist = torch.cdist(u, u)
        dist = dist + torch.eye(u.shape[0], device=u.device) * 1e9
        nearest = dist.argmin(dim=1)

    heading = u[nearest] - u
    cos = nn.functional.cosine_similarity(modes, heading, dim=1, eps=1e-8)
    return (1.0 - cos).mean()


def attunement_coherence(attunement: AttunementField, unknown: UnknownField,
                         u: torch.Tensor) -> torch.Tensor:
    """Tie omega to normalised unknown density.

    The coupling says: where the map runs out is exactly where you cannot
    pretend to stand outside it. Detached on the unknown side so this term
    shapes attunement to follow the unknowns, and does not let attunement
    quietly flatten the unknowns to make itself easier to satisfy.
    """
    omega = attunement(u)
    with torch.no_grad():
        kappa = unknown(u)
        kappa = kappa / (kappa.max() + 1e-6)
    return ((omega - kappa) ** 2).mean()


def metric_curvature(manifold, u: torch.Tensor,
                     unknown: Optional[UnknownField] = None,
                     unknown_coupling: float = 0.1) -> torch.Tensor:
    """Deviation of the embedding from local isometry, amplified by unknowns.

    Singular values of J at 1 mean the map neither stretches nor compresses.
    Where kappa is high the space is permitted — required, even — to bend more.
    """
    J = vmap(jacrev(manifold))(u)
    singular = torch.linalg.svdvals(J)
    curvature = ((singular - 1.0) ** 2).mean()
    if unknown is not None:
        curvature = curvature + unknown_coupling * unknown(u).mean()
    return curvature
