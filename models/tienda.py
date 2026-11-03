"""
Clase principal del sistema: reúne las colecciones y aplica las reglas del negocio.
La interfaz gráfica solo llama a estos métodos. Cada cambio se guarda en JSON.
"""

from .excepciones import PagoRechazadoException, SinStockException
from .gestor_datos import GestorDatos
from .pago import MedioPago
from .prenda import Prenda, PrendaEstandar, PrendaTermica, RopaInterior, prenda_desde_dict
from .usuario import Administrador, Cliente, Empleado, Vendedor
from .venta import EstadoVenta, Venta

FOLIO_INICIAL = 1001
COMPRAS_CLIENTE_FRECUENTE = 3  # Compras necesarias para tener el beneficio
DESCUENTO_CLIENTE_FRECUENTE = 5  # Porcentaje de descuento


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


class Tienda:
    def __init__(self, gestor: GestorDatos):
        self._gestor = gestor
        self.avisos: list[str] = []  # Problemas de carga que la interfaz debe mostrar
        iniciales = _datos_iniciales()
        self._prendas: list[Prenda] = self._cargar("prendas", prenda_desde_dict, iniciales["prendas"])
        self._clientes: list[Cliente] = self._cargar("clientes", Cliente.desde_dict, iniciales["clientes"])
        self._usuarios: list[Empleado] = self._cargar("usuarios", Empleado.desde_dict, iniciales["usuarios"])
        self._ventas: list[Venta] = self._cargar("ventas", Venta.desde_dict, [])

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

    def _guardar(self, nombre: str) -> None:
        coleccion = {
            "prendas": self._prendas,
            "clientes": self._clientes,
            "usuarios": self._usuarios,
            "ventas": self._ventas,
        }[nombre]
        self._gestor.guardar(nombre, [objeto.a_dict() for objeto in coleccion])

    # --- Inicio de sesión ---
    def iniciar_sesion(self, usuario: str, clave: str) -> Empleado:
        empleado = self._buscar_usuario(usuario.strip().lower())
        if empleado is None or not empleado.verificar_clave(clave):
            raise ValueError("Usuario o clave incorrectos.")
        return empleado

    # --- Usuarios ---
    @property
    def usuarios(self) -> list[Empleado]:
        return list(self._usuarios)

    def _buscar_usuario(self, usuario: str) -> Empleado | None:
        for empleado in self._usuarios:
            if empleado.usuario == usuario:
                return empleado
        return None

    def crear_usuario(self, rol: str, rut: str, nombre: str, usuario: str, clave: str) -> Empleado:
        clases = {"Administrador": Administrador, "Vendedor": Vendedor}
        if rol not in clases:
            raise ValueError("Debe seleccionar un rol.")
        nuevo = clases[rol](rut, nombre, usuario, clave)
        if self._buscar_usuario(nuevo.usuario):
            raise ValueError(f"El usuario '{nuevo.usuario}' ya existe.")
        if any(e.rut == nuevo.rut for e in self._usuarios):
            raise ValueError(f"Ya existe un usuario con el RUT {nuevo.rut}.")
        self._usuarios.append(nuevo)
        self._guardar("usuarios")
        return nuevo

    def cambiar_clave(self, usuario: str, clave: str) -> None:
        self._buscar_usuario(usuario).cambiar_clave(clave)
        self._guardar("usuarios")

    def eliminar_usuario(self, usuario: str, sesion_actual: Empleado) -> None:
        empleado = self._buscar_usuario(usuario)
        if empleado.usuario == sesion_actual.usuario:
            raise ValueError("No puede eliminar su propio usuario mientras tiene la sesión abierta.")
        self._usuarios.remove(empleado)
        self._guardar("usuarios")

    # --- Clientes ---
    @property
    def clientes(self) -> list[Cliente]:
        return list(self._clientes)

    def buscar_cliente(self, rut: str) -> Cliente | None:
        for cliente in self._clientes:
            if cliente.rut == rut:
                return cliente
        return None

    def registrar_cliente(self, rut: str, nombre: str, telefono: str, correo: str) -> Cliente:
        nuevo = Cliente(rut, nombre, telefono, correo)
        if self.buscar_cliente(nuevo.rut):
            raise ValueError(f"Ya existe un cliente con el RUT {nuevo.rut}.")
        self._clientes.append(nuevo)
        self._guardar("clientes")
        return nuevo

    def actualizar_cliente(self, rut: str, nombre: str, telefono: str, correo: str) -> None:
        # Se valida con un objeto temporal para no dejar el cliente a medio cambiar
        validado = Cliente(rut, nombre, telefono, correo)
        cliente = self.buscar_cliente(validado.rut)
        cliente.nombre = validado.nombre
        cliente.telefono = validado.telefono
        cliente.correo = validado.correo
        self._guardar("clientes")

    def eliminar_cliente(self, rut: str) -> None:
        if self.historial_cliente(rut):
            raise ValueError("No se puede eliminar un cliente que tiene compras registradas.")
        self._clientes.remove(self.buscar_cliente(rut))
        self._guardar("clientes")

    def historial_cliente(self, rut: str) -> list[Venta]:
        return [venta for venta in self._ventas if venta.cliente_rut == rut]

    def es_cliente_frecuente(self, rut: str) -> bool:
        compras = [v for v in self.historial_cliente(rut) if v.estado != EstadoVenta.CANCELADA]
        return len(compras) >= COMPRAS_CLIENTE_FRECUENTE

    # --- Inventario ---
    @property
    def prendas(self) -> list[Prenda]:
        return list(self._prendas)

    def buscar_prenda(self, codigo: str) -> Prenda | None:
        for prenda in self._prendas:
            if prenda.codigo == codigo:
                return prenda
        return None

    def agregar_prenda(self, prenda: Prenda) -> None:
        if self.buscar_prenda(prenda.codigo):
            raise ValueError(f"Ya existe una prenda con el código {prenda.codigo}.")
        self._prendas.append(prenda)
        self._guardar("prendas")

    def ajustar_stock(self, codigo: str, diferencia: int) -> None:
        """Suma o resta unidades. El setter de stock impide que quede negativo."""
        prenda = self.buscar_prenda(codigo)
        prenda.stock = prenda.stock + diferencia
        self._guardar("prendas")

    def cambiar_precio(self, codigo: str, precio: int) -> None:
        self.buscar_prenda(codigo).precio_base = precio
        self._guardar("prendas")

    def eliminar_prenda(self, codigo: str) -> None:
        if any(d.codigo == codigo for venta in self._ventas for d in venta.detalles):
            raise ValueError("No se puede eliminar una prenda que tiene ventas registradas.")
        self._prendas.remove(self.buscar_prenda(codigo))
        self._guardar("prendas")

    # --- Ventas ---
    @property
    def ventas(self) -> list[Venta]:
        return list(self._ventas)

    def buscar_venta(self, folio: int) -> Venta | None:
        for venta in self._ventas:
            if venta.folio == folio:
                return venta
        return None

    def asignar_cliente(self, venta: Venta, cliente: Cliente) -> None:
        """Asocia el cliente a la venta y le aplica su beneficio si corresponde."""
        descuento = DESCUENTO_CLIENTE_FRECUENTE if self.es_cliente_frecuente(cliente.rut) else 0
        venta.asignar_cliente(cliente, descuento)

    def registrar_venta(self, venta: Venta, medio_pago: MedioPago) -> None:
        """
        Cobra y registra la venta. Primero valida todo, y solo si no hay errores
        descuenta el stock. Así una venta rechazada no cambia nada.
        """
        if venta.estado != EstadoVenta.PENDIENTE:
            raise ValueError("Esta venta ya fue procesada.")
        if not venta.detalles:
            raise ValueError("La venta no tiene prendas.")
        if not venta.cliente_rut:
            raise ValueError("Debe seleccionar un cliente.")
        cliente = self.buscar_cliente(venta.cliente_rut)
        if cliente is None:
            raise ValueError("El cliente de esta venta ya no existe. Seleccione otro.")
        self.asignar_cliente(venta, cliente)  # Por si cambiaron sus datos con el carro abierto

        # Se revisa de nuevo porque el inventario pudo cambiar desde que se armó el carro
        for detalle in venta.detalles:
            prenda = self.buscar_prenda(detalle.codigo)
            if prenda is None:
                raise SinStockException(f"La prenda {detalle.descripcion} ya no existe en el inventario.")
            if detalle.cantidad > prenda.stock:
                raise SinStockException(f"Stock insuficiente de {prenda.descripcion}. Disponibles: {prenda.stock}.")

        comprobante = medio_pago.procesar_pago(venta.calcular_total())
        if medio_pago.COMPROBANTE_UNICO and any(v.comprobante == comprobante for v in self._ventas):
            raise PagoRechazadoException("Ese comprobante ya fue usado en otra venta.")

        for detalle in venta.detalles:
            self.buscar_prenda(detalle.codigo).descontar_stock(detalle.cantidad)

        folio = max((v.folio for v in self._ventas), default=FOLIO_INICIAL - 1) + 1
        venta.marcar_pagada(folio, medio_pago.obtener_nombre(), comprobante)
        self._ventas.append(venta)
        self._guardar("prendas")
        self._guardar("ventas")

    def entregar_venta(self, folio: int) -> None:
        self.buscar_venta(folio).marcar_entregada()
        self._guardar("ventas")

    def cancelar_venta(self, folio: int) -> None:
        """Cancela una venta pagada y devuelve las unidades al inventario."""
        venta = self.buscar_venta(folio)
        venta.marcar_cancelada()
        for detalle in venta.detalles:
            self.buscar_prenda(detalle.codigo).reponer_stock(detalle.cantidad)
        self._guardar("prendas")
        self._guardar("ventas")
