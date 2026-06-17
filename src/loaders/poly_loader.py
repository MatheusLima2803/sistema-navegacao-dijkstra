"""
Leitor do formato .poly (saída de ConverteMapaParaGrafo.c).

Estrutura (campos separados por espaços/tabs):

    nVertices  2  0  1
    id  x  y                      (× nVertices, ids 0..n-1 em ordem)
    ...
    nArestas  1
    idAresta  origem  destino  0  (× nArestas)
    ...
    0                             (marcador de fim, ignorado)

- Coordenadas já são cartesianas (UTM) com Y invertido → uso direto na tela.
- O peso não consta: é calculado como distância euclidiana ao adicionar a
  aresta. Arestas representam segmentos de via → importadas como mão dupla.
"""
from __future__ import annotations

from src.core import Graph


def load_poly(path: str) -> Graph:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        tokens = f.read().split()

    if not tokens:
        raise ValueError("Arquivo .poly vazio")

    it = iter(tokens)

    def nxt() -> str:
        return next(it)

    n_vertices = int(nxt())
    # consome o resto do cabeçalho de vértices (dimensões e flags): 3 tokens
    for _ in range(3):
        nxt()

    g = Graph(directed=False)
    for _ in range(n_vertices):
        _id = int(nxt())          # esperado == índice; preservamos a ordem
        x = float(nxt())
        y = float(nxt())
        g.add_vertex(x, y)

    # cabeçalho de arestas: nArestas seguido de 1 flag
    n_edges = int(nxt())
    nxt()  # flag

    for _ in range(n_edges):
        nxt()                     # id da aresta (descartado)
        orig = int(nxt())
        dest = int(nxt())
        nxt()                     # flag (0)
        g.add_edge(orig, dest, oneway=False)

    return g
