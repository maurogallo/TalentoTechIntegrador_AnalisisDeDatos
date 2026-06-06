import pandas as pd
import numpy as np
import glob
import os
import gc
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

COLUMNAS_ESTANDAR = [
    'carril', 'fecha_trafico', 'fecha', 'hora', 'dia_semana', 'dia_num',
    'mes_num', 'mes', 'anio', 'velocidad_kmh', 'corredor', 'sentido',
    'operacion', 'intensidad_veh_h', 'categoria_1', 'categoria_2',
    'categoria_3', 'categoria_4', 'ocupacion', 'tipo_subsistema',
    'longitud', 'latitud', 'identificador_fv', 'comuna', 'codigo_comuna',
]


def procesar_archivo_sampled(ruta, anio, sample_pct=0.15):
    try:
        df = pd.read_excel(ruta, engine='calamine', dtype=str)
    except Exception:
        try:
            df = pd.read_excel(ruta, engine='openpyxl', dtype=str)
        except Exception:
            return None

    if df.empty:
        return None

    ncols = len(df.columns)
    n_esperadas = len(COLUMNAS_ESTANDAR)
    n_usable = min(ncols, n_esperadas)
    cols = COLUMNAS_ESTANDAR[:n_usable]
    df = df.iloc[:, :n_usable]
    df.columns = cols
    for c in COLUMNAS_ESTANDAR:
        if c not in df.columns:
            df[c] = np.nan
    df = df[COLUMNAS_ESTANDAR]

    # Sample to reduce memory
    df = df.sample(frac=sample_pct, random_state=42)

    for col in ['velocidad_kmh', 'intensidad_veh_h', 'ocupacion',
                'categoria_1', 'categoria_2', 'categoria_3', 'categoria_4',
                'codigo_comuna', 'longitud', 'latitud']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    for col in ['categoria_1', 'categoria_2', 'categoria_3', 'categoria_4']:
        df[col] = df[col].fillna(0).astype('int32')

    df['hora'] = pd.to_numeric(df['hora'], errors='coerce').fillna(0).astype('int32')
    df['anio'] = pd.to_numeric(df['anio'], errors='coerce').fillna(anio).astype('int32')
    df['dia_num'] = pd.to_numeric(df['dia_num'], errors='coerce').fillna(0).astype('int32')
    df['mes_num'] = pd.to_numeric(df['mes_num'], errors='coerce').fillna(0).astype('int32')

    df['fecha_trafico'] = pd.to_datetime(df['fecha_trafico'], errors='coerce')
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')

    for col in ['corredor', 'comuna', 'dia_semana', 'mes', 'carril']:
        df[col] = df[col].astype(str).str.strip().str.title()
    df['sentido'] = df['sentido'].astype(str).str.strip().str.upper()
    df['operacion'] = df['operacion'].astype(str).str.strip().str.lower()
    df['tipo_subsistema'] = df['tipo_subsistema'].astype(str).str.strip()

    df['periodo_dia'] = pd.cut(
        df['hora'], bins=[-1, 5, 11, 17, 23],
        labels=['Madrugada', 'Mañana', 'Tarde', 'Noche']
    ).astype(str)

    df['es_hora_pico'] = ((df['hora'] >= 6) & (df['hora'] <= 9)) | ((df['hora'] >= 17) & (df['hora'] <= 20))

    return df


def main():
    print("=" * 60)
    print("ETL TRÁFICO MEDELLÍN 2019-2022 (15% muestra)")
    print("=" * 60)

    # Detectar años automáticamente
    años_disponibles = sorted([int(d) for d in os.listdir(BASE_DIR) if d.isdigit() and os.path.isdir(os.path.join(BASE_DIR, d))])

    for anio in años_disponibles:
        base_anio = os.path.join(BASE_DIR, str(anio))
        archivos = sorted([
            os.path.join(base_anio, f) for f in os.listdir(base_anio)
            if f.lower().endswith('.xlsx') and not f.startswith('~$')
        ])
        print(f"\n--- {anio}: Detectados {len(archivos)} archivos ---")

        frames = []
        for i, archivo in enumerate(archivos):
            nombre = os.path.basename(archivo)
            df = procesar_archivo_sampled(archivo, anio, sample_pct=0.15)
            if df is not None and len(df) > 0:
                frames.append(df)
                print(f"  {nombre}: {len(df):,} reg")
            if (i+1) % 4 == 0:
                gc.collect()

        if not frames:
            continue

        df_anio = pd.concat(frames, ignore_index=True)
        max_ocup = df_anio['ocupacion'].quantile(0.95)
        df_anio['indice_congestion'] = (df_anio['ocupacion'] / max_ocup).clip(0, 1) if max_ocup > 0 else 0

        salida = os.path.join(DATA_DIR, f'trafico_{anio}.parquet')
        df_anio.to_parquet(salida, index=False, compression='snappy')
        print(f"  >> {anio}: {len(df_anio):,} registros -> {salida}")
        del df_anio, frames
        gc.collect()

    print("\n--- Unificando ---")
    todos = []
    for anio in años_disponibles:
        ruta = os.path.join(DATA_DIR, f'trafico_{anio}.parquet')
        if os.path.exists(ruta):
            df = pd.read_parquet(ruta)
            todos.append(df)
            print(f"  {anio}: {len(df):,} reg")

    df_final = pd.concat(todos, ignore_index=True)
    print(f"\nTOTAL: {len(df_final):,} registros")
    print(f"Años: {sorted(df_final['anio'].unique())}")
    print(f"Corredores ({df_final['corredor'].nunique()}):")
    for c in sorted(df_final['corredor'].dropna().unique()):
        print(f"  - {c}")

    salida = os.path.join(DATA_DIR, 'trafico_medellin_unificado.parquet')
    df_final.to_parquet(salida, index=False, compression='snappy')
    print(f"\nDataset final: {salida}")
    print(f"Tamaño: {os.path.getsize(salida)/1024/1024:.1f} MB")


if __name__ == '__main__':
    main()
