"""
Controlador de clientes: registrar, editar y eliminar.
"""

# Se importa la clase Cliente del modelo.
from models.usuario import Cliente


# Reglas de los clientes: registrar, editar y eliminar.
class ControladorClientes:
    # Guarda el almacén compartido.
    def __init__(self, almacen):
        self._almacen = almacen

    # Copia de la lista de clientes, solo para mostrar.
    @property
    def clientes(self) -> list[Cliente]:
        return list(self._almacen.clientes)

    # Entrega el cliente con ese RUT, o None si no existe ('| None' en la línea indica ese posible resultado).
    def buscar(self, rut: str) -> Cliente | None:
        return self._almacen.buscar_cliente(rut)

    # Crea un cliente nuevo. Si un dato es inválido el modelo lanza ValueError y no se guarda nada.
    def registrar(self, rut: str, nombre: str, telefono: str, correo: str) -> Cliente:
        nuevo = Cliente(rut, nombre, telefono, correo)
        # No puede haber dos clientes con el mismo RUT.
        if self._almacen.buscar_cliente(nuevo.rut):
            raise ValueError(f"Ya existe un cliente con el RUT {nuevo.rut}.")
        self._almacen.clientes.append(nuevo)
        self._almacen.guardar("clientes")
        return nuevo

    # Cambia los datos de un cliente. El RUT es su identificación y no se puede cambiar.
    def actualizar(self, rut_actual: str, rut: str, nombre: str, telefono: str, correo: str) -> None:
        # Se valida con un objeto temporal para no dejar el cliente a medio cambiar
        # Primero se crea un cliente temporal: si algún dato es inválido, falla aquí y el cliente real no queda a medio cambiar.
        validado = Cliente(rut, nombre, telefono, correo)
        # Si el RUT escrito es distinto al del cliente seleccionado, se rechaza.
        if validado.rut != rut_actual:
            raise ValueError("El RUT de un cliente no se puede cambiar.")
        cliente = self._almacen.buscar_cliente(rut_actual)
        cliente.nombre = validado.nombre
        cliente.telefono = validado.telefono
        cliente.correo = validado.correo
        self._almacen.guardar("clientes")

    # Un cliente con compras registradas no se puede eliminar, para no perder el historial de ventas.
    def eliminar(self, rut: str) -> None:
        if self._almacen.ventas_de(rut):
            raise ValueError("No se puede eliminar un cliente que tiene compras registradas.")
        self._almacen.clientes.remove(self._almacen.buscar_cliente(rut))
        self._almacen.guardar("clientes")
