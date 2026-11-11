"""
netz_stromstaffel.py - Stromstaffelung der I>>-Stufen und Gesamtvorschlag (Strom, dann Zeit)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reines Python-Modul OHNE Streamlit (isoliert testbar).

Einstieg:
  stromvorschlag(netz)       -> StromErgebnis    (I>>-Ansprechwerte je Stufe mit Begruendung)
  pruefe_strom(netz)         -> StromPruefErgebnis (Gegenpruefung: Stromstaffel, Empfindlichkeit)
  gesamtvorschlag(netz)      -> GesamtVorschlag  (erst Strom, dann Zeit, dann Gegenpruefung)

Herleitung, Annahmen und Grenzen: docs/tool_vorgabe_stromstaffelung.md.

Regel (Tool-Vorgabe), je I>>-Stufe eines Schutzortes O mit naechster Station u darunter:

  I>>_O  >=  k_S * I_Bezug(u)          k_S = 1,2 (konstanten_netz.k_S_Strom)

  I_Bezug(u) = Ik max an dem Knoten HINTER u, gelesen am Messort von O
               (ueber alle Transformatoren dazwischen, mit Stufensteller:
               netz_umrechnung.py). Hinter einer Leitung ist das ihr
               Gegenknoten, hinter der OS-Seite eines Trafos die US-Sammelschiene.
  Ohne Ik max dahinter (Motor, fehlende Eingabe):
               I>> der naechsten Station, beim Motor mindestens der Anlaufstrom.

Vorgehen: von der Last zur Quelle, wie die Zeitstaffelung. Der Vorschlag hebt
einen Wert nur AN, er senkt nie unter den Wert aus dem Betriebsmittel-Tab
(Einschaltstrom, Anlauf und Wandlerfehler sind dort beruecksichtigt).
Ist k_S * I_Bezug groesser als Ik max am eigenen Messort, kann die Stufe nie
ansprechen. Dann bleibt der Wert unveraendert, die Stufe wird wie eine
Zeitstufe gestaffelt und es gibt einen Hinweis (typisch bei kurzen Kabeln).

Nach dem Stromvorschlag laeuft die Zeitstaffelung (netz_selektivitaet) mit den
neuen Ansprechwerten, danach die Gegenpruefung beider.

Robustheit: Das Modul wirft nie. Fehlende Daten fuehren zu Meldungen.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import konstanten_motor
import konstanten_netz as KN
import netz_adapter
import netz_selektivitaet as S
import netz_umrechnung as UM
from netz_adapter import UMZ
from netz_topologie import FEHLER, HINWEIS, WARNUNG, Meldung
from utils import de

# Status eines Stromvorschlags
ANGEHOBEN = "angehoben"
BLEIBT = "bleibt"
NICHT_WIRKSAM = "nicht wirksam"
ENDPUNKT = "Endpunkt"
OHNE_BEZUG = "ohne Bezug"

# Art des Bezugsstroms
ART_IK = "Ik max"
ART_I2 = "I>> unten"
ART_MOTOR = "Motor"


# ── Datenklassen ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Stromvorschlag:
    element: str
    stufe: str
    parameter: str | None          # Schluessel des Faktors im Element-Parametersatz
    I_alt_A: float                 # primaer am Messort
    I_neu_A: float
    faktor_alt: float | None       # x IN
    faktor_neu: float | None
    status: str
    grund: str

    @property
    def geaendert(self) -> bool:
        return self.status == ANGEHOBEN and abs(self.I_neu_A - self.I_alt_A) > 1e-9


@dataclass(frozen=True)
class Stromstufenpruefung:
    """Gegenpruefung je Paar (unten, oben)."""
    art: str                       # "Stromstaffel" oder "Empfindlichkeit"
    unten: str
    oben: str
    stufe_oben: str
    status: str                    # OK / Hinweis / Prüfen!
    I_soll_bez_A: float | None     # Stromstaffel: k_S * Bezug. Empfindlichkeit: gamma * Ansprechwert
    I_ist_bez_A: float | None      # Stromstaffel: Ansprechwert. Empfindlichkeit: Ik min
    text: str = ""


@dataclass
class StromPruefErgebnis:
    pruefungen: list = field(default_factory=list)
    meldungen: list = field(default_factory=list)

    @property
    def status(self) -> str | None:
        if not self.pruefungen:
            return None
        return max((p.status for p in self.pruefungen), key=S._RANG.get)


@dataclass
class StromErgebnis:
    U_bezug_kV: float | None = None
    vorschlaege: list = field(default_factory=list)
    meldungen: list = field(default_factory=list)
    adapter: object = None                       # AdapterErgebnis mit den neuen Ansprechwerten
    pruefung: StromPruefErgebnis | None = None   # Gegenpruefung mit den neuen Werten

    @property
    def ok(self) -> bool:
        return not any(m.stufe == FEHLER for m in self.meldungen)

    @property
    def geaendert(self) -> list:
        return [v for v in self.vorschlaege if v.geaendert]

    def parameter_je_element(self) -> dict:
        """Element-ID -> {Faktor-Schluessel: Faktor} fuer jede geaenderte Stufe."""
        out = {}
        for v in self.geaendert:
            if v.parameter and v.faktor_neu is not None:
                out.setdefault(v.element, {})[v.parameter] = v.faktor_neu
        return out


@dataclass
class GesamtVorschlag:
    strom: StromErgebnis
    zeit: S.VorschlagErgebnis | None = None
    meldungen: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(m.stufe == FEHLER for m in self.meldungen)

    @property
    def geaendert(self) -> list:
        """Alle geaenderten Strom- und Zeitwerte (beide Vorschlagsarten)."""
        out = list(self.strom.geaendert)
        if self.zeit is not None:
            out += self.zeit.geaendert
        return out

    def parameter_je_element(self) -> dict:
        out = {}
        for teil in (self.strom, self.zeit):
            if teil is None:
                continue
            for eid, p in teil.parameter_je_element().items():
                out.setdefault(eid, {}).update(p)
        return out


# ── Bezugsstrom hinter der naechsten Station ─────────────────────────────────
def _fernknoten(netz, zusp: dict, u: S.Schutzort):
    """
    Knoten HINTER dem Schutzort u (in Richtung Last). None bei Motor/Einspeisung.
    Speiseseitiger Ort: der andere Knoten des Elements. Lastseitiger Ort eines
    Trafos: die Sammelschiene selbst (Abgaenge dahinter gehoeren zu anderen Elementen).
    """
    e = netz.elemente[u.element]
    if e.typ not in ("trafo", "leitung"):
        return None
    if u.messort == zusp.get(u.element):
        return e.nach if e.von == u.messort else e.von
    return u.messort


def _i_hh_unten(u: S.Schutzort, U: float):
    """Kleinster I>>-Ansprechwert des Ortes u auf Bezugsspannung, None ohne I>>-Stufe."""
    werte = [S.anregestrom_bez(s, U) for s in u.stufen if ">>" in s.stufe and s.kennlinie == UMZ]
    return min(werte) if werte else None


def _bezug_unten(netz, topo, ad, zusp, o: S.Schutzort, u: S.Schutzort, U: float) -> tuple:
    """
    Bezugsstrom der naechsten Station u fuer den Schutzort o.
    Rueckgabe (I_bez_A, Text, Art, Hinweise). I_bez_A None, wenn nichts ermittelbar.
    """
    hinweise = []
    e = netz.elemente[u.element]
    fern = _fernknoten(netz, zusp, u)
    grund_fallback = ""
    if fern is not None:
        k = netz.knoten.get(fern)
        if k is not None and k.Ik_max_kA is not None:
            um = UM.umrechnen(netz, topo, k.Ik_max_kA * 1000.0, fern, o.messort, UM.MAX)
            if um.ok:
                I_bez = S.auf_bezug(um.I_A, o.UN_kV, U)
                trafo_text = "" if not um.schritte else f", über {um.text}"
                return (I_bez, f"{u.name}: Ik max {fern} {de(k.Ik_max_kA, 1)} kA{trafo_text} "
                               f"= {de(I_bez, 0)} A bez.", ART_IK, um.hinweise)
            hinweise += um.hinweise
            grund_fallback = f"Umrechnung von {fern} nach {o.messort} nicht möglich"
        else:
            grund_fallback = f"Ik max an {fern} fehlt"
    elif e.typ == "motor":
        grund_fallback = "kein Ik max hinter einem Motor"

    # Rueckfall: I>> der naechsten Station, beim Motor mindestens der Anlaufstrom
    I_hh = _i_hh_unten(u, U)
    if e.typ == "motor":
        I_anl = netz_adapter.anlaufstrom_A(ad.p_voll.get(u.element, {}))
        if I_anl is not None:
            I_anl_bez = S.auf_bezug(I_anl, u.UN_kV, U)
            I_bez = max(I_anl_bez, I_hh or 0.0)
            return (I_bez, f"{u.name}: {grund_fallback}, Bezug = max(I>> "
                           f"{de(I_hh or 0.0, 0)} A, Anlaufstrom {de(I_anl_bez, 0)} A) "
                           f"= {de(I_bez, 0)} A bez.", ART_MOTOR, hinweise)
    if I_hh is not None:
        return (I_hh, f"{u.name}: {grund_fallback}, Bezug = I>> der Station "
                      f"{de(I_hh, 0)} A bez.", ART_I2, hinweise)
    return None, f"{u.name}: {grund_fallback}, keine I>>-Stufe als Ersatz", None, hinweise


def _eigenes_ik_bez(netz, o: S.Schutzort, U: float):
    return S._grenzstrom_bez(netz.knoten, o, U)


# ── Stromvorschlag ───────────────────────────────────────────────────────────
def stromvorschlag(netz, adapter=None, U_bezug_kV: float | None = None,
                   k_S: float = KN.k_S_Strom) -> StromErgebnis:
    """I>>-Ansprechwerte vorschlagen (siehe Modulkopf). Wirft nie."""
    erg = StromErgebnis()
    try:
        return _strom(netz, adapter, U_bezug_kV, k_S, erg)
    except Exception as exc:
        erg.meldungen.append(Meldung(
            FEHLER, f"Stromvorschlag abgebrochen ({type(exc).__name__}: {exc})."))
        return erg


def _strom(netz, adapter, U_bezug_kV, k_S, erg) -> StromErgebnis:
    if not (S._ist_zahl(k_S) and k_S >= 1.0):
        erg.meldungen.append(Meldung(FEHLER, "Sicherheitsfaktor ungültig: es muss k_S >= 1 gelten."))
        return erg
    ad = adapter if adapter is not None else netz_adapter.erzeuge_schutzstufen(netz)
    if ad.topologie is None or not ad.topologie.ok or not ad.ok:
        erg.meldungen.append(Meldung(
            FEHLER, "Topologie oder Schutzstufen enthalten Fehler. Kein Stromvorschlag."))
        return erg
    st = S._struktur(netz, ad, U_bezug_kV, erg.meldungen)
    if st is None:
        return erg
    U, paare = st["U"], st["paare"]
    erg.U_bezug_kV = U
    topo = ad.topologie
    zusp = S._zuspeiseknoten(topo, netz.elemente)

    unter = {}
    for u, o in paare:
        unter.setdefault(o.schluessel, []).append(u)
    neu = {o.schluessel: o for o in st["orte"]}
    fertig = {k for k in neu if k not in unter}
    for k in sorted(fertig):                      # Endpunkte: Werte aus dem Tab, Motor pruefen
        _endpunkt(netz, ad, neu[k], U, erg)
    offen = sorted(k for k in neu if k not in fertig)
    while offen:
        naechste = [k for k in offen if all(u.schluessel in fertig for u in unter[k])]
        if not naechste:
            erg.meldungen.append(Meldung(FEHLER, "Zirkuläre Staffelkette, kein Stromvorschlag."))
            return erg
        for k in naechste:
            ort = neu[k]
            if netz.elemente[ort.element].typ == "einspeisung":
                fertig.add(k)
                offen.remove(k)
                continue
            stufen = []
            for s in ort.stufen:
                if ">>" in s.stufe and s.kennlinie == UMZ:
                    s_neu, v = _stufe(netz, topo, ad, zusp, ort, s,
                                      [neu[u.schluessel] for u in unter[k]], U, k_S, erg)
                    erg.vorschlaege.append(v)
                    stufen.append(s_neu)
                else:
                    stufen.append(s)
            neu[k] = replace(ort, stufen=tuple(stufen))
            fertig.add(k)
            offen.remove(k)

    ersetzt = {(s.element, s.stufe): s for o in neu.values() for s in o.stufen}
    erg.adapter = replace(ad, stufen=[ersetzt.get((s.element, s.stufe), s) for s in ad.stufen])
    erg.pruefung = pruefe_strom(netz, erg.adapter, U, k_S)
    return erg


def _faktor(I_A, IN):
    return None if not IN else I_A / IN


def _endpunkt(netz, ad, ort: S.Schutzort, U: float, erg: StromErgebnis) -> None:
    """Endpunkte (Motor, unterste Trafoseite) behalten ihre I>>-Werte aus dem Tab."""
    e = netz.elemente[ort.element]
    p = ad.p_voll.get(ort.element, {})
    for s in ort.stufen:
        if ">>" not in s.stufe or s.kennlinie != UMZ:
            continue
        IN = netz_adapter.nennstrom_A(e.typ, s.stufe, p)
        key = netz_adapter.STROM_PARAMETER.get(e.typ, {}).get(s.stufe)
        f = _faktor(s.I_prim_A, IN)
        erg.vorschlaege.append(Stromvorschlag(
            ort.element, s.stufe, key, s.I_prim_A, s.I_prim_A, f, f, ENDPUNKT,
            "Endpunkt, Wert aus dem Tab bleibt"))
        if e.typ == "motor":
            I_anl = netz_adapter.anlaufstrom_A(p)
            grenze = None if I_anl is None else konstanten_motor.f_50_2_Anlauf_Sicherheit * I_anl
            if grenze is not None and s.I_prim_A < grenze:
                erg.meldungen.append(Meldung(
                    WARNUNG,
                    f"{ort.element} {s.stufe}: {de(s.I_prim_A, 0)} A liegt unter dem Motor-Tab-Fenster "
                    f"{de(konstanten_motor.f_50_2_Anlauf_Sicherheit, 1)} × Anlaufstrom "
                    f"({de(grenze, 0)} A, Anlauf {de(I_anl, 0)} A). Im Motor-Tab prüfen. "
                    f"Der Vorschlag für die Stationen darüber nutzt mindestens den Anlaufstrom.",
                    (ort.element,)))


def _stufe(netz, topo, ad, zusp, ort, s, darunter, U, k_S, erg) -> tuple:
    """Vorschlag fuer eine I>>-Stufe. Rueckgabe (neue Stufe, Stromvorschlag)."""
    e = netz.elemente[ort.element]
    p = ad.p_voll.get(ort.element, {})
    key = netz_adapter.STROM_PARAMETER.get(e.typ, {}).get(s.stufe)
    IN = netz_adapter.nennstrom_A(e.typ, s.stufe, p)
    f_alt = _faktor(s.I_prim_A, IN)

    def unveraendert(status, grund):
        return s, Stromvorschlag(ort.element, s.stufe, key, s.I_prim_A, s.I_prim_A,
                                 f_alt, f_alt, status, grund)

    massgebend = None        # (k_S * I_bez, Text)
    for u in darunter:
        I_bez, text, _art, hinweise = _bezug_unten(netz, topo, ad, zusp, ort, u, U)
        for h in hinweise:
            erg.meldungen.append(Meldung(HINWEIS, h, (ort.element,)))
        if I_bez is None:
            erg.meldungen.append(Meldung(
                HINWEIS, f"{ort.element} {s.stufe}: {text}. Diese Station fließt nicht in "
                         f"den Stromvorschlag ein.", (ort.element,)))
            continue
        if massgebend is None or k_S * I_bez > massgebend[0]:
            massgebend = (k_S * I_bez, text)
    if massgebend is None:
        return unveraendert(OHNE_BEZUG, "Kein Bezugsstrom ermittelbar, Wert aus dem Tab bleibt")

    soll_bez, text = massgebend
    soll_A = soll_bez * U / ort.UN_kV                # zurueck auf die Spannung des Messorts
    kopf = f"{de(k_S, 2)} × Bezug ({text}) = {de(soll_bez, 0)} A bez."   # endet mit Punkt der Abkuerzung

    ik_eigen = _eigenes_ik_bez(netz, ort, U)
    if ik_eigen is not None and soll_bez > ik_eigen * (1 + KN.EPS_STROM):
        erg.meldungen.append(Meldung(
            HINWEIS,
            f"{ort.element} {s.stufe}: Stromstaffelung nicht wirksam. Der nötige Wert "
            f"{de(soll_bez, 0)} A bez. liegt über Ik max am Messort {ort.messort} "
            f"({de(ik_eigen, 0)} A bez.), das Ik-Gefälle zur nächsten Station ist zu klein. "
            f"Die Stufe wird wie eine Zeitstufe gestaffelt.", (ort.element,)))
        return unveraendert(NICHT_WIRKSAM,
                            f"{kopf} Über Ik max am Messort ({de(ik_eigen, 0)} A bez.), "
                            f"Wert aus dem Tab bleibt, Zeitstaffelung")
    if s.I_prim_A >= soll_A * (1 - KN.EPS_STROM):
        return unveraendert(BLEIBT, f"{kopf} Tab-Wert {de(s.I_prim_A, 0)} A reicht aus und "
                                    f"bleibt (es wird nie abgesenkt)")
    if IN is None or key is None:
        erg.meldungen.append(Meldung(
            WARNUNG, f"{ort.element} {s.stufe}: Faktor nicht ermittelbar, Vorschlag nicht "
                     f"setzbar.", (ort.element,)))
        return unveraendert(OHNE_BEZUG, f"{kopf} Nicht setzbar (Nennstrom unbekannt)")
    f_neu = S._aufrunden(soll_A / IN, KN.Raster_Faktor)
    I_neu = f_neu * IN
    s_neu = replace(s, I_prim_A=I_neu)
    return s_neu, Stromvorschlag(
        ort.element, s.stufe, key, s.I_prim_A, I_neu, f_alt, f_neu, ANGEHOBEN,
        f"{kopf} Faktor {de(f_neu, 2)} × IN = {de(I_neu, 0)} A "
        f"(bisher {de(s.I_prim_A, 0)} A)")


# ── Gegenpruefung ────────────────────────────────────────────────────────────
def pruefe_strom(netz, adapter=None, U_bezug_kV: float | None = None,
                 k_S: float = KN.k_S_Strom, gamma: float = KN.gamma_Reserve) -> StromPruefErgebnis:
    """
    Gegenpruefung der Ansprechwerte (ohne Zeiten):
      Stromstaffel:    I>> oben >= k_S * Bezug der naechsten Station. Gelb, wenn
                       nicht erfuellt (dann nur ueber die Zeit selektiv). Rot, wenn
                       ein Motorabgang unter seinem Anlaufstrom liegt.
      Empfindlichkeit: Ik min hinter der naechsten Station (zweipolig, ueber die
                       Trafos mit Stufensteller und Schaltgruppe) >= gamma * kleinster
                       Ansprechwert des oberen Schutzes. Gelb ab 1, rot darunter.
    Wirft nie.
    """
    erg = StromPruefErgebnis()
    try:
        return _pruefe_strom(netz, adapter, U_bezug_kV, k_S, gamma, erg)
    except Exception as exc:
        erg.meldungen.append(Meldung(
            FEHLER, f"Strompruefung abgebrochen ({type(exc).__name__}: {exc})."))
        return erg


def _pruefe_strom(netz, adapter, U_bezug_kV, k_S, gamma, erg) -> StromPruefErgebnis:
    ad = adapter if adapter is not None else netz_adapter.erzeuge_schutzstufen(netz)
    if ad.topologie is None or not ad.topologie.ok or not ad.ok:
        erg.meldungen.append(Meldung(
            FEHLER, "Topologie oder Schutzstufen enthalten Fehler. Keine Strompruefung."))
        return erg
    st = S._struktur(netz, ad, U_bezug_kV, [])
    if st is None:
        return erg
    U, topo = st["U"], ad.topologie
    zusp = S._zuspeiseknoten(topo, netz.elemente)
    ohne_ikmin = []
    for u, o in st["paare"]:
        # 1. Stromstaffel der I>>-Stufen von o
        hh = [s for s in o.stufen if ">>" in s.stufe and s.kennlinie == UMZ]
        if hh:
            I_bez, text, art, _h = _bezug_unten(netz, topo, ad, zusp, o, u, U)
            if I_bez is not None:
                soll = k_S * I_bez
                ik_eigen = _eigenes_ik_bez(netz, o, U)
                I_anl_bez = None
                if art == ART_MOTOR:
                    I_anl = netz_adapter.anlaufstrom_A(ad.p_voll.get(u.element, {}))
                    I_anl_bez = None if I_anl is None else S.auf_bezug(I_anl, u.UN_kV, U)
                for s in hh:
                    ist = S.anregestrom_bez(s, U)
                    erg.pruefungen.append(_urteil_staffel(u, o, s, ist, soll, I_bez, text, art,
                                                          ik_eigen, I_anl_bez))
        # 2. Empfindlichkeit des empfindlichsten Ansprechwerts von o
        fern = _fernknoten(netz, zusp, u)
        if fern is None:
            continue
        k = netz.knoten.get(fern)
        if k is None or k.Ik_min_kA is None:
            if fern not in ohne_ikmin:
                ohne_ikmin.append(fern)
            continue
        um = UM.umrechnen(netz, topo, k.Ik_min_kA * 1000.0, fern, o.messort, UM.MIN)
        if not um.ok:
            continue
        I_min = S.auf_bezug(um.I_A, o.UN_kV, U)
        I_an = min(S.anregestrom_bez(s, U) for s in o.stufen)
        erg.pruefungen.append(_urteil_empf(u, o, I_min, I_an, gamma, um, fern, k.Ik_min_kA))
    if ohne_ikmin:
        erg.meldungen.append(Meldung(
            HINWEIS, f"Ik min fehlt an {', '.join(ohne_ikmin)}: Empfindlichkeit der Reserve "
                     f"dahinter nicht prüfbar."))
    return erg


def _urteil_staffel(u, o, s, ist, soll, I_bez, text, art, ik_eigen, I_anl_bez) -> Stromstufenpruefung:
    kopf = f"{o.name} {s.stufe} {de(ist, 0)} A bez., nötig {de(soll, 0)} A bez. ({text})."
    if ist >= soll * (1 - KN.EPS_STROM):
        return Stromstufenpruefung("Stromstaffel", u.name, o.name, s.stufe, S.OK, soll, ist,
                                   kopf + " Stromstaffelung erfüllt.")
    if I_anl_bez is not None and ist < I_anl_bez * (1 - KN.EPS_STROM):
        return Stromstufenpruefung("Stromstaffel", u.name, o.name, s.stufe, S.ROT, soll, ist,
                                   kopf + " Unter dem Anlaufstrom: die Stufe löst beim Motoranlauf aus.")
    if ik_eigen is not None and soll > ik_eigen * (1 + KN.EPS_STROM):
        zusatz = " Stromstaffelung nicht möglich (Ik-Gefälle zu klein), nur über die Zeit selektiv."
    else:
        zusatz = " Stromstaffelung nicht erfüllt, nur über die Zeit selektiv."
    return Stromstufenpruefung("Stromstaffel", u.name, o.name, s.stufe, S.GELB, soll, ist, kopf + zusatz)


def _urteil_empf(u, o, I_min, I_an, gamma, um, fern, ik_min_kA) -> Stromstufenpruefung:
    weg = "" if not um.schritte else f" über {um.text}"
    kopf = (f"Ik min {fern} {de(ik_min_kA, 1)} kA{weg} = {de(I_min, 0)} A bez., "
            f"Ansprechwert {o.name} {de(I_an, 0)} A bez.")
    if I_min >= gamma * I_an:
        status, urteil = S.OK, f"Reserve mit Faktor {de(I_min / I_an, 1)} empfindlich genug"
    elif I_min >= I_an:
        status, urteil = S.GELB, (f"Faktor {de(I_min / I_an, 1)} liegt unter {de(gamma, 1)}, "
                                  f"knapp")
    else:
        status, urteil = S.ROT, "Ik min liegt unter dem Ansprechwert, keine Reserve"
    return Stromstufenpruefung("Empfindlichkeit", u.name, o.name, "kleinster Ansprechwert", status,
                               gamma * I_an, I_min, f"{kopf} {urteil}.")


# ── Gesamtvorschlag: Strom, dann Zeit, dann Gegenpruefung ────────────────────
def gesamtvorschlag(netz, adapter=None, U_bezug_kV: float | None = None,
                    dt_soll: float = KN.dt_Staffel_soll, k_S: float = KN.k_S_Strom,
                    t_min: float = KN.t_Vorschlag_min) -> GesamtVorschlag:
    """Erst die I>>-Ansprechwerte, dann die Zeiten mit diesen Werten. Wirft nie."""
    try:
        strom = stromvorschlag(netz, adapter, U_bezug_kV, k_S)
        erg = GesamtVorschlag(strom)
        erg.meldungen += strom.meldungen + (strom.pruefung.meldungen if strom.pruefung else [])
        if not strom.ok or strom.adapter is None:
            return erg
        erg.zeit = S.staffelvorschlag(netz, strom.adapter, strom.U_bezug_kV, dt_soll, t_min,
                                      strom_beruecksichtigt=True)
        gesehen = {(m.stufe, m.text) for m in erg.meldungen}
        for m in erg.zeit.meldungen:
            if (m.stufe, m.text) not in gesehen:
                erg.meldungen.append(m)
        return erg
    except Exception as exc:
        erg = GesamtVorschlag(StromErgebnis())
        erg.meldungen.append(Meldung(
            FEHLER, f"Gesamtvorschlag abgebrochen ({type(exc).__name__}: {exc})."))
        return erg
