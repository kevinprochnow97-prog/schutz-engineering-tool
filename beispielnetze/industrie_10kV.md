# Beispielnetz „Industrie 10 kV“

> **Hinweis:** Alle Werte in diesem Beispielnetz sind **Tool-Vorgaben**. Sie sind nicht aus Handbuch oder Norm belegt und dienen nur als Test- und Demonstrationsfall für die netzweite Selektivitätsplanung.

```text
BEISPIELNETZ "Industrie 10 kV" (alle Werte Tool-Vorgabe)

A) Netzform:  [x] Strahlennetz   [ ] Ring
   (spaeterer Ring-Testfall: Kupplung K3–K4 schliessen, Trennstelle dort)

B) Elemente und Verbindungen
   Name | Typ               | von | nach
   E1   | Netzeinspeisung   | -   | K1
   T1   | Trafo 110/10 kV   | K1  | K2
   L1   | Leitung           | K2  | K3
   L2   | Leitung           | K2  | K4
   M1   | Motor             | K3  | -
   T2   | Trafo 10/0,4 kV   | K4  | K5

C) Knoten
   Knoten | UN [kV] | Ik″max [kA] | Ik,min 2-pol. [kA] | Sternpunkt
   K1     | 110     | 15,7        | 6,8                 | wirksam geerdet (Netzbetreiber)
   K2     | 10      | 10,0        | 7,5                 | isoliert
   K3     | 10      | 9,1         | 6,8                 | isoliert
   K4     | 10      | 7,9         | 5,8                 | isoliert
   K5     | 0,4     | ca. 35      | –                   | TN-S, starr geerdet

D) Einspeisung E1
   Sk″max 3000 MVA, Sk″min 1500 MVA
   Schutz Netzbetreiber am Übergabepunkt: I> 160 A, t 1,2 s

E) Trafo T1
   Sn 20 MVA | 110/10 kV | uk 12 % | YNd5 | Stufensteller ±16 %
   CT OS 150/1 A | CT US 1250/1 A

   Trafo T2
   Sn 1,6 MVA | 10/0,4 kV | uk 6 % | Dyn5 | kein Stufensteller
   CT OS 100/1 A

F) Leitungen L1, L2 (beide NA2XS2Y 3x1x150 Al)
   L1: 10 kV | 0,5 km | R′ 0,206 Ω/km | X′ 0,11 Ω/km | IN 300 A | CT 200/1 A
   L2: 10 kV | 1,2 km | R′ 0,206 Ω/km | X′ 0,11 Ω/km | IN 300 A | CT 200/1 A

G) Motor M1
   Pn 2000 kW | 10 kV | cos φ 0,88 | η 0,96 | I_A/IN 5,5 | t_Anlauf 8 s
   CT 150/1 A   (IN ≈ 137 A)
   50-2: 8,81 x IN = 1204 A (1,6 x Anlaufstrom 752 A, aufgerundet, Tool-Vorgabe)

H) Keine Eigenerzeugung. Generator als spaetere Erweiterung.
```
