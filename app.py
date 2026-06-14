"""
app.py — Hauptdatei des Schutz-Engineering-Tools
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg
Starten mit: streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Schutz-Engineering-Tool | HSU Hamburg",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── HSU-Header ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.hsu-banner {
    background: #A50034; color: white;
    padding: 10px 20px; border-radius: 8px; margin-bottom: 1.2rem;
    display: flex; justify-content: space-between; align-items: center;
}
.hsu-banner h1 { font-size: 1.15rem; margin: 0; font-weight: 700; }
.hsu-banner p  { font-size: 0.78rem; margin: 0; opacity: 0.85; }
.hsu-banner .right { text-align: right; font-size: 0.75rem; opacity: 0.75; }
</style>
<div class="hsu-banner">
    <div>
        <h1>⚡ Schutz-Engineering-Tool</h1>
        <p>HSU Hamburg · Professur für Elektrische Energiesysteme · Herstellerneutrale Schutzparametrierung</p>
    </div>
    <div class="right">
        Industrienetz isoliert / kompensiert<br>
        Methodik: SIPROTEC 7UT6xx / 7UM62 / 7SJ66 / 7SA6xx / 7SD5xxx / 7SS52xx<br>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Tab-Navigation (Info zuerst, dann Betriebsmittel) ─────────────────────────
tab_info, tab_trafo, tab_gen, tab_motor, tab_leitung, tab_sb = st.tabs([
    "ℹ️  Info & Anleitung",
    "🔧  Transformator",
    "⚡  Generator",
    "⚙️  Motor",
    "📏  Leitung",
    "🛤️  Sammelschiene",
])

with tab_info:
    st.markdown("""
    ### Über dieses Tool
    Dieses Tool berechnet herstellerneutrale Schutzparameter für elektrische Betriebsmittel
    in industriellen Mittelspannungsnetzen. Die Berechnungsmethodik folgt den Einstellhinweisen
    der SIPROTEC-Gerätefamilie (Siemens) als Referenz.

    **Norm-Grundlagen:** IEC 60255-151, IEC 60255-187-3, VDE-FNN-Leitfaden

    **Aufbau einer Betriebsmittel-Seite (Beispiel Transformator):**
    - Eingaben (Grunddaten, Stromwandler primär/sekundär, Netzparameter)
    - Berechnete Grundgrößen (Nennströme, Übersetzung, Wandlerverhältnisse, Bezugsstrom)
    - Differentialschutz 87T · Erdschluss-/Erdfehlerschutz (87N · 50N/51N · U0)
    - Überstromzeitschutz Phasen 50/51 (OS + US)
    - Bemessungs-Engineering (Stufenwahl + Empfindlichkeit)
    - Thermischer Überlastschutz 49 · Schieflastschutz 46 · Übererregungsschutz 24 (U/f)
    - Plausibilitätsprüfung (Ampel) mit konkreten Korrektur-Anweisungen
    - Reserveschutz-Zuordnung · Geräte-Empfehlung Erdschlusserfassung

    **Ampel-Logik:** 🟢 OK · 🟡 Hinweis (Wert plausibel, aber prüfen) · 🔴 Prüfen! / Fehlt.

    **Hinweis zu Einheiten (Dezimaltrennzeichen):**
    Streamlit verwendet den **Punkt** als Dezimaltrennzeichen (englische Locale).
    Eingabe `16.5` entspricht also 16,5 MVA.

    **Thermische Zeitkonstante τ (ANSI 49):**
    Die Einheit hängt vom Schutzgerät ab und ist im jeweiligen Tab angegeben:
    - **Transformator (7UT613):** τ in **Minuten** (Adr. 4203)
    - **Generator (7UM62):** τ in **Sekunden** (Adr. 1603)
    - **Motor (7SJ66):** τ in **Minuten** (Adr. 4203)

    Die Verwechslung von Minuten und Sekunden ist eine häufige Fehlerquelle.

    **Selektivität / Staffelung:** Außerhalb des Scope dieses Tools.
    Das Tool berechnet komponentenbezogene Parameter — keine netzweite Selektivitätsplanung.
    Das Bemessungs-Engineering verifiziert lediglich die Stufenwahl gegen
    max. Last, Inrush und minimalen Fehlerstrom, ersetzt aber keine Kurzschlussberechnung.

    ---
    **Masterarbeit:** Kevin Prochnow | HSU Hamburg, 2026
    """)

with tab_trafo:
    from tab_trafo import show as show_trafo
    show_trafo()

with tab_gen:
    from tab_gen import show as show_gen
    show_gen()

with tab_motor:
    from tab_motor import show as show_motor
    show_motor()

with tab_leitung:
    st.info("**Leitungsschutz (SIPROTEC 7SA6 / 7SD5)** — in Entwicklung")
    st.caption("Geplante Schutzfunktionen: 21, 67N, 50/51, 79")

with tab_sb:
    st.info("**Sammelschienenschutz (SIPROTEC 7SS52)** — in Entwicklung")
    st.caption("Geplante Schutzfunktionen: 87B, 50BF")
