import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

st.set_page_config(page_title="Tráfico Medellín 2019-2022", layout="wide", page_icon="🚦")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET_PATH = os.path.join(BASE, 'data', 'trafico_medellin_unificado.parquet')
COORD_PATH = os.path.join(BASE, 'data', 'coordenadas_corredores.parquet')

@st.cache_resource
def conectar_mysql():
    from sqlalchemy import create_engine, text
    # Intentar obtener credenciales de secrets (para despliegue) o usar locales
    try:
        db_url = st.secrets["mysql"]["url"]
    except:
        db_url = os.getenv('MYSQL_URL', 'mysql+pymysql://analista:TalentoTech2024!@localhost:3306/trafico_medellin')
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        return engine
    except Exception:
        return None

@st.cache_resource(show_spinner="Cargando datos...")
def cargar_datos():
    # Prioridad 1: Archivo Parquet (Modo rápido y optimizado)
    if os.path.exists(PARQUET_PATH):
        df = pd.read_parquet(PARQUET_PATH)
        
        # FIX: Si el índice de congestión es 0 pero hay ocupación, lo calculamos al vuelo
        if 'indice_congestion' in df.columns and df['indice_congestion'].sum() == 0:
            if 'ocupacion' in df.columns and df['ocupacion'].max() > 0:
                max_o = df['ocupacion'].max()
                df['indice_congestion'] = (df['ocupacion'] / max_o).clip(0, 1)
                
        return df, 'parquet'
    
    # Prioridad 2: MySQL (Solo si no hay Parquet)
    engine = conectar_mysql()
    if engine:
        return engine, 'mysql'
    
    return None, None

@st.cache_data(show_spinner=False)
def query_mysql(_engine, sql):
    from sqlalchemy import text
    with _engine.connect() as conn:
        return pd.read_sql(text(sql), conn)

st.title("🚦 Análisis de Tráfico - Medellín 2019-2022")
st.markdown("Dashboard interactivo del flujo vehicular en la ciudad de Medellín")

con, modo = cargar_datos()
if con is None:
    st.error("No se pudieron cargar los datos. Verifica MySQL o los archivos locales.")
    st.stop()

if modo == 'mysql':
    def q(sql):
        return query_mysql(con, sql)
else:
    def q(sql):
        return con

try:
    if modo == 'mysql':
        kpi = q("SELECT COUNT(*) as total_reg, ROUND(AVG(velocidad_kmh),1) as vel_media, ROUND(AVG(intensidad_veh_h),0) as int_media, ROUND(AVG(indice_congestion)*100,1) as cong_media FROM trafico").iloc[0]
        years = q("SELECT DISTINCT anio FROM trafico ORDER BY anio")
        corredores = q("SELECT DISTINCT corredor FROM trafico WHERE corredor != '' AND corredor != 'Nan' ORDER BY corredor")
    else:
        kpi = {'total_reg': len(con), 'vel_media': con['velocidad_kmh'].mean(), 'int_media': con['intensidad_veh_h'].mean(), 'cong_media': con['indice_congestion'].mean()*100}
        years = pd.DataFrame({'anio': sorted(con['anio'].unique())})
        corredores = pd.DataFrame({'corredor': [c for c in con['corredor'].dropna().unique() if c not in ('', 'Nan')]})
except Exception as e:
    st.error(f"Error cargando datos: {e}")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Registros", f"{int(kpi['total_reg']):,}")
col2.metric("Velocidad Promedio", f"{kpi['vel_media']} km/h")
col3.metric("Intensidad Promedio", f"{int(kpi['int_media'])} veh/h")
col4.metric("Índice Congestión", f"{kpi['cong_media']}%")
st.markdown("---")

col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    sel_years = st.multiselect("Años", years['anio'].tolist(), default=years['anio'].tolist())
with col_f2:
    sel_corrs = st.multiselect("Corredores", corredores['corredor'].tolist(), default=[])
with col_f3:
    sel_per = st.selectbox("Periodo", ["Todos", "Madrugada", "Mañana", "Tarde", "Noche"])

def filtrar(sql_base):
    if modo == 'mysql':
        conds = []
        if sel_years: 
            conds.append(f"anio IN ({','.join([str(int(y)) for y in sel_years])})")
        if sel_corrs: 
            corrs_cleaned = ",".join([f"'{c.replace(chr(39), '')}'" for c in sel_corrs])
            conds.append(f"corredor IN ({corrs_cleaned})")
        if sel_per != "Todos": 
            conds.append(f"periodo_dia = '{sel_per.replace(chr(39), '')}'")
        where = " AND ".join(conds) if conds else "1=1"
        return query_mysql(con, sql_base.replace("{where}", where))
    else:
        mask = pd.Series(True, index=con.index)
        if sel_years: mask &= con['anio'].isin(sel_years)
        if sel_corrs: mask &= con['corredor'].isin(sel_corrs)
        if sel_per != "Todos": mask &= con['periodo_dia'] == sel_per
        return con[mask]

st.subheader("Velocidad Promedio por Hora del Día")
try:
    if modo == 'mysql':
        df_h = filtrar("SELECT hora, AVG(velocidad_kmh) as velocidad, AVG(intensidad_veh_h) as intensidad FROM trafico WHERE {where} GROUP BY hora ORDER BY hora")
    else:
        df_f = filtrar("")
        df_h = df_f.groupby('hora')[['velocidad_kmh', 'intensidad_veh_h']].mean().reset_index().rename(columns={'velocidad_kmh': 'velocidad', 'intensidad_veh_h': 'intensidad'})
    
    fig1 = px.line(df_h, x='hora', y='velocidad', markers=True, labels={'hora': 'Hora', 'velocidad': 'km/h'})
    fig1.add_scatter(x=df_h['hora'], y=df_h['intensidad']/df_h['intensidad'].max()*60, yaxis='y2', name='Intensidad (norm.)', line=dict(dash='dot', color='red'))
    fig1.update_layout(yaxis2=dict(overlaying='y', side='right', title=''), title="Velocidad e Intensidad por Hora")
    st.plotly_chart(fig1, width='stretch')
except Exception as e:
    st.error(f"Error en gráfico de velocidad: {e}")

st.subheader("Congestión por Corredor")
try:
    if modo == 'mysql':
        df_c = filtrar("""
            SELECT corredor, COUNT(*) as total,
                SUM(CASE WHEN velocidad_kmh < 20 THEN 1 ELSE 0 END) as congested,
                ROUND(AVG(velocidad_kmh),1) as vel_prom,
                ROUND(AVG(indice_congestion)*100,1) as idx_cong
            FROM trafico WHERE corredor != '' AND corredor != 'Nan' AND {where}
            GROUP BY corredor HAVING total > 100 ORDER BY idx_cong DESC LIMIT 15
        """)
    else:
        df_f = filtrar("")
        df_c = df_f[~df_f['corredor'].isin(['', 'Nan', 'None'])].groupby('corredor').agg(
            total=('velocidad_kmh', 'count'), congested=('velocidad_kmh', lambda x: (x<20).sum()),
            vel_prom=('velocidad_kmh', 'mean'), idx_cong=('indice_congestion', 'mean')
        ).reset_index()
        df_c['idx_cong'] = (df_c['idx_cong']*100).round(1)
        df_c = df_c[df_c['total']>100].sort_values('idx_cong', ascending=False).head(15)
    fig2 = px.bar(df_c, x='corredor', y='idx_cong', color='vel_prom',
                  color_continuous_scale='RdYlGn_r',
                  labels={'corredor': '', 'idx_cong': '% Congestión', 'vel_prom': 'km/h'})
    fig2.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig2, width='stretch')
except Exception as e:
    st.error(f"Error en congestión: {e}")

st.subheader("Intensidad: Hora vs Día de Semana")
try:
    orden = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
    if modo == 'mysql':
        df_hd = filtrar("""
            SELECT hora, dia_semana, AVG(intensidad_veh_h) as intensidad
            FROM trafico WHERE dia_semana IN ('Lunes','Martes','Miercoles','Jueves','Viernes','Sabado','Domingo') AND {where}
            GROUP BY hora, dia_semana ORDER BY hora
        """)
    else:
        df_f = filtrar("")
        # Aseguramos que la columna se llame 'intensidad' para que Plotly la encuentre
        df_hd = df_f[df_f['dia_semana'].isin(orden)].groupby(['hora', 'dia_semana'])['intensidad_veh_h'].mean().reset_index()
        df_hd = df_hd.rename(columns={'intensidad_veh_h': 'intensidad'})

    if df_hd.empty:
        st.warning("No hay datos para el heatmap con los filtros seleccionados.")
    else:
        df_hd['dia_semana'] = pd.Categorical(df_hd['dia_semana'], categories=orden, ordered=True)
        fig3 = px.density_heatmap(df_hd, x='hora', y='dia_semana', z='intensidad',
                                  color_continuous_scale='Viridis',
                                  labels={'hora': 'Hora', 'dia_semana': 'Día', 'intensidad': 'veh/h'})
        st.plotly_chart(fig3, width='stretch')
except Exception as e:
    st.error(f"Error en heatmap: {e}")

st.subheader("Evolución por Año")
try:
    if modo == 'mysql':
        df_y = q("SELECT anio, ROUND(AVG(velocidad_kmh),1) as velocidad, ROUND(AVG(intensidad_veh_h),0) as intensidad, ROUND(AVG(indice_congestion)*100,1) as congestion FROM trafico GROUP BY anio ORDER BY anio")
    else:
        df_f = filtrar("")
        df_y = df_f.groupby('anio').agg(velocidad=('velocidad_kmh', 'mean'), intensidad=('intensidad_veh_h', 'mean'), congestion=('indice_congestion', 'mean')).reset_index()
        df_y['velocidad'] = df_y['velocidad'].round(1)
        df_y['intensidad'] = df_y['intensidad'].round(0)
        df_y['congestion'] = (df_y['congestion']*100).round(1)
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(name='Velocidad (km/h)', x=df_y['anio'], y=df_y['velocidad']))
    fig4.add_trace(go.Scatter(name='Congestión (%)', x=df_y['anio'], y=df_y['congestion'], yaxis='y2', line=dict(color='red', width=3)))
    fig4.update_layout(yaxis=dict(title='km/h'), yaxis2=dict(overlaying='y', side='right', title='%'))
    st.plotly_chart(fig4, width='stretch')
except Exception as e:
    st.error(f"Error en evolución: {e}")

st.subheader("Comparativa Mensual (Estacionalidad)")
try:
    orden_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    if modo == 'mysql':
        df_est = filtrar("SELECT mes, anio, AVG(intensidad_veh_h) as intensidad, mes_num FROM trafico WHERE {where} GROUP BY mes, anio, mes_num ORDER BY mes_num")
    else:
        df_f = filtrar("")
        df_est = df_f.groupby(['mes', 'anio', 'mes_num'])['intensidad_veh_h'].mean().reset_index().rename(columns={'intensidad_veh_h': 'intensidad'})
        df_est = df_est.sort_values('mes_num')

    fig_est = px.line(df_est, x='mes', y='intensidad', color='anio', markers=True,
                      category_orders={"mes": orden_meses},
                      labels={'intensidad': 'Vehículos/h', 'mes': 'Mes', 'anio': 'Año'},
                      title="Evolución del Flujo Vehicular por Mes y Año")
    st.plotly_chart(fig_est, width='stretch')
except Exception as e:
    st.error(f"Error en estacionalidad: {e}")

st.subheader("📈 Pronóstico de Intensidad Vehicular (2023 - 2026)")
try:
    # 1. Preparar datos históricos mensuales
    if modo == 'mysql':
        df_p = q("SELECT anio, mes_num, AVG(intensidad_veh_h) as intensidad FROM trafico GROUP BY anio, mes_num ORDER BY anio, mes_num")
    else:
        df_p = con.groupby(['anio', 'mes_num'])['intensidad_veh_h'].mean().reset_index().rename(columns={'intensidad_veh_h': 'intensidad'})
    
    # Crear un índice de tiempo (meses transcurridos desde el inicio)
    df_p['t'] = (df_p['anio'] - df_p['anio'].min()) * 12 + df_p['mes_num']
    
    # Limpiar datos nulos o infinitos que causan 'nan' en la regresión
    df_p = df_p.dropna(subset=['t', 'intensidad'])
    df_p = df_p[np.isfinite(df_p['t']) & np.isfinite(df_p['intensidad'])]

    # 2. Calcular Regresión Lineal (y = mx + b)
    if len(df_p) > 1:
        m, b = np.polyfit(df_p['t'], df_p['intensidad'], 1)
    else:
        m, b = 0, 0
    
    # 3. Generar proyecciones hasta Diciembre 2026
    # Creamos un rango que incluye los meses históricos y 48 meses adicionales (años 2023, 2024, 2025 y 2026)
    t_futuro = np.arange(df_p['t'].min(), df_p['t'].max() + 49)
    predicciones = m * t_futuro + b
    
    # Crear DataFrame para el gráfico de pronóstico
    fechas_proyectadas = pd.date_range(start=f"{df_p['anio'].min()}-01-01", periods=len(t_futuro), freq='ME')
    df_forecast = pd.DataFrame({
        'Fecha': fechas_proyectadas,
        'Intensidad': predicciones,
        'Tipo': ['Histórico' if f.year <= df_p['anio'].max() else 'Pronóstico' for f in fechas_proyectadas]
    })

    fig_f = px.line(df_forecast, x='Fecha', y='Intensidad', color='Tipo',
                    line_dash='Tipo', color_discrete_map={'Histórico': '#636EFA', 'Pronóstico': '#EF553B'},
                    title="Tendencia Lineal Proyectada basada en datos 2019-2022")
    
    # Añadir los puntos reales para comparar
    df_p['Fecha'] = pd.to_datetime(df_p['anio'].astype(str) + '-' + df_p['mes_num'].replace(0, 1).astype(str) + '-01')
    fig_f.add_scatter(x=df_p['Fecha'], y=df_p['intensidad'], mode='markers', name='Datos Reales', 
                      marker=dict(color='#FFD700', size=7, line=dict(color='black', width=1)))
    
    # Mejorar el fondo y la visibilidad general (cambiar fondo gris por blanco)
    fig_f.update_layout(template="plotly_white", plot_bgcolor='white')

    st.plotly_chart(fig_f, width='stretch')
    st.info(f"**Fórmula del modelo:** Intensidad = {m:.2f} * (meses) + {b:.2f}. La tendencia indica un {'crecimiento' if m > 0 else 'decrecimiento'} mensual promedio de {abs(m):.2f} vehículos/h.")
except Exception as e:
    st.error(f"Error en pronóstico: {e}")

@st.cache_resource(show_spinner="Cargando coordenadas...")
def cargar_coordenadas():
    if os.path.exists(COORD_PATH):
        return pd.read_parquet(COORD_PATH)
    return None

coord_df = cargar_coordenadas()

# Cargar incidentes temprano para que el mapa pueda usarlos
INCIDENTES_PARQUET = os.path.join(BASE, 'data', 'incidentes_limpios.parquet')

@st.cache_resource(show_spinner="Cargando incidentes...")
def cargar_incidentes():
    if modo == 'mysql':
        try:
            df_inc = query_mysql(con, "SELECT * FROM incidentes ORDER BY fecha_incidente")
            return df_inc, 'mysql'
        except:
            pass
    if os.path.exists(INCIDENTES_PARQUET):
        df_inc = pd.read_parquet(INCIDENTES_PARQUET)
        return df_inc, 'parquet'
    return None, None

inc_con, inc_modo = cargar_incidentes()

st.subheader("📍 Mapa Interactivo de Medellín")
try:
    df_f = filtrar("")

    # Controles del mapa
    col_map_ctrl1, col_map_ctrl2, col_map_ctrl3, col_map_ctrl4 = st.columns(4)
    with col_map_ctrl1:
        color_metric = st.selectbox("Color por", ["velocidad", "intensidad", "ocupacion", "indice_congestion"],
                                    format_func=lambda x: {"velocidad": "Velocidad (km/h)", "intensidad": "Flujo (veh/h)",
                                                           "ocupacion": "Ocupación (%)", "indice_congestion": "Índice Congestión"}[x])
    with col_map_ctrl2:
        size_metric = st.selectbox("Tamaño por", ["intensidad", "velocidad", "ocupacion"],
                                   format_func=lambda x: {"intensidad": "Flujo (veh/h)", "velocidad": "Velocidad (km/h)",
                                                          "ocupacion": "Ocupación (%)"}[x])
    with col_map_ctrl3:
        map_periodo = st.selectbox("Periodo (mapa)", ["Todos", "Madrugada", "Mañana", "Tarde", "Noche"])
    with col_map_ctrl4:
        mostrar_incidentes = st.toggle("Mostrar incidentes", value=False)

    mask_map = pd.Series(True, index=df_f.index)
    if map_periodo != "Todos":
        mask_map &= df_f['periodo_dia'] == map_periodo
    df_map_base = df_f[mask_map]

    df_agg = df_map_base.groupby(['corredor', 'comuna'], as_index=False).agg(
        velocidad=('velocidad_kmh', 'mean'),
        intensidad=('intensidad_veh_h', 'mean'),
        ocupacion=('ocupacion', 'mean'),
        indice_congestion=('indice_congestion', 'mean')
    )

    if coord_df is not None:
        df_agg = df_agg.merge(coord_df, on=['corredor', 'comuna'], how='left')

    df_agg = df_agg.dropna(subset=['latitud', 'longitud'])
    df_agg = df_agg[df_agg['latitud'].between(6.0, 6.5) & df_agg['longitud'].between(-75.8, -75.3)]

    if df_agg.empty:
        st.warning("No hay coordenadas disponibles para los filtros actuales.")
    else:
        df_agg = df_agg.fillna(0)

        fig_map = px.scatter_map(
            df_agg, lat="latitud", lon="longitud",
            color=color_metric, size=size_metric,
            color_continuous_scale="RdYlGn" if color_metric == "velocidad" else "Viridis",
            size_max=18, zoom=11, map_style="open-street-map",
            hover_name="corredor",
            hover_data={c: ':.1f' for c in ['velocidad', 'intensidad', 'ocupacion', 'indice_congestion', 'comuna']},
            labels={'velocidad': 'km/h', 'intensidad': 'veh/h', 'ocupacion': '%', 'indice_congestion': ''},
            title=f"Color = {color_metric.replace('_',' ').title()} | Tamaño = {size_metric.replace('_',' ').title()}"
        )

        # Superponer incidentes si el toggle está activo
        if mostrar_incidentes and inc_con is not None and coord_df is not None:
            inc_map = inc_con.groupby('ubicacion').agg(
                total_incidentes=('id_incidente', 'count')
            ).reset_index()
            inc_map['ubicacion_lower'] = inc_map['ubicacion'].str.lower().str.strip()
            coord_inc = coord_df[['corredor', 'latitud', 'longitud']].drop_duplicates(subset='corredor').copy()
            coord_inc['corredor_lower'] = coord_inc['corredor'].str.lower().str.strip()
            inc_map = inc_map.merge(coord_inc, left_on='ubicacion_lower', right_on='corredor_lower', how='inner')
            inc_map = inc_map.dropna(subset=['latitud', 'longitud'])

            if not inc_map.empty:
                fig_map.add_trace(go.Scattermap(
                    lat=inc_map['latitud'], lon=inc_map['longitud'],
                    mode='markers', name='Incidentes',
                    marker=dict(size=inc_map['total_incidentes'] / inc_map['total_incidentes'].max() * 20 + 5,
                                color='red', opacity=0.6, symbol='x'),
                    hovertext=inc_map['ubicacion'],
                    hoverinfo='text'
                ))

        fig_map.update_layout(
            margin={"r": 0, "t": 40, "l": 0, "b": 0},
            map=dict(center=dict(lat=6.2442, lon=-75.5812)),
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )

        evento = st.plotly_chart(fig_map, width='stretch', on_select="rerun", key="mapa_interactivo")

        # Panel de detalle al hacer clic en un punto
        if evento and evento.selection and evento.selection.points:
            punto = evento.selection.points[0]
            corr_seleccionado = punto.get('hovertext', '')
            if corr_seleccionado:
                st.markdown(f"#### 📊 Detalle: {corr_seleccionado}")
                detalle = df_agg[df_agg['corredor'] == corr_seleccionado]
                if not detalle.empty:
                    r = detalle.iloc[0]
                    dc1, dc2, dc3, dc4 = st.columns(4)
                    dc1.metric("Velocidad", f"{r['velocidad']:.1f} km/h")
                    dc2.metric("Flujo", f"{r['intensidad']:.0f} veh/h")
                    dc3.metric("Ocupación", f"{r['ocupacion']:.1f}%")
                    dc4.metric("Comuna", r['comuna'])

                    # Serie temporal del corredor seleccionado
                    st.markdown(f"**Evolución horaria - {corr_seleccionado}**")
                    df_serie = df_map_base[df_map_base['corredor'] == corr_seleccionado].copy()
                    if not df_serie.empty:
                        serie = df_serie.groupby('hora')[['velocidad_kmh', 'intensidad_veh_h']].mean().reset_index()
                        fig_serie = go.Figure()
                        fig_serie.add_trace(go.Scatter(x=serie['hora'], y=serie['velocidad_kmh'],
                                                        name='Velocidad', line=dict(color='green')))
                        fig_serie.add_trace(go.Scatter(x=serie['hora'], y=serie['intensidad_veh_h'],
                                                        name='Flujo', yaxis='y2', line=dict(color='blue', dash='dot')))
                        fig_serie.update_layout(yaxis2=dict(overlaying='y', side='right'),
                                                height=250, margin=dict(l=0, r=0, t=0, b=0))
                        st.plotly_chart(fig_serie, width='stretch')

except Exception as e:
    st.error(f"Error en mapa: {e}")

st.subheader("Top Corredores por Volumen Vehicular")
try:
    if modo == 'mysql':
        df_v = filtrar("""
            SELECT corredor, SUM(intensidad_veh_h) as volumen_total, ROUND(AVG(velocidad_kmh),1) as velocidad
            FROM trafico WHERE corredor != '' AND corredor != 'Nan' AND {where}
            GROUP BY corredor ORDER BY volumen_total DESC LIMIT 10
        """)
    else:
        df_f = filtrar("")
        df_v = df_f[~df_f['corredor'].isin(['', 'Nan', 'None'])].groupby('corredor').agg(
            volumen_total=('intensidad_veh_h', 'sum'), velocidad=('velocidad_kmh', 'mean')
        ).reset_index().sort_values('volumen_total', ascending=False).head(10)
    fig5 = px.bar(df_v, x='corredor', y='volumen_total', color='velocidad',
                  color_continuous_scale='Blues',
                  labels={'corredor': '', 'volumen_total': 'Vehículos', 'velocidad': 'km/h'})
    fig5.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig5, width='stretch')
except Exception as e:
    st.error(f"Error en volumen: {e}")

st.markdown("---")
st.markdown("## 🚨 Incidentes de Tráfico")

if inc_con is not None:
    col_inc1, col_inc2, col_inc3, col_inc4 = st.columns(4)
    col_inc1.metric("Total Incidentes", f"{len(inc_con):,}")
    col_inc2.metric("Tipos Distintos", inc_con['tipo_evento'].nunique())
    col_inc3.metric("Críticos", f"{len(inc_con[inc_con['gravedad'] == 'Crítico']):,}" if 'Crítico' in inc_con['gravedad'].values else "0")
    col_inc4.metric("Años", f"{inc_con['anio'].min()} - {inc_con['anio'].max()}")

    col_inc_f1, col_inc_f2 = st.columns(2)
    with col_inc_f1:
        inc_sel_tipo = st.multiselect("Tipo de Evento", inc_con['tipo_evento'].unique(), default=[])
    with col_inc_f2:
        inc_sel_grav = st.multiselect("Gravedad", inc_con['gravedad'].unique(), default=[])

    inc_f = inc_con.copy()
    if inc_sel_tipo:
        inc_f = inc_f[inc_f['tipo_evento'].isin(inc_sel_tipo)]
    if inc_sel_grav:
        inc_f = inc_f[inc_f['gravedad'].isin(inc_sel_grav)]

    st.subheader("Incidentes por Tipo de Evento")
    try:
        inc_tipo = inc_f.groupby('tipo_evento').agg(total=('id_incidente', 'count'), vehiculos=('conteo_vehicular', 'mean')).reset_index()
        fig_inc1 = px.bar(inc_tipo, x='tipo_evento', y='total', color='vehiculos',
                          color_continuous_scale='Reds',
                          labels={'tipo_evento': '', 'total': 'Incidentes', 'vehiculos': 'Veh. promedio'})
        fig_inc1.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig_inc1, width='stretch')
    except Exception as e:
        st.error(f"Error: {e}")

    col_inc_ch1, col_inc_ch2 = st.columns(2)

    with col_inc_ch1:
        st.subheader("Distribución por Gravedad")
        try:
            inc_grav = inc_f.groupby('gravedad').agg(total=('id_incidente', 'count')).reset_index()
            fig_inc2 = px.pie(inc_grav, values='total', names='gravedad', color='gravedad',
                              color_discrete_map={'Crítico': '#EF553B', 'Moderado': '#FFA15A', 'Leve': '#00CC96'})
            st.plotly_chart(fig_inc2, width='stretch')
        except Exception as e:
            st.error(f"Error: {e}")

    with col_inc_ch2:
        st.subheader("Incidentes por Año y Gravedad")
        try:
            inc_avg = inc_f.groupby(['anio', 'gravedad']).agg(total=('id_incidente', 'count')).reset_index()
            fig_inc3 = px.bar(inc_avg, x='anio', y='total', color='gravedad', barmode='group',
                              color_discrete_map={'Crítico': '#EF553B', 'Moderado': '#FFA15A', 'Leve': '#00CC96'},
                              labels={'anio': 'Año', 'total': 'Incidentes', 'gravedad': ''})
            st.plotly_chart(fig_inc3, width='stretch')
        except Exception as e:
            st.error(f"Error: {e}")

    st.subheader("Top Ubicaciones con Más Incidentes")
    try:
        inc_ubi = inc_f.groupby('ubicacion').agg(total=('id_incidente', 'count'), vehiculos=('conteo_vehicular', 'mean')).reset_index().sort_values('total', ascending=False).head(15)
        fig_inc4 = px.bar(inc_ubi, x='ubicacion', y='total', color='vehiculos',
                          color_continuous_scale='Viridis',
                          labels={'ubicacion': '', 'total': 'Incidentes', 'vehiculos': 'Veh. afectados'})
        fig_inc4.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_inc4, width='stretch')
    except Exception as e:
        st.error(f"Error: {e}")

    st.subheader("📍 Mapa de Incidentes")
    try:
        if coord_df is not None:
            inc_ubi_agg = inc_f.groupby('ubicacion').agg(total=('id_incidente', 'count'), vehiculos=('conteo_vehicular', 'mean')).reset_index()
            inc_ubi_agg['ubicacion_lower'] = inc_ubi_agg['ubicacion'].str.lower().str.strip()
            coord_copy = coord_df[['corredor', 'latitud', 'longitud']].drop_duplicates(subset='corredor').copy()
            coord_copy['corredor_lower'] = coord_copy['corredor'].str.lower().str.strip()
            inc_map = inc_ubi_agg.merge(coord_copy, left_on='ubicacion_lower', right_on='corredor_lower', how='left')
            inc_map = inc_map.dropna(subset=['latitud', 'longitud'])

            if not inc_map.empty:
                fig_inc_map = px.scatter_map(inc_map, lat="latitud", lon="longitud",
                                                 size="total", color="vehiculos",
                                                 color_continuous_scale="RdYlGn_r", size_max=20, zoom=11,
                                                 map_style="open-street-map",
                                                 hover_name="ubicacion",
                                                 labels={'total': 'Incidentes', 'vehiculos': 'Veh. afectados'},
                                                 title="Incidentes: Tamaño = Frecuencia | Color = Vehículos afectados")
                fig_inc_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0},
                                          map=dict(center=dict(lat=6.2442, lon=-75.5812)))
                st.plotly_chart(fig_inc_map, width='stretch')
            else:
                st.info("No se pudieron geolocalizar las ubicaciones de incidentes.")
    except Exception as e:
        st.error(f"Error en mapa de incidentes: {e}")

    st.subheader("📊 Comparativa Tráfico vs Incidentes por Ubicación")
    try:
        if coord_df is not None:
            inc_por_corredor = inc_f.groupby('ubicacion').agg(
                total_incidentes=('id_incidente', 'count'),
                avg_vehiculos_afectados=('conteo_vehicular', 'mean')
            ).reset_index().rename(columns={'ubicacion': 'corredor'})

            trafico_por_corredor = df_agg[['corredor', 'intensidad', 'velocidad']].copy()

            cruce = inc_por_corredor.merge(trafico_por_corredor, on='corredor', how='inner')

            if not cruce.empty:
                fig_cruce = px.scatter(cruce, x='intensidad', y='total_incidentes',
                                       size='avg_vehiculos_afectados', color='velocidad',
                                       color_continuous_scale='RdYlGn_r',
                                       hover_name='corredor',
                                       labels={'intensidad': 'Flujo promedio (veh/h)', 'total_incidentes': 'Total incidentes',
                                               'velocidad': 'Velocidad (km/h)', 'avg_vehiculos_afectados': 'Veh. afectados'},
                                       title="Relación: Flujo Vehicular vs Incidentes por Corredor")
                st.plotly_chart(fig_cruce, width='stretch')
                st.caption("Cada punto es un corredor. Se espera que a mayor flujo, más incidentes.")
    except Exception as e:
        st.error(f"Error en comparativa: {e}")

    st.subheader("📥 Datos Filtrados")
    with st.expander("Ver datos de muestra - Tráfico"):
        try:
            if modo == 'mysql':
                df_raw = q("SELECT fecha, hora, corredor, velocidad_kmh, intensidad_veh_h, ocupacion, periodo_dia FROM trafico ORDER BY fecha DESC LIMIT 500")
            else:
                df_f = filtrar("")
                df_raw = df_f[['fecha', 'hora', 'corredor', 'velocidad_kmh', 'intensidad_veh_h', 'ocupacion', 'periodo_dia']].head(500)
            st.dataframe(df_raw, width='stretch')
        except Exception as e:
            st.error(f"Error: {e}")

    with st.expander("Ver datos de muestra - Incidentes"):
        st.dataframe(inc_f.head(500), width='stretch')

else:
    st.info("Datos de incidentes no disponibles (ni en MySQL ni en parquet local).")

st.markdown("---")
st.caption("Fuente: Secretaría de Movilidad de Medellín (2019-2022) | Dashboard analítico - Tráfico e Incidentes")
