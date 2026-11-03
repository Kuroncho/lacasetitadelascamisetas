"""
La Caserita de las Camisetas: sistema de ventas e inventario.
Para ejecutar: py main.py

Estructura MVC:
  models/       datos y reglas propias de cada objeto (y el guardado en JSON)
  controllers/  reglas del negocio: reciben lo que pide la pantalla y modifican el modelo
  views/        pantallas Tkinter: muestran datos y llaman a los controladores
"""

from pathlib import Path

from controllers import Controladores
from models.almacen import Almacen
from models.gestor_datos import GestorDatos
from views.app import Aplicacion


def main():
    carpeta_datos = Path(__file__).parent / "datos"
    almacen = Almacen(GestorDatos(carpeta_datos))
    Aplicacion(Controladores(almacen)).mainloop()


if __name__ == "__main__":
    main()
