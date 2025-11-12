import streamlit as st
import pandas as pd
import altair as alt

def render_analysis_tab(df):
    st.markdown("## 📊 Análisis y tendencias (según filtros, sin búsqueda)")
    st.caption("Los gráficos usan sólo los filtros de la barra lateral.")

    # Reaplicar los filtros básicos (sin búsqueda)
    year_range = st.session_state.get("year_range", (0, 9999))
    rating_range = st.session_state.get("rating_range", (0, 10))
    selected_genres = st.session_state.get("selected_genres", [])
    selected_directors = st.session_state.get("selected_directors", [])

    filtered = df.copy()
    if "Year" in filtered.columns:
        filtered = filtered[(filtered["Year"] >= year_range[0]) & (filtered["Year"] <= year_range[1])]
    if "Your Rating" in filtered.columns:
        filtered = filtered[(filtered["Your Rating"] >= rating_range[0]) & (filtered["Your Rating"] <= rating_range[1])]

    if selected_genres:
        filtered = filtered[
            filtered["GenreList"].apply(lambda gl: all(g in gl for g in selected_genres))
        ]

    if selected_directors:
        def _matches_any_director(cell):
            if pd.isna(cell): return False
            dirs = [d.strip() for d in str(cell).split(",") if d.strip()]
            return any(d in dirs for d in selected_directors)
        filtered = filtered[filtered["Directors"].apply(_matches_any_director)]

    if filtered.empty:
        st.info("No hay datos bajo los filtros actuales para mostrar gráficos.")
        return

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Películas por año**")
        by_year = (
            filtered[filtered["Year"].notna()].groupby("Year").size().reset_index(name="Count").sort_values("Year")
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

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("**Top géneros (por número de películas)**")
        if "GenreList" in filtered.columns:
            genres_exploded = filtered.explode("GenreList")
            genres_exploded = genres_exploded[genres_exploded["GenreList"].notna() & (genres_exploded["GenreList"] != "")]
            if not genres_exploded.empty:
                top_genres = genres_exploded["GenreList"].value_counts().head(15).reset_index()
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
                decade_imdb = tmp.groupby("Decade")["IMDb Rating"].mean().reset_index().sort_values("Decade")
                decade_imdb["Decade"] = decade_imdb["Decade"].astype(str)
                decade_imdb = decade_imdb.set_index("Decade")
                st.line_chart(decade_imdb)
            else:
                st.write("No hay datos suficientes de año para calcular décadas.")
        else:
            st.write("No hay IMDb Rating disponible.")
