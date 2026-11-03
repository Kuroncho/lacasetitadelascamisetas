"""
Controlador de usuarios: inicio de sesión y administración de empleados.
"""

from models.usuario import Administrador, Empleado, Vendedor


class ControladorUsuarios:
    def __init__(self, almacen):
        self._almacen = almacen

    @property
    def usuarios(self) -> list[Empleado]:
        return list(self._almacen.usuarios)

    def iniciar_sesion(self, usuario: str, clave: str) -> Empleado:
        empleado = self._almacen.buscar_usuario(usuario.strip().lower())
        if empleado is None or not empleado.verificar_clave(clave):
            raise ValueError("Usuario o clave incorrectos.")
        return empleado

    def crear_usuario(self, rol: str, rut: str, nombre: str, usuario: str, clave: str) -> Empleado:
        clases = {"Administrador": Administrador, "Vendedor": Vendedor}
        if rol not in clases:
            raise ValueError("Debe seleccionar un rol.")
        nuevo = clases[rol](rut, nombre, usuario, clave)
        if self._almacen.buscar_usuario(nuevo.usuario):
            raise ValueError(f"El usuario '{nuevo.usuario}' ya existe.")
        if any(e.rut == nuevo.rut for e in self._almacen.usuarios):
            raise ValueError(f"Ya existe un usuario con el RUT {nuevo.rut}.")
        self._almacen.usuarios.append(nuevo)
        self._almacen.guardar("usuarios")
        return nuevo

    def cambiar_clave(self, usuario: str, clave: str) -> None:
        self._almacen.buscar_usuario(usuario).cambiar_clave(clave)
        self._almacen.guardar("usuarios")

    def eliminar_usuario(self, usuario: str, sesion_actual: Empleado) -> None:
        empleado = self._almacen.buscar_usuario(usuario)
        if empleado.usuario == sesion_actual.usuario:
            raise ValueError("No puede eliminar su propio usuario mientras tiene la sesión abierta.")
        self._almacen.usuarios.remove(empleado)
        self._almacen.guardar("usuarios")
