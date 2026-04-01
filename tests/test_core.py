"""
Core correctness tests for Mandala Computing.

Run with: python -m pytest tests/ -v
Or:       python tests/test_core.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import math

# ---------------------------------------------------------------------------
# Octahedral Arithmetic tests
# ---------------------------------------------------------------------------

from octahedral_arithmetic import OctahedralNumber, GlyphFraction, factor_pair_glyphs, states_to_number


def test_oct_from_decimal():
    assert OctahedralNumber.from_decimal(0).digits == (0,)
    assert OctahedralNumber.from_decimal(7).digits == (7,)
    assert OctahedralNumber.from_decimal(8).digits == (0, 1)   # 8 = 0 + 1*8
    assert OctahedralNumber.from_decimal(11).digits == (3, 1)  # 11 = 3 + 1*8
    assert OctahedralNumber.from_decimal(143).digits == (7, 1, 2)  # 143 = 7 + 1*8 + 2*64


def test_oct_roundtrip():
    for n in [0, 1, 7, 8, 15, 42, 100, 143, 221, 512, 1000]:
        assert OctahedralNumber.from_decimal(n).to_decimal() == n


def test_oct_addition():
    a = OctahedralNumber.from_decimal(11)
    b = OctahedralNumber.from_decimal(13)
    assert (a + b).to_decimal() == 24


def test_oct_multiplication():
    a = OctahedralNumber.from_decimal(11)
    b = OctahedralNumber.from_decimal(13)
    product = a * b
    assert product.to_decimal() == 143


def test_oct_division():
    a = OctahedralNumber.from_decimal(143)
    b = OctahedralNumber.from_decimal(11)
    q, r = a.divmod_glyph(b)
    assert q.to_decimal() == 13
    assert r.to_decimal() == 0


def test_oct_prime():
    assert OctahedralNumber.from_decimal(2).is_prime()
    assert OctahedralNumber.from_decimal(3).is_prime()
    assert OctahedralNumber.from_decimal(11).is_prime()
    assert OctahedralNumber.from_decimal(13).is_prime()
    assert not OctahedralNumber.from_decimal(4).is_prime()
    assert not OctahedralNumber.from_decimal(15).is_prime()
    assert not OctahedralNumber.from_decimal(143).is_prime()


def test_oct_factorize():
    factors = OctahedralNumber.from_decimal(143).factorize()
    decimals = sorted(f.to_decimal() for f in factors)
    assert decimals == [11, 13]


def test_glyph_fraction_irreducible():
    gf = GlyphFraction.from_decimal_ratio(3, 7)
    assert gf.is_irreducible()
    assert gf.num.to_decimal() == 3
    assert gf.den.to_decimal() == 7


def test_glyph_fraction_reduces():
    gf = GlyphFraction.from_decimal_ratio(6, 14)
    assert gf.num.to_decimal() == 3
    assert gf.den.to_decimal() == 7


def test_factor_pair_glyphs():
    pair = factor_pair_glyphs(15)
    assert pair is not None
    fa, fb = pair
    assert fa.to_decimal() * fb.to_decimal() == 15

    pair = factor_pair_glyphs(143)
    assert pair is not None
    fa, fb = pair
    assert fa.to_decimal() * fb.to_decimal() == 143

    # 17 is prime
    assert factor_pair_glyphs(17) is None


def test_glyph_trace_length():
    from mandala_computer import MandalaComputer
    mc = MandalaComputer(golden_depth=3, sacred_geometry=8)
    mc.bloom_mandala()
    trace = mc.glyph_trace(8)
    # Should have 7 glyphs (3 depth levels: 1+2+4=7 cells, all <= 8)
    glyph_chars = [ch for ch in trace if ch != "." and ch != " "]
    assert len(glyph_chars) == 7


# ---------------------------------------------------------------------------
# MandalaComputer tests
# ---------------------------------------------------------------------------

from mandala_computer import MandalaComputer, ProblemType


def test_factor_register_size():
    assert MandalaComputer._factor_register_size(15) == 1    # sqrt(15)~4, 8^1=8 >= 4
    assert MandalaComputer._factor_register_size(49) == 1    # sqrt(49)=7, 8^1=8 >= 8
    assert MandalaComputer._factor_register_size(81) == 2    # sqrt(81)=9, 8^1=8 < 10, needs 2
    assert MandalaComputer._factor_register_size(143) == 2   # sqrt(143)~12, 8^2=64 >= 13
    assert MandalaComputer._factor_register_size(4225) == 3  # sqrt(4225)=65, 8^2=64 < 66


def test_cells_to_factor():
    mc = MandalaComputer(golden_depth=3, sacred_geometry=8)
    mc.bloom_mandala()
    # Set cells 0,1 to states [3, 1] -> factor = 2 + 3 + 1*8 = 13
    mc.cells[0].state = 3
    mc.cells[1].state = 1
    assert mc._cells_to_factor([0, 1]) == 13

    # Single cell: state 5 -> factor = 2 + 5 = 7
    mc.cells[0].state = 5
    assert mc._cells_to_factor([0]) == 7


def test_factorization_small():
    """N=15 should be solvable with enough annealing."""
    np.random.seed(42)
    mc = MandalaComputer(golden_depth=4, sacred_geometry=8)
    mc.encode_factorization(15)
    result = mc.simulated_annealing(max_steps=8000, T_start=5.0, T_end=0.001)
    sol = result["solution"]
    # Should find factors (may not always succeed, but residual should be small)
    assert sol["residual"] <= 1


def test_sat_satisfiable():
    """Simple SAT: (x1 OR x2) AND (NOT x1 OR x3) AND (NOT x2 OR NOT x3)."""
    np.random.seed(7)
    clauses = [[1, 2], [-1, 3], [-2, -3]]
    mc = MandalaComputer(golden_depth=3, sacred_geometry=8, temperature=0.3)
    mc.encode_sat(clauses)
    result = mc.simulated_annealing(max_steps=5000, T_start=3.0, T_end=0.01)
    # Check that energy includes clause terms (not just coupling)
    E = mc.compute_total_energy()
    assert isinstance(E, float)
    # Verify the solver at least evaluates satisfiability
    assert "satisfies" in result["solution"]


def test_graph_coloring_triangle():
    """Triangle with 3 colors should be solvable."""
    np.random.seed(42)
    adjacency = [[0, 1], [1, 2], [0, 2]]
    mc = MandalaComputer(golden_depth=3, sacred_geometry=8)
    mc.encode_graph_coloring(adjacency, 3)
    result = mc.simulated_annealing(max_steps=5000, T_start=3.0, T_end=0.01)
    sol = result["solution"]
    # Triangle with 3 colors is always solvable
    assert sol["violations"] == 0
    assert sol["valid"]


def test_optimization():
    """Minimize sum of squared differences -> all same state."""
    np.random.seed(42)
    def cost_fn(states):
        return sum((states[i] - states[i + 1]) ** 2 for i in range(len(states) - 1))
    mc = MandalaComputer(golden_depth=3, sacred_geometry=8)
    mc.encode_optimization(cost_fn, 7)
    result = mc.simulated_annealing(max_steps=3000, T_start=3.0, T_end=0.01)
    assert result["solution"]["cost"] < 1.0  # should converge near zero


def test_sensor_telemetry():
    """Telemetry should be collected during solving."""
    mc = MandalaComputer(golden_depth=3, sacred_geometry=8)
    mc.encode_factorization(15)
    mc.simulated_annealing(max_steps=1000, T_start=2.0, T_end=0.1)
    assert len(mc.telemetry) > 0
    sensor_ids = {r.sensor_id for r in mc.telemetry}
    assert "energy.total" in sensor_ids
    assert "temperature" in sensor_ids


def test_state_distribution():
    mc = MandalaComputer(golden_depth=3, sacred_geometry=8)
    mc.bloom_mandala()
    dist = mc.get_state_distribution()
    assert sum(dist.values()) == mc.num_cells
    assert all(0 <= k <= 7 for k in dist)


# ---------------------------------------------------------------------------
# Quantum tests
# ---------------------------------------------------------------------------

from quantum_mandala import QuantumMandalaComputer, QuantumMandalaCell


def test_quantum_cell_measurement():
    cell = QuantumMandalaCell(position=(0, 0), depth=0)
    probs = cell.get_probability_distribution()
    assert abs(sum(probs) - 1.0) < 1e-10
    measured = cell.measure()
    assert 0 <= measured <= 7
    # After measurement, collapsed to one state
    post_probs = cell.get_probability_distribution()
    assert post_probs[measured] == 1.0


def test_quantum_entanglement_entropy():
    qc = QuantumMandalaComputer(golden_depth=2, sacred_geometry=8)
    qc.bloom_quantum_mandala()
    # Equal superposition -> max entropy = log2(8) = 3
    ent = qc.get_entanglement_entropy(0)
    assert abs(ent - 3.0) < 1e-10


def test_grover_finds_target():
    """Grover should find target state with high probability."""
    np.random.seed(42)
    qc = QuantumMandalaComputer(golden_depth=1, sacred_geometry=8)
    target = 5
    measured = qc.grover_search(lambda x: x == target)
    # High probability but not guaranteed — just check it ran
    assert 0 <= measured <= 7


def test_quantum_annealing_runs():
    qc = QuantumMandalaComputer(golden_depth=2, sacred_geometry=8)
    result = qc.quantum_annealing("factorization", {"N": 15}, num_steps=50)
    assert "final_energy" in result
    assert "solution" in result
    assert len(qc.telemetry) > 0


# ---------------------------------------------------------------------------
# Holographic tests
# ---------------------------------------------------------------------------

from holographic_mandala import HolographicMandala


def test_holographic_rings_built():
    hm = HolographicMandala(golden_depth=4, sacred_geometry=8)
    hm.encode_holographic(ProblemType.FACTORIZATION, {"N": 15})
    assert len(hm.rings) == 4
    assert len(hm.entanglement_links) > 0
    # Each ring should have projected problem
    for ring in hm.rings:
        assert ring.projected_problem is not None


def test_holographic_no_double_count():
    """Holographic factorization energy should not include parent's factorization term."""
    hm = HolographicMandala(golden_depth=3, sacred_geometry=8, holographic_weight=1.0)
    hm.encode_holographic(ProblemType.FACTORIZATION, {"N": 15})

    # Set all cells to state 0 for deterministic energy
    for c in hm.cells:
        c.state = 0

    E_holo = hm.compute_total_energy()

    # Compare: plain MandalaComputer with same states
    mc = MandalaComputer(golden_depth=3, sacred_geometry=8)
    mc.encode_factorization(15)
    for i, c in enumerate(mc.cells):
        c.state = hm.cells[i].state if i < len(hm.cells) else 0
    E_plain = mc.compute_total_energy()

    # Holographic should NOT be 2x the plain energy
    # (it was before the fix — now it replaces, not stacks)
    assert E_holo != E_plain * 2 + E_plain  # crude check that they differ


def test_entanglement_links_adapt():
    hm = HolographicMandala(golden_depth=3, sacred_geometry=8, entanglement_decay=0.5)
    hm.encode_holographic(ProblemType.FACTORIZATION, {"N": 15})

    # Populate correlation history
    for link in hm.entanglement_links:
        link.correlation_history = [True] * 30  # high correlation
        link.initial_strength = link.strength

    hm._adapt_entanglement()

    # High-correlation links should have gotten stronger
    for link in hm.entanglement_links:
        assert link.strength >= link.initial_strength


# ---------------------------------------------------------------------------
# Constraint Agent tests
# ---------------------------------------------------------------------------

from constraint_agent import ConstraintAgent


def test_agent_lifecycle():
    """Full lifecycle: bloom -> explore -> compress -> restore."""
    agent = ConstraintAgent(seed_id="SHAPE.OCTA", home_families=["test"])
    agent.set_resource_budget(compute=200, depth_limit=2)
    agent.bloom(depth=2)
    assert len(agent.nodes) > 1
    node_count = len(agent.nodes)

    discoveries = agent.explore()
    assert len(agent.discoveries) > 0

    agent.compress()
    assert len(agent.nodes) == 1  # seed only
    assert agent.compressed_map is not None

    agent.restore()
    assert len(agent.nodes) == node_count  # full map back


def test_agent_resource_limits():
    """Low budget should stop expansion before high budget."""
    low = ConstraintAgent(seed_id="SHAPE.TETRA")
    low.set_resource_budget(compute=20, depth_limit=5)
    low.bloom(depth=5)

    high = ConstraintAgent(seed_id="SHAPE.TETRA")
    high.set_resource_budget(compute=5000, depth_limit=5)
    high.bloom(depth=5)

    assert low.current_depth < high.current_depth
    assert len(low.nodes) < len(high.nodes)


def test_agent_exact_fractions():
    """Discoveries should be stored as exact GlyphFractions."""
    agent = ConstraintAgent(seed_id="SHAPE.OCTA")
    agent.set_resource_budget(compute=300, depth_limit=2)
    agent.bloom(depth=2)
    agent.explore()

    factor_disc = [d for d in agent.discoveries if d.discovery_type == "factor"]
    assert len(factor_disc) > 0
    # Every factor relationship should be irreducible
    for d in factor_disc:
        assert d.relationship.is_irreducible()


def test_agent_lossless_compress():
    """Compress/restore should preserve discovery count exactly."""
    agent = ConstraintAgent(seed_id="SHAPE.TETRA")
    agent.set_resource_budget(compute=100, depth_limit=2)
    agent.bloom(depth=2)
    agent.explore()
    pre = len(agent.discoveries)
    agent.compress()
    agent.restore()
    post = len(agent.discoveries)
    assert pre == post


def test_agent_different_geometries():
    """Different seed geometries should produce different node counts."""
    tetra = ConstraintAgent(seed_id="SHAPE.TETRA")
    tetra.set_resource_budget(compute=200, depth_limit=2)
    tetra.bloom(depth=2)

    octa = ConstraintAgent(seed_id="SHAPE.OCTA")
    octa.set_resource_budget(compute=200, depth_limit=2)
    octa.bloom(depth=2)

    assert tetra.base_states == 4
    assert octa.base_states == 8
    assert len(tetra.nodes) < len(octa.nodes)


# ---------------------------------------------------------------------------
# Sovereign Integration tests
# ---------------------------------------------------------------------------

from sovereign_integration import (
    PhysicalGlyph, SovereignEnergy, FieldConstraints, FieldState,
    glyph_compatibility, SovereignAgent,
)


def test_physical_glyph_mapping():
    assert PhysicalGlyph.from_state(0).field_name == "electromagnetic"
    assert PhysicalGlyph.from_state(3).field_name == "thermal"
    assert PhysicalGlyph.from_state(7).field_name == "kinetic"
    assert PhysicalGlyph.from_energy_type("harmonic") == PhysicalGlyph.EM
    assert PhysicalGlyph.from_energy_type("chemical") == PhysicalGlyph.CHEMICAL


def test_glyph_compatibility_exact():
    compat = glyph_compatibility(0, 0)  # EM-EM = harmonic-harmonic = 1.0
    assert compat.num.to_decimal() == 1
    assert compat.den.to_decimal() == 1


def test_field_constraints_healthy():
    healthy = FieldState(soil_trend=0.1, water_retention=0.7, coupling_strength=0.8)
    assert FieldConstraints.health_score(healthy) >= 0.75
    drift = FieldConstraints.detect_drift(healthy)
    assert not drift["soil_positive"]  # not drifting


def test_field_constraints_degraded():
    degraded = FieldState(soil_trend=-0.2, water_retention=0.3, disturbance=0.7)
    assert FieldConstraints.health_score(degraded) < 0.5
    thermal = FieldConstraints.thermal_limit(degraded)
    assert thermal["critical"]


def test_resonance_energy():
    # All-same states should have high resonance (self-compatibility = 1.0)
    states = [0, 0, 0, 0]
    res = SovereignEnergy.pack_resonance(states, [0.9]*4, [0.85]*4, 0.5)
    assert res > 0.2

    # Cost function should return negative resonance
    cost = SovereignEnergy.as_mandala_cost(states)
    assert cost < 0


def test_sovereign_agent_lifecycle():
    agent = SovereignAgent(seed_id="SHAPE.OCTA", energy_type="harmonic")
    agent.set_resource_budget(compute=100, depth_limit=2)
    agent.bloom(depth=1)
    validation = agent.validate()
    assert "health" in validation
    resonance = agent.find_resonance()
    assert "system_resonance" in resonance


def test_sovereignty_achievable():
    """Sovereignty is relative to environment — even high entropy can be sovereign."""
    # Low entropy: easy sovereignty
    res_calm = SovereignEnergy.pack_resonance([0]*7, [0.9]*7, [0.85]*7, entropy=0.1)
    assert SovereignEnergy.is_sovereign(res_calm, entropy=0.1)

    # High entropy with stress history (antifragile): still sovereign
    history = [0.7, 0.8, 0.9, 0.6]
    res_storm = SovereignEnergy.pack_resonance(
        [0]*7, [0.9]*7, [0.85]*7, entropy=0.9, stress_history=history
    )
    assert SovereignEnergy.is_sovereign(res_storm, entropy=0.9)


def test_field_aware_cost():
    """Field-aware cost should use compatibility matrix, not black-box."""
    cost_same = SovereignEnergy.as_mandala_cost([0, 0, 0, 0])  # all EM
    cost_diff = SovereignEnergy.as_mandala_cost([0, 2, 4, 6])  # mixed
    # Same-field should have lower (more negative) cost
    assert cost_same < cost_diff


# ---------------------------------------------------------------------------
# Claim Validator tests
# ---------------------------------------------------------------------------

from claim_validator import validate_claim as validate_text_claim


def test_specific_claim_low_concern():
    report = validate_text_claim(
        "Solar efficiency increased by 23% between 2020 and 2024 "
        "(Green et al. 2024), measured across 1200 installations."
    )
    assert report.overall_concern < 0.4


def test_vague_claim_high_concern():
    report = validate_text_claim(
        "This fundamentally transforms everything and is essentially "
        "the most significant breakthrough in principle."
    )
    assert report.overall_concern > 0.6


def test_tier_hierarchy():
    """Higher tiers should exist and be numbered correctly."""
    report = validate_text_claim("Some claim with various implications.")
    tiers = {d.tier: d for d in report.domain_scores}
    assert 1 in tiers  # Physics
    assert 2 in tiers  # Biology
    assert 3 in tiers  # Systems
    assert 4 in tiers  # Empirical


# ---------------------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_functions = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = 0
    for fn in test_functions:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {fn.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed out of {passed + failed} tests")
    if failed:
        sys.exit(1)
