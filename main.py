"""
La Caserita de las Camisetas: sistema de ventas e inventario.
Para ejecutar: py main.py

Estructura Modelo-Vista-Controlador (MVC):
  models/       datos, lógica de negocio y persistencia en MySQL (vía repositorios) y JSON
  controllers/  reglas del negocio: reciben peticiones de las vistas y modifican el modelo
  views/        pantallas Tkinter: muestran datos e interactúan con el usuario
"""

from pathlib import Path

from controllers import Controladores
from models.almacen import Almacen
from models.conexion_bd import ConexionBD
from models.excepciones import ErrorBaseDatos
from models.gestor_datos import GestorDatos
from views.app import Aplicacion


def main():
    """Función principal: conecta las capas de la aplicación y lanza la interfaz."""
    raiz = Path(__file__).parent
    carpeta_datos = raiz / "datos"
    gestor_json = GestorDatos(carpeta_datos)

    # 1. Intentar conexión a la base de datos MySQL (administrable desde MySQL Workbench)
    conexion_mysql = None
    aviso_conexion = None

    try:
        config = ConexionBD.leer_configuracion(raiz)
        conexion_mysql = ConexionBD(config)
        # Prepara la base de datos y crea las tablas si no existen
        conexion_mysql.preparar()
    except (ErrorBaseDatos, Exception) as error:
        conexion_mysql = None
        aviso_conexion = (
            "No se pudo conectar a MySQL Workbench. Se utilizará el almacenamiento local.\n\n"
            "Para conectar con Workbench, revisa que el servicio MySQL esté iniciado y "
            "configura tu contraseña en 'config_bd.local.ini' o 'config_bd.ini'."
        )

    # 2. Inicializar el Almacén con MySQL (y respaldo en JSON)
    almacen = Almacen(gestor=gestor_json, conexion=conexion_mysql)
    if aviso_conexion:
        almacen.avisos.append(aviso_conexion)

    # 3. Iniciar la aplicación gráfica
    Aplicacion(Controladores(almacen)).mainloop()


if __name__ == "__main__":
    main()
