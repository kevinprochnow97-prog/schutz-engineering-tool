"""
test_netz_nullsystem.py - Tests fuer das Nullsystem und Ik1 in netz_kurzschluss.py
Aufruf: pytest test_netz_nullsystem.py

Eingefrorene Werte aus werkzeuge/gegenrechnung_pandapower.py (pandapower 3.5.6, 25.11.2026,
Fehlerart "1ph"), damit die Tests ohne pandapower laufen. Stand nach der Normpruefung vom
25.11.2026: Ik1 max mit Motoren, Ik1 min mit der Endtemperatur der Leitungen.
"""
import cmath
import math

import pytest

import konstanten_netz as KN
import netz_kurzschluss as KS
from netz_modell import ModellFehler, Netz
from netz_topologie import FEHLER, HINWEIS, WARNUNG

REF = "beispielnetze/industrie_10kV.json"
SQRT3 = math.sqrt(3.0)


def _ref():
    return Netz.laden(REF)


def _noe(I_E=2000.0):
    """Referenznetz mit niederohmig geerdetem 10-kV-Bereich, Sternpunktbildner an K2."""
    n = _ref()
    n.knoten_aendern("K2", sternpunkt="niederohmig", I_E_begr_A=I_E)
    for k in ("K3", "K4"):
        n.knoten_aendern(k, sternpunkt="niederohmig")
    return n


def _texte(erg, stufe=None):
    return [m.text for m in erg.meldungen if stufe is None or m.stufe == stufe]


# ── 1. Modell: neues Knotenfeld ──────────────────────────────────────────────
def test_modell_feld_I_E():
    n = Netz()
    n.knoten_hinzufuegen("K1", "A", 10.0, "niederohmig", I_E_begr_A=1500)
    assert n.knoten["K1"].I_E_begr_A == 1500.0
    n.knoten_aendern("K1", I_E_begr_A=None)
    assert n.knoten["K1"].I_E_begr_A is None
    n.knoten_aendern("K1", I_E_begr_A=800)
    assert Netz.from_dict(n.to_dict()) == n
    with pytest.raises(ModellFehler):
        n.knoten_aendern("K1", I_E_begr_A=0)
    with pytest.raises(ModellFehler):
        n.knoten_aendern("K1", I_E_begr_A="viel")
    assert n.knoten["K1"].I_E_begr_A == 800.0        # alter Stand bleibt bei Fehlern


def test_alte_netzdatei_ohne_feld():
    """Dateien ohne I_E_begr_A (Stand vor dem 25.11.2026) laden weiter."""
    n = _ref()
    assert all(k.I_E_begr_A is None for k in n.knoten.values())


# ── 2. Referenznetz: 10 kV isoliert, 110 kV und 0,4 kV starr geerdet ─────────
def test_referenz_pandapower():
    r = KS.berechne(_ref()).knoten
    # 25.11.2026: Ik1 max mit Motoren im Mit- und Gegensystem, Ik1 min mit Endtemperatur
    soll = {"K1": (16.1084, 8.1434), "K5": (37.2915, 30.2914)}
    for k, (mx, mn) in soll.items():
        assert r[k].Ik1_max_kA == pytest.approx(mx, rel=1e-4)
        assert r[k].Ik1_min_kA == pytest.approx(mn, rel=1e-4)
    for k in ("K2", "K3", "K4"):
        assert r[k].Ik1_max_kA is None and r[k].Ik1_min_kA is None
        assert "nicht geerdet" in r[k].erdung


def test_referenz_phasenwerte_unveraendert():
    """Das Nullsystem darf Ik max / Ik min nicht veraendern (Werte vom 17.11.2026)."""
    r = KS.berechne(_noe()).knoten
    r0 = KS.berechne(_ref()).knoten
    for k in r:
        assert r[k].Ik_max_kA == r0[k].Ik_max_kA
        assert r[k].Ik_min_kA == r0[k].Ik_min_kA
        assert r[k].Ik_max_mit_Motor_kA == r0[k].Ik_max_mit_Motor_kA


# ── 3. Niederohmig geerdet ueber Sternpunktbildner ───────────────────────────
def test_noe_pandapower():
    r = KS.berechne(_noe()).knoten
    soll = {"K2": (2.1769, 1.9738), "K3": (2.0318, 1.7868), "K4": (1.8420, 1.5853)}
    for k, (mx, mn) in soll.items():
        assert r[k].Ik1_max_kA == pytest.approx(mx, rel=1e-4)
        assert r[k].Ik1_min_kA == pytest.approx(mn, rel=1e-4)
        assert "Sternpunktbildner an K2" in r[k].erdung


def test_noe_handrechnung_K2():
    """Ik1 = 3 c UN/sqrt(3) / |2 Z1 + 3 R_E| am Erdungsknoten (Bildner ohne eigene Impedanz)."""
    erg = KS.berechne(_noe())
    k = erg.knoten["K2"]
    R_E = 10e3 / (SQRT3 * 2000.0)
    ik1 = 3 * 1.1 * 10e3 / SQRT3 / abs(2 * k.Zk_max_Ohm + 3 * R_E) / 1000
    assert k.Ik1_max_kA == pytest.approx(ik1, rel=1e-9)
    assert k.Z0_max_Ohm == pytest.approx(complex(3 * R_E, 0), rel=1e-9)


def test_ik1_waechst_mit_begrenzung():
    a = KS.berechne(_noe(1000.0)).knoten["K3"].Ik1_max_kA
    b = KS.berechne(_noe(2000.0)).knoten["K3"].Ik1_max_kA
    assert a < b < 2.2


def test_erdstrom_verteilung_strahl():
    erg = KS.berechne(_noe())
    d = KS.erdstrom_verteilung(erg, "K3")
    assert d.Ik1_kA == pytest.approx(erg.knoten["K3"].Ik1_max_kA)
    assert set(d.zweige) == {"L1"}                       # L2 fuehrt keinen Erdstrom
    I, von = d.zweige["L1"]
    assert I == pytest.approx(d.Ik1_kA, rel=1e-9) and von == "K2"
    assert d.erdungen == pytest.approx({"Erdung:K2": d.Ik1_kA}, rel=1e-9)
    # Fehler im 0,4-kV-Netz: Strom nur im Sternpunkt von T2, nichts im 10-kV-Bereich
    d5 = KS.erdstrom_verteilung(erg, "K5")
    assert d5.zweige == {} and set(d5.erdungen) == {"T2"}
    # Isolierter Bereich: leere Verteilung
    assert KS.erdstrom_verteilung(KS.berechne(_ref()), "K3").Ik1_kA is None


def test_erdstrom_verteilung_min():
    erg = KS.berechne(_noe())
    d = KS.erdstrom_verteilung(erg, "K4", KS.MIN)
    assert d.Ik1_kA == pytest.approx(erg.knoten["K4"].Ik1_min_kA)
    assert d.zweige["L2"][0] == pytest.approx(d.Ik1_kA, rel=1e-9)


# ── 4. Erdung am Trafo-Sternpunkt ─────────────────────────────────────────────
def _dyn_netz(sg="Dyn5", I_E=1000.0, stp="niederohmig"):
    n = Netz()
    n.knoten_hinzufuegen("A", "20 kV", 20.0, "isoliert")
    n.knoten_hinzufuegen("B", "10 kV", 10.0, stp, I_E_begr_A=I_E if stp == "niederohmig" else None)
    n.knoten_hinzufuegen("C", "10 kV Abgang", 10.0, stp)
    n.element_hinzufuegen("E", "Netz", "einspeisung", None, "A", {"Sk_max_MVA": 500, "Sk_min_MVA": 300})
    n.element_hinzufuegen("T", "Trafo", "trafo", "A", "B",
                          {"Sn_MVA": 10, "uk_pct": 10, "Schaltgruppe": sg})
    n.element_hinzufuegen("L", "Kabel", "leitung", "B", "C",
                          {"L_km": 2.0, "X_Belag": 0.1, "R_Belag": 0.2,
                           "R0_Belag": 0.8, "X0_Belag": 0.3})
    return n


def test_erdung_am_trafo_sternpunkt():
    erg = KS.berechne(_dyn_netz())
    kB, kC = erg.knoten["B"], erg.knoten["C"]
    assert "Sternpunkt T (Dyn5)" in kB.erdung and "1000 A" in kB.erdung
    # Z0 am Knoten B = K_T * Z1T + 3 R_E (K_T aus dem Mitsystem)
    z_t = next(i for i in erg.impedanzen if i.element == "T").Z_max
    R_E = 10e3 / (SQRT3 * 1000.0)
    assert kB.Z0_max_Ohm == pytest.approx(z_t * KN.Z0_Z1_Trafo + 3 * R_E, rel=1e-9)
    # Eigene Nullsystembelaege der Leitung: Z0 an C = Z0 an B + (0,8 + j0,3) * 2 km
    assert kC.Z0_max_Ohm == pytest.approx(kB.Z0_max_Ohm + complex(1.6, 0.6), rel=1e-9)
    assert kC.Ik1_max_kA < kB.Ik1_max_kA
    d = KS.erdstrom_verteilung(erg, "C")
    assert d.erdungen["T"] == pytest.approx(d.Ik1_kA, rel=1e-9)


def test_leitung_z0_aus_k0_faktoren():
    n = _dyn_netz()
    p = dict(n.elemente["L"].p)
    del p["R0_Belag"], p["X0_Belag"]
    p.update(RE_RL=0.5, XE_XL=2.0)
    n.parameter_setzen("L", p)
    z0 = next(i for i in KS.berechne(n).impedanzen0 if i.element == "L").Z_max
    assert z0 == pytest.approx(complex(0.2 * 2.5 * 2, 0.1 * 7.0 * 2), rel=1e-9)


def test_starr_geerdeter_trafo_ohne_widerstand():
    erg = KS.berechne(_dyn_netz(stp="direkt"))
    assert "starr" in erg.knoten["B"].erdung
    z_t = next(i for i in erg.impedanzen if i.element == "T").Z_max
    assert erg.knoten["B"].Z0_max_Ohm == pytest.approx(z_t, rel=1e-9)


def test_dreieck_sperrt_nullsystem():
    """YNd mit der Dreieckseite zum geerdeten Knoten: kein Erdungspunkt, Warnung."""
    erg = KS.berechne(_dyn_netz(sg="Yd5", stp="direkt"))
    assert erg.knoten["B"].Ik1_max_kA is None
    assert any("kein Erdungspunkt" in t for t in _texte(erg, WARNUNG))


def test_yyn_ohne_dreieck_hinweis():
    erg = KS.berechne(_dyn_netz(sg="Yyn0", stp="direkt"))
    assert any("ohne Dreieckwicklung" in t for t in _texte(erg, WARNUNG))
    assert erg.knoten["B"].Ik1_max_kA is None


def test_ynyn_laengszweig():
    """YNyn mit beiden Seiten starr geerdet: Erdstrom fliesst durch den Trafo zur Einspeisung."""
    n = _dyn_netz(sg="YNyn0", stp="direkt")
    n.knoten_aendern("A", sternpunkt="direkt")
    erg = KS.berechne(n)
    assert erg.knoten["B"].Ik1_max_kA is not None
    d = KS.erdstrom_verteilung(erg, "B")
    assert d.zweige["T"][1] == "A" and "Netz:E" in d.erdungen


def test_unlesbare_schaltgruppe():
    erg = KS.berechne(_dyn_netz(sg="Quatsch"))
    assert any("nicht lesbar" in t for t in _texte(erg, WARNUNG))
    assert erg.ok                                       # nie FEHLER wegen des Nullsystems


# ── 5. Robustheit und Meldungen ───────────────────────────────────────────────
def test_niederohmig_ohne_begrenzung():
    n = _noe()
    n.knoten_aendern("K2", I_E_begr_A=None)
    erg = KS.berechne(n)
    assert erg.knoten["K3"].Ik1_max_kA is None
    assert any("Erdfehlerstrom-Begrenzung eintragen" in t for t in _texte(erg, WARNUNG))
    assert erg.ok


def test_begrenzung_an_isoliertem_knoten_ignoriert():
    n = _ref()
    n.knoten_aendern("K2", I_E_begr_A=1000)
    erg = KS.berechne(n)
    assert erg.knoten["K2"].Ik1_max_kA is None
    assert any("wird ignoriert" in t for t in _texte(erg, HINWEIS))


def test_begrenzung_ausserhalb_bereich():
    n = _noe(I_E=1e6)
    erg = KS.berechne(n)
    assert any("außerhalb" in t for t in _texte(erg, WARNUNG))
    assert erg.knoten["K2"].Ik1_max_kA is None


def test_uneinheitlicher_bereich_hinweis():
    n = _noe()
    n.knoten_aendern("K4", sternpunkt="isoliert")
    erg = KS.berechne(n)
    assert any("uneinheitliche Sternpunktbehandlung" in t for t in _texte(erg, HINWEIS))


def test_nullsystem_fehler_blockiert_phasen_nicht(monkeypatch):
    def kaputt(*a, **k):
        raise RuntimeError("Test")
    monkeypatch.setattr(KS, "_nullsystem", kaputt)
    erg = KS.berechne(_noe())
    assert erg.ok
    assert erg.knoten["K3"].Ik_max_kA is not None and erg.knoten["K3"].Ik1_max_kA is None
    assert any("Nullsystem" in t for t in _texte(erg, WARNUNG))
    assert KS.erdstrom_verteilung(erg, "K3").Ik1_kA is None


def test_wicklungen():
    assert KS.wicklungen("Dyn5") == ("D", "yn")
    assert KS.wicklungen("YNd11") == ("YN", "d")
    assert KS.wicklungen("Yzn5") == ("Y", "zn")
    assert KS.wicklungen("") is None and KS.wicklungen(None) is None and KS.wicklungen("Dy") is None


def test_ring_schaltzustaende_haben_ik1():
    """Der Ring rechnet Ik1 je Lage mit (Staffelung im Ring kommt spaeter)."""
    n = Netz.laden("beispielnetze/industrie_10kV_ring.json")
    for k in n.knoten:
        if n.knoten[k].UN_kV == 10.0:
            n.knoten_aendern(k, sternpunkt="niederohmig")
    n.knoten_aendern("K2", I_E_begr_A=2000.0)
    for erg in KS.berechne_schaltzustaende(n):
        assert erg.ok
        assert all(erg.knoten[k].Ik1_max_kA for k in n.knoten if n.knoten[k].UN_kV == 10.0)
