# modules/utils.py
import re
import pandas as pd
from urllib.parse import quote_plus

def normalize_title(s: str) -> str:
    """Normaliza un título (minúsculas, sin espacios/acentos/signos) para matching."""
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

def fmt_year(y):
    if pd.isna(y):
        return ""
    try:
        return f"{int(float(y))}"
    except Exception:
        return ""

def fmt_rating(v):
    if pd.isna(v):
        return ""
    try:
        return f"{float(v):.1f}"
    except Exception:
        return str(v)

def get_rating_colors(rating):
    """
    Devuelve (border_color, glow_color) en función del rating (Your Rating o IMDb).
    Paleta sobria profesional con acento dorado / azules / púrpuras.
    """
    try:
        r = float(rating)
    except Exception:
        return ("rgba(148,163,184,0.8)", "rgba(15,23,42,0.0)")

    if r >= 9:
        return ("#22c55e", "rgba(34,197,94,0.55)")         # verde alto
    elif r >= 8:
        return ("#0ea5e9", "rgba(14,165,233,0.55)")        # azul
    elif r >= 7:
        return ("#a855f7", "rgba(168,85,247,0.50)")        # púrpura
    elif r >= 6:
        return ("#eab308", "rgba(234,179,8,0.45)")         # dorado tenue
    else:
        return ("#f97316", "rgba(249,115,22,0.45)")        # naranja

def get_spanish_review_link(title, year=None):
    if not title or pd.isna(title):
        return None
    q = f"reseña película {title}"
    try:
        if year is not None and not pd.isna(year):
            q += f" {int(float(year))}"
    except Exception:
        pass
    return "https://www.google.com/search?q=" + quote_plus(q)
