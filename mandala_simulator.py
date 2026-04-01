"""
MANDALA SIMULATOR v2.0
Lightweight entry point — stdlib-only interface to the full computation stack.

This module provides a simple API for quick experiments without requiring
numpy/scipy. It delegates to the real engines when available, and falls
back to octahedral arithmetic (stdlib only) when they're not.

Note: This is NOT the same class as mandala_computer.MandalaComputer.
      This is a lightweight wrapper for quick demos and exploration.

Usage:
    from mandala_simulator import MandalaSimulator
    sim = MandalaSimulator()
    sim.factor(143)
    sim.validate_claim("This is fundamentally the best approach.")
"""

import math
import time

PHI = (1 + math.sqrt(5)) / 2


class MandalaSimulator:
    """
    Lightweight mandala computation interface.

    Delegates to real engines when available:
      - octahedral_arithmetic (always available, stdlib only)
      - mandala_computer (requires numpy)
      - quantum_mandala (requires numpy + scipy)
      - claim_validator (always available, stdlib only)

    Falls back gracefully when dependencies are missing.
    """

    def __init__(self, golden_depth: int = 5, sacred_geometry: int = 8):
        self.golden_depth = golden_depth
        self.sacred_geometry = sacred_geometry

        # Check what's available
        self._has_arithmetic = False
        self._has_engine = False
        self._has_quantum = False
        self._has_validator = False

        try:
            from octahedral_arithmetic import OctahedralNumber, GlyphFraction, factor_pair_glyphs
            self._has_arithmetic = True
            self._OctahedralNumber = OctahedralNumber
            self._factor_pair_glyphs = factor_pair_glyphs
        except ImportError:
            pass

        try:
            from mandala_computer import MandalaComputer
            self._has_engine = True
            self._MandalaComputer = MandalaComputer
        except ImportError:
            pass

        try:
            from quantum_mandala import QuantumMandalaComputer
            self._has_quantum = True
            self._QuantumMandalaComputer = QuantumMandalaComputer
        except ImportError:
            pass

        try:
            from claim_validator import validate_claim, print_report
            self._has_validator = True
            self._validate_claim = validate_claim
            self._print_report = print_report
        except ImportError:
            pass

        engines = []
        if self._has_arithmetic:
            engines.append("glyph-arithmetic")
        if self._has_engine:
            engines.append("classical")
        if self._has_quantum:
            engines.append("quantum")
        if self._has_validator:
            engines.append("validator")
        print(f"MandalaSimulator: {', '.join(engines) or 'stdlib-only'}")

    def factor(self, N: int, method: str = "auto") -> dict:
        """
        Factor N using the best available method.

        Methods: 'glyph' (exact, stdlib), 'annealing' (classical),
                 'quantum', 'auto' (tries in order of preference).
        """
        print(f"\n  Factoring N={N}...")
        result = {"N": N, "method": None}

        # Always do exact glyph factorization if available
        if self._has_arithmetic:
            oct_N = self._OctahedralNumber.from_decimal(N)
            result["glyph"] = oct_N.to_glyphs()
            result["prime"] = oct_N.is_prime()

            if oct_N.is_prime():
                print(f"  {oct_N.to_glyphs()} is PRIME (irreducible)")
                result["method"] = "glyph"
                result["factors"] = [N]
                return result

            pair = self._factor_pair_glyphs(N)
            if pair:
                fa, fb = pair
                result["factors_glyph"] = (fa.to_glyphs(), fb.to_glyphs())
                result["factors"] = (fa.to_decimal(), fb.to_decimal())
                result["method"] = "glyph"
                print(f"  Glyph: {fa.to_glyphs()} * {fb.to_glyphs()} = {oct_N.to_glyphs()}"
                      f"  (decimal: {fa.to_decimal()} * {fb.to_decimal()} = {N})")

        # If requested or auto, try engine methods
        if method in ("annealing", "auto") and self._has_engine:
            mc = self._MandalaComputer(golden_depth=self.golden_depth, sacred_geometry=self.sacred_geometry)
            mc.encode_factorization(N)
            r = mc.simulated_annealing(max_steps=8000, T_start=5.0, T_end=0.001)
            sol = r["solution"]
            result["engine_pair"] = sol.get("best_pair")
            result["engine_verified"] = sol.get("verified", False)
            result["engine_residual"] = sol.get("residual")
            if sol.get("verified"):
                result["method"] = result.get("method", "annealing")
                print(f"  Engine: {sol['best_pair']} verified={sol['verified']}")

        if method == "quantum" and self._has_quantum:
            qc = self._QuantumMandalaComputer(golden_depth=2, sacred_geometry=self.sacred_geometry)
            r = qc.quantum_annealing("factorization", {"N": N}, num_steps=100)
            result["quantum"] = r["solution"]

        if not result.get("method"):
            # Stdlib fallback: trial division
            result["method"] = "trial_division"
            d = 2
            n = N
            factors = []
            while d * d <= n:
                while n % d == 0:
                    factors.append(d)
                    n //= d
                d += 1
            if n > 1:
                factors.append(n)
            result["factors"] = factors
            print(f"  Trial division: {' * '.join(str(f) for f in factors)} = {N}")

        return result

    def validate_claim(self, text: str) -> dict:
        """Validate a natural language claim epistemologically."""
        if not self._has_validator:
            print("  Claim validator not available")
            return {"error": "claim_validator not importable"}

        report = self._validate_claim(text)
        self._print_report(report)
        return {
            "concern": report.overall_concern,
            "interpretation": report.interpretation,
            "tiers": {d.name: d.score for d in report.domain_scores},
        }

    def glyph(self, n: int) -> str:
        """Convert a number to its glyph representation."""
        if self._has_arithmetic:
            return self._OctahedralNumber.from_decimal(n).to_glyphs()
        # Stdlib fallback: manual base-8
        if n == 0:
            return "\u2295"
        glyphs = ["\u2295", "\u2296", "\u2297", "\u2298",
                  "\u2299", "\u229a", "\u229b", "\u229c"]
        result = []
        while n > 0:
            result.append(glyphs[n % 8])
            n //= 8
        return "".join(result)

    def status(self) -> dict:
        """Report available capabilities."""
        return {
            "arithmetic": self._has_arithmetic,
            "classical_engine": self._has_engine,
            "quantum_engine": self._has_quantum,
            "claim_validator": self._has_validator,
            "golden_depth": self.golden_depth,
            "sacred_geometry": self.sacred_geometry,
        }


# ============================================================================
# Quick-access functions (backward compatible with old test_ names)
# ============================================================================

def test_p_equals_np():
    """Quick P=NP demo via factorization."""
    sim = MandalaSimulator()
    print("\n  P=NP geometric approach: factor N via energy minimization")
    for N in [15, 77, 143]:
        sim.factor(N)


def test_unified_field():
    """Quick demo showing all available engines."""
    sim = MandalaSimulator()
    print("\n  Available engines:", sim.status())


def test_consciousness():
    """Quick claim validation demo."""
    sim = MandalaSimulator()
    sim.validate_claim(
        "Recursive mandala structures naturally exhibit consciousness "
        "signatures when integrated information exceeds threshold."
    )


def demo_full():
    """Run all simulator demos."""
    sim = MandalaSimulator()

    print("=" * 60)
    print("MANDALA SIMULATOR v2.0")
    print("=" * 60)

    # Factorization
    for N in [15, 35, 143, 221]:
        sim.factor(N)

    # Glyph representation
    print("\n  Glyph representations:")
    for n in [7, 11, 13, 42, 143]:
        print(f"    {n} = {sim.glyph(n)}")

    # Claim validation
    print()
    sim.validate_claim("This increases efficiency by 300% as measured over 5 years.")
    print()
    sim.validate_claim("This fundamentally transforms everything permanently.")


if __name__ == "__main__":
    demo_full()
