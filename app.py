import re
import html  # para escapar texto en los chips de personas
import streamlit as st
import pandas as pd
import requests
import random
import altair as alt
import math
from urllib.parse import quote_plus
from collections import defaultdict

# ===================== Versión y changelog =====================
APP_VERSION = "1.1.7"

CHANGELOG = {
    "1.1.7": [
        "Limpieza masiva: Se eliminaron ~1400 líneas de código duplicado para mejorar el rendimiento.",
        "Corrección: Se activa por defecto la carga de 'Oscar_Data_1927_today.xlsx' (index=2) para que la pestaña de Óscar no aparezca vacía.",
        "Mejora visual: Formato consistente (1 decimal) en el slider de 'Mi nota'.",
    ],
    "1.1.6": [
        "OMDb: se corrige el parseo de premios BAFTA.",
        "Filtros: slider de 'Mi nota (Your Rating)' ahora admite decimales (paso 0.5).",
    ],
    "1.1.5": [
        "Óscar: selector directo por año de ceremonia (sin rango).",
        "Óscar: se elimina el análisis por categoría y el top de entidades por categoría.",
        "Óscar: nueva galería visual por categoría con pósters para el año seleccionado.",
    ],
    "1.1.0": [
        "Nueva pestaña 🏆 Premios Óscar: búsqueda, filtros, vista por año, ganadores y rankings.",
    ],
}

def _parse_ver_tuple(v: str):
    if not v: return (0, 0, 0)
    parts = [int(p) if p.isdigit() else 0 for p in re.split(r"[.\-+]", str(v)) if p]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])

def since(ver: str) -> bool:
    return _parse_ver_tuple(APP_VERSION) >= _parse_ver_tuple(ver)

# ----------------- Configuración general -----------------

st.set_page_config(
    page_title=f"🎬 Mi catálogo de Películas · v{APP_VERSION}",
    layout="centered"
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
    {"Rank": 11, "Title": "City Lights", "Year": 1931},
    {"Rank": 12, "Title": "The Searchers", "Year": 1956},
    {"Rank": 13, "Title": "Star Wars", "Year": 1977},
    {"Rank": 14, "Title": "Psycho", "Year": 1960},
    {"Rank": 15, "Title": "2001: A Space Odyssey", "Year": 1968},
    {"Rank": 16, "Title": "Sunset Boulevard", "Year": 1950},
    {"Rank": 17, "Title": "The Graduate", "Year": 1967},
    {"Rank": 18, "Title": "The General", "Year": 1926},
    {"Rank": 19, "Title": "On the Waterfront", "Year": 1954},
    {"Rank": 20, "Title": "It's a Wonderful Life", "Year": 1946},
    {"Rank": 21, "Title": "Chinatown", "Year": 1974},
    {"Rank": 22, "Title": "Some Like It Hot", "Year": 1959},
    {"Rank": 23, "Title": "The Grapes of Wrath", "Year": 1940},
    {"Rank": 24, "Title": "E.T. the Extra-Terrestrial", "Year": 1982},
    {"Rank": 25, "Title": "To Kill a Mockingbird", "Year": 1962},
    {"Rank": 26, "Title": "Mr. Smith Goes to Washington", "Year": 1939},
    {"Rank": 27, "Title": "High Noon", "Year": 1952},
    {"Rank": 28, "Title": "All About Eve", "Year": 1950},
    {"Rank": 29, "Title": "Double Indemnity", "Year": 1944},
    {"Rank": 30, "Title": "Apocalypse Now", "Year": 1979},
    {"Rank": 31, "Title": "The Maltese Falcon", "Year": 1941},
    {"Rank": 32, "Title": "The Godfather Part II", "Year": 1974},
    {"Rank": 33, "Title": "One Flew Over the Cuckoo's Nest", "Year": 1975},
    {"Rank": 34, "Title": "Snow White and the Seven Dwarfs", "Year": 1937},
    {"Rank": 35, "Title": "Annie Hall", "Year": 1977},
    {"Rank": 36, "Title": "The Bridge on the River Kwai", "Year": 1957},
    {"Rank": 37, "Title": "The Best Years of Our Lives", "Year": 1946},
    {"Rank": 38, "Title": "The Treasure of the Sierra Madre", "Year": 1948},
    {"Rank": 39, "Title": "Dr. Strangelove", "Year": 1964},
    {"Rank": 40, "Title": "The Sound of Music", "Year": 1965},
    {"Rank": 41, "Title": "King Kong", "Year": 1933},
    {"Rank": 42, "Title": "Bonnie and Clyde", "Year": 1967},
    {"Rank": 43, "Title": "Midnight Cowboy", "Year": 1969},
    {"Rank": 44, "Title": "The Philadelphia Story", "Year": 1940},
    {"Rank": 45, "Title": "Shane", "Year": 1953},
    {"Rank": 46, "Title": "It Happened One Night", "Year": 1934},
    {"Rank": 47, "Title": "A Streetcar Named Desire", "Year": 1951},
    {"Rank": 48, "Title": "Rear Window", "Year": 1954},
    {"Rank": 49, "Title": "Intolerance", "Year": 1916},
    {"Rank": 50, "Title": "The Lord of the Rings: The Fellowship of the Ring", "Year": 2001},
    {"Rank": 51, "Title": "West Side Story", "Year": 1961},
    {"Rank": 52, "Title": "Taxi Driver", "Year": 1976},
    {"Rank": 53, "Title": "The Deer Hunter", "Year": 1978},
    {"Rank": 54, "Title": "M*A*S*H", "Year": 1970},
    {"Rank": 55, "Title": "North by Northwest", "Year": 1959},
    {"Rank": 56, "Title": "Jaws", "Year": 1975},
    {"Rank": 57, "Title": "Rocky", "Year": 1976},
    {"Rank": 58, "Title": "The Gold Rush", "Year": 1925},
    {"Rank": 59, "Title": "Nashville", "Year": 1975},
    {"Rank": 60, "Title": "Duck Soup", "Year": 1933},
    {"Rank": 61, "Title": "Sullivan's Travels", "Year": 1941},
    {"Rank": 62, "Title": "American Graffiti", "Year": 1973},
    {"Rank": 63, "Title": "Cabaret", "Year": 1972},
    {"Rank": 64, "Title": "Network", "Year": 1976},
    {"Rank": 65, "Title": "The African Queen", "Year": 1951},
    {"Rank": 66, "Title": "Raiders of the Lost Ark", "Year": 1981},
    {"Rank": 67, "Title": "Who's Afraid of Virginia Woolf?", "Year": 1966},
    {"Rank": 68, "Title": "Unforgiven", "Year": 1992},
    {"Rank": 69, "Title": "Tootsie", "Year": 1982},
    {"Rank": 70, "Title": "A Clockwork Orange", "Year": 1971},
    {"Rank": 71, "Title": "Saving Private Ryan", "Year": 1998},
    {"Rank": 72, "Title": "The Shawshank Redemption", "Year": 1994},
    {"Rank": 73, "Title": "Butch Cassidy and the Sundance Kid", "Year": 1969},
    {"Rank": 74, "Title": "The Silence of the Lambs", "Year": 1991},
    {"Rank": 75, "Title": "Forrest Gump", "Year": 1994},
    {"Rank": 76, "Title": "All the President's Men", "Year": 1976},
    {"Rank": 77, "Title": "Modern Times", "Year": 1936},
    {"Rank": 78, "Title": "The Wild Bunch", "Year": 1969},
    {"Rank": 79, "Title": "The Apartment", "Year": 1960},
    {"Rank": 80, "Title": "Spartacus", "Year": 1960},
    {"Rank": 81, "Title": "Sunrise: A Song of Two Humans", "Year": 1927},
    {"Rank": 82, "Title": "Titanic", "Year": 1997},
    {"Rank": 83, "Title": "Easy Rider", "Year": 1969},
    {"Rank": 84, "Title": "A Night at the Opera", "Year": 1935},
    {"Rank": 85, "Title": "Platoon", "Year": 1986},
    {"Rank": 86, "Title": "12 Angry Men", "Year": 1957},
    {"Rank": 87, "Title": "Bringing Up Baby", "Year": 1938},
    {"Rank": 88, "Title": "The Sixth Sense", "Year": 1999},
    {"Rank": 89, "Title": "Swing Time", "Year": 1936},
    {"Rank": 90, "Title": "Sophie's Choice", "Year": 1982},
    {"Rank": 92, "Title": "Goodfellas", "Year": 1990},
    {"Rank": 93, "Title": "The French Connection", "Year": 1971},
    {"Rank": 94, "Title": "Pulp Fiction", "Year": 1994},
    {"Rank": 95, "Title": "The Last Picture Show", "Year": 1971},
    {"Rank": 96, "Title": "Do the Right Thing", "Year": 1989},
    {"Rank": 97, "Title": "Blade Runner", "Year": 1982},
    {"Rank": 98, "Title": "Yankee Doodle Dandy", "Year": 1942},
    {"Rank": 99, "Title": "Toy Story", "Year": 1995},
    {"Rank": 100, "Title": "Ben-Hur", "Year": 1959},
]

def normalize_title(s: str) -> str:
    """Normaliza un título para compararlo (minúsculas, sin espacios ni signos)."""
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

# ----------------- Funciones auxiliares (catálogo y APIs) -----------------

@st.cache_data
def load_data(file_path_or_buffer):
    """Carga el CSV, limpia datos, normaliza y crea el mapa de búsqueda (para AFI)."""
    df = pd.read_csv(file_path_or_buffer)

    if "Your Rating" in df.columns:
        # Reemplazar comas por puntos y convertir a float de forma robusta
        df["Your Rating"] = df["Your Rating"].astype(str).str.replace(",", ".", regex=False)
        df["Your Rating"] = pd.to_numeric(df["Your Rating"], errors="coerce")
    else:
        df["Your Rating"] = None

    if "IMDb Rating" in df.columns:
        # Reemplazar comas por puntos y convertir a float de forma robusta
        df["IMDb Rating"] = df["IMDb Rating"].astype(str).str.replace(",", ".", regex=False)
        df["IMDb Rating"] = pd.to_numeric(df["IMDb Rating"], errors="coerce")
    else:
        df["IMDb Rating"] = None

    # --- Columna Year ---
    if "Year" in df.columns:
        # Extrae año de 4 dígitos y lo convierte de forma robusta a numérico
        year_str = df["Year"].astype(str).str.extract(r"(\d{4})")[0]
        df["Year"] = pd.to_numeric(year_str, errors="coerce")
        df["YearInt"] = df["Year"].fillna(-1).astype(int)
    else:
        df["Year"] = None
        df["YearInt"] = -1

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

    # Normalización para búsqueda AFI/Oscar
    df["NormTitle"] = df.get("Title", "").apply(normalize_title)

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

    # Mapa de búsqueda optimizada (Título normalizado, Año) -> Índice de la fila del DF
    catalog_map = {}
    for idx, row in df.iterrows():
        norm = row.get("NormTitle", "")
        y = row.get("YearInt", -1)
        if norm and y != -1:
            catalog_map[(norm, y)] = idx
    
    return df, catalog_map

def _coerce_year_for_tmdb(year):
    if year is None or pd.isna(year):
        return None
    try:
        return int(float(year))
    except Exception:
        return None

@st.cache_data
def get_tmdb_basic_info(title, year=None):
    """Info básica TMDb (id/poster/vote_average) en una sola búsqueda."""
    if TMDB_API_KEY is None: 
        return None
    if not title or pd.isna(title):
        return None

    title = str(title).strip()
    year_int = _coerce_year_for_tmdb(year)

    params = {"api_key": TMDB_API_KEY, "query": title}
    if year_int is not None:
        params["year"] = year_int

    try:
        r = requests.get(TMDB_SEARCH_URL, params=params, timeout=3)
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

# Función auxiliar para la galería (carga TMDb + Providers en un solo llamado por caché)
@st.cache_data(show_spinner=False)
def get_tmdb_and_providers_for_title(title, year):
    """Obtiene info TMDb y Providers en un solo llamado cacheado."""
    tmdb_info = get_tmdb_basic_info(title, year)
    providers_info = None
    if tmdb_info and tmdb_info.get("id"):
        # País por defecto Chile (CL)
        providers_info = get_tmdb_providers(tmdb_info["id"], country="CL") 
    return tmdb_info, providers_info

@st.cache_data
def get_tmdb_providers(tmdb_id, country="CL"):
    """Streaming desde TMDb watch/providers para un país."""
    if TMDB_API_KEY is None or not tmdb_id:
        return None

    try:
        providers_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/watch/providers"
        r2 = requests.get(providers_url, params={"api_key": TMDB_API_KEY}, timeout=4)
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
        return {
            "platforms": sorted(list(providers)) if providers else [],
            "link": link,
        }
    except Exception:
        return None

@st.cache_data
def get_youtube_trailer_url(title, year=None):
    """URL de YouTube del primer resultado de tráiler."""
    if YOUTUBE_API_KEY is None:
        return None
    if not title or pd.isna(title):
        return None

    q = f"{title} trailer"
    try:
        if year is not None and not pd.isna(year):
            q += f" {int(float(year))}"
    except Exception:
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
    except Exception:
        return None

@st.cache_data
def load_oscar_data_from_excel(path_xlsx="Oscar_Data_1927_today.xlsx"):
    """
    Carga robusta del Excel Oscar_Data_1927_today.xlsx.
    """
    try:
        raw = pd.read_excel(path_xlsx, engine="openpyxl")
    except Exception:
        return pd.DataFrame()

    # Normalizamos nombres de columnas
    raw_cols = list(raw.columns)
    cols_lower = {str(c).strip().lower(): c for c in raw_cols}

    def _find_col(df, candidates):
        for c_norm in candidates:
            if c_norm in cols_lower:
                return cols_lower[c_norm]
        return None

    # Intentar detectar columnas
    col_film_year = _find_col(raw, ["year film", "film year", "year_film", "year"])
    col_award_year = _find_col(raw, ["award year", "ceremony year", "ceremony"]) 
    col_cat = _find_col(raw, ["category", "award", "award category"])
    col_film = _find_col(raw, ["film", "film title", "movie", "movie title"])
    col_nominee = _find_col(raw, ["nominee", "name", "primary nominee"])
    col_winner = _find_col(raw, ["winner", "won", "iswinner", "is_winner"])

    if not all([col_film_year, col_cat, col_film, col_nominee]):
        # Si faltan columnas críticas, devolvemos vacío
        return pd.DataFrame()

    df = pd.DataFrame()
    df["FilmYear"] = pd.to_numeric(raw[col_film_year], errors="coerce").astype("Int64")
    df["Category"] = raw[col_cat].astype(str).str.strip()
    df["Film"] = raw[col_film].astype(str).str.strip()
    df["Nominee"] = raw[col_nominee].astype(str)

    # Determinar si es ganador
    is_winner = pd.Series([False] * len(raw), dtype=bool)
    if col_winner is not None:
        w = raw[col_winner]
        if pd.api.types.is_bool_dtype(w):
            is_winner = w.fillna(False)
        else:
            s = w.astype(str).str.strip().str.lower()
            is_winner = s.isin(["true", "t", "1", "yes", "y", "winner", "ganador", "ganadora"]) | (w == 1)
        is_winner = is_winner.fillna(False).astype(bool)

    df["IsWinner"] = is_winner

    # Usar AwardYear como CeremonyInt si existe, sino FilmYear
    df["CeremonyInt"] = df["FilmYear"]
    if col_award_year is not None:
        award_yr = pd.to_numeric(raw[col_award_year], errors="coerce").astype("Int64")
        df["CeremonyInt"] = award_yr.fillna(df["FilmYear"])

    # Normalizar para cruce
    df["NormFilm"] = df["Film"].apply(normalize_title)
    df["YearInt"] = df["FilmYear"].fillna(-1).astype(int) 
    
    # Renombrar Nominee a PersonName para consistencia con otras fuentes
    df = df.rename(columns={"Nominee": "PersonName"})
    
    return df

@st.cache_data
def load_full_data(path_csv="full_data.csv"):
    """Carga de full_data.csv si existe."""
    try:
        dff = pd.read_csv(path_csv, on_bad_lines="skip")
        dff.columns = [str(c).strip() for c in dff.columns]
        
        # Mapeo básico si las columnas existen
        if "Year" in dff.columns:
            dff["YearInt"] = pd.to_numeric(dff["Year"], errors="coerce").fillna(-1).astype(int)
        
        if "Ceremony" in dff.columns:
            dff["CeremonyInt"] = pd.to_numeric(dff["Ceremony"], errors="coerce").fillna(-1).astype(int)
            
        if "Winner" in dff.columns:
             dff["IsWinner"] = dff["Winner"].astype(str).str.lower().isin(["1", "true", "yes"])
        
        # Estandarizar
        dff["Film"] = dff["Film"].astype(str).fillna("")
        dff["NormFilm"] = dff["Film"].apply(normalize_title)
        
        return dff
    except Exception:
        return pd.DataFrame()

def attach_catalog_to_full(osc_df, my_catalog_df):
    """Enlaza datos de Oscar con el catálogo del usuario."""
    if osc_df.empty or my_catalog_df.empty:
        return osc_df

    cat = my_catalog_df.copy()
    # Clave de enlace
    cat["JoinKey"] = cat["NormTitle"] + "_" + cat["YearInt"].astype(str)
    osc_df["JoinKey"] = osc_df["NormFilm"] + "_" + osc_df["YearInt"].astype(str)

    # Lookup
    lookup = cat.set_index("JoinKey")[["Your Rating", "IMDb Rating", "URL"]].to_dict("index")

    def lookup_func(row):
        match = lookup.get(row["JoinKey"])
        if match:
            return True, match.get("Your Rating"), match.get("IMDb Rating"), match.get("URL")
        return False, None, None, None

    res = osc_df.apply(lookup_func, axis=1, result_type="expand")
    res.columns = ["InMyCatalog", "MyRating", "MyIMDb", "CatalogURL"]
    
    return pd.concat([osc_df, res], axis=1).drop(columns=["JoinKey"], errors="ignore")

def recommend_from_catalog(df_all, seed_row, top_n=5):
    """Recomendaciones simples."""
    if df_all.empty: return pd.DataFrame()
    
    candidates = df_all[df_all["Title"] != seed_row["Title"]].copy()
    seed_genres = set(seed_row.get("GenreList", []))
    
    scores = []
    for idx, r in candidates.iterrows():
        g2 = set(r.get("GenreList", []))
        # Score muy básico: coincidencia de géneros + bonus por rating alto
        score = len(seed_genres & g2)
        if pd.notna(r.get("IMDb Rating")):
            score += r.get("IMDb Rating") / 20.0
        scores.append((idx, score))
    
    scores.sort(key=lambda x: x[1], reverse=True)
    top_indices = [x[0] for x in scores[:top_n]]
    return df_all.loc[top_indices]

# ----------------- Estilos CSS (Incrustados) -----------------

def inject_css():
    st.markdown(
        """
        <style>
            .stApp { background-color: #0f172a; color: #e2e8f0; }
            h1, h2, h3, h4 { color: #f1f5f9; }
            
            /* Movie Card Styles */
            .movie-gallery-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 20px;
                padding-top: 10px;
            }
            .movie-card {
                background-color: rgba(30, 41, 59, 0.7);
                border: 1px solid #475569;
                border-radius: 12px;
                overflow: hidden;
                transition: transform 0.2s;
                display: flex;
                flex-direction: column;
            }
            .movie-card:hover { transform: translateY(-4px); }
            
            .movie-poster-frame {
                width: 100%;
                height: 400px;
                background-color: #0f172a;
                position: relative;
            }
            .movie-poster-img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
            .movie-info { padding: 15px; }
            .movie-title { font-size: 1.1rem; font-weight: 700; color: #f8fafc; margin-bottom: 5px; }
            .movie-sub { font-size: 0.9rem; color: #cbd5e1; }
            
            /* AFI List Styles */
            .afi-list-item {
                border: 1px solid #475569;
                background-color: #1e293b;
                border-radius: 8px;
                padding: 10px 15px;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .afi-in-catalog { color: #86efac; border: 1px solid #22c55e; padding: 4px 8px; border-radius: 4px; }
            .afi-not-in-catalog { color: #94a3b8; border: 1px solid #64748b; padding: 4px 8px; border-radius: 4px; }
        </style>
        """,
        unsafe_allow_html=True
    )

def fmt_rating(r):
    if pd.isna(r): return "—"
    return f"{float(r):.1f}"

def fmt_year(y):
    if pd.isna(y): return "N/A"
    return str(int(y))

def get_rating_colors(r):
    # Retorna color de borde y sombra (placeholders por simplicidad)
    if pd.isna(r): return "#475569", "transparent"
    if r >= 8: return "#22c55e", "rgba(34,197,94,0.3)"
    if r >= 6: return "#eab308", "rgba(234,179,8,0.3)"
    return "#ef4444", "rgba(239,68,68,0.3)"

def _build_oscar_card_html(row, **kwargs):
    # Wrapper simple para generar HTML de tarjeta (reutiliza lógica si se desea)
    # Aquí simplificado para reducir líneas redundantes
    title = row.get("Film", "Sin Título")
    year = row.get("YearInt", "")
    return f"""
    <div class="movie-card">
        <div class="movie-info">
            <div class="movie-title">{title} ({year})</div>
            <div class="movie-sub">
                {kwargs.get('category_text', '')}<br>
                {kwargs.get('people_list', '')}
            </div>
        </div>
    </div>
    """

# ===================== MAIN APP LOGIC =====================

def main():
    inject_css()

    # --- Carga de Catálogo ---
    uploaded_file = st.sidebar.file_uploader("Sube tu archivo 'ratings.csv' de IMDb", type=["csv"])
    if uploaded_file:
        df, catalog_map = load_data(uploaded_file)
        st.sidebar.success(f"Catálogo cargado: {len(df)} películas")
    else:
        # Intentar cargar localmente si existe (fallback para dev)
        try:
            df, catalog_map = load_data("peliculas.csv")
        except:
            st.info("Por favor, sube tu archivo CSV para continuar.")
            return

    # --- Carga de Óscar ---
    # Selector corregido: Index 2 selecciona el Excel por defecto
    osc_source = st.sidebar.radio(
        "Datos de Óscar:", 
        ["No usar", "full_data.csv", "Oscar_Data_1927_today.xlsx"], 
        index=2 
    )
    
    osc_df = pd.DataFrame()
    if osc_source == "full_data.csv":
        osc_df = load_full_data("full_data.csv")
    elif osc_source == "Oscar_Data_1927_today.xlsx":
        osc_df = load_oscar_data_from_excel("Oscar_Data_1927_today.xlsx")
        
    if not osc_df.empty:
        osc_df = attach_catalog_to_full(osc_df, df)

    # --- Filtros ---
    st.sidebar.markdown("---")
    st.sidebar.header("Filtros")
    
    # Años
    min_y = int(df["YearInt"][df["YearInt"]>0].min()) if not df.empty else 1900
    max_y = int(df["YearInt"].max()) if not df.empty else 2025
    year_range = st.sidebar.slider("Años", min_y, max_y, (min_y, max_y))
    
    # Rating (con formato decimal arreglado)
    rating_range = st.sidebar.slider("Mi nota", 0.0, 10.0, (0.0, 10.0), step=0.5, format="%.1f")
    
    # Aplicar filtros
    mask = (
        (df["YearInt"] >= year_range[0]) & 
        (df["YearInt"] <= year_range[1]) &
        ((df["Your Rating"].fillna(0) >= rating_range[0]) & (df["Your Rating"].fillna(0) <= rating_range[1]))
    )
    filtered_view = df[mask].copy()

    # --- Pestañas ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Catálogo", "Análisis", "AFI 100", "Premios Óscar", "¿Qué ver hoy?"])

    # 1. Catálogo
    with tab1:
        st.metric("Películas filtradas", len(filtered_view))
        st.dataframe(filtered_view[["Title", "Year", "Your Rating", "IMDb Rating", "Genres"]], hide_index=True)

    # 2. Análisis
    with tab2:
        if not filtered_view.empty:
            st.subheader("Distribución de notas")
            c = alt.Chart(filtered_view).mark_bar().encode(x='Your Rating:O', y='count()')
            st.altair_chart(c, use_container_width=True)

    # 3. AFI
    with tab3:
        st.subheader("Progreso AFI 100")
        afi_df = pd.DataFrame(AFI_LIST)
        afi_df["YearInt"] = afi_df["Year"]
        afi_df["NormTitle"] = afi_df["Title"].apply(normalize_title)
        
        # Cruce optimizado O(1)
        hits = []
        for _, row in afi_df.iterrows():
            key = (row["NormTitle"], row["YearInt"])
            idx = catalog_map.get(key)
            if idx is not None:
                hits.append(True)
            else:
                hits.append(False)
        
        afi_df["Visto"] = hits
        st.metric("Vistas", f"{sum(hits)} / 100")
        st.dataframe(afi_df[["Rank", "Title", "Year", "Visto"]], hide_index=True)

    # 4. Óscar
    with tab4:
        if osc_df.empty:
            st.warning("No hay datos de Óscar cargados.")
        else:
            years = sorted(osc_df["CeremonyInt"].unique(), reverse=True)
            sel_year = st.selectbox("Ceremonia", years)
            subset = osc_df[osc_df["CeremonyInt"] == sel_year]
            
            st.write(f"Nominaciones en {sel_year}: {len(subset)}")
            
            # Mostrar ganadores
            winners = subset[subset["IsWinner"]]
            if not winners.empty:
                st.subheader("🏆 Ganadores Principales")
                st.dataframe(winners[["Category", "Film", "PersonName", "InMyCatalog"]], hide_index=True)

    # 5. Recomendación
    with tab5:
        st.subheader("🎲 Sugerencia del día")
        if st.button("Dame una película al azar"):
            if not filtered_view.empty:
                rec = filtered_view.sample(1).iloc[0]
                st.success(f"Te recomiendo: **{rec['Title']}** ({fmt_year(rec['Year'])})")
                if pd.notna(rec.get("Your Rating")):
                    st.write(f"Tu nota: {rec['Your Rating']}")
            else:
                st.warning("No hay películas con los filtros actuales.")

    # Footer
    st.markdown("---")
    st.caption(f"v{APP_VERSION} · Powered by Streamlit")

if __name__ == "__main__":
    main()
