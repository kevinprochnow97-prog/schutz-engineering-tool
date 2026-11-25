"""
test_netz_ring.py - Tests fuer den Ring ueber alle Trennstellenlagen (netz_ring.py)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Ausfuehren mit:  python test_netz_ring.py   (oder: pytest test_netz_ring.py)

Prueft:
 1. Untergrenzen im Zeitvorschlag (netz_selektivitaet.staffelvorschlag).
 2. Lagen: eine Kopie je Ringelement, Original unveraendert, Strahlennetz ohne Lagen.
 3. Ist-Pruefung in allen Lagen, Pfade je Lage gegen Handrechnung.
 4. Ringvorschlag im Beispielring gegen Handrechnung, Gegenpruefung in jeder Lage.
 5. Uebernahme ins Netz und zweiter Lauf ohne Aenderung.
 6. Ring mit vier Leitungen: gegenlaeufige Ketten, Ursache benannt, nicht uebernehmbar.
    Dreileitungsring loesbar, Ergebnis unabhaengig von der aktuellen Lage.
 7. Fehlerfaelle.
 8. Zufallsnetze: nie abgebrochen, ein Fixpunkt ist in jeder Lage selektiv.
"""

import random
from pathlib import Path

import netz_adapter as A
import netz_ring as R
import netz_selektivitaet as S
import netz_stromstaffel as SS
from netz_modell import Netz
from netz_topologie import FEHLER, HINWEIS, WARNUNG

BEISPIEL = Path(__file__).parent / "beispielnetze" / "industrie_10kV.json"
BEISPIEL_RING = Path(__file__).parent / "beispielnetze" / "industrie_10kV_ring.json"


def _ring() -> Netz:
    return Netz.laden(BEISPIEL_RING)


def _p_aendern(n, eid, **neu):
    p = n.elemente[eid].p
    for k, v in neu.items():
        if v is None:
            p.pop(k, None)
        else:
            p[k] = v
    n.parameter_setzen(eid, p)


def _text(erg, stufe) -> str:
    return " | ".join(m.text for m in erg.meldungen if m.stufe == stufe)


def _ring4() -> Netz:
    """
    Ring mit vier Leitungen La..Ld zwischen K2..K5 und je einem Motor an K3, K4, K5.
    Mit Ld als Trennstelle liegt Lb ueber Lc, mit La als Trennstelle liegt Lc ueber Lb.
    """
    n = Netz.laden(BEISPIEL)
    for e in ("M1", "T2", "L1", "L2"):
        n.element_entfernen(e)
    for k in ("K3", "K4", "K5"):
        n.knoten_entfernen(k)
    for k, ik, ikm in (("K3", 9.0, 6.5), ("K4", 8.0, 5.8), ("K5", 8.5, 6.0)):
        n.knoten_hinzufuegen(k, k, 10.0, "isoliert", ik, ikm)
    lp = dict(L_km=0.8, X_Belag=0.11, phi_Ltg=28.1, IN_Ltg=300, CT_Prim=200, CT_Sek=1,
              uebs_betriebsart="Ein: immer aktiv")
    for eid, a, b in (("La", "K2", "K3"), ("Lb", "K3", "K4"), ("Lc", "K4", "K5"), ("Ld", "K5", "K2")):
        n.element_hinzufuegen(eid, eid, "leitung", a, b, dict(lp), "ein")
    mp = dict(Pn_kW=1000, cos_phi=0.88, eta=0.96, I_Anlauf_Verh=5.5, t_Anlauf=8,
              CT_Prim=100, CT_Sek=1, f_50_2=8.81)
    for k in ("K3", "K4", "K5"):
        n.element_hinzufuegen("M" + k[1], "M" + k[1], "motor", k, None, dict(mp), "ein")
    n.element_aendern("Ld", zustand="aus")
    n.setze_netzform("ring")
    return n


# ── 1. Untergrenzen im Zeitvorschlag ─────────────────────────────────────────
def test_untergrenzen():
    n = Netz.laden(BEISPIEL)
    ohne = {(v.element, v.stufe): v for v in S.staffelvorschlag(n).vorschlaege}
    assert ohne[("L1", "Iph>")].t_neu_s == 0.8
    mit = {(v.element, v.stufe): v for v in S.staffelvorschlag(
        n, untergrenzen={("L1", "Iph>"): 1.4, ("L2", "Iph>"): 0.5, ("M1", "I> (50-1)"): 0.9}).vorschlaege}
    # Boden ueber dem Bedarf: gilt, mit Begruendung. Boden unter dem Bedarf: ohne Wirkung.
    assert mit[("L1", "Iph>")].t_neu_s == 1.4 and "Untergrenze 1,40 s" in mit[("L1", "Iph>")].grund
    assert mit[("L2", "Iph>")].t_neu_s == ohne[("L2", "Iph>")].t_neu_s == 1.1
    # Endpunkte bleiben, auch wenn ein Boden gesetzt ist
    assert mit[("M1", "I> (50-1)")].t_neu_s == 0.5
    # Der Boden wirkt nach oben weiter: T1 (US) muss ueber L1 mit 1,4 s liegen
    gesamt = SS.gesamtvorschlag(n, untergrenzen={("L1", "Iph>"): 1.4})
    z = {(v.element, v.stufe): v for v in gesamt.zeit.vorschlaege}
    assert z[("L1", "Iph>")].t_neu_s == 1.4
    print("Untergrenzen OK: Boden hebt an, wirkt nie nach unten, Endpunkte fest.")


# ── 2. Lagen ─────────────────────────────────────────────────────────────────
def test_lagen():
    n = _ring()
    vorher = n.to_dict()
    lagen, meld = R.erzeuge_lagen(n)
    assert sorted(l.trennstelle for l in lagen) == ["K34", "L1", "L2"]
    for l in lagen:
        offen = sorted(eid for eid, e in l.netz.elemente.items() if e.zustand == "aus")
        assert offen == [l.trennstelle], (l.trennstelle, offen)
        assert l.netz is not n and l.netz.netzform == "ring"
    assert n.to_dict() == vorher                          # Original unveraendert
    # Strahlennetz: keine Lagen, Hinweis statt Fehler
    lagen, meld = R.erzeuge_lagen(Netz.laden(BEISPIEL))
    assert lagen == [] and any(m.stufe == HINWEIS and "keinen Ring" in m.text for m in meld)
    print("Lagen OK: drei Trennstellen, Original unveraendert, Strahlennetz ohne Lagen.")


# ── 3. Ist-Pruefung ──────────────────────────────────────────────────────────
def test_ist_pruefung():
    erg = R.pruefe_ringlagen(_ring())
    assert erg.ok and len(erg.lagen) == 3
    pfade = {l.trennstelle: l.zeit.pfade for l in erg.lagen}
    # Kupplung offen: M1 an L1, T2 an L2. L1 offen: M1 ueber L2. L2 offen: T2 ueber L1.
    assert ["M1", "L1", "T1 (US)", "T1 (OS)", "E1"] in pfade["K34"]
    assert ["M1", "L2", "T1 (US)", "T1 (OS)", "E1"] in pfade["L1"]
    assert ["T2 (US)", "T2 (OS)", "L1", "T1 (US)", "T1 (OS)", "E1"] in pfade["L2"]
    # Mit den Werksvoreinstellungen ist in jeder Lage nur das Paar T1 (OS) gegen E1 gruen
    for l in erg.lagen:
        assert l.status == S.ROT
        gruen = [(p.unten, p.oben) for p in l.zeit.pruefungen if p.status == S.OK]
        assert gruen == [("T1 (OS)", "E1")], (l.trennstelle, gruen)
    assert erg.status == S.ROT and erg.lage("L1") is not None and erg.lage("X") is None
    assert "Ik max und Ik min" in _text(erg, HINWEIS)
    print("Ist-Prüfung OK: drei Lagen, Pfade wie erwartet, alle rot ausser dem Netzbetreiber-Paar.")


# ── 4. Ringvorschlag im Beispielring ─────────────────────────────────────────
def test_ringvorschlag_beispiel():
    rv = R.ringvorschlag(_ring())
    assert rv.ok and rv.konvergiert and rv.uebernehmbar
    assert rv.runden == 2                                  # Runde 1 rechnet, Runde 2 bestaetigt
    w = {(x.element, x.parameter): x for x in rv.werte}
    # Handrechnung: L1 und L2 liegen nie in derselben Kette, jede Leitung ist in einer Lage
    # ueber T2 (OS). Je Parameter der groesste Wert ueber alle Lagen:
    #   I>> = 1,2 * 1400 A (Ik K5 ueber T2) = 1680 A = 5,60 x IN, Iph> = 0,8 + 0,3 = 1,1 s,
    #   Iph>> 0,1 s (I>> OS T2) + 0,3 s = 0,4 s
    for eid in ("L1", "L2"):
        assert abs(w[(eid, "iph_hh")].neu - 5.6) < 1e-9
        assert abs(w[(eid, "t_iph_h")].neu - 1.1) < 1e-9 and abs(w[(eid, "t_iph_hh")].neu - 0.4) < 1e-9
    # T1 OS: 12,38 x IN (Stufensteller), T1 US: 9480 A = 8,21 x IN aus der Lage mit L1 offen
    # (nur L2 mit Ik K4 = 7,9 kA darunter, 1,2 * 7900 A = 9480 A liegt unter Ik K2 = 10 kA)
    assert abs(w[("T1", "f_I_Ph_HH_OS")].neu - 12.38) < 1e-9
    assert abs(w[("T1", "f_I_Ph_HH_US")].neu - 8.21) < 1e-9
    assert abs(w[("T1", "t_I_Ph")].neu - 1.0) < 1e-9 and abs(w[("T1", "t_I_Ph_US")].neu - 0.7) < 1e-9
    # Nichts wird abgesenkt
    assert all(x.neu >= x.alt - 1e-9 or x.art == "Zeit" for x in rv.werte)
    # Gegenpruefung: in keiner Lage rot, nur T1 (OS) gegen den Netzbetreiber (1,2 s) mit 0,2 s gelb
    assert rv.pruefung.status == S.GELB
    for l in rv.pruefung.lagen:
        gelb = [(p.unten, p.oben, round(p.dt_s, 6)) for p in l.zeit.pruefungen if p.status == S.GELB]
        assert gelb == [("T1 (OS)", "E1", 0.2)], (l.trennstelle, gelb)
        assert S.ROT not in {p.status for p in l.zeit.pruefungen}
    assert "Lage K34, L1, L2" in _text(rv, WARNUNG) and "1,00 s" in _text(rv, WARNUNG)
    print("Ringvorschlag OK: L1 und L2 gleich (5,60 · 1,1 s · 0,4 s), T1 OS 12,38, alle Lagen ohne rot.")


# ── 5. Uebernahme und zweiter Lauf ───────────────────────────────────────────
def test_uebernahme_ring():
    n = _ring()
    rv = R.ringvorschlag(n)
    for eid, p_neu in rv.parameter_je_element().items():
        p = dict(n.elemente[eid].p)
        p.update(p_neu)
        n.parameter_setzen(eid, p)
    erg = R.pruefe_ringlagen(n)
    for l in erg.lagen:
        assert S.ROT not in {p.status for p in l.zeit.pruefungen}, l.trennstelle
    zweit = R.ringvorschlag(n)
    assert zweit.konvergiert and not zweit.geaendert and not zweit.uebernehmbar
    # Faktoren: nur geaenderte werden geschrieben, die Tab-Automatik bleibt sonst erhalten
    assert "f_I_Ph_HH_OS" in rv.parameter_je_element()["T1"]
    assert "f_I_Ph_HH_OS" not in rv.parameter_je_element().get("T2", {})
    print("Übernahme OK: nach dem Schreiben in allen Lagen ohne rot, zweiter Lauf ohne Änderung.")


# ── 6. Gegenlaeufige Ketten ──────────────────────────────────────────────────
def test_gegenlaeufige_ketten():
    n = _ring4()
    # Pfade: mit Ld offen liegt Lb ueber Lc, mit La offen liegt Lc ueber Lb
    erg = R.pruefe_ringlagen(n)
    pfade = {l.trennstelle: l.zeit.pfade for l in erg.lagen}
    assert ["M5", "Lc", "Lb", "La", "T1 (US)", "T1 (OS)", "E1"] in pfade["Ld"]
    assert ["M3", "Lb", "Lc", "Ld", "T1 (US)", "T1 (OS)", "E1"] in pfade["La"]
    # Die Ursache wird aus den Pfaden namentlich bestimmt
    paare = R.gegenlaeufige_paare(erg)
    assert ("Lc", "Lb", "La", "Ld") in paare, paare
    rv = R.ringvorschlag(n)
    assert not rv.konvergiert and not rv.uebernehmbar and rv.runden == R.MAX_RUNDEN
    w = _text(rv, WARNUNG)
    assert "Gegenläufige Ketten" in w and "Lc liegt mit Trennstelle La über Lb" in w
    assert "Trennstelle festlegen" in w and "außerhalb des Tools" in w
    # Keine weggelaufenen Zeiten anzeigen: ohne Fixpunkt gibt es keine Werte
    assert rv.werte == [] and rv.pruefung is None and rv.parameter_je_element() == {}
    # Gegenprobe: jede der vier Lagen fuer sich ist staffelbar (kein Widerspruch innerhalb einer Lage)
    for l in R.erzeuge_lagen(n)[0]:
        assert SS.gesamtvorschlag(l.netz).ok
    # Im Beispielring gibt es keine gegenlaeufigen Paare
    assert R.gegenlaeufige_paare(R.pruefe_ringlagen(_ring())) == []
    print("Gegenläufige Ketten OK: Ursache benannt, keine Werte, jede Lage für sich lösbar.")


# ── 6b. Dreileitungsring und Unabhaengigkeit von der aktuellen Lage ──────────
def _ring3() -> Netz:
    """Beispielring, die Kupplung ist durch eine Leitung L3 mit eigenem Schutz ersetzt."""
    n = _ring()
    n.element_entfernen("K34")
    n.element_hinzufuegen("L3", "L3", "leitung", "K3", "K4",
                          dict(L_km=0.6, X_Belag=0.11, phi_Ltg=28.1, IN_Ltg=300, CT_Prim=200,
                               CT_Sek=1, uebs_betriebsart="Ein: immer aktiv"), "aus")
    return n


def test_dreileitungsring():
    """
    L3 liegt nie ueber L1 oder L2 (beide haengen an der Einspeise-Sammelschiene), es gibt
    also keine gegenlaeufigen Ketten. Der Ring ist loesbar, die Kette wird aber eine Stufe laenger.
    """
    n = _ring3()
    assert R.gegenlaeufige_paare(R.pruefe_ringlagen(n)) == []
    rv = R.ringvorschlag(n)
    assert rv.konvergiert and rv.uebernehmbar
    w = {(x.element, x.parameter): x for x in rv.werte}
    # L1 ueber L3 (Lage L2 offen): Ik max K4 7,9 kA * 1,2 = 9480 A = 31,6 x IN liegt ueber dem
    # Einstellbereich 10 x IN. Die Anlaufgrenze von M1 gilt trotzdem: 1,2 * 1204,2 A -> 4,82 x IN
    assert abs(w[("L1", "iph_hh")].neu - 4.82) < 1e-9 and "Anlaufstrom" in w[("L1", "iph_hh")].kurz
    # L3 ueber T2 (OS) wie L1/L2 im Beispielring: 5,60 x IN, 1,1 s, 0,4 s
    assert abs(w[("L3", "iph_hh")].neu - 5.6) < 1e-9 and abs(w[("L3", "t_iph_h")].neu - 1.1) < 1e-9
    # L1 und L2 liegen je einmal ueber L3 (1,1 s): 1,4 s
    assert abs(w[("L1", "t_iph_h")].neu - 1.4) < 1e-9 and abs(w[("L2", "t_iph_h")].neu - 1.4) < 1e-9
    for l in rv.pruefung.lagen:
        for p in l.zeit.pruefungen:
            assert p.status != S.ROT or p.oben == "E1", (l.trennstelle, p.unten, p.oben)
        assert S.ROT not in {p.status for p in l.strom.pruefungen if p.art != "Anlauf"}, l.trennstelle  # Anlauf: eigene Pruefung
    print("Dreileitungsring OK: lösbar, L1 mit Anlaufgrenze 4,82 × IN, L1 und L2 auf 1,4 s.")


def test_unabhaengig_von_aktueller_lage():
    ergebnisse = []
    for aus in ("K34", "L1", "L2"):
        n = _ring()
        for r in ("K34", "L1", "L2"):
            n.element_aendern(r, zustand="aus" if r == aus else "ein")
        rv = R.ringvorschlag(n)
        assert rv.konvergiert
        ergebnisse.append({(x.element, x.parameter): (round(x.alt, 6), round(x.neu, 6)) for x in rv.werte})
    assert ergebnisse[0] == ergebnisse[1] == ergebnisse[2]
    print("Unabhängigkeit OK: derselbe Vorschlag, egal welche Trennstelle gerade offen ist.")


# ── 7. Fehlerfaelle ──────────────────────────────────────────────────────────
def test_fehlerfaelle():
    rv = R.ringvorschlag(Netz.laden(BEISPIEL))               # Strahlennetz
    assert rv.ok and rv.werte == [] and not rv.uebernehmbar and "keinen Ring" in _text(rv, HINWEIS)
    n = _ring()
    n.element_aendern("E1", zustand="aus")
    for erg in (R.pruefe_ringlagen(n), R.ringvorschlag(n)):
        assert not erg.ok
    assert not R.ringvorschlag(Netz()).ok and R.pruefe_ringlagen(Netz()).lagen == []
    # Ring geschlossen betrieben: von der Topologie als Fehler gemeldet, kein Absturz
    n = _ring()
    n.element_aendern("K34", zustand="ein")
    assert not R.ringvorschlag(n).ok
    print("Fehlerfälle OK: Strahlennetz, fehlende Einspeisung, leeres Netz, geschlossener Ring.")


# ── 8. Zufallsnetze ──────────────────────────────────────────────────────────
def test_zufall():
    zufall = random.Random(12112026)
    konvergiert = 0
    for _ in range(40):
        n = _ring()
        for k in ("K2", "K3", "K4", "K5"):
            ik = zufall.choice([None, 2.0, 7.5, 12.0, 35.0])
            n.knoten_aendern(k, Ik_max_kA=ik, Ik_min_kA=None if ik is None else zufall.choice([None, ik * 0.4]))
        _p_aendern(n, "T1", Stufensteller_pm=zufall.choice([0, 5, 16]))
        _p_aendern(n, "L1", iph_hh=zufall.choice([None, 1.0, 5.0]), t_iph_h=zufall.choice([None, 0.4, 1.5]))
        _p_aendern(n, "L2", iph_hh=zufall.choice([None, 2.0, 8.0]))
        _p_aendern(n, "M1", f_50_2=zufall.choice([None, 4.0, 9.0]))
        rv = R.ringvorschlag(n, k_S=zufall.choice([1.0, 1.2, 1.5]), dt_soll=zufall.choice([0.2, 0.3, 0.4]))
        text = " ".join(m.text for m in rv.meldungen)
        assert "abgebrochen" not in text, text
        if rv.ok and rv.konvergiert:
            konvergiert += 1
            for l in rv.pruefung.lagen:
                for p in l.zeit.pruefungen:
                    if p.status == S.ROT:                    # nur der Netzbetreiber darf rot sein
                        assert p.oben == "E1", (l.trennstelle, p.unten, p.oben, p.text)
    assert konvergiert > 10, konvergiert
    print(f"Zufall OK: 40 Ringe, nie abgebrochen, {konvergiert} Fixpunkte alle selektiv.")


def test_ik_ersetzen_je_lage():
    """Entscheidung 17.11.2026: im Ring gilt je Lage der berechnete Ik, mit Rueckfall auf den eingegebenen."""
    n = _ring()
    vorher = n.to_dict()
    lagen, meld = R.erzeuge_lagen(n, ik_ersetzen=True)
    assert n.to_dict() == vorher and not any(m.stufe == FEHLER for m in meld)
    ik = {l.trennstelle: {k: v.Ik_max_kA for k, v in l.netz.knoten.items()} for l in lagen}
    assert abs(ik["L1"]["K3"] - 8.807) < 5e-3 and abs(ik["L2"]["K4"] - 10.101) < 5e-3   # je Lage, mit Motoren
    assert ik["L1"]["K3"] != ik["L2"]["K3"]
    assert all(l.ik_ersetzt and not l.ik_rueckfall for l in lagen)
    # ohne den Schalter bleibt alles beim Eingegebenen
    lagen0, _ = R.erzeuge_lagen(n)
    assert all(l.netz.knoten["K4"].Ik_max_kA == 7.9 for l in lagen0)
    # Vorschlag und Pruefung laufen mit berechneten Werten, der Hinweis nennt die Quelle
    rv = R.ringvorschlag(n, ik_ersetzen=True)
    assert rv.ok and rv.konvergiert and rv.pruefung is not None
    texte = " ".join(m.text for m in rv.meldungen)
    assert "je Trennstellenlage aus der Kurzschlussrechnung" in texte and "Prüfpunkte 7 und 9" in texte
    erg = R.pruefe_ringlagen(n, ik_ersetzen=True)
    assert "je Trennstellenlage aus der Kurzschlussrechnung" in " ".join(m.text for m in erg.meldungen)
    assert n.to_dict() == vorher
    # Rueckfall: ohne Sk nichts berechenbar, es gilt der eingegebene Wert, und das wird gesagt
    p = dict(n.elemente["E1"].p)
    p.pop("Sk_max_MVA"), p.pop("Sk_min_MVA")
    n.parameter_setzen("E1", p)
    lagen2, meld2 = R.erzeuge_lagen(n, ik_ersetzen=True)
    assert all(l.netz.knoten["K4"].Ik_max_kA == 7.9 for l in lagen2)
    assert any("Nicht berechenbar, deshalb gilt der eingegebene Wert" in m.text and "K4 Ik max" in m.text
               for m in meld2)
    print("Ring mit berechnetem Ik OK: je Lage, Rueckfall, Quelle genannt.")


if __name__ == "__main__":
    test_untergrenzen()
    test_lagen()
    test_ist_pruefung()
    test_ringvorschlag_beispiel()
    test_uebernahme_ring()
    test_gegenlaeufige_ketten()
    test_ik_ersetzen_je_lage()
    test_dreileitungsring()
    test_unabhaengig_von_aktueller_lage()
    test_fehlerfaelle()
    test_zufall()
    print("\nAlle Prüfungen bestanden.")
