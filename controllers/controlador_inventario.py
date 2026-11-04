"""
Controlador de inventario: crear prendas, ajustar stock y precios.
"""

# CLASES_PRENDA relaciona el nombre de un tipo con su clase.
from models.prenda import CLASES_PRENDA, Prenda
from models.validaciones import texto_a_entero


# Reglas del inventario: crear prendas, ajustar stock y precios, eliminar.
class ControladorInventario:
    def __init__(self, almacen):
        self._almacen = almacen

    # Copia de la lista de prendas, solo para mostrar.
    @property
    def prendas(self) -> list[Prenda]:
        return list(self._almacen.prendas)

    # Crea una prenda del tipo indicado. Precio y stock llegan como texto, tal como se escribieron en pantalla.
    # '*caracteristicas' recoge todos los datos extra que lleguen (cuello, manga, etc.) en una sola lista.
    def crear_prenda(self, tipo: str, codigo: str, nombre: str, talla: str,
                     precio: str, stock: str, *caracteristicas: str) -> Prenda:
        """Crea la prenda del tipo indicado. Precio y stock llegan como texto, tal como se escribieron."""
        # get() entrega la clase del tipo, o None si ese tipo no existe.
        clase = CLASES_PRENDA.get(tipo)
        # Se rechaza un tipo desconocido.
        if clase is None:
            raise ValueError("Debe seleccionar un tipo de prenda.")
        # Se crea el objeto con la clase elegida. texto_a_entero convierte el texto en número y falla si no es válido; los demás datos los valida el modelo.
        prenda = clase(
            codigo, nombre, talla,
            texto_a_entero(precio, "El precio"),
            texto_a_entero(stock, "El stock"),
            *caracteristicas,
        )
        # No puede haber dos prendas con el mismo código.
        if self._almacen.buscar_prenda(prenda.codigo):
            raise ValueError(f"Ya existe una prenda con el código {prenda.codigo}.")
        self._almacen.prendas.append(prenda)
        self._almacen.guardar("prendas")
        return prenda

    # Suma o resta unidades (botones +1, +5, -1, -5). El modelo impide que el stock quede negativo.
    def ajustar_stock(self, codigo: str, diferencia: int) -> None:
        """Suma o resta unidades. El setter de stock impide que quede negativo."""
        prenda = self._almacen.buscar_prenda(codigo)
        # Esto pasa por el setter de Prenda, que lanza error si el resultado es menor a 0.
        prenda.stock = prenda.stock + diferencia
        self._almacen.guardar("prendas")

    # Cambia el precio base. El texto se convierte a número y el modelo valida que sea mayor a 0.
    def cambiar_precio(self, codigo: str, precio: str) -> None:
        self._almacen.buscar_prenda(codigo).precio_base = texto_a_entero(precio, "El precio")
        self._almacen.guardar("prendas")

    # Una prenda que ya se vendió no se puede eliminar, para que el historial de ventas siga teniendo sentido.
    def eliminar_prenda(self, codigo: str) -> None:
        # Recorre todas las ventas y todas sus líneas; si alguna usa este código, la prenda no se elimina.
        if any(d.codigo == codigo for venta in self._almacen.ventas for d in venta.detalles):
            raise ValueError("No se puede eliminar una prenda que tiene ventas registradas.")
        self._almacen.prendas.remove(self._almacen.buscar_prenda(codigo))
        self._almacen.guardar("prendas")
