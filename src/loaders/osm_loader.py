"""
Leitor de arquivos .osm (OpenStreetMap XML), importando direto para Graph.

Espelha LeArqOSM_e_GeraArqPoly.c: extrai <node> (lat/lon), converte para
coordenadas cartesianas UTM (zona 23S, WGS84), monta arestas a partir dos
pares consecutivos de <nd> dentro de cada <way>, reduz a escala e inverte
o eixo Y (origem no canto superior-esquerdo, como no componente de imagem).

Parsing autoral linha-a-linha — sem dependência de OSMnx.
"""
from __future__ import annotations

import re
from math import sin, cos, tan, sqrt, pi

from src.core import Graph

# Parâmetros WGS84 / UTM zona 23S
_A = 6378137.0
_F = 1.0 / 298.257223563
_K0 = 0.9996
_LON0_DEG = -45.0  # meridiano central da zona 23
_SCALE_REDUCER = 2

_ATTR = {k: re.compile(k + r'="([^"]*)"') for k in ("id", "lat", "lon", "ref")}


def _attr(line: str, key: str) -> str | None:
    m = _ATTR[key].search(line)
    return m.group(1) if m else None


def _latlon_to_utm(lat_deg: float, lon_deg: float) -> tuple[float, float]:
    e2 = _F * (2 - _F)
    ep2 = e2 / (1 - e2)
    lat = lat_deg * pi / 180.0
    lon = lon_deg * pi / 180.0
    lon0 = _LON0_DEG * pi / 180.0

    N = _A / sqrt(1 - e2 * sin(lat) ** 2)
    T = tan(lat) ** 2
    C = ep2 * cos(lat) ** 2
    A = (lon - lon0) * cos(lat)

    M = _A * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * lat
              - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * sin(2 * lat)
              + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * sin(4 * lat)
              - (35 * e2 ** 3 / 3072) * sin(6 * lat))

    x = _K0 * N * (A + (1 - T + C) * A ** 3 / 6
                   + (5 - 18 * T + T ** 2 + 72 * C - 58 * ep2) * A ** 5 / 120) + 500000.0
    y = _K0 * (M + N * tan(lat) * (A ** 2 / 2
               + (5 - T + 9 * C + 4 * C ** 2) * A ** 4 / 24
               + (61 - 58 * T + T ** 2 + 600 * C - 330 * ep2) * A ** 6 / 720))
    if lat_deg < 0:
        y += 10000000.0
    return x, y


def load_osm(path: str) -> Graph:
    raw_x: list[float] = []
    raw_y: list[float] = []
    id_to_index: dict[int, int] = {}
    ways: list[list[int]] = []

    inside_way = False
    current: list[int] = []

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "<node" in line and "lat=" in line and "lon=" in line:
                oid = _attr(line, "id")
                lat = _attr(line, "lat")
                lon = _attr(line, "lon")
                if oid is None or lat is None or lon is None:
                    continue
                x, y = _latlon_to_utm(float(lat), float(lon))
                id_to_index[int(oid)] = len(raw_x)
                raw_x.append(x)
                raw_y.append(y)
            elif "<way" in line:
                inside_way = True
                current = []
            elif inside_way and "<nd" in line:
                ref = _attr(line, "ref")
                if ref is not None:
                    idx = id_to_index.get(int(ref))
                    if idx is not None:
                        current.append(idx)
            elif inside_way and "</way>" in line:
                inside_way = False
                if len(current) > 1:
                    ways.append(current)

    if not raw_x:
        raise ValueError("Nenhum nó encontrado no arquivo .osm")

    # reduz escala em relação ao mínimo
    min_x, min_y = min(raw_x), min(raw_y)
    xs = [(x - min_x) / _SCALE_REDUCER for x in raw_x]
    ys = [(y - min_y) / _SCALE_REDUCER for y in raw_y]
    # inverte Y (origem no topo-esquerda)
    max_y = max(ys)
    ys = [max_y - y for y in ys]

    g = Graph(directed=False)
    for x, y in zip(xs, ys):
        g.add_vertex(x, y)
    for w in ways:
        for j in range(len(w) - 1):
            g.add_edge(w[j], w[j + 1], oneway=False)
    return g
