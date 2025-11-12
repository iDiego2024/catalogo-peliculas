# -*- coding: utf-8 -*-
from pathlib import Path
import streamlit as st
import pandas as pd

# -------------------- Imports de módulos propios --------------------
from modules.utils import (
    APP_VERSION,
    apply_theme_and_css,
    show_changelog_sidebar,
    load_data,
)

# Tabs (pueden tener firmas distintas según versión)
import modules.imdb_catalog as imdb_catalog
import modules.analytics as analytics
import modules.afi_list as afi_list
import modules.oscars_awards as oscars_awards

# -------------------- Config básica de la app -----------------------
st.set_page_config(
    page_title="🎬 Mi catálogo de Películas",
    layout="centered"  # el CSS ajusta el ancho en escritorio
)

apply_theme_and_css()

# -------------------- Sidebar: versión y changelog ------------------
with st.sidebar:
    st.markdown(f"**Versión:** `{APP_VERSION}`")
    show_changelog_sidebar()

# -------------------- Paths y carga de CSV --------------------------
BASE_DIR = Path(__file__).parent

st.sidebar.header("📂 Datos")
uploaded = st.sidebar.file_uploader(
    "Sube tu CSV de IMDb (si no, se usa peliculas.csv del repo)",
    type=["csv"]
)

if uploaded is not None:
    df = load_data(uploaded)
else:
    csv_path = BASE_DIR / "peliculas.csv"
    if not csv_path.exists():
        st.error(
            "No se encontró **peliculas.csv** en el repo y no se subió archivo.\n\n"
            "👉 Sube tu CSV desde la barra lateral para continuar."
        )
        st.stop()
    df = load_data(str(csv_path))

if "Title" not in df.columns:
    st.error("El CSV debe contener una columna **Title** para poder funcionar.")
    st.stop()

# -------------------- Opciones de UI / funciones extra --------------
st.title("🎥 Mi catálogo de películas (IMDb)")

# Barra lateral de opciones compartidas
st.sidebar.header("🖼️ Opciones de visualización")
show_posters_fav = st.sidebar.checkbox(
    "Mostrar pósters TMDb en mis favoritas (nota ≥ 9)",
    value=True,
    key="opt_show_posters_fav"
)

st.sidebar.header("🌐 TMDb")
use_tmdb_gallery = st.sidebar.checkbox(
    "Usar TMDb en la galería visual",
    value=True,
    key="opt_use_tmdb_gallery"
)

st.sidebar.header("🎬 Tráilers")
show_trailers = st.sidebar.checkbox(
    "Mostrar tráiler de YouTube (si hay API key)",
    value=True,
    key="opt_show_trailers"
)

st.sidebar.header("⚙️ Opciones avanzadas")
show_awards = st.sidebar.checkbox(
    "Consultar premios en OMDb (puede ser más lento, usa cuota de API)",
    value=False,
    key="opt_show_awards"
)

cfg = {
    "use_tmdb_gallery": use_tmdb_gallery,
    "show_posters_fav": show_posters_fav,
    "show_trailers": show_trailers,
    "show_awards": show_awards,
}

# -------------------- Helpers de compatibilidad ---------------------
def _call_tab_any(func, df, cfg):
    """
    Compatibilidad genérica para tabs con firma nueva (df, cfg) o vieja (df).
    """
    try:
        return func(df, cfg=cfg)
    except TypeError:
        return func(df)

def _call_catalog(func, df, search_query, cfg):
    """
    Compatibilidad específica del Catálogo:
      1) func(df, search_query, cfg=cfg)
      2) func(df, search_query)
      3) func(df, cfg=cfg)
      4) func(df)
    """
    try:
        return func(df, search_query, cfg=cfg)
    except TypeError:
        try:
            return func(df, search_query)
        except TypeError:
            try:
                return func(df, cfg=cfg)
            except TypeError:
                return func(df)

# -------------------- Tabs principales ------------------------------
tab_catalog, tab_analysis, tab_awards, tab_afi = st.tabs(
    ["🎬 Catálogo", "📊 Análisis", "🏆 Premios", "🎖 AFI 100"]
)

# -------------------- TAB: Catálogo ---------------------------------
with tab_catalog:
    # Campo de búsqueda global (lo pasamos si el módulo lo requiere)
    search_query = st.text_input(
        "🔎 Búsqueda en mi catálogo (título, director, género, año o calificaciones)",
        placeholder="Escribe para filtrar (el módulo puede aplicar más filtros internos)…",
        key="global_search_query"
    )

    try:
        _call_catalog(imdb_catalog.render_catalog_tab, df, search_query, cfg)
    except Exception as e:
        st.error("Ocurrió un error al renderizar el catálogo.")
        st.exception(e)

# -------------------- TAB: Análisis ---------------------------------
with tab_analysis:
    try:
        _call_tab_any(analytics.render_analysis_tab, df, cfg)
    except Exception as e:
        st.error("Ocurrió un error al renderizar el análisis.")
        st.exception(e)

# -------------------- TAB: Premios (OMDb) ---------------------------
with tab_awards:
    try:
        _call_tab_any(oscars_awards.render_awards_tab, df, cfg)
    except Exception as e:
        st.error("Ocurrió un error al renderizar la sección de premios.")
        st.exception(e)

# -------------------- TAB: AFI 100 ----------------------------------
with tab_afi:
    try:
        _call_tab_any(afi_list.render_afi_tab, df, cfg)
    except Exception as e:
        st.error("Ocurrió un error al renderizar la lista AFI.")
        st.exception(e)
