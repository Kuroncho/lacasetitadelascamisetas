"""
La Caserita de las Camisetas: sistema de ventas e inventario.
Para ejecutar: py main.py

Estructura MVC:
  models/       datos y reglas propias de cada objeto (y el guardado en JSON)
  controllers/  reglas del negocio: reciben lo que pide la pantalla y modifican el modelo
  views/        pantallas Tkinter: muestran datos y llaman a los controladores
"""

# Cada 'import' trae lo necesario desde otro archivo. Path sirve para armar rutas de carpetas sin errores.
from pathlib import Path

# Se traen las 3 capas: controladores (reglas), almacén (datos) y la ventana (pantalla).
from controllers import Controladores
from models.almacen import Almacen
from models.gestor_datos import GestorDatos
from views.app import Aplicacion


# Función principal: crea las piezas y abre la ventana. Se conectan de adentro hacia afuera: datos -> reglas -> pantalla.
def main():
    # __file__ es la ruta de este archivo; .parent es su carpeta. Los JSON se guardan en la subcarpeta 'datos'.
    carpeta_datos = Path(__file__).parent / "datos"
    # El almacén carga los JSON (o crea datos de ejemplo la primera vez).
    almacen = Almacen(GestorDatos(carpeta_datos))
    # Se crea la ventana con los controladores y mainloop() la mantiene abierta, esperando clics, hasta que se cierra.
    Aplicacion(Controladores(almacen)).mainloop()


# Esto es verdadero solo cuando se ejecuta este archivo directamente (py main.py), y no cuando otro archivo lo importa.
if __name__ == "__main__":
    main()
