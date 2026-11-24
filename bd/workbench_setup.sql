-- =============================================================================
-- SCRIPT DE BASE DE DATOS PARA MYSQL WORKBENCH
-- Proyecto: La Caserita de las Camisetas
-- Carrera: Analista Programador (1er Semestre) - Desarrollo de Objetos
-- =============================================================================
-- Instrucciones para MySQL Workbench:
-- 1. Abre MySQL Workbench y conéctate a tu servidor local (Local instance MySQL80 / root).
-- 2. Ve al menú: File -> Open SQL Script... y selecciona este archivo.
-- 3. Presiona el botón del rayo (Execute) o presiona Ctrl + Shift + Enter.
-- 4. En el panel izquierdo "Navigator -> Schemas", haz clic derecho y "Refresh All".
--    ¡Verás la base de datos 'lacasetita' con todas sus tablas y datos cargados!
-- =============================================================================

-- 1. CREACIÓN Y SELECCIÓN DE LA BASE DE DATOS
CREATE DATABASE IF NOT EXISTS `lacasetita`
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE `lacasetita`;

-- 2. TABLA DE PRENDAS (Catálogo e Inventario)
-- Modela las 3 subclases de Prenda (Térmica, Estándar y Ropa Interior) en una sola tabla relacional.
CREATE TABLE IF NOT EXISTS `prendas` (
    `codigo` VARCHAR(20) NOT NULL,
    `tipo` VARCHAR(20) NOT NULL,
    `nombre` VARCHAR(100) NOT NULL,
    `talla` VARCHAR(5) NOT NULL,
    `precio_base` INT NOT NULL,
    `stock` INT NOT NULL,
    `tipo_cuello` VARCHAR(20) NULL,
    `nivel_termico` VARCHAR(20) NULL,
    `tipo_manga` VARCHAR(20) NULL,
    `tipo_elastico` VARCHAR(20) NULL,
    `ajuste` VARCHAR(20) NULL,
    PRIMARY KEY (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. TABLA DE CLIENTES
CREATE TABLE IF NOT EXISTS `clientes` (
    `rut` VARCHAR(12) NOT NULL,
    `nombre` VARCHAR(100) NOT NULL,
    `telefono` VARCHAR(20) NOT NULL,
    `correo` VARCHAR(120) NOT NULL,
    PRIMARY KEY (`rut`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. TABLA DE USUARIOS (Empleados: Administrador y Vendedor)
-- La contraseña se almacena de forma segura usando función de hash SHA-256 (64 caracteres hexadecimales).
CREATE TABLE IF NOT EXISTS `usuarios` (
    `rut` VARCHAR(12) NOT NULL,
    `usuario` VARCHAR(30) NOT NULL,
    `nombre` VARCHAR(100) NOT NULL,
    `rol` VARCHAR(20) NOT NULL,
    `clave_hash` CHAR(64) NOT NULL,
    PRIMARY KEY (`rut`),
    UNIQUE KEY `uk_usuarios_usuario` (`usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. TABLA DE VENTAS
-- Clave foránea hacia clientes. Si el cliente tiene compras, no se puede borrar de la base de datos.
CREATE TABLE IF NOT EXISTS `ventas` (
    `folio` INT NOT NULL,
    `fecha` DATETIME NOT NULL,
    `vendedor` VARCHAR(100) NOT NULL,
    `cliente_rut` VARCHAR(12) NOT NULL,
    `cliente_nombre` VARCHAR(100) NOT NULL,
    `descuento_cliente` INT NOT NULL,
    `estado` VARCHAR(12) NOT NULL,
    `medio_pago` VARCHAR(30) NOT NULL,
    `comprobante` VARCHAR(100) NULL,
    PRIMARY KEY (`folio`),
    CONSTRAINT `fk_ventas_cliente` FOREIGN KEY (`cliente_rut`)
        REFERENCES `clientes` (`rut`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. TABLA DE DETALLE DE VENTA (Líneas de la compra)
-- Relaciona cada venta con los productos vendidos (Composición 1 a Muchos).
CREATE TABLE IF NOT EXISTS `detalle_venta` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `folio` INT NOT NULL,
    `codigo` VARCHAR(20) NOT NULL,
    `descripcion` VARCHAR(150) NOT NULL,
    `cantidad` INT NOT NULL,
    `subtotal` INT NOT NULL,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_detalle_venta` FOREIGN KEY (`folio`)
        REFERENCES `ventas` (`folio`) ON DELETE RESTRICT,
    CONSTRAINT `fk_detalle_prenda` FOREIGN KEY (`codigo`)
        REFERENCES `prendas` (`codigo`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. TABLA DE INTENTOS DE LOGIN (Seguridad contra ataques de fuerza bruta)
CREATE TABLE IF NOT EXISTS `intentos_login` (
    `usuario` VARCHAR(30) NOT NULL,
    `fallidos` INT NOT NULL DEFAULT 0,
    `bloqueado_hasta` DOUBLE NOT NULL DEFAULT 0,
    PRIMARY KEY (`usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- DATOS INICIALES DE PRUEBA (INSERT IGNORE para no duplicar si ya existen)
-- =============================================================================

-- Prendas iniciales del catálogo
INSERT IGNORE INTO `prendas` (`codigo`, `tipo`, `nombre`, `talla`, `precio_base`, `stock`, `tipo_cuello`, `nivel_termico`, `tipo_manga`, `tipo_elastico`, `ajuste`) VALUES
('TER-001', 'Térmica', 'Beatle', 'M', 12000, 10, 'Tortuga', 'Alto', NULL, NULL, NULL),
('TER-002', 'Térmica', 'Camiseta de invierno', 'L', 10000, 8, 'Redondo', 'Medio', NULL, NULL, NULL),
('EST-001', 'Estándar', 'Polera básica', 'S', 5000, 20, NULL, NULL, 'Corta', NULL, NULL),
('EST-002', 'Estándar', 'Polera básica', 'L', 6000, 15, NULL, NULL, 'Larga', NULL, NULL),
('INT-001', 'Ropa Interior', 'Calzoncillo largo', 'M', 8000, 12, NULL, NULL, NULL, 'Ancho', 'Regular'),
('INT-002', 'Ropa Interior', 'Calzoncillo largo', 'XXL', 8000, 2, NULL, NULL, NULL, 'Ancho', 'Ceñido');

-- Clientes registrados iniciales
INSERT IGNORE INTO `clientes` (`rut`, `nombre`, `telefono`, `correo`) VALUES
('11.111.111-1', 'Juan Perez', '+56911223344', 'juan@correo.cl'),
('22.222.222-2', 'Maria Gonzalez', '+56988776655', 'maria@correo.cl');

-- Usuarios iniciales:
-- marisol / admin123 (Administrador)  -> Hash SHA-256 de 'admin123'
-- carlos / vende123  (Vendedor)       -> Hash SHA-256 de 'vende123'
INSERT IGNORE INTO `usuarios` (`rut`, `usuario`, `nombre`, `rol`, `clave_hash`) VALUES
('33.333.333-3', 'marisol', 'Marisol Mena', 'Administrador', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9'),
('44.444.444-4', 'carlos', 'Carlos Baeza', 'Vendedor', 'f6d4d5a9d18e52e519b7d8d2b270726b0147cb9e4722513fce01c6f49fc35ec1');

-- =============================================================================
-- CONSULTAS DE VERIFICACIÓN (Pruébalas en Workbench seleccionando y ejecutando)
-- =============================================================================
-- SELECT * FROM prendas;
-- SELECT * FROM clientes;
-- SELECT * FROM usuarios;
-- SELECT * FROM ventas;
-- SELECT * FROM detalle_venta;
