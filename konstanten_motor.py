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

# ── 50N/51N Erdfehler-/Erdueberstromschutz (Adr. 13xx) ───────────────────────
# Standard-Erdstromstufen fuer NIEDEROHMIG geerdete Netze (definierter Erdfehlerstrom).
# Werksdefaults sekundaer bei 1-A-Wandler (5-A-Wandler: jeweils x5). Quelle: 7SJ66 Hdb. 2.2.
f_50N2_def        = 0.50   # Adr.1302  50N-2 PICKUP (sek., 1A-Basis)       [A]
t_50N2_def        = 0.10   # Adr.1303  50N-2 DELAY                         [s]
f_50N1_def        = 0.20   # Adr.1304  50N-1 PICKUP (sek., 1A-Basis)       [A]
t_50N1_def        = 0.50   # Adr.1305  50N-1 DELAY                         [s]
f_51N_def         = 0.20   # Adr.1307  51N PICKUP (sek., 1A-Basis)         [A]
T_51N_def         = 0.20   # Adr.1308  51N TIME DIAL (IEC)                 [s]
Kennlinie_51N_def = "Normal Invers (IEC)"  # Adr.1311  51N IEC CURVE

# ── 50Ns/51Ns/67Ns Empfindlicher Erdschluss (Adr. 31xx) ──────────────────────
# Fuer ISOLIERTE / KOMPENSIERTE Netze: empfindlicher Erdstromeingang INs +
# Verlagerungsspannung U0 (VN), Richtungsbestimmung cos-phi (kompensiert) bzw.
# sin-phi (isoliert). Quelle: 7SJ66 Hdb. 2.16 (Sensitive Ground Fault Detection).
VN_50Ns_def       = 40.0   # Adr.3109  64-1 VGND (U0-Ansprechschwelle, sek.) [V]
t_64_1_def        = 10.0   # Adr.3112  64-1 DELAY (Ausloeseverz.)          [s]
f_50Ns2_def       = 0.300  # Adr.3113  50Ns-2 PICKUP (empfindl. INs, sek.) [A]
t_50Ns2_def       = 1.00   # Adr.3114  50Ns-2 DELAY                        [s]
f_50Ns1_def       = 0.100  # Adr.3117  50Ns-1 PICKUP (empfindl. INs, sek.) [A]
Richtung_67Ns_def = "Vorwärts (Forward)"   # Adr.3115  67Ns-2 DIRECT
VN_voll_V         = 100.0  # Vollausschlag U0 bei satter Erdberuehrung (e-n-Wicklung) [V]

# ── 27/59 Unter-/Ueberspannungsschutz (Adr. 50xx / 51xx) — nur VT-Variante ───
# Bezug: VT-Sekundaernennspannung UnS (verkettet, typ. 100 V). Quelle: 7SJ66 Hdb. 2.6.
# 59 Ueberspannung (Adr. 50xx)
U59_1_def         = 110.0  # Adr.5002  59-1 PICKUP (sek.)                  [V]
t_59_1_def        = 0.50   # Adr.5004  59-1 DELAY                          [s]
U59_2_def         = 120.0  # Adr.5005  59-2 PICKUP (sek.)                  [V]
t_59_2_def        = 0.50   # Adr.5007  59-2 DELAY                          [s]
# 27 Unterspannung (Adr. 51xx) — 27-1 oberes Element (Warnstufe), 27-2 unteres (Aus)
U27_1_def         = 75.0   # Adr.5102  27-1 PICKUP (sek.)                  [V]
t_27_1_def        = 1.50   # Adr.5106  27-1 DELAY                          [s]
U27_2_def         = 70.0   # Adr.5110  27-2 PICKUP (sek.)                  [V]
t_27_2_def        = 0.50   # Adr.5112  27-2 DELAY                          [s]
DOUT_27_def       = 1.20   # Adr.5113A 27-1 DOUT RATIO (Ruecksetzverhaeltnis) [-]

# ── 47 Phasenfolge / Spannungsunsymmetrie (Adr. 209 / 50xx-V2) ───────────────
# Spannungsunsymmetrie = Ueberspannung im Gegensystem V2 (Adr.5015/5016 bei
# OP.QUANTITY 59 = V2). Phasenfolgeueberwachung statisch ueber Adr.209,
# Pruefung bei |Vab|,|Vbc|,|Vca| > 40 V bzw. |Ia|,|Ib|,|Ic| > 0,5 IN.
# Quelle: 7SJ66 Hdb. 2.6 (V2) und 2.12 (Phasenfolge).
U59_V2_1_def      = 30.0   # Adr.5015  59-1-V2 PICKUP (Gegensystem-U)      [V]
U59_V2_2_def      = 50.0   # Adr.5016  59-2-V2 PICKUP (Gegensystem-U)      [V]
PHASE_SEQ_def     = "A B C (Rechtsdrehfeld)"  # Adr.209  PHASE SEQ.
PHASE_SEQ_OPTIONEN = ["A B C (Rechtsdrehfeld)", "A C B (Linksdrehfeld)"]  # Adr.209
U_PhSeq_min_def   = 40.0   # Pruefschwelle Phasenfolge (Spannung)          [V]
I_PhSeq_min_faktor= 0.50   # Pruefschwelle Phasenfolge (Strom) = 0,5 x IN  [x IN]

VT_Sek_Optionen   = [100, 110, 120]   # VT-Sekundaernennspannung (verkettet) [V]


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
U27_min_pct       = 55.0   # Plausibilitaet: 27-Ansprechwert nicht unter (zu spaet)  [%]
U27_max_pct       = 95.0   # Plausibilitaet: 27-Ansprechwert nicht ueber (Fehlausl.) [%]
U59_min_pct       = 105.0  # Plausibilitaet: 59-Ansprechwert nicht unter (Fehlausl.) [%]
U59_max_pct       = 145.0  # Plausibilitaet: 59-Ansprechwert nicht ueber (zu spaet)  [%]

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
    "f_50N2": {
        "range": "0,05 ... 35,00 A; 1 A: 0,50 A / 5 A: 2,50 A (Voreinst. 0,50 A)",
        "grund": ("50N-2 Erd-Hochstromstufe (Stromkriterium). Sinnvoll nur im NIEDEROHMIG "
                  "geerdeten Netz mit definiertem Erdfehlerstrom; oberhalb des betrieblichen "
                  "Unsymmetrie-Reststroms (7SJ66 Hdb. 2.2, Adr.1302)."),
    },
    "f_50N1": {
        "range": "0,05 ... 35,00 A; 1 A: 0,20 A / 5 A: 1,00 A (Voreinst. 0,20 A)",
        "grund": ("50N-1 Erdstrom-Reservestufe (UMZ), verzoegert. Anregung oberhalb des "
                  "natuerlichen Erd-Reststroms im Normalbetrieb (7SJ66 Hdb. 2.2, Adr.1304)."),
    },
    "f_51N": {
        "range": "0,05 ... 4,00 A; 1 A: 0,20 A / 5 A: 1,00 A (Voreinst. 0,20 A)",
        "grund": ("51N AMZ-Erdstromstufe (inverse Kennlinie). Empfindlichste Dauerstufe gegen "
                  "stehende Erdfehler im niederohmig geerdeten Netz (7SJ66 Hdb. 2.2, Adr.1307)."),
    },
    "VN_50Ns": {
        "range": "1,8 ... 170,0 V (Voreinst. 40,0 V), Vollausschlag ~100 V",
        "grund": ("Ansprechschwelle der Verlagerungsspannung U0 (64-1) fuer die empfindliche "
                  "Erdschlusserfassung im ISOLIERTEN/KOMPENSIERTEN Netz; ~40 % der vollen "
                  "Verlagerungsspannung bei satter Erdberuehrung (7SJ66 Hdb. 2.16, Adr.3109)."),
    },
    "f_50Ns2": {
        "range": "0,001 ... 1,500 A (empfindl. INs) (Voreinst. 0,300 A)",
        "grund": ("50Ns-2 empfindliche Erdstromstufe ueber den INs-Eingang (Kabelumbau-/"
                  "Summenstromwandler). Erfasst den kleinen kapazitiven bzw. Wirk-Reststrom im "
                  "isolierten/kompensierten Netz (7SJ66 Hdb. 2.16, Adr.3113)."),
    },
    "f_50Ns1": {
        "range": "0,001 ... 1,500 A (empfindl. INs) (Voreinst. 0,100 A)",
        "grund": ("50Ns-1 empfindliche Erdstrom-Grundstufe, hochempfindlich; ueblicherweise "
                  "richtungsbehaftet (67Ns, Adr.3115) ausgewertet (7SJ66 Hdb. 2.16, Adr.3117)."),
    },
    "U59_1": {
        "range": "40 ... 260 V (Voreinst. 110 V = 110 % UnS)",
        "grund": ("59-1 Ueberspannung-Warnstufe, verzoegert. Typ. 110 ... 115 % der "
                  "Bemessungsspannung (7SJ66 Hdb. 2.6, Adr.5002)."),
    },
    "U59_2": {
        "range": "40 ... 260 V (Voreinst. 120 V = 120 % UnS)",
        "grund": ("59-2 Ueberspannung-Schnellstufe, kurz verzoegert. Typ. ~130 % der "
                  "Bemessungsspannung (7SJ66 Hdb. 2.6, Adr.5005)."),
    },
    "U27_1": {
        "range": "10 ... 210 V (Voreinst. 75 V = 75 % UnS)",
        "grund": ("27-1 Unterspannung oberes Element (Warnstufe), laenger verzoegert. "
                  "Motoren typ. 70 ... 80 % UN (7SJ66 Hdb. 2.6, Adr.5102). Wird mit Strom"
                  "kriterium freigegeben (Adr.5120), um Auslosung bei Trennung zu vermeiden."),
    },
    "U27_2": {
        "range": "10 ... 210 V (Voreinst. 70 V = 70 % UnS)",
        "grund": ("27-2 Unterspannung unteres Element (Aus), kurz verzoegert. Schuetzt vor "
                  "Wiederanlauf-Stromstoss und Kippen bei tiefem Spannungseinbruch "
                  "(7SJ66 Hdb. 2.6, Adr.5110)."),
    },
    "U59_V2_1": {
        "range": "2 ... 150 V (Voreinst. 30 V)",
        "grund": ("59-1-V2: Ueberspannung im Gegensystem als Spannungsunsymmetrie-/Phasen"
                  "ausfallkriterium (OP.QUANTITY 59 = V2). Erfasst verdrehte/fehlende Phasen "
                  "spannungsseitig (7SJ66 Hdb. 2.6, Adr.5015)."),
    },
    "U59_V2_2": {
        "range": "2 ... 150 V (Voreinst. 50 V)",
        "grund": ("59-2-V2: hoehere Gegensystem-Ueberspannungsstufe, schneller. Trennt "
                  "ausgepraegte Spannungsunsymmetrie (7SJ66 Hdb. 2.6, Adr.5016)."),
    },
    "phase_seq": {
        "range": "A B C (Rechtsdrehfeld) / A C B (Linksdrehfeld) (Voreinst. A B C)",
        "grund": ("Erwartete Phasenfolge (47). Die Ueberwachung meldet 'Fail Ph. Seq.', wenn die "
                  "gemessene Drehfeldrichtung abweicht (Schutz vor Drehrichtungsumkehr des "
                  "Motors). Pruefung ab |U| > 40 V bzw. |I| > 0,5 IN (7SJ66 Hdb. 2.12, Adr.209)."),
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
    "f_50N2": "Adr.1302", "f_50N1": "Adr.1304", "f_51N": "Adr.1307",
    "VN_50Ns": "Adr.3109", "f_50Ns2": "Adr.3113", "f_50Ns1": "Adr.3117",
    "U59_1": "Adr.5002", "U59_2": "Adr.5005", "U27_1": "Adr.5102", "U27_2": "Adr.5110",
    "U59_V2_1": "Adr.5015", "U59_V2_2": "Adr.5016", "phase_seq": "Adr.209",
}
for _k, _a in _HERST_ADR.items():
    if _k in HERST:
        HERST[_k]["adr"] = _a
