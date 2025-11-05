# ----------------- Tema (siempre oscuro) + CSS -----------------

# Valores fijos de modo oscuro
primary_bg = "#0e1117"
secondary_bg = "#161b22"
text_color = "#f9fafb"
card_bg = "#161b22"

st.sidebar.header("🎨 Tema")
st.sidebar.write("Modo oscuro activado 🌚")

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {primary_bg};
        color: {text_color};
    }}
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{
        color: {text_color};
    }}
    .movie-card {{
        background-color: {card_bg};
        border-radius: 0.75rem;
        padding: 0.75rem 0.9rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.12);
        border: 1px solid rgba(148,163,184,0.35);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .movie-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.25);
    }}
    .movie-title {{
        font-weight: 600;
        margin-bottom: 0.3rem;
        color: {text_color};
    }}
    .movie-sub {{
        font-size: 0.85rem;
        opacity: 0.9;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)
