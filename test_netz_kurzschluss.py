"""
test_netz_kurzschluss.py - Tests fuer die Kurzschlussstromberechnung (netz_kurzschluss.py)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Ausfuehren mit:  python test_netz_kurzschluss.py   (oder: pytest test_netz_kurzschluss.py)

Prueft:
 1. Referenznetz gegen Handrechnung (Reihensumme der Impedanzen), ohne und mit K_T,
    und gegen die eingegebenen Werte des Referenznetzes.
 2. Motorbeitrag: nur im Wert "mit Motoren", Zeigersumme von Hand.
 3. Ik min: zweipolig, c_min, Sk_min, ohne Motoren, warmer Leiter.
 4. Optionale Angaben (ukr_pct, R_Belag, RX_Q, RX_M, theta_min_C) wirken.
 5. Handwert hat Vorrang: nichts wird ueberschrieben, ergaenzt wird nur, wo nichts steht.
 6. Schaltzustand: ausgeschaltete Elemente, Kupplung, Ring je Lage und geschlossen.
 7. Ring-Staffelung: Ergaenzung je Lage nur auf Wunsch.
 8. Fehlerfaelle: fehlende Daten, Unsinn in den Parametern, nie eine Ausnahme.
 9. Zufaellige Strahlenketten gegen die Reihensumme.
"""

import math
import random
from pathlib import Path

import konstanten_netz as KN
import netz_kurzschluss as KS
import netz_ring as R
from netz_modell import Netz
from netz_topologie import FEHLER, HINWEIS, WARNUNG

BEISPIEL = Path(__file__).parent / "beispielnetze" / "industrie_10kV.json"
BEISPIEL_RING = Path(__file__).parent / "beispielnetze" / "industrie_10kV_ring.json"
W3 = math.sqrt(3.0)


def _netz() -> Netz:
    return Netz.laden(BEISPIEL)


def _ring() -> Netz:
    return Netz.laden(BEISPIEL_RING)


def _nah(a, b, rel=1e-9):
    return a is not None and abs(a - b) <= rel * abs(b)


def _p(n, eid, **neu):
    p = dict(n.elemente[eid].p)
    for k, v in neu.items():
        if v is None:
            p.pop(k, None)
        else:
            p[k] = v
    n.parameter_setzen(eid, p)


class _ohne_KT:
    """K_T fuer die Dauer des Blocks abschalten (so sind die Handwerte entstanden)."""

    def __enter__(self):
        self.alt, KN.KT_anwenden = KN.KT_anwenden, False

    def __exit__(self, *a):
        KN.KT_anwenden = self.alt


# ── Handrechnung Referenznetz, alles in Ohm auf 10 kV ────────────────────────
R_BELAG = 0.11 / math.tan(math.radians(28.1))          # 0,2060 Ohm/km (NA2XS2Y 150 Al)
X_BELAG = 0.11


def _z_netz(c, Sk):                                     # Netzeinspeisung, R/X = 0,1
    z = c * 10.0 ** 2 / Sk
    x = z / math.hypot(0.1, 1.0)
    return complex(0.1 * x, x)


def _z_T1(kt=1.0):                                      # 20 MVA, uk 12 %, R = 0
    return complex(0.0, 0.12 * 10.0 ** 2 / 20.0 * kt)


def _z_ltg(L, warm=1.0):
    return complex(R_BELAG * L * warm, X_BELAG * L)


def _ik3(c, U, z):
    return c * U / W3 / abs(z)


# ── 1. Referenznetz gegen Handrechnung ───────────────────────────────────────
def test_referenznetz_handrechnung():
    n = _netz()
    with _ohne_KT():
        k = KS.berechne(n).knoten
    zq, zt = _z_netz(1.1, 3000), _z_T1()
    assert _nah(k["K1"].Ik_max_kA, 3000 / (W3 * 110))                 # Ik = Sk / (sqrt3 UN)
    assert _nah(k["K2"].Ik_max_kA, _ik3(1.1, 10, zq + zt))
    assert _nah(k["K3"].Ik_max_kA, _ik3(1.1, 10, zq + zt + _z_ltg(0.5)))
    assert _nah(k["K4"].Ik_max_kA, _ik3(1.1, 10, zq + zt + _z_ltg(1.2)))
    # K5: alles ueber (0,4/10)^2 auf 0,4 kV, dazu T2 (1,6 MVA, uk 6 %), c = 1,10
    z5 = (zq + zt + _z_ltg(1.2)) * (0.4 / 10) ** 2 + complex(0, 0.06 * 0.4 ** 2 / 1.6)
    assert _nah(k["K5"].Ik_max_kA, _ik3(KN.c_max_NS, 0.4, z5))
    # Zahlenwerte der Handrechnung (auf 2 Stellen) und Naehe zu den eingegebenen Werten
    assert [round(k[x].Ik_max_kA, 2) for x in ("K1", "K2", "K3", "K4")] == [15.75, 9.98, 9.08, 7.86]
    for kid, kno in n.knoten.items():
        assert abs(k[kid].Ik_max_kA - kno.Ik_max_kA) / kno.Ik_max_kA < 0.01, kid
        if kno.Ik_min_kA is not None:
            assert abs(k[kid].Ik_min_kA - kno.Ik_min_kA) / kno.Ik_min_kA < 0.01, kid
    print("Referenznetz OK: Reihensumme von Hand, eingegebene Werte auf unter 1 % getroffen.")


def test_korrekturfaktor_KT():
    kt = 0.95 * 1.1 / (1 + 0.6 * 0.12)                               # 0,9748
    assert _nah(KS.faktor_KT(0.12, 0.0, 10.0), kt) and round(kt, 4) == 0.9748
    k = KS.berechne(_netz()).knoten
    assert _nah(k["K2"].Ik_max_kA, _ik3(1.1, 10, _z_netz(1.1, 3000) + _z_T1(kt)))
    assert round(k["K2"].Ik_max_kA, 2) == 10.22
    assert _nah(k["K1"].Ik_max_kA, 3000 / (W3 * 110))                 # vor dem Trafo ohne Einfluss
    # mit Wirkanteil zaehlt nur die Reaktanz: x_T = sqrt(uk^2 - ukr^2)
    assert _nah(KS.faktor_KT(0.12, 0.01, 10.0), 0.95 * 1.1 / (1 + 0.6 * math.sqrt(0.12 ** 2 - 0.01 ** 2)))
    with _ohne_KT():
        assert KS.faktor_KT(0.12, 0.0, 10.0) == 1.0
    print("K_T OK: 0,9748 fuer T1, K2 damit 10,22 kA.")


# ── 2. Motorbeitrag ──────────────────────────────────────────────────────────
def test_motorbeitrag():
    n = _netz()
    with _ohne_KT():
        k = KS.berechne(n).knoten
        _p(n, "M1", Pn_kW=None, IN_direkt=None)                       # Motor ohne Leistung
        ohne = KS.berechne(n)
    # Hauptwert ist der netzseitige Strom: mit und ohne Motor gleich
    assert all(_nah(k[x].Ik_max_kA, ohne.knoten[x].Ik_max_kA) for x in k)
    assert all(_nah(ohne.knoten[x].Ik_max_mit_Motor_kA, ohne.knoten[x].Ik_max_kA) for x in k)
    assert any("kein Motorbeitrag" in m.text and m.stufe == HINWEIS for m in ohne.meldungen)
    # Hand: IN = Pn/(sqrt3 UN cos eta), Z_M = UN/(sqrt3 * 5,5 IN), R/X = 0,1. Zeigersumme an K3.
    IN = 2000e3 / (W3 * 10e3 * 0.88 * 0.96)
    zm_betrag = 10e3 / (W3 * 5.5 * IN)
    x = zm_betrag / math.hypot(0.1, 1.0)
    zm = complex(0.1 * x, x)
    z_netz = _z_netz(1.1, 3000) + _z_T1() + _z_ltg(0.5)
    summe = abs(1.1 * 10 / W3 / z_netz + 1.1 * 10 / W3 / zm)
    assert _nah(k["K3"].Ik_max_mit_Motor_kA, summe, 2e-5)             # Rechenkern rundet IN auf 3 Stellen
    assert 0.80 < k["K3"].Ik_Motor_kA < 0.84                          # rund 1,1 * 5,5 * 137 A
    assert k["K5"].Ik_max_mit_Motor_kA > k["K5"].Ik_max_kA
    print("Motor OK: Hauptwert ohne Motor, Wert mit Motor als Zeigersumme (K3 +0,83 kA).")


# ── 3. Ik min ────────────────────────────────────────────────────────────────
def test_ik_min():
    n = _netz()
    with _ohne_KT():
        k = KS.berechne(n).knoten
        zq, zt = _z_netz(1.0, 1500), _z_T1()
        warm = 1 + 0.004 * 70                                         # 90 Grad C (Voreinstellung)
        assert _nah(k["K2"].Ik_min_kA, W3 / 2 * _ik3(1.0, 10, zq + zt))
        assert _nah(k["K4"].Ik_min_kA, W3 / 2 * _ik3(1.0, 10, zq + zt + _z_ltg(1.2, warm)))
        assert [round(k[x].Ik_min_kA, 2) for x in ("K2", "K3", "K4")] == [7.5, 6.81, 5.81]
        # Leitertemperatur je Leitung: 20 Grad C ist der kalte Wert, mehr Strom
        _p(n, "L2", theta_min_C=20)
        kalt = KS.berechne(n).knoten["K4"].Ik_min_kA
        assert _nah(kalt, W3 / 2 * _ik3(1.0, 10, zq + zt + _z_ltg(1.2))) and kalt > k["K4"].Ik_min_kA
        # Niederspannung: c_min = 0,90 (Netze mit 10 % Spannungstoleranz)
        assert KN.c_min_NS == 0.90 and KN.c_max_NS == 1.10
        z5 = (zq + zt + _z_ltg(1.2)) * (0.4 / 10) ** 2 + complex(0, 0.06 * 0.4 ** 2 / 1.6)
        assert _nah(KS.berechne(n).knoten["K5"].Ik_min_kA, W3 / 2 * _ik3(0.90, 0.4, z5))
    # Faktor zweipolig und Schaltgruppenfaktor der Umrechnung heben sich auf
    assert _nah(KN.f_2pol * KN.f_Sg_2pol_DY, 1.0)
    for x in k.values():
        assert x.Ik_min_kA < x.Ik_max_kA
    print("Ik min OK: zweipolig, Sk min, c min, warmer Leiter (K4 5,81 kA).")


# ── 4. Optionale Angaben ─────────────────────────────────────────────────────
def test_optionale_angaben():
    with _ohne_KT():
        basis = KS.berechne(_netz()).knoten
        n = _netz()
        _p(n, "T1", ukr_pct=1.0)                                      # R_T = 0,05 Ohm, X = sqrt(12^2 - 1) %
        zt = complex(0.01, math.sqrt(0.12 ** 2 - 0.01 ** 2)) * 5.0
        assert _nah(KS.berechne(n).knoten["K2"].Ik_max_kA, _ik3(1.1, 10, _z_netz(1.1, 3000) + zt))
        n = _netz()
        _p(n, "L2", R_Belag=0.3)                                      # hat Vorrang vor phi_Ltg
        z = _z_netz(1.1, 3000) + _z_T1() + complex(0.3 * 1.2, 0.132)
        assert _nah(KS.berechne(n).knoten["K4"].Ik_max_kA, _ik3(1.1, 10, z))
        n = _netz()
        _p(n, "E1", RX_Q=0.0)                                         # rein induktives Netz
        assert _nah(KS.berechne(n).knoten["K2"].Ik_max_kA, _ik3(1.1, 10, complex(0, 1.1 * 100 / 3000) + _z_T1()))
        n = _netz()
        _p(n, "M1", RX_M=0.42)
        assert KS.berechne(n).knoten["K3"].Ik_max_mit_Motor_kA < basis["K3"].Ik_max_mit_Motor_kA
        # Leitung ohne Widerstandsangabe: gerechnet mit R' = 0, aber mit Warnung
        n = _netz()
        _p(n, "L2", phi_Ltg=None)
        erg = KS.berechne(n)
        assert any(m.stufe == WARNUNG and "L2" in m.text and "R' = 0" in m.text for m in erg.meldungen)
        assert erg.knoten["K4"].Ik_min_kA > basis["K4"].Ik_min_kA
    print("Optionen OK: ukr_pct, R_Belag, RX_Q, RX_M wirken, fehlendes R' wird gemeldet.")


# ── 5. Handwert hat Vorrang ──────────────────────────────────────────────────
def test_handwert_hat_vorrang():
    n = _netz()
    vorher = n.to_dict()
    erg = KS.berechne(n)
    kopie, ergaenzt, meld = KS.ergaenze_ik(n, erg)
    assert n.to_dict() == vorher                                      # Modell unveraendert
    assert [(e.knoten, e.groesse) for e in ergaenzt] == [("K5", "min")] and not meld
    for kid, k in n.knoten.items():                                   # jeder Handwert steht noch da
        assert kopie.knoten[kid].Ik_max_kA == k.Ik_max_kA
        if k.Ik_min_kA is not None:
            assert kopie.knoten[kid].Ik_min_kA == k.Ik_min_kA
    assert _nah(kopie.knoten["K5"].Ik_min_kA, erg.knoten["K5"].Ik_min_kA)
    # Vergleich: Abweichung mit Vorzeichen, wirksam ist der Handwert
    v = {(x.knoten, x.groesse): x for x in KS.vergleiche(n, erg)}
    assert v[("K2", "max")].wirksam == "eingegeben" and 0.02 < v[("K2", "max")].abweichung < 0.03
    assert v[("K5", "min")].wirksam == "berechnet" and v[("K5", "min")].abweichung is None
    assert not any(x.auffaellig for x in v.values())
    # Netz ganz ohne Handwerte: alles wird ergaenzt
    for kid in n.knoten:
        n.knoten_aendern(kid, Ik_max_kA=None, Ik_min_kA=None)
    kopie, ergaenzt, _ = KS.ergaenze_ik(n)
    assert len(ergaenzt) == 10 and all(k.Ik_max_kA is None for k in n.knoten.values())
    # Berechneter Wert passt nicht zum Handwert der anderen Groesse: nicht einsetzen, melden
    n = _netz()
    n.knoten_aendern("K5", Ik_max_kA=20.0)                            # berechnetes Ik min waere 24,6 kA
    kopie, ergaenzt, meld = KS.ergaenze_ik(n)
    assert not ergaenzt and kopie.knoten["K5"].Ik_min_kA is None
    assert len(meld) == 1 and meld[0].stufe == HINWEIS and "K5" in meld[0].text
    print("Vorrang OK: Modell unveraendert, nur K5 Ik min ergaenzt, Konflikt gemeldet.")


# ── 6. Schaltzustand und Ring ────────────────────────────────────────────────
def test_schaltzustand():
    n = _netz()
    n.element_aendern("L2", zustand="aus")
    erg = KS.berechne(n)
    assert erg.ok and erg.knoten["K4"].Ik_max_kA is None and erg.knoten["K5"].Ik_min_kA is None
    assert erg.knoten["K3"].Ik_max_kA is not None
    z = KS.berechne_schaltzustaende(_netz())
    assert len(z) == 1 and z[0].art == KS.AKTUELL
    print("Schaltzustand OK: ausgeschaltete Leitung, Knoten dahinter ohne Wert.")


def test_ring_je_lage():
    n = _ring()
    vorher = n.to_dict()
    with _ohne_KT():
        z = KS.berechne_schaltzustaende(n)
    assert n.to_dict() == vorher
    assert [(x.art, x.trennstelle) for x in z] == [
        (KS.LAGE, "K34"), (KS.LAGE, "L1"), (KS.LAGE, "L2"), (KS.GESCHLOSSEN, None)]
    k34, l1, l2, zu = (x.knoten for x in z)
    with _ohne_KT():
        strahl = KS.berechne(_netz()).knoten
    for kid in strahl:                                                # Ausgangslage = Strahlennetz
        assert _nah(k34[kid].Ik_max_kA, strahl[kid].Ik_max_kA) and _nah(k34[kid].Ik_min_kA, strahl[kid].Ik_min_kA)
    zq, zt = _z_netz(1.1, 3000), _z_T1()
    # L1 offen: K3 haengt ueber L2 und die Kupplung (Z = 0) an K2, also wie K4
    assert _nah(l1["K3"].Ik_max_kA, _ik3(1.1, 10, zq + zt + _z_ltg(1.2)))
    assert _nah(l1["K3"].Ik_max_kA, l1["K4"].Ik_max_kA)
    # L2 offen: K4 haengt ueber L1 an K2
    assert _nah(l2["K4"].Ik_max_kA, _ik3(1.1, 10, zq + zt + _z_ltg(0.5)))
    assert _nah(l2["K4"].Ik_min_kA, l2["K3"].Ik_min_kA)
    # Ring geschlossen: L1 und L2 parallel
    par = _z_ltg(0.5) * _z_ltg(1.2) / (_z_ltg(0.5) + _z_ltg(1.2))
    assert _nah(zu["K3"].Ik_max_kA, _ik3(1.1, 10, zq + zt + par))
    assert zu["K4"].Ik_max_kA > max(k34["K4"].Ik_max_kA, l1["K4"].Ik_max_kA, l2["K4"].Ik_max_kA)
    assert [round(x["K4"].Ik_max_kA, 2) for x in (k34, l1, l2, zu)] == [7.86, 7.86, 9.08, 9.34]
    assert all(_nah(x["K2"].Ik_max_kA, k34["K2"].Ik_max_kA) for x in (l1, l2, zu))
    # Der Handwert an K4 (7,9 kA) passt nicht zur Lage "L2 offen": +15 %, auffaellig
    v = {(x.knoten, x.groesse): x for x in KS.vergleiche(n, z[2])}
    assert v[("K4", "max")].auffaellig and 0.14 < v[("K4", "max")].abweichung < 0.16
    assert v[("K3", "max")].auffaellig is False
    v = {(x.knoten, x.groesse): x for x in KS.vergleiche(n, z[1])}
    assert v[("K3", "max")].auffaellig and v[("K3", "max")].abweichung < -0.13
    print("Ring OK: je Lage und geschlossen gegen Handrechnung, K4 in Lage L2 offen +15 %.")


# ── 7. Ring-Staffelung: Ergaenzung je Lage nur auf Wunsch ────────────────────
def test_ring_ergaenzung_je_lage():
    n = _ring()
    lagen, _ = R.erzeuge_lagen(n)
    assert all(l.netz.knoten["K5"].Ik_min_kA is None for l in lagen)  # Voreinstellung: wie bisher
    lagen, _ = R.erzeuge_lagen(n, ik_ergaenzen=True)
    werte = {l.trennstelle: l.netz.knoten["K5"].Ik_min_kA for l in lagen}
    assert all(w is not None for w in werte.values())
    assert werte["L2"] > werte["K34"] and _nah(werte["L1"], werte["K34"])   # K4 ueber L1 ist kuerzer
    for l in lagen:                                                   # Handwerte in jeder Lage unveraendert
        assert l.netz.knoten["K4"].Ik_max_kA == 7.9 and l.netz.knoten["K3"].Ik_min_kA == 6.8
    assert n.knoten["K5"].Ik_min_kA is None
    rv = R.ringvorschlag(n, ik_ergaenzen=True)
    assert rv.ok and rv.konvergiert
    assert R.pruefe_ringlagen(n, ik_ergaenzen=True).ok
    print("Ring-Ergänzung OK: K5 Ik min je Lage berechnet, Handwerte unverändert.")


# ── 8. Fehlerfaelle ──────────────────────────────────────────────────────────
def test_fehlerfaelle():
    assert KS.berechne(Netz()).knoten == {}
    # Sk min fehlt: Ik max ja, Ik min nein
    n = _netz()
    _p(n, "E1", Sk_min_MVA=None)
    erg = KS.berechne(n)
    assert erg.ok and erg.knoten["K2"].Ik_max_kA and erg.knoten["K2"].Ik_min_kA is None
    assert any(m.stufe == WARNUNG and "Sk_min_MVA" in m.text for m in erg.meldungen)
    # Trafo ohne uk: dahinter kein Wert, davor schon
    n = _netz()
    _p(n, "T1", uk_pct=None)
    erg = KS.berechne(n)
    assert erg.ok and erg.knoten["K1"].Ik_max_kA and all(erg.knoten[k].Ik_max_kA is None for k in ("K2", "K3", "K4", "K5"))
    assert any(m.stufe == WARNUNG and "hinter T1" in m.text for m in erg.meldungen)
    # Unvollstaendiges Element parallel zu einem berechneten Weg: gar kein Ergebnis
    n = _ring()
    n.element_aendern("K34", zustand="ein")
    _p(n, "L1", L_km=None)
    erg = KS.berechne(n)
    assert not erg.ok and all(k.Ik_max_kA is None and k.Ik_min_kA is None for k in erg.knoten.values())
    # Unsinn in den Parametern
    n = _netz()
    _p(n, "E1", Sk_max_MVA="viel", RX_Q="x")
    _p(n, "T2", Sn_MVA=-1)
    _p(n, "L1", L_km=True, theta_min_C="heiss")
    _p(n, "M1", Pn_kW="gross", I_Anlauf_Verh="x")
    erg = KS.berechne(n)
    assert erg.ok and erg.knoten["K2"].Ik_max_kA is None and erg.knoten["K2"].Ik_min_kA is not None
    assert not KS.ergaenze_ik(n)[1]
    # Keine oder ausgeschaltete Einspeisung, Generator
    n = _netz()
    n.element_aendern("E1", zustand="aus")
    erg = KS.berechne(n)
    assert all(k.Ik_max_kA is None for k in erg.knoten.values())
    assert any("Keine eingeschaltete Netzeinspeisung" in m.text for m in erg.meldungen)
    n = _netz()
    n.element_hinzufuegen("G1", "Generator", "generator", None, "K2", {})
    erg = KS.berechne(n)
    assert any(m.stufe == HINWEIS and "G1" in m.text for m in erg.meldungen) and erg.knoten["K2"].Ik_max_kA
    assert len(KS.berechne_schaltzustaende(n)) == 1                   # Topologie fehlerhaft: nur aktueller Zustand
    # Leitung parallel zu einer Kupplung ist ueberbrueckt
    n = _ring()
    n.element_aendern("K34", zustand="ein")
    assert KS.berechne(n).ok
    assert KS.polar_text(None) == "–" and KS.polar_text(complex(0.1, 0.25)) == "0,1000 + j0,2500 Ω"
    print("Fehlerfälle OK: fehlende Daten ergeben Meldungen und keine Werte, nie eine Ausnahme.")


# ── 9. Zufaellige Strahlenketten gegen die Reihensumme ───────────────────────
def test_zufall_reihensumme():
    zufall = random.Random(60909)
    for _ in range(60):
        n = Netz("Zufall")
        Sk_max = zufall.uniform(500, 5000)
        Sk_min = Sk_max * zufall.uniform(0.3, 1.0)
        Sn, uk = zufall.choice([10, 20, 31.5, 40]), zufall.choice([8, 10, 12, 16])
        n.knoten_hinzufuegen("K1", "", 110.0, "direkt")
        n.knoten_hinzufuegen("K2", "", 20.0, "isoliert")
        n.element_hinzufuegen("E1", "", "einspeisung", None, "K1", {"Sk_max_MVA": Sk_max, "Sk_min_MVA": Sk_min})
        n.element_hinzufuegen("T1", "", "trafo", "K1", "K2", {"Sn_MVA": Sn, "uk_pct": uk})
        kt = 0.95 * 1.1 / (1 + 0.6 * uk / 100)
        z_max = _rx(1.1 * 20 ** 2 / Sk_max) + complex(0, uk / 100 * 400 / Sn * kt)
        z_min = _rx(1.0 * 20 ** 2 / Sk_min) + complex(0, uk / 100 * 400 / Sn * kt)
        for i in range(zufall.randint(1, 5)):
            L, Xb, Rb = zufall.uniform(0.1, 8), zufall.uniform(0.08, 0.4), zufall.uniform(0.05, 0.6)
            n.knoten_hinzufuegen(f"K{i + 3}", "", 20.0, "isoliert")
            n.element_hinzufuegen(f"L{i}", "", "leitung", f"K{i + 2}", f"K{i + 3}",
                                  {"L_km": L, "X_Belag": Xb, "R_Belag": Rb})
            z_max += complex(Rb * L, Xb * L)
            z_min += complex(Rb * L * 1.28, Xb * L)
        ende = KS.berechne(n).knoten[f"K{i + 3}"]
        assert _nah(ende.Ik_max_kA, _ik3(1.1, 20, z_max), 1e-9)
        assert _nah(ende.Ik_min_kA, W3 / 2 * _ik3(1.0, 20, z_min), 1e-9)
        assert _nah(abs(ende.Zk_max_Ohm), abs(z_max), 1e-9)
    print("Zufall OK: 60 Strahlenketten stimmen mit der Reihensumme überein.")


def _rx(z):
    x = z / math.hypot(0.1, 1.0)
    return complex(0.1 * x, x)


if __name__ == "__main__":
    test_referenznetz_handrechnung()
    test_korrekturfaktor_KT()
    test_motorbeitrag()
    test_ik_min()
    test_optionale_angaben()
    test_handwert_hat_vorrang()
    test_schaltzustand()
    test_ring_je_lage()
    test_ring_ergaenzung_je_lage()
    test_fehlerfaelle()
    test_zufall_reihensumme()
    print("\nAlle Prüfungen bestanden.")
