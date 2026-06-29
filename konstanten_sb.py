"""
konstanten_sb.py — Voreinstellungen, Adressen und Plausibilitäts-Schwellwerte (Sammelschiene)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Single Source of Truth für alle SIPROTEC-Werksvoreinstellungen, Engineering-Margen
und Plausibilitätsgrenzen des Sammelschienen-Tabs. Alle Werte sind frei änderbar.

Leitgerät:
  - Dezentraler Sammelschienen-/Schalterversagerschutz SIPROTEC 7SS52 V4
    (C53000-G1100-C182-8, Firmware V4.7), bestehend aus Zentraleinheit (ZE)
    und je Abzweig einer Feldeinheit (FE).

Architekturhinweis (relevant für die Adressierung):
  Das 7SS52 ist ein verteiltes System. Die Differentialschutz- und
  Überwachungsparameter liegen in der Zentraleinheit (Adr. 6101 ff., einheitlich).
  Die Schalterversagerschutz-Parameter sind abzweigselektiv: in der
  Parameterübersicht als Basisadresse 1xx geführt, in DIGSI je Feldeinheit
  mit einem Feldeinheit-Präfix angezeigt (Handbuch-Notation XXnn/ZE). Die
  Überstrom-Reservefunktionen und die Anlagendaten liegen in der Feldeinheit
  (Adr. 11xx / 12xx / 15xx, je Abzweig).

Quellen: SIPROTEC 7SS52 V4 Handbuch C53000-G1100-C182-8 (Ausgabe 2019),
         IEC 60255-187-3 (Differentialschutz), IEC 60255-151 (UMZ/AMZ).

Hinweis: Alle Adressen wurden gegen die Parameterübersichten und Einstellhinweise
des 7SS52-Handbuchs verifiziert (Inline-Adressangaben). Keine Adresse aus dem
Gedächtnis ergänzt.
"""

# =============================================================================
# AUSWAHL-OPTIONEN
# =============================================================================

SB_GERAET_OPTIONEN = ["Sammelschienenschutz 7SS52"]
SB_GERAET_KEY = {"Sammelschienenschutz 7SS52": "7SS52"}

# Sammelschienen-Topologie. Bestimmt die Empfehlung fuer den Stabilisierungsfaktor
# der Checkzone: bei Einfachsammelschiene wie der selektive Faktor, bei Mehrfach-
# sammelschienen 0,5 zur Vermeidung der Ueberstabilisierung (7SS52 Hdb. 5.1.4).
SB_TOPOLOGIE_OPTIONEN = [
    "Einfachsammelschiene",
    "Doppelsammelschiene",
    "Dreifachsammelschiene",
    "Mehrfachsammelschiene mit Kupplung",
]
# Topologien, die als Mehrfachsammelschiene gelten (CZ-Stabilisierung 0,5):
SB_MEHRFACH = [
    "Doppelsammelschiene",
    "Dreifachsammelschiene",
    "Mehrfachsammelschiene mit Kupplung",
]

STERNPUNKT_NETZ_OPTIONEN = [
    "Niederohmig geerdet",
    "Starr geerdet",
    "Isoliert",
    "Kompensiert (Petersen)",
]
NETZ_GEERDET = ["Niederohmig geerdet", "Starr geerdet"]

# SVS-BE-Mode (Adr.114): Art und Ueberwachung der Binaereingaenge fuer den SVS-Anwurf
SVS_BE_MODE_OPTIONEN = [
    "1BE ohne Überw", "1BE mit Überw", "2BE ohne Überw", "2BE mit Überw",
]
# SVS-Betriebsart (Adr.115)
SVS_BETRIEBSART_OPTIONEN = [
    "Aus", "Externer SVS", "Verstimmung", "AUS-Wied/Verst", "I> Abfrage", "AUS-Wied/I>Abfr",
]
# Betriebsarten mit zweistufiger Auslosung (AUS-Wiederholung auf eigenen LS, dann
# Abschaltung des Sammelschienenabschnitts):
SVS_BETRIEBSART_ZWEISTUFIG = ["AUS-Wied/Verst", "AUS-Wied/I>Abfr"]

# AUS-Wiederholung 1-/3-polig (Adr.117)
AUS_WIEDERH_OPTIONEN = ["1polig", "3polig"]

# Empfindliche Kennlinie (Adr.6320A) Umschaltung der Differentialschutzkennlinie
EMPF_KENNL_OPTIONEN = ["gesperrt", "freigegeben"]

# Zusatzkriterium fuer die Auslosung ueber Binaereingang (Adr.6120A)
ZUSATZKRIT_OPTIONEN = ["nicht vorhanden", "vorhanden"]

# Stromschwache Betriebsart SVS (Adr.116)
EIN_AUS_OPTIONEN = ["Aus", "Ein"]

# Auslosecharakteristik des Reserve-Ueberstromzeitschutzes (Feldeinheit, Adr.1211/1511)
# Belegt: KENNLINIE Voreinstellung "AMZ INVERS"; UMZ als unabhaengige Stufe ueber I>>/I>.
KENNLINIE_OPTIONEN = ["UMZ (unabhängig)", "AMZ INVERS"]

# Reaktion der Id-Ueberwachung (Adr.6310/6311)
UEBERW_REAKTION_OPTIONEN = ["melden", "blockieren", "block./freig"]


# =============================================================================
# DIGSI-ADRESSEN (7SS52 V4)
# Verifiziert gegen die Parameteruebersichten des 7SS52-Handbuchs.
# Zuordnung: ZE = Zentraleinheit, FE = Feldeinheit (abzweigselektiv).
# Die SVS-Basisadressen 114..128 erscheinen in DIGSI je Feldeinheit mit
# Feldeinheit-Praefix (Handbuch-Notation XXnn/ZE).
# =============================================================================

ADR = {
    # -- Anlagendaten / Schutz allgemein (Zentraleinheit) --------------------
    "NENNFREQUENZ":   {"7SS52": "5104"},   # ZE  Nennfrequenz

    # -- Anlagendaten / Wandler (Feldeinheit) --------------------------------
    "TAUSKOM":        {"7SS52": "1141"},   # FE  Mindestdauer des Auskommandos

    # -- 87B Sammelschienen-Differentialschutz (Zentraleinheit) --------------
    "STAB_FAKTOR_SS": {"7SS52": "6101"},   # ZE  Stabilisierungsfaktor selektiv
    "ID_SS":          {"7SS52": "6102"},   # ZE  Schwellwert Id selektiv
    "STAB_FAKTOR_CZ": {"7SS52": "6103"},   # ZE  Stabilisierungsfaktor Checkzone
    "ID_CZ":          {"7SS52": "6104"},   # ZE  Schwellwert Id Checkzone
    "QUERSTAB_SS":    {"7SS52": "6105A"},  # ZE  Querstabilisierungsfaktor selektiv
    "QUERSTAB_CZ":    {"7SS52": "6107A"},  # ZE  Querstabilisierungsfaktor Checkzone
    "IS_SS_EMPF":     {"7SS52": "6108A"},  # ZE  Schwellwert Is selektiv bei empf. Kennl.
    "ID_SS_EMPF":     {"7SS52": "6109A"},  # ZE  Schwellwert Id selektiv bei empf. Kennl.
    "IS_CZ_EMPF":     {"7SS52": "6110A"},  # ZE  Schwellwert Is Checkzone bei empf. Kennl.
    "ID_CZ_EMPF":     {"7SS52": "6111A"},  # ZE  Schwellwert Id Checkzone bei empf. Kennl.
    "ZUSATZKRIT":     {"7SS52": "6120A"},  # ZE  Zusatzkriterium fuer Auslosung
    "EMPF_KENNL":     {"7SS52": "6320A"},  # ZE  Umschaltung empfindliche Kennlinie
    "T_AUS_MIN":      {"7SS52": "6106"},   # ZE  Mindestdauer des AUS-Kommandos

    # -- 50BF Schalterversagerschutz (Zentraleinheit, abzweigselektiv) -------
    "SVS_BE_MODE":    {"7SS52": "114"},    # ZE/FE  Modus der BE fuer SVS
    "SVS_BETRIEBSART":{"7SS52": "115"},    # ZE/FE  Betriebsart SVS
    "SVS_I_KLEIN":    {"7SS52": "116"},    # ZE/FE  Stromschwache Betriebsart
    "AUS_WIEDERH":    {"7SS52": "117"},    # ZE/FE  Auswiederholung 1-/3-polig
    "I_SVS":          {"7SS52": "118"},    # ZE/FE  Schwellwert I fuer SVS
    "I_SVS_EMPF":     {"7SS52": "119A"},   # ZE/FE  Schwellwert I fuer SVS bei empf. Kennl.
    "T_SVS_1P":       {"7SS52": "120"},    # ZE/FE  Verz. SVS-Mitnahme 1-pol. Fehler
    "T_SVS_MP":       {"7SS52": "121"},    # ZE/FE  Verz. SVS-Mitnahme mehrpol. Fehler
    "T_SVS_IKLEIN":   {"7SS52": "122"},    # ZE/FE  Verz. SVS-Mitnahme stromschw. Betriebsart
    "T_SVS_IMPULS":   {"7SS52": "123A"},   # ZE/FE  Verz. SVS-Mitnahme nach Mitnahmeimpuls
    "T_SVS_LS_STOER": {"7SS52": "124"},    # ZE/FE  Verz. SVS-Mitnahme nach LS-Stoerung
    "T_AUS_WIEDERH":  {"7SS52": "125"},    # ZE/FE  Verz. SVS-Mitnahme bei AUS-Wiederholung
    "T_SVS_FRUEB":    {"7SS52": "127"},    # ZE/FE  Zeitueberwachung SVS-Freigabesignal
    "T_SVS_FRTO":     {"7SS52": "128"},    # ZE/FE  Zeitueberwachung Anwurf / Freigabe
    "STAB_FAKTOR_SVS":{"7SS52": "6201"},   # ZE  Stabilisierungsfaktor SV-Schutz
    "IS_SVS_EMPF":    {"7SS52": "6202A"},  # ZE  Schwellwert Is SVS bei empf. Kennl.

    # -- Reserve-Schalterversagerschutz (Feldeinheit) ------------------------
    "RES_SVS":        {"7SS52": "3901"},   # FE  Funktion Reserve-SVS
    "RES_SVS_I":      {"7SS52": "3911"},   # FE  Schwellwert fuer den Strom
    "RES_SVS_T":      {"7SS52": "3912"},   # FE  Verzoegerungszeit AUS-Kommando

    # -- 50/51 Reserve-Ueberstromzeitschutz Phasen (Feldeinheit) -------------
    "UMZ_P":          {"7SS52": "1201"},   # FE  Ueberstromzeitschutz Phasen Ein/Aus
    "IPH_HH":         {"7SS52": "1202"},   # FE  Phasenanregestrom Hochstromstufe I>>
    "T_IPH_HH":       {"7SS52": "1203"},   # FE  Ausloeseverzoegerung I>>
    "KENNLINIE_P":    {"7SS52": "1211"},   # FE  Auslosecharakteristik Phasen
    "IPH_H":          {"7SS52": "1212"},   # FE  Phasenanregestrom I>
    "T_IPH_H":        {"7SS52": "1213"},   # FE  Ausloeseverzoegerung I>
    "IP":             {"7SS52": "1214"},   # FE  Einstellwert AMZ-Stufe Ip
    "T_IP":           {"7SS52": "1215"},   # FE  Zeitmultiplikator Ip

    # -- 50/51 Reserve-Ueberstromzeitschutz Erde (Feldeinheit) ---------------
    "UMZ_E":          {"7SS52": "1501"},   # FE  Ueberstromzeitschutz Erde Ein/Aus
    "IE_HH":          {"7SS52": "1502"},   # FE  Erdanregestrom Hochstromstufe IE>>
    "T_IE_HH":        {"7SS52": "1503"},   # FE  Ausloeseverzoegerung IE>>
    "KENNLINIE_E":    {"7SS52": "1511"},   # FE  Auslosecharakteristik Erde
    "IE_H":           {"7SS52": "1512"},   # FE  Erdanregestrom IE>
    "T_IE_H":         {"7SS52": "1513"},   # FE  Ausloeseverzoegerung IE>
    "IEP":            {"7SS52": "1514"},   # FE  Einstellwert AMZ-Stufe IEp
    "T_IEP":          {"7SS52": "1515"},   # FE  Zeitmultiplikator IEp

    # -- Ueberwachung (Zentraleinheit) ---------------------------------------
    "TR_LAUFZEIT":    {"7SS52": "6301"},   # ZE  Maximale Trenner-Laufzeit
    "ID_UEBERW":      {"7SS52": "6306"},   # ZE  Id-Ueberwachung Ein/Aus
    "T_ID_UEBERW":    {"7SS52": "6307"},   # ZE  Verzoegerung der Id-Ueberwachung
    "ID_UEBERW_SS":   {"7SS52": "6308"},   # ZE  Schwellwert Id-Ueberwachung selektiv
    "ID_UEBERW_CZ":   {"7SS52": "6309"},   # ZE  Schwellwert Id-Ueberwachung Checkzone
    "ID_UEBERW_REAK_SS": {"7SS52": "6310"},   # ZE  Reaktion Id-Ueberwachung selektiv
    "ID_UEBERW_REAK_CZ": {"7SS52": "6311"},   # ZE  Reaktion Id-Ueberwachung Checkzone
    "NULL_DG_UEBERW": {"7SS52": "6312A"},  # ZE  Nulldurchgangsueberwachung Ein/Aus
    "I_NULL_DG":      {"7SS52": "6313A"},  # ZE  Schwellwert Nulldurchgangsueberwachung
    "LS_UEBERW_ZEIT": {"7SS52": "6315"},   # ZE  LS-Ueberwachungszeit
}


def ADR_get(key: str, geraet: str = "7SS52") -> str:
    """Liefert die DIGSI-Adresse für eine Logikgröße (7SS52).

    gerät: voller Optionsname ('Sammelschienenschutz 7SS52') oder Kurz-Key ('7SS52').
    """
    key_dev = SB_GERAET_KEY.get(geraet, geraet)
    eintrag = ADR.get(key)
    if not eintrag:
        return "—"
    return eintrag.get(key_dev, "—")


# =============================================================================
# VOREINSTELLUNGEN
# Alle Ansprechwerte als Vielfaches eines Bezugsstroms (herstellerneutral):
#   - Differentialschutz 87B: Vielfaches des Zonen-Bezugsstroms Ino  [x Ino]
#   - SVS / Reserve-SVS / UMZ/AMZ: Vielfaches des Abzweig-Nennstroms In = CT prim. [x In]
# =============================================================================

# -- 87B Sammelschienen-Differentialschutz (Zentraleinheit) -------------------
diff_aktiv_def        = True
stab_faktor_ss_def    = 0.65    # Adr.6101 Stabilisierungsfaktor selektiv     [-]
id_ss_def             = 1.00    # Adr.6102 Id> selektiv                       [x Ino]
stab_faktor_cz_def    = 0.50    # Adr.6103 Stabilisierungsfaktor Checkzone    [-]
id_cz_def             = 1.00    # Adr.6104 Id> Checkzone                      [x Ino]
querstab_ss_def       = 0.40    # Adr.6105A Querstabilisierungsfaktor selektiv [-]
querstab_cz_def       = 0.40    # Adr.6107A Querstabilisierungsfaktor Checkzone [-]
empf_kennl_def        = "gesperrt"          # Adr.6320A Umschaltung empf. Kennlinie
is_ss_empf_def        = 5.00    # Adr.6108A Is< selektiv empf. Kennl.         [x Ino]
id_ss_empf_def        = 0.25    # Adr.6109A Id> selektiv empf. Kennl.         [x Ino]
is_cz_empf_def        = 4.50    # Adr.6110A Is< Checkzone empf. Kennl.        [x Ino]
id_cz_empf_def        = 0.25    # Adr.6111A Id> Checkzone empf. Kennl.        [x Ino]
zusatzkrit_def        = "nicht vorhanden"   # Adr.6120A Zusatzkriterium
t_aus_min_def         = 0.15    # Adr.6106 Mindestdauer AUS-Kommando          [s]

# -- 50BF Schalterversagerschutz (Zentraleinheit, abzweigselektiv) -----------
svs_be_mode_def       = "1BE mit Überw"    # Adr.114
svs_betriebsart_def   = "Verstimmung"       # Adr.115
svs_i_klein_def       = "Aus"               # Adr.116 stromschwache Betriebsart
aus_wiederh_def       = "1polig"            # Adr.117
i_svs_def             = 0.50    # Adr.118 Schwellwert I fuer SVS              [x In]
i_svs_empf_def        = 0.25    # Adr.119A Schwellwert I SVS empf. Kennl.     [x In]
t_svs_1p_def          = 0.25    # Adr.120 Verz. SVS-Mitnahme 1-pol.           [s]
t_svs_mp_def          = 0.25    # Adr.121 Verz. SVS-Mitnahme mehrpol.         [s]
t_svs_iklein_def      = 0.25    # Adr.122 Verz. SVS-Mitnahme stromschwach     [s]
t_svs_impuls_def      = 0.50    # Adr.123A Verz. SVS-Mitnahme Impuls          [s]
t_svs_ls_stoer_def    = 0.10    # Adr.124 Verz. SVS-Mitnahme LS-Stoerung      [s]
t_aus_wiederh_def     = 0.12    # Adr.125 Verz. SVS bei AUS-Wiederholung      [s]
t_svs_frueb_def       = 15.00   # Adr.127 Zeitueberwachung SVS-Freigabe       [s]
t_svs_frto_def        = 0.06    # Adr.128 Zeitueberwachung Anwurf/Freigabe    [s]
stab_faktor_svs_def   = 0.50    # Adr.6201 Stabilisierungsfaktor SV-Schutz    [-]
is_svs_empf_def       = 5.00    # Adr.6202A Is< SVS empf. Kennl.              [x Ino]

# -- Reserve-Schalterversagerschutz (Feldeinheit) ----------------------------
res_svs_def           = "Aus"   # Adr.3901 Funktion Reserve-SVS
res_svs_i_def         = 0.50    # Adr.3911 Schwellwert Strom                  [x In]
res_svs_t_def         = 0.12    # Adr.3912 Verzoegerungszeit AUS-Kommando     [s]

# -- 50/51 Reserve-Ueberstromzeitschutz (Feldeinheit) ------------------------
umz_aktiv_def         = True
umz_p_def             = "Ein"   # Adr.1201 UMZ/AMZ Phasen
iph_hh_def            = 2.00    # Adr.1202 I>> Hochstromstufe                 [x In]
t_iph_hh_def          = 0.10    # Adr.1203 T I>>                              [s]
kennlinie_p_def       = "AMZ INVERS"        # Adr.1211 Charakteristik Phasen
iph_h_def             = 1.00    # Adr.1212 I>                                 [x In]
t_iph_h_def           = 0.50    # Adr.1213 T I>                               [s]
ip_def                = 1.00    # Adr.1214 Ip (AMZ-Stufe)                     [x In]
t_ip_def              = 0.50    # Adr.1215 T Ip (Zeitmultiplikator)           [s]
umz_e_def             = "Ein"   # Adr.1501 UMZ/AMZ Erde
ie_hh_def             = 0.50    # Adr.1502 IE>> Hochstromstufe                [x In]
t_ie_hh_def           = 0.50    # Adr.1503 T IE>>                             [s]
kennlinie_e_def       = "AMZ INVERS"        # Adr.1511 Charakteristik Erde
ie_h_def              = 0.20    # Adr.1512 IE>                                [x In]
t_ie_h_def            = 0.50    # Adr.1513 T IE>                              [s]
iep_def               = 0.10    # Adr.1514 IEp (AMZ-Stufe)                    [x In]
t_iep_def             = 0.50    # Adr.1515 T IEp (Zeitmultiplikator)          [s]

# -- Ueberwachung (Zentraleinheit) -------------------------------------------
ueberw_aktiv_def      = True
tr_laufzeit_def       = 7.00    # Adr.6301 Maximale Trenner-Laufzeit          [s]
id_ueberw_def         = "Ein"   # Adr.6306 Id-Ueberwachung
t_id_ueberw_def       = 2.00    # Adr.6307 Verzoegerung Id-Ueberwachung       [s]
id_ueberw_ss_def      = 0.10    # Adr.6308 Schwellwert Id-Ueberwachung selektiv [x Ino]
id_ueberw_cz_def      = 0.10    # Adr.6309 Schwellwert Id-Ueberwachung Checkzone [x Ino]
id_ueberw_reak_ss_def = "blockieren"        # Adr.6310 Reaktion Id-Ueberw. selektiv
id_ueberw_reak_cz_def = "melden"            # Adr.6311 Reaktion Id-Ueberw. Checkzone
null_dg_ueberw_def    = "Ein"   # Adr.6312A Nulldurchgangsueberwachung
i_null_dg_def         = 0.50    # Adr.6313A Schwellwert Nulldurchgangsueberw. [x Ino]
ls_ueberw_zeit_def    = 7.00    # Adr.6315 LS-Ueberwachungszeit               [s]

# -- Anlagendaten allgemein --------------------------------------------------
tauskom_def           = 0.15    # Adr.1141 Mindestdauer Auskommando           [s]
f_netz_def            = 50      # Adr.5104 Nennfrequenz                       [Hz]


# =============================================================================
# GLOBALE ENGINEERING-MARGEN / PLAUSIBILITAETS-SCHWELLWERTE
# =============================================================================

# 87B Empfindlichkeit / Stabilitaet (7SS52 Hdb. 5.1.4)
# Untere Grenze des Differential-Ansprechwerts: 1,3 x Imax Abzweig (Ansprechsicherheit).
# Obere Grenze: 0,8 x Iscc min (kleinster Sammelschienen-Fehlerstrom).
ID_FAKTOR_ABZWEIG_MIN = 1.30    # Id> > 1,3 x Imax Abzweig                    [-]
ID_FAKTOR_ISCC_MAX    = 0.80    # Id> < 0,8 x Iscc min                        [-]
# Empfindliche Kennlinie: Id auf ca. 70 % des kleinsten Fehlerstroms.
ID_EMPF_ANTEIL_ISCC   = 0.70    # Id empf. ~ 0,7 x Iscc min                   [-]
# Empfindliche Kennlinie: Is< SS ~ 1,2 x (Imax Last + IEF).
IS_EMPF_FAKTOR        = 1.20    # Is< empf. = 1,2 x Imax Last                 [-]

# Stabilisierungsfaktoren plausibel (Wertebereiche Handbuch)
STAB_SS_MIN, STAB_SS_MAX = 0.10, 0.80
STAB_CZ_MIN, STAB_CZ_MAX = 0.00, 0.80
STAB_CZ_MEHRFACH         = 0.50    # Empfehlung Mehrfachsammelschiene

# SVS: I> SVS ~ 50 % des kleinsten zu erwartenden Kurzschlussstroms.
I_SVS_ANTEIL_ISCC     = 0.50    # I> SVS ~ 0,5 x Iscc min                     [-]
# SVS-Zeit ~ 2 x Ausschaltzeit des Leistungsschalters (einstufig).
T_SVS_FAKTOR_LS       = 2.0     # T-SVS ~ 2 x t_LS                            [-]

# STW-Anpassung (sekundaerer Bezug)
Anpass_min            = 0.5     # untere Grenze STW-Anpassungsfaktor          [-]
Anpass_max            = 2.0     # obere Grenze STW-Anpassungsfaktor           [-]

Toleranz_Empfehlung   = 0.20    # Abweichung Eingabe/Empfehlung -> Hinweis    [-]


# =============================================================================
# EINGABE-ABSCHNITTE (Expander-Bezeichnungen)
# Werden in den Korrekturhinweisen genannt, damit der zu verstellende Regler
# eindeutig auffindbar ist. Die Texte spiegeln die Expander-Titel in tab_sb.py
# wider (distinktive Teilzeichenkette, ohne Geviertstrich).
# =============================================================================
ABSCHNITT_EINGABEN = "Eingaben (Grunddaten, Wandler, Netz)"
ABSCHNITT_87B      = "Erweiterte Parameter, Differentialschutz 87B"
ABSCHNITT_50BF     = "Erweiterte Parameter, Schalterversagerschutz 50BF"
ABSCHNITT_RES      = "Erweiterte Parameter, Reserve-SVS und Reserve-Überstromzeitschutz 50/51"
ABSCHNITT_UEBERW   = "Erweiterte Parameter, Differential-/Trenner-Überwachung"


# =============================================================================
# REGLERGRENZEN fuer die Bereichsschranke der Empfehlungen
# Spiegeln die number_input-Grenzen in tab_sb.py und die Einstellbereiche des
# 7SS52-Handbuchs. Liegt eine berechnete Empfehlung ausserhalb [min, max], meldet
# der Korrekturhinweis dies, statt einen nicht einstellbaren Wert zu fordern.
# =============================================================================
RG_I_SVS      = (0.10, 2.00)    # I> SVS [x In]        Adr.118
RG_ID_SS_EMPF = (0.05, 4.00)    # Id> SS empf. [x Ino] Adr.6109A
RG_IS_SS_EMPF = (0.00, 25.00)   # Is< SS empf. [x Ino] Adr.6108A
RG_T_SVS      = (0.05, 10.00)   # T-SVS-1P / T-SVS-mP [s]  Adr.120 / 121
RG_STAB_CZ    = (0.00, 0.80)    # Stab.-Faktor CZ      Adr.6103


# =============================================================================
# HERSTELLER-HINWEISE (Range + Begruendung + Adresse je parametrierbarer Groesse)
# =============================================================================

HERST = {
    # -- 87B Sammelschienen-Differentialschutz --------------------------------
    "stab_faktor_ss": {
        "range": "0,10 ... 0,80  (Voreinst. 0,65)",
        "adr":   "Stab.Faktor SS Adr.6101 (ZE)",
        "grund": ("Stabilisierungsfaktor der schienenselektiven Kennlinie. Bestimmt die "
                  "Neigung der Auslösekennlinie Id = f(Is) und damit die Stabilität bei "
                  "Wandlerfehlern durchfliessenden Stromes. 0,65 deckt den üblichen "
                  "Bebürdungsfaktor ab (7SS52 Hdb. 5.1.4)."),
    },
    "id_ss": {
        "range": "0,20 ... 4,00 x Ino  (Voreinst. 1,00); 1,3 x Imax Abzw. < Id> SS < 0,8 x Iscc min",
        "adr":   "Id> SS Adr.6102 (ZE)",
        "grund": ("Ansprechwert des Differentialstroms der selektiven Zone, bezogen auf den "
                  "Zonen-Bezugsstrom Ino. Untergrenze 1,3 x größter Abzweigstrom (Stabilität), "
                  "Obergrenze 0,8 x kleinster Sammelschienen-Kurzschlussstrom mit ca. 20 % "
                  "Ansprechsicherheit (7SS52 Hdb. 5.1.4)."),
    },
    "stab_faktor_cz": {
        "range": "0,00 ... 0,80  (Voreinst. 0,50)",
        "adr":   "Stab.Faktor CZ Adr.6103 (ZE)",
        "grund": ("Stabilisierungsfaktor der Checkzone. Bei Einfachsammelschiene wie der "
                  "selektive Faktor. Bei Mehrfachsammelschienen wird 0,5 empfohlen, um eine "
                  "Überstabilisierung durch Lastströme nicht fehlerbehafteter Abschnitte zu "
                  "vermeiden (7SS52 Hdb. 5.1.4)."),
    },
    "id_cz": {
        "range": "0,20 ... 4,00 x Ino  (Voreinst. 1,00); 1,3 x Imax Abzw. < Id> CZ < 0,8 x Iscc min",
        "adr":   "Id> CZ Adr.6104 (ZE)",
        "grund": ("Ansprechwert des Differentialstroms der Checkzone. Die Checkzone gibt die "
                  "selektive Zone frei und erfasst den Gesamt-Sammelschienenfehler ohne "
                  "Trennerabbild. Bemessung wie Id> SS (7SS52 Hdb. 5.2)."),
    },
    "querstab_ss": {
        "range": "0,00 ... 1,00  (Voreinst. 0,40, nur Bestelloption Querstabilisierung)",
        "adr":   "QuerstabFak. SS Adr.6105A (ZE)",
        "grund": ("Querstabilisierungsfaktor der selektiven Zone. 0,4 ergibt in der Regel das "
                  "beste Verhältnis zwischen Stabilität bei Wandlerbeeinflussung und "
                  "Empfindlichkeit für innenliegende Fehler (7SS52 Hdb. 5.1.4)."),
    },
    "querstab_cz": {
        "range": "0,00 ... 1,00  (Voreinst. 0,40, nur Bestelloption Querstabilisierung)",
        "adr":   "QuerstabFak. CZ Adr.6107A (ZE)",
        "grund": ("Querstabilisierungsfaktor der Checkzone. Anlagenabhängig; Voreinstellung "
                  "0,4 (7SS52 Hdb. 5.1.4)."),
    },
    "empf_kennl": {
        "range": "gesperrt (Voreinst.) / freigegeben",
        "adr":   "Empf. Kennl. Adr.6320A (ZE)",
        "grund": ("Schaltet eine empfindlichere Kennlinie mit abgesenktem Differential-Schwellwert "
                  "frei. Sinnvoll, wenn schwache Einspeisung oder die Sternpunktbehandlung nur "
                  "kleine Fehlerströme erzeugt; dann ist durch Zusatzkriterien die Stabilität "
                  "sicherzustellen (7SS52 Hdb. 5.1.4)."),
    },
    "is_ss_empf": {
        "range": "0,00 ... 25,00 x Ino  (Voreinst. 5,00); 1,2 x (Imax Last + IEF)",
        "adr":   "Is< SS empf. KL Adr.6108A (ZE)",
        "grund": ("Grenzwert des Stabilisierungsstroms der selektiven Zone bei empfindlicher "
                  "Kennlinie. Unterhalb dieses Stabilisierungsstroms gilt der abgesenkte "
                  "Schwellwert. Bemessung 1,2 x (max. Laststrom + Erdfehlerstrom) "
                  "(7SS52 Hdb. 5.1.4). Nur sichtbar bei freigegebener Empf. Kennl."),
    },
    "id_ss_empf": {
        "range": "0,05 ... 4,00 x Ino  (Voreinst. 0,25); ca. 0,7 x Iscc min",
        "adr":   "Id> SS empf. KL Adr.6109A (ZE)",
        "grund": ("Abgesenkter Differential-Schwellwert der selektiven Zone für kleine "
                  "Fehlerströme. Empfehlung 70 % des kleinsten zu erwartenden Fehlerstroms "
                  "(7SS52 Hdb. 5.1.4). Nur sichtbar bei freigegebener Empf. Kennl."),
    },
    "is_cz_empf": {
        "range": "0,00 ... 25,00 x Ino  (Voreinst. 4,50); 1,2 x 0,5 x Imax Last",
        "adr":   "Is< CZ empf. KL Adr.6110A (ZE)",
        "grund": ("Grenzwert des Stabilisierungsstroms der Checkzone bei empfindlicher Kennlinie. "
                  "Wegen der Sonderbehandlung des Checkzonen-Stabilisierungsstroms auf "
                  "1,2 x 0,5 x max. Laststrom einzustellen (7SS52 Hdb. 5.2). "
                  "Nur sichtbar bei freigegebener Empf. Kennl."),
    },
    "id_cz_empf": {
        "range": "0,05 ... 4,00 x Ino  (Voreinst. 0,25); ca. 0,7 x Iscc min",
        "adr":   "Id> CZ empf. KL Adr.6111A (ZE)",
        "grund": ("Abgesenkter Differential-Schwellwert der Checkzone. Empfehlung 70 % des "
                  "kleinsten zu erwartenden Fehlerstroms (7SS52 Hdb. 5.2). "
                  "Nur sichtbar bei freigegebener Empf. Kennl."),
    },
    "zusatzkrit": {
        "range": "nicht vorhanden (Voreinst.) / vorhanden",
        "adr":   "Zusatzkriterium Adr.6120A (ZE)",
        "grund": ("Aktiviert ein zusätzliches Auslösekriterium über Binäreingang (z.B. "
                  "Freigabe durch ein Abzweigschutzgerät über die Verlagerungsspannung). "
                  "Erhöht die Sicherheit der empfindlichen Kennlinie (7SS52 Hdb. 5.1.4)."),
    },
    "t_aus_min": {
        "range": "0,01 ... 32,00 s  (Voreinst. 0,15)",
        "adr":   "T AUS min. Adr.6106 (ZE)",
        "grund": ("Mindestdauer des AUS-Kommandos. Stellt sicher, dass das Kommando lange genug "
                  "ansteht, um die Schaltspulen sicher anzusteuern (7SS52 Hdb. 5.1.4)."),
    },

    # -- 50BF Schalterversagerschutz ------------------------------------------
    "svs_be_mode": {
        "range": "1BE ohne/mit Überw, 2BE ohne/mit Überw  (Voreinst. 1BE mit Überw)",
        "adr":   "SVS-BE-Mode Adr.114 (je Feldeinheit)",
        "grund": ("Art der Binäreingangs-Auswertung für den SVS-Anwurf. Mit Überwachung "
                  "wird die Signaldauer kontrolliert, um Fehlanwürfe zu erkennen "
                  "(7SS52 Hdb. 5.3.2)."),
    },
    "svs_betriebsart": {
        "range": "Aus / Externer SVS / Verstimmung / AUS-Wied/Verst / I> Abfrage / AUS-Wied/I>Abfr "
                 "(Voreinst. Verstimmung)",
        "adr":   "SVS-Betriebsart Adr.115 (je Feldeinheit)",
        "grund": ("Betriebsart des Schalterversagerschutzes. Verstimmung wertet den fortbestehenden "
                  "Differentialstrom aus; die AUS-Wied-Varianten setzen zunächst eine "
                  "Auswiederholung auf den eigenen Leistungsschalter ab (zweistufig) "
                  "(7SS52 Hdb. 5.3.5)."),
    },
    "svs_i_klein": {
        "range": "Aus (Voreinst.) / Ein",
        "adr":   "SVS-I< Adr.116 (je Feldeinheit)",
        "grund": ("Stromschwache Betriebsart. Erfasst Schalterversagen auch bei kleinen "
                  "Abzweigströmen über die LS-Stellung, wenn kein Stromfluss mehr vorliegt "
                  "(7SS52 Hdb. 5.3.5)."),
    },
    "aus_wiederh": {
        "range": "1polig (Voreinst.) / 3polig",
        "adr":   "AUS-Wiederh. Adr.117 (je Feldeinheit)",
        "grund": ("Polzahl der AUS-Wiederholung auf den eigenen Schalter. 1-polig nur bei "
                  "1-poligem Anstoss und 1-pol-fähigem Schalter; sonst 3-polig "
                  "(7SS52 Hdb. 5.3.5)."),
    },
    "i_svs": {
        "range": "0,10 ... 2,00 x In  (Voreinst. 0,50); ca. 0,5 x Iscc min",
        "adr":   "I> SVS Adr.118 (je Feldeinheit)",
        "grund": ("Stromschwelle, ab der ein anhaltender Stromfluss als Schalterversagen gewertet "
                  "wird. Empfehlung ca. 50 % des kleinsten zu erwartenden Kurzschlussstroms "
                  "(7SS52 Hdb. 5.3.2)."),
    },
    "i_svs_empf": {
        "range": "0,05 ... 2,00 x In  (Voreinst. 0,25)",
        "adr":   "I> SVS empf. KL Adr.119A (je Feldeinheit)",
        "grund": ("Abgesenkte SVS-Stromschwelle bei freigegebener empfindlicher Kennlinie, für "
                  "stromschwache Fehler (7SS52 Hdb. 5.3.1)."),
    },
    "t_svs_1p": {
        "range": "0,05 ... 10,00 s  (Voreinst. 0,25); ca. 2 x Ausschaltzeit LS",
        "adr":   "T-SVS-1P Adr.120 (je Feldeinheit)",
        "grund": ("Verzögerung von AUS-Kommando und Mitnahme bei 1-poligem Fehler. Einstufig: "
                  "etwa das Doppelte der Ausschaltzeit des Leistungsschalters; zweistufig größer "
                  "als T-AUS-Wiederh. plus LS-Ausschaltzeit (7SS52 Hdb. 5.3.2)."),
    },
    "t_svs_mp": {
        "range": "0,05 ... 10,00 s  (Voreinst. 0,25); ca. 2 x Ausschaltzeit LS",
        "adr":   "T-SVS-mP Adr.121 (je Feldeinheit)",
        "grund": ("Verzögerung von AUS-Kommando und Mitnahme bei mehrpoligem Fehler. Bemessung "
                  "wie T-SVS-1P (7SS52 Hdb. 5.3.2)."),
    },
    "t_svs_iklein": {
        "range": "0,05 ... 10,00 s  (Voreinst. 0,25)",
        "adr":   "T-SVS-I< Adr.122 (je Feldeinheit)",
        "grund": ("Verzögerung der SVS-Mitnahme in der stromschwachen Betriebsart "
                  "(7SS52 Hdb. 5.3.5)."),
    },
    "t_svs_impuls": {
        "range": "0,05 ... 10,00 s  (Voreinst. 0,50)",
        "adr":   "T-SVS-Impuls Adr.123A (je Feldeinheit)",
        "grund": ("Verzögerung der abzweigselektiven AUS-Wiederholung im Impulsbetrieb "
                  "(7SS52 Hdb. 5.3.5)."),
    },
    "t_svs_ls_stoer": {
        "range": "0,00 ... 10,00 s  (Voreinst. 0,10)",
        "adr":   "T-SVS-LS-Störg Adr.124 (je Feldeinheit)",
        "grund": ("Verzögerung von AUS-Kommando und Mitnahme bei erkannter Störung des "
                  "Leistungsschalters dieses Abzweigs (7SS52 Hdb. 5.3.5)."),
    },
    "t_aus_wiederh": {
        "range": "0,00 ... 10,00 s  (Voreinst. 0,12); kleiner als T-SVS-1P / T-SVS-mP",
        "adr":   "T-AUS-Wiederh. Adr.125 (je Feldeinheit)",
        "grund": ("Verzögerung der abzweigselektiven AUS-Wiederholung (1. Stufe auf den eigenen "
                  "Schalter). Muss kleiner als die SVS-Verzögerungszeiten T-SVS-1P/mP eingestellt "
                  "werden (7SS52 Hdb. 5.3.5)."),
    },
    "t_svs_frueb": {
        "range": "0,02 ... 15,00 s  (Voreinst. 15,00)",
        "adr":   "T-SVS-FrÜb Adr.127 (je Feldeinheit)",
        "grund": ("Zeitfenster, in dem die Signaldauer der SVS-Freigabe überwacht wird (nur bei "
                  "SVS-BE-Mode mit Überwachung) (7SS52 Hdb. 5.3.2)."),
    },
    "t_svs_frto": {
        "range": "0,06 ... 1,00 s  (Voreinst. 0,06)",
        "adr":   "T-SVS-FrTo Adr.128 (je Feldeinheit)",
        "grund": ("Zeitfenster, innerhalb dessen ab Anstoss das Freigabesignal vorliegen muss "
                  "(7SS52 Hdb. 5.3.2)."),
    },
    "stab_faktor_svs": {
        "range": "0,00 ... 0,80  (Voreinst. 0,50)",
        "adr":   "Stab.Faktor SVS Adr.6201 (ZE)",
        "grund": ("Stabilisierungsfaktor der SVS-Kennlinie für die Verstimmungsbetriebsart "
                  "(7SS52 Hdb. 5.3.2)."),
    },
    "is_svs_empf": {
        "range": "0,00 ... 25,00 x Ino  (Voreinst. 5,00)",
        "adr":   "Is< SV empf. KL Adr.6202A (ZE)",
        "grund": ("Grenzwert des Stabilisierungsstroms der SVS-Kennlinie bei empfindlicher "
                  "Kennlinie (7SS52 Hdb. 5.3.1)."),
    },

    # -- Reserve-Schalterversagerschutz (Feldeinheit) -------------------------
    "res_svs": {
        "range": "Aus (Voreinst.) / Ein",
        "adr":   "RESERV.SVS Adr.3901 (FE)",
        "grund": ("Autarker Reserve-Schalterversagerschutz in der Feldeinheit. Arbeitet "
                  "unabhängig von der Zentraleinheit und sichert gegen Ausfall der zentralen "
                  "SVS-Funktion ab (7SS52 Hdb. 5.18)."),
    },
    "res_svs_i": {
        "range": "0,10 ... 4,00 x In  (Voreinst. 0,50)",
        "adr":   "RES.SVS-I Adr.3911 (FE)",
        "grund": ("Stromschwelle des Reserve-SVS. Wie I> SVS unterhalb des kleinsten "
                  "Kurzschlussstroms zu wählen (7SS52 Hdb. 5.18)."),
    },
    "res_svs_t": {
        "range": "0,06 ... 60,00 s  (Voreinst. 0,12)",
        "adr":   "RES.SVS-T Adr.3912 (FE)",
        "grund": ("Verzögerungszeit des Reserve-SVS bis zum AUS-Kommando. In der Regel etwas "
                  "größer als die zentrale SVS-Zeit, damit die Reserve nachgeordnet wirkt "
                  "(7SS52 Hdb. 5.18)."),
    },

    # -- 50/51 Reserve-Ueberstromzeitschutz (Feldeinheit) ---------------------
    "iph_hh": {
        "range": "0,05 ... 25,00 x In  (Voreinst. 2,00)",
        "adr":   "I>> Adr.1202 (FE)",
        "grund": ("Phasen-Hochstromstufe des Reserve-Überstromzeitschutzes. Oberhalb der "
                  "Überstromstufe I> einzustellen; dient als unverzögerte Reserve bei "
                  "nahen Fehlern (7SS52 Hdb. 5.11)."),
    },
    "t_iph_hh": {
        "range": "0,00 ... 60,00 s  (Voreinst. 0,10)",
        "adr":   "TI>> Adr.1203 (FE)",
        "grund": ("Auslöseverzögerung der Hochstromstufe I>> (7SS52 Hdb. 5.11)."),
    },
    "kennlinie_p": {
        "range": "UMZ (unabhängig) / AMZ INVERS  (Voreinst. AMZ INVERS)",
        "adr":   "KENNLINIE Adr.1211 (FE)",
        "grund": ("Auslösecharakteristik der Phasenstufe. UMZ = unabhängige (definite) Zeit, "
                  "AMZ = stromabhängige Kennlinie nach IEC 60255-151 (7SS52 Hdb. 5.11)."),
    },
    "iph_h": {
        "range": "0,05 ... 25,00 x In  (Voreinst. 1,00)",
        "adr":   "I> Adr.1212 (FE)",
        "grund": ("Phasen-Überstromstufe (UMZ). Oberhalb des maximalen Betriebsstroms und "
                  "unterhalb des minimalen Kurzschlussstroms (7SS52 Hdb. 5.11)."),
    },
    "t_iph_h": {
        "range": "0,00 ... 60,00 s  (Voreinst. 0,50)",
        "adr":   "TI> Adr.1213 (FE)",
        "grund": ("Auslöseverzögerung der Überstromstufe I> (7SS52 Hdb. 5.11)."),
    },
    "ip": {
        "range": "0,10 ... 4,00 x In  (Voreinst. 1,00)",
        "adr":   "Ip Adr.1214 (FE)",
        "grund": ("Einstellwert der stromabhängigen AMZ-Stufe Ip. Wirkt nur bei AMZ-Kennlinie "
                  "(7SS52 Hdb. 5.11)."),
    },
    "t_ip": {
        "range": "0,05 ... 10,00 s  (Voreinst. 0,50)",
        "adr":   "TIp Adr.1215 (FE)",
        "grund": ("Zeitmultiplikator der AMZ-Kennlinie der Phasenstufe (7SS52 Hdb. 5.11)."),
    },
    "ie_hh": {
        "range": "0,05 ... 25,00 x In  (Voreinst. 0,50)",
        "adr":   "IE>> Adr.1502 (FE)",
        "grund": ("Erd-Hochstromstufe des Reserve-Überstromzeitschutzes (7SS52 Hdb. 5.12)."),
    },
    "t_ie_hh": {
        "range": "0,00 ... 60,00 s  (Voreinst. 0,50)",
        "adr":   "TIE>> Adr.1503 (FE)",
        "grund": ("Auslöseverzögerung der Erd-Hochstromstufe IE>> (7SS52 Hdb. 5.12)."),
    },
    "kennlinie_e": {
        "range": "UMZ (unabhängig) / AMZ INVERS  (Voreinst. AMZ INVERS)",
        "adr":   "KENNLINIE Adr.1511 (FE)",
        "grund": ("Auslösecharakteristik der Erdstufe (7SS52 Hdb. 5.12)."),
    },
    "ie_h": {
        "range": "0,05 ... 25,00 x In  (Voreinst. 0,20)",
        "adr":   "IE> Adr.1512 (FE)",
        "grund": ("Erd-Überstromstufe (UMZ). Empfindlicher als die Phasenstufe, oberhalb der "
                  "betrieblichen Unsymmetrie (7SS52 Hdb. 5.12)."),
    },
    "t_ie_h": {
        "range": "0,00 ... 60,00 s  (Voreinst. 0,50)",
        "adr":   "TIE> Adr.1513 (FE)",
        "grund": ("Auslöseverzögerung der Erd-Überstromstufe IE> (7SS52 Hdb. 5.12)."),
    },
    "iep": {
        "range": "0,10 ... 4,00 x In  (Voreinst. 0,10)",
        "adr":   "IEp Adr.1514 (FE)",
        "grund": ("Einstellwert der stromabhängigen AMZ-Stufe IEp für Erde (7SS52 Hdb. 5.12)."),
    },
    "t_iep": {
        "range": "0,05 ... 10,00 s  (Voreinst. 0,50)",
        "adr":   "TIEp Adr.1515 (FE)",
        "grund": ("Zeitmultiplikator der AMZ-Kennlinie der Erdstufe (7SS52 Hdb. 5.12)."),
    },

    # -- Ueberwachung ---------------------------------------------------------
    "tr_laufzeit": {
        "range": "1,00 ... 180,00 s  (Voreinst. 7,00)",
        "adr":   "TR-Laufzeit Adr.6301 (ZE)",
        "grund": ("Maximale Trenner-Laufzeit. Überwacht, dass die Trenner-Stellungsmeldungen "
                  "innerhalb dieser Zeit plausibel werden; länger als die langsamste "
                  "Trennerbewegung (7SS52 Hdb. 5.9)."),
    },
    "id_ueberw": {
        "range": "Aus / Ein  (Voreinst. Ein)",
        "adr":   "Id-Überw. Adr.6306 (ZE)",
        "grund": ("Dauerüberwachung des Differentialstroms. Erkennt schleichende Wandler- oder "
                  "Verdrahtungsfehler und kann den Schutz blockieren (7SS52 Hdb. 5.9)."),
    },
    "t_id_ueberw": {
        "range": "1,00 ... 10,00 s  (Voreinst. 2,00)",
        "adr":   "T-Id-Überw. Adr.6307 (ZE)",
        "grund": ("Verzögerung der Id-Überwachung. Länger als die längste zulässige "
                  "transiente Differenz, um Fehlmeldungen zu vermeiden (7SS52 Hdb. 5.9)."),
    },
    "id_ueberw_ss": {
        "range": "0,05 ... 0,80 x Ino  (Voreinst. 0,10)",
        "adr":   "Id> Überw. SS Adr.6308 (ZE)",
        "grund": ("Schwellwert der Id-Überwachung der selektiven Zone. Deutlich unterhalb des "
                  "Ansprechwerts Id> SS, damit Fehler vor dem Schutzansprechen gemeldet werden "
                  "(7SS52 Hdb. 5.9)."),
    },
    "id_ueberw_cz": {
        "range": "0,05 ... 0,80 x Ino  (Voreinst. 0,10)",
        "adr":   "Id> Überw. CZ Adr.6309 (ZE)",
        "grund": ("Schwellwert der Id-Überwachung der Checkzone. Bemessung wie Id-Überwachung SS "
                  "(7SS52 Hdb. 5.9)."),
    },
    "id_ueberw_reak_ss": {
        "range": "melden / blockieren / block./freig  (Voreinst. blockieren)",
        "adr":   "Id-Üb.Reak. SS Adr.6310 (ZE)",
        "grund": ("Reaktion des Schutzes bei Ansprechen der Differentialstrom-Überwachung der "
                  "selektiven Zone. melden meldet nur, blockieren sperrt den selektiven Schutz "
                  "für die Dauer der Störung, block./freig sperrt mit anschließender Freigabe. "
                  "Werksseitig blockieren, da die selektive Zone vom Trennerabbild abhängt "
                  "(7SS52 Hdb. 5.5.1.8)."),
    },
    "id_ueberw_reak_cz": {
        "range": "melden / blockieren / block./freig  (Voreinst. melden)",
        "adr":   "Id-Üb.Reak. CZ Adr.6311 (ZE)",
        "grund": ("Reaktion bei Ansprechen der Id-Überwachung der Checkzone. Werksseitig melden, "
                  "da die Checkzone als unabhängige Freigabe wirkt und nicht vorschnell blockieren "
                  "soll (7SS52 Hdb. 5.5.1.8)."),
    },
    "null_dg_ueberw": {
        "range": "Aus / Ein  (Voreinst. Ein)",
        "adr":   "Null-DG-Überw. Adr.6312A (ZE)",
        "grund": ("Nulldurchgangsüberwachung. Pruft die Plausibilität der Stromnulldurchgänge "
                  "zur Erkennung von Wandler-/Messfehlern (7SS52 Hdb. 5.9)."),
    },
    "i_null_dg": {
        "range": "0,15 ... 4,00 x Ino  (Voreinst. 0,50)",
        "adr":   "I>Null-DG-Überw Adr.6313A (ZE)",
        "grund": ("Stromschwelle, ab der die Nulldurchgangsüberwachung wirkt (7SS52 Hdb. 5.9)."),
    },
    "ls_ueberw_zeit": {
        "range": "1,00 ... 180,00 s  (Voreinst. 7,00)",
        "adr":   "LS-Überw.-Zeit Adr.6315 (ZE)",
        "grund": ("Überwachungszeit der Leistungsschalter-Stellung. Länger als die langsamste "
                  "Schalterbewegung (7SS52 Hdb. 5.9)."),
    },

    # -- Anlagendaten / Wandler -----------------------------------------------
    "tauskom": {
        "range": "0,01 ... 32,00 s  (Voreinst. 0,15)",
        "adr":   "TAUSKOM Adr.1141 (FE)",
        "grund": ("Mindestdauer des Auskommandos der Feldeinheit. Stellt eine sichere "
                  "Ansteuerung der Auslösespulen sicher (7SS52 Hdb. Feldeinheit)."),
    },
}
