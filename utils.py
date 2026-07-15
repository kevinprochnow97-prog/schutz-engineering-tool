"""
utils.py — Gemeinsame Hilfsfunktionen
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Bewusst streamlit-frei: reine Formatierungsfunktionen und die Ampel-Symbolik,
damit die calc-Schicht nicht an Streamlit gekoppelt wird.
"""


def de(x, n: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma, ohne Tausenderpunkt (um Verwechslung mit der
    punktbasierten Streamlit-Eingabe und mit DIGSI-Adressen zu vermeiden).
    Beispiel: de(2.0, 2) -> '2,00', de(4000.0, 0) -> '4000'."""
    return f"{x:.{n}f}".replace(".", ",")


def deg(x) -> str:
    """Wie das Format ':g' (variable Nachkommastellen, keine unnoetigen Nullen),
    aber mit deutschem Dezimalkomma. Fuer dimensionslose Faktoren.
    Beispiel: deg(2.0) -> '2', deg(1.5) -> '1,5'."""
    return f"{x:g}".replace(".", ",")


# ── Ampel-Symbolik (gemeinsam fuer alle Betriebsmittel-Tabs) ─────────────────

AMPEL_EMOJI = {"OK": "🟢", "Hinweis": "🟡", "Prüfen!": "🔴", "Fehlt": "⚫", "—": "▫️"}
