"""
konstanten_motor.py — Voreinstellungen und Plausibilitaets-Schwellwerte (Motor)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Single Source of Truth fuer alle SIPROTEC-7SJ66-Werksvoreinstellungen,
Engineering-Margen und Plausibilitaetsgrenzen des Motor-Tabs.
Alle Werte sind frei aenderbar.

Quellen: SIPROTEC 7SJ66 Handbuch C53000-B1140-C383-D (Ausgabe 09.2023),
         IEC 60034-1 (zul. Gegensystembelastung Asynchronmaschinen),
         IEC 60255-151, IEC 60255-8 (thermisches Abbild), VDE-FNN-Leitfaden.

Hinweis zu Adressen: 7SJ66-DIGSI-Adressen (Adr.). Adressen mit "A" sind nur
unter "Weitere Parameter" sichtbar.

WICHTIG zur Zeitkonstante tau (ANSI 49):
Das 7SJ66 erwartet tau in MINUTEN (Adr.4203) — wie das 7UT613 (Trafo),
aber im Gegensatz zum 7UM62 (Generator, Sekunden!). Verwechslungsgefahr.
"""

# ── 49 Thermischer Ueberlastschutz (7SJ66, Adr. 42xx) ────────────────────────
# Zeitkonstante in MINUTEN (Adr.4203), nicht Sekunden!
k_Faktor_def      = 1.10   # Adr.4202  49 K-FAKTOR (= I_max/IN)            [x IN]
tau_Mot_def       = 100.0  # Adr.4203  Zeitkonstante  <- MINUTEN!         [min]
Theta_Warn_def    = 0.90   # Adr.4204  49 Theta-Warnstufe                 [-]
I_Warn_def        = 1.00   # Adr.4205  I ALARM (Stromwarnstufe, sek.)     [A]
Ktau_Stop_def     = 1.0    # Adr.4207A Ktau bei Motorstillstand           [-]
T_Emergency_def   = 100.0  # Adr.4208A T EMERGENCY (Notbetrieb)           [s]
Temp_Rise_def     = 100.0  # Adr.4209  Uebertemperatur bei IN             [Grad C]

# ── 48 Motoranlaufueberwachung (Adr. 41xx) ───────────────────────────────────
Startup_Current_def = 5.00 # Adr.4102  STARTUP CURRENT (sek.)             [A]
Startup_Time_def    = 10.0 # Adr.4103  STARTUP TIME (Anlaufzeit-Schwelle) [s]
Lock_Rotor_Time_def = 2.0  # Adr.4104  LOCK ROTOR TIME (zul. Blockierzeit)[s]
Startup_T_Warm_def  = 10.0 # Adr.4105  STARTUP T WARM (warmer Motor)      [s]
Temp_Cold_Motor_def = 0    # Adr.4106  TEMP.COLD MOTOR                    [%]

# ── 1107 Motoranlauf-Erkennung (gemeinsame Schwelle 48/49) ───────────────────
I_Motor_Start_def = 2.50   # Adr.1107  I MOTOR START (sek.)               [A]

# ── 66 Wiedereinschaltsperre / Anlaufzaehler (Adr. 43xx) ─────────────────────
IStart_IMOTnom_def= 4.90   # Adr.4302  IStart/IMOTnom (Anlaufstromverh.)  [-]
T_Start_Max_def   = 10     # Adr.4303  T START MAX (max. zul. Anlaufzeit) [s]
T_Equal_def       = 1.0    # Adr.4304  T Equal (Temperaturausgleichszeit) [min]
I_Mot_Nominal_def = 1.00   # Adr.4305  I MOTOR NOMINAL (sek.)             [A]
Max_Warm_Starts_def = 2    # Adr.4306  MAX.WARM STARTS                    [-]
Cold_minus_Warm_def = 1    # Adr.4307  #COLD-#WARM                        [-]
Ktau_Stop_66_def  = 5.0    # Adr.4308  Ktau bei Stillstand                [-]
Ktau_Run_66_def   = 2.0    # Adr.4309  Ktau bei Betrieb                   [-]
T_Min_Inhibit_def = 6.0    # Adr.4310  T MIN. INHIBIT (Mindestsperrzeit)  [min]

# ── 51M Lastsprung-/Load-Jam-Schutz (Adr. 44xx) ──────────────────────────────
# Auslöseschwelle typ. unterhalb Anlaufstrom bei ~2 x IN_Motor
LoadJam_I_def     = 2.00   # Adr.4402  Load Jam I> (sek.)                 [A]
LoadJam_t_def     = 1.00   # Adr.4403  TRIP DELAY                         [s]
LoadJam_IAlarm_def= 1.80   # Adr.4404  I Alarm (~75 % der Ausloesestufe)  [A]
LoadJam_tAlarm_def= 1.00   # Adr.4405  ALARM DELAY                        [s]
LoadJam_TStartBlk_def = 10.00  # Adr.4406  T Start Blk. (= 2 x Anlaufzeit)[s]
LoadJam_Faktor    = 2.0    # Auslegungsfaktor Load Jam I> = 2 x IN_Motor  [x IN]
LoadJam_Alarm_Faktor = 0.75# I Alarm = 0,75 x Load Jam I>                 [-]

# ── 46 Schieflastschutz / Gegensystem (Adr. 40xx) ────────────────────────────
# I2-Richtwerte fuer Asynchronmaschinen nach IEC 60034-1.
I2_dauer_def      = 0.11   # Adr.4002  46-1 dauernd zul. I2 (= 11 %)      [-]
t_46_1_def        = 1.50   # Adr.4003  46-1 DELAY                         [s]
I2_kurz_def       = 0.55   # Adr.4004  46-2 kurzzeitig zul. I2 (= 55 %)   [-]
t_46_2_def        = 1.50   # Adr.4005  46-2 DELAY                         [s]
Kennlinie_46_def  = "Extrem invers (IEC)"  # Adr.4006

# ── 50/51 Phasen-Ueberstromzeitschutz (Adr. 12xx) ────────────────────────────
# 50-2 Hochstromstufe (Kurzschluss), 50-1 / 51 als Reserve.
f_50_2_def        = 4.00   # 50-2 Ansprechwert (x IN_Motor)               [x IN]
t_50_2_def        = 0.00   # Adr.1203  50-2 DELAY (motorseitig 0 s!)      [s]
f_50_1_def        = 2.50   # 50-1 Ansprechwert (x IN_Motor)               [x IN]
t_50_1_def        = 0.50   # Adr.1205  50-1 DELAY                         [s]
f_51_def          = 1.20   # 51 Ansprechwert (x IN_Motor)                 [x IN]
T_51_def          = 0.50   # Adr.1208  51 TIME DIAL (IEC)                 [s]
Kennlinie_51_def  = "Invers (IEC, normal inverse)"  # Adr.1211
# Motorseitige 50-2-Auslegung (7SJ66 Hdb. 2.2): 1,6 x I_Anlauf < 50-2 < Ik,2pol,min
f_50_2_Anlauf_Sicherheit = 1.6  # Sicherheitsfaktor ueber Anlaufstrom     [-]

# ── 37 Unterstrom / Lastverlust (Setpoint, DIGSI-Matrix) ─────────────────────
# 37-1< ist kein 4xxx-Parameter, sondern ein Messwert-Setpoint (% von IN).
I_unter_pct_def   = 30.0   # 37-1< Ansprechwert in % von IN_Motor          [%]
t_unter_def       = 2.00   # Verzoegerung Lastverlust                      [s]

# ── Motor-Kenndaten (Datenblatt-Defaults Asynchronmaschine MS) ──────────────
cos_phi_def       = 0.88   # Leistungsfaktor                               [-]
eta_def           = 0.95   # Wirkungsgrad                                  [-]
I_Anlauf_Verh_def = 6.0    # Anlaufstromverhaeltnis I_A/IN                  [-]
t_Anlauf_def      = 8.0    # Anlaufzeit                                     [s]
t_LR_zul_def      = 10.0   # zul. Blockierzeit (warm), permissible LR-time [s]
I_max_Verh_def    = 1.10   # Dauer-Ueberlastfaktor I_max/IN                 [-]

# ── Globale Engineering-Margen ───────────────────────────────────────────────
k_S_51            = 1.20   # 51 = k_S_51 * I_max_Last (Reserve-Ueberstrom) [-]
gamma_Ikmin       = 1.50   # I_k_min(Ende) >= gamma * Anregewert            [-]
I_MotStart_unten  = 1.20   # I MOTOR START > I_MotStart_unten * IN_Motor    [-]
I_MotStart_oben   = 0.90   # I MOTOR START < I_MotStart_oben * I_Anlauf     [-]

# ── Plausibilitaets-Schwellwerte ─────────────────────────────────────────────
Pn_min            = 1.0    # Mindest-Pn (Plausibilitaet)                   [kW]
Anpass_min        = 0.5    # Untere Grenze STW-Anpassungsfaktor I_an       [-]
Anpass_max        = 2.0    # Obere Grenze STW-Anpassungsfaktor I_an        [-]
k_Faktor_min      = 1.0    # Plausibilitaetsgrenze k-Faktor (unten)        [-]
k_Faktor_max      = 1.2    # Plausibilitaetsgrenze k-Faktor (oben, Motor)  [-]
I2_dauer_min      = 0.05   # Plausibilitaetsgrenze I2-Dauer (unten)        [-]
I2_dauer_max      = 0.15   # Plausibilitaetsgrenze I2-Dauer (oben)         [-]
I_Anlauf_min      = 4.0    # Plausibilitaetsgrenze I_A/IN (unten)          [-]
I_Anlauf_max      = 8.5    # Plausibilitaetsgrenze I_A/IN (oben)           [-]
Toleranz_Empfehlung = 0.20 # Abweichung Eingabe/Empfehlung -> Hinweis      [-]

# ── Auswahl-Optionen ─────────────────────────────────────────────────────────
STERNPUNKT_NETZ_OPTIONEN = [
    "Isoliert",
    "Kompensiert (Petersen-Spule)",
    "Niederohmig geerdet",
]
ANTRIEBSART_OPTIONEN = [
    "Pumpe / Lüfter (quadratisches Lastmoment)",
    "Kompressor / Mühle (konstantes Lastmoment)",
    "Schweranlauf (hohes Trägheitsmoment)",
]
KUEHLUNG_OPTIONEN = ["Eigenbelüftet (selbstkühlend)", "Fremdbelüftet"]


# ═════════════════════════════════════════════════════════════════════════════
# HERSTELLER-HINWEISE (Wert/Range + Begruendung je Parameter)
# Quelle: SIPROTEC 7SJ66 Handbuch C53000-B1140-C383-D; IEC 60034-1.
# ═════════════════════════════════════════════════════════════════════════════

HERST = {
    "k_Faktor": {
        "range": "0,10 ... 4,00 x IN (Voreinst. 1,10)",
        "grund": ("Thermischer k-Faktor (ANSI 49) = dauernd zul. Strom I_max/IN. "
                  "Bei Motoren ueblich 1,05 ... 1,15 (7SJ66 Hdb. 2.11, Adr.4202)."),
    },
    "tau_min": {
        "range": "1,0 ... 999,9 min, Maschine typ. 100 min (Voreinst. 100)",
        "grund": ("Thermische Zeitkonstante. ACHTUNG: beim 7SJ66 in MINUTEN "
                  "(wie 7UT613, aber NICHT wie 7UM62 = Sekunden!). Gilt fuer den "
                  "laufenden Motor (7SJ66 Hdb. 2.11, Adr.4203)."),
    },
    "Ktau_Stop": {
        "range": "1,0 ... 10,0 (Voreinst. 1,0)",
        "grund": ("Verlaengerung der Zeitkonstante bei Motorstillstand. Eigenbelueftete "
                  "Motoren kuehlen ohne Luefter langsamer ab -> Ktau > 1 (7SJ66 Hdb. 2.11, Adr.4207A)."),
    },
    "I_Warn": {
        "range": "0,10 ... 4,00 A (1 A) (Voreinst. 1,00 A)",
        "grund": ("Stromwarnstufe (sek.). Soll auf oder knapp unter dem dauernd zul. "
                  "Strom k x IN liegen (7SJ66 Hdb. 2.11, Adr.4205)."),
    },
    "f_50_2": {
        "range": "0,10 ... 35,00 A; typ. 1,6 x I_Anlauf < 50-2 < Ik,2pol,min",
        "grund": ("Hochstromstufe 50-2 als Kurzschlussschutz. Motorseitig: oberhalb des "
                  "1,6-fachen Anlaufstroms, unterhalb des kleinsten 2-poligen Fehlerstroms. "
                  "Da im Motor keine Stossspannungs-Saettigung wie im Trafo auftritt, "
                  "darf 50-2 unverzoegert auslosen (7SJ66 Hdb. 2.2, Adr.1202)."),
    },
    "t_50_2": {
        "range": "0,00 ... 60,00 s (motorseitig 0,00 s)",
        "grund": ("Verzoegerung 50-2. Beim Motor in der Regel 0 s, da keine Inrush-"
                  "Stabilisierung wie beim Trafo notwendig (7SJ66 Hdb. 2.2, Adr.1203)."),
    },
    "f_50_1": {
        "range": "0,10 ... 35,00 A (Voreinst. ~2,5 x IN)",
        "grund": ("Reservestufe 50-1 (UMZ). Oberhalb der maximalen Betriebslast, "
                  "verzoegert als Backup zur 50-2 (7SJ66 Hdb. 2.2, Adr.1204)."),
    },
    "f_51": {
        "range": "0,10 ... 4,00 A (Voreinst. ~1,2 x IN)",
        "grund": ("AMZ-Stufe 51. Anregewert ueber max. Betriebsstrom; inverse Kennlinie "
                  "ueberstaffelt nachgelagerte Abgaenge (7SJ66 Hdb. 2.2, Adr.1207)."),
    },
    "I2_dauer": {
        "range": "5 ... 15 % (Voreinst. 11 %)",
        "grund": ("46-1: dauernd zul. Gegensystemstrom. Fuer Asynchronmaschinen nach "
                  "IEC 60034-1 typ. ~11 % (7SJ66 Hdb. 2.7, Adr.4002)."),
    },
    "I2_kurz": {
        "range": "5 ... 100 % (Voreinst. 55 %)",
        "grund": ("46-2: kurzzeitig zul. Gegensystemstrom (Tmax ~1 s). Trennt Phasen-"
                  "ausfall und 2-poligen Kurzschluss (7SJ66 Hdb. 2.7, Adr.4004)."),
    },
    "Startup_Time": {
        "range": "1,0 ... 180,0 s (Voreinst. 10,0 s)",
        "grund": ("Anlaufzeit-Schwelle der Anlaufueberwachung 48. Knapp oberhalb der "
                  "tatsaechlichen Hochlaufzeit, unterhalb der zul. Blockierzeit "
                  "(7SJ66 Hdb. 2.8, Adr.4103)."),
    },
    "Lock_Rotor_Time": {
        "range": "0,5 ... 180,0 s; unendlich (Voreinst. 2,0 s)",
        "grund": ("Zulaessige Blockierzeit (locked rotor). Bei blockiertem Laeufer loest "
                  "48 nach dieser Zeit aus, sofern Binaereingang gesetzt (7SJ66 Hdb. 2.8, Adr.4104)."),
    },
    "IStart_IMOTnom": {
        "range": "1,10 ... 10,00 (Voreinst. 4,90)",
        "grund": ("Anlaufstromverhaeltnis fuer die Wiedereinschaltsperre 66. Aus dem "
                  "Motordatenblatt I_A/IN (7SJ66 Hdb. 2.8, Adr.4302)."),
    },
    "T_Start_Max": {
        "range": "1 ... 320 s (Voreinst. 10 s)",
        "grund": ("Max. zul. Anlaufzeit fuer das thermische Laeuferabbild der "
                  "Wiedereinschaltsperre 66 (7SJ66 Hdb. 2.8, Adr.4303)."),
    },
    "Max_Warm_Starts": {
        "range": "1 ... 4 (Voreinst. 2)",
        "grund": ("Maximal zulaessige Warmstarts. Steuert die Wiedereinschaltsperre 66 "
                  "(7SJ66 Hdb. 2.8, Adr.4306)."),
    },
    "LoadJam_I": {
        "range": "0,50 ... 12,00 A; typ. 2 x IN_Motor (Voreinst. 2,00 A)",
        "grund": ("Ausloeseschwelle Lastsprung-/Load-Jam-Schutz. Unterhalb Anlaufstrom, "
                  "bei ~2 x Motornennstrom; waehrend des Anlaufs blockiert "
                  "(7SJ66 Hdb. 2.8, Adr.4402)."),
    },
    "I_unter": {
        "range": "Setpoint in % von IN (Voreinst. 30 %)",
        "grund": ("Unterstrom-/Lastverlust-Erkennung 37-1< (z. B. Trockenlauf einer Pumpe, "
                  "Kupplungsbruch). Kein 4xxx-Parameter, sondern Messwert-Setpoint in der "
                  "DIGSI-Matrix (7SJ66 Hdb. 2.27)."),
    },
}


# ── Adressen-Zuordnung fuer die Regler-Captions (eine Adresse je Parameter) ──
_HERST_ADR = {
    "k_Faktor": "Adr.4202", "tau_min": "Adr.4203", "Ktau_Stop": "Adr.4207A",
    "I_Warn": "Adr.4205", "f_50_2": "Adr.1202", "t_50_2": "Adr.1203",
    "f_50_1": "Adr.1204", "f_51": "Adr.1207", "I2_dauer": "Adr.4002",
    "I2_kurz": "Adr.4004", "Startup_Time": "Adr.4103", "Lock_Rotor_Time": "Adr.4104",
    "IStart_IMOTnom": "Adr.4302", "T_Start_Max": "Adr.4303",
    "Max_Warm_Starts": "Adr.4306", "LoadJam_I": "Adr.4402", "I_unter": "Setpoint (MV)",
}
for _k, _a in _HERST_ADR.items():
    if _k in HERST:
        HERST[_k]["adr"] = _a
