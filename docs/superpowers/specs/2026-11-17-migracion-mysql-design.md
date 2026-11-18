# Design: JSON to MySQL/MariaDB migration (HU14, SCRUM-24)

Date: 2026-11-17. Status: draft, pending user approval.
Spanish companion: `2026-11-17-migracion-mysql-design.es.md` (this English file is the source of truth).

## 1. Intent

The teacher's third test (Parcial 3) requires replacing JSON persistence with a relational database (MySQL via XAMPP/WAMP). Jira HU14 (SCRUM-24) acceptance criteria:

- Entity-relationship model with tables for garments, clients, users, sales and sale detail (SCRUM-26, SCRUM-27).
- Foreign keys prevent sales with non-existent garments or clients.
- Current JSON data is migrated without loss (SCRUM-29).
- The application behaves exactly as before; automated tests pass (SCRUM-28, SCRUM-30).

The students must explain every line to the teacher, and the user wants the solution to stay clearly object-oriented.

Also in scope: HU16 (SCRUM-36, Sprint 4, created 2026-11-17), persistent login lockout. Acceptance criteria: failed attempts and unlock time per username are stored in the database; closing and reopening the app during a lockout keeps the account locked until the 10 minutes pass; a successful login resets the counter; attempts with a non-existent username are recorded too (do not reveal which users exist); HU01 rules stay (5 consecutive failures lock for 10 minutes, RNF-04). Section 5.7.

## 2. Goals, non-goals, anti-goals

Goals
- Every write is a specific, readable SQL statement inside a method whose name says what it does.
- Registering and cancelling a sale run in one transaction (sale + detail + stock).
- Same GUI, same business rules, same error messages.
- Runs on the Mac (Homebrew MySQL) and on teammates' Windows (XAMPP, MariaDB 10.4) with the same code and SQL.

Non-goals
- Reading from the database on every screen refresh (lists stay in memory as today).
- Any change to views beyond the startup error message.

Anti-goals (would be a failure even if it works)
- SQL hidden behind a generic "sync whole table" routine (looks like JSON in disguise).
- An ORM, extra libraries or patterns the students cannot explain.
- SQL that only runs on one engine.

## 3. Constraints

- Python 3.10+, standard library plus `mysql-connector-python` (approved 2026-11-17). Installed in a venv, listed in `requirements.txt`.
- Engines: MySQL (Homebrew, Mac) and MariaDB 10.4 (XAMPP). Portable SQL: InnoDB, `utf8mb4` with collation `utf8mb4_unicode_ci` (MySQL 8's default `utf8mb4_0900_ai_ci` does not exist in MariaDB), types INT / VARCHAR / DATETIME / DECIMAL only, no JSON columns, no MySQL-8-only syntax.
- Code identifiers, comments and UI strings in Spanish, commented like the rest of the project.
- MVC layering stays: models/ knows nothing of controllers or views; controllers have no Tkinter.

## 4. Approaches considered

- A. Swap only the storage manager: `guardar("clientes")` upserts the whole table and deletes missing rows; controllers untouched. Smallest change, but SQL is generic and hidden, sale + stock is not one transaction, and it reads as JSON in disguise. Rejected.
- B. One SQL statement per operation (chosen by the user): in-memory lists stay for reads; each change becomes a named method with its own SQL; sales use a transaction. About 20 lines change in controllers.
- C. Always read from the database (no in-memory lists): rewrites all reads and adds a lot to explain without improving the grade. Rejected.

## 5. Design (approach B, object-oriented)

### 5.1 Classes

```
models/
  conexion_bd.py      ConexionBD        opens the connection from the config, creates the database
                                         and tables if missing, offers transaccion() (context manager)
  repositorios.py     Repositorio (ABC) base: holds the ConexionBD; abstract cargar_todos() -> list
                      RepositorioPrendas(Repositorio)   insertar, actualizar_stock, actualizar_precio, eliminar
                      RepositorioClientes(Repositorio)  insertar, actualizar, eliminar
                      RepositorioUsuarios(Repositorio)  insertar, actualizar_clave, eliminar
                      RepositorioVentas(Repositorio)    insertar (sale + detail rows), actualizar_estado
  almacen.py          Almacen           composition: owns the 4 repositories and the 4 in-memory lists
  gestor_datos.py     removed (the app no longer reads or writes JSON; it stays in git history)
bd/                   NEW folder: everything about the MySQL database lives here
  esquema.sql         CREATE DATABASE / CREATE TABLE statements (read by ConexionBD, also usable in phpMyAdmin)
  migrar_json_a_mysql.py  standalone one-time script: reads datos/*.json, inserts into the tables,
                      prints a count per file vs per table as proof of "no loss" (SCRUM-29)
datos/                OLD folder, kept untouched as the "before": the JSON files the app used until Parcial 2
config_bd.ini         committed defaults (localhost, 3306, root, empty password, database name)
config_bd.local.ini   git-ignored per-machine override (e.g. a real password)
```

OOP points the students can name: abstraction and inheritance (`Repositorio` is an ABC, each repository inherits and implements `cargar_todos`), polymorphism (Almacen loads all four the same way through `cargar_todos`), encapsulation (only `ConexionBD` touches the connector; only repositories contain SQL), composition (Almacen has repositories; Venta has DetalleVenta).

Rows are read with a dictionary cursor, so each repository rebuilds objects by reusing the existing `desde_dict` / `prenda_desde_dict` functions. `a_dict` stays the source of the values for INSERTs.

### 5.2 Tables

| Table | Key | Columns | Notes |
|---|---|---|---|
| prendas | codigo VARCHAR PK | tipo, nombre, talla, precio_base INT, stock INT, tipo_cuello, nivel_termico, tipo_manga, tipo_elastico, ajuste (type-specific columns NULL when not applicable) | single table for the 3 subclasses, `tipo` chooses the class |
| clientes | rut VARCHAR PK | nombre, telefono, correo | |
| usuarios | rut VARCHAR PK | usuario VARCHAR UNIQUE, nombre, rol, clave_hash CHAR(64) | |
| ventas | folio INT PK | fecha DATETIME, vendedor, cliente_rut FK -> clientes.rut, cliente_nombre, descuento_cliente, estado, medio_pago, comprobante | folio assigned by the app as today (max + 1) |
| detalle_venta | id INT AUTO_INCREMENT PK | folio FK -> ventas.folio, codigo FK -> prendas.codigo, descripcion, cantidad, subtotal | |

All foreign keys `ON DELETE RESTRICT`. `ventas.vendedor` has no foreign key on purpose: the app allows deleting employees, and the sale keeps the seller's name as a snapshot (same reason as `cliente_nombre`).

### 5.3 Write rule: database first, memory after

Each Almacen write method runs its SQL first; only if it succeeds does it change the in-memory list. If the database fails, memory stays as it was and the error reaches the screen as a message. Examples:

- `almacen.agregar_cliente(cliente)`: `INSERT INTO clientes ...`, then `self.clientes.append(cliente)`.
- `almacen.registrar_venta(venta)`: inside `with conexion.transaccion():` insert the sale, insert each detail row, `UPDATE prendas SET stock = stock - %s WHERE codigo = %s` per line; commit; then discount stock on the Prenda objects and append the sale. Any error rolls back the whole transaction.
- `almacen.cancelar_venta(venta)`: same pattern (state update + stock return in one transaction).

Controllers keep every business validation they do today and replace `lista.append(...)` + `guardar("x")` with the matching Almacen method. `Almacen.guardar(nombre)` is removed.

All SQL uses `%s` parameters, never string formatting (prevents SQL injection, easy to explain).

### 5.4 Startup

1. `ConexionBD` reads `config_bd.ini`, then `config_bd.local.ini` if present.
2. Connects to the server; `CREATE DATABASE IF NOT EXISTS`; creates tables with `CREATE TABLE IF NOT EXISTS` (same SQL as `bd/esquema.sql`, read from that file so there is one source).
3. If all tables are empty, the current seed data (`_datos_iniciales()`) is inserted. The JSON import is NOT done by the app: it is the separate script `bd/migrar_json_a_mysql.py`, run once by hand (SCRUM-29); its output goes to the Bitácora as evidence.
4. Almacen loads the four lists via `cargar_todos()`.
5. The rule "there must be at least one administrator" is kept: if `usuarios` has none, the seed administrator is inserted with a notice.
6. If the server is unreachable, the app shows a clear Tkinter error ("No se pudo conectar a MySQL. Revisa que XAMPP/MySQL esté encendido.") and closes instead of crashing with a traceback.

The corrupt-JSON recovery (`.corrupto` files) is removed with the JSON code. The `datos/` folder is not deleted: it stays as the "before" so the team can show the teacher the JSON files next to the new `bd/` folder and explain the replacement. The app never touches it.

### 5.5 Tests

- Business tests keep their current shape; `BaseTienda.setUp` builds the Almacen against a separate database `lacasetita_test`, dropping and recreating the tables before each test.
- Safeguard: the test base class refuses to drop tables unless the configured database name is exactly `lacasetita_test`, so tests can never wipe the real data.
- If MySQL is not reachable, database tests are skipped with a clear message (pure tests like validations and POO keep running).
- New tests: foreign keys reject a sale for a non-existent client/garment; registering a sale is all-or-nothing (forced failure leaves stock and sales unchanged); the migration script imports a sample JSON folder (temp dir) into `lacasetita_test` without loss; persistence across a new Almacen instance.
- `TestSeparacionMVC` is extended so only `conexion_bd.py` imports `mysql.connector` and only models/ contains SQL.

### 5.7 Persistent login lockout (HU16, SCRUM-36)

- New table `intentos_login`: `usuario VARCHAR PK`, `fallidos INT NOT NULL DEFAULT 0`, `bloqueado_hasta DOUBLE NOT NULL DEFAULT 0` (seconds since epoch, same value `time.time()` returns today). No foreign key to `usuarios`: attempts with non-existent usernames must be stored too.
- New `RepositorioIntentos(Repositorio)` with `obtener(usuario) -> dict` (returns `{"fallidos": 0, "bloqueado_hasta": 0}` when there is no row) and `guardar(usuario, fallidos, bloqueado_hasta)` (`INSERT ... ON DUPLICATE KEY UPDATE`, valid on MySQL and MariaDB). Its `cargar_todos()` returns all rows, to honour the base class contract.
- Unlike the other entities, lockout state is not kept in a memory list: `ControladorUsuarios.iniciar_sesion` reads the state from the repository (through Almacen) at the start of each attempt and saves it after each change. The `self._intentos` dictionary is removed. Reason: the state only matters at login time and must survive a restart; one read and one write per attempt is negligible.
- The injectable clock (`reloj`) stays, so tests still simulate the 10 minutes without waiting.
- Login logic, constants `MAX_INTENTOS` / `MINUTOS_BLOQUEO` and messages do not change.
- New tests: a lockout survives creating a new Almacen + controller on the same database; a successful login resets the stored counter; a non-existent username creates a row.
- Implemented after HU14 is working (it needs `ConexionBD` and the repository base class).

### 5.6 Docs and tracking

- README: install steps (venv, `pip install -r requirements.txt`, XAMPP on Windows, Homebrew MySQL on Mac, `config_bd.local.ini`), replacing the "solo librería estándar" sentence.
- `GUIA_DE_SINTAXIS.md`: short entries for `with` as transaction, `%s` parameters, ABC repository.
- Each implementation step is logged in Confluence "Bitácora de Sprints", Sprint 4 section, with date, commit and Jira key (SCRUM-26..30).

## 6. Decided by the user

- Approach B (SQL per operation, in-memory lists for reads), 2026-11-17.
- Must remain clearly object-oriented.
- `mysql-connector-python` allowed.
- JSON is replaced completely in the app; the `datos/` folder is kept (not deleted) as the "before", and a new folder `bd/` holds the database part, to explain the replacement (2026-11-17).
- Persistent login lockout is a new user story (HU16, SCRUM-36) and part of this work; the sprint choice was delegated to Claude (Sprint 4, because its theme is persistence and HU16 depends on HU14).

## 7. Calls made by Claude (user may override)

- Single `prendas` table with nullable type columns (simplest to explain; three subclass tables would add JOINs for no gain here).
- Folio stays app-assigned, not AUTO_INCREMENT, to keep the current folio logic and tests.
- No foreign key on `ventas.vendedor` (employees can be deleted).
- Repositories as separate classes in one file `models/repositorios.py`.
- Tests use database `lacasetita_test` and skip when MySQL is down.
- Migration script lives in `bd/` next to the schema, so the new folder holds everything about the database.
- If the script runs against tables that already have rows, it stops without inserting (avoids duplicates).

## 8. Left to the builder

- Exact column lengths, method names inside repositories, and the wording of comments.
- Where the startup error dialog lives (a small function in views/).
