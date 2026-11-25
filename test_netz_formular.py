"""
test_netz_formular.py - Modultests fuer netz_formular.py (ohne Streamlit)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Ausfuehren mit:  pytest test_netz_formular.py

Prueft:
1. Vorbelegung der Anlegen-Formulare passt zu den Modellwerten.
2. Anlegen: Knoten und Element, Tab-Parameter, Netzbetreiber-Werte, Fehler lassen das Netz unveraendert.
3. Bearbeiten Knoten: alle Felder, ID und Verbindungen bleiben, Fehler lassen den Knoten unveraendert.
4. Bearbeiten Element: von/nach/Name, Parameter und Zustand bleiben, Fehler lassen das Element unveraendert.
"""

from pathlib import Path

import pytest

import netz_formular as F
from netz_modell import ELEMENTTYPEN, STERNPUNKTE, ModellFehler, Netz

BEISPIEL = Path(__file__).parent / "beispielnetze" / "industrie_10kV.json"


def _netz() -> Netz:
    return Netz.laden(BEISPIEL)


# ── 1. Vorbelegung ───────────────────────────────────────────────────────────
def test_vorbelegung_passt_zum_modell():
    assert F.KNOTEN_LEER["sternpunkt"] in STERNPUNKTE
    assert F.ELEMENT_LEER["typ"] in ELEMENTTYPEN
    assert F.ELEMENT_LEER["id"] == "" and F.KNOTEN_LEER["id"] == ""
    assert F.KNOTEN_LEER["UN_kV"] is None and F.ELEMENT_LEER["I_nb_A"] is None
    assert F.ELEMENT_LEER["von"] == F.ELEMENT_LEER["nach"] == F.OHNE


# ── 2. Anlegen ───────────────────────────────────────────────────────────────
def test_knoten_anlegen():
    n = _netz()
    assert F.knoten_anlegen(n, " K6 ", " Halle 3 ", 10, "kompensiert", 0, 3.5) == "Knoten K6 angelegt."
    k = n.knoten["K6"]
    assert (k.name, k.UN_kV, k.sternpunkt, k.Ik_max_kA, k.Ik_min_kA) == ("Halle 3", 10.0, "kompensiert", None, 3.5)


@pytest.mark.parametrize("kid, un, ikmax, ikmin, text", [
    ("K1", 10.0, None, None, "bereits vergeben"),
    ("K6", None, None, None, "Wert fehlt"),
    ("K6", 10.0, 2.0, 5.0, "größer als"),
    ("", 10.0, None, None, "ungültige ID"),
])
def test_knoten_anlegen_fehler_laesst_netz_unveraendert(kid, un, ikmax, ikmin, text):
    n = _netz()
    vorher = n.to_dict()
    with pytest.raises(ModellFehler, match=text):
        F.knoten_anlegen(n, kid, "x", un, "isoliert", ikmax, ikmin)
    assert n.to_dict() == vorher


IMMER_AKTIV = {"uebs_betriebsart": "Ein: immer aktiv"}


def test_element_anlegen_mit_tab_parametern():
    n = _netz()
    p_tab = {"Sn_MVA": 16.0, "uk_pct": 6.0}
    meldung = F.element_anlegen(n, "T3", "Trafo 3", "trafo", "K4", "K5", "aus",
                                p_tab=p_tab, tab_name="Transformator")
    assert "Parameter aus dem Tab Transformator übernommen" in meldung
    e = n.elemente["T3"]
    assert (e.von, e.nach, e.zustand, e.p) == ("K4", "K5", "aus", p_tab)
    p_tab["Sn_MVA"] = 99.0                                  # Kopie, keine Rueckwirkung
    assert n.elemente["T3"].p["Sn_MVA"] == 16.0
    # ohne Tab-Daten: Hinweis, Parameter leer
    meldung = F.element_anlegen(n, "L3", "", "leitung", "K4", "K3", p_tab=None, tab_name="Leitung")
    assert "noch keine Grunddaten" in meldung and n.elemente["L3"].p == IMMER_AKTIV
    # Haekchen aus: nichts uebernehmen, kein Hinweis
    meldung = F.element_anlegen(n, "L4", "", "leitung", "K4", "K3", p_tab=p_tab, tab_name="Leitung",
                                uebernehmen=False)
    assert meldung == "Element L4 angelegt." and n.elemente["L4"].p == IMMER_AKTIV
    # Leitung: Not-UMZ immer aktiv vorbelegt (Entscheidung 17.11.2026); Tab-Voreinstellung wird
    # ersetzt und gemeldet, ein bewusst gesetztes "Aus" bleibt
    meldung = F.element_anlegen(n, "L5", "", "leitung", "K4", "K3", tab_name="Leitung",
                                p_tab={"uebs_betriebsart": "Ein: bei U-Ausfall", "Un_kV": 20.0})
    assert n.elemente["L5"].p["uebs_betriebsart"] == "Ein: immer aktiv" and "Staffelung" in meldung
    assert n.elemente["L5"].p["Un_kV"] == 20.0
    F.element_anlegen(n, "L6", "", "leitung", "K4", "K3", tab_name="Leitung",
                      p_tab={"uebs_betriebsart": "Aus"})
    assert n.elemente["L6"].p["uebs_betriebsart"] == "Aus"
    F.element_anlegen(n, "T4", "", "trafo", "K4", "K5", uebernehmen=False)
    assert n.elemente["T4"].p == {}                          # nur die Leitung wird vorbelegt


def test_element_anlegen_ignoriert_nicht_benoetigte_knoten_und_setzt_netzbetreiber():
    n = _netz()
    F.element_anlegen(n, "E2", "Einspeisung 2", "einspeisung", "K2", "K1", I_nb_A=200, t_nb_s=1.0)
    e = n.elemente["E2"]
    assert (e.von, e.nach) == (None, "K1") and e.p == {"I_gt_NB_A": 200.0, "t_gt_NB_s": 1.0}
    F.element_anlegen(n, "M2", "Motor 2", "motor", "K3", "K4")
    assert (n.elemente["M2"].von, n.elemente["M2"].nach) == ("K3", None)
    F.element_anlegen(n, "G1", "Generator", "generator", F.OHNE, "K3")
    assert n.elemente["G1"].nach == "K3"


@pytest.mark.parametrize("args, text", [
    (("L1", "", "leitung", "K2", "K3"), "bereits vergeben"),
    (("L9", "", "leitung", "K2", "K2"), "identisch"),
    (("L9", "", "leitung", "K2", "K99"), "existiert nicht"),
    (("L9", "", "leitung", F.OHNE, "K3"), "ungültige ID"),
    (("L9", "", "geheim", "K2", "K3"), "nicht zulässig"),
])
def test_element_anlegen_fehler_laesst_netz_unveraendert(args, text):
    n = _netz()
    vorher = n.to_dict()
    with pytest.raises(ModellFehler, match=text):
        F.element_anlegen(n, *args)
    assert n.to_dict() == vorher


# ── 3. Bearbeiten: Knoten ────────────────────────────────────────────────────
def test_knoten_werte_und_aendern():
    n = _netz()
    w = F.knoten_werte(n, "K4")
    assert w == {"name": "Unterverteilung 10 kV", "UN_kV": 10.0, "sternpunkt": "isoliert",
                 "Ik_max_kA": 7.9, "Ik_min_kA": 5.8, "I_E_begr_A": None}
    meldung = F.knoten_aendern(n, "K4", "Halle 2", 10, "kompensiert", 8.2, 6.0)
    assert "Bezeichnung geändert" in meldung and "Ik″ max 7.9 → 8.2" in meldung
    assert "Sternpunkt isoliert → kompensiert" in meldung
    k = n.knoten["K4"]
    assert (k.name, k.sternpunkt, k.Ik_max_kA, k.Ik_min_kA) == ("Halle 2", "kompensiert", 8.2, 6.0)
    # Verbindungen bleiben
    assert n.elemente["L2"].nach == "K4" and n.elemente["T2"].von == "K4"
    # Werte leeren (optionale Felder), keine Aenderung wird als solche gemeldet
    F.knoten_aendern(n, "K4", "Halle 2", 10, "kompensiert", None, None)
    assert n.knoten["K4"].Ik_max_kA is None and n.knoten["K4"].Ik_min_kA is None
    assert F.knoten_aendern(n, "K4", "Halle 2", 10, "kompensiert") == "Knoten K4: keine Änderung."


def test_knoten_aendern_fehler_laesst_knoten_unveraendert():
    n = _netz()
    vorher = n.to_dict()
    with pytest.raises(ModellFehler, match="größer als"):
        F.knoten_aendern(n, "K4", "x", 10, "isoliert", 5.0, 6.0)
    with pytest.raises(ModellFehler, match="Wert fehlt"):
        F.knoten_aendern(n, "K4", "x", None, "isoliert")
    with pytest.raises(ModellFehler, match="nicht zulässig"):
        F.knoten_aendern(n, "K4", "x", 10, "wasserfest")
    with pytest.raises(ModellFehler, match="existiert nicht"):
        F.knoten_aendern(n, "K99", "x", 10, "isoliert")
    assert n.to_dict() == vorher


# ── 4. Bearbeiten: Element ───────────────────────────────────────────────────
def test_trafo_richtung_tauschen_behaelt_parameter():
    n = _netz()
    vorher = n.elemente["T1"]
    w = F.element_werte(n, "T1")
    assert (w["typ"], w["von"], w["nach"]) == ("trafo", "K1", "K2")
    meldung = F.element_aendern(n, "T1", "Netztrafo", "K2", "K1")
    assert "von K1 → K2" in meldung and "nach K2 → K1" in meldung and "Parameter und Verbindungen" in meldung
    t1 = n.elemente["T1"]
    assert (t1.von, t1.nach, t1.name) == ("K2", "K1", "Netztrafo")
    assert t1.p == vorher.p and t1.zustand == vorher.zustand and t1.typ == "trafo"
    # die anderen Elemente sind unberuehrt
    for eid in ("E1", "L1", "L2", "M1", "T2"):
        assert n.elemente[eid] == _netz().elemente[eid]


def test_element_aendern_ignoriert_nicht_benoetigte_seiten():
    n = _netz()
    F.element_aendern(n, "M1", "Antrieb", "K4", "K1")        # Motor: nach wird ignoriert
    assert (n.elemente["M1"].von, n.elemente["M1"].nach) == ("K4", None)
    F.element_aendern(n, "E1", "Einspeisung", "K2", "K2")     # Einspeisung: von wird ignoriert
    assert (n.elemente["E1"].von, n.elemente["E1"].nach) == (None, "K2")


def test_einspeisung_netzbetreiber_aendern_und_leeren():
    n = _netz()
    assert F.element_werte(n, "E1")["I_nb_A"] == 160.0
    F.element_aendern(n, "E1", "Einspeisung", None, "K1", 180, 1.5)
    p = n.elemente["E1"].p
    assert p["I_gt_NB_A"] == 180.0 and p["t_gt_NB_s"] == 1.5 and p["Sk_max_MVA"] == 3000
    F.element_aendern(n, "E1", "Einspeisung", None, "K1", None, None)
    p = n.elemente["E1"].p
    assert "I_gt_NB_A" not in p and "t_gt_NB_s" not in p and p["Sk_max_MVA"] == 3000


def test_element_aendern_fehler_laesst_element_unveraendert():
    n = _netz()
    vorher = n.to_dict()
    with pytest.raises(ModellFehler, match="identisch"):
        F.element_aendern(n, "L1", "x", "K2", "K2")
    with pytest.raises(ModellFehler, match="existiert nicht"):
        F.element_aendern(n, "L1", "x", "K2", "K99")
    with pytest.raises(ModellFehler, match="existiert nicht"):
        F.element_aendern(n, "X9", "x", "K2", "K3")
    assert n.to_dict() == vorher
    assert F.element_aendern(n, "L1", n.elemente["L1"].name, "K2", "K3") == "Element L1: keine Änderung."


def test_erdfehlerstrom_begrenzung():
    """Nur bei niederohmiger Erdung uebernommen (Entscheidung 25.11.2026), sonst Hinweis."""
    n = Netz()
    m = F.knoten_anlegen(n, "K1", "A", 10, "niederohmig", None, None, 2000)
    assert n.knoten["K1"].I_E_begr_A == 2000.0 and "nicht übernommen" not in m
    m = F.knoten_anlegen(n, "K2", "B", 10, "isoliert", None, None, 2000)
    assert n.knoten["K2"].I_E_begr_A is None and "nicht übernommen" in m
    m = F.knoten_aendern(n, "K1", "A", 10, "niederohmig", None, None, 1500)
    assert "Erdfehlerstrom-Begrenzung 2000 → 1500" in m
    m = F.knoten_aendern(n, "K1", "A", 10, "isoliert", None, None, 1500)
    assert n.knoten["K1"].I_E_begr_A is None and "nicht übernommen" in m
    assert F.knoten_werte(n, "K1")["I_E_begr_A"] is None
