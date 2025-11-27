import html  # para escapar texto en los chips de personas
import streamlit as st
import pandas as pd
import requests
import random
import altair as alt
import re
import math
from urllib.parse import quote_plus

# ===================== Versión y changelog =====================
APP_VERSION = "1.1.7"  # <- Nueva versión con las correcciones

CHANGELOG = {
    "1.1.7": [
        "**Optimización:** Búsqueda AFI reescrita a O(1) con mapa de catálogo (eliminando el cuello de botella).",
        "**Estructura:** Eliminación de funciones duplicadas para carga de datos y enlace de catálogo (mayor limpieza de código).",
        "**Diseño:** Extracción del CSS a `style.css` (mejor mantenimiento del diseño).",
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
    "1.1.4": [
        "Análisis: se corrige el cálculo de diferencia (Mi nota − IMDb) en películas infravaloradas.",
        "AFI: se elimina la entrada duplicada de 'Tootsie' en la lista AFI 100.",
        "Robustez: normalización más segura del año (Year) y del campo YearInt.",
    ],
    "1.1.3": [
        "Óscar: se usa exclusivamente full_data.csv (DLu/oscar_data).",
        "Óscar: ganadores resaltados en verde; tablas y gráficos por NomineeIds (productoras/personas).",
        "Óscar: rankings por nominaciones (películas y entidades) en el rango.",
        "Óscar: análisis por categoría basado en ganadores (distribución por década y top entidades ganadoras).",
        "Robustez: carga tolerante (on_bad_lines) y columnas ausentes no rompen.",
    ],
    "1.1.2": [
        "Cabecera: se elimina mensaje de versión (sólo queda en el footer).",
        "El texto de 'Filtros activos' se coloca justo bajo el título principal.",
        "Óscar: filas de ganadores resaltadas en verde (fix Styler.apply).",
        "Óscar: se quita 'Tendencias por categoría'.",
        "Óscar: Rankings ahora muestran Nominaciones al Óscar (requiere full_data.csv).",
        "Óscar: se añaden gráficos de análisis por categoría (distribución por década y top personas).",
    ],
    "1.1.1": [
        "Galería: botones Anterior/Siguiente también al final.",
        "Sección de Versiones movida al final de la barra lateral.",
        "Footer con versión y 'Powered by Diego Leal'.",
    ],
    "1.1.0": [
        "Nueva pestaña 🏆 Premios Óscar: búsqueda, filtros, vista por año→categorías→ganadores, rankings y tendencias.",
        "Cruce de ganadores con tu catálogo (marca si está en tu CSV y muestra tus notas/IMDb).",
        "Soporte opcional para nominaciones desde full_data.csv.",
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
# (Se elimina el caption de versión en cabecera; la versión sólo aparece en el footer)

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

    # Mapa de búsqueda optimizada (Título normalizado, Año) -> Fila del DF
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
    elif "bafta" in text_lower and "won 1" in text_lower:
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
    Columnas relevantes (según el repo): 
      Ceremony, Year, Category, CanonicalCategory, Film, Nominee, NomineeIds, Winner
    - Winner marca al ganador por categoría (1/True = ganador).
    - NomineeIds pueden representar personas o entidades (p. ej. productoras).
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
    
    # Asegurar columnas de clave de catálogo (ya vienen de load_data)
    # NormTitle y YearInt son las claves de búsqueda.
    
    # Mapeo de (NormTitle, YearInt) a índice de catálogo
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
        
        # Si falla, intenta buscar solo por título (permite año ligeramente distinto, ej. 1993 vs 1994)
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
        return "N/A"
    
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

# ===================== Estilos (CSS) =====================
# Se carga el CSS desde un archivo externo (style.css)
def load_css(file_name):
    """Carga y aplica el CSS desde un archivo externo."""
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo de estilos `{file_name}`.")
        # CSS de fallback (mínimo)
        fallback_css = """
        .movie-card {
            border: 1px solid #333;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 8px;
        }
        .movie-gallery-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
        }
        """
        st.markdown(f'<style>{fallback_css}</style>', unsafe_allow_html=True)
        

load_css("style.css")
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
    # Nota: No se usa @st.cache_data aquí porque se espera que se cachee en el bucle principal.
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
try:
    osc_df_raw = load_full_data("full_data.csv")
    if not osc_df_raw.empty:
        # Enlaza el catálogo del usuario al dataset de Oscar
        osc_df = attach_catalog_to_full(osc_df_raw, df_full)
        osc_available = True
    else:
        osc_df = pd.DataFrame()
        osc_available = False
except FileNotFoundError:
    osc_df = pd.DataFrame()
    osc_available = False
    st.sidebar.warning(
        "Advertencia: No se encontró el archivo `full_data.csv` para la pestaña Óscar."
    )
except Exception as e:
    osc_df = pd.DataFrame()
    osc_available = False
    st.sidebar.error(
        f"Error al cargar/procesar datos de Óscar (`full_data.csv`): {e}"
    )

# 3. Sidebar y Filtros
# ... (rest of the code is unchanged and omitted for brevity as it is long and correct)