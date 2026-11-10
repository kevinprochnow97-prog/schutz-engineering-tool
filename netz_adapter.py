"""
netz_adapter.py - Bruecke zwischen Netzmodell und den Rechenkernen calc_<bm>.py
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reines Python-Modul OHNE Streamlit (isoliert testbar).

Einstieg: erzeuge_schutzstufen(netz) -> AdapterErgebnis

Aufgabe:
  1. Fuer jedes Element den vollstaendigen Parametersatz bilden (p_voll):
     Parametersatz des Elements + Werte der angeschlossenen Knoten
     (UN, Ik, Sternpunkt). Der Knoten ist die Wahrheit und ueberschreibt p.
  2. Die bestehenden Rechenkerne unveraendert aufrufen
     (grundgroessen + 50/51-Funktion je Betriebsmittel).
  3. Die unterschiedlichen Ergebnisformate in eine einheitliche Liste von
     Schutzstufen uebersetzen. Diese Liste ist die Eingabe fuer die
     Staffelung (netz_selektivitaet.py, Woche 2).

Die Rechenkerne werden NICHT veraendert. Alle Werte (Faktoren, Zeiten,
Kennlinien) stammen aus ihnen bzw. aus den Werksvoreinstellungen in
konstanten_<bm>.py. Der Adapter rechnet selbst nichts Fachliches.

Robustheit: Ein Element mit fehlenden Pflichtfeldern oder einem Fehler im
Rechenkern liefert eine Meldung und keine Stufen. Der Adapter wirft nie.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import calc_leitung
import calc_motor
import calc_trafo
import konstanten_leitung
import konstanten_motor
import konstanten_trafo
from netz_modell import Netz
from netz_topologie import FEHLER, HINWEIS, WARNUNG, Meldung, analysiere

UMZ = "UMZ"   # unabhaengige Kennlinie (stromunabhaengige Verzoegerung)

# ── Sternpunkt: Modellschluessel -> Text des jeweiligen Tabs ─────────────────
# Die Tabs verwenden unterschiedliche Texte (z. B. "Direkt geerdet" im Trafo-Tab,
# "Starr geerdet" im Leitungs-Tab). Ein Test prueft, dass jeder Text hier in der
# Optionsliste des Tabs existiert, damit eine Umbenennung im Tab auffaellt.
STP_TRAFO = {
    "isoliert": "Isoliert",
    "kompensiert": "Kompensiert (Petersen)",
    "niederohmig": "Niederohmig geerdet",
    "direkt": "Direkt geerdet",
}
STP_LEITUNG = {
    "isoliert": "Isoliert",
    "kompensiert": "Kompensiert (Petersen)",
    "niederohmig": "Niederohmig geerdet",
    "direkt": "Starr geerdet",
}
# Der Motor-Tab kennt kein starr geerdetes Netz. Tool-Vorgabe: als niederohmig
# behandeln (Stromkriterium 50N/51N) und darauf hinweisen.
STP_MOTOR = {
    "isoliert": "Isoliert",
    "kompensiert": "Kompensiert (Petersen-Spule)",
    "niederohmig": "Niederohmig geerdet",
    "direkt": "Niederohmig geerdet",
}

# Pflichtfelder je Typ fuer die 50/51-Stufen. Spannungen, Ik und Sternpunkt
# kommen aus den Knoten und stehen deshalb nicht hier.
PFLICHT = {
    "trafo":   ("Sn_MVA", "uk_pct", "CT_OS_Prim", "CT_OS_Sek", "CT_US_Prim", "CT_US_Sek"),
    "leitung": ("IN_Ltg", "CT_Prim", "CT_Sek"),
    "motor":   ("CT_Prim", "CT_Sek"),     # dazu Pn_kW oder IN_direkt, siehe _fehlende_felder
}

# Optionale Zahlenfelder, die die Rechenkerne ohne Typpruefung verwenden.
# Steht dort keine gueltige Zahl, wird das Feld verworfen (Werksvoreinstellung
# greift) und gemeldet. Sonst koennte z. B. ein Text in IN_direkt den
# Motor-Rechenkern zum Absturz bringen.
OPTIONAL_ZAHL = {
    "trafo":   ("Stufensteller_pm", "Ik_max_OS_kA", "Ik_max_US_kA", "k_S_IGG",
                "f_I_Ph", "t_I_Ph", "t_I_Ph_HH", "f_I_Ph_HH_OS", "f_I_Ph_HH_US",
                "t_I_Ph_US", "t_I_Ph_HH_US"),
    "leitung": ("L_km", "X_Belag", "phi_Ltg", "Ik_max_kA", "Ik_min_kA",
                "iph_h", "t_iph_h", "iph_hh", "t_iph_hh"),
    "motor":   ("Pn_kW", "IN_direkt", "cos_phi", "eta", "I_Anlauf_Verh", "t_Anlauf",
                "f_50_2", "t_50_2", "f_50_1", "t_50_1", "f_51", "T_51"),
}


@dataclass(frozen=True)
class Schutzstufe:
    element: str          # Element-ID
    stufe: str            # Anzeige, z. B. "I>", "I>>", "Ip", "I> NB"
    ansi: str             # "50" (UMZ-Hochstrom), "51" (Grund- bzw. AMZ-Stufe)
    messort: str          # Knoten-ID, an dem der Wandler sitzt
    UN_kV: float          # Spannung am Messort (fuer die Umrechnung in Woche 2)
    I_prim_A: float       # Ansprechwert primaer
    kennlinie: str        # "UMZ" oder Kennlinienname des Rechenkerns
    t_s: float | None     # Verzoegerung bei UMZ
    T_mult: float | None  # Zeitmultiplikator bei AMZ
    aktiv: bool
    quelle: str           # Herkunft, z. B. "calc_trafo.schutz_5051_phase (OS)"
    hinweis: str = ""


@dataclass
class AdapterErgebnis:
    stufen: list = field(default_factory=list)
    meldungen: list = field(default_factory=list)
    p_voll: dict = field(default_factory=dict)      # Element-ID -> vollstaendiger Parametersatz
    topologie: object = None

    @property
    def ok(self) -> bool:
        return not any(m.stufe == FEHLER for m in self.meldungen)

    def stufen_von(self, element_id: str) -> list:
        return [s for s in self.stufen if s.element == element_id]


# ── Parametersatz vervollstaendigen ──────────────────────────────────────────
def _setze_ik(p: dict, schluessel: str, wert) -> None:
    """Ik nur uebernehmen, wenn am Knoten vorhanden. Sonst bleibt ein Tab-Wert stehen."""
    if wert is not None:
        p[schluessel] = wert


def baue_p_voll(netz: Netz, element_id: str, zuspeisung: str | None = None) -> dict:
    """
    Parametersatz des Elements plus Knotenwerte. Knoten ueberschreiben p.
    zuspeisung: Knoten, von dem aus das Element versorgt wird (aus der Topologie).
    Fuer Leitungen bestimmt er Anfang (Ik max) und Ende (Ik min).
    """
    kn = netz.knoten
    e = netz.elemente[element_id]
    p = dict(e.p)
    if e.typ == "trafo":
        os_, us = kn[e.von], kn[e.nach]
        p["UN_OS_kV"], p["UN_US_kV"] = os_.UN_kV, us.UN_kV
        p["stp_OS"], p["stp_US"] = STP_TRAFO[os_.sternpunkt], STP_TRAFO[us.sternpunkt]
        _setze_ik(p, "Ik_max_OS_kA", os_.Ik_max_kA)
        _setze_ik(p, "Ik_max_US_kA", us.Ik_max_kA)
    elif e.typ == "leitung":
        anfang = zuspeisung if zuspeisung in (e.von, e.nach) else e.von
        ende = e.nach if anfang == e.von else e.von
        p["UN_kV"] = kn[anfang].UN_kV
        p["sternpunkt_netz"] = STP_LEITUNG[kn[anfang].sternpunkt]
        _setze_ik(p, "Ik_max_kA", kn[anfang].Ik_max_kA)
        _setze_ik(p, "Ik_min_kA", kn[ende].Ik_min_kA)
    elif e.typ == "motor":
        k = kn[e.von]
        p["UN_kV"] = k.UN_kV
        p["stp_Netz"] = STP_MOTOR[k.sternpunkt]
    return p


def _ist_zahl(v) -> bool:
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and v == v and v not in (float("inf"), float("-inf")))


def _verwerfe_ungueltige(typ: str, p: dict) -> list:
    """Optionale Felder ohne gueltige Zahl aus p entfernen. Gibt die Feldnamen zurueck."""
    weg = [k for k in OPTIONAL_ZAHL.get(typ, ()) if k in p and p[k] is not None and not _ist_zahl(p[k])]
    for k in weg:
        del p[k]
    return weg


def _fehlende_felder(typ: str, p: dict) -> list:
    def leer(k):
        v = p.get(k)
        return not _ist_zahl(v) or v <= 0
    fehlt = [k for k in PFLICHT.get(typ, ()) if leer(k)]
    if typ == "motor" and leer("IN_direkt") and leer("Pn_kW"):
        fehlt.append("Pn_kW oder IN_direkt")
    return fehlt


# ── Uebersetzung je Betriebsmittel ───────────────────────────────────────────
def _stufen_trafo(eid, e, p, kn) -> list:
    g = calc_trafo.grundgroessen(p)
    r = calc_trafo.schutz_5051_phase(g, p)
    q = "calc_trafo.schutz_5051_phase"
    stufen = []
    for seite, ort in (("OS", e.von), ("US", e.nach)):
        UN = kn[ort].UN_kV
        stufen.append(Schutzstufe(eid, f"I> {seite}", "51", ort, UN, r[seite]["I_prim"],
                                  UMZ, r[seite]["t_I"], None, True, f"{q} ({seite})"))
        stufen.append(Schutzstufe(eid, f"I>> {seite}", "50", ort, UN, r[seite]["IHH_prim"],
                                  UMZ, r[seite]["t_IHH"], None, True, f"{q} ({seite})"))
    return stufen


def _stufen_leitung(eid, e, p, kn, anfang) -> list:
    g = calc_leitung.grundgroessen(p)
    r = calc_leitung.schutz_5051(g, p)
    q = "calc_leitung.schutz_5051"
    UN = kn[anfang].UN_kV
    if r["betriebsart"] == "Ein: immer aktiv":
        hinweis = ""
    elif r["aktiv"]:
        hinweis = ("Not-UMZ nur bei Spannungsausfall wirksam. Für die Staffelung im "
                   "Strahlennetz Betriebsart 'Ein: immer aktiv' wählen.")
    else:
        hinweis = "Not-UMZ ausgeschaltet."
    return [
        Schutzstufe(eid, "Iph>", "51", anfang, UN, r["IphH"]["i_prim"], UMZ,
                    r["IphH"]["t"], None, r["aktiv"], q, hinweis),
        Schutzstufe(eid, "Iph>>", "50", anfang, UN, r["IphHH"]["i_prim"], UMZ,
                    r["IphHH"]["t"], None, r["aktiv"], q, hinweis),
    ]


def _stufen_motor(eid, e, p, kn) -> list:
    g = calc_motor.grundgroessen(p)
    r = calc_motor.schutz_5051(g, p)
    q = "calc_motor.schutz_5051"
    UN = kn[e.von].UN_kV
    return [
        Schutzstufe(eid, "Ip", "51", e.von, UN, r["I_51_prim"], r["kennlinie"],
                    None, r["T_51"], True, q),
        Schutzstufe(eid, "I> (50-1)", "50", e.von, UN, r["I_50_1_prim"], UMZ,
                    r["t_50_1"], None, True, q),
        Schutzstufe(eid, "I>> (50-2)", "50", e.von, UN, r["I_50_2_prim"], UMZ,
                    r["t_50_2"], None, True, q),
    ]


def _stufen_einspeisung(eid, e, p, kn) -> tuple:
    """Schutz des Netzbetreibers am Uebergabepunkt: feste Obergrenze der Staffelung."""
    I, t = p.get("I_gt_NB_A"), p.get("t_gt_NB_s")
    if not (isinstance(I, (int, float)) and I > 0 and isinstance(t, (int, float)) and t > 0):
        return [], [Meldung(
            HINWEIS,
            f"{eid}: Kein Schutz des Netzbetreibers vorgegeben (I_gt_NB_A, t_gt_NB_s). "
            f"Die Staffelung hat dann keine feste Obergrenze.", (eid,))]
    UN = kn[e.nach].UN_kV
    return [Schutzstufe(eid, "I> NB", "51", e.nach, UN, float(I), UMZ, float(t), None, True,
                        "Vorgabe Netzbetreiber (Element-Parameter)")], []


# ── Einstieg ─────────────────────────────────────────────────────────────────
def erzeuge_schutzstufen(netz: Netz, topologie=None) -> AdapterErgebnis:
    topo = topologie if topologie is not None else analysiere(netz)
    erg = AdapterErgebnis(topologie=topo)
    if not topo.ok:
        erg.meldungen.append(Meldung(
            FEHLER, "Die Topologie enthält Fehler. Schutzstufen werden erst danach erzeugt."))
        return erg

    kn = netz.knoten
    # Zuspeiseknoten je Element aus dem Versorgungsbaum
    zusp = {}
    for k, eid in topo.zufuehrung.items():
        e = netz.elemente[eid]
        zusp[eid] = e.von if e.nach == k else e.nach

    for eid, e in sorted(netz.elemente.items()):
        if e.zustand != "ein":
            continue
        if e.typ == "kupplung":
            continue                     # Tool-Vorgabe: Kupplung ohne eigenen Schutz
        if e.typ == "generator":
            erg.meldungen.append(Meldung(
                HINWEIS, f"{eid}: Generatoren werden in der Staffelung noch nicht berücksichtigt.",
                (eid,)))
            continue
        if e.typ == "einspeisung":
            st, m = _stufen_einspeisung(eid, e, e.p, kn)
            erg.stufen += st
            erg.meldungen += m
            continue
        # Kanten ausserhalb des Versorgungsbaums (z. B. offene Ringseite) haben keinen
        # eindeutigen Messort. Motoren haengen immer an ihrem von-Knoten.
        if e.typ in ("trafo", "leitung") and eid not in zusp:
            continue
        if e.typ == "motor" and e.von in topo.unversorgt:
            continue

        p = baue_p_voll(netz, eid, zusp.get(eid))
        verworfen = _verwerfe_ungueltige(e.typ, p)
        if verworfen:
            erg.meldungen.append(Meldung(
                WARNUNG, f"{eid}: Keine gültige Zahl in {', '.join(verworfen)}. "
                         f"Feld ignoriert, es gilt die Werksvoreinstellung.", (eid,)))
        erg.p_voll[eid] = p
        fehlt = _fehlende_felder(e.typ, p)
        if fehlt:
            erg.meldungen.append(Meldung(
                WARNUNG, f"{eid}: Es fehlen {', '.join(fehlt)}. Keine Schutzstufen.", (eid,)))
            continue
        if e.typ == "motor" and kn[e.von].sternpunkt == "direkt":
            erg.meldungen.append(Meldung(
                HINWEIS, f"{eid}: Der Motor-Tab kennt kein starr geerdetes Netz, "
                         f"gerechnet wird mit 'niederohmig geerdet' (Tool-Vorgabe).", (eid,)))
        try:
            if e.typ == "trafo":
                erg.stufen += _stufen_trafo(eid, e, p, kn)
            elif e.typ == "leitung":
                erg.stufen += _stufen_leitung(eid, e, p, kn, zusp[eid])
            elif e.typ == "motor":
                erg.stufen += _stufen_motor(eid, e, p, kn)
        except Exception as exc:          # Rechenkern darf die Oberflaeche nie abstuerzen lassen
            erg.meldungen.append(Meldung(
                FEHLER, f"{eid}: Rechenkern meldet {type(exc).__name__}: {exc}", (eid,)))

    for s in erg.stufen:
        if s.hinweis and s.stufe in ("Iph>",):
            erg.meldungen.append(Meldung(WARNUNG, f"{s.element}: {s.hinweis}", (s.element,)))
    return erg
