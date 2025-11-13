# app.py
import os
from pathlib import Path

import streamlit as st
import pandas as pd

# --- Importes de módulos propios
from modules.utils import (
    APP_VERSION,
    apply_theme_and_css,
    load_data,
    fmt_year,
    fmt_rating,
    filters_summary_text,
)
import modules.imdb_catalog as imdb_catalog
import modules.analytics as analytics
import modules.afi_list as afi_list
import modules.oscars_awards as oscars_awards

BASE_DIR = Path(__file__).parent

# ----------------- Configuración general -----------------
st.set_page_config(
    page_title="🎬 Mi catálogo de Películas (IMDb)",
    layout="wide",
)

apply_theme_and_css()

# ----------------- Sidebar: Datos -----------------
st.sidebar.header("📂 Datos")
uploaded = st.sidebar.file_uploader(
    "Sube tu CSV de IMDb (si no, se usa peliculas.csv del repo)",
    type=["csv"],
)

# Cargar datos
if uploaded is not None:
    df = load_data(uploaded)
else:
    default_csv = BASE_DIR / "peliculas.csv"
    if default_csv.exists():
        df = load_data(str(default_csv))
    else:
        st.error(
            "No se encontró **peliculas.csv** y no subiste un archivo.\n\n"
            "Sube tu CSV de IMDb desde la barra lateral para continuar."
        )
        st.stop()

if "Title" not in df.columns:
    st.error("El CSV debe contener una columna **Title** para poder funcionar.")
    st.stop()

# ----------------- Sidebar: Opciones visualización -----------------
st.sidebar.header("🖼️ Opciones de visualización")
use_tmdb_gallery = st.sidebar.checkbox(
    "Usar pósters TMDb en la galería", value=True
)
show_trailers = st.sidebar.checkbox(
    "Mostrar tráiler de YouTube (si hay API key)", value=False
)
consult_awards = st.sidebar.checkbox(
    "Consultar premios (OMDb) – puede ser más lento", value=False
)

# ----------------- Sidebar: Filtros -----------------
st.sidebar.header("🎛️ Filtros")

# Año
if df["Year"].notna().any():
    min_year = int(pd.to_numeric(df["Year"], errors="coerce").dropna().min())
    max_year = int(pd.to_numeric(df["Year"], errors="coerce").dropna().max())
else:
    min_year, max_year = (1900, 2100)
year_range = st.sidebar.slider("Rango de años", min_year, max_year, (min_year, max_year))

# Tu nota
if "Your Rating" in df.columns and df["Your Rating"].notna().any():
    rmin = int(pd.to_numeric(df["Your Rating"], errors="coerce").dropna().min())
    rmax = int(pd.to_numeric(df["Your Rating"], errors="coerce").dropna().max())
else:
    rmin, rmax = (1, 10)
rating_range = st.sidebar.slider("Mi nota (Your Rating)", 1, 10, (rmin, rmax))

# Géneros y directores
df["Genres"] = df.get("Genres", "").fillna("")
df["GenreList"] = df["Genres"].apply(
    lambda x: [] if pd.isna(x) or x == "" else str(x).split(", ")
)
all_genres = sorted({g for sub in df["GenreList"] for g in (sub or []) if g})
selected_genres = st.sidebar.multiselect("Géneros (todas deben estar presentes)", all_genres)

all_directors = sorted(
    {d.strip() for d in df.get("Directors", "").dropna().astype(str).tolist() for d in d.split(",") if d.strip()}
)
selected_directors = st.sidebar.multiselect("Directores", all_directors)

# Orden
order_by = st.sidebar.selectbox(
    "Ordenar por", ["Your Rating", "IMDb Rating", "Year", "Title", "Aleatorio"]
)
order_asc = st.sidebar.checkbox("Orden ascendente", value=False)

# Versión (en la barra, abajo)
st.sidebar.markdown("---")
st.sidebar.caption(f"**Versión {APP_VERSION}**\n\npowered by Diego Leal")

# ----------------- Título y bajada -----------------
st.title("🎥 Mi catálogo de películas (IMDb)")
st.caption(
    filters_summary_text(
        year_range=year_range,
        rating_range=rating_range,
        selected_genres=selected_genres,
        selected_directors=selected_directors,
    )
)

# ----------------- Búsqueda única -----------------
st.markdown("### 🔎 Búsqueda en mi catálogo (sobre los filtros actuales)")
search_query = st.text_input(
    "Buscar por título, director, género, año o calificaciones",
    placeholder="Escribe algo…",
)

# ----------------- Aplicar filtros base -----------------
filtered = df.copy()

# Año
filtered["YearNum"] = pd.to_numeric(filtered["Year"], errors="coerce")
filtered = filtered[(filtered["YearNum"] >= year_range[0]) & (filtered["YearNum"] <= year_range[1])]

# Tu nota
filtered["YourNum"] = pd.to_numeric(filtered.get("Your Rating", None), errors="coerce")
filtered = filtered[
    (filtered["YourNum"].fillna(-999) >= rating_range[0]) &
    (filtered["YourNum"].fillna(-999) <= rating_range[1])
]

# Géneros
if selected_genres:
    filtered = filtered[filtered["GenreList"].apply(lambda gl: all(g in (gl or []) for g in selected_genres))]

# Directores
if selected_directors:
    def _match_dirs(cell: str) -> bool:
        if pd.isna(cell): 
            return False
        dirs = [d.strip() for d in str(cell).split(",") if d.strip()]
        return any(d in dirs for d in selected_directors)
    filtered = filtered[filtered.get("Directors", "").apply(_match_dirs)]

# Orden
if order_by == "Aleatorio":
    if not filtered.empty:
        filtered = filtered.sample(frac=1.0, random_state=None)
elif order_by in filtered.columns:
    filtered = filtered.sort_values(order_by, ascending=order_asc)

# ----------------- Tabs -----------------
tab_catalog, tab_awards, tab_afi, tab_analysis, tab_pick = st.tabs(
    ["🎬 Mi colección", "🏆 Premios", "🎖️ AFI", "📊 Análisis", "🎲 ¿Qué ver hoy?"]
)

with tab_catalog:
    imdb_catalog.render_catalog_tab(
        filtered_df=filtered,
        search_query=search_query,
        use_tmdb_gallery=use_tmdb_gallery,
        show_trailers=show_trailers,
        consult_awards=consult_awards,
    )

with tab_awards:
    oscars_awards.render_awards_tab(filtered, consult_awards)

with tab_afi:
    afi_list.render_afi_tab(df)

with tab_analysis:
    analytics.render_analysis_tab(filtered)

with tab_pick:
    imdb_catalog.render_pick_tab(
        filtered_df=filtered,
        show_trailers=show_trailers,
        consult_awards=consult_awards,
    )
