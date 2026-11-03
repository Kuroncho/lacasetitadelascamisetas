"""
Pruebas automáticas de las reglas del negocio y de los casos borde.
Para ejecutar: py -m unittest -v
"""

import json
import tempfile
import unittest
from pathlib import Path

from models.excepciones import PagoRechazadoException, SinStockException
from models.gestor_datos import GestorDatos
from models.pago import Efectivo, TarjetaDebito, Transferencia
from models.prenda import Prenda, PrendaEstandar, PrendaTermica, RopaInterior
from models.tienda import Tienda
from models.usuario import Cliente, Usuario, Vendedor
from models.validaciones import formato_clp, texto_a_entero, validar_rut
from models.venta import EstadoVenta, Venta


class BaseTienda(unittest.TestCase):
    """Cada prueba parte con una tienda nueva en una carpeta temporal."""

    def setUp(self):
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.carpeta = Path(carpeta.name)
        self.tienda = Tienda(GestorDatos(self.carpeta))
        self.cliente = self.tienda.clientes[0]

    def nueva_venta(self, codigo="EST-001", cantidad=1):
        venta = Venta("Carlos Baeza")
        self.tienda.asignar_cliente(venta, self.cliente)
        venta.agregar_prenda(self.tienda.buscar_prenda(codigo), cantidad)
        return venta

    def reabrir(self):
        return Tienda(GestorDatos(self.carpeta))


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
        prenda = self.tienda.buscar_prenda("INT-002")  # stock 2
        with self.assertRaises(SinStockException):
            venta.agregar_prenda(prenda, 3)
        self.assertEqual(venta.detalles, [])

    def test_acumulado_en_carro_no_supera_stock(self):
        venta = Venta("Carlos")
        prenda = self.tienda.buscar_prenda("INT-002")
        venta.agregar_prenda(prenda, 2)
        with self.assertRaises(SinStockException):
            venta.agregar_prenda(prenda, 1)
        self.assertEqual(venta.cantidad_de("INT-002"), 2)

    def test_cantidad_invalida(self):
        venta = Venta("Carlos")
        for cantidad in [0, -1]:
            with self.assertRaises(ValueError):
                venta.agregar_prenda(self.tienda.buscar_prenda("EST-001"), cantidad)

    def test_stock_no_queda_negativo(self):
        self.tienda.ajustar_stock("INT-002", -2)
        with self.assertRaises(ValueError):
            self.tienda.ajustar_stock("INT-002", -1)
        self.assertEqual(self.tienda.buscar_prenda("INT-002").stock, 0)

    def test_stock_baja_despues_de_armar_el_carro(self):
        venta = self.nueva_venta("INT-002", 2)
        self.tienda.ajustar_stock("INT-002", -1)
        with self.assertRaises(SinStockException):
            self.tienda.registrar_venta(venta, Efectivo(100000))
        self.assertEqual(self.tienda.ventas, [])
        self.assertEqual(self.tienda.buscar_prenda("INT-002").stock, 1)

    def test_prenda_eliminada_con_carro_abierto(self):
        venta = self.nueva_venta("INT-002", 1)
        self.tienda.eliminar_prenda("INT-002")
        with self.assertRaises(SinStockException):
            self.tienda.registrar_venta(venta, Efectivo(100000))


class TestVentas(BaseTienda):
    def test_venta_exitosa_descuenta_stock_y_asigna_folio(self):
        venta = self.nueva_venta("EST-001", 2)  # 2 x 5.000
        self.tienda.registrar_venta(venta, Efectivo(10000))
        self.assertEqual(venta.estado, EstadoVenta.PAGADA)
        self.assertEqual(venta.folio, 1001)
        self.assertEqual(self.tienda.buscar_prenda("EST-001").stock, 18)

    def test_armar_carro_no_descuenta_stock(self):
        self.nueva_venta("EST-001", 2)
        self.assertEqual(self.tienda.buscar_prenda("EST-001").stock, 20)

    def test_iva_incluido_y_boleta_cuadra(self):
        venta = self.nueva_venta("EST-001", 2)  # $10.000
        self.assertEqual(venta.calcular_total(), 10000)
        self.assertEqual(venta.calcular_iva(), 1597)
        self.assertEqual(venta.calcular_neto(), 8403)
        self.assertEqual(venta.calcular_neto() + venta.calcular_iva(), venta.calcular_total())

    def test_efectivo_insuficiente_no_cambia_nada(self):
        venta = self.nueva_venta("EST-001", 1)
        with self.assertRaises(PagoRechazadoException):
            self.tienda.registrar_venta(venta, Efectivo(100))
        self.assertEqual(venta.estado, EstadoVenta.PENDIENTE)
        self.assertEqual(self.tienda.buscar_prenda("EST-001").stock, 20)

    def test_efectivo_calcula_vuelto(self):
        venta = self.nueva_venta("EST-001", 1)
        self.tienda.registrar_venta(venta, Efectivo(6000))
        self.assertIn("Vuelto: $1.000", venta.comprobante)

    def test_efectivo_exacto(self):
        venta = self.nueva_venta("EST-001", 1)
        self.tienda.registrar_venta(venta, Efectivo(5000))
        self.assertIn("Vuelto: $0", venta.comprobante)

    def test_transferencia_valida_comprobante(self):
        venta = self.nueva_venta()
        with self.assertRaises(PagoRechazadoException):
            self.tienda.registrar_venta(venta, Transferencia(""))
        self.tienda.registrar_venta(venta, Transferencia("abc123"))
        self.assertIn("ABC123", venta.comprobante)

    def test_transferencia_no_repite_comprobante(self):
        self.tienda.registrar_venta(self.nueva_venta(), Transferencia("ABC123"))
        venta = self.nueva_venta()
        with self.assertRaises(PagoRechazadoException):
            self.tienda.registrar_venta(venta, Transferencia("abc123"))
        self.assertEqual(self.tienda.buscar_prenda("EST-001").stock, 19)

    def test_tarjeta_valida_digitos(self):
        for digitos in ["", "123", "abcd", "12345"]:
            with self.assertRaises(PagoRechazadoException):
                self.tienda.registrar_venta(self.nueva_venta(), TarjetaDebito(digitos))
        self.tienda.registrar_venta(self.nueva_venta(), TarjetaDebito("1234"))

    def test_venta_vacia_o_sin_cliente(self):
        venta = Venta("Carlos")
        self.tienda.asignar_cliente(venta, self.cliente)
        with self.assertRaises(ValueError):
            self.tienda.registrar_venta(venta, Efectivo(1000))

        venta = Venta("Carlos")
        venta.agregar_prenda(self.tienda.buscar_prenda("EST-001"), 1)
        with self.assertRaises(ValueError):
            self.tienda.registrar_venta(venta, Efectivo(100000))

    def test_cliente_eliminado_con_carro_abierto(self):
        venta = self.nueva_venta()
        self.tienda.eliminar_cliente(self.cliente.rut)
        with self.assertRaises(ValueError):
            self.tienda.registrar_venta(venta, Efectivo(100000))
        self.assertEqual(self.tienda.buscar_prenda("EST-001").stock, 20)

    def test_venta_pagada_no_se_cobra_ni_modifica_de_nuevo(self):
        venta = self.nueva_venta()
        self.tienda.registrar_venta(venta, Efectivo(5000))
        with self.assertRaises(ValueError):
            self.tienda.registrar_venta(venta, Efectivo(5000))
        with self.assertRaises(ValueError):
            venta.agregar_prenda(self.tienda.buscar_prenda("EST-001"), 1)
        with self.assertRaises(ValueError):
            venta.quitar_detalle(0)
        self.assertEqual(self.tienda.buscar_prenda("EST-001").stock, 19)

    def test_cancelar_devuelve_stock(self):
        venta = self.nueva_venta("EST-001", 3)
        self.tienda.registrar_venta(venta, Efectivo(100000))
        self.tienda.cancelar_venta(venta.folio)
        self.assertEqual(venta.estado, EstadoVenta.CANCELADA)
        self.assertEqual(self.tienda.buscar_prenda("EST-001").stock, 20)
        with self.assertRaises(ValueError):
            self.tienda.cancelar_venta(venta.folio)
        self.assertEqual(self.tienda.buscar_prenda("EST-001").stock, 20)

    def test_entregada_no_se_cancela(self):
        venta = self.nueva_venta()
        self.tienda.registrar_venta(venta, Efectivo(100000))
        self.tienda.entregar_venta(venta.folio)
        with self.assertRaises(ValueError):
            self.tienda.cancelar_venta(venta.folio)
        with self.assertRaises(ValueError):
            self.tienda.entregar_venta(venta.folio)

    def test_cliente_frecuente_recibe_descuento(self):
        for _ in range(3):
            self.tienda.registrar_venta(self.nueva_venta(), Efectivo(100000))
        self.assertTrue(self.tienda.es_cliente_frecuente(self.cliente.rut))
        venta = self.nueva_venta("EST-001", 2)  # $10.000 - 5%
        self.assertEqual(venta.calcular_total(), 9500)


class TestGestion(BaseTienda):
    def test_login(self):
        self.assertEqual(self.tienda.iniciar_sesion("marisol", "admin123").obtener_rol(), "Administrador")
        self.assertFalse(self.tienda.iniciar_sesion(" CARLOS ", "vende123").puede_administrar())
        for usuario, clave in [("marisol", "mala"), ("nadie", "admin123"), ("", "")]:
            with self.assertRaises(ValueError):
                self.tienda.iniciar_sesion(usuario, clave)

    def test_clave_no_queda_en_texto_simple(self):
        contenido = (self.carpeta / "usuarios.json").read_text(encoding="utf-8")
        self.assertNotIn("admin123", contenido)

    def test_crear_usuario_y_duplicados(self):
        self.tienda.crear_usuario("Vendedor", "55.555.555-5", "Ana Soto", "ana", "clave123")
        self.assertIsInstance(self.reabrir().iniciar_sesion("ana", "clave123"), Vendedor)
        with self.assertRaises(ValueError):
            self.tienda.crear_usuario("Vendedor", "66.666.666-6", "Otra", "ana", "clave123")
        with self.assertRaises(ValueError):
            self.tienda.crear_usuario("Vendedor", "55.555.555-5", "Otra", "otra", "clave123")
        with self.assertRaises(ValueError):
            self.tienda.crear_usuario("Vendedor", "66.666.666-6", "Otra", "otra", "corta")

    def test_no_se_elimina_a_si_mismo(self):
        marisol = self.tienda.iniciar_sesion("marisol", "admin123")
        with self.assertRaises(ValueError):
            self.tienda.eliminar_usuario("marisol", marisol)

    def test_cliente_duplicado(self):
        with self.assertRaises(ValueError):
            self.tienda.registrar_cliente("11.111.111-1", "Otro", "+56911223344", "o@o.cl")

    def test_no_se_elimina_con_ventas(self):
        self.tienda.registrar_venta(self.nueva_venta(), Efectivo(100000))
        with self.assertRaises(ValueError):
            self.tienda.eliminar_cliente(self.cliente.rut)
        with self.assertRaises(ValueError):
            self.tienda.eliminar_prenda("EST-001")

    def test_codigo_de_prenda_duplicado(self):
        with self.assertRaises(ValueError):
            self.tienda.agregar_prenda(PrendaEstandar("est-001", "Polera", "M", 1000, 1, "Corta"))


class TestPersistencia(BaseTienda):
    def test_todo_sobrevive_al_reinicio(self):
        self.tienda.registrar_cliente("55.555.555-5", "Ana Soto", "912345678", "ana@correo.cl")
        self.tienda.agregar_prenda(RopaInterior("NUE-1", "Calza", "XL", 1000, 3, "Ancho", "Regular"))
        venta = self.nueva_venta("TER-001", 2)
        self.tienda.registrar_venta(venta, TarjetaDebito("1234"))

        otra = self.reabrir()
        self.assertIsNotNone(otra.buscar_cliente("55555555-5"))
        self.assertEqual(otra.buscar_prenda("NUE-1").calcular_precio_final(), 1100)
        self.assertEqual(otra.buscar_prenda("TER-001").stock, 8)
        guardada = otra.buscar_venta(venta.folio)
        self.assertEqual(guardada.calcular_total(), venta.calcular_total())
        self.assertEqual(guardada.generar_boleta(), venta.generar_boleta())

    def test_folio_continua_despues_de_reiniciar(self):
        self.tienda.registrar_venta(self.nueva_venta(), Efectivo(100000))
        otra = self.reabrir()
        venta = Venta("Carlos")
        otra.asignar_cliente(venta, otra.clientes[0])
        venta.agregar_prenda(otra.buscar_prenda("EST-001"), 1)
        otra.registrar_venta(venta, Efectivo(100000))
        self.assertEqual(venta.folio, 1002)

    def test_precio_viejo_se_mantiene_en_la_boleta(self):
        venta = self.nueva_venta("EST-001", 1)
        self.tienda.registrar_venta(venta, Efectivo(100000))
        self.tienda.cambiar_precio("EST-001", 9999)
        self.assertEqual(self.reabrir().buscar_venta(venta.folio).calcular_total(), 5000)

    def test_archivos_danados_se_recrean(self):
        contenidos = ["{no es json", '[{"rut": "falta todo"}]', '{"a": 1}', "[1, 2]", ""]
        for contenido in contenidos:
            for nombre in ["prendas", "clientes", "usuarios", "ventas"]:
                (self.carpeta / f"{nombre}.json").write_text(contenido, encoding="utf-8")
            tienda = self.reabrir()
            self.assertEqual(len(tienda.avisos), 4, contenido)
            self.assertIsNotNone(tienda.iniciar_sesion("marisol", "admin123"))
            self.assertTrue((self.carpeta / "prendas.corrupto").exists())

    def test_archivo_faltante_se_recrea(self):
        (self.carpeta / "prendas.json").unlink()
        tienda = self.reabrir()
        self.assertEqual(tienda.avisos, [])
        self.assertEqual(len(tienda.prendas), 6)

    def test_usuarios_sin_administrador_se_consideran_danados(self):
        datos = json.loads((self.carpeta / "usuarios.json").read_text(encoding="utf-8"))
        solo_vendedores = [d for d in datos if d["rol"] == "Vendedor"]
        (self.carpeta / "usuarios.json").write_text(json.dumps(solo_vendedores), encoding="utf-8")
        self.assertIsNotNone(self.reabrir().iniciar_sesion("marisol", "admin123"))


if __name__ == "__main__":
    unittest.main()
