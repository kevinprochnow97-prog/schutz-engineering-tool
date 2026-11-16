"""
test_netz_diagramm.py - Tests fuer das Staffeldiagramm (netz_diagramm.py)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Ausfuehren mit:  python test_netz_diagramm.py   (oder: pytest test_netz_diagramm.py)

Prueft:
 1. Ein Diagramm je Pfad, Kurven in der Reihenfolge Last -> Quelle.
 2. UMZ-Kennlinie gegen Handwerte: Senkrechte an der Anregung, Stufen, Ende bei Ik max.
 3. Diagramm und Zeitpruefung widersprechen sich nicht (gleiche Funktion, gleiche Werte).
 4. AMZ-Kennlinie des Motors, unverzoegerte Stufe auf der Anzeigegrenze.
 5. Marken Ik max / Ik min, Werte ausserhalb des Bereichs werden gemeldet.
 6. Diagramm des Staffelvorschlags zeigt die neuen Zeiten.
 7. Vega-Lite-Beschreibung ist JSON-faehig und vollstaendig.
 8. Fehlerfaelle: leeres Netz, Netz ohne Stufen, nie eine Ausnahme.
"""

import json
from pathlib import Path

import netz_diagramm as D
import netz_selektivitaet as S
import netz_stromstaffel as SS
from netz_modell import Netz

BEISPIEL = Path(__file__).parent / "beispielnetze" / "industrie_10kV.json"
BEISPIEL_RING = Path(__file__).parent / "beispielnetze" / "industrie_10kV_ring.json"


def _netz() -> Netz:
    return Netz.laden(BEISPIEL)


def _kurve(d, name):
    return [k for k in d.kurven if k.name == name][0]


def _nah(a, b, rel=1e-6):
    return abs(a - b) <= rel * abs(b)


# ── 1. Aufbau ────────────────────────────────────────────────────────────────
def test_ein_diagramm_je_pfad():
    n = _netz()
    vorher = n.to_dict()
    erg = S.pruefe_selektivitaet(n)
    ds = D.erzeuge_diagramme(n)
    assert n.to_dict() == vorher
    assert [d.pfad for d in ds] == erg.pfade
    assert ds[0].titel == "M1 → L1 → T1 (US) → T1 (OS) → E1"
    assert [k.name for k in ds[0].kurven] == ds[0].pfad
    assert all(d.U_bezug_kV == 10.0 for d in ds)
    print("Aufbau OK: zwei Pfade, Kurven von der Last zur Quelle.")


# ── 2. UMZ-Kennlinie gegen Handwerte ─────────────────────────────────────────
def test_umz_kennlinie():
    d = D.erzeuge_diagramme(_netz())[0]
    # L1: Iph> 1,2 x 300 A = 360 A / 0,5 s, Iph>> 2,0 x 300 A = 600 A / 0,1 s, Ende Ik max K2 = 10 kA
    p = _kurve(d, "L1").punkte
    assert [(round(I), round(t, 3), s) for I, t, _, s in p] == [
        (360, d.t_oben_s, "Iph>"), (360, 0.5, "Iph>"), (600, 0.5, "Iph>"),
        (600, 0.1, "Iph>>"), (10000, 0.1, "Iph>>")]
    # Netzbetreiber: 160 A bei 110 kV = 1760 A bei 10 kV, 1,2 s, bis zum rechten Rand
    p = _kurve(d, "E1").punkte
    assert _nah(p[0][0], 1760.0) and p[1][1] == 1.2 and _nah(p[-1][0], d.I_max_A)
    # Rechter Rand: 1,3 x groesster Strom auf Bezugsebene (hier I>> OS von T1 mit 11997 A)
    assert _nah(d.I_max_A, 1.3 * max(S.anregestrom_bez(s, 10.0) for o in S.pruefe_selektivitaet(_netz()).orte
                                     for s in o.stufen), 1e-9)
    assert d.t_oben_s == 10.0
    print("UMZ OK: L1 360 A / 0,5 s und 600 A / 0,1 s, Ende bei Ik max 10 kA.")


# ── 3. Diagramm und Zeitpruefung stimmen ueberein ────────────────────────────
def test_uebereinstimmung_mit_pruefung():
    n = _netz()
    erg = S.pruefe_selektivitaet(n)
    orte = {o.name: o for o in erg.orte}
    for d in D.erzeuge_diagramme(n, erg):
        for k in d.kurven:
            for I, t_anz, t, stufe in k.punkte[1:]:
                t_ref, _ = S.ausloesezeit(orte[k.name], I, erg.U_bezug_kV)
                assert t_ref is not None
                # Am Stufensprung gibt es zwei Punkte, einer traegt die Zeit vor dem Sprung
                assert t == t_ref or any(q[0] == I and q[2] == t_ref for q in k.punkte), (k.name, I)
    # Der Zeitabstand aus der Pruefung ist im Diagramm ablesbar
    p = [x for x in erg.pruefungen if x.unten == "L1" and x.oben == "T1 (US)"][0]
    dt = (S.ausloesezeit(orte["T1 (US)"], p.I_bez_A, 10.0)[0]
          - S.ausloesezeit(orte["L1"], p.I_bez_A, 10.0)[0])
    assert abs(dt - p.dt_s) < 1e-9
    print("Übereinstimmung OK: jede Zeit im Diagramm ist die Zeit der Staffelprüfung.")


# ── 4. AMZ und unverzoegerte Stufe ───────────────────────────────────────────
def test_amz_und_anzeigegrenze():
    d = D.erzeuge_diagramme(_netz())[0]
    p = _kurve(d, "M1").punkte
    assert len(p) > 20                                              # Stuetzstellen der AMZ-Kennlinie
    amz = [(I, t) for I, t_anz, t, s in p if s == "Ip"]
    assert all(a[1] >= b[1] for a, b in zip(amz, amz[1:]))          # faellt mit dem Strom
    assert all(q[1] <= d.t_oben_s for q in p)                       # oben abgeschnitten
    # 50-2 des Motors ist unverzoegert: Anzeige auf 0,01 s, echter Wert 0 s
    letzte = p[-1]
    assert letzte[3] == "I>> (50-2)" and letzte[2] == 0.0 and letzte[1] == D.T_ANZEIGE_MIN
    assert round(letzte[0]) == 9100                                 # Ende bei Ik max K3
    print("AMZ OK: Motorkennlinie fallend, 50-2 unverzögert auf der Linie 0,01 s.")


# ── 5. Marken ────────────────────────────────────────────────────────────────
def test_marken():
    ds = D.erzeuge_diagramme(_netz())
    m = {x.text: x.I_bez_A for x in ds[0].marken}
    assert m == {"Ik max K3": 9100.0, "Ik min K3": 6800.0, "Ik max K2": 10000.0, "Ik min K2": 7500.0}
    assert any("Ik max K1" in x.text and "172700" in x.text for x in ds[0].meldungen)
    # 0,4-kV-Knoten auf 10 kV bezogen: 35 kA * 0,4 / 10 = 1400 A, kein Ik min eingegeben
    m = {x.text: x.I_bez_A for x in ds[1].marken}
    assert _nah(m["Ik max K5"], 1400.0) and "Ik min K5" not in m
    assert round(_kurve(ds[1], "T2 (US)").punkte[-1][0]) == 1400    # Kurve endet dort
    print("Marken OK: Ik je Messknoten, K1 außerhalb gemeldet, K5 auf 10 kV bezogen.")


# ── 6. Diagramm des Vorschlags ───────────────────────────────────────────────
def test_vorschlag():
    n = _netz()
    vor = SS.gesamtvorschlag(n)
    ist = D.erzeuge_diagramme(n)[0]
    neu = D.erzeuge_diagramme(n, vor.zeit.pruefung)[0]
    assert neu.pfad == ist.pfad
    t_ist = _kurve(ist, "L1").punkte[1][2]
    t_neu = _kurve(neu, "L1").punkte[1][2]
    v = [x for x in vor.zeit.vorschlaege if x.element == "L1" and x.stufe == "Iph>"][0]
    assert (t_ist, t_neu) == (v.t_alt_s, v.t_neu_s) and t_neu > t_ist
    # Im Vorschlag liegt jede Kennlinie ueber der darunter (ausser gegen den Netzbetreiber)
    orte = {o.name: o for o in vor.zeit.pruefung.orte}
    for unten, oben in zip(neu.pfad, neu.pfad[1:-1]):
        for I, *_ in _kurve(neu, oben).punkte:
            tu = S.ausloesezeit(orte[unten], I, 10.0)[0]
            to = S.ausloesezeit(orte[oben], I, 10.0)[0]
            if tu is not None and to is not None and I <= _kurve(neu, unten).punkte[-1][0]:
                assert to - tu >= vor.zeit.pruefung.dt_min_s - 1e-9, (unten, oben, I)
    print("Vorschlag OK: Diagramm zeigt die neuen Zeiten, Kennlinien liegen gestaffelt.")


# ── 7. Vega-Lite ─────────────────────────────────────────────────────────────
def test_vega_spec():
    d = D.erzeuge_diagramme(_netz())[0]
    spec = json.loads(json.dumps(D.vega_spec(d)))                   # reines, JSON-faehiges Dict
    assert len(spec["layer"]) == 3
    linien = spec["layer"][1]["data"]["values"]
    assert {z["Schutzort"] for z in linien} == set(d.pfad)
    assert linien[0]["Schutzort"] == "E1"                           # Quelle zuerst gezeichnet
    enc = spec["layer"][1]["encoding"]
    assert enc["x"]["scale"]["type"] == "log" and enc["y"]["scale"]["type"] == "log"
    assert enc["order"] == {"field": "nr"} and enc["color"]["sort"] == d.pfad
    assert "10,0 kV" in enc["x"]["title"]
    assert len(spec["layer"][0]["data"]["values"]) == len(d.marken) == 4
    assert all(z["t"] >= D.T_ANZEIGE_MIN for z in linien)
    print("Vega-Lite OK: drei Ebenen, logarithmische Achsen, Daten eingebettet.")


# ── 8. Fehlerfaelle ──────────────────────────────────────────────────────────
def test_fehlerfaelle():
    assert D.erzeuge_diagramme(Netz()) == []
    n = _netz()
    for eid in ("T1", "T2", "L1", "L2", "M1"):
        n.parameter_setzen(eid, {})                                  # keine Schutzstufen mehr
    assert all(len(d.kurven) <= 1 for d in D.erzeuge_diagramme(n))
    ds = D.erzeuge_diagramme(_netz(), pruefung="Unsinn")
    assert len(ds) == 1 and not ds[0].kurven and "abgebrochen" in ds[0].meldungen[0].text
    # Ohne Ik max am Knoten laeuft die Kurve bis zum rechten Rand
    n = _netz()
    n.knoten_aendern("K2", Ik_max_kA=None, Ik_min_kA=None)
    d = D.erzeuge_diagramme(n)[0]
    assert _nah(_kurve(d, "L1").punkte[-1][0], d.I_max_A)
    # Ring: Diagramme der aktuellen Lage
    assert len(D.erzeuge_diagramme(Netz.laden(BEISPIEL_RING))) == 2
    print("Fehlerfälle OK: leeres Netz, fehlende Stufen, fehlendes Ik, nie eine Ausnahme.")


if __name__ == "__main__":
    test_ein_diagramm_je_pfad()
    test_umz_kennlinie()
    test_uebereinstimmung_mit_pruefung()
    test_amz_und_anzeigegrenze()
    test_marken()
    test_vorschlag()
    test_vega_spec()
    test_fehlerfaelle()
    print("\nAlle Prüfungen bestanden.")
