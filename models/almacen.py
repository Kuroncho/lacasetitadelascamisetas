"""
Almacén de datos del sistema.

Reúne las listas del negocio (prendas, clientes, usuarios y ventas) y las guarda y carga desde
archivos JSON. Solo conserva los datos: las reglas del negocio las aplican los controladores.
"""

from .gestor_datos import GestorDatos
from .prenda import PrendaEstandar, PrendaTermica, RopaInterior, prenda_desde_dict
from .usuario import Administrador, Cliente, Empleado, Vendedor
from .venta import Venta


def _datos_iniciales() -> dict:
    """Datos de ejemplo que se crean la primera vez que se abre el sistema."""
    return {
        "prendas": [
            PrendaTermica("TER-001", "Beatle", "M", 12000, 10, "Tortuga", "Alto"),
            PrendaTermica("TER-002", "Camiseta de invierno", "L", 10000, 8, "Redondo", "Medio"),
            PrendaEstandar("EST-001", "Polera básica", "S", 5000, 20, "Corta"),
            PrendaEstandar("EST-002", "Polera básica", "L", 6000, 15, "Larga"),
            RopaInterior("INT-001", "Calzoncillo largo", "M", 8000, 12, "Ancho", "Regular"),
            RopaInterior("INT-002", "Calzoncillo largo", "XXL", 8000, 2, "Ancho", "Ceñido"),
        ],
        "clientes": [
            Cliente("11.111.111-1", "Juan Perez", "+56911223344", "juan@correo.cl"),
            Cliente("22.222.222-2", "Maria Gonzalez", "+56988776655", "maria@correo.cl"),
        ],
        "usuarios": [
            Administrador("33.333.333-3", "Marisol Mena", "marisol", "admin123"),
            Vendedor("44.444.444-4", "Carlos Baeza", "carlos", "vende123"),
        ],
    }


class Almacen:
    def __init__(self, gestor: GestorDatos):
        self._gestor = gestor
        self.avisos: list[str] = []  # Problemas de carga que la interfaz debe mostrar
        iniciales = _datos_iniciales()
        self.prendas = self._cargar("prendas", prenda_desde_dict, iniciales["prendas"])
        self.clientes = self._cargar("clientes", Cliente.desde_dict, iniciales["clientes"])
        self.usuarios = self._cargar("usuarios", Empleado.desde_dict, iniciales["usuarios"])
        self.ventas = self._cargar("ventas", Venta.desde_dict, [])

    def _cargar(self, nombre: str, crear_objeto, iniciales: list) -> list:
        """Lee un archivo JSON. Si falta o está dañado, parte con los datos iniciales."""
        if self._gestor.existe(nombre):
            try:
                objetos = [crear_objeto(datos) for datos in self._gestor.cargar(nombre)]
                if nombre != "usuarios" or any(u.puede_administrar() for u in objetos):
                    return objetos
                raise ValueError("No hay ningún administrador.")
            except (ValueError, KeyError, TypeError, AttributeError):
                self._gestor.apartar_corrupto(nombre)
                self.avisos.append(f"El archivo {nombre}.json estaba dañado. Se guardó como {nombre}.corrupto y se creó uno nuevo.")

        self._gestor.guardar(nombre, [objeto.a_dict() for objeto in iniciales])
        return iniciales

    def guardar(self, nombre: str) -> None:
        """Guarda en JSON la lista indicada: 'prendas', 'clientes', 'usuarios' o 'ventas'."""
        coleccion = getattr(self, nombre)
        self._gestor.guardar(nombre, [objeto.a_dict() for objeto in coleccion])

    # --- Búsquedas: devuelven el objeto o None si no existe ---
    def buscar_prenda(self, codigo: str):
        return next((p for p in self.prendas if p.codigo == codigo), None)

    def buscar_cliente(self, rut: str):
        return next((c for c in self.clientes if c.rut == rut), None)

    def buscar_usuario(self, usuario: str):
        return next((u for u in self.usuarios if u.usuario == usuario), None)

    def buscar_venta(self, folio: int):
        return next((v for v in self.ventas if v.folio == folio), None)

    def ventas_de(self, rut: str) -> list[Venta]:
        return [venta for venta in self.ventas if venta.cliente_rut == rut]
