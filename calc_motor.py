"""
calc_motor.py — Berechnungslogik Motorschutz
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reine Python-Funktionen (kein Streamlit) -> isoliert testbar.
Methodik nach SIPROTEC 7SJ66 (Multifunktionsschutz mit Motorschutz fuer
Asynchronmaschinen). Ausgabe IEC-normiert (A, s, %, min).

Schutzfunktionen:
  49    Thermischer Ueberlastschutz (tau in MINUTEN!)  (Adr. 42xx)
  48    Motoranlaufueberwachung / Laeuferblockierung    (Adr. 41xx)
  66    Wiedereinschaltsperre / Anlaufzaehler           (Adr. 43xx)
  51M   Lastsprung-/Load-Jam-Schutz                     (Adr. 44xx)
  46    Schieflastschutz (Gegensystem)                  (Adr. 40xx)
  50/51 Phasen-Ueberstromzeitschutz                     (Adr. 12xx)
  37    Unterstrom / Lastverlust (Setpoint)             (DIGSI-Matrix)
"""

import math
import konstanten_motor as K
from calc_trafo import status_empfehlung, status_bereich  # gemeinsame Ampel-Helfer

SQRT3 = math.sqrt(3)


# ── Berechnete Grundgroessen ─────────────────────────────────────────────────

def grundgroessen(p: dict) -> dict:
    """
    Motor-Nennstrom, Wandlerverhaeltnis, Bezugsgroessen.
    IN_Motor aus mechanischer Leistung Pn [kW]: IN = Pn / (sqrt3 * UN * cosphi * eta).
    Direkteingabe IN_direkt [A] > 0 hat Vorrang.
    Erwartet: Pn_kW, UN_kV, cos_phi, eta, IN_direkt, CT_Prim, CT_Sek,
              I_Anlauf_Verh, I_max_Verh
    """
    Pn   = p.get("Pn_kW", 0.0)
    UN   = p.get("UN_kV", 0.0)
    cosp = p.get("cos_phi", K.cos_phi_def)
    eta  = p.get("eta", K.eta_def)

    if p.get("IN_direkt", 0.0) and p["IN_direkt"] > 0:
        IN_prim = p["IN_direkt"]
        in_quelle = "Direkteingabe"
    elif UN > 0 and cosp > 0 and eta > 0:
        IN_prim = (Pn * 1e3) / (SQRT3 * UN * 1e3 * cosp * eta)
        in_quelle = "aus Pn / (√3·UN·cosφ·η)"
    else:
        IN_prim = 0.0
        in_quelle = "fehlt"

    kCT = p["CT_Prim"] / p["CT_Sek"] if p.get("CT_Sek") else 0.0
    IN_sek = IN_prim / kCT if kCT else 0.0
    I_an   = p["CT_Sek"] / IN_sek if IN_sek else 0.0

    I_Anlauf_Verh = p.get("I_Anlauf_Verh", K.I_Anlauf_Verh_def)
    I_max_Verh    = p.get("I_max_Verh", K.I_max_Verh_def)
    I_Anlauf_prim = I_Anlauf_Verh * IN_prim
    I_Anlauf_sek  = I_Anlauf_Verh * IN_sek
    I_max_prim    = I_max_Verh * IN_prim
    I_max_sek     = I_max_Verh * IN_sek

    # Scheinleistung (informativ, fuer Einordnung): Sn = sqrt3 * UN * IN
    Sn_MVA = (SQRT3 * UN * 1e3 * IN_prim) / 1e6 if (UN and IN_prim) else 0.0

    # Spannungswandler (optional) — Voraussetzung fuer 27/59/47
    VT_vorhanden = bool(p.get("VT_vorhanden", False))
    VT_P = p.get("VT_Prim_kV", 0.0) * 1e3
    VT_S = p.get("VT_Sek_V", 0.0)
    nVT  = VT_P / VT_S if (VT_vorhanden and VT_S) else 0.0
    UnS  = VT_S if VT_vorhanden else 0.0

    return {
        "IN_prim":      round(IN_prim, 3),
        "IN_sek":       round(IN_sek, 4),
        "in_quelle":    in_quelle,
        "kCT":          round(kCT, 4),
        "I_an":         round(I_an, 4),
        "I_Anlauf_Verh":round(I_Anlauf_Verh, 2),
        "I_Anlauf_prim":round(I_Anlauf_prim, 1),
        "I_Anlauf_sek": round(I_Anlauf_sek, 4),
        "I_max_Verh":   round(I_max_Verh, 3),
        "I_max_prim":   round(I_max_prim, 2),
        "I_max_sek":    round(I_max_sek, 4),
        "Sn_MVA":       round(Sn_MVA, 3),
        "VT_vorhanden": VT_vorhanden,
        "nVT":          round(nVT, 2),
        "UnS":          round(UnS, 1),
        "UN_VT_prim":   round(VT_P / 1e3, 3),
    }


# ── 49 Thermischer Ueberlastschutz (tau in MINUTEN!) ────────────────────────

def schutz_49(g: dict, p: dict) -> dict:
    k      = p.get("k_Faktor", K.k_Faktor_def)
    tau_m  = p.get("tau_min",  K.tau_Mot_def)
    thetaW = p.get("Theta_Warn", K.Theta_Warn_def)
    I_W    = p.get("I_Warn", K.I_Warn_def)
    Ktau   = p.get("Ktau_Stop", K.Ktau_Stop_def)
    INs, INp = g["IN_sek"], g["IN_prim"]
    return {
        "k_Faktor":       k,
        "tau_min":        tau_m,
        "tau_s":          round(tau_m * 60.0, 0),
        "Theta_Warn_pct": round(thetaW * 100, 0),
        "Ktau_Stop":      Ktau,
        "I_max_zul_sek":  round(k * INs, 4),
        "I_max_zul_prim": round(k * INp, 2),
        "I_Warn_sek":     round(I_W, 4),
        "k_status":       status_bereich(k, K.k_Faktor_min, K.k_Faktor_max),
        "T_Emergency":    K.T_Emergency_def,
    }


# ── 48 Motoranlaufueberwachung ───────────────────────────────────────────────

def schutz_48(g: dict, p: dict) -> dict:
    I_start = p.get("Startup_Current", K.Startup_Current_def)  # sek.
    t_start = p.get("Startup_Time",    K.Startup_Time_def)
    t_lr    = p.get("Lock_Rotor_Time", K.Lock_Rotor_Time_def)
    I_mstart= p.get("I_Motor_Start",   K.I_Motor_Start_def)    # sek. (Adr.1107)
    return {
        "Startup_Current_sek": round(I_start, 4),
        "Startup_Time":        t_start,
        "Lock_Rotor_Time":     t_lr,
        "Startup_T_Warm":      K.Startup_T_Warm_def,
        "I_Motor_Start_sek":   round(I_mstart, 4),
        "t_Anlauf":            p.get("t_Anlauf", K.t_Anlauf_def),
        "t_LR_zul":            p.get("t_LR_zul", K.t_LR_zul_def),
    }


# ── 66 Wiedereinschaltsperre / Anlaufzaehler ────────────────────────────────

def schutz_66(g: dict, p: dict) -> dict:
    return {
        "IStart_IMOTnom":  p.get("IStart_IMOTnom", K.IStart_IMOTnom_def),
        "T_Start_Max":     p.get("T_Start_Max", K.T_Start_Max_def),
        "T_Equal":         K.T_Equal_def,
        "I_Mot_Nominal_sek": round(g["IN_sek"], 4),
        "Max_Warm_Starts": p.get("Max_Warm_Starts", K.Max_Warm_Starts_def),
        "Cold_minus_Warm": K.Cold_minus_Warm_def,
        "Ktau_Stop":       K.Ktau_Stop_66_def,
        "Ktau_Run":        K.Ktau_Run_66_def,
        "T_Min_Inhibit":   K.T_Min_Inhibit_def,
    }


# ── 51M Lastsprung-/Load-Jam-Schutz ──────────────────────────────────────────

def schutz_51M(g: dict, p: dict) -> dict:
    fak  = p.get("LoadJam_Faktor", K.LoadJam_Faktor)   # x IN_Motor
    INs, INp = g["IN_sek"], g["IN_prim"]
    LJ_sek = fak * INs
    LJ_alarm_sek = K.LoadJam_Alarm_Faktor * LJ_sek
    t_blk = round(2.0 * p.get("t_Anlauf", K.t_Anlauf_def), 2)  # = 2 x Anlaufzeit
    return {
        "LoadJam_Faktor":  fak,
        "LoadJam_I_sek":   round(LJ_sek, 4),
        "LoadJam_I_prim":  round(fak * INp, 2),
        "t_TRIP":          K.LoadJam_t_def,
        "I_Alarm_sek":     round(LJ_alarm_sek, 4),
        "t_ALARM":         K.LoadJam_tAlarm_def,
        "T_Start_Blk":     t_blk,
    }


# ── 46 Schieflastschutz (Gegensystem) ────────────────────────────────────────

def schutz_46(g: dict, p: dict) -> dict:
    I2d = p.get("I2_dauer", K.I2_dauer_def)
    I2k = p.get("I2_kurz",  K.I2_kurz_def)
    INs, INp = g["IN_sek"], g["IN_prim"]
    return {
        "I2_dauer_faktor": I2d,
        "I2_dauer_sek":    round(I2d * INs, 4),
        "I2_dauer_prim":   round(I2d * INp, 2),
        "t_46_1":          K.t_46_1_def,
        "I2_kurz_faktor":  I2k,
        "I2_kurz_sek":     round(I2k * INs, 4),
        "I2_kurz_prim":    round(I2k * INp, 2),
        "t_46_2":          K.t_46_2_def,
        "kennlinie":       K.Kennlinie_46_def,
        "I2d_status":      status_bereich(I2d, K.I2_dauer_min, K.I2_dauer_max),
    }


# ── 50/51 Phasen-Ueberstromzeitschutz ────────────────────────────────────────

def schutz_5051(g: dict, p: dict) -> dict:
    f_502 = p.get("f_50_2", K.f_50_2_def)
    t_502 = p.get("t_50_2", K.t_50_2_def)
    f_501 = p.get("f_50_1", K.f_50_1_def)
    t_501 = p.get("t_50_1", K.t_50_1_def)
    f_51  = p.get("f_51",   K.f_51_def)
    T_51  = p.get("T_51",   K.T_51_def)
    INs, INp = g["IN_sek"], g["IN_prim"]
    return {
        "f_50_2": f_502, "t_50_2": t_502,
        "f_50_1": f_501, "t_50_1": t_501,
        "f_51":   f_51,  "T_51":   T_51,
        "I_50_2_sek":  round(f_502 * INs, 4), "I_50_2_prim": round(f_502 * INp, 1),
        "I_50_1_sek":  round(f_501 * INs, 4), "I_50_1_prim": round(f_501 * INp, 1),
        "I_51_sek":    round(f_51  * INs, 4), "I_51_prim":   round(f_51  * INp, 1),
        "kennlinie":   K.Kennlinie_51_def,
    }


# ── 37 Unterstrom / Lastverlust ──────────────────────────────────────────────

def schutz_37(g: dict, p: dict) -> dict:
    pct = p.get("I_unter_pct", K.I_unter_pct_def)
    INs, INp = g["IN_sek"], g["IN_prim"]
    return {
        "I_unter_pct":  pct,
        "I_unter_sek":  round((pct / 100.0) * INs, 4),
        "I_unter_prim": round((pct / 100.0) * INp, 2),
        "t_unter":      K.t_unter_def,
    }


# ── 50N/51N Erdfehler-/Erdueberstromschutz ───────────────────────────────────

def schutz_50N51N(g: dict, p: dict) -> dict:
    """
    Erdueberstromschutz, Sternpunktbehandlung-abhaengig (analog Trafo-Tab):
      - Niederohmig geerdet -> Stromkriterium 50N/51N (Adr.13xx), definierter
        Erdfehlerstrom, Werksdefaults sekundaer (1-A-Basis).
      - Isoliert / kompensiert -> empfindliche Stufe 50Ns/51Ns ueber INs-Eingang
        + Verlagerungsspannung U0 (VN, Adr.3109); Richtungsbestimmung 67Ns
        (cos-phi kompensiert / sin-phi isoliert), Adr.3115. Das reine Strom-
        kriterium 50N/51N hat hier nur geringe Empfindlichkeit.
    Sekundaere Erdstroeme ueber das Phasenwandlerverhaeltnis auf primaer
    umgerechnet (Holmgreen). Ein separater Kabelumbauwandler kann ein eigenes
    Verhaeltnis haben (Hinweis im UI).
    """
    stp = p.get("stp_Netz", "Isoliert")
    niederohmig = "Niederohmig" in stp
    kCT = g["kCT"]

    # Standardstufen 50N/51N (Stromkriterium, sek. -> prim. ueber Phasen-CT)
    f50N2 = p.get("f_50N2", K.f_50N2_def)
    f50N1 = p.get("f_50N1", K.f_50N1_def)
    f51N  = p.get("f_51N",  K.f_51N_def)

    # Empfindliche Stufe 50Ns/51Ns + U0 (INs-Eingang, netzunabhaengig vom Phasen-CT)
    VN     = p.get("VN_50Ns", K.VN_50Ns_def)
    f50Ns2 = p.get("f_50Ns2", K.f_50Ns2_def)
    f50Ns1 = p.get("f_50Ns1", K.f_50Ns1_def)
    richtung = "sin-φ (Wattmetrisch n. anwendbar)" if stp == "Isoliert" else \
               ("cos-φ (wattmetrisch)" if "Kompensiert" in stp else K.Richtung_67Ns_def)

    return {
        "stp":           stp,
        "niederohmig":   niederohmig,
        "modus":         "Stromkriterium 50N/51N (Adr.13xx)" if niederohmig
                         else "Empfindlich 50Ns/51Ns/67Ns + U0 (Adr.31xx)",
        # Standard 50N/51N
        "f_50N2_sek":  round(f50N2, 4), "f_50N2_prim": round(f50N2 * kCT, 2), "t_50N2": K.t_50N2_def,
        "f_50N1_sek":  round(f50N1, 4), "f_50N1_prim": round(f50N1 * kCT, 2), "t_50N1": K.t_50N1_def,
        "f_51N_sek":   round(f51N, 4),  "f_51N_prim":  round(f51N * kCT, 2),  "T_51N":  K.T_51N_def,
        "kennlinie_51N": K.Kennlinie_51N_def,
        # Empfindliche Stufe
        "VN_sek":      round(VN, 1),
        "VN_pct":      round(100.0 * VN / K.VN_voll_V, 0) if K.VN_voll_V else 0.0,
        "t_64_1":      K.t_64_1_def,
        "f_50Ns2_sek": round(f50Ns2, 4), "t_50Ns2": K.t_50Ns2_def,
        "f_50Ns1_sek": round(f50Ns1, 4),
        "richtung":    richtung,
    }


# ── 27/59 Unter-/Ueberspannungsschutz (nur VT-Variante) ──────────────────────

def schutz_2759(g: dict, p: dict) -> dict:
    """
    Unter- (27) und Ueberspannungsschutz (59), je zweistufig, bezogen auf die
    VT-Sekundaernennspannung UnS (verkettet, typ. 100 V). Nur aktiv, wenn ein
    Spannungswandler eingetragen ist (7SJ66 Hdb. 2.6).
    """
    vt = g["VT_vorhanden"]
    if not vt:
        return {
            "aktiv": False,
            "grund": ("Keine Spannungsmessung eingetragen. ANSI 27/59 setzt einen "
                      "Spannungswandler am Motorabgang voraus. Im Eingabebereich "
                      "'Spannungswandler vorhanden' aktivieren und VT prim./sek. eintragen."),
        }
    UnS = g["UnS"] if g["UnS"] else 100.0
    pc = lambda v: round(100.0 * v / UnS, 0)
    U59_1 = p.get("U59_1", K.U59_1_def); U59_2 = p.get("U59_2", K.U59_2_def)
    U27_1 = p.get("U27_1", K.U27_1_def); U27_2 = p.get("U27_2", K.U27_2_def)
    return {
        "aktiv": True, "UnS": UnS,
        "U59_1": U59_1, "U59_1_pct": pc(U59_1), "t_59_1": K.t_59_1_def,
        "U59_2": U59_2, "U59_2_pct": pc(U59_2), "t_59_2": K.t_59_2_def,
        "U27_1": U27_1, "U27_1_pct": pc(U27_1), "t_27_1": K.t_27_1_def,
        "U27_2": U27_2, "U27_2_pct": pc(U27_2), "t_27_2": K.t_27_2_def,
        "DOUT_27": K.DOUT_27_def,
    }


# ── 47 Phasenfolge / Spannungsunsymmetrieschutz ──────────────────────────────

def schutz_47(g: dict, p: dict) -> dict:
    """
    Zweiteilig:
      (a) Phasenfolgeueberwachung (Adr.209): erwartete Drehfeldrichtung; meldet
          'Fail Ph. Seq.' bei Abweichung. Spannungsseitig ab |U| > 40 V, strom-
          seitig ab |I| > 0,5 IN aktiv (7SJ66 Hdb. 2.12). Die stromseitige
          Pruefung ist auch ohne VT verfuegbar.
      (b) Spannungsunsymmetrie ueber Gegensystem-Ueberspannung V2 (OP.QUANTITY
          59 = V2; Adr.5015/5016) — erfasst verdrehte/fehlende Phasenspannungen.
          Benoetigt VT.
    """
    vt  = g["VT_vorhanden"]
    UnS = g["UnS"] if g["UnS"] else 100.0
    pc  = lambda v: round(100.0 * v / UnS, 0)
    I_phseq_sek = K.I_PhSeq_min_faktor * g["IN_sek"]
    return {
        "aktiv_unsym":  vt,
        "phase_seq":    p.get("phase_seq", K.PHASE_SEQ_def),
        "U_phseq_min":  K.U_PhSeq_min_def,
        "I_phseq_min_faktor": K.I_PhSeq_min_faktor,
        "I_phseq_min_sek":    round(I_phseq_sek, 4),
        "U59_V2_1": p.get("U59_V2_1", K.U59_V2_1_def),
        "U59_V2_1_pct": pc(p.get("U59_V2_1", K.U59_V2_1_def)),
        "t_59_V2_1": K.t_59_1_def,
        "U59_V2_2": p.get("U59_V2_2", K.U59_V2_2_def),
        "U59_V2_2_pct": pc(p.get("U59_V2_2", K.U59_V2_2_def)),
        "t_59_V2_2": K.t_59_2_def,
        "grund": ("" if vt else
                  "Die Spannungsunsymmetrie (Gegensystem-Ueberspannung V2) benoetigt einen "
                  "Spannungswandler. Die stromseitige Phasenfolgepruefung (|I| > 0,5 IN) bleibt "
                  "auch ohne VT wirksam."),
    }




def bemessung_engineering(g: dict, p: dict, umz: dict, b48: dict) -> dict:
    """
    Verifiziert die motorseitige Stufenauslegung:
      - 50-2-Fenster:  1,6 x I_Anlauf < 50-2 < Ik,2pol,min   (7SJ66 Hdb. 2.2)
      - 51 (Reserve):  > k_S x I_max_Last, mit Empfindlichkeit Ik,min / 51 >= gamma
      - 48-Anlauf:     t_Anlauf < t_LR_zul   und   t_Anlauf < STARTUP TIME < t_LR_zul
      - 1107 I MOTOR START zwischen Dauerlast und Anlaufstrom
    KEIN Ersatz fuer eine Kurzschlussberechnung nach DIN EN 60909-0;
    Ik,2pol,min und Ik,min werden als Eingabe erwartet.
    """
    INp    = g["IN_prim"]
    I_max  = g["I_max_prim"]
    I_Anl  = g["I_Anlauf_prim"]
    Ik2p   = p.get("Ik_2pol_min_kA", 0.0) * 1000.0   # kleinster 2-pol. Fehlerstrom
    Ik_min_in = p.get("Ik_min_kA", 0.0) * 1000.0
    k_S    = p.get("k_S_51", K.k_S_51)
    gamma  = p.get("gamma",  K.gamma_Ikmin)

    # 50-2 Hochstromfenster (motorseitige Auslegungsregel)
    f502_untere = K.f_50_2_Anlauf_Sicherheit * I_Anl     # 1,6 x I_Anlauf
    f502_obere  = Ik2p                                    # Ik,2pol,min
    f502_gewaehlt = umz["f_50_2"] * INp
    fenster_vorhanden = bool(f502_obere and f502_untere < f502_obere)
    if not f502_obere:
        hh_status = "Fehlt"
    elif not fenster_vorhanden:
        hh_status = "Prüfen!"   # leeres Fenster: 1,6*IAnlauf >= Ik2pol,min
    elif f502_untere <= f502_gewaehlt <= f502_obere:
        hh_status = "OK"
    else:
        hh_status = "Prüfen!"

    # Rueckrechnung Primaerstrom -> Reglergroesse A sek. (fuer konkrete Stellanweisungen)
    kCT  = g["kCT"]
    _sek = lambda A: (A / kCT) if kCT else 0.0

    if hh_status == "Prüfen!" and not fenster_vorhanden:
        korr_hh = (f"Kein gueltiges 50-2-Fenster: 1,6·I_Anlauf ({f502_untere:.0f} A) liegt "
                   f"ueber Ik,2pol,min ({f502_obere:.0f} A). Eine unverzoegerte Hochstromstufe "
                   f"kann Anlauf und Kurzschluss nicht trennen — verzoegerte 50-2 oder "
                   f"Motordifferentialschutz (87M) erforderlich.")
    elif hh_status == "Prüfen!" and f502_gewaehlt < f502_untere:
        korr_hh = (f"Regler '50-2 I>> [A sek.]' von {_sek(f502_gewaehlt):.3f} auf mindestens "
                   f"{_sek(f502_untere):.3f} A sek. ERHOEHEN (= {f502_untere:.0f} A prim., "
                   f"das 1,6-fache des Anlaufstroms). Aktuell loest 50-2 bei {f502_gewaehlt:.0f} A prim. "
                   f"schon im Anlauf aus.")
    elif hh_status == "Prüfen!":
        korr_hh = (f"Regler '50-2 I>> [A sek.]' von {_sek(f502_gewaehlt):.3f} auf hoechstens "
                   f"{_sek(f502_obere):.3f} A sek. VERRINGERN (= {f502_obere:.0f} A prim., "
                   f"unter Ik,2pol,min). Aktuell liegt 50-2 bei {f502_gewaehlt:.0f} A prim. oberhalb "
                   f"des kleinsten Fehlerstroms und spricht nicht sicher an.")
    else:
        korr_hh = ""

    # 51 Reservestufe ueber Maximallast
    I51_emp      = k_S * I_max
    I51_gewaehlt = umz["f_51"] * INp
    I51_status   = "OK" if (I51_emp and I51_gewaehlt >= I51_emp * 0.999) else ("Prüfen!" if I51_emp else "Fehlt")
    korr_51 = (f"Regler '51 Ip (AMZ) [A sek.]' von {_sek(I51_gewaehlt):.3f} auf mindestens "
               f"{_sek(I51_emp):.3f} A sek. ERHOEHEN (= {I51_emp:.0f} A prim. = {k_S:g}·I_max). "
               f"Aktuell regt 51 schon bei {I51_gewaehlt:.0f} A prim. an und koennte durch Betriebslast "
               f"ausloesen." if I51_status == "Prüfen!" else "")

    # Empfindlichkeit Ik,min / 51
    if Ik_min_in > 0:
        I_k_min = Ik_min_in
        I_k_min_quelle = "Eingabe Ik,min (DIN EN 60909-0)"
    elif Ik2p > 0:
        I_k_min = Ik2p
        I_k_min_quelle = "ersatzweise Ik,2pol,min"
    else:
        I_k_min = 0.0
        I_k_min_quelle = "fehlt"
    empfind = I_k_min / I51_gewaehlt if I51_gewaehlt else 0.0
    empfind_status = "OK" if (empfind and empfind >= gamma) else ("Prüfen!" if I_k_min else "Fehlt")
    _f51_max_sek = (I_k_min / (gamma * kCT)) if (gamma and kCT) else 0.0
    korr_emp = (f"Regler '51 Ip (AMZ) [A sek.]' von {_sek(I51_gewaehlt):.3f} auf hoechstens "
                f"{_f51_max_sek:.3f} A sek. VERRINGERN (oder Kennlinie/TIME DIAL anpassen), damit "
                f"Ik,min/51 >= {gamma:g} erreicht wird (aktuell {empfind:.2f})."
                if empfind_status == "Prüfen!" else "")

    # 48-Anlauf: t_Anlauf < t_LR_zul (Motor kann thermisch anlaufen)
    t_Anl  = b48["t_Anlauf"]
    t_LR   = b48["t_LR_zul"]
    t_set  = b48["Startup_Time"]
    anlauf_moeglich = bool(t_LR and t_Anl < t_LR)
    if not t_LR:
        anlauf_status = "Fehlt"
    elif not anlauf_moeglich:
        anlauf_status = "Prüfen!"   # Anlaufzeit >= zul. Blockierzeit
    elif t_Anl < t_set < t_LR:
        anlauf_status = "OK"
    else:
        anlauf_status = "Hinweis"   # Anlauf moeglich, aber STARTUP TIME nicht im Korridor
    if anlauf_status == "Prüfen!":
        korr_anl = (f"Anlaufzeit ({t_Anl:.1f} s) >= zul. Blockierzeit ({t_LR:.1f} s): Der Motor "
                    f"kann thermisch nicht sicher hochlaufen. Lastmoment/Tragheitsmoment pruefen "
                    f"oder Motor groesser auslegen.")
    elif anlauf_status == "Hinweis":
        korr_anl = (f"Regler '48 STARTUP TIME [s]' von {t_set:.1f} auf einen Wert zwischen "
                    f"{t_Anl:.1f} s und {t_LR:.1f} s setzen (knapp ueber der realen Anlaufzeit, "
                    f"unter der zul. Blockierzeit). Empfehlung etwa {min(t_Anl*1.2, (t_Anl+t_LR)/2):.1f} s.")
    else:
        korr_anl = ""

    # 1107 I MOTOR START zwischen Dauerlast und Anlaufstrom (sek. Vergleich)
    I_ms   = b48["I_Motor_Start_sek"]
    I_ms_u = K.I_MotStart_unten * g["I_max_sek"]   # > 1,2 x I_max (sek.)
    I_ms_o = K.I_MotStart_oben  * g["I_Anlauf_sek"] # < 0,9 x I_Anlauf (sek.)
    if not g["I_Anlauf_sek"]:
        ms_status = "Fehlt"
    elif I_ms_u <= I_ms <= I_ms_o:
        ms_status = "OK"
    else:
        ms_status = "Prüfen!"
    if ms_status == "Prüfen!":
        _ms_ziel = (I_ms_u + I_ms_o) / 2.0
        _ms_richtung = "ERHOEHEN" if I_ms < I_ms_u else "VERRINGERN"
        korr_ms = (f"Regler '48 I MOTOR START [A sek.]' von {I_ms:.3f} auf einen Wert zwischen "
                   f"{I_ms_u:.3f} und {I_ms_o:.3f} A sek. {_ms_richtung} (ueber dem max. "
                   f"Betriebsstrom, sicher unter dem Anlaufstrom). Empfehlung etwa {_ms_ziel:.3f} A sek.")
    else:
        korr_ms = ""

    return {
        "I_max_Last_prim":  round(I_max, 1),
        "I_Anlauf_prim":    round(I_Anl, 1),
        "f502_untere_prim": round(f502_untere, 1),
        "f502_obere_prim":  round(f502_obere, 1),
        "f502_gewaehlt_prim": round(f502_gewaehlt, 1),
        "fenster_vorhanden": fenster_vorhanden,
        "hh_status":        hh_status,
        "korr_hh":          korr_hh,
        "I51_emp_prim":     round(I51_emp, 1),
        "I51_gewaehlt_prim":round(I51_gewaehlt, 1),
        "I51_status":       I51_status,
        "korr_51":          korr_51,
        "k_S":              round(k_S, 2),
        "I_k_min_prim":     round(I_k_min, 1),
        "I_k_min_quelle":   I_k_min_quelle,
        "empfind":          round(empfind, 2),
        "gamma":            gamma,
        "empfind_status":   empfind_status,
        "korr_emp":         korr_emp,
        "t_Anlauf":         t_Anl,
        "t_LR_zul":         t_LR,
        "Startup_Time":     t_set,
        "anlauf_status":    anlauf_status,
        "korr_anl":         korr_anl,
        "I_ms_sek":         round(I_ms, 3),
        "I_ms_unten_sek":   round(I_ms_u, 3),
        "I_ms_oben_sek":    round(I_ms_o, 3),
        "ms_status":        ms_status,
        "korr_ms":          korr_ms,
    }


# ── Plausibilitaetspruefung (Ampel) ─────────────────────────────────────────

def plausibilitaet(g: dict, p: dict, b49: dict, b46: dict, beng: dict,
                   b50N: dict, f2759: dict, f47: dict) -> list:
    checks = []

    def add(name, bezug, ergebnis, status, hinweis, korrektur=""):
        checks.append({"pruefung": name, "bezug": bezug, "ergebnis": ergebnis,
                       "status": status, "hinweis": hinweis,
                       "korrektur": korrektur if status not in ("OK",) else ""})

    # Pn / IN vorhanden
    inp_ok = g["IN_prim"] > 0
    add("Motornennstrom IN bestimmbar", "Pn/cosφ/η oder IN direkt",
        f"{g['IN_prim']:.1f} A ({g['in_quelle']})" if inp_ok else "fehlt",
        "OK" if inp_ok else "Fehlt",
        "IN = Pn / (√3·UN·cosφ·η) oder Direkteingabe — Bezug aller Motorfunktionen.",
        "Pn, UN, cosφ, η ausfuellen oder IN direkt eingeben.")

    add("Nennspannung UN vorhanden", "UN > 0",
        f"{p['UN_kV']} kV" if p.get("UN_kV", 0) > 0 else "fehlt",
        "OK" if p.get("UN_kV", 0) > 0 else "Fehlt",
        "Bemessungsspannung fuer IN-Berechnung erforderlich.",
        "Feld 'UN' ausfuellen (> 0 kV).")

    ct_ok = p.get("CT_Prim", 0) > 0 and p.get("CT_Sek", 0) > 0
    add("Stromwandler vollstaendig", "CT prim/sek > 0",
        "vollst." if ct_ok else "fehlt", "OK" if ct_ok else "Fehlt",
        "Ein Wandlersatz im Motorabgang (kein Differentialschutz im 7SJ66-Basisumfang).",
        "CT prim. [A] und sek. [1/5 A] eingeben.")

    # STW-Anpassung
    ian = g["I_an"]
    stt = status_bereich(ian, K.Anpass_min, K.Anpass_max) if ian else "Fehlt"
    if ian and ian > K.Anpass_max:
        korr = f"Anpassfaktor {ian:.2f} > {K.Anpass_max}: CT prim. verkleinern."
    elif ian and ian < K.Anpass_min:
        korr = f"Anpassfaktor {ian:.2f} < {K.Anpass_min}: CT prim. vergroessern."
    else:
        korr = "CT pruefen."
    add(f"STW-Anpassung in [{K.Anpass_min} ... {K.Anpass_max}]", "I_an = CT_sek / IN_sek",
        f"{ian:.3f}" if ian else "-", stt,
        "Anpassfaktor 0,5-2,0 fuer korrekte sekundaere Stromauswertung.", korr)

    # Anlaufstromverhaeltnis plausibel
    iav = g["I_Anlauf_Verh"]
    iav_st = status_bereich(iav, K.I_Anlauf_min, K.I_Anlauf_max)
    add("Anlaufstromverhaeltnis I_A/IN plausibel [4,0 ... 8,5]", "I_A/IN",
        f"{iav:.1f}", iav_st,
        "Asynchronmaschinen MS typ. 5 ... 7 x IN. Bestimmt 48/66/50-2.",
        f"I_A/IN = {iav:.1f} ausserhalb [4,0 ... 8,5]: Datenblattwert pruefen.")

    # k-Faktor 49
    k = b49["k_Faktor"]
    add("k-Faktor (49) im Bereich [1,0 ... 1,2]", "k = I_max/IN", f"{k:.2f}", b49["k_status"],
        "Dauer-Ueberlastbarkeit der Maschine (7SJ66 Hdb. 2.11). Motor typ. ~1,1.",
        f"k-Faktor {k:.2f} ausserhalb [1,0 ... 1,2]: Regler '49 k-Faktor' pruefen.")

    # tau-Einheit Hinweis (haeufige Fehlerquelle)
    add("Zeitkonstante tau (49) in MINUTEN eingegeben", "Adr.4203 Einheit",
        f"{b49['tau_min']:.0f} min (= {b49['tau_s']:.0f} s)", "OK",
        "WICHTIG: 7SJ66 erwartet tau in Minuten (wie 7UT613) — NICHT in Sekunden wie 7UM62.")

    # I-Warn <= k*IN
    iw_ok = b49["I_Warn_sek"] <= b49["I_max_zul_sek"] * 1.001
    add("Stromwarnstufe I ALARM <= k x IN_sek", "I ALARM <= I_max_zul",
        f"{b49['I_Warn_sek']:.3f} / {b49['I_max_zul_sek']:.3f} A",
        "OK" if iw_ok else "Hinweis",
        "I ALARM soll gleich oder unter dem dauernd zul. Strom liegen (7SJ66 Hdb. 2.11).",
        "I-ALARM-Stufe (Adr.4205) absenken (<= k x IN_sek).")

    # 46 I2-dauer plausibel
    add("46-1 dauernd zul. I2 plausibel [5 ... 15 %]", "I2 dauer", f"{b46['I2_dauer_faktor']*100:.0f} %",
        b46["I2d_status"],
        "Asynchronmaschinen nach IEC 60034-1 typ. ~11 % (7SJ66 Hdb. 2.7).",
        f"I2 dauer = {b46['I2_dauer_faktor']*100:.0f}% ausserhalb [5 ... 15 %]: Datenblatt/IEC 60034-1 pruefen.")

    # 50-2 Fenster
    add("50-2 im Fenster 1,6·I_Anlauf < 50-2 < Ik,2pol,min", "Hochstromstufe",
        f"{beng['f502_gewaehlt_prim']:.0f} A in [{beng['f502_untere_prim']:.0f} ... "
        f"{beng['f502_obere_prim']:.0f} A]" if beng['f502_obere_prim'] else "Ik,2pol,min fehlt",
        beng["hh_status"],
        "Motorseitige Auslegung: oberhalb des 1,6-fachen Anlaufstroms, unterhalb des "
        "kleinsten 2-poligen Fehlerstroms; unverzoegert (7SJ66 Hdb. 2.2).",
        beng["korr_hh"])

    # 51 ueber Maximallast
    add("51 liegt oberhalb der Maximallast", "51 >= k_S · I_max",
        f"{beng['I51_gewaehlt_prim']:.0f} / {beng['I51_emp_prim']:.0f} A", beng["I51_status"],
        "Anregung durch Betriebslast muss ausgeschlossen sein (7SJ66 Hdb. 2.2).",
        beng["korr_51"])

    # Empfindlichkeit 51
    add("Empfindlichkeit Ik,min / 51 >= gamma", f"gamma = {beng['gamma']} (Ik,min: {beng['I_k_min_quelle']})",
        f"{beng['empfind']:.2f}" if beng['empfind'] else "-", beng["empfind_status"],
        "Minimaler Fehlerstrom muss die 51-Stufe sicher anregen.",
        beng["korr_emp"])

    # 48 Anlauf moeglich
    add("Anlauf thermisch moeglich (t_Anlauf < zul. Blockierzeit)", "48 Anlaufkorridor",
        f"t_Anlauf={beng['t_Anlauf']:.1f} s; STARTUP TIME={beng['Startup_Time']:.1f} s; "
        f"t_LR_zul={beng['t_LR_zul']:.1f} s", beng["anlauf_status"],
        "STARTUP TIME knapp ueber der realen Anlaufzeit, unter der zul. Blockierzeit "
        "(7SJ66 Hdb. 2.8).",
        beng["korr_anl"])

    # 1107 I MOTOR START Position
    add("I MOTOR START zwischen Last- und Anlaufstrom", "Adr.1107",
        f"{beng['I_ms_sek']:.3f} A in [{beng['I_ms_unten_sek']:.3f} ... {beng['I_ms_oben_sek']:.3f} A]",
        beng["ms_status"],
        "Anlauf-Erkennung muss unter dem Anlaufstrom und ueber dem max. Betriebsstrom liegen "
        "(friert das thermische Abbild waehrend des Anlaufs ein; 7SJ66 Hdb. 2.1.6/2.8).",
        beng["korr_ms"])

    # ── Erdfehlerschutz 50N/51N (Sternpunktbehandlung-abhaengig) ──────────────
    if b50N["niederohmig"]:
        n2, n1 = b50N["f_50N2_sek"], b50N["f_50N1_sek"]
        ord_ok = n2 >= n1 > 0
        add("50N-Stufung 50N-2 >= 50N-1 > 0", "Erdstrom-Hochstrom > Reserve",
            f"50N-2={n2:.3f} / 50N-1={n1:.3f} A sek.", "OK" if ord_ok else "Prüfen!",
            "Niederohmig geerdetes Netz: Stromkriterium 50N/51N mit gestaffelten Stufen "
            "(7SJ66 Hdb. 2.2).",
            f"Regler '50N-2 I_E>> [A sek.]' (Adr.1302, akt. {n2:.3f}) auf einen Wert >= "
            f"'50N-1 I_E>' (Adr.1304, akt. {n1:.3f}) ERHOEHEN; beide > 0 A.")
    else:
        add("Erdschlusserfassung passend zur Sternpunktbehandlung", b50N["stp"],
            b50N["modus"], "Hinweis",
            "Isoliertes/kompensiertes Netz: das reine Stromkriterium 50N/51N ist unempfindlich. "
            "Empfindliche, gerichtete Stufe 50Ns/51Ns/67Ns ueber U0 (Adr.3109) und INs verwenden.",
            "Empfindliche Erdschlussstufe (Adr.3101 ON) mit U0-Schwelle (Adr.3109) und "
            "Richtung 67Ns (Adr.3115) parametrieren; 50N/51N nur als grober Backup.")

    # ── 27/59 Spannungsschutz (nur mit VT) ────────────────────────────────────
    if f2759["aktiv"]:
        # 59-2 muss oberhalb 59-1 liegen, 27-1 oberhalb 27-2 (Stufung)
        ov_ok = f2759["U59_2"] >= f2759["U59_1"]
        add("59-Stufung 59-2 >= 59-1", "Ueberspannung-Schnellstufe ueber Warnstufe",
            f"59-2={f2759['U59_2']:.0f} V >= 59-1={f2759['U59_1']:.0f} V",
            "OK" if ov_ok else "Prüfen!",
            "Schnellstufe 59-2 (Adr.5005) muss bei hoeherer Spannung ansprechen als die "
            "Warnstufe 59-1 (Adr.5002).",
            f"Regler '59-2 U>> [V sek.]' (Adr.5005) von {f2759['U59_2']:.0f} V auf mindestens "
            f"59-1 ({f2759['U59_1']:.0f} V) ERHOEHEN.")
        uv_ok = f2759["U27_1"] >= f2759["U27_2"]
        add("27-Stufung 27-1 >= 27-2", "Unterspannung oberes Element ueber unterem",
            f"27-1={f2759['U27_1']:.0f} V >= 27-2={f2759['U27_2']:.0f} V",
            "OK" if uv_ok else "Prüfen!",
            "Oberes Element 27-1 (Warnstufe, laenger verzoegert) liegt ueber dem unteren "
            "Element 27-2 (Aus, kurz verzoegert) (7SJ66 Hdb. 2.6).",
            f"Regler '27-1 U< (Warnstufe) [V sek.]' (Adr.5102) von {f2759['U27_1']:.0f} V auf "
            f"mindestens 27-2 ({f2759['U27_2']:.0f} V) ERHOEHEN.")
        # kein Ueberlappen: hoechste 27-Schwelle unter niedrigster 59-Schwelle
        gap_ok = f2759["U27_1"] < f2759["U59_1"]
        add("Kein Ueberlappen 27 / 59", "27-1 < 59-1",
            f"27-1={f2759['U27_1']:.0f} V < 59-1={f2759['U59_1']:.0f} V",
            "OK" if gap_ok else "Prüfen!",
            "Unter- und Ueberspannungsbereich duerfen sich nicht ueberschneiden.",
            f"Regler '27-1 U< (Warnstufe) [V sek.]' (akt. {f2759['U27_1']:.0f} V) unter "
            f"'59-1 U>' (akt. {f2759['U59_1']:.0f} V) bringen: 27-1 SENKEN oder 59-1 ANHEBEN, "
            f"bis 27-1 < 59-1.")
        # 27 plausibler Bereich
        u27_ok = K.U27_min_pct <= f2759["U27_1_pct"] <= K.U27_max_pct
        add(f"27-1 im Bereich [{K.U27_min_pct:.0f} ... {K.U27_max_pct:.0f} %] UnS", "27-1 (% UnS)",
            f"{f2759['U27_1_pct']:.0f} %", "OK" if u27_ok else "Hinweis",
            "Motoren werden typ. bei 70 ... 80 % UN abgeworfen (Kippschutz, Wiederanlaufstoss).",
            f"27-1 (Adr.5102) in [{K.U27_min_pct:.0f} ... {K.U27_max_pct:.0f} %] UnS legen.")
        # 59 plausibler Bereich
        u59_ok = K.U59_min_pct <= f2759["U59_2_pct"] <= K.U59_max_pct
        add(f"59-2 im Bereich [{K.U59_min_pct:.0f} ... {K.U59_max_pct:.0f} %] UnS", "59-2 (% UnS)",
            f"{f2759['U59_2_pct']:.0f} %", "OK" if u59_ok else "Hinweis",
            "Ueberspannungs-Schnellstufe typ. ~130 % UN (7SJ66 Hdb. 2.6).",
            f"59-2 (Adr.5005) in [{K.U59_min_pct:.0f} ... {K.U59_max_pct:.0f} %] UnS legen.")
    # Ohne Spannungswandler ist 27/59/47-Spannungsschutz schlicht nicht projektiert;
    # das ist kein Maengel und wird daher NICHT als Hinweis/Warnung gemeldet.

    # ── 47 Phasenfolge ────────────────────────────────────────────────────────
    add("Erwartete Phasenfolge (47) festgelegt", "Adr.209",
        f47["phase_seq"], "OK",
        "Drehfeldrichtung definiert; Abweichung loest 'Fail Ph. Seq.' aus (Schutz vor "
        "Drehrichtungsumkehr). Pruefung ab |U| > 40 V bzw. |I| > 0,5 IN (7SJ66 Hdb. 2.12).")

    return checks

def reserveschutz(g: dict, umz: dict, b49: dict, b46: dict, b50N: dict, f2759: dict) -> list:
    rows = [
        {"funktion": "Hochstromstufe 50-2 (Adr.1201)", "ziel": "Motorabgang",
         "I_sek": f"{umz['I_50_2_sek']:.4f}", "t": f"{umz['t_50_2']:.2f}",
         "adresse": "50-2 1202; T 1203"},
        {"funktion": "UMZ 50-1 (Adr.1201)", "ziel": "Motorabgang",
         "I_sek": f"{umz['I_50_1_sek']:.4f}", "t": f"{umz['t_50_1']:.2f}",
         "adresse": "50-1 1204; T 1205"},
        {"funktion": "AMZ 51 (Adr.1201)", "ziel": "Motorabgang",
         "I_sek": f"{umz['I_51_sek']:.4f}", "t": f"{umz['T_51']:.2f}",
         "adresse": "51 1207; TD 1208; Kennl. 1211"},
        {"funktion": "Schieflast 46 (Adr.4001)", "ziel": "Motor",
         "I_sek": f"{b46['I2_dauer_sek']:.4f}", "t": f"{b46['t_46_1']:.2f}",
         "adresse": "46-1 4002; T 4003; 46-2 4004; T 4005"},
        {"funktion": "Ueberlast 49 (Adr.4201)", "ziel": "Motor",
         "I_sek": f"{b49['I_max_zul_sek']:.4f}", "t": f"{b49['tau_min']:.0f} min",
         "adresse": "k 4202; τ 4203 (MINUTEN!); Θ 4204; I-Alarm 4205"},
    ]
    if b50N["niederohmig"]:
        rows.append(
            {"funktion": "Erdueberstrom 50N/51N (Adr.1301)", "ziel": "Motorabgang (Erde)",
             "I_sek": f"{b50N['f_50N1_sek']:.4f}", "t": f"{b50N['t_50N1']:.2f}",
             "adresse": "50N-2 1302; 50N-1 1304; 51N 1307; T 1303/1305/1308"})
    else:
        rows.append(
            {"funktion": "Empfindl. Erdschluss 50Ns/67Ns (Adr.3101)", "ziel": "Motorabgang (Erde)",
             "I_sek": f"{b50N['f_50Ns1_sek']:.4f}", "t": f"{b50N['t_50Ns2']:.2f}",
             "adresse": "VN 3109; 50Ns-2 3113; 50Ns-1 3117; 67Ns 3115"})
    if f2759["aktiv"]:
        rows.append(
            {"funktion": "Unterspannung 27 (Adr.5101)", "ziel": "Sammelschiene/Klemmen",
             "I_sek": f"{f2759['U27_2']:.0f} V", "t": f"{f2759['t_27_2']:.2f}",
             "adresse": "27-1 5102; T 5106; 27-2 5110; T 5112"})
        rows.append(
            {"funktion": "Ueberspannung 59 (Adr.5001)", "ziel": "Sammelschiene/Klemmen",
             "I_sek": f"{f2759['U59_2']:.0f} V", "t": f"{f2759['t_59_2']:.2f}",
             "adresse": "59-1 5002; T 5004; 59-2 5005; T 5007"})
    return rows


# ── Geraete-/Architektur-Empfehlung ──────────────────────────────────────────

def geraeteempfehlung(p: dict) -> dict:
    stp     = p.get("stp_Netz", "Isoliert")
    antrieb = p.get("antrieb", K.ANTRIEBSART_OPTIONEN[0])
    kuehl   = p.get("kuehlung", K.KUEHLUNG_OPTIONEN[0])

    if stp == "Isoliert":
        erd = ("Isoliertes Netz: Erdschluss erzeugt keinen nennenswerten Fehlerstrom. "
               "Empfindliche, gerichtete Erdschlusserfassung 67Ns ueber Verlagerungs"
               "spannung U0 und kapazitiven Erdstrom (sin-φ-Auswertung). Der Phasen"
               "ueberstromschutz 50/51 erfasst nur mehrpolige Fehler.")
    elif "Kompensiert" in stp:
        erd = ("Kompensiertes Netz (Petersen-Spule): Erdschluss ueber wattmetrische bzw. "
               "cos-φ-Auswertung des Wirkreststroms (67Ns), da der induktive Spulenstrom "
               "den kapazitiven Erdstrom weitgehend kompensiert.")
    else:
        erd = ("Niederohmig geerdetes Netz: definierter Erdfehlerstrom — Erdschluss ueber "
               "Stromkriterium 50N/51N direkt erfassbar.")

    if "Pumpe" in antrieb:
        ant = ("Pumpe/Luefter (quadratisches Lastmoment): vergleichsweise kurzer Anlauf. "
               "Unterstrom 37-1< sinnvoll als Trockenlauf-/Lastverlusterkennung.")
    elif "Kompressor" in antrieb:
        ant = ("Kompressor/Muehle (konstantes Lastmoment): hoeheres Anlaufmoment, "
               "Load-Jam-Schutz (51M) gegen ploetzliche Laeuferblockierung relevant.")
    else:
        ant = ("Schweranlauf (hohes Traegheitsmoment): lange Anlaufzeit nahe der zul. "
               "Blockierzeit — Anlaufueberwachung 48 und Wiedereinschaltsperre 66 sorgfaeltig "
               "parametrieren; ggf. Drehzahlwaechter (Binaereingang) ergaenzen.")

    if "Fremd" in kuehl:
        kue = ("Fremdbelueftung: Kuehlung lastunabhaengig — Kτ bei Stillstand nahe 1,0 "
               "(Adr.4207A), thermisches Abbild gilt naeherungsweise auch im Stillstand.")
    else:
        kue = ("Eigenbelueftung: im Stillstand keine Luefterkuehlung — Zeitkonstante mit "
               "Kτ > 1 verlaengern (Adr.4207A/4308), damit die Abkuehlung realistisch "
               "nachgebildet wird.")

    return {"erdschluss": erd, "antrieb": ant, "kuehlung": kue}


# ── Master-Funktion ───────────────────────────────────────────────────────────

def berechne_alle(p: dict) -> dict:
    g    = grundgroessen(p)
    b49  = schutz_49(g, p)
    b48  = schutz_48(g, p)
    b66  = schutz_66(g, p)
    b51M = schutz_51M(g, p)
    b46  = schutz_46(g, p)
    umz  = schutz_5051(g, p)
    b37  = schutz_37(g, p)
    b50N = schutz_50N51N(g, p)
    f2759= schutz_2759(g, p)
    f47  = schutz_47(g, p)
    beng = bemessung_engineering(g, p, umz, b48)
    plaus= plausibilitaet(g, p, b49, b46, beng, b50N, f2759, f47)
    rsv  = reserveschutz(g, umz, b49, b46, b50N, f2759)
    geh  = geraeteempfehlung(p)

    return {
        "grund": g,
        "49": b49,
        "48": b48,
        "66": b66,
        "51M": b51M,
        "46": b46,
        "5051": umz,
        "37": b37,
        "50N51N": b50N,
        "2759": f2759,
        "47": f47,
        "bemessung": beng,
        "plausibilitaet": plaus,
        "reserveschutz": rsv,
        "empfehlung": geh,
    }
