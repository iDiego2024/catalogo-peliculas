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

# ----------------- Opciones de visualización -----------------

st.sidebar.header("🖼️ Opciones de visualización")
show_posters_fav = st.sidebar.checkbox(
    "Mostrar pósters TMDb en favoritas (nota ≥ 9)",
    value=True  # activado por defecto
)
show_gallery = st.sidebar.checkbox(
    "Mostrar galería de pósters para resultados filtrados",
    value=True  # activado por defecto
)

# ----------------- Filtros -----------------

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

# ----------------- Aplicar filtros -----------------

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

# ----------------- Métricas -----------------

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

# ----------------- Buscador -----------------

st.markdown("### 🔎 Buscar por título")

search_title = st.text_input(
    "Buscar en título / título original",
    label_visibility="collapsed",
    placeholder="Escribe parte del título…",
    key="busqueda_titulo"
)

st.markdown("---")

title_cols = [c for c in ["Title", "Original Title"] if c in filtered.columns]
if search_title and title_cols:
    mask = False
    for c in title_cols:
        mask = mask | filtered[c].astype(str).str.contains(
            search_title, case=False, na=False
        )
    filtered = filtered[mask]

if order_by in filtered.columns:
    filtered = filtered.sort_values(order_by, ascending=order_asc)

# ----------------- Tabla principal -----------------

st.subheader("📚 Resultados")

cols_to_show = [
    c for c in ["Title", "Year", "Your Rating", "IMDb Rating", "Genres", "Directors", "Date Rated", "URL"]
    if c in filtered.columns
]

table_df = filtered[cols_to_show].copy()

# Formato visual
if "Year" in table_df.columns:
    table_df["Year"] = table_df["Year"].apply(lambda y: "" if pd.isna(y) else str(int(y)))
for col in ["Your Rating", "IMDb Rating"]:
    if col in table_df.columns:
        table_df[col] = table_df[col].apply(lambda v: f"{v:.1f}" if pd.notna(v) else "")

# Centrado global de celdas de tablas
st.markdown(
    """
    <style>
        table, th, td {
            text-align: center !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True
)

# ----------------- ReporterÍa / análisis -----------------

st.markdown("---")
st.subheader("📊 Análisis y tendencias")

if filtered.empty:
    st.info("No hay datos bajo los filtros actuales para mostrar gráficos.")
else:
    # Películas por año
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

    # Distribución de tu nota
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

    # Top géneros y IMDb por década
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

# ----------------- Favoritas con póster -----------------

st.markdown("---")
st.subheader("⭐ Tus favoritas (nota ≥ 9) en este filtro")

if "Your Rating" in filtered.columns:
    fav = filtered[filtered["Your Rating"] >= 9].copy()
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

            etiqueta = f"{int(nota)}/10 — {titulo}"
            if pd.notna(year):
                etiqueta += f" ({int(year)})"

            with st.expander(etiqueta):
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
                    st.write(f"**Géneros:** {genres}")
                    st.write(f"**Director(es):** {directors}")
                    if pd.notna(imdb_rating):
                        st.write(f"**IMDb:** {imdb_rating}")
                    if isinstance(url, str) and url.startswith("http"):
                        st.write(f"[Ver en IMDb]({url})")
    else:
        st.write("No hay películas con nota ≥ 9 bajo estos filtros.")
else:
    st.write("No se encontró la columna 'Your Rating' en el CSV.")

# ----------------- Galería tipo Netflix -----------------

st.markdown("---")
st.subheader("🎞 Galería de pósters (resultados filtrados)")

if show_gallery:
    if TMDB_API_KEY is None:
        st.warning("No hay TMDB_API_KEY configurada en Secrets, no puedo cargar pósters.")
    elif filtered.empty:
        st.info("No hay resultados con los filtros actuales.")
    else:
        gal = filtered.copy()

        if "Your Rating" in gal.columns:
            gal = gal.sort_values(
                ["Your Rating", "Year"],
                ascending=[False, True]
            )

        gal = gal.head(24)

        st.write(f"Mostrando hasta {len(gal)} pósters de las películas filtradas.")

        cols = st.columns(4)

        for i, (_, row) in enumerate(gal.iterrows()):
            col = cols[i % 4]
            with col:
                titulo = row.get("Title", "Sin título")
                year = row.get("Year", "")
                nota = row.get("Your Rating", "")
                imdb_rating = row.get("IMDb Rating", "")
                url = row.get("URL", "")

                poster_url = get_poster_url(titulo, year)
                if isinstance(poster_url, str) and poster_url:
                    st.image(poster_url)
                else:
                    st.write("Sin póster")

                if pd.notna(year):
                    st.markdown(f"**{titulo}** ({int(year)})")
                else:
                    st.markdown(f"**{titulo}**")

                if pd.notna(nota):
                    st.write(f"⭐ Tu nota: {nota}")
                if pd.notna(imdb_rating):
                    st.write(f"IMDb: {imdb_rating}")
                if isinstance(url, str) and url.startswith("http"):
                    st.write(f"[IMDb]({url})")
else:
    st.info("Desactiva la galería desde la barra lateral si no quieres ver esta sección.")

# ----------------- Recomendaciones por ratings globales -----------------

st.markdown("---")
st.subheader("🎯 Recomendaciones por ratings globales (IMDb + TMDb)")

col_a2, col_b2 = st.columns(2)
with col_a2:
    min_imdb_global = st.slider("Mínimo IMDb Rating", 0.0, 10.0, 8.0, 0.1)
with col_b2:
    min_tmdb_global = st.slider("Mínimo TMDb Rating", 0.0, 10.0, 7.5, 0.1)

if st.button("Generar recomendaciones globales"):
    if TMDB_API_KEY is None:
        st.warning("No hay TMDB_API_KEY configurada en Secrets, no puedo consultar TMDb.")
    else:
        pool = filtered.copy()
        if "IMDb Rating" in pool.columns:
            pool = pool[pool["IMDb Rating"].notna() & (pool["IMDb Rating"] >= min_imdb_global)]
        else:
            pool = pool.iloc[0:0]

        if pool.empty:
            st.warning("No hay películas con IMDb Rating suficiente bajo los filtros actuales.")
        else:
            pool = pool.sort_values("IMDb Rating", ascending=False).head(40)

            recomendaciones = []
            for _, row in pool.iterrows():
                titulo = row.get("Title", "Sin título")
                year = row.get("Year", None)
                tmdb_rating = get_tmdb_vote_average(titulo, year)
                if tmdb_rating is None:
                    continue
                if tmdb_rating >= min_tmdb_global:
                    recomendaciones.append((row, tmdb_rating))
                if len(recomendaciones) >= 10:
                    break

            if not recomendaciones:
                st.info("No encontré películas que estén altas tanto en IMDb como en TMDb con esos umbrales.")
            else:
                for row, tmdb_rating in recomendaciones:
                    titulo = row.get("Title", "Sin título")
                    year = row.get("Year", "")
                    your_rating = row.get("Your Rating", "")
                    imdb_rating = row.get("IMDb Rating", "")
                    genres = row.get("Genres", "")
                    url = row.get("URL", "")

                    col_img, col_info = st.columns([1, 3])
                    with col_img:
                        poster_url = get_poster_url(titulo, year)
                        if isinstance(poster_url, str) and poster_url:
                            st.image(poster_url)
                        else:
                            st.write("Sin póster")

                    with col_info:
                        if pd.notna(year):
                            st.markdown(f"**{titulo}** ({int(year)})")
                        else:
                            st.markdown(f"**{titulo}**")

                        if pd.notna(your_rating):
                            st.write(f"⭐ Tu nota: {your_rating}")
                        if pd.notna(imdb_rating):
                            st.write(f"IMDb: {imdb_rating}")
                        st.write(f"TMDb: {tmdb_rating:.1f}")
                        if isinstance(genres, str) and genres:
                            st.write(f"**Géneros:** {genres}")
                        if isinstance(url, str) and url.startswith("http"):
                            st.write(f"[Ver en IMDb]({url})")

# ----------------- ¿Qué ver hoy? -----------------

st.markdown("---")
st.subheader("🎲 ¿Qué ver hoy? (según tu propio gusto)")

modo = st.selectbox(
    "Modo de recomendación",
    [
        "Entre todas las películas filtradas",
        "Solo favoritas (nota ≥ 9)",
        "Entre tus 8–10 de los últimos 20 años"
    ]
)

if st.button("Recomendar una película"):
    pool = filtered.copy()

    if modo == "Solo favoritas (nota ≥ 9)":
        if "Your Rating" in pool.columns:
            pool = pool[pool["Your Rating"] >= 9]
        else:
            pool = pool.iloc[0:0]

    elif modo == "Entre tus 8–10 de los últimos 20 años":
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

        col_img, col_info = st.columns([1, 3])

        with col_img:
            poster_url = get_poster_url(titulo, year)
            if isinstance(poster_url, str) and poster_url:
                st.image(poster_url)
            else:
                st.write("Sin póster")

        with col_info:
            if pd.notna(year):
                st.markdown(f"## {titulo} ({int(year)})")
            else:
                st.markdown(f"## {titulo}")

            if pd.notna(nota):
                st.write(f"⭐ Tu nota: {nota}")
            if pd.notna(imdb_rating):
                st.write(f"IMDb: {imdb_rating}")
            st.write(f"**Géneros:** {genres}")
            st.write(f"**Director(es):** {directors}")
            if isinstance(url, str) and url.startswith("http"):
                st.write(f"[Ver en IMDb]({url})")
