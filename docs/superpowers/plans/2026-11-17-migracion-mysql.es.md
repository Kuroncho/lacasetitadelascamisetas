# Plan de implementación: migración de JSON a MySQL

> Nota: este archivo es una traducción de apoyo. La fuente oficial es `2026-11-17-migracion-mysql.md` (en inglés). Código, rutas y nombres quedan en inglés o tal como están en el proyecto.

**Objetivo:** reemplazar el guardado en JSON por MySQL/MariaDB (HU14, SCRUM-24) y guardar el bloqueo de inicio de sesión en la base (HU16, SCRUM-36), sin cambiar la interfaz ni las reglas de negocio.

**Arquitectura:** `ConexionBD` encapsula el conector y las transacciones; cada tabla tiene una clase repositorio que hereda de la clase abstracta `Repositorio` y contiene el SQL de esa tabla; `Almacen` tiene los repositorios (composición), mantiene las listas en memoria para leer y ofrece un método con nombre para cada escritura (primero la base, después la memoria). El JSON sale de la app; `datos/` queda intacta como el "antes" y la importación de una sola vez vive en la carpeta nueva `bd/`.

**Tecnologías:** Python 3.13 (`python@3.13` de Homebrew, que trae Tkinter), `mysql-connector-python` en `.venv`, MySQL 26.10 (Homebrew) en el Mac, MariaDB 10.4 (XAMPP) en el Windows de tus compañeros, unittest.

**Diseño:** `docs/superpowers/specs/2026-11-17-migracion-mysql-design.md`

## Restricciones generales

- Librería estándar más `mysql-connector-python`, con la versión fija en `requirements.txt`.
- SQL portable: `ENGINE=InnoDB`, `DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`, solo tipos INT / VARCHAR / CHAR / DATETIME / DOUBLE, sin columnas JSON, sin `utf8mb4_0900_ai_ci` y sin sintaxis exclusiva de MySQL 8. Las actualizaciones-o-inserciones usan `INSERT ... ON DUPLICATE KEY UPDATE`.
- Todo valor en SQL va con parámetros `%s`, nunca armado con f-strings.
- Solo `models/conexion_bd.py` importa `mysql.connector`; solo `models/` tiene SQL; los controladores no usan Tkinter; los modelos no importan controladores ni vistas.
- Identificadores, comentarios y textos de pantalla en español, comentados línea por línea como el resto del proyecto (ustedes deben explicar cada línea).
- Regla de escritura: primero se cambia la base; la memoria se cambia solo si la transacción se confirma. Si falla, la memoria queda (o vuelve) exactamente como estaba y llega un `ErrorBaseDatos` a quien llamó.
- `datos/` nunca se modifica ni se borra.
- Git: se trabaja en la rama `feature/mysql`. Cada paso "Commit" significa mostrarte el resumen (archivos, descripción) y esperar tu aprobación; nunca se hace push.
- Cada paso "Bitácora" (Confluence) y cualquier cambio en Jira también agrega una línea con fecha en `$HOME/GitHub/ing-requisitos/recursos/registro-jira-confluence.md` en la misma sesión (el commit allá también necesita aprobación).
- Los comandos se corren desde la raíz del repo con el venv: `.venv/bin/python -m unittest -v`.

## Puntos de revisión

1. MySQL se apaga con la app abierta → la operación muestra un error y las listas en memoria no cambian (prueba en la Tarea 3: `test_falla_de_base_no_cambia_memoria`).
2. Nombres con tildes y ñ (`"Ñuñoa Pérez"`) vuelven idénticos al reabrir (prueba en la Tarea 2: `test_tildes_y_enie_sobreviven`).
3. Esquema ejecutado en MariaDB 10.4 (XAMPP) → nada exclusivo de MySQL (prueba en la Tarea 1: `test_esquema_es_portable`, más la revisión manual de un compañero en la Tarea 6).
4. Script de migración corrido dos veces → la segunda vez se rechaza y no hay duplicados (prueba en la Tarea 4: `test_segunda_migracion_se_rechaza`).
5. Iniciar sesión con `" Carlos "` y con `"carlos"` comparte el mismo registro de bloqueo (prueba en la Tarea 5: `test_bloqueo_ignora_mayusculas_y_espacios`).

---

### Tarea 1: entorno, configuración, esquema y `ConexionBD` (SCRUM-26, SCRUM-27)

**Archivos:**
- Crear: `requirements.txt`, `config_bd.ini`, `bd/__init__.py` (vacío, para que funcione `python -m bd.migrar_json_a_mysql`), `bd/esquema.sql`, `models/conexion_bd.py`, `test_base_datos.py`
- Modificar: `.gitignore` (agregar `.venv/` y `config_bd.local.ini`), `models/excepciones.py` (agregar `ErrorBaseDatos`)

**Interfaces:**
- Entrega:
  - `class ErrorBaseDatos(Exception)` en `models/excepciones.py`.
  - `ConexionBD(config: dict)` con las claves `host, puerto, usuario, clave, base_datos`.
  - `ConexionBD.leer_configuracion(carpeta: Path) -> dict` (estático): lee la sección `[mysql]` de `config_bd.ini` y encima aplica `config_bd.local.ini` si existe (configparser).
  - `ConexionBD.preparar() -> None`: se conecta al servidor, ejecuta `CREATE DATABASE IF NOT EXISTS <base_datos> CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`, la selecciona y ejecuta cada sentencia de `bd/esquema.sql` (separadas por `;`, omitiendo las vacías).
  - `ConexionBD.transaccion()` (administrador de contexto) entrega un cursor de diccionarios; confirma si todo sale bien y deshace ante cualquier excepción; un `mysql.connector.Error` se relanza como `ErrorBaseDatos` con mensaje en español.
  - `ConexionBD.consultar(sql: str, parametros: tuple = ()) -> list[dict]`.
  - `ConexionBD.base_datos` (propiedad, texto).
  - Si `preparar()` no logra conectarse, lanza `ErrorBaseDatos("No se pudo conectar a MySQL. Revisa que XAMPP/MySQL esté encendido.")`.
- Ayudantes de prueba (en `test_base_datos.py`, los usan las tareas siguientes): `config_pruebas() -> dict` (la configuración del repo con `base_datos="lacasetita_test"`), `mysql_disponible() -> bool`, `vaciar_tablas(conexion)`, que lanza `RuntimeError` si `conexion.base_datos` no es `"lacasetita_test"` y si no, ejecuta `SET FOREIGN_KEY_CHECKS=0`, `DELETE FROM` en cada tabla y `SET FOREIGN_KEY_CHECKS=1`. Las clases de prueba que usan la base llevan `@unittest.skipUnless(mysql_disponible(), "MySQL no está disponible")`.

Esquema (`bd/esquema.sql`, todo con `CREATE TABLE IF NOT EXISTS`, comentario inicial: "en phpMyAdmin, selecciona primero la base lacasetita"):
- `prendas(codigo VARCHAR(20) PK, tipo VARCHAR(20) NOT NULL, nombre VARCHAR(60) NOT NULL, talla VARCHAR(5) NOT NULL, precio_base INT NOT NULL, stock INT NOT NULL, tipo_cuello, nivel_termico, tipo_manga, tipo_elastico, ajuste VARCHAR(20) NULL)`
- `clientes(rut VARCHAR(12) PK, nombre VARCHAR(60) NOT NULL, telefono VARCHAR(20) NOT NULL, correo VARCHAR(80) NOT NULL)`
- `usuarios(rut VARCHAR(12) PK, usuario VARCHAR(30) NOT NULL UNIQUE, nombre VARCHAR(60) NOT NULL, rol VARCHAR(20) NOT NULL, clave_hash CHAR(64) NOT NULL)`
- `ventas(folio INT PK, fecha DATETIME NOT NULL, vendedor VARCHAR(60) NOT NULL, cliente_rut VARCHAR(12) NOT NULL FK→clientes(rut), cliente_nombre VARCHAR(60) NOT NULL, descuento_cliente INT NOT NULL, estado VARCHAR(12) NOT NULL, medio_pago VARCHAR(30) NOT NULL, comprobante VARCHAR(60) NULL)`
- `detalle_venta(id INT AUTO_INCREMENT PK, folio INT NOT NULL FK→ventas(folio), codigo VARCHAR(20) NOT NULL FK→prendas(codigo), descripcion VARCHAR(80) NOT NULL, cantidad INT NOT NULL, subtotal INT NOT NULL)`
- `intentos_login(usuario VARCHAR(30) PK, fallidos INT NOT NULL DEFAULT 0, bloqueado_hasta DOUBLE NOT NULL DEFAULT 0)` (se usa en la Tarea 5; se crea ahora para que el esquema quede completo)
- Todas las claves foráneas con `ON DELETE RESTRICT`; todas las tablas con `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`. Antes de escribirlo, revisar los largos máximos reales en `models/validaciones.py` y ampliar cualquier VARCHAR que quede corto.

- [ ] **Paso 1: preparar el entorno.** `git switch -c feature/mysql`; `brew services start mysql`; `/opt/homebrew/opt/python@3.13/bin/python3.13 -m venv .venv`; `.venv/bin/pip install mysql-connector-python`; fijar la versión instalada en `requirements.txt` (`.venv/bin/pip freeze | grep -i mysql-connector`). Verificar que root no tiene contraseña: `mysql -u root -e "SELECT VERSION();"` muestra una versión. Si root tiene contraseña, detenerse y preguntarte (regla de credenciales: nunca verla; usar `config_bd.local.ini`, que llenas tú).
- [ ] **Paso 2: escribir las pruebas que fallan** en `test_base_datos.py`, clase `TestConexionBD`:
  - `test_preparar_crea_las_seis_tablas`: después de `preparar()`, `SHOW TABLES` entrega exactamente `{"prendas","clientes","usuarios","ventas","detalle_venta","intentos_login"}`.
  - `test_preparar_dos_veces_no_falla`: llamar `preparar()` dos veces no lanza nada.
  - `test_clave_foranea_rechaza_venta_de_cliente_inexistente`: un `INSERT INTO ventas` con `cliente_rut="99999999-9"` dentro de `transaccion()` lanza `ErrorBaseDatos`; `SELECT COUNT(*) FROM ventas` sigue en 0.
  - `test_clave_foranea_rechaza_detalle_de_prenda_inexistente`: lo mismo con una fila de `detalle_venta` cuyo `codigo="NO-EXISTE"`.
  - `test_transaccion_hace_rollback`: insertar un cliente y lanzar `ValueError` dentro del `with`; el cliente no queda en la tabla.
  - `test_servidor_inalcanzable_da_error_claro`: `ConexionBD({**config_pruebas(), "puerto": 1})` → `preparar()` lanza `ErrorBaseDatos` con el texto `"No se pudo conectar a MySQL"`. (No se omite aunque MySQL esté apagado.)
  - `test_vaciar_tablas_se_niega_fuera_de_la_base_de_pruebas`: `vaciar_tablas` con una `ConexionBD` de `base_datos="lacasetita"` lanza `RuntimeError` sin conectarse.
  - `test_esquema_es_portable`: el texto de `bd/esquema.sql` no contiene `0900`, ` JSON` ni `CHECK (`; sí contiene `utf8mb4_unicode_ci` e `InnoDB`.
- [ ] **Paso 3: correr** `.venv/bin/python -m unittest test_base_datos -v` → FALLA (`ModuleNotFoundError: models.conexion_bd`).
- [ ] **Paso 4: implementar** `ErrorBaseDatos`, `config_bd.ini` (`host=localhost, puerto=3306, usuario=root, clave=, base_datos=lacasetita`), `bd/esquema.sql` y `models/conexion_bd.py` según las Interfaces. Una sola conexión, abierta en `preparar()` y reutilizada; `transaccion()` llama primero a `self._conexion.ping(reconnect=True)` (confirmar esa firma en la documentación del conector con context7 antes de usarla).
- [ ] **Paso 5: correr** `.venv/bin/python -m unittest test_base_datos -v` → todo PASA.
- [ ] **Paso 6: commit** (con tu aprobación): `feat: add MySQL connection, schema and config (SCRUM-26, SCRUM-27)`.
- [ ] **Paso 7: Bitácora.** Agregar una entrada en el Sprint 4 de la página de Confluence 15499265 (fecha, hash del commit, SCRUM-26/27, una línea sobre lo hecho).

---

### Tarea 2: repositorios (SCRUM-28, parte 1)

**Archivos:**
- Crear: `models/repositorios.py`
- Pruebas: `test_base_datos.py` (clase nueva `TestRepositorios`)

**Interfaces:**
- Usa: `ConexionBD.transaccion()`, `ConexionBD.consultar()`, las funciones existentes `prenda_desde_dict`, `Cliente.desde_dict`, `Empleado.desde_dict`, `Venta.desde_dict`, y el `a_dict()` de cada modelo.
- Entrega (cada método de escritura recibe como primer argumento el `cursor` abierto, para que Almacen pueda agrupar varias escrituras en una transacción):
  - `class Repositorio(ABC)`: `__init__(self, conexion: ConexionBD)`; `@abstractmethod cargar_todos(self) -> list`; `esta_vacio(self) -> bool` usando el atributo de clase `TABLA`.
  - `RepositorioPrendas`: `cargar_todos() -> list[Prenda]` (ORDER BY codigo), `insertar(cursor, prenda)`, `actualizar_stock(cursor, codigo: str, stock: int)`, `actualizar_precio(cursor, codigo: str, precio: int)`, `eliminar(cursor, codigo: str)`. El insert llena las cinco columnas propias de cada tipo con `datos.get(...)`.
  - `RepositorioClientes`: `cargar_todos()` (ORDER BY rut), `insertar(cursor, cliente)`, `actualizar(cursor, cliente)`, `eliminar(cursor, rut: str)`.
  - `RepositorioUsuarios`: `cargar_todos()` (ORDER BY rut), `insertar(cursor, empleado)`, `actualizar_clave(cursor, empleado)`, `eliminar(cursor, usuario: str)`.
  - `RepositorioVentas`: `cargar_todos() -> list[Venta]` (ventas ORDER BY folio; detalles ORDER BY id, agrupados por folio; `fecha` se convierte con `.isoformat(timespec="seconds")` antes de `Venta.desde_dict`), `insertar(cursor, venta)` (la fila de la venta + una fila en `detalle_venta` por cada detalle), `actualizar_estado(cursor, folio: int, estado: str)`.
  - `RepositorioIntentos` se agrega en la Tarea 5.

- [ ] **Paso 1: escribir las pruebas que fallan** (`setUp`: `preparar()` + `vaciar_tablas`):
  - `test_prenda_de_cada_tipo_ida_y_vuelta`: insertar una `PrendaTermica`, una `PrendaEstandar` y una `RopaInterior`; `cargar_todos()` entrega objetos de las mismas clases con el mismo `a_dict()`.
  - `test_cliente_actualizar_y_eliminar`: insertar, cambiar el teléfono, recargar y comparar; eliminar, recargar y queda vacío.
  - `test_empleado_conserva_hash_y_rol`: insertar `Administrador("33.333.333-3","Marisol Mena","marisol","admin123")`; al recargarlo, `verificar_clave("admin123")` es True y `puede_administrar()` es True.
  - `test_venta_con_detalles_ida_y_vuelta`: insertar cliente + prendas + una `Venta` pagada con 2 detalles; el `a_dict()` recargado es igual al original.
  - `test_tildes_y_enie_sobreviven`: un cliente llamado `"Ñuñoa Pérez"` vuelve idéntico.
  - `test_repositorio_es_abstracto`: `Repositorio(conexion)` lanza `TypeError`.
- [ ] **Paso 2: correr** `.venv/bin/python -m unittest test_base_datos.TestRepositorios -v` → FALLA (error de import).
- [ ] **Paso 3: implementar** `models/repositorios.py` según las Interfaces.
- [ ] **Paso 4: correr** el mismo comando → PASA.
- [ ] **Paso 5: commit** (con aprobación): `feat: add one repository per table (SCRUM-28)`.

---

### Tarea 3: Almacen sobre MySQL, controladores e inicio (SCRUM-28 parte 2, SCRUM-30)

**Archivos:**
- Modificar: `models/almacen.py` (se reescribe la parte de guardado), `models/venta.py` (agregar `volver_a_pendiente`), `controllers/controlador_clientes.py`, `controllers/controlador_inventario.py`, `controllers/controlador_usuarios.py` (solo crear, cambiar clave y eliminar), `controllers/controlador_ventas.py`, `main.py`, `views/app.py` (función de error al iniciar), `test_proyecto.py`
- Eliminar: `models/gestor_datos.py`

**Interfaces:**
- Usa: las interfaces de las Tareas 1 y 2.
- Entrega:
  - `Almacen(conexion: ConexionBD)`; atributos `prendas, clientes, usuarios, ventas, avisos`; `buscar_*` y `ventas_de` no cambian. Si las cuatro tablas de entidades están vacías, inserta `_datos_iniciales()` en una sola transacción. Si no existe ningún administrador, inserta el `Administrador` de ejemplo y agrega el aviso `"No había ningún administrador. Se creó el usuario de ejemplo 'marisol'."`.
  - Métodos de escritura: `agregar_prenda(prenda)`, `cambiar_stock_prenda(prenda, nuevo_stock: int)`, `cambiar_precio_prenda(prenda, nuevo_precio: int)`, `eliminar_prenda(prenda)`, `agregar_cliente(cliente)`, `actualizar_cliente(cliente, nombre, telefono, correo)`, `eliminar_cliente(cliente)`, `agregar_usuario(empleado)`, `cambiar_clave_usuario(empleado, clave: str)`, `eliminar_usuario(empleado)`, `registrar_venta(venta, folio: int, medio_pago: str, comprobante: str)`, `entregar_venta(venta)`, `cancelar_venta(venta)`.
  - Cada método valida primero con el modelo cuando el modelo tiene una regla (setters, `marcar_*`), ejecuta su SQL dentro de `with self._conexion.transaccion() as cursor:` y mantiene la memoria igual a la base si algo falla. Para los atributos que se cambian antes del SQL (precio, stock, datos del cliente, hash de la clave, estado de la venta), se restaura el valor anterior en `except ErrorBaseDatos:` y se relanza el error.
  - `registrar_venta`: llama a `venta.marcar_pagada(folio, medio_pago, comprobante)` y luego, en UNA transacción, `RepositorioVentas.insertar` y el `UPDATE` del stock por cada detalle (con `RepositorioPrendas.actualizar_stock` y el valor ya calculado); después de confirmar, `descontar_stock` en cada Prenda y `self.ventas.append(venta)`. Ante `ErrorBaseDatos`: `venta.volver_a_pendiente()` y se relanza.
  - `cancelar_venta`: `marcar_cancelada()` (el modelo valida), luego UNA transacción con `actualizar_estado` + devolución de stock; después de confirmar, `reponer_stock` en memoria; si falla, el estado vuelve a `PAGADA`.
  - `Venta.volver_a_pendiente() -> None`: vuelve `_estado` a `PENDIENTE` y limpia `_folio`, `_medio_pago` y `_comprobante` (la fecha queda igual). Comentario: "solo lo usa el almacén si la base de datos falla al guardar el pago".
  - `views/app.py`: `mostrar_error_inicio(mensaje: str) -> None` (crea un `tk.Tk()` oculto, muestra `messagebox.showerror("No se pudo iniciar", mensaje)` y lo destruye).
  - `main.py`: `conexion = ConexionBD(ConexionBD.leer_configuracion(Path(__file__).parent))`; `try: conexion.preparar(); almacen = Almacen(conexion)` `except ErrorBaseDatos as error: mostrar_error_inicio(str(error)); return`.
  - Los controladores mantienen todas sus validaciones y mensajes; cada par `lista.append/remove` + `guardar(...)` se reemplaza por el método de Almacen correspondiente. El cálculo del folio sigue en `ControladorVentas.registrar_venta`; se elimina `Almacen.guardar`.
  - `test_proyecto.py`: `BaseTienda.setUp` arma `ConexionBD(config_pruebas())`, `preparar()`, `vaciar_tablas`, `Almacen(conexion)`; `reabrir()` crea una `ConexionBD` y un `Almacen` nuevos sobre la misma base de pruebas. Las clases que usan la base llevan el decorador `skipUnless`; `TestValidaciones`, `TestPOO` y `TestSeparacionMVC` quedan sin decorador. Se quitan `import json`, `GestorDatos` y `tempfile` si ya no se usan.

- [ ] **Paso 1: adaptar las pruebas.** Cambiar `BaseTienda` como se indica arriba. Borrar `test_archivos_danados_se_recrean` y `test_archivo_faltante_se_recrea` (la app ya no usa JSON). Reescribir `test_usuarios_sin_administrador_se_consideran_danados` como `test_sin_administrador_se_recrea_el_de_ejemplo`: borrar las filas de Administrador con SQL, `reabrir()`, `iniciar_sesion("marisol","admin123")` funciona y `avisos` tiene una entrada. Agregar:
  - `test_venta_falla_en_la_base_y_nada_cambia`: armar una venta válida y luego borrar su prenda con SQL (la clave foránea hace fallar el insert del detalle; primero `SET FOREIGN_KEY_CHECKS=0`, borrar, y `=1` después); `almacen.registrar_venta(...)` lanza `ErrorBaseDatos`; `venta.estado == "PENDIENTE"`; el stock en memoria de la otra línea no cambia; `SELECT COUNT(*) FROM ventas` es 0; `len(almacen.ventas)` no cambia.
  - `test_falla_de_base_no_cambia_memoria`: cortar la conexión poniendo `conexion._config["puerto"]=1` y cerrando `conexion._conexion` (ajustar a los nombres reales de los atributos); `ctrl.clientes.registrar(...)` lanza `ErrorBaseDatos`; `len(almacen.clientes)` no cambia.
  - `test_cambiar_precio_persiste`: `cambiar_precio("EST-001","7000")` → `reabrir()` muestra 7000.
  - `test_cancelar_venta_persiste_estado_y_stock`: registrar, cancelar, `reabrir()` → estado `CANCELADA` y stock devuelto.
  - En `TestSeparacionMVC`: `test_solo_conexion_bd_usa_el_conector` (solo `models/conexion_bd.py` contiene `mysql.connector`, revisando models/, controllers/, views/ y `main.py`) y `test_sql_solo_en_modelos` (ningún archivo de controllers/ ni views/ contiene `SELECT `, `INSERT `, `UPDATE ` ni `DELETE `).
- [ ] **Paso 2: correr** `.venv/bin/python -m unittest -v` → las pruebas nuevas o cambiadas FALLAN.
- [ ] **Paso 3: implementar** Almacen, `Venta.volver_a_pendiente`, los cambios en los controladores, `main.py` y `mostrar_error_inicio`; eliminar `models/gestor_datos.py`; actualizar los docstrings de `main.py` y `models/almacen.py` (ya no hay JSON).
- [ ] **Paso 4: correr** `.venv/bin/python -m unittest -v` → todo PASA (sin omitidas, con MySQL encendido). Después `brew services stop mysql`, correr de nuevo → las clases con base aparecen omitidas y el resto PASA; `brew services start mysql`.
- [ ] **Paso 5: prueba de la interfaz** con `.venv/bin/python main.py`: entrar con `marisol`/`admin123`, crear un cliente, vender, cancelar la venta, cerrar y reabrir → los datos siguen ahí. Con MySQL apagado, abrir la app → aparece el diálogo "No se pudo iniciar", sin error de Python.
- [ ] **Paso 6: commit** (con aprobación): `feat: store all data in MySQL instead of JSON (SCRUM-28, SCRUM-30)`.
- [ ] **Paso 7: Bitácora**, entrada para SCRUM-28 y SCRUM-30.

---

### Tarea 4: script de importación de JSON, de una sola vez (SCRUM-29)

**Archivos:**
- Crear: `bd/migrar_json_a_mysql.py`
- Pruebas: `test_base_datos.py` (clase `TestMigracion`)

**Interfaces:**
- Usa: `ConexionBD`, `insertar` / `esta_vacio` de los repositorios y las funciones `desde_dict` de los modelos.
- Entrega:
  - `migrar(carpeta_json: Path, conexion: ConexionBD) -> dict[str, tuple[int, int]]`: lanza `ValueError("La base ya tiene datos. Para repetir la migración, borra la base 'lacasetita' en phpMyAdmin y vuelve a ejecutar este script.")` si alguno de los cuatro repositorios de entidades no está vacío; si no, lee los JSON `prendas, clientes, usuarios, ventas` con `json` + `desde_dict` e inserta todo en UNA transacción (orden: prendas, clientes, usuarios, ventas); entrega `{nombre: (registros_en_json, filas_en_tabla)}`.
  - `main()`: lee la configuración de la raíz del repo, `preparar()`, `migrar(Path("datos"), conexion)`, muestra una línea por tabla, por ejemplo `"prendas: 6 en JSON, 6 en MySQL - OK"` (o `"- DIFERENCIA"`), y termina con código 1 ante `ValueError` / `ErrorBaseDatos`, mostrando el mensaje. Se ejecuta con `.venv/bin/python -m bd.migrar_json_a_mysql`.
  - Nunca escribe en `datos/`.

- [ ] **Paso 1: escribir las pruebas que fallan** (carpeta temporal con los cuatro JSON armados con el `a_dict()` de los objetos de `_datos_iniciales()`, más una venta pagada):
  - `test_migracion_sin_perdidas`: en cada par del resultado los dos números son iguales; el `a_dict()` de los objetos recargados es igual a los diccionarios del JSON.
  - `test_segunda_migracion_se_rechaza`: la segunda llamada a `migrar` lanza `ValueError`; la cantidad de filas no cambia.
  - `test_json_danado_no_deja_datos_a_medias`: `ventas.json` contiene `"{no es json"` → lanza error; las cuatro tablas siguen vacías.
- [ ] **Paso 2: correr** `.venv/bin/python -m unittest test_base_datos.TestMigracion -v` → FALLA.
- [ ] **Paso 3: implementar** `bd/migrar_json_a_mysql.py`.
- [ ] **Paso 4: correr** → PASA. Después, la ejecución real sobre una base `lacasetita` nueva (`mysql -u root -e "DROP DATABASE IF EXISTS lacasetita"`; preguntarte antes, porque borra los datos locales) y guardar lo que muestra para la Bitácora.
- [ ] **Paso 5: commit** (con aprobación): `feat: add one-time JSON to MySQL import script (SCRUM-29)`.
- [ ] **Paso 6: Bitácora**, con la salida del script como evidencia de "sin pérdidas".

---

### Tarea 5: bloqueo de inicio de sesión persistente (HU16, SCRUM-36)

**Archivos:**
- Modificar: `models/repositorios.py` (agregar `RepositorioIntentos`), `models/almacen.py` (exponerlo), `controllers/controlador_usuarios.py` (`iniciar_sesion`), `test_proyecto.py` (`TestBloqueoLogin`)

**Interfaces:**
- Entrega:
  - `RepositorioIntentos(Repositorio)`, `TABLA = "intentos_login"`: `cargar_todos() -> list[dict]`, `obtener(usuario: str) -> dict`, que entrega `{"fallidos": int, "bloqueado_hasta": float}` (ceros si no hay fila), y `guardar(cursor, usuario: str, fallidos: int, bloqueado_hasta: float)` con `INSERT ... ON DUPLICATE KEY UPDATE`.
  - `Almacen.obtener_intentos(usuario: str) -> dict` y `Almacen.guardar_intentos(usuario: str, fallidos: int, bloqueado_hasta: float) -> None`.
  - `ControladorUsuarios.iniciar_sesion` lee el estado con `obtener_intentos(nombre)` al comienzo y llama a `guardar_intentos` después de cada cambio (fallo sumado, bloqueo fijado, reinicio por bloqueo vencido, reinicio por inicio correcto). Se elimina `self._intentos`; `reloj`, `MAX_INTENTOS`, `MINUTOS_BLOQUEO` y todos los mensajes quedan igual.

- [ ] **Paso 1: escribir las pruebas que fallan** en `TestBloqueoLogin` (las pruebas existentes se mantienen y deben seguir pasando):
  - `test_bloqueo_sobrevive_al_reinicio`: fallar 5 veces; `reabrir()`, poner el mismo `RelojFalso` como `_reloj` del controlador nuevo; con la clave correcta sigue lanzando un error con `"minuto"` en el mensaje; después de `avanzar_minutos(MINUTOS_BLOQUEO)` el inicio de sesión funciona.
  - `test_login_correcto_reinicia_contador_guardado`: fallar 4 veces, entrar bien, `almacen.obtener_intentos("carlos")["fallidos"] == 0`.
  - `test_usuario_inexistente_crea_registro`: fallar una vez con `"nadie"` → `obtener_intentos("nadie")["fallidos"] == 1`.
  - `test_bloqueo_ignora_mayusculas_y_espacios`: fallar 5 veces alternando `" Carlos "` y `"carlos"` → la cuenta queda bloqueada.
- [ ] **Paso 2: correr** `.venv/bin/python -m unittest test_proyecto.TestBloqueoLogin -v` → las pruebas nuevas FALLAN.
- [ ] **Paso 3: implementar** según las Interfaces.
- [ ] **Paso 4: correr** `.venv/bin/python -m unittest -v` → todo PASA.
- [ ] **Paso 5: commit** (con aprobación): `feat: persist login lockout in the database (SCRUM-36)`.
- [ ] **Paso 6: Bitácora**, entrada para SCRUM-36.

---

### Tarea 6: documentación y revisión de un compañero

**Archivos:**
- Modificar: `README.md` (reemplazar "No hay que instalar nada más..." por los pasos de instalación: venv, `pip install -r requirements.txt`, XAMPP en Windows con `py -m venv .venv` y `.venv\Scripts\python`, MySQL de Homebrew en Mac, `config_bd.local.ini` para una contraseña, el script de migración y cómo correr las pruebas; indicar el orden de forma explícita: para migrar los JSON, correr `bd/migrar_json_a_mysql.py` ANTES de abrir la app por primera vez, porque la app inserta los datos de ejemplo en las tablas vacías y después el script se niega; si la app ya se abrió, borrar la base `lacasetita` en phpMyAdmin y empezar de nuevo; los compañeros que solo necesitan usar la app no corren el script, porque `datos/` tiene los mismos datos de ejemplo), `GUIA_DE_SINTAXIS.md` (reemplazar la sección 7 "JSON" por "Base de datos": `with` como transacción, parámetros `%s`, cursor de diccionarios, `Repositorio` como clase abstracta; dejar una línea que diga que la app usó JSON hasta el Parcial 2 y que los archivos siguen en `datos/`), `.claude/CLAUDE.md` en Key Commands (comandos con venv, `brew services start mysql`, script de migración), `$HOME/.claude/knowledge/Projects/lacasetitadelascamisetas/decisions.md` (sección de guardado: MySQL, repositorios, regla de escritura, `datos/` como el "antes"; marcar como reemplazadas las viñetas sobre JSON/`.corrupto` y "datos/ is git-ignored").

- [ ] **Paso 1: escribir la documentación** indicada.
- [ ] **Paso 2: verificar** `.venv/bin/python -m unittest -v` → todo PASA; `grep -rn "gestor_datos\|GestorDatos\|\.json" models controllers views main.py` → sin resultados, salvo comentarios que mencionen el JSON antiguo a propósito.
- [ ] **Paso 3: commit** (con aprobación): `docs: explain MySQL setup and syntax`.
- [ ] **Paso 4: revisión de un compañero.** Pedirte que un compañero con Windows + XAMPP baje la rama (después de que tú la subas), siga los pasos del README, corra las pruebas e informe los errores. Corregir cualquier incompatibilidad con MariaDB que aparezca.
- [ ] **Paso 5:** proponerte el merge de `feature/mysql` a `main` (fast-forward, con aprobación); mover en Jira las subtareas de SCRUM-24 y SCRUM-36 solo si tú lo pides.
