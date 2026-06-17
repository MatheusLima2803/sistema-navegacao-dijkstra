"""
Índice espacial em grade uniforme.

Permite achar o vértice mais próximo de um ponto (clique do mouse) em tempo
quase O(1), evitando varrer todos os vértices a cada evento de mouse — crucial
para grafos com milhares de nós (RNF03/04).
"""
from __future__ import annotations

import math
from math import hypot, floor


class SpatialGrid:
    __slots__ = ("_cells", "_cell", "_min_x", "_min_y", "_vertices")

    def __init__(self, vertices, target_per_cell: int = 4) -> None:
        self._cells: dict[tuple[int, int], list[int]] = {}
        self._cell = 1.0
        self._min_x = 0.0
        self._min_y = 0.0
        self._vertices = vertices
        self.rebuild(vertices, target_per_cell)

    def rebuild(self, vertices, target_per_cell: int = 4) -> None:
        self._vertices = vertices
        self._cells = {}
        active = [v for v in vertices if v.active]
        if not active:
            self._cell = 1.0
            return

        xs = [v.x for v in active]
        ys = [v.y for v in active]
        self._min_x, self._min_y = min(xs), min(ys)
        width = max(max(xs) - self._min_x, 1e-9)
        height = max(max(ys) - self._min_y, 1e-9)

        cols = max(1, int(math.sqrt(len(active) / target_per_cell)))
        self._cell = max(width, height) / cols

        for v in active:
            self._cells.setdefault(self._key(v.x, v.y), []).append(v.id)

    def _key(self, x: float, y: float) -> tuple[int, int]:
        return (floor((x - self._min_x) / self._cell),
                floor((y - self._min_y) / self._cell))

    def nearest(self, x: float, y: float, max_dist: float) -> int | None:
        """Vértice mais próximo de (x, y) dentro de `max_dist`, ou None."""
        if not self._cells:
            return None
        cx, cy = self._key(x, y)
        rings = max(1, int(max_dist / self._cell) + 1)
        best_id: int | None = None
        best_d = max_dist
        for dx in range(-rings, rings + 1):
            for dy in range(-rings, rings + 1):
                bucket = self._cells.get((cx + dx, cy + dy))
                if not bucket:
                    continue
                for vid in bucket:
                    v = self._vertices[vid]
                    d = hypot(v.x - x, v.y - y)
                    if d < best_d:
                        best_d = d
                        best_id = vid
        return best_id
