"""
Ventana principal: gestiona el ciclo de vida de la aplicación,
el inicio de sesión y la navegación por pestañas con estilo pastel armonioso.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from views import colores
from views.componentes import (
    FUENTE,
    FUENTE_BOTON,
    FUENTE_ENCABEZADO,
    FUENTE_SUBTITULO,
    crear_boton,
)
from views.imagenes import aplicar_icono_ventana, cargar_logo
from views.login import PantallaLogin
from views.pestana_clientes import PestanaClientes
from views.pestana_historial import PestanaHistorial
from views.pestana_inventario import PestanaInventario
from views.pestana_usuarios import PestanaUsuarios
from views.pestana_ventas import PestanaVentas


class Aplicacion(tk.Tk):
    """Ventana raíz de la aplicación con configuración visual global."""

    def __init__(self, controladores):
        super().__init__()
        self.controladores = controladores
        self.title("La Caserita de las Camisetas - Confecciones con Amor")
        self.geometry("1120x760")
        self.minsize(1020, 720)
        self.configure(bg=colores.BG_VENTANA)

        # Forzar a que la ventana se eleve al frente y tome el foco en Windows
        self.deiconify()
        self.lift()
        self.focus_force()
        self.after(150, lambda: (self.lift(), self.focus_force()))

        # Asigna el logo oficial al ícono de la ventana y de la barra de tareas
        aplicar_icono_ventana(self)

        # Referencia para mantener el logo del encabezado en memoria
        self.logo_header_img = None

        # Configuración estética global
        self._configurar_estilos()

        self.contenido = None
        self.mostrar_login()

        for aviso in self.controladores.avisos:
            messagebox.showwarning("Aviso de Base de Datos / Sistema", aviso)

    def _configurar_estilos(self):
        """Define la paleta pastel y tipografía para todos los widgets del sistema."""
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

        # Configuración de botones en los tonos pastel
        for nombre in ("VERDE", "AZUL", "ROSA", "DURAZNO", "LAVANDA"):
            fondo = getattr(colores, f"BTN_{nombre}_BG")
            estilo.configure(
                f"{nombre}.TButton",
                font=FUENTE_BOTON,
                padding=(14, 7),
                relief="flat",
                borderwidth=0,
                background=fondo,
                foreground=getattr(colores, f"BTN_{nombre}_FG"),
                bordercolor=fondo,
                lightcolor=fondo,
                darkcolor=fondo,
                focuscolor=fondo,
            )
            estilo.map(
                f"{nombre}.TButton",
                background=[("active", getattr(colores, f"BTN_{nombre}_HOVER"))],
            )

        # Tablas (Treeview) con filas más espaciosas y colores alternados
        estilo.configure(
            "Treeview",
            rowheight=28,
            font=FUENTE,
            borderwidth=0,
            background=colores.BG_TARJETA,
            fieldbackground=colores.BG_TARJETA,
            foreground=colores.TEXTO_CUERPO,
        )
        estilo.map(
            "Treeview",
            background=[("selected", colores.BTN_AZUL_BG)],
            foreground=[("selected", colores.TEXTO_TITULO)],
        )
        estilo.configure(
            "Treeview.Heading",
            font=FUENTE_BOTON,
            relief="flat",
            borderwidth=0,
            padding=(8, 6),
            background=colores.BG_HEADER,
            foreground=colores.FG_HEADER,
        )
        estilo.map(
            "Treeview.Heading",
            background=[("active", colores.BG_TOTAL_DESTACADO)],
        )

        # Listas desplegables (Combobox)
        estilo.configure(
            "TCombobox",
            padding=5,
            arrowsize=14,
            foreground=colores.TEXTO_TITULO,
            arrowcolor=colores.FG_HEADER,
            background=colores.BG_HEADER,
            bordercolor=colores.BORDE_SUAVE,
            lightcolor=colores.BG_TARJETA,
            darkcolor=colores.BG_TARJETA,
        )
        estilo.map(
            "TCombobox",
            fieldbackground=[("readonly", colores.BG_TARJETA), ("disabled", colores.BG_VENTANA)],
            foreground=[("readonly", colores.TEXTO_TITULO)],
            selectbackground=[("readonly", colores.BG_TARJETA)],
            selectforeground=[("readonly", colores.TEXTO_TITULO)],
            background=[("readonly", colores.BG_HEADER), ("disabled", colores.BG_VENTANA)],
        )

        # Barras de desplazamiento
        estilo.configure(
            "Vertical.TScrollbar",
            background=colores.BG_HEADER,
            troughcolor=colores.BG_VENTANA,
            bordercolor=colores.BORDE_SUAVE,
            arrowcolor=colores.FG_HEADER,
            lightcolor=colores.BG_HEADER,
            darkcolor=colores.BG_HEADER,
        )

        # Pestañas (Notebook)
        estilo.configure(
            "TNotebook",
            background=colores.BG_VENTANA,
            borderwidth=0,
            tabmargins=(14, 10, 14, 0),
        )
        estilo.configure(
            "TNotebook.Tab",
            font=FUENTE_BOTON,
            padding=(18, 7),
            borderwidth=0,
            background=colores.BG_HEADER,
            foreground=colores.FG_HEADER,
            bordercolor=colores.BG_VENTANA,
            lightcolor=colores.BG_HEADER,
        )
        estilo.map(
            "TNotebook.Tab",
            background=[
                ("selected", colores.BG_TARJETA),
                ("active", colores.BG_TOTAL_DESTACADO),
            ],
            foreground=[
                ("selected", colores.TEXTO_TITULO),
                ("active", colores.FG_HEADER),
            ],
            lightcolor=[("selected", colores.BG_TARJETA)],
        )

    def report_callback_exception(self, tipo, error, traza):
        """Muestra ventana de error amigable en caso de excepción imprevista."""
        messagebox.showerror("Error inesperado", f"Ocurrió un problema: {error}")

    def _cambiar_contenido(self, nuevo):
        """Reemplaza la vista activa."""
        if self.contenido is not None:
            self.contenido.destroy()
        self.contenido = nuevo
        self.contenido.pack(fill="both", expand=True)

    def mostrar_login(self):
        """Despliega la pantalla de inicio de sesión."""
        self._cambiar_contenido(PantallaLogin(self, self.controladores, self.mostrar_principal))

    def mostrar_principal(self, empleado):
        """Construye la vista principal con cabecera corporativa y pestañas operativas."""
        marco = tk.Frame(self, bg=colores.BG_VENTANA)

        # Encabezado corporativo refinado
        encabezado = tk.Frame(marco, bg=colores.BG_HEADER, padx=20, pady=12, relief="groove", bd=1)
        encabezado.pack(fill="x")

        # Logo oficial redimensionado para el encabezado
        self.logo_header_img = cargar_logo(48, 48)
        if self.logo_header_img:
            tk.Label(encabezado, image=self.logo_header_img, bg=colores.BG_HEADER).pack(
                side="left", padx=(0, 14)
            )
        else:
            tk.Label(encabezado, text="🧵", font=("Segoe UI", 24), bg=colores.BG_HEADER).pack(
                side="left", padx=(0, 10)
            )

        titulos = tk.Frame(encabezado, bg=colores.BG_HEADER)
        titulos.pack(side="left")

        tk.Label(
            titulos,
            text="LA CASERITA DE LAS CAMISETAS",
            font=FUENTE_ENCABEZADO,
            bg=colores.BG_HEADER,
            fg=colores.FG_HEADER,
        ).pack(anchor="w")

        tk.Label(
            titulos,
            text="Boutique & Confecciones · Made with Love · Analista Programador",
            font=FUENTE_SUBTITULO,
            bg=colores.BG_HEADER,
            fg=colores.TEXTO_MUTED,
        ).pack(anchor="w")

        # Botón para cerrar sesión
        crear_boton(encabezado, "Cerrar sesión", self.mostrar_login, "DURAZNO").pack(side="right")

        # Badge con información del empleado activo
        tk.Label(
            encabezado,
            text=f"👤  {empleado.nombre}  ({empleado.obtener_rol()})",
            font=FUENTE_BOTON,
            bg=colores.BG_BADGE,
            fg=colores.FG_BADGE,
            padx=14,
            pady=6,
            relief="groove",
            bd=1,
        ).pack(side="right", padx=14)

        # Pestañas de navegación
        pestanas = ttk.Notebook(marco)
        pestanas.pack(fill="both", expand=True)

        pestanas.add(PestanaVentas(pestanas, self.controladores, empleado), text="Ventas")
        pestanas.add(PestanaClientes(pestanas, self.controladores), text="Clientes")
        pestanas.add(PestanaHistorial(pestanas, self.controladores), text="Historial")

        if empleado.puede_administrar():
            pestanas.add(PestanaInventario(pestanas, self.controladores), text="Inventario")
            pestanas.add(PestanaUsuarios(pestanas, self.controladores, empleado), text="Usuarios")

        # Actualiza la vista de cada pestaña al hacer clic en ella
        pestanas.bind(
            "<<NotebookTabChanged>>",
            lambda evento: pestanas.nametowidget(pestanas.select()).refrescar(),
        )

        self._cambiar_contenido(marco)
