"""
CLAIM SCHEMA v1.0
Canonical compressed form for AI readers.

Every claim in this repo is a differential equation under scope,
not a noun-identity. This module provides:

  Layer 1 — CLAIM_SCHEMA dict (JSON-compatible, human + AI readable)
  Layer 2 — Pipe-delimited line format (.claims file, ~80 tokens/claim)
  Layer 3 — Binary codec (~32 bytes/claim, 120x cheaper than prose)
  Layer 4 — CLAIM_TABLE.json shared lookup (token cost paid once)

AI reader protocol:
  1. Load CLAIM_TABLE.json (one-time, ~2-5KB)
  2. Read .claims (line-per-claim) or .claims.bin (binary)
  3. Each claim deserializes into CLAIM_SCHEMA dict
  4. Operate on dX/dt + bounds + conditions
  5. Never collapse to noun-identity

CC0. Token-minimal. Binary-serializable. Physics-anchored.
"""

from __future__ import annotations

import hashlib
import json
import struct
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ================================================================
# Layer 1 — JSON Schema
# ================================================================

CYCLE_ENUM = {
    0: "instantaneous",
    1: "diurnal",
    2: "seasonal",
    3: "annual",
    4: "generational",
    5: "century",
    6: "geologic",
}

CYCLE_REVERSE = {v: k for k, v in CYCLE_ENUM.items()}


@dataclass
class Claim:
    """
    A single claim in canonical differential form.

    Every claim is dX/dt under scope — a rate of change, not a noun.
    """
    id: str
    rate: str
    bounds: list
    cond: list
    rel: list
    fail: list
    meas: list
    cyc: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "rate": self.rate, "bounds": self.bounds,
            "cond": self.cond, "rel": self.rel, "fail": self.fail,
            "meas": self.meas, "cyc": self.cyc,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Claim:
        return cls(
            id=d["id"], rate=d["rate"], bounds=d.get("bounds", []),
            cond=d.get("cond", []), rel=d.get("rel", []),
            fail=d.get("fail", []), meas=d.get("meas", []),
            cyc=d.get("cyc", 0),
        )

    def cycle_name(self) -> str:
        return CYCLE_ENUM.get(self.cyc, "unknown")


# ================================================================
# Layer 2 — Pipe-delimited line format
# ================================================================

def claim_to_line(claim: Claim) -> str:
    """Serialize claim to single pipe-delimited line (~80 tokens)."""
    return "|".join([
        claim.id,
        claim.rate,
        ",".join(str(b) for b in claim.bounds),
        ",".join(claim.cond),
        ",".join(claim.rel),
        ",".join(claim.fail),
        ",".join(claim.meas),
        str(claim.cyc),
    ])


def line_to_claim(line: str) -> Claim:
    """Parse a pipe-delimited line back to a Claim."""
    parts = line.strip().split("|")
    if len(parts) < 8:
        parts.extend([""] * (8 - len(parts)))
    return Claim(
        id=parts[0],
        rate=parts[1],
        bounds=[b for b in parts[2].split(",") if b],
        cond=[c for c in parts[3].split(",") if c],
        rel=[r for r in parts[4].split(",") if r],
        fail=[f for f in parts[5].split(",") if f],
        meas=[m for m in parts[6].split(",") if m],
        cyc=int(parts[7]) if parts[7].strip() else 0,
    )


def write_claims_file(claims: List[Claim], path: str) -> None:
    """Write claims to a .claims file (one line per claim)."""
    with open(path, "w") as f:
        for c in claims:
            f.write(claim_to_line(c) + "\n")


def read_claims_file(path: str) -> List[Claim]:
    """Read claims from a .claims file."""
    p = pathlib.Path(path)
    if not p.exists():
        return []
    claims = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            claims.append(line_to_claim(line))
    return claims


# ================================================================
# Layer 3 — Binary codec
# ================================================================

def _short_hash(s: str) -> int:
    """4-byte hash for compact ID storage."""
    return int(hashlib.blake2b(s.encode(), digest_size=4).hexdigest(), 16)


def _index_or_add(table: dict, key: str, value: str) -> int:
    """Get index of value in table[key], adding if not present."""
    lst = table.setdefault(key, [])
    if value in lst:
        return lst.index(value)
    lst.append(value)
    return len(lst) - 1


def _mask(indices: List[int]) -> int:
    """Pack up to 32 indices into a 32-bit bitmask."""
    m = 0
    for i in indices[:32]:
        m |= (1 << i)
    return m & 0xFFFFFFFF


def unmask(m: int) -> List[int]:
    """Unpack a 32-bit bitmask to list of set bit positions."""
    return [i for i in range(32) if m & (1 << i)]


def pack_claim(claim: Claim, table: dict) -> bytes:
    """
    Pack claim into ~25 bytes using shared lookup table.

    Layout: [4B id_hash][2B rate_idx][2B bounds_idx]
            [4B cond_mask][4B rel_mask][4B fail_mask]
            [4B meas_mask][1B cyc]
    """
    id_hash = _short_hash(claim.id)
    rate_idx = _index_or_add(table, "rates", claim.rate)
    bounds_str = ",".join(str(b) for b in claim.bounds)
    bounds_idx = _index_or_add(table, "bounds", bounds_str)
    cond_indices = [_index_or_add(table, "cond", c) for c in claim.cond]
    rel_indices = [_index_or_add(table, "rel", r) for r in claim.rel]
    fail_indices = [_index_or_add(table, "fail", f) for f in claim.fail]
    meas_indices = [_index_or_add(table, "meas", m) for m in claim.meas]

    return struct.pack(
        ">IHHIIIIB",
        id_hash, rate_idx, bounds_idx,
        _mask(cond_indices), _mask(rel_indices),
        _mask(fail_indices), _mask(meas_indices),
        min(claim.cyc, 255),
    )


def unpack_claim(blob: bytes, table: dict) -> dict:
    """Unpack binary claim using shared lookup table."""
    fields = struct.unpack(">IHHIIIIB", blob)
    return {
        "id_hash": fields[0],
        "rate": table.get("rates", ["?"])[min(fields[1], len(table.get("rates", [])) - 1)],
        "bounds": table.get("bounds", [""])[min(fields[2], len(table.get("bounds", [])) - 1)],
        "cond": [table["cond"][i] for i in unmask(fields[3]) if i < len(table.get("cond", []))],
        "rel": [table["rel"][i] for i in unmask(fields[4]) if i < len(table.get("rel", []))],
        "fail": [table["fail"][i] for i in unmask(fields[5]) if i < len(table.get("fail", []))],
        "meas": [table["meas"][i] for i in unmask(fields[6]) if i < len(table.get("meas", []))],
        "cyc": CYCLE_ENUM.get(fields[7], "unknown"),
    }


BINARY_CLAIM_SIZE = struct.calcsize(">IHHIIIIB")


def write_claims_binary(claims: List[Claim], bin_path: str,
                        table_path: str) -> dict:
    """Write .claims.bin and CLAIM_TABLE.json."""
    table: dict = {}
    blobs = []
    for c in claims:
        blobs.append(pack_claim(c, table))
    with open(bin_path, "wb") as f:
        for b in blobs:
            f.write(b)
    with open(table_path, "w") as f:
        json.dump(table, f, indent=2)
    return table


def read_claims_binary(bin_path: str, table_path: str) -> List[dict]:
    """Read .claims.bin using CLAIM_TABLE.json."""
    with open(table_path) as f:
        table = json.load(f)
    data = pathlib.Path(bin_path).read_bytes()
    claims = []
    for i in range(0, len(data), BINARY_CLAIM_SIZE):
        chunk = data[i:i + BINARY_CLAIM_SIZE]
        if len(chunk) == BINARY_CLAIM_SIZE:
            claims.append(unpack_claim(chunk, table))
    return claims


# ================================================================
# Layer 4 — Claim table generation
# ================================================================

def build_claim_table(claims: List[Claim]) -> dict:
    """Build CLAIM_TABLE.json from a list of claims."""
    table: dict = {}
    for c in claims:
        _index_or_add(table, "rates", c.rate)
        _index_or_add(table, "bounds", ",".join(str(b) for b in c.bounds))
        for cond in c.cond:
            _index_or_add(table, "cond", cond)
        for rel in c.rel:
            _index_or_add(table, "rel", rel)
        for fail in c.fail:
            _index_or_add(table, "fail", fail)
        for meas in c.meas:
            _index_or_add(table, "meas", meas)
    return table


# ================================================================
# Bridge to claim_validator.py
# ================================================================

def claim_to_prose(claim: Claim) -> str:
    """Convert structured claim to prose for claim_validator input."""
    parts = [f"Rate: {claim.rate}."]
    if claim.bounds:
        parts.append(f"Bounds: {', '.join(str(b) for b in claim.bounds)}.")
    if claim.cond:
        parts.append(f"Conditions: {', '.join(claim.cond)}.")
    if claim.fail:
        parts.append(f"Invalid if: {', '.join(claim.fail)}.")
    if claim.meas:
        parts.append(f"Measured by: {', '.join(claim.meas)}.")
    parts.append(f"Cycle: {claim.cycle_name()}.")
    return " ".join(parts)


def validate_claim_structured(claim: Claim) -> Optional[dict]:
    """Run a structured claim through claim_validator."""
    try:
        from claim_validator import validate_claim
        prose = claim_to_prose(claim)
        report = validate_claim(prose)
        return {
            "claim_id": claim.id,
            "concern": report.overall_concern,
            "interpretation": report.interpretation,
            "falsifiability": report.falsifiability.score,
            "tier_scores": {d.name: d.score for d in report.domain_scores},
        }
    except ImportError:
        return None


# ================================================================
# Mandala-Computing claims (extracted from codebase)
# ================================================================

MANDALA_CLAIMS = [
    Claim(
        id="oct_encode",
        rate="dS/dt=phi^depth*coupling",
        bounds=["octahedral_lattice", "8_states", "0-7"],
        cond=["phi>0", "depth>=1", "coupling>0"],
        rel=["energy_min", "factor_reg"],
        fail=["states<2", "coupling=0"],
        meas=["cell_state_histogram", "energy_trace", "glyph_trace"],
        cyc=0,
    ),
    Claim(
        id="energy_min",
        rate="dE/dt=-J*sin(|si-sj|*pi/4)^2",
        bounds=["cell_pair", "metropolis", "T>0"],
        cond=["J>0", "T>0", "neighbors_connected"],
        rel=["oct_encode", "anneal_conv"],
        fail=["T=0_frozen", "disconnected_graph"],
        meas=["energy_history", "acceptance_rate", "ground_state"],
        cyc=0,
    ),
    Claim(
        id="anneal_conv",
        rate="dT/dt=-T*cooling_rate",
        bounds=["T_start>T_KT", "T_end<<T_KT", "exp_schedule"],
        cond=["steps>100", "cooling_rate<1"],
        rel=["energy_min", "kt_phase"],
        fail=["T_start<T_end", "steps<10"],
        meas=["final_energy", "convergence_step", "temperature_trace"],
        cyc=0,
    ),
    Claim(
        id="kt_phase",
        rate="dV/dt=-vortex_binding_rate(T)",
        bounds=["XY_model", "phi_lattice", "T_KT=pi*phi/2"],
        cond=["J=phi", "adjacency_connected"],
        rel=["anneal_conv", "coherence"],
        fail=["T>5*T_KT", "isolated_nodes"],
        meas=["vortex_count", "phase_coherence", "kt_transition_step"],
        cyc=0,
    ),
    Claim(
        id="coherence",
        rate="dR/dt=alignment_torque(phases)",
        bounds=["unit_circle", "R_in_0_1", "XY_order_param"],
        cond=["T<T_KT", "connected_lattice"],
        rel=["kt_phase", "energy_min"],
        fail=["T>>T_KT", "R<0"],
        meas=["phase_coherence_R", "mean_exp_i_theta"],
        cyc=0,
    ),
    Claim(
        id="factor_reg",
        rate="dE_fact/dt=-(fa*fb-N)^2*gradient",
        bounds=["base8_register", "sqrt_N_cells", "bipartite"],
        cond=["N>1", "N_composite", "cells>=2"],
        rel=["oct_encode", "energy_min"],
        fail=["N_prime", "register_overflow"],
        meas=["residual", "best_pair", "verified_bool"],
        cyc=0,
    ),
    Claim(
        id="substrate_eq",
        rate="dGeometry/dt=sum(Basin_i*depth_i)",
        bounds=["all_substrates", "no_privilege", "breathing"],
        cond=[">=1_stream", "intersection_rule_registered"],
        rel=["breathing", "tension_signal"],
        fail=["zero_streams", "no_rules"],
        meas=["information_axes", "domain_coverage", "confidence_field"],
        cyc=0,
    ),
    Claim(
        id="breathing",
        rate="dMandala/dt=expand(streams)-contract(dropouts)",
        bounds=["runtime", "per_breath_cycle", "never_fails"],
        cond=["mandala_initialized"],
        rel=["substrate_eq", "resonate"],
        fail=["mandala_not_initialized"],
        meas=["total_axes_before_after", "domains_active", "basins_count"],
        cyc=0,
    ),
    Claim(
        id="resonate",
        rate="dCoupling/dt=sum(rule_fires)*synthesis_depth",
        bounds=["cross_domain", "EXPAND_ALIGN_STRUCTURE", "RSC_rules"],
        cond=[">=2_domains", "synthesis_enabled"],
        rel=["breathing", "substrate_eq", "verify_asym"],
        fail=["single_domain", "no_synthesis_engine"],
        meas=["synthesis_products", "coupling_strength", "cayley_factor"],
        cyc=0,
    ),
    Claim(
        id="verify_asym",
        rate="dConcern/dt=claim_validator(synthesis_why)",
        bounds=["T1_floor", "tier_hierarchy", "physics_grounded"],
        cond=["claim_validator_available"],
        rel=["resonate", "fabrication"],
        fail=["no_validator"],
        meas=["concern_score", "grounding_score", "falsifiability"],
        cyc=0,
    ),
    Claim(
        id="fabrication",
        rate="dDevice/dt=stage_sequence(7_stages)",
        bounds=["77-400K", "sub_Landauer", "sp3_109.47deg"],
        cond=["silicon_substrate", "ratio_invariant"],
        rel=["verify_asym", "oct_encode"],
        fail=["T<77K", "T>400K", "non_reversible_erase"],
        meas=["energy_per_bit_aJ", "fault_recovery_pct", "switching_THz"],
        cyc=0,
    ),
    Claim(
        id="lid_bridge",
        rate="dBasin/dt=DynamicsProjector(LID_entity)",
        bounds=["Layer3_to_Layer4", "open_substrate", "any_ontology"],
        cond=["projector_registered", "entity_has_patterns"],
        rel=["substrate_eq", "resonate"],
        fail=["no_projector", "empty_entity"],
        meas=["basins_emitted", "provenance_attached", "collectivity_score"],
        cyc=0,
    ),
]


# ================================================================
# Demo
# ================================================================

def demo():
    print("=" * 60)
    print("CLAIM SCHEMA — Compressed Differential Claims")
    print("=" * 60)

    print(f"\n  {len(MANDALA_CLAIMS)} claims extracted from Mandala-Computing")

    # Line format demo
    print(f"\n  Line format (first 3):")
    for c in MANDALA_CLAIMS[:3]:
        line = claim_to_line(c)
        print(f"    {line}")

    # Binary demo
    table: dict = {}
    total_bytes = 0
    for c in MANDALA_CLAIMS:
        blob = pack_claim(c, table)
        total_bytes += len(blob)
    print(f"\n  Binary: {total_bytes} bytes for {len(MANDALA_CLAIMS)} claims "
          f"({total_bytes / len(MANDALA_CLAIMS):.0f} bytes/claim)")
    print(f"  Table entries: {sum(len(v) for v in table.values())}")

    # Validation bridge demo
    print(f"\n  Validation bridge (first 2):")
    for c in MANDALA_CLAIMS[:2]:
        result = validate_claim_structured(c)
        if result:
            print(f"    {c.id}: concern={result['concern']:.2f}  "
                  f"falsifiability={result['falsifiability']:.2f}")
    print()


if __name__ == "__main__":
    demo()
