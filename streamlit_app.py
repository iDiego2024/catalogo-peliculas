import streamlit as st
import pandas as pd
import requests
import random
import altair as alt
import re
from urllib.parse import quote_plus

# ----------------- Configuración general -----------------

st.set_page_config(
    page_title="🎬 Mi catálogo de Películas",
    layout="wide"
)

st.title("🎥 Mi catálogo de películas (IMDb)")
# st.write(
#   "App basada en mi export de IMDb. "
#  "Una sola búsqueda central, filtros en la barra lateral y vista tipo Netflix con premios y streaming."
# )

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
    """
    Streaming desde TMDb watch/providers para un país (por id de TMDb).
    """
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
def get_omdb_awards(title, year=None):
    """
    Info de premios desde OMDb.
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

df["NormTitle"] = df["Title"].apply(normalize_title)

if "Year" in df.columns:
    df["YearInt"] = df["Year"].fillna(-1).astype(int)
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

# Selector de detalle desde la tabla
detail_title = None

# ----------------- TABS PRINCIPALES -----------------

tab_catalog, tab_analysis, tab_afi, tab_what = st.tabs(
    ["🎬 Catálogo", "📊 Análisis", "🏆 Lista AFI", "🎲 ¿Qué ver hoy?"]
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

    # Selector de detalle asociado a la tabla
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

    # ============================================================
    #              DETALLE DE PELÍCULAS (TARJETAS)
    # ============================================================

    st.markdown("---")
    st.markdown("## 🎞 Detalle de películas: pósters + información completa")

    if filtered_view.empty:
        st.info("No hay resultados bajo los filtros y la búsqueda actual.")
    else:
        netflix_df = filtered_view.copy()

        # Si selecciono una película en el selector, muestro solo esa
        if detail_title:
            netflix_df = netflix_df[
                netflix_df["Title"].astype(str) == detail_title
            ]

        # Si no hay selección manual, priorizo por mi nota
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

        cols = st.columns(4)

        for i, (_, row) in enumerate(netflix_df.iterrows()):
            col = cols[i % 4]
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

                # TMDb: una sola llamada para póster + rating + id
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
                    st.image(poster_url)
                else:
                    st.write("Sin póster")

                year_str = f" ({int(year)})" if pd.notna(year) else ""
                nota_str = f"⭐ Mi nota: {fmt_rating(nota)}" if pd.notna(nota) else ""
                imdb_str = f"IMDb: {fmt_rating(imdb_rating)}" if pd.notna(imdb_rating) else ""

                tmdb_str = (
                    f"TMDb: {fmt_rating(tmdb_rating)}"
                    if tmdb_rating is not None else "TMDb: N/A"
                )

                # Premios (OMDb) controlados por checkbox
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

    # ============================================================
    #                        MIS FAVORITAS
    # ============================================================

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


# ============================================================
#                     TAB 2: ANÁLISIS
# ============================================================

with tab_analysis:
    st.markdown("## 📊 Análisis y tendencias (según filtros, sin búsqueda)")

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

    # ============================================================
    #             ANÁLISIS DE GUSTOS PERSONALES
    # ============================================================

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

                            st.write(
                                "Géneros ordenados por mi nota media. "
                                "La desviación estándar (σ) indica cuánto varían mis notas dentro del género."
                            )
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

    # ============================================================
    #               PELÍCULAS INFRAVALORADAS
    # ============================================================

    st.markdown("---")
    st.markdown("## 🔍 Descubrir películas que yo valoro más que IMDb")

    with st.expander("Películas que puntúo muy alto y IMDb no tanto", expanded=False):
        if "Your Rating" in df.columns and "IMDb Rating" in df.columns:
            diff_df = df[df["Your Rating"].notna() & df["IMDb Rating"].notna()].copy()
            if diff_df.empty:
                st.write("No hay suficientes películas con ambas notas (mía e IMDb) para este análisis.")
            else:
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
                                {titulo}{f" ({int(year)})" if pd.notna(year) else ""}
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

    # ============================================================
    #           ESTADÍSTICAS DE PREMIOS (OSCARS, PALMA, ETC.)
    # ============================================================

    st.markdown("---")
    st.markdown("## 🏆 Estadísticas de premios (Oscars, Palma de Oro, etc.)")

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

                    # Cruce de premios con tus gustos
                    merged = awards_stats_df.merge(
                        df[["Title", "Year", "Your Rating", "IMDb Rating"]],
                        on=["Title", "Year"],
                        how="left"
                    )

                    st.markdown("### 🎯 Cómo me llevo con los premios")

                    # Palma de Oro que amas
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

                    # Palma de Oro que no te convencieron
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

                    # Grandes ganadoras de Oscar que amas
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

                    # Grandes ganadoras de Oscar donde fuiste duro
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
                df["YearInt"] = df["Year"].fillna(-1).astype(int)
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
#                     TAB 4: ¿QUÉ VER HOY?
# ============================================================

with tab_what:
    st.markdown("## 🎲 ¿Qué ver hoy? (según mi propio gusto)")

    st.write(
        "Elijo una película de mi catálogo usando mis notas, "
        "año de estreno y disponibilidad en streaming en Chile."
    )

    with st.expander("Ver recomendación aleatoria según mi gusto", expanded=True):

        modo = st.selectbox(
            "Modo de recomendación",
            [
                "Entre todas las películas filtradas",
                "Solo mis favoritas (nota ≥ 9)",
                "Entre mis 8–10 de los últimos 20 años"
            ]
        )

        if st.button("Recomendar una película", key="btn_random_reco"):
            pool = filtered.copy()

            if modo == "Solo mis favoritas (nota ≥ 9)":
                if "Your Rating" in pool.columns:
                    pool = pool[pool["Your Rating"] >= 9]
                else:
                    pool = pool.iloc[0:0]

            elif modo == "Entre mis 8–10 de los últimos 20 años":
                if "Your Rating" in pool.columns and "Year" in pool.columns:
                    pool = pool[
                        (pool["Your Rating"] >= 8) &
                        (pool["Year"].notna()) &
                        (pool["Year"] >= (pd.Timestamp.now().year - 20))
                    ]
                else:
                    pool = pool.iloc[0:0]

            if pool.empty:
                st.warning("No hay películas que cumplan con el modo seleccionado y los filtros actuales.")
            else:
                if "Your Rating" in pool.columns and pool["Your Rating"].notna().any():
                    notas = pool["Your Rating"].fillna(0)
                    pesos = (notas + 1).tolist()
                else:
                    pesos = None

                idx = random.choices(pool.index.tolist(), weights=pesos, k=1)[0]
                peli = pool.loc[idx]

                titulo = peli.get("Title", "Sin título")
                year = peli.get("Year", "")
                nota = peli.get("Your Rating", "")
                imdb_rating = peli.get("IMDb Rating", "")
                genres = peli.get("Genres", "")
                directors = peli.get("Directors", "")
                url = peli.get("URL", "")

                base_rating = nota if pd.notna(nota) else imdb_rating
                border_color, glow_color = get_rating_colors(base_rating)

                # TMDb: una sola llamada para rating + póster + id
                tmdb_info = get_tmdb_basic_info(titulo, year)
                if tmdb_info:
                    tmdb_rating = tmdb_info.get("vote_average")
                    poster_url = tmdb_info.get("poster_url")
                    tmdb_id = tmdb_info.get("id")
                    availability = get_tmdb_providers(tmdb_id, country="CL")
                else:
                    tmdb_rating = None
                    poster_url = None
                    availability = None

                tmdb_str = (
                    f"TMDb: {fmt_rating(tmdb_rating)}"
                    if tmdb_rating is not None else "TMDb: N/A"
                )

                # Premios (OMDb) controlados por checkbox
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
                    f'<a href="{link}" target="_blank">Ver opciones de streaming en TMDb (CL)</a>'
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

                col_img, col_info = st.columns([1, 3])

                with col_img:
                    if isinstance(poster_url, str) and poster_url:
                        st.image(poster_url)
                    else:
                        st.write("Sin póster")

                with col_info:
                    st.markdown(
                        f"""
                        <div class="movie-card" style="
                            border-color: {border_color};
                            box-shadow:
                                0 0 0 1px rgba(15,23,42,0.9),
                                0 0 26px {glow_color};
                            margin-bottom: 10px;
                        ">
                          <div class="movie-title">
                            {titulo}{f" ({int(year)})" if pd.notna(year) else ""}
                          </div>
                          <div class="movie-sub">
                            {f"⭐ Mi nota: {fmt_rating(nota)}<br>" if pd.notna(nota) else ""}
                            {f"IMDb: {fmt_rating(imdb_rating)}<br>" if pd.notna(imdb_rating) else ""}
                            {tmdb_str}<br>
                            <b>Géneros:</b> {genres}<br>
                            <b>Director(es):</b> {directors}<br>
                            <b>Premios:</b> {awards_text}<br>
                            <b>Streaming (CL):</b> {platforms_str}<br>
                            {link_html}<br>
                            {imdb_link_html}<br>
                            <b>Reseñas:</b> {reseñas_html}
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                st.markdown(
                    "Esta recomendación tiene en cuenta mi nota, la valoración global "
                    "y si puedo verla fácilmente en streaming en Chile."
                )

    # Pequeño ranking extra de sugerencias
    st.markdown("---")
    st.markdown("### 📌 Otras sugerencias rápidas (según mis notas)")

    if filtered.empty:
        st.info("No hay suficientes datos bajo los filtros actuales.")
    else:
        sug = filtered.copy()
        if "Your Rating" in sug.columns:
            sug = sug[sug["Your Rating"].notna()]
            if not sug.empty:
                sug = sug.sort_values(
                    ["Your Rating", "IMDb Rating", "Year"],
                    ascending=[False, False, False]
                ).head(10)

                mini = sug[["Title", "Year", "Your Rating", "IMDb Rating", "Genres"]].copy()
                mini["Year"] = mini["Year"].apply(fmt_year)
                mini["Your Rating"] = mini["Your Rating"].apply(fmt_rating)
                mini["IMDb Rating"] = mini["IMDb Rating"].apply(fmt_rating)
                mini = mini.rename(
                    columns={
                        "Title": "Película",
                        "Year": "Año",
                        "Your Rating": "Mi nota",
                        "IMDb Rating": "IMDb",
                        "Genres": "Géneros"
                    }
                )
                st.dataframe(mini, use_container_width=True, hide_index=True)
            else:
                st.write("No tengo notas suficientes para sugerencias.")
        else:
            st.write("No se encontró la columna 'Your Rating' en el CSV.")
