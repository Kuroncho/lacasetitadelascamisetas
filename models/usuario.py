"""
Usuarios del sistema.

Conceptos POO: clase abstracta, herencia, encapsulamiento y polimorfismo.

Usuario (abstracta)
├── Cliente
└── Empleado (abstracta, puede iniciar sesión)
    ├── Administrador
    └── Vendedor
"""

# Cada 'import' trae herramientas desde otro lugar. hashlib sirve para encriptar la clave:
# convertirla en un texto ilegible que no se puede devolver al original.
import hashlib
import re
# ABC significa "clase abstracta": una plantilla que no se puede usar directamente, solo sirve
# para que otras clases la hereden. 'abstractmethod' marca los métodos que cada hija está obligada a escribir.
from abc import ABC, abstractmethod

# El punto inicial significa 'desde este mismo paquete (carpeta models)'.
from .validaciones import validar_correo, validar_nombre, validar_rut, validar_telefono


# Una clase es un molde para crear objetos. Esta es la plantilla común de cualquier persona del sistema:
# guarda RUT y nombre. Las clases Cliente y Empleado la heredan (reciben todo lo que tiene).
class Usuario(ABC):
    """Datos comunes de cualquier persona registrada en el sistema."""

    # __init__ se ejecuta solo, una vez, cuando se crea un objeto (por ejemplo Cliente(...)).
    # 'self' es el propio objeto: lo que se guarda en 'self.algo' queda dentro de él.
    # ': str' indica qué tipo de dato se espera; es solo una guía para quien lee, Python no lo exige.
    def __init__(self, rut: str, nombre: str):
        # El guion bajo inicial (_rut) es una señal entre programadores: "este dato es interno, no lo toques desde afuera".
        # Antes de guardar, validar_rut revisa que el RUT sea correcto.
        self._rut = validar_rut(rut)
        # Sin guion bajo: esto pasa por el 'setter' de más abajo (def nombre(self, valor)), que valida el nombre.
        self.nombre = nombre  # Usa el setter para validar

    # @property convierte un método en un dato de solo lectura: se usa como cliente.rut (sin paréntesis).
    # Así otras partes del programa pueden leer el RUT pero no cambiarlo por accidente.
    @property
    def rut(self) -> str:
        return self._rut

    # Getter: entrega el nombre guardado.
    @property
    def nombre(self) -> str:
        return self._nombre

    # Setter: se ejecuta cuando alguien escribe cliente.nombre = "algo". Antes de guardarlo lo valida,
    # así es imposible dejar un nombre inválido (por ejemplo vacío o con números).
    @nombre.setter
    def nombre(self, valor: str):
        self._nombre = validar_nombre(valor)

    # @abstractmethod: este método no tiene código aquí. Cada clase hija está obligada a escribirlo
    # con su propia versión. Python no deja crear objetos si falta alguno.
    @abstractmethod
    def obtener_rol(self) -> str:
        """Cada clase hija indica su rol en el negocio."""

    # Convierte el objeto en un diccionario ({"clave": valor}), que es el formato que se puede guardar en un archivo JSON.
    @abstractmethod
    def a_dict(self) -> dict:
        """Retorna los datos del objeto para guardarlos en JSON."""


# Cliente hereda de Usuario: ya tiene RUT y nombre, y aquí agrega teléfono y correo.
class Cliente(Usuario):
    """Persona que compra en la tienda."""

    def __init__(self, rut: str, nombre: str, telefono: str, correo: str):
        # super() es la clase padre. Esta línea ejecuta el __init__ del padre para que guarde el RUT y el nombre.
        super().__init__(rut, nombre)
        self.telefono = telefono
        self.correo = correo

    @property
    def telefono(self) -> str:
        return self._telefono

    # Setter: cada vez que se cambia el teléfono se valida el formato.
    @telefono.setter
    def telefono(self, valor: str):
        self._telefono = validar_telefono(valor)

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor: str):
        self._correo = validar_correo(valor)

    # Aquí Cliente escribe su versión del método que el padre dejó abstracto.
    def obtener_rol(self) -> str:
        return "Cliente"

    # Versión de Cliente: devuelve sus datos como diccionario.
    def a_dict(self) -> dict:
        return {
            "rut": self.rut,
            "nombre": self.nombre,
            "telefono": self.telefono,
            "correo": self.correo,
        }

    # @staticmethod: método que no necesita un objeto previo; se usa como Cliente.desde_dict(...).
    # Hace lo contrario de a_dict: crea un Cliente a partir de los datos leídos del JSON.
    @staticmethod
    def desde_dict(datos: dict) -> "Cliente":
        return Cliente(datos["rut"], datos["nombre"], datos["telefono"], datos["correo"])


# Un Empleado es un usuario que puede iniciar sesión, por eso tiene nombre de usuario y clave.
# También es abstracta: solo se usan sus hijas Administrador y Vendedor.
class Empleado(Usuario):
    """Persona que puede iniciar sesión. La clave se guarda encriptada, nunca en texto simple."""

    def __init__(self, rut: str, nombre: str, usuario: str, clave: str):
        super().__init__(rut, nombre)
        # lower() pasa a minúsculas, así 'Marisol' y 'marisol' son el mismo usuario.
        limpio = usuario.strip().lower()
        # El usuario debe tener entre 3 y 20 letras, números o guion bajo.
        if not re.fullmatch(r"[a-z0-9_]{3,20}", limpio):
            raise ValueError("El usuario debe tener de 3 a 20 letras o números, sin espacios.")
        self._usuario = limpio
        self.cambiar_clave(clave)

    @property
    def usuario(self) -> str:
        return self._usuario

    # Convierte la clave en un código con SHA-256. Es una vía de una sola dirección: de la clave se obtiene el código,
    # pero del código no se puede recuperar la clave. Por eso en el JSON nunca queda la clave real.
    @staticmethod
    def _encriptar(clave: str) -> str:
        return hashlib.sha256(clave.encode("utf-8")).hexdigest()

    # Valida el largo de la clave y guarda solo su versión encriptada.
    def cambiar_clave(self, clave: str) -> None:
        # Mínimo 6 caracteres, y no puede ser solo espacios.
        if len(clave) < 6 or not clave.strip():
            raise ValueError("La clave debe tener al menos 6 caracteres.")
        self._clave_hash = self._encriptar(clave)

    # Para revisar un inicio de sesión no se desencripta nada: se encripta lo que escribió la persona
    # y se compara con el código guardado. Devuelve True (verdadero) o False (falso).
    def verificar_clave(self, clave: str) -> bool:
        return self._clave_hash == self._encriptar(clave)

    # Abstracto: Administrador responde True y Vendedor responde False. Con eso la pantalla decide qué pestañas mostrar.
    @abstractmethod
    def puede_administrar(self) -> bool:
        """Indica si puede gestionar el inventario y los usuarios."""

    # Versión de Empleado: guarda el rol y la clave ya encriptada.
    def a_dict(self) -> dict:
        return {
            "rol": self.obtener_rol(),
            "rut": self.rut,
            "nombre": self.nombre,
            "usuario": self.usuario,
            "clave_hash": self._clave_hash,
        }

    @staticmethod
    def desde_dict(datos: dict) -> "Empleado":
        # Diccionario que relaciona un texto con una clase. Sirve para elegir la clase correcta
        # según el rol que venía guardado en el JSON.
        clases = {"Administrador": Administrador, "Vendedor": Vendedor}
        # La clave temporal se reemplaza de inmediato por el hash guardado
        # clases[rol] devuelve la clase y los paréntesis finales la ejecutan, o sea, crean el objeto.
        empleado = clases[datos["rol"]](datos["rut"], datos["nombre"], datos["usuario"], "temporal")
        # Se reemplaza la clave temporal por el código que ya estaba guardado.
        empleado._clave_hash = datos["clave_hash"]
        return empleado


# La dueña: puede administrar inventario y usuarios.
class Administrador(Empleado):
    """La dueña: gestiona ventas, clientes, inventario y usuarios."""

    def obtener_rol(self) -> str:
        return "Administrador"

    def puede_administrar(self) -> bool:
        return True


# Atiende en el local: no puede administrar.
class Vendedor(Empleado):
    """Atiende en el local: gestiona ventas y clientes."""

    def obtener_rol(self) -> str:
        return "Vendedor"

    def puede_administrar(self) -> bool:
        return False
