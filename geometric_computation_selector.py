#!/usr/bin/env python3
"""
Geometric Computation Selector (adaptive, with LLM interface)
===============================================================
Selects the best Mandala Computing solver strategy for a given problem
type/size, learning from *real* benchmark runs against the actual engine
(mandala_computer.py, holographic_mandala.py, quantum_mandala.py) rather
than a hypothetical numerical-algorithm menu scored by invented runtimes.
See experiments/README.md for the integration plan this implements.
"""

import json
import time
import random
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

from mandala_computer import MandalaComputer, ProblemType
from holographic_mandala import HolographicMandala
from quantum_mandala import QuantumMandalaComputer

# ----------------------------------------------------------------------
# Problem representation — ProblemType is re-exported from
# mandala_computer.py rather than redefined, so it can never drift out of
# sync with what the engine actually supports.
# ----------------------------------------------------------------------
@dataclass
class Problem:
    type: ProblemType
    size: int                    # N for factorization; num_variables/clauses/cities/nodes otherwise
    data: Optional[Dict] = None  # extra generator params, e.g. {"num_colors": 4}

# ----------------------------------------------------------------------
# Method definition (with benchmark storage)
# ----------------------------------------------------------------------
@dataclass
class Method:
    name: str
    applicable_types: List[ProblemType]
    min_size: int
    max_size: int
    parallel: bool
    quantum: bool
    description: str = ""
    # Adaptive fields
    benchmark_runtimes: Dict[str, float] = field(default_factory=dict)  # key: str(size) -> runtime
    avg_score: float = 0.0

# ----------------------------------------------------------------------
# Method registry: the engine's actual solver strategies, not a
# hypothetical numerical-algorithm menu.
# ----------------------------------------------------------------------
_ALL_TYPES = list(ProblemType)

METHODS = [
    Method("relax_to_ground_state", _ALL_TYPES, 2, 10_000_000, False, False,
           "Plain Metropolis-Hastings thermal relaxation (mandala_computer.py)"),
    Method("simulated_annealing", _ALL_TYPES, 2, 10_000_000, False, False,
           "Cooling-schedule annealing (mandala_computer.py)"),
    Method("parallel_tempering", _ALL_TYPES, 2, 10_000_000, True, False,
           "Multi-replica temperature-ladder exploration (mandala_computer.py)"),
    Method("sovereign_tempering", _ALL_TYPES, 2, 10_000_000, True, False,
           "Pack-aware parallel tempering (mandala_computer.py)"),
    Method("holographic_solve", _ALL_TYPES, 20, 10_000_000, False, False,
           "Coarse-to-fine renormalization solve; best at larger sizes (holographic_mandala.py)"),
    Method("quantum_annealing", [ProblemType.FACTORIZATION, ProblemType.OPTIMIZATION], 2, 10_000, False, True,
           "Adiabatic evolution over the octahedral Hilbert space (quantum_mandala.py) — small problems only"),
    Method("qaoa", [ProblemType.FACTORIZATION, ProblemType.OPTIMIZATION], 2, 10_000, False, True,
           "QAOA with Nelder-Mead parameter optimization (quantum_mandala.py) — small problems only"),
]

# ----------------------------------------------------------------------
# 3D Bloom Cube — no counterpart yet in the engine; kept as a candidate
# for a future dedup strategy inside geometric_state_algebra.py's
# null-space search (see experiments/README.md), not wired to a solver.
# ----------------------------------------------------------------------
class BloomCube3D:
    """
    A 3D cube where each cell contains a Bloom filter of octahedral state hashes.
    """
    def __init__(self, side=16, filter_bits=1024, num_hashes=3):
        self.side = side
        self.filter_bits = filter_bits
        self.num_hashes = num_hashes
        self.cells = [[[[0] * ((filter_bits + 63) // 64) for _ in range(side)]
                       for _ in range(side)] for _ in range(side)]

    def _hash(self, key, seed):
        h = hashlib.sha256(f"{key}{seed}".encode()).hexdigest()
        return int(h[:8], 16) % self.filter_bits

    def _set_bit(self, cell, bit):
        idx = bit // 64
        mask = 1 << (bit % 64)
        self.cells[cell[0]][cell[1]][cell[2]][idx] |= mask

    def _get_bit(self, cell, bit):
        idx = bit // 64
        mask = 1 << (bit % 64)
        return (self.cells[cell[0]][cell[1]][cell[2]][idx] & mask) != 0

    def add(self, state_vector, relation_index):
        for i in range(0, len(state_vector) - 2, 3):
            cell = (state_vector[i] % self.side, state_vector[i+1] % self.side, state_vector[i+2] % self.side)
            for seed in range(self.num_hashes):
                self._set_bit(cell, self._hash(relation_index, seed))

    def query(self, state_vector, relation_index):
        for i in range(0, len(state_vector) - 2, 3):
            cell = (state_vector[i] % self.side, state_vector[i+1] % self.side, state_vector[i+2] % self.side)
            for seed in range(self.num_hashes):
                if not self._get_bit(cell, self._hash(relation_index, seed)):
                    return False
        return True

# ----------------------------------------------------------------------
# Synthetic problem generation — builds real encode_*() inputs so
# benchmark runs exercise the actual engine, not a mock.
# ----------------------------------------------------------------------
def _synthetic_kwargs(problem: Problem) -> Dict:
    import numpy as np
    size = max(2, problem.size)
    if problem.type == ProblemType.FACTORIZATION:
        return {"N": size}
    elif problem.type == ProblemType.SAT:
        num_clauses = (problem.data or {}).get("num_clauses", size * 3)
        clauses = [[random.choice([1, -1]) * random.randint(1, size) for _ in range(3)]
                   for _ in range(num_clauses)]
        return {"clauses": clauses}
    elif problem.type == ProblemType.TSP:
        return {"cities": np.random.rand(size, 2) * 100}
    elif problem.type == ProblemType.GRAPH_COLORING:
        num_colors = (problem.data or {}).get("num_colors", 3)
        adjacency = [[i, (i + 1) % size] for i in range(size)]
        return {"adjacency": adjacency, "num_colors": num_colors}
    elif problem.type == ProblemType.OPTIMIZATION:
        def cost_fn(states):
            return sum((states[i] - states[(i + 1) % len(states)]) ** 2 for i in range(len(states)))
        return {"cost_fn": cost_fn, "num_variables": size}
    raise ValueError(f"Unknown problem type: {problem.type}")


def _encode(computer: MandalaComputer, problem: Problem):
    """Encode a synthetic instance of `problem` onto `computer` via the
    engine's own encode_*() methods — no hand-rolled problem_data schemas."""
    kwargs = _synthetic_kwargs(problem)
    if problem.type == ProblemType.FACTORIZATION:
        computer.encode_factorization(kwargs["N"])
    elif problem.type == ProblemType.SAT:
        computer.encode_sat(kwargs["clauses"])
    elif problem.type == ProblemType.TSP:
        computer.encode_tsp(kwargs["cities"])
    elif problem.type == ProblemType.GRAPH_COLORING:
        computer.encode_graph_coloring(kwargs["adjacency"], kwargs["num_colors"])
    elif problem.type == ProblemType.OPTIMIZATION:
        computer.encode_optimization(kwargs["cost_fn"], kwargs["num_variables"])


def _golden_depth_for(size: int) -> int:
    if size < 50:
        return 2
    if size < 500:
        return 3
    return 4

# ----------------------------------------------------------------------
# Solver dispatch — actually runs the named method against the engine.
# ----------------------------------------------------------------------
_CLASSICAL_METHODS = {"relax_to_ground_state", "simulated_annealing",
                      "parallel_tempering", "sovereign_tempering"}


def _run_solver(method_name: str, problem: Problem, quick: bool = True) -> Dict:
    """Run the named engine solver against a synthetic instance of `problem`.
    quick=True uses reduced step counts suited to benchmarking, not solution
    quality — this is a meta-optimizer choosing between solvers, not a
    request for a fully converged answer."""
    golden_depth = _golden_depth_for(problem.size)
    max_steps = 150 if quick else 1500

    if method_name in ("quantum_annealing", "qaoa"):
        qc = QuantumMandalaComputer(golden_depth=1, sacred_geometry=8)
        engine_type = "factorization" if problem.type == ProblemType.FACTORIZATION else "optimization"
        data = {"N": problem.size} if problem.type == ProblemType.FACTORIZATION else {}
        start = time.time()
        if method_name == "quantum_annealing":
            result = qc.quantum_annealing(engine_type, data, num_steps=40 if quick else 100)
        else:
            result = qc.qaoa(engine_type, data, num_layers=2 if quick else 4, optimize=True)
        elapsed = time.time() - start
        return {"final_energy": result["final_energy"], "time": elapsed, "convergence_rate": None}

    if method_name == "holographic_solve":
        hm = HolographicMandala(golden_depth=golden_depth, sacred_geometry=8)
        problem_data = {"N": problem.size} if problem.type == ProblemType.FACTORIZATION else None
        if problem_data is None:
            scratch = MandalaComputer(golden_depth=1, sacred_geometry=8)
            _encode(scratch, problem)
            problem_data = scratch.problem_data
        result = hm.holographic_solve(problem.type, problem_data,
                                      max_steps_per_scale=max_steps,
                                      num_sweeps=1 if quick else 3)
        return {"final_energy": result.get("final_energy"), "time": result.get("time"),
                "convergence_rate": hm.get_convergence_rate()}

    if method_name in _CLASSICAL_METHODS:
        mc = MandalaComputer(golden_depth=golden_depth, sacred_geometry=8)
        _encode(mc, problem)
        if method_name == "relax_to_ground_state":
            result = mc.relax_to_ground_state(max_steps=max_steps)
        elif method_name == "simulated_annealing":
            result = mc.simulated_annealing(max_steps=max_steps)
        elif method_name == "parallel_tempering":
            result = mc.parallel_tempering(max_steps=max_steps, steps_per_swap=30)
        else:
            result = mc.sovereign_tempering(max_steps=max_steps, steps_per_swap=30)
        return {"final_energy": result.get("final_energy"), "time": result.get("time"),
                "convergence_rate": mc.get_convergence_rate()}

    raise ValueError(f"Unknown method: {method_name}")

# ----------------------------------------------------------------------
# Benchmark collector & adaptive scorer
# ----------------------------------------------------------------------
class BenchmarkCollector:
    def __init__(self, db_path="benchmark_db.json"):
        self.db_path = db_path
        self.load()

    def load(self):
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                for name, runtimes in data.items():
                    method = next((m for m in METHODS if m.name == name), None)
                    if method:
                        method.benchmark_runtimes = runtimes
        except FileNotFoundError:
            pass

    def save(self):
        data = {m.name: m.benchmark_runtimes for m in METHODS}
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)

    def add_benchmark(self, method_name: str, size: int, runtime: float):
        method = next((m for m in METHODS if m.name == method_name), None)
        if method:
            method.benchmark_runtimes[str(size)] = runtime
            self.save()

    def estimate_runtime(self, method: Method, size: int) -> Optional[float]:
        """Find the closest learned benchmark by size."""
        if not method.benchmark_runtimes:
            return None
        best_key = min(method.benchmark_runtimes, key=lambda k: abs(int(k) - size))
        return method.benchmark_runtimes[best_key]

    def run_benchmark(self, method: Method, problem: Problem, quick: bool = True) -> Optional[Dict]:
        """Actually run the engine solver and record the real wall-clock time."""
        if problem.type not in method.applicable_types:
            return None
        if not (method.min_size <= problem.size <= method.max_size):
            return None
        result = _run_solver(method.name, problem, quick=quick)
        if result.get("time") is not None:
            self.add_benchmark(method.name, problem.size, result["time"])
        return result


class AdaptiveScorer:
    def __init__(self, collector: BenchmarkCollector):
        self.collector = collector
        self.alpha = 0.7  # weight for learned benchmark vs heuristic prior

    def score(self, method: Method, problem: Problem) -> float:
        emp = self.collector.estimate_runtime(method, problem.size)
        prior = self._prior(method, problem)
        if emp is not None:
            return self.alpha * emp + (1 - self.alpha) * prior
        return prior

    def _prior(self, method: Method, problem: Problem) -> float:
        """Heuristic used before any real benchmark exists at this size —
        exact diagonalization dominates quantum methods' cost, renormalization
        pays off at scale, parallel replicas trade wall-clock for exploration."""
        base = float(problem.size ** 2)
        if method.quantum:
            base *= 8
        if method.name == "holographic_solve" and problem.size > 100:
            base *= 0.5
        if method.parallel:
            base *= 0.7
        return base

# ----------------------------------------------------------------------
# Problem analyzer
# ----------------------------------------------------------------------
def analyze_problem(description: str, size_hint: Optional[int] = None) -> Problem:
    desc = description.lower()
    if "factor" in desc:
        ptype = ProblemType.FACTORIZATION
    elif "sat" in desc or "satisfiab" in desc or "boolean" in desc:
        ptype = ProblemType.SAT
    elif "tsp" in desc or "traveling salesman" in desc or "travelling salesman" in desc:
        ptype = ProblemType.TSP
    elif "coloring" in desc or "colouring" in desc:
        ptype = ProblemType.GRAPH_COLORING
    else:
        ptype = ProblemType.OPTIMIZATION  # generic fallback — encode_optimization takes any cost_fn

    size = size_hint
    if size is None:
        digits = "".join(ch if ch.isdigit() else " " for ch in desc).split()
        size = int(digits[0]) if digits else 20
    return Problem(type=ptype, size=size)

# ----------------------------------------------------------------------
# LLM Interface Harness & Translator (Compact Grammar v2)
# ----------------------------------------------------------------------
class CompactGrammarV2:
    HELP_TEXT = "Commands: QUERY <target>, AUTO <problem description>, ACT <method> <problem description>, BENCH <method> <size>, RESET, HELP"

    @staticmethod
    def parse_command(line: str) -> Tuple[str, dict]:
        line = line.strip()
        if line.startswith("QUERY"):
            parts = line.split()
            if len(parts) == 2:
                return ("QUERY", {"target": parts[1]})
        elif line.startswith("AUTO"):
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                return ("AUTO", {"problem_desc": parts[1]})
        elif line.startswith("ACT"):
            parts = line.split(maxsplit=2)
            if len(parts) == 3:
                return ("ACT", {"method": parts[1], "problem_desc": parts[2]})
        elif line == "RESET":
            return ("RESET", {})
        elif line.startswith("BENCH"):
            parts = line.split()
            if len(parts) == 3:
                return ("BENCH", {"method": parts[1], "size": int(parts[2])})
        elif line == "HELP":
            return ("HELP", {})
        return ("ERROR", {"code": "4", "message": "syntax error"})

    @staticmethod
    def format_result(method: str, result: Dict) -> str:
        t = result.get("time")
        e = result.get("final_energy")
        t_str = f"{t:.3f}s" if t is not None else "n/a"
        e_str = f"{e:.4f}" if e is not None else "n/a"
        return f"RES {method} time={t_str} energy={e_str}"

    @staticmethod
    def format_error(code: str, msg: str) -> str:
        return f"ERR {code} {msg}"


class LLMInterfaceHarness:
    def __init__(self, selector, scorer, collector):
        self.selector = selector
        self.scorer = scorer
        self.collector = collector
        self.grammar = CompactGrammarV2()

    def process_nl(self, nl_query: str) -> str:
        """Convert natural language to compact command, execute, return compact result."""
        cmd = self._nl_to_command(nl_query)
        if cmd.startswith("ERROR"):
            return cmd
        return self.process_command(cmd)

    def _nl_to_command(self, nl: str) -> str:
        nl_lower = nl.lower()
        if "benchmark" in nl_lower:
            for m in METHODS:
                if m.name in nl_lower:
                    digits = "".join(ch if ch.isdigit() else " " for ch in nl_lower).split()
                    size = int(digits[0]) if digits else 20
                    return f"BENCH {m.name} {size}"
            return "ERROR 4 unknown method in benchmark request"
        if "select" in nl_lower or "choose" in nl_lower or "solve" in nl_lower:
            return f"AUTO {nl}"
        if "list methods" in nl_lower or nl_lower.strip() == "methods":
            return "QUERY all"
        if "help" in nl_lower:
            return "HELP"
        if "reset" in nl_lower:
            return "RESET"
        return "ERROR 4 unknown natural language"

    def process_command(self, cmd: str) -> str:
        cmd_type, args = self.grammar.parse_command(cmd)
        if cmd_type == "QUERY":
            return "METHODS: " + ", ".join(m.name for m in METHODS)
        elif cmd_type == "AUTO":
            problem = analyze_problem(args["problem_desc"])
            method, score = self.selector.select_method(problem)
            result = self.collector.run_benchmark(method, problem, quick=True)
            if result is None:
                return self.grammar.format_error("2", f"{method.name} not applicable to {problem.type.value} size={problem.size}")
            return f"AUTO {method.name} type={problem.type.value} size={problem.size} score={score:.2e} " + \
                   self.grammar.format_result(method.name, result)
        elif cmd_type == "ACT":
            method_name = args["method"]
            method = next((m for m in METHODS if m.name == method_name), None)
            if not method:
                return self.grammar.format_error("3", f"unknown method {method_name}")
            problem = analyze_problem(args["problem_desc"])
            result = self.collector.run_benchmark(method, problem, quick=True)
            if result is None:
                return self.grammar.format_error("2", f"{method_name} not applicable to {problem.type.value} size={problem.size}")
            return self.grammar.format_result(method.name, result)
        elif cmd_type == "BENCH":
            method_name = args["method"]
            size = args["size"]
            method = next((m for m in METHODS if m.name == method_name), None)
            if not method:
                return self.grammar.format_error("3", f"unknown method {method_name}")
            problem = Problem(type=method.applicable_types[0], size=size)
            result = self.collector.run_benchmark(method, problem, quick=True)
            if result is None:
                return self.grammar.format_error("2", f"{method_name} not applicable at size={size}")
            return f"BENCH DONE {method_name} type={problem.type.value} size={size} " + \
                   self.grammar.format_result(method.name, result)
        elif cmd_type == "RESET":
            self.collector.load()
            return "RESET OK"
        elif cmd_type == "HELP":
            return self.grammar.HELP_TEXT
        else:
            return self.grammar.format_error("4", "unknown command")

# ----------------------------------------------------------------------
# Adaptive Selector (main API)
# ----------------------------------------------------------------------
class AdaptiveGeometricSelector:
    def __init__(self):
        self.collector = BenchmarkCollector()
        self.scorer = AdaptiveScorer(self.collector)
        self.llm = LLMInterfaceHarness(self, self.scorer, self.collector)

    def select_method(self, problem: Problem) -> Tuple[Method, float]:
        best_method = None
        best_score = float('inf')
        for method in METHODS:
            if problem.type not in method.applicable_types:
                continue
            if not (method.min_size <= problem.size <= method.max_size):
                continue
            score = self.scorer.score(method, problem)
            if score < best_score:
                best_score = score
                best_method = method
        if best_method is None:
            # simulated_annealing has no size/type restriction, so it's
            # always a valid classical fallback.
            best_method = next(m for m in METHODS if m.name == "simulated_annealing")
        return best_method, best_score

    def solve(self, description: str, size_hint: Optional[int] = None, quick: bool = True) -> Dict:
        problem = analyze_problem(description, size_hint)
        method, score = self.select_method(problem)
        print(f"Selected {method.name} for {description!r} "
              f"(type={problem.type.value}, size={problem.size}, score={score:.2e})")
        result = self.collector.run_benchmark(method, problem, quick=quick)
        return {"method": method.name, "problem": problem, "result": result}

    def interact_llm(self, nl_query: str) -> str:
        return self.llm.process_nl(nl_query)

# ----------------------------------------------------------------------
# Demo
# ----------------------------------------------------------------------
if __name__ == "__main__":
    selector = AdaptiveGeometricSelector()

    print("=== LLM Interface ===")
    print(selector.interact_llm("Solve factorization of size 91"))
    print(selector.interact_llm("benchmark simulated_annealing size 50"))
    print(selector.interact_llm("list methods"))

    print("\n=== Adaptive Scoring Demo ===")
    prob = Problem(type=ProblemType.OPTIMIZATION, size=30)
    method, score = selector.select_method(prob)
    print(f"Selected {method.name} with score {score:.2e}")

    print("\n=== BloomCube3D sanity check (no engine counterpart yet) ===")
    bc = BloomCube3D()
    bc.add((1, 2, 3, 4, 5, 6), "relation_0")
    print("query same relation:", bc.query((1, 2, 3, 4, 5, 6), "relation_0"))
