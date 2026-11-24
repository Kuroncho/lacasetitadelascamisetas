"""
Almacén de datos del sistema.

Reúne las colecciones del negocio (prendas, clientes, usuarios y ventas).
Soporta persistencia directa en base de datos relacional MySQL / MariaDB (vía repositorios)
y respaldo en archivos JSON para entornos de prueba.
"""

from pathlib import Path
from .conexion_bd import ConexionBD
from .excepciones import ErrorBaseDatos
from .gestor_datos import GestorDatos
from .prenda import Prenda, PrendaEstandar, PrendaTermica, RopaInterior, prenda_desde_dict
from .repositorios import (
    RepositorioClientes,
    RepositorioIntentos,
    RepositorioPrendas,
    RepositorioUsuarios,
    RepositorioVentas,
)
from .usuario import Administrador, Cliente, Empleado, Vendedor
from .venta import Venta


def _datos_iniciales() -> dict:
    """Datos de ejemplo iniciales que se crean la primera vez que se abre el sistema."""
    return {
        "prendas": [
            PrendaTermica("TER-001", "Beatle", "M", 12000, 10, "Tortuga", "Alto"),
            PrendaTermica("TER-002", "Camiseta de invierno", "L", 10000, 8, "Redondo", "Medio"),
            PrendaEstandar("EST-001", "Polera básica", "S", 5000, 20, "Corta"),
            PrendaEstandar("EST-002", "Polera básica", "L", 6000, 15, "Larga"),
            RopaInterior("INT-001", "Calzoncillo largo", "M", 8000, 12, "Ancho", "Regular"),
            RopaInterior("INT-002", "Calzoncillo largo", "XXL", 8000, 2, "Ancho", "Ceñido"),
        ],
        "clientes": [
            Cliente("11.111.111-1", "Juan Perez", "+56911223344", "juan@correo.cl"),
            Cliente("22.222.222-2", "Maria Gonzalez", "+56988776655", "maria@correo.cl"),
        ],
        "usuarios": [
            Administrador("33.333.333-3", "Marisol Mena", "marisol", "admin123"),
            Vendedor("44.444.444-4", "Carlos Baeza", "carlos", "vende123"),
        ],
    }


class Almacen:
    """
    Coordina la persistencia y consulta de las colecciones del negocio.
    Usa repositorios para comunicarse con MySQL y puede usar GestorDatos como respaldo.
    """

    def __init__(self, gestor: GestorDatos | None = None, conexion: ConexionBD | None = None):
        self._gestor = gestor
        self._conexion = conexion
        self.avisos: list[str] = []

        # Repositorios para cada tabla de MySQL
        self.repo_prendas: RepositorioPrendas | None = None
        self.repo_clientes: RepositorioClientes | None = None
        self.repo_usuarios: RepositorioUsuarios | None = None
        self.repo_ventas: RepositorioVentas | None = None
        self.repo_intentos: RepositorioIntentos | None = None

        if self._conexion is not None:
            self._configurar_repositorios()
            self._cargar_desde_bd()
        elif self._gestor is not None:
            self._cargar_desde_json()
        else:
            iniciales = _datos_iniciales()
            self.prendas = list(iniciales["prendas"])
            self.clientes = list(iniciales["clientes"])
            self.usuarios = list(iniciales["usuarios"])
            self.ventas = []

    def _configurar_repositorios(self) -> None:
        """Inicializa los repositorios orientados a objetos con la conexión MySQL."""
        self.repo_prendas = RepositorioPrendas(self._conexion)
        self.repo_clientes = RepositorioClientes(self._conexion)
        self.repo_usuarios = RepositorioUsuarios(self._conexion)
        self.repo_ventas = RepositorioVentas(self._conexion)
        self.repo_intentos = RepositorioIntentos(self._conexion)

    def _cargar_desde_bd(self) -> None:
        """Carga las colecciones desde MySQL o puebla los datos iniciales si está vacía."""
        try:
            self._conexion.preparar()

            # Si las tablas principales están vacías, se insertan los datos de prueba iniciales
            if (
                self.repo_prendas.esta_vacio()
                and self.repo_clientes.esta_vacio()
                and self.repo_usuarios.esta_vacio()
            ):
                iniciales = _datos_iniciales()
                with self._conexion.transaccion() as cursor:
                    for prenda in iniciales["prendas"]:
                        self.repo_prendas.insertar(cursor, prenda)
                    for cliente in iniciales["clientes"]:
                        self.repo_clientes.insertar(cursor, cliente)
                    for usuario in iniciales["usuarios"]:
                        self.repo_usuarios.insertar(cursor, usuario)

            self.prendas = self.repo_prendas.cargar_todos()
            self.clientes = self.repo_clientes.cargar_todos()
            self.usuarios = self.repo_usuarios.cargar_todos()
            self.ventas = self.repo_ventas.cargar_todos()

            # Asegurar regla de negocio: siempre debe existir al menos un administrador
            if not any(u.puede_administrar() for u in self.usuarios):
                admin_defecto = Administrador("33.333.333-3", "Marisol Mena", "marisol", "admin123")
                with self._conexion.transaccion() as cursor:
                    self.repo_usuarios.insertar(cursor, admin_defecto)
                self.usuarios.append(admin_defecto)

        except ErrorBaseDatos as error:
            self.avisos.append(str(error))
            # Si falla la base de datos y hay un gestor JSON, se recuperan los datos locales
            if self._gestor is not None:
                self._cargar_desde_json()
            else:
                iniciales = _datos_iniciales()
                self.prendas = list(iniciales["prendas"])
                self.clientes = list(iniciales["clientes"])
                self.usuarios = list(iniciales["usuarios"])
                self.ventas = []

    def _cargar_desde_json(self) -> None:
        """Carga tradicional desde archivos JSON para compatibilidad y pruebas unitarias."""
        iniciales = _datos_iniciales()
        self.prendas = self._cargar_coleccion_json("prendas", prenda_desde_dict, iniciales["prendas"])
        self.clientes = self._cargar_coleccion_json("clientes", Cliente.desde_dict, iniciales["clientes"])
        self.usuarios = self._cargar_coleccion_json("usuarios", Empleado.desde_dict, iniciales["usuarios"])
        self.ventas = self._cargar_coleccion_json("ventas", Venta.desde_dict, [])

    def _cargar_coleccion_json(self, nombre: str, fabricador, datos_defecto: list) -> list:
        """Lee un archivo JSON individual protegiendo contra archivos dañados."""
        if self._gestor.existe(nombre):
            try:
                objetos = [fabricador(d) for d in self._gestor.cargar(nombre)]
                if nombre != "usuarios" or any(u.puede_administrar() for u in objetos):
                    return objetos
            except (ValueError, KeyError, TypeError, AttributeError):
                self._gestor.apartar_corrupto(nombre)
                self.avisos.append(f"El archivo {nombre}.json estaba dañado. Se creó uno nuevo.")

        self._gestor.guardar(nombre, [obj.a_dict() for obj in datos_defecto])
        return datos_defecto

    def guardar(self, nombre: str) -> None:
        """
        Persiste los cambios de la colección indicada en MySQL y/o JSON.
        nombre puede ser: 'prendas', 'clientes', 'usuarios' o 'ventas'.
        """
        # Si hay conexión a MySQL activa, sincroniza con la base de datos
        if self._conexion is not None:
            self._guardar_en_bd(nombre)

        # Si hay gestor de datos JSON disponible, mantiene el respaldo local actualizado
        if self._gestor is not None:
            coleccion = getattr(self, nombre, [])
            self._gestor.guardar(nombre, [obj.a_dict() for obj in coleccion])

    def _guardar_en_bd(self, nombre: str) -> None:
        """Aplica las consultas SQL de actualización en MySQL según la colección modificada."""
        try:
            with self._conexion.transaccion() as cursor:
                if nombre == "prendas":
                    # Obtener códigos actuales en base de datos para saber cuáles agregar o actualizar
                    codigos_bd = {
                        fila["codigo"]
                        for fila in self._conexion.consultar("SELECT codigo FROM prendas")
                    }
                    codigos_memoria = {p.codigo for p in self.prendas}

                    # Eliminar las prendas que se hayan borrado
                    for codigo_eliminar in codigos_bd - codigos_memoria:
                        self.repo_prendas.eliminar(cursor, codigo_eliminar)

                    # Insertar o actualizar stock y precios de las prendas en memoria
                    for prenda in self.prendas:
                        if prenda.codigo in codigos_bd:
                            self.repo_prendas.actualizar_stock(cursor, prenda.codigo, prenda.stock)
                            self.repo_prendas.actualizar_precio(cursor, prenda.codigo, prenda.precio_base)
                        else:
                            self.repo_prendas.insertar(cursor, prenda)

                elif nombre == "clientes":
                    ruts_bd = {
                        fila["rut"]
                        for fila in self._conexion.consultar("SELECT rut FROM clientes")
                    }
                    ruts_memoria = {c.rut for c in self.clientes}

                    for rut_eliminar in ruts_bd - ruts_memoria:
                        self.repo_clientes.eliminar(cursor, rut_eliminar)

                    for cliente in self.clientes:
                        if cliente.rut in ruts_bd:
                            self.repo_clientes.actualizar(cursor, cliente)
                        else:
                            self.repo_clientes.insertar(cursor, cliente)

                elif nombre == "usuarios":
                    usuarios_bd = {
                        fila["usuario"]
                        for fila in self._conexion.consultar("SELECT usuario FROM usuarios")
                    }
                    usuarios_memoria = {u.usuario for u in self.usuarios}

                    for usuario_eliminar in usuarios_bd - usuarios_memoria:
                        self.repo_usuarios.eliminar(cursor, usuario_eliminar)

                    for usuario in self.usuarios:
                        if usuario.usuario in usuarios_bd:
                            self.repo_usuarios.actualizar_clave(cursor, usuario)
                        else:
                            self.repo_usuarios.insertar(cursor, usuario)

                elif nombre == "ventas":
                    folios_bd = {
                        fila["folio"]
                        for fila in self._conexion.consultar("SELECT folio FROM ventas")
                    }
                    for venta in self.ventas:
                        if venta.folio in folios_bd:
                            self.repo_ventas.actualizar_estado(cursor, venta.folio, venta.estado)
                        else:
                            self.repo_ventas.insertar(cursor, venta)

        except ErrorBaseDatos as error:
            # Si MySQL falla, se anota el aviso para que la interfaz gráfica pueda alertar al usuario
            self.avisos.append(str(error))

    # --- Búsquedas en memoria ---
    def buscar_prenda(self, codigo: str) -> Prenda | None:
        return next((p for p in self.prendas if p.codigo == codigo), None)

    def buscar_cliente(self, rut: str) -> Cliente | None:
        return next((c for c in self.clientes if c.rut == rut), None)

    def buscar_usuario(self, usuario: str) -> Empleado | None:
        return next((u for u in self.usuarios if u.usuario == usuario), None)

    def buscar_venta(self, folio: int) -> Venta | None:
        return next((v for v in self.ventas if v.folio == folio), None)

    def ventas_de(self, rut: str) -> list[Venta]:
        return [venta for venta in self.ventas if venta.cliente_rut == rut]
