"""
utils.py — Gemeinsame Hilfsfunktionen
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg
"""

import math

SQRT3 = math.sqrt(3)


def mva_to_va(mva: float) -> float:
    return mva * 1e6


def kv_to_v(kv: float) -> float:
    return kv * 1e3


def nennstrom(S_VA: float, U_V: float) -> float:
    """Nennstrom aus Scheinleistung und Spannung (3-phasig)."""
    return S_VA / (SQRT3 * U_V)


def fmt_a(val: float, n: int = 4) -> str:
    return f"{val:.{n}f} A"


def fmt_pct(val: float, n: int = 1) -> str:
    return f"{val:.{n}f} %"


def de(x, n: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma, ohne Tausenderpunkt (um Verwechslung mit der
    punktbasierten Streamlit-Eingabe und mit DIGSI-Adressen zu vermeiden).
    Beispiel: de(2.0, 2) -> '2,00', de(4000.0, 0) -> '4000'."""
    return f"{x:.{n}f}".replace(".", ",")


# ── Ampel-Hilfsfunktionen (gemeinsam fuer alle Betriebsmittel-Tabs) ──────────

AMPEL_EMOJI = {"OK": "🟢", "Hinweis": "🟡", "Prüfen!": "🔴", "Fehlt": "⚫", "—": "▫️"}


def ampel(status: str) -> str:
    """Status-Text mit vorangestelltem Ampel-Emoji (themesicher lesbar)."""
    return f"{AMPEL_EMOJI.get(status, '')} {status}"


def fmt_min(val: float) -> str:
    """Thermische Zeitkonstante in Minuten (nicht Sekunden!)."""
    return f"{val:.0f} min"
