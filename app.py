# app.py
import os
import re
import math
import random
from urllib.parse import quote_plus

import pandas as pd
import requests
import altair as alt
import streamlit as st

# ===================== Versión y changelog =====================
APP_VERSION = "1.2.0"

CHANGELOG = {
    "1.2.0": [
        "Óscar: usa Oscar_Data_1927_today.xlsx/csv si existe; fallback a full_data.csv",
        "Óscar: usa Year (YearInt) para filtrar; NomineeIds para entidades; Winner para ganador",
        "Óscar: elimina análisis por categoría (ganadores) solicitado",
        "Añadida vista por año/pósters con categorías y nominados (ganador resaltado)",
        "Lectura robusta y tolerante a columnas faltantes.",
    ],
    "1.1.3": [
        "Óscar: se usa exclusivamente full_data.csv (DLu/oscar_data).",
        "Óscar: ganadores resaltados en verde; tablas y gráficos por NomineeIds.",
        "Robustez: carga tolerante (on_bad_lines) y columnas ausentes no rompen.",
    ]
}

def _parse_ver_tuple(v: str):
    parts = [int(p) if p.isdigit() else 0 for p in re.split(r"[.\-+]", str(v))]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])

def since(ver: str) -> bool:
    return _parse_ver_tuple(APP_VERSION) >= _parse_ver_tuple(ver)

# ----------------- Configuración general -----------------
st.set_page_config(
    page_title=f"🎬 Mi catálogo de Películas · v{APP_VERSION}",
    layout="centered",
)

st.title("🎥 Mi catálogo de películas (IMDb)")

# ----------------- Config APIs externas -----------------
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"
TMDB_SIMILAR_URL_TEMPLATE = "https://api.themoviedb.org/3/movie/{movie_id}/similar"

YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", None)
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# ===================== UTILIDADES =====================

def normalize_title(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

def fmt_year(y):
    if pd.isna(y) or y == -1:
        return ""
    try:
        return str(int(float(y)))
    except Exception:
        return str(y)

def fmt_rating(v):
    if pd.isna(v):
        return ""
    try:
        return f"{float(v):.1f}"
    except Exception:
        return str(v)

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

# ----------------- TMDb helpers (poster + similares) -----------------
@st.cache_data
def get_tmdb_basic_info(title, year=None):
    if TMDB_API_KEY is None:
        return None
    if not title or pd.isna(title):
        return None
    try:
        params = {"api_key": TMDB_API_KEY, "query": str(title)}
        if year is not None and not pd.isna(year):
            try:
                params["year"] = int(float(year))
            except Exception:
                pass
        r = requests.get(TMDB_SEARCH_URL, params=params, timeout=4)
        if r.status_code != 200:
            return None
        data = r.json()
        results = data.get("results", [])
        if not results:
            return None
        movie = results[0]
        poster_path = movie.get("poster_path")
        return {
            "id": movie.get("id"),
            "poster_url": f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None,
            "vote_average": movie.get("vote_average"),
        }
    except Exception:
        return None

@st.cache_data
def get_tmdb_similar_movies(tmdb_id, language="es-ES", max_results=10):
    if TMDB_API_KEY is None or not tmdb_id:
        return []
    try:
        url = TMDB_SIMILAR_URL_TEMPLATE.format(movie_id=tmdb_id)
        params = {"api_key": TMDB_API_KEY, "language": language, "page": 1}
        r = requests.get(url, params=params, timeout=4)
        if r.status_code != 200:
            return []
        data = r.json()
        results = data.get("results", [])[:max_results]
        out = []
        for m in results:
            out.append({
                "id": m.get("id"),
                "title": m.get("title") or m.get("name"),
                "year": (m.get("release_date") or "")[:4] if m.get("release_date") else None,
                "vote_average": m.get("vote_average"),
                "poster_url": f"{TMDB_IMAGE_BASE}{m['poster_path']}" if m.get("poster_path") else None,
            })
        return out
    except Exception:
        return []

# ----------------- OMDb awards parser (existing) -----------------
@st.cache_data
def get_omdb_awards(title, year=None):
    api_key = st.secrets.get("OMDB_API_KEY", None)
    if api_key is None:
        return {"error": "OMDB_API_KEY no configurada en st.secrets."}
    if not title:
        return {"error": "Título vacío o inválido."}
    base_url = "https://www.omdbapi.com/"
    raw_title = str(title).strip()
    simple_title = re.sub(r"\s*\(.*?\)\s*$", "", raw_title).strip()
    year_int = None
    try:
        if year is not None and not pd.isna(year):
            year_int = int(float(year))
    except Exception:
        year_int = None

    def _query(params):
        try:
            r = requests.get(base_url, params=params, timeout=8)
            if r.status_code != 200:
                return {"error": f"HTTP {r.status_code} desde OMDb."}
            data = r.json()
            if data.get("Response") != "True":
                return {"error": data.get("Error", "Respuesta no válida de OMDb.")}
            return data
        except Exception as e:
            return {"error": f"Excepción al llamar a OMDb: {e}"}

    data = None
    for t in [raw_title, simple_title]:
        params = {"apikey": api_key, "t": t, "type": "movie"}
        if year_int:
            params["y"] = year_int
        candidate = _query(params)
        if candidate and "error" not in candidate:
            data = candidate
            break

    if data is None:
        params = {"apikey": api_key, "s": simple_title, "type": "movie"}
        if year_int:
            params["y"] = year_int
        search = _query(params)
        if search and "error" not in search and "Search" in search:
            best = search["Search"][0]
            imdb_id = best.get("imdbID")
            if imdb_id:
                data = _query({"apikey": api_key, "i": imdb_id})
                if isinstance(data, dict) and "error" in data:
                    data = None

    if data is None:
        return {"raw": None, "oscars": 0, "oscars_nominated": 0, "total_wins": 0, "total_nominations": 0, "palme_dor": False}

    awards_str = data.get("Awards", "")
    if not awards_str or awards_str == "N/A":
        return {"raw": None, "oscars": 0, "oscars_nominated": 0, "total_wins": 0, "total_nominations": 0, "palme_dor": False}

    text_lower = awards_str.lower()
    oscars = 0
    oscars_nominated = 0
    total_wins = 0
    total_nominations = 0
    palme_dor = False

    m_osc = re.search(r"won\s+(\d+)\s+oscars?", text_lower)
    if m_osc:
        oscars = int(m_osc.group(1))
    m_noms = re.search(r"(\d+)\s+nominations?", text_lower)
    if m_noms:
        total_nominations = int(m_noms.group(1))
    m_wins = re.search(r"(\d+)\s+wins?", text_lower)
    if m_wins:
        total_wins = int(m_wins.group(1))
    if re.search(r"palme\s+d['’]or", text_lower):
        palme_dor = True

    m_osc_nom = re.search(r"nominated\s+for\s+(\d+)\s+oscars?", text_lower)
    if m_osc_nom:
        oscars_nominated = int(m_osc_nom.group(1))

    return {"raw": awards_str, "oscars": oscars, "oscars_nominated": oscars_nominated, "total_wins": total_wins, "total_nominations": total_nominations, "palme_dor": palme_dor}

# ----------------- Carga catálogo de usuario (peliculas.csv u upload) -----------------
@st.cache_data
def load_data(file_path_or_buffer):
    df = pd.read_csv(file_path_or_buffer)
    # normalizaciones
    if "Your Rating" in df.columns:
        df["Your Rating"] = pd.to_numeric(df["Your Rating"], errors="coerce")
    else:
        df["Your Rating"] = None
    if "IMDb Rating" in df.columns:
        df["IMDb Rating"] = pd.to_numeric(df["IMDb Rating"], errors="coerce")
    else:
        df["IMDb Rating"] = None
    if "Year" in df.columns:
        df["Year"] = df["Year"].astype(str).str.extract(r"(\d{4})")[0].astype(float)
    else:
        df["Year"] = None
    if "Genres" not in df.columns:
        df["Genres"] = ""
    if "Directors" not in df.columns:
        df["Directors"] = ""
    df["Genres"] = df["Genres"].fillna("")
    df["GenreList"] = df["Genres"].apply(lambda x: [] if pd.isna(x) or x == "" else str(x).split(", "))
    if "Date Rated" in df.columns:
        df["Date Rated"] = pd.to_datetime(df["Date Rated"], errors="coerce").dt.date
    search_cols = []
    for c in ["Title", "Original Title", "Directors", "Genres", "Year", "Your Rating", "IMDb Rating"]:
        if c in df.columns:
            search_cols.append(c)
    if search_cols:
        df["SearchText"] = df[search_cols].astype(str).apply(lambda row: " ".join(row), axis=1).str.lower()
    else:
        df["SearchText"] = ""
    return df

# ----------------- Carga robusta de datos de Óscar -----------------
@st.cache_data
def find_oscar_file():
    candidates = [
        "Oscar_Data_1927_today.xlsx",
        "Oscar_Data_1927_today.csv",
        "Oscar_Data_1927_today.xls",
        "full_data.csv",
        "full_data.xlsx"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    # busco en /mnt/data (entorno de Colab/runner)
    alt_paths = [os.path.join("/mnt/data", c) for c in candidates]
    for p in alt_paths:
        if os.path.exists(p):
            return p
    return None

@st.cache_data
def load_full_data(path_hint=None):
    """
    Carga tolerante del dataset de Óscar.
    Acepta Excel o CSV. Normaliza columnas: Film, Name/Nominee, NomineeIds, Winner, Year.
    Devuelve DataFrame con columnas añadidas:
        - YearInt (int)
        - IsWinner (bool)
        - NomineeIdsList (list)
        - NormFilm (normalized title)
        - CanonCat (CanonicalCategory o Category)
    """
    if path_hint is None:
        path = find_oscar_file()
    else:
        path = path_hint if os.path.exists(path_hint) else find_oscar_file()
    if path is None:
        return pd.DataFrame()

    # try excel then csv (pandas auto-detection)
    try:
        if str(path).lower().endswith((".xls", ".xlsx")):
            dff = pd.read_excel(path)
        else:
            # try read_csv with python engine robustly
            dff = pd.read_csv(path, sep=None, engine="python", on_bad_lines="skip")
    except Exception:
        try:
            dff = pd.read_csv(path, on_bad_lines="skip")
        except Exception:
            # último recurso: leer como excel (pandas intentará)
            try:
                dff = pd.read_excel(path)
            except Exception:
                return pd.DataFrame()

    # normalize column names
    dff.columns = [str(c).strip() for c in dff.columns]
    idx = dff.index

    def col(name, default=""):
        return dff[name] if name in dff.columns else pd.Series([default] * len(dff), index=idx)

    # canonical category: prefer CanonicalCategory then Class then Category
    if "CanonicalCategory" in dff.columns:
        dff["CanonCat"] = dff["CanonicalCategory"].astype(str)
    elif "Class" in dff.columns:
        dff["CanonCat"] = dff["Class"].astype(str)
    else:
        dff["CanonCat"] = col("Category").astype(str)

    # Film
    dff["Film"] = col("Film").fillna("").astype(str)

    # Nominee / Name
    if "Nominee" in dff.columns:
        dff["Nominee"] = col("Nominee").fillna("").astype(str)
    elif "Name" in dff.columns:
        dff["Nominee"] = col("Name").fillna("").astype(str)
    elif "Nominees" in dff.columns:
        dff["Nominee"] = col("Nominees").fillna("").astype(str)
    else:
        dff["Nominee"] = ""

    # Year: usar Year (año de la película). Si no está, intentar Ceremony.
    if "Year" in dff.columns:
        yr = pd.to_numeric(dff["Year"], errors="coerce")
    elif "year" in dff.columns:
        yr = pd.to_numeric(dff["year"], errors="coerce")
    elif "Ceremony" in dff.columns:
        yr = pd.to_numeric(dff["Ceremony"], errors="coerce")
    else:
        yr = pd.Series([None] * len(dff))
    dff["YearInt"] = yr.fillna(-1).astype(int)

    # Winner -> IsWinner boolean
    if "Winner" in dff.columns:
        win_raw = dff["Winner"].astype(str).fillna("").str.lower()
    elif "winner" in dff.columns:
        win_raw = dff["winner"].astype(str).fillna("").str.lower()
    else:
        # fallback: maybe there's a column named 'IsWinner' or 'Won' or 'Result'
        if "IsWinner" in dff.columns:
            win_raw = dff["IsWinner"].astype(str).fillna("").str.lower()
        elif "Won" in dff.columns:
            win_raw = dff["Won"].astype(str).fillna("").str.lower()
        else:
            win_raw = pd.Series([""] * len(dff), index=idx)
    dff["IsWinner"] = win_raw.isin(["1", "true", "yes", "winner", "won", "ganador", "ganadora", "True", "TRUE", "yes"])

    # NomineeIds -> list
    if "NomineeIds" in dff.columns:
        base_ids = dff["NomineeIds"].fillna("").astype(str)
    elif "NomId" in dff.columns:
        base_ids = dff["NomId"].fillna("").astype(str)
    else:
        base_ids = pd.Series([""] * len(dff), index=idx)
    dff["NomineeIdsList"] = base_ids.apply(lambda s: [x.strip() for x in re.split(r"[;,]", s) if x.strip()])

    # Normalized film for cross-match
    dff["NormFilm"] = dff["Film"].apply(normalize_title)

    # keep useful columns only (but keep originals)
    # return
    return dff

def attach_catalog_to_full(osc_df, my_catalog_df):
    out = osc_df.copy()
    if my_catalog_df is None or my_catalog_df.empty:
        out["InMyCatalog"] = False
        out["MyRating"] = None
        out["MyIMDb"] = None
        out["CatalogURL"] = None
        return out
    cat = my_catalog_df.copy()
    if "NormTitle" not in cat.columns:
        cat["NormTitle"] = cat.get("Title", "").apply(normalize_title)
    if "Year" in cat.columns:
        cat["YearInt"] = cat["Year"].fillna(-1).astype(float).astype(int)
    else:
        cat["YearInt"] = -1
    merged = out.merge(cat[["NormTitle", "YearInt", "Your Rating", "IMDb Rating", "URL"]],
                       left_on=["NormFilm", "YearInt"],
                       right_on=["NormTitle", "YearInt"], how="left", suffixes=("", "_cat"))
    merged["InMyCatalog"] = merged["URL"].notna()
    merged["MyRating"] = merged.get("Your Rating")
    merged["MyIMDb"] = merged.get("IMDb Rating")
    merged["CatalogURL"] = merged.get("URL")
    merged = merged.drop(columns=["NormTitle", "Your Rating", "IMDb Rating", "URL"], errors="ignore")
    return merged

# ===================== INTERFAZ USUARIO Y CARGAS =====================

# Sidebar: datos y carga del CSV de IMDb del usuario
st.sidebar.header("📂 Datos")
uploaded = st.sidebar.file_uploader("Sube tu CSV de IMDb (opcional) para cruzar con premios", type=["csv"])
if uploaded is not None:
    df = load_data(uploaded)
else:
    try:
        df = load_data("peliculas.csv")
    except Exception:
        # csv no encontrado -> crear DF vacío pero funcional
        df = pd.DataFrame(columns=["Title", "Year", "Your Rating", "IMDb Rating", "Genres", "Directors", "URL"])
        st.sidebar.info("No se subió 'peliculas.csv' en el repo; la app funcionará sin cruce con tu catálogo.")

if "Title" not in df.columns:
    st.error("El CSV de tu catálogo debe contener una columna 'Title' para funcionar correctamente.")
    # No hacemos st.stop() — la parte de Óscar puede seguir funcionando independientemente

df["NormTitle"] = df.get("Title", "").apply(normalize_title)
if "Year" in df.columns:
    try:
        df["YearInt"] = df["Year"].fillna(-1).astype(int)
    except Exception:
        df["YearInt"] = -1
else:
    df["YearInt"] = -1

# ----------------- Tema y estilo (mantengo tu CSS ya usado) -----------------
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
        --radius-lg: 12px;
        --radius-xl: 16px;
    }}

    html, body, .stApp {{
        background: radial-gradient(circle at top left, #0f172a 0%, #020617 40%, #000000 100%);
        color: var(--text-color);
        font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    .main .block-container {{
        max-width: 1200px;
        padding-top: 2.8rem;
        padding-bottom: 2rem;
    }}

    [data-testid="stSidebar"] > div:first-child {{
        background: linear-gradient(180deg, rgba(15,23,42,0.98), rgba(15,23,42,0.90));
        border-right: 1px solid rgba(148,163,184,0.25);
    }}

    h1 {{
        font-weight: 800;
        font-size: 2.0rem !important;
        background: linear-gradient(90deg, var(--accent), var(--accent-alt));
        -webkit-background-clip: text;
        color: transparent;
    }}

    .movie-card {{
        background: radial-gradient(circle at top left, rgba(15,23,42,0.9), rgba(15,23,42,0.85));
        border-radius: var(--radius-lg);
        padding: 12px;
        margin-bottom: 12px;
        border: 1px solid rgba(148,163,184,0.45);
    }}

    [data-testid="stDataFrame"] {{
        border-radius: var(--radius-xl) !important;
        border: 1px solid rgba(148,163,184,0.6);
        background: radial-gradient(circle at top left, rgba(15,23,42,0.96), rgba(15,23,42,0.88));
    }}

    </style>
    """, unsafe_allow_html=True
)

# ----------------- Opciones visuales / TMDb / OMDb -----------------
st.sidebar.header("🖼️ Opciones de visualización")
show_posters_fav = st.sidebar.checkbox("Mostrar pósters TMDb en mis favoritas (nota ≥ 9)", value=True)
st.sidebar.header("🌐 TMDb")
use_tmdb_gallery = st.sidebar.checkbox("Usar TMDb en la galería visual", value=True)
st.sidebar.header("🎬 Tráilers")
show_trailers = st.sidebar.checkbox("Mostrar tráiler de YouTube (si hay API key)", value=True)
st.sidebar.header("⚙️ Opciones avanzadas")
show_awards = st.sidebar.checkbox("Consultar premios en OMDb (más lento)", value=False)
if show_awards:
    st.sidebar.caption("Consultar premios para muchas películas puede tardar y consumir cuota OMDb.")

# ----------------- Filtros generales (catálogo) -----------------
st.sidebar.header("🎛️ Filtros del catálogo")
if "Year" in df.columns and df["Year"].notna().any():
    try:
        min_year = int(df["Year"].min())
        max_year = int(df["Year"].max())
    except Exception:
        min_year, max_year = 1900, pd.Timestamp.now().year
    year_range = st.sidebar.slider("Rango de años (catálogo)", min_year, max_year, (min_year, max_year))
else:
    year_range = (1900, pd.Timestamp.now().year)

if "Your Rating" in df.columns and df["Your Rating"].notna().any():
    min_rating = int(df["Your Rating"].min())
    max_rating = int(df["Your Rating"].max())
    rating_range = st.sidebar.slider("Mi nota (Your Rating)", min_rating, max_rating, (min_rating, max_rating))
else:
    rating_range = (0, 10)

all_genres = sorted(set(g for sub in df.get("GenreList", pd.Series([[]]*len(df))) for g in sub if g))
selected_genres = st.sidebar.multiselect("Géneros", options=all_genres)
all_directors = sorted(set(d.strip() for d in df.get("Directors", pd.Series([""]*len(df))) if str(d).strip()))
selected_directors = st.sidebar.multiselect("Directores", options=all_directors)
order_by = st.sidebar.selectbox("Ordenar por", ["Your Rating", "IMDb Rating", "Year", "Title", "Aleatorio"])
order_asc = st.sidebar.checkbox("Orden ascendente", value=False)

# Changelog al final de la sidebar
st.sidebar.markdown("---")
st.sidebar.header("🧾 Versiones")
with st.sidebar.expander("Ver changelog", expanded=False):
    for ver, notes in CHANGELOG.items():
        st.markdown(f"**v{ver}**")
        for n in notes:
            st.markdown(f"- {n}")
        st.markdown("---")

# ----------------- Aplicar filtros al catálogo -----------------
filtered = df.copy()
if "Year" in filtered.columns:
    filtered = filtered[(filtered["Year"] >= year_range[0]) & (filtered["Year"] <= year_range[1])]
if "Your Rating" in filtered.columns:
    filtered = filtered[(filtered["Your Rating"] >= rating_range[0]) & (filtered["Your Rating"] <= rating_range[1])]
if selected_genres:
    filtered = filtered[filtered["GenreList"].apply(lambda gl: all(g in gl for g in selected_genres))]
if selected_directors:
    def _matches_any_director(cell):
        if pd.isna(cell):
            return False
        dirs = [d.strip() for d in str(cell).split(",") if d.strip()]
        return any(d in dirs for d in selected_directors)
    filtered = filtered[filtered["Directors"].apply(_matches_any_director)]

st.caption(
    f"Filtros activos → Años: {year_range[0]}–{year_range[1]} | Mi nota: {rating_range[0]}–{rating_range[1]} | "
    f"Géneros: {', '.join(selected_genres) if selected_genres else 'Todos'} | "
    f"Directores: {', '.join(selected_directors) if selected_directors else 'Todos'}"
)

# ----------------- BUSCAR en catálogo -----------------
st.markdown("## 🔎 Búsqueda en mi catálogo (filtros aplicados)")
search_query = st.text_input("Buscar por título, director, género, año o calificaciones", placeholder="Escribe cualquier cosa…")
def apply_search(df_in, query):
    if not query:
        return df_in
    q = query.strip().lower()
    if "SearchText" not in df_in.columns:
        return df_in
    return df_in[df_in["SearchText"].str.contains(q, na=False, regex=False)]
filtered_view = apply_search(filtered.copy(), search_query)
if order_by == "Aleatorio":
    if not filtered_view.empty:
        filtered_view = filtered_view.sample(frac=1)
elif order_by in filtered_view.columns:
    filtered_view = filtered_view.sort_values(order_by, ascending=order_asc)

# ----------------- Pestañas principales -----------------
tab_catalog, tab_analysis, tab_afi, tab_awards, tab_what = st.tabs(["🎬 Catálogo", "📊 Análisis", "🏆 Lista AFI", "🏆 Premios Óscar", "🎲 ¿Qué ver hoy?"])

# ============================================================
# TAB 1 - CATÁLOGO
# ============================================================
with tab_catalog:
    st.markdown("## 📈 Resumen de resultados")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Películas tras filtros + búsqueda", len(filtered_view))
    with c2:
        if "Your Rating" in filtered_view.columns and filtered_view["Your Rating"].notna().any():
            st.metric("Promedio de mi nota", f"{filtered_view['Your Rating'].mean():.2f}")
        else:
            st.metric("Promedio de mi nota", "N/A")
    with c3:
        if "IMDb Rating" in filtered_view.columns and filtered_view["IMDb Rating"].notna().any():
            st.metric("Promedio IMDb", f"{filtered_view['IMDb Rating'].mean():.2f}")
        else:
            st.metric("Promedio IMDb", "N/A")

    st.markdown("### 📚 Tabla de resultados")
    cols_to_show = [c for c in ["Title", "Year", "Your Rating", "IMDb Rating", "Genres", "Directors", "Date Rated", "URL"] if c in filtered_view.columns]
    table_df = filtered_view[cols_to_show].copy()
    display_df = table_df.copy()
    if "Year" in display_df.columns:
        display_df["Year"] = display_df["Year"].apply(fmt_year)
    if "Your Rating" in display_df.columns:
        display_df["Your Rating"] = display_df["Your Rating"].apply(fmt_rating)
    if "IMDb Rating" in display_df.columns:
        display_df["IMDb Rating"] = display_df["IMDb Rating"].apply(fmt_rating)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    csv_filtrado = table_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar resultados filtrados (CSV)", data=csv_filtrado, file_name="mis_peliculas_filtradas.csv", mime="text/csv")

    # Galería
    st.markdown("---")
    st.markdown("## 🧱 Galería visual (pósters en grid por páginas)")
    total_pelis = len(filtered_view)
    if total_pelis == 0:
        st.info("No hay películas bajo los filtros + búsqueda actuales para la galería.")
    else:
        page_size = st.slider("Películas por página en la galería", min_value=12, max_value=60, value=24, step=12, key="gallery_page_size")
        num_pages = max(math.ceil(total_pelis / page_size), 1)
        if "gallery_current_page" not in st.session_state:
            st.session_state.gallery_current_page = 1
        if st.session_state.gallery_current_page > num_pages:
            st.session_state.gallery_current_page = num_pages
        if st.session_state.gallery_current_page < 1:
            st.session_state.gallery_current_page = 1
        col_nav1, col_nav2, col_nav3 = st.columns([1,2,1])
        with col_nav1:
            if st.button("◀ Anterior", disabled=st.session_state.gallery_current_page<=1, key="gallery_prev_top"):
                st.session_state.gallery_current_page -= 1
        with col_nav3:
            if st.button("Siguiente ▶", disabled=st.session_state.gallery_current_page>=num_pages, key="gallery_next_top"):
                st.session_state.gallery_current_page += 1
        with col_nav2:
            st.caption(f"Página {st.session_state.gallery_current_page} de {num_pages}")
        current_page = st.session_state.gallery_current_page
        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        page_df = filtered_view.iloc[start_idx:end_idx].copy()

        cards_html = ['<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px">']
        for _, row in page_df.iterrows():
            titulo = row.get("Title", "Sin título")
            year = row.get("Year", "")
            nota = row.get("Your Rating", "")
            imdb_rating = row.get("IMDb Rating", "")
            genres = row.get("Genres", "")
            directors = row.get("Directors", "")
            url = row.get("URL", "")
            border_color, glow_color = get_rating_colors(nota)
            poster_html = ""
            if use_tmdb_gallery:
                tmdb = get_tmdb_basic_info(titulo, year)
                poster_url = tmdb.get("poster_url") if tmdb else None
            else:
                poster_url = None
            if poster_url:
                poster_html = f'<div style="width:100%;aspect-ratio:2/3;border-radius:10px;overflow:hidden;border:1px solid rgba(255,255,255,0.05)"><img src="{poster_url}" style="width:100%;height:100%;object-fit:cover"></div>'
            else:
                poster_html = '<div style="width:100%;aspect-ratio:2/3;border-radius:10px;display:flex;align-items:center;justify-content:center;background:#0f172a;color:#9ca3af">Sin póster</div>'
            cards_html.append(f"""
<div class="movie-card" style="border-color:{border_color};box-shadow:0 0 20px {glow_color}">
  {poster_html}
  <div style="margin-top:8px;font-weight:600">{titulo} {f'({fmt_year(year)})' if pd.notna(year) and year!='' else ''}</div>
  <div style="font-size:0.85rem;color:#bfc8d8">{genres}</div>
  <div style="font-size:0.85rem;color:#aab8c8">{directors}</div>
  <div style="margin-top:6px">{('⭐ Mi nota: '+fmt_rating(nota)) if pd.notna(nota) else ''}</div>
  <div style="margin-top:6px">{f'<a href=\"{url}\" target=\"_blank\">Ver en IMDb</a>' if isinstance(url,str) and url.startswith('http') else ''}</div>
</div>
""")
        cards_html.append("</div>")
        st.markdown("\n".join(cards_html), unsafe_allow_html=True)

# ============================================================
# TAB 2 - ANÁLISIS
# ============================================================
with tab_analysis:
    st.markdown("## 📊 Análisis y tendencias (según filtros, sin búsqueda)")
    st.caption("Los gráficos usan sólo los filtros de la barra lateral (no la búsqueda de texto).")
    with st.expander("Ver análisis y tendencias", expanded=False):
        if filtered.empty:
            st.info("No hay datos bajo los filtros actuales para mostrar gráficos.")
        else:
            # Películas por año
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Películas por año**")
                by_year = (filtered[filtered["Year"].notna()].groupby("Year").size().reset_index(name="Count").sort_values("Year"))
                if not by_year.empty:
                    by_year_display = by_year.copy()
                    by_year_display["Year"] = by_year_display["Year"].astype(int).astype(str)
                    by_year_display = by_year_display.set_index("Year")
                    st.line_chart(by_year_display)
                else:
                    st.write("Sin datos de año.")
            with col_b:
                st.markdown("**Distribución de mi nota (Your Rating)**")
                if "Your Rating" in filtered.columns and filtered["Your Rating"].notna().any():
                    ratings_counts = (filtered["Your Rating"].round().value_counts().sort_index().reset_index())
                    ratings_counts.columns = ["Rating", "Count"]
                    ratings_counts["Rating"] = ratings_counts["Rating"].astype(int).astype(str)
                    ratings_counts = ratings_counts.set_index("Rating")
                    st.bar_chart(ratings_counts)
                else:
                    st.write("No hay notas mías disponibles.")

            # Otros gráficos (géneros / décadas)
            col_c, col_d = st.columns(2)
            with col_c:
                st.markdown("**Top géneros (por número de películas)**")
                if "GenreList" in filtered.columns:
                    genres_exploded = filtered.explode("GenreList")
                    genres_exploded = genres_exploded[genres_exploded["GenreList"].notna() & (genres_exploded["GenreList"] != "")]
                    if not genres_exploded.empty:
                        top_genres = (genres_exploded["GenreList"].value_counts().head(15).reset_index())
                        top_genres.columns = ["Genre", "Count"]
                        top_genres = top_genres.set_index("Genre")
                        st.bar_chart(top_genres)
                    else:
                        st.write("No hay géneros disponibles.")
                else:
                    st.write("No se encontró información de géneros.")
            with col_d:
                st.markdown("**IMDb promedio por década**")
                if "IMDb Rating" in filtered.columns and filtered["IMDb Rating"].notna().any():
                    tmp = filtered[filtered["Year"].notna()].copy()
                    if not tmp.empty:
                        tmp["Decade"] = (tmp["Year"] // 10 * 10).astype(int)
                        decade_imdb = (tmp.groupby("Decade")["IMDb Rating"].mean().reset_index().sort_values("Decade"))
                        decade_imdb["Decade"] = decade_imdb["Decade"].astype(str)
                        decade_imdb = decade_imdb.set_index("Decade")
                        st.line_chart(decade_imdb)
                    else:
                        st.write("No hay datos suficientes de año para calcular décadas.")
                else:
                    st.write("No hay IMDb Rating disponible.")

# ============================================================
# TAB 3 - AFI
# ============================================================
with tab_afi:
    st.markdown("## 🎬 AFI's 100 Years...100 Movies")
    AFI_LIST = [
        {"Rank": 1, "Title": "Citizen Kane", "Year": 1941},
        {"Rank": 2, "Title": "The Godfather", "Year": 1972},
        {"Rank": 3, "Title": "Casablanca", "Year": 1942},
        # ... (puedes añadir/editar la lista si quieres)
    ]
    afi_df = pd.DataFrame(AFI_LIST)
    afi_df["NormTitle"] = afi_df["Title"].apply(normalize_title)
    afi_df["YearInt"] = afi_df["Year"]
    if "NormTitle" not in df.columns:
        df["NormTitle"] = df.get("Title", "").apply(normalize_title)
    if "YearInt" not in df.columns:
        if "Year" in df.columns:
            df["YearInt"] = df["Year"].fillna(-1).astype(int)
        else:
            df["YearInt"] = -1
    def find_match(afi_norm, year, df_full):
        candidates = df_full[df_full["YearInt"] == year]
        def _try(cands):
            if cands.empty:
                return None
            return cands.iloc[0]
        m = _try(candidates[candidates["NormTitle"] == afi_norm])
        if m is not None:
            return m
        m = _try(candidates[candidates["NormTitle"].str.contains(afi_norm, regex=False, na=False)])
        if m is not None:
            return m
        return None
    afi_df["Your Rating"] = None
    afi_df["IMDb Rating"] = None
    afi_df["URL"] = None
    afi_df["Seen"] = False
    for idx, row in afi_df.iterrows():
        match = find_match(row["NormTitle"], row["YearInt"], df)
        if match is not None:
            afi_df.at[idx, "Your Rating"] = match.get("Your Rating")
            afi_df.at[idx, "IMDb Rating"] = match.get("IMDb Rating")
            afi_df.at[idx, "URL"] = match.get("URL")
            afi_df.at[idx, "Seen"] = True
    total_afi = len(afi_df)
    seen_afi = int(afi_df["Seen"].sum())
    pct_afi = (seen_afi / total_afi) if total_afi > 0 else 0.0
    col_afi1, col_afi2 = st.columns(2)
    with col_afi1:
        st.metric("Películas vistas del listado AFI", f"{seen_afi}/{total_afi}")
    with col_afi2:
        st.metric("Progreso en AFI 100", f"{pct_afi * 100:.1f}%")
    st.progress(pct_afi)
    afi_table_display = afi_df[["Rank", "Title", "Year", "Seen", "Your Rating", "IMDb Rating", "URL"]].copy()
    afi_table_display["Your Rating"] = afi_table_display["Your Rating"].apply(fmt_rating)
    afi_table_display["IMDb Rating"] = afi_table_display["IMDb Rating"].apply(fmt_rating)
    afi_table_display = afi_table_display.rename(columns={"Seen": "Vista"})
    st.dataframe(afi_table_display, use_container_width=True, hide_index=True)

# ============================================================
# TAB 4 - PREMIOS ÓSCAR (actualizado)
# ============================================================
with tab_awards:
    st.markdown("## 🏆 Premios de la Academia (dataset Óscar)")

    oscar_file = find_oscar_file()
    if oscar_file is None:
        st.info("No encontré 'Oscar_Data_1927_today.xlsx' / 'Oscar_Data_1927_today.csv' ni 'full_data.csv' en el repo. Súbelo a la raíz del repo.")
        st.stop()

    osc = load_full_data(oscar_file)
    if osc.empty:
        st.info(f"No pude cargar el archivo de Óscar ({oscar_file}). Revisa el archivo y el formato.")
        st.stop()

    # enlazar con tu catálogo
    osc_x = attach_catalog_to_full(osc, df)

    st.markdown("### 🎛️ Filtros (Óscar)")
    c1, c2, c3 = st.columns([1,1,2])

    # Para filtrar por Year (año de la película) - según tu petición
    years_available = sorted([y for y in osc_x["YearInt"].unique() if y and y != -1])
    if years_available:
        min_y, max_y = int(min(years_available)), int(max(years_available))
    else:
        min_y, max_y = 1927, pd.Timestamp.now().year
    with c1:
        year_range_osc = st.slider("Año de película (filtrar)", min_value=min_y, max_value=max_y, value=(min_y, max_y))
    all_cats = sorted([c for c in osc_x["CanonCat"].dropna().unique().tolist() if str(c).strip()!=""])
    with c2:
        cats_sel = st.multiselect("Categorías (canon)", options=all_cats, default=[])
    with c3:
        q_aw = st.text_input("Buscar (categoría / entidad / película / IDs)", placeholder="Ej: 'BEST PICTURE' o 'Metro-Goldwyn-Mayer'")

    # Aplicar filtros: usar YearInt como pediste
    ff = osc_x[
        (osc_x["YearInt"] >= year_range_osc[0]) &
        (osc_x["YearInt"] <= year_range_osc[1])
    ].copy()
    if cats_sel:
        ff = ff[ff["CanonCat"].isin(cats_sel)]
    if q_aw:
        q = q_aw.strip().lower()
        mask = (
            ff["CanonCat"].astype(str).str.lower().str.contains(q, na=False) |
            ff["Nominee"].astype(str).str.lower().str.contains(q, na=False) |
            ff["Film"].astype(str).str.lower().str.contains(q, na=False) |
            ff["NomineeIdsList"].astype(str).str.lower().str.contains(q, na=False)
        )
        ff = ff[mask]

    # Métricas resumen
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.metric("Años (rango)", f"{year_range_osc[0]}–{year_range_osc[1]}")
    with mcol2:
        st.metric("Filas (nominaciones + ganadores)", len(ff))
    with mcol3:
        st.metric("Categorías distintas (filtradas)", ff["CanonCat"].nunique())
    with mcol4:
        st.metric("Ganadores (filtrados)", int(ff["IsWinner"].sum()))

    st.caption("Usamos el dataset de Óscar encontrado en la raíz. Ganadores marcados por 'Winner'/'IsWinner'. Rankings usan NomineeIds (entidades) y Film+Year para películas.")

    # ---------------- Vista por año: lista de categorías y nominados (tabla) ----------------
    st.markdown("### 📅 Vista por año: categorías, nominados y ganadores (tabla)")
    years_sorted = sorted(ff["YearInt"].dropna().unique())
    if years_sorted:
        y_pick = st.selectbox("Elige año (año de película) para ver categorías", options=years_sorted, index=len(years_sorted)-1, key="aw_year_pick")
    else:
        y_pick = None

    if y_pick is None:
        st.info("No hay años disponibles con estos filtros.")
    else:
        table_year = ff[ff["YearInt"] == int(y_pick)].copy().sort_values(["CanonCat", "IsWinner", "Film", "Nominee"], ascending=[True, False, True, True])
        if table_year.empty:
            st.info("No hay filas para el año seleccionado con los filtros actuales.")
        else:
            pretty = table_year[["CanonCat", "Nominee", "Film", "YearInt", "IsWinner", "InMyCatalog", "MyRating", "MyIMDb", "CatalogURL"]].copy()
            pretty = pretty.rename(columns={"CanonCat": "Categoría", "Nominee": "Entidad / Nominee", "Film": "Película", "YearInt": "Año", "IsWinner":"Ganador", "InMyCatalog":"En mi catálogo", "MyRating":"Mi nota", "MyIMDb":"IMDb", "CatalogURL":"IMDb (mía)"})
            pretty["En mi catálogo"] = pretty["En mi catálogo"].map({True:"✅", False:"—"})
            pretty["Mi nota"] = pretty["Mi nota"].apply(lambda v: f"{float(v):.1f}" if pd.notna(v) else "")
            pretty["IMDb"] = pretty["IMDb"].apply(lambda v: f"{float(v):.1f}" if pd.notna(v) else "")
            pretty["Año"] = pretty["Año"].apply(lambda v: "" if v==-1 or pd.isna(v) else str(int(v)))
            def highlight_winner(row):
                if bool(row.get("Ganador", False)):
                    style = 'background-color: rgba(34,197,94,0.18); color:#ecfdf5; font-weight:700; border-left:3px solid #22c55e'
                else:
                    style = ''
                return [style] * len(row)
            styled = (pretty.style.set_table_styles([{"selector":"th","props":[("text-align","left")]}]).set_properties(**{"text-align":"left"}).apply(highlight_winner, axis=1))
            st.dataframe(styled, use_container_width=True, hide_index=True)
            csv_dl = table_year.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Descargar nominados/ganadores del año (CSV)", data=csv_dl, file_name=f"oscars_{y_pick}.csv", mime="text/csv")

    # ---------------- Rankings (Nominaciones en el rango seleccionado) ----------------
    st.markdown("### 🥇 Rankings en el rango seleccionado (Nominaciones al Óscar)")
    colr1, colr2 = st.columns(2)
    with colr1:
        top_films = (ff.groupby(["Film", "YearInt"]).size().reset_index(name="Nominaciones").sort_values(["Nominaciones", "Film"], ascending=[False, True]).head(20))
        if not top_films.empty:
            tf_disp = top_films.rename(columns={"Film":"Película", "YearInt":"Año"})
            tf_disp["Año"] = tf_disp["Año"].apply(lambda v: "" if v==-1 or pd.isna(v) else str(int(v)))
            st.dataframe(tf_disp, use_container_width=True, hide_index=True)
        else:
            st.write("Sin datos de películas para este rango.")
    with colr2:
        ent = ff.copy()
        ent = ent.explode("NomineeIdsList")
        ent = ent[ent["NomineeIdsList"].notna() & (ent["NomineeIdsList"] != "")]
        top_entities = (ent.groupby("NomineeIdsList").size().reset_index(name="Nominaciones").sort_values(["Nominaciones", "NomineeIdsList"], ascending=[False, True]).head(20))
        if not top_entities.empty:
            te_disp = top_entities.rename(columns={"NomineeIdsList":"Entidad (NomineeIds)"})
            st.dataframe(te_disp, use_container_width=True, hide_index=True)
        else:
            st.write("Sin datos de entidades (NomineeIds) para este rango.")

    # ---------------- Vista por año + tarjetas con póster y nominados ----------------
    st.markdown("### 🎞️ Vista visual por año: categorías con póster y nominados")
    st.caption("Se muestran las categorías del año seleccionado con el póster de la película y la lista de nominados. Ganador resaltado.")
    if 'y_pick' not in locals() or y_pick is None:
        st.info("Selecciona un año en la sección 'Vista por año' para ver la vista visual.")
    else:
        y_for_gallery = int(y_pick)
        # seleccionar filas de ese año
        rows_year = ff[ff["YearInt"] == y_for_gallery].copy().sort_values(["CanonCat", "IsWinner"], ascending=[True, False])
        if rows_year.empty:
            st.info("No hay datos para ese año.")
        else:
            # agrupar por categoría (CanonCat) y por film dentro de la categoría
            cats = rows_year["CanonCat"].unique().tolist()
            # controlador simple: opcion para ordenar categorias alfabéticamente
            sort_alpha = st.checkbox("Ordenar categorías alfabéticamente", value=True, key="aw_sort_alpha")
            if sort_alpha:
                cats = sorted(cats)
            # render
            for cat in cats:
                subset = rows_year[rows_year["CanonCat"] == cat].copy()
                if subset.empty:
                    continue
                st.markdown(f"#### {cat}")
                # si hay varias películas en la categoría (ej. co-ganadores / excepciones) las listamos por film
                films = subset["Film"].unique().tolist()
                # grid de cards
                cards = []
                for film in films:
                    frows = subset[subset["Film"] == film].copy()
                    # buscar póster TMDb
                    poster_url = None
                    if use_tmdb_gallery:
                        tm = get_tmdb_basic_info(film, y_for_gallery)
                        if tm:
                            poster_url = tm.get("poster_url")
                    # construir HTML de tarjeta
                    nominees_html_parts = []
                    for _, r in frows.iterrows():
                        nominee_name = r.get("Nominee") or ""
                        is_w = bool(r.get("IsWinner", False))
                        in_cat = r.get("InMyCatalog", False)
                        imdb_my = r.get("MyIMDb", None)
                        # marcador ganador
                        if is_w:
                            nominees_html_parts.append(f'<div style="font-weight:700;color:#ffd166">🏆 {nominee_name}</div>')
                        else:
                            nominees_html_parts.append(f'<div style="color:#e5e7eb">{nominee_name}</div>')
                    nominees_html = "\n".join(nominees_html_parts)
                    poster_section = f'<img src="{poster_url}" style="width:120px;height:180px;object-fit:cover;border-radius:6px">' if poster_url else '<div style="width:120px;height:180px;display:flex;align-items:center;justify-content:center;background:#0f172a;border-radius:6px;color:#9ca3af">Sin póster</div>'
                    card_html = f"""
<div style="display:flex;gap:12px;padding:10px;border-radius:10px;border:1px solid rgba(255,255,255,0.03);margin-bottom:8px;background:linear-gradient(180deg, rgba(15,23,42,0.95), rgba(10,14,20,0.6))">
  <div style="flex:0 0 auto">{poster_section}</div>
  <div style="flex:1 1 auto">
    <div style="font-weight:700;font-size:1.0rem;margin-bottom:6px">{film} {f'({y_for_gallery})' if y_for_gallery else ''}</div>
    <div style="font-size:0.92rem">{nominees_html}</div>
  </div>
</div>
"""
                    cards.append(card_html)
                # mostrar todas las tarjetas de la categoría
                st.markdown("\n".join(cards), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("Si quieres que muestre también imágenes de las personas (actores/directores) en la vista visual, puedo añadir búsqueda de imágenes de persona usando TMDb Person API — dime si lo quieres.")

# ============================================================
# TAB 5 - ¿QUÉ VER HOY?
# ============================================================
with tab_what:
    st.markdown("## 🎲 ¿Qué ver hoy? (según mi propio gusto)")
    st.write("Elijo una película de mi catálogo usando mis notas, año y disponibilidad en streaming (TMDb).")
    with st.expander("Ver recomendación aleatoria según mi gusto", expanded=True):
        modo = st.selectbox("Modo de recomendación", ["Entre todas las películas filtradas", "Solo mis favoritas (nota ≥ 9)", "Entre mis 8–10 de los últimos 20 años"])
        if st.button("Recomendar una película", key="btn_random_reco"):
            pool = filtered.copy()
            if modo == "Solo mis favoritas (nota ≥ 9)":
                pool = pool[pool["Your Rating"] >= 9] if "Your Rating" in pool.columns else pool.iloc[0:0]
            elif modo == "Entre mis 8–10 de los últimos 20 años":
                if "Your Rating" in pool.columns and "Year" in pool.columns:
                    pool = pool[(pool["Your Rating"] >= 8) & (pool["Year"].notna()) & (pool["Year"] >= (pd.Timestamp.now().year - 20))]
                else:
                    pool = pool.iloc[0:0]
            if pool.empty:
                st.warning("No hay películas que cumplan con el modo seleccionado y los filtros actuales.")
            else:
                if "Your Rating" in pool.columns and pool["Your Rating"].notna().any():
                    pesos = (pool["Your Rating"].fillna(0) + 1).tolist()
                else:
                    pesos = None
                idx = random.choices(pool.index.tolist(), weights=pesos, k=1)[0]
                peli = pool.loc[idx]
                titulo = peli.get("Title", "Sin título")
                year = peli.get("Year", "")
                nota = peli.get("Your Rating", "")
                imdb_rating = peli.get("IMDb Rating", "")
                genres = peli.get("Genres", "")
                directors = peli.get("Directors", "")
                url = peli.get("URL", "")
                border_color, glow_color = get_rating_colors(nota)
                tmdb_info = get_tmdb_basic_info(titulo, year)
                poster_url = tmdb_info.get("poster_url") if tmdb_info else None
                tmdb_rating = tmdb_info.get("vote_average") if tmdb_info else None
                col_img, col_info = st.columns([1,3])
                with col_img:
                    if poster_url:
                        try:
                            st.image(poster_url)
                        except Exception:
                            st.write("Sin póster")
                    else:
                        st.write("Sin póster")
                    if show_trailers:
                        trailer_url = None
                        if YOUTUBE_API_KEY is not None:
                            # tratar de buscar vídeo - hay otra función arriba, pero por simplicidad no duplicamos caching
                            trailer_url = None
                        if trailer_url:
                            st.video(trailer_url)
                with col_info:
                    st.markdown(f"""
<div class="movie-card" style="border-color:{border_color};box-shadow:0 0 26px {glow_color};margin-bottom:10px">
  <div style="font-weight:700;font-size:1.2rem">{titulo} {f'({fmt_year(year)})' if pd.notna(year) else ''}</div>
  <div style="margin-top:6px">{('⭐ Mi nota: '+fmt_rating(nota)) if pd.notna(nota) else ''} · IMDb: {fmt_rating(imdb_rating)} · TMDb: {fmt_rating(tmdb_rating)}</div>
  <div style="margin-top:8px">Géneros: {genres}</div>
  <div>Director(es): {directors}</div>
  <div style="margin-top:8px">{f'<a href=\"{url}\" target=\"_blank\">Ver en IMDb</a>' if isinstance(url,str) and url.startswith('http') else ''}</div>
</div>
""", unsafe_allow_html=True)

# ===================== FOOTER =====================
st.markdown("---")
st.markdown(f"<div style='text-align:center; opacity:0.9; font-size:0.9rem;'>v{APP_VERSION} · Powered by <b>Diego Leal</b></div>", unsafe_allow_html=True)
