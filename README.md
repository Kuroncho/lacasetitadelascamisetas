# La Caserita de las Camisetas

Sistema de ventas, inventario y usuarios para la tienda de Marisol Mena.
Trabajo de Programación Orientada a Objetos, Analista Programador, Duoc UC.

Si no conoces la sintaxis de Python usada aquí (clases, `try/except`, `@property`, etc.), lee `GUIA_DE_SINTAXIS.md`: explica cada concepto con ejemplos de este proyecto. Además, cada archivo `.py` tiene comentarios que explican qué hace cada parte.

## Cómo ejecutar

Requiere Python 3.10 o superior con Tkinter. No hay que instalar nada más, porque solo usa la librería estándar.

```bash
py main.py              # abre la aplicación
py -m unittest -v       # ejecuta las pruebas
```

En Mac o Linux, usa `python3` en lugar de `py`.

## Usuarios de prueba

| Usuario | Clave | Rol | Puede usar |
|---|---|---|---|
| `marisol` | `admin123` | Administrador | Ventas, Clientes, Historial, Inventario y Usuarios |
| `carlos` | `vende123` | Vendedor | Ventas, Clientes e Historial |

## Datos

Los datos se guardan en `datos/`: `prendas.json`, `clientes.json`, `usuarios.json` y `ventas.json`.

- Si la carpeta no existe, se crea con datos de ejemplo. Para partir de cero, basta con borrarla.
- Si un archivo está dañado, se renombra como `.corrupto`, se crea uno nuevo y la aplicación avisa.

## Estructura (MVC)

El código está separado en tres capas. Cada una solo conoce a la que tiene debajo:

```text
views  →  controllers  →  models
```

| Capa | Qué hace | Qué no hace |
|---|---|---|
| `models/` (modelo) | Guarda los datos y las reglas propias de cada objeto, por ejemplo el precio de cada tipo de prenda o que el stock no sea negativo. También lee y escribe los JSON. | No sabe que existen los controladores ni las pantallas. |
| `controllers/` (controlador) | Aplica las reglas del negocio: validar la venta, cobrar, descontar stock, cancelar. Convierte lo que se escribió en pantalla (texto) en datos del modelo. | No usa Tkinter ni muestra mensajes. Si algo falla, lanza una excepción. |
| `views/` (vista) | Dibuja las pantallas, recibe los clics y muestra los resultados y los errores. | No aplica reglas del negocio: llama al controlador. |

```text
main.py                          Punto de entrada: crea el almacén, los controladores y la ventana
models/
  usuario.py                     Usuario, Cliente, Empleado, Administrador, Vendedor
  prenda.py                      Prenda, PrendaTermica, PrendaEstandar, RopaInterior
  pago.py                        MedioPago, Efectivo, Transferencia, TarjetaDebito
  venta.py                       Venta, DetalleVenta, EstadoVenta
  almacen.py                     Almacen: las listas del sistema y su guardado en JSON
  gestor_datos.py                GestorDatos: lectura y escritura de archivos JSON
  excepciones.py                 SinStockException, PagoRechazadoException
  validaciones.py                RUT, nombre, teléfono, correo, números y formato de pesos
controllers/
  controlador_usuarios.py        Inicio de sesión, crear, cambiar clave y eliminar usuarios
  controlador_clientes.py        Registrar, editar y eliminar clientes
  controlador_inventario.py      Crear prendas, ajustar stock, cambiar precios
  controlador_ventas.py          Armar el carro, cobrar, entregar, cancelar, historial
views/
  app.py                         Ventana principal y estilos
  login.py                       Inicio de sesión
  pestana_*.py                   Una clase por cada pestaña
  componentes.py                 Botones, tablas y ventana de boleta reutilizables
  texto_boleta.py                Texto de la boleta
  colores.py                     Paleta pastel
test_proyecto.py                 Pruebas automáticas
```

Ejemplo: al presionar "Cobrar y emitir boleta" la vista llama a `ControladorVentas.registrar_venta()`. El controlador revisa el stock, cobra con el medio de pago y descuenta las unidades; el modelo (`Venta`, `Prenda`) guarda el resultado y el `Almacen` lo escribe en el JSON. La vista solo muestra la boleta o el mensaje de error.

## Conceptos de POO

| Concepto | Dónde se aplica |
|---|---|
| Encapsulamiento | Atributos con `_` y `@property` con validación, por ejemplo `Prenda.stock` y `Prenda.precio_base` |
| Herencia | `Usuario` → `Cliente` y `Empleado` → `Administrador` y `Vendedor`; `Prenda` → sus 3 tipos |
| Clases abstractas | `Usuario`, `Empleado` y `Prenda` no se pueden instanciar |
| Polimorfismo | `calcular_precio_final()` cambia según el tipo de prenda; `procesar_pago()` según el medio de pago |
| Interfaz | `MedioPago`: un medio de pago nuevo no requiere cambiar `ControladorVentas.registrar_venta()` |
| Composición y colecciones | `Venta` contiene una lista de `DetalleVenta`; `Almacen` contiene las listas del sistema |
| Excepciones propias | `SinStockException` y `PagoRechazadoException`, capturadas con `try/except` en la interfaz |

## Reglas del negocio

| Regla | Valor | Dónde cambiarla |
|---|---|---|
| Recargo de prendas térmicas | 15 % | `PrendaTermica.RECARGO` |
| Descuento por volumen en prendas estándar | 10 % sobre 5 unidades | `PrendaEstandar` |
| Recargo de ropa interior XL y XXL | 10 % | `RopaInterior.RECARGO_TALLA` |
| Cliente frecuente | 5 % desde 3 compras | `controllers/controlador_ventas.py` |
| IVA | 19 % incluido en el precio: `total * 19 / 119` | `models/venta.py` |

El caso de estudio pide estas reglas, pero no indica los porcentajes ni los umbrales: los valores de esta tabla son provisionales y falta confirmarlos.

Estados de una venta: `PENDIENTE` → `PAGADA` → `ENTREGADA`, o de `PAGADA` a `CANCELADA`. Al cancelar, el stock vuelve al inventario. El stock se descuenta solo cuando la venta se paga, por lo que armar un carro no cambia el inventario.
