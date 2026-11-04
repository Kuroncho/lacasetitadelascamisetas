"""
Controlador de usuarios: inicio de sesión y administración de empleados.
"""

# Los controladores usan las clases del modelo para crear y manipular objetos.
from models.usuario import Administrador, Empleado, Vendedor


# Reglas de los usuarios: iniciar sesión, crear empleados, cambiar claves y eliminarlos.
class ControladorUsuarios:
    # Guarda el almacén para poder leer y modificar las listas de datos. El guion bajo en _almacen indica uso interno.
    def __init__(self, almacen):
        self._almacen = almacen

    # Entrega una copia de la lista (list(...)). Así la pantalla puede mirarla sin modificar los datos originales.
    @property
    def usuarios(self) -> list[Empleado]:
        return list(self._almacen.usuarios)

    # Revisa usuario y clave. Si todo está bien devuelve el empleado; si no, lanza un error que la pantalla muestra.
    def iniciar_sesion(self, usuario: str, clave: str) -> Empleado:
        # Se busca al usuario. strip() quita espacios y lower() pasa a minúsculas, por si la persona los escribió mal.
        empleado = self._almacen.buscar_usuario(usuario.strip().lower())
        # 'is None' = no se encontró. El mensaje es el mismo en ambos casos para no revelar si el usuario existe.
        if empleado is None or not empleado.verificar_clave(clave):
            raise ValueError("Usuario o clave incorrectos.")
        return empleado

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
