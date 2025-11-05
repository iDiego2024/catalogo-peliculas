import streamlit as st
import pandas as pd

st.set_page_config(page_title="🎬 Catálogo de Películas", layout="wide")

st.title("🎥 Mi catálogo de películas (IMDb CSV)")

st.write("Sube tu archivo exportado desde IMDb para ver y filtrar tus películas.")

archivo = st.file_uploader("Sube tu CSV de IMDb", type=["csv"])

if archivo is None:
    st.info("⬆️ Arriba puedes subir tu archivo CSV para empezar.")
    st.stop()

# Carga de datos
df = pd.read_csv(archivo)

st.success(f"Se cargaron {len(df)} filas desde el CSV.")

# Mostrar una vista básica
st.subheader("Vista rápida de tus datos")
st.dataframe(df.head(100), use_container_width=True)
