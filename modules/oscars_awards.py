import streamlit as st
import pandas as pd
import re
from modules.utils import normalize_title

REQUIRED_COLS = [
    "year_film", "year_ceremony", "ceremony", "category",
    "canon_category", "name", "film"
]

@st.cache_data
def load_oscar_winners(path_csv="the_oscar_award.csv"):
    """Carga ganadores del CSV y normaliza columnas.
    Tolera CSVs con nombres distintos o faltantes y crea columnas de respaldo.
    """
    try:
        raw = pd.read_csv(path_csv)
    except Exception as e:
        st.warning(f"No pude leer {path_csv}: {e}")
        return pd.DataFrame(columns=REQUIRED_COLS)

    dfw = raw.copy()

    # Asegurar columnas requeridas
    for c in REQUIRED_COLS:
        if c not in dfw.columns:
            dfw[c] = ""

    # Normalizaciones numéricas
    for c in ["year_film", "year_ceremony", "ceremony"]:
        dfw[c] = pd.to_numeric(dfw[c], errors="coerce")

    # Canon category (fallback a category si falta/está vacía)
    dfw["canon_category"] = dfw["canon_category"].where(dfw["canon_category"].notna() & (dfw["canon_category"] != ""), dfw["category"])

    # Enriquecidos para joins y filtros
    dfw["YearFilmInt"] = dfw["year_film"].fillna(-1).astype(int)
    dfw["YearCeremonyInt"] = dfw["year_ceremony"].fillna(-1).astype(int)
    dfw["NormFilm"] = dfw["film"].apply(normalize_title)
    dfw["NormName"] = dfw["name"].apply(lambda s: re.sub(r"\s+", " ", str(s)).strip().lower())
    dfw["CanonCat"] = dfw["canon_category"].astype(str)

    return dfw

def attach_my_catalog_cols(winners_df, my_catalog_df):
    winners_df = winners_df.copy()

    # columnas "mi catálogo"
    winners_df["InMyCatalog"] = False
    winners_df["MyRating"] = None
    winners_df["MyIMDb"] = None
    winners_df["CatalogURL"] = None

    if winners_df.empty or my_catalog_df is None or my_catalog_df.empty:
        return winners_df

    cat = my_catalog_df.copy()
    if "NormTitle" not in cat.columns:
        cat["NormTitle"] = cat.get("Title", "").apply(normalize_title)
    if "YearInt" not in cat.columns:
        cat["YearInt"] = cat.get("Year", pd.Series([None]*len(cat))).fillna(-1).astype(float).astype(int)

    winners_df["JoinTitle"] = winners_df["NormFilm"]
    winners_df["JoinYear"] = winners_df["YearFilmInt"]

    merged = winners_df.merge(
        cat[["NormTitle", "YearInt", "Your Rating", "IMDb Rating", "URL"]],
        left_on=["JoinTitle", "JoinYear"],
        right_on=["NormTitle", "YearInt"],
        how="left",
        suffixes=("", "_cat")
    )

    merged["InMyCatalog"] = merged["URL"].notna()
    merged["MyRating"] = merged["Your Rating"]
    merged["MyIMDb"] = merged["IMDb Rating"]
    merged["CatalogURL"] = merged["URL"]

    merged = merged.drop(columns=["NormTitle", "YearInt", "Your Rating", "IMDb Rating", "URL"], errors="ignore")
    return merged

def render_awards_tab(df):
    st.markdown("## 🏆 Premios de la Academia (ganadores)")

    winners = load_oscar_winners("the_oscar_award.csv")
    if winners.empty:
        st.info("No pude cargar ganadores (the_oscar_award.csv) o no trae columnas reconocibles.")
        return

    winners_x = attach_my_catalog_cols(winners, df)

    # ------- Filtros robustos -------
    st.markdown("### 🎛️ Filtros en premios")

    # Ceremonias (si no hay números válidos, definir rango seguro)
    valid_cer = winners_x["YearCeremonyInt"][winners_x["YearCeremonyInt"] != -1]
    if valid_cer.empty:
        min_cer, max_cer = 1927, 2025
    else:
        min_cer, max_cer = int(valid_cer.min()), int(valid_cer.max())

    colf1, colf2, colf3 = st.columns([1, 1, 2])
    with colf1:
        year_range_osc = st.slider("Año de ceremonia", min_cer, max_cer, (min_cer, max_cer))
    with colf2:
        cats_all = sorted(winners_x["CanonCat"].dropna().astype(str).unique().tolist())
        cats_sel = st.multiselect("Categorías (canon)", options=cats_all, default=[])
    with colf3:
        q_aw = st.text_input("Buscar en nombre/persona, película o categoría", placeholder="Ej: 'ACTRESS' o 'Spielberg' o 'Parasite'")

    ff = winners_x[
        (winners_x["YearCeremonyInt"] >= year_range_osc[0]) &
        (winners_x["YearCeremonyInt"] <= year_range_osc[1])
    ].copy()
    if cats_sel:
        ff = ff[ff["CanonCat"].isin(cats_sel)]
    if q_aw:
        q = q_aw.strip().lower()
        mask = (
            ff["CanonCat"].astype(str).str.lower().str.contains(q, na=False) |
            ff["name"].astype(str).str.lower().str.contains(q, na=False) |
            ff["film"].astype(str).str.lower().str.contains(q, na=False)
        )
        ff = ff[mask]

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Ceremonias (rango)", f"{year_range_osc[0]}–{year_range_osc[1]}")
    with c2: st.metric("Ganadores (filtrados)", len(ff))
    with c3: st.metric("Categorías distintas", ff["CanonCat"].nunique() if not ff.empty else 0)
    with c4: st.metric("Ganadores en mi catálogo", int(ff["InMyCatalog"].sum()) if not ff.empty else 0)

    st.caption("Los ganadores provienen de `the_oscar_award.csv`.")

    # ------- Vista por año -------
    st.markdown("### 📅 Vista por año (categorías y ganadores)")
    if ff.empty or ff["YearCeremonyInt"].dropna().empty:
        st.info("No hay ganadores para mostrar con los filtros actuales.")
        return

    years_sorted = sorted([int(y) for y in ff["YearCeremonyInt"].dropna().unique()])
    y_idx = max(0, len(years_sorted) - 1)
    y_pick = st.selectbox("Elige año de ceremonia", options=years_sorted, index=y_idx, key="aw_select_year")

    table_year = ff[ff["YearCeremonyInt"] == y_pick].copy()
    if table_year.empty:
        st.info("No hay ganadores para ese año con los filtros actuales.")
    else:
        table_year = table_year.sort_values(["CanonCat", "film", "name"])
        pretty = table_year[[
            "CanonCat", "category", "name", "film",
            "YearFilmInt", "InMyCatalog", "MyRating", "MyIMDb", "CatalogURL"
        ]].copy()

        pretty = pretty.rename(columns={
            "CanonCat": "Categoría",
            "category": "Categoría (cruda)",
            "name": "Ganador/a",
            "film": "Película",
            "YearFilmInt": "Año de película",
            "InMyCatalog": "En mi catálogo",
            "MyRating": "Mi nota",
            "MyIMDb": "IMDb",
            "CatalogURL": "IMDb (mía)"
        })

        pretty["En mi catálogo"] = pretty["En mi catálogo"].map({True: "✅", False: "—"})
        if "Mi nota" in pretty.columns:
            pretty["Mi nota"] = pretty["Mi nota"].apply(lambda v: f"{float(v):.1f}" if pd.notna(v) else "")
        if "IMDb" in pretty.columns:
            pretty["IMDb"] = pretty["IMDb"].apply(lambda v: f"{float(v):.1f}" if pd.notna(v) else "")

        st.dataframe(pretty, use_container_width=True, hide_index=True)

    # ------- Rankings -------
    st.markdown("### 🥇 Rankings en el rango seleccionado")
    colr1, colr2 = st.columns(2)
    with colr1:
        if not ff.empty:
            top_films = (
                ff.groupby(["film", "YearFilmInt"])
                  .size().reset_index(name="Wins")
                  .sort_values(["Wins", "film"], ascending=[False, True]).head(15)
            )
            if not top_films.empty:
                tf_disp = top_films.rename(columns={
                    "film": "Película", "YearFilmInt": "Año", "Wins": "Óscar ganados"
                })
                st.dataframe(tf_disp, use_container_width=True, hide_index=True)
            else:
                st.write("Sin datos de películas en este rango.")
        else:
            st.write("Sin datos de películas en este rango.")
    with colr2:
        if not ff.empty:
            top_people = (
                ff.groupby("name")
                  .size().reset_index(name="Wins")
                  .sort_values(["Wins", "name"], ascending=[False, True]).head(15)
            )
            if not top_people.empty:
                tp_disp = top_people.rename(columns={"name": "Ganador/a", "Wins": "Óscar ganados"})
                st.dataframe(tp_disp, use_container_width=True, hide_index=True)
            else:
                st.write("Sin datos de personas en este rango.")
        else:
            st.write("Sin datos de personas en este rango.")
