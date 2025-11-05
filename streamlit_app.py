import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="🎬 Catálogo de Películas",
    layout="wide"
)

st.title("🎥 Mi catálogo de películas")

st.write(
    "App basada en tu export de IMDb. "
    "Puedes filtrar por año, nota, géneros, director y buscar por título."
)

# ---------- Carga de datos ----------

@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    # Asegurar tipos
    df["Your Rating"] = pd.to_numeric(df["Your Rating"], errors="coerce")
    df["IMDb Rating"] = pd.to_numeric(df["IMDb Rating"], errors="coerce")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Genres"] = df["Genres"].fillna("")
    df["Directors"] = df["Directors"].fillna("")
    # Lista de géneros
    df["GenreList"] = df["Genres"].str.split(", ")
    return df

st.sidebar.header("📂 Datos")

uploaded = st.sidebar.file_uploader(
    "Sube tu CSV de IMDb (si no, usaré peliculas.csv)",
    type=["csv"]
)

if uploaded is not None:
    df = load_data(uploaded)
else:
    df = load_data("peliculas.csv")  # archivo que subes al repo

# ---------- Filtros en sidebar ----------

st.sidebar.header("🎛️ Filtros")

# Rango de años
min_year = int(df["Year"].min())
max_year = int(df["Year"].max())
year_range = st.sidebar.slider(
    "Rango de años",
    min_year, max_year,
    (min_year, max_year)
)

# Rango de nota propia
min_rating = int(df["Your Rating"].min())
max_rating = int(df["Your Rating"].max())
rating_range = st.sidebar.slider(
    "Tu nota (Your Rating)",
    min_rating, max_rating,
    (min_rating, max_rating)
)

# Géneros
all_genres = sorted(
    set(g for sub in df["GenreList"].dropna() for g in sub if g)
)
selected_genres = st.sidebar.multiselect(
    "Géneros",
    options=all_genres
)

# Directores
all_directors = sorted(
    set(d.strip() for d in df["Directors"].dropna() if d.strip())
)
selected_directors = st.sidebar.multiselect(
    "Directores",
    options=all_directors
)

# Búsqueda por texto
search_title = st.sidebar.text_input("Buscar en título")

# Orden
order_by = st.sidebar.selectbox(
    "Ordenar por",
    ["Your Rating", "IMDb Rating", "Year", "Title"]
)
order_asc = st.sidebar.checkbox("Orden ascendente", value=False)

# ---------- Aplicar filtros ----------

filtered = df.copy()

# Año
filtered = filtered[
    (filtered["Year"] >= year_range[0]) &
    (filtered["Year"] <= year_range[1])
]

# Nota propia
filtered = filtered[
    (filtered["Your Rating"] >= rating_range[0]) &
    (filtered["Your Rating"] <= rating_range[1])
]

# Géneros (todas las seleccionadas deben estar presentes)
if selected_genres:
    filtered = filtered[
        filtered["GenreList"].apply(
            lambda gl: gl is not None and all(g in gl for g in selected_genres)
        )
    ]

# Directores
if selected_directors:
    filtered = filtered[filtered["Directors"].isin(selected_directors)]

# Búsqueda por título
if search_title:
    filtered = filtered[
        filtered["Title"].str.contains(search_title, case=False, na=False)
        | filtered["Original Title"].astype(str).str.contains(search_title, case=False, na=False)
    ]

filtered = filtered.sort_values(order_by, ascending=order_asc)

# ---------- Métricas rápidas ----------

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Películas filtradas", len(filtered))
with col2:
    st.metric("Promedio de tu nota", f"{filtered['Your Rating'].mean():.2f}")
with col3:
    st.metric("Promedio IMDb", f"{filtered['IMDb Rating'].mean():.2f}")

st.markdown("---")

# ---------- Tabla principal ----------

st.subheader("📚 Resultados")

columns_to_show = [
    "Title", "Year", "Your Rating", "IMDb Rating",
    "Genres", "Directors", "Date Rated", "URL"
]

st.dataframe(
    filtered[columns_to_show],
    use_container_width=True,
    hide_index=True
)

# ---------- Favoritas destacadas ----------

st.markdown("---")
st.subheader("⭐ Tus favoritas (nota ≥ 9) en este filtro")

fav = filtered[filtered["Your Rating"] >= 9].sort_values(
    ["Your Rating", "Year"], ascending=[False, True]
)

if fav.empty:
    st.write("No hay favoritas con estos filtros.")
else:
    for _, row in fav.iterrows():
        with st.expander(f"{int(row['Your Rating'])}/10 — {row['Title']} ({int(row['Year'])})"):
            st.write(f"**Géneros:** {row['Genres']}")
            st.write(f"**Director(es):** {row['Directors']}")
            st.write(f"**IMDb:** {row['IMDb Rating']}")
            st.write(f"[Ver en IMDb]({row['URL']})")
