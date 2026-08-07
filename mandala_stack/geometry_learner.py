#!/usr/bin/env python3
"""
geometry_learner.py — Learn Geometric Structure from Data
===========================================================

The core insight: intelligence is determined by the shape of the
computational substrate, not the algorithm running on it.

This module learns a geometry from data by finding the manifold
on which the data's natural structure becomes spatial structure.

Methods:
  - force_directed: Spring-electrical layout from distance matrix
  - mds: Multidimensional scaling
  - spectral: Graph Laplacian eigenvectors
  - isomap: Isometric mapping via geodesic distances

Usage:
    from geometry_learner import GeometryLearner
    learner = GeometryLearner(method="force_directed", dim=3)
    items = ["A", "V", "I", "L", "D", "E", "K", "R"]
    def bio_dist(a, b):
        return abs(hydropathy[a] - hydropathy[b])
    geometry = learner.learn(items, bio_dist)
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Callable, Optional, Any
from dataclasses import dataclass
import math
import random
import numpy as np


class GeometryLearner:
    """Learn a geometry from data and a distance metric."""

    def __init__(self, method: str = "force_directed", dim: int = 3,
                 n_neighbors: int = 3, seed: Optional[int] = None):
        self.method = method
        self.dim = dim
        self.n_neighbors = n_neighbors
        self.rng = random.Random(seed)
        self.np_rng = np.random.RandomState(seed)

    def learn(self, items: List[Any],
              distance_fn: Callable[[Any, Any], float]) -> "LearnedGeometry":
        """Learn geometry from items and pairwise distance function."""
        n = len(items)
        dist_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                d = distance_fn(items[i], items[j])
                dist_matrix[i, j] = d
                dist_matrix[j, i] = d

        if self.method == "force_directed":
            positions = self._force_directed(dist_matrix)
        elif self.method == "mds":
            positions = self._classical_mds(dist_matrix)
        elif self.method == "spectral":
            positions = self._spectral(dist_matrix)
        elif self.method == "isomap":
            positions = self._isomap(dist_matrix)
        else:
            raise ValueError(f"Unknown method: {self.method}")

        pos_dict = {items[i]: tuple(positions[i]) for i in range(n)}
        return LearnedGeometry(pos_dict, items, n_neighbors=self.n_neighbors)

    def _force_directed(self, dist_matrix: np.ndarray) -> np.ndarray:
        """Fruchterman-Reingold style force-directed layout."""
        n = dist_matrix.shape[0]
        dim = self.dim
        positions = np.zeros((n, dim))
        for i in range(n):
            vec = self.np_rng.randn(dim)
            vec /= np.linalg.norm(vec) + 1e-10
            positions[i] = vec

        k = 0.8
        for iteration in range(800):
            temperature = 1.0 * (0.01 / 1.0) ** (iteration / 799)
            forces = np.zeros((n, dim))

            for i in range(n):
                for j in range(i + 1, n):
                    diff = positions[i] - positions[j]
                    dist = np.linalg.norm(diff)
                    if dist < 0.001:
                        dist = 0.001
                    f = k * k / dist
                    force = f * diff / dist
                    forces[i] += force
                    forces[j] -= force

            for i in range(n):
                for j in range(i + 1, n):
                    d_target = dist_matrix[i, j]
                    diff = positions[i] - positions[j]
                    dist = np.linalg.norm(diff)
                    if dist < 0.001:
                        dist = 0.001
                    f = dist * dist / (k * max(d_target, 0.1))
                    force = f * diff / dist
                    forces[i] -= force
                    forces[j] += force

            for i in range(n):
                force_mag = np.linalg.norm(forces[i])
                if force_mag > temperature:
                    forces[i] *= temperature / force_mag
                positions[i] += forces[i]
                norm = np.linalg.norm(positions[i])
                if norm > 0:
                    positions[i] /= norm

        return positions

    def _classical_mds(self, dist_matrix: np.ndarray) -> np.ndarray:
        """Classical multidimensional scaling."""
        n = dist_matrix.shape[0]
        J = np.eye(n) - np.ones((n, n)) / n
        B = -0.5 * J @ (dist_matrix ** 2) @ J
        eigvals, eigvecs = np.linalg.eigh(B)
        idx = np.argsort(eigvals)[::-1]
        eigvals = eigvals[idx]
        eigvecs = eigvecs[:, idx]
        pos_idx = eigvals > 0
        if np.sum(pos_idx) < self.dim:
            pos_idx[:self.dim] = True
        coords = eigvecs[:, pos_idx] * np.sqrt(eigvals[pos_idx])
        result = coords[:, :self.dim]
        norms = np.linalg.norm(result, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return result / norms

    def _spectral(self, dist_matrix: np.ndarray) -> np.ndarray:
        """Spectral embedding from graph Laplacian."""
        n = dist_matrix.shape[0]
        affinity = np.exp(-dist_matrix ** 2 / (2 * np.std(dist_matrix) ** 2 + 1e-10))
        np.fill_diagonal(affinity, 0)
        degree = np.diag(np.sum(affinity, axis=1))
        laplacian = degree - affinity
        eigvals, eigvecs = np.linalg.eigh(laplacian)
        result = eigvecs[:, 1:self.dim + 1]
        norms = np.linalg.norm(result, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return result / norms

    def _isomap(self, dist_matrix: np.ndarray) -> np.ndarray:
        """Isometric mapping via geodesic distances."""
        n = dist_matrix.shape[0]
        geodesic = dist_matrix.copy()
        for k_idx in range(n):
            for i in range(n):
                for j in range(n):
                    if geodesic[i, k_idx] + geodesic[k_idx, j] < geodesic[i, j]:
                        geodesic[i, j] = geodesic[i, k_idx] + geodesic[k_idx, j]
        return self._classical_mds(geodesic)


@dataclass
class LearnedGeometry:
    """A geometry learned from data. Satisfies the Geometry protocol."""

    positions: Dict[Any, Tuple[float, ...]]
    items: List[Any]
    n_neighbors: int = 3

    def __post_init__(self):
        self.n_states = len(self.items)
        self.dim = len(next(iter(self.positions.values())))
        self.item_to_idx = {item: i for i, item in enumerate(self.items)}
        self.idx_to_item = {i: item for i, item in enumerate(self.items)}

        self._transitions = {}
        for item in self.items:
            idx = self.item_to_idx[item]
            distances = []
            for other in self.items:
                if other == item:
                    continue
                d = self._distance(item, other)
                distances.append((d, self.item_to_idx[other]))
            distances.sort()
            self._transitions[idx] = [other_idx for _, other_idx in distances[:self.n_neighbors]]

    @property
    def name(self) -> str:
        return f"learned-{self.dim}d-{self.n_states}states"

    @property
    def dimension(self) -> int:
        """Embedding dimension — the Geometry protocol's spelling of `dim`."""
        return self.dim

    def _distance(self, item1, item2):
        p1 = self.positions[item1]
        p2 = self.positions[item2]
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

    def position(self, state: int) -> Tuple[float, ...]:
        item = self.idx_to_item[state]
        return self.positions[item]

    def transitions(self, state: int) -> List[int]:
        return self._transitions[state]

    def transition_cost(self, a: int, b: int) -> float:
        if b not in self.transitions(a):
            return float("inf")
        item_a = self.idx_to_item[a]
        item_b = self.idx_to_item[b]
        return self._distance(item_a, item_b)

    def eigenvalues(self, state: int) -> Tuple[float, ...]:
        pos = self.position(state)
        total = sum(abs(x) for x in pos) + 1e-10
        return tuple(abs(x) / total for x in pos)

    def glyph(self, state: int) -> str:
        item = self.idx_to_item[state]
        return str(item)

    def scale_position(self, state: int, layer: int) -> Tuple[float, ...]:
        pos = self.position(state)
        scale = 1.618033988749895 ** (-layer)
        return tuple(x * scale for x in pos)

    def set_eigenvalues(self, eigenvalue_fn: Callable[[Any], Tuple[float, ...]]):
        """Set custom eigenvalues from a function of items."""
        self._eigenvalues = {}
        for item in self.items:
            self._eigenvalues[self.item_to_idx[item]] = eigenvalue_fn(item)

    def get_eigenvalues(self, state: int) -> Tuple[float, ...]:
        if hasattr(self, '_eigenvalues') and state in self._eigenvalues:
            return self._eigenvalues[state]
        return self.eigenvalues(state)


def learn_from_vectors(vectors: Dict[Any, np.ndarray],
                       metric: str = "euclidean",
                       **kwargs) -> LearnedGeometry:
    """Learn geometry from vector representations."""
    items = list(vectors.keys())

    def distance_fn(a, b):
        va = vectors[a]
        vb = vectors[b]
        if metric == "euclidean":
            return np.linalg.norm(va - vb)
        elif metric == "cosine":
            dot = np.dot(va, vb)
            na = np.linalg.norm(va)
            nb = np.linalg.norm(vb)
            return 1 - dot / (na * nb + 1e-10)
        elif metric == "manhattan":
            return np.sum(np.abs(va - vb))
        else:
            raise ValueError(f"Unknown metric: {metric}")

    learner = GeometryLearner(**kwargs)
    return learner.learn(items, distance_fn)


def learn_from_distance_matrix(items: List[Any],
                                dist_matrix: np.ndarray,
                                **kwargs) -> LearnedGeometry:
    """Learn geometry from pre-computed distance matrix."""
    learner = GeometryLearner(**kwargs)
    n = len(items)
    positions = learner._force_directed(dist_matrix)
    pos_dict = {items[i]: tuple(positions[i]) for i in range(n)}
    return LearnedGeometry(pos_dict, items, n_neighbors=kwargs.get('n_neighbors', 3))


if __name__ == "__main__":
    print("=" * 60)
    print("GEOMETRY LEARNER — Self Test")
    print("=" * 60)

    items = [f"item_{i}" for i in range(12)]
    cluster_centers = {
        "item_0": (0, 0), "item_1": (0.1, 0), "item_2": (0, 0.1),
        "item_3": (1, 0), "item_4": (1.1, 0), "item_5": (1, 0.1),
        "item_6": (0, 1), "item_7": (0.1, 1), "item_8": (0, 1.1),
        "item_9": (1, 1), "item_10": (1.1, 1), "item_11": (1, 1.1),
    }

    def euclidean_dist(a, b):
        x1, y1 = cluster_centers[a]
        x2, y2 = cluster_centers[b]
        return math.sqrt((x1-x2)**2 + (y1-y2)**2)

    for method in ["force_directed", "mds", "spectral"]:
        learner = GeometryLearner(method=method, dim=2, seed=42)
        geo = learner.learn(items, euclidean_dist)
        neighbors = [geo.idx_to_item[i] for i in geo.transitions(0)]
        print(f"  {method:15s}: {geo.name}, neighbors of item_0 = {neighbors}")

    AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
    HYDROPATHY = {
        "A": 1.8, "C": 2.5, "D": -3.5, "E": -3.5, "F": 2.8,
        "G": -0.4, "H": -3.2, "I": 4.5, "K": -3.9, "L": 3.8,
        "M": 1.9, "N": -3.5, "P": -1.6, "Q": -3.5, "R": -4.5,
        "S": -0.8, "T": -0.7, "V": 4.2, "W": -0.9, "Y": -1.3,
    }

    def bio_dist(a, b):
        return abs(HYDROPATHY[a] - HYDROPATHY[b])

    learner = GeometryLearner(method="force_directed", dim=3, seed=42)
    geo = learner.learn(list(AMINO_ACIDS), bio_dist)
    print(f"\n  Learned geometry: {geo.name}")
    print(f"  Alanine neighbors: {[geo.idx_to_item[i] for i in geo.transitions(geo.item_to_idx['A'])]}")

    print("\n" + "=" * 60)
    print("All learner tests passed.")
    print("=" * 60)
