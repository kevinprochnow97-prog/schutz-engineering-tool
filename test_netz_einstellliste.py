"""
test_netz_einstellliste.py - Tests fuer die Einstellliste (netz_einstellliste.py)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Ausfuehren mit:  python test_netz_einstellliste.py   (oder: pytest test_netz_einstellliste.py)

Prueft:
 1. Ist-Liste: eine Zeile je Schutzstufe, gleiche Werte wie der Adapter, nichts geaendert.
 2. Sekundaerwert = Primaerwert / Wandleruebersetzung, Faktor x IN.
 3. Staffelvorschlag: geaenderte Zeilen entsprechen den Vorschlagswerten, Begruendung vorhanden.
 4. Ringvorschlag im Ringnetz.
 5. CSV: BOM, Semikolon, Dezimalkomma, gleiche Zeilenzahl, Kopfzeilen.
 6. DIGSI-Adressen nur aus HERST, nie geraten (auch die I>-Stufen).
 7. Fehlerfaelle: leeres Netz, unbekannte Stufe im Vorschlag, nie eine Ausnahme.
"""

import csv
import io
from pathlib import Path

import konstanten_leitung
import netz_adapter
import netz_einstellliste as E
import netz_ring
import netz_stromstaffel
from netz_modell import Netz

BEISPIEL = Path(__file__).parent / "beispielnetze" / "industrie_10kV.json"
BEISPIEL_RING = Path(__file__).parent / "beispielnetze" / "industrie_10kV_ring.json"


def _netz() -> Netz:
    return Netz.laden(BEISPIEL)


def test_ist_liste():
    n = _netz()
    vorher = n.to_dict()
    ad = netz_adapter.erzeuge_schutzstufen(n)
    liste = E.erstelle(n, ad)
    assert liste.ok and len(liste.zeilen) == len(ad.stufen) == 16
    assert not liste.geaendert and liste.quelle_vorschlag == ""
    assert {(z.element, z.stufe) for z in liste.zeilen} == {(s.element, s.stufe) for s in ad.stufen}
    for z in liste.zeilen:
        s = [s for s in ad.stufen if (s.element, s.stufe) == (z.element, z.stufe)][0]
        assert z.I_prim_A == s.I_prim_A and z.t_s == s.t_s and z.messort == s.messort
    assert n.to_dict() == vorher                                     # Modell unveraendert
    print("Ist-Liste OK: 16 Stufen, Werte wie im Adapter.")


def test_sekundaer_und_faktor():
    n = _netz()
    liste = E.erstelle(n)
    mit = [z for z in liste.zeilen if z.wandler]
    assert mit, "Beispielnetz hat Wandlerangaben"
    for z in mit:
        prim, sek = (float(x.replace(".", "").replace(",", ".")) for x in z.wandler.replace(" A", "").split("/"))
        assert abs(z.I_sek_A - z.I_prim_A * sek / prim) < 1e-9
    for z in liste.zeilen:
        if z.faktor_IN is not None:
            assert z.faktor_IN > 0
    # Ohne Wandlerangabe bleibt der Sekundaerwert leer
    sauber = E._wandler("leitung", "Iph>", {})
    assert sauber == (None, "")
    print("Sekundärwerte OK.")


def test_staffelvorschlag():
    n = _netz()
    ad = netz_adapter.erzeuge_schutzstufen(n)
    vor = netz_stromstaffel.gesamtvorschlag(n, ad, dt_soll=0.30)
    aend = E.aus_gesamtvorschlag(vor)
    assert aend
    liste = E.erstelle(n, ad, aend, "Staffelvorschlag", dt_soll=0.30)
    assert liste.ok and liste.quelle_vorschlag == "Staffelvorschlag"
    assert {(z.element, z.stufe) for z in liste.geaendert} == set(aend)
    for z in liste.geaendert:
        assert z.begruendung
        if z.t_neu_s is not None:
            assert z.t_neu_s != z.t_s and "Zeit:" in z.begruendung
        if z.I_neu_prim_A is not None:
            assert "Ansprechwert:" in z.begruendung and z.faktor_neu_IN is not None
    # Ungeaenderte Zeilen haben keine neuen Werte
    assert all(z.I_neu_prim_A is None and z.t_neu_s is None for z in liste.zeilen if not z.geaendert)
    # Begruendung der Zeit im gleichen Wortlaut wie im Tab
    assert any("0,30 s über" in z.begruendung for z in liste.geaendert)
    print(f"Staffelvorschlag OK: {len(liste.geaendert)} geänderte Zeilen.")


def test_ringvorschlag():
    n = Netz.laden(BEISPIEL_RING)
    rv = netz_ring.ringvorschlag(n, dt_soll=0.30)
    aend = E.aus_ringvorschlag(rv)
    assert aend and rv.geaendert
    liste = E.erstelle(n, None, aend, "Ringvorschlag")
    assert liste.ok and liste.geaendert
    assert {(z.element, z.stufe) for z in liste.geaendert} == set(aend)
    print(f"Ringvorschlag OK: {len(liste.geaendert)} geänderte Zeilen.")


def test_csv():
    n = _netz()
    ad = netz_adapter.erzeuge_schutzstufen(n)
    aend = E.aus_gesamtvorschlag(netz_stromstaffel.gesamtvorschlag(n, ad))
    liste = E.erstelle(n, ad, aend, "Staffelvorschlag")
    text = E.als_csv(liste, stand="17.11.2026")
    assert text.startswith("﻿") and "\r\n" in text
    zeilen = list(csv.reader(io.StringIO(text.lstrip("﻿")), delimiter=";"))
    assert zeilen[0][0] == "Einstellliste Schutzstufen" and zeilen[1] == ["Stand", "17.11.2026"]
    kopf = zeilen[5]
    assert "Begründung" in kopf and "Adresse Zeit" in kopf
    daten = zeilen[6:]
    assert len(daten) == len(liste.zeilen) and all(len(z) == len(kopf) for z in daten)
    # Dezimalkomma, kein Dezimalpunkt in Zahlenfeldern
    spalte = kopf.index("I prim. [A]")
    assert all("." not in z[spalte] and "," in z[spalte] for z in daten)
    # Ist-Liste: gleiche Spalten, Vorschlagsspalten leer
    ist = E.als_csv(E.erstelle(n, ad))
    assert "keiner" in ist
    print("CSV OK: BOM, Semikolon, Dezimalkomma.")


def test_adressen_nur_aus_herst():
    n = _netz()
    liste = E.erstelle(n)
    alle = {str(v.get("adr", "")) for v in konstanten_leitung.HERST.values()}
    for z in liste.zeilen:
        if z.typ == "leitung":
            assert z.adresse_strom in alle | {""} and z.adresse_zeit in alle | {""}
    assert E._adresse("leitung", None) == "" and E._adresse("leitung", "gibt_es_nicht") == ""
    assert E._adresse("unbekannt", "x") == ""
    print("Adressen OK: nur aus HERST, sonst leer.")


def test_adressen_der_i_stufen():
    """Prüfpunkt 1: I>-Stufen haben jetzt eine Adresse, soweit HERST sie kennt. Nichts wird geraten."""
    liste = E.erstelle(_netz())
    z = {(x.element, x.stufe): x for x in liste.zeilen}
    assert z[("T1", "I> OS")].adresse_strom == "Adr.2014" and z[("T1", "I> OS")].adresse_zeit == "Adr.2016"
    assert z[("T1", "I>> OS")].adresse_strom == "Adr.2011"            # unveraendert
    assert z[("L1", "Iph>")].adresse_strom.startswith("Iph> Adr.2620")
    assert z[("M1", "I> (50-1)")].adresse_strom == "Adr.1204" and z[("M1", "Ip")].adresse_strom == "Adr.1207"
    # nicht geraten: Trafo I> US (HERST kennt nur die OS-Adresse), 50-1 und 51 Zeit, Netzbetreiber
    assert z[("T1", "I> US")].adresse_strom == "" and z[("T2", "I> US")].adresse_strom == ""
    assert z[("M1", "I> (50-1)")].adresse_zeit == "" and z[("M1", "Ip")].adresse_zeit == ""
    assert z[("E1", "I> NB")].adresse_strom == "" and z[("E1", "I> NB")].adresse_zeit == ""
    assert sum(1 for x in liste.zeilen if x.adresse_strom) == 13       # vorher 7 von 16
    assert sum(1 for x in liste.zeilen if x.adresse_zeit) == 13
    # die I>-Stufen sind trotzdem keine Stromvorschlag-Stufen
    assert "I> OS" not in netz_adapter.STROM_PARAMETER["trafo"]
    print("I>-Adressen OK: 13 von 16 Stufen, nichts geraten.")


def test_fehlerfaelle():
    leer = E.erstelle(Netz())
    assert leer.zeilen == [] and E.als_csv(leer).startswith("﻿")
    n = _netz()
    liste = E.erstelle(n, None, {("X9", "I>>"): E.Aenderung(I_neu_A=1.0)}, "Staffelvorschlag")
    assert not liste.ok and "X9" in liste.meldungen[-1].text
    assert E.aus_gesamtvorschlag(None) == {} and E.aus_ringvorschlag("Unsinn") == {}
    assert E.erstelle(None).ok is False
    print("Fehlerfälle OK: nie eine Ausnahme.")


if __name__ == "__main__":
    test_ist_liste()
    test_sekundaer_und_faktor()
    test_staffelvorschlag()
    test_ringvorschlag()
    test_csv()
    test_adressen_nur_aus_herst()
    test_adressen_der_i_stufen()
    test_fehlerfaelle()
    print("\nAlle Prüfungen bestanden.")
