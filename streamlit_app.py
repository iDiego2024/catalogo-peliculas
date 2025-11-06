
import streamlit as st
import pandas as pd
import requests
import random
import altair as alt
import re

# ----------------- Configuración general -----------------

st.set_page_config(page_title="🎬 Catálogo de Películas", layout="wide")

st.title("🎥 Mi catálogo de películas (IMDb)")
st.write(
    "App basada en tu export de IMDb. Filtra, busca y explora tu colección, con información de TMDb, OMDb y plataformas de streaming."
)

# ----------------- Configuración de APIs -----------------

TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"
OMDB_API_KEY = st.secrets.get("OMDB_API_KEY", None)

# ----------------- Funciones auxiliares -----------------

def normalize_title(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

def _coerce_year_for_tmdb(year):
    if year is None or pd.isna(year):
        return None
    try:
        return int(float(year))
    except Exception:
        return None

@st.cache_data
def get_poster_url(title, year=None):
    if TMDB_API_KEY is None:
        return None
    if not title or pd.isna(title):
        return None

    title = str(title).strip()
    year_int = _coerce_year_for_tmdb(year)
    params = {"api_key": TMDB_API_KEY, "query": title}
    if year_int is not None:
        params["year"] = year_int

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
def get_streaming_availability(title, year=None, country="CL"):
    if TMDB_API_KEY is None:
        return None
    if not title or pd.isna(title):
        return None
    title = str(title).strip()
    year_int = _coerce_year_for_tmdb(year)
    try:
        search_params = {"api_key": TMDB_API_KEY, "query": title}
        if year_int is not None:
            search_params["year"] = year_int
        r = requests.get(TMDB_SEARCH_URL, params=search_params, timeout=4)
        if r.status_code != 200:
            return None
        data = r.json()
        results = data.get("results", [])
        if not results:
            return None
        movie_id = results[0].get("id")
        if not movie_id:
            return None
        providers_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers"
        r2 = requests.get(providers_url, params={"api_key": TMDB_API_KEY}, timeout=4)
        if r2.status_code != 200:
            return None
        pdata = r2.json()
        country_data = pdata.get("results", {}).get(country.upper())
        if not country_data:
            return None
        providers = set()
        for key in ["flatrate", "rent", "buy", "ads", "free"]:
            for item in country_data.get(key, []) or []:
                name = item.get("provider_name")
                if name:
                    providers.add(name)
        return {"platforms": sorted(list(providers)), "link": country_data.get("link")}
    except Exception:
        return None

@st.cache_data
def get_omdb_awards(title, year=None):
    if OMDB_API_KEY is None:
        return None
    if not title or pd.isna(title):
        return None
    title = str(title).strip()
    params = {"apikey": OMDB_API_KEY, "t": title, "type": "movie"}
    if year and not pd.isna(year):
        params["y"] = int(float(year))
    try:
        r = requests.get("https://www.omdbapi.com/", params=params, timeout=8)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("Response") != "True":
            return None
        return data.get("Awards", "N/A")
    except Exception:
        return None

def get_rating_colors(rating):
    try:
        r = float(rating)
    except Exception:
        return ("rgba(148,163,184,0.8)", "rgba(15,23,42,0.0)")
    if r >= 9:
        return ("#22c55e", "rgba(34,197,94,0.55)")
    elif r >= 8:
        return ("#0ea5e9", "rgba(14,165,233,0.55)")
    elif r >= 7:
        return ("#a855f7", "rgba(168,85,247,0.50)")
    elif r >= 6:
        return ("#eab308", "rgba(234,179,8,0.45)")
    else:
        return ("#f97316", "rgba(249,115,22,0.45)")

@st.cache_data
def load_data(file_path_or_buffer):
    df = pd.read_csv(file_path_or_buffer)
    if "Your Rating" in df.columns:
        df["Your Rating"] = pd.to_numeric(df["Your Rating"], errors="coerce")
    if "IMDb Rating" in df.columns:
        df["IMDb Rating"] = pd.to_numeric(df["IMDb Rating"], errors="coerce")
    if "Year" in df.columns:
        df["Year"] = df["Year"].astype(str).str.extract(r"(\d{4})")[0].astype(float)
    df["Genres"] = df.get("Genres", "").fillna("")
    df["GenreList"] = df["Genres"].apply(lambda x: x.split(", ") if x else [])
    df["Directors"] = df.get("Directors", "").fillna("")
    return df

# ----------------- Carga de datos -----------------

st.sidebar.header("📂 Datos")
uploaded = st.sidebar.file_uploader("Sube tu CSV de IMDb", type=["csv"])

if uploaded is not None:
    df = load_data(uploaded)
else:
    df = load_data("peliculas.csv")

if "Title" not in df.columns:
    st.error("El CSV debe tener una columna 'Title'.")
    st.stop()

# ----------------- Filtros -----------------

year_range = st.sidebar.slider("Año", int(df["Year"].min()), int(df["Year"].max()), (1970, 2025))
rating_range = st.sidebar.slider("Tu nota", 0, 10, (0, 10))
genre_options = sorted({g for gl in df["GenreList"] for g in gl if g})
selected_genres = st.sidebar.multiselect("Géneros", genre_options)

filtered = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])]
filtered = filtered[(filtered["Your Rating"] >= rating_range[0]) & (filtered["Your Rating"] <= rating_range[1])]
if selected_genres:
    filtered = filtered[filtered["GenreList"].apply(lambda x: all(g in x for g in selected_genres))]

# ----------------- Búsqueda y resultados unificados -----------------

query = st.text_input("🔎 Buscar película (título, director o género)")
if query:
    q = query.lower()
    filtered = filtered[filtered.apply(lambda r: q in str(r["Title"]).lower() or q in str(r["Directors"]).lower() or q in str(r["Genres"]).lower(), axis=1)]

st.write(f"Se encontraron {len(filtered)} películas.")

# Mostrar resultados con poster, premios y streaming
for _, row in filtered.head(10).iterrows():
    title = row["Title"]
    year = row["Year"]
    your_rating = row["Your Rating"]
    imdb_rating = row["IMDb Rating"]
    genres = row["Genres"]
    directors = row["Directors"]
    url = row.get("URL", "")

    poster = get_poster_url(title, year)
    awards = get_omdb_awards(title, year)
    streaming = get_streaming_availability(title, year)

    border_color, glow_color = get_rating_colors(your_rating or imdb_rating)
    st.markdown(f"<div class='movie-card' style='border:2px solid {border_color};box-shadow:0 0 20px {glow_color};padding:10px;margin:10px;border-radius:10px;'>", unsafe_allow_html=True)
    cols = st.columns([1, 3])
    with cols[0]:
        if poster:
            st.image(poster)
        else:
            st.write("Sin póster")
    with cols[1]:
        st.markdown(f"### {title} ({int(year)})")
        st.write(f"⭐ Tu nota: {your_rating or 'N/A'}  |  IMDb: {imdb_rating or 'N/A'}")
        st.write(f"🎭 {genres}")
        st.write(f"🎬 {directors}")
        if awards:
            st.write(f"🏆 {awards}")
        if streaming:
            plats = ', '.join(streaming.get('platforms', [])) or "Sin datos de plataformas"
            st.write(f"📺 {plats}")
        if url and isinstance(url, str) and url.startswith('http'):
            st.markdown(f"[Ver en IMDb]({url})")
    st.markdown("</div>", unsafe_allow_html=True)
