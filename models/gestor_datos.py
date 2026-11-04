"""
Lectura y escritura de los archivos JSON del sistema.
"""

# json es el formato en que se guardan los datos: texto con claves y valores, fácil de leer y de editar.
import json
# os sirve para trabajar con archivos del sistema; aquí, para reemplazar un archivo de forma segura.
import os
# Path representa una carpeta o un archivo, y evita errores con las barras de las rutas.
from pathlib import Path


# Su única tarea es leer y escribir los archivos JSON. No sabe nada de ventas ni de clientes: solo guarda y entrega listas.
class GestorDatos:
    """Guarda y carga listas de diccionarios en archivos JSON dentro de una carpeta."""

    # Recibe la carpeta donde se guardarán los archivos.
    def __init__(self, carpeta: Path):
        self._carpeta = Path(carpeta)
        # Crea la carpeta si no existe; si ya existe no hace nada (exist_ok=True).
        self._carpeta.mkdir(parents=True, exist_ok=True)

    # Arma la ruta completa del archivo: carpeta + nombre + .json.
    def _ruta(self, nombre: str) -> Path:
        return self._carpeta / f"{nombre}.json"

    # Responde True si el archivo ya existe.
    def existe(self, nombre: str) -> bool:
        return self._ruta(nombre).exists()

    # Lee un archivo y lo convierte en una lista de diccionarios. Si el contenido está dañado, json lanza un error.
    def cargar(self, nombre: str) -> list[dict]:
        # 'with open' abre el archivo y lo cierra solo al terminar, incluso si ocurre un error. utf-8 permite tildes y ñ.
        with open(self._ruta(nombre), encoding="utf-8") as archivo:
            return json.load(archivo)

    # Primero se escribe en un archivo temporal y recién después se reemplaza el original. Así, si el computador se apaga a mitad de guardar, el archivo bueno no se daña.
    def guardar(self, nombre: str, datos: list[dict]) -> None:
        # Se escribe primero en un archivo temporal para no dañar el original si algo falla
        temporal = self._ruta(nombre).with_suffix(".tmp")
        with open(temporal, "w", encoding="utf-8") as archivo:
            # dump escribe los datos como JSON. ensure_ascii=False conserva las tildes y indent=2 deja el archivo ordenado para leerlo.
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
        os.replace(temporal, self._ruta(nombre))

    # Si un archivo está dañado, se renombra como .corrupto para no perder su contenido y poder crear uno nuevo.
    def apartar_corrupto(self, nombre: str) -> None:
        """Renombra un archivo corrupto para no perderlo, y así poder crear uno nuevo."""
        os.replace(self._ruta(nombre), self._ruta(nombre).with_suffix(".corrupto"))
