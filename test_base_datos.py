"""
Pruebas de la base de datos MySQL: conexión, tablas, claves foráneas, repositorios y migración.
Para ejecutar: .venv/bin/python -m unittest test_base_datos -v

Las pruebas usan una base aparte llamada 'lacasetita_test', así nunca tocan los datos reales.
Si MySQL está apagado, las pruebas que lo necesitan se omiten (aparecen como 'skipped').
"""

import unittest
from pathlib import Path

from models.conexion_bd import ConexionBD
from models.excepciones import ErrorBaseDatos

# Carpeta del proyecto (donde están config_bd.ini y la carpeta bd/).
RAIZ = Path(__file__).parent
# Nombre de la base de pruebas. Solo esta base se puede vaciar desde las pruebas.
BASE_PRUEBAS = "lacasetita_test"
# Las tablas del sistema, en el orden en que se pueden vaciar.
TABLAS = ["detalle_venta", "ventas", "prendas", "clientes", "usuarios", "intentos_login"]


# Configuración del proyecto, pero apuntando a la base de pruebas.
def config_pruebas() -> dict:
    config = ConexionBD.leer_configuracion(RAIZ)
    config["base_datos"] = BASE_PRUEBAS
    return config


# Responde True si se puede conectar a MySQL. Se usa para omitir pruebas cuando el servidor está apagado.
def mysql_disponible() -> bool:
    try:
        ConexionBD(config_pruebas()).preparar()
        return True
    except ErrorBaseDatos:
        return False


# Se calcula una sola vez al cargar este archivo.
MYSQL_DISPONIBLE = mysql_disponible()


# Borra todas las filas de todas las tablas. Protección: se niega si la base no es la de pruebas.
def vaciar_tablas(conexion: ConexionBD) -> None:
    if conexion.base_datos != BASE_PRUEBAS:
        raise RuntimeError(f"Por seguridad, solo se puede vaciar la base '{BASE_PRUEBAS}'.")
    with conexion.transaccion() as cursor:
        # Se desactivan las claves foráneas un momento para poder borrar en cualquier orden.
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        for tabla in TABLAS:
            cursor.execute(f"DELETE FROM {tabla}")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")


# Crea una conexión a la base de pruebas, con las tablas creadas y vacías.
def conexion_limpia() -> ConexionBD:
    conexion = ConexionBD(config_pruebas())
    conexion.preparar()
    vaciar_tablas(conexion)
    return conexion


# Estas pruebas no necesitan que MySQL esté encendido.
class TestConexionSinServidor(unittest.TestCase):
    def test_servidor_inalcanzable_da_error_claro(self):
        conexion = ConexionBD({**config_pruebas(), "puerto": 1})
        with self.assertRaises(ErrorBaseDatos) as contexto:
            conexion.preparar()
        self.assertIn("No se pudo conectar a MySQL", str(contexto.exception))

    def test_vaciar_tablas_se_niega_fuera_de_la_base_de_pruebas(self):
        conexion = ConexionBD({**config_pruebas(), "base_datos": "lacasetita"})
        with self.assertRaises(RuntimeError):
            vaciar_tablas(conexion)

    def test_esquema_es_portable(self):
        texto = (RAIZ / "bd" / "esquema.sql").read_text(encoding="utf-8")
        self.assertNotIn("0900", texto)
        self.assertNotIn(" JSON", texto)
        self.assertNotIn("CHECK (", texto)
        self.assertIn("utf8mb4_unicode_ci", texto)
        self.assertIn("InnoDB", texto)


@unittest.skipUnless(MYSQL_DISPONIBLE, "MySQL no está disponible")
class TestConexionBD(unittest.TestCase):
    def setUp(self):
        self.conexion = conexion_limpia()

    def contar(self, tabla):
        return self.conexion.consultar(f"SELECT COUNT(*) AS total FROM {tabla}")[0]["total"]

    def test_preparar_crea_las_seis_tablas(self):
        filas = self.conexion.consultar("SHOW TABLES")
        nombres = {list(fila.values())[0] for fila in filas}
        self.assertEqual(nombres, set(TABLAS))

    def test_preparar_dos_veces_no_falla(self):
        self.conexion.preparar()
        self.conexion.preparar()

    def test_clave_foranea_rechaza_venta_de_cliente_inexistente(self):
        with self.assertRaises(ErrorBaseDatos):
            with self.conexion.transaccion() as cursor:
                cursor.execute(
                    "INSERT INTO ventas (folio, fecha, vendedor, cliente_rut, cliente_nombre, descuento_cliente,"
                    " estado, medio_pago, comprobante) VALUES (1001, NOW(), 'carlos', '99999999-9', 'Nadie', 0,"
                    " 'PAGADA', 'Efectivo', NULL)"
                )
        self.assertEqual(self.contar("ventas"), 0)

    def test_clave_foranea_rechaza_detalle_de_prenda_inexistente(self):
        with self.assertRaises(ErrorBaseDatos):
            with self.conexion.transaccion() as cursor:
                cursor.execute("INSERT INTO clientes VALUES ('11111111-1', 'Juan Perez', '+56911223344', 'juan@correo.cl')")
                cursor.execute(
                    "INSERT INTO ventas (folio, fecha, vendedor, cliente_rut, cliente_nombre, descuento_cliente,"
                    " estado, medio_pago, comprobante) VALUES (1001, NOW(), 'carlos', '11111111-1', 'Juan Perez', 0,"
                    " 'PAGADA', 'Efectivo', NULL)"
                )
                cursor.execute(
                    "INSERT INTO detalle_venta (folio, codigo, descripcion, cantidad, subtotal)"
                    " VALUES (1001, 'NO-EXISTE', 'Fantasma', 1, 1000)"
                )
        self.assertEqual(self.contar("detalle_venta"), 0)
        self.assertEqual(self.contar("ventas"), 0)

    def test_transaccion_hace_rollback(self):
        with self.assertRaises(ValueError):
            with self.conexion.transaccion() as cursor:
                cursor.execute("INSERT INTO clientes VALUES ('11111111-1', 'Juan Perez', '+56911223344', 'juan@correo.cl')")
                raise ValueError("falla a propósito")
        self.assertEqual(self.contar("clientes"), 0)


@unittest.skipUnless(MYSQL_DISPONIBLE, "MySQL no está disponible")
class TestRepositorios(unittest.TestCase):
    def setUp(self):
        from models.repositorios import (
            RepositorioClientes,
            RepositorioIntentos,
            RepositorioPrendas,
            RepositorioUsuarios,
            RepositorioVentas,
        )
        self.conexion = conexion_limpia()
        self.repo_prendas = RepositorioPrendas(self.conexion)
        self.repo_clientes = RepositorioClientes(self.conexion)
        self.repo_usuarios = RepositorioUsuarios(self.conexion)
        self.repo_ventas = RepositorioVentas(self.conexion)
        self.repo_intentos = RepositorioIntentos(self.conexion)

    def test_prenda_insertar_y_cargar(self):
        from models.prenda import PrendaTermica
        prenda = PrendaTermica("TER-999", "Beatle Test", "M", 12000, 10, "Tortuga", "Alto")
        with self.conexion.transaccion() as cursor:
            self.repo_prendas.insertar(cursor, prenda)
        cargadas = self.repo_prendas.cargar_todos()
        self.assertEqual(len(cargadas), 1)
        self.assertEqual(cargadas[0].codigo, "TER-999")
        self.assertEqual(cargadas[0].nombre, "Beatle test")

    def test_venta_insertar_guarda_cabecera_y_detalle(self):
        from models.prenda import PrendaEstandar
        from models.usuario import Cliente
        from models.venta import Venta
        prenda = PrendaEstandar("EST-900", "Polera Test", "S", 5000, 10, "Corta")
        cliente = Cliente("11.111.111-1", "Juan Perez", "+56911223344", "juan@correo.cl")
        with self.conexion.transaccion() as cursor:
            self.repo_prendas.insertar(cursor, prenda)
            self.repo_clientes.insertar(cursor, cliente)
        venta = Venta("carlos")
        venta.asignar_cliente(cliente, 5)
        venta.agregar_prenda(prenda, 2)
        venta.marcar_pagada(1001, "Efectivo", "")
        with self.conexion.transaccion() as cursor:
            self.repo_ventas.insertar(cursor, venta)
        cabecera = self.conexion.consultar("SELECT descuento_cliente, estado FROM ventas WHERE folio = 1001")
        self.assertEqual(cabecera[0]["descuento_cliente"], 5)
        self.assertEqual(cabecera[0]["estado"], "PAGADA")
        detalle = self.conexion.consultar("SELECT codigo, cantidad FROM detalle_venta WHERE folio = 1001")
        self.assertEqual(len(detalle), 1)
        self.assertEqual(detalle[0]["cantidad"], 2)

    def test_cliente_crud(self):
        from models.usuario import Cliente
        cliente = Cliente("11.111.111-1", "Juan Perez", "+56911223344", "juan@correo.cl")
        with self.conexion.transaccion() as cursor:
            self.repo_clientes.insertar(cursor, cliente)
        self.assertEqual(len(self.repo_clientes.cargar_todos()), 1)

        cliente.nombre = "Juan Actualizado"
        with self.conexion.transaccion() as cursor:
            self.repo_clientes.actualizar(cursor, cliente)
        cargado = self.repo_clientes.cargar_todos()[0]
        self.assertEqual(cargado.nombre, "Juan Actualizado")

        with self.conexion.transaccion() as cursor:
            self.repo_clientes.eliminar(cursor, cliente.rut)
        self.assertEqual(len(self.repo_clientes.cargar_todos()), 0)

    def test_prenda_de_cada_tipo_ida_y_vuelta(self):
        from models.prenda import PrendaEstandar, PrendaTermica, RopaInterior
        originales = [
            RopaInterior("INT-001", "Calzoncillo largo", "XXL", 8000, 2, "Ancho", "Ceñido"),
            PrendaEstandar("EST-001", "Polera básica", "S", 5000, 20, "Corta"),
            PrendaTermica("TER-001", "Beatle", "M", 12000, 10, "Tortuga", "Alto"),
        ]
        with self.conexion.transaccion() as cursor:
            for prenda in originales:
                self.repo_prendas.insertar(cursor, prenda)
        leidas = self.repo_prendas.cargar_todos()
        # Se ordenan por código para compararlas en el mismo orden en que vuelven de la base.
        originales.sort(key=lambda p: p.codigo)
        self.assertEqual([type(p) for p in leidas], [type(p) for p in originales])
        self.assertEqual([p.a_dict() for p in leidas], [p.a_dict() for p in originales])

    def test_empleado_conserva_hash_y_rol(self):
        from models.usuario import Administrador
        with self.conexion.transaccion() as cursor:
            self.repo_usuarios.insertar(cursor, Administrador("33.333.333-3", "Marisol Mena", "marisol", "admin123"))
        leido = self.repo_usuarios.cargar_todos()[0]
        self.assertTrue(leido.verificar_clave("admin123"))
        self.assertTrue(leido.puede_administrar())

    def test_tildes_y_enie_sobreviven(self):
        from models.usuario import Cliente
        with self.conexion.transaccion() as cursor:
            self.repo_clientes.insertar(cursor, Cliente("11.111.111-1", "Ñuñoa Pérez", "+56911223344", "nunoa@correo.cl"))
        self.assertEqual(self.repo_clientes.cargar_todos()[0].nombre, "Ñuñoa Pérez")

    def test_repositorio_es_abstracto(self):
        from models.repositorios import Repositorio
        with self.assertRaises(TypeError):
            Repositorio(self.conexion)


@unittest.skipUnless(MYSQL_DISPONIBLE, "MySQL no está disponible")
class TestBloqueoPersistente(unittest.TestCase):
    """HU16: el bloqueo por intentos fallidos se guarda en MySQL y sobrevive a un reinicio de la aplicación."""

    def setUp(self):
        from controllers.controlador_usuarios import ControladorUsuarios
        from models.almacen import Almacen
        self.ControladorUsuarios = ControladorUsuarios
        self.Almacen = Almacen
        self.conexion = conexion_limpia()
        # Primer "arranque": se crean los datos iniciales (usuario marisol / admin123).
        self.ctrl = ControladorUsuarios(Almacen(conexion=self.conexion), reloj=lambda: 1000.0)

    def reiniciar(self, ahora):
        """Simula cerrar y volver a abrir la aplicación: un almacén y un controlador nuevos sobre la misma base."""
        return self.ControladorUsuarios(self.Almacen(conexion=self.conexion), reloj=lambda: ahora)

    def fallar(self, ctrl, veces, usuario="marisol"):
        for _ in range(veces):
            with self.assertRaises(ValueError):
                ctrl.iniciar_sesion(usuario, "clave-mala")

    def test_el_bloqueo_sigue_vigente_despues_de_reiniciar(self):
        self.fallar(self.ctrl, 5)
        nuevo = self.reiniciar(1100.0)  # 100 segundos despues, con la clave correcta
        with self.assertRaises(ValueError) as contexto:
            nuevo.iniciar_sesion("marisol", "admin123")
        self.assertIn("bloqueada", str(contexto.exception))

    def test_se_desbloquea_a_los_10_minutos_aunque_se_haya_reiniciado(self):
        self.fallar(self.ctrl, 5)
        nuevo = self.reiniciar(1000.0 + 10 * 60 + 1)
        self.assertEqual(nuevo.iniciar_sesion("marisol", "admin123").usuario, "marisol")

    def test_un_inicio_correcto_reinicia_el_contador(self):
        self.fallar(self.ctrl, 4)
        self.ctrl.iniciar_sesion("marisol", "admin123")
        fila = self.conexion.consultar("SELECT fallidos FROM intentos_login WHERE usuario = 'marisol'")
        self.assertEqual(fila[0]["fallidos"], 0)

    def test_los_intentos_con_usuario_inexistente_tambien_se_registran(self):
        self.fallar(self.ctrl, 1, usuario="fantasma")
        fila = self.conexion.consultar("SELECT fallidos FROM intentos_login WHERE usuario = 'fantasma'")
        self.assertEqual(fila[0]["fallidos"], 1)


class TestRespaldoJson(unittest.TestCase):
    """HU14: con MySQL activo el JSON no se toca; solo se usa como respaldo si MySQL falla o no existe."""

    def setUp(self):
        import tempfile
        from models.gestor_datos import GestorDatos
        self.carpeta = Path(tempfile.mkdtemp())
        self.gestor = GestorDatos(self.carpeta)

    def test_sin_mysql_se_guarda_en_json(self):
        from models.almacen import Almacen
        almacen = Almacen(gestor=self.gestor)
        almacen.guardar("prendas")
        self.assertTrue((self.carpeta / "prendas.json").exists())

    def test_si_mysql_falla_se_guarda_en_json_de_emergencia(self):
        from models.almacen import Almacen
        conexion = ConexionBD({**config_pruebas(), "puerto": 1})  # servidor inalcanzable
        almacen = Almacen(gestor=self.gestor, conexion=conexion)
        (self.carpeta / "prendas.json").unlink(missing_ok=True)
        almacen.guardar("prendas")
        self.assertTrue((self.carpeta / "prendas.json").exists())

    @unittest.skipUnless(MYSQL_DISPONIBLE, "MySQL no está disponible")
    def test_con_mysql_no_se_escribe_el_json(self):
        from models.almacen import Almacen
        almacen = Almacen(gestor=self.gestor, conexion=conexion_limpia())
        for nombre in ("prendas", "clientes", "usuarios", "ventas"):
            almacen.guardar(nombre)
        self.assertEqual(list(self.carpeta.glob("*.json")), [])


if __name__ == "__main__":
    unittest.main()
