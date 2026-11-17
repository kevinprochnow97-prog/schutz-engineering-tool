# Tool-Vorgabe: Einstellliste

Stand: 17.11.2026 | Gilt für `netz_einstellliste.py` und den Abschnitt „Einstellliste (Export)“ in `tab_netz.py`

> **Einordnung:** Die Einstellliste ist das Ergebnis der Netzplanung in der Form, in der es weitergegeben
> wird (Betreuer, Inbetriebnahme). Das Modul **rechnet fachlich nichts**: Stufen kommen aus
> `netz_adapter` (Rechenkerne der Betriebsmittel-Tabs), neue Werte aus dem gewählten Vorschlag
> (`netz_stromstaffel.gesamtvorschlag` oder `netz_ring.ringvorschlag`). Die Liste kann den
> Vorschlägen deshalb nicht widersprechen (Tests `test_staffelvorschlag`, `test_ringvorschlag`).

## 1. Inhalt je Zeile (eine Zeile je Schutzstufe)

| Spalte | Herkunft |
|---|---|
| Element, Bezeichnung, Messort, UN | Netzmodell |
| Wandler | `CT_*_Prim/Sek` der Elementparameter am Messort (Trafo je Seite OS/US, Leitung und Motor `CT_Prim/Sek`) |
| Stufe, ANSI, Kennlinie, aktiv | Schutzstufe aus dem Adapter |
| I prim. [A] | Ansprechwert am Messort (Adapter) |
| I sek. [A] | I prim. / Wandlerübersetzung. Ohne Wandlerangabe leer |
| x IN | I prim. / Nennstrom des Messorts (`netz_adapter.nennstrom_A`) |
| t [s], T-Mult. | UMZ-Verzögerung bzw. AMZ-Zeitmultiplikator |
| geändert, I neu, I sek. neu, x IN neu, t neu, Begründung | nur mit gewähltem Vorschlag. Nur geänderte Werte sind gefüllt |
| Adresse Ansprechwert / Zeit | `HERST[...]['adr']` aus `konstanten_<bm>.py` |

Sortierung: von der Quelle zur Last (Abstand im Pfad), je Element nach Messort und Stufe.

## 2. Entscheidungen

1. **Drei Quellen wählbar:** Einstellwerte im Netz (Ist), Staffelvorschlag, Ringvorschlag (nur im Ring).
   Begründung: Der Betreuer bekommt je nach Stand die Ist-Liste oder die Änderungsliste.
2. **Wert gilt als geändert**, wenn er sich um mehr als Rundungsrauschen unterscheidet
   (Strom relativ 1e-9, Zeit 1 µs). Unveränderte Werte erscheinen nicht als „neu“.
3. **Begründung** wie im Tab: „0,30 s über <Stufe darunter>“ (`warum_zeit`, eine Funktion für Tab und Liste).
4. **Adressen werden nie geraten.** Fehlt in HERST eine Adresse, bleibt das Feld leer.
5. **Kein Schreiben ins Modell:** Die Liste ist nur eine Ausgabe. Übernommen wird weiter über die
   Schaltflächen bei den Vorschlägen.
6. Im Ring gilt der Staffelvorschlag nur für die aktuelle Trennstellenlage (wie im Tab). Für alle
   Lagen den Ringvorschlag wählen.

## 3. CSV-Format (Tool-Vorgabe)

Semikolon als Trennzeichen, Dezimalkomma, UTF-8 mit BOM, Zeilenende CRLF. Damit öffnet ein deutsches
Excel die Datei per Doppelklick ohne Import-Dialog, mit Umlauten und Zahlen als Zahlen.
Kopf: Zeile 1 Titel und Netzname, Zeile 2 Stand (Datum der Erzeugung), Zeile 3 Vorschlag (oder
„keiner“), Zeile 4 Hinweis, Zeile 5 leer, ab Zeile 6 Spaltenüberschriften. Die Vorschlagsspalten sind
immer enthalten (bei Ist-Liste leer), damit das Layout gleich bleibt.

## 4. Robustheit

Das Modul wirft nie: leeres Netz ergibt eine leere Liste, ein Vorschlag mit unbekannter Stufe eine
Fehlermeldung, ein interner Fehler eine Meldung statt einer Ausnahme (`test_fehlerfaelle`).
Die Liste wird nur berechnet, wenn der Schalter eingeschaltet ist, die übrigen Abschnitte des Tabs
bleiben unberührt.

## 5. Prüfpunkte (offen)

| Nr. | Punkt | Stand |
|---|---|---|
| 1 | **Adressen für Ansprechwerte, Stand 17.11.2026:** Die I>-Stufen werden jetzt über `_STROM_ADRESSE_ZUSATZ` in `netz_einstellliste.py` nachgeschlagen (Trafo I> OS → `f_I_Ph` Adr.2014, Leitung Iph> → `iph_h` Adr.2620, Motor 50-1 → `f_50_1` Adr.1204, 51 → `f_51` Adr.1207). `netz_adapter.STROM_PARAMETER` bleibt bei den I>>-Stufen, sonst würde der Stromvorschlag die I>-Stufen mitstaffeln. Im Beispielnetz haben jetzt 13 von 16 Stufen eine Strom- und 13 eine Zeit-Adresse. **Weiter leer, nicht geraten:** Trafo I> US (`f_I_Ph` gilt für beide Seiten, HERST nennt nur die OS-Adresse 2014), Zeit von 50-1 und 51 (in `konstanten_motor.py` steht Adr.1205 bzw. 1208 nur im Kommentar, nicht in HERST), Netzbetreiber-Stufe. | Adressen der US-Seite und der Motor-Zeiten im Handbuch (7UT613 Kap. 2, 7SJ66) prüfen und dann in HERST ergänzen, damit sie auch in den Tabs erscheinen |
| 2 | Adresstexte stehen so in HERST, auch mit Hinweisen wie „(beide Geräte)“. Sie werden unverändert ausgegeben. | Mit Betreuer klären, ob Adresse und Hinweis getrennt sein sollen |
| 3 | Sekundärwert rechnet mit dem Wandler der Elementparameter. Bei Leitungen mit Geräten an beiden Enden gilt die Übersetzung des Messorts, nicht die des Gegenendes. | Mit realem Netz prüfen |
| 4 | Die Liste enthält keine Erdfehlerstufen, Differentialschutz oder Richtungsstufen, weil der Adapter sie noch nicht liefert. | Folgt mit dem Adapter |
| 5 | Der Stand in der CSV ist das Erzeugungsdatum, kein Versionsstand der Tool-Vorgaben. | Bei Bedarf Tool-Version ergänzen |
