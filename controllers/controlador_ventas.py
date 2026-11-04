"""
Controlador de ventas: arma el carro, cobra, entrega y cancela.
"""

# Los dos errores propios del negocio.
from models.excepciones import PagoRechazadoException, SinStockException
from models.pago import Efectivo, MedioPago, TarjetaDebito, Transferencia
from models.usuario import Empleado
from models.validaciones import texto_a_entero
from models.venta import EstadoVenta, Venta

# Constantes de las reglas del negocio: es fácil encontrarlas y cambiarlas desde un solo lugar.
FOLIO_INICIAL = 1001
COMPRAS_CLIENTE_FRECUENTE = 3  # Compras necesarias para tener el beneficio
DESCUENTO_CLIENTE_FRECUENTE = 5  # Porcentaje de descuento


# Reglas de las ventas: armar el carro, cobrar, entregar y cancelar.
class ControladorVentas:
    def __init__(self, almacen):
        self._almacen = almacen

    # Copia de la lista de ventas, solo para mostrar.
    @property
    def ventas(self) -> list[Venta]:
        return list(self._almacen.ventas)

    # Busca una venta por su folio.
    def buscar_venta(self, folio: int) -> Venta | None:
        return self._almacen.buscar_venta(folio)

    # Todas las compras de un cliente.
    def historial_cliente(self, rut: str) -> list[Venta]:
        return self._almacen.ventas_de(rut)

    # Un cliente es frecuente si tiene 3 o más compras que no estén canceladas.
    def es_cliente_frecuente(self, rut: str) -> bool:
        # Comprensión de listas: arma una lista nueva con las ventas que cumplan la condición (ver GUIA_DE_SINTAXIS.md).
        compras = [v for v in self.historial_cliente(rut) if v.estado != EstadoVenta.CANCELADA]
        return len(compras) >= COMPRAS_CLIENTE_FRECUENTE

    # --- Armar la venta ---
    # Crea un carro vacío a nombre del empleado que tiene la sesión abierta.
    def nueva_venta(self, empleado: Empleado) -> Venta:
        return Venta(empleado.nombre)

    # Asocia el cliente a la venta y le aplica el descuento si es cliente frecuente.
    def asignar_cliente(self, venta: Venta, rut: str) -> None:
        """Asocia el cliente a la venta y le aplica su beneficio si corresponde."""
        cliente = self._almacen.buscar_cliente(rut)
        if cliente is None:
            raise ValueError("El cliente de esta venta ya no existe. Seleccione otro.")
        descuento = DESCUENTO_CLIENTE_FRECUENTE if self.es_cliente_frecuente(rut) else 0
        venta.asignar_cliente(cliente, descuento)

    # Agrega unidades al carro. La cantidad llega como texto. La regla de stock la aplica la propia Venta (modelo).
    def agregar_prenda(self, venta: Venta, codigo: str, cantidad: str) -> None:
        """Agrega unidades al carro. La cantidad llega como texto, tal como se escribió."""
        prenda = self._almacen.buscar_prenda(codigo)
        if prenda is None:
            raise ValueError("La prenda seleccionada ya no existe.")
        venta.agregar_prenda(prenda, texto_a_entero(cantidad, "La cantidad"))

    # Quita una línea del carro.
    def quitar_detalle(self, venta: Venta, indice: int) -> None:
        venta.quitar_detalle(indice)

    # Deja el carro sin prendas.
    def vaciar(self, venta: Venta) -> None:
        venta.vaciar()

    # --- Cobro ---
    # Crea el objeto del medio de pago elegido a partir del nombre y de lo que se escribió (monto, comprobante o dígitos).
    def crear_medio_pago(self, nombre: str, dato: str) -> MedioPago:
        """Crea el medio de pago elegido. 'dato' es lo que se escribió: monto, comprobante o dígitos."""
        if nombre == "Efectivo":
            return Efectivo(texto_a_entero(dato, "El monto recibido"))
        if nombre == "Transferencia":
            return Transferencia(dato)
        if nombre == "Tarjeta de Débito":
            return TarjetaDebito(dato)
        raise ValueError("Debe seleccionar un medio de pago.")

    # Cobra y registra la venta. Está ordenada para que, si algo falla, NO se cambie nada:
    # primero se validan todas las condiciones y recién al final se modifican los datos.
    def registrar_venta(self, venta: Venta, medio_pago: MedioPago) -> None:
        """
        Cobra y registra la venta. Primero valida todo, y solo si no hay errores
        descuenta el stock. Así una venta rechazada no cambia nada.
        """
        # Paso 1: revisar que la venta se pueda cobrar (pendiente, con prendas y con cliente).
        if venta.estado != EstadoVenta.PENDIENTE:
            raise ValueError("Esta venta ya fue procesada.")
        if not venta.detalles:
            raise ValueError("La venta no tiene prendas.")
        if not venta.cliente_rut:
            raise ValueError("Debe seleccionar un cliente.")
        # Se vuelve a asignar el cliente por si cambió su condición de frecuente o sus datos con el carro abierto.
        self.asignar_cliente(venta, venta.cliente_rut)  # Por si cambiaron sus datos con el carro abierto

        # Se revisa de nuevo porque el inventario pudo cambiar desde que se armó el carro
        # Paso 2: revisar el stock otra vez. Mientras se armaba el carro alguien pudo vender o eliminar esa prenda.
        for detalle in venta.detalles:
            prenda = self._almacen.buscar_prenda(detalle.codigo)
            if prenda is None:
                raise SinStockException(f"La prenda {detalle.descripcion} ya no existe en el inventario.")
            if detalle.cantidad > prenda.stock:
                raise SinStockException(f"Stock insuficiente de {prenda.descripcion}. Disponibles: {prenda.stock}.")

        # Paso 3: cobrar. Si el pago falla se lanza una excepción y la función termina aquí: no se ha descontado nada todavía.
        comprobante = medio_pago.procesar_pago(venta.calcular_total())
        # En transferencias el mismo comprobante no puede usarse en dos ventas.
        if medio_pago.COMPROBANTE_UNICO and any(v.comprobante == comprobante for v in self._almacen.ventas):
            raise PagoRechazadoException("Ese comprobante ya fue usado en otra venta.")

        # Paso 4: con todo validado y cobrado, recién ahora se descuenta el stock.
        for detalle in venta.detalles:
            self._almacen.buscar_prenda(detalle.codigo).descontar_stock(detalle.cantidad)

        # El folio es el mayor folio existente más 1. 'default=' se usa cuando todavía no hay ventas.
        folio = max((v.folio for v in self._almacen.ventas), default=FOLIO_INICIAL - 1) + 1
        # Paso 5: la venta pasa a PAGADA y se agrega a la lista.
        venta.marcar_pagada(folio, medio_pago.obtener_nombre(), comprobante)
        self._almacen.ventas.append(venta)
        # Paso 6: se guardan en JSON el stock nuevo y la venta.
        self._almacen.guardar("prendas")
        self._almacen.guardar("ventas")

    # --- Después del cobro ---
    # Marca la venta como entregada (el modelo exige que esté pagada).
    def entregar_venta(self, folio: int) -> None:
        self._almacen.buscar_venta(folio).marcar_entregada()
        self._almacen.guardar("ventas")

    # Cancela una venta pagada que no se entregó y devuelve las unidades al inventario.
    def cancelar_venta(self, folio: int) -> None:
        """Cancela una venta pagada y devuelve las unidades al inventario."""
        venta = self._almacen.buscar_venta(folio)
        venta.marcar_cancelada()
        for detalle in venta.detalles:
            self._almacen.buscar_prenda(detalle.codigo).reponer_stock(detalle.cantidad)
        self._almacen.guardar("prendas")
        self._almacen.guardar("ventas")
