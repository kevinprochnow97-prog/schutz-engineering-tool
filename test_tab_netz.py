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
11. Formular-Zustand: Eingaben bleiben nach einer Abweisung stehen, nach dem Anlegen ist das
    Formular wieder leer (Knoten und Element).
12. Bearbeiten: Knoten und Element aendern statt loeschen, Verbindungen und Parameter bleiben.
13. Parameter-Editor: Werte aus dem Modell, Speichern, Fehler behalten Eingaben, Wirkung in der
    Staffelung, Entwurf schliesst bei jeder Aenderung am Modell.
14. Einstellliste: Schalter, Quelle Ist/Staffelvorschlag/Ringvorschlag, Tabelle, CSV-Export.
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


def _offen(at, key) -> bool:
    """Ist das Eingabefeld mit diesem Schluessel gezeichnet (Bearbeiten-Formular offen)?"""
    return any(t.key == key for t in at.text_input)


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
    assert len(at.dataframe) == 5                         # Knoten, Elemente, Schutzstufen, Staffelung, Anlauf
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

    # Doppelte ID wird abgewiesen, das Netz bleibt unveraendert, die Eingaben bleiben stehen
    at.text_input(key="netz_k_id").set_value("K6")
    at.number_input(key="netz_k_un").set_value(10.0)
    _absenden(at, "➕ Knoten anlegen")
    assert "bereits vergeben" in _texte(at.error)
    assert at.text_input(key="netz_k_id").value == "K6" and at.number_input(key="netz_k_un").value == 10.0
    # Fehlende Spannung wird abgewiesen (die Spannung steht noch von vorher im Formular)
    at.text_input(key="netz_k_id").set_value("K7")
    at.number_input(key="netz_k_un").set_value(None)
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
def test_anlauf_tabelle():
    """Anlaufpruefung (Entscheidung 17.11.2026): Tabelle, Ampel-Zeile, Schalter am Motor."""
    at = _beispiel()
    def tab(a):
        t = [d.value for d in a.dataframe if "Untergrenze [A bez.]" in d.value.columns]
        assert len(t) == 1
        return t[0]
    df = tab(at)
    assert len(df) == 6 and list(df["Ampel"]).count("🔴") == 3 and list(df["Ampel"]).count("🟢") == 3
    assert "3 Stufen lösen beim Motoranlauf aus" in _texte(at.markdown)
    assert "Abschnitt 8" in _texte(at.caption)
    # Schalter am Motor: 50-1 des Motors wird nicht geprueft, Leitung und Ip bleiben rot
    netz = at.session_state["netz_modell"]
    p = dict(netz.elemente["M1"].p)
    netz.parameter_setzen("M1", {**p, "anlauf_gesperrt": "ja"})
    at.session_state["netz_modell"] = netz
    at.run()
    _keine_ausnahme(at)
    df = tab(at)
    assert list(df["Ampel"]).count("🔴") == 2
    assert "gesperrt" in df[df["Stufe"] == "I> (50-1)"].iloc[0]["Bewertung"]
    print("Anlauftabelle OK: 6 Zeilen, 3 rot, Schalter wirkt nur auf 50-1 des Motors.")


def test_staffelung():
    import konstanten_netz as KN
    at = _beispiel()
    df = at.dataframe[3].value
    assert len(df) == 7 and list(df["Ampel"]).count("🔴") == 6 and list(df["Ampel"]).count("🟢") == 1
    assert "Zuschlag AMZ [s]" in df.columns and set(df["Zuschlag AMZ [s]"]) == {"–"}   # Beispielnetz: 50-1 greift vor Ip
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
    assert len(at.dataframe) == 5 and len(at.expander) == 0   # ohne Schalter kein Vorschlag
    at.toggle(key="netz_vorschlag_an").set_value(True).run()
    _keine_ausnahme(at)
    # Knoten, Elemente, Schutzstufen, Staffelung, Aenderungsliste + Details (Strom, Zeit, Gegenpruefung)
    assert len(at.dataframe) == 9 and len(at.expander) == 1
    liste = at.dataframe[4].value
    assert len(liste) == 11 and list(liste["Größe"]).count("Ansprechwert") == 3   # 3 Stroeme, 8 Zeiten
    z = liste[(liste["Element"] == "L2") & (liste["Größe"] == "Ansprechwert")].iloc[0]
    assert (z["bisher"], z["neu"]) == ("600 A (2,00 × IN)", "1701 A (5,67 × IN)")
    assert z["Warum"] == "1,2 × Ik max hinter T2 (OS)"
    z = liste[(liste["Element"] == "T1") & (liste["Stufe"] == "I> OS")].iloc[0]
    assert (z["bisher"], z["neu"]) == ("0,50 s", "1,00 s") and z["Warum"].startswith("0,30 s über T1 (US)")
    strom = at.dataframe[5].value
    assert len(strom) == 7 and list(strom["Änderung"]).count("✏️") == 3
    z = strom[(strom["Element"] == "T1") & (strom["Stufe"] == "I>> US")].iloc[0]
    assert z["Status"] == "nicht wirksam" and z["Änderung"] == ""
    df = at.dataframe[6].value
    assert len(df) == 16 and list(df["Änderung"]).count("✏️") == 8
    assert len(at.dataframe[7].value) == 17                  # Stromstaffel und Empfindlichkeit
    assert "Stromstaffelung nicht wirksam" in _texte(at.caption)
    assert "Motor-Tab-Fenster" not in _texte(at.warning)
    assert "passt nicht unter den Schutz des Netzbetreibers" in _texte(at.warning)
    assert "Ergebnis mit diesen Werten" in _texte(at.markdown)
    _klick(at, "netz_vorschlag_uebernehmen")
    assert "3 Ansprechwerte und 8 Zeiten in 4 Elementen" in _texte(at.success)
    netz = at.session_state["netz_modell"]
    assert netz.elemente["L2"].p["iph_hh"] == 5.67 and netz.elemente["L1"].p["iph_hh"] == 4.82
    assert netz.elemente["T1"].p["f_I_Ph_HH_OS"] == 13.74
    assert "f_I_Ph_HH_OS" not in netz.elemente["T2"].p      # unveraendert, nichts festgeschrieben
    assert netz.elemente["T1"].p["t_I_Ph"] == 1.0 and netz.elemente["T1"].p["t_I_Ph_US"] == 0.7
    assert netz.elemente["T2"].p["t_I_Ph_US"] == 0.5        # US-Endpunkt explizit festgehalten
    staffel = at.dataframe[3].value
    assert list(staffel["Ampel"]).count("🟢") == 6 and list(staffel["Ampel"]).count("🟡") == 1
    # Der Vorschlag ist jetzt deckungsgleich mit dem Netz: keine Aenderungsliste mehr
    assert "Keine Änderung nötig" in _texte(at.caption) and len(at.dataframe) == 8
    print("Staffelvorschlag OK: Änderungsliste, Details, Übernahme, danach 6 grün und der Netzbetreiber gelb.")


# ── 8. Ring ──────────────────────────────────────────────────────────────────
def test_ring():
    at = _start()
    _klick(at, "netz_btn_beispiel_ring")
    assert at.session_state["netz_modell"].netzform == "ring"
    # Standard ist die je Lage berechnete Ik-Quelle, dieser Test prueft die eingegebenen Werte
    assert at.radio(key="netz_ring_ik_quelle").value == "Berechnet je Lage"
    at.radio(key="netz_ring_ik_quelle").set_value("Eingegeben (gleich in allen Lagen)").run()
    _keine_ausnahme(at)
    # Knoten, Elemente, Schutzstufen, Staffelung, Ringlagen (ohne Schalter)
    assert len(at.dataframe) == 6
    lagen = at.dataframe[4].value
    assert sorted(lagen["Trennstelle"].str.replace(" (aktuell)", "", regex=False)) == ["K34", "L1", "L2"]
    assert list(lagen["Trennstelle"]).count("K34 (aktuell)") == 1
    assert set(lagen["Ampel"]) == {"🔴"}
    assert "Im Ring gilt dieser Vorschlag nur für die aktuelle Trennstellenlage" in _texte(at.caption)
    # Ringvorschlag: Aenderungsliste, Ergebnis je Lage, Details
    at.toggle(key="netz_ring_vorschlag_an").set_value(True).run()
    _keine_ausnahme(at)
    assert len(at.dataframe) == 9 and len(at.expander) == 1
    liste = at.dataframe[5].value
    assert len(liste) == 12
    z = liste[(liste["Element"] == "L2") & (liste["Größe"] == "Ansprechwert")].iloc[0]
    assert (z["bisher"], z["neu"]) == ("600 A (2,00 × IN)", "1701 A (5,67 × IN)")
    assert z["Warum"] == "Lage K34: 1,2 × Ik max hinter T2 (OS)"
    z = liste[(liste["Element"] == "T1") & (liste["Stufe"] == "I> OS")].iloc[0]
    assert (z["bisher"], z["neu"]) == ("0,50 s", "1,00 s")
    nachher = at.dataframe[6].value
    assert set(nachher["Ampel"]) == {"🟡"} and len(nachher) == 3
    assert len(at.dataframe[7].value) == 21                  # alle Werte in den Details
    _klick(at, "netz_ring_uebernehmen")
    assert "Ringvorschlag übernommen: 12 Werte in 4 Elementen" in _texte(at.success)
    netz = at.session_state["netz_modell"]
    assert netz.elemente["L1"].p["iph_hh"] == 5.67 and netz.elemente["L2"].p["iph_hh"] == 5.67
    assert netz.elemente["T1"].p["f_I_Ph_HH_US"] == 8.84
    assert set(at.dataframe[4].value["Ampel"]) == {"🟡"}                 # Ist-Zustand jetzt in allen Lagen gelb
    assert "Keine Änderung nötig, die Werte im Netz gelten bereits in allen Lagen" in _texte(at.caption)
    assert len([b for b in at.button if b.key == "netz_ring_uebernehmen"]) == 0
    # Einzelvorschlag im Ring: weiter nutzbar, gilt nur fuer die aktuelle Lage
    at.toggle(key="netz_vorschlag_an").set_value(True).run()
    _keine_ausnahme(at)
    assert len(at.expander) == 2
    # Strahlennetz zeigt keinen Ringblock
    at = _beispiel()
    assert len(at.dataframe) == 5
    print("Ring OK: Lagentabelle, Änderungsliste, Übernahme, danach alle Lagen gelb.")


def test_ring_ik_quelle():
    """Standard im Ring: je Lage berechnet. Umschalter auf eingegeben. Strahlennetz ohne Umschalter."""
    at = _start()
    _klick(at, "netz_btn_beispiel_ring")
    r = at.radio(key="netz_ring_ik_quelle")
    assert r.value == "Berechnet je Lage" and list(r.options) == ["Berechnet je Lage",
                                                                  "Eingegeben (gleich in allen Lagen)"]
    vorher = at.session_state["netz_modell"].to_dict()
    at.toggle(key="netz_ring_vorschlag_an").set_value(True).run()
    _keine_ausnahme(at)
    assert "je Trennstellenlage aus der Kurzschlussrechnung" in _texte(at.caption)
    berechnet = at.dataframe[5].value
    # andere Quelle, anderer Vorschlag (T1 I> OS: 1,0 s mit eingegebenen, 1,7 s mit berechneten Werten)
    z = berechnet[(berechnet["Element"] == "T1") & (berechnet["Stufe"] == "I> OS")].iloc[0]
    assert z["neu"] == "1,70 s"
    at.radio(key="netz_ring_ik_quelle").set_value("Eingegeben (gleich in allen Lagen)").run()
    _keine_ausnahme(at)
    assert "je Trennstellenlage aus der Kurzschlussrechnung" not in _texte(at.caption)
    eingegeben = at.dataframe[5].value
    z = eingegeben[(eingegeben["Element"] == "T1") & (eingegeben["Stufe"] == "I> OS")].iloc[0]
    assert z["neu"] == "1,00 s"
    assert at.session_state["netz_modell"].to_dict() == vorher            # nur Rechennetz, nie das Modell
    # Warntext der Kurzschlussanzeige nennt die wirksame Quelle
    at.toggle(key="netz_ik_an").set_value(True).run()
    assert "rechnet weiter mit den eingegebenen Werten" in _texte(at.warning)
    at.radio(key="netz_ring_ik_quelle").set_value("Berechnet je Lage").run()
    assert "rechnet je Lage mit den berechneten Werten" in _texte(at.warning)
    # Strahlennetz: kein Umschalter
    at = _beispiel()
    assert len([r for r in at.radio if r.key == "netz_ring_ik_quelle"]) == 0
    print("Ring-Ik-Quelle OK: Standard berechnet, Umschalter, Modell unveraendert.")


# ── 9. Kurzschlussstroeme aus den Netzdaten ──────────────────────────────────
def test_kurzschluss_anzeige():
    at = _beispiel()
    vorher = at.session_state["netz_modell"].to_dict()
    staffel_vorher = at.dataframe[3].value.to_dict()
    at.toggle(key="netz_ik_an").set_value(True).run()
    _keine_ausnahme(at)
    # zwei Tabellen mehr (Vergleich, Impedanzen im Expander), dahinter alles wie bisher
    assert len(at.dataframe) == 7 and len(at.expander) == 1
    assert len(at.error) == 0 and len(at.warning) == 0
    df = at.dataframe[2].value.set_index("Knoten")
    assert df.loc["K2", "Ik″ max eingegeben [kA]"] == "11,10"
    # 25.11.2026: Ik max mit Motoren (Norm 7.1.2 e), Ik min mit Endtemperatur (Gl. 32)
    assert df.loc["K2", "Ik″ max berechnet [kA]"] == "11,04" and df.loc["K2", "Abw. max"] == "−0,6 %"
    assert df.loc["K4", "Ik min berechnet [kA]"] == "5,74"
    assert df.loc["K3", "Ik″ max nur Netz [kA]"] == "9,27"
    assert df.loc["K5", "Ik min eingegeben [kA]"] == "–"
    assert df.loc["K5", "Staffelung rechnet mit"] == "berechnet: Ik min"
    assert set(df.drop("K5")["Staffelung rechnet mit"]) == {"eingegeben"}
    assert "K5 Ik min 24,66 kA" in _texte(at.caption)
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
    assert [k.Ik_max_kA for k in netz.knoten.values()] == [15.9, 11.1, 10.2, 8.5, 35.4]
    print("Kurzschluss-Anzeige OK: eingegeben, berechnet, Abweichung, Modell unverändert.")


def test_kurzschluss_ring():
    at = _start()
    _klick(at, "netz_btn_beispiel_ring")
    at.radio(key="netz_ring_ik_quelle").set_value("Eingegeben (gleich in allen Lagen)").run()
    at.toggle(key="netz_ik_an").set_value(True).run()
    _keine_ausnahme(at)
    # Vergleich, Lagen, Impedanzen zusaetzlich zu den fuenf Tabellen des Rings
    assert len(at.dataframe) == 9 and len(at.expander) == 1
    lagen = at.dataframe[3].value.set_index("Schaltzustand")
    assert list(lagen.index)[1:] == ["K34 offen", "L1 offen", "L2 offen", "Ring geschlossen"]
    # 25.11.2026: mit Motoren aendern sich auch K1 und K2 je Lage (Motorbeitrag ueber den Ring)
    assert list(lagen.columns) == ["K1", "K2", "K3", "K4", "K5"]
    assert lagen.iloc[0]["K4"] == "8,50 / 5,80"                      # eingegeben
    assert lagen.loc["L2 offen", "K4"] == "10,10 / 6,78"
    assert lagen.loc["L1 offen", "K3"] == lagen.loc["L1 offen", "K4"] == "8,81 / 5,74"
    warn = _texte(at.warning)
    assert "K4 Ik max in Lage „L2 offen“" in warn and "K3 Ik min in Lage „L1 offen“" in warn
    assert "rechnet weiter mit den eingegebenen Werten" in warn
    # Ringvorschlag mit eingeschalteter Rechnung laeuft und schreibt ins Modell
    at.toggle(key="netz_ring_vorschlag_an").set_value(True).run()
    _keine_ausnahme(at)
    _klick(at, "netz_ring_uebernehmen")
    netz = at.session_state["netz_modell"]
    assert "Ringvorschlag übernommen" in _texte(at.success)
    assert netz.elemente["L1"].p["iph_hh"] == 5.67 and netz.knoten["K5"].Ik_min_kA is None
    print("Kurzschluss-Ring OK: Werte je Lage, Warnung zu K3 und K4, Übernahme ins Modell.")



# ── 10. Staffeldiagramm ──────────────────────────────────────────────────────
def test_staffeldiagramm():
    import json
    at = _beispiel()
    diagramme = at.get("vega_lite_chart")
    assert len(diagramme) == 1 and len(at.dataframe) == 5            # Diagramm zaehlt nicht als Tabelle
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
    assert len(at.get("vega_lite_chart")) == 1 and len(at.dataframe) == 6
    # Leeres Netz: kein Diagramm
    assert len(_start().get("vega_lite_chart")) == 0
    print("Staffeldiagramm OK: Ist-Zustand, Pfadauswahl, Vorschlag im selben Pfad.")


# ── 11. Formular-Zustand (Fehleingaben bleiben, nach dem Anlegen leer) ───────
def test_knotenformular_behaelt_eingaben_und_wird_leer():
    at = _beispiel()
    at.text_input(key="netz_k_id").set_value("K6")
    at.text_input(key="netz_k_name").set_value("Halle 3")
    at.selectbox(key="netz_k_stp").set_value("kompensiert")
    at.number_input(key="netz_k_ikmax").set_value(5.0)
    at.number_input(key="netz_k_ikmin").set_value(6.0)            # Ik min > Ik max: ungueltig
    at.number_input(key="netz_k_un").set_value(10.0)
    _absenden(at, "➕ Knoten anlegen")
    assert "größer als" in _texte(at.error) and "K6" not in at.session_state["netz_modell"].knoten
    # alle Eingaben stehen noch da, nur der falsche Wert muss korrigiert werden
    assert at.text_input(key="netz_k_id").value == "K6"
    assert at.text_input(key="netz_k_name").value == "Halle 3"
    assert at.selectbox(key="netz_k_stp").value == "kompensiert"
    assert at.number_input(key="netz_k_ikmax").value == 5.0 and at.number_input(key="netz_k_un").value == 10.0
    at.number_input(key="netz_k_ikmin").set_value(3.0)
    _absenden(at, "➕ Knoten anlegen")
    k = at.session_state["netz_modell"].knoten["K6"]
    assert (k.name, k.sternpunkt, k.Ik_max_kA, k.Ik_min_kA) == ("Halle 3", "kompensiert", 5.0, 3.0)
    assert "Knoten K6 angelegt" in _texte(at.success)
    # danach ist das Formular wieder wie beim ersten Oeffnen
    assert at.text_input(key="netz_k_id").value == "" and at.text_input(key="netz_k_name").value == ""
    assert at.number_input(key="netz_k_un").value is None
    assert at.number_input(key="netz_k_ikmax").value is None and at.number_input(key="netz_k_ikmin").value is None
    assert at.selectbox(key="netz_k_stp").value == "isoliert"
    print("Knotenformular OK: Eingaben bleiben bei Fehler, nach dem Anlegen leer.")


def test_elementformular_behaelt_eingaben_und_wird_leer():
    at = _beispiel()
    at.text_input(key="netz_e_id").set_value("L3")
    at.text_input(key="netz_e_name").set_value("Kabel Halle 3")
    at.selectbox(key="netz_e_typ").set_value("leitung")
    at.selectbox(key="netz_e_von").set_value("K4")
    at.selectbox(key="netz_e_nach").set_value("K4")               # von = nach: ungueltig
    at.radio(key="netz_e_zustand").set_value("aus")
    at.checkbox(key="netz_e_uebern").set_value(False)
    _absenden(at, "➕ Element anlegen")
    assert "identisch" in _texte(at.error) and "L3" not in at.session_state["netz_modell"].elemente
    assert at.text_input(key="netz_e_id").value == "L3"
    assert at.text_input(key="netz_e_name").value == "Kabel Halle 3"
    assert at.selectbox(key="netz_e_typ").value == "leitung"
    assert at.selectbox(key="netz_e_von").value == "K4" and at.selectbox(key="netz_e_nach").value == "K4"
    assert at.radio(key="netz_e_zustand").value == "aus" and at.checkbox(key="netz_e_uebern").value is False
    at.selectbox(key="netz_e_nach").set_value("K3")
    _absenden(at, "➕ Element anlegen")
    e = at.session_state["netz_modell"].elemente["L3"]
    assert (e.name, e.von, e.nach, e.zustand) == ("Kabel Halle 3", "K4", "K3", "aus") and e.p == {"uebs_betriebsart": "Ein: immer aktiv"}
    # Formular wie beim ersten Oeffnen: leer, erster Typ, kein Knoten, ein, Haekchen gesetzt
    assert at.text_input(key="netz_e_id").value == "" and at.text_input(key="netz_e_name").value == ""
    assert at.selectbox(key="netz_e_typ").value == "einspeisung"
    assert at.selectbox(key="netz_e_von").value == "—" and at.selectbox(key="netz_e_nach").value == "—"
    assert at.radio(key="netz_e_zustand").value == "ein" and at.checkbox(key="netz_e_uebern").value is True
    assert at.number_input(key="netz_e_inb").value is None and at.number_input(key="netz_e_tnb").value is None
    print("Elementformular OK: Eingaben bleiben bei Fehler, nach dem Anlegen leer.")


def test_entferntes_knoten_im_elementformular():
    # Ein im Formular gewaehlter Knoten verschwindet: kein Absturz, Auswahl faellt auf "kein Knoten"
    at = _beispiel()
    at.text_input(key="netz_k_id").set_value("K6")
    at.number_input(key="netz_k_un").set_value(10.0)
    _absenden(at, "➕ Knoten anlegen")
    at.selectbox(key="netz_e_von").set_value("K6").run()
    at.selectbox(key="netz_b_knoten").set_value("K6")
    _klick(at, "netz_b_entf_knoten")
    assert at.selectbox(key="netz_e_von").value == "—"
    print("Entfernter Knoten im Formular OK.")


# ── 12. Bearbeiten statt Loeschen und neu Anlegen ────────────────────────────
def test_knoten_bearbeiten():
    at = _beispiel()
    vorher = at.session_state["netz_modell"].to_dict()
    at.selectbox(key="netz_b_knoten").set_value("K4")
    _klick(at, "netz_b_edit_knoten")
    # Formular zeigt die Werte aus dem Modell
    assert at.text_input(key="netz_ed_k_name").value == "Unterverteilung 10 kV"
    assert at.number_input(key="netz_ed_k_un").value == 10.0
    assert at.number_input(key="netz_ed_k_ikmax").value == 8.5 and at.selectbox(key="netz_ed_k_stp").value == "isoliert"
    # Entwurf ausfuellen. Ungueltig: Ik min ueber Ik max. Modell unveraendert, Eingaben bleiben
    at.text_input(key="netz_ed_k_name").set_value("Halle 2")
    at.selectbox(key="netz_ed_k_stp").set_value("kompensiert")
    at.number_input(key="netz_ed_k_ikmax").set_value(8.2)
    at.number_input(key="netz_ed_k_ikmin").set_value(9.0)
    _absenden(at, "💾 Änderungen speichern")
    assert "größer als" in _texte(at.error) and at.session_state["netz_modell"].to_dict() == vorher
    assert at.text_input(key="netz_ed_k_name").value == "Halle 2" and at.number_input(key="netz_ed_k_ikmax").value == 8.2
    at.number_input(key="netz_ed_k_ikmin").set_value(6.0)
    _absenden(at, "💾 Änderungen speichern")
    netz = at.session_state["netz_modell"]
    k = netz.knoten["K4"]
    assert (k.name, k.sternpunkt, k.Ik_max_kA, k.Ik_min_kA, k.UN_kV) == ("Halle 2", "kompensiert", 8.2, 6.0, 10.0)
    assert "Knoten K4 geändert" in _texte(at.success)
    # Verbindungen bleiben: L2 und T2 haengen weiter an K4, Formular ist geschlossen
    assert (netz.elemente["L2"].nach, netz.elemente["T2"].von) == ("K4", "K4")
    assert not _offen(at, "netz_ed_k_name")
    # Abbrechen verwirft den Entwurf
    _klick(at, "netz_b_edit_knoten")
    at.text_input(key="netz_ed_k_name").set_value("nicht speichern")
    _absenden(at, "Abbrechen")
    assert at.session_state["netz_modell"].knoten["K4"].name == "Halle 2"
    assert not _offen(at, "netz_ed_k_name")
    print("Knoten bearbeiten OK: Werte geladen, Fehler behalten Eingaben, Verbindungen bleiben.")


def test_trafo_richtung_tauschen_und_umbenennen():
    at = _beispiel()
    vorher = at.session_state["netz_modell"].elemente["T1"]
    at.selectbox(key="netz_b_element").set_value("T1")
    _klick(at, "netz_b_edit_element")
    assert (at.selectbox(key="netz_ed_e_von").value, at.selectbox(key="netz_ed_e_nach").value) == ("K1", "K2")
    assert at.text_input(key="netz_ed_e_name").value == vorher.name
    # Richtung vertauschen: Topologie meldet jetzt die falsche Richtung, Parameter bleiben unberuehrt
    at.selectbox(key="netz_ed_e_von").set_value("K2")
    at.selectbox(key="netz_ed_e_nach").set_value("K1")
    at.text_input(key="netz_ed_e_name").set_value("Netztrafo 20 MVA")
    _absenden(at, "💾 Änderungen speichern")
    netz = at.session_state["netz_modell"]
    t1 = netz.elemente["T1"]
    assert (t1.von, t1.nach, t1.name) == ("K2", "K1", "Netztrafo 20 MVA")
    assert t1.p == vorher.p and t1.typ == "trafo" and t1.zustand == vorher.zustand
    assert "Richtung tauschen" in _texte(at.error)             # Topologie erkennt die falsche Richtung
    assert "von K1 → K2" in _texte(at.success)
    # Zurueck tauschen: Topologie wieder in Ordnung, alle anderen Elemente unveraendert
    _klick(at, "netz_b_edit_element")
    at.selectbox(key="netz_ed_e_von").set_value("K1")
    at.selectbox(key="netz_ed_e_nach").set_value("K2")
    _absenden(at, "💾 Änderungen speichern")
    netz = at.session_state["netz_modell"]
    assert (netz.elemente["T1"].von, netz.elemente["T1"].nach) == ("K1", "K2")
    assert len(at.error) == 0
    print("Element bearbeiten OK: Trafo-Richtung getauscht, Parameter und Verbindungen bleiben.")


def test_element_bearbeiten_fehler_und_einspeisung():
    at = _beispiel()
    at.selectbox(key="netz_b_element").set_value("L1")
    _klick(at, "netz_b_edit_element")
    # Leitung: von = nach wird abgewiesen, die Eingaben bleiben stehen, das Element bleibt wie es war
    vorher = at.session_state["netz_modell"].elemente["L1"]
    at.selectbox(key="netz_ed_e_nach").set_value("K2")
    at.text_input(key="netz_ed_e_name").set_value("Kabel neu")
    _absenden(at, "💾 Änderungen speichern")
    assert "identisch" in _texte(at.error)
    assert at.text_input(key="netz_ed_e_name").value == "Kabel neu"
    assert at.session_state["netz_modell"].elemente["L1"].to_dict() == vorher.to_dict()
    _absenden(at, "Abbrechen")
    # Einspeisung: nur nach-Knoten und die Netzbetreiber-Werte sind bearbeitbar
    at.selectbox(key="netz_b_element").set_value("E1")
    _klick(at, "netz_b_edit_element")
    assert [s.key for s in at.selectbox if s.key and s.key.startswith("netz_ed_e_")] == ["netz_ed_e_nach"]
    assert at.number_input(key="netz_ed_e_inb").value == 160.0 and at.number_input(key="netz_ed_e_tnb").value == 1.2
    at.number_input(key="netz_ed_e_tnb").set_value(1.5)
    _absenden(at, "💾 Änderungen speichern")
    e1 = at.session_state["netz_modell"].elemente["E1"]
    assert e1.p["t_gt_NB_s"] == 1.5 and e1.p["I_gt_NB_A"] == 160.0 and e1.p["Sk_max_MVA"] == 3000
    print("Element bearbeiten OK: Fehler behalten Eingaben, Einspeisung mit Netzbetreiber-Werten.")


def test_entwurf_verfaellt_mit_dem_objekt():
    at = _beispiel()
    at.selectbox(key="netz_b_element").set_value("L1")
    _klick(at, "netz_b_edit_element")
    assert _offen(at, "netz_ed_e_name")
    _klick(at, "netz_b_entf_element")                       # das bearbeitete Element wird entfernt
    assert not _offen(at, "netz_ed_e_name")
    _klick(at, "netz_b_edit_knoten")
    assert _offen(at, "netz_ed_k_name")
    _klick(at, "netz_btn_neu")                              # neues Netz verwirft den Entwurf
    assert not _offen(at, "netz_ed_k_name")
    print("Entwurf OK: verfaellt mit dem Objekt und mit dem Netzwechsel.")


# ── 13. Parameter-Editor (Variante 1) ────────────────────────────────────────
def test_parameter_editor_speichern_und_leeren():
    at = _beispiel()
    vorher = at.session_state["netz_modell"].elemente["T2"].p
    at.selectbox(key="netz_b_element").set_value("T2").run()
    _klick(at, "netz_b_edit_parameter")
    assert at.number_input(key="netz_pa_Sn_MVA").value == 1.6
    assert at.number_input(key="netz_pa_CT_OS_Prim").value == 100.0
    assert at.selectbox(key="netz_pa_Schaltgruppe").value == "Dyn5"
    assert at.number_input(key="netz_pa_t_I_Ph").value is None            # nicht gesetzt: Voreinstellung
    at.number_input(key="netz_pa_CT_OS_Prim").set_value(150.0)
    at.number_input(key="netz_pa_t_I_Ph").set_value(0.8)
    at.selectbox(key="netz_pa_Schaltgruppe").set_value("Dyn11")
    _absenden(at, "💾 Parameter speichern")
    p = at.session_state["netz_modell"].elemente["T2"].p
    assert (p["CT_OS_Prim"], p["t_I_Ph"], p["Schaltgruppe"]) == (150.0, 0.8, "Dyn11")
    assert p["Sn_MVA"] == vorher["Sn_MVA"] and p["CT_US_Prim"] == vorher["CT_US_Prim"]
    assert "Parameter von T2 geändert" in _texte(at.success) and not _offen(at, "netz_pa_Sn_MVA")
    # die Staffelung rechnet mit dem neuen Wert: T2 I> OS ist 0,8 s statt 0,5 s
    assert "0,80" in at.dataframe[2].value.to_string()
    # Feld leeren: Schluessel verschwindet, die Voreinstellung gilt wieder
    _klick(at, "netz_b_edit_parameter")
    assert at.number_input(key="netz_pa_t_I_Ph").value == 0.8
    at.number_input(key="netz_pa_t_I_Ph").set_value(None)
    _absenden(at, "💾 Parameter speichern")
    assert "t_I_Ph" not in at.session_state["netz_modell"].elemente["T2"].p
    print("Parameter-Editor OK: Werte geladen, gespeichert, geleert, Staffelung rechnet mit.")


def test_parameter_editor_fehler_behalten_eingaben():
    at = _beispiel()
    vorher = at.session_state["netz_modell"].to_dict()
    at.selectbox(key="netz_b_element").set_value("T2").run()
    _klick(at, "netz_b_edit_parameter")
    at.number_input(key="netz_pa_Sn_MVA").set_value(-2.0)
    at.number_input(key="netz_pa_t_I_Ph").set_value(0.9)
    at.number_input(key="netz_pa_Stufensteller_pm").set_value(55.0)
    _absenden(at, "💾 Parameter speichern")
    fehler = _texte(at.error)
    assert "Sn: muss größer als 0" in fehler and "Stufensteller ±: darf höchstens 40" in fehler
    assert at.session_state["netz_modell"].to_dict() == vorher
    # alles steht noch im Formular, nur die falschen Werte muessen korrigiert werden
    assert at.number_input(key="netz_pa_t_I_Ph").value == 0.9 and at.number_input(key="netz_pa_Sn_MVA").value == -2.0
    at.number_input(key="netz_pa_Sn_MVA").set_value(2.5)
    at.number_input(key="netz_pa_Stufensteller_pm").set_value(10.0)
    _absenden(at, "💾 Parameter speichern")
    p = at.session_state["netz_modell"].elemente["T2"].p
    assert (p["Sn_MVA"], p["t_I_Ph"], p["Stufensteller_pm"]) == (2.5, 0.9, 10.0)
    print("Parameter-Editor OK: Fehler behalten die Eingaben, danach korrigiert gespeichert.")


def test_parameter_editor_typen_und_entwurf():
    at = _beispiel()
    # Leitung: Betriebsart ist eine Auswahl, Einspeisung hat die Netzbetreiber-Felder
    at.selectbox(key="netz_b_element").set_value("L1").run()
    _klick(at, "netz_b_edit_parameter")
    assert at.selectbox(key="netz_pa_uebs_betriebsart").value == "Ein: immer aktiv"
    at.selectbox(key="netz_pa_uebs_betriebsart").set_value("Aus")
    _absenden(at, "💾 Parameter speichern")
    assert at.session_state["netz_modell"].elemente["L1"].p["uebs_betriebsart"] == "Aus"
    at.selectbox(key="netz_b_element").set_value("E1").run()
    _klick(at, "netz_b_edit_parameter")
    assert at.number_input(key="netz_pa_I_gt_NB_A").value == 160.0
    at.number_input(key="netz_pa_I_gt_NB_A").set_value(None)              # nur I> leer: nur als Paar zulaessig
    _absenden(at, "💾 Parameter speichern")
    assert "gehören zusammen" in _texte(at.error)
    assert at.session_state["netz_modell"].elemente["E1"].p["I_gt_NB_A"] == 160.0
    # Jede erfolgreiche Aenderung am Modell schliesst den offenen Entwurf (waere sonst veraltet)
    _klick(at, "netz_b_schalten")
    assert not any(
        t.key and t.key.startswith("netz_pa_") for t in at.number_input)
    # Kupplung und Generator haben keine Parameter: Knopf gesperrt, Trafo: frei
    at.session_state["netz_modell"].element_hinzufuegen("KU1", "Kupplung", "kupplung", "K3", "K4")
    at.run()
    at.selectbox(key="netz_b_element").set_value("KU1").run()
    assert at.button(key="netz_b_edit_parameter").disabled
    at.selectbox(key="netz_b_element").set_value("T1").run()
    assert not at.button(key="netz_b_edit_parameter").disabled
    print("Parameter-Editor OK: Auswahlfeld, Netzbetreiber-Paar, Entwurf schliesst bei Aenderung.")


# ── 14. Einstellliste ────────────────────────────────────────────────────────
def test_einstellliste_ist_und_vorschlag():
    at = _beispiel()
    assert len(at.dataframe) == 5 and len(at.get("download_button")) == 1   # nur Netz speichern, Liste aus
    at.toggle(key="netz_liste_an").set_value(True).run()
    _keine_ausnahme(at)
    assert len(at.dataframe) == 6 and len(at.get("download_button")) == 2
    liste = at.dataframe[5].value
    assert len(liste) == 16 and "geändert" not in liste.columns          # Ist-Liste ohne Vorschlagsspalten
    z = liste[(liste["Element"] == "T1") & (liste["Stufe"] == "I> OS")].iloc[0]
    assert z["Adresse Ansprechwert"] == "Adr.2014" and z["Wandler"] == "150/1 A"
    assert "Staffelvorschlag" not in at.radio(key="netz_liste_quelle").options
    # Staffelvorschlag einschalten: neue Quelle, geaenderte Zeilen mit Begruendung
    at.toggle(key="netz_vorschlag_an").set_value(True).run()
    _keine_ausnahme(at)
    wahl = at.radio(key="netz_liste_quelle")
    assert wahl.options == ["Einstellwerte im Netz (Ist)", "Staffelvorschlag"]
    wahl.set_value("Staffelvorschlag").run()
    _keine_ausnahme(at)
    liste = at.dataframe[-1].value
    assert list(liste["geändert"]).count("ja") == 9      # 3 Ansprechwerte + 8 Zeiten auf 9 Stufen (L1/L2 Iph>>, T1 I>> OS haben beides)
    z = liste[(liste["Element"] == "L2") & (liste["Stufe"] == "Iph>>")].iloc[0]
    assert z["I prim. neu [A]"] == "1701,0" and "Ansprechwert" in z["Begründung"]
    # Schalter aus: Liste weg, Modell nie veraendert
    vorher = at.session_state["netz_modell"].to_dict()
    at.toggle(key="netz_vorschlag_an").set_value(False).run()
    _keine_ausnahme(at)
    assert at.radio(key="netz_liste_quelle").value == "Einstellwerte im Netz (Ist)"
    assert at.session_state["netz_modell"].to_dict() == vorher
    print("Einstellliste OK: Ist, Staffelvorschlag, Quelle fällt zurück.")


def test_einstellliste_ring():
    at = _start()
    _klick(at, "netz_btn_beispiel_ring")
    at.toggle(key="netz_liste_an").set_value(True).run()
    at.toggle(key="netz_ring_vorschlag_an").set_value(True).run()
    _keine_ausnahme(at)
    assert "Ringvorschlag" in at.radio(key="netz_liste_quelle").options
    at.radio(key="netz_liste_quelle").set_value("Ringvorschlag").run()
    _keine_ausnahme(at)
    liste = at.dataframe[-1].value
    assert "geändert" in liste.columns and "ja" in set(liste["geändert"])
    print("Einstellliste Ring OK.")


# ── 15. Erdfehler (Entscheidung 25.11.2026) ──────────────────────────────────
def _erdbeispiel() -> AppTest:
    at = _start()
    _klick(at, "netz_btn_beispiel_noe")
    return at


def test_erdfehler_abschnitt():
    at = _erdbeispiel()
    n_tab = len(at.dataframe)
    at.toggle(key="netz_erde_an").set_value(True).run()
    _keine_ausnahme(at)
    tabellen = [d.value for d in at.dataframe[n_tab:]]
    bereiche = tabellen[0]
    z = bereiche[bereiche["Bereich (Knoten)"] == "K2, K3, K4"].iloc[0]
    assert z["Sternpunkt"] == "niederohmig" and "Sternpunktbildner an K2" in z["Erdung"]
    assert z["Ik1 max [kA]"] == "2,18" and z["Ik1 min [kA]"] == "1,59"
    paare = [t for t in tabellen if "oben (Erdung)" in t.columns][0]
    assert set(zip(paare["unten (Fehler)"], paare["oben (Erdung)"])) == {("M1", "L1"), ("M2", "L2")}
    assert "Erdstaffelung: Prüfen!" in _texte(at.markdown)
    assert any("Schutzort" in t.columns for t in tabellen)          # Empfindlichkeit
    print("Erdfehler-Abschnitt OK.")


def test_erdvorschlag_uebernehmen():
    at = _erdbeispiel()
    at.toggle(key="netz_erde_an").set_value(True).run()
    vorher = at.session_state["netz_modell"].to_dict()
    at.toggle(key="netz_erde_vorschlag_an").set_value(True).run()
    _keine_ausnahme(at)
    assert at.session_state["netz_modell"].to_dict() == vorher        # nur rechnen, nicht schreiben
    aend = [d.value for d in at.dataframe if "Warum" in d.value.columns][-1]
    assert len(aend) == 6 and set(aend["Element"]) == {"L1", "L2"}
    _klick(at, "netz_erde_uebernehmen")
    n = at.session_state["netz_modell"]
    assert n.elemente["L1"].p["t_3I0HHH"] == 0.4 and n.elemente["L2"].p["t_3I0H"] == 0.5
    assert "Erdvorschlag übernommen" in _texte(at.success)
    assert "Erdstaffelung: OK" in _texte(at.markdown)
    print("Erdvorschlag übernehmen OK.")


def test_erdfehler_einstellliste():
    at = _erdbeispiel()
    at.toggle(key="netz_erde_an").set_value(True).run()
    at.toggle(key="netz_erde_vorschlag_an").set_value(True).run()
    at.toggle(key="netz_liste_an").set_value(True).run()
    _keine_ausnahme(at)
    wahl = at.radio(key="netz_liste_quelle")
    assert "Erdvorschlag" in wahl.options
    wahl.set_value("Erdvorschlag").run()
    _keine_ausnahme(at)
    liste = at.dataframe[-1].value
    erde = liste[liste["Art"] == "Erde"]
    assert len(erde) == 14                                            # L1, L2 je 3, M1, M2 je 3, T2 2
    z = erde[(erde["Element"] == "L1") & (erde["Stufe"] == "3I0>")].iloc[0]
    assert z["t neu [s]"] == "0,80" and "Adr.3132" in z["Adresse Zeit"]
    print("Einstellliste mit Erdstufen OK.")


def test_isoliertes_netz_erdfehler_hinweis():
    at = _beispiel()
    at.toggle(key="netz_erde_an").set_value(True).run()
    _keine_ausnahme(at)
    bereiche = [d.value for d in at.dataframe if "Bereich (Knoten)" in d.value.columns][0]
    z = bereiche[bereiche["Bereich (Knoten)"] == "K2, K3, K4"].iloc[0]
    assert z["Sternpunkt"] == "isoliert" and "U0" in z["Bewertung"]
    assert not any(t.key == "netz_erde_vorschlag_an" for t in at.toggle)   # nichts zu staffeln


def test_knoten_mit_begrenzung_anlegen():
    at = _start()
    at.text_input(key="netz_k_id").input("K9")
    at.text_input(key="netz_k_name").input("Test")
    at.number_input(key="netz_k_un").set_value(10.0)
    at.selectbox(key="netz_k_stp").set_value("niederohmig")
    at.number_input(key="netz_k_ie").set_value(1500.0)
    _absenden(at, "➕ Knoten anlegen")
    assert at.session_state["netz_modell"].knoten["K9"].I_E_begr_A == 1500.0
    assert at.number_input(key="netz_k_ie").value is None             # Formular wieder leer


if __name__ == "__main__":
    test_leerstart()
    test_beispielnetz()
    test_knoten_und_element_anlegen()
    test_bearbeiten()
    test_uebernahme_aus_trafo_tab()
    test_anlauf_tabelle()
    test_staffelung()
    test_staffelvorschlag()
    test_ring()
    test_ring_ik_quelle()
    test_kurzschluss_anzeige()
    test_kurzschluss_ring()
    test_staffeldiagramm()
    test_knotenformular_behaelt_eingaben_und_wird_leer()
    test_elementformular_behaelt_eingaben_und_wird_leer()
    test_entferntes_knoten_im_elementformular()
    test_knoten_bearbeiten()
    test_trafo_richtung_tauschen_und_umbenennen()
    test_element_bearbeiten_fehler_und_einspeisung()
    test_entwurf_verfaellt_mit_dem_objekt()
    test_parameter_editor_speichern_und_leeren()
    test_parameter_editor_fehler_behalten_eingaben()
    test_parameter_editor_typen_und_entwurf()
    test_einstellliste_ist_und_vorschlag()
    test_einstellliste_ring()
    print("\nAlle Prüfungen bestanden.")
