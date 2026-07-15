"""
calc_leitung.py — Berechnungslogik Leitungsschutz
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reine Python-Funktionen (kein Streamlit) -> isoliert testbar.
Methodik nach SIPROTEC 7SA6 (Distanzschutz) und 7SD5 (Leitungsdifferential mit
Distanzschutz). Ausgabe IEC-normiert (Ohm sek./prim., s, %, Grad).

Implementierte Schutzfunktionen (Ausbaustand):
  21   Distanzschutz, Zonen Z1/Z1B/Z2/Z3, Erdimpedanzanpassung (k0 / RE-XE)
       (Adr. 13xx 7SA6 / 16xx 7SD5, Anlagendaten 11xx adressgleich)

Sekundaerer Impedanzbezug:
  Z_sek = Z_prim * k_Z   mit   k_Z = kCT / nVT
        = Z_prim * (CT_prim/CT_sek) / (VT_prim/VT_sek)
"""

import math
import konstanten_leitung as K
from utils import de, deg
from calc_trafo import status_bereich, status_empfehlung  # gemeinsame Ampel-Helfer

SQRT3 = math.sqrt(3)


# ── Berechnete Grundgroessen ─────────────────────────────────────────────────

def grundgroessen(p: dict) -> dict:
    """
    Leitungsimpedanzen, Wandlerverhaeltnisse, Sekundaerbezug.
    Erwartet: UN_kV, L_km, X_Belag, phi_Ltg, IN_Ltg,
              CT_Prim, CT_Sek, VT_Prim_kV, VT_Sek_V
    """
    UN   = p.get("UN_kV", 0.0)
    L    = p.get("L_km", 0.0)
    Xbel = p.get("X_Belag", 0.0)
    phi  = p.get("phi_Ltg", 0.0)

    # Leitungsimpedanz primaer
    X_Ltg = Xbel * L                                  # [Ohm prim.]
    tan_phi = math.tan(math.radians(phi)) if 0 < phi < 90 else 0.0
    R_Ltg = (X_Ltg / tan_phi) if tan_phi else 0.0     # R' = X' / tan(phi)
    Z_Ltg = math.hypot(R_Ltg, X_Ltg)                  # |Z| = sqrt(R^2 + X^2)

    # Wandlerverhaeltnisse
    kCT = p["CT_Prim"] / p["CT_Sek"] if p.get("CT_Sek") else 0.0
    nVT = (p["VT_Prim_kV"] * 1e3) / p["VT_Sek_V"] if p.get("VT_Sek_V") else 0.0
    k_Z = (kCT / nVT) if nVT else 0.0                 # Z_sek / Z_prim

    X_Ltg_sek = X_Ltg * k_Z
    Z_Ltg_sek = Z_Ltg * k_Z

    # Leitungs-Nennstrom (sekundaer) fuer spaetere Reserve-/Ueberlastfunktionen
    IN_Ltg = p.get("IN_Ltg", 0.0)
    IN_Ltg_sek = IN_Ltg / kCT if kCT else 0.0
    I_an = p["CT_Sek"] / IN_Ltg_sek if IN_Ltg_sek else 0.0  # STW-Anpassung

    # Kapazitiver Nennladestrom der Leitung (fuer 87L-Plausibilitaet)
    # IcN = U_phase * 2*pi*f * C_gesamt ; C_gesamt = C-Belag[uF/km] * L[km]
    C_Belag = p.get("C_Belag", K.C_Belag_def)
    C_ges = C_Belag * 1e-6 * L                        # [F]
    U_ph  = (UN * 1e3) / SQRT3                         # [V]
    IcN = U_ph * 2 * math.pi * K.f_netz * C_ges        # [A]

    # Kurzschlussstroeme (DIN EN 60909-0) fuer Konsistenz- und
    # Empfindlichkeitspruefungen des Not-Ueberstromschutzes
    Ik_max_prim = p.get("Ik_max_kA", 0.0) * 1e3
    Ik_min_prim = p.get("Ik_min_kA", 0.0) * 1e3

    return {
        "X_Ltg":      round(X_Ltg, 4),
        "R_Ltg":      round(R_Ltg, 4),
        "Z_Ltg":      round(Z_Ltg, 4),
        "X_Ltg_sek":  round(X_Ltg_sek, 4),
        "Z_Ltg_sek":  round(Z_Ltg_sek, 4),
        "kCT":        round(kCT, 4),
        "nVT":        round(nVT, 4),
        "k_Z":        round(k_Z, 6),
        "IN_Ltg":     round(IN_Ltg, 4),
        "IN_Ltg_sek": round(IN_Ltg_sek, 4),
        "I_an":       round(I_an, 4),
        "IcN":        round(IcN, 4),
        "Ik_max_prim": round(Ik_max_prim, 1),
        "Ik_min_prim": round(Ik_min_prim, 1),
    }


# ── 21 Distanzschutz ─────────────────────────────────────────────────────────

def schutz_21(g: dict, p: dict) -> dict:
    """
    Distanzschutz mit gestaffelten Zonen Z1 / Z1B / Z2 / Z3.
    Reichweiten primaer ueber Faktor x X_Ltg, sekundaer ueber k_Z.
    R-Abschnitte ueber R/X-Faktor, Erd-R-Abschnitt ueber RE/R-Faktor.
    Adressen geraeteabhaengig (7SA6 13xx / 7SD5 16xx).
    """
    dev   = p.get("leitgeraet", K.LEITGERAET_OPTIONEN[0])
    X_Ltg = g["X_Ltg"]
    k_Z   = g["k_Z"]

    def zone(faktor, rx, t, ohne_RE=False):
        Xp = faktor * X_Ltg                  # X primaer [Ohm]
        Xs = Xp * k_Z                         # X sekundaer [Ohm]
        Rp = rx * Xp                          # R primaer
        Rs = rx * Xs                          # R sekundaer
        REp = K.RE_zu_R_def * Rp              # Erd-R primaer
        REs = K.RE_zu_R_def * Rs             # Erd-R sekundaer
        return {
            "faktor": faktor,
            "X_prim": round(Xp, 4),  "X_sek": round(Xs, 4),
            "R_prim": round(Rp, 4),  "R_sek": round(Rs, 4),
            "RE_prim": round(REp, 4), "RE_sek": round(REs, 4),
            "t": t,
        }

    aktiv = p.get("DIS_aktiv", K.DIS_aktiv_def)
    f_Z1  = p.get("f_Z1",  K.f_Z1_def)
    f_Z1B = p.get("f_Z1B", K.f_Z1B_def)
    f_Z2  = p.get("f_Z2",  K.f_Z2_def)
    f_Z3  = p.get("f_Z3",  K.f_Z3_def)

    Z1  = zone(f_Z1,  p.get("RX_Z1",  K.RX_Z1_def),  p.get("t_Z1",  K.t_Z1_def))
    Z1B = zone(f_Z1B, p.get("RX_Z1B", K.RX_Z1B_def), p.get("t_Z1B", K.t_Z1B_def))
    Z2  = zone(f_Z2,  p.get("RX_Z2",  K.RX_Z2_def),  p.get("t_Z2",  K.t_Z2_def))
    Z3  = zone(f_Z3,  p.get("RX_Z3",  K.RX_Z3_def),  p.get("t_Z3",  K.t_Z3_def))

    # ── Reservezonen Z4 / Z5 / Z6 (richtungswaehlbar) ───────────────────────
    def reservezone(name, faktor, rx, t, modus):
        z = zone(faktor, rx, t)
        aktiv_z = modus != "Unwirksam"
        # Richtungsabhaengige X-Adresse: Z5/Z6 mit getrennten +/- Adressen,
        # Z4 mit gemeinsamer Adresse.
        if name == "Z4":
            x_adr = K.ADR_get("X_Z4", dev)
        else:  # Z5 / Z6
            if modus == "Rückwärts":
                x_adr = K.ADR_get(f"X_{name}_RUECK", dev)
            else:
                x_adr = K.ADR_get(f"X_{name}_VOR", dev)
        z.update({
            "modus":  modus,
            "aktiv":  aktiv_z,
            "x_adr":  x_adr,
            "r_adr":  K.ADR_get(f"R_{name}", dev),
            "re_adr": K.ADR_get(f"RE_{name}", dev),
            "t_adr":  K.ADR_get("T4" if name == "Z4" else
                                "T5" if name == "Z5" else "T6", dev),
            "modus_adr": K.ADR_get(f"MODUS_{name}", dev),
        })
        return z

    Z4 = reservezone("Z4", p.get("f_Z4", K.f_Z4_def), p.get("RX_Z4", K.RX_Z4_def),
                     p.get("t_Z4", K.t_Z4_def), p.get("modus_Z4", K.modus_Z4_def))
    Z5 = reservezone("Z5", p.get("f_Z5", K.f_Z5_def), p.get("RX_Z5", K.RX_Z5_def),
                     p.get("t_Z5", K.t_Z5_def), p.get("modus_Z5", K.modus_Z5_def))
    Z6 = reservezone("Z6", p.get("f_Z6", K.f_Z6_def), p.get("RX_Z6", K.RX_Z6_def),
                     p.get("t_Z6", K.t_Z6_def), p.get("modus_Z6", K.modus_Z6_def))

    return {
        "aktiv":      aktiv,
        "leitgeraet": dev,
        "charakt":    p.get("DIS_charakt", K.DIS_CHARAKT_OPTIONEN[0]),
        "anr":        p.get("DIS_anr", K.DIS_ANR_OPTIONEN[0]),
        "alpha_polyg": p.get("alpha_polyg", K.alpha_polyg_def),
        "Z1": Z1, "Z1B": Z1B, "Z2": Z2, "Z3": Z3, "Z4": Z4, "Z5": Z5, "Z6": Z6,
        # Erdimpedanzanpassung
        "erdimp_format": p.get("erdimp_format", K.ERDIMP_FORMAT_OPTIONEN[0]),
        "RE_RL": p.get("RE_RL", K.RE_RL_def),
        "XE_XL": p.get("XE_XL", K.XE_XL_def),
        "K0":    p.get("K0",    K.K0_def),
        "PHI_K0": p.get("PHI_K0", K.PHI_K0_def),
        # Adressen (geraeteabhaengig) — fuer Anzeige / Sollwert-Tabelle
        "adr": {
            "X_Z1":  K.ADR_get("X_Z1", dev),  "R_Z1":  K.ADR_get("R_Z1", dev),
            "RE_Z1": K.ADR_get("RE_Z1", dev), "T1":    K.ADR_get("T1_MEHRPOL", dev),
            "X_Z1B": K.ADR_get("X_Z1B", dev), "R_Z1B": K.ADR_get("R_Z1B", dev),
            "RE_Z1B": K.ADR_get("RE_Z1B", dev), "T1B":  K.ADR_get("T1B_MEHRPOL", dev),
            "X_Z2":  K.ADR_get("X_Z2", dev),  "R_Z2":  K.ADR_get("R_Z2", dev),
            "RE_Z2": K.ADR_get("RE_Z2", dev),  "T2":    K.ADR_get("T2_MEHRPOL", dev),
            "X_Z3":  K.ADR_get("X_Z3", dev),  "R_Z3":  K.ADR_get("R_Z3", dev),
            "RE_Z3": K.ADR_get("RE_Z3", dev),  "T3":    K.ADR_get("T3", dev),
            "PHI_LTG": K.ADR_get("PHI_LTG", dev),
            "RE_RL": K.ADR_get("RE_RL_Z1", dev), "K0": K.ADR_get("K0_Z1", dev),
            "FORMAT": K.ADR_get("FORMAT_ERDIMP", dev),
            "DIS_ANR": K.ADR_get("DIS_ANR", dev), "DIS_CHARAKT": K.ADR_get("DIS_CHARAKT", dev),
        },
    }


# ── 87L Leitungslaengsdifferentialschutz (nur 7SD5) ──────────────────────────

def schutz_87L(g: dict, p: dict) -> dict:
    """
    Leitungslaengsdifferentialschutz mit stabilisierter Stufe I-DIFF> und
    unstabilisierter Hochstromstufe I-DIFF>>. Ansprechwerte als Vielfaches des
    Leitungs-Nennstroms IN_Ltg, zusaetzlich primaer und sekundaer.
    Nur fuer Leitgeraet 7SD5 verfuegbar.
    """
    dev = p.get("leitgeraet", K.LEITGERAET_OPTIONEN[0])
    verfuegbar = (dev == "Leitungsdifferential 7SD5")

    IN  = g["IN_Ltg"]
    kCT = g["kCT"]
    IcN = g["IcN"]

    def stufe(faktor):
        prim = faktor * IN                    # [A primaer]
        sek  = prim / kCT if kCT else 0.0     # [A sekundaer]
        return round(prim, 3), round(sek, 4)

    f_diff   = p.get("i_diff",         K.i_diff_def)
    f_diffhh = p.get("i_diff_hh",      K.i_diff_hh_def)
    f_zusch  = p.get("i_diff_zusch",   K.i_diff_zusch_def)
    f_freig  = p.get("i_freig_diff",   K.i_freig_diff_def)
    f_hhzu   = p.get("i_diff_hh_zusch",K.i_diff_hh_zusch_def)

    diff_prim,  diff_sek  = stufe(f_diff)
    diffhh_prim, diffhh_sek = stufe(f_diffhh)
    zusch_prim, zusch_sek = stufe(f_zusch)

    return {
        "verfuegbar":  verfuegbar,
        "aktiv":       verfuegbar and p.get("DIFF_aktiv", K.DIFF_aktiv_def),
        "i_diff":      f_diff,    "i_diff_prim": diff_prim,   "i_diff_sek": diff_sek,
        "i_diff_hh":   f_diffhh,  "i_diff_hh_prim": diffhh_prim, "i_diff_hh_sek": diffhh_sek,
        "i_diff_zusch": f_zusch,  "i_diff_zusch_prim": zusch_prim,
        "i_freig_diff": f_freig,
        "i_diff_hh_zusch": f_hhzu,
        "t_i_diff":    p.get("t_i_diff", K.t_i_diff_def),
        "ic_komp":     p.get("ic_komp", K.ic_komp_def),
        "icstab_icn":  p.get("icstab_icn", K.icstab_icn_def),
        "anzahl_geraete": p.get("anzahl_geraete", K.anzahl_geraete_def),
        "ws_verbindung": p.get("ws_verbindung", K.ws_verbindung_def),
        "IcN":         round(IcN, 4),
        "i_diff_min":  round(K.icN_faktor_min * IcN, 4),   # 2,5 x IcN [A]
        "adr": {
            "DIFF_SCHUTZ": K.ADR_get("DIFF_SCHUTZ", dev),
            "I_DIFF":      K.ADR_get("I_DIFF", dev),
            "I_DIF_ZUSCH": K.ADR_get("I_DIF_ZUSCH", dev),
            "T_I_DIF":     K.ADR_get("T_I_DIF", dev),
            "I_FREIG_DIFF": K.ADR_get("I_FREIG_DIFF", dev),
            "IC_KOMP":     K.ADR_get("IC_KOMP", dev),
            "ICSTAB_ICN":  K.ADR_get("ICSTAB_ICN", dev),
            "I_DIFF_HH":   K.ADR_get("I_DIFF_HH", dev),
            "I_DIF_HH_ZUSCH": K.ADR_get("I_DIF_HH_ZUSCH", dev),
            "ANZAHL_GERAETE": K.ADR_get("ANZAHL_GERAETE", dev),
            "WS1_EIN":     K.ADR_get("WS1_EIN", dev),
            "WS1_VERB":    K.ADR_get("WS1_VERB", dev),
            "GPS_SYNC":    K.ADR_get("GPS_SYNC", dev),
        },
    }


def plausibilitaet_87L(g: dict, p: dict, d87: dict) -> list:
    """Plausibilitaet des Differentialschutzes (nur 7SD5)."""
    checks = []
    if not d87["verfuegbar"]:
        return checks

    def add(name, bezug, ergebnis, status, hinweis, korrektur=""):
        checks.append({"pruefung": name, "bezug": bezug, "ergebnis": ergebnis,
                       "status": status, "hinweis": hinweis,
                       "korrektur": korrektur if status != "OK" else ""})

    IcN = d87["IcN"]
    i_diff_prim = d87["i_diff_prim"]
    i_min = d87["i_diff_min"]
    ic_komp = d87["ic_komp"]

    # I-DIFF> >= 2,5 x IcN (sofern ohne Ladestromkompensation)
    if ic_komp == "Aus":
        ok = i_diff_prim >= i_min if IcN > 0 else True
        add("I-DIFF> >= 2,5 x IcN (Ladestrom)", "I-DIFF> / IcN",
            f"{de(i_diff_prim, 1)} A vs. {de(i_min, 1)} A", "OK" if ok else "Prüfen!",
            "Ohne Ladestromkompensation muss der Ansprechwert oberhalb des kapazitiven "
            f"Ladestroms liegen (IcN = {de(IcN, 1)} A, Siemens-Empfehlung >= 2,5 x IcN).",
            f"I-DIFF> auf >= {de(i_min, 1)} A anheben oder Ladestromkompensation "
            "(Adr.1221) einschalten.")
    else:
        add("Ladestromkompensation aktiv", "Ic-KOMP",
            "Ein", "OK",
            "Mit Ladestromkompensation kann I-DIFF> empfindlicher eingestellt werden.", "")

    # I-DIFF>> deutlich groesser als I-DIFF>
    hh_ok = d87["i_diff_hh"] > d87["i_diff"]
    add("I-DIFF>> > I-DIFF> (Stufenstaffelung)", "I-DIFF>> / I-DIFF>",
        f"{de(d87['i_diff_hh'], 2)} / {de(d87['i_diff'], 2)} x IN", "OK" if hh_ok else "Prüfen!",
        "Die unstabilisierte Hochstromstufe muss oberhalb der stabilisierten Stufe liegen.",
        "I-DIFF>> größer als I-DIFF> setzen (z.B. 8,0 x IN).")

    # I-DIF>> ZUSCH >= I-DIFF>> (Geraetelogik)
    zu_ok = d87["i_diff_hh_zusch"] >= d87["i_diff_hh"]
    add("I-DIF>> ZUSCH. >= I-DIFF>>", "Zuschaltschwelle",
        f"{de(d87['i_diff_hh_zusch'], 2)} / {de(d87['i_diff_hh'], 2)} x IN",
        "OK" if zu_ok else "Hinweis",
        "Der Zuschaltwert wird vom Gerät automatisch auf I-DIFF>> angehoben, falls kleiner "
        "(7SD5 Hdb. 2.2.1).",
        "I-DIF>> ZUSCH. >= I-DIFF>> einstellen.")

    # Anzahl Geraete / Wirkschnittstelle
    ng = d87["anzahl_geraete"]
    add("Anzahl Geräte = Leitungsenden", "ANZAHL GERAETE",
        f"{ng}", "OK" if ng >= 2 else "Prüfen!",
        "Die Gerätezahl muss mit der Anzahl der Messstellen (Leitungsenden) "
        "übereinstimmen. Eine Wirkschnittstelle je Verbindung ist erforderlich.",
        "ANZAHL GERAETE (Adr.147) an die Zahl der Leitungsenden anpassen.")

    return checks


# ── 67N Gerichteter Erdkurzschlussschutz (beide Geraete) ─────────────────────

def schutz_67N(g: dict, p: dict) -> dict:
    """
    Gerichteter Erdkurzschlussschutz mit drei unabhaengigen Erdstromstufen
    (3I0>>>, 3I0>>, 3I0>), jeweils mit Ansprechwert (x IN_Ltg), Zeit und
    Richtungsmodus. In beiden Geraeten adressgleich (31xx). Nur in geerdeten
    Netzen sinnvoll.
    """
    dev = p.get("leitgeraet", K.LEITGERAET_OPTIONEN[0])
    stp = p.get("sternpunkt_netz", K.STERNPUNKT_NETZ_OPTIONEN[0])
    geerdet = stp in K.NETZ_GEERDET

    IN  = g["IN_Ltg"]
    kCT = g["kCT"]

    def stufe(faktor, t, modus):
        prim = faktor * IN
        sek  = prim / kCT if kCT else 0.0
        return {"faktor": faktor, "i_prim": round(prim, 3), "i_sek": round(sek, 4),
                "t": t, "modus": modus, "aktiv": modus != "Unwirksam"}

    HHH = stufe(p.get("i_3I0HHH", K.i_3I0HHH_def), p.get("t_3I0HHH", K.t_3I0HHH_def),
                p.get("modus_3I0HHH", K.modus_3I0HHH_def))
    HH  = stufe(p.get("i_3I0HH", K.i_3I0HH_def), p.get("t_3I0HH", K.t_3I0HH_def),
                p.get("modus_3I0HH", K.modus_3I0HH_def))
    H   = stufe(p.get("i_3I0H", K.i_3I0H_def), p.get("t_3I0H", K.t_3I0H_def),
                p.get("modus_3I0H", K.modus_3I0H_def))

    return {
        "geerdet":   geerdet,
        "aktiv":     geerdet and p.get("EKS_aktiv", K.EKS_aktiv_def),
        "sternpunkt": stp,
        "3I0HHH": HHH, "3I0HH": HH, "3I0H": H,
        "iph_stab": p.get("i3i0_iph_stab", K.i3i0_iph_stab_def),
        "phi_komp": p.get("phi_komp", K.phi_komp_def),
        "adr": {
            "ERDFEHLER": K.ADR_get("ERDFEHLER", dev),
            "IPH_STAB":  K.ADR_get("I3I0_IPH_STAB", dev),
            "PHI_KOMP":  K.ADR_get("PHI_KOMP", dev),
            "M_HHH": K.ADR_get("MODUS_3I0HHH", dev), "I_HHH": K.ADR_get("I3I0_HHH", dev),
            "T_HHH": K.ADR_get("T_3I0HHH", dev),
            "M_HH":  K.ADR_get("MODUS_3I0HH", dev),  "I_HH":  K.ADR_get("I3I0_HH", dev),
            "T_HH":  K.ADR_get("T_3I0HH", dev),
            "M_H":   K.ADR_get("MODUS_3I0H", dev),   "I_H":   K.ADR_get("I3I0_H", dev),
            "T_H":   K.ADR_get("T_3I0H", dev),
        },
    }


def plausibilitaet_67N(g: dict, p: dict, d67: dict) -> list:
    """Plausibilitaet des gerichteten Erdkurzschlussschutzes (geerdete Netze)."""
    checks = []

    def add(name, bezug, ergebnis, status, hinweis, korrektur=""):
        checks.append({"pruefung": name, "bezug": bezug, "ergebnis": ergebnis,
                       "status": status, "hinweis": hinweis,
                       "korrektur": korrektur if status != "OK" else ""})

    if not d67["geerdet"]:
        add("67N passend zur Sternpunktbehandlung", "Sternpunktbehandlung",
            d67["sternpunkt"], "OK",
            "Isoliertes/kompensiertes Netz erkannt: Der strombasierte gerichtete 67N ist für "
            "geerdete Netze vorgesehen und daher hier nicht wirksam (die Stufen im Abschnitt "
            "„Gerichteter Erdkurzschlussschutz 67N“ werden nur informativ angezeigt). Die "
            "Erdschlusserfassung erfolgt in solchen Netzen über die Verlagerungsspannung U0 "
            "bzw. wattmetrisch auf einem dedizierten Erdschlussgerät (z. B. 7SJ64/zentrale "
            "Erfassung), das nicht in diesem Leitungs-Tab parametriert wird. Es ist hier "
            "nichts einzustellen.")
        return checks

    HHH, HH, H = d67["3I0HHH"], d67["3I0HH"], d67["3I0H"]

    # Stromstaffelung: 3I0>>> > 3I0>> > 3I0>
    strom_ok = HHH["faktor"] > HH["faktor"] > H["faktor"]
    add("Stromstaffelung 3I0>>> > 3I0>> > 3I0>", "Ansprechwerte",
        f"{de(HHH['faktor'], 2)} / {de(HH['faktor'], 2)} / {de(H['faktor'], 2)} x IN",
        "OK" if strom_ok else "Prüfen!",
        "Die höher ansprechenden Stufen müssen höhere Stromschwellen haben.",
        "Ansprechwerte so setzen, dass 3I0>>> > 3I0>> > 3I0>.")

    # Zeitstaffelung: T 3I0>>> < T 3I0>> < T 3I0>
    zeit_ok = HHH["t"] < HH["t"] < H["t"]
    add("Zeitstaffelung T(3I0>>>) < T(3I0>>) < T(3I0>)", "Zeiten",
        f"{de(HHH['t'], 2)} / {de(HH['t'], 2)} / {de(H['t'], 2)} s",
        "OK" if zeit_ok else "Prüfen!",
        "Höher ansprechende Stufen lösen schneller aus (inverse Staffelung).",
        "Zeiten so setzen, dass T(3I0>>>) < T(3I0>>) < T(3I0>).")

    # Mindestens eine Stufe vorwaerts (Leitungsrichtung)
    vor = any(s["modus"] == "Vorwärts" for s in (HHH, HH, H))
    add("Mindestens eine Stufe vorwärts gerichtet", "MODUS 3I0",
        "vorwärts vorhanden" if vor else "keine Vorwärtsstufe",
        "OK" if vor else "Hinweis",
        "Für den Leitungsschutz sollte mindestens eine Stufe in Richtung Leitung "
        "(vorwärts) arbeiten.",
        "MODUS einer Stufe (Adr.3110/3120/3130) auf vorwärts stellen.")

    # Empfindliche Stufe oberhalb betriebsmaessiger Unsymmetrie (>= 0,05 x IN)
    h_ok = H["faktor"] >= 0.05
    add("3I0> oberhalb betriebsmäßiger Unsymmetrie", "3I0> Ansprechwert",
        f"{de(H['faktor'], 2)} x IN", "OK" if h_ok else "Hinweis",
        "Der empfindlichste Ansprechwert muss oberhalb des betriebsmäßigen "
        "Erdstroms (Unsymmetrie) liegen, um Fehlauslösungen zu vermeiden.",
        "3I0> nicht unter ca. 0,05 x IN einstellen.")

    return checks


# ── 85 Signaluebertragungsverfahren Distanzschutz (Teleschutz, beide Geraete) ──

def schutz_85(g: dict, p: dict) -> dict:
    """
    Teleschutz des Distanzschutzes. Beschleunigt die Ausloesung ueber die
    Uebergreifzone Z1B durch Signalaustausch mit der Gegenstelle.
    Verfahren: Mitnahme, Signalvergleich (Freigabe), Blocking, Unblocking.
    In beiden Geraeten adressgleich (21xx).
    """
    dev = p.get("leitgeraet", K.LEITGERAET_OPTIONEN[0])
    verfahren = p.get("signalv", K.signalv_def)
    aktiv = verfahren != "Aus"
    return {
        "aktiv":      aktiv,
        "verfahren":  verfahren,
        "anschluss":  p.get("anschluss", K.anschluss_def),
        "t_sendverl": p.get("t_sendverl", K.t_sendverl_def),
        "tv":         p.get("tv_dis", K.tv_dis_def),
        "t_warte_rueckw": p.get("t_warte_rueckw", K.t_warte_rueckw_def),
        "t_transblock": p.get("t_transblock", K.t_transblock_def),
        "blockierverfahren": verfahren == "Blocking",
        "adr": {
            "SIGNALZUSATZ": K.ADR_get("SIGNALZUSATZ_DIS", dev),
            "ANSCHLUSS":    K.ADR_get("ANSCHLUSS_DIS", dev),
            "T_SENDVERL":   K.ADR_get("T_SENDVERL", dev),
            "TV":           K.ADR_get("TV_DIS", dev),
            "T_WARTE_RUECKW": K.ADR_get("T_WARTE_RUECKW", dev),
            "T_TRANSBLOCK": K.ADR_get("T_TRANSBLOCK", dev),
        },
    }


def plausibilitaet_85(g: dict, p: dict, d85: dict, d21: dict) -> list:
    """Plausibilitaet des Teleschutzes (nur wenn ein Verfahren gewaehlt ist)."""
    checks = []

    def add(name, bezug, ergebnis, status, hinweis, korrektur=""):
        checks.append({"pruefung": name, "bezug": bezug, "ergebnis": ergebnis,
                       "status": status, "hinweis": hinweis,
                       "korrektur": korrektur if status != "OK" else ""})

    if not d85["aktiv"]:
        return checks

    dev = p.get("leitgeraet", K.LEITGERAET_OPTIONEN[0])

    # Uebergreifzone Z1B muss vorhanden und ausreichend sein (>= 120 %)
    fz1b = p.get("f_Z1B", K.f_Z1B_def)
    z1b_ok = fz1b >= K.f_uebergreif_min
    add("Übergreifzone Z1B für Teleschutz ausreichend", "f_Z1B",
        f"{de(fz1b*100, 0)} %", "OK" if z1b_ok else "Prüfen!",
        "Die Vergleichsverfahren beschleunigen über die vorwärts gerichtete Übergreifzone "
        "Z1B. Diese muss über das Leitungsende hinausreichen (>= 120 %).",
        "f_Z1B auf >= 1,20 x XL anheben (Adr.1353).")

    # Blocking-Verfahren benoetigt schnelle Rueckwaertsstufe
    if d85["blockierverfahren"]:
        rueck = any(p.get("modus_" + nm, getattr(K, "modus_" + nm + "_def")) == "Rückwärts"
                    for nm in ("Z4", "Z5", "Z6"))
        add("Blocking: schnelle Rückwärtsstufe vorhanden", "MODUS Z4/Z5/Z6",
            "rückwärts vorhanden" if rueck else "keine Rückwärtsstufe",
            "OK" if rueck else "Prüfen!",
            "Das Blocking-Verfahren benötigt eine schnelle rückwärts gerichtete Zone zur "
            "Erzeugung des Blockiersignals (7SA6 Hdb. 2.6).",
            "Eine Reservezone (Z5) auf rückwärts stellen.")

    # Transiente Blockierzeit gesetzt
    ttb = d85["t_transblock"]
    add("Transiente Blockierzeit gesetzt", "T TRANSBLOCK",
        f"{de(ttb, 2)} s", "OK" if ttb > 0 else "Hinweis",
        "Die transiente Blockierzeit muss länger sein als transiente Vorgänge bei "
        "Fehlerrichtungsumkehr, um Fehlfreigaben zu verhindern.",
        "T TRANSBLOCK > 0 setzen (Voreinst. 0,04 s).")

    # Kommunikationskanal: Voraussetzung ausserhalb des Schutzparametersatzes.
    # Wird nicht ueber einen Einstellwert, sondern ueber die Geraeteprojektierung gesetzt,
    # daher informativ (Status OK) und ohne Parameter-Korrektur.
    if dev == "Leitungsdifferential 7SD5":
        add("Kommunikationskanal (Wirkschnittstelle)", "WS1",
            d85["anschluss"], "OK",
            "Voraussetzung: Der Teleschutz nutzt bei der 7SD5 die Wirkschnittstelle. Diese wird "
            "in der Kommunikationstopologie eingestellt (WS1 Verbindung Adr.4502, WS1-EIN "
            "Adr.4501). Die Gegenstellenzahl muss mit ANZAHL GERAETE (Adr.147) übereinstimmen.",
            "")
    else:
        add("Kommunikationskanal (Signalkanal)", "Projektierung",
            f"Voraussetzung für {d85['verfahren']}", "OK",
            "Voraussetzung außerhalb des Parametersatzes: Das Verfahren benötigt einen "
            "Signalübertragungskanal zum Gegenende. Dieser wird nicht über einen Schutz-"
            "Einstellwert festgelegt, sondern in der Geräteprojektierung in DIGSI: Rangierung "
            "der Binärein-/-ausgänge für Sende-/Empfangssignal bzw. Nutzung der "
            "Wirkschnittstelle. Kein Tool-Parameter erforderlich.",
            "")

    return checks


# ── 50/51 Not-Ueberstromzeitschutz (Reserve, beide Geraete) ──────────────────

def schutz_5051(g: dict, p: dict) -> dict:
    """Not-Ueberstromzeitschutz mit zwei UMZ-Stufen (Iph>>, Iph>)."""
    dev = p.get("leitgeraet", K.LEITGERAET_OPTIONEN[0])
    IN  = g["IN_Ltg"]
    kCT = g["kCT"]
    betriebsart = p.get("uebs_betriebsart", K.uebs_betriebsart_def)

    def stufe(faktor, t):
        prim = faktor * IN
        sek  = prim / kCT if kCT else 0.0
        return {"faktor": faktor, "i_prim": round(prim, 3), "i_sek": round(sek, 4), "t": t}

    return {
        "aktiv":       betriebsart != "Aus",
        "betriebsart": betriebsart,
        "IphHH": stufe(p.get("iph_hh", K.iph_hh_def), p.get("t_iph_hh", K.t_iph_hh_def)),
        "IphH":  stufe(p.get("iph_h",  K.iph_h_def),  p.get("t_iph_h",  K.t_iph_h_def)),
        "adr": {
            "BETRIEBSART": K.ADR_get("UEBS_BETRIEBSART", dev),
            "IPH_HH": K.ADR_get("IPH_HH", dev), "T_IPH_HH": K.ADR_get("T_IPH_HH", dev),
            "IPH_H":  K.ADR_get("IPH_H", dev),  "T_IPH_H":  K.ADR_get("T_IPH_H", dev),
        },
    }


def plausibilitaet_5051(g: dict, p: dict, d50: dict) -> list:
    checks = []

    def add(name, bezug, ergebnis, status, hinweis, korrektur=""):
        checks.append({"pruefung": name, "bezug": bezug, "ergebnis": ergebnis, "status": status,
                       "hinweis": hinweis, "korrektur": korrektur if status != "OK" else ""})

    if not d50["aktiv"]:
        return checks

    HH, H = d50["IphHH"], d50["IphH"]
    add("Stromstaffelung Iph>> > Iph>", "Ansprechwerte",
        f"{de(HH['faktor'], 2)} / {de(H['faktor'], 2)} x IN",
        "OK" if HH["faktor"] > H["faktor"] else "Prüfen!",
        "Die Hochstromstufe Iph>> muss höher ansprechen als die Grundstufe Iph>.",
        "Iph>> > Iph> einstellen.")
    add("Zeitstaffelung T(Iph>>) < T(Iph>)", "Zeiten",
        f"{de(HH['t'], 2)} / {de(H['t'], 2)} s",
        "OK" if HH["t"] < H["t"] else "Prüfen!",
        "Höher ansprechende Stufe löst schneller aus.",
        "T(Iph>>) < T(Iph>) einstellen.")
    add("Iph> oberhalb Maximallast", "Iph> Ansprechwert",
        f"{de(H['faktor'], 2)} x IN", "OK" if H["faktor"] >= 1.1 else "Hinweis",
        "Die Grundstufe muss oberhalb des maximalen Betriebsstroms liegen (Faktor >= 1,1).",
        "Iph> nicht unter ca. 1,1 x IN einstellen.")

    # Empfindlichkeit gegen den minimalen Fehlerstrom am Leitungsende
    Ik_min = g.get("Ik_min_prim", 0.0)
    if Ik_min > 0:
        H_prim, HH_prim = H["i_prim"], HH["i_prim"]
        add(f"Empfindlichkeit: Ik,min >= {deg(K.gamma_Ikmin)} x Iph>", "Ik,min Leitungsende",
            f"{de(Ik_min, 0)} A / {de(H_prim, 0)} A",
            "OK" if (H_prim and Ik_min >= K.gamma_Ikmin * H_prim) else "Prüfen!",
            "Der Not-Überstromschutz muss Fehler am Leitungsende sicher anregen "
            f"(Sicherheitsfaktor {deg(K.gamma_Ikmin)} auf die Grundstufe Iph>).",
            "Iph> verkleinern oder die Ik,min-Berechnung prüfen.")
        add("Reichweite: Iph>> <= Ik,min", "Ik,min Leitungsende",
            f"{de(HH_prim, 0)} A / {de(Ik_min, 0)} A",
            "OK" if HH_prim <= Ik_min else "Hinweis",
            "Liegt Iph>> über Ik,min, erreicht die Hochstromstufe entfernte Fehler "
            "nicht. Es wirkt dann nur die Grundstufe Iph>.",
            "Iph>> reduzieren oder bewusst als Nahfehlerstufe belassen.")
    return checks


# ── 79 Wiedereinschaltautomatik (AWE, beide Geraete) ─────────────────────────

def schutz_79(g: dict, p: dict) -> dict:
    """Automatische Wiedereinschaltung mit Pausen- und Sperrzeit."""
    dev = p.get("leitgeraet", K.LEITGERAET_OPTIONEN[0])
    auto = p.get("auto_we", K.auto_we_def)
    return {
        "aktiv":     auto == "Ein",
        "auto_we":   auto,
        "anzahl":    p.get("awe_anzahl", K.awe_anzahl_def),
        "tp_1pol":   p.get("we_tp_aus1pol", K.we_tp_aus1pol_def),
        "tp_3pol":   p.get("we_tp_aus3pol", K.we_tp_aus3pol_def),
        "sperrzeit": p.get("t_sperrzeit", K.t_sperrzeit_def),
        "adr": {
            "AUTO_WE": K.ADR_get("AUTO_WE", dev),
            "TP_1POL": K.ADR_get("WE_TP_AUS1POL", dev),
            "TP_3POL": K.ADR_get("WE_TP_AUS3POL", dev),
            "SPERRZEIT": K.ADR_get("T_SPERRZEIT", dev),
        },
    }


def plausibilitaet_79(g: dict, p: dict, d79: dict) -> list:
    checks = []

    def add(name, bezug, ergebnis, status, hinweis, korrektur=""):
        checks.append({"pruefung": name, "bezug": bezug, "ergebnis": ergebnis, "status": status,
                       "hinweis": hinweis, "korrektur": korrektur if status != "OK" else ""})

    if not d79["aktiv"]:
        return checks

    sp_ok = d79["sperrzeit"] > max(d79["tp_1pol"], d79["tp_3pol"])
    add("Sperrzeit größer als Pausenzeiten", "T SPERRZEIT",
        f"{de(d79['sperrzeit'], 2)} s vs. {de(max(d79['tp_1pol'], d79['tp_3pol']), 2)} s",
        "OK" if sp_ok else "Prüfen!",
        "Die Sperrzeit (Reclaim) muss länger sein als die Pausenzeiten, damit ein "
        "Wiedereinschaltzyklus vollständig abgeschlossen wird, bevor neu gestartet wird.",
        "T SPERRZEIT größer als die Pausenzeiten setzen (z.B. 3,0 s).")
    add("1-polige Pausenzeit ausreichend (Sekundärlichtbogen)", "TP AUS1Po",
        f"{de(d79['tp_1pol'], 2)} s", "OK" if d79["tp_1pol"] >= 0.9 else "Hinweis",
        "Die spannungslose Pause nach 1-poliger Abschaltung muss lang genug für das "
        "Verlöschen des Sekundärlichtbogens sein (typ. ab ca. 1 s).",
        "TP AUS1Po nicht zu kurz wählen (Richtwert >= 1,0 s).")
    return checks


# ── 50BF Schalterversagerschutz (beide Geraete) ──────────────────────────────

def schutz_50BF(g: dict, p: dict) -> dict:
    """Schalterversagerschutz mit Stromflussueberwachung und zwei Zeitstufen."""
    dev = p.get("leitgeraet", K.LEITGERAET_OPTIONEN[0])
    IN  = g["IN_Ltg"]
    kCT = g["kCT"]
    sv = p.get("schalterv", K.schalterv_def)
    f_svs = p.get("i_svs", K.i_svs_def)
    prim = f_svs * IN
    sek  = prim / kCT if kCT else 0.0
    return {
        "aktiv":     sv == "Ein",
        "schalterv": sv,
        "i_svs":     f_svs, "i_svs_prim": round(prim, 3), "i_svs_sek": round(sek, 4),
        "i3i0_svs":  p.get("i3i0_svs", K.i3i0_svs_def),
        "aus_1pol":  p.get("aus_1pol_svs", K.aus_1pol_svs_def),
        "t1_1pol":   p.get("t1_1pol_svs", K.t1_1pol_svs_def),
        "t1_3pol":   p.get("t1_3pol_svs", K.t1_3pol_svs_def),
        "t2":        p.get("t2_svs", K.t2_svs_def),
        "adr": {
            "SCHALTERV": K.ADR_get("SCHALTERV", dev),
            "I_SVS": K.ADR_get("I_SVS", dev), "I3I0_SVS": K.ADR_get("I3I0_SVS", dev),
            "AUS_1POL": K.ADR_get("AUS_1POL_SVS", dev),
            "T1_1POL": K.ADR_get("T1_1POL_SVS", dev), "T1_3POL": K.ADR_get("T1_3POL_SVS", dev),
            "T2": K.ADR_get("T2_SVS", dev),
        },
    }


def plausibilitaet_50BF(g: dict, p: dict, dbf: dict) -> list:
    checks = []

    def add(name, bezug, ergebnis, status, hinweis, korrektur=""):
        checks.append({"pruefung": name, "bezug": bezug, "ergebnis": ergebnis, "status": status,
                       "hinweis": hinweis, "korrektur": korrektur if status != "OK" else ""})

    if not dbf["aktiv"]:
        return checks

    t1 = max(dbf["t1_1pol"], dbf["t1_3pol"])
    add("Zeitstaffelung T2 > T1", "T2 / T1",
        f"{de(dbf['t2'], 2)} s / {de(t1, 2)} s", "OK" if dbf["t2"] > t1 else "Prüfen!",
        "Die 2. Stufe (umliegende Schalter, Sammelschiene) muss später auslösen als die "
        "1. Stufe (Wiederholungskommando an den eigenen Schalter).",
        "T2 größer als T1 setzen.")
    add("Stromflussüberwachung empfindlich", "I> SVS",
        f"{de(dbf['i_svs'], 2)} x IN", "OK" if dbf["i_svs"] <= 0.2 else "Hinweis",
        "Die Stromschwelle muss kleiner sein als der kleinste Fehlerstrom, aber oberhalb des "
        "Ladestroms. Üblich sind ca. 0,1 x IN.",
        "I> SVS empfindlich einstellen (Richtwert ca. 0,1 x IN).")
    return checks


# ── 68/78 Pendelsperre / Pendelerfassung (beide Geraete) ─────────────────────

def schutz_68(g: dict, p: dict) -> dict:
    """Pendelerfassung mit Pendelsperre fuer den Distanzschutz und optionaler
    Ausloesung bei instabiler Pendelung (Außertrittauslösung)."""
    dev = p.get("leitgeraet", K.LEITGERAET_OPTIONEN[0])
    erf = p.get("pendelerfassung", K.pendelerfassung_def)
    return {
        "aktiv":        erf == "Vorhanden",
        "erfassung":    erf,
        "pen_ausloes":  p.get("pen_ausloes", K.pen_ausloes_def),
        "adr": {
            "PENDELERFASSUNG": K.ADR_get("PENDELERFASSUNG", dev),
            "PEN_AUSLOES":     K.ADR_get("PEN_AUSLOES", dev),
        },
    }


# ── 27/59 Spannungsschutz (beide Geraete) ────────────────────────────────────

def schutz_2759(g: dict, p: dict) -> dict:
    """Zweistufiger Ueber- und Unterspannungsschutz (Phasenspannung)."""
    dev = p.get("leitgeraet", K.LEITGERAET_OPTIONEN[0])
    UN  = p.get("UN_kV", 0.0)
    VTs = p.get("VT_Sek_V", 0.0)
    aktiv = p.get("spannungsschutz", K.spannungsschutz_def) == "Ein"

    def stufe(faktor):
        u_prim_ph = faktor * (UN * 1e3) / SQRT3       # [V primaer, Leiter-Erde]
        u_sek_ph  = faktor * VTs / SQRT3 if VTs else 0.0   # [V sekundaer, Leiter-Erde]
        return {"faktor": faktor, "u_prim": round(u_prim_ph, 1), "u_sek": round(u_sek_ph, 2)}

    return {
        "aktiv":     aktiv,
        "spannungsschutz": p.get("spannungsschutz", K.spannungsschutz_def),
        "UphH":  {**stufe(p.get("uph_h",  K.uph_h_def)),  "t": p.get("t_uph_h",  K.t_uph_h_def)},
        "UphHH": {**stufe(p.get("uph_hh", K.uph_hh_def)), "t": p.get("t_uph_hh", K.t_uph_hh_def)},
        "UphL":  {**stufe(p.get("uph_l",  K.uph_l_def)),  "t": p.get("t_uph_l",  K.t_uph_l_def)},
        "UphLL": {**stufe(p.get("uph_ll", K.uph_ll_def)), "t": p.get("t_uph_ll", K.t_uph_ll_def)},
        "adr": {
            "UPH_H": K.ADR_get("UPH_H", dev),   "T_UPH_H": K.ADR_get("T_UPH_H", dev),
            "UPH_HH": K.ADR_get("UPH_HH", dev), "T_UPH_HH": K.ADR_get("T_UPH_HH", dev),
            "UPH_L": K.ADR_get("UPH_L", dev),   "T_UPH_L": K.ADR_get("T_UPH_L", dev),
            "UPH_LL": K.ADR_get("UPH_LL", dev), "T_UPH_LL": K.ADR_get("T_UPH_LL", dev),
        },
    }


# ── 81 Frequenzschutz (beide Geraete, frequenzabhaengige Adressen) ───────────

def schutz_81(g: dict, p: dict) -> dict:
    """Vier Frequenzstufen f1 ... f4. Adresse je nach Nennfrequenz (50/60 Hz)."""
    dev = p.get("leitgeraet", K.LEITGERAET_OPTIONEN[0])
    fN  = p.get("f_netz", K.f_netz)
    suf = "50" if fN == 50 else "60"
    aktiv = p.get("frequenzschutz", K.frequenzschutz_def) == "Ein"

    def stufe(nm, f_def, t_def):
        f = p.get(nm.lower(), f_def)
        return {"f": f, "t": p.get("t_" + nm.lower(), t_def),
                "art": "Unterfrequenz" if f < fN else "Überfrequenz",
                "adr_f": K.ADR_get(f"{nm.upper()}_{suf}", dev),
                "adr_t": K.ADR_get(f"T_{nm.upper()}", dev)}

    return {
        "aktiv":   aktiv,
        "fN":      fN,
        "f1": stufe("f1", K.f1_def, K.t_f1_def),
        "f2": stufe("f2", K.f2_def, K.t_f2_def),
        "f3": stufe("f3", K.f3_def, K.t_f3_def),
        "f4": stufe("f4", K.f4_def, K.t_f4_def),
        "adr_funktion": K.ADR_get("FREQUENZSCHUTZ", dev),
    }


# ── 49 Thermischer Ueberlastschutz (beide Geraete) ───────────────────────────

def schutz_49(g: dict, p: dict) -> dict:
    """Thermisches Abbild. tau_th in MINUTEN (Adr.4203, geraeteabhaengig)."""
    dev = p.get("leitgeraet", K.LEITGERAET_OPTIONEN[0])
    IN  = g["IN_Ltg"]
    kCT = g["kCT"]
    aktiv = p.get("ueberlastschutz", K.ueberlastschutz_def) == "Ein"

    k = p.get("k_faktor", K.k_faktor_def)
    i_max_prim = k * IN
    i_max_sek  = i_max_prim / kCT if kCT else 0.0
    i_warn_f = p.get("i_warn", K.i_warn_def)

    return {
        "aktiv":        aktiv,
        "ueberlastschutz": p.get("ueberlastschutz", K.ueberlastschutz_def),
        "k_faktor":     k,
        "i_max_prim":   round(i_max_prim, 2),
        "i_max_sek":    round(i_max_sek, 4),
        "zeitkonstante": p.get("zeitkonstante", K.zeitkonstante_def),  # Minuten
        "theta_warn":   p.get("theta_warn", K.theta_warn_def),
        "i_warn":       i_warn_f,
        "i_warn_prim":  round(i_warn_f * IN, 2),
        "adr": {
            "UEBERLAST": K.ADR_get("UEBERLASTSCHUTZ", dev),
            "K_FAKTOR":  K.ADR_get("K_FAKTOR", dev),
            "ZEITKONST": K.ADR_get("ZEITKONSTANTE", dev),
            "THETA_WARN": K.ADR_get("THETA_WARN", dev),
            "I_WARN":    K.ADR_get("I_WARN", dev),
        },
    }


def plausibilitaet_rest(g: dict, p: dict, d68: dict, d2759: dict, d81: dict, d49: dict) -> list:
    """Plausibilitaet fuer Pendelsperre, Spannungs-, Frequenz- und Ueberlastschutz."""
    checks = []

    def add(name, bezug, ergebnis, status, hinweis, korrektur=""):
        checks.append({"pruefung": name, "bezug": bezug, "ergebnis": ergebnis, "status": status,
                       "hinweis": hinweis, "korrektur": korrektur if status != "OK" else ""})

    # 27/59 Staffelung Unter-/Ueberspannung
    if d2759["aktiv"]:
        ov_ok = d2759["UphHH"]["faktor"] > d2759["UphH"]["faktor"] > 1.0
        add("Überspannung: Uph>> > Uph> > 1,0", "Uph-Stufen",
            f"{de(d2759['UphHH']['faktor'], 2)} / {de(d2759['UphH']['faktor'], 2)} x UN",
            "OK" if ov_ok else "Prüfen!",
            "Die höhere Überspannungsstufe muss höher ansprechen als die untere, beide "
            "oberhalb der Nennspannung.",
            "Regler 'Uph>' und 'Uph>>' (Abschnitt 27/59) so setzen, dass Uph>> > Uph> > 1,0, "
            "z.B. Uph> = 1,15 und Uph>> = 1,30.")
        uv_ok = d2759["UphLL"]["faktor"] < d2759["UphL"]["faktor"] < 1.0
        add("Unterspannung: Uph<< < Uph< < 1,0", "Uph-Stufen",
            f"{de(d2759['UphLL']['faktor'], 2)} / {de(d2759['UphL']['faktor'], 2)} x UN",
            "OK" if uv_ok else "Prüfen!",
            "Die tiefere Unterspannungsstufe muss tiefer ansprechen als die obere, beide "
            "unterhalb der Nennspannung.",
            "Regler 'Uph<' und 'Uph<<' (Abschnitt 27/59) so setzen, dass Uph<< < Uph< < 1,0, "
            "z.B. Uph< = 0,75 und Uph<< = 0,65.")

    # 81 Frequenzstufen sinnvoll um fN verteilt
    if d81["aktiv"]:
        fN = d81["fN"]
        unter = [s for s in (d81["f1"], d81["f2"], d81["f3"], d81["f4"]) if s["f"] < fN]
        ueber = [s for s in (d81["f1"], d81["f2"], d81["f3"], d81["f4"]) if s["f"] > fN]
        add("Frequenzstufen um Nennfrequenz verteilt", f"fN = {deg(fN)} Hz",
            f"{len(unter)} Unter-, {len(ueber)} Überfrequenzstufen",
            "OK" if (unter and ueber) else "Hinweis",
            "Sinnvoll ist mindestens je eine Stufe für Unter- und Überfrequenz.",
            "Regler 'f1 [Hz]' … 'f4 [Hz]' (Abschnitt 81 Frequenzschutz) so verteilen, dass "
            "mindestens eine Stufe unter und eine über fN liegt, z.B. f1 = 48,0 / f2 = 49,0 "
            "(Unterfrequenz) und f3 = 51,0 / f4 = 51,5 Hz (Überfrequenz).")
        spanne = max(abs(s["f"] - fN) for s in (d81["f1"], d81["f2"], d81["f3"], d81["f4"]))
        add("Frequenz-Ansprechwerte im plausiblen Bereich", "|f - fN|",
            f"max. {de(spanne, 2)} Hz von fN", "OK" if spanne <= 5 else "Hinweis",
            "Die Ansprechwerte sollten realistisch nahe der Nennfrequenz liegen "
            "(typ. +/- 3 Hz).",
            f"Regler 'f1 [Hz]' … 'f4 [Hz]' (Abschnitt 81 Frequenzschutz) näher an fN = {deg(fN)} Hz "
            f"legen, Richtwert innerhalb {deg(fN-5)} … {deg(fN+5)} Hz.")

    # 49 Zeitkonstante und k-Faktor plausibel
    if d49["aktiv"]:
        add("k-Faktor im plausiblen Bereich", "K-FAKTOR",
            f"{de(d49['k_faktor'], 2)}", "OK" if 1.0 <= d49["k_faktor"] <= 1.3 else "Hinweis",
            "Der k-Faktor (I_dauer/IN) liegt üblicherweise zwischen 1,0 und 1,2.",
            "k-Faktor aus den thermischen Leitungsdaten bestimmen (typ. 1,0 ... 1,2).")
        add("Zeitkonstante in Minuten angegeben", "ZEITKONSTANTE",
            f"{d49['zeitkonstante']} min", "OK",
            "Die Erwärmungszeitkonstante ist bei 7SA6/7SD5 in Minuten einzustellen "
            "(geräteabhängig, anders als z.B. 7UM62 in Sekunden).", "")

    # 68/78 Pendelsperre setzt Distanzschutz voraus
    if d68["aktiv"]:
        st = "OK" if d68["pen_ausloes"] == "Nein" else "Hinweis"
        add("Pendelerfassung wirkt als Pendelsperre", "PEN-AUSLOES",
            f"Außertrittauslösung = {d68['pen_ausloes']}", st,
            "Die Pendelerfassung blockiert den Distanzschutz bei stabilen Pendelungen. Eine "
            "Auslösung bei instabiler Pendelung (Außertrittauslösung) ist nur bei "
            "entsprechender Netzanforderung zu aktivieren.",
            "PEN-AUSLOES nur bei gewünschter Außertrittauslösung auf Ja setzen.")

    return checks


# ── Plausibilitaetspruefung Distanzschutz (Ampel) ───────────────────────────


def plausibilitaet(g: dict, p: dict, d21: dict) -> list:
    checks = []

    def add(name, bezug, ergebnis, status, hinweis, korrektur=""):
        checks.append({"pruefung": name, "bezug": bezug, "ergebnis": ergebnis,
                       "status": status, "hinweis": hinweis,
                       "korrektur": korrektur if status != "OK" else ""})

    # Pflichteingaben
    add("Nennspannung UN vorhanden", "UN > 0",
        f"{deg(p.get('UN_kV', 0))} kV" if p.get("UN_kV", 0) > 0 else "fehlt",
        "OK" if p.get("UN_kV", 0) > 0 else "Fehlt",
        "Bemessungsspannung der Leitung erforderlich.",
        "Feld 'UN' ausfüllen (> 0 kV).")

    add("Leitungslänge vorhanden", "L > 0",
        f"{deg(p.get('L_km', 0))} km" if p.get("L_km", 0) > 0 else "fehlt",
        "OK" if p.get("L_km", 0) > 0 else "Fehlt",
        "Leitungslänge bestimmt die primäre Leitungsreaktanz X_Ltg.",
        "Feld 'Leitungslänge' ausfüllen (> 0 km).")

    # Konsistenz der Kurzschlussrechnung (falls beide Werte vorliegen)
    Ik_max, Ik_min = g.get("Ik_max_prim", 0.0), g.get("Ik_min_prim", 0.0)
    if Ik_max > 0 and Ik_min > 0:
        add("Konsistenz Ik″max >= Ik,min", "Kurzschlussrechnung",
            f"{de(Ik_max, 0)} A / {de(Ik_min, 0)} A",
            "OK" if Ik_max >= Ik_min else "Prüfen!",
            "Der maximale Kurzschlussstrom am Leitungsanfang muss über dem "
            "minimalen am Leitungsende liegen (DIN EN 60909-0).",
            "Eingaben Ik″max und Ik,min prüfen.")

    # Mindestlaenge fuer sinnvollen Distanzschutz (streckenartabhaengig)
    L_km = p.get("L_km", 0.0)
    art  = p.get("leitungsart", "Freileitung")
    dev  = p.get("leitgeraet", K.LEITGERAET_OPTIONEN[0])
    L_min = K.L_MIN_DISTANZ_KM.get(art, K.L_MIN_DISTANZ_DEFAULT_KM)
    if L_km > 0:
        kurz = L_km < L_min
        if dev == "Distanzschutz 7SA6":
            rx_emp = K.RX_KURZ_EMPFEHLUNG.get(art, "2 bis 5")
            add(f"Mindestleitungslänge für Distanzschutz ({art})",
                f"L = {deg(L_km)} km (Grenze {deg(L_min)} km)",
                f"{deg(L_km)} km", "Hinweis" if kurz else "OK",
                f"Für {art.lower()} gilt eine Strecke unter {deg(L_min)} km als kurz "
                "(Anwendungstabelle 7SD5-Hdb. nach Ziegler). Bei kleinen Leitungsimpedanzen wird "
                "der Z1-Reach (0,85 x X_Ltg) sehr klein und die Distanzmessung reagiert empfindlich "
                "auf Wandler- und Gerätetoleranzen.",
                f"R/X-Verhältnis der Zonen auf ca. {rx_emp} anheben. Bei sehr kurzer Strecke "
                "Leitungsdifferentialschutz 7SD5 (87L) als Hauptschutz erwägen.")
        else:
            add(f"Leitungslänge für Leitungsdifferentialschutz ({art})",
                f"L = {deg(L_km)} km (Grenze Distanzschutz {deg(L_min)} km)",
                f"{deg(L_km)} km", "OK",
                ("Der Leitungsdifferentialschutz 87L ist gerade für kurze Strecken die robuste "
                 "Wahl, da er unabhängig von der Leitungsimpedanz arbeitet."
                 if kurz else "Leitungslänge im üblichen Bereich; 87L als Hauptschutz geeignet."),
                "")

    add("Reaktanzbelag X' vorhanden", "X' > 0",
        f"{deg(p.get('X_Belag', 0))} Ω/km" if p.get("X_Belag", 0) > 0 else "fehlt",
        "OK" if p.get("X_Belag", 0) > 0 else "Fehlt",
        "Reaktanzbelag aus den Leitungskonstanten (Adr.1110 X-BELAG).",
        "Feld 'X'-Belag' ausfüllen (> 0 Ω/km).")

    # Leitungswinkel plausibel
    phi = p.get("phi_Ltg", 0)
    phi_st = status_bereich(phi, K.phi_Ltg_min, K.phi_Ltg_max) if phi else "Fehlt"
    add(f"Leitungswinkel im Bereich [{deg(K.phi_Ltg_min)} ... {deg(K.phi_Ltg_max)}°]", "PHI LTG",
        f"{deg(phi)}°" if phi else "-", phi_st,
        "Typischer Leitungswinkel arctan(X'/R') liegt bei 60 ... 88°.",
        f"PHI LTG = {deg(phi)}° außerhalb [{deg(K.phi_Ltg_min)} ... {deg(K.phi_Ltg_max)}°]: "
        "Leitungskonstanten prüfen (Adr.1105).")

    # Stromwandler / Spannungswandler vorhanden
    ct_ok = p.get("CT_Prim", 0) > 0 and p.get("CT_Sek", 0) > 0
    add("Stromwandler vorhanden", "CT prim/sek > 0",
        "vorhanden" if ct_ok else "fehlt", "OK" if ct_ok else "Fehlt",
        "Stromwandler für Sekundärbezug der Distanzzonen erforderlich.",
        "CT prim. [A] und CT sek. [A] eingeben.")

    vt_ok = p.get("VT_Prim_kV", 0) > 0 and p.get("VT_Sek_V", 0) > 0
    add("Spannungswandler vorhanden", "VT prim/sek > 0",
        "vorhanden" if vt_ok else "fehlt", "OK" if vt_ok else "Fehlt",
        "Spannungswandler für Impedanzmessung des Distanzschutzes erforderlich.",
        "VT prim. [kV] und VT sek. [V] eingeben.")

    # Sekundaerbezug k_Z plausibel (Zonen sekundaer lesbar)
    kZ = g["k_Z"]
    if kZ > 0:
        Xs_Z1 = d21["Z1"]["X_sek"]
        kz_ok = 0.05 <= Xs_Z1 <= 250.0
        add("Sekundäre Z1-Reichweite im lesbaren Bereich", "X(Z1) sek.",
            f"{de(Xs_Z1, 3)} Ω sek." if Xs_Z1 else "-",
            "OK" if kz_ok else "Hinweis",
            "Sekundäre Zonenimpedanz sollte im einstellbaren Bereich liegen.",
            "Sehr kleine/große Sekundärwerte: Wandlerdaten (CT/VT) prüfen.")

    # Z1-Unterreichweite 70 ... 90 %
    fZ1 = p.get("f_Z1", K.f_Z1_def)
    z1_st = status_bereich(fZ1, K.f_Z1_min, K.f_Z1_max)
    add(f"Z1-Reichweite im Bereich [{int(K.f_Z1_min*100)} ... {int(K.f_Z1_max*100)} %]",
        "f_Z1 x XL", f"{de(fZ1*100, 0)} %", z1_st,
        "Z1 als Unterreichweite (Voreinst. 85 %), damit die unverzögerte Zone nicht "
        "über das Leitungsende hinausreicht.",
        f"f_Z1 = {de(fZ1*100, 0)} % außerhalb [{int(K.f_Z1_min*100)} ... "
        f"{int(K.f_Z1_max*100)} %]: Z1-Reichweite auf ~85 % stellen.")

    # Uebergreifzonen >= ~120 %
    for nm, key in (("Z1B", "f_Z1B"), ("Z2", "f_Z2")):
        f = p.get(key, getattr(K, key + "_def"))
        st = "OK" if f >= K.f_uebergreif_min else "Prüfen!"
        add(f"{nm}-Reichweite >= {int(K.f_uebergreif_min*100)} % (Übergreifzone)",
            f"{key} x XL", f"{de(f*100, 0)} %", st,
            f"{nm} muss über das Leitungsende hinausreichen (>= ~120 %).",
            f"{key} = {de(f*100, 0)} % < {int(K.f_uebergreif_min*100)} %: "
            f"{nm}-Reichweite anheben (>= 1,20 x XL).")

    # Staffelung Z1 < Z2 < Z3 (monoton steigende Reichweite)
    f1, f2, f3 = (p.get("f_Z1", K.f_Z1_def), p.get("f_Z2", K.f_Z2_def),
                  p.get("f_Z3", K.f_Z3_def))
    staff_ok = f1 < f2 <= f3
    add("Staffelung der Reichweiten Z1 < Z2 <= Z3", "f_Z1 < f_Z2 <= f_Z3",
        f"{de(f1, 2)} / {de(f2, 2)} / {de(f3, 2)}", "OK" if staff_ok else "Prüfen!",
        "Reichweiten müssen mit der Zonennummer zunehmen (Zeitstaffelung).",
        "Reichweitenfaktoren so setzen, dass f_Z1 < f_Z2 <= f_Z3.")

    # Zeitstaffelung t_Z1 < t_Z2 < t_Z3
    t1, t2, t3 = (p.get("t_Z1", K.t_Z1_def), p.get("t_Z2", K.t_Z2_def),
                  p.get("t_Z3", K.t_Z3_def))
    tstaff_ok = t1 <= t2 < t3 or (t1 == 0 and t2 < t3)
    add("Zeitstaffelung T1 <= T2 < T3", "t_Z1 <= t_Z2 < t_Z3",
        f"{de(t1, 2)} / {de(t2, 2)} / {de(t3, 2)} s", "OK" if (t1 <= t2 <= t3 and t2 < t3) else "Prüfen!",
        "Z1 unverzögert, höhere Zonen zeitlich gestaffelt.",
        "Zeiten so setzen, dass T1 <= T2 < T3 (z.B. 0,00 / 0,30 / 0,60 s).")

    # Reservezonen Z4/Z5/Z6: aktive Zonen zeitlich hinter T3, Vorwaerts-Zonen
    # mit zunehmender Reichweite gestaffelt.
    aktive = []
    for nm in ("Z4", "Z5", "Z6"):
        md = p.get("modus_" + nm, getattr(K, "modus_" + nm + "_def"))
        if md != "Unwirksam":
            aktive.append((nm, md,
                           p.get("f_" + nm, getattr(K, "f_" + nm + "_def")),
                           p.get("t_" + nm, getattr(K, "t_" + nm + "_def"))))
    if aktive:
        t_vor = [t for nm, md, f, t in aktive if md in ("Vorwärts", "Ungerichtet")]
        zeit_ok = all(t >= t3 for nm, md, f, t in aktive)
        sortiert = all(t_vor[i] <= t_vor[i + 1] for i in range(len(t_vor) - 1)) if len(t_vor) > 1 else True
        liste = ", ".join(f"{nm}={md}/{de(t, 2)}s" for nm, md, f, t in aktive)
        st = "OK" if (zeit_ok and sortiert) else "Hinweis"
        add("Reservezonen Z4-Z6 zeitlich hinter T3 gestaffelt", "aktive Z4/Z5/Z6",
            liste, st,
            "Aktive Reservezonen wirken zeitverzögert nach den Hauptzonen; "
            "Vorwärtszonen mit zunehmender Reichweite ansteigend gestaffelt.",
            f"Verzögerung aktiver Reservezonen >= T3 = {de(t3, 2)} s setzen "
            "und Vorwärtszonen aufsteigend staffeln.")
    else:
        add("Reservezonen Z4-Z6", "MODUS", "alle unwirksam", "OK",
            "Keine Reservezonen aktiviert (Standardstaffelung Z1/Z1B/Z2/Z3).", "")

    # R/X-Stabilitaet der Z1
    rxz1 = p.get("RX_Z1", K.RX_Z1_def)
    rx_st = "OK" if rxz1 <= K.RX_Z1_max else "Hinweis"
    add(f"R/X-Verhältnis der Z1 <= {de(K.RX_Z1_max, 1)}", "RX_Z1",
        f"{de(rxz1, 2)}", rx_st,
        "Der 85-%-Staffelfaktor gilt nur bis R/X <= 1. Bei größerem R-Abschnitt "
        "ist die X-Reichweite zu reduzieren (7SA6 Hdb. 2.2.2).",
        f"R/X = {de(rxz1, 2)} > {de(K.RX_Z1_max, 1)}: entweder R(Z1) verkleinern oder "
        "X(Z1)-Reichweite reduzieren.")

    # Erdimpedanzanpassung gesetzt
    fmt = p.get("erdimp_format", K.ERDIMP_FORMAT_OPTIONEN[0])
    if fmt == K.ERDIMP_FORMAT_OPTIONEN[0]:   # RE/RL, XE/XL
        val = p.get("RE_RL", K.RE_RL_def)
        gesetzt = val > 0
        erg = f"RE/RL = {de(val, 2)}"
    else:                                    # K0
        val = p.get("K0", K.K0_def)
        gesetzt = val > 0
        erg = f"K0 = {de(val, 2)} ∠ {p.get('PHI_K0', K.PHI_K0_def)}°"
    add("Erdimpedanzanpassung gesetzt", "Format Adr.237",
        erg, "OK" if gesetzt else "Prüfen!",
        "k0 bzw. RE/RL,XE/XL aus den Leitungskonstanten bestimmen, nicht schätzen.",
        "Erdimpedanzfaktor aus dem Leitungsdatenblatt eintragen.")

    return checks


# ── Geraete-/Architektur-Empfehlung ──────────────────────────────────────────

def geraeteempfehlung(p: dict) -> dict:
    dev = p.get("leitgeraet", K.LEITGERAET_OPTIONEN[0])
    L   = p.get("L_km", 0.0)
    if dev == "Leitungsdifferential 7SD5":
        haupt = ("87L Leitungslängsdifferentialschutz als Hauptschutz, Distanzschutz 21 "
                 "als integrierte Reserve. Voraussetzung: Wirkschnittstelle (Kommunikation) "
                 "zwischen beiden Leitungsenden.")
    else:
        haupt = ("Distanzschutz 21 als Hauptschutz mit Signalvergleichsverfahren (Teleschutz) "
                 "zur Beschleunigung. Kein Kommunikationskanal für einen Längsvergleich "
                 "zwingend erforderlich.")
    hinweis = ""
    art = p.get("leitungsart", "Freileitung")
    L_min = K.L_MIN_DISTANZ_KM.get(art, K.L_MIN_DISTANZ_DEFAULT_KM)
    if L and L < L_min and dev == "Distanzschutz 7SA6":
        hinweis = (f"Kurze {art.lower()} (< {deg(L_min)} km): hier ist der "
                   "Leitungslängsdifferentialschutz 7SD5 (87L) häufig die robustere Wahl, da "
                   "die Distanzmessung bei kleinen Leitungsimpedanzen empfindlich auf Mess- und "
                   "Wandlerfehler reagiert.")
    return {"leitgeraet": dev, "haupt": haupt, "hinweis": hinweis}


# ── Gesamtberechnung ─────────────────────────────────────────────────────────

def berechne_alle(p: dict) -> dict:
    g    = grundgroessen(p)
    d21  = schutz_21(g, p)
    d87  = schutz_87L(g, p)
    d67  = schutz_67N(g, p)
    d85  = schutz_85(g, p)
    d50  = schutz_5051(g, p)
    d79  = schutz_79(g, p)
    dbf  = schutz_50BF(g, p)
    d68  = schutz_68(g, p)
    d2759 = schutz_2759(g, p)
    d81  = schutz_81(g, p)
    d49  = schutz_49(g, p)
    plaus = (plausibilitaet(g, p, d21) + plausibilitaet_87L(g, p, d87)
             + plausibilitaet_67N(g, p, d67) + plausibilitaet_85(g, p, d85, d21)
             + plausibilitaet_5051(g, p, d50) + plausibilitaet_79(g, p, d79)
             + plausibilitaet_50BF(g, p, dbf)
             + plausibilitaet_rest(g, p, d68, d2759, d81, d49))
    geh  = geraeteempfehlung(p)
    return {
        "grund": g,
        "21": d21, "87L": d87, "67N": d67, "85": d85,
        "50/51": d50, "79": d79, "50BF": dbf,
        "68/78": d68, "27/59": d2759, "81": d81, "49": d49,
        "plausibilitaet": plaus,
        "empfehlung": geh,
    }
