# app.py — v1.2.2
# Diego Leal · Catálogo de Películas (modular, con barra lateral y corrección de columnas)

import streamlit as st
import pandas as pd

APP_VERSION = "1.2.2"

# ================== CONFIGURACIÓN VISUAL ==================
st.set_page_config(
    page_title=f"🎬 Mi catálogo de películas (IMDb) · v{APP_VERSION}",
    page_icon="🎞️",
    layout="wide",
)

# ---- Tema oscuro y estilos (idéntico al original) ----
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
:root {
  --bg:#0b0f19; --bg2:#0e1525; --text:#e5e7eb; --accent:#c5f6fa; --accent2:#7df9ff;
}
html, body, .stApp { background: radial-gradient(circle at 10% 0%, #12182a 0%, #0b0f19 40%, #000 100%); color:var(--text); font-family:'Inter',system-ui,sans-serif;}
[data-testid="stSidebar"] { background: linear-gradient(180deg, rgba(14,21,37,.98), rgba(14,21,37,.92)); border-right:1px solid rgba(148,163,184,.25); }
a { color: var(--accent2) !important; text-decoration: none; }
a:hover { text-decoration: underline; }
h1 { text-transform: uppercase; letter-spacing:.04em; font-weight:800;
     background: linear-gradient(90deg, #eab308, #38bdf8); -webkit-background-clip: text; color: transparent; }
[data-testid="stDataFrame"] { border-radius:18px; border:1px solid rgba(148,163,184,.45);
  background: radial-gradient(circle at top left, rgba(15,23,42,.96), rgba(15,23,42,.88)); box-shadow:0 22px 45px rgba(15,23,42,.95); }
[data-testid="stDataFrame"] thead tr { background: linear-gradient(90deg, rgba(15,23,42,.95), rgba(30,64,175,.85)); text-transform:uppercase; letter-spacing:.08em;}
[data-testid="stDataFrame"] tbody tr:hover { background-color: rgba(234,179,8,.12) !important; }
button[kind="secondary"], button[kind="primary"], .stButton > button {
  border-radius:999px !important; border:1px solid rgba(250,204,21,.7) !important;
  background: radial-gradient(circle at top left, rgba(234,179,8,.25), rgba(15,23,42,1)) !important;
  color:#fefce8 !important; font-weight:600 !important; letter-spacing:.08em; text-transform:uppercase; font-size:.78rem !important;
  padding:.48rem 1.1rem !important; box-shadow:0 10px 25px rgba(234,179,8,.35); transition: all .18s ease-out;
}
.stTabs [role="tab"] { font-weight:700; }
.footer-dl { margin-top: 28px; text-align:center; color:#9ca3af; font-size:.9rem; }
.footer-dl a { color:#9ae6b4 !important; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ================== TÍTULO PRINCIPAL ==================
st.title("🎥 Mi catálogo de películas (IMDb)")

# ================== IMPORTACIÓN DE MÓDULOS ==================
try:
    from modules import imdb_catalog, analytics, oscars_awards
except Exception as e:
    st.error("❌ No se pudieron importar los módulos. Verifica la carpeta `modules/` y los nombres de archivo.")
    st.exception(e)
    st.stop()

# ================== SIDEBAR: CARGA DE DATOS ==================
st.sidebar.header("📂 Cargar datos")

uploaded_file = st.sidebar.file_uploader("Sube tu archivo CSV (o usa el de ejemplo)", type=["csv"])

def load_data(file):
    """Carga el CSV y adapta nombres de columnas a las que usan los módulos."""
    if file is not None:
        df = pd.read_csv(file)
    else:
        df = pd.read_csv("data/peliculas.csv")

    # Limpieza básica de nombres
    df.columns = [c.strip() for c in df.columns]

    # Normalización de columnas de género
    rename_map = {
        "Genre": "GenreList",
        "Genres": "GenreList",
        "genre": "GenreList",
        "genres": "GenreList"
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Si existe columna GenreList, convertir en listas
    if "GenreList" in df.columns and df["GenreList"].dtype == object:
        df["GenreList"] = df["GenreList"].apply(
            lambda x: [g.strip() for g in str(x).split(",")] if pd.notna(x) else []
        )

    # Normalizar otras columnas opcionales usadas en los módulos
    for col in ["Year", "Rating", "Title"]:
        if col not in df.columns:
            df[col] = None

    return df

df = load_data(uploaded_file)
st.sidebar.markdown(f"**Películas cargadas:** {len(df):,}")

# ================== PESTAÑAS PRINCIPALES ==================
tab1, tab2, tab3 = st.tabs(["🎬 Catálogo", "📊 Análisis", "🏆 Premios Óscar"])

with tab1:
    imdb_catalog.render_catalog_tab(df)

with tab2:
    analytics.render_analysis_tab(df)

with tab3:
    oscars_awards.render_oscars_tab(df)

# ================== FOOTER ==================
st.markdown(
    f"""
<div class="footer-dl">
  v<strong>{APP_VERSION}</strong> · powered by <strong>Diego Leal</strong>
</div>
""",
    unsafe_allow_html=True,
)
