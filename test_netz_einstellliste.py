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
    """Prüfpunkt 1: alle I>-Stufen haben eine Adresse, geprüft am 17.11.2026 gegen die Handbücher."""
    liste = E.erstelle(_netz())
    z = {(x.element, x.stufe): x for x in liste.zeilen}
    assert z[("T1", "I> OS")].adresse_strom == "Adr.2014" and z[("T1", "I> OS")].adresse_zeit == "Adr.2016"
    assert z[("T1", "I>> OS")].adresse_strom == "Adr.2011"            # unveraendert
    assert z[("L1", "Iph>")].adresse_strom.startswith("Iph> Adr.2620")
    assert z[("M1", "I> (50-1)")].adresse_strom == "Adr.1204" and z[("M1", "Ip")].adresse_strom == "Adr.1207"
    # Trafo US: zweite Ueberstromfunktion (7UT613, U/AMZ-Phase 2)
    for t in ("T1", "T2"):
        assert z[(t, "I> US")].adresse_strom.startswith("Adr.2114")
        assert z[(t, "I> US")].adresse_zeit.startswith("Adr.2116")
        assert z[(t, "I>> US")].adresse_strom.startswith("Adr.2111")
        assert z[(t, "I>> US")].adresse_zeit.startswith("Adr.2113")
    # Motor: 50-1 Zeit 1205, 51 Zeitfaktor 1208 (IEC) bzw. 1209 (ANSI), 50-2 Zeit 1203
    assert z[("M1", "I> (50-1)")].adresse_zeit == "Adr.1205"
    assert z[("M1", "Ip")].adresse_zeit.startswith("Adr.1208")
    assert z[("M1", "I>> (50-2)")].adresse_zeit == "Adr.1203"
    # bewusst leer: der Netzbetreiber-Schutz ist kein Geraet im Netz
    assert z[("E1", "I> NB")].adresse_strom == "" and z[("E1", "I> NB")].adresse_zeit == ""
    n_strom = sum(1 for x in liste.zeilen if x.adresse_strom)
    n_zeit = sum(1 for x in liste.zeilen if x.adresse_zeit)
    assert n_strom == len(liste.zeilen) - 1 and n_zeit == len(liste.zeilen) - 1
    # die I>-Stufen sind trotzdem keine Stromvorschlag-Stufen
    assert "I> OS" not in netz_adapter.STROM_PARAMETER["trafo"]
    assert "I> US" not in netz_adapter.STROM_PARAMETER["trafo"]
    print(f"I>-Adressen OK: {n_strom} von {len(liste.zeilen)} Stufen, nur der Netzbetreiber bleibt leer.")


def test_adresse_nach_nennstrom():
    """7UT613: 1 A -> Adr., 5 A -> Adr. + 1, unbekannt -> beide. Nur Trafo-Ansprechwerte, Zeiten nie."""
    n = _netz()
    z = {(x.element, x.stufe): x for x in E.erstelle(n).zeilen}
    assert z[("T1", "I>> OS")].adresse_strom == "Adr.2011"                       # 1 A: unveraendert
    p = dict(n.elemente["T1"].p)
    p.update(CT_OS_Sek=5, CT_US_Sek=5)
    n.parameter_setzen("T1", p)
    z = {(x.element, x.stufe): x for x in E.erstelle(n).zeilen}
    assert z[("T1", "I>> OS")].adresse_strom == "Adr.2012" and z[("T1", "I> OS")].adresse_strom == "Adr.2015"
    assert z[("T1", "I>> US")].adresse_strom.startswith("Adr.2112")
    assert z[("T1", "I> US")].adresse_strom.startswith("Adr.2115")
    assert z[("T1", "I> OS")].adresse_zeit == "Adr.2016"                         # Zeit-Adresse bleibt
    assert z[("T2", "I>> OS")].adresse_strom == "Adr.2011"                       # anderes Element: 1 A
    p = dict(n.elemente["T1"].p)
    p["CT_OS_Sek"] = 2                                   # weder 1 A noch 5 A (ohne Angabe liefert der Adapter keine Stufen)
    n.parameter_setzen("T1", p)
    z = {(x.element, x.stufe): x for x in E.erstelle(n).zeilen}
    assert z[("T1", "I>> OS")].adresse_strom == "Adr.2011 (1 A) / 2012 (5 A)"     # ungewoehnlich: beide
    assert z[("T1", "I>> US")].adresse_strom.startswith("Adr.2112")              # US-Seite weiter 5 A
    # kein Eingriff bei anderen Geraeten
    assert z[("L1", "Iph>")].adresse_strom.startswith("Iph> Adr.2620")
    assert z[("M1", "I> (50-1)")].adresse_strom == "Adr.1204"
    # Hilfsfunktion direkt, auch mit Muell
    assert E._strom_adresse_nach_nennstrom("trafo", "Adr.2014", "x") == "Adr.2014 (1 A) / 2015 (5 A)"
    assert E._strom_adresse_nach_nennstrom("trafo", "", 5.0) == ""
    assert E._strom_adresse_nach_nennstrom("motor", "Adr.1204", 5.0) == "Adr.1204"
    print("Nennstrom-Umschaltung OK.")


def test_hinweis_phase_2():
    liste = E.erstelle(_netz())
    for z in liste.zeilen:
        if z.typ == "trafo" and z.stufe.endswith("US"):
            assert "U/AMZ-Phase 2" in z.hinweis and "430" in z.hinweis
        else:
            assert z.hinweis == ""
    tab = E.als_tabelle(liste)
    assert all("Hinweis" in r for r in tab) and any(r["Hinweis"] for r in tab)
    assert "Hinweis" in E.als_csv(liste).split("\r\n")[4]                       # Spaltenkopf
    print("Hinweis Phase 2 OK.")


def test_hinweis_not_umz():
    n = _netz()
    _p = dict(n.elemente["L1"].p)
    assert all(z.hinweis == "" for z in E.erstelle(n).zeilen if z.typ == "leitung")
    n.parameter_setzen("L1", {**_p, "uebs_betriebsart": "Ein: bei U-Ausfall"})
    zl = [z for z in E.erstelle(n).zeilen if z.typ == "leitung" and z.element == "L1"]
    assert zl and all("Not-UMZ nur bei Spannungsausfall" in z.hinweis for z in zl)
    n.parameter_setzen("L1", {**_p, "uebs_betriebsart": "Aus"})
    assert all("ausgeschaltet" in z.hinweis for z in E.erstelle(n).zeilen if z.element == "L1")
    print("Hinweis Not-UMZ OK.")


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
    test_adresse_nach_nennstrom()
    test_hinweis_phase_2()
    test_hinweis_not_umz()
    test_fehlerfaelle()
    print("\nAlle Prüfungen bestanden.")
