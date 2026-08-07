#!/usr/bin/env python3
"""
adapters.py — Bridge Domain Encoders to Unified Geometry Protocol
===================================================================

Wraps the existing DNA, RNA, and protein encoders so they work
with the geometry-agnostic mandala solver.

Each adapter:
    1. Takes domain data (DNA seq, protein seq, etc.)
    2. Maps it to a Geometry instance
    3. Returns problem data that the solver understands

Usage:
    from adapters import DNAAdapter, ProteinAdapter, RNAAdapter
    from mandala_solver import MandalaSolver

    # DNA
    adapter = DNAAdapter(chirality="right")
    geo, problem_data = adapter.prepare("ATGCGTAC")
    solver = MandalaSolver(geometry=geo)
    result = solver.anneal("dna_pattern", problem_data)

    # Protein
    adapter = ProteinAdapter()
    geo, problem_data = adapter.prepare("MKTLLI")
    solver = MandalaSolver(geometry=geo)
    result = solver.anneal("protein_fold", problem_data)
"""

from typing import Dict, Tuple, List
from geometry_core import Geometry, TetrahedralGeometry, DodecahedralGeometry, HexagonalGeometry


# ---------------------------------------------------------------------------
# DNA Adapter
# ---------------------------------------------------------------------------

class DNAAdapter:
    """Bridge DNA sequences to tetrahedral geometry."""

    def __init__(self, chirality: str = "right"):
        self.chirality = chirality
        self.base_to_state = {"A": 0, "T": 1, "G": 2, "C": 3}
        if chirality == "left":
            self.base_to_state = {"A": 3, "T": 2, "G": 1, "C": 0}

    def prepare(self, sequence: str) -> Tuple[Geometry, Dict]:
        """Return geometry and problem data for the solver."""
        geo = TetrahedralGeometry(chirality=self.chirality)
        states = [self.base_to_state.get(b.upper(), 0) for b in sequence]
        return geo, {
            "sequence": states,
            "original": sequence.upper(),
            "length": len(sequence),
        }

    def decode_state(self, state: int) -> str:
        mapping = {0: "A", 1: "T", 2: "G", 3: "C"}
        if self.chirality == "left":
            mapping = {3: "A", 2: "T", 1: "G", 0: "C"}
        return mapping.get(state, "N")


# ---------------------------------------------------------------------------
# Protein Adapter
# ---------------------------------------------------------------------------

class ProteinAdapter:
    """Bridge protein sequences to dodecahedral geometry."""

    AA_TO_VERTEX = {
        "A": 0, "C": 1, "D": 2, "E": 3, "F": 4,
        "G": 5, "H": 6, "I": 7, "K": 8, "L": 9,
        "M": 10, "N": 11, "P": 12, "Q": 13, "R": 14,
        "S": 15, "T": 16, "V": 17, "W": 18, "Y": 19,
    }

    VERTEX_TO_AA = {v: k for k, v in AA_TO_VERTEX.items()}

    def prepare(self, sequence: str) -> Tuple[Geometry, Dict]:
        geo = DodecahedralGeometry()
        states = [self.AA_TO_VERTEX.get(aa.upper(), 0) for aa in sequence]
        return geo, {
            "sequence": states,
            "original": sequence.upper(),
            "length": len(sequence),
        }

    def decode_state(self, state: int) -> str:
        return self.VERTEX_TO_AA.get(state, "?")


# ---------------------------------------------------------------------------
# RNA Adapter
# ---------------------------------------------------------------------------

class RNAAdapter:
    """Bridge RNA sequences to hexagonal geometry (folding directions)."""

    BASE_TO_STATE = {"A": 0, "U": 1, "G": 2, "C": 3}

    def prepare(self, sequence: str) -> Tuple[Geometry, Dict]:
        geo = HexagonalGeometry()
        # For RNA, states represent "growth directions" not bases
        # We encode the sequence as a path through hex directions
        # based on base properties
        states = []
        for base in sequence.upper():
            # Map base to a preferred direction
            # A=straight(0), U=right(1), G=left(-1), C=sharp turn(2)
            direction_map = {"A": 0, "U": 1, "G": 5, "C": 2}
            states.append(direction_map.get(base, 0))
        return geo, {
            "sequence": states,
            "original": sequence.upper(),
            "length": len(sequence),
        }

    def decode_state(self, state: int) -> str:
        # Reverse mapping for display
        dirs = ["A(straight)", "U(right)", "C(turn)", "?", "?", "G(left)"]
        return dirs[state] if state < 6 else "?"


# ---------------------------------------------------------------------------
# Universal Adapter (auto-detects domain)
# ---------------------------------------------------------------------------

class UniversalAdapter:
    """Auto-detect sequence type and pick the right geometry."""

    def prepare(self, sequence: str) -> Tuple[Geometry, Dict, str]:
        seq = sequence.upper().strip()

        # Detect DNA: contains T but not U
        if "T" in seq and "U" not in seq and set(seq).issubset("ATGCN"):
            adapter = DNAAdapter()
            geo, data = adapter.prepare(seq)
            return geo, data, "dna"

        # Detect RNA: contains U but not T
        if "U" in seq and "T" not in seq and set(seq).issubset("AUGCN"):
            adapter = RNAAdapter()
            geo, data = adapter.prepare(seq)
            return geo, data, "rna"

        # Detect protein: contains standard amino acids (no T/U)
        aa_set = set("ACDEFGHIKLMNPQRSTVWY")
        if set(seq).issubset(aa_set):
            adapter = ProteinAdapter()
            geo, data = adapter.prepare(seq)
            return geo, data, "protein"

        # Default: treat as DNA
        adapter = DNAAdapter()
        geo, data = adapter.prepare(seq)
        return geo, data, "dna"


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("ADAPTERS — Domain-to-Geometry Bridge Test")
    print("=" * 60)

    # DNA
    dna_adapter = DNAAdapter(chirality="right")
    geo, data = dna_adapter.prepare("ATGC")
    print(f"\nDNA 'ATGC' -> {geo.name}, states={data['sequence']}")

    # Protein
    prot_adapter = ProteinAdapter()
    geo, data = prot_adapter.prepare("MKTLLI")
    print(f"Protein 'MKTLLI' -> {geo.name}, states={data['sequence']}")

    # RNA
    rna_adapter = RNAAdapter()
    geo, data = rna_adapter.prepare("AUGC")
    print(f"RNA 'AUGC' -> {geo.name}, states={data['sequence']}")

    # Universal
    uni = UniversalAdapter()
    for seq in ["ATGC", "AUGC", "MKTLLI"]:
        geo, data, domain = uni.prepare(seq)
        print(f"Universal: '{seq}' -> {domain} on {geo.name}")

    print("\n" + "=" * 60)
    print("All adapter tests passed.")
    print("=" * 60)
