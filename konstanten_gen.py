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
# Voreinstellungen fuer fN = 50 Hz (Markt Europa). Schwellenadressen sind
# frequenzabhaengig: 50 Hz -> 4202/4205/4208/4211, 60 Hz -> 4203/4206/4209/4212.
# Die Verzoegerungsadressen (4204/4207/4210/4213) gelten fuer beide Frequenzen.
f1_def            = 48.00  # Adr.4202 f1 (Netztrennung, fN=50)         [Hz]
t_f1_def          = 1.00   # Adr.4204 T F1                             [s]
f2_def            = 47.00  # Adr.4205 f2 (Stillsetzung, fN=50)         [Hz]
t_f2_def          = 6.00   # Adr.4207 T F2                             [s]
f3_def            = 49.50  # Adr.4208 f3 (Warnung Unterfrequenz, fN=50)[Hz]
t_f3_def          = 20.00  # Adr.4210 T F3                             [s]
f4_def            = 52.00  # Adr.4211 f4 (Ueberfrequenz, fN=50)        [Hz]
t_f4_def          = 10.00  # Adr.4213 T F4                             [s]
# 60-Hz-Voreinstellungen (Schwellenadressen 4203/4206/4209/4212)
f1_60, f2_60, f3_60, f4_60 = 58.00, 57.00, 59.50, 62.00
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

# ── 32P Vorwaertsleistungsueberwachung (Adr. 32xx) ────────────────────────────
# Ueberwacht die abgegebene Wirkleistung auf Unterschreiten (P<) und
# Ueberschreiten (P>). Einstellwerte in % der sekundaeren Nennscheinleistung
# SN_sek = sqrt(3) * UN_sek * IN_sek (identische Bezugsgroesse wie 32 Rueckleistung).
# Hauptanwendung: Erkennung von Schwachlast / bevorstehender Rueckleistung (P<)
# sowie maximaler Wirkleistung / Netzentkupplung (P>).
# Quellen: SIPROTEC 7UM62 Handbuch C53000-G1100-C149-C, Kap. 2.13.
PVorw_aktiv_def   = False  # Adr.3201 VORWAERTSLEIST.                    (Voreinst. Aus)
PVorw_un_def      = 9.7    # Adr.3202 P< VORW.  (Unterschreitungsschwelle)[% SN_sek]
t_PVorw_un_def    = 10.00  # Adr.3203 T P<      (Verzoegerung)           [s]
PVorw_ue_def      = 96.6   # Adr.3204 P> VORW.  (Ueberschreitungsschwelle)[% SN_sek]
t_PVorw_ue_def    = 10.00  # Adr.3205 T P>      (Verzoegerung)           [s]
# Adr.3206A MESSVERFAHREN: "genau" (16-Perioden-Mittelung, Normalbetrieb) /
#   "schnell" (ohne Mittelung, Netzentkupplung) — keine numerische Einstellung.

# ── IEE Empfindlicher Erdstromschutz (Adr. 51xx) ─────────────────────────────
# Zweistufige Erfassung des Erdstroms am empfindlichen IEE-Eingang.
# Einheit mA direkt am Messeingangsstrom — kein CT-Umrechnungsfaktor noetig.
# Anwendung: Staender- oder Laeufererdschlussschutz (Alternative zu 64R),
# wenn ausschliesslich der Betrag des Erdstroms als Kriterium genuegt.
# WICHTIG: Kann denselben IEE2-Messeingang wie 59N belegen -> Konfliktregel beachten.
# Quellen: SIPROTEC 7UM62 Handbuch C53000-G1100-C149-C, Kap. 2.26.
IEE_aktiv_def     = False  # Adr.5101 ERDSTROM IEE                       (Voreinst. Aus)
IEE_an_def        = 10.0   # Adr.5102 IEE>  Anregestrom (Warnstufe)      [mA]
t_IEE_an_def      = 5.00   # Adr.5103 T IEE>                             [s]
IEE_aus_def       = 23.0   # Adr.5104 IEE>> Ausloesung (~1,5 kOhm)       [mA]
t_IEE_aus_def     = 1.00   # Adr.5105 T IEE>>                            [s]
IEE_ueb_def       = 0.0    # Adr.5106 IEE<  Ueberwachungsstufe (0=inakt.)[mA]

# ── 50BF Leistungsschalterversagerschutz (Adr. 70xx) ─────────────────────────
# Ueberwacht, ob der Leistungsschalter nach einem Ausschaltbefehl innerhalb
# der parametrierbaren Zeit SVS-Taus abschaltet. Tut er es nicht, wird ein
# uebergeordneter Schalter ausgeloest.
#
# Zwei numerische Einstellparameter (alle anderen sind Konfigurationsoptionen):
#   SVS I>   (Adr.7003): Stromansprechschwelle, mindestens 10 % unterhalb
#             des kleinsten erwarteten Betriebsstroms.
#   SVS-Taus (Adr.7004): Ausloesezeit = t_LS_max + t_Rueckfall + t_Marge
#             Typisch: LS-Oeffnungszeit 60-80 ms + RF-Zeit ~20 ms + Marge ~50 ms
#             => Voreinst. 0,25 s.
#
# Nicht-numerische Parameter (nur DIGSI-Konfiguration, kein Slider):
#   Adr.7001 SCHALTERVERSAG.: Ein/Aus/Block.Relais   (Voreinst. Aus)
#   Adr.7002 AUS INTERN:      BA12/CFC/Aus           (Voreinst. Aus)
#
# SVS I> Voreinstellung marktabhaengig (CT-sek.-bezogen, Hdb. Kap. 2.36):
#   1A-CT:  0,04 ... 2,00 A, Voreinst. 0,20 A
#   5A-CT:  0,20 ... 10,00 A, Voreinst. 1,00 A
# Quellen: SIPROTEC 7UM62 Handbuch C53000-G1100-C149-C, Kap. 2.36.
BF_aktiv_def      = False  # Adr.7001 SCHALTERVERSAG.                    (Voreinst. Aus)
BF_I_sek_1A_def   = 0.20   # Adr.7003 SVS I>  fuer 1A-CT                [A sek.]
BF_I_sek_5A_def   = 1.00   # Adr.7003 SVS I>  fuer 5A-CT                [A sek.]
BF_I_sek_1A_min   = 0.04   # Adr.7003 untere Einstellgrenze (1A-CT)     [A sek.]
BF_I_sek_1A_max   = 2.00   # Adr.7003 obere Einstellgrenze (1A-CT)      [A sek.]
BF_I_sek_5A_min   = 0.20   # Adr.7003 untere Einstellgrenze (5A-CT)     [A sek.]
BF_I_sek_5A_max   = 10.00  # Adr.7003 obere Einstellgrenze (5A-CT)      [A sek.]
BF_Taus_def       = 0.25   # Adr.7004 SVS-Taus (Ausloesezeit)           [s]
BF_Taus_min       = 0.06   # Adr.7004 untere Einstellgrenze             [s]
# Engineering-Richtwerte fuer SVS-Taus-Zusammensetzung:
BF_t_LS_typ       = 0.08   # Typische max. LS-Ausschaltzeit             [s]
BF_t_RF_typ       = 0.02   # Typische Rueckfallzeit Ueberstromerfassung [s]
BF_t_Marge_typ    = 0.05   # Sicherheitsmarge                           [s]
# SVS I> Empfehlungsfaktor: Richtwert 90 % von IN_sek als Oberschranke
# (Einstellwert soll mindestens 10 % unter dem minimalen Betriebsstrom liegen)
BF_I_emp_faktor   = 0.20   # Empfehlung als Anteil von IN_K_sek (DIGSI-Default-Ratio)

# ── 81R Frequenzaenderungsschutz df/dt (Adr. 45xx) ───────────────────────────
# Vier Stufen df1/dt ... df4/dt. Jede Stufe einstellbar als Frequenzabfall
# (-df/dt<, Voreinst.) oder Frequenzanstieg (+df/dt>).
# Voreinstellung: 2 Stufen aktiv (df3/df4 werksseitig deaktiviert).
# Hauptanwendung: Netzentkupplung und Lastabwurf.
# Formel: df/dt = -fN / (2H) * (dP/SN), H = Traegheitskonstante [s].
# Quellen: SIPROTEC 7UM62 Handbuch C53000-G1100-C149-C, Kap. 2.21.
dfdt_aktiv_def    = False  # Adr.4501 df/dt - SCHUTZ                     (Voreinst. Aus)
# Stufe 1 (langsamer Gradient, verzoegert)
dfdt_1_rich_def   = "-df/dt<"  # Adr.4502 df1/dt >/< Richtung
dfdt_1_stufe_def  = 1.0    # Adr.4503 STUFE df1/dt                       [Hz/s]
dfdt_1_t_def      = 0.50   # Adr.4504 T df1/dt                           [s]
# Stufe 2 (zweite langsame Stufe, verzoegert)
dfdt_2_rich_def   = "-df/dt<"  # Adr.4506 df2/dt >/<
dfdt_2_stufe_def  = 1.0    # Adr.4507 STUFE df2/dt                       [Hz/s]
dfdt_2_t_def      = 0.50   # Adr.4508 T df2/dt                           [s]
# Stufe 3 (schneller Gradient, unverzoeert)
dfdt_3_rich_def   = "-df/dt<"  # Adr.4510 df3/dt >/<
dfdt_3_stufe_def  = 4.0    # Adr.4511 STUFE df3/dt                       [Hz/s]
dfdt_3_t_def      = 0.00   # Adr.4512 T df3/dt                           [s]
# Stufe 4 (schneller Gradient, unverzoeert)
dfdt_4_rich_def   = "-df/dt<"  # Adr.4514 df4/dt >/<
dfdt_4_stufe_def  = 4.0    # Adr.4515 STUFE df4/dt                       [Hz/s]
dfdt_4_t_def      = 0.00   # Adr.4516 T df4/dt                           [s]
# Mindestspannung (gemeinsam fuer alle Stufen)
dfdt_Umin_def     = 65.0   # Adr.4518 U MIN (~65 % UN_sek)               [V]
# Adress-Mapping fuer Stufen (kompakt als Tupel: rich, stufe, t)
DFDT_STUFEN_ADR = [
    ("Adr.4502", "Adr.4503", "Adr.4504"),  # Stufe 1
    ("Adr.4506", "Adr.4507", "Adr.4508"),  # Stufe 2
    ("Adr.4510", "Adr.4511", "Adr.4512"),  # Stufe 3
    ("Adr.4514", "Adr.4515", "Adr.4516"),  # Stufe 4
]
DFDT_RICHTUNG_OPTIONEN = ["-df/dt<", "+df/dt>"]

# ── Vektorsprung (Adr. 46xx) ───────────────────────────────────────────────────
# Erkennt Phasenwinkelsprung der Mitsystemspannung nach schlagartiger
# Stromunterbrechung (z. B. Netzausfall, automatische Wiedereinschaltung).
# Hauptanwendung: Netzentkupplung (Eigenerzeuger auf Inselbusbetrieb).
# Der Einstellwert DELTA PHI ist anlagenspezifisch (vereinfachte Formel:
#   Delta_phi = arctan(X_k / R_k * dP / P) je nach Kurzschlussverhaeltnis).
# Quellen: SIPROTEC 7UM62 Handbuch C53000-G1100-C149-C, Kap. 2.22.
VS_aktiv_def      = False  # Adr.4601 VEKTORSPRUNG                       (Voreinst. Aus)
VS_dphi_def       = 10.0   # Adr.4602 DELTA PHI (2 ... 30 Grad)          [Grad]
VS_t_dphi_def     = 0.00   # Adr.4603 T DELTA PHI (0 = unverzoeert)      [s]
VS_t_reset_def    = 5.00   # Adr.4604 T RESET (Selbstreset)              [s]
VS_Umin_def       = 80.0   # Adr.4605A U MIN (~80 % UN_sek)              [V]
VS_Umax_def       = 130.0  # Adr.4606A U MAX (~130 % UN_sek)             [V]

# ── 21 Impedanzschutz (Reserve, Seite 2) (Adr. 33xx) ─────────────────────────
# Reserve-/Zeitstaffelschutz fuer Kurzschluesse in Maschine, Ableitung und
# Maschinentrafo. Arbeitet stets mit den Stroemen der Seite 2 (Klemmen-CT).
# Zonen-Reichweiten als Sekundaer-Ohm: Z_sek = Z_prim * kCT_K / nVT.
# Voreinstellungen = marktabhaengige DIGSI-Werte (Bezug 1A-Wandler).
Imp_aktiv_def     = False  # Adr.3301 IMPEDANZSCHUTZ (Voreinst. Aus)
Imp_I_anr_Faktor  = 1.20   # Adr.3302 IMP I> Ueberstromanregung        [x IN_sek]
Imp_Uhalt_def     = False  # Adr.3303 U<-HALTUNG (Unterspg.selbsthalt.)
Imp_U_halt_def    = 80.0   # Adr.3304 U< Anregespg. der Haltung        [V sek.]
Imp_T_halt_def    = 4.00   # Adr.3305 T-HALTUNG                        [s]
Imp_Z1_def        = 2.90   # Adr.3306 ZONE Z1 (1A)                     [Ohm sek.]
Imp_T_Z1_def      = 0.10   # Adr.3307 ZONE1 T1                         [s]
Imp_Z1B_def       = 4.95   # Adr.3308 UEBERGR. Z1B (1A)                [Ohm sek.]
Imp_T_Z1B_def     = 0.10   # Adr.3309 UEBERGR. T1B                     [s]
Imp_Z2_def        = 4.15   # Adr.3310 ZONE Z2 (1A)                     [Ohm sek.]
Imp_T_Z2_def      = 0.50   # Adr.3311 ZONE2 T2                         [s]
Imp_T_End_def     = 3.00   # Adr.3312 T END (Endzeitstufe T3)          [s]

# ── 78 Aussertrittfallschutz / Polschlupf (Adr. 35xx) ────────────────────────
# Erkennt Pendelungen ueber den Verlauf des Mitsystem-Impedanzzeigers im
# Polygon. Freigaben: I1> (Mitsystem, ueber Nennstrom) und I2< (Gegensystem-
# Sperre gegen Unsymmetrie/Fehler). Polygon-Impedanzen als Sekundaer-Ohm.
Aus_aktiv_def     = False  # Adr.3501 AUSSERTRITTFALL (Voreinst. Aus)
Aus_I1_frei_def   = 120.0  # Adr.3502 I1> FREIGABE (Mitsystem)         [% IN]
Aus_I2_frei_def   = 20.0   # Adr.3503 I2< FREIGABE (Gegensystem-Sperre)[% IN]
Aus_Za_def        = 4.50   # Adr.3504 Za Resistanz/Breite (1A)         [Ohm sek.]
Aus_Zb_def        = 12.00  # Adr.3505 Zb Reaktanz rueckwaerts (1A)     [Ohm sek.]
Aus_Zc_def        = 3.60   # Adr.3506 Zc Reaktanz vorwaerts Kl.1 (1A)  [Ohm sek.]
Aus_ZdZc_def      = 6.40   # Adr.3507 Zd-Zc Reaktanzdiff. Kl.2-Kl.1(1A)[Ohm sek.]
Aus_Phi_def       = 90.0   # Adr.3508 PHI POLYGON Neigungswinkel       [Grad]
Aus_n_KL1_def     = 1      # Adr.3509 MESSWIED. KL.1 (Pendelungen)     [-]
Aus_n_KL2_def     = 4      # Adr.3510 MESSWIED. KL.2 (Pendelungen)     [-]
Aus_T_halt_def    = 20.00  # Adr.3511 T HALTUNG                        [s]
Aus_T_meld_def    = 0.05   # Adr.3512 T MELDUNG                        [s]

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
        "adr":   "Adr.2021",
        "grund": ("Ansprechwert des Staenderdifferentialschutzes. 0,20 deckt kleine "
                  "Windungsschluesse ab; tiefer als beim Trafo moeglich, da keine "
                  "Stufensteller-Fehler auftreten (7UM62 Hdb. 2.9, Adr.2021)."),
    },
    "I_DIFF_HH": {
        "range": "ca. 1/x'd, typ. (3 ... 7) x IN  (Voreinst. 5,0)",
        "adr":   "Adr.2031",
        "grund": ("Unstabilisierte Schnellausloesestufe. Muss oberhalb des max. "
                  "durchfliessenden Fehlerstroms liegen; bei Maschinen aus der "
                  "transienten Reaktanz x'd: I-DIFF>> ~ 1/x'd (7UM62 Hdb. 2.9, Adr.2031)."),
    },
    "Steigung_1": {
        "range": "0,10 ... 0,50 (Voreinst. 0,25)",
        "adr":   "Adr.2041A",
        "grund": ("Neigung des ersten Kennlinienastes. Beruecksichtigt Wandlerfehler "
                  "im unteren Strombereich (7UM62 Hdb. 2.9, Adr.2041A)."),
    },
    "Steigung_2": {
        "range": "0,25 ... 0,95 (Voreinst. 0,50)",
        "adr":   "Adr.2043A",
        "grund": ("Neigung ab Fusspunkt 2 — hoehere Stabilisierung gegen Wandler- "
                  "saettigung bei grossen Durchgangsfehlern (7UM62 Hdb. 2.9, Adr.2043A)."),
    },
    "Fusspunkt_2": {
        "range": "0,00 ... 10,00 I/InO (Voreinst. 2,50)",
        "adr":   "Adr.2044A",
        "grund": ("Knickpunkt zum steileren Kennlinienast (7UM62 Hdb. 2.9, Adr.2044A)."),
    },
    "Harm_2": {
        "range": "10 ... 80 % (Voreinst. 15 %)",
        "adr":   "Adr.2071",
        "grund": ("Inrush-Stabilisierung ueber 2. Harmonische — relevant beim "
                  "Zuschalten eines Blocktrafos (7UM62 Hdb. 2.9, Adr.2071)."),
    },
    "f_I_Ph": {
        "range": "ca. 1,2 ... 1,5 x IN (Voreinst. 1,40)",
        "adr":   "Adr.1202",
        "grund": ("Reserve-Ueberstromstufe I>. Oberhalb der max. Betriebslast; beim "
                  "Generator mit Unterspannungshaltung kombinierbar (7UM62 Hdb. 2.3, Adr.1202)."),
    },
    "t_I_Ph": {
        "range": "aus Staffelplan, typ. 1 ... 3 s (Voreinst. 3,0 s)",
        "adr":   "Adr.1203",
        "grund": ("Verzoegerung I>. Generatorseitig bewusst lang, da Reserveschutz "
                  "(7UM62 Hdb. 2.3, Adr.1203)."),
    },
    "U_Haltung": {
        "range": "10 ... 125 V (Voreinst. 80 V)",
        "adr":   "Adr.1205",
        "grund": ("Unterspannungshaltung: haelt die I>-Anregung bei einbrechender "
                  "Spannung gespeichert, damit der abklingende Generator-KS-Strom "
                  "(1/xd) trotzdem erfasst wird (7UM62 Hdb. 2.3, Adr.1205)."),
    },
    "f_I_Ph_HH": {
        "range": "typ. 3 ... 7 x IN (Voreinst. 4,0)",
        "adr":   "Adr.1302",
        "grund": ("Hochstromstufe I>> als schneller Kurzschlussschutz, oberhalb des "
                  "subtransienten Speisestroms benachbarter Quellen (7UM62 Hdb. 2.4, Adr.1302)."),
    },
    "t_I_Ph_HH": {
        "range": "0,0 ... 0,1 s (Voreinst. 0,10 s)",
        "adr":   "Adr.1303",
        "grund": ("Kurze Sicherheitsverzoegerung der Hochstromstufe (7UM62 Hdb. 2.4, Adr.1303)."),
    },
    "f_Ip": {
        "range": "0,10 ... 4,00 A bzw. ~1,0 x IN (Voreinst. 1,0)",
        "adr":   "Adr.1402",
        "grund": ("Anregewert der spannungsabhaengigen AMZ-Stufe (51V). Mit aktiver "
                  "Spannungssteuerung sinkt die Schwelle bei Spannungseinbruch "
                  "(7UM62 Hdb. 2.5, Adr.1402)."),
    },
    "U_AMZ": {
        "range": "10 ... 125 V (Voreinst. 75 V)",
        "adr":   "Adr.1408",
        "grund": ("Spannungsschwelle der 51V-Steuerung. Unterhalb dieser Spannung "
                  "wird die AMZ-Kennlinie empfindlicher / freigegeben (7UM62 Hdb. 2.5, Adr.1408)."),
    },
    "k_Faktor": {
        "range": "0,10 ... 4,00 x IN (Voreinst. 1,11)",
        "adr":   "Adr.1602",
        "grund": ("Zulaessiger thermischer Dauerstrom (ANSI 49), bezogen auf 40 Grad C "
                  "Umgebung (7UM62 Hdb. 2.6, Adr.1602)."),
    },
    "tau_s": {
        "range": "30 ... 32000 s, Maschine typ. 600 s (Voreinst. 600)",
        "adr":   "Adr.1603",
        "grund": ("Thermische Zeitkonstante. ACHTUNG: beim 7UM62 in SEKUNDEN "
                  "(beim 7UT613 in Minuten!) — haeufige Verwechslung (7UM62 Hdb. 2.6, Adr.1603)."),
    },
    "I2_zul": {
        "range": "3,0 ... 30,0 % (Voreinst. 10,6 %)",
        "adr":   "Adr.1702",
        "grund": ("Dauernd zul. Schieflast (Gegensystem I2, ANSI 46). Maschinen sind "
                  "gegensystemempfindlich — Richtwert ~10 % (7UM62 Hdb. 2.7, Adr.1702)."),
    },
    "I2_HH": {
        "range": "10 ... 200 % (Voreinst. 60 %)",
        "adr":   "Adr.1706",
        "grund": ("Unabhaengige Schnellstufe I2>>. ~60 % trennt Phasenausfall (<58 %) "
                  "vom 2-poligen Kurzschluss (7UM62 Hdb. 2.7, Adr.1706)."),
    },
    "Winkel_1": {
        "range": "50 ... 120 Grad (Voreinst. 80 Grad)",
        "adr":   "Adr.3003",
        "grund": ("Neigung Kennlinie 1 (40). Winkel der Untererregungsbegrenzung bzw. "
                  "der statischen Stabilitaetsgrenze, typ. 60 ... 80 Grad (7UM62 Hdb. 2.11, Adr.3003)."),
    },
    "xd_KL3": {
        "range": "0,20 ... 3,00 (Voreinst. 1,10)",
        "adr":   "Adr.3008",
        "grund": ("1/xd Kennlinie 3 (dyn. Stabilitaet). Wert zwischen xd und x'd, "
                  "jedoch > 1 (7UM62 Hdb. 2.11, Adr.3008)."),
    },
    "Prueck": {
        "range": "-30,00 ... -0,50 % (negativ; Voreinst. -1,93 %)",
        "adr":   "Adr.3102",
        "grund": ("Rueckleistungsschwelle (ANSI 32), ~0,5 x Schleppleistung. "
                  "Dampf 1-3 %, Gas 3-30 %, Diesel >5 % von SN (7UM62 Hdb. 2.12, Adr.3102)."),
    },
    "Uf_Warn": {
        "range": "1,00 ... 1,20 (Voreinst. 1,10)",
        "adr":   "Adr.4302",
        "grund": ("U/f-Warnstufe (ANSI 24). 1,10 schuetzt Eisen vor Saettigung beim "
                  "Hochfahren/Lastabwurf (7UM62 Hdb. 2.19, Adr.4302)."),
    },
    "Uf_Aus": {
        "range": "1,00 ... 1,40 (Voreinst. 1,40)",
        "adr":   "Adr.4304",
        "grund": ("U/f-Ausloesestufe — Schnellabschaltung bei starker Uebererregung "
                  "(7UM62 Hdb. 2.19, Adr.4304)."),
    },
    "U0": {
        "range": "2,0 ... 125,0 V (Voreinst. 10,0 V)",
        "adr":   "Adr.5002",
        "grund": ("Verlagerungsspannungs-Schwelle (90 % Staendererdschluss). 10 V bei "
                  "100 V voller Verlagerung -> 90 % Schutzbereich (7UM62 Hdb. 2.23, Adr.5002)."),
    },
    "RE_Aus": {
        "range": "1,0 ... 5,0 kOhm (Voreinst. 2,0 kOhm)",
        "adr":   "Adr.6003",
        "grund": ("Ausloeseschwelle Laeufererdschluss (64R). Unter 2 kOhm wird ein "
                  "Erdschluss der Erregerwicklung angenommen (7UM62 Hdb. 2.30, Adr.6003)."),
    },
    "Imp_I": {
        "range": "0,10 ... 20,00 A (1A); Voreinst. 1,35 A (1A) / 6,75 A (5A)",
        "adr":   "Adr.3302",
        "grund": ("Ueberstromanregung des Impedanzschutzes (ANSI 21). Muss ueber der "
                  "max. Betriebslast liegen, eine Anregung durch Ueberlast ist "
                  "auszuschliessen. Hier als Faktor x IN_sek (7UM62 Hdb. 2.14, Adr.3302)."),
    },
    "Imp_Z1": {
        "range": "0,05 ... 130,00 Ohm (1A); Voreinst. 2,90 Ohm",
        "adr":   "Adr.3306",
        "grund": ("Reichweite Zone Z1 (sek.). In Blockschaltung typ. bis ~70 % in den "
                  "Maschinentrafo. Z_prim = Z_sek x nVT/kCT. Exakte Reichweite erfordert "
                  "die Trafo-/Netzimpedanz (7UM62 Hdb. 2.14, Adr.3306)."),
    },
    "Imp_Z2": {
        "range": "0,05 ... 65,00 Ohm (1A); Voreinst. 4,15 Ohm",
        "adr":   "Adr.3310",
        "grund": ("Reichweite Zone Z2 (sek.) als verzoegerte Reservestufe ueber Z1 "
                  "hinaus. Zeitlich gestaffelt (T2 > T1) (7UM62 Hdb. 2.14, Adr.3310)."),
    },
    "Aus_I1": {
        "range": "20,0 ... 400,0 % IN (Voreinst. 120 %)",
        "adr":   "Adr.3502",
        "grund": ("Mitsystem-Freigabe I1> des Aussertrittfallschutzes (ANSI 78). "
                  "Oberhalb Nennstrom (~120 % IN), gibt die Pendelmessung nur bei "
                  "hoher Stromschwingung frei (7UM62 Hdb. 2.15, Adr.3502)."),
    },
    "Aus_I2": {
        "range": "5,0 ... 100,0 % IN (Voreinst. 20 %)",
        "adr":   "Adr.3503",
        "grund": ("Gegensystem-Sperre I2< (ANSI 78). Der Aussertrittfall ist ein "
                  "symmetrischer Vorgang; hoher I2 (Unsymmetrie/Fehler) sperrt die "
                  "Funktion (7UM62 Hdb. 2.15, Adr.3503)."),
    },
    "Aus_Za": {
        "range": "0,20 ... 130,00 Ohm (1A); Voreinst. 4,50 Ohm",
        "adr":   "Adr.3504",
        "grund": ("Resistanz/Breite Za des Pendelpolygons (sek.). Bestimmt die "
                  "Empfindlichkeit gegen das Pendelzentrum (7UM62 Hdb. 2.15, Adr.3504)."),
    },
    "Aus_Zb": {
        "range": "0,10 ... 130,00 Ohm (1A); Voreinst. 12,00 Ohm",
        "adr":   "Adr.3505",
        "grund": ("Reaktanz Zb rueckwaerts (sek.), in den Generator gerichtet. Aus der "
                  "transienten Reaktanz x'd der Maschine (7UM62 Hdb. 2.15, Adr.3505)."),
    },
    "Aus_Zc": {
        "range": "0,10 ... 130,00 Ohm (1A); Voreinst. 3,60 Ohm",
        "adr":   "Adr.3506",
        "grund": ("Reaktanz Zc vorwaerts (Kennlinie 1, sek.), in Richtung Netz/Trafo. "
                  "Begrenzt das Polygon zur Netzseite (7UM62 Hdb. 2.15, Adr.3506)."),
    },
    "PVorw_un": {
        "range": "0,5 ... 120,0 % SN_sek (Voreinst. 9,7 %)",
        "adr":   "Adr.3202",
        "grund": ("Unterschreitungsschwelle P< der Vorwaertsleistungsueberwachung. "
                  "Unterschreitet die abgegebene Wirkleistung diesen Wert (P< VORW.), loest die "
                  "Funktion aus. Typische Anwendung: Erkennung von Schwachlast vor der "
                  "Rueckleistungsgrenze. Einstellwert > |PRueck| der Rueckleistungsschwelle (32). "
                  "Bezugsgroesse SN_sek = sqrt(3)*UN_sek*IN_sek (7UM62 Hdb. 2.13, Adr.3202)."),
    },
    "PVorw_ue": {
        "range": "1,0 ... 120,0 % SN_sek (Voreinst. 96,6 %)",
        "adr":   "Adr.3204",
        "grund": ("Ueberschreitungsschwelle P> der Vorwaertsleistungsueberwachung. "
                  "Steigt die abgegebene Wirkleistung ueber diesen Wert, kann ein Steuerbefehl "
                  "ausgegeben werden (z.B. Lastabwurf, Netztrennung). Anlagenspezifisch aus "
                  "max. zulaessiger Maschinenleistung zu bestimmen (7UM62 Hdb. 2.13, Adr.3204)."),
    },
    "IEE_an": {
        "range": "2 ... 1000 mA (Voreinst. 10 mA)",
        "adr":   "Adr.5102",
        "grund": ("Anregestrom IEE> der Warnstufe. Erfasst Isolationswiderstaende RE im "
                  "Bereich 3-5 kOhm. Der Einstellwert muss mindestens doppelt so hoch sein wie "
                  "der Stoerstrom infolge der Erdkapazitaeten (7UM62 Hdb. 2.26, Adr.5102)."),
    },
    "IEE_aus": {
        "range": "2 ... 1000 mA (Voreinst. 23 mA)",
        "adr":   "Adr.5104",
        "grund": ("Ausloesesstrom IEE>>. Fuer Fehlerwiderstand RE ca. 1,5 kOhm bemessen. "
                  "IEE>> muss stets groesser als IEE> sein (7UM62 Hdb. 2.26, Adr.5104)."),
    },
    "IEE_ueb": {
        "range": "1,5 ... 50,0 mA (Voreinst. 0,0 mA = inaktiv)",
        "adr":   "Adr.5106",
        "grund": ("Ueberwachungsstufe IEE< fuer den Messkreis. Fliesst dauerhaft weniger Strom "
                  "als dieser Wert (typisch 2 mA bei Laeufererd-Verspannung), wird eine "
                  "Stoerungsmeldung ausgegeben. Auf 0 setzen, wenn Erdkapazitaeten zu klein "
                  "(7UM62 Hdb. 2.26, Adr.5106)."),
    },
    "dfdt_stufe": {
        "range": "0,1 ... 10,0 Hz/s je Stufe (Voreinst. Stufen 1/2: 1,0; Stufen 3/4: 4,0)",
        "adr":   "Adr.4503 / 4507 / 4511 / 4515",
        "grund": ("Absolutbetrag des Frequenzgradienten-Ansprechwerts. Richtung getrennt "
                  "parametrierbar (-df/dt< Abfall, +df/dt> Anstieg). Applikationsabhaengig: "
                  "typ. 1 Hz/s fuer verzoegerte Warnstufe, 4 Hz/s fuer schnelle Ausloesung. "
                  "Bemessungsformel: |df/dt| = fN/(2H) * |dP/SN| (7UM62 Hdb. 2.21)."),
    },
    "dfdt_Umin": {
        "range": "10,0 ... 125,0 V (Empfehlung ca. 65 % UN_sek; Voreinst. 65,0 V)",
        "adr":   "Adr.4518",
        "grund": ("Mindestspannung; bei Unterschreitung wird der gesamte df/dt-Schutz "
                  "blockiert, da dann keine zuverlaessige Frequenzmessung moeglich ist. "
                  "Empfohlener Wert: ~65 % UN_sek (7UM62 Hdb. 2.21, Adr.4518)."),
    },
    "VS_dphi": {
        "range": "2 ... 30 Grad (Voreinst. 10 Grad)",
        "adr":   "Adr.4602",
        "grund": ("Phasenwinkelschwelle des Vektorsprungschutzes. Anlagenspezifisch aus dem "
                  "Kurzschlussverhaeltnis des Netzes und der typischen Lastabwurfgroesse zu "
                  "ermitteln. Zu empfindlich -> Fehlausloesung bei Lastschaltvorgaengen. "
                  "Voreinstellung 10 Grad als konservativer Ausgangswert (7UM62 Hdb. 2.22, Adr.4602)."),
    },
    "VS_t_reset": {
        "range": "0,10 ... 60,00 s (Voreinst. 5,00 s)",
        "adr":   "Adr.4604",
        "grund": ("Selbstreset-Zeit T RESET. Nach Ablauf setzt die Funktion selbststaendig "
                  "zurueck; vor einer Wiedereinschaltung des Leistungsschalters muss T RESET "
                  "abgelaufen sein. Soll kein Selbstreset erfolgen, auf Unendlich setzen und "
                  "ueber Binaereingang (Hilfskontakt) ruecksetzen (7UM62 Hdb. 2.22, Adr.4604)."),
    },
    "BF_I": {
        "range": "1A-CT: 0,04...2,00 A (Voreinst. 0,20 A) · 5A-CT: 0,20...10,00 A (Voreinst. 1,00 A)",
        "adr":   "Adr.7003",
        "grund": ("Stromansprechschwelle SVS I> des Schalterversagerschutzes. Gilt fuer alle "
                  "drei Phasen. Mindestens 10 % unterhalb des kleinsten erwarteten "
                  "Betriebsstroms einstellen. Nicht zu empfindlich, da sonst "
                  "Ausgleichsvorgaenge im CT-Sekundaerkreis zu erlaengerter Rueckfallzeit "
                  "fuehren koennen (7UM62 Hdb. 2.36, Adr.7003)."),
    },
    "BF_Taus": {
        "range": "0,06 ... 60,00 s (Voreinst. 0,25 s)",
        "adr":   "Adr.7004",
        "grund": ("Ausloesezeit SVS-Taus. Setzt sich zusammen aus maximaler LS-Ausschaltzeit "
                  "zuzueglich Rueckfallzeit der Ueberstromerfassung und einer Sicherheitsmarge. "
                  "Typisch: t_LS_max (~80 ms) + t_RF (~20 ms) + t_Marge (~50 ms) = 150-200 ms. "
                  "Voreinst. 250 ms beinhaltet Marge. Zu kurz eingestellt -> Fehlanregung bei "
                  "normalem Abschaltvorgang (7UM62 Hdb. 2.36, Adr.7004)."),
    },
    "U_klein": {
        "range": "10,0 ... 125,0 V (Voreinst. 75,0 V)",
        "adr":   "Adr.4002",
        "grund": ("Anregeschwelle U< des zweistufigen Unterspannungsschutzes (ANSI 27). "
                  "Typisch ~75 % UN_sek. Haelt die I>-Anregung bei Spannungseinbruch aufrecht; "
                  "Verzögerung T U< (Adr.4003) so waehlen, dass kurzzeitige Spannungseinbrueche "
                  "nicht zu Fehlausloesung fuehren (7UM62 Hdb. 2.16, Adr.4002)."),
    },
    "U_kleinklein": {
        "range": "10,0 ... 125,0 V (Voreinst. 65,0 V)",
        "adr":   "Adr.4004",
        "grund": ("Anregeschwelle U<< der schnellen Ausloesestufe des Unterspannungsschutzes. "
                  "Typisch ~65 % UN_sek, kombiniert mit kurzer Verzoegerung T U<< = 0,5 s "
                  "(Adr.4005). Schutzt gegen instabilen Betrieb bei starken Spannungseinbruechen "
                  "(7UM62 Hdb. 2.16, Adr.4004)."),
    },
    "U_gross": {
        "range": "30,0 ... 170,0 V (Voreinst. 115,0 V)",
        "adr":   "Adr.4102",
        "grund": ("Anregeschwelle U> des zweistufigen Ueberspannungsschutzes (ANSI 59). "
                  "Typisch ~115 % UN_sek. Langzeitstufe fuer statische Ueberspannungen "
                  "(Erregerfehler, Lastabwurf). Verzoegerung T U> (Adr.4103) typisch 3 s "
                  "(7UM62 Hdb. 2.17, Adr.4102)."),
    },
    "U_grossgross": {
        "range": "30,0 ... 170,0 V (Voreinst. 130,0 V)",
        "adr":   "Adr.4104",
        "grund": ("Anregeschwelle U>> der schnellen Ausloesestufe des Ueberspannungsschutzes. "
                  "Typisch ~130 % UN_sek mit kurzer oder keiner Verzoegerung T U>> (Adr.4105). "
                  "Schutzt bei starken Ueberspannungen nach Lastabwurf "
                  "(7UM62 Hdb. 2.17, Adr.4104)."),
    },
}
