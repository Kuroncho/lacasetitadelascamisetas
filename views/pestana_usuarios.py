"""
Pestaña de usuarios, solo para administradores: crear, cambiar clave y eliminar.
"""

import tkinter as tk
from tkinter import messagebox, ttk

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


# Pestaña solo para administradores: crear usuarios, cambiar claves y eliminar.
class PestanaUsuarios(tk.Frame):
    # Recibe también al empleado con la sesión abierta, para que no pueda eliminarse a sí mismo.
    def __init__(self, padre, controladores, empleado):
        super().__init__(padre, bg=colores.BG_VENTANA, padx=12, pady=12)
        self.ctrl = controladores.usuarios
        self.empleado = empleado

        tarjeta = crear_tarjeta(self, "Datos del usuario")
        tarjeta.pack(fill="x", pady=(0, 10))

        formulario = tk.Frame(tarjeta, bg=colores.BG_TARJETA)
        formulario.pack(fill="x")

        crear_etiqueta(formulario, "Rol:").grid(row=0, column=0, sticky="w", pady=2)
        # Lista desplegable con los dos roles posibles.
        self.cmb_rol = ttk.Combobox(formulario, state="readonly", values=["Vendedor", "Administrador"], width=32, font=FUENTE)
        self.cmb_rol.current(0)
        self.cmb_rol.grid(row=0, column=1, padx=8, pady=2)

        # Diccionario con las cajas de texto, para leerlas por nombre.
        self.campos = {}
        for fila, (clave, titulo) in enumerate([
            ("rut", "RUT:"), ("nombre", "Nombre:"), ("usuario", "Usuario:"), ("clave", "Clave:"),
        ], start=1):
            crear_etiqueta(formulario, titulo).grid(row=fila, column=0, sticky="w", pady=2)
            # Solo la caja de la clave muestra asteriscos: 'show="*" if clave == "clave" else ""' elige según el nombre del campo.
            self.campos[clave] = tk.Entry(formulario, font=FUENTE, width=34, show="*" if clave == "clave" else "")
            self.campos[clave].grid(row=fila, column=1, padx=8, pady=2)

        botones = tk.Frame(tarjeta, bg=colores.BG_TARJETA)
        botones.pack(fill="x", pady=(8, 0))
        crear_boton(botones, "Crear usuario", self.crear, "VERDE").pack(side="left")
        crear_boton(botones, "Cambiar clave del seleccionado", self.cambiar_clave, "LAVANDA").pack(side="left", padx=8)
        crear_boton(botones, "Eliminar", self.eliminar, "ROSA").pack(side="left")

        tarjeta = crear_tarjeta(self, "Usuarios registrados")
        tarjeta.pack(fill="both", expand=True)
        marco, self.tabla = crear_tabla(tarjeta, [("Usuario", 140), ("Nombre", 240), ("RUT", 120), ("Rol", 130)])
        marco.pack(fill="both", expand=True)

        self.refrescar()

    # Vuelve a cargar la tabla con los usuarios actuales.
    def refrescar(self):
        llenar_tabla(self.tabla, [
            (e.usuario, (e.usuario, e.nombre, e.rut, e.obtener_rol())) for e in self.ctrl.usuarios
        ])

    # Botón Crear usuario: el controlador valida y guarda; si algo es inválido se muestra el error.
    def crear(self):
        try:
            self.ctrl.crear_usuario(
                self.cmb_rol.get(),
                self.campos["rut"].get(),
                self.campos["nombre"].get(),
                self.campos["usuario"].get(),
                self.campos["clave"].get(),
            )
        except ValueError as error:
            messagebox.showerror("Dato inválido", str(error))
            return
        # .values() entrega los valores del diccionario (las cajas). Se limpian después de crear.
        for campo in self.campos.values():
            campo.delete(0, tk.END)
        self.refrescar()
        messagebox.showinfo("Usuario creado", "El usuario ya puede iniciar sesión.")

    # Cambia la clave del usuario seleccionado con lo escrito en la caja Clave.
    def cambiar_clave(self):
        usuario = fila_seleccionada(self.tabla)
        if usuario is None:
            messagebox.showinfo("Atención", "Seleccione un usuario de la tabla.")
            return
        try:
            self.ctrl.cambiar_clave(usuario, self.campos["clave"].get())
        except ValueError as error:
            messagebox.showerror("Dato inválido", str(error))
            return
        self.campos["clave"].delete(0, tk.END)
        messagebox.showinfo("Clave cambiada", f"Se cambió la clave de {usuario}.")

    # Pregunta confirmación. El controlador impide eliminar al usuario que tiene la sesión abierta.
    def eliminar(self):
        usuario = fila_seleccionada(self.tabla)
        if usuario is None:
            messagebox.showinfo("Atención", "Seleccione un usuario de la tabla.")
            return
        if not messagebox.askyesno("Eliminar usuario", f"¿Desea eliminar a {usuario}?"):
            return
        try:
            self.ctrl.eliminar_usuario(usuario, self.empleado)
        except ValueError as error:
            messagebox.showerror("No se pudo eliminar", str(error))
            return
        self.refrescar()
