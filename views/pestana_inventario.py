"""
Pestaña de inventario, solo para administradores: crear prendas, ajustar stock y precios.
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
from models.prenda import TALLAS, PrendaEstandar, PrendaTermica, RopaInterior
from models.validaciones import formato_clp

# Por cada tipo de prenda: sus características propias (título y opciones)
# Para cada tipo de prenda, las características propias que hay que pedir (título y opciones de cada una).
TIPOS_PRENDA = {
    PrendaTermica.TIPO: [("Cuello:", PrendaTermica.CUELLOS), ("Retención:", PrendaTermica.NIVELES)],
    PrendaEstandar.TIPO: [("Manga:", PrendaEstandar.MANGAS)],
    RopaInterior.TIPO: [("Elástico:", RopaInterior.ELASTICOS), ("Ajuste:", RopaInterior.AJUSTES)],
}


# Pestaña solo para administradores: crear prendas, ajustar stock, cambiar precios y eliminar.
class PestanaInventario(tk.Frame):
    def __init__(self, padre, controladores):
        super().__init__(padre, bg=colores.BG_VENTANA, padx=12, pady=12)
        self.ctrl = controladores.inventario

        tarjeta = crear_tarjeta(self, "Nueva prenda")
        tarjeta.pack(fill="x", pady=(0, 10))

        formulario = tk.Frame(tarjeta, bg=colores.BG_TARJETA)
        formulario.pack(fill="x")

        crear_etiqueta(formulario, "Tipo:").grid(row=0, column=0, sticky="w", pady=2)
        # list(TIPOS_PRENDA) toma las claves del diccionario: ['Térmica', 'Estándar', 'Ropa Interior'].
        self.cmb_tipo = ttk.Combobox(formulario, state="readonly", values=list(TIPOS_PRENDA), width=16, font=FUENTE)
        self.cmb_tipo.grid(row=0, column=1, sticky="w", padx=8)
        # Al elegir otro tipo, cambian las características que se piden (cuello, manga, elástico...).
        self.cmb_tipo.bind("<<ComboboxSelected>>", lambda evento: self.cambiar_tipo())

        crear_etiqueta(formulario, "Código:").grid(row=0, column=2, sticky="w")
        self.txt_codigo = tk.Entry(formulario, font=FUENTE, width=14)
        self.txt_codigo.grid(row=0, column=3, sticky="w", padx=8)

        crear_etiqueta(formulario, "Nombre:").grid(row=0, column=4, sticky="w")
        self.txt_nombre = tk.Entry(formulario, font=FUENTE, width=24)
        self.txt_nombre.grid(row=0, column=5, sticky="w", padx=8)

        crear_etiqueta(formulario, "Talla:").grid(row=1, column=0, sticky="w", pady=2)
        self.cmb_talla = ttk.Combobox(formulario, state="readonly", values=TALLAS, width=16, font=FUENTE)
        self.cmb_talla.grid(row=1, column=1, sticky="w", padx=8)

        crear_etiqueta(formulario, "Precio base:").grid(row=1, column=2, sticky="w")
        self.txt_precio = tk.Entry(formulario, font=FUENTE, width=14)
        self.txt_precio.grid(row=1, column=3, sticky="w", padx=8)

        crear_etiqueta(formulario, "Stock:").grid(row=1, column=4, sticky="w")
        self.txt_stock = tk.Entry(formulario, font=FUENTE, width=24)
        self.txt_stock.grid(row=1, column=5, sticky="w", padx=8)

        # Hay dos espacios para características extra; según el tipo se usan uno, dos o los dos.
        self.lbl_extra1 = crear_etiqueta(formulario, "")
        self.lbl_extra1.grid(row=2, column=0, sticky="w", pady=2)
        self.cmb_extra1 = ttk.Combobox(formulario, state="readonly", width=16, font=FUENTE)
        self.cmb_extra1.grid(row=2, column=1, sticky="w", padx=8)
        self.lbl_extra2 = crear_etiqueta(formulario, "")
        self.lbl_extra2.grid(row=2, column=2, sticky="w")
        self.cmb_extra2 = ttk.Combobox(formulario, state="readonly", width=12, font=FUENTE)
        self.cmb_extra2.grid(row=2, column=3, sticky="w", padx=8)

        crear_boton(tarjeta, "Agregar prenda", self.agregar, "VERDE").pack(anchor="w", pady=(8, 0))

        tarjeta = crear_tarjeta(self, "Inventario")
        tarjeta.pack(fill="both", expand=True)
        marco, self.tabla = crear_tabla(tarjeta, [
            ("Código", 80), ("Tipo", 100), ("Prenda", 220), ("Detalle", 270),
            ("Precio base", 90), ("Precio final", 90), ("Stock", 60),
        ])
        marco.pack(fill="both", expand=True)

        acciones = tk.Frame(tarjeta, bg=colores.BG_TARJETA)
        acciones.pack(fill="x", pady=(8, 0))
        crear_etiqueta(acciones, "Stock:").pack(side="left")
        # Crea los 4 botones de stock con un solo bloque de código, en vez de escribirlo 4 veces.
        for diferencia in (1, 5, -1, -5):
            crear_boton(
                # {x:+d} muestra el signo (+1, -5). 'lambda d=diferencia: ...' es una mini-función; 'd=diferencia' guarda el valor de ESTE botón.
                acciones, f"{diferencia:+d}", lambda d=diferencia: self.ajustar_stock(d),
                "VERDE" if diferencia > 0 else "DURAZNO",
                ancho=3,
            ).pack(side="left", padx=2)

        crear_etiqueta(acciones, "Nuevo precio:").pack(side="left", padx=(20, 4))
        self.txt_nuevo_precio = tk.Entry(acciones, font=FUENTE, width=10)
        self.txt_nuevo_precio.pack(side="left")
        crear_boton(acciones, "Cambiar precio", self.cambiar_precio, "LAVANDA").pack(side="left", padx=6)
        crear_boton(acciones, "Eliminar prenda", self.eliminar, "ROSA").pack(side="right")

        # current(0) elige la primera opción de cada lista desplegable.
        self.cmb_tipo.current(0)
        self.cmb_talla.current(0)
        self.cambiar_tipo()
        self.refrescar()

    # Vuelve a cargar la tabla con las prendas actuales; el precio final lo calcula cada tipo de prenda.
    def refrescar(self):
        llenar_tabla(self.tabla, [
            (p.codigo, (p.codigo, p.obtener_tipo(), p.descripcion, p.detalle(), formato_clp(p.precio_base),
                        formato_clp(p.calcular_precio_final()), p.stock))
            for p in self.ctrl.prendas
        ])

    # Muestra las características que corresponden al tipo de prenda elegido y oculta las que sobran.
    def cambiar_tipo(self):
        """Muestra las características que corresponden al tipo de prenda elegido."""
        extras = TIPOS_PRENDA[self.cmb_tipo.get()]
        # Recorre los dos espacios de características extra, con su posición (0 y 1).
        for indice, (etiqueta, combo) in enumerate([(self.lbl_extra1, self.cmb_extra1), (self.lbl_extra2, self.cmb_extra2)]):
            # Si el tipo de prenda tiene una característica para esta posición se muestra; si no, se oculta.
            if indice < len(extras):
                etiqueta.config(text=extras[indice][0])
                combo.config(values=extras[indice][1], state="readonly")
                combo.current(0)
            else:
                etiqueta.config(text="")
                combo.set("")
                combo.config(values=[], state="disabled")

    # Botón Agregar prenda: junta todo lo escrito y se lo pasa al controlador.
    def agregar(self):
        # Toma lo elegido en las listas de características que estén en uso (las vacías se ignoran). Es una comprensión de listas.
        extras = [combo.get() for combo in (self.cmb_extra1, self.cmb_extra2) if combo.get()]
        try:
            # El asterisco en *extras reparte la lista como argumentos separados.
            self.ctrl.crear_prenda(
                self.cmb_tipo.get(), self.txt_codigo.get(), self.txt_nombre.get(), self.cmb_talla.get(),
                self.txt_precio.get(), self.txt_stock.get(), *extras,
            )
        except ValueError as error:
            messagebox.showerror("Dato inválido", str(error))
            return
        # Después de agregar, se limpian las cajas de texto.
        for campo in (self.txt_codigo, self.txt_nombre, self.txt_precio, self.txt_stock):
            campo.delete(0, tk.END)
        self.refrescar()

    # Devuelve el código de la prenda seleccionada, o avisa si no hay ninguna.
    def _codigo_seleccionado(self):
        codigo = fila_seleccionada(self.tabla)
        if codigo is None:
            messagebox.showinfo("Atención", "Seleccione una prenda de la tabla.")
        return codigo

    # Botones +1, +5, -1, -5. 'diferencia' es cuánto sumar o restar.
    def ajustar_stock(self, diferencia):
        codigo = self._codigo_seleccionado()
        if codigo is None:
            return
        try:
            self.ctrl.ajustar_stock(codigo, diferencia)
        # Si el resultado sería un stock negativo, el modelo lanza ValueError y se avisa.
        except ValueError:
            messagebox.showerror("Stock insuficiente", "El stock no puede quedar negativo.")
            return
        self.refrescar()

    # Cambia el precio de la prenda seleccionada con el valor escrito en la caja.
    def cambiar_precio(self):
        codigo = self._codigo_seleccionado()
        if codigo is None:
            return
        try:
            self.ctrl.cambiar_precio(codigo, self.txt_nuevo_precio.get())
        except ValueError as error:
            messagebox.showerror("Dato inválido", str(error))
            return
        self.txt_nuevo_precio.delete(0, tk.END)
        self.refrescar()

    # Pregunta confirmación. Si no hay selección ('codigo is None') termina sin preguntar; el controlador rechaza prendas ya vendidas.
    def eliminar(self):
        codigo = self._codigo_seleccionado()
        if codigo is None or not messagebox.askyesno("Eliminar prenda", f"¿Desea eliminar la prenda {codigo}?"):
            return
        try:
            self.ctrl.eliminar_prenda(codigo)
        except ValueError as error:
            messagebox.showerror("No se pudo eliminar", str(error))
            return
        self.refrescar()
