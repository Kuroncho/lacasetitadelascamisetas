-- Esquema de la base de datos de La Caserita de las Camisetas.
-- La aplicación ejecuta este archivo sola al iniciar (crea solo las tablas que falten).
-- Para usarlo a mano en phpMyAdmin: selecciona primero la base 'lacasetita' y luego pega este contenido en la pestaña SQL.
-- Funciona en MySQL y en MariaDB (XAMPP): InnoDB permite claves foráneas y transacciones; utf8mb4 permite tildes y ñ.

-- Prendas: una sola tabla para los 3 tipos. La columna 'tipo' indica la clase; las columnas propias
-- de cada tipo quedan en NULL cuando no corresponden (por ejemplo, una polera no tiene tipo_cuello).
CREATE TABLE IF NOT EXISTS prendas (
    codigo VARCHAR(20) NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    talla VARCHAR(5) NOT NULL,
    precio_base INT NOT NULL,
    stock INT NOT NULL,
    tipo_cuello VARCHAR(20) NULL,
    nivel_termico VARCHAR(20) NULL,
    tipo_manga VARCHAR(20) NULL,
    tipo_elastico VARCHAR(20) NULL,
    ajuste VARCHAR(20) NULL,
    PRIMARY KEY (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Clientes: el RUT los identifica.
CREATE TABLE IF NOT EXISTS clientes (
    rut VARCHAR(12) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    correo VARCHAR(120) NOT NULL,
    PRIMARY KEY (rut)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Empleados (administradores y vendedores). La clave se guarda encriptada (SHA-256 = 64 caracteres).
CREATE TABLE IF NOT EXISTS usuarios (
    rut VARCHAR(12) NOT NULL,
    usuario VARCHAR(30) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    rol VARCHAR(20) NOT NULL,
    clave_hash CHAR(64) NOT NULL,
    PRIMARY KEY (rut),
    UNIQUE KEY uk_usuarios_usuario (usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Ventas pagadas. La clave foránea impide guardar una venta de un cliente que no existe.
-- 'vendedor' y 'cliente_nombre' son copias: la boleta se mantiene igual aunque después cambien.
CREATE TABLE IF NOT EXISTS ventas (
    folio INT NOT NULL,
    fecha DATETIME NOT NULL,
    vendedor VARCHAR(100) NOT NULL,
    cliente_rut VARCHAR(12) NOT NULL,
    cliente_nombre VARCHAR(100) NOT NULL,
    descuento_cliente INT NOT NULL,
    estado VARCHAR(12) NOT NULL,
    medio_pago VARCHAR(30) NOT NULL,
    comprobante VARCHAR(100) NULL,
    PRIMARY KEY (folio),
    CONSTRAINT fk_ventas_cliente FOREIGN KEY (cliente_rut) REFERENCES clientes (rut) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Líneas de cada venta. Las claves foráneas impiden líneas de ventas o prendas que no existen.
CREATE TABLE IF NOT EXISTS detalle_venta (
    id INT NOT NULL AUTO_INCREMENT,
    folio INT NOT NULL,
    codigo VARCHAR(20) NOT NULL,
    descripcion VARCHAR(150) NOT NULL,
    cantidad INT NOT NULL,
    subtotal INT NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_detalle_venta FOREIGN KEY (folio) REFERENCES ventas (folio) ON DELETE RESTRICT,
    CONSTRAINT fk_detalle_prenda FOREIGN KEY (codigo) REFERENCES prendas (codigo) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Intentos fallidos de inicio de sesión (HU16). Sin clave foránea a 'usuarios' a propósito:
-- también se registran nombres que no existen, para no revelar qué usuarios hay.
-- 'bloqueado_hasta' son segundos desde 1970 (lo mismo que entrega time.time() en Python); 0 = sin bloqueo.
CREATE TABLE IF NOT EXISTS intentos_login (
    usuario VARCHAR(30) NOT NULL,
    fallidos INT NOT NULL DEFAULT 0,
    bloqueado_hasta DOUBLE NOT NULL DEFAULT 0,
    PRIMARY KEY (usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
