import streamlit as st
import pandas as pd
import re
from modules.utils import normalize_title, fmt_year, fmt_rating

@st.cache_data
def load_oscar_winners(path_csv="data/the_oscar_award.csv"):
    try:
        dfw = pd.read_csv(path_csv)
    except Exception as e:
        st.warning(f"No pude leer {path_csv}: {e}")
        return pd.DataFrame()
    for c in ["year_film","year_ceremony","ceremony"]:
        if c in dfw.columns: dfw[c] = pd.to_numeric(dfw[c], errors="coerce")
    for c in ["category","canon_category","name","film"]:
        if c not in dfw.columns: dfw[c] = ""
    dfw["YearFilmInt"] = dfw["year_film"].fillna(-1).astype(int)
    dfw["YearCeremonyInt"] = dfw["year_ceremony"].fillna(-1).astype(int)
    dfw["NormFilm"] = dfw["film"].apply(normalize_title)
    dfw["NormName"] = dfw["name"].apply(lambda s: re.sub(r"\s+", " ", str(s)).strip().lower())
    dfw["CanonCat"] = dfw["canon_category"].fillna(dfw["category"]).astype(str)
    if "winner" in dfw.columns:
        dfw["winner"] = dfw["winner"].astype(str).str.lower().isin(["1","true","yes","winner"])
    else:
        dfw["winner"] = True
    return dfw

@st.cache_data
def load_oscar_full(path_csv="data/full_data.csv"):
    try:
        dff = pd.read_csv(path_csv, sep=None, engine="python")
    except Exception:
        try: dff = pd.read_csv(path_csv, sep="\t")
        except Exception as e2:
            st.warning(f"No pude leer {path_csv}: {e2}")
            return pd.DataFrame()
    if "Year" in dff.columns: dff["YearInt"] = pd.to_numeric(dff["Year"], errors="coerce").fillna(-1).astype(int)
    else: dff["YearInt"] = -1
    if "CanonicalCategory" in dff.columns: dff["CanonCat"] = dff["CanonicalCategory"].fillna(dff.get("Category","")).astype(str)
    else: dff["CanonCat"] = dff.get("Category","").astype(str)
    dff["NormFilm"] = dff.get("Film","").apply(normalize_title) if "Film" in dff.columns else ""
    dff["NormName"] = dff.get("Name","").apply(lambda s: re.sub(r"\s+", " ", str(s)).strip().lower())
    if "Winner" in dff.columns:
        dff["IsWinner"] = dff["Winner"].astype(str).str.lower().isin(["1","true","yes","winner","ganador","ganadora"])
    else:
        dff["IsWinner"] = False
    return dff

def attach_my_catalog_cols(winners_df, my_catalog_df):
    if winners_df.empty or my_catalog_df is None or my_catalog_df.empty:
        winners_df = winners_df.copy()
        winners_df["InMyCatalog"] = False; winners_df["MyRating"] = None; winners_df["MyIMDb"] = None; winners_df["CatalogURL"] = None
        return winners_df
    cat = my_catalog_df.copy()
    if "NormTitle" not in cat.columns: cat["NormTitle"] = cat.get("Title","").apply(normalize_title)
    if "YearInt" not in cat.columns: cat["YearInt"] = cat.get("Year", pd.Series([None]*len(cat))).fillna(-1).astype(float).astype(int)
    winners_df = winners_df.copy()
    winners_df["JoinTitle"] = winners_df["NormFilm"]; winners_df["JoinYear"] = winners_df["YearFilmInt"]
    merged = winners_df.merge(
        cat[["NormTitle","YearInt","Your Rating","IMDb Rating","URL"]],
        left_on=["JoinTitle","JoinYear"], right_on=["NormTitle","YearInt"], how="left"
    )
    merged["InMyCatalog"] = merged["URL"].notna()
    merged["MyRating"] = merged["Your Rating"]; merged["MyIMDb"] = merged["IMDb Rating"]; merged["CatalogURL"] = merged["URL"]
    merged = merged.drop(columns=["NormTitle","YearInt","Your Rating","IMDb Rating","URL"], errors="ignore")
    return merged

def style_nominees(df):
    def _style_row(row):
        color = "rgba(34,197,94,0.22)" if row.get("Ganador?") == "🏆" else "rgba(0,0,0,0)"
        return [f"background-color: {color}"] * len(row)
    return df.style.apply(_style_row, axis=1)

def render_oscars_tab(df_catalog):
    st.markdown("## 🏆 Premios de la Academia (Óscar)")
    winners = load_oscar_winners("data/the_oscar_award.csv")
    nominees = load_oscar_full("data/full_data.csv")

    if winners.empty:
        st.info("No pude cargar ganadores (data/the_oscar_award.csv)."); return

    winners_x = attach_my_catalog_cols(winners, df_catalog)

    st.markdown("### 🎛️ Filtros en premios")
    colf1, colf2, colf3 = st.columns([1,1,2])

    if winners_x["YearCeremonyInt"].ne(-1).any():
        min_cer = int(winners_x.loc[winners_x["YearCeremonyInt"] != -1, "YearCeremonyInt"].min())
        max_cer = int(winners_x["YearCeremonyInt"].max())
    else:
        min_cer, max_cer = 1927, 2025

    with colf1:
        year_range_osc = st.slider("Año de ceremonia", min_cer, max_cer, (min_cer, max_cer))
    all_cats = sorted(winners_x["CanonCat"].dropna().unique().tolist())
    with colf2:
        cats_sel = st.multiselect("Categorías (canon)", options=all_cats, default=[])
    with colf3:
        q_aw = st.text_input("Buscar: categoría, persona o película", placeholder="Ej: ACTRESS / Spielberg / Parasite")

    ff = winners_x[(winners_x["YearCeremonyInt"] >= year_range_osc[0]) & (winners_x["YearCeremonyInt"] <= year_range_osc[1])].copy()
    if cats_sel: ff = ff[ff["CanonCat"].isin(cats_sel)]
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
    with c3: st.metric("Categorías distintas", ff["CanonCat"].nunique())
    with c4: st.metric("En mi catálogo", int(ff["InMyCatalog"].sum()))

    st.caption("Datos: data/the_oscar_award.csv y data/full_data.csv (si existe).")

    st.markdown("### 📅 Ganadores por año (sin comas en año)")
    years_sorted = sorted(ff["YearCeremonyInt"].unique())
    if years_sorted:
        y_pick = st.selectbox("Elige año de ceremonia", options=years_sorted, index=len(years_sorted)-1, key="aw_select_year")
        table_year = ff[ff["YearCeremonyInt"] == y_pick].copy()
    else:
        y_pick = None; table_year = pd.DataFrame()

    if table_year.empty:
        st.info("No hay ganadores para ese año con los filtros actuales.")
    else:
        pretty = table_year[["CanonCat","category","name","film","YearFilmInt","InMyCatalog","MyRating","MyIMDb","CatalogURL"]].copy()
        pretty = pretty.rename(columns={
            "CanonCat":"Categoría","category":"Categoría (cruda)","name":"Ganador/a","film":"Película",
            "YearFilmInt":"Año película","InMyCatalog":"En mi catálogo","MyRating":"Mi nota","MyIMDb":"IMDb","CatalogURL":"IMDb (mía)"
        })
        pretty["Año película"] = pretty["Año película"].apply(fmt_year)
        pretty["En mi catálogo"] = pretty["En mi catálogo"].map({True:"✅", False:"—"})
        if "Mi nota" in pretty.columns:
            pretty["Mi nota"] = pretty["Mi nota"].apply(lambda v: f"{float(v):.1f}" if pd.notna(v) else "")
        if "IMDb" in pretty.columns:
            pretty["IMDb"] = pretty["IMDb"].apply(lambda v: f"{float(v):.1f}" if pd.notna(v) else "")
        st.dataframe(pretty, use_container_width=True, hide_index=True)

    st.markdown("### 📝 Nominaciones del año (resalta ganador en verde)")
    if nominees.empty:
        st.info("No pude cargar nominaciones (data/full_data.csv).")
    else:
        if y_pick is None:
            st.info("Elige un año de ceremonia para ver nominaciones.")
        else:
            nom_year = nominees[nominees["YearInt"] == y_pick].copy()
            if nom_year.empty:
                st.write("No hay nominaciones para ese año.")
            else:
                nom_disp = nom_year[["CanonCat","Category","Film","Name","IsWinner"]].copy()
                nom_disp["Ganador?"] = nom_disp["IsWinner"].map({True:"🏆", False:"—"})
                nom_disp = nom_disp.drop(columns=["IsWinner"])
                nom_disp = nom_disp.rename(columns={
                    "CanonCat":"Categoría","Category":"Categoría (cruda)","Film":"Película","Name":"Nominee"
                })
                st.dataframe(style_nominees(nom_disp), use_container_width=True, hide_index=True)

    st.markdown("### 🥇 Rankings en el rango seleccionado")
    colr1, colr2 = st.columns(2)
    with colr1:
        top_films = ff.groupby(["film","YearFilmInt"]).size().reset_index(name="Wins").sort_values(["Wins","film"], ascending=[False,True]).head(15)
        if not top_films.empty:
            tf_disp = top_films.rename(columns={"film":"Película","YearFilmInt":"Año","Wins":"Óscar ganados"})
            tf_disp["Año"] = tf_disp["Año"].apply(fmt_year)
            st.dataframe(tf_disp, use_container_width=True, hide_index=True)
        else:
            st.write("Sin datos de películas en este rango.")
    with colr2:
        top_people = ff.groupby("name").size().reset_index(name="Wins").sort_values(["Wins","name"], ascending=[False,True]).head(15)
        if not top_people.empty:
            tp_disp = top_people.rename(columns={"name":"Ganador/a","Wins":"Óscar ganados"})
            st.dataframe(tp_disp, use_container_width=True, hide_index=True)
        else:
            st.write("Sin datos de personas en este rango.")
