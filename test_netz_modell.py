"""
test_netz_modell.py - Tests fuer das Netzmodell (netz_modell.py)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Ausfuehren mit:  python test_netz_modell.py   (oder: pytest test_netz_modell.py)

Prueft:
1. Referenznetz: beispielnetze/industrie_10kV.json laedt fehlerfrei und hat
   die erwartete Struktur.
2. Speichern und Laden: Hin- und Rueckweg ueber JSON verlustfrei.
3. Negativtests: Jede ungueltige Eingabe wird mit ModellFehler abgewiesen,
   und ein fehlgeschlagener Aufruf veraendert das Netz nicht.
4. Kapselung: Von aussen gelesene Daten koennen das Modell nicht veraendern.
"""

import json
import tempfile
from pathlib import Path

from netz_modell import ModellFehler, Netz

REFERENZNETZ = Path(__file__).parent / "beispielnetze" / "industrie_10kV.json"


def _erwarte_fehler(funktion, *args, enthaelt: str = "", **kwargs) -> str:
    """Eigener Ersatz fuer pytest.raises, damit der Test auch ohne pytest laeuft."""
    try:
        funktion(*args, **kwargs)
    except ModellFehler as exc:
        meldung = str(exc)
        assert enthaelt in meldung, f"Meldung {meldung!r} enthält nicht {enthaelt!r}"
        return meldung
    raise AssertionError(f"Kein ModellFehler bei {funktion.__name__}{args}{kwargs}")


def _kleines_netz() -> Netz:
    n = Netz("Test", "strahl")
    n.knoten_hinzufuegen("K1", "Schiene 1", 10, "isoliert", 10.0, 7.0)
    n.knoten_hinzufuegen("K2", "Schiene 2", 10, "isoliert")
    n.element_hinzufuegen("E1", "Einspeisung", "einspeisung", None, "K1")
    n.element_hinzufuegen("L1", "Kabel", "leitung", "K1", "K2", {"L_km": 1.0})
    return n


# ── 1. Referenznetz ──────────────────────────────────────────────────────────
def test_referenznetz_laden():
    n = Netz.laden(REFERENZNETZ)
    assert n.netzform == "strahl"
    assert sorted(n.knoten) == ["K1", "K2", "K3", "K4", "K5"]
    assert sorted(n.elemente) == ["E1", "L1", "L2", "M1", "T1", "T2"]
    t1 = n.elemente["T1"]
    assert (t1.typ, t1.von, t1.nach) == ("trafo", "K1", "K2")
    assert t1.p["Sn_MVA"] == 20 and t1.p["uk_pct"] == 12
    assert n.knoten["K2"].sternpunkt == "isoliert"
    assert n.elemente["M1"].nach is None
    assert sorted(n.elemente_am_knoten("K2")) == ["L1", "L2", "T1"]
    print("Referenznetz OK: 5 Knoten, 6 Elemente, Strahlennetz.")


# ── 2. Speichern und Laden ───────────────────────────────────────────────────
def test_json_hin_und_zurueck():
    n = Netz.laden(REFERENZNETZ)
    assert Netz.from_json(n.to_json()) == n
    with tempfile.TemporaryDirectory() as tmp:
        pfad = Path(tmp) / "netz.json"
        n.speichern(pfad)
        assert Netz.laden(pfad) == n
        # Umlaute muessen als echte Zeichen in der Datei stehen
        assert "Übergabe" in pfad.read_text(encoding="utf-8")
    print("Speichern/Laden OK: JSON-Rundweg verlustfrei, Umlaute erhalten.")


# ── 3. Negativtests ──────────────────────────────────────────────────────────
def test_negativ_knoten():
    n = _kleines_netz()
    _erwarte_fehler(n.knoten_hinzufuegen, "K1", "doppelt", 10, "isoliert", enthaelt="bereits vergeben")
    _erwarte_fehler(n.knoten_hinzufuegen, "L1", "wie Element", 10, "isoliert", enthaelt="bereits vergeben")
    _erwarte_fehler(n.knoten_hinzufuegen, "K 3", "Leerzeichen", 10, "isoliert", enthaelt="ungültige ID")
    _erwarte_fehler(n.knoten_hinzufuegen, "", "leer", 10, "isoliert", enthaelt="ungültige ID")
    _erwarte_fehler(n.knoten_hinzufuegen, "K3", "x", 0, "isoliert", enthaelt="größer als 0")
    _erwarte_fehler(n.knoten_hinzufuegen, "K3", "x", -10, "isoliert", enthaelt="größer als 0")
    _erwarte_fehler(n.knoten_hinzufuegen, "K3", "x", "10", "isoliert", enthaelt="Zahl erwartet")
    _erwarte_fehler(n.knoten_hinzufuegen, "K3", "x", True, "isoliert", enthaelt="Zahl erwartet")
    _erwarte_fehler(n.knoten_hinzufuegen, "K3", "x", float("nan"), "isoliert", enthaelt="ungültiger Zahlenwert")
    _erwarte_fehler(n.knoten_hinzufuegen, "K3", "x", 10, "geerdet", enthaelt="nicht zulässig")
    _erwarte_fehler(n.knoten_hinzufuegen, "K3", "x", 10, "isoliert", 5.0, 8.0, enthaelt="größer als")
    _erwarte_fehler(n.knoten_entfernen, "K1", enthaelt="noch verwendet")
    _erwarte_fehler(n.knoten_entfernen, "K9", enthaelt="existiert nicht")
    _erwarte_fehler(n.knoten_aendern, "K1", id="K7", enthaelt="nicht geändert")
    _erwarte_fehler(n.knoten_aendern, "K1", UN_kV=-1, enthaelt="größer als 0")
    assert sorted(n.knoten) == ["K1", "K2"], "Fehlversuche dürfen das Netz nicht ändern"
    print("Negativtests Knoten OK.")


def test_negativ_elemente():
    n = _kleines_netz()
    _erwarte_fehler(n.element_hinzufuegen, "X1", "x", "schalter", "K1", "K2", enthaelt="nicht zulässig")
    _erwarte_fehler(n.element_hinzufuegen, "L2", "x", "leitung", "K1", "K9", enthaelt="existiert nicht")
    _erwarte_fehler(n.element_hinzufuegen, "L2", "x", "leitung", "K1", "K1", enthaelt="identisch")
    _erwarte_fehler(n.element_hinzufuegen, "L2", "x", "leitung", None, "K2", enthaelt="ungültige ID")
    _erwarte_fehler(n.element_hinzufuegen, "M1", "x", "motor", "K2", "K1", enthaelt="keinen nach-Knoten")
    _erwarte_fehler(n.element_hinzufuegen, "E2", "x", "einspeisung", "K1", "K2", enthaelt="keinen von-Knoten")
    _erwarte_fehler(n.element_hinzufuegen, "L2", "x", "leitung", "K1", "K2", zustand="offen", enthaelt="nicht zulässig")
    _erwarte_fehler(n.element_hinzufuegen, "L2", "x", "leitung", "K1", "K2", p=[1, 2], enthaelt="Dict")
    _erwarte_fehler(n.element_hinzufuegen, "L2", "x", "leitung", "K1", "K2", p={"a": [1]}, enthaelt="nicht speicherbaren")
    _erwarte_fehler(n.element_hinzufuegen, "L1", "x", "leitung", "K1", "K2", enthaelt="bereits vergeben")
    _erwarte_fehler(n.element_aendern, "L1", nach="K9", enthaelt="existiert nicht")
    _erwarte_fehler(n.element_aendern, "L1", id="L5", enthaelt="nicht geändert")
    _erwarte_fehler(n.element_aendern, "L1", farbe="rot", enthaelt="Unbekannte")
    _erwarte_fehler(n.element_entfernen, "L9", enthaelt="existiert nicht")
    # Nach allen Fehlversuchen ist L1 unveraendert
    l1 = n.elemente["L1"]
    assert (l1.von, l1.nach, l1.p) == ("K1", "K2", {"L_km": 1.0})
    assert sorted(n.elemente) == ["E1", "L1"]
    print("Negativtests Elemente OK.")


def test_negativ_dateien():
    gut = _kleines_netz().to_dict()
    _erwarte_fehler(Netz.from_json, "{kein json", enthaelt="kein gültiges JSON")
    _erwarte_fehler(Netz.from_json, "[]", enthaelt="oberste Ebene")
    for kaputt, erwartet in (
        ({**gut, "format_version": 99}, "Formatversion"),
        ({k: v for k, v in gut.items() if k != "format_version"}, "Formatversion"),
        ({k: v for k, v in gut.items() if k != "knoten"}, "'knoten' fehlt"),
        ({**gut, "elemente": "x"}, "Listen"),
        ({**gut, "netzform": "masche"}, "nicht zulässig"),
        ({**gut, "knoten": [{"id": "K1"}]}, "falsche Felder"),
        ({**gut, "knoten": ["K1"]}, "kein Objekt"),
        ({**gut, "knoten": gut["knoten"][:1]}, "existiert nicht"),
    ):
        _erwarte_fehler(Netz.from_json, json.dumps(kaputt), enthaelt=erwartet)
    print("Negativtests Dateien OK: 10 kaputte Netzdateien abgewiesen.")


# ── 4. Kapselung und Aendern ─────────────────────────────────────────────────
def test_kapselung_und_aendern():
    n = _kleines_netz()
    # Von aussen veraenderte Kopien duerfen das Modell nicht beruehren
    n.elemente["L1"].p["L_km"] = 99.0
    n.knoten["K1"].UN_kV = 20.0
    assert n.elemente["L1"].p["L_km"] == 1.0
    assert n.knoten["K1"].UN_kV == 10.0
    # Uebergebenes p wird kopiert, nicht referenziert
    p = {"Sn_MVA": 1.6}
    n.knoten_hinzufuegen("K3", "NS", 0.4, "direkt")
    n.element_hinzufuegen("T2", "Trafo", "trafo", "K2", "K3", p)
    p["Sn_MVA"] = 100.0
    assert n.elemente["T2"].p["Sn_MVA"] == 1.6
    # Gueltige Aenderungen greifen
    n.parameter_setzen("T2", {"Sn_MVA": 2.0, "uk_pct": 6})
    n.knoten_aendern("K2", Ik_max_kA=8.0, Ik_min_kA=6.0)
    n.element_aendern("L1", zustand="aus")
    n.setze_netzform("ring")
    assert n.elemente["T2"].p == {"Sn_MVA": 2.0, "uk_pct": 6}
    assert n.knoten["K2"].Ik_max_kA == 8.0
    assert n.elemente["L1"].zustand == "aus"
    assert n.netzform == "ring"
    # Entfernen in der richtigen Reihenfolge klappt
    n.element_entfernen("T2")
    n.knoten_entfernen("K3")
    assert "K3" not in n.knoten
    print("Kapselung und Ändern OK.")


if __name__ == "__main__":
    test_referenznetz_laden()
    test_json_hin_und_zurueck()
    test_negativ_knoten()
    test_negativ_elemente()
    test_negativ_dateien()
    test_kapselung_und_aendern()
    print("\nAlle Prüfungen bestanden.")
