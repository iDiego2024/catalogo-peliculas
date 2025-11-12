st.markdown("### 🥇 Rankings en el rango seleccionado")
colr1, colr2 = st.columns(2)

with colr1:
    top_films = (
        ff.groupby(["film", "YearFilmInt"])
        .size()
        .reset_index(name="Wins")
        .sort_values(["Wins", "film"], ascending=[False, True])
        .head(15)
    )

    if not top_films.empty:
        tf_disp = top_films.rename(columns={
            "film": "Película",
            "YearFilmInt": "Año",
            "Wins": "Óscar ganados"
        }).copy()

        # ✨ Sanitizar tipos (todo string donde corresponde)
        tf_disp["Película"] = tf_disp["Película"].astype(str).fillna("")
        tf_disp["Año"] = tf_disp["Año"].apply(fmt_year)
        tf_disp["Óscar ganados"] = pd.to_numeric(tf_disp["Óscar ganados"], errors="coerce").fillna(0).astype(int)

        try:
            st.dataframe(tf_disp, use_container_width=True, hide_index=True)
        except Exception:
            st.warning("Mostrando tabla simple por un problema de renderizado.")
            st.table(tf_disp)
    else:
        st.write("Sin datos de películas en este rango.")

with colr2:
    top_people = (
        ff.groupby("name")
        .size()
        .reset_index(name="Wins")
        .sort_values(["Wins", "name"], ascending=[False, True])
        .head(15)
    )

    if not top_people.empty:
        tp_disp = top_people.rename(columns={
            "name": "Ganador/a",
            "Wins": "Óscar ganados"
        }).copy()

        # ✨ Sanitizar tipos
        tp_disp["Ganador/a"] = tp_disp["Ganador/a"].astype(str).fillna("")
        tp_disp["Óscar ganados"] = pd.to_numeric(tp_disp["Óscar ganados"], errors="coerce").fillna(0).astype(int)

        try:
            st.dataframe(tp_disp, use_container_width=True, hide_index=True)
        except Exception:
            st.warning("Mostrando tabla simple por un problema de renderizado.")
            st.table(tp_disp)
    else:
        st.write("Sin datos de personas en este rango.")
