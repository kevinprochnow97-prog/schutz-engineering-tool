"""
test_netz_bild.py - Tests fuer das Einlinienbild (netz_bild.py)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Ausfuehren mit:  python test_netz_bild.py   (oder: pytest test_netz_bild.py)

Prueft Inhalt und Kennzeichnung des DOT-Textes. Ist Graphviz (dot) installiert,
wird der Text zusaetzlich gerendert und damit die Syntax geprueft. Ohne
Graphviz entfaellt nur dieser Teil, Streamlit selbst braucht es nicht.
"""

import shutil
import subprocess
from pathlib import Path

from netz_bild import FARBE_AUS, FARBE_FEHLER, FARBE_RING, einlinienbild_dot
from netz_modell import Netz
from netz_topologie import analysiere

REFERENZNETZ = Path(__file__).parent / "beispielnetze" / "industrie_10kV.json"


def _render_ok(dot: str) -> bool:
    if not shutil.which("dot"):
        return True
    r = subprocess.run(["dot", "-Tsvg"], input=dot.encode("utf-8"), capture_output=True)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    return True


def test_referenznetz():
    n = Netz.laden(REFERENZNETZ)
    dot = einlinienbild_dot(n, analysiere(n))
    for k in ("k_K1", "k_K2", "k_K3", "k_K4", "k_K5", "e_E1", "e_T1", "e_T2", "e_M1"):
        assert k in dot, k
    assert 'label="L1"' in dot and 'label="L2"' in dot
    assert FARBE_FEHLER not in dot and FARBE_AUS not in dot
    assert "0,4 kV" in dot                                  # deutsches Dezimalkomma
    _render_ok(dot)
    print("Referenznetz OK: alle Knoten und Elemente im Bild.")


def test_ring_aus_fehler():
    n = Netz.laden(REFERENZNETZ)
    n.setze_netzform("ring")
    n.element_hinzufuegen("KU1", "Kupplung", "kupplung", "K3", "K4", zustand="aus")
    dot = einlinienbild_dot(n, analysiere(n))
    assert "(Trennstelle)" in dot and FARBE_RING in dot and 'style="dashed"' in dot
    _render_ok(dot)

    n.setze_netzform("strahl")                              # Masche im Strahl: Fehler, rot
    dot = einlinienbild_dot(n, analysiere(n))
    assert FARBE_FEHLER in dot
    _render_ok(dot)
    print("Ring, Trennstelle und Fehlerfarbe OK.")


def test_sonderzeichen():
    n = Netz()
    n.knoten_hinzufuegen("K1", 'Halle "Nord" \\ Süd', 10, "isoliert")
    n.element_hinzufuegen("E1", "Netz", "einspeisung", None, "K1")
    dot = einlinienbild_dot(n, analysiere(n))
    assert 'Halle \\"Nord\\" \\\\ Süd' in dot
    _render_ok(dot)
    dot = einlinienbild_dot(Netz())                         # leeres Netz, ohne Topologie
    assert dot.startswith("digraph") and _render_ok(dot)
    print("Sonderzeichen und leeres Netz OK.")


if __name__ == "__main__":
    test_referenznetz()
    test_ring_aus_fehler()
    test_sonderzeichen()
    print("\nAlle Prüfungen bestanden.")
