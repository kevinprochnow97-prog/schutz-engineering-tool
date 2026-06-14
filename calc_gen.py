"""
calc_gen.py — Berechnungslogik Generatorschutz
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reine Python-Funktionen (kein Streamlit) -> isoliert testbar.
Methodik nach SIPROTEC 7UM62 (Multifunktionaler Maschinenschutz),
Differential-Querverweis 7UT613. Ausgabe IEC-normiert (A, s, %, Grad).

Schutzfunktionen:
  87G  Staenderdifferentialschutz            (Adr. 20xx)
  50/51 UMZ I> mit Unterspannungshaltung      (Adr. 12xx)
  50   UMZ I>> Hochstromstufe                 (Adr. 13xx)
  51V  AMZ spannungsabhaengig                 (Adr. 14xx)
  49   Thermischer Ueberlastschutz (tau in s!) (Adr. 16xx)
  46   Schieflastschutz                        (Adr. 17xx)
  40   Untererregungsschutz (Admittanz)        (Adr. 30xx)
  32   Rueckleistungsschutz                    (Adr. 31xx)
  24   Uebererregungsschutz U/f                (Adr. 43xx)
  27/59 Unter-/Ueberspannungsschutz           (Adr. 40xx/41xx)
  81   Frequenzschutz                          (Adr. 42xx)
  59N  Staendererdschlussschutz 90 % (U0)      (Adr. 50xx)
  64R  Laeufererdschlussschutz (R, fn)         (Adr. 60xx)
"""

import math
import konstanten_gen as K
from calc_trafo import status_empfehlung, status_bereich  # gemeinsame Ampel-Helfer

SQRT3 = math.sqrt(3)


# ── Berechnete Grundgroessen ─────────────────────────────────────────────────

def grundgroessen(p: dict) -> dict:
    """
    Maschinen-Nennstrom, Wandlerverhaeltnisse, Bezugsgroessen.
    Erwartet: Sn_MVA, UN_kV, CT_K_Prim, CT_K_Sek, CT_S_Prim, CT_S_Sek,
              VT_Prim_kV, VT_Sek_V
    """
    Sn, UN = p["Sn_MVA"], p["UN_kV"]

    IN_prim = (Sn * 1e6) / (SQRT3 * UN * 1e3) if UN > 0 else 0.0

    kCT_K = p["CT_K_Prim"] / p["CT_K_Sek"] if p.get("CT_K_Sek") else 0.0  # Klemmenseite
    kCT_S = p["CT_S_Prim"] / p["CT_S_Sek"] if p.get("CT_S_Sek") else 0.0  # Sternpunktseite
    nVT   = (p["VT_Prim_kV"] * 1e3) / p["VT_Sek_V"] if p.get("VT_Sek_V") else 0.0

    IN_K_sek = IN_prim / kCT_K if kCT_K else 0.0
    IN_S_sek = IN_prim / kCT_S if kCT_S else 0.0
    IN_Obj_sek = IN_K_sek if IN_K_sek else IN_S_sek   # Bezug 87G = Klemmenseite

    # STW-Anpassung I_an = CT_Sek / IN_sek  (Soll 0,5 ... 2,0)
    I_an_K = p["CT_K_Sek"] / IN_K_sek if IN_K_sek else 0.0
    I_an_S = p["CT_S_Sek"] / IN_S_sek if IN_S_sek else 0.0

    # Sekundaere Nennscheinleistung SNsek = sqrt(3) * UN_sek * IN_sek  (fuer 32)
    UN_sek = p.get("VT_Sek_V", 0.0)
    SN_sek = SQRT3 * UN_sek * IN_K_sek if (UN_sek and IN_K_sek) else 0.0

    return {
        "IN_prim":    round(IN_prim, 4),
        "kCT_K":      round(kCT_K, 4),
        "kCT_S":      round(kCT_S, 4),
        "nVT":        round(nVT, 4),
        "IN_K_sek":   round(IN_K_sek, 4),
        "IN_S_sek":   round(IN_S_sek, 4),
        "IN_Obj_sek": round(IN_Obj_sek, 4),
        "I_an_K":     round(I_an_K, 4),
        "I_an_S":     round(I_an_S, 4),
        "UN_sek":     round(UN_sek, 4),
        "SN_sek":     round(SN_sek, 4),
    }


# ── 87G Staenderdifferentialschutz ───────────────────────────────────────────

def schutz_87G(g: dict, p: dict) -> dict:
    """
    87G nach 7UM62-Methodik. Bezug = IN_Obj (Klemmenseite). I-DIFF>> aus x'd.
    """
    INO = g["IN_Obj_sek"]
    INp = g["IN_prim"]
    xds = p.get("xd_strich", 0.20)

    I_DIFF    = p.get("I_DIFF",    K.I_DIFF_def)
    I_DIFF_HH = p.get("I_DIFF_HH", K.I_DIFF_HH_def)
    Steig1    = p.get("Steigung_1", K.Steigung_1_def)
    Steig2    = p.get("Steigung_2", K.Steigung_2_def)
    Fp2       = p.get("Fusspunkt_2", K.Fusspunkt_2_def)
    Harm2     = p.get("Harm_2", K.Harm_2_def)

    # Dynamische Empfehlungen
    emp_IDIFF   = 0.20
    emp_IDIFFHH = round(min(7.0, max(3.0, (1.0 / xds))), 1) if xds > 0 else None
    emp_Steig1  = 0.25
    emp_Steig2  = 0.50
    emp_Fp2     = 2.50

    def row(name, fak, einheit, emp, adr, sek=True, prim=True, einst=True):
        return {
            "name": name, "faktor": fak, "einheit": einheit,
            "wert_sek": round(fak * INO, 4) if sek else None,
            "wert_prim": round(fak * INp, 4) if prim else None,
            "empfehlung": emp,
            "status": status_empfehlung(fak, emp) if emp is not None else "—",
            "adresse": adr,
            "einstellbar": einst,
        }

    rows = [
        # Einstellbare Hauptparameter (entsprechen den Reglern im Tab)
        row("I-DIFF>  (Ansprechwert)",   I_DIFF,    "I/InO", emp_IDIFF,   "Adr.2021"),
        row("I-DIFF>> (Schnellausl.)",   I_DIFF_HH, "I/InO", emp_IDIFFHH, "Adr.2031"),
        {"name": "Steigung 1", "faktor": Steig1, "einheit": "-", "wert_sek": None,
         "wert_prim": None, "empfehlung": emp_Steig1, "status": status_empfehlung(Steig1, emp_Steig1),
         "adresse": "Adr.2041A", "einstellbar": True},
        {"name": "Steigung 2", "faktor": Steig2, "einheit": "-", "wert_sek": None,
         "wert_prim": None, "empfehlung": emp_Steig2, "status": status_empfehlung(Steig2, emp_Steig2),
         "adresse": "Adr.2043A", "einstellbar": True},
        row("Fusspunkt 2", Fp2, "I/InO", emp_Fp2, "Adr.2044A", sek=True, prim=False),
        {"name": "2. Harmonische (Inrush)", "faktor": round(Harm2 * 100, 1), "einheit": "%",
         "wert_sek": None, "wert_prim": None, "empfehlung": 15.0,
         "status": status_empfehlung(round(Harm2 * 100, 1), 15.0), "adresse": "Adr.2071", "einstellbar": True},
        # Feste Voreinstellungen / abgeleitete Parameter (im Tab nicht als Regler)
        {"name": "Anlauf-Stabilisierung", "faktor": K.Anlauf_Stab_def, "einheit": "I/InO",
         "wert_sek": round(K.Anlauf_Stab_def * INO, 4), "wert_prim": None,
         "empfehlung": None, "status": "—", "adresse": "Adr.2051A", "einstellbar": False},
        {"name": "EXF-Stab. (ext. Fehler)", "faktor": K.EXF_Stab_def, "einheit": "I/InO",
         "wert_sek": round(K.EXF_Stab_def * INO, 4), "wert_prim": None,
         "empfehlung": None, "status": "—", "adresse": "Adr.2061A", "einstellbar": False},
        {"name": "T I-DIFF>",  "faktor": K.T_I_DIFF_def,    "einheit": "s", "wert_sek": None,
         "wert_prim": None, "empfehlung": None, "status": "—", "adresse": "Adr.2026A", "einstellbar": False},
        {"name": "T I-DIFF>>", "faktor": K.T_I_DIFF_HH_def, "einheit": "s", "wert_sek": None,
         "wert_prim": None, "empfehlung": None, "status": "—", "adresse": "Adr.2036A", "einstellbar": False},
    ]
    return {
        "INO_Bezug_A": round(INO, 4),
        "I_DIFF_Anspr_sek_A":  round(I_DIFF * INO, 4),
        "I_DIFF_Anspr_prim_A": round(I_DIFF * INp, 4),
        "I_DIFF_HH_sek_A":     round(I_DIFF_HH * INO, 4),
        "emp_IDIFFHH":         emp_IDIFFHH,
        "rows": rows,
    }


# ── 50/51 UMZ I> (mit Unterspannungshaltung) + 50 I>> ───────────────────────

def schutz_5051(g: dict, p: dict) -> dict:
    f_I    = p.get("f_I_Ph",    K.f_I_Ph_def)
    t_I    = p.get("t_I_Ph",    K.t_I_Ph_def)
    U_Halt = p.get("U_Haltung", K.U_Haltung_def)
    f_IHH  = p.get("f_I_Ph_HH", K.f_I_Ph_HH_def)
    t_IHH  = p.get("t_I_Ph_HH", K.t_I_Ph_HH_def)
    INk, INp = g["IN_K_sek"], g["IN_prim"]
    return {
        "f_I": f_I, "t_I": t_I, "U_Haltung": U_Halt,
        "f_IHH": f_IHH, "t_IHH": t_IHH,
        "I_sek":   round(f_I   * INk, 4),
        "I_prim":  round(f_I   * INp, 4),
        "IHH_sek": round(f_IHH * INk, 4),
        "IHH_prim":round(f_IHH * INp, 4),
    }


# ── 51V AMZ spannungsabhaengig ───────────────────────────────────────────────

def schutz_51V(g: dict, p: dict) -> dict:
    f_Ip = p.get("f_Ip", K.f_Ip_def)
    T_Ip = p.get("T_Ip", K.T_Ip_def)
    U_St = p.get("U_AMZ", K.U_AMZ_def)
    INk, INp = g["IN_K_sek"], g["IN_prim"]
    UN_sek = g["UN_sek"]
    return {
        "f_Ip": f_Ip, "T_Ip": T_Ip, "U_AMZ": U_St,
        "Ip_sek":  round(f_Ip * INk, 4),
        "Ip_prim": round(f_Ip * INp, 4),
        "U_AMZ_pct": round(100 * U_St / UN_sek, 1) if UN_sek else 0.0,
        "kennlinie": K.Kennlinie_AMZ_def,
    }


# ── 49 Thermischer Ueberlastschutz (tau in SEKUNDEN!) ───────────────────────

def schutz_49(g: dict, p: dict) -> dict:
    k     = p.get("k_Faktor", K.k_Faktor_def)
    tau_s = p.get("tau_s",    K.tau_Gen_def)
    thetaW = p.get("Theta_Warn", K.Theta_Warn_def)
    I_W   = p.get("I_Warn", K.I_Warn_def)
    INk, INp = g["IN_K_sek"], g["IN_prim"]
    return {
        "k_Faktor":      k,
        "tau_s":         tau_s,
        "tau_min":       round(tau_s / 60.0, 1),
        "Theta_Warn_pct":round(thetaW * 100, 0),
        "I_max_zul_sek": round(k * INk, 4),
        "I_max_zul_prim":round(k * INp, 4),
        "I_Warn_faktor": I_W,
        "I_Warn_sek":    round(I_W * INk, 4),
        "k_status":      status_bereich(k, K.k_Faktor_min, K.k_Faktor_max),
    }


# ── 46 Schieflastschutz ──────────────────────────────────────────────────────

def schutz_46(g: dict, p: dict) -> dict:
    I2   = p.get("I2_zul", K.I2_zul_def)
    I2HH = p.get("I2_HH",  K.I2_HH_def)
    Kfak = p.get("Faktor_K", K.Faktor_K_def)
    INk, INp = g["IN_K_sek"], g["IN_prim"]
    return {
        "I2_zul_faktor": I2,
        "I2_zul_sek":    round(I2 * INk, 4),
        "I2_zul_prim":   round(I2 * INp, 4),
        "I2_HH_faktor":  I2HH,
        "I2_HH_sek":     round(I2HH * INk, 4),
        "Faktor_K":      Kfak,
        "t_Warn":        K.t_Warn_I2_def,
        "t_I2_HH":       K.t_I2_HH_def,
        "t_Abkuehl":     K.t_Abkuehl_def,
    }


# ── 40 Untererregungsschutz (Admittanzkennlinien) ───────────────────────────

def schutz_40(g: dict, p: dict) -> dict:
    """
    1/xd KL.1 (sek.) = (1/xd_Masch) * (IN_Wdl_prim/IN_Masch) * (UN_Masch/UN_Wdl_prim) * 1,05
    KL.2 = 0,9 * KL.1 ; KL.3 = Vorgabe (zwischen xd und x'd, > 1).
    """
    xd      = p.get("xd", 2.0)
    INp     = g["IN_prim"]
    CT_prim = p.get("CT_K_Prim", INp)
    UN_M    = p.get("UN_kV", 0.0) * 1e3
    UN_Vt_p = p.get("VT_Prim_kV", 0.0) * 1e3

    if xd > 0 and INp > 0 and UN_M > 0 and UN_Vt_p > 0:
        xd_KL1 = (1.0 / xd) * (CT_prim / INp) * (UN_M / UN_Vt_p) * K.xd_Sicherheit
    elif xd > 0:
        xd_KL1 = (1.0 / xd) * K.xd_Sicherheit
    else:
        xd_KL1 = 0.0

    auto = p.get("auto_xd_KL1", True)
    KL1 = round(xd_KL1, 2) if auto else p.get("xd_KL1_man", round(xd_KL1, 2))
    KL2 = round(K.xd_KL2_Faktor * KL1, 2)
    KL3 = p.get("xd_KL3", K.xd_KL3_def)

    return {
        "xd": xd,
        "xd_KL1": KL1, "winkel_1": p.get("winkel_1", K.Winkel_1_def), "t_KL1": K.T_KL1_def,
        "xd_KL2": KL2, "winkel_2": K.Winkel_2_def, "t_KL2": K.T_KL2_def,
        "xd_KL3": KL3, "winkel_3": K.Winkel_3_def, "t_KL3": K.T_KL3_def,
        "t_kurz_Uerr": K.T_kurz_Uerr_def,
        "auto": auto,
    }


# ── 32 Rueckleistungsschutz ──────────────────────────────────────────────────

def schutz_32(g: dict, p: dict) -> dict:
    turbine = p.get("turbine", "Dampfturbine")
    emp = {"Dampfturbine": K.PRueck_Dampf,
           "Gasturbine":   K.PRueck_Gas,
           "Dieselantrieb":K.PRueck_Diesel}.get(turbine, K.PRueck_Dampf)
    P    = p.get("Prueck", emp)
    SNs  = g["SN_sek"]
    # P_sek in W = P% * SNsek
    P_W  = (P / 100.0) * SNs if SNs else 0.0
    t_m  = 0.5 if turbine == "Gasturbine" else K.t_m_SSchl_def
    return {
        "turbine":  turbine,
        "Prueck_pct": P,
        "emp_pct":  emp,
        "Prueck_W": round(P_W, 1),
        "SN_sek":   round(SNs, 1),
        "t_o_SSchl":K.t_o_SSchl_def,
        "t_m_SSchl":round(t_m, 2),
        "status":   status_empfehlung(P, emp),
    }


# ── 24 Uebererregungsschutz U/f ──────────────────────────────────────────────

def schutz_24(g: dict, p: dict) -> dict:
    return {
        "Uf_Warn":  p.get("Uf_Warn", K.Uf_Warn_def),
        "t_Uf_Warn":K.t_Uf_Warn_def,
        "Uf_Aus":   p.get("Uf_Aus", K.Uf_Aus_def),
        "t_Uf_Aus": K.t_Uf_Aus_def,
    }


# ── 27/59 Unter-/Ueberspannungsschutz ───────────────────────────────────────

def schutz_2759(g: dict, p: dict) -> dict:
    UN = g["UN_sek"] if g["UN_sek"] else 100.0
    Uk  = p.get("U_klein", K.U_klein_def)
    Ukk = p.get("U_kleinklein", K.U_kleinklein_def)
    Ug  = p.get("U_gross", K.U_gross_def)
    Ugg = p.get("U_grossgross", K.U_grossgross_def)
    pc = lambda v: round(100 * v / UN, 0)
    return {
        "U_klein": Uk, "U_klein_pct": pc(Uk), "t_U_klein": K.t_U_klein_def,
        "U_kleinklein": Ukk, "U_kleinklein_pct": pc(Ukk), "t_U_kleinklein": K.t_U_kleinklein_def,
        "U_gross": Ug, "U_gross_pct": pc(Ug), "t_U_gross": K.t_U_gross_def,
        "U_grossgross": Ugg, "U_grossgross_pct": pc(Ugg), "t_U_grossgross": K.t_U_grossgross_def,
        "UN_sek": UN,
    }


# ── 81 Frequenzschutz ────────────────────────────────────────────────────────

def schutz_81(g: dict, p: dict) -> dict:
    fN = p.get("fN", 50)
    if fN == 60:
        f1, f2, f3, f4 = K.f1_60, K.f2_60, K.f3_60, K.f4_60
        adr1, adr2, adr3, adr4 = "Adr.4203 / T 4204", "Adr.4206 / T 4207", \
                                   "Adr.4209 / T 4210", "Adr.4212 / T 4213"
    else:
        f1, f2, f3, f4 = K.f1_def, K.f2_def, K.f3_def, K.f4_def
        adr1, adr2, adr3, adr4 = "Adr.4202 / T 4204", "Adr.4205 / T 4207", \
                                   "Adr.4208 / T 4210", "Adr.4211 / T 4213"
    return {
        "fN": fN,
        "stufen": [
            {"name": "f1 (Netztrennung)",       "f": f1, "t": K.t_f1_def, "adr": adr1},
            {"name": "f2 (Stillsetzung)",       "f": f2, "t": K.t_f2_def, "adr": adr2},
            {"name": "f3 (Warnung Unterfreq.)", "f": f3, "t": K.t_f3_def, "adr": adr3},
            {"name": "f4 (Ueberfrequenz)",      "f": f4, "t": K.t_f4_def, "adr": adr4},
        ],
    }


# ── 59N Staendererdschlussschutz 90 % (U0) ──────────────────────────────────

def schutz_59N(g: dict, p: dict) -> dict:
    stp = p.get("stp_Gen", "Hochohmig (Erdungstrafo / Petersen)")
    # bei isoliertem Netz ohne Erdungstrafo: sin-phi-Schaltung ~90 Grad
    winkel = K.Winkel_SES_isol if stp == "Isoliert" else K.Winkel_SES_def
    U0 = p.get("U0", K.U0_def)
    schutzbereich = round(100 * (1 - U0 / K.U0_voll_V), 0) if K.U0_voll_V else 90.0
    return {
        "aktiv":    stp in K.STERNPUNKT_GEN_NICHT_NIEDEROHMIG or stp == "Niederohmig geerdet",
        "stp":      stp,
        "U0":       U0,
        "U0_pct":   round(100 * U0 / K.U0_voll_V, 0) if K.U0_voll_V else 0.0,
        "schutzbereich_pct": schutzbereich,
        "I3I0":     K.I3I0_def,
        "winkel":   winkel,
        "t_SES":    K.t_SES_def,
    }


# ── 64R Laeufererdschlussschutz (R, fn) ─────────────────────────────────────

def schutz_64R(g: dict, p: dict) -> dict:
    return {
        "RE_Warn":   p.get("RE_Warn", K.RE_Warn_def),
        "RE_Aus":    p.get("RE_Aus",  K.RE_Aus_def),
        "t_RE_Warn": K.t_RE_Warn_def,
        "t_RE_Aus":  K.t_RE_Aus_def,
    }


# ── Bemessungs-Engineering (Reserve-Ueberstrom) ─────────────────────────────

def bemessung_engineering(g: dict, p: dict, umz: dict) -> dict:
    """
    Verifiziert die Reserve-Ueberstromstufe gegen max. Last und min. Fehlerstrom.
    KEIN Ersatz fuer eine vollstaendige Kurzschlussberechnung nach DIN EN 60909-0;
    Ik_max und Ik_min werden als Eingabe erwartet (vgl. Arbeit Abschnitt 2.4).

    Zusaetzlich werden die maschineneigenen Fehlerstrombeitraege aus den Reaktanzen
    berechnet (Arbeit Abschnitt 6.2):
        I''k  = IN / x''d   (subtransient, groesster Anfangskurzschlussstrom)
        Ik,st = IN / xd     (stationaerer Endwert des abklingenden Stroms)
    """
    k_S_I  = p.get("k_S_I",  K.k_S_I)
    gamma  = p.get("gamma",  K.gamma_Ikmin)
    INp    = g["IN_prim"]
    Ik_max = p.get("Ik_max_kA", 0.0) * 1000.0
    Ik_min_in = p.get("Ik_min_kA", 0.0) * 1000.0

    # Maschineneigene Fehlerstrombeitraege aus den Reaktanzen (geben x''d/xd eine Funktion)
    xds = p.get("xd_subtrans", 0.0)   # x''d subtransient
    xd  = p.get("xd", 0.0)            # xd  synchron
    Ik_masch_sub  = (INp / xds) if xds > 0 else 0.0   # I''k = IN / x''d
    Ik_masch_stat = (INp / xd)  if xd  > 0 else 0.0   # Ik,stat = IN / xd

    # Minimaler Fehlerstrom: echte Eingabe bevorzugt, sonst konservative Naeherung
    if Ik_min_in > 0:
        I_k_min = Ik_min_in
        I_k_min_quelle = "Eingabe Ik,min (DIN EN 60909-0)"
    elif Ik_max > 0:
        I_k_min = Ik_max * 0.3
        I_k_min_quelle = "Näherung 0,3·Ik,max (Ik,min nicht eingegeben)"
    else:
        I_k_min = 0.0
        I_k_min_quelle = "fehlt"

    I_max_Last = INp * 1.0                      # Generator: Dauerlast ~ IN
    I_emp      = k_S_I * I_max_Last
    I_gewaehlt = umz["f_I"] * INp
    I_status   = "OK" if (I_emp and I_gewaehlt >= I_emp * 0.999) else ("Prüfen!" if I_emp else "Fehlt")
    f_I_emp    = round(k_S_I, 2)

    empfind = I_k_min / I_gewaehlt if I_gewaehlt else 0.0
    empfind_status = "OK" if (empfind and empfind >= gamma) else ("Prüfen!" if I_k_min else "Fehlt")

    # Hochstromstufe I>> muss unter dem maschineneigenen I''k liegen, sonst spricht sie
    # bei einem klemmennahen Fehler nicht an.
    I_HH_gewaehlt = umz["f_IHH"] * INp
    if Ik_masch_sub:
        hh_status = "OK" if I_HH_gewaehlt <= Ik_masch_sub * 1.001 else "Prüfen!"
    else:
        hh_status = "Fehlt"

    # 51V-Notwendigkeit: faellt der selbst gespeiste Strom unter I>, ist U<-Haltung/51V noetig
    v51_noetig = bool(Ik_masch_stat and I_gewaehlt and Ik_masch_stat < I_gewaehlt)

    korr_I = (f"Regler 'I> Phase' auf >= {f_I_emp:g} x IN stellen (aktuell {umz['f_I']:g})."
              if I_status == "Prüfen!" else "")
    korr_emp = ("Empfindlichkeit zu gering: I> senken oder gamma reduzieren, "
                f"bis Ik,min/I> >= {gamma:g}." if empfind_status == "Prüfen!" else "")
    korr_hh = (f"I>> ({I_HH_gewaehlt:.0f} A) liegt über dem maschineneigenen "
               f"I''k = IN/x''d ({Ik_masch_sub:.0f} A); bei klemmennahem Fehler spricht die "
               f"Hochstromstufe nicht an. I>>-Faktor senken oder x''d prüfen."
               if hh_status == "Prüfen!" else "")

    return {
        "I_max_Last_prim": round(I_max_Last, 2),
        "I_k_min_prim":    round(I_k_min, 2),
        "I_k_min_quelle":  I_k_min_quelle,
        "I_emp_prim":      round(I_emp, 2),
        "I_gewaehlt_prim": round(I_gewaehlt, 2),
        "I_status":        I_status,
        "f_I_emp":         f_I_emp,
        "korr_I":          korr_I,
        "empfind":         round(empfind, 3),
        "gamma":           gamma,
        "empfind_status":  empfind_status,
        "korr_emp":        korr_emp,
        # Maschineneigene Kurzschlussstroeme + abgeleitete Pruefungen
        "Ik_masch_sub_prim":  round(Ik_masch_sub, 1),
        "Ik_masch_stat_prim": round(Ik_masch_stat, 1),
        "I_HH_gewaehlt_prim": round(I_HH_gewaehlt, 1),
        "hh_status":          hh_status,
        "korr_hh":            korr_hh,
        "v51_noetig":         v51_noetig,
    }


# ── Plausibilitaetspruefung (Ampel) ─────────────────────────────────────────

def plausibilitaet(g: dict, p: dict, b49: dict, beng: dict, f40: dict, f59n: dict) -> list:
    checks = []

    def add(name, bezug, ergebnis, status, hinweis, korrektur=""):
        checks.append({"pruefung": name, "bezug": bezug, "ergebnis": ergebnis,
                       "status": status, "hinweis": hinweis,
                       "korrektur": korrektur if status != "OK" else ""})

    add("Sn (Nennleistung) vorhanden", "Sn > 0",
        f"{p['Sn_MVA']} MVA" if p["Sn_MVA"] > 0 else "fehlt",
        "OK" if p["Sn_MVA"] > 0 else "Fehlt",
        "Pflichteingabe fuer alle Strom-/Anpassungsberechnungen.",
        "Feld 'Sn' ausfuellen (> 0 MVA).")

    add("Nennspannung UN vorhanden", "UN > 0",
        f"{p['UN_kV']} kV" if p["UN_kV"] > 0 else "fehlt",
        "OK" if p["UN_kV"] > 0 else "Fehlt",
        "Bemessungsspannung fuer IN-Berechnung erforderlich.",
        "Feld 'UN' ausfuellen (> 0 kV).")

    ct_ok = all(p.get(k, 0) > 0 for k in ("CT_K_Prim", "CT_K_Sek", "CT_S_Prim", "CT_S_Sek"))
    add("Stromwandler Klemmen- + Sternpunktseite vollstaendig", "beide CT-Saetze > 0",
        "vollst." if ct_ok else "fehlt", "OK" if ct_ok else "Fehlt",
        "87G benoetigt CTs an beiden Enden der Staenderwicklung.",
        "Alle vier CT-Felder (Klemme/Sternpunkt, prim./sek.) ausfuellen.")

    vt_ok = p.get("VT_Prim_kV", 0) > 0 and p.get("VT_Sek_V", 0) > 0
    add("Spannungswandler vorhanden", "VT prim/sek > 0",
        "vorhanden" if vt_ok else "fehlt", "OK" if vt_ok else "Hinweis",
        "Voraussetzung fuer 32, 24, 27/59, 81, 40, 51V.",
        "VT prim. [kV] und VT sek. [V] eingeben, sonst sind die spannungs- "
        "und leistungsbasierten Funktionen nicht parametrierbar.")

    # STW-Anpassung Klemmen-/Sternpunktseite
    for seite, ian in (("Klemme", g["I_an_K"]), ("Sternpunkt", g["I_an_S"])):
        stt = status_bereich(ian, K.Anpass_min, K.Anpass_max) if ian else "Fehlt"
        if ian and ian > K.Anpass_max:
            korr = f"Anpassfaktor {ian:.2f} > {K.Anpass_max}: CT {seite} prim. verkleinern."
        elif ian and ian < K.Anpass_min:
            korr = f"Anpassfaktor {ian:.2f} < {K.Anpass_min}: CT {seite} prim. vergroessern."
        else:
            korr = f"CT {seite} pruefen."
        add(f"STW-Anpassung {seite} in [{K.Anpass_min} ... {K.Anpass_max}]",
            "I_an = CT_Sek / IN_sek", f"{ian:.3f}" if ian else "-", stt,
            "Anpassfaktor 0,5-2,0 fuer korrekte 87G-Stabilisierung.", korr)

    # x'd plausibel
    xds = p.get("xd_strich", 0.0)
    xds_st = status_bereich(xds, K.xd_strich_min, K.xd_strich_max) if xds else "Fehlt"
    add("x'd (transient) im plausiblen Bereich [0,10 ... 0,40]", "x'd_Masch",
        f"{xds:g} p.u." if xds else "-", xds_st,
        "x'd bestimmt die I-DIFF>>-Empfehlung (~1/x'd).",
        f"x'd = {xds:g} p.u. ausserhalb [0,10 ... 0,40]: Wert vom Maschinendatenblatt pruefen.")

    # xd plausibel (fuer 40)
    xd = p.get("xd", 0.0)
    xd_st = status_bereich(xd, K.xd_min, K.xd_max) if xd else "Fehlt"
    add("xd (synchron) im plausiblen Bereich [0,8 ... 3,5]", "xd_Masch",
        f"{xd:g} p.u." if xd else "-", xd_st,
        "xd bestimmt 1/xd KL.1 des Untererregungsschutzes (40).",
        f"xd = {xd:g} p.u. ausserhalb [0,8 ... 3,5]: Wert pruefen (synchrone Laengsreaktanz).")

    # k-Faktor 49
    k = b49["k_Faktor"]
    add("k-Faktor (49) im Bereich [1,0 ... 1,5]", "k_Faktor", f"{k:.2f}", b49["k_status"],
        "Ohne Herstellerangabe typ. 1,11 (7UM62 Hdb. 2.6).",
        f"k-Faktor {k:.2f} ausserhalb [1,0 ... 1,5]: Regler '49 k-Faktor' auf ~1,11 stellen.")

    # tau-Einheit Hinweis (immer, da haeufige Fehlerquelle)
    add("Zeitkonstante tau (49) in SEKUNDEN eingegeben", "Adr.1603 Einheit",
        f"{b49['tau_s']:.0f} s (= {b49['tau_min']:.1f} min)", "OK",
        "WICHTIG: 7UM62 erwartet tau in Sekunden (7UT613 dagegen Minuten!).")

    # I-Warn <= k*IN
    iw_ok = b49["I_Warn_sek"] <= b49["I_max_zul_sek"] * 1.001
    add("Stromwarnstufe I WARN <= k x IN_sek", "I WARN <= I_max_zul",
        f"{b49['I_Warn_sek']:.3f} / {b49['I_max_zul_sek']:.3f} A",
        "OK" if iw_ok else "Hinweis",
        "I WARN soll gleich oder unter dem dauernd zul. Strom liegen (7UM62 Hdb. 2.6).",
        "I-Warnstufe absenken (<= k x IN_sek).")

    # Reserve-Ueberstrom Stufenwahl
    add("I> liegt oberhalb der Maximallast", "I> gewaehlt >= Empfehlung",
        f"{beng['I_gewaehlt_prim']:.0f} / {beng['I_emp_prim']:.0f} A", beng["I_status"],
        "Anregung durch Betriebslast muss ausgeschlossen sein (7UM62 Hdb. 2.3).",
        beng["korr_I"])

    # Empfindlichkeit
    add("Empfindlichkeit Ik,min / I> >= gamma", f"gamma = {beng['gamma']}  (Ik,min: {beng['I_k_min_quelle']})",
        f"{beng['empfind']:.2f}" if beng['empfind'] else "-", beng["empfind_status"],
        "Min. Fehlerstrom am Schutzgebiet-Ende muss I> sicher anregen. "
        "Hinweis: 51V mit Unterspannungssteuerung verbessert die Empfindlichkeit "
        "bei abklingendem Generator-KS-Strom.",
        beng["korr_emp"])

    # Hochstromstufe I>> unter maschineneigenem I''k (= IN/x''d)
    add("Hochstromstufe I>> unter maschineneigenem I''k (=IN/x''d)",
        "I>> <= I''k",
        f"{beng['I_HH_gewaehlt_prim']:.0f} / {beng['Ik_masch_sub_prim']:.0f} A" if beng['Ik_masch_sub_prim'] else "-",
        beng["hh_status"],
        "I>> muss unter dem subtransienten Eigenstrom IN/x''d liegen, sonst spricht die "
        "Hochstromstufe bei klemmennahem Fehler nicht an (Arbeit Abschnitt 6.2/6.3).",
        beng["korr_hh"])

    # 51V-Notwendigkeit aus dem abklingenden Eigenstrom (Ik,stat = IN/xd)
    if beng["v51_noetig"]:
        v51_erg = (f"Ik,stat={beng['Ik_masch_stat_prim']:.0f} A < I>={beng['I_gewaehlt_prim']:.0f} A "
                   "-> U<-Haltung/51V aktiv")
        v51_hin = ("Der selbst gespeiste KS-Strom faellt stationaer (IN/xd) unter I>. Eine reine "
                   "Ueberstromstufe wuerde zurueckfallen; U<-Haltung (Adr.1205) und 51V (Adr.1401) "
                   "fangen dies ab und sind im Parametersatz aktiv (Arbeit Abschnitt 6.4).")
    else:
        v51_erg = (f"Ik,stat={beng['Ik_masch_stat_prim']:.0f} A >= I>={beng['I_gewaehlt_prim']:.0f} A"
                   if beng['Ik_masch_stat_prim'] else "-")
        v51_hin = "Reine Ueberstromstufe haelt bereits ohne Spannungssteuerung."
    add("Reserve trotz abklingendem Eigenstrom wirksam (51V)", "Ik,stat vs I>",
        v51_erg, "OK" if beng['Ik_masch_stat_prim'] else "Fehlt", v51_hin)

    # 40 Untererregung sinnvoll
    add("Untererregung (40): 1/xd KL.1 plausibel", "0,9*KL1 = KL2 < KL1",
        f"KL1={f40['xd_KL1']:.2f}; KL2={f40['xd_KL2']:.2f}; KL3={f40['xd_KL3']:.2f}",
        "OK" if f40["xd_KL1"] > 0 else "Fehlt",
        "KL.1 statische Stabilitaet (~1/xd), KL.2=0,9*KL.1, KL.3 dynamisch (7UM62 Hdb. 2.11).",
        "xd eingeben, damit 1/xd KL.1 berechnet wird.")

    # Erdschlusserfassung passt zur Sternpunktbehandlung
    stp = f59n["stp"]
    erg = ("U0/3I0-Richtung (sin-phi ~90 Grad)" if stp == "Isoliert"
           else "U0-Verfahren (Erdungstrafo)" if "Hochohmig" in stp
           else "niederohmig: Erdstrom direkt erfassbar")
    add("Staendererdschluss passt zur Sternpunktbehandlung", "Stp_Gen",
        erg, "OK",
        "90 % Staendererdschluss ueber U0 (Adr.5002). 100 % zusaetzlich ueber "
        "3. Harmonische bzw. 20-Hz-Verspannung (7UM62 Hdb. 2.23/2.24/2.25).")

    return checks


# ── Reserveschutz-Zuordnung / DIGSI-Adressen ─────────────────────────────────

def reserveschutz(g: dict, umz: dict, v51: dict, b49: dict) -> list:
    return [
        {"funktion": "UMZ I> + U<-Haltung (Adr.1201)", "ziel": "Klemmenseite",
         "I_sek": f"{umz['I_sek']:.4f}", "t": f"{umz['t_I']:.2f}",
         "IHH_sek": f"{umz['IHH_sek']:.4f}", "tHH": f"{umz['t_IHH']:.2f}",
         "adresse": "I> 1202; T 1203; U< 1205; I>> 1302; T 1303"},
        {"funktion": "AMZ 51V spannungsabh. (Adr.1401)", "ziel": "Klemmenseite",
         "I_sek": f"{v51['Ip_sek']:.4f}", "t": f"{v51['T_Ip']:.2f}",
         "IHH_sek": "-", "tHH": "-",
         "adresse": "Ip 1402; T Ip 1403; U< 1408"},
        {"funktion": "Ueberlast 49 (Adr.1601)", "ziel": "Maschine",
         "I_sek": f"{b49['k_Faktor'] * g['IN_K_sek']:.4f}", "t": f"{b49['tau_s']:.0f} s",
         "IHH_sek": "-", "tHH": "-",
         "adresse": "k 1602; tau 1603 (SEKUNDEN!); Theta 1604; I-Warn 1610A"},
    ]


# ── Geraete-/Architektur-Empfehlung ──────────────────────────────────────────

def geraeteempfehlung(p: dict) -> dict:
    anschluss = p.get("anschluss", "Direkt auf MS-Sammelschiene")
    stp = p.get("stp_Gen", "Hochohmig (Erdungstrafo / Petersen)")
    if anschluss.startswith("Block"):
        arch = ("Blockschaltung: 87G schuetzt nur den Generator (CTs Klemme + Sternpunkt). "
                "Maschinentrafo separat ueber 87T (Trafo-Tab); ein uebergreifender "
                "Blockdifferentialschutz (87GT) kann optional ergaenzt werden.")
    else:
        arch = ("Direkter Sammelschienen-Anschluss: 87G ueber CTs Klemme + Sternpunkt; "
                "der Generator speist auf das isolierte Industrienetz.")
    if stp == "Isoliert":
        erd = ("Isolierter Generator-Sternpunkt: 90 % Staendererdschluss ueber "
               "Verlagerungsspannung U0 mit Richtung (sin-phi ~90 Grad). "
               "100 % ueber 3. Harmonische bzw. 20-Hz-Verspannung.")
    elif "Hochohmig" in stp:
        erd = ("Hochohmige Erdung (Erdungstrafo/Petersen): 90 % Staendererdschluss "
               "ueber U0 (Adr.5002), Richtungswinkel ~15 Grad. 100 % zusaetzlich "
               "ueber 3. Harmonische.")
    else:
        erd = ("Niederohmige Erdung: Erdfehlerstrom direkt erfassbar; "
               "Staendererdschluss ueber Stromkriterium moeglich.")
    return {"architektur": arch, "erdschluss": erd}


# ── Master-Funktion ───────────────────────────────────────────────────────────

def berechne_alle(p: dict) -> dict:
    g    = grundgroessen(p)
    e87G = schutz_87G(g, p)
    umz  = schutz_5051(g, p)
    v51  = schutz_51V(g, p)
    b49  = schutz_49(g, p)
    b46  = schutz_46(g, p)
    f40  = schutz_40(g, p)
    f32  = schutz_32(g, p)
    f24  = schutz_24(g, p)
    f2759= schutz_2759(g, p)
    f81  = schutz_81(g, p)
    f59n = schutz_59N(g, p)
    f64r = schutz_64R(g, p)
    beng = bemessung_engineering(g, p, umz)
    plaus = plausibilitaet(g, p, b49, beng, f40, f59n)
    rsv  = reserveschutz(g, umz, v51, b49)
    geh  = geraeteempfehlung(p)

    return {
        "grund": g,
        "87G": e87G,
        "5051": umz,
        "51V": v51,
        "49": b49,
        "46": b46,
        "40": f40,
        "32": f32,
        "24": f24,
        "2759": f2759,
        "81": f81,
        "59N": f59n,
        "64R": f64r,
        "bemessung": beng,
        "plausibilitaet": plaus,
        "reserveschutz": rsv,
        "empfehlung": geh,
    }
