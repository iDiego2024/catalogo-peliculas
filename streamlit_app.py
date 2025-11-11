import streamlit as st
import pandas as pd
import requests
import random
import altair as alt
import re
import math
from urllib.parse import quote_plus

# ----------------- Configuración general -----------------
st.set_page_config(
    page_title="🎬 Mi catálogo de Películas",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎥 Mi catálogo de películas (IMDb)")

# ----------------- Config APIs externas -----------------
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"
TMDB_SIMILAR_URL_TEMPLATE = "https://api.themoviedb.org/3/movie/{movie_id}/similar"

YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", None)
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# ----------------- Lista AFI 100 Years...100 Movies (10th Anniversary Edition) -----------------
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
    {"Rank": 10, "Title": "The Wizard of Oz", "Year": 1939},
    # … (restantes elementos) …
    {"Rank": 100, "Title": "Ben-Hur", "Year": 1959},
]

def normalize_title(s: str) -> str:
    """Normaliza un título para compararlo (minúsculas, sin espacios ni signos)."""
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

# ----------------- Funciones auxiliares -----------------

@st.cache_data
def load_data(file_path_or_buffer):
    df = pd.read_csv(file_path_or_buffer)

    # manejo de columnas
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
            df["Year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
            .astype(float)
        )
    else:
        df["Year"] = pd.NA

    if "Genres" not in df.columns:
        df["Genres"] = ""
    if "Directors" not in df.columns:
        df["Directors"] = ""

    df["Genres"] = df["Genres"].fillna("")
    df["GenreList"] = df["Genres"].apply(
        lambda x: [] if (pd.isna(x) or x == "") else str(x).split(", ")
    )

    if "Date Rated" in df.columns:
        df["Date Rated"] = pd.to_datetime(df["Date Rated"], errors="coerce").dt.date

    # Texto de búsqueda precomputado
    cols_for_search = []
    for c in ["Title", "Original Title", "Directors", "Genres", "Year", "Your Rating", "IMDb Rating"]:
        if c in df.columns:
            cols_for_search.append(c)

    if cols_for_search:
        df["SearchText"] = (
            df[cols_for_search]
            .astype(str)
            .apply(lambda row: " ".join(row), axis=1)
            .str.lower()
        )
    else:
        df["SearchText"] = ""

    return df

def _coerce_year_for_tmdb(year):
    if year is None or pd.isna(year):
        return None
    try:
        return int(float(year))
    except Exception:
        return None

@st.cache_data
def get_tmdb_basic_info(title, year=None):
    """Devuelve info básica TMDb en una sola búsqueda: id, poster_url, vote_average."""
    if TMDB_API_KEY is None or not title:
        return None
    title = str(title).strip()
    year_int = _coerce_year_for_tmdb(year)
    params = {"api_key": TMDB_API_KEY, "query": title}
    if year_int:
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
        movie_id = movie.get("id")
        poster_path = movie.get("poster_path")
        vote_average = movie.get("vote_average")
        return {
            "id": movie_id,
            "poster_url": f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None,
            "vote_average": vote_average,
        }
    except Exception:
        return None

@st.cache_data
def get_tmdb_providers(tmdb_id, country="CL"):
    """Streaming desde TMDb watch/providers para un país (por id de TMDb)."""
    if TMDB_API_KEY is None or not tmdb_id:
        return None
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/watch/providers"
        r2 = requests.get(url, params={"api_key": TMDB_API_KEY}, timeout=5)
        if r2.status_code != 200:
            return None
        pdata = r2.json()
        all_countries = pdata.get("results", {})
        cdata = all_countries.get(country.upper())
        if not cdata:
            return None
        providers = set()
        for key in ["flatrate", "rent", "buy", "ads", "free"]:
            for item in cdata.get(key, []) or []:
                name = item.get("provider_name")
                if name:
                    providers.add(name)
        link = cdata.get("link")
        return {"platforms": sorted(list(providers)), "link": link}
    except Exception:
        return None

@st.cache_data
def get_tmdb_similar_movies(tmdb_id, language="es-ES", max_results=10):
    """Devuelve lista de películas similares según TMDb para un id dado."""
    if TMDB_API_KEY is None or not tmdb_id:
        return []
    try:
        url = TMDB_SIMILAR_URL_TEMPLATE.format(movie_id=tmdb_id)
        params = {"api_key": TMDB_API_KEY, "language": language, "page": 1}
        r = requests.get(url, params=params, timeout=5)
        if r.status_code != 200:
            return []
        data = r.json()
        results = data.get("results", [])[:max_results]
        out = []
        for m in results:
            title = m.get("title") or m.get("name")
            date_str = m.get("release_date") or ""
            year = None
            if date_str:
                try:
                    year = int(date_str[:4])
                except:
                    year = None
            out.append({
                "id": m.get("id"),
                "title": title,
                "year": year,
                "vote_average": m.get("vote_average"),
                "poster_url": f"{TMDB_IMAGE_BASE}{m['poster_path']}" if m.get("poster_path") else None,
            })
        return out
    except Exception:
        return []

@st.cache_data
def get_youtube_trailer_url(title, year=None, language_hint="es"):
    """Devuelve la URL de YouTube del primer resultado tipo tráiler para ese título."""
    if YOUTUBE_API_KEY is None or not title:
        return None
    q = f"{title} trailer"
    try:
        year_int = _coerce_year_for_tmdb(year)
        if year_int:
            q += f" {year_int}"
    except:
        pass
    params = {
        "key": YOUTUBE_API_KEY,
        "part": "snippet",
        "q": q,
        "type": "video",
        "maxResults": 1,
        "videoEmbeddable": "true",
        "regionCode": "CL",
    }
    try:
        r = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=5)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data.get("items", [])
        if not items:
            return None
        vid = items[0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={vid}"
    except:
        return None

def get_rating_colors(rating):
    try:
        r = float(rating)
    except:
        return ("#94a3b8", "rgba(15,23,42,0.0)")
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
    if not title:
        return None
    q = f"reseña película {title}"
    try:
        year_int = _coerce_year_for_tmdb(year)
        if year_int:
            q += f" {year_int}"
    except:
        pass
    return "https://www.google.com/search?q=" + quote_plus(q)

def recommend_from_catalog(df_all, seed_row, top_n=5):
    """Recomendaciones inteligentes dentro de tu catálogo basadas en similitud simple."""
    if df_all.empty or seed_row is None:
        return pd.DataFrame()
    candidates = df_all.copy()
    seed_title = seed_row.get("Title")
    seed_year = seed_row.get("Year")
    candidates = candidates[
        ~((candidates["Title"] == seed_title) & (candidates["Year"] == seed_year))
    ]
    seed_genres = set(seed_row.get("GenreList") or [])
    seed_dirs = set(d.strip() for d in str(seed_row.get("Directors") or "").split(",") if d.strip())
    seed_rating = seed_row.get("Your Rating")
    scores = []
    for idx, r in candidates.iterrows():
        g2 = set(r.get("GenreList") or [])
        d2 = set(d.strip() for d in str(r.get("Directors") or "").split(",") if d.strip())
        score = 0.0
        score += 2.0 * len(seed_genres & g2)
        if seed_dirs & d2:
            score += 3.0
        if pd.notna(seed_year) and pd.notna(r.get("Year")):
            score -= min(abs(seed_year - r.get("Year")) / 10.0, 3.0)
        r2 = r.get("Your Rating")
        if pd.notna(seed_rating) and pd.notna(r2):
            score -= abs(seed_rating - r2) * 0.3
        imdb_r2 = r.get("IMDb Rating")
        if pd.notna(imdb_r2):
            score += (float(imdb_r2) - 6.5) * 0.2
        scores.append((idx, score))
    if not scores:
        return pd.DataFrame()
    scores_sorted = sorted(scores, key=lambda x: x[1], reverse=True)
    top_indices = [idx for idx, sc in scores_sorted[:top_n] if sc > 0]
    if not top_indices:
        return pd.DataFrame()
    recs = df_all.loc[top_indices].copy()
    score_map = dict(scores)
    recs["similarity_score"] = recs.index.map(score_map.get)
    return recs

# ----------------- Carga de datos -----------------
st.sidebar.header("📂 Datos")
uploaded = st.sidebar.file_uploader(
    "Sube tu CSV de IMDb (si no, se usa peliculas.csv por defecto)", type=["csv"]
)
if uploaded is not None:
    df = load_data(uploaded)
else:
    try:
        df = load_data("peliculas.csv")
    except FileNotFoundError:
        st.error("No se encontró 'peliculas.csv' y no se cargó archivo. Sube tu CSV para continuar.")
        st.stop()

if "Title" not in df.columns:
    st.error("El CSV debe contener columna ‘Title’ para funcionar.")
    st.stop()

df["NormTitle"] = df["Title"].apply(normalize_title)
df["YearInt"] = df["Year"].fillna(-1).astype(int)

# ----------------- Tema oscuro + CSS mejorado -----------------
st.markdown(
    """
    <style>
    body, .stApp { background-color: #020617; color: #e5e7eb; }
    .movie-gallery-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 16px;
        margin-top: 16px;
    }
    .movie-card {
        background: rgba(15,23,42,0.9);
        border-radius: 12px;
        padding: 8px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        overflow: hidden;
    }
    .movie-card:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 20px rgba(250,204,21,0.3);
    }
    .movie-title {
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 4px;
        color: #f9fafb;
    }
    .movie-sub {
        font-size: 0.75rem;
        color: #cbd5f5;
    }
    .movie-poster-frame {
        width: 100%;
        aspect-ratio: 2/3;
        overflow: hidden;
        border-radius: 8px;
    }
    .movie-poster-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.25s ease-out;
    }
    .movie-card:hover .movie-poster-img {
        transform: scale(1.03);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------- Opciones de visualización -----------------
st.sidebar.header("🖼️ Visualización")
show_posters_fav = st.sidebar.checkbox(
    "Mostrar pósters en mis favoritas (nota ≥ 9)", value=True
)
use_tmdb_gallery = st.sidebar.checkbox(
    "Usar pósters TMDb en galería", value=True
)
show_trailers = st.sidebar.checkbox(
    "Mostrar tráiler de YouTube (si clave API)", value=True
)
show_awards = st.sidebar.checkbox(
    "Consultar premios OMDb (más lento)", value=False
)
if show_awards:
    st.sidebar.caption("Activar consulta OMDb puede ralentizar la carga inicial.")

# ----------------- Filtros (sidebar) -----------------
st.sidebar.header("🎛️ Filtros")
if df["Year"].notna().any():
    min_year = int(df["Year"].min())
    max_year = int(df["Year"].max())
    year_range = st.sidebar.slider(
        "Rango de años", min_year, max_year, (min_year, max_year)
    )
else:
    year_range = (0, 9999)

if df["Your Rating"].notna().any():
    min_rating = int(df["Your Rating"].min())
    max_rating = int(df["Your Rating"].max())
    rating_range = st.sidebar.slider(
        "Mi nota (Your Rating)", min_rating, max_rating,
        (min_rating, max_rating)
    )
else:
    rating_range = (0, 10)

all_genres = sorted(set(g for sub in df["GenreList"].dropna() for g in sub if g))
selected_genres = st.sidebar.multiselect(
    "Géneros (todas seleccionadas deben estar presentes)",
    options=all_genres
)

all_directors = sorted(set(d.strip() for d in df["Directors"].dropna() if str(d).strip()))
selected_directors = st.sidebar.multiselect("Directores", options=all_directors)

order_by = st.sidebar.selectbox(
    "Ordenar por", ["Your Rating", "IMDb Rating", "Year", "Title", "Aleatorio"]
)
order_asc = st.sidebar.checkbox("Orden ascendente", value=False)

# ----------------- Aplicar filtros básicos -----------------
filtered = df.copy()

filtered = filtered[
    (filtered["Year"] >= year_range[0]) &
    (filtered["Year"] <= year_range[1])
]

filtered = filtered[
    (filtered["Your Rating"] >= rating_range[0]) &
    (filtered["Your Rating"] <= rating_range[1])
]

if selected_genres:
    filtered = filtered[
        filtered["GenreList"].apply(lambda gl: all(g in gl for g in selected_genres))
    ]

if selected_directors:
    def match_dir(cell):
        if pd.isna(cell): return False
        dirs = [d.strip() for d in str(cell).split(",") if d.strip()]
        return any(d in dirs for d in selected_directors)
    filtered = filtered[filtered["Directors"].apply(match_dir)]

st.caption(
    f"Filtros activos → Años: {year_range[0]}–{year_range[1]} | "
    f"Mi nota: {rating_range[0]}–{rating_range[1]} | "
    f"Géneros: {', '.join(selected_genres) if selected_genres else 'Todos'} | "
    f"Directores: {', '.join(selected_directors) if selected_directors else 'Todos'}"
)

# ----------------- Búsqueda rápida -----------------
st.markdown("## 🔎 Búsqueda en mi catálogo")
search_query = st.text_input(
    "Buscar por título, director, género, año o calificaciones",
    placeholder="Escribe cualquier cosa…"
)
def apply_search(df_in, query):
    if not query:
        return df_in
    q = query.strip().lower()
    return df_in[df_in["SearchText"].str.contains(q, na=False, regex=False)]

filtered_view = apply_search(filtered.copy(), search_query)

# Ordenado
if order_by == "Aleatorio":
    if not filtered_view.empty:
        filtered_view = filtered_view.sample(frac=1)
elif order_by in filtered_view.columns:
    filtered_view = filtered_view.sort_values(order_by, ascending=order_asc)

# ----------------- TABS principales -----------------
tab_catalog, tab_analysis, tab_afi, tab_what = st.tabs(
    ["🎬 Catálogo", "📊 Análisis", "🏆 Lista AFI", "🎲 ¿Qué ver hoy?"]
)

# ----------------- TAB 1: CATÁLOGO -----------------
with tab_catalog:
    st.markdown("## 📋 Resumen de resultados")
    col1, col2, col3 = st.columns(3)
    col1.metric("Películas tras filtros + búsqueda", len(filtered_view))
    col2.metric(
        "Promedio de mi nota",
        f"{filtered_view['Your Rating'].mean():.2f}" if filtered_view["Your Rating"].notna().any() else "N/A"
    )
    col3.metric(
        "Promedio IMDb",
        f"{filtered_view['IMDb Rating'].mean():.2f}" if filtered_view["IMDb Rating"].notna().any() else "N/A"
    )

    st.markdown("### 🗂 Tabla de resultados")
    cols_to_show = [c for c in ["Title","Year","Your Rating","IMDb Rating","Genres","Directors","Date Rated","URL"] if c in filtered_view.columns]
    table_df = filtered_view[cols_to_show].copy()
    display_df = table_df.copy()
    if "Year" in display_df.columns:
        display_df["Year"] = display_df["Year"].apply(lambda y: f"{int(y)}" if pd.notna(y) else "")
    if "Your Rating" in display_df.columns:
        display_df["Your Rating"] = display_df["Your Rating"].apply(lambda v: f"{v:.1f}" if pd.notna(v) else "")
    if "IMDb Rating" in display_df.columns:
        display_df["IMDb Rating"] = display_df["IMDb Rating"].apply(lambda v: f"{v:.1f}" if pd.notna(v) else "")

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv_filtered = table_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Descargar resultados filtrados (CSV)",
        data=csv_filtered,
        file_name="mis_peliculas_filtradas.csv",
        mime="text/csv"
    )

    st.markdown("---")
    st.markdown("## 🧱 Galería visual")
    total_pelis = len(filtered_view)
    if total_pelis == 0:
        st.info("No hay películas con los filtros seleccionados.")
    else:
        page_size = st.sidebar.slider(
            "Películas por página en galería", min_value=12, max_value=60, value=24, step=12
        )
        num_pages = max(math.ceil(total_pelis / page_size), 1)
        if "gallery_current_page" not in st.session_state:
            st.session_state.gallery_current_page = 1
        if st.session_state.gallery_current_page > num_pages:
            st.session_state.gallery_current_page = num_pages
        if st.session_state.gallery_current_page < 1:
            st.session_state.gallery_current_page = 1

        nav1, nav2, nav3 = st.columns([1,2,1])
        with nav1:
            if st.button("◀ Anterior", disabled=st.session_state.gallery_current_page<=1):
                st.session_state.gallery_current_page -= 1
        with nav3:
            if st.button("Siguiente ▶", disabled=st.session_state.gallery_current_page>=num_pages):
                st.session_state.gallery_current_page += 1
        with nav2:
            st.caption(f"Página {st.session_state.gallery_current_page} de {num_pages}")

        st.caption(f"Mostrando {total_pelis} películas · {page_size} por página")
        start_idx = (st.session_state.gallery_current_page - 1) * page_size
        end_idx = start_idx + page_size
        page_df = filtered_view.iloc[start_idx:end_idx].copy()

        st.markdown("<div class='movie-gallery-grid'>", unsafe_allow_html=True)
        for _, row in page_df.iterrows():
            titulo = row.get("Title", "Sin título")
            year = row.get("Year", "")
            nota = row.get("Your Rating", "")
            imdb_rating = row.get("IMDb Rating", "")
            genres = row.get("Genres", "")
            directors = row.get("Directors", "")
            url = row.get("URL", "")

            base_rating = nota if pd.notna(nota) else imdb_rating
            border_color, glow_color = get_rating_colors(base_rating)

            poster_url = None
            if use_tmdb_gallery:
                tmdb_info = get_tmdb_basic_info(titulo, year)
                if tmdb_info:
                    poster_url = tmdb_info.get("poster_url")

            if poster_url:
                poster_html = f"""<div class="movie-poster-frame"><img src="{poster_url}" class="movie-poster-img"></div>"""
            else:
                poster_html = """<div class="movie-poster-frame" style="background:#111;"><div style="height:100%;display:flex;align-items:center;justify-content:center;color:#888;">Sin póster</div></div>"""

            year_str = f" ({int(year)})" if pd.notna(year) else ""
            nota_str = f"⭐ Mi nota: {float(nota):.1f}" if pd.notna(nota) else ""
            imdb_str = f"IMDb: {float(imdb_rating):.1f}" if pd.notna(imdb_rating) else ""

            reseñas_html = ""
            link_html = ""
            if url and str(url).startswith("http"):
                link_html = f'<a href="{url}" target="_blank">Ver en IMDb</a><br>'
            review_link = get_spanish_review_link(titulo, year)
            if review_link:
                reseñas_html = f'<a href="{review_link}" target="_blank">Reseñas en español</a><br>'

            st.markdown(f"""
<div class="movie-card" style="border-color:{border_color};box-shadow:0 0 0 1px rgba(15,23,42,0.9),0 0 20px {glow_color};">
  {poster_html}
  <div class="movie-title">{titulo}{year_str}</div>
  <div class="movie-sub">
    {nota_str}<br>
    {imdb_str}<br>
    <b>Géneros:</b> {genres}<br>
    <b>Director(es):</b> {directors}<br>
    {link_html}
    {reseñas_html}
  </div>
</div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## ⭐ Mis favoritas (nota ≥ 9)")
    with st.expander("Mostrar favoritas", expanded=False):
        if "Your Rating" in filtered_view.columns:
            fav = filtered_view[filtered_view["Your Rating"] >= 9].copy()
            if not fav.empty:
                fav = fav.sort_values(["Your Rating","Year"], ascending=[False,True]).head(12)
                for _, row in fav.iterrows():
                    titulo = row.get("Title", "Sin título")
                    year = row.get("Year", "")
                    nota = row.get("Your Rating", "")
                    imdb_rating = row.get("IMDb Rating", "")
                    genres = row.get("Genres", "")
                    directors = row.get("Directors", "")
                    url = row.get("URL", "")

                    border_color, glow_color = get_rating_colors(nota)
                    st.markdown(f"""
<div class="movie-card" style="border-color:{border_color};box-shadow:0 0 0 1px rgba(15,23,42,0.9),0 0 24px {glow_color};margin-bottom:16px;">
  <div class="movie-title">{titulo} ({int(year)})</div>
  <div class="movie-sub">
    ⭐ Mi nota: {float(nota):.1f}<br>
    IMDb: {float(imdb_rating):.1f}<br>
    <b>Géneros:</b> {genres}<br>
    <b>Director(es):</b> {directors}<br>
    {f'<a href="{url}" target="_blank">Ver en IMDb</a><br>' if url and str(url).startswith("http") else ""}
  </div>
</div>
                    """, unsafe_allow_html=True)
            else:
                st.write("No hay películas con nota ≥ 9 bajo los filtros seleccionados.")
        else:
            st.write("Columna 'Your Rating' no disponible.")

# ----------------- TAB 2: ANÁLISIS -----------------
with tab_analysis:
    st.markdown("## 📊 Análisis y tendencias")
    st.caption("Los gráficos usan los filtros de la barra lateral (no la búsqueda).")

    with st.expander("Ver análisis", expanded=False):
        if filtered.empty:
            st.info("No hay datos bajo los filtros seleccionados.")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Películas por año**")
                by_year = (
                    filtered[filtered["Year"].notna()]
                    .groupby("Year")
                    .size()
                    .reset_index(name="Count")
                    .sort_values("Year")
                )
                if not by_year.empty:
                    by_year["Year"] = by_year["Year"].astype(int).astype(str)
                    st.line_chart(by_year.set_index("Year")["Count"])
                else:
                    st.write("Sin datos de año suficientes.")

            with col_b:
                st.markdown("**Distribución de mi nota**")
                if filtered["Your Rating"].notna().any():
                    ratings_counts = (
                        filtered["Your Rating"]
                        .dropna()
                        .round()
                        .astype(int)
                        .value_counts()
                        .sort_index()
                        .reset_index()
                    )
                    ratings_counts.columns = ["Rating", "Count"]
                    ratings_counts = ratings_counts.set_index("Rating")
                    st.bar_chart(ratings_counts["Count"])
                else:
                    st.write("No hay notas propias disponibles.")

            st.markdown("---")
            st.markdown("*Más análisis disponible...*")

# ----------------- TAB 3: LISTA AFI -----------------
with tab_afi:
    st.markdown("## 🎬 AFI 100 Years...100 Movies")
    with st.expander("Mi progreso en la lista AFI", expanded=True):
        afi_df = pd.DataFrame(AFI_LIST)
        afi_df["NormTitle"] = afi_df["Title"].apply(normalize_title)
        afi_df["YearInt"] = afi_df["Year"]

        if "NormTitle" not in df.columns:
            df["NormTitle"] = df["Title"].apply(normalize_title)
        if "YearInt" not in df.columns:
            df["YearInt"] = df["Year"].fillna(-1).astype(int)

        def find_match(afi_norm, year_int, df_full):
            cands = df_full[df_full["YearInt"] == year_int]
            exact = cands[cands["NormTitle"] == afi_norm]
            if not exact.empty:
                return exact.iloc[0]
            partial = cands[cands["NormTitle"].str.contains(afi_norm, na=False)]
            if not partial.empty:
                return partial.iloc[0]
            # fallback search in whole
            exact2 = df_full[df_full["NormTitle"] == afi_norm]
            if not exact2.empty:
                return exact2.iloc[0]
            partial2 = df_full[df_full["NormTitle"].str.contains(afi_norm, na=False)]
            if not partial2.empty:
                return partial2.iloc[0]
            return None

        afi_df["Your Rating"] = pd.NA
        afi_df["IMDb Rating"] = pd.NA
        afi_df["URL"] = ""
        afi_df["Seen"] = False

        for idx, row in afi_df.iterrows():
            match = find_match(row["NormTitle"], row["YearInt"], df)
            if match is not None:
                afi_df.at[idx, "Your Rating"] = match.get("Your Rating")
                afi_df.at[idx, "IMDb Rating"] = match.get("IMDb Rating")
                afi_df.at[idx, "URL"] = match.get("URL", "")
                afi_df.at[idx, "Seen"] = True

        total_afi = len(afi_df)
        seen_afi = int(afi_df["Seen"].sum())
        pct_afi = seen_afi / total_afi if total_afi > 0 else 0.0

        col1_afi, col2_afi = st.columns(2)
        col1_afi.metric("Películas vistas del listado AFI", f"{seen_afi}/{total_afi}")
        col2_afi.metric("Progreso en AFI 100", f"{pct_afi*100:.1f}%")
        st.progress(pct_afi)

        afi_display = afi_df[["Rank","Title","Year","Seen","Your Rating","IMDb Rating","URL"]].copy()
        afi_display["Year"] = afi_display["Year"].astype(int).astype(str)
        afi_display["Your Rating"] = afi_display["Your Rating"].apply(lambda v: f"{v:.1f}" if pd.notna(v) else "")
        afi_display["IMDb Rating"] = afi_display["IMDb Rating"].apply(lambda v: f"{v:.1f}" if pd.notna(v) else "")

        st.dataframe(afi_display, use_container_width=True, hide_index=True)

# ----------------- TAB 4: ¿QUÉ VER HOY? -----------------
with tab_what:
    st.markdown("## 🎲 ¿Qué ver hoy?")
    st.write("Selecciono una película al azar de tu catálogo según tus notas y filtros.")

    with st.expander("Generar recomendación aleatoria", expanded=True):
        modo = st.selectbox(
            "Modo de recomendación",
            ["Entre todas las películas filtradas", "Solo mis favoritas (nota ≥ 9)", "Entre mis ≥8 de los últimos 20 años"]
        )
        if st.button("Recomendar película"):
            pool = filtered.copy()
            if modo == "Solo mis favoritas (nota ≥ 9)":
                pool = pool[pool["Your Rating"] >= 9]
            elif modo == "Entre mis ≥8 de los últimos 20 años":
                current_year = pd.Timestamp.now().year
                pool = pool[(pool["Your Rating"] >= 8) & (pool["Year"] >= (current_year - 20))]
            if pool.empty:
                st.warning("No hay películas que cumplan con los criterios seleccionados.")
            else:
                if pool["Your Rating"].notna().any():
                    pesos = pool["Your Rating"].fillna(0).tolist()
                else:
                    pesos = None
                idx = random.choices(pool.index.tolist(), weights=pesos, k=1)[0] if pesos else random.choice(pool.index.tolist())
                peli = pool.loc[idx]

                titulo = peli.get("Title", "Sin título")
                year = peli.get("Year", "")
                nota = peli.get("Your Rating", "")
                imdb_rating = peli.get("IMDb Rating", "")
                genres = peli.get("Genres", "")
                directors = peli.get("Directors", "")
                url = peli.get("URL", "")

                border_color, glow_color = get_rating_colors(nota if pd.notna(nota) else imdb_rating)
                tmdb_info = get_tmdb_basic_info(titulo, year)
                poster_url = tmdb_info.get("poster_url") if tmdb_info else None
                tmdb_id = tmdb_info.get("id") if tmdb_info else None
                availability = get_tmdb_providers(tmdb_id, country="CL") if tmdb_id else None

                st.markdown(f"<div class='movie-card' style='border-color:{border_color};box-shadow:0 0 0 1px rgba(15,23,42,0.9),0 0 26px {glow_color};padding:0.5rem;'>", unsafe_allow_html=True)
                col_img, col_info = st.columns([1,3])
                with col_img:
                    if poster_url:
                        st.image(poster_url, use_column_width=True)
                    else:
                        st.write("Sin póster disponible")
                    if show_trailers:
                        trailer_url = get_youtube_trailer_url(titulo, year)
                        if trailer_url:
                            st.video(trailer_url)
                with col_info:
                    st.markdown(f"### {titulo} ({int(year) if pd.notna(year) else ''})")
                    st.write(f"**Mi nota:** {float(nota):.1f}" if pd.notna(nota) else "")
                    st.write(f"**IMDb:** {float(imdb_rating):.1f}" if pd.notna(imdb_rating) else "")
                    st.write(f"**Géneros:** {genres}")
                    st.write(f"**Director(es):** {directors}")
                    if url and str(url).startswith("http"):
                        st.write(f"[Ver en IMDb]({url})")
                    review_link = get_spanish_review_link(titulo, year)
                    if review_link:
                        st.write(f"[Reseñas en español]({review_link})")
                    if availability:
                        st.write(f"**Streaming en CL:** {', '.join(availability.get('platforms',[]))}")
                        if availability.get("link"):
                            st.write(f"[Ver opciones de streaming]({availability.get('link')})")
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("### 🎯 Recomendaciones similares dentro de mi catálogo")
                recs_cat = recommend_from_catalog(df, peli, top_n=5)
                if recs_cat.empty:
                    st.info("No se encontraron películas similares dentro de tu catálogo.")
                else:
                    for _, r in recs_cat.iterrows():
                        yr = int(r.get("Year")) if pd.notna(r.get("Year")) else ""
                        st.write(f"- **{r.get('Title')}** ({yr}) · Mi nota: {r.get('Your Rating')} · IMDb: {r.get('IMDb Rating')}")

                st.markdown("### 🌐 Recomendaciones externas (TMDb similares)")
                if tmdb_id:
                    similars = get_tmdb_similar_movies(tmdb_id, language="es-ES", max_results=8)
                    if not similars:
                        st.info("No hay recomendaciones externas disponibles para esta película.")
                    else:
                        cols = st.columns(4)
                        for i, m in enumerate(similars):
                            with cols[i % 4]:
                                t_sim = m.get("title")
                                y_sim = m.get("year")
                                poster_sim = m.get("poster_url")
                                st.write(f"**{t_sim}** ({y_sim if y_sim else ''})")
                                if poster_sim:
                                    st.image(poster_sim, use_column_width=True)
                                st.caption(f"TMDb valoración: {float(m.get('vote_average')):.1f}" if m.get("vote_average") else "")
                else:
                    st.info("No hay ID TMDb para esta película, no se pueden obtener similares.")

                st.markdown("---")
                st.markdown("### 📌 Otras sugerencias basadas en mis mejores valoradas")
                top_sug = filtered.copy()
                if "Your Rating" in top_sug.columns:
                    top_sug = top_sug[top_sug["Your Rating"].notna()].sort_values(["Your Rating","IMDb Rating","Year"], ascending=[False,False,False]).head(10)
                    top_sug = top_sug[["Title","Year","Your Rating","IMDb Rating","Genres"]].copy()
                    top_sug["Year"] = top_sug["Year"].apply(lambda y: int(y) if pd.notna(y) else "")
                    top_sug["Mi nota"] = top_sug["Your Rating"].apply(lambda v: f"{v:.1f}")
                    top_sug["IMDb"] = top_sug["IMDb Rating"].apply(lambda v: f"{v:.1f}")
                    st.dataframe(top_sug.rename(columns={"Title":"Película","Year":"Año","Mi nota":"Mi nota","IMDb":"IMDb","Genres":"Géneros"}), hide_index=True, use_container_width=True)
                else:
                    st.write("Columna 'Your Rating' no disponible para sugerencias.")

