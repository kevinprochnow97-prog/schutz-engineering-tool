# Tool-Vorgabe: Stromstaffelung der I>>-Stufen und Umrechnung über Transformatoren

Stand: 11.11.2026 | Gilt für `konstanten_netz.py`, `netz_umrechnung.py` und `netz_stromstaffel.py`

> **Einordnung:** Alles in diesem Dokument ist eine **Tool-Vorgabe**. Keine der Regeln ist
> eine Werksvoreinstellung eines Geräts. Die Herleitungen sind eigene Rechnungen, die
> durch Tests abgesichert sind. Ein Literaturbeleg ist vor einer Verwendung in der
> Ausarbeitung zu ergänzen (Abschnitt 7).

## 1. Ansatz im Überblick

Der Staffelvorschlag läuft in drei Schritten, jeweils von der Last zur Quelle:

1. **Strom:** Jede I>>-Stufe bekommt einen Ansprechwert über dem Strom, den die nächste
   Station noch führt (Abschnitt 2).
2. **Zeit:** Mit diesen Ansprechwerten werden die Zeiten gestaffelt
   (`netz_selektivitaet.staffelvorschlag`, siehe `tool_vorgabe_staffelabstand.md`).
3. **Gegenprüfung:** Zeit (Ampel je Paar), Stromstaffel und Empfindlichkeit (Abschnitt 4).

Die Reihenfolge ist fachlich zwingend. Die Zeitstufe einer I>>-Stufe hängt davon ab, bei
welchen Strömen sie anregt, und das legt erst der Ansprechwert fest.

## 2. Regel der Stromstaffelung

Für die I>>-Stufe eines Schutzortes O mit der nächsten Station u darunter:

    I>>(O)  ≥  k_S · I_Bezug(u)          mit k_S = 1,2

Gibt es mehrere Stationen darunter, gilt der größte Wert. Ströme werden vor dem Vergleich
auf die Bezugsspannung umgerechnet (`auf_bezug`).

### 2.1 Bezugsstrom I_Bezug(u)

| Fall | Bezugsstrom | Begründung |
|---|---|---|
| u liegt vor einer Leitung oder einem Trafo, Ik max am Knoten **hinter** u bekannt | Ik max dieses Knotens, gelesen am Messort von O (Abschnitt 3) | Reine Stromstaffelung: O darf bei keinem Fehler hinter u ansprechen. |
| u ist ein Motor | max(I>> des Motors, Anlaufstrom) | Hinter einem Motor gibt es keinen Knoten. Die Leitung darüber darf beim Anlauf nicht auslösen. |
| Ik max hinter u fehlt | I>> von u | Ersatz, damit O im Bereich von I>>(u) die Zeitstaffelung von u abwartet. Dazu gibt es einen Hinweis. |

„Hinter u“ heißt: der Knoten auf der Lastseite des Elements. Beim speiseseitigen Schutzort
einer Leitung ist das ihr Gegenknoten, bei der OS-Seite eines Trafos die US-Sammelschiene.
Beim lastseitigen Schutzort eines Trafos ist es die Sammelschiene selbst, weil die Abgänge
dahinter eigene Elemente sind.

### 2.2 Drei Schutzregeln für den Wert

- **Nie absenken.** Der Vorschlag hebt einen Wert nur an. Liegt der Tab-Wert schon über
  k_S · I_Bezug, bleibt er (Status „bleibt“). Einschaltstrom, Anlauf und Wandlerfehler sind
  in den Betriebsmittel-Tabs berücksichtigt und dürfen nicht unterlaufen werden.
- **Aufrunden.** Der Faktor (x IN) wird auf das Raster 0,01 **aufgerundet**
  (`konstanten_netz.Raster_Faktor`). Ein zu kleiner Wert wäre unselektiv.
- **Wirksamkeit.** Ist k_S · I_Bezug größer als Ik max am eigenen Messort, kann die Stufe nie
  ansprechen. Der Wert bleibt dann unverändert, die Stufe wird wie eine Zeitstufe gestaffelt
  und es gibt einen Hinweis. Typisch ist das bei kurzen Kabeln, wo sich Ik zwischen Anfang und
  Ende kaum ändert.

### 2.3 Zahlenwerte

| Größe | Konstante | Wert | Herkunft |
|---|---|---|---|
| Sicherheitsfaktor | `k_S_Strom` | 1,20 | Gleicher Wert wie `konstanten_trafo.k_S_IGG` (Trafo-Tab, I>> bezüglich Ik max der nachgelagerten Station). Ein Test prüft die Gleichheit. |
| Raster Faktor | `Raster_Faktor` | 0,01 | Tool-Vorgabe, gleiche Rundung wie die Trafo-Empfehlung. |
| Empfindlichkeit | `gamma_Reserve` | 1,50 | Gleicher Wert wie `konstanten_trafo.gamma_Ikmin` und `calc_leitung`. Ein Test prüft die Gleichheit. |

## 3. Umrechnung über Transformatoren

Ein Strom am Fehlerknoten wird als Strom am Messort des Schutzes gelesen. Je Trafo zwischen
beiden Punkten gilt (Strom fließt vom Fehler Richtung Quelle, also von der US- zur OS-Seite):

    I_OS = I_US · (UN_US / UN_OS) · f_Stufensteller · f_Schaltgruppe

Leitungen und Kupplungen ändern den Strom nicht. Mehrere Trafos in Reihe multiplizieren
ihre Faktoren.

### 3.1 Übersetzung

Verhältnis der **Knoten**-Nennspannungen (nicht der Typenschildwerte), damit das Modell eine
einzige Wahrheit bleibt.

### 3.2 Stufensteller

Tool-Vorgabe: Der Stufensteller sitzt auf der **OS-Wicklung**, Mittelstellung ist die
Nennübersetzung, der Stellbereich ist ±s (Element-Parameter `Stufensteller_pm`).
Hat die OS-Wicklung (1 + x) mal die Windungen, ist der OS-Strom 1/(1 + x) mal so groß.

| Fall | Stufenstellerlage | Faktor | Bei s = 16 % |
|---|---|---|---|
| Ik max (nach oben abgrenzen) | x = −s | 1 / (1 − s) | 1,190 |
| Ik min (Empfindlichkeit) | x = +s | 1 / (1 + s) | 0,862 |

Je Fall gilt die ungünstigste Lage. Fehlt der Parameter oder ist er ungültig, gilt Faktor 1
mit Hinweis.

### 3.3 Schaltgruppe beim zweipoligen Fehler

Per Tool-Vorgabe ist **Ik min an einem Knoten der kleinste zweipolige Kurzschlussstrom**
(so im Referenznetz und in `calc_motor`), **Ik max der dreipolige**.

Bei einem Wechsel zwischen Dreieck und Stern verteilt sich ein zweipoliger Fehler auf der
anderen Seite im Verhältnis 1 : ½ : ½ auf die Leiter. Der **größte** Leiterstrom ist

    I_max,Leiter = (2/√3) · Ik2 / ü  =  1,155 · Ik2 / ü

Das ist genau der Wert des dreipoligen Fehlers, wenn Ik2 = (√3/2) · Ik3 gilt. Der Test
`test_schaltgruppe_zweipolig_gegen_wicklungsrechnung` rechnet das unabhängig aus den
Wicklungsströmen nach, für Dy (Fehler auf der Sternseite) und Yd (Fehler auf der
Dreieckseite).

| Schaltgruppe (Beispiele) | Wechsel D/Y | Faktor zweipolig | Faktor dreipolig |
|---|---|---|---|
| Dyn5, Dyn11, Yd5, YNd5, YNd11, Yd11 | ja | 2/√3 = 1,155 | 1 |
| Yyn0, YNyn0, Dd0 | nein | 1 | 1 |
| Yzn5, Yzn11 | nein (Zickzack wie Stern) | 1 | 1 |

Gemessen wird dreiphasig, maßgebend ist der größte Leiterstrom. Ist die Schaltgruppe nicht
lesbar, gilt Faktor 1 (ohne Zuschlag, das ist für die Empfindlichkeit die vorsichtige Seite)
mit Hinweis.

**Wo der Faktor wirkt:** Der I>>-Vorschlag arbeitet mit Ik max, also dreipolig, und nutzt
deshalb **Übersetzung und Stufensteller**. Der Schaltgruppenfaktor 2/√3 geht in die
**Empfindlichkeit** ein (Abschnitt 4), weil dort mit Ik min zweipolig gerechnet wird.

### 3.4 Stufenstellerlage in der Zeitprüfung

Zwischen zwei Messorten mit einem Stufensteller dazwischen (z. B. T1 (US) und T1 (OS)) ist
das Stromverhältnis nicht fest. Der Strom am oberen Messort ist f-mal der Strom am unteren,
zusätzlich zur Nennübersetzung, mit f zwischen 1/(1 + s) und 1/(1 − s) (bei s = 16 % also
0,862 bis 1,190, Funktion `netz_umrechnung.tap_spanne`).

- **Zeitprüfung** (`pruefe_paar`): Je Paar wird in der Nennlage und in beiden Extremlagen
  geprüft, es gilt das schlechteste Ergebnis. Eine obere Stufe mit Ansprechwert I regt in der
  Lage f schon bei I/f unten an.
- **Zeitvorschlag** (`_zeit_fuer_stufe`): Die Zeit muss in allen drei Lagen passen. Der Text
  „Bestimmt durch“ nennt die Lage, die den Wert bestimmt hat.
- **Lücken** der Ansprechwerte (oben regt an, unten noch nicht) zählen nur in der Nennlage.
  In den Extremlagen sind sie eine Folge der Stufenstellerlage und werden nicht bewertet.
- Ohne Stufensteller oder ohne Trafo zwischen den Messorten ändert sich nichts.

Der I>>-Vorschlag und die Zeitprüfung sind damit konsistent: Der Vorschlag hält I>> OS auch bei
−16 % um k_S über Ik max der US-Sammelschiene, die Zeitprüfung bestätigt das in der Extremlage.

## 4. Gegenprüfung

| Prüfung | Bedingung | Ampel |
|---|---|---|
| Stromstaffel | I>> oben ≥ k_S · I_Bezug der nächsten Station | grün. Gelb, wenn nicht erfüllt (dann nur über die Zeit selektiv, bei zu kleinem Ik-Gefälle mit entsprechendem Text). Rot nur, wenn der Wert unter dem Anlaufstrom des Motors darunter liegt (die Stufe würde beim Anlauf auslösen). |
| Empfindlichkeit | Ik min hinter der nächsten Station (zweipolig, über Trafos) ≥ γ · kleinster Ansprechwert oben | grün ab γ = 1,5, gelb zwischen 1 und γ, rot darunter |

Fehlt Ik min an einem Knoten, entfällt die Zeile und es gibt einen Hinweis.

## 5. Ergebnis im Referenznetz „Industrie 10 kV“

Bezugsspannung 10 kV, Werksvoreinstellungen aus den Tabs. Einzige Abweichung davon: M1 I>> (50-2) steht im
Referenznetz auf 8,81 × IN (1204 A), siehe Prüfpunkt 4.

| Stufe | Bisher | Bezug | k_S · Bezug | Vorschlag | Status |
|---|---|---|---|---|---|
| L1 Iph>> | 600 A | M1: max(I>> 1204 A, Anlauf 752 A) = 1204 A | 1445 A | 4,82 × IN = 1446 A | angehoben |
| L2 Iph>> | 600 A | Ik max K5 35 kA über T2 = 1400 A | 1680 A | 5,60 × IN = 1680 A | angehoben |
| T2 I>> OS | 1680 A | wie L2 | 1680 A | 1680 A | bleibt |
| T1 I>> OS | 1091 A | Ik max K2 10 kA über T1 mit −16 % = 1082 A bei 110 kV | 1299 A bei 110 kV | 12,38 × IN = 1300 A | angehoben |
| T1 I>> US | 8083 A | Ik max K3 9,1 kA | 10 920 A über Ik max K2 (10 000 A) | 8083 A | nicht wirksam |

Wirkung auf die Zeiten: T1 (OS) braucht 1,0 s statt 1,7 s. Der Abstand zum Netzbetreiber
(1,2 s) beträgt 0,2 s (gelb, über dem Mindestwert) statt −0,5 s (rot). Der volle Soll-
abstand von 0,3 s wird damit noch nicht erreicht.

## 6. Grenzen dieses Stands

- Nur Phasenstufen 50/51. Erdfehlerstufen werden nicht gestaffelt.
- Die Stufenstellerlage wirkt in der Zeitprüfung als Spanne (Abschnitt 3.4). Eine Lage zwischen
  den Extremen wird nicht einzeln geprüft, Nennlage und beide Extremlagen genügen für UMZ.
- Ik am Knoten ist ein Eingabewert. Rückspeisung durch Motoren und Generatoren ist darin
  nicht getrennt ausgewiesen. Generatoren werden in der Staffelung noch nicht berücksichtigt.
- Messung dreiphasig angenommen. Bei Wandlern in nur zwei Phasen kann der größte Leiterstrom
  unbeobachtet bleiben.
- Der Einschaltstrom des Trafos wird nicht für die Stationen darüber nachgerechnet. Er
  steckt nur im Tab-Wert der I>>-Stufe des Trafos selbst.
- Der Vorschlag hebt nur an. Ein Tab-Wert, der höher ist als nötig, wird nicht auf Empfindlichkeit
  optimiert.

## 7. Offene Prüfpunkte („Code ist die Wahrheit“)

| Nr. | Was prüfen | Wo |
|---|---|---|
| 1 | Sitz des Stufenstellers auf der OS-Wicklung (Tool-Vorgabe). Bei Stufensteller auf der US-Seite kehrt sich der Faktor um. | Typenschild und Datenblatt der eingesetzten Trafos |
| 2 | Faktor 2/√3 für den zweipoligen Fehler hinter D/Y: eigene Herleitung, durch Test belegt. Literaturbeleg ergänzen. | Fachliteratur Kurzschlussstromberechnung (Quelle noch zu benennen) |
| 3 | k_S = 1,2 für die Stromstaffelung stammt aus `konstanten_trafo.k_S_IGG`. Die Herkunft dort (7UT613-Handbuch Kap. 2.4) ist in diesem Schritt nicht neu am Handbuch geprüft. | Handbuch 7UT613, Abschnitt Überstromzeitschutz |
| 4 | **Erledigt 11.11.2026 (Referenznetz).** M1 I>> (50-2) stand mit der Werksvoreinstellung 4,0 × IN bei 547 A unter dem Anlaufstrom 752 A. Im Referenznetz jetzt 8,81 × IN = 1204 A (kleinster Faktor mit ≥ 1,6 × Anlaufstrom = 1203 A, Tool-Vorgabe). **Offen:** Der Motor-Default `konstanten_motor.f_50_2_def` = 4,0 liegt für I_A/IN > 2,5 unter dem eigenen Fenster des Motor-Tabs. Das betrifft den Motor-Tab selbst, nicht den Netz-Tab, und ist mit dem Betreuer zu klären. | `beispielnetze/industrie_10kV.json`, `konstanten_motor.py` |
| 5 | **Erledigt 11.11.2026.** Das Feld heißt jetzt „Ik min 2-pol. [kA]“ mit Hilfetext. | `tab_netz.py`, Knoten-Formular |
| 6 | **Erledigt 11.11.2026.** Stufenstellerlage in Zeitprüfung und Zeitvorschlag (Abschnitt 3.4). | `netz_selektivitaet.py` |
| 7 | Δt-Einzelwerte aus `tool_vorgabe_staffelabstand.md`, Abschnitt 5, sind weiter nicht gegen Handbücher geprüft. | Handbücher 7SJ66, 7UT613, 7SA6 |

## Quellen

Dieses Dokument stützt sich auf eigene Herleitungen und auf Werte aus dem bestehenden Tool
(`konstanten_trafo.py`, `calc_trafo.py`, `calc_leitung.py`, `calc_motor.py`). Für die
Ausarbeitung sind Quellen zu Abschnitt 3.3 und zur üblichen Stromstaffelung noch zu
benennen (Prüfpunkte 2 und 3).
