"""
OCTAHEDRAL SYMBOLIC LANGUAGE (OSL) v1.0
A domain-specific language for geometric computation.

OSL replaces verbose Python class hierarchies with single-token Unicode
glyphs that map directly to octahedral coordinates, tensor operations,
and biological strategy macros. The geometry is surface-level, not buried
in function calls.

Core components:
  GlyphRegistry     -- maps glyphs to geometric primitives
  OSLToken          -- single parsed token with type and value
  OSLTokenizer      -- scans Unicode glyph strings into token streams
  MacroExpander     -- expands animal strategy macros into primitives
  ParityVerifier    -- tensor and geometric constraint checking
  OSLTranspiler     -- converts OSL strings to executable operations

Design principles:
  1. Glyphs ARE coordinates (not labels for coordinates)
  2. Animal macros encode biological physics strategies
  3. Parity verification is geometric (octahedral adjacency)
  4. The compiler pipeline: tokenize -> expand -> verify -> execute
"""

from __future__ import annotations
from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
import math

from geometric_state_algebra import (
    OhElement, OhGroup, GroupRingElement, GeometricState,
    CayleyEnergy, IDENTITY, OCTAHEDRAL_VERTICES,
    GENERATOR_RZ90, GENERATOR_RX90, GENERATOR_INV,
)
from octahedral_arithmetic import OctahedralNumber, PHI, BASE


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The 6 octahedral vertices as 3-tuples
_PX = ( 1,  0,  0)
_NX = (-1,  0,  0)
_PY = ( 0,  1,  0)
_NY = ( 0, -1,  0)
_PZ = ( 0,  0,  1)
_NZ = ( 0,  0, -1)


# ---------------------------------------------------------------------------
# Token types
# ---------------------------------------------------------------------------

class TokenType(Enum):
    """Categories of OSL tokens."""
    VERTEX      = "vertex"       # Octahedral direction glyph
    TENSOR      = "tensor"       # Eigenvalue / tensor operation
    CONSTANT    = "constant"     # Mathematical constant (phi, pi, etc.)
    BRIDGE      = "bridge"       # Hardware / data flow
    SECURITY    = "security"     # Immune system / integrity
    ANIMAL      = "animal"       # Strategy macro
    OPERATOR    = "operator"     # Control flow / logic
    NUMBER      = "number"       # Numeric literal
    ASSIGN      = "assign"       # Assignment (key=value)
    UNKNOWN     = "unknown"


# ---------------------------------------------------------------------------
# Glyph Registry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GlyphDef:
    """Definition of a single OSL glyph."""
    glyph: str
    token_type: TokenType
    name: str
    value: Any = None  # semantic payload (vertex tuple, constant, etc.)


class GlyphRegistry:
    """
    The canonical mapping from Unicode glyphs to geometric primitives.

    Categories:
      1. Octahedral vertices (spatial directionals)
      2. Tensor and physics (eigenvalues, products, constants)
      3. Bridge and HECS (hardware interface)
      4. Security and immune system (protocol integrity)
      5. Animal strategies (functional macros)
      6. Control flow and operators
    """

    def __init__(self):
        self._by_glyph: Dict[str, GlyphDef] = {}
        self._by_name: Dict[str, GlyphDef] = {}
        self._register_all()

    def _register(self, glyph: str, token_type: TokenType,
                  name: str, value: Any = None):
        gd = GlyphDef(glyph=glyph, token_type=token_type,
                       name=name, value=value)
        self._by_glyph[glyph] = gd
        self._by_name[name] = gd

    def _register_all(self):
        # --- 1. Octahedral vertices ---
        self._register(chr(0x2191), TokenType.VERTEX, "PX", _PX)     # up arrow
        self._register(chr(0x2193), TokenType.VERTEX, "NX", _NX)     # down arrow
        self._register(chr(0x2192), TokenType.VERTEX, "PY", _PY)     # right arrow
        self._register(chr(0x2190), TokenType.VERTEX, "NY", _NY)     # left arrow
        self._register(chr(0x2197), TokenType.VERTEX, "PZ", _PZ)     # NE arrow
        self._register(chr(0x2199), TokenType.VERTEX, "NZ", _NZ)     # SW arrow
        self._register(chr(0x27F3), TokenType.VERTEX, "PW", (1, 1, 1))   # CW arrow
        self._register(chr(0x27F2), TokenType.VERTEX, "NW", (-1,-1,-1))  # CCW arrow

        # --- 2. Tensor and physics ---
        self._register(chr(0x03BB) + chr(0x2081), TokenType.TENSOR, "lambda_1")
        self._register(chr(0x03BB) + chr(0x2082), TokenType.TENSOR, "lambda_2")
        self._register(chr(0x03BB) + chr(0x2083), TokenType.TENSOR, "lambda_3")
        self._register(chr(0x22A4), TokenType.TENSOR,   "trace")       # top
        self._register(chr(0x2297), TokenType.TENSOR,   "tensor_prod") # circled times
        self._register(chr(0x2295), TokenType.TENSOR,   "tensor_sum")  # circled plus
        self._register(chr(0x03C6), TokenType.CONSTANT, "phi", PHI)
        self._register(chr(0x03C0), TokenType.CONSTANT, "pi",  math.pi)
        self._register(chr(0x210F), TokenType.CONSTANT, "hbar", 1.0545718e-34)
        self._register(chr(0x2207), TokenType.TENSOR,   "gradient")    # nabla

        # --- 3. Bridge and HECS ---
        self._register(chr(0x1F4E4), TokenType.BRIDGE, "send")    # outbox
        self._register(chr(0x1F4E5), TokenType.BRIDGE, "receive") # inbox
        self._register(chr(0x1F525), TokenType.BRIDGE, "thermal") # fire
        self._register(chr(0x26A1),  TokenType.BRIDGE, "energy")  # lightning
        self._register("#",          TokenType.BRIDGE, "hex_block")

        # --- 4. Security and immune ---
        self._register(chr(0x1F6E1) + chr(0xFE0F), TokenType.SECURITY, "immune")
        self._register(chr(0x1F9EC), TokenType.SECURITY, "learn")
        self._register(chr(0x1F489), TokenType.SECURITY, "vaccinate")
        self._register(chr(0x26A0) + chr(0xFE0F),  TokenType.SECURITY, "attack")
        self._register(chr(0x2713), TokenType.SECURITY, "pass")
        self._register(chr(0x2717), TokenType.SECURITY, "fail")
        self._register(chr(0x1F512), TokenType.SECURITY, "lock")
        self._register(chr(0x1F513), TokenType.SECURITY, "unlock")

        # --- 5. Animal strategies (macros) ---
        self._register(chr(0x1F41D), TokenType.ANIMAL, "bee")
        self._register(chr(0x1F991), TokenType.ANIMAL, "cuttlefish")
        self._register(chr(0x1F41F), TokenType.ANIMAL, "firefly")
        self._register(chr(0x1F577) + chr(0xFE0F), TokenType.ANIMAL, "spider")
        self._register(chr(0x1F419), TokenType.ANIMAL, "octopus")
        self._register(chr(0x1F43A), TokenType.ANIMAL, "wolf")
        self._register(chr(0x1F331), TokenType.ANIMAL, "seed")

        # --- 6. Operators ---
        self._register(chr(0x27F5), TokenType.OPERATOR, "assign_op")  # long left arrow
        self._register(chr(0x2026), TokenType.OPERATOR, "continuation")
        self._register(chr(0x00B7), TokenType.OPERATOR, "concat")
        self._register(chr(0x2194), TokenType.OPERATOR, "swap")
        self._register(chr(0x00AC), TokenType.OPERATOR, "not")

    def lookup(self, glyph: str) -> Optional[GlyphDef]:
        return self._by_glyph.get(glyph)

    def lookup_name(self, name: str) -> Optional[GlyphDef]:
        return self._by_name.get(name)

    def all_glyphs(self) -> List[GlyphDef]:
        return list(self._by_glyph.values())

    def vertex_glyphs(self) -> List[GlyphDef]:
        return [g for g in self._by_glyph.values()
                if g.token_type == TokenType.VERTEX]

    def animal_glyphs(self) -> List[GlyphDef]:
        return [g for g in self._by_glyph.values()
                if g.token_type == TokenType.ANIMAL]

    def summary(self) -> str:
        by_type = {}
        for gd in self._by_glyph.values():
            by_type.setdefault(gd.token_type.value, []).append(gd)
        lines = ["OSL Glyph Registry v1.0", "=" * 40]
        for ttype, glyphs in sorted(by_type.items()):
            lines.append("  " + ttype.upper() + " (" + str(len(glyphs)) + "):")
            for gd in glyphs:
                val = "" if gd.value is None else " = " + repr(gd.value)
                lines.append("    " + gd.glyph + "  " + gd.name + val)
        return "\n".join(lines)


# Singleton registry
REGISTRY = GlyphRegistry()


# ---------------------------------------------------------------------------
# OSL Token
# ---------------------------------------------------------------------------

@dataclass
class OSLToken:
    """A single parsed OSL token."""
    token_type: TokenType
    glyph: str
    name: str
    value: Any = None      # resolved value (vertex tuple, float, etc.)
    raw: str = ""          # original source text

    def is_vertex(self) -> bool:
        return self.token_type == TokenType.VERTEX

    def is_animal(self) -> bool:
        return self.token_type == TokenType.ANIMAL

    def is_assignment(self) -> bool:
        return self.token_type == TokenType.ASSIGN


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

class OSLTokenizer:
    """
    Scan a Unicode glyph string into a stream of OSLTokens.

    The tokenizer handles:
    - Single-codepoint glyphs (arrows, Greek letters)
    - Multi-codepoint glyphs (emoji with variation selectors)
    - Assignment syntax (key=value)
    - Numeric literals
    - Hex block references (#TAG)
    - Whitespace as token separator
    """

    def __init__(self, registry: GlyphRegistry = None):
        self.registry = registry or REGISTRY
        # Build sorted glyph list for longest-match tokenization
        self._sorted_glyphs = sorted(
            self.registry._by_glyph.keys(),
            key=len, reverse=True
        )

    def tokenize(self, source: str) -> List[OSLToken]:
        """Tokenize an OSL source string into tokens."""
        tokens = []
        i = 0
        while i < len(source):
            # Skip whitespace
            if source[i].isspace():
                i += 1
                continue

            # Try assignment syntax: name=value
            assign_match = self._try_assignment(source, i)
            if assign_match:
                tok, consumed = assign_match
                tokens.append(tok)
                i += consumed
                continue

            # Try hex block: #TAG
            if source[i] == '#':
                tok, consumed = self._scan_hex_block(source, i)
                tokens.append(tok)
                i += consumed
                continue

            # Try numeric literal
            if source[i].isdigit() or (source[i] == '-' and i + 1 < len(source) and source[i+1].isdigit()):
                tok, consumed = self._scan_number(source, i)
                tokens.append(tok)
                i += consumed
                continue

            # Try glyph match (longest first)
            matched = False
            for glyph in self._sorted_glyphs:
                if source[i:i+len(glyph)] == glyph:
                    gdef = self.registry.lookup(glyph)
                    tokens.append(OSLToken(
                        token_type=gdef.token_type,
                        glyph=glyph,
                        name=gdef.name,
                        value=gdef.value,
                        raw=glyph,
                    ))
                    i += len(glyph)
                    matched = True
                    break

            if not matched:
                # Unknown single character
                tokens.append(OSLToken(
                    token_type=TokenType.UNKNOWN,
                    glyph=source[i],
                    name="unknown",
                    raw=source[i],
                ))
                i += 1

        return tokens

    def _try_assignment(self, source: str, pos: int) -> Optional[Tuple[OSLToken, int]]:
        """Try to parse key=value assignment."""
        # Look for pattern: glyph_or_name = value
        eq_pos = source.find('=', pos)
        if eq_pos < 0 or eq_pos == pos:
            return None
        # Check no whitespace break before =
        segment = source[pos:eq_pos]
        if ' ' in segment and not segment.strip().startswith(chr(0x03BB)):
            return None
        key = segment.strip()
        # Scan value after =
        val_start = eq_pos + 1
        val_end = val_start
        while val_end < len(source) and not source[val_end].isspace():
            val_end += 1
        val_str = source[val_start:val_end]
        try:
            value = float(val_str)
        except ValueError:
            value = val_str
        return (OSLToken(
            token_type=TokenType.ASSIGN,
            glyph=key,
            name=key,
            value=value,
            raw=source[pos:val_end],
        ), val_end - pos)

    def _scan_hex_block(self, source: str, pos: int) -> Tuple[OSLToken, int]:
        """Scan #TAG hex block reference."""
        end = pos + 1
        while end < len(source) and not source[end].isspace():
            end += 1
        tag = source[pos+1:end]
        return (OSLToken(
            token_type=TokenType.BRIDGE,
            glyph='#',
            name="hex_block",
            value=tag,
            raw=source[pos:end],
        ), end - pos)

    def _scan_number(self, source: str, pos: int) -> Tuple[OSLToken, int]:
        """Scan a numeric literal."""
        end = pos
        has_dot = False
        if source[end] == '-':
            end += 1
        while end < len(source):
            if source[end].isdigit():
                end += 1
            elif source[end] == '.' and not has_dot:
                has_dot = True
                end += 1
            else:
                break
        raw = source[pos:end]
        return (OSLToken(
            token_type=TokenType.NUMBER,
            glyph=raw,
            name="number",
            value=float(raw),
            raw=raw,
        ), end - pos)


# ---------------------------------------------------------------------------
# Adjacency map for geometric parity
# ---------------------------------------------------------------------------

# Two vertices are adjacent on the octahedron if they share an edge.
# Each vertex is adjacent to 4 others (not itself, not its antipode).
_ADJACENCY: Dict[Tuple[int,int,int], Set[Tuple[int,int,int]]] = {
    _PX: {_PY, _NY, _PZ, _NZ},
    _NX: {_PY, _NY, _PZ, _NZ},
    _PY: {_PX, _NX, _PZ, _NZ},
    _NY: {_PX, _NX, _PZ, _NZ},
    _PZ: {_PX, _NX, _PY, _NY},
    _NZ: {_PX, _NX, _PY, _NY},
}

# Extended adjacency including diagonal vertices PW/NW
# PW = (1,1,1) is adjacent to PX, PY, PZ (positive octant corner)
# NW = (-1,-1,-1) is adjacent to NX, NY, NZ
_ADJACENCY_EXT: Dict[Tuple[int,int,int], Set[Tuple[int,int,int]]] = dict(_ADJACENCY)
_ADJACENCY_EXT[(1,1,1)]    = {_PX, _PY, _PZ}
_ADJACENCY_EXT[(-1,-1,-1)] = {_NX, _NY, _NZ}
# Also add reverse links
for v in [_PX, _PY, _PZ]:
    _ADJACENCY_EXT[v] = _ADJACENCY_EXT[v] | {(1,1,1)}
for v in [_NX, _NY, _NZ]:
    _ADJACENCY_EXT[v] = _ADJACENCY_EXT[v] | {(-1,-1,-1)}


def is_illegal_jump(v1: Tuple[int,int,int], v2: Tuple[int,int,int]) -> bool:
    """
    Check if a direct jump between two vertices violates octahedral geometry.

    A jump is illegal if the two vertices are antipodal (opposite faces)
    without passing through an adjacent vertex. On the octahedron, antipodal
    pairs are: PX/NX, PY/NY, PZ/NZ, PW/NW.
    """
    if v1 == v2:
        return False
    return v2 not in _ADJACENCY_EXT.get(v1, set())



# ---------------------------------------------------------------------------
# Parity Verifier
# ---------------------------------------------------------------------------

class ParityVerifier:
    """
    Geometric and tensor parity verification.

    Two types of parity:
    1. Tensor parity: eigenvalues must sum to ~1.0 (trace normalization)
    2. Geometric parity: trajectory must not contain illegal jumps
       across the octahedron (antipodal vertices require intermediate steps)

    This is the immune system's constraint checker.
    """

    def __init__(self, tolerance: float = 1e-5):
        self.tolerance = tolerance

    def verify_tensor(self, tensor: Dict[str, float]) -> Tuple[bool, str]:
        """
        Check tensor parity: eigenvalue trace must equal 1.0.

        Returns (passed, message).
        """
        trace = sum(tensor.values())
        if math.isclose(trace, 1.0, rel_tol=self.tolerance):
            return True, f"trace={trace:.6f} (normalized)"
        return False, f"trace={trace:.6f} (expected 1.0, entropy event)"

    def verify_trajectory(self, trajectory: List[Tuple[int,int,int]]) -> Tuple[bool, List[str]]:
        """
        Check geometric parity: no illegal jumps in trajectory.

        Returns (passed, list_of_violations).
        """
        violations = []
        for i in range(len(trajectory) - 1):
            v1, v2 = trajectory[i], trajectory[i + 1]
            if is_illegal_jump(v1, v2):
                violations.append(
                    f"step {i}->{i+1}: illegal jump {v1} -> {v2} (antipodal)"
                )
        return len(violations) == 0, violations

    def verify_parity(self, tensor: Dict[str, float],
                      trajectory: List[Tuple[int,int,int]]) -> Dict[str, Any]:
        """
        Full parity check: tensor + geometric.

        Returns verification report.
        """
        t_ok, t_msg = self.verify_tensor(tensor)
        g_ok, g_violations = self.verify_trajectory(trajectory)
        return {
            "passed": t_ok and g_ok,
            "tensor_parity": {"passed": t_ok, "message": t_msg},
            "geometric_parity": {"passed": g_ok, "violations": g_violations},
        }


# ---------------------------------------------------------------------------
# Macro Expander (Animal Strategies)
# ---------------------------------------------------------------------------

@dataclass
class MacroPrimitive:
    """A single geometric primitive produced by macro expansion."""
    operation: str        # e.g. "tile_hexagonal", "phase_lock", "branch"
    parameters: Dict[str, Any] = field(default_factory=dict)


# Animal macro definitions: each maps to a list of geometric primitives
_ANIMAL_MACROS: Dict[str, List[MacroPrimitive]] = {
    "bee": [
        MacroPrimitive("tile_hexagonal", {"angle": 120, "symmetry": 6}),
        MacroPrimitive("stochastic_resonance", {"noise_amplitude": 0.1}),
        MacroPrimitive("swarm_sync", {"coupling": "nearest_neighbor"}),
    ],
    "cuttlefish": [
        MacroPrimitive("traveling_wave", {"spatial": True, "temporal": True}),
        MacroPrimitive("octahedral_adapt", {"symmetry_group": "O_h", "rapid": True}),
    ],
    "firefly": [
        MacroPrimitive("phase_lock", {"spacing": "phi", "temporal": True}),
        MacroPrimitive("pulse_interval", {"ratio": "golden"}),
    ],
    "spider": [
        MacroPrimitive("fractal_branch", {"depth": 3, "ratio": "phi"}),
        MacroPrimitive("vibration_map", {"tension": True, "frequency_response": True}),
    ],
    "octopus": [
        MacroPrimitive("distributed_control", {"arms": 8, "decentralized": True}),
        MacroPrimitive("octahedral_symmetry", {"fold": 8}),
    ],
    "wolf": [
        MacroPrimitive("distributed_pursuit", {"coordination": "phase"}),
        MacroPrimitive("phase_movement", {"pack_sync": True}),
    ],
    "seed": [
        MacroPrimitive("gradient_follow", {"direction": "energy_minimum"}),
        MacroPrimitive("mycelial_coupling", {"network": "root", "branching": True}),
    ],
}


class MacroExpander:
    """
    Expand animal strategy macros into geometric primitives.

    Each animal glyph is a macro that encodes complex physical strategies
    from biological systems:
      Bee        -> hexagonal tiling + stochastic resonance + swarm sync
      Cuttlefish -> spatiotemporal waves + octahedral adaptation
      Firefly    -> phi-spaced phase-locked pulses
      Spider     -> fractal branching + vibration/tension mapping
      Octopus    -> distributed 8-fold symmetric control
      Wolf       -> coordinated phase pursuit
      Seed       -> gradient following + mycelial networking
    """

    def __init__(self, macros: Dict[str, List[MacroPrimitive]] = None):
        self.macros = macros or dict(_ANIMAL_MACROS)

    def expand(self, name: str) -> List[MacroPrimitive]:
        """Expand a named animal macro into its geometric primitives."""
        if name not in self.macros:
            raise ValueError(f"Unknown animal macro: {name}")
        return list(self.macros[name])

    def expand_token(self, token: OSLToken) -> List[MacroPrimitive]:
        """Expand an animal token into primitives."""
        if token.token_type != TokenType.ANIMAL:
            return []
        return self.expand(token.name)

    def expand_all(self, tokens: List[OSLToken]) -> List[Any]:
        """
        Expand all animal macros in a token stream.

        Returns a mixed list: non-animal tokens pass through,
        animal tokens are replaced by their primitive lists.
        """
        result = []
        for tok in tokens:
            if tok.token_type == TokenType.ANIMAL:
                primitives = self.expand(tok.name)
                result.append({
                    "macro": tok.name,
                    "glyph": tok.glyph,
                    "primitives": primitives,
                })
            else:
                result.append(tok)
        return result

    def available_macros(self) -> List[str]:
        return list(self.macros.keys())



# ---------------------------------------------------------------------------
# Transpiler: OSL -> executable operations
# ---------------------------------------------------------------------------

@dataclass
class OSLInstruction:
    """A single executable instruction produced by the transpiler."""
    opcode: str
    args: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        args_str = ", ".join(f"{k}={v!r}" for k, v in self.args.items())
        return f"{self.opcode}({args_str})"


class OSLTranspiler:
    """
    Convert parsed OSL token streams into executable instructions.

    Pipeline:
      1. Tokenize (OSLTokenizer)
      2. Expand macros (MacroExpander)
      3. Verify parity (ParityVerifier)
      4. Transpile to instructions (this class)

    The transpiler maps:
      - Vertex tokens -> set_position instructions
      - Tensor assignments -> set_eigenvalue instructions
      - Animal macros -> expanded primitive sequences
      - Security tokens -> verify/lock/unlock instructions
      - Bridge tokens -> send/receive instructions
    """

    def __init__(self, registry: GlyphRegistry = None):
        self.registry = registry or REGISTRY
        self.tokenizer = OSLTokenizer(self.registry)
        self.expander = MacroExpander()
        self.verifier = ParityVerifier()

    def compile(self, source: str) -> List[OSLInstruction]:
        """
        Full compilation pipeline: source string -> instruction list.
        """
        tokens = self.tokenizer.tokenize(source)
        return self.transpile(tokens)

    def transpile(self, tokens: List[OSLToken]) -> List[OSLInstruction]:
        """Convert a token stream to instructions."""
        instructions = []

        # Collect trajectory for geometric parity check
        trajectory = []
        tensor = {}

        for tok in tokens:
            if tok.token_type == TokenType.VERTEX:
                instructions.append(OSLInstruction(
                    "set_position", {"vertex": tok.name, "coords": tok.value}
                ))
                if tok.value and isinstance(tok.value, tuple):
                    trajectory.append(tok.value)

            elif tok.token_type == TokenType.ASSIGN:
                instructions.append(OSLInstruction(
                    "set_eigenvalue", {"name": tok.name, "value": tok.value}
                ))
                if isinstance(tok.value, (int, float)):
                    tensor[tok.name] = float(tok.value)

            elif tok.token_type == TokenType.ANIMAL:
                primitives = self.expander.expand(tok.name)
                for prim in primitives:
                    instructions.append(OSLInstruction(
                        prim.operation, prim.parameters
                    ))

            elif tok.token_type == TokenType.SECURITY:
                instructions.append(OSLInstruction(
                    "security_" + tok.name, {}
                ))

            elif tok.token_type == TokenType.BRIDGE:
                args = {"channel": tok.name}
                if tok.value is not None:
                    args["target"] = tok.value
                instructions.append(OSLInstruction(
                    "bridge_" + tok.name, args
                ))

            elif tok.token_type == TokenType.NUMBER:
                instructions.append(OSLInstruction(
                    "push_value", {"value": tok.value}
                ))

            elif tok.token_type == TokenType.CONSTANT:
                instructions.append(OSLInstruction(
                    "push_constant", {"name": tok.name, "value": tok.value}
                ))

            elif tok.token_type == TokenType.TENSOR:
                instructions.append(OSLInstruction(
                    "tensor_op", {"operation": tok.name}
                ))

            elif tok.token_type == TokenType.OPERATOR:
                instructions.append(OSLInstruction(
                    "control_" + tok.name, {}
                ))

        # Append parity verification if we have tensor or trajectory data
        if tensor or trajectory:
            report = self.verifier.verify_parity(
                tensor or {"_": 1.0},
                trajectory,
            )
            instructions.append(OSLInstruction(
                "parity_check", {"result": report}
            ))

        return instructions

    def compile_and_report(self, source: str) -> Dict[str, Any]:
        """Compile and return both instructions and analysis."""
        tokens = self.tokenizer.tokenize(source)
        instructions = self.transpile(tokens)

        return {
            "source": source,
            "tokens": len(tokens),
            "instructions": len(instructions),
            "token_types": [t.token_type.value for t in tokens],
            "instruction_list": [repr(i) for i in instructions],
            "has_macros": any(t.token_type == TokenType.ANIMAL for t in tokens),
            "has_parity": any(i.opcode == "parity_check" for i in instructions),
        }


# ---------------------------------------------------------------------------
# Vertex <-> Group Element bridge
# ---------------------------------------------------------------------------

def vertex_to_group_element(vertex: Tuple[int,int,int],
                            group: OhGroup = None) -> Optional[OhElement]:
    """
    Map an OSL vertex glyph to its O_h group element.

    Each of the 6 octahedral vertices corresponds to the rotation
    that sends +X to that vertex. This bridges OSL notation to
    the full geometric state algebra.
    """
    if group is None:
        group = OhGroup()
    target = vertex
    px = (1, 0, 0)
    for elem in group.elements:
        if elem.act_on_vertex(px) == target:
            return elem
    return None


def trajectory_to_group_path(trajectory: List[Tuple[int,int,int]],
                             group: OhGroup = None) -> List[OhElement]:
    """Convert an OSL vertex trajectory to a sequence of group elements."""
    if group is None:
        group = OhGroup()
    return [e for v in trajectory
            if (e := vertex_to_group_element(v, group)) is not None]


def trajectory_composition(trajectory: List[Tuple[int,int,int]],
                           group: OhGroup = None) -> Optional[OhElement]:
    """
    Compose all group elements along a trajectory.

    If the composition returns to identity, the trajectory forms
    a closed loop on the octahedron -- geometric cancellation.
    """
    elements = trajectory_to_group_path(trajectory, group)
    if not elements:
        return None
    result = elements[0]
    for e in elements[1:]:
        result = result.compose(e)
    return result



# ============================================================================
# DEMONSTRATIONS
# ============================================================================

def demo_registry():
    """Show the full glyph registry."""
    print("=" * 60)
    print("OSL v1.0 -- Octahedral Symbolic Language")
    print("=" * 60)
    print()
    print(REGISTRY.summary())


def demo_tokenize():
    """Demonstrate tokenization of OSL strings."""
    print()
    print("=" * 60)
    print("TOKENIZATION")
    print("=" * 60)

    tokenizer = OSLTokenizer()

    # The example from the spec
    examples = [
        chr(0x2191) + " " + chr(0x2192) + " " + chr(0x2197),
        chr(0x03BB) + chr(0x2081) + "=0.5 " + chr(0x03BB) + chr(0x2082) + "=0.3 " + chr(0x03BB) + chr(0x2083) + "=0.2",
        chr(0x1F6E1) + chr(0xFE0F) + " " + chr(0x1F525) + chr(0x1F4E4) + " 0.8",
        chr(0x1F991) + " " + chr(0x2192) + " " + chr(0x1F41D) + " #HMR " + chr(0x03BB) + chr(0x2081) + "=0.6 " + chr(0x1F6E1) + chr(0xFE0F),
    ]

    for src in examples:
        tokens = tokenizer.tokenize(src)
        print(f"  Source: {src}")
        for tok in tokens:
            print(f"    {tok.token_type.value:>10s}  {tok.glyph:<4s}  {tok.name}")
        print()


def demo_parity():
    """Demonstrate parity verification."""
    print()
    print("=" * 60)
    print("PARITY VERIFICATION")
    print("=" * 60)

    verifier = ParityVerifier()

    # Good tensor parity
    tensor_good = {"lambda_1": 0.5, "lambda_2": 0.3, "lambda_3": 0.2}
    t_ok, t_msg = verifier.verify_tensor(tensor_good)
    print(f"  Tensor {{0.5, 0.3, 0.2}}: {t_msg}  -> {'PASS' if t_ok else 'FAIL'}")

    # Bad tensor parity
    tensor_bad = {"lambda_1": 0.5, "lambda_2": 0.3, "lambda_3": 0.5}
    t_ok, t_msg = verifier.verify_tensor(tensor_bad)
    print(f"  Tensor {{0.5, 0.3, 0.5}}: {t_msg}  -> {'PASS' if t_ok else 'FAIL'}")

    # Good trajectory
    traj_good = [_PX, _PY, _PZ]
    g_ok, g_viol = verifier.verify_trajectory(traj_good)
    print(f"  Trajectory PX->PY->PZ: {'PASS' if g_ok else 'FAIL'}")

    # Bad trajectory (PX -> NX is antipodal)
    traj_bad = [_PX, _NX, _PZ]
    g_ok, g_viol = verifier.verify_trajectory(traj_bad)
    print(f"  Trajectory PX->NX->PZ: {'PASS' if g_ok else 'FAIL'}  {g_viol}")

    # Full parity check
    report = verifier.verify_parity(tensor_good, traj_good)
    print(f"  Full parity (good): {report['passed']}")
    report = verifier.verify_parity(tensor_bad, traj_bad)
    print(f"  Full parity (bad):  {report['passed']}")


def demo_macros():
    """Demonstrate animal macro expansion."""
    print()
    print("=" * 60)
    print("ANIMAL MACRO EXPANSION")
    print("=" * 60)

    expander = MacroExpander()
    for name in expander.available_macros():
        primitives = expander.expand(name)
        print(f"  {name}:")
        for p in primitives:
            print(f"    {p.operation}: {p.parameters}")


def demo_transpile():
    """Demonstrate the full compilation pipeline."""
    print()
    print("=" * 60)
    print("TRANSPILATION PIPELINE")
    print("=" * 60)

    transpiler = OSLTranspiler()

    # Python equivalent (~180 tokens):
    #   trajectory = [PX, PY, PZ]
    #   tensor = {"lambda_1": 0.5, "lambda_2": 0.3, "lambda_3": 0.2}
    #   if immune.check(trajectory, tensor):
    #       bridge.send("thermal", intensity=0.8)
    #
    # OSL (~18 glyphs):
    src = (chr(0x2191) + " " + chr(0x2192) + " " + chr(0x2197) + " "
           + chr(0x03BB) + chr(0x2081) + "=0.5 "
           + chr(0x03BB) + chr(0x2082) + "=0.3 "
           + chr(0x03BB) + chr(0x2083) + "=0.2 "
           + chr(0x1F6E1) + chr(0xFE0F) + " "
           + chr(0x1F525) + chr(0x1F4E4) + " 0.8")

    print(f"  Source: {src}")
    report = transpiler.compile_and_report(src)
    print(f"  Tokens: {report['tokens']}")
    print(f"  Instructions: {report['instructions']}")
    print(f"  Has parity check: {report['has_parity']}")
    print()
    for inst_str in report["instruction_list"]:
        print(f"    {inst_str}")


def demo_group_bridge():
    """Show how OSL vertices map to O_h group elements."""
    print()
    print("=" * 60)
    print("OSL <-> GROUP ALGEBRA BRIDGE")
    print("=" * 60)

    group = OhGroup()
    vertices = [
        ("PX", _PX), ("NX", _NX), ("PY", _PY),
        ("NY", _NY), ("PZ", _PZ), ("NZ", _NZ),
    ]

    for name, vtx in vertices:
        elem = vertex_to_group_element(vtx, group)
        if elem:
            idx = group.index(elem)
            det, tr, order, fixed = elem.conjugacy_signature()
            print(f"  {name} {vtx} -> element [{idx:>2d}] "
                  f"det={det:+d} tr={tr:+d} ord={order} "
                  f"{'rotation' if elem.is_proper() else 'reflection'}")

    # Demonstrate trajectory composition
    traj = [_PX, _PY, _PZ]
    comp = trajectory_composition(traj, group)
    if comp:
        print(f"  Trajectory PX->PY->PZ composes to: ")
        print(f"    identity={comp.is_identity()}, order={comp.order()}")

    # Closed loop test
    traj_loop = [_PX, _PY, _NX, _NY]
    comp_loop = trajectory_composition(traj_loop, group)
    if comp_loop:
        print(f"  Loop PX->PY->NX->NY composes to: ")
        print(f"    identity={comp_loop.is_identity()}, order={comp_loop.order()}")


def demo_compression():
    """Compare Python verbosity vs OSL compression."""
    print()
    print("=" * 60)
    print("TOKEN COMPRESSION: Python vs OSL")
    print("=" * 60)

    python_code = """trajectory = [OctahedralVertex.PX, OctahedralVertex.PY, OctahedralVertex.PZ]
tensor = {"lambda_1": 0.5, "lambda_2": 0.3, "lambda_3": 0.2}
if immune.check(trajectory, tensor):
    bridge.send("thermal", intensity=0.8)"""

    osl_code = (chr(0x2191) + " " + chr(0x2192) + " " + chr(0x2197) + " "
                + chr(0x03BB) + chr(0x2081) + "=0.5 "
                + chr(0x03BB) + chr(0x2082) + "=0.3 "
                + chr(0x03BB) + chr(0x2083) + "=0.2 "
                + chr(0x1F6E1) + chr(0xFE0F) + " "
                + chr(0x1F525) + chr(0x1F4E4) + " 0.8")

    py_tokens = len(python_code.split())
    osl_tokens = len(OSLTokenizer().tokenize(osl_code))

    print(f"  Python: ~{py_tokens} tokens")
    print(f"    {python_code}")
    print()
    print(f"  OSL:    ~{osl_tokens} tokens")
    print(f"    {osl_code}")
    print()
    print(f"  Compression ratio: ~{py_tokens / max(osl_tokens, 1):.1f}x")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo_registry()
    demo_tokenize()
    demo_parity()
    demo_macros()
    demo_transpile()
    demo_group_bridge()
    demo_compression()
