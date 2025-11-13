# modules/imdb_catalog.py
import math
import pandas as pd
import streamlit as st

from modules.utils import (
    get_tmdb_basic_info, get_tmdb_providers, get_tmdb_similar_movies,
    get_youtube_trailer_url, get_rating_colors, fmt_year, fmt_rating
)

def _apply_search(df_in: pd.DataFrame, query: str) -> pd.DataFrame:
    if not query: return df_in
    q = str(query).strip().lower()
    if "SearchText" not in df_in.columns: return df_in
    return df_in[df_in["SearchText"].str.contains(q, na=False, regex=False)]

def render_catalog_tab(
    filtered_df: pd.DataFrame,
    search_query: str,
    use_tmdb_gallery: bool,
    show_trailers: bool,
    consult_awards: bool,   # no-op aquí (compat)
):
    # --- KPIs
    st.markdown("### 📈 Resumen de resultados")
    c1,c2,c3 = st.columns(3)
    with c1: st.metric("Películas tras filtros + búsqueda", len(_apply_search(filtered_df, search_query)))
    with c2:
        col = pd.to_numeric(filtered_df.get("Your Rating"), errors="coerce")
        st.metric("Promedio de mi nota", f"{col.dropna().mean():.2f}" if col.notna().any() else "N/A")
    with c3:
        col = pd.to_numeric(filtered_df.get("IMDb Rating"), errors="coerce")
        st.metric("Promedio IMDb", f"{col.dropna().mean():.2f}" if col.notna().any() else "N/A")

    st.markdown("### 📚 Resultados")
    view = _apply_search(filtered_df.copy(), search_query)

    cols_to_show = [c for c in ["Title","Year","Your Rating","IMDb Rating","Genres","Directors","URL"] if c in view.columns]
    table_df = view[cols_to_show].copy()
    disp = table_df.copy()
    if "Year" in disp: disp["Year"] = disp["Year"].apply(fmt_year)
    if "Your Rating" in disp: disp["Your Rating"] = disp["Your Rating"].apply(fmt_rating)
    if "IMDb Rating" in disp: disp["IMDb Rating"] = disp["IMDb Rating"].apply(fmt_rating)
    st.dataframe(disp, hide_index=True, use_container_width=True)

    # ----------------- Galería -----------------
    st.markdown("---")
    st.markdown("### 🧱 Galería visual (paginada)")

    total = len(view)
    if total == 0:
        st.info("No hay películas para mostrar en la galería.")
        return

    page_size = st.slider("Películas por página", 12, 60, 24, 12, key="gallery_page_size")
    num_pages = max(math.ceil(total / page_size), 1)
    if "gallery_page" not in st.session_state: st.session_state.gallery_page = 1
    col_nav1, col_nav2, col_nav3 = st.columns([1,2,1])
    with col_nav1:
        if st.button("◀ Anterior", disabled=st.session_state.gallery_page<=1):
            st.session_state.gallery_page -= 1
    with col_nav3:
        if st.button("Siguiente ▶", disabled=st.session_state.gallery_page>=num_pages):
            st.session_state.gallery_page += 1
    with col_nav2:
        st.caption(f"Página {st.session_state.gallery_page} de {num_pages}")

    start = (st.session_state.gallery_page-1) * page_size
    end = start + page_size
    page_df = view.iloc[start:end].copy()

    # Render
    cards_html = ['<div class="movie-gallery-grid">']
    for _, r in page_df.iterrows():
        title = r.get("Title","(sin título)")
        year  = r.get("Year")
        my    = r.get("Your Rating")
        imdb  = r.get("IMDb Rating")

        base_rating = my if pd.notna(my) else imdb
        border, glow = get_rating_colors(base_rating)

        poster_url, tmdb_rating, tmdb_id = None, None, None
        if use_tmdb_gallery:
            tmdb_info = get_tmdb_basic_info(title, year)
            if tmdb_info:
                poster_url = tmdb_info.get("poster_url")
                tmdb_rating = tmdb_info.get("vote_average")
                tmdb_id = tmdb_info.get("id")

        poster_html = (
            f'<img src="{poster_url}" alt="{title}">' if poster_url else
            '<div style="width:100%;aspect-ratio:2/3;border:1px dashed #475569;border-radius:12px;display:flex;align-items:center;justify-content:center;">Sin póster</div>'
        )
        line_top = []
        if pd.notna(my):   line_top.append(f"⭐ {fmt_rating(my)}")
        if pd.notna(imdb): line_top.append(f"IMDb {fmt_rating(imdb)}")
        if tmdb_rating is not None: line_top.append(f"TMDb {fmt_rating(tmdb_rating)}")
        meta = " | ".join(line_top) if line_top else "&nbsp;"

        cards_html.append(
            f"""
<div class="poster-card" style="border-color:{border}; box-shadow: 0 0 0 1px rgba(15,23,42,0.9), 0 0 20px {glow};">
  {poster_html}
  <h4>{title} {f"({fmt_year(year)})" if pd.notna(year) else ""}</h4>
  <p>{meta}</p>
</div>
"""
        )
    cards_html.append("</div>")
    st.markdown("\n".join(cards_html), unsafe_allow_html=True)

def render_pick_tab(filtered_df: pd.DataFrame, show_trailers: bool, consult_awards: bool):
    import random
    st.markdown("### 🎯 Recomendar una película ahora")
    if filtered_df.empty:
        st.info("No hay datos bajo los filtros actuales.")
        return
    if st.button("Recomendar"):
        pool = filtered_df.copy()
        notas = pd.to_numeric(pool.get("Your Rating"), errors="coerce").fillna(0)
        pesos = (notas + 1).tolist()
        idx = random.choices(pool.index.tolist(), weights=pesos, k=1)[0]
        r = pool.loc[idx]
        title = r.get("Title","(sin título)")
        year  = r.get("Year")
        my    = r.get("Your Rating")
        imdb  = r.get("IMDb Rating")
        border, glow = get_rating_colors(my if pd.notna(my) else imdb)

        tmdb = get_tmdb_basic_info(title, year)
        poster_url = tmdb.get("poster_url") if tmdb else None
        tmdb_rating = tmdb.get("vote_average") if tmdb else None
        tmdb_id = tmdb.get("id") if tmdb else None

        cols = st.columns([1,2])
        with cols[0]:
            if poster_url: st.image(poster_url, use_container_width=True)
            if show_trailers:
                yt = get_youtube_trailer_url(title, year)
                if yt: st.video(yt)
        with cols[1]:
            st.markdown(
                f"""
<div class="poster-card" style="border-color:{border}; box-shadow: 0 0 0 1px rgba(15,23,42,0.9), 0 0 26px {glow};">
  <h4 style="margin:.2rem 0 .4rem">{title} {f"({fmt_year(year)})" if pd.notna(year) else ""}</h4>
  <p>
    {f"⭐ {fmt_rating(my)} · " if pd.notna(my) else ""}{f"IMDb {fmt_rating(imdb)} · " if pd.notna(imdb) else ""}{f"TMDb {fmt_rating(tmdb_rating)}" if tmdb_rating is not None else ""}
  </p>
</div>
                """,
                unsafe_allow_html=True
            )

        if tmdb_id:
            st.markdown("#### 🌐 Similares (TMDb)")
            sims = get_tmdb_similar_movies(tmdb_id, max_results=8)
            if sims:
                cols = st.columns(4)
                for i, m in enumerate(sims):
                    with cols[i%4]:
                        st.write(f"**{m.get('title','')}** {f'({m.get(\"year\")})' if m.get('year') else ''}")
                        if m.get("poster_url"):
                            st.image(m["poster_url"], use_container_width=True)
                        st.caption(f"TMDb: {fmt_rating(m.get('vote_average'))}")
            else:
                st.caption("Sin recomendaciones externas.")
