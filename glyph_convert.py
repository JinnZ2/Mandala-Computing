"""
GLYPH CONVERTER v1.0
Human-facing bridge between decimal and octahedral glyph space.

Accepts decimal input, converts to native glyph representation,
performs computation in glyph space, and presents results in both
glyph and decimal for human readability.

Usage:
    python glyph_convert.py                  # interactive mode
    python glyph_convert.py 143              # factor a number
    python glyph_convert.py 3/7             # convert a fraction
    python glyph_convert.py 11 * 13          # glyph arithmetic
"""

from __future__ import annotations
import sys

from octahedral_arithmetic import (
    OctahedralNumber, GlyphFraction, GLYPHS, BASE,
    factor_pair_glyphs,
)


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def dual(n: OctahedralNumber, label: str = "") -> str:
    """Display a number in both glyph and decimal, side by side."""
    prefix = f"{label}: " if label else ""
    return f"{prefix}{n.to_glyphs():<10s}  (decimal: {n.to_decimal()})"


def dual_fraction(f: GlyphFraction, label: str = "") -> str:
    """Display a fraction in both glyph and decimal."""
    prefix = f"{label}: " if label else ""
    p, q = f.to_decimal_ratio()
    return f"{prefix}{f.to_glyphs():<14s}  (decimal: {p}/{q})"


# ---------------------------------------------------------------------------
# Conversion functions
# ---------------------------------------------------------------------------

def convert_number(n: int) -> dict:
    """Convert a decimal integer to full glyph analysis."""
    oct_n = OctahedralNumber.from_decimal(n)
    result = {
        "decimal": n,
        "glyph": oct_n.to_glyphs(),
        "glyph_msb": oct_n.to_glyphs_msb(),
        "digits": len(oct_n),
        "phi_weight": oct_n.phi_weight(),
        "is_prime": oct_n.is_prime(),
    }

    if not oct_n.is_prime() and n > 1:
        factors = oct_n.factorize()
        result["factors_glyph"] = [f.to_glyphs() for f in factors]
        result["factors_decimal"] = [f.to_decimal() for f in factors]

        pair = factor_pair_glyphs(n)
        if pair:
            fa, fb = pair
            result["factor_pair"] = (fa.to_glyphs(), fb.to_glyphs())
            result["factor_pair_decimal"] = (fa.to_decimal(), fb.to_decimal())
    else:
        result["factors_glyph"] = ["IRREDUCIBLE"]
        result["factors_decimal"] = [n]

    return result


def convert_fraction(p: int, q: int) -> dict:
    """Convert a decimal fraction to glyph representation."""
    gf = GlyphFraction.from_decimal_ratio(p, q)
    return {
        "decimal": f"{p}/{q}",
        "glyph": gf.to_glyphs(),
        "irreducible": gf.is_irreducible(),
        "reduced_decimal": f"{gf.num.to_decimal()}/{gf.den.to_decimal()}",
        "numerator_glyph": gf.num.to_glyphs(),
        "denominator_glyph": gf.den.to_glyphs(),
    }


def glyph_arithmetic(a: int, op: str, b: int) -> dict:
    """Perform arithmetic in glyph space."""
    oa = OctahedralNumber.from_decimal(a)
    ob = OctahedralNumber.from_decimal(b)

    if op == "+":
        result = oa + ob
        op_name = "addition"
    elif op == "-":
        result = oa - ob
        op_name = "subtraction"
    elif op in ("*", "x"):
        result = oa * ob
        op_name = "multiplication"
    elif op == "/":
        q, r = oa.divmod_glyph(ob)
        return {
            "expression_decimal": f"{a} / {b}",
            "expression_glyph": f"{oa.to_glyphs()} / {ob.to_glyphs()}",
            "quotient_glyph": q.to_glyphs(),
            "quotient_decimal": q.to_decimal(),
            "remainder_glyph": r.to_glyphs(),
            "remainder_decimal": r.to_decimal(),
            "exact": r.is_zero(),
        }
    elif op == "%":
        _, r = oa.divmod_glyph(ob)
        result = r
        op_name = "modulo"
    else:
        raise ValueError(f"Unknown operator: {op}")

    return {
        "expression_decimal": f"{a} {op} {b} = {result.to_decimal()}",
        "expression_glyph": f"{oa.to_glyphs()} {op} {ob.to_glyphs()} = {result.to_glyphs()}",
        "result_glyph": result.to_glyphs(),
        "result_decimal": result.to_decimal(),
        "operation": op_name,
    }


def solve_factorization(N: int, method: str = "annealing") -> dict:
    """
    Factor N using the mandala solver, return results in glyph space.

    Methods: 'annealing', 'tempering', 'holographic'
    """
    from mandala_computer import MandalaComputer

    mc = MandalaComputer(golden_depth=5, sacred_geometry=8)
    mc.encode_factorization(N)

    if method == "tempering":
        r = mc.parallel_tempering(num_replicas=5, T_min=0.05, T_max=10.0, max_steps=10000)
    elif method == "holographic":
        from holographic_mandala import HolographicMandala, ProblemType
        hm = HolographicMandala(golden_depth=5, sacred_geometry=8,
                                entanglement_decay=0.6, holographic_weight=0.5)
        r = hm.holographic_solve(ProblemType.FACTORIZATION, {"N": N},
                                 max_steps_per_scale=2000, num_sweeps=3)
    else:
        r = mc.simulated_annealing(max_steps=10000, T_start=8.0, T_end=0.001)

    sol = r["solution"]
    oct_N = OctahedralNumber.from_decimal(N)

    result = {
        "N_decimal": N,
        "N_glyph": oct_N.to_glyphs(),
        "method": method,
        "verified": sol.get("verified", False),
        "energy": r["final_energy"],
    }

    pair = sol.get("best_pair")
    if pair:
        ga = OctahedralNumber.from_decimal(pair[0])
        gb = OctahedralNumber.from_decimal(pair[1])
        result["pair_decimal"] = pair
        result["pair_glyph"] = (ga.to_glyphs(), gb.to_glyphs())
        result["product_glyph"] = (ga * gb).to_glyphs()
        result["residual"] = sol.get("residual", "?")

    # Exact factorization in glyph space for comparison
    exact = factor_pair_glyphs(N)
    if exact:
        ea, eb = exact
        result["exact_glyph"] = (ea.to_glyphs(), eb.to_glyphs())
        result["exact_decimal"] = (ea.to_decimal(), eb.to_decimal())
    else:
        result["exact_glyph"] = "PRIME"

    return result


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def print_number(n: int):
    """Pretty-print a number analysis."""
    info = convert_number(n)
    print(f"\n  decimal:     {info['decimal']}")
    print(f"  glyph:       {info['glyph']}")
    print(f"  glyph (msb): {info['glyph_msb']}")
    print(f"  digits:      {info['digits']}")
    print(f"  phi-weight:  {info['phi_weight']:.4f}")
    print(f"  prime:       {info['is_prime']}")
    if "factor_pair" in info:
        print(f"  factors:     {info['factor_pair'][0]} * {info['factor_pair'][1]}"
              f"  (decimal: {info['factor_pair_decimal'][0]} * {info['factor_pair_decimal'][1]})")
    elif info["is_prime"]:
        print(f"  factors:     IRREDUCIBLE")


def print_fraction(p: int, q: int):
    """Pretty-print a fraction analysis."""
    info = convert_fraction(p, q)
    print(f"\n  decimal:     {info['decimal']}")
    print(f"  glyph:       {info['glyph']}")
    print(f"  reduced:     {info['reduced_decimal']}")
    print(f"  irreducible: {info['irreducible']}")


def print_arithmetic(a: int, op: str, b: int):
    """Pretty-print an arithmetic operation."""
    info = glyph_arithmetic(a, op, b)
    print(f"\n  decimal: {info['expression_decimal']}")
    print(f"  glyph:   {info['expression_glyph']}")
    if "quotient_glyph" in info:
        print(f"  exact:   {info['exact']}")


def print_solve(N: int, method: str = "annealing"):
    """Pretty-print a mandala factorization solve."""
    info = solve_factorization(N, method)
    print(f"\n  N:        {info['N_glyph']}  (decimal: {info['N_decimal']})")
    print(f"  method:   {info['method']}")
    if "pair_glyph" in info:
        print(f"  solver:   {info['pair_glyph'][0]} * {info['pair_glyph'][1]}"
              f"  = {info['product_glyph']}"
              f"  (decimal: {info['pair_decimal'][0]} * {info['pair_decimal'][1]})")
        print(f"  verified: {info['verified']}  residual: {info['residual']}")
    if "exact_glyph" in info and info["exact_glyph"] != "PRIME":
        print(f"  exact:    {info['exact_glyph'][0]} * {info['exact_glyph'][1]}"
              f"  (decimal: {info['exact_decimal'][0]} * {info['exact_decimal'][1]})")


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------

def interactive():
    """Interactive glyph converter."""
    print("=" * 50)
    print("GLYPH CONVERTER")
    print("  decimal -> glyph -> compute -> display")
    print("=" * 50)
    print()
    print("Commands:")
    print("  <number>         — analyze a number")
    print("  <p>/<q>          — convert a fraction")
    print("  <a> + <b>        — glyph addition")
    print("  <a> * <b>        — glyph multiplication")
    print("  <a> / <b>        — glyph division")
    print("  factor <N>       — factor N via mandala solver")
    print("  primes <max>     — list primes up to max")
    print("  table            — multiplication table")
    print("  quit             — exit")
    print()

    while True:
        try:
            line = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not line or line == "quit":
            break

        try:
            if line == "table":
                _print_table()
            elif line.startswith("primes"):
                parts = line.split()
                limit = int(parts[1]) if len(parts) > 1 else 50
                _print_primes(limit)
            elif line.startswith("factor"):
                parts = line.split()
                N = int(parts[1])
                method = parts[2] if len(parts) > 2 else "annealing"
                print_solve(N, method)
            elif "/" in line and not any(c.isalpha() for c in line):
                # Could be fraction or division
                parts = line.split("/")
                if len(parts) == 2:
                    p, q = int(parts[0].strip()), int(parts[1].strip())
                    print_fraction(p, q)
            elif any(op in line for op in [" + ", " - ", " * ", " x ", " % "]):
                for op in ["+", "-", "*", "x", "%"]:
                    if f" {op} " in line:
                        parts = line.split(f" {op} ")
                        a, b = int(parts[0].strip()), int(parts[1].strip())
                        print_arithmetic(a, op, b)
                        break
            else:
                n = int(line)
                print_number(n)
        except Exception as e:
            print(f"  error: {e}")

        print()


def _print_primes(limit: int):
    """List primes in glyph space."""
    print(f"\n  Primes up to {limit}:")
    count = 0
    for i in range(2, limit + 1):
        n = OctahedralNumber.from_decimal(i)
        if n.is_prime():
            count += 1
            print(f"    {n.to_glyphs():<8s}  (decimal: {i})")
    print(f"\n  {count} primes found")


def _print_table():
    """Print glyph multiplication table."""
    print("\n    ", end="")
    for j in range(BASE):
        print(f"  {GLYPHS[j]:>4s}", end="")
    print()
    print("    " + "-" * (6 * BASE))
    for i in range(BASE):
        print(f" {GLYPHS[i]} |", end="")
        for j in range(BASE):
            p = OctahedralNumber((i,)) * OctahedralNumber((j,))
            print(f"  {p.to_glyphs():>4s}", end="")
        print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        interactive()
    elif len(args) == 1:
        arg = args[0]
        if "/" in arg:
            parts = arg.split("/")
            print_fraction(int(parts[0]), int(parts[1]))
        else:
            n = int(arg)
            print_number(n)
            if not OctahedralNumber.from_decimal(n).is_prime() and n > 3:
                print("\n  Mandala solver:")
                print_solve(n)
    elif len(args) == 3:
        a, op, b = int(args[0]), args[1], int(args[2])
        print_arithmetic(a, op, b)
    else:
        print(f"Usage: python glyph_convert.py [number | p/q | a op b]")
