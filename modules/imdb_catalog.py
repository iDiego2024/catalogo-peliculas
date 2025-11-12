# -*- coding: utf-8 -*-
import streamlit as st
import math
from modules.utils import fmt_year, fmt_rating, get_tmdb_basic_info

def render_catalog_tab(df, search_query):
    # ------------------- FILTROS BÁSICOS -------------------
    if search_query:
        df = df[df["SearchText"].str.contains(search_query.lower(), na=False)]

    st.markdown("### 📚 Resultados")

    if df.empty:
        st.warning("No hay resultados que coincidan con los filtros actuales.")
        return

    # ------------------- TABLA -------------------
    cols = [
        c for c in ["Title", "Year", "Your Rating", "IMDb Rating", "Genres", "Directors", "URL"]
        if c in df.columns
    ]
    table = df[cols].copy()
    table["Year"] = table["Year"].apply(fmt_year)
    table["Your Rating"] = table["Your Rating"].apply(fmt_rating)
    table["IMDb Rating"] = table["IMDb Rating"].apply(fmt_rating)

    st.dataframe(table, use_container_width=True, hide_index=True)

    # ------------------- GALERÍA -------------------
    st.markdown("---")
    st.markdown("### 🧱 Galería Visual")

    per_page = 24
    total = len(df)
    if total == 0:
        st.info("No hay películas para mostrar en la galería.")
        return

    num_pages = max(math.ceil(total / per_page), 1)
    page = st.session_state.get("gallery_page", 1)
    start = (page - 1) * per_page
    end = start + per_page
    page_df = df.iloc[start:end]

    st.caption(f"Mostrando {start+1}–{min(end, total)} de {total} películas")

    # ------------------- ESTILOS CSS -------------------
    st.markdown("""
        <style>
        .poster-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .poster-card {
            background: rgba(17, 24, 39, 0.85);
            border-radius: 12px;
            padding: 10px;
            text-align: center;
            border: 1px solid rgba(148,163,184,0.35);
            box-shadow: 0 10px 25px rgba(0,0,0,0.4);
            transition: transform 0.2s ease-in-out;
        }
        .poster-card:hover {
            transform: scale(1.03);
            border-color: #facc15;
        }
        .poster-card img {
            width: 100%;
            border-radius: 10px;
            margin-bottom: 8px;
            aspect-ratio: 2/3;
            object-fit: cover;
        }
        .poster-card h4 {
            color: #f9fafb;
            font-size: 0.95rem;
            margin-bottom: 4px;
            line-height: 1.2;
        }
        .poster-card p {
            color: #a1a1aa;
            font-size: 0.8rem;
            margin: 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # ------------------- CONSTRUCCIÓN DEL GRID -------------------
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
