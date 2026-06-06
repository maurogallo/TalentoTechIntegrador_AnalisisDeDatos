USE trafico_medellin;

-- ============================================================
-- 1. EXPLORACIÓN GENERAL
-- ============================================================

-- 1.1 Tráfico: resumen por año
SELECT anio, COUNT(*) as total_registros,
       ROUND(AVG(velocidad_kmh), 1) as velocidad_promedio,
       SUM(intensidad_veh_h) as total_vehiculos,
       ROUND(AVG(intensidad_veh_h), 0) as promedio_vehiculos_por_hora
FROM trafico
GROUP BY anio
ORDER BY anio;

-- 1.2 Incidentes: distribución por tipo de evento
SELECT tipo_evento, COUNT(*) as total,
       ROUND(AVG(conteo_vehicular), 0) as avg_vehiculos_afectados,
       ROUND(AVG(velocidad_promedio), 1) as avg_velocidad
FROM incidentes
GROUP BY tipo_evento
ORDER BY total DESC;

-- 1.3 Incidentes: distribución por gravedad
SELECT gravedad, COUNT(*) as total,
       ROUND(AVG(conteo_vehicular), 0) as avg_vehiculos_afectados
FROM incidentes
GROUP BY gravedad
ORDER BY FIELD(gravedad, 'Crítico', 'Moderado', 'Leve');

-- ============================================================
-- 2. KPIs DE CONGESTIÓN Y FLUJO
-- ============================================================

-- 2.1 KPI: Índice de Congestión por zona (tiempo con velocidad < 30 km/h)
SELECT comuna, corredor,
       COUNT(*) as total_registros,
       SUM(CASE WHEN velocidad_kmh < 30 THEN 1 ELSE 0 END) as registros_congestion,
       ROUND(SUM(CASE WHEN velocidad_kmh < 30 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as indice_congestion_pct,
       ROUND(AVG(velocidad_kmh), 1) as velocidad_promedio_kmh
FROM trafico
GROUP BY comuna, corredor
ORDER BY indice_congestion_pct DESC;

-- 2.2 KPI: Velocidad Promedio por hora del día
SELECT hora,
       ROUND(AVG(velocidad_kmh), 1) as velocidad_promedio,
       SUM(intensidad_veh_h) as total_vehiculos,
       COUNT(*) as registros
FROM trafico
GROUP BY hora
ORDER BY hora;

-- 2.3 KPI: Volumen Vehicular por día de la semana
SELECT dia_semana,
       SUM(intensidad_veh_h) as total_vehiculos,
       ROUND(AVG(intensidad_veh_h), 0) as promedio_diario,
       ROUND(AVG(velocidad_kmh), 1) as velocidad_promedio
FROM trafico
GROUP BY dia_semana
ORDER BY FIELD(dia_semana, 'Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo');

-- ============================================================
-- 3. KPI: IMPACTO TEMPORAL
-- ============================================================

-- 3.1 Pico Horario de Congestión
SELECT periodo_dia, hora,
       ROUND(AVG(velocidad_kmh), 1) as velocidad_promedio,
       ROUND(AVG(intensidad_veh_h), 0) as avg_vehiculos,
       COUNT(*) as registros
FROM trafico
GROUP BY periodo_dia, hora
ORDER BY avg_vehiculos DESC
LIMIT 10;

-- ============================================================
-- 4. KPI: INCIDENTES Y SEGURIDAD VIAL
-- ============================================================

-- 4.1 Tasa de Incidentes por Gravedad y Periodo
SELECT
    CASE
        WHEN HOUR(inc.fecha_incidente) BETWEEN 0 AND 5 THEN 'Madrugada'
        WHEN HOUR(inc.fecha_incidente) BETWEEN 6 AND 11 THEN 'Mañana'
        WHEN HOUR(inc.fecha_incidente) BETWEEN 12 AND 17 THEN 'Tarde'
        ELSE 'Noche'
    END as periodo,
    inc.gravedad,
    COUNT(*) as total_incidentes
FROM incidentes inc
GROUP BY periodo, inc.gravedad
ORDER BY FIELD(periodo, 'Madrugada', 'Mañana', 'Tarde', 'Noche'),
         FIELD(inc.gravedad, 'Crítico', 'Moderado', 'Leve');

-- 4.2 Top zonas con más incidentes
SELECT ubicacion, COUNT(*) as total_incidentes,
       ROUND(AVG(conteo_vehicular), 0) as avg_vehiculos_afectados,
       ROUND(AVG(velocidad_promedio), 1) as velocidad_promedio
FROM incidentes
GROUP BY ubicacion
ORDER BY total_incidentes DESC
LIMIT 15;

-- 4.3 Incidentes por mes del año
SELECT MONTH(fecha_incidente) as mes,
       COUNT(*) as total_incidentes,
       SUM(CASE WHEN gravedad = 'Crítico' THEN 1 ELSE 0 END) as criticos,
       SUM(CASE WHEN gravedad = 'Moderado' THEN 1 ELSE 0 END) as moderados,
       SUM(CASE WHEN gravedad = 'Leve' THEN 1 ELSE 0 END) as leves
FROM incidentes
GROUP BY mes
ORDER BY mes;

-- ============================================================
-- 5. CONSULTAS AVANZADAS
-- ============================================================

-- 5.1 JOIN: Relación entre incidentes y tráfico (por corredor)
SELECT t.comuna, t.corredor,
       ROUND(AVG(t.velocidad_kmh), 1) as velocidad_trafico,
       ROUND(AVG(t.intensidad_veh_h), 0) as volumen_trafico,
       COUNT(DISTINCT i.id) as total_incidentes,
       ROUND(AVG(i.conteo_vehicular), 0) as vehiculos_afectados_incidentes
FROM trafico t
LEFT JOIN incidentes i ON t.corredor = i.ubicacion
GROUP BY t.comuna, t.corredor
ORDER BY total_incidentes DESC;

-- 5.2 Subconsulta: Corredores con congestión por encima del promedio
SELECT corredor, comuna,
       ROUND(AVG(velocidad_kmh), 1) as velocidad_promedio,
       ROUND(AVG(intensidad_veh_h), 0) as volumen_promedio
FROM trafico
GROUP BY corredor, comuna
HAVING AVG(velocidad_kmh) < (
    SELECT AVG(velocidad_kmh) FROM trafico
)
ORDER BY velocidad_promedio ASC;

-- 5.3 Ventana: Días con mayor volumen vehicular por comuna
WITH ranking_diario AS (
    SELECT fecha, comuna, SUM(intensidad_veh_h) as volumen_diario,
           ROW_NUMBER() OVER (PARTITION BY comuna ORDER BY SUM(intensidad_veh_h) DESC) as rank_pos
    FROM trafico
    GROUP BY fecha, comuna
)
SELECT comuna, fecha, volumen_diario
FROM ranking_diario
WHERE rank_pos <= 3
ORDER BY comuna, rank_pos;

-- ============================================================
-- 6. VISTAS PARA EL DASHBOARD
-- ============================================================

CREATE OR REPLACE VIEW vw_resumen_diario AS
SELECT fecha, anio, mes, dia_semana,
       SUM(intensidad_veh_h) as total_vehiculos,
       ROUND(AVG(velocidad_kmh), 1) as velocidad_promedio,
       ROUND(AVG(CASE WHEN velocidad_kmh < 30 THEN 1 ELSE 0 END) * 100, 1) as pct_congestion
FROM trafico
GROUP BY fecha, anio, mes, dia_semana;

CREATE OR REPLACE VIEW vw_incidentes_por_zona AS
SELECT ubicacion,
       COUNT(*) as total_incidentes,
       SUM(CASE WHEN gravedad = 'Crítico' THEN 1 ELSE 0 END) as criticos,
       SUM(CASE WHEN gravedad = 'Moderado' THEN 1 ELSE 0 END) as moderados,
       SUM(CASE WHEN gravedad = 'Leve' THEN 1 ELSE 0 END) as leves,
       ROUND(AVG(conteo_vehicular), 0) as avg_vehiculos_afectados
FROM incidentes
GROUP BY ubicacion;

CREATE OR REPLACE VIEW vw_kpi_generales AS
SELECT
    (SELECT COUNT(*) FROM trafico) as total_registros_trafico,
    (SELECT COUNT(*) FROM incidentes) as total_incidentes,
    (SELECT ROUND(AVG(velocidad_kmh), 1) FROM trafico) as velocidad_promedio_general,
    (SELECT SUM(intensidad_veh_h) FROM trafico) as volumen_vehicular_total,
    (SELECT ROUND(AVG(conteo_vehicular), 0) FROM incidentes) as avg_vehiculos_afectados_incidentes;
