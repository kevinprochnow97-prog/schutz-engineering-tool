"""
test_netz_adapter.py - Tests fuer den Adapter (netz_adapter.py)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Ausfuehren mit:  python test_netz_adapter.py   (oder: pytest test_netz_adapter.py)

Prueft:
1. Referenznetz: alle Stufen vorhanden, Werte gegen Handrechnung.
2. Knoten sind die Wahrheit: UN, Ik und Sternpunkt kommen aus den Knoten.
3. Ring: Messorte folgen dem Schaltzustand.
4. Unvollstaendige Daten und Fehlerfaelle: Meldung statt Absturz.
5. Sternpunkt-Abbildung passt zu den Optionslisten der Tabs.
6. Zufallsnetze: der Adapter wirft nie.
"""

import math
from pathlib import Path

import calc_trafo
import konstanten_leitung
import konstanten_motor
import konstanten_trafo
import netz_adapter as A
from netz_modell import Netz
from netz_topologie import FEHLER, HINWEIS, WARNUNG

REFERENZNETZ = Path(__file__).parent / "beispielnetze" / "industrie_10kV.json"


def _ref() -> Netz:
    return Netz.laden(REFERENZNETZ)


def _stufe(erg, element, stufe):
    treffer = [s for s in erg.stufen if s.element == element and s.stufe == stufe]
    assert len(treffer) == 1, f"{element} {stufe}: {len(treffer)} Treffer"
    return treffer[0]


def _hat(erg, stufe, enthaelt):
    t = " | ".join(m.text for m in erg.meldungen if m.stufe == stufe)
    assert enthaelt in t, f"Erwartet {stufe} mit {enthaelt!r}, erhalten: {t!r}"


def _p_aendern(n, eid, **neu):
    p = n.elemente[eid].p
    for k, v in neu.items():
        if v is None:
            p.pop(k, None)
        else:
            p[k] = v
    n.parameter_setzen(eid, p)


# ── 1. Referenznetz ──────────────────────────────────────────────────────────
def test_referenznetz():
    erg = A.erzeuge_schutzstufen(_ref())
    assert erg.ok and erg.meldungen == [], erg.meldungen
    assert len(erg.stufen) == 16
    anzahl = {e: len(erg.stufen_von(e)) for e in ("E1", "T1", "L1", "L2", "M1", "T2")}
    assert anzahl == {"E1": 1, "T1": 4, "L1": 2, "L2": 2, "M1": 3, "T2": 4}

    # Handrechnung T1: IN_OS = 20 MVA / (sqrt3 * 110 kV) = 104,97 A, I> = 1,5 * IN
    IN_OS = 20e6 / (math.sqrt(3) * 110e3)
    s = _stufe(erg, "T1", "I> OS")
    assert abs(s.I_prim_A - 1.5 * IN_OS) < 0.1 and (s.messort, s.UN_kV, s.t_s) == ("K1", 110, 0.5)
    # I>> OS = k_S_IGG * Ik_max_US / nT = 1,2 * 10 kA / 11
    s = _stufe(erg, "T1", "I>> OS")
    assert abs(s.I_prim_A - 1.2 * 10000 / 11) < 1.0
    assert _stufe(erg, "T1", "I> US").messort == "K2"
    # Motor: IN = 2000 kW / (sqrt3 * 10 kV * 0,88 * 0,96) = 136,7 A, Ip = 1,2 * IN
    IN_M = 2000e3 / (math.sqrt(3) * 10e3 * 0.88 * 0.96)
    s = _stufe(erg, "M1", "Ip")
    assert abs(s.I_prim_A - 1.2 * IN_M) < 0.1
    assert s.kennlinie.startswith("Invers") and s.t_s is None and s.T_mult == 0.5
    # Leitung: Iph> = 1,2 * 300 A, gemessen am Leitungsanfang K2
    s = _stufe(erg, "L1", "Iph>")
    assert (s.I_prim_A, s.messort, s.aktiv) == (360.0, "K2", True)
    # Netzbetreiber als Obergrenze
    s = _stufe(erg, "E1", "I> NB")
    assert (s.I_prim_A, s.t_s, s.messort) == (160.0, 1.2, "K1")
    print("Referenznetz OK: 16 Stufen, Werte stimmen mit der Handrechnung.")


# ── 2. Knoten sind die Wahrheit ──────────────────────────────────────────────
def test_knoten_ist_wahrheit():
    n = _ref()
    _p_aendern(n, "T1", UN_US_kV=20.0, Ik_max_US_kA=99.0)
    erg = A.erzeuge_schutzstufen(n)
    p = erg.p_voll["T1"]
    assert (p["UN_OS_kV"], p["UN_US_kV"], p["Ik_max_US_kA"]) == (110, 10, 10.0)
    assert (p["stp_OS"], p["stp_US"]) == ("Direkt geerdet", "Isoliert")
    pl = erg.p_voll["L2"]
    assert (pl["Ik_max_kA"], pl["Ik_min_kA"]) == (10.0, 5.8)      # Anfang K2, Ende K4
    assert erg.p_voll["M1"]["stp_Netz"] == "Isoliert"

    # Fehlt Ik am Knoten, bleibt der Tab-Wert. Fehlt beides, greift der Rechenkern-Fallback 1,2/uk.
    n = _ref()
    n.knoten_aendern("K2", Ik_max_kA=None, Ik_min_kA=None)
    _p_aendern(n, "T1", Ik_max_US_kA=8.0)
    assert A.erzeuge_schutzstufen(n).p_voll["T1"]["Ik_max_US_kA"] == 8.0
    _p_aendern(n, "T1", Ik_max_US_kA=None)
    erg = A.erzeuge_schutzstufen(n)
    IN_OS = 20e6 / (math.sqrt(3) * 110e3)
    assert abs(_stufe(erg, "T1", "I>> OS").I_prim_A - (1.2 / 0.12) * IN_OS) < 0.1
    print("Knoten als Wahrheit OK: UN, Ik und Sternpunkt aus den Knoten, Fallback greift.")


# ── 3. Ring ──────────────────────────────────────────────────────────────────
def test_ring_messorte():
    n = _ref()
    n.setze_netzform("ring")
    n.element_hinzufuegen("KU1", "Kupplung", "kupplung", "K3", "K4")
    n.element_aendern("L2", zustand="aus")
    erg = A.erzeuge_schutzstufen(n)
    assert erg.ok, erg.meldungen
    assert erg.stufen_von("L2") == [] and erg.stufen_von("KU1") == []
    assert _stufe(erg, "T2", "I> OS").messort == "K4"
    # Ohne Ringschluss ueber KU1 waere T2 unversorgt, jetzt hat T2 weiterhin Stufen
    assert len(erg.stufen_von("T2")) == 4
    print("Ring OK: offene Seite ohne Stufen, T2 über die Kupplung versorgt.")


# ── 4. Unvollstaendige Daten und Fehlerfaelle ────────────────────────────────
def test_unvollstaendig():
    n = _ref()
    _p_aendern(n, "T2", CT_OS_Prim=None)
    _p_aendern(n, "M1", Pn_kW=None)
    _p_aendern(n, "L1", IN_Ltg="dreihundert")
    _p_aendern(n, "T1", t_I_Ph="schnell")
    erg = A.erzeuge_schutzstufen(n)
    assert erg.ok                                 # fehlende Daten sind Warnungen, keine Fehler
    _hat(erg, WARNUNG, "T2: Es fehlen CT_OS_Prim")
    _hat(erg, WARNUNG, "M1: Es fehlen Pn_kW oder IN_direkt")
    _hat(erg, WARNUNG, "L1: Es fehlen IN_Ltg")
    assert erg.stufen_von("T2") == erg.stufen_von("M1") == erg.stufen_von("L1") == []
    assert len(erg.stufen_von("T1")) == 4         # Rest laeuft weiter
    _hat(erg, WARNUNG, "T1: Keine gültige Zahl in t_I_Ph")
    assert _stufe(erg, "T1", "I> OS").t_s == konstanten_trafo.t_I_Ph_def

    # Der gefundene Fall: Pn_kW gueltig, IN_direkt ist Text
    n = _ref()
    _p_aendern(n, "M1", IN_direkt="x")
    erg = A.erzeuge_schutzstufen(n)
    _hat(erg, WARNUNG, "M1: Keine gültige Zahl in IN_direkt")
    assert len(erg.stufen_von("M1")) == 3

    n = _ref()
    _p_aendern(n, "E1", I_gt_NB_A=None)
    erg = A.erzeuge_schutzstufen(n)
    _hat(erg, HINWEIS, "Kein Schutz des Netzbetreibers")
    assert erg.stufen_von("E1") == []

    n = _ref()
    n.element_aendern("L2", zustand="aus")
    erg = A.erzeuge_schutzstufen(n)
    assert erg.stufen_von("L2") == erg.stufen_von("T2") == []
    print("Unvollständige Daten OK: Warnungen, Rest wird weiter berechnet.")


def test_leitung_betriebsart():
    n = _ref()
    _p_aendern(n, "L1", uebs_betriebsart=None)    # Werksvoreinstellung: nur bei U-Ausfall
    erg = A.erzeuge_schutzstufen(n)
    assert _stufe(erg, "L1", "Iph>").aktiv
    _hat(erg, WARNUNG, "Not-UMZ nur bei Spannungsausfall")
    _p_aendern(n, "L1", uebs_betriebsart="Aus")
    assert not _stufe(A.erzeuge_schutzstufen(n), "L1", "Iph>").aktiv
    print("Betriebsart Leitung OK: Not-UMZ wird erkannt und gemeldet.")


def test_fehlerfaelle():
    n = _ref()
    n.setze_netzform("ring")                      # Topologiefehler: Ring ohne Masche
    erg = A.erzeuge_schutzstufen(n)
    assert not erg.ok and erg.stufen == []
    _hat(erg, FEHLER, "Topologie enthält Fehler")

    # Rechenkern wirft: Meldung statt Absturz, andere Elemente laufen weiter
    original = calc_trafo.grundgroessen
    def kaputt(p):
        raise ZeroDivisionError("Test")
    calc_trafo.grundgroessen = kaputt
    try:
        erg = A.erzeuge_schutzstufen(_ref())
    finally:
        calc_trafo.grundgroessen = original
    _hat(erg, FEHLER, "T1: Rechenkern meldet ZeroDivisionError")
    assert len(erg.stufen_von("M1")) == 3

    n = _ref()
    n.knoten_aendern("K3", sternpunkt="direkt")
    erg = A.erzeuge_schutzstufen(n)
    _hat(erg, HINWEIS, "kein starr geerdetes Netz")
    assert erg.p_voll["M1"]["stp_Netz"] == "Niederohmig geerdet"
    print("Fehlerfälle OK: Topologiefehler, Rechenkernfehler, Sternpunkt-Ersatz.")


# ── 5. Sternpunkt-Abbildung ──────────────────────────────────────────────────
def test_sternpunkt_texte():
    for abbildung, optionen in (
        (A.STP_TRAFO, konstanten_trafo.STERNPUNKT_OPTIONEN),
        (A.STP_LEITUNG, konstanten_leitung.STERNPUNKT_NETZ_OPTIONEN),
        (A.STP_MOTOR, konstanten_motor.STERNPUNKT_NETZ_OPTIONEN),
    ):
        for text in abbildung.values():
            assert text in optionen, f"{text!r} fehlt in {optionen}"
    print("Sternpunkt-Abbildung OK: alle Texte existieren in den Tabs.")


# ── 6. Zufallsnetze ──────────────────────────────────────────────────────────
def test_zufallsnetze():
    import random
    rnd = random.Random(20261109)
    werte = [None, 0, -1, 1, 6, 12, 150, 1000, "x", True]
    schluessel = ["Sn_MVA", "uk_pct", "CT_OS_Prim", "CT_OS_Sek", "CT_US_Prim", "CT_US_Sek",
                  "IN_Ltg", "CT_Prim", "CT_Sek", "Pn_kW", "IN_direkt", "I_gt_NB_A", "t_gt_NB_s"]
    mit_stufen = 0
    for _ in range(300):
        n = _ref()
        for eid in n.elemente:
            p = n.elemente[eid].p
            for k in rnd.sample(schluessel, 4):
                v = rnd.choice(werte)
                if v is None:
                    p.pop(k, None)
                else:
                    p[k] = v
            n.parameter_setzen(eid, p)
        for kid in rnd.sample(sorted(n.knoten), 2):
            n.knoten_aendern(kid, Ik_max_kA=rnd.choice([None, 1.0, 50.0]), Ik_min_kA=None)
        erg = A.erzeuge_schutzstufen(n)           # darf nicht werfen
        # Das Sicherheitsnetz (try/except) darf nie greifen muessen, sonst ist eine
        # Eingabepruefung lueckenhaft. Gefunden so: Text in IN_direkt bei gueltigem Pn_kW.
        versteckt = [m.text for m in erg.meldungen if "Rechenkern meldet" in m.text]
        assert not versteckt, versteckt
        for s in erg.stufen:
            assert isinstance(s.I_prim_A, (int, float)), s
        mit_stufen += bool(erg.stufen)
    assert mit_stufen > 50
    print(f"Zufallsnetze OK: 300 Netze mit zufällig kaputten Parametern ohne Absturz.")


if __name__ == "__main__":
    test_referenznetz()
    test_knoten_ist_wahrheit()
    test_ring_messorte()
    test_unvollstaendig()
    test_leitung_betriebsart()
    test_fehlerfaelle()
    test_sternpunkt_texte()
    test_zufallsnetze()
    print("\nAlle Prüfungen bestanden.")
