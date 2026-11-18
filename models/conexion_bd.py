"""
Conexión con la base de datos MySQL (o MariaDB, en XAMPP).

Es el ÚNICO archivo del proyecto que usa la librería mysql.connector. El resto del programa
trabaja con esta clase, así que si algún día se cambia de motor, solo se modifica este archivo.
"""

# configparser lee archivos .ini (secciones con 'clave = valor').
import configparser
# contextmanager permite crear bloques 'with' propios, como el de las transacciones.
from contextlib import contextmanager
from pathlib import Path

# El conector oficial de MySQL para Python (se instala con: pip install -r requirements.txt).
import mysql.connector

from .excepciones import ErrorBaseDatos

# Archivo con las sentencias CREATE TABLE. Está en la carpeta bd/, junto a la raíz del proyecto.
ARCHIVO_ESQUEMA = Path(__file__).parent.parent / "bd" / "esquema.sql"
# Mensaje que ve la persona si el servidor no responde.
MENSAJE_SIN_CONEXION = "No se pudo conectar a MySQL. Revisa que XAMPP/MySQL esté encendido."


# ENCAPSULAMIENTO: la conexión real (_conexion) es interna. Desde afuera solo se usan
# preparar(), transaccion() y consultar().
class ConexionBD:
    """Abre la conexión con MySQL, crea la base y las tablas, y ejecuta transacciones."""

    # Recibe un diccionario con host, puerto, usuario, clave y base_datos.
    def __init__(self, config: dict):
        # dict(config) hace una copia, para que un cambio afuera no afecte a esta conexión.
        self._config = dict(config)
        # Todavía no hay conexión: se abre en preparar().
        self._conexion = None

    # @staticmethod: se llama sin crear un objeto, como ConexionBD.leer_configuracion(carpeta).
    # Lee config_bd.ini y, si existe, config_bd.local.ini, cuyos valores reemplazan a los primeros.
    @staticmethod
    def leer_configuracion(carpeta: Path) -> dict:
        lector = configparser.ConfigParser()
        # read() ignora los archivos que no existen, por eso el .local es opcional.
        lector.read([Path(carpeta) / "config_bd.ini", Path(carpeta) / "config_bd.local.ini"], encoding="utf-8")
        seccion = lector["mysql"]
        return {
            "host": seccion.get("host", "localhost"),
            # getint convierte el texto "3306" en el número 3306.
            "puerto": seccion.getint("puerto", 3306),
            "usuario": seccion.get("usuario", "root"),
            "clave": seccion.get("clave", ""),
            "base_datos": seccion.get("base_datos", "lacasetita"),
        }

    # Nombre de la base de datos que usa esta conexión (de solo lectura).
    @property
    def base_datos(self) -> str:
        return self._config["base_datos"]

    # Abre una conexión nueva. Si se indica una base, queda seleccionada.
    def _conectar(self, con_base: bool):
        parametros = {
            "host": self._config["host"],
            "port": self._config["puerto"],
            "user": self._config["usuario"],
            "password": self._config["clave"],
            # utf8mb4 permite tildes y ñ. La colación se indica a mano porque la que MySQL usa por defecto
            # no existe en MariaDB (XAMPP), y la conexión fallaría en los computadores con Windows.
            "charset": "utf8mb4",
            "collation": "utf8mb4_unicode_ci",
            # Si el servidor no responde en 5 segundos, se rinde en vez de quedarse esperando.
            "connection_timeout": 5,
        }
        if con_base:
            parametros["database"] = self.base_datos
        # ** reparte el diccionario como argumentos con nombre: host=..., port=..., etc.
        return mysql.connector.connect(**parametros)

    # Prepara todo lo necesario: crea la base si no existe, crea las tablas que falten y deja la conexión abierta.
    def preparar(self) -> None:
        try:
            # 1. Conexión sin base, solo para crearla si todavía no existe.
            servidor = self._conectar(con_base=False)
            cursor = servidor.cursor()
            # El nombre de una base no se puede pasar como parámetro %s; va entre comillas invertidas (`).
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{self.base_datos}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cursor.close()
            servidor.close()
            # 2. Conexión definitiva, ya con la base seleccionada. Se reutiliza durante todo el programa.
            if self._conexion is not None:
                self._conexion.close()
            self._conexion = self._conectar(con_base=True)
        except mysql.connector.Error as error:
            # 'from error' conserva el error original por si hay que revisarlo.
            raise ErrorBaseDatos(MENSAJE_SIN_CONEXION) from error

        # 3. Se crean las tablas leyendo el archivo bd/esquema.sql.
        with self.transaccion() as cursor:
            for sentencia in self._sentencias_del_esquema():
                cursor.execute(sentencia)

    # Lee esquema.sql y lo separa en sentencias. Primero quita los comentarios (líneas que empiezan con --),
    # porque pueden tener un ';' que confundiría la separación.
    def _sentencias_del_esquema(self) -> list[str]:
        lineas = ARCHIVO_ESQUEMA.read_text(encoding="utf-8").splitlines()
        sin_comentarios = "\n".join(linea for linea in lineas if not linea.strip().startswith("--"))
        # split(";") corta el texto en cada punto y coma; se descartan los trozos vacíos.
        return [sentencia.strip() for sentencia in sin_comentarios.split(";") if sentencia.strip()]

    # TRANSACCIÓN: un grupo de cambios que se guarda completo o no se guarda nada.
    # Se usa así:   with conexion.transaccion() as cursor:
    #                   cursor.execute("INSERT ...", (valor1, valor2))
    # Si el bloque termina bien, se confirma (commit). Si ocurre cualquier error, se deshace (rollback).
    @contextmanager
    def transaccion(self):
        if self._conexion is None:
            raise ErrorBaseDatos("La base de datos no está preparada. Llama primero a preparar().")
        try:
            # ping revisa que la conexión siga viva y, si se cortó, intenta reconectar.
            self._conexion.ping(reconnect=True)
            # dictionary=True: cada fila leída llega como diccionario {"columna": valor}.
            cursor = self._conexion.cursor(dictionary=True)
        except mysql.connector.Error as error:
            raise ErrorBaseDatos(MENSAJE_SIN_CONEXION) from error
        try:
            # 'yield' entrega el cursor al bloque 'with'. Aquí se ejecuta lo que esté dentro del bloque.
            yield cursor
            # Si el bloque terminó sin errores, se guardan los cambios.
            self._conexion.commit()
        except mysql.connector.Error as error:
            self._deshacer()
            raise ErrorBaseDatos(f"La base de datos rechazó la operación: {error.msg}") from error
        except Exception:
            # Cualquier otro error (por ejemplo, una regla del negocio) también deshace los cambios.
            self._deshacer()
            # 'raise' solo, sin nada más, vuelve a lanzar el mismo error para que lo vea quien llamó.
            raise
        finally:
            # 'finally' se ejecuta siempre, haya error o no: el cursor se cierra.
            cursor.close()

    # Deshace los cambios pendientes. Si la conexión ya se cortó, no hay nada que deshacer.
    def _deshacer(self) -> None:
        try:
            self._conexion.rollback()
        except mysql.connector.Error:
            pass

    # Ejecuta una consulta SELECT y entrega las filas como una lista de diccionarios.
    def consultar(self, sql: str, parametros: tuple = ()) -> list[dict]:
        with self.transaccion() as cursor:
            # %s en el SQL se reemplaza por los parámetros de forma segura (evita la inyección SQL).
            cursor.execute(sql, parametros)
            return cursor.fetchall()
