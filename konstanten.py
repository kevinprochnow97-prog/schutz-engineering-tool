"""
konstanten.py — Voreinstellungen und Plausibilitaets-Schwellwerte
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Single Source of Truth für alle SIPROTEC-7UT6xx-Werksvoreinstellungen,
Engineering-Margen (Selektivität/Empfindlichkeit) und Plausibilitätsgrenzen.
Entspricht dem Excel-Blatt "Konstanten" + den Engineering-Zeilen in
"Eingaben_Allgemein". Alle Werte sind frei änderbar.

Quellen: SIPROTEC 7UT613 Handbuch (Kap. 2.2.7 / 2.3 / 2.4 / 2.9),
IEC 60255-151, IEC 60255-187-3, VDE-FNN-Leitfaden.
"""

# ── 87T Differentialschutz (7UT6xx) ──────────────────────────────────────────
I_DIFF_def        = 0.20   # Adr.1221  Ansprechwert IDIFF>            [I/InO]
T_I_DIFF_def      = 0.00   # Adr.1226A Verzögerung TIDIFF>           [s]
I_DIFF_HH_def     = 10.4   # Adr.1231  Ansprechwert IDIFF>> (Hochstr.)[I/InO]
T_I_DIFF_HH_def   = 0.00   # Adr.1236A Verzögerung TIDIFF>>          [s]
Steigung_1_def    = 0.25   # Adr.1241A Steigung 1                     [-]
Fusspunkt_1_def   = 0.00   # Adr.1242A Fußpunkt 1                    [I/InO]
Steigung_2_def    = 0.50   # Adr.1243A Steigung 2                     [-]
Fusspunkt_2_def   = 2.50   # Adr.1244A Fußpunkt 2                    [I/InO]
Anlauf_Stab_def   = 0.10   # Adr.1251A ISTAB Anlauferkennung          [I/InO]
Anlauf_Faktor_def = 1.00   # Adr.1252A Ansprechwert-Erhöhung Anlauf  [-]
EXF_Stab_def      = 4.00   # Adr.1261A ISTAB Zusatzstab. ext. Fehler  [I/InO]
Harm_2_def        = 0.15   # Adr.1271  2.Harmonische (Inrush-Stab.)   [-]
Harm_n_def        = 0.30   # Adr.1276  n.Harmonische (Stab.)          [-]

# ── 87N Erdfehler-Differentialschutz EDS (7UT6xx) ────────────────────────────
I_EDS_def         = 0.15   # Adr.1311  Ansprechwert EDS               [I/InS]
T_I_EDS_def       = 0.00   # Adr.1312A Verzögerung TIEDS>            [s]
Steigung_EDS_def  = 0.00   # Adr.1313A Steigung I-EDS> = f(ISUM)      [-]

# ── 50/51 Überstromzeitschutz Phasen (7UT6xx / 7SJ6x) ───────────────────────
f_I_Ph_def        = 1.50   # Faktor I>  Phase                         [I/InS]
t_I_Ph_def        = 0.50   # Verzögerung I>                          [s]
f_I_Ph_HH_def     = 7.00   # Faktor I>> Phase (Hochstromstufe)        [I/InS]
t_I_Ph_HH_def     = 0.10   # Verzögerung I>>                         [s]
Rush_2H_Ph_def    = 0.15   # Adr.2041 2.HARMON. PHASE, Anteil 2.Harm. (Schalter Adr.2002)   [-]

# ── 50N/51N Überstromzeitschutz Erde (Sternpunkt-Strom) ─────────────────────
I_E_def           = 0.40   # Adr.2413 Anregestrom IE>  (1A-Wandler)   [A sek.]
t_I_E_def         = 2.00   # Adr.2414 Verzögerung TIE>               [s]
I_E_HH_def        = 1.00   # Adr.2411 Anregestrom IE>> (1A-Wandler)   [A sek.]
t_I_E_HH_def      = 1.50   # Adr.2412 Verzögerung TIE>>              [s]

# ── 49 Thermischer Ueberlastschutz (thermisches Abbild) ──────────────────────
k_Faktor_def      = 1.10   # Adr.4202 k-Faktor (zul. Dauerstrom)      [x IN]
tau_Trafo_def     = 100.0  # Adr.4203 Zeitkonstante  ← MINUTEN!       [min]
Theta_Warn_def    = 0.90   # Adr.4204 Thermische Warnstufe            [-]
I_Warn_def        = 1.00   # Adr.4205 Stromwarnstufe                  [I/InS]

# ── 46 Schieflastschutz (optional) ───────────────────────────────────────────
I2_zul_def        = 0.16   # Adr.4032 Dauernd zul. Schieflast I2      [I/InS]
t_Warn_I2_def     = 20.0   # Adr.4033 Verzögerung Warnstufe I2       [s]

# ── Reserveschutz-Erweiterung UAMZ-3I0 ───────────────────────────────────────
f_I_3I0_def       = 0.30   # Adr.2214 Faktor 3I0>                     [I/InS]
t_I_3I0_def       = 0.50   # Adr.2216 Verzögerung T 3I0>             [s]
f_I_3I0_HH_def    = 1.50   # Adr.2211 Faktor 3I0>> (Hochstromstufe)   [I/InS]
t_I_3I0_HH_def    = 0.10   # Adr.2213 Verzögerung T 3I0>>            [s]

# ── Globale Engineering-Margen (Selektivität / Empfindlichkeit) ─────────────
dt_Staffel        = 0.30   # Globale Staffelzeit (typ. 0,25 ... 0,40) [s]
k_S_I             = 1.20   # I>  = k_S_I  * I_max_Last                [-]
k_S_IGG           = 1.20   # I>> bzgl. I_k_max nachgel. Station       [-]
gamma_Ikmin       = 1.50   # I_k_min(Ende) >= gamma * I>             [-]
Inrush_Faktor     = 8.00   # Trafo-Inrush-Spitze als Vielfaches IN    [x IN]

# ── U0-Erdschlusserfassung (isoliertes/kompensiertes Netz) ───────────────────
U0_Meldung_pu     = 0.30   # U0>  Meldestufe         [p.u. UN/sqrt(3)]
t_U0_Meldung      = 10.0   # Verzögerung U0>                         [s]
U0_Abschalt_pu    = 0.50   # U0>> Abschaltstufe      [p.u. UN/sqrt(3)]
t_U0_Abschalt     = 60.0   # Verzögerung U0>>                        [s]
cos_phi_pct       = 5.0    # cos-phi-Stufe (nur kompensiert) [% IE_kap]
t_cos_phi         = 1.0    # Verzögerung cos-phi-Stufe               [s]

# ── Plausibilitaets-Schwellwerte (Geräte-Empfehlung) ────────────────────────
Sn_min_87T        = 5.0    # Mindest-Sn für 87T-Sinnhaftigkeit       [MVA]
Anpass_min        = 0.5    # Untere Grenze STW-Anpassungsfaktor I_an  [-]
Anpass_max        = 2.0    # Obere Grenze STW-Anpassungsfaktor I_an   [-]
Stufensteller_max = 30     # Max. Regelbereich verträglich m. Steig.1 [%]
uk_min            = 4.0    # Plausibilitätsgrenze uk (unten)         [%]
uk_max            = 20.0   # Plausibilitätsgrenze uk (oben)          [%]
k_Faktor_min      = 1.0    # Plausibilitätsgrenze k-Faktor (unten)   [-]
k_Faktor_max      = 1.5    # Plausibilitätsgrenze k-Faktor (oben)    [-]

# ── Empfehlungs-Schwellwerte für 87T (Sektion 4.6) ──────────────────────────
Stufensteller_warn   = 15  # > 15 % -> I-DIFF> auf 0,25 anheben       [%]
Stufensteller_hoch   = 25  # > 25 % -> I-DIFF> auf 0,30 anheben       [%]
Stufensteller_steig1 = 20  # > 20 % -> Steigung 1 auf 0,30 anheben    [%]
Sn_steig2_hoch       = 100 # > 100 MVA -> Steigung 2 auf 0,55         [MVA]
uk_fusspunkt_niedrig = 6   # uk < 6 % -> Fußpunkt 2 auf 3,0          [%]
Toleranz_Empfehlung  = 0.20  # Abweichung Eingabe/Empfehlung Hinweis  [-]

# ── Sternpunktbehandlungs-Optionen (steuern Funktionsauswahl) ────────────────
STERNPUNKT_OPTIONEN = [
    "Isoliert",
    "Kompensiert (Petersen)",
    "Niederohmig geerdet",
    "Direkt geerdet",
]
STERNPUNKT_NICHT_GEERDET = ["Isoliert", "Kompensiert (Petersen)"]

SCHALTGRUPPEN = [
    "Yyn0", "YNyn0", "Dyn5", "Dyn11", "Yd5", "Yd11",
    "YNd5", "YNd11", "Yzn5", "Yzn11",
]


# ═════════════════════════════════════════════════════════════════════════════
# HERSTELLER-HINWEISE (Wert/Range + Begründung je Parameter)
# Quelle: SIPROTEC 7UT613 Handbuch C53000-G1100-C160-3, IEC 60255, FNN-Leitfaden.
# Format je Schlüssel: dict(range=Anzeigetext, grund=Begründung des Herstellers)
# Wird im Reglerbereich (Caption) UND in den Korrektur-Hinweisen verwendet.
# ═════════════════════════════════════════════════════════════════════════════

HERST = {
    "I_DIFF": {
        "range": "0,20 ... 0,30 I/InO (Voreinst. 0,20)",
        "grund": ("Ansprechwert des Differentialschutzes. Bei Stufenstellern großer "
                  "30 % auf 0,25-0,30 anheben, da der Regelbereich einen stationären "
                  "Differenzstrom erzeugt (7UT613 Hdb. 2.2.7)."),
    },
    "I_DIFF_HH": {
        "range": "Daumenwert IN/uk, hier ca. 1,2/uk (Voreinst. 10,4)",
        "grund": ("Hochstromstufe (unstabilisiert). Muss oberhalb des maximalen "
                  "Durchgangsfehlerstroms liegen, damit sie nur bei inneren Fehlern "
                  "anspricht (7UT613 Hdb. 2.2.7)."),
    },
    "Steigung_1": {
        "range": "0,25 ... 0,30 (Voreinst. 0,25)",
        "grund": ("Neigung des ersten Kennlinienabschnitts. Berücksichtigt Stromwandler- "
                  "und Stufenstellerfehler im unteren Strombereich. Bei Stufensteller "
                  "größer 20 % auf 0,30 anheben."),
    },
    "Steigung_2": {
        "range": "0,50 ... 0,55 (Voreinst. 0,50)",
        "grund": ("Neigung ab Fußpunkt 2. Höhere Stabilisierung gegen Wandlersättigung "
                  "bei großen Durchgangsfehlern. Bei Sn größer 100 MVA auf 0,55."),
    },
    "Fusspunkt_2": {
        "range": "2,5 ... 3,0 I/InO (Voreinst. 2,5)",
        "grund": ("Knickpunkt zum steileren Kennlinienast. Bei kleinem uk (kleiner 6 %) "
                  "auf 3,0 erhöhen, da höhere Durchgangsfehlerströme auftreten."),
    },
    "Harm_2": {
        "range": "10 ... 20 % (Voreinst. 15 %)",
        "grund": ("Inrush-Stabilisierung über 2. Harmonische. 15 % passt in den "
                  "meisten Fällen; bei sehr ungünstigen Einschaltbedingungen kleiner "
                  "stellen (7UT613 Hdb. 2.2.7)."),
    },
    "f_I_Ph": {
        "range": "ca. 1,2 ... 1,4 x IN (Trafo: +40 % über Maximallast)",
        "grund": ("Ueberstromstufe I> als Reserveschutz. Muss oberhalb der maximalen "
                  "Betriebslast liegen, Anregung durch Überlast ausgeschlossen. Bei "
                  "Transformatoren ca. 40 % über Maximallast (7UT613 Hdb. 2.4)."),
    },
    "t_I_Ph": {
        "range": "aus Staffelplan, typ. 0,3 ... 0,6 s (Voreinst. 0,5 s)",
        "grund": ("Verzögerung I>. Ergibt sich aus dem netzweiten Staffelplan "
                  "(reine Zusatzverzögerung, ohne Eigenzeit)."),
    },
    "f_I_Ph_HH_OS": {
        "range": "1,2/uk bzw. über Durchgangsfehler (auto aus uk/Ik_max_US)",
        "grund": ("Hochstromstufe Speiseseite (OS). Muss für Fehler bis in den Trafo "
                  "ansprechen, aber NICHT bei durchfließendem US-Kurzschlussstrom. "
                  "Einstellwert = 1,2 x Ik_max_US (auf OS bezogen). 7UT613 Hdb. 2.4, "
                  "Beispiel: 35 MVA / uk 15 % -> I>> = 0,8 x INS."),
    },
    "f_I_Ph_HH_US": {
        "range": "gegen nachgelagerte Staffelung, typ. 4 ... 8 x IN",
        "grund": ("Hochstromstufe US-Seite. Wird gegen die nachgelagerte Stromstaffelung "
                  "bemessen; oberhalb des größten Abgangs-Kurzschlussstroms, unter dem "
                  "Sammelschienen-Fehlerstrom."),
    },
    "t_I_Ph_HH": {
        "range": "0,0 ... 0,1 s (Voreinst. 0,1 s)",
        "grund": ("Verzögerung I>>. Beim Trafo kurze Sicherheitsverzögerung gegen "
                  "transiente Sättigung sinnvoll; Rush-Stabilisierung wirkt NICHT auf "
                  "I>> (7UT613 Hdb. 2.4)."),
    },
    "k_Faktor": {
        "range": "1,0 ... 1,5 x IN (Voreinst. 1,10)",
        "grund": ("Zulässiger thermischer Dauerstrom (k-Faktor, ANSI 49). Ohne "
                  "Herstellerangabe bei Trafos typ. 1,10 (7UT613 Hdb. 2.9)."),
    },
    "tau_min": {
        "range": "1 ... 240 min, Trafo typ. 100 min (Voreinst. 100)",
        "grund": ("Thermische Zeitkonstante. Achtung: Eingabe in MINUTEN, nicht "
                  "Sekunden (häufige Fehlerquelle, 7UT613 Hdb. 2.9)."),
    },
    "I2_zul": {
        "range": "0,08 ... 0,16 I/InS (Voreinst. 0,16)",
        "grund": ("Dauernd zulässige Schieflast (Gegensystem I2, ANSI 46). Richtwert "
                  "für Transformatoren ca. 0,16."),
    },
    "k_S_I": {
        "range": "1,1 ... 1,4 (Voreinst. 1,20)",
        "grund": "Sicherheitsfaktor I> gegen die maximale Betriebslast.",
    },
    "k_S_IGG": {
        "range": "1,1 ... 1,4 (Voreinst. 1,20)",
        "grund": ("Sicherheitsfaktor I>> gegen den maximalen Durchgangsfehlerstrom "
                  "(7UT613 Hdb. 2.4, dort 1,2)."),
    },
    "gamma": {
        "range": "1,2 ... 2,0 (Voreinst. 1,50)",
        "grund": ("Empfindlichkeitsfaktor. Der minimale Fehlerstrom am Schutzgebiet-Ende "
                  "muss I> um diesen Faktor sicher übersteigen."),
    },
    "Inrush_Faktor": {
        "range": "6 ... 12 x IN (Voreinst. 8)",
        "grund": ("Trafo-Einschaltstromspitze als Vielfaches von IN. I>> muss darüber "
                  "liegen, da die 2. Harmonische nicht auf I>> wirkt."),
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# Spannungs- und Frequenzschutz (nur 7UT613/633 mit Spannungsmesseingang)
# Quelle: 7UT613/63x Handbuch, Abschnitte 2.11, 2.14, 2.15, 2.16
# ═══════════════════════════════════════════════════════════════════════════

# ── Spannungswandler-Eingabe (Gerätevariante mit VT) ─────────────────────────
VT_Sek_Optionen   = [100, 110, 200]   # Sekundaer-Nennspannung VT (verkettet) [V]

# ── 27 Unterspannungsschutz (Mitsystem, verkettete Werte) ────────────────────
# Projektierung Adr.152 UNTERSPANNUNG; Funktion Adr.5201 EIN/AUS
U_lt_def          = 0.75   # Adr.5212 U<  Ansprechwert  (Hdb. 2.14.2: 0,75-0,80) [x UnS]
t_U_lt_def        = 1.50   # Adr.5213 T U<                                       [s]
U_ltlt_def        = 0.65   # Adr.5215 U<< Ansprechwert (2. Stufe, tiefer)        [x UnS]
t_U_ltlt_def      = 0.50   # Adr.5216 T U<<                                      [s]

# ── 59 Überspannungsschutz (verkettete Werte) ────────────────────────────────
# Projektierung Adr.153 ÜBERSPANNUNG; Funktion Adr.5301 EIN/AUS
U_gt_def          = 1.15   # Adr.5312 U>  Ansprechwert (Hdb. 2.15.2: ~5 % ueber max. Betr.-U, Bsp. 1,20) [x UnS]
t_U_gt_def        = 2.00   # Adr.5313 T U>  (einige Sekunden)                    [s]
U_gtgt_def        = 1.30   # Adr.5315 U>> Ansprechwert (Hdb.: 1,3-1,5-fach)      [x UnS]
t_U_gtgt_def      = 0.30   # Adr.5316 T U>> (0,1-0,5 s)                          [s]
U_Rueckfall_def   = 0.98   # Adr.5317 Rueckfallverhaeltnis                       [-]

# ── 81 Frequenzschutz (4-stufig, Werte fuer fN = 50 Hz) ──────────────────────
# Projektierung Adr.156 FREQUENZSCHUTZ; Funktion Adr.5601 EIN/AUS
f_lt_def          = 49.0   # Adr.5611 f<   (Hdb. 2.16.2: Rueckgang bis ~48 Hz zulaessig) [Hz]
t_f_lt_def        = 1.50   # Adr.5641 T f<                                       [s]
f_ltlt_def        = 48.0   # Adr.5612 f<<                                        [Hz]
t_f_ltlt_def      = 0.50   # Adr.5642 T f<<                                      [s]
f_ltltlt_def      = 47.5   # Adr.5613 f<<<                                       [Hz]
t_f_ltltlt_def    = 0.30   # Adr.5643 T f<<<                                     [s]
f_gt_def          = 51.5   # Adr.5614 f>                                         [Hz]
t_f_gt_def        = 2.00   # Adr.5644 T f>                                       [s]
fN_default        = 50.0   # Nennfrequenz [Hz]

# ── 24 Übererregungsschutz U/f (bezogen auf Nenn-U/f) ────────────────────────
# Projektierung Adr.143 ÜBERERREGUNG; Funktion Adr.4301 EIN/AUS
Uf_gt_def         = 1.10   # Adr.4302 U/f >  Warnstufe (Hdb. 2.11.2: 1,00-1,20, Voreinst. 1,10) [x (U/f)N]
t_Uf_gt_def       = 10.0   # Adr.4303 T U/f >  (~10 s)                           [s]
Uf_gtgt_def       = 1.40   # Adr.4304 U/f >> Schnellauslösestufe                 [x (U/f)N]
t_Uf_gtgt_def     = 1.0    # Adr.4305 T U/f >> (~1 s)                            [s]

# ── HERST-Hinweise fuer die neuen Regler (ins HERST-Dict einfuegen) ──────────
HERST.update({
    "U_lt": {"range": "0,75 ... 0,80 x UnS (Voreinst. 0,75)",
             "grund": "Unterspannung U< etwas unter minimaler Betriebsspannung (7UT613 Hdb. 2.14.2)."},
    "U_gt": {"range": "~5 % ueber max. Betriebsspannung (Bsp. 1,20 x UnS)",
             "grund": "Stationaere Ueberspannung U> (7UT613 Hdb. 2.15.2)."},
    "U_gtgt": {"range": "1,30 ... 1,50 x UnS (Voreinst. 1,30)",
               "grund": "Schnelle Stufe U>> fuer kurzzeitige hohe Ueberspannung (7UT613 Hdb. 2.15.2)."},
    "f_lt": {"range": "~49 Hz (Rueckgang bis 48 Hz zulaessig)",
             "grund": "Unterfrequenzstufe f< zur Netz-/Kraftwerksueberwachung (7UT613 Hdb. 2.16.2)."},
    "Uf_gt": {"range": "1,00 ... 1,20 x (U/f)N (Voreinst. 1,10)",
              "grund": "Dauernd zulaessige Induktion B/BN, zugleich Warnstufe (7UT613 Hdb. 2.11.2)."},
})


# ── 50BF Leistungsschalterversagerschutz ─────────────────────────────────────
# Projektierung Adr.170 SCHALTERVERSAG.; Funktion Adr.7001 EIN/AUS
# Zuordnung Adr.470 SCHALTERV ZUORD; Zeiten Adr.7015 (T1), 7016 (T2)
I_BF_def          = 0.10   # Stromflusskriterium (Faktor x IN, typ. SVS-Wert) [x IN]
t_LS_aus_def      = 0.060  # max. Ausschaltzeit Leistungsschalter             [s]
t_RF_strom_def    = 0.025  # Rueckfallzeit Stromflusserfassung 7UT613         [s]
t_sich_BF_def     = 0.065  # Sicherheitszuschlag                              [s]
zweistufig_def    = False  # False = nur T2 (Sammelschiene); True = T1 + T2

HERST.update({
    "I_BF": {"range": "~0,10 x IN (typ.)",
             "grund": "Stromflusskriterium SVS, sicher ueber Laststrom-Rueckfall (7UT613 Hdb. 2.17)."},
    "T2_BF": {"range": "t_LS-aus + t_Rueckfall + t_Sicherheit (~0,15 s typ.)",
              "grund": "Verzoegerung T2 bis zur Sammelschienen-Ausloesung (7UT613 Hdb. 2.17, Adr.7016)."},
})


# ── Eintrag-Adressen für die Pin-Anzeige unter den Reglern ───────────────────
# Echte DIGSI-Parameter erhalten ihre Adresse. Reine Engineering-Margen
# (k_S_I, k_S_IGG, gamma, Inrush_Faktor) bleiben ohne Adresse, da sie tool-intern
# in die Sollwertberechnung einfließen und nicht direkt ins Gerät eingetragen werden.
_EINTRAG_ADRESSEN = {
    "I_DIFF": "Adr.1221", "I_DIFF_HH": "Adr.1231",
    "Steigung_1": "Adr.1241A", "Steigung_2": "Adr.1243A", "Fusspunkt_2": "Adr.1244A",
    "Harm_2": "Adr.1271",
    "f_I_Ph": "Adr.2011", "t_I_Ph": "Adr.2013",
    "f_I_Ph_HH_OS": "Adr.2014", "f_I_Ph_HH_US": "Adr.2014 (Seite 2)", "t_I_Ph_HH": "Adr.2016",
    "k_Faktor": "Adr.4202", "tau_min": "Adr.4203", "I2_zul": "Adr.4032",
    "U_lt": "Adr.5212 (bez.) / 5211 (V)", "U_gt": "Adr.5312 (bez.) / 5311 (V)",
    "U_gtgt": "Adr.5315 (bez.) / 5314 (V)", "f_lt": "Adr.5611",
    "Uf_gt": "Adr.4302", "I_BF": "LS-I> Stromflussüberw. (Adr.7015/7016 für T1/T2)",
    "T2_BF": "Adr.7016",
}
for _k, _a in _EINTRAG_ADRESSEN.items():
    if _k in HERST:
        HERST[_k]["adr"] = _a
