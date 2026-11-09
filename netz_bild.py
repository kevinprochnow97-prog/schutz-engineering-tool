"""
netz_bild.py - Einlinienbild des Netzes als Graphviz-DOT-Text
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reines Python-Modul OHNE Streamlit (isoliert testbar). tab_netz.py gibt den
Text mit st.graphviz_chart aus. Dafuer wird kein Graphviz-Paket installiert,
Streamlit rendert DOT im Browser.

Darstellung:
  Knoten (Sammelschienen)   graues Rechteck mit ID, Name und Spannung
  Einspeisung / Generator   Symbol oberhalb ihres Knotens
  Trafo                     Doppelkreis zwischen OS- und US-Knoten
  Leitung / Kupplung        Linie zwischen zwei Knoten (Kupplung fett)
  Motor                     Kreis "M" unterhalb seines Knotens
  ausgeschaltet             gestrichelt und grau
  Ring                      blau, Trennstelle als solche beschriftet
  Fehler der Topologie      rot
"""

from __future__ import annotations

from netz_modell import Netz
from netz_topologie import FEHLER

FARBE_NORMAL = "#333333"
FARBE_AUS = "#9E9E9E"
FARBE_RING = "#2E5A87"
FARBE_FEHLER = "#C62828"


def _q(text) -> str:
    """Text als DOT-String in Anfuehrungszeichen, Sonderzeichen maskiert."""
    s = str(text).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{s}"'


def _zahl(x) -> str:
    return f"{x:g}".replace(".", ",")


def einlinienbild_dot(netz: Netz, topologie=None) -> str:
    kn = netz.knoten
    el = netz.elemente
    fehler_ids, ring, trennstelle = set(), set(), None
    if topologie is not None:
        for m in topologie.meldungen:
            if m.stufe == FEHLER:
                fehler_ids.update(m.ids)
        ring = set(topologie.ring_elemente)
        trennstelle = topologie.trennstelle

    def farbe(eid):
        if eid in fehler_ids:
            return FARBE_FEHLER
        if el[eid].zustand == "aus":
            return FARBE_AUS
        if eid in ring:
            return FARBE_RING
        return FARBE_NORMAL

    def stil(eid, extra=""):
        teile = [f"color={_q(farbe(eid))}", f"fontcolor={_q(farbe(eid))}"]
        if el[eid].zustand == "aus":
            teile.append('style="dashed"')
        if extra:
            teile.append(extra)
        return ", ".join(teile)

    def label(eid):
        e = el[eid]
        zusatz = ""
        if eid == trennstelle:
            zusatz = "\n(Trennstelle)"
        elif e.zustand == "aus":
            zusatz = "\n(aus)"
        return f"{eid}{zusatz}"

    z = [
        "digraph Netz {",
        '  graph [rankdir=TB, nodesep=0.5, ranksep=0.45, fontname="Helvetica", bgcolor="transparent"];',
        '  node [fontname="Helvetica", fontsize=10];',
        '  edge [fontname="Helvetica", fontsize=9, arrowhead=none];',
    ]
    for kid, k in sorted(kn.items()):
        rand = FARBE_FEHLER if kid in fehler_ids else "#555555"
        z.append(
            f"  k_{kid} [shape=box, style=\"filled\", fillcolor=\"#E8E8E8\", color={_q(rand)}, "
            f"penwidth=1.5, width=2.2, label={_q(f'{kid}  {k.name}' + chr(10) + _zahl(k.UN_kV) + ' kV')}];"
        )
    for eid, e in sorted(el.items()):
        n = f"e_{eid}"
        if e.typ in ("einspeisung", "generator"):
            symbol = "≈ Netz" if e.typ == "einspeisung" else "G"
            form = "box" if e.typ == "einspeisung" else "circle"
            z.append(f"  {n} [shape={form}, label={_q(label(eid) + chr(10) + symbol)}, {stil(eid)}];")
            z.append(f"  {n} -> k_{e.nach} [{stil(eid)}];")
        elif e.typ == "trafo":
            z.append(f"  {n} [shape=doublecircle, width=0.35, fixedsize=false, "
                     f"label={_q(label(eid))}, {stil(eid)}];")
            z.append(f"  k_{e.von} -> {n} [{stil(eid)}];")
            z.append(f"  {n} -> k_{e.nach} [{stil(eid)}];")
        elif e.typ in ("leitung", "kupplung"):
            dick = "penwidth=2.5" if e.typ == "kupplung" else "penwidth=1.2"
            # Kupplung im Ring soll die Knoten nicht in eine Rangfolge zwingen
            rang = ", constraint=false" if e.typ == "kupplung" else ""
            z.append(f"  k_{e.von} -> k_{e.nach} [label={_q(label(eid))}, {stil(eid, dick)}{rang}];")
        elif e.typ == "motor":
            z.append(f"  {n} [shape=circle, label={_q(label(eid) + chr(10) + 'M')}, {stil(eid)}];")
            z.append(f"  k_{e.von} -> {n} [{stil(eid)}];")
    z.append("}")
    return "\n".join(z)
