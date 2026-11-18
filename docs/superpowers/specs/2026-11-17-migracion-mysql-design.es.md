# Diseño: migración de JSON a MySQL/MariaDB (HU14, SCRUM-24)

> Nota: este archivo es una traducción de apoyo. La fuente oficial es `2026-11-17-migracion-mysql-design.md` (en inglés).

Fecha: 17-11-2026. Estado: borrador, pendiente de tu aprobación.

## 1. Propósito

El tercer parcial exige reemplazar el guardado en JSON por una base de datos relacional (MySQL con XAMPP/WAMP). Criterios de aceptación de HU14 (SCRUM-24) en Jira:

- Modelo entidad-relación con tablas de prendas, clientes, usuarios, ventas y detalle de venta (SCRUM-26, SCRUM-27).
- Las claves foráneas impiden ventas con prendas o clientes inexistentes.
- Los datos actuales de los JSON se migran sin pérdidas (SCRUM-29).
- La aplicación funciona igual que antes y las pruebas automáticas pasan (SCRUM-28, SCRUM-30).

Ustedes tienen que explicar cada línea al profesor, y la solución debe seguir siendo claramente orientada a objetos.

También entra en el alcance la HU16 (SCRUM-36, Sprint 4, creada el 17-11-2026): bloqueo de inicio de sesión persistente. Criterios de aceptación: los intentos fallidos y la hora de desbloqueo de cada nombre de usuario se guardan en la base; si se cierra y se vuelve a abrir la app durante un bloqueo, la cuenta sigue bloqueada hasta cumplir los 10 minutos; un inicio de sesión correcto reinicia el contador; los intentos con un usuario inexistente también se registran (para no revelar qué usuarios existen); se mantienen las reglas de HU01 (5 fallos seguidos bloquean por 10 minutos, RNF-04). Ver sección 5.7.

## 2. Objetivos, lo que queda fuera y lo que sería un fracaso

Objetivos
- Cada escritura es una consulta SQL concreta y legible, dentro de un método cuyo nombre dice lo que hace.
- Registrar y cancelar una venta ocurre en una sola transacción (venta + detalle + stock).
- La misma interfaz, las mismas reglas de negocio y los mismos mensajes de error.
- Funciona en el Mac (MySQL de Homebrew) y en el Windows de tus compañeros (XAMPP, MariaDB 10.4) con el mismo código y el mismo SQL.

Fuera de alcance
- Leer desde la base en cada refresco de pantalla (las listas siguen en memoria, igual que hoy).
- Cambios en las pantallas, salvo el mensaje de error al iniciar.

Sería un fracaso (aunque funcione)
- SQL escondido en una rutina genérica de "sincronizar toda la tabla" (parece JSON disfrazado).
- Un ORM, librerías extra o patrones que ustedes no puedan explicar.
- SQL que solo funcione en uno de los dos motores.

## 3. Restricciones

- Python 3.10 o superior, librería estándar más `mysql-connector-python` (aprobado el 17-11-2026). Se instala en un venv y queda en `requirements.txt`.
- Motores: MySQL (Homebrew, Mac) y MariaDB 10.4 (XAMPP). SQL portable: InnoDB, `utf8mb4` con colación `utf8mb4_unicode_ci` (la colación por defecto de MySQL 8, `utf8mb4_0900_ai_ci`, no existe en MariaDB), solo tipos INT / VARCHAR / DATETIME / DECIMAL, sin columnas JSON y sin sintaxis exclusiva de MySQL 8.
- Identificadores, comentarios y textos de pantalla en español, comentados como el resto del proyecto.
- Se mantiene MVC: models/ no conoce controladores ni pantallas, y los controladores no usan Tkinter.

## 4. Enfoques considerados

- A. Cambiar solo el gestor de guardado: `guardar("clientes")` inserta o actualiza la tabla completa y borra las filas que faltan; los controladores no cambian. Es el cambio más chico, pero el SQL queda genérico y escondido, la venta y el stock no van en una sola transacción y parece JSON disfrazado. Descartado.
- B. Una consulta SQL por operación (elegido por ti): las listas en memoria se mantienen para leer; cada cambio es un método con nombre y su propio SQL; las ventas usan transacción. Cambian unas 20 líneas en los controladores.
- C. Leer siempre desde la base (sin listas en memoria): reescribe todas las lecturas y suma mucho que explicar sin mejorar la nota. Descartado.

## 5. Diseño (enfoque B, orientado a objetos)

### 5.1 Clases

```
models/
  conexion_bd.py      ConexionBD        abre la conexión según la configuración, crea la base y las tablas
                                         si faltan, y ofrece transaccion() (administrador de contexto)
  repositorios.py     Repositorio (ABC) clase base: guarda la ConexionBD; método abstracto cargar_todos() -> list
                      RepositorioPrendas(Repositorio)   insertar, actualizar_stock, actualizar_precio, eliminar
                      RepositorioClientes(Repositorio)  insertar, actualizar, eliminar
                      RepositorioUsuarios(Repositorio)  insertar, actualizar_clave, eliminar
                      RepositorioVentas(Repositorio)    insertar (venta + filas de detalle), actualizar_estado
  almacen.py          Almacen           composición: tiene los 4 repositorios y las 4 listas en memoria
  gestor_datos.py     se elimina (la app ya no lee ni escribe JSON; queda en el historial de git)
bd/                   carpeta NUEVA: aquí está todo lo de la base de datos MySQL
  esquema.sql         sentencias CREATE DATABASE / CREATE TABLE (las lee ConexionBD y sirven en phpMyAdmin)
  migrar_json_a_mysql.py  script aparte, se usa una sola vez: lee datos/*.json, los inserta en las tablas
                      y muestra cuántos registros hay por archivo y por tabla como prueba de "sin pérdidas" (SCRUM-29)
datos/                carpeta ANTIGUA, queda intacta como el "antes": los JSON que usó la app hasta el Parcial 2
config_bd.ini         valores por defecto versionados (localhost, 3306, root, sin contraseña, nombre de la base)
config_bd.local.ini   ajuste por equipo, ignorado por git (por ejemplo, una contraseña real)
```

Conceptos de POO que ustedes pueden nombrar: abstracción y herencia (`Repositorio` es una clase abstracta y cada repositorio hereda de ella e implementa `cargar_todos`), polimorfismo (Almacen carga los cuatro de la misma forma con `cargar_todos`), encapsulamiento (solo `ConexionBD` usa el conector y solo los repositorios contienen SQL) y composición (Almacen tiene repositorios; Venta tiene DetalleVenta).

Las filas se leen con un cursor de diccionarios, así que cada repositorio reconstruye los objetos reutilizando las funciones `desde_dict` / `prenda_desde_dict` que ya existen. `a_dict` sigue entregando los valores para los INSERT.

### 5.2 Tablas

| Tabla | Clave | Columnas | Notas |
|---|---|---|---|
| prendas | codigo VARCHAR PK | tipo, nombre, talla, precio_base INT, stock INT, tipo_cuello, nivel_termico, tipo_manga, tipo_elastico, ajuste (las columnas propias de cada tipo quedan en NULL cuando no aplican) | una sola tabla para las 3 subclases; `tipo` decide la clase |
| clientes | rut VARCHAR PK | nombre, telefono, correo | |
| usuarios | rut VARCHAR PK | usuario VARCHAR UNIQUE, nombre, rol, clave_hash CHAR(64) | |
| ventas | folio INT PK | fecha DATETIME, vendedor, cliente_rut FK -> clientes.rut, cliente_nombre, descuento_cliente, estado, medio_pago, comprobante | el folio lo asigna la app como hoy (máximo + 1) |
| detalle_venta | id INT AUTO_INCREMENT PK | folio FK -> ventas.folio, codigo FK -> prendas.codigo, descripcion, cantidad, subtotal | |

Todas las claves foráneas usan `ON DELETE RESTRICT`. `ventas.vendedor` no tiene clave foránea a propósito: la app permite eliminar empleados, y la venta guarda el nombre del vendedor como copia (por la misma razón existe `cliente_nombre`).

### 5.3 Regla de escritura: primero la base, después la memoria

Cada método de escritura de Almacen ejecuta primero su SQL y solo si funciona cambia la lista en memoria. Si la base falla, la memoria queda como estaba y el error llega a la pantalla como mensaje. Ejemplos:

- `almacen.agregar_cliente(cliente)`: `INSERT INTO clientes ...` y luego `self.clientes.append(cliente)`.
- `almacen.registrar_venta(venta)`: dentro de `with conexion.transaccion():` inserta la venta, inserta cada fila de detalle y ejecuta `UPDATE prendas SET stock = stock - %s WHERE codigo = %s` por cada línea; confirma (commit); recién entonces descuenta el stock en los objetos Prenda y agrega la venta a la lista. Si algo falla, se deshace toda la transacción (rollback).
- `almacen.cancelar_venta(venta)`: el mismo patrón (cambio de estado + devolución de stock en una transacción).

Los controladores mantienen todas las validaciones de negocio que hacen hoy y cambian `lista.append(...)` + `guardar("x")` por el método de Almacen correspondiente. Se elimina `Almacen.guardar(nombre)`.

Todo el SQL usa parámetros `%s`, nunca texto armado a mano (evita la inyección SQL y es fácil de explicar).

### 5.4 Inicio de la aplicación

1. `ConexionBD` lee `config_bd.ini` y después `config_bd.local.ini`, si existe.
2. Se conecta al servidor, ejecuta `CREATE DATABASE IF NOT EXISTS` y crea las tablas con `CREATE TABLE IF NOT EXISTS`. Ese SQL se lee desde `bd/esquema.sql`, para que exista en un solo lugar.
3. Si todas las tablas están vacías, se insertan los datos de ejemplo actuales (`_datos_iniciales()`). La importación de los JSON NO la hace la app: es el script aparte `bd/migrar_json_a_mysql.py`, que se corre una vez a mano (SCRUM-29); su resultado va a la Bitácora como evidencia.
4. Almacen carga las cuatro listas con `cargar_todos()`.
5. Se mantiene la regla "debe existir al menos un administrador": si `usuarios` no tiene ninguno, se inserta el administrador de ejemplo y se muestra un aviso.
6. Si el servidor no responde, la app muestra un error claro en Tkinter ("No se pudo conectar a MySQL. Revisa que XAMPP/MySQL esté encendido.") y se cierra, en vez de caerse mostrando el error de Python.

La recuperación de JSON dañados (archivos `.corrupto`) se elimina junto con el código JSON. La carpeta `datos/` no se borra: queda como el "antes", para mostrarle al profesor los JSON al lado de la carpeta nueva `bd/` y explicar el reemplazo. La app nunca la toca.

### 5.5 Pruebas

- Las pruebas de negocio mantienen su forma actual; `BaseTienda.setUp` arma el Almacen contra una base separada, `lacasetita_test`, y borra y vuelve a crear las tablas antes de cada prueba.
- Protección: la clase base de las pruebas se niega a borrar tablas si el nombre de la base configurada no es exactamente `lacasetita_test`, así las pruebas nunca pueden borrar los datos reales.
- Si MySQL no responde, las pruebas que usan la base se omiten con un mensaje claro (las pruebas que no usan la base, como las de validaciones y POO, siguen corriendo).
- Pruebas nuevas: las claves foráneas rechazan una venta con un cliente o una prenda que no existe; registrar una venta es todo o nada (si se fuerza una falla, el stock y las ventas quedan sin cambios); el script de migración importa una carpeta JSON de ejemplo (carpeta temporal) a `lacasetita_test` sin perder datos; los datos persisten al crear un Almacen nuevo.
- Se amplía `TestSeparacionMVC` para verificar que solo `conexion_bd.py` importa `mysql.connector` y que solo models/ contiene SQL.

### 5.7 Bloqueo de inicio de sesión persistente (HU16, SCRUM-36)

- Tabla nueva `intentos_login`: `usuario VARCHAR PK`, `fallidos INT NOT NULL DEFAULT 0`, `bloqueado_hasta DOUBLE NOT NULL DEFAULT 0` (segundos desde 1970, el mismo valor que entrega hoy `time.time()`). Sin clave foránea a `usuarios`: también hay que guardar los intentos con nombres de usuario que no existen.
- Nuevo `RepositorioIntentos(Repositorio)` con `obtener(usuario) -> dict` (entrega `{"fallidos": 0, "bloqueado_hasta": 0}` si no hay fila) y `guardar(usuario, fallidos, bloqueado_hasta)` (`INSERT ... ON DUPLICATE KEY UPDATE`, válido en MySQL y MariaDB). Su `cargar_todos()` entrega todas las filas, para cumplir con la clase base.
- A diferencia de las demás entidades, el estado del bloqueo no se guarda en una lista en memoria: `ControladorUsuarios.iniciar_sesion` lee el estado desde el repositorio (a través de Almacen) al comienzo de cada intento y lo guarda después de cada cambio. Se elimina el diccionario `self._intentos`. Razón: el estado solo importa al iniciar sesión y debe sobrevivir a un reinicio; una lectura y una escritura por intento no pesan nada.
- Se mantiene el reloj inyectable (`reloj`), para que las pruebas sigan simulando los 10 minutos sin esperar.
- No cambian la lógica de inicio de sesión, las constantes `MAX_INTENTOS` / `MINUTOS_BLOQUEO` ni los mensajes.
- Pruebas nuevas: el bloqueo sigue vigente al crear un Almacen y un controlador nuevos sobre la misma base; un inicio de sesión correcto reinicia el contador guardado; un nombre de usuario inexistente crea una fila.
- Se implementa después de que la HU14 funcione (necesita `ConexionBD` y la clase base de los repositorios).

### 5.6 Documentación y seguimiento

- README: pasos de instalación (venv, `pip install -r requirements.txt`, XAMPP en Windows, MySQL de Homebrew en Mac, `config_bd.local.ini`), en reemplazo de la frase "solo usa la librería estándar".
- `GUIA_DE_SINTAXIS.md`: entradas breves sobre `with` como transacción, los parámetros `%s` y el repositorio como clase abstracta.
- Cada paso de la implementación se registra en Confluence, en "Bitácora de Sprints" (sección Sprint 4), con fecha, commit y clave de Jira (SCRUM-26..30).

## 6. Decidido por ti

- Enfoque B (SQL por operación, listas en memoria para leer), 17-11-2026.
- Debe seguir siendo claramente orientado a objetos.
- Se permite `mysql-connector-python`.
- El JSON se reemplaza por completo dentro de la app; la carpeta `datos/` se mantiene (no se borra) como el "antes", y una carpeta nueva `bd/` tiene la parte de la base de datos, para explicar el reemplazo (17-11-2026).
- El bloqueo de login persistente es una historia de usuario nueva (HU16, SCRUM-36) y forma parte de este trabajo; la elección del sprint me la dejaste a mí (Sprint 4, porque su tema es la persistencia y la HU16 depende de la HU14).

## 7. Decisiones tomadas por Claude (puedes cambiarlas)

- Una sola tabla `prendas` con columnas opcionales por tipo (es lo más simple de explicar; tres tablas por subclase agregarían JOINs sin ganar nada aquí).
- El folio lo sigue asignando la app, sin AUTO_INCREMENT, para mantener la lógica y las pruebas actuales del folio.
- Sin clave foránea en `ventas.vendedor` (los empleados se pueden eliminar).
- Los repositorios son clases separadas dentro de un solo archivo, `models/repositorios.py`.
- Las pruebas usan la base `lacasetita_test` y se omiten si MySQL está apagado.
- El script de migración queda en `bd/` junto al esquema, para que la carpeta nueva tenga todo lo de la base de datos.
- Si el script se corre sobre tablas que ya tienen filas, se detiene sin insertar nada (evita duplicados).

## 8. Lo que queda a criterio de quien implemente

- El largo exacto de las columnas, los nombres de los métodos dentro de los repositorios y la redacción de los comentarios.
- Dónde queda el diálogo de error al iniciar (una función pequeña en views/).
