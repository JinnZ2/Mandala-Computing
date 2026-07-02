# ===================================================================
#  MANDALA COMPUTING EXPLORER v3
#  Adaptive RG + Quantum Circuit (Ising Model)
#  ===================================================================

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from ipywidgets import interact, Dropdown, IntSlider, FloatSlider, VBox, HBox, Output, Button, Checkbox, Label
from IPython.display import display, clear_output
from scipy.linalg import expm
import warnings
warnings.filterwarnings('ignore')

# -------------------------------------------------------------------
# 1. Octahedral Glyph System
# -------------------------------------------------------------------
GLYPHS = ['◈', '◉', '◊', '○', '●', '◐', '◑', '◒']

def int_to_glyph(n, width=1):
    if n == 0:
        return GLYPHS[0]
    digits = []
    while n > 0:
        digits.append(GLYPHS[n % 8])
        n //= 8
    return ''.join(reversed(digits)).rjust(width, GLYPHS[0])

# -------------------------------------------------------------------
# 2. Problem Encoder (same as before, but we'll keep it clean)
# -------------------------------------------------------------------
class ProblemEncoder:
    def __init__(self, problem_type='factorization', N=143, qubits=4):
        self.problem_type = problem_type
        self.N = N
        self.qubits = qubits
        self.total_cells = 0
        self._init_problem()
        
    def _init_problem(self):
        if self.problem_type == 'factorization':
            import math
            max_factor = int(math.isqrt(self.N))
            cells = max(1, len(str(max_factor)))
            self.total_cells = 2 * cells
        elif self.problem_type == 'sat':
            self.total_cells = 3
        elif self.problem_type == 'graph_coloring':
            self.total_cells = 3
        elif self.problem_type == 'ising':
            self.total_cells = self.qubits
            # Random Ising couplings (J) and fields (h)
            np.random.seed(42)
            self.J = np.random.randn(self.qubits, self.qubits) * 2
            self.J = (self.J + self.J.T) / 2
            np.fill_diagonal(self.J, 0)
            self.h = np.random.randn(self.qubits) * 2
        elif self.problem_type == 'tsp':
            self.num_cities = 5
            self.total_cells = self.num_cities
            np.random.seed(42)
            self.dist = np.random.rand(self.num_cities, self.num_cities)
            self.dist = (self.dist + self.dist.T) / 2
            np.fill_diagonal(self.dist, 0)
        elif self.problem_type == 'knapsack':
            self.num_items = 6
            self.total_cells = self.num_items
            np.random.seed(42)
            self.weights = np.random.randint(1, 10, self.num_items)
            self.values = np.random.randint(5, 20, self.num_items)
            self.capacity = int(np.sum(self.weights) * 0.5)
            
    def energy(self, state):
        state = np.array(state).astype(int)
        if self.problem_type == 'factorization':
            half = len(state) // 2
            f1, f2 = 0, 0
            for d in state[:half]:
                f1 = f1 * 8 + d
            for d in state[half:]:
                f2 = f2 * 8 + d
            if f1 < 2 or f2 < 2:
                return 1e6 + abs(f1 * f2 - self.N)
            return (f1 * f2 - self.N) ** 2
        elif self.problem_type == 'sat':
            x1 = state[0] >= 4
            x2 = state[1] >= 4
            x3 = state[2] >= 4
            c1 = x1 or x2 or x3
            c2 = (not x1) or (not x2) or (not x3)
            return 2 * ((not c1) + (not c2))
        elif self.problem_type == 'graph_coloring':
            c = state[:3]
            violations = (c[0] == c[1]) + (c[1] == c[2]) + (c[0] == c[2])
            return 2 * violations - 0.618 * (3 - violations)
        elif self.problem_type == 'ising':
            # Map state (0-7) to spin ±1 using parity (0-3 = -1, 4-7 = +1)
            spin = 2 * (state // 4) - 1  # 0->-1, 1->-1, ..., 4->+1, 5->+1...
            energy = np.sum(self.h * spin)
            for i in range(len(spin)):
                for j in range(i+1, len(spin)):
                    energy += self.J[i, j] * spin[i] * spin[j]
            return energy
        elif self.problem_type == 'tsp':
            perm = sorted(range(self.num_cities), key=lambda i: state[i])
            total = 0
            for i in range(self.num_cities):
                total += self.dist[perm[i], perm[(i+1) % self.num_cities]]
            return total
        elif self.problem_type == 'knapsack':
            total_w, total_v = 0, 0
            for i, s in enumerate(state):
                if s > 0:
                    total_w += self.weights[i]
                    total_v += self.values[i]
            if total_w > self.capacity:
                return 1e6 + (total_w - self.capacity) * 100
            return -total_v
        return 0
    
    def decode_solution(self, state):
        state = np.array(state).astype(int)
        if self.problem_type == 'factorization':
            half = len(state) // 2
            f1, f2 = 0, 0
            for d in state[:half]:
                f1 = f1 * 8 + d
            for d in state[half:]:
                f2 = f2 * 8 + d
            if f1 < 2 or f2 < 2:
                return None
            return {'factors': [f1, f2], 'verified': f1*f2 == self.N}
        elif self.problem_type == 'sat':
            x1 = state[0] >= 4
            x2 = state[1] >= 4
            x3 = state[2] >= 4
            return {'assignment': [x1, x2, x3], 
                    'clauses_satisfied': (x1 or x2 or x3) and ((not x1) or (not x2) or (not x3))}
        elif self.problem_type == 'graph_coloring':
            return {'colors': state[:3].tolist(), 'valid': len(set(state[:3])) == 3}
        elif self.problem_type == 'ising':
            # Map back to spin
            spin = 2 * (state // 4) - 1
            return {'spin_config': spin.tolist(), 'energy': self.energy(state)}
        elif self.problem_type == 'tsp':
            perm = sorted(range(self.num_cities), key=lambda i: state[i])
            return {'tour': perm, 'length': self.energy(state)}
        elif self.problem_type == 'knapsack':
            taken = [i for i, s in enumerate(state) if s > 0]
            total_w = sum(self.weights[i] for i in taken)
            total_v = sum(self.values[i] for i in taken)
            return {'taken': taken, 'total_weight': total_w, 'total_value': total_v}
        return None

# -------------------------------------------------------------------
# 3. Simulated Annealing (base)
# -------------------------------------------------------------------
class SimulatedAnnealing:
    def __init__(self, encoder, T_start=5.0, T_end=0.001, steps=5000):
        self.encoder = encoder
        self.T_start = T_start
        self.T_end = T_end
        self.steps = steps
        self.history = {'energy': [], 'temperature': [], 'acceptance': []}
        
    def solve(self, initial_state=None):
        n_cells = self.encoder.total_cells
        if initial_state is None:
            state = np.random.randint(0, 8, n_cells)
        else:
            state = np.array(initial_state)
        current_energy = self.encoder.energy(state)
        best_state = state.copy()
        best_energy = current_energy
        self.history = {'energy': [current_energy], 'temperature': [], 'acceptance': []}
        
        for step in range(self.steps):
            t = step / self.steps
            T = self.T_start * (self.T_end / self.T_start) ** t
            self.history['temperature'].append(T)
            new_state = state.copy()
            cell_idx = np.random.randint(0, n_cells)
            new_state[cell_idx] = np.random.randint(0, 8)
            new_energy = self.encoder.energy(new_state)
            delta_E = new_energy - current_energy
            if delta_E < 0 or np.random.rand() < np.exp(-delta_E / (T + 1e-10)):
                state = new_state
                current_energy = new_energy
                self.history['acceptance'].append(1)
                if current_energy < best_energy:
                    best_state = state.copy()
                    best_energy = current_energy
            else:
                self.history['acceptance'].append(0)
            self.history['energy'].append(current_energy)
            if best_energy == 0:
                break
        return best_state, best_energy

# -------------------------------------------------------------------
# 4. Adaptive Holographic RG
# -------------------------------------------------------------------
class AdaptiveHolographicRG:
    def __init__(self, encoder, base_solver, max_rg_steps=3, tolerance=0.5):
        self.encoder = encoder
        self.base_solver = base_solver
        self.max_rg_steps = max_rg_steps
        self.tolerance = tolerance
        self.rg_history = []
        self.rg_energies = []
        
    def coarse_grain(self, state):
        if len(state) <= 2:
            return state
        new_state = []
        for i in range(0, len(state) - 1, 2):
            avg = int(round((state[i] + state[i+1]) / 2))
            new_state.append(np.clip(avg, 0, 7))
        if len(state) % 2 == 1:
            new_state.append(state[-1])
        return np.array(new_state)
    
    def project_back(self, coarse_state, n_cells_orig):
        full = []
        for s in coarse_state:
            full.append(s)
            if len(full) < n_cells_orig:
                full.append(s)
        while len(full) < n_cells_orig:
            full.append(np.random.randint(0, 8))
        return np.array(full[:n_cells_orig])
    
    def solve(self, initial_state=None):
        n_cells_orig = self.encoder.total_cells
        if initial_state is None:
            state = np.random.randint(0, 8, n_cells_orig)
        else:
            state = np.array(initial_state)
        
        self.rg_history = [state.copy()]
        self.rg_energies = [self.encoder.energy(state)]
        
        # Store original encoder
        orig_encoder = self.encoder
        
        for rg_step in range(self.max_rg_steps):
            # Coarse-grain
            coarse = self.coarse_grain(state)
            if len(coarse) <= 2:
                break  # too small
            
            # Create a temporary encoder for the coarse level
            # We'll use a trick: we create a new encoder of the same type but with reduced cells
            temp_encoder = ProblemEncoder(orig_encoder.problem_type, orig_encoder.N)
            temp_encoder.total_cells = len(coarse)
            # Copy Ising parameters if applicable
            if orig_encoder.problem_type == 'ising':
                temp_encoder.h = orig_encoder.h[:len(coarse)]  # truncate fields
                temp_encoder.J = orig_encoder.J[:len(coarse), :len(coarse)]
            # For other types, we can't easily map, so we just treat the coarse state as the new state
            # But we can evaluate the energy using the original encoder's energy on a projected state
            # We'll use the original energy function on a projected state (padded with zeros)
            def coarse_energy(c):
                # Project back to original size (with zeros) and evaluate
                proj = np.zeros(n_cells_orig, dtype=int)
                # Fill first len(c) cells
                proj[:len(c)] = c
                return orig_encoder.energy(proj)
            
            # Solve on coarse level using the base solver, but with a modified energy function
            # We'll just use a local search for simplicity
            best_coarse = coarse.copy()
            best_coarse_E = coarse_energy(coarse)
            # Try a few random perturbations
            for _ in range(100):
                test = coarse.copy()
                idx = np.random.randint(0, len(test))
                test[idx] = np.random.randint(0, 8)
                e = coarse_energy(test)
                if e < best_coarse_E:
                    best_coarse = test
                    best_coarse_E = e
            
            # Project back to original resolution
            full_state = self.project_back(best_coarse, n_cells_orig)
            full_energy = orig_encoder.energy(full_state)
            
            # Check if energy improved
            if full_energy < self.rg_energies[-1] - self.tolerance:
                # Improvement! Keep the coarse state and continue
                state = full_state
                self.rg_history.append(best_coarse)
                self.rg_energies.append(full_energy)
            else:
                # No improvement: stop RG and revert to previous best
                break
        
        # Final refinement using base solver on the best state found
        final_solver = SimulatedAnnealing(orig_encoder, T_start=0.5, T_end=0.01, steps=500)
        best_final, _ = final_solver.solve(state)
        final_energy = orig_encoder.energy(best_final)
        
        return best_final, final_energy

# -------------------------------------------------------------------
# 5. Quantum Circuit Simulator (Exact Diagonalization)
# -------------------------------------------------------------------
class QuantumCircuitSimulator:
    def __init__(self, encoder, qubits=4, steps=100, dt=0.1, Gamma_start=5.0, Gamma_end=0.1):
        self.encoder = encoder
        self.qubits = qubits
        self.steps = steps
        self.dt = dt
        self.Gamma_start = Gamma_start
        self.Gamma_end = Gamma_end
        self.history = {'energy': [], 'ground_prob': [], 'Gamma': []}
        
    def solve(self, initial_state=None):
        n = self.qubits
        dim = 2 ** n
        
        # Build Ising Hamiltonian (H_ising)
        # We need to map the problem to spin-1/2. The encoder's energy function gives us the classical energy.
        # We'll construct the Ising Hamiltonian matrix.
        # We'll use the fact that energy(s) = sum_i h_i * sigma_i^z + sum_ij J_ij * sigma_i^z * sigma_j^z
        # We'll build the matrix in the computational basis.
        
        # Get J and h from the encoder (if it's an Ising problem)
        if self.encoder.problem_type == 'ising':
            J = self.encoder.J
            h = self.encoder.h
        else:
            # For non-Ising problems, we'll generate a random Ising problem for demonstration
            np.random.seed(42)
            J = np.random.randn(n, n) * 2
            J = (J + J.T) / 2
            np.fill_diagonal(J, 0)
            h = np.random.randn(n) * 2
            print("⚠️  Non-Ising problem: using random Ising model for quantum circuit demo.")
        
        # Build H_ising matrix
        H_ising = np.zeros((dim, dim))
        for state_idx in range(dim):
            # Get spin configuration (+1/-1) from bitstring (0->+1, 1->-1)
            bits = [(state_idx >> i) & 1 for i in range(n)]
            spin = np.array([1 if b == 0 else -1 for b in bits])
            # Energy
            E = np.sum(h * spin)
            for i in range(n):
                for j in range(i+1, n):
                    E += J[i, j] * spin[i] * spin[j]
            H_ising[state_idx, state_idx] = E
        
        # Build transverse field term: H_field = -Gamma * sum_i sigma_i^x
        # We'll compute the full H_field matrix (sparse, but we'll build explicitly for small n)
        def build_field_matrix(Gamma):
            H_field = np.zeros((dim, dim))
            for i in range(n):
                # sigma_i^x acts on qubit i
                for state_idx in range(dim):
                    # Flip bit i
                    flipped = state_idx ^ (1 << i)
                    H_field[state_idx, flipped] -= Gamma
            return H_field
        
        # Initial state: equal superposition (all |+>)
        psi = np.ones(dim) / np.sqrt(dim)
        
        # Time evolution
        self.history = {'energy': [], 'ground_prob': [], 'Gamma': []}
        
        # Compute ground state (for probability tracking)
        eigvals, eigvecs = np.linalg.eigh(H_ising)
        ground_state = eigvecs[:, 0]
        ground_energy = eigvals[0]
        
        for step in range(self.steps):
            t = step / self.steps
            Gamma = self.Gamma_start * (self.Gamma_end / self.Gamma_start) ** t
            self.history['Gamma'].append(Gamma)
            
            # Hamiltonian at this step: H = H_ising + H_field(Gamma)
            H_total = H_ising + build_field_matrix(Gamma)
            
            # Time evolution (U = exp(-i H dt))
            U = expm(-1j * H_total * self.dt)
            psi = U @ psi
            
            # Compute expectation values
            # Energy expectation
            E_exp = np.real(np.conj(psi).T @ H_ising @ psi)
            # Ground state probability
            prob_ground = np.abs(np.conj(ground_state).T @ psi)**2
            
            self.history['energy'].append(E_exp)
            self.history['ground_prob'].append(prob_ground)
        
        # Final measurement: sample from the final state
        probs = np.abs(psi)**2
        most_likely_idx = np.argmax(probs)
        # Convert to glyph state
        # For Ising, we can map back to 8-state cells: 0-3 = -1, 4-7 = +1
        spin_config = np.array([1 if (most_likely_idx >> i) & 1 == 0 else -1 for i in range(n)])
        # Convert spin to glyph state (0-7)
        glyph_state = np.zeros(n, dtype=int)
        for i, s in enumerate(spin_config):
            glyph_state[i] = 4 if s == 1 else 0  # +1 -> 4, -1 -> 0
        # Also, the energy of the final state
        final_energy = self.encoder.energy(glyph_state)
        
        # Store best result
        self.best_state = glyph_state
        self.best_energy = final_energy
        self.probs = probs
        self.ground_energy = ground_energy
        
        return self.best_state, self.best_energy

# -------------------------------------------------------------------
# 6. Unified Explorer
# -------------------------------------------------------------------
class MandalaExplorerV3:
    def __init__(self):
        self.encoder = None
        self.result = None
        self.best_state = None
        self.history = None
        self.rg_history = None
        
    def run(self, problem_type='factorization', N=143, solver_type='simulated_annealing',
            T_start=5.0, T_end=0.001, steps=5000, Gamma=2.0, adaptive_rg=False, qubits=4):
        
        self.encoder = ProblemEncoder(problem_type, N, qubits)
        self.encoder._init_problem()
        
        if solver_type == 'simulated_annealing':
            solver = SimulatedAnnealing(self.encoder, T_start, T_end, steps)
            best_state, best_energy = solver.solve()
            self.history = solver.history
            self.rg_history = None
        
        elif solver_type == 'quantum_annealing':
            # Use QuantumAnnealing from previous version (we'll keep it simple)
            # We'll import the QuantumAnnealing class from earlier or redefine
            class QuantumAnnealing:
                def __init__(self, enc, Ts, Te, st, Gs, Ge):
                    self.encoder = enc
                    self.T_start = Ts
                    self.T_end = Te
                    self.steps = st
                    self.Gamma_start = Gs
                    self.Gamma_end = Ge
                    self.history = {'energy': [], 'temperature': [], 'acceptance': [], 'tunneling': []}
                def solve(self, init=None):
                    n_cells = self.encoder.total_cells
                    state = np.random.randint(0, 8, n_cells) if init is None else np.array(init)
                    current_energy = self.encoder.energy(state)
                    best_state = state.copy()
                    best_energy = current_energy
                    self.history = {'energy': [current_energy], 'temperature': [], 'acceptance': [], 'tunneling': []}
                    for step in range(self.steps):
                        t = step / self.steps
                        T = self.T_start * (self.T_end / self.T_start) ** t
                        Gamma = self.Gamma_start * (self.Gamma_end / self.Gamma_start) ** t
                        self.history['temperature'].append(T)
                        new_state = state.copy()
                        cell_idx = np.random.randint(0, n_cells)
                        new_state[cell_idx] = np.random.randint(0, 8)
                        new_energy = self.encoder.energy(new_state)
                        delta_E = new_energy - current_energy
                        accept = False
                        tunneling = False
                        if delta_E < 0:
                            accept = True
                        else:
                            if np.random.rand() < np.exp(-delta_E / (T + 1e-10)):
                                accept = True
                            elif np.random.rand() < np.exp(-Gamma * np.sqrt(abs(delta_E) + 1e-10)):
                                accept = True
                                tunneling = True
                        if accept:
                            state = new_state
                            current_energy = new_energy
                            self.history['acceptance'].append(1)
                            self.history['tunneling'].append(1 if tunneling else 0)
                            if current_energy < best_energy:
                                best_state = state.copy()
                                best_energy = current_energy
                        else:
                            self.history['acceptance'].append(0)
                            self.history['tunneling'].append(0)
                        self.history['energy'].append(current_energy)
                        if best_energy == 0:
                            break
                    return best_state, best_energy
            solver = QuantumAnnealing(self.encoder, T_start, T_end, steps, Gamma, 0.1)
            best_state, best_energy = solver.solve()
            self.history = solver.history
            self.rg_history = None
        
        elif solver_type == 'holographic_rg':
            base_solver = SimulatedAnnealing(self.encoder, T_start, T_end, max(500, steps//5))
            if adaptive_rg:
                rg = AdaptiveHolographicRG(self.encoder, base_solver, max_rg_steps=3, tolerance=0.5)
                best_state, best_energy = rg.solve()
                self.rg_history = rg.rg_history
            else:
                # Non-adaptive RG (fixed steps)
                class FixedRG:
                    def __init__(self, enc, base, rg_steps):
                        self.encoder = enc
                        self.base = base
                        self.rg_steps = rg_steps
                        self.rg_history = []
                    def solve(self, init=None):
                        state = np.random.randint(0, 8, self.encoder.total_cells) if init is None else np.array(init)
                        self.rg_history = [state.copy()]
                        for _ in range(self.rg_steps):
                            if len(state) <= 2:
                                break
                            new_state = []
                            for i in range(0, len(state)-1, 2):
                                avg = int(round((state[i] + state[i+1]) / 2))
                                new_state.append(np.clip(avg, 0, 7))
                            if len(state) % 2 == 1:
                                new_state.append(state[-1])
                            state = np.array(new_state)
                            self.rg_history.append(state)
                        # Solve on coarsest level
                        # We need to project back for energy? Actually, we'll just solve the coarse problem.
                        # But the encoder expects the original number of cells; we'll pad.
                        pad_state = np.zeros(self.encoder.total_cells, dtype=int)
                        pad_state[:len(state)] = state
                        best, _ = self.base.solve(pad_state)
                        return best, self.encoder.energy(best)
                rg = FixedRG(self.encoder, base_solver, steps//500 + 1)
                best_state, best_energy = rg.solve()
                self.rg_history = rg.rg_history
        
        elif solver_type == 'quantum_circuit':
            if problem_type != 'ising':
                print("Quantum Circuit is best used with 'ising' problem type.")
                # Force to Ising with given qubits
                self.encoder = ProblemEncoder('ising', N, qubits)
                self.encoder._init_problem()
            qsim = QuantumCircuitSimulator(self.encoder, qubits, steps=steps, dt=0.05, Gamma_start=5.0, Gamma_end=0.1)
            best_state, best_energy = qsim.solve()
            self.history = qsim.history
            self.rg_history = None
            # Store extra info
            self.probs = qsim.probs
            self.ground_energy = qsim.ground_energy
        
        self.best_state = best_state
        self.best_energy = best_energy
        self.result = self.encoder.decode_solution(best_state)
        
        return self.plot_results()
    
    def plot_results(self):
        fig = plt.figure(figsize=(18, 14))
        gs = gridspec.GridSpec(3, 3, height_ratios=[1, 1, 0.8])
        
        # Panel 1: Energy history
        ax = fig.add_subplot(gs[0, 0])
        if self.history and 'energy' in self.history:
            ax.plot(self.history['energy'], 'b-', lw=1, alpha=0.7)
            ax.set_xlabel('Step')
            ax.set_ylabel('Energy')
            ax.set_title('Energy vs Time')
            ax.grid(True, alpha=0.3)
            if 'temperature' in self.history and len(self.history['temperature']) > 0:
                ax2 = ax.twinx()
                ax2.plot(self.history['temperature'], 'r--', lw=1, alpha=0.5)
                ax2.set_ylabel('Temperature', color='r')
                ax2.tick_params(axis='y', labelcolor='r')
        
        # Panel 2: Acceptance / Tunneling
        ax = fig.add_subplot(gs[0, 1])
        if 'acceptance' in self.history and len(self.history['acceptance']) > 0:
            window = min(100, len(self.history['acceptance']))
            acc_avg = np.convolve(self.history['acceptance'], np.ones(window)/window, mode='valid')
            ax.plot(acc_avg, 'g-', lw=2, label='Acceptance')
            if 'tunneling' in self.history and len(self.history['tunneling']) > 0:
                tun_avg = np.convolve(self.history['tunneling'], np.ones(window)/window, mode='valid')
                ax.plot(tun_avg, 'm--', lw=2, label='Tunneling')
            ax.set_xlabel('Step')
            ax.set_ylabel('Rate')
            ax.set_title('Acceptance & Tunneling')
            ax.legend()
            ax.set_ylim(-0.05, 1.05)
            ax.grid(True, alpha=0.3)
        
        # Panel 3: Quantum Circuit specific (ground state probability)
        ax = fig.add_subplot(gs[0, 2])
        if 'ground_prob' in self.history and len(self.history['ground_prob']) > 0:
            ax.plot(self.history['ground_prob'], 'purple', lw=2, label='Ground state prob')
            ax.set_xlabel('Step')
            ax.set_ylabel('Probability')
            ax.set_title('Quantum Annealing: Ground State Probability')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_ylim(-0.05, 1.05)
        else:
            ax.text(0.5, 0.5, 'Not a quantum circuit run', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Quantum Circuit Info')
        
        # Panel 4: Glyph Mandala
        ax = fig.add_subplot(gs[1, 0])
        n_cells = len(self.best_state)
        angles = np.linspace(0, 2*np.pi, n_cells, endpoint=False)
        radius = 0.4
        for i, (s, angle) in enumerate(zip(self.best_state, angles)):
            x = 0.5 + radius * np.cos(angle)
            y = 0.5 + radius * np.sin(angle)
            ax.text(x, y, GLYPHS[s], fontsize=28, ha='center', va='center',
                   bbox=dict(boxstyle='circle', facecolor='lightblue', alpha=0.8))
            for j in range(i+1, n_cells):
                x2 = 0.5 + radius * np.cos(angles[j])
                y2 = 0.5 + radius * np.sin(angles[j])
                ax.plot([x, x2], [y, y2], 'k-', alpha=0.15, lw=0.5)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('Solution Mandala (Glyphs)')
        
        # Panel 5: RG Flow (if available)
        ax = fig.add_subplot(gs[1, 1])
        if self.rg_history:
            for i, rg_state in enumerate(self.rg_history):
                ax.scatter([i]*len(rg_state), rg_state, s=50, alpha=0.7, label=f'RG {i}')
            ax.set_xlabel('RG Step (coarse → fine)')
            ax.set_ylabel('Cell State (0-7)')
            ax.set_title('Holographic RG Flow')
            ax.legend()
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'No RG data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Renormalization Flow')
        
        # Panel 6: Solution details
        ax = fig.add_subplot(gs[1, 2])
        ax.axis('off')
        info = f"""
        📊 **Problem:** {self.encoder.problem_type}
        ─────────────────────────────────
        Cells: {self.encoder.total_cells}
        Energy: {self.best_energy:.2f}
        """
        if self.encoder.problem_type == 'factorization':
            info += f"\nN = {self.encoder.N}"
        if self.result:
            if self.encoder.problem_type == 'factorization':
                info += f"\n\n✅ {self.result['factors'][0]} × {self.result['factors'][1]} = {self.encoder.N}"
                info += f"\nGlyph: {int_to_glyph(self.result['factors'][0])} × {int_to_glyph(self.result['factors'][1])}"
            elif self.encoder.problem_type == 'ising':
                info += f"\nSpin config: {self.result['spin_config']}"
                info += f"\nEnergy: {self.result['energy']:.2f}"
                if hasattr(self, 'ground_energy'):
                    info += f"\nGround state energy: {self.ground_energy:.2f}"
            else:
                info += f"\n{self.result}"
        else:
            info += "\nNo solution found."
        ax.text(0.05, 0.95, info, transform=ax.transAxes, fontsize=11,
                verticalalignment='top', family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))
        
        # Panel 7: Quantum probability distribution (if available)
        ax = fig.add_subplot(gs[2, 0])
        if hasattr(self, 'probs'):
            ax.bar(range(len(self.probs)), self.probs, color='purple', alpha=0.7)
            ax.set_xlabel('State index')
            ax.set_ylabel('Probability')
            ax.set_title('Final Quantum State Distribution')
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'No quantum circuit data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Quantum State Distribution')
        
        # Panel 8: Ising couplings (if Ising problem)
        ax = fig.add_subplot(gs[2, 1])
        if self.encoder.problem_type == 'ising' and hasattr(self.encoder, 'J'):
            im = ax.imshow(self.encoder.J, cmap='RdBu_r', origin='lower', vmin=-3, vmax=3)
            ax.set_title('Ising Couplings (J)')
            plt.colorbar(im, ax=ax, fraction=0.05)
            ax.set_xlabel('Qubit')
            ax.set_ylabel('Qubit')
        else:
            ax.text(0.5, 0.5, 'Not an Ising problem', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Ising Couplings')
        
        # Panel 9: Adaptive RG info
        ax = fig.add_subplot(gs[2, 2])
        if self.rg_history:
            energies = [self.encoder.energy(np.pad(rg, (0, self.encoder.total_cells - len(rg)))) 
                        if len(rg) < self.encoder.total_cells else self.encoder.energy(rg) 
                        for rg in self.rg_history]
            ax.plot(energies, 'go-', lw=2)
            ax.set_xlabel('RG Step')
            ax.set_ylabel('Energy')
            ax.set_title('Adaptive RG: Energy per Scale')
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'Adaptive RG not used', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Adaptive RG Progress')
        
        plt.tight_layout()
        plt.show()
        return fig

# -------------------------------------------------------------------
# 7. Interactive UI
# -------------------------------------------------------------------
explorer = MandalaExplorerV3()
output = Output()

def run_interactive(problem_type, N, solver_type, T_start, T_end, steps, Gamma, adaptive_rg, qubits):
    with output:
        clear_output(wait=True)
        explorer.run(problem_type, N, solver_type, T_start, T_end, steps, Gamma, adaptive_rg, qubits)

# Widgets
problem_dropdown = Dropdown(
    options=['factorization', 'sat', 'graph_coloring', 'ising', 'tsp', 'knapsack'],
    value='ising',
    description='Problem:'
)
N_slider = IntSlider(value=143, min=15, max=1000, step=1, description='N (factor):')
solver_dropdown = Dropdown(
    options=['simulated_annealing', 'quantum_annealing', 'holographic_rg', 'quantum_circuit'],
    value='quantum_circuit',
    description='Solver:'
)
T_start_slider = FloatSlider(value=5.0, min=0.5, max=20.0, step=0.5, description='Start Temp:')
T_end_slider = FloatSlider(value=0.001, min=0.0001, max=1.0, step=0.0005, description='End Temp:')
steps_slider = IntSlider(value=200, min=50, max=500, step=10, description='Steps:')
Gamma_slider = FloatSlider(value=2.0, min=0.1, max=10.0, step=0.1, description='Tunneling (Γ):')
adaptive_rg_checkbox = Checkbox(value=False, description='Adaptive RG')
qubits_slider = IntSlider(value=4, min=2, max=6, step=1, description='Qubits (Ising):')

run_button = Button(description='Run Simulation', button_style='primary')
reset_button = Button(description='Reset', button_style='warning')

def on_run_clicked(b):
    run_interactive(
        problem_dropdown.value,
        N_slider.value,
        solver_dropdown.value,
        T_start_slider.value,
        T_end_slider.value,
        steps_slider.value,
        Gamma_slider.value,
        adaptive_rg_checkbox.value,
        qubits_slider.value
    )

def on_reset_clicked(b):
    with output:
        clear_output()
        print("🧘 Mandala Computing Explorer v3 ready.")

run_button.on_click(on_run_clicked)
reset_button.on_click(on_reset_clicked)

ui = VBox([
    HTML("<h2>🧘 Mandala Computing Explorer v3</h2>"),
    HTML("<i>Adaptive RG · Quantum Circuit (Ising) · Tunneling · RG Flow</i>"),
    HBox([problem_dropdown, N_slider]),
    HBox([solver_dropdown, T_start_slider, T_end_slider]),
    HBox([steps_slider, Gamma_slider, qubits_slider]),
    HBox([adaptive_rg_checkbox]),
    HBox([run_button, reset_button]),
    output
])

display(ui)
print("🚀 Mandala Explorer v3 loaded. Select parameters and click 'Run Simulation'.")

# -------------------------------------------------------------------
# 8. Default demo: Ising model with Quantum Circuit
# -------------------------------------------------------------------
print("\n🧪 Running default: 4-qubit Ising spin glass with Quantum Circuit...")
run_interactive('ising', 143, 'quantum_circuit', 5.0, 0.001, 200, 2.0, False, 4)
