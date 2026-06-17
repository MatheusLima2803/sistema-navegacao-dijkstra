"""
Algoritmo de Dijkstra (autoral) com heap mínima e *lazy deletion*.

Estruturas exigidas pela disciplina (seção 5 da documentação):
  - vetor de distâncias  (dist)
  - vetor de predecessores (prev) — reconstrói o caminho
  - conjunto de visitados (visited)
  - fila de prioridade (MinHeap)

Complexidade: O((V + E) · log V) tempo, O(V) memória adicional.
"""
from __future__ import annotations

from time import perf_counter

from .graph import Graph
from .min_heap import MinHeap

INF = float("inf")


class DijkstraResult:
    __slots__ = ("dist", "path", "nodes_explored", "elapsed_ms")

    def __init__(self, dist: float, path: list[int],
                 nodes_explored: int, elapsed_ms: float) -> None:
        self.dist = dist
        self.path = path
        self.nodes_explored = nodes_explored
        self.elapsed_ms = elapsed_ms

    @property
    def found(self) -> bool:
        return self.dist != INF and len(self.path) > 0

    def __repr__(self) -> str:
        return (f"DijkstraResult(dist={self.dist:.2f}, "
                f"|path|={len(self.path)}, explored={self.nodes_explored}, "
                f"{self.elapsed_ms:.2f} ms)")


def dijkstra(g: Graph, source: int, target: int) -> DijkstraResult:
    """Menor caminho de `source` a `target` segundo Dijkstra."""
    start = perf_counter()
    n = g.size()

    if not (0 <= source < n and 0 <= target < n):
        return DijkstraResult(INF, [], 0, (perf_counter() - start) * 1000.0)

    dist = [INF] * n
    prev = [-1] * n
    visited = [False] * n

    dist[source] = 0.0
    heap = MinHeap()
    heap.push(0.0, source)
    explored = 0

    while not heap.is_empty():
        d, u = heap.pop_min()
        if visited[u]:
            continue  # entrada obsoleta (lazy deletion)
        visited[u] = True
        explored += 1
        if u == target:
            break  # parada antecipada — o alvo já está finalizado
        for e in g.adj[u]:
            v = e.to
            if not visited[v]:
                nd = d + e.weight
                if nd < dist[v]:
                    dist[v] = nd
                    prev[v] = u
                    heap.push(nd, v)

    elapsed_ms = (perf_counter() - start) * 1000.0

    if dist[target] == INF:
        return DijkstraResult(INF, [], explored, elapsed_ms)

    # reconstrói o caminho da origem ao destino via predecessores
    path: list[int] = []
    v = target
    while v != -1:
        path.append(v)
        v = prev[v]
    path.reverse()

    return DijkstraResult(dist[target], path, explored, elapsed_ms)
