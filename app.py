import streamlit as st
import pandas as pd
import requests
import random
import altair as alt
import re
import math
from urllib.parse import quote_plus
from thefuzz import fuzz

# ===================== Configuración y Constantes =====================
APP_VERSION = "1.1.8"

st.set_page_config(page_title=f"🎬 Mi catálogo · v{APP_VERSION}", layout="centered")

# Credenciales
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", None)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"
TMDB_SIMILAR = "https://api.themoviedb.org/3/movie/{movie_id}/similar"
YOUTUBE_SEARCH = "https://www.googleapis.com/youtube/v3/search"

# Lista AFI Compactada
AFI_LIST = [
    {"Rank": 1, "Title": "Citizen Kane", "Year": 1941}, {"Rank": 2, "Title": "The Godfather", "Year": 1972},
    {"Rank": 3, "Title": "Casablanca", "Year": 1942}, {"Rank": 4, "Title": "Raging Bull", "Year": 1980},
    {"Rank": 5, "Title": "Singin' in the Rain", "Year": 1952}, {"Rank": 6, "Title": "Gone with the Wind", "Year": 1939},
    {"Rank": 7, "Title": "Lawrence of Arabia", "Year": 1962}, {"Rank": 8, "Title": "Schindler's List", "Year": 1993},
    {"Rank": 9, "Title": "Vertigo", "Year": 1958}, {"Rank": 10, "Title": "The Wizard of Oz", "Year": 1939},
    {"Rank": 11, "Title": "City Lights", "Year": 1931}, {"Rank": 12, "Title": "The Searchers", "Year": 1956},
    {"Rank": 13, "Title": "Star Wars", "Year": 1977}, {"Rank": 14, "Title": "Psycho", "Year": 1960},
    {"Rank": 15, "Title": "2001: A Space Odyssey", "Year": 1968}, {"Rank": 16, "Title": "Sunset Boulevard", "Year": 1950},
    {"Rank": 17, "Title": "The Graduate", "Year": 1967}, {"Rank": 18, "Title": "The General", "Year": 1926},
    {"Rank": 19, "Title": "On the Waterfront", "Year": 1954}, {"Rank": 20, "Title": "It's a Wonderful Life", "Year": 1946},
    {"Rank": 21, "Title": "Chinatown", "Year": 1974}, {"Rank": 22, "Title": "Some Like It Hot", "Year": 1959},
    {"Rank": 23, "Title": "The Grapes of Wrath", "Year": 1940}, {"Rank": 24, "Title": "E.T. the Extra-Terrestrial", "Year": 1982},
    {"Rank": 25, "Title": "To Kill a Mockingbird", "Year": 1962}, {"Rank": 26, "Title": "Mr. Smith Goes to Washington", "Year": 1939},
    {"Rank": 27, "Title": "High Noon", "Year": 1952}, {"Rank": 28, "Title": "All About Eve", "Year": 1950},
    {"Rank": 29, "Title": "Double Indemnity", "Year": 1944}, {"Rank": 30, "Title": "Apocalypse Now", "Year": 1979},
    {"Rank": 31, "Title": "The Maltese Falcon", "Year": 1941}, {"Rank": 32, "Title": "The Godfather Part II", "Year": 1974},
    {"Rank": 33, "Title": "One Flew Over the Cuckoo's Nest", "Year": 1975}, {"Rank": 34, "Title": "Snow White and the Seven Dwarfs", "Year": 1937},
    {"Rank": 35, "Title": "Annie Hall", "Year": 1977}, {"Rank": 36, "Title": "The Bridge on the River Kwai", "Year": 1957},
    {"Rank": 37, "Title": "The Best Years of Our Lives", "Year": 1946}, {"Rank": 38, "Title": "The Treasure of the Sierra Madre", "Year": 1948},
    {"Rank": 39, "Title": "Dr. Strangelove", "Year": 1964}, {"Rank": 40, "Title": "The Sound of Music", "Year": 1965},
    {"Rank": 41, "Title": "King Kong", "Year": 1933}, {"Rank": 42, "Title": "Bonnie and Clyde", "Year": 1967},
    {"Rank": 43, "Title": "Midnight Cowboy", "Year": 1969}, {"Rank": 44, "Title": "The Philadelphia Story", "Year": 1940},
    {"Rank": 45, "Title": "Shane", "Year": 1953}, {"Rank": 46, "Title": "It Happened One Night", "Year": 1934},
    {"Rank": 47, "Title": "A Streetcar Named Desire", "Year": 1951}, {"Rank": 48, "Title": "Rear Window", "Year": 1954},
    {"Rank": 49, "Title": "Intolerance", "Year": 1916}, {"Rank": 50, "Title": "LOTR: Fellowship of the Ring", "Year": 2001},
    {"Rank": 51, "Title": "West Side Story", "Year": 1961}, {"Rank": 52, "Title": "Taxi Driver", "Year": 1976},
    {"Rank": 53, "Title": "The Deer Hunter", "Year": 1978}, {"Rank": 54, "Title": "M*A*S*H", "Year": 1970},
    {"Rank": 55, "Title": "North by Northwest", "Year": 1959}, {"Rank": 56, "Title": "Jaws", "Year": 1975},
    {"Rank": 57, "Title": "Rocky", "Year": 1976}, {"Rank": 58, "Title": "The Gold Rush", "Year": 1925},
    {"Rank": 59, "Title": "Nashville", "Year": 1975}, {"Rank": 60, "Title": "Duck Soup", "Year": 1933},
    {"Rank": 61, "Title": "Sullivan's Travels", "Year": 1941}, {"Rank": 62, "Title": "American Graffiti", "Year": 1973},
    {"Rank": 63, "Title": "Cabaret", "Year": 1972}, {"Rank": 64, "Title": "Network", "Year": 1976},
    {"Rank": 65, "Title": "The African Queen", "Year": 1951}, {"Rank": 66, "Title": "Raiders of the Lost Ark", "Year": 1981},
    {"Rank": 67, "Title": "Who's Afraid of Virginia Woolf?", "Year": 1966}, {"Rank": 68, "Title": "Unforgiven", "Year": 1992},
    {"Rank": 69, "Title": "Tootsie", "Year": 1982}, {"Rank": 70, "Title": "A Clockwork Orange", "Year": 1971},
    {"Rank": 71, "Title": "Saving Private Ryan", "Year": 1998}, {"Rank": 72, "Title": "The Shawshank Redemption", "Year": 1994},
    {"Rank": 73, "Title": "Butch Cassidy and the Sundance Kid", "Year": 1969}, {"Rank": 74, "Title": "The Silence of the Lambs", "Year": 1991},
    {"Rank": 75, "Title": "Forrest Gump", "Year": 1994}, {"Rank": 76, "Title": "All the President's Men", "Year": 1976},
    {"Rank": 77, "Title": "Modern Times", "Year": 1936}, {"Rank": 78, "Title": "The Wild Bunch", "Year": 1969},
    {"Rank": 79, "Title": "The Apartment", "Year": 1960}, {"Rank": 80, "Title": "Spartacus", "Year": 1960},
    {"Rank": 81, "Title": "Sunrise", "Year": 1927}, {"Rank": 82, "Title": "Titanic", "Year": 1997},
    {"Rank": 83, "Title": "Easy Rider", "Year": 1969}, {"Rank": 84, "Title": "A Night at the Opera", "Year": 1935},
    {"Rank": 85, "Title": "Platoon", "Year": 1986}, {"Rank": 86, "Title": "12 Angry Men", "Year": 1957},
    {"Rank": 87, "Title": "Bringing Up Baby", "Year": 1938}, {"Rank": 88, "Title": "The Sixth Sense", "Year": 1999},
    {"Rank": 89, "Title": "Swing Time", "Year": 1936}, {"Rank": 90, "Title": "Sophie's Choice", "Year": 1982},
    {"Rank": 92, "Title": "Goodfellas", "Year": 1990}, {"Rank": 93, "Title": "The French Connection", "Year": 1971},
    {"Rank": 94, "Title": "Pulp Fiction", "Year": 1994}, {"Rank": 95, "Title": "The Last Picture Show", "Year": 1971},
    {"Rank": 96, "Title": "Do the Right Thing", "Year": 1989}, {"Rank": 97, "Title": "Blade Runner", "Year": 1982},
    {"Rank": 98, "Title": "Yankee Doodle Dandy", "Year": 1942}, {"Rank": 99, "Title": "Toy Story", "Year": 1995},
    {"Rank": 100, "Title": "Ben-Hur", "Year": 1959},
]

# ===================== Funciones de Ayuda y Datos =====================

def normalize_title(s): return re.sub(r"[^a-z0-9]+", "", str(s).lower())
def fmt_year(y): return f"{int(float(y))}" if pd.notna(y) else ""
def fmt_rating(v): return f"{float(v):.1f}" if pd.notna(v) else ""

@st.cache_data
def load_data(file_buffer):
    df = pd.read_csv(file_buffer)
    # Conversión robusta
    for c in ["Your Rating", "IMDb Rating"]:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
    if "Year" in df.columns:
        df["Year"] = pd.to_numeric(df["Year"].astype(str).str.extract(r"(\d{4})")[0], errors="coerce")
    
    df["Genres"] = df.get("Genres", "").fillna("")
    df["GenreList"] = df["Genres"].apply(lambda x: str(x).split(", ") if x else [])
    df["Directors"] = df.get("Directors", "").fillna("")
    if "Date Rated" in df.columns: df["Date Rated"] = pd.to_datetime(df["Date Rated"], errors="coerce").dt.date
    
    # Texto de búsqueda (Vectorizado)
    cols = [c for c in ["Title", "Directors", "Genres", "Year"] if c in df.columns]
    df["SearchText"] = df[cols].astype(str).agg(' '.join, axis=1).str.lower()
    return df

@st.cache_data
def load_oscar_data_from_excel(path="Oscar_Data_1927_today.xlsx"):
    try: raw = pd.read_excel(path)
    except: return pd.DataFrame()
    
    # Mapeo flexible de columnas
    def get_col(candidates):
        return next((raw.columns[i] for i, c in enumerate(raw.columns) if str(c).lower() in candidates), None)

    col_film = get_col(["film", "movie", "film title"])
    col_year = get_col(["year_film", "year", "film_year"])
    col_cat = get_col(["category", "award"])
    col_name = get_col(["nominee", "name"])
    col_win = get_col(["winner", "iswinner"])

    if not (col_film and col_year and col_cat): return pd.DataFrame()

    df = pd.DataFrame({
        "Film": raw[col_film].astype(str).str.strip(),
        "FilmYear": pd.to_numeric(raw[col_year], errors="coerce"),
        "Category": raw[col_cat].astype(str).str.strip().str.upper(),
        "PersonName": raw[col_name].astype(str).str.strip() if col_name else "",
    })
    
    if col_win:
        w = raw[col_win].astype(str).str.lower()
        df["IsWinner"] = w.isin(["true", "yes", "1", "winner", "won"]) | (raw[col_win] == 1)
    else:
        df["IsWinner"] = False
        
    df["NormFilm"] = df["Film"].apply(normalize_title)
    return df

def attach_catalog_to_oscar(osc_df, cat_df):
    if osc_df.empty or cat_df.empty: return osc_df.assign(InMyCatalog=False, MyRating=None, MyIMDb=None, CatalogURL=None)
    
    c = cat_df.copy()
    c["NormTitle"] = c["Title"].apply(normalize_title)
    c["YearInt"] = c["Year"].fillna(-1).astype(int)
    
    m = osc_df.merge(c[["NormTitle", "YearInt", "Your Rating", "IMDb Rating", "URL"]], 
                     left_on=["NormFilm", "FilmYear"], right_on=["NormTitle", "YearInt"], how="left")
    
    return m.rename(columns={"Your Rating": "MyRating", "IMDb Rating": "MyIMDb", "URL": "CatalogURL"})\
            .assign(InMyCatalog=lambda x: x["CatalogURL"].notna())\
            .drop(columns=["NormTitle", "YearInt"])

# ===================== APIs =====================

@st.cache_data
def get_tmdb_basic_info(title, year=None):
    if not TMDB_API_KEY or not title: return None
    p = {"api_key": TMDB_API_KEY, "query": title}
    if year: p["year"] = int(year)
    try:
        r = requests.get(TMDB_SEARCH_URL, params=p, timeout=2).json()
        if r.get("results"):
            m = r["results"][0]
            return {"id": m["id"], "poster_url": f"{TMDB_IMAGE_BASE}{m['poster_path']}" if m.get('poster_path') else None, "vote": m.get("vote_average")}
    except: pass
    return None

@st.cache_data
def get_tmdb_providers(tmdb_id, country="CL"):
    if not TMDB_API_KEY or not tmdb_id: return None
    try:
        r = requests.get(f"https://api.themoviedb.org/3/movie/{tmdb_id}/watch/providers", params={"api_key": TMDB_API_KEY}, timeout=3).json()
        c = r.get("results", {}).get(country.upper())
        if c:
            p = set(x["provider_name"] for k in ["flatrate", "rent", "buy"] for x in c.get(k, []))
            return {"platforms": sorted(list(p)), "link": c.get("link")}
    except: pass
    return None

@st.cache_data
def get_youtube_trailer_url(title, year=None):
    if not YOUTUBE_API_KEY or not title: return None
    q = f"{title} trailer {int(year)}" if year else f"{title} trailer"
    try:
        r = requests.get(YOUTUBE_SEARCH, params={"key": YOUTUBE_API_KEY, "part": "snippet", "q": q, "maxResults": 1, "type": "video"}, timeout=3).json()
        if r.get("items"): return f"https://www.youtube.com/watch?v={r['items'][0]['id']['videoId']}"
    except: pass
    return None

@st.cache_data
def get_omdb_awards(title, year=None):
    key = st.secrets.get("OMDB_API_KEY")
    if not key or not title: return {}
    p = {"apikey": key, "t": title}
    if year: p["y"] = int(year)
    
    try:
        d = requests.get("https://www.omdbapi.com/", params=p, timeout=3).json()
        if d.get("Response") != "True": return {}
    except: return {}

    txt = d.get("Awards", "").lower()
    res = {"raw": d.get("Awards"), "palme_dor": "palme d'or" in txt}
    
    # Regex optimizado
    pats = {
        "oscars": r"won\s+(\d+)\s+oscar", "oscars_nominated": r"nominated\s+for\s+(\d+)\s+oscar",
        "emmys": r"won\s+(\d+)\s+emmy", "baftas": r"won\s+(\d+)\s+bafta",
        "golden_globes": r"won\s+(\d+)\s+golden\s+globe",
        "wins": r"(\d+)\s+win", "noms": r"(\d+)\s+nomination"
    }
    for k, rgx in pats.items():
        m = re.search(rgx, txt)
        res[k] = int(m.group(1)) if m else 0
    return res

def compute_awards_table(sub_df):
    rows = []
    for _, r in sub_df.iterrows():
        aw = get_omdb_awards(r["Title"], r.get("Year"))
        if aw: rows.append({**{"Title": r["Title"], "Year": r["Year"]}, **aw})
    return pd.DataFrame(rows)

# ===================== UI Helpers =====================

def get_rating_colors(r):
    try: v = float(r)
    except: return "#f97316", "rgba(249,115,22,0.45)"
    if v >= 9: return "#22c55e", "rgba(34,197,94,0.55)"
    if v >= 8: return "#0ea5e9", "rgba(14,165,233,0.55)"
    if v >= 7: return "#a855f7", "rgba(168,85,247,0.50)"
    return "#eab308", "rgba(234,179,8,0.45)"

def inject_css():
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    .stApp { background: radial-gradient(circle at top left, #0f172a 0%, #020617 40%, #000000 100%); font-family: 'Inter', sans-serif; color: #e5e7eb; }
    h1 { background: linear-gradient(90deg, #eab308, #38bdf8); -webkit-background-clip: text; color: transparent; font-weight: 800; }
    [data-testid="stSidebar"] { background: rgba(15,23,42,0.98); border-right: 1px solid rgba(148,163,184,0.2); }
    .movie-card { background: rgba(15,23,42,0.9); border-radius: 14px; padding: 12px; border: 1px solid rgba(148,163,184,0.4); margin-bottom: 14px; transition: transform 0.2s; }
    .movie-card:hover { transform: translateY(-4px); border-color: #facc15 !important; }
    .movie-poster-frame { width: 100%; aspect-ratio: 2/3; border-radius: 10px; overflow: hidden; background: #000; margin-bottom: 8px; }
    .movie-poster-img { width: 100%; height: 100%; object-fit: cover; }
    .movie-title { font-weight: 700; font-size: 0.9rem; color: #fff; margin-bottom: 4px; }
    .movie-sub { font-size: 0.8rem; color: #cbd5f5; line-height: 1.3; }
    [data-testid="stMetric"] { background: rgba(15,23,42,0.8); border: 1px solid rgba(148,163,184,0.3); border-radius: 12px; }
    </style>""", unsafe_allow_html=True)

def build_card_html(row, is_oscar_mode=False, oscar_meta=None):
    # Meta extraction
    title = row.get("Title") or row.get("Film")
    year = row.get("Year") or row.get("FilmYear")
    my_r = row.get("Your Rating") if "Your Rating" in row else row.get("MyRating")
    imdb_r = row.get("IMDb Rating") if "IMDb Rating" in row else row.get("MyIMDb")
    
    # Visuals
    color, glow = get_rating_colors(my_r if pd.notna(my_r) else imdb_r)
    if is_oscar_mode and oscar_meta.get("winner"): color, glow = "#22c55e", "rgba(34,197,94,0.7)"
    
    tmdb = get_tmdb_basic_info(title, year)
    poster = tmdb.get("poster_url") if tmdb else None
    
    img_div = f"<img src='{poster}' class='movie-poster-img'>" if poster else "<div style='height:100%;display:flex;align-items:center;justify-content:center;color:#666'>🎞️</div>"
    
    extras = ""
    if is_oscar_mode:
        if oscar_meta.get("winner"): extras += "<span style='color:#bbf7d0;border:1px solid #22c55e;padding:2px 6px;border-radius:8px;font-size:0.7em'>WINNER 🏆</span><br>"
        extras += f"<span style='font-size:0.8em;color:#9ca3af'>{oscar_meta.get('cat')}</span><br>"
        if row.get("InMyCatalog"): extras += f"<span style='color:#fef9c3;font-size:0.75em'>En catálogo (Nota: {fmt_rating(my_r)})</span>"
    else:
        extras += f"Mi nota: {fmt_rating(my_r)} | IMDb: {fmt_rating(imdb_r)}<br>"
        if tmdb: extras += f"TMDb: {fmt_rating(tmdb.get('vote'))}<br>"
    
    return f"""
    <div class="movie-card movie-card-grid" style="border-color:{color};box-shadow:0 0 15px {glow}">
        <div class="movie-poster-frame">{img_div}</div>
        <div class="movie-title">{title} ({fmt_year(year)})</div>
        <div class="movie-sub">{extras}</div>
    </div>
    """

# ===================== MAIN =====================

st.title("🎥 Mi catálogo de películas (IMDb)")
inject_css()

# --- Sidebar ---
st.sidebar.header("📂 Datos")
upl = st.sidebar.file_uploader("Subir CSV", type=["csv"])
try:
    df = load_data(upl if upl else "peliculas.csv")
    df["NormTitle"] = df["Title"].apply(normalize_title)
    df["YearInt"] = pd.to_numeric(df["Year"], errors="coerce").fillna(-1).astype(int)
except:
    st.error("Sube 'peliculas.csv' o cárgalo en la barra lateral."); st.stop()

# --- Filtros ---
st.sidebar.header("🎛️ Filtros")
ymin, ymax = int(df["Year"].min()), int(df["Year"].max())
yr = st.sidebar.slider("Años", ymin, ymax, (ymin, ymax))

genres = sorted(set(g for s in df["GenreList"] for g in s))
sel_g = st.sidebar.multiselect("Géneros", genres)

fil = df[(df["Year"].between(yr[0], yr[1]))].copy()
if sel_g: fil = fil[fil["GenreList"].apply(lambda x: all(g in x for g in sel_g))]

if "Your Rating" in fil.columns:
    rmin, rmax = int(fil["Your Rating"].min()), int(fil["Your Rating"].max())
    rr = st.sidebar.slider("Mi Nota", rmin, rmax, (rmin, rmax))
    fil = fil[fil["Your Rating"].between(rr[0], rr[1])]

check_awards = st.sidebar.checkbox("Consultar OMDb (Lento)", value=False)

# --- Búsqueda ---
st.markdown("## 🔎 Búsqueda")
q = st.text_input("Buscar...", key="search").strip().lower()
if q:
    mask = fil["SearchText"].str.contains(q, na=False)
    if len(q) >= 3: mask |= fil["SearchText"].apply(lambda x: fuzz.partial_token_set_ratio(q, x) >= 75)
    fil = fil[mask]

# --- TABS ---
t1, t2, t3, t4, t5 = st.tabs(["Catálogo", "Análisis", "AFI List", "Premios Óscar", "¿Qué ver?"])

with t1:
    st.metric("Películas", len(fil))
    st.dataframe(fil[["Title", "Year", "Your Rating", "Genres", "Directors"]], use_container_width=True, hide_index=True)
    
    st.markdown("### Galería Visual")
    page_size = 20
    page = st.number_input("Página", 1, max(1, math.ceil(len(fil)/page_size)), 1)
    chunk = fil.iloc[(page-1)*page_size : page*page_size]
    
    cols = st.columns(4)
    for i, (_, row) in enumerate(chunk.iterrows()):
        with cols[i%4]:
            st.markdown(build_card_html(row), unsafe_allow_html=True)

with t2:
    if not fil.empty:
        c1, c2 = st.columns(2)
        c1.line_chart(fil["Year"].value_counts().sort_index())
        if "Your Rating" in fil.columns: c2.bar_chart(fil["Your Rating"].value_counts().sort_index())
        
        st.markdown("#### Análisis vs IMDb")
        if "IMDb Rating" in fil.columns:
            fil["Diff"] = fil["Your Rating"] - fil["IMDb Rating"]
            st.metric("Diferencia Media", f"{fil['Diff'].mean():.2f}")
            st.bar_chart(fil["Diff"].round(1).value_counts())

with t3:
    st.markdown("### Progreso AFI 100")
    afi = pd.DataFrame(AFI_LIST)
    afi["Norm"] = afi["Title"].apply(normalize_title)
    lookup = df.set_index("NormTitle")["Your Rating"].to_dict()
    afi["MyRating"] = afi["Norm"].map(lookup)
    afi["Seen"] = afi["MyRating"].notna()
    
    st.progress(afi["Seen"].mean())
    st.dataframe(afi[["Rank", "Title", "Year", "Seen", "MyRating"]], use_container_width=True)

with t4:
    st.markdown("### 🏆 Oscars (Excel)")
    osc = load_oscar_data_from_excel()
    if osc.empty:
        st.warning("Falta 'Oscar_Data_1927_today.xlsx'")
    else:
        full_osc = attach_catalog_to_oscar(osc, df)
        yrs = sorted(full_osc["FilmYear"].dropna().unique(), reverse=True)
        sy = st.selectbox("Año Ceremonia", yrs)
        
        sub = full_osc[full_osc["FilmYear"] == sy]
        if st.checkbox("Solo Ganadores"): sub = sub[sub["IsWinner"]]
        
        st.dataframe(sub[["Category", "Film", "PersonName", "IsWinner", "MyRating"]], use_container_width=True)
        
        st.markdown("#### Galería")
        gcols = st.columns(4)
        for i, (_, row) in enumerate(sub.head(24).iterrows()):
            with gcols[i%4]:
                st.markdown(build_card_html(row, True, {"winner": row["IsWinner"], "cat": row["Category"]}), unsafe_allow_html=True)

with t5:
    st.markdown("### 🎲 ¿Qué ver hoy?")
    if st.button("Sugerir Película"):
        pool = fil[fil["Your Rating"].isna()] if st.checkbox("Solo no vistas") else fil
        if not pool.empty:
            pick = pool.sample(1).iloc[0]
            st.success(f"Te recomiendo: **{pick['Title']}** ({int(pick['Year'])})")
            c1, c2 = st.columns([1,3])
            tmdb = get_tmdb_basic_info(pick["Title"], pick["Year"])
            if tmdb and tmdb.get("poster_url"): c1.image(tmdb["poster_url"])
            c2.write(f"IMDb: {pick.get('IMDb Rating', 'N/A')}")
            c2.write(f"Géneros: {pick['Genres']}")
            
            prov = get_tmdb_providers(tmdb["id"]) if tmdb else None
            if prov and prov.get("platforms"): c2.info(f"Disponible en: {', '.join(prov['platforms'])}")
        else:
            st.warning("No hay películas con esos filtros.")

st.markdown("---")
st.caption(f"v{APP_VERSION} Optimized")
