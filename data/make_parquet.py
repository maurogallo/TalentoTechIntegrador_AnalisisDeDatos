import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sqlalchemy import create_engine, text
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, 'data', 'trafico_medellin_unificado.parquet')

DB_URL = os.getenv('MYSQL_URL', 'mysql+pymysql://analista:TalentoTech2024!@localhost:3306/trafico_medellin')
engine = create_engine(DB_URL)

def optimizar_tipos(df):
    """Reduce el peso del DataFrame optimizando tipos numéricos."""
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')
    for col in df.select_dtypes(include=['int64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')
    return df

def exportar_a_parquet_robusto(sample_fraction=1.0):
    mode_text = "completa" if sample_fraction >= 1.0 else f"muestreada ({sample_fraction*100:.0f}%)"
    print(f"🚀 Iniciando exportación {mode_text} (~19.3M de registros base)...")
    
    with engine.connect() as conn:
        # Excluimos la columna 'id' de MySQL ya que no aporta al análisis y ahorramos espacio
        columnas = "carril, fecha_trafico, fecha, hora, dia_semana, dia_num, mes_num, mes, anio, velocidad_kmh, corredor, sentido, operacion, intensidad_veh_h, ocupacion, tipo_subsistema, longitud, latitud, identificador_fv, comuna, codigo_comuna, periodo_dia, es_hora_pico, indice_congestion"
        
        where_clause = ""
        if sample_fraction < 1.0:
            # Usamos el ID para un muestreo eficiente (ej: 0.2 -> cada 5 registros)
            divisor = int(1 / sample_fraction)
            where_clause = f" WHERE id % {divisor} = 0"

        # Calculamos el total real de filas a exportar para que la barra de progreso sea exacta
        count_query = text(f"SELECT COUNT(*) FROM trafico{where_clause}")
        expected_total = conn.execute(count_query).scalar()

        query = text(f"SELECT {columnas} FROM trafico{where_clause}")
        
        # Reducimos el chunksize para mayor estabilidad en equipos con RAM limitada
        chunks = pd.read_sql(query, conn, chunksize=200000)
        
        writer = None
        total_rows = 0

        for i, chunk in enumerate(chunks):
            # Optimización de tipos antes de convertir a Arrow
            chunk = optimizar_tipos(chunk)
            table = pa.Table.from_pandas(chunk, preserve_index=False)
            
            if writer is None:
                writer = pq.ParquetWriter(OUTPUT_PATH, table.schema, compression='snappy')
            
            writer.write_table(table)
            total_rows += len(chunk)
            
            # Feedback visual de progreso
            progreso = (total_rows / expected_total) * 100 if expected_total > 0 else 0
            print(f"  [OK] Lote {i+1:02d} | Acumulado: {total_rows:10,} | Progreso: {progreso:6.2f}%")
        
        if writer:
            writer.close()
            
    print(f"\n¡Éxito! Archivo generado en: {OUTPUT_PATH}")
    print(f"Total final exportado: {total_rows:,} registros.")

if __name__ == "__main__":
    # Recomendación: usa 0.2 (20%) para un balance ideal entre precisión y velocidad.
    # Si sigue fallando, prueba con 0.1 (10%).
    exportar_a_parquet_robusto(sample_fraction=0.2)
