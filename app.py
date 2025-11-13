# app.py
from pathlib import Path
import streamlit as st
import pandas as pd

from modules.utils import (
    APP_VERSION,
    apply_theme_and_css,
    show_changelog_sidebar,
    load_data,
    normalize_title,
)

import modules.imdb_catalog as imdb_catalog

BASE_DIR = Path(__file__).parent

# ── Configuración de página
st.set_page_config(page_title="🎬 Mi catálogo de Películas", layout="wide")
apply_theme_and_css()

# ── Barra lateral
st.sidebar.header("📂 Datos")
uploaded = st.sidebar.file_uploader(
    "Sube tu CSV de IMDb (si no, se usa peliculas.csv del repo)",
    type=["csv"]
)

st.sidebar.markdown("---")
st.sidebar.header("🧱 Galería")
use_tmdb_gallery = st.sidebar.checkbox("Usar pósters de TMDb", value=True)
page_size_default = st.sidebar.select_slider(
    "Pósters por página (por defecto)",
    options=[12, 24, 36, 48, 60],
    value=24
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Versión **{APP_VERSION}**  \npowered by Diego Leal")
show_changelog_sidebar()

# ── Carga de datos
if uploaded is not None:
    df = load_data(uploaded)
else:
    df = load_data(str(BASE_DIR / "peliculas.csv"))

if "Title" not in df.columns:
    st.error("El CSV debe contener una columna 'Title'.")
    st.stop()

df["NormTitle"] = df["Title"].apply(normalize_title)
df["YearInt"] = df["Year"].fillna(-1).astype(int) if "Year" in df.columns else -1

# ── Cabecera
st.markdown(
    """
    <div class="page-hero">
      <h1 class="golden-title">Mi catálogo de películas (IMDb)</h1>
      <div class="subtitle-line">
        Filtros activos → Años: 1921–2025 | Mi nota: 1–10 | Géneros: Todos | Directores: Todos
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# (Si más adelante vuelves a activar filtros/búsqueda, usa ese DF)
df_view = df

# ── Catálogo (tabla + galería)
imdb_catalog.render_catalog_tab(
    df_view,
    page_size=int(page_size_default),
    use_tmdb_gallery=use_tmdb_gallery
)
