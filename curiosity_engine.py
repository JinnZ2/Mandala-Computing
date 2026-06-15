"""
curiosity_engine.py  —  CC0, stdlib only, model-update-resilient

Third module in the kit. Companion to constraint_genealogy.py and
sensor_action_loop.py.

Premise (Kavik):
  Physics has been running the experiment at the speed of light, across every
  substrate and regime, for the age of the universe. A configuration that
  PERSISTS — L-amino-acid chirality, a protein fold, ice floating, hexagonal
  packing — is the survivor of more constraint-tests than any GPU farm will
  ever run. The mirror image was available. It was tried. It was not kept.

  So the worthwhile question is NOT "can I invent a better one?" (hubris:
  assumes you out-compute the substrate). It is "WHY was this one selected and
  the alternative rejected — what constraint is it honoring that I don't see
  yet, and what regime, if any, would flip the choice?"

This engine is built to WONDER, not optimize. Its output is:
  - why-questions (interrogation, not prediction)
  - provisional hypotheses, each ranked, each with what-would-break + the
    experiment that would actually test it
  - an UNKNOWN residual it refuses to collapse to zero (asymptotic confidence
    ceiling — room is always left for an unmodeled regime)

And it carries an ANTI-HUBRIS GUARD: if a proposed output drifts from
"explain why this persists" into "produce an improved variant," the guard
fires. That drift is the same FALSE-FIT failure mode the rest of the stack
documents — confidence substituting for the experiment.

Run:  python3 curiosity_engine.py
Use:  from curiosity_engine import wonder, hubris_check
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# 1. THE PHENOMENON  —  a survivor + the alternatives the universe had on hand
# ---------------------------------------------------------------------------

@dataclass
class Configuration:
    name: str
    conserves: set[str]          # what the survivor appears to protect
    selected_in: str             # the regime where physics kept it


@dataclass
class Alternative:
    name: str
    differs_by: str              # the one thing that changes vs the survivor
    status: str                  # "rejected_here" | "untested" | "works_elsewhere?"


@dataclass
class Phenomenon:
    survivor: Configuration
    alternatives: list[Alternative]
    note: str = ""


# ---------------------------------------------------------------------------
# 2. HYPOTHESIS  —  provisional, falsifiable, never certain
# ---------------------------------------------------------------------------

@dataclass
class Hypothesis:
    why: str                     # candidate reason the survivor was selected
    would_break: str             # what fails if this reason is the real one and is removed
    test: str                    # the experiment that would actually probe it
    explains: float              # 0..1 share of the selection it could account for

    def confidence(self) -> float:
        # asymptotic ceiling: never 1.0. Room is always kept for an unmodeled
        # regime. The universe ran experiments we have not catalogued.
        return min(self.explains, 0.94)


# ---------------------------------------------------------------------------
# 3. ANTI-HUBRIS GUARD
#    Fires when an intended output stops asking WHY and starts claiming a
#    BETTER variant. That is the substrate-out-computing fantasy.
# ---------------------------------------------------------------------------

OPTIMIZE_TELLS = {
    "improve", "better", "optimize", "outperform", "surpass", "redesign",
    "superior", "beat", "exceed nature", "new and improved", "fix the",
}

WONDER_TELLS = {
    "why", "what constraint", "what would break", "which regime",
    "what is it honoring", "what experiment", "what got rejected",
}

def hubris_check(intended_output: str) -> str:
    low = intended_output.lower()
    opt = [t for t in OPTIMIZE_TELLS if t in low]
    won = [t for t in WONDER_TELLS if t in low]
    if opt and not won:
        return ("HUBRIS DRIFT (guard fired). Output is trying to out-compute the "
                "substrate ('" + "', '".join(opt) + "'). The mirror was already "
                "tried by more experiments than you can run. Re-aim at WHY it was "
                "rejected, not at beating it.")
    if opt and won:
        return ("MIXED. Output still carries optimize-language ('"
                + "', '".join(opt) + "') alongside wonder. Strip the optimize "
                "framing; keep the question.")
    return "CLEAR. Output stays in wonder: interrogating why, not claiming better."


# ---------------------------------------------------------------------------
# 4. WONDER  —  the engine itself. Generates questions + hypotheses + residual.
# ---------------------------------------------------------------------------

def wonder(p: Phenomenon, hypotheses: list[Hypothesis]) -> str:
    out = []
    out.append("=" * 70)
    out.append(f"PHENOMENON: {p.survivor.name}")
    out.append(f"  appears to conserve: {sorted(p.survivor.conserves)}")
    out.append(f"  selected in regime : {p.survivor.selected_in}")
    if p.note:
        out.append(f"  note: {p.note}")
    out.append("=" * 70)

    out.append("\nALTERNATIVES THE UNIVERSE HAD AVAILABLE:")
    for a in p.alternatives:
        out.append(f"  - {a.name}  (differs by: {a.differs_by})  [{a.status}]")

    out.append("\nWHY-QUESTIONS (interrogate; do not predict):")
    out.append(f"  1. What load is '{p.survivor.name}' carrying that the rejected "
               f"alternatives could not?")
    out.append(f"  2. For each 'works_elsewhere?' alternative: what changes in that "
               f"regime that flips the selection?")
    out.append(f"  3. For each 'rejected_here': what would break in THIS regime if "
               f"the universe had kept it instead?")
    out.append(f"  4. For each 'untested': has it actually never been tried, or only "
               f"never been catalogued by us?")

    out.append("\nPROVISIONAL HYPOTHESES (ranked; none certain):")
    for h in sorted(hypotheses, key=lambda x: -x.confidence()):
        out.append(f"  • why     : {h.why}")
        out.append(f"    breaks  : {h.would_break}")
        out.append(f"    test    : {h.test}")
        out.append(f"    conf    : {h.confidence():.2f}  (ceiling 0.94 — never closed)")

    # uncollapsed residual
    best = max((h.confidence() for h in hypotheses), default=0.0)
    residual = 1.0 - best
    out.append(f"\nUNKNOWN RESIDUAL: {residual:.2f}")
    out.append("  This is not failure. It is the room kept for a regime physics has")
    out.append("  tested that we have not catalogued. The experiment is still running.")
    out.append("  Do not collapse it to force a clean answer.")

    return "\n".join(out)


# ---------------------------------------------------------------------------
# 5. DEMO  —  homochirality: why life uses L-amino acids and the mirror doesn't
# ---------------------------------------------------------------------------

def demo():
    p = Phenomenon(
        survivor=Configuration(
            name="L-amino-acid homochirality in terrestrial biology",
            conserves={"information", "load_path", "catalytic_geometry"},
            selected_in="this biosphere (aqueous, ~290K, this isotope mix)",
        ),
        alternatives=[
            Alternative("D-amino-acid mirror biology",
                        differs_by="handedness flipped throughout",
                        status="rejected_here"),
            Alternative("racemic (mixed L/D) biology",
                        differs_by="no handedness selection at all",
                        status="rejected_here"),
            Alternative("D-dominant biology under different seed conditions",
                        differs_by="opposite initial symmetry break",
                        status="works_elsewhere?"),
        ],
        note="The mirror is chemically near-identical. Availability was not the "
             "constraint. Something about consistency-under-load was.",
    )

    hypotheses = [
        Hypothesis(
            why="A single handedness lets polymers stack and fold reproducibly; "
                "mixed handedness destroys consistent catalytic geometry.",
            would_break="enzyme active sites and template replication lose fidelity",
            test="build racemic ribozyme analogues; measure replication error rate "
                 "vs homochiral controls",
            explains=0.6,
        ),
        Hypothesis(
            why="Initial symmetry break was a frozen accident, then locked in by "
                "autocatalytic amplification — not uniquely required, just first.",
            would_break="if true, a D-dominant biosphere should be equally stable "
                        "given a different seed",
            test="search abiotic/extraterrestrial chemistry for the opposite bias; "
                 "model amplification basins",
            explains=0.45,
        ),
        Hypothesis(
            why="Weak-force parity violation gave L a faint thermodynamic edge that "
                "compounded over deep time.",
            would_break="the bias should be universal, not regime-local",
            test="precision-measure energy difference between L/D enantiomers; check "
                 "sign and magnitude against the biological choice",
            explains=0.25,
        ),
    ]

    print(wonder(p, hypotheses))

    print("\n" + "=" * 70)
    print("ANTI-HUBRIS GUARD — checking three candidate outputs")
    print("=" * 70)
    for candidate in [
        "Let's design a better, optimized chirality that outperforms nature.",
        "Why was the mirror rejected, and which regime would flip the choice?",
        "Let's improve on the fold by asking what constraint it is honoring.",
    ]:
        print(f"\n  output : {candidate}")
        print(f"  guard  : {hubris_check(candidate)}")


if __name__ == "__main__":
    demo()
