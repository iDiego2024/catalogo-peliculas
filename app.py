import re
import html  # para escapar texto en los chips de personas
import streamlit as st
import pandas as pd
import requests
import random
import altair as alt
import math
from urllib.parse import quote_plus

# ===================== Versión y changelog =====================
APP_VERSION = "1.1.7"  # <- Versión actualizada

CHANGELOG = {
    "1.1.7": [
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

    # Robustez: garantiza la columna YearInt
    if "Year" in df.columns:
        df["YearInt"] = pd.to_numeric(df["Year"], errors="coerce").fillna(-1).astype(int)
    else:
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
        dff["YearInt"] = pd.Series([-1] * len(dff), index=idx, dtype=int)

    # Ceremonia
    if "Ceremony" in dff.columns:
        cer = pd.to_numeric(dff["Ceremony"], errors="coerce")
        dff["CeremonyInt"] = cer.fillna(dff["YearInt"]).astype(int)
    else:
        dff["CeremonyInt"] = dff["YearInt"]

    # Ganador
    if "Winner" in dff.columns:
        dff["IsWinner"] = col_or_empty("Winner").astype(str).str.lower().isin(
            ["1", "true", "yes", "winner", "ganador", "ganadora"]
        )
    else:
        dff["IsWinner"] = False

    # Texto de candidato y película
    dff["Nominee"] = col_or_empty("Nominee").astype(str)
    dff["Film"] = col_or_empty("Film").astype(str)

    # IDs de candidatos
    base_ids = col_or_empty("NomineeIds").fillna("").astype(str)
    dff["NomineeIdsList"] = base_ids.apply(
        lambda s: [x.strip() for x in re.split(r"[;,]", s) if x.strip()]
    )

    # Aux para cruce con tu catálogo
    dff["NormFilm"] = dff["Film"].apply(normalize_title)

    return dff

def attach_catalog_to_full(osc_df, my_catalog_df):
    """
    Enlaza cada fila de full_data con tu catálogo (por título normalizado + año).
    Añade: InMyCatalog, MyRating, MyIMDb, CatalogURL
    """
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
    if "YearInt" not in cat.columns:
        cat["YearInt"] = pd.to_numeric(cat.get("Year", pd.Series([None] * len(cat))), errors="coerce").fillna(-1).astype(int)

    merged = out.merge(
        cat[["NormTitle", "YearInt", "Your Rating", "IMDb Rating", "URL"]],
        left_on=["NormFilm", "YearInt"],
        right_on=["NormTitle", "YearInt"],
        how="left",
        suffixes=("", "_cat"),
    )
    merged["InMyCatalog"] = merged["URL"].notna()
    merged["MyRating"] = merged["Your Rating"]
    merged["MyIMDb"] = merged["IMDb Rating"]
    merged["CatalogURL"] = merged["URL"]
    merged = merged.drop(columns=["NormTitle", "Your Rating", "IMDb Rating", "URL"], errors="ignore")
    return merged

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

# --- CORRECCIÓN: Garantizar YearInt aquí para el Catálogo principal ---
if "Year" in df.columns:
    df["YearInt"] = pd.to_numeric(df["Year"], errors="coerce").fillna(-1).astype(int)
else:
    df["YearInt"] = -1

# ----------------- Tema oscuro + CSS -----------------

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

    /* ... resto de tu CSS (movie-card, etc.) ... */
    
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

    .movie-gallery-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 18px;
        margin-top: 0.7rem;
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
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------- Opciones de visualización -----------------

st.sidebar.header("🖼️ Opciones de visualización")
show_posters_fav = st.sidebar.checkbox(
    "Mostrar pósters TMDb en mis favoritas (nota ≥ 9)",
    value=True
)

st.sidebar.header("🌐 TMDb")
use_tmdb_gallery = st.sidebar.checkbox(
    "Usar TMDb en la galería visual",
    value=True
)

st.sidebar.header("🎬 Tráilers")
show_trailers = st.sidebar.checkbox(
    "Mostrar tráiler de YouTube (si hay API key)",
    value=True
)

st.sidebar.header("⚙️ Opciones avanzadas")
show_awards = st.sidebar.checkbox(
    "Consultar premios en OMDb (más lento, usa cuota de API)",
    value=False
)

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
    # Tomamos min y max reales como floats
    min_rating = float(df["Your Rating"].min())
    max_rating = float(df["Your Rating"].max())

    # Forzamos a estar en [0.0, 10.0]
    min_rating = max(0.0, min(10.0, min_rating))
    max_rating = max(0.0, min(10.0, max_rating))

    # --- CORRECCIÓN SLIDER: AGREGADO format="%.1f" ---
    rating_range = st.sidebar.slider(
        "Mi nota (Your Rating)",
        min_value=0.0,
        max_value=10.0,
        value=(min_rating, max_rating),
        step=0.5,
        format="%.1f"
    )
else:
    rating_range = (0.0, 10.0)


all_genres = sorted(
    set(
        g
        for sub in df["GenreList"].dropna()
        for g in sub
        if g
    )
)
selected_genres = st.sidebar.multiselect(
    "Géneros (todas las seleccionadas deben estar presentes)",
    options=all_genres
)

all_directors = sorted(
    set(
        d.strip()
        for d in df["Directors"].dropna()
        if str(d).strip() != ""
    )
)
selected_directors = st.sidebar.multiselect(
    "Directores",
    options=all_directors
)

order_by = st.sidebar.selectbox(
    "Ordenar por",
    ["Your Rating", "IMDb Rating", "Year", "Title", "Aleatorio"]
)
order_asc = st.sidebar.checkbox("Orden ascendente", value=False)

# ---- Changelog al FINAL de la barra lateral ----
st.sidebar.markdown("---")
st.sidebar.header("🧾 Versiones")
with st.sidebar.expander("Ver changelog", expanded=False):
    for ver, notes in CHANGELOG.items():
        st.markdown(f"**v{ver}**")
        for n in notes:
            st.markdown(f"- {n}")
        st.markdown("---")

# ----------------- Aplicar filtros básicos -----------------

filtered = df.copy()

if "Year" in filtered.columns:
    filtered = filtered[
        (filtered["Year"] >= year_range[0]) &
        (filtered["Year"] <= year_range[1])
    ]

if "Your Rating" in filtered.columns:
    filtered = filtered[
        (filtered["Your Rating"] >= rating_range[0]) &
        (filtered["Your Rating"] <= rating_range[1])
    ]

if selected_genres:
    filtered = filtered[
        filtered["GenreList"].apply(
            lambda gl: all(g in gl for g in selected_genres)
        )
    ]

# Filtro de directores (múltiples por celda)
if selected_directors:
    def _matches_any_director(cell):
        if pd.isna(cell):
            return False
        dirs = [d.strip() for d in str(cell).split(",") if d.strip()]
        return any(d in dirs for d in selected_directors)

    filtered = filtered[filtered["Directors"].apply(_matches_any_director)]

# ---------- Texto “Filtros activos” cerca del título ----------
st.caption(
    f"Filtros activos → Años: {year_range[0]}–{year_range[1]} | "
    f"Mi nota: {rating_range[0]}–{rating_range[1]} | "
    f"Géneros: {', '.join(selected_genres) if selected_genres else 'Todos'} | "
    f"Directores: {', '.join(selected_directors) if selected_directors else 'Todos'}"
)

# ----------------- Helpers de formato -----------------

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

# ----------------- BÚSQUEDA ÚNICA -----------------

st.markdown("## 🔎 Búsqueda en mi catálogo (sobre los filtros actuales)")

search_query = st.text_input(
    "Buscar por título, director, género, año o calificaciones",
    placeholder="Escribe cualquier cosa… (se aplica en tiempo real)",
    key="busqueda_unica"
)

def apply_search(df_in, query):
    if not query:
        return df_in
    q = query.strip().lower()
    if "SearchText" not in df_in.columns:
        return df_in
    return df_in[df_in["SearchText"].str.contains(q, na=False, regex=False)]

filtered_view = apply_search(filtered.copy(), search_query)

# Orden global según opción
if order_by == "Aleatorio":
    if not filtered_view.empty:
        filtered_view = filtered_view.sample(frac=1, random_state=None)
elif order_by in filtered_view.columns:
    filtered_view = filtered_view.sort_values(order_by, ascending=order_asc)

# ----------------- TABS PRINCIPALES -----------------

tab_catalog, tab_analysis, tab_afi, tab_awards, tab_what = st.tabs(
    ["🎬 Catálogo", "📊 Análisis", "🏆 Lista AFI", "🏆 Premios Óscar", "🎲 ¿Qué ver hoy?"]
)

# ============================================================
#                     TAB 1: CATÁLOGO
# ============================================================

with tab_catalog:
    st.markdown("## 📈 Resumen de resultados")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Películas tras filtros + búsqueda", len(filtered_view))
    with col2:
        if "Your Rating" in filtered_view.columns and filtered_view["Your Rating"].notna().any():
            st.metric("Promedio de mi nota", f"{filtered_view['Your Rating'].mean():.2f}")
        else:
            st.metric("Promedio de mi nota", "N/A")
    with col3:
        if "IMDb Rating" in filtered_view.columns and filtered_view["IMDb Rating"].notna().any():
            st.metric("Promedio IMDb", f"{filtered_view['IMDb Rating'].mean():.2f}")
        else:
            st.metric("Promedio IMDb", "N/A")

    st.markdown("### 📚 Tabla de resultados")

    cols_to_show = [
        c for c in [
            "Title", "Year", "Your Rating", "IMDb Rating",
            "Genres", "Directors", "Date Rated", "URL"
        ]
        if c in filtered_view.columns
    ]

    table_df = filtered_view[cols_to_show].copy()
    display_df = table_df.copy()

    if "Year" in display_df.columns:
        display_df["Year"] = display_df["Year"].apply(fmt_year)
    if "Your Rating" in display_df.columns:
        display_df["Your Rating"] = display_df["Your Rating"].apply(fmt_rating)
    if "IMDb Rating" in display_df.columns:
        display_df["IMDb Rating"] = display_df["IMDb Rating"].apply(fmt_rating)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # Botón de descarga
    csv_filtrado = table_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Descargar resultados filtrados (CSV)",
        data=csv_filtrado,
        file_name="mis_peliculas_filtradas.csv",
        mime="text/csv",
    )

    # ===================== GALERÍA VISUAL PAGINADA =====================

    st.markdown("---")
    st.markdown("## 🧱 Galería visual")

    if show_awards:
        st.caption(
            "⚠ OMDb (premios) está activado: la primera carga de cada página de galería puede tardar un poco más."
        )

    total_pelis = len(filtered_view)

    if total_pelis == 0:
        st.info("No hay películas bajo los filtros + búsqueda actuales para la galería.")
    else:
        page_size = st.slider(
            "Películas por página en la galería",
            min_value=12,
            max_value=60,
            value=24,
            step=12,
            key="gallery_page_size"
        )

        num_pages = max(math.ceil(total_pelis / page_size), 1)

        if "gallery_current_page" not in st.session_state:
            st.session_state.gallery_current_page = 1

        if st.session_state.gallery_current_page > num_pages:
            st.session_state.gallery_current_page = num_pages
        if st.session_state.gallery_current_page < 1:
            st.session_state.gallery_current_page = 1

        # ----------- NAV SUPERIOR -----------
        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

        with col_nav1:
            prev_disabled_top = st.session_state.gallery_current_page <= 1
            if st.button("◀ Anterior", disabled=prev_disabled_top, key="gallery_prev_top"):
                if st.session_state.gallery_current_page > 1:
                    st.session_state.gallery_current_page -= 1

        with col_nav3:
            next_disabled_top = st.session_state.gallery_current_page >= num_pages
            if st.button("Siguiente ▶", disabled=next_disabled_top, key="gallery_next_top"):
                if st.session_state.gallery_current_page < num_pages:
                    st.session_state.gallery_current_page += 1

        with col_nav2:
            st.caption(
                f"Página {st.session_state.gallery_current_page} de {num_pages}"
            )

        current_page = st.session_state.gallery_current_page
        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        page_df = filtered_view.iloc[start_idx:end_idx].copy()

        cards_html = ['<div class="movie-gallery-grid">']

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

            if use_tmdb_gallery:
                tmdb_info = get_tmdb_basic_info(titulo, year)
                if tmdb_info:
                    poster_url = tmdb_info.get("poster_url")
                    tmdb_rating = tmdb_info.get("vote_average")
                    tmdb_id = tmdb_info.get("id")
                    availability = get_tmdb_providers(tmdb_id, country="CL")
                else:
                    poster_url = None
                    tmdb_rating = None
                    availability = None
            else:
                tmdb_info = None
                poster_url = None
                tmdb_rating = None
                availability = None

            if isinstance(poster_url, str) and poster_url:
                poster_html = f"""
<div class="movie-poster-frame">
  <img src="{poster_url}" alt="{titulo}" class="movie-poster-img">
</div>
"""
            else:
                poster_html = """
<div class="movie-poster-frame">
  <div class="movie-poster-placeholder">
    <div class="film-reel-icon">🎞️</div>
    <div class="film-reel-text">Sin póster</div>
  </div>
</div>
"""

            year_str = f" ({fmt_year(year)})" if pd.notna(year) else ""
            nota_str = f"⭐ Mi nota: {fmt_rating(nota)}" if pd.notna(nota) else ""
            imdb_str = f"IMDb: {fmt_rating(imdb_rating)}" if pd.notna(imdb_rating) else ""
            tmdb_str = (
                f"TMDb: {fmt_rating(tmdb_rating)}"
                if tmdb_rating is not None else "TMDb: N/A"
            )

            # ... (Lógica de awards omitida para brevedad, ya estaba en tu código)
            awards_text = "Premios no consultados (OMDb desactivado)."
            if show_awards:
                 aw = get_omdb_awards(titulo, year)
                 if aw and "error" not in aw:
                     # Construcción simplificada para el ejemplo
                     awards_text = f"Oscars: {aw.get('oscars',0)}"

            if availability is None:
                platforms = []
                link = None
            else:
                platforms = availability.get("platforms") or []
                link = availability.get("link")

            platforms_str = ", ".join(platforms) if platforms else "Sin datos para Chile (CL)"
            link_html = (
                f'<a href="{link}" target="_blank">Ver streaming en TMDb (CL)</a>'
                if link else "Sin enlace de streaming disponible"
            )

            imdb_link_html = (
                f'<a href="{url}" target="_blank">Ver en IMDb</a>'
                if isinstance(url, str) and url.startswith("http")
                else ""
            )

            reseñas_url = get_spanish_review_link(titulo, year)
            reseñas_html = (
                f'<a href="{reseñas_url}" target="_blank">Reseñas en español</a>'
                if reseñas_url else ""
            )

            genres_html = (
                f"<b>Géneros:</b> {genres}<br>"
                if isinstance(genres, str) and genres else ""
            )
            directors_html = (
                f"<b>Director(es):</b> {directors}<br>"
                if isinstance(directors, str) and directors else ""
            )

            card_html = f"""
<div class="movie-card movie-card-grid" style="
    border-color: {border_color};
    box-shadow:
        0 0 0 1px rgba(15,23,42,0.9),
        0 0 20px {glow_color};
">
{poster_html}
  <div class="movie-title">{titulo}{year_str}</div>
  <div class="movie-sub">
    {nota_str}<br>
    {imdb_str}<br>
    {tmdb_str}<br>
    {genres_html}
    {directors_html}
    <b>Streaming (CL):</b> {platforms_str}<br>
    {link_html}<br>
    {imdb_link_html}<br>
    <b>Reseñas:</b> {reseñas_html}
  </div>
</div>
"""
            cards_html.append(card_html)

        cards_html.append("</div>")
        gallery_html = "\n".join(cards_html)
        st.markdown(gallery_html, unsafe_allow_html=True)

        # ----------- NAV INFERIOR -----------
        # (Botones inferiores igual que arriba)
        # ...

    # ===================== MIS FAVORITAS =====================
    # (Tu código original de favoritas va aquí, sin cambios)
    # ...

# ============================================================
#                     TAB 2, 3 (Análisis, AFI)
# ============================================================
# (Mantén el código original de las pestañas Análisis y AFI tal cual lo tienes)
# ...

# ============================================================
#           ÓSCAR – helpers para Excel + unión catálogo
# ============================================================

@st.cache_data
def _find_col(df, candidates):
    cand = {c.lower() for c in candidates}
    for col in df.columns:
        if str(col).strip().lower() in cand:
            return col
    return None

@st.cache_data
def load_oscar_data_from_excel(path_xlsx="Oscar_Data_1927_today.xlsx"):
    try:
        raw = pd.read_excel(path_xlsx, engine="openpyxl")
    except Exception:
        return pd.DataFrame()

    raw_cols = list(raw.columns)
    col_year = _find_col(raw, {"year film", "film year", "year_film", "year", "year_of_film"})
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

    w = raw[col_winner].astype(str).str.strip().str.lower()
    df["IsWinner"] = w.isin(["true", "1", "yes", "winner", "won", "y", "si", "sí"])
    df["NormFilm"] = df["Film"].apply(normalize_title)

    return df

@st.cache_data
def attach_catalog_to_oscars(osc_df, catalog_df):
    if osc_df is None or osc_df.empty: return pd.DataFrame()
    out = osc_df.copy()
    if catalog_df is None or catalog_df.empty:
        out["InMyCatalog"] = False; out["MyRating"]=None; out["MyIMDb"]=None; out["CatalogURL"]=None
        return out

    cat = catalog_df.copy()
    if "NormTitle" not in cat.columns: cat["NormTitle"] = cat["Title"].apply(normalize_title)
    # YearInt ya se garantiza en load_data

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
    merged = merged.drop(columns=["NormTitle", "YearInt", "Your Rating", "IMDb Rating", "URL"], errors="ignore")
    return merged

def _build_people_chips(nominee_str: str) -> str:
    if not isinstance(nominee_str, str) or not nominee_str.strip(): return ""
    parts = re.split(r",| & | and ", nominee_str)
    chips = []
    for p in parts:
        name = p.strip()
        if not name: continue
        chips.append(
            f"<span style='background:rgba(148,163,184,0.18);border-radius:999px;padding:2px 9px;font-size:0.72rem;border:1px solid rgba(148,163,184,0.85);color:#e5e7eb;'>✦ {name}</span>"
        )
    if not chips: return ""
    return "<div style='margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;'>" + "".join(chips) + "</div>"

def _winner_badge_html():
    return "<span style='background:rgba(34,197,94,0.20);border-radius:999px;padding:2px 8px;font-size:0.7rem;border:1px solid #22c55e;color:#bbf7d0;'>WINNER 🏆</span>"

def _catalog_badge_html(my_rating):
    if pd.isna(my_rating): return ""
    return f"<span style='background:rgba(250,204,21,0.12);border-radius:999px;padding:3px 10px;font-size:0.72rem;border:1px solid rgba(250,204,21,0.85);color:#fef9c3;'>En mi catálogo · Mi nota: {float(my_rating):.1f}</span>"

def _build_oscar_card_html(row, categories_for_film=None, wins_for_film=None, noms_for_film=None, highlight_winner=False):
    title = row.get("Film", "Sin título")
    year = row.get("YearFilm", pd.NA)
    year_str = "" if pd.isna(year) else f" ({int(year)})"
    my_rating = row.get("MyRating")
    my_imdb = row.get("MyIMDb")
    in_cat = bool(row.get("InMyCatalog", False))
    imdb_url = row.get("CatalogURL")
    is_winner = highlight_winner or bool(row.get("IsWinner", False))

    tmdb_info = get_tmdb_basic_info(title, year)
    poster_url = tmdb_info.get("poster_url") if tmdb_info else None
    
    if is_winner: border="#22c55e"; glow="rgba(34,197,94,0.80)"
    else: border, glow = get_rating_colors(my_rating if pd.notna(my_rating) else my_imdb)

    if poster_url:
        poster_html = f"<div class='movie-poster-frame'><img src='{poster_url}' alt='{title}' class='movie-poster-img' /></div>"
    else:
        poster_html = "<div class='movie-poster-frame'><div class='movie-poster-placeholder'>Sin póster</div></div>"

    winner_badge = _winner_badge_html() if is_winner else ""
    catalog_badge = _catalog_badge_html(my_rating) if in_cat else ""
    
    # ... (Resto de la lógica de construcción HTML igual que tu original)
    
    return f"""
    <div class="movie-card movie-card-grid" style="border-color:{border}; box-shadow: 0 0 0 1px rgba(15,23,42,0.9), 0 0 26px {glow};">
      {poster_html}
      <div class="movie-title">{title}{year_str}</div>
      <div class="movie-sub">
        {winner_badge} {catalog_badge}
        <br>
        {_build_people_chips(row.get("Nominee", ""))}
      </div>
    </div>
    """

# ============================================================
#                     TAB 4: PREMIOS ÓSCAR
# ============================================================

with tab_awards:
    st.markdown("## 🏆 Premios de la Academia")

    # --- CORRECCIÓN CLAVE: Selección automática del Excel por defecto ---
    osc_source_options = ["No usar", "full_data.csv (Nominaciones)", "Oscar_Data_1927_today.xlsx"]
    osc_data_source = st.sidebar.radio(
        "Fuente de datos de Óscar (opcional)",
        osc_source_options,
        index=2  # <--- CORRECCIÓN: Índice 2 para seleccionar el Excel por defecto
    )

    osc_raw = pd.DataFrame()
    if osc_data_source == "Oscar_Data_1927_today.xlsx":
        osc_raw = load_oscar_data_from_excel("Oscar_Data_1927_today.xlsx")
    elif osc_data_source == "full_data.csv (Nominaciones)":
        # (Aquí iría tu lógica para CSV si la tuvieras, por ahora fallback a Excel o vacío)
        pass 

    if osc_raw.empty:
        st.info("Selecciona una fuente válida o asegúrate de que el archivo existe.")
    else:
        osc = attach_catalog_to_oscars(osc_raw, df)

        # ---------- Filtros principales ----------
        st.markdown("### 🧮 Filtros en premios")
        
        # (Tu lógica de filtros: Slider de año, multiselect de categoría, búsqueda texto)
        # ...
        
        # AÑOS
        years_sorted = sorted(osc["YearFilm"].dropna().unique().astype(int))
        if not years_sorted: st.stop()
        min_year, max_year = years_sorted[0], years_sorted[-1]
        
        year_selected = st.slider("Año de película", min_year, max_year, max_year)
        
        # FILTRADO
        ff = osc[osc["YearFilm"] == year_selected].copy()
        
        # GALERÍA
        st.markdown("### 🖼️ Galería visual por categoría")
        
        if ff.empty:
            st.info("No hay datos para este año.")
        else:
            # Iterar categorías y mostrar tarjetas
            cats = sorted(ff["Category"].unique())
            for cat in cats:
                st.markdown(f"**{cat}**")
                subset = ff[ff["Category"] == cat]
                
                cards = []
                for _, row in subset.iterrows():
                    cards.append(_build_oscar_card_html(row))
                
                # Renderizar grid
                st.markdown(f'<div class="movie-gallery-grid">{"".join(cards)}</div>', unsafe_allow_html=True)

# ============================================================
#                     TAB 5: ¿QUÉ VER HOY?
# ============================================================
# (Tu código original)
# ...

# ============================================================
#                     FOOTER
# ============================================================
st.markdown("---")
st.caption(f"Versión de la app: v{APP_VERSION} · Powered by Diego Leal")
