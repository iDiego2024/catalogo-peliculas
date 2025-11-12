# app.py — Orquestador modular
import streamlit as st
import pandas as pd
import os

# ====== Versión ======
APP_VERSION = "1.1.1"  # sube un patch por los fixes

# ====== Imports de módulos ======
try:
    from modules import imdb_catalog, analytics, oscars_awards, afi_list, what_to_watch, utils
except Exception as e:
    st.error("No se pudieron importar los módulos. Revisa la carpeta 'modules/'.\n\n" + str(e))
    st.stop()

# ====== Config ======
st.set_page_config(
    page_title=f"🎬 Mi catálogo de Películas · v{APP_VERSION}",
    layout="wide",
)

st.markdown(
    "<h1 style='margin-top:0'>🎥 Mi catálogo de películas (IMDb)</h1>",
    unsafe_allow_html=True,
)

# ====== Carga de datos (sidebar) ======
st.sidebar.header("📂 Datos")
uploaded = st.sidebar.file_uploader(
    "Sube tu CSV de IMDb (si no, se usa peliculas.csv del repo)",
    type=["csv"]
)

def _safe_load(path_or_buf):
    """Usa utils.load_data si existe; si no, un lector mínimo compatible."""
    if hasattr(utils, "load_data"):
        return utils.load_data(path_or_buf)
    # lector mínimo
    df = pd.read_csv(path_or_buf)
    if "Your Rating" in df.columns:
        df["Your Rating"] = pd.to_numeric(df["Your Rating"], errors="coerce")
    if "IMDb Rating" in df.columns:
        df["IMDb Rating"] = pd.to_numeric(df["IMDb Rating"], errors="coerce")
    if "Year" in df.columns:
        df["Year"] = (
            df["Year"].astype(str).str.extract(r"(\d{4})")[0].astype(float)
        )
    else:
        df["Year"] = None
    # columnas esperadas por los módulos
    if "Genres" not in df.columns:
        df["Genres"] = ""
    if hasattr(utils, "normalize_title"):
        norm = utils.normalize_title
    else:
        import re
        norm = lambda s: re.sub(r"[^a-z0-9]+", "", str(s).lower())
    df["NormTitle"] = df.get("Title", "").apply(norm)
    df["GenreList"] = df["Genres"].fillna("").apply(lambda x: [] if x == "" else str(x).split(", "))
    df["YearInt"] = df["Year"].fillna(-1).astype(int)
    return df

if uploaded is not None:
    df = _safe_load(uploaded)
else:
    if os.path.exists("peliculas.csv"):
        df = _safe_load("peliculas.csv")
    else:
        st.error("No encontré 'peliculas.csv' y no subiste CSV. Sube tu CSV para continuar.")
        st.stop()

if "Title" not in df.columns:
    st.error("El CSV debe contener una columna 'Title'.")
    st.stop()

# ====== Tabs ======
tab_catalog, tab_analysis, tab_afi, tab_awards, tab_what = st.tabs(
    ["🎬 Catálogo", "📊 Análisis", "🏆 Lista AFI", "🏆 Premios Óscar", "🎲 ¿Qué ver hoy?"]
)

with tab_catalog:
    imdb_catalog.render_catalog_tab(df)

with tab_analysis:
    analytics.render_analysis_tab(df)

with tab_afi:
    afi_list.render_afi_tab(df)

with tab_awards:
    oscars_awards.render_oscars_tab(df)

with tab_what:
    what_to_watch.render_what_tab(df)

# ====== Footer con versión ======
st.markdown("---")
st.caption(f"Versión **v{APP_VERSION}** · powered by **Diego Leal**")
