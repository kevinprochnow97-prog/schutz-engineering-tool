"""
netz_parameter.py - Parameter-Editor fuer Netzelemente (Logik ohne Streamlit)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Variante 1 der Parameterbearbeitung (docs/tool_vorgabe_bedienung.md, Abschnitt 3):
Die netzrelevanten Parameter eines Elements werden direkt am Modell bearbeitet, ohne
Eingriff in die Betriebsmittel-Tabs. Geschrieben wird ausschliesslich ueber
Netz.parameter_setzen, also atomar (erst alles pruefen, dann ersetzen).

Welche Felder es gibt: FELDER[typ] fuehrt genau die Schluessel, die der Adapter
(netz_adapter: PFLICHT, OPTIONAL_ZAHL) und die Kurzschlussrechnung (netz_kurzschluss)
aus dem Parametersatz lesen. Alle anderen Schluessel des Parametersatzes (alles, was ein
Tab sonst noch mitgibt) bleiben beim Speichern unberuehrt. Ik-Werte stehen hier nicht:
die Knoten sind die Wahrheit dafuer.

Regeln:
- Leeres Feld = Schluessel aus dem Parametersatz entfernen. Dann gilt die
  Werksvoreinstellung der Rechenkerne bzw. die Tool-Vorgabe (steht als Hinweis am Feld).
- Es wird nichts verworfen, ohne dass es der Nutzer sieht: Fehler werden gesammelt und
  alle zusammen gemeldet, der Parametersatz bleibt dann unveraendert.
- Pflichtfelder duerfen leer bleiben. Der Adapter meldet fehlende Felder je Element.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import konstanten_leitung
import konstanten_motor
import konstanten_netz
import konstanten_trafo
from netz_modell import ModellFehler, Netz

ZAHL = "zahl"
WAHL = "wahl"

G_GRUND = "Grunddaten"
G_WANDLER = "Stromwandler"
G_SCHUTZ = "Schutzeinstellungen (50/51)"
G_NB = "Schutz des Netzbetreibers"
G_KS = "Kurzschlussrechnung (optional)"


@dataclass(frozen=True)
class Feld:
    key: str
    label: str
    einheit: str = ""
    gruppe: str = G_GRUND
    art: str = ZAHL
    minimum: float = 0.0
    min_inklusive: bool = False     # False: Wert muss groesser als minimum sein
    maximum: float | None = None
    optionen: tuple = ()
    vorgabe: str = ""               # Hinweis, was bei leerem Feld gilt
    pflicht: bool = False

    @property
    def titel(self) -> str:
        return f"{self.label} [{self.einheit}]" if self.einheit else self.label


def _d(modul, name: str, einheit: str = "") -> str:
    """Werksvoreinstellung aus den Konstanten als Hinweistext (Dezimalkomma)."""
    wert = getattr(modul, name)
    text = f"{wert:g}".replace(".", ",") if isinstance(wert, (int, float)) else str(wert)
    return f"Werksvoreinstellung {text}{(' ' + einheit) if einheit else ''}"


_KT, _KL, _KM = konstanten_trafo, konstanten_leitung, konstanten_motor

FELDER: dict = {
    "einspeisung": (
        Feld("Sk_max_MVA", "Sk″ max", "MVA", G_GRUND),
        Feld("Sk_min_MVA", "Sk″ min", "MVA", G_GRUND),
        Feld("I_gt_NB_A", "I> Netzbetreiber", "A", G_NB, vorgabe="kein Schutz des Netzbetreibers"),
        Feld("t_gt_NB_s", "t Netzbetreiber", "s", G_NB, vorgabe="kein Schutz des Netzbetreibers"),
        Feld("RX_Q", "R/X der Einspeisung", "", G_KS, min_inklusive=True,
             vorgabe=f"Tool-Vorgabe {str(konstanten_netz.RX_Q_def).replace('.', ',')}"),
    ),
    "trafo": (
        Feld("Sn_MVA", "Sn", "MVA", G_GRUND, pflicht=True),
        Feld("uk_pct", "uk", "%", G_GRUND, pflicht=True),
        Feld("Schaltgruppe", "Schaltgruppe", "", G_GRUND, art=WAHL, optionen=tuple(_KT.SCHALTGRUPPEN)),
        Feld("Stufensteller_pm", "Stufensteller ±", "%", G_GRUND, min_inklusive=True, maximum=40.0,
             vorgabe="kein Stufensteller"),
        Feld("CT_OS_Prim", "CT OS primär", "A", G_WANDLER, pflicht=True),
        Feld("CT_OS_Sek", "CT OS sekundär", "A", G_WANDLER, pflicht=True),
        Feld("CT_US_Prim", "CT US primär", "A", G_WANDLER, pflicht=True),
        Feld("CT_US_Sek", "CT US sekundär", "A", G_WANDLER, pflicht=True),
        Feld("f_I_Ph", "I> Ansprechwert", "× IN", G_SCHUTZ, vorgabe=_d(_KT, "f_I_Ph_def", "× IN")),
        Feld("t_I_Ph", "t I> OS", "s", G_SCHUTZ, min_inklusive=True, vorgabe=_d(_KT, "t_I_Ph_def", "s")),
        Feld("t_I_Ph_US", "t I> US", "s", G_SCHUTZ, min_inklusive=True, vorgabe="wie OS-Seite"),
        Feld("f_I_Ph_HH_OS", "I>> OS Ansprechwert", "× IN", G_SCHUTZ,
             vorgabe="automatisch aus uk bzw. Ik max US"),
        Feld("t_I_Ph_HH", "t I>> OS", "s", G_SCHUTZ, min_inklusive=True,
             vorgabe=_d(_KT, "t_I_Ph_HH_def", "s")),
        Feld("f_I_Ph_HH_US", "I>> US Ansprechwert", "× IN", G_SCHUTZ,
             vorgabe=_d(_KT, "f_I_Ph_HH_def", "× IN")),
        Feld("t_I_Ph_HH_US", "t I>> US", "s", G_SCHUTZ, min_inklusive=True, vorgabe="wie OS-Seite"),
        Feld("ukr_pct", "ukr (Wirkanteil von uk)", "%", G_KS, min_inklusive=True,
             vorgabe="R = 0 (Tool-Vorgabe)"),
    ),
    "leitung": (
        Feld("L_km", "Länge", "km", G_GRUND),
        Feld("X_Belag", "X′-Belag", "Ω/km", G_GRUND),
        Feld("phi_Ltg", "Leitungswinkel φ", "°", G_GRUND, maximum=90.0),
        Feld("IN_Ltg", "Dauerstrom IN", "A", G_GRUND, pflicht=True),
        Feld("CT_Prim", "CT primär", "A", G_WANDLER, pflicht=True),
        Feld("CT_Sek", "CT sekundär", "A", G_WANDLER, pflicht=True),
        Feld("uebs_betriebsart", "Betriebsart Not-UMZ", "", G_SCHUTZ, art=WAHL,
             optionen=tuple(_KL.UEBS_BETRIEBSART_OPTIONEN),
             vorgabe=_d(_KL, "uebs_betriebsart_def")),
        Feld("iph_h", "Iph> Ansprechwert", "× IN", G_SCHUTZ, vorgabe=_d(_KL, "iph_h_def", "× IN")),
        Feld("t_iph_h", "t Iph>", "s", G_SCHUTZ, min_inklusive=True, vorgabe=_d(_KL, "t_iph_h_def", "s")),
        Feld("iph_hh", "Iph>> Ansprechwert", "× IN", G_SCHUTZ, vorgabe=_d(_KL, "iph_hh_def", "× IN")),
        Feld("t_iph_hh", "t Iph>>", "s", G_SCHUTZ, min_inklusive=True,
             vorgabe=_d(_KL, "t_iph_hh_def", "s")),
        Feld("R_Belag", "R′-Belag", "Ω/km", G_KS, min_inklusive=True,
             vorgabe="aus X′ und φ, sonst R′ = 0"),
        Feld("theta_min_C", "Leitertemperatur für Ik min", "°C", G_KS, min_inklusive=True,
             minimum=20.0, maximum=250.0,
             vorgabe=f"Tool-Vorgabe {konstanten_netz.theta_Leiter_min_C:g} °C"),
    ),
    "motor": (
        Feld("Pn_kW", "Pn", "kW", G_GRUND),
        Feld("IN_direkt", "IN direkt (statt Pn)", "A", G_GRUND),
        Feld("cos_phi", "cos φ", "", G_GRUND, maximum=1.0, vorgabe=_d(_KM, "cos_phi_def")),
        Feld("eta", "Wirkungsgrad η", "", G_GRUND, maximum=1.0, vorgabe=_d(_KM, "eta_def")),
        Feld("I_Anlauf_Verh", "Anlaufstrom I_A/IN", "", G_GRUND, vorgabe=_d(_KM, "I_Anlauf_Verh_def")),
        Feld("t_Anlauf", "Anlaufzeit", "s", G_GRUND, vorgabe=_d(_KM, "t_Anlauf_def", "s")),
        Feld("CT_Prim", "CT primär", "A", G_WANDLER, pflicht=True),
        Feld("CT_Sek", "CT sekundär", "A", G_WANDLER, pflicht=True),
        Feld("anlauf_gesperrt", "Anlauf im Gerät gesperrt (50-1)", "", G_SCHUTZ, art=WAHL,
             optionen=("nein", "ja"),
             vorgabe="Tool-Vorgabe nein. Mit ja gilt 50-1 beim Anlauf als gesperrt "
                     "(Blockierlogik im Gerät), die Anlaufprüfung entfällt für diese Stufe"),
        Feld("f_51", "51 Ansprechwert", "× IN", G_SCHUTZ, vorgabe=_d(_KM, "f_51_def", "× IN")),
        Feld("T_51", "51 Zeitfaktor", "s", G_SCHUTZ, vorgabe=_d(_KM, "T_51_def", "s")),
        Feld("f_50_1", "50-1 Ansprechwert", "× IN", G_SCHUTZ, vorgabe=_d(_KM, "f_50_1_def", "× IN")),
        Feld("t_50_1", "t 50-1", "s", G_SCHUTZ, min_inklusive=True, vorgabe=_d(_KM, "t_50_1_def", "s")),
        Feld("f_50_2", "50-2 Ansprechwert", "× IN", G_SCHUTZ, vorgabe=_d(_KM, "f_50_2_def", "× IN")),
        Feld("t_50_2", "t 50-2", "s", G_SCHUTZ, min_inklusive=True, vorgabe=_d(_KM, "t_50_2_def", "s")),
        Feld("RX_M", "R/X des Motors", "", G_KS, min_inklusive=True,
             vorgabe=f"Tool-Vorgabe {str(konstanten_netz.RX_M_HS).replace('.', ',')} "
                     f"(über 1 kV), {str(konstanten_netz.RX_M_NS).replace('.', ',')} (bis 1 kV)"),
    ),
}


def hat_felder(typ: str) -> bool:
    return typ in FELDER


def felder(typ: str) -> tuple:
    return FELDER.get(typ, ())


def gruppen(typ: str) -> list:
    """Gruppen in der Reihenfolge der Felder."""
    out = []
    for f in felder(typ):
        if f.gruppe not in out:
            out.append(f.gruppe)
    return out


# ── Lesen ────────────────────────────────────────────────────────────────────
def _ist_zahl(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _element(netz: Netz, eid: str):
    e = netz.elemente.get(eid)
    if e is None:
        raise ModellFehler(f"Element {eid} existiert nicht.")
    if e.typ not in FELDER:
        raise ModellFehler(f"Element {eid}: Für Typ {e.typ} gibt es keine bearbeitbaren Parameter.")
    return e


def parameter_werte(netz: Netz, eid: str) -> dict:
    """
    Aktueller Wert je Feld fuer die Vorbelegung. None, wenn der Schluessel fehlt oder
    keinen passenden Wert hat (dann gilt die Voreinstellung).
    """
    e = _element(netz, eid)
    out = {}
    for f in FELDER[e.typ]:
        v = e.p.get(f.key)
        if f.art == ZAHL:
            out[f.key] = float(v) if _ist_zahl(v) else None
        else:
            out[f.key] = v if isinstance(v, str) and v in f.optionen else None
    return out


# ── Pruefen ──────────────────────────────────────────────────────────────────
def _pruefe_feld(f: Feld, wert) -> str | None:
    """Fehlertext oder None. wert ist nicht None."""
    if f.art == WAHL:
        if wert not in f.optionen:
            return f"{f.label}: {wert!r} ist nicht zulässig. Erlaubt: {', '.join(f.optionen)}."
        return None
    if isinstance(wert, bool) or not _ist_zahl(wert):
        return f"{f.label}: Zahl erwartet, erhalten {wert!r}."
    if f.min_inklusive and wert < f.minimum:
        return f"{f.label}: muss mindestens {f.minimum:g} sein, erhalten {wert:g}."
    if not f.min_inklusive and wert <= f.minimum:
        return f"{f.label}: muss größer als {f.minimum:g} sein, erhalten {wert:g}."
    if f.maximum is not None and wert > f.maximum:
        return f"{f.label}: darf höchstens {f.maximum:g} sein, erhalten {wert:g}."
    return None


def _querpruefung(typ: str, p: dict) -> list:
    """Beziehungen zwischen Feldern, die der Rechenkern oder die Kurzschlussrechnung braucht."""
    fehler = []
    if typ == "trafo":
        uk, ukr = p.get("uk_pct"), p.get("ukr_pct")
        if _ist_zahl(uk) and _ist_zahl(ukr) and ukr >= uk:
            fehler.append(f"ukr ({ukr:g} %) muss kleiner als uk ({uk:g} %) sein.")
    if typ == "einspeisung":
        smax, smin = p.get("Sk_max_MVA"), p.get("Sk_min_MVA")
        if _ist_zahl(smax) and _ist_zahl(smin) and smin > smax:
            fehler.append(f"Sk″ min ({smin:g} MVA) ist größer als Sk″ max ({smax:g} MVA).")
        if _ist_zahl(p.get("I_gt_NB_A")) != _ist_zahl(p.get("t_gt_NB_s")):
            fehler.append("Schutz des Netzbetreibers: I> und t gehören zusammen, "
                          "entweder beide angeben oder beide leer lassen.")
    return fehler


def _text(v) -> str:
    return "leer" if v is None else (f"{v:g}".replace(".", ",") if _ist_zahl(v) else str(v))


def parameter_aendern(netz: Netz, eid: str, werte: dict) -> str:
    """
    Parameter eines Elements setzen. werte: Feldschluessel -> Zahl, Text oder None (leer).
    Schluessel, die nicht in werte stehen, bleiben unveraendert, ebenso alle Schluessel
    ausserhalb der Feldliste. Bei Fehlern wird nichts geschrieben (ModellFehler mit allen
    Fehlern, einer je Zeile).
    """
    e = _element(netz, eid)
    bekannt = {f.key: f for f in FELDER[e.typ]}
    unbekannt = sorted(set(werte) - set(bekannt))
    if unbekannt:
        raise ModellFehler(f"Element {eid}: Unbekannte Parameter: {', '.join(unbekannt)}.")
    p = dict(e.p)
    fehler, geaendert = [], []
    for key, f in bekannt.items():
        if key not in werte:
            continue
        neu = werte[key]
        if neu == "":
            neu = None
        if neu is not None:
            msg = _pruefe_feld(f, neu)
            if msg:
                fehler.append(msg)
                continue
        alt = p.get(key)
        if neu is None:
            if key in p:
                if alt is not None:
                    geaendert.append(f"{f.label} {_text(alt)} → leer")
                del p[key]
        elif alt != neu:                         # 150 und 150.0 sind gleich: nichts anfassen
            geaendert.append(f"{f.label} {_text(alt)} → {_text(neu)}")
            p[key] = float(neu) if f.art == ZAHL else neu
    fehler += _querpruefung(e.typ, p)
    if fehler:
        raise ModellFehler("\n".join(fehler))
    if not geaendert:
        return f"{eid}: keine Änderung an den Parametern."
    netz.parameter_setzen(eid, p)
    return f"Parameter von {eid} geändert: {'; '.join(geaendert)}."
