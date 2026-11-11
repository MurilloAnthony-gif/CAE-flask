-- =====================================================================
--  Sistema CAE - Control de Asistencia de Empleados
--  Script de creación de la base de datos (MySQL 8)
--  Ejecutar completo en MySQL Workbench (rayo ⚡ "Execute all")
-- =====================================================================

CREATE DATABASE IF NOT EXISTS cae_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE cae_db;

-- Se borran en orden inverso por las claves foráneas
DROP TABLE IF EXISTS asistencias;
DROP TABLE IF EXISTS empleados;
DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS horarios;
DROP TABLE IF EXISTS cargos;
DROP TABLE IF EXISTS departamentos;

-- ---------------------------------------------------------------------
-- 1. departamentos: áreas de la empresa
-- ---------------------------------------------------------------------
CREATE TABLE departamentos (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(80)  NOT NULL UNIQUE,
    descripcion VARCHAR(255) NULL,
    activo      TINYINT(1)   NOT NULL DEFAULT 1
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 2. cargos: puestos de trabajo
-- ---------------------------------------------------------------------
CREATE TABLE cargos (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(80)   NOT NULL UNIQUE,
    descripcion  VARCHAR(255)  NULL,
    salario_base DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    activo       TINYINT(1)    NOT NULL DEFAULT 1
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3. horarios: jornada asignada a los empleados
--    dias_laborables: números separados por coma (1=Lunes ... 7=Domingo)
-- ---------------------------------------------------------------------
CREATE TABLE horarios (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(60) NOT NULL UNIQUE,
    hora_entrada    TIME        NOT NULL,
    hora_salida     TIME        NOT NULL,
    tolerancia_min  INT         NOT NULL DEFAULT 10,
    dias_laborables VARCHAR(20) NOT NULL DEFAULT '1,2,3,4,5',
    CONSTRAINT chk_horario_horas CHECK (hora_salida > hora_entrada),
    CONSTRAINT chk_tolerancia    CHECK (tolerancia_min >= 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 4. usuarios: acceso al sistema (administradores)
--    El usuario admin por defecto lo crea la app al iniciar (ver db.py),
--    porque la contraseña se guarda con hash generado en Python.
-- ---------------------------------------------------------------------
CREATE TABLE usuarios (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre        VARCHAR(100) NOT NULL,
    rol           ENUM('ADMIN','SUPERVISOR') NOT NULL DEFAULT 'ADMIN'
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 5. empleados: datos personales y laborales
--    pin_hash: PIN personal para el marcador (guardado con hash)
-- ---------------------------------------------------------------------
CREATE TABLE empleados (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    cedula          VARCHAR(10)  NOT NULL UNIQUE,
    nombres         VARCHAR(80)  NOT NULL,
    apellidos       VARCHAR(80)  NOT NULL,
    email           VARCHAR(120) NULL,
    telefono        VARCHAR(15)  NULL,
    fecha_ingreso   DATE         NOT NULL,
    pin_hash        VARCHAR(255) NULL,
    departamento_id INT NOT NULL,
    cargo_id        INT NOT NULL,
    horario_id      INT NOT NULL,
    activo          TINYINT(1)   NOT NULL DEFAULT 1,
    CONSTRAINT fk_empleado_departamento FOREIGN KEY (departamento_id)
        REFERENCES departamentos(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_empleado_cargo FOREIGN KEY (cargo_id)
        REFERENCES cargos(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_empleado_horario FOREIGN KEY (horario_id)
        REFERENCES horarios(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 6. asistencias: entradas, salidas y atrasos
--    metodo: PIN    -> marcó el empleado (hora del servidor)
--            AJUSTE -> corrección del admin (observacion obligatoria)
--            FACIAL -> reconocimiento facial (etapa 2)
--    registrado_por: NULL si marcó el empleado, id del admin si fue AJUSTE
-- ---------------------------------------------------------------------
CREATE TABLE asistencias (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    empleado_id    INT  NOT NULL,
    fecha          DATE NOT NULL,
    hora_entrada   TIME NULL,
    hora_salida    TIME NULL,
    minutos_atraso INT  NOT NULL DEFAULT 0,
    estado         ENUM('PUNTUAL','ATRASO') NULL,
    metodo         ENUM('PIN','AJUSTE','FACIAL') NOT NULL DEFAULT 'PIN',
    observacion    VARCHAR(255) NULL,
    registrado_por INT NULL,
    CONSTRAINT uq_asistencia_dia UNIQUE (empleado_id, fecha),
    CONSTRAINT fk_asistencia_empleado FOREIGN KEY (empleado_id)
        REFERENCES empleados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_asistencia_usuario FOREIGN KEY (registrado_por)
        REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- =====================================================================
--  Datos de prueba
-- =====================================================================
INSERT INTO departamentos (nombre, descripcion) VALUES
    ('Administración',  'Gestión general de la empresa'),
    ('Talento Humano',  'Gestión del personal'),
    ('Tecnología',      'Sistemas y soporte técnico'),
    ('Ventas',          'Atención y ventas a clientes');

INSERT INTO cargos (nombre, descripcion, salario_base) VALUES
    ('Gerente',       'Responsable del área',        1500.00),
    ('Analista',      'Análisis y control',           900.00),
    ('Desarrollador', 'Desarrollo de software',      1100.00),
    ('Asistente',     'Apoyo administrativo',         600.00);

INSERT INTO horarios (nombre, hora_entrada, hora_salida, tolerancia_min, dias_laborables) VALUES
    ('Matutino',   '08:00:00', '17:00:00', 10, '1,2,3,4,5'),
    ('Vespertino', '14:00:00', '22:00:00', 10, '1,2,3,4,5'),
    ('Fin de semana', '09:00:00', '15:00:00', 5, '6,7');

-- Empleados sin PIN todavía (se asigna desde el CRUD de empleados)
INSERT INTO empleados (cedula, nombres, apellidos, email, telefono, fecha_ingreso,
                       departamento_id, cargo_id, horario_id) VALUES
    ('1310000001', 'Juan Carlos', 'Pérez Zambrano', 'juan.perez@empresa.com',  '0991111111', '2024-03-01', 1, 1, 1),
    ('1310000002', 'María José',  'López Vera',     'maria.lopez@empresa.com', '0992222222', '2024-06-15', 3, 3, 1),
    ('1310000003', 'Carlos Andrés','Mendoza Cedeño', 'carlos.m@empresa.com',   '0993333333', '2025-01-10', 4, 4, 2);
