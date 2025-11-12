# modules/imdb_catalog.py
# Catálogo + tabla + GALERÍA VISUAL paginada

import streamlit as st
import pandas as pd
import math

from .utils import (
    fmt_year, fmt_rating, normalize_title, get_rating_colors,
    get_tmdb_basic_info, get_tmdb_providers, get_youtube_trailer_url,
    get_omdb_awards,
)

def _ensure_catalog_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Garantiza columnas mínimas y deriva GenreList/NormTitle/YearInt."""
    out = df.copy()

    # columnas base
    for col in ["Title", "Year", "Your Rating", "IMDb Rating", "Genres", "Directors", "URL"]:
        if col not in out.columns:
            out[col] = None

    # YearInt sin comas ni rarezas
    if "YearInt" not in out.columns:
        out["YearInt"] = out["Year"].fillna(-1).astype(float).astype(int)

    # lista de géneros
    if "GenreList" not in out.columns:
        out["Genres"] = out["Genres"].fillna("")
        out["GenreList"] = out["Genres"].apply(
            lambda x: [] if pd.isna(x) or x == "" else str(x).split(", ")
        )

    # columna de búsqueda
    if "SearchText" not in out.columns:
        search_cols = [c for c in ["Title","Original Title","Directors","Genres","Year","Your Rating","IMDb Rating"] if c in out.columns]
        out["SearchText"] = (
            out[search_cols].astype(str).apply(lambda row: " ".join(row), axis=1).str.lower()
            if search_cols else ""
        )

    # normalización de título
    if "NormTitle" not in out.columns:
        out["NormTitle"] = out["Title"].apply(normalize_title)

    return out


def render_catalog_tab(df_in: pd.DataFrame):
    """Dibuja resumen, tabla y GALERÍA paginada."""
    df = _ensure_catalog_columns(df_in)

    # --------- LECTURA DE FLAGS DESDE SESSION STATE (con defaults) ----------
    show_posters_fav = st.session_state.get("show_posters_fav", True)
    use_tmdb_gallery = st.session_state.get("use_tmdb_gallery", True)
    show_trailers    = st.session_state.get("show_trailers", True)
    show_awards      = st.session_state.get("show_awards", False)

    # ----------------- Filtros (usamos los de la barra lateral ya creada) -----------------
    # Derivamos los valores que la app principal ya establece:
    year_range   = st.session_state.get("year_range", (int(df["YearInt"].replace(-1, pd.NA).min(skipna=True) or 0),
                                                       int(df["YearInt"].replace(-1, pd.NA).max(skipna=True) or 9999)))
    rating_range = st.session_state.get("rating_range", (0,10))
    selected_genres    = st.session_state.get("selected_genres", [])
    selected_directors = st.session_state.get("selected_directors", [])
    order_by     = st.session_state.get("order_by", "Your Rating")
    order_asc    = st.session_state.get("order_asc", False)
    search_query = st.session_state.get("busqueda_unica", "")

    # Aplicar filtros como en tu app original
    filtered = df.copy()
    filtered = filtered[(filtered["Year"].fillna(0) >= year_range[0]) & (filtered["Year"].fillna(9999) <= year_range[1])]
    filtered = filtered[(filtered["Your Rating"].fillna(-1) >= rating_range[0]) & (filtered["Your Rating"].fillna(99) <= rating_range[1])]

    if selected_genres:
        filtered = filtered[filtered["GenreList"].apply(lambda gl: all(g in gl for g in selected_genres))]

    if selected_directors:
        def _has_any(cell):
            if pd.isna(cell):
                return False
            dirs = [d.strip() for d in str(cell).split(",") if d.strip()]
            return any(d in dirs for d in selected_directors)
        filtered = filtered[filtered["Directors"].apply(_has_any)]

    # Búsqueda texto libre
    if search_query:
        q = str(search_query).strip().lower()
        filtered_view = filtered[filtered["SearchText"].str.contains(q, na=False, regex=False)]
    else:
        filtered_view = filtered

    # Orden
    if order_by == "Aleatorio":
        if not filtered_view.empty:
            filtered_view = filtered_view.sample(frac=1, random_state=None)
    elif order_by in filtered_view.columns:
        filtered_view = filtered_view.sort_values(order_by, ascending=order_asc)

    # ----------------- RESUMEN -----------------
    st.markdown("## 📈 Resumen de resultados")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Películas tras filtros + búsqueda", len(filtered_view))
    with col2:
        if filtered_view["Your Rating"].notna().any():
            st.metric("Promedio de mi nota", f"{filtered_view['Your Rating'].mean():.2f}")
        else:
            st.metric("Promedio de mi nota", "N/A")
    with col3:
        if filtered_view["IMDb Rating"].notna().any():
            st.metric("Promedio IMDb", f"{filtered_view['IMDb Rating'].mean():.2f}")
        else:
            st.metric("Promedio IMDb", "N/A")

    # ----------------- TABLA -----------------
    st.markdown("### 📚 Tabla de resultados")
    cols_to_show = [c for c in ["Title","Year","Your Rating","IMDb Rating","Genres","Directors","Date Rated","URL"] if c in filtered_view.columns]
    table_df = filtered_view[cols_to_show].copy()

    display_df = table_df.copy()
    if "Year" in display_df.columns:
        display_df["Year"] = display_df["Year"].apply(fmt_year)  # <- sin comas
    if "Your Rating" in display_df.columns:
        display_df["Your Rating"] = display_df["Your Rating"].apply(fmt_rating)
    if "IMDb Rating" in display_df.columns:
        display_df["IMDb Rating"] = display_df["IMDb Rating"].apply(fmt_rating)

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Descarga CSV filtrado
    st.download_button(
        label="⬇️ Descargar resultados filtrados (CSV)",
        data=table_df.to_csv(index=False).encode("utf-8"),
        file_name="mis_peliculas_filtradas.csv",
        mime="text/csv",
    )

    # ----------------- GALERÍA VISUAL PAGINADA -----------------
    st.markdown("---")
    st.markdown("## 🧱 Galería visual (pósters en grid por páginas)")

    if show_awards:
        st.caption("⚠ OMDb (premios) está activado: la primera carga de cada página puede tardar un poco más.")

    total_pelis = len(filtered_view)
    if total_pelis == 0:
        st.info("No hay películas bajo los filtros + búsqueda actuales para la galería.")
        return

    page_size = st.slider(
        "Películas por página en la galería",
        min_value=12, max_value=60, value=24, step=12, key="gallery_page_size"
    )

    num_pages = max(math.ceil(total_pelis / page_size), 1)
    if "gallery_current_page" not in st.session_state:
        st.session_state.gallery_current_page = 1
    if st.session_state.gallery_current_page > num_pages:
        st.session_state.gallery_current_page = num_pages
    if st.session_state.gallery_current_page < 1:
        st.session_state.gallery_current_page = 1

    col_nav1, col_nav2, col_nav3 = st.columns([1,2,1])
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

    # grid HTML
    cards_html = ['<div class="movie-gallery-grid">']

    for _, row in page_df.iterrows():
        titulo = row.get("Title", "Sin título")
        year   = row.get("Year", "")
        nota   = row.get("Your Rating", "")
        imdb_r = row.get("IMDb Rating", "")
        genres = row.get("Genres", "")
        dirs   = row.get("Directors", "")
        url    = row.get("URL", "")

        base_rating = nota if pd.notna(nota) else imdb_r
        border_color, glow_color = get_rating_colors(base_rating)

        poster_url = None
        tmdb_rating = None
        availability = None
        tmdb_id = None

        if use_tmdb_gallery:
            tmdb_info = get_tmdb_basic_info(titulo, year)
            if tmdb_info:
                poster_url = tmdb_info.get("poster_url")
                tmdb_rating = tmdb_info.get("vote_average")
                tmdb_id = tmdb_info.get("id")
                availability = get_tmdb_providers(tmdb_id, country="CL")

        # póster
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

        year_str  = f" ({fmt_year(year)})" if pd.notna(year) else ""
        nota_str  = f"⭐ Mi nota: {fmt_rating(nota)}" if pd.notna(nota) else ""
        imdb_str  = f"IMDb: {fmt_rating(imdb_r)}" if pd.notna(imdb_r) else ""
        tmdb_str  = f"TMDb: {fmt_rating(tmdb_rating)}" if tmdb_rating is not None else "TMDb: N/A"

        # premios (opcional)
        if show_awards:
            awards = get_omdb_awards(titulo, year)
        else:
            awards = None

        if not show_awards:
            awards_text = "Premios no consultados (OMDb desactivado)."
        elif awards is None:
            awards_text = "Sin datos de premios (OMDb)."
        elif isinstance(awards, dict) and "error" in awards:
            awards_text = f"Error OMDb: {awards['error']}"
        else:
            base_parts = []
            if awards.get("oscars", 0):         base_parts.append(f"🏆 {awards['oscars']} Oscar(s)")
            if awards.get("emmys", 0):          base_parts.append(f"📺 {awards['emmys']} Emmy(s)")
            if awards.get("baftas", 0):         base_parts.append(f"🎭 {awards['baftas']} BAFTA(s)")
            if awards.get("golden_globes", 0):  base_parts.append(f"🌐 {awards['golden_globes']} Globo(s) de Oro")
            if awards.get("palme_dor", False):  base_parts.append("🌴 Palma de Oro")
            extra_parts = []
            if awards.get("oscars_nominated", 0):  extra_parts.append(f"🎬 Nominada a {awards['oscars_nominated']} Oscar(s)")
            if awards.get("total_wins", 0):        extra_parts.append(f"{awards['total_wins']} premios totales")
            if awards.get("total_nominations", 0): extra_parts.append(f"{awards['total_nominations']} nominaciones totales")
            parts = base_parts + extra_parts
            awards_text = "Sin grandes premios detectados." if not parts else " · ".join(parts)
            if awards.get("raw"):
                awards_text += f"<br><span style='font-size:0.75rem;color:#9ca3af;'>OMDb: {awards['raw']}</span>"

        if availability is None:
            platforms = []
            link = None
        else:
            platforms = availability.get("platforms") or []
            link = availability.get("link")

        platforms_str = ", ".join(platforms) if platforms else "Sin datos para Chile (CL)"
        link_html = (f'<a href="{link}" target="_blank">Ver streaming en TMDb (CL)</a>' if link else "Sin enlace de streaming disponible")
        imdb_link_html = (f'<a href="{url}" target="_blank">Ver en IMDb</a>' if isinstance(url, str) and url.startswith("http") else "")

        # reseñas
        # usamos un pequeño buscador en español (en utils está la función si la tienes);
        # si no, remueve este bloque o deja un enlace vacío.
        try:
            from .utils import get_spanish_review_link
            reseñas_url = get_spanish_review_link(titulo, year)
            reseñas_html = (f'<a href="{reseñas_url}" target="_blank">Reseñas en español</a>' if reseñas_url else "")
        except Exception:
            reseñas_html = ""

        genres_html = (f"<b>Géneros:</b> {genres}<br>" if isinstance(genres, str) and genres else "")
        directors_html = (f"<b>Director(es):</b> {dirs}<br>" if isinstance(dirs, str) and dirs else "")

        card_html = f"""
<div class="movie-card movie-card-grid" style="
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
