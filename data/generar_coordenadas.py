import pandas as pd
import numpy as np
from pyproj import Transformer
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET_PATH = os.path.join(BASE_DIR, 'data', 'trafico_medellin_unificado.parquet')
SALIDA = os.path.join(BASE_DIR, 'data', 'coordenadas_corredores.parquet')

transformer = Transformer.from_crs('EPSG:3116', 'EPSG:4326', always_xy=True)

def convertir_coordenadas(lat, lon):
    if pd.isna(lat) or pd.isna(lon) or lat == 0 or lon == 0:
        return None, None
    try:
        lon_wgs, lat_wgs = transformer.transform(float(lon), float(lat))
        if 6.0 <= lat_wgs <= 6.5 and -75.8 <= lon_wgs <= -75.3:
            return round(lat_wgs, 6), round(lon_wgs, 6)
    except:
        pass
    return None, None

COORD_SINTETICAS = {
    'El Poblado': (6.210, -75.565),
    'La Candelaria': (6.245, -75.570),
    'Laureles - Estadio': (6.250, -75.590),
    'Belen': (6.230, -75.600),
    'Americas': (6.235, -75.595),
    'Robledo': (6.270, -75.580),
    'Aranjuez': (6.270, -75.555),
    'Castilla': (6.280, -75.565),
    'Doce de Octubre': (6.290, -75.560),
    'Buenos Aires': (6.235, -75.545),
    'La America': (6.255, -75.600),
    'San Javier': (6.260, -75.615),
    'Villa Hermosa': (6.220, -75.540),
    'San Cristobal': (6.270, -75.630),
    'Popular': (6.300, -75.550),
    'Santa Cruz': (6.290, -75.545),
    'Manrique': (6.260, -75.540),
    'Guayabal': (6.210, -75.580),
    'Corregimientos': (6.300, -75.620),
    'Poblado': (6.210, -75.565),
    'Candelaria': (6.245, -75.570),
    'Laureles': (6.250, -75.590),
}

print("Leyendo parquet...")
df = pd.read_parquet(PARQUET_PATH, columns=['corredor', 'comuna', 'latitud', 'longitud'])
print(f"Total registros: {len(df):,}")

# Extraer combinaciones unicas corredor-comuna
print("Extrayendo combinaciones unicas...")
unicos = df.drop_duplicates(subset=['corredor', 'comuna']).copy()
print(f"Combinaciones unicas: {len(unicos)}")

# Convertir coordenadas existentes
print("Convirtiendo coordenadas EPSG:3116 -> WGS84...")
resultados = []
for _, row in unicos.iterrows():
    lat_wgs, lon_wgs = convertir_coordenadas(row['latitud'], row['longitud'])
    resultados.append({'corredor': row['corredor'], 'comuna': row['comuna'],
                       'latitud': lat_wgs, 'longitud': lon_wgs})

coord_df = pd.DataFrame(resultados)

# Asignar coordenadas sinteticas donde no se pudo convertir
sin_coord = coord_df['latitud'].isna()
print(f"Sin coordenadas validas: {sin_coord.sum():,}")

for idx in coord_df[sin_coord].index:
    comuna = coord_df.loc[idx, 'comuna']
    if pd.isna(comuna) or comuna == 'None' or comuna == '':
        continue
    for clave, (lat, lon) in COORD_SINTETICAS.items():
        if clave.lower() in comuna.lower():
            coord_df.loc[idx, 'latitud'] = lat
            coord_df.loc[idx, 'longitud'] = lon
            break

# Para los que aun quedan sin coordenadas, asignar un valor default por corredor
sin_coord = coord_df['latitud'].isna()
if sin_coord.any():
    # Agrupar por corredor y promediar coordenadas disponibles
    prom_corredor = coord_df[~coord_df['latitud'].isna()].groupby('corredor')[['latitud', 'longitud']].mean()
    for idx in coord_df[sin_coord].index:
        corr = coord_df.loc[idx, 'corredor']
        if corr in prom_corredor.index:
            coord_df.loc[idx, 'latitud'] = prom_corredor.loc[corr, 'latitud']
            coord_df.loc[idx, 'longitud'] = prom_corredor.loc[corr, 'longitud']

# Ultimo fallback: centro de Medellin
coord_df['latitud'] = coord_df['latitud'].fillna(6.245)
coord_df['longitud'] = coord_df['longitud'].fillna(-75.581)

print(f"Coordenadas finales: {coord_df['latitud'].notna().sum():,} de {len(coord_df)}")

coord_df.to_parquet(SALIDA, index=False)
print(f"Mapping guardado en: {SALIDA}")
print(f"Corredores con coordenadas: {coord_df['latitud'].notna().sum()}")
print("\nMuestra:")
print(coord_df.drop_duplicates(subset=['corredor']).head(10).to_string(index=False))
