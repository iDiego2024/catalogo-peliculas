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
            f"{filtered['Your Rating"].mean():.2f}"
        )
    else:
        st.metric("Promedio de tu nota", "N/A")

with col3:
    if "IMDb Rating" in filtered.columns and filtered["IMDb Rating"].notna().any():
        st.metric(
            "Promedio IMDb",
            f"{filtered['IMDb Rating"].mean():.2f}"
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

st.dataframe(
    filtered[columns_to_show],
    use_container_width=True,
    hide_index=True
)

# ----------------- Favoritas con póster -----------------

st.markdown("---")
st.subheader("⭐ Tus favoritas (nota ≥ 9) en este filtro")

if "Your Rating" in filtered.columns:
    fav = filtered[filtered["Your Rating"] >= 9].copy()
    if not fav.empty:
        fav = fav.sort_values(["Your Rating", "Year"], ascending=[False, True])

        # límite para no hacer demasiadas llamadas a la API
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

        # Orden por tu nota (desc) y año
        if "Your Rating" in gal.columns:
            gal = gal.sort_values(
                ["Your Rating", "Year"],
                ascending=[False, True]
            )

        gal = gal.head(24)  # máximo 24 pósters

        st.write(f"Mostrando hasta {len(gal)} pósters de las películas filtradas.")

        cols = st.columns(4)  # 4 columnas tipo grid

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

                # Texto bajo el póster
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
    st.info("Activa 'Mostrar galería de pósters para resultados filtrados' en la barra lateral para ver la vista tipo Netflix.")

# ----------------- Recomendaciones por ratings globales -----------------

st.markdown("---")
st.subheader("🎯 Recomendaciones por ratings globales (IMDb + TMDb)")

col_a, col_b = st.columns(2)
with col_a:
    min_imdb_global = st.slider("Mínimo IMDb Rating", 0.0, 10.0, 8.0, 0.1)
with col_b:
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
            pesos = None  # selección uniforme

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
