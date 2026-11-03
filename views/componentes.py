"""
Piezas de interfaz que se repiten en todas las pestañas.
"""

import tkinter as tk
from tkinter import ttk

from views import colores
from views.texto_boleta import generar_boleta

FUENTE = ("Segoe UI", 11)
FUENTE_BOTON = ("Segoe UI", 11, "bold")
FUENTE_TITULO = ("Segoe UI", 13, "bold")
FUENTE_ENCABEZADO = ("Segoe UI", 16, "bold")


def crear_boton(padre, texto, comando, color="AZUL", ancho=0):
    """Crea un botón con la paleta pastel: VERDE, AZUL, ROSA, DURAZNO o LAVANDA."""
    return ttk.Button(padre, text=texto, command=comando, style=f"{color}.TButton", cursor="hand2", width=ancho or len(texto))


def crear_etiqueta(padre, texto, fuente=FUENTE):
    """Crea un texto con el mismo color de fondo que su contenedor."""
    return tk.Label(padre, text=texto, font=fuente, bg=padre.cget("bg"), fg=colores.TEXTO_CUERPO)


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


def crear_tabla(padre, columnas, altura=10):
    """Crea una tabla. columnas es una lista de (título, ancho)."""
    marco = tk.Frame(padre, bg=padre.cget("bg"))
    claves = [str(i) for i in range(len(columnas))]
    tabla = ttk.Treeview(marco, columns=claves, show="headings", height=altura, selectmode="browse")
    for clave, (titulo, ancho) in zip(claves, columnas):
        tabla.heading(clave, text=titulo)
        tabla.column(clave, width=ancho, anchor="w")
    barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=barra.set)
    tabla.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")
    return marco, tabla


def llenar_tabla(tabla, filas):
    """Reemplaza el contenido de la tabla. filas es una lista de (id_fila, valores)."""
    seleccion = tabla.selection()
    tabla.delete(*tabla.get_children())
    for id_fila, valores in filas:
        tabla.insert("", "end", iid=id_fila, values=valores)
    if seleccion and tabla.exists(seleccion[0]):
        tabla.selection_set(seleccion[0])


def fila_seleccionada(tabla):
    """Retorna el id de la fila seleccionada, o None si no hay ninguna."""
    seleccion = tabla.selection()
    return seleccion[0] if seleccion else None


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
    texto = tk.Text(ventana, font=("Courier New", 11), width=52, height=28, bg=colores.BG_TARJETA, relief="flat", highlightthickness=0, padx=8, pady=8)
    texto.insert("1.0", generar_boleta(venta))
    texto.configure(state="disabled")
    texto.pack(padx=12, pady=12, fill="both", expand=True)
    crear_boton(ventana, "Cerrar", ventana.destroy, "ROSA").pack(pady=(0, 12))
    ventana.transient(padre.winfo_toplevel())
