# app.py
import streamlit as st
from modules import imdb_catalog, analytics, afi_list, oscars_awards
from modules.utils import (
    load_data, apply_theme_and_css, show_changelog_sidebar, APP_VERSION
)

# ----------------- CONFIGURACIÓN INICIAL -----------------
st.set_page_config(
    page_title="🎥 Mi Catálogo de Películas (IMDb)",
    layout="wide",
    page_icon="🎬"
)

apply_theme_and_css()
show_changelog_sidebar()

st.title("🎥 Mi catálogo de películas (IMDb)")

# ----------------- CARGA DE DATOS -----------------
df = load_data("peliculas.csv")

# ----------------- BÚSQUEDA -----------------
st.markdown("### 🔎 Búsqueda en mi catálogo")
search_query = st.text_input(
    "Buscar por título, director, género, año o calificación",
    placeholder="Escribe algo...",
    key="search_query"
)

# ----------------- TABS -----------------
tab_catalog, tab_awards, tab_afi, tab_analytics = st.tabs(
    ["🎬 Mi colección", "🏆 Premios", "🎞️ AFI", "📊 Análisis"]
)

with tab_catalog:
    # Catálogo IMDb
    imdb_catalog.render_catalog_tab(df, search_query)

with tab_awards:
    # Premios (Oscar)
    oscars_awards.render_awards_tab(df)

with tab_afi:
    # AFI
    afi_list.render_afi_tab(df)

with tab_analytics:
    # Estadísticas
    analytics.render_analysis_tab(df)

# ----------------- PIE DE PÁGINA -----------------
st.markdown(
    f"""
    <hr style="margin-top:40px;opacity:0.4">
    <div style='text-align:center; font-size:0.9rem; color:#aaa;'>
        <b>Versión {APP_VERSION}</b> — powered by Diego Leal
    </div>
    """,
    unsafe_allow_html=True,
)
