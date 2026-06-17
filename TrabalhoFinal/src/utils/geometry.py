"""Funções geométricas auxiliares."""
from __future__ import annotations

from math import hypot


def euclid(ax: float, ay: float, bx: float, by: float) -> float:
    """Distância euclidiana entre (ax, ay) e (bx, by)."""
    return hypot(ax - bx, ay - by)


def bounding_box(vertices) -> tuple[float, float, float, float]:
    """Retorna (min_x, min_y, max_x, max_y) dos vértices ativos.

    Para grafo vazio retorna (0, 0, 1, 1) para evitar divisão por zero
    nos cálculos de escala da visualização.
    """
    xs = [v.x for v in vertices if getattr(v, "active", True)]
    ys = [v.y for v in vertices if getattr(v, "active", True)]
    if not xs:
        return (0.0, 0.0, 1.0, 1.0)
    return (min(xs), min(ys), max(xs), max(ys))
