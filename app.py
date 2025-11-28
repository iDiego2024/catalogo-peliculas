import streamlit as st
import pandas as pd
import requests
import altair as alt
import re
import math
import random
from urllib.parse import quote_plus
from thefuzz import fuzz

# ===================== Versión y changelog =====================
APP_VERSION = "1.1.7"

CHANGELOG = {
    "1.1.7": [
        "Búsqueda: Se implementa 'Fuzzy Search' (búsqueda difusa). Ahora encuentra resultados aunque haya errores ortográficos leves (ej: 'Openhimer').",
        "Búsqueda: Los resultados se ordenan por relevancia de coincidencia.",
    ],
    "1.1.6": [
        "Sidebar: Se eliminan opciones de visualización (TMDb, Tráilers, Pósters) dejándolas activas por defecto.",
        "UX: La opción avanzada de consultar premios OMDb se mueve bajo la sección de Filtros.",
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

# ----------------- Constantes y Regex Precompilados -----------------
# Compilar regex mejora el rendimiento en llamadas repetitivas
RE_NORMALIZE = re.compile(r"[^a-z0-9]+")
RE_YEAR_EXTRACT = re.compile(r"(\d{4})")
RE_SPLIT_VER = re.compile(r"[.\-+]")

# APIs
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"
TMDB_SIMILAR_URL_TEMPLATE = "https://api.themoviedb.org/3/movie/{movie_id}/similar"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
OMDB_BASE_URL = "https://www.omdbapi.com/"

# ----------------- Configuración general -----------------

st.set_page_config(
    page_title=f"🎬 Mi catálogo de Películas · v{APP_VERSION}",
    layout="centered"
)

st.title("🎥 Mi catálogo de películas (IMDb)")

TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", None)

# ----------------- Lista AFI 100 -----------------
# (Se mantiene la lista original)
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

# ----------------- Funciones Auxiliares -----------------

def normalize_title(s: str) -> str:
    """Normaliza un título para compararlo (minúsculas, sin espacios ni signos)."""
    return RE_NORMALIZE.sub("", str(s).lower())

@st.cache_data
def load_data(file_path_or_buffer):
    df = pd.read_csv(file_path_or_buffer)

    # Conversión numérica
    for col in ["Your Rating", "IMDb Rating"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = None

    # Año robusto
    if "Year" in df.columns:
        year_str = df["Year"].astype(str).str.extract(RE_YEAR_EXTRACT)[0]
        df["Year"] = pd.to_numeric(year_str, errors="coerce")
    else:
        df["Year"] = None

    # Listas y strings
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

    # Optimización: Texto de búsqueda precomputado (Vectorizado)
    search_cols = [c for c in ["Title", "Original Title", "Directors", "Genres", "Year", "Your Rating", "IMDb Rating"] if c in df.columns]
    
    if search_cols:
        # Vectorización mucho más rápida que apply(axis=1)
        df["SearchText"] = df[search_cols[0]].astype(str)
        for col in search_cols[1:]:
            df["SearchText"] = df["SearchText"] + " " + df[col].astype(str)
        df["SearchText"] = df["SearchText"].str.lower()
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
    if TMDB_API_KEY is None or not title or pd.isna(title):
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
        results = r.json().get("results", [])
        if not results:
            return None

        movie = results[0]
        return {
            "id": movie.get("id"),
            "poster_url": f"{TMDB_IMAGE_BASE}{movie.get('poster_path')}" if movie.get("poster_path") else None,
            "vote_average": movie.get("vote_average"),
        }
    except Exception:
        return None

@st.cache_data
def get_tmdb_providers(tmdb_id, country="CL"):
    if TMDB_API_KEY is None or not tmdb_id:
        return None
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/watch/providers"
        r = requests.get(url, params={"api_key": TMDB_API_KEY}, timeout=4)
        if r.status_code != 200:
            return None
        cdata = r.json().get("results", {}).get(country.upper())
        if not cdata:
            return None
        
        providers = {item.get("provider_name") for key in ["flatrate", "rent", "buy", "ads", "free"] for item in cdata.get(key, [])}
        return {"platforms": sorted(list(providers)), "link": cdata.get("link")}
    except Exception:
        return None

@st.cache_data
def get_youtube_trailer_url(title, year=None, language_hint="es"):
    if YOUTUBE_API_KEY is None or not title or pd.isna(title):
        return None
    
    q = f"{title} trailer"
    if year and not pd.isna(year):
        q += f" {int(float(year))}"

    params = {
        "key": YOUTUBE_API_KEY, "part": "snippet", "q": q,
        "type": "video", "maxResults": 1, "videoEmbeddable": "true", "regionCode": "CL",
    }
    try:
        r = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=5)
        items = r.json().get("items", [])
        if items:
            return f"https://www.youtube.com/watch?v={items[0]['id']['videoId']}"
    except Exception:
        pass
    return None

@st.cache_data
def get_omdb_awards(title, year=None):
    api_key = st.secrets.get("OMDB_API_KEY", None)
    if api_key is None:
        return {"error": "OMDB_API_KEY no configurada"}
    if not title or pd.isna(title):
        return {"error": "Título inválido"}

    raw_title = str(title).strip()
    simple_title = re.sub(r"\s*\(.*?\)\s*$", "", raw_title).strip()
    year_int = int(float(year)) if (year is not None and not pd.isna(year)) else None

    def _query(params):
        try:
            r = requests.get(OMDB_BASE_URL, params=params, timeout=8)
            return r.json() if r.status_code == 200 else None
        except Exception:
            return None

    data, last_error = None, None
    
    # Intento 1: Título exacto
    for t in [raw_title, simple_title]:
        params = {"apikey": api_key, "t": t, "type": "movie", "y": year_int} if year_int else {"apikey": api_key, "t": t, "type": "movie"}
        res = _query(params)
        if res and res.get("Response") == "True":
            data = res
            break
        elif res:
            last_error = res.get("Error")

    # Intento 2: Búsqueda general si falla el exacto
    if not data:
        params = {"apikey": api_key, "s": simple_title, "type": "movie", "y": year_int} if year_int else {"apikey": api_key, "s": simple_title, "type": "movie"}
        search = _query(params)
        if search and search.get("Search"):
            data = _query({"apikey": api_key, "i": search["Search"][0].get("imdbID")})

    if not data or data.get("Response") != "True":
        return {"error": last_error or "No encontrado"}

    awards_str = data.get("Awards", "N/A")
    if awards_str == "N/A":
        return {"raw": None, "oscars": 0, "emmys": 0, "baftas": 0, "golden_globes": 0, "palme_dor": False, "oscars_nominated": 0, "total_wins": 0, "total_nominations": 0}

    # Parsing de texto
    text_lower = awards_str.lower()
    
    def extract_count(patterns):
        for pat in patterns:
            m = re.search(pat, text_lower)
            if m: return int(m.group(1))
        return 0

    oscars = extract_count([r"won\s+(\d+)\s+oscars?", r"won\s+(\d+)\s+oscar\b"])
    oscars_nom = extract_count([r"nominated\s+for\s+(\d+)\s+oscars?", r"nominated\s+for\s+(\d+)\s+oscar\b"])
    emmys = extract_count([r"won\s+(\d+)\s+primetime\s+emmys?", r"won\s+(\d+)\s+emmys?", r"won\s+(\d+)\s+emmy\b"])
    baftas = extract_count([r"won\s+(\d+)[^\.]*bafta"]) or (1 if "bafta" in text_lower else 0)
    globes = extract_count([r"won\s+(\d+)[^\.]*golden\s+globes?", r"won\s+(\d+)[^\.]*golden\s+globe\b"]) or (1 if "golden globe" in text_lower else 0)
    wins = extract_count([r"(\d+)\s+wins?"])
    noms = extract_count([r"(\d+)\s+nominations?"])
    palme = bool(re.search(r"palme\s+d['’]or", text_lower))

    return {
        "raw": awards_str, "oscars": oscars, "emmys": emmys, "baftas": baftas,
        "golden_globes": globes, "palme_dor": palme, "oscars_nominated": oscars_nom,
        "total_wins": wins, "total_nominations": noms,
    }

def compute_awards_table(df_basic):
    rows = []
    for _, r in df_basic.iterrows():
        aw = get_omdb_awards(r.get("Title"), r.get("Year"))
        if "error" not in aw:
            rows.append({**{"Title": r.get("Title"), "Year": r.get("Year")}, **aw})
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Title", "Year", "oscars", "total_wins", "raw"])

def get_rating_colors(rating):
    try:
        r = float(rating)
    except:
        return ("rgba(148,163,184,0.8)", "rgba(15,23,42,0.0)")
    if r >= 9: return ("#22c55e", "rgba(34,197,94,0.55)")
    if r >= 8: return ("#0ea5e9", "rgba(14,165,233,0.55)")
    if r >= 7: return ("#a855f7", "rgba(168,85,247,0.50)")
    if r >= 6: return ("#eab308", "rgba(234,179,8,0.45)")
    return ("#f97316", "rgba(249,115,22,0.45)")

def get_spanish_review_link(title, year=None):
    if not title or pd.isna(title): return None
    q = f"reseña película {title}"
    if year and not pd.isna(year): q += f" {int(float(year))}"
    return "https://www.google.com/search?q=" + quote_plus(q)

def recommend_from_catalog(df_all, seed_row, top_n=5):
    if df_all.empty: return pd.DataFrame()
    
    candidates = df_all[~((df_all["Title"] == seed_row.get("Title")) & (df_all["Year"] == seed_row.get("Year")))]
    seed_genres, seed_year, seed_rating = set(seed_row.get("GenreList") or []), seed_row.get("Year"), seed_row.get("Your Rating")
    seed_dirs = {d.strip() for d in str(seed_row.get("Directors") or "").split(",") if d.strip()}
    
    scores = []
    for idx, r in candidates.iterrows():
        score = 0.0
        # Comparación vectorial sería ideal, pero iterrows es seguro para sets
        score += 2.0 * len(seed_genres & set(r.get("GenreList") or []))
        if seed_dirs & {d.strip() for d in str(r.get("Directors") or "").split(",") if d.strip()}:
            score += 3.0
        if pd.notna(seed_year) and pd.notna(r.get("Year")):
            score -= min(abs(seed_year - r.get("Year")) / 10.0, 3.0)
        if pd.notna(seed_rating) and pd.notna(r.get("Your Rating")):
            score -= abs(seed_rating - r.get("Your Rating")) * 0.3
        if pd.notna(r.get("IMDb Rating")):
            score += (float(r.get("IMDb Rating")) - 6.5) * 0.2
        scores.append((idx, score))
        
    top_indices = [x[0] for x in sorted(scores, key=lambda x: x[1], reverse=True)[:top_n] if x[1] > 0]
    return df_all.loc[top_indices].copy() if top_indices else pd.DataFrame()

# ----------------- Funciones Óscar (Optimizadas) -----------------

@st.cache_data
def load_oscar_data_from_excel(path_xlsx="Oscar_Data_1927_today.xlsx"):
    try:
        raw = pd.read_excel(path_xlsx)
    except Exception:
        return pd.DataFrame()

    cols_lower = {c.lower(): c for c in raw.columns}
    
    def get_col(candidates):
        for c in candidates:
            if c in cols_lower: return cols_lower[c]
        return None

    film_year = raw[get_col(["year_film", "year film", "film_year", "year"])] if get_col(["year_film", "year"]) else None
    award_year = raw[get_col(["year_award", "ceremony"])] if get_col(["year_award", "ceremony"]) else film_year
    cat_col = get_col(["category", "award"]) or list(raw.columns)[0]
    name_col = get_col(["name", "nominee"])
    film_col = get_col(["film", "movie"])
    
    # Detección de ganador
    winner_col = next((c for c in raw.columns if "winner" in str(c).lower()), None)
    is_winner = raw[winner_col].astype(str).str.lower().isin(["true", "1", "yes", "winner"]) if winner_col else False

    df_osc = pd.DataFrame({
        "FilmYear": pd.to_numeric(film_year, errors="coerce"),
        "AwardYear": pd.to_numeric(award_year, errors="coerce"),
        "CategoryRaw": raw[cat_col].astype(str),
        "PersonName": raw[name_col].astype(str) if name_col else "",
        "Film": raw[film_col].astype(str) if film_col else "",
        "IsWinner": is_winner
    })
    
    df_osc["Category"] = df_osc["CategoryRaw"].str.strip().str.upper()
    df_osc["NormFilm"] = df_osc["Film"].apply(normalize_title)
    return df_osc

def attach_catalog_to_oscar(osc_df, my_catalog_df):
    if osc_df.empty: return osc_df
    
    out = osc_df.copy()
    if my_catalog_df is None or my_catalog_df.empty:
        for c in ["InMyCatalog", "MyRating", "MyIMDb", "CatalogURL"]: out[c] = None
        return out

    cat = my_catalog_df.copy()
    if "NormTitle" not in cat.columns: cat["NormTitle"] = cat["Title"].apply(normalize_title)
    cat["YearInt"] = pd.to_numeric(cat["Year"], errors="coerce").fillna(-1).astype(int)

    merged = out.merge(
        cat[["NormTitle", "YearInt", "Your Rating", "IMDb Rating", "URL"]],
        left_on=["NormFilm", "FilmYear"], right_on=["NormTitle", "YearInt"],
        how="left", suffixes=("", "_cat")
    )
    
    merged["InMyCatalog"] = merged["URL"].notna()
    merged["MyRating"] = merged["Your Rating"]
    merged["MyIMDb"] = merged["IMDb Rating"]
    merged["CatalogURL"] = merged["URL"]
    return merged.drop(columns=["NormTitle", "YearInt", "Your Rating", "IMDb Rating"], errors="ignore")

def fmt_year(y): return f"{int(float(y))}" if pd.notna(y) else ""
def fmt_rating(v): return f"{float(v):.1f}" if pd.notna(v) else ""

# ----------------- Inicio de App -----------------

st.sidebar.header("📂 Datos")
uploaded = st.sidebar.file_uploader("Subo mi CSV de IMDb", type=["csv"])

if uploaded:
    df = load_data(uploaded)
else:
    try:
        df = load_data("peliculas.csv")
    except FileNotFoundError:
        st.error("No se encontró 'peliculas.csv'. Sube tu archivo.")
        st.stop()

if "Title" not in df.columns:
    st.error("El CSV debe contener una columna 'Title'.")
    st.stop()

df["NormTitle"] = df["Title"].apply(normalize_title)
df["YearInt"] = pd.to_numeric(df["Year"], errors="coerce").fillna(-1).astype(int)

# ----------------- CSS -----------------
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    :root {{ --bg-primary: #020617; --text-color: #e5e7eb; --card-bg: rgba(15,23,42,0.9); --accent: #eab308; }}
    html, body, .stApp {{ background: radial-gradient(circle at top left, #0f172a 0%, #020617 40%, #000000 100%); color: var(--text-color); font-family: 'Inter', sans-serif; }}
    h1 {{ text-transform: uppercase; font-weight: 800; background: linear-gradient(90deg, var(--accent), #38bdf8); -webkit-background-clip: text; color: transparent; }}
    [data-testid="stSidebar"] > div:first-child {{ background: linear-gradient(180deg, rgba(15,23,42,0.98), rgba(15,23,42,0.90)); }}
    .movie-card {{ background: radial-gradient(circle at top left, rgba(15,23,42,0.9), rgba(15,23,42,0.85)); border-radius: 14px; padding: 14px; margin-bottom: 14px; border: 1px solid rgba(148,163,184,0.45); box-shadow: 0 18px 40px rgba(15,23,42,0.8); backdrop-filter: blur(12px); }}
    .movie-card:hover {{ transform: translateY(-4px) scale(1.01); border-color: #facc15 !important; }}
    .movie-title {{ font-weight: 600; text-transform: uppercase; margin-bottom: 2px; color: #f9fafb; }}
    .movie-sub {{ font-size: 0.78rem; line-height: 1.35; color: #cbd5f5; }}
    .movie-gallery-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 18px; }}
    .movie-poster-frame {{ width: 100%; aspect-ratio: 2/3; border-radius: 14px; overflow: hidden; margin-bottom: 8px; }}
    .movie-poster-img {{ width: 100%; height: 100%; object-fit: cover; }}
    [data-testid="stMetric"] {{ background: radial-gradient(circle at top left, rgba(15,23,42,0.95), rgba(15,23,42,0.75)); border-radius: 14px; border: 1px solid rgba(148,163,184,0.45); }}
    </style>
""", unsafe_allow_html=True)

# ----------------- Opciones Fijas -----------------
show_posters_fav, use_tmdb_gallery, show_trailers = True, True, True

# ----------------- Filtros -----------------
st.sidebar.header("🎛️ Filtros")

min_year, max_year = (int(df["Year"].min()), int(df["Year"].max())) if df["Year"].notna().any() else (0, 9999)
year_range = st.sidebar.slider("Rango de años", min_year, max_year, (min_year, max_year))

min_rating, max_rating = (int(df["Your Rating"].min()), int(df["Your Rating"].max())) if df["Your Rating"].notna().any() else (0, 10)
rating_range = st.sidebar.slider("Mi nota (Your Rating)", min_rating, max_rating, (min_rating, max_rating))

all_genres = sorted({g for sub in df["GenreList"].dropna() for g in sub if g})
selected_genres = st.sidebar.multiselect("Géneros", options=all_genres)

all_directors = sorted({d.strip() for d in df["Directors"].dropna() if str(d).strip()})
selected_directors = st.sidebar.multiselect("Directores", options=all_directors)

order_by = st.sidebar.selectbox("Ordenar por", ["Your Rating", "IMDb Rating", "Year", "Title", "Aleatorio"])
order_asc = st.sidebar.checkbox("Orden ascendente", value=False)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Opciones avanzadas")
show_awards = st.sidebar.checkbox("Consultar premios en OMDb", value=False)

st.sidebar.markdown("---")
st.sidebar.header("🧾 Versiones")
with st.sidebar.expander("Ver changelog", expanded=False):
    for ver, notes in CHANGELOG.items():
        st.markdown(f"**v{ver}**")
        for n in notes: st.markdown(f"- {n}")
        st.markdown("---")

# ----------------- Lógica de Filtrado -----------------
filtered = df.copy()
if "Year" in filtered.columns:
    filtered = filtered[(filtered["Year"] >= year_range[0]) & (filtered["Year"] <= year_range[1])]
if "Your Rating" in filtered.columns:
    filtered = filtered[(filtered["Your Rating"] >= rating_range[0]) & (filtered["Your Rating"] <= rating_range[1])]
if selected_genres:
    filtered = filtered[filtered["GenreList"].apply(lambda gl: all(g in gl for g in selected_genres))]
if selected_directors:
    filtered = filtered[filtered["Directors"].apply(lambda cell: any(d in str(cell) for d in selected_directors))]

st.caption(f"Filtros activos → Años: {year_range} | Nota: {rating_range} | Géneros: {selected_genres or 'Todos'}")

# ----------------- Búsqueda -----------------
st.markdown("## 🔎 Búsqueda en mi catálogo")
search_query = st.text_input("Buscar por título, director, género...", placeholder="Escribe...", key="busqueda_unica")

def apply_search(df_in, query):
    if not query: return df_in
    q = query.strip().lower()
    if "SearchText" not in df_in.columns: return df_in
    
    mask_exact = df_in["SearchText"].str.contains(q, na=False, regex=False)
    if len(q) < 3: return df_in[mask_exact]
    
    scored_df = df_in.copy()
    scored_df["search_score"] = scored_df["SearchText"].apply(lambda t: fuzz.partial_token_set_ratio(q, str(t)))
    return scored_df[mask_exact | (scored_df["search_score"] >= 75)].sort_values("search_score", ascending=False)

filtered_view = apply_search(filtered.copy(), search_query)

if order_by == "Aleatorio":
    filtered_view = filtered_view.sample(frac=1) if not filtered_view.empty else filtered_view
elif order_by in filtered_view.columns:
    filtered_view = filtered_view.sort_values(order_by, ascending=order_asc)

# ----------------- TABS -----------------
tab_catalog, tab_analysis, tab_afi, tab_awards, tab_what = st.tabs(
    ["🎬 Catálogo", "📊 Análisis", "🏆 Lista AFI", "🏆 Premios Óscar", "🎲 ¿Qué ver hoy?"]
)

# === TAB 1: CATÁLOGO ===
with tab_catalog:
    st.markdown("## 📈 Resumen")
    c1, c2, c3 = st.columns(3)
    c1.metric("Películas", len(filtered_view))
    c2.metric("Promedio Mi Nota", f"{filtered_view['Your Rating'].mean():.2f}" if "Your Rating" in filtered_view else "N/A")
    c3.metric("Promedio IMDb", f"{filtered_view['IMDb Rating'].mean():.2f}" if "IMDb Rating" in filtered_view else "N/A")

    st.markdown("### 📚 Tabla")
    st.dataframe(filtered_view[["Title", "Year", "Your Rating", "IMDb Rating", "Genres", "Directors"]], use_container_width=True, hide_index=True)
    st.download_button("⬇️ CSV", filtered_view.to_csv(index=False).encode("utf-8"), "peliculas.csv", "text/csv")

    st.markdown("---")
    st.markdown("## 🧱 Galería")
    
    page_size = st.slider("Películas por página", 12, 60, 24, 12)
    total_pelis = len(filtered_view)
    num_pages = max(math.ceil(total_pelis / page_size), 1)
    
    if "gallery_page" not in st.session_state: st.session_state.gallery_page = 1
    if st.session_state.gallery_page > num_pages: st.session_state.gallery_page = num_pages
    
    c_prev, c_info, c_next = st.columns([1, 2, 1])
    if c_prev.button("◀ Prev") and st.session_state.gallery_page > 1: st.session_state.gallery_page -= 1
    if c_next.button("Next ▶") and st.session_state.gallery_page < num_pages: st.session_state.gallery_page += 1
    c_info.caption(f"Página {st.session_state.gallery_page} de {num_pages}")

    start = (st.session_state.gallery_page - 1) * page_size
    page_df = filtered_view.iloc[start : start + page_size]
    
    html_cards = []
    for _, row in page_df.iterrows():
        title, year = row.get("Title"), row.get("Year")
        tmdb = get_tmdb_basic_info(title, year) if use_tmdb_gallery else None
        poster = tmdb["poster_url"] if tmdb and tmdb.get("poster_url") else None
        
        rating_col, glow_col = get_rating_colors(row.get("Your Rating"))
        
        poster_div = f"<img src='{poster}' class='movie-poster-img'>" if poster else "<div class='movie-poster-placeholder'>🎞️</div>"
        
        card = f"""
        <div class="movie-card movie-card-grid" style="border-color: {rating_col}; box-shadow: 0 0 20px {glow_col};">
            <div class="movie-poster-frame">{poster_div}</div>
            <div class="movie-title">{title} ({fmt_year(year)})</div>
            <div class="movie-sub">⭐ {fmt_rating(row.get('Your Rating'))} | IMDb: {fmt_rating(row.get('IMDb Rating'))}</div>
        </div>
        """
        html_cards.append(card)
    
    st.markdown(f"<div class='movie-gallery-grid'>{''.join(html_cards)}</div>", unsafe_allow_html=True)

# === TAB 2: ANÁLISIS ===
with tab_analysis:
    if filtered.empty:
        st.info("Sin datos.")
    else:
        st.markdown("## 📊 Estadísticas")
        c1, c2 = st.columns(2)
        
        # Gráficos
        chart_year = filtered["Year"].value_counts().sort_index().reset_index()
        chart_year.columns = ["Year", "Count"]
        c1.line_chart(chart_year.set_index("Year"))
        
        chart_rating = filtered["Your Rating"].round().value_counts().sort_index().reset_index()
        chart_rating.columns = ["Rating", "Count"]
        c2.bar_chart(chart_rating.set_index("Rating"))
        
        # Correlación
        if "Your Rating" in filtered and "IMDb Rating" in filtered:
            corr = filtered[["Your Rating", "IMDb Rating"]].corr().iloc[0,1]
            st.metric("Correlación Mi Nota vs IMDb", f"{corr:.2f}")

# === TAB 3: AFI ===
with tab_afi:
    st.markdown("## 🎬 AFI 100")
    
    afi_df = pd.DataFrame(AFI_LIST)
    afi_df["NormTitle"] = afi_df["Title"].apply(normalize_title)
    
    # Lógica de coincidencia optimizada
    matches = []
    df_catalog = df.copy() # Usar catálogo completo
    
    for idx, row in afi_df.iterrows():
        # Intento de coincidencia
        match = df_catalog[
            (df_catalog["NormTitle"] == row["NormTitle"]) | 
            (df_catalog["NormTitle"].str.contains(row["NormTitle"], regex=False))
        ]
        
        if not match.empty:
            m = match.iloc[0]
            matches.append({
                "Rank": row["Rank"], "Title": row["Title"], "Seen": True,
                "My Rating": m.get("Your Rating"), "URL": m.get("URL")
            })
        else:
            matches.append({
                "Rank": row["Rank"], "Title": row["Title"], "Seen": False,
                "My Rating": None, "URL": None
            })
            
    res_df = pd.DataFrame(matches)
    seen_count = res_df["Seen"].sum()
    st.progress(seen_count / 100)
    st.metric("Vistas", f"{seen_count}/100")
    st.dataframe(res_df, use_container_width=True)

# === TAB 4: OSCARS ===
with tab_awards:
    st.markdown("## 🏆 Oscars")
    osc_raw = load_oscar_data_from_excel("Oscar_Data_1927_today.xlsx")
    
    if osc_raw.empty:
        st.error("No se pudo cargar el Excel de Oscars.")
    else:
        osc = attach_catalog_to_oscar(osc_raw, df)
        
        years = sorted(osc["FilmYear"].dropna().unique().astype(int))
        sel_year = st.slider("Año", min(years), max(years), max(years))
        
        ff = osc[osc["FilmYear"] == sel_year]
        st.metric("Nominaciones", len(ff))
        
        st.dataframe(ff[["Category", "Film", "PersonName", "IsWinner", "MyRating"]].sort_values("IsWinner", ascending=False), use_container_width=True)

# === TAB 5: RECOMENDACIÓN ===
with tab_what:
    st.markdown("## 🎲 ¿Qué ver?")
    if st.button("Sugerir película"):
        pool = filtered_view[filtered_view["Your Rating"].isna()] if "Your Rating" in filtered_view else filtered_view
        if not pool.empty:
            rec = pool.sample(1).iloc[0]
            st.success(f"Te sugiero: **{rec['Title']}** ({fmt_year(rec.get('Year'))})")
            
            c1, c2 = st.columns([1, 2])
            tmdb = get_tmdb_basic_info(rec["Title"], rec.get("Year"))
            if tmdb and tmdb.get("poster_url"):
                c1.image(tmdb["poster_url"])
            c2.write(f"IMDb: {rec.get('IMDb Rating', 'N/A')}")
            c2.write(f"Géneros: {rec.get('Genres')}")
        else:
            st.warning("No hay películas pendientes con los filtros actuales.")

# Footer
st.markdown("---")
st.caption(f"v{APP_VERSION} · Powered by Diego Leal")
