"""
ui.py — Gemeinsame Streamlit-UI-Bausteine (Styling, Metrik-Kacheln, Sektionen, Pills)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Diese Datei buendelt die zuvor in jedem Betriebsmittel-Tab duplizierten
Praesentationsbausteine. utils.py bleibt bewusst streamlit-frei (reine Rechen- und
Formatierungsfunktionen), damit die calc-Schicht nicht an Streamlit gekoppelt wird.
"""

import streamlit as st

from utils import AMPEL_EMOJI

# ── Farbkodierung (explizite Textfarben -> auch im Dark-Theme lesbar) ─────────
TAB_CSS = """
<style>
/* Einklappbare Sektionen (st.expander) durchgehend HSU-blau */
[data-testid="stExpander"] summary {
    background: #2E5A87 !important;
    border-radius: 6px !important;
    padding: 5px 12px !important;
}
[data-testid="stExpander"] summary:hover { background: #27496e !important; }
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: #ffffff !important; font-weight: 600 !important; font-size: 0.92rem !important;
}
[data-testid="stExpander"] summary svg { fill: #ffffff !important; color: #ffffff !important; }
[data-testid="stExpander"] details { border: none !important; }

.result-box {
    background: #eef3f8; color: #14203a;
    border-left: 4px solid #2E5A87; border-radius: 6px;
    padding: 10px 14px; margin-bottom: 8px;
}
.result-box .val { font-size: 1.2rem; font-weight: 700; color: #14203a; font-family: monospace; }
.result-box .lbl { font-size: 0.76rem; color: #43526b; }
.result-box .sub { font-size: 0.74rem; color: #5d6b82; margin-top: 2px; }
.warn-box {
    background: #fff4d6; color: #5b4a00;
    border-left: 4px solid #f4a800; border-radius: 6px;
    padding: 10px 14px; font-size: 0.86rem; margin-bottom: 8px;
}
.off-box {
    background: #fbe3ea; color: #7a0024;
    border-left: 4px solid #A50034; border-radius: 6px;
    padding: 10px 14px; font-size: 0.86rem; margin-bottom: 8px;
}
.off-box b { color: #A50034; }
.info-box {
    background: #e7f3ec; color: #14502b;
    border-left: 4px solid #2e7d32; border-radius: 6px;
    padding: 10px 14px; font-size: 0.86rem; margin-bottom: 8px;
}
.pill { display:inline-block; padding:2px 9px; border-radius:11px;
        font-size:0.75rem; font-weight:700; }
.pill-ok   { background:#d6f0dc; color:#1d6b32; }
.pill-warn { background:#fdeccb; color:#8a5b00; }
.pill-bad  { background:#fad3dc; color:#a3002b; }
.pill-na   { background:#e6e9ee; color:#5d6b82; }
</style>
"""

PILL_CLASS = {"OK": "pill-ok", "Hinweis": "pill-warn", "Prüfen!": "pill-bad",
              "Fehlt": "pill-na", "—": "pill-na"}


def inject_css():
    """CSS einmal pro Tab-Aufruf in die Seite einspielen."""
    st.markdown(TAB_CSS, unsafe_allow_html=True)


def metric(label, value, sub=""):
    """Ergebnis-Kachel (Label + Wert + optionaler Unterzeile)."""
    st.markdown(
        f'<div class="result-box"><div class="lbl">{label}</div>'
        f'<div class="val">{value}</div>'
        + (f'<div class="sub">{sub}</div>' if sub else "") + "</div>",
        unsafe_allow_html=True,
    )


def section(title, expanded=True):
    """Einklappbare, blau gestylte Sektion. Verwendung: with section('...'):"""
    return st.expander(title, expanded=expanded)


def grphead(title):
    """Funktions-Untertitel innerhalb eines gruppierten Erweiterte-Parameter-Expanders.
    Erbt die Theme-Textfarbe (im dunklen Theme weiss), mit blauem Trennstrich wie die Tabs.
    Einheitlich ueber alle Betriebsmittel-Tabs (zuvor lokal in Leitung/Sammelschiene)."""
    st.markdown(
        f'<div style="font-weight:700;font-size:0.97rem;margin:18px 0 8px;'
        f'padding-bottom:4px;border-bottom:2px solid #2E5A87;">{title}</div>',
        unsafe_allow_html=True)


def pin(adr):
    """Schlanker Adress-Pin unter einem Eingabefeld ('Eintragen unter: Adr.X').
    Fuer Parameter ohne HERST-Hinweis; ergaenzt die Hersteller-Box hreg()."""
    if not adr:
        return
    st.markdown(
        f'<div style="font-size:0.72rem;color:#5d6b82;margin:-6px 0 10px;">'
        f'📍 <b>Eintragen unter:</b> Adr.{adr}</div>',
        unsafe_allow_html=True)


def pill(status, count):
    """Statistik-Pill fuer den Plausibilitaets-Header: Emoji + Status + Anzahl."""
    cls = PILL_CLASS.get(status, "pill-na")
    emj = AMPEL_EMOJI.get(status, "")
    return f'<span class="pill {cls}">{emj} {status}: {count}</span>'


def hreg(herst, key):
    """Hersteller-Hinweis (Range + Begruendung + Eintrag-Adresse) unter einem Regler.

    herst: das HERST-Dict des jeweiligen Betriebsmittel-Moduls (z. B. K.HERST).
    Bei Eintraegen ohne DIGSI-Adresse wird ein Rechengroessen-Hinweis gezeigt.
    """
    h = herst.get(key)
    if not h:
        return
    adr = h.get("adr")
    pin = (f'<br>📍 <b>Eintragen unter:</b> {adr}' if adr
           else '<br>📍 <b>Rechengröße</b> (kein direkter DIGSI-Parameter, '
                'fließt in die Sollwerte ein)')
    st.markdown(
        f'<div style="font-size:0.72rem;color:#5d6b82;margin:-6px 0 10px;line-height:1.25;">'
        f'<b>Hersteller:</b> {h["range"]}<br>{h["grund"]}{pin}</div>',
        unsafe_allow_html=True)
