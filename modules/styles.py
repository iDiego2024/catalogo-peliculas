# modules/styles.py
import streamlit as st

def inject_theme_css():
    """
    Inyecta el tema oscuro con efectos dorados + layout más ancho en desktop
    y clases para la galería (cuadrícula con 2:3).
    """
    primary_bg = "#020617"
    secondary_bg = "#020617"
    text_color = "#e5e7eb"
    card_bg = "rgba(15,23,42,0.9)"
    accent_color = "#eab308"     # dorado
    accent_soft = "rgba(234,179,8,0.25)"
    accent_alt = "#38bdf8"       # celeste de acento

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        :root {{
            --bg-primary: {primary_bg};
            --bg-secondary: {secondary_bg};
            --text-color: {text_color};
            --card-bg: {card_bg};
            --accent: {accent_color};
            --accent-soft: {accent_soft};
            --accent-alt: {accent_alt};
            --radius-lg: 14px;
            --radius-xl: 18px;
        }}

        html, body, .stApp {{
            background: radial-gradient(circle at top left, #0f172a 0%, #020617 40%, #000000 100%);
            color: var(--text-color);
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        /* MÁS ANCHO EN ESCRITORIO, responsivo en móvil */
        .main .block-container {{
            max-width: 1200px;
            padding-top: 3.0rem;
            padding-bottom: 3rem;
        }}

        @media (min-width: 1500px) {{
            .main .block-container {{
                max-width: 1400px;
            }}
        }}

        @media (max-width: 900px) {{
            .main .block-container {{
                max-width: 100%;
                padding-left: 0.75rem;
                padding-right: 0.75rem;
            }}
        }}

        /* Sidebar */
        [data-testid="stSidebar"] > div:first-child {{
            background: linear-gradient(180deg, rgba(15,23,42,0.98), rgba(15,23,42,0.90));
            border-right: 1px solid rgba(148,163,184,0.25);
            box-shadow: 0 0 30px rgba(0,0,0,0.7);
        }}
        [data-testid="stSidebar"] * {{
            color: #e5e7eb !important;
            font-size: 0.9rem;
        }}

        /* Títulos con degradado dorado */
        h1, h2, h3, h4 {{
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
            letter-spacing: 0.04em;
        }}
        h1 {{
            text-transform: uppercase;
            font-weight: 800;
            font-size: 2.0rem !important;
            background: linear-gradient(90deg, var(--accent), var(--accent-alt));
            -webkit-background-clip: text;
            color: transparent;
            margin-top: 1.2rem;
            margin-bottom: 0.6rem;
            line-height: 1.25;
            text-align: left;
        }}
        h2 {{
            font-weight: 700;
            font-size: 1.4rem !important;
            margin-top: 1.5rem;
            margin-bottom: 0.25rem;
        }}

        .stMarkdown, .stText, .stCaption, p {{ color: var(--text-color); }}
        a {{ color: var(--accent-alt) !important; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}

        /* Métricas */
        [data-testid="stMetric"] {{
            background: radial-gradient(circle at top left, rgba(15,23,42,0.95), rgba(15,23,42,0.75));
            padding: 14px 16px;
            border-radius: 14px;
            border: 1px solid rgba(148,163,184,0.45);
            box-shadow: 0 12px 30px rgba(15,23,42,0.7);
            backdrop-filter: blur(10px);
        }}
        [data-testid="stMetricLabel"], [data-testid="stMetricDelta"] {{
            color: #9ca3af !important;
            font-size: 0.75rem !important;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }}
        [data-testid="stMetricValue"] {{
            color: #e5e7eb !important;
            font-weight: 700;
            font-size: 1.4rem !important;
        }}

        /* Expanders y botones */
        [data-testid="stExpander"] {{
            border-radius: var(--radius-xl) !important;
            border: 1px solid rgba(148,163,184,0.5);
            background: radial-gradient(circle at top left, rgba(15,23,42,0.98), rgba(15,23,42,0.85));
            margin-bottom: 1rem;
            box-shadow: 0 12px 30px rgba(15,23,42,0.7);
        }}
        button[kind="secondary"], button[kind="primary"], .stButton > button {{
            border-radius: 999px !important;
            border: 1px solid rgba(250, 204, 21, 0.7) !important;
            background: radial-gradient(circle at top left, rgba(234,179,8,0.25), rgba(15,23,42,1)) !important;
            color: #fefce8 !important;
            font-weight: 600 !important;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-size: 0.75rem !important;
            padding: 0.45rem 1.2rem !important;
            box-shadow: 0 10px 25px rgba(234,179,8,0.35);
            transition: all 0.18s ease-out;
        }}
        button[kind="secondary"]:hover, button[kind="primary"]:hover, .stButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 0 0 1px rgba(250,204,21,0.7), 0 0 26px rgba(250,204,21,0.75);
        }}

        /* Dataframes */
        [data-testid="stDataFrame"] {{
            border-radius: var(--radius-xl) !important;
            border: 1px solid rgba(148,163,184,0.6);
            background: radial-gradient(circle at top left, rgba(15,23,42,0.96), rgba(15,23,42,0.88));
            box-shadow: 0 0 0 1px rgba(15,23,42,0.9), 0 22px 45px rgba(15,23,42,0.95);
            overflow: hidden;
        }}
        [data-testid="stDataFrame"] * {{ color: #e5e7eb !important; font-size: 0.82rem; }}
        [data-testid="stDataFrame"] thead tr {{
            background: linear-gradient(90deg, rgba(15,23,42,0.95), rgba(30,64,175,0.85));
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}
        [data-testid="stDataFrame"] tbody tr:hover {{
            background-color: rgba(234,179,8,0.12) !important;
            transition: background-color 0.15s ease-out;
        }}

        /* Tarjetas + galería 2:3 */
        .movie-card {{
            background: radial-gradient(circle at top left, rgba(15,23,42,0.9), rgba(15,23,42,0.85));
            border-radius: var(--radius-lg);
            padding: 14px 14px 12px 14px;
            margin-bottom: 14px;
            border: 1px solid rgba(148,163,184,0.45);
            box-shadow: 0 18px 40px rgba(15,23,42,0.8);
            backdrop-filter: blur(12px);
            position: relative;
            overflow: hidden;
            transition: all 0.16s ease-out;
        }}
        .movie-card-grid {{ display: flex; flex-direction: column; gap: 0.4rem; }}
        .movie-card-grid:hover {{
            transform: translateY(-4px) scale(1.01);
            box-shadow: 0 0 0 1px rgba(250,204,21,0.7), 0 0 32px rgba(250,204,21,0.85);
            border-color: #facc15 !important;
        }}
        .movie-title {{
            font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase;
            font-size: 0.86rem; margin-bottom: 2px; color: #f9fafb;
        }}
        .movie-sub {{ font-size: 0.78rem; line-height: 1.35; color: #cbd5f5; }}

        .movie-gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 18px;
            margin-top: 0.7rem;
        }}
        @media (max-width: 900px) {{
            .movie-gallery-grid {{
                grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
                gap: 14px;
            }}
        }}

        .movie-poster-frame {{
            width: 100%;
            aspect-ratio: 2 / 3; /* CUADRATURA 2:3 */
            border-radius: 14px;
            overflow: hidden;
            background: radial-gradient(circle at top, #020617 0%, #000000 55%, #020617 100%);
            border: 1px solid rgba(148,163,184,0.5);
            position: relative;
            box-shadow: 0 14px 30px rgba(0,0,0,0.85);
        }}
        .movie-poster-img {{
            width: 100%; height: 100%; object-fit: cover; display: block;
            transform-origin: center; transition: transform 0.25s ease-out;
        }}
        .movie-card-grid:hover .movie-poster-img {{ transform: scale(1.03); }}

        .movie-poster-placeholder {{
            width: 100%; height: 100%; display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            background: radial-gradient(circle at 15% 0%, rgba(250,204,21,0.12), rgba(15,23,42,1)),
                        radial-gradient(circle at 85% 100%, rgba(56,189,248,0.16), rgba(0,0,0,1));
            position: relative;
        }}
        .film-reel-text {{
            font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.16em;
            color: #e5e7eb; opacity: 0.95;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
