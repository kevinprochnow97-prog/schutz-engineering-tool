# Beispielnetz „Industrie 10 kV Ring“

> **Hinweis:** Alle Werte sind **Tool-Vorgaben** und nur als Test- und Demonstrationsfall gedacht.

Wie `industrie_10kV.json` (siehe `industrie_10kV.md`), zusätzlich mit der Kupplung **K34** zwischen
K3 und K4. Die Kupplung ist offen und damit die Trennstelle. Der Ring besteht aus L1, K34 und L2.

```text
          K2 ──L1── K3 ──K34(offen)── K4 ──L2── K2
                     │                 │
                     M1                T2
```

Mögliche Trennstellenlagen: K34 (Ausgangslage), L1 oder L2. Die Kupplung hat per Tool-Vorgabe
keinen eigenen Schutz. Der Ring ist mit einer Einspeisung versorgt, die Reihenfolge der Leitungen
in den Staffelketten kehrt sich deshalb nie um.
