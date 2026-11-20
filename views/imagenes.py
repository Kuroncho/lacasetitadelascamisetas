"""
Carga y gestión de imágenes para la interfaz gráfica.
Mantiene referencias en caché para evitar que el recolector de basura de Python
elimine las imágenes en Tkinter.
"""

from pathlib import Path
import tkinter as tk

# Ruta base del proyecto y carpeta de recursos
RUTA_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_LOGO = RUTA_PROYECTO / "assets" / "logo.png"

# Caché para evitar que Tkinter pierda las imágenes por garbage collection
_CACHE_IMAGENES = {}


def cargar_logo(ancho=None, alto=None):
    """
    Carga el logo de la aplicación redimensionado al tamaño solicitado.
    Usa Pillow (PIL) si está disponible para máxima calidad de escalado (LANCZOS).
    Tiene fallback automático a tk.PhotoImage si Pillow no estuviera presente.
    """
    clave = (ancho, alto)
    if clave in _CACHE_IMAGENES:
        return _CACHE_IMAGENES[clave]

    if not RUTA_LOGO.exists():
        return None

    imagen_tk = None

    try:
        from PIL import Image, ImageTk

        img_pil = Image.open(RUTA_LOGO)
        if ancho and alto:
            img_pil = img_pil.resize((ancho, alto), Image.Resampling.LANCZOS)
        elif ancho:
            proporcion = ancho / float(img_pil.width)
            alto_calc = int(float(img_pil.height) * proporcion)
            img_pil = img_pil.resize((ancho, alto_calc), Image.Resampling.LANCZOS)
        elif alto:
            proporcion = alto / float(img_pil.height)
            ancho_calc = int(float(img_pil.width) * proporcion)
            img_pil = img_pil.resize((ancho_calc, alto), Image.Resampling.LANCZOS)

        imagen_tk = ImageTk.PhotoImage(img_pil)
    except Exception:
        # Fallback a tk.PhotoImage estándar
        try:
            foto_base = tk.PhotoImage(file=str(RUTA_LOGO))
            if ancho and alto and foto_base.width() > 0:
                factor_x = max(1, round(foto_base.width() / ancho))
                factor_y = max(1, round(foto_base.height() / alto))
                imagen_tk = foto_base.subsample(factor_x, factor_y)
            else:
                imagen_tk = foto_base
        except Exception:
            imagen_tk = None

    if imagen_tk:
        _CACHE_IMAGENES[clave] = imagen_tk

    return imagen_tk


def aplicar_icono_ventana(ventana):
    """Aplica el logo como ícono de la ventana y de la barra de tareas."""
    try:
        icono = cargar_logo(48, 48)
        if icono:
            ventana.iconphoto(True, icono)
    except Exception:
        pass
