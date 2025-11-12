import streamlit as st
import pandas as pd

from modules.utils import (
    APP_VERSION, apply_theme_and_css, show_changelog_sidebar, load_data
)
from modules import imdb_catalog, analytics, afi_list, oscars_awards

st.set_page_config(
    page_title=f"🎬 Mi catálogo de Películas · v{APP_VERSION}",
    layout="centered"
)
apply_theme_and_css()

st.title("🎥 Mi catálogo de películas (IMDb)")
st.caption(f"Versión **v{APP_VERSION}** · powered by Diego Leal")

# -------- Datos --------
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
    except Exception:
        st.error(
            "No se encontró 'peliculas.csv' y no se subió archivo.\n\n"
            "Sube tu CSV de IMDb desde la barra lateral para continuar."
        )
        st.stop()

if "Title" not in df.columns:
    st.error("El CSV debe contener una columna 'Title'.")
    st.stop()

# -------- Barra lateral --------
st.sidebar.header("🖼️ Opciones de visualización")
show_posters_fav = st.sidebar.checkbox("Mostrar pósters TMDb en mis favoritas (nota ≥ 9)", value=True)

st.sidebar.header("🌐 TMDb")
use_tmdb_gallery = st.sidebar.checkbox("Usar TMDb en la galería visual", value=True)

st.sidebar.header("🎬 Tráilers")
show_trailers = st.sidebar.checkbox("Mostrar tráiler de YouTube (si hay API key)", value=True)

st.sidebar.header("⚙️ Opciones avanzadas")
show_awards = st.sidebar.checkbox("Consultar premios en OMDb (más lento)", value=False)
if show_awards:
    st.sidebar.caption("⚠ Puede hacer más lenta la primera carga.")

show_changelog_sidebar()

st.sidebar.header("🎛️ Filtros")
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

all_genres = sorted(
    set(g for sub in df.get("GenreList", pd.Series(dtype=object)).dropna() for g in sub if g)
)
selected_genres = st.sidebar.multiselect("Géneros (todas las seleccionadas deben estar presentes)", options=all_genres)

all_directors = sorted(
    set(d.strip() for d in df.get("Directors", pd.Series(dtype=str)).dropna() if str(d).strip() != "")
)
selected_directors = st.sidebar.multiselect("Directores", options=all_directors)

order_by = st.sidebar.selectbox("Ordenar por", ["Your Rating", "IMDb Rating", "Year", "Title", "Aleatorio"])
order_asc = st.sidebar.checkbox("Orden ascendente", value=False)

st.session_state.update({
    "show_posters_fav": show_posters_fav,
    "use_tmdb_gallery": use_tmdb_gallery,
    "show_trailers": show_trailers,
    "show_awards": show_awards,
    "year_range": year_range,
    "rating_range": rating_range,
    "selected_genres": selected_genres,
    "selected_directors": selected_directors,
    "order_by": order_by,
    "order_asc": order_asc,
})

st.markdown("## 🔎 Búsqueda en mi catálogo (sobre los filtros actuales)")
search_query = st.text_input(
    "Buscar por título, director, género, año o calificaciones",
    placeholder="Escribe cualquier cosa… (se aplica en tiempo real)",
    key="busqueda_unica"
)

tab_catalog, tab_analysis, tab_afi, tab_awards, tab_what = st.tabs(
    ["🎬 Catálogo", "📊 Análisis", "🏆 Lista AFI", "🏆 Premios Óscar", "🎲 ¿Qué ver hoy?"]
)

with tab_catalog:
    try:
        imdb_catalog.render_catalog_tab(df, search_query)
    except Exception as e:
        st.error("❌ Error en pestaña Catálogo. Se omite para no detener la app.")
        st.exception(e)

with tab_analysis:
    try:
        analytics.render_analysis_tab(df)
    except Exception as e:
        st.error("❌ Error en pestaña Análisis.")
        st.exception(e)

with tab_afi:
    try:
        afi_list.render_afi_tab(df)
    except Exception as e:
        st.error("❌ Error en pestaña AFI. Revisa que el CSV tenga 'Title' y 'Year'.")
        st.exception(e)

with tab_awards:
    try:
        oscars_awards.render_awards_tab(df)
    except Exception as e:
        st.error("❌ Error en pestaña Premios Óscar. Revisa 'the_oscar_award.csv'.")
        st.exception(e)

with tab_what:
    try:
        imdb_catalog.render_what_to_watch(df)
    except Exception as e:
        st.error("❌ Error en pestaña ¿Qué ver hoy?.")
        st.exception(e)

st.markdown("---")
st.caption(f"Versión **v{APP_VERSION}** — powered by **Diego Leal**")
