"""
Pestaña con todas las ventas: ver boleta, marcar como entregada o cancelar.
"""

import tkinter as tk
from tkinter import messagebox

from views import colores
# Funciones de componentes.py para crear botones, tablas, tarjetas y la ventana de boleta.
from views.componentes import (
    crear_boton,
    crear_tabla,
    crear_tarjeta,
    fila_seleccionada,
    llenar_tabla,
    mostrar_boleta,
)
from models.validaciones import formato_clp


# Pestaña con todas las ventas hechas: ver la boleta, marcar como entregada o cancelar.
class PestanaHistorial(tk.Frame):
    def __init__(self, padre, controladores):
        super().__init__(padre, bg=colores.BG_VENTANA, padx=12, pady=12)
        self.ctrl = controladores.ventas

        tarjeta = crear_tarjeta(self, "Ventas registradas")
        tarjeta.pack(fill="both", expand=True)
        marco, self.tabla = crear_tabla(tarjeta, [
            ("Folio", 70), ("Fecha", 140), ("Cliente", 200), ("Vendedor", 160),
            ("Pago", 130), ("Total", 90), ("Estado", 100),
        ], altura=18)
        marco.pack(fill="both", expand=True)

        botones = tk.Frame(tarjeta, bg=colores.BG_TARJETA)
        botones.pack(fill="x", pady=(8, 0))
        crear_boton(botones, "Ver boleta", self.ver_boleta, "AZUL").pack(side="left")
        crear_boton(botones, "Marcar entregada", self.entregar, "VERDE").pack(side="left", padx=8)
        crear_boton(botones, "Cancelar venta", self.cancelar, "ROSA").pack(side="left")

        self.refrescar()

    # Carga la tabla con las ventas. reversed(...) las muestra de la más nueva a la más antigua.
    def refrescar(self):
        llenar_tabla(self.tabla, [
            (str(v.folio), (v.folio, v.fecha.strftime("%d-%m-%Y %H:%M"), v.cliente_nombre, v.vendedor,
                            v.medio_pago, formato_clp(v.calcular_total()), v.estado))
            for v in reversed(self.ctrl.ventas)
        ])

    # Devuelve el folio de la venta seleccionada como número, o None (con aviso) si no hay selección.
    def _folio_seleccionado(self):
        fila = fila_seleccionada(self.tabla)
        if fila is None:
            messagebox.showinfo("Atención", "Seleccione una venta de la tabla.")
            return None
        return int(fila)

    # Abre la boleta de la venta seleccionada.
    def ver_boleta(self):
        folio = self._folio_seleccionado()
        if folio is not None:
            mostrar_boleta(self, self.ctrl.buscar_venta(folio))

    # Marca la venta como entregada. El modelo solo lo permite si estaba pagada.
    def entregar(self):
        folio = self._folio_seleccionado()
        if folio is None:
            return
        try:
            self.ctrl.entregar_venta(folio)
        except ValueError as error:
            messagebox.showerror("No se pudo entregar", str(error))
            return
        self.refrescar()

    # Cancela la venta y devuelve las prendas al inventario. Primero pregunta confirmación.
    def cancelar(self):
        folio = self._folio_seleccionado()
        if folio is None or not messagebox.askyesno("Cancelar venta", f"¿Desea cancelar la venta {folio} y devolver el stock?"):
            return
        try:
            self.ctrl.cancelar_venta(folio)
        except ValueError as error:
            messagebox.showerror("No se pudo cancelar", str(error))
            return
        self.refrescar()
