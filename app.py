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
APP_VERSION = "1.1.7"  # <- Versión corregida

CHANGELOG = {
    "1.1.7": [
        "Mejora visual: Formato consistente (1 decimal) en el slider de 'Mi nota'.",
        "Corrección: Eliminado caracter de cierre incorrecto al final del archivo.",
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
        dff["YearInt"] = pd.Series([-1] * len(dff), index=idx, dtype=int)

    # Ceremonia (si no hay, usa YearInt)
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

    # IDs de candidatos (personas/entidades). Separados por ; o ,
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
if show_awards:
    st.sidebar.caption(
        "⚠ Consultar premios para muchas películas puede hacer la app más lenta en la primera carga."
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

    # Botón de descarga de resultados filtrados
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

        # Estado de la página actual
        if "gallery_current_page" not in st.session_state:
            st.session_state.gallery_current_page = 1

        # Ajustar si cambia el número de páginas
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

        st.caption(
            f"Mostrando pósters de tus películas filtradas: "
            f"{total_pelis} en total · {page_size} por página."
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

            if show_awards:
                awards = get_omdb_awards(titulo, year)
            else:
                awards = None

            if not show_awards:
                awards_text = "Premios no consultados (OMDb desactivado)."
            elif awards is None:
                awards_text = "Sin datos de premios (OMDb)."
            elif isinstance(awards, dict) and "error" in awards:
                awards_text = f"Error OMDb: {awards['error']}"
            else:
                base_parts = []
                if awards.get("oscars", 0):
                    base_parts.append(f"🏆 {awards['oscars']} Oscar(s)")
                if awards.get("emmys", 0):
                    base_parts.append(f"📺 {awards['emmys']} Emmy(s)")
                if awards.get("baftas", 0):
                    base_parts.append(f"🎭 {awards['baftas']} BAFTA(s)")
                if awards.get("golden_globes", 0):
                    base_parts.append(f"🌐 {awards['golden_globes']} Globo(s) de Oro")
                if awards.get("palme_dor", False):
                    base_parts.append("🌴 Palma de Oro")

                extra_parts = []
                if awards.get("oscars_nominated", 0):
                    extra_parts.append(f"🎬 Nominada a {awards['oscars_nominated']} Oscar(s)")
                if awards.get("total_wins", 0):
                    extra_parts.append(f"{awards['total_wins']} premios totales")
                if awards.get("total_nominations", 0):
                    extra_parts.append(f"{awards['total_nominations']} nominaciones totales")

                parts = base_parts + extra_parts
                if not parts:
                    awards_text = "Sin grandes premios detectados."
                else:
                    awards_text = " · ".join(parts)

                if awards.get("raw"):
                    awards_text += (
                        f"<br><span style='font-size:0.75rem;color:#9ca3af;'>"
                        f"OMDb: {awards['raw']}</span>"
                    )

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
    <b>Premios:</b> {awards_text}<br>
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
        st.markdown("")
        col_navb1, col_navb2, col_navb3 = st.columns([1, 2, 1])

        with col_navb1:
            prev_disabled_bottom = st.session_state.gallery_current_page <= 1
            if st.button("◀ Anterior", disabled=prev_disabled_bottom, key="gallery_prev_bottom"):
                if st.session_state.gallery_current_page > 1:
                    st.session_state.gallery_current_page -= 1

        with col_navb3:
            next_disabled_bottom = st.session_state.gallery_current_page >= num_pages
            if st.button("Siguiente ▶", disabled=next_disabled_bottom, key="gallery_next_bottom"):
                if st.session_state.gallery_current_page < num_pages:
                    st.session_state.gallery_current_page += 1

        with col_navb2:
            st.caption(
                f"Página {st.session_state.gallery_current_page} de {num_pages}"
            )

    # ===================== MIS FAVORITAS =====================

    st.markdown("---")
    st.markdown("## ⭐ Mis favoritas (nota ≥ 9) con filtros + búsqueda")

    with st.expander("Ver mis favoritas", expanded=False):
        if "Your Rating" in filtered_view.columns:
            fav = filtered_view[filtered_view["Your Rating"] >= 9].copy()
            if not fav.empty:
                fav = fav.sort_values(["Your Rating", "Year"], ascending=[False, True])
                fav = fav.head(12)

                for _, row in fav.iterrows():
                    titulo = row.get("Title", "Sin título")
                    year = row.get("Year", "")
                    nota = row.get("Your Rating", "")
                    imdb_rating = row.get("IMDb Rating", "")
                    genres = row.get("Genres", "")
                    directors = row.get("Directors", "")
                    url = row.get("URL", "")

                    border_color, glow_color = get_rating_colors(nota)

                    etiqueta = f"{titulo}"
                    if pd.notna(nota):
                        etiqueta = f"{int(nota)}/10 — {titulo}"
                    y_str = fmt_year(year)
                    if y_str:
                        etiqueta += f" ({y_str})"

                    st.markdown(
                        f"""
<div class="movie-card" style="
    border-color: {border_color};
    box-shadow:
        0 0 0 1px rgba(15,23,42,0.9),
        0 0 24px {glow_color};
    margin-bottom: 22px;
">
  <div class="movie-title">{etiqueta}</div>
  <div class="movie-sub">
""",
                        unsafe_allow_html=True,
                    )

                    col_img, col_info = st.columns([1, 3])

                    with col_img:
                        if show_posters_fav:
                            tmdb_info = get_tmdb_basic_info(titulo, year)
                            poster_url = tmdb_info.get("poster_url") if tmdb_info else None
                            if isinstance(poster_url, str) and poster_url:
                                try:
                                    st.image(poster_url)
                                except Exception:
                                    st.write("Sin póster")
                            else:
                                st.write("Sin póster")
                        else:
                            st.write("Póster desactivado (actívalo en la barra lateral).")

                    with col_info:
                        if isinstance(genres, str) and genres:
                            st.write(f"**Géneros:** {genres}")
                        if isinstance(directors, str) and directors:
                            st.write(f"**Director(es):** {directors}")
                        if pd.notna(imdb_rating):
                            st.write(f"**IMDb:** {fmt_rating(imdb_rating)}")
                        if isinstance(url, str) and url.startswith("http"):
                            st.write(f"[Ver en IMDb]({url})")
                        reseñas_url = get_spanish_review_link(titulo, year)
                        if reseñas_url:
                            st.write(f"[Reseñas en español]({reseñas_url})")

                        if show_trailers:
                            trailer_url = get_youtube_trailer_url(titulo, year)
                            if trailer_url:
                                st.video(trailer_url)

                    st.markdown(
                        "</div></div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.write("No hay películas con nota ≥ 9 bajo estos filtros + búsqueda.")
        else:
            st.write("No se encontró la columna 'Your Rating' en el CSV.")





            
# ============================================================
#                     TAB 2: ANÁLISIS
# ============================================================

with tab_analysis:
    st.markdown("## 📊 Análisis y tendencias (según filtros, sin búsqueda)")
    st.caption("Los gráficos usan sólo los filtros de la barra lateral (no la búsqueda de texto).")

    with st.expander("Ver análisis y tendencias", expanded=False):
        if filtered.empty:
            st.info("No hay datos bajo los filtros actuales para mostrar gráficos.")
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
                    by_year_display = by_year.copy()
                    by_year_display["Year"] = by_year_display["Year"].astype(int).astype(str)
                    by_year_display = by_year_display.set_index("Year")
                    st.line_chart(by_year_display)
                else:
                    st.write("Sin datos de año.")

            with col_b:
                st.markdown("**Distribución de mi nota (Your Rating)**")
                if "Your Rating" in filtered.columns and filtered["Your Rating"].notna().any():
                    ratings_counts = (
                        filtered["Your Rating"]
                        .round()
                        .value_counts()
                        .sort_index()
                        .reset_index()
                    )
                    ratings_counts.columns = ["Rating", "Count"]
                    ratings_counts["Rating"] = ratings_counts["Rating"].astype(int).astype(str)
                    ratings_counts = ratings_counts.set_index("Rating")
                    st.bar_chart(ratings_counts)
                else:
                    st.write("No hay notas mías disponibles.")

            col_c, col_d = st.columns(2)
            with col_c:
                st.markdown("**Top géneros (por número de películas)**")
                if "GenreList" in filtered.columns:
                    genres_exploded = filtered.explode("GenreList")
                    genres_exploded = genres_exploded[
                        genres_exploded["GenreList"].notna() &
                        (genres_exploded["GenreList"] != "")
                    ]
                    if not genres_exploded.empty:
                        top_genres = (
                            genres_exploded["GenreList"]
                            .value_counts()
                            .head(15)
                            .reset_index()
                        )
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
                        decade_imdb = (
                            tmp.groupby("Decade")["IMDb Rating"]
                            .mean()
                            .reset_index()
                            .sort_values("Decade")
                        )
                        decade_imdb["Decade"] = decade_imdb["Decade"].astype(str)
                        decade_imdb = decade_imdb.set_index("Decade")
                        st.line_chart(decade_imdb)
                    else:
                        st.write("No hay datos suficientes de año para calcular décadas.")
                else:
                    st.write("No hay IMDb Rating disponible.")

            st.markdown("### 🔬 Análisis avanzado (mi nota vs IMDb)")

            if (
                "Your Rating" in filtered.columns
                and "IMDb Rating" in filtered.columns
            ):
                corr_df = filtered[["Your Rating", "IMDb Rating"]].dropna()
            else:
                corr_df = pd.DataFrame()

            col_adv1, col_adv2 = st.columns(2)

            with col_adv1:
                if not corr_df.empty and len(corr_df) > 1:
                    corr = corr_df["Your Rating"].corr(corr_df["IMDb Rating"])
                    st.metric("Correlación Pearson (mi nota vs IMDb)", f"{corr:.2f}")
                else:
                    st.metric("Correlación Pearson (mi nota vs IMDb)", "N/A")
                st.write(
                    "Valores cercanos a 1 indican que suelo coincidir con IMDb; "
                    "cercanos a 0 indican independencia; negativos, que tiendo a ir en contra."
                )

            with col_adv2:
                st.markdown("**Dispersión: IMDb vs mi nota**")
                if not corr_df.empty:
                    scatter_chart = (
                        alt.Chart(corr_df.reset_index())
                        .mark_circle(size=60, opacity=0.6)
                        .encode(
                            x=alt.X("IMDb Rating:Q", scale=alt.Scale(domain=[0, 10])),
                            y=alt.Y("Your Rating:Q", scale=alt.Scale(domain=[0, 10])),
                            tooltip=["IMDb Rating", "Your Rating"],
                        )
                        .properties(height=300)
                    )
                    st.altair_chart(scatter_chart, use_container_width=True)
                else:
                    st.write("No hay datos suficientes para el gráfico de dispersión.")

            st.markdown("**Mapa de calor: mi nota media por género y década**")
            if "GenreList" in filtered.columns and "Your Rating" in filtered.columns:
                tmp = filtered.copy()
                tmp = tmp[tmp["Year"].notna() & tmp["Your Rating"].notna()]
                if not tmp.empty:
                    tmp["Decade"] = (tmp["Year"] // 10 * 10).astype(int).astype(str)
                    tmp_genres = tmp.explode("GenreList")
                    tmp_genres = tmp_genres[
                        tmp_genres["GenreList"].notna() &
                        (tmp_genres["GenreList"] != "")
                    ]
                    if not tmp_genres.empty:
                        heat_df = (
                            tmp_genres
                            .groupby(["GenreList", "Decade"])["Your Rating"]
                            .mean()
                            .reset_index()
                        )
                        heat_chart = (
                            alt.Chart(heat_df)
                            .mark_rect()
                            .encode(
                                x=alt.X("Decade:N", title="Década"),
                                y=alt.Y("GenreList:N", title="Género"),
                                color=alt.Color(
                                    "Your Rating:Q",
                                    title="Mi nota media",
                                    scale=alt.Scale(scheme="viridis"),
                                ),
                                tooltip=["GenreList", "Decade", "Your Rating"],
                            )
                            .properties(height=400)
                        )
                        st.altair_chart(heat_chart, use_container_width=True)
                    else:
                        st.write("No hay datos suficientes de géneros para el mapa de calor.")
                else:
                    st.write("No hay datos suficientes (año + mi nota) para el mapa de calor.")
            else:
                st.write("Faltan columnas necesarias para el mapa de calor.")

    # ===================== ANÁLISIS DE GUSTOS PERSONALES =====================

    st.markdown("---")
    st.markdown("## 🧠 Análisis de mis gustos personales")

    with st.expander("Ver análisis de mis gustos personales", expanded=False):
        if filtered.empty:
            st.info("No hay datos bajo los filtros actuales para analizar mis gustos.")
        else:
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                st.markdown("### 🎭 Géneros según mi gusto")

                if "GenreList" in filtered.columns and "Your Rating" in filtered.columns:
                    tmp = filtered.copy()
                    tmp = tmp[tmp["Your Rating"].notna()]
                    genres_exploded = tmp.explode("GenreList")
                    genres_exploded = genres_exploded[
                        genres_exploded["GenreList"].notna() &
                        (genres_exploded["GenreList"] != "")
                    ]
                    if not genres_exploded.empty:
                        genre_stats = (
                            genres_exploded
                            .groupby("GenreList")["Your Rating"]
                            .agg(["count", "mean", "std"])
                            .reset_index()
                        )
                        genre_stats = genre_stats[genre_stats["count"] >= 3]
                        if not genre_stats.empty:
                            genre_stats = genre_stats.sort_values("mean", ascending=False)
                            genre_stats["mean"] = genre_stats["mean"].round(2)
                            genre_stats["std"] = genre_stats["std"].fillna(0).round(2)

                            st.dataframe(
                                genre_stats.rename(
                                    columns={
                                        "GenreList": "Género",
                                        "count": "Nº pelis",
                                        "mean": "Mi nota media",
                                        "std": "Desviación (σ)"
                                    }
                                ),
                                hide_index=True,
                                use_container_width=True
                            )
                        else:
                            st.write("No hay géneros con suficientes películas para mostrar estadísticas.")
                    else:
                        st.write("No hay información suficiente de géneros para analizar mis gustos.")
                else:
                    st.write("Faltan columnas 'GenreList' o 'Your Rating' para este análisis.")

            with col_g2:
                st.markdown("### ⚖️ ¿Soy más exigente que IMDb?")

                if "Your Rating" in filtered.columns and "IMDb Rating" in filtered.columns:
                    diff_df = filtered[
                        filtered["Your Rating"].notna() &
                        filtered["IMDb Rating"].notna()
                    ].copy()
                    if not diff_df.empty:
                        diff_df["Diff"] = diff_df["Your Rating"] - diff_df["IMDb Rating"]

                        media_diff = diff_df["Diff"].mean()
                        st.metric(
                            "Diferencia media (Mi nota - IMDb)",
                            f"{media_diff:.2f}"
                        )

                        st.write(
                            "Valores positivos ⇒ suelo puntuar **más alto** que IMDb. "
                            "Valores negativos ⇒ suelo ser **más duro** que IMDb."
                        )

                        hist = (
                            diff_df["Diff"]
                            .round(1)
                            .value_counts()
                            .sort_index()
                            .reset_index()
                        )
                        hist.columns = ["Diff", "Count"]
                        hist["Diff"] = hist["Diff"].astype(str)
                        hist = hist.set_index("Diff")
                        st.bar_chart(hist)
                    else:
                        st.write("No hay suficientes películas con ambas notas (mía e IMDb) para comparar.")
                else:
                    st.write("Faltan columnas 'Your Rating' o 'IMDb Rating' para comparar con IMDb.")

            st.markdown("### ⏳ Evolución de mi exigencia con los años")

            if (
                "Year" in filtered.columns and
                "Your Rating" in filtered.columns and
                "IMDb Rating" in filtered.columns
            ):
                tmp = filtered.copy()
                tmp = tmp[
                    tmp["Year"].notna() &
                    tmp["Your Rating"].notna() &
                    tmp["IMDb Rating"].notna()
                ]
                if not tmp.empty:
                    by_year_gusto = (
                        tmp.groupby("Year")[["Your Rating", "IMDb Rating"]]
                        .mean()
                        .reset_index()
                        .sort_values("Year")
                    )
                    by_year_gusto["Diff"] = by_year_gusto["Your Rating"] - by_year_gusto["IMDb Rating"]

                    long_df = by_year_gusto.melt(
                        id_vars="Year",
                        value_vars=["Your Rating", "IMDb Rating"],
                        var_name="Fuente",
                        value_name="Rating"
                    )
                    long_df["Year"] = long_df["Year"].astype(int)

                    chart = (
                        alt.Chart(long_df)
                        .mark_line(point=True)
                        .encode(
                            x=alt.X("Year:O", title="Año"),
                            y=alt.Y("Rating:Q", title="Nota media"),
                            color=alt.Color("Fuente:N", title="Fuente"),
                            tooltip=["Year", "Fuente", "Rating"]
                        )
                        .properties(height=350)
                    )
                    st.altair_chart(chart, use_container_width=True)

                    tmp["Decade"] = (tmp["Year"] // 10 * 10).astype(int)
                    decade_diff = (
                        tmp.groupby("Decade")
                        .apply(lambda g: (g["Your Rating"] - g["IMDb Rating"]).mean())
                        .reset_index(name="Diff media")
                        .sort_values("Decade")
                    )
                    if not decade_diff.empty:
                        decade_diff["Decade"] = decade_diff["Decade"].astype(int)
                        st.write("**Diferencia media por década (Mi nota - IMDb):**")
                        st.dataframe(
                            decade_diff.rename(columns={"Decade": "Década"}),
                            hide_index=True,
                            use_container_width=True
                        )
                else:
                    st.write("No hay suficientes datos (año + mis notas + IMDb) para analizar mi evolución.")
            else:
                st.write("Faltan columnas 'Year', 'Your Rating' o 'IMDb Rating' para analizar mi evolución en el tiempo.")

    # ===================== PELÍCULAS INFRAVALORADAS =====================

    st.markdown("---")
    st.markdown("## 🔍 Descubrir películas que yo valoro más que IMDb")

    with st.expander("Películas que puntúo muy alto y IMDb no tanto", expanded=False):
        if "Your Rating" in df.columns and "IMDb Rating" in df.columns:
            diff_df = df[df["Your Rating"].notna() & df["IMDb Rating"].notna()].copy()
            if diff_df.empty:
                st.write("No hay suficientes películas con ambas notas (mía e IMDb) para este análisis.")
            else:
                # BUG FIX: antes restaba contra df["IMDb Rating"] en vez de diff_df["IMDb Rating"]
                diff_df["Diff"] = diff_df["Your Rating"] - diff_df["IMDb Rating"]
                infraval = diff_df[(diff_df["Your Rating"] >= 8) & (diff_df["Diff"] >= 1.0)]
                infraval = infraval.sort_values("Diff", ascending=False).head(30)

                if infraval.empty:
                    st.write("No se detectaron películas claramente infravaloradas con los criterios actuales.")
                else:
                    st.write(
                        "Mostrando películas donde mi nota supera al menos en 1 punto a la de IMDb "
                        "(y mi nota es ≥ 8)."
                    )
                    for _, row in infraval.iterrows():
                        titulo = row.get("Title", "Sin título")
                        year = row.get("Year", "")
                        my_rating = row.get("Your Rating")
                        imdb_rating = row.get("IMDb Rating")
                        genres = row.get("Genres", "")
                        url = row.get("URL", "")

                        diff_val = float(my_rating) - float(imdb_rating)
                        border_color, glow_color = get_rating_colors(my_rating)
                        reseñas_url = get_spanish_review_link(titulo, year)
                        reseñas_html = (
                            f'<a href="{reseñas_url}" target="_blank">Reseñas en español</a>'
                            if reseñas_url else ""
                        )

                        y_str = fmt_year(year)

                        st.markdown(
                            f"""
<div class="movie-card" style="
    border-color: {border_color};
    box-shadow:
        0 0 0 1px rgba(15,23,42,0.9),
        0 0 26px {glow_color};
    margin-bottom: 12px;
">
  <div class="movie-title">
    {titulo}{f" ({y_str})" if y_str else ""}
  </div>
  <div class="movie-sub">
    ⭐ Mi nota: {float(my_rating):.1f}<br>
    IMDb: {float(imdb_rating):.1f}<br>
    Diferencia (Mi − IMDb): {diff_val:.1f}<br>
    {("<b>Géneros:</b> " + genres + "<br>") if isinstance(genres, str) and genres else ""}
    {f'<a href="{url}" target="_blank">Ver en IMDb</a>' if isinstance(url, str) and url.startswith("http") else ""}<br>
    <b>Reseñas:</b> {reseñas_html}
  </div>
</div>
                            """,
                            unsafe_allow_html=True,
                        )
        else:
            st.write("Faltan columnas 'Your Rating' o 'IMDb Rating' para este análisis.")

    # ===================== ESTADÍSTICAS OMDb (OSCARS, PALMA...) =====================

    st.markdown("---")
    st.markdown("## 🏆 Estadísticas de premios (OMDb, por película)")

    with st.expander("Ver estadísticas de premios basadas en OMDb", expanded=False):
        if not show_awards:
            st.info("Activa 'Consultar premios en OMDb' en la barra lateral para usar esta sección.")
        elif filtered.empty:
            st.info("No hay datos bajo los filtros actuales.")
        else:
            if st.button("Calcular estadísticas de premios para las películas filtradas"):
                awards_stats_df = compute_awards_table(filtered[["Title", "Year"]])
                if awards_stats_df.empty:
                    st.write("No se pudieron obtener datos de premios para estas películas.")
                else:
                    st.markdown("### Películas con más Oscars / premios totales")
                    top_oscars = awards_stats_df.sort_values(
                        ["oscars", "total_wins", "total_nominations"],
                        ascending=[False, False, False]
                    )
                    show_top = top_oscars.head(30).copy()
                    show_top["Year"] = show_top["Year"].apply(fmt_year)
                    show_top = show_top.rename(
                        columns={
                            "Title": "Película",
                            "Year": "Año",
                            "oscars": "Oscars ganados",
                            "oscars_nominated": "Nominaciones al Oscar",
                            "total_wins": "Premios totales",
                            "total_nominations": "Nominaciones totales",
                            "palme_dor": "Palma de Oro",
                        }
                    )
                    st.dataframe(show_top.drop(columns=["raw"]), hide_index=True, use_container_width=True)

                    palme = awards_stats_df[awards_stats_df["palme_dor"]].copy()
                    if not palme.empty:
                        palme["Year"] = palme["Year"].apply(fmt_year)
                        palme = palme.rename(
                            columns={
                                "Title": "Película",
                                "Year": "Año",
                                "oscars": "Oscars ganados",
                                "total_wins": "Premios totales",
                            }
                        )
                        st.markdown("### Películas con Palma de Oro")
                        st.dataframe(
                            palme[["Película", "Año", "Oscars ganados", "Premios totales"]],
                            hide_index=True,
                            use_container_width=True
                        )
                    else:
                        st.write("Ninguna de las películas filtradas aparece con Palma de Oro en OMDb.")

                    merged = awards_stats_df.merge(
                        df[["Title", "Year", "Your Rating", "IMDb Rating"]],
                        on=["Title", "Year"],
                        how="left"
                    )

                    st.markdown("### 🎯 Cómo me llevo con los premios")

                    loved_palme = merged[
                        (merged["palme_dor"]) &
                        (merged["Your Rating"].notna()) &
                        (merged["Your Rating"] >= 8)
                    ].copy()

                    if not loved_palme.empty:
                        loved_palme["Year"] = loved_palme["Year"].apply(fmt_year)
                        loved_palme["Mi nota"] = loved_palme["Your Rating"].apply(fmt_rating)
                        loved_palme["IMDb"] = loved_palme["IMDb Rating"].apply(fmt_rating)
                        loved_palme = loved_palme.sort_values("Your Rating", ascending=False)
                        st.markdown("#### 🌴 Palmas de Oro que amo (mi nota ≥ 8)")
                        st.dataframe(
                            loved_palme[["Title", "Year", "Mi nota", "IMDb", "oscars", "total_wins"]].rename(
                                columns={
                                    "Title": "Película",
                                    "Year": "Año",
                                    "oscars": "Oscars ganados",
                                    "total_wins": "Premios totales",
                                }
                            ),
                            hide_index=True,
                            use_container_width=True
                        )

                    disliked_palme = merged[
                        (merged["palme_dor"]) &
                        (merged["Your Rating"].notna()) &
                        (merged["Your Rating"] <= 6)
                    ].copy()

                    if not disliked_palme.empty:
                        disliked_palme["Year"] = disliked_palme["Year"].apply(fmt_year)
                        disliked_palme["Mi nota"] = disliked_palme["Your Rating"].apply(fmt_rating)
                        disliked_palme["IMDb"] = disliked_palme["IMDb Rating"].apply(fmt_rating)
                        disliked_palme = disliked_palme.sort_values("Your Rating", ascending=True)
                        st.markdown("#### 🌴 Palmas de Oro que no me convencieron (mi nota ≤ 6)")
                        st.dataframe(
                            disliked_palme[["Title", "Year", "Mi nota", "IMDb", "oscars", "total_wins"]].rename(
                                columns={
                                    "Title": "Película",
                                    "Year": "Año",
                                    "oscars": "Oscars ganados",
                                    "total_wins": "Premios totales",
                                }
                            ),
                            hide_index=True,
                            use_container_width=True
                        )

                    loved_oscars = merged[
                        (merged["oscars"] >= 3) &
                        (merged["Your Rating"].notna()) &
                        (merged["Your Rating"] >= 8)
                    ].copy()

                    if not loved_oscars.empty:
                        loved_oscars["Year"] = loved_oscars["Year"].apply(fmt_year)
                        loved_oscars["Mi nota"] = loved_oscars["Your Rating"].apply(fmt_rating)
                        loved_oscars["IMDb"] = loved_oscars["IMDb Rating"].apply(fmt_rating)
                        loved_oscars = loved_oscars.sort_values(["oscars", "Your Rating"], ascending=[False, False])
                        st.markdown("#### 🏆 Grandes ganadoras de Oscar que amo (Oscars ≥ 3 y mi nota ≥ 8)")
                        st.dataframe(
                            loved_oscars[["Title", "Year", "Mi nota", "IMDb", "oscars", "total_wins"]].rename(
                                columns={
                                    "Title": "Película",
                                    "Year": "Año",
                                    "oscars": "Oscars ganados",
                                    "total_wins": "Premios totales",
                                }
                            ),
                            hide_index=True,
                            use_container_width=True
                        )

                    harsh_oscars = merged[
                        (merged["oscars"] >= 3) &
                        (merged["Your Rating"].notna()) &
                        (merged["Your Rating"] <= 6)
                    ].copy()

                    if not harsh_oscars.empty:
                        harsh_oscars["Year"] = harsh_oscars["Year"].apply(fmt_year)
                        harsh_oscars["Mi nota"] = harsh_oscars["Your Rating"].apply(fmt_rating)
                        harsh_oscars["IMDb"] = harsh_oscars["IMDb Rating"].apply(fmt_rating)
                        harsh_oscars = harsh_oscars.sort_values("Your Rating", ascending=True)
                        st.markdown("#### 🥊 Grandes ganadoras de Oscar donde fui duro (Oscars ≥ 3 y mi nota ≤ 6)")
                        st.dataframe(
                            harsh_oscars[["Title", "Year", "Mi nota", "IMDb", "oscars", "total_wins"]].rename(
                                columns={
                                    "Title": "Película",
                                    "Year": "Año",
                                    "oscars": "Oscars ganados",
                                    "total_wins": "Premios totales",
                                }
                            ),
                            hide_index=True,
                            use_container_width=True
                        )

                    st.markdown("### Texto original de premios (OMDb)")
                    raw_df = awards_stats_df[["Title", "Year", "raw"]].copy()
                    raw_df["Year"] = raw_df["Year"].apply(fmt_year)
                    raw_df = raw_df.rename(
                        columns={
                            "Title": "Película",
                            "Year": "Año",
                            "raw": "Premios (texto OMDb)"
                        }
                    )
                    st.dataframe(raw_df, hide_index=True, use_container_width=True)










                    
# ============================================================
#                     TAB 3: LISTA AFI
# ============================================================

with tab_afi:
    st.markdown("## 🎬 AFI's 100 Years...100 Movies — 10th Anniversary Edition")

    with st.expander("Ver mi progreso en la lista AFI 100", expanded=True):

        afi_df = pd.DataFrame(AFI_LIST)
        afi_df["NormTitle"] = afi_df["Title"].apply(normalize_title)
        afi_df["YearInt"] = afi_df["Year"]

        if "YearInt" not in df.columns:
            if "Year" in df.columns:
                df["YearInt"] = pd.to_numeric(df["Year"], errors="coerce").fillna(-1).astype(int)
            else:
                df["YearInt"] = -1
        if "NormTitle" not in df.columns:
            if "Title" in df.columns:
                df["NormTitle"] = df["Title"].apply(normalize_title)
            else:
                df["NormTitle"] = ""

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

            m = _try(
                candidates[candidates["NormTitle"].apply(
                    lambda t: afi_norm in t or t in afi_norm
                )]
            )
            if m is not None:
                return m

            candidates = df_full

            m = _try(candidates[candidates["NormTitle"] == afi_norm])
            if m is not None:
                return m

            m = _try(candidates[candidates["NormTitle"].str.contains(afi_norm, regex=False, na=False)])
            if m is not None:
                return m

            m = _try(
                candidates[candidates["NormTitle"].apply(
                    lambda t: afi_norm in t or t in afi_norm
                )]
            )
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

        st.write("Este progreso se calcula sobre todo mi catálogo de IMDb, no solo sobre los filtros actuales.")

        afi_table = afi_df.copy()
        afi_table["Vista"] = afi_table["Seen"].map({True: "✅", False: "—"})

        afi_table_display = afi_table[[
            "Rank", "Title", "Year", "Vista", "Your Rating", "IMDb Rating", "URL"
        ]].copy()

        afi_table_display["Year"] = afi_table_display["Year"].astype(int).astype(str)
        afi_table_display["Your Rating"] = afi_table_display["Your Rating"].apply(fmt_rating)
        afi_table_display["IMDb Rating"] = afi_table_display["IMDb Rating"].apply(fmt_rating)

        st.markdown("### Detalle del listado AFI (con mi avance)")

        st.dataframe(
            afi_table_display,
            hide_index=True,
            use_container_width=True
        )


# ============================================================
#           ÓSCAR – helpers para Excel + unión catálogo
# ============================================================

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

    Intentamos adaptarnos a distintos nombres de columnas. 
    Campos que se construyen:
      - YearFilm  : año de la película (para el filtro principal)
      - Category  : categoría del premio
      - Film      : título de la película
      - Nominee   : persona / entidad nominada
      - IsWinner  : bool si ganó la categoría
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
        # Si falta algo importante, devolvemos vacío para no romper la app
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


@st.cache_data
def attach_catalog_to_oscars(osc_df, catalog_df):
    """
    Enlaza el dataset de Óscar con tu catálogo IMDb por título normalizado + año.
    Añade:
      - InMyCatalog
      - MyRating
      - MyIMDb
      - CatalogURL
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


def _build_oscar_card_html(row, categories_for_film=None, wins_for_film=None,
                           noms_for_film=None, highlight_winner=False):
    """
    Genera el HTML de una card de película para la sección Óscar.
    - row: fila de óscar + catálogo ya unidas
    - categories_for_film: lista de categorías (para vista solo ganadoras)
    - wins_for_film / noms_for_film: int o None
    - highlight_winner: si se fuerza borde ganador aunque la fila no lo sea
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

# ============================================================
#                     TAB 5: ¿QUÉ VER HOY?
# ============================================================

with tab_what:
    st.markdown("## 🎲 ¿Qué ver hoy?")
    st.caption(
        "Basado en tu catálogo, tus notas, TMDb y (si está activa) la información de streaming."
    )

    if df.empty:
        st.info("No hay datos en el catálogo para sugerir nada.")
    else:
        st.markdown("### 🎯 Configuración rápida de la recomendación")

        colw1, colw2, colw3 = st.columns(3)

        with colw1:
            use_filtered = st.checkbox(
                "Usar filtros actuales",
                value=True,
                help="Si está marcado, la recomendación se hace sobre el subconjunto filtrado.",
            )

        with colw2:
            only_unrated = st.checkbox(
                "Sólo pendientes (sin nota mía)",
                value=False,
                help="Recomienda solo películas donde `Your Rating` está vacío.",
            )

        with colw3:
            min_imdb_pick = st.slider(
                "IMDb mínima para sugerencia",
                min_value=0.0,
                max_value=10.0,
                value=6.5,
                step=0.1,
            )

        pool = filtered_view if use_filtered and not filtered_view.empty else df.copy()

        if only_unrated and "Your Rating" in pool.columns:
            pool = pool[pool["Your Rating"].isna()].copy()

        if "IMDb Rating" in pool.columns:
            pool = pool[
                (pool["IMDb Rating"].isna())
                | (pool["IMDb Rating"] >= float(min_imdb_pick))
            ]

        if pool.empty:
            st.info(
                "No hay películas que cumplan las condiciones actuales para recomendar."
            )
        else:
            st.markdown("### 🎬 Sugerencia principal")

            if "what_pick" not in st.session_state:
                st.session_state.what_pick = None

            def _pick_random_movie():
                if pool.empty:
                    return None
                return pool.sample(1).iloc[0]

            col_btn1, col_btn2 = st.columns([1, 3])
            with col_btn1:
                if st.button("🎲 Sugerir película"):
                    st.session_state.what_pick = _pick_random_movie()

            if st.session_state.what_pick is None and not pool.empty:
                # Primera sugerencia automática
                st.session_state.what_pick = _pick_random_movie()

            row = st.session_state.what_pick

            if row is None:
                st.info("No se pudo generar una sugerencia con los criterios actuales.")
            else:
                titulo = row.get("Title", "Sin título")
                year = row.get("Year", None)
                my_rating = row.get("Your Rating", None)
                imdb_rating = row.get("IMDb Rating", None)
                genres = row.get("Genres", "")
                directors = row.get("Directors", "")
                url = row.get("URL", "")

                st.markdown(
                    f"#### 🎬 Recomendación de hoy: **{titulo}**"
                    f"{f' ({fmt_year(year)})' if pd.notna(year) else ''}"
                )

                col_info1, col_info2 = st.columns([1.1, 2])

                # Póster + trailer
                with col_info1:
                    tmdb_info = get_tmdb_basic_info(titulo, year)
                    tmdb_id = None
                    if tmdb_info:
                        poster_url = tmdb_info.get("poster_url")
                        tmdb_id = tmdb_info.get("id")
                        tmdb_vote = tmdb_info.get("vote_average")
                    else:
                        poster_url = None
                        tmdb_vote = None

                    if poster_url:
                        st.image(poster_url, use_column_width=True)
                    else:
                        st.write("Sin póster disponible.")

                    if show_trailers:
                        trailer_url = get_youtube_trailer_url(titulo, year)
                        if trailer_url:
                            st.video(trailer_url)

                # Detalle + streaming + enlaces
                with col_info2:
                    if isinstance(genres, str) and genres:
                        st.write(f"**Géneros:** {genres}")
                    if isinstance(directors, str) and directors:
                        st.write(f"**Director(es):** {directors}")

                    my_r_str = fmt_rating(my_rating) if pd.notna(my_rating) else "—"
                    imdb_r_str = fmt_rating(imdb_rating) if pd.notna(imdb_rating) else "—"
                    tmdb_r_str = (
                        fmt_rating(tmdb_vote) if tmdb_vote is not None else "N/A"
                    )

                    st.write(
                        f"**Mi nota:** {my_r_str} · "
                        f"**IMDb:** {imdb_r_str} · "
                        f"**TMDb:** {tmdb_r_str}"
                    )

                    if isinstance(url, str) and url.startswith("http"):
                        st.write(f"[Ver ficha en IMDb]({url})")

                    if tmdb_id is not None:
                        providers = get_tmdb_providers(tmdb_id, country="CL")
                    else:
                        providers = None

                    if providers is None:
                        st.write("**Streaming (CL):** sin datos de TMDb o sin API key.")
                    else:
                        platforms = providers.get("platforms") or []
                        link = providers.get("link")
                        if platforms:
                            st.write(
                                "**Streaming (CL):** "
                                + ", ".join(sorted(set(platforms)))
                            )
                        else:
                            st.write(
                                "**Streaming (CL):** sin plataformas listadas para Chile."
                            )
                        if link:
                            st.write(f"[Ver detalle de streaming en TMDb]({link})")

                    reseñas_url = get_spanish_review_link(titulo, year)
                    if reseñas_url:
                        st.write(f"[Buscar reseñas en español]({reseñas_url})")

                # --------- Recomendaciones similares dentro de tu catálogo ----------
                st.markdown("### ➕ Otras películas de tu catálogo que te podrían gustar")

                recs = recommend_from_catalog(df, row, top_n=6)
                if recs.empty:
                    st.info("No se pudieron generar recomendaciones similares en tu catálogo.")
                else:
                    cards_html = ['<div class="movie-gallery-grid">']

                    for _, r2 in recs.iterrows():
                        t2 = r2.get("Title", "Sin título")
                        y2 = r2.get("Year", None)
                        my2 = r2.get("Your Rating", None)
                        imdb2 = r2.get("IMDb Rating", None)
                        url2 = r2.get("URL", "")

                        base_rating2 = my2 if pd.notna(my2) else imdb2
                        border_color2, glow_color2 = get_rating_colors(base_rating2)

                        tmdb2 = get_tmdb_basic_info(t2, y2)
                        poster2 = tmdb2.get("poster_url") if tmdb2 else None

                        if poster2:
                            poster_html2 = f"""
<div class="movie-poster-frame">
  <img src="{poster2}" alt="{t2}" class="movie-poster-img">
</div>
"""
                        else:
                            poster_html2 = """
<div class="movie-poster-frame">
  <div class="movie-poster-placeholder">
    <div class="film-reel-icon">🎞️</div>
    <div class="film-reel-text">Sin póster</div>
  </div>
</div>
"""

                        y2_str = (
                            f" ({fmt_year(y2)})"
                            if y2 not in (None, -1) and not pd.isna(y2)
                            else ""
                        )
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
                        cards_html.append(card_html2)

                    cards_html.append("</div>")
                    gallery_recs_html = "\n".join(cards_html)
                    st.markdown(gallery_recs_html, unsafe_allow_html=True)

# ============================================================
#                     FOOTER / PIE DE PÁGINA
# ============================================================

st.markdown("---")
st.caption(f"Versión de la app: v{APP_VERSION} · Powered by Diego Leal")



