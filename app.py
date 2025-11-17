# ============================================================
#             TAB 4: PREMIOS ÓSCAR (Oscar_Data_1927_today.xlsx)
# ============================================================

@st.cache_data
def load_oscar_data_from_excel(path_xlsx="Oscar_Data_1927_today.xlsx"):
    """
    Carga robusta desde Oscar_Data_1927_today.xlsx.

    Intenta detectar de forma flexible:
      - Año de ceremonia -> CeremonyInt
      - Año de la película -> YearInt
      - Categoría canónica -> CanonCat
      - Película -> Film
      - Nominee / Entidad -> Nominee
      - Winner -> IsWinner
      - IDs de entidad -> NomineeIdsList (opcional)

    Además añade NormFilm para cruce con tu catálogo.
    """
    try:
        try:
            raw = pd.read_excel(path_xlsx, engine="openpyxl")
        except Exception:
            raw = pd.read_excel(path_xlsx)
    except FileNotFoundError:
        return pd.DataFrame()

    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    idx = df.index

    def norm_name(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower())

    # Map normalizado -> nombre real
    norm_map = {norm_name(c): c for c in df.columns}

    def find_col(candidates):
        for cand in candidates:
            key = norm_name(cand)
            if key in norm_map:
                return norm_map[key]
        return None

    # Columnas candidatas
    col_cer = find_col(["ceremony", "ceremonynumber", "ceremonyyear",
                        "yearceremony", "awardyear", "ceremony_no"])
    col_year_film = find_col(["filmyear", "yearfilm", "year_film",
                              "filmyearreleased", "yearoffilm", "releaseyear"])
    col_year_generic = find_col(["year"])
    col_cat = find_col(["canonicalcategory", "canoncat", "category", "awardcategory"])
    col_film = find_col(["film", "filmtitle", "movietitle", "title", "film_name"])
    col_nominee = find_col(["nominee", "name", "entity", "person", "recipient"])
    col_winner = find_col(["winner", "iswinner", "win", "won"])
    col_ids = find_col(["nomineeids", "nomineeid", "entityid", "personid"])

    # Año de la película
    if col_year_film is not None:
        yr = pd.to_numeric(df[col_year_film], errors="coerce")
    elif col_year_generic is not None:
        yr = pd.to_numeric(df[col_year_generic], errors="coerce")
    else:
        yr = pd.Series([-1] * len(df), index=idx, dtype="float64")
    df["YearInt"] = yr.fillna(-1).astype(int)

    # Año / número de ceremonia
    if col_cer is not None:
        cer = pd.to_numeric(df[col_cer], errors="coerce")
        df["CeremonyInt"] = cer.fillna(df["YearInt"]).astype(int)
    else:
        # Fallback: usa YearInt como proxy de ceremonia
        df["CeremonyInt"] = df["YearInt"]

    # Categoría canónica
    if col_cat is not None:
        df["CanonCat"] = df[col_cat].astype(str)
    else:
        df["CanonCat"] = ""

    # Película
    if col_film is not None:
        df["Film"] = df[col_film].astype(str)
    else:
        df["Film"] = ""

    # Nominee / Entidad
    if col_nominee is not None:
        df["Nominee"] = df[col_nominee].astype(str)
    else:
        df["Nominee"] = ""

    # Winner -> IsWinner
    if col_winner is not None:
        win_series = df[col_winner].astype(str).str.lower()
        df["IsWinner"] = win_series.isin(
            ["1", "true", "t", "yes", "y", "winner", "won", "ganador", "ganadora"]
        )
    else:
        df["IsWinner"] = False

    # IDs de entidad (opcional)
    if col_ids is not None:
        base_ids = df[col_ids].fillna("").astype(str)
    else:
        base_ids = pd.Series([""] * len(df), index=idx)
    df["NomineeIdsList"] = base_ids.apply(
        lambda s: [x.strip() for x in re.split(r"[;,]", s) if x.strip()]
    )

    # Normalización de título de película
    df["NormFilm"] = df["Film"].apply(normalize_title)

    return df


with tab_awards:
    st.markdown("## 🏆 Premios de la Academia (Oscar_Data_1927_today.xlsx)")

    osc = load_oscar_data_from_excel("Oscar_Data_1927_today.xlsx")
    if osc.empty:
        st.info(
            "No pude cargar 'Oscar_Data_1927_today.xlsx'. "
            "Asegúrate de incluirlo en la raíz del proyecto."
        )
        st.stop()

    # Enlaza con tu catálogo (usando NormFilm + YearInt)
    osc_x = attach_catalog_to_full(osc, df)

    # ------------- Filtros -------------
    st.markdown("### 🧊 Filtros en premios")

    colf1, colf2, colf3 = st.columns([1.6, 1.4, 2.3])

    # Años de ceremonia disponibles
    valid_years = osc_x.loc[osc_x["CeremonyInt"] >= 0, "CeremonyInt"].unique()
    if valid_years.size == 0:
        st.info("No hay años de ceremonia válidos en los datos de Óscar.")
        st.stop()

    all_years_sorted = sorted(int(y) for y in valid_years)

    # Estado: año seleccionado
    if "osc_year_sel" not in st.session_state:
        st.session_state["osc_year_sel"] = all_years_sorted[-1]
    year_selected = st.session_state["osc_year_sel"]

    with colf1:
        st.markdown("**Año de ceremonia**")
        # Tira horizontal (varias filas, pero con años en horizontal)
        n_cols = 12  # años por fila
        rows = (len(all_years_sorted) + n_cols - 1) // n_cols
        for r in range(rows):
            cols_row = st.columns(n_cols)
            for c in range(n_cols):
                idx_year = r * n_cols + c
                if idx_year >= len(all_years_sorted):
                    continue
                y = all_years_sorted[idx_year]
                label = str(y)
                is_active = (y == year_selected)
                button_label = f"{label}" + (" ⭐" if is_active else "")
                if cols_row[c].button(
                    button_label,
                    key=f"osc_year_btn_{y}"
                ):
                    st.session_state["osc_year_sel"] = y
                    year_selected = y

    all_cats = sorted(osc_x["CanonCat"].dropna().unique().tolist())
    with colf2:
        cats_sel = st.multiselect(
            "Categorías (canon, opcional)",
            options=all_cats,
            default=[],
            key="osc_cats_sel",
        )

    with colf3:
        q_aw = st.text_input(
            "Buscar (categoría / entidad / película / IDs)",
            placeholder="Ej: 'Best Picture' o 'Spielberg' o 'Warner Bros.'",
            key="osc_search",
        )

    # ------------- Aplicar filtros base para el año seleccionado -------------
    ff = osc_x[osc_x["CeremonyInt"] == year_selected].copy()

    if cats_sel:
        ff = ff[ff["CanonCat"].isin(cats_sel)]

    if q_aw:
        q = q_aw.strip().lower()
        mask = (
            ff["CanonCat"].astype(str).str.lower().str.contains(q, na=False) |
            ff["Nominee"].astype(str).str.lower().str.contains(q, na=False) |
            ff["Film"].astype(str).str.lower().str.contains(q, na=False) |
            ff["NomineeIdsList"].astype(str).str.lower().str.contains(q, na=False)
        )
        ff = ff[mask]

    # ------------- Métricas -------------
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Ceremonia seleccionada", year_selected)
    with c2:
        st.metric("Filas (nominaciones + ganadores)", len(ff))
    with c3:
        st.metric("Categorías distintas", ff["CanonCat"].nunique())
    with c4:
        st.metric("Ganadores (filtrados)", int(ff["IsWinner"].sum()))

    st.caption(
        "Se usa **Oscar_Data_1927_today.xlsx**. "
        "El resaltado en **verde** marca a los ganadores (`IsWinner`). "
        "Los rankings de entidades se basan en el campo **Nominee**."
    )

    # ========================================================
    #   GALERÍA VISUAL POR CATEGORÍA (GANADORES) – CON PÓSTERS
    # ========================================================

    st.markdown("### 🎬 Galería visual por categoría (ganadores)")

    winners = ff[ff["IsWinner"]].copy()
    if winners.empty:
        st.info("No hay ganadores para ese año con los filtros actuales.")
    else:
        winners = winners.sort_values(["CanonCat", "Film", "Nominee"])

        cards_html = ['<div class="movie-gallery-grid">']

        for _, row in winners.iterrows():
            categoria = row.get("CanonCat", "")
            film = row.get("Film", "Sin título")
            film_year = row.get("YearInt", "")
            nominee = row.get("Nominee", "")
            my_rating = row.get("MyRating")
            my_imdb = row.get("MyIMDb")
            in_catalog = row.get("InMyCatalog", False)
            url_catalog = row.get("CatalogURL", "")

            base_rating = my_rating if pd.notna(my_rating) else my_imdb
            border_color, glow_color = get_rating_colors(base_rating)

            # TMDb
            tmdb_info = get_tmdb_basic_info(film, film_year)
            poster_url = tmdb_info.get("poster_url") if tmdb_info else None
            tmdb_rating = tmdb_info.get("vote_average") if tmdb_info else None

            if isinstance(poster_url, str) and poster_url:
                poster_html = f"""
<div class="movie-poster-frame">
  <img src="{poster_url}" alt="{film}" class="movie-poster-img">
</div>
"""
            else:
                poster_html = """
<div class="movie-poster-frame">
  <div class="movie-poster-placeholder">
    <div class="film-reel-icon">🏆</div>
    <div class="film-reel-text">Sin póster</div>
  </div>
</div>
"""

            year_str = f" ({film_year})" if isinstance(film_year, (int, float)) and film_year > 0 else ""
            my_rating_str = (
                f"⭐ Mi nota: {fmt_rating(my_rating)}"
                if pd.notna(my_rating) else "⭐ Mi nota: —"
            )
            imdb_str = (
                f"IMDb (mía): {fmt_rating(my_imdb)}"
                if pd.notna(my_imdb) else "IMDb (mía): —"
            )
            tmdb_str = f"TMDb: {fmt_rating(tmdb_rating)}" if tmdb_rating is not None else "TMDb: N/D"
            in_cat_str = "✅ En mi catálogo" if in_catalog else "— No está en mi catálogo"

            imdb_link_html = (
                f'<a href="{url_catalog}" target="_blank">Ver en IMDb (mi enlace)</a>'
                if isinstance(url_catalog, str) and url_catalog.startswith("http")
                else ""
            )

            card_html = f"""
<div class="movie-card movie-card-grid" style="
    border-color: {border_color};
    box-shadow:
        0 0 0 1px rgba(15,23,42,0.9),
        0 0 22px {glow_color};
">
  {poster_html}
  <div class="movie-title">{categoria}</div>
  <div class="movie-sub">
    <b>Película:</b> {film}{year_str}<br>
    <b>Ganador:</b> {nominee}<br>
    {my_rating_str}<br>
    {imdb_str}<br>
    {tmdb_str}<br>
    {in_cat_str}<br>
    {imdb_link_html}
  </div>
</div>
"""
            cards_html.append(card_html)

        cards_html.append("</div>")
        gallery_html = "\n".join(cards_html)
        st.markdown(gallery_html, unsafe_allow_html=True)

    # ========================================================
    #   TABLA: VISTA POR AÑO (CATEGORÍAS, NOMINADOS, GANADORES)
    # ========================================================

    st.markdown("### 📅 Vista por año (categorías, nominados y ganadores)")

    if ff.empty:
        st.info("No hay datos para ese año con los filtros actuales.")
        table_year = pd.DataFrame()
    else:
        table_year = ff.copy().sort_values(
            ["CanonCat", "IsWinner", "Film", "Nominee"],
            ascending=[True, False, True, True]
        )

        pretty = table_year[[
            "CanonCat", "Nominee", "Film", "YearInt", "IsWinner",
            "InMyCatalog", "MyRating", "MyIMDb", "CatalogURL"
        ]].copy()

        pretty = pretty.rename(columns={
            "CanonCat": "Categoría",
            "Nominee": "Entidad / Nominee",
            "Film": "Película",
            "YearInt": "Año de película",
            "IsWinner": "Ganador",
            "InMyCatalog": "En mi catálogo",
            "MyRating": "Mi nota",
            "MyIMDb": "IMDb",
            "CatalogURL": "IMDb (mía)",
        })

        pretty["En mi catálogo"] = pretty["En mi catálogo"].map({True: "✅", False: "—"})
        if "Mi nota" in pretty.columns:
            pretty["Mi nota"] = pretty["Mi nota"].apply(
                lambda v: f"{float(v):.1f}" if pd.notna(v) else ""
            )
        if "IMDb" in pretty.columns:
            pretty["IMDb"] = pretty["IMDb"].apply(
                lambda v: f"{float(v):.1f}" if pd.notna(v) else ""
            )
        pretty["Año de película"] = pretty["Año de película"].apply(
            lambda v: "" if v == -1 or pd.isna(v) else str(int(v))
        )

        def highlight_winner(row):
            if bool(row.get("Ganador", False)):
                style = (
                    "background-color: rgba(34,197,94,0.18); "
                    "color:#ecfdf5; font-weight:700; border-left:3px solid #22c55e"
                )
            else:
                style = ""
            return [style] * len(row)

        styled = (
            pretty.style
            .set_table_styles([{"selector": "th", "props": [("text-align", "left")]}])
            .set_properties(**{"text-align": "left"})
            .apply(highlight_winner, axis=1)
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

        csv_dl = table_year.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar nominados/ganadores del año (CSV)",
            data=csv_dl,
            file_name=f"oscars_{year_selected}_desde_excel.csv",
            mime="text/csv"
        )

    # ========================================================
    #   RANKINGS EN EL AÑO SELECCIONADO
    # ========================================================

    st.markdown("### 🥇 Rankings en el año seleccionado (Nominaciones al Óscar)")

    nom_ff = ff.copy()

    colr1, colr2 = st.columns(2)

    with colr1:
        st.markdown("**Películas con más nominaciones**")
        top_films = (
            nom_ff.groupby(["Film", "YearInt"])
            .size()
            .reset_index(name="Nominaciones")
            .sort_values(["Nominaciones", "Film"], ascending=[False, True])
            .head(20)
        )
        if not top_films.empty:
            tf_disp = top_films.rename(columns={"Film": "Película", "YearInt": "Año"})
            tf_disp["Año"] = tf_disp["Año"].apply(
                lambda v: "" if v == -1 or pd.isna(v) else str(int(v))
            )
            st.dataframe(tf_disp, use_container_width=True, hide_index=True)
        else:
            st.write("Sin datos de películas para este año con los filtros actuales.")

    with colr2:
        st.markdown("**Entidades (Nominee) con más nominaciones**")
        ent = nom_ff.copy()
        ent = ent[ent["Nominee"].astype(str).str.strip() != ""]
        top_entities = (
            ent.groupby("Nominee")
            .size()
            .reset_index(name="Nominaciones")
            .sort_values(["Nominaciones", "Nominee"], ascending=[False, True])
            .head(20)
        )
        if not top_entities.empty:
            te_disp = top_entities.rename(columns={"Nominee": "Entidad"})
            st.dataframe(te_disp, use_container_width=True, hide_index=True)
        else:
            st.write("Sin datos de entidades para este año con los filtros actuales.")
