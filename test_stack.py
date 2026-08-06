#!/usr/bin/env python3
import sys, os, importlib, traceback

modules = [
    'quantum_mandala',
    'octahedral_arithmetic',
    'scale_invariance_breakdown',
    'consumer_hardware',
]

print("="*60)
print("MANDALA STACK INTEGRATION TEST")
print("="*60)

all_ok = True
for mod in modules:
    try:
        m = importlib.import_module(mod)
        print(f"  [PASS] {mod}")
    except Exception as e:
        print(f"  [FAIL] {mod}: {e}")
        traceback.print_exc()
        all_ok = False

# Test key class instantiations
print("\n--- Class instantiation ---")
try:
    from quantum_mandala import QuantumMandalaComputer
    qc = QuantumMandalaComputer(golden_depth=1, sacred_geometry=8)
    print("  [PASS] QuantumMandalaComputer")
except Exception as e:
    print(f"  [FAIL] QuantumMandalaComputer: {e}")
    all_ok = False

try:
    from octahedral_arithmetic import OctahedralNumber
    n = OctahedralNumber.from_decimal(42)
    print(f"  [PASS] OctahedralNumber ({n})")
except Exception as e:
    print(f"  [FAIL] OctahedralNumber: {e}")
    all_ok = False

try:
    from consumer_hardware import ConsumerGeometricComputer
    c = ConsumerGeometricComputer()
    print("  [PASS] ConsumerGeometricComputer")
except Exception as e:
    print(f"  [FAIL] ConsumerGeometricComputer: {e}")
    all_ok = False

print("\n" + "="*60)
print("RESULT: " + ("ALL TESTS PASSED" if all_ok else "SOME TESTS FAILED"))
print("="*60)
