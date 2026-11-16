"""
test_tab_netz.py - Oberflaechentests fuer den Netz-Tab (tab_netz.py)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Ausfuehren mit:  python test_tab_netz.py   (oder: pytest test_tab_netz.py)

Wie test_app.py ueber AppTest (ohne Browser). Die meisten Tests rendern nur
den Netz-Tab (schnell). Ein Test laeuft durch die ganze App und prueft die
Uebernahme eines echten Parametersatzes aus dem Trafo-Tab.

Prueft:
1. Leerstart: genau ein Hinweis, keine Tabellen, keine Ausnahmen.
2. Beispielnetz laden: Einlinienbild, vier Tabellen, 16 Schutzstufen.
3. Baumeingabe: Knoten und Element anlegen, Fehleingaben werden abgewiesen.
4. Bearbeiten: Netzform, Schalten, Entfernen.
5. Uebernahme aus dem Trafo-Tab in der vollstaendigen App.
6. Staffelung: 7 Paare mit Ampel wie im Modultest, Sollabstand wirkt, Pfade sichtbar.
8. Ring: Beispielring laden, Lagentabelle, Ringvorschlag und Uebernahme.
7. Staffelvorschlag (erst Strom, dann Zeit): Tabellen, Gegenpruefungen, Uebernahme ins
   Modell, danach ist die Staffelpruefung bis auf den Netzbetreiber (gelb) gruen.
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

ORDNER = Path(__file__).parent
NUR_NETZ = f"import sys\nsys.path.insert(0, {str(ORDNER)!r})\nimport tab_netz\ntab_netz.show()\n"


def _start() -> AppTest:
    at = AppTest.from_string(NUR_NETZ, default_timeout=60)
    at.run()
    _keine_ausnahme(at)
    return at


def _keine_ausnahme(at):
    assert len(at.exception) == 0, "; ".join(str(e.value)[:200] for e in at.exception)


def _klick(at, key):
    at.button(key=key).click().run()
    _keine_ausnahme(at)


def _absenden(at, label):
    [b for b in at.button if b.label == label][0].click().run()
    _keine_ausnahme(at)


def _texte(liste) -> str:
    return " | ".join(str(x.value) for x in liste)


def _beispiel() -> AppTest:
    at = _start()
    _klick(at, "netz_btn_beispiel")
    return at


# ── 1. Leerstart ─────────────────────────────────────────────────────────────
def test_leerstart():
    at = _start()
    assert len(at.info) == 1 and len(at.dataframe) == 0 and len(at.error) == 0
    assert len(at.expander) == 0       # Voraussetzung fuer die unveraenderte Inventur in test_app.py
    print("Leerstart OK: 1 Hinweis, keine Tabellen, keine Expander.")


# ── 2. Beispielnetz ──────────────────────────────────────────────────────────
def test_beispielnetz():
    at = _beispiel()
    netz = at.session_state["netz_modell"]
    assert sorted(netz.elemente) == ["E1", "L1", "L2", "M1", "T1", "T2"]
    assert "Beispielnetz" in _texte(at.success)
    assert len(at.info) == 0 and len(at.error) == 0 and len(at.warning) == 0
    assert len(at.dataframe) == 4                         # Knoten, Elemente, Schutzstufen, Staffelung
    assert len(at.dataframe[2].value) == 16               # 16 Schutzstufen wie im Adaptertest
    assert any(c.type == "graphviz_chart" for c in at.main.children.values()) or \
        "graphviz_chart" in str(at._tree)
    print("Beispielnetz OK: Einlinienbild, 4 Tabellen, 16 Schutzstufen.")


# ── 3. Baumeingabe ───────────────────────────────────────────────────────────
def test_knoten_und_element_anlegen():
    at = _beispiel()
    at.text_input(key="netz_k_id").set_value("K6")
    at.text_input(key="netz_k_name").set_value("Halle 3")
    at.number_input(key="netz_k_un").set_value(10.0)
    _absenden(at, "➕ Knoten anlegen")
    netz = at.session_state["netz_modell"]
    assert "K6" in netz.knoten and netz.knoten["K6"].sternpunkt == "isoliert"
    assert "K6 ist mit keinem Element" in _texte(at.warning)

    # Doppelte ID wird abgewiesen, das Netz bleibt unveraendert
    at.text_input(key="netz_k_id").set_value("K6")
    at.number_input(key="netz_k_un").set_value(10.0)
    _absenden(at, "➕ Knoten anlegen")
    assert "bereits vergeben" in _texte(at.error)
    # Fehlende Spannung wird abgewiesen
    at.text_input(key="netz_k_id").set_value("K7")
    _absenden(at, "➕ Knoten anlegen")
    assert "Wert fehlt" in _texte(at.error)
    assert sorted(at.session_state["netz_modell"].knoten) == ["K1", "K2", "K3", "K4", "K5", "K6"]

    # Leitung K4 -> K6 ohne Tab-Daten: Element entsteht, Adapter meldet fehlende Parameter
    at.text_input(key="netz_e_id").set_value("L3")
    at.selectbox(key="netz_e_typ").set_value("leitung")
    at.selectbox(key="netz_e_von").set_value("K4")
    at.selectbox(key="netz_e_nach").set_value("K6")
    _absenden(at, "➕ Element anlegen")
    netz = at.session_state["netz_modell"]
    assert (netz.elemente["L3"].von, netz.elemente["L3"].nach) == ("K4", "K6")
    assert "noch keine Grunddaten" in _texte(at.success)
    assert "L3: Es fehlen" in _texte(at.warning)

    # Leitung zwischen verschiedenen Spannungen: Topologiefehler, keine Schutzstufen
    at.text_input(key="netz_e_id").set_value("L4")
    at.selectbox(key="netz_e_typ").set_value("leitung")
    at.selectbox(key="netz_e_von").set_value("K6")
    at.selectbox(key="netz_e_nach").set_value("K5")
    _absenden(at, "➕ Element anlegen")
    assert "nur über einen Trafo" in _texte(at.error)
    assert len(at.dataframe) == 2                         # Schutzstufen-Tabelle entfaellt
    print("Baumeingabe OK: Anlegen, Fehleingaben abgewiesen, Topologiefehler angezeigt.")


# ── 4. Bearbeiten ────────────────────────────────────────────────────────────
def test_bearbeiten():
    at = _beispiel()
    at.radio[0].set_value("ring").run()
    _keine_ausnahme(at)
    assert at.session_state["netz_modell"].netzform == "ring"
    assert "keine Masche" in _texte(at.error)
    at.radio[0].set_value("strahl").run()

    at.selectbox(key="netz_b_element").set_value("L2")
    _klick(at, "netz_b_schalten")
    assert at.session_state["netz_modell"].elemente["L2"].zustand == "aus"
    assert "nicht versorgt: K4, K5" in _texte(at.warning)

    at.selectbox(key="netz_b_knoten").set_value("K5")
    _klick(at, "netz_b_entf_knoten")
    assert "noch verwendet" in _texte(at.error)
    at.selectbox(key="netz_b_element").set_value("T2")
    _klick(at, "netz_b_entf_element")
    at.selectbox(key="netz_b_knoten").set_value("K5")
    _klick(at, "netz_b_entf_knoten")
    assert "K5" not in at.session_state["netz_modell"].knoten

    _klick(at, "netz_btn_neu")
    assert len(at.info) == 1 and not at.session_state["netz_modell"].knoten
    print("Bearbeiten OK: Netzform, Schalten, Entfernen, neues Netz.")


# ── 5. Uebernahme aus dem Trafo-Tab (ganze App) ──────────────────────────────
def test_uebernahme_aus_trafo_tab():
    import test_app
    at = AppTest.from_file(str(ORDNER / "app.py"), default_timeout=240)
    at.run()
    test_app._fill_grunddaten(at)                      # fuellt u. a. den Trafo-Tab (16 MVA)
    _keine_ausnahme(at)
    assert at.session_state["netz_p_trafo"]["Sn_MVA"] == 16.0
    _klick(at, "netz_btn_beispiel")
    # Erst waehlen und neu zeichnen: der Knopf ist fuer die vorgewaehlte Einspeisung deaktiviert
    at.selectbox(key="netz_b_element").set_value("T2").run()
    _klick(at, "netz_b_uebernehmen")
    t2 = at.session_state["netz_modell"].elemente["T2"]
    assert t2.p["Sn_MVA"] == 16.0
    # Die Tab-Spannungen (110/10 kV) widersprechen den Knoten von T2 (10/0,4 kV):
    # Warnung, gerechnet wird mit den Knoten
    assert "T2: UN_OS_kV = 110 kV" in _texte(at.warning)
    assert "Parameter von T2" in _texte(at.success)
    print("Übernahme OK: Parametersatz aus dem Trafo-Tab im Netz, Knoten bleiben die Wahrheit.")


# ── 6. Staffelung ────────────────────────────────────────────────────────────
def test_staffelung():
    import konstanten_netz as KN
    at = _beispiel()
    df = at.dataframe[3].value
    assert len(df) == 7 and list(df["Ampel"]).count("🔴") == 6 and list(df["Ampel"]).count("🟢") == 1
    assert "M1 → L1 → T1 (US) → T1 (OS) → E1" in _texte(at.caption)
    assert at.number_input(key="netz_dt_soll").value == KN.dt_Staffel_soll
    # Sollabstand hochsetzen: das einzige gruene Paar (0,7 s) wird gelb, der Mindestwert bleibt
    at.number_input(key="netz_dt_soll").set_value(0.8).run()
    _keine_ausnahme(at)
    df = at.dataframe[3].value
    assert list(df["Ampel"]).count("🟡") == 1 and list(df["Ampel"]).count("🔴") == 6
    # Ohne Schutzstufen (alle Elemente ohne Parameter) kein Absturz, kein Staffel-Dataframe
    at.selectbox(key="netz_b_element").set_value("E1")
    _klick(at, "netz_b_entf_element")
    _keine_ausnahme(at)
    assert "keine Einspeisung" in _texte(at.error).lower() or len(at.error) >= 1
    print("Staffelung OK: 7 Paare, Ampel wie im Modultest, Sollabstand wirkt.")


# ── 7. Staffelvorschlag (erst Strom, dann Zeit) ──────────────────────────────
def test_staffelvorschlag():
    at = _beispiel()
    assert len(at.dataframe) == 4 and len(at.expander) == 0   # ohne Schalter kein Vorschlag
    at.toggle(key="netz_vorschlag_an").set_value(True).run()
    _keine_ausnahme(at)
    # Knoten, Elemente, Schutzstufen, Staffelung, Aenderungsliste + Details (Strom, Zeit, Gegenpruefung)
    assert len(at.dataframe) == 8 and len(at.expander) == 1
    liste = at.dataframe[4].value
    assert len(liste) == 11 and list(liste["Größe"]).count("Ansprechwert") == 3   # 3 Stroeme, 8 Zeiten
    z = liste[(liste["Element"] == "L2") & (liste["Größe"] == "Ansprechwert")].iloc[0]
    assert (z["bisher"], z["neu"]) == ("600 A (2,00 × IN)", "1680 A (5,60 × IN)")
    assert z["Warum"] == "1,2 × Ik max hinter T2 (OS)"
    z = liste[(liste["Element"] == "T1") & (liste["Stufe"] == "I> OS")].iloc[0]
    assert (z["bisher"], z["neu"]) == ("0,50 s", "1,00 s") and z["Warum"].startswith("0,30 s über T1 (US)")
    strom = at.dataframe[5].value
    assert len(strom) == 7 and list(strom["Änderung"]).count("✏️") == 3
    z = strom[(strom["Element"] == "T1") & (strom["Stufe"] == "I>> US")].iloc[0]
    assert z["Status"] == "nicht wirksam" and z["Änderung"] == ""
    df = at.dataframe[6].value
    assert len(df) == 16 and list(df["Änderung"]).count("✏️") == 8
    assert len(at.dataframe[7].value) == 11                  # Stromstaffel und Empfindlichkeit
    assert "Stromstaffelung nicht wirksam" in _texte(at.caption)
    assert "Motor-Tab-Fenster" not in _texte(at.warning)
    assert "passt nicht unter den Schutz des Netzbetreibers" in _texte(at.warning)
    assert "Ergebnis mit diesen Werten" in _texte(at.markdown)
    _klick(at, "netz_vorschlag_uebernehmen")
    assert "3 Ansprechwerte und 8 Zeiten in 4 Elementen" in _texte(at.success)
    netz = at.session_state["netz_modell"]
    assert netz.elemente["L2"].p["iph_hh"] == 5.6 and netz.elemente["L1"].p["iph_hh"] == 4.82
    assert netz.elemente["T1"].p["f_I_Ph_HH_OS"] == 12.38
    assert "f_I_Ph_HH_OS" not in netz.elemente["T2"].p      # unveraendert, nichts festgeschrieben
    assert netz.elemente["T1"].p["t_I_Ph"] == 1.0 and netz.elemente["T1"].p["t_I_Ph_US"] == 0.7
    assert netz.elemente["T2"].p["t_I_Ph_US"] == 0.5        # US-Endpunkt explizit festgehalten
    staffel = at.dataframe[3].value
    assert list(staffel["Ampel"]).count("🟢") == 6 and list(staffel["Ampel"]).count("🟡") == 1
    # Der Vorschlag ist jetzt deckungsgleich mit dem Netz: keine Aenderungsliste mehr
    assert "Keine Änderung nötig" in _texte(at.caption) and len(at.dataframe) == 7
    print("Staffelvorschlag OK: Änderungsliste, Details, Übernahme, danach 6 grün und der Netzbetreiber gelb.")


# ── 8. Ring ──────────────────────────────────────────────────────────────────
def test_ring():
    at = _start()
    _klick(at, "netz_btn_beispiel_ring")
    assert at.session_state["netz_modell"].netzform == "ring"
    # Knoten, Elemente, Schutzstufen, Staffelung, Ringlagen (ohne Schalter)
    assert len(at.dataframe) == 5
    lagen = at.dataframe[4].value
    assert sorted(lagen["Trennstelle"].str.replace(" (aktuell)", "", regex=False)) == ["K34", "L1", "L2"]
    assert list(lagen["Trennstelle"]).count("K34 (aktuell)") == 1
    assert set(lagen["Ampel"]) == {"🔴"}
    assert "Im Ring gilt dieser Vorschlag nur für die aktuelle Trennstellenlage" in _texte(at.caption)
    # Ringvorschlag: Aenderungsliste, Ergebnis je Lage, Details
    at.toggle(key="netz_ring_vorschlag_an").set_value(True).run()
    _keine_ausnahme(at)
    assert len(at.dataframe) == 8 and len(at.expander) == 1
    liste = at.dataframe[5].value
    assert len(liste) == 12
    z = liste[(liste["Element"] == "L2") & (liste["Größe"] == "Ansprechwert")].iloc[0]
    assert (z["bisher"], z["neu"]) == ("600 A (2,00 × IN)", "1680 A (5,60 × IN)")
    assert z["Warum"] == "Lage K34: 1,2 × Ik max hinter T2 (OS)"
    z = liste[(liste["Element"] == "T1") & (liste["Stufe"] == "I> OS")].iloc[0]
    assert (z["bisher"], z["neu"]) == ("0,50 s", "1,00 s")
    nachher = at.dataframe[6].value
    assert set(nachher["Ampel"]) == {"🟡"} and len(nachher) == 3
    assert len(at.dataframe[7].value) == 21                  # alle Werte in den Details
    _klick(at, "netz_ring_uebernehmen")
    assert "Ringvorschlag übernommen: 12 Werte in 4 Elementen" in _texte(at.success)
    netz = at.session_state["netz_modell"]
    assert netz.elemente["L1"].p["iph_hh"] == 5.6 and netz.elemente["L2"].p["iph_hh"] == 5.6
    assert netz.elemente["T1"].p["f_I_Ph_HH_US"] == 8.21
    assert set(at.dataframe[4].value["Ampel"]) == {"🟡"}                 # Ist-Zustand jetzt in allen Lagen gelb
    assert "Keine Änderung nötig, die Werte im Netz gelten bereits in allen Lagen" in _texte(at.caption)
    assert len([b for b in at.button if b.key == "netz_ring_uebernehmen"]) == 0
    # Einzelvorschlag im Ring: weiter nutzbar, gilt nur fuer die aktuelle Lage
    at.toggle(key="netz_vorschlag_an").set_value(True).run()
    _keine_ausnahme(at)
    assert len(at.expander) == 2
    # Strahlennetz zeigt keinen Ringblock
    at = _beispiel()
    assert len(at.dataframe) == 4
    print("Ring OK: Lagentabelle, Änderungsliste, Übernahme, danach alle Lagen gelb.")


# ── 9. Kurzschlussstroeme aus den Netzdaten ──────────────────────────────────
def test_kurzschluss_anzeige():
    at = _beispiel()
    vorher = at.session_state["netz_modell"].to_dict()
    staffel_vorher = at.dataframe[3].value.to_dict()
    at.toggle(key="netz_ik_an").set_value(True).run()
    _keine_ausnahme(at)
    # zwei Tabellen mehr (Vergleich, Impedanzen im Expander), dahinter alles wie bisher
    assert len(at.dataframe) == 6 and len(at.expander) == 1
    assert len(at.error) == 0 and len(at.warning) == 0
    df = at.dataframe[2].value.set_index("Knoten")
    assert df.loc["K2", "Ik″ max eingegeben [kA]"] == "10,00"
    assert df.loc["K2", "Ik″ max berechnet [kA]"] == "10,22" and df.loc["K2", "Abw. max"] == "+2,2 %"
    assert df.loc["K4", "Ik min berechnet [kA]"] == "5,90"
    assert df.loc["K3", "Ik″ max mit Motoren [kA]"] == "10,10"
    assert df.loc["K5", "Ik min eingegeben [kA]"] == "–"
    assert df.loc["K5", "Staffelung rechnet mit"] == "berechnet: Ik min"
    assert set(df.drop("K5")["Staffelung rechnet mit"]) == {"eingegeben"}
    assert "K5 Ik min 24,58 kA" in _texte(at.caption)
    assert len(at.dataframe[3].value) == 6                           # Impedanzen: E1, L1, L2, M1, T1, T2
    # Das Modell bleibt auf den eingegebenen Werten, die Zeitstaffelung aendert sich nicht
    assert at.session_state["netz_modell"].to_dict() == vorher
    assert at.dataframe[5].value.to_dict() == staffel_vorher
    # Vorschlag mit eingeschalteter Rechnung: Uebernahme schreibt ins Modell, Ik bleibt
    at.toggle(key="netz_vorschlag_an").set_value(True).run()
    _keine_ausnahme(at)
    _klick(at, "netz_vorschlag_uebernehmen")
    netz = at.session_state["netz_modell"]
    assert "Staffelvorschlag übernommen" in _texte(at.success)
    assert netz.to_dict() != vorher and netz.knoten["K5"].Ik_min_kA is None
    assert [k.Ik_max_kA for k in netz.knoten.values()] == [15.7, 10.0, 9.1, 7.9, 35.0]
    print("Kurzschluss-Anzeige OK: eingegeben, berechnet, Abweichung, Modell unverändert.")


def test_kurzschluss_ring():
    at = _start()
    _klick(at, "netz_btn_beispiel_ring")
    at.toggle(key="netz_ik_an").set_value(True).run()
    _keine_ausnahme(at)
    # Vergleich, Lagen, Impedanzen zusaetzlich zu den fuenf Tabellen des Rings
    assert len(at.dataframe) == 8 and len(at.expander) == 1
    lagen = at.dataframe[3].value.set_index("Schaltzustand")
    assert list(lagen.index)[1:] == ["K34 offen", "L1 offen", "L2 offen", "Ring geschlossen"]
    assert list(lagen.columns) == ["K3", "K4", "K5"]                 # K1 und K2 aendern sich nicht
    assert lagen.iloc[0]["K4"] == "7,90 / 5,80"                      # eingegeben
    assert lagen.loc["L2 offen", "K4"] == "9,27 / 6,95"
    assert lagen.loc["L1 offen", "K3"] == lagen.loc["L1 offen", "K4"] == "8,00 / 5,90"
    warn = _texte(at.warning)
    assert "K4 Ik max in Lage „L2 offen“" in warn and "K3 Ik max in Lage „L1 offen“" in warn
    assert "rechnet weiter mit den eingegebenen Werten" in warn
    # Ringvorschlag mit eingeschalteter Rechnung laeuft und schreibt ins Modell
    at.toggle(key="netz_ring_vorschlag_an").set_value(True).run()
    _keine_ausnahme(at)
    _klick(at, "netz_ring_uebernehmen")
    netz = at.session_state["netz_modell"]
    assert "Ringvorschlag übernommen" in _texte(at.success)
    assert netz.elemente["L1"].p["iph_hh"] == 5.6 and netz.knoten["K5"].Ik_min_kA is None
    print("Kurzschluss-Ring OK: Werte je Lage, Warnung zu K3 und K4, Übernahme ins Modell.")



# ── 10. Staffeldiagramm ──────────────────────────────────────────────────────
def test_staffeldiagramm():
    import json
    at = _beispiel()
    diagramme = at.get("vega_lite_chart")
    assert len(diagramme) == 1 and len(at.dataframe) == 4            # Diagramm zaehlt nicht als Tabelle
    wahl = at.selectbox(key="netz_diag_pfad")
    assert len(wahl.options) == 2 and wahl.options[0] == "M1 → L1 → T1 (US) → T1 (OS) → E1"
    spec = json.loads(diagramme[0].proto.spec)
    assert {z["Schutzort"] for z in spec["layer"][1]["data"]["values"]} == {"M1", "L1", "T1 (US)", "T1 (OS)", "E1"}
    # Zweiter Pfad, dann Vorschlag: das zweite Diagramm zeigt denselben Pfad mit den neuen Zeiten
    wahl.set_value(1).run()
    _keine_ausnahme(at)
    at.toggle(key="netz_vorschlag_an").set_value(True).run()
    _keine_ausnahme(at)
    diagramme = at.get("vega_lite_chart")
    assert len(diagramme) == 2
    ist, neu = (json.loads(d.proto.spec)["layer"][1]["data"]["values"] for d in diagramme)
    assert {z["Schutzort"] for z in ist} == {z["Schutzort"] for z in neu}
    assert "T2 (US)" in {z["Schutzort"] for z in neu}

    def zeit(werte, ort, stufe):
        return [z["t_s"] for z in werte if z["Schutzort"] == ort and z["Stufe"] == stufe][-1]
    assert zeit(neu, "L2", "Iph>") > zeit(ist, "L2", "Iph>") == 0.5
    assert "Staffeldiagramm mit dem Vorschlag" in " ".join(str(m.value) for m in at.markdown)
    # Ring-Beispiel: Diagramm der aktuellen Lage
    at = _start()
    _klick(at, "netz_btn_beispiel_ring")
    assert len(at.get("vega_lite_chart")) == 1 and len(at.dataframe) == 5
    # Leeres Netz: kein Diagramm
    assert len(_start().get("vega_lite_chart")) == 0
    print("Staffeldiagramm OK: Ist-Zustand, Pfadauswahl, Vorschlag im selben Pfad.")


if __name__ == "__main__":
    test_leerstart()
    test_beispielnetz()
    test_knoten_und_element_anlegen()
    test_bearbeiten()
    test_uebernahme_aus_trafo_tab()
    test_staffelung()
    test_staffelvorschlag()
    test_ring()
    test_kurzschluss_anzeige()
    test_kurzschluss_ring()
    test_staffeldiagramm()
    print("\nAlle Prüfungen bestanden.")
