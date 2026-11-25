# Tool-Vorgabe: Staffelabstand Δt für die netzweite Zeitstaffelung

Stand: 17.11.2026 | Gilt für `konstanten_netz.py` und `netz_selektivitaet.py`

> **Einordnung:** Der Staffelabstand ist keine Werksvoreinstellung eines Geräts.
> Er ist eine **Tool-Vorgabe**, die aus Literatur hergeleitet ist. Die Einzelwerte
> müssen vor einer Verwendung in der Ausarbeitung gegen die Technischen Daten der
> eingesetzten Geräte und Schalter geprüft werden (Abschnitt 5).

## 1. Ansatz

Für unabhängige Überstromzeitstufen (UMZ) numerischer Schutzgeräte setzt sich der
Staffelabstand aus vier Anteilen zusammen [1, Gl. 8.2.2]:

    Δt = t_LS + t_Rück + 2 · t_Tol + t_Sich

| Anteil | Bedeutung | Warum er eingeht |
|---|---|---|
| t_LS | Ausschaltzeit des Leistungsschalters inkl. Lichtbogenzeit | So lange fließt der Fehlerstrom nach dem AUS-Kommando des unteren Schutzes weiter. |
| t_Rück | Rückfallzeit (Überlaufzeit) des oberen Schutzes | Fällt der Strom erst kurz vor Ablauf der Verzögerung weg, kann der obere Schutz sein Kommando nicht mehr zurücknehmen. |
| 2 · t_Tol | Zeittoleranz der Verzögerung, einmal je Gerät | Ungünstigster Fall: der untere Schutz ist zu langsam und der obere zu schnell. |
| t_Sich | Sicherheitszuschlag | Verzögerte Anregung durch Wandlersättigung (Gleichstromglied), Hilfsrelais im Auslösekreis. |

## 2. Zahlenwerte im Tool

| Größe | Konstante | Wert | Quelle und Begründung |
|---|---|---|---|
| t_LS | `dt_t_LS` | 80 ms | Konservativ gegenüber dem Beispielwert 50 ms in [1]. Gleiche Annahme wie beim Schalterversagerschutz im Generator-Tab (`konstanten_gen.py`, Hinweis zu Adr. 7004: t_LS_max ca. 80 ms). |
| t_Rück | `dt_t_Rueck` | 35 ms | Größter Wert der eingesetzten Geräte: 7UT613 ca. 35 ms (Handbuch Kap. 4.4), 7SJ66 und 7SA6 ca. 30 ms. Geändert am 16.11.2026, vorher 30 ms (Beispielwert in [1]). Numerische Relais nach [2, Tab. 9.2]: Überlaufzeit 20 ms. |
| t_Tol | `dt_t_Tol` | 25 ms | Beispielwert in [1]. Konservativ gegenüber der typischen SIPROTEC-Angabe „1 % vom Einstellwert bzw. 10 ms“ [4]. |
| t_Sich | `dt_t_Sich` | 20 ms | Etwa eine Netzperiode bei 50 Hz, nach [1] der kleinste sinnvolle Wert. |
| Summe | `dt_summe()` | 185 ms | 80 + 35 + 2 · 25 + 20 |
| **Mindestwert** | `dt_Staffel_min` | **0,20 s** | Summe, auf das Einstellraster 0,05 s aufgerundet. |
| **Sollwert** | `dt_Staffel_soll` | **0,30 s** | Siehe Abschnitt 3. |

Zum Vergleich das Rechenbeispiel aus [1]: 2 · 25 + 50 + 30 + 20 = 150 ms. Der
Unterschied zum Tool kommt allein aus der längeren Schalterzeit.

## 3. Warum 0,30 s als Sollwert und nicht 0,20 s

- [2, Tab. 9.2] nennt für numerische Relais einen typischen Gesamtstaffelabstand von 0,3 s.
- Siemens-Autoren geben für den Reserveschutz 300 bis 400 ms je weiterer Staffelstufe an [3].
- Der Trafo-Tab arbeitet bereits mit `dt_Staffel = 0,30 s` (typ. 0,25 bis 0,40 s). Ein Test stellt sicher, dass beide Werte gleich bleiben.
- Die Reserve von 0,10 s gegenüber dem Mindestwert deckt langsamere Schalter und unterschiedlich gesättigte Wandler ab. Nach [1] ist der Sicherheitszuschlag zu erhöhen, wenn die Überstromziffern der Wandler in der Kette stark voneinander abweichen.

## 3a. AMZ gegen AMZ und AMZ gegen UMZ (Punkt 7, umgesetzt 17.11.2026)

Der feste Anteil 2 · t_Tol gilt für UMZ-Stufen. Bei einer abhängigen Kennlinie (AMZ) ist die
Toleranz der Auslösezeit ein **Anteil der Zeit selbst**, der nötige Abstand wächst also mit der
Auslösezeit [1, Gl. 8.2.3]. Das Tool nimmt die Toleranz aus den Technischen Daten des 7SJ66 [5]:
Auslösezeit für 2 ≤ I/Ip ≤ 20 „5 % vom berechneten Wert + 2 % Stromtoleranz, oder 30 ms“.

    Tol_AMZ(I) = max( 5 % · t(I) + |t(I · (1 ∓ 2 %)) − t(I)| ; 30 ms ; t_Tol )
    Zuschlag(I) = (Tol_unten(I) − t_Tol) + (Tol_oben(I) − t_Tol)
    Soll(I) = Δt_soll + Zuschlag(I)        Mindestwert(I) = Δt_min + Zuschlag(I)

- Ungünstige Richtung: Der untere Schutz misst 2 % zu wenig Strom (langsamer), der obere 2 % zu
  viel (schneller).
- Bei UMZ bleibt die Toleranz t_Tol = 25 ms, der Zuschlag ist null. UMZ gegen UMZ ist unverändert.
- Geprüft wird an jedem Prüfstrom. Maßgebend ist die kleinste **Reserve** (Abstand minus Zuschlag),
  nicht der kleinste Abstand. Die Staffeltabelle zeigt den Zuschlag in einer eigenen Spalte.
- Der Staffelvorschlag rechnet den Zuschlag mit ein. Für eine UMZ-Stufe über einer AMZ-Stufe
  ergibt sich die Zeit aus t_unten + Δt_soll + Zuschlag. AMZ-Stufen selbst verändert der Vorschlag
  weiterhin nicht.
- Größenordnung: Normal invers bei 1,5 · Ip und T = 0,1 (t = 1,72 s): Zuschlag 0,15 s. Bei kurzen
  AMZ-Zeiten (unter etwa 0,5 s) greift nur der Mindestwert 30 ms, der Zuschlag ist 5 ms je Gerät.
- Im Beispielnetz ändert sich nichts: Beim kritischen Strom greift am Motor die UMZ-Stufe 50-1
  (0,5 s) vor der AMZ-Stufe Ip.

**Tool-Vorgaben:** Die Toleranz des 7SJ66 gilt für alle AMZ-Stufen, auch unterhalb von 2 · Ip, wo
das Handbuch keinen Wert nennt. Die Stromtoleranz wirkt über die Steilheit der Kennlinie, dicht an
der Anregeschwelle (1,1 · Ip) wird sie sehr groß. Liegt der um 2 % verschobene Strom unter der
Anregeschwelle, rechnet das Tool nur mit dem Zeitanteil.

## 4. Umsetzung als Ampel

| Kleinster Abstand zwischen zwei benachbarten Schutzorten | Ampel |
|---|---|
| Δt ≥ 0,30 s | OK (grün) |
| 0,20 s ≤ Δt < 0,30 s | Hinweis (gelb): technisch möglich, aber ohne Reserve |
| Δt < 0,20 s | Prüfen! (rot): Selektivität nicht gesichert |

Beide Schwellen sind Parameter von `pruefe_selektivitaet()` und lassen sich später
im Netz-Tab einstellbar machen.

## 5. Offene Prüfpunkte („Code ist die Wahrheit“)

| Nr. | Was prüfen | Wo |
|---|---|---|
| 1 | Zeittoleranz der UMZ-Verzögerung und Rückfallzeit. **Geprüft 16.11.2026:** Zeittoleranz in allen drei Handbüchern 1 % vom Einstellwert bzw. 10 ms, die 25 ms des Tools sind damit konservativ. Rückfallzeit 7SJ66 ca. 30 ms (Grundschwingung), 7SA6 ca. 30 ms, **7UT613 ca. 35 ms** bei 50 Hz. `dt_t_Rueck` ist deshalb seit dem 16.11.2026 auf 35 ms gesetzt (Summe 185 ms, Mindestwert nach der Rundung unverändert 0,20 s). **7SD5 geprüft 17.11.2026:** Rückfallzeit der Phasen-Überstromstufen ca. 30 ms (Handbuch C53000-G1100-C169-6, Kap. 4.16, Hoch- und Überstromstufen), Zeittoleranz 1 % bzw. 10 ms. Beides durch die 35 ms und 25 ms des Tools abgedeckt, `dt_t_Rueck` bleibt 35 ms. | 7SJ66 Handbuch C53000-B1140-C383-D (09.2023), Kap. 4.2. 7SA6 Handbuch, Kap. 4.11. 7UT613 Handbuch C53000-G1100-C160-3, Kap. 4.4 |
| 2 | Ausschaltzeit der eingesetzten MS-Leistungsschalter. **Geprüft 17.11.2026 an zwei Herstellerangaben:** Siemens Vakuum-Leistungsschalter 3AE8, 12 kV: Ausschalteigenzeit ≤ 30 ms, Lichtbogenzeit ≤ 15 ms, zusammen ≤ 45 ms. DRIESCHER Vakuum-Leistungsschalter 747, 12 kV: Ausschaltzeit ca. 65 ms. Die 80 ms des Tools decken beide ab, `dt_t_LS` bleibt. Für ein reales Netz gilt das Datenblatt des eingebauten Schalters. | Siemens Datenblatt 3AE8 12 kV (infrastructure-cities.siemens.com.cn, 3159 EN 3AE8); DRIESCHER Betriebsanleitung B747, Technische Daten (driescher.de) |
| 3 | Anregeschwelle der AMZ-Stufen (Tool: 1,1 · Ip). **Bestätigt 16.11.2026:** 7SJ66 nennt für die IEC-Kennlinien eine Anregeschwelle von ca. 1,10 · Ip. | 7SJ66 Handbuch C53000-B1140-C383-D (09.2023), Kap. 4.3. Achtung: [1] nennt für die Norm 1,3. |
| 4 | Kennlinienkonstanten AMZ (0,14 / 0,02 usw.) | IEC 60255-151 bzw. Handbuch 7SJ66. Stimmen mit [1, Tab. 8.2.1] überein. |
| 5 | Bei AMZ gegen AMZ reicht ein fester Abstand streng genommen nicht. **Umgesetzt 17.11.2026** (Abschnitt 3a), Toleranz aus [5]. Offen: (a) Form von [1, Gl. 8.2.3] am Original gegenlesen, (b) Toleranz unterhalb 2 · Ip ist Tool-Vorgabe, (c) Toleranzen anderer AMZ-Geräte, falls im Netz eingesetzt. | [1], [5] |

## Quellen

[1] ABB Oy: Distribution Automation Handbook, Section 8.2 Relay Coordination. 1MRS757285, Rev. A, 2011. Gl. 8.2.2, Gl. 8.2.3, Tab. 8.2.1 und Rechenbeispiel.

[2] Alstom Grid: Network Protection & Automation Guide. Kap. 9 Overcurrent Protection for Phase and Earth Faults, Abschnitt 9.11 und 9.12, Tab. 9.2.

[3] R. Krebs, G. Ziegler: Avoiding Cascading Protection Tripping in Transmission Systems. IEEE PowerTech 2009.

[4] Siemens AG: SIPROTEC 5 Überstromzeitschutz 7SJ82/7SJ85, Handbuch C53000-G5040-C017, Technische Daten. Nur als Orientierung, die Geräte im Tool sind SIPROTEC 4.

Die Seiten- und Tabellennummern zu [2] bis [4] stammen aus einer Online-Recherche
und sind vor dem Zitieren am Original zu prüfen.

[5] Siemens AG: SIPROTEC 4 7SJ66, Handbuch C53000-B1140-C383-D, Ausgabe 09.2023, Kap. 4.3
Technische Daten, Überstromzeitschutz mit abhängiger Kennlinie: Toleranzen der Auslösezeit.
