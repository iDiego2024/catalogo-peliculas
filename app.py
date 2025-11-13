# app.py (fragmento esencial)

import streamlit as st
import pandas as pd
from pathlib import Path

from modules.utils import (
    APP_VERSION, apply_theme_and_css, show_changelog_sidebar, load_data,
    normalize_title,
)
import modules.imdb_catalog as imdb_catalog

BASE_DIR = Path(__file__).parent

st.set_page_config(page_title="🎬 Mi catálogo de Películas", layout="wide")
apply_theme_and_css()

# ---------------- Barra lateral ----------------
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

# Versión al final de la barra
st.sidebar.caption(f"Versión **{APP_VERSION}**  \npowered by Diego Leal")
show_changelog_sidebar()

# ------------- Carga de datos --------------
if uploaded:
    df = load_data(uploaded)
else:
    df = load_data(str(BASE_DIR / "peliculas.csv"))

# Campos auxiliares (por seguridad)
df["NormTitle"] = df["Title"].apply(normalize_title)
df["YearInt"] = df["Year"].fillna(-1).astype(int)

# ---------------- Título + bajada ----------------
st.title("🎥 Mi catálogo de películas (IMDb)")
st.caption(
    "Filtros activos → Años: 1921–2025 | Mi nota: 1–10 | "
    "Géneros: Todos | Directores: Todos"
)

# Aquí tu búsqueda/filtros/ordenado… (si ya los tienes en otro módulo, perfecto)
# Suponiendo que el dataframe final filtrado/ordenado se llama df_view:
df_view = df  # (coloca tus filtros reales aquí)

# ---------------- Render catálogo ----------------
imdb_catalog.render_catalog_tab(
    df_view,
    page_size=int(page_size_default),           # por defecto
    use_tmdb_gallery=use_tmdb_gallery           # <- importante
)
