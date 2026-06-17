"""Medição de desempenho (RF07)."""
from __future__ import annotations

from time import perf_counter


class Timer:
    """Context manager que mede tempo decorrido em milissegundos.

    Uso:
        with Timer() as t:
            ...
        print(t.elapsed_ms)
    """

    __slots__ = ("_start", "elapsed_ms")

    def __init__(self) -> None:
        self._start = 0.0
        self.elapsed_ms = 0.0

    def __enter__(self) -> "Timer":
        self._start = perf_counter()
        return self

    def __exit__(self, *exc) -> None:
        self.elapsed_ms = (perf_counter() - self._start) * 1000.0
