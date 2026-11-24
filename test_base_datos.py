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


if __name__ == "__main__":
    unittest.main()
