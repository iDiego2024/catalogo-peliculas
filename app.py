import streamlit as st
import pandas as pd
import requests
import random
import altair as alt
import re
import math
from urllib.parse import quote_plus
from thefuzz import fuzz

# ===================== Versión y changelog =====================
APP_VERSION = "1.2.0"

CHANGELOG = {
    "1.2.0": [
        "Rendimiento: Se activa 'persist=\"disk\"' en las consultas a APIs (TMDb, OMDb, YouTube). Los datos se guardan en disco para sesiones futuras.",
        "Nuevo Tab: '🔍 Ficha Detallada'. Buscador específico para ver póster en grande, sinopsis, cast y premios detallados de una película.",
        "Nuevo Tab: '🎬 Directores'. Estadísticas de directores (cantidad vs calidad) y gráficos interactivos.",
        "Corrección: Reestructuración del código para evitar errores de definición (NameError) en la carga de datos.",
    ],
    "1.1.7": [
        "Búsqueda: Se implementa 'Fuzzy Search' (búsqueda difusa).",
        "Búsqueda: Los resultados se ordenan por relevancia.",
    ],
    "1.1.6": [
        "Sidebar: Se eliminan opciones de visualización (TMDb, Tráilers, Pósters) dejándolas activas por defecto.",
        "UX: La opción avanzada de consultar premios OMDb se mueve bajo la sección de Filtros.",
    ],
    "1.1.5": [
        "Óscar: selector directo por año de ceremonia (sin rango).",
        "Óscar: nueva galería visual por categoría con pósters para el año seleccionado.",
    ],
    # ... (Se mantienen versiones anteriores en el historial)
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
    layout="centered"
)

st.title("🎥 Mi catálogo de películas (IMDb)")

# ----------------- Config APIs externas -----------------

TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500" # Calidad aumentada para ficha detalle

TMDB_SIMILAR_URL_TEMPLATE = "https://api.themoviedb.org/3/movie/{movie_id}/similar"

YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", None)
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# ----------------- Lista AFI 100 -----------------

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

# --- AQUÍ PEGAS EL CÓDIGO FALTANTE ---
def fmt_year(y):
    if pd.isna(y):
        return ""
    return f"{int(float(y))}"

def fmt_rating(v):
    if pd.isna(v):
        return ""
    try:
        return f"{float(v):.1f}"
    except Exception:
        return str(v)
# --------------------------------------

# ===================== FUNCIONES AUXILIARES GLOBALES =====================

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

    if "Year" in df.columns:
        # Extrae año de 4 dígitos y lo convierte de forma robusta a numérico
        year_str = df["Year"].astype(str).str.extract(r"(\d{4})")[0]
        df["Year"] = pd.to_numeric(year_str, errors="coerce")
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

    return df

def _coerce_year_for_tmdb(year):
    if year is None or pd.isna(year):
        return None
    try:
        return int(float(year))
    except Exception:
        return None

# --- OPTIMIZACIÓN v1.2.0: persist="disk" ---
@st.cache_data(persist="disk")
def get_tmdb_basic_info(title, year=None):
    """Info básica TMDb (id/poster/vote_average/overview) en una sola búsqueda."""
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
        overview = movie.get("overview") # Nuevo en v1.2.0

        return {
            "id": movie_id,
            "poster_url": f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None,
            "vote_average": vote_average,
            "overview": overview
        }
    except Exception:
        return None

@st.cache_data(persist="disk")
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

@st.cache_data(persist="disk")
def get_tmdb_similar_movies(tmdb_id, language="es-ES", max_results=10):
    """Películas similares desde TMDb."""
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
            title = m.get("title") or m.get("name")
            date_str = m.get("release_date") or ""
            year = None
            if date_str:
                try:
                    year = int(date_str[:4])
                except Exception:
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

@st.cache_data(persist="disk")
def get_youtube_trailer_url(title, year=None, language_hint="es"):
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

@st.cache_data(persist="disk")
def get_omdb_awards(title, year=None):
    """Info de premios desde OMDb (texto + parseo básico)."""
    api_key = st.secrets.get("OMDB_API_KEY", None)
    if api_key is None:
        return {"error": "OMDB_API_KEY no está configurada en st.secrets."}
    if not title or pd.isna(title):
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
    last_error = None

    for t in [raw_title, simple_title]:
        params = {"apikey": api_key, "t": t, "type": "movie"}
        if year_int:
            params["y"] = year_int
        candidate = _query(params)
        if candidate is None:
            continue
        if "error" in candidate:
            last_error = candidate["error"]
        else:
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
                    last_error = data["error"]
        elif search and "error" in search:
            last_error = search["error"]

    if data is None:
        return {"error": last_error or "No se encontró la película en OMDb."}
    if "error" in data:
        return {"error": data["error"]}

    awards_str = data.get("Awards", "")
    plot_str = data.get("Plot", "Sin sinopsis disponible.") # Nuevo en v1.2.0

    if not awards_str or awards_str == "N/A":
        return {
            "raw": None,
            "oscars": 0,
            "emmys": 0,
            "baftas": 0,
            "golden_globes": 0,
            "palme_dor": False,
            "oscars_nominated": 0,
            "total_wins": 0,
            "total_nominations": 0,
            "plot": plot_str,
        }

    text_lower = awards_str.lower()

    oscars = 0
    emmys = 0
    baftas = 0
    golden_globes = 0
    palme_dor = False
    oscars_nominated = 0
    total_wins = 0
    total_nominations = 0

    m_osc = re.search(r"won\s+(\d+)\s+oscars?", text_lower)
    if not m_osc:
        m_osc = re.search(r"won\s+(\d+)\s+oscar\b", text_lower)
    if m_osc:
        oscars = int(m_osc.group(1))

    m_osc_nom = re.search(r"nominated\s+for\s+(\d+)\s+oscars?", text_lower)
    if not m_osc_nom:
        m_osc_nom = re.search(r"nominated\s+for\s+(\d+)\s+oscar\b", text_lower)
    if m_osc_nom:
        oscars_nominated = int(m_osc_nom.group(1))

    for pat in [
        r"won\s+(\d+)\s+primetime\s+emmys?",
        r"won\s+(\d+)\s+emmys?",
        r"won\s+(\d+)\s+emmy\b",
    ]:
        m = re.search(pat, text_lower)
        if m:
            emmys = int(m.group(1))
            break

    m_bafta = re.search(r"won\s+(\d+)[^\.]*bafta", text_lower)
    if m_bafta:
        baftas = int(m_bafta)
    elif "bafta" in text_lower:
        baftas = 1

    m_globe = re.search(r"won\s+(\d+)[^\.]*golden\s+globes?", text_lower)
    if not m_globe:
        m_globe = re.search(r"won\s+(\d+)[^\.]*golden\s+globe\b", text_lower)
    if m_globe:
        golden_globes = int(m_globe.group(1))
    elif "golden globe" in text_lower:
        golden_globes = 1

    if re.search(r"palme\s+d['’]or", text_lower):
        palme_dor = True

    m_wins = re.search(r"(\d+)\s+wins?", text_lower)
    if m_wins:
        total_wins = int(m_wins.group(1))

    m_noms = re.search(r"(\d+)\s+nominations?", text_lower)
    if m_noms:
        total_nominations = int(m_noms.group(1))

    return {
        "raw": awards_str,
        "oscars": oscars,
        "emmys": emmys,
        "baftas": baftas,
        "golden_globes": golden_globes,
        "palme_dor": palme_dor,
        "oscars_nominated": oscars_nominated,
        "total_wins": total_wins,
        "total_nominations": total_nominations,
        "plot": plot_str,
    }

def compute_awards_table(df_basic):
    """Tabla de premios OMDb para un subconjunto de pelis (Title/Year)."""
    rows = []
    for _, r in df_basic.iterrows():
        title = r.get("Title")
        year = r.get("Year")
        awards = get_omdb_awards(title, year)
        if not isinstance(awards, dict) or "error" in awards:
            continue
        rows.append({
            "Title": title,
            "Year": year,
            "oscars": awards.get("oscars", 0),
            "oscars_nominated": awards.get("oscars_nominated", 0),
            "total_wins": awards.get("total_wins", 0),
            "total_nominations": awards.get("total_nominations", 0),
            "palme_dor": awards.get("palme_dor", False),
            "raw": awards.get("raw"),
        })
    if not rows:
        return pd.DataFrame(
            columns=[
                "Title", "Year", "oscars", "oscars_nominated",
                "total_wins", "total_nominations", "palme_dor", "raw"
            ]
        )
    return pd.DataFrame(rows)

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

def recommend_from_catalog(df_all, seed_row, top_n=5):
    """Recomendaciones simples dentro de tu catálogo a partir de una película semilla."""
    if df_all.empty:
        return pd.DataFrame()

    candidates = df_all.copy()
    if "Title" in candidates.columns and "Year" in candidates.columns:
        candidates = candidates[
            ~(
                (candidates["Title"] == seed_row.get("Title")) &
                (candidates["Year"] == seed_row.get("Year"))
            )
        ]

    seed_genres = set(seed_row.get("GenreList") or [])
    seed_dirs = {d.strip() for d in str(seed_row.get("Directors") or "").split(",") if d.strip()}
    seed_year = seed_row.get("Year")
    seed_rating = seed_row.get("Your Rating")

    scores = []
    for idx, r in candidates.iterrows():
        g2 = set(r.get("GenreList") or [])
        d2 = {d.strip() for d in str(r.get("Directors") or "").split(",") if d.strip()}
        score = 0.0

        # géneros compartidos
        score += 2.0 * len(seed_genres & g2)

        # directores compartidos
        if seed_dirs & d2:
            score += 3.0

        # cercanía en año
        y2 = r.get("Year")
        if pd.notna(seed_year) and pd.notna(y2):
            score -= min(abs(seed_year - y2) / 10.0, 3.0)

        # similitud de tu nota
        r2 = r.get("Your Rating")
        if pd.notna(seed_rating) and pd.notna(r2):
            score -= abs(seed_rating - r2) * 0.3

        # pequeño boost por IMDb alta
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

# ===================== FUNCIONES DE ÓSCAR (MOVIDAS ARRIBA) =====================

@st.cache_data
def _find_col(df, candidates):
    """Busca la primera columna cuyo nombre (lower) esté en candidates."""
    cand = {c.lower() for c in candidates}
    for col in df.columns:
        if str(col).strip().lower() in cand:
            return col
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

    col_year = _find_col(raw, {"year film", "film year", "year_film",
                               "year", "year_of_film"})
    col_cat = _find_col(raw, {"category", "award", "award category"})
    col_film = _find_col(raw, {"film", "film title", "movie", "movie title"})
    col_nominee = _find_col(raw, {"nominee", "name", "primary nominee"})
    col_winner = _find_col(raw, {"winner", "won", "iswinner", "is_winner"})

    if not all([col_year, col_cat, col_film, col_nominee, col_winner]):
        return pd.DataFrame()

    df = pd.DataFrame()
    df["YearFilm"] = pd.to_numeric(raw[col_year], errors="coerce").astype("Int64")
    df["Category"] = raw[col_cat].astype(str).str.strip()
    df["Film"] = raw[col_film].astype(str).str.strip()
    df["Nominee"] = raw[col_nominee].astype(str).str.strip()

    # Parse robusto de Winner -> bool
    w = raw[col_winner].astype(str).str.strip().str.lower()
    df["IsWinner"] = w.isin(
        ["true", "1", "yes", "winner", "won", "y", "si", "sí"]
    )

    # Normalización para cruce con catálogo
    df["NormFilm"] = df["Film"].apply(normalize_title)

    return df

def attach_catalog_to_oscar(osc_df, catalog_df):
    """
    Enlaza el dataset de Óscar con tu catálogo IMDb por título normalizado + año.
    """
    if osc_df is None or osc_df.empty:
        return pd.DataFrame()

    out = osc_df.copy()

    if catalog_df is None or catalog_df.empty:
        out["InMyCatalog"] = False
        out["MyRating"] = None
        out["MyIMDb"] = None
        out["CatalogURL"] = None
        return out

    cat = catalog_df.copy()
    if "NormTitle" not in cat.columns:
        cat["NormTitle"] = cat["Title"].apply(normalize_title)

    if "YearInt" not in cat.columns:
        if "Year" in cat.columns:
            cat["YearInt"] = pd.to_numeric(cat["Year"], errors="coerce").fillna(-1).astype(int)
        else:
            cat["YearInt"] = -1

    merged = out.merge(
        cat[["NormTitle", "YearInt", "Your Rating", "IMDb Rating", "URL"]],
        left_on=["NormFilm", "YearFilm"],
        right_on=["NormTitle", "YearInt"],
        how="left",
        suffixes=("", "_cat"),
    )

    merged["InMyCatalog"] = merged["URL"].notna()
    merged["MyRating"] = merged["Your Rating"]
    merged["MyIMDb"] = merged["IMDb Rating"]
    merged["CatalogURL"] = merged["URL"]

    merged = merged.drop(
        columns=["NormTitle", "YearInt", "Your Rating", "IMDb Rating", "URL"],
        errors="ignore",
    )
    return merged

def _build_people_chips(nominee_str: str) -> str:
    """
    Convierte el campo Nominee en chips HTML (personas / entidades).
    """
    if not isinstance(nominee_str, str) or not nominee_str.strip():
        return ""
    # Separador básico por ' and ', '&', ','
    parts = re.split(r",| & | and ", nominee_str)
    chips = []
    for p in parts:
        name = p.strip()
        if not name:
            continue
        chips.append(
            f"<span style='background:rgba(148,163,184,0.18);"
            f"border-radius:999px;padding:2px 9px;font-size:0.72rem;"
            f"text-transform:uppercase;letter-spacing:0.10em;"
            f"border:1px solid rgba(148,163,184,0.85);color:#e5e7eb;'>✦ {name}</span>"
        )
    if not chips:
        return ""
    return (
        "<div style='margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;'>"
        + "".join(chips)
        + "</div>"
    )

def _winner_badge_html():
    return (
        "<span style='background:rgba(34,197,94,0.20);"
        "border-radius:999px;padding:2px 8px;font-size:0.7rem;"
        "text-transform:uppercase;letter-spacing:0.12em;"
        "border:1px solid #22c55e;color:#bbf7d0;'>WINNER 🏆</span>"
    )

def _catalog_badge_html(my_rating):
    if pd.isna(my_rating):
        return ""
    return (
        "<span style='background:rgba(250,204,21,0.12);"
        "border-radius:999px;padding:3px 10px;font-size:0.72rem;"
        "text-transform:uppercase;letter-spacing:0.10em;"
        "border:1px solid rgba(250,204,21,0.85);color:#fef9c3;'>"
        f"En mi catálogo · Mi nota: {float(my_rating):.1f}</span>"
    )

def build_oscar_movie_card_html(row, categories_for_film=None, wins_for_film=None,
                            noms_for_film=None, highlight_winner=False):
    """
    Genera el HTML de una card de película para la sección Óscar.
    """
    title = row.get("Film", "Sin título")
    year = row.get("YearFilm", pd.NA)
    year_str = "" if pd.isna(year) else f" ({int(year)})"

    norm_film = row.get("NormFilm", "")
    my_rating = row.get("MyRating")
    my_imdb = row.get("MyIMDb")
    in_cat = bool(row.get("InMyCatalog", False))
    imdb_url = row.get("CatalogURL")

    is_winner_row = bool(row.get("IsWinner", False))
    is_winner = highlight_winner or is_winner_row

    # Poster / TMDb / streaming
    tmdb_info = get_tmdb_basic_info(title, year)
    poster_url = tmdb_info.get("poster_url") if tmdb_info else None
    tmdb_rating = tmdb_info.get("vote_average") if tmdb_info else None
    tmdb_id = tmdb_info.get("id") if tmdb_info else None
    providers = get_tmdb_providers(tmdb_id, country="CL") if tmdb_id else None

    # Colores del borde según winner
    if is_winner:
        border = "#22c55e"
        glow = "rgba(34,197,94,0.80)"
    else:
        border, glow = get_rating_colors(
            my_rating if pd.notna(my_rating) else my_imdb
        )

    # Poster HTML
    if poster_url:
        poster_html = (
            "<div class='movie-poster-frame'>"
            f"<img src='{poster_url}' alt='{title}' class='movie-poster-img' />"
            "</div>"
        )
    else:
        poster_html = """
<div class="movie-poster-frame">
  <div class="movie-poster-placeholder">
    <div class="film-reel-icon">🎞️</div>
    <div class="film-reel-text">Sin póster</div>
  </div>
</div>
"""

    # Reseñas y streaming
    reseñas_url = get_spanish_review_link(title, year)
    reseñas_html = (
        f"<a href='{reseñas_url}' target='_blank'>Reseñas en español</a>"
        if reseñas_url
        else ""
    )

    if providers:
        plats = providers.get("platforms") or []
        plats_str = ", ".join(plats) if plats else "Sin datos específicos para Chile (CL)"
        watch_link = providers.get("link")
        streaming_html = (
            f"Streaming (CL): {plats_str}"
            + (
                f"<br><a href='{watch_link}' target='_blank'>Ver streaming en TMDb (CL)</a>"
                if watch_link
                else ""
            )
        )
    else:
        streaming_html = "Streaming (CL): Sin datos para Chile (CL)"

    imdb_line = (
        f"IMDb: {float(my_imdb):.1f}"
        if pd.notna(my_imdb)
        else ("IMDb: N/D")
    )
    tmdb_line = (
        f"TMDb: {float(tmdb_rating):.1f}"
        if tmdb_rating is not None
        else "TMDb: N/D"
    )

    winner_badge = _winner_badge_html() if is_winner else ""
    catalog_badge = _catalog_badge_html(my_rating) if in_cat else ""

    badges_block = ""
    if winner_badge or catalog_badge:
        badges_block = (
            "<div style='margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;'>"
            f"{winner_badge}{catalog_badge}"
            "</div>"
        )

    # Categorías del film (sólo para vista ganadoras)
    cat_block = ""
    if categories_for_film:
        cats_txt = " · ".join(sorted(categories_for_film))
        cat_block = (
            "<br><span style='font-size:0.78rem;color:#9ca3af;'>Categoría(s):</span>"
            f"<br><span style='font-size:0.82rem;font-weight:500;'>{cats_txt}</span>"
        )

    # Chips con personas / entidades
    chips_html = _build_people_chips(row.get("Nominee", ""))

    # Resumen de premios / nominaciones del film (si se pasa)
    summary_counts = ""
    if wins_for_film is not None and noms_for_film is not None:
        summary_counts = (
            "<div style='margin-top:7px;display:flex;flex-wrap:wrap;gap:6px;'>"
            f"<span style='background:rgba(34,197,94,0.16);border-radius:999px;"
            f"padding:3px 10px;font-size:0.72rem;text-transform:uppercase;"
            f"letter-spacing:0.10em;border:1px solid rgba(34,197,94,0.75);"
            f"color:#bbf7d0;'>🏆 {wins_for_film} premio(s)</span>"
            f"<span style='background:rgba(148,163,184,0.16);border-radius:999px;"
            f"padding:3px 10px;font-size:0.72rem;text-transform:uppercase;"
            f"letter-spacing:0.10em;border:1px solid rgba(148,163,184,0.85);"
            f"color:#e5e7eb;'>🎯 {noms_for_film} nominación(es)</span>"
            "</div>"
        )

    card_html = f"""
<div class="movie-card movie-card-grid" style="
    border-color:{border};
    box-shadow:
        0 0 0 1px rgba(15,23,42,0.9),
        0 0 26px {glow};
">
  {poster_html}
  <div class="movie-title">{title}{year_str}</div>
  <div class="movie-sub">
    {imdb_line}<br>
    {tmdb_line}<br>
    {reseñas_html}<br>
    {streaming_html}
    {cat_block}
    {badges_block}
    {chips_html}
    {summary_counts}
    {f"<br><a href='{imdb_url}' target='_blank'>Ver en mi ficha de IMDb</a>" if isinstance(imdb_url,str) and imdb_url.startswith("http") else ""}
  </div>
</div>
"""
    return card_html

# ===================== LOGICA PRINCIPAL =====================

# ----------------- Carga de datos -----------------

st.sidebar.header("📂 Datos")

uploaded = st.sidebar.file_uploader(
    "Subo mi CSV de IMDb (si no, se usa peliculas.csv del repo)",
    type=["csv"]
)

if uploaded is not None:
    df = load_data(uploaded)
else:
    try:
        df = load_data("peliculas.csv")
    except FileNotFoundError:
        st.error(
            "No se encontró 'peliculas.csv' en el repositorio y no se subió archivo.\n\n"
            "Sube tu CSV de IMDb desde la barra lateral para continuar."
        )
        st.stop()

if "Title" not in df.columns:
    st.error("El CSV debe contener una columna 'Title' para poder funcionar.")
    st.stop()

df["NormTitle"] = df["Title"].apply(normalize_title)

if "Year" in df.columns:
    df["YearInt"] = pd.to_numeric(df["Year"], errors="coerce").fillna(-1).astype(int)
else:
    df["YearInt"] = -1

# ----------------- Tema oscuro + CSS (Mantenido v1.1.7) -----------------

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

    .main .block-container {{
        max-width: 1200px;
        padding-top: 3.0rem;
        padding-bottom: 3rem;
    }}

    @media (min-width: 1500px) {{
        .main .block-container {{
            max-width: 1400px;
        }}
    }}

    @media (max-width: 900px) {{
        .main .block-container {{
            max-width: 100%;
            padding-left: 0.75rem;
            padding-right: 0.75rem;
        }}
    }}

    [data-testid="stSidebar"] > div:first-child {{
        background: linear-gradient(180deg, rgba(15,23,42,0.98), rgba(15,23,42,0.90));
        border-right: 1px solid rgba(148,163,184,0.25);
        box-shadow: 0 0 30px rgba(0,0,0,0.7);
    }}

    [data-testid="stSidebar"] * {{
        color: #e5e7eb !important;
        font-size: 0.9rem;
    }}

    h1, h2, h3, h4 {{
        font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
        letter-spacing: 0.04em;
    }}

    h1 {{
        text-transform: uppercase;
        font-weight: 800;
        font-size: 2.0rem !important;
        background: linear-gradient(90deg, var(--accent), var(--accent-alt));
        -webkit-background-clip: text;
        color: transparent;
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
        line-height: 1.25;
        text-align: left;
    }}

    h2 {{
        font-weight: 700;
        font-size: 1.4rem !important;
        margin-top: 1.5rem;
        margin-bottom: 0.25rem;
    }}

    .stMarkdown, .stText, .stCaption, p {{
        color: var(--text-color);
    }}

    a {{
        color: var(--accent-alt) !important;
        text-decoration: none;
    }}
    a:hover {{
        text-decoration: underline;
    }}

    [data-testid="stMetric"] {{
        background: radial-gradient(circle at top left, rgba(15,23,42,0.95), rgba(15,23,42,0.75));
        padding: 14px 16px;
        border-radius: 14px;
        border: 1px solid rgba(148,163,184,0.45);
        box-shadow: 0 12px 30px rgba(15,23,42,0.7);
        backdrop-filter: blur(10px);
    }}

    [data-testid="stMetricLabel"], [data-testid="stMetricDelta"] {{
        color: #9ca3af !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.12em;
    }}

    [data-testid="stMetricValue"] {{
        color: #e5e7eb !important;
        font-weight: 700;
        font-size: 1.4rem !important;
    }}

    [data-testid="stExpander"] {{
        border-radius: var(--radius-xl) !important;
        border: 1px solid rgba(148,163,184,0.5);
        background: radial-gradient(circle at top left, rgba(15,23,42,0.98), rgba(15,23,42,0.85));
        margin-bottom: 1rem;
        box-shadow: 0 12px 30px rgba(15,23,42,0.7);
    }}

    button[kind="secondary"], button[kind="primary"], .stButton > button {{
        border-radius: 999px !important;
        border: 1px solid rgba(250, 204, 21, 0.7) !important;
        background: radial-gradient(circle at top left, rgba(234,179,8,0.25), rgba(15,23,42,1)) !important;
        color: #fefce8 !important;
        font-weight: 600 !important;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 0.75rem !important;
        padding: 0.45rem 1.2rem !important;
        box-shadow: 0 10px 25px rgba(234,179,8,0.35);
        transition: all 0.18s ease-out;
    }}

    button[kind="secondary"]:hover, button[kind="primary"]:hover, .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow:
            0 0 0 1px rgba(250,204,21,0.7),
            0 0 26px rgba(250,204,21,0.75);
    }}

    .movie-card {{
        background: radial-gradient(circle at top left, rgba(15,23,42,0.9), rgba(15,23,42,0.85));
        border-radius: var(--radius-lg);
        padding: 14px 14px 12px 14px;
        margin-bottom: 14px;
        border: 1px solid rgba(148,163,184,0.45);
        box-shadow: 0 18px 40px rgba(15,23,42,0.8);
        backdrop-filter: blur(12px);
        position: relative;
        overflow: hidden;
        transition: all 0.16s ease-out;
    }}

    .movie-card-grid {{
        height: 100%;
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }}

    .movie-card-grid:hover {{
        transform: translateY(-4px) scale(1.01);
        box-shadow:
            0 0 0 1px rgba(250,204,21,0.7),
            0 0 32px rgba(250,204,21,0.85);
        border-color: #facc15 !important;
    }}

    .movie-title {{
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        font-size: 0.86rem;
        margin-bottom: 2px;
        color: #f9fafb;
    }}

    .movie-sub {{
        font-size: 0.78rem;
        line-height: 1.35;
        color: #cbd5f5;
    }}

    .movie-gallery-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 18px;
        margin-top: 0.7rem;
    }}

    @media (max-width: 900px) {{
        .movie-gallery-grid {{
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 14px;
        }}
    }}

    .movie-poster-frame {{
        width: 100%;
        aspect-ratio: 2 / 3;
        border-radius: 14px;
        overflow: hidden;
        background: radial-gradient(circle at top, #020617 0%, #000000 55%, #020617 100%);
        border: 1px solid rgba(148,163,184,0.5);
        position: relative;
        box-shadow: 0 14px 30px rgba(0,0,0,0.85);
    }}

    .movie-poster-img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
        transform-origin: center;
        transition: transform 0.25s ease-out;
    }}

    .movie-card-grid:hover .movie-poster-img {{
        transform: scale(1.03);
    }}

    .movie-poster-placeholder {{
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background:
            radial-gradient(circle at 15% 0%, rgba(250,204,21,0.12), rgba(15,23,42,1)),
            radial-gradient(circle at 85% 100%, rgba(56,189,248,0.16), rgba(0,0,0,1));
        position: relative;
    }}

    .film-reel-icon {{
        font-size: 2.2rem;
        filter: drop-shadow(0 0 12px rgba(250,204,21,0.85));
        margin-bottom: 0.25rem;
    }}

    .film-reel-text {{
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: #e5e7eb;
        opacity: 0.95;
    }}

    [data-testid="stDataFrame"] {{
        border-radius: var(--radius-xl) !important;
        border: 1px solid rgba(148,163,184,0.6);
        background: radial-gradient(circle at top left, rgba(15,23,42,0.96), rgba(15,23,42,0.88));
        box-shadow:
            0 0 0 1px rgba(15,23,42,0.9),
            0 22px 45px rgba(15,23,42,0.95);
        overflow: hidden;
    }}

    [data-testid="stDataFrame"] * {{
        color: #e5e7eb !important;
        font-size: 0.82rem;
    }}

    [data-testid="stDataFrame"] thead tr {{
        background: linear-gradient(90deg, rgba(15,23,42,0.95), rgba(30,64,175,0.85));
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}

    [data-testid="stDataFrame"] tbody tr:hover {{
        background-color: rgba(234,179,8,0.12) !important;
        transition: background-color 0.15s ease-out;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Opciones visuales FIJAS
show_posters_fav = True
use_tmdb_gallery = True
show_trailers = True

# 2. Sidebar Filtros
st.sidebar.header("🎛️ Filtros")
year_range = st.sidebar.slider("Años", int(df["Year"].min()), int(df["Year"].max()), (int(df["Year"].min()), int(df["Year"].max()))) if df["Year"].notna().any() else (0, 9999)
rating_range = st.sidebar.slider("Mi nota", 0, 10, (0, 10)) if "Your Rating" in df.columns else (0, 10)

all_genres = sorted(set(g for sub in df["GenreList"].dropna() for g in sub if g))
selected_genres = st.sidebar.multiselect("Géneros", options=all_genres)

all_directors = sorted(set(d.strip() for d in df["Directors"].dropna() if str(d).strip()))
selected_directors = st.sidebar.multiselect("Directores", options=all_directors)

order_by = st.sidebar.selectbox("Ordenar por", ["Your Rating", "IMDb Rating", "Year", "Title", "Aleatorio"])
order_asc = st.sidebar.checkbox("Orden ascendente", value=False)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Opciones avanzadas")
show_awards = st.sidebar.checkbox("Consultar premios en OMDb (más lento, usa cuota de API)", value=False)
if show_awards:
    st.sidebar.caption("⚠ Consultar premios para muchas películas puede hacer la app más lenta en la primera carga.")

st.sidebar.markdown("---")
st.sidebar.header("🧾 Versiones")
with st.sidebar.expander("Ver changelog", expanded=False):
    for v, n in CHANGELOG.items():
        st.markdown(f"**v{v}**")
        for i in n: st.markdown(f"- {i}")

# 3. Filtrado
filtered = df.copy()
if "Year" in filtered.columns:
    filtered = filtered[(filtered["Year"] >= year_range[0]) & (filtered["Year"] <= year_range[1])]
if "Your Rating" in filtered.columns:
    filtered = filtered[(filtered["Your Rating"] >= rating_range[0]) & (filtered["Your Rating"] <= rating_range[1])]
if selected_genres:
    filtered = filtered[filtered["GenreList"].apply(lambda gl: all(g in gl for g in selected_genres))]
if selected_directors:
    filtered = filtered[filtered["Directors"].apply(lambda d: any(x in str(d) for x in selected_directors))]

# 4. Buscador
st.markdown("## 🔎 Búsqueda Global")
search_query = st.text_input("Busca por título, director o género (acepta errores leves)", placeholder="Ej: Oppenhimer...", key="main_search")

def apply_search(df_in, query):
    if not query: return df_in
    q = query.strip().lower()
    if "SearchText" not in df_in.columns: return df_in
    mask_exact = df_in["SearchText"].str.contains(q, na=False, regex=False)
    if len(q) < 3: return df_in[mask_exact]
    scored = df_in.copy()
    scored["score"] = scored["SearchText"].apply(lambda t: fuzz.partial_token_set_ratio(q, str(t)))
    return scored[mask_exact | (scored["score"] >= 75)].sort_values("score", ascending=False)

filtered_view = apply_search(filtered.copy(), search_query)

if order_by == "Aleatorio" and not filtered_view.empty:
    filtered_view = filtered_view.sample(frac=1)
elif order_by in filtered_view.columns:
    filtered_view = filtered_view.sort_values(order_by, ascending=order_asc)

# 5. TABS
tabs = st.tabs(["🎬 Catálogo", "🔍 Ficha Detallada", "🎬 Directores", "📊 Análisis", "🏆 Lista AFI", "🏆 Premios Óscar", "🎲 ¿Qué ver?"])

# --- TAB 1: CATALOGO ---
with tabs[0]:
    st.markdown("## 📈 Resumen de resultados")
    col1, col2, col3 = st.columns(3)
    col1.metric("Películas", len(filtered_view))
    if "Your Rating" in filtered_view.columns and not filtered_view.empty:
        col2.metric("Promedio Nota", f"{filtered_view['Your Rating'].mean():.2f}")
    if "IMDb Rating" in filtered_view.columns and not filtered_view.empty:
        col3.metric("Promedio IMDb", f"{filtered_view['IMDb Rating'].mean():.2f}")
    
    st.markdown("### 📚 Tabla de resultados")
    st.dataframe(filtered_view[["Title", "Year", "Your Rating", "IMDb Rating", "Genres", "Directors"]], use_container_width=True, hide_index=True)
    
    csv_filtrado = filtered_view.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar resultados (CSV)", csv_filtrado, "mis_peliculas.csv", "text/csv")

    st.markdown("---")
    st.markdown("## 🧱 Galería visual (pósters en grid por páginas)")
    
    page_size = 24
    if "gal_page" not in st.session_state: st.session_state.gal_page = 1
    total_pages = max(1, math.ceil(len(filtered_view)/page_size))
    
    c1, c2, c3 = st.columns([1,3,1])
    if c1.button("◀ Anterior", disabled=st.session_state.gal_page<=1, key="gp1"): st.session_state.gal_page -= 1
    if c3.button("Siguiente ▶", disabled=st.session_state.gal_page>=total_pages, key="gn1"): st.session_state.gal_page += 1
    c2.write(f"Página {st.session_state.gal_page} de {total_pages}")
    
    start = (st.session_state.gal_page - 1) * page_size
    page_df = filtered_view.iloc[start:start+page_size]
    
    html_cards = ['<div class="movie-gallery-grid">']
    for _, row in page_df.iterrows():
        tmdb = get_tmdb_basic_info(row["Title"], row["Year"])
        poster = tmdb.get("poster_url") if tmdb else None
        
        # Color rating
        try: r = float(row.get("Your Rating", 0))
        except: r = 0
        border = "#22c55e" if r >= 9 else "#0ea5e9" if r >= 8 else "#f97316"
        
        card = f"""
        <div class="movie-card movie-card-grid" style="border-color: {border};">
            <div class="movie-poster-frame">
                {f'<img src="{poster}" class="movie-poster-img">' if poster else '<div class="movie-poster-placeholder"><div class="film-reel-icon">🎞️</div></div>'}
            </div>
            <div class="movie-title">{row['Title']}</div>
            <div class="movie-sub">
                {int(row['Year']) if pd.notna(row['Year']) else ''}<br>
                ⭐ {row.get('Your Rating', '-')}/10
            </div>
        </div>
        """
        html_cards.append(card)
    html_cards.append("</div>")
    st.markdown("".join(html_cards), unsafe_allow_html=True)

# --- TAB 2: FICHA DETALLADA (NUEVO v1.2.0) ---
with tabs[1]:
    st.markdown("## 🔍 Ficha Detallada de Película")
    
    if filtered_view.empty:
        st.info("Sin películas para mostrar.")
    else:
        # Generar lista única para el selectbox
        # filtered_view = filtered_view.reset_index(drop=True)
        movie_options = []
        for idx, row in filtered_view.iterrows():
             movie_options.append((f"{row['Title']} ({int(row['Year']) if pd.notna(row['Year']) else '?'})", idx))
        
        sel_tuple = st.selectbox("Selecciona película:", movie_options, format_func=lambda x: x[0])
        
        if sel_tuple is not None:
            sel_idx = sel_tuple[1]
            movie = df.loc[sel_idx] # Usamos df original con el indice
            
            # Fetch data
            tmdb_data = get_tmdb_basic_info(movie["Title"], movie["Year"])
            tmdb_id = tmdb_data.get("id") if tmdb_data else None
            providers = get_tmdb_providers(tmdb_id) if tmdb_id else None
            omdb_data = get_omdb_awards(movie["Title"], movie["Year"])
            trailer = get_youtube_trailer_url(movie["Title"], movie["Year"])
            
            c_poster, c_info = st.columns([1.2, 2])
            
            with c_poster:
                if tmdb_data and tmdb_data.get("poster_url"):
                    st.image(tmdb_data["poster_url"], use_column_width=True)
                else:
                    st.info("Sin póster")
                if trailer: st.video(trailer)
            
            with c_info:
                st.markdown(f"<h1 style='margin-top:0;'>{movie['Title']} <span style='font-weight:300; font-size:1.5rem; color:#94a3b8;'>({fmt_year(movie['Year'])})</span></h1>", unsafe_allow_html=True)
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Mi Nota", movie.get("Your Rating", "-"))
                m2.metric("IMDb", movie.get("IMDb Rating", "-"))
                m3.metric("TMDb", tmdb_data.get("vote_average") if tmdb_data else "-")
                
                st.markdown("---")
                
                # Sinopsis
                overview = ""
                if tmdb_data and tmdb_data.get("overview"):
                    overview = tmdb_data.get("overview")
                elif omdb_data and not "error" in omdb_data and omdb_data.get("plot"):
                    overview = omdb_data.get("plot")
                
                if overview:
                    st.markdown(f"**📝 Sinopsis:**\n\n{overview}")
                
                st.markdown(f"**🎭 Géneros:** {movie.get('Genres')}")
                st.markdown(f"**🎬 Dirección:** {movie.get('Directors', 'Desconocido')}")
                
                # Premios
                if omdb_data and "error" not in omdb_data:
                    st.markdown("### 🏆 Premios y Nominaciones")
                    if omdb_data.get("palme_dor"):
                        st.success("🌿 Ganadora de la Palma de Oro (Cannes)")
                    
                    osc = omdb_data.get("oscars", 0)
                    if osc > 0:
                        st.markdown(f"**Oscars Ganados:** {osc}")
                    
                    wins = omdb_data.get("total_wins", 0)
                    if wins > 0:
                        st.markdown(f"**Total Premios Ganados:** {wins}")
                    
                    raw_txt = omdb_data.get("raw")
                    if raw_txt and raw_txt != "N/A":
                        st.caption(f"Detalle completo: {raw_txt}")
                
                if providers and providers['platforms']:
                    st.markdown("### 📺 Streaming (CL)")
                    st.write(", ".join(providers['platforms']))
            
            # Recomendaciones similares
            st.markdown("---")
            st.markdown("### 🔄 Películas similares (según catálogo)")
            recs = recommend_from_catalog(df, movie, top_n=4)
            if not recs.empty:
                cols = st.columns(4)
                for idx_col, (_, r_rec) in enumerate(recs.iterrows()):
                    with cols[idx_col]:
                        t_rec = r_rec["Title"]
                        y_rec = r_rec["Year"]
                        tmdb_rec = get_tmdb_basic_info(t_rec, y_rec)
                        if tmdb_rec and tmdb_rec.get("poster_url"):
                            st.image(tmdb_rec["poster_url"], use_column_width=True)
                        st.caption(f"**{t_rec}** ({fmt_year(y_rec)})\n⭐ {fmt_rating(r_rec.get('Your Rating'))}")

# --- TAB 3: DIRECTORES (NUEVO v1.2.0) ---
with tabs[2]:
    st.markdown("## 🎬 Estadísticas de Directores")
    st.caption("Analiza qué directores ves más y cómo los calificas.")

    if "Directors" in df.columns:
        dirs_exploded = filtered.assign(Director=filtered['Directors'].str.split(', ')).explode('Director')
        
        # Limpieza
        dirs_exploded['Director'] = dirs_exploded['Director'].str.strip()
        dirs_exploded = dirs_exploded[dirs_exploded['Director'].astype(bool)]
        
        dir_stats = dirs_exploded.groupby("Director").agg(
            Peliculas=('Title', 'count'),
            Nota_Media=('Your Rating', 'mean'),
            IMDb_Media=('IMDb Rating', 'mean')
        ).reset_index()
        
        min_movs = st.slider("Mínimo de películas vistas", 1, 10, 2)
        dir_stats_filtered = dir_stats[dir_stats["Peliculas"] >= min_movs].sort_values("Nota_Media", ascending=False)
        
        if dir_stats_filtered.empty:
            st.warning("No hay directores que cumplan con ese mínimo.")
        else:
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"### 🌟 Top Directores (Min. {min_movs} pelis)")
                chart = alt.Chart(dir_stats_filtered.head(15)).mark_bar().encode(
                    x=alt.X('Nota_Media', title='Mi Nota Promedio', scale=alt.Scale(domain=[0, 10])),
                    y=alt.Y('Director', sort='-x'),
                    color=alt.Color('Peliculas', scale=alt.Scale(scheme='goldorange')),
                    tooltip=['Director', 'Peliculas', 'Nota_Media']
                )
                st.altair_chart(chart, use_container_width=True)
            with c2:
                st.markdown("### 📋 Datos")
                st.dataframe(dir_stats_filtered.style.format({"Nota_Media": "{:.2f}", "IMDb_Media": "{:.2f}"}), hide_index=True)

# --- TAB 4: ANALISIS ---
with tabs[3]:
    st.markdown("## 📊 Análisis y tendencias")
    if not filtered.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Películas por año**")
            yr_counts = filtered[filtered["Year"].notna()]['Year'].value_counts().sort_index().reset_index()
            yr_counts.columns = ['Year', 'Count']
            yr_counts["Year"] = yr_counts["Year"].astype(int).astype(str)
            st.line_chart(yr_counts.set_index('Year'))
        
        with col_b:
            st.markdown("**Distribución de mis notas**")
            if "Your Rating" in filtered.columns:
                rt_counts = filtered['Your Rating'].value_counts().sort_index()
                st.bar_chart(rt_counts)
        
        if "Your Rating" in filtered.columns and "IMDb Rating" in filtered.columns:
            st.markdown("### 🔬 Mi nota vs IMDb")
            chart = alt.Chart(filtered).mark_circle(size=60).encode(
                x=alt.X('IMDb Rating', scale=alt.Scale(domain=[0, 10])),
                y=alt.Y('Your Rating', scale=alt.Scale(domain=[0, 10])),
                tooltip=['Title', 'Year', 'IMDb Rating', 'Your Rating']
            ).interactive().properties(height=350)
            st.altair_chart(chart, use_container_width=True)

# --- TAB 5: AFI ---
with tabs[4]:
    st.markdown("## 🎬 AFI's 100 Years...100 Movies")
    st.caption("Progreso en la lista de 10th Anniversary Edition")
    
    afi_frame = pd.DataFrame(AFI_LIST)
    afi_frame['NormTitle'] = afi_frame['Title'].apply(normalize_title)
    
    # Check si está en mi catálogo completo (df, no filtered)
    my_titles = set(df['NormTitle'])
    
    def check_seen(row):
        # Lógica simplificada de coincidencia
        if row['NormTitle'] in my_titles:
            return True
        return False

    afi_frame['Visto'] = afi_frame.apply(check_seen, axis=1)
    
    vistos = afi_frame['Visto'].sum()
    st.progress(vistos/100)
    st.metric("Películas vistas", f"{vistos}/100")
    
    afi_frame["Visto_Icon"] = afi_frame["Visto"].map({True: "✅", False: "—"})
    st.dataframe(afi_frame[['Rank', 'Title', 'Year', 'Visto_Icon']], hide_index=True, use_container_width=True)

# --- TAB 6: OSCAR ---
with tabs[5]:
    st.markdown("## 🏆 Premios de la Academia (Excel)")
    osc_raw = load_oscar_data_from_excel("Oscar_Data_1927_today.xlsx")
    if osc_raw.empty:
        st.warning("No se pudo cargar el archivo 'Oscar_Data_1927_today.xlsx'.")
    else:
        osc = attach_catalog_to_oscar(osc_raw, df)
        
        years = sorted(osc["FilmYear"].dropna().unique(), reverse=True)
        if not years:
            st.error("No hay años válidos en el archivo Excel.")
        else:
            col_filt_1, col_filt_2 = st.columns([2, 1])
            with col_filt_1:
                sel_y = st.slider("Año Ceremonia", min_value=int(min(years)), max_value=int(max(years)), value=int(max(years)))
            with col_filt_2:
                show_winners = st.checkbox("Solo Ganadores", value=False)
            
            ff = osc[osc["FilmYear"] == sel_y]
            
            if show_winners:
                st.markdown("#### 🥇 Películas ganadoras")
                grouped = ff[ff["IsWinner"]].groupby("Film")
                html_osc = ['<div class="movie-gallery-grid">']
                for film, group in grouped:
                    r = group.iloc[0]
                    cats = group["Category"].unique().tolist()
                    cat_text = " · ".join(cats)
                    t_info = get_tmdb_basic_info(r["Film"], r["FilmYear"])
                    
                    card = build_oscar_movie_card_html(
                        r, cat_text, group["PersonName"].tolist(), True,
                        r["InMyCatalog"], r["MyRating"], r["MyIMDb"], r["CatalogURL"], t_info
                    )
                    html_osc.append(card)
                html_osc.append('</div>')
                st.markdown("".join(html_osc), unsafe_allow_html=True)
            else:
                cats = sorted(ff["Category"].unique())
                for cat in cats:
                    st.markdown(f"**🎞️ {cat}**")
                    cat_rows = ff[ff["Category"] == cat]
                    grouped_cat = cat_rows.groupby("Film")
                    
                    html_osc = ['<div class="movie-gallery-grid">']
                    for film, group in grouped_cat:
                        r = group.iloc[0]
                        is_winner = group["IsWinner"].any()
                        t_info = get_tmdb_basic_info(r["Film"], r["FilmYear"])
                        
                        card = build_oscar_movie_card_html(
                            r, cat, group["PersonName"].tolist(), is_winner,
                            r["InMyCatalog"], r["MyRating"], r["MyIMDb"], r["CatalogURL"], t_info
                        )
                        html_osc.append(card)
                    html_osc.append('</div>')
                    st.markdown("".join(html_osc), unsafe_allow_html=True)

# --- TAB 7: QUE VER ---
with tabs[6]:
    st.markdown("## 🎲 ¿Qué ver hoy?")
    if st.button("¡Sorpréndeme!"):
        pool = df[df["Your Rating"].isna()]
        if pool.empty: pool = df
        
        if not pool.empty:
            pick = pool.sample(1).iloc[0]
            st.success(f"Te recomiendo: **{pick['Title']}** ({int(pick['Year'])})")
            
            c1, c2 = st.columns([1, 2])
            info = get_tmdb_basic_info(pick['Title'], pick['Year'])
            
            with c1:
                if info and info.get('poster_url'): st.image(info['poster_url'], use_column_width=True)
            with c2:
                if info and info.get('overview'): st.write(info['overview'])
                genres = pick.get("Genres")
                if genres: st.caption(f"Géneros: {genres}")
        else:
            st.warning("El catálogo está vacío.")

st.markdown("---")
st.caption(f"Versión de la app: v{APP_VERSION} · Powered by Diego Leal")
