# Plan und Stand: Netzweite Selektivitätsplanung

Stand: 25.11.2026 | Zeitraum 05.11. bis 18.12.2026 | Branch `netz-selektivitaet`

## Worum geht es?

Das Tool konnte bisher jedes Betriebsmittel (Trafo, Leitung, Motor …) einzeln einstellen.
Neu ist der **Netz-Tab**: Dort baut man aus diesen Betriebsmitteln ein ganzes Netz zusammen.
Das Tool prüft dann, ob die Schutzgeräte **zueinander passen**: Bei einem Fehler soll nur das
Gerät auslösen, das am nächsten am Fehler sitzt (Selektivität). Passt es nicht, schlägt das
Tool neue Werte vor und gibt am Ende eine Einstellliste aus.

## Der Plan in Bausteinen

| Nr. | Baustein | Was er macht | Stand |
|---|---|---|---|
| 1 | Netzmodell und Baumeingabe | Knoten und Elemente anlegen, speichern, laden | ✅ fertig |
| 2 | Topologie | Erkennt Einspeisung, Pfade und Fehler im Aufbau | ✅ fertig |
| 3 | Übernahme aus den Tabs | Holt die Schutzstufen aus Trafo-, Leitungs- und Motor-Tab | ✅ fertig |
| 4 | Zeitstaffelung | Prüft je Paar den Zeitabstand, Ampel grün/gelb/rot | ✅ fertig |
| 5 | Stromstaffelung | Ansprechwerte so, dass das richtige Gerät zuerst anregt, auch über Trafos | ✅ fertig |
| 6 | Staffelvorschlag | Schlägt neue Ströme und Zeiten vor, mit Begründung und Übernahme-Knopf | ✅ fertig |
| 7 | Ringnetz | Offener Ring, jede Trennstellenlage wird geprüft, ein Vorschlag für alle Lagen | ✅ fertig |
| 8 | Kurzschlussrechnung | Rechnet Ik max und Ik min aus den Netzdaten (angelehnt an IEC 60909) | ✅ fertig, mit pandapower gegengerechnet |
| 9 | Staffeldiagramm | Kennlinien aller Geräte in einem Bild | ✅ fertig |
| 10 | Einstellliste | Alle Werte mit Geräteadresse, als CSV zum Mitnehmen | ✅ fertig |
| 11 | Bedienung | Bearbeiten statt Löschen, Parameter direkt im Netz-Tab ändern | ✅ fertig |
| 12 | Motoranlauf | Warnt, wenn eine Stufe beim Anlauf des Motors auslösen würde | ✅ fertig (nur Meldung) |
| 13 | AMZ-Abstand | Bei abhängigen Kennlinien wächst der nötige Abstand mit der Zeit | ✅ fertig |
| 14 | Robustheit und Feinschliff | Unsinnige Eingaben abfangen, Texte vereinfachen, Browser-Durchlauf | 🔄 laufend |
| 15 | Programmpaket (.exe) | Neue Module in der `.spec` eintragen, Build testen | ⏳ offen (Kevin) |
| 16 | Doku für die Ausarbeitung | Aus den Tool-Vorgaben in `docs/` einen Text für die Arbeit machen | ⏳ offen |
| 17 | Erdfehler (Strahlennetz) | Ik1 aus dem Nullsystem, Erdstufen der Tabs staffeln, Empfindlichkeit, Vorschlag, Einstellliste | ✅ fertig (25.11.2026), mit pandapower gegengerechnet |
| – | Drag & Drop, Richtungsstufen, mehrere Einspeisungen, Erdfehler im Ring | Bewusst nicht in diesem Zeitraum. Betreuer 25.11.2026: Netzausgestaltung nicht komplexer | ➖ später |

## Wie weit sind wir?

Grob gesagt: **Die Technik ist fertig, jetzt kommen Absicherung und Doku.**

- 14 von 17 Bausteinen sind fertig, das sind alle fachlichen Bausteine (seit 25.11.2026 mit Erdfehler).
- Es gibt 232 automatische Tests, alle grün.
- Zeitlich sind wir nach knapp 3 von 6 Wochen weit vorne, auch mit dem Erdfehler. Die restlichen
  gut 3 Wochen reichen für Feinschliff, Programmpaket, Betreuer-Antworten und die Doku.

## Was noch offen ist, einfach gesagt

**Beim Tool**
- Die `.spec` für das Programmpaket ergänzen (Module `netz_formular`, `netz_parameter`,
  `netz_einstellliste`, `netz_kurzschluss`, `netz_diagramm`, neu `netz_erdfehler`) und den Build
  einmal testen. Das neue Beispielnetz `beispielnetze/industrie_10kV_noe.json` mitnehmen.
- Einen ruhigen Durchlauf im Browser mit einem selbst gebauten Netz machen und notieren, was
  unklar oder umständlich ist.
- Optional später: Beim Motoranlauf nicht nur warnen, sondern im Vorschlag gleich eine
  Untergrenze setzen.

**Bei den Belegen** (überall steht heute eine begründete Annahme)
- ~~Normtext DIN EN 60909-0 am Original prüfen~~ **erledigt 25.11.2026**: alles bestätigt, zwei
  Änderungen eingebaut (Motoren bei Ik max, Leitertemperatur bei Ik min adiabatisch). Das
  Normbeispiel IEC/TR 60909-4, Abschnitt 5, kommt exakt heraus. Beiblatt 4 (IEC/TR 60909-2) gelesen 25.11.2026, Yzn-Nullreaktanz 0,1 eingebaut. K und β an DIN VDE 0100-540, Anhang A geprüft. Offen:
  Quelle für 2/√3.
- Literaturstelle für die Staffelung im offenen Ring.
- Netzdaten am Übergabepunkt (Sk″) und Schalterzeiten: für ein echtes Netz vom Netzbetreiber
  bzw. aus dem Datenblatt.
- Erdfehler: R0′/X0′ der Kabel aus dem Datenblatt, Z0 der Trafos, Ik1″ am Übergabepunkt und
  die Adressen der Erdstufen am Handbuch (Prüfpunkte in `tool_vorgabe_erdfehler.md`).

**Für den Betreuer** (nur kurz informieren oder fragen)
- Zur Info: Motoranlauf wird geprüft und gemeldet, nicht automatisch korrigiert.
- Zur Info: Ringe nur ohne Richtungsstufen, K_T nur bei Ik max.
- Frage: Wird die Trafo-US-Stufe real über „U/AMZ-Phase 2“ abgebildet?
- Frage: Darf man annehmen, dass der Gerätenennstrom gleich dem Wandler-Sekundärstrom ist?
- Frage: Gibt es ein reales oder veröffentlichtes Netz zum Testen?

## Wichtige Entscheidungen vom 17.11.2026

| Thema | Entscheidung |
|---|---|
| Ik im Ring | Je Trennstellenlage mit berechneten Werten, Schalter auf „eingegeben“ möglich |
| Motoranlauf | Prüfung mit Ampel, Schalter „Anlauf im Gerät gesperrt“ nur für 50-1 des Motors |
| Ring-Grenzen | Keine Richtungsstufen, keine gegenläufigen Ketten, kein geschlossener Ring |
| Leitung | Neue Leitungen mit Not-UMZ „Ein: immer aktiv“, sonst Warnung |
| Kurzschluss | K_T nur bei Ik max (Gegenrechnung mit pandapower) |
| AMZ-Abstand | Zuschlag aus der Zeittoleranz des 7SJ66 (5 % + 2 % Strom, mindestens 30 ms) |

## Entscheidungen vom 25.11.2026 (Gespräch mit dem Betreuer)

| Thema | Entscheidung |
|---|---|
| Umfang | Netzausgestaltung nicht komplexer, der aktuelle Umfang ist in Ordnung |
| Erdfehler | Einpoliger Erdkurzschluss wird ergänzt, zuerst nur im Strahlennetz |
| Erdungspunkt | Feld „Erdfehlerstrom-Begrenzung“ am Knoten (nur niederohmig), sonst Sternpunkt eines Trafos |
| Kabel-Nullsystem | Felder R0′/X0′, ohne Eingabe aus RE/RL und XE/XL der Leitung |
| Testfall | Neues Beispielnetz `industrie_10kV_noe.json`, Referenznetz unverändert |
| Handwerte Ik max | Auf die Werte mit Motoren angehoben (alle drei Beispielnetze). Die Werte in der Masterarbeit waren ohne Motoren |
| Kabel-Nullimpedanz | Beispielnetze bleiben bei Z0 = 4 · Z1 (Beiblatt-4-Werte ändern Ik1 um höchstens 0,3 %) |
| NS-Toleranz | Bleibt fest bei 10 % (c 1,10 / 0,90), keine Auswahl in der Oberfläche |

Die Herleitungen stehen in den `tool_vorgabe_*.md`-Dateien im selben Ordner.
