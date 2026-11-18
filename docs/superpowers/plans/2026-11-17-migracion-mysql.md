# JSON to MySQL Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the app's JSON persistence with MySQL/MariaDB (HU14, SCRUM-24) and persist the login lockout (HU16, SCRUM-36), keeping the GUI and business rules unchanged.

**Architecture:** `ConexionBD` wraps the connector and transactions; one repository class per table inherits from an abstract `Repositorio` and holds that table's SQL; `Almacen` composes the repositories, keeps the in-memory lists for reads and exposes one named write method per operation (database first, memory after). JSON leaves the app; `datos/` stays untouched as the "before" and the one-time import lives in the new `bd/` folder.

**Tech Stack:** Python 3.13 (Homebrew `python@3.13`, has Tkinter), `mysql-connector-python` in `.venv`, MySQL 26.10 (Homebrew) locally, MariaDB 10.4 (XAMPP) on teammates' Windows, unittest.

**Spec:** `docs/superpowers/specs/2026-11-17-migracion-mysql-design.md`

## Global Constraints

- Standard library plus `mysql-connector-python` only; pinned in `requirements.txt`.
- Portable SQL: `ENGINE=InnoDB`, `DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`, types INT / VARCHAR / CHAR / DATETIME / DOUBLE only, no JSON columns, no `utf8mb4_0900_ai_ci`, no MySQL-8-only syntax. Upserts with `INSERT ... ON DUPLICATE KEY UPDATE`.
- Every SQL value goes through `%s` parameters, never f-strings.
- Only `models/conexion_bd.py` imports `mysql.connector`; only `models/` contains SQL; controllers have no Tkinter; models import nothing from controllers/views.
- Identifiers, comments and UI strings in Spanish, commented line by line in the same style as the existing files (students must explain every line).
- Write rule: change the database first; change memory only after the commit succeeds. On failure memory is left (or restored) exactly as before and an `ErrorBaseDatos` reaches the caller.
- `datos/` is never modified or deleted.
- Git: work on branch `feature/mysql`. Every "Commit" step means: show the user the commit summary (files, description) and wait for approval; never push.
- Every "Bitácora" step (Confluence) and any Jira change also appends one dated line to `$HOME/GitHub/ing-requisitos/recursos/registro-jira-confluence.md` in the same session (commit there needs approval too).
- Run commands from the repo root with the venv: `.venv/bin/python -m unittest -v`.

## Review Focus

1. MySQL stops while the app is open → the operation shows an error and the in-memory lists are unchanged (test in Task 3: `test_falla_de_base_no_cambia_memoria`).
2. Names with tildes and ñ (`"Ñuñoa Pérez"`) survive a reopen byte-for-byte (test in Task 2: `test_tildes_y_enie_sobreviven`).
3. Schema run on MariaDB 10.4 (XAMPP) → no MySQL-only constructs (test in Task 1: `test_esquema_es_portable`; plus a teammate's manual check, Task 6).
4. Migration script run twice → second run refuses, no duplicates (test in Task 4: `test_segunda_migracion_se_rechaza`).
5. Login with `" Carlos "` and `"carlos"` share the same lockout row (test in Task 5: `test_bloqueo_ignora_mayusculas_y_espacios`).

---

### Task 1: Environment, configuration, schema and `ConexionBD` (SCRUM-26, SCRUM-27)

**Files:**
- Create: `requirements.txt`, `config_bd.ini`, `bd/__init__.py` (empty, so `python -m bd.migrar_json_a_mysql` works), `bd/esquema.sql`, `models/conexion_bd.py`, `test_base_datos.py`
- Modify: `.gitignore` (add `.venv/` and `config_bd.local.ini`), `models/excepciones.py` (add `ErrorBaseDatos`)

**Interfaces:**
- Produces:
  - `class ErrorBaseDatos(Exception)` in `models/excepciones.py`.
  - `ConexionBD(config: dict)` with keys `host, puerto, usuario, clave, base_datos`.
  - `ConexionBD.leer_configuracion(carpeta: Path) -> dict` (static): reads `config_bd.ini` section `[mysql]`, then overlays `config_bd.local.ini` if present (configparser).
  - `ConexionBD.preparar() -> None`: connects to the server, `CREATE DATABASE IF NOT EXISTS <base_datos> CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`, selects it, runs every statement of `bd/esquema.sql` (split on `;`, skip blanks).
  - `ConexionBD.transaccion()` (contextmanager) yields a dictionary cursor; commit on success, rollback on any exception; `mysql.connector.Error` is re-raised as `ErrorBaseDatos` with a Spanish message.
  - `ConexionBD.consultar(sql: str, parametros: tuple = ()) -> list[dict]`.
  - `ConexionBD.base_datos` (property, str).
  - Connection failure in `preparar()` raises `ErrorBaseDatos("No se pudo conectar a MySQL. Revisa que XAMPP/MySQL esté encendido.")`.
- Test helper (in `test_base_datos.py`, reused by later tasks): `config_pruebas() -> dict` (repo config with `base_datos="lacasetita_test"`), `mysql_disponible() -> bool`, `vaciar_tablas(conexion)` which raises `RuntimeError` unless `conexion.base_datos == "lacasetita_test"`, then `SET FOREIGN_KEY_CHECKS=0`, `DELETE FROM` each table, `SET FOREIGN_KEY_CHECKS=1`. Database test classes use `@unittest.skipUnless(mysql_disponible(), "MySQL no está disponible")`.

Schema (`bd/esquema.sql`, all `CREATE TABLE IF NOT EXISTS`, header comment: "en phpMyAdmin, selecciona primero la base lacasetita"):
- `prendas(codigo VARCHAR(20) PK, tipo VARCHAR(20) NOT NULL, nombre VARCHAR(60) NOT NULL, talla VARCHAR(5) NOT NULL, precio_base INT NOT NULL, stock INT NOT NULL, tipo_cuello, nivel_termico, tipo_manga, tipo_elastico, ajuste VARCHAR(20) NULL)`
- `clientes(rut VARCHAR(12) PK, nombre VARCHAR(60) NOT NULL, telefono VARCHAR(20) NOT NULL, correo VARCHAR(80) NOT NULL)`
- `usuarios(rut VARCHAR(12) PK, usuario VARCHAR(30) NOT NULL UNIQUE, nombre VARCHAR(60) NOT NULL, rol VARCHAR(20) NOT NULL, clave_hash CHAR(64) NOT NULL)`
- `ventas(folio INT PK, fecha DATETIME NOT NULL, vendedor VARCHAR(60) NOT NULL, cliente_rut VARCHAR(12) NOT NULL FK→clientes(rut), cliente_nombre VARCHAR(60) NOT NULL, descuento_cliente INT NOT NULL, estado VARCHAR(12) NOT NULL, medio_pago VARCHAR(30) NOT NULL, comprobante VARCHAR(60) NULL)`
- `detalle_venta(id INT AUTO_INCREMENT PK, folio INT NOT NULL FK→ventas(folio), codigo VARCHAR(20) NOT NULL FK→prendas(codigo), descripcion VARCHAR(80) NOT NULL, cantidad INT NOT NULL, subtotal INT NOT NULL)`
- `intentos_login(usuario VARCHAR(30) PK, fallidos INT NOT NULL DEFAULT 0, bloqueado_hasta DOUBLE NOT NULL DEFAULT 0)` (used in Task 5, created now so the schema is complete)
- All FKs `ON DELETE RESTRICT`; all tables `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`. Before writing, check real max lengths in `models/validaciones.py` and widen any VARCHAR that is shorter.

- [ ] **Step 1: Prepare environment.** `git switch -c feature/mysql`; `brew services start mysql`; `/opt/homebrew/opt/python@3.13/bin/python3.13 -m venv .venv`; `.venv/bin/pip install mysql-connector-python`; pin the installed version in `requirements.txt` (`.venv/bin/pip freeze | grep -i mysql-connector`). Verify passwordless root: `mysql -u root -e "SELECT VERSION();"` prints a version. If root has a password, stop and ask the user (credential rules: never see it; use `config_bd.local.ini` filled by the user).
- [ ] **Step 2: Write failing tests** in `test_base_datos.py`, class `TestConexionBD`:
  - `test_preparar_crea_las_seis_tablas`: after `preparar()`, `SHOW TABLES` returns exactly `{"prendas","clientes","usuarios","ventas","detalle_venta","intentos_login"}`.
  - `test_preparar_dos_veces_no_falla`: calling `preparar()` twice raises nothing.
  - `test_clave_foranea_rechaza_venta_de_cliente_inexistente`: `INSERT INTO ventas` with `cliente_rut="99999999-9"` inside `transaccion()` raises `ErrorBaseDatos`; `SELECT COUNT(*) FROM ventas` stays 0.
  - `test_clave_foranea_rechaza_detalle_de_prenda_inexistente`: same with a `detalle_venta` row whose `codigo="NO-EXISTE"`.
  - `test_transaccion_hace_rollback`: insert a client then raise `ValueError` inside the `with`; the client is not in the table.
  - `test_servidor_inalcanzable_da_error_claro`: `ConexionBD({**config_pruebas(), "puerto": 1})` → `preparar()` raises `ErrorBaseDatos` whose text contains `"No se pudo conectar a MySQL"`. (Not skipped when MySQL is down.)
  - `test_vaciar_tablas_se_niega_fuera_de_la_base_de_pruebas`: `vaciar_tablas` on a `ConexionBD` with `base_datos="lacasetita"` raises `RuntimeError` without connecting.
  - `test_esquema_es_portable`: text of `bd/esquema.sql` does not contain `0900`, ` JSON`, `CHECK (`; contains `utf8mb4_unicode_ci` and `InnoDB`.
- [ ] **Step 3: Run** `.venv/bin/python -m unittest test_base_datos -v` → FAIL (`ModuleNotFoundError: models.conexion_bd`).
- [ ] **Step 4: Implement** `ErrorBaseDatos`, `config_bd.ini` (`host=localhost, puerto=3306, usuario=root, clave=, base_datos=lacasetita`), `bd/esquema.sql`, `models/conexion_bd.py` per Interfaces. One connection opened in `preparar()` and reused; `transaccion()` calls `self._conexion.ping(reconnect=True)` first (confirm the signature in the connector docs via context7 before using it).
- [ ] **Step 5: Run** `.venv/bin/python -m unittest test_base_datos -v` → all PASS.
- [ ] **Step 6: Commit** (with user approval): `feat: add MySQL connection, schema and config (SCRUM-26, SCRUM-27)`.
- [ ] **Step 7: Bitácora.** Add a Sprint 4 entry in Confluence page 15499265 (date, commit hash, SCRUM-26/27, one line on what was done).

---

### Task 2: Repositories (SCRUM-28, part 1)

**Files:**
- Create: `models/repositorios.py`
- Test: `test_base_datos.py` (new class `TestRepositorios`)

**Interfaces:**
- Consumes: `ConexionBD.transaccion()`, `ConexionBD.consultar()`, existing `prenda_desde_dict`, `Cliente.desde_dict`, `Empleado.desde_dict`, `Venta.desde_dict`, and each model's `a_dict()`.
- Produces (every write method takes the open `cursor` as first argument so Almacen can group several writes in one transaction):
  - `class Repositorio(ABC)`: `__init__(self, conexion: ConexionBD)`; `@abstractmethod cargar_todos(self) -> list`; `esta_vacio(self) -> bool` using class attribute `TABLA`.
  - `RepositorioPrendas`: `cargar_todos() -> list[Prenda]` (ORDER BY codigo), `insertar(cursor, prenda)`, `actualizar_stock(cursor, codigo: str, stock: int)`, `actualizar_precio(cursor, codigo: str, precio: int)`, `eliminar(cursor, codigo: str)`. Insert fills the five type columns with `datos.get(...)`.
  - `RepositorioClientes`: `cargar_todos()` (ORDER BY rut), `insertar(cursor, cliente)`, `actualizar(cursor, cliente)`, `eliminar(cursor, rut: str)`.
  - `RepositorioUsuarios`: `cargar_todos()` (ORDER BY rut), `insertar(cursor, empleado)`, `actualizar_clave(cursor, empleado)`, `eliminar(cursor, usuario: str)`.
  - `RepositorioVentas`: `cargar_todos() -> list[Venta]` (ventas ORDER BY folio; detalles ORDER BY id, grouped by folio; `fecha` converted with `.isoformat(timespec="seconds")` before `Venta.desde_dict`), `insertar(cursor, venta)` (sale row + one `detalle_venta` row per detail), `actualizar_estado(cursor, folio: int, estado: str)`.
  - `RepositorioIntentos` is added in Task 5.

- [ ] **Step 1: Write failing tests** (`setUp`: `preparar()` + `vaciar_tablas`):
  - `test_prenda_de_cada_tipo_ida_y_vuelta`: insert one `PrendaTermica`, `PrendaEstandar`, `RopaInterior`; `cargar_todos()` returns objects of the same classes with equal `a_dict()`.
  - `test_cliente_actualizar_y_eliminar`: insert, update phone, reload equals; delete, reload empty.
  - `test_empleado_conserva_hash_y_rol`: insert `Administrador("33.333.333-3","Marisol Mena","marisol","admin123")`; reloaded `verificar_clave("admin123")` is True and `puede_administrar()` is True.
  - `test_venta_con_detalles_ida_y_vuelta`: insert client + prendas + a paid `Venta` with 2 details; reloaded `a_dict()` equals the original's.
  - `test_tildes_y_enie_sobreviven`: client name `"Ñuñoa Pérez"` reloads identical.
  - `test_repositorio_es_abstracto`: `Repositorio(conexion)` raises `TypeError`.
- [ ] **Step 2: Run** `.venv/bin/python -m unittest test_base_datos.TestRepositorios -v` → FAIL (import error).
- [ ] **Step 3: Implement** `models/repositorios.py` per Interfaces.
- [ ] **Step 4: Run** the same command → PASS.
- [ ] **Step 5: Commit** (with approval): `feat: add one repository per table (SCRUM-28)`.

---

### Task 3: Almacen on MySQL, controllers, startup (SCRUM-28 part 2, SCRUM-30)

**Files:**
- Modify: `models/almacen.py` (rewrite persistence part), `models/venta.py` (add `volver_a_pendiente`), `controllers/controlador_clientes.py`, `controllers/controlador_inventario.py`, `controllers/controlador_usuarios.py` (create/change key/delete only), `controllers/controlador_ventas.py`, `main.py`, `views/app.py` (startup error function), `test_proyecto.py`
- Delete: `models/gestor_datos.py`

**Interfaces:**
- Consumes: Task 1 and Task 2 interfaces.
- Produces:
  - `Almacen(conexion: ConexionBD)`; attributes `prendas, clientes, usuarios, ventas, avisos`; existing `buscar_*` and `ventas_de` unchanged. If all four entity tables are empty, insert `_datos_iniciales()` in one transaction. If no administrator exists, insert the seed `Administrador` and append the aviso `"No había ningún administrador. Se creó el usuario de ejemplo 'marisol'."`.
  - Write methods: `agregar_prenda(prenda)`, `cambiar_stock_prenda(prenda, nuevo_stock: int)`, `cambiar_precio_prenda(prenda, nuevo_precio: int)`, `eliminar_prenda(prenda)`, `agregar_cliente(cliente)`, `actualizar_cliente(cliente, nombre, telefono, correo)`, `eliminar_cliente(cliente)`, `agregar_usuario(empleado)`, `cambiar_clave_usuario(empleado, clave: str)`, `eliminar_usuario(empleado)`, `registrar_venta(venta, folio: int, medio_pago: str, comprobante: str)`, `entregar_venta(venta)`, `cancelar_venta(venta)`.
  - Each method validates through the model first where the model has a rule (setters, `marcar_*`), runs its SQL in `with self._conexion.transaccion() as cursor:`, and keeps memory consistent with the database on failure. For object attributes changed before the SQL (price, stock, client fields, password hash, sale state), restore the previous value in `except ErrorBaseDatos:` and re-raise.
  - `registrar_venta`: calls `venta.marcar_pagada(folio, medio_pago, comprobante)`, then in ONE transaction: `RepositorioVentas.insertar` and `UPDATE prendas SET stock = stock - %s` per detail (via `RepositorioPrendas.actualizar_stock` with the computed value); after commit: `descontar_stock` on each Prenda and `self.ventas.append(venta)`. On `ErrorBaseDatos`: `venta.volver_a_pendiente()` and re-raise.
  - `cancelar_venta`: `marcar_cancelada()` (model validates), then ONE transaction with `actualizar_estado` + stock return; after commit `reponer_stock` in memory; on failure restore estado `PAGADA`.
  - `Venta.volver_a_pendiente() -> None`: sets `_estado` back to `PENDIENTE` and clears `_folio`, `_medio_pago`, `_comprobante` (fecha left as is). Comment: "solo lo usa el almacén si la base de datos falla al guardar el pago".
  - `views/app.py`: `mostrar_error_inicio(mensaje: str) -> None` (creates a hidden `tk.Tk()`, `messagebox.showerror("No se pudo iniciar", mensaje)`, destroys it).
  - `main.py`: `conexion = ConexionBD(ConexionBD.leer_configuracion(Path(__file__).parent))`; `try: conexion.preparar(); almacen = Almacen(conexion)` `except ErrorBaseDatos as error: mostrar_error_inicio(str(error)); return`.
  - Controllers keep every validation and message; replace each `lista.append/remove` + `guardar(...)` pair with the Almacen method. Folio calculation stays in `ControladorVentas.registrar_venta`; `Almacen.guardar` is removed.
  - `test_proyecto.py`: `BaseTienda.setUp` builds `ConexionBD(config_pruebas())`, `preparar()`, `vaciar_tablas`, `Almacen(conexion)`; `reabrir()` builds a new `ConexionBD` + `Almacen` on the same test database. Database-backed classes get the `skipUnless` decorator; `TestValidaciones`, `TestPOO`, `TestSeparacionMVC` stay undecorated. Remove `import json`, `GestorDatos`, `tempfile` if unused.

- [ ] **Step 1: Adapt tests.** Change `BaseTienda` as above. Delete `test_archivos_danados_se_recrean` and `test_archivo_faltante_se_recrea` (JSON no longer exists in the app). Rewrite `test_usuarios_sin_administrador_se_consideran_danados` as `test_sin_administrador_se_recrea_el_de_ejemplo`: delete Administrador rows via SQL, `reabrir()`, `iniciar_sesion("marisol","admin123")` works and `avisos` has one entry. Add:
  - `test_venta_falla_en_la_base_y_nada_cambia`: build a valid sale, then delete its prenda row by SQL (FK makes the detail insert fail; first `SET FOREIGN_KEY_CHECKS=0` delete, `=1` after); `almacen.registrar_venta(...)` raises `ErrorBaseDatos`; `venta.estado == "PENDIENTE"`; memory stock of the other line unchanged; `SELECT COUNT(*) FROM ventas` is 0; `len(almacen.ventas)` unchanged.
  - `test_falla_de_base_no_cambia_memoria`: close the connection's server side by setting `conexion._config["puerto"]=1` and closing `conexion._conexion` (adapt to the real attribute names); `ctrl.clientes.registrar(...)` raises `ErrorBaseDatos`; `len(almacen.clientes)` unchanged.
  - `test_cambiar_precio_persiste`: `cambiar_precio("EST-001","7000")` → `reabrir()` shows 7000.
  - `test_cancelar_venta_persiste_estado_y_stock`: register, cancel, `reabrir()` → estado `CANCELADA` and stock restored.
  - In `TestSeparacionMVC`: `test_solo_conexion_bd_usa_el_conector` (only `models/conexion_bd.py` contains `mysql.connector`, checked across models/, controllers/, views/, `main.py`) and `test_sql_solo_en_modelos` (no file in controllers/ or views/ contains `SELECT `, `INSERT `, `UPDATE `, `DELETE `).
- [ ] **Step 2: Run** `.venv/bin/python -m unittest -v` → new/changed tests FAIL.
- [ ] **Step 3: Implement** Almacen, `Venta.volver_a_pendiente`, controller changes, `main.py`, `mostrar_error_inicio`; delete `models/gestor_datos.py`; update the module docstrings in `main.py` and `models/almacen.py` (no more JSON).
- [ ] **Step 4: Run** `.venv/bin/python -m unittest -v` → all PASS (no skips with MySQL running). Then `brew services stop mysql`, run again → DB classes reported as skipped, rest PASS; `brew services start mysql`.
- [ ] **Step 5: GUI smoke test** with `.venv/bin/python main.py`: login `marisol`/`admin123`, create a client, sell, cancel the sale, close, reopen → data still there. Stop MySQL and start the app → the "No se pudo iniciar" dialog, no traceback.
- [ ] **Step 6: Commit** (with approval): `feat: store all data in MySQL instead of JSON (SCRUM-28, SCRUM-30)`.
- [ ] **Step 7: Bitácora** entry (SCRUM-28, SCRUM-30).

---

### Task 4: One-time JSON import script (SCRUM-29)

**Files:**
- Create: `bd/migrar_json_a_mysql.py`
- Test: `test_base_datos.py` (class `TestMigracion`)

**Interfaces:**
- Consumes: `ConexionBD`, repositories' `insertar` / `esta_vacio`, model `desde_dict` functions.
- Produces:
  - `migrar(carpeta_json: Path, conexion: ConexionBD) -> dict[str, tuple[int, int]]`: raises `ValueError("La base ya tiene datos. Para repetir la migración, borra la base 'lacasetita' en phpMyAdmin y vuelve a ejecutar este script.")` if any of the four entity repositories is not empty; otherwise reads `prendas, clientes, usuarios, ventas` JSON with `json` + `desde_dict` and inserts everything in ONE transaction (order: prendas, clientes, usuarios, ventas); returns `{nombre: (registros_en_json, filas_en_tabla)}`.
  - `main()`: reads config from the repo root, `preparar()`, `migrar(Path("datos"), conexion)`, prints one line per table `"prendas: 6 en JSON, 6 en MySQL - OK"` (or `"- DIFERENCIA"`), exits 1 on `ValueError` / `ErrorBaseDatos` with the message. Run as `.venv/bin/python -m bd.migrar_json_a_mysql`.
  - Never writes to `datos/`.

- [ ] **Step 1: Write failing tests** (temp folder with four JSON files built from `_datos_iniciales()` objects' `a_dict()`, plus one paid sale):
  - `test_migracion_sin_perdidas`: every tuple in the result has equal numbers; reloaded objects' `a_dict()` equal the JSON dicts.
  - `test_segunda_migracion_se_rechaza`: second `migrar` raises `ValueError`; row counts unchanged.
  - `test_json_danado_no_deja_datos_a_medias`: `ventas.json` contains `"{no es json"` → raises; all four tables still empty.
- [ ] **Step 2: Run** `.venv/bin/python -m unittest test_base_datos.TestMigracion -v` → FAIL.
- [ ] **Step 3: Implement** `bd/migrar_json_a_mysql.py`.
- [ ] **Step 4: Run** → PASS. Then the real run on a fresh `lacasetita` database (`mysql -u root -e "DROP DATABASE IF EXISTS lacasetita"`, ask the user first since it deletes local data) and save the printed output for the Bitácora.
- [ ] **Step 5: Commit** (with approval): `feat: add one-time JSON to MySQL import script (SCRUM-29)`.
- [ ] **Step 6: Bitácora** entry with the script output as evidence of "sin pérdidas".

---

### Task 5: Persistent login lockout (HU16, SCRUM-36)

**Files:**
- Modify: `models/repositorios.py` (add `RepositorioIntentos`), `models/almacen.py` (expose it), `controllers/controlador_usuarios.py` (`iniciar_sesion`), `test_proyecto.py` (`TestBloqueoLogin`)

**Interfaces:**
- Produces:
  - `RepositorioIntentos(Repositorio)`, `TABLA = "intentos_login"`: `cargar_todos() -> list[dict]`, `obtener(usuario: str) -> dict` returning `{"fallidos": int, "bloqueado_hasta": float}` (zeros when no row), `guardar(cursor, usuario: str, fallidos: int, bloqueado_hasta: float)` with `INSERT ... ON DUPLICATE KEY UPDATE`.
  - `Almacen.obtener_intentos(usuario: str) -> dict` and `Almacen.guardar_intentos(usuario: str, fallidos: int, bloqueado_hasta: float) -> None`.
  - `ControladorUsuarios.iniciar_sesion` reads the state with `obtener_intentos(nombre)` at the start and calls `guardar_intentos` after every change (failure count, lock set, lock expired reset, success reset). `self._intentos` removed; `reloj`, `MAX_INTENTOS`, `MINUTOS_BLOQUEO` and all messages unchanged.

- [ ] **Step 1: Write failing tests** in `TestBloqueoLogin` (existing tests stay and must keep passing):
  - `test_bloqueo_sobrevive_al_reinicio`: fail 5 times; `reabrir()`, set the new controller's `_reloj` to the same `RelojFalso`; correct password still raises with `"minuto"` in the message; after `avanzar_minutos(MINUTOS_BLOQUEO)` login works.
  - `test_login_correcto_reinicia_contador_guardado`: fail 4 times, log in OK, `almacen.obtener_intentos("carlos")["fallidos"] == 0`.
  - `test_usuario_inexistente_crea_registro`: fail once with `"nadie"` → `obtener_intentos("nadie")["fallidos"] == 1`.
  - `test_bloqueo_ignora_mayusculas_y_espacios`: fail 5 times alternating `" Carlos "` and `"carlos"` → account locked.
- [ ] **Step 2: Run** `.venv/bin/python -m unittest test_proyecto.TestBloqueoLogin -v` → new tests FAIL.
- [ ] **Step 3: Implement** per Interfaces.
- [ ] **Step 4: Run** `.venv/bin/python -m unittest -v` → all PASS.
- [ ] **Step 5: Commit** (with approval): `feat: persist login lockout in the database (SCRUM-36)`.
- [ ] **Step 6: Bitácora** entry (SCRUM-36).

---

### Task 6: Documentation and teammate check

**Files:**
- Modify: `README.md` (replace "No hay que instalar nada más..." with install steps: venv, `pip install -r requirements.txt`, XAMPP on Windows with `py -m venv .venv` and `.venv\Scripts\python`, Homebrew MySQL on Mac, `config_bd.local.ini` for a password, migration script, how to run tests; state the order explicitly: to migrate the JSON, run `bd/migrar_json_a_mysql.py` BEFORE opening the app for the first time, because the app inserts seed data into empty tables and the script then refuses; if the app was opened first, drop the `lacasetita` database in phpMyAdmin and start again; teammates who only need to run the app skip the script, since `datos/` holds the same seed data), `GUIA_DE_SINTAXIS.md` (replace section 7 "JSON" with "Base de datos": `with` as transaction, `%s` parameters, dictionary cursor, `Repositorio` as ABC; keep a one-line note that the app used JSON until Parcial 2 and the files remain in `datos/`), `.claude/CLAUDE.md` Key Commands (venv commands, `brew services start mysql`, migration script), `$HOME/.claude/knowledge/Projects/lacasetitadelascamisetas/decisions.md` (persistence section: MySQL, repositories, write rule, `datos/` kept as "before"; mark the JSON/`.corrupto` and "datos/ is git-ignored" bullets as superseded).

- [ ] **Step 1: Write the docs** above.
- [ ] **Step 2: Verify** `.venv/bin/python -m unittest -v` → all PASS; `grep -rn "gestor_datos\|GestorDatos\|\.json" models controllers views main.py` → no hits except comments that mention the old JSON on purpose.
- [ ] **Step 3: Commit** (with approval): `docs: explain MySQL setup and syntax`.
- [ ] **Step 4: Teammate check.** Ask the user to have a teammate with Windows + XAMPP pull the branch (after the user pushes it), run the README steps and the tests, and report errors. Fix any MariaDB incompatibility found.
- [ ] **Step 5:** Offer the user the merge of `feature/mysql` into `main` (fast-forward, with approval); move SCRUM-24 subtasks and SCRUM-36 in Jira only if the user asks.
