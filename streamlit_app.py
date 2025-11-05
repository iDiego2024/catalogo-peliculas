import streamlit as st
import pandas as pd
import requests
import random

# ----------------- Configuración general -----------------

st.set_page_config(
    page_title="🎬 Catálogo de Películas",
    layout="wide"
)

st.title("🎥 Mi catálogo de películas (IMDb)")
st.write(
    "App basada en tu export de IMDb. "
    "Puedes filtrar por año, nota, géneros, director y buscar por título."
)

# ----------------- Config TMDb -----------------

TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"


# ----------------- Funciones auxiliares -----------------


@st.cache_data
def load_data(file_path_or_buffer):
    df = pd.read_csv(file_path_or_buffer)

    # Asegurar tipos básicos

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

    # Year: extraer solo un año de 4 dígitos aunque venga sucio (ej. "2019–2020", "2019,", etc.)
    if "Year" in df.columns:
        df["Year"] = (
            df["Year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]  # primer grupo de 4 dígitos
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


@st.cache_data
def get_poster_url(title, year=None):
    """Devuelve solo la URL del póster de TMDb."""
    if TMDB_API_KEY is None:
        return None  # No hay API key configurada

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
        df = load_data("peliculas.csv")  # archivo en el repo
    except FileNotFoundError:
        st.error(
            "No se encontró 'peliculas.csv' en el repositorio y no se subió archivo.\n\n"
            "Sube tu CSV de IMDb desde la barra lateral para continuar."
        )
        st.stop()

# Checkbox para controlar los pósters y galería
st.sidebar.header("🖼️ Opciones de visualización")
show_posters_fav = st.sidebar.checkbox(
    "Mostrar pósters TMDb en favoritas (nota ≥ 9)",
    value=False
)
show_gallery = st.sidebar.checkbox(
    "Mostrar galería de pósters para resultados filtrados",
    value=False
)

# ----------------- Filtros en sidebar -----------------

st.sidebar.header("🎛️ Filtros")

# Año
if df["Year"].notna().any():
    min_year = int(df["Year"].min())
    max_year = int(df["Year"].max())
    year_range = st.sidebar.slider(
        "Rango de años",
        min_year, max_year,
        (min_year, max_year)
    )
else:
    year_range = (0, 9999)

# Tu nota
if df["Your Rating"].notna().any():
    min_rating = int(df["Your Rating"].min())
    max_rating = int(df["Your Rating"].max())
    rating_range = st.sidebar.slider(
        "Tu nota (Your Rating)",
        min_rating, max_rating,
        (min_rating, max_rating)
    )
else:
    rating_range = (0, 10)

# Géneros
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

# Directores
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

# Orden
order_by = st.sidebar.selectbox(
    "Ordenar por",
    ["Your Rating", "IMDb Rating", "Year", "Title"]
)
order_asc = st.sidebar.checkbox("Orden ascendente", value=False)

# ----------------- Aplicar filtros básicos -----------------

filtered = df.copy()

# Año
if "Year" in filtered.columns:
    filtered = filtered[
        (filtered["Year"] >= year_range[0]) &
        (filtered["Year"] <= year_range[1])
    ]

# Nota
if "Your Rating" in filtered.columns:
    filtered = filtered[
        (filtered["Your Rating"] >= rating_range[0]) &
        (filtered["Your Rating"] <= rating_range[1])
    ]

# Géneros (todas las seleccionadas deben estar en la lista de la peli)
if selected_genres:
    filtered = filtered[
        filtered["GenreList"].apply(
            lambda gl: all(g in gl for g in selected_genres)
        )
    ]

# Directores
if selected_directors:
    filtered = filtered[filtered["Directors"].isin(selected_directors)]

# ----------------- Métricas rápidas -----------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Películas filtradas", len(filtered))

with col2:
    if "Your Rating" in filtered.columns and filtered["Your Rating"].notna().any():
        st.metric(
            "Promedio de tu nota",
            f"{filtered['Your Rating'].mean():.2f}"
        )
    else:
        st.metric("Promedio de tu nota", "N/A")

with col3:
    if "IMDb Rating" in filtered.columns and filtered["IMDb Rating"].notna().any():
        st.metric(
            "Promedio IMDb",
            f"{filtered['IMDb Rating'].mean():.2f}"
        )
    else:
        st.metric("Promedio IMDb", "N/A")

# ----------------- Buscador (alineado a la izquierda) -----------------

st.markdown("### 🔎 Buscar por título")

search_title = st.text_input(
    "Buscar en título / título original",
    label_visibility="collapsed",
    placeholder="Escribe parte del título…",
    key="busqueda_titulo"
)

st.markdown("---")

# ----------------- Aplicar búsqueda por texto -----------------

title_cols = [c for c in ["Title", "Original Title"] if c in filtered.columns]

if search_title and title_cols:
    mask = False
    for c in title_cols:
        mask = mask | filtered[c].astype(str).str.contains(
            search_title, case=False, na=False
        )
    filtered = filtered[mask]

# Orden final
if order_by in filtered.columns:
    filtered = filtered.sort_values(order_by, ascending=order_asc)

# ----------------- Tabla principal -----------------

st.subheader("📚 Resultados")

columns_to_show = []
for c in ["Title", "Year", "Your Rating", "IMDb Rating",
          "Genres", "Directors", "Date Rated", "URL"]:
    if c in filtered.columns:
        columns_to_show.append(c)

# Copia para formateo de visualización
table_df = filtered[columns_to_show].copy()

# Formatear Year como texto sin separador de miles
if "Year" in table_df.columns:
    table_df["Year"] = table_df["Year"].apply(
        lambda y: "" if pd.isna(y) else str(int(y))
    )

# Centramos las columnas numéricas
styled_table = table_df.style.set_properties(
    subset=["Year", "Your Rating", "IMDb Rating"],
    **{"text-align": "center"}
).set_table_styles(
    [
        {"selector": "th.col_heading", "props": [("text-align", "center")]},
        {"selector": "td", "props": [("vertical-align", "middle")]}
    ]
)

st.dataframe(
    styled_table,
    use_container_width=True,
    hide_index=True
)
