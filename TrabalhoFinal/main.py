"""
Sistema de Navegação Primitivo — ponto de entrada.

Disciplina: Algoritmos e Estruturas de Dados 2 — INF/UFG — 2026/1
Encontra o menor caminho entre dois pontos (Dijkstra) sobre grafos de mapas.

Execução:
    python main.py
"""
import os
import sys

# Garante que o diretório do projeto esteja no sys.path (resolve o pacote `src`),
# inclusive quando empacotado pelo PyInstaller.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication  # noqa: E402

from src.ui.main_window import MainWindow  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
