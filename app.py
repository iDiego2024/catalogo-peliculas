# -*- coding: utf-8 -*-
import streamlit as st
from modules import imdb_catalog, analytics, afi_list, oscars_awards
from modules.utils import (
    APP_VERSION,
    load_data,
    apply_theme_and_css,
    show_changelog_sidebar
)

# ---------------- CONFIGURACIÓN BÁSICA ----------------
st.set_page_config(
    page_title="🎬 Mi catálogo de películas (IMDb)",
    layout="wide",
    page_icon="🎥"
)

apply_theme_and_css()

# ---------------- SIDEBAR ----------------
show_changelog_sidebar()

st.sidebar.header("📂 Datos")
uploaded_file = st.sidebar.file_uploader(
    "Sube tu CSV de IMDb (si no, se usa peliculas.csv del repo)",
    type=["csv"]
)

if uploaded_file:
    df = load_data(uploaded_file)
else:
    df = load_data("peliculas.csv")

# Separador visual en la barra lateral
st.sidebar.markdown("---")

# Sección inferior: versión + autor
st.sidebar.markdown(
    f"""
    <div style='text-align:center; font-size:0.9rem; color:#aaa; margin-top:40px;'>
        <b>Versión {APP_VERSION}</b><br>
        powered by Diego Leal
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------- TÍTULO PRINCIPAL ----------------
st.title("🎬 MI CATÁLOGO DE PELÍCULAS (IMDB)")

# ---- BAJADA (fija bajo el título) ----
st.caption("Filtros activos → Años: 1921–2025 | Mi nota: 1–10 | Géneros: Todos | Directores: Todos")

# ---------------- BÚSQUEDA ----------------
st.markdown("### 🔎 Búsqueda en mi catálogo")
search_query = st.text_input(
    "Buscar por título, director, género, año o calificaciones",
    placeholder="Escribe algo...",
    key="search_query"
)

# ---------------- TABS PRINCIPALES ----------------
tab_catalog, tab_awards, tab_afi, tab_analysis = st.tabs(
    ["🎞️ Mi colección", "🏆 Premios", "🎖 AFI", "📊 Análisis"]
)

with tab_catalog:
    try:
        imdb_catalog.render_catalog_tab(df, search_query)
    except Exception as e:
        st.error("Error al cargar el catálogo.")
        st.exception(e)

with tab_awards:
    try:
        oscars_awards.render_awards_tab(df)
    except Exception as e:
        st.error("Error al cargar los premios.")
        st.exception(e)

with tab_afi:
    try:
        afi_list.render_afi_tab(df)
    except Exception as e:
        st.error("Error al cargar la lista AFI.")
        st.exception(e)

with tab_analysis:
    try:
        analytics.render_analysis_tab(df)
    except Exception as e:
        st.error("Error al cargar el análisis.")
        st.exception(e)
