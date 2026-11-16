"""
tab_netz.py - Streamlit-UI fuer die netzweite Selektivitaetsplanung
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Einziges Netz-Modul mit Streamlit. Die gesamte Logik liegt in netz_*.py.
Das Netzmodell (st.session_state["netz_modell"]) ist die einzige Wahrheit,
diese Seite ist nur eine Ansicht darauf und aendert es ausschliesslich ueber
die Methoden von netz_modell.Netz.

Ablauf:
  1. Steuerleiste: Netzform, Beispielnetz, neues Netz, Speichern/Laden (JSON)
  2. Einlinienbild und Topologie-Meldungen (nur wenn ein Netz vorhanden ist)
  3. Baumeingabe: Knoten anlegen, Element anlegen (Parameter aus den Tabs)
  4. Netz bearbeiten: schalten, Parameter uebernehmen, entfernen
  4b. Kurzschlussstroeme aus den Netzdaten (netz_kurzschluss.py), per Schalter:
      eingegeben, berechnet, Abweichung, im Ring je Trennstellenlage. Eingegebene
      Werte haben immer Vorrang. Nur Knoten OHNE Eingabewert rechnen in der
      Staffelung mit dem berechneten Wert (Kopie, das Modell bleibt unveraendert).
  5. Schutzstufen aus den Betriebsmittel-Tabs (Adapter)
  6. Zeitstaffelung: Pfade, Ampel je benachbartem Paar, Meldungen
     (netz_selektivitaet.py)
  6b. Ring: Pruefung und Vorschlag ueber alle Trennstellenlagen (netz_ring.py)
  7. Staffelvorschlag: erst I>>-Ansprechwerte (Strom), dann Zeiten, Gegenpruefung
     beider, Uebernahme ins Modell (netz_stromstaffel.py)

Bezug zu test_app.py: Bei leerem Netz zeigt die Seite genau einen st.info,
keine Expander und keine Tabellen. Dadurch aendern sich in der Inventur nur
die Zahl der Tabs (6 -> 7) und der Hinweise (5 -> 6). Mit geladenem Netz
zeigt der Tab vier Tabellen (Knoten, Elemente, Schutzstufen, Staffelung).
"""

from pathlib import Path

import pandas as pd
import streamlit as st

import konstanten_netz as KN
import netz_adapter
import netz_bild
import netz_kurzschluss
import netz_ring
import netz_selektivitaet
import netz_stromstaffel
import netz_topologie
from netz_modell import ELEMENTTYPEN, STERNPUNKTE, ModellFehler, Netz
from ui import grphead, inject_css, pill
from utils import AMPEL_EMOJI, de

SCHLUESSEL = "netz_modell"
BEISPIELNETZ = Path(__file__).parent / "beispielnetze" / "industrie_10kV.json"
BEISPIELNETZ_RING = Path(__file__).parent / "beispielnetze" / "industrie_10kV_ring.json"

NETZFORM_TEXT = {"strahl": "Strahlennetz", "ring": "Ringnetz (offen betrieben)"}
STERNPUNKT_TEXT = {
    "isoliert": "Isoliert",
    "kompensiert": "Kompensiert (Petersen)",
    "niederohmig": "Niederohmig geerdet",
    "direkt": "Direkt (starr) geerdet",
}
TYP_TEXT = {
    "einspeisung": "Netzeinspeisung",
    "trafo": "Transformator",
    "leitung": "Leitung",
    "motor": "Motor",
    "kupplung": "Kupplung",
    "generator": "Generator",
}
# Element-Typ -> Tab, dessen Parametersatz uebernommen werden kann
TAB_QUELLE = {"trafo": ("netz_p_trafo", "Transformator"),
              "leitung": ("netz_p_leitung", "Leitung"),
              "motor": ("netz_p_motor", "Motor")}
OHNE = "—"


# ── Zustand ──────────────────────────────────────────────────────────────────
def _netz() -> Netz:
    if SCHLUESSEL not in st.session_state:
        st.session_state[SCHLUESSEL] = Netz()
    return st.session_state[SCHLUESSEL]


def _setze_netz(netz: Netz, meldung: str) -> None:
    st.session_state[SCHLUESSEL] = netz
    st.session_state["netz_erfolg"] = meldung


def _erfolg(meldung: str) -> None:
    """Erfolgsmeldung fuer den naechsten Lauf merken und neu zeichnen."""
    st.session_state["netz_erfolg"] = meldung
    st.rerun()


def _p_aus_tab(typ: str):
    """Letzten Parametersatz des passenden Tabs holen, nur speicherbare Werte."""
    if typ not in TAB_QUELLE:
        return None
    p = st.session_state.get(TAB_QUELLE[typ][0])
    if not isinstance(p, dict):
        return None
    return {k: v for k, v in p.items()
            if isinstance(k, str) and (v is None or isinstance(v, (bool, int, float, str)))}


def _zahl_oder_none(x):
    return None if x is None else float(x)


# ── Anzeige von Meldungen ────────────────────────────────────────────────────
def _meldungen(meldungen) -> None:
    for m in meldungen:
        if m.stufe == netz_topologie.FEHLER:
            st.error(m.text, icon="🔴")
        elif m.stufe == netz_topologie.WARNUNG:
            st.warning(m.text, icon="🟡")
        else:
            st.caption(f"ℹ️ {m.text}")


# ── 1. Steuerleiste ──────────────────────────────────────────────────────────
def _steuerleiste(netz: Netz) -> None:
    c1, c2, c3, c4 = st.columns([2.2, 1, 1, 1])
    with c1:
        # Ohne key: der Wert kommt bei jedem Lauf aus dem Modell (Modell ist die Wahrheit)
        form = st.radio("Netzform", list(NETZFORM_TEXT), horizontal=True,
                        index=list(NETZFORM_TEXT).index(netz.netzform),
                        format_func=NETZFORM_TEXT.get)
        if form != netz.netzform:
            netz.setze_netzform(form)
            st.rerun()
    with c2:
        if st.button("📂 Beispielnetz laden", key="netz_btn_beispiel", width="stretch"):
            try:
                _setze_netz(Netz.laden(BEISPIELNETZ), "Beispielnetz „Industrie 10 kV“ geladen.")
                st.rerun()
            except (OSError, ModellFehler) as exc:
                st.error(f"Beispielnetz konnte nicht geladen werden: {exc}")
        if st.button("🔁 Ring-Beispiel laden", key="netz_btn_beispiel_ring", width="stretch"):
            try:
                _setze_netz(Netz.laden(BEISPIELNETZ_RING), "Ring-Beispielnetz „Industrie 10 kV Ring“ geladen.")
                st.rerun()
            except (OSError, ModellFehler) as exc:
                st.error(f"Beispielnetz konnte nicht geladen werden: {exc}")
    with c3:
        if st.button("🗑️ Neues leeres Netz", key="netz_btn_neu", width="stretch"):
            _setze_netz(Netz(), "Neues leeres Netz angelegt.")
            st.rerun()
    with c4:
        st.download_button("💾 Netz speichern", data=netz.to_json(),
                           file_name="netz.json", mime="application/json",
                           key="netz_btn_speichern", width="stretch")

    datei = st.file_uploader("Gespeichertes Netz laden (JSON)", type=["json"], key="netz_upload")
    # Ein hochgeladenes File bleibt bei jedem Lauf stehen. Nur einmal einlesen.
    if datei is not None and st.session_state.get("netz_upload_id") != datei.file_id:
        st.session_state["netz_upload_id"] = datei.file_id
        try:
            _setze_netz(Netz.from_json(datei.getvalue().decode("utf-8")),
                        f"Netz aus „{datei.name}“ geladen.")
            st.rerun()
        except (ModellFehler, UnicodeDecodeError) as exc:
            st.error(f"Datei konnte nicht geladen werden: {exc}")


# ── 3. Baumeingabe ───────────────────────────────────────────────────────────
def _form_knoten(netz: Netz) -> None:
    grphead("Knoten anlegen (Sammelschiene)")
    with st.form("netz_form_knoten", clear_on_submit=True):
        a, b, c = st.columns([1, 2, 1])
        kid = a.text_input("ID", placeholder="z. B. K6", key="netz_k_id")
        name = b.text_input("Bezeichnung", placeholder="z. B. Unterverteilung Halle 3", key="netz_k_name")
        un = c.number_input("UN [kV]", min_value=0.0, value=None, step=1.0, key="netz_k_un",
                            placeholder="z. B. 10")
        d, e, f = st.columns(3)
        stp = d.selectbox("Sternpunktbehandlung", STERNPUNKTE, format_func=STERNPUNKT_TEXT.get,
                          key="netz_k_stp")
        ikmax = e.number_input("Ik″ max [kA]", min_value=0.0, value=None, step=0.5,
                               key="netz_k_ikmax", placeholder="optional")
        ikmin = f.number_input("Ik min 2-pol. [kA]", min_value=0.0, value=None, step=0.5,
                               help="Kleinster zweipoliger Kurzschlussstrom (Tool-Vorgabe). "
                                    "Er geht in die Empfindlichkeitsprüfung ein.",
                               key="netz_k_ikmin", placeholder="optional")
        if st.form_submit_button("➕ Knoten anlegen"):
            try:
                netz.knoten_hinzufuegen(kid.strip(), name.strip(), _zahl_oder_none(un), stp,
                                        _zahl_oder_none(ikmax) or None, _zahl_oder_none(ikmin) or None)
                _erfolg(f"Knoten {kid.strip()} angelegt.")
            except ModellFehler as exc:
                st.error(str(exc))


def _form_element(netz: Netz) -> None:
    grphead("Element anlegen (Betriebsmittel)")
    if not netz.knoten:
        st.caption("Zuerst mindestens einen Knoten anlegen.")
        return
    knoten = [OHNE] + sorted(netz.knoten)
    with st.form("netz_form_element", clear_on_submit=True):
        a, b, c = st.columns([1, 2, 1.3])
        eid = a.text_input("ID", placeholder="z. B. L3", key="netz_e_id")
        name = b.text_input("Bezeichnung", placeholder="z. B. Kabel zur Halle 3", key="netz_e_name")
        typ = c.selectbox("Typ", list(ELEMENTTYPEN), format_func=TYP_TEXT.get, key="netz_e_typ")
        d, e, f = st.columns(3)
        von = d.selectbox("von Knoten (Speiseseite, Trafo: OS)", knoten, key="netz_e_von")
        nach = e.selectbox("nach Knoten (Lastseite, Trafo: US)", knoten, key="netz_e_nach")
        zustand = f.radio("Zustand", ["ein", "aus"], horizontal=True, key="netz_e_zustand")
        st.caption("Einspeisung und Generator nutzen nur „nach“, der Motor nur „von“. "
                   "Das jeweils andere Feld wird ignoriert.")
        g, h, i = st.columns([2, 1, 1])
        uebernehmen = g.checkbox("Parameter aus dem passenden Tab übernehmen "
                                 "(Trafo, Leitung, Motor)", value=True, key="netz_e_uebern")
        i_nb = h.number_input("Einspeisung: I> Netzbetreiber [A]", min_value=0.0, value=None,
                              key="netz_e_inb", placeholder="optional")
        t_nb = i.number_input("Einspeisung: t Netzbetreiber [s]", min_value=0.0, value=None,
                              key="netz_e_tnb", placeholder="optional")
        if st.form_submit_button("➕ Element anlegen"):
            braucht_von, braucht_nach = ELEMENTTYPEN[typ]
            v = von if (braucht_von and von != OHNE) else None
            n = nach if (braucht_nach and nach != OHNE) else None
            p, hinweis = {}, ""
            if uebernehmen and typ in TAB_QUELLE:
                p = _p_aus_tab(typ) or {}
                hinweis = (f" Parameter aus dem Tab {TAB_QUELLE[typ][1]} übernommen." if p else
                           f" Im Tab {TAB_QUELLE[typ][1]} sind noch keine Grunddaten berechnet, "
                           f"Parameter bleiben leer.")
            if typ == "einspeisung":
                if i_nb:
                    p["I_gt_NB_A"] = float(i_nb)
                if t_nb:
                    p["t_gt_NB_s"] = float(t_nb)
            try:
                netz.element_hinzufuegen(eid.strip(), name.strip(), typ, v, n, p, zustand)
                _erfolg(f"Element {eid.strip()} angelegt.{hinweis}")
            except ModellFehler as exc:
                st.error(str(exc))


# ── 4. Netz bearbeiten ───────────────────────────────────────────────────────
def _bearbeiten(netz: Netz) -> None:
    grphead("Netz bearbeiten")
    elemente = netz.elemente
    knoten = netz.knoten
    if elemente:
        a, b, c, d = st.columns([1.4, 1, 1.4, 1])
        eid = a.selectbox("Element", sorted(elemente), key="netz_b_element",
                          format_func=lambda x: f"{x} · {TYP_TEXT[elemente[x].typ]}")
        e = elemente[eid]
        if b.button("🔀 Ein/Aus schalten", key="netz_b_schalten", width="stretch"):
            netz.element_aendern(eid, zustand="aus" if e.zustand == "ein" else "ein")
            _erfolg(f"{eid} ist jetzt {'aus' if e.zustand == 'ein' else 'ein'}geschaltet.")
        kann_uebernehmen = e.typ in TAB_QUELLE
        if c.button("📥 Parameter aus Tab übernehmen", key="netz_b_uebernehmen",
                    width="stretch", disabled=not kann_uebernehmen):
            p = _p_aus_tab(e.typ)
            if p:
                netz.parameter_setzen(eid, p)
                _erfolg(f"Parameter von {eid} aus dem Tab {TAB_QUELLE[e.typ][1]} übernommen.")
            else:
                st.warning(f"Im Tab {TAB_QUELLE[e.typ][1]} sind noch keine Grunddaten berechnet.")
        if d.button("❌ Element entfernen", key="netz_b_entf_element", width="stretch"):
            netz.element_entfernen(eid)
            _erfolg(f"Element {eid} entfernt.")
    if knoten:
        a, b, _ = st.columns([1.4, 1, 2.4])
        kid = a.selectbox("Knoten", sorted(knoten), key="netz_b_knoten")
        if b.button("❌ Knoten entfernen", key="netz_b_entf_knoten", width="stretch"):
            try:
                netz.knoten_entfernen(kid)
                _erfolg(f"Knoten {kid} entfernt.")
            except ModellFehler as exc:
                st.error(str(exc))

    st.dataframe(pd.DataFrame([{
        "Knoten": k.id, "Bezeichnung": k.name, "UN [kV]": de(k.UN_kV, 1),
        "Sternpunkt": STERNPUNKT_TEXT[k.sternpunkt],
        "Ik″ max [kA]": "–" if k.Ik_max_kA is None else de(k.Ik_max_kA, 1),
        "Ik min 2-pol. [kA]": "–" if k.Ik_min_kA is None else de(k.Ik_min_kA, 1),
    } for k in sorted(knoten.values(), key=lambda k: k.id)]), width="stretch", hide_index=True)
    if elemente:
        st.dataframe(pd.DataFrame([{
            "Element": e.id, "Typ": TYP_TEXT[e.typ], "Bezeichnung": e.name,
            "von": e.von or "–", "nach": e.nach or "–", "Zustand": e.zustand,
            "Parameter": len(e.p),
        } for e in sorted(elemente.values(), key=lambda e: e.id)]), width="stretch", hide_index=True)


# ── 4b. Kurzschlussstroeme aus den Netzdaten ─────────────────────────────────
def _ka(wert, stellen: int = 2) -> str:
    return "–" if wert is None else de(wert, stellen)


def _abw(v) -> str:
    a = v.abweichung
    if a is None:
        return "–"
    return f"{'+' if a >= 0 else '−'}{de(abs(a) * 100, 1)} %" + (" ⚠️" if v.auffaellig else "")


def _kurzschluss(netz: Netz):
    """
    Berechnete Kurzschlussstroeme neben den eingegebenen zeigen. Rueckgabe (Rechennetz, an):
    Das Rechennetz ist eine Kopie, in der NUR Knoten ohne Eingabewert den berechneten Ik
    tragen. Ohne Schalter das Netz selbst. Geschrieben wird immer ins Modell, nie in die Kopie.
    """
    grphead("Kurzschlussströme aus den Netzdaten")
    if not st.toggle("Kurzschlussströme berechnen und mit den eingegebenen Werten vergleichen",
                     key="netz_ik_an",
                     help="Vereinfachte Rechnung in Anlehnung an IEC 60909-0 aus Sk″ der "
                          "Einspeisung, uk der Trafos und den Leitungsbelägen. Eingegebene Werte "
                          "haben immer Vorrang und werden nie überschrieben. Nur wo kein Wert "
                          "eingegeben ist, rechnet die Staffelung mit dem berechneten. "
                          "Annahmen: docs/tool_vorgabe_kurzschluss.md."):
        return netz, False
    zustaende = netz_kurzschluss.berechne_schaltzustaende(netz)
    akt = zustaende[0]
    _meldungen(akt.meldungen)
    if not any(k.Ik_max_kA is not None or k.Ik_min_kA is not None for k in akt.knoten.values()):
        st.caption("Noch nichts berechenbar. Nötig sind eine Einspeisung mit Sk″ und die "
                   "Impedanzdaten der Trafos (Sn, uk) und Leitungen (Länge, X′).")
        return netz, True
    vgl = {(v.knoten, v.groesse): v for v in netz_kurzschluss.vergleiche(netz, akt)}
    netz_r, ergaenzt, meld = netz_kurzschluss.ergaenze_ik(netz, akt)
    _meldungen(meld)
    gilt = {}
    for e in ergaenzt:
        gilt.setdefault(e.knoten, []).append("Ik max" if e.groesse == "max" else "Ik min")

    def zeile(kid):
        r, vmax, vmin = akt.knoten[kid], vgl[(kid, "max")], vgl[(kid, "min")]
        return {
            "Knoten": kid, "UN [kV]": de(r.UN_kV, 1),
            "Ik″ max eingegeben [kA]": _ka(vmax.eingegeben_kA),
            "Ik″ max berechnet [kA]": _ka(vmax.berechnet_kA), "Abw. max": _abw(vmax),
            "Ik min eingegeben [kA]": _ka(vmin.eingegeben_kA),
            "Ik min berechnet [kA]": _ka(vmin.berechnet_kA), "Abw. min": _abw(vmin),
            "Ik″ max mit Motoren [kA]": _ka(r.Ik_max_mit_Motor_kA),
            "Staffelung rechnet mit": ("berechnet: " + ", ".join(gilt[kid])) if kid in gilt
                                      else "eingegeben",
        }

    st.dataframe(pd.DataFrame([zeile(k) for k in sorted(akt.knoten)]),
                 width="stretch", hide_index=True)
    titel = "" if akt.art == netz_kurzschluss.AKTUELL else f" Lage: {akt.bezeichnung}."
    st.caption("Ik″ max dreipolig ohne Motoren (der Strom, den die vorgelagerten Schutzgeräte "
               "führen), Ik min zweipolig. Abweichung = berechnet gegen eingegeben, ⚠️ ab "
               f"{de(KN.Ik_Abweichung_Hinweis * 100, 0)} %. Eingegebene Werte bleiben gültig."
               + titel)
    if ergaenzt:
        st.caption("Ohne Eingabewert, deshalb berechnet in der Staffelung verwendet: "
                   + ", ".join(f"{e.knoten} {'Ik max' if e.groesse == 'max' else 'Ik min'} "
                               f"{de(e.wert_kA, 2)} kA" for e in ergaenzt) + ".")

    if len(zustaende) > 1:
        _kurzschluss_lagen(netz, zustaende)

    with st.expander("Details: Impedanzen und Annahmen der Kurzschlussrechnung"):
        st.dataframe(pd.DataFrame([{
            "Element": i.element, "Typ": TYP_TEXT.get(i.typ, i.typ),
            "bezogen auf [kV]": de(i.UN_kV, 1),
            "Z für Ik max": netz_kurzschluss.polar_text(i.Z_max),
            "Z für Ik min": netz_kurzschluss.polar_text(i.Z_min),
            "Annahmen": "; ".join(i.annahmen) or "–",
        } for i in akt.impedanzen]), width="stretch", hide_index=True)
        st.caption(
            f"Spannungsfaktor c: über 1 kV {de(KN.c_max_HS, 2)} (max) und {de(KN.c_min_HS, 2)} "
            f"(min), bis 1 kV {de(KN.c_max_NS, 2)} und {de(KN.c_min_NS, 2)}. Ik min = √3/2 × "
            "dreipoliger Strom. Nicht berücksichtigt: Generatoren, Erdfehler, Lastströme, "
            "Lichtbogenwiderstand. Alle Annahmen sind Tool-Vorgaben "
            "(docs/tool_vorgabe_kurzschluss.md).")
    return netz_r, True


def _kurzschluss_lagen(netz: Netz, zustaende) -> None:
    """Ring: berechnete Werte je Trennstellenlage, nur fuer Knoten, deren Wert sich aendert."""
    kn = netz.knoten

    def paar(z, kid):
        r = z.knoten.get(kid)
        return (None, None) if r is None else (r.Ik_max_kA, r.Ik_min_kA)

    def verschieden(kid):
        werte = [paar(z, kid) for z in zustaende]
        return any(a is not None and b is not None and abs(a - b) > 1e-6 * max(a, b)
                   for w in werte for a, b in zip(w, werte[0]))

    wechselnd = [k for k in sorted(kn) if verschieden(k)]
    if not wechselnd:
        st.caption("Im Ring ändert sich kein berechneter Wert mit der Trennstellenlage.")
        return
    st.markdown("**Berechnet je Trennstellenlage** (Ik″ max / Ik min 2-pol. in kA)")
    zeilen = [{"Schaltzustand": "eingegeben (gilt in der Staffelung für alle Lagen)",
               **{k: f"{_ka(kn[k].Ik_max_kA)} / {_ka(kn[k].Ik_min_kA)}" for k in wechselnd}}]
    hinweise = []
    for z in zustaende:
        zeilen.append({"Schaltzustand": z.bezeichnung,
                       **{k: f"{_ka(paar(z, k)[0])} / {_ka(paar(z, k)[1])}" for k in wechselnd}})
        if z.art != netz_kurzschluss.LAGE:
            continue
        for v in netz_kurzschluss.vergleiche(netz, z):
            if v.knoten in wechselnd and v.auffaellig:
                hinweise.append(
                    f"{v.knoten} {'Ik max' if v.groesse == 'max' else 'Ik min'} in Lage "
                    f"„{z.bezeichnung}“: berechnet {de(v.berechnet_kA, 2)} kA, eingegeben "
                    f"{de(v.eingegeben_kA, 2)} kA ({_abw(v).replace(' ⚠️', '')})")
    st.dataframe(pd.DataFrame(zeilen), width="stretch", hide_index=True)
    st.caption("Nur Knoten, deren Wert sich mit der Lage ändert. „Ring geschlossen“ ist kein "
               "Betriebszustand der Staffelung, zeigt aber den größten Ik″ max beim Umschalten "
               "ohne Unterbrechung.")
    if hinweise:
        st.warning("Die eingegebenen Werte passen nicht zu jeder Trennstellenlage: "
                   + "; ".join(hinweise) + ". Die Ringstaffelung rechnet weiter mit den "
                   "eingegebenen Werten.")


# ── 5. Schutzstufen ──────────────────────────────────────────────────────────
def _schutzstufen(netz: Netz, topo):
    """Schutzstufen anzeigen. Liefert das Adapter-Ergebnis fuer die Staffelung (oder None)."""
    grphead("Schutzstufen aus den Betriebsmittel-Tabs")
    if not topo.ok:
        st.caption("Erst die Topologie-Fehler oben beheben, dann werden die Schutzstufen erzeugt.")
        return None
    erg = netz_adapter.erzeuge_schutzstufen(netz, topo)
    _meldungen(erg.meldungen)
    if not erg.stufen:
        st.caption("Noch keine Schutzstufen. Elemente brauchen Parameter aus den Tabs.")
        return None
    st.caption("Werte aus den Rechenkernen der Tabs (Werksvoreinstellung, sofern im Tab nicht "
               "geändert). Die Zeiten werden im nächsten Abschnitt gegeneinander gestaffelt.")
    st.dataframe(pd.DataFrame([{
        "Element": s.element, "Stufe": s.stufe, "ANSI": s.ansi, "Messort": s.messort,
        "UN [kV]": de(s.UN_kV, 1), "I prim. [A]": de(s.I_prim_A, 1), "Kennlinie": s.kennlinie,
        "t [s]": "–" if s.t_s is None else de(s.t_s, 2),
        "T-Mult.": "–" if s.T_mult is None else de(s.T_mult, 2),
        "aktiv": "ja" if s.aktiv else "nein", "Herkunft": s.quelle,
    } for s in sorted(erg.stufen, key=lambda s: (-s.UN_kV, s.element, s.stufe))]),
        width="stretch", hide_index=True)
    return erg


# ── 6. Zeitstaffelung ────────────────────────────────────────────────────────
def _zeit(t) -> str:
    return "–" if t is None else de(t, 2)


def _staffelung(netz: Netz, adapter, ziel: Netz | None = None, ik_an: bool = False) -> None:
    """
    Ergebnis von netz_selektivitaet.pruefe_selektivitaet anzeigen.
    Der Sollabstand ist hier einstellbar (Tool-Vorgabe 0,30 s), der technische
    Mindestwert bleibt fest, damit die rote Ampel nicht weggeregelt werden kann.
    netz ist das Rechennetz (ggf. mit berechnet ergaenzten Ik), ziel das Modell, in das
    Vorschlaege geschrieben werden.
    """
    ziel = netz if ziel is None else ziel
    grphead("Zeitstaffelung entlang der Versorgungspfade")
    if adapter is None:
        st.caption("Die Staffelprüfung läuft, sobald Schutzstufen vorhanden sind.")
        return
    a, b = st.columns([1, 3])
    dt_soll = a.number_input("Staffelabstand Soll [s]", min_value=KN.dt_Staffel_min,
                             max_value=1.0, value=KN.dt_Staffel_soll, step=0.05,
                             format="%.2f", key="netz_dt_soll",
                             help="Tool-Vorgabe, Herleitung in docs/tool_vorgabe_staffelabstand.md. "
                                  f"Technischer Mindestwert {de(KN.dt_Staffel_min, 2)} s "
                                  "(Schalterzeit, Rückfallzeit, Toleranzen, Sicherheitszuschlag).")
    erg = netz_selektivitaet.pruefe_selektivitaet(netz, adapter, dt_soll=float(dt_soll))
    _meldungen(erg.meldungen)
    if not erg.pruefungen:
        if erg.ok:
            st.caption("Keine Paare zu prüfen: es gibt nur einen Schutzort je Pfad.")
        return

    anz = {k: sum(1 for p in erg.pruefungen if p.status == k)
           for k in (netz_selektivitaet.OK, netz_selektivitaet.GELB, netz_selektivitaet.ROT)}
    with b:
        st.markdown(
            f'<div style="margin-top:28px">{AMPEL_EMOJI[erg.status]} <b>Gesamt: {erg.status}</b> &nbsp; '
            + " ".join(pill(k, n) for k, n in anz.items() if n)
            + f'<br><span style="font-size:0.8rem;color:#5d6b82">Bezugsspannung '
            f'{de(erg.U_bezug_kV, 1)} kV · Soll {de(erg.dt_soll_s, 2)} s · '
            f'Mindestwert {de(erg.dt_min_s, 2)} s · {len(erg.pruefungen)} Paare</span></div>',
            unsafe_allow_html=True)
    for pfad in erg.pfade:
        st.caption("🔗 " + " → ".join(pfad))

    # Reihenfolge wie in den Pfaden (von der Last zur Quelle), nicht nach Element-ID
    rang = {}
    for pfad in erg.pfade:
        for i, name in enumerate(pfad):
            rang.setdefault(name, (len(rang), i))
    pruefungen = sorted(erg.pruefungen, key=lambda p: rang.get(p.unten, (99, 99)))
    st.dataframe(pd.DataFrame([{
        "Ampel": AMPEL_EMOJI[p.status], "unten (Last)": p.unten, "Stufe unten": p.stufe_unten or "–",
        "t unten [s]": _zeit(p.t_unten_s), "oben (Quelle)": p.oben, "Stufe oben": p.stufe_oben or "–",
        "t oben [s]": _zeit(p.t_oben_s), "Δt [s]": _zeit(p.dt_s),
        "I [A bez.]": "–" if p.I_bez_A is None else de(p.I_bez_A, 0),
        "Bewertung": p.text,
    } for p in pruefungen]), width="stretch", hide_index=True)
    st.caption("Je Paar der kleinste Zeitabstand über alle Ströme, bei denen beide Schutzorte "
               "anregen. Ströme auf die Bezugsspannung umgerechnet. Grün ab Soll, gelb zwischen "
               "Mindestwert und Soll, rot darunter. Nur Phasenstufen 50/51, Erdfehlerstufen "
               "werden nicht gestaffelt. Die Zeitprüfung rechnet in Nennübersetzung, Stufensteller "
               "und Schaltgruppe berücksichtigt die Stromstaffelung im Staffelvorschlag.")
    if adapter.topologie is not None and adapter.topologie.netzform_erkannt == "ring":
        _ring(ziel, float(dt_soll), adapter.topologie.trennstelle, ik_an)
    _vorschlag(netz, adapter, float(dt_soll), ziel)


# ── 6b. Ring: alle Trennstellenlagen ─────────────────────────────────────────
def _lagentabelle(erg, aktuell) -> None:
    zeilen = []
    for l in erg.lagen:
        z = l.zeit.pruefungen if l.zeit else []
        n = {k: sum(1 for p in z if p.status == k)
             for k in (netz_selektivitaet.OK, netz_selektivitaet.GELB, netz_selektivitaet.ROT)}
        sp = l.schlechtestes_paar
        zeilen.append({
            "Ampel": AMPEL_EMOJI[l.status] if l.status else "–",
            "Trennstelle": l.trennstelle + (" (aktuell)" if l.trennstelle == aktuell else ""),
            "grün / gelb / rot": f"{n[netz_selektivitaet.OK]} / {n[netz_selektivitaet.GELB]} / "
                                 f"{n[netz_selektivitaet.ROT]}",
            "Strom": AMPEL_EMOJI[l.strom.status] if l.strom and l.strom.status else "–",
            "Schlechtestes Paar": "–" if sp is None else
                                  f"{sp.unten} → {sp.oben}, Δt {_zeit(sp.dt_s)} s",
        })
    st.dataframe(pd.DataFrame(zeilen), width="stretch", hide_index=True)


def _strom_text(I_A, faktor) -> str:
    """Ansprechwert fuer die Aenderungsliste: primaer in A, dahinter der Faktor."""
    return f"{de(I_A, 0)} A" if faktor is None else f"{de(I_A, 0)} A ({de(faktor, 2)} × IN)"


def _warum_zeit(grund: str, dt_soll: float) -> str:
    """Kurzbegruendung einer Zeit: 'Staffelabstand ueber <Stufe darunter>'."""
    if grund.startswith("Lage ") and ": " in grund:
        lage, rest = grund.split(": ", 1)
        return f"{lage}: {_warum_zeit(rest, dt_soll)}"
    if grund.startswith(("Mindestzeit", "Untergrenze", "Endpunkt", "Netzbetreiber", "AMZ")):
        return grund
    return f"{de(dt_soll, 2)} s über {grund}"


def _aenderungsliste(zeilen, titel: str) -> None:
    st.markdown(f"**{titel}**")
    st.dataframe(pd.DataFrame(zeilen), width="stretch", hide_index=True)


def _ring(netz: Netz, dt_soll: float, aktuell, ik_an: bool = False) -> None:
    """
    Ring: Ist-Einstellungen in jeder moeglichen Trennstellenlage pruefen und auf Wunsch
    einen Satz Werte vorschlagen, der in allen Lagen gilt (netz_ring.py).
    """
    grphead("Ring: Staffelung in allen Trennstellenlagen")
    erg = netz_ring.pruefe_ringlagen(netz, dt_soll=dt_soll, ik_ergaenzen=ik_an)
    _meldungen(erg.meldungen)
    if not erg.lagen:
        return
    _lagentabelle(erg, aktuell)
    st.caption("Jedes Ringelement kann Trennstelle werden. Je Zeile ist dieses Element offen, "
               "geprüft werden die Einstellwerte im Netz. Spalte Strom: Stromstaffel und "
               "Empfindlichkeit.")
    if not st.toggle("Ringvorschlag berechnen (ein Satz Werte für alle Lagen)",
                     key="netz_ring_vorschlag_an",
                     help="Je Lage erst Strom, dann Zeit. Je Wert gilt der größte über alle "
                          "Lagen, wiederholt bis sich nichts mehr ändert. Gegenläufige Ketten "
                          "werden namentlich gemeldet. Herleitung: docs/tool_vorgabe_ring.md."):
        return
    rv = netz_ring.ringvorschlag(netz, dt_soll=dt_soll, ik_ergaenzen=ik_an)
    _meldungen(rv.meldungen)
    if not rv.werte:
        return
    if rv.geaendert:
        _aenderungsliste([{
            "Element": w.element, "Stufe": w.stufe,
            "Größe": "Ansprechwert" if w.art == "Strom" else "Zeit",
            "bisher": _strom_text(w.alt * w.IN_A, w.alt) if w.art == "Strom" and w.IN_A
                      else f"{de(w.alt, 2)} s",
            "neu": _strom_text(w.neu * w.IN_A, w.neu) if w.art == "Strom" and w.IN_A
                   else f"{de(w.neu, 2)} s",
            "Warum": w.kurz if w.art == "Strom" else _warum_zeit(w.kurz, dt_soll),
        } for w in rv.geaendert], "Was ist zu ändern (gilt in allen Lagen)")
    else:
        st.caption("Keine Änderung nötig, die Werte im Netz gelten bereits in allen Lagen.")
    if rv.pruefung is not None and rv.pruefung.lagen:
        st.markdown("**Ergebnis mit diesen Werten, je Lage**")
        _lagentabelle(rv.pruefung, aktuell)
    if rv.uebernehmbar:
        if st.button("✅ Ringvorschlag ins Netz übernehmen", key="netz_ring_uebernehmen"):
            je_element = rv.parameter_je_element()
            for eid, p_neu in je_element.items():
                p_alt = dict(netz.elemente[eid].p)
                p_alt.update(p_neu)
                netz.parameter_setzen(eid, p_alt)
            _erfolg(f"Ringvorschlag übernommen: {len(rv.geaendert)} Werte in "
                    f"{len(je_element)} Elementen gesetzt.")
    with st.expander("Details: alle Werte mit Herleitung"):
        st.dataframe(pd.DataFrame([{
            "Element": w.element, "Stufe": w.stufe, "Parameter": w.parameter, "Art": w.art,
            "bisher": de(w.alt, 2), "Vorschlag": de(w.neu, 2),
            "Änderung": "✏️" if w.geaendert else "", "Bestimmt durch": w.grund or "–",
        } for w in rv.werte]), width="stretch", hide_index=True)
        st.caption(f"{rv.runden} Runden bis zum Fixpunkt. Zeiten in s, Ansprechwerte als "
                   "Faktor × IN. Geschrieben werden die Parameter in der Spalte Parameter.")


# ── 7. Staffelvorschlag ──────────────────────────────────────────────────────
def _vorschlag(netz: Netz, adapter, dt_soll: float, ziel: Netz | None = None) -> None:
    """
    Vorschlag von der Last zur Quelle: erst die I>>-Ansprechwerte (Stromstaffelung),
    dann die Zeiten mit diesen Werten, dann Gegenpruefung. Oben steht nur, was zu aendern
    ist. Alle Stufen mit Herleitung stehen im aufklappbaren Bereich. Der Vorschlag wird bei
    jedem Lauf neu aus dem Modell gerechnet (Modell ist die Wahrheit).
    netz ist das Rechennetz, ziel das Modell, in das die Uebernahme schreibt.
    """
    ziel = netz if ziel is None else ziel
    ring = adapter.topologie is not None and adapter.topologie.netzform_erkannt == "ring"
    grphead("Staffelvorschlag nur für die aktuelle Trennstellenlage" if ring
            else "Staffelvorschlag (erst Strom, dann Zeit)")
    if ring:
        st.caption("Im Ring gilt dieser Vorschlag nur für die aktuelle Trennstellenlage. "
                   "Für alle Lagen den Ringvorschlag oben verwenden.")
    if not st.toggle("Staffelvorschlag berechnen", key="netz_vorschlag_an",
                     help="Erst die I>>-Ansprechwerte über Ik max der nächsten Station (mit "
                          "Stufensteller und Schaltgruppe), dann jede UMZ-Stufe so schnell wie "
                          "möglich, aber einen Staffelabstand über allem, was darunter bei "
                          "demselben Strom auslöst. Endpunkte (Motor, unterste Trafoseite) und "
                          "Netzbetreiber bleiben unverändert. Herleitung: "
                          "docs/tool_vorgabe_stromstaffelung.md."):
        return
    vor = netz_stromstaffel.gesamtvorschlag(netz, adapter, dt_soll=dt_soll)
    _meldungen(vor.meldungen)
    if vor.zeit is None or vor.zeit.pruefung is None:
        return

    n_strom, n_zeit = len(vor.strom.geaendert), len(vor.zeit.geaendert)
    if n_strom or n_zeit:
        zeilen = [{
            "Element": v.element, "Stufe": v.stufe, "Größe": "Ansprechwert",
            "bisher": _strom_text(v.I_alt_A, v.faktor_alt), "neu": _strom_text(v.I_neu_A, v.faktor_neu),
            "Warum": v.kurz or v.status,
        } for v in vor.strom.geaendert] + [{
            "Element": v.element, "Stufe": v.stufe, "Größe": "Zeit",
            "bisher": f"{de(v.t_alt_s, 2)} s", "neu": f"{de(v.t_neu_s, 2)} s",
            "Warum": _warum_zeit(v.grund, dt_soll),
        } for v in vor.zeit.geaendert]
        _aenderungsliste(zeilen, "Was ist zu ändern")
    else:
        st.caption("Keine Änderung nötig, die Werte im Netz entsprechen bereits dem Vorschlag.")

    p, sp = vor.zeit.pruefung, vor.strom.pruefung
    anz = {k: sum(1 for x in p.pruefungen if x.status == k)
           for k in (netz_selektivitaet.OK, netz_selektivitaet.GELB, netz_selektivitaet.ROT)}
    strom_text = "" if sp is None or sp.status is None else (
        f" &nbsp;·&nbsp; {AMPEL_EMOJI[sp.status]} **Strom: {sp.status}**")
    st.markdown(f"Ergebnis mit diesen Werten: {AMPEL_EMOJI[p.status]} **Zeit: {p.status}** &nbsp; "
                + " ".join(pill(k, n) for k, n in anz.items() if n) + strom_text,
                unsafe_allow_html=True)
    if n_strom or n_zeit:
        st.caption(f"{n_strom} Ansprechwerte und {n_zeit} Zeiten würden geändert. Die Übernahme "
                   "schreibt sie in die Element-Parameter des Netzes (nicht in die Betriebsmittel-"
                   "Tabs).")
        if st.button("✅ Vorschlag ins Netz übernehmen", key="netz_vorschlag_uebernehmen"):
            je_element = vor.parameter_je_element()
            for eid, p_neu in je_element.items():
                p_alt = dict(ziel.elemente[eid].p)
                p_alt.update(p_neu)
                ziel.parameter_setzen(eid, p_alt)
            _erfolg(f"Staffelvorschlag übernommen: {n_strom} Ansprechwerte und {n_zeit} Zeiten in "
                    f"{len(je_element)} Elementen gesetzt.")

    with st.expander("Details: alle Stufen, Herleitung und Gegenprüfung"):
        st.markdown("**1. Strom: I>>-Ansprechwerte**")
        st.dataframe(pd.DataFrame([{
            "Element": v.element, "Stufe": v.stufe, "Parameter": v.parameter or "–",
            "I bisher [A]": de(v.I_alt_A, 0), "I Vorschlag [A]": de(v.I_neu_A, 0),
            "Faktor bisher": "–" if v.faktor_alt is None else de(v.faktor_alt, 2),
            "Faktor Vorschlag": "–" if v.faktor_neu is None else de(v.faktor_neu, 2),
            "Änderung": "✏️" if v.geaendert else "", "Status": v.status,
            "Begründung": v.grund,
        } for v in vor.strom.vorschlaege]), width="stretch", hide_index=True)
        st.markdown("**2. Zeit** (mit den Ansprechwerten aus Schritt 1)")
        st.dataframe(pd.DataFrame([{
            "Element": v.element, "Stufe": v.stufe,
            "Parameter": v.parameter or "–",
            "t bisher [s]": "–" if v.t_alt_s != v.t_alt_s else de(v.t_alt_s, 2),
            "t Vorschlag [s]": "–" if v.t_neu_s != v.t_neu_s else de(v.t_neu_s, 2),
            "Änderung": "✏️" if v.geaendert else "",
            "Bestimmt durch": v.grund,
        } for v in vor.zeit.vorschlaege]), width="stretch", hide_index=True)
        if sp is not None and sp.pruefungen:
            st.markdown("**3. Gegenprüfung Strom** (Stromstaffel und Empfindlichkeit)")
            st.dataframe(pd.DataFrame([{
                "Ampel": AMPEL_EMOJI[x.status], "Prüfung": x.art, "unten (Last)": x.unten,
                "oben (Quelle)": x.oben, "Stufe oben": x.stufe_oben,
                "Soll [A bez.]": "–" if x.I_soll_bez_A is None else de(x.I_soll_bez_A, 0),
                "Ist [A bez.]": "–" if x.I_ist_bez_A is None else de(x.I_ist_bez_A, 0),
                "Bewertung": x.text,
            } for x in sp.pruefungen]), width="stretch", hide_index=True)
        st.caption("„A bez.“ heißt: Strom auf die Bezugsspannung der Staffelprüfung umgerechnet. "
                   "Stromstaffel: I>> oben mindestens k_S × Strom hinter der nächsten Station. "
                   "Empfindlichkeit: Ik min (zweipolig, über Stufensteller und Schaltgruppe) "
                   "mindestens γ × kleinster Ansprechwert oben.")


# ── Einstieg ─────────────────────────────────────────────────────────────────
def show():
    inject_css()
    netz = _netz()
    st.caption("Betriebsmittel zu einem Gesamtnetz verbinden. Knoten sind Sammelschienen, "
               "Elemente verbinden sie. Die Kenndaten kommen aus den Betriebsmittel-Tabs.")
    _steuerleiste(netz)
    if "netz_erfolg" in st.session_state:
        st.success(st.session_state.pop("netz_erfolg"), icon="✅")

    leer = not netz.knoten and not netz.elemente
    if leer:
        st.info("Noch kein Netz angelegt. Beispielnetz laden oder unten mit dem ersten "
                "Knoten beginnen.")
        topo = None
    else:
        topo = netz_topologie.analysiere(netz)
        st.graphviz_chart(netz_bild.einlinienbild_dot(netz, topo))
        erkannt = {"strahl": "Strahlennetz", "ring": "Ring", "vermascht": "vermascht",
                   "leer": "leer"}[topo.netzform_erkannt]
        st.caption(f"Erkannte Struktur: {erkannt} · {len(netz.knoten)} Knoten · "
                   f"{len(netz.elemente)} Elemente · "
                   f"{'🟢 Topologie in Ordnung' if topo.ok else '🔴 Topologie fehlerhaft'}")
        _meldungen(topo.meldungen)

    _form_knoten(netz)
    _form_element(netz)
    if not leer:
        _bearbeiten(netz)
        netz_r, ik_an = _kurzschluss(netz)
        adapter = _schutzstufen(netz_r, topo)
        if topo.ok:
            _staffelung(netz_r, adapter, netz, ik_an)
