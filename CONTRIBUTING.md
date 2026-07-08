# Contributing to Mandala Computing

Thanks for considering a contribution. This is a research repo with a solo/small
maintainer team — these guidelines exist to keep contributions easy to review, not
to gatekeep.

## Before you start

- Read `README.md` for what this project does and does not claim.
- Read `CLAUDE.md` for the full architecture: module list, dependency layers, coding
  conventions, and known risks/decision trees for common change types.
- If you're picking up one of the `experiments/` playgrounds, read
  `experiments/README.md` first — it documents the intended (already-wired)
  relationship between each playground and the core engine, so you don't
  accidentally reintroduce a standalone reimplementation of something the engine
  already does.

## Running the tests

```bash
pip install numpy scipy
python tests/test_core.py
```

All 336 tests should pass before and after your change. The test functions in
`tests/test_core.py` are written in plain `assert`-based, pytest-compatible style
(`def test_something(): assert ...`) even though the file is currently invoked with
a custom runner — if you have `pytest` installed, `pytest tests/test_core.py` should
also work and gives you `-k` filtering for running a single test while you iterate.

If you add a new module, add tests for it to `tests/test_core.py` following the
existing per-module import + `test_*` naming pattern used throughout that file.

## Coding conventions

(Full table in `CLAUDE.md`'s "coding-conventions" section — summary here.)

| element | style |
|---|---|
| classes | `PascalCase` |
| functions | `snake_case` |
| constants | `UPPER_SNAKE_CASE` |
| type hints | used extensively on function signatures |
| docstrings | description + Args + Returns, standard Python format |

- Prefer editing existing modules over creating new ones for closely-related
  functionality — see `CLAUDE.md`'s decision tree for "is this a new substrate /
  new domain / new coupling rule" before adding a new top-level file.
- This is research code — exploratory patterns, "sketch" implementations, and
  documented approximations are acceptable, as long as they're labeled as such
  (see "Labeling speculative content" below).
- `PHI` is canonically defined in `octahedral_arithmetic.py`; other modules that
  need it standalone (e.g. `quantum_mandala.py`, `geis.py`) redefine it locally
  for zero-dependency operation rather than importing across dependency layers —
  keep this pattern rather than introducing a new redundant definition.
- Octahedral state glyphs (`⊕⊖⊗⊘⊙⊚⊛⊜`) are canonical and shared via
  `glyphs/mandala.json` / `atlas/glyphs/mandala.json` and
  `octahedral_arithmetic.GLYPHS`. Import them; don't redefine a new glyph set for
  the same 8 states elsewhere.

## Where does a new file go?

- **Core engine capability** (a new solver, a new problem encoding, a new
  substrate): goes at repo root next to `mandala_computer.py` /
  `quantum_mandala.py` / `holographic_mandala.py`, following whichever of those
  three is the closest architectural match.
- **Exploratory / UI-facing playground** that routes through the core engine
  rather than reimplementing it: goes in `experiments/`, with an entry added to
  `experiments/README.md`'s inventory table.
- **Self-description / epistemology module** (CC0-licensed, describes the repo
  to an AI reader — in the spirit of `claim_schema.py`,
  `mandala_computing_module.py`, `mandala_scale_invariance_breakdown.py`,
  `curiosity_engine.py`): follows the existing pattern of a generic base module
  (if one exists, e.g. `scale_invariance_breakdown.py`) plus a
  `mandala_`-prefixed per-repo instantiation that imports from it rather than
  redefining shared dataclasses.
- If a new module is intended to be an instantiation of a generic
  cross-repo pattern, and the generic version doesn't exist yet in this repo,
  either add it (see `scale_invariance_breakdown.py` for the pattern) or tag the
  reference explicitly as `(external: RepoName)`, matching the convention in
  `P=np-hypothesis.md`. Don't leave an unqualified reference to a file that
  doesn't exist anywhere in this repo.

## Adding a claim to `claim_schema.py`

If your change introduces a new falsifiable claim about the framework (a new
solver's convergence property, a new energy-model invariant, etc.), consider
adding a `Claim` entry to `claim_schema.py`'s `MANDALA_CLAIMS` list — with
explicit `bounds` (scope), `cond` (preconditions), `fail` (falsifying
conditions), and `meas` (what would be measured to check it). Regenerate
`mandala.claims` / `mandala.claims.bin` / `CLAIM_TABLE.json` from the updated
list (see `claim_schema.py`'s `write_claims_file` / `write_claims_binary`) so
they stay in sync with `MANDALA_CLAIMS` — these files should never be hand-edited
directly.

## Labeling speculative content

Some `.md` files in this repo (`Checklist.md`, `Questions.md`, and others)
contain Python code blocks that are illustrative sketches, not shipped code.
When adding this kind of content, mark it explicitly — e.g. a leading
`# SKETCH — not implemented in this repo` comment inside the code fence, or
prose immediately before the fence stating it's conceptual — so a reader
(human or AI) can't mistake it for a real, importable module. See
`Checklist.md` for the convention now in use.

## Pull requests

- Keep the diff focused — this repo's own audit history shows scope creep
  (accidentally duplicating an entire file inside another one, leaving stale
  numbers in five places) causes real, if not necessarily commonly occurring, cleanup debt later.
- Run the test suite and mention the result in your PR description.
- If your change affects a number cited in multiple docs (module count, test
  count, completion percentage), search for all occurrences
  (`grep -rn` across `*.md` and `*.py`) rather than updating just the file you
  were looking at — see `REVIEW.md` for a worked example of how far these can
  drift when that isn't done.

## License

Code is MIT (see `LICENSE`). Several self-description/epistemology modules
(`claim_schema.py`, `mandala_computing_module.py`,
`mandala_scale_invariance_breakdown.py`, `scale_invariance_breakdown.py`) are
additionally marked CC0 in their own docstrings — keep that dual marking if you
edit them, and use CC0 for new modules in that same family.
