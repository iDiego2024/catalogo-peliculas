# modules/imdb_catalog.py
from __future__ import annotations
import math
from typing import Dict, Any, Optional, List

import streamlit as st
import pandas as pd

from modules.utils import (
    fmt_year, fmt_rating, get_rating_colors,
    get_tmdb_basic_info, get_tmdb_providers,
)

# ------------------------------------------------------------
# Helpers internos
# ------------------------------------------------------------

def _poster_card_html(title: str,
                      year,
                      your_rating,
                      imdb_rating,
                      poster_url: Optional[str]) -> str:
    base_rating = your_rating if pd.notna(your_rating) else imdb_rating
    border, glow = get_rating_colors(base_rating)
    year_str = f" ({fmt_year(year)})" if pd.notna(year) else ""

    if poster_url:
        poster = f"""
<div class="poster-frame">
  <img class="poster-img" src="{poster_url}" alt="{title}">
</div>"""
    else:
        poster = """
<div class="poster-frame">
  <div class="poster-placeholder">
    <div class="film-reel">🎞️</div>
    <div class="film-reel-text">Sin póster</div>
  </div>
</div>"""

    rating_line = (
        f"{'⭐ ' + fmt_rating(your_rating) if pd.notna(your_rating) else ''}"
        f"{' | ' if pd.notna(your_rating) and pd.notna(imdb_rating) else ''}"
        f"{'IMDb ' + fmt_rating(imdb_rating) if pd.notna(imdb_rating) else ''}"
    )

    return f"""
<div class="poster-card" style="
  border-color:{border};
  box-shadow:0 0 0 1px rgba(15,23,42,.9), 0 0 22px {glow};
">
  {poster}
  <h4>{title}{year_str}</h4>
  <p>{rating_line}</p>
</div>"""

def _grid_css_once():
    if "grid_css_injected" in st.session_state:
        return
    st.session_state["grid_css_injected"] = True
    st.markdown("""
<style>
.poster-grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
  gap:18px;
  width:100%;
}
@media (max-width:900px){
  .poster-grid{grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;}
}
.poster-card{
  background: radial-gradient(circle at top left, rgba(15,23,42,.90), rgba(15,23,42,.82));
  border:1px solid rgba(148,163,184,.45);
  border-radius:14px;
  padding:12px;
  transition:transform .15s ease-out, box-shadow .15s ease-out, border-color .15s;
}
.poster-card:hover{
  transform:translateY(-3px) scale(1.01);
  border-color:#facc15;
  box-shadow:0 0 0 1px rgba(250,204,21,.7), 0 0 28px rgba(250,204,21,.8);
}
.poster-card h4{
  margin:.4rem 0 .1rem 0;
  font-weight:700; letter-spacing:.02em; font-size:.92rem; color:#f9fafb;
}
.poster-card p{
  margin:0; color:#cbd5f5; font-size:.82rem;
}
.poster-frame{
  width:100%; aspect-ratio:2/3; border-radius:12px; overflow:hidden;
  border:1px solid rgba(148,163,184,.5);
  background: radial-gradient(circle at top, #020617 0%, #000 55%, #020617 100%);
  box-shadow:0 14px 30px rgba(0,0,0,.85);
}
.poster-img{ width:100%; height:100%; object-fit:cover; display:block; transition:transform .25s ease-out;}
.poster-card:hover .poster-img{ transform:scale(1.03); }
.poster-placeholder{
  width:100%; height:100%; display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  background:radial-gradient(circle at 15% 0%, rgba(250,204,21,.12), rgba(15,23,42,1)),
            radial-gradient(circle at 85% 100%, rgba(56,189,248,.16), rgba(0,0,0,1));
}
.film-reel{font-size:2rem; filter:drop-shadow(0 0 10px rgba(250,204,21,.9))}
.film-reel-text{font-size:.78rem; letter-spacing:.14em; text-transform:uppercase; color:#e5e7eb}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# API principal (llamada desde app.py)
# ------------------------------------------------------------

def render_catalog_tab(df: pd.DataFrame,
                       page_size: int = 24,
                       use_tmdb_gallery: bool = True) -> None:
    """
    Renderiza la tabla, la galería en cuadrícula y la paginación.
    - df: dataframe ya filtrado y ordenado desde app.py
    - page_size: cantidad por página para la galería
    - use_tmdb_gallery: si True, intenta buscar pósteres en TMDb
    """
    st.markdown("### 📚 Resultados")
    cols_to_show = [c for c in [
        "Title", "Year", "Your Rating", "IMDb Rating", "Genres", "Directors", "URL"
    ] if c in df.columns]
    if cols_to_show:
        show = df[cols_to_show].copy()
        if "Year" in show.columns:        show["Year"] = show["Year"].apply(fmt_year)
        if "Your Rating" in show.columns: show["Your Rating"] = show["Your Rating"].apply(fmt_rating)
        if "IMDb Rating" in show.columns: show["IMDb Rating"] = show["IMDb Rating"].apply(fmt_rating)
        st.dataframe(show, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 🧱 Galería Visual")

    total = len(df)
    if total == 0:
        st.info("No hay películas para la galería con los filtros actuales.")
        return

    # Controles de paginación
    left, mid, right = st.columns([1,2,1])
    with left:
        page_size = st.slider("Pósters por página", 12, 60, page_size, 12, key="gal_page_size")
    num_pages = max(math.ceil(total / page_size), 1)
    st.session_state.setdefault("gal_page", 1)
    if st.session_state.gal_page > num_pages:
        st.session_state.gal_page = num_pages

    with right:
        if st.button("Siguiente ▶", disabled=st.session_state.gal_page >= num_pages):
            st.session_state.gal_page += 1
    with left:
        if st.button("◀ Anterior", disabled=st.session_state.gal_page <= 1):
            st.session_state.gal_page -= 1
    with mid:
        st.caption(f"Página {st.session_state.gal_page} de {num_pages} — Mostrando {page_size} por página")

    # Página actual
    start = (st.session_state.gal_page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end].copy()

    # Inyectar CSS de la grilla (una sola vez)
    _grid_css_once()

    # Construcción de tarjetas
    cards: List[str] = []
    for _, r in page_df.iterrows():
        title = r.get("Title", "Sin título")
        year = r.get("Year")
        your_rating = r.get("Your Rating")
        imdb_rating = r.get("IMDb Rating")

        poster_url = None
        if use_tmdb_gallery:
            tmdb = get_tmdb_basic_info(title, year)
            poster_url = (tmdb or {}).get("poster_url")

        cards.append(_poster_card_html(title, year, your_rating, imdb_rating, poster_url))

    html = f'<div class="poster-grid">\n' + "\n".join(cards) + "\n</div>"
    # IMPORTANTE: renderizar como HTML
    st.markdown(html, unsafe_allow_html=True)
