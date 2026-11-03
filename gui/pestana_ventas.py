"""
Pestaña para armar el carro y cobrar una venta.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from gui import colores
from gui.componentes import (
    FUENTE,
    FUENTE_TITULO,
    crear_boton,
    crear_etiqueta,
    crear_tabla,
    crear_tarjeta,
    fila_seleccionada,
    llenar_tabla,
    mostrar_boleta,
)
from models.excepciones import PagoRechazadoException, SinStockException
from models.pago import Efectivo, TarjetaDebito, Transferencia
from models.validaciones import formato_clp, texto_a_entero
from models.venta import Venta

ETIQUETAS_PAGO = {
    "Efectivo": "Monto recibido ($):",
    "Transferencia": "Código de comprobante:",
    "Tarjeta de Débito": "Últimos 4 dígitos:",
}


class PestanaVentas(tk.Frame):
    def __init__(self, padre, tienda, empleado):
        super().__init__(padre, bg=colores.BG_VENTANA, padx=12, pady=12)
        self.tienda = tienda
        self.empleado = empleado
        self.venta = Venta(empleado.nombre)
        self.lista_clientes = []
        self.lista_prendas = []

        # Dos columnas, como la pantalla original: datos a la izquierda y carro a la derecha
        izquierda = tk.Frame(self, bg=colores.BG_VENTANA)
        izquierda.pack(side="left", fill="both", padx=(0, 10))
        derecha = tk.Frame(self, bg=colores.BG_VENTANA)
        derecha.pack(side="right", fill="both", expand=True)

        # 1. Selección de cliente y prenda
        tarjeta = crear_tarjeta(izquierda, "1. Cliente y prenda")
        tarjeta.pack(fill="x", pady=(0, 10))

        crear_etiqueta(tarjeta, "Cliente:").pack(anchor="w")
        self.cmb_cliente = ttk.Combobox(tarjeta, state="readonly", width=46, font=FUENTE)
        self.cmb_cliente.pack(fill="x", pady=(2, 8))
        self.cmb_cliente.bind("<<ComboboxSelected>>", lambda evento: self.seleccionar_cliente())

        crear_etiqueta(tarjeta, "Prenda:").pack(anchor="w")
        self.cmb_prenda = ttk.Combobox(tarjeta, state="readonly", width=46, font=FUENTE)
        self.cmb_prenda.pack(fill="x", pady=(2, 8))

        fila = tk.Frame(tarjeta, bg=colores.BG_TARJETA)
        fila.pack(fill="x")
        crear_etiqueta(fila, "Cantidad:").pack(side="left")
        self.txt_cantidad = tk.Entry(fila, font=FUENTE, width=8)
        self.txt_cantidad.insert(0, "1")
        self.txt_cantidad.pack(side="left", padx=8)
        crear_boton(fila, "Agregar al carro", self.agregar, "VERDE").pack(side="right")

        # 2. Medio de pago
        tarjeta = crear_tarjeta(izquierda, "2. Medio de pago")
        tarjeta.pack(fill="x")

        self.medio_pago = tk.StringVar(value="Efectivo")
        for nombre in ETIQUETAS_PAGO:
            tk.Radiobutton(
                tarjeta, text=nombre, value=nombre, variable=self.medio_pago, font=FUENTE,
                bg=colores.BG_TARJETA, activebackground=colores.BG_TARJETA, command=self.cambiar_medio_pago,
            ).pack(anchor="w")
        self.lbl_dato_pago = crear_etiqueta(tarjeta, ETIQUETAS_PAGO["Efectivo"])
        self.lbl_dato_pago.pack(anchor="w", pady=(6, 0))
        self.txt_dato_pago = tk.Entry(tarjeta, font=FUENTE)
        self.txt_dato_pago.pack(fill="x", pady=(2, 0))

        # 3. Carro
        tarjeta = crear_tarjeta(derecha, "3. Carro de compras")
        tarjeta.pack(fill="both", expand=True, pady=(0, 10))

        marco, self.tabla = crear_tabla(tarjeta, [("Código", 70), ("Prenda", 210), ("Cant.", 50), ("Subtotal", 80)], altura=8)
        marco.pack(fill="both", expand=True)

        botones = tk.Frame(tarjeta, bg=colores.BG_TARJETA)
        botones.pack(fill="x", pady=(8, 0))
        crear_boton(botones, "Quitar prenda", self.quitar, "ROSA").pack(side="left")
        crear_boton(botones, "Vaciar carro", self.vaciar, "DURAZNO").pack(side="left", padx=8)

        # 4. Totales
        tarjeta = crear_tarjeta(derecha, "4. Totales")
        tarjeta.pack(fill="x")

        self.lbl_subtotal = crear_etiqueta(tarjeta, "")
        self.lbl_subtotal.pack(anchor="e")
        self.lbl_descuento = crear_etiqueta(tarjeta, "")
        self.lbl_descuento.pack(anchor="e")
        self.lbl_iva = crear_etiqueta(tarjeta, "")
        self.lbl_iva.pack(anchor="e")

        destacado = tk.Frame(tarjeta, bg=colores.BG_TOTAL_DESTACADO, padx=8, pady=4)
        destacado.pack(fill="x", pady=6)
        self.lbl_total = tk.Label(
            destacado, font=FUENTE_TITULO, anchor="e",
            bg=colores.BG_TOTAL_DESTACADO, fg=colores.FG_TOTAL_DESTACADO,
        )
        self.lbl_total.pack(fill="x")

        crear_boton(tarjeta, "Cobrar y emitir boleta", self.cobrar, "AZUL").pack(fill="x")

        self.refrescar()

    def refrescar(self):
        """Actualiza las listas y los totales con los datos actuales de la tienda."""
        self.lista_clientes = self.tienda.clientes
        self.cmb_cliente["values"] = [f"{c.nombre} (RUT {c.rut})" for c in self.lista_clientes]
        indice = next((i for i, c in enumerate(self.lista_clientes) if c.rut == self.venta.cliente_rut), -1)
        if indice >= 0:
            self.cmb_cliente.current(indice)
        else:
            self.cmb_cliente.set("")

        self.lista_prendas = self.tienda.prendas
        anterior = self.cmb_prenda.current()
        self.cmb_prenda["values"] = [
            f"{p.codigo} | {p.descripcion} | {formato_clp(p.calcular_precio_final())} | "
            f"Disp.: {p.stock - self.venta.cantidad_de(p.codigo)}"
            for p in self.lista_prendas
        ]
        if 0 <= anterior < len(self.lista_prendas):
            self.cmb_prenda.current(anterior)
        elif self.lista_prendas:
            self.cmb_prenda.current(0)
        else:
            self.cmb_prenda.set("")

        llenar_tabla(self.tabla, [
            (str(i), (d.codigo, d.descripcion, d.cantidad, formato_clp(d.subtotal)))
            for i, d in enumerate(self.venta.detalles)
        ])
        self.lbl_subtotal.config(text=f"Subtotal: {formato_clp(self.venta.calcular_subtotal())}")
        self.lbl_descuento.config(text=f"Descuento cliente frecuente: -{formato_clp(self.venta.calcular_descuento())}")
        self.lbl_iva.config(text=f"IVA incluido (19%): {formato_clp(self.venta.calcular_iva())}")
        self.lbl_total.config(text=f"TOTAL: {formato_clp(self.venta.calcular_total())}")

    def seleccionar_cliente(self):
        indice = self.cmb_cliente.current()
        if indice >= 0:
            self.tienda.asignar_cliente(self.venta, self.lista_clientes[indice])
            self.refrescar()

    def cambiar_medio_pago(self):
        self.lbl_dato_pago.config(text=ETIQUETAS_PAGO[self.medio_pago.get()])
        self.txt_dato_pago.delete(0, tk.END)

    def agregar(self):
        indice = self.cmb_prenda.current()
        if indice < 0:
            messagebox.showwarning("Atención", "Seleccione una prenda.")
            return
        try:
            cantidad = texto_a_entero(self.txt_cantidad.get(), "La cantidad")
            self.venta.agregar_prenda(self.lista_prendas[indice], cantidad)
        except SinStockException as error:
            messagebox.showwarning("Sin stock", str(error))
            return
        except ValueError as error:
            messagebox.showerror("Dato inválido", str(error))
            return
        self.txt_cantidad.delete(0, tk.END)
        self.txt_cantidad.insert(0, "1")
        self.refrescar()

    def quitar(self):
        fila = fila_seleccionada(self.tabla)
        if fila is None:
            messagebox.showinfo("Atención", "Seleccione una prenda del carro.")
            return
        self.venta.quitar_detalle(int(fila))
        self.refrescar()

    def vaciar(self):
        if self.venta.detalles and messagebox.askyesno("Vaciar carro", "¿Desea quitar todas las prendas del carro?"):
            self.venta.vaciar()
            self.refrescar()

    def _crear_medio_pago(self):
        """Crea el objeto del medio de pago elegido en pantalla."""
        dato = self.txt_dato_pago.get()
        nombre = self.medio_pago.get()
        if nombre == "Efectivo":
            return Efectivo(texto_a_entero(dato, "El monto recibido"))
        if nombre == "Transferencia":
            return Transferencia(dato)
        return TarjetaDebito(dato)

    def cobrar(self):
        try:
            self.tienda.registrar_venta(self.venta, self._crear_medio_pago())
        except SinStockException as error:
            messagebox.showwarning("Sin stock", str(error))
            self.refrescar()
            return
        except PagoRechazadoException as error:
            messagebox.showerror("Pago rechazado", str(error))
            return
        except ValueError as error:
            messagebox.showerror("Dato inválido", str(error))
            return

        mostrar_boleta(self, self.venta)
        self.venta = Venta(self.empleado.nombre)
        self.txt_dato_pago.delete(0, tk.END)
        self.refrescar()
