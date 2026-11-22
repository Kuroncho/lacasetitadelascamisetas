"""
Piezas de interfaz reutilizables con diseño elegante y colores pasteles.
"""

import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk

from views import colores
from views.imagenes import aplicar_icono_ventana, cargar_logo
from views.texto_boleta import generar_boleta, generar_url_whatsapp

# Tipografía elegante: serif clásico (Georgia) para títulos y marca; Segoe UI para datos y botones.
FUENTE = ("Segoe UI", 10)
FUENTE_NEGRILLA = ("Segoe UI", 10, "bold")
FUENTE_BOTON = ("Segoe UI", 10, "bold")
FUENTE_TITULO = ("Georgia", 12, "bold")
FUENTE_ENCABEZADO = ("Georgia", 16, "bold")
FUENTE_LOGO = ("Georgia", 18, "bold")
FUENTE_SUBTITULO = ("Georgia", 10, "italic")
FUENTE_MONO = ("Consolas", 10)


def crear_boton(padre, texto, comando, color="AZUL", ancho=0):
    """Crea un botón estilizado con la paleta pastel: VERDE, AZUL, ROSA, DURAZNO o LAVANDA."""
    return ttk.Button(
        padre,
        text=texto,
        command=comando,
        style=f"{color}.TButton",
        cursor="hand2",
        width=ancho or len(texto),
    )


def crear_etiqueta(padre, texto, fuente=FUENTE):
    """Crea un texto con el mismo color de fondo que su contenedor y tipografía cuidada."""
    return tk.Label(
        padre,
        text=texto,
        font=fuente,
        bg=padre.cget("bg"),
        fg=colores.TEXTO_CUERPO,
    )


def crear_tarjeta(padre, titulo):
    """Crea una tarjeta contenedora elegante con borde suave y título en serif."""
    return tk.LabelFrame(
        padre,
        text=f"  {titulo}  ",
        font=FUENTE_TITULO,
        bg=colores.BG_TARJETA,
        fg=colores.TEXTO_TITULO,
        padx=14,
        pady=10,
        relief="groove",
        bd=1,
    )


def crear_tabla(padre, columnas, altura=10):
    """Crea una tabla con encabezados estilizados y barra de desplazamiento vertical."""
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
    """
    Reemplaza el contenido de la tabla aplicando filas alternadas en colores pastel
    para mayor legibilidad visual.
    """
    seleccion = tabla.selection()
    tabla.delete(*tabla.get_children())

    for i, (id_fila, valores) in enumerate(filas):
        tag = "fila_par" if i % 2 == 0 else "fila_impar"
        tabla.insert("", "end", iid=id_fila, values=valores, tags=(tag,))

    tabla.tag_configure("fila_par", background=colores.BG_TARJETA)
    tabla.tag_configure("fila_impar", background=colores.BG_FILA_IMPAR)

    if seleccion and tabla.exists(seleccion[0]):
        tabla.selection_set(seleccion[0])


def fila_seleccionada(tabla):
    """Retorna el id de la fila seleccionada, o None si no hay ninguna."""
    seleccion = tabla.selection()
    return seleccion[0] if seleccion else None


def enviar_whatsapp(venta):
    """Abre WhatsApp Web o la app con el resumen de la venta formateado."""
    abierto = False
    try:
        abierto = webbrowser.open(generar_url_whatsapp(venta))
    except webbrowser.Error:
        abierto = False
    if not abierto:
        messagebox.showerror("WhatsApp", "No se pudo abrir WhatsApp en el navegador.")


def mostrar_boleta(padre, venta):
    """Abre una ventana modal con la boleta de venta en tipografía monoespaciada clara."""
    ventana = tk.Toplevel(padre)
    ventana.title(f"Boleta N° {venta.folio} - La Caserita")
    ventana.configure(bg=colores.BG_VENTANA)
    aplicar_icono_ventana(ventana)

    encabezado = tk.Frame(ventana, bg=colores.BG_HEADER, pady=12, padx=16)
    encabezado.pack(fill="x")

    logo_img = cargar_logo(38, 38)
    if logo_img:
        ventana._logo_ref = logo_img
        tk.Label(encabezado, image=logo_img, bg=colores.BG_HEADER).pack(side="left", padx=(0, 12))

    titulos = tk.Frame(encabezado, bg=colores.BG_HEADER)
    titulos.pack(side="left")

    tk.Label(
        titulos,
        text="LA CASERITA DE LAS CAMISETAS",
        font=FUENTE_TITULO,
        bg=colores.BG_HEADER,
        fg=colores.FG_HEADER,
    ).pack(anchor="w")

    tk.Label(
        titulos,
        text=f"Comprobante Electrónico · Folio #{venta.folio}",
        font=FUENTE_SUBTITULO,
        bg=colores.BG_HEADER,
        fg=colores.TEXTO_MUTED,
    ).pack(anchor="w", pady=(2, 0))

    # Área de texto de la boleta
    caja_texto = tk.Frame(ventana, bg=colores.BG_TARJETA, padx=12, pady=10, relief="groove", bd=1)
    caja_texto.pack(padx=16, pady=12, fill="both", expand=True)

    texto = tk.Text(
        caja_texto,
        font=FUENTE_MONO,
        width=54,
        height=26,
        bg=colores.BG_TARJETA,
        fg=colores.TEXTO_TITULO,
        relief="flat",
        highlightthickness=0,
    )
    texto.insert("1.0", generar_boleta(venta))
    texto.configure(state="disabled")
    texto.pack(fill="both", expand=True)

    acciones = tk.Frame(ventana, bg=colores.BG_VENTANA, pady=10)
    acciones.pack(fill="x")
    crear_boton(acciones, "Enviar resumen por WhatsApp", lambda: enviar_whatsapp(venta), "VERDE").pack(
        side="left", padx=(16, 8)
    )
    crear_boton(acciones, "Cerrar", ventana.destroy, "DURAZNO").pack(side="right", padx=(8, 16))

    ventana.transient(padre.winfo_toplevel())
