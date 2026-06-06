  CREATE DATABASE IF NOT EXISTS trafico_medellin
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE trafico_medellin;

DROP TABLE IF EXISTS incidentes;
DROP TABLE IF EXISTS trafico;

CREATE TABLE trafico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    carril VARCHAR(100),
    fecha_trafico DATETIME,
    fecha DATE,
    hora INT,
    dia_semana VARCHAR(20),
    dia_num INT,
    mes_num INT,
    mes VARCHAR(20),
    anio INT,
    velocidad_kmh DECIMAL(10,2),
    corredor VARCHAR(100),
    sentido VARCHAR(10),
    operacion VARCHAR(30),
    intensidad_veh_h INT,
    categoria_1 INT,
    categoria_2 INT,
    categoria_3 INT,
    categoria_4 INT,
    ocupacion DECIMAL(10,2),
    tipo_subsistema VARCHAR(50),
    longitud DECIMAL(15,6),
    latitud DECIMAL(15,6),
    identificador_fv VARCHAR(10),
    comuna VARCHAR(100),
    codigo_comuna INT,
    nombre_comuna VARCHAR(100),
    periodo_dia VARCHAR(20),
    es_hora_pico BOOLEAN,
    indice_congestion DECIMAL(10,4),
    INDEX idx_fecha (fecha),
    INDEX idx_corredor (corredor),
    INDEX idx_comuna (comuna),
    INDEX idx_mes_anio (mes_num, anio),
    INDEX idx_hora (hora)
);

CREATE TABLE incidentes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha_incidente DATETIME,
    ubicacion VARCHAR(200),
    tipo_evento VARCHAR(100),
    gravedad VARCHAR(50),
    conteo_vehicular INT,
    velocidad_promedio DECIMAL(10,2),
    corredor VARCHAR(100),
    INDEX idx_fecha_incidente (fecha_incidente),
    INDEX idx_tipo_evento (tipo_evento),
    INDEX idx_gravedad (gravedad),
    INDEX idx_ubicacion (ubicacion)
);

CREATE TABLE zonas_criticas AS
SELECT
    corredor,
    comuna,
    COUNT(*) as total_registros,
    AVG(velocidad_kmh) as velocidad_promedio,
    AVG(intensidad_veh_h) as intensidad_promedio,
    AVG(ocupacion) as ocupacion_promedio
FROM trafico
GROUP BY corredor, comuna;

ALTER TABLE zonas_criticas ADD INDEX idx_corredor (corredor);
