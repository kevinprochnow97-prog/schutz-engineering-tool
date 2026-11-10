# Tool-Vorgabe: Staffelabstand Δt für die netzweite Zeitstaffelung

Stand: 10.11.2026 | Gilt für `konstanten_netz.py` und `netz_selektivitaet.py`

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
| t_Rück | `dt_t_Rueck` | 30 ms | Beispielwert in [1]. Numerische Relais nach [2, Tab. 9.2]: Überlaufzeit 20 ms. |
| t_Tol | `dt_t_Tol` | 25 ms | Beispielwert in [1]. Konservativ gegenüber der typischen SIPROTEC-Angabe „1 % vom Einstellwert bzw. 10 ms“ [4]. |
| t_Sich | `dt_t_Sich` | 20 ms | Etwa eine Netzperiode bei 50 Hz, nach [1] der kleinste sinnvolle Wert. |
| Summe | `dt_summe()` | 180 ms | 80 + 30 + 2 · 25 + 20 |
| **Mindestwert** | `dt_Staffel_min` | **0,20 s** | Summe, auf das Einstellraster 0,05 s aufgerundet. |
| **Sollwert** | `dt_Staffel_soll` | **0,30 s** | Siehe Abschnitt 3. |

Zum Vergleich das Rechenbeispiel aus [1]: 2 · 25 + 50 + 30 + 20 = 150 ms. Der
Unterschied zum Tool kommt allein aus der längeren Schalterzeit.

## 3. Warum 0,30 s als Sollwert und nicht 0,20 s

- [2, Tab. 9.2] nennt für numerische Relais einen typischen Gesamtstaffelabstand von 0,3 s.
- Siemens-Autoren geben für den Reserveschutz 300 bis 400 ms je weiterer Staffelstufe an [3].
- Der Trafo-Tab arbeitet bereits mit `dt_Staffel = 0,30 s` (typ. 0,25 bis 0,40 s). Ein Test stellt sicher, dass beide Werte gleich bleiben.
- Die Reserve von 0,10 s gegenüber dem Mindestwert deckt langsamere Schalter und unterschiedlich gesättigte Wandler ab. Nach [1] ist der Sicherheitszuschlag zu erhöhen, wenn die Überstromziffern der Wandler in der Kette stark voneinander abweichen.

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
| 1 | Zeittoleranz der UMZ-Verzögerung und Rückfallzeit | Technische Daten 7SJ66, 7UT613, 7SA6/7SD5 (jeweils Abschnitt Überstromzeitschutz) |
| 2 | Ausschaltzeit der eingesetzten MS-Leistungsschalter | Datenblatt des Schalters. Vakuumschalter liegen meist unter 80 ms, dann ist der Wert konservativ. |
| 3 | Anregeschwelle der AMZ-Stufen (Tool: 1,1 · Ip) | Technische Daten 7SJ66. Für SIPROTEC 5 ist 1,1 · Schwellwert dokumentiert [4]. Achtung: [1] nennt für die Norm 1,3. |
| 4 | Kennlinienkonstanten AMZ (0,14 / 0,02 usw.) | IEC 60255-151 bzw. Handbuch 7SJ66. Stimmen mit [1, Tab. 8.2.1] überein. |
| 5 | Bei AMZ gegen AMZ reicht ein fester Abstand streng genommen nicht | Nach [1, Gl. 8.2.3] wächst der Abstand mit der Auslösezeit des unteren Schutzes. Im Tool noch nicht umgesetzt, als Erweiterung vorgemerkt. |

## Quellen

[1] ABB Oy: Distribution Automation Handbook, Section 8.2 Relay Coordination. 1MRS757285, Rev. A, 2011. Gl. 8.2.2, Gl. 8.2.3, Tab. 8.2.1 und Rechenbeispiel.

[2] Alstom Grid: Network Protection & Automation Guide. Kap. 9 Overcurrent Protection for Phase and Earth Faults, Abschnitt 9.11 und 9.12, Tab. 9.2.

[3] R. Krebs, G. Ziegler: Avoiding Cascading Protection Tripping in Transmission Systems. IEEE PowerTech 2009.

[4] Siemens AG: SIPROTEC 5 Überstromzeitschutz 7SJ82/7SJ85, Handbuch C53000-G5040-C017, Technische Daten. Nur als Orientierung, die Geräte im Tool sind SIPROTEC 4.

Die Seiten- und Tabellennummern zu [2] bis [4] stammen aus einer Online-Recherche
und sind vor dem Zitieren am Original zu prüfen.
