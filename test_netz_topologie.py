"""
test_netz_topologie.py - Tests fuer die Topologieanalyse (netz_topologie.py)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Ausfuehren mit:  python test_netz_topologie.py   (oder: pytest test_netz_topologie.py)

Prueft:
1. Referenznetz (Strahl): fehlerfrei, Pfade zur Quelle, Abgaenge.
2. Ringvariante (Kupplung K3-K4): offener Ring, Trennstelle, Umschaltung.
3. Negativtests Netzform: Masche im Strahl, Ring ohne Masche, geschlossener
   Ring, vermascht, zwei Trennstellen.
4. Negativtests Quelle, Zusammenhang, Spannungen.
5. Randfaelle: leeres Netz, ausgeschalteter Abgang, parallele Kabel.
6. Zufallsnetze: 500 Netze, kein Absturz, Pfade bei gueltigem Ergebnis vollstaendig.
"""

from pathlib import Path

from netz_modell import Netz
from netz_topologie import FEHLER, HINWEIS, WARNUNG, analysiere

REFERENZNETZ = Path(__file__).parent / "beispielnetze" / "industrie_10kV.json"


def _ref() -> Netz:
    return Netz.laden(REFERENZNETZ)


def _ring(kupplung_zustand: str = "aus") -> Netz:
    """Referenznetz plus Kupplung K3-K4 als Ringschluss."""
    n = _ref()
    n.setze_netzform("ring")
    n.element_hinzufuegen("KU1", "Kupplung K3-K4", "kupplung", "K3", "K4", zustand=kupplung_zustand)
    return n


def _texte(erg, stufe) -> str:
    return " | ".join(m.text for m in erg.meldungen_der_stufe(stufe))


def _hat(erg, stufe, enthaelt):
    t = _texte(erg, stufe)
    assert enthaelt in t, f"Erwartet {stufe} mit {enthaelt!r}, erhalten: {t!r}"


# ── 1. Referenznetz ──────────────────────────────────────────────────────────
def test_referenznetz():
    erg = analysiere(_ref())
    assert erg.ok, erg.meldungen
    assert erg.meldungen == [], erg.meldungen
    assert (erg.netzform_erkannt, erg.maschen_gesamt, erg.quelle) == ("strahl", 0, "E1")
    assert erg.zufuehrung == {"K2": "T1", "K3": "L1", "K4": "L2", "K5": "T2"}
    assert erg.pfad_zur_quelle("M1") == ["M1", "L1", "T1", "E1"]
    assert erg.pfad_zur_quelle("T2") == ["T2", "L2", "T1", "E1"]
    assert erg.pfad_zur_quelle("T1") == ["T1", "E1"]
    assert erg.pfad_zur_quelle("E1") == ["E1"]
    assert erg.abgaenge("K2") == ["L1", "L2"]
    assert erg.abgaenge("K3") == ["M1"]
    assert erg.abgaenge("K1") == ["T1"]
    print("Referenznetz OK: Strahl, keine Meldungen, Staffelpfade M1 -> L1 -> T1 -> E1.")


# ── 2. Ringvariante ──────────────────────────────────────────────────────────
def test_offener_ring():
    erg = analysiere(_ring("aus"))
    assert erg.ok, erg.meldungen
    assert (erg.netzform_erkannt, erg.maschen_gesamt, erg.maschen_betrieb) == ("ring", 1, 0)
    assert erg.ring_elemente == ("KU1", "L1", "L2")
    assert erg.trennstelle == "KU1"
    _hat(erg, HINWEIS, "Trennstelle bei KU1")
    assert erg.pfad_zur_quelle("T2") == ["T2", "L2", "T1", "E1"]
    assert erg.pfad_zur_quelle("KU1") == []        # offen, liegt nicht im Versorgungsbaum

    # Trennstelle verlegen: Kupplung ein, L2 aus. T2 wird jetzt ueber L1 und KU1 versorgt.
    n = _ring("ein")
    n.element_aendern("L2", zustand="aus")
    erg = analysiere(n)
    assert erg.ok, erg.meldungen
    assert erg.trennstelle == "L2"
    assert erg.unversorgt == ()
    assert erg.pfad_zur_quelle("T2") == ["T2", "KU1", "L1", "T1", "E1"]
    assert erg.abgaenge("K3") == ["KU1", "M1"]
    print("Offener Ring OK: Trennstelle erkannt, Versorgung folgt dem Schaltzustand.")


# ── 3. Negativtests Netzform ─────────────────────────────────────────────────
def test_negativ_netzform():
    n = _ring("aus")
    n.setze_netzform("strahl")
    erg = analysiere(n)
    assert not erg.ok
    _hat(erg, FEHLER, "Strahlennetz gewählt")
    assert erg.pfad_zur_quelle("M1") == []          # bei Fehlern keine Pfade

    n = _ref()
    n.setze_netzform("ring")
    _hat(analysiere(n), FEHLER, "keine Masche")

    _hat(analysiere(_ring("ein")), FEHLER, "geschlossen betrieben")

    n = _ring("aus")
    n.element_aendern("L1", zustand="aus")
    _hat(analysiere(n), FEHLER, "Mehrere offene Elemente")

    n = _ring("aus")
    n.element_hinzufuegen("L3", "Kabel K2-K3 parallel", "leitung", "K2", "K3")
    erg = analysiere(n)
    assert erg.maschen_gesamt == 2
    _hat(erg, FEHLER, "vermascht")
    print("Negativtests Netzform OK.")


# ── 4. Negativtests Quelle, Zusammenhang, Spannung ───────────────────────────
def test_negativ_quelle():
    n = _ref()
    n.element_entfernen("E1")
    _hat(analysiere(n), FEHLER, "Keine Einspeisung")

    n = _ref()
    n.element_hinzufuegen("G1", "Generator", "generator", None, "K2")
    _hat(analysiere(n), FEHLER, "Mehrere Quellen")

    n = _ref()
    n.element_aendern("E1", zustand="aus")
    erg = analysiere(n)
    _hat(erg, FEHLER, "ausgeschaltet")
    print("Negativtests Quelle OK.")


def test_negativ_zusammenhang():
    n = _ref()
    n.knoten_hinzufuegen("K9", "Reserve", 10, "isoliert")
    erg = analysiere(n)
    assert erg.ok                                    # unbenutzter Knoten ist nur eine Warnung
    _hat(erg, WARNUNG, "K9 ist mit keinem Element")

    n.knoten_hinzufuegen("K8", "Insel", 10, "isoliert")
    n.element_hinzufuegen("L9", "Inselkabel", "leitung", "K8", "K9")
    _hat(analysiere(n), FEHLER, "2 getrennte Teile")
    print("Negativtests Zusammenhang OK.")


def test_negativ_spannung():
    n = _ref()
    n.knoten_hinzufuegen("K6", "NS 2", 0.4, "direkt")
    n.element_hinzufuegen("L9", "Kabel 10 kV auf 0,4 kV", "leitung", "K4", "K6")
    _hat(analysiere(n), FEHLER, "Unterschiedliche Spannungen nur über einen Trafo")

    n = _ref()
    n.knoten_hinzufuegen("K6", "NS 2", 0.4, "direkt")
    n.element_hinzufuegen("T9", "Trafo verkehrt", "trafo", "K6", "K4")
    _hat(analysiere(n), FEHLER, "Richtung tauschen")

    n = _ref()
    n.knoten_hinzufuegen("K6", "10 kV", 10, "isoliert")
    n.element_hinzufuegen("T9", "Trafo 10/10", "trafo", "K4", "K6")
    _hat(analysiere(n), FEHLER, "gleicher Spannung")

    # Tab-Wert weicht vom Knoten ab: nur Warnung, Knoten ist die Wahrheit
    n = _ref()
    p = n.elemente["T1"].p
    p["UN_US_kV"] = 20.0
    n.parameter_setzen("T1", p)
    p_m = n.elemente["M1"].p
    p_m["UN_kV"] = 6.0
    n.parameter_setzen("M1", p_m)
    erg = analysiere(n)
    assert erg.ok
    _hat(erg, WARNUNG, "T1: UN_US_kV = 20 kV")
    _hat(erg, WARNUNG, "M1: UN_kV = 6 kV")
    print("Negativtests Spannung OK.")


# ── 5. Randfaelle ────────────────────────────────────────────────────────────
def test_randfaelle():
    erg = analysiere(Netz())
    assert not erg.ok and erg.netzform_erkannt == "leer"
    _hat(erg, FEHLER, "leer")

    n = Netz()
    n.knoten_hinzufuegen("K1", "Schiene", 10, "isoliert")
    erg = analysiere(n)                               # nur ein Knoten: darf nicht abstuerzen
    _hat(erg, FEHLER, "Keine Einspeisung")

    n = _ref()
    n.element_aendern("L2", zustand="aus")
    erg = analysiere(n)
    assert erg.ok
    assert erg.unversorgt == ("K4", "K5")
    _hat(erg, WARNUNG, "nicht versorgt: K4, K5")
    _hat(erg, HINWEIS, "L2 ist ausgeschaltet")
    assert erg.pfad_zur_quelle("T2") == []
    assert erg.abgaenge("K2") == ["L1"]

    n = _ref()
    n.element_aendern("M1", zustand="aus")
    erg = analysiere(n)
    assert erg.ok and erg.unversorgt == ()
    assert erg.pfad_zur_quelle("M1") == []

    # Doppelkabel als Ring: parallele Kanten sind eine Masche
    n = _ref()
    n.setze_netzform("ring")
    n.element_hinzufuegen("L1b", "Kabel K2-K3 parallel", "leitung", "K2", "K3", zustand="aus")
    erg = analysiere(n)
    assert erg.ok and erg.trennstelle == "L1b" and erg.ring_elemente == ("L1", "L1b")
    print("Randfälle OK: leeres Netz, ausgeschaltete Abgänge, Parallelkabel.")


# ── 6. Zufallsnetze (Robustheit) ─────────────────────────────────────────────
def test_zufallsnetze():
    """
    500 zufaellige Netze, auch unsinnige. Anforderungen:
    analysiere() wirft nie, und bei ok hat jedes eingeschaltete, versorgte
    Element einen Pfad, der bei der Quelle endet.
    """
    import random
    rnd = random.Random(20261109)          # fester Startwert, damit Fehler reproduzierbar sind
    typen = ["trafo", "leitung", "leitung", "kupplung", "motor", "einspeisung", "generator"]
    anzahl_ok = 0
    for lauf in range(500):
        n = Netz(netzform=rnd.choice(["strahl", "ring"]))
        kn = [f"K{i}" for i in range(rnd.randint(1, 7))]
        for k in kn:
            n.knoten_hinzufuegen(k, k, rnd.choice([0.4, 10, 10, 110]), "isoliert")
        for j in range(rnd.randint(0, 9)):
            typ = rnd.choice(typen)
            a, b = rnd.choice(kn), rnd.choice(kn)
            von = None if typ in ("einspeisung", "generator") else a
            nach = None if typ == "motor" else b
            if von is not None and von == nach:
                continue
            n.element_hinzufuegen(f"X{j}", typ, typ, von, nach,
                                  zustand=rnd.choice(["ein", "ein", "ein", "aus"]))
        erg = analysiere(n)                # darf nicht werfen
        for eid in n.elemente:
            erg.pfad_zur_quelle(eid)       # darf nicht werfen
        for k in kn:
            erg.abgaenge(k)
        if erg.ok:
            anzahl_ok += 1
            versorgt = set(erg.zufuehrung) | {n.elemente[erg.quelle].nach}
            for eid, e in n.elemente.items():
                if e.zustand != "ein" or not set(e.knoten_ids) <= versorgt:
                    continue
                if e.von is not None and e.nach is not None and eid not in erg.zufuehrung.values():
                    continue               # Kante ausserhalb des Versorgungsbaums
                pfad = erg.pfad_zur_quelle(eid)
                assert pfad and pfad[-1] == erg.quelle, (lauf, eid, pfad)
    assert anzahl_ok > 20, f"Zu wenige gültige Zufallsnetze ({anzahl_ok}), Test aussagelos"
    print(f"Zufallsnetze OK: 500 Netze ohne Absturz, {anzahl_ok} davon gültig und mit vollständigen Pfaden.")


if __name__ == "__main__":
    test_referenznetz()
    test_offener_ring()
    test_negativ_netzform()
    test_negativ_quelle()
    test_negativ_zusammenhang()
    test_negativ_spannung()
    test_randfaelle()
    test_zufallsnetze()
    print("\nAlle Prüfungen bestanden.")
