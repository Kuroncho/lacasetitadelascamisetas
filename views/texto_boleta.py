"""
Texto de la boleta. Es presentación (cómo se ve la venta), por eso vive en las vistas
y no en el modelo. No usa Tkinter, así que también se puede probar sin ventana.
"""

# quote convierte un texto para que pueda ir dentro de una dirección web (espacios y tildes se codifican).
from urllib.parse import quote

# formato_clp muestra los montos con puntos de miles ($12.345).
from models.validaciones import formato_clp

# Número de WhatsApp de la tienda, con código de país y sin '+' (56 = Chile).
# PROVISIONAL: es un número de ejemplo y hay que reemplazarlo por el número real de la tienda.
NUMERO_WHATSAPP_TIENDA = "56900000000"


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


# Arma el mensaje con el resumen de la venta para enviarlo por WhatsApp. Es una función pura: solo lee la venta y devuelve un texto.
def generar_resumen_whatsapp(venta) -> str:
    lineas = [
        "CONFECCIONES MARISOL MENA",
        f"Resumen de tu compra - Folio N° {venta.folio}",
        "",
    ]
    # Por cada prenda: la descripción ya incluye la talla (por ejemplo "Polera (Talla M)"), la cantidad y el subtotal.
    for detalle in venta.detalles:
        lineas.append(f"- {detalle.descripcion} x{detalle.cantidad}: {formato_clp(detalle.subtotal)}")
    lineas.append("")
    lineas.append(f"TOTAL (IVA incluido): {formato_clp(venta.calcular_total())}")
    lineas.append(f"Medio de pago: {venta.medio_pago}")
    # join une todas las líneas en un solo texto, separadas por saltos de línea (\n).
    return "\n".join(lineas)


# Arma la dirección de WhatsApp: https://wa.me/<número>?text=<mensaje>.
# quote(..., safe="") codifica todo lo especial del mensaje: el espacio pasa a %20 y el salto de línea a %0A.
def generar_url_whatsapp(venta) -> str:
    return f"https://wa.me/{NUMERO_WHATSAPP_TIENDA}?text={quote(generar_resumen_whatsapp(venta), safe='')}"
