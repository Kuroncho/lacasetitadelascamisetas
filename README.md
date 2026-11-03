# La Casetita de las Camisetas

Sistema de ventas, inventario y usuarios para la tienda de Marisol Mena.
Trabajo de Programación Orientada a Objetos, Analista Programador, Duoc UC.

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

## Estructura

```text
main.py                     Punto de entrada
models/
  usuario.py                Usuario, Cliente, Empleado, Administrador, Vendedor
  prenda.py                 Prenda, PrendaTermica, PrendaEstandar, RopaInterior
  pago.py                   MedioPago, Efectivo, Transferencia, TarjetaDebito
  venta.py                  Venta, DetalleVenta, EstadoVenta
  tienda.py                 Tienda: colecciones y reglas del negocio
  gestor_datos.py           GestorDatos: lectura y escritura de JSON
  excepciones.py            SinStockException, PagoRechazadoException
  validaciones.py           RUT, nombre, teléfono, correo, números y formato de pesos
gui/
  app.py                    Ventana principal
  login.py                  Inicio de sesión
  pestana_*.py              Una clase por cada pestaña
  componentes.py            Botones, tablas y boleta reutilizables
  colores.py                Paleta pastel
test_proyecto.py            Pruebas automáticas
```

## Conceptos de POO

| Concepto | Dónde se aplica |
|---|---|
| Encapsulamiento | Atributos con `_` y `@property` con validación, por ejemplo `Prenda.stock` y `Prenda.precio_base` |
| Herencia | `Usuario` → `Cliente` y `Empleado` → `Administrador` y `Vendedor`; `Prenda` → sus 3 tipos |
| Clases abstractas | `Usuario`, `Empleado` y `Prenda` no se pueden instanciar |
| Polimorfismo | `calcular_precio_final()` cambia según el tipo de prenda; `procesar_pago()` según el medio de pago |
| Interfaz | `MedioPago`: un medio de pago nuevo no requiere cambiar `Tienda.registrar_venta()` |
| Composición y colecciones | `Venta` contiene una lista de `DetalleVenta`; `Tienda` contiene las listas del sistema |
| Excepciones propias | `SinStockException` y `PagoRechazadoException`, capturadas con `try/except` en la interfaz |

## Reglas del negocio

| Regla | Valor | Dónde cambiarla |
|---|---|---|
| Recargo de prendas térmicas | 15 % | `PrendaTermica.RECARGO` |
| Descuento por volumen en prendas estándar | 10 % sobre 5 unidades | `PrendaEstandar` |
| Recargo de ropa interior XL y XXL | 10 % | `RopaInterior.RECARGO_TALLA` |
| Cliente frecuente | 5 % desde 3 compras | `models/tienda.py` |
| IVA | 19 % incluido en el precio: `total * 19 / 119` | `models/venta.py` |

El caso de estudio pide estas reglas, pero no indica los porcentajes ni los umbrales: los valores de esta tabla son provisionales y falta confirmarlos.

Estados de una venta: `PENDIENTE` → `PAGADA` → `ENTREGADA`, o de `PAGADA` a `CANCELADA`. Al cancelar, el stock vuelve al inventario. El stock se descuenta solo cuando la venta se paga, por lo que armar un carro no cambia el inventario.
