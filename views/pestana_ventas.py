"""
Pestaña para armar el carro y cobrar una venta.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from views import colores
# Se importan funciones de componentes.py. Los paréntesis permiten escribir la lista en varias líneas.
from views.componentes import (
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
# La vista conoce los errores del negocio solo para atraparlos y mostrar su mensaje.
from models.excepciones import PagoRechazadoException, SinStockException
from models.validaciones import formato_clp

# Diccionario: para cada medio de pago, el texto que se muestra sobre la caja de datos.
ETIQUETAS_PAGO = {
    "Efectivo": "Monto recibido ($):",
    "Transferencia": "Código de comprobante:",
    "Tarjeta de Débito": "Últimos 4 dígitos:",
}


# Cada pestaña es un Frame que se agrega al Notebook de la ventana principal.
class PestanaVentas(tk.Frame):
    # Arma la pantalla de ventas. Todo lo que se decide (stock, cobro) lo hacen los controladores; aquí solo se dibuja.
    def __init__(self, padre, controladores, empleado):
        super().__init__(padre, bg=colores.BG_VENTANA, padx=12, pady=12)
        # Se guardan los controladores que usa esta pestaña.
        self.ctrl = controladores.ventas
        self.ctrl_clientes = controladores.clientes
        self.ctrl_inventario = controladores.inventario
        self.empleado = empleado
        # El carro actual: un objeto Venta del modelo. Se trabaja con un carro a la vez; al cobrar se crea otro.
        self.venta = self.ctrl.nueva_venta(empleado)
        # Listas que guardan lo mostrado en los desplegables, para saber a qué cliente o prenda corresponde la opción elegida.
        self.lista_clientes = []
        self.lista_prendas = []

        # Dos columnas, como la pantalla original: datos a la izquierda y carro a la derecha
        # La pantalla se divide en dos columnas (cajas): datos y pago a la izquierda, carro y totales a la derecha.
        izquierda = tk.Frame(self, bg=colores.BG_VENTANA)
        izquierda.pack(side="left", fill="both", padx=(0, 10))
        derecha = tk.Frame(self, bg=colores.BG_VENTANA)
        derecha.pack(side="right", fill="both", expand=True)

        # 1. Selección de cliente y prenda
        tarjeta = crear_tarjeta(izquierda, "1. Cliente y prenda")
        tarjeta.pack(fill="x", pady=(0, 10))

        crear_etiqueta(tarjeta, "Cliente:").pack(anchor="w")
        # Combobox es una lista desplegable. state='readonly': solo se puede elegir una opción, no escribir.
        self.cmb_cliente = ttk.Combobox(tarjeta, state="readonly", width=46, font=FUENTE)
        self.cmb_cliente.pack(fill="x", pady=(2, 8))
        # Al elegir un cliente se ejecuta seleccionar_cliente().
        self.cmb_cliente.bind("<<ComboboxSelected>>", lambda evento: self.seleccionar_cliente())

        crear_etiqueta(tarjeta, "Prenda:").pack(anchor="w")
        self.cmb_prenda = ttk.Combobox(tarjeta, state="readonly", width=46, font=FUENTE)
        self.cmb_prenda.pack(fill="x", pady=(2, 8))

        fila = tk.Frame(tarjeta, bg=colores.BG_TARJETA)
        fila.pack(fill="x")
        crear_etiqueta(fila, "Cantidad:").pack(side="left")
        # insert(0, '1') deja escrito el 1 como valor inicial.
        self.txt_cantidad = tk.Entry(fila, font=FUENTE, width=8)
        self.txt_cantidad.insert(0, "1")
        self.txt_cantidad.pack(side="left", padx=8)
        crear_boton(fila, "Agregar al carro", self.agregar, "VERDE").pack(side="right")

        # 2. Medio de pago
        tarjeta = crear_tarjeta(izquierda, "2. Medio de pago")
        tarjeta.pack(fill="x")

        # StringVar es una variable de Tkinter conectada a los botones de opción: guarda cuál medio de pago está elegido.
        self.medio_pago = tk.StringVar(value="Efectivo")
        # Recorrer un diccionario entrega sus claves ('Efectivo', 'Transferencia'...). Se crea un botón de opción por cada una.
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

        # La tabla del carro. crear_tabla devuelve dos cosas: el marco que la contiene y la tabla.
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

        # Llena las listas, el carro y los totales por primera vez.
        self.refrescar()

    # Se llama cada vez que algo cambia (agregar, quitar, cobrar) para que la pantalla siempre muestre los datos actuales.
    def refrescar(self):
        """Actualiza las listas y los totales con los datos actuales de la tienda."""
        self.lista_clientes = self.ctrl_clientes.clientes
        # Lista de textos para el desplegable, armada con una comprensión de listas (ver GUIA_DE_SINTAXIS.md).
        self.cmb_cliente["values"] = [f"{c.nombre} (RUT {c.rut})" for c in self.lista_clientes]
        # Busca la posición del cliente ya elegido; si no hay ninguno devuelve -1. enumerate entrega (posición, elemento).
        indice = next((i for i, c in enumerate(self.lista_clientes) if c.rut == self.venta.cliente_rut), -1)
        if indice >= 0:
            self.cmb_cliente.current(indice)
        else:
            self.cmb_cliente.set("")

        self.lista_prendas = self.ctrl_inventario.prendas
        # Se recuerda qué prenda estaba elegida para no perder la selección al refrescar.
        anterior = self.cmb_prenda.current()
        self.cmb_prenda["values"] = [
            # Texto de cada opción. 'Disp.' es el stock menos lo que ya hay en el carro.
            f"{p.codigo} | {p.descripcion} | {formato_clp(p.calcular_precio_final())} | "
            f"Disp.: {p.stock - self.venta.cantidad_de(p.codigo)}"
            for p in self.lista_prendas
        ]
        # Condición doble: la posición debe estar entre 0 y el largo de la lista.
        if 0 <= anterior < len(self.lista_prendas):
            self.cmb_prenda.current(anterior)
        elif self.lista_prendas:
            self.cmb_prenda.current(0)
        else:
            self.cmb_prenda.set("")

        # Rellena la tabla del carro con las líneas de la venta.
        llenar_tabla(self.tabla, [
            (str(i), (d.codigo, d.descripcion, d.cantidad, formato_clp(d.subtotal)))
            for i, d in enumerate(self.venta.detalles)
        ])
        # config() cambia el texto de una etiqueta. Los montos los calcula el modelo (Venta); aquí solo se muestran.
        self.lbl_subtotal.config(text=f"Subtotal: {formato_clp(self.venta.calcular_subtotal())}")
        self.lbl_descuento.config(text=f"Descuento cliente frecuente: -{formato_clp(self.venta.calcular_descuento())}")
        self.lbl_iva.config(text=f"IVA incluido (19%): {formato_clp(self.venta.calcular_iva())}")
        self.lbl_total.config(text=f"TOTAL: {formato_clp(self.venta.calcular_total())}")

    # Al elegir un cliente se lo asigna a la venta (y se aplica su descuento si corresponde).
    def seleccionar_cliente(self):
        indice = self.cmb_cliente.current()
        if indice >= 0:
            self.ctrl.asignar_cliente(self.venta, self.lista_clientes[indice].rut)
            self.refrescar()

    # Al cambiar de medio de pago se actualiza el texto de la caja y se borra lo escrito.
    def cambiar_medio_pago(self):
        self.lbl_dato_pago.config(text=ETIQUETAS_PAGO[self.medio_pago.get()])
        self.txt_dato_pago.delete(0, tk.END)

    # Botón "Agregar al carro". Casi todos los botones del programa siguen el mismo patrón:
    # 1) leer lo escrito, 2) pedirle al controlador que lo haga, 3) si hay error mostrarlo, 4) si no, refrescar la pantalla.
    def agregar(self):
        indice = self.cmb_prenda.current()
        # -1 significa que no hay nada seleccionado.
        if indice < 0:
            messagebox.showwarning("Atención", "Seleccione una prenda.")
            return
        try:
            # El controlador convierte el texto a número, valida y agrega al carro.
            self.ctrl.agregar_prenda(self.venta, self.lista_prendas[indice].codigo, self.txt_cantidad.get())
        # Se atrapan primero los errores más específicos: aquí, falta de stock. 'str(error)' es el mensaje del error.
        except SinStockException as error:
            messagebox.showwarning("Sin stock", str(error))
            return
        # Cualquier otro dato inválido (cantidad con letras, etc.).
        except ValueError as error:
            messagebox.showerror("Dato inválido", str(error))
            return
        self.txt_cantidad.delete(0, tk.END)
        self.txt_cantidad.insert(0, "1")
        self.refrescar()

    # Quita del carro la línea seleccionada.
    def quitar(self):
        fila = fila_seleccionada(self.tabla)
        if fila is None:
            messagebox.showinfo("Atención", "Seleccione una prenda del carro.")
            return
        # int() convierte el id de la fila (texto) en número.
        self.ctrl.quitar_detalle(self.venta, int(fila))
        self.refrescar()

    # askyesno abre una pregunta y devuelve True si se presiona Sí. 'and' evalúa lo segundo solo si lo primero es verdadero.
    def vaciar(self):
        if self.venta.detalles and messagebox.askyesno("Vaciar carro", "¿Desea quitar todas las prendas del carro?"):
            self.ctrl.vaciar(self.venta)
            self.refrescar()

    # Botón de cobro. Se intenta todo dentro del 'try' y los errores se atrapan del más específico al más general.
    def cobrar(self):
        try:
            medio_pago = self.ctrl.crear_medio_pago(self.medio_pago.get(), self.txt_dato_pago.get())
            self.ctrl.registrar_venta(self.venta, medio_pago)
        except SinStockException as error:
            messagebox.showwarning("Sin stock", str(error))
            self.refrescar()
            return
        # El pago no se pudo completar (monto insuficiente, comprobante inválido...). La venta queda como estaba.
        except PagoRechazadoException as error:
            messagebox.showerror("Pago rechazado", str(error))
            return
        except ValueError as error:
            messagebox.showerror("Dato inválido", str(error))
            return

        # Si no hubo errores el pago se aprobó: se muestra la boleta y se parte con un carro nuevo.
        mostrar_boleta(self, self.venta)
        self.venta = self.ctrl.nueva_venta(self.empleado)
        self.txt_dato_pago.delete(0, tk.END)
        self.refrescar()
