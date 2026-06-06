import pandas as pd
from sqlalchemy import create_engine, text
import os

DB_URL = os.getenv('MYSQL_URL', 'mysql+pymysql://analista:TalentoTech2024!@localhost:3306/trafico_medellin')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET_INCIDENTES = os.path.join(BASE_DIR, 'data', 'incidentes_limpios.parquet')

engine = create_engine(DB_URL)

with engine.connect() as conn:
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS incidentes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_incidente VARCHAR(50),
        fecha_incidente DATETIME,
        ubicacion VARCHAR(200),
        tipo_evento VARCHAR(100),
        gravedad VARCHAR(50),
        conteo_vehicular INT,
        velocidad_promedio DECIMAL(10,2),
        anio INT,
        INDEX idx_fecha_incidente (fecha_incidente),
        INDEX idx_tipo_evento (tipo_evento),
        INDEX idx_gravedad (gravedad),
        INDEX idx_ubicacion (ubicacion)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """))
    conn.execute(text("TRUNCATE TABLE incidentes"))
    conn.commit()

print("Leyendo incidentes_limpios.parquet...")
df = pd.read_parquet(PARQUET_INCIDENTES)
print(f"Registros: {len(df):,}")
print(f"Columnas: {list(df.columns)}")
print(f"Años: {sorted(df['anio'].unique())}")

df['fecha_incidente'] = pd.to_datetime(df['fecha_incidente'], errors='coerce')
df['conteo_vehicular'] = pd.to_numeric(df['conteo_vehicular'], errors='coerce').fillna(0).astype(int)
df['velocidad_promedio'] = pd.to_numeric(df['velocidad_promedio'], errors='coerce')

print("Cargando a MySQL...")
df.to_sql('incidentes', engine, if_exists='append', index=False, method='multi', chunksize=5000)

with engine.connect() as conn:
    r = conn.execute(text("SELECT COUNT(*) FROM incidentes"))
    print(f"\nTotal incidentes cargados: {r.fetchone()[0]:,}")
    r = conn.execute(text("SELECT anio, COUNT(*) FROM incidentes GROUP BY anio ORDER BY anio"))
    for row in r:
        print(f"  {row[0]}: {row[1]:,}")

print("\nCreando tabla zonas_criticas desde trafico...")
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS zonas_criticas"))
    conn.execute(text("""
        CREATE TABLE zonas_criticas AS
        SELECT
            corredor,
            comuna,
            COUNT(*) as total_registros,
            AVG(velocidad_kmh) as velocidad_promedio,
            AVG(intensidad_veh_h) as intensidad_promedio,
            AVG(ocupacion) as ocupacion_promedio
        FROM trafico
        GROUP BY corredor, comuna
    """))
    conn.execute(text("ALTER TABLE zonas_criticas ADD INDEX idx_corredor (corredor)"))
    r = conn.execute(text("SELECT COUNT(*) FROM zonas_criticas"))
    print(f"Zonas críticas creadas: {r.fetchone()[0]:,} registros")

print("\nVerificando tablas finales:")
with engine.connect() as conn:
    r = conn.execute(text("SHOW TABLES"))
    for row in r:
        print(f"  - {row[0]}")

print("OK!")
