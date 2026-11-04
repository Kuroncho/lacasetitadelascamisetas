"""
Texto de la boleta. Es presentación (cómo se ve la venta), por eso vive en las vistas
y no en el modelo. No usa Tkinter, así que también se puede probar sin ventana.
"""

# formato_clp muestra los montos con puntos de miles ($12.345).
from models.validaciones import formato_clp


# Arma el texto de la boleta, línea por línea. Es presentación (cómo se ve la venta), por eso vive en las vistas y no en el modelo.
# Solo lee datos de la venta, no cambia nada.
def generar_boleta(venta) -> str:
    # Una lista de textos; cada elemento es una línea de la boleta. '=' * 50 repite el signo 50 veces.
    lineas = [
        "=" * 50,
        # center(50) centra el texto en un ancho de 50 caracteres.
        "CONFECCIONES MARISOL MENA".center(50),
        "=" * 50,
        f"Folio N°:  {venta.folio}",
        f"Fecha:     {venta.fecha.strftime('%d-%m-%Y %H:%M')}",
        f"Vendedor:  {venta.vendedor}",
        f"Cliente:   {venta.cliente_nombre} (RUT {venta.cliente_rut})",
        f"Estado:    {venta.estado}",
        "-" * 50,
    ]
    # Por cada prenda del carro se agregan dos líneas a la boleta.
    for detalle in venta.detalles:
        lineas.append(f"{detalle.cantidad} x {detalle.descripcion}")
        # En un f-string, ':>50' alinea el texto a la derecha en 50 espacios y ':<30' a la izquierda. Así los montos quedan en columna.
        lineas.append(f"{formato_clp(detalle.subtotal):>50}")
    lineas.append("-" * 50)
    lineas.append(f"{'Subtotal:':<30}{formato_clp(venta.calcular_subtotal()):>20}")
    lineas.append(f"{'Descuento cliente frecuente:':<30}{'-' + formato_clp(venta.calcular_descuento()):>20}")
    lineas.append(f"{'TOTAL A PAGAR:':<30}{formato_clp(venta.calcular_total()):>20}")
    lineas.append(f"{'  Neto incluido:':<30}{formato_clp(venta.calcular_neto()):>20}")
    lineas.append(f"{'  IVA incluido (19%):':<30}{formato_clp(venta.calcular_iva()):>20}")
    lineas.append("-" * 50)
    lineas.append(f"Pago: {venta.medio_pago}")
    lineas.append(venta.comprobante)
    lineas.append("=" * 50)
    # join une todas las líneas en un solo texto, separadas por saltos de línea (\n).
    return "\n".join(lineas)
