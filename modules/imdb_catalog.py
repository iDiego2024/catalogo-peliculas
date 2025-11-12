import streamlit as st
import pandas as pd
import math

from modules.utils import (
    get_tmdb_basic_info, get_tmdb_providers, get_youtube_trailer_url,
    get_spanish_review_link, get_rating_colors, fmt_year, fmt_rating
)

def _apply_filters(df):
    year_range = st.session_state.get("year_range", (0, 9999))
    rating_range = st.session_state.get("rating_range", (0, 10))
    selected_genres = st.session_state.get("selected_genres", [])
    selected_directors = st.session_state.get("selected_directors", [])
    order_by = st.session_state.get("order_by", "Your Rating")
    order_asc = st.session_state.get("order_asc", False)

    filtered = df.copy()

    if "Year" in filtered.columns:
        filtered = filtered[
            (filtered["Year"] >= year_range[0]) &
            (filtered["Year"] <= year_range[1])
        ]

    if "Your Rating" in filtered.columns:
        filtered = filtered[
            (filtered["Your Rating"] >= rating_range[0]) &
            (filtered["Your Rating"] <= rating_range[1])
        ]

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

    # Orden global
    if order_by == "Aleatorio":
        if not filtered.empty:
            filtered = filtered.sample(frac=1, random_state=None)
    elif order_by in filtered.columns:
        filtered = filtered.sort_values(order_by, ascending=order_asc)

    return filtered

def _apply_search(df_in, query):
    if not query:
        return df_in
    q = query.strip().lower()
    if "SearchText" not in df_in.columns:
        return df_in
    return df_in[df_in["SearchText"].str.contains(q, na=False, regex=False)]

def render_catalog_tab(df, search_query):
    # métricas resumen
    filtered = _apply_filters(df)
    filtered_view = _apply_search(filtered.copy(), search_query)

    st.markdown("## 📈 Resumen de resultados")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Películas tras filtros + búsqueda", len(filtered_view))
    with col2:
        if "Your Rating" in filtered_view.columns and filtered_view["Your Rating"].notna().any():
            st.metric("Promedio de mi nota", f"{filtered_view['Your Rating'].mean():.2f}")
        else:
            st.metric("Promedio de mi nota", "N/A")
    with col3:
        if "IMDb Rating" in filtered_view.columns and filtered_view["IMDb Rating"].notna().any():
            st.metric("Promedio IMDb", f"{filtered_view['IMDb Rating'].mean():.2f}")
        else:
            st.metric("Promedio IMDb", "N/A")

    # tabla principal
    st.markdown("### 📚 Tabla de resultados")
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

    # Galería visual
    st.markdown("---")
    st.markdown("## 🧱 Galería visual (pósters en grid por páginas)")

    use_tmdb_gallery = st.session_state.get("use_tmdb_gallery", True)
    show_awards = st.session_state.get("show_awards", False)

    if show_awards:
        st.caption("⚠ OMDb (premios) está activado: la primera carga de cada página puede tardar un poco más.")

    total_pelis = len(filtered_view)
    if total_pelis == 0:
        st.info("No hay películas bajo los filtros + búsqueda actuales para la galería.")
    else:
        page_size = st.slider("Películas por página en la galería", 12, 60, 24, 12, key="gallery_page_size")
        num_pages = max(math.ceil(total_pelis / page_size), 1)

        if "gallery_current_page" not in st.session_state:
            st.session_state.gallery_current_page = 1
        if st.session_state.gallery_current_page > num_pages:
            st.session_state.gallery_current_page = num_pages
        if st.session_state.gallery_current_page < 1:
            st.session_state.gallery_current_page = 1

        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
        with col_nav1:
            prev_disabled = st.session_state.gallery_current_page <= 1
            if st.button("◀ Anterior", disabled=prev_disabled, key="gallery_prev"):
                if st.session_state.gallery_current_page > 1:
                    st.session_state.gallery_current_page -= 1
        with col_nav3:
            next_disabled = st.session_state.gallery_current_page >= num_pages
            if st.button("Siguiente ▶", disabled=next_disabled, key="gallery_next"):
                if st.session_state.gallery_current_page < num_pages:
                    st.session_state.gallery_current_page += 1
        with col_nav2:
            st.caption(f"Página {st.session_state.gallery_current_page} de {num_pages}")

        st.caption(f"Mostrando pósters de tus películas filtradas: {total_pelis} en total · {page_size} por página.")

        current_page = st.session_state.gallery_current_page
        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        page_df = filtered_view.iloc[start_idx:end_idx].copy()

        cards_html = ['<div class="movie-gallery-grid">']

        for _, row in page_df.iterrows():
            titulo = row.get("Title", "Sin título")
            year = row.get("Year", "")
            nota = row.get("Your Rating", "")
            imdb_rating = row.get("IMDb Rating", "")
            genres = row.get("Genres", "")
            directors = row.get("Directors", "")
            url = row.get("URL", "")

            base_rating = nota if pd.notna(nota) else imdb_rating
            border_color, glow_color = get_rating_colors(base_rating)

            poster_url = None
            tmdb_rating = None
            availability = None

            if use_tmdb_gallery:
                tmdb_info = get_tmdb_basic_info(titulo, year)
                if tmdb_info:
                    poster_url = tmdb_info.get("poster_url")
                    tmdb_rating = tmdb_info.get("vote_average")
                    tmdb_id = tmdb_info.get("id")
                    availability = get_tmdb_providers(tmdb_id, country="CL")

            if isinstance(poster_url, str) and poster_url:
                poster_html = f"""
<div class="movie-poster-frame">
  <img src="{poster_url}" alt="{titulo}" class="movie-poster-img">
</div>
"""
            else:
                poster_html = """
<div class="movie-poster-frame">
  <div class="movie-poster-placeholder">
    <div class="film-reel-icon">🎞️</div>
    <div class="film-reel-text">Sin póster</div>
  </div>
</div>
"""

            year_str = f" ({fmt_year(year)})" if pd.notna(year) else ""
            nota_str = f"⭐ Mi nota: {fmt_rating(nota)}" if pd.notna(nota) else ""
            imdb_str = f"IMDb: {fmt_rating(imdb_rating)}" if pd.notna(imdb_rating) else ""
            tmdb_str = f"TMDb: {fmt_rating(tmdb_rating)}" if tmdb_rating is not None else "TMDb: N/A"

            # Premios (texto ligero)
            if st.session_state.get("show_awards", False):
                awards_text = "Consultando OMDb…"
                awards_raw = None
                try:
                    from modules.utils import get_omdb_awards
                    awards_raw = get_omdb_awards(titulo, year)
                except Exception:
                    awards_raw = None
                if not awards_raw:
                    awards_text = "Sin datos de premios (OMDb)."
                else:
                    awards_text = awards_raw
            else:
                awards_text = "Premios no consultados (OMDb desactivado)."

            platforms = []
            link = None
            if availability:
                platforms = availability.get("platforms") or []
                link = availability.get("link")

            platforms_str = ", ".join(platforms) if platforms else "Sin datos para Chile (CL)"
            link_html = (f'<a href="{link}" target="_blank">Ver streaming en TMDb (CL)</a>' if link else "Sin enlace de streaming disponible")
            imdb_link_html = (f'<a href="{url}" target="_blank">Ver en IMDb</a>' if isinstance(url, str) and url.startswith("http") else "")

            reseñas_url = get_spanish_review_link(titulo, year)
            reseñas_html = (f'<a href="{reseñas_url}" target="_blank">Reseñas en español</a>' if reseñas_url else "")

            genres_html = (f"<b>Géneros:</b> {genres}<br>" if isinstance(genres, str) and genres else "")
            directors_html = (f"<b>Director(es):</b> {directors}<br>" if isinstance(directors, str) and directors else "")

            card_html = f"""
<div class="movie-card" style="
    border-color: {border_color};
    box-shadow: 0 0 0 1px rgba(15,23,42,0.9), 0 0 20px {glow_color};
">
  {poster_html}
  <div class="movie-title">{titulo}{year_str}</div>
  <div class="movie-sub">
    {nota_str}<br>
    {imdb_str}<br>
    {tmdb_str}<br>
    {genres_html}
    {directors_html}
    <b>Premios:</b> {awards_text}<br>
    <b>Streaming (CL):</b> {platforms_str}<br>
    {link_html}<br>
    {imdb_link_html}<br>
    <b>Reseñas:</b> {reseñas_html}
  </div>
</div>
"""
            cards_html.append(card_html)

        cards_html.append("</div>")
        st.markdown("\n".join(cards_html), unsafe_allow_html=True)

def render_what_to_watch(df):
    import random
    from modules.utils import get_tmdb_basic_info, get_tmdb_providers, get_youtube_trailer_url, fmt_year, fmt_rating, get_spanish_review_link, get_rating_colors

    st.markdown("## 🎲 ¿Qué ver hoy? (según mi propio gusto)")
    st.write("Elijo una película de mi catálogo usando mis notas, año y disponibilidad en streaming.")

    with st.expander("Ver recomendación aleatoria según mi gusto", expanded=True):
        modo = st.selectbox(
            "Modo de recomendación",
            ["Entre todas las películas filtradas", "Solo mis favoritas (nota ≥ 9)", "Entre mis 8–10 de los últimos 20 años"]
        )

        # reusar filtros básicos, sin búsqueda
        filtered = _apply_filters(df)

        if st.button("Recomendar una película", key="btn_random_reco"):
            pool = filtered.copy()

            if modo == "Solo mis favoritas (nota ≥ 9)":
                if "Your Rating" in pool.columns:
                    pool = pool[pool["Your Rating"] >= 9]
                else:
                    pool = pool.iloc[0:0]
            elif modo == "Entre mis 8–10 de los últimos 20 años":
                if "Your Rating" in pool.columns and "Year" in pool.columns:
                    pool = pool[(pool["Your Rating"] >= 8) & (pool["Year"].notna()) & (pool["Year"] >= (pd.Timestamp.now().year - 20))]
                else:
                    pool = pool.iloc[0:0]

            if pool.empty:
                st.warning("No hay películas que cumplan con el modo seleccionado y los filtros actuales.")
                return

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
            genres = peli.get("Genres", "")
            directors = peli.get("Directors", "")
            url = peli.get("URL", "")

            base_rating = nota if pd.notna(nota) else imdb_rating
            border_color, glow_color = get_rating_colors(base_rating)

            tmdb_info = get_tmdb_basic_info(titulo, year)
            if tmdb_info:
                tmdb_rating = tmdb_info.get("vote_average")
                poster_url = tmdb_info.get("poster_url")
                tmdb_id = tmdb_info.get("id")
                availability = get_tmdb_providers(tmdb_id, country="CL")
            else:
                tmdb_rating = None
                poster_url = None
                tmdb_id = None
                availability = None

            tmdb_str = f"TMDb: {fmt_rating(tmdb_rating)}" if tmdb_rating is not None else "TMDb: N/A"

            if st.session_state.get("show_awards", False):
                try:
                    from modules.utils import get_omdb_awards
                    awards_raw = get_omdb_awards(titulo, year)
                except Exception:
                    awards_raw = None
                awards_text = awards_raw or "Sin datos de premios (OMDb)."
            else:
                awards_text = "Premios no consultados (OMDb desactivado)."

            platforms = []
            link = None
            if availability is not None:
                platforms = availability.get("platforms") or []
                link = availability.get("link")

            platforms_str = ", ".join(platforms) if platforms else "Sin datos para Chile (CL)"
            link_html = (f'<a href="{link}" target="_blank">Ver opciones de streaming en TMDb (CL)</a>' if link else "Sin enlace de streaming disponible")
            imdb_link_html = (f'<a href="{url}" target="_blank">Ver en IMDb</a>' if isinstance(url, str) and url.startswith("http") else "")
            reseñas_url = get_spanish_review_link(titulo, year)
            reseñas_html = (f'<a href="{reseñas_url}" target="_blank">Reseñas en español</a>' if reseñas_url else "")

            col_img, col_info = st.columns([1, 3])

            with col_img:
                if isinstance(poster_url, str) and poster_url:
                    try:
                        st.image(poster_url)
                    except Exception:
                        st.write("Sin póster")
                else:
                    st.write("Sin póster")
                if st.session_state.get("show_trailers", True):
                    trailer_url = get_youtube_trailer_url(titulo, year)
                    if trailer_url:
                        st.video(trailer_url)

            with col_info:
                st.markdown(
                    f"""
<div class="movie-card" style="border-color: {border_color}; box-shadow: 0 0 0 1px rgba(15,23,42,0.9), 0 0 26px {glow_color}; margin-bottom: 10px;">
  <div class="movie-title">{titulo}{f" ({int(year)})" if pd.notna(year) else ""}</div>
  <div class="movie-sub">
    {f"⭐ Mi nota: {fmt_rating(nota)}<br>" if pd.notna(nota) else ""}
    {f"IMDb: {fmt_rating(imdb_rating)}<br>" if pd.notna(imdb_rating) else ""}
    {tmdb_str}<br>
    <b>Géneros:</b> {genres}<br>
    <b>Director(es):</b> {directors}<br>
    <b>Premios:</b> {awards_text}<br>
    <b>Streaming (CL):</b> {platforms_str}<br>
    {link_html}<br>
    {imdb_link_html}<br>
    <b>Reseñas:</b> {reseñas_html}
  </div>
</div>
""",
                    unsafe_allow_html=True,
                )
