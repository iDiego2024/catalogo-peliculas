import streamlit as st
import pandas as pd
from modules.utils import fmt_year, fmt_rating

def apply_search(df_in, query):
    if not query: return df_in
    q = query.strip().lower()
    if "SearchText" not in df_in.columns: return df_in
    return df_in[df_in["SearchText"].str.contains(q, na=False, regex=False)]

def render_catalog_tab(df):
    st.sidebar.header("🎛️ Filtros")
    if df["Year"].notna().any():
        min_year = int(df["Year"].min()); max_year = int(df["Year"].max())
        year_range = st.sidebar.slider("Rango de años", min_year, max_year, (min_year, max_year))
    else:
        year_range = (0, 9999)
    if df["Your Rating"].notna().any():
        min_rating = int(df["Your Rating"].min()); max_rating = int(df["Your Rating"].max())
        rating_range = st.sidebar.slider("Mi nota (Your Rating)", min_rating, max_rating, (min_rating, max_rating))
    else:
        rating_range = (0, 10)
    all_genres = sorted(set(g for sub in df["GenreList"].dropna() for g in sub if g))
    selected_genres = st.sidebar.multiselect("Géneros (todas deben estar)", options=all_genres)
    all_directors = sorted(set(d.strip() for d in df["Directors"].dropna() if str(d).strip() != ""))
    selected_directors = st.sidebar.multiselect("Directores", options=all_directors)
    order_by = st.sidebar.selectbox("Ordenar por", ["Your Rating","IMDb Rating","Year","Title","Aleatorio"])
    order_asc = st.sidebar.checkbox("Orden ascendente", value=False)

    filtered = df.copy()
    filtered = filtered[(filtered["Year"] >= year_range[0]) & (filtered["Year"] <= year_range[1])]
    filtered = filtered[(filtered["Your Rating"] >= rating_range[0]) & (filtered["Your Rating"] <= rating_range[1])]

    if selected_genres:
        filtered = filtered[filtered["GenreList"].apply(lambda gl: all(g in gl for g in selected_genres))]

    if selected_directors:
        def _matches_any(cell):
            if pd.isna(cell): return False
            dirs = [d.strip() for d in str(cell).split(",") if d.strip()]
            return any(d in dirs for d in selected_directors)
        filtered = filtered[filtered["Directors"].apply(_matches_any)]

    st.markdown("## 🔎 Búsqueda en mi catálogo")
    search_query = st.text_input("Buscar por título, director, género, año o calificaciones", placeholder="Escribe cualquier cosa…")
    filtered_view = apply_search(filtered.copy(), search_query)

    if order_by == "Aleatorio":
        if not filtered_view.empty:
            filtered_view = filtered_view.sample(frac=1, random_state=None)
    elif order_by in filtered_view.columns:
        filtered_view = filtered_view.sort_values(order_by, ascending=order_asc)

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Películas tras filtros + búsqueda", len(filtered_view))
    with col2:
        if filtered_view["Your Rating"].notna().any():
            st.metric("Promedio de mi nota", f"{filtered_view['Your Rating'].mean():.2f}")
        else: st.metric("Promedio de mi nota", "N/A")
    with col3:
        if filtered_view["IMDb Rating"].notna().any():
            st.metric("Promedio IMDb", f"{filtered_view['IMDb Rating'].mean():.2f}")
        else: st.metric("Promedio IMDb", "N/A")

    st.markdown("### 📚 Tabla de resultados")
    cols_to_show = [c for c in ["Title","Year","Your Rating","IMDb Rating","Genres","Directors","Date Rated","URL"] if c in filtered_view.columns]
    table_df = filtered_view[cols_to_show].copy()
    display_df = table_df.copy()
    if "Year" in display_df.columns: display_df["Year"] = display_df["Year"].apply(fmt_year)
    if "Your Rating" in display_df.columns: display_df["Your Rating"] = display_df["Your Rating"].apply(fmt_rating)
    if "IMDb Rating" in display_df.columns: display_df["IMDb Rating"] = display_df["IMDb Rating"].apply(fmt_rating)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv_filtrado = table_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar resultados filtrados (CSV)", data=csv_filtrado, file_name="mis_peliculas_filtradas.csv", mime="text/csv")
