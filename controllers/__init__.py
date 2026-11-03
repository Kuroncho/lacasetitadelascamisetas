"""
Controladores: reciben lo que pide la pantalla, aplican las reglas del negocio
y modifican el modelo. Las vistas solo llaman a estos métodos y muestran el resultado.
"""

from .controlador_clientes import ControladorClientes
from .controlador_inventario import ControladorInventario
from .controlador_usuarios import ControladorUsuarios
from .controlador_ventas import ControladorVentas


class Controladores:
    """Agrupa los controladores del sistema para pasarlos juntos a la vista."""

    def __init__(self, almacen):
        self.avisos = almacen.avisos  # Problemas de carga de datos, para mostrarlos al abrir
        self.usuarios = ControladorUsuarios(almacen)
        self.clientes = ControladorClientes(almacen)
        self.inventario = ControladorInventario(almacen)
        self.ventas = ControladorVentas(almacen)
