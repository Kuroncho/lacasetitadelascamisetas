"""
Funciones de validación y formato usadas por las clases del negocio.
Todas lanzan ValueError con un mensaje claro cuando el dato no es válido.
"""

# 'import' trae herramientas que Python ya incluye. 're' sirve para revisar si un texto cumple un patrón
# (por ejemplo, que un teléfono tenga 9 dígitos). Esos patrones se llaman "expresiones regulares".
import re

# Constante: un valor que no cambia mientras el programa corre. Por convención se escribe en MAYÚSCULAS.
# Los guiones bajos en 100_000_000 solo ayudan a leer el número (equivale a 100000000).
MAXIMO_NUMERO = 100_000_000  # Límite para evitar precios o cantidades absurdas


# Revisa que un RUT sea válido y lo deja siempre con el mismo formato (12345678-5).
# Una función se define con 'def'; recibe datos entre paréntesis y entrega un resultado con 'return'.
# Si el dato es inválido, 'raise' lanza un error y la función se detiene en ese punto.
def validar_rut(rut: str) -> str:
    """Valida el dígito verificador (módulo 11) y retorna el RUT como 12345678-5."""
    # Quita puntos, guion y espacios, y pasa todo a mayúscula (así se acepta tanto 'k' como 'K').
    limpio = rut.replace(".", "").replace("-", "").strip().upper()
    # Debe tener 7 u 8 números y, al final, un número o la letra K. Si no, está mal escrito.
    if not re.fullmatch(r"\d{7,8}[0-9K]", limpio):
        raise ValueError("El RUT debe tener el formato 12.345.678-5.")

    # Los corchetes con ':' cortan un texto. [:-1] es "todo menos el último carácter" (el cuerpo del RUT)
    # y [-1] es "solo el último" (el dígito verificador).
    numero = limpio[:-1]
    digito = limpio[-1]

    # Cálculo del dígito verificador (método "módulo 11"): se multiplica cada cifra, de derecha a izquierda,
    # por 2, 3, 4, 5, 6, 7, 2, 3... y se suman los resultados.
    suma = 0
    factor = 2
    # 'for' repite lo que está adentro una vez por cada elemento. 'reversed' recorre el número al revés.
    for cifra in reversed(numero):
        suma += int(cifra) * factor
        # Forma corta de if/else: si el factor llegó a 7 vuelve a 2; si no, sube de a 1.
        factor = 2 if factor == 7 else factor + 1

    # El símbolo % entrega el resto de una división. Con eso se obtiene el dígito que debería tener el RUT.
    resto = 11 - (suma % 11)
    # Casos especiales del método: el 11 se escribe como 0 y el 10 como K.
    if resto == 11:
        esperado = "0"
    elif resto == 10:
        esperado = "K"
    else:
        esperado = str(resto)

    # '!=' significa 'distinto de'. Si el dígito escrito no coincide con el calculado, el RUT es falso.
    if digito != esperado:
        raise ValueError("El dígito verificador del RUT no es correcto.")
    # Un texto con una f delante (f-string) reemplaza lo que está entre llaves { } por su valor.
    return f"{numero}-{digito}"


# El nombre solo puede tener letras y espacios, con al menos 2 letras.
def validar_nombre(nombre: str) -> str:
    """El nombre solo puede tener letras y espacios, con al menos 2 letras."""
    # split() separa el texto en palabras y join() las junta con un solo espacio: así se eliminan los espacios repetidos.
    limpio = " ".join(nombre.split())
    # len() cuenta los caracteres. all(...) es verdadero solo si TODAS las letras cumplen la condición
    # (ser letra o espacio); 'c for c in limpio' recorre el nombre letra por letra.
    if len(limpio) < 2 or not all(c.isalpha() or c == " " for c in limpio):
        raise ValueError("El nombre debe tener al menos 2 letras y no puede tener números ni símbolos.")
    # title() deja cada palabra con la primera letra en mayúscula: 'juan perez' queda 'Juan Perez'.
    return limpio.title()


# Acepta un celular chileno de 9 dígitos que parte con 9, con o sin +56.
def validar_telefono(telefono: str) -> str:
    """Acepta un celular chileno de 9 dígitos, con o sin +56."""
    limpio = telefono.replace(" ", "")
    if not re.fullmatch(r"(\+?56)?9\d{8}", limpio):
        raise ValueError("El teléfono debe ser un celular como +56912345678.")
    # [-9:] toma los últimos 9 caracteres. Así siempre se guarda con el formato +569XXXXXXXX.
    return "+56" + limpio[-9:]


# Revisa que el correo tenga la forma algo@algo.algo (sin espacios y con una sola arroba).
def validar_correo(correo: str) -> str:
    limpio = correo.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", limpio):
        raise ValueError("El correo debe tener un formato como nombre@dominio.cl.")
    return limpio


# Revisa que un número esté dentro del rango permitido. 'minimo=0' es un valor por defecto:
# si quien llama a la función no lo indica, se usa 0.
def validar_entero(valor: int, nombre: str, minimo: int = 0) -> int:
    """Revisa que el valor sea un entero dentro del rango permitido."""
    # Rechaza lo que no sea un número entero (por ejemplo 1.5 o un texto).
    if type(valor) is not int:
        raise ValueError(f"{nombre} debe ser un número entero.")
    if valor < minimo:
        raise ValueError(f"{nombre} no puede ser menor a {minimo}.")
    if valor > MAXIMO_NUMERO:
        raise ValueError(f"{nombre} es demasiado grande.")
    return valor


# Las cajas de texto de la pantalla siempre entregan texto ('50.000'). Esta función lo convierte en número (50000).
# Acepta puntos de miles y rechaza letras, decimales y números gigantes.
def texto_a_entero(texto: str, nombre: str) -> int:
    """Convierte lo escrito en pantalla a entero. Acepta puntos de miles: 50.000."""
    # strip() quita los espacios al inicio y al final.
    limpio = texto.strip().replace("$", "")
    # Si tiene formato de miles (50.000 o 1.234.567), se sacan los puntos.
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", limpio):
        limpio = limpio.replace(".", "")
    if not re.fullmatch(r"-?[0-9]+", limpio):
        raise ValueError(f"{nombre} debe ser un número entero.")
    if len(limpio) > 12:
        raise ValueError(f"{nombre} es demasiado grande.")
    # int() convierte un texto de dígitos en un número.
    return int(limpio)


# Muestra un monto como pesos chilenos: 12345 queda $12.345.
# {monto:,} escribe el número con comas de miles; después se cambian las comas por puntos.
def formato_clp(monto: int) -> str:
    """Muestra un monto en pesos chilenos: 12345 -> $12.345."""
    return f"${monto:,}".replace(",", ".")
