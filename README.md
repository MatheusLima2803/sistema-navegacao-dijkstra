# Sistema de Navegação Primitivo

Aplicação gráfica que encontra o **menor caminho entre dois pontos** em grafos
de mapas reais, usando o **algoritmo de Dijkstra** com estruturas de dados
implementadas pela equipe (lista de adjacência + heap mínima).

> Projeto Final — Algoritmos e Estruturas de Dados 2 — INF/UFG — 2026/1
> Prof. André L. Moura

**Integrantes (ordem alfabética):** Erick Vaz Magalhães · José Borges da Cruz ·
Matheus Marques Lima · Vítor Albert Gonçalves Pinheiro Avila

---

## Pré-requisitos

- **Python 3.12+** (testado também em 3.14)
- Sistema operacional **Windows** ou **Linux**
- Conexão com a internet apenas para instalar as dependências

## Instalação

```bash
pip install -r requirements.txt
```

Única dependência externa: **PyQt6**. Todo o núcleo (grafo, heap, Dijkstra,
leitura de `.poly`/`.osm`/`.txt`) é código próprio, sem bibliotecas de grafos.

## Execução

```bash
python main.py
```

## Geração do executável (opcional)

```bash
pyinstaller --onefile --windowed main.py
```

O executável é gerado em `dist/`.

---

## Como usar

1. **Abrir mapa** (`Ctrl+O`): selecione um arquivo `.poly`, `.osm`/`.xml` ou
   `.txt`. Use os arquivos oficiais de `Campus2UFG&Regiao.zip` (SIGAA).
2. **Navegar:** roda do mouse dá zoom (centrado no cursor); arrastar com o botão
   esquerdo faz *pan*; "Ajustar à tela" reenquadra o grafo.
3. **Selecionar origem e destino:** clique em um vértice (fica **verde** =
   origem) e em outro (**azul** = destino). Clicar novamente sobre eles desfaz a
   seleção.
4. **Traçar menor caminho** (`Ctrl+R`): a rota aparece em **vermelho** e o painel
   lateral mostra distância total, nós explorados e tempo de processamento.
5. **Exibição:** "Numerar vértices" e "Rotular arestas" mostram ids e pesos
   (aparecem ao aproximar o zoom).
6. **Tipos de grafo:** "Grafo direcionado" e "Nova aresta mão única" controlam o
   sentido; vias de mão única são desenhadas com **seta**, mão dupla com linha.
7. **Modo edição:** clique em área vazia cria vértice; clique em dois vértices
   cria aresta; **botão direito** remove vértice.
8. **Copiar imagem** (`Ctrl+C`): copia a visualização atual para a área de
   transferência.

---

## Formatos de entrada

| Formato | Descrição |
|---|---|
| `.poly` | Saída de `ConverteMapaParaGrafo.c`: vértices `id x y` (coordenadas cartesianas) + arestas. Peso = distância euclidiana. |
| `.osm` / `.xml` | OpenStreetMap. Converte lat/lon → UTM (zona 23S) e monta o grafo direto. |
| `.txt` | Lista simples `Origem,Destino,Peso` (um por linha). |

---

## Arquitetura

Três camadas com baixo acoplamento (`core` não depende de `ui`/`loaders`):

```
main.py
src/
├── core/      grafo, heap mínima e Dijkstra (autorais)
├── loaders/   leitura de .poly / .osm / .txt
├── ui/        janela, canvas (QPainter), índice espacial
└── utils/     geometria, desempenho, área de transferência
```

Detalhes completos em [`docs/ESPECIFICACAO_TECNICA.md`](docs/ESPECIFICACAO_TECNICA.md).

## Desempenho

Grafo em grade de 10.000 vértices / ~39.600 arestas dirigidas: Dijkstra
ponta-a-ponta em **~17 ms**. Grafo de ~500 nós: **< 1 ms** (requisito: < 2 s).
```
