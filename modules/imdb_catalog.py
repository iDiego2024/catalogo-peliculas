# -*- coding: utf-8 -*-
import math
import pandas as pd
import streamlit as st
from modules.utils import (
    fmt_year, fmt_rating, get_rating_colors,
    get_tmdb_basic_info, get_tmdb_providers, get_spanish_review_link
)

def render_catalog_tab(df, search_query):
    st.markdown("## 🎬 Catálogo de Películas")

    # ------------------- FILTROS EN SIDEBAR -------------------
    st.sidebar.header("🎛️ Filtros del Catálogo")

    year_min, year_max = int(df["Year"].min()), int(df["Year"].max())
    year_range = st.sidebar.slider(
        "Rango de años", min_value=year_min, max_value=year_max,
        value=(year_min, year_max), key="filter_year_range"
    )

    rating_min, rating_max = 1, 10
    rating_range = st.sidebar.slider(
        "Mi nota (Your Rating)", min_value=rating_min, max_value=rating_max,
        value=(rating_min, rating_max), key="filter_rating_range"
    )

    all_genres = sorted(set(g for sub in df["GenreList"].dropna() for g in sub if g))
    selected_genres = st.sidebar.multiselect("Géneros", all_genres, key="filter_genres")

    all_directors = sorted(set(d.strip() for d in df["Directors"].dropna() if d.strip()))
    selected_directors = st.sidebar.multiselect("Directores", all_directors, key="filter_directors")

    # ------------------- APLICAR FILTROS -------------------
    filtered = df[
        df["Year"].between(year_range[0], year_range[1])
        & df["Your Rating"].between(rating_range[0], rating_range[1])
    ]

    if selected_genres:
        filtered = filtered[
            filtered["GenreList"].apply(lambda gl: all(g in gl for g in selected_genres))
        ]

    if selected_directors:
        filtered = filtered[
            filtered["Directors"].apply(
                lambda d: any(sd.lower() in str(d).lower() for sd in selected_directors)
            )
        ]

    # ------------------- BAJADA (Resumen de filtros) -------------------
    st.caption(
        f"Filtros activos → Años: {year_range[0]}–{year_range[1]} | "
        f"Mi nota: {rating_range[0]}–{rating_range[1]} | "
        f"Géneros: {', '.join(selected_genres) if selected_genres else 'Todos'} | "
        f"Directores: {', '.join(selected_directors) if selected_directors else 'Todos'}"
    )

    # ------------------- BÚSQUEDA -------------------
    if search_query:
        filtered = filtered[
            filtered["SearchText"].str.contains(search_query.lower(), na=False)
        ]

    st.markdown("---")

    # ------------------- ESTILO DE TABLA -------------------
    st.markdown("""
        <style>
        .stDataFrame, .stTable {
            font-family: 'Inter', sans-serif;
            font-size: 0.95rem;
            color: #e5e5e5 !important;
        }
        th {
            background-color: #0f172a !important;
            color: #facc15 !important;
            font-weight: 600 !important;
            text-transform: uppercase;
        }
        table {
            border-radius: 8px;
            border-collapse: collapse;
            overflow: hidden;
            box-shadow: 0px 4px 18px rgba(0,0,0,0.4);
        }
        </style>
    """, unsafe_allow_html=True)

    # ------------------- TABLA PRINCIPAL -------------------
    st.markdown("### 🎞️ Resultados")
    cols = [
        c for c in ["Title", "Year", "Your Rating", "IMDb Rating", "Genres", "Directors", "URL"]
        if c in filtered.columns
    ]
    table = filtered[cols].copy()
    table["Year"] = table["Year"].apply(fmt_year)
    table["Your Rating"] = table["Your Rating"].apply(fmt_rating)
    table["IMDb Rating"] = table["IMDb Rating"].apply(fmt_rating)

    st.dataframe(table, use_container_width=True, hide_index=True)

    # ------------------- GALERÍA -------------------
    st.markdown("---")
    st.markdown("### 🧱 Galería Visual")

    per_page = 24
    total = len(filtered)
    if total == 0:
        st.info("No hay películas bajo los filtros actuales.")
        return

    num_pages = max(math.ceil(total / per_page), 1)
    page = st.session_state.get("gallery_page", 1)
    start = (page - 1) * per_page
    end = start + per_page
    page_df = filtered.iloc[start:end]

    st.caption(f"Mostrando {start+1}–{min(end,total)} de {total} películas")

    # CSS de cuadrícula
    st.markdown("""
        <style>
        .poster-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }
        .poster-card {
            background: rgba(15,23,42,0.95);
            border-radius: 14px;
            padding: 10px;
            text-align: center;
            border: 1px solid rgba(148,163,184,0.35);
            box-shadow: 0 10px 25px rgba(0,0,0,0.6);
        }
        .poster-card img {
            width: 100%;
            border-radius: 10px;
            margin-bottom: 8px;
        }
        .poster-card h4 {
            color: #f9fafb;
            font-size: 0.95rem;
            margin-bottom: 4px;
        }
        .poster-card p {
            color: #a1a1aa;
            font-size: 0.8rem;
            margin: 0;
        }
        </style>
    """, unsafe_allow_html=True)

    grid = ['<div class="poster-grid">']
    for _, row in page_df.iterrows():
        title = row.get("Title", "Sin título")
        year = fmt_year(row.get("Year"))
        poster_info = get_tmdb_basic_info(title, row.get("Year"))
        poster_url = poster_info.get("poster_url") if poster_info else None
        if poster_url:
            grid.append(f"""
                <div class="poster-card">
                    <img src="{poster_url}" alt="{title}">
                    <h4>{title} ({year})</h4>
                    <p>⭐ {fmt_rating(row.get('Your Rating'))} | IMDb {fmt_rating(row.get('IMDb Rating'))}</p>
                </div>
            """)
    grid.append("</div>")
    st.markdown("\n".join(grid), unsafe_allow_html=True)
