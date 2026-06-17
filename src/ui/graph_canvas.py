"""
Canvas de desenho do grafo (QWidget + QPainter).

Responsabilidades:
  - renderizar vértices/arestas com culling de viewport (RNF03/04);
  - pan (arrastar) e zoom (roda do mouse) centrado no cursor;
  - selecionar/desfazer origem (verde) e destino (azul) — RF03;
  - destacar a rota do menor caminho em vermelho — RF04;
  - modo de edição: adicionar/remover vértices e arestas com o mouse — RF05;
  - diferenciar via de mão única (seta) de mão dupla (linha) — RNF02;
  - alternar numeração de vértices e rótulos de peso — RF02;
  - fornecer um QPixmap do conteúdo para cópia (RF08).
"""
from __future__ import annotations

from math import atan2, cos, sin, pi

from PyQt6.QtCore import Qt, QPointF, QLineF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QPolygonF, QFont
from PyQt6.QtWidgets import QWidget

from src.core import Graph, dijkstra, DijkstraResult
from .spatial_grid import SpatialGrid

# Cores (RNF01: vértices e arestas em cores distintas)
COL_BG = QColor(255, 255, 255)
COL_EDGE = QColor(60, 90, 200)        # arestas — azul
COL_EDGE_ONEWAY = QColor(150, 90, 200)  # mão única — roxo
COL_VERTEX = QColor(40, 40, 40)       # vértices — quase preto
COL_PATH = QColor(220, 30, 30)        # rota — vermelho
COL_ORIGIN = QColor(20, 160, 40)      # origem — verde
COL_DEST = QColor(30, 80, 230)        # destino — azul forte
COL_PENDING = QColor(230, 140, 0)     # vértice pendente p/ nova aresta

PICK_RADIUS_PX = 12     # raio de clique (pixels)
LABEL_MIN_SCALE = 0.6   # só desenha rótulos acima desta escala
VERTEX_MIN_SCALE = 0.25  # só desenha pontos de vértice acima desta escala
DRAG_THRESHOLD = 4      # pixels para distinguir clique de arraste


class GraphCanvas(QWidget):
    selectionChanged = pyqtSignal()   # origem/destino mudaram
    graphChanged = pyqtSignal()       # estrutura do grafo mudou
    statusMessage = pyqtSignal(str)   # mensagem para a barra de status

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.graph = Graph(directed=False)
        self.grid = SpatialGrid(self.graph.vertices)

        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0

        self.origin: int | None = None
        self.destination: int | None = None
        self.result: DijkstraResult | None = None

        self.show_vertex_ids = False
        self.show_edge_labels = False
        self.edit_mode = False
        self.new_edge_oneway = False
        self._pending_edge: int | None = None

        self._panning = False
        self._press_pos: QPointF | None = None
        self._moved = False
        self._last = QPointF(0, 0)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def set_graph(self, graph: Graph) -> None:
        self.graph = graph
        self.grid = SpatialGrid(graph.vertices)
        self.origin = self.destination = None
        self.result = None
        self._pending_edge = None
        self.fit_to_view()
        self.selectionChanged.emit()
        self.graphChanged.emit()
        self.update()

    def clear_all(self) -> None:
        self.origin = self.destination = None
        self.result = None
        self._pending_edge = None
        self.selectionChanged.emit()
        self.update()

    def run_dijkstra(self) -> DijkstraResult | None:
        if self.origin is None or self.destination is None:
            self.statusMessage.emit("Selecione origem e destino primeiro.")
            return None
        self.result = dijkstra(self.graph, self.origin, self.destination)
        self.update()
        return self.result

    def to_pixmap(self):
        return self.grab()

    # ------------------------------------------------------------------
    # Transformações mundo <-> tela
    # ------------------------------------------------------------------
    def _to_screen(self, x: float, y: float) -> QPointF:
        return QPointF(x * self.scale + self.offset_x,
                       y * self.scale + self.offset_y)

    def _to_world(self, sx: float, sy: float) -> tuple[float, float]:
        return ((sx - self.offset_x) / self.scale,
                (sy - self.offset_y) / self.scale)

    def fit_to_view(self) -> None:
        from src.utils import bounding_box
        min_x, min_y, max_x, max_y = bounding_box(self.graph.vertices)
        w = max(max_x - min_x, 1e-9)
        h = max(max_y - min_y, 1e-9)
        margin = 0.05
        vw = max(self.width(), 1)
        vh = max(self.height(), 1)
        self.scale = min(vw / w, vh / h) * (1 - 2 * margin)
        self.offset_x = (vw - w * self.scale) / 2 - min_x * self.scale
        self.offset_y = (vh - h * self.scale) / 2 - min_y * self.scale

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------
    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), COL_BG)

        g = self.graph
        if not g.vertices:
            painter.setPen(QColor(120, 120, 120))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                             "Abra um arquivo .poly / .osm / .txt para começar")
            painter.end()
            return

        # retângulo visível em coordenadas-mundo (culling)
        wx0, wy0 = self._to_world(0, 0)
        wx1, wy1 = self._to_world(self.width(), self.height())
        vis_min_x, vis_max_x = min(wx0, wx1), max(wx0, wx1)
        vis_min_y, vis_max_y = min(wy0, wy1), max(wy0, wy1)

        def visible(a, b) -> bool:
            if max(a.x, b.x) < vis_min_x or min(a.x, b.x) > vis_max_x:
                return False
            if max(a.y, b.y) < vis_min_y or min(a.y, b.y) > vis_max_y:
                return False
            return True

        verts = g.vertices
        two_way_lines: list[QLineF] = []

        # --- arestas ----------------------------------------------------
        pen_one = QPen(COL_EDGE_ONEWAY, 1.2)
        painter.setPen(pen_one)
        for u in range(len(g.adj)):
            vu = verts[u]
            if not vu.active:
                continue
            for e in g.adj[u]:
                vv = verts[e.to]
                if not vv.active or not visible(vu, vv):
                    continue
                if e.oneway:
                    self._draw_arrow(painter, vu, vv)
                elif u < e.to:  # mão dupla guardada nos dois sentidos: desenha 1x
                    two_way_lines.append(QLineF(self._to_screen(vu.x, vu.y),
                                                self._to_screen(vv.x, vv.y)))
        if two_way_lines:
            painter.setPen(QPen(COL_EDGE, 1.0))
            painter.drawLines(two_way_lines)

        # --- rótulos de peso (RF02) ------------------------------------
        if self.show_edge_labels and self.scale >= LABEL_MIN_SCALE:
            painter.setPen(QColor(90, 90, 90))
            painter.setFont(QFont("Arial", 7))
            for u in range(len(g.adj)):
                vu = verts[u]
                if not vu.active:
                    continue
                for e in g.adj[u]:
                    if e.oneway or u < e.to:
                        vv = verts[e.to]
                        if vv.active and visible(vu, vv):
                            mid = self._to_screen((vu.x + vv.x) / 2,
                                                  (vu.y + vv.y) / 2)
                            painter.drawText(mid, f"{e.weight:.0f}")

        # --- rota do menor caminho (RF04) ------------------------------
        if self.result and self.result.found:
            pen_path = QPen(COL_PATH, 3.0)
            pen_path.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_path)
            path = self.result.path
            lines = []
            for i in range(len(path) - 1):
                a, b = verts[path[i]], verts[path[i + 1]]
                lines.append(QLineF(self._to_screen(a.x, a.y),
                                    self._to_screen(b.x, b.y)))
            painter.drawLines(lines)

        # --- vértices ---------------------------------------------------
        if self.scale >= VERTEX_MIN_SCALE:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(COL_VERTEX)
            r = 2.0
            for v in verts:
                if not v.active:
                    continue
                if not (vis_min_x <= v.x <= vis_max_x and
                        vis_min_y <= v.y <= vis_max_y):
                    continue
                p = self._to_screen(v.x, v.y)
                painter.drawEllipse(p, r, r)

            if self.show_vertex_ids and self.scale >= LABEL_MIN_SCALE:
                painter.setPen(QColor(20, 20, 20))
                painter.setFont(QFont("Arial", 7))
                for v in verts:
                    if v.active and vis_min_x <= v.x <= vis_max_x and \
                            vis_min_y <= v.y <= vis_max_y:
                        p = self._to_screen(v.x, v.y)
                        painter.drawText(QPointF(p.x() + 4, p.y() - 4), str(v.id))

        # --- marcadores especiais --------------------------------------
        self._draw_marker(painter, self._pending_edge, COL_PENDING, 6)
        self._draw_marker(painter, self.origin, COL_ORIGIN, 7)
        self._draw_marker(painter, self.destination, COL_DEST, 7)

        painter.end()

    def _draw_marker(self, painter, vid, color, radius) -> None:
        if vid is None or vid >= len(self.graph.vertices):
            return
        v = self.graph.vertices[vid]
        if not v.active:
            return
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(self._to_screen(v.x, v.y), radius, radius)

    def _draw_arrow(self, painter, vu, vv) -> None:
        p1 = self._to_screen(vu.x, vu.y)
        p2 = self._to_screen(vv.x, vv.y)
        painter.drawLine(p1, p2)
        # cabeça da seta um pouco antes do destino
        ang = atan2(p2.y() - p1.y(), p2.x() - p1.x())
        size = 7.0
        tip = QPointF(p2.x() - 6 * cos(ang), p2.y() - 6 * sin(ang))
        left = QPointF(tip.x() - size * cos(ang - pi / 7),
                       tip.y() - size * sin(ang - pi / 7))
        right = QPointF(tip.x() - size * cos(ang + pi / 7),
                        tip.y() - size * sin(ang + pi / 7))
        painter.drawPolyline(QPolygonF([left, tip, right]))

    # ------------------------------------------------------------------
    # Interação
    # ------------------------------------------------------------------
    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y()
        if delta == 0:
            return
        factor = 1.15 if delta > 0 else 1 / 1.15
        pos = event.position()
        wx, wy = self._to_world(pos.x(), pos.y())
        self.scale *= factor
        # mantém o ponto sob o cursor fixo
        self.offset_x = pos.x() - wx * self.scale
        self.offset_y = pos.y() - wy * self.scale
        self.update()

    def mousePressEvent(self, event) -> None:
        self._press_pos = event.position()
        self._last = event.position()
        self._moved = False
        if event.button() in (Qt.MouseButton.MiddleButton,):
            self._panning = True
        elif event.button() == Qt.MouseButton.LeftButton and not self.edit_mode:
            # em modo navegação, arrasto com botão esquerdo faz pan;
            # clique sem arraste seleciona (decidido no release)
            self._panning = True

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        if self._press_pos is not None:
            if (abs(pos.x() - self._press_pos.x()) > DRAG_THRESHOLD or
                    abs(pos.y() - self._press_pos.y()) > DRAG_THRESHOLD):
                self._moved = True
        if self._panning and self._press_pos is not None and self._moved:
            self.offset_x += pos.x() - self._last.x()
            self.offset_y += pos.y() - self._last.y()
            self.update()
        self._last = pos
        wx, wy = self._to_world(pos.x(), pos.y())
        self.statusMessage.emit(f"Posição: ({wx:.0f}, {wy:.0f})")

    def mouseReleaseEvent(self, event) -> None:
        pos = event.position()
        was_pan = self._panning
        self._panning = False
        if self._moved and was_pan:
            return  # foi um arraste (pan), não um clique

        if event.button() == Qt.MouseButton.LeftButton:
            if self.edit_mode:
                self._edit_click(pos)
            else:
                self._select_click(pos)
        elif event.button() == Qt.MouseButton.RightButton and self.edit_mode:
            self._delete_click(pos)

    # --- ações de clique ----------------------------------------------
    def _pick(self, pos) -> int | None:
        wx, wy = self._to_world(pos.x(), pos.y())
        return self.grid.nearest(wx, wy, PICK_RADIUS_PX / self.scale)

    def _select_click(self, pos) -> None:
        vid = self._pick(pos)
        if vid is None:
            return
        if vid == self.origin:                 # desfazer origem
            self.origin = None
        elif vid == self.destination:          # desfazer destino
            self.destination = None
        elif self.origin is None:
            self.origin = vid
        elif self.destination is None:
            self.destination = vid
        else:                                  # recomeça seleção
            self.origin = vid
            self.destination = None
            self.result = None
        self.selectionChanged.emit()
        self.update()

    def _edit_click(self, pos) -> None:
        vid = self._pick(pos)
        if vid is not None:
            if self._pending_edge is None:
                self._pending_edge = vid
                self.statusMessage.emit(f"Vértice {vid} selecionado — clique em outro para criar aresta.")
            else:
                if self._pending_edge != vid:
                    self.graph.add_edge(self._pending_edge, vid,
                                        oneway=self.new_edge_oneway)
                    self.statusMessage.emit(f"Aresta {self._pending_edge}→{vid} criada.")
                self._pending_edge = None
                self.graphChanged.emit()
        else:
            wx, wy = self._to_world(pos.x(), pos.y())
            new_id = self.graph.add_vertex(wx, wy)
            self.grid.rebuild(self.graph.vertices)
            self.statusMessage.emit(f"Vértice {new_id} criado.")
            self.graphChanged.emit()
        self.update()

    def _delete_click(self, pos) -> None:
        vid = self._pick(pos)
        if vid is None:
            return
        self.graph.remove_vertex(vid)
        self.grid.rebuild(self.graph.vertices)
        if self.origin == vid:
            self.origin = None
        if self.destination == vid:
            self.destination = None
        self.result = None
        self.statusMessage.emit(f"Vértice {vid} removido.")
        self.selectionChanged.emit()
        self.graphChanged.emit()
        self.update()
