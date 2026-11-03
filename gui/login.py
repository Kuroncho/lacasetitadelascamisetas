"""
Pantalla de inicio de sesión.
"""

import tkinter as tk
from tkinter import messagebox

from gui import colores
from gui.componentes import FUENTE, FUENTE_ENCABEZADO, crear_boton, crear_etiqueta, crear_tarjeta


class PantallaLogin(tk.Frame):
    def __init__(self, padre, tienda, al_ingresar):
        super().__init__(padre, bg=colores.BG_VENTANA)
        self.tienda = tienda
        self.al_ingresar = al_ingresar  # Función que recibe al empleado que ingresó

        tk.Label(self, text="🧵", font=("Segoe UI", 40), bg=colores.BG_VENTANA).place(relx=0.5, rely=0.17, anchor="center")
        crear_etiqueta(self, "LA CASETITA DE LAS CAMISETAS", FUENTE_ENCABEZADO).place(relx=0.5, rely=0.26, anchor="center")

        caja = crear_tarjeta(self, "Iniciar sesión")
        caja.place(relx=0.5, rely=0.48, anchor="center")

        crear_etiqueta(caja, "Usuario:").grid(row=1, column=0, sticky="e", pady=4)
        self.txt_usuario = tk.Entry(caja, font=FUENTE, width=24)
        self.txt_usuario.grid(row=1, column=1, pady=4, padx=8)

        crear_etiqueta(caja, "Clave:").grid(row=2, column=0, sticky="e", pady=4)
        self.txt_clave = tk.Entry(caja, font=FUENTE, width=24, show="*")
        self.txt_clave.grid(row=2, column=1, pady=4, padx=8)

        self.ver_clave = tk.BooleanVar(value=False)
        tk.Checkbutton(
            caja, text="Ver clave", variable=self.ver_clave, command=self._alternar_clave,
            font=FUENTE, bg=colores.BG_TARJETA, activebackground=colores.BG_TARJETA,
        ).grid(row=3, column=1, sticky="w")

        crear_boton(caja, "Ingresar", self.ingresar, "VERDE").grid(row=4, columnspan=2, pady=12)

        self.txt_clave.bind("<Return>", lambda evento: self.ingresar())
        self.txt_usuario.focus_set()

    def _alternar_clave(self):
        self.txt_clave.config(show="" if self.ver_clave.get() else "*")

    def ingresar(self):
        try:
            empleado = self.tienda.iniciar_sesion(self.txt_usuario.get(), self.txt_clave.get())
        except ValueError as error:
            messagebox.showerror("No se pudo ingresar", str(error))
            self.txt_clave.delete(0, tk.END)
            return
        self.al_ingresar(empleado)
