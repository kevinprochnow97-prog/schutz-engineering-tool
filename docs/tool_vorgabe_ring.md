# Tool-Vorgabe: Staffelung im offenen Ring über alle Trennstellenlagen

Stand: 11.11.2026 (überarbeitet nach Review) | Gilt für `netz_ring.py` sowie die Erweiterungen in `netz_selektivitaet.py` und `netz_stromstaffel.py`

> **Einordnung:** Alles hier ist eine **Tool-Vorgabe**. Das Verfahren ist eigene Entwicklung und
> durch Tests abgesichert. Ein Literaturbeleg zu Ringnetzschutz und Richtungsstufen ist vor einer
> Verwendung in der Ausarbeitung zu ergänzen (Abschnitt 7).

## 1. Problem

Ein offener Ring wird mit einer Trennstelle betrieben und ist in jeder Lage ein Strahlennetz.
Wird die Trennstelle verlegt (Umschaltung nach einem Fehler, Wartung), ändert sich der
Versorgungsbaum und damit die Staffelkette. Ein Vorschlag nur für die aktuelle Lage ist nach dem
Umschalten nicht mehr selektiv. Im Beispielring braucht L1 als Einzelvorschlag in der Lage
„K34 offen“ 0,8 s für Iph>, in der Lage „L2 offen“ 1,1 s.

Jedes Ringelement kommt als Trennstelle in Frage (`erzeuge_lagen`). Für jede Lage gibt es eine
Kopie des Netzes mit genau diesem Element offen und allen anderen Ringelementen geschlossen.
Das Ergebnis hängt nicht davon ab, welche Lage gerade im Netz eingestellt ist (Test
`test_unabhaengig_von_aktueller_lage`).

## 2. Modellannahme

Eine Leitung hat **einen** Parametersatz. Der Schutz sitzt in jeder Lage am speiseseitigen Ende.
Das entspricht zwei gleich eingestellten, ungerichteten Relais an beiden Leitungsenden. Bei einer
Einspeisung führen beide Enden bei einem Fehler hinter der Leitung denselben Strom, das zweite
Relais ändert das Verhalten also nicht.

## 3. Ist-Prüfung in allen Lagen

`pruefe_ringlagen` führt je Lage die Zeitprüfung und die Stromprüfung mit den Einstellwerten im Netz
aus. Die Oberfläche zeigt eine Zeile je Lage: Ampel, Zahl der grünen, gelben und roten Paare,
Strom-Ampel und das schlechteste Paar.

## 4. Vorschlag für alle Lagen

`ringvorschlag` liefert **einen Satz Einstellwerte, der in allen Lagen gilt**.

1. Je Lage läuft der Gesamtvorschlag (erst Strom, dann Zeit).
2. Je Parameter gilt der **größte** Wert über alle Lagen. Endpunkte einer Lage zählen mit ihrem
   Wert mit. Ein Schutz, der in einer Lage Endpunkt und in einer anderen Mittelstation ist, wird
   so nie abgesenkt.
3. Weil sich die Lagen gegenseitig beeinflussen, wird mit den neuen Werten wiederholt, bis sich
   nichts mehr ändert (Fixpunkt, Werte nur nach oben, höchstens 12 Runden). Die letzte Runde
   bestätigt den Fixpunkt, deshalb sind es mindestens 2 Runden.
4. Der Zeitvorschlag bekommt dafür **Untergrenzen** je Stufe (`untergrenzen`). Ohne sie würde er
   eine Mittelstation jedes Mal aus den Endpunkten neu berechnen und den Zuwachs aus einer
   anderen Lage nicht sehen.
5. Gegenprobe: Ein Fixpunkt muss in jeder Lage selektiv sein, nur der Netzbetreiber darf rot sein.
   Sonst wird er als nicht übernehmbar gemeldet. Das ist durch Zufallsnetze abgesichert.

Beim Strom gilt weiter „nie absenken“. Faktoren werden nur geschrieben, wenn sie sich ändern.
Zeiten werden je Element vollständig geschrieben, weil beim Trafo die US-Zeit sonst der OS-Zeit folgt.

### Ergebnis im Beispielring

Ring: L1, K34 (Trennstelle), L2. Lagen: K34, L1, L2. Fixpunkt nach 2 Runden.

| Stufe | bisher | Vorschlag | bestimmt durch |
|---|---|---|---|
| L1 und L2 Iph>> | 600 A (2,00 × IN) | 1680 A (5,60 × IN) | 1,2 × Ik max hinter T2 (OS) |
| L1 und L2 Iph> (Zeit) | 0,5 s | 1,1 s | 0,3 s über T2 (OS) I> 0,8 s |
| L1 und L2 Iph>> (Zeit) | 0,1 s | 0,4 s | 0,3 s über T2 (OS) I>> 0,1 s |
| T1 I>> OS | 1091 A (10,39 × IN) | 1300 A (12,38 × IN) | Stufensteller, wie im Strahlennetz |
| T1 I>> US | 8083 A (7,00 × IN) | 9480 A (8,21 × IN) | Lage „L1 offen“: 1,2 × Ik max hinter L2 |
| T1 I> OS (Zeit) | 0,5 s | 1,0 s | 0,3 s über T1 (US) I> US 0,7 s |

Nach dem Schreiben ist in keiner Lage ein Paar rot. Das Paar T1 (OS) gegen den Netzbetreiber ist
mit 0,2 s Abstand gelb, in jeder Lage derselbe Wert wie im Strahlennetz.

## 5. Wann ein Ring lösbar ist

**Lösbar** ist ein Ring, in dem kein Schutzort in zwei Lagen in umgekehrter Reihenfolge zu einem
anderen liegt. Das gilt, solange höchstens ein Ringelement mit eigenem Schutz nicht an der
Einspeise-Sammelschiene hängt:

- Beispielring (L1, Kupplung, L2): lösbar.
- Dreileitungsring (L1, L3, L2): lösbar. L3 liegt nie über L1 oder L2. Die Kette wird eine Stufe
  länger (L1 und L2 auf 1,4 s), der Abstand zum Netzbetreiber reicht im Beispiel dann nicht mehr.

**Nicht lösbar** sind gegenläufige Ketten. Beispiel (Testnetz, vier Leitungen La bis Ld zwischen
K2 und K5): Mit Ld als Trennstelle liegt Lb über Lc, mit La als Trennstelle liegt Lc über Lb. Jede
Lage fordert mehr Zeit als die andere liefert, es gibt keinen Fixpunkt. Das Tool liefert dann
**keine Werte**, benennt die Paare („Lc liegt mit Trennstelle La über Lb, mit Trennstelle Ld
darunter“, Funktion `gegenlaeufige_paare`) und empfiehlt, die Trennstelle festzulegen und den
Vorschlag für die aktuelle Lage zu nutzen.

### Was für gegenläufige Ketten nötig wäre

Gegenläufige Ketten brauchen **Richtungsstufen und je Leitungsende eigene Einstellwerte**, beides
zusammen. Eigene Werte je Ende ohne Richtung genügen nicht: Bei einem Fehler hinter der Leitung
führt das lastseitige Relais denselben Strom wie das speiseseitige und würde mit seinen Werten für
die andere Lage auslösen. Erst die Richtung sperrt das lastseitige Relais. Für das Netzmodell heißt
das: Schutzgeräte werden eigene Objekte an einem Leitungsende mit Richtung, statt wie heute ein
Parametersatz je Element. Das ist die Voraussetzung für größere Ringe und für Netze mit mehreren
Einspeisungen.

## 6. Weitere Grenzen

**Abgrenzung (Entscheidung 17.11.2026):** Das Tool staffelt Ringe mit einer Einspeisung, einer
Masche und ungerichteten Stufen, Betrieb offen mit einer Trennstelle. Nicht abgebildet sind
gegenläufige Ketten und Richtungsstufen, der geschlossene Ring, Vermaschung und mehrere Quellen. Bei
gegenläufigen Paaren nennt die Meldung die Paare und rät, die Trennstelle festzulegen oder Richtungs-
stufen außerhalb des Tools zu planen. Die Beschränkung ist bewusst: Sie hält das Modell einfach
(ein Parametersatz je Element), die Erweiterung wäre ein eigener Ausbauschritt (Abschnitt 5).

- **Ik an den Knoten:** Entscheidung 17.11.2026: Im Ring rechnet die Staffelung je Lage mit den
  **berechneten** Ik (`netz_kurzschluss.ersetze_ik`). Wo für einen Knoten nichts berechenbar ist,
  gilt der eingegebene Wert, die Quelle steht in der Ausgabe. Über den Schalter „Ik-Quelle im Ring“
  lässt sich auf „Eingegeben (gleich in allen Lagen)“ umstellen. Das Strahlennetz bleibt bei
  „eingegebener Wert hat Vorrang“. Folge im Beispielring: Mit berechneten Werten steigen die
  Zeiten (T1 I> OS 1,7 s), die Kette passt dann nicht mehr unter den Netzbetreiber (E1 löst bei
  1,2 s aus). Die eingegebenen Werte lagen in „L2 offen“ um rund 17 % unter dem berechneten Wert.
- **Eine Einspeisung, eine Masche.** Mehrere Maschen und geschlossener Betrieb meldet die Topologie
  als Fehler.
- **Kupplung ohne eigenen Schutz** (Tool-Vorgabe, wie bisher).
- **Umschaltzeit und Zwischenzustände** (kurzzeitig geschlossener Ring beim Umschalten) werden
  nicht betrachtet.

## 7. Offene Prüfpunkte

| Nr. | Was prüfen | Wo |
|---|---|---|
| 1 | Entscheidung mit dem Betreuer: Reicht die Beschränkung auf Ringe ohne gegenläufige Ketten, oder sollen Richtungsstufen mit Schutzgeräten je Leitungsende ins Modell | Aufgabenstellung, Abschnitt Netzformen |
| 2 | Literaturbeleg zu Staffelung im offenen Ring und zu Richtungsstufen | Fachliteratur Netzschutz (Quelle noch zu benennen) |
| 3 | **Erledigt 17.11.2026 (Ring).** `netz_kurzschluss.py` rechnet Ik max und Ik min je Trennstellenlage und die Oberfläche warnt bei mehr als 10 % Abweichung vom eingegebenen Wert. Die Ringstaffelung rechnet weiter mit den eingegebenen Werten, nur Knoten ohne Eingabewert bekommen den Wert der jeweiligen Lage. Die Ringstaffelung rechnet standardmäßig je Lage mit den berechneten Werten (Abschnitt 6). Offen: Belege für die Kurzschlussrechnung selbst (Prüfpunkt 5 der Besprechung). | `netz_kurzschluss.py`, `tool_vorgabe_kurzschluss.md` |
| 4 | Höchstzahl der Runden (12) ist eine Tool-Vorgabe ohne Herleitung. Im Beispielring genügen 2, im Dreileitungsring 3 | `netz_ring.py` |
