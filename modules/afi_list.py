# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

from modules.utils import (
    AFI_LIST,
    normalize_title,
    fmt_year,
    fmt_rating,   # <- ojo, con "g"
)

def _ensure_aux_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "YearInt" not in out.columns:
        if "Year" in out.columns:
            out["YearInt"] = out["Year"].fillna(-1).astype(int)
        else:
            out["YearInt"] = -1
    if "NormTitle" not in out.columns:
        if "Title" in out.columns:
            out["NormTitle"] = out["Title"].apply(normalize_title)
        else:
            out["NormTitle"] = ""
    return out

def _find_match(afi_norm, year, df_full):
    candidates = df_full[df_full["YearInt"] == year]

    def _try(cands):
        if cands.empty:
            return None
        return cands.iloc[0]

    m = _try(candidates[candidates["NormTitle"] == afi_norm])
    if m is not None: return m

    m = _try(candidates[candidates["NormTitle"].str.contains(afi_norm, regex=False, na=False)])
    if m is not None: return m

    m = _try(candidates[candidates["NormTitle"].apply(lambda t: afi_norm in t or t in afi_norm)])
    if m is not None: return m

    candidates = df_full

    m = _try(candidates[candidates["NormTitle"] == afi_norm])
    if m is not None: return m

    m = _try(candidates[candidates["NormTitle"].str.contains(afi_norm, regex=False, na=False)])
    if m is not None: return m

    m = _try(candidates[candidates["NormTitle"].apply(lambda t: afi_norm in t or t in afi_norm)])
    if m is not None: return m

    return None

def render_afi_tab(df: pd.DataFrame):
    st.markdown("## 🎬 AFI's 100 Years...100 Movies — 10th Anniversary Edition")

    with st.expander("Ver mi progreso en la lista AFI 100", expanded=True):
        afi_df = pd.DataFrame(AFI_LIST)
        afi_df["NormTitle"] = afi_df["Title"].apply(normalize_title)
        afi_df["YearInt"] = afi_df["Year"]

        df2 = _ensure_aux_cols(df)

        afi_df["Your Rating"] = None
        afi_df["IMDb Rating"] = None
        afi_df["URL"] = None
        afi_df["Seen"] = False

        for idx, row in afi_df.iterrows():
            match = _find_match(row["NormTitle"], row["YearInt"], df2)
            if match is not None:
                afi_df.at[idx, "Your Rating"] = match.get("Your Rating")
                afi_df.at[idx, "IMDb Rating"] = match.get("IMDb Rating")
                afi_df.at[idx, "URL"] = match.get("URL")
                afi_df.at[idx, "Seen"] = True

        total_afi = len(afi_df)
        seen_afi = int(afi_df["Seen"].sum())
        pct_afi = (seen_afi / total_afi) if total_afi > 0 else 0.0

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Películas vistas del listado AFI", f"{seen_afi}/{total_afi}")
        with col2:
            st.metric("Progreso en AFI 100", f"{pct_afi * 100:.1f}%")
        st.progress(pct_afi)

        st.write("Este progreso se calcula sobre todo mi catálogo, no sólo los filtros actuales.")

        afi_table = afi_df.copy()
        afi_table["Vista"] = afi_table["Seen"].map({True: "✅", False: "—"})

        afi_table_display = afi_table[["Rank", "Title", "Year", "Vista", "Your Rating", "IMDb Rating", "URL"]].copy()
        afi_table_display["Year"] = afi_table_display["Year"].astype(int).astype(str)
        afi_table_display["Your Rating"] = afi_table_display["Your Rating"].apply(fmt_rating)
        afi_table_display["IMDb Rating"] = afi_table_display["IMDb Rating"].apply(fmt_rating)

        st.markdown("### Detalle del listado AFI (con mi avance)")
        st.dataframe(afi_table_display, hide_index=True, use_container_width=True)
