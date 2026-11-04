"""
Controladores: reciben lo que pide la pantalla, aplican las reglas del negocio
y modifican el modelo. Las vistas solo llaman a estos métodos y muestran el resultado.
"""

# Un controlador es el intermediario: la pantalla le pide algo ("cobra esta venta"), el controlador aplica las reglas
# del negocio y modifica el modelo. El punto inicial significa "desde esta misma carpeta".
from .controlador_clientes import ControladorClientes
from .controlador_inventario import ControladorInventario
from .controlador_usuarios import ControladorUsuarios
from .controlador_ventas import ControladorVentas


# Una caja que junta los 4 controladores para pasarlos todos juntos a la pantalla en vez de uno por uno.
class Controladores:
    """Agrupa los controladores del sistema para pasarlos juntos a la vista."""

    # Todos los controladores comparten el mismo almacén, es decir, trabajan sobre los mismos datos.
    def __init__(self, almacen):
        self.avisos = almacen.avisos  # Problemas de carga de datos, para mostrarlos al abrir
        self.usuarios = ControladorUsuarios(almacen)
        self.clientes = ControladorClientes(almacen)
        self.inventario = ControladorInventario(almacen)
        self.ventas = ControladorVentas(almacen)
