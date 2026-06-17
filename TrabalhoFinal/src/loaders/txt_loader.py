"""
Leitor do formato .txt simples:  Origem,Destino,Peso  (um por linha).

Exemplo:
    A,B,10
    A,C,15
    B,D,8

Rótulos arbitrários são mapeados para ids internos. Como o arquivo não traz
coordenadas, os vértices são dispostos em círculo apenas para visualização;
o peso usado no Dijkstra é o informado no arquivo (não a distância na tela).
"""
from __future__ import annotations

from math import cos, sin, pi

from src.core import Graph


def load_txt(path: str) -> Graph:
    edges: list[tuple[str, str, float]] = []
    labels: dict[str, int] = {}
    order: list[str] = []

    def ensure(label: str) -> None:
        if label not in labels:
            labels[label] = len(order)
            order.append(label)

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.replace(";", ",").split(",")]
            if len(parts) < 3:
                continue
            a, b, w = parts[0], parts[1], parts[2]
            ensure(a)
            ensure(b)
            edges.append((a, b, float(w)))

    g = Graph(directed=False)
    n = max(len(order), 1)
    radius = 100.0 * n
    for i in range(len(order)):
        ang = 2 * pi * i / n
        g.add_vertex(radius * cos(ang) + radius, radius * sin(ang) + radius)

    for a, b, w in edges:
        g.add_edge(labels[a], labels[b], oneway=False, weight=w)
    return g
