# modules/utils.py
import os
import re
import streamlit as st
import pandas as pd
from urllib.parse import quote_plus

# ----------------- Versión de la app -----------------
APP_VERSION = "v1.0.0"

# ----------------- Tema / CSS dorado -----------------
def apply_theme_and_css(page_title: str = "Mi catálogo de Películas", layout: str = "centered"):
    """
    Compat: función que tu app.py importaba antes.
    - Configura page_config (layout) y título
    - Inyecta el CSS dorado/anchos/cuadrícula
    """
    try:
        st.set_page_config(page_title=page_title, layout=layout)
    except Exception:
        # Streamlit Cloud podría llamar set_page_config dos veces; ignorar.
        pass

    # Import local para evitar dependencias circulares
    try:
        from modules.styles import inject_theme_css
        inject_theme_css()
    except Exception as e:
        st.warning(f"No se pudo inyectar el tema CSS: {e}")

# ----------------- Changelog / versión en la barra -----------------
def show_changelog_sidebar():
    """
    Muestra versión y un mini changelog en la barra lateral.
    Si existe CHANGELOG.md en el repo, lo muestra dentro de un expander.
    """
    st.sidebar.markdown("### ℹ️ Acerca de")
    st.sidebar.write(f"**Versión:** {APP_VERSION}")

    # En Streamlit Cloud, la ruta raíz es /mount/src/<repo>/
    # Intentamos leer un CHANGELOG.md si existe.
    changelog_text = None
    for candidate in ["CHANGELOG.md", "Changelog.md", "changelog.md", "docs/CHANGELOG.md"]:
        if os.path.exists(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    changelog_text = f.read()
                    break
            except Exception:
                pass

    with st.sidebar.expander("Changelog", expanded=False):
        if changelog_text:
            st.markdown(changelog_text)
        else:
            st.caption("Agrega un `CHANGELOG.md` al repositorio para mostrarlo aquí.")

# ----------------- Normalización de títulos -----------------
def normalize_title(s: str) -> str:
    """Normaliza un título (minúsculas, sin espacios/acentos/signos) para matching."""
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

# ----------------- Formateos -----------------
def fmt_year(y):
    if pd.isna(y):
        return ""
    try:
        return f"{int(float(y))}"
    except Exception:
        return ""

def fmt_rating(v):
    if pd.isna(v):
        return ""
    try:
        return f"{float(v):.1f}"
    except Exception:
        return str(v)

# ----------------- Colores por rating -----------------
def get_rating_colors(rating):
    """
    Devuelve (border_color, glow_color) en función del rating (Your Rating o IMDb).
    Paleta sobria profesional con acento dorado / azules / púrpuras.
    """
    try:
        r = float(rating)
    except Exception:
        return ("rgba(148,163,184,0.8)", "rgba(15,23,42,0.0)")

    if r >= 9:
        return ("#22c55e", "rgba(34,197,94,0.55)")         # verde alto
    elif r >= 8:
        return ("#0ea5e9", "rgba(14,165,233,0.55)")        # azul
    elif r >= 7:
        return ("#a855f7", "rgba(168,85,247,0.50)")        # púrpura
    elif r >= 6:
        return ("#eab308", "rgba(234,179,8,0.45)")         # dorado tenue
    else:
        return ("#f97316", "rgba(249,115,22,0.45)")        # naranja

# ----------------- Link a reseñas en español -----------------
def get_spanish_review_link(title, year=None):
    if not title or pd.isna(title):
        return None
    q = f"reseña película {title}"
    try:
        if year is not None and not pd.isna(year):
            q += f" {int(float(year))}"
    except Exception:
        pass
    return "https://www.google.com/search?q=" + quote_plus(q)

# ----------------- Carga y preparación de datos -----------------
@st.cache_data
def load_data(file_path_or_buffer):
    """
    Carga CSV de IMDb y prepara columnas usadas por la app y módulos:
    - Your Rating / IMDb Rating a numérico
    - Year (extrae año de strings)
    - Genres/Directors y GenreList
    - Date Rated a fecha
    - SearchText para búsqueda rápida
    """
    df = pd.read_csv(file_path_or_buffer)

    if "Your Rating" in df.columns:
        df["Your Rating"] = pd.to_numeric(df["Your Rating"], errors="coerce")
    else:
        df["Your Rating"] = None

    if "IMDb Rating" in df.columns:
        df["IMDb Rating"] = pd.to_numeric(df["IMDb Rating"], errors="coerce")
    else:
        df["IMDb Rating"] = None

    if "Year" in df.columns:
        df["Year"] = (
            df["Year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
            .astype(float)
        )
    else:
        df["Year"] = None

    if "Genres" not in df.columns:
        df["Genres"] = ""

    if "Directors" not in df.columns:
        df["Directors"] = ""

    df["Genres"] = df["Genres"].fillna("")
    df["GenreList"] = df["Genres"].apply(
        lambda x: [] if pd.isna(x) or x == "" else str(x).split(", ")
    )

    if "Date Rated" in df.columns:
        df["Date Rated"] = pd.to_datetime(df["Date Rated"], errors="coerce").dt.date

    # Texto de búsqueda precomputado
    search_cols = []
    for c in ["Title", "Original Title", "Directors", "Genres", "Year", "Your Rating", "IMDb Rating"]:
        if c in df.columns:
            search_cols.append(c)

    if search_cols:
        df["SearchText"] = (
            df[search_cols]
            .astype(str)
            .apply(lambda row: " ".join(row), axis=1)
            .str.lower()
        )
    else:
        df["SearchText"] = ""

    # Aux para AFI/match
    df["NormTitle"] = df["Title"].apply(normalize_title) if "Title" in df.columns else ""
    df["YearInt"] = df["Year"].fillna(-1).astype(int) if "Year" in df.columns else -1

    return df
