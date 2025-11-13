# modules/utils.py
from __future__ import annotations
import re
from typing import Optional, Dict, Any

import pandas as pd
import streamlit as st
import requests

APP_VERSION = "v2.1.3"

# ─────────────────────────────────────────
# Estilos (tema + tablas + hero dorado)
# ─────────────────────────────────────────
def apply_theme_and_css() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root{
      --bg1:#020617; --bg2:#0f172a; --txt:#e5e7eb;
      --card: rgba(15,23,42,.90);
      --gold:#facc15; --gold-soft: rgba(250,204,21,.28);
      --sky:#38bdf8;
    }

    html, body, .stApp {
      background: radial-gradient(circle at 10% 0%, var(--bg2) 0%, var(--bg1) 40%, #000 100%);
      color: var(--txt);
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .main .block-container {
      max-width: 1400px; padding-top: 2.2rem; padding-bottom: 2rem;
    }
    @media (min-width:1600px){
      .main .block-container { max-width: 1550px; }
    }

    [data-testid="stSidebar"] > div:first-child {
      background: linear-gradient(180deg, rgba(15,23,42,.98), rgba(15,23,42,.90));
      border-right: 1px solid rgba(148,163,184,.25);
      box-shadow: 0 0 30px rgba(0,0,0,.7);
    }
    [data-testid="stSidebar"] * { color:#e5e7eb !important; }

    .page-hero { margin-bottom: .6rem; }
    .golden-title{
      font-size:2.2rem; font-weight:800; letter-spacing:.03em; margin:.2rem 0 .2rem 0;
      background: linear-gradient(90deg, var(--gold) 0%, var(--sky) 60%);
      -webkit-background-clip: text; color: transparent;
      text-transform: uppercase;
    }
    .subtitle-line{
      color:#9ca3af; font-size:.92rem; letter-spacing:.02em; margin-top:.1rem;
    }

    /* Botones */
    .stButton button{
      border-radius: 999px!important; border:1px solid rgba(250,204,21,.7)!important;
      background: radial-gradient(circle at top left, var(--gold-soft), rgba(15,23,42,1))!important;
      color:#fdfbea!important; font-weight:600!important; letter-spacing:.06em; font-size:.78rem!important;
      padding:.45rem 1.1rem!important; box-shadow:0 10px 24px rgba(250,204,21,.3);
      transition: all .18s ease-out;
    }
    .stButton button:hover{
      transform: translateY(-1px);
      box-shadow:0 0 0 1px rgba(250,204,21,.7), 0 0 26px rgba(250,204,21,.75);
    }

    /* DataFrames */
    [data-testid="stDataFrame"]{
      border-radius:16px!important; border:1px solid rgba(148,163,184,.55);
      background: radial-gradient(circle at top left, rgba(15,23,42,.96), rgba(15,23,42,.88));
      box-shadow:0 0 0 1px rgba(15,23,42,.9), 0 22px 45px rgba(15,23,42,.95);
      overflow:hidden;
    }
    [data-testid="stDataFrame"] *{ color:#e5e7eb!important; font-size:.86rem; }
    [data-testid="stDataFrame"] thead tr{
      background:linear-gradient(90deg, rgba(15,23,42,.95), rgba(30,64,175,.85));
      text-transform:uppercase; letter-spacing:.08em;
    }
    [data-testid="stDataFrame"] tbody tr:hover{ background-color:rgba(234,179,8,.10)!important; }

    /* Galería */
    .poster-grid{
      display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:18px; width:100%;
    }
    @media (max-width:900px){
      .poster-grid{ grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:14px; }
    }
    .poster-card{
      background: radial-gradient(circle at top left, rgba(15,23,42,.92), rgba(15,23,42,.84));
      border:1px solid rgba(148,163,184,.45);
      border-radius:14px; padding:12px; transition:transform .15s, box-shadow .15s, border-color .15s;
    }
    .poster-card:hover{
      transform:translateY(-3px) scale(1.01);
      border-color:var(--gold);
      box-shadow:0 0 0 1px rgba(250,204,21,.7), 0 0 28px rgba(250,204,21,.8);
    }
    .poster-frame{
      width:100%; aspect-ratio:2/3; border-radius:12px; overflow:hidden;
      border:1px solid rgba(148,163,184,.5);
      background: radial-gradient(circle at top, #020617 0%, #000 55%, #020617 100%);
      box-shadow:0 14px 30px rgba(0,0,0,.85);
    }
    .poster-img{ width:100%; height:100%; object-fit:cover; display:block; transition:transform .25s; }
    .poster-card:hover .poster-img{ transform:scale(1.03); }
    .poster-placeholder{
      width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center;
      background:radial-gradient(circle at 15% 0%, rgba(250,204,21,.12), rgba(15,23,42,1)),
                 radial-gradient(circle at 85% 100%, rgba(56,189,248,.16), rgba(0,0,0,1));
    }
    .film-reel{ font-size:2rem; filter:drop-shadow(0 0 10px rgba(250,204,21,.9)) }
    .film-reel-text{ font-size:.78rem; letter-spacing:.14em; text-transform:uppercase; color:#e5e7eb }
    .poster-card h4{ margin:.45rem 0 .15rem 0; font-weight:700; letter-spacing:.02em; font-size:.94rem; color:#f9fafb; }
    .poster-card p{ margin:0; color:#cbd5f5; font-size:.84rem; }
    </style>
    """, unsafe_allow_html=True)

def show_changelog_sidebar() -> None:
    with st.sidebar.expander("🗒️ Changelog", expanded=False):
        st.markdown(
            "- **2.1.3**: Tema dorado, tarjetas con glow, tablas mejoradas y ancho mayor.\n"
            "- **2.1.2**: Galería modular y CSS base.\n"
            "- **2.1.1**: Estilos de tablas y métricas."
        )

# ─────────────────────────────────────────
# Data utils
# ─────────────────────────────────────────
def normalize_title(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

@st.cache_data
def load_data(file_path_or_buffer) -> pd.DataFrame:
    df = pd.read_csv(file_path_or_buffer)

    if "Your Rating" in df.columns:
        df["Your Rating"] = pd.to_numeric(df["Your Rating"], errors="coerce")
    else:
        df["Your Rating"] = pd.NA

    if "IMDb Rating" in df.columns:
        df["IMDb Rating"] = pd.to_numeric(df["IMDb Rating"], errors="coerce")
    else:
        df["IMDb Rating"] = pd.NA

    if "Year" in df.columns:
        df["Year"] = df["Year"].astype(str).str.extract(r"(\\d{4})")[0].astype(float)
    else:
        df["Year"] = pd.NA

    if "Genres" not in df.columns:
        df["Genres"] = ""
    else:
        df["Genres"] = df["Genres"].fillna("")

    if "Directors" not in df.columns:
        df["Directors"] = ""
    else:
        df["Directors"] = df["Directors"].fillna("")

    df["GenreList"] = df["Genres"].apply(
        lambda x: [] if pd.isna(x) or x == "" else str(x).split(", ")
    )

    if "Date Rated" in df.columns:
        df["Date Rated"] = pd.to_datetime(df["Date Rated"], errors="coerce").dt.date

    cols = [c for c in ["Title","Original Title","Directors","Genres","Year","Your Rating","IMDb Rating"] if c in df.columns]
    df["SearchText"] = (df[cols].astype(str).apply(lambda r: " ".join(r), axis=1).str.lower()) if cols else ""
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

# ─────────────────────────────────────────
# TMDb helpers
# ─────────────────────────────────────────
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
        for key in ["flatrate","rent","buy","ads","free"]:
            for it in cdata.get(key, []) or []:
                name = it.get("provider_name")
                if name: providers.add(name)
        return {"platforms": sorted(providers), "link": cdata.get("link")}
    except Exception:
        return None
