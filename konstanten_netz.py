"""
konstanten_netz.py - Vorgaben fuer die netzweite Selektivitaetsplanung
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reines Python-Modul OHNE Streamlit.

Alle Werte in dieser Datei sind TOOL-VORGABEN, keine Werksvoreinstellungen
eines Geraets. Herleitung und Quellen: docs/tool_vorgabe_staffelabstand.md.
Die Einzelwerte sind dort als "gegen Handbuch pruefen" markiert, solange sie
nicht gegen die Technischen Daten der eingesetzten Geraete und Schalter
bestaetigt sind.
"""

# ── Staffelabstand fuer UMZ-Stufen numerischer Schutzgeraete ─────────────────
# Zusammensetzung: dt = t_LS + t_Rueck + 2 * t_Tol + t_Sich
# (Form nach ABB Distribution Automation Handbook, Abschnitt 8.2, Gl. 8.2.2)
dt_t_LS     = 0.080   # Ausschaltzeit Leistungsschalter inkl. Lichtbogenzeit   [s]
dt_t_Rueck  = 0.035   # Rueckfallzeit des oberen Schutzes. Groesster Wert der eingesetzten
                      # Geraete: 7UT613 ca. 35 ms (Hdb. Kap. 4.4), 7SJ66 und 7SA6 ca. 30 ms  [s]
dt_t_Tol    = 0.025   # Zeittoleranz je Geraet, geht fuer zwei Geraete ein     [s]
dt_t_Sich   = 0.020   # Sicherheitszuschlag, ca. eine Netzperiode bei 50 Hz    [s]
dt_Raster   = 0.050   # Einstellraster, auf das der Mindestwert aufgerundet wird [s]


def dt_summe() -> float:
    """Rechnerische Summe der Einzelanteile (ohne Rundung)."""
    return dt_t_LS + dt_t_Rueck + 2 * dt_t_Tol + dt_t_Sich


def _aufrunden(wert: float, raster: float) -> float:
    schritte = int(wert / raster + 1e-9)
    if schritte * raster < wert - 1e-9:
        schritte += 1
    return round(schritte * raster, 6)


# Technischer Mindestabstand: Summe der Einzelanteile, auf das Raster aufgerundet.
# Darunter ist Selektivitaet auch mit schnellen Schaltern nicht mehr gesichert.
dt_Staffel_min = _aufrunden(dt_summe(), dt_Raster)      # 0,185 s -> 0,20 s

# Soll-Staffelabstand (Tool-Vorgabe). Enthaelt gegenueber dem Mindestwert eine
# Reserve fuer Wandlersaettigung durch das Gleichstromglied und fuer langsamere
# Schalter. Gleicher Wert wie konstanten_trafo.dt_Staffel (ein Test prueft das).
dt_Staffel_soll = 0.30

# ── Zahlentoleranzen der Auswertung ──────────────────────────────────────────
EPS_ZEIT  = 1e-6      # Zeitvergleich: 0,8 - 0,5 ist in Gleitkomma nicht exakt 0,3  [s]
EPS_STROM = 1e-3      # Stromvergleich relativ: gleiche Ansprechwerte auf OS und US
                      # eines Trafos unterscheiden sich nach der Umrechnung nur
                      # durch die Rundung im Rechenkern (4 Nachkommastellen)

# ── AMZ-Kennlinien nach IEC 60255-151: t = T * k / ((I/Ip)^alpha - 1) ────────
# Schluessel sind die Kennliniennamen, wie sie die Rechenkerne liefern.
# Unbekannte Namen werden in der Staffelpruefung nicht bewertet und gemeldet.
AMZ_KENNLINIEN = {
    "Invers (IEC, normal inverse)": (0.14, 0.02),     # konstanten_motor.Kennlinie_51_def
    "Normal Invers (IEC)":          (0.14, 0.02),
    "Stark invers (IEC)":           (13.5, 1.0),
    "Extrem invers (IEC)":          (80.0, 2.0),
}
# Eine AMZ-Stufe regt erst oberhalb ihres Einstellwerts Ip an. Tool-Vorgabe 1,1 * Ip
# (uebliche Anregeschwelle numerischer Geraete, gegen 7SJ66 Techn. Daten pruefen).
AMZ_Anregefaktor = 1.10

# Zeittoleranz der AMZ-Kennlinien (Punkt 7, 17.11.2026). 7SJ66 Handbuch C53000-B1140-C383-D,
# Kap. 4.3 Technische Daten: Ausloesezeit fuer 2 <= I/Ip <= 20 "5 % of reference (calculated)
# value + 2 % current tolerance, or 30 ms". Tool-Vorgabe: gilt fuer alle AMZ-Stufen und den ganzen
# Strombereich, der groessere Wert zaehlt. Bei UMZ bleibt dt_t_Tol. Wo die AMZ-Toleranz ueber
# dt_t_Tol liegt, waechst der noetige Staffelabstand um die Differenz (je Geraet).
AMZ_Tol_rel   = 0.05    # Anteil der berechneten Ausloesezeit
AMZ_Tol_Strom = 0.02    # Stromtoleranz, wirkt ueber die Kennliniensteilheit auf die Zeit
AMZ_Tol_min_s = 0.030   # Mindestwert [s]
# Stuetzstellen je Pruefung, wenn eine AMZ-Stufe beteiligt ist (logarithmisch verteilt)
AMZ_Stuetzstellen = 60

# ── Staffelvorschlag ─────────────────────────────────────────────────────────
# Kleinste Verzoegerung, die der Vorschlag einer UMZ-Stufe gibt (Tool-Vorgabe).
# Entspricht der Werksvoreinstellung der Hochstromstufen (7UT613 Adr.2013,
# 7SA6 Adr.2611: 0,10 s) und haelt Einschaltvorgaenge und Wandler-Transienten fern.
t_Vorschlag_min = 0.10

# ── Stromstaffelung (I>>-Stufen) ─────────────────────────────────────────────
# Herleitung und Grenzen: docs/tool_vorgabe_stromstaffelung.md
# Sicherheitsfaktor der I>>-Stufe ueber dem Bezugsstrom. Gleicher Wert wie
# konstanten_trafo.k_S_IGG (Ausgangspunkt laut Aufgabe, ein Test prueft das).
k_S_Strom = 1.20
# Anlaufpruefung der I>-Stufen (Tool-Vorgabe 17.11.2026): der Ansprechwert jeder I>- und AMZ-Stufe im
# Pfad zu einem Motor soll ueber k * Anlaufstrom liegen. Gleicher Wert wie k_S_Strom. Das Handbuch
# nennt 1,6 nur fuer die 50-2-Stufe des Motors (7SJ66 Hdb. 2.2), fuer I> gibt es keine Herstellervorgabe.
k_Anlauf_Strom = 1.20
# Einstellraster des I>>-Faktors (x IN). Der Vorschlag wird auf dieses Raster
# AUFgerundet, nie abgerundet (ein zu kleiner Wert waere unselektiv).
Raster_Faktor = 0.01
# Empfindlichkeit der Reserve: Ik min hinter der naechsten Station muss
# mindestens gamma * Ansprechwert des oberen Schutzes betragen. Gleicher Wert
# wie konstanten_trafo.gamma_Ikmin und calc_leitung (ein Test prueft das).
gamma_Reserve = 1.50

# ── Umrechnung ueber Transformatoren (netz_umrechnung.py) ────────────────────
# Zweipoliger Fehler hinter einer Wicklungsgruppe mit D<->Y-Wechsel: der groesste
# Strangstrom auf der anderen Seite ist 2/sqrt(3) * Ik2 / ue (Ik2 = zweipoliger
# Fehlerstrom). Das ist exakt der Wert des dreipoligen Fehlers, wenn
# Ik2 = sqrt(3)/2 * Ik3 gilt. Herleitung in docs/tool_vorgabe_stromstaffelung.md.
f_Sg_2pol_DY = 2.0 / 3.0 ** 0.5

# Groesster Faktor (x IN), den der Vorschlag einer I>>-Stufe gibt. Tool-Vorgabe: der
# Reglerbereich des jeweiligen Betriebsmittel-Tabs (tab_leitung.py: Iph>> 0,5 bis 10,
# tab_trafo.py: I>> US 4 bis 12). Fuer I>> OS des Trafos gibt es keine Grenze, weil die
# Automatik im Trafo-Tab selbst ueber den Reglerbereich hinausgeht (z. B. 18,19 x IN bei T2
# im Referenznetz). Der Einstellbereich des Geraets in Sekundaerampere ist damit nicht
# geprueft (Pruefpunkt in docs/tool_vorgabe_stromstaffelung.md). Liegt der noetige Wert
# darueber, bleibt die Stufe unveraendert und wird wie eine Zeitstufe gestaffelt.
Faktor_max = {
    ("trafo", "I>> US"): 12.0,
    ("leitung", "Iph>>"): 10.0,
}

# ── Kurzschlussstromberechnung (netz_kurzschluss.py) ─────────────────────────
# Vereinfachte Rechnung in Anlehnung an IEC 60909-0. Die Werte sind am 16.11.2026 gegen
# Sekundaerquellen geprueft (Lehrbuch, Fachaufsatz, Datenblatt), der Normtext selbst lag
# nicht vor. Quellen und offene Punkte: docs/tool_vorgabe_kurzschluss.md, Abschnitt 8.
# Spannungsfaktor c am Fehlerort, getrennt nach Spannungsebene (Grenze 1 kV).
c_max_HS = 1.10       # UN > 1 kV, groesster Kurzschlussstrom
c_min_HS = 1.00       # UN > 1 kV, kleinster Kurzschlussstrom
c_max_NS = 1.10       # UN <= 1 kV, Netze mit 10 % Spannungstoleranz (400/230 V).
                      # Fuer Netze mit +6 % Toleranz nennt die Norm 1,05.
c_min_NS = 0.90       # UN <= 1 kV, passend zu 10 % Toleranz (Ausgabe 2016). Bei 6 %
                      # Toleranz und in der Ausgabe 2001 steht 0,95.
U_Grenze_NS_kV = 1.0

# Netzeinspeisung: ohne Angabe RX_Q im Element gilt R_Q = RX_Q_def * X_Q
RX_Q_def = 0.10

# Korrekturfaktor fuer Netztransformatoren: K_T = 0,95 * c_max / (1 + 0,6 * x_T).
# False rechnet ohne K_T (so sind die Handwerte des Referenznetzes entstanden).
KT_anwenden = True
KT_a, KT_b = 0.95, 0.60
# K_T nur beim groessten Kurzschlussstrom (IEC 60909-0:2016, Abschnitt 6.3.3, Normstelle nach
# pandapower 3.5, Funktion _transformer_correction_factor; Normtext nicht gelesen). Beim kleinsten
# Strom ohne K_T: hoehere Impedanz, kleinerer Ik min, also auf der sicheren Seite fuer die
# Empfindlichkeit. Entscheidung 17.11.2026 nach Gegenrechnung mit pandapower.
KT_bei_min = False

# Leitung: der Widerstandsbelag aus den Elementdaten gilt als Wert bei 20 Grad C.
# Fuer Ik min wird er auf die Leitertemperatur am Ende des Kurzschlusses umgerechnet:
# R = R20 * (1 + alpha * (theta - 20)). Die Norm verlangt die Leitertemperatur am Ende
# des Kurzschlusses. Tool-Vorgabe 90 Grad C: hoechste zulaessige Betriebstemperatur von
# VPE-Kabeln (Datenblaetter NA2XS(F)2Y). Das ist die untere Grenze fuer ein vorbelastetes
# Kabel, die Kurzschlusserwaermung selbst (zulaessig bis 250 Grad C) ist nicht enthalten.
# Je Leitung ueber den Parameter theta_min_C aenderbar.
alpha_Leiter_1K = 0.004
# Anfangstemperatur des Leiters vor dem Kurzschluss (hoechste zulaessige Betriebstemperatur
# VPE). Ab 25.11.2026 Startwert der adiabatischen Erwaermung, nicht mehr die Endtemperatur.
theta_Leiter_min_C = 90.0

# Endtemperatur am Ende des Kurzschlusses (DIN EN 60909-0:2016-12, 7.1.2 Punkt 7, Gl. (32),
# geprueft am 25.11.2026): adiabatische Erwaermung nach IEC 60949 (Normtext nicht gelesen,
# Pruefpunkt in docs/tool_vorgabe_kurzschluss.md):
#   theta_e = (theta_i + beta) * exp(I^2 * t / (K^2 * S^2)) - beta
# I: Ik2 min bei einem Fehler am Ende der Leitung (groesster Strom, den die Leitung bei Ik min
# fuehrt, also sichere Seite), t: Kurzschlussdauer, S: Leiterquerschnitt.
# Werte je Leitermaterial: K in A*s^0,5/mm^2, beta in K, spez. Widerstand bei 20 Grad C in
# Ohm*mm^2/m (DIN EN 60909-0, 6.4: Cu 1/54, Al 1/34). Ohne Querschnitt A_mm2 wird er aus
# R' und dem spezifischen Widerstand abgeleitet.
LEITER = {
    "Al": {"K": 148.0, "beta": 228.0, "rho": 1.0 / 34.0},
    "Cu": {"K": 226.0, "beta": 234.5, "rho": 1.0 / 54.0},
}
Leitermaterial_def = "Al"          # Tool-Vorgabe: NA2XS(F)2Y, Aluminium
# Kurzschlussdauer fuer Ik min: Tool-Vorgabe 1,0 s (Abschaltung ueber eine verzoegerte
# Stufe bzw. den Reserveschutz). Je Leitung ueber t_KS_s aenderbar.
t_KS_Ikmin_s = 1.0
# Hoechste zulaessige Kurzschlusstemperatur VPE (Datenblatt): darueber Warnung, Rechnung
# mit diesem Wert begrenzt.
theta_KS_max_C = 250.0
# Iteration Strom <-> Widerstand
theta_Iter_max = 20
theta_Iter_tol_K = 0.1

# Motoren beim groessten Strom (DIN EN 60909-0:2016-12, 7.1.2 e) und 7.1.3, geprueft am
# 25.11.2026): Ik max enthaelt die Motorbeitraege. Ausnahme: Motoren, die nach Art der
# Schaltung (Verriegelung) oder Prozessfuehrung nicht gleichzeitig laufen. Schalter am Motor:
KS_BEITRAG_OPTIONEN = ("Ja", "Nein: läuft nicht gleichzeitig (Verriegelung)")

# Asynchronmotor: R_M/X_M ohne Angabe RX_M im Element. Die Norm staffelt nach
# Leistung je Polpaar (ueber 1 kV: 0,10 ab 1 MW je Polpaar, sonst 0,15. Bis 1 kV: 0,42).
# Das Netzmodell kennt die Polpaarzahl nicht. Tool-Vorgabe ueber 1 kV: 0,10.
RX_M_HS = 0.10
RX_M_NS = 0.42

# Zweipoliger Kurzschluss fern von Generatoren (Z2 = Z1): Ik2 = sqrt(3)/2 * Ik3
f_2pol = 3.0 ** 0.5 / 2.0

# Anzeige: ab dieser Abweichung zwischen eingegebenem und berechnetem Ik weist die
# Oberflaeche darauf hin (Tool-Vorgabe, halbe Sicherheit von k_S_Strom = 1,2)
Ik_Abweichung_Hinweis = 0.10

# ── Erdfehler: Nullsystem und einpoliger Kurzschluss (netz_kurzschluss.py) ───
# Einpoliger Fehler (Erdkurzschluss) nach dem Verfahren der symmetrischen Komponenten:
#   Ik1 = 3 * c * UN / sqrt(3) / |Z1 + Z2 + Z0|, mit Z2 = Z1 (generatorfern).
# Herleitung, Annahmen und offene Pruefpunkte in docs/tool_vorgabe_erdfehler.md.
#
# Transformator, Nullimpedanz der Wicklung mit herausgefuehrtem Sternpunkt, wenn die andere
# Seite ein Dreieck ist (Dyn, YNd, ...): Z0T = Z0_Z1_Trafo * Z1T. Tool-Vorgabe 1,0 (gleicher
# Wert wie Z1T, uebliche Naeherung bei Dreischenkel-Trafos mit Dreieckwicklung). Der Faktor
# K_T gilt beim groessten Strom auch fuer Z0T.
Z0_Z1_Trafo = 1.0

# Netzeinspeisung an einem starr geerdeten Knoten: Z0Q = X0_X1_Q_def * Z1Q, wenn das Element
# keinen eigenen Wert X0_X1_Q hat. Tool-Vorgabe 1,0 (dann ist Ik1 = Ik3 am Uebergabepunkt).
# Fuer ein echtes Netz kommt der Wert vom Netzbetreiber (Ik1'' am Uebergabepunkt).
X0_X1_Q_def = 1.0

# Leitung ohne eigene Nullsystembelaege R0_Belag / X0_Belag: Nullimpedanz aus den
# Erdimpedanz-Faktoren der Leitung (RE/RL, XE/XL, dieselben Werte wie beim Distanzschutz):
#   R0' = R1' * (1 + 3 * RE/RL),  X0' = X1' * (1 + 3 * XE/XL)
# Ohne Angabe gelten die Werksvoreinstellungen aus konstanten_leitung (RE_RL_def, XE_XL_def).

# Erdfehlerstrom-Begrenzung am Knoten (niederohmige Sternpunkterdung):
#   R_E = UN / (sqrt(3) * I_E_begr). Die Impedanz eines Sternpunktbildners selbst ist nicht
#   enthalten (Tool-Vorgabe, gegenueber 3 * R_E klein). Liegt am Knoten ein Trafo mit
#   herausgefuehrtem Sternpunkt, gilt die Erdung an dessen Sternpunkt: Z0 = Z0T + 3 * R_E.
I_E_begr_Bereich_A = (1.0, 100000.0)
