"""
Lectura y escritura de los archivos JSON del sistema.
"""

import json
import os
from pathlib import Path


class GestorDatos:
    """Guarda y carga listas de diccionarios en archivos JSON dentro de una carpeta."""

    def __init__(self, carpeta: Path):
        self._carpeta = Path(carpeta)
        self._carpeta.mkdir(parents=True, exist_ok=True)

    def _ruta(self, nombre: str) -> Path:
        return self._carpeta / f"{nombre}.json"

    def existe(self, nombre: str) -> bool:
        return self._ruta(nombre).exists()

    def cargar(self, nombre: str) -> list[dict]:
        with open(self._ruta(nombre), encoding="utf-8") as archivo:
            return json.load(archivo)

    def guardar(self, nombre: str, datos: list[dict]) -> None:
        # Se escribe primero en un archivo temporal para no dañar el original si algo falla
        temporal = self._ruta(nombre).with_suffix(".tmp")
        with open(temporal, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
        os.replace(temporal, self._ruta(nombre))

    def apartar_corrupto(self, nombre: str) -> None:
        """Renombra un archivo corrupto para no perderlo, y así poder crear uno nuevo."""
        os.replace(self._ruta(nombre), self._ruta(nombre).with_suffix(".corrupto"))
