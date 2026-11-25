"""
test_norm_60909_4.py - Normbeispiel DIN IEC/TR 60909-4 (VDE 0102-4):2024-12, Abschnitt 5
(Niederspannungsnetz Un = 400 V, Kurzschlussstellen F1 bis F3), nachgerechnet am 25.11.2026.
Aufruf: pytest test_norm_60909_4.py

Netzaufbau aus Bild 6 und 5.4.1 (F1 an den US-Klemmen von T1, F2 Sammelschiene, an der T1 ueber
L1 und T2 ueber L2 zusammenlaufen, F3 hinter L3 und L4). Daten aus Tabelle 3, Sollwerte aus
Tabelle 4. Das Beispiel rechnet mit c max = 1,05 (Niederspannungsnetz mit 6 % Toleranz) und den
Trafo-Bemessungsspannungen 20 kV / 410 V.
"""
import math

import pytest

import konstanten_netz as KN
import netz_kurzschluss as KS
from netz_modell import Netz

# Tabelle 4: Kurzschlussstelle -> (Zk, Z0 in mOhm, Ik'' in kA, Ik1'' in kA)
TABELLE_4 = {
    "F1": (7.003, 6.378, 34.62, 35.71),
    "F2": (7.108, 6.606, 34.12, 34.98),
    "F3": (34.928, 80.79, 6.94, 4.83),
}


def _netz() -> Netz:
    n = Netz("IEC/TR 60909-4, Abschnitt 5")
    n.knoten_hinzufuegen("Q", "Netzeinspeisung 20 kV", 20.0, "isoliert")
    for k in ("F1", "F2", "T2LV", "FX", "F3"):
        n.knoten_hinzufuegen(k, k, 0.4, "direkt")
    Sk = math.sqrt(3) * 20 * 10                                   # UnQ = 20 kV, I''kQ = 10 kA
    n.element_hinzufuegen("EQ", "Netz", "einspeisung", None, "Q",
                          {"Sk_max_MVA": Sk, "Sk_min_MVA": Sk, "RX_Q": 0.1})
    for t, nach, Sn, PkrT in (("T1", "F1", 0.63, 6.5), ("T2", "T2LV", 0.4, 4.6)):
        n.element_hinzufuegen(t, t, "trafo", "Q", nach, {
            "Sn_MVA": Sn, "uk_pct": 4.0, "ukr_pct": PkrT / (Sn * 1000) * 100,
            "Schaltgruppe": "Dyn5", "UrT_OS_kV": 20.0, "UrT_US_kV": 0.41,
            "R0_R_T": 1.0, "X0_X_T": 0.95})

    def ltg(i, a, b, L, R, X, r0, x0):
        n.element_hinzufuegen(i, i, "leitung", a, b, {
            "L_km": L, "R_Belag": R, "X_Belag": X, "R0_Belag": R * r0, "X0_Belag": X * x0,
            "t_KS_s": 0.06})
    ltg("L1", "F1", "F2", 0.010, 0.077 / 2, 0.079 / 2, 3.7, 1.81)     # zwei parallele Kabel
    ltg("L2", "T2LV", "F2", 0.004, 0.208 / 2, 0.068 / 2, 4.23, 1.21)  # zwei parallele Kabel
    ltg("L3", "F2", "FX", 0.020, 0.271, 0.087, 3.0, 4.46)
    ltg("L4", "FX", "F3", 0.050, 0.3704, 0.297, 2.0, 3.0)              # Freileitung
    return n


@pytest.fixture
def toleranz_6(monkeypatch):
    monkeypatch.setattr(KN, "NS_Toleranz_pct", 6)


def test_tabelle_4(toleranz_6):
    erg = KS.berechne(_netz())
    assert erg.ok
    for kid, (zk, z0, ik, ik1) in TABELLE_4.items():
        r = erg.knoten[kid]
        assert abs(r.Zk_max_Ohm) * 1000 == pytest.approx(zk, abs=1.5e-3), kid
        assert abs(r.Z0_max_Ohm) * 1000 == pytest.approx(z0, abs=1e-2), kid
        assert r.Ik_max_kA == pytest.approx(ik, abs=5e-3), kid
        assert r.Ik1_max_kA == pytest.approx(ik1, abs=5e-3), kid


def test_einzelwerte_5_2(toleranz_6):
    """Zwischenwerte aus 5.2.1 und 5.2.2: Z_Qt, K_T und Z_TK."""
    erg = KS.berechne(_netz())
    imp = {i.element: i for i in erg.impedanzen}
    # Z_Qt = 0,053 + j0,531 mOhm (auf 410 V umgerechnet, im Tool erscheint sie auf 20 kV bezogen)
    zq = imp["EQ"].Z_max * (0.41 / 20) ** 2 * 1000
    assert zq.real == pytest.approx(0.053, abs=1e-3) and zq.imag == pytest.approx(0.531, abs=1e-3)
    # K_T1 = 0,975 mit c max = 1,05, Z_T1K = 2,684 + j10,053 mOhm (auf 410 V, Tool auf 400 V)
    assert KS.faktor_KT(0.04, 6.5 / 630, 0.4) == pytest.approx(0.975, abs=5e-4)
    zt = imp["T1"].Z_max * 1000
    assert zt.real == pytest.approx(2.684, abs=1e-3) and zt.imag == pytest.approx(10.053, abs=1e-3)


def test_ohne_bemessungsspannung_weicht_ab(toleranz_6):
    """Ohne UrT = 410 V rechnet das Tool mit 400 V: Ik an F1 etwa 2 bis 3 % anders."""
    n = _netz()
    for t in ("T1", "T2"):
        p = dict(n.elemente[t].p)
        del p["UrT_OS_kV"], p["UrT_US_kV"]
        n.parameter_setzen(t, p)
    ik = KS.berechne(n).knoten["F1"].Ik_max_kA
    assert 0.01 < abs(ik / TABELLE_4["F1"][2] - 1) < 0.05


def test_toleranz_10_prozent_hoeher():
    """Mit der Tool-Vorgabe 10 % (c max = 1,10) liegt Ik ueber dem Normbeispiel."""
    assert KN.NS_Toleranz_pct == 10
    erg = KS.berechne(_netz())
    assert erg.knoten["F1"].Ik_max_kA > TABELLE_4["F1"][2]
