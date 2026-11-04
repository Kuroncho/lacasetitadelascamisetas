"""
Piezas de interfaz que se repiten en todas las pestañas.
"""

# Tkinter es la herramienta de Python para crear ventanas. 'as tk' le da un nombre corto (tk.Frame en vez de tkinter.Frame).
# Un "widget" es cualquier elemento visible: botón, texto, caja, tabla...
import tkinter as tk
# ttk son widgets más modernos (botones, tablas, pestañas) que se pueden personalizar con estilos.
from tkinter import ttk

from views import colores
# El texto de la boleta se arma en otro archivo; aquí solo se muestra en una ventana.
from views.texto_boleta import generar_boleta

# Una fuente se describe con una tupla: (tipo de letra, tamaño, estilo). Son valores fijos que se reutilizan en toda la pantalla.
FUENTE = ("Segoe UI", 11)
FUENTE_BOTON = ("Segoe UI", 11, "bold")
FUENTE_TITULO = ("Segoe UI", 13, "bold")
FUENTE_ENCABEZADO = ("Segoe UI", 16, "bold")


# Estas funciones evitan repetir 15 líneas cada vez que se necesita un botón o una tabla: se crean siempre con el mismo estilo.
# 'color="AZUL"' es un valor por defecto: si no se indica otro color, el botón es azul.
# 'command' es la función que se ejecuta al hacer clic (se pasa sin paréntesis: se ejecuta recién cuando hacen clic).
def crear_boton(padre, texto, comando, color="AZUL", ancho=0):
    """Crea un botón con la paleta pastel: VERDE, AZUL, ROSA, DURAZNO o LAVANDA."""
    return ttk.Button(padre, text=texto, command=comando, style=f"{color}.TButton", cursor="hand2", width=ancho or len(texto))


# Una etiqueta (Label) es un texto en pantalla. padre.cget('bg') lee el color de fondo del contenedor para que el texto se vea integrado.
def crear_etiqueta(padre, texto, fuente=FUENTE):
    """Crea un texto con el mismo color de fondo que su contenedor."""
    return tk.Label(padre, text=texto, font=fuente, bg=padre.cget("bg"), fg=colores.TEXTO_CUERPO)


# Un LabelFrame es una caja con borde y título que agrupa otros widgets, como una tarjeta.
def crear_tarjeta(padre, titulo):
    """Crea un recuadro blanco con título para agrupar elementos."""
    return tk.LabelFrame(
        padre,
        text=f" {titulo} ",
        font=FUENTE_BOTON,
        bg=colores.BG_TARJETA,
        fg=colores.TEXTO_TITULO,
        padx=12,
        pady=8,
        relief="groove",
        bd=1,
    )


# Treeview es la tabla con columnas. Esta función devuelve DOS cosas (el marco y la tabla); quien la llama las recibe así:
# marco, tabla = crear_tabla(...).
def crear_tabla(padre, columnas, altura=10):
    """Crea una tabla. columnas es una lista de (título, ancho)."""
    marco = tk.Frame(padre, bg=padre.cget("bg"))
    # Comprensión de listas: crea ['0', '1', '2', ...], un nombre interno para cada columna (ver GUIA_DE_SINTAXIS.md).
    claves = [str(i) for i in range(len(columnas))]
    tabla = ttk.Treeview(marco, columns=claves, show="headings", height=altura, selectmode="browse")
    # zip junta dos listas elemento a elemento; así se recorren a la vez los nombres internos y los datos de cada columna.
    for clave, (titulo, ancho) in zip(claves, columnas):
        tabla.heading(clave, text=titulo)
        tabla.column(clave, width=ancho, anchor="w")
    # Barra de desplazamiento vertical, conectada a la tabla.
    barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=barra.set)
    # pack() ubica un widget dentro de su contenedor. side='left' lo pega a la izquierda; fill y expand lo estiran para ocupar el espacio.
    tabla.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")
    return marco, tabla


# Reemplaza el contenido de la tabla: anota qué fila estaba seleccionada, borra todas, inserta las nuevas
# y vuelve a seleccionar la misma si todavía existe.
def llenar_tabla(tabla, filas):
    """Reemplaza el contenido de la tabla. filas es una lista de (id_fila, valores)."""
    seleccion = tabla.selection()
    # El asterisco reparte la lista de filas como argumentos separados, para borrarlas todas de una vez.
    tabla.delete(*tabla.get_children())
    for id_fila, valores in filas:
        tabla.insert("", "end", iid=id_fila, values=valores)
    if seleccion and tabla.exists(seleccion[0]):
        tabla.selection_set(seleccion[0])


# Devuelve el id de la fila seleccionada, o None si no hay ninguna.
def fila_seleccionada(tabla):
    """Retorna el id de la fila seleccionada, o None si no hay ninguna."""
    seleccion = tabla.selection()
    # Forma corta de if/else: si la lista 'seleccion' tiene algo, devuelve el primero; si está vacía, devuelve None.
    return seleccion[0] if seleccion else None


# Abre una ventana nueva (Toplevel) con el texto de la boleta.
def mostrar_boleta(padre, venta):
    """Abre una ventana con la boleta de la venta."""
    ventana = tk.Toplevel(padre)
    ventana.title(f"Boleta N° {venta.folio}")
    ventana.configure(bg=colores.BG_VENTANA)
    encabezado = tk.Frame(ventana, bg=colores.BG_HEADER, pady=8)
    encabezado.pack(fill="x")
    tk.Label(
        encabezado, text=f"Comprobante de Venta - Folio #{venta.folio}", font=FUENTE_BOTON,
        bg=colores.BG_HEADER, fg=colores.FG_HEADER,
    ).pack()
    # Text es un cuadro de texto de varias líneas, con letra de ancho fijo para que las columnas queden alineadas.
    texto = tk.Text(ventana, font=("Courier New", 11), width=52, height=28, bg=colores.BG_TARJETA, relief="flat", highlightthickness=0, padx=8, pady=8)
    texto.insert("1.0", generar_boleta(venta))
    # 'disabled' deja el texto en solo lectura: se puede leer pero no editar.
    texto.configure(state="disabled")
    texto.pack(padx=12, pady=12, fill="both", expand=True)
    crear_boton(ventana, "Cerrar", ventana.destroy, "ROSA").pack(pady=(0, 12))
    ventana.transient(padre.winfo_toplevel())
