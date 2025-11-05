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
    "Puedes filtrar por año, nota, géneros, director y usar una búsqueda global."
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

    # Duración (minutos), si existe
    if "Runtime (mins)" in df.columns:
        df["Runtime (mins)"] = pd.to_numeric(df["Runtime (mins)"], errors="coerce")
    else:
        df["Runtime (mins)"] = None

    # Genres
    if "Genres" not in df.columns:
        df["Genres"] = ""

    # Directors
    if "Directors" not in df.columns:
        df["Directors"] = ""

    # Actors (si viene en el CSV)
    if "Actors" not in df.columns:
        df["Actors"] = ""

    # Lista de géneros para filtros
    df["Genres"] = df["Genres"].fillna("")
    df["GenreList"] = df["Genres"].apply(
        lambda x: [] if pd.isna(x) or x == "" else str(x).split(", ")
    )

    # Parsear fecha calificada
    if "Date Rated" in df.columns:
        df["Date Rated"] = pd.to_datetime(df["Date Rated"], errors="coerce").dt.date

    return df


@st.cache_data
def get_poster_url(title, year=None):
    """Devuelve solo la URL del póster de TMDb."""
    if TMDB_API_KEY is None:
        return None

    if not title or pd.isna(title):
        return None

    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
    }
    if year is not None and not pd.isna(year):
        try:
            params["year"] = int(year)
        except Exception:
            pass

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

    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
    }
    if year is not None and not pd.isna(year):
        try:
            params["year"] = int(year)
        except Exception:
            pass

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

# Normalización para matching AFI y otras cosas
if "Title" in df.columns:
    df["NormTitle"] = df["Title"].apply(normalize_title)
else:
    df["NormTitle"] = ""

if "Year" in df.columns:
    df["YearInt"] = df["Year"].fillna(-1).astype(int)
else:
    df["YearInt"] = -1

# ----------------- Tema (siempre oscuro) + CSS -----------------

primary_bg = "#0e1117"
secondary_bg = "#161b22"
text_color = "#f9fafb"
card_bg = "#161b22"

st.sidebar.header("🎨 Tema")
st.sidebar.write("Modo oscuro activado 🌚")

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {primary_bg};
        color: {text_color};
    }}
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{
        color: {text_color};
    }}
    .movie-card {{
        background-color: {card_bg};
        border-radius: 0.75rem;
        padding: 0.75rem 0.9rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.12);
        border: 1px solid rgba(148,163,184,0.35);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .movie-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.25);
    }}
    .movie-title {{
        font-weight: 600;
        margin-bottom: 0.3rem;
        color: {text_color};
    }}
    .movie-sub {{
        font-size: 0.85rem;
        opacity: 0.9;
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

# ============================================================
#                     BÚSQUEDA
# ============================================================

st.markdown("## 🔎 Búsqueda")

search_query = st.text_input(
    "Buscar en títulos, directores, géneros, años o calificaciones",
    label_visibility="collapsed",
    placeholder="Escribe cualquier cosa…",
    key="busqueda"
)

st.markdown("---")

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

    filtered = filtered[filtered.apply(match_any, axis=1)]

# Orden final tras búsqueda
if order_by in filtered.columns:
    filtered = filtered.sort_values(order_by, ascending=order_asc)

# ============================================================
#               RESUMEN + TABLA / TARJETAS
# ============================================================

st.markdown("## 📈 Resumen de resultados")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Películas filtradas", len(filtered))
with col2:
    if "Your Rating" in filtered.columns and filtered["Your Rating"].notna().any():
        st.metric("Promedio de tu nota", f"{filtered['Your Rating'].mean():.2f}")
    else:
        st.metric("Promedio de tu nota", "N/A")
with col3:
    if "IMDb Rating" in filtered.columns and filtered["IMDb Rating"].notna().any():
        st.metric("Promedio IMDb", f"{filtered['IMDb Rating'].mean():.2f}")
    else:
        st.metric("Promedio IMDb", "N/A")

st.markdown("### 📚 Resultados")

cols_to_show = [
    c for c in ["Title", "Year", "Your Rating", "IMDb Rating",
                "Genres", "Directors", "Date Rated", "URL"]
    if c in filtered.columns
]

table_df = filtered[cols_to_show].copy()

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
    .set_properties(
        subset=subset_cols,
        **{"text-align": "center"}
    )
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

            your_str = fmt_rating(your_rating) if your_rating is not None else ""
            imdb_str = fmt_rating(imdb_rating) if imdb_rating is not None else ""

            card_html = f"""
            <div class="movie-card">
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
#                  ANÁLISIS Y TENDENCIAS
# ============================================================

st.markdown("---")
st.markdown("## 📊 Análisis y tendencias")

with st.expander("Ver análisis y tendencias", expanded=False):
    if filtered.empty:
        st.info("No hay datos bajo los filtros actuales para mostrar gráficos.")
    else:
        # 1) Películas por año
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

        # 2) Distribución de tu nota
        with col_b:
            st.markdown("**Distribución de tu nota (Your Rating)**")
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
                st.write("No hay notas tuyas disponibles.")

        # 3) Tendencia de tus calificaciones por año (promedio + móvil)
        st.markdown("### 📈 Tendencia de tus calificaciones por año")

        if "Year" in filtered.columns and "Your Rating" in filtered.columns:
            tmp = filtered[
                filtered["Year"].notna() &
                filtered["Your Rating"].notna()
            ].copy()
            if not tmp.empty:
                by_year_rating = (
                    tmp.groupby("Year")["Your Rating"]
                    .mean()
                    .reset_index()
                    .sort_values("Year")
                )
                by_year_rating["YearInt"] = by_year_rating["Year"].astype(int)
                by_year_rating["MA_3"] = (
                    by_year_rating["Your Rating"]
                    .rolling(window=3, min_periods=1)
                    .mean()
                )

                long_trend = by_year_rating.melt(
                    id_vars="YearInt",
                    value_vars=["Your Rating", "MA_3"],
                    var_name="Serie",
                    value_name="Rating"
                )

                trend_chart = (
                    alt.Chart(long_trend)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("YearInt:O", title="Año"),
                        y=alt.Y("Rating:Q", title="Nota media"),
                        color=alt.Color("Serie:N", title="Serie", scale=alt.Scale(
                            domain=["Your Rating", "MA_3"],
                            range=["#60a5fa", "#f97316"]
                        )),
                        tooltip=["YearInt", "Serie", "Rating"]
                    )
                    .properties(height=350)
                )
                st.altair_chart(trend_chart, use_container_width=True)
                st.caption("Línea azul: promedio anual. Naranja: promedio móvil de 3 años (suaviza la tendencia).")
            else:
                st.write("No hay suficientes datos (año + tu nota) para calcular la tendencia.")
        else:
            st.write("Faltan columnas 'Year' o 'Your Rating' para la tendencia.")

        # 4) IMDb promedio por década
        col_c, col_d = st.columns(2)
        with col_c:
            st.markdown("**IMDb promedio por década**")
            if "IMDb Rating" in filtered.columns and filtered["IMDb Rating"].notna().any():
                tmp_dec = filtered[filtered["Year"].notna()].copy()
                if not tmp_dec.empty:
                    tmp_dec["Decade"] = (tmp_dec["Year"] // 10 * 10).astype(int)
                    decade_imdb = (
                        tmp_dec.groupby("Decade")["IMDb Rating"]
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

        # 5) Desviación tu nota vs IMDb por año
        with col_d:
            st.markdown("**¿Más generoso o más crítico? (Tu nota - IMDb por año)**")
            if (
                "Your Rating" in filtered.columns
                and "IMDb Rating" in filtered.columns
            ):
                tmp_diff = filtered[
                    filtered["Year"].notna() &
                    filtered["Your Rating"].notna() &
                    filtered["IMDb Rating"].notna()
                ].copy()
                if not tmp_diff.empty:
                    tmp_diff["Diff"] = tmp_diff["Your Rating"] - tmp_diff["IMDb Rating"]
                    diff_by_year = (
                        tmp_diff.groupby("Year")["Diff"]
                        .mean()
                        .reset_index()
                        .sort_values("Year")
                    )
                    diff_by_year["YearInt"] = diff_by_year["Year"].astype(int)

                    diff_chart = (
                        alt.Chart(diff_by_year)
                        .mark_line(point=True)
                        .encode(
                            x=alt.X("YearInt:O", title="Año"),
                            y=alt.Y("Diff:Q", title="Tu nota - IMDb"),
                            tooltip=["YearInt", "Diff"]
                        )
                        .properties(height=300)
                    )
                    st.altair_chart(diff_chart, use_container_width=True)
                    st.caption(
                        "Valores por encima de 0 ⇒ sueles puntuar por encima de IMDb ese año. "
                        "Por debajo de 0 ⇒ más duro que IMDb."
                    )
                else:
                    st.write("No hay suficientes películas con tu nota e IMDb para este análisis.")
            else:
                st.write("Faltan columnas 'Your Rating' o 'IMDb Rating'.")

        # 6) Mapa de calor: tu nota media por género y década
        st.markdown("### 🎭 Mapa de calor: tu nota media por género y década")

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
                                title="Tu nota media",
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
                st.write("No hay datos suficientes (año + tu nota) para el mapa de calor.")
        else:
            st.write("Faltan columnas necesarias para el mapa de calor.")

        # 7) Qué géneros te gustan últimamente (género vs año reciente)
        st.markdown("### 🕒 Qué tipo de cine te gusta más últimamente")

        if "GenreList" in filtered.columns and "Your Rating" in filtered.columns:
            tmp = filtered.copy()
            tmp = tmp[tmp["Year"].notna() & tmp["Your Rating"].notna()]
            if not tmp.empty:
                current_year = int(pd.Timestamp.now().year)
                recent_limit = current_year - 10  # últimos 10 años
                tmp_recent = tmp[tmp["Year"] >= recent_limit]

                if not tmp_recent.empty:
                    g_exp = tmp_recent.explode("GenreList")
                    g_exp = g_exp[
                        g_exp["GenreList"].notna() &
                        (g_exp["GenreList"] != "")
                    ]

                    if not g_exp.empty:
                        top_gen_counts = (
                            g_exp["GenreList"]
                            .value_counts()
                            .head(5)
                            .index.tolist()
                        )
                        g_top = g_exp[g_exp["GenreList"].isin(top_gen_counts)]

                        genre_year = (
                            g_top
                            .groupby(["Year", "GenreList"])["Your Rating"]
                            .mean()
                            .reset_index()
                        )
                        genre_year["YearInt"] = genre_year["Year"].astype(int)

                        gy_chart = (
                            alt.Chart(genre_year)
                            .mark_line(point=True)
                            .encode(
                                x=alt.X("YearInt:O", title="Año"),
                                y=alt.Y("Your Rating:Q", title="Tu nota media"),
                                color=alt.Color("GenreList:N", title="Género"),
                                tooltip=["YearInt", "GenreList", "Your Rating"]
                            )
                            .properties(height=350)
                        )
                        st.altair_chart(gy_chart, use_container_width=True)
                        st.caption(
                            "Mostrados los 5 géneros más frecuentes en los últimos ~10 años y cómo los puntúas."
                        )
                    else:
                        st.write("No hay géneros suficientes en los últimos años para este análisis.")
                else:
                    st.write("No tienes películas recientes (últimos ~10 años) con año y nota.")
            else:
                st.write("No hay datos suficientes (año + tu nota) para este análisis.")
        else:
            st.write("Faltan columnas 'GenreList' o 'Your Rating' para este análisis.")

        # 8) Duración media por año y por género (si existe Runtime)
        st.markdown("### ⏱️ Duración media de las películas")

        if "Runtime (mins)" in filtered.columns and filtered["Runtime (mins)"].notna().any():
            col_dur1, col_dur2 = st.columns(2)

            with col_dur1:
                st.markdown("**Duración media por año**")
                tmp = filtered[
                    filtered["Year"].notna() &
                    filtered["Runtime (mins)"].notna()
                ].copy()
                if not tmp.empty:
                    dur_year = (
                        tmp.groupby("Year")["Runtime (mins)"]
                        .mean()
                        .reset_index()
                        .sort_values("Year")
                    )
                    dur_year["YearInt"] = dur_year["Year"].astype(int)

                    dur_chart = (
                        alt.Chart(dur_year)
                        .mark_line(point=True)
                        .encode(
                            x=alt.X("YearInt:O", title="Año"),
                            y=alt.Y("Runtime (mins):Q", title="Minutos de duración"),
                            tooltip=["YearInt", "Runtime (mins)"]
                        )
                        .properties(height=300)
                    )
                    st.altair_chart(dur_chart, use_container_width=True)
                else:
                    st.write("No hay datos suficientes de duración por año.")

            with col_dur2:
                st.markdown("**Duración media por género (top 10)**")
                tmp = filtered[
                    filtered["Runtime (mins)"].notna()
                ].copy()
                if "GenreList" in tmp.columns:
                    g_exp = tmp.explode("GenreList")
                    g_exp = g_exp[
                        g_exp["GenreList"].notna() &
                        (g_exp["GenreList"] != "")
                    ]
                    if not g_exp.empty:
                        dur_genre = (
                            g_exp
                            .groupby("GenreList")["Runtime (mins)"]
                            .mean()
                            .reset_index()
                        )
                        dur_genre = dur_genre.sort_values("Runtime (mins)", ascending=False).head(10)
                        dur_genre = dur_genre.set_index("GenreList")
                        st.bar_chart(dur_genre)
                    else:
                        st.write("No hay géneros suficientes con duración.")
                else:
                    st.write("No se encontró información de géneros para este análisis.")
        else:
            st.write("El CSV no tiene 'Runtime (mins)' o no hay datos suficientes de duración.")

# ============================================================
#             ANALISIS DE GUSTOS PERSONALES
# ============================================================

# (Sección ya incluida arriba)

# ============================================================
#                   LISTA AFI 100 (10th Anniversary)
# ============================================================

# (Sección ya incluida arriba)

# ============================================================
#                        FAVORITAS
# ============================================================

# (Sección ya incluida arriba)

# ============================================================
#                       GALERÍA
# ============================================================

# (Sección ya incluida arriba)

# ============================================================
#             RECOMENDACIONES POR RATINGS GLOBALES
# ============================================================

# (Sección ya incluida arriba)

# ============================================================
#                      ¿QUÉ VER HOY?
# ============================================================

# (Sección ya incluida arriba)
