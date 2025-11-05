import streamlit as st
import pandas as pd
import requests
import random

# ----------------- Configuración general -----------------

st.set_page_config(
    page_title="🎬 Catálogo de Películas",
    layout="wide"
)

st.title("🎥 Mi catálogo de películas (IMDb)")
st.write(
    "App basada en tu export de IMDb. "
    "Puedes filtrar por año, nota, géneros, director y buscar por título."
)

# ----------------- Config TMDb -----------------

TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"


# ----------------- Funciones auxiliares -----------------


@st.cache_data
def load_data(file_path_or_buffer):
    df = pd.read_csv(file_path_or_buffer)

    # Asegurar tipos básicos

    # Tu nota
    if "Your Rating" in df.columns:
        df["Your Rating"] = pd.to_numeric(df["Your Rating"], errors="coerce")
    else:
        df["Your Rating"] = None

    # IMDb Rating
    if "IMDb Rating" in df.columns:
        df["IMDb Rating"] = pd.to_numeric(df["IMDb Rating"], errors="coerce")
    else:
        df["IMDb Rating"] = None

    # Year: extraer solo un año de 4 dígitos aunque venga sucio (ej. "2019–2020", "2019,", etc.)
    if "Year" in df.columns:
        df["Year"] = (
            df["Year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]  # primer grupo de 4 dígitos
            .astype(float)
        )
    else:
        df["Year"] = None

    # Genres
    if "Genres" not in df.columns:
        df["Genres"] = ""

    # Directors
    if "Directors" not in df.columns:
        df["Directors"] = ""

    # Lista de géneros para filtros
    df["Genres"] = df["Genres"].fillna("")
    df["GenreList"] = df["Genres"].apply(
        lambda x: [] if pd.isna(x) or x == "" else str(x).split(", ")
    )

    # Parsear fecha calificada
    if "Date Rated" in df.columns:
        df["Date Rated"] = pd.to_datetime(df["Date Rated"], errors="coerce").dt.date

    return df


@st.cache_data
def get_poster_url(title, year=None):
    """Devuelve solo la URL del póster de TMDb."""
    if TMDB_API_KEY is None:
        return None  # No hay API key configurada

    if not title or pd.isna(title):
        return None

    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
    }
    if year is not None and not pd.isna(year):
        try:
            params["year"] = int(year)
        except Exception:
            pass

    try:
        r = requests.get(TMDB_SEARCH_URL, params=params, timeout=2)
        if r.status_code != 200:
            return None

        data = r.json()
        results = data.get("results", [])
        if not results:
            return None

        poster_path = results[0].get("poster_path")
        if not poster_path:
            return None

        return f"{TMDB_IMAGE_BASE}{poster_path}"
    except Exception:
        return None


@st.cache_data
def get_tmdb_vote_average(title, year=None):
    """Devuelve el voto medio de TMDb (vote_average) para un título."""
    if TMDB_API_KEY is None:
        return None

    if not title or pd.isna(title):
        return None

    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
    }
    if year is not None and not pd.isna(year):
        try:
            params["year"] = int(year)
        except Exception:
            pass

    try:
        r = requests.get(TMDB_SEARCH_URL, params=params, timeout=2)
        if r.status_code != 200:
            return None

        data = r.json()
        results = data.get("results", [])
        if not results:
            return None

        return results[0].get("vote_average")
    except Exception:
        return None


# ----------------- Carga de datos -----------------

st.sidebar.header("📂 Datos")

uploaded = st.sidebar.file_uploader(
    "Sube tu CSV de IMDb (si no, usaré peliculas.csv del repo)",
    type=["csv"]
)

if uploaded is not None:
    df = load_data(uploaded)
else:
    try:
        df = load_data("peliculas.csv")  # archivo en el repo
