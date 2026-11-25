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

  Gegen DIN EN 60909-0:2016-12 geprueft am 25.11.2026 (Fundstellen in
  docs/tool_vorgabe_kurzschluss.md). Danach zwei Aenderungen:
    - Ik max enthaelt die Motoren (7.1.2 e, 7.1.3). Ein Motor mit KS_Beitrag "Nein" (laeuft
      nicht gleichzeitig) faellt heraus. Ik max ohne Motoren bleibt zum Vergleich.
    - Ik min: Leitertemperatur am Ende des Kurzschlusses (7.1.2 Punkt 7, Gl. (32)) aus der
      adiabatischen Erwaermung mit dem Strom am Leitungsende (iterativ), siehe
      _endtemperatur. Ein Handwert theta_min_C hat Vorrang.

  Erdfehler (einpolig, Entscheidung 25.11.2026, docs/tool_vorgabe_erdfehler.md):
    Ik1 = 3 * c * UN / sqrt(3) / |2 * Z1 + Z0|  (Z2 = Z1), Z0 aus einer eigenen Nullsystem-
    Matrix. Nur in geerdeten Bereichen (Knoten "direkt" oder "niederohmig" mit
    Erdfehlerstrom-Begrenzung I_E_begr_A), sonst kein Wert. Ik1 max mit c_max, Sk_max, K_T,
    Ik1 min mit c_min, Sk_min, warmem Leiter, ohne K_T. Motoren ohne Beitrag.
    Nullsystem je Element:
      Einspeisung (Knoten direkt)   Z0 = X0_X1_Q * Z1Q
      Trafo, Stern mit N gegen D    Querzweig Z0T = Z0_Z1_Trafo * Z1T (+ 3 R_E) am Sternknoten
      Trafo YNyn                    Laengszweig Z0T (+ 3 R_E je Seite)
      Trafo ohne N oder Yyn         kein Nullsystem (D sperrt, Yyn mit Hinweis)
      Leitung                       Z0 = (R0' + jX0') * L, sonst aus RE/RL und XE/XL
      Knoten niederohmig ohne Trafo Querzweig 3 R_E (Sternpunktbildner)
  erdstrom_verteilung(netz, knoten) -> 3I0 durch jedes Element und jeden Erdungspunkt.

Nicht berechnet: Generatoren, Erdschluss in isolierten oder kompensierten Netzen, Stoss-,
Ausschalt- und thermischer Strom. Der Stufensteller wirkt nicht auf die Impedanz, er geht wie bisher in
netz_umrechnung.py als Faktor auf den Strom ein.

Robustheit: Das Modul wirft nie. Fehlen Daten, gibt es Meldungen und fuer die betroffenen
Knoten keinen Wert (None) statt eines geschaetzten.
"""

from __future__ import annotations

import cmath
import math
import re
from dataclasses import dataclass, field

import numpy as np

import calc_motor
import konstanten_leitung
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
    # Ab 25.11.2026 (DIN EN 60909-0:2016-12, 7.1.2 e): Ik max MIT den Motoren, die gleichzeitig
    # laufen. Ik_max_mit_Motor_kA bleibt als gleichwertiger Name fuer aeltere Aufrufer.
    Ik_max_kA: float | None = None            # dreipolig, groesster (mit Motoren)
    Ik_max_mit_Motor_kA: float | None = None  # = Ik_max_kA
    Ik_min_kA: float | None = None            # zweipolig, kleinster
    Zk_max_Ohm: complex | None = None         # Kurzschlussimpedanz am Knoten (mit Motoren)
    Zk_min_Ohm: complex | None = None
    Ik1_max_kA: float | None = None           # einpolig (Erdkurzschluss), groesster
    Ik1_min_kA: float | None = None           # einpolig, kleinster
    Z0_max_Ohm: complex | None = None         # Nullimpedanz am Knoten
    erdung: str = ""                          # Kurztext: wie der Bereich geerdet ist
    Ik_max_ohne_Motor_kA: float | None = None # dreipolig, nur Netz (Vergleich, Gegenrechnung)

    @property
    def Ik_Motor_kA(self) -> float | None:
        """Zuwachs durch die Motoren (Betragsdifferenz), None wenn nicht ermittelbar."""
        if self.Ik_max_kA is None or self.Ik_max_ohne_Motor_kA is None:
            return None
        return max(self.Ik_max_kA - self.Ik_max_ohne_Motor_kA, 0.0)


@dataclass
class KurzschlussErgebnis:
    bezeichnung: str = "Aktueller Schaltzustand"
    art: str = AKTUELL                          # AKTUELL, LAGE oder GESCHLOSSEN
    trennstelle: str | None = None              # nur bei art == LAGE
    knoten: dict = field(default_factory=dict)  # Knoten-ID -> KnotenIk
    impedanzen: list = field(default_factory=list)
    impedanzen0: list = field(default_factory=list)  # Nullimpedanzen (Leitungen, Erdungspunkte)
    meldungen: list = field(default_factory=list)
    # Aufgebautes Nullsystem fuer erdstrom_verteilung (intern, nicht fuer die Anzeige)
    null: dict | None = field(default=None, repr=False, compare=False)
    theta_e: dict = field(default_factory=dict)    # Leitung -> Endtemperatur bei Ik min [Grad C]

    @property
    def ok(self) -> bool:
        return not any(m.stufe == FEHLER for m in self.meldungen)


@dataclass(frozen=True)
class ErdstromVerteilung:
    """
    Erdstrom 3I0 bei einem einpoligen Fehler am Knoten fehlerknoten.
    zweige: Element-ID -> (3I0 in kA, Knoten, von dem der Strom in das Element hinein zum
            Fehler fliesst). Nur Elemente mit Nullsystem-Laengszweig (Leitung, Trafo YNyn).
    erdungen: Erdungspunkt -> 3I0 in kA. Schluessel ist die Trafo-ID (Strom im Sternpunkt),
            "Netz:<Einspeisung>" oder "Erdung:<Knoten>" (Sternpunktbildner).
    """
    fehlerknoten: str
    fall: str
    Ik1_kA: float | None
    zweige: dict = field(default_factory=dict)
    erdungen: dict = field(default_factory=dict)


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
    if ns:
        c_max, c_min = KN.C_NS.get(KN.NS_Toleranz_pct, (KN.c_max_NS, KN.c_min_NS))
        return c_max if fall == MAX else c_min
    return KN.c_max_HS if fall == MAX else KN.c_min_HS


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
    # Bemessungsspannungen (optional): Impedanz auf UrUS bezogen, Abweichung der Bemessungs-
    # uebersetzung t_r von UN_OS/UN_US als Uebersetzung tau im Ersatzschaltbild (Norm 6.2, Gl. 6:
    # Netzimpedanz mit 1/t_r^2 auf die US-Seite).
    UrOS, UrUS = e.p.get("UrT_OS_kV"), e.p.get("UrT_US_kV")
    f_US = 1.0
    if _zahl(UrUS) and UrUS > 0:
        f_US = (UrUS / kn[e.nach].UN_kV) ** 2
        ann.append(f"bezogen auf UrUS = {de(UrUS * 1000, 0)} V")
    z = complex(ukr, math.sqrt(uk * uk - ukr * ukr)) * S_B_MVA / Sn * f_US
    return z * kt, (z * kt if KN.KT_bei_min else z), ann, ""


def uebersetzung(e, kn) -> float:
    """tau = (UrOS/UrUS) / (UN_OS/UN_US); 1,0 ohne Bemessungsspannungen."""
    UrOS, UrUS = e.p.get("UrT_OS_kV"), e.p.get("UrT_US_kV")
    if not (_zahl(UrOS) and UrOS > 0 and _zahl(UrUS) and UrUS > 0):
        return 1.0
    return (UrOS / UrUS) / (kn[e.von].UN_kV / kn[e.nach].UN_kV)


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
    theta = theta_fest(e)
    if theta is None:
        theta = KN.theta_Leiter_min_C            # Startwert, die Rechnung ersetzt ihn
    f_warm = 1.0 + KN.alpha_Leiter_1K * (theta - 20.0)
    zb = S_B_MVA / (UN * UN)
    return (complex(Rb * L, Xb * L) * zb, complex(Rb * L * f_warm, Xb * L) * zb, ann, "", warn)


def theta_fest(e) -> float | None:
    """Von Hand vorgegebene Leitertemperatur fuer Ik min (Vorrang vor der Rechnung)."""
    theta = e.p.get("theta_min_C")
    return float(theta) if _zahl(theta) and 20 <= theta <= KN.theta_KS_max_C else None


def leiterdaten(e) -> tuple:
    """(Material, Querschnitt mm^2, Herkunft) der Leitung. Querschnitt None, wenn unbekannt."""
    mat = e.p.get("Leitermaterial")
    mat = mat if mat in KN.LEITER else KN.Leitermaterial_def
    A = e.p.get("A_mm2")
    if _zahl(A) and A > 0:
        return mat, float(A), "eingegeben"
    Xb = e.p.get("X_Belag")
    Rb = e.p.get("R_Belag")
    phi = e.p.get("phi_Ltg")
    if not (_zahl(Rb) and Rb > 0) and _zahl(Xb) and Xb > 0 and _zahl(phi) and 0 < phi < 90:
        Rb = Xb / math.tan(math.radians(phi))
    if _zahl(Rb) and Rb > 0:
        return mat, KN.LEITER[mat]["rho"] * 1000.0 / Rb, "aus R′"
    return mat, None, ""


def _endtemperatur(theta_i, I_kA, t_s, A_mm2, mat) -> float:
    """Adiabatische Erwaermung (IEC 60949): theta_e = (theta_i + beta)*exp(I^2 t/(K^2 S^2)) - beta."""
    d = KN.LEITER[mat]
    I = I_kA * 1000.0
    x = I * I * t_s / (d["K"] ** 2 * A_mm2 ** 2)
    return (theta_i + d["beta"]) * math.exp(min(x, 50.0)) - d["beta"]


def motor_im_kurzschluss(e) -> bool:
    """Beitrag zu Ik max (Nein: laeuft nach Art der Schaltung nicht gleichzeitig, 7.1.3)."""
    return e.p.get("KS_Beitrag", KN.KS_BEITRAG_OPTIONEN[0]) != KN.KS_BEITRAG_OPTIONEN[1]


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


# ── Nullsystem (Erdfehler) ───────────────────────────────────────────────────
_SG_MUSTER = re.compile(r"(YN|Y|D|ZN|Z)(yn|y|d|zn|z)(\d{1,2})")


def wicklungen(schaltgruppe) -> tuple | None:
    """'Dyn5' -> ('D', 'yn'). None, wenn die Schaltgruppe nicht lesbar ist."""
    if not isinstance(schaltgruppe, str):
        return None
    m = _SG_MUSTER.fullmatch(schaltgruppe.strip())
    return (m.group(1), m.group(2)) if m else None


def geerdet(knoten) -> bool:
    """Sternpunktbehandlung mit Erdfehlerstrom (starr oder niederohmig geerdet)."""
    return knoten.sternpunkt in ("direkt", "niederohmig")


def R_E_Ohm(knoten) -> float | None:
    """Erdungswiderstand aus der Begrenzung: R_E = UN / (sqrt(3) * I_E). Nur bei niederohmig."""
    I_E = knoten.I_E_begr_A
    if knoten.sternpunkt != "niederohmig" or not _zahl(I_E):
        return None
    lo, hi = KN.I_E_begr_Bereich_A
    if not (lo <= I_E <= hi):
        return None
    return knoten.UN_kV * 1000.0 / (SQRT3 * I_E)


def _sternseite(e) -> list:
    """Knoten-IDs, an denen der Trafo e einen herausgefuehrten Sternpunkt (N) hat."""
    wk = wicklungen(e.p.get("Schaltgruppe"))
    if wk is None:
        return []
    return ([e.von] if wk[0] in ("YN", "ZN") else []) + ([e.nach] if wk[1] in ("yn", "zn") else [])


def _erster_sterntrafo(kid, aktiv) -> str | None:
    """Erster eingeschalteter Trafo (nach ID) mit herausgefuehrtem Sternpunkt am Knoten."""
    for e in aktiv:
        if e.typ == "trafo" and kid in _sternseite(e):
            return e.id
    return None


def erdung_am_trafo(netz: Netz, trafo_id: str) -> str | None:
    """
    Knoten, an dem der Sternpunkt des Trafos geerdet ist (dort sitzt ein Sternpunktwandler),
    None, wenn kein Sternpunkt geerdet ist. Gleiche Regel wie in der Kurzschlussrechnung:
    am starr geerdeten Knoten jeder Sternpunkt, am niederohmigen Knoten mit Begrenzung nur der
    erste Trafo mit Sternpunkt (ein Erdungspunkt je Knoten). Bei YNyn zaehlt die US-Seite zuerst.
    """
    e = netz.elemente.get(trafo_id)
    if e is None or e.typ != "trafo" or e.zustand != "ein":
        return None
    aktiv = [x for _, x in sorted(netz.elemente.items()) if x.zustand == "ein"]
    for kid in sorted(_sternseite(e), key=lambda k: k != e.nach):
        k = netz.knoten[kid]
        if k.sternpunkt == "direkt":
            return kid
        if (k.sternpunkt == "niederohmig" and R_E_Ohm(k) is not None
                and _erster_sterntrafo(kid, aktiv) == trafo_id):
            return kid
    return None


def _z0_leitung(e, kn, theta=None) -> tuple:
    """
    (z0_max, z0_min, Annahmen, Fehlertext) bezogen. Ik1 min mit warmem Leiter (auch R0), mit
    derselben Endtemperatur wie im Mitsystem (theta aus _loese_min).
    """
    L, Xb = _pos(e.p, "L_km"), _pos(e.p, "X_Belag")
    if L is None or Xb is None:
        return None, None, [], "L_km oder X_Belag fehlt"
    UN = kn[e.von].UN_kV
    ann = []
    Rb = e.p.get("R_Belag")
    phi = e.p.get("phi_Ltg")
    if _zahl(Rb) and Rb >= 0:
        Rb = float(Rb)
    elif _zahl(phi) and 0 < phi < 90:
        Rb = Xb / math.tan(math.radians(phi))
    else:
        Rb = 0.0
    R0, X0 = e.p.get("R0_Belag"), e.p.get("X0_Belag")
    if not (_zahl(R0) and R0 >= 0):
        kR = e.p.get("RE_RL")
        if not (_zahl(kR) and kR >= 0):
            kR = konstanten_leitung.RE_RL_def
        R0 = Rb * (1.0 + 3.0 * kR)
        ann.append(f"R0' = R1' · (1 + 3 · {de(kR, 2)}) aus RE/RL")
    if not (_zahl(X0) and X0 > 0):
        kX = e.p.get("XE_XL")
        if not (_zahl(kX) and kX >= 0):
            kX = konstanten_leitung.XE_XL_def
        X0 = Xb * (1.0 + 3.0 * kX)
        ann.append(f"X0' = X1' · (1 + 3 · {de(kX, 2)}) aus XE/XL")
    if theta is None:
        theta = theta_fest(e) or KN.theta_Leiter_min_C
    f_warm = 1.0 + KN.alpha_Leiter_1K * (theta - 20.0)
    zb = S_B_MVA / (UN * UN)
    return (complex(R0 * L, X0 * L) * zb, complex(R0 * L * f_warm, X0 * L) * zb, ann, "")


def _nullsystem(kn, verbund, aktiv, z1, erg, theta_e=None) -> dict:
    """
    Nullsystem aufbauen. z1: Element-ID -> (z_max, z_min) des Mitsystems (Einspeisung, Trafo).
    Rueckgabe dict mit zweige {fall: [(a, b, z, eid, von, nach)]},
    erden {fall: [(a, z, quelle, knoten)]},
    texte {Wurzel: [Text je Erdungspunkt]}, ungueltig (bool: Ik1 nicht berechenbar).
    Meldungen gehen nach erg.meldungen, nie als FEHLER: das Nullsystem darf die
    Phasenrechnung nicht blockieren.
    """
    zweige = {MAX: [], MIN: []}
    erden = {MAX: [], MIN: []}
    texte: dict = {}
    w = verbund.wurzel

    def erde(knoten_id, z_max, z_min, quelle, text):
        a = w(knoten_id)
        zb = kn[knoten_id].UN_kV ** 2 / S_B_MVA
        erg.impedanzen0.append(ElementImpedanz(
            quelle, "erdung", kn[knoten_id].UN_kV, None if z_max is None else z_max * zb,
            None if z_min is None else z_min * zb, (text,)))
        for fall, z in ((MAX, z_max), (MIN, z_min)):
            if z is not None and abs(z) > 1e-12:
                erden[fall].append((a, z, quelle, knoten_id))
        texte.setdefault(a, []).append(text)

    # Erdungswiderstand je niederohmigem Knoten: an den ersten Trafo mit Sternpunkt dort,
    # sonst Sternpunktbildner. Ein Erdungspunkt je Knoten (Tool-Vorgabe).
    re_bei = {}                  # Knoten-ID -> Trafo-ID, der den Widerstand traegt
    for kid, k in sorted(kn.items()):
        if k.I_E_begr_A is not None and k.sternpunkt != "niederohmig":
            erg.meldungen.append(Meldung(
                HINWEIS, f"{kid}: Erdfehlerstrom-Begrenzung ist eingetragen, der Knoten ist aber "
                         f"nicht niederohmig geerdet. Der Wert wird ignoriert.", (kid,)))
            continue
        if k.sternpunkt != "niederohmig" or k.I_E_begr_A is None:
            continue
        if R_E_Ohm(k) is None:
            lo, hi = KN.I_E_begr_Bereich_A
            erg.meldungen.append(Meldung(
                WARNUNG, f"{kid}: Erdfehlerstrom-Begrenzung {de(k.I_E_begr_A, 0)} A liegt "
                         f"außerhalb von {de(lo, 0)} bis {de(hi, 0)} A. Keine Erdung angesetzt.",
                (kid,)))
            continue
        t = _erster_sterntrafo(kid, aktiv)
        if t is not None:
            re_bei[kid] = t

    def z_RE(kid):
        R = R_E_Ohm(kn[kid])
        return 0.0 if R is None else 3.0 * R * S_B_MVA / kn[kid].UN_kV ** 2

    for e in aktiv:
        if e.typ == "einspeisung":
            k = kn[e.nach]
            if k.sternpunkt != "direkt" or e.id not in z1:
                continue
            zq_max, zq_min, _ = z1[e.id]
            r = e.p.get("X0_X1_Q")
            ann = ""
            if not (_zahl(r) and r > 0):
                r = KN.X0_X1_Q_def
                ann = " (Tool-Vorgabe)"
            if zq_max is None and zq_min is None:
                continue
            erde(e.nach, None if zq_max is None else zq_max * r,
                 None if zq_min is None else zq_min * r, f"Netz:{e.id}",
                 f"Netz {e.id} starr geerdet, X0/X1 = {de(r, 2)}{ann}")
        elif e.typ == "trafo":
            if e.id not in z1 or z1[e.id][0] is None:
                if geerdet(kn[e.von]) or geerdet(kn[e.nach]):
                    erg.meldungen.append(Meldung(
                        WARNUNG, f"{e.id}: ohne Sn/uk kein Nullsystem. Ik1 im angrenzenden "
                                 f"geerdeten Bereich ist unsicher.", (e.id,)))
                continue
            sg = e.p.get("Schaltgruppe")
            wk = wicklungen(sg)
            if wk is None:
                if geerdet(kn[e.von]) or geerdet(kn[e.nach]):
                    erg.meldungen.append(Meldung(
                        WARNUNG, f"{e.id}: Schaltgruppe {sg!r} ist nicht lesbar. Das Nullsystem "
                                 f"des Trafos ist nicht abgebildet.", (e.id,)))
                continue
            z_a, z_b, tau = z1[e.id]
            r0 = e.p.get("R0_R_T")
            x0 = e.p.get("X0_X_T")
            r0 = float(r0) if _zahl(r0) and r0 >= 0 else KN.Z0_Z1_Trafo
            x0 = float(x0) if _zahl(x0) and x0 > 0 else KN.Z0_Z1_Trafo
            zt_max, zt_min = (complex(z.real * r0, z.imag * x0) for z in (z_a, z_b))
            os_n, us_n = wk[0] in ("YN", "ZN"), wk[1] in ("yn", "zn")
            os_d, us_d = wk[0] == "D", wk[1] == "d"

            def sternseite(kid):
                """(Zusatz 3 R_E bezogen, Text) oder None, wenn der Sternpunkt nicht geerdet ist."""
                k = kn[kid]
                if k.sternpunkt == "direkt":
                    return 0.0, "starr"
                if k.sternpunkt == "niederohmig" and re_bei.get(kid) == e.id:
                    return z_RE(kid), f"über R_E, I_E = {de(k.I_E_begr_A, 0)} A"
                return None

            if os_n and us_n:
                a, b = sternseite(e.von), sternseite(e.nach)
                if a is not None and b is not None:
                    zus = a[0] + b[0]
                    zweige[MAX].append((w(e.von), w(e.nach), zt_max + zus, e.id, e.von, e.nach))
                    zweige[MIN].append((w(e.von), w(e.nach), zt_min + zus, e.id, e.von, e.nach))
            elif (os_n and us_d) or (us_n and os_d):
                kid = e.von if os_n else e.nach
                st = sternseite(kid)
                f_os = tau * tau if os_n else 1.0      # Impedanz ist auf die US-Seite bezogen
                if st is not None:
                    erde(kid, zt_max * f_os + st[0], zt_min * f_os + st[0], e.id,
                         f"Sternpunkt {e.id} ({sg}) {st[1]}")
            elif os_n or us_n:
                kid = e.von if os_n else e.nach
                if geerdet(kn[kid]):
                    erg.meldungen.append(Meldung(
                        WARNUNG, f"{e.id}: Schaltgruppe {sg} ohne Dreieckwicklung. Die "
                                 f"Nullimpedanz hängt von der Kernbauart ab und ist nicht "
                                 f"abgebildet, der Sternpunkt zählt nicht als Erdung.", (e.id,)))
        elif e.typ == "leitung":
            z0_max, z0_min, ann, fehlt = _z0_leitung(e, kn, (theta_e or {}).get(e.id))
            a, b = w(e.von), w(e.nach)
            if fehlt or a == b:
                continue
            if abs(z0_max) < 1e-12 or abs(z0_min) < 1e-12:
                continue
            zweige[MAX].append((a, b, z0_max, e.id, e.von, e.nach))
            zweige[MIN].append((a, b, z0_min, e.id, e.von, e.nach))
            zb = kn[e.von].UN_kV ** 2 / S_B_MVA
            erg.impedanzen0.append(ElementImpedanz(
                e.id, e.typ, kn[e.von].UN_kV, z0_max * zb, z0_min * zb, tuple(ann)))

    # Sternpunktbildner: niederohmige Knoten mit Begrenzung, aber ohne Trafo-Sternpunkt
    for kid, k in sorted(kn.items()):
        if k.sternpunkt == "niederohmig" and R_E_Ohm(k) is not None and kid not in re_bei:
            z = complex(z_RE(kid), 0.0)
            erde(kid, z, z, f"Erdung:{kid}",
                 f"Sternpunktbildner an {kid}, I_E = {de(k.I_E_begr_A, 0)} A")
    return {"zweige": zweige, "erden": erden, "texte": texte}


def _bereiche(kn, verbund, aktiv) -> dict:
    """Wurzel -> Bereichsnummer: Knoten, die galvanisch ueber Leitungen/Kupplungen verbunden sind."""
    v = _Verbund({verbund.wurzel(k) for k in kn})
    for e in aktiv:
        if e.typ == "leitung":
            v.verbinde(verbund.wurzel(e.von), verbund.wurzel(e.nach))
    return {r: v.wurzel(r) for r in v.v}


def _loese_voll(zweige: list, shunts: list) -> tuple:
    """Wie _loese, aber mit der ganzen Impedanzmatrix: (pos, Z). zweige (a, b, z, ...)."""
    nachbarn: dict = {}
    for a, b, *_ in zweige:
        nachbarn.setdefault(a, set()).add(b)
        nachbarn.setdefault(b, set()).add(a)
    versorgt, offen = set(), [s[0] for s in shunts]
    while offen:
        k = offen.pop()
        if k in versorgt:
            continue
        versorgt.add(k)
        offen.extend(nachbarn.get(k, set()) - versorgt)
    ids = sorted(versorgt)
    if not ids:
        return {}, None
    pos = {k: i for i, k in enumerate(ids)}
    Y = np.zeros((len(ids), len(ids)), dtype=complex)
    for t in zweige:
        _zweig_in_Y(Y, pos, t)
    for a, z, *_ in shunts:
        Y[pos[a], pos[a]] += 1.0 / z
    return pos, np.linalg.inv(Y)


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
    for a, b, *_ in zweige:
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
    for t in zweige:
        _zweig_in_Y(Y, pos, t)
    for a, z in shunts:
        Y[pos[a], pos[a]] += 1.0 / z
    Z = np.linalg.inv(Y)
    return {k: complex(Z[i, i]) for k, i in pos.items()}


def _zweig_in_Y(Y, pos, t) -> None:
    """
    Zweig (a, b, z) oder (a, b, z, tau) in die Admittanzmatrix. tau: Uebersetzung eines idealen
    Trafos auf der Seite a (Abweichung der Bemessungsuebersetzung von UN_a/UN_b), z auf b bezogen:
    Y_aa += y/tau^2, Y_bb += y, Y_ab = Y_ba -= y/tau. Ohne tau (oder Nullsystem-Tupel) gilt 1.
    """
    a, b, z = t[0], t[1], t[2]
    tau = t[3] if len(t) == 4 and isinstance(t[3], float) else 1.0
    if a not in pos or b not in pos:
        return
    y = 1.0 / z
    i, j = pos[a], pos[b]
    Y[i, i] += y / (tau * tau)
    Y[j, j] += y
    Y[i, j] -= y / tau
    Y[j, i] -= y / tau


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


def _loese_min(kn, wurzeln, zweige_min, quellen_min, leitungen, erg) -> tuple:
    """
    Ik min mit der Leitertemperatur am Ende des Kurzschlusses (Gl. (32)). Je Leitung:
    Handwert theta_min_C, sonst adiabatisch aus dem zweipoligen Strom im Zweig bei einem Fehler
    an einem seiner Enden (der groessere von beiden, im Strahlennetz der Fehler am fernen Ende),
    Kurzschlussdauer t_KS_s und Querschnitt. Strom und Widerstand haengen
    voneinander ab, daher Fixpunkt-Iteration ab der Anfangstemperatur. Die Temperatur steigt
    monoton, der Strom faellt, die Iteration konvergiert.
    Rueckgabe ({Wurzel: z}, {Element-ID: theta_e}). Schreibt die Annahmen in erg.impedanzen.
    """
    if not quellen_min:
        return {}, {}
    daten = {}
    for e, a, b, z_max, idx in leitungen:
        fest = theta_fest(e)
        mat, A, herkunft = leiterdaten(e)
        t = e.p.get("t_KS_s")
        t = float(t) if _zahl(t) and t > 0 else KN.t_KS_Ikmin_s
        daten[e.id] = (e, a, b, z_max, idx, fest, mat, A, herkunft, t)

    def z_leitung(e, z_max, theta):
        """Mitimpedanz bei theta: nur der Wirkanteil waechst (z_max ist bei 20 Grad C)."""
        f = 1.0 + KN.alpha_Leiter_1K * (theta - 20.0)
        return complex(z_max.real * f, z_max.imag)

    theta = {eid: (d[5] if d[5] is not None else KN.theta_Leiter_min_C) for eid, d in daten.items()}
    zk = {}
    for _ in range(KN.theta_Iter_max):
        zw = list(zweige_min) + [(d[1], d[2], z_leitung(d[0], d[3], theta[eid]), 1.0)
                                 for eid, d in daten.items()]
        pos, Z = _loese_voll(zw, quellen_min)
        neu = dict(theta)
        for eid, (e, a, b, z_max, idx, fest, mat, A, herkunft, t) in daten.items():
            if fest is not None or A is None or Z is None or a not in pos or b not in pos:
                continue
            # Strom im Zweig bei einem Fehler an einem der beiden Enden (Ueberlagerung,
            # Ersatzspannungsquelle c am Fehlerort): i_ab = (Z_bf - Z_af) * I_f / z_ab
            UN = kn[e.von].UN_kV
            c = c_faktor(UN, MIN)
            z_l = z_leitung(e, z_max, theta[eid])
            i = 0.0
            for f in (a, b):
                I_f = c / Z[pos[f], pos[f]]
                i = max(i, abs((Z[pos[b], pos[f]] - Z[pos[a], pos[f]]) * I_f / z_l))
            ik2 = KN.f_2pol * i * S_B_MVA / (SQRT3 * UN)        # zweipolig, kA
            neu[eid] = min(_endtemperatur(KN.theta_Leiter_min_C, ik2, t, A, mat),
                           KN.theta_KS_max_C + 1e-9)
        fertig = all(abs(neu[k] - theta[k]) < KN.theta_Iter_tol_K for k in theta)
        theta = neu
        if fertig:
            break
    # endgueltig mit den letzten Temperaturen loesen und Annahmen eintragen
    zw = list(zweige_min) + [(d[1], d[2], z_leitung(d[0], d[3], theta[eid]), 1.0) for eid, d in daten.items()]
    zk = _loese(wurzeln, zw, quellen_min)
    for eid, (e, a, b, z_max, idx, fest, mat, A, herkunft, t) in daten.items():
        imp = erg.impedanzen[idx]
        th = theta[eid]
        zb = imp.UN_kV ** 2 / S_B_MVA
        f = 1.0 + KN.alpha_Leiter_1K * (th - 20.0)
        if fest is not None:
            text = f"Ik min mit {de(th, 0)} °C (Handwert, R × {de(f, 2)})"
        elif A is None:
            text = (f"Ik min mit {de(th, 0)} °C (Anfangstemperatur, Querschnitt unbekannt, "
                    f"R × {de(f, 2)})")
            erg.meldungen.append(Meldung(
                HINWEIS, f"{eid}: Ohne Querschnitt und ohne R′ keine Erwärmung im Kurzschluss. "
                         f"Ik min gilt mit {de(th, 0)} °C und ist eher zu groß.", (eid,)))
        else:
            text = (f"Ik min mit θe = {de(th, 0)} °C (adiabatisch ab "
                    f"{de(KN.theta_Leiter_min_C, 0)} °C, t = {de(t, 2)} s, {de(A, 0)} mm² {mat} "
                    f"{herkunft}, R × {de(f, 2)})")
            if th >= KN.theta_KS_max_C:
                erg.meldungen.append(Meldung(
                    WARNUNG, f"{eid}: Die Leitertemperatur erreicht im Kurzschluss "
                             f"{de(KN.theta_KS_max_C, 0)} °C (Grenze VPE). Die Leitung ist bei "
                             f"Ik min und t = {de(t, 2)} s thermisch überlastet. Gerechnet ist mit "
                             f"{de(KN.theta_KS_max_C, 0)} °C.", (eid,)))
        erg.impedanzen[idx] = ElementImpedanz(
            imp.element, imp.typ, imp.UN_kV, imp.Z_max, z_leitung(e, z_max, th) * zb,
            imp.annahmen + (text,))
    erg.theta_e = theta
    return zk, theta


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
    z1 = {}                            # Element-ID -> (z_max, z_min) fuer das Nullsystem
    leitungen = []                     # (Element, a, b, z_max, Index in erg.impedanzen)
    for e in aktiv:
        if e.typ == "einspeisung":
            z_max, z_min, ann, meld = _z_einspeisung(e, kn)
            z1[e.id] = (z_max, z_min, 1.0)
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
            if e.typ == "trafo":
                z1[e.id] = (z_max, z_min, uebersetzung(e, kn))
            a, b = verbund.wurzel(e.von), verbund.wurzel(e.nach)
            if a != b:                               # sonst durch eine Kupplung ueberbrueckt
                if abs(z_max) < 1e-12 or abs(z_min) < 1e-12:
                    unvollstaendig.append((e, "Impedanz ist null"))
                    continue
                tau = uebersetzung(e, kn) if e.typ == "trafo" else 1.0
                zweige[MAX].append((a, b, z_max, tau))
                if e.typ == "leitung":
                    leitungen.append((e, a, b, z_max, len(erg.impedanzen)))
                else:
                    zweige[MIN].append((a, b, z_min, tau))
            zb = UN * UN / S_B_MVA
            erg.impedanzen.append(ElementImpedanz(e.id, e.typ, UN, z_max * zb, z_min * zb, tuple(ann)))
        elif e.typ == "motor":
            if not motor_im_kurzschluss(e):
                erg.meldungen.append(Meldung(
                    HINWEIS, f"{e.id}: läuft nicht gleichzeitig (Verriegelung), kein Beitrag zu "
                             f"Ik max.", (e.id,)))
                continue
            z, ann = _z_motor(e, kn)
            if z is None:
                erg.meldungen.append(Meldung(
                    HINWEIS, f"{e.id}: Anlaufstrom nicht ermittelbar, kein Motorbeitrag.", (e.id,)))
                continue
            motoren.append((verbund.wurzel(e.von), z))
            zb = kn[e.von].UN_kV ** 2 / S_B_MVA
            erg.impedanzen.append(ElementImpedanz(e.id, e.typ, kn[e.von].UN_kV, z * zb, None,
                                                  tuple(ann + ["nur bei Ik max"])))

    wurzeln = sorted({verbund.wurzel(k) for k in kn})
    zk_min, theta_e = _loese_min(kn, wurzeln, zweige[MIN], quellen[MIN], leitungen, erg)
    zk = {
        "netz": _loese(wurzeln, zweige[MAX], quellen[MAX]) if quellen[MAX] else {},
        "max": _loese(wurzeln, zweige[MAX], quellen[MAX] + motoren) if quellen[MAX] else {},
        "min": zk_min,
    }
    if not any(e.typ == "einspeisung" for e in aktiv):
        erg.meldungen.append(Meldung(
            HINWEIS, "Keine eingeschaltete Netzeinspeisung. Es werden keine Kurzschlussströme "
                     "berechnet."))

    # Elemente ohne Impedanzdaten: Was dahinter liegt, ist nicht berechenbar. Liegt ein
    # solches Element parallel zu einem berechneten Weg, waere jedes Ergebnis falsch.
    versorgt = set(zk["netz"]) | set(zk["min"])     # nur ueber das Netz, ein Motor allein speist nicht
    for e, text in unvollstaendig:
        a, b = verbund.wurzel(e.von), verbund.wurzel(e.nach)
        if a in versorgt and b in versorgt:
            erg.meldungen.append(Meldung(
                FEHLER, f"{e.id}: {text}. Das Element liegt parallel zu einem anderen Weg, "
                        f"ohne seine Impedanz ist kein Kurzschlussstrom berechenbar.", (e.id,)))
            zk = {"netz": {}, "max": {}, "min": {}}
            break
        erg.meldungen.append(Meldung(
            WARNUNG, f"{e.id}: {text}. Für die Knoten hinter {e.id} wird kein Ik berechnet.",
            (e.id,)))

    # Nullsystem (Erdfehler). Fehler hier duerfen die Phasenrechnung nie beeintraechtigen.
    z0k = {MAX: {}, MIN: {}}
    null = None
    try:
        null = _nullsystem(kn, verbund, aktiv, z1, erg, theta_e)
        for fall in (MAX, MIN):
            pos, Z = _loese_voll(null["zweige"][fall], null["erden"][fall])
            if Z is not None:
                z0k[fall] = {k: complex(Z[i, i]) for k, i in pos.items()}
            null[fall] = (pos, Z)
        null["bereich"] = _bereiche(kn, verbund, aktiv)
        null["verbund"] = verbund
        erg.null = null
    except Exception as exc:
        z0k = {MAX: {}, MIN: {}}
        erg.meldungen.append(Meldung(
            WARNUNG, f"Erdfehlerrechnung (Nullsystem) abgebrochen ({type(exc).__name__}: {exc}). "
                     f"Die Phasenwerte sind davon nicht betroffen."))

    for kid in sorted(kn):
        k, w = kn[kid], verbund.wurzel(kid)
        UN = k.UN_kV
        I_B_kA = S_B_MVA / (SQRT3 * UN)
        zb = UN * UN / S_B_MVA

        def strom(z, fall):
            return None if z is None or abs(z) == 0 else c_faktor(UN, fall) * I_B_kA / abs(z)

        def strom1(z1k, z0, fall):
            if z1k is None or z0 is None:
                return None
            n = abs(2.0 * z1k + z0)
            return None if n == 0 else 3.0 * c_faktor(UN, fall) * I_B_kA / n

        z_netz, z_max, z_min = zk["netz"].get(w), zk["max"].get(w), zk["min"].get(w)
        if z_netz is None:                  # ohne Netzanbindung laeuft kein Motor
            z_max = None
        z0_max, z0_min = z0k[MAX].get(w), z0k[MIN].get(w)
        ik3_min = strom(z_min, MIN)
        ik_max = strom(z_max, MAX)
        erg.knoten[kid] = KnotenIk(
            kid, UN, ik_max, ik_max,
            None if ik3_min is None else KN.f_2pol * ik3_min,
            None if z_max is None else z_max * zb, None if z_min is None else z_min * zb,
            strom1(z_max, z0_max, MAX), strom1(z_min, z0_min, MIN),
            None if z0_max is None else z0_max * zb, _erdungstext(kid, k, w, null),
            strom(z_netz, MAX))
    _meldungen_erdung(kn, verbund, null, erg)
    return erg


_STP_TEXT = {"isoliert": "isoliert", "kompensiert": "kompensiert", "niederohmig": "niederohmig",
             "direkt": "starr geerdet"}


def _erdungstext(kid, k, w, null) -> str:
    """Kurztext fuer die Anzeige: wie der Bereich des Knotens geerdet ist."""
    if not geerdet(k):
        return f"nicht geerdet ({_STP_TEXT.get(k.sternpunkt, k.sternpunkt)}), kein Ik1"
    if null is None:
        return "Nullsystem nicht berechnet"
    ber = null["bereich"].get(w)
    texte = [t for r, tl in null["texte"].items() if null["bereich"].get(r) == ber for t in tl]
    return "; ".join(texte) if texte else "geerdet, aber kein Erdungspunkt erkannt"


def _meldungen_erdung(kn, verbund, null, erg) -> None:
    """Je Bereich: geerdet ohne Erdungspunkt oder uneinheitliche Sternpunktbehandlung melden."""
    if null is None:
        return
    je_bereich: dict = {}
    for kid, k in kn.items():
        je_bereich.setdefault(null["bereich"][verbund.wurzel(kid)], []).append(k)
    for _, knoten in sorted(je_bereich.items()):
        ids = tuple(sorted(k.id for k in knoten))
        arten = {k.sternpunkt for k in knoten}
        if len(arten) > 1:
            erg.meldungen.append(Meldung(
                HINWEIS, f"Bereich {', '.join(ids)}: uneinheitliche Sternpunktbehandlung "
                         f"({', '.join(sorted(_STP_TEXT.get(a, a) for a in arten))}). Galvanisch "
                         f"verbundene Knoten haben dieselbe Erdung. Ik1 gilt für den ganzen Bereich.",
                ids))
        if any(geerdet(k) for k in knoten):
            ber = null["bereich"][verbund.wurzel(knoten[0].id)]
            if not any(null["bereich"].get(r) == ber for r in null["texte"]):
                ohne = [k.id for k in knoten if k.sternpunkt == "niederohmig" and k.I_E_begr_A is None]
                tipp = (f" Bei {', '.join(ohne)} die Erdfehlerstrom-Begrenzung eintragen."
                        if ohne else "")
                erg.meldungen.append(Meldung(
                    WARNUNG, f"Bereich {', '.join(ids)} ist geerdet, aber es ist kein Erdungspunkt "
                             f"erkennbar. Ik1 wird nicht berechnet.{tipp}", ids))


def erdstrom_verteilung(ergebnis: KurzschlussErgebnis, fehlerknoten: str,
                        fall: str = MAX) -> ErdstromVerteilung:
    """
    3I0 durch jedes Element und jeden Erdungspunkt bei einem einpoligen Fehler am Knoten.
    Grundlage: Nullsystem-Matrix des Ergebnisses. Wirft nie, leere Verteilung ohne Daten.
    """
    leer = ErdstromVerteilung(fehlerknoten, fall, None)
    try:
        null, r = ergebnis.null, ergebnis.knoten.get(fehlerknoten)
        if null is None or r is None or fall not in null:
            return leer
        pos, Z = null[fall]
        verbund = null["verbund"]
        k = verbund.wurzel(fehlerknoten)
        z1k = r.Zk_max_Ohm if fall == MAX else r.Zk_min_Ohm
        if Z is None or k not in pos or z1k is None:
            return leer
        UN = r.UN_kV
        z1 = z1k * S_B_MVA / (UN * UN)
        z0 = complex(Z[pos[k], pos[k]])
        I0f = c_faktor(UN, fall) / (2.0 * z1 + z0)           # bezogen, E = c
        v = {kk: -complex(Z[i, pos[k]]) * I0f for kk, i in pos.items()}
        I_B = lambda kid: S_B_MVA / (SQRT3 * ergebnis.knoten[kid].UN_kV)
        zweige, erdungen = {}, {}
        for a, b, z, eid, von, nach in null["zweige"][fall]:
            if a not in v or b not in v:
                continue
            i = (v[a] - v[b]) / z
            betrag = 3.0 * abs(i) * I_B(von)
            vorwaerts = (i / I0f).real >= 0                   # von -> nach, Richtung Fehler
            zweige[eid] = (betrag, von if vorwaerts else nach)
        for a, z, quelle, kid in null["erden"][fall]:
            if a not in v:
                continue
            erdungen[quelle] = erdungen.get(quelle, 0.0) + 3.0 * abs(v[a] / z) * I_B(kid)
        Ik1 = r.Ik1_max_kA if fall == MAX else r.Ik1_min_kA
        schwelle = 1e-9 * (Ik1 or 1.0)                       # Rundungsreste weglassen
        zweige = {k: w for k, w in zweige.items() if w[0] > schwelle}
        erdungen = {k: x for k, x in erdungen.items() if x > schwelle}
        return ErdstromVerteilung(fehlerknoten, fall, Ik1, zweige, erdungen)
    except Exception:
        return leer


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
