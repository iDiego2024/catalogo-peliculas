# modules/utils.py
from __future__ import annotations
import re
from typing import Optional, Dict, Any

import pandas as pd
import streamlit as st
import requests

APP_VERSION = "v2.1.2"

# ───────────────────────────────────────────────────────────
# Estilos (tema + tablas)
# ───────────────────────────────────────────────────────────
def apply_theme_and_css() -> None:
    st.markdown("""
    <style>
    html, body, .stApp {
      background: radial-gradient(circle at top left, #0f172a 0%, #020617 40%, #000 100%);
      color: #e5e7eb;
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .main .block-container { max-width: 1200px; padding-top: 2.2rem; padding-bottom: 2rem; }
    @media (min-width:1500px){ .main .block-container{ max-width: 1400px; } }

    [data-testid="stSidebar"] > div:first-child {
      background: linear-gradient(180deg, rgba(15,23,42,.98), rgba(15,23,42,.90));
      border-right: 1px solid rgba(148,163,184,.25);
      box-shadow: 0 0 30px rgba(0,0,0,.7);
    }
    [data-testid="stSidebar"] * { color: #e5e7eb !important; }

    [data-testid="stDataFrame"]{
      border-radius:16px !important; border:1px solid rgba(148,163,184,.55);
      background: radial-gradient(circle at top left, rgba(15,23,42,.96), rgba(15,23,42,.88));
      box-shadow:0 0 0 1px rgba(15,23,42,.9), 0 22px 45px rgba(15,23,42,.95);
      overflow:hidden;
    }
    [data-testid="stDataFrame"] *{ color:#e5e7eb !important; font-size:.86rem; }
    [data-testid="stDataFrame"] thead tr{
      background:linear-gradient(90deg, rgba(15,23,42,.95), rgba(30,64,175,.85));
      text-transform:uppercase; letter-spacing:.08em;
    }
    [data-testid="stDataFrame"] tbody tr:hover{ background-color:rgba(234,179,8,.12) !important; }
    </style>
    """, unsafe_allow_html=True)

def show_changelog_sidebar() -> None:
    with st.sidebar.expander("🗒️ Changelog", expanded=False):
        st.markdown(
            "- **2.1.2**: Galería modular con cuadrícula y CSS pulido.\n"
            "- **2.1.1**: Estilos de tablas y métricas.\n"
            "- **2.1.0**: Refactor a módulos."
        )

# ───────────────────────────────────────────────────────────
# Data utils
# ───────────────────────────────────────────────────────────
def normalize_title(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

@st.cache_data
def load_data(file_path_or_buffer) -> pd.DataFrame:
    df = pd.read_csv(file_path_or_buffer)

    # Columnas básicas
    if "Your Rating" in df.columns:
        df["Your Rating"] = pd.to_numeric(df["Your Rating"], errors="coerce")
    else:
        df["Your Rating"] = pd.NA

    if "IMDb Rating" in df.columns:
        df["IMDb Rating"] = pd.to_numeric(df["IMDb Rating"], errors="coerce")
    else:
        df["IMDb Rating"] = pd.NA

    if "Year" in df.columns:
        df["Year"] = (
            df["Year"].astype(str).str.extract(r"(\d{4})")[0].astype(float)
        )
    else:
        df["Year"] = pd.NA

    # Asegurar columnas de texto
    if "Genres" not in df.columns:
        df["Genres"] = ""
    else:
        df["Genres"] = df["Genres"].fillna("")
    if "Directors" not in df.columns:
        df["Directors"] = ""
    else:
        df["Directors"] = df["Directors"].fillna("")

    # Listado de géneros
    df["GenreList"] = df["Genres"].apply(
        lambda x: [] if pd.isna(x) or x == "" else str(x).split(", ")
    )

    # Fecha
    if "Date Rated" in df.columns:
        df["Date Rated"] = pd.to_datetime(df["Date Rated"], errors="coerce").dt.date

    # Texto de búsqueda
    cols = [c for c in ["Title", "Original Title", "Directors", "Genres", "Year", "Your Rating", "IMDb Rating"] if c in df.columns]
    df["SearchText"] = (
        df[cols].astype(str).apply(lambda r: " ".join(r), axis=1).str.lower()
        if cols else ""
    )
    return df

def fmt_year(y) -> str:
    if pd.isna(y): return ""
    try: return f"{int(float(y))}"
    except Exception: return ""

def fmt_rating(v) -> str:
    if pd.isna(v): return ""
    try: return f"{float(v):.1f}"
    except Exception: return ""

def get_rating_colors(rating) -> tuple[str, str]:
    try:
        r = float(rating) if not pd.isna(rating) else None
    except Exception:
        r = None
    if r is None: return ("rgba(148,163,184,0.8)", "rgba(15,23,42,0.0)")
    if r >= 9: return ("#22c55e", "rgba(34,197,94,0.55)")
    if r >= 8: return ("#0ea5e9", "rgba(14,165,233,0.55)")
    if r >= 7: return ("#a855f7", "rgba(168,85,247,0.50)")
    if r >= 6: return ("#eab308", "rgba(234,179,8,0.45)")
    return ("#f97316", "rgba(249,115,22,0.45)")

# ───────────────────────────────────────────────────────────
# TMDb helpers
# ───────────────────────────────────────────────────────────
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"

def _coerce_year_for_tmdb(year):
    if year is None or pd.isna(year): return None
    try: return int(float(year))
    except Exception: return None

@st.cache_data
def get_tmdb_basic_info(title: str, year=None) -> Optional[Dict[str, Any]]:
    if TMDB_API_KEY is None: return None
    if not title: return None
    params = {"api_key": TMDB_API_KEY, "query": str(title).strip()}
    y = _coerce_year_for_tmdb(year)
    if y is not None: params["year"] = y
    try:
        r = requests.get(TMDB_SEARCH_URL, params=params, timeout=4)
        if r.status_code != 200: return None
        res = (r.json() or {}).get("results", [])
        if not res: return None
        movie = res[0]
        return {
            "id": movie.get("id"),
            "poster_url": f"{TMDB_IMAGE_BASE}{movie.get('poster_path')}" if movie.get("poster_path") else None,
            "vote_average": movie.get("vote_average"),
        }
    except Exception:
        return None

@st.cache_data
def get_tmdb_providers(tmdb_id: int, country: str = "CL") -> Optional[Dict[str, Any]]:
    if TMDB_API_KEY is None or not tmdb_id: return None
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/watch/providers"
        r = requests.get(url, params={"api_key": TMDB_API_KEY}, timeout=4)
        if r.status_code != 200: return None
        results = (r.json() or {}).get("results", {})
        cdata = results.get(country.upper())
        if not cdata: return None
        providers = set()
        for key in ["flatrate", "rent", "buy", "ads", "free"]:
            for it in cdata.get(key, []) or []:
                name = it.get("provider_name")
                if name: providers.add(name)
        return {"platforms": sorted(providers), "link": cdata.get("link")}
    except Exception:
        return None
