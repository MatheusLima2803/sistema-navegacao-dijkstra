"""
Heap binária mínima (autoral) usada como fila de prioridade do Dijkstra.

Ordena por chave float crescente. Cada elemento é a tupla (chave, item),
onde `item` é o id de um vértice. A comparação de tuplas em Python já
desempata pela própria chave/id, então não precisamos de comparador custom.

Não implementa decrease-key: o Dijkstra usa *lazy deletion* (empurra uma
nova entrada quando a distância melhora e descarta entradas obsoletas no pop).
"""
from __future__ import annotations


class MinHeap:
    __slots__ = ("_data",)

    def __init__(self) -> None:
        self._data: list[tuple[float, int]] = []

    def __len__(self) -> int:
        return len(self._data)

    def is_empty(self) -> bool:
        return not self._data

    def push(self, key: float, item: int) -> None:
        """Insere (key, item) e restaura a propriedade de heap. O(log n)."""
        data = self._data
        data.append((key, item))
        self._sift_up(len(data) - 1)

    def pop_min(self) -> tuple[float, int]:
        """Remove e retorna o par de menor chave. O(log n)."""
        data = self._data
        if not data:
            raise IndexError("pop_min em heap vazia")
        top = data[0]
        last = data.pop()
        if data:
            data[0] = last
            self._sift_down(0)
        return top

    # --- operações internas ---------------------------------------------
    def _sift_up(self, i: int) -> None:
        data = self._data
        item = data[i]
        while i > 0:
            parent = (i - 1) >> 1
            if data[parent] <= item:
                break
            data[i] = data[parent]
            i = parent
        data[i] = item

    def _sift_down(self, i: int) -> None:
        data = self._data
        n = len(data)
        item = data[i]
        while True:
            left = 2 * i + 1
            right = left + 1
            smallest = i
            candidate = item
            if left < n and data[left] < candidate:
                smallest = left
                candidate = data[left]
            if right < n and data[right] < candidate:
                smallest = right
                candidate = data[right]
            if smallest == i:
                break
            data[i] = data[smallest]
            i = smallest
        data[i] = item
