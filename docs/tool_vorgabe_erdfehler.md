# Tool-Vorgabe: Erdfehler (einpoliger Erdkurzschluss) im Strahlennetz

Stand: 25.11.2026 | Gilt für das Nullsystem in `netz_kurzschluss.py`, die Erdstufen in `netz_adapter.py`, `netz_erdfehler.py`, die Erdzeilen in `netz_einstellliste.py`, den Abschnitt „Erdfehler“ in `tab_netz.py` und die Konstanten im Abschnitt „Erdfehler“ von `konstanten_netz.py`

> **Einordnung:** Das Verfahren folgt DIN EN 60909-0 (VDE 0102):2016-12, am 25.11.2026 am
> Normtext geprüft: einpoliger Erdkurzschluss 7.5, Gl. (54), K_T auch im Nullsystem und
> Sternpunkt-Erde-Impedanz ohne K_T (6.3.3, 7.1.2 c), Nullimpedanz von Trafo und Kabel vom
> Hersteller bzw. aus IEC/TR 60909-2 (6.3.1, 6.4). Die übrigen Festlegungen (Erdungspunkt, Staffelung,
> Z0-Annahmen) sind **Tool-Vorgaben**. Die Rechnung ist gegen pandapower 3.5.6 geprüft (Abschnitt 10).

## 1. Entscheidung und Umfang

Gespräch mit dem Betreuer am 25.11.2026: Die Netzausgestaltung soll nicht weiter an Komplexität
gewinnen. Ergänzt wird stattdessen die Fehlerart **Erdfehler**. Am selben Tag festgelegt:

| Frage | Entscheidung |
|---|---|
| Netzform | zuerst nur das **Strahlennetz**. Im Ring wird Ik1 je Lage gerechnet, gestaffelt wird nicht. |
| Erdungspunkt | **Feld am Knoten** „Erdfehlerstrom-Begrenzung [A]“, nur bei niederohmiger Erdung |
| Nullimpedanz der Leitung | eigene Felder R0′ und X0′, ohne Eingabe aus RE/RL und XE/XL der Leitung |
| Testfall | **neues Beispielnetz** `industrie_10kV_noe.json`, das Referenznetz bleibt unverändert |

Die Phasenstaffelung ist von der Erweiterung nicht betroffen. Die Erdstufen stehen in einer
eigenen Liste, die Phasenwerte sind durch Tests gegen den Stand vom 17.11.2026 abgesichert.
Probleme im Nullsystem erzeugen nie einen Fehler, der die Phasenrechnung anhält.

## 2. Einpoliger Kurzschlussstrom

Mit der Ersatzspannungsquelle `c · UN / √3` am Fehlerort und den Impedanzen des Mit-, Gegen- und
Nullsystems am Fehlerort gilt

    Ik1 = 3 · c · UN / √3 / |Z1 + Z2 + Z0|     mit Z2 = Z1 (generatorfern)

Z1 ist dieselbe Kurzschlussimpedanz wie beim dreipoligen Fehler (ohne Motoren). Z0 kommt aus einer
eigenen Knotenadmittanzmatrix des Nullsystems.

| Fall | c | Einspeisung | Trafo | Leitung |
|---|---|---|---|---|
| Ik1 max | c max | Sk max | mit K_T, auch auf Z0T | 20 °C |
| Ik1 min | c min | Sk min | ohne K_T | Endtemperatur wie Ik min, auch R0 |

Motoren: kein Nullsystem (Sternpunkt nicht geerdet). Seit der Normprüfung vom 25.11.2026 zählen
sie bei Ik1 max im Mit- und Gegensystem mit (DIN EN 60909-0, 7.1.2 e und 6.10), bei Ik1 min nicht.

## 3. Nullsystem je Element

| Element | Nullsystem |
|---|---|
| Einspeisung an einem starr geerdeten Knoten | Querzweig Z0Q = X0/X1 · Z1Q. Tool-Vorgabe X0/X1 = 1,0 (Feld `X0_X1_Q`) |
| Trafo, Sternwicklung mit N gegen Dreieck (Dyn, YNd) | Querzweig am Sternknoten: Z0T = 1,0 · Z1T (Tool-Vorgabe `Z0_Z1_Trafo`, Beiblatt 4: 0,8 bis 1,0), dazu 3 · R_E bei niederohmiger Erdung |
| Trafo mit Zickzackwicklung mit N (Yzn, Dzn) | Querzweig am Zickzackknoten: Z0T = 0,1 · Z1T (Beiblatt 4, 2.3), unabhängig von der anderen Seite |
| Trafo YNyn | Längszweig Z0T zwischen beiden Knoten, wenn beide Sternpunkte geerdet sind |
| Trafo Yyn und ähnliche ohne Dreieck | nicht abgebildet, Warnung (Nullimpedanz hängt von der Kernbauart ab) |
| Trafo ohne N auf der Seite des Knotens | kein Nullsystem, das Dreieck sperrt |
| Leitung | Z0 = (R0′ + jX0′) · L. Ohne Eingabe: R0′ = R1′ · (1 + 3 · RE/RL), X0′ = X1′ · (1 + 3 · XE/XL) |
| Kupplung | verbindet wie im Mitsystem |
| Motor | kein Nullsystem |

Ein Sternpunkt mit N an einem starr geerdeten Knoten gilt als starr geerdet. An einem
niederohmigen Knoten gilt nur ein Erdungspunkt (Abschnitt 4).

**Kabel (Beiblatt 4 zu DIN EN 60909-0, Tabelle 9, gelesen 25.11.2026):** Für 10-kV-Einleiterkabel
N2XS2Y (Cu, Dreieck, Kupferschirm, Rückleitung über Schirm und Erde) nennt das Beiblatt bei
150/25 mm² R0/R1 = 5,96 und X0/X1 = 2,93, also R0′ = 0,74 und X0′ = 0,31 Ω/km. Für das
Aluminiumkabel NA2XS2Y 150/25 der Beispielnetze (R1′ = 0,206 Ω/km, gleicher Schirm) folgt
R0′ ≈ 0,206 + (0,74 − 0,124) = 0,82 Ω/km, also R0/R1 ≈ 4,0, und X0′ ≈ 0,31 Ω/km, also
X0/X1 ≈ 2,8. Die Werksvoreinstellung RE/RL = XE/XL = 1,0 (Z0 = 4 · Z1) trifft R0 gut und liegt
bei X0 etwa 40 % zu hoch. Ik1 wird damit etwas zu klein, also auf der sicheren Seite. Die frühere
Abschätzung R0′ ≈ R1′ + 3 · R_Schirm war deutlich zu pessimistisch und ist hiermit überholt. Für ein
echtes Netz R0′ und X0′ aus dem Datenblatt oder aus Beiblatt 4 eintragen.

## 4. Erdungspunkt und Begrenzung

Am Knoten mit Sternpunktbehandlung „niederohmig“ steht die Erdfehlerstrom-Begrenzung I_E. Daraus
folgt der Erdungswiderstand

    R_E = UN / (√3 · I_E)          im Nullsystem 3 · R_E

Regeln:

1. Hängt am Knoten ein Trafo mit herausgeführtem Sternpunkt (YN bzw. yn), sitzt die Erdung an
   dessen Sternpunkt: Z0 = Z0T + 3 · R_E. Bei mehreren gilt der erste nach ID (ein Erdungspunkt je
   Knoten). Dieselbe Regel nutzt der Adapter für den Sternpunktwandler (`erdung_am_trafo`).
2. Sonst gilt die Erdung als **Sternpunktbildner** am Knoten mit Z0 = 3 · R_E. Die Impedanz des
   Sternpunktbildners selbst ist nicht enthalten (gegenüber 3 · R_E klein).
3. Ist der Bereich niederohmig, aber an keinem Knoten steht I_E, gibt es eine Warnung und kein
   Ik1. Ein I_E an einem nicht niederohmigen Knoten wird ignoriert (Hinweis). Das Formular
   übernimmt den Wert dort gar nicht.
4. I_E ist auf c = 1 bezogen. Mit c max = 1,1 liegt Ik1 max am Erdungsknoten etwas darüber
   (Beispielnetz: 2,18 kA bei 2000 A).

Das Referenznetz bleibt im 10-kV-Bereich isoliert. T1 ist YNd5, die 10-kV-Seite also ein Dreieck.
Darum sitzt die Erdung im Beispielnetz an einem Sternpunktbildner an K2.

## 5. Erdungsbereiche

Ein Bereich ist eine galvanisch verbundene Gruppe von Knoten (über Leitungen und Kupplungen). Ein
Trafo trennt die Bereiche, weil das Nullsystem über die Dreieckwicklung nicht übertragen wird. Ein
Erdfehler im 10-kV-Netz ist auf der 110-kV-Seite nicht als Erdstrom zu sehen. Gestaffelt wird nur
innerhalb eines Bereichs.

| Bereich | Bewertung |
|---|---|
| starr oder niederohmig geerdet, Ik1 berechenbar | Erdstufen werden gestaffelt |
| isoliert oder kompensiert | nur Hinweis: Erdschluss mit kleinem Strom, keine Stromstaffelung. Erfassung über U0 bzw. wattmetrisch (Erdschlussstufen der Tabs) |
| geerdet ohne Erdungspunkt | Warnung, kein Ik1 |
| uneinheitliche Sternpunktbehandlung | Hinweis, Ik1 gilt für den ganzen Bereich |

## 6. Erdstufen aus den Betriebsmittel-Tabs

| Element | Stufen | Messort | Wandler | Rechenkern |
|---|---|---|---|---|
| Leitung (7SA6/7SD5) | 3I0>>>, 3I0>>, 3I0> (67N) | speiseseitiger Knoten | Phasenwandler | `calc_leitung.schutz_67N` |
| Motor (7SJ66) | 50N-2, 50N-1 (UMZ), 51N (AMZ) | Anschlussknoten | Phasenwandler (Holmgreen) | `calc_motor.schutz_50N51N` |
| Trafo (7UT613) | IE>>, IE> (UMZ) | Knoten mit geerdetem Sternpunkt | Sternpunktwandler CT_E | `calc_trafo.schutz_5051_erde` |

- Die Leitung liefert Erdstufen nur, wenn ihr Netz geerdet ist und 67N eingeschaltet ist.
  Stufen mit Richtung „Rückwärts“ zählen für Fehler vor dem Schutzort nicht, „Unwirksam“ ist aus.
- Der Motor liefert 50N/51N nur bei niederohmiger Erdung (der Motor-Tab kennt kein starr geerdetes
  Netz und rechnet dort wie bisher mit niederohmig).
- Der Trafo liefert IE> nur, wenn sein Sternpunkt nach Abschnitt 4 geerdet ist und ein
  Sternpunktwandler eingetragen ist. Sonst gibt es einen Hinweis.

**Änderung an zwei Rechenkernen (25.11.2026):** `calc_trafo.schutz_5051_erde` und
`calc_motor.schutz_50N51N` gaben die Zeiten der Erdstufen (und beim Trafo auch die Ansprechwerte)
fest als Werksvoreinstellung zurück. Sie lesen die Werte jetzt aus dem Parametersatz, mit der
Werksvoreinstellung als Rückfall (`I_E`, `t_I_E`, `I_E_HH`, `t_I_E_HH`, `t_50N1`, `t_50N2`,
`T_51N`). Die Tabs setzen diese Schlüssel nicht, dort ändert sich nichts. Ohne diese Änderung
könnte ein Vorschlag nie übernommen werden. Alle neuen Felder stehen im Parameter-Editor unter
„Erdschutz“.

## 7. Staffelung

1. **Fehlerorte:** jeder Knoten eines geerdeten Bereichs mit Ik1 und jeder Motorabgang.
2. **Erdstrom je Schutzort:** aus der Nullsystem-Matrix (`erdstrom_verteilung`). Leitung: 3I0 im
   Zweig, mit Richtung. Trafo: Strom im Sternpunkt. Motor: Ik1 seines Knotens, nur beim Fehler im
   eigenen Abgang.
3. **Reihenfolge:** Schutzort A liegt unter B, wenn B bei allen Fehlern Strom führt, bei denen A
   Strom führt, und bei weiteren. Benachbart sind A und B, wenn kein Schutzort dazwischen liegt.
   Im Strahlennetz mit einem Erdungspunkt ergibt das die Kette vom Fehler zur Erdung.
4. **Paarprüfung:** dieselbe Funktion wie bei den Phasen (`netz_selektivitaet.pruefe_paar`), mit
   gleichem Soll- und Mindestabstand und AMZ-Zuschlag. Grenzstrom ist der größte 3I0 durch A.
5. **Mehrere Erdungspunkte:** Führt B weniger Strom als A, geht das Verhältnis I_B / I_A wie ein
   Stufensteller in die Prüfung ein (kleinstes und größtes Verhältnis, dazu 1,0 als sichere Seite).
   Fließt Erdstrom rückwärts durch eine Leitung, gibt es einen Hinweis statt einer Prüfung.
6. **Gleiche Fehlermengen:** Sehen zwei Schutzorte genau dieselben Fehler, ist die Reihenfolge
   nicht bestimmbar. Es gibt einen Hinweis, sie werden nicht gegeneinander gestaffelt.

## 8. Empfindlichkeit

Der kleinste Ansprechwert eines Schutzortes (AMZ: Anregung 1,1 · Ip) muss mindestens um
γ = 1,5 unter dem kleinsten Erdstrom bei Ik1 min liegen. Das ist derselbe Wert wie bei den Phasen
(`gamma_Reserve`). Grün ab γ, gelb zwischen 1 und γ, rot darunter. Beim Sternpunktwandler eines
Trafos gilt der kleinste Strom im ganzen Bereich (Reserveschutz). Ein Fehlerwiderstand ist nicht
berücksichtigt (Prüfpunkt 6).

## 9. Vorschlag

Wie bei den Phasen von unten nach oben: Jede UMZ-Erdstufe bekommt die kleinste Zeit, die bei jedem
Erdstrom, bei dem sie anregt, einen Staffelabstand über allem liegt, was darunter auslöst.
Gerundet auf 0,05 s. Endpunkte (Schutzorte ohne Schutz darunter, im Beispiel die Motoren und der
Sternpunkt von T2) behalten ihre Zeiten. AMZ-Stufen werden berücksichtigt, aber nicht verändert.
Ansprechwerte ändert der Vorschlag nicht. Bei niederohmiger Erdung ändert sich Ik1 entlang des
Bereichs kaum, eine Stromstaffelung der Erdstufen wäre fast nie wirksam.

**Reihenfolge im Gerät:** Der Leitungs-Tab prüft T(3I0>>>) < T(3I0>>) < T(3I0>). Damit der
Vorschlag dort keine rote Ampel erzeugt, löst eine Stufe mit kleinerem Ansprechwert mindestens
einen Rasterschritt (0,05 s) später aus als die Stufe mit dem nächstgrößeren.

Die Übernahme schreibt nur in die Element-Parameter des Netzmodells, nicht in die Tabs.

**Beispielnetz:** Mit den Werksvoreinstellungen lösen M1 50N-2 und L1 3I0>>> beide nach 0,10 s
aus (rot), ebenso M2 und L2. Der Vorschlag setzt L1 auf 0,40 / 0,45 / 0,80 s und L2 auf
0,40 / 0,45 / 0,50 s (3I0>>> / 3I0>> / 3I0>). Danach haben beide Paare 0,30 s Abstand.

## 10. Gegenrechnung mit pandapower (25.11.2026)

Das Skript `werkzeuge/gegenrechnung_pandapower.py` baut beide Beispielnetze in pandapower 3.5.6
nach (`fault = "1ph"`). Der Sternpunktbildner ist dort ein YNd-Trafo an K2 mit sehr kleiner
Streuimpedanz und `rn_ohm = R_E`. pandapower wendet K_T auf Z0T an, aber nicht auf die
Sternpunktimpedanz, genau wie das Tool.

| Knoten | Ik1 max Tool = pandapower [kA] | Ik1 min [kA] | Netz |
|---|---|---|---|
| K1 | 16,128 | 8,143 | niederohmig (16,108 im Referenznetz) |
| K2 | 2,177 | 1,974 | niederohmig |
| K3 | 2,032 | 1,787 | niederohmig |
| K4 | 1,850 | 1,585 | niederohmig |
| K5 | 37,450 | 30,291 | niederohmig (37,292 im Referenznetz) |

Stand nach der Normprüfung vom 25.11.2026 (Ik1 max mit den Motoren M1 und M2, Ik1 min mit den
Endtemperaturen der Leitungen).

Abweichung an allen Knoten 0,00 %. Im Referenznetz sind K2 bis K4 isoliert, beide Programme
liefern dort keinen Strom. Die Werte sind in `test_netz_nullsystem.py` eingefroren.

**Aussagekraft:** wie bei der dreipoligen Rechnung. Die Gegenrechnung zeigt dieselbe Umsetzung,
nicht dass beide die Norm richtig umsetzen. Die Verteilung des Erdstroms auf die Zweige ist im
Strahlennetz eine einfache Reihenschaltung und durch Tests mit Handrechnung abgesichert.

## 11. Grenzen

- Nur Strahlennetz. Im Ring gibt es Ik1 je Trennstellenlage, aber keine Erdstaffelung.
- Nur die Erdstufen. Bei starrer Erdung kann Ik1 größer als Ik3 sein (Beispiel K5: 37,0 gegen
  34,9 kA). Die Phasenstaffelung rechnet weiter mit Ik3 als größtem Strom.
- Kein Fehlerwiderstand, keine Leitungskapazitäten (kapazitiver Erdschlussstrom).
- Der Sternpunktbildner hat im Tool keinen eigenen Schutz.
- Generatoren fehlen wie in der dreipoligen Rechnung.
- Isolierte und kompensierte Netze: nur Hinweis, keine Bewertung der U0- und
  Wattmetrie-Stufen.

## 12. Offene Prüfpunkte

| Nr. | Punkt | Stand |
|---|---|---|
| 1 | Ik1-Formel und Spannungsfaktor am Normtext bestätigen | erledigt 25.11.2026: 7.5, Gl. (54), Tabelle 1 |
| 2 | Z0T = 1,0 · Z1T für Trafos mit Dreieckwicklung | Beiblatt 4 (25.11.2026): YNd 0,8 bis 1,0, Yzn 0,1 (eingebaut). Für ein echtes Netz aus dem Prüfprotokoll, Felder `R0_R_T`, `X0_X_T` |
| 3 | R0′/X0′ der Kabel aus dem Datenblatt (Schirmquerschnitt, Erdung des Schirms) | Beiblatt 4, Tabelle 9 (25.11.2026): Default trifft R0, X0 etwa 40 % zu hoch (Abschnitt 3) |
| 4 | X0/X1 der Einspeisung | Tool-Vorgabe 1,0, für ein echtes Netz Ik1″ vom Netzbetreiber |
| 5 | Adressen der Erdstufen: Trafo IE 2411 bis 2414 (aus den Kommentaren in `konstanten_trafo.py`, nur 1-A-Sternpunktwandler) und Motor-Zeiten 1303, 1305, 1308 (aus der Sollwerttabelle in `tab_motor.py`) gegen das Handbuch prüfen | offen |
| 6 | Fehlerwiderstand bei der Empfindlichkeit | nicht berücksichtigt |
| 7 | Mindestabstand 0,05 s zwischen den Stufen eines Geräts | Tool-Vorgabe passend zur Plausibilität im Leitungs-Tab |
| 8 | Erdstaffelung im Ring | später |

## Quellen

[1] IEC 60909-0:2016 bzw. DIN EN 60909-0 (VDE 0102):2016-12, Kurzschlussströme in
Drehstromnetzen. Normtext nicht gelesen, Verfahren nach den Sekundärquellen in
`tool_vorgabe_kurzschluss.md`.

[2] pandapower 3.5.6, Modul `pandapower.shortcircuit` mit `fault = "1ph"`, Nullsystem in
`pd2ppc_zero.py` (Sternpunktimpedanz `rn_ohm`/`xn_ohm`, nach K_T addiert).
https://www.pandapower.org

[3] Lehrbuch „Elektrische Energieversorgung“ (vorliegende Datei), Abschnitte zu symmetrischen
Komponenten und Sternpunktbehandlung. Abschnittsnummern vor dem Zitieren am Buch ergänzen.

[4] DIN EN 60909-0 Beiblatt 4 (VDE 0102 Beiblatt 4):2009-08 (IEC/TR 60909-2:2008), Daten
elektrischer Betriebsmittel. Gelesen am 25.11.2026: 2.3 mit Tabelle 2 (Nullreaktanzen der
Trafos), 2.5 mit Tabelle 9 (10-kV-Kabel N2XS2Y), 2.6 mit Tabelle 16 (Asynchronmotoren).
