"""
tab_leitung.py — Streamlit-UI fuer Leitungsschutz (SIPROTEC 7SA6 / 7SD5)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Leitgeraet-Selector waehlt zwischen Distanzschutz 7SA6 und Leitungsdifferential 7SD5.
Die Geraetewahl schaltet den Hauptschutz frei und waehlt den korrekten DIGSI-Adresssatz.
"""

import pandas as pd
import streamlit as st

import konstanten_leitung as KL
from calc_leitung import berechne_alle


# ── Farbkodierung (identisch zu den uebrigen Tabs) ───────────────────────────
_CSS = """
<style>
[data-testid="stExpander"] summary {
    background: #2E5A87 !important; border-radius: 6px !important; padding: 5px 12px !important;
}
[data-testid="stExpander"] summary:hover { background: #27496e !important; }
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: #ffffff !important; font-weight: 600 !important; font-size: 0.92rem !important;
}
[data-testid="stExpander"] summary svg { fill: #ffffff !important; color: #ffffff !important; }
[data-testid="stExpander"] details { border: none !important; }
.result-box { background: #eef3f8; color: #14203a; border-left: 4px solid #2E5A87;
    border-radius: 6px; padding: 10px 14px; margin-bottom: 8px; }
.result-box .val { font-size: 1.2rem; font-weight: 700; color: #14203a; font-family: monospace; }
.result-box .lbl { font-size: 0.76rem; color: #43526b; }
.result-box .sub { font-size: 0.74rem; color: #5d6b82; margin-top: 2px; }
.warn-box { background: #fff4d6; color: #5b4a00; border-left: 4px solid #f4a800;
    border-radius: 6px; padding: 10px 14px; font-size: 0.86rem; margin-bottom: 8px; }
.off-box { background: #fbe3ea; color: #7a0024; border-left: 4px solid #A50034;
    border-radius: 6px; padding: 10px 14px; font-size: 0.86rem; margin-bottom: 8px; }
.off-box b { color: #A50034; }
.info-box { background: #e7f3ec; color: #14502b; border-left: 4px solid #2e7d32;
    border-radius: 6px; padding: 10px 14px; font-size: 0.86rem; margin-bottom: 8px; }
.pill { display:inline-block; padding:2px 9px; border-radius:11px; font-size:0.75rem; font-weight:700; }
.pill-ok   { background:#d6f0dc; color:#1d6b32; }
.pill-warn { background:#fdeccb; color:#8a5b00; }
.pill-bad  { background:#fad3dc; color:#a3002b; }
.pill-na   { background:#e6e9ee; color:#5d6b82; }
</style>
"""

_AMPEL_EMOJI = {"OK": "🟢", "Hinweis": "🟡", "Prüfen!": "🔴", "Fehlt": "⚫", "—": "▫️"}
_PILL_CLASS  = {"OK": "pill-ok", "Hinweis": "pill-warn", "Prüfen!": "pill-bad",
                "Fehlt": "pill-na", "—": "pill-na"}


def _metric(label, value, sub=""):
    st.markdown(
        f'<div class="result-box"><div class="lbl">{label}</div>'
        f'<div class="val">{value}</div>'
        + (f'<div class="sub">{sub}</div>' if sub else "") + "</div>",
        unsafe_allow_html=True)


def _section(title, expanded=True):
    return st.expander(title, expanded=expanded)


def _hreg(key):
    h = KL.HERST.get(key)
    if not h:
        return
    adr_pin = (f'<br>📍 <b>Eintragen unter:</b> {h["adr"]}' if h.get("adr") else '')
    st.markdown(
        f'<div style="font-size:0.72rem;color:#5d6b82;margin:-6px 0 10px;line-height:1.25;">'
        f'<b>Hersteller:</b> {h["range"]}<br>{h["grund"]}{adr_pin}</div>',
        unsafe_allow_html=True)


def _pin(adr):
    """Schlanker Adress-Pin unter einem Eingabefeld (einheitlich fuer alle Parameter)."""
    if not adr:
        return
    st.markdown(
        f'<div style="font-size:0.72rem;color:#5d6b82;margin:-6px 0 10px;">'
        f'📍 <b>Eintragen unter:</b> Adr.{adr}</div>',
        unsafe_allow_html=True)


def _grphead(title):
    """Funktions-Untertitel innerhalb eines gruppierten Erweiterte-Parameter-Expanders.
    Erbt die Theme-Textfarbe (im dunklen Theme weiss), mit blauem Trennstrich wie die Tabs."""
    st.markdown(
        f'<div style="font-weight:700;font-size:0.97rem;margin:18px 0 8px;'
        f'padding-bottom:4px;border-bottom:2px solid #2E5A87;">{title}</div>',
        unsafe_allow_html=True)


def _pill(status, count):
    cls = _PILL_CLASS.get(status, "pill-na")
    emj = _AMPEL_EMOJI.get(status, "")
    return f'<span class="pill {cls}">{emj} {status}: {count}</span>'


# ── Hauptfunktion ─────────────────────────────────────────────────────────────

def show():
    st.markdown(_CSS, unsafe_allow_html=True)

    # ══════════════════════ EINGABEN ══════════════════════
    with _section("Eingaben — Leitgeraet, Leitungsdaten, Wandler, Netz"):
        ci1, ci2, ci3 = st.columns(3, gap="medium")
        with ci1:
            st.caption("**Leitungs-Grunddaten**")
            UN  = st.number_input("UN — Bemessungsspannung [kV]", 0.4, value=110.0, step=1.0, format="%.1f", key="ltg_un")
            ltgart = st.selectbox("Leitungsart", KL.LEITUNGSART_OPTIONEN, index=0, key="ltg_art")
            L   = st.number_input("Leitungslänge [km]", 0.1, value=25.0, step=0.5, format="%.2f", key="ltg_l")
            Xbel = st.number_input("X′-Belag [Ω/km]", 0.001, value=KL.X_Belag_def, step=0.001, format="%.3f", key="ltg_xbel")
            Cbel = st.number_input("C′-Belag [µF/km]", 0.0, value=KL.C_Belag_def, step=0.001, format="%.4f", key="ltg_cbel",
                                   help="Kapazitätsbelag der Leitung (Adr.1114), bestimmt den Nennladestrom IcN für 87L.")
            phi = st.number_input("Leitungswinkel φ_Ltg [°]", 30, 90, value=KL.phi_Ltg_def, step=1, key="ltg_phi")
            IN_Ltg = st.number_input("Dauerstrombelastbarkeit IN_Ltg [A]", 0.0, value=600.0, step=10.0, format="%.0f", key="ltg_in",
                                     help="Thermischer Dauerstrom der Leitung (für Reserve-/Überlastfunktionen).")
        with ci2:
            st.caption("**Stromwandler**")
            c1, c2 = st.columns(2)
            with c1:
                CT_P = st.number_input("CT prim. [A]", 1, value=600, step=1, key="ltg_ctp")
            with c2:
                CT_S = st.selectbox("CT sek. [A]", [1, 5], index=0, key="ltg_cts")
            st.caption("**Spannungswandler**")
            v1, v2 = st.columns(2)
            with v1:
                VT_P = st.number_input("VT prim. [kV]", 0.1, value=110.0, step=0.1, format="%.2f", key="ltg_vtp")
            with v2:
                VT_S = st.number_input("VT sek. [V]", 50.0, 230.0, value=100.0, step=1.0, format="%.1f", key="ltg_vts")
        with ci3:
            st.caption("**Leitgerät & Netz**")
            leitgeraet = st.selectbox("⚙️ Leitgerät (Schutzkonzept)", KL.LEITGERAET_OPTIONEN, index=0, key="ltg_dev",
                                      help="7SA6 = Distanzschutz als Hauptschutz · "
                                           "7SD5 = Leitungslängsdifferentialschutz (87L) + integrierter Distanzschutz.")
            stp = st.selectbox("Sternpunktbehandlung Netz", KL.STERNPUNKT_NETZ_OPTIONEN, index=0, key="ltg_stp")
            Ik_max = st.number_input("Ik″ max am Leitungsanfang [kA]", 0.0, value=12.0, step=0.5, format="%.1f", key="ltg_ikmax")
            Ik_min = st.number_input("Ik min am Leitungsende [kA]", 0.0, value=0.0, step=0.1, format="%.2f", key="ltg_ikmin",
                                     help="Minimaler Kurzschlussstrom (DIN EN 60909-0). 0 = nicht vorhanden.")

    dev_key = KL.LEITGERAET_KEY[leitgeraet]

    # ── Erweiterte Parameter ──────────────────────────────────────────────────
    with _section("Erweiterte Parameter (Voreinstellungen nach SIPROTEC 7SA6 / 7SD5 — frei änderbar)", expanded=False):
        st.caption("ℹ️ Adressen beziehen sich auf das gewählte Leitgerät "
                   f"(aktuell: **{leitgeraet}**). Anlagendaten sind in beiden Geräten adressgleich, "
                   "die Distanzzonen divergieren (7SA6 13xx / 7SD5 16xx).")
        e1, e2, e3 = st.columns(3)
        with e1:
            st.markdown("**Distanzschutz — Charakteristik**")
            DIS_charakt = st.selectbox("Auslösecharakteristik", KL.DIS_CHARAKT_OPTIONEN, index=0, key="ltg_charakt")
            _hreg("DIS_charakt")
            DIS_anr = st.selectbox("Anregeverfahren", KL.DIS_ANR_OPTIONEN, index=0, key="ltg_anr")
            _hreg("DIS_anr")
            alpha_polyg = st.number_input("ALPHA POLYG (Z1-Neigung) [°]", 0, 45, value=KL.alpha_polyg_def, step=1, key="ltg_alpha")
            _hreg("alpha_polyg")
            st.markdown("**Reichweitenfaktoren (× X_Ltg)**")
            f_Z1  = st.slider("f_Z1 (Unterreichweite)", 0.50, 1.00, value=KL.f_Z1_def, step=0.01, key="ltg_fz1")
            _hreg("f_Z1")
            f_Z1B = st.slider("f_Z1B (Übergreifzone)", 1.00, 2.00, value=KL.f_Z1B_def, step=0.05, key="ltg_fz1b")
            _hreg("f_Z1B")
            f_Z2  = st.slider("f_Z2 (Übergreifzone)", 1.00, 2.50, value=KL.f_Z2_def, step=0.05, key="ltg_fz2")
            _hreg("f_Z2")
            f_Z3  = st.slider("f_Z3 (Vorwärts-Reserve)", 1.00, 3.00, value=KL.f_Z3_def, step=0.05, key="ltg_fz3")
            _hreg("f_Z3")
        with e2:
            st.markdown("**R/X-Faktoren je Zone**")
            RX_Z1  = st.slider("R/X Z1", 0.2, 2.0, value=KL.RX_Z1_def, step=0.1, key="ltg_rxz1")
            _hreg("RX_Z1")
            RX_Z1B = st.slider("R/X Z1B", 0.2, 3.0, value=KL.RX_Z1B_def, step=0.1, key="ltg_rxz1b")
            _hreg("RX_Z1B")
            RX_Z2  = st.slider("R/X Z2", 0.2, 3.0, value=KL.RX_Z2_def, step=0.1, key="ltg_rxz2")
            _hreg("RX_Z2")
            RX_Z3  = st.slider("R/X Z3", 0.2, 4.0, value=KL.RX_Z3_def, step=0.1, key="ltg_rxz3")
            _hreg("RX_Z3")
            st.markdown("**Staffelzeiten [s]**")
            t_Z1  = st.number_input("T1 (Z1)",  0.00, 10.0, value=KL.t_Z1_def,  step=0.05, format="%.2f", key="ltg_tz1")
            _hreg("t_Z1")
            t_Z1B = st.number_input("T1B (Z1B)", 0.00, 10.0, value=KL.t_Z1B_def, step=0.05, format="%.2f", key="ltg_tz1b")
            _hreg("t_Z1B")
            t_Z2  = st.number_input("T2 (Z2)",  0.00, 10.0, value=KL.t_Z2_def,  step=0.05, format="%.2f", key="ltg_tz2")
            _hreg("t_Z2")
            t_Z3  = st.number_input("T3 (Z3)",  0.00, 10.0, value=KL.t_Z3_def,  step=0.05, format="%.2f", key="ltg_tz3")
            _hreg("t_Z3")
        with e3:
            st.markdown("**Erdimpedanzanpassung**")
            erdimp_format = st.selectbox("Format (Adr.237)", KL.ERDIMP_FORMAT_OPTIONEN, index=0, key="ltg_efmt")
            if erdimp_format == KL.ERDIMP_FORMAT_OPTIONEN[0]:
                RE_RL = st.number_input("RE/RL (Z1)", 0.0, 10.0, value=KL.RE_RL_def, step=0.05, format="%.2f", key="ltg_rerl")
                XE_XL = st.number_input("XE/XL (Z1)", 0.0, 10.0, value=KL.XE_XL_def, step=0.05, format="%.2f", key="ltg_xexl")
                K0, PHI_K0 = KL.K0_def, KL.PHI_K0_def
            else:
                K0 = st.number_input("K0 (Z1) Betrag", 0.0, 5.0, value=KL.K0_def, step=0.05, format="%.2f", key="ltg_k0")
                PHI_K0 = st.number_input("PHI K0 (Z1) [°]", -180, 180, value=KL.PHI_K0_def, step=1, key="ltg_phik0")
                RE_RL, XE_XL = KL.RE_RL_def, KL.XE_XL_def
            _hreg("RE_RL")
            st.markdown("**Leitungswinkel-Hinweis**")
            _hreg("phi_Ltg")

        st.divider()
        st.markdown("**Reservezonen Z4 / Z5 / Z6 (richtungswählbar)**")
        _hreg("reserve_zonen")
        z4c, z5c, z6c = st.columns(3)
        with z4c:
            st.caption("**Z4** (Adr.1331/1631)")
            modus_Z4 = st.selectbox("MODUS Z4", KL.ZONE_MODUS_OPTIONEN, index=1, key="ltg_mz4")
            _pin(KL.ADR_get("MODUS_Z4", leitgeraet))
            f_Z4  = st.slider("f_Z4 (× X_Ltg)", 0.2, 4.0, value=KL.f_Z4_def, step=0.05, key="ltg_fz4")
            _pin(KL.ADR_get("X_Z4", leitgeraet))
            RX_Z4 = st.slider("R/X Z4", 0.2, 5.0, value=KL.RX_Z4_def, step=0.1, key="ltg_rxz4")
            _pin(KL.ADR_get("R_Z4", leitgeraet))
            t_Z4  = st.number_input("T4 [s]", 0.00, 30.0, value=KL.t_Z4_def, step=0.05, format="%.2f", key="ltg_tz4")
            _pin(KL.ADR_get("T4", leitgeraet))
        with z5c:
            st.caption("**Z5** (Adr.1341/1641, ±)")
            modus_Z5 = st.selectbox("MODUS Z5", KL.ZONE_MODUS_OPTIONEN, index=2, key="ltg_mz5")
            _pin(KL.ADR_get("MODUS_Z5", leitgeraet))
            f_Z5  = st.slider("f_Z5 (× X_Ltg)", 0.2, 4.0, value=KL.f_Z5_def, step=0.05, key="ltg_fz5")
            _pin(KL.ADR_get("X_Z5_VOR", leitgeraet))
            RX_Z5 = st.slider("R/X Z5", 0.2, 5.0, value=KL.RX_Z5_def, step=0.1, key="ltg_rxz5")
            _pin(KL.ADR_get("R_Z5", leitgeraet))
            t_Z5  = st.number_input("T5 [s]", 0.00, 30.0, value=KL.t_Z5_def, step=0.05, format="%.2f", key="ltg_tz5")
            _pin(KL.ADR_get("T5", leitgeraet))
        with z6c:
            st.caption("**Z6** (Adr.1361/1661, ±)")
            modus_Z6 = st.selectbox("MODUS Z6", KL.ZONE_MODUS_OPTIONEN, index=0, key="ltg_mz6")
            _pin(KL.ADR_get("MODUS_Z6", leitgeraet))
            f_Z6  = st.slider("f_Z6 (× X_Ltg)", 0.2, 4.0, value=KL.f_Z6_def, step=0.05, key="ltg_fz6")
            _pin(KL.ADR_get("X_Z6_VOR", leitgeraet))
            RX_Z6 = st.slider("R/X Z6", 0.2, 5.0, value=KL.RX_Z6_def, step=0.1, key="ltg_rxz6")
            _pin(KL.ADR_get("R_Z6", leitgeraet))
            t_Z6  = st.number_input("T6 [s]", 0.00, 30.0, value=KL.t_Z6_def, step=0.05, format="%.2f", key="ltg_tz6")
            _pin(KL.ADR_get("T6", leitgeraet))

    # ══ Erweiterte Parameter — Gruppe: Hauptschutz-Ergänzung (87L · 85) ══
    # Defaults 87L (immer gesetzt; Eingaben nur bei Leitgerät 7SD5)
    i_diff = KL.i_diff_def; i_diff_hh = KL.i_diff_hh_def; i_diff_zusch = KL.i_diff_zusch_def
    i_freig_diff = KL.i_freig_diff_def; i_diff_hh_zusch = KL.i_diff_hh_zusch_def
    t_i_diff = KL.t_i_diff_def; ic_komp = KL.ic_komp_def; icstab_icn = KL.icstab_icn_def
    anzahl_geraete = KL.anzahl_geraete_def; ws_verbindung = KL.ws_verbindung_def
    with _section("Erweiterte Parameter — Hauptschutz-Ergänzung: Differentialschutz 87L (7SD5) · Teleschutz 85", expanded=False):
        if dev_key == "7SD5":
            _grphead("87L Leitungsdifferentialschutz (Hauptschutz 7SD5)")
            st.caption("Ansprechwerte als Vielfaches des Leitungs-Nennstroms IN_Ltg.")
            d1, d2, d3 = st.columns(3)
            with d1:
                st.markdown("**Stabilisierte Stufe I-DIFF>**")
                i_diff = st.slider("I-DIFF> (× IN_Ltg)", 0.10, 2.00, value=KL.i_diff_def, step=0.05, key="ltg_idiff")
                _hreg("i_diff")
                i_diff_zusch = st.slider("I-DIF> ZUSCH. (× IN)", 0.10, 2.00, value=KL.i_diff_zusch_def, step=0.05, key="ltg_idz")
                _hreg("i_diff_zusch")
                t_i_diff = st.number_input("T-I-DIF> [s]", 0.00, 10.0, value=KL.t_i_diff_def, step=0.05, format="%.2f", key="ltg_tidiff")
                _hreg("t_i_diff")
                i_freig_diff = st.slider("I> FREIG. DIFF (× IN)", 0.05, 1.00, value=KL.i_freig_diff_def, step=0.05, key="ltg_ifreig")
                _hreg("i_freig_diff")
            with d2:
                st.markdown("**Hochstromstufe I-DIFF>>**")
                i_diff_hh = st.slider("I-DIFF>> (× IN_Ltg)", 2.0, 15.0, value=KL.i_diff_hh_def, step=0.5, key="ltg_idiffhh")
                _hreg("i_diff_hh")
                i_diff_hh_zusch = st.slider("I-DIF>> ZUSCH. (× IN)", 2.0, 15.0, value=KL.i_diff_hh_zusch_def, step=0.5, key="ltg_idhhz")
                _hreg("i_diff_hh_zusch")
                st.markdown("**Ladestrom**")
                ic_komp = st.selectbox("Ladestromkompensation", KL.IC_KOMP_OPTIONEN, index=0, key="ltg_ickomp")
                _hreg("ic_komp")
                icstab_icn = st.slider("IcSTAB/IcN (× IcN)", 1.0, 3.0, value=KL.icstab_icn_def, step=0.1, key="ltg_icstab")
                _hreg("icstab_icn")
            with d3:
                st.markdown("**Schutzdatentopologie**")
                anzahl_geraete = st.selectbox("ANZAHL GERAETE", KL.ANZAHL_GERAETE_OPTIONEN, index=0, key="ltg_anzg")
                _hreg("anzahl_geraete")
                ws_verbindung = st.selectbox("WS1 Verbindung", KL.WS_VERBINDUNG_OPTIONEN, index=0, key="ltg_wsverb")
                _hreg("ws_verbindung")
        else:
            st.caption('Der Leitungsdifferentialschutz 87L ist nur bei Leitgerät '
                       '"Leitungsdifferential 7SD5" verfügbar. '
                       'Aktuell ist "Distanzschutz 7SA6" gewählt.')

        _grphead("85 Signalübertragungsverfahren Distanzschutz (Teleschutz)")
        st.caption("Beschleunigt die Auslösung über die Übergreifzone Z1B. Adressen 7SA6/7SD5 identisch. "
                   "Voraussetzung ist ein Kommunikationskanal zum Gegenende.")
        s1, s2, s3 = st.columns(3)
        with s1:
            signalv = st.selectbox("Verfahren SIGNALZUSATZ", KL.SIGNALV_OPTIONEN, index=2, key="ltg_signalv")
            _hreg("signalv")
            anschluss = st.selectbox("ANSCHLUSS", KL.ANSCHLUSS_OPTIONEN, index=0, key="ltg_anschluss")
            _hreg("anschluss")
        with s2:
            t_sendverl = st.number_input("T SENDVERL. [s]", 0.00, 5.0, value=KL.t_sendverl_def, step=0.01, format="%.2f", key="ltg_tsend")
            _hreg("t_sendverl")
            tv_dis = st.number_input("TV Freigabe Z1B [s]", 0.00, 5.0, value=KL.tv_dis_def, step=0.01, format="%.2f", key="ltg_tvdis")
            _hreg("tv_dis")
        with s3:
            t_warte_rueckw = st.number_input("T WARTE RÜCKW. [s]", 0.00, 5.0, value=KL.t_warte_rueckw_def, step=0.01, format="%.2f", key="ltg_twarte")
            _hreg("t_warte_rueckw")
            t_transblock = st.number_input("T TRANSBLOCK [s]", 0.00, 5.0, value=KL.t_transblock_def, step=0.01, format="%.2f", key="ltg_ttrans")
            _hreg("t_transblock")

    # ══ Erweiterte Parameter — Gruppe: Erdkurzschluss 67N (geerdet) · Not-Überstrom 50/51 ══
    geerdet = stp in KL.NETZ_GEERDET
    modus_3I0HHH = KL.modus_3I0HHH_def; i_3I0HHH = KL.i_3I0HHH_def; t_3I0HHH = KL.t_3I0HHH_def
    modus_3I0HH  = KL.modus_3I0HH_def;  i_3I0HH  = KL.i_3I0HH_def;  t_3I0HH  = KL.t_3I0HH_def
    modus_3I0H   = KL.modus_3I0H_def;   i_3I0H   = KL.i_3I0H_def;   t_3I0H   = KL.t_3I0H_def
    i3i0_iph_stab = KL.i3i0_iph_stab_def; phi_komp = KL.phi_komp_def
    with _section("Erweiterte Parameter — Erdkurzschluss 67N (geerdetes Netz) · Not-Überstrom 50/51", expanded=False):
        if geerdet:
            _grphead("67N Gerichteter Erdkurzschlussschutz (geerdetes Netz)")
            st.caption("Drei unabhängige Erdstromstufen, Ansprechwerte als Vielfaches von IN_Ltg. "
                       "Adressen 7SA6/7SD5 identisch.")
            g1, g2, g3 = st.columns(3)
            with g1:
                st.markdown("**3I0>>> (Hochstromstufe)**")
                modus_3I0HHH = st.selectbox("MODUS 3I0>>>", KL.ZONE_MODUS_OPTIONEN, index=1, key="ltg_m3hhh")
                _pin("3110")
                i_3I0HHH = st.slider("3I0>>> (× IN)", 0.1, 5.0, value=KL.i_3I0HHH_def, step=0.1, key="ltg_i3hhh")
                _hreg("i_3I0HHH")
                t_3I0HHH = st.number_input("T 3I0>>> [s]", 0.00, 10.0, value=KL.t_3I0HHH_def, step=0.05, format="%.2f", key="ltg_t3hhh")
                _hreg("t_3I0HHH")
            with g2:
                st.markdown("**3I0>> (mittlere Stufe)**")
                modus_3I0HH = st.selectbox("MODUS 3I0>>", KL.ZONE_MODUS_OPTIONEN, index=1, key="ltg_m3hh")
                _pin("3120")
                i_3I0HH = st.slider("3I0>> (× IN)", 0.1, 3.0, value=KL.i_3I0HH_def, step=0.05, key="ltg_i3hh")
                _hreg("i_3I0HH")
                t_3I0HH = st.number_input("T 3I0>> [s]", 0.00, 10.0, value=KL.t_3I0HH_def, step=0.05, format="%.2f", key="ltg_t3hh")
                _hreg("t_3I0HH")
                st.markdown("**Richtung**")
                phi_komp = st.number_input("PHI KOMP [°]", 0, 90, value=KL.phi_komp_def, step=1, key="ltg_phikomp")
                _hreg("phi_komp")
            with g3:
                st.markdown("**3I0> (empfindliche Stufe)**")
                modus_3I0H = st.selectbox("MODUS 3I0>", KL.ZONE_MODUS_OPTIONEN, index=1, key="ltg_m3h")
                _pin("3130")
                i_3I0H = st.slider("3I0> (× IN)", 0.02, 1.0, value=KL.i_3I0H_def, step=0.01, key="ltg_i3h")
                _hreg("i_3I0H")
                t_3I0H = st.number_input("T 3I0> [s]", 0.00, 10.0, value=KL.t_3I0H_def, step=0.05, format="%.2f", key="ltg_t3h")
                _hreg("t_3I0H")
                i3i0_iph_stab = st.slider("3I0 IPH STAB (× Iph)", 0.0, 0.5, value=KL.i3i0_iph_stab_def, step=0.01, key="ltg_iphstab")
                _hreg("i3i0_iph_stab")
        else:
            st.caption("Der gerichtete Erdkurzschlussschutz 67N ist für geerdete Netze vorgesehen. Das aktuell "
                       "gewählte Netz ist isoliert oder kompensiert; dort wirkt die Erdschlusserfassung über "
                       "die Verlagerungsspannung.")

        _grphead("50/51 Not-Überstromzeitschutz (Reserveschutz)")
        st.caption("Reserveschutz bei Ausfall der Distanzmessung. Ansprechwerte × IN_Ltg. "
                   "Adressen 7SA6/7SD5 identisch.")
        o1, o2, o3 = st.columns(3)
        with o1:
            uebs_betriebsart = st.selectbox("Betriebsart", KL.UEBS_BETRIEBSART_OPTIONEN, index=2, key="ltg_ubart")
            _hreg("uebs_betriebsart")
        with o2:
            iph_hh = st.slider("Iph>> (× IN)", 0.5, 10.0, value=KL.iph_hh_def, step=0.1, key="ltg_iphhh")
            _hreg("iph_hh")
            t_iph_hh = st.number_input("T Iph>> [s]", 0.00, 10.0, value=KL.t_iph_hh_def, step=0.05, format="%.2f", key="ltg_tiphhh")
            _hreg("t_iph_hh")
        with o3:
            iph_h = st.slider("Iph> (× IN)", 0.5, 5.0, value=KL.iph_h_def, step=0.05, key="ltg_iphh")
            _hreg("iph_h")
            t_iph_h = st.number_input("T Iph> [s]", 0.00, 10.0, value=KL.t_iph_h_def, step=0.05, format="%.2f", key="ltg_tiphh")
            _hreg("t_iph_h")

    # ══ Erweiterte Parameter — Gruppe: Automatik & Schalter (79 · 50BF · 68/78) ══
    with _section("Erweiterte Parameter — Automatik & Schalter: Wiedereinschaltung 79 · Schalterversager 50BF · Pendelsperre 68/78", expanded=False):
        _grphead("79 Wiedereinschaltautomatik (AWE)")
        st.caption("Automatische Wiedereinschaltung nach transientem Fehler. Adressen 7SA6/7SD5 identisch.")
        w1, w2, w3 = st.columns(3)
        with w1:
            auto_we = st.selectbox("AUTO-WE", ["Ein", "Aus"], index=0, key="ltg_autowe")
            _pin("3401")
            awe_anzahl = st.selectbox("Anzahl Unterbrechungszyklen", KL.AWE_ANZAHL_OPTIONEN, index=0, key="ltg_aweanz")
            _hreg("awe_anzahl")
        with w2:
            we_tp_aus1pol = st.number_input("TP nach 1-pol. AUS [s]", 0.00, 10.0, value=KL.we_tp_aus1pol_def, step=0.05, format="%.2f", key="ltg_tp1")
            _hreg("we_tp_aus1pol")
            we_tp_aus3pol = st.number_input("TP nach 3-pol. AUS [s]", 0.00, 10.0, value=KL.we_tp_aus3pol_def, step=0.05, format="%.2f", key="ltg_tp3")
            _hreg("we_tp_aus3pol")
        with w3:
            t_sperrzeit = st.number_input("T SPERRZEIT [s]", 0.00, 60.0, value=KL.t_sperrzeit_def, step=0.1, format="%.2f", key="ltg_sperr")
            _hreg("t_sperrzeit")

        _grphead("50BF Schalterversagerschutz")
        st.caption("Überwacht das Ausschalten des Leistungsschalters und löst bei Versagen die umliegenden "
                   "Schalter aus. Adressen 7SA6/7SD5 identisch.")
        b1, b2, b3 = st.columns(3)
        with b1:
            schalterv = st.selectbox("SCHALTERV.", ["Ein", "Aus"], index=0, key="ltg_schaltv")
            _pin("3901")
            i_svs = st.slider("I> SVS (× IN)", 0.02, 1.0, value=KL.i_svs_def, step=0.01, key="ltg_isvs")
            _hreg("i_svs")
        with b2:
            i3i0_svs = st.slider("3I0> SVS (× IN)", 0.02, 1.0, value=KL.i3i0_svs_def, step=0.01, key="ltg_i3svs")
            _hreg("i3i0_svs")
            aus_1pol_svs = st.selectbox("AUS 1POL (T1)", KL.JN_OPTIONEN, index=1, key="ltg_aus1pol")
            _hreg("aus_1pol_svs")
        with b3:
            t1_1pol_svs = st.number_input("T1 1POL [s]", 0.00, 5.0, value=KL.t1_1pol_svs_def, step=0.01, format="%.2f", key="ltg_t11p")
            _hreg("t1_1pol_svs")
            t1_3pol_svs = st.number_input("T1 3POL [s]", 0.00, 5.0, value=KL.t1_3pol_svs_def, step=0.01, format="%.2f", key="ltg_t13p")
            _hreg("t1_3pol_svs")
            t2_svs = st.number_input("T2 [s]", 0.00, 5.0, value=KL.t2_svs_def, step=0.01, format="%.2f", key="ltg_t2svs")
            _hreg("t2_svs")

        _grphead("68/78 Pendelsperre / Pendelerfassung")
        st.caption("Erkennt Leistungspendelungen und blockiert den Distanzschutz. Adressen 7SA6/7SD5 identisch.")
        pp1, pp2 = st.columns(2)
        with pp1:
            pendelerfassung = st.selectbox("PENDELERFASSUNG", KL.PENDELERFASSUNG_OPTIONEN, index=0, key="ltg_penderf")
            _hreg("pendelerfassung")
        with pp2:
            pen_ausloes = st.selectbox("PEN-AUSLÖS Außertrittauslösung", KL.JN_OPTIONEN, index=0, key="ltg_penaus")
            _hreg("pen_ausloes")

    # ══ Erweiterte Parameter — Gruppe: Spannung 27/59 · Frequenz 81 · Überlast 49 ══
    with _section("Erweiterte Parameter — Spannung 27/59 · Frequenz 81 · Überlast 49", expanded=False):
        _grphead("27/59 Spannungsschutz (Über- und Unterspannung)")
        st.caption("Zweistufiger Über- und Unterspannungsschutz. Ansprechwerte × UN. Adressen 7SA6/7SD5 identisch.")
        u0, u1, u2 = st.columns(3)
        with u0:
            spannungsschutz = st.selectbox("Spannungsschutz", ["Ein", "Aus"], index=0, key="ltg_uschutz")
            _pin("137")
        with u1:
            st.markdown("**Überspannung**")
            uph_h = st.slider("Uph> (× UN)", 1.00, 1.50, value=KL.uph_h_def, step=0.01, key="ltg_uphh")
            _hreg("uph_h")
            t_uph_h = st.number_input("T Uph> [s]", 0.00, 30.0, value=KL.t_uph_h_def, step=0.1, format="%.2f", key="ltg_tuphh")
            _hreg("t_uph_h")
            uph_hh = st.slider("Uph>> (× UN)", 1.00, 1.60, value=KL.uph_hh_def, step=0.01, key="ltg_uphhh")
            _hreg("uph_hh")
            t_uph_hh = st.number_input("T Uph>> [s]", 0.00, 30.0, value=KL.t_uph_hh_def, step=0.1, format="%.2f", key="ltg_tuphhh")
            _hreg("t_uph_hh")
        with u2:
            st.markdown("**Unterspannung**")
            uph_l = st.slider("Uph< (× UN)", 0.30, 1.00, value=KL.uph_l_def, step=0.01, key="ltg_uphl")
            _hreg("uph_l")
            t_uph_l = st.number_input("T Uph< [s]", 0.00, 30.0, value=KL.t_uph_l_def, step=0.1, format="%.2f", key="ltg_tuphl")
            _hreg("t_uph_l")
            uph_ll = st.slider("Uph<< (× UN)", 0.20, 1.00, value=KL.uph_ll_def, step=0.01, key="ltg_uphll")
            _hreg("uph_ll")
            t_uph_ll = st.number_input("T Uph<< [s]", 0.00, 30.0, value=KL.t_uph_ll_def, step=0.1, format="%.2f", key="ltg_tuphll")
            _hreg("t_uph_ll")

        _grphead("81 Frequenzschutz (vier Stufen f1 … f4)")
        st.caption("Vier Frequenzstufen für Unter- und Überfrequenz. Die DIGSI-Adresse hängt von der "
                   "Nennfrequenz ab (50 Hz: 3602/3612/3622/3632 · 60 Hz: 3603/3613/3623/3633).")
        ff0, ff1, ff2 = st.columns(3)
        with ff0:
            frequenzschutz = st.selectbox("Frequenzschutz", ["Ein", "Aus"], index=0, key="ltg_fschutz")
            _pin("3601")
            f_netz = st.selectbox("Nennfrequenz fN [Hz]", [50, 60], index=0, key="ltg_fnetz")
            _hreg("f1")
        with ff1:
            f1 = st.number_input("f1 [Hz]", 45.0, 65.0, value=KL.f1_def, step=0.1, format="%.2f", key="ltg_f1")
            _pin("3602 / 3603")
            t_f1 = st.number_input("T f1 [s]", 0.00, 100.0, value=KL.t_f1_def, step=0.05, format="%.2f", key="ltg_tf1")
            _hreg("t_f")
            f2 = st.number_input("f2 [Hz]", 45.0, 65.0, value=KL.f2_def, step=0.1, format="%.2f", key="ltg_f2")
            _pin("3612 / 3613")
            t_f2 = st.number_input("T f2 [s]", 0.00, 100.0, value=KL.t_f2_def, step=0.05, format="%.2f", key="ltg_tf2")
            _hreg("t_f")
        with ff2:
            f3 = st.number_input("f3 [Hz]", 45.0, 65.0, value=KL.f3_def, step=0.1, format="%.2f", key="ltg_f3")
            _pin("3622 / 3623")
            t_f3 = st.number_input("T f3 [s]", 0.00, 100.0, value=KL.t_f3_def, step=0.05, format="%.2f", key="ltg_tf3")
            _hreg("t_f")
            f4 = st.number_input("f4 [Hz]", 45.0, 65.0, value=KL.f4_def, step=0.1, format="%.2f", key="ltg_f4")
            _pin("3632 / 3633")
            t_f4 = st.number_input("T f4 [s]", 0.00, 100.0, value=KL.t_f4_def, step=0.05, format="%.2f", key="ltg_tf4")
            _hreg("t_f")

        _grphead("49 Thermischer Überlastschutz")
        st.caption("Thermisches Abbild der Leitung. Zeitkonstante τ_th in MINUTEN (gerätespezifisch). "
                   "Adressen 7SA6/7SD5 identisch.")
        th0, th1, th2 = st.columns(3)
        with th0:
            ueberlastschutz = st.selectbox("Überlastschutz", ["Ein", "Aus"], index=0, key="ltg_uebl")
            _pin("4201")
            k_faktor = st.slider("K-FAKTOR", 1.00, 1.50, value=KL.k_faktor_def, step=0.01, key="ltg_kfak")
            _hreg("k_faktor")
        with th1:
            zeitkonstante = st.number_input("ZEITKONSTANTE τ_th [min]", 1, 600, value=KL.zeitkonstante_def, step=1, key="ltg_tauth")
            _hreg("zeitkonstante")
        with th2:
            theta_warn = st.number_input("Θ WARN [%]", 50, 100, value=KL.theta_warn_def, step=1, key="ltg_thwarn")
            _hreg("theta_warn")
            i_warn = st.slider("I WARN (× IN)", 0.5, 1.5, value=KL.i_warn_def, step=0.01, key="ltg_iwarn")
            _hreg("i_warn")

    # ── Parameter-Dict ─────────────────────────────────────────────────────────
    p = dict(
        UN_kV=UN, leitungsart=ltgart, L_km=L, X_Belag=Xbel, C_Belag=Cbel, phi_Ltg=phi, IN_Ltg=IN_Ltg,
        CT_Prim=CT_P, CT_Sek=CT_S, VT_Prim_kV=VT_P, VT_Sek_V=VT_S,
        leitgeraet=leitgeraet, sternpunkt_netz=stp, Ik_max_kA=Ik_max, Ik_min_kA=Ik_min,
        DIS_charakt=DIS_charakt, DIS_anr=DIS_anr, alpha_polyg=alpha_polyg,
        f_Z1=f_Z1, f_Z1B=f_Z1B, f_Z2=f_Z2, f_Z3=f_Z3,
        RX_Z1=RX_Z1, RX_Z1B=RX_Z1B, RX_Z2=RX_Z2, RX_Z3=RX_Z3,
        t_Z1=t_Z1, t_Z1B=t_Z1B, t_Z2=t_Z2, t_Z3=t_Z3,
        modus_Z4=modus_Z4, f_Z4=f_Z4, RX_Z4=RX_Z4, t_Z4=t_Z4,
        modus_Z5=modus_Z5, f_Z5=f_Z5, RX_Z5=RX_Z5, t_Z5=t_Z5,
        modus_Z6=modus_Z6, f_Z6=f_Z6, RX_Z6=RX_Z6, t_Z6=t_Z6,
        i_diff=i_diff, i_diff_hh=i_diff_hh, i_diff_zusch=i_diff_zusch,
        i_freig_diff=i_freig_diff, i_diff_hh_zusch=i_diff_hh_zusch, t_i_diff=t_i_diff,
        ic_komp=ic_komp, icstab_icn=icstab_icn, anzahl_geraete=anzahl_geraete,
        ws_verbindung=ws_verbindung,
        modus_3I0HHH=modus_3I0HHH, i_3I0HHH=i_3I0HHH, t_3I0HHH=t_3I0HHH,
        modus_3I0HH=modus_3I0HH, i_3I0HH=i_3I0HH, t_3I0HH=t_3I0HH,
        modus_3I0H=modus_3I0H, i_3I0H=i_3I0H, t_3I0H=t_3I0H,
        i3i0_iph_stab=i3i0_iph_stab, phi_komp=phi_komp,
        signalv=signalv, anschluss=anschluss, t_sendverl=t_sendverl, tv_dis=tv_dis,
        t_warte_rueckw=t_warte_rueckw, t_transblock=t_transblock,
        uebs_betriebsart=uebs_betriebsart, iph_hh=iph_hh, t_iph_hh=t_iph_hh,
        iph_h=iph_h, t_iph_h=t_iph_h,
        auto_we=auto_we, awe_anzahl=awe_anzahl, we_tp_aus1pol=we_tp_aus1pol,
        we_tp_aus3pol=we_tp_aus3pol, t_sperrzeit=t_sperrzeit,
        schalterv=schalterv, i_svs=i_svs, i3i0_svs=i3i0_svs, aus_1pol_svs=aus_1pol_svs,
        t1_1pol_svs=t1_1pol_svs, t1_3pol_svs=t1_3pol_svs, t2_svs=t2_svs,
        pendelerfassung=pendelerfassung, pen_ausloes=pen_ausloes,
        spannungsschutz=spannungsschutz, uph_h=uph_h, t_uph_h=t_uph_h, uph_hh=uph_hh, t_uph_hh=t_uph_hh,
        uph_l=uph_l, t_uph_l=t_uph_l, uph_ll=uph_ll, t_uph_ll=t_uph_ll,
        frequenzschutz=frequenzschutz, f_netz=f_netz, f1=f1, t_f1=t_f1, f2=f2, t_f2=t_f2,
        f3=f3, t_f3=t_f3, f4=f4, t_f4=t_f4,
        ueberlastschutz=ueberlastschutz, k_faktor=k_faktor, zeitkonstante=zeitkonstante,
        theta_warn=theta_warn, i_warn=i_warn,
        erdimp_format=erdimp_format, RE_RL=RE_RL, XE_XL=XE_XL, K0=K0, PHI_K0=PHI_K0,
    )
    r = berechne_alle(p)
    g, d21, d87, d67, d85 = r["grund"], r["21"], r["87L"], r["67N"], r["85"]
    d50, d79, dbf = r["50/51"], r["79"], r["50BF"]
    d68, d2759, d81, d49 = r["68/78"], r["27/59"], r["81"], r["49"]

    # ══════════════════════ PLAUSIBILITÄT — ZUSAMMENFASSUNG ══════════════════════
    plaus = r["plausibilitaet"]
    n_ok  = sum(1 for c in plaus if c["status"] == "OK")
    n_hin = sum(1 for c in plaus if c["status"] == "Hinweis")
    n_bad = sum(1 for c in plaus if c["status"] in ("Prüfen!", "Fehlt"))
    st.markdown(
        f'<div style="margin:0.6rem 0;">Plausibilität: '
        f'{_pill("OK", n_ok)} &nbsp; {_pill("Hinweis", n_hin)} &nbsp; '
        f'{_pill("Prüfen!", n_bad)}</div>', unsafe_allow_html=True)

    todo = [c for c in plaus if c["status"] in ("Prüfen!", "Fehlt") and c["korrektur"]]
    hinw = [c for c in plaus if c["status"] == "Hinweis" and c["korrektur"]]
    if todo:
        items = "".join(
            f'<li style="margin-bottom:6px;"><b>{c["pruefung"]}</b> (Ergebnis: {c["ergebnis"]})<br>'
            f'<span style="color:#7a0024;">➜ {c["korrektur"]}</span></li>' for c in todo)
        st.markdown(f'<div class="off-box"><b>🔴 Handlungsbedarf — konkret zu verstellen:</b>'
                    f'<ul style="margin:6px 0 0 0;padding-left:18px;">{items}</ul></div>',
                    unsafe_allow_html=True)
    if hinw:
        items = "".join(
            f'<li style="margin-bottom:6px;"><b>{c["pruefung"]}</b><br>'
            f'<span style="color:#8a5b00;">➜ {c["korrektur"]}</span></li>' for c in hinw)
        st.markdown(f'<div class="warn-box"><b>🟡 Hinweise (prüfen, ggf. anpassen):</b>'
                    f'<ul style="margin:6px 0 0 0;padding-left:18px;">{items}</ul></div>',
                    unsafe_allow_html=True)
    if not todo and not hinw:
        st.markdown('<div class="info-box">🟢 <b>Alle Plausibilitätsprüfungen bestanden.</b> '
                    'Die berechneten Werte sind konsistent und entsprechen der 7SA6-/7SD5-Methodik. '
                    'Bewusste Abweichungen bleiben dir überlassen.</div>', unsafe_allow_html=True)

    # ══════════════════════ GRUNDGRÖSSEN ══════════════════════
    with _section("Berechnete Grundgrößen"):
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            _metric("Leitungsreaktanz X_Ltg", f"{g['X_Ltg']:.3f} Ω", f"X′ · L = {Xbel:g} · {L:g}")
        with m2:
            _metric("Leitungsresistanz R_Ltg", f"{g['R_Ltg']:.3f} Ω", f"X_Ltg / tan({phi}°)")
        with m3:
            _metric("Schleifenimpedanz Z_Ltg", f"{g['Z_Ltg']:.3f} Ω", "√(R² + X²) primär")
        with m4:
            _metric("Z_Ltg sekundär", f"{g['Z_Ltg_sek']:.3f} Ω", f"× k_Z = {g['k_Z']:.4f}")
        m5, m6, m7, m8 = st.columns(4)
        with m5:
            _metric("Wandlerverhältnis kCT", f"{g['kCT']:.2f}", f"{CT_P}/{CT_S} A")
        with m6:
            _metric("Wandlerverhältnis nVT", f"{g['nVT']:.2f}", f"{VT_P} kV / {VT_S} V")
        with m7:
            _metric("Sekundärfaktor k_Z", f"{g['k_Z']:.4f}", "Z_sek / Z_prim = kCT / nVT")
        with m8:
            _metric("STW-Anpassung I_an", f"{g['I_an']:.2f}" if g["I_an"] else "—", "CT_sek / IN_Ltg_sek")
        m9, m10, m11, m12 = st.columns(4)
        with m9:
            _metric("Leitungs-Nennstrom IN_Ltg", f"{g['IN_Ltg']:.1f} A",
                    "Bezugsgröße für 87L · 67N · 50/51 · 49")
        with m10:
            _metric("IN_Ltg sekundär", f"{g['IN_Ltg_sek']:.3f} A",
                    f"IN_Ltg / kCT = {g['IN_Ltg']:.1f} / {g['kCT']:.2f}")
        with m11:
            _metric("Nennladestrom IcN", f"{g['IcN']:.3f} A",
                    "U/√3 · 2πf · C′·L  (Mindestbezug 87L)")
        with m12:
            _metric("X_Ltg sekundär", f"{g['X_Ltg_sek']:.3f} Ω",
                    f"X_Ltg × k_Z")

    # ══════════════════════ DISTANZSCHUTZ 21 ══════════════════════
    with _section(f"Distanzschutz 21 — Zonen ({leitgeraet})"):
        st.caption(f"Charakteristik **{d21['charakt']}** · Anregeverfahren **{d21['anr']}** · "
                   f"ALPHA POLYG **{d21['alpha_polyg']}°** · Erdimpedanzanpassung **{d21['erdimp_format']}**")

        adr = d21["adr"]
        zr = []
        # Hauptzonen (vorwaerts gerichtet)
        for nm, z, ax, ar, are, at in (
            ("Z1 (Unterreichweite)",    d21["Z1"],  adr["X_Z1"],  adr["R_Z1"],  adr["RE_Z1"],  adr["T1"]),
            ("Z1B (Übergreifzone)",     d21["Z1B"], adr["X_Z1B"], adr["R_Z1B"], adr["RE_Z1B"], adr["T1B"]),
            ("Z2 (Übergreif, Staffel)", d21["Z2"],  adr["X_Z2"],  adr["R_Z2"],  adr["RE_Z2"],  adr["T2"]),
            ("Z3 (Vorwärts-Reserve)",   d21["Z3"],  adr["X_Z3"],  adr["R_Z3"],  adr["RE_Z3"],  adr["T3"]),
        ):
            zr.append((
                nm, "Vorwärts",
                f"{z['faktor']*100:.0f} %",
                f"{z['X_prim']:.3f}", f"{z['X_sek']:.3f}",
                f"{z['R_sek']:.3f}", f"{z['RE_sek']:.3f}",
                f"{z['t']:.2f}",
                f"X(sek.)→{ax} | R(sek.)→{ar} | RE(sek.)→{are} | T→{at}",
            ))
        # Reservezonen Z4/Z5/Z6 (richtungswaehlbar, ggf. unwirksam)
        for nm, z in (("Z4 (Reserve)", d21["Z4"]), ("Z5 (Reserve)", d21["Z5"]),
                      ("Z6 (Reserve)", d21["Z6"])):
            if z["aktiv"]:
                zr.append((
                    nm, z["modus"],
                    f"{z['faktor']*100:.0f} %",
                    f"{z['X_prim']:.3f}", f"{z['X_sek']:.3f}",
                    f"{z['R_sek']:.3f}", f"{z['RE_sek']:.3f}",
                    f"{z['t']:.2f}",
                    f"X(sek.)→{z['x_adr']} | R(sek.)→{z['r_adr']} | RE(sek.)→{z['re_adr']} | T→{z['t_adr']}",
                ))
            else:
                zr.append((nm, "Unwirksam", "—", "—", "—", "—", "—", "—",
                           f"MODUS {z['modus_adr']}"))
        dfz = pd.DataFrame(zr, columns=[
            "Zone", "Richtung", "Reichw.", "X prim. [Ω]", "X sek. [Ω]", "R sek. [Ω]",
            "RE sek. [Ω]", "t [s]", "DIGSI-Adressen (sek.-Wert → Adresse)"])
        st.dataframe(dfz, width="stretch", hide_index=True)
        st.caption("Primäre Reichweite X(Zk) = f_Zk · X_Ltg; sekundär × k_Z. "
                   "R(Zk) = R/X-Faktor · X(Zk), RE(Zk) = 1,5 · R(Zk). "
                   "Adressspalte: X(sek.) → X-Adresse | R(sek.) → R-Adresse | "
                   "RE(sek.) → RE-Adresse | T → Zeitadresse. "
                   "Z5/Z6 nutzen je nach Richtung die Vorwärts- (+) oder Rückwärts-Adresse (−). "
                   "Adressen gelten für das gewählte Leitgerät.")

    # ══════════════════════ 87L LEITUNGSDIFFERENTIALSCHUTZ (nur 7SD5) ══════════════════════
    if d87["verfuegbar"]:
        with _section("Leitungsdifferentialschutz 87L (Hauptschutz 7SD5)"):
            a87 = d87["adr"]
            st.caption(f"Ladestromkompensation **{d87['ic_komp']}** · "
                       f"IcSTAB/IcN **{d87['icstab_icn']:.1f}** · Schutzdatentopologie "
                       f"**{d87['anzahl_geraete']} Geräte** · WS1 **{d87['ws_verbindung']}**")
            n1, n2, n3 = st.columns(3)
            with n1:
                _metric("Nennladestrom IcN", f"{d87['IcN']:.2f} A", "U/√3 · 2πf · C′·L")
            with n2:
                _metric("Mindest-Ansprechwert", f"{d87['i_diff_min']:.1f} A", "2,5 · IcN (Siemens-Empf.)")
            with n3:
                _metric("Auslöseverzögerung T-I-DIF>", f"{d87['t_i_diff']:.2f} s", f"Adr.{a87['T_I_DIF']}")
            sr = [
                ("I-DIFF> (stabilisiert)", f"{d87['i_diff']:.2f} × IN",
                 f"{d87['i_diff_prim']:.1f}", f"{d87['i_diff_sek']:.3f}",
                 f"I(sek.)→{a87['I_DIFF']} | T→{a87['T_I_DIF']}"),
                ("I-DIF> ZUSCH.", f"{d87['i_diff_zusch']:.2f} × IN",
                 f"{d87['i_diff_zusch_prim']:.1f}", "—",
                 f"I(sek.)→{a87['I_DIF_ZUSCH']}"),
                ("I-DIFF>> (unstabilisiert)", f"{d87['i_diff_hh']:.2f} × IN",
                 f"{d87['i_diff_hh_prim']:.1f}", f"{d87['i_diff_hh_sek']:.3f}",
                 f"I(sek.)→{a87['I_DIFF_HH']}"),
            ]
            dfd = pd.DataFrame(sr, columns=["Stufe", "Ansprechwert", "I prim. [A]", "I sek. [A]", "DIGSI-Adressen (Wert → Adresse)"])
            st.dataframe(dfd, width="stretch", hide_index=True)
            st.caption("87L ist der schnelle Hauptschutz der 7SD5. Die stabilisierte Stufe I-DIFF> "
                       "muss oberhalb des kapazitiven Ladestroms liegen, die unstabilisierte Stufe "
                       "I-DIFF>> löst bei schweren inneren Fehlern unverzögert aus. Die Geräte an den "
                       "Leitungsenden tauschen die Messgrößen über die Wirkschnittstelle aus "
                       "(Adr.4501/4502, Topologie Adr.147).")

    # ══════════════════════ 67N GERICHTETER ERDKURZSCHLUSSSCHUTZ ══════════════════════
    with _section("Gerichteter Erdkurzschlussschutz 67N"):
        a67 = d67["adr"]
        if not d67["geerdet"]:
            st.markdown(
                f'<div class="warn-box">Sternpunktbehandlung <b>{d67["sternpunkt"]}</b>: '
                'Der strombasierte 67N ist für geerdete Netze vorgesehen. In isolierten oder '
                'kompensierten Netzen erfolgt die Erdschlusserfassung über die '
                'Verlagerungsspannung U0 bzw. wattmetrisch. Die Stufen werden hier nur '
                'informativ angezeigt.</div>',
                unsafe_allow_html=True)
        else:
            st.caption(f"Netz **{d67['sternpunkt']}** · Richtungswinkel PHI KOMP "
                       f"**{d67['phi_komp']}°** · Stabilisierung 3I0 IPH STAB "
                       f"**{d67['iph_stab']*100:.0f} %**")
        er = []
        for nm, s, ai, at, am in (
            ("3I0>>> (Hochstrom)", d67["3I0HHH"], a67["I_HHH"], a67["T_HHH"], a67["M_HHH"]),
            ("3I0>> (mittel)",     d67["3I0HH"],  a67["I_HH"],  a67["T_HH"],  a67["M_HH"]),
            ("3I0> (empfindlich)", d67["3I0H"],   a67["I_H"],   a67["T_H"],   a67["M_H"]),
        ):
            er.append((
                nm,
                s["modus"],
                f"{s['faktor']:.2f} × IN",
                f"{s['i_prim']:.1f}",
                f"{s['i_sek']:.3f}",
                f"{s['t']:.2f}",
                f"I(sek.)→{ai} | T→{at} | MODUS→{am}",
            ))
        dfe = pd.DataFrame(er, columns=[
            "Stufe", "Richtung", "Ansprechwert", "I prim. [A]", "I sek. [A]", "t [s]", "DIGSI-Adressen (Wert → Adresse)"])
        st.dataframe(dfe, width="stretch", hide_index=True)
        st.caption("Erdstrom 3I0 als Vielfaches von IN_Ltg, primär und sekundär. Jede Stufe ist "
                   "über MODUS (Adr.3110/3120/3130) richtungswählbar. Der Richtungswinkel PHI KOMP "
                   "(Adr.3168) legt die Symmetrieachse der Richtungskennlinie fest. "
                   "Adressen sind in 7SA6 und 7SD5 identisch.")

    # ══════════════════════ 85 TELESCHUTZ / SIGNALVERGLEICH ══════════════════════
    with _section("Signalübertragungsverfahren 85 (Teleschutz Distanzschutz)"):
        a85 = d85["adr"]
        if not d85["aktiv"]:
            st.markdown(
                '<div class="warn-box">SIGNALZUSATZ = <b>Aus</b>: Kein Teleschutzverfahren aktiv. '
                'Der Distanzschutz arbeitet rein zeitgestaffelt ohne Beschleunigung der Z1B.</div>',
                unsafe_allow_html=True)
        else:
            st.caption(f"Verfahren **{d85['verfahren']}** · Anschluss **{d85['anschluss']}** · "
                       f"beschleunigt die **Übergreifzone Z1B** "
                       f"({'Blockierverfahren' if d85['blockierverfahren'] else 'Freigabeverfahren'})")
        sr = [
            ("Verfahren", d85["verfahren"], "—", f"Adr.{a85['SIGNALZUSATZ']}"),
            ("Anschluss (Gegenenden)", d85["anschluss"], "—", f"Adr.{a85['ANSCHLUSS']}"),
            ("T SENDVERL. (Sendeverlängerung)", f"{d85['t_sendverl']:.2f}", "s", f"Adr.{a85['T_SENDVERL']}"),
            ("TV (Freigabeverzögerung Z1B)", f"{d85['tv']:.2f}", "s", f"Adr.{a85['TV']}"),
            ("T WARTE RÜCKW.", f"{d85['t_warte_rueckw']:.2f}", "s", f"Adr.{a85['T_WARTE_RUECKW']}"),
            ("T TRANSBLOCK", f"{d85['t_transblock']:.2f}", "s", f"Adr.{a85['T_TRANSBLOCK']}"),
        ]
        dfs = pd.DataFrame(sr, columns=["Parameter", "Wert", "Einheit", "DIGSI-Adr."])
        st.dataframe(dfs, width="stretch", hide_index=True)
        st.caption("Die Freigabeverfahren (Mitnahme, Signalvergleich, Unblocking) senden bei "
                   "Vorwärtsfehler ein Freigabesignal und lösen Z1B bei Empfang sofort aus. Das "
                   "Blocking-Verfahren sendet bei Rückwärtsfehler ein Blockiersignal und benötigt "
                   "dafür eine schnelle Rückwärtsstufe. Voraussetzung ist in beiden Fällen, dass "
                   "Z1 und Z1B vorwärts gerichtet sind.")

    # ══════════════════════ 50/51 NOT-ÜBERSTROM ══════════════════════
    with _section("Not-Überstromzeitschutz 50/51 (Reserve)"):
        a50 = d50["adr"]
        if not d50["aktiv"]:
            st.markdown('<div class="warn-box">Betriebsart = <b>Aus</b>: Reserve-Überstromschutz '
                        'nicht aktiv.</div>', unsafe_allow_html=True)
        else:
            st.caption(f"Betriebsart **{d50['betriebsart']}**")
        r50 = [
            ("Iph>> (Hochstrom)", f"{d50['IphHH']['faktor']:.2f} × IN", f"{d50['IphHH']['i_prim']:.1f}",
             f"{d50['IphHH']['i_sek']:.3f}", f"{d50['IphHH']['t']:.2f}",
             f"I(sek.)→{a50['IPH_HH']} | T→{a50['T_IPH_HH']}"),
            ("Iph> (Grundstufe)", f"{d50['IphH']['faktor']:.2f} × IN", f"{d50['IphH']['i_prim']:.1f}",
             f"{d50['IphH']['i_sek']:.3f}", f"{d50['IphH']['t']:.2f}",
             f"I(sek.)→{a50['IPH_H']} | T→{a50['T_IPH_H']}"),
        ]
        df50 = pd.DataFrame(r50, columns=["Stufe", "Ansprechwert", "I prim. [A]", "I sek. [A]", "t [s]", "DIGSI-Adressen (Wert → Adresse)"])
        st.dataframe(df50, width="stretch", hide_index=True)
        st.caption("Üblich ist die Betriebsart 'bei U-Ausfall': der Überstromschutz übernimmt nur, "
                   "wenn der Distanzschutz wegen Messspannungsausfall nicht messen kann.")

    # ══════════════════════ 79 AWE ══════════════════════
    with _section("Wiedereinschaltautomatik 79 (AWE)"):
        a79 = d79["adr"]
        if not d79["aktiv"]:
            st.markdown('<div class="warn-box">AUTO-WE = <b>Aus</b>: Keine automatische '
                        'Wiedereinschaltung.</div>', unsafe_allow_html=True)
        else:
            st.caption(f"AUTO-WE **Ein** · **{d79['anzahl']}** Unterbrechungszyklus/-zyklen")
        r79 = [
            ("Pausenzeit nach 1-pol. AUS", f"{d79['tp_1pol']:.2f}", "s", f"Adr.{a79['TP_1POL']}"),
            ("Pausenzeit nach 3-pol. AUS", f"{d79['tp_3pol']:.2f}", "s", f"Adr.{a79['TP_3POL']}"),
            ("Sperrzeit (Reclaim)", f"{d79['sperrzeit']:.2f}", "s", f"Adr.{a79['SPERRZEIT']}"),
        ]
        df79 = pd.DataFrame(r79, columns=["Parameter", "Wert", "Einheit", "DIGSI-Adr."])
        st.dataframe(df79, width="stretch", hide_index=True)
        st.caption("Die 1-polige Pausenzeit muss lang genug für das Verlöschen des "
                   "Sekundärlichtbogens sein, die 3-polige Pausenzeit richtet sich nach der "
                   "Netzstabilität.")

    # ══════════════════════ 50BF SCHALTERVERSAGER ══════════════════════
    with _section("Schalterversagerschutz 50BF"):
        abf = dbf["adr"]
        if not dbf["aktiv"]:
            st.markdown('<div class="warn-box">SCHALTERV. = <b>Aus</b>: Schalterversagerschutz '
                        'nicht aktiv.</div>', unsafe_allow_html=True)
        else:
            st.caption(f"SCHALTERV. **Ein** · 1-poliges AUS (T1) **{dbf['aus_1pol']}**")
        n1, n2, n3 = st.columns(3)
        with n1:
            _metric("I> SVS (Stromflussüberw.)", f"{dbf['i_svs_prim']:.1f} A",
                    f"{dbf['i_svs']:.2f} × IN · Adr.{abf['I_SVS']}")
        with n2:
            _metric("T1 (eigener Schalter)", f"{dbf['t1_3pol']:.2f} s", f"Adr.{abf['T1_3POL']}")
        with n3:
            _metric("T2 (umliegende Schalter)", f"{dbf['t2']:.2f} s", f"Adr.{abf['T2']}")
        st.caption("Stufe 1 (T1) gibt ein Wiederholungskommando an den eigenen Schalter, Stufe 2 "
                   "(T2) schaltet bei echtem Versagen die umliegenden Leistungsschalter "
                   "(Sammelschiene) ab. T2 muss größer als T1 sein.")

    # ══════════════════════ 68/78 PENDELSPERRE ══════════════════════
    with _section("Pendelsperre / Pendelerfassung 68/78"):
        a68 = d68["adr"]
        if not d68["aktiv"]:
            st.markdown('<div class="warn-box">PENDELERFASSUNG = <b>Nicht vorhanden</b>: Keine '
                        'Pendelerfassung projektiert.</div>', unsafe_allow_html=True)
        else:
            modus = "Außertrittauslösung aktiv" if d68["pen_ausloes"] == "Ja" else "nur Pendelsperre (Blockierung)"
            st.caption(f"Pendelerfassung **vorhanden** · **{modus}** · PEN-AUSLÖS Adr.{a68['PEN_AUSLOES']}")
        st.caption("Die Pendelerfassung misst die Änderungsgeschwindigkeit der Impedanz (dZ/dt) "
                   "und blockiert den Distanzschutz bei stabilen Leistungspendelungen, damit "
                   "diese nicht als Kurzschluss fehlinterpretiert werden. Bei instabiler Pendelung "
                   "kann optional gezielt ausgelöst werden (Funktionsumfang Adr.120).")

    # ══════════════════════ 27/59 SPANNUNGSSCHUTZ ══════════════════════
    with _section("Spannungsschutz 27/59 (Über- und Unterspannung)"):
        a27 = d2759["adr"]
        if not d2759["aktiv"]:
            st.markdown('<div class="warn-box">Spannungsschutz = <b>Aus</b>.</div>', unsafe_allow_html=True)
        r27 = [
            ("Uph>> (Überspannung)", f"{d2759['UphHH']['faktor']:.2f} × UN", f"{d2759['UphHH']['u_sek']:.1f}",
             f"{d2759['UphHH']['t']:.2f}", f"U(sek.)→{a27['UPH_HH']} | T→{a27['T_UPH_HH']}"),
            ("Uph> (Überspannung)", f"{d2759['UphH']['faktor']:.2f} × UN", f"{d2759['UphH']['u_sek']:.1f}",
             f"{d2759['UphH']['t']:.2f}", f"U(sek.)→{a27['UPH_H']} | T→{a27['T_UPH_H']}"),
            ("Uph< (Unterspannung)", f"{d2759['UphL']['faktor']:.2f} × UN", f"{d2759['UphL']['u_sek']:.1f}",
             f"{d2759['UphL']['t']:.2f}", f"U(sek.)→{a27['UPH_L']} | T→{a27['T_UPH_L']}"),
            ("Uph<< (Unterspannung)", f"{d2759['UphLL']['faktor']:.2f} × UN", f"{d2759['UphLL']['u_sek']:.1f}",
             f"{d2759['UphLL']['t']:.2f}", f"U(sek.)→{a27['UPH_LL']} | T→{a27['T_UPH_LL']}"),
        ]
        df27 = pd.DataFrame(r27, columns=["Stufe", "Ansprechwert", "U sek. (L-E) [V]", "t [s]", "DIGSI-Adressen (Wert → Adresse)"])
        st.dataframe(df27, width="stretch", hide_index=True)
        st.caption("Ansprechwerte als Vielfaches der Bemessungsspannung. Der sekundäre Wert ist "
                   "die Leiter-Erde-Spannung (UN_sek/√3).")

    # ══════════════════════ 81 FREQUENZSCHUTZ ══════════════════════
    with _section("Frequenzschutz 81 (vier Stufen)"):
        if not d81["aktiv"]:
            st.markdown('<div class="warn-box">Frequenzschutz = <b>Aus</b>.</div>', unsafe_allow_html=True)
        else:
            st.caption(f"Nennfrequenz fN **{d81['fN']} Hz** · Adressen frequenzabhängig gewählt")
        r81 = []
        for nm in ("f1", "f2", "f3", "f4"):
            s = d81[nm]
            r81.append((nm, f"{s['f']:.2f} Hz", s["art"], f"{s['t']:.2f}",
                        f"f(Hz)→{s['adr_f']} | T→{s['adr_t']}"))
        df81 = pd.DataFrame(r81, columns=["Stufe", "Ansprechwert", "Art", "t [s]", "DIGSI-Adressen (Wert → Adresse)"])
        st.dataframe(df81, width="stretch", hide_index=True)
        st.caption("Bei fN = 50 Hz gelten die Adressen 3602/3612/3622/3632, bei 60 Hz die "
                   "Adressen 3603/3613/3623/3633. Die Art (Unter-/Überfrequenz) ergibt sich aus "
                   "dem Vergleich mit der Nennfrequenz.")

    # ══════════════════════ 49 ÜBERLASTSCHUTZ ══════════════════════
    with _section("Thermischer Überlastschutz 49"):
        a49 = d49["adr"]
        if not d49["aktiv"]:
            st.markdown('<div class="warn-box">Überlastschutz = <b>Aus</b>.</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            _metric("K-FAKTOR", f"{d49['k_faktor']:.2f}", f"I_dauer/IN · Adr.{a49['K_FAKTOR']}")
        with c2:
            _metric("Dauergrenzstrom k·IN", f"{d49['i_max_prim']:.0f} A", "thermischer Endwert")
        with c3:
            _metric("Zeitkonstante τ_th", f"{d49['zeitkonstante']} min", f"Adr.{a49['ZEITKONST']}")
        with c4:
            _metric("Θ WARN / I WARN", f"{d49['theta_warn']} % / {d49['i_warn']:.2f}×IN", f"Adr.{a49['THETA_WARN']}/{a49['I_WARN']}")
        st.caption("Das thermische Abbild bildet die Erwärmung der Leitung nach. Auslösung bei "
                   "100 % des Abbilds (k·IN dauerhaft). WICHTIG: Die Zeitkonstante ist bei 7SA6/7SD5 "
                   "in Minuten einzustellen, im Unterschied zu Sekunden bei anderen Gerätefamilien.")

    # ══════════════════════ PLAUSIBILITÄT ══════════════════════
    with _section("Plausibilitätsprüfung (Ampel)"):
        rows = []
        for c in r["plausibilitaet"]:
            rows.append((
                f'{_AMPEL_EMOJI.get(c["status"], "")} {c["status"]}',
                c["pruefung"], c["ergebnis"], c["hinweis"],
                c["korrektur"] or "—",
            ))
        dfp = pd.DataFrame(rows, columns=["Status", "Prüfung", "Ergebnis", "Hinweis", "Korrektur"])
        st.dataframe(dfp, width="stretch", hide_index=True)

    # ══════════════════════ GERÄTE-EMPFEHLUNG ══════════════════════
    with _section("Geräte- / Architektur-Empfehlung"):
        geh = r["empfehlung"]
        st.markdown(f'<div class="info-box"><b>Hauptschutzkonzept:</b> {geh["haupt"]}</div>',
                    unsafe_allow_html=True)
        if geh["hinweis"]:
            st.markdown(f'<div class="warn-box">{geh["hinweis"]}</div>', unsafe_allow_html=True)

    # ══════════════════════ SOLLWERT-TABELLE ══════════════════════
    with _section(f"📋  Herstellerneutrale Sollwert-Tabelle (DIGSI-Adressen {dev_key})"):
        adr = d21["adr"]

        # ── Tabelle 1: Distanzschutz 21 — Zonenimpedanzen (Zonenmatrix) ─────
        st.markdown("**Distanzschutz 21 — Zonenimpedanzen**")
        st.caption("Jede Zeile entspricht einer Zone. Alle Sekundärwerte sind direkt in DIGSI "
                   "einzutragen. X(Zk), R(Zk), RE(Zk) in Ω sek., T in Sekunden.")
        zonen_sw = []
        for znm, z, ax, ar, are_, at in (
            ("Z1  (Unterreichweite)",    d21["Z1"],  adr["X_Z1"],  adr["R_Z1"],  adr["RE_Z1"],  adr["T1"]),
            ("Z1B (Übergreifzone)",      d21["Z1B"], adr["X_Z1B"], adr["R_Z1B"], adr["RE_Z1B"], adr["T1B"]),
            ("Z2  (Staffel/Übergreif)",  d21["Z2"],  adr["X_Z2"],  adr["R_Z2"],  adr["RE_Z2"],  adr["T2"]),
            ("Z3  (Vorwärts-Reserve)",   d21["Z3"],  adr["X_Z3"],  adr["R_Z3"],  adr["RE_Z3"],  adr["T3"]),
        ):
            zonen_sw.append((
                znm,
                f"{z['X_sek']:.3f}", ax,
                f"{z['R_sek']:.3f}", ar,
                f"{z['RE_sek']:.3f}", are_,
                f"{z['t']:.2f}", at,
            ))
        for rnm, z in (("Z4", d21["Z4"]), ("Z5", d21["Z5"]), ("Z6", d21["Z6"])):
            if z["aktiv"]:
                zonen_sw.append((
                    f"{rnm}  [{z['modus']}]",
                    f"{z['X_sek']:.3f}", z["x_adr"],
                    f"{z['R_sek']:.3f}", z["r_adr"],
                    f"{z['RE_sek']:.3f}", z["re_adr"],
                    f"{z['t']:.2f}", z["t_adr"],
                ))
        dfz_sw = pd.DataFrame(zonen_sw, columns=[
            "Zone",
            "X sek. [Ω]", "Adr. X",
            "R sek. [Ω]", "Adr. R",
            "RE sek. [Ω]", "Adr. RE",
            "t [s]", "Adr. T",
        ])
        st.dataframe(dfz_sw, width="stretch", hide_index=True)

        # Erdimpedanzanpassung direkt unter Zonenmatrix (gehört zu 21)
        erdimp_rows = []
        if d21["erdimp_format"] == KL.ERDIMP_FORMAT_OPTIONEN[0]:
            erdimp_rows.append(("RE/RL (Z1)", f"{d21['RE_RL']:.2f}", "—", f"Adr.{adr['RE_RL']}"))
            erdimp_rows.append(("XE/XL (Z1)", f"{d21['XE_XL']:.2f}", "—",
                                "Adr." + KL.ADR_get("XE_XL_Z1", leitgeraet)))
        else:
            erdimp_rows.append(("K0 (Z1) Betrag", f"{d21['K0']:.2f}", "—", f"Adr.{adr['K0']}"))
            erdimp_rows.append(("PHI K0 (Z1)", f"{d21['PHI_K0']}", "°",
                                "Adr." + KL.ADR_get("PHI_K0_Z1", leitgeraet)))
        erdimp_rows.append(("PHI LTG (Leitungswinkel)", f"{phi}", "°", f"Adr.{adr['PHI_LTG']}"))
        erdimp_rows.append(("Format Erdimpedanz", d21["erdimp_format"], "—", f"Adr.{adr['FORMAT']}"))
        erdimp_rows.append(("Anregeverfahren", d21["anr"], "—", f"Adr.{adr['DIS_ANR']}"))
        erdimp_rows.append(("Charakteristik", d21["charakt"], "—", f"Adr.{adr['DIS_CHARAKT']}"))
        dfe_sw = pd.DataFrame(erdimp_rows,
                              columns=["Parameter (21 / Anlagendaten)", "Sollwert", "Einheit", "DIGSI-Adresse"])
        st.dataframe(dfe_sw, width="stretch", hide_index=True)

        st.divider()

        # ── Tabelle 2: Alle übrigen Schutzfunktionen ─────────────────────────
        st.markdown("**Alle Schutzfunktionen — Parameterliste**")
        rows = []
        # 87L Leitungsdifferentialschutz (nur 7SD5)
        if d87["verfuegbar"]:
            a87 = d87["adr"]
            rows.append(("87L", "DIFF.-SCHUTZ", "Ein", "—", f"Adr.{a87['DIFF_SCHUTZ']}"))
            rows.append(("87L", "I-DIFF>  I (prim.)", f"{d87['i_diff_prim']:.1f}", "A prim.", f"Adr.{a87['I_DIFF']}"))
            rows.append(("87L", "I-DIFF>  T", f"{d87['t_i_diff']:.2f}", "s", f"Adr.{a87['T_I_DIF']}"))
            rows.append(("87L", "I-DIF> ZUSCH.", f"{d87['i_diff_zusch_prim']:.1f}", "A prim.", f"Adr.{a87['I_DIF_ZUSCH']}"))
            rows.append(("87L", "I-DIFF>>", f"{d87['i_diff_hh_prim']:.1f}", "A prim.", f"Adr.{a87['I_DIFF_HH']}"))
            rows.append(("87L", "Ic-KOMP.", d87["ic_komp"], "—", f"Adr.{a87['IC_KOMP']}"))
            rows.append(("87L", "IcSTAB/IcN", f"{d87['icstab_icn']:.1f}", "× IcN", f"Adr.{a87['ICSTAB_ICN']}"))
            rows.append(("87L", "ANZAHL GERAETE", f"{d87['anzahl_geraete']}", "—", f"Adr.{a87['ANZAHL_GERAETE']}"))
        # 67N Gerichteter Erdkurzschlussschutz (geerdete Netze)
        if d67["geerdet"]:
            a67 = d67["adr"]
            rows.append(("67N", "ERDFEHLER", "Ein", "—", f"Adr.{a67['ERDFEHLER']}"))
            for nm, s, ai, at, am in (
                ("3I0>>>", d67["3I0HHH"], a67["I_HHH"], a67["T_HHH"], a67["M_HHH"]),
                ("3I0>>",  d67["3I0HH"],  a67["I_HH"],  a67["T_HH"],  a67["M_HH"]),
                ("3I0>",   d67["3I0H"],   a67["I_H"],   a67["T_H"],   a67["M_H"]),
            ):
                rows.append(("67N", f"{nm}  MODUS [{s['modus']}]", s["modus"], "—", f"Adr.{am}"))
                rows.append(("67N", f"{nm}  I (prim.)", f"{s['i_prim']:.1f}", "A prim.", f"Adr.{ai}"))
                rows.append(("67N", f"{nm}  T", f"{s['t']:.2f}", "s", f"Adr.{at}"))
            rows.append(("67N", "PHI KOMP", f"{d67['phi_komp']}", "°", f"Adr.{a67['PHI_KOMP']}"))
        # 85 Signalübertragungsverfahren (wenn aktiv)
        if d85["aktiv"]:
            a85 = d85["adr"]
            rows.append(("85", "SIGNALZUSATZ", d85["verfahren"], "—", f"Adr.{a85['SIGNALZUSATZ']}"))
            rows.append(("85", "T SENDVERL.", f"{d85['t_sendverl']:.2f}", "s", f"Adr.{a85['T_SENDVERL']}"))
            rows.append(("85", "TV (Freigabe Z1B)", f"{d85['tv']:.2f}", "s", f"Adr.{a85['TV']}"))
            rows.append(("85", "T WARTE RÜCKW.", f"{d85['t_warte_rueckw']:.2f}", "s", f"Adr.{a85['T_WARTE_RUECKW']}"))
            rows.append(("85", "T TRANSBLOCK", f"{d85['t_transblock']:.2f}", "s", f"Adr.{a85['T_TRANSBLOCK']}"))
        # 50/51 Not-Überstrom (wenn aktiv)
        if d50["aktiv"]:
            a50 = d50["adr"]
            rows.append(("50/51", "Betriebsart", d50["betriebsart"], "—", f"Adr.{a50['BETRIEBSART']}"))
            rows.append(("50/51", "Iph>>  I (prim.)", f"{d50['IphHH']['i_prim']:.1f}", "A prim.", f"Adr.{a50['IPH_HH']}"))
            rows.append(("50/51", "Iph>>  T", f"{d50['IphHH']['t']:.2f}", "s", f"Adr.{a50['T_IPH_HH']}"))
            rows.append(("50/51", "Iph>  I (prim.)", f"{d50['IphH']['i_prim']:.1f}", "A prim.", f"Adr.{a50['IPH_H']}"))
            rows.append(("50/51", "Iph>  T", f"{d50['IphH']['t']:.2f}", "s", f"Adr.{a50['T_IPH_H']}"))
        # 79 AWE (wenn aktiv)
        if d79["aktiv"]:
            a79 = d79["adr"]
            rows.append(("79", "AUTO-WE", f"Ein ({d79['anzahl']} Zyklen)", "—", f"Adr.{a79['AUTO_WE']}"))
            rows.append(("79", "TP nach 1-pol. AUS", f"{d79['tp_1pol']:.2f}", "s", f"Adr.{a79['TP_1POL']}"))
            rows.append(("79", "TP nach 3-pol. AUS", f"{d79['tp_3pol']:.2f}", "s", f"Adr.{a79['TP_3POL']}"))
            rows.append(("79", "Sperrzeit", f"{d79['sperrzeit']:.2f}", "s", f"Adr.{a79['SPERRZEIT']}"))
        # 50BF Schalterversager (wenn aktiv)
        if dbf["aktiv"]:
            abf = dbf["adr"]
            rows.append(("50BF", "I> SVS", f"{dbf['i_svs_prim']:.1f}", "A prim.", f"Adr.{abf['I_SVS']}"))
            rows.append(("50BF", "3I0> SVS", f"{round(dbf['i3i0_svs'] * g['IN_Ltg'], 1):.1f}", "A prim.", f"Adr.{abf['I3I0_SVS']}"))
            rows.append(("50BF", "AUS 1POL (T1)", dbf["aus_1pol"], "Ja/Nein", f"Adr.{abf['AUS_1POL']}"))
            rows.append(("50BF", "T1 1POL", f"{dbf['t1_1pol']:.2f}", "s", f"Adr.{abf['T1_1POL']}"))
            rows.append(("50BF", "T1 3POL (eigener LS)", f"{dbf['t1_3pol']:.2f}", "s", f"Adr.{abf['T1_3POL']}"))
            rows.append(("50BF", "T2 (umliegende LS)", f"{dbf['t2']:.2f}", "s", f"Adr.{abf['T2']}"))
        # 68/78 Pendelsperre
        if d68["aktiv"]:
            a68 = d68["adr"]
            rows.append(("68/78", "PEN-AUSLÖS", d68["pen_ausloes"], "—", f"Adr.{a68['PEN_AUSLOES']}"))
        # 27/59 Spannungsschutz — alle vier Stufen, je Wert und Zeit getrennt
        if d2759["aktiv"]:
            a27 = d2759["adr"]
            rows.append(("59", "Uph>>  U (× UN)", f"{d2759['UphHH']['faktor']:.2f}", "× UN", f"Adr.{a27['UPH_HH']}"))
            rows.append(("59", "Uph>>  T", f"{d2759['UphHH']['t']:.2f}", "s", f"Adr.{a27['T_UPH_HH']}"))
            rows.append(("59", "Uph>  U (× UN)", f"{d2759['UphH']['faktor']:.2f}", "× UN", f"Adr.{a27['UPH_H']}"))
            rows.append(("59", "Uph>  T", f"{d2759['UphH']['t']:.2f}", "s", f"Adr.{a27['T_UPH_H']}"))
            rows.append(("27", "Uph<  U (× UN)", f"{d2759['UphL']['faktor']:.2f}", "× UN", f"Adr.{a27['UPH_L']}"))
            rows.append(("27", "Uph<  T", f"{d2759['UphL']['t']:.2f}", "s", f"Adr.{a27['T_UPH_L']}"))
            rows.append(("27", "Uph<<  U (× UN)", f"{d2759['UphLL']['faktor']:.2f}", "× UN", f"Adr.{a27['UPH_LL']}"))
            rows.append(("27", "Uph<<  T", f"{d2759['UphLL']['t']:.2f}", "s", f"Adr.{a27['T_UPH_LL']}"))
        # 81 Frequenzschutz — f und T je eigene Zeile
        if d81["aktiv"]:
            for nm in ("f1", "f2", "f3", "f4"):
                s = d81[nm]
                rows.append(("81", f"{nm}  f ({s['art']})", f"{s['f']:.2f}", "Hz", f"Adr.{s['adr_f']}"))
                rows.append(("81", f"{nm}  T", f"{s['t']:.2f}", "s", f"Adr.{s['adr_t']}"))
        # 49 Überlastschutz
        if d49["aktiv"]:
            a49 = d49["adr"]
            rows.append(("49", "K-FAKTOR", f"{d49['k_faktor']:.2f}", "—", f"Adr.{a49['K_FAKTOR']}"))
            rows.append(("49", "ZEITKONSTANTE τ_th", f"{d49['zeitkonstante']}", "min", f"Adr.{a49['ZEITKONST']}"))
            rows.append(("49", "THETA WARN", f"{d49['theta_warn']}", "%", f"Adr.{a49['THETA_WARN']}"))
            rows.append(("49", "I WARN", f"{d49['i_warn']:.2f}", "× IN", f"Adr.{a49['I_WARN']}"))
        dft = pd.DataFrame(rows, columns=["ANSI", "Parameter", "Sollwert", "Einheit", "Hinweis / Adresse"])
        st.dataframe(dft, width="stretch", hide_index=True)
        st.caption("Sekundärwerte gelten für die gewählten Wandler. Physikalische IEC-Größen "
                   "(Ω, s, A, °) → auf andere Relaisfamilien übertragbar; die SIPROTEC-Adressen dienen "
                   "als nachvollziehbare Berechnungsgrundlage. "
                   "Der Distanzschutz 21 ist bei beiden Leitgeräten vorhanden, der "
                   "Leitungsdifferentialschutz 87L nur bei der 7SD5.")
