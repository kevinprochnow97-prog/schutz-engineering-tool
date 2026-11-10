"""
test_netz_selektivitaet.py - Tests fuer die Zeitstaffelpruefung (netz_selektivitaet.py)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Ausfuehren mit:  python test_netz_selektivitaet.py   (oder: pytest test_netz_selektivitaet.py)

Prueft:
 1. Staffelabstand: Summe der Einzelanteile, Mindestwert, Soll, Gleichheit mit dem Trafo-Tab.
 2. Umrechnung auf Bezugsspannung und Wahl der Bezugsspannung.
 3. Kennlinien: UMZ-Anregung, AMZ nach IEC gegen Handrechnung.
 4. Trafo: getrennte OS/US-Zeiten, ohne Vorgabe unveraendertes Verhalten.
 5. Referenznetz mit Werksvoreinstellungen: erwartete Ampel je Paar (Handrechnung).
 6. Gestaffeltes Referenznetz: alles gruen.
 7. Ampelschwellen als Parametersweep.
 8. Ik-Grenze, fehlende Reserve, Luecke in den Ansprechwerten.
 9. Ergebnis haengt nicht von der Bezugsspannung ab.
10. Ring: Ketten folgen dem Schaltzustand.
11. Unvollstaendige Daten und Fehlerfaelle: Meldung statt Absturz.
12. Zufallsnetze: das Modul wirft nie, das Sicherheitsnetz greift nie.
"""

from pathlib import Path

import calc_trafo
import konstanten_motor
import konstanten_netz as KN
import konstanten_trafo
import netz_adapter as A
import netz_selektivitaet as S
from netz_adapter import UMZ, Schutzstufe
from netz_modell import Netz
from netz_topologie import FEHLER, HINWEIS, WARNUNG

REFERENZNETZ = Path(__file__).parent / "beispielnetze" / "industrie_10kV.json"
NI = "Invers (IEC, normal inverse)"


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


def _hat(erg, stufe, enthaelt):
    t = " | ".join(m.text for m in erg.meldungen if m.stufe == stufe)
    assert enthaelt in t, f"Erwartet {stufe} mit {enthaelt!r}, erhalten: {t!r}"


def _stufe(I, t, name="I>", UN=10.0, kennlinie=UMZ, T=None, aktiv=True, element="X"):
    return Schutzstufe(element, name, "51", "K", UN, I, kennlinie, t, T, aktiv, "Test")


def _ort(name, *stufen, UN=10.0):
    return S.Schutzort(name, "", "K_" + name, UN, tuple(stufen))


def _gestaffelt() -> Netz:
    """
    Referenznetz, von der Last zur Quelle mit 0,3 s gestaffelt (Handrechnung).
    Mit den Werksvoreinstellungen passt die Kette nicht unter die 1,2 s des
    Netzbetreibers, deshalb hier 2,0 s. Das ist ein Ergebnis, kein Testtrick:
    fuenf Schutzorte hintereinander brauchen vier Staffelschritte.
    """
    n = _ref()
    _p_aendern(n, "M1", t_50_1=0.2)
    _p_aendern(n, "L1", t_iph_hh=0.3)                            # Iph> bleibt 0,5 s
    _p_aendern(n, "T2", t_I_Ph=0.8, t_I_Ph_US=0.5)                # OS 0,8 s, US 0,5 s
    _p_aendern(n, "L2", t_iph_h=1.1, iph_hh=6.0, t_iph_hh=0.4)    # Iph>> ueber I>> von T2 OS
    _p_aendern(n, "T1", t_I_Ph=1.7, t_I_Ph_US=1.4, t_I_Ph_HH_US=0.7)
    _p_aendern(n, "E1", t_gt_NB_s=2.0)
    return n


# ── 1. Staffelabstand ────────────────────────────────────────────────────────
def test_staffelabstand():
    assert abs(KN.dt_summe() - 0.18) < 1e-9
    assert KN.dt_Staffel_min == 0.20
    assert KN.dt_Staffel_soll == 0.30
    assert KN.dt_Staffel_min <= KN.dt_Staffel_soll
    # Ein Wert im ganzen Tool: der Trafo-Tab fuehrt dieselbe Staffelzeit
    assert KN.dt_Staffel_soll == konstanten_trafo.dt_Staffel
    assert KN._aufrunden(0.20, 0.05) == 0.20 and KN._aufrunden(0.201, 0.05) == 0.25
    print("Staffelabstand OK: Summe 0,18 s, Mindestwert 0,20 s, Soll 0,30 s.")


# ── 2. Umrechnung ────────────────────────────────────────────────────────────
def test_umrechnung():
    assert abs(S.auf_bezug(160, 110, 10) - 1760) < 1e-9
    assert abs(S.auf_bezug(3464.1, 0.4, 10) - 138.564) < 1e-9
    assert abs(S.auf_bezug(S.auf_bezug(250, 10, 110), 110, 10) - 250) < 1e-9
    erg = A.erzeuge_schutzstufen(_ref())
    assert S.waehle_bezugsspannung(erg.stufen) == 10.0
    assert S.waehle_bezugsspannung([]) is None
    # Gleichstand: die hoehere Ebene
    assert S.waehle_bezugsspannung([_stufe(1, 0, UN=10.0), _stufe(1, 0, UN=110.0)]) == 110.0
    # I> von T1 ist auf OS und US derselbe Faktor, umgerechnet also derselbe Strom
    os_ = [s for s in erg.stufen if s.element == "T1" and s.stufe == "I> OS"][0]
    us = [s for s in erg.stufen if s.element == "T1" and s.stufe == "I> US"][0]
    a, b = S.anregestrom_bez(os_, 10.0), S.anregestrom_bez(us, 10.0)
    assert abs(a - b) / b < KN.EPS_STROM
    print("Umrechnung OK: 160 A bei 110 kV = 1760 A bei 10 kV, Bezug 10 kV gewählt.")


# ── 3. Kennlinien ────────────────────────────────────────────────────────────
def test_kennlinien():
    s = _stufe(360, 0.5)
    assert S.zeit_der_stufe(s, 359.0, 10.0) is None
    assert S.zeit_der_stufe(s, 360.0, 10.0) == 0.5
    assert S.zeit_der_stufe(s, 5000.0, 10.0) == 0.5
    # AMZ normal inverse: t = T * 0,14 / ((I/Ip)^0,02 - 1). Bei 2 * Ip und T = 1: 10,03 s
    a = _stufe(100, None, "Ip", kennlinie=NI, T=1.0)
    assert abs(S.zeit_der_stufe(a, 200.0, 10.0) - 10.029) < 0.001
    assert abs(S.zeit_der_stufe(a, 1000.0, 10.0) - 2.971) < 0.001
    assert S.zeit_der_stufe(a, 105.0, 10.0) is None            # unter 1,1 * Ip keine Anregung
    assert S.zeit_der_stufe(a, 110.0, 10.0) is not None
    assert konstanten_motor.Kennlinie_51_def in KN.AMZ_KENNLINIEN
    # Bewertbarkeit
    assert S.bewertbar(s) and S.bewertbar(a)
    assert not S.bewertbar(_stufe(360, 0.5, aktiv=False))
    assert not S.bewertbar(_stufe(360, None))
    assert not S.bewertbar(_stufe(0, 0.5))
    assert not S.bewertbar(_stufe(100, None, kennlinie="ANSI moderately inverse", T=1.0))
    # Schnellste angeregte Stufe gewinnt
    o = _ort("A", _stufe(360, 0.5, "I>"), _stufe(600, 0.1, "I>>"))
    assert S.ausloesezeit(o, 400, 10.0)[0] == 0.5
    assert S.ausloesezeit(o, 600, 10.0)[0] == 0.1
    assert S.ausloesezeit(o, 100, 10.0) == (None, None)
    print("Kennlinien OK: UMZ-Anregung, AMZ gegen Handrechnung (10,03 s bei 2 x Ip).")


# ── 4. Trafo: getrennte OS/US-Zeiten ─────────────────────────────────────────
def test_trafo_os_us_zeiten():
    n = _ref()
    p = A.baue_p_voll(n, "T1")
    g = calc_trafo.grundgroessen(p)
    alt = calc_trafo.schutz_5051_phase(g, p)
    # Ohne Vorgabe: beide Seiten wie bisher, bestehende Schluessel unveraendert
    assert alt["t_I"] == alt["OS"]["t_I"] == alt["US"]["t_I"] == konstanten_trafo.t_I_Ph_def
    assert alt["t_IHH"] == alt["OS"]["t_IHH"] == alt["US"]["t_IHH"] == konstanten_trafo.t_I_Ph_HH_def
    # None (leeres Feld im Tab) wirkt wie "nicht vorgegeben"
    assert calc_trafo.schutz_5051_phase(g, dict(p, t_I_Ph_US=None, t_I_Ph_HH_US=None)) == alt
    # Die OS-Zeit zieht die US-Zeit mit, solange US nicht eigens gesetzt ist
    r = calc_trafo.schutz_5051_phase(g, dict(p, t_I_Ph=0.9))
    assert r["OS"]["t_I"] == r["US"]["t_I"] == 0.9
    # Mit Vorgabe: getrennt, Stroeme unveraendert
    neu = calc_trafo.schutz_5051_phase(g, dict(p, t_I_Ph=0.8, t_I_Ph_US=0.5, t_I_Ph_HH_US=0.3))
    assert (neu["OS"]["t_I"], neu["US"]["t_I"]) == (0.8, 0.5)
    assert (neu["OS"]["t_IHH"], neu["US"]["t_IHH"]) == (konstanten_trafo.t_I_Ph_HH_def, 0.3)
    for seite in ("OS", "US"):
        for k in ("I_prim", "IHH_prim", "I_sek", "IHH_sek"):
            assert neu[seite][k] == alt[seite][k]
    # Der Adapter reicht die Seitenzeiten durch, Text wird verworfen
    _p_aendern(n, "T1", t_I_Ph=0.8, t_I_Ph_US=0.5)
    zeiten = {s.stufe: s.t_s for s in A.erzeuge_schutzstufen(n).stufen_von("T1")}
    assert zeiten["I> OS"] == 0.8 and zeiten["I> US"] == 0.5
    _p_aendern(n, "T1", t_I_Ph_US="kurz")
    erg = A.erzeuge_schutzstufen(n)
    _hat(erg, WARNUNG, "T1: Keine gültige Zahl in t_I_Ph_US")
    assert {s.stufe: s.t_s for s in erg.stufen_von("T1")}["I> US"] == 0.8
    # Die Adressen der US-Zeiten stehen im Herstellerhinweis
    assert "2116" in konstanten_trafo.HERST["t_I_Ph_US"]["adr"]
    assert "2113" in konstanten_trafo.HERST["t_I_Ph_HH_US"]["adr"]
    print("Trafo OS/US OK: ohne Vorgabe unverändert, mit Vorgabe getrennte Zeiten.")


# ── 5. Referenznetz mit Werksvoreinstellungen ────────────────────────────────
def test_referenznetz_werkseinstellung():
    erg = S.pruefe_selektivitaet(_ref())
    assert erg.ok and erg.meldungen == [], erg.meldungen
    assert erg.U_bezug_kV == 10.0
    assert erg.pfade == [["M1", "L1", "T1 (US)", "T1 (OS)", "E1"],
                         ["T2 (US)", "T2 (OS)", "L2", "T1 (US)", "T1 (OS)", "E1"]]
    assert len(erg.orte) == 8 and len(erg.pruefungen) == 7       # gemeinsame Paare nur einmal

    # Handrechnung, alle Stroeme auf 10 kV:
    erwartet = {
        # M1 50-1 (341,7 A, 0,5 s) gegen L1 Iph> (360 A, 0,5 s)
        ("M1", "L1"):            (S.ROT, 0.0, 360.0),
        # L1 Iph>> (600 A, 0,1 s) gegen T1 I>> US (8083 A, 0,1 s), Ik max K2 = 10 kA
        ("L1", "T1 (US)"):       (S.ROT, 0.0, 8082.9),
        ("L2", "T1 (US)"):       (S.ROT, 0.0, 8082.9),
        # gleiche Zeit 0,5 s auf beiden Trafoseiten
        ("T1 (US)", "T1 (OS)"):  (S.ROT, 0.0, 1732.05),
        ("T2 (US)", "T2 (OS)"):  (S.ROT, 0.0, 138.56),
        # T2 I> OS (0,5 s) gegen L2 Iph>> (600 A, 0,1 s): oben schneller als unten
        ("T2 (OS)", "L2"):       (S.ROT, -0.4, 600.0),
        # T1 I> OS (0,5 s) gegen Netzbetreiber 160 A / 1,2 s = 1760 A auf 10 kV
        ("T1 (OS)", "E1"):       (S.OK, 0.7, 1760.0),
    }
    for (u, o), (status, dt, I) in erwartet.items():
        p = erg.pruefung(u, o)
        assert p is not None, f"{u} -> {o} fehlt"
        assert p.status == status, f"{u} -> {o}: {p.status} ({p.text})"
        assert abs(p.dt_s - dt) < 1e-6, f"{u} -> {o}: dt {p.dt_s}"
        assert abs(p.I_bez_A - I) < 0.1, f"{u} -> {o}: I {p.I_bez_A}"
    assert erg.status == S.ROT
    # I>> OS von T1 (11997 A auf 10 kV) liegt ueber Ik max K2 (10 kA): wird zu Recht nicht erreicht
    assert erg.pruefung("T1 (US)", "T1 (OS)").stufe_oben == "I> OS"
    print("Referenznetz OK: 7 Paare, 6 x rot und 1 x grün wie in der Handrechnung.")


# ── 6. Gestaffeltes Referenznetz ─────────────────────────────────────────────
def test_gestaffeltes_netz():
    erg = S.pruefe_selektivitaet(_gestaffelt())
    assert erg.ok and erg.meldungen == [], erg.meldungen
    for p in erg.pruefungen:
        assert p.status == S.OK, f"{p.unten} -> {p.oben}: {p.text}"
        assert p.dt_s >= KN.dt_Staffel_soll - KN.EPS_ZEIT
    assert erg.status == S.OK and len(erg.pruefungen) == 7
    assert abs(min(p.dt_s for p in erg.pruefungen) - 0.3) < 1e-6
    # Gegenprobe: dieselbe Staffelung passt nicht unter die 1,2 s des Netzbetreibers
    n = _gestaffelt()
    _p_aendern(n, "E1", t_gt_NB_s=1.2)
    assert S.pruefe_selektivitaet(n).pruefung("T1 (OS)", "E1").status == S.ROT
    print("Gestaffeltes Netz OK: alle 7 Paare grün, kleinster Abstand 0,30 s.")


# ── 7. Ampelschwellen ────────────────────────────────────────────────────────
def test_ampel_sweep():
    unten = _ort("U", _stufe(300, 0.5))
    for i in range(0, 21):                                     # dt = 0,00 ... 1,00 s
        dt = round(i * 0.05, 2)
        p = S.pruefe_paar(unten, _ort("O", _stufe(600, 0.5 + dt)), 10.0, 5000.0)
        soll = S.ROT if dt < 0.20 else (S.GELB if dt < 0.30 else S.OK)
        assert p.status == soll, f"dt {dt}: {p.status}"
        assert abs(p.dt_s - dt) < 1e-6
    # Eigene Schwellen werden uebernommen
    p = S.pruefe_paar(unten, _ort("O", _stufe(600, 0.9)), 10.0, 5000.0, dt_soll=0.5, dt_min=0.4)
    assert p.status == S.GELB
    # AMZ unten, UMZ oben: der kleinste Abstand liegt am Ansprechwert des oberen Schutzes
    amz = _ort("U", _stufe(100, None, "Ip", kennlinie=NI, T=0.1))
    p = S.pruefe_paar(amz, _ort("O", _stufe(400, 1.0)), 10.0, 5000.0)
    t400 = 0.1 * 0.14 / (4 ** 0.02 - 1)                         # 0,498 s
    assert abs(p.dt_s - (1.0 - t400)) < 1e-6 and p.status == S.OK
    print("Ampel OK: rot unter 0,20 s, gelb bis unter 0,30 s, grün ab 0,30 s.")


# ── 8. Ik-Grenze, Reserve, Luecke ────────────────────────────────────────────
def test_ik_grenze_und_luecke():
    unten = _ort("U", _stufe(300, 0.5, "I>"), _stufe(1000, 0.1, "I>>"))
    oben = _ort("O", _stufe(600, 0.8, "I>"), _stufe(4000, 0.1, "I>>"))
    # Ik max 3 kA: I>> oben (4 kA) wird nie erreicht -> selektiv
    p = S.pruefe_paar(unten, oben, 10.0, 3000.0)
    assert p.status == S.OK and abs(p.dt_s - 0.3) < 1e-6
    # Ik max 5 kA: I>> oben trifft auf I>> unten -> 0 s
    p = S.pruefe_paar(unten, oben, 10.0, 5000.0)
    assert p.status == S.ROT and abs(p.I_bez_A - 4000) < 1e-6
    # Ohne Ik max: strenger (alle Ansprechwerte), mit Hinweis im Text
    p = S.pruefe_paar(unten, oben, 10.0, None)
    assert p.status == S.ROT and "ohne obere Stromgrenze" in p.text
    # Oberer Schutz regt gar nicht an: selektiv, aber keine Reserve
    p = S.pruefe_paar(unten, _ort("O", _stufe(6000, 0.1)), 10.0, 5000.0)
    assert p.status == S.OK and p.dt_s is None and "keine Reserve" in p.text
    # Luecke: oben empfindlicher als unten -> hoechstens gelb, Verweis auf Stromstaffelung
    p = S.pruefe_paar(_ort("U", _stufe(500, 0.2)), _ort("O", _stufe(300, 0.8)), 10.0, 5000.0)
    assert p.status == S.GELB and "Stromstaffelung" in p.text and abs(p.dt_s - 0.6) < 1e-6
    # Gar kein gemeinsamer Bereich
    p = S.pruefe_paar(_ort("U", _stufe(900, 0.2)), _ort("O", _stufe(300, 0.8)), 10.0, 600.0)
    assert p.status == S.GELB and p.dt_s is None
    # Im Netz: ohne Ik max an K2 wird I>> OS von T1 mitgeprueft, das Ergebnis nennt den Grund
    n = _gestaffelt()
    n.knoten_aendern("K2", Ik_max_kA=None)
    _p_aendern(n, "T1", Ik_max_US_kA=None)
    p = S.pruefe_selektivitaet(n).pruefung("T1 (US)", "T1 (OS)")
    assert p.I_grenz_bez_A is None and "ohne obere Stromgrenze" in p.text
    print("Ik-Grenze OK: Stufen über Ik max zählen nicht, Lücken werden gemeldet.")


# ── 9. Unabhaengigkeit von der Bezugsspannung ────────────────────────────────
def test_bezugsspannung_invariant():
    for netz in (_ref(), _gestaffelt()):
        basis = S.pruefe_selektivitaet(netz, U_bezug_kV=10.0)
        for U in (0.4, 20.0, 110.0):
            erg = S.pruefe_selektivitaet(netz, U_bezug_kV=U)
            assert erg.U_bezug_kV == U
            for a, b in zip(basis.pruefungen, erg.pruefungen):
                assert (a.unten, a.oben, a.status) == (b.unten, b.oben, b.status)
                assert abs(a.dt_s - b.dt_s) < 1e-6
                assert abs(a.I_bez_A * 10.0 - b.I_bez_A * U) < 1e-3 * a.I_bez_A * 10.0
    erg = S.pruefe_selektivitaet(_ref(), U_bezug_kV=-5)
    _hat(erg, WARNUNG, "Bezugsspannung")
    assert erg.U_bezug_kV == 10.0
    print("Bezugsspannung OK: Ampel und Abstände sind für 0,4 / 10 / 20 / 110 kV gleich.")


# ── 10. Ring ─────────────────────────────────────────────────────────────────
def test_ring():
    n = _gestaffelt()
    n.setze_netzform("ring")
    n.element_hinzufuegen("KU1", "Kupplung", "kupplung", "K3", "K4")
    n.element_aendern("L2", zustand="aus")                      # Trennstelle bei L2
    erg = S.pruefe_selektivitaet(n)
    assert erg.ok, erg.meldungen
    # T2 haengt jetzt ueber die Kupplung hinter L1, L2 kommt nicht mehr vor
    assert ["T2 (US)", "T2 (OS)", "L1", "T1 (US)", "T1 (OS)", "E1"] in erg.pfade
    assert not any("L2" in pfad for pfad in erg.pfade)
    assert erg.pruefung("T2 (OS)", "L1") is not None and erg.pruefung("T2 (OS)", "L2") is None
    # L1 war nur gegen den Motor gestaffelt und ist fuer T2 zu schnell: das muss auffallen
    assert erg.pruefung("T2 (OS)", "L1").status == S.ROT
    # Trennstelle auf die andere Seite: L1 offen, alles haengt hinter L2
    n.element_aendern("L2", zustand="ein")
    n.element_aendern("L1", zustand="aus")
    erg = S.pruefe_selektivitaet(n)
    assert erg.ok and ["M1", "L2", "T1 (US)", "T1 (OS)", "E1"] in erg.pfade
    print("Ring OK: Ketten folgen dem Schaltzustand, die zweite Speiserichtung wird geprüft.")


# ── 11. Unvollstaendige Daten und Fehlerfaelle ───────────────────────────────
def test_unvollstaendig_und_fehler():
    # Element im Pfad ohne Stufen: Staffelung laeuft darueber hinweg, mit Warnung
    n = _ref()
    _p_aendern(n, "L1", IN_Ltg=None)
    erg = S.pruefe_selektivitaet(n)
    assert erg.ok
    _hat(erg, WARNUNG, "L1 liegt in einem Versorgungspfad")
    assert erg.pruefung("M1", "T1 (US)") is not None and erg.pruefung("M1", "L1") is None

    # Kein Netzbetreiberschutz: Kette endet am Trafo
    n = _ref()
    _p_aendern(n, "E1", I_gt_NB_A=None)
    erg = S.pruefe_selektivitaet(n)
    _hat(erg, HINWEIS, "Ohne Schutz des Netzbetreibers")
    assert erg.pfade[0][-1] == "T1 (OS)"

    # Not-UMZ aus: Leitung hat keine aktive Stufe
    n = _ref()
    _p_aendern(n, "L2", uebs_betriebsart="Aus")
    erg = S.pruefe_selektivitaet(n)
    assert erg.pruefung("T2 (OS)", "T1 (US)") is not None
    _hat(erg, WARNUNG, "L2 liegt in einem Versorgungspfad")

    # Topologiefehler: keine Pruefung, klare Meldung
    n = _ref()
    n.setze_netzform("ring")
    erg = S.pruefe_selektivitaet(n)
    assert not erg.ok and erg.pruefungen == [] and erg.status is None
    _hat(erg, FEHLER, "Topologie oder Schutzstufen")

    # Leeres Netz und Netz ohne Parameter
    assert not S.pruefe_selektivitaet(Netz()).ok
    n = _ref()
    for eid in n.elemente:
        n.parameter_setzen(eid, {})
    erg = S.pruefe_selektivitaet(n)
    assert erg.ok and erg.pruefungen == []
    _hat(erg, HINWEIS, "Keine bewertbaren Schutzstufen")

    # Ungueltiger Staffelabstand
    erg = S.pruefe_selektivitaet(_ref(), dt_soll=0.1, dt_min=0.2)
    _hat(erg, FEHLER, "Staffelabstand ungültig")

    # Unbekannte Kennlinie: Stufe wird nicht bewertet, Rest laeuft
    original = konstanten_motor.Kennlinie_51_def
    konstanten_motor.Kennlinie_51_def = "ANSI moderately inverse"
    try:
        erg = S.pruefe_selektivitaet(_ref())
    finally:
        konstanten_motor.Kennlinie_51_def = original
    _hat(erg, HINWEIS, "wird in der Zeitstaffelung noch nicht bewertet")
    assert erg.pruefung("M1", "L1") is not None

    # Sicherheitsnetz: ein Fehler in der Auswertung wird zur Meldung
    original = S.pruefe_paar
    def kaputt(*a, **k):
        raise ZeroDivisionError("Test")
    S.pruefe_paar = kaputt
    try:
        erg = S.pruefe_selektivitaet(_ref())
    finally:
        S.pruefe_paar = original
    _hat(erg, FEHLER, "Staffelprüfung abgebrochen (ZeroDivisionError")
    print("Fehlerfälle OK: fehlende Stufen, fehlender NB-Schutz, Topologiefehler, Sicherheitsnetz.")


# ── 12. Zufallsnetze ─────────────────────────────────────────────────────────
def test_zufallsnetze():
    import random
    rnd = random.Random(20261110)
    werte = [None, 0, -1, 0.05, 0.3, 1, 6, 12, 150, 1000, "x", True]
    schluessel = ["Sn_MVA", "uk_pct", "CT_OS_Prim", "CT_US_Prim", "IN_Ltg", "CT_Prim", "Pn_kW",
                  "I_gt_NB_A", "t_gt_NB_s", "t_I_Ph", "t_I_Ph_US", "t_I_Ph_HH", "t_I_Ph_HH_US",
                  "t_iph_h", "t_iph_hh", "iph_h", "iph_hh", "t_50_1", "t_50_2", "T_51", "f_51",
                  "uebs_betriebsart"]
    geprueft = 0
    for i in range(300):
        n = _ref()
        if i % 3 == 0:
            n.setze_netzform("ring")
            n.element_hinzufuegen("KU1", "Kupplung", "kupplung", "K3", "K4")
            n.element_aendern(rnd.choice(["L1", "L2", "KU1"]), zustand="aus")
        for eid in n.elemente:
            p = n.elemente[eid].p
            for k in rnd.sample(schluessel, 6):
                v = rnd.choice(werte)
                if v is None:
                    p.pop(k, None)
                else:
                    p[k] = v
            n.parameter_setzen(eid, p)
        for kid in rnd.sample(sorted(n.knoten), 2):
            n.knoten_aendern(kid, Ik_max_kA=rnd.choice([None, 0.5, 1.0, 50.0]), Ik_min_kA=None)
        erg = S.pruefe_selektivitaet(n, U_bezug_kV=rnd.choice([None, 0.4, 10.0, 110.0]))
        # Das Sicherheitsnetz darf nie greifen muessen
        versteckt = [m.text for m in erg.meldungen if "abgebrochen" in m.text]
        assert not versteckt, versteckt
        for p in erg.pruefungen:
            assert p.status in (S.OK, S.GELB, S.ROT) and p.text
            assert p.dt_s is None or p.dt_s == p.dt_s           # kein NaN
        geprueft += bool(erg.pruefungen)
    assert geprueft > 100, geprueft
    print(f"Zufallsnetze OK: 300 Netze ohne Absturz, {geprueft} davon mit Staffelprüfung.")


if __name__ == "__main__":
    test_staffelabstand()
    test_umrechnung()
    test_kennlinien()
    test_trafo_os_us_zeiten()
    test_referenznetz_werkseinstellung()
    test_gestaffeltes_netz()
    test_ampel_sweep()
    test_ik_grenze_und_luecke()
    test_bezugsspannung_invariant()
    test_ring()
    test_unvollstaendig_und_fehler()
    test_zufallsnetze()
    print("\nAlle Prüfungen bestanden.")
