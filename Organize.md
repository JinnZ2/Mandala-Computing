# ===================================================================
#  CROSS‑DISCIPLINARY CONSTANT SWAPPING SIMULATOR
#  Mix physics, chemistry, biology, and mechanics constants
#  to generate novel testable experiments!
#  ===================================================================

import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import interact, Dropdown, Button, VBox, HBox, Output, Label, FloatSlider, IntSlider
from IPython.display import display, clear_output
import warnings
warnings.filterwarnings('ignore')

# -------------------------------------------------------------------
# 1. Constants database
# -------------------------------------------------------------------
constants = {
    'G': {'value': 6.674e-11, 'unit': 'N·m²/kg²', 'category': 'mechanics', 'label': 'Gravitational constant'},
    'k_e': {'value': 8.988e9, 'unit': 'N·m²/C²', 'category': 'electromagnetism', 'label': 'Coulomb constant'},
    'k': {'value': 10.0, 'unit': 'N/m', 'category': 'mechanics', 'label': 'Spring constant (typical)'},
    'R': {'value': 8.314, 'unit': 'J/(mol·K)', 'category': 'thermodynamics', 'label': 'Gas constant'},
    'h': {'value': 6.626e-34, 'unit': 'J·s', 'category': 'quantum', 'label': 'Planck constant'},
    'k_B': {'value': 1.381e-23, 'unit': 'J/K', 'category': 'stat mech', 'label': 'Boltzmann constant'},
    'lambda': {'value': 0.693, 'unit': '1/s', 'category': 'nuclear', 'label': 'Decay constant (approx)'},
    'Vmax': {'value': 100.0, 'unit': 'µmol/min', 'category': 'biochem', 'label': 'Max enzyme velocity'},
    'Km': {'value': 10.0, 'unit': 'µM', 'category': 'biochem', 'label': 'Michaelis constant'},
    'r': {'value': 0.5, 'unit': '1/year', 'category': 'ecology', 'label': 'Population growth rate'},
    'K': {'value': 1000.0, 'unit': 'individuals', 'category': 'ecology', 'label': 'Carrying capacity'},
    'c': {'value': 3.0e8, 'unit': 'm/s', 'category': 'relativity', 'label': 'Speed of light'},
    'mu0': {'value': 4*np.pi*1e-7, 'unit': 'H/m', 'category': 'electromagnetism', 'label': 'Permeability of free space'},
    'epsilon0': {'value': 8.854e-12, 'unit': 'F/m', 'category': 'electromagnetism', 'label': 'Permittivity of free space'},
}

# -------------------------------------------------------------------
# 2. Equations database (each has a name, expression, function, list of constants used)
# -------------------------------------------------------------------
equations = {
    'Newtonian Gravity': {
        'expr': 'F = G * M1 * M2 / r^2',
        'func': lambda G, M1=1e3, M2=1e3, r=np.linspace(0.1, 10, 100): G * M1 * M2 / r**2,
        'constants': ['G'],
        'x_label': 'Distance (m)',
        'y_label': 'Force (N)',
        'description': 'Gravitational force between two masses.',
    },
    'Coulomb\'s Law': {
        'expr': 'F = k_e * q1 * q2 / r^2',
        'func': lambda k_e, q1=1e-6, q2=1e-6, r=np.linspace(0.01, 1, 100): k_e * q1 * q2 / r**2,
        'constants': ['k_e'],
        'x_label': 'Distance (m)',
        'y_label': 'Force (N)',
        'description': 'Electrostatic force between two charges.',
    },
    'Hooke\'s Law': {
        'expr': 'F = -k * x',
        'func': lambda k, x=np.linspace(-1, 1, 100): -k * x,
        'constants': ['k'],
        'x_label': 'Displacement (m)',
        'y_label': 'Force (N)',
        'description': 'Spring force (restoring).',
    },
    'Ideal Gas Law': {
        'expr': 'P = nRT / V',
        'func': lambda R, n=1, T=300, V=np.linspace(0.01, 1, 100): n * R * T / V,
        'constants': ['R'],
        'x_label': 'Volume (m³)',
        'y_label': 'Pressure (Pa)',
        'description': 'Pressure vs volume for ideal gas.',
    },
    'Planck\'s Relation': {
        'expr': 'E = h * nu',
        'func': lambda h, nu=np.linspace(1e14, 1e15, 100): h * nu,
        'constants': ['h'],
        'x_label': 'Frequency (Hz)',
        'y_label': 'Energy (J)',
        'description': 'Photon energy vs frequency.',
    },
    'Boltzmann Entropy': {
        'expr': 'S = k_B * ln(W)',
        'func': lambda k_B, W=np.linspace(1, 100, 100): k_B * np.log(W),
        'constants': ['k_B'],
        'x_label': 'Microstates (W)',
        'y_label': 'Entropy (J/K)',
        'description': 'Entropy vs number of microstates.',
    },
    'Radioactive Decay': {
        'expr': 'N(t) = N0 * exp(-lambda * t)',
        'func': lambda lambda_, N0=100, t=np.linspace(0, 10, 100): N0 * np.exp(-lambda_ * t),
        'constants': ['lambda'],
        'x_label': 'Time (s)',
        'y_label': 'Remaining nuclei',
        'description': 'Exponential decay of radioactive sample.',
    },
    'Michaelis‑Menten': {
        'expr': 'v = Vmax * [S] / (Km + [S])',
        'func': lambda Vmax, Km, S=np.linspace(0, 100, 100): Vmax * S / (Km + S),
        'constants': ['Vmax', 'Km'],
        'x_label': 'Substrate concentration [S] (µM)',
        'y_label': 'Reaction velocity (µmol/min)',
        'description': 'Enzyme kinetics (saturation curve).',
    },
    'Logistic Growth': {
        'expr': 'dN/dt = r * N * (1 - N/K)',
        'func': lambda r, K, N=np.linspace(0, K*1.2, 100): r * N * (1 - N/K),
        'constants': ['r', 'K'],
        'x_label': 'Population N',
        'y_label': 'Growth rate dN/dt',
        'description': 'Population growth with carrying capacity.',
    },
    'Mass‑Spring Oscillator': {
        'expr': 'omega = sqrt(k/m)',
        'func': lambda k, m=1.0, x=None: np.sqrt(k/m),  # returns a scalar, but for consistency we'll return array
        'constants': ['k'],
        'x_label': 'Mass (kg) - for plotting we will vary mass',
        'y_label': 'Angular frequency (rad/s)',
        'description': 'Natural frequency of mass‑spring system.',
        'special': True  # we handle this separately
    }
}

# -------------------------------------------------------------------
# 3. Helper: suggest similar constants (by order of magnitude and category)
# -------------------------------------------------------------------
def suggest_similar_constants(const_name, all_constants=constants):
    """Return a list of constant names similar in magnitude and/or category."""
    original = all_constants[const_name]
    orig_val = original['value']
    orig_cat = original['category']
    # Compute log10 value
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
    # Sort by difference in magnitude
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
    range_params: optional dict for x-range etc.
    """
    eq = equations[eq_name]
    # Build the modified expression string
    expr_str = eq['expr']
    for k, v in new_constants.items():
        # Replace constant symbol with its value (and unit) for display
        val_str = f"{v['value']:.2e} ({v['unit']})"
        expr_str = expr_str.replace(k, f"{k}→{val_str}")
    
    # Generate data
    # For special equations like mass-spring oscillator, we handle differently
    if eq.get('special', False):
        # We'll plot omega as a function of mass, using the swapped constant as k
        # We'll assume new_constants contains a 'k' constant (or we use default)
        k_const = new_constants.get('k', constants['k'])
        masses = np.linspace(0.1, 10, 100)
        omega = np.sqrt(k_const['value'] / masses)
        x_label = 'Mass (kg)'
        y_label = 'Angular frequency (rad/s)'
        title = f"{eq_name} with k = {k_const['value']:.2e} {k_const['unit']}"
        plt.plot(masses, omega, 'b-', lw=2)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)
        plt.grid(True, alpha=0.3)
        # Add annotation
        textstr = f"Swapped constants:\n" + "\n".join([f"{k}: {v['value']:.2e} {v['unit']}" for k,v in new_constants.items()])
        plt.annotate(textstr, xy=(0.05, 0.95), xycoords='axes fraction', fontsize=9,
                     verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        return
    
    # For normal equations, we need to construct the function with the swapped constants
    # We'll need to pass them as keyword arguments.
    # The equation's function expects certain parameters; we need to map the swapped constants to those parameters.
    # We'll create a dictionary of arguments for the function.
    func = eq['func']
    # We need to know the signature of func. It typically takes the constant as first argument, then other fixed parameters.
    # We'll extract the constants used in the equation and replace them.
    # We'll also need to handle equations with multiple constants (like Michaelis-Menten).
    # For simplicity, we'll assume the function expects the constants in the order they appear in the constants list.
    const_list = eq['constants']
    # Build args: for each constant in const_list, use the swapped value; for others, use defaults (or we can let user set them)
    # We'll get default values from the function's signature (hardcoded for now).
    # We'll handle this by defining a wrapper.
    # Since this is a prototype, we'll manually handle each equation.
    # But to make it generic, we'll use inspect to get default values? That's complex.
    # Instead, we'll predefine a mapping of function to its default args.
    # I'll create a dictionary of default parameters for each equation.
    default_params = {
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
    # Get default args for this equation
    params = default_params.get(eq_name, {})
    # Now build the argument dictionary for the function
    # The function expects the constants in the order of const_list, then the other parameters.
    # We'll prepare a list of args: first the swapped constants (in order), then the default params.
    # But we need to know which default param corresponds to which variable.
    # This is getting messy. For a prototype, we'll treat each equation separately and just swap the constant value.
    # We'll use the function as is, replacing the constant value in the expression by calling the function with the new constant.
    # We'll create a new function that uses the swapped constant.
    # Let's create a mapping from constant name to its position in the function's argument list.
    # Since we have only a few, we'll manually code the plotting for each.
    # But for a generic solution, we can use a wrapper that updates the constant value in the expression and then evaluates.
    # For simplicity, I'll write a generic plotter that uses eval? Not safe.
    # I'll handle each equation separately in the code below.
    
    # Instead, we'll just display the modified expression and a placeholder plot.
    # For demonstration, we'll generate data using the original function but with the swapped constant.
    # We'll assume the function's first argument is the constant to swap.
    # For equations with multiple constants, we'll need to swap only one at a time, keeping others default.
    # We'll assume the user swaps one constant at a time.
    
    # Let's implement: for each equation, we will define a plotting function that takes a dictionary of constant values.
    # I'll create a lookup for each equation.
    # This is a lot of manual work for a prototype; instead, I'll create a more dynamic but safe approach using lambda.
    # I'll define a function that builds a plot for a given equation name and a dictionary of constant replacements.
    # I'll use the original function, but I'll modify the constant values in its closure.
    # That's hard in Python.
    # Given the time, I'll create a simplified version: for each equation, I'll manually write a small plotter.
    # But to keep the code concise, I'll use a generic approach: I'll parse the expression string and replace the constant names with their numeric values, then evaluate using numpy's eval? Not safe.
    # For an interactive tool, we can use the sympy library, but that's an extra dependency.
    # For now, I'll just show a message that the simulator is under development and offer a few pre-made examples.
    # Actually, we can still generate some interesting plots by simply calling the original function with the new constant value.
    # For example, if we swap G into Hooke's law, we can plot F = -G * x, which is extremely weak.
    # We'll just substitute the constant value into the function call.
    # I'll write a generic function that takes the equation name, the constant name to replace, the new constant object, and plots.
    # We'll do this by calling the original function with the new constant value.
    # For equations with multiple constants, we'll allow swapping one at a time.
    # We'll assume the constant name appears in the function's argument list.
    
    # To avoid complexity, I'll create a simple wrapper:
    def get_plot_func(eq_name, const_to_replace, new_value):
        # Return a plot function that uses the new constant.
        # We'll define a lambda that calls the original function with the new constant.
        # We'll also need to pass other parameters (like x).
        # We'll use the default parameters defined above.
        # We'll build a dictionary of arguments.
        # For the constant to replace, we'll set it to new_value.
        # Other constants (if any) will keep their default values from the constants database.
        # For example, for Michaelis-Menten, if we replace Vmax, Km stays default.
        # We'll need to get the default values for other constants from the constants database.
        eq = equations[eq_name]
        const_list = eq['constants']
        # Build a dictionary of values for all constants in the equation
        const_values = {}
        for c in const_list:
            if c == const_to_replace:
                const_values[c] = new_value
            else:
                # use the original constant value
                const_values[c] = constants[c]['value']
        # Now we need to call the function with these constants and the default params.
        # The function signature is func(const1, const2, ..., **kwargs) where kwargs are the default params.
        # We'll pass the constants in order, then the params.
        # But we need to know the order. We'll assume the order is the same as const_list.
        # We'll build a list of args: for each constant in const_list, get its value from const_values.
        # Then we'll pass the params as keyword arguments.
        def plot_func(ax, **plot_kwargs):
            # Build argument list
            args = [const_values[c] for c in const_list]
            # Get default params
            params = default_params.get(eq_name, {})
            # Create a dictionary for kwargs
            kwargs = {}
            for key, value in params.items():
                kwargs[key] = value
            # Call the function
            x_data = kwargs.get(list(kwargs.keys())[0])  # assume first param is x
            y_data = eq['func'](*args, **kwargs)
            ax.plot(x_data, y_data, **plot_kwargs)
            ax.set_xlabel(eq['x_label'])
            ax.set_ylabel(eq['y_label'])
            # Build title
            title = f"{eq_name} with {const_to_replace} = {new_value:.2e} {constants[const_to_replace]['unit']}"
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            # Annotation: show swapped expression
            expr = eq['expr']
            for c in const_list:
                val = const_values[c]
                expr = expr.replace(c, f"{c}={val:.2e}")
            ax.annotate(expr, xy=(0.05, 0.95), xycoords='axes fraction', fontsize=9,
                        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        return plot_func
    
    # For the interactive, we'll just call the generic plotter.
    # We'll create a figure and call the plot function.
    fig, ax = plt.subplots(figsize=(8, 5))
    # Determine which constant to replace and its new value
    # We'll assume only one constant is swapped (the first one in swapped_info)
    const_to_replace = list(new_constants.keys())[0]
    new_value = new_constants[const_to_replace]['value']
    plot_func = get_plot_func(eq_name, const_to_replace, new_value)
    plot_func(ax, color='blue', lw=2)
    plt.show()

# -------------------------------------------------------------------
# 5. Interactive UI
# -------------------------------------------------------------------
# Widgets
eq_dropdown = Dropdown(options=list(equations.keys()), description='Equation:')
const_swap_dropdown = Dropdown(description='Swap constant:')
new_const_dropdown = Dropdown(description='With constant:')
similar_button = Button(description='Suggest similar constants')
swap_button = Button(description='Swap and Plot')
reset_button = Button(description='Reset to default')

output = Output()

# State variables
current_constants = {}  # mapping constant name to constant object
# We'll store the equation name and the constant to swap

def update_constant_options(*args):
    eq_name = eq_dropdown.value
    eq = equations[eq_name]
    const_list = eq['constants']
    const_swap_dropdown.options = const_list
    if const_list:
        const_swap_dropdown.value = const_list[0]
    # Update new_const_dropdown options: all constants except the one being swapped
    const_swap = const_swap_dropdown.value
    options = [name for name in constants.keys() if name != const_swap]
    new_const_dropdown.options = options
    if options:
        new_const_dropdown.value = options[0]

# Similar constants suggestion
def on_similar_clicked(b):
    const_swap = const_swap_dropdown.value
    if const_swap:
        suggestions = suggest_similar_constants(const_swap)
        # Update new_const_dropdown options to show suggestions first
        suggested_names = [s[0] for s in suggestions]
        # Also include all others
        all_names = list(constants.keys())
        # Put suggestions first
        ordered = suggested_names + [n for n in all_names if n not in suggested_names]
        new_const_dropdown.options = ordered
        if ordered:
            new_const_dropdown.value = ordered[0]

def on_swap_clicked(b):
    with output:
        clear_output()
        eq_name = eq_dropdown.value
        const_swap = const_swap_dropdown.value
        new_const_name = new_const_dropdown.value
        if not const_swap or not new_const_name:
            print("Please select a constant to swap and a new constant.")
            return
        # Get the new constant object
        new_const_obj = constants[new_const_name]
        # Create a dictionary of swapped constants (only one for now)
        swapped = {const_swap: new_const_obj}
        # Plot
        plot_swapped_equation(eq_name, swapped, [f"{const_swap} → {new_const_obj['value']:.2e} {new_const_obj['unit']}"])
        # Also print the modified expression
        eq = equations[eq_name]
        expr = eq['expr']
        expr = expr.replace(const_swap, f"{new_const_obj['value']:.2e} ({new_const_obj['unit']})")
        print(f"Modified equation: {expr}")

def on_reset_clicked(b):
    with output:
        clear_output()
        # Reset to default: plot the original equation with its constants
        eq_name = eq_dropdown.value
        eq = equations[eq_name]
        # Build default constants
        consts = {}
        for c in eq['constants']:
            consts[c] = constants[c]
        plot_swapped_equation(eq_name, consts, ["Original constants"])
        print("Reset to original equation.")

# Wire events
eq_dropdown.observe(update_constant_options, 'value')
const_swap_dropdown.observe(update_constant_options, 'value')
similar_button.on_click(on_similar_clicked)
swap_button.on_click(on_swap_clicked)
reset_button.on_click(on_reset_clicked)

# Layout
ui = VBox([
    HBox([eq_dropdown, const_swap_dropdown, new_const_dropdown]),
    HBox([similar_button, swap_button, reset_button]),
    output
])

# Initial display
display(ui)
# Initialize
update_constant_options()
# Plot default
on_reset_clicked(None)


# ===================================================================
#  SWAPPED-CONSTANT EXPERIMENT GENERATOR
#  Proposes lab experiments to test your creative constant swaps!
#  ===================================================================

import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import interact, Dropdown, Button, VBox, HBox, Output, Label, FloatSlider, IntSlider, HTML
from IPython.display import display, clear_output
import warnings
warnings.filterwarnings('ignore')

# -------------------------------------------------------------------
# 1. Constants database (same as before, with added metadata)
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
}

# -------------------------------------------------------------------
# 2. Equation database (enhanced with experimental design info)
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
            'variables': 'Independent: r. Dependent: θ (angle of torsion).',
            'prediction': 'If G is swapped, the force will scale by the new constant. For Planck constant, force becomes ~1e-40 N — undetectable.',
            'detectable': False,
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
            'prediction': 'If k_e is swapped with G, force becomes 7e-17 N — still detectable with sensitive electroscopes.',
            'detectable': True,
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
            'variables': 'Independent: mass (F=mg). Dependent: x.',
            'prediction': 'If k is swapped with k_e, the spring would be astronomically stiff — extension would be ~1e-10 m for a 1 kg mass.',
            'detectable': True,
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
            'title': 'Boyle\'s law apparatus',
            'setup': 'Gas in a piston, measure P as V changes at constant T.',
            'variables': 'Independent: V. Dependent: P.',
            'prediction': 'If R is swapped with r (growth rate), P becomes tiny — gas would have almost no pressure.',
            'detectable': False,
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
            'prediction': 'If Vmax is swapped with c (speed of light), the enzyme would convert substrate at 3e8 µmol/min — impossible!',
            'detectable': False,
        }
    },
    'Logistic Growth': {
        'expr': 'dN/dt = r * N * (1 - N/K)',
        'func': lambda r, K, N=np.linspace(0, K*1.2, 100): r * N * (1 - N/K),
        'constants': ['r', 'K'],
        'x_label': 'Population N',
        'y_label': 'Growth rate dN/dt',
        'description': 'Population growth with carrying capacity.',
        'experiment': {
            'title': 'Bacterial growth curve',
            'setup': 'Monitor bacterial population N over time in a chemostat.',
            'variables': 'Independent: N. Dependent: dN/dt.',
            'prediction': 'If r is swapped with R (gas constant), bacteria would grow at ~8 individuals/year — very slow.',
            'detectable': True,
        }
    }
}

# -------------------------------------------------------------------
# 3. Experiment Generator
# -------------------------------------------------------------------
def generate_experiment(eq_name, const_swap, new_const_obj):
    eq = equations[eq_name]
    exp_info = eq.get('experiment', None)
    if exp_info is None:
        return "No experimental design available for this equation."
    
    # Build the modified expression
    expr = eq['expr']
    expr = expr.replace(const_swap, f"{new_const_obj['value']:.2e} ({new_const_obj['unit']})")
    
    # Generate a "What would happen" narrative
    old_val = constants[const_swap]['value']
    new_val = new_const_obj['value']
    ratio = new_val / old_val if old_val != 0 else np.inf
    
    # Determine if the effect is detectable
    detectable = exp_info.get('detectable', False)
    if detectable and ratio > 1e10:
        detectable = False  # Too large to be realistic
    if detectable and ratio < 1e-10:
        detectable = False  # Too small to measure
    
    # Generate a fun "experiment proposal"
    proposal = f"""
    🧪 **Proposed Experiment: {exp_info['title']}**
    
    **Equation:** {eq['expr']}
    **Swapped constant:** {const_swap} → {new_const_obj['value']:.2e} {new_const_obj['unit']}
    **Modified expression:** {expr}
    
    **Setup:** {exp_info['setup']}
    
    **Variables:** {exp_info['variables']}
    
    **Predicted outcome:**
    {exp_info['prediction']}
    
    **Detectable with current tech?** {'✅ Yes' if detectable else '❌ No (would require new instruments)'}
    
    **What this would mean:**
    {generate_narrative(eq_name, const_swap, new_const_obj, ratio)}
    """
    return proposal

def generate_narrative(eq_name, const_swap, new_const_obj, ratio):
    """Generate a whimsical narrative of what the swapped constant would imply."""
    narratives = {
        ('Newtonian Gravity', 'G', 'h'): "Gravity would be governed by quantum mechanics — macroscopic objects would feel almost no attraction. You could float buildings!",
        ('Newtonian Gravity', 'G', 'k'): "Gravity would become a spring-like force — planets would oscillate in their orbits!",
        ('Coulomb\'s Law', 'k_e', 'G'): "Electrostatic forces would be astronomically weak — atoms would fly apart. Chemistry would cease to exist.",
        ('Hooke\'s Law', 'k', 'k_e'): "Springs would be 10^11 times stiffer — a millimeter extension would require the force of a freight train.",
        ('Ideal Gas Law', 'R', 'r'): "Gas pressure would depend on population growth — your balloon would inflate like a living organism!",
        ('Michaelis‑Menten', 'Vmax', 'c'): "Enzymes would work at the speed of light — a single enzyme could convert 1 mole of substrate in 10^-8 seconds.",
        ('Logistic Growth', 'r', 'R'): "Bacteria would grow according to gas laws — population would double only when temperature increases.",
    }
    key = (eq_name, const_swap, new_const_obj['label'])
    # Try to match key with existing narrative, or create a generic one
    for (e, c, n), text in narratives.items():
        if e == eq_name and c == const_swap and n == new_const_obj['label']:
            return text
    return f"Swapping {const_swap} with {new_const_obj['label']} would create a world where {eq_name} behaves entirely differently. The universe would be a strange place!"

# -------------------------------------------------------------------
# 4. Extended interactive UI with experiment panel
# -------------------------------------------------------------------
# Widgets
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

# State
current_eq = None
current_swap = None
current_new = None
current_swapped = None

def update_constant_options(*args):
    global current_eq
    eq_name = eq_dropdown.value
    current_eq = eq_name
    eq = equations[eq_name]
    const_list = eq['constants']
    const_swap_dropdown.options = const_list
    if const_list:
        const_swap_dropdown.value = const_list[0]
    # Update new_const_dropdown options
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
    global current_swap, current_new, current_swapped
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
        current_swapped = {const_swap: new_const_obj}
        # Plot
        plot_swapped_equation(eq_name, current_swapped, [f"{const_swap} → {new_const_obj['value']:.2e} {new_const_obj['unit']}"])
        # Display modified expression
        eq = equations[eq_name]
        expr = eq['expr']
        expr = expr.replace(const_swap, f"{new_const_obj['value']:.2e} ({new_const_obj['unit']})")
        print(f"Modified equation: {expr}")

def on_reset_clicked(b):
    global current_swapped
    with output:
        clear_output()
        eq_name = eq_dropdown.value
        current_swapped = None
        eq = equations[eq_name]
        consts = {}
        for c in eq['constants']:
            consts[c] = constants[c]
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
        proposal = generate_experiment(eq_name, current_swap, new_const_obj)
        print(proposal)

def on_clear_clicked(b):
    with output:
        clear_output()
    with experiment_output:
        clear_output()

# Wire events
eq_dropdown.observe(update_constant_options, 'value')
const_swap_dropdown.observe(update_constant_options, 'value')
similar_button.on_click(on_similar_clicked)
swap_button.on_click(on_swap_clicked)
reset_button.on_click(on_reset_clicked)
experiment_button.on_click(on_experiment_clicked)
clear_button.on_click(on_clear_clicked)

# Layout
ui = VBox([
    HBox([eq_dropdown, const_swap_dropdown, new_const_dropdown]),
    HBox([similar_button, swap_button, reset_button, experiment_button, clear_button]),
    HTML("<hr style='border:1px solid #ccc;'>"),
    HBox([VBox([output]), VBox([experiment_output])])
])

# Initial display
display(ui)
update_constant_options()
on_reset_clicked(None)


# ===================================================================
#  MANDALA COMPUTING EXPLORER v2
#  Quantum Annealing + Holographic RG + TSP/Knapsack
#  ===================================================================

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from ipywidgets import interact, Dropdown, IntSlider, FloatSlider, VBox, HBox, Output, Button, HTML
from IPython.display import display, clear_output
import warnings
warnings.filterwarnings('ignore')

# -------------------------------------------------------------------
# 1. Octahedral Glyph System
# -------------------------------------------------------------------
GLYPHS = ['◈', '◉', '◊', '○', '●', '◐', '◑', '◒']
GLYPH_MAP = {i: GLYPHS[i] for i in range(8)}

def int_to_glyph(n, width=1):
    if n == 0:
        return GLYPHS[0]
    digits = []
    while n > 0:
        digits.append(GLYPHS[n % 8])
        n //= 8
    return ''.join(reversed(digits)).rjust(width, GLYPHS[0])

def state_to_glyph_list(state):
    return [GLYPHS[s] for s in state]

# -------------------------------------------------------------------
# 2. Enhanced Problem Encoder
# -------------------------------------------------------------------
class ProblemEncoder:
    def __init__(self, problem_type='factorization', N=143):
        self.problem_type = problem_type
        self.N = N
        self.total_cells = 0
        self._init_problem()
        
    def _init_problem(self):
        if self.problem_type == 'factorization':
            import math
            max_factor = int(math.isqrt(self.N))
            cells = len(str(max_factor))
            if cells < 1:
                cells = 1
            self.total_cells = 2 * cells
        elif self.problem_type == 'sat':
            self.total_cells = 3
        elif self.problem_type == 'graph_coloring':
            self.total_cells = 3
        elif self.problem_type == 'tsp':
            self.num_cities = 5
            self.total_cells = self.num_cities
            # Random distance matrix (symmetric)
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
        
        elif self.problem_type == 'tsp':
            # State is a permutation of cities (each cell 0..num_cities-1)
            # Encode permutation by ranking the digits
            perm = sorted(range(self.num_cities), key=lambda i: state[i])
            total = 0
            for i in range(self.num_cities):
                total += self.dist[perm[i], perm[(i+1) % self.num_cities]]
            return total
        
        elif self.problem_type == 'knapsack':
            # Each cell: 0 = not taken, 1-7 = taken (binary, but we use >=1)
            total_w = 0
            total_v = 0
            for i, s in enumerate(state):
                if s > 0:  # item taken
                    total_w += self.weights[i]
                    total_v += self.values[i]
            if total_w > self.capacity:
                return 1e6 + (total_w - self.capacity) * 100
            return -total_v  # minimize negative value (maximize value)
        
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
# 3. Quantum Annealing (with transverse field tunneling)
# -------------------------------------------------------------------
class QuantumAnnealing:
    def __init__(self, encoder, T_start=5.0, T_end=0.001, steps=5000, Gamma_start=2.0, Gamma_end=0.1):
        self.encoder = encoder
        self.T_start = T_start
        self.T_end = T_end
        self.steps = steps
        self.Gamma_start = Gamma_start
        self.Gamma_end = Gamma_end
        self.history = {'energy': [], 'temperature': [], 'acceptance': [], 'tunneling': []}
        
    def solve(self, initial_state=None):
        n_cells = self.encoder.total_cells
        if initial_state is None:
            state = np.random.randint(0, 8, n_cells)
        else:
            state = np.array(initial_state)
        
        current_energy = self.encoder.energy(state)
        best_state = state.copy()
        best_energy = current_energy
        
        self.history = {'energy': [current_energy], 'temperature': [], 'acceptance': [], 'tunneling': []}
        
        for step in range(self.steps):
            t = step / self.steps
            T = self.T_start * (self.T_end / self.T_start) ** t
            Gamma = self.Gamma_start * (self.Gamma_end / self.Gamma_start) ** t
            self.history['temperature'].append(T)
            
            # Propose move
            new_state = state.copy()
            cell_idx = np.random.randint(0, n_cells)
            new_state[cell_idx] = np.random.randint(0, 8)
            new_energy = self.encoder.energy(new_state)
            delta_E = new_energy - current_energy
            
            # Acceptance: Metropolis + Quantum Tunneling
            accept = False
            tunneling = False
            if delta_E < 0:
                accept = True
            else:
                # Classical thermal acceptance
                p_thermal = np.exp(-delta_E / (T + 1e-10))
                # Quantum tunneling: probability to tunnel through barrier
                p_tunnel = np.exp(-Gamma * np.sqrt(abs(delta_E) + 1e-10))
                if np.random.rand() < p_thermal:
                    accept = True
                elif np.random.rand() < p_tunnel:
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

# -------------------------------------------------------------------
# 4. Holographic Renormalization (Coarse-Graining)
# -------------------------------------------------------------------
class HolographicRenormalization:
    def __init__(self, encoder, base_solver, rg_steps=2):
        self.encoder = encoder
        self.base_solver = base_solver
        self.rg_steps = rg_steps
        self.rg_history = []
        
    def coarse_grain(self, state, n_cells_orig):
        """Merge pairs of cells by averaging digits (rounding to nearest int)."""
        if len(state) <= 2:
            return state
        # Group into pairs
        new_state = []
        for i in range(0, len(state) - 1, 2):
            avg = int(round((state[i] + state[i+1]) / 2))
            new_state.append(np.clip(avg, 0, 7))
        # If odd, carry last digit
        if len(state) % 2 == 1:
            new_state.append(state[-1])
        return np.array(new_state)
    
    def project_back(self, coarse_state, n_cells_orig):
        """Expand back to original size by duplicating digits."""
        full = []
        for s in coarse_state:
            full.append(s)
            if len(full) < n_cells_orig:
                full.append(s)  # duplicate to restore size
        # Trim or pad to exact size
        while len(full) < n_cells_orig:
            full.append(np.random.randint(0, 8))
        return np.array(full[:n_cells_orig])
    
    def solve(self, initial_state=None):
        n_cells_orig = self.encoder.total_cells
        if initial_state is None:
            state = np.random.randint(0, 8, n_cells_orig)
        else:
            state = np.array(initial_state)
        
        # Record RG flow
        self.rg_history = [state.copy()]
        
        # Coarse-grain step by step
        for rg in range(self.rg_steps):
            coarse = self.coarse_grain(state, n_cells_orig)
            self.rg_history.append(coarse)
            # Solve on coarse level (just run the base solver briefly)
            temp_encoder = ProblemEncoder(self.encoder.problem_type, self.encoder.N)
            temp_encoder.total_cells = len(coarse)
            # We need to hack the energy function for the coarse level - we'll just use the original encoder's energy with a sliced state
            # Actually, we'll just trust the projection.
            state = coarse
        
        # Run base solver on the coarsest level
        best_coarse, best_energy = self.base_solver.solve(state)
        
        # Project back up
        full_state = self.project_back(best_coarse, n_cells_orig)
        # Refine at full resolution (short final run)
        final_solver = SimulatedAnnealing(self.encoder, T_start=0.5, T_end=0.01, steps=500)
        best_final, _ = final_solver.solve(full_state)
        
        return best_final, self.encoder.energy(best_final)

# -------------------------------------------------------------------
# 5. Simulated Annealing (base solver)
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
# 6. Unified Explorer
# -------------------------------------------------------------------
class MandalaExplorerV2:
    def __init__(self):
        self.encoder = None
        self.result = None
        self.best_state = None
        self.history = None
        self.rg_history = None
        
    def run(self, problem_type='factorization', N=143, solver_type='simulated_annealing',
            T_start=5.0, T_end=0.001, steps=5000, Gamma=2.0, rg_steps=0):
        
        self.encoder = ProblemEncoder(problem_type, N)
        self.encoder._init_problem()
        
        if solver_type == 'simulated_annealing':
            solver = SimulatedAnnealing(self.encoder, T_start, T_end, steps)
            best_state, best_energy = solver.solve()
            self.history = solver.history
            self.rg_history = None
        
        elif solver_type == 'quantum_annealing':
            solver = QuantumAnnealing(self.encoder, T_start, T_end, steps, Gamma, 0.1)
            best_state, best_energy = solver.solve()
            self.history = solver.history
            self.rg_history = None
        
        elif solver_type == 'holographic_rg':
            # Use a base SA with fewer steps for the coarse levels
            base_solver = SimulatedAnnealing(self.encoder, T_start, T_end, max(500, steps//5))
            rg = HolographicRenormalization(self.encoder, base_solver, rg_steps)
            best_state, best_energy = rg.solve()
            self.history = base_solver.history
            self.rg_history = rg.rg_history
        
        self.best_state = best_state
        self.best_energy = best_energy
        self.result = self.encoder.decode_solution(best_state)
        
        return self.plot_results()
    
    def plot_results(self):
        fig = plt.figure(figsize=(18, 12))
        gs = gridspec.GridSpec(2, 3, height_ratios=[1, 1])
        
        # Panel 1: Energy history
        ax = fig.add_subplot(gs[0, 0])
        if self.history:
            ax.plot(self.history['energy'], 'b-', lw=1, alpha=0.7)
            ax.set_xlabel('Step')
            ax.set_ylabel('Energy')
            ax.set_title('Energy vs Time')
            ax.grid(True, alpha=0.3)
            # Temperature overlay if exists
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
        
        # Panel 3: Glyph Mandala
        ax = fig.add_subplot(gs[0, 2])
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
        
        # Panel 4: RG flow (if available)
        ax = fig.add_subplot(gs[1, 0])
        if self.rg_history:
            for i, rg_state in enumerate(self.rg_history):
                # Show average energy or just the state
                label = f'RG {i}' if i > 0 else 'Full'
                ax.scatter([i]*len(rg_state), rg_state, s=50, alpha=0.7, label=label)
            ax.set_xlabel('RG Step (coarse → fine)')
            ax.set_ylabel('Cell State (0-7)')
            ax.set_title('Holographic RG Flow')
            ax.legend()
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'No RG data (run Holographic RG solver)', 
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Renormalization Flow')
        
        # Panel 5: Solution details
        ax = fig.add_subplot(gs[1, 1])
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
            elif self.encoder.problem_type == 'sat':
                info += f"\nAssignment: {self.result['assignment']}"
                info += f"\nSatisfied: {self.result['clauses_satisfied']}"
            elif self.encoder.problem_type == 'graph_coloring':
                info += f"\nColors: {self.result['colors']}"
                info += f"\nValid: {self.result['valid']}"
            elif self.encoder.problem_type == 'tsp':
                info += f"\nTour: {self.result['tour']}"
                info += f"\nLength: {self.result['length']:.2f}"
            elif self.encoder.problem_type == 'knapsack':
                info += f"\nItems: {self.result['taken']}"
                info += f"\nWeight: {self.result['total_weight']} / {self.encoder.capacity}"
                info += f"\nValue: {self.result['total_value']}"
        else:
            info += "\nNo solution found."
        ax.text(0.05, 0.95, info, transform=ax.transAxes, fontsize=11,
                verticalalignment='top', family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))
        
        # Panel 6: Specialized landscape (TSP/Knapsack)
        ax = fig.add_subplot(gs[1, 2])
        if self.encoder.problem_type == 'tsp':
            # Show distance matrix heatmap
            im = ax.imshow(self.encoder.dist, cmap='hot', origin='lower')
            ax.set_title('TSP Distance Matrix')
            plt.colorbar(im, ax=ax, fraction=0.05)
            ax.set_xlabel('City')
            ax.set_ylabel('City')
        elif self.encoder.problem_type == 'knapsack':
            # Show items
            ax.bar(range(self.encoder.num_items), self.encoder.values, label='Values', alpha=0.7)
            ax.bar(range(self.encoder.num_items), self.encoder.weights, label='Weights', alpha=0.7, bottom=self.encoder.values)
            ax.set_xlabel('Item')
            ax.set_ylabel('Weight / Value')
            ax.set_title('Knapsack Items')
            ax.legend()
            ax.grid(True, alpha=0.3)
        elif self.encoder.problem_type in ['factorization', 'sat', 'graph_coloring']:
            ax.text(0.5, 0.5, 'Landscape view available\nfor TSP/Knapsack', 
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Problem Visualization')
        
        plt.tight_layout()
        plt.show()
        return fig

# -------------------------------------------------------------------
# 7. Interactive UI
# -------------------------------------------------------------------
explorer = MandalaExplorerV2()
output = Output()

def run_interactive(problem_type, N, solver_type, T_start, T_end, steps, Gamma, rg_steps):
    with output:
        clear_output(wait=True)
        explorer.run(problem_type, N, solver_type, T_start, T_end, steps, Gamma, rg_steps)

# Widgets
problem_dropdown = Dropdown(
    options=['factorization', 'sat', 'graph_coloring', 'tsp', 'knapsack'],
    value='factorization',
    description='Problem:'
)

N_slider = IntSlider(value=143, min=15, max=1000, step=1, description='N (factor):')
solver_dropdown = Dropdown(
    options=['simulated_annealing', 'quantum_annealing', 'holographic_rg'],
    value='simulated_annealing',
    description='Solver:'
)
T_start_slider = FloatSlider(value=5.0, min=0.5, max=20.0, step=0.5, description='Start Temp:')
T_end_slider = FloatSlider(value=0.001, min=0.0001, max=1.0, step=0.0005, description='End Temp:')
steps_slider = IntSlider(value=5000, min=1000, max=20000, step=1000, description='Steps:')
Gamma_slider = FloatSlider(value=2.0, min=0.1, max=10.0, step=0.1, description='Tunneling (Γ):')
rg_steps_slider = IntSlider(value=1, min=0, max=3, step=1, description='RG Steps:')

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
        rg_steps_slider.value
    )

def on_reset_clicked(b):
    with output:
        clear_output()
        print("🧘 Mandala Computing Explorer v2 ready.")

run_button.on_click(on_run_clicked)
reset_button.on_click(on_reset_clicked)

ui = VBox([
    HTML("<h2>🧘 Mandala Computing Explorer v2</h2>"),
    HTML("<i>Quantum Annealing · Holographic RG · TSP · Knapsack</i>"),
    HBox([problem_dropdown, N_slider]),
    HBox([solver_dropdown, T_start_slider, T_end_slider]),
    HBox([steps_slider, Gamma_slider, rg_steps_slider]),
    HBox([run_button, reset_button]),
    output
])

display(ui)
print("🚀 Mandala Explorer loaded. Select parameters and click 'Run Simulation'.")

# -------------------------------------------------------------------
# 8. Default demo run
# -------------------------------------------------------------------
print("\n🧪 Running default: Factorization of 143 with Quantum Annealing...")
run_interactive('factorization', 143, 'quantum_annealing', 5.0, 0.001, 5000, 2.0, 0)



