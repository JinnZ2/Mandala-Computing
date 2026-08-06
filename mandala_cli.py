#!/usr/bin/env python3
"""
Mandala Computing Unified CLI
Runs without Jupyter. No ipywidgets required.
"""
import argparse
import sys
import os

# Add stack directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

def main():
    ap = argparse.ArgumentParser(description="Mandala Computing Unified CLI")
    ap.add_argument('--quantum', action='store_true', help='Run quantum demos')
    ap.add_argument('--octahedral', action='store_true', help='Run octahedral arithmetic demos')
    ap.add_argument('--consumer', action='store_true', help='Run consumer hardware demos')
    ap.add_argument('--scale-audit', action='store_true', help='Run scale invariance audit')
    ap.add_argument('--fractal-map', nargs='+', metavar='DIR', help='Build fractal address map for directories')
    ap.add_argument('--all', action='store_true', help='Run all demos')
    args = ap.parse_args()

    if not any([args.quantum, args.octahedral, args.consumer, args.scale_audit, args.fractal_map, args.all]):
        ap.print_help()
        sys.exit(0)

    if args.all or args.quantum:
        run_quantum_demos()
    if args.all or args.octahedral:
        run_octahedral_demos()
    if args.all or args.consumer:
        run_consumer_demos()
    if args.all or args.scale_audit:
        run_scale_audit()
    if args.fractal_map:
        run_fractal_map(args.fractal_map)

if __name__ == '__main__':
    main()
