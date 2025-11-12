# app.py
# 🎬 Mi catálogo de Películas (IMDb) + Premios Óscar
# Versión visual: secciones, premios, correcciones de año y rankings
# ---------------------------------------------------------------

import streamlit as st
import pandas as pd
import requests
import random
import altair as alt
import re
import math
from urllib.parse import quote_plus

# =========================
# Config general + versión
# =========================
APP_VERSION = "1.2.0"

st.set_page_config(
    page_title="🎬 Mi catálogo de Películas",
    layout="centered"
)
st.title("🎥 Mi catálogo de películas (IMDb)")

# =========================
# APIs externas (opcionales)
# =========================
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", None)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"
TMDB_SIMILAR_URL_TEMPLATE = "https://api.themoviedb.org/3/movie/{movie_id}/similar"

YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", None)
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# =========================
# Utilidades
# =========================
def normalize_title(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

def fmt_year(y):
    """Devuelve año como texto sin separadores (evita '2,023')."""
    if pd.isna(y):
        return ""
    try:
        return f"{int(float(y))}"
    except Exception:
        return str(y)

def fmt_rating(v):
    if pd.isna(v):
        return ""
    try:
        return f"{float(v):.1f}"
    except Exception:
        return str(v)

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

# =========================
# Carga catálogo IMDb
# =========================
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

    # Prepara texto búsqueda
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

# =========================
# Carga de archivo(s)
# =========================
st.sidebar.header("📂 Datos")
uploaded = st.sidebar.file_uploader(
    "Sube tu CSV de IMDb (si no, se usa peliculas.csv del repo)",
    type=["csv"]
)
if uploaded is not None:
    df = load_data(uploaded)
else:
    try:
        df = load_data("peliculas.csv")
    except FileNotFoundError:
        st.error("No se encontró 'peliculas.csv' en el repositorio y no se subió archivo.")
        st.stop()

if "Title" not in df.columns:
    st.error("El CSV debe contener una columna 'Title'.")
    st.stop()

df["NormTitle"] = df["Title"].apply(normalize_title)
df["YearInt"] = df["Year"].fillna(-1).astype(int) if "Year" in df.columns else -1

# =========================
# Opciones UI generales
# =========================
st.sidebar.header("🖼️ Opciones")
show_trailers = st.sidebar.checkbox("Mostrar tráiler de YouTube (si hay API key)", True)

# =========================
# Filtros catálogo
# =========================
st.sidebar.header("🎛️ Filtros catálogo")
if df["Year"].notna().any():
    min_year = int(df["Year"].min())
    max_year = int(df["Year"].max())
    year_range = st.sidebar.slider("Rango de años", min_year, max_year, (min_year, max_year))
else:
    year_range = (0, 9999)

if df["Your Rating"].notna().any():
    min_rating = int(df["Your Rating"].min())
    max_rating = int(df["Your Rating"].max())
    rating_range = st.sidebar.slider("Mi nota (Your Rating)", min_rating, max_rating, (min_rating, max_rating))
else:
    rating_range = (0, 10)

all_genres = sorted(set(g for sub in df["GenreList"].dropna() for g in sub if g))
selected_genres = st.sidebar.multiselect("Géneros (todas deben estar presentes)", options=all_genres)

all_directors = sorted(set(d.strip() for d in df["Directors"].dropna() if str(d).strip() != ""))
selected_directors = st.sidebar.multiselect("Directores", options=all_directors)

order_by = st.sidebar.selectbox("Ordenar por", ["Your Rating", "IMDb Rating", "Year", "Title", "Aleatorio"])
order_asc = st.sidebar.checkbox("Orden ascendente", value=False)

# =========================
# Aplicar filtros catálogo
# =========================
filtered = df.copy()
if "Year" in filtered.columns:
    filtered = filtered[(filtered["Year"] >= year_range[0]) & (filtered["Year"] <= year_range[1])]
if "Your Rating" in filtered.columns:
    filtered = filtered[(filtered["Your Rating"] >= rating_range[0]) & (filtered["Your Rating"] <= rating_range[1])]
if selected_genres:
    filtered = filtered[filtered["GenreList"].apply(lambda gl: all(g in gl for g in selected_genres))]
if selected_directors:
    def _matches_any_director(cell):
        if pd.isna(cell):
            return False
        dirs = [d.strip() for d in str(cell).split(",") if d.strip()]
        return any(d in dirs for d in selected_directors)
    filtered = filtered[filtered["Directors"].apply(_matches_any_director)]

st.caption(
    f"Filtros → Años: {year_range[0]}–{year_range[1]} | "
    f"Mi nota: {rating_range[0]}–{rating_range[1]} | "
    f"Géneros: {', '.join(selected_genres) if selected_genres else 'Todos'} | "
    f"Directores: {', '.join(selected_directors) if selected_directors else 'Todos'}"
)

# =========================
# Helpers de búsqueda
# =========================
st.markdown("## 🔎 Búsqueda en mi catálogo (sobre los filtros actuales)")
search_query = st.text_input("Buscar por título, director, género, año o calificaciones", key="busqueda_unica",
                             placeholder="Escribe cualquier cosa…")

def apply_search(df_in, query):
    if not query:
        return df_in
    q = query.strip().lower()
    if "SearchText" not in df_in.columns:
        return df_in
    return df_in[df_in["SearchText"].str.contains(q, na=False, regex=False)]

filtered_view = apply_search(filtered.copy(), search_query)

if order_by == "Aleatorio":
    if not filtered_view.empty:
        filtered_view = filtered_view.sample(frac=1, random_state=None)
elif order_by in filtered_view.columns:
    filtered_view = filtered_view.sort_values(order_by, ascending=order_asc)

# =========================
# TABs principales
# =========================
tab_catalog, tab_analysis, tab_awards, tab_what = st.tabs(
    ["🎬 Catálogo", "📊 Análisis", "🏆 Premios Óscar", "🎲 ¿Qué ver hoy?"]
)

# ============================================================
# TAB 1: CATÁLOGO
# ============================================================
with tab_catalog:
    st.markdown("## 📚 Resultados")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Películas tras filtros + búsqueda", len(filtered_view))
    with col2:
        st.metric("Promedio de mi nota", f"{filtered_view['Your Rating'].mean():.2f}" if filtered_view["Your Rating"].notna().any() else "N/A")
    with col3:
        st.metric("Promedio IMDb", f"{filtered_view['IMDb Rating'].mean():.2f}" if filtered_view["IMDb Rating"].notna().any() else "N/A")

    cols_to_show = [c for c in ["Title", "Year", "Your Rating", "IMDb Rating", "Genres", "Directors", "Date Rated", "URL"] if c in filtered_view.columns]
    table_df = filtered_view[cols_to_show].copy()
    display_df = table_df.copy()
    if "Year" in display_df.columns:
        display_df["Year"] = display_df["Year"].apply(fmt_year)
    if "Your Rating" in display_df.columns:
        display_df["Your Rating"] = display_df["Your Rating"].apply(fmt_rating)
    if "IMDb Rating" in display_df.columns:
        display_df["IMDb Rating"] = display_df["IMDb Rating"].apply(fmt_rating)

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv_filtrado = table_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar resultados filtrados (CSV)", data=csv_filtrado, file_name="mis_peliculas_filtradas.csv", mime="text/csv")

# ============================================================
# TAB 2: ANÁLISIS (rápido)
# ============================================================
with tab_analysis:
    st.markdown("## 📊 Tendencias (según filtros, sin búsqueda)")
    if filtered.empty:
        st.info("No hay datos bajo los filtros actuales.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Películas por año**")
            by_year = (
                filtered[filtered["Year"].notna()]
                .groupby("Year").size()
                .reset_index(name="Count").sort_values("Year")
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
                ratings_counts = filtered["Your Rating"].round().value_counts().sort_index().reset_index()
                ratings_counts.columns = ["Rating", "Count"]
                ratings_counts["Rating"] = ratings_counts["Rating"].astype(int).astype(str)
                ratings_counts = ratings_counts.set_index("Rating")
                st.bar_chart(ratings_counts)
            else:
                st.write("No hay notas mías disponibles.")

        st.markdown("### 🔬 Correlación con IMDb")
        if "Your Rating" in filtered.columns and "IMDb Rating" in filtered.columns:
            corr_df = filtered[["Your Rating", "IMDb Rating"]].dropna()
        else:
            corr_df = pd.DataFrame()
        col_c, col_d = st.columns(2)
        with col_c:
            if not corr_df.empty and len(corr_df) > 1:
                corr = corr_df["Your Rating"].corr(corr_df["IMDb Rating"])
                st.metric("Correlación Pearson (mi nota vs IMDb)", f"{corr:.2f}")
            else:
                st.metric("Correlación Pearson (mi nota vs IMDb)", "N/A")
        with col_d:
            if not corr_df.empty:
                scatter_chart = (
                    alt.Chart(corr_df.reset_index())
                    .mark_circle(size=60, opacity=0.6)
                    .encode(
                        x=alt.X("IMDb Rating:Q", scale=alt.Scale(domain=[0, 10])),
                        y=alt.Y("Your Rating:Q", scale=alt.Scale(domain=[0, 10])),
                        tooltip=["IMDb Rating", "Your Rating"],
                    ).properties(height=300)
                )
                st.altair_chart(scatter_chart, use_container_width=True)
            else:
                st.write("No hay datos suficientes para el gráfico de dispersión.")

# ============================================================
# TAB 3: PREMIOS ÓSCAR
# ============================================================

# ---------- Carga de ficheros de premios ----------
@st.cache_data
def load_oscars(award_path="the_oscar_award.csv", full_path="full_data.csv"):
    """
    Carga datos del Oscar. Devuelve:
      - awards: todas las filas (nominaciones y ganadores)
      - winners: solo ganadores
    """
    awards = pd.read_csv(award_path)
    # Campos esperados típicos: year_film, year_ceremony, category, name, film, winner (True/False)
    # Normalizaciones robustas
    for col in ["year_film", "year_ceremony"]:
        if col in awards.columns:
            awards[col] = pd.to_numeric(awards[col], errors="coerce")
    for col in ["category", "name", "film"]:
        if col in awards.columns:
            awards[col] = awards[col].fillna("").astype(str)

    if "winner" in awards.columns:
        # convertir a bool
        if awards["winner"].dtype != bool:
            awards["winner"] = awards["winner"].map({True: True, False: False, 1: True, 0: False, "True": True, "FALSE": False, "False": False}).fillna(False).astype(bool)
    else:
        awards["winner"] = False

    awards["YearFilmInt"] = awards["year_film"].fillna(awards["year_ceremony"]).astype("Int64")
    awards["CanonCat"] = awards["category"].apply(canon_category)

    # Para link con catálogo
    awards["NormFilm"] = awards["film"].apply(normalize_title)
    winners = awards[awards["winner"] == True].copy().reset_index(drop=True)

    # full_data (opcional) si existe, solo para chequear esquema
    try:
        _ = pd.read_csv(full_path)
    except Exception:
        pass

    return awards, winners

def canon_category(cat: str) -> str:
    """Agrupa categorías a nombres 'canónicos' (para badges)."""
    c = (cat or "").lower()
    # ejemplos frecuentes
    if "best picture" in c or "outstanding picture" in c:
        return "Mejor Película"
    if "actor in a leading" in c or "actor leading" in c:
        return "Actor Protagonista"
    if "actress in a leading" in c or "actress leading" in c:
        return "Actriz Protagonista"
    if "actor in a supporting" in c:
        return "Actor de Reparto"
    if "actress in a supporting" in c:
        return "Actriz de Reparto"
    if "directing" in c or "best director" in c:
        return "Dirección"
    if "original screenplay" in c:
        return "Guion Original"
    if "adapted screenplay" in c:
        return "Guion Adaptado"
    if "cinematography" in c:
        return "Fotografía"
    if "film editing" in c:
        return "Montaje"
    if "international feature" in c or "foreign language" in c:
        return "Película Internacional"
    if "animated feature" in c:
        return "Película Animada"
    if "visual effects" in c:
        return "Efectos Visuales"
    if "sound" in c:
        return "Sonido"
    if "production design" in c or "art direction" in c:
        return "Diseño de Producción"
    if "costume" in c:
        return "Vestuario"
    if "makeup" in c:
        return "Maquillaje/Peinado"
    if "original song" in c:
        return "Canción Original"
    if "original score" in c or "music (original score)" in c:
        return "Banda Sonora"
    if "documentary feature" in c:
        return "Documental (Largo)"
    if "documentary short" in c:
        return "Documental (Corto)"
    if "live action short" in c:
        return "Cortometraje (Acción Viva)"
    if "animated short" in c:
        return "Cortometraje (Animado)"
    return "Otro"

CATEGORY_BADGES = {
    "Mejor Película": ("🎬", "#1e293b"),
    "Dirección": ("🎥", "#0f766e"),
    "Actor Protagonista": ("🕴️", "#3b0764"),
    "Actriz Protagonista": ("👗", "#5b21b6"),
    "Actor de Reparto": ("🎭", "#78350f"),
    "Actriz de Reparto": ("🎭", "#92400e"),
    "Guion Original": ("✍️", "#1f2937"),
    "Guion Adaptado": ("📚", "#1f2937"),
    "Fotografía": ("📸", "#14532d"),
    "Montaje": ("✂️", "#0e7490"),
    "Película Internacional": ("🌍", "#334155"),
    "Película Animada": ("🐭", "#3f6212"),
    "Efectos Visuales": ("✨", "#0369a1"),
    "Sonido": ("🔊", "#374151"),
    "Diseño de Producción": ("🏛️", "#4b5563"),
    "Vestuario": ("🧵", "#64748b"),
    "Maquillaje/Peinado": ("💄", "#6b21a8"),
    "Canción Original": ("🎵", "#1d4ed8"),
    "Banda Sonora": ("🎼", "#1d4ed8"),
    "Documental (Largo)": ("🎞️", "#334155"),
    "Documental (Corto)": ("🎞️", "#334155"),
    "Cortometraje (Acción Viva)": ("🎬", "#7c2d12"),
    "Cortometraje (Animado)": ("🎬", "#7c2d12"),
    "Otro": ("🏅", "#334155"),
}

def badge_text(cat):
    icon, _ = CATEGORY_BADGES.get(cat, ("🏅", "#334155"))
    return f"{icon} {cat}"

def style_badge(col: pd.Series):
    """Aplica color de fondo SOLO a la columna de categoría."""
    styles = []
    for val in col:
        _, color = CATEGORY_BADGES.get(val, ("🏅", "#334155"))
        styles.append(f"background-color: {color}; color: #e5e7eb; font-weight: 600;")
    return styles

def style_winner_row(row):
    """Resalta ganador (verde) en tablas que mezclan nominados."""
    if row.get("Ganador") == "🏆" or row.get("ES_GANADOR", False):
        return ['background-color: #14532d; color: #eaffea'] * len(row)
    return [''] * len(row)

with tab_awards:
    st.markdown("## 🏆 Premios Óscar — Ganadores y nominaciones")

    # Carga
    try:
        awards, winners = load_oscars("the_oscar_award.csv", "full_data.csv")
    except Exception as e:
        st.error(f"No pude cargar archivos de premios. Asegúrate de tener 'the_oscar_award.csv' y 'full_data.csv' en el repo. Detalle: {e}")
        st.stop()

    # Enlazar con mi catálogo para saber si está en mis datos
    join_cols = ["NormTitle", "YearInt", "Your Rating", "IMDb Rating", "URL"]
    catalog_slim = df[["NormTitle", "YearInt", "Your Rating", "IMDb Rating", "URL"]].copy()
    awards = awards.merge(
        catalog_slim,
        left_on=["NormFilm", "YearFilmInt"],
        right_on=["NormTitle", "YearInt"],
        how="left",
    )
    awards["InMyCatalog"] = awards["NormTitle"].notna()
    awards["MyRating"] = awards["Your Rating"]
    awards["MyIMDb"] = awards["IMDb Rating"]
    awards["CatalogURL"] = awards["URL"]

    # Controles
    st.sidebar.markdown("---")
    st.sidebar.header("🎚️ Filtros Premios")
    years = awards["YearFilmInt"].dropna().astype(int)
    if years.empty:
        st.info("No hay años válidos en los premios.")
        st.stop()
    min_y, max_y = int(years.min()), int(years.max())
    y_from, y_to = st.sidebar.slider("Rango de año de película", min_y, max_y, (max(min_y, 1927), max_y))
    cats = sorted(awards["CanonCat"].dropna().unique().tolist())
    sel_cats = st.sidebar.multiselect("Categorías", cats, default=[])

    txt = st.text_input("Buscar en premios (título/ganador/categoría)...", "")

    # Dataset filtrado para análisis
    ff = awards[(awards["YearFilmInt"].between(y_from, y_to))]
    if sel_cats:
        ff = ff[ff["CanonCat"].isin(sel_cats)]
    if txt.strip():
        q = txt.strip().lower()
        ff = ff[
            ff["film"].str.lower().str.contains(q, na=False) |
            ff["name"].str.lower().str.contains(q, na=False) |
            ff["CanonCat"].str.lower().str.contains(q, na=False) |
            ff["category"].str.lower().str.contains(q, na=False)
        ]

    # ---- Vista por año (ganadores + nominados) ----
    st.markdown("### 📅 Ganadores por año")
    year_pick = st.selectbox("Selecciona un año de película", sorted(ff["YearFilmInt"].dropna().astype(int).unique().tolist(), reverse=True))

    table_year_all = awards[awards["YearFilmInt"] == year_pick].copy()
    table_winners = table_year_all[table_year_all["winner"] == True].copy()
    # Orden por categoría canónica + película
    table_winners = table_winners.sort_values(["CanonCat", "film", "name"])

    pretty = table_winners[[
        "CanonCat", "category", "name", "film",
        "YearFilmInt", "InMyCatalog", "MyRating", "MyIMDb", "CatalogURL"
    ]].copy()

    pretty = pretty.rename(columns={
        "CanonCat": "Categoría",
        "category": "Categoría (cruda)",
        "name": "Ganador/a",
        "film": "Película",
        "YearFilmInt": "Año de película",
        "InMyCatalog": "En mi catálogo",
        "MyRating": "Mi nota",
        "MyIMDb": "IMDb",
        "CatalogURL": "IMDb (mía)"
    })

    # Insignias + formatos
    pretty["Categoría"] = pretty["Categoría"].apply(badge_text)
    pretty["Año de película"] = pretty["Año de película"].apply(fmt_year)
    if "Mi nota" in pretty.columns:
        pretty["Mi nota"] = pretty["Mi nota"].apply(lambda v: f"{float(v):.1f}" if pd.notna(v) else "")
    if "IMDb" in pretty.columns:
        pretty["IMDb"] = pretty["IMDb"].apply(lambda v: f"{float(v):.1f}" if pd.notna(v) else "")
    pretty["En mi catálogo"] = pretty["En mi catálogo"].map({True: "✅", False: "—"})
    pretty["ES_GANADOR"] = True  # todas estas filas lo son

    # Styler: badge en columna categoría + ganador verde
    # Para colorear solo la columna, aplicamos sobre el texto SIN el emoji
    # Creamos una col auxiliar que solo almacene nombre canónico (para estilo)
    _badge_col = table_winners["CanonCat"].tolist()
    # Pasamos un DataFrame paralelo para estilos de categoría
    def _style_badge_only(df_for_style):
        return style_badge(pd.Series(_badge_col, index=df_for_style.index))

    styler = pretty.drop(columns=["ES_GANADOR"]).style.apply(
        style_winner_row, axis=1
    ).apply(
        _style_badge_only, subset=["Categoría"]
    )

    st.dataframe(styler, use_container_width=True, hide_index=True)

    with st.expander("👀 (Opcional) Ver también nominaciones de ese año", expanded=False):
        nom_year = table_year_all.copy()
        nom_year["Ganador"] = nom_year["winner"].map({True: "🏆", False: ""})
        nom_disp = nom_year[[
            "CanonCat", "category", "Ganador", "name", "film",
            "YearFilmInt"
        ]].copy().rename(columns={
            "CanonCat": "Categoría",
            "category": "Categoría (cruda)",
            "name": "Persona/Equipo",
            "film": "Película",
            "YearFilmInt": "Año de película"
        })
        nom_disp["Categoría"] = nom_disp["Categoría"].apply(badge_text)
        nom_disp["Año de película"] = nom_disp["Año de película"].apply(fmt_year)

        styler_nom = nom_disp.style.apply(style_winner_row, axis=1).apply(
            lambda s: style_badge(s), subset=["Categoría"]
        )
        st.dataframe(styler_nom, use_container_width=True, hide_index=True)

    # ---- Rankings (saneados para evitar errores de render) ----
    st.markdown("### 🥇 Rankings en el rango seleccionado")
    colr1, colr2 = st.columns(2)
    with colr1:
        top_films = (
            ff[ff["winner"] == True]
            .groupby(["film", "YearFilmInt"])
            .size().reset_index(name="Wins")
            .sort_values(["Wins", "film"], ascending=[False, True])
            .head(15)
        )
        if not top_films.empty:
            tf_disp = top_films.rename(columns={
                "film": "Película", "YearFilmInt": "Año", "Wins": "Óscar ganados"
            }).copy()
            tf_disp["Película"] = tf_disp["Película"].astype(str).fillna("")
            tf_disp["Año"] = tf_disp["Año"].apply(fmt_year)
            tf_disp["Óscar ganados"] = pd.to_numeric(tf_disp["Óscar ganados"], errors="coerce").fillna(0).astype(int)
            try:
                st.dataframe(tf_disp, use_container_width=True, hide_index=True)
            except Exception:
                st.warning("Mostrando tabla simple por un problema de renderizado.")
                st.table(tf_disp)
        else:
            st.write("Sin datos de películas en este rango.")
    with colr2:
        top_people = (
            ff[ff["winner"] == True]
            .groupby("name")
            .size().reset_index(name="Wins")
            .sort_values(["Wins", "name"], ascending=[False, True])
            .head(15)
        )
        if not top_people.empty:
            tp_disp = top_people.rename(columns={
                "name": "Ganador/a", "Wins": "Óscar ganados"
            }).copy()
            tp_disp["Ganador/a"] = tp_disp["Ganador/a"].astype(str).fillna("")
            tp_disp["Óscar ganados"] = pd.to_numeric(tp_disp["Óscar ganados"], errors="coerce").fillna(0).astype(int)
            try:
                st.dataframe(tp_disp, use_container_width=True, hide_index=True)
            except Exception:
                st.warning("Mostrando tabla simple por un problema de renderizado.")
                st.table(tp_disp)
        else:
            st.write("Sin datos de personas en este rango.")

# ============================================================
# TAB 4: ¿QUÉ VER HOY?
# ============================================================
def get_youtube_trailer_url(title, year=None, language_hint="es"):
    if YOUTUBE_API_KEY is None or not title or pd.isna(title):
        return None
    q = f"{title} trailer"
    try:
        if year is not None and not pd.isna(year):
            q += f" {int(float(year))}"
    except Exception:
        pass
    params = {
        "key": YOUTUBE_API_KEY,
        "part": "snippet",
        "q": q,
        "type": "video",
        "maxResults": 1,
        "videoEmbeddable": "true",
        "regionCode": "CL",
    }
    try:
        r = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=5)
        if r.status_code != 200:
            return None
        data = r.json()
        items = data.get("items", [])
        if not items:
            return None
        vid = items[0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={vid}"
    except Exception:
        return None

with tab_what:
    st.markdown("## 🎲 ¿Qué ver hoy? (según mi propio gusto)")
    if st.button("Recomendar una película"):
        pool = filtered.copy()
        if pool.empty:
            st.warning("No hay películas con los filtros actuales.")
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
            border_color, glow_color = get_rating_colors(nota if pd.notna(nota) else imdb_rating)
            reseñas_url = get_spanish_review_link(titulo, year)
            col_img, col_info = st.columns([1, 3])
            with col_img:
                if show_trailers:
                    trailer_url = get_youtube_trailer_url(titulo, year)
                    if trailer_url:
                        st.video(trailer_url)
            with col_info:
                st.markdown(
                    f"""
<div style="
    border-radius: 12px;
    border: 1px solid {border_color};
    padding: 10px;
    box-shadow: 0 0 18px {glow_color};
">
<b>{titulo}</b> {f"({fmt_year(year)})" if pd.notna(year) else ""}<br>
{f"⭐ Mi nota: {fmt_rating(nota)}<br>" if pd.notna(nota) else ""}
{f"IMDb: {fmt_rating(imdb_rating)}" if pd.notna(imdb_rating) else ""}
</div>
                    """,
                    unsafe_allow_html=True
                )
                if reseñas_url:
                    st.write(f"[Reseñas en español]({reseñas_url})")

# =========================
# Pie de página
# =========================
st.markdown("---")
st.markdown(
    f"<div style='text-align:center; opacity:0.8'>v{APP_VERSION} · powered by <b>Diego Leal</b></div>",
    unsafe_allow_html=True
)
