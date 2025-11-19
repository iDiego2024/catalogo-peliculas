import streamlit as st
import pandas as pd
import requests
import random
import altair as alt
import re
import math
from urllib.parse import quote_plus

# ===================== Versión y changelog =====================
APP_VERSION = "1.1.6"  # <- súbela cuando publiques cambios

CHANGELOG = {
    "1.1.6": [
        "Corrección del parser de premios BAFTA desde OMDb.",
        "Slider de 'Mi nota' ahora permite valores decimales con paso 0.5.",
    ],
    "1.1.5": [
        "Óscar: selector directo por año de ceremonia (sin rango).",
        "Óscar: se elimina el análisis por categoría y el top de entidades por categoría.",
        "Óscar: nueva galería visual por categoría con pósters para el año seleccionado.",
    ],
    "1.1.4": [
        "Análisis: se corrige el cálculo de diferencia (Mi nota − IMDb) en películas infravaloradas.",
        "Análisis: se ordenan correctamente las tablas y gráficos por infravaloradas/sobrevaloradas.",
        "Se renuevan textos de ayuda en la sección de análisis.",
    ],
    "1.1.3": [
        "Se añade pestaña de Análisis con histogramas y comparaciones con IMDb.",
        "Mejoras visuales en tablas y tarjetas.",
    ],
    "1.1.2": [
        "Se añaden tooltips explicativos en distintas secciones.",
        "Se mejora el layout responsivo en móviles.",
    ],
    "1.1.1": [
        "Se agrega soporte para proveedores de streaming por país (TMDb Watch Providers).",
        "Mejoras en la vista de galería con pósters y tooltips.",
    ],
    "1.1.0": [
        "Vista de galería visual con pósters usando TMDb.",
        "Integración básica con OMDb para texto de premios.",
        "Pequeñas optimizaciones de rendimiento con cache.",
    ],
    "1.0.0": [
        "Versión inicial de Mi Cine con carga de CSV, filtros básicos y tabla principal.",
    ],
}

# ===================== Configuración de la app =====================

st.set_page_config(
    page_title="Mi Cine",
    page_icon="🎬",
    layout="wide",
)

# ===================== Estilos y CSS =====================

CUSTOM_CSS = """
<style>
/* Estilos generales */
body {
    background-color: #0e1117;
    color: #fafafa;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

/* Títulos */
h1, h2, h3 {
    color: #ffffff;
}

/* Tarjetas */
.movie-card {
    background: #111827;
    border-radius: 12px;
    padding: 12px;
    border: 1px solid #1f2933;
    box-shadow: 0 4px 12px rgba(0,0,0,0.35);
    display: flex;
    gap: 12px;
}

/* Póster */
.movie-poster {
    width: 110px;
    border-radius: 8px;
    object-fit: cover;
}

/* Botones */
.stButton>button {
    background: linear-gradient(90deg, #1f2937, #111827);
    border-radius: 999px;
    border: 1px solid #374151;
    color: #f9fafb;
    padding: 0.5rem 1.25rem;
}
.stButton>button:hover {
    border-color: #60a5fa;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.7rem;
    margin-right: 4px;
    background: #1f2937;
    color: #e5e7eb;
}

/* Rating pill */
.rating-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    border-radius: 999px;
    font-size: 0.8rem;
    background: #0f172a;
    border: 1px solid #1e293b;
}

/* Tabla destacada */
.highlight-table table {
    border-radius: 12px;
    overflow: hidden;
}

/* Footer */
.footer {
    text-align: center;
    color: #9ca3af;
    font-size: 0.8rem;
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 1px solid #1f2937;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ===================== Configuración de APIs externas =====================

TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
OMDB_API_KEY = st.secrets.get("OMDB_API_KEY", None)

TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_MOVIE_DETAILS_URL = "https://api.themoviedb.org/3/movie/{movie_id}"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
TMDB_WATCH_PROVIDERS_URL = "https://api.themoviedb.org/3/movie/{movie_id}/watch/providers"
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
    {"Rank": 16, "Title": "Sunset Blvd.", "Year": 1950},
    {"Rank": 17, "Title": "The Graduate", "Year": 1967},
    {"Rank": 18, "Title": "The General", "Year": 1926},
    {"Rank": 19, "Title": "On the Waterfront", "Year": 1954},
    {"Rank": 20, "Title": "It's a Wonderful Life", "Year": 1946},
    {"Rank": 21, "Title": "Chinatown", "Year": 1974},
    {"Rank": 22, "Title": "Some Like It Hot", "Year": 1959},
    {"Rank": 23, "Title": "The Grapes of Wrath", "Year": 1940},
    {"Rank": 24, "Title": "E.T. The Extra-Terrestrial", "Year": 1982},
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
    {"Rank": 39, "Title": "Dr. Strangelove or: How I Learned to Stop Worrying and Love the Bomb", "Year": 1964},
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
    {"Rank": 54, "Title": "MASH", "Year": 1970},
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
    {"Rank": 75, "Title": "In the Heat of the Night", "Year": 1967},
    {"Rank": 76, "Title": "Forrest Gump", "Year": 1994},
    {"Rank": 77, "Title": "All the President's Men", "Year": 1976},
    {"Rank": 78, "Title": "Modern Times", "Year": 1936},
    {"Rank": 79, "Title": "The Wild Bunch", "Year": 1969},
    {"Rank": 80, "Title": "The Apartment", "Year": 1960},
    {"Rank": 81, "Title": "Spartacus", "Year": 1960},
    {"Rank": 82, "Title": "Sunrise: A Song of Two Humans", "Year": 1927},
    {"Rank": 83, "Title": "Titanic", "Year": 1997},
    {"Rank": 84, "Title": "Easy Rider", "Year": 1969},
    {"Rank": 85, "Title": "A Night at the Opera", "Year": 1935},
    {"Rank": 86, "Title": "Platoon", "Year": 1986},
    {"Rank": 87, "Title": "12 Angry Men", "Year": 1957},
    {"Rank": 88, "Title": "Bringing Up Baby", "Year": 1938},
    {"Rank": 89, "Title": "The Sixth Sense", "Year": 1999},
    {"Rank": 90, "Title": "Swing Time", "Year": 1936},
    {"Rank": 91, "Title": "Sophie's Choice", "Year": 1982},
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

AFI_DF = pd.DataFrame(AFI_LIST)

# ===================== Funciones auxiliares =====================

@st.cache_data
def load_data(csv_file: str) -> pd.DataFrame:
    df = pd.read_csv(csv_file)
    df["YearInt"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["Your Rating"] = pd.to_numeric(df["Your Rating"], errors="coerce")
    df["IMDb Rating"] = pd.to_numeric(df["IMDb Rating"], errors="coerce")
    df["Runtime (mins)"] = pd.to_numeric(df["Runtime (mins)"], errors="coerce")

    for col in ["Title", "Directors", "Genres", "URL"]:
        if col in df.columns:
            df[col] = df[col].fillna("")

    df["GenreList"] = df["Genres"].apply(
        lambda x: [g.strip() for g in str(x).split(",")] if pd.notna(x) else []
    )
    df["NormTitle"] = df["Title"].str.strip().str.lower()

    df["SearchText"] = (
        df["Title"].fillna("") + " " +
        df["Directors"].fillna("") + " " +
        df["Genres"].fillna("")
    ).str.lower()

    return df


@st.cache_data
def load_full_data(csv_file: str) -> pd.DataFrame:
    df = pd.read_csv(csv_file)
    return df


@st.cache_data
def load_oscars_data(csv_file: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(
            csv_file,
            on_bad_lines="skip",
        )
        if "Year" in df.columns:
            df["CeremonyYear"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
        if "Film" in df.columns:
            df["FilmNorm"] = df["Film"].astype(str).str.strip().str.lower()
        return df
    except Exception:
        return pd.DataFrame()


def normalize_title_for_match(title: str) -> str:
    if not isinstance(title, str):
        return ""
    t = title.strip().lower()
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t


@st.cache_data
def attach_catalog_to_full(df_full: pd.DataFrame, df_catalog: pd.DataFrame) -> pd.DataFrame:
    df_catalog = df_catalog.copy()
    df_catalog["NormTitle"] = df_catalog["Title"].str.strip().str.lower()
    df_full = df_full.copy()
    df_full["NormTitleFull"] = df_full["Title"].str.strip().str.lower()

    merged = df_full.merge(
        df_catalog[["NormTitle", "Your Rating"]],
        how="left",
        left_on="NormTitleFull",
        right_on="NormTitle",
        suffixes=("", "_catalog"),
    )
    merged["Your Rating"] = merged["Your Rating"].fillna(merged["Your Rating_catalog"])
    merged.drop(columns=["NormTitle_catalog"], inplace=True)
    return merged


@st.cache_data
def get_tmdb_basic_info(title: str, year: int = None):
    if not TMDB_API_KEY:
        return {"error": "TMDb API key not configured."}

    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "include_adult": "false",
        "language": "en-US",
    }
    if year:
        params["year"] = year

    try:
        resp = requests.get(TMDB_SEARCH_URL, params=params, timeout=10)
        if resp.status_code != 200:
            return {"error": f"TMDb error: {resp.status_code}"}
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return {"error": "No TMDb results"}

        movie = results[0]
        poster_url = None
        if movie.get("poster_path"):
            poster_url = f"{TMDB_IMAGE_BASE}{movie['poster_path']}"

        info = {
            "tmdb_id": movie.get("id"),
            "title": movie.get("title") or movie.get("name"),
            "overview": movie.get("overview"),
            "poster_url": poster_url,
            "vote_average": movie.get("vote_average"),
            "vote_count": movie.get("vote_count"),
            "release_date": movie.get("release_date"),
            "original_language": movie.get("original_language"),
        }
        return info

    except Exception as e:
        return {"error": str(e)}


@st.cache_data
def get_tmdb_providers(tmdb_id: int, country: str = "CL"):
    if not TMDB_API_KEY:
        return {"error": "TMDb API key not configured."}
    if not tmdb_id:
        return {"error": "Invalid TMDb ID"}

    url = TMDB_WATCH_PROVIDERS_URL.format(movie_id=tmdb_id)
    params = {"api_key": TMDB_API_KEY}

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return {"error": f"TMDb providers error: {resp.status_code}"}
        data = resp.json()
        results = data.get("results", {})
        country_data = results.get(country) or {}
        providers = {
            "flatrate": country_data.get("flatrate", []),
            "rent": country_data.get("rent", []),
            "buy": country_data.get("buy", []),
        }
        return providers
    except Exception as e:
        return {"error": str(e)}


@st.cache_data
def get_youtube_trailer_url(title: str, year: int = None):
    if not YOUTUBE_API_KEY:
        return None

    query = f"{title} trailer"
    if year:
        query += f" {year}"

    params = {
        "key": YOUTUBE_API_KEY,
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 1,
    }

    try:
        resp = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        items = data.get("items", [])
        if not items:
            return None
        video_id = items[0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={video_id}"
    except Exception:
        return None


@st.cache_data
def get_omdb_awards(title: str, year: int = None):
    if not OMDB_API_KEY:
        return {"error": "OMDb API key not configured."}

    def _do_request(params):
        try:
            resp = requests.get("https://www.omdbapi.com/", params=params, timeout=10)
            if resp.status_code != 200:
                return {"error": f"OMDb error: {resp.status_code}"}
            data = resp.json()
            return data
        except Exception as e:
            return {"error": str(e)}

    queries = []
    if year:
        queries.append(
            {
                "t": title,
                "y": year,
                "apikey": OMDB_API_KEY,
            }
        )
    queries.append(
        {
            "t": title,
            "apikey": OMDB_API_KEY,
        }
    )

    data = None
    last_error = None
    for q in queries:
        search = _do_request(q)
        if "error" not in search:
            data = search
            break
        else:
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

    if "palme d'or" in text_lower or "palme dor" in text_lower:
        palme_dor = True

    m_total_wins = re.search(r"(\d+)\s+wins?", text_lower)
    if m_total_wins:
        total_wins = int(m_total_wins.group(1))

    m_total_noms = re.search(r"(\d+)\s+nominations?", text_lower)
    if m_total_noms:
        total_nominations = int(m_total_noms.group(1))

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


def format_awards_summary(awards: dict) -> str:
    if not awards or not awards.get("raw"):
        return "Sin información de premios."

    parts = []

    if awards.get("oscars", 0) > 0:
        parts.append(f"🏆 {awards['oscars']} Óscar(s) ganados")
    if awards.get("oscars_nominated", 0) > 0:
        parts.append(f"🎬 {awards['oscars_nominated']} nominación(es) al Óscar")

    if awards.get("emmys", 0) > 0:
        parts.append(f"📺 {awards['emmys']} Emmy(s) ganados")

    if awards.get("baftas", 0) > 0:
        parts.append(f"🎭 {awards['baftas']} BAFTA(s) ganados")

    if awards.get("golden_globes", 0) > 0:
        parts.append(f"🌐 {awards['golden_globes']} Globo(s) de Oro ganados")

    if awards.get("palme_dor"):
        parts.append("🌴 Ganadora de la Palma de Oro")

    if awards.get("total_wins", 0) > 0 or awards.get("total_nominations", 0) > 0:
        extra = []
        if awards.get("total_wins", 0) > 0:
            extra.append(f"{awards['total_wins']} premios")
        if awards.get("total_nominations", 0) > 0:
            extra.append(f"{awards['total_nominations']} nominaciones")
        parts.append("⭐ " + ", ".join(extra))

    if not parts:
        return awards["raw"]

    return " · ".join(parts)


def compute_awards_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        title = row.get("Title")
        year = row.get("YearInt")
        awards_info = row.get("AwardsInfo", None)
        if not awards_info or not isinstance(awards_info, dict):
            continue
        summary = format_awards_summary(awards_info)
        rows.append(
            {
                "Title": title,
                "Year": year,
                "Awards": summary,
                "Raw": awards_info.get("raw", ""),
            }
        )
    return pd.DataFrame(rows)


def is_in_afi(title: str, year: int = None) -> bool:
    norm = normalize_title_for_match(title)
    for _, row in AFI_DF.iterrows():
        afi_title = normalize_title_for_match(row["Title"])
        if norm == afi_title:
            if year and not pd.isna(row["Year"]):
                if int(year) != int(row["Year"]):
                    continue
            return True
    return False


def get_afi_rank(title: str) -> int:
    norm = normalize_title_for_match(title)
    for _, row in AFI_DF.iterrows():
        afi_title = normalize_title_for_match(row["Title"])
        if norm == afi_title:
            return int(row["Rank"])
    return None


def recommend_from_catalog(df: pd.DataFrame, selected_title: str, top_n: int = 5):
    if df.empty:
        return pd.DataFrame()

    row = df[df["Title"] == selected_title]
    if row.empty:
        return pd.DataFrame()

    row = row.iloc[0]
    base_genres = set(row.get("GenreList", []))
    base_directors = set(
        d.strip() for d in str(row.get("Directors", "")).split(",") if d.strip()
    )
    base_year = row.get("YearInt", None)
    base_rating = row.get("Your Rating", None)

    candidates = df[df["Title"] != selected_title].copy()

    scores = []
    for _, r in candidates.iterrows():
        score = 0.0

        genres = set(r.get("GenreList", []))
        g_inter = base_genres.intersection(genres)
        score += 1.5 * len(g_inter)

        dirs = set(
            d.strip() for d in str(r.get("Directors", "")).split(",") if d.strip()
        )
        d_inter = base_directors.intersection(dirs)
        score += 2.0 * len(d_inter)

        y = r.get("YearInt", None)
        if base_year and y and not pd.isna(base_year) and not pd.isna(y):
            diff = abs(int(base_year) - int(y))
            score += max(0, 3 - diff / 10.0)

        rt = r.get("Your Rating", None)
        if base_rating and rt and not pd.isna(base_rating) and not pd.isna(rt):
            diff_r = abs(float(base_rating) - float(rt))
            score += max(0, 2 - diff_r)

        imdb = r.get("IMDb Rating", None)
        if imdb and not pd.isna(imdb) and float(imdb) >= 8.0:
            score += 0.5

        scores.append(score)

    candidates["RecScore"] = scores
    candidates = candidates[candidates["RecScore"] > 0]
    candidates = candidates.sort_values("RecScore", ascending=False)
    return candidates.head(top_n)


def color_imdb_rating(val):
    if pd.isna(val):
        return ""
    v = float(val)
    if v >= 8.5:
        return "background-color: #14532d; color: #e5e7eb;"
    elif v >= 8.0:
        return "background-color: #166534; color: #e5e7eb;"
    elif v >= 7.0:
        return "background-color: #1f2937; color: #e5e7eb;"
    else:
        return "background-color: #111827; color: #9ca3af;"


def color_your_rating(val):
    if pd.isna(val):
        return ""
    v = float(val)
    if v >= 9.0:
        return "background-color: #7c2d12; color: #fef2f2;"
    elif v >= 8.0:
        return "background-color: #b91c1c; color: #fef2f2;"
    elif v >= 7.0:
        return "background-color: #1f2937; color: #e5e7eb;"
    else:
        return "background-color: #111827; color: #9ca3af;"


def color_diff(val):
    if pd.isna(val):
        return ""
    v = float(val)
    if v >= 1.5:
        return "background-color: #064e3b; color: #ecfdf5;"
    elif v >= 1.0:
        return "background-color: #047857; color: #ecfdf5;"
    elif v <= -1.5:
        return "background-color: #7f1d1d; color: #fef2f2;"
    elif v <= -1.0:
        return "background-color: #b91c1c; color: #fef2f2;"
    else:
        return "background-color: #111827; color: #e5e7eb;"


def main():
    st.title("🎬 Mi Cine")
    st.caption("Tu base de datos cinematográfica personalizada, potenciada con APIs externas y análisis.")

    st.sidebar.title("Configuración y filtros")

    st.sidebar.markdown(
        f"**Versión de la app:** `v{APP_VERSION}`"
    )

    show_changelog = st.sidebar.checkbox("Mostrar changelog", value=False)
    if show_changelog:
        st.sidebar.markdown("### Changelog")
        for ver, items in CHANGELOG.items():
            with st.sidebar.expander(f"v{ver}", expanded=(ver == APP_VERSION)):
                for it in items:
                    st.write(f"- {it}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Carga de datos")

    uploaded_file = st.sidebar.file_uploader(
        "Sube tu CSV de Mi Cine (descargado desde IMDb)", type=["csv"]
    )

    default_csv = st.secrets.get("DEFAULT_CSV", None)
    df = None
    df_full = None

    if uploaded_file is not None:
        df = load_data(uploaded_file)
        df_full = load_full_data(uploaded_file)
    elif default_csv:
        try:
            df = load_data(default_csv)
            df_full = load_full_data(default_csv)
            st.sidebar.info("Usando CSV por defecto configurado en secrets.")
        except Exception:
            st.sidebar.error("No fue posible cargar el CSV por defecto.")
    else:
        st.sidebar.warning("Sube un CSV para comenzar.")

    oscars_csv = st.secrets.get("OSCARS_CSV", None)
    oscars_df = pd.DataFrame()
    if oscars_csv:
        oscars_df = load_oscars_data(oscars_csv)

    use_tmdb_gallery = st.sidebar.checkbox(
        "Usar galería visual con TMDb (pósters)", value=True
    )
    show_awards = st.sidebar.checkbox(
        "Mostrar resumen de premios (OMDb)", value=False
    )
    show_trailers = st.sidebar.checkbox(
        "Mostrar botón de tráiler (YouTube)", value=False
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filtros principales")

    if df is not None and not df.empty:
        if df["YearInt"].notna().any():
            min_year = int(df["YearInt"].min())
            max_year = int(df["YearInt"].max())
            year_range = st.sidebar.slider(
                "Rango de años", min_year, max_year, (min_year, max_year)
            )
        else:
            year_range = (0, 9999)

        if df["Your Rating"].notna().any():
            min_rating = float(df["Your Rating"].min())
            max_rating = float(df["Your Rating"].max())
            rating_range = st.sidebar.slider(
                "Mi nota (Your Rating)",
                min_value=0.0,
                max_value=10.0,
                value=(min_rating, max_rating),
                step=0.5,
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

        order_main = st.sidebar.selectbox(
            "Orden principal",
            options=[
                "Título (A-Z)",
                "Año (asc)",
                "Año (desc)",
                "Mi nota (desc)",
                "IMDb Rating (desc)",
            ],
        )

        search_text = st.sidebar.text_input(
            "Búsqueda de texto libre (título, director, género...)", ""
        ).strip().lower()

        st.sidebar.markdown("---")
        st.sidebar.markdown("### Opciones de análisis")

        enable_analysis = st.sidebar.checkbox(
            "Habilitar pestaña de análisis (infravaloradas/sobrevaloradas)", value=True
        )
        show_afi_badge = st.sidebar.checkbox(
            "Resaltar películas que están en la lista AFI 100", value=True
        )

        st.sidebar.markdown("---")
        st.sidebar.markdown("### Opciones avanzadas")

        advanced_show_oscars = st.sidebar.checkbox(
            "Mostrar pestaña de Óscar", value=True
        )

        st.sidebar.info(
            "Consejo: los filtros aplican sobre tu catálogo. La vista de galería usa TMDb para mostrar pósters, "
            "proveedores de streaming y, opcionalmente, premios OMDb y tráilers de YouTube."
        )
    else:
        year_range = (0, 9999)
        rating_range = (0.0, 10.0)
        selected_genres = []
        selected_directors = []
        order_main = "Título (A-Z)"
        search_text = ""
        enable_analysis = False
        show_afi_badge = False
        advanced_show_oscars = False

    if df is None or df.empty:
        st.warning("No hay datos para mostrar. Sube un CSV en la barra lateral.")
        st.markdown(
            """
            #### ¿Cómo obtener el CSV desde IMDb?
            1. Ve a tu lista de películas en IMDb (por ejemplo, tu watchlist o lista personalizada).
            2. En la parte inferior o superior, busca la opción **Export this list**.
            3. Descarga el archivo CSV.
            4. Súbelo aquí en la barra lateral.

            Este CSV se usará para generar la vista principal, la galería visual, análisis, etc.
            """
        )
        st.stop()

    filtered = df.copy()

    filtered = filtered[
        (filtered["YearInt"].fillna(0) >= year_range[0]) &
        (filtered["YearInt"].fillna(9999) <= year_range[1])
    ]

    filtered = filtered[
        (filtered["Your Rating"].fillna(0.0) >= rating_range[0]) &
        (filtered["Your Rating"].fillna(10.0) <= rating_range[1])
    ]

    if selected_genres:
        filtered = filtered[
            filtered["GenreList"].apply(
                lambda gl: all(g in gl for g in selected_genres)
            )
        ]

    if selected_directors:
        def _has_selected_director(dirs_str):
            dirs = [d.strip() for d in str(dirs_str).split(",") if d.strip()]
            return any(d in dirs for d in selected_directors)

        filtered = filtered[filtered["Directors"].apply(_has_selected_director)]

    if search_text:
        filtered = filtered[
            filtered["SearchText"].str.contains(search_text, case=False, na=False)
        ]

    if order_main == "Título (A-Z)":
        filtered = filtered.sort_values("Title")
    elif order_main == "Año (asc)":
        filtered = filtered.sort_values("YearInt", ascending=True)
    elif order_main == "Año (desc)":
        filtered = filtered.sort_values("YearInt", ascending=False)
    elif order_main == "Mi nota (desc)":
        filtered = filtered.sort_values("Your Rating", ascending=False)
    elif order_main == "IMDb Rating (desc)":
        filtered = filtered.sort_values("IMDb Rating", ascending=False)

    tabs = ["Tabla", "Galería"]
    if enable_analysis:
        tabs.append("Análisis")
    if advanced_show_oscars:
        tabs.append("Óscar")

    tab_objs = st.tabs(tabs)

    tab_table = tab_objs[0]
    tab_gallery = tab_objs[1]
    tab_analysis = None
    tab_oscars = None

    idx_tab = 2
    if enable_analysis:
        tab_analysis = tab_objs[idx_tab]
        idx_tab += 1
    if advanced_show_oscars and len(tab_objs) > idx_tab:
        tab_oscars = tab_objs[idx_tab]

    with tab_table:
        st.subheader("Tabla principal de tu catálogo")

        display_cols = ["Title", "Year", "Directors", "Genres", "Your Rating", "IMDb Rating", "Runtime (mins)"]
        display_cols = [c for c in display_cols if c in filtered.columns]

        df_display = filtered[display_cols].copy()

        if "Your Rating" in df_display.columns and "IMDb Rating" in df_display.columns:
            df_display["Diff (Yo - IMDb)"] = df_display["Your Rating"] - df_display["IMDb Rating"]

        styled = df_display.style

        if "IMDb Rating" in df_display.columns:
            styled = styled.applymap(color_imdb_rating, subset=["IMDb Rating"])
        if "Your Rating" in df_display.columns:
            styled = styled.applymap(color_your_rating, subset=["Your Rating"])
        if "Diff (Yo - IMDb)" in df_display.columns:
            styled = styled.applymap(color_diff, subset=["Diff (Yo - IMDb)"])

        st.dataframe(styled, use_container_width=True)

        st.markdown(
            """
            **Nota:**  
            - Mi nota: tu calificación personal.  
            - IMDb Rating: promedio global en IMDb.  
            - Diff (Yo - IMDb): positivo → tú la valoras más que el promedio; negativo → la valoras menos.
            """
        )

    with tab_gallery:
        st.subheader("Galería visual de películas")

        if filtered.empty:
            st.info("No hay películas que cumplan los filtros actuales.")
        else:
            page_size = 24
            num_pages = math.ceil(len(filtered) / page_size)
            if num_pages <= 0:
                num_pages = 1

            page = st.number_input(
                "Página", min_value=1, max_value=num_pages, value=1, step=1
            )
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_df = filtered.iloc[start_idx:end_idx]

            cols_per_row = 4
            rows = math.ceil(len(page_df) / cols_per_row)

            for r in range(rows):
                row_cols = st.columns(cols_per_row)
                for c in range(cols_per_row):
                    idx = r * cols_per_row + c
                    if idx >= len(page_df):
                        break
                    movie = page_df.iloc[idx]
                    with row_cols[c]:
                        render_movie_card(
                            movie,
                            show_afi_badge=show_afi_badge,
                            use_tmdb_gallery=use_tmdb_gallery,
                            show_awards=show_awards,
                            show_trailers=show_trailers,
                            df_catalog=df,
                        )

    if enable_analysis and tab_analysis is not None:
        with tab_analysis:
            render_analysis_tab(filtered)

    if advanced_show_oscars and tab_oscars is not None and not oscars_df.empty:
        with tab_oscars:
            render_oscars_tab(oscars_df, df)


def render_movie_card(
    movie_row,
    show_afi_badge: bool,
    use_tmdb_gallery: bool,
    show_awards: bool,
    show_trailers: bool,
    df_catalog: pd.DataFrame,
):
    title = movie_row.get("Title", "Sin título")
    year = movie_row.get("YearInt", None)
    directors = movie_row.get("Directors", "")
    genres = movie_row.get("Genres", "")
    your_rating = movie_row.get("Your Rating", None)
    imdb_rating = movie_row.get("IMDb Rating", None)
    url = movie_row.get("URL", "")

    afi_badge = ""
    afi_rank = None
    if show_afi_badge:
        if is_in_afi(title, year):
            afi_rank = get_afi_rank(title)
            afi_badge = f'<span class="badge">🎖️ AFI Top 100 #{afi_rank}</span>'

    poster_url = None
    overview = ""
    providers_info = None
    awards_summary = ""
    trailer_url = None

    if use_tmdb_gallery:
        info = get_tmdb_basic_info(title, year)
        if not info.get("error"):
            poster_url = info.get("poster_url")
            overview = info.get("overview") or ""
            if info.get("tmdb_id"):
                providers_info = get_tmdb_providers(info["tmdb_id"], country="CL")
            if show_trailers:
                trailer_url = get_youtube_trailer_url(title, year)

    awards_info = None
    if show_awards:
        awards_info = get_omdb_awards(title, year)
        if not awards_info.get("error") and awards_info.get("raw"):
            awards_summary = format_awards_summary(awards_info)

    fav_recs = recommend_from_catalog(df_catalog, title, top_n=3)
    has_recs = not fav_recs.empty

    st.markdown(
        f"""
        <div class="movie-card">
            <div>
        """,
        unsafe_allow_html=True,
    )

    if poster_url:
        st.markdown(
            f'<img src="{poster_url}" class="movie-poster" alt="Poster de {title}"/>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="
                width:110px;
                height:165px;
                border-radius:8px;
                background:#111827;
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:0.8rem;
                color:#6b7280;
                border:1px dashed #374151;
            ">
            Sin póster
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
            </div>
            <div style="flex:1; min-width:0;">
        """,
        unsafe_allow_html=True,
    )

    year_str = f" ({int(year)})" if year and not pd.isna(year) else ""
    st.markdown(
        f"<h3 style='margin-bottom:0.2rem;'>{title}{year_str}</h3>",
        unsafe_allow_html=True,
    )

    meta_line = []
    if directors:
        meta_line.append(f"👤 {directors}")
    if genres:
        meta_line.append(f"🎭 {genres}")
    if meta_line:
        st.markdown(
            f"<div style='color:#9ca3af; font-size:0.85rem; margin-bottom:0.3rem;'>"
            + " · ".join(meta_line)
            + "</div>",
            unsafe_allow_html=True,
        )

    rating_bits = []
    if your_rating and not pd.isna(your_rating):
        rating_bits.append(f"⭐ {your_rating:.1f} (mi nota)")
    if imdb_rating and not pd.isna(imdb_rating):
        rating_bits.append(f"🌍 {imdb_rating:.1f} IMDb")

    if rating_bits:
        st.markdown(
            "<div class='rating-pill'>" + " · ".join(rating_bits) + "</div>",
            unsafe_allow_html=True,
        )

    if show_afi_badge and afi_badge:
        st.markdown(
            f"<div style='margin-top:0.3rem;'>{afi_badge}</div>",
            unsafe_allow_html=True,
        )

    if overview:
        short_overview = overview
        if len(short_overview) > 260:
            short_overview = short_overview[:260].rsplit(" ", 1)[0] + "..."
        st.markdown(
            f"<p style='margin-top:0.5rem; font-size:0.9rem; color:#e5e7eb;'>{short_overview}</p>",
            unsafe_allow_html=True,
        )

    if providers_info and not providers_info.get("error"):
        prov_texts = []
        flatrate = providers_info.get("flatrate") or []
        rent = providers_info.get("rent") or []
        buy = providers_info.get("buy") or []

        if flatrate:
            names = ", ".join(p.get("provider_name", "") for p in flatrate)
            prov_texts.append(f"📺 Suscripción: {names}")
        if rent:
            names = ", ".join(p.get("provider_name", "") for p in rent)
            prov_texts.append(f"💰 Arriendo: {names}")
        if buy:
            names = ", ".join(p.get("provider_name", "") for p in buy)
            prov_texts.append(f"🛒 Compra: {names}")

        if prov_texts:
            st.markdown(
                "<div style='margin-top:0.4rem; font-size:0.8rem; color:#d1d5db;'>"
                + "<br>".join(prov_texts)
                + "</div>",
                unsafe_allow_html=True,
            )

    if awards_summary:
        st.markdown(
            f"<div style='margin-top:0.4rem; font-size:0.8rem; color:#e5e7eb;'>🏆 {awards_summary}</div>",
            unsafe_allow_html=True,
        )

    buttons_cols = st.columns(3)

    with buttons_cols[0]:
        if url and isinstance(url, str) and url.strip():
            imdb_link = url.strip()
            st.markdown(
                f"<a href='{imdb_link}' target='_blank'>🌐 Ver en IMDb</a>",
                unsafe_allow_html=True,
            )

    with buttons_cols[1]:
        if trailer_url:
            st.markdown(
                f"<a href='{trailer_url}' target='_blank'>▶️ Ver tráiler</a>",
                unsafe_allow_html=True,
            )

    with buttons_cols[2]:
        if has_recs:
            with st.expander("🎯 Recomendaciones similares de tu catálogo"):
                for _, rec in fav_recs.iterrows():
                    rec_title = rec.get("Title", "Sin título")
                    rec_year = rec.get("YearInt", None)
                    rec_rating = rec.get("Your Rating", None)
                    diff_rt = ""
                    if rec_rating and not pd.isna(rec_rating):
                        diff_rt = f" · ⭐ {rec_rating:.1f}"
                    if rec_year and not pd.isna(rec_year):
                        st.markdown(f"- **{rec_title}** ({int(rec_year)}){diff_rt}")
                    else:
                        st.markdown(f"- **{rec_title}**{diff_rt}")

    st.markdown(
        """
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_analysis_tab(filtered: pd.DataFrame):
    st.subheader("Análisis de tu catálogo")

    if filtered.empty:
        st.info("No hay datos suficientes para análisis con los filtros actuales.")
        return

    if "Your Rating" not in filtered.columns or "IMDb Rating" not in filtered.columns:
        st.warning("Para el análisis se requieren columnas 'Your Rating' y 'IMDb Rating'.")
        return

    df_an = filtered.copy()
    df_an["Your Rating"] = pd.to_numeric(df_an["Your Rating"], errors="coerce")
    df_an["IMDb Rating"] = pd.to_numeric(df_an["IMDb Rating"], errors="coerce")
    df_an["Diff (Yo - IMDb)"] = df_an["Your Rating"] - df_an["IMDb Rating"]

    st.markdown("### Distribución de mis notas")

    chart = (
        alt.Chart(df_an.dropna(subset=["Your Rating"]))
        .mark_bar()
        .encode(
            x=alt.X("Your Rating:Q", bin=alt.Bin(maxbins=20), title="Mi nota"),
            y=alt.Y("count()", title="Cantidad de películas"),
            tooltip=["count()"],
        )
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)

    st.markdown("### Películas que considero más infravaloradas (Yo >> IMDb)")

    infra = df_an.dropna(subset=["Diff (Yo - IMDb)"]).copy()
    infra = infra.sort_values("Diff (Yo - IMDb)", ascending=False)
    infra = infra[infra["Diff (Yo - IMDb)"] > 0]
    top_infra = infra.head(20)[
        ["Title", "Year", "Your Rating", "IMDb Rating", "Diff (Yo - IMDb)"]
    ]

    styled_infra = top_infra.style.applymap(color_diff, subset=["Diff (Yo - IMDb)"])
    st.markdown("Top 20 películas donde tu nota es mayor que la de IMDb:")
    st.dataframe(styled_infra, use_container_width=True)

    st.markdown("### Películas que considero más sobrevaloradas (Yo << IMDb)")

    sobre = df_an.dropna(subset=["Diff (Yo - IMDb)"]).copy()
    sobre = sobre.sort_values("Diff (Yo - IMDb)", ascending=True)
    sobre = sobre[sobre["Diff (Yo - IMDb)"] < 0]
    top_sobre = sobre.head(20)[
        ["Title", "Year", "Your Rating", "IMDb Rating", "Diff (Yo - IMDb)"]
    ]

    styled_sobre = top_sobre.style.applymap(color_diff, subset=["Diff (Yo - IMDb)"])
    st.markdown("Top 20 películas donde tu nota es menor que la de IMDb:")
    st.dataframe(styled_sobre, use_container_width=True)

    st.markdown(
        """
        **Interpretación rápida:**
        - Valores positivos grandes en *Diff (Yo - IMDb)* => películas infravaloradas por la masa (según tu criterio).
        - Valores negativos grandes => películas sobrevaloradas (para ti).
        """
    )


def render_oscars_tab(oscars_df: pd.DataFrame, catalog_df: pd.DataFrame):
    st.subheader("Óscar: conexión con tu catálogo")

    if oscars_df.empty:
        st.info("No hay datos de Óscar configurados.")
        return

    st.markdown(
        """
        Esta sección cruza tu catálogo con un dataset de premios de la Academia
        para explorar:
        - Películas de tu catálogo que han ganado o sido nominadas.
        - Resultados por año de la ceremonia.
        """
    )

    min_year = int(oscars_df["CeremonyYear"].min())
    max_year = int(oscars_df["CeremonyYear"].max())

    ceremony_year = st.slider(
        "Año de la ceremonia de los Óscar",
        min_value=min_year,
        max_value=max_year,
        value=min_year,
        step=1,
    )

    year_df = oscars_df[oscars_df["CeremonyYear"] == ceremony_year].copy()

    st.markdown(f"### Resultados de la ceremonia {ceremony_year}")

    cols = ["Category", "Nominee", "Film", "Winner"]
    year_display = year_df[cols].copy()
    st.dataframe(year_display, use_container_width=True)

    st.markdown("### Películas de tu catálogo presentes en estos Óscar")

    catalog_df = catalog_df.copy()
    catalog_df["NormTitle"] = catalog_df["Title"].str.strip().str.lower()
    year_df["FilmNorm"] = year_df["Film"].astype(str).str.strip().str.lower()

    merged = year_df.merge(
        catalog_df,
        how="inner",
        left_on="FilmNorm",
        right_on="NormTitle",
        suffixes=("_oscars", "_catalog"),
    )

    if merged.empty:
        st.info("Ninguna película de tu catálogo aparece en esta ceremonia.")
        return

    merged_display = merged[
        ["Film", "Year_catalog", "Category", "Winner", "Your Rating", "IMDb Rating"]
    ].copy()
    merged_display.rename(columns={"Year_catalog": "Year"}, inplace=True)

    styled = merged_display.style
    if "Your Rating" in merged_display.columns:
        styled = styled.applymap(color_your_rating, subset=["Your Rating"])
    if "IMDb Rating" in merged_display.columns:
        styled = styled.applymap(color_imdb_rating, subset=["IMDb Rating"])

    st.dataframe(styled, use_container_width=True)

    st.markdown(
        """
        **Notas:**
        - Se considera coincidencia exacta por título normalizado (ignorando mayúsculas y algunos signos).
        - Puede haber discrepancias si los títulos en IMDb y el dataset de Óscar difieren mucho.
        """
    )


if __name__ == "__main__":
    main()
    st.markdown(
        f"""
        <div class="footer">
        Versión de la app: v{APP_VERSION} · Powered by Diego Leal
        </div>
        """,
        unsafe_allow_html=True,
    )
