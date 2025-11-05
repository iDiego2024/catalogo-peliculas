# ============================================================
#                        FAVORITAS
# ============================================================

st.markdown("---")
st.markdown("## ⭐ Tus favoritas (nota ≥ 9) en este filtro")

with st.expander("Ver favoritas", expanded=False):
    if "Your Rating" in filtered.columns:
        fav = filtered[filtered["Your Rating"] >= 9].copy()
        if not fav.empty:
            fav = fav.sort_values(["Your Rating", "Year"], ascending=[False, True])
            fav = fav.head(12)

            for _, row in fav.iterrows():
                titulo = row.get("Title", "Sin título")
                year = row.get("Year", "")
                nota = row.get("Your Rating", "")
                imdb_rating = row.get("IMDb Rating", "")
                genres = row.get("Genres", "")
                directors = row.get("Directors", "")
                url = row.get("URL", "")

                # Etiqueta de cabecera para cada favorita
                if pd.notna(nota):
                    etiqueta = f"{int(nota)}/10 — {titulo}"
                else:
                    etiqueta = f"{titulo}"

                if pd.notna(year):
                    etiqueta += f" ({int(year)})"

                st.markdown(f"### {etiqueta}")

                col_img, col_info = st.columns([1, 3])

                with col_img:
                    if show_posters_fav:
                        poster_url = get_poster_url(titulo, year)
                        if isinstance(poster_url, str) and poster_url:
                            st.image(poster_url)
                        else:
                            st.write("Sin póster")
                    else:
                        st.write("Póster desactivado (actívalo en la barra lateral).")

                with col_info:
                    if isinstance(genres, str) and genres:
                        st.write(f"**Géneros:** {genres}")
                    if isinstance(directors, str) and directors:
                        st.write(f"**Director(es):** {directors}")
                    if pd.notna(imdb_rating):
                        st.write(f"**IMDb:** {imdb_rating}")
                    if isinstance(url, str) and url.startswith("http"):
                        st.write(f"[Ver en IMDb]({url})")

                st.markdown("---")
        else:
            st.write("No hay películas con nota ≥ 9 bajo estos filtros.")
    else:
        st.write("No se encontró la columna 'Your Rating' en el CSV.")
