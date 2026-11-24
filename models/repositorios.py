"""
Repositorios del sistema: una clase por tabla que encapsula las consultas SQL.

Conceptos de Programación Orientada a Objetos (POO):
- Abstracción: Repositorio es una clase abstracta (ABC) con el método común cargar_todos().
- Herencia: cada repositorio concreto hereda de Repositorio (RepositorioPrendas, RepositorioClientes, etc.).
- Polimorfismo: cada repositorio implementa cargar_todos() a su manera, retornando los objetos de su clase.
- Encapsulamiento: el código SQL de cada tabla vive únicamente dentro de su repositorio correspondiente.
"""

from abc import ABC, abstractmethod
from datetime import datetime

from .conexion_bd import ConexionBD
from .prenda import Prenda, prenda_desde_dict
from .usuario import Cliente, Empleado
from .venta import DetalleVenta, Venta


# Clase base abstracta para todos los repositorios.
class Repositorio(ABC):
    """Clase base de acceso a datos para una tabla de la base de datos."""

    # Nombre de la tabla en MySQL; cada subclase define el suyo propio.
    TABLA: str = ""

    def __init__(self, conexion: ConexionBD):
        self._conexion = conexion

    @property
    def conexion(self) -> ConexionBD:
        return self._conexion

    # Método polimórfico: cada repositorio concreto lo implementa para cargar sus objetos.
    @abstractmethod
    def cargar_todos(self) -> list:
        """Carga y retorna todos los registros de la tabla convertidos en objetos."""

    # Revisa si la tabla no tiene ninguna fila.
    def esta_vacio(self) -> bool:
        """Retorna True si la tabla no contiene ningún registro."""
        filas = self._conexion.consultar(f"SELECT 1 FROM {self.TABLA} LIMIT 1")
        return len(filas) == 0

    # Cuenta cuántas filas existen en la tabla.
    def contar(self) -> int:
        """Retorna la cantidad total de registros en la tabla."""
        filas = self._conexion.consultar(f"SELECT COUNT(*) AS total FROM {self.TABLA}")
        return filas[0]["total"] if filas else 0


# Repositorio para la tabla 'prendas'. Maneja las 3 subclases de prenda en una sola tabla.
class RepositorioPrendas(Repositorio):
    """Operaciones de base de datos para el catálogo de prendas."""

    TABLA = "prendas"

    def cargar_todos(self) -> list[Prenda]:
        """Carga todas las prendas ordenadas por código."""
        filas = self._conexion.consultar(f"SELECT * FROM {self.TABLA} ORDER BY codigo")
        return [prenda_desde_dict(fila) for fila in filas]

    def insertar(self, cursor, prenda: Prenda) -> None:
        """Inserta una nueva prenda en la base de datos."""
        datos = prenda.a_dict()
        sql = (
            f"INSERT INTO {self.TABLA} "
            "(codigo, tipo, nombre, talla, precio_base, stock, "
            "tipo_cuello, nivel_termico, tipo_manga, tipo_elastico, ajuste) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        valores = (
            prenda.codigo,
            prenda.obtener_tipo(),
            prenda.nombre,
            prenda.talla,
            prenda.precio_base,
            prenda.stock,
            datos.get("tipo_cuello"),
            datos.get("nivel_termico"),
            datos.get("tipo_manga"),
            datos.get("tipo_elastico"),
            datos.get("ajuste"),
        )
        cursor.execute(sql, valores)

    def actualizar_stock(self, cursor, codigo: str, stock: int) -> None:
        """Actualiza el stock disponible de una prenda."""
        sql = f"UPDATE {self.TABLA} SET stock = %s WHERE codigo = %s"
        cursor.execute(sql, (stock, codigo))

    def actualizar_precio(self, cursor, codigo: str, precio_base: int) -> None:
        """Actualiza el precio base de una prenda."""
        sql = f"UPDATE {self.TABLA} SET precio_base = %s WHERE codigo = %s"
        cursor.execute(sql, (precio_base, codigo))

    def eliminar(self, cursor, codigo: str) -> None:
        """Elimina una prenda de la base de datos por su código."""
        sql = f"DELETE FROM {self.TABLA} WHERE codigo = %s"
        cursor.execute(sql, (codigo,))


# Repositorio para la tabla 'clientes'.
class RepositorioClientes(Repositorio):
    """Operaciones de base de datos para los clientes de la tienda."""

    TABLA = "clientes"

    def cargar_todos(self) -> list[Cliente]:
        """Carga todos los clientes ordenados por RUT."""
        filas = self._conexion.consultar(f"SELECT * FROM {self.TABLA} ORDER BY rut")
        return [Cliente.desde_dict(fila) for fila in filas]

    def insertar(self, cursor, cliente: Cliente) -> None:
        """Inserta un nuevo cliente en la base de datos."""
        sql = f"INSERT INTO {self.TABLA} (rut, nombre, telefono, correo) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (cliente.rut, cliente.nombre, cliente.telefono, cliente.correo))

    def actualizar(self, cursor, cliente: Cliente) -> None:
        """Actualiza los datos de contacto y nombre de un cliente."""
        sql = f"UPDATE {self.TABLA} SET nombre = %s, telefono = %s, correo = %s WHERE rut = %s"
        cursor.execute(sql, (cliente.nombre, cliente.telefono, cliente.correo, cliente.rut))

    def eliminar(self, cursor, rut: str) -> None:
        """Elimina un cliente de la base de datos por su RUT."""
        sql = f"DELETE FROM {self.TABLA} WHERE rut = %s"
        cursor.execute(sql, (rut,))


# Repositorio para la tabla 'usuarios' (empleados: Administrador y Vendedor).
class RepositorioUsuarios(Repositorio):
    """Operaciones de base de datos para los usuarios del sistema."""

    TABLA = "usuarios"

    def cargar_todos(self) -> list[Empleado]:
        """Carga todos los usuarios ordenados por RUT."""
        filas = self._conexion.consultar(f"SELECT * FROM {self.TABLA} ORDER BY rut")
        return [Empleado.desde_dict(fila) for fila in filas]

    def insertar(self, cursor, empleado: Empleado) -> None:
        """Inserta un nuevo empleado con su contraseña ya encriptada."""
        datos = empleado.a_dict()
        sql = (
            f"INSERT INTO {self.TABLA} (rut, usuario, nombre, rol, clave_hash) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        cursor.execute(sql, (datos["rut"], datos["usuario"], datos["nombre"], datos["rol"], datos["clave_hash"]))

    def actualizar_clave(self, cursor, empleado: Empleado) -> None:
        """Actualiza el hash de la contraseña de un empleado."""
        datos = empleado.a_dict()
        sql = f"UPDATE {self.TABLA} SET clave_hash = %s WHERE usuario = %s"
        cursor.execute(sql, (datos["clave_hash"], datos["usuario"]))

    def eliminar(self, cursor, usuario: str) -> None:
        """Elimina un empleado por su nombre de usuario."""
        sql = f"DELETE FROM {self.TABLA} WHERE usuario = %s"
        cursor.execute(sql, (usuario,))


# Repositorio para 'ventas' y 'detalle_venta'.
class RepositorioVentas(Repositorio):
    """Operaciones de base de datos para las ventas y sus líneas de detalle."""

    TABLA = "ventas"
    TABLA_DETALLE = "detalle_venta"

    def cargar_todos(self) -> list[Venta]:
        """Carga todas las ventas con sus líneas de detalle reconstruidas."""
        filas_ventas = self._conexion.consultar(f"SELECT * FROM {self.TABLA} ORDER BY folio")
        filas_detalles = self._conexion.consultar(f"SELECT * FROM {self.TABLA_DETALLE} ORDER BY id")

        # Agrupa los detalles por folio de venta: {folio: [DetalleVenta, ...]}
        detalles_por_folio: dict[int, list] = {}
        for d in filas_detalles:
            folio = d["folio"]
            detalles_por_folio.setdefault(folio, []).append({
                "codigo": d["codigo"],
                "descripcion": d["descripcion"],
                "cantidad": d["cantidad"],
                "subtotal": d["subtotal"],
            })

        ventas = []
        for f in filas_ventas:
            datos_venta = dict(f)
            # MySQL entrega 'fecha' como objeto datetime; Venta.desde_dict espera texto ISO
            if isinstance(datos_venta["fecha"], datetime):
                datos_venta["fecha"] = datos_venta["fecha"].isoformat(timespec="seconds")
            datos_venta["detalles"] = detalles_por_folio.get(f["folio"], [])
            ventas.append(Venta.desde_dict(datos_venta))

        return ventas

    def insertar(self, cursor, venta: Venta) -> None:
        """
        Inserta la cabecera de la venta y cada una de sus líneas de detalle
        dentro de la misma transacción.
        """
        sql_venta = (
            f"INSERT INTO {self.TABLA} "
            "(folio, fecha, vendedor, cliente_rut, cliente_nombre, "
            "descuento_cliente, estado, medio_pago, comprobante) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        valores_venta = (
            venta.folio,
            venta.fecha.strftime("%Y-%m-%d %H:%M:%S"),
            venta.vendedor,
            venta.cliente_rut,
            venta.cliente_nombre,
            venta.descuento_cliente,
            venta.estado,
            venta.medio_pago,
            venta.comprobante or None,
        )
        cursor.execute(sql_venta, valores_venta)

        sql_detalle = (
            f"INSERT INTO {self.TABLA_DETALLE} "
            "(folio, codigo, descripcion, cantidad, subtotal) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        for detalle in venta.detalles:
            cursor.execute(
                sql_detalle,
                (venta.folio, detalle.codigo, detalle.descripcion, detalle.cantidad, detalle.subtotal),
            )

    def actualizar_estado(self, cursor, folio: int, estado: str) -> None:
        """Actualiza el estado de una venta (PAGADA, ENTREGADA, CANCELADA)."""
        sql = f"UPDATE {self.TABLA} SET estado = %s WHERE folio = %s"
        cursor.execute(sql, (estado, folio))


# Repositorio para la tabla 'intentos_login' (bloqueo persistente contra ataques de fuerza bruta).
class RepositorioIntentos(Repositorio):
    """Guarda y consulta los intentos fallidos de inicio de sesión por usuario."""

    TABLA = "intentos_login"

    def cargar_todos(self) -> list[dict]:
        """Retorna todos los registros de intentos de login."""
        return self._conexion.consultar(f"SELECT * FROM {self.TABLA} ORDER BY usuario")

    def obtener(self, usuario: str) -> dict:
        """Retorna el estado de intentos de un usuario o un registro limpio si no existe."""
        nombre = usuario.strip().lower()
        filas = self._conexion.consultar(
            f"SELECT fallidos, bloqueado_hasta FROM {self.TABLA} WHERE usuario = %s",
            (nombre,),
        )
        if filas:
            return {"fallidos": filas[0]["fallidos"], "bloqueado_hasta": filas[0]["bloqueado_hasta"]}
        return {"fallidos": 0, "bloqueado_hasta": 0.0}

    def guardar(self, cursor, usuario: str, fallidos: int, bloqueado_hasta: float) -> None:
        """Inserta o actualiza el contador de intentos y bloqueo para un usuario."""
        nombre = usuario.strip().lower()
        sql = (
            f"INSERT INTO {self.TABLA} (usuario, fallidos, bloqueado_hasta) "
            "VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE fallidos = %s, bloqueado_hasta = %s"
        )
        cursor.execute(sql, (nombre, fallidos, bloqueado_hasta, fallidos, bloqueado_hasta))
