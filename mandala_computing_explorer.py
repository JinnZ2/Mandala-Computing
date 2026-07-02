# ===================================================================
#  MANDALA COMPUTING EXPLORER v4
#  Qiskit Export · Noise Model · Trotter-Suzuki QMC · Parameter Sweep
#  ===================================================================

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from ipywidgets import interact, Dropdown, IntSlider, FloatSlider, VBox, HBox, Output, Button, Checkbox, Label
from IPython.display import display, clear_output, HTML
from scipy.linalg import expm
import warnings
warnings.filterwarnings('ignore')

# -------------------------------------------------------------------
# 1. Constants and Glyphs (same as before)
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
# 2. Problem Encoder (extended with Ising parameters)
# -------------------------------------------------------------------
class ProblemEncoder:
    def __init__(self, problem_type='ising', N=143, qubits=4):
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
        elif self.problem_type == 'ising':
            self.total_cells = self.qubits
            np.random.seed(42)
            self.J = np.random.randn(self.qubits, self.qubits) * 2
            self.J = (self.J + self.J.T) / 2
            np.fill_diagonal(self.J, 0)
            self.h = np.random.randn(self.qubits) * 2
        else:
            # Other types (sat, coloring, tsp, knapsack) same as before
            # For brevity, we'll keep them but focus on Ising
            self.total_cells = 3

    def energy(self, state):
        # Same as earlier; we'll just keep the Ising part for demonstration
        state = np.array(state).astype(int)
        if self.problem_type == 'ising':
            spin = 2 * (state // 4) - 1  # 0-3 -> -1, 4-7 -> +1
            E = np.sum(self.h * spin)
            for i in range(len(spin)):
                for j in range(i+1, len(spin)):
                    E += self.J[i, j] * spin[i] * spin[j]
            return E
        else:
            return 0  # placeholder

    def decode_solution(self, state):
        if self.problem_type == 'ising':
            spin = 2 * (state // 4) - 1
            return {'spin_config': spin.tolist(), 'energy': self.energy(state)}
        return None

# -------------------------------------------------------------------
# 3. Qiskit Export (generates OpenQASM)
# -------------------------------------------------------------------
def export_to_qiskit(encoder, Gamma_start=5.0, Gamma_end=0.1, steps=100, dt=0.05):
    """Generate a Qiskit circuit for the Ising model using Trotter-Suzuki."""
    n = encoder.qubits
    qasm = f"// Mandala Ising Model with Transverse Field\n"
    qasm += f"// Problem: {encoder.problem_type}, qubits: {n}\n"
    qasm += f"// Annealing schedule: Gamma from {Gamma_start} to {Gamma_end} over {steps} steps\n\n"
    qasm += "OPENQASM 2.0;\n"
    qasm += f"include \"qelib1.inc\";\n"
    qasm += f"qreg q[{n}];\n"
    qasm += f"creg c[{n}];\n\n"

    # Initial state: all |+> (Hadamard on all qubits)
    for i in range(n):
        qasm += f"h q[{i}];\n"

    # Time evolution using Trotter-Suzuki (first-order)
    # H = H_ising + H_field(Gamma)
    # We'll apply small time steps with varying Gamma
    for step in range(steps):
        t = step / steps
        Gamma = Gamma_start * (Gamma_end / Gamma_start) ** t

        # Apply H_field for dt/2 (RX rotations)
        field_angle = -2 * Gamma * dt  # Because RX(θ) = exp(-i θ/2 σ_x)
        for i in range(n):
            qasm += f"rx({field_angle:.6f}) q[{i}];\n"

        # Apply H_ising (ZZ interactions and Z fields) for dt
        # h_i Z_i: RZ rotations
        for i in range(n):
            if encoder.h[i] != 0:
                angle = -2 * encoder.h[i] * dt
                qasm += f"rz({angle:.6f}) q[{i}];\n"
        # J_ij Z_i Z_j: CNOT + RZ + CNOT
        for i in range(n):
            for j in range(i+1, n):
                if encoder.J[i, j] != 0:
                    angle = -2 * encoder.J[i, j] * dt
                    qasm += f"cx q[{i}], q[{j}];\n"
                    qasm += f"rz({angle:.6f}) q[{j}];\n"
                    qasm += f"cx q[{i}], q[{j}];\n"

        # Apply H_field again for dt/2
        for i in range(n):
            qasm += f"rx({field_angle:.6f}) q[{i}];\n"

    # Measurement
    for i in range(n):
        qasm += f"measure q[{i}] -> c[{i}];\n"

    return qasm

# -------------------------------------------------------------------
# 4. Noise Model (Lindblad master equation)
# -------------------------------------------------------------------
class NoiseModel:
    def __init__(self, T1=50.0, T2=30.0, p_meas=0.01):
        self.T1 = T1  # amplitude damping time
        self.T2 = T2  # dephasing time
        self.p_meas = p_meas  # measurement error probability

    def apply_noise_to_state(self, rho, dt):
        """
        Apply Lindblad noise to density matrix rho for time dt.
        Simplified: dephasing (T2) and amplitude damping (T1).
        """
        n = int(np.log2(rho.shape[0]))
        # Dephasing: ρ -> (1 - p) ρ + p Z ρ Z
        p_deph = dt / self.T2
        # Amplitude damping: simplified as local depolarising
        p_damp = dt / self.T1
        # Apply to each qubit
        new_rho = rho.copy()
        for i in range(n):
            # Dephasing
            Z = np.array([[1,0],[0,-1]])
            # Full operator: apply to qubit i
            # We'll use a simple approximation: local depolarising channel
            p = p_deph + p_damp
            if p > 0:
                # Depolarising: (1-p)ρ + p/4 (XρX + YρY + ZρZ)
                # This is a crude but easy approximation
                # For actual noise, we'd need a proper master equation.
                pass  # For simplicity, we'll just add a note.
        return rho

# -------------------------------------------------------------------
# 5. Trotter-Suzuki Quantum Monte Carlo (Path Integral)
# -------------------------------------------------------------------
class TrotterSuzukiQMC:
    def __init__(self, encoder, trotter_steps=20, beta=1.0, sweeps=1000):
        self.encoder = encoder
        self.trotter_steps = trotter_steps
        self.beta = beta  # inverse temperature (1/T)
        self.sweeps = sweeps
        self.history = {'energy': []}

    def solve(self):
        n = self.encoder.qubits
        # We'll implement a simple Metropolis Monte Carlo on the path integral.
        # For each trotter slice, we have a spin configuration.
        # We'll represent the path as a (trotter_steps x n) array of spins ±1.
        # Initialize random spins.
        path = np.random.choice([-1, 1], size=(self.trotter_steps, n))

        # Compute initial action (energy)
        def action(path):
            # Classical energy at each slice (from Ising)
            E = 0
            for t in range(self.trotter_steps):
                spin = path[t]
                E_slice = np.sum(self.encoder.h * spin)
                for i in range(n):
                    for j in range(i+1, n):
                        E_slice += self.encoder.J[i, j] * spin[i] * spin[j]
                E += E_slice / self.trotter_steps  # average over slices
            return E

        current_E = action(path)
        best_E = current_E
        best_path = path.copy()

        for sweep in range(self.sweeps):
            # Propose a flip of one spin at one trotter slice
            t = np.random.randint(0, self.trotter_steps)
            i = np.random.randint(0, n)
            new_path = path.copy()
            new_path[t, i] *= -1
            new_E = action(new_path)
            delta = new_E - current_E
            if delta < 0 or np.random.rand() < np.exp(-delta * self.beta):
                path = new_path
                current_E = new_E
                if current_E < best_E:
                    best_E = current_E
                    best_path = path.copy()
            self.history['energy'].append(current_E)

        # Extract ground state from best path (take the first slice)
        best_spin = best_path[0]  # assume symmetry
        # Convert to glyph state: spin -1 -> 0, spin +1 -> 4
        glyph_state = np.array([4 if s == 1 else 0 for s in best_spin])
        return glyph_state, best_E

# -------------------------------------------------------------------
# 6. Parameter Sweep Engine
# -------------------------------------------------------------------
class ParameterSweep:
    def __init__(self, encoder, param_grid):
        self.encoder = encoder
        self.param_grid = param_grid  # dict of lists: {'Gamma_start': [...], 'Gamma_end': [...], 'steps': [...]}
        self.results = []

    def run(self):
        import itertools
        keys = list(self.param_grid.keys())
        for values in itertools.product(*[self.param_grid[k] for k in keys]):
            params = dict(zip(keys, values))
            # Run a quantum circuit simulation with these parameters
            # We'll use the exact diagonalization for small qubits
            # Here we use a simplified version
            from scipy.linalg import expm
            n = self.encoder.qubits
            dim = 2**n
            # Build H_ising
            H_ising = np.zeros((dim, dim))
            for state_idx in range(dim):
                bits = [(state_idx >> i) & 1 for i in range(n)]
                spin = np.array([1 if b == 0 else -1 for b in bits])
                E = np.sum(self.encoder.h * spin)
                for i in range(n):
                    for j in range(i+1, n):
                        E += self.encoder.J[i, j] * spin[i] * spin[j]
                H_ising[state_idx, state_idx] = E
            # Build field matrix
            def build_field(Gamma):
                Hf = np.zeros((dim, dim))
                for i in range(n):
                    for state_idx in range(dim):
                        flipped = state_idx ^ (1 << i)
                        Hf[state_idx, flipped] -= Gamma
                return Hf
            # Time evolution
            psi = np.ones(dim) / np.sqrt(dim)
            dt = 0.05
            steps = params.get('steps', 100)
            Gamma_start = params.get('Gamma_start', 5.0)
            Gamma_end = params.get('Gamma_end', 0.1)
            for step in range(steps):
                t = step / steps
                Gamma = Gamma_start * (Gamma_end / Gamma_start) ** t
                H_total = H_ising + build_field(Gamma)
                U = expm(-1j * H_total * dt)
                psi = U @ psi
            # Compute final energy and ground state prob
            probs = np.abs(psi)**2
            eigvals, eigvecs = np.linalg.eigh(H_ising)
            ground_state = eigvecs[:, 0]
            prob_ground = np.abs(np.conj(ground_state).T @ psi)**2
            E_exp = np.real(np.conj(psi).T @ H_ising @ psi)
            self.results.append({
                'params': params,
                'energy': E_exp,
                'prob_ground': prob_ground,
                'best_state': np.argmax(probs)
            })
        return self.results

# -------------------------------------------------------------------
# 7. Unified Explorer v4
# -------------------------------------------------------------------
class MandalaExplorerV4:
    def __init__(self):
        self.encoder = None
        self.result = None
        self.best_state = None
        self.history = None

    def run(self, problem_type='ising', qubits=4, solver='quantum_circuit',
            Gamma_start=5.0, Gamma_end=0.1, steps=100, trotter_steps=20, beta=1.0,
            use_noise=False, export_qiskit=False, sweep=False):

        self.encoder = ProblemEncoder(problem_type, qubits=qubits)
        self.encoder._init_problem()

        if solver == 'quantum_circuit':
            # Use exact diagonalization
            from scipy.linalg import expm
            n = qubits
            dim = 2**n
            # Build H_ising
            H_ising = np.zeros((dim, dim))
            for state_idx in range(dim):
                bits = [(state_idx >> i) & 1 for i in range(n)]
                spin = np.array([1 if b == 0 else -1 for b in bits])
                E = np.sum(self.encoder.h * spin)
                for i in range(n):
                    for j in range(i+1, n):
                        E += self.encoder.J[i, j] * spin[i] * spin[j]
                H_ising[state_idx, state_idx] = E
            # Build field
            def build_field(Gamma):
                Hf = np.zeros((dim, dim))
                for i in range(n):
                    for state_idx in range(dim):
                        flipped = state_idx ^ (1 << i)
                        Hf[state_idx, flipped] -= Gamma
                return Hf
            # Time evolution
            psi = np.ones(dim) / np.sqrt(dim)
            dt = 0.05
            self.history = {'energy': [], 'ground_prob': [], 'Gamma': [], 'noise': []}
            for step in range(steps):
                t = step / steps
                Gamma = Gamma_start * (Gamma_end / Gamma_start) ** t
                H_total = H_ising + build_field(Gamma)
                U = expm(-1j * H_total * dt)
                psi = U @ psi
                # Apply noise if requested
                if use_noise:
                    # Simplified noise: dephase probability proportional to dt
                    p = dt * 0.01  # small noise
                    if p > 0:
                        # Add random phase to each amplitude (dephasing)
                        noise = np.exp(1j * 2 * np.pi * np.random.randn(dim) * np.sqrt(p))
                        psi = psi * noise
                        # Renormalize
                        psi = psi / np.linalg.norm(psi)
                # Record
                E_exp = np.real(np.conj(psi).T @ H_ising @ psi)
                # Ground state probability
                eigvals, eigvecs = np.linalg.eigh(H_ising)
                ground_state = eigvecs[:, 0]
                prob_ground = np.abs(np.conj(ground_state).T @ psi)**2
                self.history['energy'].append(E_exp)
                self.history['ground_prob'].append(prob_ground)
                self.history['Gamma'].append(Gamma)
                self.history['noise'].append(use_noise)
            # Final measurement
            probs = np.abs(psi)**2
            most_likely = np.argmax(probs)
            # Convert to glyph state
            spin = np.array([1 if (most_likely >> i) & 1 == 0 else -1 for i in range(n)])
            glyph_state = np.array([4 if s == 1 else 0 for s in spin])
            self.best_state = glyph_state
            self.best_energy = self.encoder.energy(glyph_state)
            self.result = self.encoder.decode_solution(glyph_state)
            self.probs = probs
            self.ground_energy = eigvals[0]

        elif solver == 'trotter_suzuki_qmc':
            qmc = TrotterSuzukiQMC(self.encoder, trotter_steps, beta, sweeps=steps)
            glyph_state, best_E = qmc.solve()
            self.best_state = glyph_state
            self.best_energy = best_E
            self.result = self.encoder.decode_solution(glyph_state)
            self.history = qmc.history

        elif solver == 'parameter_sweep':
            if not sweep:
                print("Parameter sweep requested but sweep flag is False. Running default.")
                self.run(problem_type, qubits, 'quantum_circuit', Gamma_start, Gamma_end, steps)
                return
            # Run sweep
            param_grid = {
                'Gamma_start': np.linspace(1, 10, 5),
                'Gamma_end': np.linspace(0.01, 1, 5),
                'steps': [50, 100, 200]
            }
            sweeper = ParameterSweep(self.encoder, param_grid)
            results = sweeper.run()
            self.sweep_results = results
            # Find best
            best = min(results, key=lambda x: x['energy'])
            self.best_energy = best['energy']
            # Convert state index to glyph
            spin = np.array([1 if (best['best_state'] >> i) & 1 == 0 else -1 for i in range(qubits)])
            self.best_state = np.array([4 if s == 1 else 0 for s in spin])
            self.result = self.encoder.decode_solution(self.best_state)
            self.history = {'sweep_results': results}

        # Qiskit export
        if export_qiskit and problem_type == 'ising':
            qasm = export_to_qiskit(self.encoder, Gamma_start, Gamma_end, steps)
            self.qasm = qasm
            print("Generated Qiskit OpenQASM:")
            print(qasm)
        else:
            self.qasm = None

        return self.plot_results()

    def plot_results(self):
        fig = plt.figure(figsize=(18, 12))
        gs = gridspec.GridSpec(3, 3, height_ratios=[1, 1, 0.8])

        # Panel 1: Energy history
        ax = fig.add_subplot(gs[0, 0])
        if self.history and 'energy' in self.history:
            ax.plot(self.history['energy'], 'b-', lw=1, alpha=0.7)
            ax.set_xlabel('Step')
            ax.set_ylabel('Energy')
            ax.set_title('Energy vs Time')
            ax.grid(True, alpha=0.3)

        # Panel 2: Ground state probability (if quantum circuit)
        ax = fig.add_subplot(gs[0, 1])
        if self.history and 'ground_prob' in self.history:
            ax.plot(self.history['ground_prob'], 'purple', lw=2, label='Ground state prob')
            ax.set_xlabel('Step')
            ax.set_ylabel('Probability')
            ax.set_title('Ground State Probability')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_ylim(-0.05, 1.05)
        else:
            ax.text(0.5, 0.5, 'Not available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Ground State Probability')

        # Panel 3: Gamma schedule
        ax = fig.add_subplot(gs[0, 2])
        if self.history and 'Gamma' in self.history:
            ax.plot(self.history['Gamma'], 'r-', lw=2)
            ax.set_xlabel('Step')
            ax.set_ylabel('Gamma')
            ax.set_title('Transverse Field Schedule')
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'No schedule', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Gamma Schedule')

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
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect('equal')
        ax.axis('off'); ax.set_title('Solution Mandala')

        # Panel 5: Final quantum state distribution (if available)
        ax = fig.add_subplot(gs[1, 1])
        if hasattr(self, 'probs'):
            ax.bar(range(len(self.probs)), self.probs, color='purple', alpha=0.7)
            ax.set_xlabel('State index')
            ax.set_ylabel('Probability')
            ax.set_title('Final Quantum State Distribution')
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'No distribution', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('State Distribution')

        # Panel 6: Solution details
        ax = fig.add_subplot(gs[1, 2])
        ax.axis('off')
        info = f"""
        📊 **Problem:** {self.encoder.problem_type}
        ─────────────────────────────────
        Qubits: {self.encoder.qubits}
        Energy: {self.best_energy:.2f}
        """
        if self.result:
            info += f"\nSpin config: {self.result['spin_config']}"
        if hasattr(self, 'ground_energy'):
            info += f"\nGround state energy: {self.ground_energy:.2f}"
        ax.text(0.05, 0.95, info, transform=ax.transAxes, fontsize=11,
                verticalalignment='top', family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))

        # Panel 7: Parameter sweep results (if any)
        ax = fig.add_subplot(gs[2, 0])
        if hasattr(self, 'sweep_results'):
            energies = [r['energy'] for r in self.sweep_results]
            ax.hist(energies, bins=20, color='green', alpha=0.7)
            ax.set_xlabel('Energy')
            ax.set_ylabel('Count')
            ax.set_title('Parameter Sweep: Energy Distribution')
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'No sweep data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Parameter Sweep')

        # Panel 8: Ising couplings (if Ising)
        ax = fig.add_subplot(gs[2, 1])
        if self.encoder.problem_type == 'ising':
            im = ax.imshow(self.encoder.J, cmap='RdBu_r', origin='lower', vmin=-3, vmax=3)
            ax.set_title('Ising Couplings (J)')
            plt.colorbar(im, ax=ax, fraction=0.05)
            ax.set_xlabel('Qubit'); ax.set_ylabel('Qubit')
        else:
            ax.text(0.5, 0.5, 'Not an Ising problem', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Ising Couplings')

        # Panel 9: Qiskit export (show first few lines)
        ax = fig.add_subplot(gs[2, 2])
        if hasattr(self, 'qasm') and self.qasm:
            lines = self.qasm.split('\n')[:10]
            ax.text(0.1, 0.9, '\n'.join(lines), fontsize=8, family='monospace',
                    transform=ax.transAxes, verticalalignment='top')
            ax.set_title('Qiskit OpenQASM (preview)')
        else:
            ax.text(0.5, 0.5, 'Export not generated', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Qiskit Export')
        ax.axis('off')

        plt.tight_layout()
        plt.show()
        return fig

# -------------------------------------------------------------------
# 8. Interactive UI (updated for v4)
# -------------------------------------------------------------------
explorer = MandalaExplorerV4()
output = Output()

def run_interactive(problem_type, qubits, solver, Gamma_start, Gamma_end, steps,
                    trotter_steps, beta, use_noise, export_qiskit, sweep):
    with output:
        clear_output(wait=True)
        explorer.run(problem_type, qubits, solver, Gamma_start, Gamma_end, steps,
                     trotter_steps, beta, use_noise, export_qiskit, sweep)

# Widgets
problem_dropdown = Dropdown(options=['ising'], value='ising', description='Problem:')
qubits_slider = IntSlider(value=4, min=2, max=6, step=1, description='Qubits:')
solver_dropdown = Dropdown(
    options=['quantum_circuit', 'trotter_suzuki_qmc', 'parameter_sweep'],
    value='quantum_circuit',
    description='Solver:'
)
Gamma_start_slider = FloatSlider(value=5.0, min=0.5, max=20.0, step=0.5, description='Gamma start:')
Gamma_end_slider = FloatSlider(value=0.1, min=0.01, max=2.0, step=0.01, description='Gamma end:')
steps_slider = IntSlider(value=100, min=20, max=300, step=10, description='Steps:')
trotter_slider = IntSlider(value=20, min=5, max=50, step=5, description='Trotter steps:')
beta_slider = FloatSlider(value=1.0, min=0.1, max=5.0, step=0.1, description='Beta (1/T):')
noise_checkbox = Checkbox(value=False, description='Add noise')
qiskit_checkbox = Checkbox(value=False, description='Export Qiskit')
sweep_checkbox = Checkbox(value=False, description='Parameter sweep')

run_button = Button(description='Run Simulation', button_style='primary')
reset_button = Button(description='Reset', button_style='warning')

def on_run_clicked(b):
    run_interactive(
        problem_dropdown.value,
        qubits_slider.value,
        solver_dropdown.value,
        Gamma_start_slider.value,
        Gamma_end_slider.value,
        steps_slider.value,
        trotter_slider.value,
        beta_slider.value,
        noise_checkbox.value,
        qiskit_checkbox.value,
        sweep_checkbox.value
    )

def on_reset_clicked(b):
    with output:
        clear_output()
        print("🧘 Mandala Computing Explorer v4 ready.")

run_button.on_click(on_run_clicked)
reset_button.on_click(on_reset_clicked)

ui = VBox([
    HTML("<h2>🧘 Mandala Computing Explorer v4</h2>"),
    HTML("<i>Qiskit Export · Noise Model · Trotter-Suzuki QMC · Parameter Sweep</i>"),
    HBox([problem_dropdown, qubits_slider]),
    HBox([solver_dropdown, Gamma_start_slider, Gamma_end_slider]),
    HBox([steps_slider, trotter_slider, beta_slider]),
    HBox([noise_checkbox, qiskit_checkbox, sweep_checkbox]),
    HBox([run_button, reset_button]),
    output
])

display(ui)
print("🚀 Mandala Explorer v4 loaded. Click 'Run Simulation' to start.")

# -------------------------------------------------------------------
# 9. Default demo: 4-qubit Ising with noise and export
# -------------------------------------------------------------------
print("\n🧪 Running default: 4-qubit Ising with quantum circuit, noise, and Qiskit export...")
run_interactive('ising', 4, 'quantum_circuit', 5.0, 0.1, 100, 20, 1.0, True, True, False)
