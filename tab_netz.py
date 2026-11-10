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
  5. Schutzstufen aus den Betriebsmittel-Tabs (Adapter)
  6. Zeitstaffelung: Pfade, Ampel je benachbartem Paar, Meldungen
     (netz_selektivitaet.py)

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
import netz_selektivitaet
import netz_topologie
from netz_modell import ELEMENTTYPEN, STERNPUNKTE, ModellFehler, Netz
from ui import grphead, inject_css, pill
from utils import AMPEL_EMOJI, de

SCHLUESSEL = "netz_modell"
BEISPIELNETZ = Path(__file__).parent / "beispielnetze" / "industrie_10kV.json"

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
        ikmin = f.number_input("Ik min [kA]", min_value=0.0, value=None, step=0.5,
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
        "Ik min [kA]": "–" if k.Ik_min_kA is None else de(k.Ik_min_kA, 1),
    } for k in sorted(knoten.values(), key=lambda k: k.id)]), width="stretch", hide_index=True)
    if elemente:
        st.dataframe(pd.DataFrame([{
            "Element": e.id, "Typ": TYP_TEXT[e.typ], "Bezeichnung": e.name,
            "von": e.von or "–", "nach": e.nach or "–", "Zustand": e.zustand,
            "Parameter": len(e.p),
        } for e in sorted(elemente.values(), key=lambda e: e.id)]), width="stretch", hide_index=True)


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


def _staffelung(netz: Netz, adapter) -> None:
    """
    Ergebnis von netz_selektivitaet.pruefe_selektivitaet anzeigen.
    Der Sollabstand ist hier einstellbar (Tool-Vorgabe 0,30 s), der technische
    Mindestwert bleibt fest, damit die rote Ampel nicht weggeregelt werden kann.
    """
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
               "Mindestwert und Soll, rot darunter. Nur Phasenstufen 50/51, Erdfehler und "
               "Stromverteilung über die Schaltgruppe folgen mit der Stromstaffelung.")


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
        adapter = _schutzstufen(netz, topo)
        if topo.ok:
            _staffelung(netz, adapter)
