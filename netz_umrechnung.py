"""
netz_umrechnung.py - Kurzschlussstroeme ueber Transformatoren umrechnen
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reines Python-Modul OHNE Streamlit (isoliert testbar).

Aufgabe: Ein Kurzschlussstrom, der an einem Knoten (Fehlerort) angegeben ist,
soll als Strom am Messort eines Schutzes gelesen werden. Dazwischen liegen im
Versorgungsbaum null, ein oder mehrere Transformatoren. Je Transformator gilt
(Herleitung und Grenzen: docs/tool_vorgabe_stromstaffelung.md):

  I_OS = I_US * (UN_US / UN_OS) * f_Stufensteller * f_Schaltgruppe

  1. Uebersetzung: Verhaeltnis der KNOTEN-Nennspannungen (wie auf_bezug()).
  2. Stufensteller (Tool-Vorgabe): sitzt auf der OS-Wicklung, Mittelstellung =
     Nennuebersetzung, Stellbereich +-s. Bei s_Wicklung = 1 + x hat die OS-Wicklung
     (1 + x) mal die Windungen, der OS-Strom ist 1/(1 + x) mal so gross.
       Fall "max" (Ik max, Strom nach oben abgrenzen): x = -s, Faktor 1/(1 - s)
       Fall "min" (Ik min, Empfindlichkeit):           x = +s, Faktor 1/(1 + s)
  3. Schaltgruppe, nur beim zweipoligen Fehler (Fall "min", Ik min ist per
     Tool-Vorgabe der kleinste ZWEIPOLIGE Kurzschlussstrom):
       Wechsel D<->Y (z. B. Dyn, YNd): groesster Strangstrom = 2/sqrt(3) = 1,155.
       Kein Wechsel (Yy, Dd): Faktor 1.
     Dreipoliger Fehler (Fall "max"): Faktor 1 bei jeder Schaltgruppe.

Messung: dreiphasig, massgebend ist der GROESSTE Strangstrom. Bei Wandlern in
nur zwei Phasen koennte der groesste Strang unbeobachtet sein (nicht abgedeckt).

Robustheit: Das Modul wirft nie. Unbekannte Schaltgruppe oder ungueltiger
Stufensteller fuehren zu einem Hinweistext und zum neutralen Faktor 1.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

import konstanten_netz as KN
from utils import de

MAX = "max"      # Ik max: dreipoliger Fehler, Stufensteller in der unguenstigsten Lage fuer den GROESSTEN Strom
MIN = "min"      # Ik min: zweipoliger Fehler, Stufensteller in der unguenstigsten Lage fuer den KLEINSTEN Strom

# Gross = OS-Wicklung, klein = US-Wicklung (IEC-Kennzeichnung, z. B. "YNd5", "Dyn11")
_SG_MUSTER = re.compile(r"^(YN|Y|D|ZN|Z)(yn|y|d|zn|z)(\d{1,2})?$")


def _ist_zahl(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def wicklungen(schaltgruppe) -> tuple | None:
    """
    ("D"|"Y"|"Z", "D"|"Y"|"Z") fuer OS und US, None wenn nicht lesbar.
    YN und ZN zaehlen als Stern bzw. Zickzack, der Sternpunkt ist hier ohne Belang.
    """
    if not isinstance(schaltgruppe, str):
        return None
    m = _SG_MUSTER.match(schaltgruppe.strip())
    if not m:
        return None
    return m.group(1)[0], m.group(2)[0].upper()


def faktor_schaltgruppe(schaltgruppe, fall: str) -> tuple:
    """(Faktor, Text). Nur der zweipolige Fehler (Fall MIN) hat bei D<->Y einen Faktor."""
    if fall != MIN:
        return 1.0, "dreipoliger Fehler, Faktor 1"
    w = wicklungen(schaltgruppe)
    if w is None:
        return 1.0, (f"Schaltgruppe {schaltgruppe!r} nicht lesbar, Faktor 1 "
                     f"(ohne Zuschlag fuer den zweipoligen Fehler)")
    # Zickzack verhaelt sich beim zweipoligen Fehler wie Stern
    delta_os, delta_us = w[0] == "D", w[1] == "D"
    if delta_os != delta_us:
        return KN.f_Sg_2pol_DY, f"{schaltgruppe}: Wechsel D/Y, zweipolig Faktor 2/sqrt(3)"
    return 1.0, f"{schaltgruppe}: kein Wechsel D/Y, Faktor 1"


def faktor_stufensteller(stufensteller_pm, fall: str) -> tuple:
    """(Faktor, Text) fuer den OS-Strom bei gegebenem US-Strom, ungünstigste Lage je Fall."""
    if stufensteller_pm is None:
        return 1.0, "Stufensteller nicht angegeben, Faktor 1"
    if not _ist_zahl(stufensteller_pm) or not (0 <= stufensteller_pm < 100):
        return 1.0, f"Stufensteller {stufensteller_pm!r} ungueltig, Faktor 1"
    s = stufensteller_pm / 100.0
    if s == 0:
        return 1.0, "kein Stufensteller"
    if fall == MAX:
        return 1.0 / (1.0 - s), f"Stufensteller -{stufensteller_pm:g} %, Faktor 1/(1-s)"
    return 1.0 / (1.0 + s), f"Stufensteller +{stufensteller_pm:g} %, Faktor 1/(1+s)"


@dataclass(frozen=True)
class Schritt:
    """Ein Transformator auf dem Weg vom Fehlerort zum Messort."""
    element: str
    f_uebersetzung: float
    f_stufensteller: float
    f_schaltgruppe: float
    texte: tuple = ()

    @property
    def faktor(self) -> float:
        return self.f_uebersetzung * self.f_stufensteller * self.f_schaltgruppe


@dataclass
class Umrechnung:
    """Ergebnis einer Umrechnung. I_A ist der Strom am Messknoten in Ampere."""
    I_A: float | None = None
    faktor: float = 1.0
    schritte: list = field(default_factory=list)
    hinweise: list = field(default_factory=list)
    ok: bool = True

    @property
    def text(self) -> str:
        if not self.schritte:
            return "ohne Transformator, Strom unveraendert"
        return "; ".join(f"{s.element}: ×{de(s.faktor, 4)}" for s in self.schritte)


def pfad_elemente(netz, topo, fernknoten: str, messknoten: str) -> list | None:
    """
    Elemente im Versorgungsbaum vom Fehlerknoten (fern) zum Messknoten, in dieser
    Reihenfolge. [] wenn beide Knoten gleich sind, None wenn der Messknoten nicht
    oberhalb des Fehlerknotens im Versorgungsbaum liegt.
    """
    try:
        zuf, elemente = topo.zufuehrung, netz.elemente
        knoten, weg, besucht = fernknoten, [], set()
        while knoten != messknoten:
            if knoten in besucht or knoten not in zuf:
                return None
            besucht.add(knoten)
            eid = zuf[knoten]
            weg.append(eid)
            e = elemente[eid]
            knoten = e.von if e.nach == knoten else e.nach
        return weg
    except Exception:
        return None


def umrechnen(netz, topo, I_A: float, fernknoten: str, messknoten: str, fall: str) -> Umrechnung:
    """
    Strom I_A am Fehlerknoten als Strom am Messknoten lesen (Ampere am Messknoten).
    Nur Transformatoren veraendern den Strom, Leitungen und Kupplungen nicht.
    """
    erg = Umrechnung()
    if fall not in (MAX, MIN):
        erg.ok, erg.I_A = False, None
        erg.hinweise.append(f"Unbekannter Fall {fall!r}.")
        return erg
    weg = pfad_elemente(netz, topo, fernknoten, messknoten)
    if weg is None:
        erg.ok, erg.I_A = False, None
        erg.hinweise.append(f"{messknoten} liegt nicht oberhalb von {fernknoten} im Versorgungsbaum.")
        return erg
    kn, el = netz.knoten, netz.elemente
    faktor = 1.0
    for eid in weg:
        e = el[eid]
        if e.typ != "trafo":
            continue
        # Strom fliesst vom Fehler Richtung Quelle: von der US- zur OS-Seite
        if not (e.von in kn and e.nach in kn):
            erg.ok, erg.I_A = False, None
            erg.hinweise.append(f"{eid}: Knoten fehlen.")
            return erg
        f_u = kn[e.nach].UN_kV / kn[e.von].UN_kV
        f_t, t_t = faktor_stufensteller(e.p.get("Stufensteller_pm"), fall)
        f_s, t_s = faktor_schaltgruppe(e.p.get("Schaltgruppe"), fall)
        for t in (t_t, t_s):
            if "nicht lesbar" in t or "ungueltig" in t:
                erg.hinweise.append(f"{eid}: {t}.")
        erg.schritte.append(Schritt(eid, f_u, f_t, f_s, (t_t, t_s)))
        faktor *= f_u * f_t * f_s
    erg.faktor = faktor
    erg.I_A = I_A * faktor
    return erg
