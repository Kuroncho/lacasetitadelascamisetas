"""
Medios de pago.

Conceptos POO: interfaz (clase abstracta) y polimorfismo. Todas las clases cumplen
el mismo contrato, por lo que se puede agregar un medio de pago nuevo sin tocar
la lógica de ventas.
"""

# re permite revisar que un texto cumpla un patrón (por ejemplo, 4 dígitos).
import re
from abc import ABC, abstractmethod

from .excepciones import PagoRechazadoException
from .validaciones import formato_clp


# Esta es una "interfaz": define QUÉ debe poder hacer cualquier forma de pago, pero no CÓMO.
# Efectivo, Transferencia y TarjetaDebito la cumplen cada una a su manera. Si mañana se agrega
# otro medio de pago, basta con crear otra clase hija y no hay que cambiar el módulo de ventas.
class MedioPago(ABC):
    """Contrato común de todas las formas de pago."""

    # Valor por defecto: el comprobante de este medio de pago se puede repetir. Las hijas pueden cambiarlo.
    COMPROBANTE_UNICO = False  # True si el comprobante no se puede usar en dos ventas

    # Cada hija valida el pago a su manera y devuelve el texto del comprobante.
    @abstractmethod
    def procesar_pago(self, monto: int) -> str:
        """Valida el pago y retorna el texto del comprobante. Si falla, lanza PagoRechazadoException."""

    # Cada hija devuelve su nombre, que se muestra en la boleta.
    @abstractmethod
    def obtener_nombre(self) -> str:
        """Retorna el nombre del medio de pago."""


# Pago en efectivo: revisa que alcance el dinero y calcula el vuelto.
class Efectivo(MedioPago):
    """Valida el monto recibido y calcula el vuelto."""

    # Guarda cuánto dinero entregó el cliente.
    def __init__(self, monto_recibido: int):
        self._monto_recibido = monto_recibido

    def procesar_pago(self, monto: int) -> str:
        # Si lo recibido es menor al total, el pago se rechaza lanzando una excepción (raise).
        if self._monto_recibido < monto:
            raise PagoRechazadoException(
                f"El monto recibido ({formato_clp(self._monto_recibido)}) no alcanza para pagar {formato_clp(monto)}."
            )
        # El vuelto es lo recibido menos lo que se debe.
        vuelto = self._monto_recibido - monto
        return f"Recibido: {formato_clp(self._monto_recibido)} | Vuelto: {formato_clp(vuelto)}"

    def obtener_nombre(self) -> str:
        return "Efectivo"


# Transferencia bancaria: exige un código de comprobante.
class Transferencia(MedioPago):
    """Exige un código de comprobante bancario, que no se puede repetir."""

    # Aquí sí: el mismo comprobante no puede usarse en dos ventas distintas (la revisión la hace el controlador).
    COMPROBANTE_UNICO = True

    def __init__(self, codigo_comprobante: str):
        self._codigo = codigo_comprobante.strip().upper()

    def procesar_pago(self, monto: int) -> str:
        # El comprobante debe tener entre 6 y 20 letras o números.
        if not re.fullmatch(r"[A-Z0-9]{6,20}", self._codigo):
            raise PagoRechazadoException("El comprobante debe tener de 6 a 20 letras o números.")
        return f"Comprobante bancario: {self._codigo}"

    def obtener_nombre(self) -> str:
        return "Transferencia"


# Tarjeta de débito: registra los últimos 4 dígitos.
class TarjetaDebito(MedioPago):
    """Registra los últimos 4 dígitos de la tarjeta."""

    def __init__(self, ultimos_digitos: str):
        self._ultimos_digitos = ultimos_digitos.strip()

    def procesar_pago(self, monto: int) -> str:
        # Exactamente 4 dígitos.
        if not re.fullmatch(r"[0-9]{4}", self._ultimos_digitos):
            raise PagoRechazadoException("Debe ingresar los últimos 4 dígitos de la tarjeta.")
        return f"Tarjeta terminada en {self._ultimos_digitos}"

    def obtener_nombre(self) -> str:
        return "Tarjeta de Débito"
