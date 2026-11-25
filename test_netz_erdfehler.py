"""
test_netz_erdfehler.py - Tests fuer die Erdfehlerstaffelung (netz_erdfehler.py) und die
Erdstufen im Adapter.
Aufruf: pytest test_netz_erdfehler.py
"""
import pytest

import konstanten_netz as KN
import netz_adapter as A
import netz_erdfehler as EF
import netz_kurzschluss as KS
import netz_parameter as P
import netz_selektivitaet as S
from netz_modell import Netz
from netz_topologie import FEHLER, HINWEIS

NOE = "beispielnetze/industrie_10kV_noe.json"
REF = "beispielnetze/industrie_10kV.json"


def _noe():
    return Netz.laden(NOE)


def _setze(n, eid, **werte):
    p = dict(n.elemente[eid].p)
    p.update(werte)
    n.parameter_setzen(eid, p)


# ── 1. Adapter: Erdstufen getrennt von den Phasenstufen ──────────────────────
def test_adapter_erdstufen_getrennt():
    n = _noe()
    ad = A.erzeuge_schutzstufen(n)
    namen = {(s.element, s.stufe) for s in ad.erdstufen}
    assert {("L1", "3I0>>>"), ("L1", "3I0>>"), ("L1", "3I0>"), ("M1", "50N-1"), ("M1", "50N-2"),
            ("M1", "51N"), ("T2", "IE>"), ("T2", "IE>>")} <= namen
    assert not any(s.ansi.endswith("N") for s in ad.stufen)        # Phasenliste ohne Erdstufen
    t2 = [s for s in ad.erdstufen if s.element == "T2"]
    assert all(s.messort == "K5" for s in t2)                       # Sternpunkt auf der US-Seite
    assert [s for s in t2 if s.stufe == "IE>"][0].I_prim_A == pytest.approx(0.4 * 1000)
    l1 = [s for s in ad.erdstufen if s.element == "L1" and s.stufe == "3I0>"][0]
    assert l1.I_prim_A == pytest.approx(0.2 * 300) and l1.richtung == "Vorwärts"


def test_adapter_isoliert_keine_erdstufen():
    ad = A.erzeuge_schutzstufen(Netz.laden(REF))
    # Im isolierten 10-kV-Bereich weder 67N noch 50N. T1/T2 ohne Sternpunktwandler: nur Hinweise
    assert ad.erdstufen == []
    assert all(m.stufe == HINWEIS for m in ad.erd_meldungen)


def test_adapter_phasen_unveraendert():
    """Die Phasenstufen des Referenznetzes sind durch die Erdstufen nicht veraendert."""
    n = Netz.laden(REF)
    vorher = A.erzeuge_schutzstufen(n).stufen
    for k in ("K2", "K3", "K4"):
        n.knoten_aendern(k, sternpunkt="niederohmig")
    n.knoten_aendern("K2", I_E_begr_A=2000.0)
    nachher = A.erzeuge_schutzstufen(n).stufen
    assert [(s.element, s.stufe, s.I_prim_A, s.t_s) for s in vorher] == \
           [(s.element, s.stufe, s.I_prim_A, s.t_s) for s in nachher]


def test_adapter_erdstufe_fehler_ist_kein_FEHLER(monkeypatch):
    def kaputt(*a, **k):
        raise RuntimeError("Test")
    monkeypatch.setattr(A, "_erdstufen_leitung", kaputt)
    ad = A.erzeuge_schutzstufen(_noe())
    assert ad.ok and ad.stufen
    assert any("Erdstufen nicht ermittelbar" in m.text for m in ad.erd_meldungen)


def test_trafo_ohne_sternpunktwandler_hinweis():
    n = _noe()
    p = dict(n.elemente["T2"].p)
    del p["CT_E_Prim"], p["CT_E_Sek"]
    n.parameter_setzen("T2", p)
    ad = A.erzeuge_schutzstufen(n)
    assert not any(s.element == "T2" for s in ad.erdstufen)
    assert any("T2" in m.text and "Sternpunktwandler" in m.text for m in ad.erd_meldungen)


def test_erd_parameter_sind_editierbar_und_wirken():
    """Was der Erdvorschlag schreibt, steht im Parameter-Editor und erreicht den Rechenkern."""
    for typ in ("trafo", "leitung", "motor"):
        keys = {f.key for f in P.felder(typ)}
        for k in (*A.ERD_ZEIT_PARAMETER[typ].values(), *A.ERD_STROM_PARAMETER[typ].values()):
            assert k in keys, (typ, k)
    n = _noe()
    _setze(n, "T2", t_I_E=1.25, I_E=0.3)
    _setze(n, "M1", t_50N2=0.15)
    _setze(n, "L1", t_3I0H=0.9)
    st = {(s.element, s.stufe): s for s in A.erzeuge_schutzstufen(n).erdstufen}
    assert st[("T2", "IE>")].t_s == 1.25 and st[("T2", "IE>")].I_prim_A == pytest.approx(300)
    assert st[("M1", "50N-2")].t_s == 0.15
    assert st[("L1", "3I0>")].t_s == 0.9


def test_rueckwaerts_stufe_zaehlt_nicht():
    n = _noe()
    _setze(n, "L1", modus_3I0HHH="Rückwärts")
    orte = {o.element: o for o in EF.pruefe_erdfehler(n).orte}
    assert "3I0>>>" not in {s.stufe for s in orte["L1"].stufen}


# ── 2. Pruefung ──────────────────────────────────────────────────────────────
def test_bereiche():
    r = EF.pruefe_erdfehler(_noe())
    b = {x.name: x for x in r.bereiche}
    assert set(b) == {"K1", "K2, K3, K4", "K5"}
    assert "Sternpunktbildner an K2" in b["K2, K3, K4"].erdung
    assert b["K2, K3, K4"].Ik1_max_kA == pytest.approx(2.1774, rel=1e-4)
    assert b["K2, K3, K4"].Ik1_min_kA == pytest.approx(1.5853, rel=1e-4)


def test_isoliertes_netz_nur_hinweis():
    r = EF.pruefe_erdfehler(Netz.laden(REF))
    b = {x.name: x for x in r.bereiche}
    assert not b["K2, K3, K4"].geerdet and "U0" in b["K2, K3, K4"].text
    assert r.pruefungen == [] and r.ok


def test_ketten_und_paare():
    r = EF.pruefe_erdfehler(_noe())
    assert sorted(r.pfade) == [["M1", "L1"], ["M2", "L2"], ["T2 (Sternpunkt K5)"]]
    assert {(p.unten, p.oben) for p in r.pruefungen} == {("M1", "L1"), ("M2", "L2")}


def test_werksvoreinstellung_nicht_selektiv():
    """M1 50N-2 und L1 3I0>>> loesen mit Werksvoreinstellung beide nach 0,10 s aus."""
    r = EF.pruefe_erdfehler(_noe())
    p = r.pruefung("M1", "L1")
    assert p.status == S.ROT and p.dt_s == pytest.approx(0.0)
    assert r.status == S.ROT


def test_grenzstrom_ist_erdstrom():
    r = EF.pruefe_erdfehler(_noe())
    ik1_k3 = KS.berechne(_noe()).knoten["K3"].Ik1_max_kA * 1000
    assert r.pruefung("M1", "L1").I_grenz_bez_A == pytest.approx(ik1_k3, rel=1e-9)
    assert r.stroeme["L1"]["K3"][0] == pytest.approx(ik1_k3, rel=1e-9)
    assert "K4" not in r.stroeme["L1"]                      # L1 sieht Fehler an K4 nicht


def test_empfindlichkeit():
    r = EF.pruefe_erdfehler(_noe())
    e = {x.ort: x for x in r.empfindlichkeit}
    assert e["L1"].status == S.OK and e["L1"].stufe == "3I0>"
    assert e["L1"].I_min_A == pytest.approx(KS.berechne(_noe()).knoten["K3"].Ik1_min_kA * 1000)
    # Ansprechwert ueber dem kleinsten Erdstrom: rot
    n = _noe()
    _setze(n, "L1", i_3I0H=7.0, i_3I0HH=8.0, i_3I0HHH=9.0)     # 2100 A > Ik1 min an K3
    e = {x.ort: x for x in EF.pruefe_erdfehler(n).empfindlichkeit}
    assert e["L1"].status == S.ROT
    # knapp: zwischen 1 und gamma
    n = _noe()
    _setze(n, "L1", i_3I0H=1800 / 300 / 1.2, i_3I0HH=8.0, i_3I0HHH=9.0)
    e = {x.ort: x for x in EF.pruefe_erdfehler(n).empfindlichkeit}
    assert e["L1"].status == S.GELB


def test_ring_nur_hinweis():
    n = Netz.laden("beispielnetze/industrie_10kV_ring.json")
    for k in n.knoten:
        if n.knoten[k].UN_kV == 10.0:
            n.knoten_aendern(k, sternpunkt="niederohmig")
    n.knoten_aendern("K2", I_E_begr_A=2000.0)
    r = EF.pruefe_erdfehler(n)
    assert r.pruefungen == [] and r.ok
    assert any("nur im Strahlennetz" in m.text for m in r.meldungen)
    assert all(b.Ik1_max_kA for b in r.bereiche if b.UN_kV == 10.0)


# ── 3. Vorschlag ─────────────────────────────────────────────────────────────
def test_vorschlag_beispielnetz():
    v = EF.erdvorschlag(_noe())
    assert v.parameter_je_element() == {
        "L1": {"t_3I0HHH": 0.4, "t_3I0HH": 0.45, "t_3I0H": 0.8},
        "L2": {"t_3I0HHH": 0.4, "t_3I0HH": 0.45, "t_3I0H": 0.5},
    }
    assert v.pruefung.status == S.OK
    assert all(p.dt_s == pytest.approx(0.3) for p in v.pruefung.pruefungen)


def test_vorschlag_endpunkte_bleiben():
    v = EF.erdvorschlag(_noe())
    for x in v.vorschlaege:
        if x.element in ("M1", "M2", "T2"):
            assert not x.geaendert


def test_vorschlag_reihenfolge_im_geraet():
    """Nach dem Vorschlag gilt die Plausibilitaet des Leitungs-Tabs T(3I0>>>) < T(3I0>>) < T(3I0>)."""
    for werte in EF.erdvorschlag(_noe()).parameter_je_element().values():
        assert werte["t_3I0HHH"] < werte["t_3I0HH"] < werte["t_3I0H"]


def test_vorschlag_uebernehmen_und_gegenpruefen():
    n = _noe()
    v = EF.erdvorschlag(n)
    assert EF.vorschlag_uebernehmen(n, v) == ["L1", "L2"]
    r = EF.pruefe_erdfehler(n)
    assert r.status == S.OK
    assert EF.erdvorschlag(n).geaendert == []                # stabil: zweiter Lauf aendert nichts
    # Phasenstufen unberuehrt
    alt = {(s.element, s.stufe): s.t_s for s in A.erzeuge_schutzstufen(_noe()).stufen}
    neu = {(s.element, s.stufe): s.t_s for s in A.erzeuge_schutzstufen(n).stufen}
    assert alt == neu


def test_vorschlag_mit_amz_unten():
    """Motor 51N als AMZ: der Vorschlag beruecksichtigt die Kennlinie (inkl. AMZ-Zuschlag)."""
    n = _noe()
    _setze(n, "M1", f_50N1=5.0, f_50N2=6.0, T_51N=0.5)       # 50N weit oben, 51N wirkt
    v = EF.erdvorschlag(n)
    assert v.pruefung.pruefung("M1", "L1").status == S.OK
    assert v.ok


def test_zwei_erdungspunkte_stromverhaeltnis():
    """
    Zweiter Sternpunktbildner an K4: bei einem Fehler am Abgang M2 fliesst ein Teil des Stroms
    direkt ueber K4, L2 fuehrt weniger als M2. Bei einem Fehler an K3 fliesst Strom
    rueckwaerts durch L2 (Hinweis).
    """
    n = _noe()
    n.knoten_aendern("K4", I_E_begr_A=2000.0)
    r = EF.pruefe_erdfehler(n)
    I_M2 = r.stroeme["M2"]["Abgang M2"][0]
    I_L2 = r.stroeme["L2"]["Abgang M2"][0]
    assert 0.3 * I_M2 < I_L2 < 0.7 * I_M2
    assert r.pruefung("M2", "L2") is not None and r.ok
    assert any("L2" in m.text and "Rückwärtsrichtung" in m.text for m in r.meldungen)
    v = EF.erdvorschlag(n)
    assert v.pruefung.pruefung("M2", "L2").status == S.OK


def test_keine_erdstufen_hinweis():
    n = _noe()
    for eid in ("L1", "L2"):
        _setze(n, eid, modus_3I0HHH="Unwirksam", modus_3I0HH="Unwirksam", modus_3I0H="Unwirksam")
    r = EF.pruefe_erdfehler(n)
    assert r.pruefung("M1", "L1") is None and r.ok


def test_wirft_nie(monkeypatch):
    def kaputt(*a, **k):
        raise RuntimeError("Test")
    monkeypatch.setattr(EF, "_struktur", kaputt)
    r = EF.pruefe_erdfehler(_noe())
    assert r.ok and any("abgebrochen" in m.text for m in r.meldungen)
    v = EF.erdvorschlag(_noe())
    assert v.ok and v.geaendert == []


def test_ungueltiger_staffelabstand():
    v = EF.erdvorschlag(_noe(), dt_soll=-1)
    assert v.vorschlaege == [] and v.meldungen
