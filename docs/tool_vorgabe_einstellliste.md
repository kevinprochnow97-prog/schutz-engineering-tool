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
| 1 | **Adressen, Stand 17.11.2026, gegen die Handbücher geprüft: erledigt.** Im Beispielnetz haben alle Stufen außer der Netzbetreiber-Stufe eine Strom- und eine Zeit-Adresse. Geprüft in 7UT613 (C53000-G1100-C160-3), 7SJ66 (C53000-B1140-C383-D, 09.2023), 7SA6 (C53000-G1100-C156-9) und 7SD5 (C53000-G1100-C169-6). **Trafo 7UT613:** OS 2011 I>>, 2013 T I>>, 2014 I>, 2016 T I>. US ist die zweite Überstromfunktion „U/AMZ-Phase 2“: 2111 I>>, 2113 T I>>, 2114 I>, 2116 T I>. Neu in HERST: `f_I_Ph_US` → Adr.2114. **Motor 7SJ66:** 1202 50-2, 1203 T 50-2, 1204 50-1, 1205 T 50-1 (neu in HERST), 1207 51, 1208 Zeitfaktor 51 bei IEC-Kennlinie (neu in HERST, ANSI: 1209). **Leitung 7SA6 und 7SD5:** 2610 Iph>>, 2611 T Iph>>, 2620 Iph>, 2621 T Iph> in beiden Geräten gleich, unverändert. Die Netzbetreiber-Stufe bleibt bewusst leer, sie ist kein Gerät im Netz. **Umgesetzt am 17.11.2026:** (a) Trafo-Ansprechwerte (I>>, I>, OS und US) schalten nach `CT_Sek` der jeweiligen Seite um: 1 A zeigt die 1-A-Adresse (2011, 2014, 2111, 2114), 5 A die um eins höhere (2012, 2015, 2112, 2115), jeder andere Wert beide Adressen („Adr.2011 (1 A) / 2012 (5 A)“). Zeiten und die Geräte 7SJ66, 7SA6, 7SD5 sind davon nicht betroffen. **Tool-Vorgabe:** Gerätenennstrom = Wandler-Sekundärstrom. (b) Die US-Stufen des Trafos tragen in der Spalte „Hinweis“ (Tabelle und CSV): „Setzt U/AMZ-Phase 2 voraus (projektiert, Adr. 430 = Seite US)“. Das Tool prüft die Projektierung nicht, es kennt sie nicht. **Offen:** Der Handbuch-Text nennt an einer Stelle für T I> der ersten Funktion „Adresse 2116“. Das ist ein Schreibfehler, die Tabelle sagt 2016. | (a) Die Annahme Nennstrom = CT_Sek bei einem echten Gerät bestätigen. (b) Beim ersten Gerät mit DIGSI gegenprüfen, ob U/AMZ-Phase 2 projektierbar und der US-Seite zugeordnet ist. Frage an den Betreuer: Wird die US-Stufe real über die zweite Überstromfunktion abgebildet?
| 1b | **Leitung, 17.11.2026:** Die Spalte „Hinweis“ zeigt bei Betriebsart „Ein: bei U-Ausfall“ den Text „Not-UMZ nur bei Spannungsausfall wirksam …“, bei „Aus“ „Not-UMZ ausgeschaltet.“ (kommt aus dem Adapter). | Erledigt | `netz_adapter._stufen_leitung` |
| 2 | Adresstexte stehen so in HERST, auch mit Hinweisen wie „(beide Geräte)“. Sie werden unverändert ausgegeben. | Mit Betreuer klären, ob Adresse und Hinweis getrennt sein sollen |
| 3 | Sekundärwert rechnet mit dem Wandler der Elementparameter. Bei Leitungen mit Geräten an beiden Enden gilt die Übersetzung des Messorts, nicht die des Gegenendes. | Mit realem Netz prüfen |
| 4 | Die Liste enthält keine Erdfehlerstufen, Differentialschutz oder Richtungsstufen, weil der Adapter sie noch nicht liefert. | Folgt mit dem Adapter |
| 5 | Der Stand in der CSV ist das Erzeugungsdatum, kein Versionsstand der Tool-Vorgaben. | Bei Bedarf Tool-Version ergänzen |
