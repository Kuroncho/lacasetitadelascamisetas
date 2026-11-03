"""
Ventana principal: muestra el inicio de sesión y luego las pestañas según el rol.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from gui import colores
from gui.componentes import FUENTE, FUENTE_BOTON, FUENTE_ENCABEZADO, crear_boton
from gui.login import PantallaLogin
from gui.pestana_clientes import PestanaClientes
from gui.pestana_historial import PestanaHistorial
from gui.pestana_inventario import PestanaInventario
from gui.pestana_usuarios import PestanaUsuarios
from gui.pestana_ventas import PestanaVentas


class Aplicacion(tk.Tk):
    def __init__(self, tienda):
        super().__init__()
        self.tienda = tienda
        self.title("La Caserita de las Camisetas")
        self.geometry("1100x760")
        self.minsize(1000, 720)
        self.configure(bg=colores.BG_VENTANA)

        self._configurar_estilos()

        self.contenido = None
        self.mostrar_login()
        for aviso in self.tienda.avisos:
            messagebox.showwarning("Aviso", aviso)

    def _configurar_estilos(self):
        """Fija los colores pastel, para que se vean igual en cualquier computador y en modo oscuro."""
        for opcion, valor in [
            ("*Entry.background", colores.BG_TARJETA),
            ("*Entry.foreground", colores.TEXTO_TITULO),
            ("*Entry.insertBackground", colores.TEXTO_TITULO),
            ("*Entry.relief", "flat"),
            ("*Entry.highlightThickness", 1),
            ("*Entry.highlightBackground", colores.BORDE_SUAVE),
            ("*Entry.highlightColor", colores.BTN_AZUL_HOVER),
            ("*Radiobutton.foreground", colores.TEXTO_CUERPO),
            ("*Radiobutton.selectColor", colores.BG_TARJETA),
            ("*Radiobutton.highlightThickness", 0),
            ("*Checkbutton.foreground", colores.TEXTO_CUERPO),
            ("*Checkbutton.selectColor", colores.BG_TARJETA),
            ("*Checkbutton.highlightThickness", 0),
            ("*Text.foreground", colores.TEXTO_TITULO),
            ("*TCombobox*Listbox.background", colores.BG_TARJETA),
            ("*TCombobox*Listbox.foreground", colores.TEXTO_TITULO),
            ("*TCombobox*Listbox.selectBackground", colores.BTN_AZUL_BG),
            ("*TCombobox*Listbox.selectForeground", colores.TEXTO_TITULO),
        ]:
            self.option_add(opcion, valor)

        estilo = ttk.Style(self)
        estilo.theme_use("clam")

        # Un estilo de botón por cada color pastel
        for nombre in ("VERDE", "AZUL", "ROSA", "DURAZNO", "LAVANDA"):
            fondo = getattr(colores, f"BTN_{nombre}_BG")
            estilo.configure(
                f"{nombre}.TButton", font=FUENTE_BOTON, padding=(12, 6), relief="flat", borderwidth=0,
                background=fondo, foreground=getattr(colores, f"BTN_{nombre}_FG"),
                bordercolor=fondo, lightcolor=fondo, darkcolor=fondo, focuscolor=fondo,
            )
            estilo.map(f"{nombre}.TButton", background=[("active", getattr(colores, f"BTN_{nombre}_HOVER"))])

        estilo.configure(
            "Treeview", rowheight=26, font=FUENTE, borderwidth=0, background=colores.BG_TARJETA,
            fieldbackground=colores.BG_TARJETA, foreground=colores.TEXTO_CUERPO,
        )
        estilo.map(
            "Treeview",
            background=[("selected", colores.BG_TOTAL_DESTACADO)],
            foreground=[("selected", colores.TEXTO_TITULO)],
        )
        estilo.configure(
            "Treeview.Heading", font=FUENTE_BOTON, relief="flat", borderwidth=0,
            background=colores.BG_HEADER, foreground=colores.FG_HEADER,
        )
        estilo.map("Treeview.Heading", background=[("active", colores.BG_TOTAL_DESTACADO)])

        estilo.configure(
            "TCombobox", padding=4, arrowsize=14, foreground=colores.TEXTO_TITULO, arrowcolor=colores.FG_HEADER,
            background=colores.BG_HEADER, bordercolor=colores.BORDE_SUAVE,
            lightcolor=colores.BG_TARJETA, darkcolor=colores.BG_TARJETA,
        )
        estilo.map(
            "TCombobox",
            fieldbackground=[("readonly", colores.BG_TARJETA), ("disabled", colores.BG_VENTANA)],
            foreground=[("readonly", colores.TEXTO_TITULO)],
            selectbackground=[("readonly", colores.BG_TARJETA)],
            selectforeground=[("readonly", colores.TEXTO_TITULO)],
            background=[("readonly", colores.BG_HEADER), ("disabled", colores.BG_VENTANA)],
        )

        estilo.configure(
            "Vertical.TScrollbar", background=colores.BG_HEADER, troughcolor=colores.BG_VENTANA,
            bordercolor=colores.BORDE_SUAVE, arrowcolor=colores.FG_HEADER,
            lightcolor=colores.BG_HEADER, darkcolor=colores.BG_HEADER,
        )

        estilo.configure("TNotebook", background=colores.BG_VENTANA, borderwidth=0, tabmargins=(12, 8, 12, 0))
        estilo.configure(
            "TNotebook.Tab", font=FUENTE_BOTON, padding=(16, 6), borderwidth=0,
            background=colores.BG_HEADER, foreground=colores.FG_HEADER,
            bordercolor=colores.BG_VENTANA, lightcolor=colores.BG_HEADER,
        )
        estilo.map(
            "TNotebook.Tab",
            background=[("selected", colores.BG_TARJETA), ("active", colores.BG_TOTAL_DESTACADO)],
            lightcolor=[("selected", colores.BG_TARJETA)],
        )

    def report_callback_exception(self, tipo, error, traza):
        """Evita que un error inesperado pase en silencio: siempre se muestra un mensaje."""
        messagebox.showerror("Error inesperado", f"Ocurrió un problema: {error}")

    def _cambiar_contenido(self, nuevo):
        if self.contenido is not None:
            self.contenido.destroy()
        self.contenido = nuevo
        self.contenido.pack(fill="both", expand=True)

    def mostrar_login(self):
        self._cambiar_contenido(PantallaLogin(self, self.tienda, self.mostrar_principal))

    def mostrar_principal(self, empleado):
        marco = tk.Frame(self, bg=colores.BG_VENTANA)

        encabezado = tk.Frame(marco, bg=colores.BG_HEADER, padx=20, pady=10)
        encabezado.pack(fill="x")
        tk.Label(encabezado, text="🧵", font=("Segoe UI", 26), bg=colores.BG_HEADER).pack(side="left", padx=(0, 10))
        titulos = tk.Frame(encabezado, bg=colores.BG_HEADER)
        titulos.pack(side="left")
        tk.Label(
            titulos, text="LA CASERITA DE LAS CAMISETAS", font=FUENTE_ENCABEZADO,
            bg=colores.BG_HEADER, fg=colores.FG_HEADER,
        ).pack(anchor="w")
        tk.Label(
            titulos, text="Sistema de Ventas e Inventario | Analista Programador - Duoc UC", font=("Segoe UI", 9),
            bg=colores.BG_HEADER, fg=colores.TEXTO_CUERPO,
        ).pack(anchor="w")
        crear_boton(encabezado, "Cerrar sesión", self.mostrar_login, "DURAZNO").pack(side="right")
        tk.Label(
            encabezado, text=f"{empleado.nombre} ({empleado.obtener_rol()})", font=FUENTE_BOTON,
            bg=colores.BG_TOTAL_DESTACADO, fg=colores.FG_TOTAL_DESTACADO, padx=12, pady=6,
        ).pack(side="right", padx=12)

        pestanas = ttk.Notebook(marco)
        pestanas.pack(fill="both", expand=True)
        pestanas.add(PestanaVentas(pestanas, self.tienda, empleado), text="Ventas")
        pestanas.add(PestanaClientes(pestanas, self.tienda), text="Clientes")
        pestanas.add(PestanaHistorial(pestanas, self.tienda), text="Historial")
        if empleado.puede_administrar():
            pestanas.add(PestanaInventario(pestanas, self.tienda), text="Inventario")
            pestanas.add(PestanaUsuarios(pestanas, self.tienda, empleado), text="Usuarios")

        # Al cambiar de pestaña se actualizan sus datos
        pestanas.bind(
            "<<NotebookTabChanged>>",
            lambda evento: pestanas.nametowidget(pestanas.select()).refrescar(),
        )
        self._cambiar_contenido(marco)
