"""
Example: Octahedral Symbolic Language (OSL) v1.0

Demonstrates the full OSL pipeline:
  1. Glyph registry and vertex mapping
  2. Tokenization of Unicode glyph strings
  3. Parity verification (tensor + geometric)
  4. Animal strategy macro expansion
  5. Full transpilation pipeline
  6. Bridge to geometric state algebra (O_h group)
  7. Token compression comparison

Run: python examples/example-osl.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from osl import (
    demo_registry, demo_tokenize, demo_parity,
    demo_macros, demo_transpile, demo_group_bridge,
    demo_compression,
)


if __name__ == "__main__":
    print()
    print("OCTAHEDRAL SYMBOLIC LANGUAGE (OSL) v1.0")
    print("Geometric DSL for octahedral computation")
    print()

    # 1. Full glyph registry
    demo_registry()

    # 2. Tokenization examples
    demo_tokenize()

    # 3. Parity verification
    demo_parity()

    # 4. Animal macro expansion
    demo_macros()

    # 5. Full transpilation pipeline
    demo_transpile()

    # 6. Bridge to O_h group algebra
    demo_group_bridge()

    # 7. Compression ratio
    demo_compression()

    print()
    print("=" * 60)
    print("OSL demo complete.")
    print("=" * 60)
