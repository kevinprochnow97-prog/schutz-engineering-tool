"""
calc_trafo.py — Berechnungslogik Transformatorschutz
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reine Python-Funktionen (kein Streamlit) -> isoliert testbar.
Bildet die Excel-Sektionen 4.5 bis 4.16 ab:
  4.5  Berechnete Grundgrößen
  4.6  Differentialschutz 87T
  4.7  Erdfehler-Differentialschutz 87N (EDS)
  4.8  Überstromzeitschutz Phasen 50/51 (OS + US)
  4.9  Überstromzeitschutz Erde 50N/51N
  4.10 U0-Erdschlusserfassung (isoliert/kompensiert)
  4.11 Thermischer Ueberlastschutz 49
  4.12 Schieflastschutz 46
  4.13 Plausibilitätsprüfung (Ampel)
  4.14 Bemessungs-Engineering (I_max_Last, I_k_min, Empfindlichkeit)
  4.15 Reserveschutz-Zuordnung / DIGSI-Adressen
  4.16 Geräte-Empfehlung Erdschlusserfassung
"""

import math
import konstanten as K

SQRT3 = math.sqrt(3)


# ── Hilfsfunktion: Ampel-Status Eingabe vs. Empfehlung ───────────────────────

def status_empfehlung(eingabe, empfehlung, tol: float = K.Toleranz_Empfehlung) -> str:
    """OK = identisch | Hinweis = Abweichung < tol | Prüfen! = Abweichung >= tol."""
    if empfehlung is None or empfehlung == "":
        return "Fehlt"
    if abs(eingabe - empfehlung) < 1e-9:
        return "OK"
    if abs(eingabe - empfehlung) / max(abs(empfehlung), 1e-3) < tol:
        return "Hinweis"
    return "Prüfen!"


def status_bereich(wert, unten, oben) -> str:
    """OK wenn Wert im Bereich [unten, oben], sonst Prüfen!"""
    if wert is None:
        return "Fehlt"
    return "OK" if (unten <= wert <= oben) else "Prüfen!"


# ── 4.5  Berechnete Grundgrößen ────────────────────────────────────────────

def grundgroessen(p: dict) -> dict:
    """
    Nennströme, Trafo-Uebersetzung, Wandlerverhältnisse, Bezugsströme.
    Erwartet in p: Sn_MVA, UN_OS_kV, UN_US_kV,
                   CT_OS_Prim, CT_OS_Sek, CT_US_Prim, CT_US_Sek,
                   CT_E_Prim, CT_E_Sek
    """
    Sn, UOS, UUS = p["Sn_MVA"], p["UN_OS_kV"], p["UN_US_kV"]

    IN_OS_prim = (Sn * 1e6) / (SQRT3 * UOS * 1e3) if UOS > 0 else 0.0
    IN_US_prim = (Sn * 1e6) / (SQRT3 * UUS * 1e3) if UUS > 0 else 0.0
    nT = UOS / UUS if UUS > 0 else 0.0

    kCT_OS = p["CT_OS_Prim"] / p["CT_OS_Sek"] if p["CT_OS_Sek"] else 0.0
    kCT_US = p["CT_US_Prim"] / p["CT_US_Sek"] if p["CT_US_Sek"] else 0.0
    kCT_E  = p["CT_E_Prim"]  / p["CT_E_Sek"]  if p.get("CT_E_Sek") else 0.0

    IN_OS_sek = IN_OS_prim / kCT_OS if kCT_OS else 0.0
    IN_US_sek = IN_US_prim / kCT_US if kCT_US else 0.0
    IN_Obj_sek = max(IN_OS_sek, IN_US_sek)

    # STW-Anpassungsfaktor I_an = CT_Sek / IN_sek  (7UT613 Hdb. 2.2.7: 0,5 ... 2,0)
    I_an_OS = p["CT_OS_Sek"] / IN_OS_sek if IN_OS_sek else 0.0
    I_an_US = p["CT_US_Sek"] / IN_US_sek if IN_US_sek else 0.0

    return {
        "IN_OS_prim": round(IN_OS_prim, 4),
        "IN_US_prim": round(IN_US_prim, 4),
        "nT":         round(nT, 4),
        "kCT_OS":     round(kCT_OS, 4),
        "kCT_US":     round(kCT_US, 4),
        "kCT_E":      round(kCT_E, 4),
        "IN_OS_sek":  round(IN_OS_sek, 4),
        "IN_US_sek":  round(IN_US_sek, 4),
        "IN_Obj_sek": round(IN_Obj_sek, 4),
        "I_an_OS":    round(I_an_OS, 4),
        "I_an_US":    round(I_an_US, 4),
    }


# ── 4.6  Differentialschutz 87T ──────────────────────────────────────────────

def schutz_87T(g: dict, p: dict) -> dict:
    """
    87T nach 7UT6xx-Methodik. Bezugsstrom = IN_Obj_sek (größerer Sekundär-Nennstrom).
    Liefert je Parameter: Eingabe, Wert sek., Wert prim. OS, dyn. Empfehlung, Status.
    """
    INO_sek = g["IN_Obj_sek"]
    INOS_pr = g["IN_OS_prim"]
    uk  = p["uk_pct"]
    stp = p["Stufensteller_pm"]
    Sn  = p["Sn_MVA"]

    # Eingaben (mit Override-Möglichkeit, sonst Konstanten)
    I_DIFF    = p.get("I_DIFF",    K.I_DIFF_def)
    I_DIFF_HH = p.get("I_DIFF_HH", K.I_DIFF_HH_def)
    Fp1       = p.get("Fusspunkt_1", K.Fusspunkt_1_def)
    Fp2       = p.get("Fusspunkt_2", K.Fusspunkt_2_def)
    Stb_Anl   = K.Anlauf_Stab_def
    Stb_EXF   = K.EXF_Stab_def
    Steig1    = p.get("Steigung_1", K.Steigung_1_def)
    Steig2    = p.get("Steigung_2", K.Steigung_2_def)
    AnlFak    = K.Anlauf_Faktor_def
    Harm2     = p.get("Harm_2", K.Harm_2_def)
    Harmn     = K.Harm_n_def

    # Dynamische Empfehlungen (Spalte F der Excel)
    emp_IDIFF  = 0.30 if stp > K.Stufensteller_hoch else (0.25 if stp > K.Stufensteller_warn else 0.20)
    emp_IDIFFH = min(15.0, round(120.0 / uk, 1)) if uk > 0 else None
    emp_Fp1    = 0.0
    emp_Fp2    = (3.0 if uk < K.uk_fusspunkt_niedrig else 2.5) if uk > 0 else None
    emp_Steig1 = 0.30 if stp > K.Stufensteller_steig1 else 0.25
    emp_Steig2 = 0.55 if Sn > K.Sn_steig2_hoch else 0.50

    def row(name, fak, einheit, emp, adr, sek=True, prim=True):
        return {
            "name": name, "faktor": fak, "einheit": einheit,
            "wert_sek": round(fak * INO_sek, 4) if sek else None,
            "wert_prim": round(fak * INOS_pr, 4) if prim else None,
            "empfehlung": emp,
            "status": status_empfehlung(fak, emp) if emp is not None else "—",
            "adresse": adr,
        }

    rows = [
        row("I-DIFF>  (Ansprechwert)",       I_DIFF,    "I/InO", emp_IDIFF,  "Adr.1221"),
        row("I-DIFF>> (Hochstromstufe)",     I_DIFF_HH, "I/InO", emp_IDIFFH, "Adr.1231"),
        row("Fußpunkt 1",                   Fp1,       "I/InO", emp_Fp1,    "Adr.1242A"),
        row("Fußpunkt 2",                   Fp2,       "I/InO", emp_Fp2,    "Adr.1244A"),
        row("Anlauf-Stabilisierung ISTAB",  Stb_Anl,   "I/InO", None,       "Adr.1251A"),
        row("EXF-Stab. (ext. Fehler)",      Stb_EXF,   "I/InO", None,       "Adr.1261A"),
    ]
    # Steigungen / Faktoren ohne Stromwert
    rows += [
        {"name": "Steigung 1", "faktor": Steig1, "einheit": "-", "wert_sek": None,
         "wert_prim": None, "empfehlung": emp_Steig1, "status": status_empfehlung(Steig1, emp_Steig1), "adresse": "Adr.1241A"},
        {"name": "Steigung 2", "faktor": Steig2, "einheit": "-", "wert_sek": None,
         "wert_prim": None, "empfehlung": emp_Steig2, "status": status_empfehlung(Steig2, emp_Steig2), "adresse": "Adr.1243A"},
        {"name": "Anlauf-Faktor", "faktor": AnlFak, "einheit": "-", "wert_sek": None,
         "wert_prim": None, "empfehlung": None, "status": "—", "adresse": "Adr.1252A"},
        {"name": "T I-DIFF>",  "faktor": K.T_I_DIFF_def,    "einheit": "s", "wert_sek": None,
         "wert_prim": None, "empfehlung": None, "status": "—", "adresse": "Adr.1226A"},
        {"name": "T I-DIFF>>", "faktor": K.T_I_DIFF_HH_def, "einheit": "s", "wert_sek": None,
         "wert_prim": None, "empfehlung": None, "status": "—", "adresse": "Adr.1236A"},
        {"name": "2. Harmonische (Inrush)", "faktor": round(Harm2 * 100, 1), "einheit": "%", "wert_sek": None,
         "wert_prim": None, "empfehlung": None, "status": "—", "adresse": "Adr.1271"},
        {"name": "n. Harmonische", "faktor": round(Harmn * 100, 1), "einheit": "%", "wert_sek": None,
         "wert_prim": None, "empfehlung": None, "status": "—", "adresse": "Adr.1276"},
    ]
    return {
        "INN_Bezug_A": round(INO_sek, 4),
        "I_DIFF_Anspr_sek_A":  round(I_DIFF * INO_sek, 4),
        "I_DIFF_Anspr_prim_A": round(I_DIFF * INOS_pr, 4),
        "rows": rows,
    }


# ── 4.7  Erdfehler-Differentialschutz 87N (EDS) ──────────────────────────────

def schutz_87N(g: dict, p: dict) -> dict:
    """
    87N benötigt geerdeten Sternpunkt + Sternpunkt-CT (IE-Wandler).
    Bei isoliertem/kompensiertem Netz oder fehlendem IE-CT -> nicht geeignet.
    """
    geerdet = (p["stp_OS"] not in K.STERNPUNKT_NICHT_GEERDET
               or p["stp_US"] not in K.STERNPUNKT_NICHT_GEERDET)
    ie_ct = p.get("IE_Wandler", True) and p.get("CT_E_Prim", 0) > 0

    if not geerdet or not ie_ct:
        grund = ("Beide Seiten isoliert/kompensiert: kein ausreichender Erdfehlerstrom. "
                 "Erdschlusserfassung über U0/wattmetrisch (siehe Erdschluss-/Erdfehlerschutz)."
                 if not geerdet else
                 "Kein Sternpunkt-Stromwandler (IE-CT) vorhanden -> 87N nicht möglich.")
        return {"aktiv": False, "grund": grund}

    I_EDS = K.I_EDS_def
    return {
        "aktiv": True,
        "I_EDS_sek_A":  round(I_EDS * g["IN_OS_sek"], 4),
        "I_EDS_prim_A": round(I_EDS * g["IN_OS_prim"], 4),
        "I_EDS_faktor": I_EDS,
        "T_I_EDS_s":    K.T_I_EDS_def,
        "Steigung_EDS": K.Steigung_EDS_def,
    }


# ── 4.8  Überstromzeitschutz Phasen 50/51 (OS + US) ─────────────────────────

def empfehlung_IHH_OS(g: dict, p: dict) -> float:
    """
    Empfohlener I>>-Faktor OS-Speiseseite (x IN_OS) nach 7UT613 Hdb. 2.4:
    I>> muss oberhalb des maximalen Durchgangsfehlerstroms liegen.
      I>>_prim = k_S_IGG * Ik_max_US (auf OS bezogen, d.h. / nT)
      Faktor   = I>>_prim / IN_OS_prim
    Fallback über 1,2/uk, falls kein Ik_max_US eingegeben wurde.
    """
    k_S_IGG = p.get("k_S_IGG", K.k_S_IGG)
    nT      = g["nT"]
    INOS_pr = g["IN_OS_prim"]
    Ik_US   = p.get("Ik_max_US_kA", 0.0) * 1000.0  # A prim. US

    if Ik_US > 0 and nT and INOS_pr:
        I_durch_OS = Ik_US / nT                      # Durchgangsfehler auf OS bezogen
        faktor = k_S_IGG * I_durch_OS / INOS_pr
    elif p.get("uk_pct", 0) > 0:
        faktor = k_S_IGG / (p["uk_pct"] / 100.0)     # Daumenwert 1,2/uk
    else:
        faktor = K.f_I_Ph_HH_def
    return round(faktor, 2)


def schutz_5051_phase(g: dict, p: dict) -> dict:
    """
    I>/I>> Phasen beidseitig (OS + US), Faktor x IN_Seite.
    I>> ist für OS und US GETRENNT:
      - OS (Speiseseite): Default automatisch aus 1,2/uk bzw. Ik_max_US.
      - US: gegen die nachgelagerte Staffelung (eigener Faktor).
    Eingaben f_I_Ph_HH_OS / f_I_Ph_HH_US überschreiben die Defaults.
    """
    f_I    = p.get("f_I_Ph",  K.f_I_Ph_def)
    t_I    = p.get("t_I_Ph",  K.t_I_Ph_def)
    t_IHH  = p.get("t_I_Ph_HH", K.t_I_Ph_HH_def)

    f_IHH_OS_emp = empfehlung_IHH_OS(g, p)
    f_IHH_OS = p.get("f_I_Ph_HH_OS", f_IHH_OS_emp)
    f_IHH_US = p.get("f_I_Ph_HH_US", K.f_I_Ph_HH_def)

    return {
        "f_I": f_I, "t_I": t_I, "t_IHH": t_IHH,
        "f_IHH_OS": f_IHH_OS, "f_IHH_US": f_IHH_US,
        "f_IHH_OS_emp": f_IHH_OS_emp,
        "rush_2H_pct": round(K.Rush_2H_Ph_def * 100, 1),
        "OS": {
            "I_sek":   round(f_I      * g["IN_OS_sek"], 4),
            "I_prim":  round(f_I      * g["IN_OS_prim"], 4),
            "IHH_sek": round(f_IHH_OS * g["IN_OS_sek"], 4),
            "IHH_prim":round(f_IHH_OS * g["IN_OS_prim"], 4),
        },
        "US": {
            "I_sek":   round(f_I      * g["IN_US_sek"], 4),
            "I_prim":  round(f_I      * g["IN_US_prim"], 4),
            "IHH_sek": round(f_IHH_US * g["IN_US_sek"], 4),
            "IHH_prim":round(f_IHH_US * g["IN_US_prim"], 4),
        },
    }


# ── 4.9  Überstromzeitschutz Erde 50N/51N (Sternpunkt-Strom) ────────────────

def schutz_5051_erde(g: dict, p: dict) -> dict:
    """
    IE>/IE>> am Sternpunkt-CT. Sinnvoll bei geerdetem Sternpunkt.
    Werte sind Sekundärwerte (1A/5A-CT); Primär = x kCT_E.
    """
    geerdet = (p["stp_OS"] not in K.STERNPUNKT_NICHT_GEERDET
               or p["stp_US"] not in K.STERNPUNKT_NICHT_GEERDET)
    return {
        "anwendbar": geerdet and g["kCT_E"] > 0,
        "IE_sek":   K.I_E_def,
        "IE_prim":  round(K.I_E_def * g["kCT_E"], 4),
        "t_IE":     K.t_I_E_def,
        "IEHH_sek": K.I_E_HH_def,
        "IEHH_prim":round(K.I_E_HH_def * g["kCT_E"], 4),
        "t_IEHH":   K.t_I_E_HH_def,
    }


# ── 4.10  U0-Erdschlusserfassung (isoliert/kompensiert) ──────────────────────

def schutz_U0(p: dict) -> dict:
    """
    U0-basierte Erdschlusserfassung. Aktiv bei isoliertem/kompensiertem Netz.
    Hinweis: nicht im 7UT613 enthalten -> separates 7SJ66/zentrale Erfassung.
    """
    isol_komp = (p["stp_OS"] in K.STERNPUNKT_NICHT_GEERDET
                 or p["stp_US"] in K.STERNPUNKT_NICHT_GEERDET)
    kompensiert = ("Kompensiert (Petersen)" in (p["stp_OS"], p["stp_US"]))
    U_LE = p["UN_US_kV"] * 1000 / SQRT3  # Sternspannung US in V

    return {
        "aktiv": isol_komp,
        "kompensiert": kompensiert,
        "U0_Meld_pu":   K.U0_Meldung_pu,
        "U0_Meld_V":    round(K.U0_Meldung_pu * U_LE, 1),
        "t_Meld":       K.t_U0_Meldung,
        "U0_Absch_pu":  K.U0_Abschalt_pu,
        "U0_Absch_V":   round(K.U0_Abschalt_pu * U_LE, 1),
        "t_Absch":      K.t_U0_Abschalt,
        "cos_phi_pct":  K.cos_phi_pct,
        "t_cos_phi":    K.t_cos_phi,
    }


# ── 4.11  Thermischer Ueberlastschutz 49 ─────────────────────────────────────

def schutz_49(g: dict, p: dict) -> dict:
    """Thermisches Abbild. tau in MINUTEN (häufige Fehlerquelle!)."""
    k    = p.get("k_Faktor", K.k_Faktor_def)
    tau  = p.get("tau_min",  K.tau_Trafo_def)
    thetaW = K.Theta_Warn_def
    I_W  = K.I_Warn_def
    return {
        "k_Faktor":      k,
        "tau_min":       tau,
        "tau_s":         round(tau * 60, 0),
        "Theta_Warn_pct":round(thetaW * 100, 0),
        "I_max_zul_sek": round(k * g["IN_OS_sek"], 4),
        "I_max_zul_prim":round(k * g["IN_OS_prim"], 4),
        "I_Warn_faktor": I_W,
        "I_Warn_sek":    round(I_W * g["IN_OS_sek"], 4),
        "I_Warn_prim":   round(I_W * g["IN_OS_prim"], 4),
        "k_status":      status_bereich(k, K.k_Faktor_min, K.k_Faktor_max),
    }


# ── 4.12  Schieflastschutz 46 (optional) ─────────────────────────────────────

def schutz_46(g: dict, p: dict) -> dict:
    """Gegensystem-/Schieflastschutz I2."""
    I2 = p.get("I2_zul", K.I2_zul_def)
    return {
        "I2_zul_faktor": I2,
        "I2_zul_sek":    round(I2 * g["IN_OS_sek"], 4),
        "I2_zul_prim":   round(I2 * g["IN_OS_prim"], 4),
        "t_Warn_I2":     K.t_Warn_I2_def,
    }


# ── 4.x  Uebererregungsschutz U/f (ANSI 24) ──────────────────────────────────

def schutz_24(p: dict) -> dict:
    """
    Uebererregungsschutz U/f (ANSI 24). Bezugsgroesse ist das Verhaeltnis U/f
    relativ zum Nennwert (U/f = 1,0), daher dimensionslos und ohne zusaetzliche
    Eingaben berechenbar. Voraussetzung im Geraet: Spannungseingang vorhanden
    (7UT613/633), Projektierung Adr.143 = vorhanden (7UT613 Hdb. 2.11).
    """
    return {
        "Uf_Warn":   p.get("Uf_Warn", K.Uf_Warn_def),
        "t_Uf_Warn": K.t_Uf_Warn_def,
        "Uf_Aus":    p.get("Uf_Aus", K.Uf_Aus_def),
        "t_Uf_Aus":  K.t_Uf_Aus_def,
    }


# ── 4.14  Bemessungs-Engineering (Stufenwahl + Empfindlichkeit) ──────────────

def bemessung_engineering(g: dict, p: dict, umz: dict) -> dict:
    """
    Verifiziert die UMZ-Stufenwahl gegen max. Last, Inrush und min. Fehlerstrom.
    KEIN Ersatz für eine vollständige Kurzschlussberechnung.
    Bezugsseite OS (Speiseseite). Werte primaer.
    """
    k_S_I   = p.get("k_S_I",   K.k_S_I)
    k_S_IGG = p.get("k_S_IGG", K.k_S_IGG)
    gamma   = p.get("gamma",   K.gamma_Ikmin)
    inrush  = p.get("Inrush_Faktor", K.Inrush_Faktor)

    INOS_pr   = g["IN_OS_prim"]
    nT        = g["nT"]
    Ik_max_OS = p["Ik_max_OS_kA"] * 1000  # A
    Ik_max_US = p["Ik_max_US_kA"] * 1000  # A
    Ik_min_in = p.get("Ik_min_OS_kA", 0.0) * 1000  # A prim. OS (DIN EN 60909-0)

    I_max_Last = INOS_pr * 1.2                 # Default 1,2 * IN (A prim. OS)
    if Ik_min_in > 0:
        I_k_min        = Ik_min_in
        I_k_min_quelle = "Eingabe Ik,min OS (DIN EN 60909-0)"
    elif Ik_max_OS > 0:
        I_k_min        = Ik_max_OS * 0.3       # Näherung min. Fehlerstrom (A prim. OS)
        I_k_min_quelle = "Näherung 0,3·Ik,max OS (Ik,min nicht eingegeben)"
    else:
        I_k_min        = 0.0
        I_k_min_quelle = "fehlt"

    # I> Empfehlung (A prim.) = k_S_I * I_max_Last
    I_emp     = k_S_I * I_max_Last
    I_gewaehlt = umz["f_I"] * INOS_pr          # gewählter I> OS primaer
    I_status  = "OK" if I_gewaehlt >= I_emp * 0.999 else "Prüfen!"
    f_I_emp   = round(k_S_I * 1.2, 2)           # empfohlener Faktor I> (x IN_OS)

    # I>> Empfehlung (A prim.) = max(k_S_IGG * Ik_max_US ref. OS ; Inrush * IN)
    I_Ik   = (k_S_IGG * Ik_max_US / nT) if nT else 0.0
    I_Inr  = inrush * INOS_pr
    IHH_emp = max(I_Ik, I_Inr)
    massgebend = "Ik_max US (ref. OS)" if I_Ik >= I_Inr else "Inrush (Einschaltstoß)"
    IHH_gewaehlt = umz["f_IHH_OS"] * INOS_pr
    IHH_status   = "OK" if IHH_gewaehlt >= IHH_emp * 0.999 else "Prüfen!"
    f_IHH_emp = round(IHH_emp / INOS_pr, 2) if INOS_pr else 0.0  # empf. Faktor I>> OS

    # Empfindlichkeit: I_k_min / I> >= gamma
    empfind = I_k_min / I_gewaehlt if I_gewaehlt else 0.0
    empfind_status = "OK" if empfind >= gamma else "Prüfen!"

    # Konkrete Korrektur-Anweisungen
    korr_I   = (f"Regler 'I> Phase' auf >= {f_I_emp:g} x IN stellen "
                f"(aktuell {umz['f_I']:g})." if I_status != "OK" else "")
    korr_IHH = (f"Regler 'I>> Phase OS' auf >= {f_IHH_emp:g} x IN stellen "
                f"(aktuell {umz['f_IHH_OS']:g}). Maßgebend: {massgebend}."
                if IHH_status != "OK" else "")
    korr_emp = ("Empfindlichkeit zu gering: I> senken oder Empfindlichkeitsfaktor gamma "
                f"reduzieren, bis I_k_min/I> >= {gamma:g}." if empfind_status != "OK" else "")

    return {
        "I_max_Last_prim": round(I_max_Last, 2),
        "I_k_min_prim":    round(I_k_min, 2),
        "I_k_min_quelle":  I_k_min_quelle,
        "I_emp_prim":      round(I_emp, 2),
        "I_gewaehlt_prim": round(I_gewaehlt, 2),
        "I_status":        I_status,
        "f_I_emp":         f_I_emp,
        "korr_I":          korr_I,
        "IHH_emp_prim":    round(IHH_emp, 2),
        "IHH_Ik_prim":     round(I_Ik, 2),
        "IHH_Inr_prim":    round(I_Inr, 2),
        "massgebend":      massgebend,
        "IHH_gewaehlt_prim": round(IHH_gewaehlt, 2),
        "IHH_status":      IHH_status,
        "f_IHH_emp":       f_IHH_emp,
        "korr_IHH":        korr_IHH,
        "empfind":         round(empfind, 3),
        "gamma":           gamma,
        "empfind_status":  empfind_status,
        "korr_emp":        korr_emp,
    }


# ── 4.13  Plausibilitätsprüfung (Ampel) ────────────────────────────────────

def plausibilitaet(g: dict, p: dict, b49: dict, beng: dict, umz: dict) -> list:
    """
    Liste von Pruefungen mit konkreter Korrektur-Anweisung.
    Felder: pruefung, bezug, ergebnis, status, hinweis, korrektur.
    'korrektur' ist nur bei status != OK gefüllt und nennt den konkreten Regler/Wert.
    """
    checks = []

    def add(name, bezug, ergebnis, status, hinweis, korrektur=""):
        checks.append({"pruefung": name, "bezug": bezug, "ergebnis": ergebnis,
                       "status": status, "hinweis": hinweis,
                       "korrektur": korrektur if status != "OK" else ""})

    # Eingaben vorhanden
    add("Sn (Nennleistung) vorhanden", "Sn > 0",
        f"{p['Sn_MVA']} MVA" if p["Sn_MVA"] > 0 else "fehlt",
        "OK" if p["Sn_MVA"] > 0 else "Fehlt",
        "Pflichteingabe für alle Strom-/Anpassungsberechnungen.",
        "Feld 'Sn — Bemessungsleistung' ausfüllen (> 0 MVA).")

    add("Spannungen OS+US vorhanden", "UN_OS, UN_US > 0",
        "vorhanden" if (p["UN_OS_kV"] > 0 and p["UN_US_kV"] > 0) else "fehlt",
        "OK" if (p["UN_OS_kV"] > 0 and p["UN_US_kV"] > 0) else "Fehlt",
        "Beide Bemessungsspannungen für IN-Berechnung erforderlich.",
        "Felder 'UN OS' und 'UN US' ausfüllen (> 0 kV).")

    ct_ok = all(p[k] > 0 for k in ("CT_OS_Prim", "CT_OS_Sek", "CT_US_Prim", "CT_US_Sek"))
    add("Stromwandler OS+US vollständig", "CT prim/sek OS+US > 0",
        "vollst." if ct_ok else "fehlt", "OK" if ct_ok else "Fehlt",
        "Ohne Wandlerdaten keine Sekundär-Sollwerte.",
        "Alle vier Felder 'CT OS/US prim. + sek.' ausfüllen.")

    # 87T wirtschaftlich
    if p["Sn_MVA"] == 0:
        add("87T wirtschaftlich sinnvoll", f"Sn >= {K.Sn_min_87T} MVA", "fehlt", "Fehlt",
            "FNN-Leitfaden: unter 5 MVA oft nur Buchholz + UMZ.",
            "Sn eingeben.")
    else:
        ok = p["Sn_MVA"] >= K.Sn_min_87T
        add("87T wirtschaftlich sinnvoll", f"Sn >= {K.Sn_min_87T} MVA",
            "ja" if ok else "grenzwertig", "OK" if ok else "Hinweis",
            "FNN-Leitfaden: unter 5 MVA wirtschaftlich oft nur Buchholz + UMZ.",
            f"Sn = {p['Sn_MVA']} MVA < {K.Sn_min_87T} MVA: pruefen, ob 87T wirklich nötig "
            "ist, oder ob Buchholz + UMZ als Hauptschutz genügen.")

    # STW-Anpassung OS/US in [0,5 ... 2,0]
    for seite, ian, ctp, cts in (("OS", g["I_an_OS"], p["CT_OS_Prim"], p["CT_OS_Sek"]),
                                  ("US", g["I_an_US"], p["CT_US_Prim"], p["CT_US_Sek"])):
        st = status_bereich(ian, K.Anpass_min, K.Anpass_max) if ian else "Fehlt"
        if ian and ian > K.Anpass_max:
            korr = (f"Anpassfaktor {ian:.2f} > {K.Anpass_max}: CT {seite} prim. "
                    f"verkleinern (näher an IN {seite}) oder kleineren Wandler wählen.")
        elif ian and ian < K.Anpass_min:
            korr = (f"Anpassfaktor {ian:.2f} < {K.Anpass_min}: CT {seite} prim. "
                    f"vergrößern.")
        else:
            korr = f"CT {seite} pruefen."
        add(f"STW-Anpassung {seite} in [{K.Anpass_min} ... {K.Anpass_max}]",
            "I_an = CT_Sek / IN_sek", f"{ian:.3f}" if ian else "-", st,
            "7UT613 Hdb. 2.2.7: Anpassfaktor 0,5-2,0 (Meldung 5620).", korr)

    # Stufensteller
    stp = p["Stufensteller_pm"]
    add("Stufensteller mit Steigung 1 = 0,25 verträglich", f"<= {K.Stufensteller_max} %",
        f"{stp} %", "OK" if stp <= K.Stufensteller_max else "Hinweis",
        "Bei > 30 % Steigung 1 auf 0,30 anheben (7UT613 Hdb. 2.2.7).",
        f"Stufensteller {stp} % > {K.Stufensteller_max} %: Regler 'Steigung 1' auf 0,30 "
        "und ggf. 'I-DIFF>' auf 0,25-0,30 anheben.")

    # uk plausibel
    uk = p["uk_pct"]
    uk_st = status_bereich(uk, K.uk_min, K.uk_max) if uk else "Fehlt"
    add("uk im plausiblen Bereich [4 % ... 20 %]", "uk_Trafo", f"{uk} %", uk_st,
        "Verteilungstrafos typ. 4-12 %, Netzkuppler bis 20 %.",
        f"uk = {uk} % außerhalb [4 ... 20 %]: Wert vom Typenschild pruefen.")

    # 87N sinnvoll
    geerdet = (p["stp_OS"] not in K.STERNPUNKT_NICHT_GEERDET
               or p["stp_US"] not in K.STERNPUNKT_NICHT_GEERDET)
    ie_ct = p.get("IE_Wandler", True) and p.get("CT_E_Prim", 0) > 0
    ok87n = geerdet and ie_ct
    add("87N (EDS) sinnvoll - geerdeter Stp. + IE-Wandler", "Sternpunkt + IE-CT",
        "ja" if ok87n else "nein", "OK" if ok87n else "Hinweis",
        "7UT613 Hdb. 2.3.3: 87N benötigt Sternpunkt-Wandler bei geerdetem Stp.",
        ("Netz isoliert/kompensiert: 87N bewusst aus, Erdschluss über U0-Verfahren."
         if not geerdet else
         "Geerdet, aber kein IE-CT: Haken 'Sternpunkt-Wandler (IE-CT)' setzen und "
         "CT Erder prim. eingeben, sonst 87N nicht möglich."))

    # k-Faktor 49
    k = b49["k_Faktor"]
    k_st = status_bereich(k, K.k_Faktor_min, K.k_Faktor_max)
    add("k-Faktor (49) im Bereich [1,0 ... 1,5]", "k_Faktor", f"{k:.2f}", k_st,
        "Bei Trafos ohne Herstellerangabe typ. 1,10 (7UT613 Hdb. 2.9).",
        f"k-Faktor {k:.2f} außerhalb [1,0 ... 1,5]: Regler '49 k-Faktor' auf ~1,10 stellen.")

    # I> Stufenwahl (aus 4.14)
    add("I> liegt oberhalb der Maximallast", "I> gewählt >= Empfehlung",
        f"{beng['I_gewaehlt_prim']:.0f} / {beng['I_emp_prim']:.0f} A", beng["I_status"],
        "Anregung durch Überlast muss ausgeschlossen sein (7UT613 Hdb. 2.4).",
        beng["korr_I"])

    # I>> Stufenwahl OS (aus 4.14)
    add("I>> OS deckt Durchgangsfehler + Inrush", "I>> OS gewählt >= Empfehlung",
        f"{beng['IHH_gewaehlt_prim']:.0f} / {beng['IHH_emp_prim']:.0f} A",
        beng["IHH_status"],
        f"Maßgebend: {beng['massgebend']}. 7UT613 Hdb. 2.4.",
        beng["korr_IHH"])

    # Empfindlichkeit
    add("Empfindlichkeit I_k_min / I> >= gamma", f"gamma = {beng['gamma']}",
        f"{beng['empfind']:.2f}", beng["empfind_status"],
        "I_k_min am Schutzgebiet-Ende muss I> sicher anregen.",
        beng["korr_emp"])

    # Erdschlusserfassung passt (immer OK, nur informativ)
    isol = (p["stp_OS"] in K.STERNPUNKT_NICHT_GEERDET
            or p["stp_US"] in K.STERNPUNKT_NICHT_GEERDET)
    erg = "U0-Verfahren aktiv" if isol else "50N/51N anwendbar"
    add("Erdschlusserfassung passt zur Sternpunktbehandlung", "Stp_OS / Stp_US",
        erg, "OK", "Isoliert/kompensiert -> U0; sonst 50N/51N. FNN-Leitfaden Kap. 4.4.")

    return checks


# ── 4.15  Reserveschutz-Zuordnung / DIGSI-Adressen ───────────────────────────

def reserveschutz(g: dict, umz: dict, b49: dict) -> list:
    """Zuordnungstabelle Reserveschutz (UAMZ-PH / -3I0 / -ERD / Überlast)."""
    return [
        {"funktion": "UAMZ-PH 1 (Adr.420)", "ziel": "Seite 1 (OS)",
         "I_sek": f"{umz['OS']['I_sek']:.4f}", "t": f"{umz['t_I']:.2f}",
         "IHH_sek": f"{umz['OS']['IHH_sek']:.4f}", "tHH": f"{umz['t_IHH']:.2f}",
         "adresse": "Stufen 2011/2014; T 2013/2016"},
        {"funktion": "UAMZ-PH 1 (Adr.420)", "ziel": "Seite 2 (US)",
         "I_sek": f"{umz['US']['I_sek']:.4f}", "t": f"{umz['t_I']:.2f}",
         "IHH_sek": f"{umz['US']['IHH_sek']:.4f}", "tHH": f"{umz['t_IHH']:.2f}",
         "adresse": "Stufen 2011/2014; T 2013/2016"},
        {"funktion": "UAMZ-3I0 1 (Adr.422)", "ziel": "Seite 1 (OS)",
         "I_sek": f"{K.f_I_3I0_def * g['IN_OS_sek']:.4f}", "t": f"{K.t_I_3I0_def:.2f}",
         "IHH_sek": f"{K.f_I_3I0_HH_def * g['IN_OS_sek']:.4f}", "tHH": f"{K.t_I_3I0_HH_def:.2f}",
         "adresse": "Stufen 2211/2214; T 2213/2216"},
        {"funktion": "Überlast 49 (Adr.442)", "ziel": "Seite 1 (OS)",
         "I_sek": f"{b49['k_Faktor'] * g['IN_OS_sek']:.4f}", "t": f"{b49['tau_min']:.0f} min",
         "IHH_sek": "-", "tHH": "-",
         "adresse": "k 4202; tau 4203 (t> = MINUTEN!); Theta 4204; I-Warn 4205"},
    ]


# ── 4.16  Geräte-Empfehlung Erdschlusserfassung ─────────────────────────────

def geraeteempfehlung_erdschluss(p: dict) -> dict:
    stp = (p["stp_OS"], p["stp_US"])
    if "Isoliert" in stp:
        geraet = ("7SJ66 mit Erdschlusspaket (wattmetrisch / sin-phi) "
                  "oder zentrale Erdschlusserfassung")
        grund  = ("Isolierter Sternpunkt -> kapazitiver Erdschlussstrom zu klein "
                  "für 50N/51N. U0/wattmetrisch erforderlich.")
    elif "Kompensiert (Petersen)" in stp:
        geraet = "7SJ66 mit cos-phi-Erfassung + Pulsortung"
        grund  = ("Erdschlussstrom durch Petersenspule kompensiert -> "
                  "nur Reststrom-Auswertung (cos-phi/wattmetrisch) sinnvoll.")
    else:
        geraet = "50N/51N im 7UT613 ausreichend (Sternpunkt-CT erforderlich)"
        grund  = "Sternpunkt geerdet -> ausreichend Strom für klassisches 50N/51N."
    return {"geraet": geraet, "grund": grund}


# ── Master-Funktion ───────────────────────────────────────────────────────────

def berechne_alle(p: dict) -> dict:
    """
    Erwartete Pflichtfelder in p:
      Sn_MVA, UN_OS_kV, UN_US_kV, uk_pct, Vektorgruppe, Stufensteller_pm,
      CT_OS_Prim, CT_OS_Sek, CT_US_Prim, CT_US_Sek, CT_E_Prim, CT_E_Sek,
      IE_Wandler, stp_OS, stp_US, Ik_max_OS_kA, Ik_max_US_kA
    Optional: Override-Faktoren (siehe einzelne Funktionen).
    """
    g    = grundgroessen(p)
    e87T = schutz_87T(g, p)
    e87N = schutz_87N(g, p)
    umz  = schutz_5051_phase(g, p)
    erde = schutz_5051_erde(g, p)
    u0   = schutz_U0(p)
    b49  = schutz_49(g, p)
    b46  = schutz_46(g, p)
    b24  = schutz_24(p)
    beng = bemessung_engineering(g, p, umz)
    plaus = plausibilitaet(g, p, b49, beng, umz)
    rsv  = reserveschutz(g, umz, b49)
    erdg = geraeteempfehlung_erdschluss(p)

    return {
        "grund": g,
        "87T": e87T,
        "87N": e87N,
        "5051": umz,
        "50N51N": erde,
        "U0": u0,
        "49": b49,
        "46": b46,
        "24": b24,
        "bemessung": beng,
        "plausibilitaet": plaus,
        "reserveschutz": rsv,
        "erdschluss_geraet": erdg,
    }
