"""
Pruebas automáticas de las reglas del negocio y de los casos borde.
Para ejecutar: py -m unittest -v
"""

import json
import tempfile
import unittest
from pathlib import Path

from controllers import Controladores
from models.almacen import Almacen
from models.excepciones import PagoRechazadoException, SinStockException
from models.gestor_datos import GestorDatos
from models.pago import Efectivo, TarjetaDebito, Transferencia
from models.prenda import Prenda, PrendaEstandar, PrendaTermica, RopaInterior
from models.usuario import Cliente, Usuario, Vendedor
from models.validaciones import formato_clp, texto_a_entero, validar_rut
from models.venta import EstadoVenta, Venta
from views.texto_boleta import generar_boleta


class BaseTienda(unittest.TestCase):
    """Cada prueba parte con datos nuevos en una carpeta temporal."""

    def setUp(self):
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.carpeta = Path(carpeta.name)
        self.almacen = Almacen(GestorDatos(self.carpeta))
        self.ctrl = Controladores(self.almacen)
        self.cliente = self.almacen.clientes[0]

    def nueva_venta(self, codigo="EST-001", cantidad=1):
        venta = self.ctrl.ventas.nueva_venta(self.almacen.buscar_usuario("carlos"))
        self.ctrl.ventas.asignar_cliente(venta, self.cliente.rut)
        self.ctrl.ventas.agregar_prenda(venta, codigo, str(cantidad))
        return venta

    def reabrir(self):
        """Simula cerrar y abrir la aplicación: retorna el almacén y los controladores nuevos."""
        almacen = Almacen(GestorDatos(self.carpeta))
        return almacen, Controladores(almacen)


class TestValidaciones(unittest.TestCase):
    def test_rut_valido_se_normaliza(self):
        self.assertEqual(validar_rut("11.111.111-1"), "11111111-1")

    def test_rut_invalido_se_rechaza(self):
        for rut in ["abc", "", "11.111.111-2", "123"]:
            with self.assertRaises(ValueError):
                validar_rut(rut)

    def test_nombre_invalido_se_rechaza(self):
        for nombre in ["", "A", "123", "Juan2"]:
            with self.assertRaises(ValueError):
                Cliente("11.111.111-1", nombre, "+56911223344", "a@b.cl")

    def test_telefono_y_correo_invalidos(self):
        with self.assertRaises(ValueError):
            Cliente("11.111.111-1", "Juan", "123", "a@b.cl")
        with self.assertRaises(ValueError):
            Cliente("11.111.111-1", "Juan", "+56911223344", "sin-arroba")

    def test_texto_a_entero(self):
        self.assertEqual(texto_a_entero("50.000", "Monto"), 50000)
        self.assertEqual(texto_a_entero(" 7 ", "Monto"), 7)
        for texto in ["abc", "", "1.5", "50,000", "9" * 50]:
            with self.assertRaises(ValueError):
                texto_a_entero(texto, "Monto")

    def test_formato_clp(self):
        self.assertEqual(formato_clp(1234567), "$1.234.567")


class TestPOO(unittest.TestCase):
    def test_clases_abstractas_no_se_instancian(self):
        with self.assertRaises(TypeError):
            Usuario("11.111.111-1", "Juan")
        with self.assertRaises(TypeError):
            Prenda("A", "Polera", "M", 1000, 1)

    def test_precio_polimorfico(self):
        self.assertEqual(PrendaTermica("A", "Beatle", "M", 10000, 5, "Tortuga", "Alto").calcular_precio_final(), 11500)
        self.assertEqual(PrendaEstandar("B", "Polera", "M", 1000, 9, "Corta").calcular_precio_final(5), 5000)
        self.assertEqual(PrendaEstandar("B", "Polera", "M", 1000, 9, "Corta").calcular_precio_final(6), 5400)
        self.assertEqual(RopaInterior("C", "Calza", "L", 1000, 5, "Ancho", "Regular").calcular_precio_final(), 1000)
        self.assertEqual(RopaInterior("C", "Calza", "XXL", 1000, 5, "Ancho", "Regular").calcular_precio_final(), 1100)

    def test_prenda_rechaza_datos_invalidos(self):
        with self.assertRaises(ValueError):
            PrendaEstandar("B", "Polera", "XS", 1000, 1, "Corta")
        with self.assertRaises(ValueError):
            PrendaEstandar("B", "Polera", "M", 0, 1, "Corta")
        with self.assertRaises(ValueError):
            PrendaEstandar("B", "Polera", "M", 1000, -1, "Corta")
        with self.assertRaises(ValueError):
            PrendaEstandar("", "Polera", "M", 1000, 1, "Corta")


class TestStock(BaseTienda):
    def test_no_se_agrega_mas_que_el_stock(self):
        venta = Venta("Carlos")
        prenda = self.almacen.buscar_prenda("INT-002")  # stock 2
        with self.assertRaises(SinStockException):
            venta.agregar_prenda(prenda, 3)
        with self.assertRaises(SinStockException):
            self.ctrl.ventas.agregar_prenda(venta, "INT-002", "3")
        self.assertEqual(venta.detalles, [])

    def test_acumulado_en_carro_no_supera_stock(self):
        venta = Venta("Carlos")
        self.ctrl.ventas.agregar_prenda(venta, "INT-002", "2")
        with self.assertRaises(SinStockException):
            self.ctrl.ventas.agregar_prenda(venta, "INT-002", "1")
        self.assertEqual(venta.cantidad_de("INT-002"), 2)

    def test_cantidad_invalida(self):
        venta = Venta("Carlos")
        for cantidad in ["0", "-1", "abc", "1.5", "", "9" * 50]:
            with self.assertRaises(ValueError):
                self.ctrl.ventas.agregar_prenda(venta, "EST-001", cantidad)
        self.assertEqual(venta.detalles, [])

    def test_prenda_inexistente(self):
        with self.assertRaises(ValueError):
            self.ctrl.ventas.agregar_prenda(Venta("Carlos"), "NO-EXISTE", "1")

    def test_stock_no_queda_negativo(self):
        self.ctrl.inventario.ajustar_stock("INT-002", -2)
        with self.assertRaises(ValueError):
            self.ctrl.inventario.ajustar_stock("INT-002", -1)
        self.assertEqual(self.almacen.buscar_prenda("INT-002").stock, 0)

    def test_stock_baja_despues_de_armar_el_carro(self):
        venta = self.nueva_venta("INT-002", 2)
        self.ctrl.inventario.ajustar_stock("INT-002", -1)
        with self.assertRaises(SinStockException):
            self.ctrl.ventas.registrar_venta(venta, Efectivo(100000))
        self.assertEqual(self.almacen.ventas, [])
        self.assertEqual(self.almacen.buscar_prenda("INT-002").stock, 1)

    def test_prenda_eliminada_con_carro_abierto(self):
        venta = self.nueva_venta("INT-002", 1)
        self.ctrl.inventario.eliminar_prenda("INT-002")
        with self.assertRaises(SinStockException):
            self.ctrl.ventas.registrar_venta(venta, Efectivo(100000))


class TestVentas(BaseTienda):
    def test_venta_exitosa_descuenta_stock_y_asigna_folio(self):
        venta = self.nueva_venta("EST-001", 2)  # 2 x 5.000
        self.ctrl.ventas.registrar_venta(venta, Efectivo(10000))
        self.assertEqual(venta.estado, EstadoVenta.PAGADA)
        self.assertEqual(venta.folio, 1001)
        self.assertEqual(self.almacen.buscar_prenda("EST-001").stock, 18)

    def test_armar_carro_no_descuenta_stock(self):
        self.nueva_venta("EST-001", 2)
        self.assertEqual(self.almacen.buscar_prenda("EST-001").stock, 20)

    def test_iva_incluido_y_boleta_cuadra(self):
        venta = self.nueva_venta("EST-001", 2)  # $10.000
        self.assertEqual(venta.calcular_total(), 10000)
        self.assertEqual(venta.calcular_iva(), 1597)
        self.assertEqual(venta.calcular_neto(), 8403)
        self.assertEqual(venta.calcular_neto() + venta.calcular_iva(), venta.calcular_total())

    def test_efectivo_insuficiente_no_cambia_nada(self):
        venta = self.nueva_venta("EST-001", 1)
        with self.assertRaises(PagoRechazadoException):
            self.ctrl.ventas.registrar_venta(venta, Efectivo(100))
        self.assertEqual(venta.estado, EstadoVenta.PENDIENTE)
        self.assertEqual(self.almacen.buscar_prenda("EST-001").stock, 20)

    def test_efectivo_calcula_vuelto(self):
        venta = self.nueva_venta("EST-001", 1)
        self.ctrl.ventas.registrar_venta(venta, Efectivo(6000))
        self.assertIn("Vuelto: $1.000", venta.comprobante)

    def test_efectivo_exacto(self):
        venta = self.nueva_venta("EST-001", 1)
        self.ctrl.ventas.registrar_venta(venta, Efectivo(5000))
        self.assertIn("Vuelto: $0", venta.comprobante)

    def test_transferencia_valida_comprobante(self):
        venta = self.nueva_venta()
        with self.assertRaises(PagoRechazadoException):
            self.ctrl.ventas.registrar_venta(venta, Transferencia(""))
        self.ctrl.ventas.registrar_venta(venta, Transferencia("abc123"))
        self.assertIn("ABC123", venta.comprobante)

    def test_transferencia_no_repite_comprobante(self):
        self.ctrl.ventas.registrar_venta(self.nueva_venta(), Transferencia("ABC123"))
        venta = self.nueva_venta()
        with self.assertRaises(PagoRechazadoException):
            self.ctrl.ventas.registrar_venta(venta, Transferencia("abc123"))
        self.assertEqual(self.almacen.buscar_prenda("EST-001").stock, 19)

    def test_tarjeta_valida_digitos(self):
        for digitos in ["", "123", "abcd", "12345"]:
            with self.assertRaises(PagoRechazadoException):
                self.ctrl.ventas.registrar_venta(self.nueva_venta(), TarjetaDebito(digitos))
        self.ctrl.ventas.registrar_venta(self.nueva_venta(), TarjetaDebito("1234"))

    def test_crear_medio_pago_desde_texto(self):
        ventas = self.ctrl.ventas
        self.assertIsInstance(ventas.crear_medio_pago("Efectivo", "50.000"), Efectivo)
        self.assertIsInstance(ventas.crear_medio_pago("Transferencia", "ABC123"), Transferencia)
        self.assertIsInstance(ventas.crear_medio_pago("Tarjeta de Débito", "1234"), TarjetaDebito)
        for nombre, dato in [("Efectivo", "abc"), ("Efectivo", ""), ("Efectivo", "-5000"), ("Bitcoin", "1")]:
            with self.assertRaises(ValueError):
                ventas.registrar_venta(self.nueva_venta(), ventas.crear_medio_pago(nombre, dato))
        self.assertEqual(self.almacen.ventas, [])

    def test_venta_vacia_o_sin_cliente(self):
        venta = Venta("Carlos")
        self.ctrl.ventas.asignar_cliente(venta, self.cliente.rut)
        with self.assertRaises(ValueError):
            self.ctrl.ventas.registrar_venta(venta, Efectivo(1000))

        venta = Venta("Carlos")
        self.ctrl.ventas.agregar_prenda(venta, "EST-001", "1")
        with self.assertRaises(ValueError):
            self.ctrl.ventas.registrar_venta(venta, Efectivo(100000))

    def test_cliente_eliminado_con_carro_abierto(self):
        venta = self.nueva_venta()
        self.ctrl.clientes.eliminar(self.cliente.rut)
        with self.assertRaises(ValueError):
            self.ctrl.ventas.registrar_venta(venta, Efectivo(100000))
        self.assertEqual(self.almacen.buscar_prenda("EST-001").stock, 20)

    def test_venta_pagada_no_se_cobra_ni_modifica_de_nuevo(self):
        venta = self.nueva_venta()
        self.ctrl.ventas.registrar_venta(venta, Efectivo(5000))
        with self.assertRaises(ValueError):
            self.ctrl.ventas.registrar_venta(venta, Efectivo(5000))
        with self.assertRaises(ValueError):
            self.ctrl.ventas.agregar_prenda(venta, "EST-001", "1")
        with self.assertRaises(ValueError):
            self.ctrl.ventas.quitar_detalle(venta, 0)
        self.assertEqual(self.almacen.buscar_prenda("EST-001").stock, 19)

    def test_cancelar_devuelve_stock(self):
        venta = self.nueva_venta("EST-001", 3)
        self.ctrl.ventas.registrar_venta(venta, Efectivo(100000))
        self.ctrl.ventas.cancelar_venta(venta.folio)
        self.assertEqual(venta.estado, EstadoVenta.CANCELADA)
        self.assertEqual(self.almacen.buscar_prenda("EST-001").stock, 20)
        with self.assertRaises(ValueError):
            self.ctrl.ventas.cancelar_venta(venta.folio)
        self.assertEqual(self.almacen.buscar_prenda("EST-001").stock, 20)

    def test_entregada_no_se_cancela(self):
        venta = self.nueva_venta()
        self.ctrl.ventas.registrar_venta(venta, Efectivo(100000))
        self.ctrl.ventas.entregar_venta(venta.folio)
        with self.assertRaises(ValueError):
            self.ctrl.ventas.cancelar_venta(venta.folio)
        with self.assertRaises(ValueError):
            self.ctrl.ventas.entregar_venta(venta.folio)

    def test_cliente_frecuente_recibe_descuento(self):
        for _ in range(3):
            self.ctrl.ventas.registrar_venta(self.nueva_venta(), Efectivo(100000))
        self.assertTrue(self.ctrl.ventas.es_cliente_frecuente(self.cliente.rut))
        venta = self.nueva_venta("EST-001", 2)  # $10.000 - 5%
        self.assertEqual(venta.calcular_total(), 9500)


class TestGestion(BaseTienda):
    def test_login(self):
        usuarios = self.ctrl.usuarios
        self.assertEqual(usuarios.iniciar_sesion("marisol", "admin123").obtener_rol(), "Administrador")
        self.assertFalse(usuarios.iniciar_sesion(" CARLOS ", "vende123").puede_administrar())
        for usuario, clave in [("marisol", "mala"), ("nadie", "admin123"), ("", "")]:
            with self.assertRaises(ValueError):
                usuarios.iniciar_sesion(usuario, clave)

    def test_clave_no_queda_en_texto_simple(self):
        contenido = (self.carpeta / "usuarios.json").read_text(encoding="utf-8")
        self.assertNotIn("admin123", contenido)

    def test_crear_usuario_y_duplicados(self):
        usuarios = self.ctrl.usuarios
        usuarios.crear_usuario("Vendedor", "55.555.555-5", "Ana Soto", "ana", "clave123")
        self.assertIsInstance(self.reabrir()[1].usuarios.iniciar_sesion("ana", "clave123"), Vendedor)
        with self.assertRaises(ValueError):
            usuarios.crear_usuario("Vendedor", "66.666.666-6", "Otra", "ana", "clave123")
        with self.assertRaises(ValueError):
            usuarios.crear_usuario("Vendedor", "55.555.555-5", "Otra", "otra", "clave123")
        with self.assertRaises(ValueError):
            usuarios.crear_usuario("Vendedor", "66.666.666-6", "Otra", "otra", "corta")
        with self.assertRaises(ValueError):
            usuarios.crear_usuario("Jefe", "66.666.666-6", "Otra", "otra", "clave123")

    def test_no_se_elimina_a_si_mismo(self):
        marisol = self.ctrl.usuarios.iniciar_sesion("marisol", "admin123")
        with self.assertRaises(ValueError):
            self.ctrl.usuarios.eliminar_usuario("marisol", marisol)

    def test_cliente_duplicado(self):
        with self.assertRaises(ValueError):
            self.ctrl.clientes.registrar("11.111.111-1", "Otro", "+56911223344", "o@o.cl")

    def test_rut_de_cliente_no_se_cambia(self):
        with self.assertRaises(ValueError):
            self.ctrl.clientes.actualizar("11111111-1", "22.222.222-2", "Juan", "+56911223344", "j@j.cl")
        self.ctrl.clientes.actualizar("11111111-1", "11.111.111-1", "Juan Nuevo", "912345678", "j@j.cl")
        self.assertEqual(self.almacen.buscar_cliente("11111111-1").nombre, "Juan Nuevo")

    def test_actualizar_cliente_con_datos_malos_no_cambia_nada(self):
        with self.assertRaises(ValueError):
            self.ctrl.clientes.actualizar("11111111-1", "11.111.111-1", "Nuevo Nombre", "123", "j@j.cl")
        self.assertEqual(self.almacen.buscar_cliente("11111111-1").nombre, "Juan Perez")

    def test_no_se_elimina_con_ventas(self):
        self.ctrl.ventas.registrar_venta(self.nueva_venta(), Efectivo(100000))
        with self.assertRaises(ValueError):
            self.ctrl.clientes.eliminar(self.cliente.rut)
        with self.assertRaises(ValueError):
            self.ctrl.inventario.eliminar_prenda("EST-001")

    def test_crear_prenda_desde_texto(self):
        inventario = self.ctrl.inventario
        inventario.crear_prenda("Estándar", "est-9", "Polera nueva", "M", "1.000", "5", "Corta")
        self.assertEqual(self.almacen.buscar_prenda("EST-9").stock, 5)
        casos = [
            ("Estándar", "EST-001", "Polera", "M", "1000", "1", "Corta"),  # código repetido
            ("Inventado", "X-1", "Polera", "M", "1000", "1"),              # tipo desconocido
            ("Estándar", "X-1", "Polera", "M", "abc", "1", "Corta"),       # precio no numérico
            ("Estándar", "X-1", "Polera", "M", "0", "1", "Corta"),         # precio cero
            ("Estándar", "X-1", "Polera", "M", "1000", "-1", "Corta"),     # stock negativo
            ("Estándar", "X-1", "Polera", "XS", "1000", "1", "Corta"),     # talla inválida
        ]
        for caso in casos:
            with self.assertRaises(ValueError):
                inventario.crear_prenda(*caso)
        self.assertIsNone(self.almacen.buscar_prenda("X-1"))

    def test_cambiar_precio_desde_texto(self):
        self.ctrl.inventario.cambiar_precio("EST-001", "6.500")
        self.assertEqual(self.almacen.buscar_prenda("EST-001").precio_base, 6500)
        for texto in ["abc", "0", "-1", ""]:
            with self.assertRaises(ValueError):
                self.ctrl.inventario.cambiar_precio("EST-001", texto)
        self.assertEqual(self.almacen.buscar_prenda("EST-001").precio_base, 6500)

    def test_codigo_de_prenda_duplicado(self):
        with self.assertRaises(ValueError):
            self.ctrl.inventario.crear_prenda("Estándar", "est-001", "Polera", "M", "1000", "1", "Corta")


class TestPersistencia(BaseTienda):
    def test_todo_sobrevive_al_reinicio(self):
        self.ctrl.clientes.registrar("55.555.555-5", "Ana Soto", "912345678", "ana@correo.cl")
        self.ctrl.inventario.crear_prenda("Ropa Interior", "NUE-1", "Calza", "XL", "1000", "3", "Ancho", "Regular")
        venta = self.nueva_venta("TER-001", 2)
        self.ctrl.ventas.registrar_venta(venta, TarjetaDebito("1234"))

        almacen, _ = self.reabrir()
        self.assertIsNotNone(almacen.buscar_cliente("55555555-5"))
        self.assertEqual(almacen.buscar_prenda("NUE-1").calcular_precio_final(), 1100)
        self.assertEqual(almacen.buscar_prenda("TER-001").stock, 8)
        guardada = almacen.buscar_venta(venta.folio)
        self.assertEqual(guardada.calcular_total(), venta.calcular_total())
        self.assertEqual(generar_boleta(guardada), generar_boleta(venta))

    def test_folio_continua_despues_de_reiniciar(self):
        self.ctrl.ventas.registrar_venta(self.nueva_venta(), Efectivo(100000))
        almacen, ctrl = self.reabrir()
        venta = ctrl.ventas.nueva_venta(almacen.buscar_usuario("carlos"))
        ctrl.ventas.asignar_cliente(venta, almacen.clientes[0].rut)
        ctrl.ventas.agregar_prenda(venta, "EST-001", "1")
        ctrl.ventas.registrar_venta(venta, Efectivo(100000))
        self.assertEqual(venta.folio, 1002)

    def test_precio_viejo_se_mantiene_en_la_boleta(self):
        venta = self.nueva_venta("EST-001", 1)
        self.ctrl.ventas.registrar_venta(venta, Efectivo(100000))
        self.ctrl.inventario.cambiar_precio("EST-001", "9999")
        self.assertEqual(self.reabrir()[0].buscar_venta(venta.folio).calcular_total(), 5000)

    def test_archivos_danados_se_recrean(self):
        contenidos = ["{no es json", '[{"rut": "falta todo"}]', '{"a": 1}', "[1, 2]", ""]
        for contenido in contenidos:
            for nombre in ["prendas", "clientes", "usuarios", "ventas"]:
                (self.carpeta / f"{nombre}.json").write_text(contenido, encoding="utf-8")
            almacen, ctrl = self.reabrir()
            self.assertEqual(len(almacen.avisos), 4, contenido)
            self.assertEqual(ctrl.avisos, almacen.avisos)
            self.assertIsNotNone(ctrl.usuarios.iniciar_sesion("marisol", "admin123"))
            self.assertTrue((self.carpeta / "prendas.corrupto").exists())

    def test_archivo_faltante_se_recrea(self):
        (self.carpeta / "prendas.json").unlink()
        almacen, _ = self.reabrir()
        self.assertEqual(almacen.avisos, [])
        self.assertEqual(len(almacen.prendas), 6)

    def test_usuarios_sin_administrador_se_consideran_danados(self):
        datos = json.loads((self.carpeta / "usuarios.json").read_text(encoding="utf-8"))
        solo_vendedores = [d for d in datos if d["rol"] == "Vendedor"]
        (self.carpeta / "usuarios.json").write_text(json.dumps(solo_vendedores), encoding="utf-8")
        self.assertIsNotNone(self.reabrir()[1].usuarios.iniciar_sesion("marisol", "admin123"))


class TestSeparacionMVC(unittest.TestCase):
    """La capa de modelo no debe conocer a controladores ni vistas, y los controladores no deben conocer la pantalla."""

    def revisar(self, carpeta, prohibidos):
        for archivo in Path(carpeta).glob("*.py"):
            texto = archivo.read_text(encoding="utf-8")
            for prohibido in prohibidos:
                self.assertNotIn(prohibido, texto, f"{archivo} no debería usar {prohibido}")

    def test_modelo_no_usa_controladores_ni_vistas(self):
        self.revisar("models", ["import controllers", "from controllers", "import views", "from views", "tkinter"])

    def test_controladores_no_usan_vistas_ni_pantalla(self):
        self.revisar("controllers", ["import views", "from views", "tkinter", "messagebox"])


if __name__ == "__main__":
    unittest.main()
