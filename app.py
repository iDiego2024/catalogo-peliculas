import streamlit as st
from modules.utils import APP_VERSION, CHANGELOG, setup_page, footer, load_data, render_afi_tab, render_what_to_watch_tab
from modules.imdb_catalog import render_catalog_tab
from modules.analytics import render_analytics_tab
from modules.oscars_awards import render_oscars_tab

st.set_page_config(page_title="🎬 Mi catálogo de Películas", layout="centered")
setup_page()
st.title("🎥 Mi catálogo de películas (IMDb)")

st.sidebar.header("📂 Datos")
uploaded = st.sidebar.file_uploader(
    "Sube tu CSV exportado desde IMDb (si no, se usa data/peliculas.csv)",
    type=["csv"]
)

if uploaded is not None:
    df = load_data(uploaded)
else:
    try:
        df = load_data("data/peliculas.csv")
    except FileNotFoundError:
        st.error(
            "No se encontró 'data/peliculas.csv' y no subiste archivo.\n\n"
            "Sube tu CSV de IMDb desde la barra lateral para continuar."
        )
        st.stop()

tab_catalog, tab_analysis, tab_afi, tab_awards, tab_what = st.tabs(
    ["🎬 Catálogo", "📊 Análisis", "🏆 Lista AFI", "🏆 Premios Óscar", "🎲 ¿Qué ver hoy?"]
)

with tab_catalog:
    render_catalog_tab(df)
with tab_analysis:
    render_analytics_tab(df)
with tab_afi:
    render_afi_tab(df)
with tab_awards:
    render_oscars_tab(df)
with tab_what:
    render_what_to_watch_tab(df)

st.sidebar.header("🧾 Versiones")
with st.sidebar.expander("Ver changelog", expanded=False):
    for ver, notes in CHANGELOG.items():
        st.markdown(f"**v{ver}**")
        for n in notes:
            st.markdown(f"- {n}")
        st.markdown("---")

footer()
