"""
Órdenes de venta y su detalle.

Conceptos POO: composición (una Venta contiene una lista de DetalleVenta) y encapsulamiento.
"""

from datetime import datetime

from .excepciones import SinStockException
from .prenda import Prenda
from .usuario import Cliente
from .validaciones import formato_clp, validar_entero

TASA_IVA = 19  # Los precios de la tienda ya incluyen IVA


class EstadoVenta:
    """Estados posibles de una venta."""

    PENDIENTE = "PENDIENTE"
    PAGADA = "PAGADA"
    ENTREGADA = "ENTREGADA"
    CANCELADA = "CANCELADA"


class DetalleVenta:
    """Una línea de la venta. Guarda los datos del momento, por si después cambia el precio."""

    def __init__(self, codigo: str, descripcion: str, cantidad: int, subtotal: int):
        self.codigo = codigo
        self.descripcion = descripcion
        self.cantidad = cantidad
        self.subtotal = subtotal

    def a_dict(self) -> dict:
        return {
            "codigo": self.codigo,
            "descripcion": self.descripcion,
            "cantidad": self.cantidad,
            "subtotal": self.subtotal,
        }


class Venta:
    """Orden de venta: nace PENDIENTE y solo se guarda cuando se paga."""

    def __init__(self, vendedor: str):
        self._folio = 0
        self._fecha = datetime.now()
        self._vendedor = vendedor
        self._cliente_rut = ""
        self._cliente_nombre = ""
        self._descuento_cliente = 0  # Porcentaje de descuento por cliente frecuente
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

    @property
    def detalles(self) -> list[DetalleVenta]:
        """Retorna una copia para proteger la lista interna."""
        return list(self._detalles)

    def asignar_cliente(self, cliente: Cliente, descuento: int) -> None:
        self._cliente_rut = cliente.rut
        self._cliente_nombre = cliente.nombre
        self._descuento_cliente = descuento

    def cantidad_de(self, codigo: str) -> int:
        """Retorna cuántas unidades de una prenda hay en esta venta."""
        for detalle in self._detalles:
            if detalle.codigo == codigo:
                return detalle.cantidad
        return 0

    def agregar_prenda(self, prenda: Prenda, cantidad: int) -> None:
        """Agrega unidades a la venta. Si no hay stock suficiente lanza SinStockException."""
        if self._estado != EstadoVenta.PENDIENTE:
            raise ValueError("Solo se pueden modificar ventas pendientes.")
        validar_entero(cantidad, "La cantidad", minimo=1)

        total = self.cantidad_de(prenda.codigo) + cantidad
        if total > prenda.stock:
            raise SinStockException(
                f"Stock insuficiente de {prenda.descripcion}. "
                f"Disponibles: {prenda.stock}, solicitadas: {total}."
            )

        subtotal = prenda.calcular_precio_final(total)
        for detalle in self._detalles:
            if detalle.codigo == prenda.codigo:
                detalle.cantidad = total
                detalle.subtotal = subtotal
                return
        self._detalles.append(DetalleVenta(prenda.codigo, prenda.descripcion, total, subtotal))

    def quitar_detalle(self, indice: int) -> None:
        if self._estado != EstadoVenta.PENDIENTE:
            raise ValueError("Solo se pueden modificar ventas pendientes.")
        self._detalles.pop(indice)

    def vaciar(self) -> None:
        if self._estado != EstadoVenta.PENDIENTE:
            raise ValueError("Solo se pueden modificar ventas pendientes.")
        self._detalles.clear()

    # --- Cálculos: los precios ya incluyen IVA ---
    def calcular_subtotal(self) -> int:
        return sum(detalle.subtotal for detalle in self._detalles)

    def calcular_descuento(self) -> int:
        return round(self.calcular_subtotal() * self._descuento_cliente / 100)

    def calcular_total(self) -> int:
        return self.calcular_subtotal() - self.calcular_descuento()

    def calcular_iva(self) -> int:
        """IVA contenido en el total: total * 19 / 119."""
        return round(self.calcular_total() * TASA_IVA / (100 + TASA_IVA))

    def calcular_neto(self) -> int:
        return self.calcular_total() - self.calcular_iva()

    # --- Cambios de estado ---
    def marcar_pagada(self, folio: int, medio_pago: str, comprobante: str) -> None:
        self._folio = folio
        self._fecha = datetime.now()
        self._medio_pago = medio_pago
        self._comprobante = comprobante
        self._estado = EstadoVenta.PAGADA

    def marcar_entregada(self) -> None:
        if self._estado != EstadoVenta.PAGADA:
            raise ValueError("Solo se puede entregar una venta pagada.")
        self._estado = EstadoVenta.ENTREGADA

    def marcar_cancelada(self) -> None:
        if self._estado != EstadoVenta.PAGADA:
            raise ValueError("Solo se puede cancelar una venta pagada que no se haya entregado.")
        self._estado = EstadoVenta.CANCELADA

    def generar_boleta(self) -> str:
        lineas = [
            "=" * 50,
            "CONFECCIONES MARISOL MENA".center(50),
            "=" * 50,
            f"Folio N°:  {self._folio}",
            f"Fecha:     {self._fecha.strftime('%d-%m-%Y %H:%M')}",
            f"Vendedor:  {self._vendedor}",
            f"Cliente:   {self._cliente_nombre} (RUT {self._cliente_rut})",
            f"Estado:    {self._estado}",
            "-" * 50,
        ]
        for detalle in self._detalles:
            lineas.append(f"{detalle.cantidad} x {detalle.descripcion}")
            lineas.append(f"{formato_clp(detalle.subtotal):>50}")
        lineas.append("-" * 50)
        lineas.append(f"{'Subtotal:':<30}{formato_clp(self.calcular_subtotal()):>20}")
        lineas.append(f"{'Descuento cliente frecuente:':<30}{'-' + formato_clp(self.calcular_descuento()):>20}")
        lineas.append(f"{'TOTAL A PAGAR:':<30}{formato_clp(self.calcular_total()):>20}")
        lineas.append(f"{'  Neto incluido:':<30}{formato_clp(self.calcular_neto()):>20}")
        lineas.append(f"{'  IVA incluido (19%):':<30}{formato_clp(self.calcular_iva()):>20}")
        lineas.append("-" * 50)
        lineas.append(f"Pago: {self._medio_pago}")
        lineas.append(self._comprobante)
        lineas.append("=" * 50)
        return "\n".join(lineas)

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

    @staticmethod
    def desde_dict(datos: dict) -> "Venta":
        venta = Venta(datos["vendedor"])
        venta._folio = datos["folio"]
        venta._fecha = datetime.fromisoformat(datos["fecha"])
        venta._cliente_rut = datos["cliente_rut"]
        venta._cliente_nombre = datos["cliente_nombre"]
        venta._descuento_cliente = datos["descuento_cliente"]
        venta._detalles = [
            DetalleVenta(d["codigo"], d["descripcion"], d["cantidad"], d["subtotal"])
            for d in datos["detalles"]
        ]
        venta._estado = datos["estado"]
        venta._medio_pago = datos["medio_pago"]
        venta._comprobante = datos["comprobante"]
        return venta
