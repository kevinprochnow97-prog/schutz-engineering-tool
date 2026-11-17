"""
netz_kurzschluss.py - Kurzschlussstroeme aus den Netzdaten
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reines Python-Modul OHNE Streamlit (isoliert testbar).

Einstieg:
  berechne(netz)                 -> KurzschlussErgebnis  (ein Schaltzustand, so wie im Netz)
  berechne_schaltzustaende(netz) -> Liste KurzschlussErgebnis (im Ring je Trennstellenlage
                                    und zusaetzlich mit geschlossenem Ring)
  vergleiche(netz, ergebnis)     -> Liste Vergleich (eingegeben, berechnet, Abweichung)
  ersetze_ik(netz)               -> (Netzkopie, Ersetzungen, Rueckfaelle, Meldungen): berechnete
                                    Werte ersetzen die eingegebenen (Ring, je Lage)
  ergaenze_ik(netz)              -> (Netzkopie, Liste Ergaenzung): berechnete Werte NUR an
                                    Knoten ohne Handwert

Grundsatz: Ein von Hand eingegebener Ik-Wert hat Vorrang. Einzige Ausnahme ist die Staffelung im
Ring (ersetze_ik, Entscheidung 17.11.2026): dort ist ein Wert fuer alle Lagen falsch. Dieses Modul schreibt
nie in das uebergebene Netz. Berechnete Werte stehen im Ergebnisobjekt, ergaenze_ik
liefert eine Kopie und laesst vorhandene Werte unveraendert.

Verfahren (Tool-Vorgabe in Anlehnung an IEC 60909-0, Herleitung, Annahmen und offene
Pruefpunkte in docs/tool_vorgabe_kurzschluss.md):
  Ersatzspannungsquelle c * UN / sqrt(3) am Fehlerort, alle anderen Quellen kurzgeschlossen.
  Mitsystem-Impedanzen in bezogenen Groessen (S_B = 100 MVA, U_B = UN des Knotens). Das
  entspricht der Umrechnung ueber das Verhaeltnis der Knoten-Nennspannungen.
  Knotenadmittanzmatrix Y, Kurzschlussimpedanz am Knoten k = Diagonalelement von Y^-1.
  Im Strahlennetz ist das die Reihensumme der Impedanzen bis zur Einspeisung (Tests).

    Einspeisung  z = c * S_B / Sk         R/X = RX_Q (ohne Angabe 0,1)
    Trafo        z = uk * S_B / Sn * K_T  R aus ukr_pct (ohne Angabe 0), Mittelstellung
    Leitung      Z = (R' + jX') * L       R' = R_Belag oder X'/tan(phi), Ik min mit warmem Leiter
    Kupplung     Z = 0                    beide Knoten werden zu einem zusammengefasst
    Motor        Z = UN / (sqrt(3) * I_Anlauf), nur beim groessten Kurzschlussstrom

  Ik max: dreipolig, c_max, Sk_max. Hauptwert OHNE Motoren (netzseitiger Strom, den die
          vorgelagerten Schutzgeraete fuehren). Der Wert mit Motoren steht daneben.
  Ik min: zweipolig = sqrt(3)/2 * Ik3, c_min, Sk_min, ohne Motoren, warmer Leiter.

Nicht berechnet: Generatoren, Erdfehler (kein Nullsystem), Stoss-, Ausschalt- und
thermischer Strom. Der Stufensteller wirkt nicht auf die Impedanz, er geht wie bisher in
netz_umrechnung.py als Faktor auf den Strom ein.

Robustheit: Das Modul wirft nie. Fehlen Daten, gibt es Meldungen und fuer die betroffenen
Knoten keinen Wert (None) statt eines geschaetzten.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass, field

import numpy as np

import calc_motor
import konstanten_netz as KN
from netz_modell import ModellFehler, Netz
from netz_topologie import FEHLER, HINWEIS, WARNUNG, Meldung
from utils import de

S_B_MVA = 100.0          # Bezugsleistung der bezogenen Rechnung (kuerzt sich heraus)
MAX, MIN = "max", "min"
SQRT3 = math.sqrt(3.0)

AKTUELL, LAGE, GESCHLOSSEN = "aktuell", "lage", "geschlossen"


# ── Datenklassen ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class ElementImpedanz:
    """Impedanz eines Elements in Ohm auf seiner eigenen Spannung, je Fall. Fuer die Anzeige."""
    element: str
    typ: str
    UN_kV: float                    # Spannung, auf die Z bezogen ist (Trafo: US-Seite)
    Z_max: complex | None           # None: fuer diesen Fall nicht ermittelbar
    Z_min: complex | None
    annahmen: tuple = ()


@dataclass(frozen=True)
class KnotenIk:
    knoten: str
    UN_kV: float
    Ik_max_kA: float | None = None            # dreipolig, ohne Motoren
    Ik_max_mit_Motor_kA: float | None = None  # dreipolig, mit Motoren
    Ik_min_kA: float | None = None            # zweipolig, kleinster
    Zk_max_Ohm: complex | None = None         # Kurzschlussimpedanz am Knoten (ohne Motoren)
    Zk_min_Ohm: complex | None = None

    @property
    def Ik_Motor_kA(self) -> float | None:
        """Zuwachs durch die Motoren (Betragsdifferenz), None wenn nicht ermittelbar."""
        if self.Ik_max_kA is None or self.Ik_max_mit_Motor_kA is None:
            return None
        return max(self.Ik_max_mit_Motor_kA - self.Ik_max_kA, 0.0)


@dataclass
class KurzschlussErgebnis:
    bezeichnung: str = "Aktueller Schaltzustand"
    art: str = AKTUELL                          # AKTUELL, LAGE oder GESCHLOSSEN
    trennstelle: str | None = None              # nur bei art == LAGE
    knoten: dict = field(default_factory=dict)  # Knoten-ID -> KnotenIk
    impedanzen: list = field(default_factory=list)
    meldungen: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(m.stufe == FEHLER for m in self.meldungen)


@dataclass(frozen=True)
class Vergleich:
    knoten: str
    groesse: str                 # MAX oder MIN
    eingegeben_kA: float | None
    berechnet_kA: float | None
    wirksam: str                 # "eingegeben", "berechnet" oder "fehlt"

    @property
    def abweichung(self) -> float | None:
        """(berechnet - eingegeben) / eingegeben, None wenn einer der Werte fehlt."""
        if self.eingegeben_kA is None or self.berechnet_kA is None:
            return None
        return (self.berechnet_kA - self.eingegeben_kA) / self.eingegeben_kA

    @property
    def auffaellig(self) -> bool:
        a = self.abweichung
        return a is not None and abs(a) > KN.Ik_Abweichung_Hinweis + 1e-12


@dataclass(frozen=True)
class Ergaenzung:
    knoten: str
    groesse: str                 # MAX oder MIN
    wert_kA: float


# ── Hilfen ───────────────────────────────────────────────────────────────────
def _zahl(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _pos(p: dict, key: str):
    v = p.get(key)
    return float(v) if _zahl(v) and v > 0 else None


def c_faktor(UN_kV: float, fall: str) -> float:
    ns = UN_kV <= KN.U_Grenze_NS_kV
    if fall == MAX:
        return KN.c_max_NS if ns else KN.c_max_HS
    return KN.c_min_NS if ns else KN.c_min_HS


def _rx_zu_z(betrag: float, rx: float) -> complex:
    """Komplexe Impedanz aus Betrag und Verhaeltnis R/X."""
    x = betrag / math.hypot(rx, 1.0)
    return complex(rx * x, x)


def faktor_KT(uk: float, ukr: float, UN_US_kV: float) -> float:
    """K_T = 0,95 * c_max / (1 + 0,6 * x_T), x_T = bezogene Reaktanz, c_max der US-Seite."""
    if not KN.KT_anwenden:
        return 1.0
    x_T = math.sqrt(max(uk * uk - ukr * ukr, 0.0))
    return KN.KT_a * c_faktor(UN_US_kV, MAX) / (1.0 + KN.KT_b * x_T)


# ── Impedanzen je Element (bezogen auf S_B und UN des Anschlussknotens) ──────
def _z_einspeisung(e, kn) -> tuple:
    """(z_max, z_min, Annahmen, Meldungen) in bezogenen Groessen. None, wenn Sk fehlt."""
    UN = kn[e.nach].UN_kV
    rx = e.p.get("RX_Q")
    ann = []
    if not (_zahl(rx) and rx >= 0):
        rx = KN.RX_Q_def
        ann.append(f"R/X = {de(rx, 2)} (Tool-Vorgabe)")
    out, meld = [], []
    for fall, key in ((MAX, "Sk_max_MVA"), (MIN, "Sk_min_MVA")):
        Sk = _pos(e.p, key)
        if Sk is None:
            out.append(None)
            meld.append(Meldung(
                WARNUNG, f"{e.id}: {key} fehlt. Ik {fall} wird nicht berechnet.", (e.id,)))
        else:
            out.append(_rx_zu_z(c_faktor(UN, fall) * S_B_MVA / Sk, rx))
    return out[0], out[1], ann, meld


def _z_trafo(e, kn) -> tuple:
    """(z_max, z_min, Annahmen, Fehlertext). K_T nur bei Ik max (IEC 60909-0:2016, 6.3.3)."""
    Sn, uk_pct = _pos(e.p, "Sn_MVA"), _pos(e.p, "uk_pct")
    if Sn is None or uk_pct is None:
        return None, None, [], "Sn_MVA oder uk_pct fehlt"
    uk = uk_pct / 100.0
    ukr_pct = e.p.get("ukr_pct")
    ann = []
    if _zahl(ukr_pct) and 0 <= ukr_pct < uk_pct:
        ukr = ukr_pct / 100.0
    else:
        ukr = 0.0
        ann.append("R = 0 (ukr_pct nicht angegeben)")
    kt = faktor_KT(uk, ukr, kn[e.nach].UN_kV)
    if KN.KT_anwenden:
        ann.append(f"K_T = {de(kt, 4)}")
    if KN.KT_anwenden and not KN.KT_bei_min:
        ann.append("K_T nur bei Ik max")
    ann.append("Stufensteller in Mittelstellung")
    z = complex(ukr, math.sqrt(uk * uk - ukr * ukr)) * S_B_MVA / Sn
    return z * kt, (z * kt if KN.KT_bei_min else z), ann, ""


def _z_leitung(e, kn) -> tuple:
    """(z_max, z_min, Annahmen, Fehlertext, Warnung)."""
    L, Xb = _pos(e.p, "L_km"), _pos(e.p, "X_Belag")
    if L is None or Xb is None:
        return None, None, [], "L_km oder X_Belag fehlt", ""
    UN = kn[e.von].UN_kV
    ann, warn = [], ""
    Rb = e.p.get("R_Belag")
    phi = e.p.get("phi_Ltg")
    if _zahl(Rb) and Rb >= 0:
        Rb = float(Rb)
    elif _zahl(phi) and 0 < phi < 90:
        Rb = Xb / math.tan(math.radians(phi))       # wie calc_leitung.grundgroessen
        ann.append("R' = X'/tan(phi)")
    else:
        Rb = 0.0
        ann.append("R' = 0 (weder R_Belag noch phi_Ltg)")
        warn = (f"{e.id}: Kein Widerstandsbelag (R_Belag oder phi_Ltg). Mit R' = 0 ist "
                f"Ik min hinter der Leitung zu groß gerechnet.")
    theta = e.p.get("theta_min_C")
    if not (_zahl(theta) and 20 <= theta <= 250):
        theta = KN.theta_Leiter_min_C
    f_warm = 1.0 + KN.alpha_Leiter_1K * (theta - 20.0)
    ann.append(f"Ik min mit {de(theta, 0)} °C (R × {de(f_warm, 2)})")
    zb = S_B_MVA / (UN * UN)
    return (complex(Rb * L, Xb * L) * zb, complex(Rb * L * f_warm, Xb * L) * zb, ann, "", warn)


def _z_motor(e, kn) -> tuple:
    """(z, Annahmen). None, wenn der Anlaufstrom nicht ermittelbar ist."""
    UN = kn[e.von].UN_kV
    try:
        p = dict(e.p)
        p["UN_kV"] = UN
        I_A = calc_motor.grundgroessen(p)["I_Anlauf_prim"]
    except Exception:
        return None, []
    if not (_zahl(I_A) and I_A > 0):
        return None, []
    rx = e.p.get("RX_M")
    ann = []
    if not (_zahl(rx) and rx >= 0):
        rx = KN.RX_M_NS if UN <= KN.U_Grenze_NS_kV else KN.RX_M_HS
        ann.append(f"R/X = {de(rx, 2)} (Tool-Vorgabe)")
    Z_ohm = UN * 1000.0 / (SQRT3 * I_A)
    return _rx_zu_z(Z_ohm, rx) * S_B_MVA / (UN * UN), ann


# ── Netz aufbauen und loesen ─────────────────────────────────────────────────
class _Verbund:
    """Knoten, die ueber Kupplungen (Z = 0) verbunden sind, zaehlen als ein Knoten."""

    def __init__(self, ids):
        self.v = {k: k for k in ids}

    def wurzel(self, k):
        while self.v[k] != k:
            self.v[k] = self.v[self.v[k]]
            k = self.v[k]
        return k

    def verbinde(self, a, b):
        a, b = self.wurzel(a), self.wurzel(b)
        if a != b:
            self.v[max(a, b)] = min(a, b)


def _loese(wurzeln: list, zweige: list, shunts: list) -> dict:
    """
    Kurzschlussimpedanz (bezogen) je Sammelknoten. zweige: (a, b, z), shunts: (a, z).
    Nur die Teilnetze mit Verbindung zur Bezugsebene (Shunt) sind loesbar, alle anderen
    Knoten fehlen im Ergebnis.
    """
    nachbarn = {w: set() for w in wurzeln}
    for a, b, _ in zweige:
        nachbarn[a].add(b)
        nachbarn[b].add(a)
    versorgt, offen = set(), [a for a, _ in shunts]
    while offen:
        k = offen.pop()
        if k in versorgt:
            continue
        versorgt.add(k)
        offen.extend(nachbarn[k] - versorgt)
    ids = sorted(versorgt)
    if not ids:
        return {}
    pos = {k: i for i, k in enumerate(ids)}
    Y = np.zeros((len(ids), len(ids)), dtype=complex)
    for a, b, z in zweige:
        if a in pos and b in pos:
            y = 1.0 / z
            i, j = pos[a], pos[b]
            Y[i, i] += y
            Y[j, j] += y
            Y[i, j] -= y
            Y[j, i] -= y
    for a, z in shunts:
        Y[pos[a], pos[a]] += 1.0 / z
    Z = np.linalg.inv(Y)
    return {k: complex(Z[i, i]) for k, i in pos.items()}


def berechne(netz: Netz, bezeichnung: str = "Aktueller Schaltzustand", art: str = AKTUELL,
             trennstelle: str | None = None) -> KurzschlussErgebnis:
    """Ik max und Ik min je Knoten fuer den Schaltzustand, wie er im Netz steht. Wirft nie."""
    erg = KurzschlussErgebnis(bezeichnung, art, trennstelle)
    try:
        return _berechne(netz, erg)
    except Exception as exc:
        erg.knoten = {}
        erg.meldungen.append(Meldung(
            FEHLER, f"Kurzschlussrechnung abgebrochen ({type(exc).__name__}: {exc})."))
        return erg


def _berechne(netz: Netz, erg: KurzschlussErgebnis) -> KurzschlussErgebnis:
    kn, el = netz.knoten, netz.elemente
    if not kn:
        return erg
    verbund = _Verbund(kn)
    aktiv = [e for _, e in sorted(el.items()) if e.zustand == "ein"]
    for e in aktiv:
        if e.typ == "kupplung":
            verbund.verbinde(e.von, e.nach)

    zweige = {MAX: [], MIN: []}        # (a, b, z)
    quellen = {MAX: [], MIN: []}       # (a, z)
    motoren = []                       # (a, z)
    unvollstaendig = []                # (Element, Text)
    for e in aktiv:
        if e.typ == "einspeisung":
            z_max, z_min, ann, meld = _z_einspeisung(e, kn)
            erg.meldungen += meld
            a = verbund.wurzel(e.nach)
            if z_max is not None:
                quellen[MAX].append((a, z_max))
            if z_min is not None:
                quellen[MIN].append((a, z_min))
            zb = kn[e.nach].UN_kV ** 2 / S_B_MVA
            erg.impedanzen.append(ElementImpedanz(
                e.id, e.typ, kn[e.nach].UN_kV,
                None if z_max is None else z_max * zb,
                None if z_min is None else z_min * zb, tuple(ann)))
        elif e.typ == "generator":
            erg.meldungen.append(Meldung(
                HINWEIS, f"{e.id}: Generatoren werden in der Kurzschlussrechnung noch nicht "
                         f"berücksichtigt. Ik ist ohne ihren Beitrag gerechnet.", (e.id,)))
        elif e.typ in ("trafo", "leitung"):
            if e.typ == "trafo":
                z_max, z_min, ann, fehlt = _z_trafo(e, kn)
                UN, warn = kn[e.nach].UN_kV, ""
            else:
                z_max, z_min, ann, fehlt, warn = _z_leitung(e, kn)
                UN = kn[e.von].UN_kV
            if warn:
                erg.meldungen.append(Meldung(WARNUNG, warn, (e.id,)))
            if fehlt:
                unvollstaendig.append((e, fehlt))
                continue
            a, b = verbund.wurzel(e.von), verbund.wurzel(e.nach)
            if a != b:                               # sonst durch eine Kupplung ueberbrueckt
                if abs(z_max) < 1e-12 or abs(z_min) < 1e-12:
                    unvollstaendig.append((e, "Impedanz ist null"))
                    continue
                zweige[MAX].append((a, b, z_max))
                zweige[MIN].append((a, b, z_min))
            zb = UN * UN / S_B_MVA
            erg.impedanzen.append(ElementImpedanz(e.id, e.typ, UN, z_max * zb, z_min * zb, tuple(ann)))
        elif e.typ == "motor":
            z, ann = _z_motor(e, kn)
            if z is None:
                erg.meldungen.append(Meldung(
                    HINWEIS, f"{e.id}: Anlaufstrom nicht ermittelbar, kein Motorbeitrag.", (e.id,)))
                continue
            motoren.append((verbund.wurzel(e.von), z))
            zb = kn[e.von].UN_kV ** 2 / S_B_MVA
            erg.impedanzen.append(ElementImpedanz(e.id, e.typ, kn[e.von].UN_kV, z * zb, None,
                                                  tuple(ann + ["nur bei Ik max mit Motoren"])))

    wurzeln = sorted({verbund.wurzel(k) for k in kn})
    zk = {
        "max": _loese(wurzeln, zweige[MAX], quellen[MAX]) if quellen[MAX] else {},
        "mot": _loese(wurzeln, zweige[MAX], quellen[MAX] + motoren) if quellen[MAX] else {},
        "min": _loese(wurzeln, zweige[MIN], quellen[MIN]) if quellen[MIN] else {},
    }
    if not any(e.typ == "einspeisung" for e in aktiv):
        erg.meldungen.append(Meldung(
            HINWEIS, "Keine eingeschaltete Netzeinspeisung. Es werden keine Kurzschlussströme "
                     "berechnet."))

    # Elemente ohne Impedanzdaten: Was dahinter liegt, ist nicht berechenbar. Liegt ein
    # solches Element parallel zu einem berechneten Weg, waere jedes Ergebnis falsch.
    versorgt = set(zk["max"]) | set(zk["min"])
    for e, text in unvollstaendig:
        a, b = verbund.wurzel(e.von), verbund.wurzel(e.nach)
        if a in versorgt and b in versorgt:
            erg.meldungen.append(Meldung(
                FEHLER, f"{e.id}: {text}. Das Element liegt parallel zu einem anderen Weg, "
                        f"ohne seine Impedanz ist kein Kurzschlussstrom berechenbar.", (e.id,)))
            zk = {"max": {}, "mot": {}, "min": {}}
            break
        erg.meldungen.append(Meldung(
            WARNUNG, f"{e.id}: {text}. Für die Knoten hinter {e.id} wird kein Ik berechnet.",
            (e.id,)))

    for kid in sorted(kn):
        k, w = kn[kid], verbund.wurzel(kid)
        UN = k.UN_kV
        I_B_kA = S_B_MVA / (SQRT3 * UN)
        zb = UN * UN / S_B_MVA

        def strom(z, fall):
            return None if z is None or abs(z) == 0 else c_faktor(UN, fall) * I_B_kA / abs(z)

        z_max, z_mot, z_min = zk["max"].get(w), zk["mot"].get(w), zk["min"].get(w)
        ik3_min = strom(z_min, MIN)
        erg.knoten[kid] = KnotenIk(
            kid, UN, strom(z_max, MAX), strom(z_mot, MAX),
            None if ik3_min is None else KN.f_2pol * ik3_min,
            None if z_max is None else z_max * zb, None if z_min is None else z_min * zb)
    return erg


# ── Schaltzustaende ──────────────────────────────────────────────────────────
def berechne_schaltzustaende(netz: Netz) -> list:
    """
    Strahlennetz: ein Ergebnis (aktueller Zustand).
    Ring: ein Ergebnis je Trennstellenlage (dieselben Lagen wie netz_ring.erzeuge_lagen,
    die aktuelle zuerst) und eines mit geschlossenem Ring. Der geschlossene Ring ist kein
    Betriebszustand der Staffelung, er liefert den groessten Ik max an den Ringknoten
    (kurzzeitig beim Umschalten ohne Unterbrechung).
    Wirft nie. Kann der Ring nicht zerlegt werden, bleibt es beim aktuellen Zustand.
    """
    try:
        import netz_ring                    # hier, weil netz_ring dieses Modul importiert
        import netz_topologie
        topo = netz_topologie.analysiere(netz)
        if not topo.ok or topo.netzform_erkannt != "ring" or not topo.ring_elemente:
            return [berechne(netz)]
        lagen, _ = netz_ring.erzeuge_lagen(netz)
        if not lagen:
            return [berechne(netz)]
        lagen.sort(key=lambda l: (l.trennstelle != topo.trennstelle, l.trennstelle))
        out = [berechne(l.netz, f"{l.trennstelle} offen", LAGE, l.trennstelle) for l in lagen]
        zu = Netz.from_dict(netz.to_dict())
        for r in topo.ring_elemente:
            zu.element_aendern(r, zustand="ein")
        out.append(berechne(zu, "Ring geschlossen", GESCHLOSSEN))
        return out
    except Exception as exc:
        erg = berechne(netz)
        erg.meldungen.append(Meldung(
            WARNUNG, f"Schaltzustände nicht bestimmbar ({type(exc).__name__}: {exc}). "
                     f"Gerechnet ist nur der aktuelle Zustand."))
        return [erg]


# ── Vergleich mit den eingegebenen Werten ────────────────────────────────────
def vergleiche(netz: Netz, ergebnis: KurzschlussErgebnis) -> list:
    """Je Knoten zwei Zeilen (max, min): eingegeben, berechnet und welcher Wert gilt."""
    out = []
    for kid, k in sorted(netz.knoten.items()):
        r = ergebnis.knoten.get(kid)
        for groesse, ein, ber in ((MAX, k.Ik_max_kA, None if r is None else r.Ik_max_kA),
                                  (MIN, k.Ik_min_kA, None if r is None else r.Ik_min_kA)):
            wirksam = "eingegeben" if ein is not None else ("berechnet" if ber is not None else "fehlt")
            out.append(Vergleich(kid, groesse, ein, ber, wirksam))
    return out


def ergaenze_ik(netz: Netz, ergebnis: KurzschlussErgebnis | None = None) -> tuple:
    """
    Kopie des Netzes, in der Knoten OHNE Handwert den berechneten Ik bekommen.
    Vorhandene Werte bleiben unveraendert, das uebergebene Netz ebenfalls.
    Rueckgabe (Netzkopie, Ergaenzungen, Meldungen). Ein berechneter Wert, der zum Handwert
    der anderen Groesse nicht passt (Ik min ueber Ik max), wird nicht eingesetzt und gemeldet.
    Wirft nie.
    """
    kopie, erg_liste, meld = netz, [], []
    try:
        kopie = Netz.from_dict(netz.to_dict())
        erg = ergebnis if ergebnis is not None else berechne(netz)
        for v in vergleiche(netz, erg):
            if v.wirksam != "berechnet":
                continue
            feld = "Ik_max_kA" if v.groesse == MAX else "Ik_min_kA"
            try:
                kopie.knoten_aendern(v.knoten, **{feld: v.berechnet_kA})
                erg_liste.append(Ergaenzung(v.knoten, v.groesse, v.berechnet_kA))
            except ModellFehler:
                meld.append(Meldung(
                    HINWEIS, f"{v.knoten}: berechneter Ik {v.groesse} "
                             f"({de(v.berechnet_kA, 2)} kA) passt nicht zum eingegebenen Wert "
                             f"der anderen Größe und wird nicht eingesetzt.", (v.knoten,)))
    except Exception as exc:
        meld.append(Meldung(
            WARNUNG, f"Ik-Werte konnten nicht ergänzt werden ({type(exc).__name__}: {exc})."))
    return kopie, erg_liste, meld


def ersetze_ik(netz: Netz, ergebnis: KurzschlussErgebnis | None = None) -> tuple:
    """
    Kopie des Netzes, in der JEDER berechenbare Ik den eingegebenen Wert ersetzt (Ring: je Lage
    der fuer diese Lage berechnete Wert, Entscheidung 17.11.2026, tool_vorgabe_ring.md).
    Rueckfall auf den eingegebenen Wert, wo nichts berechnet werden kann. Ist die Rechnung
    insgesamt fehlerhaft (Ergebnis nicht ok), wird nichts ersetzt. Das uebergebene Netz bleibt
    unveraendert. Rueckgabe (Netzkopie, Ersetzungen, Rueckfaelle, Meldungen):
      Ersetzungen: Liste Ergaenzung (berechneter Wert, der den eingegebenen ersetzt oder fehlt)
      Rueckfaelle: Liste (Knoten, Groesse) mit eingegebenem Wert, der gilt, weil nichts berechnet ist
    Wirft nie.
    """
    kopie, ersetzt, rueckfall, meld = netz, [], [], []
    try:
        kopie = Netz.from_dict(netz.to_dict())
        erg = ergebnis if ergebnis is not None else berechne(netz)
        if not erg.ok:
            meld.append(Meldung(
                WARNUNG, "Die Kurzschlussrechnung ist nicht möglich. Es gelten die eingegebenen "
                         "Werte. " + " ".join(m.text for m in erg.meldungen if m.stufe == FEHLER)[:200]))
            return kopie, ersetzt, [(v.knoten, v.groesse) for v in vergleiche(netz, erg)
                                    if v.eingegeben_kA is not None], meld
        je_knoten: dict = {}
        for v in vergleiche(netz, erg):
            if v.berechnet_kA is None:
                if v.eingegeben_kA is not None:
                    rueckfall.append((v.knoten, v.groesse))
                continue
            feld = "Ik_max_kA" if v.groesse == MAX else "Ik_min_kA"
            je_knoten.setdefault(v.knoten, {})[feld] = v
        for kid, felder in je_knoten.items():
            try:                              # beide Werte eines Knotens zusammen, die Pruefung sieht beide
                kopie.knoten_aendern(kid, **{f: v.berechnet_kA for f, v in felder.items()})
                ersetzt += [Ergaenzung(kid, v.groesse, v.berechnet_kA) for v in felder.values()]
            except ModellFehler:
                for f, v in felder.items():
                    if v.eingegeben_kA is not None:
                        rueckfall.append((kid, v.groesse))
                meld.append(Meldung(
                    HINWEIS, f"{kid}: die berechneten Werte passen nicht zusammen und werden nicht "
                             f"eingesetzt, es gilt der eingegebene Wert.", (kid,)))
    except Exception as exc:
        meld.append(Meldung(
            WARNUNG, f"Ik-Werte konnten nicht ersetzt werden ({type(exc).__name__}: {exc})."))
    return kopie, ersetzt, rueckfall, meld


def polar_text(z: complex | None) -> str:
    """Impedanz als 'R + jX Ω' mit deutschem Komma, '–' ohne Wert."""
    if z is None:
        return "–"
    return f"{de(z.real, 4)} + j{de(z.imag, 4)} Ω"
