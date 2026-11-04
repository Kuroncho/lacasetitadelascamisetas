"""
Órdenes de venta y su detalle.

Conceptos POO: composición (una Venta contiene una lista de DetalleVenta) y encapsulamiento.
"""

# datetime entrega la fecha y hora actuales (datetime.now()).
from datetime import datetime

from .excepciones import SinStockException
from .prenda import Prenda
from .usuario import Cliente
from .validaciones import validar_entero

# Constante: el IVA en Chile es 19%. Los precios de la tienda ya lo incluyen.
TASA_IVA = 19  # Los precios de la tienda ya incluyen IVA


# Los estados posibles de una venta, escritos una sola vez para no equivocarse al escribirlos en otras partes.
class EstadoVenta:
    """Estados posibles de una venta."""

    PENDIENTE = "PENDIENTE"
    PAGADA = "PAGADA"
    ENTREGADA = "ENTREGADA"
    CANCELADA = "CANCELADA"


# Una línea de la venta (por ejemplo "2 x Polera básica"). Guarda una copia del nombre y del subtotal
# del momento de la compra, así la boleta no cambia aunque después cambie el precio.
class DetalleVenta:
    """Una línea de la venta. Guarda los datos del momento, por si después cambia el precio."""

    def __init__(self, codigo: str, descripcion: str, cantidad: int, subtotal: int):
        self.codigo = codigo
        self.descripcion = descripcion
        self.cantidad = cantidad
        self.subtotal = subtotal

    # Convierte la línea en diccionario para guardarla en el JSON.
    def a_dict(self) -> dict:
        return {
            "codigo": self.codigo,
            "descripcion": self.descripcion,
            "cantidad": self.cantidad,
            "subtotal": self.subtotal,
        }


# Una orden de venta. Nace PENDIENTE (carro en armado) y cuando se paga pasa a PAGADA.
# Contiene una lista de DetalleVenta: eso se llama composición (un objeto formado por otros).
class Venta:
    """Orden de venta: nace PENDIENTE y solo se guarda cuando se paga."""

    # Estado inicial de una venta nueva: sin folio, sin cliente y sin prendas.
    def __init__(self, vendedor: str):
        self._folio = 0
        self._fecha = datetime.now()
        self._vendedor = vendedor
        self._cliente_rut = ""
        self._cliente_nombre = ""
        self._descuento_cliente = 0  # Porcentaje de descuento por cliente frecuente
        # Una lista vacía. Aquí se irán agregando las prendas del carro.
        self._detalles: list[DetalleVenta] = []
        self._estado = EstadoVenta.PENDIENTE
        self._medio_pago = ""
        self._comprobante = ""

    @property
    def folio(self) -> int:
        return self._folio

    @property
    def fecha(self) -> datetime:
        return self._fecha

    @property
    def vendedor(self) -> str:
        return self._vendedor

    @property
    def cliente_rut(self) -> str:
        return self._cliente_rut

    @property
    def cliente_nombre(self) -> str:
        return self._cliente_nombre

    @property
    def estado(self) -> str:
        return self._estado

    @property
    def medio_pago(self) -> str:
        return self._medio_pago

    @property
    def comprobante(self) -> str:
        return self._comprobante

    # Entrega una copia de la lista. Así quien la lea no puede modificar el carro sin pasar por los métodos de esta clase.
    @property
    def detalles(self) -> list[DetalleVenta]:
        """Retorna una copia para proteger la lista interna."""
        return list(self._detalles)

    # Guarda el RUT y el nombre del cliente, y su porcentaje de descuento (0 si no es cliente frecuente).
    def asignar_cliente(self, cliente: Cliente, descuento: int) -> None:
        self._cliente_rut = cliente.rut
        self._cliente_nombre = cliente.nombre
        self._descuento_cliente = descuento

    # Cuenta cuántas unidades de una prenda hay ya en el carro. Recorre las líneas con un for; si no la encuentra devuelve 0.
    def cantidad_de(self, codigo: str) -> int:
        """Retorna cuántas unidades de una prenda hay en esta venta."""
        for detalle in self._detalles:
            if detalle.codigo == codigo:
                return detalle.cantidad
        return 0

    # Agrega unidades al carro. Es la regla principal contra la venta sin stock:
    # se suma lo que ya hay en el carro con lo nuevo y, si supera el stock de la prenda, se lanza SinStockException.
    def agregar_prenda(self, prenda: Prenda, cantidad: int) -> None:
        """Agrega unidades a la venta. Si no hay stock suficiente lanza SinStockException."""
        # Una venta ya pagada o cancelada no se puede modificar.
        if self._estado != EstadoVenta.PENDIENTE:
            raise ValueError("Solo se pueden modificar ventas pendientes.")
        # La cantidad debe ser un entero de al menos 1 (rechaza 0 y negativos).
        validar_entero(cantidad, "La cantidad", minimo=1)

        # Total que habría en el carro si se acepta esta cantidad.
        total = self.cantidad_de(prenda.codigo) + cantidad
        # Si se pide más de lo que existe, se detiene todo y el carro queda como estaba.
        if total > prenda.stock:
            raise SinStockException(
                f"Stock insuficiente de {prenda.descripcion}. "
                f"Disponibles: {prenda.stock}, solicitadas: {total}."
            )

        # Cada prenda calcula su precio con su propia regla (polimorfismo).
        subtotal = prenda.calcular_precio_final(total)
        # Si la prenda ya estaba en el carro se actualiza su línea y se termina (return); si no, se agrega una nueva más abajo.
        for detalle in self._detalles:
            if detalle.codigo == prenda.codigo:
                detalle.cantidad = total
                detalle.subtotal = subtotal
                return
        self._detalles.append(DetalleVenta(prenda.codigo, prenda.descripcion, total, subtotal))

    # pop(indice) quita de la lista el elemento que está en esa posición (la primera posición es la 0).
    def quitar_detalle(self, indice: int) -> None:
        if self._estado != EstadoVenta.PENDIENTE:
            raise ValueError("Solo se pueden modificar ventas pendientes.")
        self._detalles.pop(indice)

    # clear() deja la lista sin elementos.
    def vaciar(self) -> None:
        if self._estado != EstadoVenta.PENDIENTE:
            raise ValueError("Solo se pueden modificar ventas pendientes.")
        self._detalles.clear()

    # --- Cálculos: los precios ya incluyen IVA ---
    # sum(...) suma todos los subtotales de las líneas del carro.
    def calcular_subtotal(self) -> int:
        return sum(detalle.subtotal for detalle in self._detalles)

    # Porcentaje de descuento del cliente aplicado al subtotal.
    def calcular_descuento(self) -> int:
        return round(self.calcular_subtotal() * self._descuento_cliente / 100)

    # Lo que paga el cliente: subtotal menos descuento.
    def calcular_total(self) -> int:
        return self.calcular_subtotal() - self.calcular_descuento()

    # Como el precio ya incluye IVA, se calcula cuánto IVA hay dentro del total: total * 19 / 119.
    # (Un 19% sobre el neto equivale a 19/119 del total con IVA.)
    def calcular_iva(self) -> int:
        """IVA contenido en el total: total * 19 / 119."""
        return round(self.calcular_total() * TASA_IVA / (100 + TASA_IVA))

    # El monto sin IVA es el total menos el IVA.
    def calcular_neto(self) -> int:
        return self.calcular_total() - self.calcular_iva()

    # --- Cambios de estado ---
    # Se llama cuando el cobro resultó bien: guarda el folio, la fecha de pago, el medio de pago y cambia el estado.
    def marcar_pagada(self, folio: int, medio_pago: str, comprobante: str) -> None:
        self._folio = folio
        self._fecha = datetime.now()
        self._medio_pago = medio_pago
        self._comprobante = comprobante
        self._estado = EstadoVenta.PAGADA

    # Solo se puede entregar una venta que está pagada.
    def marcar_entregada(self) -> None:
        if self._estado != EstadoVenta.PAGADA:
            raise ValueError("Solo se puede entregar una venta pagada.")
        self._estado = EstadoVenta.ENTREGADA

    # Solo se puede cancelar una venta pagada y que aún no se entregó.
    def marcar_cancelada(self) -> None:
        if self._estado != EstadoVenta.PAGADA:
            raise ValueError("Solo se puede cancelar una venta pagada que no se haya entregado.")
        self._estado = EstadoVenta.CANCELADA

    # Convierte la venta completa en diccionario. La lista de detalles se convierte línea por línea.
    def a_dict(self) -> dict:
        return {
            "folio": self._folio,
            "fecha": self._fecha.isoformat(timespec="seconds"),
            "vendedor": self._vendedor,
            "cliente_rut": self._cliente_rut,
            "cliente_nombre": self._cliente_nombre,
            "descuento_cliente": self._descuento_cliente,
            "detalles": [detalle.a_dict() for detalle in self._detalles],
            "estado": self._estado,
            "medio_pago": self._medio_pago,
            "comprobante": self._comprobante,
        }

    # Reconstruye una Venta leyendo los datos guardados en el JSON (lo contrario de a_dict).
    @staticmethod
    def desde_dict(datos: dict) -> "Venta":
        venta = Venta(datos["vendedor"])
        venta._folio = datos["folio"]
        venta._fecha = datetime.fromisoformat(datos["fecha"])
        venta._cliente_rut = datos["cliente_rut"]
        venta._cliente_nombre = datos["cliente_nombre"]
        venta._descuento_cliente = datos["descuento_cliente"]
        # Crea la lista de líneas recorriendo los datos guardados (comprensión de listas, ver GUIA_DE_SINTAXIS.md).
        venta._detalles = [
            DetalleVenta(d["codigo"], d["descripcion"], d["cantidad"], d["subtotal"])
            for d in datos["detalles"]
        ]
        venta._estado = datos["estado"]
        venta._medio_pago = datos["medio_pago"]
        venta._comprobante = datos["comprobante"]
        return venta
