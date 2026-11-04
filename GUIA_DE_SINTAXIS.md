# Guía de sintaxis de Python para entender este proyecto

Se asume que ya conoces lo básico: `import`, `if`, `while`, variables. Aquí está lo que **no** es básico y aparece en el código, con un ejemplo real de este proyecto. Los comentarios de los archivos `.py` explican cada parte en su lugar; esta guía junta lo que se repite.

## 1. Tipos de datos que se repiten

| Tipo | Ejemplo | Para qué se usa aquí |
|---|---|---|
| texto (`str`) | `"Polera básica"` | nombres, códigos, mensajes |
| entero (`int`) | `5000` | precios, stock, cantidades |
| lista (`list`) | `["S", "M", "L"]` | tallas, ventas, clientes. Se puede agregar y quitar |
| tupla (`tuple`) | `("Segoe UI", 11)` | un grupo fijo de valores que no cambia |
| diccionario (`dict`) | `{"rut": "11111111-1", "nombre": "Juan"}` | datos con nombre. Es el formato en que se guarda el JSON |
| `None` | `None` | "no hay nada". Una búsqueda sin resultado devuelve `None` |
| verdadero/falso (`bool`) | `True`, `False` | respuestas de sí o no |

Del diccionario se lee con la clave entre corchetes: `datos["rut"]`.

## 2. Funciones

```python
def validar_nombre(nombre: str) -> str:
    ...
    return limpio.title()
```

- `def` crea una función. Entre paréntesis van los datos que recibe.
- `return` entrega el resultado y termina la función.
- `: str` y `-> str` indican el tipo esperado. Son una ayuda para leer; Python no los exige.
- Valor por defecto: `def validar_entero(valor, nombre, minimo=0)`. Si no se indica `minimo`, vale 0.
- `*argumentos` recoge o reparte varios valores: `registrar(*self._datos_formulario())` entrega la lista como argumentos separados.

## 3. Clases y objetos (POO)

```python
class Cliente(Usuario):
    def __init__(self, rut, nombre, telefono, correo):
        super().__init__(rut, nombre)
        self.telefono = telefono
```

- **Clase**: un molde. **Objeto**: lo que se crea con ese molde (`Cliente("11.111.111-1", "Juan", ...)`).
- `__init__`: se ejecuta solo al crear el objeto. Es el *constructor*.
- `self`: el propio objeto. Lo que se guarda en `self.algo` queda dentro de él.
- `class Cliente(Usuario)`: **herencia**. Cliente recibe todo lo de Usuario.
- `super()`: la clase padre. `super().__init__(...)` ejecuta el constructor del padre.
- **Clase abstracta** (`ABC`) y `@abstractmethod`: una plantilla que no se puede usar directamente. Obliga a las hijas a escribir esos métodos.
- **Polimorfismo**: el mismo método, resultado distinto según la clase. `calcular_precio_final()` da un precio distinto para una prenda térmica y para ropa interior.

## 4. Encapsulamiento: `_atributo` y `@property`

```python
self._stock = 0                  # el guion bajo avisa: "no lo toques desde afuera"

@property
def stock(self):                 # se lee como prenda.stock
    return self._stock

@stock.setter
def stock(self, valor):          # se ejecuta con prenda.stock = 5
    if valor < 0:
        raise ValueError("...")
    self._stock = valor
```

El *setter* revisa el valor antes de guardarlo, así es imposible dejar un stock negativo.

## 5. Errores: `try`, `except`, `raise`

```python
try:
    self.ctrl.agregar_prenda(...)       # se intenta
except SinStockException as error:      # si falla con este error...
    messagebox.showwarning("Sin stock", str(error))   # ...se avisa
```

- `raise ValueError("mensaje")` **lanza** un error. La función se detiene en ese punto.
- `try` / `except` **atrapa** el error para que el programa no se caiga.
- Se escriben primero los `except` más específicos y al final el más general.
- `SinStockException` y `PagoRechazadoException` son errores propios del negocio (`models/excepciones.py`).

## 6. Formas cortas que se repiten

| Forma | Qué hace |
|---|---|
| `f"Hola {nombre}"` | f-string: reemplaza lo que está entre `{ }` por su valor |
| `x if condicion else y` | un `if/else` en una línea |
| `[c.rut for c in clientes]` | **comprensión de listas**: crea una lista nueva recorriendo otra |
| `[v for v in ventas if v.activa]` | igual, pero solo con los elementos que cumplen la condición |
| `texto[:-1]`, `texto[-1]`, `texto[-9:]` | cortes de texto: sin el último, solo el último, últimos 9 |
| `for i, c in enumerate(lista)` | recorre con la posición (`i`) y el elemento (`c`) |
| `for a, b in zip(lista1, lista2)` | recorre dos listas a la vez |
| `lambda evento: self.ingresar()` | una mini-función de una línea, usada en botones |
| `lista.append(x)` / `lista.remove(x)` | agrega al final / quita un elemento |
| `x is None`, `x is not None` | pregunta si es "nada" |
| `any(...)`, `all(...)` | verdadero si alguno / todos cumplen la condición |
| `with open(...) as archivo:` | abre un archivo y lo cierra solo al terminar |

Ejemplo de comprensión de listas, del controlador de ventas:

```python
compras = [v for v in self.historial_cliente(rut) if v.estado != EstadoVenta.CANCELADA]
```

Es lo mismo que:

```python
compras = []
for v in self.historial_cliente(rut):
    if v.estado != EstadoVenta.CANCELADA:
        compras.append(v)
```

## 7. JSON

JSON es un formato de texto para guardar listas y diccionarios, fácil de leer. Un ejemplo de `datos/clientes.json`:

```json
[
  {"rut": "11111111-1", "nombre": "Juan Perez", "telefono": "+56911223344", "correo": "juan@correo.cl"}
]
```

- Para guardar: cada objeto tiene un método `a_dict()` que lo convierte en diccionario, y `json.dump` lo escribe.
- Para cargar: `json.load` lee el archivo y `desde_dict(...)` convierte cada diccionario otra vez en objeto.

## 8. Tkinter (las ventanas)

| Palabra | Qué es |
|---|---|
| widget | cualquier elemento visible: botón, texto, caja, tabla |
| `Frame` | una caja que contiene otros widgets |
| `Label` | un texto en pantalla |
| `Entry` | una caja donde se escribe. Se lee con `.get()` |
| `Combobox` | lista desplegable |
| `Treeview` | tabla |
| `Notebook` | las pestañas |
| `pack`, `grid`, `place` | tres formas de ubicar un widget dentro de su caja |
| `command=...` | la función que se ejecuta al hacer clic en un botón (se escribe sin paréntesis) |
| `bind(evento, función)` | ejecuta una función cuando ocurre algo (Enter, elegir una opción...) |
| `messagebox` | ventanas de aviso, error o pregunta |
| `mainloop()` | mantiene la ventana abierta esperando clics |

## 9. Cómo se conectan las capas (MVC)

```text
views  →  controllers  →  models
```

Ejemplo: al presionar **Cobrar** la vista llama a `ControladorVentas.registrar_venta()`. El controlador revisa el stock, cobra y descuenta; el modelo (`Venta`, `Prenda`) guarda el resultado y el `Almacen` lo escribe en el JSON. La vista solo muestra la boleta o el error.

Para seguir una acción de punta a punta, busca en `views/` el botón, luego el método del controlador al que llama, y luego las clases del modelo que usa.
