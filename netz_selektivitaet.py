"""
netz_selektivitaet.py - Zeitstaffelpruefung fuer die netzweite Selektivitaetsplanung
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reines Python-Modul OHNE Streamlit (isoliert testbar).

Einstieg: pruefe_selektivitaet(netz) -> SelektivitaetErgebnis
          staffelvorschlag(netz)     -> VorschlagErgebnis (Zeiten so, dass alles passt)

Stand Woche 2 (Zeitstaffelung im Strahlennetz bzw. offenen Ring):
  1. Alle Ansprechwerte auf eine gemeinsame Bezugsspannung umrechnen.
  2. Entlang jedes Pfades zur Quelle die Schutzorte in eine Kette bringen
     (z. B. M1 -> L1 -> T1 (US) -> T1 (OS) -> E1).
  3. Je benachbartem Paar (unten, oben) pruefen, ob der obere Schutz bei jedem
     Strom, bei dem er anregt, mindestens einen Staffelabstand spaeter ausloest
     als der untere. Ergebnis als Ampel: OK / Hinweis / Prüfen!.

Pruefprinzip (wirksame Ausloesezeit):
  t_aus(Ort, I) = kleinste Zeit aller aktiven Stufen des Ortes, die bei I anregen.
  Geprueft wird dt(I) = t_aus(oben, I) - t_aus(unten, I) fuer alle Stroeme vom
  kleinsten Ansprechwert des oberen Schutzes bis zum groessten Kurzschlussstrom,
  der durch beide Schutzorte fliessen kann (Ik max am Messort des unteren
  Schutzes). Bei UMZ ist dt(I) stueckweise konstant, es genuegen deshalb die
  Ansprechwerte als Pruefstroeme. Ist eine AMZ-Stufe beteiligt, kommen
  logarithmisch verteilte Stuetzstellen dazu.

Tool-Vorgaben und Grenzen dieses Stands (bewusst, siehe Zeitplan):
  - Umrechnung mit dem Verhaeltnis der Knoten-Nennspannungen. Stufensteller und
    die Stromverteilung ueber die Schaltgruppe (z. B. zweipoliger Fehler hinter
    Dy) bleiben unberuecksichtigt. Das gehoert zur Stromstaffelung (Woche 3).
  - Nur Phasenstufen 50/51. Erdfehlerstufen werden nicht gestaffelt.
  - Fehlt Ik max am Knoten, wird ohne obere Stromgrenze geprueft (strenger)
    und darauf hingewiesen.
  - OS- und US-Stufe eines Trafos werden wie zwei Schutzorte behandelt und
    gegeneinander gestaffelt.
  - Staffelabstand: konstanten_netz.py, Herleitung in
    docs/tool_vorgabe_staffelabstand.md.

Staffelvorschlag (reine Zeitstaffelung):
  Von der Last zur Quelle wird jede UMZ-Stufe eines Schutzortes so schnell wie
  moeglich gesetzt, aber einen Staffelabstand ueber allem, was darunter bei
  demselben Strom ausloest. Endpunkte (Schutzorte ohne weiteren Schutz
  darunter, z. B. Motor oder die US-Seite des letzten Trafos) behalten die
  Zeiten aus ihrem Tab, der Netzbetreiber ebenso (feste Obergrenze). AMZ-Stufen
  werden nicht veraendert, nur beruecksichtigt. Der Vorschlag wird anschliessend
  mit pruefe_selektivitaet gegengeprueft.

Robustheit: Das Modul wirft nie. Unvollstaendige oder nicht bewertbare Daten
fuehren zu Meldungen.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import konstanten_netz as KN
import netz_adapter
from netz_adapter import UMZ, Schutzstufe
from netz_modell import Netz
from netz_topologie import FEHLER, HINWEIS, WARNUNG, Meldung
from utils import de

# Ampelstufen wie in den Betriebsmittel-Tabs (utils.AMPEL_EMOJI)
OK, GELB, ROT = "OK", "Hinweis", "Prüfen!"
_RANG = {OK: 0, GELB: 1, ROT: 2}


# ── Datenklassen ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Schutzort:
    """Ein Messort mit allen Stufen eines Elements. Ein Trafo hat zwei (US und OS)."""
    element: str
    seite: str            # "OS" / "US" beim Trafo, sonst ""
    messort: str          # Knoten-ID
    UN_kV: float
    stufen: tuple         # aktive Schutzstufen an diesem Ort

    @property
    def name(self) -> str:
        return f"{self.element} ({self.seite})" if self.seite else self.element

    @property
    def schluessel(self) -> tuple:
        return (self.element, self.messort)


@dataclass(frozen=True)
class Staffelpruefung:
    """Ergebnis fuer ein Paar benachbarter Schutzorte (unten = naeher an der Last)."""
    unten: str                    # Anzeigename, z. B. "L1"
    oben: str                     # Anzeigename, z. B. "T1 (US)"
    status: str                   # OK / Hinweis / Prüfen!
    dt_s: float | None            # kleinster Zeitabstand, None wenn nicht bewertbar
    I_bez_A: float | None         # Strom (auf Bezugsspannung), bei dem dt_s auftritt
    stufe_unten: str = ""
    stufe_oben: str = ""
    t_unten_s: float | None = None
    t_oben_s: float | None = None
    I_grenz_bez_A: float | None = None    # Ik max am unteren Messort, None = unbekannt
    text: str = ""


@dataclass
class SelektivitaetErgebnis:
    U_bezug_kV: float | None = None
    dt_soll_s: float = KN.dt_Staffel_soll
    dt_min_s: float = KN.dt_Staffel_min
    orte: list = field(default_factory=list)          # alle Schutzorte
    pfade: list = field(default_factory=list)         # Ketten als Listen von Anzeigenamen
    pruefungen: list = field(default_factory=list)    # Staffelpruefung je Paar
    meldungen: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(m.stufe == FEHLER for m in self.meldungen)

    @property
    def status(self) -> str | None:
        """Schlechteste Ampel aller Pruefungen. None, wenn nichts geprueft wurde."""
        if not self.pruefungen:
            return None
        return max((p.status for p in self.pruefungen), key=_RANG.get)

    def pruefung(self, unten: str, oben: str):
        for p in self.pruefungen:
            if p.unten == unten and p.oben == oben:
                return p
        return None


@dataclass(frozen=True)
class Zeitvorschlag:
    element: str
    stufe: str
    parameter: str | None       # Schluessel im Element-Parametersatz (None = nicht setzbar)
    t_alt_s: float
    t_neu_s: float
    grund: str

    @property
    def geaendert(self) -> bool:
        return abs(self.t_alt_s - self.t_neu_s) > KN.EPS_ZEIT


@dataclass
class VorschlagErgebnis:
    vorschlaege: list = field(default_factory=list)      # Zeitvorschlag je UMZ-Stufe
    pruefung: SelektivitaetErgebnis | None = None         # Gegenpruefung mit den neuen Zeiten
    meldungen: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(m.stufe == FEHLER for m in self.meldungen)

    @property
    def geaendert(self) -> list:
        return [v for v in self.vorschlaege if v.geaendert]

    def parameter_je_element(self) -> dict:
        """
        Element-ID -> {Parameter: Zeit} fuer jedes Element mit mindestens einer Aenderung.
        Es werden ALLE setzbaren Zeiten des Elements geschrieben, auch unveraenderte:
        beim Trafo folgt die US-Zeit der OS-Zeit, solange sie nicht eigens gesetzt ist.
        Nur die geaenderte OS-Zeit zu schreiben wuerde die US-Seite mitziehen.
        """
        betroffen = {v.element for v in self.geaendert}
        out = {}
        for v in self.vorschlaege:
            if v.element in betroffen and v.parameter and v.t_neu_s == v.t_neu_s:
                out.setdefault(v.element, {})[v.parameter] = v.t_neu_s
        return out


# ── 1. Umrechnung auf Bezugsspannung ─────────────────────────────────────────
def auf_bezug(I_A: float, UN_kV: float, U_bezug_kV: float) -> float:
    """
    Strom von der Spannungsebene UN auf die Bezugsspannung umrechnen.
    Gleiche Leistung auf beiden Ebenen: I_bez = I * UN / U_bezug.
    Beispiel: 160 A bei 110 kV entsprechen 1760 A bei 10 kV.
    """
    return I_A * UN_kV / U_bezug_kV


def waehle_bezugsspannung(stufen) -> float | None:
    """
    Tool-Vorgabe: die Spannungsebene mit den meisten Schutzstufen, bei
    Gleichstand die hoehere. Im Industrienetz ist das die MS-Ebene, auf der
    auch der Staffelplan gelesen wird.
    """
    zaehler = {}
    for s in stufen:
        zaehler[s.UN_kV] = zaehler.get(s.UN_kV, 0) + 1
    if not zaehler:
        return None
    return max(zaehler, key=lambda u: (zaehler[u], u))


# ── 2. Kennlinien: Anregung und Ausloesezeit einer Stufe ─────────────────────
def _ist_zahl(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def bewertbar(s: Schutzstufe) -> bool:
    """True, wenn die Stufe in der Zeitstaffelung gerechnet werden kann."""
    if not s.aktiv or not _ist_zahl(s.I_prim_A) or s.I_prim_A <= 0:
        return False
    if not _ist_zahl(s.UN_kV) or s.UN_kV <= 0:
        return False
    if s.kennlinie == UMZ:
        return _ist_zahl(s.t_s) and s.t_s >= 0
    return s.kennlinie in KN.AMZ_KENNLINIEN and _ist_zahl(s.T_mult) and s.T_mult > 0


def anregestrom_bez(s: Schutzstufe, U_bezug_kV: float) -> float:
    """Strom auf Bezugsspannung, ab dem die Stufe anregt (AMZ: 1,1 * Ip)."""
    I = auf_bezug(s.I_prim_A, s.UN_kV, U_bezug_kV)
    return I if s.kennlinie == UMZ else I * KN.AMZ_Anregefaktor


def zeit_der_stufe(s: Schutzstufe, I_bez_A: float, U_bezug_kV: float) -> float | None:
    """Ausloesezeit der Stufe beim Strom I (auf Bezugsspannung). None = regt nicht an."""
    if I_bez_A < anregestrom_bez(s, U_bezug_kV) * (1 - KN.EPS_STROM):
        return None
    if s.kennlinie == UMZ:
        return float(s.t_s)
    k, alpha = KN.AMZ_KENNLINIEN[s.kennlinie]
    Ip = auf_bezug(s.I_prim_A, s.UN_kV, U_bezug_kV)
    nenner = (I_bez_A / Ip) ** alpha - 1
    if nenner <= 0:
        return None
    return s.T_mult * k / nenner


def ausloesezeit(ort: Schutzort, I_bez_A: float, U_bezug_kV: float) -> tuple:
    """Wirksame Ausloesezeit des Schutzortes: (t, Stufe) der schnellsten angeregten Stufe."""
    bester = (None, None)
    for s in ort.stufen:
        t = zeit_der_stufe(s, I_bez_A, U_bezug_kV)
        if t is not None and (bester[0] is None or t < bester[0]):
            bester = (t, s)
    return bester


# ── 3. Schutzorte und Ketten entlang der Pfade ───────────────────────────────
def _zuspeiseknoten(topo, elemente) -> dict:
    """Element-ID -> Knoten, von dem aus das Element versorgt wird (nur Kanten)."""
    zusp = {}
    for knoten, eid in topo.zufuehrung.items():
        e = elemente[eid]
        zusp[eid] = e.von if e.nach == knoten else e.nach
    return zusp


def _orte_des_elements(e, stufen, zusp) -> list:
    """Schutzorte eines Elements in Richtung Quelle (lastseitiger Messort zuerst)."""
    je_messort = {}
    for s in stufen:
        je_messort.setdefault(s.messort, []).append(s)
    speiseseite = zusp.get(e.id)
    reihenfolge = sorted(je_messort, key=lambda k: (k == speiseseite, k))
    orte = []
    for k in reihenfolge:
        seite = ""
        if e.typ == "trafo":
            seite = "OS" if k == e.von else "US"
        orte.append(Schutzort(e.id, seite, k, je_messort[k][0].UN_kV, tuple(je_messort[k])))
    return orte


def _grenzstrom_bez(knoten, ort: Schutzort, U_bezug_kV: float) -> float | None:
    """Groesster Strom durch unten und oben: Ik max am Messort des unteren Schutzes."""
    k = knoten.get(ort.messort)
    if k is None or k.Ik_max_kA is None:
        return None
    return auf_bezug(k.Ik_max_kA * 1000.0, k.UN_kV, U_bezug_kV)


# ── 4. Pruefung eines Paares ─────────────────────────────────────────────────
def _pruefstroeme(unten: Schutzort, oben: Schutzort, U: float, I_grenz) -> list:
    an_oben = [anregestrom_bez(s, U) for s in oben.stufen]
    an_alle = an_oben + [anregestrom_bez(s, U) for s in unten.stufen]
    I_min = min(an_oben)
    I_max = I_grenz if I_grenz is not None else max(an_alle)
    if I_max < I_min * (1 - KN.EPS_STROM):
        return []                                   # oberer Schutz regt nie an
    I_max = max(I_max, I_min)
    punkte = {I for I in an_alle if I_min * (1 - KN.EPS_STROM) <= I <= I_max * (1 + KN.EPS_STROM)}
    punkte.add(I_max)
    amz = any(s.kennlinie != UMZ for s in unten.stufen + oben.stufen)
    if amz and I_max > I_min:
        n = KN.AMZ_Stuetzstellen
        q = (I_max / I_min) ** (1 / n)
        punkte.update(I_min * q ** i for i in range(n + 1))
    return sorted(punkte)


def pruefe_paar(unten: Schutzort, oben: Schutzort, U_bezug_kV: float,
                I_grenz_bez_A: float | None = None,
                dt_soll: float = KN.dt_Staffel_soll,
                dt_min: float = KN.dt_Staffel_min) -> Staffelpruefung:
    """Zeitstaffelung zwischen zwei benachbarten Schutzorten pruefen."""
    U = U_bezug_kV
    ohne_grenze = ("" if I_grenz_bez_A is not None else
                   f" Ohne Ik max an {unten.messort} wurde ohne obere Stromgrenze geprüft.")
    stroeme = _pruefstroeme(unten, oben, U, I_grenz_bez_A)
    if not stroeme:
        return Staffelpruefung(
            unten.name, oben.name, OK, None, None, I_grenz_bez_A=I_grenz_bez_A,
            text=(f"{oben.name} regt bei Fehlern hinter {unten.name} nicht an "
                  f"(kleinster Ansprechwert über Ik max {de(I_grenz_bez_A, 0)} A). "
                  f"Selektiv, aber keine Reserve durch {oben.name}."))

    schlecht = None          # (dt, I, t_u, s_u, t_o, s_o) mit kleinstem dt
    luecke = None            # kleinster Strom, bei dem oben anregt und unten nicht
    for I in stroeme:
        t_o, s_o = ausloesezeit(oben, I, U)
        if t_o is None:
            continue
        t_u, s_u = ausloesezeit(unten, I, U)
        if t_u is None:
            if luecke is None:
                luecke = (I, s_o)
            continue
        dt = t_o - t_u
        if schlecht is None or dt < schlecht[0] - KN.EPS_ZEIT:
            schlecht = (dt, I, t_u, s_u, t_o, s_o)

    text_luecke = ""
    if luecke is not None:
        text_luecke = (f" {oben.name} ({luecke[1].stufe}) regt ab {de(luecke[0], 0)} A an, "
                       f"{unten.name} dort noch nicht. Ansprechwerte prüfen (Stromstaffelung).")

    if schlecht is None:
        return Staffelpruefung(
            unten.name, oben.name, GELB, None, luecke[0] if luecke else None,
            I_grenz_bez_A=I_grenz_bez_A,
            text=("Kein gemeinsamer Strombereich, in dem beide Schutzorte anregen."
                  + text_luecke + ohne_grenze))

    dt, I, t_u, s_u, t_o, s_o = schlecht
    if dt < dt_min - KN.EPS_ZEIT:
        status = ROT
        urteil = (f"nicht selektiv: Abstand {de(dt, 2)} s liegt unter dem technischen "
                  f"Mindestwert {de(dt_min, 2)} s")
    elif dt < dt_soll - KN.EPS_ZEIT:
        status = GELB
        urteil = (f"knapp: Abstand {de(dt, 2)} s liegt unter dem Soll {de(dt_soll, 2)} s, "
                  f"aber über dem Mindestwert {de(dt_min, 2)} s")
    else:
        status = OK
        urteil = f"selektiv: Abstand {de(dt, 2)} s (Soll {de(dt_soll, 2)} s)"
    if status == OK and luecke is not None:
        status = GELB
    text = (f"Bei {de(I, 0)} A: {unten.name} {s_u.stufe} {de(t_u, 2)} s, "
            f"{oben.name} {s_o.stufe} {de(t_o, 2)} s. Ergebnis {urteil}."
            + text_luecke + ohne_grenze)
    return Staffelpruefung(unten.name, oben.name, status, round(dt, 6), I,
                           s_u.stufe, s_o.stufe, t_u, t_o, I_grenz_bez_A, text)


# ── Einstieg ─────────────────────────────────────────────────────────────────
def pruefe_selektivitaet(netz: Netz, adapter=None, U_bezug_kV: float | None = None,
                         dt_soll: float = KN.dt_Staffel_soll,
                         dt_min: float = KN.dt_Staffel_min) -> SelektivitaetErgebnis:
    """
    Zeitstaffelung des gesamten Netzes pruefen.
    adapter: Ergebnis von netz_adapter.erzeuge_schutzstufen(netz), wird sonst erzeugt.
    U_bezug_kV: Bezugsspannung, sonst waehle_bezugsspannung().
    """
    erg = SelektivitaetErgebnis(dt_soll_s=dt_soll, dt_min_s=dt_min)
    try:
        return _pruefe(netz, adapter, U_bezug_kV, dt_soll, dt_min, erg)
    except Exception as exc:              # Auswertung darf die Oberflaeche nie abstuerzen lassen
        erg.meldungen.append(Meldung(
            FEHLER, f"Staffelprüfung abgebrochen ({type(exc).__name__}: {exc})."))
        return erg


def _struktur(netz, ad, U_bezug_kV, meldungen) -> dict | None:
    """
    Gemeinsamer Unterbau von Pruefung und Vorschlag: bewertbare Stufen, Bezugsspannung,
    Schutzorte, Ketten (Pfade) und die zu pruefenden Paare (unten, oben).
    None, wenn nichts zu pruefen ist (Meldung ist dann angehaengt).
    """
    elemente, knoten = netz.elemente, netz.knoten
    gute = {}
    for s in ad.stufen:
        if not s.aktiv:
            continue
        if bewertbar(s):
            gute.setdefault(s.element, []).append(s)
        elif s.kennlinie != UMZ and s.kennlinie not in KN.AMZ_KENNLINIEN:
            meldungen.append(Meldung(
                HINWEIS, f"{s.element} {s.stufe}: Kennlinie „{s.kennlinie}“ wird in der "
                         f"Zeitstaffelung noch nicht bewertet.", (s.element,)))
        else:
            meldungen.append(Meldung(
                WARNUNG, f"{s.element} {s.stufe}: Ansprechwert oder Zeit fehlt, "
                         f"Stufe wird nicht bewertet.", (s.element,)))
    alle = [s for liste in gute.values() for s in liste]
    if not alle:
        meldungen.append(Meldung(HINWEIS, "Keine bewertbaren Schutzstufen vorhanden."))
        return None

    if U_bezug_kV is not None and not (_ist_zahl(U_bezug_kV) and U_bezug_kV > 0):
        meldungen.append(Meldung(
            WARNUNG, f"Bezugsspannung {U_bezug_kV!r} ist ungültig, es wird automatisch gewählt."))
        U_bezug_kV = None
    U = float(U_bezug_kV) if U_bezug_kV is not None else waehle_bezugsspannung(alle)

    topo = ad.topologie
    zusp = _zuspeiseknoten(topo, elemente)
    orte = {eid: _orte_des_elements(elemente[eid], st, zusp) for eid, st in gute.items()}

    pfade, paare, ohne_schutz = [], [], set()
    for eid in sorted(orte):
        pfad = topo.pfad_zur_quelle(eid)
        if len(pfad) < 2:
            continue
        kette = []
        for pid in pfad:
            if pid in orte:
                kette += orte[pid]
            elif elemente[pid].typ in ("trafo", "leitung", "motor"):
                ohne_schutz.add(pid)
        namen = [o.name for o in kette]
        # Teilpfade (z. B. L1 -> T1 -> E1) stecken schon im Pfad des Abgangs dahinter
        if len(namen) >= 2 and not any(_ist_ende_von(namen, p) for p in pfade):
            pfade = [p for p in pfade if not _ist_ende_von(p, namen)] + [namen]
        for unten, oben in zip(kette, kette[1:]):
            schl = (unten.schluessel, oben.schluessel)
            if schl not in {(u.schluessel, o.schluessel) for u, o in paare}:
                paare.append((unten, oben))

    for pid in sorted(ohne_schutz):
        meldungen.append(Meldung(
            WARNUNG, f"{pid} liegt in einem Versorgungspfad, hat aber keine bewertbaren "
                     f"Schutzstufen. Die Staffelung wird über {pid} hinweg geprüft.", (pid,)))
    if not any(elemente[e].typ == "einspeisung" for e in orte):
        meldungen.append(Meldung(
            HINWEIS, "Ohne Schutz des Netzbetreibers an der Einspeisung endet die "
                     "Staffelprüfung am obersten eigenen Schutz."))
    return {"U": U, "orte": [o for eid in sorted(orte) for o in orte[eid]],
            "pfade": pfade, "paare": paare}


def _pruefe(netz, adapter, U_bezug_kV, dt_soll, dt_min, erg) -> SelektivitaetErgebnis:
    if not (_ist_zahl(dt_soll) and _ist_zahl(dt_min) and 0 < dt_min <= dt_soll):
        erg.meldungen.append(Meldung(
            FEHLER, "Staffelabstand ungültig: es muss 0 < Mindestwert <= Soll gelten."))
        return erg
    ad = adapter if adapter is not None else netz_adapter.erzeuge_schutzstufen(netz)
    topo = ad.topologie
    if topo is None or not topo.ok or not ad.ok:
        erg.meldungen.append(Meldung(
            FEHLER, "Topologie oder Schutzstufen enthalten Fehler. "
                    "Die Staffelprüfung läuft erst danach."))
        return erg
    st = _struktur(netz, ad, U_bezug_kV, erg.meldungen)
    if st is None:
        return erg
    U = st["U"]
    erg.U_bezug_kV, erg.orte, erg.pfade = U, st["orte"], st["pfade"]
    erg.pruefungen = [pruefe_paar(u, o, U, _grenzstrom_bez(netz.knoten, u, U), dt_soll, dt_min)
                      for u, o in st["paare"]]
    return erg


# ── Staffelvorschlag ─────────────────────────────────────────────────────────
def _aufrunden(wert: float, raster: float) -> float:
    schritte = int(wert / raster + 1e-9)
    if schritte * raster < wert - 1e-9:
        schritte += 1
    return round(schritte * raster, 6)


def staffelvorschlag(netz: Netz, adapter=None, U_bezug_kV: float | None = None,
                     dt_soll: float = KN.dt_Staffel_soll,
                     t_min: float = KN.t_Vorschlag_min) -> VorschlagErgebnis:
    """
    Zeiten fuer eine reine Zeitstaffelung vorschlagen (siehe Modulkopf).
    Jede UMZ-Stufe erhaelt die kleinste Zeit >= t_min, die bei jedem Strom, bei dem sie
    anregt, einen Staffelabstand dt_soll ueber der wirksamen Ausloesezeit aller
    Schutzorte darunter liegt. Gerundet auf das Einstellraster.
    """
    erg = VorschlagErgebnis()
    try:
        return _vorschlag(netz, adapter, U_bezug_kV, dt_soll, t_min, erg)
    except Exception as exc:
        erg.meldungen.append(Meldung(
            FEHLER, f"Staffelvorschlag abgebrochen ({type(exc).__name__}: {exc})."))
        return erg


def _vorschlag(netz, adapter, U_bezug_kV, dt_soll, t_min, erg) -> VorschlagErgebnis:
    if not (_ist_zahl(dt_soll) and dt_soll > 0 and _ist_zahl(t_min) and t_min >= 0):
        erg.meldungen.append(Meldung(FEHLER, "Staffelabstand oder Mindestzeit ungültig."))
        return erg
    ad = adapter if adapter is not None else netz_adapter.erzeuge_schutzstufen(netz)
    if ad.topologie is None or not ad.topologie.ok or not ad.ok:
        erg.meldungen.append(Meldung(
            FEHLER, "Topologie oder Schutzstufen enthalten Fehler. Kein Staffelvorschlag."))
        return erg
    st = _struktur(netz, ad, U_bezug_kV, erg.meldungen)
    if st is None:
        return erg
    U, paare = st["U"], st["paare"]
    elemente, knoten = netz.elemente, netz.knoten

    # Was liegt unter welchem Schutzort? Reihenfolge: ein Ort erst, wenn alles darunter fest ist.
    unter = {}
    for u, o in paare:
        unter.setdefault(o.schluessel, []).append(u)
    neu = {o.schluessel: o for o in st["orte"]}        # aktueller Stand je Schutzort
    fertig = set(k for k in neu if k not in unter)      # Endpunkte: unveraendert
    for ort in st["orte"]:
        if ort.schluessel in fertig:
            for s in ort.stufen:
                _merke(erg, elemente, ort, s, s.t_s,
                       "Endpunkt, Zeit aus dem Tab bleibt" if s.kennlinie == UMZ else "AMZ, unverändert")
    offen = [k for k in neu if k not in fertig]
    while offen:
        naechste = [k for k in offen if all(u.schluessel in fertig for u in unter[k])]
        if not naechste:
            erg.meldungen.append(Meldung(FEHLER, "Zirkuläre Staffelkette, kein Vorschlag möglich."))
            return erg
        for k in naechste:
            ort = neu[k]
            if elemente[ort.element].typ == "einspeisung":
                for s in ort.stufen:
                    _merke(erg, elemente, ort, s, s.t_s, "Netzbetreiber, feste Obergrenze")
            else:
                stufen = []
                for s in ort.stufen:
                    if s.kennlinie != UMZ:
                        _merke(erg, elemente, ort, s, None, "AMZ, unverändert (nur berücksichtigt)")
                        stufen.append(s)
                        continue
                    t_neu, grund = _zeit_fuer_stufe(ort, s, [neu[u.schluessel] for u in unter[k]],
                                                    U, knoten, dt_soll, t_min)
                    _merke(erg, elemente, ort, s, t_neu, grund)
                    stufen.append(replace(s, t_s=t_neu))
                neu[k] = replace(ort, stufen=tuple(stufen))
            fertig.add(k)
            offen.remove(k)

    # Gegenpruefung mit den neuen Zeiten: Adapter-Kopie mit ersetzten Stufen
    ersetzt = {(s.element, s.stufe): s for o in neu.values() for s in o.stufen}
    ad_neu = replace(ad, stufen=[ersetzt.get((s.element, s.stufe), s) for s in ad.stufen])
    erg.pruefung = pruefe_selektivitaet(netz, ad_neu, U, dt_soll)
    for p in erg.pruefung.pruefungen:
        if p.status != OK and elemente[_element_von_name(p.oben)].typ == "einspeisung":
            detail = (f"{p.unten} braucht {de(p.t_unten_s, 2)} s, {p.oben} löst bei "
                      f"{de(p.t_oben_s, 2)} s aus." if p.dt_s is not None else p.text)
            erg.meldungen.append(Meldung(
                WARNUNG, f"Die Kette passt nicht unter den Schutz des Netzbetreibers: {detail} "
                         f"Abhilfe: weniger Staffelstufen, kürzere Zeiten an den Endpunkten "
                         f"oder Stromstaffelung über die I>>-Stufen."))
    return erg


def _element_von_name(name: str) -> str:
    return name.split(" (")[0]


def _merke(erg, elemente, ort, s, t_neu, grund) -> None:
    key = netz_adapter.ZEIT_PARAMETER.get(elemente[ort.element].typ, {}).get(s.stufe)
    t_alt = s.t_s if s.t_s is not None else float("nan")
    t_neu = t_alt if t_neu is None else t_neu
    erg.vorschlaege.append(Zeitvorschlag(ort.element, s.stufe, key, t_alt, t_neu, grund))


def _zeit_fuer_stufe(ort, s, darunter, U, knoten, dt_soll, t_min) -> tuple:
    """Kleinste Zeit der Stufe s, die ueber allen Schutzorten darunter liegt."""
    I_an = anregestrom_bez(s, U)
    bedarf, wegen = t_min, "Mindestzeit (Tool-Vorgabe)"
    for u in darunter:
        I_grenz = _grenzstrom_bez(knoten, u, U)
        for I in _pruefstroeme(u, ort, U, I_grenz):
            if I < I_an * (1 - KN.EPS_STROM):
                continue
            t_u, s_u = ausloesezeit(u, I, U)
            if t_u is not None and t_u + dt_soll > bedarf + KN.EPS_ZEIT:
                bedarf, wegen = t_u + dt_soll, f"{u.name} {s_u.stufe} {de(t_u, 2)} s bei {de(I, 0)} A"
    return _aufrunden(bedarf, KN.dt_Raster), wegen


def _ist_ende_von(kurz: list, lang: list) -> bool:
    """True, wenn die Kette 'kurz' das quellseitige Ende der Kette 'lang' ist."""
    return len(kurz) <= len(lang) and lang[len(lang) - len(kurz):] == kurz
