"""
Texto de la boleta. Es presentación (cómo se ve la venta), por eso vive en las vistas
y no en el modelo. No usa Tkinter, así que también se puede probar sin ventana.
"""

from models.validaciones import formato_clp


def generar_boleta(venta) -> str:
    lineas = [
        "=" * 50,
        "CONFECCIONES MARISOL MENA".center(50),
        "=" * 50,
        f"Folio N°:  {venta.folio}",
        f"Fecha:     {venta.fecha.strftime('%d-%m-%Y %H:%M')}",
        f"Vendedor:  {venta.vendedor}",
        f"Cliente:   {venta.cliente_nombre} (RUT {venta.cliente_rut})",
        f"Estado:    {venta.estado}",
        "-" * 50,
    ]
    for detalle in venta.detalles:
        lineas.append(f"{detalle.cantidad} x {detalle.descripcion}")
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
    return "\n".join(lineas)
