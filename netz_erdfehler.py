"""
netz_erdfehler.py - Staffelung der Erdstufen im Strahlennetz (einpoliger Erdkurzschluss)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reines Python-Modul OHNE Streamlit (isoliert testbar).

Einstieg:
  pruefe_erdfehler(netz)  -> ErdfehlerErgebnis   (Bereiche, Zeitstaffelung, Empfindlichkeit)
  erdvorschlag(netz)      -> ErdVorschlagErgebnis (Zeiten der Erdstufen, mit Gegenpruefung)

Entscheidung 25.11.2026 (docs/tool_vorgabe_erdfehler.md): Erdfehler zuerst nur im Strahlennetz.
Im Ring liefert das Modul nur die Bereiche und einen Hinweis.

Ablauf:
  1. Kurzschlussrechnung mit Nullsystem (netz_kurzschluss): Ik1 je Knoten und Erdstrom 3I0
     durch jedes Element und jeden Erdungspunkt (erdstrom_verteilung).
  2. Erdungsbereiche: galvanisch verbundene Knoten (ueber Leitungen und Kupplungen). Ein
     Trafo mit Dreieckwicklung trennt die Bereiche, ein Erdfehler ist dahinter nicht als
     Erdstrom zu sehen. Isolierte und kompensierte Bereiche: nur Hinweis (Erdschluss, keine
     Stromstaffelung moeglich, Erfassung ueber U0 bzw. wattmetrisch).
  3. Fehlerorte: jeder Knoten eines geerdeten Bereichs und jeder Motorabgang. Fuer jeden
     Schutzort mit Erdstufen (Leitung 67N, Motor 50N/51N, Trafo IE am Sternpunkt) wird
     bestimmt, bei welchen Fehlern er Erdstrom in Vorwaertsrichtung fuehrt.
  4. Reihenfolge: Schutzort A liegt unter B, wenn B bei allen Fehlern Strom fuehrt, bei denen
     A Strom fuehrt, und bei weiteren. Benachbarte Paare werden wie bei den Phasen mit
     netz_selektivitaet.pruefe_paar geprueft, als Grenzstrom gilt der groesste 3I0 durch A.
     Fuehrt B weniger Strom als A (mehrere Erdungspunkte), geht das Verhaeltnis wie ein
     Stufensteller in die Pruefung ein.
  5. Empfindlichkeit: kleinster Ansprechwert jedes Schutzortes gegen den kleinsten 3I0 bei
     Ik1 min, Reserve gamma_Reserve = 1,5 wie bei den Phasen.

Tool-Vorgaben und Grenzen (bewusst, siehe Tool-Vorgabe):
  - Nur Erdstufen. Phasenstufen, die einen starren Erdkurzschluss ebenfalls sehen, werden hier
    nicht betrachtet.
  - Richtung: Stufen "Vorwaerts" und "Ungerichtet" zaehlen fuer Fehler vor dem Schutzort,
    "Rueckwaerts" nicht. Fliesst Erdstrom rueckwaerts durch eine Leitung (zweiter
    Erdungspunkt), gibt es einen Hinweis statt einer Pruefung.
  - Kein Fehlerwiderstand. Der Vorschlag aendert nur Zeiten von UMZ-Stufen, keine Stroeme.
    Innerhalb eines Geraets loest eine Stufe mit kleinerem Ansprechwert mindestens dt_Raster
    spaeter aus (Plausibilitaet des Leitungs-Tabs).
    AMZ-Stufen (51N des Motors) werden beruecksichtigt, aber nicht veraendert.
  - Der Sternpunktbildner (Erdung am Knoten ohne Trafo) hat im Tool keinen eigenen Schutz.

Robustheit: Das Modul wirft nie. Meldungen statt Ausnahmen, und es setzt nie FEHLER fuer
Fragen, die die Phasenstaffelung nicht betreffen.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import konstanten_netz as KN
import netz_adapter
import netz_kurzschluss as KS
import netz_selektivitaet as S
from netz_adapter import UMZ
from netz_modell import Netz
from netz_topologie import FEHLER, HINWEIS, WARNUNG, Meldung, analysiere
from utils import de

OK, GELB, ROT = S.OK, S.GELB, S.ROT
_RANG = {OK: 0, GELB: 1, ROT: 2}
VORWAERTS = ("", "Vorwärts", "Ungerichtet")
_EPS_REL = 1e-6           # Erdstrom unter diesem Anteil von Ik1 gilt als "kein Strom"


# ── Datenklassen ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Bereich:
    """Galvanisch verbundene Knoten einer Spannungsebene."""
    knoten: tuple
    UN_kV: float
    sternpunkt: str          # Sternpunktbehandlung (bei uneinheitlich: die erste nach Knoten-ID)
    geerdet: bool
    erdung: str              # Text aus der Kurzschlussrechnung
    Ik1_max_kA: float | None  # groesster Wert im Bereich
    Ik1_min_kA: float | None  # kleinster Wert im Bereich
    text: str = ""

    @property
    def name(self) -> str:
        return ", ".join(self.knoten)


@dataclass(frozen=True)
class Empfindlichkeit:
    ort: str                 # Anzeigename des Schutzortes
    stufe: str               # empfindlichste Stufe
    I_an_A: float            # Ansprechwert primaer (AMZ: Anregung 1,1 * Ip)
    I_min_A: float | None    # kleinster Erdstrom durch den Schutzort bei Ik1 min
    fehlerort: str           # wo dieser kleinste Strom auftritt
    status: str
    text: str

    @property
    def reserve(self) -> float | None:
        return None if not self.I_min_A or not self.I_an_A else self.I_min_A / self.I_an_A


@dataclass
class ErdfehlerErgebnis:
    dt_soll_s: float = KN.dt_Staffel_soll
    dt_min_s: float = KN.dt_Staffel_min
    bereiche: list = field(default_factory=list)          # Bereich
    orte: list = field(default_factory=list)              # Schutzorte mit Erdstufen
    pfade: list = field(default_factory=list)             # Ketten als Listen von Anzeigenamen
    pruefungen: list = field(default_factory=list)        # S.Staffelpruefung je Paar
    empfindlichkeit: list = field(default_factory=list)   # Empfindlichkeit je Schutzort
    stroeme: dict = field(default_factory=dict)           # Ort -> {Fehlerort: (I max A, I min A)}
    meldungen: list = field(default_factory=list)
    kurzschluss: object = None
    # intern: Struktur fuer den Vorschlag
    _struktur: dict | None = field(default=None, repr=False, compare=False)

    @property
    def ok(self) -> bool:
        return not any(m.stufe == FEHLER for m in self.meldungen)

    @property
    def status(self) -> str | None:
        alle = [p.status for p in self.pruefungen] + [e.status for e in self.empfindlichkeit]
        return max(alle, key=_RANG.get) if alle else None

    def pruefung(self, unten: str, oben: str):
        for p in self.pruefungen:
            if p.unten == unten and p.oben == oben:
                return p
        return None


@dataclass
class ErdVorschlagErgebnis:
    vorschlaege: list = field(default_factory=list)       # S.Zeitvorschlag je UMZ-Erdstufe
    pruefung: ErdfehlerErgebnis | None = None             # Gegenpruefung mit den neuen Zeiten
    meldungen: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(m.stufe == FEHLER for m in self.meldungen)

    @property
    def geaendert(self) -> list:
        return [v for v in self.vorschlaege if v.geaendert]

    def parameter_je_element(self) -> dict:
        """Element-ID -> {Parameter: Zeit}, nur Elemente mit mindestens einer Aenderung."""
        betroffen = {v.element for v in self.geaendert}
        out = {}
        for v in self.vorschlaege:
            if v.element in betroffen and v.parameter and v.t_neu_s == v.t_neu_s:
                out.setdefault(v.element, {})[v.parameter] = v.t_neu_s
        return out


# ── Hilfen ───────────────────────────────────────────────────────────────────
def _ortname(e, messort) -> str:
    if e.typ == "trafo":
        return f"{e.id} (Sternpunkt {messort})"
    return e.id


def _schutzorte(netz, erdstufen) -> list:
    """Ein Schutzort je (Element, Messort) mit den aktiven, bewertbaren Vorwaerts-Erdstufen."""
    je = {}
    for s in erdstufen:
        je.setdefault((s.element, s.messort), []).append(s)
    orte = []
    for (eid, messort), stufen in sorted(je.items()):
        wirksam = tuple(s for s in stufen if S.bewertbar(s) and s.richtung in VORWAERTS)
        if not wirksam:
            continue
        e = netz.elemente[eid]
        seite = f"Sternpunkt {messort}" if e.typ == "trafo" else ""
        orte.append(S.Schutzort(eid, seite, messort, stufen[0].UN_kV, wirksam))
    return orte


def _bereiche(netz, ks) -> tuple:
    """(Liste Bereich, Knoten-ID -> Bereichsname)."""
    null = ks.null
    if null is None:
        return [], {}
    verbund = null["verbund"]
    je = {}
    for kid in sorted(netz.knoten):
        je.setdefault(null["bereich"][verbund.wurzel(kid)], []).append(kid)
    out, zu = [], {}
    for _, ids in sorted(je.items(), key=lambda x: x[1]):
        kn = [netz.knoten[k] for k in ids]
        r = [ks.knoten[k] for k in ids if k in ks.knoten]
        geerdet = any(KS.geerdet(k) for k in kn)
        mx = [x.Ik1_max_kA for x in r if x.Ik1_max_kA is not None]
        mn = [x.Ik1_min_kA for x in r if x.Ik1_min_kA is not None]
        stp = kn[0].sternpunkt
        if not geerdet:
            text = ("Erdschluss, kein Erdkurzschluss: der Fehlerstrom ist klein und lässt sich "
                    "nicht über Stromstufen staffeln. Erfassung über die Verlagerungsspannung U0 "
                    "bzw. wattmetrisch (cos φ / sin φ), siehe Erdschlussstufen in den Tabs.")
        elif not mx:
            text = "Geerdet, aber Ik1 ist nicht berechenbar (Meldungen der Kurzschlussrechnung)."
        else:
            text = f"Ik1 von {de(min(mn) if mn else min(mx), 2)} bis {de(max(mx), 2)} kA."
        b = Bereich(tuple(ids), kn[0].UN_kV, stp, geerdet, r[0].erdung if r else "",
                    max(mx) if mx else None, min(mn) if mn else None, text)
        out.append(b)
        for k in ids:
            zu[k] = b.name
    return out, zu


def _fehlerorte(netz, ks) -> list:
    """(Name, Knoten, Motor-ID oder None) fuer jeden Knoten mit Ik1 und jeden Motorabgang."""
    out = []
    for kid in sorted(netz.knoten):
        r = ks.knoten.get(kid)
        if r is None or r.Ik1_max_kA is None:
            continue
        out.append((kid, kid, None))
    mit_ik1 = {k for k, _, _ in out}
    for eid, e in sorted(netz.elemente.items()):
        if e.typ == "motor" and e.zustand == "ein" and e.von in mit_ik1:
            out.append((f"Abgang {eid}", e.von, eid))
    return out


def _strom_durch(ort, e, vert, motor, eps) -> float | None:
    """Erdstrom durch den Schutzort [A], None = kein Strom in Vorwaertsrichtung."""
    if e.typ == "motor":
        return vert.Ik1_kA * 1000.0 if motor == e.id and vert.Ik1_kA else None
    if e.typ == "trafo":
        I = vert.erdungen.get(e.id)
        return I * 1000.0 if I is not None and I > eps else None
    if e.typ == "leitung":
        w = vert.zweige.get(e.id)
        if w is None or w[0] <= eps:
            return None
        return w[0] * 1000.0 if w[1] == ort.messort else -w[0] * 1000.0   # negativ = rueckwaerts
    return None


# ── Struktur: Stroeme, Fehlermengen, Paare ───────────────────────────────────
def _struktur(netz, ad, ks, erg) -> dict:
    orte = _schutzorte(netz, ad.erdstufen)
    erg.orte = orte
    fehler = _fehlerorte(netz, ks)
    vert = {}
    for name, kid, _ in fehler:
        if kid not in vert:
            vert[kid] = (KS.erdstrom_verteilung(ks, kid, KS.MAX), KS.erdstrom_verteilung(ks, kid, KS.MIN))

    F = {}            # Ort-Schluessel -> {Fehlername: (I_max, I_min)}
    rueck = []        # (Ort, Fehlername)
    for o in orte:
        e = netz.elemente[o.element]
        F[o.schluessel] = {}
        for name, kid, motor in fehler:
            vmax, vmin = vert[kid]
            eps = _EPS_REL * (vmax.Ik1_kA or 1.0)
            Imax = _strom_durch(o, e, vmax, motor, eps)
            if Imax is None:
                continue
            if Imax < 0:
                rueck.append((o, name))
                continue
            Imin = _strom_durch(o, e, vmin, motor, eps)
            F[o.schluessel][name] = (Imax, Imin if Imin is not None and Imin > 0 else None)
    erg.stroeme = {o.name: dict(F[o.schluessel]) for o in orte}
    for o, name in rueck:
        erg.meldungen.append(Meldung(
            HINWEIS, f"{o.name} führt bei einem Erdfehler an {name} Erdstrom in Rückwärtsrichtung "
                     f"(mehr als ein Erdungspunkt). Ungerichtete Erdstufen dort von Hand prüfen.",
            (o.element,)))

    # Paare: A unter B, wenn F(A) echte Teilmenge von F(B), und nichts dazwischen
    menge = {k: set(v) for k, v in F.items() if v}
    ohne = [o for o in orte if not menge.get(o.schluessel)]
    for o in ohne:
        erg.meldungen.append(Meldung(
            HINWEIS, f"{o.name}: führt bei keinem berechneten Erdfehler Strom in Vorwärtsrichtung, "
                     f"keine Erdstaffelung.", (o.element,)))
    aktiv = [o for o in orte if menge.get(o.schluessel)]
    paare = []
    for a in aktiv:
        Fa = menge[a.schluessel]
        ueber = [b for b in aktiv if b is not a and Fa < menge[b.schluessel]]
        for b in ueber:
            if not any(Fa < menge[c.schluessel] < menge[b.schluessel] for c in ueber if c is not b):
                paare.append((a, b))
        gleich = [b for b in aktiv if b is not a and Fa == menge[b.schluessel] and b.name > a.name]
        for b in gleich:
            erg.meldungen.append(Meldung(
                HINWEIS, f"{a.name} und {b.name} sehen genau dieselben Erdfehler. Ihre Reihenfolge "
                         f"ist nicht bestimmbar, sie werden nicht gegeneinander gestaffelt.",
                (a.element, b.element)))

    # Ketten fuer die Anzeige: von jedem untersten Ort nach oben
    unter_von = {}
    for a, b in paare:
        unter_von.setdefault(b.schluessel, []).append(a)
    ueber_von = {}
    for a, b in paare:
        ueber_von.setdefault(a.schluessel, []).append(b)
    unterste = [o for o in aktiv if o.schluessel not in unter_von]

    def ketten(o):
        hoch = ueber_von.get(o.schluessel, [])
        if not hoch:
            return [[o.name]]
        return [[o.name] + k for b in sorted(hoch, key=lambda x: x.name) for k in ketten(b)]
    erg.pfade = [k for o in unterste for k in ketten(o)]
    return {"orte": orte, "F": F, "paare": paare, "unter": unter_von}


def _grenze(F, ort) -> float | None:
    werte = [v[0] for v in F[ort.schluessel].values()]
    return max(werte) if werte else None


def _verhaeltnis(F, a, b) -> tuple | None:
    """(kleinstes, groesstes) Verhaeltnis I_B / I_A ueber die Fehler von A. None = immer 1."""
    r = [F[b.schluessel][f][0] / v[0] for f, v in F[a.schluessel].items()
         if f in F[b.schluessel] and v[0] > 0]
    if not r or all(abs(x - 1.0) < 1e-6 for x in r):
        return None
    return (min(r), max(r))


def _empfindlichkeit(netz, ort, F, gamma) -> Empfindlichkeit | None:
    werte = F[ort.schluessel]
    if not werte:
        return None
    s = min(ort.stufen, key=lambda x: S.anregestrom_bez(x, ort.UN_kV))
    I_an = S.anregestrom_bez(s, ort.UN_kV)
    mins = [(v[1], f) for f, v in werte.items() if v[1] is not None]
    if not mins:
        return Empfindlichkeit(ort.name, s.stufe, I_an, None, "", GELB,
                               "Ik1 min ist nicht berechenbar, Empfindlichkeit nicht prüfbar.")
    e = netz.elemente[ort.element]
    if e.typ == "trafo":                    # Reserve fuer den ganzen Bereich, kleinster Strom zaehlt
        I_min, wo = min(mins)
    else:                                   # eigener Schutzbereich: entferntester Fehler = kleinster
        I_min, wo = min(mins)
    q = I_min / I_an if I_an > 0 else math.inf
    if q >= gamma - 1e-9:
        st, t = OK, (f"{s.stufe} {de(I_an, 0)} A spricht beim kleinsten Erdstrom {de(I_min, 0)} A "
                     f"(Fehler an {wo}) sicher an, Reserve {de(q, 2)} (Soll {de(gamma, 2)}).")
    elif q >= 1.0:
        st, t = GELB, (f"{s.stufe} {de(I_an, 0)} A: knapp, kleinster Erdstrom {de(I_min, 0)} A "
                       f"(Fehler an {wo}), Reserve nur {de(q, 2)} (Soll {de(gamma, 2)}).")
    else:
        st, t = ROT, (f"{s.stufe} {de(I_an, 0)} A regt beim kleinsten Erdstrom {de(I_min, 0)} A "
                      f"(Fehler an {wo}) nicht an. Ansprechwert senken.")
    return Empfindlichkeit(ort.name, s.stufe, I_an, I_min, wo, st, t)


# ── Einstieg: Pruefung ───────────────────────────────────────────────────────
def pruefe_erdfehler(netz: Netz, adapter=None, kurzschluss=None,
                     dt_soll: float = KN.dt_Staffel_soll,
                     dt_min: float = KN.dt_Staffel_min,
                     gamma: float = KN.gamma_Reserve) -> ErdfehlerErgebnis:
    """
    Erdfehlerstaffelung des Strahlennetzes pruefen.
    adapter: netz_adapter.erzeuge_schutzstufen(netz), kurzschluss: netz_kurzschluss.berechne(netz).
    Beide werden sonst erzeugt.
    """
    erg = ErdfehlerErgebnis(dt_soll_s=dt_soll, dt_min_s=dt_min)
    try:
        return _pruefe(netz, adapter, kurzschluss, dt_soll, dt_min, gamma, erg)
    except Exception as exc:              # Auswertung darf die Oberflaeche nie abstuerzen lassen
        erg.meldungen.append(Meldung(
            WARNUNG, f"Erdfehlerprüfung abgebrochen ({type(exc).__name__}: {exc})."))
        return erg


def _pruefe(netz, adapter, kurzschluss, dt_soll, dt_min, gamma, erg) -> ErdfehlerErgebnis:
    ks = kurzschluss if kurzschluss is not None else KS.berechne(netz)
    erg.kurzschluss = ks
    erg.bereiche, _ = _bereiche(netz, ks)
    if not any(b.geerdet for b in erg.bereiche):
        erg.meldungen.append(Meldung(
            HINWEIS, "Kein Bereich ist starr oder niederohmig geerdet. Es gibt keinen "
                     "Erdkurzschlussstrom, die Erdstufen werden nicht gestaffelt."))
        return erg
    topo = analysiere(netz)
    if topo.netzform_erkannt == "ring" or netz.netzform == "ring":
        erg.meldungen.append(Meldung(
            HINWEIS, "Die Erdfehlerstaffelung gibt es bisher nur im Strahlennetz "
                     "(Entscheidung 25.11.2026). Ik1 je Knoten ist berechnet."))
        return erg
    ad = adapter if adapter is not None else netz_adapter.erzeuge_schutzstufen(netz, topo)
    erg.meldungen += ad.erd_meldungen
    if not ad.erdstufen:
        erg.meldungen.append(Meldung(
            HINWEIS, "Im Netz gibt es keine wirksamen Erdstufen (67N, 50N/51N, IE>)."))
        return erg
    st = _struktur(netz, ad, ks, erg)
    erg._struktur = st
    F = st["F"]
    for a, b in st["paare"]:
        I_grenz = _grenze(F, a)
        r = _verhaeltnis(F, a, b)
        p = S.pruefe_paar(a, b, a.UN_kV, I_grenz, dt_soll, dt_min, tap=r)
        erg.pruefungen.append(p)
    for o in erg.orte:
        e = _empfindlichkeit(netz, o, F, gamma)
        if e is not None:
            erg.empfindlichkeit.append(e)
    return erg


# ── Einstieg: Vorschlag ──────────────────────────────────────────────────────
def erdvorschlag(netz: Netz, adapter=None, kurzschluss=None,
                 dt_soll: float = KN.dt_Staffel_soll,
                 t_min: float = KN.t_Vorschlag_min) -> ErdVorschlagErgebnis:
    """
    Zeiten der Erd-UMZ-Stufen so vorschlagen, dass jede Stufe einen Staffelabstand ueber allem
    liegt, was darunter beim selben Erdstrom ausloest. Endpunkte (kein Schutzort darunter, z. B.
    Motor) behalten ihre Zeiten. Innerhalb eines Schutzortes bleibt die Reihenfolge erhalten:
    eine Stufe mit kleinerem Ansprechwert ist nie schneller als eine mit groesserem.
    """
    erg = ErdVorschlagErgebnis()
    try:
        return _vorschlag(netz, adapter, kurzschluss, dt_soll, t_min, erg)
    except Exception as exc:
        erg.meldungen.append(Meldung(
            WARNUNG, f"Erdstaffelvorschlag abgebrochen ({type(exc).__name__}: {exc})."))
        return erg


def _merke(erg, netz, ort, s, t_neu, grund) -> None:
    key = netz_adapter.ERD_ZEIT_PARAMETER.get(netz.elemente[ort.element].typ, {}).get(s.stufe)
    t_alt = s.t_s if s.t_s is not None else float("nan")
    t_neu = t_alt if t_neu is None else t_neu
    erg.vorschlaege.append(S.Zeitvorschlag(ort.element, s.stufe, key, t_alt, t_neu, grund))


def _vorschlag(netz, adapter, kurzschluss, dt_soll, t_min, erg) -> ErdVorschlagErgebnis:
    if not (S._ist_zahl(dt_soll) and dt_soll > 0 and S._ist_zahl(t_min) and t_min >= 0):
        erg.meldungen.append(Meldung(WARNUNG, "Staffelabstand oder Mindestzeit ungültig."))
        return erg
    ks = kurzschluss if kurzschluss is not None else KS.berechne(netz)
    ad = adapter if adapter is not None else netz_adapter.erzeuge_schutzstufen(netz)
    vorher = pruefe_erdfehler(netz, ad, ks, dt_soll)
    erg.meldungen += [m for m in vorher.meldungen if m.stufe != HINWEIS]
    st = vorher._struktur
    if st is None:
        erg.pruefung = vorher
        return erg
    F, unter = st["F"], st["unter"]
    neu = {o.schluessel: o for o in st["orte"]}
    fertig = {k for k in neu if k not in unter}
    for k in sorted(fertig):
        for s in neu[k].stufen:
            _merke(erg, netz, neu[k], s, s.t_s,
                   "Endpunkt, Zeit aus dem Tab bleibt" if s.kennlinie == UMZ else "AMZ, unverändert")
    offen = [k for k in neu if k not in fertig]
    while offen:
        naechste = [k for k in offen if all(u.schluessel in fertig for u in unter[k])]
        if not naechste:
            erg.meldungen.append(Meldung(WARNUNG, "Zirkuläre Erdstaffelkette, kein Vorschlag."))
            break
        for k in naechste:
            ort = neu[k]
            darunter = [neu[u.schluessel] for u in unter[k]]
            tap = {}
            for u in unter[k]:
                r = _verhaeltnis(F, u, ort)
                if r is not None:
                    tap[(u.schluessel, ort.schluessel)] = r
            grenz = lambda u: _grenze(F, u)
            zeiten = {}
            for s in ort.stufen:
                if s.kennlinie != UMZ:
                    continue
                t_neu, grund = S._zeit_fuer_stufe(ort, s, darunter, ort.UN_kV, netz.knoten,
                                                  dt_soll, t_min, tap, grenzstrom=grenz)
                zeiten[s.stufe] = (t_neu, grund)
            # Reihenfolge im Geraet erhalten: eine Stufe mit kleinerem Ansprechwert loest
            # mindestens einen Rasterschritt spaeter aus (wie die Plausibilitaet im Leitungs-Tab:
            # T(3I0>>>) < T(3I0>>) < T(3I0>)). Tool-Vorgabe.
            umz = sorted((s for s in ort.stufen if s.kennlinie == UMZ),
                         key=lambda x: -x.I_prim_A)
            t_lauf, vorige = None, None
            for s in umz:
                t, g = zeiten[s.stufe]
                if t_lauf is not None and t < t_lauf + KN.dt_Raster - KN.EPS_ZEIT:
                    t = round(t_lauf + KN.dt_Raster, 6)
                    g = (f"Reihenfolge im Gerät: {de(KN.dt_Raster, 2)} s nach {vorige} "
                         f"(größerer Ansprechwert)")
                    zeiten[s.stufe] = (t, g)
                t_lauf, vorige = t, s.stufe
            stufen = []
            for s in ort.stufen:
                if s.kennlinie != UMZ:
                    _merke(erg, netz, ort, s, None, "AMZ, unverändert (nur berücksichtigt)")
                    stufen.append(s)
                    continue
                t, g = zeiten[s.stufe]
                _merke(erg, netz, ort, s, t, g)
                stufen.append(replace(s, t_s=t))
            neu[k] = replace(ort, stufen=tuple(stufen))
            fertig.add(k)
            offen.remove(k)

    ersetzt = {(s.element, s.stufe): s for o in neu.values() for s in o.stufen}
    ad_neu = replace(ad, erdstufen=[ersetzt.get((s.element, s.stufe), s) for s in ad.erdstufen])
    erg.pruefung = pruefe_erdfehler(netz, ad_neu, ks, dt_soll)
    return erg


def vorschlag_uebernehmen(netz: Netz, vorschlag: ErdVorschlagErgebnis) -> list:
    """
    Vorgeschlagene Zeiten in das Netzmodell schreiben (atomar je Element ueber
    Netz.parameter_setzen). Rueckgabe: Liste der geaenderten Element-IDs.
    """
    geaendert = []
    for eid, werte in sorted(vorschlag.parameter_je_element().items()):
        p = dict(netz.elemente[eid].p)
        p.update(werte)
        netz.parameter_setzen(eid, p)
        geaendert.append(eid)
    return geaendert
