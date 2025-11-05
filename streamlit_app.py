# ============================================================
#                  ANÁLISIS Y TENDENCIAS
# ============================================================

st.markdown("---")
st.markdown("## 📊 Análisis y tendencias")

with st.expander("Ver análisis y tendencias", expanded=False):
    if filtered.empty:
        st.info("No hay datos bajo los filtros actuales para mostrar gráficos.")
    else:
        # ----------------------------------------------------
        # 1) Películas por año
        # ----------------------------------------------------
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Películas por año**")
            by_year = (
                filtered[filtered["Year"].notna()]
                .groupby("Year")
                .size()
                .reset_index(name="Count")
                .sort_values("Year")
            )
            if not by_year.empty:
                by_year_display = by_year.copy()
                by_year_display["Year"] = by_year_display["Year"].astype(int).astype(str)
                by_year_display = by_year_display.set_index("Year")
                st.line_chart(by_year_display)
            else:
                st.write("Sin datos de año.")

        # ----------------------------------------------------
        # 2) Distribución de tu nota
        # ----------------------------------------------------
        with col_b:
            st.markdown("**Distribución de tu nota (Your Rating)**")
            if "Your Rating" in filtered.columns and filtered["Your Rating"].notna().any():
                ratings_counts = (
                    filtered["Your Rating"]
                    .round()
                    .value_counts()
                    .sort_index()
                    .reset_index()
                )
                ratings_counts.columns = ["Rating", "Count"]
                ratings_counts["Rating"] = ratings_counts["Rating"].astype(int).astype(str)
                ratings_counts = ratings_counts.set_index("Rating")
                st.bar_chart(ratings_counts)
            else:
                st.write("No hay notas tuyas disponibles.")

        # ----------------------------------------------------
        # 3) Tendencia de tus calificaciones por año (promedio + móvil)
        # ----------------------------------------------------
        st.markdown("### 📈 Tendencia de tus calificaciones por año")

        if "Year" in filtered.columns and "Your Rating" in filtered.columns:
            tmp = filtered[
                filtered["Year"].notna() &
                filtered["Your Rating"].notna()
            ].copy()
            if not tmp.empty:
                by_year_rating = (
                    tmp.groupby("Year")["Your Rating"]
                    .mean()
                    .reset_index()
                    .sort_values("Year")
                )
                by_year_rating["YearInt"] = by_year_rating["Year"].astype(int)
                by_year_rating["MA_3"] = (
                    by_year_rating["Your Rating"]
                    .rolling(window=3, min_periods=1)
                    .mean()
                )

                long_trend = by_year_rating.melt(
                    id_vars="YearInt",
                    value_vars=["Your Rating", "MA_3"],
                    var_name="Serie",
                    value_name="Rating"
                )

                trend_chart = (
                    alt.Chart(long_trend)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("YearInt:O", title="Año"),
                        y=alt.Y("Rating:Q", title="Nota media"),
                        color=alt.Color("Serie:N", title="Serie", scale=alt.Scale(
                            domain=["Your Rating", "MA_3"],
                            range=["#60a5fa", "#f97316"]
                        )),
                        tooltip=["YearInt", "Serie", "Rating"]
                    )
                    .properties(height=350)
                )
                st.altair_chart(trend_chart, use_container_width=True)
                st.caption("Línea azul: promedio anual. Naranja: promedio móvil de 3 años (suaviza la tendencia).")
            else:
                st.write("No hay suficientes datos (año + tu nota) para calcular la tendencia.")
        else:
            st.write("Faltan columnas 'Year' o 'Your Rating' para la tendencia.")

        # ----------------------------------------------------
        # 4) IMDb promedio por década
        # ----------------------------------------------------
        col_c, col_d = st.columns(2)
        with col_c:
            st.markdown("**IMDb promedio por década**")
            if "IMDb Rating" in filtered.columns and filtered["IMDb Rating"].notna().any():
                tmp_dec = filtered[filtered["Year"].notna()].copy()
                if not tmp_dec.empty:
                    tmp_dec["Decade"] = (tmp_dec["Year"] // 10 * 10).astype(int)
                    decade_imdb = (
                        tmp_dec.groupby("Decade")["IMDb Rating"]
                        .mean()
                        .reset_index()
                        .sort_values("Decade")
                    )
                    decade_imdb["Decade"] = decade_imdb["Decade"].astype(str)
                    decade_imdb = decade_imdb.set_index("Decade")
                    st.line_chart(decade_imdb)
                else:
                    st.write("No hay datos suficientes de año para calcular décadas.")
            else:
                st.write("No hay IMDb Rating disponible.")

        # ----------------------------------------------------
        # 5) Desviación tu nota vs IMDb por año
        # ----------------------------------------------------
        with col_d:
            st.markdown("**¿Más generoso o más crítico? (Tu nota - IMDb por año)**")
            if (
                "Your Rating" in filtered.columns
                and "IMDb Rating" in filtered.columns
            ):
                tmp_diff = filtered[
                    filtered["Year"].notna() &
                    filtered["Your Rating"].notna() &
                    filtered["IMDb Rating"].notna()
                ].copy()
                if not tmp_diff.empty:
                    tmp_diff["Diff"] = tmp_diff["Your Rating"] - tmp_diff["IMDb Rating"]
                    diff_by_year = (
                        tmp_diff.groupby("Year")["Diff"]
                        .mean()
                        .reset_index()
                        .sort_values("Year")
                    )
                    diff_by_year["YearInt"] = diff_by_year["Year"].astype(int)

                    diff_chart = (
                        alt.Chart(diff_by_year)
                        .mark_line(point=True)
                        .encode(
                            x=alt.X("YearInt:O", title="Año"),
                            y=alt.Y("Diff:Q", title="Tu nota - IMDb"),
                            tooltip=["YearInt", "Diff"]
                        )
                        .properties(height=300)
                    )
                    st.altair_chart(diff_chart, use_container_width=True)
                    st.caption(
                        "Valores por encima de 0 ⇒ sueles puntuar por encima de IMDb ese año. "
                        "Por debajo de 0 ⇒ más duro que IMDb."
                    )
                else:
                    st.write("No hay suficientes películas con tu nota e IMDb para este análisis.")
            else:
                st.write("Faltan columnas 'Your Rating' o 'IMDb Rating'.")

        # ----------------------------------------------------
        # 6) Mapa de calor: tu nota media por género y década
        # ----------------------------------------------------
        st.markdown("### 🎭 Mapa de calor: tu nota media por género y década")

        if "GenreList" in filtered.columns and "Your Rating" in filtered.columns:
            tmp = filtered.copy()
            tmp = tmp[tmp["Year"].notna() & tmp["Your Rating"].notna()]
            if not tmp.empty:
                tmp["Decade"] = (tmp["Year"] // 10 * 10).astype(int).astype(str)
                tmp_genres = tmp.explode("GenreList")
                tmp_genres = tmp_genres[
                    tmp_genres["GenreList"].notna() &
                    (tmp_genres["GenreList"] != "")
                ]
                if not tmp_genres.empty:
                    heat_df = (
                        tmp_genres
                        .groupby(["GenreList", "Decade"])["Your Rating"]
                        .mean()
                        .reset_index()
                    )
                    heat_chart = (
                        alt.Chart(heat_df)
                        .mark_rect()
                        .encode(
                            x=alt.X("Decade:N", title="Década"),
                            y=alt.Y("GenreList:N", title="Género"),
                            color=alt.Color(
                                "Your Rating:Q",
                                title="Tu nota media",
                                scale=alt.Scale(scheme="viridis"),
                            ),
                            tooltip=["GenreList", "Decade", "Your Rating"],
                        )
                        .properties(height=400)
                    )
                    st.altair_chart(heat_chart, use_container_width=True)
                else:
                    st.write("No hay datos suficientes de géneros para el mapa de calor.")
            else:
                st.write("No hay datos suficientes (año + tu nota) para el mapa de calor.")
        else:
            st.write("Faltan columnas necesarias para el mapa de calor.")

        # ----------------------------------------------------
        # 7) Qué géneros te gustan últimamente (género vs año reciente)
        # ----------------------------------------------------
        st.markdown("### 🕒 Qué tipo de cine te gusta más últimamente")

        if "GenreList" in filtered.columns and "Your Rating" in filtered.columns:
            tmp = filtered.copy()
            tmp = tmp[tmp["Year"].notna() & tmp["Your Rating"].notna()]
            if not tmp.empty:
                current_year = int(pd.Timestamp.now().year)
                recent_limit = current_year - 10  # últimos 10 años
                tmp_recent = tmp[tmp["Year"] >= recent_limit]

                if not tmp_recent.empty:
                    g_exp = tmp_recent.explode("GenreList")
                    g_exp = g_exp[
                        g_exp["GenreList"].notna() &
                        (g_exp["GenreList"] != "")
                    ]

                    if not g_exp.empty:
                        # top géneros por nº de pelis en estos años
                        top_gen_counts = (
                            g_exp["GenreList"]
                            .value_counts()
                            .head(5)
                            .index.tolist()
                        )
                        g_top = g_exp[g_exp["GenreList"].isin(top_gen_counts)]

                        genre_year = (
                            g_top
                            .groupby(["Year", "GenreList"])["Your Rating"]
                            .mean()
                            .reset_index()
                        )
                        genre_year["YearInt"] = genre_year["Year"].astype(int)

                        gy_chart = (
                            alt.Chart(genre_year)
                            .mark_line(point=True)
                            .encode(
                                x=alt.X("YearInt:O", title="Año"),
                                y=alt.Y("Your Rating:Q", title="Tu nota media"),
                                color=alt.Color("GenreList:N", title="Género"),
                                tooltip=["YearInt", "GenreList", "Your Rating"]
                            )
                            .properties(height=350)
                        )
                        st.altair_chart(gy_chart, use_container_width=True)
                        st.caption(
                            "Mostrados los 5 géneros más frecuentes en los últimos ~10 años y cómo los puntúas."
                        )
                    else:
                        st.write("No hay géneros suficientes en los últimos años para este análisis.")
                else:
                    st.write("No tienes películas recientes (últimos ~10 años) con año y nota.")
            else:
                st.write("No hay datos suficientes (año + tu nota) para este análisis.")
        else:
            st.write("Faltan columnas 'GenreList' o 'Your Rating' para este análisis.")

        # ----------------------------------------------------
        # 8) Duración media por año y por género (si existe Runtime)
        # ----------------------------------------------------
        st.markdown("### ⏱️ Duración media de las películas")

        if "Runtime (mins)" in filtered.columns and filtered["Runtime (mins)"].notna().any():
            col_dur1, col_dur2 = st.columns(2)

            with col_dur1:
                st.markdown("**Duración media por año**")
                tmp = filtered[
                    filtered["Year"].notna() &
                    filtered["Runtime (mins)"].notna()
                ].copy()
                if not tmp.empty:
                    dur_year = (
                        tmp.groupby("Year")["Runtime (mins)"]
                        .mean()
                        .reset_index()
                        .sort_values("Year")
                    )
                    dur_year["YearInt"] = dur_year["Year"].astype(int)

                    dur_chart = (
                        alt.Chart(dur_year)
                        .mark_line(point=True)
                        .encode(
                            x=alt.X("YearInt:O", title="Año"),
                            y=alt.Y("Runtime (mins):Q", title="Minutos de duración"),
                            tooltip=["YearInt", "Runtime (mins)"]
                        )
                        .properties(height=300)
                    )
                    st.altair_chart(dur_chart, use_container_width=True)
                else:
                    st.write("No hay datos suficientes de duración por año.")

            with col_dur2:
                st.markdown("**Duración media por género (top 10)**")
                tmp = filtered[
                    filtered["Runtime (mins)"].notna()
                ].copy()
                if "GenreList" in tmp.columns:
                    g_exp = tmp.explode("GenreList")
                    g_exp = g_exp[
                        g_exp["GenreList"].notna() &
                        (g_exp["GenreList"] != "")
                    ]
                    if not g_exp.empty:
                        dur_genre = (
                            g_exp
                            .groupby("GenreList")["Runtime (mins)"]
                            .mean()
                            .reset_index()
                        )
                        dur_genre = dur_genre.sort_values("Runtime (mins)", ascending=False).head(10)
                        dur_genre = dur_genre.set_index("GenreList")
                        st.bar_chart(dur_genre)
                    else:
                        st.write("No hay géneros suficientes con duración.")
                else:
                    st.write("No se encontró información de géneros para este análisis.")
        else:
            st.write("El CSV no tiene 'Runtime (mins)' o no hay datos suficientes de duración.")
