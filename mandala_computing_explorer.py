# ===================================================================
#  MANDALA COMPUTING EXPLORER v4
#  Qiskit Export · Trotter-Suzuki QMC · Parameter Sweep
#  Solvers are provided by quantum_mandala.py's QuantumMandalaComputer —
#  this file is UI/plotting only. See experiments/README.md.
#  ===================================================================

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from ipywidgets import interact, Dropdown, IntSlider, FloatSlider, VBox, HBox, Output, Button, Checkbox, Label, HTML
from IPython.display import display, clear_output
import warnings
warnings.filterwarnings('ignore')

from quantum_mandala import QuantumMandalaComputer, export_ising_qiskit
from octahedral_arithmetic import GLYPHS

# -------------------------------------------------------------------
# 1. Constants and Glyphs (canonical octahedral state glyphs, shared
#    with mandala_computer.py / quantum_mandala.py / glyphs/mandala.json)
# -------------------------------------------------------------------
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
# 3. Parameter Sweep Engine
# -------------------------------------------------------------------
class ParameterSweep:
    def __init__(self, J, h, param_grid):
        self.J = J
        self.h = h
        self.param_grid = param_grid  # dict of lists: {'Gamma_start': [...], 'Gamma_end': [...], 'steps': [...]}
        self.results = []

    def run(self):
        import itertools
        keys = list(self.param_grid.keys())
        for values in itertools.product(*[self.param_grid[k] for k in keys]):
            params = dict(zip(keys, values))
            qc = QuantumMandalaComputer(golden_depth=1, sacred_geometry=8)
            result = qc.transverse_field_ising_anneal(
                self.J, self.h,
                Gamma_start=params.get('Gamma_start', 5.0),
                Gamma_end=params.get('Gamma_end', 0.1),
                steps=params.get('steps', 100),
            )
            self.results.append({
                'params': params,
                'energy': result['final_energy'],
                'prob_ground': result['history']['ground_prob'][-1],
                'best_state': result['measured_state'],
            })
        return self.results

# -------------------------------------------------------------------
# 4. Unified Explorer v4
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
            qc = QuantumMandalaComputer(golden_depth=1, sacred_geometry=8)
            result = qc.transverse_field_ising_anneal(
                self.encoder.J, self.encoder.h,
                Gamma_start=Gamma_start, Gamma_end=Gamma_end, steps=steps,
                use_noise=use_noise,
            )
            self.history = result['history']
            self.probs = result['probs']
            self.ground_energy = result['ground_energy']
            glyph_state = np.array([4 if s == 1 else 0 for s in result['spin_config']])
            self.best_state = glyph_state
            self.best_energy = self.encoder.energy(glyph_state)
            self.result = self.encoder.decode_solution(glyph_state)

        elif solver == 'trotter_suzuki_qmc':
            qc = QuantumMandalaComputer(golden_depth=1, sacred_geometry=8)
            result = qc.trotter_suzuki_qmc(
                self.encoder.J, self.encoder.h,
                trotter_steps=trotter_steps, beta=beta, sweeps=steps,
            )
            glyph_state = np.array([4 if s == 1 else 0 for s in result['spin_config']])
            self.best_state = glyph_state
            self.best_energy = result['final_energy']
            self.result = self.encoder.decode_solution(glyph_state)
            self.history = result['history']

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
            sweeper = ParameterSweep(self.encoder.J, self.encoder.h, param_grid)
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
            qasm = export_ising_qiskit(self.encoder.J, self.encoder.h, Gamma_start, Gamma_end, steps)
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
# 5. Interactive UI (updated for v4)
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
    HTML("<i>Qiskit Export · Trotter-Suzuki QMC · Parameter Sweep</i>"),
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
# 6. Default demo: 4-qubit Ising with noise and export
# -------------------------------------------------------------------
print("\n🧪 Running default: 4-qubit Ising with quantum circuit, noise, and Qiskit export...")
run_interactive('ising', 4, 'quantum_circuit', 5.0, 0.1, 100, 20, 1.0, True, True, False)
