"""
Controlador de usuarios: inicio de sesión y administración de empleados.
"""

# math.ceil redondea hacia arriba; time.time() entrega la hora actual en segundos.
import math
import time

# Los controladores usan las clases del modelo para crear y manipular objetos.
from models.usuario import Administrador, Empleado, Vendedor


# Constantes del bloqueo por intentos fallidos (RNF-04): es fácil encontrarlas y cambiarlas desde un solo lugar.
MAX_INTENTOS = 5  # Claves incorrectas seguidas que bloquean la cuenta
MINUTOS_BLOQUEO = 10  # Cuánto dura el bloqueo


# Reglas de los usuarios: iniciar sesión, crear empleados, cambiar claves y eliminarlos.
class ControladorUsuarios:
    # Guarda el almacén para poder leer y modificar las listas de datos. El guion bajo en _almacen indica uso interno.
    # 'reloj' es la función que entrega la hora actual. Por defecto es time.time, pero las pruebas pueden darle otra
    # para simular que pasan los 10 minutos sin esperar de verdad.
    def __init__(self, almacen, reloj=time.time):
        self._almacen = almacen
        self._reloj = reloj
        # Diccionario en memoria (se pierde al cerrar el programa). La clave es el nombre de usuario y el valor es otro
        # diccionario con 'fallidos' (intentos seguidos) y 'bloqueado_hasta' (hora de desbloqueo; 0 = no bloqueado).
        self._intentos = {}

    # Entrega una copia de la lista (list(...)). Así la pantalla puede mirarla sin modificar los datos originales.
    @property
    def usuarios(self) -> list[Empleado]:
        return list(self._almacen.usuarios)

    # Revisa usuario y clave. Si todo está bien devuelve el empleado; si no, lanza un error que la pantalla muestra.
    # Después de MAX_INTENTOS claves incorrectas seguidas, la cuenta queda bloqueada durante MINUTOS_BLOQUEO minutos.
    def iniciar_sesion(self, usuario: str, clave: str) -> Empleado:
        # strip() quita espacios y lower() pasa a minúsculas, por si la persona los escribió mal.
        nombre = usuario.strip().lower()
        ahora = self._reloj()
        # setdefault entrega el estado de ese nombre; si no existe todavía, lo crea sin intentos y sin bloqueo.
        # Se hace igual con usuarios que no existen, para no revelar si el usuario existe o no.
        estado = self._intentos.setdefault(nombre, {"fallidos": 0, "bloqueado_hasta": 0})

        # Si todavía no llega la hora de desbloqueo, se rechaza aunque la clave sea correcta.
        if estado["bloqueado_hasta"] > ahora:
            raise ValueError(self._mensaje_bloqueo(estado["bloqueado_hasta"] - ahora))
        # Si había un bloqueo y ya pasó el tiempo, la cuenta vuelve a partir de cero.
        if estado["bloqueado_hasta"] != 0:
            estado["fallidos"] = 0
            estado["bloqueado_hasta"] = 0

        # Se busca al usuario.
        empleado = self._almacen.buscar_usuario(nombre)
        # 'is None' = no se encontró. El mensaje es el mismo en ambos casos para no revelar si el usuario existe.
        if empleado is None or not empleado.verificar_clave(clave):
            # Se cuenta un intento fallido más.
            estado["fallidos"] += 1
            # Al llegar al máximo se fija la hora de desbloqueo: ahora + minutos * 60 segundos.
            if estado["fallidos"] >= MAX_INTENTOS:
                estado["bloqueado_hasta"] = ahora + MINUTOS_BLOQUEO * 60
                raise ValueError(self._mensaje_bloqueo(MINUTOS_BLOQUEO * 60))
            raise ValueError("Usuario o clave incorrectos.")

        # Inicio de sesión correcto: el contador de fallos vuelve a cero.
        estado["fallidos"] = 0
        return empleado

    # Arma el mensaje de bloqueo. math.ceil redondea hacia arriba (si faltan 30 segundos, se muestra 1 minuto).
    def _mensaje_bloqueo(self, segundos: float) -> str:
        minutos = math.ceil(segundos / 60)
        return f"Cuenta bloqueada por demasiados intentos fallidos. Intente nuevamente en {minutos} minuto(s)."

    # Crea un empleado nuevo. Al crear el objeto, el modelo ya valida RUT, nombre, usuario y clave.
    def crear_usuario(self, rol: str, rut: str, nombre: str, usuario: str, clave: str) -> Empleado:
        # Relaciona el texto del rol con su clase.
        clases = {"Administrador": Administrador, "Vendedor": Vendedor}
        # Si el rol no es ninguno de los dos, se rechaza.
        if rol not in clases:
            raise ValueError("Debe seleccionar un rol.")
        # Crea el objeto. Si algún dato es inválido, el modelo lanza ValueError y la función se detiene aquí.
        nuevo = clases[rol](rut, nombre, usuario, clave)
        # Regla del negocio: no puede haber dos usuarios con el mismo nombre de usuario.
        if self._almacen.buscar_usuario(nuevo.usuario):
            raise ValueError(f"El usuario '{nuevo.usuario}' ya existe.")
        # any(...) es verdadero si al menos un usuario ya tiene ese RUT.
        if any(e.rut == nuevo.rut for e in self._almacen.usuarios):
            raise ValueError(f"Ya existe un usuario con el RUT {nuevo.rut}.")
        # append agrega el elemento al final de la lista. Después se guarda la lista en el JSON.
        self._almacen.usuarios.append(nuevo)
        self._almacen.guardar("usuarios")
        return nuevo

    # Cambia la clave de un usuario; el modelo valida el largo y la guarda encriptada.
    def cambiar_clave(self, usuario: str, clave: str) -> None:
        self._almacen.buscar_usuario(usuario).cambiar_clave(clave)
        self._almacen.guardar("usuarios")

    # Elimina un usuario, salvo el que tiene la sesión abierta (así nunca se queda el sistema sin quien administre).
    def eliminar_usuario(self, usuario: str, sesion_actual: Empleado) -> None:
        empleado = self._almacen.buscar_usuario(usuario)
        if empleado.usuario == sesion_actual.usuario:
            raise ValueError("No puede eliminar su propio usuario mientras tiene la sesión abierta.")
        # remove quita ese elemento de la lista.
        self._almacen.usuarios.remove(empleado)
        self._almacen.guardar("usuarios")
