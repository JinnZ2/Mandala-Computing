#!/usr/bin/env python3
"""
stack_cli.py — Unified geometry-agnostic Mandala CLI
===================================================

One entry point for every geometry, every problem, every scale.

Named stack_cli.py, not mandala_cli.py, because the repo root already has a
mandala_cli.py (the quantum/octahedral/consumer demo runner). That one now
delegates here for anything geometry-agnostic — see its --geometry flag.

Usage:
    # Run a math problem on octahedral geometry
    python mandala_stack/stack_cli.py --geometry octahedral-distorted --problem factorization --data N=15

    # Run DNA analysis on tetrahedral geometry
    python mandala_stack/stack_cli.py --domain dna --seq ATGCGTAC --problem dna_pattern

    # Auto-detect domain and run
    python mandala_stack/stack_cli.py --seq MKTLLI --problem protein_fold

    # Run all demos
    python mandala_stack/stack_cli.py --demo all

    # Build fractal map of a directory
    python mandala_stack/stack_cli.py --fractal-map /path/to/project --order 6

    # Run exploration framework
    python mandala_stack/stack_cli.py --explore --run all

    # List available geometries
    python mandala_stack/stack_cli.py --list-geometries
"""

import argparse
import sys
import os
import json
import math
import tempfile

# Ensure both mandala_stack/ and the repo root are importable, so the legacy
# hooks below (quantum_mandala, octahedral_arithmetic, ...) resolve to the
# repo's copies rather than needing duplicates in this folder.
try:
    from ._paths import bootstrap
except ImportError:  # run as a plain script
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _paths import bootstrap
bootstrap()

from geometry_core import get_geometry, list_geometries
from mandala_solver import MandalaSolver
from adapters import DNAAdapter, ProteinAdapter, RNAAdapter, UniversalAdapter

# Root-backed geometries ("octahedral-root", "cayley-oh") join the registry so
# --list-geometries and --geometry see them alongside the stack's own shapes.
try:
    from stack_bridge import register_bridge_geometries
    register_bridge_geometries()
except Exception:  # bridge is optional; the stack stands alone without it
    pass


def parse_data(data_str: str) -> dict:
    """Parse 'key=value,key2=value2' into dict."""
    result = {}
    if not data_str:
        return result
    for pair in data_str.split(","):
        if "=" in pair:
            k, v = pair.split("=", 1)
            # Try int, then float, then string
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    pass
            result[k.strip()] = v
    return result


def cmd_geometry(args):
    """Run a problem on a specific geometry."""
    geo = get_geometry(args.geometry)
    solver = MandalaSolver(geometry=geo, seed=args.seed)
    data = parse_data(args.data)

    print(f"Geometry: {geo.name}")
    print(f"States: {geo.n_states}, Dimension: {geo.dimension}")
    print(f"Problem: {args.problem}")
    print(f"Data: {data}")
    print("-" * 50)

    if args.problem == "factorization":
        N = data.get("N", 15)
        result = solver.factor(N)
        print(f"N={result.N}, factors={result.factors}, correct={result.correct}")
    elif args.problem == "bloom":
        center = data.get("center", 0)
        layers = data.get("layers", 3)
        result = solver.bloom(center_state=center, expansion_layers=layers)
        print(f"Bloom from state {result.center_state}:")
        for layer in result.layers:
            print(f"  Layer {layer['layer_index']}: {layer['n_states']} states, "
                  f"radius={layer['radius']:.3f}")
    else:
        result = solver.anneal(
            problem_type=args.problem,
            data=data,
            steps=args.steps,
            T_start=args.T_start,
            T_end=args.T_end,
        )
        print(f"Best state: {result.best_state}")
        print(f"Best energy: {result.best_energy:.4f}")
        print(f"Trace length: {len(result.energy_trace)}")


def cmd_domain(args):
    """Run a domain-specific problem (DNA, RNA, protein)."""
    seq = args.seq.upper()
    uni = UniversalAdapter()
    geo, data, detected = uni.prepare(seq)

    # Override if user specified domain
    if args.domain == "dna":
        adapter = DNAAdapter(chirality=args.chirality or "right")
        geo, data = adapter.prepare(seq)
        detected = "dna"
    elif args.domain == "rna":
        adapter = RNAAdapter()
        geo, data = adapter.prepare(seq)
        detected = "rna"
    elif args.domain == "protein":
        adapter = ProteinAdapter()
        geo, data = adapter.prepare(seq)
        detected = "protein"

    solver = MandalaSolver(geometry=geo, seed=args.seed)

    print(f"Sequence: {seq}")
    print(f"Detected domain: {detected}")
    print(f"Geometry: {geo.name}")
    print(f"States: {data['sequence']}")
    print("-" * 50)

    problem = args.problem or f"{detected}_pattern"
    result = solver.anneal(problem_type=problem, data=data, steps=args.steps)
    print(f"Best state: {result.best_state}")
    print(f"Best energy: {result.best_energy:.4f}")

    # Decode back
    if detected == "dna":
        decoded = DNAAdapter(chirality=args.chirality or "right").decode_state(result.best_state)
        print(f"Decoded: {decoded}")
    elif detected == "protein":
        decoded = ProteinAdapter().decode_state(result.best_state)
        print(f"Decoded: {decoded}")
    elif detected == "rna":
        decoded = RNAAdapter().decode_state(result.best_state)
        print(f"Decoded: {decoded}")


def cmd_fractal_map(args):
    """Build fractal address map for files in a directory."""
    import hashlib
    from pathlib import Path
    from fractal_address import ledger_latest, address_tuple

    root = Path(args.fractal_map)
    ledger = []

    for pyfile in root.rglob("*.py"):
        try:
            content = pyfile.read_text()
            h = hashlib.sha256(content.encode()).hexdigest()
            # Detect glyphs
            glyphs = ""
            for g in ["\u2295", "\u2296", "\u2297", "\u2298",
                      "\u2299", "\u229a", "\u229b", "\u229c"]:
                if g in content:
                    glyphs += g
            ledger.append({
                "path": str(pyfile),
                "hash": h,
                "size": len(content),
                "mtime": pyfile.stat().st_mtime,
                "glyphs": glyphs,
            })
        except Exception:
            pass

    ledger_path = Path(tempfile.gettempdir()) / "glyph_ledger.jsonl"
    with open(ledger_path, "w") as f:
        for rec in ledger:
            f.write(json.dumps(rec) + "\n")

    print(f"Ledger: {ledger_path} ({len(ledger)} files)")
    print(f"\nFractal addresses (order={args.order}):")
    print("-" * 60)

    latest = ledger_latest(str(ledger_path))
    for p, rec in sorted(latest.items())[:20]:
        idx, x, y, addr = address_tuple(args.order, rec)
        short = os.path.basename(p)
        print(f"  {addr:<25s}  {short}")


def cmd_explore(args):
    """Run the exploration framework."""
    try:
        from explore import ExplorationRegistry
    except ImportError:
        print("ERROR: explore.py not found in stack directory.")
        print("Copy it from your uploads to the stack directory.")
        sys.exit(1)

    reg = ExplorationRegistry()

    if args.experiment == "all":
        results = reg.run_all(args.mode)
    else:
        result = reg.run_experiment(args.experiment, args.mode)
        results = [result]

    reg.print_report()

    if args.export:
        reg.export_json(args.export)
    if args.csv:
        reg.export_csv(args.csv)


def cmd_demo(args):
    """Run built-in demonstrations."""
    demos = {
        "quantum": _demo_quantum,
        "octahedral": _demo_octahedral,
        "consumer": _demo_consumer,
        "geometry": _demo_geometry,
        "all": _demo_all,
    }

    if args.demo_name not in demos:
        print(f"Unknown demo: {args.demo_name}")
        print(f"Available: {list(demos.keys())}")
        sys.exit(1)

    demos[args.demo_name]()


def _demo_quantum():
    print("\n" + "=" * 60)
    print("DEMO: Quantum Mandala")
    print("=" * 60)
    try:
        from quantum_mandala import QuantumMandalaComputer
        qc = QuantumMandalaComputer(golden_depth=1, sacred_geometry=8)
        result = qc.quantum_annealing("factorization", {"N": 15}, num_steps=50)
        print(f"Factorization of 15: {result['solution']}")
    except Exception as e:
        print(f"Quantum demo skipped: {e}")


def _demo_octahedral():
    print("\n" + "=" * 60)
    print("DEMO: Octahedral Arithmetic")
    print("=" * 60)
    try:
        from octahedral_arithmetic import OctahedralNumber
        n = OctahedralNumber.from_decimal(42)
        print(f"Decimal 42 in glyphs: {n.to_glyphs()}")
        m = OctahedralNumber.from_decimal(7)
        print(f"{n.to_glyphs()} * {m.to_glyphs()} = {(n * m).to_glyphs()}")
    except Exception as e:
        print(f"Octahedral demo skipped: {e}")


def _demo_consumer():
    print("\n" + "=" * 60)
    print("DEMO: Consumer Hardware")
    print("=" * 60)
    try:
        from consumer_hardware import ConsumerGeometricComputer
        c = ConsumerGeometricComputer()
        result = c.compute("factorization", {"N": 15})
        print(f"Factor 15: {result['result']}")
    except Exception as e:
        print(f"Consumer demo skipped: {e}")


def _demo_geometry():
    print("\n" + "=" * 60)
    print("DEMO: Unified Geometry Protocol")
    print("=" * 60)
    for name in list_geometries():
        geo = get_geometry(name)
        print(f"  {name:25s} states={geo.n_states:4d} dim={geo.dimension}")


def _demo_all():
    _demo_geometry()
    _demo_quantum()
    _demo_octahedral()
    _demo_consumer()




def cmd_learn(args):
    """Learn a geometry from data and run a problem."""
    from geometry_learner import GeometryLearner

    print(f"Learning geometry: method={args.learn_method}, dim={args.learn_dim}")

    # For now, support protein sequences as the primary use case
    if args.seq:
        seq = args.seq.upper()
        items = list(seq)

        # Use biochemical properties as the distance metric
        HYDROPATHY = {
            "A": 1.8, "C": 2.5, "D": -3.5, "E": -3.5, "F": 2.8,
            "G": -0.4, "H": -3.2, "I": 4.5, "K": -3.9, "L": 3.8,
            "M": 1.9, "N": -3.5, "P": -1.6, "Q": -3.5, "R": -4.5,
            "S": -0.8, "T": -0.7, "V": 4.2, "W": -0.9, "Y": -1.3,
        }
        MW = {
            "A": 89.1, "C": 121.2, "D": 133.1, "E": 147.1, "F": 165.2,
            "G": 75.1, "H": 155.2, "I": 131.2, "K": 146.2, "L": 131.2,
            "M": 149.2, "N": 132.1, "P": 115.1, "Q": 146.2, "R": 174.2,
            "S": 105.1, "T": 119.1, "V": 117.1, "W": 204.2, "Y": 181.2,
        }
        PKA = {"C": 8.3, "D": 3.9, "E": 4.3, "H": 6.0, "K": 10.5, "R": 12.5, "Y": 10.1}

        def bio_dist(a, b):
            h1 = HYDROPATHY.get(a, 0)
            h2 = HYDROPATHY.get(b, 0)
            m1 = MW.get(a, 100)
            m2 = MW.get(b, 100)
            c1 = PKA.get(a, 7.0)
            c2 = PKA.get(b, 7.0)
            return math.sqrt(4*(h1-h2)**2 + 0.01*(m1-m2)**2 + (c1-c2)**2)

        learner = GeometryLearner(
            method=args.learn_method,
            dim=args.learn_dim,
            n_neighbors=3,
            seed=args.seed
        )
        geo = learner.learn(items, bio_dist)

        # Set real eigenvalues
        def ev_fn(item):
            h = (HYDROPATHY.get(item, 0) + 5) / 10
            m = MW.get(item, 100) / 210.0
            c = PKA.get(item, 7.0) / 14.0
            total = h + m + c
            return (h/total, m/total, c/total)
        geo.set_eigenvalues(ev_fn)

        print(f"Learned geometry: {geo.name}")
        print(f"Positions (first 3):")
        for i in range(min(3, len(items))):
            print(f"  {items[i]}: {geo.position(i)}")
        print(f"Transitions (first 3):")
        for i in range(min(3, len(items))):
            print(f"  {items[i]} -> {[geo.idx_to_item[j] for j in geo.transitions(i)]}")

        # Register for use
        from geometry_core import register_learned_geometry
        register_learned_geometry("learned-protein", geo)

        # Now run the problem
        solver = MandalaSolver(geometry=geo, seed=args.seed)
        data = {"sequence": [geo.item_to_idx[aa] for aa in items], "original": seq}
        problem = args.problem or "protein_fold"
        result = solver.anneal(problem_type=problem, data=data, steps=args.steps)
        print(f"\nAnnealing result:")
        print(f"  Best state: {result.best_state}")
        print(f"  Best energy: {result.best_energy:.4f}")

        # Bloom
        bloom = solver.bloom(center_state=0, expansion_layers=3)
        print(f"\nBloom from {items[0]}:")
        for layer in bloom.layers:
            ring_items = [geo.idx_to_item[s] for s in layer['states']]
            print(f"  Layer {layer['layer_index']}: {ring_items}")

        return geo
    else:
        print("--learn-geometry requires --seq (sequence to learn from)")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Unified Mandala Computing CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --geometry octahedral-distorted --problem factorization --data N=15
  %(prog)s --seq ATGCGTAC --domain dna --problem dna_pattern
  %(prog)s --seq MKTLLI --problem protein_fold
  %(prog)s --fractal-map . --order 6
  %(prog)s --explore --run all --mode distorted
  %(prog)s --demo all
  %(prog)s --list-geometries
        """,
    )

    # Geometry mode
    parser.add_argument("--geometry", help="Geometry name (see --list-geometries)")
    parser.add_argument("--problem", help="Problem type")
    parser.add_argument("--data", default="", help="Problem data as key=value,key2=value2")
    parser.add_argument("--steps", type=int, default=200, help="Annealing steps")
    parser.add_argument("--T-start", type=float, default=2.0)
    parser.add_argument("--T-end", type=float, default=0.01)

    # Domain mode
    parser.add_argument("--seq", help="Biological sequence (DNA/RNA/protein)")
    parser.add_argument("--domain", choices=["dna", "rna", "protein"],
                        help="Force domain type (auto-detected if omitted)")
    parser.add_argument("--chirality", choices=["right", "left"],
                        help="Chirality for DNA/RNA")

    # Fractal map
    parser.add_argument("--fractal-map", metavar="DIR",
                        help="Build fractal address map for directory")
    parser.add_argument("--order", type=int, default=6,
                        help="Hilbert order for fractal map")

    # Exploration
    parser.add_argument("--explore", action="store_true",
                        help="Run exploration framework")
    parser.add_argument("--run", dest="experiment", default="all",
                        help="Experiment to run (or 'all')")
    parser.add_argument("--mode", choices=["distorted", "cube"], default="distorted",
                        help="Geometry mode for exploration")
    parser.add_argument("--export", help="Export exploration results to JSON")
    parser.add_argument("--csv", help="Export exploration results to CSV")

    # Demo
    parser.add_argument("--demo", dest="demo_name",
                        help="Run demo: quantum, octahedral, consumer, geometry, all")


    # Learned geometry mode
    parser.add_argument("--learn-geometry", action="store_true",
                        help="Learn geometry from data instead of using pre-defined")
    parser.add_argument("--learn-method", choices=["force_directed", "mds", "spectral", "isomap"],
                        default="force_directed", help="Geometry learning method")
    parser.add_argument("--learn-dim", type=int, default=3,
                        help="Dimension of learned geometry")
    # Meta
    parser.add_argument("--list-geometries", action="store_true",
                        help="List available geometries")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    if args.list_geometries:
        print("Available geometries:")
        for name in list_geometries():
            geo = get_geometry(name)
            print(f"  {name:25s} states={geo.n_states:4d} dim={geo.dimension}")
        return

    if args.learn_geometry:
        cmd_learn(args)
        return

    if args.demo_name:
        cmd_demo(args)
    elif args.fractal_map:
        cmd_fractal_map(args)
    elif args.explore:
        cmd_explore(args)
    elif args.seq:
        cmd_domain(args)
    elif args.geometry:
        cmd_geometry(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
