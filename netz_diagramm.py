"""
netz_diagramm.py - Staffeldiagramm (Strom-Zeit-Kennlinien) je Versorgungspfad
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reines Python-Modul OHNE Streamlit (isoliert testbar).

Einstieg:
  erzeuge_diagramme(netz, pruefung=None) -> Liste Diagramm (eines je Pfad)
  vega_spec(diagramm)                    -> Dict (Vega-Lite), fuer st.vega_lite_chart

Ein Diagramm zeigt fuer einen Pfad von der Last zur Quelle die wirksame Ausloesezeit
jedes Schutzortes ueber dem Strom, beide Achsen logarithmisch, alle Stroeme auf die
Bezugsspannung der Zeitstaffelung umgerechnet. Dazu als senkrechte Marken Ik max und
Ik min der Knoten des Pfades.

Das Modul rechnet nichts Eigenes: Die Kennlinie ist netz_selektivitaet.ausloesezeit(),
also genau die Funktion, mit der die Ampeln der Zeitstaffelung entstehen. Diagramm und
Tabelle koennen sich deshalb nicht widersprechen (ein Test prueft das).

Tool-Vorgaben der Darstellung:
  - Eine Kennlinie beginnt am kleinsten Anregestrom des Schutzortes mit einer Senkrechten
    (darunter keine Ausloesung) und endet bei Ik max an ihrem Messort: mehr Strom kann
    durch diesen Schutz nicht fliessen. Fehlt Ik max dort, laeuft sie bis zum rechten Rand.
  - Rechter Rand: 1,3 * groesster Wert aus Ik max der Knoten des Pfades und den
    Ansprechwerten. Knoten auf einer anderen Spannungsebene als der Bezugsspannung
    zaehlen nicht mit (Ik der 110-kV-Seite waere auf 10 kV bezogen weit ausserhalb).
  - Zeiten unter T_ANZEIGE_MIN (0,01 s) stehen auf dieser Linie, weil eine logarithmische
    Achse keine Null kennt. Der echte Wert steht im Feld "t_s".
  - Wie die Zeitpruefung: Nennuebersetzung, Stufensteller in Mittelstellung.

Robustheit: Das Modul wirft nie. Ohne bewertbare Stufen gibt es eine leere Liste.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import konstanten_netz as KN
import netz_selektivitaet as S
from netz_topologie import FEHLER, HINWEIS, Meldung
from utils import de

T_ANZEIGE_MIN = 0.01        # kleinste dargestellte Zeit [s]
T_OBEN_MIN = 10.0           # obere Zeitgrenze mindestens [s]
F_RAND = 1.3                # Abstand des rechten Rands vom groessten Strom
N_AMZ = 60                  # Stuetzstellen je Dekadenbereich fuer AMZ-Kennlinien


@dataclass(frozen=True)
class Kurve:
    name: str                # Anzeigename des Schutzortes, z. B. "T1 (US)"
    punkte: tuple            # ((I_bez_A, t_anzeige_s, t_s, Stufe), ...) in Zeichenreihenfolge
    I_anrege_A: float        # kleinster Anregestrom auf Bezugsspannung


@dataclass(frozen=True)
class Marke:
    knoten: str
    art: str                 # "Ik max" oder "Ik min"
    I_bez_A: float

    @property
    def text(self) -> str:
        return f"{self.art} {self.knoten}"


@dataclass
class Diagramm:
    pfad: list = field(default_factory=list)       # Anzeigenamen von der Last zur Quelle
    U_bezug_kV: float = 0.0
    kurven: list = field(default_factory=list)
    marken: list = field(default_factory=list)
    I_min_A: float = 1.0
    I_max_A: float = 10.0
    t_oben_s: float = T_OBEN_MIN
    meldungen: list = field(default_factory=list)

    @property
    def titel(self) -> str:
        return " → ".join(self.pfad)


def _log_raster(a: float, b: float, n: int) -> list:
    if not (a > 0 and b > a):
        return []
    return [a * (b / a) ** (i / n) for i in range(1, n)]


def _kurve(ort, U: float, I_max: float, t_oben: float) -> Kurve | None:
    """Wirksame Ausloesezeit des Schutzortes als Linienzug von der Anregung bis I_max."""
    schwellen = sorted({S.anregestrom_bez(s, U) for s in ort.stufen})
    if not schwellen or schwellen[0] >= I_max:
        return None
    hat_amz = any(s.kennlinie != S.UMZ for s in ort.stufen)
    stroeme = set(x for x in schwellen if x < I_max) | {I_max}
    if hat_amz:
        stroeme |= set(_log_raster(schwellen[0], I_max, N_AMZ))
    punkte, t_vorher = [], None
    for I in sorted(stroeme):
        t, stufe = S.ausloesezeit(ort, I, U)
        if t is None:
            continue
        name = stufe.stufe if stufe is not None else ""
        zeige = min(max(t, T_ANZEIGE_MIN), t_oben)
        if not punkte:
            punkte.append((I, t_oben, t, name))            # Senkrechte an der Anregung
        elif I in schwellen and t_vorher is not None and abs(zeige - t_vorher[0]) > 1e-12:
            punkte.append((I, t_vorher[0], t_vorher[1], t_vorher[2]))   # Stufe: erst waagerecht
        punkte.append((I, zeige, t, name))
        t_vorher = (zeige, t, name)
    if len(punkte) < 2:
        return None
    return Kurve(ort.name, tuple(punkte), schwellen[0])


def erzeuge_diagramme(netz, pruefung=None, adapter=None) -> list:
    """
    Ein Diagramm je Pfad der Zeitstaffelung.
    pruefung: Ergebnis von netz_selektivitaet.pruefe_selektivitaet (z. B. die Gegenpruefung
    eines Vorschlags). Fehlt es, wird es aus dem Netz gerechnet. Wirft nie.
    """
    try:
        return _erzeuge(netz, pruefung, adapter)
    except Exception as exc:
        d = Diagramm()
        d.meldungen.append(Meldung(
            FEHLER, f"Staffeldiagramm abgebrochen ({type(exc).__name__}: {exc})."))
        return [d]


def _erzeuge(netz, pruefung, adapter) -> list:
    erg = pruefung if pruefung is not None else S.pruefe_selektivitaet(netz, adapter)
    U = erg.U_bezug_kV
    if not erg.orte or not erg.pfade or not U:
        return []
    orte = {o.name: o for o in erg.orte}
    knoten = netz.knoten
    out = []
    for pfad in erg.pfade:
        kette = [orte[n] for n in pfad if n in orte]
        if not kette:
            continue
        d = Diagramm(pfad=[o.name for o in kette], U_bezug_kV=U)
        # Marken: Ik der Messknoten des Pfades, jede Groesse je Knoten einmal
        gesehen, aussen = set(), []
        anrege = [S.anregestrom_bez(s, U) for o in kette for s in o.stufen]
        grenze = list(anrege)
        marken = []
        for o in kette:
            k = knoten.get(o.messort)
            if k is None or o.messort in gesehen:
                continue
            gesehen.add(o.messort)
            for art, wert in (("Ik max", k.Ik_max_kA), ("Ik min", k.Ik_min_kA)):
                if wert is None:
                    continue
                I = S.auf_bezug(wert * 1000.0, k.UN_kV, U)
                marken.append((Marke(o.messort, art, I), abs(k.UN_kV - U) <= 1e-9 * U))
                if abs(k.UN_kV - U) <= 1e-9 * U:
                    grenze.append(I)
        d.I_max_A = F_RAND * max(grenze)
        d.I_min_A = min(anrege) / F_RAND
        for m, _ in marken:
            if d.I_min_A <= m.I_bez_A <= d.I_max_A:
                d.marken.append(m)
            else:
                aussen.append(f"{m.text} ({de(m.I_bez_A, 0)} A bez.)")
        zeiten = [s.t_s for o in kette for s in o.stufen if s.kennlinie == S.UMZ and s.t_s]
        d.t_oben_s = max(T_OBEN_MIN, 3.0 * max(zeiten, default=0.0))
        for o in kette:
            ende = S._grenzstrom_bez(knoten, o, U)
            ende = d.I_max_A if ende is None else min(ende, d.I_max_A)
            k = _kurve(o, U, ende, d.t_oben_s)
            if k is not None:
                d.kurven.append(k)
        if aussen:
            d.meldungen.append(Meldung(
                HINWEIS, "Außerhalb des dargestellten Strombereichs: " + ", ".join(aussen) + "."))
        if d.kurven:
            out.append(d)
    return out


# ── Vega-Lite ────────────────────────────────────────────────────────────────
def vega_spec(d: Diagramm) -> dict:
    """Vega-Lite-Beschreibung des Diagramms als reines Dict (Daten eingebettet)."""
    linien, reihenfolge = [], [k.name for k in d.kurven]
    # Quelle zuerst zeichnen (breite Linie), Last zuletzt (schmale Linie obenauf), damit
    # deckungsgleiche Abschnitte sichtbar bleiben
    for k in reversed(d.kurven):
        for nr, (I, t_anz, t, stufe) in enumerate(k.punkte):
            linien.append({"Schutzort": k.name, "nr": nr, "I": round(I, 3), "t": round(t_anz, 5),
                           "t_s": round(t, 4), "Stufe": stufe})
    # Beschriftung der Marken unten im Diagramm (dort liegen kaum Kennlinien), in zwei
    # Hoehen versetzt, damit sich Nachbarn nicht ueberdecken
    hoehen = (1.25, 3.4)
    marken = [{"Marke": m.text, "I": round(m.I_bez_A, 3), "Art": m.art,
               "t": T_ANZEIGE_MIN * hoehen[i % 2]}
              for i, m in enumerate(sorted(d.marken, key=lambda m: m.I_bez_A))]
    zahl = "replace(format(datum.value, '~g'), '.', ',')"
    x = {"field": "I", "type": "quantitative",
         "scale": {"type": "log", "domain": [d.I_min_A, d.I_max_A], "nice": False},
         "axis": {"labelExpr": zahl},
         "title": f"Strom [A], bezogen auf {de(d.U_bezug_kV, 1)} kV"}
    y = {"field": "t", "type": "quantitative",
         "scale": {"type": "log", "domain": [T_ANZEIGE_MIN, d.t_oben_s], "nice": False},
         "axis": {"labelExpr": zahl},
         "title": "Auslösezeit [s]"}
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "height": 380,
        "layer": [
            {"data": {"values": marken},
             "mark": {"type": "rule", "strokeDash": [5, 4], "color": "#8a94a6"},
             "encoding": {"x": x, "tooltip": [{"field": "Marke"}, {"field": "I", "title": "I [A bez.]"}]}},
            {"data": {"values": linien},
             "mark": {"type": "line", "interpolate": "linear", "clip": True},
             "encoding": {
                 "x": x, "y": y, "order": {"field": "nr"},
                 "size": {"field": "Schutzort", "type": "ordinal", "sort": reihenfolge,
                          "scale": {"range": [2, 6]}, "legend": None},
                 "color": {"field": "Schutzort", "type": "nominal", "sort": reihenfolge,
                           "legend": {"title": "Schutzort (Last → Quelle)", "orient": "bottom"}},
                 "tooltip": [{"field": "Schutzort"}, {"field": "Stufe"},
                             {"field": "I", "title": "I [A bez.]"},
                             {"field": "t_s", "title": "t [s]"}]}},
            {"data": {"values": marken},
             "mark": {"type": "text", "angle": 270, "align": "left", "dx": 0, "dy": -5,
                      "fontSize": 10, "color": "#5d6b82"},
             "encoding": {"x": x, "y": y, "text": {"field": "Marke"}}},
        ],
    }
