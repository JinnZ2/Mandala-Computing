# ===================================================================
#  CROSS-DISCIPLINARY CONSTANT SWAPPING SIMULATOR
#  Mix physics, chemistry, biology, and mechanics constants to search
#  for falsifiable, testable experiments — via the Mandala engine.
#  ===================================================================

import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import interact, Dropdown, Button, VBox, HBox, Output, Label, FloatSlider, IntSlider, HTML
from IPython.display import display, clear_output
from typing import Dict
import warnings
warnings.filterwarnings('ignore')

from mandala_computer import MandalaComputer

# -------------------------------------------------------------------
# 1. Constants database
# -------------------------------------------------------------------
constants = {
    'G': {'value': 6.674e-11, 'unit': 'N·m²/kg²', 'category': 'mechanics', 'label': 'Gravitational constant', 'measurable': 'force (N)', 'apparatus': 'torsion balance, masses'},
    'k_e': {'value': 8.988e9, 'unit': 'N·m²/C²', 'category': 'electromagnetism', 'label': 'Coulomb constant', 'measurable': 'force (N)', 'apparatus': 'electroscope, charged spheres'},
    'k': {'value': 10.0, 'unit': 'N/m', 'category': 'mechanics', 'label': 'Spring constant (typical)', 'measurable': 'displacement (m)', 'apparatus': 'spring, masses, ruler'},
    'R': {'value': 8.314, 'unit': 'J/(mol·K)', 'category': 'thermodynamics', 'label': 'Gas constant', 'measurable': 'pressure (Pa)', 'apparatus': 'piston, manometer, thermometer'},
    'h': {'value': 6.626e-34, 'unit': 'J·s', 'category': 'quantum', 'label': 'Planck constant', 'measurable': 'photon energy (eV)', 'apparatus': 'photodiode, monochromator, LED'},
    'k_B': {'value': 1.381e-23, 'unit': 'J/K', 'category': 'stat mech', 'label': 'Boltzmann constant', 'measurable': 'entropy (J/K)', 'apparatus': 'calorimeter, thermometer'},
    'lambda': {'value': 0.693, 'unit': '1/s', 'category': 'nuclear', 'label': 'Decay constant (approx)', 'measurable': 'counts per minute', 'apparatus': 'Geiger counter, radioactive sample'},
    'Vmax': {'value': 100.0, 'unit': 'µmol/min', 'category': 'biochem', 'label': 'Max enzyme velocity', 'measurable': 'product concentration (µM)', 'apparatus': 'spectrophotometer, cuvette, enzyme solution'},
    'Km': {'value': 10.0, 'unit': 'µM', 'category': 'biochem', 'label': 'Michaelis constant', 'measurable': 'substrate concentration (µM)', 'apparatus': 'spectrophotometer, cuvette, enzyme solution'},
    'r': {'value': 0.5, 'unit': '1/year', 'category': 'ecology', 'label': 'Population growth rate', 'measurable': 'population count', 'apparatus': 'microscope, petri dish, nutrient agar'},
    'K': {'value': 1000.0, 'unit': 'individuals', 'category': 'ecology', 'label': 'Carrying capacity', 'measurable': 'population count at steady state', 'apparatus': 'microscope, petri dish, nutrient agar'},
    'c': {'value': 3.0e8, 'unit': 'm/s', 'category': 'relativity', 'label': 'Speed of light', 'measurable': 'time-of-flight (s)', 'apparatus': 'laser, mirror, photodetector, oscilloscope'},
    'mu0': {'value': 4*np.pi*1e-7, 'unit': 'H/m', 'category': 'electromagnetism', 'label': 'Permeability of free space', 'measurable': 'inductance (H)', 'apparatus': 'solenoid, LCR meter'},
    'epsilon0': {'value': 8.854e-12, 'unit': 'F/m', 'category': 'electromagnetism', 'label': 'Permittivity of free space', 'measurable': 'capacitance (F)', 'apparatus': 'parallel-plate capacitor, LCR meter'},
}

# -------------------------------------------------------------------
# 2. Equations database — expression, function, and the apparatus that
#    would measure its output (used by the self-consistency search below).
# -------------------------------------------------------------------
equations = {
    'Newtonian Gravity': {
        'expr': 'F = G * M1 * M2 / r^2',
        'func': lambda G, M1=1e3, M2=1e3, r=np.linspace(0.1, 10, 100): G * M1 * M2 / r**2,
        'constants': ['G'],
        'x_label': 'Distance (m)',
        'y_label': 'Force (N)',
        'description': 'Gravitational force between two masses.',
        'experiment': {
            'title': 'Cavendish-style torsion balance',
            'setup': 'Two large lead spheres (M1, M2) at varying distance r. Measure torque via a fiber.',
            'variables': 'Independent: r. Dependent: F (via torsion angle).',
        }
    },
    'Coulomb\'s Law': {
        'expr': 'F = k_e * q1 * q2 / r^2',
        'func': lambda k_e, q1=1e-6, q2=1e-6, r=np.linspace(0.01, 1, 100): k_e * q1 * q2 / r**2,
        'constants': ['k_e'],
        'x_label': 'Distance (m)',
        'y_label': 'Force (N)',
        'description': 'Electrostatic force between two charges.',
        'experiment': {
            'title': 'Coulomb balance',
            'setup': 'Two charged spheres (q1, q2) at variable distance r. Measure force with a torsion balance.',
            'variables': 'Independent: r. Dependent: F.',
        }
    },
    'Hooke\'s Law': {
        'expr': 'F = -k * x',
        'func': lambda k, x=np.linspace(-1, 1, 100): -k * x,
        'constants': ['k'],
        'x_label': 'Displacement (m)',
        'y_label': 'Force (N)',
        'description': 'Spring force (restoring).',
        'experiment': {
            'title': 'Spring constant measurement',
            'setup': 'Attach masses to spring, measure extension x. Plot F vs x.',
            'variables': 'Independent: x (displacement). Dependent: F.',
        }
    },
    'Ideal Gas Law': {
        'expr': 'P = nRT / V',
        'func': lambda R, n=1, T=300, V=np.linspace(0.01, 1, 100): n * R * T / V,
        'constants': ['R'],
        'x_label': 'Volume (m³)',
        'y_label': 'Pressure (Pa)',
        'description': 'Pressure vs volume for ideal gas.',
        'experiment': {
            'title': "Boyle's law apparatus",
            'setup': 'Gas in a piston, measure P as V changes at constant T.',
            'variables': 'Independent: V. Dependent: P.',
        }
    },
    'Planck\'s Relation': {
        'expr': 'E = h * nu',
        'func': lambda h, nu=np.linspace(1e14, 1e15, 100): h * nu,
        'constants': ['h'],
        'x_label': 'Frequency (Hz)',
        'y_label': 'Energy (J)',
        'description': 'Photon energy vs frequency.',
        'experiment': {
            'title': 'Photoelectric / LED photon-energy measurement',
            'setup': 'Shine monochromatic light of frequency nu on a photodiode; read photon energy via stopping voltage.',
            'variables': 'Independent: nu (frequency). Dependent: E (photon energy).',
        }
    },
    'Boltzmann Entropy': {
        'expr': 'S = k_B * ln(W)',
        'func': lambda k_B, W=np.linspace(1, 100, 100): k_B * np.log(W),
        'constants': ['k_B'],
        'x_label': 'Microstates (W)',
        'y_label': 'Entropy (J/K)',
        'description': 'Entropy vs number of microstates.',
        'experiment': {
            'title': 'Calorimetric entropy measurement',
            'setup': 'Vary the number of accessible microstates W in a thermal system and read entropy change with a calorimeter.',
            'variables': 'Independent: W (microstates). Dependent: S (entropy).',
        }
    },
    'Radioactive Decay': {
        'expr': 'N(t) = N0 * exp(-lambda * t)',
        'func': lambda lambda_, N0=100, t=np.linspace(0, 10, 100): N0 * np.exp(-lambda_ * t),
        'constants': ['lambda'],
        'x_label': 'Time (s)',
        'y_label': 'Remaining nuclei',
        'description': 'Exponential decay of radioactive sample.',
        'experiment': {
            'title': 'Geiger-counter decay curve',
            'setup': 'Monitor count rate of a radioactive sample over time with a Geiger counter.',
            'variables': 'Independent: t (time). Dependent: N(t) (remaining nuclei / count rate).',
        }
    },
    'Michaelis‑Menten': {
        'expr': 'v = Vmax * [S] / (Km + [S])',
        'func': lambda Vmax, Km, S=np.linspace(0, 100, 100): Vmax * S / (Km + S),
        'constants': ['Vmax', 'Km'],
        'x_label': 'Substrate concentration [S] (µM)',
        'y_label': 'Reaction velocity (µmol/min)',
        'description': 'Enzyme kinetics (saturation curve).',
        'experiment': {
            'title': 'Enzyme assay with spectrophotometer',
            'setup': 'Vary substrate [S], measure product formation rate v.',
            'variables': 'Independent: [S]. Dependent: v.',
        }
    },
    'Logistic Growth': {
        'expr': 'dN/dt = r * N * (1 - N/K)',
        'func': lambda r, K, N=np.linspace(0, 1200, 100): r * N * (1 - N/K),
        'constants': ['r', 'K'],
        'x_label': 'Population N',
        'y_label': 'Growth rate dN/dt',
        'description': 'Population growth with carrying capacity.',
        'experiment': {
            'title': 'Bacterial growth curve',
            'setup': 'Monitor bacterial population N over time in a chemostat.',
            'variables': 'Independent: N. Dependent: dN/dt.',
        }
    },
    'Mass‑Spring Oscillator': {
        'expr': 'omega = sqrt(k/m)',
        'func': lambda k, m=1.0, x=None: np.sqrt(k/m),
        'constants': ['k'],
        'x_label': 'Mass (kg)',
        'y_label': 'Angular frequency (rad/s)',
        'description': 'Natural frequency of mass-spring system.',
        'special': True,  # plotted directly against mass; not run through the generic search below
    }
}

# Free-variable defaults shared by plotting and the self-consistency search.
# Exactly one entry per equation (besides 'Mass-Spring Oscillator') is an
# array -- that's the swept/free variable.
DEFAULT_FREE_PARAMS = {
    'Newtonian Gravity': {'M1': 1e3, 'M2': 1e3, 'r': np.linspace(0.1, 10, 100)},
    'Coulomb\'s Law': {'q1': 1e-6, 'q2': 1e-6, 'r': np.linspace(0.01, 1, 100)},
    'Hooke\'s Law': {'x': np.linspace(-1, 1, 100)},
    'Ideal Gas Law': {'n': 1, 'T': 300, 'V': np.linspace(0.01, 1, 100)},
    'Planck\'s Relation': {'nu': np.linspace(1e14, 1e15, 100)},
    'Boltzmann Entropy': {'W': np.linspace(1, 100, 100)},
    'Radioactive Decay': {'N0': 100, 't': np.linspace(0, 10, 100)},
    'Michaelis‑Menten': {'S': np.linspace(0, 100, 100)},
    'Logistic Growth': {'N': np.linspace(0, 1200, 100)},
}

# -------------------------------------------------------------------
# 3. Helper: suggest similar constants (by order of magnitude and category)
# -------------------------------------------------------------------
def suggest_similar_constants(const_name, all_constants=constants):
    """Return a list of constant names similar in magnitude and/or category."""
    original = all_constants[const_name]
    orig_val = original['value']
    orig_cat = original['category']
    log_orig = np.log10(abs(orig_val)) if orig_val != 0 else 0
    suggestions = []
    for name, c in all_constants.items():
        if name == const_name:
            continue
        val = c['value']
        if val == 0:
            continue
        log_val = np.log10(abs(val))
        diff = abs(log_val - log_orig)
        # Similar if within 3 orders of magnitude or same category
        if diff <= 3 or c['category'] == orig_cat:
            suggestions.append((name, diff, c['category']))
    suggestions.sort(key=lambda x: x[1])
    return suggestions

# -------------------------------------------------------------------
# 4. Plotting function for swapped equations
# -------------------------------------------------------------------
def plot_swapped_equation(eq_name, new_constants, swapped_info, range_params=None):
    """
    eq_name: name of equation
    new_constants: dict mapping constant name (in eq) to new constant object
    swapped_info: list of strings for annotation
    """
    eq = equations[eq_name]

    if eq.get('special', False):
        # Mass-spring oscillator: plot omega vs mass directly.
        k_const = new_constants.get('k', constants['k'])
        masses = np.linspace(0.1, 10, 100)
        omega = np.sqrt(k_const['value'] / masses)
        plt.plot(masses, omega, 'b-', lw=2)
        plt.xlabel('Mass (kg)')
        plt.ylabel('Angular frequency (rad/s)')
        plt.title(f"{eq_name} with k = {k_const['value']:.2e} {k_const['unit']}")
        plt.grid(True, alpha=0.3)
        textstr = "Swapped constants:\n" + "\n".join(f"{k}: {v['value']:.2e} {v['unit']}" for k, v in new_constants.items())
        plt.annotate(textstr, xy=(0.05, 0.95), xycoords='axes fraction', fontsize=9,
                     verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        return

    # Build the argument list: swapped constant(s) positionally, in the
    # order eq['constants'] declares them, plus the equation's default
    # free-variable sweep as keyword arguments.
    const_list = eq['constants']
    const_values = {c: new_constants[c]['value'] if c in new_constants else constants[c]['value']
                     for c in const_list}
    kwargs = dict(DEFAULT_FREE_PARAMS.get(eq_name, {}))
    args = [const_values[c] for c in const_list]

    fig, ax = plt.subplots(figsize=(8, 5))
    x_key = next(k for k, v in kwargs.items() if isinstance(v, np.ndarray))
    x_data = kwargs[x_key]
    y_data = eq['func'](*args, **kwargs)
    ax.plot(x_data, y_data, color='blue', lw=2)
    ax.set_xlabel(eq['x_label'])
    ax.set_ylabel(eq['y_label'])

    const_to_replace = list(new_constants.keys())[0] if new_constants else const_list[0]
    new_value = const_values[const_to_replace]
    ax.set_title(f"{eq_name} with {const_to_replace} = {new_value:.2e} {constants[const_to_replace]['unit']}")
    ax.grid(True, alpha=0.3)

    expr = eq['expr']
    for c in const_list:
        expr = expr.replace(c, f"{c}={const_values[c]:.2e}")
    ax.annotate(expr, xy=(0.05, 0.95), xycoords='axes fraction', fontsize=9,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    plt.show()

# -------------------------------------------------------------------
# 5. Self-consistency search — replaces the old text-template experiment
#    generator with a real search over MandalaComputer.encode_optimization.
#
#    A swap doesn't have a "correct answer" to converge to; instead we ask
#    whether there EXISTS an operating point (a value of the equation's free
#    variable) where the swapped equation's output falls in a plausible
#    detectable range. The cost function is 0 exactly there, so relaxing to
#    the ground state finds that operating point (or shows none exists in
#    the searched range) -- a falsifiable numeric prediction instead of a
#    narrative guess. See experiments/README.md.
# -------------------------------------------------------------------

# Heuristic "plausible modern lab sensitivity" band: roughly a sensitive
# torsion balance (~1e-11 N) up to a bathroom-scale-sized reading. This is
# a single broad order-of-magnitude judgment call, not a precise
# per-instrument claim -- deliberately wide so the search is about whether
# *any* detectable regime exists, not about hitting an exact number.
DETECTABLE_MIN = 1e-12
DETECTABLE_MAX = 1e6

SEARCH_DIGITS = 4          # base-8 cells encoding the free-variable index (8^4 = 4096 samples)
SEARCH_GOLDEN_DEPTH = 3    # bloom_mandala(golden_depth=3) yields 7 cells >= SEARCH_DIGITS
SEARCH_X_MIN = 1e-6
SEARCH_X_MAX = 1e6


def _decode_free_variable(states) -> float:
    """Base-8 cell states -> log-uniform sample in [SEARCH_X_MIN, SEARCH_X_MAX]."""
    idx = 0
    for s in states[:SEARCH_DIGITS]:
        idx = idx * 8 + s
    max_idx = 8 ** SEARCH_DIGITS - 1
    frac = idx / max_idx
    return SEARCH_X_MIN * (SEARCH_X_MAX / SEARCH_X_MIN) ** frac


def _evaluate_swapped_equation(eq_name: str, const_swap: str, new_const_obj: dict, x: float):
    eq = equations[eq_name]
    const_list = eq['constants']
    const_values = {c: (new_const_obj['value'] if c == const_swap else constants[c]['value'])
                     for c in const_list}
    free_params = DEFAULT_FREE_PARAMS.get(eq_name, {})
    free_var = next((k for k, v in free_params.items() if isinstance(v, np.ndarray)), None)
    kwargs = dict(free_params)
    if free_var:
        kwargs[free_var] = x
    args = [const_values[c] for c in const_list]
    try:
        y = eq['func'](*args, **kwargs)
    except (OverflowError, ValueError, ZeroDivisionError):
        return free_var, float('inf')
    return free_var, float(np.abs(np.atleast_1d(y)).flat[0])


def _consistency_cost(y_val: float) -> float:
    """0 when |y| falls in the detectable band; log-distance to the nearest edge otherwise."""
    if not np.isfinite(y_val) or y_val <= 0:
        return 12.0  # roughly the decade-width of the search band
    log_y = math.log10(y_val)
    log_min, log_max = math.log10(DETECTABLE_MIN), math.log10(DETECTABLE_MAX)
    if log_min <= log_y <= log_max:
        return 0.0
    return min(abs(log_y - log_min), abs(log_y - log_max))


def run_self_consistency_search(eq_name: str, const_swap: str, new_const_obj: dict, quick: bool = True) -> Dict:
    """
    Encode "does a detectable operating point exist for this swap" as an
    optimization problem and relax MandalaComputer to its ground state.
    """
    eq = equations[eq_name]
    if eq.get('special'):
        return {"error": f"Self-consistency search not implemented for '{eq_name}' yet."}

    def cost_fn(states):
        x = _decode_free_variable(states)
        _, y_val = _evaluate_swapped_equation(eq_name, const_swap, new_const_obj, x)
        return _consistency_cost(y_val)

    computer = MandalaComputer(golden_depth=SEARCH_GOLDEN_DEPTH, sacred_geometry=8)
    computer.encode_optimization(cost_fn, num_variables=SEARCH_DIGITS)
    result = computer.relax_to_ground_state(max_steps=400 if quick else 4000)

    x = _decode_free_variable(computer.ground_state)
    free_var, y_val = _evaluate_swapped_equation(eq_name, const_swap, new_const_obj, x)

    return {
        "free_var": free_var,
        "x": x,
        "y": y_val,
        "final_energy": result["final_energy"],
        "detectable": result["final_energy"] < 1e-6,
        "steps": result["steps"],
        "time": result["time"],
    }


def generate_experiment(eq_name: str, const_swap: str, new_const_obj: dict, quick: bool = True) -> str:
    """Run the self-consistency search and format it as an experiment proposal."""
    eq = equations[eq_name]
    exp_info = eq.get('experiment')
    if exp_info is None:
        return "No experimental design available for this equation."

    search = run_self_consistency_search(eq_name, const_swap, new_const_obj, quick=quick)
    if "error" in search:
        return search["error"]

    expr = eq['expr'].replace(const_swap, f"{new_const_obj['value']:.2e} ({new_const_obj['unit']})")
    old_val = constants[const_swap]['value']
    ratio = new_const_obj['value'] / old_val if old_val != 0 else float('inf')
    free_var = search['free_var'] or '(fixed)'
    detectable_str = '✅ Yes' if search['detectable'] else '❌ No (no operating point in range falls within the detectable band)'

    if search['detectable']:
        meaning = ("This is a concrete, falsifiable prediction: build the apparatus above, "
                   "set the free variable to this value, and check whether the measured output matches.")
    else:
        meaning = ("No operating point in the searched range lands in a plausible detectable band, "
                   "so this swap is not experimentally falsifiable with the listed apparatus.")

    return f"""
    🧪 **Proposed Experiment: {exp_info['title']}**

    **Equation:** {eq['expr']}
    **Swapped constant:** {const_swap} → {new_const_obj['value']:.2e} {new_const_obj['unit']} ({ratio:.2e}x original)
    **Modified expression:** {expr}

    **Setup:** {exp_info['setup']}

    **Variables:** {exp_info['variables']}

    **Search result** (Mandala relaxation, {search['steps']} steps, {search['time']:.2f}s):
    Swept {free_var} over [{SEARCH_X_MIN:.0e}, {SEARCH_X_MAX:.0e}] via encode_optimization().
    Ground state: {free_var} = {search['x']:.3e}  ->  predicted output = {search['y']:.3e}
    Self-consistency energy: {search['final_energy']:.4f} (0 = falls within detectable band
    [{DETECTABLE_MIN:.0e}, {DETECTABLE_MAX:.0e}])

    **Detectable with current tech?** {detectable_str}

    **What this would mean:**
    At {free_var} = {search['x']:.3e}, swapping {const_swap} for {new_const_obj['label']} changes the
    predicted {eq['y_label'].lower()} to {search['y']:.3e} -- {ratio:.2e}x what the original constant
    would give at the same operating point. {meaning}
    """

# -------------------------------------------------------------------
# 6. Interactive UI
# -------------------------------------------------------------------
eq_dropdown = Dropdown(options=list(equations.keys()), description='Equation:')
const_swap_dropdown = Dropdown(description='Swap constant:')
new_const_dropdown = Dropdown(description='With constant:')
similar_button = Button(description='Suggest similar constants')
swap_button = Button(description='Swap and Plot')
reset_button = Button(description='Reset to default')
experiment_button = Button(description='Generate Experiment')
clear_button = Button(description='Clear Output')

output = Output()
experiment_output = Output()

current_swap = None
current_new = None

def update_constant_options(*args):
    eq_name = eq_dropdown.value
    eq = equations[eq_name]
    const_list = eq['constants']
    const_swap_dropdown.options = const_list
    if const_list:
        const_swap_dropdown.value = const_list[0]
    const_swap = const_swap_dropdown.value
    options = [name for name in constants.keys() if name != const_swap]
    new_const_dropdown.options = options
    if options:
        new_const_dropdown.value = options[0]

def on_similar_clicked(b):
    const_swap = const_swap_dropdown.value
    if const_swap:
        suggestions = suggest_similar_constants(const_swap)
        suggested_names = [s[0] for s in suggestions]
        all_names = list(constants.keys())
        ordered = suggested_names + [n for n in all_names if n not in suggested_names]
        new_const_dropdown.options = ordered
        if ordered:
            new_const_dropdown.value = ordered[0]

def on_swap_clicked(b):
    global current_swap, current_new
    with output:
        clear_output()
        eq_name = eq_dropdown.value
        const_swap = const_swap_dropdown.value
        new_const_name = new_const_dropdown.value
        if not const_swap or not new_const_name:
            print("Please select a constant to swap and a new constant.")
            return
        current_swap = const_swap
        current_new = new_const_name
        new_const_obj = constants[new_const_name]
        plot_swapped_equation(eq_name, {const_swap: new_const_obj},
                              [f"{const_swap} → {new_const_obj['value']:.2e} {new_const_obj['unit']}"])
        eq = equations[eq_name]
        expr = eq['expr'].replace(const_swap, f"{new_const_obj['value']:.2e} ({new_const_obj['unit']})")
        print(f"Modified equation: {expr}")

def on_reset_clicked(b):
    global current_swap, current_new
    with output:
        clear_output()
        current_swap = None
        current_new = None
        eq_name = eq_dropdown.value
        eq = equations[eq_name]
        consts = {c: constants[c] for c in eq['constants']}
        plot_swapped_equation(eq_name, consts, ["Original constants"])
        print("Reset to original equation.")

def on_experiment_clicked(b):
    with experiment_output:
        clear_output()
        if current_swap is None or current_new is None:
            print("Please perform a swap first (click 'Swap and Plot').")
            return
        eq_name = eq_dropdown.value
        new_const_obj = constants[current_new]
        print(generate_experiment(eq_name, current_swap, new_const_obj))

def on_clear_clicked(b):
    with output:
        clear_output()
    with experiment_output:
        clear_output()

eq_dropdown.observe(update_constant_options, 'value')
const_swap_dropdown.observe(update_constant_options, 'value')
similar_button.on_click(on_similar_clicked)
swap_button.on_click(on_swap_clicked)
reset_button.on_click(on_reset_clicked)
experiment_button.on_click(on_experiment_clicked)
clear_button.on_click(on_clear_clicked)

ui = VBox([
    HBox([eq_dropdown, const_swap_dropdown, new_const_dropdown]),
    HBox([similar_button, swap_button, reset_button, experiment_button, clear_button]),
    HTML("<hr style='border:1px solid #ccc;'>"),
    HBox([VBox([output]), VBox([experiment_output])])
])

display(ui)
update_constant_options()
on_reset_clicked(None)
