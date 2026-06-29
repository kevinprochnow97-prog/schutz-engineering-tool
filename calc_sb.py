"""
calc_sb.py — Berechnungslogik Sammelschienenschutz (SIPROTEC 7SS52)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reine Python-Funktionen (kein Streamlit) -> isoliert testbar.
Methodik nach SIPROTEC 7SS52 V4 (dezentraler Sammelschienen- und
Schalterversagerschutz). Ausgabe IEC-normiert (x Bezugsstrom, A prim./sek., s).

Bezugsströme (herstellerneutral):
  - 87B Differentialschutz:        Vielfaches des Zonen-Bezugsstroms Ino
  - SVS / Reserve-SVS / UMZ/AMZ:   Vielfaches des Abzweig-Nennstroms In = CT prim.

Sekundärumrechnung:
  i_sek = i_prim / kCT     mit   kCT = CT_prim / CT_sek
"""

import math
import konstanten_sb as K
from calc_trafo import status_bereich, status_empfehlung  # gemeinsame Ampel-Helfer
from utils import de

SQRT3 = math.sqrt(3)


# -- Berechnete Grundgroessen -------------------------------------------------

def grundgroessen(p: dict) -> dict:
    """
    Wandlerverhältnis, Bezugsströme und sekundäre Umrechnungsfaktoren.
    Erwartet: UN_kV, IN_ref (Ino prim. [A]), CT_Prim, CT_Sek,
              anzahl_abzweige, Imax_Last, Imax_Abzweig, Iscc_min_kA, Iscc_max_kA, t_LS
    """
    CT_P = p.get("CT_Prim", 0.0)
    CT_S = p.get("CT_Sek", 0.0)

    kCT = (CT_P / CT_S) if CT_S else 0.0

    IN_ref = p.get("IN_ref", 0.0)                      # Zonen-Bezugsstrom Ino prim. [A]
    IN_ref_sek = (IN_ref / kCT) if kCT else 0.0        # Ino sekundaer [A]

    # Abzweig-Nennstrom In (= primaerer Wandlernennstrom), sekundaer = CT_Sek
    In_prim = CT_P
    In_sek = CT_S

    # STW-Anpassung: Verhaeltnis Bezugsstrom zu Wandler-Nennstrom (ideal ~ 1)
    Anpass = (IN_ref / CT_P) if CT_P else 0.0

    # Kurzschlussstroeme in A primaer
    Iscc_min = p.get("Iscc_min_kA", 0.0) * 1e3
    Iscc_max = p.get("Iscc_max_kA", 0.0) * 1e3

    return {
        "kCT":        round(kCT, 4),
        "IN_ref":     round(IN_ref, 3),
        "IN_ref_sek": round(IN_ref_sek, 4),
        "In_prim":    round(In_prim, 3),
        "In_sek":     round(In_sek, 4),
        "Anpass":     round(Anpass, 4),
        "Imax_Last":  round(p.get("Imax_Last", 0.0), 3),
        "Imax_Abz":   round(p.get("Imax_Abzweig", 0.0), 3),
        "Iscc_min":   round(Iscc_min, 3),
        "Iscc_max":   round(Iscc_max, 3),
        "t_LS":       round(p.get("t_LS", 0.0), 4),
        "anzahl_abzweige": int(p.get("anzahl_abzweige", 0)),
    }


def _prim_sek_ino(faktor, g):
    """Primär/Sekundär aus Vielfachem des Bezugsstroms Ino."""
    prim = faktor * g["IN_ref"]
    sek = (prim / g["kCT"]) if g["kCT"] else 0.0
    return round(prim, 3), round(sek, 4)


def _prim_sek_in(faktor, g):
    """Primär/Sekundär aus Vielfachem des Abzweig-Nennstroms In = CT prim."""
    prim = faktor * g["In_prim"]
    sek = faktor * g["In_sek"]
    return round(prim, 3), round(sek, 4)


def _korr(regler, adr, abschnitt, aktion):
    """Einheitlicher Korrekturhinweis: nennt den exakten Regler, dessen DIGSI-Adresse,
    den Eingabe-Abschnitt (Expander) zum Auffinden und die konkrete Aktion."""
    adr_teil = f" (Adr.{adr})" if adr and adr != "—" else ""
    return f"Regler '{regler}'{adr_teil} im Abschnitt '{abschnitt}' {aktion}"


def _status_weich(eingabe, empfehlung) -> str:
    """Abweichung von einer Empfehlung ist höchstens ein Hinweis, nie ein Fehler:
    die Werksvoreinstellung ist plausibel, aber noch nicht an die Netzdaten angepasst."""
    return "OK" if status_empfehlung(eingabe, empfehlung) == "OK" else "Hinweis"


def _ziel(wert, vmin, vmax, einheit="", prim=None):
    """Formuliert die Stellaktion 'auf ca. X Einheit (entspricht etwa P A) setzen' und
    behandelt den Fall, dass die Empfehlung außerhalb des Reglerbereichs [vmin, vmax]
    liegt (Punkt 2): dann wird auf den erreichbaren Grenzwert verwiesen und die nicht
    einstellbare Empfehlung ausgewiesen, statt einen unmöglichen Wert zu fordern."""
    eh = f" {einheit}" if einheit else ""
    prim_teil = f" (entspricht etwa {de(prim, 0)} A)" if prim is not None else ""
    if wert > vmax:
        return (f"auf den Maximalwert {de(vmax, 2)}{eh} setzen. Die Empfehlung von "
                f"{de(wert, 2)}{eh}{prim_teil} liegt oberhalb des Reglerbereichs "
                f"(Maximum {de(vmax, 2)}{eh}); Wandlerauslegung bzw. Bezugsstrom prüfen.")
    if wert < vmin:
        return (f"auf den Minimalwert {de(vmin, 2)}{eh} setzen. Die Empfehlung von "
                f"{de(wert, 2)}{eh}{prim_teil} liegt unterhalb des Reglerbereichs "
                f"(Minimum {de(vmin, 2)}{eh}).")
    return f"auf ca. {de(wert, 2)}{eh}{prim_teil} setzen."


# -- 87B Sammelschienen-Differentialschutz ------------------------------------

def schutz_87B(g: dict, p: dict) -> dict:
    """
    Stabilisierte Differentialstufe (selektive Zone SS und Checkzone CZ),
    optional empfindliche Kennlinie. Ansprechwerte als Vielfaches von Ino.
    Adressen Zentraleinheit (Adr.6101 ff.).
    """
    aktiv = p.get("diff_aktiv", K.diff_aktiv_def)

    stab_ss = p.get("stab_faktor_ss", K.stab_faktor_ss_def)
    stab_cz = p.get("stab_faktor_cz", K.stab_faktor_cz_def)
    id_ss_f = p.get("id_ss", K.id_ss_def)
    id_cz_f = p.get("id_cz", K.id_cz_def)
    querstab_ss = p.get("querstab_ss", K.querstab_ss_def)
    querstab_cz = p.get("querstab_cz", K.querstab_cz_def)

    empf = p.get("empf_kennl", K.empf_kennl_def)
    empf_frei = (empf == "freigegeben")
    is_ss_e = p.get("is_ss_empf", K.is_ss_empf_def)
    id_ss_e = p.get("id_ss_empf", K.id_ss_empf_def)
    is_cz_e = p.get("is_cz_empf", K.is_cz_empf_def)
    id_cz_e = p.get("id_cz_empf", K.id_cz_empf_def)

    zusatzkrit = p.get("zusatzkrit", K.zusatzkrit_def)
    t_aus_min = p.get("t_aus_min", K.t_aus_min_def)

    id_ss_prim, id_ss_sek = _prim_sek_ino(id_ss_f, g)
    id_cz_prim, id_cz_sek = _prim_sek_ino(id_cz_f, g)
    id_ss_e_prim, id_ss_e_sek = _prim_sek_ino(id_ss_e, g)
    id_cz_e_prim, id_cz_e_sek = _prim_sek_ino(id_cz_e, g)

    # Empfehlungsfenster fuer den Ansprechwert (1,3 x Imax Abzw. < Id> < 0,8 x Iscc min)
    id_min_prim = K.ID_FAKTOR_ABZWEIG_MIN * g["Imax_Abz"]
    id_max_prim = K.ID_FAKTOR_ISCC_MAX * g["Iscc_min"]
    id_empf_prim = K.ID_EMPF_ANTEIL_ISCC * g["Iscc_min"]
    is_empf_prim = K.IS_EMPF_FAKTOR * g["Imax_Last"]

    def adr(key):
        return K.ADR_get(key)

    return {
        "aktiv": aktiv,
        "stab_ss": stab_ss, "stab_cz": stab_cz,
        "id_ss_f": id_ss_f, "id_ss_prim": id_ss_prim, "id_ss_sek": id_ss_sek,
        "id_cz_f": id_cz_f, "id_cz_prim": id_cz_prim, "id_cz_sek": id_cz_sek,
        "querstab_ss": querstab_ss, "querstab_cz": querstab_cz,
        "empf_kennl": empf, "empf_frei": empf_frei,
        "is_ss_e": is_ss_e, "id_ss_e": id_ss_e,
        "is_cz_e": is_cz_e, "id_cz_e": id_cz_e,
        "id_ss_e_prim": id_ss_e_prim, "id_ss_e_sek": id_ss_e_sek,
        "id_cz_e_prim": id_cz_e_prim, "id_cz_e_sek": id_cz_e_sek,
        "zusatzkrit": zusatzkrit, "t_aus_min": t_aus_min,
        "id_min_prim": round(id_min_prim, 1), "id_max_prim": round(id_max_prim, 1),
        "id_empf_prim": round(id_empf_prim, 1), "is_empf_prim": round(is_empf_prim, 1),
        "adr": {
            "STAB_SS": adr("STAB_FAKTOR_SS"), "ID_SS": adr("ID_SS"),
            "STAB_CZ": adr("STAB_FAKTOR_CZ"), "ID_CZ": adr("ID_CZ"),
            "QUERSTAB_SS": adr("QUERSTAB_SS"), "QUERSTAB_CZ": adr("QUERSTAB_CZ"),
            "IS_SS_EMPF": adr("IS_SS_EMPF"), "ID_SS_EMPF": adr("ID_SS_EMPF"),
            "IS_CZ_EMPF": adr("IS_CZ_EMPF"), "ID_CZ_EMPF": adr("ID_CZ_EMPF"),
            "ZUSATZKRIT": adr("ZUSATZKRIT"), "EMPF_KENNL": adr("EMPF_KENNL"),
            "T_AUS_MIN": adr("T_AUS_MIN"),
        },
    }


def plausibilitaet_87B(g: dict, p: dict, d: dict) -> list:
    checks = []
    if not d["aktiv"]:
        return checks

    def add(name, bezug, ergebnis, status, hinweis, korrektur=""):
        checks.append({"pruefung": name, "bezug": bezug, "ergebnis": ergebnis,
                       "status": status, "hinweis": hinweis,
                       "korrektur": korrektur if status != "OK" else ""})

    IN_ref = g["IN_ref"]

    def xino(prim):
        return (prim / IN_ref) if IN_ref else 0.0

    # Eingabe-Vollstaendigkeit Bezugsstrom
    if IN_ref <= 0:
        add("Bezugsstrom Ino vorhanden", "Ino", "—", "Fehlt",
            "Ohne Bezugsstrom Ino lassen sich die Ansprechwerte nicht in primäre Ströme "
            "umrechnen.",
            _korr("Bezugsstrom Ino [A]", "", K.ABSCHNITT_EINGABEN,
                  "mit einem Wert größer 0 A belegen."))
        return checks

    # Id> SS im Fenster 1,3 x Imax Abzw. < Id> SS < 0,8 x Iscc min
    if g["Imax_Abz"] > 0 and g["Iscc_min"] > 0:
        ss_ok = d["id_min_prim"] < d["id_ss_prim"] < d["id_max_prim"]
        add("Id> SS im Stabilitäts-/Empfindlichkeitsfenster",
            "1,3 x Imax Abzw. < Id> SS < 0,8 x Iscc min",
            f"{de(d['id_min_prim'], 0)} < {de(d['id_ss_prim'], 0)} < {de(d['id_max_prim'], 0)} A",
            "OK" if ss_ok else "Prüfen!",
            "Der Differential-Ansprechwert muss oberhalb des größten Abzweigstroms (Stabilität) "
            "und unterhalb von 80 % des kleinsten Sammelschienen-Kurzschlussstroms liegen.",
            _korr("Id> SS [x Ino]", d['adr']['ID_SS'], K.ABSCHNITT_87B,
                  f"in das Fenster {de(xino(d['id_min_prim']), 2)} ... {de(xino(d['id_max_prim']), 2)} "
                  f"x Ino (entspricht etwa {de(d['id_min_prim'], 0)} ... {de(d['id_max_prim'], 0)} A) "
                  "legen."))
        cz_ok = d["id_min_prim"] < d["id_cz_prim"] < d["id_max_prim"]
        add("Id> CZ im Stabilitäts-/Empfindlichkeitsfenster",
            "1,3 x Imax Abzw. < Id> CZ < 0,8 x Iscc min",
            f"{de(d['id_min_prim'], 0)} < {de(d['id_cz_prim'], 0)} < {de(d['id_max_prim'], 0)} A",
            "OK" if cz_ok else "Prüfen!",
            "Bemessung der Checkzone wie der selektiven Zone.",
            _korr("Id> CZ [x Ino]", d['adr']['ID_CZ'], K.ABSCHNITT_87B,
                  f"in das Fenster {de(xino(d['id_min_prim']), 2)} ... {de(xino(d['id_max_prim']), 2)} "
                  f"x Ino (entspricht etwa {de(d['id_min_prim'], 0)} ... {de(d['id_max_prim'], 0)} A) "
                  "legen."))
    else:
        add("Id>-Bemessung nicht prüfbar", "Imax Abzw. / Iscc min",
            "—", "Hinweis",
            "Ohne Imax Abzweig und Iscc min kann das Empfehlungsfenster nicht geprüft werden.",
            f"Regler 'Imax Abzweig [A]' und 'Iscc min Sammelschiene [kA]' im Abschnitt "
            f"'{K.ABSCHNITT_EINGABEN}' mit Werten größer 0 belegen.")

    # Stabilisierungsfaktor SS im zulaessigen Bereich
    st_ss = status_bereich(d["stab_ss"], K.STAB_SS_MIN, K.STAB_SS_MAX)
    add("Stab.Faktor SS im Bereich", "0,10 ... 0,80",
        f"{de(d['stab_ss'], 2)}", st_ss,
        "Der Stabilisierungsfaktor der selektiven Zone bestimmt die Kennliniensteigung.",
        _korr("Stab.-Faktor SS", d['adr']['STAB_SS'], K.ABSCHNITT_87B,
              f"in {de(K.STAB_SS_MIN, 2)} ... {de(K.STAB_SS_MAX, 2)} setzen."))

    # Stabilisierungsfaktor CZ: Empfehlung topologieabhaengig (Abweichung -> Hinweis)
    mehrfach = p.get("topologie") in K.SB_MEHRFACH
    empf_cz = K.STAB_CZ_MEHRFACH if mehrfach else d["stab_ss"]
    st_cz = _status_weich(d["stab_cz"], empf_cz)
    add("Stab.Faktor CZ topologiegerecht", "Stab.Faktor CZ",
        f"{de(d['stab_cz'], 2)} vs. Empf. {de(empf_cz, 2)}", st_cz,
        ("Bei Mehrfachsammelschienen wird 0,5 empfohlen, um Überstabilisierung zu vermeiden."
         if mehrfach else
         "Bei Einfachsammelschiene wie der selektive Faktor zu wählen."),
        _korr("Stab.-Faktor CZ", d['adr']['STAB_CZ'], K.ABSCHNITT_87B,
              _ziel(empf_cz, *K.RG_STAB_CZ)))

    # Empfindliche Kennlinie: Konsistenz und Bemessung
    if d["empf_frei"]:
        e_lt_ok = d["id_ss_e"] < d["id_ss_f"]
        add("Id empf. < Id Standard (selektiv)", "Id> SS empf. / Id> SS",
            f"{de(d['id_ss_e'], 2)} / {de(d['id_ss_f'], 2)} x Ino",
            "OK" if e_lt_ok else "Prüfen!",
            "Die empfindliche Kennlinie muss einen niedrigeren Schwellwert als die "
            "Standardkennlinie haben.",
            _korr("Id> SS empf. [x Ino]", d['adr']['ID_SS_EMPF'], K.ABSCHNITT_87B,
                  f"kleiner als Id> SS ({de(d['id_ss_f'], 2)} x Ino) setzen."))
        if g["Iscc_min"] > 0:
            st_e = _status_weich(d["id_ss_e_prim"], d["id_empf_prim"])
            add("Id> SS empf. ~ 0,7 x Iscc min", "Id> SS empf.",
                f"{de(d['id_ss_e_prim'], 0)} A vs. Empf. {de(d['id_empf_prim'], 0)} A", st_e,
                "Empfehlung: empfindlicher Schwellwert auf 70 % des kleinsten Fehlerstroms.",
                _korr("Id> SS empf. [x Ino]", d['adr']['ID_SS_EMPF'], K.ABSCHNITT_87B,
                      _ziel(xino(d['id_empf_prim']), *K.RG_ID_SS_EMPF, "x Ino",
                            d['id_empf_prim'])))
        if g["Imax_Last"] > 0:
            is_ss_e_prim = round(d["is_ss_e"] * IN_ref, 1)
            st_is = _status_weich(is_ss_e_prim, d["is_empf_prim"])
            add("Is< SS empf. ~ 1,2 x Imax Last", "Is< SS empf.",
                f"{de(is_ss_e_prim, 0)} A vs. Empf. {de(d['is_empf_prim'], 0)} A", st_is,
                "Der Stabilisierungsstrom-Grenzwert begrenzt den Wirkbereich der empfindlichen "
                "Kennlinie auf den Lastbereich.",
                _korr("Is< SS empf. [x Ino]", d['adr']['IS_SS_EMPF'], K.ABSCHNITT_87B,
                      _ziel(xino(d['is_empf_prim']), *K.RG_IS_SS_EMPF, "x Ino",
                            d['is_empf_prim'])))
        if d["zusatzkrit"] != "vorhanden":
            add("Zusatzkriterium bei empf. Kennlinie", "Zusatzkriterium",
                d["zusatzkrit"], "Hinweis",
                "Bei freigegebener empfindlicher Kennlinie kann der Ausfall eines Wandlers bei "
                "hoher Last zur Sammelschienenauslösung führen. Ein Zusatzkriterium (z.B. Freigabe "
                "durch ein Abzweigschutzgerät) erhöht die Sicherheit.",
                _korr("Zusatzkriterium für Auslösung", d['adr']['ZUSATZKRIT'], K.ABSCHNITT_87B,
                      "auf 'vorhanden' setzen."))

    # STW-Anpassung im Bereich
    if g["Anpass"] > 0:
        st_an = status_bereich(g["Anpass"], K.Anpass_min, K.Anpass_max)
        add("STW-Anpassung Ino / CT prim.", "Ino / CT prim.",
            f"{de(g['Anpass'], 2)}", st_an,
            "Der Bezugsstrom sollte in der Nähe des Wandler-Nennstroms liegen, damit die "
            "Empfindlichkeit nicht durch eine grobe Anpassung verfälscht wird.",
            f"Regler 'Bezugsstrom Ino [A]' im Abschnitt '{K.ABSCHNITT_EINGABEN}' näher an den "
            f"Wandler-Nennstrom (CT prim.) legen (Faktor {de(K.Anpass_min, 1)} ... "
            f"{de(K.Anpass_max, 1)}).")

    return checks


# -- 50BF Schalterversagerschutz (Zentraleinheit, abzweigselektiv) ------------

def schutz_50BF(g: dict, p: dict) -> dict:
    betriebsart = p.get("svs_betriebsart", K.svs_betriebsart_def)
    aktiv = (betriebsart != "Aus")
    zweistufig = betriebsart in K.SVS_BETRIEBSART_ZWEISTUFIG

    be_mode = p.get("svs_be_mode", K.svs_be_mode_def)
    i_klein = p.get("svs_i_klein", K.svs_i_klein_def)
    aus_wiederh = p.get("aus_wiederh", K.aus_wiederh_def)

    i_svs_f = p.get("i_svs", K.i_svs_def)
    i_svs_e_f = p.get("i_svs_empf", K.i_svs_empf_def)
    i_svs_prim, i_svs_sek = _prim_sek_in(i_svs_f, g)
    i_svs_e_prim, i_svs_e_sek = _prim_sek_in(i_svs_e_f, g)

    t_1p = p.get("t_svs_1p", K.t_svs_1p_def)
    t_mp = p.get("t_svs_mp", K.t_svs_mp_def)
    t_ik = p.get("t_svs_iklein", K.t_svs_iklein_def)
    t_imp = p.get("t_svs_impuls", K.t_svs_impuls_def)
    t_lsst = p.get("t_svs_ls_stoer", K.t_svs_ls_stoer_def)
    t_ausw = p.get("t_aus_wiederh", K.t_aus_wiederh_def)
    t_frueb = p.get("t_svs_frueb", K.t_svs_frueb_def)
    t_frto = p.get("t_svs_frto", K.t_svs_frto_def)
    stab_svs = p.get("stab_faktor_svs", K.stab_faktor_svs_def)
    is_svs_e = p.get("is_svs_empf", K.is_svs_empf_def)

    i_svs_empf_prim = K.I_SVS_ANTEIL_ISCC * g["Iscc_min"]   # Empfehlung 0,5 x Iscc min
    t_svs_empf = K.T_SVS_FAKTOR_LS * g["t_LS"]              # Empfehlung 2 x t_LS

    def adr(key):
        return K.ADR_get(key)

    return {
        "aktiv": aktiv, "zweistufig": zweistufig,
        "betriebsart": betriebsart, "be_mode": be_mode,
        "i_klein": i_klein, "aus_wiederh": aus_wiederh,
        "i_svs_f": i_svs_f, "i_svs_prim": i_svs_prim, "i_svs_sek": i_svs_sek,
        "i_svs_e_f": i_svs_e_f, "i_svs_e_prim": i_svs_e_prim, "i_svs_e_sek": i_svs_e_sek,
        "t_1p": t_1p, "t_mp": t_mp, "t_ik": t_ik, "t_imp": t_imp,
        "t_lsst": t_lsst, "t_ausw": t_ausw, "t_frueb": t_frueb, "t_frto": t_frto,
        "stab_svs": stab_svs, "is_svs_e": is_svs_e,
        "i_svs_empf_prim": round(i_svs_empf_prim, 1), "t_svs_empf": round(t_svs_empf, 3),
        "adr": {
            "BE_MODE": adr("SVS_BE_MODE"), "BETRIEBSART": adr("SVS_BETRIEBSART"),
            "I_KLEIN": adr("SVS_I_KLEIN"), "AUS_WIEDERH": adr("AUS_WIEDERH"),
            "I_SVS": adr("I_SVS"), "I_SVS_EMPF": adr("I_SVS_EMPF"),
            "T_1P": adr("T_SVS_1P"), "T_MP": adr("T_SVS_MP"), "T_IK": adr("T_SVS_IKLEIN"),
            "T_IMP": adr("T_SVS_IMPULS"), "T_LSST": adr("T_SVS_LS_STOER"),
            "T_AUSW": adr("T_AUS_WIEDERH"), "T_FRUEB": adr("T_SVS_FRUEB"),
            "T_FRTO": adr("T_SVS_FRTO"),
            "STAB_SVS": adr("STAB_FAKTOR_SVS"), "IS_SVS_EMPF": adr("IS_SVS_EMPF"),
        },
    }


def plausibilitaet_50BF(g: dict, p: dict, d: dict) -> list:
    checks = []

    def add(name, bezug, ergebnis, status, hinweis, korrektur=""):
        checks.append({"pruefung": name, "bezug": bezug, "ergebnis": ergebnis,
                       "status": status, "hinweis": hinweis,
                       "korrektur": korrektur if status != "OK" else ""})

    if not d["aktiv"]:
        add("Schalterversagerschutz aktiv", "SVS-Betriebsart",
            "Aus", "Hinweis",
            "Der Schalterversagerschutz ist ausgeschaltet. Bei Sammelschienen mit Mitnahme zum "
            "Leitungsgegenende ist der SVS in der Regel vorzusehen.",
            _korr("SVS-Betriebsart", d['adr']['BETRIEBSART'], K.ABSCHNITT_50BF,
                  "z.B. auf 'Verstimmung' setzen."))
        return checks

    In_prim = g["In_prim"]

    def xin(prim):
        return (prim / In_prim) if In_prim else 0.0

    # I> SVS ~ 0,5 x Iscc min (Empfehlung). Werksvoreinstellung ist plausibel, aber noch nicht
    # an die Netzdaten angepasst -> hoechstens Hinweis, kein Fehler.
    if g["Iscc_min"] > 0:
        st_i = _status_weich(d["i_svs_prim"], d["i_svs_empf_prim"])
        add("I> SVS an Netzdaten anpassen (~ 0,5 x Iscc min)", "I> SVS",
            f"{de(d['i_svs_prim'], 0)} A vs. Empf. {de(d['i_svs_empf_prim'], 0)} A", st_i,
            "Die Werksvoreinstellung ist plausibel, aber noch nicht an die eingegebenen Netzdaten "
            "angepasst. Die Stromschwelle soll sicher unterhalb des kleinsten Kurzschlussstroms "
            "ansprechen, aber nicht unnötig niedrig sein.",
            _korr("I> SVS [x In]", d['adr']['I_SVS'], K.ABSCHNITT_50BF,
                  _ziel(xin(d['i_svs_empf_prim']), *K.RG_I_SVS, "x In",
                        d['i_svs_empf_prim'])))
        below = d["i_svs_prim"] < g["Iscc_min"]
        if not below:
            add("I> SVS unterhalb Iscc min", "I> SVS / Iscc min",
                f"{de(d['i_svs_prim'], 0)} A vs. {de(g['Iscc_min'], 0)} A", "Prüfen!",
                "Liegt die Schwelle oberhalb des kleinsten Kurzschlussstroms, spricht der SVS bei "
                "schwachen Fehlern nicht an.",
                _korr("I> SVS [x In]", d['adr']['I_SVS'], K.ABSCHNITT_50BF,
                      f"deutlich unter {de(xin(g['Iscc_min']), 2)} x In (entspricht etwa "
                      f"{de(g['Iscc_min'], 0)} A) setzen."))

    # T-SVS ~ 2 x Ausschaltzeit des LS (einstufig). Wie I> SVS: hoechstens Hinweis.
    if g["t_LS"] > 0:
        st_t1 = _status_weich(d["t_1p"], d["t_svs_empf"])
        add("T-SVS-1P an Netzdaten anpassen (~ 2 x t_LS)", "T-SVS-1P",
            f"{de(d['t_1p'], 2)} s vs. Empf. {de(d['t_svs_empf'], 2)} s", st_t1,
            "Die Werksvoreinstellung ist plausibel, aber noch nicht an die eingegebene "
            "Ausschaltzeit angepasst. Die Verzögerung muss die Eigenzeit des Leistungsschalters "
            "plus Rücksetzzeit der Stromüberwachung sicher überbrücken (einstufig ca. 2 x "
            "Ausschaltzeit).",
            _korr("T-SVS-1P [s]", d['adr']['T_1P'], K.ABSCHNITT_50BF,
                  _ziel(d['t_svs_empf'], *K.RG_T_SVS, "s")))
        st_tm = _status_weich(d["t_mp"], d["t_svs_empf"])
        add("T-SVS-mP an Netzdaten anpassen (~ 2 x t_LS)", "T-SVS-mP",
            f"{de(d['t_mp'], 2)} s vs. Empf. {de(d['t_svs_empf'], 2)} s", st_tm,
            "Bemessung wie T-SVS-1P (mehrpoliger Fehler).",
            _korr("T-SVS-mP [s]", d['adr']['T_MP'], K.ABSCHNITT_50BF,
                  _ziel(d['t_svs_empf'], *K.RG_T_SVS, "s")))

    # Zweistufig: T-AUS-Wiederh < T-SVS-1P und < T-SVS-mP (Konsistenz -> ggf. Fehler)
    if d["zweistufig"]:
        ok_1p = d["t_ausw"] < d["t_1p"]
        ok_mp = d["t_ausw"] < d["t_mp"]
        st = "OK" if (ok_1p and ok_mp) else "Prüfen!"
        add("T-AUS-Wiederh. < T-SVS (zweistufig)", "T-AUS-Wiederh. / T-SVS",
            f"{de(d['t_ausw'], 2)} s vs. {de(min(d['t_1p'], d['t_mp']), 2)} s", st,
            "Im zweistufigen Betrieb muss die Auswiederholung auf den eigenen Schalter vor der "
            "Abschaltung des Sammelschienenabschnitts ablaufen.",
            _korr("T-AUS-Wiederh. [s]", d['adr']['T_AUSW'], K.ABSCHNITT_50BF,
                  f"kleiner als T-SVS-1P/mP ({de(min(d['t_1p'], d['t_mp']), 2)} s) einstellen."))

    # 1-polige Auswiederholung nur sinnvoll mit 1-pol-faehigem Anstoss
    if d["aus_wiederh"] == "1polig":
        add("Auswiederholung 1-polig", "AUS-Wiederh.",
            "1polig", "Hinweis",
            "Eine 1-polige Auswiederholung setzt einen 1-poligen Anstoss und einen 1-pol-fähigen "
            "Leistungsschalter voraus. Andernfalls auf 3-polig stellen.",
            _korr("AUS-Wiederholung", d['adr']['AUS_WIEDERH'], K.ABSCHNITT_50BF,
                  "ggf. auf '3polig' setzen."))

    return checks


# -- Reserve-Schalterversagerschutz (Feldeinheit) -----------------------------

def schutz_res_svs(g: dict, p: dict) -> dict:
    zustand = p.get("res_svs", K.res_svs_def)
    aktiv = (zustand == "Ein")
    i_f = p.get("res_svs_i", K.res_svs_i_def)
    t = p.get("res_svs_t", K.res_svs_t_def)
    i_prim, i_sek = _prim_sek_in(i_f, g)
    return {
        "aktiv": aktiv, "zustand": zustand,
        "i_f": i_f, "i_prim": i_prim, "i_sek": i_sek, "t": t,
        "adr": {
            "RES_SVS": K.ADR_get("RES_SVS"),
            "RES_SVS_I": K.ADR_get("RES_SVS_I"),
            "RES_SVS_T": K.ADR_get("RES_SVS_T"),
        },
    }


def plausibilitaet_res_svs(g: dict, p: dict, d: dict, dbf: dict) -> list:
    checks = []
    if not d["aktiv"]:
        return checks

    def add(name, bezug, ergebnis, status, hinweis, korrektur=""):
        checks.append({"pruefung": name, "bezug": bezug, "ergebnis": ergebnis,
                       "status": status, "hinweis": hinweis,
                       "korrektur": korrektur if status != "OK" else ""})

    In_prim = g["In_prim"]

    def xin(prim):
        return (prim / In_prim) if In_prim else 0.0

    # RES.SVS-I unterhalb Iscc min (Funktionsbedingung -> ggf. Fehler)
    if g["Iscc_min"] > 0:
        ok = d["i_prim"] < g["Iscc_min"]
        add("RES.SVS-I unterhalb Iscc min", "RES.SVS-I / Iscc min",
            f"{de(d['i_prim'], 0)} A vs. {de(g['Iscc_min'], 0)} A",
            "OK" if ok else "Prüfen!",
            "Die Stromschwelle des Reserve-SVS muss sicher unterhalb des kleinsten "
            "Kurzschlussstroms liegen.",
            _korr("RES.SVS-I [x In]", d['adr']['RES_SVS_I'], K.ABSCHNITT_RES,
                  f"deutlich unter {de(xin(g['Iscc_min']), 2)} x In (entspricht etwa "
                  f"{de(g['Iscc_min'], 0)} A) setzen."))

    # RES.SVS-T sollte >= zentrale SVS-Zeit (nachgeordnete Reserve -> Hinweis)
    if dbf["aktiv"]:
        t_zentral = max(dbf["t_1p"], dbf["t_mp"])
        ok_t = d["t"] >= t_zentral
        add("RES.SVS-T nachgeordnet zur zentralen SVS-Zeit", "RES.SVS-T / T-SVS",
            f"{de(d['t'], 2)} s vs. {de(t_zentral, 2)} s",
            "OK" if ok_t else "Hinweis",
            "Der Reserve-SVS soll nach dem zentralen SVS wirken, damit er nur dessen Ausfall "
            "abdeckt und nicht überfunktioniert.",
            _korr("RES.SVS-T [s]", d['adr']['RES_SVS_T'], K.ABSCHNITT_RES,
                  f"größer oder gleich {de(t_zentral, 2)} s wählen."))

    return checks


# -- 50/51 Reserve-Ueberstromzeitschutz (Feldeinheit) -------------------------

def schutz_5051(g: dict, p: dict) -> dict:
    aktiv = p.get("umz_aktiv", K.umz_aktiv_def)
    umz_p = p.get("umz_p", K.umz_p_def)
    umz_e = p.get("umz_e", K.umz_e_def)

    iph_hh = p.get("iph_hh", K.iph_hh_def)
    iph_h = p.get("iph_h", K.iph_h_def)
    ip = p.get("ip", K.ip_def)
    ie_hh = p.get("ie_hh", K.ie_hh_def)
    ie_h = p.get("ie_h", K.ie_h_def)
    iep = p.get("iep", K.iep_def)

    def stufe_in(f, t):
        prim, sek = _prim_sek_in(f, g)
        return {"f": f, "i_prim": prim, "i_sek": sek, "t": t}

    return {
        "aktiv": aktiv,
        "umz_p": umz_p, "umz_e": umz_e,
        "kennlinie_p": p.get("kennlinie_p", K.kennlinie_p_def),
        "kennlinie_e": p.get("kennlinie_e", K.kennlinie_e_def),
        "IphHH": stufe_in(iph_hh, p.get("t_iph_hh", K.t_iph_hh_def)),
        "IphH":  stufe_in(iph_h,  p.get("t_iph_h", K.t_iph_h_def)),
        "Ip":    stufe_in(ip,     p.get("t_ip", K.t_ip_def)),
        "IeHH":  stufe_in(ie_hh,  p.get("t_ie_hh", K.t_ie_hh_def)),
        "IeH":   stufe_in(ie_h,   p.get("t_ie_h", K.t_ie_h_def)),
        "Iep":   stufe_in(iep,    p.get("t_iep", K.t_iep_def)),
        "adr": {
            "UMZ_P": K.ADR_get("UMZ_P"), "IPH_HH": K.ADR_get("IPH_HH"),
            "T_IPH_HH": K.ADR_get("T_IPH_HH"), "KENNLINIE_P": K.ADR_get("KENNLINIE_P"),
            "IPH_H": K.ADR_get("IPH_H"), "T_IPH_H": K.ADR_get("T_IPH_H"),
            "IP": K.ADR_get("IP"), "T_IP": K.ADR_get("T_IP"),
            "UMZ_E": K.ADR_get("UMZ_E"), "IE_HH": K.ADR_get("IE_HH"),
            "T_IE_HH": K.ADR_get("T_IE_HH"), "KENNLINIE_E": K.ADR_get("KENNLINIE_E"),
            "IE_H": K.ADR_get("IE_H"), "T_IE_H": K.ADR_get("T_IE_H"),
            "IEP": K.ADR_get("IEP"), "T_IEP": K.ADR_get("T_IEP"),
        },
    }


def plausibilitaet_5051(g: dict, p: dict, d: dict) -> list:
    checks = []
    if not d["aktiv"]:
        return checks

    def add(name, bezug, ergebnis, status, hinweis, korrektur=""):
        checks.append({"pruefung": name, "bezug": bezug, "ergebnis": ergebnis,
                       "status": status, "hinweis": hinweis,
                       "korrektur": korrektur if status != "OK" else ""})

    In_prim = g["In_prim"]

    def xin(prim):
        return (prim / In_prim) if In_prim else 0.0

    # I> oberhalb des maximalen Betriebsstroms (Anregesicherheit -> ggf. Fehler)
    if g["Imax_Abz"] > 0:
        iph_h_prim = d["IphH"]["i_prim"]
        ok = iph_h_prim > g["Imax_Abz"]
        add("I> oberhalb max. Betriebsstrom", "I> / Imax Abzw.",
            f"{de(iph_h_prim, 0)} A vs. {de(g['Imax_Abz'], 0)} A",
            "OK" if ok else "Prüfen!",
            "Die Phasen-Überstromstufe darf nicht im Lastbereich anregen.",
            _korr("I> [x In]", d['adr']['IPH_H'], K.ABSCHNITT_RES,
                  f"oberhalb {de(xin(g['Imax_Abz']), 2)} x In (entspricht etwa "
                  f"{de(g['Imax_Abz'], 0)} A) setzen."))

    # I>> > I> (Stufenstaffelung Phasen -> ggf. Fehler)
    hh_ok = d["IphHH"]["i_prim"] > d["IphH"]["i_prim"]
    add("I>> > I> (Stufenstaffelung Phasen)", "I>> / I>",
        f"{de(d['IphHH']['f'], 2)} / {de(d['IphH']['f'], 2)} x In",
        "OK" if hh_ok else "Prüfen!",
        "Die Hochstromstufe muss oberhalb der Überstromstufe liegen.",
        _korr("I>> [x In]", d['adr']['IPH_HH'], K.ABSCHNITT_RES,
              f"größer als I> ({de(d['IphH']['f'], 2)} x In) einstellen."))

    # I>> unterhalb Iscc max (sonst spricht die Schnellstufe nie an -> Hinweis)
    if g["Iscc_max"] > 0:
        below = d["IphHH"]["i_prim"] < g["Iscc_max"]
        add("I>> unterhalb Iscc max", "I>> / Iscc max",
            f"{de(d['IphHH']['i_prim'], 0)} A vs. {de(g['Iscc_max'], 0)} A",
            "OK" if below else "Hinweis",
            "Liegt die Hochstromstufe oberhalb des maximalen Kurzschlussstroms, ist sie unwirksam.",
            _korr("I>> [x In]", d['adr']['IPH_HH'], K.ABSCHNITT_RES,
                  f"unterhalb {de(xin(g['Iscc_max']), 2)} x In (entspricht etwa "
                  f"{de(g['Iscc_max'], 0)} A) wählen."))

    # IE>> > IE> Konsistenz (-> ggf. Fehler)
    e_ok = d["IeHH"]["i_prim"] > d["IeH"]["i_prim"]
    add("IE>> > IE> (Stufenstaffelung Erde)", "IE>> / IE>",
        f"{de(d['IeHH']['f'], 2)} / {de(d['IeH']['f'], 2)} x In",
        "OK" if e_ok else "Prüfen!",
        "Die Erd-Hochstromstufe muss oberhalb der Erd-Überstromstufe liegen.",
        _korr("IE>> [x In]", d['adr']['IE_HH'], K.ABSCHNITT_RES,
              f"größer als IE> ({de(d['IeH']['f'], 2)} x In) einstellen."))

    return checks


# -- Ueberwachung (Zentraleinheit) --------------------------------------------

def schutz_ueberwachung(g: dict, p: dict) -> dict:
    aktiv = p.get("ueberw_aktiv", K.ueberw_aktiv_def)
    id_ueb = p.get("id_ueberw", K.id_ueberw_def)
    null_dg = p.get("null_dg_ueberw", K.null_dg_ueberw_def)
    id_ueb_ss = p.get("id_ueberw_ss", K.id_ueberw_ss_def)
    id_ueb_cz = p.get("id_ueberw_cz", K.id_ueberw_cz_def)
    reak_ss = p.get("id_ueberw_reak_ss", K.id_ueberw_reak_ss_def)
    reak_cz = p.get("id_ueberw_reak_cz", K.id_ueberw_reak_cz_def)
    i_null = p.get("i_null_dg", K.i_null_dg_def)
    id_ueb_ss_prim, id_ueb_ss_sek = _prim_sek_ino(id_ueb_ss, g)
    id_ueb_cz_prim, id_ueb_cz_sek = _prim_sek_ino(id_ueb_cz, g)
    return {
        "aktiv": aktiv,
        "id_ueberw": id_ueb, "null_dg": null_dg,
        "reak_ss": reak_ss, "reak_cz": reak_cz,
        "tr_laufzeit": p.get("tr_laufzeit", K.tr_laufzeit_def),
        "t_id_ueberw": p.get("t_id_ueberw", K.t_id_ueberw_def),
        "id_ueb_ss": id_ueb_ss, "id_ueb_cz": id_ueb_cz, "i_null": i_null,
        "id_ueb_ss_prim": id_ueb_ss_prim, "id_ueb_cz_prim": id_ueb_cz_prim,
        "ls_ueberw_zeit": p.get("ls_ueberw_zeit", K.ls_ueberw_zeit_def),
        "adr": {
            "TR_LAUFZEIT": K.ADR_get("TR_LAUFZEIT"), "ID_UEBERW": K.ADR_get("ID_UEBERW"),
            "T_ID_UEBERW": K.ADR_get("T_ID_UEBERW"), "ID_UEBERW_SS": K.ADR_get("ID_UEBERW_SS"),
            "ID_UEBERW_CZ": K.ADR_get("ID_UEBERW_CZ"), "NULL_DG": K.ADR_get("NULL_DG_UEBERW"),
            "I_NULL_DG": K.ADR_get("I_NULL_DG"), "LS_UEBERW_ZEIT": K.ADR_get("LS_UEBERW_ZEIT"),
            "REAK_SS": K.ADR_get("ID_UEBERW_REAK_SS"), "REAK_CZ": K.ADR_get("ID_UEBERW_REAK_CZ"),
        },
    }


def plausibilitaet_ueberwachung(g: dict, p: dict, d: dict, d87: dict) -> list:
    checks = []
    if not d["aktiv"]:
        return checks

    def add(name, bezug, ergebnis, status, hinweis, korrektur=""):
        checks.append({"pruefung": name, "bezug": bezug, "ergebnis": ergebnis,
                       "status": status, "hinweis": hinweis,
                       "korrektur": korrektur if status != "OK" else ""})

    # Id-Ueberwachung deutlich unter Ansprechwert Id> SS (Funktionsbedingung -> ggf. Fehler)
    if d["id_ueberw"] == "Ein" and d87["aktiv"]:
        ok_ss = d["id_ueb_ss"] < d87["id_ss_f"]
        add("Id-Überwachung SS unter Ansprechwert", "Id> Überw. SS / Id> SS",
            f"{de(d['id_ueb_ss'], 2)} / {de(d87['id_ss_f'], 2)} x Ino",
            "OK" if ok_ss else "Prüfen!",
            "Die Überwachungsschwelle muss unterhalb des Schutzansprechwerts liegen, damit "
            "schleichende Fehler vor der Auslösung gemeldet werden.",
            _korr("Id> Überw. SS [x Ino]", d['adr']['ID_UEBERW_SS'], K.ABSCHNITT_UEBERW,
                  f"kleiner als Id> SS ({de(d87['id_ss_f'], 2)} x Ino) setzen."))
        ok_cz = d["id_ueb_cz"] < d87["id_cz_f"]
        add("Id-Überwachung CZ unter Ansprechwert", "Id> Überw. CZ / Id> CZ",
            f"{de(d['id_ueb_cz'], 2)} / {de(d87['id_cz_f'], 2)} x Ino",
            "OK" if ok_cz else "Prüfen!",
            "Wie Id-Überwachung der selektiven Zone.",
            _korr("Id> Überw. CZ [x Ino]", d['adr']['ID_UEBERW_CZ'], K.ABSCHNITT_UEBERW,
                  f"kleiner als Id> CZ ({de(d87['id_cz_f'], 2)} x Ino) setzen."))

    # T-Id-Ueberwachung im Bereich 1 ... 10 s
    st_t = status_bereich(d["t_id_ueberw"], 1.0, 10.0)
    add("T-Id-Überwachung im Bereich", "1,00 ... 10,00 s",
        f"{de(d['t_id_ueberw'], 2)} s", st_t,
        "Die Verzögerung muss lang genug sein, um transiente Differenzströme nicht zu melden.",
        _korr("T-Id-Überw. [s]", d['adr']['T_ID_UEBERW'], K.ABSCHNITT_UEBERW,
              "in 1,00 ... 10,00 s setzen."))

    return checks


# -- Geraete-/Architektur-Empfehlung ------------------------------------------

def geraeteempfehlung(p: dict) -> dict:
    topo = p.get("topologie", K.SB_TOPOLOGIE_OPTIONEN[0])
    n_abz = int(p.get("anzahl_abzweige", 0))
    mehrfach = topo in K.SB_MEHRFACH

    haupt = ("Dezentraler Sammelschienenschutz SIPROTEC 7SS52: eine Zentraleinheit plus je "
             f"Abzweig eine Feldeinheit ({n_abz} Feldeinheiten bei {n_abz} Abzweigen).")
    if mehrfach:
        hinweis = ("Mehrfachsammelschiene: die selektive Zone wird über das Trennerabbild den "
                   "Sammelschienenabschnitten zugeordnet, die Checkzone gibt frei. "
                   "Stabilisierungsfaktor der Checkzone 0,5 zur Vermeidung der Überstabilisierung.")
    else:
        hinweis = ("Einfachsammelschiene: selektive Zone und Checkzone erfassen denselben "
                   "Schutzbereich. Stabilisierungsfaktoren von SS und CZ können gleich gewählt "
                   "werden.")
    return {"haupt": haupt, "hinweis": hinweis, "topologie": topo,
            "anzahl_abzweige": n_abz, "mehrfach": mehrfach}


# -- Einstiegspunkt -----------------------------------------------------------

def berechne_alle(p: dict) -> dict:
    g    = grundgroessen(p)
    d87  = schutz_87B(g, p)
    dbf  = schutz_50BF(g, p)
    dres = schutz_res_svs(g, p)
    d50  = schutz_5051(g, p)
    dueb = schutz_ueberwachung(g, p)
    plaus = (plausibilitaet_87B(g, p, d87)
             + plausibilitaet_50BF(g, p, dbf)
             + plausibilitaet_res_svs(g, p, dres, dbf)
             + plausibilitaet_5051(g, p, d50)
             + plausibilitaet_ueberwachung(g, p, dueb, d87))
    geh  = geraeteempfehlung(p)
    return {
        "grund": g,
        "87B": d87, "50BF": dbf, "RES_SVS": dres,
        "50/51": d50, "ueberwachung": dueb,
        "plausibilitaet": plaus,
        "empfehlung": geh,
    }
