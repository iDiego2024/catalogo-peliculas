{\rtf1\ansi\ansicpg1252\cocoartf2865
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import pandas as pd\
\
st.set_page_config(\
    page_title="\uc0\u55356 \u57260  Cat\'e1logo de Pel\'edculas",\
    layout="wide"\
)\
\
st.title("\uc0\u55356 \u57253  Mi cat\'e1logo de pel\'edculas")\
\
st.write(\
    "App basada en tu export de IMDb. "\
    "Puedes filtrar por a\'f1o, nota, g\'e9neros, director y buscar por t\'edtulo."\
)\
\
# ---------- Carga de datos ----------\
\
@st.cache_data\
def load_data(file):\
    df = pd.read_csv(file)\
    # Asegurar tipos\
    df["Your Rating"] = pd.to_numeric(df["Your Rating"], errors="coerce")\
    df["IMDb Rating"] = pd.to_numeric(df["IMDb Rating"], errors="coerce")\
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")\
    df["Genres"] = df["Genres"].fillna("")\
    df["Directors"] = df["Directors"].fillna("")\
    # Lista de g\'e9neros\
    df["GenreList"] = df["Genres"].str.split(", ")\
    return df\
\
st.sidebar.header("\uc0\u55357 \u56514  Datos")\
\
uploaded = st.sidebar.file_uploader(\
    "Sube tu CSV de IMDb (si no, usar\'e9 peliculas.csv)",\
    type=["csv"]\
)\
\
if uploaded is not None:\
    df = load_data(uploaded)\
else:\
    df = load_data("peliculas.csv")  # archivo que subes al repo\
\
# ---------- Filtros en sidebar ----------\
\
st.sidebar.header("\uc0\u55356 \u57243 \u65039  Filtros")\
\
# Rango de a\'f1os\
min_year = int(df["Year"].min())\
max_year = int(df["Year"].max())\
year_range = st.sidebar.slider(\
    "Rango de a\'f1os",\
    min_year, max_year,\
    (min_year, max_year)\
)\
\
# Rango de nota propia\
min_rating = int(df["Your Rating"].min())\
max_rating = int(df["Your Rating"].max())\
rating_range = st.sidebar.slider(\
    "Tu nota (Your Rating)",\
    min_rating, max_rating,\
    (min_rating, max_rating)\
)\
\
# G\'e9neros\
all_genres = sorted(\
    set(g for sub in df["GenreList"].dropna() for g in sub if g)\
)\
selected_genres = st.sidebar.multiselect(\
    "G\'e9neros",\
    options=all_genres\
)\
\
# Directores\
all_directors = sorted(\
    set(d.strip() for d in df["Directors"].dropna() if d.strip())\
)\
selected_directors = st.sidebar.multiselect(\
    "Directores",\
    options=all_directors\
)\
\
# B\'fasqueda por texto\
search_title = st.sidebar.text_input("Buscar en t\'edtulo")\
\
# Orden\
order_by = st.sidebar.selectbox(\
    "Ordenar por",\
    ["Your Rating", "IMDb Rating", "Year", "Title"]\
)\
order_asc = st.sidebar.checkbox("Orden ascendente", value=False)\
\
# ---------- Aplicar filtros ----------\
\
filtered = df.copy()\
\
# A\'f1o\
filtered = filtered[\
    (filtered["Year"] >= year_range[0]) &\
    (filtered["Year"] <= year_range[1])\
]\
\
# Nota propia\
filtered = filtered[\
    (filtered["Your Rating"] >= rating_range[0]) &\
    (filtered["Your Rating"] <= rating_range[1])\
]\
\
# G\'e9neros (todas las seleccionadas deben estar presentes)\
if selected_genres:\
    filtered = filtered[\
        filtered["GenreList"].apply(\
            lambda gl: gl is not None and all(g in gl for g in selected_genres)\
        )\
    ]\
\
# Directores\
if selected_directors:\
    filtered = filtered[filtered["Directors"].isin(selected_directors)]\
\
# B\'fasqueda por t\'edtulo\
if search_title:\
    filtered = filtered[\
        filtered["Title"].str.contains(search_title, case=False, na=False)\
        | filtered["Original Title"].astype(str).str.contains(search_title, case=False, na=False)\
    ]\
\
filtered = filtered.sort_values(order_by, ascending=order_asc)\
\
# ---------- M\'e9tricas r\'e1pidas ----------\
\
col1, col2, col3 = st.columns(3)\
with col1:\
    st.metric("Pel\'edculas filtradas", len(filtered))\
with col2:\
    st.metric("Promedio de tu nota", f"\{filtered['Your Rating'].mean():.2f\}")\
with col3:\
    st.metric("Promedio IMDb", f"\{filtered['IMDb Rating'].mean():.2f\}")\
\
st.markdown("---")\
\
# ---------- Tabla principal ----------\
\
st.subheader("\uc0\u55357 \u56538  Resultados")\
\
columns_to_show = [\
    "Title", "Year", "Your Rating", "IMDb Rating",\
    "Genres", "Directors", "Date Rated", "URL"\
]\
\
st.dataframe(\
    filtered[columns_to_show],\
    use_container_width=True,\
    hide_index=True\
)\
\
# ---------- Favoritas destacadas ----------\
\
st.markdown("---")\
st.subheader("\uc0\u11088  Tus favoritas (nota \u8805  9) en este filtro")\
\
fav = filtered[filtered["Your Rating"] >= 9].sort_values(\
    ["Your Rating", "Year"], ascending=[False, True]\
)\
\
if fav.empty:\
    st.write("No hay favoritas con estos filtros.")\
else:\
    for _, row in fav.iterrows():\
        with st.expander(f"\{int(row['Your Rating'])\}/10 \'97 \{row['Title']\} (\{int(row['Year'])\})"):\
            st.write(f"**G\'e9neros:** \{row['Genres']\}")\
            st.write(f"**Director(es):** \{row['Directors']\}")\
            st.write(f"**IMDb:** \{row['IMDb Rating']\}")\
            st.write(f"[Ver en IMDb](\{row['URL']\})")\
}