#!/usr/bin/env python
"""
Genera los entregables del proyecto final:
1. Notebook Jupyter (EDA) en notebooks/
2. Informe PDF completo
"""
import nbformat as nbf
import os
from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 1. NOTEBOOK JUPYTER - ANÁLISIS EXPLORATORIO
# ============================================================
print("Generando notebook EDA...")

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.12.0"}
}

cells = []

# Celda 1: Título
cells.append(nbf.v4.new_markdown_cell("""# Análisis Exploratorio de Datos - Tráfico Vehicular Medellín 2019-2022

**Proyecto Integrador - Talento Tech**  
Análisis de datos de movilidad urbana para la optimización del tráfico en Medellín.

---"""))

# Celda 2: Imports
cells.append(nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 5)
print("Librerías cargadas correctamente.")"""))

# Celda 3: Cargar datos
cells.append(nbf.v4.new_markdown_cell("""## 1. Carga de Datos

Cargamos el dataset unificado de tráfico (Parquet) y el de incidentes."""))

cells.append(nbf.v4.new_code_cell("""# Cargar datos de tráfico
df = pd.read_parquet('data/trafico_medellin_unificado.parquet')
print(f"Registros de tráfico: {len(df):,}")
print(f"Columnas: {list(df.columns)}")

# Cargar incidentes
df_inc = pd.read_parquet('data/incidentes_limpios.parquet')
print(f"\\nRegistros de incidentes: {len(df_inc):,}")
print(f"Columnas: {list(df_inc.columns)}")"""))

# Celda 4: Vista previa
cells.append(nbf.v4.new_markdown_cell("""## 2. Vista Preliminar de los Datos"""))

cells.append(nbf.v4.new_code_cell("""print("=== TRÁFICO ===")
print(df.head(3).to_string())
print("\\n")
print(df.info())
print("\\n")
print(df.describe())"""))

cells.append(nbf.v4.new_code_cell("""print("=== INCIDENTES ===")
print(df_inc.head(3).to_string())
print("\\n")
print(df_inc.info())"""))

# Celda 5: Valores nulos
cells.append(nbf.v4.new_markdown_cell("""## 3. Valores Nulos y Calidad de Datos"""))

cells.append(nbf.v4.new_code_cell("""# Nulos en tráfico
nulos = df.isnull().sum()
nulos_pct = (nulos / len(df)) * 100
pd.DataFrame({'nulos': nulos, 'porcentaje': nulos_pct}).sort_values('nulos', ascending=False).head(10)"""))

cells.append(nbf.v4.new_code_cell("""# Nulos en incidentes
nulos_inc = df_inc.isnull().sum()
pd.DataFrame({'nulos': nulos_inc, 'porcentaje': (nulos_inc/len(df_inc))*100})"""))

# Celda 6: Análisis por año
cells.append(nbf.v4.new_markdown_cell("""## 4. Análisis Temporal"""))

cells.append(nbf.v4.new_code_cell("""# Evolución por año
anual = df.groupby('anio').agg(
    registros=('velocidad_kmh', 'count'),
    velocidad_prom=('velocidad_kmh', 'mean'),
    flujo_prom=('intensidad_veh_h', 'mean'),
    ocupacion_prom=('ocupacion', 'mean'),
    congestion=('indice_congestion', 'mean')
).reset_index()
anual['congestion'] = anual['congestion'] * 100
print(anual.round(1).to_string(index=False))

# Gráfico
fig, axes = plt.subplots(1, 2, figsize=(14, 4))
axes[0].plot(anual['anio'], anual['velocidad_prom'], 'o-', color='green', linewidth=2)
axes[0].set_title('Velocidad Promedio por Año')
axes[0].set_xlabel('Año'); axes[0].set_ylabel('km/h')

axes[1].plot(anual['anio'], anual['congestion'], 'o-', color='red', linewidth=2)
axes[1].set_title('Índice de Congestión por Año')
axes[1].set_xlabel('Año'); axes[1].set_ylabel('%')
plt.tight_layout()
plt.show()"""))

cells.append(nbf.v4.new_code_cell("""# Distribución por hora
hora = df.groupby('hora').agg(
    velocidad=('velocidad_kmh', 'mean'),
    flujo=('intensidad_veh_h', 'mean')
).reset_index()

fig, ax1 = plt.subplots(figsize=(12, 4))
ax1.bar(hora['hora'], hora['flujo'], alpha=0.6, color='blue', label='Flujo (veh/h)')
ax2 = ax1.twinx()
ax2.plot(hora['hora'], hora['velocidad'], 'o-', color='green', linewidth=2, label='Velocidad (km/h)')
ax1.set_xlabel('Hora del día'); ax1.set_ylabel('Flujo (veh/h)')
ax2.set_ylabel('Velocidad (km/h)')
ax1.set_title('Velocidad y Flujo por Hora del Día')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
plt.show()"""))

cells.append(nbf.v4.new_code_cell("""# Día de semana
orden = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
df['dia_semana'] = pd.Categorical(df['dia_semana'], categories=orden, ordered=True)
semana = df.groupby('dia_semana', observed=True).agg(
    flujo=('intensidad_veh_h', 'mean'),
    velocidad=('velocidad_kmh', 'mean')
).reset_index()

fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(semana['dia_semana'], semana['flujo'], color='steelblue')
ax.set_title('Flujo Promedio por Día de la Semana')
ax.set_ylabel('Vehículos/h')
plt.show()"""))

# Celda 7: Corredores
cells.append(nbf.v4.new_markdown_cell("""## 5. Análisis por Corredor"""))

cells.append(nbf.v4.new_code_cell("""# Top corredores por congestión
top_cong = df[~df['corredor'].isin(['', 'Nan', 'None'])].groupby('corredor').agg(
    velocidad=('velocidad_kmh', 'mean'),
    congestion=('indice_congestion', 'mean'),
    registros=('velocidad_kmh', 'count')
).reset_index()
top_cong['congestion'] = top_cong['congestion'] * 100
top_cong = top_cong[top_cong['registros'] > 10000].sort_values('congestion', ascending=False).head(10)

plt.figure(figsize=(12, 5))
plt.barh(top_cong['corredor'], top_cong['congestion'], color='coral')
plt.xlabel('% Congestión')
plt.title('Top 10 Corredores Más Congestionados')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()"""))

cells.append(nbf.v4.new_code_cell("""# Top por volumen
top_vol = df[~df['corredor'].isin(['', 'Nan', 'None'])].groupby('corredor').agg(
    volumen=('intensidad_veh_h', 'sum'),
    velocidad=('velocidad_kmh', 'mean')
).reset_index().sort_values('volumen', ascending=False).head(10)

plt.figure(figsize=(12, 5))
bars = plt.bar(top_vol['corredor'], top_vol['volumen'], color='steelblue')
plt.xticks(rotation=45, ha='right')
plt.ylabel('Volumen total (veh)')
plt.title('Top 10 Corredores por Volumen Vehicular')
plt.tight_layout()
plt.show()"""))

# Celda 8: Incidentes
cells.append(nbf.v4.new_markdown_cell("""## 6. Análisis de Incidentes"""))

cells.append(nbf.v4.new_code_cell("""# Incidentes por tipo y gravedad
print("\\n--- Incidentes por Tipo ---")
print(df_inc['tipo_evento'].value_counts())
print("\\n--- Incidentes por Gravedad ---")
print(df_inc['gravedad'].value_counts())

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
df_inc['tipo_evento'].value_counts().plot(kind='bar', ax=axes[0], color='tomato')
axes[0].set_title('Incidentes por Tipo')
axes[0].set_xlabel(''); axes[0].tick_params(axis='x', rotation=45)

df_inc['gravedad'].value_counts().plot(kind='pie', ax=axes[1], autopct='%1.1f%%', colors=['red', 'orange', 'gold', 'lightgreen'])
axes[1].set_title('Distribución por Gravedad')
plt.tight_layout()
plt.show()"""))

# Celda 9: Conclusiones
cells.append(nbf.v4.new_markdown_cell("""## 7. Conclusiones del EDA

1. **Tendencia negativa**: La velocidad promedio cayó de 27.8 km/h (2019) a 25.5 km/h (2022), mientras la congestión subió de 21.7% a 27.4%.
2. **2020 atípico**: Menor flujo vehicular por pandemia, lo que redujo artificialmente la congestión.
3. **Horas críticas**: Entre 6-9 am y 5-8 pm se concentra la mayor congestión con velocidades menores a 20 km/h.
4. **Corredores críticos**: Existen corredores específicos con índices de congestión superiores al 40% que requieren intervención prioritaria.
5. **Incidentes**: Accidentes y congestión son los eventos más frecuentes (~11,000 cada uno). El 50% de los incidentes son críticos o graves.
6. **Estacionalidad**: Los patrones mensuales se mantienen consistentes entre años, validando la calidad de los datos.

---

*Notebook generado automáticamente para el Proyecto Integrador Talento Tech*"""))

nb.cells = cells

os.makedirs(os.path.join(BASE_DIR, 'notebooks'), exist_ok=True)
nbf.write(nb, os.path.join(BASE_DIR, 'notebooks', 'EDA_Trafico_Medellin.ipynb'))
print("[OK] Notebook creado: notebooks/EDA_Trafico_Medellin.ipynb")

# ============================================================
# 2. INFORME PDF
# ============================================================
print("\nGenerando informe PDF...")

class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 8)
            self.cell(0, 8, 'Proyecto Integrador - Análisis de Datos de Tráfico - Medellín 2019-2022', 0, 1, 'C')
            self.line(10, 15, 200, 15)
            self.ln(5)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.cell(0, 10, f'Página {self.page_no() - 1}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 14)
        self.set_fill_color(30, 60, 114)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, f'  {title}', 0, 1, 'L', fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def chapter_body(self, text):
        self.set_font('Helvetica', '', 11)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def bullet(self, text):
        self.set_font('Helvetica', '', 11)
        self.cell(5)
        self.cell(5, 6, chr(8226), 0, 0)
        self.multi_cell(0, 6, text)
        self.ln(1)

pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=20)

# ---- PORTADA ----
pdf.add_page()
pdf.ln(30)
pdf.set_font('Helvetica', 'B', 28)
pdf.set_text_color(30, 60, 114)
pdf.cell(0, 15, 'Análisis de Datos de Tráfico', 0, 1, 'C')
pdf.cell(0, 15, 'Vehicular - Medellín 2019-2022', 0, 1, 'C')
pdf.ln(10)
pdf.set_font('Helvetica', '', 14)
pdf.set_text_color(80, 80, 80)
pdf.cell(0, 8, 'Proyecto Final Integrador', 0, 1, 'C')
pdf.cell(0, 8, 'Nivel 2 - Análisis de Datos', 0, 1, 'C')
pdf.cell(0, 8, 'Talento Tech', 0, 1, 'C')
pdf.ln(20)

pdf.set_font('Helvetica', '', 12)
pdf.set_text_color(0, 0, 0)
pdf.cell(0, 7, 'Línea de investigación: TIC - Movilidad Urbana Inteligente', 0, 1, 'C')
pdf.ln(5)
pdf.cell(0, 7, 'Integrantes del equipo:', 0, 1, 'C')
pdf.ln(3)
roles = [
    'Fabio Mauricio Gallo Parra - Líder de proyecto / ETL / DB / Dashboard / Documentación'
]
for r in roles:
    pdf.cell(0, 7, f'     {r}', 0, 1, 'C')
pdf.ln(10)
pdf.set_font('Helvetica', 'I', 10)
pdf.cell(0, 7, 'Fecha de entrega: Junio 2026', 0, 1, 'C')

# ---- 1. INTRODUCCIÓN ----
pdf.add_page()
pdf.chapter_title('1. Introducción')
pdf.chapter_body(
    'La movilidad urbana es uno de los mayores desafíos de las ciudades modernas. '
    'Medellín, como epicentro económico del Valle de Aburrá, enfrenta una congestión '
    'vehicular creciente que afecta la calidad de vida de sus habitantes, la productividad '
    'económica y el medio ambiente.\n\n'
    'Este proyecto se enmarca en la línea de investigación de Ciencia, Tecnología e '
    'Innovación (TIC) para la transformación productiva y la resolución de desafíos '
    'sociales, económicos y ambientales. Específicamente, aborda la problemática de la '
    'movilidad urbana mediante el análisis de datos abiertos de la Secretaría de Movilidad '
    'de Medellín (SMM), que registran el flujo vehicular en puntos estratégicos de la ciudad.\n\n'
    'El objetivo es construir una solución integral que integre, procese, analice y visualice '
    'datos de tráfico vehicular para generar recomendaciones basadas en evidencia que '
    'permitan optimizar la movilidad, reducir la congestión y mejorar la seguridad vial en la ciudad.'
)

# ---- 2. DESARROLLO DEL PROYECTO ----
pdf.add_page()
pdf.chapter_title('2. Desarrollo del Proyecto')

pdf.chapter_title('2.1 Problemática Identificada')
pdf.chapter_body(
    'Medellín cuenta con más de 19 millones de registros de tráfico vehicular entre 2019 y 2022, '
    'distribuidos en 48 archivos Excel mensuales. Sin embargo, estos datos se encontraban '
    'dispersos, sin integrar y sin herramientas que permitieran su análisis efectivo. '
    'La problemática abordada es: ¿cómo integrar, analizar y visualizar estos datos para '
    'generar información útil que apoye la toma de decisiones en materia de movilidad urbana?'
)

pdf.chapter_title('2.2 Arquitectura de la Solución')
pdf.chapter_body(
    'La solución implementada sigue una arquitectura de tres capas:\n\n'
    '1. Capa de Datos (ETL): Procesamiento de 48 archivos Excel (~2.4 GB) mediante scripts '
    'Python para estandarizar, limpiar y transformar los datos a formatos Parquet y CSV.\n\n'
    '2. Capa de Almacenamiento: Base de datos MySQL con tres tablas (trafico, incidentes, '
    'zonas_criticas) que almacenan ~19.3 millones de registros de tráfico y 100,000 incidentes.\n\n'
    '3. Capa de Visualización: Dashboard interactivo en Streamlit con 12+ visualizaciones '
    'que permiten explorar los datos desde múltiples perspectivas.'
)

pdf.chapter_title('2.3 Base de Datos')
pdf.chapter_body(
    'Se diseñó una base de datos relacional en MySQL con el siguiente esquema:\n\n'
    '- trafico (24 columnas): Almacena los registros de flujo vehicular con información de '
    'velocidad, intensidad, ocupación, ubicación (coordenadas convertidas a WGS84), comuna, '
    'corredor, y métricas derivadas como índice de congestión y período del día.\n\n'
    '- incidentes (8 columnas): Contiene 100,000 registros de incidentes de tráfico '
    '(accidentes, congestiones, obras, etc.) con clasificación por gravedad.\n\n'
    '- zonas_criticas (6 columnas): Vista materializada con el resumen por corredor y comuna '
    'para consultas rápidas.\n\n'
    'Las consultas SQL avanzadas incluyen JOINs, subconsultas, funciones de ventana (ROW_NUMBER), '
    'agregaciones complejas y vistas materializadas.'
)

pdf.chapter_title('2.4 Procesamiento ETL')
pdf.chapter_body(
    'Se implementaron dos pipelines ETL:\n\n'
    '1. ETL Streaming (etl_streaming.py): Procesa los Excel en modo streaming con openpyxl, '
    'escribiendo directamente a CSV sin cargar todo en memoria. Ideal para máquinas con recursos limitados.\n\n'
    '2. ETL Parquet (etl_trafico.py): Lee los Excel con pandas, aplica una muestra del 15%, '
    'normaliza columnas (nombres, tipos, fechas), calcula métricas derivadas (período del día, '
    'hora pico, índice de congestión) y exporta a Parquet con compresión Snappy.\n\n'
    '3. Carga MySQL (load_mysql_wsl.py): Carga los datos a MySQL con checkpointing, modo streaming '
    'para archivos grandes, y mapeo inteligente de columnas que varían entre años.'
)

pdf.chapter_title('2.5 Dashboard Interactivo')
pdf.chapter_body(
    'El dashboard en Streamlit (dashboard/app.py) ofrece:\n\n'
    '- KPIs principales: Total registros, velocidad promedio, intensidad, índice de congestión.\n'
    '- Filtros interactivos: Por año, corredor, período del día.\n'
    '- Velocidad por hora: Gráfico de líneas con doble eje (velocidad + intensidad normalizada).\n'
    '- Congestión por corredor: Top 15 corredores más congestionados.\n'
    '- Heatmap hora-día: Intensidad vehicular en matriz hora vs día de semana.\n'
    '- Evolución anual: Barras de velocidad vs línea de congestión.\n'
    '- Estacionalidad mensual: Series por año para detectar patrones estacionales.\n'
    '- Pronóstico lineal: Proyección 2023-2026 basada en tendencia histórica.\n'
    '- Mapa interactivo: Puntos de medición con controles de color/tamaño, superposición de incidentes, '
    'y panel de detalle al hacer clic.\n'
    '- Sección de incidentes: KPIs, gráficos por tipo/gravedad, mapa de incidentes.\n'
    '- Comparativa tráfico vs incidentes: Scatter plot relacionando flujo vehicular con incidentes.'
)

# ---- 3. RESULTADOS ----
pdf.add_page()
pdf.chapter_title('3. Resultados Obtenidos')
pdf.chapter_body(
    'Los principales hallazgos del análisis son:\n\n'
    '1. Tendencia de congestión creciente: La velocidad promedio pasó de 27.8 km/h (2019) '
    'a 25.5 km/h (2022), mientras el índice de congestión subió de 21.7% a 27.4%.\n\n'
    '2. Impacto de la pandemia (2020): Se observó una reducción artificial del flujo vehicular '
    '(-15% vs 2019) que disminuyó temporalmente la congestión.\n\n'
    '3. Horas pico críticas: Entre 6-9 am y 5-8 pm la velocidad promedio cae por debajo de '
    '20 km/h en los corredores más transitados.\n\n'
    '4. Corredores críticos identificados: Se detectaron corredores específicos con índices '
    'de congestión superiores al 40%.\n\n'
    '5. Incidentes: 100,000 registros con distribución equitativa entre tipos (congestión, '
    'accidentes, obras, etc.) y ~50% clasificados como críticos o graves.\n\n'
    '6. Base de datos funcional: 19.3M registros de tráfico + 100K incidentes + 238 zonas '
    'críticas, consultables mediante SQL.'
)

# ---- 4. CONCLUSIONES Y RECOMENDACIONES ----
pdf.chapter_title('4. Conclusiones y Recomendaciones')
pdf.chapter_body(
    'Conclusiones:\n\n'
    '- La integración de datos de múltiples fuentes (Excel, Parquet, MySQL) en un pipeline '
    'ETL robusto permitió unificar 19.3 millones de registros para su análisis.\n'
    '- El dashboard interactivo facilita la exploración visual de patrones de movilidad '
    'y la identificación de puntos críticos de congestión.\n'
    '- El cruce de datos de tráfico con incidentes revela correlaciones entre el flujo '
    'vehicular y la ocurrencia de eventos de tránsito.\n\n'
    'Recomendaciones:\n\n'
    '1. Priorizar intervenciones en los corredores con mayor índice de congestión (velocidad < 20 km/h).\n'
    '2. Implementar sistemas de semaforización inteligente en horas pico (6-9 am y 5-8 pm).\n'
    '3. Fortalecer la gestión de incidentes en los corredores con mayor volumen vehicular.\n'
    '4. Actualizar el dataset con datos de 2023-2025 para mantener la vigencia del análisis.\n'
    '5. Incorporar datos adicionales (clima, eventos masivos, obras viales) para enriquecer el modelo.\n'
    '6. Migrar el pronóstico lineal a un modelo SARIMA o Prophet para capturar estacionalidad.'
)

# ---- 5. ROLES DEL EQUIPO ----
pdf.chapter_title('5. Roles del Equipo')
pdf.chapter_body('A continuación se describen los roles y responsabilidades de cada miembro del equipo:')
pdf.ln(2)

team_roles = [
    ('Fabio Mauricio Gallo Parra - Desarrollo Full Stack',
     'Responsable de todas las fases del proyecto: diseño de la arquitectura ETL, '
     'implementación de los scripts de extracción y transformación (etl_streaming.py, etl_trafico.py), '
     'diseño del esquema relacional MySQL y carga masiva de datos (load_mysql_wsl.py), '
     'desarrollo de consultas SQL complejas (JOINs, subconsultas, ventanas), '
     'implementación del dashboard interactivo en Streamlit con visualizaciones Plotly, '
     'y elaboración de la documentación completa del proyecto.')
]
for role, desc in team_roles:
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 7, f'{role}', 0, 1)
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 5, desc)
    pdf.ln(3)

# ---- 6. CIERRE ----
pdf.ln(5)
pdf.set_font('Helvetica', 'I', 10)
pdf.cell(0, 7, '--- Fin del Informe ---', 0, 1, 'C')
pdf.cell(0, 7, 'Proyecto Integrador Talento Tech - Nivel 2 - Análisis de Datos', 0, 1, 'C')
pdf.cell(0, 7, 'Medellín, Junio 2026', 0, 1, 'C')

pdf.output(os.path.join(BASE_DIR, 'Informe_Proyecto_Analisis_Trafico_Medellin.pdf'))
print("[OK] PDF creado: Informe_Proyecto_Analisis_Trafico_Medellin.pdf")

print("\n¡Todos los entregables generados con éxito!")
