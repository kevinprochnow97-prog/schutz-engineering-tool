"""
test_netz_umrechnung.py - Tests fuer die Umrechnung ueber Transformatoren (netz_umrechnung.py)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Ausfuehren mit:  python test_netz_umrechnung.py   (oder: pytest test_netz_umrechnung.py)

Prueft:
 1. Schaltgruppen lesen: gueltige und ungueltige Bezeichnungen.
 2. Faktor der Schaltgruppe beim zweipoligen Fehler, gegen eine unabhaengige
    Rechnung mit Wicklungsstroemen (Dy und Yd, ein Fehler an den Klemmen y bzw. d).
 3. Stufensteller: Handrechnung fuer Ik max und Ik min, ungueltige Eingaben.
 4. Umrechnung im Referenznetz gegen Handrechnung (T1 mit Stufensteller und YNd,
    T2 mit Dyn, Fehlerort ueber Leitung und Trafo hinweg).
 5. Fehlerfaelle: falsche Richtung, unbekannter Fall, unlesbare Schaltgruppe.
 6. Parametersweep: Reihenfolge min <= nominal <= max, Rueckrechnung.
 7. Zufallseingaben: das Modul wirft nie.
"""

import math
import random
from pathlib import Path

import konstanten_netz as KN
import netz_topologie
import netz_umrechnung as U
from netz_modell import Netz

REFERENZNETZ = Path(__file__).parent / "beispielnetze" / "industrie_10kV.json"


def _ref() -> Netz:
    return Netz.laden(REFERENZNETZ)


def _umr(n, I, fern, mess, fall):
    return U.umrechnen(n, netz_topologie.analysiere(n), I, fern, mess, fall)


# ── 1. Schaltgruppen lesen ───────────────────────────────────────────────────
def test_schaltgruppe_lesen():
    import konstanten_trafo
    erwartet = {"YNd5": ("Y", "D"), "Dyn5": ("D", "Y"), "Yzn5": ("Y", "Z"), "Yyn0": ("Y", "Y"),
                "YNyn0": ("Y", "Y"), "Yd11": ("Y", "D"), "Dd0": ("D", "D")}
    for sg, w in erwartet.items():
        assert U.wicklungen(sg) == w, sg
    # Jede Schaltgruppe, die der Trafo-Tab anbietet, ist lesbar
    for sg in konstanten_trafo.SCHALTGRUPPEN:
        assert U.wicklungen(sg) is not None, sg
    for schlecht in (None, "", "XYZ", 5, "dyn5", "Yyx", "YNdd5", "Y d5", ["Dyn5"], float("nan")):
        assert U.wicklungen(schlecht) is None, schlecht
    print(f"Schaltgruppen OK: {len(konstanten_trafo.SCHALTGRUPPEN)} Gruppen des Trafo-Tabs lesbar.")


# ── 2. Schaltgruppe, zweipoliger Fehler ──────────────────────────────────────
def _loese_dreieck(I_a, I_b, I_c):
    """Strangstroeme (ab, bc, ca) einer Dreieckwicklung aus den Leiterstroemen, ohne Kreisstrom."""
    # I_a = I_ab - I_ca, I_b = I_bc - I_ab, I_c = I_ca - I_bc, I_ab + I_bc + I_ca = 0
    I_ab = (I_a - I_b) / 3.0
    I_bc = (I_b - I_c) / 3.0
    I_ca = (I_c - I_a) / 3.0
    return I_ab, I_bc, I_ca


def test_schaltgruppe_zweipolig_gegen_wicklungsrechnung():
    """
    Unabhaengige Rechnung ohne netz_umrechnung: zweipoliger Fehler zwischen b und c
    mit dem Fehlerstrom I2 in den Leitern. Den groessten Leiterstrom auf der anderen
    Seite je Wicklungsgruppe aus Amperewindungen bestimmen und mit dem Tool vergleichen.
    """
    UHV, ULV, I2 = 110.0, 10.0, 1000.0          # Leiterspannungen in kV, Fehlerstrom in A
    ue = UHV / ULV
    # Dy: Fehler auf der Sternseite (LV). Dreieck (HV) traegt k * Sternstrom, k = (ULV/sqrt3)/UHV
    k = (ULV / math.sqrt(3)) / UHV
    I_dreieck_wick = [k * x for x in (0.0, I2, -I2)]            # Wicklung je Phase a, b, c
    ab, bc, ca = I_dreieck_wick
    leiter = (ab - ca, bc - ab, ca - bc)
    groesst_dy = max(abs(x) for x in leiter)
    # Yd: Fehler auf der Dreieckseite (LV), Stern (HV) traegt Strangstrom * Windungsverhaeltnis
    wab, wbc, wca = _loese_dreieck(0.0, I2, -I2)
    w = ULV / (UHV / math.sqrt(3))                               # HV-Strang / LV-Strang
    groesst_yd = max(abs(x) * w for x in (wab, wbc, wca))
    f, _ = U.faktor_schaltgruppe("Dyn5", U.MIN)
    assert abs(groesst_dy - f * I2 / ue) < 1e-9 * I2, (groesst_dy, f * I2 / ue)
    f2, _ = U.faktor_schaltgruppe("YNd5", U.MIN)
    assert abs(groesst_yd - f2 * I2 / ue) < 1e-9 * I2, (groesst_yd, f2 * I2 / ue)
    # Gleicher Wert wie der dreipolige Fehler, wenn Ik2 = sqrt(3)/2 * Ik3
    Ik3 = I2 / (math.sqrt(3) / 2)
    assert abs(groesst_dy - Ik3 / ue) < 1e-9 * Ik3
    # Gruppen ohne D/Y-Wechsel und dreipoliger Fehler: Faktor 1
    for sg in ("Yyn0", "YNyn0", "Yzn5", "Dd0"):
        assert U.faktor_schaltgruppe(sg, U.MIN)[0] == 1.0, sg
    for sg in ("Dyn5", "YNd5", "Yd11", "Dyn11", "Yyn0"):
        assert U.faktor_schaltgruppe(sg, U.MAX)[0] == 1.0, sg
    assert abs(KN.f_Sg_2pol_DY - 2 / math.sqrt(3)) < 1e-12
    # Unlesbar: Faktor 1 mit Hinweis
    f3, t3 = U.faktor_schaltgruppe("abc", U.MIN)
    assert f3 == 1.0 and "nicht lesbar" in t3
    print("Schaltgruppe OK: 2/sqrt(3) bei D/Y-Wechsel, gegen Wicklungsrechnung bestätigt.")


# ── 3. Stufensteller ─────────────────────────────────────────────────────────
def test_stufensteller():
    f_max, _ = U.faktor_stufensteller(16, U.MAX)
    f_min, _ = U.faktor_stufensteller(16, U.MIN)
    assert abs(f_max - 1 / 0.84) < 1e-12 and abs(f_min - 1 / 1.16) < 1e-12
    assert U.faktor_stufensteller(0, U.MAX)[0] == 1.0 and U.faktor_stufensteller(None, U.MIN)[0] == 1.0
    for schlecht in (-5, 100, 150, "x", float("nan"), float("inf"), True):
        f, t = U.faktor_stufensteller(schlecht, U.MAX)
        assert f == 1.0 and "ungueltig" in t, schlecht
    print("Stufensteller OK: ±16 % ergibt 1,190 (max) und 0,862 (min).")


# ── 4. Referenznetz gegen Handrechnung ───────────────────────────────────────
def test_referenznetz_umrechnung():
    n = _ref()
    # T1: K2 (10 kV) -> K1 (110 kV). 10 kA * 10/110 / (1 - 0,16) = 1082,25 A. YNd, dreipolig: Faktor 1
    r = _umr(n, 10000.0, "K2", "K1", U.MAX)
    assert r.ok and abs(r.I_A - 10000 * (10 / 110) / 0.84) < 1e-6
    assert [s.element for s in r.schritte] == ["T1"]
    # Ik min zweipolig: 7,5 kA * 10/110 / 1,16 * 2/sqrt(3) = 678,70 A
    r = _umr(n, 7500.0, "K2", "K1", U.MIN)
    assert abs(r.I_A - 7500 * (10 / 110) / 1.16 * 2 / math.sqrt(3)) < 1e-6
    # T2: K5 (0,4 kV) -> K4 (10 kV), kein Stufensteller: 35 kA * 0,4/10 = 1400 A (dreipolig)
    r = _umr(n, 35000.0, "K5", "K4", U.MAX)
    assert abs(r.I_A - 1400.0) < 1e-9
    # Ueber Leitung L2 und Trafo T2 bis K2: die Leitung aendert nichts
    r = _umr(n, 35000.0, "K5", "K2", U.MAX)
    assert abs(r.I_A - 1400.0) < 1e-9 and [s.element for s in r.schritte] == ["T2"]
    # Dyn5 zweipolig: Ik min 3,2 kA bei 0,4 kV -> 128 A * 2/sqrt(3) = 147,8 A
    r = _umr(n, 3200.0, "K5", "K4", U.MIN)
    assert abs(r.I_A - 3200 * 0.04 * 2 / math.sqrt(3)) < 1e-9
    # Zwei Trafos in Reihe: K5 -> K1 ueber T2 und T1 (nur ein Weg, Faktoren multiplizieren)
    r = _umr(n, 35000.0, "K5", "K1", U.MAX)
    assert [s.element for s in r.schritte] == ["T2", "T1"]
    assert abs(r.I_A - 35000 * 0.04 * (10 / 110) / 0.84) < 1e-6
    # Gleicher Knoten: nichts zu tun
    r = _umr(n, 1234.0, "K2", "K2", U.MAX)
    assert r.ok and r.I_A == 1234.0 and r.schritte == []
    print("Referenznetz OK: T1 1082,25 A (max) und 678,70 A (min), T2 1400 A, Reihe T2+T1.")


# ── 5. Fehlerfaelle ──────────────────────────────────────────────────────────
def test_fehlerfaelle():
    n = _ref()
    r = _umr(n, 1000.0, "K1", "K2", U.MAX)            # Messknoten liegt unterhalb des Fehlers
    assert not r.ok and r.I_A is None and r.hinweise
    r = _umr(n, 1000.0, "K2", "K1", "quer")
    assert not r.ok and r.I_A is None
    r = _umr(n, 1000.0, "KX", "K1", U.MAX)
    assert not r.ok
    # unlesbare Schaltgruppe: Rechnung laeuft, Hinweis wird gemeldet
    p = dict(n.elemente["T2"].p)
    p["Schaltgruppe"] = "ohne Sinn"
    n.parameter_setzen("T2", p)
    r = _umr(n, 3200.0, "K5", "K4", U.MIN)
    assert r.ok and abs(r.I_A - 128.0) < 1e-9 and any("nicht lesbar" in h for h in r.hinweise)
    # Ring: die Kupplung K3-K4 geschlossen, die Umrechnung folgt dem Versorgungsbaum
    n = _ref()
    n.element_hinzufuegen("K34", "Kupplung", "kupplung", "K3", "K4", {}, "ein")
    n.setze_netzform("ring")
    topo = netz_topologie.analysiere(n)
    if topo.ok:
        r = U.umrechnen(n, topo, 35000.0, "K5", "K2", U.MAX)
        assert r.ok and abs(r.I_A - 1400.0) < 1e-9
    print("Fehlerfälle OK: falsche Richtung, unbekannter Fall, unlesbare Gruppe, Ring.")


# ── 6. Parametersweep ────────────────────────────────────────────────────────
def test_sweep():
    n = _ref()
    topo = netz_topologie.analysiere(n)
    for pm in (0, 2.5, 5, 10, 16, 25, 40):
        for sg in ("Yyn0", "Dyn5", "YNd5", "Yzn5"):
            p = dict(n.elemente["T1"].p)
            p["Stufensteller_pm"], p["Schaltgruppe"] = pm, sg
            n.parameter_setzen("T1", p)
            nenn = 10000 * (10 / 110)
            i_max = U.umrechnen(n, topo, 10000.0, "K2", "K1", U.MAX).I_A
            i_min = U.umrechnen(n, topo, 10000.0, "K2", "K1", U.MIN).I_A
            s = pm / 100
            assert abs(i_max - nenn / (1 - s)) < 1e-6
            f_sg = 2 / math.sqrt(3) if sg in ("Dyn5", "YNd5") else 1.0
            assert abs(i_min - nenn / (1 + s) * f_sg) < 1e-6
            # Ohne Schaltgruppen-Zuschlag ist ein groesserer Stufenbereich nur nach oben/unten ungünstiger
            assert i_min / f_sg <= nenn + 1e-9 <= i_max + 1e-9
    print("Sweep OK: Stufensteller 0 bis 40 % und vier Schaltgruppen gegen die Formel.")


# ── 7. Zufallseingaben ───────────────────────────────────────────────────────
def test_zufall():
    zufall = random.Random(20261111)
    n = _ref()
    topo = netz_topologie.analysiere(n)
    werte = [None, "", "x", -1, 0, 0.0, 16, 99.9, 100, 1e12, float("nan"), float("inf"), True, [], {}]
    for _ in range(300):
        p = dict(n.elemente["T1"].p)
        p["Stufensteller_pm"] = zufall.choice(werte)
        p["Schaltgruppe"] = zufall.choice(werte + ["Dyn5", "YNd5"])
        try:
            n.parameter_setzen("T1", {k: v for k, v in p.items() if not isinstance(v, (list, dict))})
        except Exception:
            continue
        fern, mess = zufall.choice(["K1", "K2", "K3", "K5", "KX"]), zufall.choice(["K1", "K2", "K4", "KY"])
        r = U.umrechnen(n, topo, zufall.choice([1.0, 1e3, 0.0, -5.0]), fern, mess,
                        zufall.choice([U.MAX, U.MIN, "?"]))
        assert r.ok or r.I_A is None
    print("Zufall OK: 300 Eingaben ohne Ausnahme.")


if __name__ == "__main__":
    test_schaltgruppe_lesen()
    test_schaltgruppe_zweipolig_gegen_wicklungsrechnung()
    test_stufensteller()
    test_referenznetz_umrechnung()
    test_fehlerfaelle()
    test_sweep()
    test_zufall()
    print("\nAlle Prüfungen bestanden.")
