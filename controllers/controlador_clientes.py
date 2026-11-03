"""
Controlador de clientes: registrar, editar y eliminar.
"""

from models.usuario import Cliente


class ControladorClientes:
    def __init__(self, almacen):
        self._almacen = almacen

    @property
    def clientes(self) -> list[Cliente]:
        return list(self._almacen.clientes)

    def buscar(self, rut: str) -> Cliente | None:
        return self._almacen.buscar_cliente(rut)

    def registrar(self, rut: str, nombre: str, telefono: str, correo: str) -> Cliente:
        nuevo = Cliente(rut, nombre, telefono, correo)
        if self._almacen.buscar_cliente(nuevo.rut):
            raise ValueError(f"Ya existe un cliente con el RUT {nuevo.rut}.")
        self._almacen.clientes.append(nuevo)
        self._almacen.guardar("clientes")
        return nuevo

    def actualizar(self, rut_actual: str, rut: str, nombre: str, telefono: str, correo: str) -> None:
        # Se valida con un objeto temporal para no dejar el cliente a medio cambiar
        validado = Cliente(rut, nombre, telefono, correo)
        if validado.rut != rut_actual:
            raise ValueError("El RUT de un cliente no se puede cambiar.")
        cliente = self._almacen.buscar_cliente(rut_actual)
        cliente.nombre = validado.nombre
        cliente.telefono = validado.telefono
        cliente.correo = validado.correo
        self._almacen.guardar("clientes")

    def eliminar(self, rut: str) -> None:
        if self._almacen.ventas_de(rut):
            raise ValueError("No se puede eliminar un cliente que tiene compras registradas.")
        self._almacen.clientes.remove(self._almacen.buscar_cliente(rut))
        self._almacen.guardar("clientes")
