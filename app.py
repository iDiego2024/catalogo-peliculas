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
APP_VERSION = "1.1.6"  # <- súbela cuando publiques cambios

CHANGELOG = {
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

    # Ids de nominado (para rankings)
    nom_ids = col_or_empty("NomineeIds").astype(str)
    dff["NomineeIdsList"] = nom_ids.apply(
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

    # Crear una clave de enlace
    cat["JoinKey"] = cat["NormTitle"] + "_" + cat["YearInt"].astype(str)
    out["JoinKey"] = out["NormFilm"] + "_" + out["YearInt"].astype(str)

    # Crear un diccionario de lookup para el merge
    lookup = cat.set_index("JoinKey")[
        ["Your Rating", "IMDb Rating", "URL"]
    ].to_dict("index")

    def lookup_func(row):
        match = lookup.get(row["JoinKey"])
        if match:
            return {
                "InMyCatalog": True,
                "MyRating": match.get("Your Rating"),
                "MyIMDb": match.get("IMDb Rating"),
                "CatalogURL": match.get("URL"),
            }
        return {
            "InMyCatalog": False,
            "MyRating": None,
            "MyIMDb": None,
            "CatalogURL": None,
        }

    results = out.apply(lookup_func, axis=1, result_type="expand")

    out["InMyCatalog"] = results["InMyCatalog"]
    out["MyRating"] = results["MyRating"]
    out["MyIMDb"] = results["MyIMDb"]
    out["CatalogURL"] = results["CatalogURL"]

    return out.drop(columns=["JoinKey", "NormFilm"], errors="ignore")


@st.cache_data
def load_oscar_data_from_excel(path_xlsx="Oscar_Data_1927_today.xlsx"):
    """
    Carga robusta del Excel Oscar_Data_1927_today.xlsx.
    Intentamos adaptarnos a distintos nombres de columnas.
    Campos que se construyen:
    - FilmYear : año de la película (para el filtro principal)
    - Category : categoría del premio
    - Film : título de la película
    - Nominee : persona / entidad nominada
    - IsWinner : bool si ganó la categoría
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
            for c_raw in raw_cols:
                if str(c_raw).strip().lower() == c_norm:
                    return c_raw
        return None

    col_film_year = _find_col(raw, {"year film", "film year", "year_film", "year", "year_of_film"})
    col_award_year = _find_col(raw, {"award year", "ceremony year", "ceremony"}) # Lo usaremos como secundario si existe
    col_cat = _find_col(raw, {"category", "award", "award category"})
    col_film = _find_col(raw, {"film", "film title", "movie", "movie title"})
    col_nominee = _find_col(raw, {"nominee", "name", "primary nominee"})
    col_winner = _find_col(raw, {"winner", "won", "iswinner", "is_winner"})

    if not all([col_film_year, col_cat, col_film, col_nominee, col_winner]):
        # Si falta algo importante, devolvemos vacío para no romper la app
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
            is_winner = s.isin(
                ["true", "t", "1", "yes", "y", "winner", "ganador", "ganadora"]
            ) | (w == 1)
        is_winner = is_winner.fillna(False).astype(bool)

    df["IsWinner"] = is_winner

    # Usar AwardYear como CeremonyInt si existe, sino FilmYear
    df["CeremonyInt"] = df["FilmYear"]
    if col_award_year is not None:
        award_yr = pd.to_numeric(raw[col_award_year], errors="coerce").astype("Int64")
        df["CeremonyInt"] = award_yr.fillna(df["FilmYear"])

    # Normalizar para cruce
    df["NormFilm"] = df["Film"].apply(normalize_title)
    df["YearInt"] = df["FilmYear"].fillna(-1).astype(int) # Para que coincida con attach_catalog_to_full
    df = df[df["FilmYear"].notna()].reset_index(drop=True)

    return df.rename(columns={"Nominee": "PersonName"}) # Usar PersonName para consistencia

# ----------------- Funciones de visualización (HTML/CSS) -----------------

def _build_people_chips(nominee_str: str) -> str:
    """Convierte la lista de nominados en chips HTML."""
    if not nominee_str or not nominee_str.strip():
        return ""

    # Separador básico por ' and ', '&', ','
    parts = re.split(r",| & | and ", nominee_str)
    chips = []
    for p in parts:
        name = p.strip()
        if not name:
            continue
        # Escapar el texto para HTML y usar '·' en vez de '✦'
        safe_name = html.escape(name).replace("'", "’")
        chips.append(
            f"<span style='background:rgba(148,163,184,0.18);"
            f"border-radius:999px;padding:2px 9px;font-size:0.72rem;"
            f"text-transform:uppercase;letter-spacing:0.10em;"
            f"border:1px solid rgba(148,163,184,0.85);color:#e5e7eb;'>· {safe_name}</span>"
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

def _awards_summary_html(n_wins, n_noms):
    if n_wins == 0 and n_noms == 0:
        return ""
    wins_txt = f"{n_wins} Premio{'s' if n_wins != 1 else ''}"
    noms_txt = f"{n_noms} Nominación{'es' if n_noms != 1 else ''}"
    return (
        "<div style='margin-top:7px;display:flex;flex-wrap:wrap;gap:6px;'>"
        f"<span style='background:rgba(34,197,94,0.16);border-radius:999px;"
        f"padding:3px 10px;font-size:0.72rem;border:1px solid rgba(34,197,94,0.5);"
        f"color:#bbf7d0;'>🏆 {wins_txt}</span>"
        f"<span style='background:rgba(148,163,184,0.16);border-radius:999px;"
        f"padding:3px 10px;font-size:0.72rem;border:1px solid rgba(148,163,184,0.5);"
        f"color:#e5e7eb;'>✨ {noms_txt}</span>"
        "</div>"
    )

def fmt_rating(rating):
    return f"{float(rating):.1f}"

# Función unificada para la tarjeta de película (Catálogo o Óscar)
def build_movie_card_html(
    film_title,
    film_year,
    my_rating,
    my_imdb,
    imdb_url,
    tmdb_info,
    providers_info=None,
    is_winner_in_this_context=False,
    categories_for_film=None, # Solo para vista Óscar
    nominee_person_name=None, # Solo para vista Óscar
    wins_for_film=None,       # Solo para vista Óscar
    noms_for_film=None,        # Solo para vista Óscar
):
    """
    Genera el HTML de una tarjeta de película en la galería de catálogo o la galería de Óscar.
    La estructura está alineada con las tarjetas de tu catálogo.
    """
    import math
    import pandas as pd

    # --- TMDb info ---
    poster_url = None
    tmdb_rating = None
    if tmdb_info:
        poster_url = tmdb_info.get("poster_url")
        tmdb_rating = tmdb_info.get("vote_average")

    # --- Colores base según rating (mi nota > IMDb > TMDb) ---
    base_rating = None
    if pd.notna(my_rating):
        base_rating = my_rating
    elif pd.notna(my_imdb):
        base_rating = my_imdb
    elif tmdb_rating is not None and not (isinstance(tmdb_rating, float) and math.isnan(tmdb_rating)):
        base_rating = tmdb_rating

    border_color, glow_color = get_rating_colors(base_rating)

    # Si es ganadora, borde verde nuclear
    if is_winner_in_this_context:
        border_color = "#22c55e"
        glow_color = "rgba(34,197,94,0.80)"

    year_str = f" ({int(film_year)})" if pd.notna(film_year) else ""

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
    if providers_info:
        platforms = providers_info.get("platforms") or []
        platforms_str = ", ".join(platforms) if platforms else "Sin datos para Chile (CL)"
        streaming_link = providers_info.get("link")
    else:
        platforms_str = "Sin datos para Chile (CL)"
        streaming_link = None

    if streaming_link:
        streaming_html = (
            f"Streaming (CL): {platforms_str}<br>"
            f'<a href="{streaming_link}" target="_blank">Ver dónde verla</a>'
        )
    else:
        streaming_html = f"Streaming (CL): {platforms_str}"


    # --- Bloque de Ratings (Mi nota / IMDb / TMDb) ---
    my_rating_txt = (
        f"Mi nota: {fmt_rating(my_rating)}"
        if pd.notna(my_rating) else "Mi nota: —"
    )
    imdb_txt = (
        f"IMDb: {fmt_rating(my_imdb)}"
        if pd.notna(my_imdb) else "IMDb: N/D"
    )
    tmdb_txt = (
        f"TMDb: {fmt_rating(tmdb_rating)}"
        if tmdb_rating is not None else "TMDb: N/D"
    )

    ratings_block = f"""
    <div style='margin-top:10px;font-size:0.85rem;'>
        <b>{my_rating_txt}</b> · {imdb_txt} · {tmdb_txt}
    </div>
    """

    # --- Badges y Chips ---
    winner_badge = _winner_badge_html() if is_winner_in_this_context else ""
    catalog_badge = _catalog_badge_html(my_rating) if pd.notna(my_rating) else ""

    badges = [b for b in [winner_badge, catalog_badge] if b]
    badges_row = ""
    if badges:
        badges_row = (
            "<div style='margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;'>"
            + "".join(badges)
            + "</div>"
        )

    # Bloques específicos de Óscar
    oscars_summary = _awards_summary_html(wins_for_film, noms_for_film) if wins_for_film is not None and noms_for_film is not None else ""
    oscars_categories = ""
    if categories_for_film:
        cats_txt = " · ".join(sorted(categories_for_film))
        oscars_categories = (
            "<br><span style='font-size:0.78rem;color:#9ca3af;'>Categoría(s):</span>"
            f"<br><span style='font-size:0.82rem;font-weight:500;'>{cats_txt}</span>"
        )
    oscars_nominee_chips = _build_people_chips(nominee_person_name) if nominee_person_name else ""


    # --- Póster ---
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

    # Estructura principal
    html_card = f"""
    <div class="movie-card" style="
        border-color: {border_color};
        box-shadow: 
            0 0 0 1px rgba(15,23,42,0.9),
            0 0 22px {glow_color};
    ">
      {poster_html}
      <div class="movie-info">
        <h3 class="movie-title">{film_title}{year_str}</h3>
        
        {badges_row}
        {oscars_summary}
        {oscars_categories}

        {ratings_block}
        
        {oscars_nominee_chips}

        <div class="movie-links" style='margin-top:10px;'>
            {streaming_html}<br>
            {imdb_link_html}
            <span style='margin: 0 5px;'>·</span>
            {reseñas_html}
        </div>
      </div>
    </div>
    """
    return html_card

# ===================== Estilo CSS para la app =====================

def inject_css():
    st.markdown(
        f"""
        <style>
            /* General */
            .stApp {{
                background-color: #0f172a; /* Fondo azul oscuro/gris */
                color: #e2e8f0; /* Texto claro */
            }}
            
            /* Título y subtítulos */
            h1, h2, h3, h4 {{
                color: #f1f5f9; /* Títulos casi blancos */
            }}
            .st-emotion-cache-10trblm {{ /* Título principal */
                color: #94a3b8;
                font-size: 2.2rem;
                font-weight: 700;
            }}
            .stCaption {{ /* st.caption */
                color: #94a3b8;
                font-size: 0.85rem;
            }}
            .stMetric .st-emotion-cache-16sx60x {{ /* Valor en st.metric */
                color: #f1f5f9;
            }}
            .st-emotion-cache-116h52m {{ /* Icono y label de st.metric */
                color: #94a3b8;
            }}

            /* Sidebar */
            .st-emotion-cache-1c5vsmg {{ /* Sidebar background */
                background-color: #1e293b;
            }}
            .st-emotion-cache-vk3ypb h2 {{ /* Títulos en sidebar */
                color: #f1f5f9;
            }}

            /* Tarjeta de película (Galería) */
            .movie-gallery-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 20px;
                padding-top: 10px;
                padding-bottom: 20px;
            }}
            .movie-card {{
                display: flex;
                background-color: rgba(15,23,42,0.6);
                border: 2px solid;
                border-radius: 12px;
                overflow: hidden;
                transition: transform 0.2s, box-shadow 0.2s;
                min-height: 220px;
                max-width: 500px; /* Limitar el ancho en vista Catálogo */
            }}
            .movie-card-grid {{ /* Usado en Recomendaciones, más compacto */
                flex-direction: column;
                max-width: none;
                min-height: 380px;
            }}
            .movie-card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 0 0 1px #94a3b8, 0 8px 15px rgba(0, 0, 0, 0.3);
            }}
            .movie-poster-frame {{
                flex-shrink: 0;
                width: 150px;
                height: auto;
                background-color: #0f172a;
                border-right: 1px solid rgba(148,163,184,0.3);
                position: relative;
            }}
            .movie-card-grid .movie-poster-frame {{
                width: 100%;
                height: 225px; /* Altura fija para el póster en grilla */
                border-right: none;
                border-bottom: 1px solid rgba(148,163,184,0.3);
            }}
            .movie-poster-img {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                display: block;
            }}
            .movie-poster-placeholder {{
                width: 100%;
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                color: #94a3b8;
                font-size: 1.1rem;
            }}
            .film-reel-icon {{
                font-size: 3rem;
                margin-bottom: 5px;
            }}
            .movie-info {{
                padding: 15px;
                flex-grow: 1;
            }}
            .movie-card-grid .movie-info {{
                padding: 10px;
                flex-grow: 1;
            }}
            .movie-title {{
                font-size: 1.25rem;
                font-weight: 700;
                color: #f1f5f9;
                margin: 0 0 5px 0;
            }}
            .movie-card-grid .movie-title {{
                font-size: 1.1rem;
                margin-bottom: 3px;
                text-align: center;
            }}
            .movie-sub {{
                font-size: 0.9rem;
                color: #cbd5e1;
            }}
            .movie-card-grid .movie-sub {{
                text-align: center;
                margin-bottom: 10px;
            }}
            .movie-card a {{
                color: #38bdf8; /* Enlaces color turquesa/azul claro */
                text-decoration: none;
            }}
            .movie-card a:hover {{
                text-decoration: underline;
                color: #0ea5e9;
            }}
            
            /* Tarjeta AFI */
            .afi-list-item {{
                border: 1px solid #475569;
                background-color: #1e293b;
                border-radius: 8px;
                padding: 10px 15px;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}
            .afi-rank {{
                font-weight: 700;
                font-size: 1.1rem;
                color: #64748b;
                margin-right: 15px;
                width: 30px;
                text-align: right;
            }}
            .afi-info {{
                flex-grow: 1;
            }}
            .afi-title {{
                font-weight: 600;
                color: #f1f5f9;
            }}
            .afi-year {{
                font-size: 0.85rem;
                color: #94a3b8;
            }}
            .afi-status {{
                font-size: 0.85rem;
                padding: 4px 8px;
                border-radius: 4px;
                margin-left: 15px;
                font-weight: 500;
                flex-shrink: 0;
            }}
            .afi-in-catalog {{
                background-color: rgba(34, 197, 94, 0.2);
                color: #86efac;
                border: 1px solid #22c55e;
            }}
            .afi-not-in-catalog {{
                background-color: rgba(100, 116, 139, 0.1);
                color: #94a3b8;
                border: 1px solid #64748b;
            }}

            /* Ajustes de Streamlit */
            /* Quitar padding de st.columns */
            .st-emotion-cache-1vb64ze {{
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ===================== Lógica de la APP Streamlit =====================

def main():
    inject_css()

    # --- Archivo de catálogo ---
    uploaded_file = st.sidebar.file_uploader(
        "Sube tu archivo 'ratings.csv' de IMDb", type=["csv"]
    )
    df = None
    if uploaded_file is not None:
        try:
            df = load_data(uploaded_file)
            st.sidebar.success("Archivo cargado correctamente.")
        except Exception as e:
            st.sidebar.error(f"Error al cargar el CSV: {e}")
            df = None
    else:
        st.info("Sube tu archivo 'ratings.csv' de IMDb para comenzar.")
        return # No seguir si no hay datos

    # --- Archivo de Óscar (Opcional) ---
    osc_data_source = st.sidebar.radio(
        "Fuente de datos de Óscar (opcional)",
        ["No usar", "full_data.csv (Nominaciones)", "Oscar_Data_1927_today.xlsx"],
        index=0,
    )
    osc_df = None
    osc_file_name = None

    if osc_data_source == "full_data.csv (Nominaciones)":
        osc_file_name = "full_data.csv"
    elif osc_data_source == "Oscar_Data_1927_today.xlsx":
        osc_file_name = "Oscar_Data_1927_today.xlsx"

    if osc_file_name:
        try:
            if osc_file_name.endswith(".csv"):
                osc_df = load_full_data(osc_file_name)
            elif osc_file_name.endswith(".xlsx"):
                osc_df = load_oscar_data_from_excel(osc_file_name)

            if osc_df.empty:
                st.sidebar.warning(f"No se pudo cargar {osc_file_name} o estaba vacío.")
            else:
                osc_df = attach_catalog_to_full(osc_df, df)
                st.sidebar.success(f"Datos de Óscar cargados y cruzados con el catálogo.")

        except FileNotFoundError:
            st.sidebar.warning(
                f"No se encontró el archivo '{osc_file_name}' en el directorio de la app."
            )
        except Exception as e:
            st.sidebar.error(f"Error al cargar o procesar {osc_file_name}: {e}")
            osc_df = None

    # ----------------- Filtros en la barra lateral -----------------

    st.sidebar.header("⚙️ Filtros")

    # Rango de años
    min_year = int(df["Year"].min()) if df["Year"].notna().any() else 1900
    max_year = int(df["Year"].max()) if df["Year"].notna().any() else 2024
    if min_year > max_year:
        min_year, max_year = 1900, 2024

    year_range = st.sidebar.slider(
        "Rango de años (Year)",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        step=1,
    )

    # Rango de mi nota
    min_rating = 0.0
    max_rating = 10.0

    rating_range = st.sidebar.slider(
        "Mi nota (Your Rating)",
        min_value=min_rating,
        max_value=max_rating,
        value=(min_rating, max_rating),
        step=0.5,
        format="%.1f",
    )

    # Géneros
    all_genres = sorted(
        set(g for g_list in df["GenreList"] for g in g_list if g != "")
    )
    selected_genres = st.sidebar.multiselect(
        "Géneros (todas las seleccionadas deben estar presentes)",
        options=all_genres
    )

    # Directores
    all_directors = sorted(
        set(
            d.strip()
            for d in df["Directors"].dropna()
            if str(d).strip() != ""
            for d in str(d).split(",")
        )
    )
    selected_directors = st.sidebar.multiselect(
        "Directores",
        options=all_directors
    )

    # Ordenar
    order_by = st.sidebar.selectbox(
        "Ordenar por", ["Your Rating", "IMDb Rating", "Year", "Title", "Aleatorio"]
    )
    order_asc = st.sidebar.checkbox("Orden ascendente", value=False)


    # ---- Opciones de Galería ----
    st.sidebar.header("🖼️ Opciones de Galería")
    show_trailers = st.sidebar.checkbox("Mostrar tráilers (YouTube)", value=False)
    show_providers = st.sidebar.checkbox("Mostrar streaming (TMDb)", value=False)

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
            (filtered["Year"] >= year_range[0]) & (filtered["Year"] <= year_range[1])
        ]

    if "Your Rating" in filtered.columns:
        filtered = filtered[
            (filtered["Your Rating"] >= rating_range[0])
            & (filtered["Your Rating"] <= rating_range[1])
        ]

    if selected_genres:
        filtered = filtered[
            filtered["GenreList"].apply(lambda gl: all(g in gl for g in selected_genres))
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
        f"Filtros activos → Años: {year_range[0]}–{year_range[1]} · "
        f"Mi nota: {rating_range[0]:.1f}–{rating_range[1]:.1f} · "
        f"Géneros: {', '.join(selected_genres) if selected_genres else 'Todos'} · "
        f"Directores: {', '.join(selected_directors) if selected_directors else 'Todos'}"
    )

    # ---------- Búsqueda de texto ----------
    search_query = st.text_input(
        "Búsqueda por título, director o género (adicional a los filtros)",
        placeholder="Ej: 'Inception', 'Nolan', 'Sci-Fi'...",
        key="main_search",
    ).strip().lower()

    filtered_view = filtered.copy()
    if search_query:
        # La columna 'SearchText' ya está en minúsculas
        filtered_view = filtered_view[
            filtered_view["SearchText"].str.contains(search_query, na=False)
        ]

    # ---------- Ordenar resultados ----------
    if not filtered_view.empty:
        if order_by == "Aleatorio":
            filtered_view = filtered_view.sample(frac=1, random_state=42)
        elif order_by in filtered_view.columns:
            # Asegurar que la columna de ordenación exista y sea numérica si aplica
            if filtered_view[order_by].dtype not in ['float64', 'int64']:
                 # Si la columna no es numérica (ej: Title), ordenar por esa columna.
                 # Si es un rating, rellenar NaNs para que queden al final/inicio.
                 filtered_view[order_by] = pd.to_numeric(filtered_view[order_by], errors='coerce').fillna(-1 if order_asc else 11)

            filtered_view = filtered_view.sort_values(
                by=order_by, ascending=order_asc
            )


    # ----------------- TABS -----------------
    tab_catalog, tab_gallery, tab_analysis, tab_afi, tab_oscar, tab_recommend = st.tabs(
        [
            "Catálogo",
            "Galería visual",
            "Análisis",
            "AFI 100",
            "🏆 Premios Óscar",
            "¿Qué ver hoy?",
        ]
    )

    # ============================================================
    # TAB 1: CATÁLOGO
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
        if filtered_view.empty:
            st.info("No hay películas que coincidan con los filtros y la búsqueda.")
        else:
            cols_to_show = [
                c
                for c in [
                    "Title",
                    "Year",
                    "Your Rating",
                    "IMDb Rating",
                    "Genres",
                    "Directors",
                    "Date Rated",
                    "URL"
                ]
                if c in filtered_view.columns
            ]
            st.dataframe(filtered_view[cols_to_show], hide_index=True)


    # ============================================================
    # TAB 2: GALERÍA VISUAL
    # ============================================================
    @st.cache_data
    def get_tmdb_and_providers_for_title(title, year):
        """Función helper para cachear ambas llamadas API."""
        tmdb_info = get_tmdb_basic_info(title, year)
        providers_info = None
        if tmdb_info and show_providers:
            providers_info = get_tmdb_providers(tmdb_info.get("id"))
        return tmdb_info, providers_info

    with tab_gallery:
        st.markdown("## 🖼️ Galería visual")
        
        if filtered_view.empty:
            st.info("No hay películas para mostrar en la galería.")
            
        else:
            # Paginación
            page_size = st.slider("Películas por página", 5, 20, 10, step=5, key="gallery_page_size")
            total_pages = math.ceil(len(filtered_view) / page_size)
            
            col_g1, col_g2, col_g3 = st.columns([1, 2, 1])
            with col_g1:
                if "page" not in st.session_state:
                    st.session_state.page = 1
                if st.button("← Anterior", disabled=(st.session_state.page == 1)):
                    st.session_state.page -= 1
            with col_g2:
                st.markdown(
                    f"<div style='text-align:center; padding-top: 5px; color:#94a3b8;'>Página {st.session_state.page} de {total_pages}</div>",
                    unsafe_allow_html=True
                )
            with col_g3:
                if st.button("Siguiente →", disabled=(st.session_state.page == total_pages)):
                    st.session_state.page += 1

            start_idx = (st.session_state.page - 1) * page_size
            end_idx = start_idx + page_size
            page_data = filtered_view.iloc[start_idx:end_idx]

            gallery_html = ['<div class="movie-gallery-grid">']

            for _, row in page_data.iterrows():
                titulo = row.get("Title")
                year = row.get("Year")
                my_rating = row.get("Your Rating")
                imdb_rating = row.get("IMDb Rating")
                url = row.get("URL")

                tmdb_info, providers_info = get_tmdb_and_providers_for_title(titulo, year)

                card_html = build_movie_card_html(
                    film_title=titulo,
                    film_year=year,
                    my_rating=my_rating,
                    my_imdb=imdb_rating,
                    imdb_url=url,
                    tmdb_info=tmdb_info,
                    providers_info=providers_info,
                )
                gallery_html.append(card_html)
                
            gallery_html.append("</div>")
            st.markdown("\n".join(gallery_html), unsafe_allow_html=True)
            
            # Botones de navegación al final
            col_g4, col_g5, col_g6 = st.columns([1, 2, 1])
            with col_g4:
                if st.button("← Anterior", disabled=(st.session_state.page == 1), key="prev_bottom"):
                    st.session_state.page -= 1
            with col_g6:
                if st.button("Siguiente →", disabled=(st.session_state.page == total_pages), key="next_bottom"):
                    st.session_state.page += 1


    # ============================================================
    # TAB 3: ANÁLISIS
    # ============================================================
    with tab_analysis:
        st.markdown("## 📊 Análisis y tendencias (según filtros, sin búsqueda)")
        st.caption("Los gráficos usan sólo los filtros de la barra lateral (no la búsqueda de texto).")

        with st.expander("Ver análisis y tendencias", expanded=False):
            if filtered.empty:
                st.info("No hay datos bajo los filtros actuales para mostrar gráficos.")
            else:
                col_a, col_b = st.columns(2)

                # Películas por año
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

                # Distribución de mi nota
                with col_b:
                    st.markdown("**Distribución de mi nota (Your Rating)**")
                    if "Your Rating" in filtered.columns and filtered["Your Rating"].notna().any():
                        # Redondear para la distribución
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

                st.markdown("---")

                # Top géneros
                col_c, col_d = st.columns(2)
                with col_c:
                    st.markdown("**Top 10 Géneros**")
                    if "GenreList" in filtered.columns:
                        all_genres_flat = [g for gl in filtered["GenreList"] for g in gl]
                        if all_genres_flat:
                            top_genres = pd.Series(all_genres_flat).value_counts().head(10)
                            chart_data = top_genres.reset_index()
                            chart_data.columns = ["Genre", "Count"]
                            chart = (
                                alt.Chart(chart_data)
                                .mark_bar()
                                .encode(
                                    x=alt.X("Count"),
                                    y=alt.Y("Genre", sort="-x"),
                                    tooltip=["Genre", "Count"],
                                )
                                .properties(height=300)
                            )
                            st.altair_chart(chart, use_container_width=True)
                        else:
                            st.write("Sin datos de género.")

                # Películas infravaloradas (Mi nota >> IMDb)
                with col_d:
                    st.markdown("**Películas infravaloradas por IMDb**")
                    if "Your Rating" in filtered.columns and "IMDb Rating" in filtered.columns:
                        infra = filtered.copy()
                        infra = infra[
                            infra["Your Rating"].notna() & infra["IMDb Rating"].notna()
                        ]
                        infra["Diff"] = infra["Your Rating"] - infra["IMDb Rating"]
                        top_infra = infra.sort_values(by="Diff", ascending=False).head(10)

                        if not top_infra.empty:
                            st.dataframe(
                                top_infra[["Title", "Year", "Your Rating", "IMDb Rating", "Diff"]].reset_index(drop=True),
                                hide_index=True
                            )
                        else:
                            st.write("No hay datos para calcular la diferencia de notas.")
                    else:
                        st.write("Faltan las columnas 'Your Rating' o 'IMDb Rating'.")


                st.markdown("---")

                # Correlación y dispersión
                col_adv1, col_adv2 = st.columns(2)
                corr_df = filtered[
                    filtered["Your Rating"].notna() & filtered["IMDb Rating"].notna()
                ]
                corr = corr_df["Your Rating"].corr(corr_df["IMDb Rating"])
                if pd.notna(corr):
                    with col_adv1:
                        st.markdown("**Correlación (Mi nota vs IMDb)**")
                        st.metric("Coeficiente de correlación (Pearson)", f"{corr:.3f}")
                        st.caption(
                            "Correlación cercana a 1.0 significa que mi nota tiende a "
                            "coincidir con IMDb; "
                            "cercanos a 0 indican independencia; negativos, que tiendo a ir en contra."
                        )
                else:
                    with col_adv1:
                        st.write("No hay suficientes datos para calcular la correlación.")


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


                st.markdown("---")

                # Mapa de calor
                st.markdown("**Mapa de calor: mi nota media por género y década**")
                if "GenreList" in filtered.columns and "Your Rating" in filtered.columns:
                    tmp = filtered.copy()
                    tmp = tmp[tmp["Year"].notna() & tmp["Your Rating"].notna()]
                    tmp["Decade"] = (tmp["Year"] // 10 * 10).astype(int).astype(str)
                    
                    # Explode los géneros y calcula la media
                    tmp_exploded = tmp.explode("GenreList")
                    
                    if not tmp_exploded.empty:
                        heatmap_data = (
                            tmp_exploded.groupby(["Decade", "GenreList"])["Your Rating"]
                            .mean()
                            .reset_index(name="AvgRating")
                        )

                        # Filtro simple para que no colapse con demasiados géneros (ej. 15 máx)
                        top_genres_hm = (
                            heatmap_data.groupby("GenreList")["AvgRating"]
                            .mean()
                            .sort_values(ascending=False)
                            .head(15)
                            .index.tolist()
                        )
                        heatmap_data = heatmap_data[
                            heatmap_data["GenreList"].isin(top_genres_hm)
                        ]

                        chart = (
                            alt.Chart(heatmap_data)
                            .mark_rect()
                            .encode(
                                x=alt.X("Decade:O", sort="ascending"),
                                y=alt.Y("GenreList:O", title="Género", sort=top_genres_hm), # Ordenar por media
                                color=alt.Color(
                                    "AvgRating:Q",
                                    scale=alt.Scale(range="heatmap", domain=[5, 10]),
                                    legend=alt.Legend(title="Nota Media"),
                                ),
                                tooltip=["Decade", "GenreList", alt.Tooltip("AvgRating:Q", format=".2f")],
                            )
                            .properties(title="Nota media por Década y Género (Top 15 Géneros)")
                        )
                        st.altair_chart(chart, use_container_width=True)
                    else:
                        st.write("No hay suficientes datos de género y nota para el mapa de calor.")
                else:
                    st.write("Faltan las columnas 'GenreList' o 'Your Rating'.")



    # ============================================================
    # TAB 4: AFI 100
    # ============================================================
    with tab_afi:
        st.markdown(
            "## 🎬 AFI's 100 Years...100 Movies — 10th Anniversary Edition"
        )
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

            # Funcción de búsqueda robusta
            def find_match(afi_norm, year, df_full):
                # 1. Búsqueda exacta por título normalizado + año
                candidates = df_full[df_full["YearInt"] == year]
                m = candidates[candidates["NormTitle"] == afi_norm]
                if not m.empty:
                    return m.iloc[0]
                
                # 2. Búsqueda exacta por título normalizado sin año
                m = df_full[df_full["NormTitle"] == afi_norm]
                if not m.empty:
                    return m.iloc[0]
                
                # 3. Búsqueda parcial (contiene) por título normalizado + año
                m = candidates[candidates["NormTitle"].str.contains(afi_norm, regex=False, na=False)]
                if not m.empty:
                    return m.iloc[0]

                return None


            afi_df["InMyCatalog"] = False
            afi_df["MyRating"] = None
            afi_df["IMDbRating"] = None
            afi_df["CatalogURL"] = None
            afi_df["MatchTitle"] = None
            afi_df["MatchYear"] = None

            for i, row in afi_df.iterrows():
                match = find_match(row["NormTitle"], row["YearInt"], df)
                if match is not None:
                    afi_df.loc[i, "InMyCatalog"] = True
                    afi_df.loc[i, "MyRating"] = match.get("Your Rating")
                    afi_df.loc[i, "IMDbRating"] = match.get("IMDb Rating")
                    afi_df.loc[i, "CatalogURL"] = match.get("URL")
                    afi_df.loc[i, "MatchTitle"] = match.get("Title")
                    afi_df.loc[i, "MatchYear"] = match.get("Year")


            # Mostrar resultados
            total = len(afi_df)
            watched = afi_df["InMyCatalog"].sum()

            st.metric("Películas AFI 100 vistas", f"{watched} de {total}")

            afi_html = []
            for _, row in afi_df.iterrows():
                rank = row["Rank"]
                title = row["Title"]
                year = row["Year"]
                in_catalog = row["InMyCatalog"]
                my_rating = row["MyRating"]
                url = row["CatalogURL"]

                status_class = "afi-in-catalog" if in_catalog else "afi-not-in-catalog"
                status_text = "Vista"
                
                details = ""
                if in_catalog:
                    rating_str = f"Mi nota: {float(my_rating):.1f}" if pd.notna(my_rating) else "Mi nota: —"
                    link_html = f'<a href="{url}" target="_blank" style="color: inherit;">Ver en IMDb</a>' if url else ""
                    details = f"{rating_str} {link_html}"
                else:
                    status_text = "Pendiente"
                    details = ""


                afi_html.append(f"""
                <div class="afi-list-item">
                    <span class="afi-rank">#{rank}</span>
                    <div class="afi-info">
                        <div class="afi-title">{title}</div>
                        <div class="afi-year">{year}</div>
                    </div>
                    <div class="{status_class} afi-status">{status_text}</div>
                </div>
                """)

            st.markdown("".join(afi_html), unsafe_allow_html=True)


    # ============================================================
    # TAB 5: PREMIOS ÓSCAR
    # ============================================================
    with tab_oscar:
        st.markdown("## 🏆 Premios Óscar")
        
        if osc_df is None or osc_df.empty:
            st.warning(
                "Para usar esta pestaña, selecciona una fuente de datos de Óscar "
                "en la barra lateral (por ejemplo, 'full_data.csv')."
            )
        else:
            # 1. Filtros
            st.sidebar.header("⚙️ Filtros Óscar")
            
            # Selector de año de ceremonia
            min_c = int(osc_df["CeremonyInt"].min()) if osc_df["CeremonyInt"].notna().any() else 1927
            max_c = int(osc_df["CeremonyInt"].max()) if osc_df["CeremonyInt"].notna().any() else 2024
            
            # Usar el año de ceremonia más reciente por defecto
            default_year = st.session_state.get("osc_year_selected", max_c)
            if default_year not in osc_df["CeremonyInt"].unique():
                 default_year = max_c

            year_selected = st.sidebar.selectbox(
                "Año de Ceremonia (Award Year)",
                options=sorted(osc_df["CeremonyInt"].unique(), reverse=True),
                index=sorted(osc_df["CeremonyInt"].unique(), reverse=True).index(default_year)
            )
            st.session_state.osc_year_selected = year_selected

            # Filtro por categoría
            all_cats = sorted(osc_df[osc_df["CeremonyInt"] == year_selected]["Category"].unique())
            cats_selected = st.sidebar.multiselect(
                "Categorías",
                options=all_cats,
            )

            # Búsqueda de texto
            search_osc = st.text_input(
                "Búsqueda por Nominee, Film o Category",
                placeholder="Ej: 'BEST PICTURE', 'Chalamet', 'Nolan'…",
                key="osc_search_text",
            )
            
            # ---------- Filtrado para el año seleccionado ----------
            ff = osc_df[osc_df["CeremonyInt"] == year_selected].copy()
            ff = ff[ff["Film"].astype(str).str.strip() != ""] # Quitar filas sin película

            if cats_selected:
                ff = ff[ff["Category"].isin(cats_selected)]
                
            if search_osc:
                q = search_osc.strip().lower()
                mask = (
                    ff["Category"].str.lower().str.contains(q, na=False)
                    | ff["Nominee"].str.lower().str.contains(q, na=False) # Nominee para full_data
                    | ff["PersonName"].str.lower().str.contains(q, na=False) # PersonName para excel
                    | ff["Film"].str.lower().str.contains(q, na=False)
                )
                ff = ff[mask]

            # Unificar columna de nominado
            if "Nominee" in ff.columns:
                 ff["PersonName_Display"] = ff["Nominee"]
            elif "PersonName" in ff.columns:
                 ff["PersonName_Display"] = ff["PersonName"]
            else:
                 ff["PersonName_Display"] = ""


            # ---------- Métricas ----------
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Año seleccionado", int(year_selected))
            with col_m2:
                st.metric("Filas (nominaciones)", len(ff))
            with col_m3:
                st.metric("Categorías", ff["Category"].nunique())
            with col_m4:
                st.metric("Premios (Winner=True)", ff["IsWinner"].sum())

            st.markdown("---")


            # 2. Galería por Película Ganadora
            st.markdown("### 🎬 Galería de Películas y Ganadores")
            
            # Obtener las películas únicas en el resultado filtrado
            unique_films = ff[["Film", "YearInt"]].drop_duplicates()
            
            if unique_films.empty:
                st.info("No hay nominaciones que coincidan con los filtros para este año.")
            else:
                # Calcular info por película (ganadas/nominadas, categorías)
                film_stats = ff.groupby("Film").agg(
                    n_wins=("IsWinner", "sum"),
                    n_noms=("IsWinner", "size"),
                    categories=("Category", lambda x: list(x.unique()))
                ).reset_index()

                # Merge con unique_films para obtener el YearInt
                unique_films = unique_films.merge(film_stats, on="Film", how="left")

                # Ordenar: Ganadoras primero, luego por título
                unique_films["IsAnyWinner"] = unique_films["n_wins"] > 0
                unique_films = unique_films.sort_values(
                    by=["IsAnyWinner", "Film"], 
                    ascending=[False, True]
                )
                
                # Renderizar las tarjetas
                gallery_html_osc = ['<div class="movie-gallery-grid">']
                
                for _, row_film in unique_films.iterrows():
                    sel_film = row_film["Film"]
                    film_year_val = row_film["YearInt"]
                    n_wins = int(row_film["n_wins"])
                    n_noms = int(row_film["n_noms"])
                    categories_for_film = row_film["categories"]
                    
                    # Buscar la fila de la película en el catálogo (usando la lógica de cruce de attach_catalog_to_full)
                    # Tomar la primera fila (ya que MyRating/MyIMDb/URL deberían ser los mismos para todos los registros del mismo film/año)
                    film_rows = ff[ff["Film"] == sel_film]
                    
                    # Para el chip de Nominee, si la peli fue nominada, tomamos la lista de nominados de la fila con más nominados.
                    # Esto es un workaround para full_data.csv que puede tener múltiples Nominee/NomineeIds por película/categoría.
                    # Para Excel, usamos PersonName de la primera fila.
                    
                    nominee_person_name = film_rows["PersonName_Display"].iloc[0] if "PersonName_Display" in film_rows.columns and not film_rows.empty else None

                    in_my_catalog = bool(film_rows["InMyCatalog"].any())
                    my_rating = (
                        film_rows["MyRating"].dropna().iloc[0] 
                        if film_rows["MyRating"].notna().any() else None
                    )
                    my_imdb = (
                        film_rows["MyIMDb"].dropna().iloc[0] 
                        if film_rows["MyIMDb"].notna().any() else None
                    )
                    imdb_url = (
                        film_rows["CatalogURL"].dropna().iloc[0] 
                        if film_rows["CatalogURL"].notna().any() else None
                    )
                    
                    tmdb_info, providers_info = get_tmdb_and_providers_for_title(
                        sel_film, film_year_val
                    )

                    card_html_osc = build_movie_card_html(
                        film_title=sel_film,
                        film_year=film_year_val,
                        my_rating=my_rating,
                        my_imdb=my_imdb,
                        imdb_url=imdb_url,
                        tmdb_info=tmdb_info,
                        providers_info=providers_info,
                        is_winner_in_this_context=n_wins > 0,
                        categories_for_film=categories_for_film,
                        nominee_person_name=nominee_person_name,
                        wins_for_film=n_wins,
                        noms_for_film=n_noms,
                    )
                    gallery_html_osc.append(card_html_osc)
                
                gallery_html_osc.append("</div>")
                st.markdown("\n".join(gallery_html_osc), unsafe_allow_html=True)
                
                
            # 3. Ranking de nominados/películas
            st.markdown("---")
            st.markdown("### 🏆 Rankings por Ceremonia")
            st.caption(f"Rankings basados en el año de ceremonia seleccionado: {year_selected}")

            col_r1, col_r2 = st.columns(2)

            # Ranking por Película
            with col_r1:
                st.markdown("**Top Películas por Nominaciones**")
                film_rank = (
                    ff.groupby(["Film", "YearInt"])["Category"].size()
                    .reset_index(name="Nominaciones")
                    .sort_values(by="Nominaciones", ascending=False)
                    .head(10)
                )
                if not film_rank.empty:
                    st.dataframe(film_rank, hide_index=True)
                else:
                    st.info("Sin datos de nominaciones por película.")

            # Ranking por Persona/Entidad
            with col_r2:
                st.markdown("**Top Nominados (Personas/Entidades)**")
                
                # Se usa la columna PersonName_Display que unifica Nominee/PersonName
                if "PersonName_Display" in ff.columns:
                    nominee_rank = (
                        ff.groupby("PersonName_Display")["Category"].size()
                        .reset_index(name="Nominaciones")
                        .sort_values(by="Nominaciones", ascending=False)
                        .head(10)
                    )
                    if not nominee_rank.empty:
                        st.dataframe(nominee_rank, hide_index=True)
                    else:
                        st.info("Sin datos de nominados.")
                else:
                    st.info("Columna de nominado no disponible.")



    # ============================================================
    # TAB 6: ¿QUÉ VER HOY? (Aleatorio/Recomendación)
    # ============================================================
    with tab_recommend:
        st.markdown("## 🍿 ¿Qué ver hoy?")
        
        reco_type = st.radio(
            "Selecciona un modo de recomendación:",
            ["Película al azar (según filtros activos)", "Similar a una película vista"],
            index=0,
        )

        if filtered.empty:
             st.info("Aplica filtros en la barra lateral primero.")
             return
             
        if reco_type == "Película al azar (según filtros activos)":
            st.markdown("### 🎲 Película al azar")
            if st.button("Buscar película al azar", key="random_button"):
                if not filtered.empty:
                    random_row = filtered.sample(n=1).iloc[0]
                    titulo = random_row.get("Title")
                    year = random_row.get("Year")
                    my_rating = random_row.get("Your Rating")
                    imdb_rating = random_row.get("IMDb Rating")
                    url = random_row.get("URL")

                    st.markdown("#### 🎁 ¡Recomendación del día!")
                    tmdb_info, providers_info = get_tmdb_and_providers_for_title(titulo, year)

                    card_html = build_movie_card_html(
                        film_title=titulo,
                        film_year=year,
                        my_rating=my_rating,
                        my_imdb=imdb_rating,
                        imdb_url=url,
                        tmdb_info=tmdb_info,
                        providers_info=providers_info,
                    )
                    st.markdown(card_html, unsafe_allow_html=True)
                else:
                    st.warning("No hay películas que coincidan con los filtros activos.")

        elif reco_type == "Similar a una película vista":
            st.markdown("### 💡 Recomendaciones basadas en similitud de catálogo")
            
            # Selector de película semilla (solo las que tengo nota)
            rated_films = filtered[filtered["Your Rating"].notna()]
            if rated_films.empty:
                st.warning("Necesitas tener películas con 'Your Rating' para esta función.")
                return

            film_options = (
                rated_films["Title"]
                + " ("
                + rated_films["Year"].astype(float).astype(int).astype(str)
                + " · "
                + rated_films["Your Rating"].astype(float).round(1).astype(str)
                + ")"
            ).tolist()
            
            selected_option = st.selectbox(
                "Selecciona una película de tu catálogo como referencia:",
                options=[""] + film_options,
            )

            if selected_option:
                # Extraer título de la opción seleccionada
                title_match = re.search(r"^(.*)\s\(\d+\s·", selected_option)
                if title_match:
                    selected_title = title_match.group(1).strip()
                    seed_row = rated_films[rated_films["Title"] == selected_title].iloc[0]
                    
                    st.markdown(f"#### Película de referencia: {seed_row.get('Title')} ({int(seed_row.get('Year'))})")

                    # Generar recomendaciones
                    recs = recommend_from_catalog(df, seed_row, top_n=5)
                    
                    if recs.empty:
                        st.info("No se encontraron recomendaciones similares en tu catálogo.")
                    else:
                        st.markdown("#### 🌟 Películas similares en tu catálogo:")
                        cards_html = ['<div class="movie-gallery-grid">']

                        @st.cache_data
                        def get_tmdb_for_rec(t, y):
                             return get_tmdb_basic_info(t, y)

                        for _, r2 in recs.iterrows():
                            t2 = r2.get("Title", "Sin título")
                            y2 = r2.get("Year", None)
                            my2 = r2.get("Your Rating", None)
                            imdb2 = r2.get("IMDb Rating", None)
                            url2 = r2.get("URL", "")
                            
                            tmdb_info2 = get_tmdb_for_rec(t2, y2)
                            
                            # Usar la misma lógica de colores/estilos que la galería
                            base_rating2 = my2 if pd.notna(my2) else imdb2
                            border_color2, glow_color2 = get_rating_colors(base_rating2)
                            
                            y2_str = f" ({int(y2)})" if pd.notna(y2) else ""
                            poster_url2 = tmdb_info2.get("poster_url") if tmdb_info2 else None
                            
                            if isinstance(poster_url2, str) and poster_url2:
                                poster_html2 = (
                                    "<div class='movie-poster-frame'>"
                                    f"<img src='{poster_url2}' alt='{t2}' class='movie-poster-img' />"
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
                                
                            # Formato para ratings
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
  <div class="movie-info" style="padding: 10px;">
    <div class="movie-title" style="text-align:center; font-size: 1.1rem; margin-bottom: 3px;">{t2}{y2_str}</div>
    <div class="movie-sub" style="text-align:center;">
      <b>Mi nota:</b> {my2_str} · <b>IMDb:</b> {imdb2_str}<br>
      {imdb_link2}
    </div>
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


st.markdown(
    f"""
    <footer style="position: fixed; left: 0; bottom: 0; width: 100%; 
                   text-align: center; padding: 5px; background-color: #0f172a; 
                   color: #475569; font-size: 0.75rem; border-top: 1px solid #1e293b;">
        Mi catálogo de películas · v{APP_VERSION} · Powered by 
        <a href="https://github.com/diegoleal/streamlit-imdb-catalog" target="_blank" style="color: #64748b; text-decoration: none;">Diego Leal</a>
    </footer>
    """,
    unsafe_allow_html=True,
)

if __name__ == "__main__":
    main()
