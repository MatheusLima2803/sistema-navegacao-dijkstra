# Especificação Técnica — Sistema de Navegação Primitivo

**Disciplina:** Algoritmos e Estruturas de Dados 2 — INF/UFG — 2026/1
**Professor:** André L. Moura
**Integrantes (ordem alfabética):** Erick Vaz Magalhães · José Borges da Cruz · Matheus Marques Lima · Vítor Albert Gonçalves Pinheiro Avila
**Data:** 2026-06-07

> Este documento é a **especificação de engenharia** que guia a implementação. Ele complementa a *Documentação do Projeto.md* (visão de alto nível) detalhando estruturas de dados, assinaturas, formatos de arquivo, algoritmo e critérios de aceite por requisito.

---

## 1. Decisões de projeto

| Decisão | Escolha | Justificativa |
|---|---|---|
| Núcleo algorítmico | **Autoral** (lista de adjacência + heap mínima + Dijkstra implementados pela equipe) | É o objeto de avaliação de AED2. Bibliotecas (`NetworkX`/`OSMnx`) substituiriam a ED. |
| Representação do grafo | **Lista de adjacência** `list[list[Edge]]` indexada por id | `.poly` traz ids `0..n-1` sequenciais → acesso O(1), memória O(V+E), ótimo p/ grafos esparsos (RNF03/05). |
| Fila de prioridade | **Heap binária mínima** autoral + **lazy deletion** | Dá O((V+E)·log V) sem precisar de *decrease-key*. Atende RNF03/04. |
| Peso da aresta | Distância **euclidiana** entre coordenadas, calculada ao montar o grafo | Igual ao `calcDist` do código de referência; o peso não vem no arquivo. |
| Canvas | **PyQt6 + QPainter** (QWidget próprio) | Render fluido de ~10k arestas com pan/zoom/clique; mais rápido que Matplotlib embarcado. |
| Linguagem | **Python 3.12** | Conforme enunciado e documentação. |

**Dependências mínimas:** `PyQt6`. Tudo o mais (parse de `.poly`/`.osm`/`.txt`, grafo, heap, Dijkstra, geometria) é stdlib + código autoral. `PyInstaller` apenas para gerar o executável.

---

## 2. Arquitetura

Três camadas, baixo acoplamento, cada módulo com responsabilidade única e interface bem definida.

```
PF_<nomes>/
├── main.py                  # ponto de entrada: instancia QApplication + MainWindow
├── requirements.txt
├── README.md
└── src/
    ├── core/                # DOMÍNIO — sem dependência de PyQt
    │   ├── graph.py         # Vertex, Edge, Graph
    │   ├── min_heap.py      # MinHeap
    │   └── dijkstra.py      # dijkstra(...) -> DijkstraResult
    ├── loaders/             # ENTRADA/SAÍDA de grafos
    │   │                    #   (nomeado "loaders" e não "io" para não
    │   │                    #    sombrear o módulo `io` da stdlib no sys.path)
    │   ├── poly_loader.py   # load_poly(path) -> Graph
    │   ├── osm_loader.py    # load_osm(path)  -> Graph   (importa .osm direto)
    │   └── txt_loader.py    # load_txt(path)  -> Graph   (Origem,Destino,Peso)
    ├── ui/                  # APRESENTAÇÃO — PyQt6
    │   ├── main_window.py   # QMainWindow: barra de ferramentas + painel de stats
    │   ├── graph_canvas.py  # QWidget: render, pan/zoom, seleção, edição
    │   └── spatial_grid.py  # SpatialGrid: vértice mais próximo de um clique
    └── utils/
        ├── geometry.py      # distância euclidiana, bounding box
        ├── performance.py   # cronometragem e contadores
        └── clipboard.py     # copiar QPixmap do canvas p/ área de transferência
```

**Regra de dependência:** `core` não importa `ui` nem `io`. `ui` depende de `core` e `io`. Isso permite testar o algoritmo isoladamente (RNF08).

**Fluxo de dados:**
```
arquivo (.poly/.osm/.txt) → io.*_loader → Graph (core)
                                              │
usuário clica origem/destino (ui) ───────────┤
                                              ▼
                                core.dijkstra → DijkstraResult ──► ui.graph_canvas (desenha rota)
                                                              └──► ui.main_window (estatísticas)
```

---

## 3. Camada de domínio (`src/core`)

### 3.1 `graph.py`

```python
class Vertex:
    __slots__ = ("id", "x", "y")
    id: int          # 0..n-1
    x: float         # coordenada cartesiana (já em UTM/pixels, Y crescente p/ baixo)
    y: float

class Edge:
    __slots__ = ("to", "weight", "oneway")
    to: int          # id do vértice de destino
    weight: float    # distância euclidiana
    oneway: bool     # True = via de mão única (seta); False = mão dupla

class Graph:
    vertices: list[Vertex]          # indexado por id
    adj: list[list[Edge]]           # adj[u] = arestas saindo de u
    directed: bool                  # modo global do grafo

    def __init__(self, directed: bool = False) -> None
    def add_vertex(self, x: float, y: float) -> int        # retorna o novo id
    def add_edge(self, u: int, v: int, oneway: bool = False) -> None
        # peso = euclid(vertices[u], vertices[v]).
        # Se (not directed) e (not oneway): adiciona u->v e v->u.
        # Se oneway ou directed: adiciona só u->v.
    def remove_vertex(self, u: int) -> None                # remove vértice e arestas incidentes
    def remove_edge(self, u: int, v: int) -> None
    def num_vertices(self) -> int
    def num_edges(self) -> int                             # conta arestas dirigidas armazenadas

# Obs.: a busca do vértice mais próximo de um clique NÃO fica no Graph.
# Ela vive na UI, via ui.spatial_grid.SpatialGrid (seção 5.1), que o canvas possui e reconstrói após edições.
```

> **Remoção de vértice:** como ids são posicionais, `remove_vertex` marca o vértice como inativo (tombstone) em vez de reindexar, evitando invalidar arestas. Vértices inativos não são desenhados nem explorados. Alternativa aceitável p/ MVP: bloquear remoção de vértice e permitir só remoção de aresta (RF05 ainda pontua).

### 3.2 `min_heap.py`

Heap binária mínima sobre array, ordenada por chave `float`. **Autoral.**

```python
class MinHeap:
    _data: list[tuple[float, int]]      # (chave, vértice)

    def push(self, key: float, item: int) -> None   # O(log n) — sobe (sift-up)
    def pop_min(self) -> tuple[float, int]           # O(log n) — desce (sift-down)
    def is_empty(self) -> bool
    def __len__(self) -> int
```

Sem *decrease-key*: o Dijkstra usa **lazy deletion** (ver 3.3).

### 3.3 `dijkstra.py`

```python
class DijkstraResult:
    dist: float                 # custo total origem→destino (INF se sem caminho)
    path: list[int]             # sequência de ids origem→destino ([] se sem caminho)
    nodes_explored: int         # nº de vértices finalizados (pops válidos)
    elapsed_ms: float           # tempo de processamento

INF = float("inf")

def dijkstra(g: Graph, source: int, target: int) -> DijkstraResult
```

**Pseudocódigo (com lazy deletion e parada antecipada no alvo):**
```
dist[]    ← INF para todos;   dist[source] ← 0
prev[]    ← -1 para todos
visited[] ← False para todos
heap.push(0, source)
explored ← 0
enquanto heap não vazio:
    (d, u) ← heap.pop_min()
    se visited[u]: continue          # entrada obsoleta (lazy deletion)
    visited[u] ← True
    explored++
    se u == target: break            # parada antecipada
    para cada aresta (u → v, w) em adj[u]:
        se não visited[v] e dist[u] + w < dist[v]:
            dist[v] ← dist[u] + w
            prev[v] ← u
            heap.push(dist[v], v)     # duplicata; a antiga será descartada no pop
reconstruir path de target via prev[] (invertido)
medir elapsed com time.perf_counter()
```

Complexidade: **O((V+E)·log V)** tempo, **O(V)** memória extra.

---

## 4. Camada de E/S (`src/io`)

### 4.1 Formato `.poly` (oficial — saída de `ConverteMapaParaGrafo.c`)

Separador: **tab** (`\t`). Estrutura:

```
<nVertices>\t2\t0\t1            # cabeçalho: nº vértices, dimensões(=2), flag, flag
<id>\t<x>\t<y>                  # × nVertices  (ids 0..n-1, em ordem)
...
<nArestas>\t1                   # cabeçalho de arestas
<idAresta>\t<origem>\t<destino>\t0   # × nArestas
...
0                              # marcador de fim
```

- Coordenadas `x,y` já vêm cartesianas (UTM) e com **Y invertido** (origem no canto superior-esquerdo — direto p/ tela). Não há conversão a fazer.
- O peso da aresta **não** consta; calcular euclidiano ao chamar `add_edge`.
- Arestas do `.poly` representam segmentos de via → importar como **não-direcionado** (mão dupla) por padrão.

```python
def load_poly(path: str) -> Graph
    # 1ª linha: nVertices = int(tokens[0])
    # lê nVertices linhas "id x y" → add_vertex (validar id == índice esperado)
    # próxima linha: nArestas = int(tokens[0])
    # lê nArestas linhas "id orig dest 0" → add_edge(orig, dest, oneway=False)
    # ignora o "0" final. Robusto a linhas em branco.
```

### 4.2 Formato `.osm` (XML do OpenStreetMap)

Parsing autoral linha-a-linha (espelha `LeArqOSM_e_GeraArqPoly.c`), evitando dependência de OSMnx:
- `<node id= lat= lon=>` → coletar; converter (lat,lon) → UTM (zona 23S) via fórmula de Transversa de Mercator do código de referência.
- `<way>...<nd ref=.../>...</way>` → cada par consecutivo de nós vira uma aresta.
- Reduzir escala e inverter Y como no C (origem no topo-esquerda).

```python
def load_osm(path: str) -> Graph
def _latlon_to_utm(lat_deg, lon_deg) -> tuple[float, float]   # zona 23S, WGS84
```

> Prioridade baixa (passo 7). O `.poly` cobre RF01 com o arquivo oficial; `.osm` é bônus.

### 4.3 Formato `.txt` (lista simples)

```
A,B,10
A,C,15
B,D,8
```
Rótulos são mapeados a ids internos. Sem coordenadas → atribuir layout em grade/círculo para exibição. Bônus.

```python
def load_txt(path: str) -> Graph
```

---

## 5. Camada de apresentação (`src/ui`)

### 5.1 `spatial_grid.py`

Grade uniforme p/ achar o vértice mais próximo de um clique em ~O(1) (essencial p/ 10k nós; varredura linear seria lenta a cada movimento de mouse).

```python
class SpatialGrid:
    def __init__(self, vertices, cell_size): ...
    def nearest(self, x: float, y: float, max_dist: float) -> int | None
    def rebuild(self, vertices) -> None          # após edição
```

### 5.2 `graph_canvas.py` (QWidget)

Estado: `graph`, `SpatialGrid`, transform de visualização (`scale`, `offset_x/y`), `origin: int|None`, `destination: int|None`, `result: DijkstraResult|None`, flags `show_vertex_ids`, `show_edge_labels`, `edit_mode`.

**Transform mundo→tela:** `sx = x*scale + offset_x`, `sy = y*scale + offset_y`. Pan ajusta `offset`; zoom (roda do mouse) ajusta `scale` mantendo o ponto sob o cursor fixo.

`paintEvent`:
1. Arestas mão-dupla: lote único `painter.drawLines(QLineF[...])` (cor padrão — RNF01).
2. Arestas mão-única: linha + seta no destino (RNF02).
3. Rota (`result.path`): por cima, em **vermelho**, mais grossa (RF04).
4. Vértices (opcional/clipping por viewport): pontos; origem **verde**, destino **azul** (RF03/RNF01).
5. Rótulos só se `scale` acima de um limiar (RF02), para não pesar.

> **Otimização (RNF03/04):** desenhar apenas o que cai no viewport (culling pela bounding box visível) e rebaixar detalhe (sem vértices/rótulos) durante pan/zoom.

Eventos de mouse:
- **Clique esquerdo, modo navegação:** pega vértice mais próximo (≤ limiar). 1º vira origem (verde), 2º vira destino (azul). Clicar de novo na origem/destino **desfaz** a seleção (RF03 "fazer/desfazer").
- **Clique esquerdo, modo edição:** em vazio → `add_vertex`; sobre vértice A e depois B → `add_edge(A,B)`; `rebuild` da grade.
- **Clique direito, modo edição:** remove vértice/aresta sob o cursor.
- **Roda:** zoom centrado no cursor. **Arrastar (botão do meio ou espaço+arrasto):** pan.

`grab_pixmap() -> QPixmap` para RF08.

### 5.3 `main_window.py` (QMainWindow)

- **Barra de ferramentas/menu:** Abrir (.poly/.osm/.txt), Traçar Menor Caminho (`Ctrl+C` no print do Anexo I — usaremos botão + atalho), alternar Numerar vértices / Rotular arestas, alternar modo Edição, alternar Direcionado/Não-direcionado (RF06), Copiar imagem (RF08), Desfazer tudo, Sair.
- **Painel lateral de estatísticas (RF07):** Total de vértices, Total de arestas, Distância total (u.m.), Nós explorados, Tempo de processamento (ms), e a lista de vértices da rota (id, x, y) — como no Anexo I.
- Conecta sinais do canvas (origem/destino selecionados) → habilita "Traçar"; ao traçar, chama `dijkstra`, repassa `DijkstraResult` ao canvas e ao painel.

---

## 6. Utilitários (`src/utils`)

```python
# geometry.py
def euclid(ax, ay, bx, by) -> float            # sqrt((ax-bx)^2 + (ay-by)^2)
def bounding_box(vertices) -> (minx, miny, maxx, maxy)

# performance.py
class Timer:                                    # context manager → elapsed_ms
    def __enter__(self); def __exit__(...)

# clipboard.py
def copy_pixmap_to_clipboard(pixmap) -> None    # QApplication.clipboard().setPixmap(...)
```

---

## 7. Rastreabilidade — Requisitos → Implementação → Aceite

| Req | Onde | Critério de aceite | Pts |
|---|---|---|---:|
| **RF01** Importar mapas | `io.poly_loader` (+osm/txt) | Abre `Campus2UFG&Regiao.poly` e desenha o grafo | 0,75 |
| **RF02** Enumerar vértices / rotular arestas | `graph_canvas` toggles | Botões mostram ids dos vértices e pesos das arestas | 0,20 |
| **RF03** Selecionar/desfazer origem e destino | `graph_canvas` mouse | Origem verde, destino azul; clicar de novo desfaz | 0,20 |
| **RF04** Calcular e exibir menor caminho | `core.dijkstra` + render | Rota em vermelho entre s e t; coerente com pesos | 1,50 |
| **RF05** Criar/editar grafo | `graph_canvas` edit + `Graph` | Add/remove vértice e aresta via mouse | 1,10 |
| **RF06** Direcionado/não-direcionado | `Graph.directed` + `Edge.oneway` | Alternar modo; mão única só permite um sentido | 1,30 |
| **RF07** Estatísticas | `main_window` painel + `performance` | Mostra tempo, nós explorados, custo total | 0,75 |
| **RF08** Copiar imagem | `utils.clipboard` | Imagem do grafo vai p/ área de transferência | 0,20 |
| **RNF01** Cores distintas | render | Vértices e arestas com cores diferentes | 0,25 |
| **RNF02** Mão única × dupla | render seta | Aresta dirigida com seta; dupla sem | 0,25 |
| **RNF03** Otimizado p/ grafos grandes | lista adj + heap + culling | Abre 10k nós sem travar | 0,25 |
| **RNF04** < 2 s p/ ~500 nós | dijkstra + parada antecipada | Tempo medido < 2 s | 0,25 |
| **RNF05** Memória eficiente | `__slots__`, list adj | Sem estruturas O(V²) | 0,25 |
| **RNF06** Interface intuitiva | `main_window` | Fluxo abrir→clicar→traçar claro | 0,25 |
| **RNF07** Windows/Linux | Python+PyQt6 puro | Roda nos dois SOs | 0,25 |
| **RNF08** Código modular/documentado | arquitetura em camadas | Módulos isolados, docstrings | 0,25 |

---

## 8. Ordem de construção (priorizada por pontos — entrega hoje)

1. **core**: `graph.py` → `min_heap.py` → `dijkstra.py` *(RF04 + RNF03/04/05 — 2,50)*
2. **io**: `poly_loader.py` *(RF01 — 0,75)*
3. **ui base**: `graph_canvas` render + pan/zoom + `main_window` abrir arquivo *(RNF01 — 0,25)*
4. **fluxo principal**: selecionar origem/destino + traçar Dijkstra em vermelho *(RF03 — 0,20)*
5. **estatísticas** *(RF07 — 0,75)*
6. **RF06** direcionado/mão única + seta *(RF06+RNF02 — 1,55)*
7. **RF05** edição add/remove *(1,10)*
8. **RF02 rótulos + RF08 clipboard** *(0,40)*
9. **osm/txt loaders** (bônus RF01) + **README** + **PyInstaller**

Passos 1–4 entregam ~3,70 pts ponta-a-ponta; cada passo seguinte é incremental e independente.

---

## 9. Instalação e execução (resumo p/ README)

```bash
pip install -r requirements.txt        # PyQt6
python main.py                         # abre a aplicação
pyinstaller --onefile --windowed main.py   # gera o executável (artefato d do enunciado)
```

Entrega: compactar tudo como `PF_<primeiroNome><ultimoNome>.zip` e postar no SIGAA.

---

## 10. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Render de 10k arestas lento no QPainter | `drawLines` em lote + culling de viewport + rebaixar detalhe durante interação |
| `nearest_vertex` lento a cada mousemove | `SpatialGrid` (busca por célula) em vez de varredura linear |
| Remoção de vértice invalida ids | tombstone (marcar inativo) em vez de reindexar |
| Tempo de entrega (hoje) | seguir a ordem priorizada; passos 1–4 já são uma entrega defensável |
| `.osm` consome tempo | tratar como bônus; `.poly` oficial cobre RF01 |
```
