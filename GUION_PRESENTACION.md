# Guion de Presentación — Análisis de Tráfico Medellín 2019-2022

**Duración estimada:** 15-20 min  
**Formato:** Slides + Demo en vivo  
**URL demo:** https://zohczgrh82trgdhkmyyfpn.streamlit.app

---

## Slide 1 — Portada (1 min)

**Texto en slide:**  
"Análisis de Datos de Tráfico — Medellín 2019-2022"  
Integrante: Fabio Mauricio Gallo Parra  
Curso: TalentoTech — Análisis de Datos

**Qué decir:**  
"Buenos días/tardes. Hoy les presento mi proyecto de análisis de datos de tráfico de la ciudad de Medellín, cubriendo el periodo 2019 a 2022. El proyecto incluye un pipeline ETL completo, una base de datos MySQL, y un dashboard interactivo desplegado en la nube."

---

## Slide 2 — Contexto y Problema (1-2 min)

**Texto en slide:**  
- Medellín: 2.5M habitantes, parque automotor creciente
- Congestión: pérdidas económicas y ambientales
- Incidentes de tránsito: seguridad vial
- Datos abiertos: Secretaría de Movilidad

**Qué decir:**  
"Medellín enfrenta desafíos importantes de movilidad. La congestión no solo afecta la calidad de vida, sino que tiene impactos económicos y ambientales.  
Este proyecto busca responder preguntas como:  
- ¿Cuáles son los corredores más congestionados?  
- ¿Cómo varía el tráfico por hora, día, mes?  
- ¿Existe relación entre el flujo vehicular y los incidentes de tránsito?"

---

## Slide 3 — Datos (2 min)

**Texto en slide:**

| Origen | Volumen | Periodo |
|--------|---------|---------|
| 46 archivos Excel | ~2.4 GB brutos | 2019-2022 |
| Tráfico unificado | 3.86M registros → 16.7 MB (Parquet) | 2019-2022 |
| Incidentes | 100K registros | 2019-2022 |

**Columnas principales:** hora, velocidad_kmh, intensidad_veh_h, ocupacion, corredor, comuna, periodo_dia

**Qué decir:**  
"Los datos provienen de la Secretaría de Movilidad de Medellín, publicados en Medellín Cómo Vamos.  
Son 46 archivos Excel mensuales que totalizan 2.4 GB. Tras el proceso ETL, los redujimos a 16.7 MB en formato Parquet, una compresión del 99%.  
Las variables clave son velocidad, intensidad (vehículos por hora), ocupación del carril, y metadatos como corredor, comuna y periodo del día."

---

## Slide 4 — Arquitectura (3 min)

**Mostrar diagrama de ARQUITECTURA.md** (tenerlo en pantalla)

**Texto en slide:**
```
Excel → ETL (Python) → Parquet + MySQL → Streamlit Cloud
         │
         └── Conversión coordenadas: MAGNA (EPSG:3116) → WGS84

Modo principal: Parquet (rápido, 16.7 MB)
Fallback: MySQL (si está disponible)
```

**Qué decir:**  
"La arquitectura tiene 3 capas:  
1. **ETL**: Los Excel se procesan con pandas, se unifican, se convierten a Parquet y se cargan a MySQL.  
2. **Almacenamiento**: Parquet como formato principal por su velocidad y compresión; MySQL como respaldo.  
3. **Dashboard**: Streamlit consume Parquet por defecto, con fallback automático a MySQL.  

Un detalle técnico importante: las coordenadas vienen en formato MAGNA Colombia (EPSG:3116), un sistema de proyección. Las convertimos a latitud/longitud (WGS84) para poder mostrarlas en el mapa.  
El dashboard está desplegado en Streamlit Community Cloud, accesible desde cualquier navegador."

---

## Slide 5 — Demo en Vivo: Dashboard (5-7 min)

**Prepárate para compartir pantalla. Abre la URL.**

### 5a. KPIs Globales
**Qué hacer:** Mostrar los 4 KPIs en la parte superior.
**Qué decir:** "Al cargar el dashboard vemos 4 indicadores clave: total de registros, velocidad promedio del periodo (alrededor de 40-45 km/h), intensidad promedio (veh/h), y el índice de congestión."

### 5b. Gráficos de Análisis
**Qué hacer:** Señalar cada gráfico rápidamente.
**Qué decir:**  
- "Velocidad por hora del día: notamos los picos en la madrugada (alta velocidad, poco tráfico) y los valles en hora pico."
- "Congestión por corredor: en rojo los más congestionados, en verde los de flujo libre."
- "Heatmap día vs hora: los días de semana tienen más densidad en horas laborales; los fines de semana el patrón cambia."
- "Evolución anual: vemos la tendencia de velocidad vs congestión."
- "Pronóstico 2023-2026: una regresión lineal simple proyecta la tendencia del flujo vehicular."

### 5c. Mapa Interactivo (EL MOMENTO CLAVE)
**Qué hacer:** Interactuar con el mapa.
1. Cambiar "Color por" a "Velocidad" → los puntos se vuelven verde/rojo.
2. Cambiar "Color por" a "Índice Congestión".
3. Activar toggle "Mostrar incidentes" → aparecen X rojas.
4. **Hacer clic en un punto del mapa** → mostrar el panel de detalle con la evolución horaria.

**Qué decir:**  
"El mapa es la pieza central. Cada punto es un corredor en una comuna.  
El color representa la métrica seleccionada: velocidad (rojo=lento, verde=rápido) o congestión.  
Podemos activar los incidentes como superposición.  
Y lo más importante: **al hacer clic en cualquier punto**, se despliega el detalle del corredor con sus métricas y un gráfico de evolución horaria."

### 5d. Sección Incidentes
**Qué hacer:** Scroll down a la sección de incidentes.
**Qué decir:**  
"La sección de incidentes tiene sus propios KPIs, filtros por tipo y gravedad, distribución, y un mapa específico.  
La gráfica de comparativa tráfico vs incidentes es particularmente interesante: muestra si a mayor flujo vehicular hay más incidentes, y la velocidad asociada."

---

## Slide 6 — Hallazgos Clave (2-3 min)

**Texto en slide:**
- **Velocidad promedio:** ~42 km/h en la ciudad
- **Corredores críticos:** Los de mayor congestión tienen velocidades <20 km/h en hora pico
- **Pico de tráfico:** 7-8 AM y 5-7 PM (lunes a viernes)
- **2020:** Caída atípica por pandemia, recuperación en 2021-2022
- **Incidentes:** Mayor concentración en corredores de alto flujo
- **Pronóstico:** Tendencia al alza en intensidad vehicular

**Qué decir:**  
"Los hallazgos confirman lo esperado: los corredores principales tienen alta congestión en horas pico.  
El año 2020 muestra una anomalía clara por la pandemia, con caída en intensidad y aumento de velocidad.  
La relación flujo-incidentes no es perfectamente lineal: algunos corredores con flujo moderado tienen muchos incidentes, lo que sugiere factores como diseño vial o condiciones de la vía.  
El pronóstico lineal sugiere que la intensidad vehicular seguirá aumentando si no hay cambios en infraestructura o políticas de movilidad."

---

## Slide 7 — Tecnologías Usadas (1 min)

**Texto en slide:**

| Propósito | Herramienta |
|-----------|------------|
| Lenguaje | Python 3.12 |
| Procesamiento | pandas, numpy, pyarrow |
| Visualización | Streamlit, Plotly, Mapbox |
| Base de datos | MySQL 8.0 |
| Coordenadas | pyproj (EPSG:3116 → WGS84) |
| Despliegue | Streamlit Community Cloud |
| Control de versión | Git + GitHub |
| Formato datos | Parquet (columnar, comprimido) |

**Qué decir:**  
"Usamos Python con pandas para el procesamiento, Streamlit + Plotly para el dashboard interactivo, Parquet como formato de almacenamiento columnar (rápido y comprimido), y MySQL para consultas analíticas.  
El proyecto está versionado en GitHub y el dashboard desplegado en Streamlit Cloud."

---

## Slide 8 — Conclusiones y Próximos Pasos (1 min)

**Texto en slide:**
- ✅ Pipeline ETL completo (Excel → Parquet → Dashboard)
- ✅ Dashboard interactivo desplegado en la nube
- ✅ Análisis temporal, espacial y de incidentes
- 🔜 Modelos predictivos más avanzados (SARIMA, Prophet)
- 🔜 Más fuentes de datos (clima, eventos, obras viales)
- 🔜 Segmentación por sentido vial y carril

**Qué decir:**  
"El proyecto cumple el objetivo: construir un pipeline de datos funcional con un dashboard interactivo accesible desde cualquier lugar.  
A futuro, se podría mejorar con modelos predictivos más robustos como SARIMA o Prophet, integrar datos climáticos y de eventos, y profundizar en el análisis por sentido y carril."

---

## Slide 9 — Preguntas

**Texto en slide:** "Gracias — Preguntas"  
**Tener preparado:** GitHub repo, URL del dashboard, PDF del informe

---

## Tips Técnicos para la Exposición

### Antes de presentar:
1. **Abrir la URL del dashboard** y verificar que cargue
2. Tener el repo abierto en GitHub: https://github.com/maurogallo/TalentoTechIntegrador_AnalisisDeDatos
3. Tener ARQUITECTURA.md abierto para mostrarlo
4. **Capturas de respaldo** (ver sección abajo)
5. Cerrar pestañas innecesarias

### Durante la demo:
- **No te apresures** en los filtros — deja que los gráficos se carguen
- El clic en el mapa es lo que más impresiona: hazlo con calma
- Si falla internet, di "el dashboard está desplegado en la nube, permítanme mostrar las capturas"

### Posibles preguntas difíciles:
- **"¿Por qué Parquet y no CSV?"** → Compresión 99%, lectura 10x más rápida, formato columnar ideal para analytics
- **"¿Streamlit es gratis?"** → Streamlit Community Cloud tiene tier gratuito con 1 GB RAM
- **"¿Los datos son confiables?"** → Datos oficiales de la Secretaría de Movilidad vía Medellín Cómo Vamos

---

## Capturas de Respaldo

Si no puedes hacer la demo en vivo, muestra estas capturas del dashboard:

1. **Dashboard completo** — visión general con KPIs
2. **Mapa con incidentes activados** — lo más impactante
3. **Gráfico de congestión por corredor** — muestra los más críticos
4. **Sección de incidentes** — demuestra profundidad del análisis
5. **Arquitectura (Mermaid)** — diagrama del pipeline

---

## Checklist Final

- [ ] Dashboard cargando en el navegador
- [ ] Repositorio GitHub accesible
- [ ] PDF del informe listo
- [ ] Capturas de respaldo descargadas
- [ ] Diagrama de arquitectura visible
- [ ] Cuenta de Streamil t logueada (share.streamlit.io)
- [ ] Notebook Jupyter listo por si preguntan por código

---

**Buena suerte con la exposición.** 🚀
