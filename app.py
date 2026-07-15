"""
app.py — Hauptdatei des Schutz-Engineering-Tools
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg
Starten mit: streamlit run app.py
"""

import streamlit as st

# Tab-Module in der Schreibweise "import modul" einbinden (wichtig fuer die
# EXE-Erstellung: der Import-Scanner von streamlit-desktop-app versteht nur
# diese Form korrekt; "from X import Y" erzeugt den kaputten Namen "X.Y").
import tab_trafo
import tab_gen
import tab_motor
import tab_leitung
import tab_sb

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
        MS-Industrienetze inkl. 110-kV-Netzanbindung · Sternpunkt isoliert, kompensiert oder geerdet<br>
        Methodik: SIPROTEC 7UT6xx / 7UM62 / 7SJ66 / 7SA6xx / 7SD5xxx / 7SS52xx<br>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Tab-Navigation (Info zuerst, dann Betriebsmittel) ─────────────────────────
tab_info, tab_trafo_ui, tab_gen_ui, tab_motor_ui, tab_leitung_ui, tab_sb_ui = st.tabs([
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
    in industriellen Mittelspannungsnetzen und deren 110-kV-Netzanbindung. Die
    Berechnungsmethodik folgt den Einstellhinweisen der SIPROTEC-Gerätefamilie (Siemens)
    als Referenz.

    **Norm-Grundlagen:** IEC 60255-151 (Überstromzeitschutz), IEC 60255-187-1 (Differentialschutz),
    DIN EN 60909-0 (Kurzschlussströme), IEC 60034-1 (drehende Maschinen), VDE-FNN-Leitfaden

    #### Arbeitsablauf
    1. **Betriebsmittel-Tab wählen** (Transformator, Generator, Motor, Leitung oder Sammelschiene).
    2. **Eingaben ausfüllen:** Grunddaten, Stromwandler und Netzparameter. Die erweiterten
       Parameter sind mit Voreinstellungen belegt und nur bei Bedarf anzupassen.
    3. **Plausibilitätsprüfung abarbeiten:** Die Ampel zeigt je Prüfung den Status, die Box
       „Handlungsbedarf“ nennt bei 🔴 den konkreten Regler und den Zielwert.
    4. **Sollwert-Tabelle übertragen:** Die herstellerneutrale Sollwert-Tabelle am Ende jeder
       Seite enthält alle Einstellwerte mit DIGSI-Adressen für die Parametrierung.

    #### Aufbau jeder Betriebsmittel-Seite (einheitliches Schema)
    - Eingaben (Grunddaten, Stromwandler primär/sekundär, Netzparameter)
    - Erweiterte Parameter (gerätespezifische Voreinstellungen, frei änderbar)
    - Berechnete Grundgrößen (Nennströme, Übersetzung, Wandlerverhältnisse, Bezugsstrom)
    - Schutzfunktionen des Betriebsmittels (Haupt- und Reserveschutz)
    - Plausibilitätsprüfung (Ampel) mit konkreten Korrektur-Anweisungen
    - Geräte-/Architektur-Empfehlung
    - Herstellerneutrale Sollwert-Tabelle mit DIGSI-Adressen

    Die konkreten Schutzfunktionen unterscheiden sich je Betriebsmittel, etwa
    Differentialschutz 87T beim Transformator, Distanzschutz 21 bei der Leitung oder
    Sammelschienen-Differentialschutz 87B bei der Sammelschiene.

    **Ampel-Legende:** 🟢 OK · 🟡 Hinweis (Wert plausibel, aber prüfen) ·
    🔴 Prüfen! (konkrete Korrektur erforderlich) · ⚫ Fehlt (Pflichtangabe nicht ausgefüllt) ·
    ▫️ nicht anwendbar bzw. keine Empfehlung hinterlegt

    #### Herstellerneutralität
    Alle Ansprechwerte werden als bezogene Größen geführt (x IN, x Ino, p.u.) und zusätzlich
    primär und sekundär in Ampere ausgewiesen. Damit sind die Sollwerte auf jedes Schutzgerät
    übertragbar. Die DIGSI-Adressen der SIPROTEC-Leitgeräte dienen als Referenzumsetzung für
    die direkte Parametrierung. Die Übertragung auf Geräte anderer Hersteller (ABB, Schneider
    Electric) behandeln die Vergleichstabellen der begleitenden Masterarbeit.

    #### Voreinstellungen und Tool-Vorgaben
    Die erweiterten Parameter sind mit den Werksvoreinstellungen der Leitgeräte vorbelegt.
    Wo eine anlagenbezogene Ableitung fachlich besser ist (z. B. I-DIFF>> aus 1,2/uk beim
    Transformator statt pauschal 7,5), ist der Wert als **Tool-Vorgabe** gekennzeichnet und
    die Werksvoreinstellung daneben angegeben.

    #### Hinweise zu Eingaben und Einheiten
    **Dezimaltrennzeichen:** Bei der **Eingabe** verwendet Streamlit den **Punkt** als
    Dezimaltrennzeichen (englische Locale). Die Eingabe `16.5` entspricht also 16,5 MVA.
    Alle **berechneten Ausgaben** (Metriken, Tabellen, Sollwerte) werden dagegen mit
    deutschem **Komma** dargestellt.

    **Thermische Zeitkonstante τ (ANSI 49):**
    Die Einheit hängt vom Schutzgerät ab und ist im jeweiligen Tab angegeben:
    - **Transformator (7UT613):** τ in **Minuten** (Adr. 4203)
    - **Generator (7UM62):** τ in **Sekunden** (Adr. 1603)
    - **Motor (7SJ66):** τ in **Minuten** (Adr. 4203)
    - **Leitung (7SA6 / 7SD5):** τ in **Minuten** (Adr. 4203)

    Die Sammelschiene (7SS52) besitzt keinen thermischen Überlastschutz 49.
    Die Verwechslung von Minuten und Sekunden ist eine häufige Fehlerquelle.

    #### Validierung
    Der Berechnungskern ist gegen das durchgerechnete Zahlenbeispiel in Kapitel 2.4 des
    7UT613-Handbuchs validiert. Dabei wurde ein Druckfehler des Handbuchs identifiziert und
    dokumentiert (0,8 statt korrekt 8,0 · I_N), was die unabhängige Nachrechnung des Tools
    belegt. Referenzfall und Rechenweg sind in der begleitenden Masterarbeit dokumentiert.

    #### Grenzen des Tools
    - **Keine netzweite Selektivitätsplanung:** Das Tool berechnet komponentenbezogene
      Parameter. Das Bemessungs-Engineering verifiziert die Stufenwahl gegen maximale Last,
      Einschaltstromstoß und minimalen Fehlerstrom, ersetzt aber keine Staffelplanung über
      mehrere Netzebenen.
    - **Keine Kurzschlussstromberechnung:** Ik″max und Ik,min sind Eingaben und stammen aus
      einer Berechnung nach DIN EN 60909-0.
    - **Keine Stromwandler-Dimensionierung:** Bebürdung und Sättigungsverhalten der Wandler
      sind separat nachzuweisen. Das Tool prüft lediglich den Anpassungsfaktor
      (Soll 0,5 bis 2,0).

    ---
    **Masterarbeit:** Kevin Prochnow | HSU Hamburg, 2026
    """)

with tab_trafo_ui:
    tab_trafo.show()

with tab_gen_ui:
    tab_gen.show()

with tab_motor_ui:
    tab_motor.show()

with tab_leitung_ui:
    tab_leitung.show()

with tab_sb_ui:
    tab_sb.show()
