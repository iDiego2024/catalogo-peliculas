# modules/analytics.py — pestaña 📊 Análisis
import streamlit as st
import pandas as pd
import altair as alt

def _fmt_year_col(s):
    try:
        return s.astype(int).astype(str)
    except Exception:
        return s

def render_analysis_tab(df: pd.DataFrame):
    st.markdown("## 📊 Análisis y tendencias (según filtros, sin búsqueda)")
    st.caption("Los gráficos usan todo tu catálogo cargado.")

    if df.empty:
        st.info("No hay datos para analizar.")
        return

    # Asegurar columnas mínimas
    if "Year" not in df.columns:
        df = df.assign(Year=None)
    if "Your Rating" not in df.columns:
        df = df.assign(**{"Your Rating": None})
    if "IMDb Rating" not in df.columns:
        df = df.assign(**{"IMDb Rating": None})
    if "GenreList" not in df.columns and "Genres" in df.columns:
        df = df.assign(GenreList=df["Genres"].fillna("").apply(lambda x: [] if x == "" else str(x).split(", ")))
    elif "GenreList" not in df.columns:
        df = df.assign(GenreList=[])

    col_a, col_b = st.columns(2)

    # Películas por año
    with col_a:
        st.markdown("**Películas por año**")
        by_year = (
            df[df["Year"].notna()]
            .groupby("Year")
            .size()
            .reset_index(name="Count")
            .sort_values("Year")
        )
        if not by_year.empty:
            by_year["Year"] = _fmt_year_col(by_year["Year"])
            st.line_chart(by_year.set_index("Year"))
        else:
            st.write("Sin datos de año.")

    # Distribución de mi nota
    with col_b:
        st.markdown("**Distribución de mi nota (Your Rating)**")
        if df["Your Rating"].notna().any():
            rc = (
                df["Your Rating"]
                .round()
                .value_counts()
                .sort_index()
                .reset_index()
            )
            rc.columns = ["Rating", "Count"]
            rc["Rating"] = rc["Rating"].astype(int).astype(str)
            st.bar_chart(rc.set_index("Rating"))
        else:
            st.write("No hay notas propias.")

    col_c, col_d = st.columns(2)

    # Top géneros
    with col_c:
        st.markdown("**Top géneros (por número de películas)**")
        gexp = df.explode("GenreList")
        gexp = gexp[gexp["GenreList"].notna() & (gexp["GenreList"] != "")]
        if not gexp.empty:
            tg = gexp["GenreList"].value_counts().head(15).reset_index()
            tg.columns = ["Genre", "Count"]
            st.bar_chart(tg.set_index("Genre"))
        else:
            st.write("No hay géneros.")

    # IMDb promedio por década
    with col_d:
        st.markdown("**IMDb promedio por década**")
        tmp = df[df["Year"].notna() & df["IMDb Rating"].notna()].copy()
        if not tmp.empty:
            tmp["Decade"] = (tmp["Year"] // 10 * 10).astype(int)
            di = tmp.groupby("Decade")["IMDb Rating"].mean().reset_index().sort_values("Decade")
            di["Decade"] = di["Decade"].astype(int).astype(str)
            st.line_chart(di.set_index("Decade"))
        else:
            st.write("No hay IMDb Rating suficiente.")

    st.markdown("### 🔬 Análisis avanzado (mi nota vs IMDb)")
    corr_df = df[["Your Rating", "IMDb Rating"]].dropna() if {"Your Rating", "IMDb Rating"}.issubset(df.columns) else pd.DataFrame()

    col_e, col_f = st.columns(2)
    with col_e:
        if not corr_df.empty and len(corr_df) > 1:
            corr = corr_df["Your Rating"].corr(corr_df["IMDb Rating"])
            st.metric("Correlación Pearson (mi nota vs IMDb)", f"{corr:.2f}")
        else:
            st.metric("Correlación Pearson (mi nota vs IMDb)", "N/A")
        st.write("Valores cercanos a 1 → coincido con IMDb; 0 → independiente; negativos → voy en contra.")

    with col_f:
        st.markdown("**Dispersión: IMDb vs mi nota**")
        if not corr_df.empty:
            chart = (
                alt.Chart(corr_df.reset_index())
                .mark_circle(size=60, opacity=0.6)
                .encode(
                    x=alt.X("IMDb Rating:Q", scale=alt.Scale(domain=[0,10])),
                    y=alt.Y("Your Rating:Q", scale=alt.Scale(domain=[0,10])),
                    tooltip=["IMDb Rating", "Your Rating"]
                )
                .properties(height=300)
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("No hay suficientes datos para el scatter.")

    # Mapa de calor: mi nota media por género y década
    st.markdown("**Mapa de calor: mi nota media por género y década**")
    tmp = df[df["Year"].notna() & df["Your Rating"].notna()].copy()
    if not tmp.empty and "GenreList" in tmp.columns:
        tmp["Decade"] = (tmp["Year"] // 10 * 10).astype(int).astype(str)
        g = tmp.explode("GenreList")
        g = g[g["GenreList"].notna() & (g["GenreList"] != "")]
        if not g.empty:
            heat = g.groupby(["GenreList","Decade"])["Your Rating"].mean().reset_index()
            heat = heat.rename(columns={"GenreList":"Género","Decade":"Década","Your Rating":"Mi nota media"})
            st.dataframe(heat, use_container_width=True, hide_index=True)
        else:
            st.write("No hay datos suficientes de géneros.")
    else:
        st.write("Faltan columnas 'Year' y/o 'Your Rating'.")
