"""
Script de migración: importa los datos desde los archivos JSON hacia MySQL Workbench.
Para ejecutar: py -m bd.migrar_json_a_mysql
"""

from pathlib import Path
from models.conexion_bd import ConexionBD
from models.gestor_datos import GestorDatos
from models.prenda import prenda_desde_dict
from models.repositorios import (
    RepositorioClientes,
    RepositorioPrendas,
    RepositorioUsuarios,
    RepositorioVentas,
)
from models.usuario import Cliente, Empleado
from models.venta import Venta


def migrar():
    raiz = Path(__file__).resolve().parent.parent
    gestor = GestorDatos(raiz / "datos")
    config = ConexionBD.leer_configuracion(raiz)
    conexion = ConexionBD(config)

    print("=" * 60)
    print("MIGRACIÓN DE DATOS JSON A MYSQL WORKBENCH")
    print(f"Base de datos destino: {config['base_datos']}")
    print("=" * 60)

    try:
        conexion.preparar()
        print("✓ Conexión y tablas verificadas con éxito.")
    except Exception as error:
        print(f"✗ Error al conectar con MySQL: {error}")
        print("Revisa que MySQL esté encendido y que las credenciales en config_bd.ini sean correctas.")
        return

    repo_prendas = RepositorioPrendas(conexion)
    repo_clientes = RepositorioClientes(conexion)
    repo_usuarios = RepositorioUsuarios(conexion)
    repo_ventas = RepositorioVentas(conexion)

    with conexion.transaccion() as cursor:
        # 1. Prendas
        prendas = [prenda_desde_dict(d) for d in gestor.cargar("prendas")]
        for p in prendas:
            # Si no existe, la inserta
            filas = conexion.consultar("SELECT codigo FROM prendas WHERE codigo = %s", (p.codigo,))
            if not filas:
                repo_prendas.insertar(cursor, p)
        print(f"✓ Prendas sincronizadas: {len(prendas)}")

        # 2. Clientes
        clientes = [Cliente.desde_dict(d) for d in gestor.cargar("clientes")]
        for c in clientes:
            filas = conexion.consultar("SELECT rut FROM clientes WHERE rut = %s", (c.rut,))
            if not filas:
                repo_clientes.insertar(cursor, c)
        print(f"✓ Clientes sincronizados: {len(clientes)}")

        # 3. Usuarios
        usuarios = [Empleado.desde_dict(d) for d in gestor.cargar("usuarios")]
        for u in usuarios:
            filas = conexion.consultar("SELECT usuario FROM usuarios WHERE usuario = %s", (u.usuario,))
            if not filas:
                repo_usuarios.insertar(cursor, u)
        print(f"✓ Usuarios sincronizados: {len(usuarios)}")

        # 4. Ventas
        if gestor.existe("ventas"):
            ventas = [Venta.desde_dict(d) for d in gestor.cargar("ventas")]
            for v in ventas:
                filas = conexion.consultar("SELECT folio FROM ventas WHERE folio = %s", (v.folio,))
                if not filas:
                    repo_ventas.insertar(cursor, v)
            print(f"✓ Ventas sincronizadas: {len(ventas)}")

    print("=" * 60)
    print("¡MIGRACIÓN COMPLETADA EXITOSAMENTE!")
    print("Ahora puedes abrir MySQL Workbench y consultar tus tablas.")
    print("=" * 60)


if __name__ == "__main__":
    migrar()
