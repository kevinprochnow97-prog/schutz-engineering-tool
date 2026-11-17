# Plan und Stand: Netzweite Selektivitätsplanung

Stand: 17.11.2026 | Zeitraum 05.11. bis 18.12.2026 | Branch `netz-selektivitaet`

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
| – | Drag & Drop, Richtungsstufen, mehrere Einspeisungen | Bewusst nicht in diesem Zeitraum | ➖ später |

## Wie weit sind wir?

Grob gesagt: **Die Technik ist fertig, jetzt kommen Absicherung und Doku.**

- 13 von 16 Bausteinen sind fertig, das sind alle fachlichen Bausteine.
- Es gibt 174 automatische Tests, alle grün.
- Zeitlich sind wir nach knapp 2 von 6 Wochen weit vorne. Die restlichen gut 4 Wochen reichen für
  Feinschliff, Programmpaket, Betreuer-Antworten und die Doku.

## Was noch offen ist, einfach gesagt

**Beim Tool**
- Die `.spec` für das Programmpaket ergänzen (Module `netz_formular`, `netz_parameter`,
  `netz_einstellliste`, `netz_kurzschluss`, `netz_diagramm`) und den Build einmal testen.
- Einen ruhigen Durchlauf im Browser mit einem selbst gebauten Netz machen und notieren, was
  unklar oder umständlich ist.
- Optional später: Beim Motoranlauf nicht nur warnen, sondern im Vorschlag gleich eine
  Untergrenze setzen.

**Bei den Belegen** (überall steht heute eine begründete Annahme)
- Normtext DIN EN 60909-0: einzelne Faktoren (zum Beispiel c min in der Niederspannung, Faktor
  hinter D/Y-Trafos) am Original bestätigen.
- Literaturstelle für die Staffelung im offenen Ring.
- Netzdaten am Übergabepunkt (Sk″) und Schalterzeiten: für ein echtes Netz vom Netzbetreiber
  bzw. aus dem Datenblatt.

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

Die Herleitungen stehen in den `tool_vorgabe_*.md`-Dateien im selben Ordner.
