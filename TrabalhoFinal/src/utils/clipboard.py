"""Cópia de imagem para a área de transferência (RF08)."""
from __future__ import annotations


def copy_pixmap_to_clipboard(pixmap) -> None:
    """Copia um QPixmap para a área de transferência do sistema."""
    from PyQt6.QtWidgets import QApplication

    QApplication.clipboard().setPixmap(pixmap)
