"""
netz_einstellliste.py - Einstellliste aller Schutzstufen des Netzes mit Export
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reines Python-Modul OHNE Streamlit (isoliert testbar).

Einstieg:
  erstelle(netz, adapter=None, aenderungen=None) -> Einstellliste
  aus_gesamtvorschlag(vorschlag) -> aenderungen   (netz_stromstaffel.gesamtvorschlag)
  aus_ringvorschlag(vorschlag)   -> aenderungen   (netz_ring.ringvorschlag)
  als_tabelle(liste) -> Liste von Dicts (Anzeige)
  als_csv(liste)     -> Text (Export fuer Excel)

Die Liste ist das Ergebnis der Selektivitaetsplanung in der Form, in der es weitergegeben
wird: je Schutzstufe eine Zeile mit Messort, Wandler, Ansprechwert primaer und sekundaer,
Zeit und, wenn ein Vorschlag gerechnet ist, dem neuen Wert mit Begruendung.

Das Modul rechnet nichts Fachliches:
  - Die Stufen kommen aus netz_adapter (Rechenkerne der Betriebsmittel-Tabs).
  - Neue Werte kommen aus dem Vorschlag, der uebergeben wird.
  - Sekundaerwert = Primaerwert / Wandleruebersetzung des Messorts (Wandler aus den
    Elementparametern). Ohne Wandlerangabe bleibt das Feld leer.
  - Die DIGSI-Adresse stammt aus dem HERST-Verzeichnis des jeweiligen Betriebsmittel-Tabs
    (konstanten_<bm>.HERST). Steht dort keine, bleibt das Feld leer. Es wird keine Adresse
    geraten ("Code ist die Wahrheit").

CSV (Tool-Vorgabe): Semikolon als Trennzeichen, Dezimalkomma, UTF-8 mit BOM. So oeffnet
ein deutsches Excel die Datei ohne Import-Dialog mit richtigen Umlauten und Zahlen.

Robustheit: Das Modul wirft nie. Fehlende Daten ergeben leere Felder und Meldungen.
"""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass, field

import konstanten_leitung
import konstanten_motor
import konstanten_trafo
import netz_adapter
from netz_topologie import FEHLER, Meldung
from utils import de

_HERST = {"trafo": konstanten_trafo, "leitung": konstanten_leitung, "motor": konstanten_motor}
_EPS = 1e-9

# Stufen, die nur fuer die ADRESSE des Ansprechwerts nachgeschlagen werden: Stufenname -> HERST-Schluessel.
# netz_adapter.STROM_PARAMETER kennt nur die I>>-Stufen, weil der Stromvorschlag nur diese schreibt.
# Die I>-Stufen gehoeren bewusst nicht dorthin (sie wuerden sonst vom Stromvorschlag mitgestaffelt).
# Die Zuordnung stimmt mit den Adresspaaren in HERST ueberein (Ansprechwert, Zeit): Trafo 2014/2016,
# Leitung 2620/2621, Motor 50-1 1204 (Zeit-Adresse steht nicht in HERST).
# Trafo "I> US": f_I_Ph gilt fuer beide Seiten, in HERST steht nur die OS-Adresse 2014. Die
# US-Adresse wird nicht geraten, das Feld bleibt leer (docs/tool_vorgabe_einstellliste.md, Punkt 1).
_STROM_ADRESSE_ZUSATZ = {
    "trafo":   {"I> OS": "f_I_Ph"},
    "leitung": {"Iph>": "iph_h"},
    "motor":   {"I> (50-1)": "f_50_1", "Ip": "f_51"},
}


def warum_zeit(grund: str, dt_soll: float) -> str:
    """Kurzbegruendung einer Zeit: 'Staffelabstand ueber <Stufe darunter>'."""
    if grund.startswith("Lage ") and ": " in grund:
        lage, rest = grund.split(": ", 1)
        return f"{lage}: {warum_zeit(rest, dt_soll)}"
    if not grund or grund.startswith(("Mindestzeit", "Untergrenze", "Endpunkt", "Netzbetreiber", "AMZ")):
        return grund
    return f"{de(dt_soll, 2)} s über {grund}"


def _zahl(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


@dataclass(frozen=True)
class Aenderung:
    """Neuer Wert einer Stufe aus einem Vorschlag. None = dieser Wert aendert sich nicht."""
    I_neu_A: float | None = None       # primaer am Messort
    t_neu_s: float | None = None
    grund_strom: str = ""
    grund_zeit: str = ""


@dataclass(frozen=True)
class Zeile:
    element: str
    bezeichnung: str
    typ: str
    stufe: str
    ansi: str
    messort: str
    UN_kV: float
    wandler: str                       # "200/1 A" oder ""
    kennlinie: str
    aktiv: bool
    I_prim_A: float
    I_sek_A: float | None
    faktor_IN: float | None            # Ansprechwert als Vielfaches des Nennstroms
    t_s: float | None                  # UMZ-Verzoegerung
    T_mult: float | None               # AMZ-Zeitmultiplikator
    adresse_strom: str = ""
    adresse_zeit: str = ""
    I_neu_prim_A: float | None = None  # nur gesetzt, wenn sich der Wert aendert
    I_neu_sek_A: float | None = None
    faktor_neu_IN: float | None = None
    t_neu_s: float | None = None
    begruendung: str = ""

    @property
    def geaendert(self) -> bool:
        return self.I_neu_prim_A is not None or self.t_neu_s is not None


@dataclass
class Einstellliste:
    netzname: str = ""
    quelle_vorschlag: str = ""         # "", "Staffelvorschlag" oder "Ringvorschlag"
    zeilen: list = field(default_factory=list)
    meldungen: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(m.stufe == FEHLER for m in self.meldungen)

    @property
    def geaendert(self) -> list:
        return [z for z in self.zeilen if z.geaendert]


# ── Aenderungen aus den Vorschlaegen ─────────────────────────────────────────
def aus_gesamtvorschlag(vorschlag) -> dict:
    """{(Element, Stufe): Aenderung} aus netz_stromstaffel.gesamtvorschlag. Wirft nie."""
    out = {}
    try:
        for v in vorschlag.strom.geaendert:
            out[(v.element, v.stufe)] = Aenderung(I_neu_A=v.I_neu_A, grund_strom=v.kurz or v.status)
        if vorschlag.zeit is not None:
            for v in vorschlag.zeit.geaendert:
                alt = out.get((v.element, v.stufe), Aenderung())
                out[(v.element, v.stufe)] = Aenderung(alt.I_neu_A, v.t_neu_s, alt.grund_strom, v.grund)
    except Exception:
        return {}
    return out


def aus_ringvorschlag(vorschlag) -> dict:
    """{(Element, Stufe): Aenderung} aus netz_ring.ringvorschlag. Wirft nie."""
    out = {}
    try:
        for w in vorschlag.geaendert:
            alt = out.get((w.element, w.stufe), Aenderung())
            if w.art == "Strom":
                if not w.IN_A:
                    continue
                out[(w.element, w.stufe)] = Aenderung(w.neu * w.IN_A, alt.t_neu_s, w.kurz, alt.grund_zeit)
            else:
                out[(w.element, w.stufe)] = Aenderung(alt.I_neu_A, w.neu, alt.grund_strom, w.kurz)
    except Exception:
        return {}
    return out


# ── Hilfen je Stufe ──────────────────────────────────────────────────────────
def _wandler(typ: str, stufe: str, p: dict) -> tuple:
    """(Uebersetzung, Text) des Stromwandlers am Messort der Stufe. (None, "") ohne Angabe."""
    if typ == "trafo":
        seite = "OS" if stufe.endswith("OS") else "US"
        prim, sek = p.get(f"CT_{seite}_Prim"), p.get(f"CT_{seite}_Sek")
    elif typ in ("leitung", "motor"):
        prim, sek = p.get("CT_Prim"), p.get("CT_Sek")
    else:
        return None, ""
    if not (_zahl(prim) and _zahl(sek) and prim > 0 and sek > 0):
        return None, ""
    return prim / sek, f"{de(prim, 0)}/{de(sek, 0)} A"


def _adresse(typ: str, schluessel) -> str:
    if not schluessel or typ not in _HERST:
        return ""
    eintrag = getattr(_HERST[typ], "HERST", {}).get(schluessel)
    return str(eintrag.get("adr", "")) if isinstance(eintrag, dict) else ""


def _tiefe(topo, element_id: str) -> int:
    """Abstand zur Quelle in Elementen. Die Liste laeuft von der Quelle zur Last."""
    try:
        return len(topo.pfad_zur_quelle(element_id)) or 99
    except Exception:
        return 99


# ── Einstieg ─────────────────────────────────────────────────────────────────
def erstelle(netz, adapter=None, aenderungen: dict | None = None,
             quelle_vorschlag: str = "", dt_soll: float = 0.30) -> Einstellliste:
    """
    Einstellliste aller Schutzstufen. aenderungen: Ergebnis von aus_gesamtvorschlag oder
    aus_ringvorschlag. Ohne sie zeigt die Liste nur den Ist-Zustand. Wirft nie.
    """
    liste = Einstellliste(quelle_vorschlag=quelle_vorschlag if aenderungen else "")
    try:
        return _erstelle(netz, adapter, aenderungen or {}, liste, dt_soll)
    except Exception as exc:
        liste.zeilen = []
        liste.meldungen.append(Meldung(
            FEHLER, f"Einstellliste abgebrochen ({type(exc).__name__}: {exc})."))
        return liste


def _erstelle(netz, adapter, aenderungen, liste, dt_soll) -> Einstellliste:
    liste.netzname = netz.name
    ad = adapter if adapter is not None else netz_adapter.erzeuge_schutzstufen(netz)
    liste.meldungen += [m for m in ad.meldungen if m.stufe == FEHLER]
    elemente = netz.elemente
    benutzt = set()
    for s in ad.stufen:
        e = elemente[s.element]
        p = ad.p_voll.get(s.element, e.p)
        ue, wandler = _wandler(e.typ, s.stufe, p)
        IN = netz_adapter.nennstrom_A(e.typ, s.stufe, p) if e.typ in _HERST else None
        IN = IN if _zahl(IN) and IN > 0 else None
        a = aenderungen.get((s.element, s.stufe))
        I_neu = t_neu = None
        gruende = []
        if a is not None:
            benutzt.add((s.element, s.stufe))
            if _zahl(a.I_neu_A) and abs(a.I_neu_A - s.I_prim_A) > _EPS * max(s.I_prim_A, 1.0):
                I_neu = float(a.I_neu_A)
                if a.grund_strom:
                    gruende.append(f"Ansprechwert: {a.grund_strom}")
            if _zahl(a.t_neu_s) and _zahl(s.t_s) and abs(a.t_neu_s - s.t_s) > 1e-6:
                t_neu = float(a.t_neu_s)
                if a.grund_zeit:
                    gruende.append(f"Zeit: {warum_zeit(a.grund_zeit, dt_soll)}")
        liste.zeilen.append(Zeile(
            element=s.element, bezeichnung=e.name, typ=e.typ, stufe=s.stufe, ansi=s.ansi,
            messort=s.messort, UN_kV=s.UN_kV, wandler=wandler, kennlinie=s.kennlinie,
            aktiv=s.aktiv, I_prim_A=s.I_prim_A,
            I_sek_A=None if ue is None else s.I_prim_A / ue,
            faktor_IN=None if IN is None else s.I_prim_A / IN,
            t_s=s.t_s, T_mult=s.T_mult,
            adresse_strom=_adresse(e.typ, {**netz_adapter.STROM_PARAMETER.get(e.typ, {}),
                                           **_STROM_ADRESSE_ZUSATZ.get(e.typ, {})}.get(s.stufe)),
            adresse_zeit=_adresse(e.typ, netz_adapter.ZEIT_PARAMETER.get(e.typ, {}).get(s.stufe)),
            I_neu_prim_A=I_neu,
            I_neu_sek_A=None if I_neu is None or ue is None else I_neu / ue,
            faktor_neu_IN=None if I_neu is None or IN is None else I_neu / IN,
            t_neu_s=t_neu, begruendung=". ".join(gruende)))
    topo = ad.topologie
    reihenfolge = {z.element: i for i, z in enumerate(liste.zeilen)}
    liste.zeilen.sort(key=lambda z: (_tiefe(topo, z.element), z.element, z.messort != elemente[z.element].von,
                                     reihenfolge[z.element]))
    fehlend = sorted(set(aenderungen) - benutzt)
    if fehlend:
        liste.meldungen.append(Meldung(
            FEHLER, "Der Vorschlag enthält Stufen, die es im Netz nicht gibt: "
                    + ", ".join(f"{e} {s}" for e, s in fehlend) + "."))
    return liste


# ── Ausgabe ──────────────────────────────────────────────────────────────────
def _z(wert, stellen) -> str:
    return "" if wert is None else de(wert, stellen)


def als_tabelle(liste: Einstellliste, mit_vorschlag: bool | None = None) -> list:
    """
    Zeilen als Dicts mit deutschen Spaltennamen und Zahlen als Text mit Dezimalkomma.
    mit_vorschlag: Spalten "neu" und "Begründung" zeigen. None = nur wenn es Aenderungen gibt.
    """
    if mit_vorschlag is None:
        mit_vorschlag = bool(liste.geaendert)
    out = []
    for z in liste.zeilen:
        zeile = {
            "Element": z.element, "Bezeichnung": z.bezeichnung, "Messort": z.messort,
            "UN [kV]": de(z.UN_kV, 1), "Wandler": z.wandler, "Stufe": z.stufe, "ANSI": z.ansi,
            "Kennlinie": z.kennlinie, "aktiv": "ja" if z.aktiv else "nein",
            "I prim. [A]": de(z.I_prim_A, 1), "I sek. [A]": _z(z.I_sek_A, 2),
            "x IN": _z(z.faktor_IN, 2), "t [s]": _z(z.t_s, 2), "T-Mult.": _z(z.T_mult, 2),
        }
        if mit_vorschlag:
            zeile.update({
                "geändert": "ja" if z.geaendert else "",
                "I prim. neu [A]": _z(z.I_neu_prim_A, 1), "I sek. neu [A]": _z(z.I_neu_sek_A, 2),
                "x IN neu": _z(z.faktor_neu_IN, 2), "t neu [s]": _z(z.t_neu_s, 2),
                "Begründung": z.begruendung,
            })
        zeile.update({"Adresse Ansprechwert": z.adresse_strom, "Adresse Zeit": z.adresse_zeit})
        out.append(zeile)
    return out


def als_csv(liste: Einstellliste, stand: str = "") -> str:
    """
    CSV fuer Excel: Semikolon, Dezimalkomma, BOM. Kopfzeilen mit Netzname und Hinweis,
    dann die Tabelle immer mit den Spalten des Vorschlags (leer, wenn keiner gerechnet ist).
    """
    puffer = io.StringIO()
    w = csv.writer(puffer, delimiter=";", lineterminator="\r\n")
    w.writerow(["Einstellliste Schutzstufen", liste.netzname])
    if stand:
        w.writerow(["Stand", stand])
    w.writerow(["Vorschlag", liste.quelle_vorschlag or "keiner, nur Einstellwerte im Netz"])
    w.writerow(["Hinweis", "Werte aus dem Schutz-Engineering-Tool. Tool-Vorgaben, vor der "
                           "Parametrierung am Gerät gegen Handbuch und Netzdaten prüfen."])
    w.writerow([])
    zeilen = als_tabelle(liste, mit_vorschlag=True)
    if zeilen:
        w.writerow(list(zeilen[0]))
        for z in zeilen:
            w.writerow(list(z.values()))
    return "﻿" + puffer.getvalue()
