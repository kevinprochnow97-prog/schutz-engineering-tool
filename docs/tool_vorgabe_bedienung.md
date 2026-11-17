# Tool-Vorgabe: Bedienung des Netz-Tabs (Formulare und Bearbeiten)

Stand: 17.11.2026 | Gilt für `netz_formular.py`, `netz_parameter.py` und die Abschnitte „Knoten/Element anlegen“ und „Netz bearbeiten“ in `tab_netz.py`

> **Einordnung:** Das Dokument beschreibt Bedienregeln des Tools, keine Normvorgaben. Alle Regeln sind
> Tool-Vorgaben. Das Netzmodell bleibt die einzige Wahrheit, die Formulare sind nur Entwürfe.

## 1. Formular-Zustand beim Anlegen

| Regel | Umsetzung | Warum |
|---|---|---|
| Wird eine Eingabe abgewiesen, bleiben alle Werte im Formular stehen | Die Formulare nutzen kein `clear_on_submit`. Fehlermeldung unter dem Formular, es wird nichts ins Modell geschrieben | Nur der falsche Wert muss korrigiert werden |
| Nach erfolgreichem Anlegen sieht das Formular aus wie beim ersten Öffnen | Der Aufruf setzt einen Merker (`netz_reset_k`, `netz_reset_e`). Beim nächsten Lauf schreibt das Formular **vor dem Zeichnen** die Vorbelegung `KNOTEN_LEER` / `ELEMENT_LEER` in die Widgets | Streamlit erlaubt das Setzen eines Widget-Werts nur, bevor das Widget gezeichnet ist. Gesetzt statt gelöscht, damit der Browser den neuen Wert sicher übernimmt |
| Ein gemerkter Knoten, der inzwischen entfernt wurde, bricht das Formular nicht | Auswahl fällt auf „—“ zurück | Sonst wirft die Selectbox eine Ausnahme |

„Angelegt und im Schaltplan eingebunden“ ist hier gleichbedeutend mit „vom Modell angenommen“. Ein Knoten ohne
Element wird angelegt (und von der Topologie gemeldet), danach ist das Formular leer.

## 2. Bearbeiten statt Löschen und neu Anlegen

Knopf **✏️ Bearbeiten** neben der Auswahl von Element bzw. Knoten. Der Entwurf wird aus dem Modell geladen und erst
mit **💾 Änderungen speichern** ins Modell geschrieben. **Abbrechen** verwirft ihn.

| Objekt | Änderbar | Bleibt | Besonderheit |
|---|---|---|---|
| Knoten | Bezeichnung, UN, Sternpunkt, Ik″ max, Ik min | ID, damit alle Verbindungen der Elemente erhalten bleiben | Ändert sich UN, meldet die Topologie sofort die Spannungsverträglichkeit entlang der Kanten |
| Element | Bezeichnung, von-Knoten, nach-Knoten, bei der Einspeisung I> und t des Netzbetreibers | ID, Typ, Zustand, Parametersatz | Nur die Knotenfelder, die der Typ braucht, erscheinen (Einspeisung nur „nach“, Motor nur „von“) |

Gründe für die Grenzen:

- **ID und Typ** sind fest. Andere Elemente und Meldungen verweisen auf die ID. Der Parametersatz hängt am Typ
  (ein Trafo-Satz ergibt für eine Leitung keinen Sinn). Wer den Typ ändern will, legt neu an.
- **Zustand** schaltet der vorhandene Knopf Ein/Aus. Im Entwurf wäre er veraltet, sobald zwischendurch geschaltet wird,
  und Speichern würde die Schaltung zurücknehmen.
- **Trafo-Richtung tauschen:** `von` ist die Oberspannungsseite (OS). Die Seitenangaben im Parametersatz (CT OS/US, Sn, uk)
  gehören zu den physischen Seiten. Wird die Richtung nur korrigiert, tauschen daher allein die beiden Knoten, die Parameter
  stimmen danach. Die Topologieprüfung meldet eine falsche Richtung („Richtung tauschen“) und verschwindet mit der Korrektur.
- **Atomar:** `Netz.element_aendern` und `Netz.knoten_aendern` prüfen erst komplett und ersetzen dann. Bei einem Fehler
  bleibt das Objekt wie es war, die Eingaben bleiben im Formular.
- Ein offener Entwurf verfällt, wenn sein Objekt entfernt oder ein anderes Netz geladen wird.

## 3. Parameter im Betriebsmittel-Tab bearbeiten (Befund und Entscheidung)

**Wunsch:** Ein Element im Tab Transformator, Leitung oder Motor bearbeiten, um Schutzparameter und Wandler genauer
einzustellen.

**Ist-Zustand des Datenflusses:** Jeder Tab schreibt am Ende von `show()` eine Kopie seines Parametersatzes nach
`st.session_state["netz_p_<typ>"]`. Der Netz-Tab übernimmt diese Kopie nur auf Knopfdruck („Parameter aus Tab übernehmen“
bzw. beim Anlegen) ins Modell (`Element.p`). Die Richtung ist also immer **Tab → Modell**, der Tab ist ein Rechner mit
eigenem Eingabestand und nie Quelle der Wahrheit.

**Was gegen ein direktes „Element im Tab öffnen“ spricht (Stand Code):**

| Befund | Folge |
|---|---|
| `tab_trafo.py` hat 69 Eingabe-Widgets, **keines mit `key=`** | Werte lassen sich nicht von außen setzen. Es wären 69 Schlüssel nachzurüsten, auch in `test_app.py` (Befüllung per Label) |
| `tab_leitung.py` (`ltg_*`) und `tab_motor.py` (`mot_*`) haben Schlüssel, die **nicht** den Parameterschlüsseln `p[...]` entsprechen | Je Tab ist eine Zuordnungstabelle Parameterschlüssel → Widget-Schlüssel nötig, die bei jeder Änderung eines Tabs mitgepflegt werden muss |
| Die Tabs laufen im selben Lauf **vor** dem Netz-Tab | Das Laden Modell → Tab ist nur in einem Knopf-Callback möglich (vor dem Zeichnen) |
| Während der Bearbeitung unterscheiden sich Tab und Modell | Zwei Stände nebeneinander. Das ist mit „Modell ist die Wahrheit“ nur vereinbar, wenn der Tab klar als Entwurf gekennzeichnet ist und nur ein Knopf schreibt |

**Zwei saubere Varianten:**

| | Variante 1: Parameter-Editor im Netz-Tab | Variante 2: Tab-Rundlauf |
|---|---|---|
| Idee | Ausgewählte Parameter des Elements direkt am Modell bearbeiten (Wandler, Ansprechwerte, Zeiten je Typ), Formular wie das Bearbeiten-Formular | Knopf „Im Tab bearbeiten“ lädt `Element.p` per Callback in den Tab, Banner „Entwurf für T2“, Knopf „Ins Netz zurückschreiben“ bzw. „Verwerfen“ |
| Modell ist Wahrheit | Ja, Schreiben nur über `Netz.parameter_setzen` | Ja, wenn der Entwurf gekennzeichnet ist und nur der Knopf schreibt |
| Eingriff in Betriebsmittel-Tabs | Keiner | Schlüssel für alle Widgets, Zuordnungstabellen, Banner, Anpassung `test_app.py` |
| Bedienung | Nicht die gewohnte Tab-Oberfläche, nur die netzrelevanten Parameter | Volle Tab-Oberfläche mit Herstellerhinweisen |
| Aufwand (grobe Schätzung) | ca. 1 Tag | ca. 2 bis 3 Tage, Risiko für die Inventur in `test_app.py` |

**Entscheidung 17.11.2026: Variante 1.** Variante 2 bleibt als Option, falls die volle Tab-Oberfläche gebraucht wird.

### 3.1 Umsetzung Variante 1 (`netz_parameter.py`, Knopf „🔧 Parameter bearbeiten“)

| Regel | Umsetzung |
|---|---|
| Welche Felder | `netz_parameter.FELDER[typ]`: genau die Schlüssel, die Adapter (`PFLICHT`, `OPTIONAL_ZAHL`) und Kurzschlussrechnung aus `Element.p` lesen. Ein Test stellt sicher, dass alle Schlüssel, die Zeit- und Stromvorschlag schreiben, editierbar sind |
| Typen | Einspeisung (Sk″, Netzbetreiber-Schutz, R/X), Trafo, Leitung, Motor. Kupplung und Generator haben keine Parameter, der Knopf ist gesperrt |
| Nicht im Editor | Ik-Werte (die Knoten sind die Wahrheit, der Adapter überschreibt sie ohnehin), `k_S_IGG` und alle übrigen Schlüssel aus den Tabs. Sie bleiben beim Speichern unverändert |
| Leeres Feld | Schlüssel wird entfernt, es gilt die Werksvoreinstellung des Rechenkerns bzw. die Tool-Vorgabe. Sie steht als Hinweis (Tooltip und Platzhalter) am Feld |
| Prüfung | Wertebereiche je Feld und Querprüfungen (ukr < uk, Sk″ min ≤ Sk″ max, I> und t des Netzbetreibers nur als Paar). **Alle** Fehler werden zusammen gemeldet, bei einem Fehler wird nichts geschrieben und die Eingaben bleiben stehen |
| Pflichtfelder | Dürfen leer bleiben (mit * markiert). Der Adapter meldet fehlende Felder je Element, wie beim Anlegen ohne Tab-Daten |
| Schreiben | Nur über `Netz.parameter_setzen`, also atomar |
| Entwurf | Jede erfolgreiche Änderung am Modell (Schalten, Übernahme aus dem Tab, Vorschlag übernehmen, Entfernen, Anlegen) schließt einen offenen Entwurf. Sonst würde Speichern neuere Werte mit alten überschreiben |

Grenzen: Der Editor zeigt Schlüssel mit sprechenden Namen, aber ohne die Herstellerhinweise der Tabs (DIGSI-Adressen, Bereiche).
Für die Adressen gilt weiter der Tab bzw. die Einstellliste. Wertebereiche sind die der Rechenkerne und Tabs
(zum Beispiel Stufensteller 0 bis 40 %, φ bis 90°), keine Gerätegrenzen.

## 4. Offene Prüfpunkte

| Nr. | Was prüfen | Wo |
|---|---|---|
| 1 | Zurücksetzen und Behalten der Formularwerte im echten Browser (AppTest zeigt nur den Serverzustand): Knoten mit Fehler anlegen, Werte müssen stehen bleiben. Danach gültig anlegen, Formular muss leer sein | `streamlit run app.py`, Netz-Tab |
| 2 | Parameter-Editor im Browser: Trafo T2 öffnen, CT ändern, speichern, Staffelung muss sich ändern. Feld leeren, Voreinstellung muss gelten | `streamlit run app.py`, Netz-Tab |
| 3 | `netz_formular` und `netz_parameter` in `hiddenimports` der `.spec` im Hauptordner 15files eintragen (zusammen mit `netz_kurzschluss`, `netz_diagramm`, `netz_einstellliste`) | `.spec` |
