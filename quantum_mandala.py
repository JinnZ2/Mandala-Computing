"""
QUANTUM MANDALA COMPUTING v2.0
Superposition of Octahedral States in 8-Dimensional Hilbert Space

The classical mandala relaxes through thermal fluctuations.
The quantum mandala explores ALL paths simultaneously through superposition.

Key insight: 8 octahedral states -> 8-dimensional quantum state space
Each cell becomes a qubit-octit (8-level quantum system)

v2.0: JSON layer wiring, QAOA, sensor telemetry, introspection
"""

from __future__ import annotations

import numpy as np
from typing import List, Tuple, Dict
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
        Hamiltonian for factorization with expanded factor mapping.

        Two-cell system: 8x8 = 64-dimensional space.
        Factor mapping scales based on N:
          - N <= 81: fa = 2+i, fb = 2+j (range [2..9])
          - N > 81:  fa = 2 + i*stride, fb = 2 + j*stride
            where stride = ceil(sqrt(N)/8) to cover the factor range

        Energy = -(1 / (1 + (fa*fb - N)^2)) so ground state is sharpest
        at exact factorization, with smooth gradient toward it.
        """
        N = data["N"]
        dim = 64
        max_factor = int(math.isqrt(N)) + 1
        # Stride: how much each state increment represents
        stride = max(1, math.ceil(max_factor / 8))

        H = np.zeros((dim, dim), dtype=complex)
        for i in range(8):
            for j in range(8):
                fa = 2 + i * stride
                fb = 2 + j * stride
                idx = i * 8 + j
                residual = (fa * fb - N) ** 2
                # Smooth energy: -1 at solution, approaches +1 far away
                H[idx, idx] = 1.0 - 2.0 / (1.0 + residual)
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
    # Multi-cell tensor product Hamiltonian
    # ------------------------------------------------------------------

    def _build_multicell_hamiltonian(self, num_cells: int, problem_type: str,
                                     problem_data: Dict) -> np.ndarray:
        """
        Build Hamiltonian over tensor product of multiple 8-dim cells.

        For num_cells cells, Hilbert space is 8^num_cells dimensional.
        Includes local terms + nearest-neighbor coupling.

        Practical limit: num_cells <= 3 (8^3 = 512 dim) for exact computation.
        """
        d = 8  # single-cell dimension
        dim = d ** num_cells
        H = np.zeros((dim, dim), dtype=complex)

        # Local terms: encode problem on each cell
        if problem_type == "factorization":
            N = problem_data["N"]
            # For 2+ cells, pair them as factor candidates
            for cell_idx in range(0, num_cells - 1, 2):
                for state_a in range(d):
                    for state_b in range(d):
                        fa = 2 + state_a
                        fb = 2 + state_b
                        penalty = (fa * fb - N) ** 2
                        # Apply to all basis states where cell_idx has state_a
                        # and cell_idx+1 has state_b
                        for basis in range(dim):
                            digits = self._basis_to_states(basis, num_cells, d)
                            if digits[cell_idx] == state_a and digits[cell_idx + 1] == state_b:
                                H[basis, basis] += penalty

        # Inter-cell coupling: ZZ-like interaction on neighbors
        for c in range(num_cells - 1):
            for basis in range(dim):
                digits = self._basis_to_states(basis, num_cells, d)
                diff = abs(digits[c] - digits[c + 1])
                coupling = self.entanglement_strength * math.sin(diff * math.pi / 4) ** 2
                H[basis, basis] += coupling

        # Off-diagonal: single-cell transitions (X-like mixing)
        for c in range(num_cells):
            for basis in range(dim):
                digits = self._basis_to_states(basis, num_cells, d)
                for new_s in range(d):
                    if new_s != digits[c]:
                        new_digits = list(digits)
                        new_digits[c] = new_s
                        new_basis = self._states_to_basis(new_digits, d)
                        H[basis, new_basis] += -0.01  # small mixing

        return H

    @staticmethod
    def _basis_to_states(basis: int, num_cells: int, d: int) -> List[int]:
        """Convert basis index to per-cell state tuple."""
        digits = []
        for _ in range(num_cells):
            digits.append(basis % d)
            basis //= d
        return digits

    @staticmethod
    def _states_to_basis(states: List[int], d: int) -> int:
        """Convert per-cell states to basis index."""
        idx = 0
        for i, s in enumerate(states):
            idx += s * (d ** i)
        return idx

    def entangled_annealing(self, problem_type: str, problem_data: Dict,
                            num_cells: int = 2, num_steps: int = 100) -> Dict:
        """
        Quantum annealing over entangled multi-cell Hilbert space.

        Evolves the full 8^num_cells dimensional state vector,
        including inter-cell entanglement through coupling terms.
        """
        dim = 8 ** num_cells
        print(f"\n   Entangled annealing: {num_cells} cells, dim={dim}, {num_steps} steps")

        H_problem = self._build_multicell_hamiltonian(num_cells, problem_type, problem_data)
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
                # Compute entanglement entropy via reduced density matrix
                ent_entropy = self._compute_entanglement_entropy(state, num_cells)
                self._emit_sensor("energy.total", step, energy)
                self._emit_sensor("quantum.fidelity", step, fidelity)
                self._emit_sensor("quantum.entanglement", step, ent_entropy)
                self.energy_history.append(energy)
                print(f"   Step {step:>4d}: E={energy:.4f}  fidelity={fidelity:.4f}  S_ent={ent_entropy:.3f}")

        probs = np.abs(state) ** 2
        measured = np.random.choice(dim, p=probs)
        digits = self._basis_to_states(measured, num_cells, 8)
        final_energy = float(np.real(state.conj() @ H_problem @ state))

        solution = self._extract_quantum_solution(measured, problem_type, problem_data)
        solution["cell_states"] = digits
        print(f"   Final: E={final_energy:.4f}, states={digits}")
        return {
            "measured_state": measured,
            "cell_states": digits,
            "final_energy": final_energy,
            "state_vector": state,
            "solution": solution,
        }

    def _compute_entanglement_entropy(self, state: np.ndarray, num_cells: int) -> float:
        """
        Compute entanglement entropy between first cell and the rest.
        Traces out all cells except the first to get reduced density matrix.
        """
        d = 8
        dim_a = d  # first cell
        dim_b = d ** (num_cells - 1)  # rest
        psi = state.reshape(dim_b, dim_a)
        rho_a = psi.conj().T @ psi
        eigvals = np.linalg.eigvalsh(rho_a)
        eigvals = eigvals[eigvals > 1e-15]
        if len(eigvals) == 0:
            return 0.0
        return float(-np.sum(eigvals * np.log2(eigvals)))

    # ------------------------------------------------------------------
    # FRET dipolar coupling (XX + YY terms)
    # ------------------------------------------------------------------

    def _build_fret_coupling(self, num_cells: int, coupling_strengths: Dict[Tuple[int, int], float] = None) -> np.ndarray:
        """
        Build FRET dipolar coupling Hamiltonian with XX + YY terms.

        Unlike ZZ coupling (diagonal, classical-like), XX+YY coupling
        enables excitation hopping between cells — the quantum signature
        of dipole-dipole interaction.

        For octahedral states 0-7, we generalize the 2-level XX+YY:
          H_FRET = J * sum_{s != s'} (|s,s'><s',s| + h.c.)

        This means: if cell A is in state s and cell B in state s',
        they can swap excitations with amplitude J.

        In biological FRET, this is how a photon absorbed by one
        chromophore hops to a neighbor without re-emission.
        """
        d = 8
        dim = d ** num_cells

        if coupling_strengths is None:
            # Default: nearest-neighbor chain with FRET-like distance decay
            coupling_strengths = {}
            for c in range(num_cells - 1):
                coupling_strengths[(c, c + 1)] = self.entanglement_strength

        H_fret = np.zeros((dim, dim), dtype=complex)

        for (cell_a, cell_b), J in coupling_strengths.items():
            if cell_a >= num_cells or cell_b >= num_cells:
                continue
            # For each pair of states (s, s'), add hopping term
            for basis in range(dim):
                digits = self._basis_to_states(basis, num_cells, d)
                sa = digits[cell_a]
                sb = digits[cell_b]
                if sa != sb:
                    # Swap excitation: |..sa..sb..> -> |..sb..sa..>
                    new_digits = list(digits)
                    new_digits[cell_a] = sb
                    new_digits[cell_b] = sa
                    new_basis = self._states_to_basis(new_digits, d)
                    # Coupling weighted by geometric proximity of states
                    # States that are adjacent on the octahedron couple more
                    state_dist = min(abs(sa - sb), d - abs(sa - sb))
                    fret_weight = J / (1.0 + state_dist)
                    H_fret[basis, new_basis] += fret_weight

        return H_fret

    # ------------------------------------------------------------------
    # Lindblad noise channels (open quantum system)
    # ------------------------------------------------------------------

    def _build_lindblad_operators(self, num_cells: int,
                                  gamma_decay: float = 0.01,
                                  gamma_dephase: float = 0.05) -> List[np.ndarray]:
        """
        Build Lindblad collapse operators for open-system dynamics.

        Two noise channels per cell:
        1. Decay (gamma_decay): excitation loss to environment
           L_decay = sqrt(gamma) * |0><s| for each excited state s>0
           Models spontaneous emission, thermal relaxation.

        2. Dephasing (gamma_dephase): pure phase noise
           L_dephase = sqrt(gamma) * |s><s| (diagonal, no population change)
           Models elastic collisions with thermal bath.

        At room temperature, dephasing >> decay (thermal fluctuations
        scramble phase faster than they drain energy).
        """
        d = 8
        dim = d ** num_cells
        collapse_ops = []

        for cell in range(num_cells):
            # Decay: excited states relax toward ground
            if gamma_decay > 0:
                for excited in range(1, d):
                    L = np.zeros((dim, dim), dtype=complex)
                    for basis in range(dim):
                        digits = self._basis_to_states(basis, num_cells, d)
                        if digits[cell] == excited:
                            new_digits = list(digits)
                            new_digits[cell] = 0  # decay to ground
                            new_basis = self._states_to_basis(new_digits, d)
                            L[new_basis, basis] = np.sqrt(gamma_decay)
                    collapse_ops.append(L)

            # Dephasing: diagonal noise (phase scrambling)
            if gamma_dephase > 0:
                for state in range(d):
                    L = np.zeros((dim, dim), dtype=complex)
                    for basis in range(dim):
                        digits = self._basis_to_states(basis, num_cells, d)
                        if digits[cell] == state:
                            L[basis, basis] = np.sqrt(gamma_dephase)
                    collapse_ops.append(L)

        return collapse_ops

    def _lindblad_step(self, rho: np.ndarray, H: np.ndarray,
                       collapse_ops: List[np.ndarray], dt: float) -> np.ndarray:
        """
        Single Lindblad master equation step (first-order Euler).

        drho/dt = -i[H, rho] + sum_k (L_k rho L_k^dag - 0.5 {L_k^dag L_k, rho})

        This is the standard open quantum system evolution:
        - First term: unitary (Hamiltonian) evolution
        - Second term: dissipation from environment coupling

        The noise is not a bug — it's the thermal bath that makes
        room-temperature quantum effects possible.
        """
        # Unitary part: -i[H, rho]
        drho = -1j * (H @ rho - rho @ H)

        # Dissipative part: Lindblad terms
        for L in collapse_ops:
            Ldag = L.conj().T
            LdagL = Ldag @ L
            drho += L @ rho @ Ldag - 0.5 * (LdagL @ rho + rho @ LdagL)

        rho_new = rho + dt * drho

        # Ensure hermiticity
        rho_new = (rho_new + rho_new.conj().T) / 2

        # Ensure positivity: clamp negative eigenvalues
        eigvals, eigvecs = np.linalg.eigh(rho_new)
        eigvals = np.maximum(eigvals, 0)
        rho_new = (eigvecs * eigvals) @ eigvecs.conj().T

        # Ensure trace = 1
        tr = np.trace(rho_new).real
        if tr > 1e-15:
            rho_new /= tr
        else:
            # Reset to maximally mixed if trace collapsed
            rho_new = np.eye(rho.shape[0], dtype=complex) / rho.shape[0]

        return rho_new

    def _pairwise_coherence(self, rho: np.ndarray, num_cells: int,
                            cell_a: int, cell_b: int) -> float:
        """
        Measure quantum coherence between two cells.

        Traces out all other cells, then measures the magnitude of
        off-diagonal elements in the reduced 2-cell density matrix.

        High coherence = the cells are quantum-correlated.
        Zero coherence = classically independent.
        """
        d = 8
        dim = d ** num_cells
        dim_ab = d * d  # reduced space for cells a and b

        # Build reduced density matrix for cells (a, b)
        rho_ab = np.zeros((dim_ab, dim_ab), dtype=complex)

        for i in range(dim):
            for j in range(dim):
                if abs(rho[i, j]) < 1e-15:
                    continue
                di = self._basis_to_states(i, num_cells, d)
                dj = self._basis_to_states(j, num_cells, d)

                # Check if all OTHER cells match (partial trace condition)
                match = True
                for c in range(num_cells):
                    if c != cell_a and c != cell_b:
                        if di[c] != dj[c]:
                            match = False
                            break
                if not match:
                    continue

                # Map to reduced indices
                ri = di[cell_a] * d + di[cell_b]
                rj = dj[cell_a] * d + dj[cell_b]
                rho_ab[ri, rj] += rho[i, j]

        # Coherence = sum of |off-diagonal| elements (l1-norm of coherence)
        coherence = 0.0
        for i in range(dim_ab):
            for j in range(dim_ab):
                if i != j:
                    coherence += abs(rho_ab[i, j])

        return coherence

    # ------------------------------------------------------------------
    # Thermal bridge: phonon-assisted energy transfer
    # ------------------------------------------------------------------

    def thermal_bridge_evolution(self, problem_type: str, problem_data: Dict,
                                 num_cells: int = 2, num_steps: int = 100,
                                 gamma_decay: float = 0.01,
                                 gamma_dephase: float = 0.05,
                                 bridge_strength: float = 0.1) -> Dict:
        """
        Open-system quantum evolution with thermal bridge.

        The thermal bridge is the key insight from biological FRET:
        noise doesn't just destroy coherence — it can HELP energy
        transfer across energy gaps that pure unitary evolution can't
        bridge efficiently.

        The mechanism:
        1. Build problem Hamiltonian (unitary dynamics)
        2. Add FRET dipolar coupling (excitation hopping)
        3. Add Lindblad noise (thermal bath interaction)
        4. The noise fills in the energy gap between mismatched cells,
           acting as a "lubricant" for quantum state transfer

        This is how photosynthesis works: the protein scaffold provides
        thermal vibrations (phonons) tuned to match energy gaps between
        chlorophyll molecules, enabling near-perfect energy transfer
        at room temperature.

        Returns dict with evolution history: energy, coherence, entropy.
        """
        d = 8
        dim = d ** num_cells
        dt = 0.1

        print(f"\n   Thermal bridge evolution: {num_cells} cells, dim={dim}")
        print(f"   Noise: decay={gamma_decay}, dephase={gamma_dephase}")
        print(f"   Bridge coupling: {bridge_strength}")

        # Build Hamiltonian with FRET coupling
        H_problem = self._build_multicell_hamiltonian(num_cells, problem_type, problem_data)
        H_fret = self._build_fret_coupling(num_cells)
        H_total = H_problem + bridge_strength * H_fret

        # Build Lindblad operators
        collapse_ops = self._build_lindblad_operators(
            num_cells, gamma_decay=gamma_decay, gamma_dephase=gamma_dephase
        )

        # Initial state: first cell excited, rest ground
        # As density matrix (mixed state from the start)
        psi0 = np.zeros(dim, dtype=complex)
        initial_digits = [0] * num_cells
        initial_digits[0] = 1  # first cell in state |1>
        psi0[self._states_to_basis(initial_digits, d)] = 1.0
        rho = np.outer(psi0, psi0.conj())

        # Evolution with telemetry
        history = {
            "energy": [],
            "coherence_01": [],
            "entropy": [],
            "populations": [[] for _ in range(num_cells)],
        }

        for step in range(num_steps):
            # Interpolate: ramp up problem Hamiltonian
            s = min(step / max(num_steps // 2, 1), 1.0)
            H_initial = -np.ones((dim, dim), dtype=complex) / dim
            H = (1 - s) * H_initial + s * H_total

            rho = self._lindblad_step(rho, H, collapse_ops, dt)

            if step % 10 == 0:
                energy = float(np.real(np.trace(H_problem @ rho)))
                entropy = self._density_matrix_entropy(rho)
                coherence = self._pairwise_coherence(rho, num_cells, 0, min(1, num_cells - 1))

                # Per-cell populations
                for c in range(num_cells):
                    pop = self._cell_population(rho, num_cells, c)
                    history["populations"][c].append(pop)

                history["energy"].append(energy)
                history["coherence_01"].append(coherence)
                history["entropy"].append(entropy)

                self._emit_sensor("thermal_bridge.energy", step, energy)
                self._emit_sensor("thermal_bridge.coherence", step, coherence)
                self._emit_sensor("thermal_bridge.entropy", step, entropy)

                if step % 50 == 0:
                    print(f"   Step {step:>4d}: E={energy:.4f}  "
                          f"coh={coherence:.4f}  S={entropy:.3f}")

        # Final measurement
        probs = np.real(np.diag(rho))
        probs = np.maximum(probs, 0)
        probs /= probs.sum()
        measured = np.random.choice(dim, p=probs)
        digits = self._basis_to_states(measured, num_cells, d)

        solution = self._extract_quantum_solution(measured, problem_type, problem_data)
        solution["cell_states"] = digits

        final_coherence = history["coherence_01"][-1] if history["coherence_01"] else 0
        final_entropy = history["entropy"][-1] if history["entropy"] else 0

        print(f"   Final: states={digits}, coherence={final_coherence:.4f}, "
              f"entropy={final_entropy:.3f}")

        if final_coherence > 0.01:
            print(f"   >>> THERMAL BRIDGE ACTIVE: Coherence sustained with noise")
        else:
            print(f"   >>> Coherence decayed (try stronger bridge coupling)")

        return {
            "measured_state": measured,
            "cell_states": digits,
            "solution": solution,
            "history": history,
            "final_coherence": final_coherence,
            "final_entropy": final_entropy,
            "thermal_bridge_active": final_coherence > 0.01,
        }

    def _density_matrix_entropy(self, rho: np.ndarray) -> float:
        """Von Neumann entropy: S = -Tr(rho * log2(rho))."""
        eigvals = np.linalg.eigvalsh(rho)
        eigvals = eigvals[eigvals > 1e-15]
        if len(eigvals) == 0:
            return 0.0
        return float(-np.sum(eigvals * np.log2(eigvals)))

    def _cell_population(self, rho: np.ndarray, num_cells: int, cell_idx: int) -> float:
        """Probability that cell_idx is in any excited state (not |0>)."""
        d = 8
        dim = d ** num_cells
        pop = 0.0
        for basis in range(dim):
            digits = self._basis_to_states(basis, num_cells, d)
            if digits[cell_idx] > 0:
                pop += np.real(rho[basis, basis])
        return float(pop)

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
             num_layers: int = 3, optimize: bool = True) -> Dict:
        """
        Quantum Approximate Optimization Algorithm.

        Uses Nelder-Mead to optimize gamma/beta parameters (when optimize=True).
        Falls back to random search if scipy.optimize is unavailable.
        """
        print(f"\n   QAOA: {num_layers} layers, optimize={optimize}")
        H_problem = self._build_hamiltonian(problem_type, problem_data)
        dim = H_problem.shape[0]

        # Mixer: sum of X operators (single bit-flip transitions)
        H_mixer = np.zeros((dim, dim), dtype=complex)
        for i in range(dim):
            for j in range(dim):
                if bin(i ^ j).count("1") == 1:
                    H_mixer[i, j] = 1.0

        # Precompute initial state
        psi0 = np.ones(dim, dtype=complex) / np.sqrt(dim)

        eval_count = [0]

        def qaoa_energy(params):
            """Evaluate QAOA circuit for given parameters."""
            gammas = params[:num_layers]
            betas = params[num_layers:]
            state = psi0.copy()
            for layer in range(num_layers):
                U_p = self._matrix_exponential(-1j * gammas[layer] * H_problem)
                state = U_p @ state
                U_m = self._matrix_exponential(-1j * betas[layer] * H_mixer)
                state = U_m @ state
            state /= np.linalg.norm(state)
            energy = float(np.real(state.conj() @ H_problem @ state))
            eval_count[0] += 1
            if eval_count[0] % 20 == 0:
                self._emit_sensor("energy.total", eval_count[0], energy)
                self.energy_history.append(energy)
            return energy

        if optimize:
            try:
                from scipy.optimize import minimize
                # Random initial point
                x0 = np.concatenate([
                    np.random.uniform(0, 2 * np.pi, num_layers),
                    np.random.uniform(0, np.pi, num_layers),
                ])
                result = minimize(qaoa_energy, x0, method="Nelder-Mead",
                                  options={"maxiter": 200, "xatol": 1e-3, "fatol": 1e-4})
                best_params = result.x
                best_energy = result.fun
                print(f"   Nelder-Mead converged: E={best_energy:.6f} ({result.nfev} evals)")
            except ImportError:
                print("   scipy.optimize not available, falling back to random search")
                optimize = False  # fall through to random search

        if not optimize:
            # Random search fallback
            best_energy = float("inf")
            best_params = None
            for sample in range(50):
                params = np.concatenate([
                    np.random.uniform(0, 2 * np.pi, num_layers),
                    np.random.uniform(0, np.pi, num_layers),
                ])
                e = qaoa_energy(params)
                if e < best_energy:
                    best_energy = e
                    best_params = params
                if sample % 10 == 0:
                    print(f"   Sample {sample:>3d}: best E={best_energy:.4f}")

        # Evaluate best params to get state vector
        gammas = best_params[:num_layers]
        betas = best_params[num_layers:]
        state = psi0.copy()
        for layer in range(num_layers):
            U_p = self._matrix_exponential(-1j * gammas[layer] * H_problem)
            state = U_p @ state
            U_m = self._matrix_exponential(-1j * betas[layer] * H_mixer)
            state = U_m @ state
        state /= np.linalg.norm(state)

        probs = np.abs(state) ** 2
        measured = np.random.choice(dim, p=probs)
        solution = self._extract_quantum_solution(measured, problem_type, problem_data)
        print(f"   QAOA best energy: {best_energy:.6f}")
        return {
            "measured_state": measured,
            "final_energy": best_energy,
            "state_vector": state,
            "solution": solution,
            "params": {"gammas": list(gammas), "betas": list(betas)},
        }

    # ------------------------------------------------------------------
    # Solution extraction
    # ------------------------------------------------------------------

    def _extract_quantum_solution(self, measured_state: int,
                                  problem_type: str, problem_data: Dict) -> Dict:
        if problem_type == "factorization":
            N = problem_data["N"]
            max_factor = int(math.isqrt(N)) + 1
            stride = max(1, math.ceil(max_factor / 8))
            i = measured_state // 8
            j = measured_state % 8
            fa = 2 + i * stride
            fb = 2 + j * stride
            return {"factors": [fa, fb], "product": fa * fb, "correct": fa * fb == N,
                    "stride": stride}
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
        if len(nz) == 0:
            return 0.0
        return float(-np.sum(nz * np.log2(nz)))

    def glyph_trace(self, max_cells: int = 10) -> str:
        """Show dominant state of each cell as glyphs (no spaces, consistent with classical)."""
        cells = self.cells[:max_cells]
        parts = []
        for c in cells:
            dominant = int(np.argmax(c.get_probability_distribution()))
            g = _STATE_GLYPHS[dominant] if dominant < len(_STATE_GLYPHS) else str(dominant)
            parts.append(g)
        if self.num_cells > max_cells:
            parts.append("...")
        return "".join(parts)


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
    """QAOA with Nelder-Mead optimization."""
    print("\n" + "=" * 60)
    print("QUANTUM DEMO: QAOA (NELDER-MEAD)")
    print("=" * 60)
    N = 15
    qc = QuantumMandalaComputer(golden_depth=2, sacred_geometry=8, entanglement_strength=0.1)
    qc.bloom_quantum_mandala()
    result = qc.qaoa("factorization", {"N": N}, num_layers=4, optimize=True)
    sol = result["solution"]
    print(f"\n   N={N}, factors={sol['factors']}, correct={sol['correct']}")
    print(f"   Telemetry: {len(qc.telemetry)} readings")
    return result


def demo_entangled_annealing():
    """Entangled multi-cell annealing with real entanglement entropy."""
    print("\n" + "=" * 60)
    print("QUANTUM DEMO: ENTANGLED MULTI-CELL ANNEALING")
    print("=" * 60)
    N = 15
    qc = QuantumMandalaComputer(golden_depth=2, sacred_geometry=8, entanglement_strength=0.5)
    result = qc.entangled_annealing("factorization", {"N": N}, num_cells=2, num_steps=100)
    sol = result["solution"]
    print(f"\n   N={N}, cell states={result['cell_states']}")
    print(f"   Factors: {sol['factors']}, correct: {sol['correct']}")
    # Show entanglement readings
    ent_readings = [r for r in qc.telemetry if r["sensor_id"] == "quantum.entanglement"]
    if ent_readings:
        print(f"   Entanglement entropy: {ent_readings[0]['value']:.3f} -> {ent_readings[-1]['value']:.3f} bits")
    return result


def demo_thermal_bridge():
    """Thermal bridge: noise-assisted quantum energy transfer."""
    print("\n" + "=" * 60)
    print("QUANTUM DEMO: THERMAL BRIDGE (Room Temperature)")
    print("=" * 60)
    print("   Like photosynthesis: thermal noise HELPS energy transfer")

    N = 15
    qc = QuantumMandalaComputer(golden_depth=2, sacred_geometry=8, entanglement_strength=0.3)

    # Compare: no noise vs with noise (thermal bridge)
    print("\n   --- Pure unitary (no noise, cryogenic) ---")
    result_pure = qc.thermal_bridge_evolution(
        "factorization", {"N": N}, num_cells=2, num_steps=100,
        gamma_decay=0.0, gamma_dephase=0.0, bridge_strength=0.2,
    )

    print("\n   --- Thermal bridge (room temperature noise) ---")
    qc2 = QuantumMandalaComputer(golden_depth=2, sacred_geometry=8, entanglement_strength=0.3)
    result_bridge = qc2.thermal_bridge_evolution(
        "factorization", {"N": N}, num_cells=2, num_steps=100,
        gamma_decay=0.01, gamma_dephase=0.05, bridge_strength=0.2,
    )

    print(f"\n   Comparison:")
    print(f"     Pure unitary coherence:    {result_pure['final_coherence']:.4f}")
    print(f"     Thermal bridge coherence:  {result_bridge['final_coherence']:.4f}")
    print(f"     Bridge active: {result_bridge['thermal_bridge_active']}")

    return result_bridge


def demo_fret_coupling():
    """FRET dipolar coupling: excitation hopping between cells."""
    print("\n" + "=" * 60)
    print("QUANTUM DEMO: FRET DIPOLAR COUPLING")
    print("=" * 60)

    qc = QuantumMandalaComputer(golden_depth=2, sacred_geometry=8, entanglement_strength=0.5)

    # Build FRET Hamiltonian for 2 cells
    H_fret = qc._build_fret_coupling(2)
    print(f"\n   FRET coupling matrix: {H_fret.shape[0]}x{H_fret.shape[1]}")
    print(f"   Non-zero elements: {np.count_nonzero(H_fret)}")
    print(f"   Hermitian: {np.allclose(H_fret, H_fret.conj().T)}")

    # Compare ZZ (diagonal) vs XX+YY (off-diagonal) coupling
    H_zz = qc._build_multicell_hamiltonian(2, "factorization", {"N": 15})
    fret_offdiag = np.count_nonzero(H_fret - np.diag(np.diag(H_fret)))
    zz_offdiag = np.count_nonzero(H_zz - np.diag(np.diag(H_zz)))
    print(f"\n   ZZ coupling off-diagonal elements: {zz_offdiag}")
    print(f"   FRET coupling off-diagonal elements: {fret_offdiag}")
    print(f"   FRET enables excitation HOPPING (not just energy shifting)")

    return H_fret


if __name__ == "__main__":
    print("=" * 60)
    print("QUANTUM MANDALA COMPUTING v2.0")
    print("   Superposition of Octahedral States")
    print("=" * 60)

    demo_quantum_factorization()
    demo_grover_search()
    demo_quantum_superposition()
    demo_qaoa()
    demo_entangled_annealing()
    demo_fret_coupling()
    demo_thermal_bridge()

    print("\n" + "=" * 60)
    print("ALL QUANTUM DEMONSTRATIONS COMPLETE")
    print("=" * 60)
