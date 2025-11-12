import streamlit as st
import pandas as pd
from modules.utils import AFI_LIST, normalize_title, fmt_year, fmt_rating

def render_afi_tab(df):
    st.markdown("## 🎬 AFI's 100 Years...100 Movies — 10th Anniversary Edition")

    with st.expander("Ver mi progreso en la lista AFI 100", expanded=True):
        afi_df = pd.DataFrame(AFI_LIST)
        if afi_df.empty or not {"Rank","Title","Year"}.issubset(afi_df.columns):
            st.info("La lista AFI está vacía o incompleta.")
            return

        afi_df["NormTitle"] = afi_df["Title"].apply(normalize_title)
        afi_df["YearInt"] = pd.to_numeric(afi_df["Year"], errors="coerce").fillna(-1).astype(int)

        # Asegurar columnas base en mi catálogo
        dlocal = df.copy()
        if "YearInt" not in dlocal.columns:
            dlocal["YearInt"] = pd.to_numeric(dlocal.get("Year"), errors="coerce").fillna(-1).astype(float).astype(int)
        if "NormTitle" not in dlocal.columns:
            dlocal["NormTitle"] = dlocal.get("Title", "").apply(normalize_title)

        def find_match(afi_norm, year, df_full):
            # 1) por año exacto
            cands = df_full[df_full["YearInt"] == year]
            if not cands.empty:
                m = cands[cands["NormTitle"] == afi_norm]
                if not m.empty: return m.iloc[0]
                m = cands[cands["NormTitle"].str.contains(afi_norm, regex=False, na=False)]
                if not m.empty: return m.iloc[0]
            # 2) sin año
            m = df_full[df_full["NormTitle"] == afi_norm]
            if not m.empty: return m.iloc[0]
            m = df_full[df_full["NormTitle"].str.contains(afi_norm, regex=False, na=False)]
            if not m.empty: return m.iloc[0]
            return None

        afi_df["Your Rating"] = None
        afi_df["IMDb Rating"] = None
        afi_df["URL"] = None
        afi_df["Seen"] = False

        for idx, row in afi_df.iterrows():
            match = find_match(row["NormTitle"], row["YearInt"], dlocal)
            if match is not None:
                afi_df.at[idx, "Your Rating"] = match.get("Your Rating")
                afi_df.at[idx, "IMDb Rating"] = match.get("IMDb Rating")
                afi_df.at[idx, "URL"] = match.get("URL")
                afi_df.at[idx, "Seen"] = True

        total_afi = len(afi_df)
        seen_afi = int(afi_df["Seen"].sum())
        pct_afi = (seen_afi / total_afi) if total_afi > 0 else 0.0

        col_afi1, col_afi2 = st.columns(2)
        with col_afi1:
            st.metric("Películas vistas del listado AFI", f"{seen_afi}/{total_afi}")
        with col_afi2:
            st.metric("Progreso en AFI 100", f"{pct_afi * 100:.1f}%")
        st.progress(pct_afi)

        table = afi_df.copy()
        table["Seen"] = table["Seen"].map({True: "✅", False: "—"})
        table["Year"] = pd.to_numeric(table["Year"], errors="coerce").fillna(-1).astype(int).astype(str)
        table["Your Rating"] = table["Your Rating"].apply(fmt_rating)
        table["IMDb Rating"] = table["IMDb Rating"].apply(fmt_rating)

        st.markdown("### Detalle del listado AFI (con mi avance)")
        st.dataframe(
            table[["Rank", "Title", "Year", "Seen", "Your Rating", "IMDb Rating", "URL"]],
            use_container_width=True, hide_index=True
        )
