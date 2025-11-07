import streamlit as st
import pandas as pd
import math
import requests

# ============================ CONFIGURACIÓN BÁSICA ============================

st.set_page_config(
    page_title="Mi Catálogo de Cine",
    page_icon="🎬",
    layout="wide"
)

# ============================ CLAVES DE API ============================

TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"

OMDB_API_KEY = st.secrets.get("OMDB_API_KEY", None)

# ============================ FUNCIONES AUXILIARES ============================

@st.cache_data(ttl=86400)
def get_tmdb_basic_info(title, year=None):
    if TMDB_API_KEY is None:
        return None
    params = {"api_key": TMDB_API_KEY, "query": title, "include_adult": "false"}
    if year:
        params["year"] = year
    try:
        r = requests.get(TMDB_SEARCH_URL, params=params, timeout=6)
        data = r.json()
        if "results" in data and len(data["results"]) > 0:
            item = data["results"][0]
            return {
                "poster_url": f"{TMDB_IMAGE_BASE}{item['poster_path']}" if item.get("poster_path") else None,
                "overview": item.get("overview", ""),
                "tmdb_id": item.get("id"),
            }
    except Exception:
        pass
    return None


def fmt_rating(x):
    try:
        return f"{float(x):.1f}"
    except Exception:
        return ""


# ============================ ESTILO GLOBAL ============================

st.markdown(
    '''
    <style>
    html, body, .stApp {
        background: radial-gradient(circle at top left, #0f172a 0%, #020617 40%, #000000 100%);
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
    }
    .movie-card {
        background-color: rgba(15,23,42,0.6);
        border-radius: 14px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.35);
        padding: 10px;
        margin-bottom: 15px;
        transition: transform 0.15s ease-in-out;
        text-align: center;
    }
    .movie-card:hover {transform: scale(1.03);}
    .movie-poster {
        width: 100%;
        border-radius: 10px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.5);
    }
    .movie-title {
        margin-top: 6px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .movie-rating {
        color: #fbbf24;
        font-size: 0.85rem;
    }
    .movie-links {
        font-size: 0.8rem;
        margin-top: 4px;
    }
    .main .block-container {
        max-width: 1200px;
        padding-top: 4rem;
        padding-bottom: 3rem;
    }
    </style>
    ''',
    unsafe_allow_html=True,
)

# ============================ CARGA DE DATOS ============================

uploaded = st.sidebar.file_uploader("Sube tu archivo CSV de IMDb", type=["csv"])
if uploaded is not None:
    df = pd.read_csv(uploaded)
else:
    st.stop()

# ============================ FILTROS ============================

search_text = st.sidebar.text_input("🔍 Buscar título o director")
min_rating = st.sidebar.slider("⭐ Mínimo rating", 0.0, 10.0, 0.0, 0.5)
year_filter = st.sidebar.text_input("🎞️ Año (opcional)")

filtered_view = df.copy()
if search_text:
    mask = filtered_view["Title"].str.contains(search_text, case=False, na=False)
    filtered_view = filtered_view[mask]
if min_rating > 0:
    filtered_view = filtered_view[pd.to_numeric(filtered_view["Your Rating"], errors="coerce") >= min_rating]
if year_filter:
    filtered_view = filtered_view[filtered_view["Year"].astype(str).str.contains(year_filter)]

total_pelis = len(filtered_view)
st.markdown(f"### 🎬 Resultados ({total_pelis} películas)")

# ============================ GALERÍA ============================

if total_pelis == 0:
    st.info("No hay películas que coincidan con los filtros.")
else:
    page_size = st.slider("Películas por página", 12, 60, 30, step=6)
    num_pages = math.ceil(total_pelis / page_size)
    page = st.number_input("Página", 1, num_pages, 1)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_df = filtered_view.iloc[start_idx:end_idx]

    cols = st.columns(6)
    for i, (_, row) in enumerate(page_df.iterrows()):
        col = cols[i % 6]
        with col:
            titulo = row.get("Title", "Sin título")
            year = row.get("Year", "")
            nota = row.get("Your Rating", "")
            imdb_url = row.get("URL", "")

            info = get_tmdb_basic_info(titulo, year)
            poster_url = info["poster_url"] if info else None

            if poster_url:
                st.markdown(
                    f"<div class='movie-card'><img src='{poster_url}' class='movie-poster'>"
                    f"<div class='movie-title'>{titulo} ({year})</div>"
                    f"<div class='movie-rating'>⭐ {fmt_rating(nota)}</div>"
                    f"<div class='movie-links'><a href='{imdb_url}' target='_blank' style='color:#38bdf8;'>IMDb</a></div></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='movie-card'><div style='width:100%;aspect-ratio:2/3;border-radius:10px;background:#1e293b;color:#94a3b8;display:flex;align-items:center;justify-content:center;'>Sin póster</div>"
                    f"<div class='movie-title'>{titulo} ({year})</div>"
                    f"<div class='movie-rating'>⭐ {fmt_rating(nota)}</div></div>",
                    unsafe_allow_html=True,
                )
