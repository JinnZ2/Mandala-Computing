# mandala_bloom — the seven bases of measurement

## What This Is

`mandala_stack/` made the **shape** an input. This folder makes the
**measurement** an input.

A distance in here is never bare. It is taken by an instrument with its own
sensitivity, read against a calibration standard, traversed in a particular way
of knowing, through a space with acknowledged blind spots, by an observer who
may be standing inside the thing being measured.

| # | Basis | Role | Object |
|---|-------|------|--------|
| 1 | Measurement | distance, difference, resolution | Riemannian metric `g_ij(u) = JᵀJ` |
| 2 | Instruments | sensitivity and bias — what the metric can *feel* | symmetric PD tensor field `I_ij(u)` |
| 3 | Metrology | calibration — alignment to a shared standard | scalar `μ(u)`, penalised for drifting |
| 4 | Ways of knowing | modes of traversal (logic, analogy, intuition) | one vector field `Vᵅ(u)` per mode |
| 5 | Unknowns | gaps, blind spots, edges of the map | `κ(u) ≥ 0`, amplifies allowed curvature |
| 6 | Physics | the governing law of change | the energy functional over all of these |
| 7 | Attunement | observer participation — am I inside this? | `ω(u) ∈ [0,1]`, softens the instrument |

Base 7 is the one that changes the others. At `ω = 0` the instrument applies
as-is: the detached stance, where the observer is assumed not to matter. As
`ω` rises the instrument is interpolated toward the identity — the more you are
part of the system, the less your apparatus imposes its own shape on what you
find. It is coupled to base 5, because where the map runs out is exactly where
you cannot pretend to stand outside it.

## Two Levels

```
level 0 (parent)   each Atlas entry is a point u_i, laid out so that
                   instrument-measured distance matches concept/glyph
                   dissimilarity
                            │
                   hypernetwork: u_i → the weights of a child manifold
                            │
level 1 (child)    the entry's concept path (🪨 → 🛡️ → 🧭 → 🕸️ → ∞ → 📡 → ⚖️)
                   is a *curve* on that child manifold
```

The two levels are tied by a cross-scale term: the metric the parent sees at
`u_i` should match the average metric along that entry's child curve. That
coupling is why this is a **bloom** and not two independent fits — where an
entry sits in the large space and what shape its own small space has are one
object, learned together.

## Files

| File | Purpose | Needs torch |
|------|---------|-------------|
| `concept_atlas.py` | emoji concept map, Atlas entries, similarity | no |
| `bloom_bridge.py` | connection layer to `mandala_stack/` and the root | no |
| `bases.py` | the seven bases as differentiable fields | yes |
| `bloom.py` | the two-level model and trainer | yes |
| `_paths.py` | `sys.path` bootstrap across the three directories | no |

## Torch Is Optional

The repo core stays numpy + scipy. PyTorch buys you the differentiable bases
and the two-level coupling — nothing else.

Without it: `concept_atlas` works, `bloom_bridge.learn_atlas_geometry()`
embeds the Atlas with the stack's *own* learner, and a `BloomResult` trained on
another machine still loads and still solves, because it is plain floats — no
tensors survive into the result object. Asking for `mandala_bloom.bloom`
without a backend raises an ImportError that names the fix.

This is the repo's own invariant applied to a dependency: breathing degrades,
never fails.

```bash
pip install -r requirements-bloom.txt   # only if you want to train
```

## How This Folder Connects

All three directories share one flat namespace (`_paths.bootstrap()` puts the
repo root, `mandala_stack/` and this folder on `sys.path`):

```python
import mandala_bloom
from mandala_bloom import learn_atlas_geometry   # this folder, no torch
from mandala_solver import MandalaSolver         # mandala_stack/
from octahedral_arithmetic import PHI            # repo root
```

| direction | what it does |
|---|---|
| atlas → stack `Geometry` | `learn_atlas_geometry()` hands the concept/glyph dissimilarity to `mandala_stack.GeometryLearner`. No torch, and it doubles as the control |
| bloom → stack `Geometry` | `geometry_from_bloom()` wraps a `BloomResult` as a `Geometry` whose `transition_cost` uses the **learned instrument tensor**, not Euclidean distance |
| atlas → solver | `solve_on_atlas()` — the same `MandalaSolver` that anneals octahedra anneals the concept atlas, unchanged on both sides |
| concept path → root arithmetic | `path_to_glyphs()`, `path_to_number()` project a concept story onto the octahedral glyph alphabet and into exact base-8 arithmetic |

`BloomGeometry` is the one thing here that `LearnedGeometry` cannot do:
`LearnedGeometry._distance` is Euclidean in the embedding, so its metric is
isotropic everywhere. `BloomGeometry` measures with

```
d(a,b)² = (u_a − u_b)ᵀ · ½(I_a + I_b) · (u_a − u_b)
```

which is base 2 — sensitivity that varies from point to point.

```bash
python mandala_bloom/concept_atlas.py    # the atlas and its similarity matrix
python mandala_bloom/bloom_bridge.py     # all four connections, self-test
python mandala_bloom/bloom.py            # train a bloom, print the chart
```

## Measured Result — and What It Is Not

Does the learned position-dependent metric actually buy anything? The
falsifiable version: correlate each embedding's pairwise distances against the
concept/glyph dissimilarity all of them are fitting. Higher `r` means the
layout genuinely realises meaning as geometry.

Eight seeds, 800 epochs each (`compare_embeddings()`):

| method | mean r | sd | min | max |
|---|---|---|---|---|
| **bloom, with instrument** | **+0.745** | 0.230 | +0.367 | +0.945 |
| bloom, instrument ablated | +0.496 | 0.355 | −0.171 | +0.977 |
| `mandala_stack` learner (control) | +0.161 | 0.411 | −0.669 | +0.685 |

The bloom wins on the mean and — more interesting — is the **most stable** of
the three (sd 0.230 against 0.355 and 0.411). Ablating just the instrument
tensor while keeping the same learned positions costs about 0.25 of
correlation, which is the closest thing here to isolating base 2.

**Now the part that matters more than the table.** This is 4 entries. Four.
That is 12 off-diagonal pairs, fitted by a model with thousands of parameters.
The ranges overlap heavily — on seeds 2 and 5 the ablated bloom *beat* the full
one. A mean separation of 0.25 across 8 seeds at that sample size is a
direction, not a result, and anyone quoting the +0.745 without the sd and the
n=4 is misreporting it.

What would make it a result: more entries. The architecture takes any number;
the Atlas currently has four. Until then the honest claim is *"the instrument
tensor appears to help and appears to stabilise, on a sample far too small to
carry the conclusion."*

This is the same posture as `mandala_stack/README.md`, which records that the
root repo's `sin²` metric does not imply the octahedron it asserts. Recording
what the measurement actually says, including when it is too weak to say much,
is the point of having the bases at all.

## Six Defects Found in the Original Scripts

The three pasted iterations were verified by execution, not by reading. Five
crash; one does not.

| # | Where | Effect |
|---|-------|--------|
| 1 | v1 calls `curvature_loss_manifold` | never defined → `NameError` at epoch 0 |
| 2 | v2 `ConceptField(d=2, num_concepts, hidden=12)` | positional after keyword → file will not parse |
| 3 | v2 `concept_to_idx["🔄"] if "↻" in concept_to_idx` | guard tests `↻`, indexes `🔄` → `KeyError` |
| 4 | all three, hypernetwork weights | `nn.Linear` stores `(out, in)`; unpacked as `(in, out)` → shape crash |
| 5 | all three, `cross_scale_metric_loss` | `jacrev(f)(u.unsqueeze(0)).squeeze(0)` is rank 3; `.T` on it is invalid → crash |
| 6 | **all three, `child.weight.data = W`** | **silent: the hypernetwork receives exactly zero gradient** |

**#6 is the one that mattered.** Assigning to `.data` detaches from the
autograd graph. The model still runs, still trains, still prints a falling
loss — and the parent → child generation learns nothing, which makes the
cross-scale coupling, the entire reason the thing is two-level, inert.
Measured on the original: all 4 hypernetwork parameters came back `grad=None`,
total `|grad| = 0`. After the fix: `|grad| = 1.46e5`, and the encoder feels the
child level too, so the coupling runs both ways.

`_ChildManifold` applies hypernetwork-produced tensors through
`torch.func.functional_call` against a parameterless template, so the child
stays a real function of `u_i` and `jacrev`/`vmap` still differentiate through
it. `tests/test_core.py::test_bloom_hypernetwork_receives_gradient` asserts
non-zero gradient, so this cannot silently come back.

Three smaller things fixed along the way, none of which crash:

- `calibration_smoothness_loss` called `u.requires_grad_(True)` on `u`, which
  is a **non-leaf** tensor in the training loop. That is a silent no-op, so the
  term was differentiating the wrong thing. Now uses `torch.func.jacrev`.
- `mode_alignment_loss` masked the `cdist` diagonal with `inf` on a tensor
  carrying gradient, which propagates `NaN` backward. The neighbour search is
  now done under `no_grad`.
- The mode labels disagreed with themselves: the comment said `1 = analogy,
  2 = intuition`, the printout said index 1 was `"Intuition"`. Both now read
  from `concept_atlas.KNOWING_MODES`.

## Known Limits

- **n = 4.** Everything above. The single most valuable contribution to this
  folder is more Atlas entries, not more architecture.
- The concept paths are hand-assigned. Which emoji tell an entry's story, and
  in what order, is a human judgement not derived from the glyph string — so
  the concept half of the similarity carries an unmeasured prior. This is the
  same "projector subjectivity" risk `CLAUDE.md` logs for `mandala_runtime`.
- `path_to_glyphs` / `path_to_number` project 22 concepts onto 8 octahedral
  states with `mod 8`. Lossy and not invertible — display and arithmetic only,
  never an encoding to read back.
- `InstrumentField` assumes `d = 2`. The Cholesky packing is hardcoded for a
  2×2; other dimensions raise rather than silently mis-shape.
- Attunement is coupled to unknowns *by construction* (`attunement_coherence`),
  so the two are not independent evidence of each other. If ω tracking κ is
  presented as a finding, it is circular — the loss put it there.

## Next

1. **More entries.** Everything else is downstream of n = 4.
2. **Derive concept paths from the glyph strings** rather than assigning them,
   which would remove the unmeasured prior and make the concept similarity
   falsifiable against the glyph similarity instead of blended with it.
3. **Instrument fields on the root octahedron.** `mandala_stack.stack_bridge`
   found that the root's `sin²` coupling metric does not imply an octahedron.
   A learned `I_ij` over the 8 states is one way to ask whether some
   *instrument* on that metric does.
4. **Christoffel terms in `curve_curvature`.** The current second derivative is
   coordinate, not covariant — fine for near-isometric children, wrong as the
   child geometry gets more curved.
