# modules/afi_list.py — pestaña 🏆 Lista AFI
import streamlit as st
import pandas as pd
import re

AFI_LIST = [
    {"Rank": 1, "Title": "Citizen Kane", "Year": 1941},
    {"Rank": 2, "Title": "The Godfather", "Year": 1972},
    {"Rank": 3, "Title": "Casablanca", "Year": 1942},
    {"Rank": 4, "Title": "Raging Bull", "Year": 1980},
    {"Rank": 5, "Title": "Singin' in the Rain", "Year": 1952},
    {"Rank": 6, "Title": "Gone with the Wind", "Year": 1939},
    {"Rank": 7, "Title": "Lawrence of Arabia", "Year": 1962},
    {"Rank": 8, "Title": "Schindler's List", "Year": 1993},
    {"Rank": 9, "Title": "Vertigo", "Year": 1958},
    {"Rank": 10, "Title": "The Wizard of Oz", "Year": 1939},
    {"Rank": 11, "Title": "City Lights", "Year": 1931},
    {"Rank": 12, "Title": "The Searchers", "Year": 1956},
    {"Rank": 13, "Title": "Star Wars", "Year": 1977},
    {"Rank": 14, "Title": "Psycho", "Year": 1960},
    {"Rank": 15, "Title": "2001: A Space Odyssey", "Year": 1968},
    {"Rank": 16, "Title": "Sunset Boulevard", "Year": 1950},
    {"Rank": 17, "Title": "The Graduate", "Year": 1967},
    {"Rank": 18, "Title": "The General", "Year": 1926},
    {"Rank": 19, "Title": "On the Waterfront", "Year": 1954},
    {"Rank": 20, "Title": "It's a Wonderful Life", "Year": 1946},
    {"Rank": 21, "Title": "Chinatown", "Year": 1974},
    {"Rank": 22, "Title": "Some Like It Hot", "Year": 1959},
    {"Rank": 23, "Title": "The Grapes of Wrath", "Year": 1940},
    {"Rank": 24, "Title": "E.T. the Extra-Terrestrial", "Year": 1982},
    {"Rank": 25, "Title": "To Kill a Mockingbird", "Year": 1962},
    {"Rank": 26, "Title": "Mr. Smith Goes to Washington", "Year": 1939},
    {"Rank": 27, "Title": "High Noon", "Year": 1952},
    {"Rank": 28, "Title": "All About Eve", "Year": 1950},
    {"Rank": 29, "Title": "Double Indemnity", "Year": 1944},
    {"Rank": 30, "Title": "Apocalypse Now", "Year": 1979},
    {"Rank": 31, "Title": "The Maltese Falcon", "Year": 1941},
    {"Rank": 32, "Title": "The Godfather Part II", "Year": 1974},
    {"Rank": 33, "Title": "One Flew Over the Cuckoo's Nest", "Year": 1975},
    {"Rank": 34, "Title": "Snow White and the Seven Dwarfs", "Year": 1937},
    {"Rank": 35, "Title": "Annie Hall", "Year": 1977},
    {"Rank": 36, "Title": "The Bridge on the River Kwai", "Year": 1957},
    {"Rank": 37, "Title": "The Best Years of Our Lives", "Year": 1946},
    {"Rank": 38, "Title": "The Treasure of the Sierra Madre", "Year": 1948},
    {"Rank": 39, "Title": "Dr. Strangelove", "Year": 1964},
    {"Rank": 40, "Title": "The Sound of Music", "Year": 1965},
    {"Rank": 41, "Title": "King Kong", "Year": 1933},
    {"Rank": 42, "Title": "Bonnie and Clyde", "Year": 1967},
    {"Rank": 43, "Title": "Midnight Cowboy", "Year": 1969},
    {"Rank": 44, "Title": "The Philadelphia Story", "Year": 1940},
    {"Rank": 45, "Title": "Shane", "Year": 1953},
    {"Rank": 46, "Title": "It Happened One Night", "Year": 1934},
    {"Rank": 47, "Title": "A Streetcar Named Desire", "Year": 1951},
    {"Rank": 48, "Title": "Rear Window", "Year": 1954},
    {"Rank": 49, "Title": "Intolerance", "Year": 1916},
    {"Rank": 50, "Title": "The Lord of the Rings: The Fellowship of the Ring", "Year": 2001},
    {"Rank": 51, "Title": "West Side Story", "Year": 1961},
    {"Rank": 52, "Title": "Taxi Driver", "Year": 1976},
    {"Rank": 53, "Title": "The Deer Hunter", "Year": 1978},
    {"Rank": 54, "Title": "M*A*S*H", "Year": 1970},
    {"Rank": 55, "Title": "North by Northwest", "Year": 1959},
    {"Rank": 56, "Title": "Jaws", "Year": 1975},
    {"Rank": 57, "Title": "Rocky", "Year": 1976},
    {"Rank": 58, "Title": "The Gold Rush", "Year": 1925},
    {"Rank": 59, "Title": "Nashville", "Year": 1975},
    {"Rank": 60, "Title": "Duck Soup", "Year": 1933},
    {"Rank": 61, "Title": "Sullivan's Travels", "Year": 1941},
    {"Rank": 62, "Title": "American Graffiti", "Year": 1973},
    {"Rank": 63, "Title": "Cabaret", "Year": 1972},
    {"Rank": 64, "Title": "Network", "Year": 1976},
    {"Rank": 65, "Title": "The African Queen", "Year": 1951},
    {"Rank": 66, "Title": "Raiders of the Lost Ark", "Year": 1981},
    {"Rank": 67, "Title": "Who's Afraid of Virginia Woolf?", "Year": 1966},
    {"Rank": 68, "Title": "Unforgiven", "Year": 1992},
    {"Rank": 69, "Title": "Tootsie", "Year": 1982},
    {"Rank": 70, "Title": "A Clockwork Orange", "Year": 1971},
    {"Rank": 71, "Title": "Saving Private Ryan", "Year": 1998},
    {"Rank": 72, "Title": "The Shawshank Redemption", "Year": 1994},
    {"Rank": 73, "Title": "Butch Cassidy and the Sundance Kid", "Year": 1969},
    {"Rank": 74, "Title": "The Silence of the Lambs", "Year": 1991},
    {"Rank": 75, "Title": "Forrest Gump", "Year": 1994},
    {"Rank": 76, "Title": "All the President's Men", "Year": 1976},
    {"Rank": 77, "Title": "Modern Times", "Year": 1936},
    {"Rank": 78, "Title": "The Wild Bunch", "Year": 1969},
    {"Rank": 79, "Title": "The Apartment", "Year": 1960},
    {"Rank": 80, "Title": "Spartacus", "Year": 1960},
    {"Rank": 81, "Title": "Sunrise: A Song of Two Humans", "Year": 1927},
    {"Rank": 82, "Title": "Titanic", "Year": 1997},
    {"Rank": 83, "Title": "Easy Rider", "Year": 1969},
    {"Rank": 84, "Title": "A Night at the Opera", "Year": 1935},
    {"Rank": 85, "Title": "Platoon", "Year": 1986},
    {"Rank": 86, "Title": "12 Angry Men", "Year": 1957},
    {"Rank": 87, "Title": "Bringing Up Baby", "Year": 1938},
    {"Rank": 88, "Title": "The Sixth Sense", "Year": 1999},
    {"Rank": 89, "Title": "Swing Time", "Year": 1936},
    {"Rank": 90, "Title": "Sophie's Choice", "Year": 1982},
    {"Rank": 91, "Title": "Tootsie", "Year": 1982},
    {"Rank": 92, "Title": "Goodfellas", "Year": 1990},
    {"Rank": 93, "Title": "The French Connection", "Year": 1971},
    {"Rank": 94, "Title": "Pulp Fiction", "Year": 1994},
    {"Rank": 95, "Title": "The Last Picture Show", "Year": 1971},
    {"Rank": 96, "Title": "Do the Right Thing", "Year": 1989},
    {"Rank": 97, "Title": "Blade Runner", "Year": 1982},
    {"Rank": 98, "Title": "Yankee Doodle Dandy", "Year": 1942},
    {"Rank": 99, "Title": "Toy Story", "Year": 1995},
    {"Rank": 100, "Title": "Ben-Hur", "Year": 1959},
]

def _normalize_title(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

def _dedup_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Hace únicos los nombres de columnas conservando orden."""
    cols = []
    seen = {}
    for c in df.columns.tolist():
        if c not in seen:
            seen[c] = 0
            cols.append(c)
        else:
            seen[c] += 1
            cols.append(f"{c}.{seen[c]}")
    df = df.copy()
    df.columns = cols
    return df

def render_afi_tab(df: pd.DataFrame):
    st.markdown("## 🎬 AFI's 100 Years...100 Movies — 10th Anniversary Edition")

    # Garantizar columnas mínimas del catálogo
    base = df.copy()
    if "Year" not in base.columns:
        base["Year"] = None
    if "Your Rating" not in base.columns:
        base["Your Rating"] = None
    if "IMDb Rating" not in base.columns:
        base["IMDb Rating"] = None
    if "URL" not in base.columns:
        base["URL"] = None
    if "NormTitle" not in base.columns:
        base["NormTitle"] = base.get("Title", "").apply(_normalize_title)
    if "YearInt" not in base.columns:
        base["YearInt"] = base["Year"].fillna(-1).astype(int)

    afi_df = pd.DataFrame(AFI_LIST)
    afi_df["NormTitle"] = afi_df["Title"].apply(_normalize_title)
    afi_df["YearInt"] = afi_df["Year"]

    # Matching flexible por título y año
    def find_match(afi_norm, year, df_full):
        cands = df_full[df_full["YearInt"] == year]
        if not cands.empty:
            m = cands[cands["NormTitle"] == afi_norm]
            if not m.empty:
                return m.iloc[0]
            m = cands[cands["NormTitle"].str.contains(afi_norm, regex=False, na=False)]
            if not m.empty:
                return m.iloc[0]
        # sin año exacto: buscar global
        m = df_full[df_full["NormTitle"] == afi_norm]
        if not m.empty:
            return m.iloc[0]
        m = df_full[df_full["NormTitle"].str.contains(afi_norm, regex=False, na=False)]
        if not m.empty:
            return m.iloc[0]
        return None

    afi_df["Your Rating"] = None
    afi_df["IMDb Rating"] = None
    afi_df["URL"] = None
    afi_df["Seen"] = False

    for idx, row in afi_df.iterrows():
        match = find_match(row["NormTitle"], row["YearInt"], base)
        if match is not None:
            afi_df.at[idx, "Your Rating"] = match.get("Your Rating")
            afi_df.at[idx, "IMDb Rating"] = match.get("IMDb Rating")
            afi_df.at[idx, "URL"] = match.get("URL")
            afi_df.at[idx, "Seen"] = True

    total_afi = len(afi_df)
    seen_afi = int(afi_df["Seen"].sum())
    pct_afi = (seen_afi / total_afi) if total_afi else 0

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Películas vistas del listado AFI", f"{seen_afi}/{total_afi}")
    with c2:
        st.metric("Progreso en AFI 100", f"{pct_afi*100:.1f}%")
    st.progress(pct_afi)

    # Tabla limpia, sin columnas duplicadas y con nombres únicos
    table = afi_df[["Rank", "Title", "Year", "Seen", "Your Rating", "IMDb Rating", "URL"]].copy()
    table = _dedup_columns(table)  # <- evita el ValueError de nombres duplicados

    # Formateo para visualización
    table["Seen"] = table["Seen"].map({True: "✅", False: "—"})
    for col in ["Your Rating", "IMDb Rating"]:
        table[col] = table[col].apply(lambda v: f"{float(v):.1f}" if pd.notna(v) else "")

    st.markdown("### Detalle del listado AFI (con mi avance)")
    st.dataframe(table, use_container_width=True, hide_index=True)
