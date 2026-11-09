# CLAUDE.md

Anleitung für Claude Code (claude.ai/code) für dieses Repository.

## Projekt

Herstellerneutrales Schutz-Engineering-Tool (Masterarbeit, HSU Hamburg): Streamlit-App, die Einstellwerte für Schutzgeräte (Transformator, Generator, Motor, Leitung, Sammelschiene) nach SIPROTEC-Methodik berechnet und als herstellerneutrale Sollwert-Tabelle mit DIGSI-Adressen ausgibt. Code, Kommentare und UI sind deutsch. In Bezeichnern und Kommentaren stehen Umlaute meist als ae/oe/ue, in UI-Texten und Ausgaben echte Umlaute.

## Befehle

pip install -r requirements.txt        # streamlit, pandas
streamlit run app.py                   # App starten
python test_app.py                     # alle Prüfungen (ca. 1 min, AppTest rendert die ganze App)
pytest test_app.py                     # alternativ
pytest test_app.py::test_validierung_handbuch   # einzelner Test

Es gibt keinen Linter/Formatter.

## Architektur

Pro Betriebsmittel <bm> in {trafo, gen, motor, leitung, sb} gibt es drei Schichten:

- konstanten_<bm>.py: Werksvoreinstellungen (*_def), Auswahllisten und das HERST-Dict (range, grund, adr je Parameter-Key), das unter jedem Regler als Herstellerhinweis angezeigt wird.
- calc_<bm>.py: reine Rechenfunktionen OHNE Streamlit (muss so bleiben, damit isoliert testbar). Muster: grundgroessen(p) -> g, dann schutz_<ANSI>(g, p) je Schutzfunktion, plausibilitaet(...) (Ampel-Liste) und berechne_alle(p) bündelt alles in einem Dict. Eingabe p ist ein flaches Dict mit Einheiten im Schlüsselnamen (Sn_MVA, UN_OS_kV, uk_pct, CT_OS_Prim, ...).
- tab_<bm>.py: Streamlit-UI mit genau einer öffentlichen Funktion show(). Ablauf: Eingaben -> Pflichtfeldprüfung (fehlen Grunddaten: ein st.info und return) -> erweiterte Parameter -> berechne_alle(p) -> Ergebnisse, Ampel, Sollwert-Tabelle.

Gemeinsame Bausteine:
- calc_trafo.py enthält status_empfehlung / status_bereich (Ampel-Logik: OK / Hinweis / Prüfen! / Fehlt). Alle anderen calc_*-Module importieren sie von dort.
- utils.py (streamlit-frei): de() / deg() für Ausgabe mit deutschem Dezimalkomma ohne Tausenderpunkt, AMPEL_EMOJI.
- ui.py: CSS und Streamlit-Bausteine (section, metric, hreg, pin, pill, grphead).
- app.py: Seitenkopf, Info-Tab und Aufruf von tab_<bm>.show() in sechs st.tabs.

## Wichtige Konventionen

- Imports in app.py nur als "import tab_xyz", nicht "from tab_xyz import show". Der Import-Scanner der EXE-Erstellung (streamlit-desktop-app / PyInstaller) bricht sonst. Neue Tab-Module auch in hiddenimports der .spec eintragen (die .spec liegt nicht in diesem Repo, sondern im Hauptordner 15files).
- Einheit der thermischen Zeitkonstante tau (ANSI 49) ist geräteabhängig: Generator (7UM62) in Sekunden, Trafo/Motor/Leitung in Minuten. Die Sammelschiene hat kein 49.
- Eingaben nutzen den Punkt als Dezimaltrenner (Streamlit), alle Ausgaben laufen über de()/deg() mit Komma.
- Grunddaten-Felder starten leer (value=None). Berechnet wird erst, wenn alle Pflichtfelder gefüllt sind.

## Tests (test_app.py)

- test_leerstart: ohne Eingaben genau 5 st.info-Hinweise, 0 Tabellen, 0 Ausnahmen.
- test_struktur: füllt Grunddaten (per Widget-key bzw. -Label in _fill_grunddaten) und prüft die Referenzinventur REF_TABS=6, REF_EXPANDER=86, REF_TABELLEN=53. Jede neue oder entfernte st.expander- oder Tabellen-Ausgabe ändert diese Zahlen. Dann die Konstanten anpassen und den Nutzer darauf hinweisen (Abschnitt 9.2 der Masterarbeit muss nachgezogen werden). Umbenannte Widget-Keys/Labels in _fill_grunddaten nachziehen.
- test_validierung_handbuch: Referenzfall 7UT613-Handbuch Kap. 2.4 (35 MVA, 110/20 kV, uk 15 %, 200/5 A -> 183,7 A / 1469,6 A / 36,7 A / Faktor 8,0). Diese Werte nicht ändern.
- test_parametersweep_uk: 50/51-Empfehlung = 1,2/uk. 87T I-DIFF>> = min(15, round(120/uk, 1)).

## Aufgabe: Netzweite Selektivitätsplanung (Weiterführung der Masterarbeit)

Ziel: Neuer Netz-Tab. Betriebsmittel (Trafo, Motor, Leitung u. a.) werden zu einem Gesamtnetz kombiniert, die Kenndaten kommen aus den bestehenden Tabs, die Schutzsysteme werden für das Gesamtsystem selektiv eingestellt.
- Netzformen: Strahlen- und Ringnetz (Auswahlschalter). Langfristig industrielles MS-Netz, deshalb tief ausbaubar.
- Eingabe: zuerst Baumeingabe, Drag & Drop später. Robustheit vor Funktionsumfang.
- Rahmen: ca. 4 Tage à 5 h pro Woche, Ziel 18.12.2026, Gesamtzeitraum 2 Monate ab 05.11.2026.
- Änderungen vom Betreuer (datiert ergänzen):

## Zusätzliche Regeln für diese Aufgabe

- Netz-Logik in eigenen Modulen netz_*.py ohne Streamlit (Modell, Topologie, Adapter, Selektivität). Nur tab_netz.py darf Streamlit nutzen.
- Das Netzmodell ist die einzige Wahrheit, die UI ist nur eine Ansicht darauf.
- "Code ist die Wahrheit": DIGSI-Adressen, Defaults und Formeln gegen Handbuch und Code prüfen. Annahmen, die nicht aus Handbuch oder Norm belegt sind, als Tool-Vorgabe kennzeichnen.
- Vor jeder Lieferung: Syntaxcheck, test_app.py und neue Tests für neue Module.
- Der neue Tab verändert test_app.py: REF_TABS wird 7, und test_leerstart erwartet derzeit genau 5 st.info-Hinweise. Beides bewusst anpassen und mich darauf hinweisen.
- Arbeiten nur auf dem Branch netz-selektivitaet, main nicht ändern.
- Kurz begründen, warum eine Änderung gemacht wird, nicht nur was.
