# Arquitectura del Proyecto - Analisis de Trafico Medellin 2019-2022

```mermaid
flowchart LR
    subgraph Fuentes["Fuentes de Datos"]
        EXCEL2019["2019 - 12 archivos Excel"]
        EXCEL2020["2020 - 12 archivos Excel"]
        EXCEL2021["2021 - 10 archivos Excel"]
        EXCEL2022["2022 - 12 archivos Excel"]
        EXCEL_INC["Incidentes - 1 archivo XLS"]
    end

    subgraph ETL["Capa ETL - Procesamiento"]
        S1["etl_streaming.py - Excel a CSV"]
        S2["etl_trafico.py - Excel a Parquet"]
        S3["load_mysql_wsl.py - Excel a MySQL"]
        S4["generar_coordenadas.py - Conversion WGS84"]
        S5["cargar_incidentes.py - Parquet a MySQL"]
    end

    subgraph Storage["Capa de Almacenamiento"]
        CSV["Archivos CSV - 1.2 GB"]
        PARQUET["Parquet unificado - 16.77 MB"]
        MYSQL[("MySQL - trafico_medellin")]
        COORD["Coordenadas WGS84 - 250 ubicaciones"]
    end

    subgraph Dashboard["Capa de Visualizacion"]
        STREAMLIT["Streamlit (puerto 8501)"]
        GRAFICOS["12 graficos Plotly interactivos"]
        MAPA["Mapa OpenStreetMap con incidentes"]
        FILTROS["Filtros: ano, corredor, periodo"]
    end

    subgraph Entregables["Entregables del Proyecto"]
        PDF["Informe PDF"]
        NB["Notebook Jupyter EDA"]
        SQL["consultas_analiticas.sql"]
        DASH["Dashboard app.py"]
    end

    EXCEL2019 --> S1 & S2 & S3
    EXCEL2020 --> S1 & S2 & S3
    EXCEL2021 --> S1 & S2 & S3
    EXCEL2022 --> S1 & S2 & S3
    EXCEL_INC --> S5

    S1 --> CSV
    S2 --> PARQUET
    S3 --> MYSQL
    S4 --> COORD
    S5 --> MYSQL

    PARQUET --> STREAMLIT
    MYSQL -.->|fallback| STREAMLIT
    COORD --> STREAMLIT

    STREAMLIT --> GRAFICOS & MAPA & FILTROS
    PARQUET --> NB
    MYSQL --> SQL
    STREAMLIT --> DASH

    style Fuentes fill:#e8f5e9,stroke:#2e7d32
    style ETL fill:#fff3e0,stroke:#e65100
    style Storage fill:#e3f2fd,stroke:#1565c0
    style Dashboard fill:#fce4ec,stroke:#c62828
    style Entregables fill:#e0f2f1,stroke:#00695c
```

## Tecnologias Utilizadas

| Categoria | Herramientas |
|-----------|-------------|
| **Lenguaje** | Python 3.12 |
| **Librerias** | pandas, numpy, plotly, streamlit, sqlalchemy, pymysql, pyarrow, openpyxl, pyproj |
| **Base de datos** | MySQL 8.0 (WSL Ubuntu) |
| **Visualizacion** | Streamlit 1.58, Plotly 6.8, Mapbox OpenStreetMap |
| **Contenedor** | Docker (python:3.11-slim) |
| **Formatos** | Excel (.xlsx) -> CSV -> Parquet -> MySQL -> Dashboard |

## Flujo de Datos

```
Excel (46 archivos, 2.4 GB)
    |
    |-- etl_streaming.py --> CSV (~1.2 GB)
    |-- etl_trafico.py   --> Parquet (16.77 MB, 3.86M registros)
    |-- load_mysql_wsl.py --> MySQL (19.3M registros)
    |                          |-- trafico (24 columnas)
    |                          |-- incidentes (100K registros)
    |                          |-- zonas_criticas (238 registros)
    |
    v
Dashboard Streamlit
    |-- Modo principal: Parquet (rapido)
    |-- Fallback: MySQL
    |-- 12 visualizaciones + mapa interactivo + incidentes
```

## Base de Datos MySQL

```
trafico_medellin
    |-- trafico (19,343,072 registros)
    |   Columnas: id, carril, fecha, hora, dia_semana, mes, anio,
    |             velocidad_kmh, corredor, sentido, intensidad_veh_h,
    |             ocupacion, comuna, latitud, longitud, periodo_dia,
    |             es_hora_pico, indice_congestion
    |
    |-- incidentes (100,000 registros)
    |   Columnas: id, fecha_incidente, ubicacion, tipo_evento,
    |             gravedad, conteo_vehicular, velocidad_promedio
    |
    |-- zonas_criticas (238 registros)
        Columnas: corredor, comuna, velocidad_promedio,
                  intensidad_promedio, ocupacion_promedio
```
