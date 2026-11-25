# Tool-Vorgabe: Staffeldiagramm

Stand: 16.11.2026 | Gilt für `netz_diagramm.py` und den Abschnitt „Staffeldiagramm“ in `tab_netz.py`

> **Einordnung:** Das Diagramm ist eine reine Darstellung. Es rechnet nichts Eigenes, jede Zeit
> stammt aus `netz_selektivitaet.ausloesezeit()`, also aus derselben Funktion wie die Ampeln der
> Zeitstaffelung. Diagramm und Tabelle können sich deshalb nicht widersprechen (Test
> `test_uebereinstimmung_mit_pruefung`). Die Regeln der Darstellung sind Tool-Vorgaben.

## 1. Was das Diagramm zeigt

Je Versorgungspfad (von der Last zur Quelle) die wirksame Auslösezeit jedes Schutzortes über dem
Strom. Beide Achsen sind logarithmisch. Alle Ströme sind auf die Bezugsspannung der Zeitstaffelung
umgerechnet (Nennübersetzung, Stufensteller in Mittelstellung, wie in der Zeitprüfung).

Der Pfad ist selektiv, wenn jede Kennlinie im gemeinsamen Strombereich mit Abstand über der des
Schutzes darunter liegt. Mit eingeschaltetem Staffelvorschlag zeigt ein zweites Diagramm denselben
Pfad mit den vorgeschlagenen Werten.

## 2. Regeln der Darstellung

| Regel | Begründung |
|---|---|
| Die Kennlinie beginnt am kleinsten Anregestrom mit einer Senkrechten | Darunter löst der Schutz nicht aus. Bei AMZ ist das 1,1 · Ip. |
| Die Kennlinie endet bei Ik max am eigenen Messort | Mehr Strom kann durch diesen Schutz nicht fließen. Fehlt Ik max, läuft sie bis zum rechten Rand. |
| Rechter Rand = 1,3 · größter Strom aus Ik max der Knoten des Pfades und den Ansprechwerten | Knoten auf anderer Spannungsebene zählen nicht mit. Ik der 110-kV-Seite liegt auf 10 kV bezogen bei 172,7 kA und würde das Bild stauchen. Solche Werte werden unter dem Diagramm genannt. |
| Zeiten unter 0,01 s stehen auf der Linie 0,01 s | Eine logarithmische Achse kennt keine Null. Der echte Wert steht im Tooltip. |
| Obere Zeitgrenze 10 s oder das Dreifache der längsten UMZ-Zeit | AMZ-Kennlinien werden dort abgeschnitten. |
| Senkrechte Marken: Ik max und Ik min der Messknoten des Pfades | Zeigt, in welchem Strombereich die Staffelung wirken muss. |
| Linien der Quelle breit, der Last schmal und obenauf | Deckungsgleiche Abschnitte bleiben sichtbar. |

## 3. Grenzen

- Nur Phasenstufen 50/51, wie die Zeitstaffelung.
- Stufenstellerlage und Schaltgruppe sind nicht dargestellt. Sie stecken in der Stromstaffelung.
- Im Ring zeigt das Diagramm die aktuelle Trennstellenlage.
- Toleranzbänder der Geräte sind nicht eingezeichnet.
- Die Eigenzeit des Leistungsschalters ist nicht addiert. Das Diagramm zeigt die Kommandozeit des
  Schutzes, der Staffelabstand deckt die Schalterzeit ab.

## 4. Offene Prüfpunkte

| Nr. | Was prüfen | Wo |
|---|---|---|
| 1 | Übliche Darstellung im Staffelplan (Kennlinie bis Ik max, Bezugsspannung, Kommandozeit oder Gesamtausschaltzeit) mit einer Quelle belegen | FNN-Leitfaden zum Einsatz von Schutzsystemen, Fachliteratur Netzschutz |
| 2 | Export des Diagramms als Bild für die Ausarbeitung (bisher nur über das Menü des Diagramms in der Oberfläche) | `tab_netz.py` |
