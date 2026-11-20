"""
Pantalla de inicio de sesión con diseño refinado, colores pasteles y logo oficial.
"""

import tkinter as tk
from tkinter import messagebox

from views import colores
from views.componentes import (
    FUENTE,
    FUENTE_BOTON,
    FUENTE_ENCABEZADO,
    FUENTE_SUBTITULO,
    crear_boton,
    crear_etiqueta,
    crear_tarjeta,
)
from views.imagenes import cargar_logo


class PantallaLogin(tk.Frame):
    """Pantalla inicial de autenticación con presentación elegante de la marca."""

    def __init__(self, padre, controladores, al_ingresar):
        super().__init__(padre, bg=colores.BG_VENTANA)
        self.controladores = controladores
        self.al_ingresar = al_ingresar

        # Contenedor central que se adapta armoniosamente al tamaño de la ventana
        centro = tk.Frame(self, bg=colores.BG_VENTANA)
        centro.place(relx=0.5, rely=0.5, anchor="center")

        # Carga del logo oficial proporcionado
        self.logo_img = cargar_logo(150, 150)
        if self.logo_img:
            lbl_logo = tk.Label(centro, image=self.logo_img, bg=colores.BG_VENTANA)
            lbl_logo.pack(pady=(0, 6))
        else:
            # Fallback en caso excepcional
            tk.Label(centro, text="🧵", font=("Segoe UI", 42), bg=colores.BG_VENTANA).pack(pady=(0, 6))

        # Título y subtítulo elegantes
        tk.Label(
            centro,
            text="LA CASERITA DE LAS CAMISETAS",
            font=FUENTE_ENCABEZADO,
            bg=colores.BG_VENTANA,
            fg=colores.TEXTO_TITULO,
        ).pack()

        tk.Label(
            centro,
            text="Boutique & Confecciones · Made with Love",
            font=FUENTE_SUBTITULO,
            bg=colores.BG_VENTANA,
            fg=colores.TEXTO_MUTED,
        ).pack(pady=(2, 14))

        # Tarjeta blanca para el formulario de acceso
        caja = crear_tarjeta(centro, "Iniciar sesión")
        caja.pack(fill="x", padx=10)

        # Campos de usuario y clave
        cuerpo = tk.Frame(caja, bg=colores.BG_TARJETA, padx=10, pady=8)
        cuerpo.pack(fill="both", expand=True)

        crear_etiqueta(cuerpo, "Usuario:").grid(row=0, column=0, sticky="e", pady=6, padx=(0, 6))
        self.txt_usuario = tk.Entry(cuerpo, font=FUENTE, width=24)
        self.txt_usuario.grid(row=0, column=1, pady=6)

        crear_etiqueta(cuerpo, "Clave:").grid(row=1, column=0, sticky="e", pady=6, padx=(0, 6))
        self.txt_clave = tk.Entry(cuerpo, font=FUENTE, width=24, show="*")
        self.txt_clave.grid(row=1, column=1, pady=6)

        self.ver_clave = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(
            cuerpo,
            text="Ver clave",
            variable=self.ver_clave,
            command=self._alternar_clave,
            font=FUENTE,
            bg=colores.BG_TARJETA,
            activebackground=colores.BG_TARJETA,
            fg=colores.TEXTO_CUERPO,
        )
        chk.grid(row=2, column=1, sticky="w", pady=(2, 6))

        # Botón de ingreso con estilo verde salvia pastel
        btn_ingresar = crear_boton(cuerpo, "Ingresar al Sistema", self.ingresar, "VERDE", ancho=22)
        btn_ingresar.grid(row=3, columnspan=2, pady=(10, 6))

        # Subtexto académico discreto
        tk.Label(
            centro,
            text="Desarrollo de Objetos · Analista Programador",
            font=("Segoe UI", 9),
            bg=colores.BG_VENTANA,
            fg=colores.TEXTO_MUTED,
        ).pack(pady=(14, 0))

        # Atajos y foco inicial
        self.txt_clave.bind("<Return>", lambda evento: self.ingresar())
        self.txt_usuario.bind("<Return>", lambda evento: self.txt_clave.focus_set())
        self.txt_usuario.focus_set()

    def _alternar_clave(self):
        """Muestra u oculta los caracteres de la contraseña."""
        self.txt_clave.config(show="" if self.ver_clave.get() else "*")

    def ingresar(self):
        """Valida las credenciales con el controlador correspondiente."""
        try:
            empleado = self.controladores.usuarios.iniciar_sesion(
                self.txt_usuario.get(), self.txt_clave.get()
            )
        except ValueError as error:
            messagebox.showerror("No se pudo ingresar", str(error))
            self.txt_clave.delete(0, tk.END)
            return

        self.al_ingresar(empleado)
