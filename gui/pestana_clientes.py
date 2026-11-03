"""
Pestaña para registrar clientes y consultar su historial de compras.
"""

import tkinter as tk
from tkinter import messagebox

from gui import colores
from gui.componentes import (
    FUENTE,
    crear_boton,
    crear_etiqueta,
    crear_tabla,
    crear_tarjeta,
    fila_seleccionada,
    llenar_tabla,
)
from models.validaciones import formato_clp


class PestanaClientes(tk.Frame):
    def __init__(self, padre, tienda):
        super().__init__(padre, bg=colores.BG_VENTANA, padx=12, pady=12)
        self.tienda = tienda

        tarjeta = crear_tarjeta(self, "Datos del cliente")
        tarjeta.pack(fill="x", pady=(0, 10))

        formulario = tk.Frame(tarjeta, bg=colores.BG_TARJETA)
        formulario.pack(fill="x")
        self.campos = {}
        for fila, (clave, titulo) in enumerate([
            ("rut", "RUT:"), ("nombre", "Nombre:"), ("telefono", "Teléfono:"), ("correo", "Correo:"),
        ]):
            crear_etiqueta(formulario, titulo).grid(row=fila, column=0, sticky="w", pady=2)
            self.campos[clave] = tk.Entry(formulario, font=FUENTE, width=34)
            self.campos[clave].grid(row=fila, column=1, padx=8, pady=2)

        botones = tk.Frame(tarjeta, bg=colores.BG_TARJETA)
        botones.pack(fill="x", pady=(8, 0))
        crear_boton(botones, "Registrar", self.registrar, "VERDE").pack(side="left")
        crear_boton(botones, "Guardar cambios", self.actualizar, "AZUL").pack(side="left", padx=8)
        crear_boton(botones, "Eliminar", self.eliminar, "ROSA").pack(side="left")

        tarjeta = crear_tarjeta(self, "Clientes registrados")
        tarjeta.pack(fill="both", expand=True, pady=(0, 10))
        marco, self.tabla = crear_tabla(
            tarjeta, [("RUT", 110), ("Nombre", 220), ("Teléfono", 130), ("Correo", 220), ("Beneficio", 130)], altura=7,
        )
        marco.pack(fill="both", expand=True)
        self.tabla.bind("<<TreeviewSelect>>", lambda evento: self.mostrar_seleccionado())

        tarjeta = crear_tarjeta(self, "Historial de compras del cliente seleccionado")
        tarjeta.pack(fill="both", expand=True)
        marco, self.tabla_historial = crear_tabla(
            tarjeta, [("Folio", 70), ("Fecha", 150), ("Estado", 110), ("Total", 100)], altura=5,
        )
        marco.pack(fill="both", expand=True)

        self.refrescar()

    def refrescar(self):
        filas = []
        for cliente in self.tienda.clientes:
            beneficio = "Cliente frecuente" if self.tienda.es_cliente_frecuente(cliente.rut) else "-"
            filas.append((cliente.rut, (cliente.rut, cliente.nombre, cliente.telefono, cliente.correo, beneficio)))
        llenar_tabla(self.tabla, filas)
        self._mostrar_historial()

    def _mostrar_historial(self):
        rut = fila_seleccionada(self.tabla)
        ventas = self.tienda.historial_cliente(rut) if rut else []
        llenar_tabla(self.tabla_historial, [
            (str(v.folio), (v.folio, v.fecha.strftime("%d-%m-%Y %H:%M"), v.estado, formato_clp(v.calcular_total())))
            for v in ventas
        ])

    def mostrar_seleccionado(self):
        """Copia los datos del cliente seleccionado al formulario."""
        cliente = self.tienda.buscar_cliente(fila_seleccionada(self.tabla))
        if cliente:
            for clave in self.campos:
                self.campos[clave].delete(0, tk.END)
                self.campos[clave].insert(0, getattr(cliente, clave))
        self._mostrar_historial()

    def _limpiar_formulario(self):
        for campo in self.campos.values():
            campo.delete(0, tk.END)

    def _datos_formulario(self):
        return [self.campos[clave].get() for clave in ("rut", "nombre", "telefono", "correo")]

    def registrar(self):
        try:
            self.tienda.registrar_cliente(*self._datos_formulario())
        except ValueError as error:
            messagebox.showerror("Dato inválido", str(error))
            return
        self.tabla.selection_remove(*self.tabla.selection())
        self._limpiar_formulario()
        self.refrescar()
        messagebox.showinfo("Cliente registrado", "El cliente se registró correctamente.")

    def actualizar(self):
        rut = fila_seleccionada(self.tabla)
        if rut is None:
            messagebox.showinfo("Atención", "Seleccione un cliente de la tabla.")
            return
        try:
            datos = self._datos_formulario()
            if self.tienda.buscar_cliente(rut).rut != datos[0].replace(".", "").strip().upper():
                raise ValueError("El RUT de un cliente no se puede cambiar.")
            self.tienda.actualizar_cliente(*datos)
        except ValueError as error:
            messagebox.showerror("Dato inválido", str(error))
            return
        self.refrescar()
        messagebox.showinfo("Cliente actualizado", "Los cambios se guardaron correctamente.")

    def eliminar(self):
        rut = fila_seleccionada(self.tabla)
        if rut is None:
            messagebox.showinfo("Atención", "Seleccione un cliente de la tabla.")
            return
        if not messagebox.askyesno("Eliminar cliente", "¿Desea eliminar este cliente?"):
            return
        try:
            self.tienda.eliminar_cliente(rut)
        except ValueError as error:
            messagebox.showerror("No se pudo eliminar", str(error))
            return
        self._limpiar_formulario()
        self.refrescar()
