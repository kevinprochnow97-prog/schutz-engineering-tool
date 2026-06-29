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

    def row(name, fak, einheit, emp, adr, sek=True, prim=True):
        return {
            "name": name, "faktor": fak, "einheit": einheit,
            "wert_sek": round(fak * INO, 4) if sek else None,
            "wert_prim": round(fak * INp, 4) if prim else None,
            "empfehlung": emp,
            "status": status_empfehlung(fak, emp) if emp is not None else "—",
            "adresse": adr,
        }

    rows = [
        row("I-DIFF>  (Ansprechwert)",   I_DIFF,    "I/InO", emp_IDIFF,   "Adr.2021"),
        row("I-DIFF>> (Schnellausl.)",   I_DIFF_HH, "I/InO", emp_IDIFFHH, "Adr.2031"),
        {"name": "Steigung 1", "faktor": Steig1, "einheit": "-", "wert_sek": None,
         "wert_prim": None, "empfehlung": emp_Steig1, "status": status_empfehlung(Steig1, emp_Steig1), "adresse": "Adr.2041A"},
        {"name": "Steigung 2", "faktor": Steig2, "einheit": "-", "wert_sek": None,
         "wert_prim": None, "empfehlung": emp_Steig2, "status": status_empfehlung(Steig2, emp_Steig2), "adresse": "Adr.2043A"},
        row("Fusspunkt 2", Fp2, "I/InO", emp_Fp2, "Adr.2044A", sek=True, prim=False),
        {"name": "Anlauf-Stabilisierung", "faktor": K.Anlauf_Stab_def, "einheit": "I/InO",
         "wert_sek": round(K.Anlauf_Stab_def * INO, 4), "wert_prim": None,
         "empfehlung": None, "status": "—", "adresse": "Adr.2051A"},
        {"name": "EXF-Stab. (ext. Fehler)", "faktor": K.EXF_Stab_def, "einheit": "I/InO",
         "wert_sek": round(K.EXF_Stab_def * INO, 4), "wert_prim": None,
         "empfehlung": None, "status": "—", "adresse": "Adr.2061A"},
        {"name": "T I-DIFF>",  "faktor": K.T_I_DIFF_def,    "einheit": "s", "wert_sek": None,
         "wert_prim": None, "empfehlung": None, "status": "—", "adresse": "Adr.2026A"},
        {"name": "T I-DIFF>>", "faktor": K.T_I_DIFF_HH_def, "einheit": "s", "wert_sek": None,
         "wert_prim": None, "empfehlung": None, "status": "—", "adresse": "Adr.2036A"},
        {"name": "2. Harmonische (Inrush)", "faktor": round(Harm2 * 100, 1), "einheit": "%",
         "wert_sek": None, "wert_prim": None, "empfehlung": None, "status": "—", "adresse": "Adr.2071"},
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
        a1, a2, a3, a4 = "4203", "4206", "4209", "4212"   # 60-Hz-Schwellenadressen
    else:
        f1, f2, f3, f4 = K.f1_def, K.f2_def, K.f3_def, K.f4_def
        a1, a2, a3, a4 = "4202", "4205", "4208", "4211"   # 50-Hz-Schwellenadressen
    return {
        "fN": fN,
        "stufen": [
            {"name": "f1 (Netztrennung)",       "f": f1, "t": K.t_f1_def, "adr": f"Adr.{a1} / T 4204"},
            {"name": "f2 (Stillsetzung)",       "f": f2, "t": K.t_f2_def, "adr": f"Adr.{a2} / T 4207"},
            {"name": "f3 (Warnung Unterfreq.)", "f": f3, "t": K.t_f3_def, "adr": f"Adr.{a3} / T 4210"},
            {"name": "f4 (Ueberfrequenz)",      "f": f4, "t": K.t_f4_def, "adr": f"Adr.{a4} / T 4213"},
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


# ── 21 Impedanzschutz (Reserve, Seite 2) ─────────────────────────────────────

def schutz_21(g: dict, p: dict) -> dict:
    """
    Impedanzschutz (ANSI 21) als Reserve-/Zeitstaffelschutz, Bezug Seite 2 (Klemmen-CT).
    Anregung IMP I> = Faktor x IN_K_sek (oberhalb der max. Betriebslast).
    Zonen Z1/Z1B/Z2 als Sekundaer-Ohm; Primaerreichweite ueber
    Z_prim = Z_sek * nVT / kCT_K  (Umkehrung von Z_sek = Z_prim * kCT_K/nVT).
    Die exakte Zonen-Reichweite haengt von der Maschinentrafo-/Netzimpedanz ab und
    ist daher als Hersteller-Voreinstellung mit Umrechnung dargestellt (7UM62 Hdb. 2.14).
    """
    INk, INp = g["IN_K_sek"], g["IN_prim"]
    kCT_K, nVT = g["kCT_K"], g["nVT"]
    k_Z = (kCT_K / nVT) if nVT else 0.0          # Z_sek / Z_prim

    def z_prim(z_sek):
        return round(z_sek / k_Z, 4) if k_Z else 0.0

    f_I = p.get("Imp_I_Faktor", K.Imp_I_anr_Faktor)
    Z1  = p.get("Imp_Z1",  K.Imp_Z1_def)
    Z1B = p.get("Imp_Z1B", K.Imp_Z1B_def)
    Z2  = p.get("Imp_Z2",  K.Imp_Z2_def)
    return {
        "aktiv":        p.get("Imp_aktiv", K.Imp_aktiv_def),
        "f_I_anr":      f_I,
        "I_anr_sek":    round(f_I * INk, 4),
        "I_anr_prim":   round(f_I * INp, 4),
        "U_halt_aktiv": p.get("Imp_Uhalt", K.Imp_Uhalt_def),
        "U_halt":       p.get("Imp_U_halt", K.Imp_U_halt_def),
        "T_halt":       p.get("Imp_T_halt", K.Imp_T_halt_def),
        "k_Z":          round(k_Z, 4),
        "Z1_sek": Z1,   "Z1_prim": z_prim(Z1),   "t_Z1":  p.get("Imp_T_Z1",  K.Imp_T_Z1_def),
        "Z1B_sek": Z1B, "Z1B_prim": z_prim(Z1B), "t_Z1B": p.get("Imp_T_Z1B", K.Imp_T_Z1B_def),
        "Z2_sek": Z2,   "Z2_prim": z_prim(Z2),   "t_Z2":  p.get("Imp_T_Z2",  K.Imp_T_Z2_def),
        "T_End":        p.get("Imp_T_End", K.Imp_T_End_def),
    }


# ── 78 Aussertrittfallschutz / Polschlupf ────────────────────────────────────

def schutz_78(g: dict, p: dict) -> dict:
    """
    Aussertrittfallschutz (ANSI 78). Polygon Za/Zb/Zc/(Zd-Zc) als Sekundaer-Ohm.
    Freigaben: I1> (Mitsystem, ueber Nennstrom) gibt frei, I2< (Gegensystem) sperrt.
    Polygon-Reichweite ergibt sich aus der transienten Maschinenreaktanz x'd und der
    Netz-/Trafoimpedanz; daher Hersteller-Voreinstellung mit Sekundaer/Primaer-
    Umrechnung (7UM62 Hdb. 2.15).
    """
    INk, INp = g["IN_K_sek"], g["IN_prim"]
    kCT_K, nVT = g["kCT_K"], g["nVT"]
    k_Z = (kCT_K / nVT) if nVT else 0.0

    def z_prim(z_sek):
        return round(z_sek / k_Z, 4) if k_Z else 0.0

    I1 = p.get("Aus_I1_frei", K.Aus_I1_frei_def)   # % IN
    I2 = p.get("Aus_I2_frei", K.Aus_I2_frei_def)   # % IN
    Za   = p.get("Aus_Za",   K.Aus_Za_def)
    Zb   = p.get("Aus_Zb",   K.Aus_Zb_def)
    Zc   = p.get("Aus_Zc",   K.Aus_Zc_def)
    ZdZc = p.get("Aus_ZdZc", K.Aus_ZdZc_def)
    return {
        "aktiv":       p.get("Aus_aktiv", K.Aus_aktiv_def),
        "k_Z":         round(k_Z, 4),
        "I1_frei_pct": I1, "I1_frei_sek": round(I1 / 100 * INk, 4), "I1_frei_prim": round(I1 / 100 * INp, 4),
        "I2_frei_pct": I2, "I2_frei_sek": round(I2 / 100 * INk, 4), "I2_frei_prim": round(I2 / 100 * INp, 4),
        "Za_sek": Za,     "Za_prim": z_prim(Za),
        "Zb_sek": Zb,     "Zb_prim": z_prim(Zb),
        "Zc_sek": Zc,     "Zc_prim": z_prim(Zc),
        "ZdZc_sek": ZdZc, "ZdZc_prim": z_prim(ZdZc),
        "phi":   p.get("Aus_Phi",   K.Aus_Phi_def),
        "n_KL1": p.get("Aus_n_KL1", K.Aus_n_KL1_def),
        "n_KL2": p.get("Aus_n_KL2", K.Aus_n_KL2_def),
        "T_halt": p.get("Aus_T_halt", K.Aus_T_halt_def),
        "T_meld": p.get("Aus_T_meld", K.Aus_T_meld_def),
    }


# ── Bemessungs-Engineering (Reserve-Ueberstrom) ─────────────────────────────

def bemessung_engineering(g: dict, p: dict, umz: dict) -> dict:
    """
    Verifiziert die Reserve-Ueberstromstufe gegen max. Last und min. Fehlerstrom.
    KEIN Ersatz fuer eine Kurzschlussberechnung.
    """
    k_S_I  = p.get("k_S_I",  K.k_S_I)
    gamma  = p.get("gamma",  K.gamma_Ikmin)
    INp    = g["IN_prim"]
    Ik_max = p.get("Ik_max_kA", 0.0) * 1000.0

    I_max_Last = INp * 1.0                      # Generator: Dauerlast ~ IN
    # I_k_min: bevorzugt Eingabe (DIN EN 60909-0, c=0,95), sonst Näherung 0,3 x Ik''max.
    Ik_min = p.get("Ik_min_kA", 0.0) * 1000.0
    if Ik_min > 0:
        I_k_min        = Ik_min
        I_k_min_quelle = "Eingabe (DIN EN 60909-0)"
    elif Ik_max:
        I_k_min        = Ik_max * 0.3
        I_k_min_quelle = "Näherung 0,3 × Ik″max"
    else:
        I_k_min        = 0.0
        I_k_min_quelle = "fehlt (Ik max/min eingeben)"
    I_emp      = k_S_I * I_max_Last
    I_gewaehlt = umz["f_I"] * INp
    I_status   = "OK" if (I_emp and I_gewaehlt >= I_emp * 0.999) else ("Prüfen!" if I_emp else "Fehlt")
    f_I_emp    = round(k_S_I, 2)

    empfind = I_k_min / I_gewaehlt if I_gewaehlt else 0.0
    empfind_status = "OK" if (empfind and empfind >= gamma) else ("Prüfen!" if I_k_min else "Fehlt")

    korr_I = (f"Regler 'I> Phase' auf >= {f_I_emp:g} x IN stellen (aktuell {umz['f_I']:g})."
              if I_status == "Prüfen!" else "")
    korr_emp = ("Empfindlichkeit zu gering: I> senken oder gamma reduzieren, "
                f"bis I_k_min/I> >= {gamma:g}." if empfind_status == "Prüfen!" else "")

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
    }


# ── Plausibilitaetspruefung (Ampel) ─────────────────────────────────────────

def plausibilitaet(g: dict, p: dict, b49: dict, beng: dict, f40: dict,
                   f59n: dict, f32P: dict, fIEE: dict,
                   f81R: dict, fVS: dict, fBF: dict) -> list:
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
    add("Empfindlichkeit I_k_min / I> >= gamma", f"gamma = {beng['gamma']}",
        f"{beng['empfind']:.2f}" if beng['empfind'] else "-", beng["empfind_status"],
        "Min. Fehlerstrom am Schutzgebiet-Ende muss I> sicher anregen. "
        "Hinweis: 51V mit Unterspannungssteuerung verbessert die Empfindlichkeit "
        "bei abklingendem Generator-KS-Strom.",
        beng["korr_emp"])

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

    # 32P Vorwaertsleistung: P< muss kleiner als P> sein (sinnvolle Stufenfolge)
    if f32P["aktiv"]:
        pvorw_ok = f32P["P_un_pct"] < f32P["P_ue_pct"]
        add("32P: P< VORW. < P> VORW. (Stufenfolge plausibel)",
            "P_un < P_ue",
            f"{f32P['P_un_pct']:.1f} % < {f32P['P_ue_pct']:.1f} %",
            "OK" if pvorw_ok else "Prüfen!",
            "Unterschreitungsschwelle muss unter Ueberschreitungsschwelle liegen (7UM62 Hdb. 2.13).",
            "P< VORW. (Adr.3202) verkleinern oder P> VORW. (Adr.3204) vergroessern.")
        vt_ok = f32P["vt_ok"]
        add("32P: VT-Daten vorhanden (fuer SN_sek-Umrechnung)",
            "SN_sek > 0",
            f"SN_sek = {f32P['SN_sek']:.1f} VA" if vt_ok else "SN_sek = 0",
            "OK" if vt_ok else "Fehlt",
            "32P benoetigt Spannungswandler-Daten zur Umrechnung in Wattwert.",
            "VT prim. [kV] und VT sek. [V] sowie CT-Daten eingeben.")

    # IEE Empfindlicher Erdstromschutz: IEE>> > IEE>
    if fIEE["aktiv"]:
        add("IEE: Ausloesestrom IEE>> > Anregestrom IEE>",
            "IEE>> > IEE>",
            f"{fIEE['IEE_aus']:.1f} mA > {fIEE['IEE_an']:.1f} mA",
            "OK" if fIEE["stufen_ok"] else "Prüfen!",
            "Ausloesestrom muss ueber Anregestrom liegen — sonst keine sinnvolle Zweistufigkeit "
            "(7UM62 Hdb. 2.26, Adr.5102/5104).",
            "IEE>> (Adr.5104) groesser als IEE> (Adr.5102) einstellen.")

    # 81R df/dt: VT-Check und U_MIN-Empfehlung
    if f81R["aktiv"]:
        add("81R df/dt: VT-Daten vorhanden (fuer Frequenzmessung)",
            "UN_sek > 0",
            f"UN_sek = {f81R['UN_sek']:.1f} V" if f81R["vt_ok"] else "UN_sek = 0",
            "OK" if f81R["vt_ok"] else "Fehlt",
            "df/dt erfordert Mitsystemspannung. Spannungswandler-Daten eingeben.",
            "VT prim. [kV] und VT sek. [V] in den Grunddaten eingeben.")
        add("81R df/dt: U_MIN im empfohlenen Bereich (55...75 % UN_sek)",
            "0,55 * UN <= U_MIN <= 0,75 * UN",
            f"{f81R['Umin']:.0f} V = {f81R['Umin_pct']:.0f} % UN_sek",
            "OK" if f81R["umin_ok"] else "Hinweis",
            "Empfehlung: ~65 % UN_sek, damit bei Spannungseinbruch die Messung "
            "noch zuverlaessig ist (7UM62 Hdb. 2.21, Adr.4518).",
            f"U_MIN (Adr.4518) auf ca. {0.65 * f81R['UN_sek']:.0f} V ({65:.0f} % UN_sek) stellen.")

    # Vektorsprung: VT-Check und Spannungsband
    if fVS["aktiv"]:
        add("Vektorsprung: VT-Daten vorhanden",
            "UN_sek > 0",
            "vorhanden" if fVS["vt_ok"] else "fehlt",
            "OK" if fVS["vt_ok"] else "Fehlt",
            "Vektorsprung benoetigt Mitsystemspannung. VT-Daten eingeben.",
            "VT prim. [kV] und VT sek. [V] in den Grunddaten eingeben.")
        add("Vektorsprung: U_MIN < U_MAX (Spannungsband sinnvoll)",
            "U_MIN < U_MAX",
            f"{fVS['Umin']:.0f} V < {fVS['Umax']:.0f} V",
            "OK" if fVS["uband_ok"] else "Prüfen!",
            "Der Spannungsarbeitsbereich U_MIN (Adr.4605A) muss kleiner als U_MAX (Adr.4606A) sein "
            "(7UM62 Hdb. 2.22).",
            "U_MIN verkleinern oder U_MAX vergroessern.")

    # 50BF Leistungsschalterversagerschutz
    if fBF["aktiv"]:
        add("50BF: SVS I> im gueltigen Einstellbereich",
            f"[{fBF['I_min']:.2f} ... {fBF['I_max']:.2f}] A sek.",
            f"{fBF['I_sek']:.3f} A sek. (CT {fBF['CT_sek']} A)",
            "OK" if fBF["I_ok"] else "Prüfen!",
            "Stromansprechschwelle mindestens 10 % unterhalb des kleinsten erwarteten "
            "Betriebsstroms — nicht zu niedrig, da sonst CT-Ausgleichsvorgaenge "
            "die Rueckfallzeit erlaengern (7UM62 Hdb. 2.36, Adr.7003).",
            f"SVS I> (Adr.7003) in gueltigen Bereich {fBF['I_min']:.2f}...{fBF['I_max']:.2f} A bringen.")
        add("50BF: SVS-Taus >= empfohlene Mindestzeit",
            f">= t_LS + t_RF + t_Marge = {fBF['Taus_min_emp']:.3f} s",
            f"{fBF['Taus']:.3f} s",
            "OK" if fBF["Taus_ok"] else "Hinweis",
            "SVS-Taus = t_LS_max + t_RF + t_Marge. "
            f"Richtwert: 80 ms LS-Zeit + 20 ms Rueckfall + 50 ms Marge = {fBF['Taus_min_emp']:.0f} ms "
            "(7UM62 Hdb. 2.36, Adr.7004).",
            f"SVS-Taus (Adr.7004) auf mindestens {fBF['Taus_min_emp']:.3f} s erhoehen.")

    return checks



# ── Reserveschutz-Zuordnung / DIGSI-Adressen ─────────────────────────────────

def reserveschutz(g: dict, umz: dict, v51: dict, b49: dict, p: dict) -> list:
    un  = p.get("UN_kV", 0.0)
    anschluss = p.get("anschluss", "")
    netz = "Maschinentrafo (Blockschaltung)" if anschluss.startswith("Block") else "MS-Sammelschiene (Direktanschluss)"
    return [
        {"funktion": "UMZ I> + U<-Haltung (Adr.1201)",
         "ziel": f"Generator-Klemmen — Netzschnittstelle zu {netz} (CT Klemme, {un:.1f} kV)",
         "I_sek": f"{umz['I_sek']:.4f}", "t": f"{umz['t_I']:.2f}",
         "IHH_sek": f"{umz['IHH_sek']:.4f}", "tHH": f"{umz['t_IHH']:.2f}",
         "adresse": "I> 1202; T 1203; U< 1205; I>> 1302; T 1303"},
        {"funktion": "AMZ 51V spannungsabh. (Adr.1401)",
         "ziel": f"Generator-Klemmen — Netzschnittstelle zu {netz} (CT Klemme, {un:.1f} kV)",
         "I_sek": f"{v51['Ip_sek']:.4f}", "t": f"{v51['T_Ip']:.2f}",
         "IHH_sek": "-", "tHH": "-",
         "adresse": "Ip 1402; T Ip 1403; U< 1408"},
        {"funktion": "Ueberlast 49 (Adr.1601)",
         "ziel": f"Generator-Stator — Wicklungsschutz thermisch (CT Klemme, {un:.1f} kV)",
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


# ── 32P Vorwaertsleistungsueberwachung ───────────────────────────────────────

def schutz_32P(g: dict, p: dict) -> dict:
    """
    Vorwaertsleistungsueberwachung (ANSI 32P, 7UM62 Kap. 2.13).
    Einstellwerte in % der sekundaeren Nennscheinleistung SN_sek.
    P_sek = P_pct / 100 * SN_sek (SN_sek = sqrt(3) * UN_sek * IN_sek, identisch zu 32).
    Kein Rueckleistungs-/Generatorkennwert noetig; reine Schwellwertfunktion.
    Voraussetzung: VT-Daten muss vorhanden sein (SN_sek > 0).
    """
    SNs  = g["SN_sek"]
    P_un = p.get("PVorw_un",  K.PVorw_un_def)
    t_un = p.get("t_PVorw_un", K.t_PVorw_un_def)
    P_ue = p.get("PVorw_ue",  K.PVorw_ue_def)
    t_ue = p.get("t_PVorw_ue", K.t_PVorw_ue_def)
    return {
        "aktiv":    p.get("PVorw_aktiv", K.PVorw_aktiv_def),
        "P_un_pct": P_un,
        "t_un":     t_un,
        "P_ue_pct": P_ue,
        "t_ue":     t_ue,
        "P_un_W":   round((P_un / 100.0) * SNs, 1) if SNs else 0.0,
        "P_ue_W":   round((P_ue / 100.0) * SNs, 1) if SNs else 0.0,
        "SN_sek":   round(SNs, 1),
        "vt_ok":    SNs > 0.0,
    }


# ── IEE Empfindlicher Erdstromschutz ─────────────────────────────────────────

def schutz_IEE(g: dict, p: dict) -> dict:
    """
    Empfindlicher Erdstromschutz (7UM62 Kap. 2.26, Adr. 5101-5106).
    Zweistufige Erfassung des Erdstroms am empfindlichen IEE-Eingang (mA).
    Alle Einstellwerte direkt in Milliampere — keine CT-Umrechnung erforderlich.
    Anwendung: Staender- oder Laeufererdschluss als Ergaenzung zu 64R oder als
    Alternative, wenn ausschliesslich der Erdstrombetrag als Kriterium genuegt.
    Sinnvoll: IEE>> > IEE> (Stufenfolge einhalten).
    """
    IEE_an  = p.get("IEE_an",    K.IEE_an_def)
    t_an    = p.get("t_IEE_an",  K.t_IEE_an_def)
    IEE_aus = p.get("IEE_aus",   K.IEE_aus_def)
    t_aus   = p.get("t_IEE_aus", K.t_IEE_aus_def)
    IEE_ueb = p.get("IEE_ueb",   K.IEE_ueb_def)
    # Plausibilitaet: Ausloesewert muss ueber Anregewert liegen
    stufen_ok = IEE_aus > IEE_an if IEE_an > 0 else True
    return {
        "aktiv":      p.get("IEE_aktiv", K.IEE_aktiv_def),
        "IEE_an":     IEE_an,
        "t_IEE_an":   t_an,
        "IEE_aus":    IEE_aus,
        "t_IEE_aus":  t_aus,
        "IEE_ueb":    IEE_ueb,
        "ueb_aktiv":  IEE_ueb > 0.0,
        "stufen_ok":  stufen_ok,
    }



# ── 81R Frequenzaenderungsschutz df/dt ────────────────────────────────────────

def schutz_dfdt(g: dict, p: dict) -> dict:
    """
    Frequenzaenderungsschutz df/dt (ANSI 81R, 7UM62 Kap. 2.21, Adr. 4501-4518).
    Vier Stufen, jede mit Richtung, Ansprechwert [Hz/s] und Verzoegerung [s].
    Voraussetzung: VT muss vorhanden sein (Frequenzmessung aus Mitsystemspannung).
    Ansprechwert anlagenspezifisch; Naeherung:
        |df/dt| = fN / (2*H) * |dP/SN|
    mit H = Traegheitskonstante der Maschine [s], dP/SN = relativer Leistungssprung.
    """
    vt_ok = g["UN_sek"] > 0
    rich_keys  = ["dfdt_1_rich",  "dfdt_2_rich",  "dfdt_3_rich",  "dfdt_4_rich"]
    stufe_keys = ["dfdt_1_stufe", "dfdt_2_stufe", "dfdt_3_stufe", "dfdt_4_stufe"]
    t_keys     = ["dfdt_1_t",     "dfdt_2_t",     "dfdt_3_t",     "dfdt_4_t"]
    rich_defs  = [K.dfdt_1_rich_def,  K.dfdt_2_rich_def,
                  K.dfdt_3_rich_def,  K.dfdt_4_rich_def]
    stufe_defs = [K.dfdt_1_stufe_def, K.dfdt_2_stufe_def,
                  K.dfdt_3_stufe_def, K.dfdt_4_stufe_def]
    t_defs     = [K.dfdt_1_t_def, K.dfdt_2_t_def, K.dfdt_3_t_def, K.dfdt_4_t_def]
    stufen = []
    for i in range(4):
        rich  = p.get(rich_keys[i],  rich_defs[i])
        stufe = p.get(stufe_keys[i], stufe_defs[i])
        t_val = p.get(t_keys[i],     t_defs[i])
        adrs  = K.DFDT_STUFEN_ADR[i]
        stufen.append({
            "nr": i + 1, "name": f"df{i+1}/dt",
            "richtung": rich, "stufe": stufe, "t": t_val,
            "adr_r": adrs[0], "adr_s": adrs[1], "adr_t": adrs[2],
        })
    Umin   = p.get("dfdt_Umin", K.dfdt_Umin_def)
    UN_sek = g["UN_sek"] if g["UN_sek"] else 100.0
    umin_ok = 0.55 * UN_sek <= Umin <= 0.75 * UN_sek
    return {
        "aktiv":    p.get("dfdt_aktiv", K.dfdt_aktiv_def),
        "stufen":   stufen,
        "Umin":     Umin,
        "Umin_pct": round(100 * Umin / UN_sek, 0),
        "umin_ok":  umin_ok,
        "vt_ok":    vt_ok,
        "UN_sek":   UN_sek,
    }


# ── Vektorsprung ──────────────────────────────────────────────────────────────

def schutz_vektorsprung(g: dict, p: dict) -> dict:
    """
    Vektorsprungschutz (7UM62 Kap. 2.22, Adr. 4601-4607).
    Erkennt Phasenwinkelsprung der Mitsystemspannung nach Stromunterbrechung.
    Hauptanwendung: Netzentkupplung von Eigenerzeugern.
    Einstellwert DELTA PHI ist anlagenspezifisch; Voreinst. 10 Grad konservativ.
    Voraussetzung: VT muss vorhanden sein.
    """
    vt_ok  = g["UN_sek"] > 0
    UN_sek = g["UN_sek"] if g["UN_sek"] else 100.0
    dphi   = p.get("VS_dphi",    K.VS_dphi_def)
    t_dphi = p.get("VS_t_dphi",  K.VS_t_dphi_def)
    t_rst  = p.get("VS_t_reset", K.VS_t_reset_def)
    Umin   = p.get("VS_Umin",    K.VS_Umin_def)
    Umax   = p.get("VS_Umax",    K.VS_Umax_def)
    uband_ok = Umin < Umax
    return {
        "aktiv":    p.get("VS_aktiv", K.VS_aktiv_def),
        "dphi":     dphi,
        "t_dphi":   t_dphi,
        "t_reset":  t_rst,
        "Umin":     Umin,
        "Umax":     Umax,
        "Umin_pct": round(100 * Umin / UN_sek, 0),
        "Umax_pct": round(100 * Umax / UN_sek, 0),
        "uband_ok": uband_ok,
        "vt_ok":    vt_ok,
    }


# ── 50BF Leistungsschalterversagerschutz ──────────────────────────────────────

def schutz_50BF(g: dict, p: dict) -> dict:
    """
    Leistungsschalterversagerschutz (ANSI 50BF, 7UM62 Kap. 2.36, Adr. 7001-7004).
    Zwei numerisch einstellbare Parameter:
      SVS I>   (Adr.7003): Stromansprechschwelle, mindestens 10 % unterhalb des
               kleinsten erwarteten Betriebsstroms. Voreinstellung CT-abhaengig.
      SVS-Taus (Adr.7004): Ausloesezeit = t_LS_max + t_RF + t_Marge.
    Nicht-numerische Konfigurationsoptionen (keine Sliders):
      Adr.7001 SCHALTERVERSAG.: Ein/Aus  — im Tool als Checkbox.
      Adr.7002 AUS INTERN: BA12/CFC/Aus  — im Tool als Info-Text (kein DIGSI-Zahlenwert).
    SVS I> wird primaer und sekundaer angezeigt; Empfehlung = DIGSI-Default-Ratio (20 % IN_sek).
    """
    CT_sek  = p.get("CT_K_Sek", 1)
    INk     = g["IN_K_sek"]
    INp     = g["IN_prim"]
    kCT_K   = g["kCT_K"]

    # Voreinstellung CT-abhaengig
    I_def   = K.BF_I_sek_5A_def if CT_sek == 5 else K.BF_I_sek_1A_def
    I_min   = K.BF_I_sek_5A_min if CT_sek == 5 else K.BF_I_sek_1A_min
    I_max   = K.BF_I_sek_5A_max if CT_sek == 5 else K.BF_I_sek_1A_max

    I_sek   = p.get("BF_I_sek", I_def)
    Taus    = p.get("BF_Taus",  K.BF_Taus_def)

    # Primaer-Aequivalent
    I_prim  = round(I_sek * kCT_K, 2) if kCT_K else 0.0
    # Empfehlung: DIGSI-Default-Ratio (20 % von IN_sek) als Oberschranke-Richtwert
    emp_I   = round(K.BF_I_emp_faktor * INk, 4) if INk else I_def

    # Plausibilitaet: I_sek muss im gueltigen Einstellbereich liegen
    I_ok    = I_min <= I_sek <= I_max
    # SVS-Taus muss >= empfohlene Mindestzeit sein (t_LS_typ + t_RF_typ)
    Taus_min_emp = K.BF_t_LS_typ + K.BF_t_RF_typ   # ohne Marge: 100 ms
    Taus_ok = Taus >= (Taus_min_emp + K.BF_t_Marge_typ)  # mit Marge: 150 ms

    return {
        "aktiv":       p.get("BF_aktiv", K.BF_aktiv_def),
        "CT_sek":      CT_sek,
        "I_sek":       I_sek,
        "I_prim":      I_prim,
        "emp_I_sek":   emp_I,
        "I_ok":        I_ok,
        "I_min":       I_min,
        "I_max":       I_max,
        "Taus":        Taus,
        "Taus_ok":     Taus_ok,
        "Taus_min_emp":round(K.BF_t_LS_typ + K.BF_t_RF_typ + K.BF_t_Marge_typ, 3),
    }


def berechne_alle(p: dict) -> dict:
    g    = grundgroessen(p)
    e87G = schutz_87G(g, p)
    umz  = schutz_5051(g, p)
    v51  = schutz_51V(g, p)
    b49  = schutz_49(g, p)
    b46  = schutz_46(g, p)
    f40  = schutz_40(g, p)
    f32  = schutz_32(g, p)
    f32P = schutz_32P(g, p)
    f24  = schutz_24(g, p)
    f2759= schutz_2759(g, p)
    f81  = schutz_81(g, p)
    f81R = schutz_dfdt(g, p)
    fVS  = schutz_vektorsprung(g, p)
    fBF  = schutz_50BF(g, p)
    f59n = schutz_59N(g, p)
    fIEE = schutz_IEE(g, p)
    f64r = schutz_64R(g, p)
    f21  = schutz_21(g, p)
    f78  = schutz_78(g, p)
    beng = bemessung_engineering(g, p, umz)
    plaus = plausibilitaet(g, p, b49, beng, f40, f59n, f32P, fIEE, f81R, fVS, fBF)
    rsv  = reserveschutz(g, umz, v51, b49, p)
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
        "32P": f32P,
        "24": f24,
        "2759": f2759,
        "81": f81,
        "81R": f81R,
        "VS": fVS,
        "50BF": fBF,
        "59N": f59n,
        "IEE": fIEE,
        "64R": f64r,
        "21": f21,
        "78": f78,
        "bemessung": beng,
        "plausibilitaet": plaus,
        "reserveschutz": rsv,
        "empfehlung": geh,
    }
