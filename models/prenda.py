"""
Catálogo de prendas.

Conceptos POO: clase abstracta, herencia y polimorfismo. Cada tipo de prenda
calcula su precio final con su propia regla en calcular_precio_final().
"""

# ABC y abstractmethod: ver models/usuario.py. Prenda es una plantilla y cada tipo de prenda calcula su precio a su manera.
from abc import ABC, abstractmethod

# Importa el error propio que se lanza cuando se pide más cantidad de la que hay.
from .excepciones import SinStockException
from .validaciones import validar_entero

# Una lista ([ ]) con las tallas permitidas. Es la única fuente de verdad: el formulario y las validaciones la usan.
TALLAS = ["S", "M", "L", "XL", "XXL"]


# Función auxiliar (el guion bajo indica que es de uso interno de este archivo).
# 'in' revisa si un valor está dentro de una lista; 'not in' es lo contrario.
def _validar_opcion(valor: str, opciones: list[str], nombre: str) -> str:
    if valor not in opciones:
        # ', '.join(opciones) une la lista en un solo texto separado por comas.
        raise ValueError(f"{nombre} debe ser una de estas opciones: {', '.join(opciones)}.")
    return valor


# Plantilla común de todas las prendas: código, nombre, talla, precio y stock.
# No se puede crear una 'Prenda' directamente, solo sus hijas (térmica, estándar, ropa interior).
class Prenda(ABC):
    """Atributos y comportamiento común de todas las prendas."""

    # Constructor: se ejecuta al crear una prenda y valida cada dato antes de guardarlo.
    def __init__(self, codigo: str, nombre: str, talla: str, precio_base: int, stock: int):
        # El código siempre se guarda en mayúsculas y sin espacios en los bordes ('est-001' pasa a 'EST-001').
        limpio = codigo.strip().upper()
        # 'not limpio' es verdadero si el texto está vacío. Tampoco se permiten espacios dentro del código.
        if not limpio or " " in limpio:
            raise ValueError("El código no puede estar vacío ni tener espacios.")
        if len(nombre.strip()) < 2:
            raise ValueError("El nombre de la prenda debe tener al menos 2 caracteres.")
        self._codigo = limpio
        # capitalize() deja solo la primera letra en mayúscula.
        self._nombre = nombre.strip().capitalize()
        self._talla = _validar_opcion(talla, TALLAS, "La talla")
        # Sin guion bajo: usa el setter de más abajo, que valida el precio. Lo mismo ocurre con el stock.
        self.precio_base = precio_base
        self.stock = stock

    # @property: se usa como prenda.codigo (sin paréntesis). Es de solo lectura: el código no se puede cambiar.
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

    # Setter: el precio debe ser un entero de al menos 1.
    @precio_base.setter
    def precio_base(self, valor: int):
        self._precio_base = validar_entero(valor, "El precio", minimo=1)

    @property
    def stock(self) -> int:
        return self._stock

    # Setter: el stock debe ser un entero de 0 o más. Así es imposible dejarlo negativo.
    @stock.setter
    def stock(self, valor: int):
        self._stock = validar_entero(valor, "El stock", minimo=0)

    # Texto corto para mostrar la prenda, por ejemplo 'Beatle (Talla M)'.
    @property
    def descripcion(self) -> str:
        return f"{self._nombre} (Talla {self._talla})"

    # Resta unidades al vender. Si se pide más de lo que hay, lanza SinStockException y no cambia nada.
    def descontar_stock(self, cantidad: int) -> None:
        if cantidad > self._stock:
            raise SinStockException(f"Stock insuficiente de {self.descripcion}. Disponibles: {self._stock}.")
        self.stock = self._stock - cantidad

    # Suma unidades de vuelta (por ejemplo al cancelar una venta).
    def reponer_stock(self, cantidad: int) -> None:
        self.stock = self._stock + cantidad

    # POLIMORFISMO: este método existe en todas las prendas pero cada tipo lo hace distinto.
    # Aquí no tiene código: cada hija escribe su propia regla de precio.
    @abstractmethod
    def calcular_precio_final(self, cantidad: int = 1) -> int:
        """Retorna el precio total de comprar esa cantidad, con las reglas del tipo de prenda."""

    # Abstracto: cada hija devuelve su nombre de tipo.
    @abstractmethod
    def obtener_tipo(self) -> str:
        """Retorna el nombre del tipo de prenda."""

    # Abstracto: cada hija devuelve un texto con sus características propias.
    @abstractmethod
    def detalle(self) -> str:
        """Retorna las características propias del tipo de prenda."""

    # Datos comunes en formato diccionario, para guardar en el JSON.
    def a_dict(self) -> dict:
        return {
            "tipo": self.obtener_tipo(),
            "codigo": self.codigo,
            "nombre": self.nombre,
            "talla": self.talla,
            "precio_base": self.precio_base,
            "stock": self.stock,
        }


# Prenda térmica (beatles y camisetas de invierno): su precio lleva un recargo fijo.
class PrendaTermica(Prenda):
    """Camisetas de invierno y beatles. Su precio lleva un recargo fijo."""

    # Variables de clase: valores compartidos por todas las prendas de este tipo (no cambian de una a otra).
    TIPO = "Térmica"
    RECARGO = 0.15
    CUELLOS = ["Tortuga", "Alto", "Redondo"]
    NIVELES = ["Bajo", "Medio", "Alto"]

    # Recibe los datos comunes y, además, los propios de la prenda térmica.
    def __init__(self, codigo, nombre, talla, precio_base, stock, tipo_cuello, nivel_termico):
        # Llama al constructor de Prenda (la clase padre) para guardar los datos comunes.
        super().__init__(codigo, nombre, talla, precio_base, stock)
        self._tipo_cuello = _validar_opcion(tipo_cuello, self.CUELLOS, "El tipo de cuello")
        self._nivel_termico = _validar_opcion(nivel_termico, self.NIVELES, "El nivel térmico")

    # Regla térmica: precio base + 15% de recargo, por la cantidad. round() redondea al entero más cercano.
    def calcular_precio_final(self, cantidad: int = 1) -> int:
        return round(self.precio_base * (1 + self.RECARGO)) * cantidad

    # Devuelve el tipo de esta prenda.
    def obtener_tipo(self) -> str:
        return self.TIPO

    # Características propias de la térmica.
    def detalle(self) -> str:
        return f"Cuello {self._tipo_cuello}, retención {self._nivel_termico}"

    # Primero toma los datos comunes del padre (super) y luego agrega los propios.
    def a_dict(self) -> dict:
        datos = super().a_dict()
        datos["tipo_cuello"] = self._tipo_cuello
        datos["nivel_termico"] = self._nivel_termico
        return datos


# Poleras básicas: tienen descuento si se compran más unidades que el umbral.
class PrendaEstandar(Prenda):
    """Poleras básicas. Tienen descuento si se compra sobre el umbral de unidades."""

    TIPO = "Estándar"
    UMBRAL_VOLUMEN = 5
    DESCUENTO_VOLUMEN = 0.10
    MANGAS = ["Corta", "Larga"]

    def __init__(self, codigo, nombre, talla, precio_base, stock, tipo_manga):
        super().__init__(codigo, nombre, talla, precio_base, stock)
        self._tipo_manga = _validar_opcion(tipo_manga, self.MANGAS, "El tipo de manga")

    # Regla estándar: si se compran más de 5 unidades se descuenta el 10%.
    # 'total -= x' es lo mismo que 'total = total - x'.
    def calcular_precio_final(self, cantidad: int = 1) -> int:
        total = self.precio_base * cantidad
        if cantidad > self.UMBRAL_VOLUMEN:
            total -= round(total * self.DESCUENTO_VOLUMEN)
        return total

    # Devuelve el tipo de esta prenda.
    def obtener_tipo(self) -> str:
        return self.TIPO

    # Características propias de la estándar.
    def detalle(self) -> str:
        return f"Manga {self._tipo_manga}"

    # Datos comunes más el tipo de manga.
    def a_dict(self) -> dict:
        datos = super().a_dict()
        datos["tipo_manga"] = self._tipo_manga
        return datos


# Ropa interior de abrigo: las tallas XL y XXL llevan recargo.
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

    # Regla de ropa interior: si la talla está en la lista de tallas con recargo, el precio sube 10%.
    def calcular_precio_final(self, cantidad: int = 1) -> int:
        precio = self.precio_base
        if self.talla in self.TALLAS_CON_RECARGO:
            precio = round(precio * (1 + self.RECARGO_TALLA))
        return precio * cantidad

    # Devuelve el tipo de esta prenda.
    def obtener_tipo(self) -> str:
        return self.TIPO

    # Características propias de la ropa interior.
    def detalle(self) -> str:
        return f"Elástico {self._tipo_elastico}, ajuste {self._ajuste}"

    # Datos comunes más elástico y ajuste.
    def a_dict(self) -> dict:
        datos = super().a_dict()
        datos["tipo_elastico"] = self._tipo_elastico
        datos["ajuste"] = self._ajuste
        return datos


# Cada tipo de prenda con su clase, para crear la correcta a partir del nombre del tipo
# Diccionario ({clave: valor}) que relaciona el nombre de un tipo con su clase. Sirve para crear la prenda correcta a partir de un texto.
CLASES_PRENDA = {
    PrendaTermica.TIPO: PrendaTermica,
    PrendaEstandar.TIPO: PrendaEstandar,
    RopaInterior.TIPO: RopaInterior,
}


# Hace lo contrario de a_dict: lee los datos guardados en el JSON y crea la prenda del tipo que corresponda.
def prenda_desde_dict(datos: dict) -> Prenda:
    """Crea el objeto de la clase correcta a partir de lo guardado en JSON."""
    # Tupla (una lista que no cambia) con los datos comunes.
    base = (datos["codigo"], datos["nombre"], datos["talla"], datos["precio_base"], datos["stock"])
    # '==' compara si dos valores son iguales. El asterisco en *base reparte los elementos de la tupla como argumentos separados.
    if datos["tipo"] == PrendaTermica.TIPO:
        return PrendaTermica(*base, datos["tipo_cuello"], datos["nivel_termico"])
    if datos["tipo"] == PrendaEstandar.TIPO:
        return PrendaEstandar(*base, datos["tipo_manga"])
    if datos["tipo"] == RopaInterior.TIPO:
        return RopaInterior(*base, datos["tipo_elastico"], datos["ajuste"])
    raise ValueError(f"Tipo de prenda desconocido: {datos['tipo']}")
