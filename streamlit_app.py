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
    layout="centered"
)

st.title("🎥 Mi catálogo de películas (IMDb)")

# ----------------- Config TMDb / OMDb -----------------

# Aquí puedes poner tanto:
# - API key (v3 auth): algo tipo "1234567890abcdef..."
# - API Read Access Token (v4 auth): cadena larga que empieza por "eyJ..."
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)

TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"

OMDB_API_KEY = st.secrets.get("OMDB_API_KEY", None)


def _tmdb_request(url, params=None, timeout=4):
    """
    Envía una petición a TMDb soportando:
      - API key v3 (query param api_key=)
      - API token v4 (Authorization: Bearer ...)
    Devuelve el objeto Response o None si no hay clave / error gordo.
    """
    if TMDB_API_KEY is None:
        return None

    params = params.copy() if params else {}
    headers = {}

    # Heurística simple: si parece un JWT largo, lo usamos como token v4
    if isinstance(TMDB_API_KEY, str) and TMDB_API_KEY.startswith("eyJ"):
        headers["Authorization"] = f"Bearer {TMDB_API_KEY}"
    else:
        params["api_key"] = TMDB_API_KEY

    try:
        r = requests.get(url, params=params, headers=headers, timeout=timeout)
        return r
    except Exception:
        return None


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

    if "Your Rating" in df.columns:
        df["Your Rating"] = pd.to_numeric(df["Your Rating"], errors="coerce")
    else:
        df["Your Rating"] = None

    if "IMDb Rating" in df.columns:
        df["IMDb Rating"] = pd.to_numeric(df["IMDb Rating"], errors="coerce")
    else:
        df["IMDb Rating"] = None

    if "Year" in df.columns:
        df["Year"] = (
            df["Year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
            .astype(float)
        )
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
    """
    Devuelve info básica TMDb en una sola búsqueda:
    - id
    - poster_url
    - vote_average
    """
    if TMDB_API_KEY is None:
        return None
    if not title or pd.isna(title):
        return None

    title = str(title).strip()
    year_int = _coerce_year_for_tmdb(year)

    params = {"query": title}
    if year_int is not None:
        params["year"] = year_int

    r = _tmdb_request(TMDB_SEARCH_URL, params=params, timeout=5)
    if r is None or r.status_code != 200:
        return None

    try:
        data = r.json()
    except Exception:
        return None

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


@st.cache_data
def get_tmdb_providers(tmdb_id, country="CL"):
    """
    Streaming desde TMDb watch/providers para un país (por id de TMDb).
    """
    if TMDB_API_KEY is None or not tmdb_id:
        return None

    providers_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/watch/providers"
    r = _tmdb_request(providers_url, params=None, timeout=5)
    if r is None or r.status_code != 200:
        return None

    try:
        pdata = r.json()
    except Exception:
        return None

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


@st.cache_data
def get_omdb_awards(title, year=None):
    """
    Info de premios desde OMDb.
    """
    api_key = OMDB_API_KEY
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


@st.cache_data
def compute_awards_table(df_basic):
    """
    Calcula tabla de premios (Oscars, Palma de Oro, etc.) para un subconjunto de pelis.
    df_basic debe tener columnas Title y Year.
    """
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

df["NormTitle"] = df["Title"].fillna("").apply(normalize_title)

if "Year" in df.columns:
    df["YearInt"] = df["Year"].fillna(-1).astype(int)
else:
    df["YearInt"] = -1

# Avisos de API keys en la barra lateral
if TMDB_API_KEY is None:
    st.sidebar.warning(
        "⚠️ No se encontró TMDB_API_KEY en st.secrets. "
        "No se podrán mostrar pósters ni proveedores de streaming desde TMDb."
    )
else:
    st.sidebar.caption("TMDb configurado: intentaré cargar pósters en tarjetas y galería.")

if OMDB_API_KEY is None:
    st.sidebar.info(
        "ℹ️ OMDB_API_KEY no está configurada en st.secrets. "
        "La sección de premios de OMDb mostrará mensajes de error."
    )

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
        padding-top: 3.5rem;
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
            padding-top: 4.5rem;
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
max_netflix_items = st.sidebar.slider(
    "Máx. películas en tarjetas de detalle",
    min_value=4, max_value=20, value=8, step=1
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
    min_rating = int(df["Your Rating"].min())
    max_rating = int(df["Your Rating"].max())
    rating_range = st.sidebar.slider(
        "Mi nota (Your Rating)", min_rating, max_rating, (min_rating, max_rating)
    )
else:
    rating_range = (0, 10)

all_genres = sorted(
    set(
        g
        for sub in df.get("GenreList", pd.Series([])).dropna()
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

if selected_directors:
    filtered = filtered[filtered["Directors"].isin(selected_directors)]

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
    return df_in[df_in["SearchText"].str.contains(q, na=False)]


filtered_view = apply_search(filtered.copy(), search_query)

if order_by in filtered_view.columns:
    filtered_view = filtered_view.sort_values(order_by, ascending=order_asc)

detail_title = None

# ----------------- TABS PRINCIPALES -----------------

tab_catalog, tab_analysis, tab_afi, tab_what = st.tabs(
    ["🎬 Catálogo", "📊 Análisis", "🏆 Lista AFI", "🎲 ¿Qué ver hoy?"]
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

    csv_filtrado = table_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Descargar resultados filtrados (CSV)",
        data=csv_filtrado,
        file_name="mis_peliculas_filtradas.csv",
        mime="text/csv",
    )

    if not filtered_view.empty:
        opciones_detalle = ["(ninguna)"] + [
            f"{row['Title']} ({fmt_year(row['Year'])})"
            for _, row in filtered_view.iterrows()
        ]
        seleccion = st.selectbox(
            "Selecciona una película de la tabla para ver su ficha abajo:",
            opciones_detalle,
            index=0
        )
        if seleccion != "(ninguna)":
            titulo_sel = seleccion.rsplit(" (", 1)[0]
            detail_title = titulo_sel

    # --------- TARJETAS DETALLE ----------

    st.markdown("---")
    st.markdown("## 🎞 Detalle de películas: pósters + información completa")

    if filtered_view.empty:
        st.info("No hay resultados bajo los filtros y la búsqueda actual.")
    else:
        netflix_df = filtered_view.copy()

        if detail_title:
            netflix_df = netflix_df[
                netflix_df["Title"].astype(str) == detail_title
            ]

        if not detail_title and "Your Rating" in netflix_df.columns:
            netflix_df = netflix_df.sort_values(
                ["Your Rating", "Year"],
                ascending=[False, True]
            )

        netflix_df = netflix_df.head(max_netflix_items)

        st.write(
            f"Mostrando hasta {len(netflix_df)} películas en tarjetas de detalle "
            f"con mi nota, IMDb, TMDb, premios y streaming en Chile."
        )

        cols = st.columns(3)

        for i, (_, row) in enumerate(netflix_df.iterrows()):
            col = cols[i % 3]
            with col:
                titulo = row.get("Title", "Sin título")
                year = row.get("Year", "")
                nota = row.get("Your Rating", "")
                imdb_rating = row.get("IMDb Rating", "")
                genres = row.get("Genres", "")
                directors = row.get("Directors", "")
                url = row.get("URL", "")

                base_rating = nota if pd.notna(nota) else imdb_rating
                border_color, glow_color = get_rating_colors(base_rating)

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

                if isinstance(poster_url, str) and poster_url:
                    try:
                        st.image(poster_url)
                    except Exception:
                        st.write("Sin póster")
                else:
                    st.write("Sin póster")

                year_str = f" ({int(year)})" if pd.notna(year) else ""
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
                    {tmdb_str}<br>
                    {f"<b>Géneros:</b> {genres}<br>" if isinstance(genres, str) and genres else ""}
                    {f"<b>Director(es):</b> {directors}<br>" if isinstance(directors, str) and directors else ""}
                    <b>Premios:</b> {awards_text}<br>
                    <b>Streaming (CL):</b> {platforms_str}<br>
                    {link_html}<br>
                    {imdb_link_html}<br>
                    <b>Reseñas:</b> {reseñas_html}
                  </div>
                </div>
                """
                st.markdown(info_html, unsafe_allow_html=True)

    # --------- FAVORITAS ----------

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
                    if pd.notna(year):
                        etiqueta += f" ({int(year)})"

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

                    st.markdown(
                        "</div></div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.write("No hay películas con nota ≥ 9 bajo estos filtros + búsqueda.")
        else:
            st.write("No se encontró la columna 'Your Rating' en el CSV.")

    # --------- GALERÍA VISUAL ----------

    st.markdown("---")
    st.markdown("## 🧱 Galería visual (pósters por páginas)")

    total_pelis = len(filtered_view)

    if total_pelis == 0:
        st.info("No hay películas bajo los filtros + búsqueda actuales para la galería.")
    else:
        page_size = st.slider(
            "Películas por página en la galería",
            min_value=20,
            max_value=60,
            value=30,
            step=10,
            key="gallery_page_size"
        )

        num_pages = math.ceil(total_pelis / page_size)

        col_page_info_1, col_page_info_2 = st.columns([2, 1])
        with col_page_info_1:
            st.caption(
                f"Mostrando pósters de tus películas filtradas: "
                f"{total_pelis} en total · {page_size} por página."
            )
        with col_page_info_2:
            current_page = st.number_input(
                "Página",
                min_value=1,
                max_value=max(num_pages, 1),
                value=1,
                step=1,
                key="gallery_current_page"
            )

        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        page_df = filtered_view.iloc[start_idx:end_idx]

        st.caption(f"Página {current_page} de {num_pages}")

        cols_gallery = st.columns(6)

        for i, (_, row) in enumerate(page_df.iterrows()):
            col = cols_gallery[i % 6]
            with col:
                titulo = row.get("Title", "Sin título")
                year = row.get("Year", "")
                nota = row.get("Your Rating", "")
                url = row.get("URL", "")

                tmdb_info = get_tmdb_basic_info(titulo, year)
                poster_url = tmdb_info.get("poster_url") if tmdb_info else None

                if isinstance(poster_url, str) and poster_url:
                    try:
                        st.image(poster_url, use_container_width=True)
                    except Exception:
                        st.write("Sin póster")
                else:
                    st.write("Sin póster")

                year_str = f" ({fmt_year(year)})" if pd.notna(year) else ""
                nota_str = f" · ⭐ {fmt_rating(nota)}" if pd.notna(nota) else ""

                st.markdown(
                    f"**{titulo}**{year_str}{nota_str}",
                    help="Título desde tu catálogo de IMDb"
                )

                enlaces = []

                if isinstance(url, str) and url.startswith("http"):
                    enlaces.append(f"[IMDb]({url})")

                reseñas_url = get_spanish_review_link(titulo, year)
                if reseñas_url:
                    enlaces.append(f"[Reseñas ESP]({reseñas_url})")

                if enlaces:
                    st.markdown(" · ".join(enlaces))

# ============================================================
# Las demás pestañas (Análisis, AFI, ¿Qué ver hoy?)
# ============================================================

# --- El resto de tu código (tab_analysis, tab_afi, tab_what) se mantiene
#     exactamente igual al que ya tenías y que funcionaba.
#     Para no hacer este mensaje interminable, no lo repito: puedes
#     pegar aquí debajo las mismas secciones que ya tenías.
