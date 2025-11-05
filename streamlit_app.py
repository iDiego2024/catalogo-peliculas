import streamlit as st
import pandas as pd
import requests
import random
import altair as alt

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
#               RESUMEN + TABLA DE RESULTADOS
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

st.markdown("### 📚 Tabla de resultados")

cols_to_show = [
    c for c in ["Title", "Year", "Your Rating", "IMDb Rating",
                "Genres", "Directors", "Date Rated", "URL"]
    if c in filtered.columns
]

table_df = filtered[cols_to_show].copy()

# Funciones de formato
def fmt_year(y):
    if pd.isna(y):
        return ""
    return f"{int(y)}"

def fmt_rating(v):
    if pd.isna(v):
        return ""
    try:
        return f"{float(v):.1f}"
    except Exception:
        return v

# Diccionario de formatos y columnas a centrar
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

st.dataframe(
    styled_table,
    use_container_width=True,
    hide_index=True
)

# ============================================================
#                  ANÁLISIS Y TENDENCIAS
# ============================================================

st.markdown("---")
st.markdown("## 📊 Análisis y tendencias")

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

    # ----------------- Análisis avanzado -----------------
    st.markdown("### 🔬 Análisis avanzado (tu nota vs IMDb)")

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
            st.metric("Correlación Pearson (tu nota vs IMDb)", f"{corr:.2f}")
        else:
            st.metric("Correlación Pearson (tu nota vs IMDb)", "N/A")
        st.write(
            "Valores cercanos a 1 indican que sueles coincidir con IMDb; "
            "cercanos a 0 indican independencia; negativos, que tiendes a ir en contra."
        )

    with col_adv2:
        st.markdown("**Dispersión: IMDb vs tu nota**")
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

    # Heatmap género vs década (tu nota media)
    st.markdown("**Mapa de calor: tu nota media por género y década**")
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

# ============================================================
#             ANÁLISIS DE GUSTOS PERSONALES
# ============================================================

st.markdown("---")
st.markdown("## 🧠 Análisis de tus gustos personales")

if filtered.empty:
    st.info("No hay datos bajo los filtros actuales para analizar tus gustos.")
else:
    col_g1, col_g2 = st.columns(2)

    # 1) Media y dispersión por género
    with col_g1:
        st.markdown("### 🎭 Géneros según tu gusto")

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
                        "Géneros ordenados por tu nota media. "
                        "La desviación estándar (σ) indica cuánto varían tus notas dentro del género."
                    )
                    st.dataframe(
                        genre_stats.rename(
                            columns={
                                "GenreList": "Género",
                                "count": "Nº pelis",
                                "mean": "Tu nota media",
                                "std": "Desviación (σ)"
                            }
                        ),
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.write("No hay géneros con suficientes películas para mostrar estadísticas.")
            else:
                st.write("No hay información suficiente de géneros para analizar tus gustos.")
        else:
            st.write("Faltan columnas 'GenreList' o 'Your Rating' para este análisis.")

    # 2) Diferencia entre tu nota e IMDb
    with col_g2:
        st.markdown("### ⚖️ ¿Eres más exigente que IMDb?")

        if "Your Rating" in filtered.columns and "IMDb Rating" in filtered.columns:
            diff_df = filtered[
                filtered["Your Rating"].notna() &
                filtered["IMDb Rating"].notna()
            ].copy()
            if not diff_df.empty:
                diff_df["Diff"] = diff_df["Your Rating"] - diff_df["IMDb Rating"]

                media_diff = diff_df["Diff"].mean()
                st.metric(
                    "Diferencia media (Tu nota - IMDb)",
                    f"{media_diff:.2f}"
                )

                st.write(
                    "Valores positivos ⇒ sueles puntuar **más alto** que IMDb. "
                    "Valores negativos ⇒ sueles ser **más duro** que IMDb."
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
                st.write("No hay suficientes películas con ambas notas (tuya e IMDb) para comparar.")
        else:
            st.write("Faltan columnas 'Your Rating' o 'IMDb Rating' para comparar con IMDb.")

    # 3) Evolución de tu exigencia en el tiempo
    st.markdown("### ⏳ Evolución de tu exigencia con los años")

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

            st.write(
                "Si tu curva (Your Rating) va **bajando** con los años mientras IMDb se mantiene, "
                "es que te estás volviendo más exigente. Si sube, te estás ablandando con la edad cinéfila 😄."
            )

            tmp["Decade"] = (tmp["Year"] // 10 * 10).astype(int)
            decade_diff = (
                tmp.groupby("Decade")
                .apply(lambda g: (g["Your Rating"] - g["IMDb Rating"]).mean())
                .reset_index(name="Diff media")
                .sort_values("Decade")
            )
            if not decade_diff.empty:
                decade_diff["Decade"] = decade_diff["Decade"].astype(int)
                st.write("**Diferencia media por década (Tu nota - IMDb):**")
                st.dataframe(
                    decade_diff.rename(columns={"Decade": "Década"}),
                    hide_index=True,
                    use_container_width=True
                )
        else:
            st.write("No hay suficientes datos (año + tus notas + IMDb) para analizar tu evolución.")
    else:
        st.write("Faltan columnas 'Year', 'Your Rating' o 'IMDb Rating' para analizar tu evolución en el tiempo.")

# ============================================================
#                        FAVORITAS
# ============================================================

st.markdown("---")
st.markdown("## ⭐ Tus favoritas (nota ≥ 9) en este filtro")

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

# ============================================================
#                       GALERÍA
# ============================================================

st.markdown("---")
st.markdown("## 🎞 Galería de pósters (resultados filtrados)")

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

# ============================================================
#             RECOMENDACIONES POR RATINGS GLOBALES
# ============================================================

st.markdown("---")
st.markdown("## 🎯 Recomendaciones por ratings globales (IMDb + TMDb)")

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

# ============================================================
#                      ¿QUÉ VER HOY?
# ============================================================

st.markdown("---")
st.markdown("## 🎲 ¿Qué ver hoy? (según tu propio gusto)")

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
