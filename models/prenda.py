"""
Catálogo de prendas.

Conceptos POO: clase abstracta, herencia y polimorfismo. Cada tipo de prenda
calcula su precio final con su propia regla en calcular_precio_final().
"""

from abc import ABC, abstractmethod

from .excepciones import SinStockException
from .validaciones import validar_entero

TALLAS = ["S", "M", "L", "XL", "XXL"]


def _validar_opcion(valor: str, opciones: list[str], nombre: str) -> str:
    if valor not in opciones:
        raise ValueError(f"{nombre} debe ser una de estas opciones: {', '.join(opciones)}.")
    return valor


class Prenda(ABC):
    """Atributos y comportamiento común de todas las prendas."""

    def __init__(self, codigo: str, nombre: str, talla: str, precio_base: int, stock: int):
        limpio = codigo.strip().upper()
        if not limpio or " " in limpio:
            raise ValueError("El código no puede estar vacío ni tener espacios.")
        if len(nombre.strip()) < 2:
            raise ValueError("El nombre de la prenda debe tener al menos 2 caracteres.")
        self._codigo = limpio
        self._nombre = nombre.strip().capitalize()
        self._talla = _validar_opcion(talla, TALLAS, "La talla")
        self.precio_base = precio_base
        self.stock = stock

    @property
    def codigo(self) -> str:
        return self._codigo

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def talla(self) -> str:
        return self._talla

    @property
    def precio_base(self) -> int:
        return self._precio_base

    @precio_base.setter
    def precio_base(self, valor: int):
        self._precio_base = validar_entero(valor, "El precio", minimo=1)

    @property
    def stock(self) -> int:
        return self._stock

    @stock.setter
    def stock(self, valor: int):
        self._stock = validar_entero(valor, "El stock", minimo=0)

    @property
    def descripcion(self) -> str:
        return f"{self._nombre} (Talla {self._talla})"

    def descontar_stock(self, cantidad: int) -> None:
        if cantidad > self._stock:
            raise SinStockException(f"Stock insuficiente de {self.descripcion}. Disponibles: {self._stock}.")
        self.stock = self._stock - cantidad

    def reponer_stock(self, cantidad: int) -> None:
        self.stock = self._stock + cantidad

    @abstractmethod
    def calcular_precio_final(self, cantidad: int = 1) -> int:
        """Retorna el precio total de comprar esa cantidad, con las reglas del tipo de prenda."""

    @abstractmethod
    def obtener_tipo(self) -> str:
        """Retorna el nombre del tipo de prenda."""

    @abstractmethod
    def detalle(self) -> str:
        """Retorna las características propias del tipo de prenda."""

    def a_dict(self) -> dict:
        return {
            "tipo": self.obtener_tipo(),
            "codigo": self.codigo,
            "nombre": self.nombre,
            "talla": self.talla,
            "precio_base": self.precio_base,
            "stock": self.stock,
        }


class PrendaTermica(Prenda):
    """Camisetas de invierno y beatles. Su precio lleva un recargo fijo."""

    TIPO = "Térmica"
    RECARGO = 0.15
    CUELLOS = ["Tortuga", "Alto", "Redondo"]
    NIVELES = ["Bajo", "Medio", "Alto"]

    def __init__(self, codigo, nombre, talla, precio_base, stock, tipo_cuello, nivel_termico):
        super().__init__(codigo, nombre, talla, precio_base, stock)
        self._tipo_cuello = _validar_opcion(tipo_cuello, self.CUELLOS, "El tipo de cuello")
        self._nivel_termico = _validar_opcion(nivel_termico, self.NIVELES, "El nivel térmico")

    def calcular_precio_final(self, cantidad: int = 1) -> int:
        return round(self.precio_base * (1 + self.RECARGO)) * cantidad

    def obtener_tipo(self) -> str:
        return self.TIPO

    def detalle(self) -> str:
        return f"Cuello {self._tipo_cuello}, retención {self._nivel_termico}"

    def a_dict(self) -> dict:
        datos = super().a_dict()
        datos["tipo_cuello"] = self._tipo_cuello
        datos["nivel_termico"] = self._nivel_termico
        return datos


class PrendaEstandar(Prenda):
    """Poleras básicas. Tienen descuento si se compra sobre el umbral de unidades."""

    TIPO = "Estándar"
    UMBRAL_VOLUMEN = 5
    DESCUENTO_VOLUMEN = 0.10
    MANGAS = ["Corta", "Larga"]

    def __init__(self, codigo, nombre, talla, precio_base, stock, tipo_manga):
        super().__init__(codigo, nombre, talla, precio_base, stock)
        self._tipo_manga = _validar_opcion(tipo_manga, self.MANGAS, "El tipo de manga")

    def calcular_precio_final(self, cantidad: int = 1) -> int:
        total = self.precio_base * cantidad
        if cantidad > self.UMBRAL_VOLUMEN:
            total -= round(total * self.DESCUENTO_VOLUMEN)
        return total

    def obtener_tipo(self) -> str:
        return self.TIPO

    def detalle(self) -> str:
        return f"Manga {self._tipo_manga}"

    def a_dict(self) -> dict:
        datos = super().a_dict()
        datos["tipo_manga"] = self._tipo_manga
        return datos


class RopaInterior(Prenda):
    """Primeras capas inferiores. Las tallas XL y XXL llevan recargo."""

    TIPO = "Ropa Interior"
    RECARGO_TALLA = 0.10
    TALLAS_CON_RECARGO = ["XL", "XXL"]
    ELASTICOS = ["Ancho", "Angosto"]
    AJUSTES = ["Ceñido", "Regular"]

    def __init__(self, codigo, nombre, talla, precio_base, stock, tipo_elastico, ajuste):
        super().__init__(codigo, nombre, talla, precio_base, stock)
        self._tipo_elastico = _validar_opcion(tipo_elastico, self.ELASTICOS, "El elástico")
        self._ajuste = _validar_opcion(ajuste, self.AJUSTES, "El ajuste")

    def calcular_precio_final(self, cantidad: int = 1) -> int:
        precio = self.precio_base
        if self.talla in self.TALLAS_CON_RECARGO:
            precio = round(precio * (1 + self.RECARGO_TALLA))
        return precio * cantidad

    def obtener_tipo(self) -> str:
        return self.TIPO

    def detalle(self) -> str:
        return f"Elástico {self._tipo_elastico}, ajuste {self._ajuste}"

    def a_dict(self) -> dict:
        datos = super().a_dict()
        datos["tipo_elastico"] = self._tipo_elastico
        datos["ajuste"] = self._ajuste
        return datos


# Cada tipo de prenda con su clase, para crear la correcta a partir del nombre del tipo
CLASES_PRENDA = {
    PrendaTermica.TIPO: PrendaTermica,
    PrendaEstandar.TIPO: PrendaEstandar,
    RopaInterior.TIPO: RopaInterior,
}


def prenda_desde_dict(datos: dict) -> Prenda:
    """Crea el objeto de la clase correcta a partir de lo guardado en JSON."""
    base = (datos["codigo"], datos["nombre"], datos["talla"], datos["precio_base"], datos["stock"])
    if datos["tipo"] == PrendaTermica.TIPO:
        return PrendaTermica(*base, datos["tipo_cuello"], datos["nivel_termico"])
    if datos["tipo"] == PrendaEstandar.TIPO:
        return PrendaEstandar(*base, datos["tipo_manga"])
    if datos["tipo"] == RopaInterior.TIPO:
        return RopaInterior(*base, datos["tipo_elastico"], datos["ajuste"])
    raise ValueError(f"Tipo de prenda desconocido: {datos['tipo']}")
