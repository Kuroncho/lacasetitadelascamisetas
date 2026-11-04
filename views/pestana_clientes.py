"""
Pestaña para registrar clientes y consultar su historial de compras.
"""

import tkinter as tk
from tkinter import messagebox

from views import colores
# Funciones de componentes.py para crear botones, tablas y tarjetas.
from views.componentes import (
    FUENTE,
    crear_boton,
    crear_etiqueta,
    crear_tabla,
    crear_tarjeta,
    fila_seleccionada,
    llenar_tabla,
)
from models.validaciones import formato_clp


# Pestaña para registrar, editar y eliminar clientes, y ver su historial de compras.
class PestanaClientes(tk.Frame):
    # Arma la pantalla. Usa dos controladores: el de clientes y el de ventas (para el historial).
    def __init__(self, padre, controladores):
        super().__init__(padre, bg=colores.BG_VENTANA, padx=12, pady=12)
        self.ctrl_clientes = controladores.clientes
        self.ctrl_ventas = controladores.ventas

        tarjeta = crear_tarjeta(self, "Datos del cliente")
        tarjeta.pack(fill="x", pady=(0, 10))

        formulario = tk.Frame(tarjeta, bg=colores.BG_TARJETA)
        formulario.pack(fill="x")
        # Diccionario que guarda cada caja de texto con su nombre ('rut', 'nombre'...), para leerlas todas con un for.
        self.campos = {}
        # enumerate numera los elementos (0, 1, 2...): sirve para poner cada campo en su propia fila.
        for fila, (clave, titulo) in enumerate([
            ("rut", "RUT:"), ("nombre", "Nombre:"), ("telefono", "Teléfono:"), ("correo", "Correo:"),
        ]):
            crear_etiqueta(formulario, titulo).grid(row=fila, column=0, sticky="w", pady=2)
            # Crea la caja de texto y la guarda en el diccionario con su nombre.
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
        # Al seleccionar una fila de la tabla, se copian sus datos al formulario.
        self.tabla.bind("<<TreeviewSelect>>", lambda evento: self.mostrar_seleccionado())

        tarjeta = crear_tarjeta(self, "Historial de compras del cliente seleccionado")
        tarjeta.pack(fill="both", expand=True)
        marco, self.tabla_historial = crear_tabla(
            tarjeta, [("Folio", 70), ("Fecha", 150), ("Estado", 110), ("Total", 100)], altura=5,
        )
        marco.pack(fill="both", expand=True)

        self.refrescar()

    # Vuelve a cargar la tabla de clientes con los datos actuales.
    def refrescar(self):
        # Lista vacía que se va llenando con append().
        filas = []
        for cliente in self.ctrl_clientes.clientes:
            # Forma corta de if/else: si el cliente es frecuente muestra el texto, si no, un guion.
            beneficio = "Cliente frecuente" if self.ctrl_ventas.es_cliente_frecuente(cliente.rut) else "-"
            filas.append((cliente.rut, (cliente.rut, cliente.nombre, cliente.telefono, cliente.correo, beneficio)))
        llenar_tabla(self.tabla, filas)
        self._mostrar_historial()

    # Muestra en la tabla de abajo las compras del cliente seleccionado.
    def _mostrar_historial(self):
        rut = fila_seleccionada(self.tabla)
        # Si hay un cliente seleccionado se piden sus ventas; si no, queda una lista vacía.
        ventas = self.ctrl_ventas.historial_cliente(rut) if rut else []
        llenar_tabla(self.tabla_historial, [
            (str(v.folio), (v.folio, v.fecha.strftime("%d-%m-%Y %H:%M"), v.estado, formato_clp(v.calcular_total())))
            for v in ventas
        ])

    # Copia los datos del cliente seleccionado a las cajas del formulario.
    def mostrar_seleccionado(self):
        """Copia los datos del cliente seleccionado al formulario."""
        cliente = self.ctrl_clientes.buscar(fila_seleccionada(self.tabla))
        if cliente:
            for clave in self.campos:
                self.campos[clave].delete(0, tk.END)
                # getattr(cliente, 'rut') equivale a cliente.rut, pero con el nombre del dato guardado en una variable.
                self.campos[clave].insert(0, getattr(cliente, clave))
        self._mostrar_historial()

    # Borra el contenido de todas las cajas (delete(0, tk.END) borra desde el primer hasta el último carácter).
    def _limpiar_formulario(self):
        for campo in self.campos.values():
            campo.delete(0, tk.END)

    # Lee las 4 cajas y devuelve una lista con lo escrito (comprensión de listas).
    def _datos_formulario(self):
        return [self.campos[clave].get() for clave in ("rut", "nombre", "telefono", "correo")]

    # Botón Registrar: pide al controlador crear el cliente. Si hay datos inválidos, muestra el error.
    def registrar(self):
        try:
            # El asterisco reparte la lista como 4 argumentos separados: (rut, nombre, telefono, correo).
            self.ctrl_clientes.registrar(*self._datos_formulario())
        except ValueError as error:
            messagebox.showerror("Dato inválido", str(error))
            return
        self.tabla.selection_remove(*self.tabla.selection())
        self._limpiar_formulario()
        self.refrescar()
        messagebox.showinfo("Cliente registrado", "El cliente se registró correctamente.")

    # Botón Guardar cambios: exige tener un cliente seleccionado (si 'rut is None', avisa y termina).
    def actualizar(self):
        rut = fila_seleccionada(self.tabla)
        if rut is None:
            messagebox.showinfo("Atención", "Seleccione un cliente de la tabla.")
            return
        try:
            self.ctrl_clientes.actualizar(rut, *self._datos_formulario())
        except ValueError as error:
            messagebox.showerror("Dato inválido", str(error))
            return
        self.refrescar()
        messagebox.showinfo("Cliente actualizado", "Los cambios se guardaron correctamente.")

    # Botón Eliminar: pregunta confirmación y el controlador rechaza si el cliente tiene compras.
    def eliminar(self):
        rut = fila_seleccionada(self.tabla)
        if rut is None:
            messagebox.showinfo("Atención", "Seleccione un cliente de la tabla.")
            return
        if not messagebox.askyesno("Eliminar cliente", "¿Desea eliminar este cliente?"):
            return
        try:
            self.ctrl_clientes.eliminar(rut)
        except ValueError as error:
            messagebox.showerror("No se pudo eliminar", str(error))
            return
        self._limpiar_formulario()
        self.refrescar()
