"""
Excepciones personalizadas del negocio.

Heredan de ValueError para que la interfaz pueda capturarlas de forma específica
o junto con los demás errores de validación.
"""


# Una excepción es un aviso de error. Con 'raise SinStockException(...)' se lanza el aviso y,
# con 'try ... except SinStockException', otra parte del programa lo atrapa y decide qué hacer.
# Esta clase queda casi vacía a propósito: hereda todo de ValueError y solo le da un nombre propio
# a este error, para distinguir "no hay stock" de cualquier otro problema.
class SinStockException(ValueError):
    """Se lanza cuando se pide más cantidad de la que hay en inventario."""


# Igual que la anterior, pero para pagos que no se pueden completar
# (monto insuficiente, comprobante inválido, etc.).
class PagoRechazadoException(ValueError):
    """Se lanza cuando un medio de pago no puede completar la transacción."""
