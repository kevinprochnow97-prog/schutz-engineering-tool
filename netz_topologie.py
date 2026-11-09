"""
netz_topologie.py - Topologieanalyse fuer die netzweite Selektivitaetsplanung
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reines Python-Modul OHNE Streamlit (isoliert testbar).

Einstieg: analysiere(netz) -> TopologieErgebnis

Abgrenzung zu netz_modell.py:
  Das Modell wirft ModellFehler, weil ein ungueltiger Datensatz nie entstehen
  darf. Die Topologie liefert dagegen Meldungen (fehler / warnung / hinweis),
  weil ein Netz waehrend der Eingabe ganz normal unfertig ist. Erst wenn keine
  Meldung der Stufe "fehler" vorliegt (ergebnis.ok), duerfen nachfolgende
  Schritte (Adapter, Staffelung) mit dem Netz rechnen.

Graphmodell:
  Knoten des Graphen sind die Netzknoten. Kanten sind alle Elemente mit zwei
  Anschluessen (Trafo, Leitung, Kupplung). Einspeisung, Generator und Motor
  haengen nur an einem Knoten und bilden keine Kante.
  Gesamtgraph: alle Kanten, unabhaengig vom Schaltzustand.
  Betriebsgraph: nur Kanten im Zustand "ein".

Maschenzahl: m = Kanten - Knoten + Zusammenhangskomponenten (zyklomatische
Zahl). Parallele Kanten zwischen denselben Knoten zaehlen als Masche.

Umfang (Tool-Vorgabe, bewusst begrenzt auf den Stand des Zeitplans):
  - genau eine Quelle (Einspeisung oder Generator)
  - Strahlennetz: keine Masche
  - Ringnetz: genau eine Masche, offen betrieben mit genau einer Trennstelle
  Geschlossener Ring, vermaschte Netze und mehrere Quellen werden erkannt
  und als noch nicht unterstuetzt gemeldet.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from netz_modell import Netz

FEHLER, WARNUNG, HINWEIS = "fehler", "warnung", "hinweis"

QUELLTYPEN = ("einspeisung", "generator")

# Relative Toleranz fuer den Spannungsvergleich Knoten <-> Parametersatz
_TOL_SPANNUNG = 1e-6


@dataclass(frozen=True)
class Meldung:
    stufe: str            # "fehler", "warnung" oder "hinweis"
    text: str
    ids: tuple = ()       # betroffene Knoten- und Element-IDs (fuer Hervorhebung in der UI)


@dataclass
class TopologieErgebnis:
    netzform_gewaehlt: str
    netzform_erkannt: str               # "leer", "strahl", "ring" oder "vermascht"
    maschen_gesamt: int
    maschen_betrieb: int
    quelle: str | None                  # Element-ID der Quelle
    ring_elemente: tuple                # Kanten, die auf einer Masche liegen
    trennstelle: str | None             # offenes Element auf dem Ring
    zufuehrung: dict                    # Knoten-ID -> Element-ID, ueber das der Knoten versorgt wird
    unversorgt: tuple                   # Knoten ohne Verbindung zur Quelle im Betrieb
    meldungen: list = field(default_factory=list)
    _elemente: dict = field(default_factory=dict, repr=False)

    @property
    def ok(self) -> bool:
        """True, wenn keine Meldung der Stufe 'fehler' vorliegt."""
        return not any(m.stufe == FEHLER for m in self.meldungen)

    def meldungen_der_stufe(self, stufe: str) -> list:
        return [m for m in self.meldungen if m.stufe == stufe]

    def pfad_zur_quelle(self, element_id: str) -> list:
        """
        Elemente vom angegebenen Element bis zur Quelle, in Richtung Quelle.
        Beispiel Referenznetz: M1 -> ["M1", "L1", "T1", "E1"].
        Das ist die Reihenfolge, in der spaeter zeitlich gestaffelt wird.
        Leere Liste, wenn das Element nicht versorgt ist oder die Topologie Fehler hat.
        """
        if not self.ok or element_id not in self._elemente:
            return []
        e = self._elemente[element_id]
        if e.typ in QUELLTYPEN:
            return [element_id]
        if e.zustand != "ein":
            return []
        # Bei Kanten ist der versorgende Knoten der, ueber den das Element selbst zugefuehrt wird
        if e.von is not None and e.nach is not None:
            if self.zufuehrung.get(e.nach) == element_id:
                start = e.von
            elif self.zufuehrung.get(e.von) == element_id:
                start = e.nach
            else:
                return []     # Kante liegt nicht im Versorgungsbaum
        else:
            start = e.von if e.von is not None else e.nach
        if self.quelle is None:
            return []
        quellknoten = self._elemente[self.quelle].nach
        pfad = [element_id]
        knoten = start
        besucht = set()
        while True:
            if knoten == quellknoten:
                pfad.append(self.quelle)
                return pfad
            if knoten not in self.zufuehrung or knoten in besucht:
                return []
            besucht.add(knoten)
            eid = self.zufuehrung[knoten]
            pfad.append(eid)
            ez = self._elemente[eid]
            knoten = ez.von if ez.nach == knoten else ez.nach

    def abgaenge(self, knoten_id: str) -> list:
        """Elemente, die vom Knoten aus in Richtung Last versorgt werden (inkl. Motoren)."""
        if not self.ok:
            return []
        ergebnis = []
        for eid, e in self._elemente.items():
            if e.typ in QUELLTYPEN or e.zustand != "ein":
                continue
            if e.nach is None and e.von == knoten_id:                  # Verbraucher am Knoten
                ergebnis.append(eid)
            elif e.von is not None and e.nach is not None:
                for nah, fern in ((e.von, e.nach), (e.nach, e.von)):
                    if nah == knoten_id and self.zufuehrung.get(fern) == eid:
                        ergebnis.append(eid)
        return sorted(ergebnis)


# ── Graph-Hilfsfunktionen ────────────────────────────────────────────────────
def _ist_kante(e) -> bool:
    return e.von is not None and e.nach is not None


def _komponenten(knoten_ids, kanten) -> list:
    """Zusammenhangskomponenten als Liste von Mengen. kanten: Liste (eid, a, b)."""
    nachbarn = {k: set() for k in knoten_ids}
    for _, a, b in kanten:
        nachbarn[a].add(b)
        nachbarn[b].add(a)
    rest = set(knoten_ids)
    komps = []
    while rest:
        start = min(rest)
        komp = {start}
        warte = deque([start])
        while warte:
            k = warte.popleft()
            for n in nachbarn[k]:
                if n not in komp:
                    komp.add(n)
                    warte.append(n)
        komps.append(komp)
        rest -= komp
    return komps


def _maschenzahl(knoten_ids, kanten) -> int:
    if not knoten_ids:
        return 0
    return len(kanten) - len(knoten_ids) + len(_komponenten(knoten_ids, kanten))


def _maschenkanten(knoten_ids, kanten) -> set:
    """
    Kanten, die auf einer Masche liegen. Eine Kante liegt genau dann auf einer
    Masche, wenn ihr Entfernen die Zahl der Komponenten nicht erhoeht.
    Einfach und robust, fuer Netzgroessen im Tool voellig ausreichend.
    """
    basis = len(_komponenten(knoten_ids, kanten))
    ergebnis = set()
    for i, (eid, _, _) in enumerate(kanten):
        ohne = kanten[:i] + kanten[i + 1:]
        if len(_komponenten(knoten_ids, ohne)) == basis:
            ergebnis.add(eid)
    return ergebnis


def _versorgungsbaum(quellknoten, knoten_ids, kanten) -> dict:
    """Breitensuche ab Quellknoten: Knoten -> zufuehrendes Element."""
    nachbarn = {k: [] for k in knoten_ids}
    for eid, a, b in sorted(kanten):
        nachbarn[a].append((b, eid))
        nachbarn[b].append((a, eid))
    zuf = {}
    besucht = {quellknoten}
    warte = deque([quellknoten])
    while warte:
        k = warte.popleft()
        for n, eid in nachbarn[k]:
            if n not in besucht:
                besucht.add(n)
                zuf[n] = eid
                warte.append(n)
    return zuf


def _gleich(a: float, b: float) -> bool:
    return abs(a - b) <= _TOL_SPANNUNG * max(abs(a), abs(b), 1.0)


# ── Pruefschritte ────────────────────────────────────────────────────────────
def _pruefe_quellen(elemente) -> tuple:
    quellen = sorted(eid for eid, e in elemente.items() if e.typ in QUELLTYPEN)
    meld = []
    if not quellen:
        meld.append(Meldung(FEHLER, "Keine Einspeisung vorhanden. Das Netz braucht genau eine Quelle."))
        return None, meld
    if len(quellen) > 1:
        meld.append(Meldung(
            FEHLER,
            f"Mehrere Quellen ({', '.join(quellen)}). Derzeit wird genau eine Quelle "
            f"unterstützt (Tool-Vorgabe), mehrere Einspeisungen sind für später vorgesehen.",
            tuple(quellen)))
        return None, meld
    q = quellen[0]
    if elemente[q].zustand != "ein":
        meld.append(Meldung(FEHLER, f"Die Quelle {q} ist ausgeschaltet.", (q,)))
    return q, meld


def _pruefe_spannungen(knoten, elemente) -> list:
    meld = []
    for eid, e in sorted(elemente.items()):
        if e.typ == "trafo":
            uo, uu = knoten[e.von].UN_kV, knoten[e.nach].UN_kV
            if _gleich(uo, uu):
                meld.append(Meldung(
                    FEHLER, f"Trafo {eid} verbindet zwei Knoten gleicher Spannung ({uo:g} kV).",
                    (eid, e.von, e.nach)))
            elif uo < uu:
                meld.append(Meldung(
                    FEHLER,
                    f"Trafo {eid}: von-Knoten {e.von} ({uo:g} kV) muss die Oberspannungsseite sein, "
                    f"nach-Knoten {e.nach} hat aber {uu:g} kV. Richtung tauschen.",
                    (eid, e.von, e.nach)))
            for schluessel, kid in (("UN_OS_kV", e.von), ("UN_US_kV", e.nach)):
                meld += _vergleich_p(eid, e.p, schluessel, kid, knoten[kid].UN_kV)
        elif e.typ in ("leitung", "kupplung"):
            ua, ub = knoten[e.von].UN_kV, knoten[e.nach].UN_kV
            if not _gleich(ua, ub):
                meld.append(Meldung(
                    FEHLER,
                    f"{e.typ.capitalize()} {eid} verbindet {e.von} ({ua:g} kV) mit "
                    f"{e.nach} ({ub:g} kV). Unterschiedliche Spannungen nur über einen Trafo.",
                    (eid, e.von, e.nach)))
            meld += _vergleich_p(eid, e.p, "UN_kV", e.von, ua)
        else:
            kid = e.von if e.von is not None else e.nach
            meld += _vergleich_p(eid, e.p, "UN_kV", kid, knoten[kid].UN_kV)
    return meld


def _vergleich_p(eid, p, schluessel, kid, un_knoten) -> list:
    """Spannung im Parametersatz gegen den Knoten pruefen. Der Knoten ist die Wahrheit."""
    wert = p.get(schluessel)
    if isinstance(wert, (int, float)) and not isinstance(wert, bool) and not _gleich(wert, un_knoten):
        return [Meldung(
            WARNUNG,
            f"{eid}: {schluessel} = {wert:g} kV im Parametersatz weicht von Knoten {kid} "
            f"({un_knoten:g} kV) ab. Gerechnet wird mit dem Knotenwert.",
            (eid, kid))]
    return []


def _pruefe_netzform(netzform, m_ges, m_betr, ring, aus_auf_ring) -> list:
    meld = []
    if netzform == "strahl":
        if m_ges > 0:
            meld.append(Meldung(
                FEHLER,
                f"Netzform Strahlennetz gewählt, das Netz enthält aber "
                f"{m_ges} Masche(n) über {', '.join(sorted(ring))}. "
                f"Für einen offenen Ring die Netzform auf Ringnetz umstellen.",
                tuple(sorted(ring))))
        return meld
    # Ringnetz
    if m_ges == 0:
        meld.append(Meldung(
            FEHLER,
            "Netzform Ringnetz gewählt, das Netz enthält aber keine Masche. "
            "Ring schließen (z. B. Kupplung zwischen zwei Abgängen) oder Strahlennetz wählen."))
    elif m_ges > 1:
        meld.append(Meldung(
            FEHLER,
            f"Das Netz enthält {m_ges} Maschen (vermascht). Unterstützt wird derzeit "
            f"genau ein Ring (Tool-Vorgabe).",
            tuple(sorted(ring))))
    elif m_betr > 0:
        meld.append(Meldung(
            FEHLER,
            "Der Ring ist geschlossen betrieben. Unterstützt wird derzeit nur der offene Ring "
            "mit einer Trennstelle. Ein Element auf dem Ring auf 'aus' setzen.",
            tuple(sorted(ring))))
    elif len(aus_auf_ring) > 1:
        meld.append(Meldung(
            FEHLER,
            f"Mehrere offene Elemente auf dem Ring ({', '.join(aus_auf_ring)}). "
            f"Ein offener Ring hat genau eine Trennstelle.",
            tuple(aus_auf_ring)))
    return meld


# ── Einstieg ─────────────────────────────────────────────────────────────────
def analysiere(netz: Netz) -> TopologieErgebnis:
    knoten = netz.knoten
    elemente = netz.elemente
    meldungen = []

    knoten_ids = set(knoten)
    kanten_ges = sorted((eid, e.von, e.nach) for eid, e in elemente.items() if _ist_kante(e))
    kanten_betr = [k for k in kanten_ges if elemente[k[0]].zustand == "ein"]

    if not knoten and not elemente:
        return TopologieErgebnis(
            netz.netzform, "leer", 0, 0, None, (), None, {}, (),
            [Meldung(FEHLER, "Das Netz ist leer. Mit Einspeisung und erstem Knoten beginnen.")],
            elemente)

    # 1. Quelle
    quelle, m = _pruefe_quellen(elemente)
    meldungen += m

    # 2. Unbenutzte Knoten und Zusammenhang
    benutzt = {k for e in elemente.values() for k in e.knoten_ids}
    for k in sorted(knoten_ids - benutzt):
        meldungen.append(Meldung(WARNUNG, f"Knoten {k} ist mit keinem Element verbunden.", (k,)))
    komps = [c for c in _komponenten(knoten_ids, kanten_ges) if c & benutzt]
    if len(komps) > 1:
        teile = "; ".join(", ".join(sorted(c)) for c in komps)
        meldungen.append(Meldung(
            FEHLER, f"Das Netz zerfällt in {len(komps)} getrennte Teile ({teile}).",
            tuple(sorted(set().union(*komps)))))

    # 3. Spannungen
    meldungen += _pruefe_spannungen(knoten, elemente)

    # 4. Maschen und Netzform
    m_ges = _maschenzahl(knoten_ids, kanten_ges)
    m_betr = _maschenzahl(knoten_ids, kanten_betr)
    ring = _maschenkanten(knoten_ids, kanten_ges)
    aus_auf_ring = sorted(eid for eid in ring if elemente[eid].zustand == "aus")
    erkannt = "strahl" if m_ges == 0 else ("ring" if m_ges == 1 else "vermascht")
    meldungen += _pruefe_netzform(netz.netzform, m_ges, m_betr, ring, aus_auf_ring)
    trennstelle = aus_auf_ring[0] if (erkannt == "ring" and len(aus_auf_ring) == 1) else None

    # 5. Versorgung im Betrieb
    zufuehrung, unversorgt = {}, ()
    if quelle is not None and elemente[quelle].zustand == "ein":
        qk = elemente[quelle].nach
        zufuehrung = _versorgungsbaum(qk, knoten_ids, kanten_betr)
        erreicht = {qk} | set(zufuehrung)
        unversorgt = tuple(sorted((knoten_ids & benutzt) - erreicht))
        if unversorgt and len(komps) <= 1:
            meldungen.append(Meldung(
                WARNUNG,
                f"Im aktuellen Schaltzustand nicht versorgt: {', '.join(unversorgt)}.",
                unversorgt))
    for eid, e in sorted(elemente.items()):
        if e.zustand == "aus" and eid not in ring and e.typ not in QUELLTYPEN:
            meldungen.append(Meldung(HINWEIS, f"{eid} ist ausgeschaltet.", (eid,)))

    if trennstelle:
        meldungen.append(Meldung(HINWEIS, f"Offener Ring, Trennstelle bei {trennstelle}.", (trennstelle,)))

    return TopologieErgebnis(
        netzform_gewaehlt=netz.netzform,
        netzform_erkannt=erkannt,
        maschen_gesamt=m_ges,
        maschen_betrieb=m_betr,
        quelle=quelle,
        ring_elemente=tuple(sorted(ring)),
        trennstelle=trennstelle,
        zufuehrung=zufuehrung,
        unversorgt=unversorgt,
        meldungen=meldungen,
        _elemente=elemente,
    )
