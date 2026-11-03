"""
Usuarios del sistema.

Conceptos POO: clase abstracta, herencia, encapsulamiento y polimorfismo.

Usuario (abstracta)
├── Cliente
└── Empleado (abstracta, puede iniciar sesión)
    ├── Administrador
    └── Vendedor
"""

import hashlib
import re
from abc import ABC, abstractmethod

from .validaciones import validar_correo, validar_nombre, validar_rut, validar_telefono


class Usuario(ABC):
    """Datos comunes de cualquier persona registrada en el sistema."""

    def __init__(self, rut: str, nombre: str):
        self._rut = validar_rut(rut)
        self.nombre = nombre  # Usa el setter para validar

    @property
    def rut(self) -> str:
        return self._rut

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str):
        self._nombre = validar_nombre(valor)

    @abstractmethod
    def obtener_rol(self) -> str:
        """Cada clase hija indica su rol en el negocio."""

    @abstractmethod
    def a_dict(self) -> dict:
        """Retorna los datos del objeto para guardarlos en JSON."""


class Cliente(Usuario):
    """Persona que compra en la tienda."""

    def __init__(self, rut: str, nombre: str, telefono: str, correo: str):
        super().__init__(rut, nombre)
        self.telefono = telefono
        self.correo = correo

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str):
        self._telefono = validar_telefono(valor)

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor: str):
        self._correo = validar_correo(valor)

    def obtener_rol(self) -> str:
        return "Cliente"

    def a_dict(self) -> dict:
        return {
            "rut": self.rut,
            "nombre": self.nombre,
            "telefono": self.telefono,
            "correo": self.correo,
        }

    @staticmethod
    def desde_dict(datos: dict) -> "Cliente":
        return Cliente(datos["rut"], datos["nombre"], datos["telefono"], datos["correo"])


class Empleado(Usuario):
    """Persona que puede iniciar sesión. La clave se guarda encriptada, nunca en texto simple."""

    def __init__(self, rut: str, nombre: str, usuario: str, clave: str):
        super().__init__(rut, nombre)
        limpio = usuario.strip().lower()
        if not re.fullmatch(r"[a-z0-9_]{3,20}", limpio):
            raise ValueError("El usuario debe tener de 3 a 20 letras o números, sin espacios.")
        self._usuario = limpio
        self.cambiar_clave(clave)

    @property
    def usuario(self) -> str:
        return self._usuario

    @staticmethod
    def _encriptar(clave: str) -> str:
        return hashlib.sha256(clave.encode("utf-8")).hexdigest()

    def cambiar_clave(self, clave: str) -> None:
        if len(clave) < 6 or not clave.strip():
            raise ValueError("La clave debe tener al menos 6 caracteres.")
        self._clave_hash = self._encriptar(clave)

    def verificar_clave(self, clave: str) -> bool:
        return self._clave_hash == self._encriptar(clave)

    @abstractmethod
    def puede_administrar(self) -> bool:
        """Indica si puede gestionar el inventario y los usuarios."""

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
        clases = {"Administrador": Administrador, "Vendedor": Vendedor}
        # La clave temporal se reemplaza de inmediato por el hash guardado
        empleado = clases[datos["rol"]](datos["rut"], datos["nombre"], datos["usuario"], "temporal")
        empleado._clave_hash = datos["clave_hash"]
        return empleado


class Administrador(Empleado):
    """La dueña: gestiona ventas, clientes, inventario y usuarios."""

    def obtener_rol(self) -> str:
        return "Administrador"

    def puede_administrar(self) -> bool:
        return True


class Vendedor(Empleado):
    """Atiende en el local: gestiona ventas y clientes."""

    def obtener_rol(self) -> str:
        return "Vendedor"

    def puede_administrar(self) -> bool:
        return False
