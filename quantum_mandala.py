"""
QUANTUM MANDALA COMPUTING v2.0
Superposition of Octahedral States in 8-Dimensional Hilbert Space

The classical mandala relaxes through thermal fluctuations.
The quantum mandala explores ALL paths simultaneously through superposition.

Key insight: 8 octahedral states -> 8-dimensional quantum state space
Each cell becomes a qubit-octit (8-level quantum system)

v2.0: JSON layer wiring, QAOA, sensor telemetry, introspection
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import time
import json
import pathlib
import math

PHI = (1 + np.sqrt(5)) / 2

# ---------------------------------------------------------------------------
# JSON Layer
# ---------------------------------------------------------------------------

_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_STATE_GLYPHS = ["\u2295", "\u2296", "\u2297", "\u2298", "\u2299", "\u229a", "\u229b", "\u229c"]

try:
    with open(_SCRIPT_DIR / "glyphs" / "mandala.json") as _f:
        _GLYPH_DATA = json.load(_f)
        _loaded = [g["unicode"] for g in _GLYPH_DATA.get("octahedral_state_glyphs", [])]
        if _loaded:
            _STATE_GLYPHS = _loaded
except (FileNotFoundError, json.JSONDecodeError, KeyError):
    _GLYPH_DATA = None

# Pauli matrices for 2-level systems
PAULI_X = np.array([[0, 1], [1, 0]], dtype=complex)
PAULI_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
PAULI_Z = np.array([[1, 0], [0, -1]], dtype=complex)
IDENTITY_2 = np.eye(2, dtype=complex)

FRET_CUTOFF = 3.0 * PHI


# ---------------------------------------------------------------------------
# Quantum cell
# ---------------------------------------------------------------------------

class QuantumMandalaCell:
    """
    Quantum cell with 8-level octahedral state space.

    State vector |psi> in C^8 (8-dimensional Hilbert space).
    Basis states correspond to octahedral vertices: |0> .. |7>.
    """

    def __init__(self, position: Tuple[float, float], depth: int):
        self.position = position
        self.depth = depth
        # Equal superposition: |psi> = (|0> + |1> + ... + |7>) / sqrt(8)
        self.state_vector = np.ones(8, dtype=complex) / np.sqrt(8)
        self.neighbors: List[int] = []
        self.geometric_phase = 0.0

    def get_probability_distribution(self) -> np.ndarray:
        """P(state i) = |alpha_i|^2"""
        return np.abs(self.state_vector) ** 2

    def measure(self) -> int:
        """Quantum measurement - collapses to one of 8 states."""
        probs = self.get_probability_distribution()
        measured = np.random.choice(8, p=probs)
        self.state_vector = np.zeros(8, dtype=complex)
        self.state_vector[measured] = 1.0
        return measured

    def apply_unitary(self, U: np.ndarray):
        """Apply unitary transformation: |psi'> = U|psi>."""
        self.state_vector = U @ self.state_vector
        norm = np.linalg.norm(self.state_vector)
        if abs(norm - 1.0) > 1e-10:
            self.state_vector /= norm


# ---------------------------------------------------------------------------
# Quantum Mandala Computer
# ---------------------------------------------------------------------------

class QuantumMandalaComputer:
    """
    Quantum extension of Mandala Computing.

    Uses superposition and entanglement to explore solution space
    exponentially faster than classical geometric relaxation.
    """

    def __init__(self,
                 golden_depth: int = 4,
                 sacred_geometry: int = 8,
                 entanglement_strength: float = 0.1):
        self.golden_depth = golden_depth
        self.sacred_geometry = sacred_geometry
        self.entanglement_strength = entanglement_strength

        self.cells: List[QuantumMandalaCell] = []
        self.num_cells = 0

        self.hamiltonian = None

        # Telemetry
        self.telemetry: List[Dict] = []
        self.energy_history: List[float] = []

        print(f"Quantum Mandala Computer initialized")
        print(f"   Depth: {golden_depth}, Hilbert dim: {sacred_geometry}")
        print(f"   Entanglement: {entanglement_strength}")

    # ------------------------------------------------------------------
    # Bloom
    # ------------------------------------------------------------------

    def bloom_quantum_mandala(self):
        """Create quantum mandala with cells in superposition."""
        self.cells = []
        for depth in range(self.golden_depth):
            n = int(PHI ** (depth + 1))
            radius = PHI ** depth
            for i in range(n):
                angle = 2 * np.pi * i / n
                cell = QuantumMandalaCell(
                    position=(radius * np.cos(angle), radius * np.sin(angle)),
                    depth=depth,
                )
                self.cells.append(cell)
        self.num_cells = len(self.cells)
        self._establish_entanglement()
        print(f"   Created {self.num_cells} quantum cells")
        print(f"   Total Hilbert space: 8^{self.num_cells} = {8 ** self.num_cells}")

    def _establish_entanglement(self):
        """Create entanglement topology between nearby cells."""
        for i, ci in enumerate(self.cells):
            for j, cj in enumerate(self.cells):
                if i >= j:
                    continue
                dx = ci.position[0] - cj.position[0]
                dy = ci.position[1] - cj.position[1]
                dist = math.sqrt(dx * dx + dy * dy)
                if 0 < dist < FRET_CUTOFF:
                    ci.neighbors.append(j)
                    cj.neighbors.append(i)

    # ------------------------------------------------------------------
    # Telemetry
    # ------------------------------------------------------------------

    def _emit_sensor(self, sensor_id: str, step: int, value, metadata: dict = None):
        self.telemetry.append({
            "sensor_id": sensor_id,
            "timestamp_step": step,
            "value": value,
            "metadata": metadata or {},
        })

    # ------------------------------------------------------------------
    # Operators
    # ------------------------------------------------------------------

    def _build_octahedral_rotation(self, angle: float, axis: int) -> np.ndarray:
        """Build 8x8 unitary rotation via block-diagonal 2x2 rotations."""
        U = np.zeros((8, 8), dtype=complex)
        for block in range(4):
            phi_offset = block * np.pi / 4
            c = np.cos(angle / 2 + phi_offset)
            s = np.sin(angle / 2 + phi_offset)
            R = np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)
            U[2 * block:2 * block + 2, 2 * block:2 * block + 2] = R
        return U

    def _build_hamiltonian(self, problem_type: str, problem_data: Dict) -> np.ndarray:
        if problem_type == "factorization":
            return self._build_factorization_hamiltonian(problem_data)
        elif problem_type == "optimization":
            return self._build_optimization_hamiltonian(problem_data)
        raise ValueError(f"Unknown problem type: {problem_type}")

    def _build_factorization_hamiltonian(self, data: Dict) -> np.ndarray:
        """
        Hamiltonian for factorization.
        Two-cell system: 8x8 = 64-dimensional space.
        Energy -1 for correct factor pairs, +1 otherwise.
        """
        N = data["N"]
        dim = 64
        H = np.zeros((dim, dim), dtype=complex)
        for i in range(8):
            for j in range(8):
                fa, fb = 2 + i, 2 + j
                idx = i * 8 + j
                H[idx, idx] = -1.0 if fa * fb == N else 1.0
        return H

    def _build_optimization_hamiltonian(self, data: Dict) -> np.ndarray:
        """Generic optimization Hamiltonian (random Hermitian for demo)."""
        dim = 8
        H = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        return (H + H.conj().T) / 2

    def _matrix_exponential(self, M: np.ndarray) -> np.ndarray:
        """Matrix exponential via scipy or Taylor series fallback."""
        if M.shape[0] <= 64:
            from scipy.linalg import expm
            return expm(M)
        result = np.eye(M.shape[0], dtype=complex)
        term = np.eye(M.shape[0], dtype=complex)
        for k in range(1, 12):
            term = term @ M / k
            result += term
        return result

    # ------------------------------------------------------------------
    # Quantum annealing
    # ------------------------------------------------------------------

    def quantum_annealing(self, problem_type: str, problem_data: Dict,
                          num_steps: int = 100) -> Dict:
        """
        Adiabatic evolution: H(t) = (1-s)H_initial + s*H_problem.
        Adiabatic theorem guarantees ground-state tracking if slow enough.
        """
        print(f"\n   Quantum annealing: {problem_type}, {num_steps} steps")
        H_problem = self._build_hamiltonian(problem_type, problem_data)
        dim = H_problem.shape[0]
        H_initial = -np.ones((dim, dim), dtype=complex) / dim
        state = np.ones(dim, dtype=complex) / np.sqrt(dim)

        for step in range(num_steps):
            s = step / max(num_steps - 1, 1)
            H = (1 - s) * H_initial + s * H_problem
            dt = 0.1
            U = self._matrix_exponential(-1j * H * dt)
            state = U @ state
            state /= np.linalg.norm(state)

            if step % 20 == 0:
                energy = float(np.real(state.conj() @ H_problem @ state))
                fidelity = float(np.max(np.abs(state) ** 2))
                self._emit_sensor("energy.total", step, energy)
                self._emit_sensor("quantum.fidelity", step, fidelity)
                self.energy_history.append(energy)
                print(f"   Step {step:>4d}: E={energy:.4f}  fidelity={fidelity:.4f}")

        probabilities = np.abs(state) ** 2
        measured_state = np.random.choice(dim, p=probabilities)
        final_energy = float(np.real(state.conj() @ H_problem @ state))
        solution = self._extract_quantum_solution(measured_state, problem_type, problem_data)
        print(f"   Final energy: {final_energy:.4f}")
        return {
            "measured_state": measured_state,
            "final_energy": final_energy,
            "state_vector": state,
            "solution": solution,
        }

    # ------------------------------------------------------------------
    # Grover search
    # ------------------------------------------------------------------

    def grover_search(self, oracle, num_iterations: int = None) -> int:
        """
        Grover's quantum search on 8-state space.
        Finds solution in O(sqrt(N)) instead of O(N).
        """
        N = 8
        if num_iterations is None:
            num_iterations = int(np.pi * np.sqrt(N) / 4)
        print(f"\n   Grover search: {N} states, {num_iterations} iterations")

        state = np.ones(N, dtype=complex) / np.sqrt(N)
        for _ in range(num_iterations):
            for i in range(N):
                if oracle(i):
                    state[i] *= -1
            avg = np.mean(state)
            state = 2 * avg - state

        probs = np.abs(state) ** 2
        print("   Probabilities:")
        for i, p in enumerate(probs):
            g = _STATE_GLYPHS[i] if i < len(_STATE_GLYPHS) else str(i)
            print(f"      {g} State {i}: {p:.4f}")

        measured = np.random.choice(N, p=probs)
        print(f"   Measured: {measured} (solution: {oracle(measured)})")
        return measured

    # ------------------------------------------------------------------
    # QAOA
    # ------------------------------------------------------------------

    def qaoa(self, problem_type: str, problem_data: Dict,
             num_layers: int = 3, num_samples: int = 50) -> Dict:
        """
        Quantum Approximate Optimization Algorithm.
        Alternates problem and mixer unitaries with random parameter search.
        """
        print(f"\n   QAOA: {num_layers} layers, {num_samples} samples")
        H_problem = self._build_hamiltonian(problem_type, problem_data)
        dim = H_problem.shape[0]

        # Mixer: sum of single-qubit X operators
        H_mixer = np.zeros((dim, dim), dtype=complex)
        for i in range(dim):
            for j in range(dim):
                if bin(i ^ j).count("1") == 1:
                    H_mixer[i, j] = 1.0

        best_energy = float("inf")
        best_state = None
        best_params = None

        for sample in range(num_samples):
            gammas = np.random.uniform(0, 2 * np.pi, num_layers)
            betas = np.random.uniform(0, np.pi, num_layers)
            state = np.ones(dim, dtype=complex) / np.sqrt(dim)

            for layer in range(num_layers):
                U_p = self._matrix_exponential(-1j * gammas[layer] * H_problem)
                state = U_p @ state
                U_m = self._matrix_exponential(-1j * betas[layer] * H_mixer)
                state = U_m @ state

            state /= np.linalg.norm(state)
            energy = float(np.real(state.conj() @ H_problem @ state))

            if energy < best_energy:
                best_energy = energy
                best_state = state.copy()
                best_params = (gammas.copy(), betas.copy())

            if sample % 10 == 0:
                self._emit_sensor("energy.total", sample, best_energy)
                self.energy_history.append(best_energy)
                print(f"   Sample {sample:>3d}: best E={best_energy:.4f}")

        probs = np.abs(best_state) ** 2
        measured = np.random.choice(dim, p=probs)
        solution = self._extract_quantum_solution(measured, problem_type, problem_data)
        print(f"   QAOA best energy: {best_energy:.4f}")
        return {
            "measured_state": measured,
            "final_energy": best_energy,
            "state_vector": best_state,
            "solution": solution,
            "params": best_params,
        }

    # ------------------------------------------------------------------
    # Solution extraction
    # ------------------------------------------------------------------

    def _extract_quantum_solution(self, measured_state: int,
                                  problem_type: str, problem_data: Dict) -> Dict:
        if problem_type == "factorization":
            N = problem_data["N"]
            i = measured_state // 8
            j = measured_state % 8
            fa, fb = 2 + i, 2 + j
            return {"factors": [fa, fb], "product": fa * fb, "correct": fa * fb == N}
        return {"state": measured_state}

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_probability_landscape(self) -> List[np.ndarray]:
        """Probability distributions for all cells."""
        return [c.get_probability_distribution() for c in self.cells]

    def get_entanglement_entropy(self, cell_idx: int) -> float:
        """Shannon entropy of cell's probability distribution (proxy for entanglement)."""
        probs = self.cells[cell_idx].get_probability_distribution()
        nz = probs[probs > 1e-15]
        return float(-np.sum(nz * np.log2(nz)))

    def glyph_trace(self, num_cells: int = None) -> str:
        """Show dominant state of each cell as glyphs."""
        cells = self.cells[:num_cells] if num_cells else self.cells
        parts = []
        for c in cells:
            dominant = int(np.argmax(c.get_probability_distribution()))
            g = _STATE_GLYPHS[dominant] if dominant < len(_STATE_GLYPHS) else str(dominant)
            parts.append(g)
        return " ".join(parts)


# ============================================================================
# DEMONSTRATIONS
# ============================================================================

def demo_quantum_factorization():
    """Quantum factorization via annealing."""
    print("=" * 60)
    print("QUANTUM DEMO: FACTORIZATION VIA ANNEALING")
    print("=" * 60)
    N = 15
    qc = QuantumMandalaComputer(golden_depth=2, sacred_geometry=8, entanglement_strength=0.1)
    result = qc.quantum_annealing("factorization", {"N": N}, num_steps=100)
    sol = result["solution"]
    print(f"\n   N={N}, factors={sol['factors']}, product={sol['product']}, correct={sol['correct']}")
    print(f"   Telemetry: {len(qc.telemetry)} readings")
    return result


def demo_grover_search():
    """Grover's algorithm for quantum search."""
    print("\n" + "=" * 60)
    print("QUANTUM DEMO: GROVER SEARCH")
    print("=" * 60)
    target = 5
    qc = QuantumMandalaComputer(golden_depth=1, sacred_geometry=8)
    print(f"   Target: {target}, classical O(8), quantum O(sqrt(8))~3")
    measured = qc.grover_search(lambda x: x == target)
    return measured


def demo_quantum_superposition():
    """Octahedral superposition demo."""
    print("\n" + "=" * 60)
    print("QUANTUM DEMO: OCTAHEDRAL SUPERPOSITION")
    print("=" * 60)
    cell = QuantumMandalaCell(position=(0, 0), depth=0)
    print("   Initial: equal superposition of 8 states")
    probs = cell.get_probability_distribution()
    for i, p in enumerate(probs):
        g = _STATE_GLYPHS[i] if i < len(_STATE_GLYPHS) else str(i)
        print(f"      {g} |{i}>: {p:.4f}")

    U = np.eye(8, dtype=complex)
    U = np.roll(U, 1, axis=1)
    cell.apply_unitary(U)
    measured = cell.measure()
    g = _STATE_GLYPHS[measured] if measured < len(_STATE_GLYPHS) else str(measured)
    print(f"   After rotation + measurement: collapsed to {g} |{measured}>")
    return cell


def demo_qaoa():
    """QAOA for quantum optimization."""
    print("\n" + "=" * 60)
    print("QUANTUM DEMO: QAOA OPTIMIZATION")
    print("=" * 60)
    N = 15
    qc = QuantumMandalaComputer(golden_depth=2, sacred_geometry=8, entanglement_strength=0.1)
    qc.bloom_quantum_mandala()
    result = qc.qaoa("factorization", {"N": N}, num_layers=3, num_samples=30)
    sol = result["solution"]
    print(f"\n   N={N}, factors={sol['factors']}, correct={sol['correct']}")
    print(f"   Telemetry: {len(qc.telemetry)} readings")
    print(f"   Glyph trace: {qc.glyph_trace()}")
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("QUANTUM MANDALA COMPUTING v2.0")
    print("   Superposition of Octahedral States")
    print("=" * 60)

    demo_quantum_factorization()
    demo_grover_search()
    demo_quantum_superposition()
    demo_qaoa()

    print("\n" + "=" * 60)
    print("ALL QUANTUM DEMONSTRATIONS COMPLETE")
    print("=" * 60)
