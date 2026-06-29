"""
konstanten_leitung.py — Voreinstellungen, Adressen und Plausibilitaets-Schwellwerte (Leitung)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Single Source of Truth fuer alle SIPROTEC-Werksvoreinstellungen, Engineering-Margen
und Plausibilitaetsgrenzen des Leitungs-Tabs. Alle Werte sind frei aenderbar.

Zwei Leitgeraete werden abgebildet:
  - Distanzschutz 7SA6      (C53000-G1100-C156-9, ab V4.74)
  - Leitungsdifferential 7SD5 (Leitungsdifferentialschutz mit Distanzschutz, V4.7)

Die beiden Geraete fuehren dieselben Logikfunktionen unter teils unterschiedlichen
DIGSI-Adressen. Die Anlagendaten (Leitungsdaten, Erdimpedanzanpassung) sind in beiden
Geraeten adressgleich, die Distanzzonen divergieren systematisch (7SA6 13xx, 7SD5 16xx).
Die Funktion ADR(...) liefert geraeteabhaengig die korrekte Adresse.

Quellen: SIPROTEC 7SA6 Handbuch C53000-G1100-C156-9, SIPROTEC 7SD5 Handbuch,
         IEC 60255-121 (Distanzschutz), IEC 60255-151, VDE-FNN-Leitfaden.

Hinweis: Alle Adressen wurden gegen die im Projekt liegenden Geraetehandbuecher
verifiziert (Inline-Adressangaben der Einstellhinweise).
"""

# ═════════════════════════════════════════════════════════════════════════════
# AUSWAHL-OPTIONEN
# ═════════════════════════════════════════════════════════════════════════════

LEITGERAET_OPTIONEN = [
    "Distanzschutz 7SA6",
    "Leitungsdifferential 7SD5",
]
# Kurz-Keys fuer die Adressauswahl
LEITGERAET_KEY = {
    "Distanzschutz 7SA6":        "7SA6",
    "Leitungsdifferential 7SD5": "7SD5",
}

LEITUNGSART_OPTIONEN = ["Freileitung", "Kabel", "Freileitung-Kabel-Mischstrecke"]

# Mindestlaenge fuer den sinnvollen Einsatz des Distanzschutzes (streckenartabhaengig).
# Unterhalb gilt die Strecke als "kurz": die Distanzmessung reagiert wegen der kleinen
# Leitungsimpedanz empfindlich auf Mess- und Wandlerfehler, der Z1-Reach wird sehr klein.
# Quelle: Anwendungstabelle 7SD5-Handbuch (nach Ziegler, Digitaler Distanzschutz):
# kurze Kabelstrecken ca. 0,5 ... 3 km, kurze Freileitungsstrecken < 10 km.
L_MIN_DISTANZ_KM = {
    "Kabel":                          3.0,   # darunter: kurze Kabelstrecke
    "Freileitung":                    10.0,  # darunter: kurze Freileitungsstrecke
    "Freileitung-Kabel-Mischstrecke": 10.0,  # konservativ wie Freileitung
}
L_MIN_DISTANZ_DEFAULT_KM = 10.0
# Empfohlenes R/X-Verhaeltnis der Zoneneinstellung bei kurzen Strecken (gleiche Quelle)
RX_KURZ_EMPFEHLUNG = {"Kabel": "3 bis 5", "Freileitung": "2 bis 5",
                      "Freileitung-Kabel-Mischstrecke": "2 bis 5"}

STERNPUNKT_NETZ_OPTIONEN = [
    "Niederohmig geerdet",
    "Starr geerdet",
    "Isoliert",
    "Kompensiert (Petersen)",
]
# Netze, in denen der gerichtete Erdkurzschlussschutz fuer geerdete Netze (67N)
# und die Erdfehlererfassung des Distanzschutzes sinnvoll sind:
NETZ_GEERDET = ["Niederohmig geerdet", "Starr geerdet"]

# Format der Erdimpedanzanpassung (Adr. 237, in beiden Geraeten identisch)
ERDIMP_FORMAT_OPTIONEN = [
    "RE/RL, XE/XL (skalar)",
    "K0 (Betrag/Winkel)",
]

# Ausloesecharakteristik Distanzschutz (Adr. 115)
DIS_CHARAKT_OPTIONEN = ["Polygon", "Kreis (MHO)"]

# Anregeverfahren Distanzschutz (Adr. 114)
DIS_ANR_OPTIONEN = ["IMPEDANZ", "I-ANR.", "U-I-ANR.", "U-I-φ-ANR"]

# Richtung/Wirksamkeit der Staffelzonen (MODUS Z2 ... Z6)
# Belegt: "rueckwaerts, vorwaerts oder ungerichtet" (7SA6 Hdb. 2.2.1); "Unwirksam" deaktiviert.
ZONE_MODUS_OPTIONEN = ["Unwirksam", "Vorwärts", "Rückwärts", "Ungerichtet"]

# 87L Leitungsdifferentialschutz (nur 7SD5)
IC_KOMP_OPTIONEN = ["Aus", "Ein"]                       # Ladestromkompensation (Adr.1221)
WS_VERBINDUNG_OPTIONEN = [                               # Wirkschnittstelle (Adr.4502)
    "LWL direkt", "Kommunikationsumsetzer", "LWL über Lichtwellenleiter-Modul",
]
ANZAHL_GERAETE_OPTIONEN = [2, 3]                         # Messstellen / Leitungsenden (Adr.147)

# 85 Signaluebertragungsverfahren Distanzschutz (Teleschutz, Adr.2101)
SIGNALV_OPTIONEN = [
    "Aus", "Mitnahme", "Signalvergleich", "Blocking", "Unblocking",
]
ANSCHLUSS_OPTIONEN = ["1 Gegenende (Zweienden)", "2 Gegenenden (Dreienden)"]

# 50/51 Not-Ueberstromzeitschutz (Betriebsart Adr.2601)
UEBS_BETRIEBSART_OPTIONEN = ["Aus", "Ein: immer aktiv", "Ein: bei U-Ausfall"]

# 79 Wiedereinschaltautomatik (Anzahl Unterbrechungszyklen)
AWE_ANZAHL_OPTIONEN = [1, 2, 3, 4]

# Allgemeine Ja/Nein-Auswahl
JN_OPTIONEN = ["Nein", "Ja"]

# 68/78 Pendelerfassung (Funktionsumfang Adr.120)
PENDELERFASSUNG_OPTIONEN = ["Vorhanden", "Nicht vorhanden"]


# ═════════════════════════════════════════════════════════════════════════════
# DIGSI-ADRESSEN (geraeteabhaengig)
# Jede Logikgroesse ist mit der Adresse fuer 7SA6 UND 7SD5 hinterlegt.
# Verifiziert gegen die Inline-Adressangaben beider Handbuecher.
# ═════════════════════════════════════════════════════════════════════════════

ADR = {
    # ── Anlagendaten / Leitungsdaten (in beiden Geraeten adressgleich) ──────
    "LAENGENEINHEIT":   {"7SA6": "236",  "7SD5": "236"},   # km / Meilen
    "FORMAT_ERDIMP":    {"7SA6": "237",  "7SD5": "237"},   # RE/RL,XE/XL <-> K0
    "EF_1POLIG":        {"7SA6": "238",  "7SD5": "238"},   # separate 1-pol. Erdfehler-Einst.
    "T_LS_EIN":         {"7SA6": "239",  "7SD5": "239"},   # LS-Einschaltzeit
    "PHI_LTG":          {"7SA6": "1105", "7SD5": "1105"},  # Leitungswinkel
    "X_BELAG":          {"7SA6": "1110", "7SD5": "1110"},  # Reaktanzbelag [Ohm/km]
    "LTGS_LAENGE":      {"7SA6": "1111", "7SD5": "1111"},  # Leitungslaenge [km]
    "C_BELAG":          {"7SA6": "1114", "7SD5": "1114"},  # Kapazitaetsbelag [uF/km]
    # Erdimpedanzanpassung skalar (Gruppe Z1 und Gruppe > Z1)
    "RE_RL_Z1":         {"7SA6": "1116", "7SD5": "1116"},
    "XE_XL_Z1":         {"7SA6": "1117", "7SD5": "1117"},
    "RE_RL_GZ1":        {"7SA6": "1118", "7SD5": "1118"},  # RE/RL (> Z1)
    "XE_XL_GZ1":        {"7SA6": "1119", "7SD5": "1119"},  # XE/XL (> Z1)
    # Erdimpedanzanpassung komplex K0 (Betrag/Winkel)
    "K0_Z1":            {"7SA6": "1120", "7SD5": "1120"},
    "PHI_K0_Z1":        {"7SA6": "1121", "7SD5": "1121"},
    "K0_GZ1":           {"7SA6": "1122", "7SD5": "1122"},  # K0 (> Z1)
    "PHI_K0_GZ1":       {"7SA6": "1123", "7SD5": "1123"},  # PHI K0 (> Z1)

    # ── Distanzschutz allgemein ─────────────────────────────────────────────
    "DIS_ANR":          {"7SA6": "114",  "7SD5": "114"},   # Anregeverfahren
    "DIS_CHARAKT":      {"7SA6": "115",  "7SD5": "115"},   # Polygon / Kreis

    # ── Distanzzonen polygonal — 7SA6 13xx / 7SD5 16xx (Offset +300) ────────
    "MODUS_Z1":         {"7SA6": "1301", "7SD5": "1601"},
    "R_Z1":             {"7SA6": "1302", "7SD5": "1602"},
    "X_Z1":             {"7SA6": "1303", "7SD5": "1603"},
    "RE_Z1":            {"7SA6": "1304", "7SD5": "1604"},
    "T1_1POL":          {"7SA6": "1305", "7SD5": "1605"},
    "T1_MEHRPOL":       {"7SA6": "1306", "7SD5": "1606"},
    "ALPHA_POLYG":      {"7SA6": "1307", "7SD5": "1607"},

    "MODUS_Z1B":        {"7SA6": "1351", "7SD5": "1651"},
    "R_Z1B":            {"7SA6": "1352", "7SD5": "1652"},   # Uebergreifzone (R vor X)
    "X_Z1B":            {"7SA6": "1353", "7SD5": "1653"},
    "RE_Z1B":           {"7SA6": "1354", "7SD5": "1654"},
    "T1B_1POL":         {"7SA6": "1355", "7SD5": "1655"},
    "T1B_MEHRPOL":      {"7SA6": "1356", "7SD5": "1656"},

    "MODUS_Z2":         {"7SA6": "1311", "7SD5": "1611"},
    "R_Z2":             {"7SA6": "1312", "7SD5": "1612"},
    "X_Z2":             {"7SA6": "1313", "7SD5": "1613"},
    "RE_Z2":            {"7SA6": "1314", "7SD5": "1614"},
    "T2_1POL":          {"7SA6": "1315", "7SD5": "1615"},
    "T2_MEHRPOL":       {"7SA6": "1316", "7SD5": "1616"},

    "MODUS_Z3":         {"7SA6": "1321", "7SD5": "1621"},
    "R_Z3":             {"7SA6": "1322", "7SD5": "1622"},
    "X_Z3":             {"7SA6": "1323", "7SD5": "1623"},
    "RE_Z3":            {"7SA6": "1324", "7SD5": "1624"},
    "T3":               {"7SA6": "1325", "7SD5": "1625"},

    "MODUS_Z4":         {"7SA6": "1331", "7SD5": "1631"},
    "R_Z4":             {"7SA6": "1332", "7SD5": "1632"},
    "X_Z4":             {"7SA6": "1333", "7SD5": "1633"},
    "RE_Z4":            {"7SA6": "1334", "7SD5": "1634"},
    "T4":               {"7SA6": "1335", "7SD5": "1635"},

    "MODUS_Z5":         {"7SA6": "1341", "7SD5": "1641"},
    "R_Z5":             {"7SA6": "1342", "7SD5": "1642"},
    "X_Z5_VOR":         {"7SA6": "1343", "7SD5": "1643"},   # Vorwaertsrichtung
    "RE_Z5":            {"7SA6": "1344", "7SD5": "1644"},
    "T5":               {"7SA6": "1345", "7SD5": "1645"},
    "X_Z5_RUECK":       {"7SA6": "1346", "7SD5": "1646"},   # Rueckwaertsrichtung

    "MODUS_Z6":         {"7SA6": "1361", "7SD5": "1661"},
    "R_Z6":             {"7SA6": "1362", "7SD5": "1662"},
    "X_Z6_VOR":         {"7SA6": "1363", "7SD5": "1663"},   # Vorwaertsrichtung
    "RE_Z6":            {"7SA6": "1364", "7SD5": "1664"},
    "T6":               {"7SA6": "1365", "7SD5": "1665"},
    "X_Z6_RUECK":       {"7SA6": "1366", "7SD5": "1666"},   # Rueckwaertsrichtung

    # ── 87L Leitungslaengsdifferentialschutz — nur 7SD5 ─────────────────────
    "DIFF_SCHUTZ":      {"7SA6": "—", "7SD5": "1201"},   # Funktionsumfang Ein/Aus
    "I_DIFF":           {"7SA6": "—", "7SD5": "1210"},   # I-DIFF> Ansprechwert Diffstufe
    "I_DIF_ZUSCH":      {"7SA6": "—", "7SD5": "1213"},   # I-DIF> ZUSCH. (Zuschalterkennung)
    "T_I_DIF":          {"7SA6": "—", "7SD5": "1217"},   # T-I-DIF> Ausloeseverzoegerung (1217A)
    "I_FREIG_DIFF":     {"7SA6": "—", "7SD5": "1219"},   # I> FREIG. DIFF (1219A)
    "IC_KOMP":          {"7SA6": "—", "7SD5": "1221"},   # Ladestromkompensation Ein/Aus
    "ICSTAB_ICN":       {"7SA6": "—", "7SD5": "1224"},   # IcSTAB/IcN Stabilisierungsfaktor
    "I_DIFF_HH":        {"7SA6": "—", "7SD5": "1233"},   # I-DIFF>> Ladungsvergleichs-/Hochstromstufe
    "I_DIF_HH_ZUSCH":   {"7SA6": "—", "7SD5": "1235"},   # I-DIF>> ZUSCH.
    # Wirkschnittstelle / Schutzdatentopologie
    "ANZAHL_GERAETE":   {"7SA6": "—", "7SD5": "147"},    # Anzahl Geraete an den Messstellen
    "WS1":              {"7SA6": "—", "7SD5": "145"},    # Wirkschnittstelle 1 vorhanden
    "WS2":              {"7SA6": "—", "7SD5": "146"},    # Wirkschnittstelle 2 vorhanden
    "WS1_EIN":          {"7SA6": "—", "7SD5": "4501"},   # WS1 Ein/Aus
    "WS1_VERB":         {"7SA6": "—", "7SD5": "4502"},   # WS1 Verbindung (LWL direkt etc.)
    "GPS_SYNC":         {"7SA6": "—", "7SD5": "4801"},   # GPS-Synchronisierung

    # ── 67N Gerichteter Erdkurzschlussschutz — in beiden Geraeten adressgleich ──
    "ERDFEHLER":        {"7SA6": "3101", "7SD5": "3101"},  # Funktionsumfang Ein/Aus
    "I3I0_IPH_STAB":    {"7SA6": "3104", "7SD5": "3104"},  # 3I0 IPH STAB (Stabilisierung)
    "I3I0_SIGZUS":      {"7SA6": "3105", "7SD5": "3105"},  # 3I0> SIG.ZUS.
    "MODUS_3I0HHH":     {"7SA6": "3110", "7SD5": "3110"},  # MODUS 3I0>>>
    "I3I0_HHH":         {"7SA6": "3111", "7SD5": "3111"},  # 3I0>>> Ansprechwert
    "T_3I0HHH":         {"7SA6": "3112", "7SD5": "3112"},  # T 3I0>>>
    "MODUS_3I0HH":      {"7SA6": "3120", "7SD5": "3120"},  # MODUS 3I0>>
    "I3I0_HH":          {"7SA6": "3121", "7SD5": "3121"},  # 3I0>> Ansprechwert
    "T_3I0HH":          {"7SA6": "3122", "7SD5": "3122"},  # T 3I0>>
    "MODUS_3I0H":       {"7SA6": "3130", "7SD5": "3130"},  # MODUS 3I0>
    "I3I0_H":           {"7SA6": "3131", "7SD5": "3131"},  # 3I0> Ansprechwert
    "T_3I0H":           {"7SA6": "3132", "7SD5": "3132"},  # T 3I0>
    "MODUS_3I0P":       {"7SA6": "3140", "7SD5": "3140"},  # MODUS 3I0P (AMZ)
    "I3I0P":            {"7SA6": "3141", "7SD5": "3141"},  # 3I0P Ansprechwert (AMZ)
    "T_3I0P":           {"7SA6": "3143", "7SD5": "3143"},  # T 3I0P (Zeitmultiplikator)
    "PHI_KOMP":         {"7SA6": "3168", "7SD5": "3168"},  # PHI KOMP Richtungswinkel

    # ── 85 Signaluebertragungsverfahren Distanzschutz (Teleschutz, beide Geraete) ──
    "SIGNALZUSATZ_DIS": {"7SA6": "2101", "7SD5": "2101"},  # Verfahren (Aus/Mitnahme/...)
    "ANSCHLUSS_DIS":    {"7SA6": "2102", "7SD5": "2102"},  # 1 oder 2 Gegenenden
    "T_SENDVERL":       {"7SA6": "2103", "7SD5": "2103"},  # Sendesignalverlaengerung
    "TV_DIS":           {"7SA6": "2108", "7SD5": "2108"},  # Freigabeverzoegerung Z1B
    "T_WARTE_RUECKW":   {"7SA6": "2109", "7SD5": "2109"},  # Wartezeit vor transienter Blockierung
    "T_TRANSBLOCK":     {"7SA6": "2110", "7SD5": "2110"},  # Transiente Blockierzeit
    "DIS_EMPF_MERKEN":  {"7SA6": "2113", "7SD5": "2113"},  # Empfangssignal merken

    # ── 50/51 Not-Ueberstromzeitschutz — beide Geraete adressgleich (26xx) ──────
    "UEBS_BETRIEBSART": {"7SA6": "2601", "7SD5": "2601"},  # Betriebsart (Aus/immer/U-Ausfall)
    "IPH_HH":           {"7SA6": "2610", "7SD5": "2610"},  # Iph>> Ansprechwert
    "T_IPH_HH":         {"7SA6": "2611", "7SD5": "2611"},  # T Iph>>
    "I3I0_HH_UEBS":     {"7SA6": "2612", "7SD5": "2612"},  # 3I0>>
    "T_3I0HH_UEBS":     {"7SA6": "2613", "7SD5": "2613"},  # T 3I0>>
    "IPH_H":            {"7SA6": "2620", "7SD5": "2620"},  # Iph> Ansprechwert
    "T_IPH_H":          {"7SA6": "2621", "7SD5": "2621"},  # T Iph>
    "I3I0_H_UEBS":      {"7SA6": "2622", "7SD5": "2622"},  # 3I0>
    "T_3I0H_UEBS":      {"7SA6": "2623", "7SD5": "2623"},  # T 3I0>
    "IPH_P":            {"7SA6": "2640", "7SD5": "2640"},  # IP (AMZ) Ansprechwert
    "T_IPH_P":          {"7SA6": "2642", "7SD5": "2642"},  # T IP (Zeitmultiplikator IEC)

    # ── 79 Wiedereinschaltautomatik (AWE) — beide Geraete adressgleich (34xx) ──
    "AUTO_WE":          {"7SA6": "3401", "7SD5": "3401"},  # AUTO-WE Ein/Aus
    "T_SPERRZEIT":      {"7SA6": "3403", "7SD5": "3403"},  # Sperrzeit (Reclaim)
    "T_LS_UEBERW":      {"7SA6": "3409", "7SD5": "3409"},  # LS-Ueberwachungszeit
    "WE_TP_AUS1POL":    {"7SA6": "3456", "7SD5": "3456"},  # 1.WE TP nach 1-pol. AUS (Pause)
    "WE_TP_AUS3POL":    {"7SA6": "3457", "7SD5": "3457"},  # 1.WE TP nach 3-pol. AUS (Pause)
    "WE_TP_FOLGE":      {"7SA6": "3458", "7SD5": "3458"},  # 1.WE TP Folgefehler

    # ── 50BF Schalterversagerschutz — beide Geraete adressgleich (39xx) ────────
    "SCHALTERV":        {"7SA6": "3901", "7SD5": "3901"},  # SCHALTERV. Ein/Aus
    "I_SVS":            {"7SA6": "3902", "7SD5": "3902"},  # I> SVS Stromansprechwert
    "AUS_1POL_SVS":     {"7SA6": "3903", "7SD5": "3903"},  # AUS 1POL (T1)
    "T1_1POL_SVS":      {"7SA6": "3904", "7SD5": "3904"},  # T1 1POL
    "T1_3POL_SVS":      {"7SA6": "3905", "7SD5": "3905"},  # T1 3POL
    "T2_SVS":           {"7SA6": "3906", "7SD5": "3906"},  # T2 (umliegende Schalter)
    "I3I0_SVS":         {"7SA6": "3912", "7SD5": "3912"},  # 3I0> SVS Erdstromschwelle

    # ── 68/78 Pendelsperre / Pendelerfassung — beide Geraete adressgleich ──────
    "PENDELERFASSUNG":  {"7SA6": "120",  "7SD5": "120"},   # Funktionsumfang vorhanden
    "PEN_AUSLOES":      {"7SA6": "2006", "7SD5": "2006"},  # Ausloesung bei instabiler Pendelung

    # ── 27/59 Spannungsschutz — beide Geraete adressgleich (37xx) ──────────────
    "SPANNUNGSSCHUTZ":  {"7SA6": "137",  "7SD5": "137"},   # Funktionsumfang
    "UPH_HH_EIN":       {"7SA6": "3701", "7SD5": "3701"},  # Uph>(>) Ein/Aus
    "UPH_H":            {"7SA6": "3702", "7SD5": "3702"},  # Uph> Ansprechwert
    "T_UPH_H":          {"7SA6": "3703", "7SD5": "3703"},  # T Uph>
    "UPH_HH":           {"7SA6": "3704", "7SD5": "3704"},  # Uph>> Ansprechwert
    "T_UPH_HH":         {"7SA6": "3705", "7SD5": "3705"},  # T Uph>>
    "UPH_RUECK":        {"7SA6": "3709", "7SD5": "3709"},  # Uph>(>) Rueckfallverhaeltnis
    "UPH_L":            {"7SA6": "3752", "7SD5": "3752"},  # Uph< Ansprechwert
    "T_UPH_L":          {"7SA6": "3753", "7SD5": "3753"},  # T Uph<
    "UPH_LL":           {"7SA6": "3754", "7SD5": "3754"},  # Uph<< Ansprechwert
    "T_UPH_LL":         {"7SA6": "3755", "7SD5": "3755"},  # T Uph<<

    # ── 81 Frequenzschutz — beide Geraete adressgleich, frequenzabhaengig (36xx) ──
    "FREQUENZSCHUTZ":   {"7SA6": "3601", "7SD5": "3601"},  # Funktionsumfang Ein/Aus
    "F1_50":            {"7SA6": "3602", "7SD5": "3602"},  # FREQUENZ f1 bei 50 Hz
    "F1_60":            {"7SA6": "3603", "7SD5": "3603"},  # FREQUENZ f1 bei 60 Hz
    "T_F1":             {"7SA6": "3604", "7SD5": "3604"},  # T f1
    "F2_50":            {"7SA6": "3612", "7SD5": "3612"},
    "F2_60":            {"7SA6": "3613", "7SD5": "3613"},
    "T_F2":             {"7SA6": "3614", "7SD5": "3614"},
    "F3_50":            {"7SA6": "3622", "7SD5": "3622"},
    "F3_60":            {"7SA6": "3623", "7SD5": "3623"},
    "T_F3":             {"7SA6": "3624", "7SD5": "3624"},
    "F4_50":            {"7SA6": "3632", "7SD5": "3632"},
    "F4_60":            {"7SA6": "3633", "7SD5": "3633"},
    "T_F4":             {"7SA6": "3634", "7SD5": "3634"},

    # ── 49 Thermischer Ueberlastschutz — beide Geraete adressgleich (42xx) ─────
    "UEBERLASTSCHUTZ":  {"7SA6": "4201", "7SD5": "4201"},  # Funktionsumfang Ein/Aus
    "K_FAKTOR":         {"7SA6": "4202", "7SD5": "4202"},  # K-FAKTOR
    "ZEITKONSTANTE":    {"7SA6": "4203", "7SD5": "4203"},  # tau_th in MINUTEN
    "THETA_WARN":       {"7SA6": "4204", "7SD5": "4204"},  # Thermische Warnstufe
    "I_WARN":           {"7SA6": "4205", "7SD5": "4205"},  # Strommaessige Warnstufe
}


def ADR_get(key: str, leitgeraet: str) -> str:
    """Liefert die DIGSI-Adresse fuer eine Logikgroesse abhaengig vom Leitgeraet.

    leitgeraet: voller Optionsname ('Distanzschutz 7SA6' / 'Leitungsdifferential 7SD5')
                oder Kurz-Key ('7SA6' / '7SD5').
    """
    key_dev = LEITGERAET_KEY.get(leitgeraet, leitgeraet)
    eintrag = ADR.get(key)
    if not eintrag:
        return "—"
    return eintrag.get(key_dev, "—")


# ═════════════════════════════════════════════════════════════════════════════
# VOREINSTELLUNGEN DISTANZSCHUTZ 21
# ═════════════════════════════════════════════════════════════════════════════

# ── Zonen-Reichweitenfaktoren (x XL = primaere Leitungsreaktanz) ─────────────
# Belegt durch Einstellhinweise: Z1 ~ 85 % (Unterreichweite, X1prim = 0,85*XL),
# Uebergreifzone/Z2 >= 120 % der Leitungsstrecke (7SA6 Hdb. 2.2.1).
DIS_aktiv_def       = True

f_Z1_def            = 0.85    # Z1 Unterreichweite (x XL)                 [-]
t_Z1_def            = 0.00    # Adr.1305/1306 T1 (unverzoegert)           [s]

f_Z1B_def           = 1.20    # Z1B Uebergreifzone (Teleschutz, x XL)     [-]
t_Z1B_def           = 0.00    # Adr.1355/1356 T1B (gesteuert)             [s]

f_Z2_def            = 1.20    # Z2 Uebergreifzone (Zeitstaffel, x XL)     [-]
t_Z2_def            = 0.30    # Adr.1315/1316 T2                          [s]

f_Z3_def            = 1.50    # Z3 Vorwaerts-Reserve (x XL)               [-]
t_Z3_def            = 0.60    # Adr.1325 T3                               [s]

# Reservezonen Z4/Z5/Z6 — situativ, richtungswaehlbar (vorwaerts/rueckwaerts).
# Voreinstellung: Z4 vorwaerts (Fernreserve), Z5 rueckwaerts (Sammelschienen-/
# Richtungsvergleichsreserve), Z6 unwirksam.
modus_Z4_def        = "Vorwärts"
f_Z4_def            = 2.00    # Z4 Reichweite (x XL)                      [-]
RX_Z4_def           = 3.00    # R(Z4) / X(Z4)                            [-]
t_Z4_def            = 0.90    # Adr.1335 T4                              [s]

modus_Z5_def        = "Rückwärts"
f_Z5_def            = 0.50    # Z5 Reichweite (x XL, rueckwaerts)         [-]
RX_Z5_def           = 3.00    # R(Z5) / X(Z5)                            [-]
t_Z5_def            = 1.20    # Adr.1345 T5                              [s]

modus_Z6_def        = "Unwirksam"
f_Z6_def            = 1.00    # Z6 Reichweite (x XL)                      [-]
RX_Z6_def           = 3.00    # R(Z6) / X(Z6)                            [-]
t_Z6_def            = 1.50    # Adr.1365 T6                              [s]

# R/X-Faktor je Zone: R(Zk) = RX_Zk * X(Zk) (Lichtbogen-/Fehlerwiderstand).
# Stabilitaetsgrenze Z1: R/X <= 1 (7SA6 Hdb. 2.2.2). Hoehere Zonen breiter.
RX_Z1_def           = 1.00    # R(Z1) / X(Z1)                             [-]
RX_Z1B_def          = 1.50    # R(Z1B) / X(Z1B)                           [-]
RX_Z2_def           = 2.00    # R(Z2) / X(Z2)                             [-]
RX_Z3_def           = 2.50    # R(Z3) / X(Z3)                             [-]

# Verhaeltnis Erd-R-Abschnitt zu Phasen-R-Abschnitt: RE(Zk) = RE_RX * R(Zk)
RE_zu_R_def         = 1.50    # RE(Zk) / R(Zk) (groesserer Erdschleifen-R) [-]

# Polygon-Neigung Z1 (Adr.1307) — Voreinstellung 0 Grad (keine Neigung)
alpha_polyg_def     = 0       # Adr.1307 ALPHA POLYG                      [Grad]

# ── Erdimpedanzanpassung (Voreinstellungen) ─────────────────────────────────
# Geraete-Voreinstellung K0 = 1,0 * e^(j 0 Grad) (7SA6 Hdb. 2.1.4).
RE_RL_def           = 1.00    # Adr.1116 RE/RL(Z1)                        [-]
XE_XL_def           = 1.00    # Adr.1117 XE/XL(Z1)                        [-]
K0_def              = 1.00    # Adr.1120 K0(Z1) Betrag                    [-]
PHI_K0_def          = 0       # Adr.1121 PHI K0(Z1) Winkel               [Grad]

# ── Leitungsdaten-Voreinstellungen (Beispiel Freileitung, Hdb.-Beispiel) ────
X_Belag_def         = 0.229   # Adr.1110 X-BELAG (Reaktanzbelag)          [Ohm/km]
C_Belag_def         = 0.015   # Adr.1114 C-BELAG (Kapazitaetsbelag)       [uF/km]
phi_Ltg_def         = 80      # Adr.1105 PHI LTG (Leitungswinkel)         [Grad]


# ═════════════════════════════════════════════════════════════════════════════
# VOREINSTELLUNGEN 87L LEITUNGSDIFFERENTIALSCHUTZ (nur 7SD5)
# ═════════════════════════════════════════════════════════════════════════════
# Ansprechwerte als Vielfaches des Leitungs-Nennstroms IN_Ltg (herstellerneutral),
# zusaetzlich primaer [A] und sekundaer [A] ausgewiesen.
DIFF_aktiv_def      = True
i_diff_def          = 0.30    # Adr.1210 I-DIFF> (x IN_Ltg)               [-]
i_diff_zusch_def    = 0.30    # Adr.1213 I-DIF> ZUSCH. (x IN_Ltg)         [-]
t_i_diff_def        = 0.00    # Adr.1217A T-I-DIF> Ausloeseverzoegerung   [s]
i_freig_diff_def    = 0.20    # Adr.1219A I> FREIG. DIFF (x IN_Ltg)       [-]
i_diff_hh_def       = 8.00    # Adr.1233 I-DIFF>> (x IN_Ltg, unstabil.)   [-]
i_diff_hh_zusch_def = 8.00    # Adr.1235 I-DIF>> ZUSCH. (x IN_Ltg)        [-]

ic_komp_def         = "Aus"   # Adr.1221 Ladestromkompensation
icstab_icn_def      = 1.5     # Adr.1224 IcSTAB/IcN (Siemens-Empf. 1,5)   [-]
anzahl_geraete_def  = 2       # Adr.147 Anzahl Messstellen (Leitungsenden)
ws_verbindung_def   = "LWL direkt"   # Adr.4502 Wirkschnittstelle 1

# Plausibilitaet 87L
icN_faktor_min      = 2.5     # I-DIFF> >= 2,5 x IcN (Siemens-Empfehlung)  [-]
f_netz              = 50      # Netzfrequenz fuer Ladestromberechnung      [Hz]


# ═════════════════════════════════════════════════════════════════════════════
# VOREINSTELLUNGEN 67N GERICHTETER ERDKURZSCHLUSSSCHUTZ (beide Geraete)
# ═════════════════════════════════════════════════════════════════════════════
# Nur in geerdeten Netzen sinnvoll (niederohmig/starr geerdet). Ansprechwerte als
# Vielfaches des Leitungs-Nennstroms IN_Ltg, drei unabhaengige Stromstufen.
EKS_aktiv_def       = True
# 3I0>>> (Hochstromstufe, schnell)
modus_3I0HHH_def    = "Vorwärts"
i_3I0HHH_def        = 2.00    # Adr.3111 (x IN_Ltg)                       [-]
t_3I0HHH_def        = 0.10    # Adr.3112 T 3I0>>>                         [s]
# 3I0>> (mittlere Stufe)
modus_3I0HH_def     = "Vorwärts"
i_3I0HH_def         = 0.50    # Adr.3121 (x IN_Ltg)                       [-]
t_3I0HH_def         = 0.30    # Adr.3122 T 3I0>>                          [s]
# 3I0> (empfindliche Stufe)
modus_3I0H_def      = "Vorwärts"
i_3I0H_def          = 0.20    # Adr.3131 (x IN_Ltg)                       [-]
t_3I0H_def          = 0.60    # Adr.3132 T 3I0>                           [s]
# Stabilisierung und Richtung
i3i0_iph_stab_def   = 0.10    # Adr.3104 3I0 IPH STAB (x Iphase)          [-]
phi_komp_def        = 45      # Adr.3168 PHI KOMP (Richtungskennlinie)    [Grad]


# ═════════════════════════════════════════════════════════════════════════════
# VOREINSTELLUNGEN 85 SIGNALUEBERTRAGUNG DISTANZSCHUTZ (Teleschutz, beide Geraete)
# ═════════════════════════════════════════════════════════════════════════════
# Beschleunigt die Ausloesung ueber die Uebergreifzone Z1B durch Signalaustausch
# mit der Gegenstelle. Erfordert einen Kommunikationskanal (Wirkschnittstelle 7SD5
# bzw. Signalkanal 7SA6).
signalv_def         = "Signalvergleich"   # Adr.2101 Verfahren (POTT/Freigabe)
anschluss_def       = "1 Gegenende (Zweienden)"   # Adr.2102
t_sendverl_def      = 0.05    # Adr.2103 T SENDVERL. (Sendesignalverlaengerung) [s]
tv_dis_def          = 0.00    # Adr.2108 TV (Freigabeverzoegerung Z1B)          [s]
t_warte_rueckw_def  = 0.05    # Adr.2109 T WARTE RUECKW.                        [s]
t_transblock_def    = 0.04    # Adr.2110 T TRANSBLOCK (transiente Blockierzeit) [s]


# ═════════════════════════════════════════════════════════════════════════════
# VOREINSTELLUNGEN 50/51 NOT-UEBERSTROMZEITSCHUTZ (Reserve, beide Geraete)
# ═════════════════════════════════════════════════════════════════════════════
# Reserveschutz, der bei Ausfall der Distanzmessung (z.B. Messspannungsausfall)
# wirkt. Ansprechwerte als Vielfaches von IN_Ltg.
uebs_betriebsart_def = "Ein: bei U-Ausfall"   # Adr.2601
iph_hh_def          = 2.00    # Adr.2610 Iph>> (x IN_Ltg)                 [-]
t_iph_hh_def        = 0.10    # Adr.2611 T Iph>>                          [s]
iph_h_def           = 1.20    # Adr.2620 Iph> (x IN_Ltg)                  [-]
t_iph_h_def         = 0.50    # Adr.2621 T Iph>                           [s]


# ═════════════════════════════════════════════════════════════════════════════
# VOREINSTELLUNGEN 79 WIEDEREINSCHALTAUTOMATIK (AWE, beide Geraete)
# ═════════════════════════════════════════════════════════════════════════════
auto_we_def         = "Ein"   # Adr.3401 AUTO-WE
awe_anzahl_def      = 1       # Anzahl Unterbrechungszyklen
we_tp_aus1pol_def   = 1.20    # Adr.3456 Pausenzeit nach 1-pol. AUS       [s]
we_tp_aus3pol_def   = 0.50    # Adr.3457 Pausenzeit nach 3-pol. AUS       [s]
t_sperrzeit_def     = 3.00    # Adr.3403 Sperrzeit (Reclaim)              [s]


# ═════════════════════════════════════════════════════════════════════════════
# VOREINSTELLUNGEN 50BF SCHALTERVERSAGERSCHUTZ (beide Geraete)
# ═════════════════════════════════════════════════════════════════════════════
schalterv_def       = "Ein"   # Adr.3901 SCHALTERV.
i_svs_def           = 0.10    # Adr.3902 I> SVS (x IN_Ltg, Stromflussueberw.) [-]
i3i0_svs_def        = 0.10    # Adr.3912 3I0> SVS (x IN_Ltg)              [-]
aus_1pol_svs_def    = "Ja"    # Adr.3903 AUS 1POL (T1)
t1_1pol_svs_def     = 0.15    # Adr.3904 T1 1POL (Stufe 1)                [s]
t1_3pol_svs_def     = 0.15    # Adr.3905 T1 3POL (Stufe 1)                [s]
t2_svs_def          = 0.30    # Adr.3906 T2 (umliegende Schalter)         [s]


# ═════════════════════════════════════════════════════════════════════════════
# VOREINSTELLUNGEN 68/78 PENDELSPERRE / PENDELERFASSUNG (beide Geraete)
# ═════════════════════════════════════════════════════════════════════════════
pendelerfassung_def = "Vorhanden"   # Adr.120 PENDELERFASSUNG
pen_ausloes_def     = "Nein"        # Adr.2006 PEN-AUSLOES (Außertrittauslösung)


# ═════════════════════════════════════════════════════════════════════════════
# VOREINSTELLUNGEN 27/59 SPANNUNGSSCHUTZ (beide Geraete)
# ═════════════════════════════════════════════════════════════════════════════
# Ansprechwerte als Vielfaches der Bemessungsspannung UN (Leiter-Erde-bezogen
# ueber UN/sqrt3). Zweistufiger Ueber- und Unterspannungsschutz.
spannungsschutz_def = "Ein"
uph_h_def           = 1.15    # Adr.3702 Uph> (x UN)                      [-]
t_uph_h_def         = 2.00    # Adr.3703 T Uph>                           [s]
uph_hh_def          = 1.25    # Adr.3704 Uph>> (x UN)                     [-]
t_uph_hh_def        = 0.50    # Adr.3705 T Uph>>                          [s]
uph_l_def           = 0.75    # Adr.3752 Uph< (x UN)                      [-]
t_uph_l_def         = 2.00    # Adr.3753 T Uph<                           [s]
uph_ll_def          = 0.60    # Adr.3754 Uph<< (x UN)                     [-]
t_uph_ll_def        = 1.00    # Adr.3755 T Uph<<                          [s]


# ═════════════════════════════════════════════════════════════════════════════
# VOREINSTELLUNGEN 81 FREQUENZSCHUTZ (beide Geraete, frequenzabhaengige Adressen)
# ═════════════════════════════════════════════════════════════════════════════
# Vier Stufen f1 ... f4. Adresse haengt von der Nennfrequenz ab (50 vs. 60 Hz).
# Voreinstellung: f1/f2 Unterfrequenz, f3/f4 Ueberfrequenz.
frequenzschutz_def  = "Ein"
f1_def              = 49.5    # Adr.3602/3603 f1 (Unterfrequenz)          [Hz]
t_f1_def            = 0.10    # Adr.3604 T f1                             [s]
f2_def              = 49.0    # Adr.3612/3613 f2 (Unterfrequenz)          [Hz]
t_f2_def            = 0.10    # Adr.3614 T f2                             [s]
f3_def              = 50.5    # Adr.3622/3623 f3 (Ueberfrequenz)          [Hz]
t_f3_def            = 0.10    # Adr.3624 T f3                             [s]
f4_def              = 51.0    # Adr.3632/3633 f4 (Ueberfrequenz)          [Hz]
t_f4_def            = 0.10    # Adr.3634 T f4                             [s]


# ═════════════════════════════════════════════════════════════════════════════
# VOREINSTELLUNGEN 49 THERMISCHER UEBERLASTSCHUTZ (beide Geraete)
# ═════════════════════════════════════════════════════════════════════════════
# WICHTIG: Die Erwaermungszeitkonstante tau_th ist bei 7SA6/7SD5 in MINUTEN
# einzustellen (Adr.4203). Vergleich: 7UT613/7SJ66 ebenfalls Minuten, 7UM62 in
# Sekunden. Diese Geraeteabhaengigkeit ist zu beachten.
ueberlastschutz_def = "Ein"
k_faktor_def        = 1.10    # Adr.4202 K-FAKTOR (I_dauer / IN)          [-]
zeitkonstante_def   = 45      # Adr.4203 ZEITKONSTANTE tau_th             [min]
theta_warn_def      = 90      # Adr.4204 Thermische Warnstufe             [%]
i_warn_def          = 1.00    # Adr.4205 Strommaessige Warnstufe (x IN)   [-]


# ═════════════════════════════════════════════════════════════════════════════
# GLOBALE ENGINEERING-MARGEN / PLAUSIBILITAETS-SCHWELLWERTE
# ═════════════════════════════════════════════════════════════════════════════

# STW-/SPW-Anpassung (sekundaerer Bezug)
Anpass_min          = 0.5     # Untere Grenze STW-Anpassungsfaktor        [-]
Anpass_max          = 2.0     # Obere Grenze STW-Anpassungsfaktor         [-]

# Reichweiten-Plausibilitaet Distanzschutz
f_Z1_min            = 0.70    # Z1 sollte 70 ... 90 % der Leitung sein    [-]
f_Z1_max            = 0.90
f_uebergreif_min    = 1.15    # Uebergreifzonen >= ~120 % (mind. 115 %)   [-]
RX_Z1_max           = 1.0     # Stabilitaetsgrenze R/X der Z1             [-]

# Leitungswinkel plausibel
phi_Ltg_min         = 60      # Freileitung/Kabel typ. 60 ... 88 Grad     [Grad]
phi_Ltg_max         = 88

Toleranz_Empfehlung = 0.20    # Abweichung Eingabe/Empfehlung -> Hinweis  [-]


# ═════════════════════════════════════════════════════════════════════════════
# HERSTELLER-HINWEISE (Range + Begruendung + Adresse je Parameter)
# adr-Feld kann geraeteabhaengig zur Laufzeit ueberschrieben werden (siehe _hreg).
# ═════════════════════════════════════════════════════════════════════════════

HERST = {
    "f_Z1": {
        "range": "0,80 ... 0,90 x XL  (Voreinst. 0,85)",
        "adr":   "X(Z1) Adr.1303 (7SA6) / 1603 (7SD5)",
        "grund": ("Unterreichweite der 1. Zone. 85 % der Leitungsreaktanz stellt sicher, "
                  "dass die schnelle, unverzoegerte Zone Z1 wegen Mess- und "
                  "Wandlertoleranzen nicht ueber das Leitungsende hinausreicht "
                  "(7SA6 Hdb. 2.2.1, X1prim = 0,85 * XL)."),
    },
    "f_Z1B": {
        "range": ">= 1,20 x XL  (Voreinst. 1,20)",
        "adr":   "X(Z1B) Adr.1353 (7SA6) / 1653 (7SD5)",
        "grund": ("Uebergreifzone fuer das Signalvergleichsverfahren (Teleschutz). "
                  "Reicht bewusst ueber das Leitungsende hinaus (>= 120 %), wird aber "
                  "nur bei Freigabe durch die Gegenstelle ausgeloest (7SA6 Hdb. 2.2.2)."),
    },
    "f_Z2": {
        "range": ">= 1,20 x XL  (Voreinst. 1,20)",
        "adr":   "X(Z2) Adr.1313 (7SA6) / 1613 (7SD5)",
        "grund": ("Zeitgestaffelte Uebergreifzone als Reserve fuer die Gegenleitung. "
                  "Mindestens 120 % der eigenen Leitung, verzoegert mit T2 "
                  "(7SA6 Hdb. 2.2.1, Uebergreifzone >= 120 %)."),
    },
    "t_Z2": {
        "range": "0,2 ... 0,5 s  (Voreinst. 0,30)",
        "adr":   "T2 Adr.1315/1316 (7SA6) / 1615/1616 (7SD5)",
        "grund": ("Staffelzeit der 2. Zone gegenueber der schnellen Zone der "
                  "nachgelagerten Leitung (Selektivitaet, ein Staffelschritt)."),
    },
    "f_Z3": {
        "range": "1,2 ... 2,0 x XL  (Voreinst. 1,50)",
        "adr":   "X(Z3) Adr.1323 (7SA6) / 1623 (7SD5)",
        "grund": ("Vorwaerts-Reservezone. Reicht in die Folgeleitung; die exakte "
                  "Reichweite haengt von der Netzstaffelung ab (ausserhalb des "
                  "komponentenbezogenen Scope dieses Tools)."),
    },
    "reserve_zonen": {
        "range": "Z4/Z5/Z6 frei staffelbar: vorwaerts, rueckwaerts, ungerichtet",
        "adr":   "MODUS Z4/Z5/Z6 Adr.1331/1341/1361 (7SA6) bzw. 1631/1641/1661 (7SD5)",
        "grund": ("Zusaetzliche Staffelstufen. Z5 und Z6 besitzen getrennte Adressen fuer "
                  "Vorwaerts- und Rueckwaertsreichweite (X(Z5)+ Adr.1343 / X(Z5)- Adr.1346 "
                  "bzw. X(Z6)+ Adr.1363 / X(Z6)- Adr.1366), Z4 nutzt eine gemeinsame "
                  "Reichweite (Adr.1333) mit ueber MODUS gewaehlter Richtung. Eine "
                  "rueckwaerts gerichtete Zone dient als Reserve fuer die Sammelschiene "
                  "oder im Signalvergleichsverfahren (7SA6 Hdb. 2.2.1)."),
    },
    "RX_Z1": {
        "range": "<= 1,0  (Voreinst. 1,00)",
        "adr":   "R(Z1) Adr.1302 (7SA6) / 1602 (7SD5)",
        "grund": ("R-Abschnitt der Z1 fuer Lichtbogen-/Fehlerwiderstand. Der "
                  "Staffelfaktor 85 % gilt nur bis R/X <= 1 (7SA6 Hdb. 2.2.2), darueber "
                  "ist die Reichweite zu reduzieren."),
    },
    "RE_RL": {
        "range": "0,5 ... 8,0 (skalar)  bzw. K0 = 1,0 e^0 Grad",
        "adr":   "RE/RL Adr.1116 / K0 Adr.1120 (beide Geraete)",
        "grund": ("Erdimpedanzanpassung der Leitung. Bestimmt die korrekte "
                  "Schleifenimpedanz bei Erdkurzschluss. Aus den Leitungskonstanten "
                  "zu berechnen, nicht aus dem Gedaechtnis (7SA6 Hdb. 2.1.4, Adr.237 "
                  "waehlt das Format RE/RL,XE/XL oder K0)."),
    },
    "phi_Ltg": {
        "range": "60 ... 88 Grad  (Voreinst. 80)",
        "adr":   "PHI LTG Adr.1105 (beide Geraete)",
        "grund": ("Leitungswinkel arctan(X'/R'). Geht in die Erdimpedanzanpassung "
                  "und die Richtungsbestimmung ein (7SA6 Hdb. 2.1.4)."),
    },
    "i_diff": {
        "range": ">= 2,5 x IcN  (Nennladestrom)",
        "adr":   "I-DIFF> Adr.1210 (nur 7SD5)",
        "grund": ("Ansprechwert der stabilisierten Differentialstufe. Muss oberhalb des "
                  "kapazitiven Ladestroms liegen. Siemens empfiehlt mindestens 2,5 x IcN als "
                  "Ansprechwert; mit Ladestromkompensation (Adr.1221) kann er kleiner gewaehlt "
                  "werden (7SD5 Hdb. 2.2.1)."),
    },
    "i_diff_hh": {
        "range": "5 ... 12 x IN  (Voreinst. 8,0)",
        "adr":   "I-DIFF>> Adr.1233 (nur 7SD5)",
        "grund": ("Ansprechwert der unstabilisierten Hochstrom-/Ladungsvergleichsstufe fuer "
                  "die schnelle Ausloesung bei schweren inneren Fehlern. Muss deutlich ueber "
                  "I-DIFF> liegen (7SD5 Hdb. 2.2.1)."),
    },
    "icstab_icn": {
        "range": "1,5 x IcN  (Siemens-Voreinst.)",
        "adr":   "IcSTAB/IcN Adr.1224 (nur 7SD5)",
        "grund": ("Stabilisierungsstrom als Vielfaches des Nennladestroms. Mit 1,5 x IcN wird "
                  "die Siemens-Empfehlung eines minimalen Ansprechwerts von 2,5 x IcN der "
                  "I-DIFF>-Stufe erfuellt (7SD5 Hdb. 2.2.1)."),
    },
    "anzahl_geraete": {
        "range": "2 (Zweiendenleitung) oder 3 (Dreiendenleitung)",
        "adr":   "ANZAHL GERAETE Adr.147 (nur 7SD5)",
        "grund": ("Anzahl der Messstellen an den Grenzen des Schutzobjekts. Muss mit der Zahl "
                  "der Leitungsenden uebereinstimmen. Die Wirkschnittstelle (Adr.4501/4502) "
                  "verbindet die Geraete kommunikativ (7SD5 Hdb. 2.1.2)."),
    },
    "i_3I0H": {
        "range": "0,1 ... 0,5 x IN (empfindliche Stufe)",
        "adr":   "3I0> Adr.3131 (beide Geraete)",
        "grund": ("Empfindlichste Erdstromstufe. Muss oberhalb des betriebsmaessigen "
                  "Unsymmetriestroms (Erdstrom im fehlerfreien Betrieb) liegen, aber den "
                  "minimalen Erdkurzschlussstrom sicher erfassen (7SA6 Hdb. 2.5)."),
    },
    "i_3I0HHH": {
        "range": "1,0 ... 4,0 x IN (Hochstromstufe)",
        "adr":   "3I0>>> Adr.3111 (beide Geraete)",
        "grund": ("Schnelle Hochstromstufe fuer hohe Erdkurzschlussstroeme nahe der "
                  "Einspeisung. Oberhalb der mittleren Stufe einzustellen, kurze Verzoegerung."),
    },
    "phi_komp": {
        "range": "ca. 45 Grad  (Symmetrieachse der Richtungskennlinie)",
        "adr":   "PHI KOMP Adr.3168 (beide Geraete)",
        "grund": ("Kompensationswinkel der Richtungsbestimmung. Legt die Symmetrieachse der "
                  "Richtungskennlinie fest und richtet sie am Nullsystem-Quellwinkel des "
                  "Netzes aus (7SA6 Hdb. 2.5, Richtungsbestimmung)."),
    },
    "signalv": {
        "range": "Mitnahme / Signalvergleich / Blocking / Unblocking",
        "adr":   "SIGNALZUSATZ Adr.2101 (beide Geraete)",
        "grund": ("Signaluebertragungsverfahren des Distanzschutzes. Beschleunigt die "
                  "Ausloesung ueber die Uebergreifzone Z1B durch Austausch eines Freigabe- oder "
                  "Blockiersignals mit der Gegenstelle. Voraussetzung ist ein "
                  "Kommunikationskanal; Z1 und Z1B muessen vorwaerts gerichtet sein "
                  "(7SA6 Hdb. 2.6)."),
    },
    "t_transblock": {
        "range": "> Dauer transienter Signale  (Voreinst. 0,04 s)",
        "adr":   "T TRANSBLOCK Adr.2110 (beide Geraete)",
        "grund": ("Transiente Blockierzeit nach Richtungsumkehr. Muss laenger sein als die "
                  "Dauer transienter Vorgaenge bei Fehlerrichtungsumkehr, um Fehlfreigaben zu "
                  "verhindern (7SA6 Hdb. 2.6)."),
    },
    "iph_h": {
        "range": "1,1 ... 1,5 x IN (oberhalb Maximallast)",
        "adr":   "Iph> Adr.2620 (beide Geraete)",
        "grund": ("Grundstufe des Not-Ueberstromzeitschutzes. Muss oberhalb des maximal "
                  "auftretenden Betriebsstroms liegen, damit keine Fehlausloesung im "
                  "Normalbetrieb erfolgt (7SA6 Hdb. 2.7)."),
    },
    "uebs_betriebsart": {
        "range": "Aus / immer aktiv / bei U-Ausfall",
        "adr":   "BETRIEBSART Adr.2601 (beide Geraete)",
        "grund": ("Der Not-Ueberstromzeitschutz ist Reserveschutz. Ueblich ist die Einstellung "
                  "'bei U-Ausfall': er uebernimmt nur, wenn der Distanzschutz wegen "
                  "Messspannungsausfall nicht messen kann (7SA6 Hdb. 2.7)."),
    },
    "we_tp_aus1pol": {
        "range": "ca. 1,0 ... 1,5 s (1-polige Pause)",
        "adr":   "1.WE TP AUS1Po Adr.3456 (beide Geraete)",
        "grund": ("Spannungslose Pause nach 1-poliger Abschaltung. Muss lang genug fuer das "
                  "Verloeschen des Lichtbogens (Sekundaerlichtbogen) sein, aber kurz genug "
                  "fuer die Netzstabilitaet (7SA6 Hdb. 2.13)."),
    },
    "i_svs": {
        "range": "ca. 0,1 x IN (Stromflussueberwachung)",
        "adr":   "I> SVS Adr.3902 (beide Geraete)",
        "grund": ("Stromschwelle der Schalterversagerueberwachung. Erkennt, ob nach dem "
                  "AUS-Kommando noch Strom fliesst. Empfindlich, aber oberhalb des "
                  "Ladestroms einzustellen (7SA6 Hdb. 2.14)."),
    },
    "t2_svs": {
        "range": "Eigenzeit LS + Sicherheitsmarge",
        "adr":   "T2 SVS Adr.3906 (beide Geraete)",
        "grund": ("Verzoegerung der 2. Stufe (umliegende Leistungsschalter). Muss laenger sein "
                  "als die Ausschalteigenzeit des eigenen Schalters plus Ruecksetzzeit, damit "
                  "nur bei echtem Schalterversagen die Sammelschiene abgeschaltet wird "
                  "(7SA6 Hdb. 2.14)."),
    },
    "zeitkonstante": {
        "range": "geraetespezifisch, in MINUTEN  (Voreinst. 45)",
        "adr":   "ZEITKONSTANTE Adr.4203 (beide Geraete)",
        "grund": ("Erwaermungszeitkonstante tau_th des thermischen Abbilds. ACHTUNG: bei "
                  "7SA6/7SD5 in Minuten einzustellen (anders als z.B. 7UM62 in Sekunden). "
                  "Aus der t6-Zeit ergibt sich tau_th = t6 * 6^2 (7SA6 Hdb. 2.15)."),
    },
    "k_faktor": {
        "range": "1,0 ... 1,2 (I_dauer / IN)",
        "adr":   "K-FAKTOR Adr.4202 (beide Geraete)",
        "grund": ("Verhaeltnis des thermisch dauernd zulaessigen Stroms zum Bemessungsstrom. "
                  "Bestimmt den Endwert des thermischen Abbilds (7SA6 Hdb. 2.15)."),
    },
    "uph_l": {
        "range": "0,7 ... 0,8 x UN  (Unterspannung)",
        "adr":   "Uph< Adr.3752 (beide Geraete)",
        "grund": ("Ansprechwert des Unterspannungsschutzes. Muss unterhalb der niedrigsten "
                  "betrieblichen Spannung liegen, um Fehlausloesungen bei Lastschwankungen zu "
                  "vermeiden (7SA6 Hdb. 2.10)."),
    },
    "anschluss": {
        "range": "1 Gegenende (Zweienden, Voreinst.) / 2 Gegenenden (Dreienden)",
        "adr":   "ANSCHLUSS Adr.2102 (beide Geraete)",
        "grund": ("Konfiguriert, ob der Teleschutz mit einem oder zwei Gegenenden arbeitet. "
                  "Bei einer normalen Zweienden-Leitung '1 Gegenende' waehlen. Bei einer "
                  "T-Einspeisung (drei Leitungsenden) '2 Gegenenden' (7SA6 Hdb. 2.6)."),
    },
    "aus_1pol_svs": {
        "range": "Ja (Voreinst.) / Nein",
        "adr":   "AUS 1POL (T1) Adr.3903 (beide Geraete)",
        "grund": ("Legt fest, ob nach 1-poligem Ausloesen ein Wiederholungskommando (T1 1POL) "
                  "an den eigenen Schalter gegeben wird. Bei Netzen mit einpoliger "
                  "Wiedereinschaltung auf Ja setzen (7SA6 Hdb. 2.14)."),
    },
    "theta_warn": {
        "range": "80 ... 100 %  (Voreinst. 90)",
        "adr":   "THETA WARN Adr.4204 (beide Geraete)",
        "grund": ("Thermische Warnschwelle des Ueberlastschutzes als Prozentsatz des "
                  "Ausloesewerts (100 %). Ein Vorwarnsignal bei 90 % gibt dem Betreiber Zeit, "
                  "die Last zu reduzieren, bevor die Ausloesung erfolgt (7SA6 Hdb. 2.15)."),
    },
    "i_warn": {
        "range": "ca. 0,9 ... 1,0 x IN  (Voreinst. 1,00)",
        "adr":   "I WARN Adr.4205 (beide Geraete)",
        "grund": ("Strommaessige Warnschwelle parallel zur thermischen Warnschwelle. Spricht "
                  "bei Dauerstrom nahe dem Nennstrom an und warnt vor thermischer Ueberlastung, "
                  "bevor das thermische Abbild vollstaendig aufgefuellt ist (7SA6 Hdb. 2.15)."),
    },
    "f1": {
        "range": "Unterfrequenz ca. 49,5 / 49,0 Hz, Ueberfrequenz 50,5 / 51,0 Hz",
        "adr":   "FREQUENZ f1 Adr.3602 (50 Hz) / 3603 (60 Hz)",
        "grund": ("Frequenzstufen f1 ... f4 fuer Unter- und Ueberfrequenz. Die Adresse haengt "
                  "von der Nennfrequenz ab (50 oder 60 Hz). Staffelung nach Netzlastabwurf-Plan "
                  "(7SA6 Hdb. 2.11)."),
    },

    # ── Distanzschutz allgemein: Charakteristik und Anregeverfahren ──────────
    "DIS_charakt": {
        "range": "Polygon (Voreinst.) oder Kreis (MHO)",
        "adr":   "DIS-CHARAKT. Adr.115 (beide Geraete)",
        "grund": ("Auswahl der Ausloesecharakteristik. Die polygonale Charakteristik erlaubt eine "
                  "getrennte Einstellung von R- und X-Abschnitt und damit eine optimale Anpassung "
                  "an Leitungswinkel und Lichtbogenwiderstand; sie ist die uebliche Wahl. Die "
                  "Kreis-(MHO-)Charakteristik bildet je Zone einen gemeinsamen Impedanzkreis "
                  "(7SA6 Hdb. 2.2.1/2.2.2)."),
    },
    "DIS_anr": {
        "range": "IMPEDANZ / I-ANR. / U-I-ANR. / U-I-φ-ANR",
        "adr":   "DIS ANR Adr.114 (beide Geraete)",
        "grund": ("Anregeverfahren des Distanzschutzes. I-ANR. (Ueberstromanregung), wenn die Hoehe "
                  "des Kurzschlussstroms allein Kurzschluss und Last sicher trennt; U-I-ANR. "
                  "(spannungsabhaengige Stromanregung), wenn zusaetzlich der Spannungseinbruch als "
                  "Kriterium noetig ist; U-I-φ-ANR fuer hochbelastbare Hoch- und Hoechstspannungs"
                  "leitungen; IMPEDANZ nutzt die am weitesten eingestellten R/X-Abschnitte als "
                  "Anregekriterium (7SA6 Hdb. 2.2.1)."),
    },
    "alpha_polyg": {
        "range": "0 ... 45 Grad  (Voreinst. 0)",
        "adr":   "ALPHA POLYG Adr.1307 (7SA6) / 1607 (7SD5)",
        "grund": ("Neigung der R-Achse des Ausloesepolygons. Eine Neigung dreht den oberen R-Rand "
                  "der Zone, um den Einfluss des Lastwinkels und des Fehlerwiderstands zu "
                  "beruecksichtigen. Voreinstellung 0 Grad (keine Neigung) ist fuer die meisten "
                  "Leitungen ausreichend (7SA6 Hdb. 2.2.2)."),
    },

    # ── R/X-Faktoren der weiteren Zonen ──────────────────────────────────────
    "RX_Z1B": {
        "range": "ca. 1,0 ... 2,0  (Voreinst. 1,50)",
        "adr":   "R(Z1B) Adr.1352 (7SA6) / 1652 (7SD5)",
        "grund": ("R-Abschnitt der Uebergreifzone Z1B fuer den Teleschutz. Etwas breiter als Z1, "
                  "damit auch Erdfehler mit Lichtbogenwiderstand am Leitungsende sicher erfasst "
                  "werden. Die R-Aufweitung darf nicht in den Lastbereich reichen (7SA6 Hdb. 2.2.2)."),
    },
    "RX_Z2": {
        "range": "ca. 1,5 ... 2,5  (Voreinst. 2,00)",
        "adr":   "R(Z2) Adr.1312 (7SA6) / 1612 (7SD5)",
        "grund": ("R-Abschnitt der zeitgestaffelten Uebergreifzone Z2. Breiter gewaehlt, da Z2 als "
                  "Reserve fuer die Gegenleitung auch hochohmige Fehler erfassen soll, jedoch "
                  "weiterhin unterhalb der minimalen Lastimpedanz bleiben muss (7SA6 Hdb. 2.2.2)."),
    },
    "RX_Z3": {
        "range": "ca. 2,0 ... 3,0  (Voreinst. 2,50)",
        "adr":   "R(Z3) Adr.1322 (7SA6) / 1622 (7SD5)",
        "grund": ("R-Abschnitt der Vorwaerts-Reservezone Z3. Am breitesten der Hauptzonen, um "
                  "entfernte hochohmige Fehler als Fernreserve zu erfassen. Die Lastausblendung "
                  "(Lastkegel bzw. Anregekennlinie) verhindert ein Eingreifen im Lastbetrieb "
                  "(7SA6 Hdb. 2.2.2)."),
    },

    # ── Staffelzeiten der Distanzzonen ───────────────────────────────────────
    "t_Z1": {
        "range": "0,00 s (unverzoegert)  (Voreinst. 0,00)",
        "adr":   "T1 Adr.1305 (1-pol.) / 1306 (mehrpol.), 7SA6 (7SD5 1605/1606)",
        "grund": ("Ausloeseverzoegerung der schnellen Unterreichweitenzone Z1. Da Z1 sicher "
                  "innerhalb der eigenen Leitung liegt (85 %), loest sie unverzoegert aus. Eine "
                  "Verzoegerung > 0 ist nur in Sonderfaellen (z.B. Kurzschlussfestigkeit) noetig "
                  "(7SA6 Hdb. 2.2.1)."),
    },
    "t_Z1B": {
        "range": "0,00 s (signalgesteuert)  (Voreinst. 0,00)",
        "adr":   "T1B Adr.1355 (1-pol.) / 1356 (mehrpol.), 7SA6 (7SD5 1655/1656)",
        "grund": ("Verzoegerung der Uebergreifzone Z1B. Im Teleschutz loest Z1B nach Empfang des "
                  "Freigabesignals unverzoegert aus (T1B = 0). Ohne Signal wirkt Z1B erst nach der "
                  "uebergeordneten Staffelzeit; T1B steuert die Eigenzeit der signalgesteuerten "
                  "Stufe (7SA6 Hdb. 2.2.1/2.6)."),
    },
    "t_Z3": {
        "range": "ca. 0,6 ... 1,0 s  (Voreinst. 0,60)",
        "adr":   "T3 Adr.1325 (7SA6) / 1625 (7SD5)",
        "grund": ("Staffelzeit der Vorwaerts-Reservezone Z3, ein bis zwei Staffelschritte hinter T2. "
                  "Die genaue Zeit ergibt sich aus dem netzweiten Staffelplan, der ausserhalb des "
                  "komponentenbezogenen Scope dieses Tools liegt (7SA6 Hdb. 2.2.1)."),
    },

    # ── 87L Leitungsdifferentialschutz: weitere Stufen (nur 7SD5) ────────────
    "i_diff_zusch": {
        "range": "= I-DIFF> (Voreinst. 0,30 x IN)",
        "adr":   "I-DIF> ZUSCH. Adr.1213 (nur 7SD5)",
        "grund": ("Erhoehter Ansprechwert der stabilisierten Stufe waehrend der Zuschalterkennung "
                  "(manuelles Zuschalten auf einen Fehler). Verhindert Fehlausloesungen durch "
                  "Einschaltstroeme; ueblicherweise gleich oder etwas ueber I-DIFF> "
                  "(7SD5 Hdb. 2.2.1)."),
    },
    "t_i_diff": {
        "range": "0,00 s (unverzoegert)  (Voreinst. 0,00)",
        "adr":   "T-I-DIF> Adr.1217A (nur 7SD5)",
        "grund": ("Ausloeseverzoegerung der stabilisierten Differentialstufe. Als schneller "
                  "Hauptschutz arbeitet 87L unverzoegert (T = 0); eine Verzoegerung wird nur in "
                  "Sonderfaellen gesetzt (7SD5 Hdb. 2.2.1)."),
    },
    "i_freig_diff": {
        "range": "ca. 0,15 ... 0,25 x IN  (Voreinst. 0,20)",
        "adr":   "I> FREIG. DIFF Adr.1219A (nur 7SD5)",
        "grund": ("Stromschwelle zur Freigabe der Differentialmessung. Unterhalb dieses Werts wird "
                  "die empfindliche Diffstufe blockiert, um Fehlmessungen bei kleinen Stroemen und "
                  "Messrauschen zu vermeiden (7SD5 Hdb. 2.2.1)."),
    },
    "i_diff_hh_zusch": {
        "range": ">= I-DIFF>>  (Voreinst. 8,0 x IN)",
        "adr":   "I-DIF>> ZUSCH. Adr.1235 (nur 7SD5)",
        "grund": ("Zuschaltschwelle der unstabilisierten Hochstromstufe. Wird vom Geraet "
                  "automatisch auf I-DIFF>> angehoben, falls kleiner eingestellt; sollte daher "
                  ">= I-DIFF>> gewaehlt werden (7SD5 Hdb. 2.2.1)."),
    },
    "ic_komp": {
        "range": "Aus (Voreinst.) / Ein",
        "adr":   "Ic-KOMP. Adr.1221 (nur 7SD5)",
        "grund": ("Ladestromkompensation. Bei langen Kabeln oder Leitungen mit hohem kapazitiven "
                  "Ladestrom rechnet das Geraet den Ladestrom aus dem Differenzstrom heraus. Dann "
                  "kann I-DIFF> empfindlicher als 2,5 x IcN eingestellt werden (7SD5 Hdb. 2.2.1)."),
    },
    "ws_verbindung": {
        "range": "LWL direkt / Kommunikationsumsetzer / LWL-Modul",
        "adr":   "WS1 Verbindung Adr.4502 (nur 7SD5)",
        "grund": ("Art der Wirkschnittstelle 1 zwischen den Leitungsenden. LWL direkt fuer kurze "
                  "Distanzen, Kommunikationsumsetzer fuer Strecken ueber Kommunikationsnetze. Die "
                  "Verbindung ist Projektierung, kein Schutz-Ansprechwert (7SD5 Hdb. 2.1.2)."),
    },

    # ── 85 Teleschutz: Zeitparameter ─────────────────────────────────────────
    "t_sendverl": {
        "range": "ca. 0,05 s  (Voreinst. 0,05)",
        "adr":   "T SENDVERL. Adr.2103 (beide Geraete)",
        "grund": ("Sendesignalverlaengerung. Haelt das Sendesignal nach Ruecknahme der Anregung "
                  "kurz aufrecht, damit die Gegenstelle das Freigabesignal sicher empfaengt "
                  "(7SA6 Hdb. 2.6)."),
    },
    "tv_dis": {
        "range": "0,00 s (unverzoegert)  (Voreinst. 0,00)",
        "adr":   "TV Adr.2108 (beide Geraete)",
        "grund": ("Freigabeverzoegerung der Z1B im Vergleichsverfahren. Im Normalfall 0, damit die "
                  "Ausloesung nach Signalempfang nicht zusaetzlich verzoegert wird (7SA6 Hdb. 2.6)."),
    },
    "t_warte_rueckw": {
        "range": "ca. 0,04 ... 0,05 s  (Voreinst. 0,05)",
        "adr":   "T WARTE RUECKW. Adr.2109 (beide Geraete)",
        "grund": ("Wartezeit vor dem Wirksamwerden der transienten Blockierung bei "
                  "Fehlerrichtungsumkehr. Verhindert Fehlfreigaben bei kurzzeitiger "
                  "Richtungsumkehr (7SA6 Hdb. 2.6)."),
    },

    # ── 67N Gerichteter Erdkurzschlussschutz: Stufen-Zeiten und Stabilisierung ──
    "t_3I0HHH": {
        "range": "ca. 0,1 s (schnell)  (Voreinst. 0,10)",
        "adr":   "T 3I0>>> Adr.3112 (beide Geraete)",
        "grund": ("Kurze Verzoegerung der schnellen Hochstromstufe 3I0>>>. Erfasst hohe "
                  "Erdkurzschlussstroeme nahe der Einspeisung mit minimaler Zeit (7SA6 Hdb. 2.5)."),
    },
    "i_3I0HH": {
        "range": "ca. 0,3 ... 0,8 x IN  (Voreinst. 0,50)",
        "adr":   "3I0>> Adr.3121 (beide Geraete)",
        "grund": ("Ansprechwert der mittleren Erdstromstufe, zwischen empfindlicher Stufe 3I0> und "
                  "Hochstromstufe 3I0>>> gestaffelt (7SA6 Hdb. 2.5)."),
    },
    "t_3I0HH": {
        "range": "ca. 0,3 s  (Voreinst. 0,30)",
        "adr":   "T 3I0>> Adr.3122 (beide Geraete)",
        "grund": ("Staffelzeit der mittleren Erdstromstufe, zeitlich zwischen 3I0>>> und 3I0> "
                  "(inverse Staffelung: hoeherer Ansprechwert loest schneller aus, 7SA6 Hdb. 2.5)."),
    },
    "t_3I0H": {
        "range": "ca. 0,6 s  (Voreinst. 0,60)",
        "adr":   "T 3I0> Adr.3132 (beide Geraete)",
        "grund": ("Staffelzeit der empfindlichen Erdstromstufe. Laengste Zeit der drei Stufen, da "
                  "sie den kleinsten Erdstrom erfasst und gegen die naeher liegenden Stufen "
                  "selektiv gestaffelt ist (7SA6 Hdb. 2.5)."),
    },
    "i3i0_iph_stab": {
        "range": "ca. 0,1 x Iph  (Voreinst. 0,10)",
        "adr":   "3I0 IPH STAB Adr.3104 (beide Geraete)",
        "grund": ("Stabilisierung des Erdstromschutzes gegen den Phasenstrom. Verhindert "
                  "Fehlanregungen durch Stromwandlerfehler bei hohen Phasenstroemen, indem die "
                  "Erdstromschwelle stromabhaengig angehoben wird (7SA6 Hdb. 2.5)."),
    },

    # ── 50/51 Not-Ueberstromzeitschutz: Stufen-Zeiten und Hochstromstufe ─────
    "iph_hh": {
        "range": "ca. 1,5 ... 2,5 x IN  (Voreinst. 2,00)",
        "adr":   "Iph>> Adr.2610 (beide Geraete)",
        "grund": ("Hochstromstufe des Not-Ueberstromschutzes. Spricht auf hohe Kurzschlussstroeme "
                  "an und loest schneller aus als die Grundstufe Iph>; oberhalb des maximalen "
                  "durchfliessenden Kurzschlussstroms bei Fehlern hinter der Leitung "
                  "(7SA6 Hdb. 2.7)."),
    },
    "t_iph_hh": {
        "range": "ca. 0,1 s  (Voreinst. 0,10)",
        "adr":   "T Iph>> Adr.2611 (beide Geraete)",
        "grund": ("Kurze Verzoegerung der Hochstromstufe. Da der Not-Ueberstromschutz nur bei "
                  "Ausfall der Distanzmessung wirkt, ist eine schnelle Hochstromstufe zur "
                  "Begrenzung der Fehlerdauer sinnvoll (7SA6 Hdb. 2.7)."),
    },
    "t_iph_h": {
        "range": "ca. 0,3 ... 0,6 s  (Voreinst. 0,50)",
        "adr":   "T Iph> Adr.2621 (beide Geraete)",
        "grund": ("Verzoegerung der Grundstufe Iph>. Zeitlich hinter der Hochstromstufe gestaffelt, "
                  "damit die Reserve selektiv zu den nachgelagerten Schutzeinrichtungen bleibt "
                  "(7SA6 Hdb. 2.7)."),
    },

    # ── 79 Wiedereinschaltautomatik: Zyklen, 3-pol. Pause, Sperrzeit ─────────
    "awe_anzahl": {
        "range": "1 (Voreinst.) ... 4 Unterbrechungszyklen",
        "adr":   "Anzahl WE-Zyklen (AWE-Projektierung, beide Geraete)",
        "grund": ("Anzahl der Wiedereinschaltversuche. In Hoch- und Hoechstspannungsnetzen ist "
                  "meist eine schnelle einmalige WE ueblich; mehrere Zyklen werden im "
                  "Verteilnetz eingesetzt (7SA6 Hdb. 2.13)."),
    },
    "we_tp_aus3pol": {
        "range": "ca. 0,3 ... 0,5 s  (Voreinst. 0,50)",
        "adr":   "1.WE TP nach 3-pol. AUS Adr.3457 (beide Geraete)",
        "grund": ("Spannungslose Pause nach 3-poliger Abschaltung. Kuerzer als die 1-polige Pause, "
                  "da kein Sekundaerlichtbogen ueber die gesunden Phasen gespeist wird; die Laenge "
                  "richtet sich nach der Netzstabilitaet (7SA6 Hdb. 2.13)."),
    },
    "t_sperrzeit": {
        "range": "ca. 3,0 s  (Voreinst. 3,00)",
        "adr":   "T SPERRZEIT Adr.3403 (beide Geraete)",
        "grund": ("Sperrzeit (Reclaim Time) nach erfolgreicher Wiedereinschaltung. Muss laenger "
                  "sein als die Pausenzeiten, damit ein WE-Zyklus vollstaendig abgeschlossen ist, "
                  "bevor ein neuer Fehler einen neuen Zyklus startet (7SA6 Hdb. 2.13)."),
    },

    # ── 50BF Schalterversagerschutz: Erdstromschwelle und Zeiten ─────────────
    "i3i0_svs": {
        "range": "ca. 0,1 x IN  (Voreinst. 0,10)",
        "adr":   "3I0> SVS Adr.3912 (beide Geraete)",
        "grund": ("Erdstromschwelle der Schalterversagerueberwachung. Empfindlich eingestellt, um "
                  "auch kleine Reststroeme nach dem AUS-Kommando zu erkennen, aber oberhalb des "
                  "betriebsmaessigen Erdstroms (7SA6 Hdb. 2.14)."),
    },
    "t1_1pol_svs": {
        "range": "ca. 0,12 ... 0,2 s  (Voreinst. 0,15)",
        "adr":   "T1 1POL Adr.3904 (beide Geraete)",
        "grund": ("Verzoegerung der 1. Stufe nach 1-poligem AUS (Wiederholungskommando an den "
                  "eigenen Schalter). Muss laenger sein als die Ausschalteigenzeit des Schalters "
                  "plus Ruecksetzzeit der Stromueberwachung (7SA6 Hdb. 2.14)."),
    },
    "t1_3pol_svs": {
        "range": "ca. 0,12 ... 0,2 s  (Voreinst. 0,15)",
        "adr":   "T1 3POL Adr.3905 (beide Geraete)",
        "grund": ("Verzoegerung der 1. Stufe nach 3-poligem AUS. Wie T1 1POL bemessen aus "
                  "Schalter-Eigenzeit und Ruecksetzzeit; Wiederholungskommando an den eigenen "
                  "Schalter vor Ausloesung der umliegenden Schalter (7SA6 Hdb. 2.14)."),
    },

    # ── 68/78 Pendelerfassung ────────────────────────────────────────────────
    "pendelerfassung": {
        "range": "Vorhanden (Voreinst.) / Nicht vorhanden",
        "adr":   "PENDELERFASSUNG Adr.120 (beide Geraete)",
        "grund": ("Funktionsumfang der Pendelerfassung. Bei vermaschten Netzen mit moeglichen "
                  "Leistungspendelungen vorzusehen, damit der Distanzschutz Pendelungen nicht als "
                  "Kurzschluss fehlinterpretiert (7SA6 Hdb. 2.3)."),
    },
    "pen_ausloes": {
        "range": "Nein (nur Sperre, Voreinst.) / Ja (Aussertrittauslösung)",
        "adr":   "PEN-AUSLOES Adr.2006 (beide Geraete)",
        "grund": ("Legt fest, ob bei instabiler Pendelung (Aussertrittfall) gezielt ausgeloest wird. "
                  "Voreinstellung Nein: die Funktion wirkt nur als Pendelsperre. Eine "
                  "Aussertrittauslösung nur bei entsprechender Netzanforderung aktivieren "
                  "(7SA6 Hdb. 2.3)."),
    },

    # ── 27/59 Spannungsschutz: Ansprechwerte und Zeiten ──────────────────────
    "uph_h": {
        "range": "ca. 1,10 ... 1,15 x UN  (Voreinst. 1,15)",
        "adr":   "Uph> Adr.3702 (beide Geraete)",
        "grund": ("Erste Ueberspannungsstufe. Oberhalb der hoechsten betrieblichen Spannung, mit "
                  "laengerer Verzoegerung als die Hochstufe Uph>> (7SA6 Hdb. 2.10)."),
    },
    "t_uph_h": {
        "range": "ca. 1,5 ... 3,0 s  (Voreinst. 2,00)",
        "adr":   "T Uph> Adr.3703 (beide Geraete)",
        "grund": ("Verzoegerung der ersten Ueberspannungsstufe. Laenger als T Uph>>, damit "
                  "kurzzeitige Spannungsanstiege nicht zur Ausloesung fuehren (7SA6 Hdb. 2.10)."),
    },
    "uph_hh": {
        "range": "ca. 1,20 ... 1,30 x UN  (Voreinst. 1,25)",
        "adr":   "Uph>> Adr.3704 (beide Geraete)",
        "grund": ("Zweite (hoehere) Ueberspannungsstufe fuer schnelle Abschaltung bei deutlicher "
                  "Ueberspannung. Hoeher als Uph>, mit kuerzerer Verzoegerung (7SA6 Hdb. 2.10)."),
    },
    "t_uph_hh": {
        "range": "ca. 0,3 ... 0,5 s  (Voreinst. 0,50)",
        "adr":   "T Uph>> Adr.3705 (beide Geraete)",
        "grund": ("Kurze Verzoegerung der hohen Ueberspannungsstufe. Begrenzt die Dauer hoher "
                  "Ueberspannungen, ohne auf transiente Spitzen anzusprechen (7SA6 Hdb. 2.10)."),
    },
    "t_uph_l": {
        "range": "ca. 1,5 ... 3,0 s  (Voreinst. 2,00)",
        "adr":   "T Uph< Adr.3753 (beide Geraete)",
        "grund": ("Verzoegerung der ersten Unterspannungsstufe. Lang genug, um kurzzeitige "
                  "Spannungseinbruechen (z.B. Anlaufvorgaenge) nicht zu folgen (7SA6 Hdb. 2.10)."),
    },
    "uph_ll": {
        "range": "ca. 0,5 ... 0,65 x UN  (Voreinst. 0,60)",
        "adr":   "Uph<< Adr.3754 (beide Geraete)",
        "grund": ("Zweite (tiefere) Unterspannungsstufe fuer schnellere Abschaltung bei starkem "
                  "Spannungseinbruch. Tiefer als Uph<, mit kuerzerer Verzoegerung "
                  "(7SA6 Hdb. 2.10)."),
    },
    "t_uph_ll": {
        "range": "ca. 0,5 ... 1,0 s  (Voreinst. 1,00)",
        "adr":   "T Uph<< Adr.3755 (beide Geraete)",
        "grund": ("Kurze Verzoegerung der tiefen Unterspannungsstufe. Begrenzt die Dauer starker "
                  "Spannungseinbruechen (7SA6 Hdb. 2.10)."),
    },

    # ── 81 Frequenzschutz: Stufenzeit ────────────────────────────────────────
    "t_f": {
        "range": "ca. 0,1 s je Stufe  (Voreinst. 0,10)",
        "adr":   "T f1...f4 Adr.3604 / 3614 / 3624 / 3634 (beide Geraete)",
        "grund": ("Ausloeseverzoegerung je Frequenzstufe. Kurze Zeiten fuer einen schnellen "
                  "Lastabwurf bei Unterfrequenz; die Staffelung der Stufen folgt dem "
                  "Lastabwurfplan des Netzbetreibers (7SA6 Hdb. 2.11)."),
    },
}
