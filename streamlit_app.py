
# 🎬 Catálogo de Películas - Versión Final Dorado
# Estructura: Resumen → Tabla → Galería (todas las películas filtradas) → Favoritas

import streamlit as st
import pandas as pd
import requests
import math
import random
import re
from urllib.parse import quote_plus

# ---------------- CONFIGURACIÓN GENERAL ----------------

st.set_page_config(page_title="🎬 Catálogo de Películas", layout="wide")

st.markdown('''
    <style>
        body { background-color: #000; color: #fefce8; }
        .main { background-color: #000; color: #fefce8; }
        h1, h2, h3, h4 {
            color: #facc15;
            text-shadow: 0 0 20px rgba(250,204,21,0.6);
        }
        .movie-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
            gap: 20px;
            justify-items: center;
            padding: 20px;
        }
        .movie-card {
            background: radial-gradient(circle at top left, #0f172a 0%, #000 100%);
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid rgba(250,204,21,0.5);
            box-shadow: 0 0 25px rgba(250,204,21,0.3);
            transition: all 0.3s ease;
            width: 100%;
            max-width: 240px;
        }
        .movie-card:hover {
            transform: scale(1.05);
            box-shadow: 0 0 40px rgba(250,204,21,0.7);
        }
        .movie-poster-frame {
            width: 100%;
            height: 340px;
            background: #111;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        .movie-poster-img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .movie-poster-placeholder {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: radial-gradient(circle at center, #111 40%, #000 100%);
            width: 100%;
            height: 100%;
            color: #facc15;
            font-size: 22px;
            text-shadow: 0 0 12px #facc15;
        }
        .film-reel-icon { font-size: 42px; margin-bottom: 10px; }
        .movie-title {
            text-align: center;
            color: #facc15;
            font-weight: bold;
            padding: 10px;
            font-size: 1rem;
            text-shadow: 0 0 10px #facc15;
        }
        .movie-sub {
            padding: 10px;
            font-size: 0.9rem;
            color: #e5e7eb;
            text-align: center;
        }
    </style>
''', unsafe_allow_html=True)

# ---------------- FUNCIONES AUXILIARES ----------------

def get_tmdb_data(title):
    return {
        "poster": "https://image.tmdb.org/t/p/w342/saHP97rTPS5eLmrLQEcANmKrsFl.jpg" if random.random() > 0.4 else None,
        "imdb": round(random.uniform(6, 9), 1),
        "tmdb": round(random.uniform(6, 9), 1),
        "streaming": random.choice(["Netflix", "Amazon Prime Video", "Disney+", "HBO Max", "Apple TV", "MovistarTV"]),
        "premios": random.choice(["Oscar", "Golden Globe", "BAFTA", "Cannes", "Sin premios"])
    }

def fmt_rating(v):
    return f"{v:.1f}" if v else "N/A"

# ---------------- DATOS SIMULADOS ----------------

peliculas = [
    {"titulo": "Blade Runner", "año": 1982, "nota": 10.0, "director": "Ridley Scott", "generos": "Sci-Fi, Drama"},
    {"titulo": "Casablanca", "año": 1942, "nota": 9.8, "director": "Michael Curtiz", "generos": "Romance, War"},
    {"titulo": "E.T.", "año": 1982, "nota": 9.7, "director": "Steven Spielberg", "generos": "Family, Sci-Fi"},
    {"titulo": "Apocalypse Now", "año": 1979, "nota": 9.5, "director": "Francis Ford Coppola", "generos": "War, Drama"},
    {"titulo": "Inside Out", "año": 2015, "nota": 9.0, "director": "Pete Docter", "generos": "Animation, Family"},
    {"titulo": "The Godfather", "año": 1972, "nota": 10.0, "director": "Francis Ford Coppola", "generos": "Crime, Drama"},
]

# ---------------- FILTROS ----------------

st.sidebar.header("🎛️ Filtros")
año_min, año_max = st.sidebar.slider("Rango de años", 1940, 2025, (1940, 2025))
nota_min, nota_max = st.sidebar.slider("Rango de notas", 0.0, 10.0, (0.0, 10.0))
orden = st.sidebar.selectbox("Ordenar por:", ["Título", "Año", "Nota"], index=0)
desc = st.sidebar.checkbox("Orden descendente", value=False)

filtro = [p for p in peliculas if año_min <= p["año"] <= año_max and nota_min <= p["nota"] <= nota_max]
filtro.sort(key=lambda x: x["nota"] if orden == "Nota" else x["año"] if orden == "Año" else x["titulo"], reverse=desc)

# ---------------- SECCIONES ----------------

st.title("🎬 Catálogo de Películas")

# 1️⃣ RESUMEN
st.markdown("## 📊 Resumen de resultados")
col1, col2, col3 = st.columns(3)
col1.metric("Películas encontradas", len(filtro))
col2.metric("Promedio de nota", f"{sum(p['nota'] for p in filtro)/len(filtro):.2f}" if filtro else "N/A")
col3.metric("Década más frecuente", f"{(sum(p['año'] for p in filtro)//len(filtro))//10*10}s" if filtro else "N/A")

# 2️⃣ TABLA
st.markdown("## 📋 Tabla de resultados")
df = pd.DataFrame(filtro)
st.dataframe(df, use_container_width=True, hide_index=True)

# 3️⃣ GALERÍA COMPLETA
st.markdown("## 🧱 Galería visual de películas (todas las filtradas)")
if not filtro:
    st.info("No hay películas con los filtros actuales.")
else:
    st.markdown('<div class="movie-grid">', unsafe_allow_html=True)
    for p in filtro:
        info = get_tmdb_data(p["titulo"])
        st.markdown(f'''
        <div class="movie-card">
            <div class="movie-poster-frame">
                {f'<img src="{info["poster"]}" class="movie-poster-img">' if info["poster"] else '<div class="movie-poster-placeholder"><div class="film-reel-icon">🎞️</div><div class="film-reel-text">Sin póster</div></div>'}
            </div>
            <div class="movie-title">{p["titulo"]} ({p["año"]})</div>
            <div class="movie-sub">
                ⭐ Mi nota: {fmt_rating(p["nota"])}<br>
                IMDb: {fmt_rating(info["imdb"])} | TMDb: {fmt_rating(info["tmdb"])}<br>
                <b>Géneros:</b> {p["generos"]}<br>
                <b>Director:</b> {p["director"]}<br>
                <b>Premios:</b> {info["premios"]}<br>
                <b>Streaming:</b> {info["streaming"]}<br>
                <a href="https://www.google.com/search?q=reseña+película+{quote_plus(p["titulo"])}" target="_blank">🔗 Reseñas en español</a>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 4️⃣ FAVORITAS
st.markdown("## ⭐ Mis favoritas (nota ≥ 9.5)")
favoritas = [p for p in filtro if p["nota"] >= 9.5]
if not favoritas:
    st.info("No hay películas favoritas con los filtros actuales.")
else:
    for f in favoritas:
        st.markdown(f"🎥 **{f['titulo']} ({f['año']})** — ⭐ {f['nota']} — 🎬 {f['director']}")
