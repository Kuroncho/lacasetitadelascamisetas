"""
Controlador de inventario: crear prendas, ajustar stock y precios.
"""

from models.prenda import CLASES_PRENDA, Prenda
from models.validaciones import texto_a_entero


class ControladorInventario:
    def __init__(self, almacen):
        self._almacen = almacen

    @property
    def prendas(self) -> list[Prenda]:
        return list(self._almacen.prendas)

    def crear_prenda(self, tipo: str, codigo: str, nombre: str, talla: str,
                     precio: str, stock: str, *caracteristicas: str) -> Prenda:
        """Crea la prenda del tipo indicado. Precio y stock llegan como texto, tal como se escribieron."""
        clase = CLASES_PRENDA.get(tipo)
        if clase is None:
            raise ValueError("Debe seleccionar un tipo de prenda.")
        prenda = clase(
            codigo, nombre, talla,
            texto_a_entero(precio, "El precio"),
            texto_a_entero(stock, "El stock"),
            *caracteristicas,
        )
        if self._almacen.buscar_prenda(prenda.codigo):
            raise ValueError(f"Ya existe una prenda con el código {prenda.codigo}.")
        self._almacen.prendas.append(prenda)
        self._almacen.guardar("prendas")
        return prenda

    def ajustar_stock(self, codigo: str, diferencia: int) -> None:
        """Suma o resta unidades. El setter de stock impide que quede negativo."""
        prenda = self._almacen.buscar_prenda(codigo)
        prenda.stock = prenda.stock + diferencia
        self._almacen.guardar("prendas")

    def cambiar_precio(self, codigo: str, precio: str) -> None:
        self._almacen.buscar_prenda(codigo).precio_base = texto_a_entero(precio, "El precio")
        self._almacen.guardar("prendas")

    def eliminar_prenda(self, codigo: str) -> None:
        if any(d.codigo == codigo for venta in self._almacen.ventas for d in venta.detalles):
            raise ValueError("No se puede eliminar una prenda que tiene ventas registradas.")
        self._almacen.prendas.remove(self._almacen.buscar_prenda(codigo))
        self._almacen.guardar("prendas")
