import streamlit as st
import pandas as pd
import requests
import re
from urllib.parse import quote
import random

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(page_title="🎬 Mi Catálogo de Películas", layout="wide", page_icon="🎥")

# Estilos visuales
st.markdown("""
<style>
div.block-container { padding-top: 2.8rem; }
h1, h2, h3 { margin-top: 1.4em !important; }
h1 { font-size: 2.2rem !important; font-weight: 700 !important; }
h2 { font-size: 1.6rem !important; font-weight: 600 !important; }
.stTabs [data-baseweb="tab"] {
  font-size: 1rem !important;
  padding: 0.6rem 0.8rem !important;
}
body, .stApp { font-size: 0.95rem !important; color: #e6e6e6 !important; }
.movie-card {
    text-align: center;
    background-color: rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 0.8rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.movie-card:hover {
    transform: scale(1.03);
    box-shadow: 0px 0px 20px rgba(255,255,255,0.2);
}
.movie-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #f5f5f5;
}
.movie-sub {
    font-size: 0.8rem;
    color: #b3b3b3;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CLAVES DE API (MANEJO SEGURO)
# ============================================================

def get_secret(key):
    return st.secrets.get("general", {}).get(key, "")

TMDB_KEY = get_secret("TMDB_API_KEY")
OMDB_KEY = get_secret("OMDB_API_KEY")
YT_KEY   = get_secret("YOUTUBE_API_KEY")

if not any([TMDB_KEY, OMDB_KEY, YT_KEY]):
    st.warning("⚠️ No se detectaron claves API. Puedes agregarlas en .streamlit/secrets.toml dentro del bloque [general].")

# ============================================================
# FUNCIONES UTILITARIAS
# ============================================================

def fmt_year(y): return str(int(y)) if pd.notna(y) and str(y).isdigit() else ""
def fmt_rating(v): return f"{v:.1f}" if pd.notna(v) else "–"
def normalize_title(t): return re.sub(r"[^a-z0-9]", "", str(t).lower())

@st.cache_data
def load_data(csv_path):
    df = pd.read_csv(csv_path)
    df["YearInt"] = df["Year"].fillna(-1).astype(int)
    df["NormTitle"] = df["Title"].apply(normalize_title)
    df["GenreList"] = df["Genres"].fillna("").apply(lambda x: x.split(", ") if x else [])
    return df

@st.cache_data
def get_tmdb_basic_info(title, year):
    if not TMDB_KEY: return None
    q = quote(title)
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={q}&year={year}"
    r = requests.get(url).json()
    if r.get("results"):
        res = r["results"][0]
        return {
            "id": res["id"],
            "poster": f"https://image.tmdb.org/t/p/w500{res.get('poster_path')}" if res.get("poster_path") else None,
            "overview": res.get("overview", "")
        }
    return None

@st.cache_data
def get_youtube_trailer_url(title, year, region="CL"):
    if not YT_KEY: return None
    query = f"{title} {year} tráiler oficial"
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=1&key={YT_KEY}&q={quote(query)}&regionCode={region}"
    try:
        vid = requests.get(url).json()["items"][0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={vid}"
    except Exception:
        return None

# ============================================================
# CARGA DE DATOS
# ============================================================

df = load_data("movies.csv")

# ============================================================
# TÍTULO PRINCIPAL
# ============================================================

st.title("🎬 Mi Catálogo de Películas")
st.caption("Explora tu colección de películas con tráilers, datos y recomendaciones inteligentes.")

# ============================================================
# BÚSQUEDA
# ============================================================

query = st.text_input("🔍 Buscar por título, director o género...").strip().lower()
filtered = df[df.apply(
    lambda row: query in row["Title"].lower() or query in str(row["Directors"]).lower() or query in str(row["Genres"]).lower(),
    axis=1
)] if query else df

# ============================================================
# TABS PRINCIPALES
# ============================================================

tab_gallery, tab_analysis, tab_afi, tab_recs = st.tabs(["🎞 Galería", "📊 Análisis", "🏆 Lista AFI", "🎲 ¿Qué ver hoy?"])

# ============================================================
# TAB 1: GALERÍA VISUAL
# ============================================================

with tab_gallery:
    st.markdown("## 🎥 Galería visual")
    st.caption("Haz clic en una película para ver su tráiler y más detalles.")

    page_size = 12
    total_pages = max(1, (len(filtered) + page_size - 1) // page_size)
    page = st.number_input("Página", min_value=1, max_value=total_pages, value=1)
    start, end = (page - 1) * page_size, page * page_size

    cols = st.columns(4)
    subset = filtered.iloc[start:end]

    for i, (_, row) in enumerate(subset.iterrows()):
        tmdb = get_tmdb_basic_info(row["Title"], row["Year"])
        poster = tmdb["poster"] if tmdb else None
        overview = tmdb["overview"][:180] + "…" if tmdb and tmdb["overview"] else "Sin descripción disponible."
        col = cols[i % 4]
        with col:
            with st.container():
                if poster:
                    st.image(poster, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/300x450?text=Sin+Imagen", use_container_width=True)
                st.markdown(f"<div class='movie-card'><div class='movie-title'>{row['Title']} ({fmt_year(row['Year'])})</div><div class='movie-sub'>⭐ {fmt_rating(row['Your Rating'])} | IMDb {fmt_rating(row['IMDb Rating'])}</div><div class='movie-sub'>{overview}</div></div>", unsafe_allow_html=True)

# ============================================================
# TAB 2: ANÁLISIS
# ============================================================

with tab_analysis:
    st.markdown("## 📊 Estadísticas de tu catálogo")
    st.caption("Usa los filtros de la barra lateral para explorar tus datos.")
    # Aquí puedes mantener tus gráficos previos

# ============================================================
# TAB 3: LISTA AFI
# ============================================================

AFI_LIST = [
    {"Rank": 1, "Title": "Citizen Kane", "Year": 1941},
    {"Rank": 2, "Title": "The Godfather", "Year": 1972},
    {"Rank": 3, "Title": "Casablanca", "Year": 1942},
    {"Rank": 4, "Title": "Raging Bull", "Year": 1980},
    {"Rank": 5, "Title": "Singin' in the Rain", "Year": 1952},
    {"Rank": 6, "Title": "Gone with the Wind", "Year": 1939},
    {"Rank": 7, "Title": "Lawrence of Arabia", "Year": 1962},
    {"Rank": 8, "Title": "Schindler's List", "Year": 1993},
    {"Rank": 9, "Title": "Vertigo", "Year": 1958},
    {"Rank": 10, "Title": "The Wizard of Oz", "Year": 1939}
]

with tab_afi:
    st.markdown("## 🏆 Comparación con la lista AFI")
    afi_df = pd.DataFrame(AFI_LIST)
    df["NormTitle"] = df["Title"].apply(normalize_title)
    afi_df["NormTitle"] = afi_df["Title"].apply(normalize_title)
    merged = afi_df.merge(df, on="NormTitle", how="left")
    merged["Vista"] = merged["Your Rating"].notna()

    col1, col2, col3 = st.columns(3)
    col1.metric("Películas vistas", int(merged["Vista"].sum()))
    col2.metric("Total AFI", len(merged))
    col3.metric("Porcentaje visto", f"{100 * merged['Vista'].mean():.1f}%")

    seen = merged[merged["Vista"]]
    unseen = merged[~merged["Vista"]]
    st.markdown("### 🎬 Películas AFI que viste")
    st.dataframe(seen[["Rank", "Title_x", "Year_x", "Your Rating"]], hide_index=True, use_container_width=True)
    st.markdown("### 📋 Películas AFI pendientes")
    st.dataframe(unseen[["Rank", "Title_x", "Year_x"]], hide_index=True, use_container_width=True)

# ============================================================
# TAB 4: ¿QUÉ VER HOY? + RECOMENDACIONES
# ============================================================

with tab_recs:
    st.markdown("## 🎲 ¿Qué ver hoy?")
    peli = filtered.sample(1).iloc[0]
    st.subheader(f"🎥 {peli['Title']} ({fmt_year(peli['Year'])})")
    st.write(f"**Tu nota:** {fmt_rating(peli['Your Rating'])} | **IMDb:** {fmt_rating(peli['IMDb Rating'])}")

    tmdb = get_tmdb_basic_info(peli["Title"], peli["Year"])
    if tmdb:
        if tmdb["poster"]:
            st.image(tmdb["poster"], width=300)
        if tmdb["overview"]:
            st.caption(tmdb["overview"])

    yt_url = get_youtube_trailer_url(peli["Title"], peli["Year"])
    if yt_url:
        st.video(yt_url)
    else:
        st.info("No se encontró tráiler disponible en YouTube.")

    st.markdown("### 🎯 Recomendaciones similares en tu catálogo")
    genres = set(peli["GenreList"])
    similares = df[df["Title"] != peli["Title"]].copy()
    similares["SimScore"] = similares["GenreList"].apply(lambda g: len(set(g) & genres))
    recs = similares[similares["SimScore"] > 0].sort_values("SimScore", ascending=False).head(5)
    for _, r in recs.iterrows():
        st.write(f"- **{r['Title']}** ({fmt_year(r['Year'])}) — {', '.join(r['GenreList'])}")

    if tmdb and TMDB_KEY:
        st.markdown("### 🌐 Recomendaciones fuera de tu catálogo")
        try:
            tid = tmdb["id"]
            url = f"https://api.themoviedb.org/3/movie/{tid}/recommendations?api_key={TMDB_KEY}&language=es-ES"
            recs_tmdb = requests.get(url).json().get("results", [])[:5]
            for r in recs_tmdb:
                name = r["title"]
                poster = f"https://image.tmdb.org/t/p/w200{r['poster_path']}" if r.get("poster_path") else None
                col1, col2 = st.columns([1, 4])
                with col1:
                    if poster: st.image(poster, width=100)
                with col2:
                    st.write(f"**{name}** ({r.get('release_date','')[:4]})")
                    st.caption(r.get("overview", "")[:180] + "…")
        except Exception:
            st.warning("No se pudieron obtener recomendaciones externas.")
