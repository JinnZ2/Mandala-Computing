import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from ipywidgets import interact, Dropdown, IntSlider, FloatSlider, VBox, HBox, Output, Button, HTML
from IPython.display import display, clear_output
import warnings
warnings.filterwarnings('ignore')

# -------------------------------------------------------------------
# 1. Octahedral Glyph System (8-state cells)
# -------------------------------------------------------------------
GLYPHS = ['◈', '◉', '◊', '○', '●', '◐', '◑', '◒']  # 8 glyphs representing states 0-7
GLYPH_MAP = {i: GLYPHS[i] for i in range(8)}

def int_to_glyph(n, width=1):
    """Convert integer to base-8 glyph sequence."""
    if n == 0:
        return GLYPHS[0]
    digits = []
    while n > 0:
        digits.append(GLYPHS[n % 8])
        n //= 8
    return ''.join(reversed(digits)).rjust(width, GLYPHS[0])

def glyph_to_int(glyph_str):
    """Convert glyph sequence back to integer."""
    n = 0
    for g in glyph_str:
        for i, glyph in enumerate(GLYPHS):
            if g == glyph:
                n = n * 8 + i
                break
    return n

# -------------------------------------------------------------------
# 2. Problem Encoder (Factorization)
# -------------------------------------------------------------------
class ProblemEncoder:
    def __init__(self, problem_type='factorization', N=143):
        self.problem_type = problem_type
        self.N = N
        self.cells = 0
        self.cell_states = None
        self.best_energy = float('inf')
        self.best_state = None
        
    def encode_factorization(self, N):
        """Encode N as energy landscape for factorization."""
        self.N = N
        # Auto-scale register size: cells per factor
        import math
        max_factor = int(math.isqrt(N))
        self.cells = len(str(max_factor))  # number of base-8 digits needed
        if self.cells < 1:
            self.cells = 1
        # Total cells: 2 * cells (one for each factor)
        self.total_cells = 2 * self.cells
        return self.total_cells
    
    def energy(self, state):
        """Compute energy of a given state (array of cell values 0-7)."""
        if self.problem_type == 'factorization':
            # Split state into two factors
            half = len(state) // 2
            f1_digits = state[:half]
            f2_digits = state[half:]
            # Convert base-8 digits to integer
            f1 = 0
            f2 = 0
            for d in f1_digits:
                f1 = f1 * 8 + d
            for d in f2_digits:
                f2 = f2 * 8 + d
            # Avoid zero factors
            if f1 < 2 or f2 < 2:
                return 1e6 + abs(f1 * f2 - self.N)
            return (f1 * f2 - self.N) ** 2
        elif self.problem_type == 'sat':
            # Simple 3-SAT with 3 variables, 2 clauses
            # State: 3 cells, each 0-7 (0-3=False, 4-7=True)
            # Clause 1: (x1 OR x2 OR x3)
            # Clause 2: (NOT x1 OR NOT x2 OR NOT x3)
            x1 = state[0] >= 4
            x2 = state[1] >= 4
            x3 = state[2] >= 4
            c1 = x1 or x2 or x3
            c2 = (not x1) or (not x2) or (not x3)
            unsatisfied = (not c1) + (not c2)
            return 2 * unsatisfied
        elif self.problem_type == 'graph_coloring':
            # Simple graph: triangle (3 nodes, each needs different color)
            # State: 3 cells, each 0-7 (color index)
            colors = state[:3]
            violations = 0
            if colors[0] == colors[1]:
                violations += 2
            if colors[1] == colors[2]:
                violations += 2
            if colors[0] == colors[2]:
                violations += 2
            # PHI = golden ratio penalty for satisfied edges (simplified)
            return violations - 0.618 * (3 - violations)
        return 0
    
    def decode_solution(self, state):
        """Decode state back to human-readable solution."""
        if self.problem_type == 'factorization':
            half = len(state) // 2
            f1 = 0
            f2 = 0
            for d in state[:half]:
                f1 = f1 * 8 + d
            for d in state[half:]:
                f2 = f2 * 8 + d
            if f1 < 2 or f2 < 2:
                return None
            if f1 * f2 == self.N:
                return {'factors': [f1, f2], 'verified': True}
            else:
                return {'factors': [f1, f2], 'verified': False}
        elif self.problem_type == 'sat':
            x1 = state[0] >= 4
            x2 = state[1] >= 4
            x3 = state[2] >= 4
            return {'assignment': [x1, x2, x3], 'clauses_satisfied': (x1 or x2 or x3) and ((not x1) or (not x2) or (not x3))}
        elif self.problem_type == 'graph_coloring':
            return {'colors': state[:3], 'valid': len(set(state[:3])) == 3}
        return None

# -------------------------------------------------------------------
# 3. Simulated Annealing Solver
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
            # Cooling schedule (geometric)
            t = step / self.steps
            T = self.T_start * (self.T_end / self.T_start) ** t
            self.history['temperature'].append(T)
            
            # Propose move: flip one cell to a random new state (0-7)
            new_state = state.copy()
            cell_idx = np.random.randint(0, n_cells)
            new_state[cell_idx] = np.random.randint(0, 8)
            
            new_energy = self.encoder.energy(new_state)
            delta_E = new_energy - current_energy
            
            # Acceptance probability (Metropolis)
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
            
            # Early exit if energy is zero (solution found)
            if best_energy == 0:
                break
        
        return best_state, best_energy

# -------------------------------------------------------------------
# 4. Parallel Tempering Solver
# -------------------------------------------------------------------
class ParallelTempering:
    def __init__(self, encoder, n_replicas=5, T_min=0.01, T_max=10.0, steps=3000):
        self.encoder = encoder
        self.n_replicas = n_replicas
        self.T_min = T_min
        self.T_max = T_max
        self.steps = steps
        self.history = {'energy': [], 'swap_acceptance': []}
        
    def solve(self):
        n_cells = self.encoder.total_cells
        # Initialize replicas at different temperatures
        T_list = np.logspace(np.log10(self.T_min), np.log10(self.T_max), self.n_replicas)
        states = [np.random.randint(0, 8, n_cells) for _ in range(self.n_replicas)]
        energies = [self.encoder.energy(s) for s in states]
        
        best_state = states[0].copy()
        best_energy = energies[0]
        
        self.history = {'energy': [[] for _ in range(self.n_replicas)], 
                        'swap_acceptance': []}
        
        for step in range(self.steps):
            # Parallel Monte Carlo sweeps
            for r in range(self.n_replicas):
                # Propose move
                new_state = states[r].copy()
                cell_idx = np.random.randint(0, n_cells)
                new_state[cell_idx] = np.random.randint(0, 8)
                new_energy = self.encoder.energy(new_state)
                delta_E = new_energy - energies[r]
                
                if delta_E < 0 or np.random.rand() < np.exp(-delta_E / (T_list[r] + 1e-10)):
                    states[r] = new_state
                    energies[r] = new_energy
                    
                    if energies[r] < best_energy:
                        best_state = states[r].copy()
                        best_energy = energies[r]
            
            # Attempt replica swaps (every few steps)
            if step % 10 == 0 and self.n_replicas > 1:
                for r in range(self.n_replicas - 1):
                    # Swap adjacent replicas with probability based on energy difference
                    delta = (energies[r+1] - energies[r]) * (1/T_list[r+1] - 1/T_list[r])
                    if delta < 0 or np.random.rand() < np.exp(delta):
                        # Swap states and energies
                        states[r], states[r+1] = states[r+1], states[r]
                        energies[r], energies[r+1] = energies[r+1], energies[r]
                        self.history['swap_acceptance'].append(1)
                    else:
                        self.history['swap_acceptance'].append(0)
            
            # Record energy history
            for r in range(self.n_replicas):
                self.history['energy'][r].append(energies[r])
            
            if best_energy == 0:
                break
        
        return best_state, best_energy

# -------------------------------------------------------------------
# 5. Interactive Simulation
# -------------------------------------------------------------------
class MandalaExplorer:
    def __init__(self):
        self.encoder = None
        self.solver = None
        self.result = None
        self.history = None
        
    def run(self, problem_type='factorization', N=143, solver_type='simulated_annealing', 
            T_start=5.0, T_end=0.001, steps=5000, n_replicas=5):
        # Create encoder
        self.encoder = ProblemEncoder(problem_type, N)
        if problem_type == 'factorization':
            self.encoder.total_cells = self.encoder.encode_factorization(N)
        elif problem_type == 'sat':
            self.encoder.total_cells = 3  # 3 variables
        elif problem_type == 'graph_coloring':
            self.encoder.total_cells = 3  # 3 nodes
            
        # Run solver
        if solver_type == 'simulated_annealing':
            self.solver = SimulatedAnnealing(self.encoder, T_start, T_end, steps)
            best_state, best_energy = self.solver.solve()
            self.history = self.solver.history
        else:  # parallel_tempering
            self.solver = ParallelTempering(self.encoder, n_replicas, 0.01, 10.0, steps)
            best_state, best_energy = self.solver.solve()
            self.history = self.solver.history
            
        self.result = self.encoder.decode_solution(best_state)
        self.best_state = best_state
        self.best_energy = best_energy
        
        return self.plot_results()
    
    def plot_results(self):
        fig = plt.figure(figsize=(16, 10))
        gs = gridspec.GridSpec(2, 3, height_ratios=[1, 1])
        
        # Panel 1: Energy landscape (history)
        ax = fig.add_subplot(gs[0, 0])
        if isinstance(self.solver, SimulatedAnnealing):
            ax.plot(self.history['energy'], 'b-', lw=1, alpha=0.7)
            ax.set_xlabel('Step')
            ax.set_ylabel('Energy')
            ax.set_title('Energy vs Time (Simulated Annealing)')
            ax.grid(True, alpha=0.3)
            # Add temperature overlay
            ax2 = ax.twinx()
            ax2.plot(self.history['temperature'], 'r--', lw=1, alpha=0.5)
            ax2.set_ylabel('Temperature', color='r')
            ax2.tick_params(axis='y', labelcolor='r')
        else:
            # Parallel tempering: show all replicas
            for r in range(len(self.history['energy'])):
                ax.plot(self.history['energy'][r], lw=1, alpha=0.5, label=f'Replica {r}')
            ax.set_xlabel('Step')
            ax.set_ylabel('Energy')
            ax.set_title('Energy vs Time (Parallel Tempering)')
            ax.legend(loc='upper right', fontsize=8)
            ax.grid(True, alpha=0.3)
        
        # Panel 2: Acceptance rate
        ax = fig.add_subplot(gs[0, 1])
        if isinstance(self.solver, SimulatedAnnealing):
            if len(self.history['acceptance']) > 0:
                # Running average of acceptance
                window = min(100, len(self.history['acceptance']))
                acc_avg = np.convolve(self.history['acceptance'], np.ones(window)/window, mode='valid')
                ax.plot(acc_avg, 'g-', lw=2)
                ax.set_xlabel('Step')
                ax.set_ylabel('Acceptance rate')
                ax.set_title('Acceptance Rate (window={})'.format(window))
                ax.set_ylim(-0.05, 1.05)
                ax.grid(True, alpha=0.3)
        else:
            # Swap acceptance for parallel tempering
            if len(self.history['swap_acceptance']) > 0:
                window = min(50, len(self.history['swap_acceptance']))
                acc_avg = np.convolve(self.history['swap_acceptance'], np.ones(window)/window, mode='valid')
                ax.plot(acc_avg, 'purple', lw=2)
                ax.set_xlabel('Swap attempt')
                ax.set_ylabel('Swap acceptance')
                ax.set_title('Replica Swap Acceptance')
                ax.set_ylim(-0.05, 1.05)
                ax.grid(True, alpha=0.3)
        
        # Panel 3: State visualization (glyphs)
        ax = fig.add_subplot(gs[0, 2])
        n_cells = len(self.best_state)
        # Create a circular mandala-like arrangement
        angles = np.linspace(0, 2*np.pi, n_cells, endpoint=False)
        radius = 0.4
        for i, (state, angle) in enumerate(zip(self.best_state, angles)):
            x = 0.5 + radius * np.cos(angle)
            y = 0.5 + radius * np.sin(angle)
            ax.text(x, y, GLYPHS[state], fontsize=24, ha='center', va='center',
                   bbox=dict(boxstyle='circle', facecolor='lightblue', alpha=0.7))
            # Draw connecting lines (mandala pattern)
            for j in range(i+1, n_cells):
                x2 = 0.5 + radius * np.cos(angles[j])
                y2 = 0.5 + radius * np.sin(angles[j])
                ax.plot([x, x2], [y, y2], 'k-', alpha=0.2, lw=0.5)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('Solution State (Glyphs)')
        
        # Panel 4: Problem info & solution
        ax = fig.add_subplot(gs[1, 0])
        ax.axis('off')
        info = f"""
        📊 **Problem Information**
        ─────────────────────────
        Problem: {self.encoder.problem_type}
        """
        if self.encoder.problem_type == 'factorization':
            info += f"N = {self.encoder.N}"
        info += f"\nCells: {self.encoder.total_cells}"
        info += f"\nEnergy: {self.best_energy:.2f}"
        info += f"\n\n🔍 **Solution**"
        if self.result:
            if self.encoder.problem_type == 'factorization':
                if self.result['verified']:
                    info += f"\n✅ {self.result['factors'][0]} × {self.result['factors'][1]} = {self.encoder.N}"
                    info += f"\nGlyph: {int_to_glyph(self.result['factors'][0])} × {int_to_glyph(self.result['factors'][1])} = {int_to_glyph(self.encoder.N)}"
                else:
                    info += f"\n❌ {self.result['factors'][0]} × {self.result['factors'][1]} = {self.result['factors'][0]*self.result['factors'][1]} (≠ {self.encoder.N})"
            elif self.encoder.problem_type == 'sat':
                info += f"\nAssignment: {self.result['assignment']}"
                info += f"\nClauses satisfied: {self.result['clauses_satisfied']}"
            elif self.encoder.problem_type == 'graph_coloring':
                info += f"\nColors: {self.result['colors']}"
                info += f"\nValid: {self.result['valid']}"
        else:
            info += "\nNo solution found yet."
        ax.text(0.05, 0.95, info, transform=ax.transAxes, fontsize=11,
                verticalalignment='top', family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))
        
        # Panel 5: Temperature / replica profile
        ax = fig.add_subplot(gs[1, 1])
        if isinstance(self.solver, SimulatedAnnealing):
            # Show energy vs temperature
            if len(self.history['energy']) > 10:
                # Sample every 10 steps
                energies = np.array(self.history['energy'][::10])
                temps = np.array(self.history['temperature'][::10])
                ax.scatter(temps, energies, s=10, alpha=0.5, c='blue')
                ax.set_xlabel('Temperature')
                ax.set_ylabel('Energy')
                ax.set_title('Energy vs Temperature')
                ax.grid(True, alpha=0.3)
                ax.set_xscale('log')
        else:
            # Show replica temperatures and their final energies
            T_list = np.logspace(np.log10(0.01), np.log10(10.0), self.solver.n_replicas)
            final_energies = [self.history['energy'][r][-1] if len(self.history['energy'][r]) > 0 else 0 
                             for r in range(self.solver.n_replicas)]
            ax.scatter(T_list, final_energies, s=50, c='purple', alpha=0.7)
            ax.set_xlabel('Replica Temperature')
            ax.set_ylabel('Final Energy')
            ax.set_title('Replica Final Energies')
            ax.grid(True, alpha=0.3)
            ax.set_xscale('log')
        
        # Panel 6: Energy landscape preview (3D-like)
        ax = fig.add_subplot(gs[1, 2])
        if self.encoder.problem_type == 'factorization' and self.encoder.total_cells <= 4:
            # Show a 2D slice of the landscape (fix some cells)
            n_cells = self.encoder.total_cells
            half = n_cells // 2
            # Fix the second factor to its best value (if available)
            if self.result and self.result.get('verified'):
                f2 = self.result['factors'][1]
                # Convert f2 to base-8 digits
                f2_digits = []
                temp = f2
                for _ in range(half):
                    f2_digits.append(temp % 8)
                    temp //= 8
                f2_digits = f2_digits[::-1]
                # Scan first factor values
                f1_vals = range(2, 100)
                energies = []
                for f1 in f1_vals:
                    # Convert f1 to base-8 digits
                    f1_digits = []
                    temp = f1
                    for _ in range(half):
                        f1_digits.append(temp % 8)
                        temp //= 8
                    f1_digits = f1_digits[::-1]
                    # Pad if needed
                    while len(f1_digits) < half:
                        f1_digits = [0] + f1_digits
                    state = f1_digits + f2_digits
                    energies.append(self.encoder.energy(state))
                ax.plot(f1_vals, energies, 'b-', lw=2)
                ax.axhline(y=0, color='r', linestyle='--', alpha=0.5, label='Solution (E=0)')
                ax.set_xlabel('Factor 1 value')
                ax.set_ylabel('Energy')
                ax.set_title('Energy Landscape Slice')
                ax.grid(True, alpha=0.3)
                ax.legend()
            else:
                ax.text(0.5, 0.5, 'Run solver to see landscape', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Energy Landscape')
        else:
            ax.text(0.5, 0.5, 'Landscape view available\nfor factorization with ≤4 cells', 
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Energy Landscape')
        
        plt.tight_layout()
        plt.show()
        return fig

# -------------------------------------------------------------------
# 6. Interactive Widgets
# -------------------------------------------------------------------
explorer = MandalaExplorer()
output = Output()

def run_interactive(problem_type, N, solver_type, T_start, T_end, steps, n_replicas):
    with output:
        clear_output(wait=True)
        explorer.run(problem_type, N, solver_type, T_start, T_end, steps, n_replicas)

# Widgets
problem_dropdown = Dropdown(
    options=['factorization', 'sat', 'graph_coloring'],
    value='factorization',
    description='Problem:'
)

N_slider = IntSlider(
    value=143, min=15, max=1000, step=1,
    description='N (factorization):'
)

solver_dropdown = Dropdown(
    options=['simulated_annealing', 'parallel_tempering'],
    value='simulated_annealing',
    description='Solver:'
)

T_start_slider = FloatSlider(
    value=5.0, min=0.5, max=20.0, step=0.5,
    description='Start Temp:'
)

T_end_slider = FloatSlider(
    value=0.001, min=0.0001, max=1.0, step=0.0005,
    description='End Temp:'
)

steps_slider = IntSlider(
    value=5000, min=1000, max=20000, step=1000,
    description='Steps:'
)

replicas_slider = IntSlider(
    value=5, min=2, max=10, step=1,
    description='Replicas:'
)

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
        replicas_slider.value
    )

def on_reset_clicked(b):
    with output:
        clear_output()
        print("Ready. Click 'Run Simulation' to start.")

run_button.on_click(on_run_clicked)
reset_button.on_click(on_reset_clicked)

# Layout
ui = VBox([
    HTML("<h2>🧘 Mandala Computing Explorer</h2>"),
    HTML("<p><i>Explore computational models inspired by fractal geometry, mandala structures, and golden ratio dynamics.</i></p>"),
    HBox([problem_dropdown, N_slider]),
    HBox([solver_dropdown, T_start_slider, T_end_slider]),
    HBox([steps_slider, replicas_slider]),
    HBox([run_button, reset_button]),
    output
])

display(ui)
print("🚀 Ready! Select parameters and click 'Run Simulation'.")
