"""
test_netz_parameter.py - Modultests fuer netz_parameter.py (ohne Streamlit)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Ausfuehren mit:  pytest test_netz_parameter.py

Prueft:
1. Die Feldlisten passen zum Adapter und zu den Rechenkernen (jeder Schluessel wird gelesen).
2. Lesen: aktuelle Werte, fehlende Schluessel als None.
3. Schreiben: Aenderung, Leeren, unbekannte Schluessel, Wertebereiche, Querpruefungen.
4. Fehler lassen den Parametersatz unveraendert, alle Fehler werden zusammen gemeldet.
5. Das Ergebnis geht durch Adapter und Zeitpruefung (kein Absturz, Wirkung sichtbar).
"""

from pathlib import Path

import pytest

import netz_adapter
import netz_parameter as P
import netz_selektivitaet
from netz_modell import ModellFehler, Netz

BEISPIEL = Path(__file__).parent / "beispielnetze" / "industrie_10kV.json"


def _netz() -> Netz:
    return Netz.laden(BEISPIEL)


# ── 1. Feldlisten ────────────────────────────────────────────────────────────
def test_feldlisten_decken_adapter_ab():
    for typ in ("trafo", "leitung", "motor"):
        keys = {f.key for f in P.felder(typ)}
        assert set(netz_adapter.PFLICHT[typ]) <= keys, typ
        assert set(netz_adapter.OPTIONAL_ZAHL[typ]) - keys <= {"Ik_max_OS_kA", "Ik_max_US_kA", "k_S_IGG",
                                                               "Ik_max_kA", "Ik_min_kA"}, typ
        for schluessel in (*netz_adapter.ZEIT_PARAMETER[typ].values(),
                           *netz_adapter.STROM_PARAMETER[typ].values()):
            assert schluessel in keys, (typ, schluessel)       # was der Vorschlag schreibt, ist editierbar
    assert {"Sk_max_MVA", "Sk_min_MVA", "I_gt_NB_A", "t_gt_NB_s"} <= {f.key for f in P.felder("einspeisung")}
    assert not P.hat_felder("kupplung") and not P.hat_felder("generator")


def test_schluessel_sind_eindeutig_und_haben_gueltige_optionen():
    for typ, felder in P.FELDER.items():
        keys = [f.key for f in felder]
        assert len(keys) == len(set(keys)), typ
        for f in felder:
            assert f.art in (P.ZAHL, P.WAHL)
            assert (f.art == P.WAHL) == bool(f.optionen), f.key
            assert f.vorgabe == "" or isinstance(f.vorgabe, str)


# ── 2. Lesen ─────────────────────────────────────────────────────────────────
def test_parameter_werte():
    n = _netz()
    w = P.parameter_werte(n, "T2")
    assert w["Sn_MVA"] == 1.6 and w["CT_OS_Prim"] == 100.0 and w["Schaltgruppe"] == "Dyn5"
    assert w["t_I_Ph"] is None and w["f_I_Ph_HH_OS"] is None          # nicht gesetzt: Voreinstellung
    assert P.parameter_werte(n, "L1")["uebs_betriebsart"] == "Ein: immer aktiv"
    assert P.parameter_werte(n, "E1")["I_gt_NB_A"] == 160.0
    with pytest.raises(ModellFehler, match="existiert nicht"):
        P.parameter_werte(n, "X9")


def test_typ_ohne_parameter():
    n = _netz()
    n.element_hinzufuegen("KU1", "Kupplung", "kupplung", "K3", "K4")
    with pytest.raises(ModellFehler, match="keine bearbeitbaren Parameter"):
        P.parameter_werte(n, "KU1")


# ── 3. Schreiben ─────────────────────────────────────────────────────────────
def test_aendern_setzen_und_leeren():
    n = _netz()
    vorher = n.elemente["T2"].p
    meldung = P.parameter_aendern(n, "T2", {"CT_OS_Prim": 150, "t_I_Ph": 0.8, "Schaltgruppe": "Dyn11"})
    p = n.elemente["T2"].p
    assert (p["CT_OS_Prim"], p["t_I_Ph"], p["Schaltgruppe"]) == (150.0, 0.8, "Dyn11")
    assert "CT OS primär 100 → 150" in meldung and "t I> OS leer → 0,8" in meldung
    # alles andere unveraendert, auch Schluessel ausserhalb der Feldliste
    n.parameter_setzen("T2", {**p, "Rush_unbekannt": 1.5})
    P.parameter_aendern(n, "T2", {"Sn_MVA": 2.0})
    p = n.elemente["T2"].p
    assert p["Rush_unbekannt"] == 1.5 and p["uk_pct"] == vorher["uk_pct"] and p["Sn_MVA"] == 2.0
    # leeren entfernt den Schluessel: die Voreinstellung gilt wieder
    meldung = P.parameter_aendern(n, "T2", {"t_I_Ph": None, "Schaltgruppe": None})
    assert "t_I_Ph" not in n.elemente["T2"].p and "Schaltgruppe" not in n.elemente["T2"].p
    assert "t I> OS 0,8 → leer" in meldung
    # nichts geaendert (150 == 150.0) und Parameter ausserhalb von werte bleiben
    assert P.parameter_aendern(n, "T2", {"CT_OS_Prim": 150.0}) == "T2: keine Änderung an den Parametern."


def test_anlauf_gesperrt_feld():
    n = _netz()
    felder = {f.key: f for f in P.felder("motor")}
    f = felder["anlauf_gesperrt"]
    assert f.art == P.WAHL and tuple(f.optionen) == ("nein", "ja")
    P.parameter_aendern(n, "M1", {"anlauf_gesperrt": "ja"})
    assert n.elemente["M1"].p["anlauf_gesperrt"] == "ja"
    P.parameter_aendern(n, "M1", {"anlauf_gesperrt": None})
    assert "anlauf_gesperrt" not in n.elemente["M1"].p                  # leer = Standard "nein"
    with pytest.raises(ModellFehler):
        P.parameter_aendern(n, "M1", {"anlauf_gesperrt": "vielleicht"})


def test_einspeisung_netzbetreiber_paar():
    n = _netz()
    P.parameter_aendern(n, "E1", {"I_gt_NB_A": 200, "t_gt_NB_s": 1.0, "Sk_min_MVA": 1000})
    p = n.elemente["E1"].p
    assert (p["I_gt_NB_A"], p["t_gt_NB_s"], p["Sk_min_MVA"], p["Sk_max_MVA"]) == (200.0, 1.0, 1000.0, 3000)
    with pytest.raises(ModellFehler, match="gehören zusammen"):
        P.parameter_aendern(n, "E1", {"t_gt_NB_s": None})
    P.parameter_aendern(n, "E1", {"I_gt_NB_A": None, "t_gt_NB_s": None})      # beide leer: ohne Netzbetreiber
    assert "I_gt_NB_A" not in n.elemente["E1"].p


# ── 4. Fehler ────────────────────────────────────────────────────────────────
def test_fehler_werden_gesammelt_und_nichts_geschrieben():
    n = _netz()
    vorher = n.to_dict()
    with pytest.raises(ModellFehler) as exc:
        P.parameter_aendern(n, "T2", {"Sn_MVA": 0, "uk_pct": -3, "t_I_Ph": -0.1,
                                      "Stufensteller_pm": 50, "Schaltgruppe": "XYZ", "CT_OS_Sek": "fünf"})
    zeilen = str(exc.value).splitlines()
    assert len(zeilen) == 6
    assert any("Sn: muss größer als 0" in z for z in zeilen)
    assert any("t I> OS: muss mindestens 0" in z for z in zeilen)
    assert any("Stufensteller ±: darf höchstens 40" in z for z in zeilen)
    assert any("Schaltgruppe" in z and "nicht zulässig" in z for z in zeilen)
    assert any("CT OS sekundär: Zahl erwartet" in z for z in zeilen)
    assert n.to_dict() == vorher


@pytest.mark.parametrize("eid, werte, text", [
    ("T2", {"ukr_pct": 6.0}, "ukr"),                       # ukr >= uk
    ("E1", {"Sk_min_MVA": 4000}, "Sk″ min"),               # Sk min > Sk max
    ("L1", {"phi_Ltg": 95}, "höchstens 90"),
    ("M1", {"cos_phi": 1.2}, "höchstens 1"),
    ("M1", {"t_50_2": -1}, "mindestens 0"),
    ("L1", {"uebs_betriebsart": "vielleicht"}, "nicht zulässig"),
    ("L1", {"gibt_es_nicht": 1}, "Unbekannte Parameter"),
    ("X9", {"a": 1}, "existiert nicht"),
])
def test_ungueltige_werte(eid, werte, text):
    n = _netz()
    vorher = n.to_dict()
    with pytest.raises(ModellFehler, match=text):
        P.parameter_aendern(n, eid, werte)
    assert n.to_dict() == vorher


# ── 5. Wirkung im Netz ───────────────────────────────────────────────────────
def test_aenderung_wirkt_in_adapter_und_staffelung():
    n = _netz()
    P.parameter_aendern(n, "L1", {"t_iph_h": 1.1, "iph_h": 1.5})
    erg = netz_adapter.erzeuge_schutzstufen(n)
    s = [x for x in erg.stufen if x.element == "L1" and x.stufe == "Iph>"][0]
    assert s.t_s == 1.1 and round(s.I_prim_A) == 450             # 1,5 x IN 300 A
    pr = netz_selektivitaet.pruefe_selektivitaet(n, erg)
    paar = [p for p in pr.pruefungen if p.unten == "M1" and p.oben == "L1"]
    assert len(paar) == 1 and paar[0].dt_s is not None            # die Staffelung rechnet mit dem neuen Wert
    # CT-Wandler der Leitung leeren: der Adapter meldet das fehlende Pflichtfeld, kein Absturz
    P.parameter_aendern(n, "L1", {"CT_Prim": None})
    erg = netz_adapter.erzeuge_schutzstufen(n)
    assert any("L1: Es fehlen" in m.text for m in erg.meldungen)
