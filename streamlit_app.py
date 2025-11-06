import streamlit as st
import pandas as pd
import requests
import random
import altair as alt
import re

# ----------------- Configuración general -----------------

st.set_page_config(
    page_title="🎬 Catálogo de Películas",
    layout="wide"
)

st.title("🎥 Mi catálogo de películas (IMDb)")
st.write(
    "App basada en tu export de IMDb. "
    "Puedes filtrar por año, nota, géneros, director y usar una búsqueda sobre los resultados filtrados."
)

# ----------------- Config TMDb -----------------

TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"

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


def normalize_title(s: str) -> str:
    """Normaliza un título para compararlo (minúsculas, sin espacios ni signos)."""
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())


# ----------------- Funciones auxiliares -----------------


@st.cache_data
def load_data(file_path_or_buffer):
    df = pd.read_csv(file_path_or_buffer)

    # Tu nota
    if "Your Rating" in df.columns:
        df["Your Rating"] = pd.to_numeric(df["Your Rating"], errors="coerce")
    else:
        df["Your Rating"] = None

    # IMDb Rating
    if "IMDb Rating" in df.columns:
        df["IMDb Rating"] = pd.to_numeric(df["IMDb Rating"], errors="coerce")
    else:
        df["IMDb Rating"] = None

    # Year: extraer solo un año de 4 dígitos aunque venga sucio
    if "Year" in df.columns:
        df["Year"] = (
            df["Year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
            .astype(float)
        )
    else:
        df["Year"] = None

    # Genres
    if "Genres" not in df.columns:
        df["Genres"] = ""

    # Directors
    if "Directors" not in df.columns:
        df["Directors"] = ""

    # Lista de géneros para filtros
    df["Genres"] = df["Genres"].fillna("")
    df["GenreList"] = df["Genres"].apply(
        lambda x: [] if pd.isna(x) or x == "" else str(x).split(", ")
    )

    # Parsear fecha calificada
    if "Date Rated" in df.columns:
        df["Date Rated"] = pd.to_datetime(df["Date Rated"], errors="coerce").dt.date

    return df


def _coerce_year_for_tmdb(year):
    """Intenta convertir el año a int para TMDb, devolviendo None si no es válido."""
    if year is None or pd.isna(year):
        return None
    try:
        return int(float(year))
    except Exception:
        return None


@st.cache_data
def get_poster_url(title, year=None):
    """Devuelve solo la URL del póster de TMDb."""
    if TMDB_API_KEY is None:
        return None

    if not title or pd.isna(title):
        return None

    title = str(title).strip()
    year_int = _coerce_year_for_tmdb(year)

    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
    }
    if year_int is not None:
        params["year"] = year_int

    try:
        r = requests.get(TMDB_SEARCH_URL, params=params, timeout=2)
        if r.status_code != 200:
            return None

        data = r.json()
        results = data.get("results", [])
               if not results:
            return None

        poster_path = results[0].get("poster_path")
        if not poster_path:
            return None

        return f"{TMDB_IMAGE_BASE}{poster_path}"
    except Exception:
        return None


@st.cache_data
def get_tmdb_vote_average(title, year=None):
    """Devuelve el voto medio de TMDb (vote_average) para un título."""
    if TMDB_API_KEY is None:
        return None

    if not title or pd.isna(title):
        return None

    title = str(title).strip()
    year_int = _coerce_year_for_tmdb(year)

    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
    }
    if year_int is not None:
        params["year"] = year_int

    try:
        r = requests.get(TMDB_SEARCH_URL, params=params, timeout=2)
        if r.status_code != 200:
            return None

        data = r.json()
        results = data.get("results", [])
        if not results:
            return None

        return results[0].get("vote_average")
    except Exception:
        return None


@st.cache_data
def get_omdb_awards(title, year=None):
    """
    Consulta OMDb y devuelve info de premios importantes.
    - raw: texto original del campo Awards
    - oscars: nº de Oscars ganados
    - emmys: nº de Emmys ganados
    - baftas: nº de BAFTA ganados (aprox)
    - golden_globes: nº de Globos de Oro ganados (aprox)
    - palme_dor: True si detecta Palma de Oro en el texto
    - error: texto de error de OMDb si lo hay
    """
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

    # 1) intento exacto por título / título sin paréntesis
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

    # 2) búsqueda general si lo anterior falla
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
        }

    text_lower = awards_str.lower()

    oscars = 0
    emmys = 0
    baftas = 0
    golden_globes = 0
    palme_dor = False

    # Oscars
    m_osc = re.search(r"won\s+(\d+)\s+oscars?", text_lower)
    if not m_osc:
        m_osc = re.search(r"won\s+(\d+)\s+oscar\b", text_lower)
    if m_osc:
        oscars = int(m_osc.group(1))

    # Emmys
    for pat in [
        r"won\s+(\d+)\s+primetime\s+emmys?",
        r"won\s+(\d+)\s+emmys?",
        r"won\s+(\d+)\s+emmy\b",
    ]:
        m = re.search(pat, text_lower)
        if m:
            emmys = int(m.group(1))
            break

    # BAFTA
    m_bafta = re.search(r"won\s+(\d+)[^\.]*bafta", text_lower)
    if m_bafta:
        baftas = int(m_bafta.group(1))
    elif "bafta" in text_lower:
        baftas = 1

    # Globos de Oro
    m_globe = re.search(r"won\s+(\d+)[^\.]*golden\s+globes?", text_lower)
    if not m_globe:
        m_globe = re.search(r"won\s+(\d+)[^\.]*golden\s+globe\b", text_lower)
    if m_globe:
        golden_globes = int(m_globe.group(1))
    elif "golden globe" in text_lower:
        golden_globes = 1

    # Palma de Oro
    if re.search(r"palme\s+d['’]or", text_lower):
        palme_dor = True

    return {
        "raw": awards_str,
        "oscars": oscars,
        "emmys": emmys,
        "baftas": baftas,
        "golden_globes": golden_globes,
        "palme_dor": palme_dor,
    }


@st.cache_data
def get_streaming_availability(title, year=None, country="CL"):
    """
    Devuelve info de streaming para un título usando TMDb (pensado para Chile - CL).
    - Busca la película (search/movie) para obtener movie_id.
    - Luego consulta /movie/{movie_id}/watch/providers.
    Devuelve:
      {
        "platforms": [lista de nombres de plataformas],
        "link": URL a la página de TMDb con opciones de streaming en ese país
      }
    """
    if TMDB_API_KEY is None:
        return None

    if not title or pd.isna(title):
        return None

    title = str(title).strip()
    year_int = _coerce_year_for_tmdb(year)

    # 1) Buscar la película para obtener el ID
    try:
        search_params = {
            "api_key": TMDB_API_KEY,
            "query": title,
        }
        if year_int is not None:
            search_params["year"] = year_int

        r = requests.get(TMDB_SEARCH_URL, params=search_params, timeout=4)
        if r.status_code != 200:
            return None

        data = r.json()
        results = data.get("results", [])
        if not results:
            return None

        movie_id = results[0].get("id")
        if not movie_id:
            return None
    except Exception:
        return None

    # 2) Consultar proveedores de streaming para ese movie_id
    try:
        providers_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers"
        r2 = requests.get(
            providers_url,
            params={"api_key": TMDB_API_KEY},
            timeout=4
        )
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


def get_rating_colors(rating):
    """
    Devuelve (border_color, glow_color) según la nota.
    Usa tu nota si está, si no, IMDb.
    """
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


# ----------------- Carga de datos -----------------

st.sidebar.header("📂 Datos")

uploaded = st.sidebar.file_uploader(
    "Sube tu CSV de IMDb (si no, usaré peliculas.csv del repo)",
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
    df["YearInt"] = df["Year"].fillna(-1).astype(int)
else:
    df["YearInt"] = -1

# ----------------- Tema oscuro fijo + CSS -----------------

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
        font-size: 1.9rem !important;
        background: linear-gradient(90deg, var(--accent), var(--accent-alt));
        -webkit-background-clip: text;
        color: transparent;
        margin-bottom: 0.1rem;
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
    "Mostrar pósters TMDb en favoritas (nota ≥ 9)",
    value=True
)
show_gallery = st.sidebar.checkbox(
    "Mostrar galería de pósters para resultados filtrados",
    value=True
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
    min_rating = int(df["Your Rating"].min())
    max_rating = int(df["Your Rating"].max())
    rating_range = st.sidebar.slider(
        "Tu nota (Your Rating)", min_rating, max_rating, (min_rating, max_rating)
    )
else:
    rating_range = (0, 10)

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
    ["Your Rating", "IMDb Rating", "Year", "Title"]
)
order_asc = st.sidebar.checkbox("Orden ascendente", value=False)

# ----------------- Aplicar filtros básicos (base para todas las pestañas) -----------------

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

if selected_directors:
    filtered = filtered[filtered["Directors"].isin(selected_directors)]

st.caption(
    f"Filtros activos → Años: {year_range[0]}–{year_range[1]} | "
    f"Your Rating: {rating_range[0]}–{rating_range[1]} | "
    f"Géneros: {', '.join(selected_genres) if selected_genres else 'Todos'} | "
    f"Directores: {', '.join(selected_directors) if selected_directors else 'Todos'}"
)

# ----------------- Funciones de formato -----------------


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


# ----------------- Pestañas principales -----------------

tab_catalog, tab_analysis, tab_awards, tab_streaming = st.tabs(
    ["🎬 Catálogo", "📊 Análisis", "🏆 Premios & listas", "🌐 Streaming & recos"]
)

# ============================================================
#                     TAB 1: CATÁLOGO
# ============================================================

with tab_catalog:
    st.markdown("## 🔎 Búsqueda en tu catálogo (respeta los filtros)")

    search_query = st.text_input(
        "Buscar por título, director, género, año o nota…",
        placeholder="Escribe cualquier cosa…",
        key="busqueda_catalogo"
    )

    # Base: siempre los resultados con filtros de la barra lateral
    results_df = filtered.copy()

    if search_query:
        q = search_query.strip().lower()

        def match_any(row):
            campos = [
                row.get("Title", ""),
                row.get("Original Title", ""),
                row.get("Directors", ""),
                row.get("Genres", ""),
                row.get("Year", ""),
                row.get("Your Rating", ""),
                row.get("IMDb Rating", "")
            ]
            texto = " ".join(str(x).lower() for x in campos if pd.notna(x))
            return q in texto

        results_df = results_df[results_df.apply(match_any, axis=1)]

    if order_by in results_df.columns:
        results_df = results_df.sort_values(order_by, ascending=order_asc)

    # ============================================================
    #               RESUMEN + TABLA / TARJETAS
    # ============================================================

    st.markdown("---")
    st.markdown("## 📈 Resumen de resultados (filtros + búsqueda)")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Películas encontradas", len(results_df))
    with col2:
        if "Your Rating" in results_df.columns and results_df["Your Rating"].notna().any():
            st.metric("Promedio de tu nota", f"{results_df['Your Rating'].mean():.2f}")
        else:
            st.metric("Promedio de tu nota", "N/A")
    with col3:
        if "IMDb Rating" in results_df.columns and results_df["IMDb Rating"].notna().any():
            st.metric("Promedio IMDb", f"{results_df['IMDb Rating'].mean():.2f}")
        else:
            st.metric("Promedio IMDb", "N/A")

    st.markdown("### 📚 Resultados (tabla o tarjetas simples)")

    cols_to_show = [
        c for c in ["Title", "Year", "Your Rating", "IMDb Rating",
                    "Genres", "Directors", "Date Rated", "URL"]
        if c in results_df.columns
    ]
    table_df = results_df[cols_to_show].copy()

    format_dict = {}
    subset_cols = []

    if "Year" in table_df.columns:
        format_dict["Year"] = fmt_year
        subset_cols.append("Year")

    if "Your Rating" in table_df.columns:
        format_dict["Your Rating"] = fmt_rating
        subset_cols.append("Your Rating")

    if "IMDb Rating" in table_df.columns:
        format_dict["IMDb Rating"] = fmt_rating
        subset_cols.append("IMDb Rating")

    styled_table = (
        table_df.style
        .format(format_dict)
        .set_properties(subset=subset_cols, **{"text-align": "center"})
        .set_table_styles(
            [
                {"selector": "th.col_heading", "props": [("text-align", "center")]},
            ]
        )
    )

    view_mode = st.radio(
        "Modo de vista",
        ["Tabla", "Tarjetas (grid)"],
        horizontal=True
    )

    if view_mode == "Tabla":
        st.dataframe(
            styled_table,
            use_container_width=True,
            hide_index=True
        )
    else:
        if table_df.empty:
            st.info("No hay resultados para mostrar en modo tarjetas.")
        else:
            st.markdown("Mostrando resultados como tarjetas:")
            num_cols = 4
            cols_cards = st.columns(num_cols)
            cards_df = table_df.copy()

            for i, (_, row) in enumerate(cards_df.iterrows()):
                col = cols_cards[i % num_cols]
                titulo = row.get("Title", "Sin título")
                year = row.get("Year", "")
                year_str = fmt_year(year) if "Year" in cards_df.columns else ""
                your_rating = row.get("Your Rating", None)
                imdb_rating = row.get("IMDb Rating", None)
                genres = row.get("Genres", "")
                directors = row.get("Directors", "")
                url = row.get("URL", "")

                base_rating = your_rating if your_rating is not None and not pd.isna(your_rating) else imdb_rating
                border_color, glow_color = get_rating_colors(base_rating)

                your_str = fmt_rating(your_rating) if your_rating is not None else ""
                imdb_str = fmt_rating(imdb_rating) if imdb_rating is not None else ""

                card_html = f"""
                <div class="movie-card" style="
                    border-color: {border_color};
                    box-shadow:
                        0 0 0 1px rgba(15,23,42,0.9),
                        0 0 22px {glow_color};
                ">
                  <div class="movie-title">{titulo}{f" ({year_str})" if year_str else ""}</div>
                  <div class="movie-sub">
                    {("⭐ Tu nota: " + your_str + "<br>") if your_str else ""}
                    {("IMDb: " + imdb_str + "<br>") if imdb_str else ""}
                    {("<b>Géneros:</b> " + genres + "<br>") if isinstance(genres, str) and genres else ""}
                    {("<b>Director(es):</b> " + directors + "<br>") if isinstance(directors, str) and directors else ""}
                    {f'<a href="{url}" target="_blank">Ver en IMDb</a>' if isinstance(url, str) and url.startswith("http") else ""}
                  </div>
                </div>
                """
                with col:
                    st.markdown(card_html, unsafe_allow_html=True)

    # ============================================================
    #        RESULTADOS DETALLADOS (PÓSTER + PREMIOS + STREAMING)
    # ============================================================

    st.markdown("---")
    st.markdown("## 🎬 Resultados detallados (póster + premios + streaming)")

    if not search_query:
        st.info("Escribe algo en la barra de búsqueda para ver fichas detalladas de las películas.")
    else:
        if results_df.empty:
            st.info("No hay resultados que coincidan con esa búsqueda y los filtros actuales.")
        else:
            max_items_det = st.slider(
                "Número máximo de películas detalladas (para no abusar de las APIs)",
                min_value=1,
                max_value=10,
                value=5,
                step=1,
                key="detallados_max_items"
            )

            base_df_det = results_df.head(max_items_det)

            omdb_key = st.secrets.get("OMDB_API_KEY", None)

            for _, row in base_df_det.iterrows():
                titulo = row.get("Title", "Sin título")
                year = row.get("Year", None)
                your_rating = row.get("Your Rating", None)
                imdb_rating = row.get("IMDb Rating", None)
                genres = row.get("Genres", "")
                directors = row.get("Directors", "")
                url = row.get("URL", "")

                # Ratings base
                base_rating = your_rating if pd.notna(your_rating) else imdb_rating
                border_color, glow_color = get_rating_colors(base_rating)

                # Poster y rating TMDb
                tmdb_rating = get_tmdb_vote_average(titulo, year)
                poster_url = get_poster_url(titulo, year)

                # Premios
                if omdb_key is None:
                    awards_text = "OMDb no configurado (OMDB_API_KEY falta en Secrets)."
                else:
                    awards = get_omdb_awards(titulo, year)
                    if awards is None:
                        awards_text = "No se pudo obtener información de OMDb."
                    elif isinstance(awards, dict) and "error" in awards:
                        awards_text = f"Error OMDb: {awards['error']}"
                    else:
                        parts = []
                        if awards.get("oscars", 0):
                            parts.append(f"🏆 {awards['oscars']} Oscar(s)")
                        if awards.get("emmys", 0):
                            parts.append(f"📺 {awards['emmys']} Emmy(s)")
                        if awards.get("baftas", 0):
                            parts.append(f"🎭 {awards['baftas']} BAFTA(s)")
                        if awards.get("golden_globes", 0):
                            parts.append(f"🌐 {awards['golden_globes']} Globo(s) de Oro")
                        if awards.get("palme_dor", False):
                            parts.append("🌴 Palma de Oro en Cannes")

                        if not parts:
                            awards_text = "Sin grandes premios detectados en OMDb."
                        else:
                            awards_text = " · ".join(parts)

                # Streaming
                availability = get_streaming_availability(titulo, year, country="CL")
                if availability is None:
                    platforms = []
                    link = None
                else:
                    platforms = availability.get("platforms") or []
                    link = availability.get("link")
                platforms_str = ", ".join(platforms) if platforms else "Sin datos para Chile (CL)"
                link_html = (
                    f'<a href="{link}" target="_blank">Ver opciones de streaming en TMDb (Chile)</a>'
                    if link else "Sin enlace de streaming disponible"
                )

                col_img, col_info = st.columns([1, 3])

                with col_img:
                    if isinstance(poster_url, str) and poster_url:
                        st.image(poster_url)
                    else:
                        st.write("Sin póster")

                with col_info:
                    year_str = fmt_year(year) if year is not None else ""
                    year_str = f" ({year_str})" if year_str else ""
                    your_str = fmt_rating(your_rating) if your_rating is not None and pd.notna(your_rating) else "N/A"
                    imdb_str = fmt_rating(imdb_rating) if imdb_rating is not None and pd.notna(imdb_rating) else "N/A"
                    tmdb_str = fmt_rating(tmdb_rating) if tmdb_rating is not None else "N/A"

                    st.markdown(
                        f"""
                        <div class="movie-card" style="
                            border-color: {border_color};
                            box-shadow:
                                0 0 0 1px rgba(15,23,42,0.9),
                                0 0 26px {glow_color};
                            margin-bottom: 16px;
                        ">
                          <div class="movie-title">
                            {titulo}{year_str}
                          </div>
                          <div class="movie-sub">
                            ⭐ Tu nota: {your_str}<br>
                            IMDb: {imdb_str}<br>
                            TMDb: {tmdb_str}<br>
                            <b>Premios:</b> {awards_text}<br>
                            <b>Streaming (CL):</b> {platforms_str}<br>
                            {link_html}<br>
                            {f'<a href="{url}" target="_blank">Ver en IMDb</a>' if isinstance(url, str) and url.startswith("http") else ""}
                            {f"<br><b>Géneros:</b> {genres}" if isinstance(genres, str) and genres else ""}
                            {f"<br><b>Director(es):</b> {directors}" if isinstance(directors, str) and directors else ""}
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # ============================================================
    #                        FAVORITAS
    # ============================================================

    st.markdown("---")
    st.markdown("## ⭐ Tus favoritas (nota ≥ 9) en este contexto")

    with st.expander("Ver favoritas", expanded=False):
        if "Your Rating" in results_df.columns:
            fav = results_df[results_df["Your Rating"] >= 9].copy()
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

                    year_str = fmt_year(year)
                    etiqueta = f"{titulo}"
                    if pd.notna(nota):
                        etiqueta = f"{int(nota)}/10 — {titulo}"
                    if year_str:
                        etiqueta += f" ({year_str})"

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
                            poster_url = get_poster_url(titulo, year)
                            if isinstance(poster_url, str) and poster_url:
                                st.image(poster_url)
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

                    st.markdown(
                        "</div></div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.write("No hay películas con nota ≥ 9 bajo estos filtros + búsqueda.")
        else:
            st.write("No se encontró la columna 'Your Rating' en el CSV.")

    # ============================================================
    #                       GALERÍA
    # ============================================================

    st.markdown("---")
    st.markdown("## 🎞 Galería de pósters (resultados actuales)")

    with st.expander("Ver galería de pósters", expanded=False):
        if show_gallery:
            if TMDB_API_KEY is None:
                st.warning("No hay TMDB_API_KEY configurada en Secrets, no puedo cargar pósters.")
            elif results_df.empty:
                st.info("No hay resultados con los filtros y la búsqueda actual.")
            else:
                gal = results_df.copy()

                if "Your Rating" in gal.columns:
                    gal = gal.sort_values(
                        ["Your Rating", "Year"],
                        ascending=[False, True]
                    )

                gal = gal.head(24)

                st.write(f"Mostrando hasta {len(gal)} pósters de las películas actuales.")

                cols = st.columns(4)

                for i, (_, row) in enumerate(gal.iterrows()):
                    col = cols[i % 4]
                    with col:
                        titulo = row.get("Title", "Sin título")
                        year = row.get("Year", "")
                        nota = row.get("Your Rating", "")
                        imdb_rating = row.get("IMDb Rating", "")
                        url = row.get("URL", "")

                        base_rating = nota if pd.notna(nota) else imdb_rating
                        border_color, glow_color = get_rating_colors(base_rating)

                        poster_url = get_poster_url(titulo, year)
                        if isinstance(poster_url, str) and poster_url:
                            st.image(poster_url)
                        else:
                            st.write("Sin póster")

                        year_str_num = fmt_year(year)
                        year_str = f" ({year_str_num})" if year_str_num else ""
                        nota_str = f"⭐ Tu nota: {fmt_rating(nota)}" if pd.notna(nota) else ""
                        imdb_str = f"IMDb: {fmt_rating(imdb_rating)}" if pd.notna(imdb_rating) else ""
                        imdb_link = f"[IMDb]({url})" if isinstance(url, str) and url.startswith("http") else ""

                        info_html = f"""
                        <div class="movie-card" style="
                            border-color: {border_color};
                            box-shadow:
                                0 0 0 1px rgba(15,23,42,0.9),
                                0 0 20px {glow_color};
                            padding: 10px 10px 8px 10px;
                            margin-top: 8px;
                        ">
                          <div class="movie-title">{titulo}{year_str}</div>
                          <div class="movie-sub">
                            {nota_str}<br>
                            {imdb_str}<br>
                            {imdb_link}
                          </div>
                        </div>
                        """
                        st.markdown(info_html, unsafe_allow_html=True)
        else:
            st.info("La galería está desactivada en las opciones de visualización.")


# ============================================================
#                     TAB 2: ANÁLISIS
# ============================================================

with tab_analysis:
    # (todo el contenido del tab análisis se mantiene igual que antes)
    # ...
    # Para no hacer esto eterno, aquí iría SIN CAMBIOS el código que ya tenías
    # de análisis, gustos personales e infravaloradas.
    # (Puedes pegar aquí el bloque de TAB 2, TAB 3 y TAB 4 que te di en el mensaje anterior,
    #  porque no requieren cambios para esta nueva lógica de búsqueda.)
    st.write("El resto de pestañas (Análisis, Premios & listas, Streaming & recos) siguen igual que en la versión anterior.")
