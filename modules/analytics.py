import streamlit as st
import pandas as pd

def render_analytics_tab(df):
    st.markdown("## 📊 Análisis y tendencias")
    if df.empty:
        st.info("No hay datos para analizar."); return
    by_year = (
        df[df["Year"].notna()].groupby("Year").size().reset_index(name="Count").sort_values("Year")
    )
    if not by_year.empty:
        disp = by_year.copy(); disp["Year"] = disp["Year"].astype(int).astype(str); disp = disp.set_index("Year")
        st.line_chart(disp)
    else:
        st.write("Sin datos de año.")
