# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import random
import re
import math
from urllib.parse import quote_plus

# CSS (dorado + ancho)
from .styles import GOLDEN_CSS

# --------- Versión de la app ----------
APP_VERSION = "v2.1.0"

# --------- Config APIs externas --------
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"
TMDB_SIMILAR_URL_TEMPLATE = "https://api.themoviedb.org/3/movie/{movie_id}/similar"

YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", None)
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# ==================== ESTILO / SIDEBAR ====================

def apply_theme_and_css():
    """Aplica el CSS dorado ancho + tipografías. (Look & feel del original)"""
    st.markdown(GOLDEN_CSS, unsafe_allow_html=True)

def show_changelog_sidebar():
    """Bloque de changelog/versión con un look más profesional."""
    with st.expander("📌 Información & cambios", expanded=False):
        st.write(
            f"- **Versión:** {APP_VERSION}\n"
            "- **Novedades UX:** tema dorado, grid más ancho, tarjetas pulidas.\n"
            "- **Arquitectura:** módulos separados (`modules/`).\n"
            "- **Rendimiento:** cache para TMDb/OMDb/YouTube."
        )
        st.caption("Sugerencias de mejoras visuales: tipografías, microanimaciones y hover en tarjetas ya incluidos.")

# ==================== CARGA DE DATOS ======================

@st.cache_data
def load_data(file_path_or_buffer):
    """Carga CSV de IMDb y normaliza columnas usadas por toda la app."""
    df = pd.read_csv(file_path_or_buffer)

    # Columnas esperadas/normalización
    df["Your Rating"] = pd.to_numeric(df.get("Your Rating"), errors="coerce")
    df["IMDb Rating"] = pd.to_numeric(df.get("IMDb Rating"), errors="coerce")

    if "Year" in df.columns:
        df["Year"] = (
            df["Year"].astype(str).str.extract(r"(\d{4})")[0].astype(float)
        )
    else:
        df["Year"] = None

    df["Genres"] = (df.get("Genres") or "").fillna("")
    df["Directors"] = (df.get("Directors") or "").fillna("")

    df["GenreList"] = df["Genres"].apply(
        lambda x: [] if pd.isna(x) or x == "" else str(x).split(", ")
    )

    if "Date Rated" in df.columns:
        df["Date Rated"] = pd.to_datetime(df["Date Rated"], errors="coerce").dt.date

    # Texto de búsqueda precomputado (para filtros rápidos de tus módulos)
    search_cols = [c for c in ["Title", "Original Title", "Directors", "Genres", "Year", "Your Rating", "IMDb Rating"] if c in df.columns]
    df["SearchText"] = (
        df[search_cols].astype(str).apply(lambda row: " ".join(row), axis=1).str.lower()
        if search_cols else ""
    )

    # Auxiliares usados en la lista AFI
    df["NormTitle"] = df["Title"].apply(normalize_title) if "Title" in df else ""
    df["YearInt"] = df["Year"].fillna(-1).astype(int) if "Year" in df else -1

    return df

# ================== HELPERS DE FORMATO ====================

def normalize_title(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

def fmt_year(y):
    if pd.isna(y): return ""
    return f"{int(float(y))}"

def fmt_rating(v):
    if pd.isna(v): return ""
    try: return f"{float(v):.1f}"
    except Exception: return str(v)

def get_rating_colors(rating):
    """Devuelve (border_color, glow_color) según rating."""
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

# ================== TMDb / YouTube / OMDb =================

def _coerce_year_for_tmdb(year):
    if year is None or pd.isna(year): return None
    try: return int(float(year))
    except Exception: return None

@st.cache_data
def get_tmdb_basic_info(title, year=None):
    """Devuelve {'id','poster_url','vote_average'} de TMDb para un título."""
    if TMDB_API_KEY is None or not title or pd.isna(title):
        return None
    params = {"api_key": TMDB_API_KEY, "query": str(title).strip()}
    y = _coerce_year_for_tmdb(year)
    if y is not None: params["year"] = y
    try:
        r = requests.get(TMDB_SEARCH_URL, params=params, timeout=4)
        if r.status_code != 200: return None
        results = r.json().get("results", [])
        if not results: return None
        m = results[0]
        return {
            "id": m.get("id"),
            "poster_url": f"{TMDB_IMAGE_BASE}{m['poster_path']}" if m.get("poster_path") else None,
            "vote_average": m.get("vote_average"),
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
        if r.status_code != 200: return None
        cdata = r.json().get("results", {}).get(country.upper())
        if not cdata: return None
        providers = set()
        for key in ["flatrate", "rent", "buy", "ads", "free"]:
            for item in cdata.get(key, []) or []:
                name = item.get("provider_name")
                if name: providers.add(name)
        return {"platforms": sorted(providers) if providers else [], "link": cdata.get("link")}
    except Exception:
        return None

@st.cache_data
def get_youtube_trailer_url(title, year=None):
    if YOUTUBE_API_KEY is None or not title or pd.isna(title):
        return None
    q = f"{title} trailer"
    try:
        if year is not None and not pd.isna(year):
            q += f" {int(float(year))}"
    except Exception:
        pass
    params = {
        "key": YOUTUBE_API_KEY, "part": "snippet", "q": q,
        "type": "video", "maxResults": 1, "videoEmbeddable": "true", "regionCode": "CL",
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

@st.cache_data
def get_omdb_awards(title, year=None):
    """Devuelve dict con resumen de premios (u {'error': ...})."""
    api_key = st.secrets.get("OMDB_API_KEY", None)
    if api_key is None: return {"error": "OMDB_API_KEY no está configurada en st.secrets."}
    if not title or pd.isna(title): return {"error": "Título vacío o inválido."}

    base_url = "https://www.omdbapi.com/"
    raw_title = str(title).strip()
    simple_title = re.sub(r"\s*\(.*?\)\s*$", "", raw_title).strip()
    y = None
    try:
        if year is not None and not pd.isna(year): y = int(float(year))
    except Exception:
        y = None

    def _query(params):
        try:
            r = requests.get(base_url, params=params, timeout=8)
            if r.status_code != 200: return {"error": f"HTTP {r.status_code} desde OMDb."}
            data = r.json()
            if data.get("Response") != "True":
                return {"error": data.get("Error", "Respuesta no válida de OMDb.")}
            return data
        except Exception as e:
            return {"error": f"Excepción OMDb: {e}"}

    # Búsqueda directa por título (dos variaciones) y, si no, por búsqueda/ID
    data, last_error = None, None
    for t in [raw_title, simple_title]:
        params = {"apikey": api_key, "type": "movie", "t": t}
        if y: params["y"] = y
        out = _query(params)
        if "error" in out: last_error = out["error"]
        else: data = out; break
    if data is None:
        params = {"apikey": api_key, "type": "movie", "s": simple_title}
        if y: params["y"] = y
        search = _query(params)
        if search and "error" not in search and "Search" in search:
            best = search["Search"][0]
            imdb_id = best.get("imdbID")
            if imdb_id:
                data = _query({"apikey": api_key, "i": imdb_id})
                if isinstance(data, dict) and "error" in data:
                    last_error = data["error"]
        elif search and "error" in search:
            last_error = search["error"]
    if data is None:
        return {"error": last_error or "No se encontró la película en OMDb."}
    if "error" in data:
        return {"error": data["error"]}

    awards_str = data.get("Awards", "") or ""
    if not awards_str or awards_str == "N/A":
        return {"raw": None, "oscars": 0, "emmys": 0, "baftas": 0, "golden_globes": 0,
                "palme_dor": False, "oscars_nominated": 0, "total_wins": 0, "total_nominations": 0}

    text_lower = awards_str.lower()
    oscars=emmys=baftas=golden_globes=oscars_nominated=total_wins=total_nominations=0
    palme_dor=False

    m = re.search(r"won\s+(\d+)\s+oscars?", text_lower) or re.search(r"won\s+(\d+)\s+oscar\b", text_lower)
    if m: oscars=int(m.group(1))
    m = re.search(r"nominated\s+for\s+(\d+)\s+oscars?", text_lower) or re.search(r"nominated\s+for\s+(\d+)\s+oscar\b", text_lower)
    if m: oscars_nominated=int(m.group(1))
    for pat in [r"won\s+(\d+)\s+primetime\s+emmys?", r"won\s+(\d+)\s+emmys?", r"won\s+(\d+)\s+emmy\b"]:
        m=re.search(pat,text_lower)
        if m: emmys=int(m.group(1)); break
    m=re.search(r"won\s+(\d+)[^\.]*bafta", text_lower)
    if m: baftas=int(m.group(1))
    elif "bafta" in text_lower: baftas=1
    m=re.search(r"won\s+(\d+)[^\.]*golden\s+globes?", text_lower) or re.search(r"won\s+(\d+)[^\.]*golden\s+globe\b", text_lower)
    if m: golden_globes=int(m.group(1))
    elif "golden globe" in text_lower: golden_globes=1
    if re.search(r"palme\s+d['’]or", text_lower): palme_dor=True
    m=re.search(r"(\d+)\s+wins?", text_lower)
    if m: total_wins=int(m.group(1))
    m=re.search(r"(\d+)\s+nominations?", text_lower)
    if m: total_nominations=int(m.group(1))

    return {
        "raw": awards_str,
        "oscars": oscars, "emmys": emmys, "baftas": baftas, "golden_globes": golden_globes,
        "palme_dor": palme_dor, "oscars_nominated": oscars_nominated,
        "total_wins": total_wins, "total_nominations": total_nominations,
    }

# ================== RECOMENDACIONES =======================

def recommend_from_catalog(df_all, seed_row, top_n=5):
    """Recomendaciones simples por géneros/directores/año/notas dentro del catálogo."""
    if df_all.empty: return pd.DataFrame()
    candidates = df_all.copy()
    if "Title" in candidates.columns and "Year" in candidates.columns:
        candidates = candidates[~((candidates["Title"] == seed_row.get("Title")) &
                                  (candidates["Year"] == seed_row.get("Year")))]
    seed_genres = set(seed_row.get("GenreList") or [])
    seed_dirs = {d.strip() for d in str(seed_row.get("Directors") or "").split(",") if d.strip()}
    seed_year = seed_row.get("Year")
    seed_rating = seed_row.get("Your Rating")

    scores=[]
    for idx, r in candidates.iterrows():
        g2=set(r.get("GenreList") or [])
        d2={d.strip() for d in str(r.get("Directors") or "").split(",") if d.strip()}
        score=0.0
        score += 2.0*len(seed_genres & g2)
        if seed_dirs & d2: score += 3.0
        y2=r.get("Year")
        if pd.notna(seed_year) and pd.notna(y2):
            score -= min(abs(seed_year - y2)/10.0, 3.0)
        r2=r.get("Your Rating")
        if pd.notna(seed_rating) and pd.notna(r2):
            score -= abs(seed_rating - r2)*0.3
        imdb_r2=r.get("IMDb Rating")
        if pd.notna(imdb_r2):
            score += (float(imdb_r2) - 6.5)*0.2
        scores.append((idx, score))
    if not scores: return pd.DataFrame()
    scores_sorted=sorted(scores, key=lambda x: x[1], reverse=True)
    top_indices=[idx for idx, sc in scores_sorted[:top_n] if sc>0]
    if not top_indices: return pd.DataFrame()
    recs=df_all.loc[top_indices].copy()
    score_map=dict(scores)
    recs["similarity_score"]=recs.index.map(score_map.get)
    return recs

# ================== UTILIDADES VARIAS =====================

@st.cache_data
def compute_awards_table(df_basic):
    """Construye tabla de premios vía OMDb para subconjunto de películas."""
    rows=[]
    for _, r in df_basic.iterrows():
        title=r.get("Title"); year=r.get("Year")
        awards=get_omdb_awards(title, year)
        if not isinstance(awards, dict) or "error" in awards: continue
        rows.append({
            "Title": title, "Year": year,
            "oscars": awards.get("oscars",0),
            "oscars_nominated": awards.get("oscars_nominated",0),
            "total_wins": awards.get("total_wins",0),
            "total_nominations": awards.get("total_nominations",0),
            "palme_dor": awards.get("palme_dor",False),
            "raw": awards.get("raw"),
        })
    if not rows:
        return pd.DataFrame(columns=[
            "Title","Year","oscars","oscars_nominated","total_wins","total_nominations","palme_dor","raw"
        ])
    return pd.DataFrame(rows)
