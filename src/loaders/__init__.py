"""
Leitores de grafos a partir de arquivos.

Nomeado `loaders` (e não `io`) para não sombrear o módulo `io` da
biblioteca padrão quando `src/` está no sys.path.
"""
from .poly_loader import load_poly
from .osm_loader import load_osm
from .txt_loader import load_txt

__all__ = ["load_poly", "load_osm", "load_txt", "load_any"]


def load_any(path: str):
    """Carrega um grafo escolhendo o leitor pela extensão do arquivo."""
    lower = path.lower()
    if lower.endswith(".poly"):
        return load_poly(path)
    if lower.endswith(".osm") or lower.endswith(".xml"):
        return load_osm(path)
    if lower.endswith(".txt"):
        return load_txt(path)
    raise ValueError(f"Extensão não suportada: {path}")
