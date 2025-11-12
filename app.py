# --- resolver rutas para imports en Streamlit Cloud / local ---
import sys, pathlib
BASE_DIR = pathlib.Path(__file__).resolve().parent
MODULES_DIR = BASE_DIR / "modules"
for p in (BASE_DIR, MODULES_DIR):
    p_str = str(p)
    if p.exists() and p_str not in sys.path:
        sys.path.insert(0, p_str)
# --------------------------------------------------------------

import streamlit as st

# Importar submódulos (tu código modular ya creado)
import modules.imdb_catalog as imdb_catalog
import modules.analytics as analytics
import modules.afi_list as afi_list
import modules.oscars_awards as oscars_awards

# Importar utilidades centrales (versión, tema CSS, carga de datos)
from modules.utils import (
    APP_VERSION,
    apply_theme_and_css,
    show_changelog_sidebar,
    load_data,
)

# ----------------- Configuración general de página -----------------
st.set_page_config(
    page_title="🎬 Mi catálogo de Películas",
    layout="wide",  # ancho como el original
    page_icon="🎬",
)

# ----------------- Tema y CSS (dorado + ancho + fuentes) ----------
apply_theme_and_css()  # inyecta el CSS dorado y ensancha contenedor

# ----------------- Encabezado -------------------------------------
st.title("🎥 Mi catálogo de películas (IMDb)")
st.caption(f"Versión de la app: **{APP_VERSION}**")

# ----------------- Barra lateral: datos + changelog ----------------
with st.sidebar:
    st.header("📂 Datos")
    uploaded = st.file_uploader(
        "Sube tu CSV de IMDb (si no, se usa 'peliculas.csv' del repo)",
        type=["csv"],
        key="uploader_main",
    )

    show_changelog_sidebar()  # panel de versiones / changelog profesional

# ----------------- Carga de datos ---------------------------------
if uploaded is not None:
    df = load_data(uploaded)
else:
    try:
        df = load_data(str(BASE_DIR / "peliculas.csv"))
    except FileNotFoundError:
        st.error(
            "No se encontró **peliculas.csv** y no subiste archivo.\n\n"
            "→ Sube tu CSV de IMDb desde la barra lateral para continuar."
        )
        st.stop()

if "Title" not in df.columns:
    st.error("El CSV debe contener una columna **Title** para poder funcionar.")
    st.stop()

# ----------------- TABS principales (como tu app original) --------
tab_catalog, tab_analysis, tab_afi, tab_what = st.tabs(
    ["🎬 Catálogo", "📊 Análisis", "🏆 Lista AFI", "🎲 ¿Qué ver hoy?"]
)

with tab_catalog:
    # Render de la galería/tabla/filtros (tu módulo)
    imdb_catalog.render_catalog_tab(df)

with tab_analysis:
    analytics.render_analysis_tab(df)

with tab_afi:
    afi_list.render_afi_tab(df)

with tab_what:
    oscars_awards.render_awards_tab(df)

# ----------------- Footer pequeño -----------------
st.markdown(
    "<div style='text-align:center;opacity:0.7;margin-top:1.5rem'>"
    "Hecho con ❤️ y dorado por Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
