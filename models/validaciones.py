"""
Funciones de validación y formato usadas por las clases del negocio.
Todas lanzan ValueError con un mensaje claro cuando el dato no es válido.
"""

import re

MAXIMO_NUMERO = 100_000_000  # Límite para evitar precios o cantidades absurdas


def validar_rut(rut: str) -> str:
    """Valida el dígito verificador (módulo 11) y retorna el RUT como 12345678-5."""
    limpio = rut.replace(".", "").replace("-", "").strip().upper()
    if not re.fullmatch(r"\d{7,8}[0-9K]", limpio):
        raise ValueError("El RUT debe tener el formato 12.345.678-5.")

    numero = limpio[:-1]
    digito = limpio[-1]

    suma = 0
    factor = 2
    for cifra in reversed(numero):
        suma += int(cifra) * factor
        factor = 2 if factor == 7 else factor + 1

    resto = 11 - (suma % 11)
    if resto == 11:
        esperado = "0"
    elif resto == 10:
        esperado = "K"
    else:
        esperado = str(resto)

    if digito != esperado:
        raise ValueError("El dígito verificador del RUT no es correcto.")
    return f"{numero}-{digito}"


def validar_nombre(nombre: str) -> str:
    """El nombre solo puede tener letras y espacios, con al menos 2 letras."""
    limpio = " ".join(nombre.split())
    if len(limpio) < 2 or not all(c.isalpha() or c == " " for c in limpio):
        raise ValueError("El nombre debe tener al menos 2 letras y no puede tener números ni símbolos.")
    return limpio.title()


def validar_telefono(telefono: str) -> str:
    """Acepta un celular chileno de 9 dígitos, con o sin +56."""
    limpio = telefono.replace(" ", "")
    if not re.fullmatch(r"(\+?56)?9\d{8}", limpio):
        raise ValueError("El teléfono debe ser un celular como +56912345678.")
    return "+56" + limpio[-9:]


def validar_correo(correo: str) -> str:
    limpio = correo.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", limpio):
        raise ValueError("El correo debe tener un formato como nombre@dominio.cl.")
    return limpio


def validar_entero(valor: int, nombre: str, minimo: int = 0) -> int:
    """Revisa que el valor sea un entero dentro del rango permitido."""
    if type(valor) is not int:
        raise ValueError(f"{nombre} debe ser un número entero.")
    if valor < minimo:
        raise ValueError(f"{nombre} no puede ser menor a {minimo}.")
    if valor > MAXIMO_NUMERO:
        raise ValueError(f"{nombre} es demasiado grande.")
    return valor


def texto_a_entero(texto: str, nombre: str) -> int:
    """Convierte lo escrito en pantalla a entero. Acepta puntos de miles: 50.000."""
    limpio = texto.strip().replace("$", "")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", limpio):
        limpio = limpio.replace(".", "")
    if not re.fullmatch(r"-?[0-9]+", limpio):
        raise ValueError(f"{nombre} debe ser un número entero.")
    if len(limpio) > 12:
        raise ValueError(f"{nombre} es demasiado grande.")
    return int(limpio)


def formato_clp(monto: int) -> str:
    """Muestra un monto en pesos chilenos: 12345 -> $12.345."""
    return f"${monto:,}".replace(",", ".")
