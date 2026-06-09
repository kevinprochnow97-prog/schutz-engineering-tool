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
Rush_2H_Ph_def    = 0.15   # 2.Harm. Phasen-Rushstabilisierung        [-]

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

# ── 24 Übererregungsschutz U/f (nur 7UT613/633 mit Spannungseingang) ─────────
# U/f-Werte sind dimensionslos, bezogen auf U/f unter Nennbedingungen (= 1,0).
Uf_Warn_def       = 1.10   # Adr.4302 U/f >  (Warnstufe)              [-]
t_Uf_Warn_def     = 10.00  # Adr.4303 T U/f>                         [s]
Uf_Aus_def        = 1.40   # Adr.4304 U/f >> (Auslösestufe)          [-]
t_Uf_Aus_def      = 1.00   # Adr.4305 T U/f >>                       [s]

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

VEKTORGRUPPEN = [
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
    "Uf_Warn": {
        "range": "1,00 ... 1,20 (Voreinst. 1,10)",
        "grund": ("U/f-Warnstufe (ANSI 24, Adr.4302). Der vom Hersteller angegebene "
                  "dauernd zulässige Induktionswert B/BN bildet die Grundlage; 1,10 schützt "
                  "den Kern vor Sättigung bei Spannungsanstieg oder Frequenzeinbruch "
                  "(7UT613 Hdb. 2.11). Nur bei Geräten mit Spannungseingang."),
    },
    "Uf_Aus": {
        "range": "1,00 ... 1,40 (Voreinst. 1,40)",
        "grund": ("U/f-Schnellauslösestufe (Adr.4304). Hohe Übererregung gefährdet den "
                  "Kern bereits in kurzer Zeit, daher nur kurz verzögert (T U/f>> ca. 1 s, "
                  "Adr.4305). 7UT613 Hdb. 2.11."),
    },
}


# ── Adressen-Zuordnung fuer die Regler-Captions (eine Adresse je Parameter) ──
# Nur echte 7UT6xx-Relaisparameter. Engineering-Margen (k_S_*, gamma, Inrush)
# sind tool-intern und bekommen bewusst KEINE Adresse.
_HERST_ADR = {
    "I_DIFF": "Adr.1221", "I_DIFF_HH": "Adr.1231", "Steigung_1": "Adr.1241A",
    "Steigung_2": "Adr.1243A", "Fusspunkt_2": "Adr.1244A", "Harm_2": "Adr.1271",
    "f_I_Ph": "Adr.2011", "t_I_Ph": "Adr.2013",
    "f_I_Ph_HH_OS": "Adr.2014 (Seite OS)", "f_I_Ph_HH_US": "Adr.2014 (Seite US)",
    "t_I_Ph_HH": "Adr.2016", "k_Faktor": "Adr.4202", "tau_min": "Adr.4203",
    "I2_zul": "Adr.4032", "Uf_Warn": "Adr.4302", "Uf_Aus": "Adr.4304",
}
for _k, _a in _HERST_ADR.items():
    if _k in HERST:
        HERST[_k]["adr"] = _a
