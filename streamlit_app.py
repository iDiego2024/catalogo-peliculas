import streamlit as st
import pandas as pd
import requests
import re

# ---------------- CONFIGURACIÓN GENERAL ---------------- #

st.set_page_config(page_title="🎬 Catálogo de Películas", layout="wide")

st.title("🎥 Mi catálogo de películas (IMDb)")
st.write(
    "Visualiza tu colección exportada desde IMDb. Filtra, busca y explora con información extendida de TMDb, OMDb y plataformas de streaming."
)

# ---------------- CONFIGURACIÓN DE APIs ---------------- #

TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
OMDB_API_KEY = st.secrets.get("OMDB_API_KEY", None)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"

# ---------------- FUNCIONES AUXILIARES ---------------- #

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
def load_data(file_path_or_buffer):
    df = pd.read_csv(file_path_or_buffer)
    df["Your Rating"] = pd.to_numeric(df.get("Your Rating", None), errors="coerce")
    df["IMDb Rating"] = pd.to_numeric(df.get("IMDb Rating", None), errors="coerce")
    df["Year"] = df["Year"].astype(str).str.extract(r"(\d{4})")[0].astype(float)
    df["Genres"] = df.get("Genres", "").fillna("")
    df["GenreList"] = df["Genres"].apply(lambda x: x.split(", ") if x else [])
    df["Directors"] = df.get("Directors", "").fillna("")
    return df

@st.cache_data
def get_poster_url(title, year=None):
    if TMDB_API_KEY is None:
        return None
    if not title:
        return None
    year_int = _coerce_year_for_tmdb(year)
    params = {"api_key": TMDB_API_KEY, "query": title}
    if year_int:
        params["year"] = year_int
    try:
        r = requests.get(TMDB_SEARCH_URL, params=params, timeout=2)
        if r.status_code != 200:
            return None
        results = r.json().get("results", [])
        if not results:
            return None
        poster_path = results[0].get("poster_path")
        return f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None
    except Exception:
        return None

@st.cache_data
def get_omdb_awards(title, year=None):
    if OMDB_API_KEY is None:
        return None
    params = {"apikey": OMDB_API_KEY, "t": title, "type": "movie"}
    if year and not pd.isna(year):
        params["y"] = int(float(year))
    try:
        r = requests.get("https://www.omdbapi.com/", params=params, timeout=5)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("Response") != "True":
            return None
        return data.get("Awards", "")
    except Exception:
        return None

@st.cache_data
def get_streaming_availability(title, year=None, country="CL"):
    if TMDB_API_KEY is None:
        return None
    try:
        year_int = _coerce_year_for_tmdb(year)
        search_params = {"api_key": TMDB_API_KEY, "query": title}
        if year_int:
            search_params["year"] = year_int
        r = requests.get(TMDB_SEARCH_URL, params=search_params, timeout=3)
        if r.status_code != 200:
            return None
        data = r.json().get("results", [])
        if not data:
            return None
        movie_id = data[0].get("id")
        r2 = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers",
            params={"api_key": TMDB_API_KEY},
            timeout=3,
        )
        if r2.status_code != 200:
            return None
        pdata = r2.json().get("results", {}).get(country.upper(), {})
        providers = set()
        for key in ["flatrate", "rent", "buy", "ads", "free"]:
            for item in pdata.get(key, []) or []:
                name = item.get("provider_name")
                if name:
                    providers.add(name)
        return {
            "platforms": sorted(list(providers)) if providers else [],
            "link": pdata.get("link"),
        }
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

# ---------------- CARGA DE DATOS ---------------- #

st.sidebar.header("📂 Datos")
uploaded = st.sidebar.file_uploader("Sube tu CSV de IMDb", type=["csv"])

if uploaded:
    df = load_data(uploaded)
else:
    df = load_data("peliculas.csv")

# ---------------- FILTROS ---------------- #

year_range = st.sidebar.slider("Rango de años", int(df["Year"].min()), int(df["Year"].max()), (1970, 2025))
rating_range = st.sidebar.slider("Tu nota", 0, 10, (0, 10))
all_genres = sorted({g for gl in df["GenreList"] for g in gl if g})
selected_genres = st.sidebar.multiselect("Géneros", all_genres)

filtered = df.copy()
filtered = filtered[(filtered["Year"] >= year_range[0]) & (filtered["Year"] <= year_range[1])]
filtered = filtered[(filtered["Your Rating"] >= rating_range[0]) & (filtered["Your Rating"] <= rating_range[1])]
if selected_genres:
    filtered = filtered[filtered["GenreList"].apply(lambda gl: all(g in gl for g in selected_genres))]

# ---------------- BÚSQUEDA ---------------- #

query = st.text_input("🔎 Buscar título, director o género...")
if query:
    q = query.lower()
    filtered = filtered[
        filtered.apply(
            lambda row: any(q in str(v).lower() for v in [row["Title"], row["Directors"], row["Genres"]]),
            axis=1,
        )
    ]

# ---------------- TABLA PRINCIPAL ---------------- #

st.markdown("## 📋 Resultados filtrados")
if not filtered.empty:
    st.dataframe(
        filtered[["Title", "Year", "Your Rating", "IMDb Rating", "Genres", "Directors"]],
        hide_index=True,
        use_container_width=True,
    )
else:
    st.warning("No hay películas que coincidan con los filtros o búsqueda.")
    st.stop()

# ---------------- GALERÍA DE CARÁTULAS ---------------- #

st.markdown("## 🎞️ Galería de películas")

cols = st.columns(4)
for i, (_, row) in enumerate(filtered.head(16).iterrows()):
    col = cols[i % 4]
    with col:
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

        st.markdown(
            f"""
            <div style="
                border: 2px solid {border_color};
                box-shadow: 0 0 20px {glow_color};
                border-radius: 12px;
                padding: 10px;
                margin-bottom: 16px;
                background: rgba(15,23,42,0.85);
            ">
            """,
            unsafe_allow_html=True,
        )
        if poster:
            st.image(poster, use_container_width=True)
        st.markdown(
            f"""
            <div style="color:#f9fafb;text-align:center">
                <b>{title}</b> ({int(year) if not pd.isna(year) else ""})<br>
                ⭐ Tu nota: {your_rating or 'N/A'} | IMDb: {imdb_rating or 'N/A'}<br>
                🎭 {genres}<br>
                🎬 {directors}<br>
                {f"🏆 {awards}<br>" if awards else ""}
                {f"📺 {', '.join(streaming.get('platforms', []))}<br>" if streaming and streaming.get('platforms') else ""}
                {f'<a href="{url}" target="_blank">Ver en IMDb</a>' if url and url.startswith('http') else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
