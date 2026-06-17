# Sistema de Navegação Dijkstra

Aplicação gráfica para cálculo de rotas em mapas reais utilizando grafos, heap mínima e o algoritmo de Dijkstra.

Desenvolvido em Python como projeto final da disciplina Algoritmos e Estruturas de Dados II da Universidade Federal de Goiás (UFG).

---

## Demonstração

### Tela Principal

![Tela Principal](images/tela-principal.png)

### Menor Caminho Encontrado

![Rota Calculada](images/rota-calculada.png)

### Visualização do Grafo

![Zoom no Mapa](images/zoom-mapa.png)

## Funcionalidades

- Carregamento de mapas reais
- Importação de arquivos `.poly`, `.osm`, `.xml` e `.txt`
- Cálculo do menor caminho entre dois pontos
- Visualização gráfica interativa
- Zoom e navegação no mapa
- Grafos direcionados e não direcionados
- Criação e remoção de vértices e arestas
- Exibição de métricas de desempenho

---

## Tecnologias e Conceitos

### Linguagens e Ferramentas

- Python 3
- PyQt6
- OpenStreetMap (OSM)

### Estruturas de Dados

- Lista de adjacência
- Heap mínima

### Algoritmos

- Algoritmo de Dijkstra
- Busca de menor caminho em grafos

---

## Arquitetura

```text
src/
├── core/       # Grafo, Heap Mínima e Dijkstra
├── loaders/    # Leitura de arquivos
├── ui/         # Interface gráfica
└── utils/      # Funções auxiliares
```

O projeto segue uma arquitetura modular com separação entre:

- Interface gráfica
- Estruturas de dados
- Algoritmos
- Carregamento de arquivos

---

## Instalação

Clone o repositório:

```bash
git clone https://github.com/MatheusLima2803/sistema-navegacao-dijkstra.git
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## Execução

```bash
python main.py
```

---

## Formatos Suportados

| Formato | Descrição |
|----------|-----------|
| `.poly` | Grafo gerado a partir de mapas |
| `.osm` / `.xml` | Dados do OpenStreetMap |
| `.txt` | Lista simples de arestas |

---

## Desempenho

Resultados obtidos durante os testes:

| Cenário | Tempo |
|----------|--------|
| ~500 vértices | < 1 ms |
| 10.000 vértices | ~17 ms |

O projeto atende com ampla margem o requisito acadêmico de resposta inferior a 2 segundos.

---

## Equipe

- Erick Vaz Magalhães
- José Borges da Cruz
- Matheus Marques Lima
- Vítor Albert Gonçalves Pinheiro Avila

---

## Contexto Acadêmico

Projeto Final — Algoritmos e Estruturas de Dados II

Instituto de Informática (INF) — Universidade Federal de Goiás (UFG)

Professor: André L. Moura

---

## Licença

MIT License