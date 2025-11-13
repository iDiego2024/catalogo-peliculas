# modules/analytics.py
import pandas as pd
import streamlit as st

def render_analysis_tab(filtered_df: pd.DataFrame):
    st.markdown("### 📊 Análisis simple (según filtros)")
    if filtered_df.empty:
        st.info("No hay datos bajo los filtros actuales.")
        return
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("**Películas por año**")
        dfy = filtered_df.copy()
        dfy = dfy[pd.to_numeric(dfy["Year"], errors="coerce").notna()].copy()
        dfy["Year"] = dfy["Year"].astype(int).astype(str)
        st.line_chart(dfy.groupby("Year").size())
    with c2:
        st.markdown("**Distribución de mi nota**")
        if "Your Rating" in filtered_df.columns and filtered_df["Your Rating"].notna().any():
            r = filtered_df["Your Rating"].round().value_counts().sort_index()
            r.index = r.index.astype(int).astype(str)
            st.bar_chart(r)
        else:
            st.write("Sin notas personales.")
