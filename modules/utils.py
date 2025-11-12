import streamlit as st
import pandas as pd
import requests
import re
import random
import altair as alt
from urllib.parse import quote_plus

APP_VERSION = "1.2.0"

CHANGELOG = {
    "1.2.0": [
        "Refactor modular: app separada en módulos y carpeta data/.",
        "Corrección de año SIN comas en todas las vistas (se fuerza a string).",
        "Ganador marcado en verde en nominaciones/año.",
        "Versión movida al pie de página con 'powered by Diego Leal'.",
    ],
    "1.1.0": [
        "Nueva pestaña 🏆 Premios Óscar (búsqueda, filtros, vista por año→categorías→ganadores, rankings y tendencias).",
        "Cruce de ganadores con tu catálogo (marca si está en tu CSV y muestra tus notas/IMDb).",
        "Soporte opcional para nominaciones desde full_data.csv.",
    ],
    "1.0.0": [
        "Catálogo, filtros, galería visual paginada, análisis, AFI y ¿Qué ver hoy?",
        "Integraciones opcionales: TMDb, YouTube y OMDb para premios por película.",
    ],
}

def setup_page():
    st.markdown("""
    <style>
    [data-testid=\"stDataFrame\"] tbody tr:hover { background-color: rgba(234,179,8,0.12) !important; }
    </style>
    """, unsafe_allow_html=True)

def footer():
    st.markdown("---")
    st.caption(f"Versión **v{APP_VERSION}** · powered by Diego Leal")

def normalize_title(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

@st.cache_data
def load_data(file_path_or_buffer):
    df = pd.read_csv(file_path_or_buffer)
    if "Your Rating" in df.columns: df["Your Rating"] = pd.to_numeric(df["Your Rating"], errors="coerce")
    else: df["Your Rating"] = None
    if "IMDb Rating" in df.columns: df["IMDb Rating"] = pd.to_numeric(df["IMDb Rating"], errors="coerce")
    else: df["IMDb Rating"] = None
    if "Year" in df.columns:
        df["Year"] = df["Year"].astype(str).str.extract(r"(\d{4})")[0].astype(float)
    else:
        df["Year"] = None
    if "Genres" not in df.columns: df["Genres"] = ""
    if "Directors" not in df.columns: df["Directors"] = ""
    df["Genres"] = df["Genres"].fillna("")
    df["GenreList"] = df["Genres"].apply(lambda x: [] if pd.isna(x) or x == "" else str(x).split(", "))
    if "Date Rated" in df.columns: df["Date Rated"] = pd.to_datetime(df["Date Rated"], errors="coerce").dt.date
    search_cols = [c for c in ["Title","Original Title","Directors","Genres","Year","Your Rating","IMDb Rating"] if c in df.columns]
    df["SearchText"] = (df[search_cols].astype(str).apply(lambda row: " ".join(row), axis=1).str.lower()) if search_cols else ""
    df["NormTitle"] = df["Title"].apply(normalize_title)
    df["YearInt"] = df["Year"].fillna(-1).astype(int) if "Year" in df.columns else -1
    return df

def fmt_year(y):
    if pd.isna(y): return ""
    return f"{int(float(y))}"

def fmt_rating(v):
    if pd.isna(v): return ""
    try: return f"{float(v):.1f}"
    except Exception: return str(v)

def get_spanish_review_link(title, year=None):
    if not title or pd.isna(title): return None
    q = f"reseña película {title}"
    try:
        if year is not None and not pd.isna(year): q += f" {int(float(year))}"
    except Exception: pass
    return "https://www.google.com/search?q=" + quote_plus(q)

AFI_LIST = [
    {"Rank": 1, "Title": "Citizen Kane", "Year": 1941},
    {"Rank": 2, "Title": "The Godfather", "Year": 1972},
    {"Rank": 3, "Title": "Casablanca", "Year": 1942},
]

def render_afi_tab(df):
    st.markdown("## 🎬 AFI's 100 Years...100 Movies — 10th Anniversary Edition")
    import pandas as pd
    afi_df = pd.DataFrame(AFI_LIST)
    afi_df["NormTitle"] = afi_df["Title"].apply(normalize_title)
    afi_df["YearInt"] = afi_df["Year"]
    if "YearInt" not in df.columns:
        df["YearInt"] = df["Year"].fillna(-1).astype(int) if "Year" in df.columns else -1
    if "NormTitle" not in df.columns:
        df["NormTitle"] = df["Title"].apply(normalize_title) if "Title" in df.columns else ""

    afi_df["Your Rating"] = None
    afi_df["IMDb Rating"] = None
    afi_df["URL"] = None
    afi_df["Seen"] = False

    for idx, row in afi_df.iterrows():
        year = row["YearInt"]; nt = row["NormTitle"]
        cands = df[df["YearInt"] == year]
        match = None
        if not cands.empty:
            m = cands[cands["NormTitle"] == nt]
            if not m.empty: match = m.iloc[0]
        if match is None and not cands.empty:
            m = cands[cands["NormTitle"].str.contains(nt, na=False)]
            if not m.empty: match = m.iloc[0]
        if match is None:
            m = df[df["NormTitle"] == nt]
            if not m.empty: match = m.iloc[0]
        if match is None:
            m = df[df["NormTitle"].str.contains(nt, na=False)]
            if not m.empty: match = m.iloc[0]
        if match is not None:
            afi_df.at[idx, "Your Rating"] = match.get("Your Rating")
            afi_df.at[idx, "IMDb Rating"] = match.get("IMDb Rating")
            afi_df.at[idx, "URL"] = match.get("URL")
            afi_df.at[idx, "Seen"] = True

    total_afi = len(afi_df); seen_afi = int(afi_df["Seen"].sum()); pct_afi = (seen_afi/total_afi) if total_afi>0 else 0.0
    col1, col2 = st.columns(2)
    with col1: st.metric("Películas vistas del listado AFI", f"{seen_afi}/{total_afi}")
    with col2: st.metric("Progreso en AFI 100", f"{pct_afi*100:.1f}%"); st.progress(pct_afi)

    afi_table = afi_df.copy(); afi_table["Vista"] = afi_table["Seen"].map({True:"✅", False:"—"})
    afi_table_display = afi_table[["Rank","Title","Year","Vista","Your Rating","IMDb Rating","URL"]].copy()
    afi_table_display["Year"] = afi_table_display["Year"].astype(int).astype(str)
    afi_table_display["Your Rating"] = afi_table_display["Your Rating"].apply(fmt_rating)
    afi_table_display["IMDb Rating"] = afi_table_display["IMDb Rating"].apply(fmt_rating)
    st.dataframe(afi_table_display, hide_index=True, use_container_width=True)

def render_what_to_watch_tab(df):
    st.markdown("## 🎲 ¿Qué ver hoy?")
    pool = df.copy()
    if st.button("Recomendar una película"):
        if pool.empty:
            st.warning("Tu catálogo está vacío."); return
        if "Your Rating" in pool.columns and pool["Your Rating"].notna().any():
            notas = pool["Your Rating"].fillna(0); pesos = (notas + 1).tolist()
        else:
            pesos = None
        import random
        idx = random.choices(pool.index.tolist(), weights=pesos, k=1)[0]
        peli = pool.loc[idx]
        titulo = peli.get("Title", "Sin título"); year = peli.get("Year", "")
        st.success(f"Recomendación: **{titulo}** {{'(' + str(int(year)) + ')' if year else ''}}")
