"""
GEOMETRIC INFORMATION ENCODING SYSTEM (GEIS) v1.0
Bridge between geometric octahedral states and binary representation.

Ported from Geometric-to-Binary-Computational-Bridge/GEIS and adapted
for the Mandala Computing framework.  Provides:

  OctahedralState    — 8 vertex positions in cubic coordinates, binary/token notation
  GeometricEncoder   — bidirectional token <-> flat binary conversion
  StateTensor        — 3x3 symmetric tensor (outer product) per state
  vector_to_token    — map arbitrary 3D direction + phase to a geometric token
  find_dependencies  — discover tensor-cancellation dependencies in token streams
  bits_to_cube / find_cube_dependencies — 3D binary cube XOR dependency search

Integration helpers:
  cell_state_to_token  — MandalaCell state (0-7) -> GEIS token
  token_to_cell_state  — GEIS token -> cell state integer
  cells_to_tensor_map  — build tensor fingerprint for a MandalaComputer config
"""

from __future__ import annotations

import math
import numpy as np
from typing import List, Tuple, Dict, Optional
from collections import defaultdict
from itertools import combinations
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PHI = (1 + math.sqrt(5)) / 2

# ---------------------------------------------------------------------------
# OctahedralState
# ---------------------------------------------------------------------------

class OctahedralState:
    """
    One of 8 octahedral vertex positions in cubic coordinates.

    Each state maps to a 3-bit binary address (000-111) and can be
    expressed as a geometric token like '001|O'.
    """

    POSITIONS: Dict[int, Tuple[float, float, float]] = {
        0: ( 0.25,  0.25,  0.25),   # (+,+,+)
        1: ( 0.25, -0.25,  0.25),   # (+,-,+)
        2: (-0.25,  0.25,  0.25),   # (-,+,+)
        3: (-0.25, -0.25,  0.25),   # (-,-,+)
        4: ( 0.25,  0.25, -0.25),   # (+,+,-)
        5: ( 0.25, -0.25, -0.25),   # (+,-,-)
        6: (-0.25,  0.25, -0.25),   # (-,+,-)
        7: (-0.25, -0.25, -0.25),   # (-,-,-)
    }

    # Unit-sphere normalised positions (matching POSITIONS index order)
    _UNIT_POSITIONS: List[np.ndarray] = []
    for _i in range(8):
        _v = np.array(POSITIONS[_i], dtype=float)
        _v = _v / np.linalg.norm(_v)
        _UNIT_POSITIONS.append(_v)

    def __init__(self, index: int):
        if not isinstance(index, int) or not (0 <= index <= 7):
            raise ValueError("Index must be integer 0-7")
        self.index = index
        self.position = np.array(self.POSITIONS[index])

    # -- conversions --------------------------------------------------------

    def to_binary(self, width: int = 3) -> str:
        """State index as zero-padded binary string."""
        return format(self.index, f'0{width}b')

    def to_token(self, operator: str = '|', symbol: str = 'O') -> str:
        """Geometric token notation, e.g. '001|O'."""
        return f"{self.to_binary()}{operator}{symbol}"

    @classmethod
    def from_token(cls, token: str) -> OctahedralState:
        """Parse a token back to a state."""
        for op in ('||', '|', '/', ':'):
            if op in token:
                binary_str = token.split(op, 1)[0]
                return cls(int(binary_str, 2))
        raise ValueError("Token must contain an operator ('|', '/', ':')")

    @classmethod
    def from_binary(cls, binary_str: str) -> OctahedralState:
        """Create state from a binary string like '110'."""
        return cls(int(binary_str, 2))

    @classmethod
    def closest(cls, vec: np.ndarray) -> OctahedralState:
        """Find the vertex closest to an arbitrary 3-D direction."""
        v = np.asarray(vec, dtype=float)
        v = v / np.linalg.norm(v)
        dots = [np.dot(v, p) for p in cls._UNIT_POSITIONS]
        return cls(int(np.argmax(dots)))

    # -- operations ---------------------------------------------------------

    def invert(self) -> OctahedralState:
        """Octahedral inversion (NOT): i -> 7 - i."""
        return OctahedralState(7 - self.index)

    def distance_to(self, other: OctahedralState) -> float:
        """Euclidean distance to another state."""
        return float(np.linalg.norm(self.position - other.position))

    def dot_product(self, other: OctahedralState) -> float:
        """Dot product with another state's position."""
        return float(np.dot(self.position, other.position))

    # -- dunder -------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        return isinstance(other, OctahedralState) and self.index == other.index

    def __hash__(self) -> int:
        return hash(self.index)

    def __repr__(self) -> str:
        return f"OctahedralState(index={self.index}, pos={tuple(self.position)})"

    def __str__(self) -> str:
        return f"O{self.index}@{self.to_binary()}"


# ---------------------------------------------------------------------------
# GeometricEncoder
# ---------------------------------------------------------------------------

class GeometricEncoder:
    """
    Bidirectional encoder between geometric tokens and flat binary.

    Token anatomy:  <vertex_bits><operator><symbol>
        vertex_bits : 3-bit address (000-111)
        operator    : '|' radial, '/' tangential, '||' nested shell
        symbol      : O (octahedral), I (inversion), X (exchange), Delta (delta)

    Binary layout:  [vertex 3b][operator 1-2b][symbol 2b]  = 6 or 7 bits
    """

    SYMBOL_MAP = {'O': '00', 'I': '01', 'X': '10', '\u0394': '11'}
    REVERSE_SYMBOL_MAP = {v: k for k, v in SYMBOL_MAP.items()}

    OPERATOR_MAP = {'|': '1', '/': '0', ':': '0'}
    REVERSE_OPERATOR_MAP = {'1': '|', '0': '/'}

    def __init__(self, vertex_width: int = 3):
        self.vertex_width = vertex_width

    def encode_to_binary(self, token: str) -> str:
        """Convert geometric token to flat binary.  '001|O' -> '001100'."""
        if '||' in token:
            parts = token.split('||', 1)
            vertex_bits = parts[0]
            symbol = parts[1][0] if parts[1] else 'O'
            operator_bits = '11'
        else:
            operator_found = next((op for op in ('|', '/', ':') if op in token), None)
            if operator_found is None:
                raise ValueError("Token must contain operator ('|', '/', or ':')")
            parts = token.split(operator_found, 1)
            vertex_bits = parts[0]
            symbol = parts[1][0] if parts[1] else 'O'
            operator_bits = self.OPERATOR_MAP[operator_found]

        if len(vertex_bits) != self.vertex_width:
            raise ValueError(f"Vertex bits must be {self.vertex_width} wide, got {len(vertex_bits)}")
        int(vertex_bits, 2)  # validate binary

        if symbol not in self.SYMBOL_MAP:
            raise ValueError(f"Unknown symbol '{symbol}'. Valid: {list(self.SYMBOL_MAP.keys())}")

        return vertex_bits + operator_bits + self.SYMBOL_MAP[symbol]

    def decode_from_binary(self, binary_string: str) -> str:
        """Convert flat binary back to geometric token.  '001100' -> '001|O'."""
        min_length = self.vertex_width + 3
        if len(binary_string) < min_length:
            raise ValueError(f"Binary string too short (need {min_length} bits)")

        vertex_bits = binary_string[:self.vertex_width]
        op_start = self.vertex_width

        if (len(binary_string) >= self.vertex_width + 4
                and binary_string[op_start:op_start + 2] == '11'):
            operator = '||'
            symbol_bits = binary_string[op_start + 2:op_start + 4]
        else:
            operator = self.REVERSE_OPERATOR_MAP.get(binary_string[op_start], '|')
            symbol_bits = binary_string[op_start + 1:op_start + 3]

        symbol = self.REVERSE_SYMBOL_MAP.get(symbol_bits, 'O')
        return f"{vertex_bits}{operator}{symbol}"

    def validate_token(self, token: str) -> bool:
        """True if token round-trips cleanly."""
        try:
            return self.decode_from_binary(self.encode_to_binary(token)) == token
        except Exception:
            return False

    def get_components(self, token: str) -> Tuple[str, str, str]:
        """Return (vertex_bits, operator, symbol)."""
        for op in ('||', '|', '/'):
            if op in token:
                parts = token.split(op, 1)
                symbol = parts[1][0] if parts[1] else 'O'
                return parts[0], op, symbol
        raise ValueError("Invalid token format")


# ---------------------------------------------------------------------------
# StateTensor
# ---------------------------------------------------------------------------

class StateTensor:
    """
    3x3 symmetric tensor for an octahedral state.

    The tensor is the outer product of the state's position vector,
    optionally weighted by electron-density-like factor.
    """

    def __init__(self, state: OctahedralState, weight: float = 1.0):
        self.state = state
        self.weight = weight
        self.vector = state.position
        self.tensor = self._calculate_tensor()

    def _calculate_tensor(self) -> np.ndarray:
        v = self.vector * self.weight
        return np.outer(v, v)

    def project(self, direction: np.ndarray) -> float:
        """Scalar projection n-hat . T . n-hat  (the | operator)."""
        n = np.asarray(direction, dtype=float)
        n = n / np.linalg.norm(n)
        return float(n @ self.tensor @ n)

    def eigenvalues(self) -> np.ndarray:
        return np.linalg.eigvalsh(self.tensor)

    def eigenvectors(self) -> Tuple[np.ndarray, np.ndarray]:
        return np.linalg.eigh(self.tensor)

    def trace(self) -> float:
        return float(np.trace(self.tensor))

    def determinant(self) -> float:
        return float(np.linalg.det(self.tensor))

    def norm(self) -> float:
        """Frobenius norm."""
        return float(np.linalg.norm(self.tensor))

    @staticmethod
    def combine(tensors: List[StateTensor]) -> np.ndarray:
        """Sum of individual tensors."""
        if not tensors:
            return np.zeros((3, 3))
        return sum((t.tensor for t in tensors), np.zeros((3, 3)))

    def rotate(self, rotation_matrix: np.ndarray) -> StateTensor:
        """T' = R T R^T, snapped to closest octahedral vertex."""
        R = np.asarray(rotation_matrix, dtype=float)
        rotated_tensor = R @ self.tensor @ R.T
        rotated_pos = R @ self.vector
        distances = [np.linalg.norm(rotated_pos - np.array(OctahedralState.POSITIONS[i]))
                     for i in range(8)]
        result = StateTensor(OctahedralState(int(np.argmin(distances))), self.weight)
        result.tensor = rotated_tensor
        return result

    def __repr__(self) -> str:
        return f"StateTensor(state={self.state.index}, weight={self.weight})"


# ---------------------------------------------------------------------------
# Geometric sensor simulation
# ---------------------------------------------------------------------------

def vector_to_token(direction: np.ndarray, phase: float = 0.0) -> str:
    """
    Convert a 3-D direction vector and phase angle (degrees) to a GEIS token.

    Vertex determined by closest octahedral position.
    Operator: '|' if direction aligns with radial axis (1,1,1), else '/'.
    Symbol mapped from phase quadrant: O(0), I(90), X(180), Delta(270).
    """
    d = np.asarray(direction, dtype=float)
    state = OctahedralState.closest(d)
    vertex_bits = state.to_binary()

    radial = np.array([1, 1, 1]) / math.sqrt(3)
    dot = abs(np.dot(d / np.linalg.norm(d), radial))
    operator = '|' if dot > 0.7 else '/'

    symbol_idx = int(round((phase % 360) / 90.0)) % 4
    symbol = ['O', 'I', 'X', '\u0394'][symbol_idx]

    return f"{vertex_bits}{operator}{symbol}"


def random_token() -> str:
    """Generate a random geometric token."""
    vertex_bits = format(np.random.randint(0, 8), '03b')
    operator = np.random.choice(['|', '/'])
    symbol = np.random.choice(['O', 'I', 'X', '\u0394'])
    return f"{vertex_bits}{operator}{symbol}"


# ---------------------------------------------------------------------------
# Tensor dependency finding
# ---------------------------------------------------------------------------

def token_to_tensor(token: str) -> np.ndarray:
    """3x3 outer-product tensor for a token's vertex vector."""
    idx = int(token[:3], 2)
    v = OctahedralState._UNIT_POSITIONS[idx]
    return np.outer(v, v)


def find_dependencies(tokens: List[str], max_len: int = 4) -> List[List[int]]:
    """
    Find subsets of token indices whose tensors sum to near-zero (norm < 1e-6).

    Uses brute-force for pairs/triples and meet-in-the-middle for quadruples.
    """
    tensors = [token_to_tensor(tok) for tok in tokens]
    n = len(tokens)
    deps: List[List[int]] = []

    def _norm(T: np.ndarray) -> float:
        return float(np.linalg.norm(T))

    # Pairs
    for i in range(n):
        for j in range(i + 1, n):
            if _norm(tensors[i] + tensors[j]) < 1e-6:
                deps.append([i, j])

    # Triples
    if max_len >= 3 and n <= 200:
        for i in range(n):
            for j in range(i + 1, n):
                Tij = tensors[i] + tensors[j]
                for k in range(j + 1, n):
                    if _norm(Tij + tensors[k]) < 1e-6:
                        deps.append([i, j, k])

    # Meet-in-the-middle for length-4
    if max_len >= 4 and n <= 500:
        half = n // 2
        sum_map: Dict[tuple, List[Tuple[int, ...]]] = defaultdict(list)
        for l in range(1, max_len // 2 + 1):
            for combo in combinations(range(half), l):
                S = sum((tensors[i] for i in combo), np.zeros((3, 3)))
                key = tuple(np.round(S.flatten(), decimals=10))
                sum_map[key].append(combo)
        for l in range(1, max_len - max_len // 2 + 1):
            for combo in combinations(range(half, n), l):
                S = sum((tensors[i] for i in combo), np.zeros((3, 3)))
                target = tuple(np.round((-S).flatten(), decimals=10))
                if target in sum_map:
                    for first in sum_map[target]:
                        combined = list(first) + list(combo)
                        if len(combined) <= max_len:
                            deps.append(combined)

    # Deduplicate
    seen: set = set()
    unique: List[List[int]] = []
    for dep in deps:
        key = tuple(sorted(dep))
        if key not in seen:
            seen.add(key)
            unique.append(dep)
    return unique


# ---------------------------------------------------------------------------
# 3-D binary cube operations
# ---------------------------------------------------------------------------

def bits_to_cube(bits: str, side: Optional[int] = None) -> np.ndarray:
    """Convert binary string to a 3-D cube, padding with zeros."""
    n_bits = len(bits)
    if side is None:
        side = int(math.ceil(n_bits ** (1 / 3)))
    cube = np.zeros((side, side, side), dtype=np.uint8)
    idx = 0
    for i in range(side):
        for j in range(side):
            for k in range(side):
                if idx < n_bits:
                    cube[i, j, k] = int(bits[idx])
                idx += 1
    return cube


def cube_to_bits(cube: np.ndarray) -> str:
    """Flatten cube back to binary string."""
    return ''.join(str(b) for b in cube.flatten())


def cube_xor(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Pointwise XOR of two cubes."""
    return a ^ b


def cube_norm(cube: np.ndarray) -> int:
    """Number of 1-bits (Hamming weight)."""
    return int(np.sum(cube))


def all_rotations_reflections(cube: np.ndarray) -> List[np.ndarray]:
    """
    All distinct rotations and reflections of a cube (full octahedral group).

    Generates up to 48 unique orientations via 90-degree rotations and
    single-axis reflection.
    """
    unique: Dict[bytes, np.ndarray] = {}
    for x in range(4):
        for y in range(4):
            for z in range(4):
                rot = np.rot90(cube, x, axes=(0, 1))
                rot = np.rot90(rot, y, axes=(0, 2))
                rot = np.rot90(rot, z, axes=(1, 2))
                key = rot.tobytes()
                if key not in unique:
                    unique[key] = rot.copy()
                flipped = np.flip(rot, axis=0)
                fkey = flipped.tobytes()
                if fkey not in unique:
                    unique[fkey] = flipped.copy()
    return list(unique.values())


def canonical_form(cube: np.ndarray) -> bytes:
    """Lexicographically smallest byte representation among all orientations."""
    best: Optional[bytes] = None
    for rot in all_rotations_reflections(cube):
        flat = rot.tobytes()
        if best is None or flat < best:
            best = flat
    return best  # type: ignore[return-value]


def find_cube_dependencies(cubes: List[np.ndarray],
                           max_comb: int = 4) -> List[List[int]]:
    """
    Find subsets of cubes whose XOR sum is zero.

    Phase 1 — exact duplicate pairs.
    Phase 2 — brute-force small combinations (n <= 30).
    """
    n = len(cubes)
    deps: List[List[int]] = []

    # Phase 1: exact-duplicate pairs
    hash_map: Dict[bytes, List[int]] = defaultdict(list)
    for i, c in enumerate(cubes):
        hash_map[c.tobytes()].append(i)
    for indices in hash_map.values():
        for a in range(len(indices)):
            for b in range(a + 1, len(indices)):
                deps.append([indices[a], indices[b]])

    # Phase 2: brute-force small combinations
    if n <= 30:
        for r in range(2, max_comb + 1):
            for combo in combinations(range(n), r):
                total = np.zeros_like(cubes[0])
                for idx in combo:
                    total ^= cubes[idx]
                if cube_norm(total) == 0:
                    deps.append(list(combo))

    # Deduplicate
    seen: set = set()
    unique: List[List[int]] = []
    for dep in deps:
        key = tuple(sorted(dep))
        if key not in seen:
            seen.add(key)
            unique.append(dep)
    return unique


# ---------------------------------------------------------------------------
# Mandala integration helpers
# ---------------------------------------------------------------------------

def cell_state_to_token(state: int, operator: str = '|',
                        symbol: str = 'O') -> str:
    """Convert a MandalaCell state (0-7) to a GEIS token."""
    if not (0 <= state <= 7):
        raise ValueError("Cell state must be 0-7")
    return f"{format(state, '03b')}{operator}{symbol}"


def token_to_cell_state(token: str) -> int:
    """Extract the cell state integer (0-7) from a GEIS token."""
    return OctahedralState.from_token(token).index


def cells_to_tensor_map(states: List[int]) -> np.ndarray:
    """
    Build a combined tensor fingerprint from a list of cell states.

    Each state (0-7) contributes its outer-product tensor.
    The result is the sum — useful for analysing geometric balance
    and finding cancellations in a MandalaComputer configuration.
    """
    tensors = [StateTensor(OctahedralState(s)) for s in states]
    return StateTensor.combine(tensors)


def state_tensor_profile(states: List[int]) -> Dict[str, object]:
    """
    Tensor analysis of a cell-state configuration.

    Returns eigenvalues, trace, determinant, and norm of the
    combined tensor — a geometric fingerprint of the configuration.
    """
    combined = cells_to_tensor_map(states)
    evals = np.linalg.eigvalsh(combined)
    return {
        "eigenvalues": evals.tolist(),
        "trace": float(np.trace(combined)),
        "determinant": float(np.linalg.det(combined)),
        "norm": float(np.linalg.norm(combined)),
        "num_states": len(states),
    }


# ---------------------------------------------------------------------------
# Demonstrations
# ---------------------------------------------------------------------------

def demo_basic_states():
    """Show all 8 octahedral states with positions and tokens."""
    print("=" * 60)
    print("GEIS: All 8 Octahedral States")
    print("=" * 60)
    enc = GeometricEncoder()
    for i in range(8):
        s = OctahedralState(i)
        token = s.to_token()
        binary = enc.encode_to_binary(token)
        pos = tuple(s.position)
        print(f"  {i}: {str(s):12s}  token={token}  binary={binary}  pos={pos}")
    print()


def demo_dual_mode_encoding():
    """Demonstrate the |O bridge symbol and round-trip encoding."""
    print("=" * 60)
    print("GEIS: Dual-Mode Encoding (Bridge Symbol |O)")
    print("=" * 60)
    enc = GeometricEncoder()
    tokens = ['001|O', '101|X', '010/I', '110|\u0394', '001||O']
    for token in tokens:
        binary = enc.encode_to_binary(token)
        decoded = enc.decode_from_binary(binary)
        match = "ok" if decoded == token else "MISMATCH"
        print(f"  {token:8s} -> {binary:8s} -> {decoded:8s}  [{match}]")
    print()


def demo_tensor_operations():
    """Show tensor properties for several states."""
    print("=" * 60)
    print("GEIS: Tensor Operations")
    print("=" * 60)
    for i in (0, 3, 7):
        t = StateTensor(OctahedralState(i))
        evals = t.eigenvalues()
        print(f"  State {i}: trace={t.trace():.4f}  det={t.determinant():.6f}  "
              f"norm={t.norm():.4f}  eigenvalues={np.round(evals, 4).tolist()}")

    # Combine opposite states
    t0 = StateTensor(OctahedralState(0))
    t7 = StateTensor(OctahedralState(7))
    combined = StateTensor.combine([t0, t7])
    print(f"\n  Combined (0+7): trace={np.trace(combined):.4f}  "
          f"det={np.linalg.det(combined):.6f}")

    # Projection
    proj_x = t0.project([1, 0, 0])
    proj_diag = t0.project([1, 1, 1])
    print(f"\n  State 0 projection along x-axis: {proj_x:.4f}")
    print(f"  State 0 projection along (1,1,1): {proj_diag:.4f}")
    print()


def demo_sensor_simulation():
    """Simulate random 3-D directions -> tokens -> dependency search."""
    print("=" * 60)
    print("GEIS: Sensor Simulation + Dependency Search")
    print("=" * 60)
    np.random.seed(42)
    tokens = []
    for _ in range(80):
        theta = np.random.uniform(0, 2 * math.pi)
        phi_angle = math.acos(2 * np.random.uniform() - 1)
        x = math.sin(phi_angle) * math.cos(theta)
        y = math.sin(phi_angle) * math.sin(theta)
        z = math.cos(phi_angle)
        phase = np.random.uniform(0, 360)
        tokens.append(vector_to_token(np.array([x, y, z]), phase))

    print(f"  Generated {len(tokens)} tokens (first 5): {tokens[:5]}")
    deps = find_dependencies(tokens, max_len=3)
    print(f"  Tensor-cancellation dependencies found: {len(deps)}")
    for dep in deps[:3]:
        T = sum((token_to_tensor(tokens[j]) for j in dep), np.zeros((3, 3)))
        print(f"    indices {dep}  norm={np.linalg.norm(T):.2e}")
    print()


def demo_cube_dependencies():
    """Demonstrate 3-D binary cube XOR dependency finding."""
    print("=" * 60)
    print("GEIS: 3-D Binary Cube Dependencies")
    print("=" * 60)
    np.random.seed(42)
    cubes = []
    for _ in range(5):
        bits = ''.join(str(np.random.randint(0, 2)) for _ in range(27))
        cubes.append(bits_to_cube(bits, side=3))
    # Add an exact duplicate to guarantee a dependency
    cubes.append(cubes[0].copy())

    print(f"  Created {len(cubes)} cubes of shape {cubes[0].shape}")
    deps = find_cube_dependencies(cubes, max_comb=3)
    print(f"  XOR-cancellation dependencies: {len(deps)}")
    for dep in deps[:3]:
        total = np.zeros_like(cubes[0])
        for idx in dep:
            total ^= cubes[idx]
        print(f"    indices {dep}  XOR norm={cube_norm(total)}")
    print()


def demo_mandala_bridge():
    """Show integration with Mandala cell states."""
    print("=" * 60)
    print("GEIS: Mandala Bridge")
    print("=" * 60)
    states = [0, 3, 5, 7, 2, 6, 1, 4]
    tokens = [cell_state_to_token(s) for s in states]
    print(f"  Cell states: {states}")
    print(f"  Tokens:      {tokens}")

    # Round-trip
    recovered = [token_to_cell_state(t) for t in tokens]
    print(f"  Recovered:   {recovered}")
    print(f"  Lossless:    {states == recovered}")

    # Tensor fingerprint
    profile = state_tensor_profile(states)
    print(f"\n  Tensor profile:")
    print(f"    eigenvalues: {[round(e, 4) for e in profile['eigenvalues']]}")
    print(f"    trace: {profile['trace']:.4f}")
    print(f"    norm:  {profile['norm']:.4f}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("GEOMETRIC INFORMATION ENCODING SYSTEM (GEIS) v1.0")
    print("  Bridge between geometric states and binary representation")
    print("=" * 60)
    print()
    demo_basic_states()
    demo_dual_mode_encoding()
    demo_tensor_operations()
    demo_sensor_simulation()
    demo_cube_dependencies()
    demo_mandala_bridge()
    print("=" * 60)
    print("All demonstrations complete.")
    print("Geometry encodes. Tensors reveal. Binary bridges.")
    print("=" * 60)
