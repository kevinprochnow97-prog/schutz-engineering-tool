# Beispielnetz „Industrie 10 kV, niederohmig geerdet“

> **Hinweis:** Alle Werte in diesem Beispielnetz sind **Tool-Vorgaben**. Sie sind nicht aus Handbuch oder Norm belegt und dienen nur als Test- und Demonstrationsfall für die Erdfehlerstaffelung (Entscheidung 25.11.2026).

Kopie des Referenznetzes `industrie_10kV.json` mit drei Änderungen:

1. **10-kV-Bereich niederohmig geerdet.** K2, K3 und K4 haben die Sternpunktbehandlung „niederohmig“. T1 ist YNd5, die 10-kV-Seite also ein Dreieck ohne Sternpunkt. Die Erdung sitzt deshalb an einem **Sternpunktbildner an K2**, mit einer Erdfehlerstrom-Begrenzung von **2000 A** (R_E = 10 kV / (√3 · 2000 A) = 2,89 Ω).
2. **Zweiter Motor M2** (Pumpe 800 kW) direkt an K4. Damit hat jeder Kabelabgang einen Motor darunter, und es gibt zwei Erdketten (M1 → L1 und M2 → L2).
3. **Sternpunktwandler an T2** (CT_E 1000/1 A). Damit hat der starr geerdete 0,4-kV-Bereich eine Erdstufe IE> am Sternpunkt von T2.

```text
E1 ── K1 (110 kV, starr) ── T1 YNd5 ── K2 (10 kV, niederohmig, Sternpunktbildner 2000 A)
                                         ├── L1 ── K3 ── M1 (2000 kW)
                                         └── L2 ── K4 ── M2 (800 kW)
                                                    └── T2 Dyn5 ── K5 (0,4 kV, starr)
```

## M2

| Größe | Wert |
|---|---|
| Pn | 800 kW, cos φ 0,87, η 0,95 |
| I_A/IN | 6,0, Anlaufzeit 5 s |
| CT | 75/1 A |
| 50-2 | 9,6 × IN (1,6 × Anlaufstrom, aufgerundet, wie bei M1) |

## Handwerte Ik″max

Mit Motorbeitrag (M1 und M2) nach DIN EN 60909-0, 7.1.2, angehoben am 25.11.2026:
K1 15,9, K2 11,4, K3 10,4, K4 8,9, K5 35,6 kA. Wegen M2 etwas höher als im Referenznetz.

## Erwartete Ergebnisse (Stand 25.11.2026)

Ik1 aus der Kurzschlussrechnung, mit pandapower 3.5.6 gegengerechnet (Abweichung 0,00 %). Stand nach der Normprüfung vom 25.11.2026: Ik1 max mit den Motoren, Ik1 min mit der Endtemperatur der Leitungen.

| Knoten | Ik1 max [kA] | Ik1 min [kA] |
|---|---|---|
| K1 | 16,13 | 8,14 |
| K2 | 2,18 | 1,97 |
| K3 | 2,03 | 1,79 |
| K4 | 1,85 | 1,59 |
| K5 | 37,45 | 30,29 |

Mit den Werksvoreinstellungen der Erdstufen sind beide Erdketten nicht selektiv: M1 50N-2 und L1 3I0>>> lösen beide nach 0,10 s aus, ebenso M2 und L2. Der Erdstaffelvorschlag setzt:

| Element | 3I0>>> | 3I0>> | 3I0> |
|---|---|---|---|
| L1 | 0,40 s | 0,45 s | 0,80 s |
| L2 | 0,40 s | 0,45 s | 0,50 s |

Danach sind beide Paare mit 0,30 s Abstand grün. Die Phasenstaffelung verhält sich wie im Referenznetz.
