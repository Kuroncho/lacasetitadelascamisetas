"""
La Caserita de las Camisetas: sistema de ventas e inventario.
Para ejecutar: py main.py
"""

from pathlib import Path

from gui.app import Aplicacion
from models.gestor_datos import GestorDatos
from models.tienda import Tienda


def main():
    carpeta_datos = Path(__file__).parent / "datos"
    tienda = Tienda(GestorDatos(carpeta_datos))
    Aplicacion(tienda).mainloop()


if __name__ == "__main__":
    main()
