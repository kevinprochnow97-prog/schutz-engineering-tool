# Tool-Vorgabe: Kurzschlussströme aus den Netzdaten

Stand: 16.11.2026 | Gilt für `netz_kurzschluss.py`, die Konstanten im Abschnitt „Kurzschlussstromberechnung“ von `konstanten_netz.py`, den Schalter `ik_ergaenzen` in `netz_ring.py` und den Abschnitt „Kurzschlussströme aus den Netzdaten“ in `tab_netz.py`

> **Einordnung:** Das Verfahren ist eine **vereinfachte Rechnung in Anlehnung an IEC 60909-0**
> (DIN EN 60909-0, VDE 0102). Die Faktoren und Formeln sind am 16.11.2026 gegen Sekundärquellen
> geprüft worden (Lehrbuch, Fachaufsatz zur Ausgabe 2016, Kabeldatenblätter, siehe Abschnitt 8
> und Quellen). **Der Normtext selbst lag nicht vor.** Vor dem Zitieren in der Ausarbeitung sind
> die Angaben an der Norm zu bestätigen. Das Tool ersetzt keine normgerechte
> Kurzschlussstromberechnung.

## 1. Zweck und Grundsatz

Bisher waren Ik max und Ik min an jedem Knoten Eingabewerte. Das Modul rechnet sie aus den Daten,
die das Netzmodell ohnehin enthält, und stellt sie neben die eingegebenen Werte.

**Ein von Hand eingegebener Wert hat immer Vorrang.** Das Modul schreibt nie in das Netzmodell.
Berechnete Werte stehen in einem eigenen Ergebnisobjekt (`KurzschlussErgebnis`). Nur an Knoten
**ohne** Eingabewert rechnet die Staffelung mit dem berechneten Wert, und zwar auf einer Kopie des
Netzes (`ergaenze_ik`). Die Oberfläche nennt diese Knoten ausdrücklich. Das Referenznetz bleibt
damit auf seinen eingegebenen Werten, alle Handrechnungen der bisherigen Tests gelten weiter.

Die Rechnung ist in der Oberfläche ein Schalter und in der Voreinstellung aus. Ohne Schalter
verhält sich der Netz-Tab wie zuvor.

## 2. Verfahren

Ersatzspannungsquelle `c · UN / √3` am Fehlerort, alle anderen Quellen sind kurzgeschlossen. Es
wird nur das Mitsystem gerechnet. Die Impedanzen stehen in bezogenen Größen (S_B = 100 MVA,
U_B = Nennspannung des jeweiligen Knotens). Das entspricht der Umrechnung über das Verhältnis der
Knoten-Nennspannungen, wie sie `netz_selektivitaet.auf_bezug()` für Ströme macht.

Aus allen eingeschalteten Elementen entsteht die Knotenadmittanzmatrix Y. Die Kurzschlussimpedanz
am Knoten k ist das Diagonalelement von Y⁻¹. Im Strahlennetz ist das exakt die Reihensumme der
Impedanzen bis zur Einspeisung. Die Tests prüfen das an 60 zufälligen Strahlenketten und am
Referenznetz von Hand. Die Matrix wurde gewählt, weil sie ohne Änderung auch Motoren als zweite
Quelle und den geschlossenen Ring rechnet.

    Ik3 = c · UN / (√3 · |Zk|)          Ik2 = √3/2 · Ik3

### Impedanzen je Betriebsmittel

| Element | Formel | Daten aus dem Netzmodell | Annahme, wenn nichts angegeben |
|---|---|---|---|
| Einspeisung | Z_Q = c · UN² / Sk″ | `Sk_max_MVA`, `Sk_min_MVA` | R_Q/X_Q = 0,1 (`RX_Q`) |
| Trafo | Z_T = uk · UN² / Sn · K_T | `Sn_MVA`, `uk_pct` | R_T = 0 (`ukr_pct`), Mittelstellung |
| Leitung | Z_L = (R′ + jX′) · L | `L_km`, `X_Belag`, `phi_Ltg` | R′ = X′/tan φ wie `calc_leitung` (`R_Belag` hat Vorrang) |
| Kupplung | Z = 0 | keine | beide Knoten zählen als ein Knoten |
| Motor | Z_M = UN / (√3 · I_Anlauf) | Anlaufstrom aus `calc_motor.grundgroessen` | R_M/X_M = 0,10 über 1 kV, 0,42 bis 1 kV (`RX_M`) |

In Klammern steht jeweils der optionale Parameter, mit dem die Annahme im Element überschrieben
werden kann. Keiner davon ist ein Pflichtfeld, beide Beispielnetze rechnen ohne neue Eingaben.

### Ik max und Ik min

| | Ik max | Ik min |
|---|---|---|
| Fehlerart | dreipolig | zweipolig (√3/2 · Ik3) |
| Spannungsfaktor über 1 kV | 1,10 | 1,00 |
| Spannungsfaktor bis 1 kV | 1,10 | 0,90 |
| Einspeisung | Sk max | Sk min |
| Netzimpedanz Z_Q | mit c max | mit c min |
| Leiterwiderstand | 20 °C | 90 °C: R · (1 + 0,004/K · 70 K) = R · 1,28 |
| Motoren | Hauptwert ohne, Zusatzwert mit | ohne |

## 3. Annahmen und Entscheidungen (16.11.2026)

1. **Korrekturfaktor K_T.** `K_T = 0,95 · c_max / (1 + 0,6 · x_T)`, mit x_T als bezogener Reaktanz
   und c_max der Unterspannungsseite. Er wirkt auf die Trafoimpedanz in beiden Fällen. Schalter
   `KT_anwenden` in `konstanten_netz.py`. Für T1 (uk 12 %) ergibt sich 0,9748, die Ströme hinter T1
   liegen damit rund 2,4 % über den Handwerten des Referenznetzes, die ohne K_T entstanden sind.
2. **Motorbeitrag getrennt.** Der Hauptwert Ik max ist der netzseitige Strom ohne Motoren. Das ist
   der Strom, den die vorgelagerten Schutzgeräte bei einem Fehler führen, und damit der richtige
   Bezug für die Stromstaffelung. Der Wert mit Motoren steht als Information daneben (im
   Referenznetz an K3 rund 0,83 kA mehr). Er wäre für die Bemessung der Schaltanlage maßgebend, die
   das Tool nicht prüft.
3. **Geschlossener Ring** wird zusätzlich zu den Trennstellenlagen gerechnet. Er ist kein
   Betriebszustand der Staffelung, liefert aber den größten Ik max an den Ringknoten (kurzzeitig
   beim Umschalten ohne Unterbrechung). Die Topologie meldet den geschlossenen Betrieb weiter als
   Fehler.
4. **Handwert im Ring.** Ein eingegebener Wert gilt streng genommen nur für eine Trennstellenlage.
   Die Ringstaffelung rechnet trotzdem in allen Lagen mit den eingegebenen Werten (wie bisher). Die
   Oberfläche zeigt die berechneten Werte je Lage und warnt, wenn eine Lage mehr als 10 % vom
   eingegebenen Wert abweicht (`Ik_Abweichung_Hinweis`, die Hälfte der Sicherheit k_S = 1,2).
5. **Leitertemperatur 90 °C** für Ik min, α = 0,004/K. Der Widerstandsbelag aus den Elementdaten
   gilt als Wert bei 20 °C. Je Leitung über `theta_min_C` änderbar. **Geändert nach der
   Quellenprüfung** (zuerst 80 °C): Die Norm verlangt die Leitertemperatur am Ende des
   Kurzschlusses. 90 °C ist die höchste zulässige Betriebstemperatur der VPE-Kabel [5, 6] und
   damit die untere Grenze für ein vorbelastetes Kabel. Die Erwärmung durch den Kurzschluss
   selbst (zulässig bis 250 °C [6]) ist nicht enthalten, Ik min ist insoweit eher zu groß. Der
   Einfluss ist im Referenznetz klein (K4: 5,90 statt 5,93 kA).
6. **Spannungsfaktor Niederspannung 1,10 und 0,90.** 1,10 gilt für Netze mit 10 %
   Spannungstoleranz, also 400/230 V [1, 3]. Er passt zum eingegebenen Wert an K5 (berechnet
   35,1 kA ohne K_T, mit 1,05 wären es 33,5 kA). **Geändert nach der Quellenprüfung:** c min war
   zuerst 0,95. Für Netze mit 10 % Toleranz nennen die Quellen zur Ausgabe 2016 den Wert 0,90
   [2, 3], 0,95 gehört zur Toleranz 6 % und zur Ausgabe 2001 [1, 4]. Betroffen ist nur K5
   (Ik min 24,6 statt 25,9 kA).
7. **Knoten ohne Handwert** rechnen in der Staffelung mit dem berechneten Wert, sichtbar benannt.
   Im Ring wird je Lage ergänzt (`ik_ergaenzen` in `netz_ring.py`, Voreinstellung aus).
8. **Generatoren** werden nicht gerechnet. Das Modul meldet das je Generator.

## 4. Vernachlässigungen

- Leitungskapazitäten, Querzweige und Lastströme vor dem Fehler.
- Lichtbogen- und Fehlerwiderstand (Ik min ist dadurch eher zu groß).
- Einfluss des Stufenstellers auf die Trafoimpedanz. Die Übersetzung in ungünstigster Lage geht
  weiter als Faktor auf den Strom in `netz_umrechnung.py` ein.
- Nullsystem und damit alle Erdfehler. Ik min ist der zweipolige Fehler ohne Erdberührung.
- Stoßkurzschlussstrom ip, Ausschaltstrom Ib, thermischer Strom Ith, Gleichstromglied.
- Abklingen des Motorbeitrags. Gerechnet ist der Anfangswert.
- Abweichung der Trafo-Bemessungsspannungen von den Knoten-Nennspannungen.
- Zweipolig = √3/2 · dreipolig setzt Z₂ = Z₁ voraus (generatorfern).

## 5. Ergebnis in den Beispielnetzen

Referenznetz, Ik max / Ik min zweipolig in kA:

| Knoten | eingegeben | berechnet ohne K_T | berechnet mit K_T (Voreinstellung) | mit Motoren |
|---|---|---|---|---|
| K1 | 15,7 / 6,8 | 15,75 / 6,82 | 15,75 / 6,82 | 15,82 |
| K2 | 10,0 / 7,5 | 9,98 / 7,50 | 10,22 / 7,68 | 11,04 |
| K3 | 9,1 / 6,8 | 9,08 / 6,81 | 9,27 / 6,95 | 10,10 |
| K4 | 7,9 / 5,8 | 7,86 / 5,81 | 8,00 / 5,90 | 8,45 |
| K5 | 35,0 / – | 35,08 / 24,67 | 34,95 / 24,58 | 35,30 |

Ohne K_T treffen die berechneten Werte die eingegebenen auf unter 1 % (Test
`test_referenznetz_handrechnung`).

Beispielring, mit K_T, Ik max / Ik min in kA:

| Schaltzustand | K3 | K4 |
|---|---|---|
| eingegeben | 9,10 / 6,80 | 7,90 / 5,80 |
| K34 offen (Ausgangslage) | 9,27 / 6,95 | 8,00 / 5,90 |
| L1 offen | 8,00 / 5,90 | 8,00 / 5,90 |
| L2 offen | 9,27 / 6,95 | 9,27 / 6,95 |
| Ring geschlossen | 9,56 / 7,17 | 9,56 / 7,17 |

In der Lage „L2 offen“ liegt Ik max an K4 um 17 % über dem eingegebenen Wert, in der Lage
„L1 offen“ an K3 um 12 % darunter. Die Stromstaffelung hat mit k_S = 1,2 nur 20 % Sicherheit, die
Empfindlichkeitsprüfung arbeitet mit Ik min. Beide sind in diesen Lagen mit den eingegebenen Werten
nicht belastbar. Das ist der Grund für Prüfpunkt 8.

## 6. Robustheit

Das Modul wirft nie. Fehlende Daten führen zu Meldungen und zu **keinem** Wert statt zu einem
geschätzten:

- `Sk_max_MVA` oder `Sk_min_MVA` fehlt: der jeweilige Fall wird nicht berechnet.
- Trafo ohne `Sn_MVA` oder `uk_pct`, Leitung ohne `L_km` oder `X_Belag`: Knoten dahinter ohne Wert.
- Liegt ein solches Element parallel zu einem berechneten Weg (geschlossener Ring), wäre jedes
  Ergebnis falsch. Dann gibt es gar kein Ergebnis und eine Fehlermeldung.
- Leitung ohne Widerstandsangabe: gerechnet mit R′ = 0 und Warnung, weil Ik min dann zu groß ist.
- Ein berechneter Wert, der zum Handwert der anderen Größe nicht passt (Ik min über Ik max), wird
  nicht eingesetzt und gemeldet.

## 7. Grenzen

- Eine oder mehrere Netzeinspeisungen rechnet die Matrix, die Topologie lässt bisher nur eine zu.
- Die Ringstaffelung nutzt die berechneten Werte je Lage nur an Knoten ohne Handwert.
- Kein Abgleich mit einem Netzberechnungsprogramm. Die Gegenprüfung ist die Handrechnung.

## 8. Prüfpunkte („Code ist die Wahrheit“)

Stand der Quellenprüfung vom 16.11.2026. „Bestätigt“ heißt: durch die genannten Sekundärquellen
gedeckt. Die Bestätigung am Normtext steht bei allen Punkten noch aus (Punkt 11).

| Nr. | Was | Stand | Quelle |
|---|---|---|---|
| 1 | Spannungsfaktoren über 1 kV: c max 1,10, c min 1,00 | Bestätigt | [1, Abschnitt 6.1.1.1 und Gl. 6.13], [2], [3], [4] |
| 1b | Spannungsfaktoren bis 1 kV: c max 1,05 (Toleranz 6 %) oder 1,10 (10 %, 400/230 V), c min 0,95 oder 0,90 | Teilweise bestätigt, die Quellen weichen bei c min voneinander ab: [1] und [4] nennen 0,95, [2] und [3] für 10 % Toleranz 0,90. Tool rechnet mit 1,10 und 0,90. Am Normtext klären. | [1], [2], [3], [4] |
| 2 | Netzimpedanz Z_Q = c · UN² / Sk″, für Ik min mit c min, R_Q = 0,1 · X_Q und X_Q = 0,995 · Z_Q, wenn nichts bekannt ist | Bestätigt | [2, Gl. 1 bis 3], [4, Gl. 1] |
| 3 | K_T = 0,95 · c max / (1 + 0,6 · x_T), c max der Unterspannungsseite | Formel bestätigt. Offen: Anwendung auch beim kleinsten Kurzschlussstrom (Tool: ja). [2] merkt an, dass K_T bei Verteiltransformatoren vernachlässigt werden kann. | [4, Gl. 4 und 5], [2] |
| 3b | Stufensteller: Rechnung mit der Bemessungsübersetzung | Bestätigt | [1, Abschnitt 6.1.1.2] |
| 4 | Leiterwiderstand für Ik min: R = R20 · [1 + α · (θe − 20 °C)], α = 0,004/K, θe = Leitertemperatur am Ende des Kurzschlusses | Formel bestätigt. θe = 90 °C ist eine Tool-Vorgabe (Betriebstemperatur laut [5, 6]). [2] rechnet in Beispielen mit 80 °C und 160 °C, [4] mit 90 °C für Kabel. Offen: begründeter Wert für die Endtemperatur. | [2, Gl. 21], [4, Gl. 3], [5], [6] |
| 5 | Asynchronmotor: Z_M = UrM² / (I_LR/I_rM · S_rM), R_M/X_M = 0,10 über 1 kV ab 1 MW je Polpaar, 0,15 darunter, 0,42 bis 1 kV | Bestätigt. Das Tool kennt die Polpaarzahl nicht und nimmt über 1 kV immer 0,10 (für M1 mit 2 MW richtig bis zwei Polpaare, sonst `RX_M` setzen). | [2, Gl. 23 und 24], [1, Gl. 6.33] |
| 5b | Wann Motoren zählen: nach [1] gesondert zu erfassen, wenn ihr Anteil 5 % übersteigt. M1 liefert an K3 rund 9 %. Das Tool weist den Wert mit Motoren deshalb aus. | Bestätigt | [1, Abschnitt 6.3], [3] |
| 6 | Zweipoliger Kurzschluss = √3/2 · dreipolig und Faktor 2/√3 hinter D/Y | Offen, in dieser Runde nicht nachgelesen | [1, Abschnitt 10.3.2] |
| 7 | Sk″ max, Sk″ min und R/X am Übergabepunkt | Offen, Angabe des Netzbetreibers | Netzbetreiber |
| 8 | Entscheidung: Ringstaffelung je Lage mit berechneten statt eingegebenen Werten (löst Prüfpunkt 3 in `tool_vorgabe_ring.md`) | Offen | Betreuer |
| 9 | Kabeldaten des Referenznetzes: R′ = 0,206 Ω/km für 150 mm² Al | Bestätigt (Leiterwiderstand laut Datenblatt, 3x1x150/25, 6/10 kV). Offen: X′ = 0,11 Ω/km, beide Datenblätter nennen keine Reaktanz. | [5] |
| 10 | Gegenrechnung mit einem Netzberechnungsprogramm oder einem durchgerechneten Normbeispiel | Offen | IEC TR 60909-4 |
| 11 | Alle bestätigten Punkte am Normtext nachschlagen und mit Abschnitt und Gleichungsnummer zitieren | Offen, die Norm lag nicht vor | DIN EN 60909-0 (VDE 0102):2016-12 |

## Quellen

[1] Lehrbuch „Elektrische Energieversorgung. Erzeugung, Übertragung und Verteilung elektrischer
Energie für Studium und Praxis“ (vorliegende Datei, Autoren und Auflage dem Buch entnehmen).
Abschnitt 6.1.1.1 (Spannungsfaktoren, kleinster Kurzschlussstrom), Gl. 6.13, Abschnitt 6.1.1.2
(Bemessungsübersetzung), Abschnitt 6.3 mit Gl. 6.33 (Asynchronmotor), Abschnitt 10.3.2.

[2] Fachaufsatz zur Kurzschlussstromberechnung nach DIN EN 60909-0 (VDE 0102):2016, Zeitschrift
„de“, Heft 19/2017, Langversion.
https://www.elektro.net/file/show/124844/ef6e94/DE_2017_19_EI41_Langversion_neu.pdf

[3] TÜV SÜD: Kurzschlussstromberechnung, mit Bezug auf DIN EN 60909-0 (VDE 0102):2016-12.
https://www.tuvsud.com/de-de/indust-re/elektrotechnik-info/kurzschlussstromberechnung

[4] Vectorized Calculation of Short Circuit Currents Considering Distributed Generation. An Open
Source Implementation of IEC 60909. arXiv:1802.01502. https://arxiv.org/pdf/1802.01502

[5] Klaus Faber AG: Datenblatt Mittelspannungskabel NA2XS(F)2Y 3-fach verseilt, Ausgabe
14.11.2026 (Leiterwiderstand, höchste zulässige Leitertemperatur 90 °C).

[6] HELUKABEL: Datenblatt NA2XS2Y 6/10 kV, 12/20 kV, 18/30 kV, Stand 04.08.2021 (zulässige
Betriebstemperatur am Leiter 90 °C, Kurzschlusstemperatur 250 °C bei höchstens 5 s).

Die Angaben aus [2] bis [4] stammen aus einer Online-Recherche über Textauszüge. Formeln, die dort
als Bild gesetzt sind, konnten nicht gelesen werden. Vor dem Zitieren am Original prüfen.
