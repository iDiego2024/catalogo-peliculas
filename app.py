# app.py  — v1.2.0 (carátula visual + orquestación de pestañas)

import streamlit as st

APP_VERSION = "1.2.0"

# ====== Config de página (tema y look&feel idéntico al original) ======
st.set_page_config(
    page_title=f"🎬 Mi catálogo de películas (IMDb) · v{APP_VERSION}",
    page_icon="🎞️",
    layout="wide",
)

# ---- CSS (tema oscuro + detalles visuales) ----
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

# ====== Encabezado ======
st.title("🎥 Mi catálogo de películas (IMDb)")

# ==============================================================
#  Imports de módulos (ajusta nombres si tus archivos difieren)
# ==============================================================

# Opción A: módulos por pestaña (recomendado)
try:
    from modules.data_io import load_catalog  # lectura del CSV y normalizaciones comunes
    from modules.tab_catalog import render_catalog_tab
    from modules.tab_analysis import render_analysis_tab
    from modules.tab_afi import render_afi_tab
    from modules.tab_oscars import render_oscars_tab
    from modules.tab_what_to_watch import render_what_tab
    MODULE_MODE = "tabs"
except Exception:
    # Opción B: un solo módulo con un runner (por si tu modularización es diferente)
    try:
        from modules.app_core import run_app  # debe encapsular todo el flujo
        MODULE_MODE = "core"
    except Exception as e:
        MODULE_MODE = None
        st.error("No se pudieron importar los módulos. Revisa que la carpeta `modules/` exista y los nombres coincidan.")
        st.exception(e)

# ==============================================================
#  Carga de datos (sidebar) y estado compartido
# ==============================================================

if MODULE_MODE == "tabs":
    with st.sidebar:
        st.header("📂 Datos")
        uploaded = st.file_uploader("Sube tu CSV de IMDb (si no, usaré `data/peliculas.csv`)", type=["csv"])
        # `load_catalog` debe aceptar `uploaded` o ruta por defecto
    df = load_catalog(uploaded)  # el módulo se encarga de usar data/peliculas.csv cuando uploaded es None

    # Guardamos en session_state para que todos los tabs lo lean igual
    st.session_state["catalog_df"] = df

    # ==============================================================
    #  Pestañas principales
    # ==============================================================
    tab_catalog, tab_analysis, tab_afi, tab_awards, tab_what = st.tabs(
        ["🎬 Catálogo", "📊 Análisis", "🏆 Lista AFI", "🏆 Premios Óscar", "🎲 ¿Qué ver hoy?"]
    )

    with tab_catalog:
        render_catalog_tab(df)

    with tab_analysis:
        render_analysis_tab(df)

    with tab_afi:
        render_afi_tab(df)

    with tab_awards:
        render_oscars_tab(df)

    with tab_what:
        render_what_tab(df)

elif MODULE_MODE == "core":
    # Si tu modularización usa un solo “runner”, lo ejecutamos y listo.
    run_app(APP_VERSION)

# ====== Footer con versión (abajo) ======
st.markdown(
    f"""
<div class="footer-dl">
  v<strong>{APP_VERSION}</strong> · powered by <strong>Diego Leal</strong>
</div>
""",
    unsafe_allow_html=True,
)
