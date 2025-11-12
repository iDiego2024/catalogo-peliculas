# modules/what_to_watch.py
# Pestaña: 🎲 ¿Qué ver hoy?

import streamlit as st
import pandas as pd
import random

def fmt_year(y):
    try:
        if pd.isna(y):
            return ""
        return f"{int(float(y))}"
    except Exception:
        return ""

def fmt_rating(v):
    try:
        return "" if pd.isna(v) else f"{float(v):.1f}"
    except Exception:
        return ""

def render_what_tab(df: pd.DataFrame):
    st.markdown("## 🎲 ¿Qué ver hoy? (según mi propio gusto)")
    st.write("Elige una película de tu catálogo usando tus notas y el año de estreno.")

    with st.expander("Ver recomendación aleatoria según mi gusto", expanded=True):
        modo = st.selectbox(
            "Modo de recomendación",
            [
                "Entre todas las películas",
                "Solo mis favoritas (nota ≥ 9)",
                "Entre mis 8–10 de los últimos 20 años",
            ],
            key="what_mode",
        )

        if st.button("Recomendar una película", key="btn_reco"):
            pool = df.copy()

            # Asegurar columnas
            if "Your Rating" not in pool.columns:
                pool["Your Rating"] = None
            if "Year" not in pool.columns:
                pool["Year"] = None

            if modo == "Solo mis favoritas (nota ≥ 9)":
                pool = pool[pool["Your Rating"].notna() & (pool["Your Rating"] >= 9)]
            elif modo == "Entre mis 8–10 de los últimos 20 años":
                current_year = pd.Timestamp.now().year
                pool = pool[
                    pool["Your Rating"].notna()
                    & (pool["Your Rating"] >= 8)
                    & pool["Year"].notna()
                    & (pool["Year"] >= current_year - 20)
                ]

            if pool.empty:
                st.warning("No hay películas que cumplan el criterio.")
                return

            # Pesos por tu nota (si existe)
            if pool["Your Rating"].notna().any():
                pesos = (pool["Your Rating"].fillna(0) + 1).tolist()
            else:
                pesos = None

            idx = random.choices(pool.index.tolist(), weights=pesos, k=1)[0]
            peli = pool.loc[idx]

            title = peli.get("Title", "Sin título")
            year = peli.get("Year")
            my = peli.get("Your Rating")
            imdb = peli.get("IMDb Rating")
            genres = peli.get("Genres") or ""
            directors = peli.get("Directors") or ""
            url = peli.get("URL") or ""

            st.markdown(f"### ✅ Te recomiendo: **{title}** {f'({fmt_year(year)})' if year is not None else ''}")
            col1, col2 = st.columns(2)
            with col1:
                if pd.notna(my):
                    st.metric("Mi nota", fmt_rating(my))
                if pd.notna(imdb):
                    st.metric("IMDb", fmt_rating(imdb))
            with col2:
                if genres:
                    st.write(f"**Géneros:** {genres}")
                if directors:
                    st.write(f"**Director(es):** {directors}")
                if isinstance(url, str) and url.startswith("http"):
                    st.write(f"[Ver en IMDb]({url})")

    # Sugerencias rápidas (top por tu nota)
    st.markdown("---")
    st.markdown("### 📌 Otras sugerencias rápidas (según mis notas)")
    sug = df.copy()
    if "Your Rating" in sug.columns:
        sug = sug[sug["Your Rating"].notna()]
        if not sug.empty:
            sug = sug.sort_values(["Your Rating", "IMDb Rating", "Year"], ascending=[False, False, False]).head(10)
            mini = sug[["Title", "Year", "Your Rating", "IMDb Rating", "Genres"]].copy()
            mini["Year"] = mini["Year"].apply(fmt_year)
            mini["Your Rating"] = mini["Your Rating"].apply(fmt_rating)
            mini["IMDb Rating"] = mini["IMDb Rating"].apply(fmt_rating)
            mini = mini.rename(columns={
                "Title": "Película", "Year": "Año", "Your Rating": "Mi nota", "IMDb Rating": "IMDb", "Genres": "Géneros"
            })
            st.dataframe(mini, use_container_width=True, hide_index=True)
        else:
            st.write("No tengo notas suficientes para sugerencias.")
    else:
        st.write("No se encontró la columna 'Your Rating' en el CSV.")
