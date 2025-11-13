# modules/afi_list.py
import pandas as pd
import streamlit as st
from modules.utils import fmt_year, fmt_rating

# Lista corta para ejemplo; puedes reemplazar por tu lista completa
AFI_LIST = [
    {"Rank": 1, "Title": "Citizen Kane", "Year": 1941},
    {"Rank": 2, "Title": "The Godfather", "Year": 1972},
    {"Rank": 3, "Title": "Casablanca", "Year": 1942},
    {"Rank": 4, "Title": "Raging Bull", "Year": 1980},
    {"Rank": 5, "Title": "Singin' in the Rain", "Year": 1952},
]

def _normalize(s: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+","", str(s).lower())

def render_afi_tab(df_all: pd.DataFrame):
    st.markdown("### 🎖️ AFI 100 — Mi progreso")
    afi = pd.DataFrame(AFI_LIST)
    afi["Norm"] = afi["Title"].apply(_normalize)
    pool = df_all.copy()
    if "Year" not in pool.columns or "Title" not in pool.columns:
        st.info("Faltan columnas básicas en el CSV para cruzar la lista AFI.")
        return
    pool["Norm"] = pool["Title"].apply(_normalize)
    pool["YearInt"] = pd.to_numeric(pool["Year"], errors="coerce").fillna(-1).astype(int)

    afi["Seen"] = False
    afi["Your Rating"] = None
    afi["IMDb Rating"] = None
    afi["URL"] = None

    for i, r in afi.iterrows():
        cands = pool[pool["YearInt"]==int(r["Year"])]
        m = cands[cands["Norm"]==r["Norm"]]
        if m.empty:
            m = cands[cands["Norm"].str.contains(r["Norm"], regex=False, na=False)]
        if m.empty:
            m = pool[pool["Norm"]==r["Norm"]]
        if not m.empty:
            row = m.iloc[0]
            afi.at[i,"Seen"] = True
            afi.at[i,"Your Rating"] = row.get("Your Rating")
            afi.at[i,"IMDb Rating"] = row.get("IMDb Rating")
            afi.at[i,"URL"] = row.get("URL")

    total = len(afi); seen = int(afi["Seen"].sum())
    st.metric("Películas vistas", f"{seen}/{total}")
    st.progress(seen/total if total else 0.0)

    show = afi[["Rank","Title","Year","Seen","Your Rating","IMDb Rating","URL"]].copy()
    show["Year"] = show["Year"].astype(int).astype(str)
    show["Your Rating"] = show["Your Rating"].apply(fmt_rating)
    show["IMDb Rating"] = show["IMDb Rating"].apply(fmt_rating)
    show["Vista"] = show["Seen"].map({True:"✅", False:"—"})
    st.dataframe(
        show[["Rank","Title","Year","Vista","Your Rating","IMDb Rating","URL"]],
        hide_index=True, use_container_width=True
    )
