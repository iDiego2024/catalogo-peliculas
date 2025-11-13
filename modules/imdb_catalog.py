# modules/imdb_catalog.py
from __future__ import annotations
import math
from typing import Optional, List

import streamlit as st
import pandas as pd

from modules.utils import (
    fmt_year, fmt_rating, get_rating_colors,
    get_tmdb_basic_info,
)

def _grid_css_once():
    if "grid_css_injected" in st.session_state:
        return
    st.session_state["grid_css_injected"] = True
    st.markdown("""
<style>
.poster-grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
  gap:18px; width:100%;
}
@media (max-width:900px){
  .poster-grid{grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;}
}
.poster-card{
  background: radial-gradient(circle at top left, rgba(15,23,42,.90), rgba(15,23,42,.82));
  border:1px solid rgba(148,163,184,.45);
  border-radius:14px; padding:12px;
  transition:transform .15s, box-shadow .15s, border-color .15s;
}
.poster-card:hover{
  transform:translateY(-3px) scale(1.01);
  border-color:#facc15;
  box-shadow:0 0 0 1px rgba(250,204,21,.7), 0 0 28px rgba(250,204,21,.8);
}
.poster-card h4{
  margin:.4rem 0 .1rem 0; font-weight:700; letter-spacing:.02em;
  font-size:.92rem; color:#f9fafb;
}
.poster-card p{ margin:0; color:#cbd5f5; font-size:.82rem; }
.poster-frame{
  width:100%; aspect-ratio:2/3; border-radius:12px; overflow:hidden;
  border:1px solid rgba(148,163,184,.5);
  background: radial-gradient(circle at top, #020617 0%, #000 55%, #020617 100%);
  box-shadow:0 14px 30px rgba(0,0,0,.85);
}
.poster-img{ width:100%; height:100%; object-fit:cover; display:block; transition:transform .25s; }
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

def _poster_card_html(title: str, year, your_rating, imdb_rating, poster_url: Optional[str]) -> str:
    base = your_rating if pd.notna(your_rating) else imdb_rating
    border, glow = get_rating_colors(base)
    y = f" ({fmt_year(year)})" if pd.notna(year) else ""
    poster = (
        f'<div class="poster-frame"><img class="poster-img" src="{poster_url}" alt="{title}"></div>'
        if poster_url else
        '<div class="poster-frame"><div class="poster-placeholder"><div class="film-reel">🎞️</div><div class="film-reel-text">Sin póster</div></div></div>'
    )
    rating_line = (
        f"{'⭐ ' + fmt_rating(your_rating) if pd.notna(your_rating) else ''}"
        f"{' | ' if pd.notna(your_rating) and pd.notna(imdb_rating) else ''}"
        f"{'IMDb ' + fmt_rating(imdb_rating) if pd.notna(imdb_rating) else ''}"
    )
    return f"""
<div class="poster-card" style="border-color:{border}; box-shadow:0 0 0 1px rgba(15,23,42,.9), 0 0 22px {glow};">
  {poster}
  <h4>{title}{y}</h4>
  <p>{rating_line}</p>
</div>"""

def render_catalog_tab(df: pd.DataFrame, page_size: int = 24, use_tmdb_gallery: bool = True) -> None:
    st.markdown("### 📚 Resultados")
    cols = [c for c in ["Title","Year","Your Rating","IMDb Rating","Genres","Directors","URL"] if c in df.columns]
    if cols:
        show = df[cols].copy()
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

    left, mid, right = st.columns([1,2,1])
    with left:
        page_size = st.slider("Pósters por página", 12, 60, page_size, 12, key="gal_page_size")
    pages = max(math.ceil(total / page_size), 1)
    st.session_state.setdefault("gal_page", 1)
    if st.session_state.gal_page > pages: st.session_state.gal_page = pages

    with right:
        if st.button("Siguiente ▶", disabled=st.session_state.gal_page >= pages):
            st.session_state.gal_page += 1
    with left:
        if st.button("◀ Anterior", disabled=st.session_state.gal_page <= 1):
            st.session_state.gal_page -= 1
    with mid:
        st.caption(f"Página {st.session_state.gal_page} de {pages} — Mostrando {page_size} por página")

    start = (st.session_state.gal_page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end].copy()

    _grid_css_once()

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

    html = '<div class="poster-grid">' + "\n".join(cards) + "</div>"
    st.markdown(html, unsafe_allow_html=True)
