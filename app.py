import html  # para escapar texto en los chips de personas
import streamlit as st
import pandas as pd
import requests
import random
import altair as alt
import re
import math
from urllib.parse import quote_plus
from collections import defaultdict

# ===================== Versión y changelog =====================
APP_VERSION = "1.1.7"  # Versión final con el CSS incrustado y correcciones

CHANGELOG = {
    "1.1.7": [
        "**Estructura:** Código unificado en un solo archivo `app.py`. CSS incrustado (eliminando la dependencia de `style.css`).",
        "**Optimización:** Búsqueda AFI reescrita a O(1) con mapa de catálogo (eliminando el cuello de botella).",
        "**Estructura:** Eliminación de funciones duplicadas para carga de datos y enlace de catálogo (mayor limpieza de código).",
        "OMDb: se corrige el parseo de premios BAFTA.",
        "Filtros: slider de 'Mi nota (Your Rating)' ahora admite decimales (paso 0.5).",
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
    "1.0.0": [
        "Catálogo, filtros, galería visual paginada, análisis, AFI y ¿Qué ver hoy?",
        "Integraciones opcionales: TMDb, YouTube y OMDb para premios por película.",
    ],
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
        df["YearInt"] = pd.to_numeric(year_str, errors="coerce").fillna(-1).astype(int)
        df["Year"] = df["YearInt"].apply(lambda x: x if x != -1 else None)
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
        # Usamos el índice para la fila completa
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
    # Uso de get() para manejar claves no existentes en st.secrets de forma segura
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

@st.cache_data
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

@st.cache_data
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
        pass

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
        baftas = int(m_bafta.group(1))
    elif "bafta" in text_lower and re.search(r"won\s+1\s+bafta", text_lower):
         baftas = 1 # caso de "Won 1 BAFTA Award."
    elif "bafta" in text_lower and baftas == 0:
        # A veces OMDb no pone el número y solo la palabra
        pass # Dejar en 0 si no se puede parsear número de forma segura

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

# ===================== ÓSCAR: carga y helpers (full_data.csv) =====================

@st.cache_data
def load_full_data(path_csv="full_data.csv"):
    """
    Carga robusta del dataset unificado (nominaciones + ganadores) de DLu/oscar_data.
    """
    # 1) Lectura tolerante al separador y a filas problemáticas
    try:
        dff = pd.read_csv(path_csv, sep=None, engine="python", on_bad_lines="skip")
    except Exception:
        dff = pd.read_csv(path_csv, sep="\t", on_bad_lines="skip")

    # 2) Normaliza encabezados
    dff.columns = [str(c).strip() for c in dff.columns]
    idx = dff.index

    def col_or_empty(name, default=""):
        """Devuelve la Serie si existe; si no, una Serie constante del mismo largo."""
        return dff[name] if name in dff.columns else pd.Series([default] * len(dff), index=idx)

    # Categoría canónica
    if "CanonicalCategory" in dff.columns:
        dff["CanonCat"] = dff["CanonicalCategory"].astype(str)
    else:
        dff["CanonCat"] = col_or_empty("Category").astype(str)

    # Años
    if "Year" in dff.columns:
        yr = pd.to_numeric(dff["Year"], errors="coerce")
        dff["YearInt"] = yr.fillna(-1).astype(int)
    else:
        dff["YearInt"] = -1

    # Ceremonia
    if "Ceremony" in dff.columns:
        dff["Ceremony"] = pd.to_numeric(dff["Ceremony"], errors="coerce").fillna(-1).astype(int)
    else:
        dff["Ceremony"] = -1

    # Ganador
    if "Winner" in dff.columns:
        dff["IsWinner"] = col_or_empty("Winner").astype(int).astype(bool)
    else:
        dff["IsWinner"] = False

    # IDs de nominados (personas/entidades)
    dff["NomineeIds"] = col_or_empty("NomineeIds").astype(str)
    dff["NomineeIdList"] = dff["NomineeIds"].apply(
        lambda s: [x.strip() for x in re.split(r"[;,]", s) if x.strip()]
    )

    # Aux para cruce con tu catálogo
    dff["NormFilm"] = col_or_empty("Film").apply(normalize_title)
    
    return dff

def attach_catalog_to_full(osc_df, my_catalog_df):
    """ Enlaza cada fila de full_data con tu catálogo (por título normalizado + año). Añade: InMyCatalog, MyRating, MyIMDb, CatalogURL """
    out = osc_df.copy()

    if my_catalog_df is None or my_catalog_df.empty:
        out["InMyCatalog"] = False
        out["MyRating"] = None
        out["MyIMDb"] = None
        out["CatalogURL"] = None
        return out

    cat = my_catalog_df.copy()
    
    # Mapeo de (NormTitle, YearInt) a (Your Rating, IMDb Rating, URL)
    cat_map = {}
    for idx, row in cat.iterrows():
        key = (row.get("NormTitle", ""), row.get("YearInt", -1))
        if key[0] and key[1] != -1:
            cat_map[key] = (
                row.get("Your Rating"), 
                row.get("IMDb Rating"), 
                row.get("URL"), 
                idx
            )

    def lookup_catalog(row):
        key = (row.get("NormFilm", ""), row.get("YearInt", -1))
        
        # Búsqueda estricta por NormFilm + Year
        match = cat_map.get(key)
        
        if match:
            my_rating, my_imdb, url, idx = match
            return True, my_rating, my_imdb, url
        
        # Si falla, intenta buscar por año +/- 1
        for year_offset in [-1, 1]:
            key_fuzzy = (row.get("NormFilm", ""), row.get("YearInt", -1) + year_offset)
            match_fuzzy = cat_map.get(key_fuzzy)
            if match_fuzzy:
                my_rating, my_imdb, url, idx = match_fuzzy
                return True, my_rating, my_imdb, url

        return False, None, None, None

    # Aplicar la función de búsqueda
    results = out.apply(lookup_catalog, axis=1, result_type='expand')
    results.columns = ["InMyCatalog", "MyRating", "MyIMDb", "CatalogURL"]
    
    # Unir resultados
    out = pd.concat([out, results], axis=1)

    return out


# ----------------- Funciones de formato y visualización -----------------

def fmt_rating(r):
    """Formatea la nota con colores."""
    if pd.isna(r) or r is None:
        return "—"
    
    r_float = float(r)
    color = get_rating_colors(r_float)[0]
    return f'<b style="color:{color};">{r_float:.1f}</b>'

def fmt_year(y):
    """Formatea el año."""
    if pd.isna(y) or y is None:
        return "N/A"
    try:
        return str(int(y))
    except Exception:
        return "N/A"

# ===================== Estilos (CSS) incrustados =====================
def apply_embedded_css():
    """Define y aplica los estilos CSS directamente en el script."""
    embedded_css = """
/*
  ESTILOS PRINCIPALES INCRUSTADOS
  Necesarios para las tarjetas de la galería y el modo oscuro
*/

.movie-card {
    border: 1px solid #475569;
    padding: 15px;
    margin-bottom: 15px;
    border-radius: 12px;
    background-color: #1e293b;
    color: #e5e7eb;
    transition: all 0.3s ease;
}

.movie-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

.movie-gallery-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
}

.movie-card-grid {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
    position: relative;
    /* Los bordes y sombras dinámicas se aplican inline, esto es el base */
    box-shadow: 0 0 0 1px rgba(15,23,42,0.9), 0 0 12px rgba(148,163,184,0.1); 
}

.movie-poster-frame {
    flex-shrink: 0;
    width: 100%;
    padding-bottom: 150%; /* Aspect ratio 2:3 */
    position: relative;
    overflow: hidden;
    border-radius: 8px;
}

.movie-poster-img {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

.movie-poster-placeholder {
    width: 100%;
    height: 100%;
    background-color: #334155;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: #94a3b8;
    font-size: 1rem;
}

.film-reel-icon {
    font-size: 3rem;
}

.film-reel-text {
    margin-top: 5px;
    font-size: 0.9rem;
}

.movie-title {
    margin-top: 10px;
    font-size: 1.15rem;
    font-weight: 700;
    color: #f8fafc;
    line-height: 1.3;
    flex-grow: 0;
}

.movie-sub {
    margin-top: 8px;
    font-size: 0.85rem;
    color: #94a3b8;
    line-height: 1.6;
    flex-grow: 1;
}

/* Estilos de Streamlit para mejorar el aspecto general (fondo, etc.) */
.stApp {
    background-color: #0f172a; 
    color: #e5e7eb;
}

/* Ocultar menú y footer de Streamlit */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* Estilo para los rating boxes en 'Qué ver hoy' */
.rating-box {
    padding: 10px 15px;
    border: 1px solid #475569;
    border-radius: 6px;
    background-color: #334155;
    font-weight: 600;
    color: #f8fafc;
}

/* Estilo para la tabla de análisis */
table {
    width: 100%;
    margin-top: 15px;
    border-collapse: collapse;
    font-size: 0.95rem;
}
th {
    background-color: #334155 !important; 
    color: #e5e7eb;
    text-align: left;
    padding: 10px 12px;
}
td {
    padding: 10px 12px;
    border-bottom: 1px solid #334155;
}
tr:nth-child(even) {
    background-color: #1e293b;
}
a {
    color: #38bdf8; 
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}
"""
    st.markdown(f'<style>{embedded_css}</style>', unsafe_allow_html=True)

# Aplica el CSS antes de cualquier otro elemento de Streamlit
apply_embedded_css()
# =========================================================


def _build_people_chips(nominee_str):
    """Convierte una cadena de nominados en chips HTML."""
    if not isinstance(nominee_str, str) or not nominee_str.strip():
        return ""
    # Separador básico por ' and ', '&', ','
    parts = re.split(r",| & | and ", nominee_str)
    chips = []
    for p in parts:
        name = p.strip()
        if not name:
            continue
        # Escapar el nombre para evitar inyección XSS si hay comillas en el nombre
        safe_name = html.escape(name) 
        chips.append(
            f"<span style='background:rgba(148,163,184,0.18);"
            f"border-radius:999px;padding:2px 9px;font-size:0.72rem;"
            f"text-transform:uppercase;letter-spacing:0.10em;"
            f"border:1px solid rgba(148,163,184,0.85);color:#e5e7eb;'>✦ {safe_name}</span>"
        )
    if not chips:
        return ""
    return (
        "<div style='margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;'>" + "".join(chips) + "</div>"
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

def _build_oscar_card_html(
    row,
    categories_for_film=None,
    is_winner_in_this_context=False,
    wins_for_film=None,
    noms_for_film=None
):
    """
    Construye el HTML para una tarjeta de película en la sección de Óscar.
    Se reutilizan estilos y lógica de la galería principal.
    """
    film_title = row.get("Film", "Sin título")
    film_year = row.get("YearInt")
    
    in_cat = row.get("InMyCatalog", False)
    my_rating = row.get("MyRating")
    my_imdb = row.get("MyIMDb")
    imdb_url = row.get("CatalogURL")
    
    # Intentar obtener info TMDb/Streaming
    # Nota: Se usa una función cacheada para evitar llamadas duplicadas en la misma sesión
    tmdb_info, providers_info = get_tmdb_and_providers_for_title(film_title, film_year)
    
    # --- TMDb info ---
    poster_url = None
    tmdb_rating = None
    if tmdb_info:
        poster_url = tmdb_info.get("poster_url")
        tmdb_rating = tmdb_info.get("vote_average")
    
    # --- Colores base según rating (mi nota > IMDb) ---
    base_rating = None
    if pd.notna(my_rating):
        base_rating = my_rating
    elif my_imdb is not None and not (isinstance(my_imdb, float) and math.isnan(my_imdb)):
        base_rating = my_imdb
    
    # Colores por defecto (gris)
    border_color, glow_color = get_rating_colors(base_rating)

    # Si es ganadora, borde verde nuclear
    if is_winner_in_this_context:
        border_color = "#22c55e"
        glow_color = "rgba(34,197,94,0.80)"

    year_str = f" ({fmt_year(film_year)})" if pd.notna(film_year) else ""

    # --- Links utilitarios ---
    reseñas_url = get_spanish_review_link(film_title, film_year)
    reseñas_html = (
        f'<a href="{reseñas_url}" target="_blank">Reseñas en español</a>'
        if reseñas_url else ""
    )
    imdb_link_html = (
        f'<a href="{imdb_url}" target="_blank">Ver en mi ficha de IMDb</a>'
        if isinstance(imdb_url, str) and imdb_url.startswith("http") else ""
    )
    
    # --- Streaming (CL desde TMDb) ---
    platforms_str = "Sin datos para Chile (CL)"
    streaming_link = None
    if providers_info:
        platforms = providers_info.get("platforms") or []
        platforms_str = ", ".join(platforms) if platforms else "Sin datos para Chile (CL)"
        streaming_link = providers_info.get("link")

    if streaming_link:
        streaming_html = (
            f"Streaming (CL): {platforms_str}<br>"
            f'<a href="{streaming_link}" target="_blank">Ver streaming en TMDb (CL)</a>'
        )
    else:
        streaming_html = f"Streaming (CL): {platforms_str}"

    # --- Ratings ---
    my_txt = f"Mi nota: {fmt_rating(my_rating)}" if pd.notna(my_rating) else "Mi nota: N/D"
    imdb_txt = f"IMDb: {fmt_rating(my_imdb)}" if pd.notna(my_imdb) else "IMDb: N/D"
    tmdb_txt = f"TMDb: {fmt_rating(tmdb_rating)}" if tmdb_rating is not None else "TMDb: N/D"
    
    ratings_lines = []
    if pd.notna(my_rating): ratings_lines.append(my_txt)
    ratings_lines.append(imdb_txt)
    ratings_lines.append(tmdb_txt)
    ratings_html = "<br>".join(ratings_lines)
    
    # --- Poster ---
    if isinstance(poster_url, str) and poster_url:
        poster_html = (
            "<div class='movie-poster-frame'>"
            f"<img src='{poster_url}' alt='{film_title}' class='movie-poster-img' />"
            "</div>"
        )
    else:
        poster_html = (
            "<div class='movie-poster-frame'>"
            "<div class='movie-poster-placeholder'>"
            "<div class='film-reel-icon'>🎞️</div>"
            "<div class='film-reel-text'>Sin póster</div>"
            "</div></div>"
        )
    
    # --- Bloque principal ---
    winner_badge = _winner_badge_html() if is_winner_in_this_context else ""
    catalog_badge = _catalog_badge_html(my_rating) if in_cat else ""
    
    badges_row = ""
    badges = [b for b in [winner_badge, catalog_badge] if b]
    if badges:
        badges_row = (
            "<div style='margin-top:8px;display:flex;flex-wrap:wrap;gap:8px;'>" + "".join(badges) + "</div>"
        )

    # Texto de categoría
    category_text = "N/A"
    people_html = ""
    if categories_for_film:
        category_text = " · ".join(sorted(categories_for_film))
    else:
        # Si no se pasó categorías, intentamos usar Nominee (para vista de nominados individuales)
        category_text = row.get("Category", "N/A")
        people_html = _build_people_chips(row.get("Nominee", ""))


    category_block = (
        "<span style='font-size:0.78rem;color:#9ca3af;'>Categoría(s):</span><br>"
        f"<span style='font-size:0.82rem;font-weight:500;'>{category_text}</span>"
    )

    # Detalle de premios/nominaciones (solo para vista de ganadores por film)
    summary_counts = ""
    if wins_for_film is not None and noms_for_film is not None:
        summary_counts = (
            "<div style='margin-top:7px;display:flex;flex-wrap:wrap;gap:6px;'>"
            f"<span style='background:rgba(34,197,94,0.16);border-radius:999px;"
            f"padding:3px 10px;font-size:0.72rem;text-transform:uppercase;"
            f"letter-spacing:0.10em;border:1px solid #22c55e;color:#bbf7d0;'>"
            f"🏆 {wins_for_film} premio(s)</span>"
            f"<span style='background:rgba(148,163,184,0.16);border-radius:999px;"
            f"padding:3px 10px;font-size:0.72rem;text-transform:uppercase;"
            f"letter-spacing:0.10em;border:1px solid rgba(148,163,184,0.85);color:#e5e7eb;'>"
            f"🎫 {noms_for_film} nominación(es)</span>"
            "</div>"
        )

    # Sección de links
    links_block_parts = []
    if reseñas_html: links_block_parts.append(reseñas_html)
    if imdb_link_html: links_block_parts.append(imdb_link_html)
    links_block = "<br>".join(links_block_parts)

    # Construcción final
    card_html = f"""
    <div class="movie-card movie-card-grid" style="
        border-color:{border_color}; 
        box-shadow:0 0 0 1px rgba(15,23,42,0.9), 0 0 26px {glow_color};
    ">
      {poster_html}
      <div class="movie-title">{film_title}{year_str}</div>
      <div class="movie-sub">
        {ratings_html}<br>
        {links_block}<br>
        {streaming_html}<br>
        
        {summary_counts} 
        <div style="margin-top:10px;">{category_block}</div>
        
        {badges_row}
        {people_html}
      </div>
    </div>
    """
    return card_html


# ===================== EJECUCIÓN PRINCIPAL =====================

# 1. Carga de datos
try:
    uploaded_file = st.sidebar.file_uploader(
        "Cargar archivo CSV (IMDb o Letterboxd)", type=["csv"]
    )
    if uploaded_file is None:
        # Intenta cargar un archivo de catálogo local si no se subió uno
        df, catalog_map = load_data("peliculas.csv")
        df_full = df.copy() # Copia del catálogo completo
    else:
        # Archivo subido
        df, catalog_map = load_data(uploaded_file)
        df_full = df.copy() # Copia del catálogo completo
except FileNotFoundError:
    st.error(
        "Error: Asegúrate de tener un archivo `peliculas.csv` o sube tu catálogo."
    )
    df = pd.DataFrame()
    df_full = pd.DataFrame()
    catalog_map = {}
except Exception as e:
    st.error(f"Error al cargar/procesar el CSV. Revisa el formato: {e}")
    df = pd.DataFrame()
    df_full = pd.DataFrame()
    catalog_map = {}

# 2. Carga de datos de ÓSCAR
osc_df = pd.DataFrame()
osc_available = False
if not df.empty:
    try:
        osc_df_raw = load_full_data("full_data.csv")
        if not osc_df_raw.empty:
            # Enlaza el catálogo del usuario al dataset de Oscar
            osc_df = attach_catalog_to_full(osc_df_raw, df_full)
            osc_available = True
        else:
            st.sidebar.warning(
                "Advertencia: El archivo `full_data.csv` está vacío o incompleto. Pestaña Óscar deshabilitada."
            )
    except FileNotFoundError:
        st.sidebar.warning(
            "Advertencia: No se encontró el archivo `full_data.csv` para la pestaña Óscar. La pestaña estará deshabilitada."
        )
    except Exception as e:
        st.sidebar.error(
            f"Error al cargar/procesar datos de Óscar (`full_data.csv`): {e}"
        )


if not df.empty:

    # ----------------- INICIO DE SIDEBAR Y FILTROS -----------------

    # Contenedor de filtros en la barra lateral
    st.sidebar.header("Filtros de Catálogo")
    st.sidebar.markdown(
        f"**Películas cargadas:** {len(df_full):,} | **Filtradas:** {len(df):,}"
    )

    # 1. Búsqueda de texto
    search_query = st.sidebar.text_input(
        "Buscar por título, director o género:", key="search_query"
    ).lower()

    # 2. Rango de años
    min_year_default = df_full["YearInt"].replace(-1, None).min() if not df_full.empty and "YearInt" in df_full.columns else 1900
    max_year_default = df_full["YearInt"].replace(-1, None).max() if not df_full.empty and "YearInt" in df_full.columns else 2025

    if min_year_default is not None and max_year_default is not None:
        # Asegurarse de que los valores sean enteros y que el rango sea válido
        min_y = int(min_year_default)
        max_y = int(max_year_default)
        if min_y > max_y:
             min_y, max_y = 1900, 2025 # Fallback seguro
             
        year_range = st.sidebar.slider(
            "Rango de años de estreno (Year):",
            min_value=min_y,
            max_value=max_y,
            value=(min_y, max_y),
            step=1,
            key="year_range",
        )
    else:
        year_range = (1900, 2025)
        st.sidebar.warning("Datos de año no disponibles o incompletos para usar el slider.")


    # 3. Géneros
    all_genres = sorted(
        list(
            set(
                g
                for genres in df_full["GenreList"]
                if isinstance(genres, list)
                for g in genres
            )
        )
    )
    selected_genres = st.sidebar.multiselect(
        "Filtrar por género(s):", all_genres, key="selected_genres"
    )

    # 4. Mi Nota (Your Rating)
    if "Your Rating" in df_full.columns and not df_full["Your Rating"].isna().all():
        min_rating = float(df_full["Your Rating"].min())
        max_rating = float(df_full["Your Rating"].max())
        rating_range = st.sidebar.slider(
            "Mi nota (Your Rating):",
            min_value=min_rating,
            max_value=max_rating,
            value=(min_rating, max_rating),
            step=0.5, 
            key="rating_range",
        )
    else:
        rating_range = (1.0, 10.0)
        st.sidebar.info("La columna 'Your Rating' no está disponible o está vacía.")

    # 5. Vistas
    selected_views = st.sidebar.radio(
        "Vistas:", ["Películas vistas", "Películas sin ver"], key="views_mode"
    )

    # 6. Sort
    sort_options = {
        "Mi Nota (Descending)": ("Your Rating", False),
        "IMDb Rating (Descending)": ("IMDb Rating", False),
        "Fecha en que califiqué (Latest)": ("Date Rated", False),
        "Año de estreno (Latest)": ("YearInt", False),
        "Título (A-Z)": ("Title", True),
    }
    sort_by_label = st.sidebar.selectbox(
        "Ordenar por:",
        list(sort_options.keys()),
        index=0,
        key="sort_order_label",
    )
    sort_col, sort_asc = sort_options[sort_by_label]


    # ----------------- APLICACIÓN DE FILTROS -----------------

    df_filtered = df_full.copy()

    # 1. Filtro de búsqueda de texto (Title, Original Title, Directors, Genres)
    if search_query:
        df_filtered = df_filtered[
            df_filtered["SearchText"].str.contains(search_query, case=False, na=False)
        ]

    # 2. Filtro de rango de años (YearInt)
    df_filtered = df_filtered[
        (df_filtered["YearInt"] >= year_range[0])
        & (df_filtered["YearInt"] <= year_range[1])
    ]

    # 3. Filtro de géneros (GenreList)
    if selected_genres:
        df_filtered = df_filtered[
            df_filtered["GenreList"].apply(
                lambda x: all(genre in x for genre in selected_genres)
            )
        ]

    # 4. Filtro de Mi Nota (Your Rating)
    if (
        "Your Rating" in df_filtered.columns
        and not df_filtered["Your Rating"].isna().all()
    ):
        df_filtered = df_filtered[
            (df_filtered["Your Rating"].fillna(0) >= rating_range[0])
            & (df_filtered["Your Rating"].fillna(0) <= rating_range[1])
        ]

    # 5. Filtro de Vistas
    if selected_views == "Películas vistas":
        df_filtered = df_filtered[
            df_filtered["Your Rating"].notna()
        ]  # Asume que si tiene nota, está vista
    elif selected_views == "Películas sin ver":
        df_filtered = df_filtered[
            df_filtered["Your Rating"].isna()
        ]  # Asume que si no tiene nota, no está vista

    # 6. Ordenamiento
    if sort_col in df_filtered.columns:
        df_filtered = df_filtered.sort_values(
            by=sort_col, ascending=sort_asc, na_position="last"
        )
    df = df_filtered.copy()

    # Mostrar filtros activos
    st.caption(f"Filtros activos: {len(df):,} películas.")
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**App Version:** `v{APP_VERSION}`")
    with st.sidebar.expander("Changelog"):
        st.markdown(
            "".join(
                f"**v{ver}** ({len(changes)} cambios):<ul>{''.join(f'<li>{c}</li>' for c in changes)}</ul>"
                for ver, changes in CHANGELOG.items()
            ),
            unsafe_allow_html=True,
        )


    # ----------------- INICIO DE PESTAÑAS -----------------

    tabs = ["1. Galería", "2. Análisis", "3. AFI 100", "4. ¿Qué ver hoy?"]
    if osc_available:
        tabs.insert(2, "🏆 Premios Óscar") # Pestaña en la posición 3

    # Desempaquetado dinámico de pestañas
    tab_objects = st.tabs(tabs)
    tab_map = {name: obj for name, obj in zip(tabs, tab_objects)}
    
    tab_gallery = tab_map["1. Galería"]
    tab_analysis = tab_map["2. Análisis"]
    
    # Obtener el resto de las pestañas
    tab_afi = tab_map["3. AFI 100"]
    tab_today = tab_map["4. ¿Qué ver hoy?"]
    tab_oscar = tab_map.get("🏆 Premios Óscar")


    # ----------------- TAB 1: GALERÍA VISUAL -----------------
    with tab_gallery:
        st.header("Catálogo Filtrado (Galería)")
        if df.empty:
            st.warning("No hay películas que coincidan con los filtros seleccionados.")
        else:
            # Paginación
            items_per_page = st.slider(
                "Películas por página:", 10, 100, 30, key="items_per_page_gallery"
            )
            total_items = len(df)
            total_pages = (total_items + items_per_page - 1) // items_per_page

            if "page_number" not in st.session_state:
                st.session_state.page_number = 1

            col_prev, col_info, col_next = st.columns([1, 2, 1])

            with col_prev:
                if st.button("<< Anterior", key="prev_page"):
                    st.session_state.page_number = max(
                        1, st.session_state.page_number - 1
                    )
            with col_next:
                if st.button("Siguiente >>", key="next_page"):
                    st.session_state.page_number = min(
                        total_pages, st.session_state.page_number + 1
                    )
            with col_info:
                st.markdown(
                    f"<div style='text-align:center; padding-top:10px;'>Página **{st.session_state.page_number}** de **{total_pages}**</div>",
                    unsafe_allow_html=True,
                )

            start_idx = (st.session_state.page_number - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, total_items)
            df_page = df.iloc[start_idx:end_idx].copy()

            # --- Generación de las tarjetas HTML (función optimizada) ---
            cards_html = []
            for _, row in df_page.iterrows():
                # Obtener info de APIs (cacheado)
                tmdb_info, providers_info = get_tmdb_and_providers_for_title(
                    row.get("Title"), row.get("Year")
                )

                # Info de Rating
                my_rating = row.get("Your Rating")
                imdb_rating = row.get("IMDb Rating")
                tmdb_rating = tmdb_info.get("vote_average") if tmdb_info else None

                # Colores
                base_rating = my_rating if pd.notna(my_rating) else imdb_rating
                border_color, glow_color = get_rating_colors(base_rating)

                # Poster
                poster_url = tmdb_info.get("poster_url") if tmdb_info else None
                if isinstance(poster_url, str) and poster_url:
                    poster_html = (
                        "<div class='movie-poster-frame'>"
                        f"<img src='{poster_url}' alt='{row.get('Title')}' class='movie-poster-img' />"
                        "</div>"
                    )
                else:
                    poster_html = (
                        "<div class='movie-poster-frame'>"
                        "<div class='movie-poster-placeholder'>"
                        "<div class='film-reel-icon'>🎞️</div>"
                        "<div class='film-reel-text'>Sin póster</div>"
                        "</div></div>"
                    )

                # Ratings
                my_txt = f"Mi nota: {fmt_rating(my_rating)}" if pd.notna(my_rating) else "Mi nota: N/D"
                imdb_txt = f"IMDb: {fmt_rating(imdb_rating)}" if pd.notna(imdb_rating) else "IMDb: N/D"
                tmdb_txt = f"TMDb: {fmt_rating(tmdb_rating)}" if tmdb_rating is not None else "TMDb: N/D"
                ratings_lines = []
                if pd.notna(my_rating): ratings_lines.append(my_txt)
                ratings_lines.append(imdb_txt)
                ratings_lines.append(tmdb_txt)
                ratings_html = "<br>".join(ratings_lines)

                # Links
                imdb_link_html = (
                    f'<a href="{row.get("URL")}" target="_blank">Ver en IMDb</a>'
                    if isinstance(row.get("URL"), str)
                    and row.get("URL").startswith("http")
                    else ""
                )
                
                # Streaming
                platforms_str = "Sin datos para Chile (CL)"
                streaming_link = None
                if providers_info:
                    platforms = providers_info.get("platforms") or []
                    platforms_str = ", ".join(platforms) if platforms else "Sin datos para Chile (CL)"
                    streaming_link = providers_info.get("link")

                if streaming_link:
                    streaming_html = (
                        f"Streaming (CL): {platforms_str}<br>"
                        f'<a href="{streaming_link}" target="_blank">Ver streaming en TMDb (CL)</a>'
                    )
                else:
                    streaming_html = f"Streaming (CL): {platforms_str}"


                # Tarjeta HTML
                card_html = f"""
                <div class="movie-card movie-card-grid" style="
                    border-color: {border_color};
                    box-shadow: 0 0 0 1px rgba(15,23,42,0.9), 0 0 22px {glow_color};
                ">
                  {poster_html}
                  <div class="movie-title">{row.get('Title')} ({fmt_year(row.get('Year'))})</div>
                  <div class="movie-sub">
                    {ratings_html}<br>
                    {imdb_link_html}<br>
                    {streaming_html}
                  </div>
                </div>
                """
                cards_html.append(card_html)

            gallery_html = (
                "<div class='movie-gallery-grid'>"
                + "\n".join(cards_html)
                + "</div>"
            )
            st.markdown(gallery_html, unsafe_allow_html=True)

            # Controles de paginación al final
            col_prev_b, col_info_b, col_next_b = st.columns([1, 2, 1])

            with col_prev_b:
                if st.button("<< Anterior", key="prev_page_b"):
                    st.session_state.page_number = max(
                        1, st.session_state.page_number - 1
                    )
            with col_next_b:
                if st.button("Siguiente >>", key="next_page_b"):
                    st.session_state.page_number = min(
                        total_pages, st.session_state.page_number + 1
                    )
            with col_info_b:
                st.markdown(
                    f"<div style='text-align:center; padding-top:10px;'>Página **{st.session_state.page_number}** de **{total_pages}**</div>",
                    unsafe_allow_html=True,
                )


    # ----------------- TAB 2: ANÁLISIS -----------------
    with tab_analysis:
        st.header("Análisis de tu Catálogo")

        if df.empty:
            st.warning("No hay datos para analizar.")
        else:
            # Resumen Numérico
            col1, col2, col3, col4 = st.columns(4)

            # Películas Vistas
            col1.metric("Películas vistas", len(df[df["Your Rating"].notna()]))

            # Nota promedio
            avg_rating = df["Your Rating"].mean()
            col2.metric(
                "Mi Nota Promedio", f"{avg_rating:.2f}" if pd.notna(avg_rating) else "N/A"
            )

            # IMDb Promedio
            avg_imdb = df["IMDb Rating"].mean()
            col3.metric(
                "IMDb Rating Promedio",
                f"{avg_imdb:.2f}" if pd.notna(avg_imdb) else "N/A",
            )

            # Película más antigua
            oldest_year = df["YearInt"].min()
            col4.metric(
                "Película más antigua", fmt_year(oldest_year)
            )

            st.markdown("---")

            # 1. Distribución de Mi Nota
            st.subheader("Distribución de Mi Nota (Your Rating)")
            df_ratings = df[df["Your Rating"].notna()]
            if not df_ratings.empty:
                chart_data = (
                    df_ratings.groupby("Your Rating")
                    .size()
                    .reset_index(name="Count")
                )
                
                # Definir colores para cada rating
                rating_colors = {
                    r: get_rating_colors(r)[0] for r in chart_data["Your Rating"].unique()
                }

                chart = (
                    alt.Chart(chart_data)
                    .mark_bar(binSpacing=0, cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
                    .encode(
                        x=alt.X("Your Rating:O", title="Mi Nota"),
                        y=alt.Y("Count:Q", title="Cantidad de Películas"),
                        color=alt.Color(
                            "Your Rating:O",
                            scale=alt.Scale(domain=list(rating_colors.keys()), range=list(rating_colors.values())),
                            legend=None
                        ),
                        tooltip=["Your Rating", "Count"],
                    )
                    .properties(height=350)
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No hay notas disponibles para graficar.")

            st.markdown("---")

            # 2. Top Géneros
            st.subheader("Top 10 Géneros más comunes")
            genre_counts = defaultdict(int)
            for genres in df["GenreList"]:
                for g in genres:
                    genre_counts[g] += 1
            
            df_genres = pd.DataFrame(
                list(genre_counts.items()), columns=["Genre", "Count"]
            ).sort_values("Count", ascending=False).head(10)

            if not df_genres.empty:
                chart_genres = (
                    alt.Chart(df_genres)
                    .mark_bar()
                    .encode(
                        x=alt.X("Count:Q", title="Cantidad de Películas"),
                        y=alt.Y("Genre:N", sort="-x", title="Género"),
                        tooltip=["Genre", "Count"],
                        color=alt.value("#6366f1") 
                    )
                    .properties(height=300)
                )
                st.altair_chart(chart_genres, use_container_width=True)
            else:
                st.info("No hay datos de géneros para graficar.")

            st.markdown("---")

            # 3. Diferencia de Rating (Infra/Sobrevaloradas)
            st.subheader("Diferencia de Notas (Mi Nota - IMDb Rating)")
            
            df_diff = df_ratings[
                ["Title", "Your Rating", "IMDb Rating", "YearInt", "URL"]
            ].copy()
            df_diff["Diff"] = df_diff["Your Rating"] - df_diff["IMDb Rating"]
            
            # Películas más infravaloradas (Tienen mucha más nota de la que da IMDb)
            st.markdown("#### Películas que *infravaloro* (Mi Nota >> IMDb)")
            df_infra = df_diff[df_diff["Diff"] >= 1.5].sort_values("Diff", ascending=False).head(5)
            if not df_infra.empty:
                df_infra["Your Rating"] = df_infra["Your Rating"].apply(lambda x: f"**{x:.1f}**")
                df_infra["IMDb Rating"] = df_infra["IMDb Rating"].apply(lambda x: f"*{x:.1f}*")
                df_infra["Diff"] = df_infra["Diff"].apply(lambda x: f"{x:.1f}")
                df_infra["TitleLink"] = df_infra.apply(
                    lambda r: f'<a href="{r["URL"]}" target="_blank">{r["Title"]} ({r["YearInt"]})</a>', axis=1
                )
                
                st.markdown(
                    df_infra[["TitleLink", "Your Rating", "IMDb Rating", "Diff"]]
                    .rename(columns={"TitleLink": "Película", "Your Rating": "Mi Nota", "IMDb Rating": "IMDb", "Diff": "Diferencia"})
                    .to_html(escape=False, index=False),
                    unsafe_allow_html=True
                )
            else:
                st.info("Ninguna película en esta vista tiene una diferencia significativa.")

            # Películas más sobrevaloradas (Tienen mucha menos nota de la que da IMDb)
            st.markdown("#### Películas que *sobrevaloro* (IMDb >> Mi Nota)")
            df_sobre = df_diff[df_diff["Diff"] <= -1.5].sort_values("Diff", ascending=True).head(5)
            if not df_sobre.empty:
                df_sobre["Your Rating"] = df_sobre["Your Rating"].apply(lambda x: f"*{x:.1f}*")
                df_sobre["IMDb Rating"] = df_sobre["IMDb Rating"].apply(lambda x: f"**{x:.1f}**")
                df_sobre["Diff"] = df_sobre["Diff"].apply(lambda x: f"{x:.1f}")
                df_sobre["TitleLink"] = df_sobre.apply(
                    lambda r: f'<a href="{r["URL"]}" target="_blank">{r["Title"]} ({r["YearInt"]})</a>', axis=1
                )
                
                st.markdown(
                    df_sobre[["TitleLink", "Your Rating", "IMDb Rating", "Diff"]]
                    .rename(columns={"TitleLink": "Película", "Your Rating": "Mi Nota", "IMDb Rating": "IMDb", "Diff": "Diferencia"})
                    .to_html(escape=False, index=False),
                    unsafe_allow_html=True
                )
            else:
                st.info("Ninguna película en esta vista tiene una diferencia significativa.")


    # ----------------- TAB 3: AFI 100 -----------------
    with tab_afi:
        st.header("Lista AFI 100 Years...100 Movies (10th Anniversary)")
        
        afi_df = pd.DataFrame(AFI_LIST)
        afi_df["YearInt"] = afi_df["Year"].astype(int)
        afi_df["NormTitle"] = afi_df["Title"].apply(normalize_title)
        
        # Nuevas columnas para el cruce
        afi_df["Seen"] = False
        afi_df["Your Rating"] = None
        afi_df["IMDb Rating"] = None
        afi_df["URL"] = None

        # Usar el mapa de catálogo precomputado (¡Optimización clave!)
        for idx, row in afi_df.iterrows():
            afi_norm = row.get("NormTitle", "")
            afi_year = row.get("YearInt", -1)
            
            # 1. Búsqueda estricta (NormTitle + Año)
            match_index = catalog_map.get((afi_norm, afi_year))

            # 2. Búsqueda flexible (NormTitle + Año +/- 1)
            if match_index is None:
                for year_offset in [-1, 1]:
                    match_index = catalog_map.get((afi_norm, afi_year + year_offset))
                    if match_index is not None:
                        break # Encontramos match, salimos del bucle offset
            
            # Si hay una coincidencia en el catálogo del usuario
            if match_index is not None:
                match_row = df_full.loc[match_index]
                afi_df.at[idx, "Your Rating"] = match_row.get("Your Rating")
                afi_df.at[idx, "IMDb Rating"] = match_row.get("IMDb Rating")
                afi_df.at[idx, "URL"] = match_row.get("URL")
                afi_df.at[idx, "Seen"] = pd.notna(match_row.get("Your Rating")) # Asumimos vista si hay nota

        # Formateo final para la tabla
        def fmt_link(row):
            title = f"{row['Rank']}. {row['Title']} ({row['Year']})"
            url = row['URL']
            return f'<a href="{url}" target="_blank">{title}</a>' if isinstance(url, str) else title
        
        afi_df["Película"] = afi_df.apply(fmt_link, axis=1)
        afi_df["Mi Nota"] = afi_df["Your Rating"].apply(lambda x: f'<b style="color:{get_rating_colors(x)[0]};">{x:.1f}</b>' if pd.notna(x) else "—")
        afi_df["IMDb"] = afi_df["IMDb Rating"].apply(lambda x: f'{x:.1f}' if pd.notna(x) else "—")
        afi_df["Vista"] = afi_df["Seen"].apply(lambda x: "✅ Sí" if x else "❌ No")
        
        # Resumen rápido
        total_seen = afi_df["Seen"].sum()
        st.markdown(f"**Resumen:** Has visto **{total_seen}** de las 100 películas ({(total_seen/100)*100:.1f}%).")

        # Configuración de la tabla final
        cols_to_display = ["Película", "Mi Nota", "IMDb", "Vista"]

        def style_afi_row(row):
            if row["Vista"] == "✅ Sí":
                return ['background-color: rgba(34, 197, 94, 0.1)'] * len(cols_to_display)
            return [''] * len(cols_to_display)

        styler = (
            afi_df[cols_to_display]
            .style.apply(style_afi_row, axis=1)
            .hide(axis="index")
            .set_properties(**{"text-align": "left", "border": "none"})
            .set_table_styles([
                {'selector': 'th', 'props': [('background-color', '#1e293b'), ('color', '#e5e7eb')]},
                {'selector': 'td', 'props': [('padding', '10px 12px')]}
            ])
        )

        st.markdown(styler.to_html(), unsafe_allow_html=True)


    # ----------------- TAB 4: ¿QUÉ VER HOY? -----------------
    with tab_today:
        st.header("✨ Recomendación del día")

        # Opciones para la recomendación
        st.subheader("Opciones de filtro rápido:")
        col_rec_1, col_rec_2 = st.columns(2)
        
        # Filtrar por Género (sólo los que están en tu catálogo)
        selected_genre_rec = col_rec_1.selectbox(
            "Filtrar por género:", ["Cualquiera"] + all_genres, key="rec_genre"
        )
        
        # Vistas vs Sin ver
        view_mode_rec = col_rec_2.radio(
            "Tipo de película:", ["Sin ver", "Vista (alta nota)"], key="rec_view_mode"
        )
        
        # Filtrar por año
        if min_year_default is not None and max_year_default is not None:
            year_range_rec = st.slider(
                "Rango de años:", 
                min_value=int(min_year_default),
                max_value=int(max_year_default),
                value=(int(min_year_default), int(max_year_default)),
                step=1,
                key="rec_year_range",
            )
        else:
            year_range_rec = (1900, 2025)
            
        st.markdown("---")

        
        # Lógica de la recomendación
        filtered_view = df_full.copy()
        
        # Filtro de Género
        if selected_genre_rec != "Cualquiera":
            filtered_view = filtered_view[
                filtered_view["GenreList"].apply(lambda x: selected_genre_rec in x)
            ]

        # Filtro de Año
        filtered_view = filtered_view[
            (filtered_view["YearInt"] >= year_range_rec[0])
            & (filtered_view["YearInt"] <= year_range_rec[1])
        ]

        # Filtro de Vistas
        if view_mode_rec == "Sin ver":
            filtered_view = filtered_view[
                filtered_view["Your Rating"].isna()
            ] 
        elif view_mode_rec == "Vista (alta nota)":
            filtered_view = filtered_view[
                (filtered_view["Your Rating"].notna()) & (filtered_view["Your Rating"] >= 7.5)
            ]
        
        # Pool de selección: usa una combinación de IMDb (o TMDb si existe) y aleatoriedad
        if filtered_view.empty:
            st.error("No hay películas que coincidan con estos filtros. ¡Prueba otros!")
            today_movie = None
        else:
            # Ponderación para la selección (más aleatorio que el top)
            weights = filtered_view["IMDb Rating"].fillna(filtered_view["IMDb Rating"].mean()).apply(lambda x: (x / 10.0) ** 2)
            weights = weights / weights.sum() # Normalizar
            
            today_movie = filtered_view.sample(1, weights=weights, random_state=random.randint(0, 10000)).iloc[0]


        if today_movie is not None:
            # --- Renderizado de la Película Recomendada ---
            
            # Datos principales
            title = today_movie.get("Title")
            year = today_movie.get("YearInt")
            imdb_url = today_movie.get("URL")
            
            # Datos de APIs
            tmdb_info, providers_info = get_tmdb_and_providers_for_title(title, year)
            
            # Datos de Rating
            my_rating = today_movie.get("Your Rating")
            imdb_rating = today_movie.get("IMDb Rating")
            tmdb_rating = tmdb_info.get("vote_average") if tmdb_info else None
            
            # Streaming (CL)
            platforms_str = "Sin datos para Chile (CL)"
            streaming_link = None
            if providers_info:
                platforms = providers_info.get("platforms") or []
                platforms_str = ", ".join(platforms) if platforms else "Sin datos para Chile (CL)"
                streaming_link = providers_info.get("link")

            # Colores
            base_rating = my_rating if pd.notna(my_rating) else imdb_rating
            border_color, glow_color = get_rating_colors(base_rating)

            # Poster
            poster_url = tmdb_info.get("poster_url") if tmdb_info else None
            if isinstance(poster_url, str) and poster_url:
                poster_html = (
                    "<div style='width: 100%; max-width: 200px; margin: 0 auto;'>"
                    "<div class='movie-poster-frame' style='margin:0;'>"
                    f"<img src='{poster_url}' alt='{title}' class='movie-poster-img' />"
                    "</div></div>"
                )
            else:
                poster_html = (
                    "<div style='width: 100%; max-width: 200px; margin: 0 auto;'>"
                    "<div class='movie-poster-frame' style='margin:0;'>"
                    "<div class='movie-poster-placeholder'>"
                    "<div class='film-reel-icon'>🎞️</div>"
                    "<div class='film-reel-text'>Sin póster</div>"
                    "</div></div></div>"
                )
            
            # Trailer de YouTube
            trailer_url = get_youtube_trailer_url(title, year)
            
            # Contenedor principal de la tarjeta
            card_html = f"""
            <div class="movie-card" style="
                border-color:{border_color}; 
                box-shadow:0 0 0 1px rgba(15,23,42,0.9), 0 0 30px {glow_color};
                display: flex; flex-direction: column; align-items: center; text-align: center;
                padding: 30px;
            ">
                {poster_html}
                <h2 style='margin-top:20px; margin-bottom: 5px; color:#f8fafc; border-bottom: none;'>{title} ({fmt_year(year)})</h2>
                
                <div style='margin-bottom: 20px; font-size: 0.95rem; color: #94a3b8;'>
                    **Géneros:** {today_movie.get("Genres")}
                </div>

                <div style='display: flex; gap: 20px; margin-bottom: 25px;'>
                    <div class="rating-box">Mi Nota: {fmt_rating(my_rating)}</div>
                    <div class="rating-box">IMDb: {fmt_rating(imdb_rating)}</div>
                    <div class="rating-box">TMDb: {fmt_rating(tmdb_rating)}</div>
                </div>
                
                <div style='margin-bottom: 20px; font-size: 0.85rem;'>
                    Streaming (CL): {platforms_str}
                    {f'<br><a href="{streaming_link}" target="_blank">Ver streaming en TMDb (CL)</a>' if streaming_link else ''}
                </div>

                <div style='display: flex; gap: 15px;'>
                    {f'<a href="{imdb_url}" target="_blank" style="padding: 10px 15px; background: #475569; border-radius: 6px;">Ver ficha en IMDb</a>' if imdb_url else ''}
                    {f'<a href="{trailer_url}" target="_blank" style="padding: 10px 15px; background: #ef4444; border-radius: 6px;">Ver tráiler en YouTube</a>' if trailer_url else ''}
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            st.markdown("---")
            st.subheader("Otras recomendaciones similares")
            recs_df = recommend_from_catalog(df_full, today_movie, top_n=5)
            
            if recs_df.empty:
                st.info("No se encontraron películas similares en tu catálogo.")
            else:
                cards_html_recs = ["<div class='movie-gallery-grid'>"]
                for _, row_rec in recs_df.iterrows():
                    # Obtener info de APIs (cacheado)
                    tmdb_info2, _ = get_tmdb_and_providers_for_title(row_rec.get("Title"), row_rec.get("Year"))

                    my2 = row_rec.get("Your Rating")
                    imdb2 = row_rec.get("IMDb Rating")
                    
                    base_rating2 = my2 if pd.notna(my2) else imdb2
                    border_color2, glow_color2 = get_rating_colors(base_rating2)
                    
                    poster_url2 = tmdb_info2.get("poster_url") if tmdb_info2 else None
                    if isinstance(poster_url2, str) and poster_url2:
                        poster_html2 = (
                            "<div class='movie-poster-frame'>"
                            f"<img src='{poster_url2}' alt='{row_rec.get('Title')}' class='movie-poster-img' />"
                            "</div>"
                        )
                    else:
                        poster_html2 = (
                            "<div class='movie-poster-frame'>"
                            "<div class='movie-poster-placeholder'>"
                            "<div class='film-reel-icon'>🎞️</div>"
                            "<div class='film-reel-text'>Sin póster</div>"
                            "</div></div>"
                        )
                    
                    t2 = row_rec.get("Title")
                    y2_str = f" ({fmt_year(row_rec.get('Year'))})"
                    url2 = row_rec.get("URL")
                    
                    my2_str = (
                        fmt_rating(my2) if pd.notna(my2) else "—"
                    )
                    imdb2_str = (
                        fmt_rating(imdb2) if pd.notna(imdb2) else "—"
                    )

                    imdb_link2 = (
                        f'<a href="{url2}" target="_blank">Ver en IMDb</a>'
                        if isinstance(url2, str) and url2.startswith("http")
                        else ""
                    )

                    card_html2 = f"""
<div class="movie-card movie-card-grid" style="
    border-color: {border_color2};
    box-shadow:
        0 0 0 1px rgba(15,23,42,0.9),
        0 0 22px {glow_color2};
">
  {poster_html2}
  <div class="movie-title">{t2}{y2_str}</div>
  <div class="movie-sub">
    <b>Mi nota:</b> {my2_str} · <b>IMDb:</b> {imdb2_str}<br>
    {imdb_link2}
  </div>
</div>
"""
                    cards_html_recs.append(card_html2)

                cards_html_recs.append("</div>")
                gallery_recs_html = "\n".join(cards_html_recs)
                st.markdown(gallery_recs_html, unsafe_allow_html=True)

        else:
            st.info("No se pudo generar una recomendación con los filtros actuales.")



    # ----------------- TAB: PREMIOS ÓSCAR -----------------
    if osc_available and tab_oscar is not None:
        with tab_oscar:
            st.header("🏆 Premios Óscar (Nominaciones y Ganadores)")

            if osc_df.empty:
                st.warning("No se pudo cargar o procesar el dataset de los Óscar.")
            else:
                
                # Resumen de rango de años
                min_c = osc_df["Ceremony"].min()
                max_c = osc_df["Ceremony"].max()
                
                st.caption(f"Datos desde la ceremonia **#{min_c}** hasta la **#{max_c}**.")
                
                # Selector de Año de Ceremonia
                ceremonies = sorted(osc_df["Ceremony"].unique(), reverse=True)
                selected_ceremony = st.selectbox(
                    "Selecciona el año de la Ceremonia:", ceremonies, index=0
                )
                
                # --- Filtro principal ---
                df_osc_year = osc_df[osc_df["Ceremony"] == selected_ceremony].copy()
                
                # --- Vista por Categoría/Ganadores ---
                st.markdown("---")
                st.subheader(f"Ganadores y Nominados de la Ceremonia #{selected_ceremony}")
                
                # Obtener la lista de categorías canónicas únicas para el año seleccionado
                canon_cats = sorted(df_osc_year["CanonCat"].unique())

                if not canon_cats:
                    st.warning("No hay datos de categorías para el año seleccionado.")
                else:
                    
                    # 1. Resumen de películas
                    film_summary = (
                        df_osc_year.groupby("Film")
                        .agg(
                            Nominations=("Film", "size"),
                            Wins=("IsWinner", "sum"),
                            InMyCatalog=("InMyCatalog", "max"),
                            YearInt=("YearInt", "first"),
                            MyRating=("MyRating", "first"),
                            IMDbRating=("MyIMDb", "first"),
                            CatalogURL=("CatalogURL", "first"),
                        )
                        .reset_index()
                        .sort_values(["Wins", "Nominations"], ascending=[False, False])
                    )
                    
                    film_summary = film_summary[film_summary["Nominations"] > 0]
                    
                    st.markdown("#### Resumen de Películas (Máximos Ganadores)")
                    
                    # Tabla de Resumen
                    film_summary["TitleLink"] = film_summary.apply(
                        lambda r: f'<a href="{r["CatalogURL"]}" target="_blank">{r["Film"]} ({fmt_year(r["YearInt"])})</a>' 
                                  if isinstance(r["CatalogURL"], str) and r["CatalogURL"].startswith("http") else f'{r["Film"]} ({fmt_year(r["YearInt"])})', axis=1
                    )
                    
                    film_summary["Mi Nota"] = film_summary["MyRating"].apply(lambda x: f'<b style="color:{get_rating_colors(x)[0]};">{x:.1f}</b>' if pd.notna(x) else "—")
                    film_summary["IMDb"] = film_summary["IMDbRating"].apply(lambda x: f'{x:.1f}' if pd.notna(x) else "—")
                    film_summary["En Catálogo"] = film_summary["InMyCatalog"].apply(lambda x: "✅ Sí" if x else "❌ No")

                    cols_summary = ["TitleLink", "Nominations", "Wins", "Mi Nota", "IMDb", "En Catálogo"]
                    
                    def style_summary_row(row):
                        if row["Wins"] > 0:
                            return ['background-color: rgba(34, 197, 94, 0.1)'] * len(cols_summary)
                        return [''] * len(cols_summary)
                        
                    styler_summary = (
                        film_summary[cols_summary]
                        .rename(columns={"TitleLink": "Película", "Nominations": "Noms", "Wins": "Premios"})
                        .style.apply(style_summary_row, axis=1)
                        .hide(axis="index")
                        .set_properties(**{"text-align": "left", "border": "none"})
                        .set_table_styles([
                            {'selector': 'th', 'props': [('background-color', '#1e293b'), ('color', '#e5e7eb')]},
                            {'selector': 'td', 'props': [('padding', '8px 10px')]}
                        ])
                    )
                    st.markdown(styler_summary.to_html(), unsafe_allow_html=True)
                    st.markdown("---")
                    
                    # 2. Galería de Ganadores por Categoría
                    
                    # Colapso por categorías
                    for cat in canon_cats:
                        df_cat = df_osc_year[df_osc_year["CanonCat"] == cat].copy()
                        
                        # Agrupar las nominaciones por Film (porque una película puede tener múltiples nominados en la misma categoría)
                        df_films_in_cat = (
                            df_cat.groupby("Film")
                            .agg(
                                YearInt=("YearInt", "first"),
                                Nominee=("Nominee", lambda x: " / ".join(x.dropna().astype(str))),
                                WinnerCount=("IsWinner", "sum"),
                                InMyCatalog=("InMyCatalog", "max"),
                                MyRating=("MyRating", "first"),
                                MyIMDb=("MyIMDb", "first"),
                                CatalogURL=("CatalogURL", "first"),
                            )
                            .reset_index()
                            .sort_values("WinnerCount", ascending=False) # Ganadores al principio
                        )
                        
                        
                        with st.expander(f"🏅 {cat} ({len(df_films_in_cat)} Nominados)"):
                            
                            # Mostrar las tarjetas de cada película nominada en la categoría
                            cards_html_cat = ["<div class='movie-gallery-grid'>"]
                            
                            
                            for _, row_film in df_films_in_cat.iterrows():
                                
                                is_winner = row_film["WinnerCount"] > 0
                                
                                # Simular una 'fila' de la película (datos mínimos para la función de tarjeta)
                                mock_row = {
                                    "Film": row_film["Film"],
                                    "YearInt": row_film["YearInt"],
                                    "InMyCatalog": row_film["InMyCatalog"],
                                    "MyRating": row_film["MyRating"],
                                    "MyIMDb": row_film["MyIMDb"],
                                    "CatalogURL": row_film["CatalogURL"],
                                    "Category": cat, # La categoría es el foco principal aquí
                                    "Nominee": row_film["Nominee"] # La lista de personas/entidades
                                }
                                
                                # Contar las nominaciones y premios totales para el badge de resumen
                                # Se usa el film_summary precalculado para no tener que buscar de nuevo
                                summary_match = film_summary[film_summary["Film"] == row_film["Film"]]
                                total_wins = summary_match["Wins"].iloc[0] if not summary_match.empty else 0
                                total_noms = summary_match["Nominations"].iloc[0] if not summary_match.empty else 0
                                
                                card_html = _build_oscar_card_html(
                                    mock_row,
                                    categories_for_film=[cat], # Solo la categoría actual
                                    is_winner_in_this_context=is_winner,
                                    wins_for_film=total_wins, # Totales de la película
                                    noms_for_film=total_noms
                                )
                                cards_html_cat.append(card_html)
                            
                            cards_html_cat.append("</div>")
                            st.markdown("\n".join(cards_html_cat), unsafe_allow_html=True)
                            
                # --- Análisis de Tendencias y Ránking (Rango de Años) ---
                
                st.markdown("---")
                st.subheader("Análisis y Ránking Histórico (Todas las Ceremonias)")
                
                # Selector de Rango
                min_ceremony = st.slider(
                    "Rango de Ceremonias a analizar:", 
                    min_value=min_c, 
                    max_value=max_c, 
                    value=(max(min_c, max_c - 15), max_c), # Por defecto, últimos 15
                    step=1,
                    key="oscar_year_range",
                )
                
                df_osc_range = osc_df[
                    (osc_df["Ceremony"] >= min_ceremony[0])
                    & (osc_df["Ceremony"] <= min_ceremony[1])
                ].copy()
                
                if not df_osc_range.empty:
                    
                    # Ránking 1: Películas con más Nominaciones
                    st.markdown("#### Top 10 Películas con más Nominaciones")
                    df_rank_film = (
                        df_osc_range.groupby("Film")
                        .agg(
                            Nominations=("Film", "size"),
                            Wins=("IsWinner", "sum"),
                        )
                        .reset_index()
                        .sort_values("Nominations", ascending=False)
                        .head(10)
                    )
                    st.dataframe(df_rank_film, hide_index=True)
                    
                    # Ránking 2: Personas/Entidades con más Nominaciones (excluyendo "Film")
                    st.markdown("#### Top 10 Entidades (Personas/Productoras) con más Nominaciones")
                    
                    # Expande la lista de NomineeIds para contar individualmente
                    df_ids = df_osc_range.explode("NomineeIdList")
                    
                    # Filtra las IDs que no son de personas/entidades (ej. el nombre de la película)
                    # Se usa un filtro simple, ya que el NomineeIdList del dataset es inconsistente
                    df_ids = df_ids[df_ids["NomineeIdList"].str.len() > 3] 
                    
                    df_rank_nom = (
                        df_ids.groupby("NomineeIdList")
                        .agg(
                            Nominations=("NomineeIdList", "size"),
                            Wins=("IsWinner", "sum"),
                            Ejemplo=("Nominee", "first"), # Tomar un ejemplo de nombre (Nominee)
                        )
                        .reset_index()
                        .sort_values("Nominations", ascending=False)
                        .head(10)
                    )
                    
                    # Renombrar IDs al nombre de ejemplo para la visualización
                    df_rank_nom["Entidad"] = df_rank_nom["Ejemplo"]
                    
                    st.dataframe(df_rank_nom[["Entidad", "Nominations", "Wins"]], hide_index=True)
                    
                else:
                    st.info("No hay datos de Óscar en el rango de ceremonias seleccionado.")

# ----------------- FIN DE LA APLICACIÓN -----------------
