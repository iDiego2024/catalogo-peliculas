# ============================================================
#             ANÁLISIS DE GUSTOS PERSONALES
# ============================================================

st.markdown("---")
st.markdown("## 🧠 Análisis de tus gustos personales")

with st.expander("Ver análisis de gustos personales", expanded=False):
    if filtered.empty:
        st.info("No hay datos bajo los filtros actuales para analizar tus gustos.")
    else:
        col_g1, col_g2 = st.columns(2)

        # 1) Media y dispersión por género
        with col_g1:
            st.markdown("### 🎭 Géneros según tu gusto")

            if "GenreList" in filtered.columns and "Your Rating" in filtered.columns:
                tmp = filtered.copy()
                tmp = tmp[tmp["Your Rating"].notna()]
                genres_exploded = tmp.explode("GenreList")
                genres_exploded = genres_exploded[
                    genres_exploded["GenreList"].notna() &
                    (genres_exploded["GenreList"] != "")
                ]
                if not genres_exploded.empty:
                    genre_stats = (
                        genres_exploded
                        .groupby("GenreList")["Your Rating"]
                        .agg(["count", "mean", "std"])
                        .reset_index()
                    )
                    genre_stats = genre_stats[genre_stats["count"] >= 3]
                    if not genre_stats.empty:
                        genre_stats = genre_stats.sort_values("mean", ascending=False)
                        genre_stats["mean"] = genre_stats["mean"].round(2)
                        genre_stats["std"] = genre_stats["std"].fillna(0).round(2)

                        st.write(
                            "Géneros ordenados por tu nota media. "
                            "La desviación estándar (σ) indica cuánto varían tus notas dentro del género."
                        )
                        st.dataframe(
                            genre_stats.rename(
                                columns={
                                    "GenreList": "Género",
                                    "count": "Nº pelis",
                                    "mean": "Tu nota media",
                                    "std": "Desviación (σ)"
                                }
                            ),
                            hide_index=True,
                            use_container_width=True
                        )
                    else:
                        st.write("No hay géneros con suficientes películas para mostrar estadísticas.")
                else:
                    st.write("No hay información suficiente de géneros para analizar tus gustos.")
            else:
                st.write("Faltan columnas 'GenreList' o 'Your Rating' para este análisis.")

        # 2) Diferencia entre tu nota e IMDb (estático, no por año)
        with col_g2:
            st.markdown("### ⚖️ ¿Eres más exigente que IMDb? (global)")

            if "Your Rating" in filtered.columns and "IMDb Rating" in filtered.columns:
                diff_df = filtered[
                    filtered["Your Rating"].notna() &
                    filtered["IMDb Rating"].notna()
                ].copy()
                if not diff_df.empty:
                    diff_df["Diff"] = diff_df["Your Rating"] - diff_df["IMDb Rating"]

                    media_diff = diff_df["Diff"].mean()
                    st.metric(
                        "Diferencia media (Tu nota - IMDb)",
                        f"{media_diff:.2f}"
                    )

                    st.write(
                        "Valores positivos ⇒ sueles puntuar **más alto** que IMDb. "
                        "Valores negativos ⇒ sueles ser **más duro** que IMDb."
                    )

                    hist = (
                        diff_df["Diff"]
                        .round(1)
                        .value_counts()
                        .sort_index()
                        .reset_index()
                    )
                    hist.columns = ["Diff", "Count"]
                    hist["Diff"] = hist["Diff"].astype(str)
                    hist = hist.set_index("Diff")
                    st.bar_chart(hist)
                else:
                    st.write("No hay suficientes películas con ambas notas (tuya e IMDb) para comparar.")
            else:
                st.write("Faltan columnas 'Your Rating' o 'IMDb Rating' para comparar con IMDb.")

        # 3) Evolución de tu exigencia en el tiempo
        st.markdown("### ⏳ Evolución de tu exigencia con los años")

        if (
            "Year" in filtered.columns and
            "Your Rating" in filtered.columns and
            "IMDb Rating" in filtered.columns
        ):
            tmp = filtered.copy()
            tmp = tmp[
                tmp["Year"].notna() &
                tmp["Your Rating"].notna() &
                tmp["IMDb Rating"].notna()
            ]
            if not tmp.empty:
                by_year_gusto = (
                    tmp.groupby("Year")[["Your Rating", "IMDb Rating"]]
                    .mean()
                    .reset_index()
                    .sort_values("Year")
                )
                by_year_gusto["Diff"] = by_year_gusto["Your Rating"] - by_year_gusto["IMDb Rating"]

                long_df = by_year_gusto.melt(
                    id_vars="Year",
                    value_vars=["Your Rating", "IMDb Rating"],
                    var_name="Fuente",
                    value_name="Rating"
                )
                long_df["Year"] = long_df["Year"].astype(int)

                chart = (
                    alt.Chart(long_df)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("Year:O", title="Año"),
                        y=alt.Y("Rating:Q", title="Nota media"),
                        color=alt.Color("Fuente:N", title="Fuente"),
                        tooltip=["Year", "Fuente", "Rating"]
                    )
                    .properties(height=350)
                )
                st.altair_chart(chart, use_container_width=True)

                st.write(
                    "Si tu curva (Your Rating) va **bajando** con los años mientras IMDb se mantiene, "
                    "es que te estás volviendo más exigente. Si sube, te estás ablandando con la edad cinéfila 😄."
                )

                tmp["Decade"] = (tmp["Year"] // 10 * 10).astype(int)
                decade_diff = (
                    tmp.groupby("Decade")
                    .apply(lambda g: (g["Your Rating"] - g["IMDb Rating"]).mean())
                    .reset_index(name="Diff media")
                    .sort_values("Decade")
                )
                if not decade_diff.empty:
                    decade_diff["Decade"] = decade_diff["Decade"].astype(int)
                    st.write("**Diferencia media por década (Tu nota - IMDb):**")
                    st.dataframe(
                        decade_diff.rename(columns={"Decade": "Década"}),
                        hide_index=True,
                        use_container_width=True
                    )
            else:
                st.write("No hay suficientes datos (año + tus notas + IMDb) para analizar tu evolución.")
        else:
            st.write("Faltan columnas 'Year', 'Your Rating' o 'IMDb Rating' para analizar tu evolución en el tiempo.")

        # 4) Ranking de directores más vistos
        st.markdown("### 🎬 Directores que más ves")

        if "Directors" in filtered.columns:
            tmp_dir = filtered.copy()
            tmp_dir = tmp_dir[tmp_dir["Directors"].notna() & (tmp_dir["Directors"].astype(str).str.strip() != "")]
            if not tmp_dir.empty:
                # Algunos CSV tienen varios directores separados por coma
                dir_exp = tmp_dir.copy()
                dir_exp["Directors"] = dir_exp["Directors"].astype(str)
                dir_exp = dir_exp.assign(
                    DirectorList=dir_exp["Directors"].apply(lambda x: [d.strip() for d in x.split(",")])
                )
                dir_exp = dir_exp.explode("DirectorList")
                dir_exp = dir_exp[dir_exp["DirectorList"] != ""]

                if not dir_exp.empty:
                    dir_stats = (
                        dir_exp.groupby("DirectorList")["Your Rating"]
                        .agg(["count", "mean"])
                        .reset_index()
                    )
                    dir_stats = dir_stats[dir_stats["count"] >= 3]
                    if not dir_stats.empty:
                        dir_stats = dir_stats.sort_values(
                            ["count", "mean"], ascending=[False, False]
                        ).head(20)
                        dir_stats["mean"] = dir_stats["mean"].round(2)
                        st.dataframe(
                            dir_stats.rename(
                                columns={
                                    "DirectorList": "Director",
                                    "count": "Nº pelis",
                                    "mean": "Tu nota media"
                                }
                            ),
                            hide_index=True,
                            use_container_width=True
                        )
                    else:
                        st.write("No hay directores con al menos 3 películas vistas.")
                else:
                    st.write("No se pudo descomponer la lista de directores.")
            else:
                st.write("No hay información de directores en los datos filtrados.")
        else:
            st.write("El CSV no tiene columna 'Directors'.")

        # 5) Ranking de actores más vistos (si existe columna)
        st.markdown("### 🎭 Actores/actrices que más ves")

        if "Actors" in filtered.columns:
            tmp_act = filtered.copy()
            tmp_act = tmp_act[tmp_act["Actors"].notna() & (tmp_act["Actors"].astype(str).str.strip() != "")]
            if not tmp_act.empty:
                act_exp = tmp_act.copy()
                act_exp["Actors"] = act_exp["Actors"].astype(str)
                act_exp = act_exp.assign(
                    ActorList=act_exp["Actors"].apply(lambda x: [a.strip() for a in x.split(",")])
                )
                act_exp = act_exp.explode("ActorList")
                act_exp = act_exp[act_exp["ActorList"] != ""]

                if not act_exp.empty:
                    act_stats = (
                        act_exp.groupby("ActorList")["Your Rating"]
                        .agg(["count", "mean"])
                        .reset_index()
                    )
                    act_stats = act_stats[act_stats["count"] >= 3]
                    if not act_stats.empty:
                        act_stats = act_stats.sort_values(
                            ["count", "mean"], ascending=[False, False]
                        ).head(20)
                        act_stats["mean"] = act_stats["mean"].round(2)
                        st.dataframe(
                            act_stats.rename(
                                columns={
                                    "ActorList": "Actor/Actriz",
                                    "count": "Nº pelis",
                                    "mean": "Tu nota media"
                                }
                            ),
                            hide_index=True,
                            use_container_width=True
                        )
                    else:
                        st.write("No hay actores/actrices con al menos 3 películas vistas.")
                else:
                    st.write("No se pudo descomponer la lista de actores.")
            else:
                st.write("No hay información de actores en los datos filtrados.")
        else:
            st.write("El CSV no tiene columna 'Actors'.")
