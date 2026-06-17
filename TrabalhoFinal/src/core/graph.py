"""
Grafo ponderado representado por lista de adjacência (autoral).

- Vértices têm id posicional (0..n-1) e coordenadas cartesianas (x, y).
- Arestas guardam destino, peso (distância euclidiana) e a flag `oneway`.
- O grafo pode ser global-mente direcionado (`directed`) ou não. Vias de
  mão única são modeladas por arestas com `oneway=True` (um único sentido),
  independentemente do modo global.

Remoção de vértice usa *tombstone* (marcação de inativo) para não reindexar
e invalidar arestas existentes — ids permanecem estáveis.
"""
from __future__ import annotations

from math import hypot


class Vertex:
    __slots__ = ("id", "x", "y", "active")

    def __init__(self, vid: int, x: float, y: float) -> None:
        self.id = vid
        self.x = x
        self.y = y
        self.active = True

    def __repr__(self) -> str:
        return f"Vertex({self.id}, x={self.x:.2f}, y={self.y:.2f})"


class Edge:
    __slots__ = ("to", "weight", "oneway")

    def __init__(self, to: int, weight: float, oneway: bool = False) -> None:
        self.to = to
        self.weight = weight
        self.oneway = oneway

    def __repr__(self) -> str:
        seta = "→" if self.oneway else "—"
        return f"Edge({seta}{self.to}, w={self.weight:.2f})"


class Graph:
    __slots__ = ("vertices", "adj", "directed", "_edge_count")

    def __init__(self, directed: bool = False) -> None:
        self.vertices: list[Vertex] = []
        self.adj: list[list[Edge]] = []
        self.directed = directed
        self._edge_count = 0  # conta arestas dirigidas efetivamente armazenadas

    # --- construção ------------------------------------------------------
    def add_vertex(self, x: float, y: float) -> int:
        vid = len(self.vertices)
        self.vertices.append(Vertex(vid, x, y))
        self.adj.append([])
        return vid

    def add_edge(self, u: int, v: int, oneway: bool = False,
                 weight: float | None = None) -> None:
        """
        Adiciona aresta u→v.

        O peso é a distância euclidiana entre os vértices, salvo quando
        `weight` é informado explicitamente (ex.: formato .txt com pesos).

        Se a via é de mão única (`oneway`) ou o grafo é direcionado, grava
        apenas u→v. Caso contrário (mão dupla em grafo não-direcionado),
        grava também v→u.
        """
        if not (self._valid(u) and self._valid(v)) or u == v:
            return
        w = self.edge_weight(u, v) if weight is None else weight
        single = oneway or self.directed
        self.adj[u].append(Edge(v, w, oneway))
        self._edge_count += 1
        if not single:
            self.adj[v].append(Edge(u, w, oneway))
            self._edge_count += 1

    # --- remoção ---------------------------------------------------------
    def remove_edge(self, u: int, v: int) -> None:
        if self._valid(u):
            before = len(self.adj[u])
            self.adj[u] = [e for e in self.adj[u] if e.to != v]
            self._edge_count -= before - len(self.adj[u])
        if self._valid(v):
            before = len(self.adj[v])
            self.adj[v] = [e for e in self.adj[v] if e.to != u]
            self._edge_count -= before - len(self.adj[v])

    def remove_vertex(self, u: int) -> None:
        """Marca o vértice como inativo e remove todas as arestas incidentes."""
        if not self._valid(u):
            return
        self._edge_count -= len(self.adj[u])
        self.adj[u] = []
        self.vertices[u].active = False
        for w in range(len(self.adj)):
            before = len(self.adj[w])
            self.adj[w] = [e for e in self.adj[w] if e.to != u]
            self._edge_count -= before - len(self.adj[w])

    # --- consultas -------------------------------------------------------
    def edge_weight(self, u: int, v: int) -> float:
        a, b = self.vertices[u], self.vertices[v]
        return hypot(a.x - b.x, a.y - b.y)

    def num_vertices(self) -> int:
        return sum(1 for v in self.vertices if v.active)

    def num_edges(self) -> int:
        return self._edge_count

    def size(self) -> int:
        """Tamanho do vetor de vértices (inclui inativos) — para indexação."""
        return len(self.vertices)

    def _valid(self, u: int) -> bool:
        return 0 <= u < len(self.vertices) and self.vertices[u].active
