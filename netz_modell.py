"""
netz_modell.py - Datenmodell fuer die netzweite Selektivitaetsplanung
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reines Python-Modul OHNE Streamlit (isoliert testbar).

Das Netzmodell ist die einzige Wahrheit. Die Oberflaeche (tab_netz.py) ist nur
eine Ansicht darauf und veraendert das Netz ausschliesslich ueber die
Methoden dieser Klasse.

Aufbau:
  Netz     - Name, Netzform, Knoten, Elemente
  Knoten   - Sammelschiene bzw. Verbindungspunkt mit UN, Ik und Sternpunkt
  Element  - Betriebsmittel als Kante zwischen zwei Knoten (von -> nach).
             Quellen (Einspeisung, Generator) haben kein "von",
             Verbraucher (Motor) haben kein "nach".
             p ist der Parametersatz mit denselben Schluesseln, die das
             passende calc_<bm>.berechne_alle(p) erwartet. Das Modell prueft
             nur, dass p ein flaches, JSON-faehiges Dict ist. Die fachliche
             Pruefung von p uebernimmt der Adapter (netz_adapter.py).

Was dieses Modul prueft (Modellebene):
  Datentypen, eindeutige IDs, gueltige Typen, Knotenverweise, Wertebereiche.
Was es NICHT prueft (Topologieebene, netz_topologie.py):
  Zusammenhang, Maschen, Netzform, Spannungskonsistenz entlang der Kanten.

Grundsatz: Ueber die oeffentlichen Methoden kann kein Netz entstehen, das auf
Modellebene ungueltig ist. Fehler werfen ModellFehler mit deutscher Meldung.
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# ── Konstanten ───────────────────────────────────────────────────────────────
FORMAT_VERSION = 1

NETZFORMEN = ("strahl", "ring")

# Sternpunktbehandlung am Knoten. Eigene, kurze Schluessel im Modell.
# Die Abbildung auf die Texte der Tabs (z. B. "Kompensiert (Petersen)" im
# Trafo-Tab, "Kompensiert (Petersen-Spule)" im Motor-Tab) macht der Adapter.
STERNPUNKTE = ("isoliert", "kompensiert", "niederohmig", "direkt")

ZUSTAENDE = ("ein", "aus")

# typ -> (braucht von-Knoten, braucht nach-Knoten)
ELEMENTTYPEN = {
    "einspeisung": (False, True),
    "generator":   (False, True),
    "trafo":       (True, True),
    "leitung":     (True, True),
    "kupplung":    (True, True),
    "motor":       (True, False),
}

# IDs werden spaeter als Graphviz-Knotennamen und Dateinamen genutzt,
# deshalb nur ein sicherer Zeichenvorrat.
_ID_MUSTER = re.compile(r"^[A-Za-z0-9_\-]{1,32}$")


class ModellFehler(ValueError):
    """Ungueltige Eingabe oder ungueltige Datei auf Modellebene."""


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────
def _pruefe_id(wert, was: str) -> str:
    if not isinstance(wert, str) or not _ID_MUSTER.match(wert):
        raise ModellFehler(
            f"{was}: ungültige ID {wert!r}. Erlaubt sind 1 bis 32 Zeichen "
            f"aus Buchstaben, Ziffern, '_' und '-'."
        )
    return wert


def _pruefe_zahl(wert, was: str, *, erlaubt_none: bool, groesser_null: bool):
    if wert is None:
        if erlaubt_none:
            return None
        raise ModellFehler(f"{was}: Wert fehlt.")
    # bool ist in Python ein int, soll hier aber nicht als Zahl durchgehen
    if isinstance(wert, bool) or not isinstance(wert, (int, float)):
        raise ModellFehler(f"{was}: Zahl erwartet, erhalten {wert!r}.")
    wert = float(wert)
    if wert != wert or wert in (float("inf"), float("-inf")):
        raise ModellFehler(f"{was}: ungültiger Zahlenwert {wert!r}.")
    if groesser_null and wert <= 0:
        raise ModellFehler(f"{was}: muss größer als 0 sein, erhalten {wert}.")
    return wert


def _pruefe_auswahl(wert, erlaubt, was: str) -> str:
    if wert not in erlaubt:
        raise ModellFehler(
            f"{was}: {wert!r} ist nicht zulässig. Erlaubt: {', '.join(erlaubt)}."
        )
    return wert


def _pruefe_parameter(p, was: str) -> dict:
    """p muss ein flaches Dict mit String-Schluesseln und einfachen Werten sein."""
    if p is None:
        return {}
    if not isinstance(p, dict):
        raise ModellFehler(f"{was}: Parametersatz muss ein Dict sein.")
    for k, v in p.items():
        if not isinstance(k, str):
            raise ModellFehler(f"{was}: Parameterschlüssel {k!r} ist kein Text.")
        if v is not None and not isinstance(v, (bool, int, float, str)):
            raise ModellFehler(
                f"{was}: Parameter {k!r} hat einen nicht speicherbaren Typ "
                f"({type(v).__name__})."
            )
    return copy.deepcopy(p)


# ── Datenklassen ─────────────────────────────────────────────────────────────
@dataclass
class Knoten:
    id: str
    name: str
    UN_kV: float
    sternpunkt: str
    Ik_max_kA: float | None = None
    Ik_min_kA: float | None = None

    def __post_init__(self):
        _pruefe_id(self.id, "Knoten")
        was = f"Knoten {self.id}"
        if not isinstance(self.name, str):
            raise ModellFehler(f"{was}: Name muss Text sein.")
        self.UN_kV = _pruefe_zahl(self.UN_kV, f"{was} UN", erlaubt_none=False, groesser_null=True)
        self.sternpunkt = _pruefe_auswahl(self.sternpunkt, STERNPUNKTE, f"{was} Sternpunkt")
        self.Ik_max_kA = _pruefe_zahl(self.Ik_max_kA, f"{was} Ik max", erlaubt_none=True, groesser_null=True)
        self.Ik_min_kA = _pruefe_zahl(self.Ik_min_kA, f"{was} Ik min", erlaubt_none=True, groesser_null=True)
        if (self.Ik_max_kA is not None and self.Ik_min_kA is not None
                and self.Ik_min_kA > self.Ik_max_kA):
            raise ModellFehler(
                f"{was}: Ik min ({self.Ik_min_kA} kA) ist größer als "
                f"Ik max ({self.Ik_max_kA} kA)."
            )

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "UN_kV": self.UN_kV,
            "sternpunkt": self.sternpunkt,
            "Ik_max_kA": self.Ik_max_kA, "Ik_min_kA": self.Ik_min_kA,
        }


@dataclass
class Element:
    id: str
    name: str
    typ: str
    von: str | None
    nach: str | None
    p: dict = field(default_factory=dict)
    zustand: str = "ein"

    def __post_init__(self):
        _pruefe_id(self.id, "Element")
        was = f"Element {self.id}"
        if not isinstance(self.name, str):
            raise ModellFehler(f"{was}: Name muss Text sein.")
        self.typ = _pruefe_auswahl(self.typ, tuple(ELEMENTTYPEN), f"{was} Typ")
        self.zustand = _pruefe_auswahl(self.zustand, ZUSTAENDE, f"{was} Zustand")
        braucht_von, braucht_nach = ELEMENTTYPEN[self.typ]
        for seite, braucht, wert in (("von", braucht_von, self.von),
                                     ("nach", braucht_nach, self.nach)):
            if braucht:
                _pruefe_id(wert, f"{was} ({seite}-Knoten)")
            elif wert is not None:
                raise ModellFehler(
                    f"{was}: Typ {self.typ} hat keinen {seite}-Knoten, "
                    f"angegeben war {wert!r}."
                )
        if self.von is not None and self.von == self.nach:
            raise ModellFehler(f"{was}: von- und nach-Knoten sind identisch ({self.von}).")
        self.p = _pruefe_parameter(self.p, was)

    @property
    def knoten_ids(self) -> tuple:
        """Alle Knoten, an denen das Element angeschlossen ist."""
        return tuple(k for k in (self.von, self.nach) if k is not None)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "typ": self.typ,
            "von": self.von, "nach": self.nach, "zustand": self.zustand,
            "p": copy.deepcopy(self.p),
        }


class Netz:
    """Gesamtnetz aus Knoten und Elementen. Einzige Wahrheit fuer den Netz-Tab."""

    def __init__(self, name: str = "Neues Netz", netzform: str = "strahl"):
        if not isinstance(name, str):
            raise ModellFehler("Netzname muss Text sein.")
        self.name = name
        self.netzform = _pruefe_auswahl(netzform, NETZFORMEN, "Netzform")
        self._knoten: dict[str, Knoten] = {}
        self._elemente: dict[str, Element] = {}

    # ── Lesen ────────────────────────────────────────────────────────────────
    @property
    def knoten(self) -> dict:
        """Kopie der Knoten (Aenderungen nur ueber die Methoden)."""
        return {k: copy.deepcopy(v) for k, v in self._knoten.items()}

    @property
    def elemente(self) -> dict:
        """Kopie der Elemente (Aenderungen nur ueber die Methoden)."""
        return {k: copy.deepcopy(v) for k, v in self._elemente.items()}

    def elemente_am_knoten(self, knoten_id: str) -> list:
        """IDs aller Elemente, die am Knoten angeschlossen sind."""
        return [e.id for e in self._elemente.values() if knoten_id in e.knoten_ids]

    # ── Netzform ─────────────────────────────────────────────────────────────
    def setze_netzform(self, netzform: str) -> None:
        self.netzform = _pruefe_auswahl(netzform, NETZFORMEN, "Netzform")

    # ── Knoten ───────────────────────────────────────────────────────────────
    def knoten_hinzufuegen(self, id: str, name: str, UN_kV: float, sternpunkt: str,
                           Ik_max_kA: float | None = None,
                           Ik_min_kA: float | None = None) -> Knoten:
        _pruefe_id(id, "Knoten")
        if id in self._knoten or id in self._elemente:
            raise ModellFehler(f"ID {id} ist bereits vergeben.")
        k = Knoten(id, name, UN_kV, sternpunkt, Ik_max_kA, Ik_min_kA)
        self._knoten[id] = k
        return copy.deepcopy(k)

    def knoten_aendern(self, id: str, /, **felder) -> None:
        if id not in self._knoten:
            raise ModellFehler(f"Knoten {id} existiert nicht.")
        if "id" in felder:
            raise ModellFehler("Die ID eines Knotens kann nicht geändert werden.")
        daten = self._knoten[id].to_dict()
        unbekannt = set(felder) - set(daten)
        if unbekannt:
            raise ModellFehler(f"Unbekannte Knotenfelder: {', '.join(sorted(unbekannt))}.")
        daten.update(felder)
        # Erst komplett pruefen, dann ersetzen. So bleibt der alte Stand bei Fehlern erhalten.
        self._knoten[id] = Knoten(**daten)

    def knoten_entfernen(self, id: str) -> None:
        if id not in self._knoten:
            raise ModellFehler(f"Knoten {id} existiert nicht.")
        belegt = self.elemente_am_knoten(id)
        if belegt:
            raise ModellFehler(
                f"Knoten {id} wird noch verwendet von: {', '.join(belegt)}. "
                f"Erst diese Elemente entfernen."
            )
        del self._knoten[id]

    # ── Elemente ─────────────────────────────────────────────────────────────
    def element_hinzufuegen(self, id: str, name: str, typ: str,
                            von: str | None, nach: str | None,
                            p: dict | None = None, zustand: str = "ein") -> Element:
        _pruefe_id(id, "Element")
        if id in self._elemente or id in self._knoten:
            raise ModellFehler(f"ID {id} ist bereits vergeben.")
        e = Element(id, name, typ, von, nach, p or {}, zustand)
        self._pruefe_knotenverweise(e)
        self._elemente[id] = e
        return copy.deepcopy(e)

    def element_aendern(self, id: str, /, **felder) -> None:
        if id not in self._elemente:
            raise ModellFehler(f"Element {id} existiert nicht.")
        if "id" in felder:
            raise ModellFehler("Die ID eines Elements kann nicht geändert werden.")
        daten = self._elemente[id].to_dict()
        unbekannt = set(felder) - set(daten)
        if unbekannt:
            raise ModellFehler(f"Unbekannte Elementfelder: {', '.join(sorted(unbekannt))}.")
        daten.update(felder)
        e = Element(**daten)
        self._pruefe_knotenverweise(e)
        self._elemente[id] = e

    def parameter_setzen(self, id: str, p: dict) -> None:
        """Parametersatz komplett ersetzen, z. B. 'In Netz übernehmen' aus einem Tab."""
        self.element_aendern(id, p=p)

    def element_entfernen(self, id: str) -> None:
        if id not in self._elemente:
            raise ModellFehler(f"Element {id} existiert nicht.")
        del self._elemente[id]

    def _pruefe_knotenverweise(self, e: Element) -> None:
        for k in e.knoten_ids:
            if k not in self._knoten:
                raise ModellFehler(f"Element {e.id}: Knoten {k} existiert nicht.")

    # ── Serialisierung ───────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "format_version": FORMAT_VERSION,
            "name": self.name,
            "netzform": self.netzform,
            "knoten": [k.to_dict() for k in self._knoten.values()],
            "elemente": [e.to_dict() for e in self._elemente.values()],
        }

    @classmethod
    def from_dict(cls, daten) -> "Netz":
        """Baut ein Netz aus einem Dict. Jeder Fehler wird als ModellFehler gemeldet."""
        if not isinstance(daten, dict):
            raise ModellFehler("Netzdatei: oberste Ebene muss ein Objekt sein.")
        version = daten.get("format_version")
        if version != FORMAT_VERSION:
            raise ModellFehler(
                f"Netzdatei: Formatversion {version!r} wird nicht unterstützt "
                f"(erwartet {FORMAT_VERSION})."
            )
        for schluessel in ("name", "netzform", "knoten", "elemente"):
            if schluessel not in daten:
                raise ModellFehler(f"Netzdatei: Eintrag '{schluessel}' fehlt.")
        if not isinstance(daten["knoten"], list) or not isinstance(daten["elemente"], list):
            raise ModellFehler("Netzdatei: 'knoten' und 'elemente' müssen Listen sein.")

        netz = cls(daten["name"], daten["netzform"])
        # Erst alle Knoten, dann die Elemente, damit Verweise aufgeloest werden koennen
        for i, k in enumerate(daten["knoten"]):
            if not isinstance(k, dict):
                raise ModellFehler(f"Netzdatei: Knoten Nr. {i + 1} ist kein Objekt.")
            try:
                netz.knoten_hinzufuegen(**k)
            except TypeError as exc:
                raise ModellFehler(f"Netzdatei: Knoten Nr. {i + 1} hat falsche Felder ({exc}).") from None
        for i, e in enumerate(daten["elemente"]):
            if not isinstance(e, dict):
                raise ModellFehler(f"Netzdatei: Element Nr. {i + 1} ist kein Objekt.")
            try:
                netz.element_hinzufuegen(**e)
            except TypeError as exc:
                raise ModellFehler(f"Netzdatei: Element Nr. {i + 1} hat falsche Felder ({exc}).") from None
        return netz

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, text: str) -> "Netz":
        try:
            daten = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ModellFehler(f"Netzdatei ist kein gültiges JSON (Zeile {exc.lineno}).") from None
        return cls.from_dict(daten)

    def speichern(self, pfad) -> None:
        Path(pfad).write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def laden(cls, pfad) -> "Netz":
        return cls.from_json(Path(pfad).read_text(encoding="utf-8"))

    def __eq__(self, other) -> bool:
        return isinstance(other, Netz) and self.to_dict() == other.to_dict()

    def __repr__(self) -> str:
        return (f"Netz({self.name!r}, {self.netzform}, "
                f"{len(self._knoten)} Knoten, {len(self._elemente)} Elemente)")
