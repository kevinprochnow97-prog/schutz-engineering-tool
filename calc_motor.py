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


# ── Bemessungs-Engineering (Kurzschluss-/Anlaufverifikation) ────────────────

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

    if hh_status == "Prüfen!" and not fenster_vorhanden:
        korr_hh = (f"Kein gueltiges 50-2-Fenster: 1,6·I_Anlauf ({f502_untere:.0f} A) liegt "
                   f"ueber Ik,2pol,min ({f502_obere:.0f} A). Eine unverzoegerte Hochstromstufe "
                   f"kann Anlauf und Kurzschluss nicht trennen — verzoegerte 50-2 oder "
                   f"Motordifferentialschutz (87M) erforderlich.")
    elif hh_status == "Prüfen!":
        korr_hh = (f"50-2 ({f502_gewaehlt:.0f} A) ausserhalb des Fensters "
                   f"[{f502_untere:.0f} ... {f502_obere:.0f} A]. 50-2-Faktor anpassen "
                   f"(oberhalb 1,6·I_Anlauf, unterhalb Ik,2pol,min).")
    else:
        korr_hh = ""

    # 51 Reservestufe ueber Maximallast
    I51_emp      = k_S * I_max
    I51_gewaehlt = umz["f_51"] * INp
    I51_status   = "OK" if (I51_emp and I51_gewaehlt >= I51_emp * 0.999) else ("Prüfen!" if I51_emp else "Fehlt")
    korr_51 = (f"51-Anregewert auf >= {k_S:g}·I_max ({I51_emp:.0f} A) anheben "
               f"(aktuell {I51_gewaehlt:.0f} A)." if I51_status == "Prüfen!" else "")

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
    korr_emp = ("Empfindlichkeit zu gering: 51-Anregewert senken oder Kennlinie/TD anpassen, "
                f"bis Ik,min/51 >= {gamma:g}." if empfind_status == "Prüfen!" else "")

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
        korr_anl = (f"STARTUP TIME ({t_set:.1f} s) ausserhalb des Korridors "
                    f"({t_Anl:.1f} s ... {t_LR:.1f} s). Knapp oberhalb der realen Anlaufzeit "
                    f"und unterhalb der zul. Blockierzeit einstellen.")
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
    korr_ms = (f"I MOTOR START ({I_ms:.3f} A) zwischen {I_ms_u:.3f} A und {I_ms_o:.3f} A (sek.) "
               f"legen — ueber max. Betriebsstrom, sicher unter dem Anlaufstrom."
               if ms_status == "Prüfen!" else "")

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

def plausibilitaet(g: dict, p: dict, b49: dict, b46: dict, beng: dict) -> list:
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

    return checks


# ── Reserveschutz-Zuordnung / DIGSI-Adressen ─────────────────────────────────

def reserveschutz(g: dict, umz: dict, b49: dict, b46: dict) -> list:
    return [
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
    beng = bemessung_engineering(g, p, umz, b48)
    plaus= plausibilitaet(g, p, b49, b46, beng)
    rsv  = reserveschutz(g, umz, b49, b46)
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
        "bemessung": beng,
        "plausibilitaet": plaus,
        "reserveschutz": rsv,
        "empfehlung": geh,
    }
