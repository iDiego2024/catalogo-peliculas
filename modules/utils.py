import streamlit as st
import pandas as pd
import requests
import re
from urllib.parse import quote_plus

# ========= Versión & changelog =========
APP_VERSION = "1.2.0"
CHANGELOG = {
    "1.2.0": [
        "Refactor modular (modules/*) con paridad visual.",
        "Restaura galería en cuadrícula, barra lateral y changelog.",
    ],
    "1.1.0": [
        "Pestaña 🏆 Premios Óscar, cruces con catálogo, rankings.",
    ],
    "1.0.0": [
        "Catálogo, filtros, galería, análisis, AFI y ¿Qué ver hoy?",
    ],
}

# ========= Tema/CSS =========
def apply_theme_and_css():
    primary_bg = "#020617"
    secondary_bg = "#020617"
    text_color = "#e5e7eb"
    card_bg = "rgba(15,23,42,0.9)"
    accent_color = "#eab308"
    accent_soft = "rgba(234,179,8,0.25)"
    accent_alt = "#38bdf8"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        :root {{
            --bg-primary: {primary_bg};
            --bg-secondary: {secondary_bg};
            --text-color: {text_color};
            --card-bg: {card_bg};
            --accent: {accent_color};
            --accent-soft: {accent_soft};
            --accent-alt: {accent_alt};
            --radius-lg: 14px;
            --radius-xl: 18px;
        }}
        html, body, .stApp {{
            background: radial-gradient(circle at top left, #0f172a 0%, #020617 40%, #000000 100%);
            color: var(--text-color);
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
        }}
        .main .block-container {{ max-width: 1200px; padding-top: 3.0rem; padding-bottom: 3rem; }}
        [data-testid="stSidebar"] > div:first-child {{
            background: linear-gradient(180deg, rgba(15,23,42,0.98), rgba(15,23,42,0.90));
            border-right: 1px solid rgba(148,163,184,0.25);
            box-shadow: 0 0 30px rgba(0,0,0,0.7);
        }}
        [data-testid="stSidebar"] * {{ color: #e5e7eb !important; font-size: 0.9rem; }}

        h1 {{
            text-transform: uppercase; font-weight: 800; font-size: 2.0rem !important;
            background: linear-gradient(90deg, var(--accent), var(--accent-alt));
            -webkit-background-clip: text; color: transparent; margin-top: 1.2rem; margin-bottom: 0.6rem;
            line-height: 1.25; text-align: left;
        }}

        .movie-gallery-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 18px; margin-top: 0.7rem;
        }}
        @media (max-width: 900px) {{
            .movie-gallery-grid {{ grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; }}
        }}
        .movie-card {{
            background: radial-gradient(circle at top left, rgba(15,23,42,0.9), rgba(15,23,42,0.85));
            border-radius: var(--radius-lg); padding: 14px 14px 12px 14px;
            border: 1px solid rgba(148,163,184,0.45); box-shadow: 0 18px 40px rgba(15,23,42,0.8);
        }}
        .movie-poster-frame {{
            width: 100%; aspect-ratio: 2/3; border-radius: 14px; overflow: hidden;
            background: radial-gradient(circle at top, #020617 0%, #000000 55%, #020617 100%);
            border: 1px solid rgba(148,163,184,0.5); position: relative; box-shadow: 0 14px 30px rgba(0,0,0,0.85);
        }}
        .movie-poster-img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
        .movie-poster-placeholder {{
            width: 100%; height: 100%; display:flex; align-items:center; justify-content:center;
            background: radial-gradient(circle at 15% 0%, rgba(250,204,21,0.12), rgba(15,23,42,1)),
                        radial-gradient(circle at 85% 100%, rgba(56,189,248,0.16), rgba(0,0,0,1));
        }}
        .movie-title {{ font-weight:600; letter-spacing:.04em; text-transform:uppercase; font-size:.86rem; color:#f9fafb; }}
        .movie-sub {{ font-size:.78rem; line-height:1.35; color:#cbd5f5; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def show_changelog_sidebar():
    st.sidebar.header("🧾 Versiones")
    with st.sidebar.expander("Ver changelog", expanded=False):
        for ver, notes in CHANGELOG.items():
            st.markdown(f"**v{ver}**")
            for n in notes:
                st.markdown(f"- {n}")
            st.markdown("---")

# ========= Utilidades de datos/UI =========
def normalize_title(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

@st.cache_data
def load_data(file_path_or_buffer):
    df = pd.read_csv(file_path_or_buffer)

    if "Your Rating" in df.columns:
        df["Your Rating"] = pd.to_numeric(df["Your Rating"], errors="coerce")
    else:
        df["Your Rating"] = None

    if "IMDb Rating" in df.columns:
        df["IMDb Rating"] = pd.to_numeric(df["IMDb Rating"], errors="coerce")
    else:
        df["IMDb Rating"] = None

    # Year sin comas (2,023 -> 2023)
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

    df["NormTitle"] = df["Title"].apply(normalize_title)
    df["YearInt"] = df["Year"].fillna(-1).astype(int)

    return df

def fmt_year(y):
    if pd.isna(y): return ""
    return f"{int(float(y))}"

def fmt_rating(v):
    if pd.isna(v): return ""
    try: return f"{float(v):.1f}"
    except Exception: return str(v)

def get_rating_colors(rating):
    try:
        r = float(rating)
    except Exception:
        return ("rgba(148,163,184,0.8)", "rgba(15,23,42,0.0)")
    if r >= 9:  return ("#22c55e", "rgba(34,197,94,0.55)")
    if r >= 8:  return ("#0ea5e9", "rgba(14,165,233,0.55)")
    if r >= 7:  return ("#a855f7", "rgba(168,85,247,0.50)")
    if r >= 6:  return ("#eab308", "rgba(234,179,8,0.45)")
    return ("#f97316", "rgba(249,115,22,0.45)")

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

# ========= APIs externas opcionales =========
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"
TMDB_SIMILAR_URL_TEMPLATE = "https://api.themoviedb.org/3/movie/{movie_id}/similar"

YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", None)
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

def _coerce_year_for_tmdb(year):
    if year is None or pd.isna(year):
        return None
    try:
        return int(float(year))
    except Exception:
        return None

@st.cache_data
def get_tmdb_basic_info(title, year=None):
    if TMDB_API_KEY is None or not title or pd.isna(title):
        return None
    title = str(title).strip()
    year_int = _coerce_year_for_tmdb(year)

    params = {"api_key": TMDB_API_KEY, "query": title}
    if year_int is not None:
        params["year"] = year_int

    try:
        r = requests.get(TMDB_SEARCH_URL, params=params, timeout=4)
        if r.status_code != 200:
            return None
        data = r.json()
        results = data.get("results", [])
        if not results:
            return None
        movie = results[0]
        return {
            "id": movie.get("id"),
            "poster_url": f"{TMDB_IMAGE_BASE}{movie.get('poster_path')}" if movie.get("poster_path") else None,
            "vote_average": movie.get("vote_average"),
        }
    except Exception:
        return None

@st.cache_data
def get_tmdb_providers(tmdb_id, country="CL"):
    if TMDB_API_KEY is None or not tmdb_id:
        return None
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/watch/providers"
        r = requests.get(url, params={"api_key": TMDB_API_KEY}, timeout=4)
        if r.status_code != 200:
            return None
        pdata = r.json()
        cdata = pdata.get("results", {}).get(country.upper())
        if not cdata:
            return None
        providers = set()
        for key in ["flatrate", "rent", "buy", "ads", "free"]:
            for item in cdata.get(key, []) or []:
                name = item.get("provider_name")
                if name:
                    providers.add(name)
        return {"platforms": sorted(list(providers)), "link": cdata.get("link")}
    except Exception:
        return None

@st.cache_data
def get_youtube_trailer_url(title, year=None, language_hint="es"):
    if YOUTUBE_API_KEY is None or not title or pd.isna(title):
        return None
    q = f"{title} trailer"
    try:
        if year is not None and not pd.isna(year):
            q += f" {int(float(year))}"
    except Exception:
        pass
    params = {
        "key": YOUTUBE_API_KEY, "part": "snippet", "q": q, "type": "video",
        "maxResults": 1, "videoEmbeddable": "true", "regionCode": "CL",
    }
    try:
        r = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=5)
        if r.status_code != 200:
            return None
        items = r.json().get("items", [])
        if not items:
            return None
        return f"https://www.youtube.com/watch?v={items[0]['id']['videoId']}"
    except Exception:
        return None

# ========= AFI =========
AFI_LIST = [
    {"Rank": 1, "Title": "Citizen Kane", "Year": 1941},
    {"Rank": 2, "Title": "The Godfather", "Year": 1972},
    {"Rank": 3, "Title": "Casablanca", "Year": 1942},
    # ... (lista completa si ya la tienes; si no, basta con estas para que funcione)
]

# ========= (Opcional) Premios via OMDb: helpers ligeros =========
def get_omdb_awards(title, year=None):
    api_key = st.secrets.get("OMDB_API_KEY", None)
    if api_key is None or not title or pd.isna(title):
        return None
    base_url = "https://www.omdbapi.com/"
    params = {"apikey": api_key, "t": str(title).strip(), "type": "movie"}
    try:
        if year is not None and not pd.isna(year):
            params["y"] = int(float(year))
    except Exception:
        pass
    try:
        r = requests.get(base_url, params=params, timeout=8)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("Response") != "True":
            return None
        return data.get("Awards")
    except Exception:
        return None
