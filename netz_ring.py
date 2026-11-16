"""
netz_ring.py - Staffelung im offenen Ring ueber alle Trennstellenlagen
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reines Python-Modul OHNE Streamlit (isoliert testbar).

Einstieg:
  pruefe_ringlagen(netz) -> RingErgebnis    (Ist-Einstellungen in jeder Lage pruefen)
  ringvorschlag(netz)    -> RingVorschlag   (ein Satz Einstellwerte fuer alle Lagen)

Hintergrund: Ein offener Ring hat im Betrieb eine Trennstelle. Wird sie verlegt
(Umschaltung nach einem Fehler, Wartung), aendert sich der Versorgungsbaum und damit
die Staffelkette. Ein Vorschlag nur fuer die aktuelle Lage ist nach dem Umschalten
nicht mehr selektiv. Jedes Ringelement kommt als Trennstelle in Frage.

Vorschlag fuer alle Lagen (Tool-Vorgabe, Herleitung in docs/tool_vorgabe_ring.md):
  Je Lage laeuft der Gesamtvorschlag (erst Strom, dann Zeit). Je Parameter gilt der
  GROESSTE Wert ueber alle Lagen. Endpunkte einer Lage zaehlen mit ihrem Wert, damit ein
  Schutz, der in einer Lage Endpunkt und in einer anderen Mittelstation ist, nicht
  abgesenkt wird. Weil sich die Lagen gegenseitig beeinflussen, wird mit den neuen
  Werten wiederholt, bis sich nichts mehr aendert (Fixpunkt, Werte nur nach oben).
  Laufen Ketten in zwei Lagen gegenlaeufig (A ueber B und B ueber A), gibt es keinen
  Fixpunkt. Die Iteration endet dann nach MAX_RUNDEN, es werden keine Werte geliefert und
  die gegenlaeufigen Paare werden namentlich gemeldet (gegenlaeufige_paare).

Modellannahme und Grenzen:
  - Eine Leitung hat EINEN Parametersatz, der Schutz sitzt in jeder Lage am speiseseitigen
    Ende. Das entspricht zwei gleich eingestellten, ungerichteten Relais an beiden Enden
    (bei einer Einspeisung fuehren beide denselben Strom).
  - Gegenlaeufige Ketten sind damit nicht loesbar. Dafuer braucht es Richtungsstufen UND
    je Leitungsende eigene Einstellwerte. Eigene Werte je Ende ohne Richtung genuegen
    nicht: das lastseitige Relais fuehrt bei Durchgangsfehlern denselben Strom und
    wuerde mit seinen Werten fuer die andere Lage ausloesen.
  - Ik max und Ik min an den Knoten sind Eingabewerte und gelten fuer jede Lage gleich.
    In der Realitaet aendern sie sich mit der Trennstelle.
  - Genau eine Masche, wie in netz_topologie.py.

Robustheit: Das Modul wirft nie. Fehlende oder fehlerhafte Daten fuehren zu Meldungen.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import konstanten_netz as KN
import netz_adapter
import netz_selektivitaet as S
import netz_stromstaffel as SS
import netz_topologie
from netz_modell import Netz
from netz_topologie import FEHLER, HINWEIS, WARNUNG, Meldung
from utils import de

MAX_RUNDEN = 12          # Abbruch der Iteration (Tool-Vorgabe, im Beispielring genuegen 2 bis 3)
_EPS_WERT = 1e-6


# ── Datenklassen ─────────────────────────────────────────────────────────────
@dataclass
class RingLage:
    trennstelle: str
    netz: Netz
    zeit: S.SelektivitaetErgebnis | None = None
    strom: SS.StromPruefErgebnis | None = None

    @property
    def status(self) -> str | None:
        return None if self.zeit is None else self.zeit.status

    @property
    def schlechtestes_paar(self):
        if self.zeit is None or not self.zeit.pruefungen:
            return None
        b = self.zeit.pruefungen[0]
        for p in self.zeit.pruefungen[1:]:
            if S._schlechter(p, b):
                b = p
        return b


@dataclass
class RingErgebnis:
    lagen: list = field(default_factory=list)
    meldungen: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(m.stufe == FEHLER for m in self.meldungen)

    @property
    def status(self) -> str | None:
        st = [l.status for l in self.lagen if l.status is not None]
        return max(st, key=S._RANG.get) if st else None

    def lage(self, trennstelle: str):
        for l in self.lagen:
            if l.trennstelle == trennstelle:
                return l
        return None


@dataclass(frozen=True)
class RingWert:
    element: str
    stufe: str
    parameter: str
    art: str                 # "Zeit" oder "Strom"
    alt: float               # Zeit in s bzw. Faktor x IN
    neu: float
    grund: str = ""
    kurz: str = ""           # Begruendung in einem Halbsatz
    IN_A: float | None = None   # nur Strom: Nennstrom, mit dem der Faktor multipliziert wird

    @property
    def geaendert(self) -> bool:
        return abs(self.neu - self.alt) > _EPS_WERT


@dataclass
class RingVorschlag:
    werte: list = field(default_factory=list)
    pruefung: RingErgebnis | None = None       # Gegenpruefung aller Lagen mit den neuen Werten
    runden: int = 0
    konvergiert: bool = False
    meldungen: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(m.stufe == FEHLER for m in self.meldungen)

    @property
    def geaendert(self) -> list:
        return [w for w in self.werte if w.geaendert]

    @property
    def uebernehmbar(self) -> bool:
        """Nur ein Fixpunkt, der in jeder Lage selektiv ist, darf ins Netz geschrieben werden."""
        return self.ok and self.konvergiert and bool(self.geaendert)

    def parameter_je_element(self) -> dict:
        """
        Element-ID -> {Parameter: Wert} fuer jedes Element mit mindestens einer Aenderung.
        Zeiten: alle Zeiten des Elements (beim Trafo folgt die US-Zeit sonst der OS-Zeit).
        Ansprechfaktoren: nur die geaenderten (sonst waere die Tab-Automatik eingefroren).
        """
        betroffen = {w.element for w in self.geaendert}
        out = {}
        for w in self.werte:
            if w.element not in betroffen:
                continue
            if w.art == "Zeit" or w.geaendert:
                out.setdefault(w.element, {})[w.parameter] = w.neu
        return out


# ── Lagen erzeugen ───────────────────────────────────────────────────────────
def _kopie(netz: Netz) -> Netz:
    return Netz.from_dict(netz.to_dict())


def erzeuge_lagen(netz: Netz) -> tuple:
    """
    Eine Netzkopie je moeglicher Trennstelle (jedes Ringelement). Rueckgabe (Lagen, Meldungen).
    Ohne gueltigen Ring: leere Liste mit Meldung.
    """
    meldungen = []
    try:
        topo = netz_topologie.analysiere(netz)
        if not topo.ok:
            meldungen.append(Meldung(
                FEHLER, "Die Topologie enthält Fehler. Die Ringlagen werden erst danach geprüft."))
            return [], meldungen
        if topo.netzform_erkannt != "ring" or not topo.ring_elemente:
            meldungen.append(Meldung(HINWEIS, "Das Netz enthält keinen Ring, es gibt nur eine Lage."))
            return [], meldungen
        lagen = []
        for eid in topo.ring_elemente:
            n = _kopie(netz)
            for r in topo.ring_elemente:
                n.element_aendern(r, zustand="ein")
            n.element_aendern(eid, zustand="aus")
            lagen.append(RingLage(eid, n))
        return lagen, meldungen
    except Exception as exc:
        meldungen.append(Meldung(FEHLER, f"Ringlagen konnten nicht erzeugt werden ({type(exc).__name__}: {exc})."))
        return [], meldungen


# ── Ist-Pruefung in allen Lagen ──────────────────────────────────────────────
def pruefe_ringlagen(netz: Netz, U_bezug_kV: float | None = None,
                     dt_soll: float = KN.dt_Staffel_soll,
                     dt_min: float = KN.dt_Staffel_min) -> RingErgebnis:
    """Zeit- und Strompruefung der vorhandenen Einstellwerte in jeder Trennstellenlage."""
    erg = RingErgebnis()
    try:
        erg.lagen, erg.meldungen = erzeuge_lagen(netz)
        for lage in erg.lagen:
            lage.zeit = S.pruefe_selektivitaet(lage.netz, None, U_bezug_kV, dt_soll, dt_min)
            lage.strom = SS.pruefe_strom(lage.netz, None, U_bezug_kV)
            for m in lage.zeit.meldungen:
                if m.stufe == FEHLER:
                    erg.meldungen.append(Meldung(
                        FEHLER, f"Lage {lage.trennstelle}: {m.text}", m.ids))
        if erg.lagen:
            erg.meldungen.append(_hinweis_ik())
        return erg
    except Exception as exc:
        erg.meldungen.append(Meldung(
            FEHLER, f"Ringprüfung abgebrochen ({type(exc).__name__}: {exc})."))
        return erg


def _hinweis_ik() -> Meldung:
    return Meldung(
        HINWEIS,
        "Ik max und Ik min an den Knoten gelten für jede Trennstellenlage gleich. "
        "In der Realität ändern sie sich mit der Lage.")


# ── Vorschlag fuer alle Lagen ────────────────────────────────────────────────
def _werte_der_lage(g: SS.GesamtVorschlag) -> dict:
    """(Element, Parameter) -> (Stufe, Art, alt, neu, Grund, Kurz, IN) aller setzbaren Stufen."""
    out = {}
    if g.zeit is not None:
        for v in g.zeit.vorschlaege:
            if v.parameter and S._ist_zahl(v.t_neu_s) and S._ist_zahl(v.t_alt_s):
                out[(v.element, v.parameter)] = (v.stufe, "Zeit", v.t_alt_s, v.t_neu_s,
                                                 v.grund, v.grund, None)
    for v in g.strom.vorschlaege:
        if v.parameter and v.faktor_neu is not None and v.faktor_alt:
            out[(v.element, v.parameter)] = (v.stufe, "Strom", v.faktor_alt, v.faktor_neu,
                                             v.grund, v.kurz or v.status, v.I_alt_A / v.faktor_alt)
    return out


def gegenlaeufige_paare(ergebnis: RingErgebnis) -> list:
    """
    Paare von Elementen, die in zwei Lagen in umgekehrter Reihenfolge in einer Kette liegen.
    Rueckgabe: Liste (oben, unten, Lage, Lage_umgekehrt). Grundlage sind die Pfade der Lagen.
    """
    ueber = {}                                   # (unten, oben) -> erste Lage mit dieser Reihenfolge
    for lage in ergebnis.lagen:
        for pfad in (lage.zeit.pfade if lage.zeit else []):
            elemente = []
            for name in pfad:
                e = S._element_von_name(name)
                if e not in elemente:
                    elemente.append(e)
            for i, unten in enumerate(elemente):
                for oben in elemente[i + 1:]:
                    ueber.setdefault((unten, oben), lage.trennstelle)
    out = []
    for (unten, oben), lage in sorted(ueber.items()):
        if unten < oben and (oben, unten) in ueber:
            out.append((oben, unten, lage, ueber[(oben, unten)]))
    return out


def _setze(netz: Netz, stand: dict) -> None:
    je_element = {}
    for (eid, key), wert in stand.items():
        je_element.setdefault(eid, {})[key] = wert
    for eid, neu in je_element.items():
        p = dict(netz.elemente[eid].p)
        p.update(neu)
        netz.parameter_setzen(eid, p)


def _untergrenzen(netz: Netz, stand: dict) -> dict:
    """{(Element, Stufe): Zeit} aus dem Stand, nur Zeitparameter."""
    out = {}
    for (eid, key), wert in stand.items():
        typ = netz.elemente[eid].typ
        for stufe, k in netz_adapter.ZEIT_PARAMETER.get(typ, {}).items():
            if k == key:
                out[(eid, stufe)] = wert
    return out


def ringvorschlag(netz: Netz, U_bezug_kV: float | None = None,
                  dt_soll: float = KN.dt_Staffel_soll, k_S: float = KN.k_S_Strom,
                  t_min: float = KN.t_Vorschlag_min) -> RingVorschlag:
    """Ein Satz Einstellwerte, der in allen Trennstellenlagen gilt (siehe Modulkopf). Wirft nie."""
    erg = RingVorschlag()
    try:
        return _ringvorschlag(netz, U_bezug_kV, dt_soll, k_S, t_min, erg)
    except Exception as exc:
        erg.meldungen.append(Meldung(
            FEHLER, f"Ringvorschlag abgebrochen ({type(exc).__name__}: {exc})."))
        return erg


def _ringvorschlag(netz, U_bezug_kV, dt_soll, k_S, t_min, erg) -> RingVorschlag:
    lagen, meld = erzeuge_lagen(netz)
    erg.meldungen += meld
    if not lagen:
        return erg
    stand: dict = {}              # (Element, Parameter) -> Wert, nur nach oben
    basis: dict = {}              # (Element, Parameter) -> (Stufe, Art, Wert im Netz, IN)
    grund: dict = {}              # (Element, Parameter) -> (Grund, Kurz) der letzten Anhebung
    warnungen: dict = {}          # (Stufe, Text) -> Lagen, aus der letzten Runde
    erg.konvergiert = False
    for runde in range(1, MAX_RUNDEN + 1):
        erg.runden = runde
        warnungen = {}
        zuwachs = False
        for lage in lagen:
            _setze(lage.netz, stand)
            g = SS.gesamtvorschlag(lage.netz, None, U_bezug_kV, dt_soll, k_S, t_min,
                                   _untergrenzen(lage.netz, stand))
            for m in g.meldungen:
                if m.stufe in (FEHLER, WARNUNG):
                    warnungen.setdefault((m.stufe, m.text), []).append(lage.trennstelle)
            if not g.ok or g.zeit is None:
                erg.meldungen.append(Meldung(
                    FEHLER, f"Lage {lage.trennstelle}: kein Vorschlag möglich."))
                return erg
            for k, (stufe, art, alt, neu, gr, kurz, IN) in _werte_der_lage(g).items():
                if runde == 1:
                    basis.setdefault(k, (stufe, art, alt, IN))
                if neu > stand.get(k, -math.inf) + _EPS_WERT:
                    stand[k] = neu
                    grund[k] = (f"Lage {lage.trennstelle}: {gr}", f"Lage {lage.trennstelle}: {kurz}")
                    zuwachs = True
        if not zuwachs:                  # eine volle Runde ohne Anhebung: Fixpunkt erreicht
            erg.konvergiert = True
            break

    if not erg.konvergiert:
        # Kein Satz Werte fuer alle Lagen. Ursache benennen statt weggelaufene Zeiten zu zeigen.
        paare = gegenlaeufige_paare(pruefe_ringlagen(netz, U_bezug_kV, dt_soll))
        if paare:
            bsp = "; ".join(f"{o} liegt mit Trennstelle {l1} über {u}, mit Trennstelle {l2} darunter"
                            for o, u, l1, l2 in paare[:3])
            ursache = f"Gegenläufige Ketten: {bsp}."
        else:
            ursache = f"Keine Konvergenz nach {MAX_RUNDEN} Runden."
        erg.meldungen.append(Meldung(
            WARNUNG, f"{ursache} Mit ungerichteten Stufen und einem Parametersatz je Leitung "
                     f"gibt es keinen Satz Zeiten, der in allen Lagen selektiv ist. Abhilfe: "
                     f"die Trennstelle festlegen und den Vorschlag für die aktuelle Lage nutzen. "
                     f"Richtungsstufen bildet das Tool noch nicht ab."))
        erg.meldungen.append(_hinweis_ik())
        return erg

    erg.werte = [RingWert(eid, basis[(eid, key)][0], key, basis[(eid, key)][1],
                          basis[(eid, key)][2], stand[(eid, key)],
                          grund.get((eid, key), ("", ""))[0], grund.get((eid, key), ("", ""))[1],
                          basis[(eid, key)][3])
                 for (eid, key) in sorted(stand) if (eid, key) in basis]
    for (stufe, text), namen in warnungen.items():
        if text.startswith("Die Kette passt nicht unter den Schutz des Netzbetreibers"):
            erg.meldungen.append(Meldung(stufe, f"Lage {', '.join(namen)}: {text}"))
    erg.meldungen.append(_hinweis_ik())
    # Gegenpruefung: alle Lagen mit dem fertigen Satz
    kopie = _kopie(netz)
    _setze(kopie, stand)
    erg.pruefung = pruefe_ringlagen(kopie, U_bezug_kV, dt_soll)
    if erg.konvergiert:
        # Gegenprobe: ein Fixpunkt muss in jeder Lage selektiv sein (ausser gegen den Netzbetreiber)
        offen = []
        for lage in erg.pruefung.lagen:
            for p in lage.zeit.pruefungen if lage.zeit else []:
                if p.status == S.ROT and netz.elemente[S._element_von_name(p.oben)].typ != "einspeisung":
                    offen.append(f"{p.unten} → {p.oben} in Lage {lage.trennstelle}")
        if offen:
            erg.konvergiert = False
            erg.meldungen.append(Meldung(
                WARNUNG, f"Die Gegenprüfung findet nicht selektive Paare ({'; '.join(offen[:4])}). "
                         f"Der Vorschlag ist nicht übernehmbar."))
    return erg
