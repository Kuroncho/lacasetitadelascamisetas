"""
Medios de pago.

Conceptos POO: interfaz (clase abstracta) y polimorfismo. Todas las clases cumplen
el mismo contrato, por lo que se puede agregar un medio de pago nuevo sin tocar
la lógica de ventas.
"""

import re
from abc import ABC, abstractmethod

from .excepciones import PagoRechazadoException
from .validaciones import formato_clp


class MedioPago(ABC):
    """Contrato común de todas las formas de pago."""

    COMPROBANTE_UNICO = False  # True si el comprobante no se puede usar en dos ventas

    @abstractmethod
    def procesar_pago(self, monto: int) -> str:
        """Valida el pago y retorna el texto del comprobante. Si falla, lanza PagoRechazadoException."""

    @abstractmethod
    def obtener_nombre(self) -> str:
        """Retorna el nombre del medio de pago."""


class Efectivo(MedioPago):
    """Valida el monto recibido y calcula el vuelto."""

    def __init__(self, monto_recibido: int):
        self._monto_recibido = monto_recibido

    def procesar_pago(self, monto: int) -> str:
        if self._monto_recibido < monto:
            raise PagoRechazadoException(
                f"El monto recibido ({formato_clp(self._monto_recibido)}) no alcanza para pagar {formato_clp(monto)}."
            )
        vuelto = self._monto_recibido - monto
        return f"Recibido: {formato_clp(self._monto_recibido)} | Vuelto: {formato_clp(vuelto)}"

    def obtener_nombre(self) -> str:
        return "Efectivo"


class Transferencia(MedioPago):
    """Exige un código de comprobante bancario, que no se puede repetir."""

    COMPROBANTE_UNICO = True

    def __init__(self, codigo_comprobante: str):
        self._codigo = codigo_comprobante.strip().upper()

    def procesar_pago(self, monto: int) -> str:
        if not re.fullmatch(r"[A-Z0-9]{6,20}", self._codigo):
            raise PagoRechazadoException("El comprobante debe tener de 6 a 20 letras o números.")
        return f"Comprobante bancario: {self._codigo}"

    def obtener_nombre(self) -> str:
        return "Transferencia"


class TarjetaDebito(MedioPago):
    """Registra los últimos 4 dígitos de la tarjeta."""

    def __init__(self, ultimos_digitos: str):
        self._ultimos_digitos = ultimos_digitos.strip()

    def procesar_pago(self, monto: int) -> str:
        if not re.fullmatch(r"[0-9]{4}", self._ultimos_digitos):
            raise PagoRechazadoException("Debe ingresar los últimos 4 dígitos de la tarjeta.")
        return f"Tarjeta terminada en {self._ultimos_digitos}"

    def obtener_nombre(self) -> str:
        return "Tarjeta de Débito"
