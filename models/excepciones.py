"""
Excepciones personalizadas del negocio.

Heredan de ValueError para que la interfaz pueda capturarlas de forma específica
o junto con los demás errores de validación.
"""


class SinStockException(ValueError):
    """Se lanza cuando se pide más cantidad de la que hay en inventario."""


class PagoRechazadoException(ValueError):
    """Se lanza cuando un medio de pago no puede completar la transacción."""
