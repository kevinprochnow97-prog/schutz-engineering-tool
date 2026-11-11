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
    assert len(at.dataframe) == 4                           # ohne Schalter keine Vorschlagstabelle
    at.toggle(key="netz_vorschlag_an").set_value(True).run()
    _keine_ausnahme(at)
    # Knoten, Elemente, Schutzstufen, Staffelung, Strom, Zeit, Gegenpruefung Strom
    assert len(at.dataframe) == 7
    strom = at.dataframe[4].value
    assert len(strom) == 7 and list(strom["Änderung"]).count("✏️") == 3
    z = strom[(strom["Element"] == "L2") & (strom["Stufe"] == "Iph>>")].iloc[0]
    assert (z["I bisher [A]"], z["I Vorschlag [A]"], z["Faktor Vorschlag"]) == ("600", "1680", "5,60")
    z = strom[(strom["Element"] == "T1") & (strom["Stufe"] == "I>> US")].iloc[0]
    assert z["Status"] == "nicht wirksam" and z["Änderung"] == ""
    df = at.dataframe[5].value
    assert len(df) == 16 and list(df["Änderung"]).count("✏️") == 8
    zeile = df[(df["Element"] == "T1") & (df["Stufe"] == "I> OS")].iloc[0]
    assert (zeile["t bisher [s]"], zeile["t Vorschlag [s]"]) == ("0,50", "1,00")
    assert len(at.dataframe[6].value) == 10                  # Stromstaffel und Empfindlichkeit
    assert "Stromstaffelung nicht wirksam" in _texte(at.caption)
    assert "Motor-Tab-Fenster" not in _texte(at.warning)
    assert "passt nicht unter den Schutz des Netzbetreibers" in _texte(at.warning)
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
    # Der Vorschlag ist jetzt deckungsgleich mit dem Netz
    assert "Keine Änderung nötig" in _texte(at.caption)
    print("Staffelvorschlag OK: Strom und Zeit, Übernahme, danach 6 grün und der Netzbetreiber gelb.")


if __name__ == "__main__":
    test_leerstart()
    test_beispielnetz()
    test_knoten_und_element_anlegen()
    test_bearbeiten()
    test_uebernahme_aus_trafo_tab()
    test_staffelung()
    test_staffelvorschlag()
    print("\nAlle Prüfungen bestanden.")
