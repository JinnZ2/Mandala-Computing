#!/usr/bin/env python3
"""
Mandala Computing Unified CLI
Runs without Jupyter. No ipywidgets required.

Covers the root repo's demos (quantum, octahedral arithmetic, scale audit) plus
the geometry-agnostic stack in mandala_stack/ (consumer hardware, fractal
address mapping, and every registered geometry). Both directories are put on
sys.path, so this file imports either side by plain module name.

For the full geometry-agnostic surface — domain adapters, learned geometries,
geodesic memory — use mandala_stack/stack_cli.py.
"""
import argparse
import sys
import os

# Add the repo root and the mandala_stack/ folder to path, so consumer_hardware,
# fractal_address, geometry_core, ... resolve without duplicating them here.
_ROOT = os.path.dirname(os.path.abspath(__file__))
for _path in (_ROOT, os.path.join(_ROOT, 'mandala_stack')):
    if _path not in sys.path:
        sys.path.insert(0, _path)

def run_quantum_demos():
    from quantum_mandala import (
        demo_quantum_factorization, demo_grover_search,
        demo_quantum_superposition, demo_qaoa,
        demo_entangled_annealing, demo_thermal_bridge,
        demo_fret_coupling, demo_ising_annealing
    )
    print("\n" + "="*60)
    print("QUANTUM MANDALA DEMONSTRATIONS")
    print("="*60)
    demo_quantum_factorization()
    demo_grover_search()
    demo_quantum_superposition()
    demo_qaoa()
    demo_entangled_annealing()
    demo_thermal_bridge()
    demo_fret_coupling()
    demo_ising_annealing()

def run_octahedral_demos():
    from octahedral_arithmetic import (
        demo_glyph_arithmetic, demo_primes,
        demo_fractions, demo_multiplication_table,
        demo_factorization_bridge
    )
    print("\n" + "="*60)
    print("OCTAHEDRAL ARITHMETIC DEMONSTRATIONS")
    print("="*60)
    demo_glyph_arithmetic()
    demo_primes()
    demo_fractions()
    demo_multiplication_table()
    demo_factorization_bridge()

def run_consumer_demos():
    from consumer_hardware import (
        demo_audio, demo_image, demo_text,
        demo_factorization, demo_progressive, demo_mobile
    )
    print("\n" + "="*60)
    print("CONSUMER HARDWARE DEMONSTRATIONS")
    print("="*60)
    demo_audio()
    demo_image()
    demo_text()
    demo_factorization()
    demo_progressive()
    demo_mobile()

def run_scale_audit():
    from scale_invariance_breakdown import list_breakdown_classes, list_proof_protocol
    print("\n" + "="*60)
    print("SCALE INVARIANCE AUDIT")
    print("="*60)
    print(list_breakdown_classes())
    print(list_proof_protocol())

def run_fractal_map(root_dirs):
    import json
    import tempfile
    # Build a minimal glyph ledger from Python files in root_dirs
    ledger = []
    for root in root_dirs:
        for dirpath, _, filenames in os.walk(root):
            for fn in filenames:
                if fn.endswith('.py'):
                    path = os.path.join(dirpath, fn)
                    try:
                        with open(path, 'r') as f:
                            content = f.read()
                        import hashlib
                        h = hashlib.sha256(content.encode()).hexdigest()
                        # Simple glyph detection: look for octahedral unicode
                        glyphs = ''
                        for g in ['\u2295','\u2296','\u2297','\u2298','\u2299','\u229a','\u229b','\u229c']:
                            if g in content:
                                glyphs += g
                        ledger.append({
                            "path": path,
                            "hash": h,
                            "size": len(content),
                            "mtime": os.path.getmtime(path),
                            "glyphs": glyphs
                        })
                    except Exception:
                        pass
    ledger_path = os.path.join(tempfile.gettempdir(), 'glyph_ledger.jsonl')
    with open(ledger_path, 'w') as f:
        for rec in ledger:
            f.write(json.dumps(rec) + '\n')
    print(f"Ledger written: {ledger_path} ({len(ledger)} files)")
    # Run fractal map
    from fractal_address import ledger_latest, address_tuple
    latest = ledger_latest(ledger_path)
    print(f"\nFractal addresses (order=6):")
    for p, rec in list(latest.items())[:10]:
        idx, x, y, addr = address_tuple(6, rec)
        print(f"  {addr:<20s}  {os.path.basename(p)}")

def run_geometry_demos():
    """Geometry-agnostic stack: every registered shape, plus the root bridge."""
    from geometry_core import get_geometry, list_geometries
    from mandala_solver import MandalaSolver
    from stack_bridge import register_bridge_geometries

    register_bridge_geometries()
    print("\n" + "="*60)
    print("GEOMETRY-AGNOSTIC STACK (mandala_stack/)")
    print("="*60)
    for name in list_geometries():
        geo = get_geometry(name)
        print(f"  {name:<24s} states={geo.n_states:<6d} dim={geo.dimension}")

    print("\n  Same solver, different shapes — factoring 15:")
    for name in ["octahedral-distorted", "octahedral-root", "cayley-oh",
                 "dodecahedral"]:
        solver = MandalaSolver(geometry=get_geometry(name), seed=42)
        result = solver.factor(15)
        print(f"    {name:<24s} -> {result.factors} (correct={result.correct})")


def run_bridge_demo():
    """Bridge: stack geometry proposing moves, root engine scoring them."""
    from stack_bridge import _self_test
    _self_test()


def main():
    ap = argparse.ArgumentParser(
        description="Mandala Computing Unified CLI "
                    "(root engine + mandala_stack/ geometries)")
    ap.add_argument('--quantum', action='store_true', help='Run quantum demos')
    ap.add_argument('--octahedral', action='store_true', help='Run octahedral arithmetic demos')
    ap.add_argument('--consumer', action='store_true', help='Run consumer hardware demos (mandala_stack/)')
    ap.add_argument('--geometry', action='store_true', help='Run geometry-agnostic stack demos (mandala_stack/)')
    ap.add_argument('--bridge', action='store_true', help='Run the stack <-> root engine bridge self-test')
    ap.add_argument('--scale-audit', action='store_true', help='Run scale invariance audit')
    ap.add_argument('--fractal-map', nargs='+', metavar='DIR', help='Build fractal address map for directories')
    ap.add_argument('--all', action='store_true', help='Run all demos')
    args = ap.parse_args()

    if not any([args.quantum, args.octahedral, args.consumer, args.geometry,
                args.bridge, args.scale_audit, args.fractal_map, args.all]):
        ap.print_help()
        sys.exit(0)

    if args.all or args.quantum:
        run_quantum_demos()
    if args.all or args.octahedral:
        run_octahedral_demos()
    if args.all or args.consumer:
        run_consumer_demos()
    if args.all or args.geometry:
        run_geometry_demos()
    if args.all or args.bridge:
        run_bridge_demo()
    if args.all or args.scale_audit:
        run_scale_audit()
    if args.fractal_map:
        run_fractal_map(args.fractal_map)

if __name__ == '__main__':
    main()
