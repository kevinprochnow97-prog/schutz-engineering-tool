"""
konstanten_gen.py — Voreinstellungen und Plausibilitaets-Schwellwerte (Generator)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Single Source of Truth fuer alle SIPROTEC-7UM62-Werksvoreinstellungen,
Engineering-Margen und Plausibilitaetsgrenzen des Generator-Tabs.
Alle Werte sind frei aenderbar.

Quellen: SIPROTEC 7UM62 Handbuch C53000-G1100-C149-C (Ausgabe 08.2018),
         Querverweis SIPROTEC 7UT613 (Differentialmethodik),
         IEC 60255-151, IEC 60255-187-3, VDE-FNN-Leitfaden.

Hinweis zu Adressen: 7UM62-DIGSI-Adressen (Adr.), Adressen mit "A" sind nur
unter "Weitere Parameter" sichtbar.
"""

# ── 87G Staenderdifferentialschutz (7UM62, Adr. 20xx) ────────────────────────
I_DIFF_def        = 0.20   # Adr.2021  Ansprechwert I-DIFF>            [I/InO]
T_I_DIFF_def      = 0.00   # Adr.2026A Verzoegerung T I-DIFF>          [s]
I_DIFF_HH_def     = 5.00   # Adr.2031  Ansprechwert I-DIFF>> (Schnell) [I/InO]
T_I_DIFF_HH_def   = 0.00   # Adr.2036A Verzoegerung T I-DIFF>>         [s]
Steigung_1_def    = 0.25   # Adr.2041A Steigung 1                      [-]
Fusspunkt_1_def   = 0.00   # Adr.2042A Fusspunkt 1                     [I/InO]
Steigung_2_def    = 0.50   # Adr.2043A Steigung 2                      [-]
Fusspunkt_2_def   = 2.50   # Adr.2044A Fusspunkt 2                     [I/InO]
Anlauf_Stab_def   = 0.10   # Adr.2051A ISTAB Anlauferkennung           [I/InO]
Anlauf_Faktor_def = 1.00   # Adr.2052A Ansprechwert-Erhoehung Anlauf   [-]
Max_Anlaufzeit_def= 5.00   # Adr.2053  Max. Anlaufzeit                 [s]
EXF_Stab_def      = 4.00   # Adr.2061A ISTAB Zusatzstab. ext. Fehler   [I/InO]
Harm_2_def        = 0.15   # Adr.2071  2.Harmonische (Inrush-Stab.)    [-]
Harm_n_def        = 0.30   # Adr.2076  n.Harmonische (Stab.)           [-]

# ── 50/51 UMZ I> mit Unterspannungshaltung (Adr. 12xx) ──────────────────────
f_I_Ph_def        = 1.40   # Faktor I> (x IN_Masch)                    [I/InS]
t_I_Ph_def        = 3.00   # Adr.1203 Verzoegerung T I>                [s]
U_Haltung_def     = 80.0   # Adr.1205 U< (Unterspannungshaltung)       [V]
t_Haltung_def     = 4.00   # Adr.1206 T-HALTUNG                        [s]
RV_I_def          = 0.95   # Adr.1207A Rueckfallverhaeltnis            [-]

# ── 50 UMZ I>> Hochstromstufe (Adr. 13xx) ────────────────────────────────────
f_I_Ph_HH_def     = 4.00   # Faktor I>> (x IN_Masch)                   [I/InS]
t_I_Ph_HH_def     = 0.10   # Adr.1303 Verzoegerung T I>>               [s]

# ── 51V AMZ spannungsabhaengig (Adr. 14xx) ──────────────────────────────────
f_Ip_def          = 1.00   # Adr.1402 Ip (x IN_Masch)                  [I/InS]
T_Ip_def          = 0.50   # Adr.1403 Zeitmultiplikator T Ip (IEC)     [s]
U_AMZ_def         = 75.0   # Adr.1408 U< (Spannungssteuerung)          [V]
Kennlinie_AMZ_def = "Invers (IEC, normal inverse)"  # Adr.1405

# ── 49 Thermischer Ueberlastschutz (Adr. 16xx) ──────────────────────────────
# ACHTUNG: Zeitkonstante beim 7UM62 in SEKUNDEN (anders als 7UT613 = Minuten!)
k_Faktor_def      = 1.11   # Adr.1602 k-Faktor                         [x IN]
tau_Gen_def       = 600.0  # Adr.1603 Zeitkonstante  <- SEKUNDEN!      [s]
Theta_Warn_def    = 0.90   # Adr.1604 Thermische Warnstufe             [-]
I_Warn_def        = 1.00   # Adr.1610A Stromwarnstufe (x IN_sek)       [-]
Ktau_Faktor_def   = 1.00   # Adr.1612A Kτ Stillstandsverlaengerung     [-]

# ── 46 Schieflastschutz (Adr. 17xx) ──────────────────────────────────────────
I2_zul_def        = 0.106  # Adr.1702 Dauernd zul. Schieflast I2 ZUL.  [-]  (10,6 %)
t_Warn_I2_def     = 20.0   # Adr.1703 Verzoegerung Warnstufe           [s]
Faktor_K_def      = 18.7   # Adr.1704 Unsymmetriefaktor K              [s]
t_Abkuehl_def     = 1650.0 # Adr.1705 Abkuehlzeit                      [s]
I2_HH_def         = 0.60   # Adr.1706 I2>> Anregeschwelle              [-]  (60 %)
t_I2_HH_def       = 3.00   # Adr.1707 Verzoegerung T I2>>              [s]

# ── 40 Untererregungsschutz (Adr. 30xx) ──────────────────────────────────────
xd_Sicherheit     = 1.05   # Sicherheitsfaktor fuer 1/xd KL.1
Winkel_1_def      = 80     # Adr.3003 WINKEL 1 (statische Stab.)       [Grad]
T_KL1_def         = 10.00  # Adr.3004 T KL 1                           [s]
Winkel_2_def      = 90     # Adr.3006 WINKEL 2                         [Grad]
T_KL2_def         = 10.00  # Adr.3007 T KL 2                           [s]
xd_KL2_Faktor     = 0.90   # 1/xd KL.2 = 0,9 * (1/xd KL.1)
xd_KL3_def        = 1.10   # Adr.3008 1/xd KL.3 (dyn. Stab.)           [-]
Winkel_3_def      = 90     # Adr.3009 WINKEL 3                         [Grad]
T_KL3_def         = 0.30   # Adr.3010 T KL 3                           [s]
T_kurz_Uerr_def   = 0.50   # Adr.3011 T KURZ U< (Erregerausfall)       [s]

# ── 32 Rueckleistungsschutz (Adr. 31xx) ──────────────────────────────────────
# Prueck> als negativer Wert in % der sek. Nennscheinleistung SNsek.
Prueck_def        = -1.93  # Adr.3102 Prueck>                          [%]
t_o_SSchl_def     = 10.00  # Adr.3103 T o.S-SCHL. (ohne Schnellschluss)[s]
t_m_SSchl_def     = 1.00   # Adr.3104 T m.S-SCHL. (mit Schnellschluss) [s]
# Richtwerte Schleppleistung PRueck/SN je Antrieb (Mittelwerte fuer Empfehlung):
PRueck_Dampf      = -2.0   # Dampfturbine     1...3 %
PRueck_Gas        = -5.0   # Gasturbine       3...30 %
PRueck_Diesel     = -8.0   # Dieselantrieb    > 5 %

# ── 24 Uebererregungsschutz U/f (Adr. 43xx) ─────────────────────────────────
Uf_Warn_def       = 1.10   # Adr.4302 U/f >  (Warnstufe)               [-]
t_Uf_Warn_def     = 10.00  # Adr.4303 T U/f>                           [s]
Uf_Aus_def        = 1.40   # Adr.4304 U/f >> (Ausloesestufe)           [-]
t_Uf_Aus_def      = 1.00   # Adr.4305 T U/f >>                         [s]

# ── 27 Unterspannungsschutz (Adr. 40xx) ──────────────────────────────────────
U_klein_def       = 75.0   # Adr.4002 U<                               [V]
t_U_klein_def     = 3.00   # Adr.4003 T U<                             [s]
U_kleinklein_def  = 65.0   # Adr.4004 U<<                              [V]
t_U_kleinklein_def= 0.50   # Adr.4005 T U<<                            [s]

# ── 59 Ueberspannungsschutz (Adr. 41xx) ──────────────────────────────────────
U_gross_def       = 115.0  # Adr.4102 U>                               [V]
t_U_gross_def     = 3.00   # Adr.4103 T U>                             [s]
U_grossgross_def  = 130.0  # Adr.4104 U>>                              [V]
t_U_grossgross_def= 0.50   # Adr.4105 T U>>                            [s]

# ── 81 Frequenzschutz (Adr. 42xx) ────────────────────────────────────────────
# Voreinstellungen fuer fN = 50 Hz (Markt Europa). 60-Hz-Werte in Klammern im Hdb.
f1_def   = 48.00  # Adr.4202 f1 50Hz / Adr.4203 f1 60Hz  [Hz]
t_f1_def = 1.00   # Adr.4204 T F1                         [s]
f2_def   = 47.00  # Adr.4205 f2 50Hz / Adr.4206 f2 60Hz  [Hz]
t_f2_def = 6.00   # Adr.4207 T F2                         [s]
f3_def   = 49.50  # Adr.4208 f3 50Hz / Adr.4209 f3 60Hz  [Hz]
t_f3_def = 20.00  # Adr.4210 T F3                         [s]
f4_def   = 52.00  # Adr.4211 f4 50Hz / Adr.4212 f4 60Hz  [Hz]
t_f4_def = 10.00  # Adr.4213 T F4                         [s]
# 60-Hz-Voreinstellungen
f1_60, f2_60, f3_60, f4_60 = 58.00, 57.00, 59.50, 62.00

# ── 59N / 64G-1  Staendererdschlussschutz 90 % (U0) (Adr. 50xx) ─────────────
U0_def            = 10.0   # Adr.5002 U0>                              [V]
I3I0_def          = 5.0    # Adr.5003 3I0>                             [mA]
Winkel_SES_def    = 15     # Adr.5004 WINKEL (Richtung)                [Grad]
Winkel_SES_isol   = 90     # isoliertes Netz ohne Erdungstrafo -> sin-phi ~90 Grad
t_SES_def         = 0.30   # Adr.5005 T SES                            [s]
U0_voll_V         = 100.0  # U0 bei voller Verlagerung (e-n-Wicklung)  [V]

# ── 64R  Laeufererdschlussschutz (R, fn) (Adr. 60xx) ─────────────────────────
RE_Warn_def       = 10.0   # Adr.6002 RE WARN                          [kOhm]
RE_Aus_def        = 2.0    # Adr.6003 RE AUS                           [kOhm]
t_RE_Warn_def     = 10.00  # Adr.6004 T RE WARN                        [s]
t_RE_Aus_def      = 0.50   # Adr.6005 T RE AUS                         [s]

# ── Globale Engineering-Margen (Reserveschutz / Empfindlichkeit) ────────────
k_S_I             = 1.20   # I>  = k_S_I  * I_max_Last                  [-]
k_S_IGG           = 1.20   # I>> bzgl. max. Durchgangsfehler           [-]
gamma_Ikmin       = 1.50   # I_k_min(Ende) >= gamma * I>               [-]

# ── Plausibilitaets-Schwellwerte ─────────────────────────────────────────────
Sn_min_87G        = 1.0    # Mindest-Sn fuer 87G-Sinnhaftigkeit        [MVA]
Anpass_min        = 0.5    # Untere Grenze STW-Anpassungsfaktor I_an    [-]
Anpass_max        = 2.0    # Obere Grenze STW-Anpassungsfaktor I_an     [-]
k_Faktor_min      = 1.0    # Plausibilitaetsgrenze k-Faktor (unten)     [-]
k_Faktor_max      = 1.5    # Plausibilitaetsgrenze k-Faktor (oben)      [-]
xd_strich_min     = 0.10   # Plausibilitaetsgrenze x'd (unten)          [p.u.]
xd_strich_max     = 0.40   # Plausibilitaetsgrenze x'd (oben)           [p.u.]
xd_min            = 0.8    # Plausibilitaetsgrenze xd (unten)           [p.u.]
xd_max            = 3.5    # Plausibilitaetsgrenze xd (oben)            [p.u.]
Toleranz_Empfehlung = 0.20 # Abweichung Eingabe/Empfehlung -> Hinweis   [-]

# ── Auswahl-Optionen (steuern Funktionsauswahl/Empfehlungen) ────────────────
ANSCHLUSS_OPTIONEN = [
    "Direkt auf MS-Sammelschiene",
    "Blockschaltung (Maschinentrafo)",
]
STERNPUNKT_GEN_OPTIONEN = [
    "Isoliert",
    "Hochohmig (Erdungstrafo / Petersen)",
    "Niederohmig geerdet",
]
STERNPUNKT_GEN_NICHT_NIEDEROHMIG = ["Isoliert", "Hochohmig (Erdungstrafo / Petersen)"]
TURBINEN_OPTIONEN = ["Dampfturbine", "Gasturbine", "Dieselantrieb"]
FN_OPTIONEN = [50, 60]


# ═════════════════════════════════════════════════════════════════════════════
# HERSTELLER-HINWEISE (Wert/Range + Begruendung je Parameter)
# Quelle: SIPROTEC 7UM62 Handbuch C53000-G1100-C149-C; Querverweis 7UT613.
# ═════════════════════════════════════════════════════════════════════════════

HERST = {
    "I_DIFF": {
        "range": "0,05 ... 2,00 I/InO (Voreinst. 0,20)",
        "grund": ("Ansprechwert des Staenderdifferentialschutzes. 0,20 deckt kleine "
                  "Windungsschluesse ab; tiefer als beim Trafo moeglich, da keine "
                  "Stufensteller-Fehler auftreten (7UM62 Hdb. 2.9, Adr.2021)."),
    },
    "I_DIFF_HH": {
        "range": "ca. 1/x'd, typ. (3 ... 7) x IN  (Voreinst. 5,0)",
        "grund": ("Unstabilisierte Schnellausloesestufe. Muss oberhalb des max. "
                  "durchfliessenden Fehlerstroms liegen; bei Maschinen aus der "
                  "transienten Reaktanz x'd: I-DIFF>> ~ 1/x'd (7UM62 Hdb. 2.9, Adr.2031)."),
    },
    "Steigung_1": {
        "range": "0,10 ... 0,50 (Voreinst. 0,25)",
        "grund": ("Neigung des ersten Kennlinienastes. Beruecksichtigt Wandlerfehler "
                  "im unteren Strombereich (7UM62 Hdb. 2.9, Adr.2041A)."),
    },
    "Steigung_2": {
        "range": "0,25 ... 0,95 (Voreinst. 0,50)",
        "grund": ("Neigung ab Fusspunkt 2 — hoehere Stabilisierung gegen Wandler- "
                  "saettigung bei grossen Durchgangsfehlern (7UM62 Hdb. 2.9, Adr.2043A)."),
    },
    "Fusspunkt_2": {
        "range": "0,00 ... 10,00 I/InO (Voreinst. 2,50)",
        "grund": ("Knickpunkt zum steileren Kennlinienast (7UM62 Hdb. 2.9, Adr.2044A)."),
    },
    "Harm_2": {
        "range": "10 ... 80 % (Voreinst. 15 %)",
        "grund": ("Inrush-Stabilisierung ueber 2. Harmonische — relevant beim "
                  "Zuschalten eines Blocktrafos (7UM62 Hdb. 2.9, Adr.2071)."),
    },
    "f_I_Ph": {
        "range": "ca. 1,2 ... 1,5 x IN (Voreinst. 1,40)",
        "grund": ("Reserve-Ueberstromstufe I>. Oberhalb der max. Betriebslast; beim "
                  "Generator mit Unterspannungshaltung kombinierbar (7UM62 Hdb. 2.3, Adr.1202)."),
    },
    "t_I_Ph": {
        "range": "aus Staffelplan, typ. 1 ... 3 s (Voreinst. 3,0 s)",
        "grund": ("Verzoegerung I>. Generatorseitig bewusst lang, da Reserveschutz "
                  "(7UM62 Hdb. 2.3, Adr.1203)."),
    },
    "U_Haltung": {
        "range": "10 ... 125 V (Voreinst. 80 V)",
        "grund": ("Unterspannungshaltung: haelt die I>-Anregung bei einbrechender "
                  "Spannung gespeichert, damit der abklingende Generator-KS-Strom "
                  "(1/xd) trotzdem erfasst wird (7UM62 Hdb. 2.3, Adr.1205)."),
    },
    "f_I_Ph_HH": {
        "range": "typ. 3 ... 7 x IN (Voreinst. 4,0)",
        "grund": ("Hochstromstufe I>> als schneller Kurzschlussschutz, oberhalb des "
                  "subtransienten Speisestroms benachbarter Quellen (7UM62 Hdb. 2.4, Adr.1302)."),
    },
    "t_I_Ph_HH": {
        "range": "0,0 ... 0,1 s (Voreinst. 0,10 s)",
        "grund": ("Kurze Sicherheitsverzoegerung der Hochstromstufe (7UM62 Hdb. 2.4, Adr.1303)."),
    },
    "f_Ip": {
        "range": "0,10 ... 4,00 A bzw. ~1,0 x IN (Voreinst. 1,0)",
        "grund": ("Anregewert der spannungsabhaengigen AMZ-Stufe (51V). Mit aktiver "
                  "Spannungssteuerung sinkt die Schwelle bei Spannungseinbruch "
                  "(7UM62 Hdb. 2.5, Adr.1402)."),
    },
    "U_AMZ": {
        "range": "10 ... 125 V (Voreinst. 75 V)",
        "grund": ("Spannungsschwelle der 51V-Steuerung. Unterhalb dieser Spannung "
                  "wird die AMZ-Kennlinie empfindlicher / freigegeben (7UM62 Hdb. 2.5, Adr.1408)."),
    },
    "k_Faktor": {
        "range": "0,10 ... 4,00 x IN (Voreinst. 1,11)",
        "grund": ("Zulaessiger thermischer Dauerstrom (ANSI 49), bezogen auf 40 Grad C "
                  "Umgebung (7UM62 Hdb. 2.6, Adr.1602)."),
    },
    "tau_s": {
        "range": "30 ... 32000 s, Maschine typ. 600 s (Voreinst. 600)",
        "grund": ("Thermische Zeitkonstante. ACHTUNG: beim 7UM62 in SEKUNDEN "
                  "(beim 7UT613 in Minuten!) — haeufige Verwechslung (7UM62 Hdb. 2.6, Adr.1603)."),
    },
    "I2_zul": {
        "range": "3,0 ... 30,0 % (Voreinst. 10,6 %)",
        "grund": ("Dauernd zul. Schieflast (Gegensystem I2, ANSI 46). Maschinen sind "
                  "gegensystemempfindlich — Richtwert ~10 % (7UM62 Hdb. 2.7, Adr.1702)."),
    },
    "I2_HH": {
        "range": "10 ... 200 % (Voreinst. 60 %)",
        "grund": ("Unabhaengige Schnellstufe I2>>. ~60 % trennt Phasenausfall (<58 %) "
                  "vom 2-poligen Kurzschluss (7UM62 Hdb. 2.7, Adr.1706)."),
    },
    "Winkel_1": {
        "range": "50 ... 120 Grad (Voreinst. 80 Grad)",
        "grund": ("Neigung Kennlinie 1 (40). Winkel der Untererregungsbegrenzung bzw. "
                  "der statischen Stabilitaetsgrenze, typ. 60 ... 80 Grad (7UM62 Hdb. 2.11, Adr.3003)."),
    },
    "xd_KL3": {
        "range": "0,20 ... 3,00 (Voreinst. 1,10)",
        "grund": ("1/xd Kennlinie 3 (dyn. Stabilitaet). Wert zwischen xd und x'd, "
                  "jedoch > 1 (7UM62 Hdb. 2.11, Adr.3008)."),
    },
    "Prueck": {
        "range": "-30,00 ... -0,50 % (negativ; Voreinst. -1,93 %)",
        "grund": ("Rueckleistungsschwelle (ANSI 32), ~0,5 x Schleppleistung. "
                  "Dampf 1-3 %, Gas 3-30 %, Diesel >5 % von SN (7UM62 Hdb. 2.12, Adr.3102)."),
    },
    "Uf_Warn": {
        "range": "1,00 ... 1,20 (Voreinst. 1,10)",
        "grund": ("U/f-Warnstufe (ANSI 24). 1,10 schuetzt Eisen vor Saettigung beim "
                  "Hochfahren/Lastabwurf (7UM62 Hdb. 2.19, Adr.4302)."),
    },
    "Uf_Aus": {
        "range": "1,00 ... 1,40 (Voreinst. 1,40)",
        "grund": ("U/f-Ausloesestufe — Schnellabschaltung bei starker Uebererregung "
                  "(7UM62 Hdb. 2.19, Adr.4304)."),
    },
    "U0": {
        "range": "2,0 ... 125,0 V (Voreinst. 10,0 V)",
        "grund": ("Verlagerungsspannungs-Schwelle (90 % Staendererdschluss). 10 V bei "
                  "100 V voller Verlagerung -> 90 % Schutzbereich (7UM62 Hdb. 2.23, Adr.5002)."),
    },
    "RE_Aus": {
        "range": "1,0 ... 5,0 kOhm (Voreinst. 2,0 kOhm)",
        "grund": ("Ausloeseschwelle Laeufererdschluss (64R). Unter 2 kOhm wird ein "
                  "Erdschluss der Erregerwicklung angenommen (7UM62 Hdb. 2.30, Adr.6003)."),
    },
    "U_klein": {
    "range": "10,0 ... 125,0 V (Voreinst. 75,0 V)",
    "grund": ("Unterspannungs-Schwelle (ANSI 27). Schutz vor Netzausfaellen und "
              "Spannungsabsenkungen. Typisch 0,9 × UN (7UM62 Hdb. 2.17, Adr.4002)."),
},
"U_kleinklein": {
    "range": "10,0 ... 125,0 V (Voreinst. 65,0 V)",
    "grund": ("Zweite Unterspannungsstufe (tiefere Auslösesch., schneller). Typically "
              "0,8 × UN oder als independent verzoegerte Stufe (7UM62 Hdb. 2.17, Adr.4004)."),
},
"U_gross": {
    "range": "30,0 ... 170,0 V (Voreinst. 115,0 V)",
    "grund": ("Ueberspannungs-Schwelle (ANSI 59). Schutz vor Netzhochfahren und "
              "Fehlerloeschung. Typisch 1,1 × UN (7UM62 Hdb. 2.18, Adr.4102)."),
},
"U_grossgross": {
    "range": "30,0 ... 170,0 V (Voreinst. 130,0 V)",
    "grund": ("Zweite Ueberspannungsstufe (schneller Schutz bei kritischen "
              "Ueberspaennungen). Typically 1,2 × UN (7UM62 Hdb. 2.18, Adr.4104)."),
},
}


# ── Adressen-Zuordnung fuer die Regler-Captions (eine Adresse je Parameter) ──
# Wird in tab_gen._hreg() als "Eintragen unter: Adr.XXXX" direkt am Regler gezeigt.
_HERST_ADR = {
    "I_DIFF": "Adr.2021", "I_DIFF_HH": "Adr.2031", "Steigung_1": "Adr.2041A",
    "Steigung_2": "Adr.2043A", "Fusspunkt_2": "Adr.2044A", "Harm_2": "Adr.2071",
    "f_I_Ph": "Adr.1202", "t_I_Ph": "Adr.1203", "U_Haltung": "Adr.1205",
    "f_I_Ph_HH": "Adr.1302", "t_I_Ph_HH": "Adr.1303", "f_Ip": "Adr.1402",
    "U_AMZ": "Adr.1408", "k_Faktor": "Adr.1602", "tau_s": "Adr.1603",
    "I2_zul": "Adr.1702", "I2_HH": "Adr.1706", "Winkel_1": "Adr.3003",
    "xd_KL3": "Adr.3008", "Prueck": "Adr.3102", "Uf_Warn": "Adr.4302",
    "Uf_Aus": "Adr.4304", "U0": "Adr.5002", "RE_Aus": "Adr.6003","U_klein": "Adr.4002", "U_kleinklein": "Adr.4004",
"U_gross": "Adr.4102", "U_grossgross": "Adr.4104",
}
for _k, _a in _HERST_ADR.items():
    if _k in HERST:
        HERST[_k]["adr"] = _a
