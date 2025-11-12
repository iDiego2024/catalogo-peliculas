# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import re
from urllib.parse import quote_plus

from .styles import GOLDEN_CSS

# --------- Versión de la app ----------
APP_VERSION = "v2.1.2"  # bump por fix de load_data

# --------- Config APIs externas --------
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"
TMDB_SIMILAR_URL_TEMPLATE = "https://api.themoviedb.org/3/movie/{movie_id}/similar"

YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", None)
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# ----------------- AFI LIST (10th Anniversary) -----------------
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
    {"Rank": 91, "Title": "Tootsie", "Year": 1982},
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

# ==================== ESTILO / SIDEBAR ====================

def apply_theme_and_css():
    st.markdown(GOLDEN_CSS, unsafe_allow_html=True)

def show_changelog_sidebar():
    with st.expander("📌 Información & cambios", expanded=False):
        st.write(
            f"- **Versión:** {APP_VERSION}\n"
            "- **UX:** tema dorado + grid ancho + tarjetas pulidas.\n"
            "- **Arquitectura:** módulos separados (`modules/`)."
        )
        st.caption("Cache en TMDb/OMDb/YouTube para mejor rendimiento.")

# ==================== CARGA DE DATOS ======================

@st.cache_data
def load_data(file_path_or_buffer):
    df = pd.read_csv(file_path_or_buffer)

    # numéricas
    df["Your Rating"] = pd.to_numeric(df.get("Your Rating"), errors="coerce")
    df["IMDb Rating"] = pd.to_numeric(df.get("IMDb Rating"), errors="coerce")

    # Year
    if "Year" in df.columns:
        df["Year"] = df["Year"].astype(str).str.extract(r"(\d{4})")[0].astype(float)
    else:
        df["Year"] = None

    # ---- FIX: NO usar `or ""` con Series ----
    if "Genres" in df.columns:
        df["Genres"] = df["Genres"].fillna("")
    else:
        df["Genres"] = ""

    if "Directors" in df.columns:
        df["Directors"] = df["Directors"].fillna("")
    else:
        df["Directors"] = ""

    # listas de géneros
    df["GenreList"] = df["Genres"].apply(
        lambda x: [] if pd.isna(x) or x == "" else str(x).split(", ")
    )

    # fecha
    if "Date Rated" in df.columns:
        df["Date Rated"] = pd.to_datetime(df["Date Rated"], errors="coerce").dt.date

    # texto de búsqueda
    search_cols = [
        c for c in ["Title", "Original Title", "Directors", "Genres", "Year", "Your Rating", "IMDb Rating"]
        if c in df.columns
    ]
    if search_cols:
        df["SearchText"] = (
            df[search_cols].astype(str).apply(lambda row: " ".join(row), axis=1).str.lower()
        )
    else:
        df["SearchText"] = ""

    # auxiliares
    if "Title" in df.columns:
        df["NormTitle"] = df["Title"].apply(normalize_title)
    else:
        df["NormTitle"] = ""

    if "Year" in df.columns:
        df["YearInt"] = df["Year"].fillna(-1).astype(int)
    else:
        df["YearInt"] = -1

    return df

# ================== HELPERS ==============================

def normalize_title(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

def fmt_year(y):
    if pd.isna(y): return ""
    return f"{int(float(y))}"

def fmt_rating(v):
    if pd.isna(v): return ""
    try: return f"{float(v):.1f}"
    except Exception: return str(v)

def get_rating_colors(rating):
    try:
        r = float(rating)
    except Exception:
        return ("rgba(148,163,184,0.8)", "rgba(15,23,42,0.0)")
    if r >= 9:   return ("#22c55e", "rgba(34,197,94,0.55)")
    if r >= 8:   return ("#0ea5e9", "rgba(14,165,233,0.55)")
    if r >= 7:   return ("#a855f7", "rgba(168,85,247,0.50)")
    if r >= 6:   return ("#eab308", "rgba(234,179,8,0.45)")
    return ("#f97316", "rgba(249,115,22,0.45)")

def get_spanish_review_link(title, year=None):
    if not title or pd.isna(title): return None
    q = f"reseña película {title}"
    try:
        if year is not None and not pd.isna(year):
            q += f" {int(float(year))}"
    except Exception:
        pass
    return "https://www.google.com/search?q=" + quote_plus(q)

# ================== TMDb / YouTube / OMDb =================

def _coerce_year_for_tmdb(year):
    if year is None or pd.isna(year): return None
    try: return int(float(year))
    except Exception: return None

@st.cache_data
def get_tmdb_basic_info(title, year=None):
    if TMDB_API_KEY is None or not title or pd.isna(title): return None
    params = {"api_key": TMDB_API_KEY, "query": str(title).strip()}
    y = _coerce_year_for_tmdb(year)
    if y is not None: params["year"] = y
    try:
        r = requests.get(TMDB_SEARCH_URL, params=params, timeout=4)
        if r.status_code != 200: return None
        results = r.json().get("results", [])
        if not results: return None
        m = results[0]
        return {
            "id": m.get("id"),
            "poster_url": f"{TMDB_IMAGE_BASE}{m['poster_path']}" if m.get("poster_path") else None,
            "vote_average": m.get("vote_average"),
        }
    except Exception:
        return None

@st.cache_data
def get_tmdb_providers(tmdb_id, country="CL"):
    if TMDB_API_KEY is None or not tmdb_id: return None
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/watch/providers"
        r = requests.get(url, params={"api_key": TMDB_API_KEY}, timeout=4)
        if r.status_code != 200: return None
        cdata = r.json().get("results", {}).get(country.upper())
        if not cdata: return None
        providers = set()
        for key in ["flatrate", "rent", "buy", "ads", "free"]:
            for item in cdata.get(key, []) or []:
                name = item.get("provider_name")
                if name: providers.add(name)
        return {"platforms": sorted(providers) if providers else [], "link": cdata.get("link")}
    except Exception:
        return None

@st.cache_data
def get_youtube_trailer_url(title, year=None):
    if YOUTUBE_API_KEY is None or not title or pd.isna(title): return None
    q = f"{title} trailer"
    try:
        if year is not None and not pd.isna(year): q += f" {int(float(year))}"
    except Exception:
        pass
    params = {"key": YOUTUBE_API_KEY, "part": "snippet", "q": q,
              "type": "video", "maxResults": 1, "videoEmbeddable": "true", "regionCode": "CL"}
    try:
        r = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=5)
        if r.status_code != 200: return None
        items = r.json().get("items", [])
        if not items: return None
        vid = items[0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={vid}"
    except Exception:
        return None

@st.cache_data
def get_omdb_awards(title, year=None):
    api_key = st.secrets.get("OMDB_API_KEY", None)
    if api_key is None: return {"error": "OMDB_API_KEY no está configurada en st.secrets."}
    if not title or pd.isna(title): return {"error": "Título vacío o inválido."}
    base_url = "https://www.omdbapi.com/"
    raw_title = str(title).strip()
    simple_title = re.sub(r"\s*\(.*?\)\s*$", "", raw_title).strip()
    y = None
    try:
        if year is not None and not pd.isna(year): y = int(float(year))
    except Exception:
        y = None

    def _query(params):
        try:
            r = requests.get(base_url, params=params, timeout=8)
            if r.status_code != 200: return {"error": f"HTTP {r.status_code} desde OMDb."}
            data = r.json()
            if data.get("Response") != "True":
                return {"error": data.get("Error", "Respuesta no válida de OMDb.")}
            return data
        except Exception as e:
            return {"error": f"Excepción OMDb: {e}"}

    data, last_error = None, None
    for t in [raw_title, simple_title]:
        params = {"apikey": api_key, "type": "movie", "t": t}
        if y: params["y"] = y
        out = _query(params)
        if "error" in out: last_error = out["error"]
        else: data = out; break
    if data is None:
        params = {"apikey": api_key, "type": "movie", "s": simple_title}
        if y: params["y"] = y
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

    awards_str = data.get("Awards", "") or ""
    if not awards_str or awards_str == "N/A":
        return {"raw": None, "oscars": 0, "emmys": 0, "baftas": 0, "golden_globes": 0,
                "palme_dor": False, "oscars_nominated": 0, "total_wins": 0, "total_nominations": 0}

    text_lower = awards_str.lower()
    oscars=emmys=baftas=golden_globes=oscars_nominated=total_wins=total_nominations=0
    palme_dor=False

    m = re.search(r"won\s+(\d+)\s+oscars?", text_lower) or re.search(r"won\s+(\d+)\s+oscar\b", text_lower)
    if m: oscars=int(m.group(1))
    m = re.search(r"nominated\s+for\s+(\d+)\s+oscars?", text_lower) or re.search(r"nominated\s+for\s+(\d+)\s+oscar\b", text_lower)
    if m: oscars_nominated=int(m.group(1))
    for pat in [r"won\s+(\d+)\s+primetime\s+emmys?", r"won\s+(\d+)\s+emmys?", r"won\s+(\d+)\s+emmy\b"]:
        m=re.search(pat,text_lower)
        if m: emmys=int(m.group(1)); break
    m=re.search(r"won\s+(\d+)[^\.]*bafta", text_lower)
    if m: baftas=int(m.group(1))
    elif "bafta" in text_lower: baftas=1
    m=re.search(r"won\s+(\d+)[^\.]*golden\s+globes?", text_lower) or re.search(r"won\s+(\d+)[^\.]*golden\s+globe\b", text_lower)
    if m: golden_globes=int(m.group(1))
    elif "golden globe" in text_lower: golden_globes=1
    if re.search(r"palme\s+d['’]or", text_lower): palme_dor=True
    m=re.search(r"(\d+)\s+wins?", text_lower)
    if m: total_wins=int(m.group(1))
    m=re.search(r"(\d+)\s+nominations?", text_lower)
    if m: total_nominations=int(m.group(1))

    return {
        "raw": awards_str,
        "oscars": oscars, "emmys": emmys, "baftas": baftas, "golden_globes": golden_globes,
        "palme_dor": palme_dor, "oscars_nominated": oscars_nominated,
        "total_wins": total_wins, "total_nominations": total_nominations,
    }
