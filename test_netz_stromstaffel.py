"""
test_netz_stromstaffel.py - Tests fuer die Stromstaffelung (netz_stromstaffel.py)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Ausfuehren mit:  python test_netz_stromstaffel.py   (oder: pytest test_netz_stromstaffel.py)

Prueft:
 1. Konstanten: gleiche Werte wie im Trafo-Tab und in der Leitungsrechnung.
 2. Adapter: Faktor-Schluessel der I>>-Stufen erreichen die Rechenkerne.
 3. Referenznetz: jeder Stromvorschlag gegen Handrechnung.
 4. Stufensteller wirkt im Vorschlag (0 % gegen 16 %).
 5. Nie absenken: ein hoeherer Tab-Wert bleibt.
 6. Wirksamkeit als Parametersweep ueber Ik max am Nachbarknoten.
 7. Gegenpruefung: Anlaufstrom (rot), Motor-I>> unter dem Tab-Fenster, Empfindlichkeit mit Schaltgruppe (Dyn gegen Yyn).
 8. Gesamtvorschlag: erst Strom, dann Zeit, gegen Handrechnung und gegen die reine Zeitstaffelung.
 9. Uebernahme ins Netz: zweiter Lauf ohne Aenderung, Parameter erreichen die Rechenkerne.
10. Fehlerfaelle und Zufallsnetze: Meldung statt Absturz, das Sicherheitsnetz greift nie.
11. Ring: offen betriebener Ring.
12. Stufenstellerlage in der Zeitpruefung: Paar gegen Handrechnung, Referenznetz mit
    knapp bemessenem I>> OS (0 % gegen 16 %), Spanne der Faktoren.
"""

import random
from pathlib import Path

import konstanten_leitung
import konstanten_netz as KN
import konstanten_trafo
import netz_adapter as A
import netz_selektivitaet as S
import netz_stromstaffel as SS
from netz_adapter import UMZ
from netz_modell import Netz
from netz_topologie import FEHLER, HINWEIS, WARNUNG

REFERENZNETZ = Path(__file__).parent / "beispielnetze" / "industrie_10kV.json"


def _ref() -> Netz:
    return Netz.laden(REFERENZNETZ)


def _p_aendern(n, eid, **neu):
    p = n.elemente[eid].p
    for k, v in neu.items():
        if v is None:
            p.pop(k, None)
        else:
            p[k] = v
    n.parameter_setzen(eid, p)


def _v(erg, element, stufe):
    treffer = [v for v in erg.vorschlaege if v.element == element and v.stufe == stufe]
    assert len(treffer) == 1, (element, stufe, [x.element + x.stufe for x in erg.vorschlaege])
    return treffer[0]


def _meldungen(erg, stufe) -> str:
    return " | ".join(m.text for m in erg.meldungen if m.stufe == stufe)


# ── 1. Konstanten ────────────────────────────────────────────────────────────
def test_konstanten():
    assert KN.k_S_Strom == konstanten_trafo.k_S_IGG == 1.20
    assert KN.gamma_Reserve == konstanten_trafo.gamma_Ikmin == konstanten_leitung.gamma_Ikmin == 1.50
    assert KN.Raster_Faktor == 0.01
    print("Konstanten OK: k_S 1,2 und gamma 1,5 wie im Trafo-Tab und im Leitungs-Tab.")


# ── 2. Adapter: Faktor-Schluessel ────────────────────────────────────────────
def test_adapter_stromparameter():
    ref = _ref()
    ad = A.erzeuge_schutzstufen(ref)
    for typ, stufen in A.STROM_PARAMETER.items():
        for stufe, key in stufen.items():
            assert key in A.OPTIONAL_ZAHL[typ], (typ, key)
            eid = {"trafo": "T1", "leitung": "L1", "motor": "M1"}[typ]
            m = _ref()
            _p_aendern(m, eid, **{key: 3.0})
            ad_m = A.erzeuge_schutzstufen(m)
            IN = A.nennstrom_A(typ, stufe, ad_m.p_voll[eid])
            ist = {s.stufe: s.I_prim_A for s in ad_m.stufen_von(eid)}[stufe]
            assert abs(ist - 3.0 * IN) < 1e-3 * IN, (typ, stufe, ist, 3.0 * IN)
    # Nennstroeme gegen Handrechnung: T1 20 MVA bei 110 kV und 10 kV, Leitung 300 A, Motor 2 MW
    assert abs(A.nennstrom_A("trafo", "I>> OS", ad.p_voll["T1"]) - 20e6 / (3 ** 0.5 * 110e3)) < 1e-2
    assert abs(A.nennstrom_A("trafo", "I>> US", ad.p_voll["T1"]) - 20e6 / (3 ** 0.5 * 10e3)) < 1e-2
    assert A.nennstrom_A("leitung", "Iph>>", ad.p_voll["L1"]) == 300
    assert abs(A.anlaufstrom_A(ad.p_voll["M1"]) - 5.5 * 136.683) < 0.2
    assert A.nennstrom_A("trafo", "I>> OS", {}) is None and A.anlaufstrom_A({}) is None
    print("Adapter OK: Faktor × IN ergibt den Ansprechwert der Stufe.")


# ── 3. Referenznetz gegen Handrechnung ───────────────────────────────────────
def test_referenznetz_handrechnung():
    erg = SS.stromvorschlag(_ref())
    assert erg.ok and erg.U_bezug_kV == 10.0
    assert len(erg.vorschlaege) == 7
    # L1: Motor M1 darunter, kein Ik dahinter. Bezug = max(I>> 8,81 x IN = 1204,2 A; Anlauf 751,8 A)
    # = 1204,2 A. 1,2 * 1204,2 = 1445,0 A, / 300 A = 4,8167 -> aufgerundet 4,82 -> 1446 A
    v = _v(erg, "L1", "Iph>>")
    assert v.status == SS.ANGEHOBEN and v.faktor_neu == 4.82 and abs(v.I_neu_A - 1446.0) < 1e-9
    assert v.I_alt_A == 600.0 and v.parameter == "iph_hh" and "Anlaufstrom" in v.grund
    # L2: T2 (OS) darunter. Ik max K5 35 kA * 0,4/10 = 1400 A, * 1,2 = 1680 A, / 300 A = 5,6
    v = _v(erg, "L2", "Iph>>")
    assert v.status == SS.ANGEHOBEN and v.faktor_neu == 5.6 and abs(v.I_neu_A - 1680.0) < 1e-9
    assert "Ik max K5" in v.grund and "T2" in v.grund
    # T2 (OS): derselbe Bezug 1680 A, der Tab liefert 1680,3 A. Reicht, bleibt.
    v = _v(erg, "T2", "I>> OS")
    assert v.status == SS.BLEIBT and not v.geaendert and abs(v.I_neu_A - 1680.3) < 0.1
    # T1 (OS): K2 10 kA * 10/110 / (1 - 0,16) = 1082,25 A bei 110 kV, * 1,2 = 1298,70 A.
    # IN_OS = 104,97 A -> Faktor 12,372 -> aufgerundet 12,38 -> 1299,6 A
    v = _v(erg, "T1", "I>> OS")
    assert v.status == SS.ANGEHOBEN and v.faktor_neu == 12.38 and v.parameter == "f_I_Ph_HH_OS"
    assert abs(v.I_neu_A - 12.38 * 104.9728) < 0.01
    assert v.I_neu_A >= 1.2 * 10000 * (10 / 110) / 0.84 - 1e-6
    # T1 (US): L1 dahinter, K3 9,1 kA * 1,2 = 10,92 kA liegt ueber Ik max K2 (10 kA): nicht wirksam
    v = _v(erg, "T1", "I>> US")
    assert v.status == SS.NICHT_WIRKSAM and not v.geaendert and v.I_neu_A == v.I_alt_A
    assert "Stromstaffelung nicht wirksam" in _meldungen(erg, HINWEIS)
    # Endpunkte bleiben. M1 liegt mit 8,81 x IN (1204 A) im Motor-Tab-Fenster: keine Warnung
    for e, s in (("M1", "I>> (50-2)"), ("T2", "I>> US")):
        v = _v(erg, e, s)
        assert v.status == SS.ENDPUNKT and not v.geaendert
    assert "Motor-Tab-Fenster" not in _meldungen(erg, WARNUNG)
    assert sorted(erg.parameter_je_element()) == ["L1", "L2", "T1"]
    assert erg.parameter_je_element()["T1"] == {"f_I_Ph_HH_OS": 12.38}
    print("Referenznetz OK: L1 4,82 · L2 5,60 · T1 OS 12,38 · T2 bleibt · T1 US nicht wirksam.")


# ── 4. Stufensteller wirkt ───────────────────────────────────────────────────
def test_stufensteller_im_vorschlag():
    n0 = _ref()
    _p_aendern(n0, "T1", Stufensteller_pm=0)
    v0 = _v(SS.stromvorschlag(n0), "T1", "I>> OS")
    # ohne Stufensteller: 1,2 * 909,09 A = 1090,9 A, / 104,9728 A = 10,392. Der Tab liefert
    # 10,39 (1090,7 A), das liegt innerhalb der Stromtoleranz von 0,1 %: der Wert bleibt
    assert v0.status == SS.BLEIBT and abs(v0.faktor_neu - 10.39) < 1e-6, (v0.status, v0.faktor_neu)
    assert abs(v0.I_neu_A - 1.2 * 10000 * 10 / 110) < 0.1 * 1.2 * 10000 * 10 / 110 / 100
    n1 = _ref()
    v1 = _v(SS.stromvorschlag(n1), "T1", "I>> OS")
    assert abs(v1.I_neu_A / v0.I_neu_A - 1 / 0.84) < 0.01      # 12,38 / 10,39
    print("Stufensteller OK: ±16 % hebt I>> OS von 10,39 auf 12,38 × IN (Faktor 1/0,84).")


# ── 5. Nie absenken ──────────────────────────────────────────────────────────
def test_nie_absenken():
    n = _ref()
    _p_aendern(n, "L2", iph_hh=8.0)                    # 2400 A, mehr als die noetigen 1680 A
    erg = SS.stromvorschlag(n)
    v = _v(erg, "L2", "Iph>>")
    assert v.status == SS.BLEIBT and v.I_neu_A == v.I_alt_A == 2400.0 and not v.geaendert
    assert "L2" not in erg.parameter_je_element()
    # Alle Vorschlaege liegen nie unter dem Tab-Wert
    for e in (SS.stromvorschlag(_ref()), erg):
        assert all(x.I_neu_A >= x.I_alt_A - 1e-9 for x in e.vorschlaege)
    print("Nie absenken OK.")


# ── 6. Wirksamkeit als Parametersweep ────────────────────────────────────────
def test_wirksamkeit_sweep():
    """T1 US, Bezug L1: 1,2 * Ik max K3 gegen Ik max K2 = 10 kA und den Tab-Wert 8082,9 A."""
    for ik3 in (1.0, 3.0, 5.0, 6.7, 7.0, 7.5, 8.0, 8.3, 8.34, 8.5, 9.1):
        n = _ref()
        n.knoten_aendern("K3", Ik_max_kA=ik3, Ik_min_kA=None)
        erg = SS.stromvorschlag(n)
        v = _v(erg, "T1", "I>> US")
        soll = 1.2 * ik3 * 1000
        # L2 (Ik K4 = 7,9 kA) liefert 9480 A als zweiten Kandidaten
        soll = max(soll, 1.2 * 7900.0)
        if soll > 10000.0 * (1 + KN.EPS_STROM):
            assert v.status == SS.NICHT_WIRKSAM, (ik3, v.status)
        elif soll <= 8082.9 * (1 + KN.EPS_STROM):
            assert v.status == SS.BLEIBT, (ik3, v.status)
        else:
            assert v.status == SS.ANGEHOBEN, (ik3, v.status)
            assert soll - 1e-6 <= v.I_neu_A < soll + 0.01 * 1154.7 + 1e-6    # aufgerundet, max. ein Raster
    print("Wirksamkeit OK: 11 Werte von Ik max K3, Grenze bei 1,2 × Ik = Ik max K2.")


# ── 7. Gegenpruefung ─────────────────────────────────────────────────────────
def test_gegenpruefung_anlaufstrom():
    """Anlaufstrom M1 751,8 A, I>> M1 1204,2 A. Iph>> von L1 gegen beide Grenzen."""
    n = _ref()
    ergebnisse = {}
    for faktor in (2.0, 2.4, 2.6, 4.82):                     # 600 A, 720 A, 780 A, 1446 A
        _p_aendern(n, "L1", iph_hh=faktor)
        pr = SS.pruefe_strom(n)
        ergebnisse[faktor] = [p for p in pr.pruefungen if p.art == "Stromstaffel" and p.unten == "M1"][0]
    assert ergebnisse[2.0].status == S.ROT and "Anlaufstrom" in ergebnisse[2.0].text
    assert ergebnisse[2.4].status == S.ROT                    # 720 A < 751,8 A: Anlauf loest aus
    # 780 A liegt ueber dem Anlaufstrom, aber unter 1,2 x 1204 A: kein Anlaufproblem, nur Zeitstaffelung
    assert ergebnisse[2.6].status == S.GELB and "löst beim Motoranlauf" not in ergebnisse[2.6].text
    assert ergebnisse[4.82].status == S.OK
    erg = SS.stromvorschlag(_ref())
    soll = [p for p in erg.pruefung.pruefungen if p.art == "Stromstaffel" and p.unten == "M1"][0]
    assert soll.status == S.OK
    print("Gegenprüfung OK: unter 752 A rot, 752 bis 1445 A gelb, ab 1446 A grün.")


def test_motor_i_hh_unter_anlaufstrom():
    """M1 mit Werksvoreinstellung 4,0 x IN (547 A): Warnung, Bezug fuer L1 ist der Anlaufstrom."""
    n = _ref()
    _p_aendern(n, "M1", f_50_2=4.0)
    erg = SS.stromvorschlag(n)
    assert "unter dem Motor-Tab-Fenster" in _meldungen(erg, WARNUNG)
    v = _v(erg, "L1", "Iph>>")
    # Bezug = max(547 A; 751,8 A) = 751,8 A, 1,2 * 751,8 = 902,2 A, / 300 A = 3,0072 -> 3,01 -> 903 A
    assert v.faktor_neu == 3.01 and abs(v.I_neu_A - 903.0) < 1e-9 and "Anlaufstrom 752 A" in v.grund
    print("Motor-Warnung OK: I>> 547 A unter dem Fenster, L1 nutzt den Anlaufstrom (3,01 × IN).")


def test_gegenpruefung_empfindlichkeit_schaltgruppe():
    """K5 Ik min 3,2 kA: 128 A bei 10 kV. Dyn5 liest 2/sqrt(3) mehr, Yyn0 nicht. Schwelle T2 (OS) 138,6 A."""
    ergebnisse = {}
    for sg in ("Yyn0", "Dyn5"):
        n = _ref()
        n.knoten_aendern("K5", Ik_min_kA=3.2)
        _p_aendern(n, "T2", Schaltgruppe=sg)
        pr = SS.pruefe_strom(n)
        e = [p for p in pr.pruefungen if p.art == "Empfindlichkeit"
             and p.unten == "T2 (US)" and p.oben == "T2 (OS)"][0]
        ergebnisse[sg] = e
    assert abs(ergebnisse["Yyn0"].I_ist_bez_A - 128.0) < 1e-6
    assert abs(ergebnisse["Dyn5"].I_ist_bez_A - 128.0 * 2 / 3 ** 0.5) < 1e-6
    assert ergebnisse["Yyn0"].status == S.ROT        # 128 A < 138,6 A
    assert ergebnisse["Dyn5"].status == S.GELB       # 147,8 A >= 138,6 A, aber < 1,5 * 138,6 A
    assert abs(ergebnisse["Dyn5"].I_soll_bez_A - 1.5 * 138.564) < 0.1
    # Ohne Ik min an K5 keine Zeile, dafuer ein Hinweis
    pr = SS.pruefe_strom(_ref())
    assert not [p for p in pr.pruefungen if p.art == "Empfindlichkeit" and p.unten == "T2 (US)"]
    assert "Ik min fehlt an K5" in " ".join(m.text for m in pr.meldungen)
    # T1 mit Stufensteller und YNd, Handrechnung: 7,5 kA * 10/110 / 1,16 * 2/sqrt(3) = 678,70 A bei 110 kV
    # -> bezogen auf 10 kV: * 110/10 = 7465,7 A
    e = [p for p in pr.pruefungen if p.art == "Empfindlichkeit" and p.unten == "T1 (US)"][0]
    assert abs(e.I_ist_bez_A - 7500 / 1.16 * 2 / 3 ** 0.5) < 1e-3 and e.status == S.OK
    print("Empfindlichkeit OK: Dyn5 gegen Yyn0 kippt rot nach gelb, T1 mit Stufensteller und YNd.")


# ── 8. Gesamtvorschlag: erst Strom, dann Zeit ────────────────────────────────
def test_gesamtvorschlag():
    n = _ref()
    gesamt = SS.gesamtvorschlag(n)
    rein = S.staffelvorschlag(_ref())
    assert gesamt.ok and gesamt.zeit is not None and gesamt.zeit.ok
    zeit = {(v.element, v.stufe): v for v in gesamt.zeit.vorschlaege}
    rein_t = {(v.element, v.stufe): v for v in rein.vorschlaege}
    # Handrechnung der Zeiten mit den neuen Ansprechwerten (Delta t = 0,3 s):
    #   M1 I> 0,5 s -> L1 Iph> 0,8 s; M1 I>> 0,0 s bei 903 A -> L1 Iph>> 0,3 s
    #   T2 (US) 0,5 s -> T2 (OS) I> 0,8 s; L2 Iph> 0,8 + 0,3 = 1,1 s
    #   L2 Iph>> 1680 A gegen T2 (OS) I>> 0,1 s -> 0,4 s
    #   T1 (US) I> (1732 A): L2 Iph>> 0,4 s ist die schnellste Stufe -> 0,7 s, T1 (OS) 1,0 s
    assert zeit[("L1", "Iph>")].t_neu_s == 0.8 and zeit[("L1", "Iph>>")].t_neu_s == 0.3
    assert zeit[("L2", "Iph>")].t_neu_s == 1.1 and zeit[("L2", "Iph>>")].t_neu_s == 0.4
    assert zeit[("T1", "I> US")].t_neu_s == 0.7 and zeit[("T1", "I> OS")].t_neu_s == 1.0
    # Reine Zeitstaffelung braucht 1,1 s fuer L2 Iph>> und 1,7 s fuer T1 (OS)
    assert rein_t[("L2", "Iph>>")].t_neu_s == 1.1 and rein_t[("T1", "I> OS")].t_neu_s == 1.7
    # Gegenpruefung Zeit: T1 (OS) gegen Netzbetreiber 1,2 s: Abstand 0,2 s, gelb statt rot
    p = gesamt.zeit.pruefung.pruefung("T1 (OS)", "E1")
    assert p.status == S.GELB and abs(p.dt_s - 0.2) < 1e-9
    assert rein.pruefung.pruefung("T1 (OS)", "E1").status == S.ROT
    assert "bereits berücksichtigt" in _meldungen(gesamt, WARNUNG)
    # Gegenpruefung Strom hat keine roten Zeilen
    assert gesamt.strom.pruefung.status in (S.OK, S.GELB)
    # Beide Vorschlagsarten in einem Parametersatz
    pe = gesamt.parameter_je_element()
    assert pe["L2"] == {"iph_hh": 5.6, "t_iph_h": 1.1, "t_iph_hh": 0.4}
    assert pe["T1"]["f_I_Ph_HH_OS"] == 12.38 and pe["T1"]["t_I_Ph"] == 1.0
    assert len(gesamt.strom.geaendert) == 3 and len(gesamt.zeit.geaendert) == 8
    assert len(gesamt.geaendert) == 11
    print("Gesamtvorschlag OK: T1 (OS) 1,0 s statt 1,7 s, Abstand zum Netzbetreiber 0,2 s.")


# ── 9. Uebernahme ins Netz ───────────────────────────────────────────────────
def test_uebernahme_und_zweiter_lauf():
    n = _ref()
    gesamt = SS.gesamtvorschlag(n)
    for eid, p_neu in gesamt.parameter_je_element().items():
        p = dict(n.elemente[eid].p)
        p.update(p_neu)
        n.parameter_setzen(eid, p)
    ad = A.erzeuge_schutzstufen(n)
    stufen = {(s.element, s.stufe): s for s in ad.stufen}
    # Die Rechenkerne liefern jetzt genau die vorgeschlagenen Ansprechwerte
    for v in gesamt.strom.vorschlaege:
        assert abs(stufen[(v.element, v.stufe)].I_prim_A - v.I_neu_A) < 1e-2, (v.element, v.stufe)
    zweit = SS.gesamtvorschlag(n)
    assert not zweit.strom.geaendert and not zweit.zeit.geaendert
    assert [v.status for v in zweit.strom.vorschlaege] == [
        ("bleibt" if v.status == SS.ANGEHOBEN else v.status) for v in gesamt.strom.vorschlaege]
    pr = S.pruefe_selektivitaet(n)
    assert [p.status for p in pr.pruefungen].count(S.GELB) == 1 and S.ROT not in {p.status for p in pr.pruefungen}
    print("Übernahme OK: Rechenkerne liefern die Vorschlagswerte, zweiter Lauf ohne Änderung.")


# ── 10. Fehlerfaelle und Zufallsnetze ────────────────────────────────────────
def test_fehlerfaelle():
    m = _ref()
    m.element_aendern("E1", zustand="aus")
    erg = SS.stromvorschlag(m)
    assert not erg.ok and erg.pruefung is None
    g = SS.gesamtvorschlag(m)
    assert not g.ok and g.zeit is None
    assert not SS.stromvorschlag(_ref(), k_S=0.5).ok
    assert not SS.stromvorschlag(_ref(), k_S=float("nan")).ok
    leer = Netz()
    assert SS.gesamtvorschlag(leer).zeit is None or SS.gesamtvorschlag(leer).zeit.vorschlaege == []
    assert SS.pruefe_strom(leer).status is None
    # Ik max fehlt am Knoten hinter L1: Rueckfall auf I>> der Station, Hinweis
    n = _ref()
    n.knoten_aendern("K4", Ik_max_kA=None, Ik_min_kA=None)
    erg = SS.stromvorschlag(n)
    assert erg.ok
    v = _v(erg, "T1", "I>> US")
    assert v.status in (SS.NICHT_WIRKSAM, SS.ANGEHOBEN, SS.BLEIBT)
    print("Fehlerfälle OK: Meldung statt Absturz, fehlendes Ik max wird abgefangen.")


def test_zufallsnetze():
    zufall = random.Random(11112026)
    for _ in range(120):
        n = _ref()
        for k in ("K1", "K2", "K3", "K4", "K5"):
            ik = zufall.choice([None, 0.5, 2.0, 7.5, 12.0, 35.0])
            ik_min = None if ik is None else zufall.choice([None, ik * 0.4])
            n.knoten_aendern(k, Ik_max_kA=ik, Ik_min_kA=ik_min)
        _p_aendern(n, "T1", Stufensteller_pm=zufall.choice([0, 5, 16, 40]),
                   Schaltgruppe=zufall.choice(["YNd5", "Dyn5", "Yyn0", "unsinn", None]))
        _p_aendern(n, "T2", Schaltgruppe=zufall.choice(["Dyn5", "Yd11", "Yzn5", "?"]))
        _p_aendern(n, "L1", iph_hh=zufall.choice([None, 1.0, 2.0, 10.0]))
        _p_aendern(n, "M1", f_50_2=zufall.choice([None, 2.0, 4.0, 9.0]))
        if zufall.random() < 0.2:
            n.element_aendern(zufall.choice(["L1", "L2", "M1", "T2"]), zustand="aus")
        g = SS.gesamtvorschlag(n, k_S=zufall.choice([1.0, 1.2, 1.5]), dt_soll=zufall.choice([0.2, 0.3, 0.4]))
        texte = " ".join(m.text for m in g.meldungen)
        assert "abgebrochen" not in texte, texte                 # Sicherheitsnetz greift nie
        if g.ok and g.zeit is not None:
            assert all(v.I_neu_A >= v.I_alt_A - 1e-9 for v in g.strom.vorschlaege)
            assert g.strom.pruefung is not None
    print("Zufallsnetze OK: 120 Netze, nie abgebrochen, nie abgesenkt.")


# ── 11. Ring ─────────────────────────────────────────────────────────────────
def test_ring():
    n = _ref()
    n.element_hinzufuegen("K34", "Kupplung offen", "kupplung", "K3", "K4", {}, "aus")
    n.setze_netzform("ring")
    g = SS.gesamtvorschlag(n)
    assert g.ok and g.zeit is not None
    assert _v(g.strom, "L2", "Iph>>").faktor_neu == 5.6 and _v(g.strom, "T1", "I>> OS").faktor_neu == 12.38
    print("Ring OK: offen betriebener Ring liefert denselben Vorschlag wie das Strahlennetz.")


# ── 12. Stufenstellerlage in der Zeitpruefung ───────────────────────────────
def _stufe_x(name, I, t, element="X"):
    return A.Schutzstufe(element, name, "51", "K", 10.0, I, UMZ, t, None, True, "Test")


def test_stufenstellerlage_paar():
    """
    Unten Iph> 1000 A / 1,0 s, oben I>> 5000 A / 0,1 s, Ik max unten 4800 A.
    Nennlage: oben regt nie an (5000 > 4800), selektiv. Mit Stufensteller ±16 % sieht
    oben bis zu 1/0,84 = 1,190 mal den Strom: er regt ab 5000/1,190 = 4200 A an,
    unten loest dort noch erst nach 1,0 s aus -> Abstand -0,9 s.
    """
    unten = S.Schutzort("U", "", "K1", 10.0, (_stufe_x("Iph>", 1000.0, 1.0),))
    oben = S.Schutzort("O", "", "K2", 10.0, (_stufe_x("I>>", 5000.0, 0.1),))
    ohne = S.pruefe_paar(unten, oben, 10.0, 4800.0)
    assert ohne.status == S.OK and ohne.f_stufensteller is None
    f_lo, f_hi = 1 / 1.16, 1 / 0.84
    mit = S.pruefe_paar(unten, oben, 10.0, 4800.0, tap=(f_lo, f_hi))
    assert mit.status == S.ROT and abs(mit.f_stufensteller - f_hi) < 1e-12
    assert abs(mit.dt_s - (0.1 - 1.0)) < 1e-9 and "Stufensteller-Lage ×1,190" in mit.text
    assert abs(mit.I_bez_A - 5000 / f_hi) < 1e-6
    # Neutrale Spanne oder keine Angabe: wie ohne Stufensteller
    for neutral in ((1.0, 1.0), None):
        assert S.pruefe_paar(unten, oben, 10.0, 4800.0, tap=neutral) == ohne
    # Ergebnis ist nie besser als die Nennlage
    for lo, hi in ((0.9, 1.1), (0.7, 1.3), (0.5, 1.0), (1.0, 2.0)):
        p = S.pruefe_paar(unten, oben, 10.0, 4800.0, tap=(lo, hi))
        assert S._RANG[p.status] >= S._RANG[ohne.status]
    print("Stufenstellerlage Paar OK: Nennlage selektiv, Extremlage -0,9 s und rot.")


def test_stufenstellerlage_referenznetz():
    # Gestaffeltes Netz laut Gesamtvorschlag uebernehmen, dann I>> OS von T1 knapp bemessen:
    # 9,53 x IN_OS = 11 003 A bez. = 1,10 x Ik max K2. Nennlage: regt nie an.
    ergebnisse = {}
    for pm in (0, 16):
        n = _ref()
        _p_aendern(n, "T1", Stufensteller_pm=pm)
        for eid, p_neu in SS.gesamtvorschlag(n).parameter_je_element().items():
            p = dict(n.elemente[eid].p)
            p.update(p_neu)
            n.parameter_setzen(eid, p)
        _p_aendern(n, "T1", f_I_Ph_HH_OS=9.53, t_I_Ph_HH=0.1)
        pr = S.pruefe_selektivitaet(n)
        ergebnisse[pm] = pr.pruefung("T1 (US)", "T1 (OS)")
        vor = S.staffelvorschlag(n)
        z = [v for v in vor.vorschlaege if v.element == "T1" and v.stufe == "I>> OS"][0]
        ergebnisse[(pm, "zeit")] = z
    assert ergebnisse[0].status == S.OK and ergebnisse[0].f_stufensteller is None
    assert ergebnisse[16].status == S.ROT and abs(ergebnisse[16].f_stufensteller - 1 / 0.84) < 1e-9
    # Zeitvorschlag: ohne Stufensteller reicht die Mindestzeit, mit +-16 % muss I>> OS
    # hinter T1 (US) I>> US (0,7 s) abwarten: 0,7 + 0,3 = 1,0 s
    assert ergebnisse[(0, "zeit")].t_neu_s == 0.1
    assert ergebnisse[(16, "zeit")].t_neu_s == 1.0 and "Stufensteller" in ergebnisse[(16, "zeit")].grund
    print("Stufenstellerlage Referenznetz OK: gleicher Aufbau, mit ±16 % rot und 1,0 s statt 0,1 s.")


def test_tap_spanne():
    import netz_topologie
    import netz_umrechnung as UM
    n = _ref()
    topo = netz_topologie.analysiere(n)
    f_lo, f_hi = UM.tap_spanne(n, topo, "K2", "K1")            # ueber T1 mit ±16 %
    assert abs(f_lo - 1 / 1.16) < 1e-12 and abs(f_hi - 1 / 0.84) < 1e-12
    assert UM.tap_spanne(n, topo, "K5", "K4") == (1.0, 1.0)    # T2 ohne Stufensteller
    assert UM.tap_spanne(n, topo, "K4", "K2") == (1.0, 1.0)    # nur Leitung
    assert UM.tap_spanne(n, topo, "K1", "K2") == (1.0, 1.0)    # falsche Richtung: neutral
    f_lo, f_hi = UM.tap_spanne(n, topo, "K5", "K1")            # T2 (0 %) und T1 (±16 %)
    assert abs(f_hi - 1 / 0.84) < 1e-12
    print("Tap-Spanne OK.")


if __name__ == "__main__":
    test_konstanten()
    test_adapter_stromparameter()
    test_referenznetz_handrechnung()
    test_stufensteller_im_vorschlag()
    test_nie_absenken()
    test_wirksamkeit_sweep()
    test_gegenpruefung_anlaufstrom()
    test_motor_i_hh_unter_anlaufstrom()
    test_gegenpruefung_empfindlichkeit_schaltgruppe()
    test_gesamtvorschlag()
    test_uebernahme_und_zweiter_lauf()
    test_fehlerfaelle()
    test_zufallsnetze()
    test_ring()
    test_stufenstellerlage_paar()
    test_stufenstellerlage_referenznetz()
    test_tap_spanne()
    print("\nAlle Prüfungen bestanden.")
