"""
Pantalla de inicio de sesión.
"""

# Tkinter crea las ventanas ('as tk' es un nombre corto). messagebox muestra ventanas de aviso.
import tkinter as tk
from tkinter import messagebox

from views import colores
# Funciones de componentes.py para crear botones, etiquetas y tarjetas con el estilo pastel.
from views.componentes import FUENTE, FUENTE_ENCABEZADO, crear_boton, crear_etiqueta, crear_tarjeta


# Un Frame es una caja contenedora. Esta clase es la pantalla de inicio de sesión: hereda de Frame, así que se puede mostrar dentro de la ventana.
class PantallaLogin(tk.Frame):
    # 'padre' es el contenedor donde se dibuja. 'al_ingresar' es una función que se ejecuta cuando el inicio de sesión resulta bien
    # (la ventana principal la usa para mostrar las pestañas).
    def __init__(self, padre, controladores, al_ingresar):
        # Construye el Frame base con el color de fondo de la paleta.
        super().__init__(padre, bg=colores.BG_VENTANA)
        self.controladores = controladores
        self.al_ingresar = al_ingresar  # Función que recibe al empleado que ingresó

        # place(relx=0.5, rely=0.17) ubica el widget con porcentajes de la ventana: 0.5 es la mitad (centro).
        tk.Label(self, text="🧵", font=("Segoe UI", 40), bg=colores.BG_VENTANA).place(relx=0.5, rely=0.17, anchor="center")
        crear_etiqueta(self, "LA CASERITA DE LAS CAMISETAS", FUENTE_ENCABEZADO).place(relx=0.5, rely=0.26, anchor="center")

        # La tarjeta blanca que contiene el formulario.
        caja = crear_tarjeta(self, "Iniciar sesión")
        caja.place(relx=0.5, rely=0.48, anchor="center")

        # grid() ubica los widgets en una tabla invisible de filas y columnas. sticky='e' pega el texto al lado este (derecha).
        crear_etiqueta(caja, "Usuario:").grid(row=1, column=0, sticky="e", pady=4)
        # Entry es una caja de texto. Se guarda en 'self.' para poder leer después lo que se escriba, con .get().
        self.txt_usuario = tk.Entry(caja, font=FUENTE, width=24)
        self.txt_usuario.grid(row=1, column=1, pady=4, padx=8)

        crear_etiqueta(caja, "Clave:").grid(row=2, column=0, sticky="e", pady=4)
        # show='*' muestra asteriscos en vez de lo escrito.
        self.txt_clave = tk.Entry(caja, font=FUENTE, width=24, show="*")
        self.txt_clave.grid(row=2, column=1, pady=4, padx=8)

        # BooleanVar es una variable de Tkinter (verdadero/falso) conectada al cuadro 'Ver clave': cambia sola al marcarlo.
        self.ver_clave = tk.BooleanVar(value=False)
        tk.Checkbutton(
            caja, text="Ver clave", variable=self.ver_clave, command=self._alternar_clave,
            font=FUENTE, bg=colores.BG_TARJETA, activebackground=colores.BG_TARJETA,
        ).grid(row=3, column=1, sticky="w")

        # Al hacer clic se ejecuta self.ingresar.
        crear_boton(caja, "Ingresar", self.ingresar, "VERDE").grid(row=4, columnspan=2, pady=12)

        # bind asocia un evento (presionar Enter) con una función. lambda es una mini-función de una línea: aquí llama a self.ingresar().
        self.txt_clave.bind("<Return>", lambda evento: self.ingresar())
        # El cursor parte en la caja de usuario.
        self.txt_usuario.focus_set()

    # Si 'Ver clave' está marcado, show='' muestra el texto; si no, show='*' lo oculta.
    def _alternar_clave(self):
        self.txt_clave.config(show="" if self.ver_clave.get() else "*")

    # Se ejecuta al presionar 'Ingresar' o Enter. Lee lo escrito, se lo pasa al controlador y muestra el resultado.
    def ingresar(self):
        # Se prueba iniciar sesión. Si el controlador lanza ValueError (usuario o clave incorrectos), Python salta al 'except'.
        try:
            empleado = self.controladores.usuarios.iniciar_sesion(self.txt_usuario.get(), self.txt_clave.get())
        # 'as error' guarda el error para mostrar su mensaje con str(error). 'return' termina la función aquí.
        except ValueError as error:
            messagebox.showerror("No se pudo ingresar", str(error))
            self.txt_clave.delete(0, tk.END)
            return
        # Si no hubo error, se avisa a la ventana principal, que muestra las pestañas.
        self.al_ingresar(empleado)
