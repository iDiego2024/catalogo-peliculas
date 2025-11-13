# modules/utils.py
from __future__ import annotations
import re
import math
from typing import Iterable, Optional, Tuple, List, Dict

import pandas as pd
import requests
import streamlit as st
from urllib.parse import quote_plus

APP_VERSION = "v2.1.3"

# ======================== ESTILOS =========================
def apply_theme_and_css():
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

html, body, .stApp {
  background: radial-gradient(circle at top left, #0f172a 0%, #020617 40%, #000000 100%);
  color:#e5e7eb;
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}
.main .block-container { max-width: 1200px; padding-top: 1.25rem; }
h1 { 
  text-transform: uppercase; font-weight: 800; letter-spacing:.03em;
  background: linear-gradient(90deg,#facc15,#38bdf8); -webkit-background-clip:text; color:transparent;
}
[data-testid="stSidebar"] > div:first-child {
  background: linear-gradient(180deg, rgba(15,23,42,0.98), rgba(15,23,42,0.90));
  border-right: 1px solid rgba(148,163,184,0.25);
}
[data-testid="stSidebar"] * { color:#e5e7eb !important; }

.movie-gallery-grid {
  display:grid; gap:18px;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  margin-top: .7rem;
}
.poster-card {
  background: radial-gradient(circle at top left, rgba(15,23,42,.9), rgba(15,23,42,.85));
  border-radius: 14px; padding: 12px; border:1px solid rgba(148,163,184,.45);
  box-shadow: 0 18px 40px rgba(15,23,42,.8); overflow:hidden;
  transition: transform .18s ease-out, box-shadow .18s ease-out, border-color .18s ease-out;
}
.poster-card:hover { transform: translateY(-3px) scale(1.01); border-color:#facc15; }
.poster-card img { width:100%; height:auto; border-radius:12px; display:block; }
.poster-card h4 { margin:.4rem 0 .1rem; font-size:.95rem; font-weight:700; color:#f9fafb; }
.poster-card p { margin:0; font-size:.85rem; color:#cbd5f5; }
</style>
        """,
        unsafe_allow_html=True,
    )

# ======================== DATOS ==========================
@st.cache_data
def load_data(file_path_or_buffer) -> pd.DataFrame:
    df = pd.read_csv(file_path_or_buffer)

    # Tipos
    if "Your Rating" in df.columns:
        df["Your Rating"] = pd.to_numeric(df["Your Rating"], errors="coerce")
    if "IMDb Rating" in df.columns:
        df["IMDb Rating"] = pd.to_numeric(df["IMDb Rating"], errors="coerce")
    if "Year" in df.columns:
        df["Year"] = (
            df["Year"].astype(str).str.extract(r"(\d{4})")[0].astype(float)
        )

    # Columnas base
    if "Genres" not in df.columns:
        df["Genres"] = ""
    df["Genres"] = df["Genres"].fillna("")
    df["GenreList"] = df["Genres"].apply(
        lambda x: [] if pd.isna(x) or x == "" else str(x).split(", ")
    )
    if "Directors" not in df.columns:
        df["Directors"] = ""

    # Texto búsqueda
    search_cols = [c for c in ["Title","Original Title","Directors","Genres","Year","Your Rating","IMDb Rating"] if c in df.columns]
    if search_cols:
        df["SearchText"] = (
            df[search_cols].astype(str).apply(lambda r: " ".join(r), axis=1).str.lower()
        )
    else:
        df["SearchText"] = ""
    return df

# ===================== FORMATO / UTILS ===================
def fmt_year(y): 
    if pd.isna(y): return ""
    return f"{int(float(y))}"

def fmt_rating(v):
    if pd.isna(v): return ""
    try: return f"{float(v):.1f}"
    except Exception: return str(v)

def get_rating_colors(rating) -> Tuple[str,str]:
    try: r = float(rating)
    except Exception: return ("rgba(148,163,184,0.8)", "rgba(15,23,42,0.0)")
    if r >= 9:  return ("#22c55e", "rgba(34,197,94,0.55)")
    if r >= 8:  return ("#0ea5e9", "rgba(14,165,233,0.55)")
    if r >= 7:  return ("#a855f7", "rgba(168,85,247,0.50)")
    if r >= 6:  return ("#eab308", "rgba(234,179,8,0.45)")
    return ("#f97316", "rgba(249,115,22,0.45)")

def filters_summary_text(year_range, rating_range, selected_genres, selected_directors) -> str:
    g_txt = ", ".join(selected_genres) if selected_genres else "Todos"
    d_txt = ", ".join(selected_directors) if selected_directors else "Todos"
    return (
        f"**Filtros activos** → Años: {year_range[0]}–{year_range[1]} | "
        f"Mi nota: {rating_range[0]}–{rating_range[1]} | "
        f"Géneros: {g_txt} | Directores: {d_txt}"
    )

# ====================== TMDb & YouTube ====================
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"
TMDB_SIMILAR_URL = "https://api.themoviedb.org/3/movie/{id}/similar"

YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", None)
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

def _coerce_year_for_tmdb(year):
    if year is None or pd.isna(year): return None
    try: return int(float(year))
    except Exception: return None

@st.cache_data
def get_tmdb_basic_info(title, year=None):
    if TMDB_API_KEY is None or not title: return None
    params = {"api_key": TMDB_API_KEY, "query": str(title).strip()}
    y = _coerce_year_for_tmdb(year)
    if y: params["year"] = y
    try:
        r = requests.get(TMDB_SEARCH_URL, params=params, timeout=4)
        if r.status_code != 200: return None
        results = r.json().get("results", [])
        if not results: return None
        m = results[0]
        return {
            "id": m.get("id"),
            "poster_url": f"{TMDB_IMAGE_BASE}{m.get('poster_path')}" if m.get("poster_path") else None,
            "vote_average": m.get("vote_average"),
        }
    except Exception:
        return None

@st.cache_data
def get_tmdb_providers(tmdb_id, country="CL"):
    if TMDB_API_KEY is None or not tmdb_id: return None
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/watch/providers"
        r = requests.get(url, params={"api_key": TMDB_API_KEY}, timeout=4)
        if r.status_code != 200: return None
        cdata = r.json().get("results", {}).get(country.upper())
        if not cdata: return None
        providers = set()
        for key in ["flatrate","rent","buy","ads","free"]:
            for it in cdata.get(key,[]) or []:
                if it.get("provider_name"): providers.add(it["provider_name"])
        return {"platforms": sorted(list(providers)), "link": cdata.get("link")}
    except Exception:
        return None

@st.cache_data
def get_tmdb_similar_movies(tmdb_id, language="es-ES", max_results=8):
    if TMDB_API_KEY is None or not tmdb_id: return []
    try:
        url = TMDB_SIMILAR_URL.format(id=tmdb_id)
        r = requests.get(url, params={"api_key": TMDB_API_KEY, "language": language}, timeout=4)
        if r.status_code != 200: return []
        out=[]
        for m in r.json().get("results", [])[:max_results]:
            year=None
            if m.get("release_date"):
                try: year = int(m["release_date"][:4])
                except: pass
            out.append({
                "id": m.get("id"),
                "title": m.get("title") or m.get("name"),
                "year": year,
                "vote_average": m.get("vote_average"),
                "poster_url": f"{TMDB_IMAGE_BASE}{m['poster_path']}" if m.get("poster_path") else None,
            })
        return out
    except Exception:
        return []

@st.cache_data
def get_youtube_trailer_url(title, year=None):
    if YOUTUBE_API_KEY is None or not title: return None
    q = f"{title} trailer"
    try:
        if year not in (None, float("nan")): q += f" {int(float(year))}"
    except Exception:
        pass
    params = {
        "key": YOUTUBE_API_KEY, "part": "snippet", "q": q, "type":"video",
        "maxResults":1, "videoEmbeddable":"true", "regionCode":"CL",
    }
    try:
        r = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=5)
        if r.status_code != 200: return None
        items = r.json().get("items", [])
        if not items: return None
        vid = items[0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={vid}"
    except Exception:
        return None
