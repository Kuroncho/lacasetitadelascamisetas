"""
Ventana principal: muestra el inicio de sesión y luego las pestañas según el rol.
"""

# Tkinter es la herramienta de Python para crear ventanas ('as tk' es un nombre corto). Un "widget" es cualquier elemento visible:
# botón, texto, caja, tabla... Las vistas solo dibujan y llaman a los controladores; no deciden reglas del negocio.
import tkinter as tk
# messagebox: ventanas de aviso (error, pregunta, información). ttk: widgets modernos que se pueden estilizar.
from tkinter import messagebox, ttk

# colores.py guarda la paleta pastel; aquí se usa por nombre (colores.BG_VENTANA).
from views import colores
from views.componentes import FUENTE, FUENTE_BOTON, FUENTE_ENCABEZADO, crear_boton
from views.login import PantallaLogin
from views.pestana_clientes import PestanaClientes
from views.pestana_historial import PestanaHistorial
from views.pestana_inventario import PestanaInventario
from views.pestana_usuarios import PestanaUsuarios
from views.pestana_ventas import PestanaVentas


# La ventana principal. Hereda de tk.Tk (la ventana base de Tkinter), así que ya sabe abrirse, cambiar de tamaño, etc.
class Aplicacion(tk.Tk):
    # Recibe los controladores: es la única conexión de la pantalla con las reglas del negocio.
    def __init__(self, controladores):
        # Inicializa la ventana base de Tkinter (la clase padre).
        super().__init__()
        self.controladores = controladores
        # Título de la ventana, tamaño inicial (ancho x alto) y tamaño mínimo.
        self.title("La Caserita de las Camisetas")
        self.geometry("1100x760")
        self.minsize(1000, 720)
        self.configure(bg=colores.BG_VENTANA)

        # Define colores y fuentes de todos los widgets (más abajo).
        self._configurar_estilos()

        # None significa 'nada todavía'. Aquí se guarda lo que se está mostrando (el login o la pantalla principal).
        self.contenido = None
        # Al abrir el programa lo primero es el inicio de sesión.
        self.mostrar_login()
        # Si al abrir había un archivo de datos dañado, se avisa con una ventana.
        for aviso in self.controladores.avisos:
            messagebox.showwarning("Aviso", aviso)

    # Esta función solo define colores y fuentes de los widgets; no tiene lógica del negocio, se puede leer por encima.
    # Se aplican de forma global para que se vean igual en cualquier computador.
    def _configurar_estilos(self):
        """Fija los colores pastel, para que se vean igual en cualquier computador y en modo oscuro."""
        # Recorre una lista de pares (opción, valor). option_add aplica cada opción a todos los widgets de ese tipo.
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

        # Los widgets 'ttk' se personalizan con estilos. Se parte del tema 'clam', que permite cambiar colores.
        estilo = ttk.Style(self)
        estilo.theme_use("clam")

        # Un estilo de botón por cada color pastel
        # Se crea un estilo de botón por cada color pastel (verde, azul, rosa, durazno y lavanda).
        for nombre in ("VERDE", "AZUL", "ROSA", "DURAZNO", "LAVANDA"):
            # getattr(colores, 'BTN_VERDE_BG') obtiene la variable de colores.py cuyo nombre se arma con texto.
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

    # Tkinter llama a esta función si ocurre un error inesperado dentro de un botón. Así se muestra un mensaje en vez de que no pase nada.
    def report_callback_exception(self, tipo, error, traza):
        """Evita que un error inesperado pase en silencio: siempre se muestra un mensaje."""
        messagebox.showerror("Error inesperado", f"Ocurrió un problema: {error}")

    # Reemplaza lo que hay en la ventana: elimina lo anterior (destroy) y muestra lo nuevo.
    def _cambiar_contenido(self, nuevo):
        # 'is not None' = ya había algo mostrado.
        if self.contenido is not None:
            self.contenido.destroy()
        self.contenido = nuevo
        # pack() ubica el widget en su contenedor; fill='both' y expand=True lo estiran para ocupar todo el espacio.
        self.contenido.pack(fill="both", expand=True)

    # Muestra el login. Cuando el ingreso resulta bien, PantallaLogin llama a self.mostrar_principal.
    def mostrar_login(self):
        self._cambiar_contenido(PantallaLogin(self, self.controladores, self.mostrar_principal))

    # Arma la pantalla principal después de iniciar sesión. 'marco' es la caja que contiene todo.
    def mostrar_principal(self, empleado):
        marco = tk.Frame(self, bg=colores.BG_VENTANA)

        # Frame = caja contenedora. Esta es la franja celeste de arriba.
        encabezado = tk.Frame(marco, bg=colores.BG_HEADER, padx=20, pady=10)
        encabezado.pack(fill="x")
        # Label = texto sin interacción. side='left' lo pega a la izquierda; padx es el margen horizontal.
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
        # Al hacer clic vuelve al login. Se pasa self.mostrar_login sin paréntesis: se ejecuta cuando hacen clic, no ahora.
        crear_boton(encabezado, "Cerrar sesión", self.mostrar_login, "DURAZNO").pack(side="right")
        tk.Label(
            encabezado, text=f"{empleado.nombre} ({empleado.obtener_rol()})", font=FUENTE_BOTON,
            bg=colores.BG_TOTAL_DESTACADO, fg=colores.FG_TOTAL_DESTACADO, padx=12, pady=6,
        ).pack(side="right", padx=12)

        # Notebook es el widget de pestañas.
        pestanas = ttk.Notebook(marco)
        pestanas.pack(fill="both", expand=True)
        # Cada pestaña es una clase en su propio archivo (pestana_*.py). Se crea y se agrega con su título.
        pestanas.add(PestanaVentas(pestanas, self.controladores, empleado), text="Ventas")
        pestanas.add(PestanaClientes(pestanas, self.controladores), text="Clientes")
        pestanas.add(PestanaHistorial(pestanas, self.controladores), text="Historial")
        # Solo el administrador ve las pestañas Inventario y Usuarios.
        if empleado.puede_administrar():
            pestanas.add(PestanaInventario(pestanas, self.controladores), text="Inventario")
            pestanas.add(PestanaUsuarios(pestanas, self.controladores, empleado), text="Usuarios")

        # Al cambiar de pestaña se actualizan sus datos
        # bind asocia un evento (cambiar de pestaña) con una función. 'lambda evento: ...' es una mini-función de una línea:
        # cuando se abre una pestaña, se llama a su método refrescar() para mostrar los datos actualizados.
        pestanas.bind(
            "<<NotebookTabChanged>>",
            lambda evento: pestanas.nametowidget(pestanas.select()).refrescar(),
        )
        self._cambiar_contenido(marco)
