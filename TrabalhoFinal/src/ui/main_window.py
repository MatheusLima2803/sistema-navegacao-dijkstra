"""
Janela principal da aplicação.

Reúne a barra de ferramentas, o canvas do grafo e o painel lateral de
estatísticas (RF07). Orquestra a abertura de arquivos (RF01), o disparo do
Dijkstra (RF04), os modos de exibição/edição e a cópia da imagem (RF08).
"""
from __future__ import annotations

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow, QFileDialog, QDockWidget, QTextEdit, QToolBar,
    QMessageBox, QWidget, QVBoxLayout, QLabel, QCheckBox,
)

from src.loaders import load_any
from src.utils.clipboard import copy_pixmap_to_clipboard
from .graph_canvas import GraphCanvas


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Sistema de Navegação Primitivo — Dijkstra (AED2/UFG)")
        self.resize(1200, 760)

        self.canvas = GraphCanvas(self)
        self.setCentralWidget(self.canvas)

        self._build_toolbar()
        self._build_stats_panel()

        self.canvas.statusMessage.connect(self.statusBar().showMessage)
        self.canvas.selectionChanged.connect(self._refresh_stats)
        self.canvas.graphChanged.connect(self._refresh_stats)
        self._refresh_stats()

    # ------------------------------------------------------------------
    def _build_toolbar(self) -> None:
        tb = QToolBar("Ferramentas")
        tb.setMovable(False)
        self.addToolBar(tb)

        act_open = QAction("Abrir mapa", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.triggered.connect(self.open_file)
        tb.addAction(act_open)

        act_run = QAction("Traçar menor caminho", self)
        act_run.setShortcut("Ctrl+R")
        act_run.triggered.connect(self.trace_path)
        tb.addAction(act_run)

        tb.addSeparator()

        self.chk_ids = QCheckBox("Numerar vértices")
        self.chk_ids.toggled.connect(self._toggle_ids)
        tb.addWidget(self.chk_ids)

        self.chk_labels = QCheckBox("Rotular arestas")
        self.chk_labels.toggled.connect(self._toggle_labels)
        tb.addWidget(self.chk_labels)

        tb.addSeparator()

        self.chk_edit = QCheckBox("Modo edição")
        self.chk_edit.toggled.connect(self._toggle_edit)
        tb.addWidget(self.chk_edit)

        self.chk_oneway = QCheckBox("Nova aresta mão única")
        self.chk_oneway.toggled.connect(self._toggle_oneway)
        tb.addWidget(self.chk_oneway)

        self.chk_directed = QCheckBox("Grafo direcionado")
        self.chk_directed.toggled.connect(self._toggle_directed)
        tb.addWidget(self.chk_directed)

        tb.addSeparator()

        act_copy = QAction("Copiar imagem", self)
        act_copy.setShortcut("Ctrl+C")
        act_copy.triggered.connect(self.copy_image)
        tb.addAction(act_copy)

        act_clear = QAction("Desfazer tudo", self)
        act_clear.triggered.connect(self.canvas.clear_all)
        tb.addAction(act_clear)

        act_fit = QAction("Ajustar à tela", self)
        act_fit.triggered.connect(lambda: (self.canvas.fit_to_view(), self.canvas.update()))
        tb.addAction(act_fit)

    def _build_stats_panel(self) -> None:
        dock = QDockWidget("Estatísticas", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea |
                             Qt.DockWidgetArea.RightDockWidgetArea)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)

        self.lbl_summary = QLabel()
        self.lbl_summary.setWordWrap(True)
        self.lbl_summary.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.lbl_summary)

        self.txt_route = QTextEdit()
        self.txt_route.setReadOnly(True)
        layout.addWidget(QLabel("Rota (id, x, y):"))
        layout.addWidget(self.txt_route)

        dock.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------
    def open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir mapa/grafo", "",
            "Grafos (*.poly *.osm *.xml *.txt);;Todos (*.*)")
        if not path:
            return
        try:
            graph = load_any(path)
        except Exception as exc:  # erro de leitura é informado ao usuário
            QMessageBox.critical(self, "Erro ao abrir", str(exc))
            return
        self.chk_directed.setChecked(graph.directed)
        self.canvas.set_graph(graph)
        self.statusBar().showMessage(
            f"{os.path.basename(path)} — {graph.num_vertices()} vértices, "
            f"{graph.num_edges()} arestas")

    def trace_path(self) -> None:
        result = self.canvas.run_dijkstra()
        if result is None:
            return
        if not result.found:
            QMessageBox.information(self, "Sem caminho",
                                    "Não há caminho entre origem e destino.")
        self._refresh_stats()

    def copy_image(self) -> None:
        copy_pixmap_to_clipboard(self.canvas.to_pixmap())
        self.statusBar().showMessage("Imagem copiada para a área de transferência.")

    # --- toggles -------------------------------------------------------
    def _toggle_ids(self, on: bool) -> None:
        self.canvas.show_vertex_ids = on
        self.canvas.update()

    def _toggle_labels(self, on: bool) -> None:
        self.canvas.show_edge_labels = on
        self.canvas.update()

    def _toggle_edit(self, on: bool) -> None:
        self.canvas.edit_mode = on
        self.canvas._pending_edge = None
        self.statusBar().showMessage(
            "Modo edição: clique vazio cria vértice; dois vértices criam aresta; "
            "botão direito remove." if on else "Modo navegação.")

    def _toggle_oneway(self, on: bool) -> None:
        self.canvas.new_edge_oneway = on

    def _toggle_directed(self, on: bool) -> None:
        self.canvas.graph.directed = on

    # ------------------------------------------------------------------
    def _refresh_stats(self) -> None:
        g = self.canvas.graph
        origin = self.canvas.origin
        dest = self.canvas.destination
        res = self.canvas.result

        lines = [
            f"<b>Total de vértices:</b> {g.num_vertices()}",
            f"<b>Total de arestas:</b> {g.num_edges()}",
            f"<b>Origem:</b> {origin if origin is not None else '—'}",
            f"<b>Destino:</b> {dest if dest is not None else '—'}",
        ]
        if res is not None:
            if res.found:
                lines += [
                    "<hr>",
                    f"<b>Distância total:</b> {res.dist:.2f} u.m.",
                    f"<b>Nós explorados:</b> {res.nodes_explored}",
                    f"<b>Tempo:</b> {res.elapsed_ms:.2f} ms",
                    f"<b>Vértices na rota:</b> {len(res.path)}",
                ]
            else:
                lines += ["<hr>", "<b>Sem caminho entre origem e destino.</b>"]
        self.lbl_summary.setText("<br>".join(lines))

        if res is not None and res.found:
            rows = []
            for vid in res.path:
                v = g.vertices[vid]
                rows.append(f"{vid} (x={v.x:.1f}, y={v.y:.1f})")
            self.txt_route.setPlainText("\n".join(rows))
        else:
            self.txt_route.clear()
