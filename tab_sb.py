"""
tab_sb.py — Streamlit-UI für Sammelschienenschutz (SIPROTEC 7SS52)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Dezentraler Sammelschienen- und Schalterversagerschutz: Zentraleinheit (ZE) plus
je Abzweig eine Feldeinheit (FE). Funktionsumfang des 7SS52: 87B (Differential-
schutz, selektive Zone SS und Checkzone CZ), 50BF (Schalterversagerschutz),
Reserve-Schalterversagerschutz und Reserve-Überstromzeitschutz 50/51 in der
Feldeinheit sowie die Differential-/Trenner-Überwachung.

Hinweis: Das 7SS52 führt keinen Spannungsschutz (27/59); der Schutz ist
strombasiert. Spannungsschutz bleibt daher außerhalb des Funktionsumfangs.
"""

import pandas as pd
import streamlit as st

import konstanten_sb as KS
from calc_sb import berechne_alle
from utils import de


# -- Farbkodierung (identisch zu den uebrigen Tabs) ---------------------------
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
    h = KS.HERST.get(key)
    if not h:
        return
    adr_pin = (f'<br>📍 <b>Eintragen unter:</b> {h["adr"]}' if h.get("adr") else '')
    st.markdown(
        f'<div style="font-size:0.72rem;color:#5d6b82;margin:-6px 0 10px;line-height:1.25;">'
        f'<b>Hersteller:</b> {h["range"]}<br>{h["grund"]}{adr_pin}</div>',
        unsafe_allow_html=True)


def _pin(adr):
    """Schlanker Adress-Pin unter einem Eingabefeld (nur reine Ein/Aus-Schalter)."""
    if not adr:
        return
    st.markdown(
        f'<div style="font-size:0.72rem;color:#5d6b82;margin:-6px 0 10px;">'
        f'📍 <b>Eintragen unter:</b> Adr.{adr}</div>',
        unsafe_allow_html=True)


def _grphead(title):
    st.markdown(
        f'<div style="font-weight:700;font-size:0.97rem;margin:18px 0 8px;'
        f'padding-bottom:4px;border-bottom:2px solid #2E5A87;">{title}</div>',
        unsafe_allow_html=True)


def _pill(status, count):
    cls = _PILL_CLASS.get(status, "pill-na")
    emj = _AMPEL_EMOJI.get(status, "")
    return f'<span class="pill {cls}">{emj} {status}: {count}</span>'


# -- Hauptfunktion ------------------------------------------------------------

def show():
    st.markdown(_CSS, unsafe_allow_html=True)

    # ====================== EINGABEN ======================
    with _section("Eingaben — Grunddaten, Wandler, Netz"):
        ci1, ci2, ci3 = st.columns(3, gap="medium")
        with ci1:
            st.caption("**Sammelschienen-Grunddaten**")
            UN = st.number_input("UN — Bemessungsspannung [kV]", 0.4, value=20.0, step=1.0,
                                 format="%.1f", key="sb_un")
            topo = st.selectbox("Sammelschienen-Topologie", KS.SB_TOPOLOGIE_OPTIONEN, index=1,
                                key="sb_topo")
            n_abz = st.number_input("Anzahl Abzweige (Feldeinheiten)", 2, 48, value=8, step=1,
                                    key="sb_nabz",
                                    help="Je Abzweig eine Feldeinheit; max. 48 Längstrenner / "
                                         "16 Kupplungen im 7SS52 V4.")
            IN_ref = st.number_input("Bezugsstrom Ino [A]", 0.0, value=2000.0, step=10.0,
                                     format="%.0f", key="sb_inref",
                                     help="Zonen-Bezugsstrom, auf den die Differential-Ansprechwerte "
                                          "(x Ino) bezogen sind. Üblich: Nennstrom des größten "
                                          "Abzweigs bzw. ein gewählter Referenzstrom.")
        with ci2:
            st.caption("**Referenz-Stromwandler**")
            c1, c2 = st.columns(2)
            with c1:
                CT_P = st.number_input("CT prim. [A]", 1, value=2000, step=10, key="sb_ctp")
            with c2:
                CT_S = st.selectbox("CT sek. [A]", [1, 5], index=0, key="sb_cts")
            st.caption("Der Referenzwandler dient der Sekundärumrechnung. Die Feldeinheiten "
                       "normieren ihre Abzweigwandler intern auf den Bezugsstrom Ino.")
            f_netz = st.selectbox("Nennfrequenz [Hz]", [50, 60],
                                  index=[50, 60].index(KS.f_netz_def), key="sb_f",
                                  help="Adr.5104 (Zentraleinheit).")
        with ci3:
            st.caption("**Netz & Bemessungsströme**")
            stp = st.selectbox("Sternpunktbehandlung Netz", KS.STERNPUNKT_NETZ_OPTIONEN, index=0,
                               key="sb_stp")
            Imax_Last = st.number_input("Imax Last (Summe Abzweige) [A]", 0.0, value=1800.0,
                                        step=10.0, format="%.0f", key="sb_imaxlast",
                                        help="Größter durchfliessender Laststrom der Sammelschiene "
                                             "(für die empfindliche Kennlinie).")
            Imax_Abz = st.number_input("Imax Abzweig [A]", 0.0, value=600.0, step=10.0,
                                       format="%.0f", key="sb_imaxabz",
                                       help="Größter Strom eines einzelnen Abzweigs (untere "
                                            "Stabilitätsgrenze für Id>).")
            Iscc_min = st.number_input("Iscc min Sammelschiene [kA]", 0.0, value=8.0, step=0.5,
                                       format="%.2f", key="sb_isccmin",
                                       help="Kleinster Sammelschienen-Kurzschlussstrom (DIN EN "
                                            "60909-0). Obergrenze für Id> und Bezug für I> SVS.")
            Iscc_max = st.number_input("Iscc max Sammelschiene [kA]", 0.0, value=25.0, step=1.0,
                                       format="%.1f", key="sb_isccmax")
            t_LS = st.number_input("Ausschaltzeit Leistungsschalter t_LS [s]", 0.0, value=0.06,
                                   step=0.01, format="%.3f", key="sb_tls",
                                   help="Eigenzeit des Leistungsschalters (Bezug für die "
                                        "SVS-Verzögerung T-SVS ~ 2 x t_LS).")

    dev_key = KS.SB_GERAET_KEY[KS.SB_GERAET_OPTIONEN[0]]

    # -- Erweiterte Parameter: 87B Differentialschutz --------------------------
    with _section("Erweiterte Parameter — Differentialschutz 87B (Zentraleinheit)", expanded=False):
        st.caption("ℹ️ Adressen der Zentraleinheit (Adr.6101 ff.). Ansprechwerte als Vielfaches "
                   "des Bezugsstroms Ino. SS = schienenselektive Zone, CZ = Checkzone.")
        diff_aktiv = st.checkbox("87B Sammelschienen-Differentialschutz aktiv", value=KS.diff_aktiv_def,
                                 key="sb_diffaktiv")
        cda, cdb = st.columns(2)
        with cda:
            _grphead("Selektive Zone (SS)")
            stab_faktor_ss = st.number_input("Stab.-Faktor SS", 0.10, 0.80, value=KS.stab_faktor_ss_def,
                                             step=0.05, format="%.2f", key="sb_stabss")
            _hreg("stab_faktor_ss")
            id_ss = st.number_input("Id> SS [x Ino]", 0.20, 4.00, value=KS.id_ss_def, step=0.05,
                                    format="%.2f", key="sb_idss")
            _hreg("id_ss")
            querstab_ss = st.number_input("Querstab.-Faktor SS", 0.00, 1.00, value=KS.querstab_ss_def,
                                          step=0.05, format="%.2f", key="sb_qsss")
            _hreg("querstab_ss")
        with cdb:
            _grphead("Checkzone (CZ)")
            stab_faktor_cz = st.number_input("Stab.-Faktor CZ", 0.00, 0.80, value=KS.stab_faktor_cz_def,
                                             step=0.05, format="%.2f", key="sb_stabcz")
            _hreg("stab_faktor_cz")
            id_cz = st.number_input("Id> CZ [x Ino]", 0.20, 4.00, value=KS.id_cz_def, step=0.05,
                                    format="%.2f", key="sb_idcz")
            _hreg("id_cz")
            querstab_cz = st.number_input("Querstab.-Faktor CZ", 0.00, 1.00, value=KS.querstab_cz_def,
                                          step=0.05, format="%.2f", key="sb_qscz")
            _hreg("querstab_cz")

        _grphead("Empfindliche Kennlinie und Zusatzkriterium")
        empf_kennl = st.selectbox("Empfindliche Kennlinie", KS.EMPF_KENNL_OPTIONEN,
                                  index=KS.EMPF_KENNL_OPTIONEN.index(KS.empf_kennl_def), key="sb_empf")
        _hreg("empf_kennl")
        # Voreinstellungen, falls empfindliche Kennlinie gesperrt bleibt
        id_ss_empf, is_ss_empf = KS.id_ss_empf_def, KS.is_ss_empf_def
        id_cz_empf, is_cz_empf = KS.id_cz_empf_def, KS.is_cz_empf_def
        if empf_kennl == "freigegeben":
            ce1, ce2 = st.columns(2)
            with ce1:
                id_ss_empf = st.number_input("Id> SS empf. [x Ino]", 0.05, 4.00,
                                             value=KS.id_ss_empf_def, step=0.05, format="%.2f",
                                             key="sb_idssempf")
                _hreg("id_ss_empf")
                is_ss_empf = st.number_input("Is< SS empf. [x Ino]", 0.00, 25.00,
                                             value=KS.is_ss_empf_def, step=0.5, format="%.2f",
                                             key="sb_isssempf")
                _hreg("is_ss_empf")
            with ce2:
                id_cz_empf = st.number_input("Id> CZ empf. [x Ino]", 0.05, 4.00,
                                             value=KS.id_cz_empf_def, step=0.05, format="%.2f",
                                             key="sb_idczempf")
                _hreg("id_cz_empf")
                is_cz_empf = st.number_input("Is< CZ empf. [x Ino]", 0.00, 25.00,
                                             value=KS.is_cz_empf_def, step=0.5, format="%.2f",
                                             key="sb_isczempf")
                _hreg("is_cz_empf")
        zusatzkrit = st.selectbox("Zusatzkriterium für Auslösung", KS.ZUSATZKRIT_OPTIONEN,
                                  index=KS.ZUSATZKRIT_OPTIONEN.index(KS.zusatzkrit_def), key="sb_zusatz")
        _hreg("zusatzkrit")
        t_aus_min = st.number_input("T AUS min. [s]", 0.01, 32.00, value=KS.t_aus_min_def, step=0.01,
                                    format="%.2f", key="sb_tausmin")
        _hreg("t_aus_min")

    # -- Erweiterte Parameter: 50BF Schalterversagerschutz ---------------------
    with _section("Erweiterte Parameter — Schalterversagerschutz 50BF (abzweigselektiv)",
                  expanded=False):
        st.caption("ℹ️ SVS-Basisadressen 114 ... 128 je Feldeinheit (in DIGSI mit "
                   "Feldeinheit-Präfix). Stromschwelle als Vielfaches des Abzweig-Nennstroms In.")
        _grphead("Betriebsart und Anwurf")
        cs1, cs2 = st.columns(2)
        with cs1:
            svs_betriebsart = st.selectbox("SVS-Betriebsart", KS.SVS_BETRIEBSART_OPTIONEN,
                                           index=KS.SVS_BETRIEBSART_OPTIONEN.index(KS.svs_betriebsart_def),
                                           key="sb_svsbart")
            _hreg("svs_betriebsart")
            svs_be_mode = st.selectbox("SVS-BE-Mode (Anwurf-Binäreingänge)", KS.SVS_BE_MODE_OPTIONEN,
                                       index=KS.SVS_BE_MODE_OPTIONEN.index(KS.svs_be_mode_def),
                                       key="sb_svsbemode")
            _hreg("svs_be_mode")
        with cs2:
            svs_i_klein = st.selectbox("Stromschwache Betriebsart (SVS-I<)", KS.EIN_AUS_OPTIONEN,
                                       index=KS.EIN_AUS_OPTIONEN.index(KS.svs_i_klein_def),
                                       key="sb_svsiklein")
            _hreg("svs_i_klein")
            aus_wiederh = st.selectbox("AUS-Wiederholung", KS.AUS_WIEDERH_OPTIONEN,
                                       index=KS.AUS_WIEDERH_OPTIONEN.index(KS.aus_wiederh_def),
                                       key="sb_auswiederh")
            _hreg("aus_wiederh")

        _grphead("Stromschwellen und Stabilisierung")
        cs3, cs4 = st.columns(2)
        with cs3:
            i_svs = st.number_input("I> SVS [x In]", 0.10, 2.00, value=KS.i_svs_def, step=0.05,
                                    format="%.2f", key="sb_isvs")
            _hreg("i_svs")
            i_svs_empf = st.number_input("I> SVS empf. [x In]", 0.05, 2.00, value=KS.i_svs_empf_def,
                                         step=0.05, format="%.2f", key="sb_isvsempf")
            _hreg("i_svs_empf")
        with cs4:
            stab_faktor_svs = st.number_input("Stab.-Faktor SVS", 0.00, 0.80,
                                              value=KS.stab_faktor_svs_def, step=0.05, format="%.2f",
                                              key="sb_stabsvs")
            _hreg("stab_faktor_svs")
            is_svs_empf = st.number_input("Is< SVS empf. [x Ino]", 0.00, 25.00,
                                          value=KS.is_svs_empf_def, step=0.5, format="%.2f",
                                          key="sb_issvsempf")
            _hreg("is_svs_empf")

        _grphead("Verzögerungszeiten")
        ct1, ct2, ct3 = st.columns(3)
        with ct1:
            t_svs_1p = st.number_input("T-SVS-1P [s]", 0.05, 10.00, value=KS.t_svs_1p_def, step=0.01,
                                       format="%.2f", key="sb_tsvs1p")
            _hreg("t_svs_1p")
            t_svs_iklein = st.number_input("T-SVS-I< [s]", 0.05, 10.00, value=KS.t_svs_iklein_def,
                                           step=0.01, format="%.2f", key="sb_tsvsik")
            _hreg("t_svs_iklein")
        with ct2:
            t_svs_mp = st.number_input("T-SVS-mP [s]", 0.05, 10.00, value=KS.t_svs_mp_def, step=0.01,
                                       format="%.2f", key="sb_tsvsmp")
            _hreg("t_svs_mp")
            t_svs_impuls = st.number_input("T-SVS-Impuls [s]", 0.05, 10.00, value=KS.t_svs_impuls_def,
                                           step=0.01, format="%.2f", key="sb_tsvsimp")
            _hreg("t_svs_impuls")
        with ct3:
            t_aus_wiederh = st.number_input("T-AUS-Wiederh. [s]", 0.00, 10.00, value=KS.t_aus_wiederh_def,
                                            step=0.01, format="%.2f", key="sb_tausw")
            _hreg("t_aus_wiederh")
            t_svs_ls_stoer = st.number_input("T-SVS-LS-Störg [s]", 0.00, 10.00,
                                             value=KS.t_svs_ls_stoer_def, step=0.01, format="%.2f",
                                             key="sb_tsvslsst")
            _hreg("t_svs_ls_stoer")
        ct4, ct5 = st.columns(2)
        with ct4:
            t_svs_frueb = st.number_input("T-SVS-FrÜb [s]", 0.02, 15.00, value=KS.t_svs_frueb_def,
                                          step=0.1, format="%.2f", key="sb_tsvsfrueb")
            _hreg("t_svs_frueb")
        with ct5:
            t_svs_frto = st.number_input("T-SVS-FrTo [s]", 0.06, 1.00, value=KS.t_svs_frto_def,
                                         step=0.01, format="%.2f", key="sb_tsvsfrto")
            _hreg("t_svs_frto")

    # -- Erweiterte Parameter: Reserve-SVS + 50/51 (Feldeinheit) ---------------
    with _section("Erweiterte Parameter — Reserve-SVS und Reserve-Überstromzeitschutz 50/51 "
                  "(Feldeinheit)", expanded=False):
        _grphead("Reserve-Schalterversagerschutz (Feldeinheit)")
        cr1, cr2, cr3 = st.columns(3)
        with cr1:
            res_svs = st.selectbox("Reserve-SVS", KS.EIN_AUS_OPTIONEN,
                                   index=KS.EIN_AUS_OPTIONEN.index(KS.res_svs_def), key="sb_ressvs")
            _hreg("res_svs")
        with cr2:
            res_svs_i = st.number_input("RES.SVS-I [x In]", 0.10, 4.00, value=KS.res_svs_i_def,
                                        step=0.05, format="%.2f", key="sb_ressvsi")
            _hreg("res_svs_i")
        with cr3:
            res_svs_t = st.number_input("RES.SVS-T [s]", 0.06, 60.00, value=KS.res_svs_t_def,
                                        step=0.01, format="%.2f", key="sb_ressvst")
            _hreg("res_svs_t")

        _grphead("50/51 Reserve-Überstromzeitschutz Phasen")
        umz_p = st.selectbox("UMZ/AMZ Phasen", KS.EIN_AUS_OPTIONEN,
                             index=KS.EIN_AUS_OPTIONEN.index(KS.umz_p_def), key="sb_umzp")
        _pin(KS.ADR_get("UMZ_P"))
        kennlinie_p = st.selectbox("Auslösecharakteristik Phasen", KS.KENNLINIE_OPTIONEN,
                                   index=KS.KENNLINIE_OPTIONEN.index(KS.kennlinie_p_def), key="sb_kennp")
        _hreg("kennlinie_p")
        cp1, cp2, cp3 = st.columns(3)
        with cp1:
            iph_hh = st.number_input("I>> [x In]", 0.05, 25.00, value=KS.iph_hh_def, step=0.05,
                                     format="%.2f", key="sb_iphhh")
            _hreg("iph_hh")
            t_iph_hh = st.number_input("T I>> [s]", 0.00, 60.00, value=KS.t_iph_hh_def, step=0.01,
                                       format="%.2f", key="sb_tiphhh")
            _hreg("t_iph_hh")
        with cp2:
            iph_h = st.number_input("I> [x In]", 0.05, 25.00, value=KS.iph_h_def, step=0.05,
                                    format="%.2f", key="sb_iphh")
            _hreg("iph_h")
            t_iph_h = st.number_input("T I> [s]", 0.00, 60.00, value=KS.t_iph_h_def, step=0.01,
                                      format="%.2f", key="sb_tiphh")
            _hreg("t_iph_h")
        with cp3:
            ip = st.number_input("Ip (AMZ) [x In]", 0.10, 4.00, value=KS.ip_def, step=0.05,
                                 format="%.2f", key="sb_ip")
            _hreg("ip")
            t_ip = st.number_input("T Ip [s]", 0.05, 10.00, value=KS.t_ip_def, step=0.01,
                                   format="%.2f", key="sb_tip")
            _hreg("t_ip")

        _grphead("50/51 Reserve-Überstromzeitschutz Erde")
        umz_e = st.selectbox("UMZ/AMZ Erde", KS.EIN_AUS_OPTIONEN,
                             index=KS.EIN_AUS_OPTIONEN.index(KS.umz_e_def), key="sb_umze")
        _pin(KS.ADR_get("UMZ_E"))
        kennlinie_e = st.selectbox("Auslösecharakteristik Erde", KS.KENNLINIE_OPTIONEN,
                                   index=KS.KENNLINIE_OPTIONEN.index(KS.kennlinie_e_def), key="sb_kenne")
        _hreg("kennlinie_e")
        ce1, ce2, ce3 = st.columns(3)
        with ce1:
            ie_hh = st.number_input("IE>> [x In]", 0.05, 25.00, value=KS.ie_hh_def, step=0.05,
                                    format="%.2f", key="sb_iehh")
            _hreg("ie_hh")
            t_ie_hh = st.number_input("T IE>> [s]", 0.00, 60.00, value=KS.t_ie_hh_def, step=0.01,
                                      format="%.2f", key="sb_tiehh")
            _hreg("t_ie_hh")
        with ce2:
            ie_h = st.number_input("IE> [x In]", 0.05, 25.00, value=KS.ie_h_def, step=0.05,
                                   format="%.2f", key="sb_ieh")
            _hreg("ie_h")
            t_ie_h = st.number_input("T IE> [s]", 0.00, 60.00, value=KS.t_ie_h_def, step=0.01,
                                     format="%.2f", key="sb_tieh")
            _hreg("t_ie_h")
        with ce3:
            iep = st.number_input("IEp (AMZ) [x In]", 0.10, 4.00, value=KS.iep_def, step=0.05,
                                  format="%.2f", key="sb_iep")
            _hreg("iep")
            t_iep = st.number_input("T IEp [s]", 0.05, 10.00, value=KS.t_iep_def, step=0.01,
                                    format="%.2f", key="sb_tiep")
            _hreg("t_iep")

    # -- Erweiterte Parameter: Ueberwachung ------------------------------------
    with _section("Erweiterte Parameter — Differential-/Trenner-Überwachung (Zentraleinheit)",
                  expanded=False):
        cu1, cu2 = st.columns(2)
        with cu1:
            _grphead("Id-Überwachung")
            id_ueberw = st.selectbox("Id-Überwachung", KS.EIN_AUS_OPTIONEN,
                                     index=KS.EIN_AUS_OPTIONEN.index(KS.id_ueberw_def), key="sb_idueb")
            _hreg("id_ueberw")
            t_id_ueberw = st.number_input("T-Id-Überw. [s]", 1.00, 10.00, value=KS.t_id_ueberw_def,
                                          step=0.1, format="%.2f", key="sb_tidueb")
            _hreg("t_id_ueberw")
            id_ueberw_ss = st.number_input("Id> Überw. SS [x Ino]", 0.05, 0.80,
                                           value=KS.id_ueberw_ss_def, step=0.01, format="%.2f",
                                           key="sb_iduebss")
            _hreg("id_ueberw_ss")
            id_ueberw_cz = st.number_input("Id> Überw. CZ [x Ino]", 0.05, 0.80,
                                           value=KS.id_ueberw_cz_def, step=0.01, format="%.2f",
                                           key="sb_iduebcz")
            _hreg("id_ueberw_cz")
            id_ueberw_reak_ss = st.selectbox("Reaktion Id-Überw. SS", KS.UEBERW_REAKTION_OPTIONEN,
                                             index=KS.UEBERW_REAKTION_OPTIONEN.index(
                                                 KS.id_ueberw_reak_ss_def), key="sb_idreakss")
            _hreg("id_ueberw_reak_ss")
            id_ueberw_reak_cz = st.selectbox("Reaktion Id-Überw. CZ", KS.UEBERW_REAKTION_OPTIONEN,
                                             index=KS.UEBERW_REAKTION_OPTIONEN.index(
                                                 KS.id_ueberw_reak_cz_def), key="sb_idreakcz")
            _hreg("id_ueberw_reak_cz")
        with cu2:
            _grphead("Nulldurchgang / Trenner / LS")
            null_dg_ueberw = st.selectbox("Nulldurchgangsüberwachung", KS.EIN_AUS_OPTIONEN,
                                          index=KS.EIN_AUS_OPTIONEN.index(KS.null_dg_ueberw_def),
                                          key="sb_nulldg")
            _hreg("null_dg_ueberw")
            i_null_dg = st.number_input("I> Null-DG-Überw. [x Ino]", 0.15, 4.00,
                                        value=KS.i_null_dg_def, step=0.05, format="%.2f",
                                        key="sb_inulldg")
            _hreg("i_null_dg")
            tr_laufzeit = st.number_input("TR-Laufzeit [s]", 1.00, 180.00, value=KS.tr_laufzeit_def,
                                          step=1.0, format="%.2f", key="sb_trlauf")
            _hreg("tr_laufzeit")
            ls_ueberw_zeit = st.number_input("LS-Überw.-Zeit [s]", 1.00, 180.00,
                                             value=KS.ls_ueberw_zeit_def, step=1.0, format="%.2f",
                                             key="sb_lsueb")
            _hreg("ls_ueberw_zeit")

    # -- Parameter-Dict zusammenstellen ---------------------------------------
    p = dict(
        UN_kV=UN, topologie=topo, anzahl_abzweige=n_abz, IN_ref=IN_ref,
        CT_Prim=CT_P, CT_Sek=CT_S, f_netz=f_netz, sternpunkt=stp,
        Imax_Last=Imax_Last, Imax_Abzweig=Imax_Abz, Iscc_min_kA=Iscc_min,
        Iscc_max_kA=Iscc_max, t_LS=t_LS,
        diff_aktiv=diff_aktiv, stab_faktor_ss=stab_faktor_ss, stab_faktor_cz=stab_faktor_cz,
        id_ss=id_ss, id_cz=id_cz, querstab_ss=querstab_ss, querstab_cz=querstab_cz,
        empf_kennl=empf_kennl, id_ss_empf=id_ss_empf, is_ss_empf=is_ss_empf,
        id_cz_empf=id_cz_empf, is_cz_empf=is_cz_empf, zusatzkrit=zusatzkrit, t_aus_min=t_aus_min,
        svs_betriebsart=svs_betriebsart, svs_be_mode=svs_be_mode, svs_i_klein=svs_i_klein,
        aus_wiederh=aus_wiederh, i_svs=i_svs, i_svs_empf=i_svs_empf,
        stab_faktor_svs=stab_faktor_svs, is_svs_empf=is_svs_empf,
        t_svs_1p=t_svs_1p, t_svs_mp=t_svs_mp, t_svs_iklein=t_svs_iklein, t_svs_impuls=t_svs_impuls,
        t_svs_ls_stoer=t_svs_ls_stoer, t_aus_wiederh=t_aus_wiederh,
        t_svs_frueb=t_svs_frueb, t_svs_frto=t_svs_frto,
        res_svs=res_svs, res_svs_i=res_svs_i, res_svs_t=res_svs_t,
        umz_p=umz_p, kennlinie_p=kennlinie_p, iph_hh=iph_hh, t_iph_hh=t_iph_hh,
        iph_h=iph_h, t_iph_h=t_iph_h, ip=ip, t_ip=t_ip,
        umz_e=umz_e, kennlinie_e=kennlinie_e, ie_hh=ie_hh, t_ie_hh=t_ie_hh,
        ie_h=ie_h, t_ie_h=t_ie_h, iep=iep, t_iep=t_iep,
        id_ueberw=id_ueberw, t_id_ueberw=t_id_ueberw, id_ueberw_ss=id_ueberw_ss,
        id_ueberw_cz=id_ueberw_cz, id_ueberw_reak_ss=id_ueberw_reak_ss,
        id_ueberw_reak_cz=id_ueberw_reak_cz,
        null_dg_ueberw=null_dg_ueberw, i_null_dg=i_null_dg,
        tr_laufzeit=tr_laufzeit, ls_ueberw_zeit=ls_ueberw_zeit,
    )
    r = berechne_alle(p)
    g, d87, dbf = r["grund"], r["87B"], r["50BF"]
    dres, d50, dueb = r["RES_SVS"], r["50/51"], r["ueberwachung"]

    # ====================== PLAUSIBILITAET — ZUSAMMENFASSUNG ======================
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
                    'Die berechneten Werte sind konsistent und entsprechen der 7SS52-Methodik. '
                    'Bewusste Abweichungen bleiben dir überlassen.</div>', unsafe_allow_html=True)

    # ====================== GRUNDGROESSEN ======================
    with _section("Berechnete Grundgrößen"):
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            _metric("Bezugsstrom Ino", f"{de(g['IN_ref'], 0)} A", "Bezug der Differential-Ansprechwerte")
        with m2:
            _metric("Ino sekundär", f"{de(g['IN_ref_sek'], 3)} A", f"Ino / kCT  (kCT = {de(g['kCT'], 1)})")
        with m3:
            _metric("Wandlerverhältnis kCT", f"{de(g['kCT'], 1)}", f"{CT_P}/{CT_S} A")
        with m4:
            _metric("STW-Anpassung", f"{de(g['Anpass'], 2)}" if g["Anpass"] else "—",
                    "Ino / CT prim. (ideal ≈ 1)")
        m5, m6, m7, m8 = st.columns(4)
        with m5:
            _metric("Id>-Untergrenze", f"{de(d87['id_min_prim'], 0)} A", "1,3 · Imax Abzweig")
        with m6:
            _metric("Id>-Obergrenze", f"{de(d87['id_max_prim'], 0)} A", "0,8 · Iscc min")
        with m7:
            _metric("I> SVS Empfehlung", f"{de(dbf['i_svs_empf_prim'], 0)} A", "0,5 · Iscc min")
        with m8:
            _metric("T-SVS Empfehlung", f"{de(dbf['t_svs_empf'], 2)} s", "2 · t_LS")

    # ====================== 87B DIFFERENTIALSCHUTZ ======================
    with _section("Sammelschienen-Differentialschutz 87B (selektive Zone + Checkzone)"):
        if not d87["aktiv"]:
            st.markdown('<div class="off-box"><b>87B ausgeschaltet.</b></div>', unsafe_allow_html=True)
        else:
            a = d87["adr"]
            rows = [
                ("Selektive Zone (SS)", f"{de(d87['id_ss_f'], 2)}", f"{de(d87['id_ss_prim'], 0)}",
                 f"{de(d87['id_ss_sek'], 3)}", f"{de(d87['stab_ss'], 2)}",
                 f"Id→{a['ID_SS']} | Stab→{a['STAB_SS']} | Querstab→{a['QUERSTAB_SS']}"),
                ("Checkzone (CZ)", f"{de(d87['id_cz_f'], 2)}", f"{de(d87['id_cz_prim'], 0)}",
                 f"{de(d87['id_cz_sek'], 3)}", f"{de(d87['stab_cz'], 2)}",
                 f"Id→{a['ID_CZ']} | Stab→{a['STAB_CZ']} | Querstab→{a['QUERSTAB_CZ']}"),
            ]
            if d87["empf_frei"]:
                rows.append((
                    "Selektive Zone empf. (SS)", f"{de(d87['id_ss_e'], 2)}", f"{de(d87['id_ss_e_prim'], 0)}",
                    f"{de(d87['id_ss_e_sek'], 3)}", f"Is< {de(d87['is_ss_e'], 2)}",
                    f"Id→{a['ID_SS_EMPF']} | Is<→{a['IS_SS_EMPF']}"))
                rows.append((
                    "Checkzone empf. (CZ)", f"{de(d87['id_cz_e'], 2)}", f"{de(d87['id_cz_e_prim'], 0)}",
                    f"{de(d87['id_cz_e_sek'], 3)}", f"Is< {de(d87['is_cz_e'], 2)}",
                    f"Id→{a['ID_CZ_EMPF']} | Is<→{a['IS_CZ_EMPF']}"))
            dfd = pd.DataFrame(rows, columns=[
                "Messsystem", "Id> [x Ino]", "Id prim. [A]", "Id sek. [A]", "Stab.-/Is<-Faktor",
                "DIGSI-Adressen (Wert → Adresse)"])
            st.dataframe(dfd, width="stretch", hide_index=True)
            st.caption(f"Empfindliche Kennlinie: **{d87['empf_kennl']}** (Adr.{a['EMPF_KENNL']}) · "
                       f"Zusatzkriterium: **{d87['zusatzkrit']}** (Adr.{a['ZUSATZKRIT']}) · "
                       f"T AUS min.: **{de(d87['t_aus_min'], 2)} s** (Adr.{a['T_AUS_MIN']}). "
                       "Id prim. = Id> · Ino, Id sek. = Id prim. / kCT. Adressspalte: "
                       "Wert → zugehörige DIGSI-Adresse der Zentraleinheit.")

    # ====================== 50BF SCHALTERVERSAGERSCHUTZ ======================
    with _section("Schalterversagerschutz 50BF"):
        if not dbf["aktiv"]:
            st.markdown('<div class="off-box"><b>SVS-Betriebsart Aus.</b></div>',
                        unsafe_allow_html=True)
        else:
            a = dbf["adr"]
            rows = [(
                "I> SVS", f"{de(dbf['i_svs_f'], 2)}", f"{de(dbf['i_svs_prim'], 0)}",
                f"{de(dbf['i_svs_sek'], 3)}", f"{de(dbf['t_1p'], 2)}", f"{de(dbf['t_mp'], 2)}",
                f"I>→{a['I_SVS']} | T1P→{a['T_1P']} | TmP→{a['T_MP']}")]
            if dbf["zweistufig"]:
                rows.append((
                    "I> SVS (empf.)", f"{de(dbf['i_svs_e_f'], 2)}", f"{de(dbf['i_svs_e_prim'], 0)}",
                    f"{de(dbf['i_svs_e_sek'], 3)}", f"AUS-Wied. {de(dbf['t_ausw'], 2)}",
                    f"LS-Stör. {de(dbf['t_lsst'], 2)}",
                    f"I>empf→{a['I_SVS_EMPF']} | T-AUSw→{a['T_AUSW']} | T-LSst→{a['T_LSST']}"))
            dfb = pd.DataFrame(rows, columns=[
                "Stufe", "I> [x In]", "I prim. [A]", "I sek. [A]",
                "t-1P / AUS-Wied. [s]", "t-mP / LS-Stör. [s]",
                "DIGSI-Adressen (Wert → Adresse)"])
            st.dataframe(dfb, width="stretch", hide_index=True)
            st.caption(f"Betriebsart **{dbf['betriebsart']}** (Adr.{a['BETRIEBSART']}) · "
                       f"BE-Mode **{dbf['be_mode']}** (Adr.{a['BE_MODE']}) · "
                       f"stromschwach **{dbf['i_klein']}** (Adr.{a['I_KLEIN']}) · "
                       f"AUS-Wiederholung **{dbf['aus_wiederh']}** (Adr.{a['AUS_WIEDERH']}). "
                       "Bei zweistufigem Betrieb (AUS-Wied-Varianten) läuft zunächst die "
                       "Auswiederholung auf den eigenen Schalter, danach die SVS-Abschaltung des "
                       "Sammelschienenabschnitts.")

    # ====================== RESERVE-SVS ======================
    with _section("Reserve-Schalterversagerschutz (Feldeinheit)"):
        a = dres["adr"]
        if not dres["aktiv"]:
            st.markdown('<div class="off-box"><b>Reserve-SVS Aus.</b> '
                        f'(Adr.{a["RES_SVS"]})</div>', unsafe_allow_html=True)
        else:
            rr = [
                ("RES.SVS-I", f"{de(dres['i_f'], 2)}", "x In", f"{de(dres['i_f'], 2)}→{a['RES_SVS_I']}"),
                ("RES.SVS-I (prim.)", f"{de(dres['i_prim'], 0)}", "A prim.", f"→{a['RES_SVS_I']}"),
                ("RES.SVS-T", f"{de(dres['t'], 2)}", "s", f"{de(dres['t'], 2)}→{a['RES_SVS_T']}"),
            ]
            dfr = pd.DataFrame(rr, columns=["Parameter", "Wert", "Einheit",
                                            "DIGSI-Adresse (Wert → Adresse)"])
            st.dataframe(dfr, width="stretch", hide_index=True)

    # ====================== 50/51 RESERVE-UEBERSTROMZEITSCHUTZ ======================
    with _section("Reserve-Überstromzeitschutz 50/51 (Feldeinheit)"):
        a = d50["adr"]
        rows = []
        for nm, s, ai, at in (
            ("I>>  (Hochstrom)", d50["IphHH"], a["IPH_HH"], a["T_IPH_HH"]),
            ("I>   (Überstrom)", d50["IphH"],  a["IPH_H"],  a["T_IPH_H"]),
            ("Ip   (AMZ)",       d50["Ip"],    a["IP"],     a["T_IP"]),
            ("IE>> (Hochstrom)", d50["IeHH"],  a["IE_HH"],  a["T_IE_HH"]),
            ("IE>  (Überstrom)", d50["IeH"],   a["IE_H"],   a["T_IE_H"]),
            ("IEp  (AMZ)",       d50["Iep"],   a["IEP"],    a["T_IEP"]),
        ):
            rows.append((
                nm, f"{de(s['f'], 2)}", f"{de(s['i_prim'], 0)}", f"{de(s['i_sek'], 3)}", f"{de(s['t'], 2)}",
                f"I→{ai} | T→{at}"))
        df50 = pd.DataFrame(rows, columns=[
            "Stufe", "Ansprechwert [x In]", "I prim. [A]", "I sek. [A]", "t [s]",
            "DIGSI-Adressen (Wert → Adresse)"])
        st.dataframe(df50, width="stretch", hide_index=True)
        st.caption(f"Phasen **{d50['umz_p']}** (Adr.{a['UMZ_P']}), Kennlinie **{d50['kennlinie_p']}** "
                   f"(Adr.{a['KENNLINIE_P']}) · Erde **{d50['umz_e']}** (Adr.{a['UMZ_E']}), Kennlinie "
                   f"**{d50['kennlinie_e']}** (Adr.{a['KENNLINIE_E']}). Bei UMZ wirken nur die "
                   "unabhängigen Stufen I>>/I>; bei AMZ zusätzlich die stromabhängige Stufe Ip.")

    # ====================== UEBERWACHUNG ======================
    with _section("Differential- / Trenner-Überwachung (Zentraleinheit)"):
        a = dueb["adr"]
        rows = [
            ("Id-Überwachung", dueb["id_ueberw"], "—", f"{dueb['id_ueberw']}→{a['ID_UEBERW']}"),
            ("T-Id-Überw.", f"{de(dueb['t_id_ueberw'], 2)}", "s", f"{de(dueb['t_id_ueberw'], 2)}→{a['T_ID_UEBERW']}"),
            ("Id> Überw. SS", f"{de(dueb['id_ueb_ss'], 2)}", "x Ino", f"{de(dueb['id_ueb_ss'], 2)}→{a['ID_UEBERW_SS']}"),
            ("Id> Überw. CZ", f"{de(dueb['id_ueb_cz'], 2)}", "x Ino", f"{de(dueb['id_ueb_cz'], 2)}→{a['ID_UEBERW_CZ']}"),
            ("Reaktion Id-Überw. SS", dueb["reak_ss"], "—", f"{dueb['reak_ss']}→{a['REAK_SS']}"),
            ("Reaktion Id-Überw. CZ", dueb["reak_cz"], "—", f"{dueb['reak_cz']}→{a['REAK_CZ']}"),
            ("Nulldurchgangsüberw.", dueb["null_dg"], "—", f"{dueb['null_dg']}→{a['NULL_DG']}"),
            ("I> Null-DG-Überw.", f"{de(dueb['i_null'], 2)}", "x Ino", f"{de(dueb['i_null'], 2)}→{a['I_NULL_DG']}"),
            ("TR-Laufzeit", f"{de(dueb['tr_laufzeit'], 2)}", "s", f"{de(dueb['tr_laufzeit'], 2)}→{a['TR_LAUFZEIT']}"),
            ("LS-Überw.-Zeit", f"{de(dueb['ls_ueberw_zeit'], 2)}", "s", f"{de(dueb['ls_ueberw_zeit'], 2)}→{a['LS_UEBERW_ZEIT']}"),
        ]
        dfu = pd.DataFrame(rows, columns=["Parameter", "Wert", "Einheit",
                                          "DIGSI-Adresse (Wert → Adresse)"])
        st.dataframe(dfu, width="stretch", hide_index=True)

    # ====================== PLAUSIBILITAETSPRUEFUNG (VOLLSTAENDIG) ======================
    with _section("Plausibilitätsprüfung (Ampel)"):
        rows = [(_AMPEL_EMOJI.get(c["status"], "") + " " + c["status"], c["pruefung"],
                 c["ergebnis"], c["hinweis"], c["korrektur"]) for c in plaus]
        dfp = pd.DataFrame(rows, columns=["Status", "Prüfung", "Ergebnis", "Hinweis", "Korrektur"])
        st.dataframe(dfp, width="stretch", hide_index=True)

    # ====================== GERAETE-/ARCHITEKTUR-EMPFEHLUNG ======================
    with _section("Geräte- / Architektur-Empfehlung"):
        e = r["empfehlung"]
        st.markdown(f'<div class="info-box">{e["haupt"]}<br><br>{e["hinweis"]}</div>',
                    unsafe_allow_html=True)
        st.caption("Hinweis: Das 7SS52 ist ein reiner Strom-Differential-/Schalterversagerschutz "
                   "und enthält keinen Spannungsschutz (27/59). Spannungs- und Frequenzschutz "
                   "sind den Abzweig-/Einspeiseschutzgeräten zugeordnet.")

    # ====================== SOLLWERT-TABELLE ======================
    with _section(f"📋  Herstellerneutrale Sollwert-Tabelle (DIGSI-Adressen {dev_key})"):
        a = d87["adr"]

        # -- Tabelle 1: Differentialschutz-Matrix (Hauptschutz-Stromschwellen) --
        st.markdown("**Differentialschutz 87B — Ansprechwert-Matrix**")
        st.caption("Jede Zeile entspricht einem Messsystem (selektive Zone / Checkzone, ggf. "
                   "empfindliche Kennlinie). Id> als Vielfaches von Ino, primär und sekundär. "
                   "Wichtig: Ansprechwert, Stabilisierungsfaktor und Querstabilisierungsfaktor "
                   "einer Zeile besitzen jeweils eine eigene DIGSI-Adresse und sind getrennt "
                   "einzutragen (Spalte DIGSI-Adressen).")
        matrix = [
            ("Selektive Zone (SS)", f"{de(d87['id_ss_f'], 2)}", f"{de(d87['id_ss_prim'], 0)}",
             f"{de(d87['id_ss_sek'], 3)}", f"{de(d87['stab_ss'], 2)}", f"{de(d87['querstab_ss'], 2)}",
             f"Id {a['ID_SS']} · Stab {a['STAB_SS']} · Querstab {a['QUERSTAB_SS']}"),
            ("Checkzone (CZ)", f"{de(d87['id_cz_f'], 2)}", f"{de(d87['id_cz_prim'], 0)}",
             f"{de(d87['id_cz_sek'], 3)}", f"{de(d87['stab_cz'], 2)}", f"{de(d87['querstab_cz'], 2)}",
             f"Id {a['ID_CZ']} · Stab {a['STAB_CZ']} · Querstab {a['QUERSTAB_CZ']}"),
        ]
        if d87["empf_frei"]:
            matrix.append((
                "Selektive Zone empf.", f"{de(d87['id_ss_e'], 2)}", f"{de(d87['id_ss_e_prim'], 0)}",
                f"{de(d87['id_ss_e_sek'], 3)}", f"Is< {de(d87['is_ss_e'], 2)}", "—",
                f"Id {a['ID_SS_EMPF']} · Is< {a['IS_SS_EMPF']}"))
            matrix.append((
                "Checkzone empf.", f"{de(d87['id_cz_e'], 2)}", f"{de(d87['id_cz_e_prim'], 0)}",
                f"{de(d87['id_cz_e_sek'], 3)}", f"Is< {de(d87['is_cz_e'], 2)}", "—",
                f"Id {a['ID_CZ_EMPF']} · Is< {a['IS_CZ_EMPF']}"))
        dfm = pd.DataFrame(matrix, columns=[
            "Messsystem", "Id> [x Ino]", "Id prim. [A]", "Id sek. [A]", "Stab./Is<", "Querstab.",
            "DIGSI-Adressen"])
        st.dataframe(dfm, width="stretch", hide_index=True)

        st.divider()

        # -- Tabelle 2: vollstaendige Parameterliste --------------------------
        st.markdown("**Alle Schutzfunktionen — Parameterliste**")
        rows = []
        # 87B
        if d87["aktiv"]:
            rows.append(("87B", "Stab.-Faktor SS", f"{de(d87['stab_ss'], 2)}", "—", f"Adr.{a['STAB_SS']}"))
            rows.append(("87B", "Id> SS", f"{de(d87['id_ss_prim'], 0)}", "A prim.", f"Adr.{a['ID_SS']}"))
            rows.append(("87B", "Stab.-Faktor CZ", f"{de(d87['stab_cz'], 2)}", "—", f"Adr.{a['STAB_CZ']}"))
            rows.append(("87B", "Id> CZ", f"{de(d87['id_cz_prim'], 0)}", "A prim.", f"Adr.{a['ID_CZ']}"))
            rows.append(("87B", "Querstab. SS", f"{de(d87['querstab_ss'], 2)}", "—", f"Adr.{a['QUERSTAB_SS']}"))
            rows.append(("87B", "Querstab. CZ", f"{de(d87['querstab_cz'], 2)}", "—", f"Adr.{a['QUERSTAB_CZ']}"))
            rows.append(("87B", "Empf. Kennlinie", d87["empf_kennl"], "—", f"Adr.{a['EMPF_KENNL']}"))
            if d87["empf_frei"]:
                rows.append(("87B", "Id> SS empf.", f"{de(d87['id_ss_e_prim'], 0)}", "A prim.",
                             f"Adr.{a['ID_SS_EMPF']}"))
                rows.append(("87B", "Is< SS empf.", f"{de(d87['is_ss_e'], 2)}", "x Ino",
                             f"Adr.{a['IS_SS_EMPF']}"))
                rows.append(("87B", "Id> CZ empf.", f"{de(d87['id_cz_e_prim'], 0)}", "A prim.",
                             f"Adr.{a['ID_CZ_EMPF']}"))
                rows.append(("87B", "Is< CZ empf.", f"{de(d87['is_cz_e'], 2)}", "x Ino",
                             f"Adr.{a['IS_CZ_EMPF']}"))
            rows.append(("87B", "Zusatzkriterium", d87["zusatzkrit"], "—", f"Adr.{a['ZUSATZKRIT']}"))
            rows.append(("87B", "T AUS min.", f"{de(d87['t_aus_min'], 2)}", "s", f"Adr.{a['T_AUS_MIN']}"))
        # 50BF
        if dbf["aktiv"]:
            ab = dbf["adr"]
            rows.append(("50BF", "SVS-Betriebsart", dbf["betriebsart"], "—", f"Adr.{ab['BETRIEBSART']}"))
            rows.append(("50BF", "SVS-BE-Mode", dbf["be_mode"], "—", f"Adr.{ab['BE_MODE']}"))
            rows.append(("50BF", "Stromschwach (SVS-I<)", dbf["i_klein"], "—", f"Adr.{ab['I_KLEIN']}"))
            rows.append(("50BF", "AUS-Wiederholung", dbf["aus_wiederh"], "—", f"Adr.{ab['AUS_WIEDERH']}"))
            rows.append(("50BF", "I> SVS", f"{de(dbf['i_svs_prim'], 0)}", "A prim.", f"Adr.{ab['I_SVS']}"))
            rows.append(("50BF", "I> SVS empf.", f"{de(dbf['i_svs_e_prim'], 0)}", "A prim.",
                         f"Adr.{ab['I_SVS_EMPF']}"))
            rows.append(("50BF", "Stab.-Faktor SVS", f"{de(dbf['stab_svs'], 2)}", "—", f"Adr.{ab['STAB_SVS']}"))
            rows.append(("50BF", "T-SVS-1P", f"{de(dbf['t_1p'], 2)}", "s", f"Adr.{ab['T_1P']}"))
            rows.append(("50BF", "T-SVS-mP", f"{de(dbf['t_mp'], 2)}", "s", f"Adr.{ab['T_MP']}"))
            rows.append(("50BF", "T-SVS-I<", f"{de(dbf['t_ik'], 2)}", "s", f"Adr.{ab['T_IK']}"))
            rows.append(("50BF", "T-AUS-Wiederh.", f"{de(dbf['t_ausw'], 2)}", "s", f"Adr.{ab['T_AUSW']}"))
            rows.append(("50BF", "T-SVS-LS-Störg", f"{de(dbf['t_lsst'], 2)}", "s", f"Adr.{ab['T_LSST']}"))
            rows.append(("50BF", "T-SVS-Impuls", f"{de(dbf['t_imp'], 2)}", "s", f"Adr.{ab['T_IMP']}"))
            rows.append(("50BF", "T-SVS-FrÜb", f"{de(dbf['t_frueb'], 2)}", "s", f"Adr.{ab['T_FRUEB']}"))
            rows.append(("50BF", "T-SVS-FrTo", f"{de(dbf['t_frto'], 2)}", "s", f"Adr.{ab['T_FRTO']}"))
        # Reserve-SVS
        if dres["aktiv"]:
            ar = dres["adr"]
            rows.append(("50BF*", "Reserve-SVS", "Ein", "—", f"Adr.{ar['RES_SVS']}"))
            rows.append(("50BF*", "RES.SVS-I", f"{de(dres['i_prim'], 0)}", "A prim.", f"Adr.{ar['RES_SVS_I']}"))
            rows.append(("50BF*", "RES.SVS-T", f"{de(dres['t'], 2)}", "s", f"Adr.{ar['RES_SVS_T']}"))
        # 50/51
        a5 = d50["adr"]
        if d50["umz_p"] == "Ein":
            rows.append(("50/51", "I>> (prim.)", f"{de(d50['IphHH']['i_prim'], 0)}", "A prim.",
                         f"Adr.{a5['IPH_HH']}"))
            rows.append(("50/51", "T I>>", f"{de(d50['IphHH']['t'], 2)}", "s", f"Adr.{a5['T_IPH_HH']}"))
            rows.append(("50/51", "I> (prim.)", f"{de(d50['IphH']['i_prim'], 0)}", "A prim.",
                         f"Adr.{a5['IPH_H']}"))
            rows.append(("50/51", "T I>", f"{de(d50['IphH']['t'], 2)}", "s", f"Adr.{a5['T_IPH_H']}"))
            rows.append(("50/51", "Ip (prim.)", f"{de(d50['Ip']['i_prim'], 0)}", "A prim.",
                         f"Adr.{a5['IP']}"))
            rows.append(("50/51", "T Ip", f"{de(d50['Ip']['t'], 2)}", "s", f"Adr.{a5['T_IP']}"))
        if d50["umz_e"] == "Ein":
            rows.append(("50N/51N", "IE>> (prim.)", f"{de(d50['IeHH']['i_prim'], 0)}", "A prim.",
                         f"Adr.{a5['IE_HH']}"))
            rows.append(("50N/51N", "T IE>>", f"{de(d50['IeHH']['t'], 2)}", "s", f"Adr.{a5['T_IE_HH']}"))
            rows.append(("50N/51N", "IE> (prim.)", f"{de(d50['IeH']['i_prim'], 0)}", "A prim.",
                         f"Adr.{a5['IE_H']}"))
            rows.append(("50N/51N", "T IE>", f"{de(d50['IeH']['t'], 2)}", "s", f"Adr.{a5['T_IE_H']}"))
            rows.append(("50N/51N", "IEp (prim.)", f"{de(d50['Iep']['i_prim'], 0)}", "A prim.",
                         f"Adr.{a5['IEP']}"))
            rows.append(("50N/51N", "T IEp", f"{de(d50['Iep']['t'], 2)}", "s", f"Adr.{a5['T_IEP']}"))
        # Ueberwachung
        au = dueb["adr"]
        rows.append(("Überw.", "Id-Überwachung", dueb["id_ueberw"], "—", f"Adr.{au['ID_UEBERW']}"))
        rows.append(("Überw.", "T-Id-Überw.", f"{de(dueb['t_id_ueberw'], 2)}", "s", f"Adr.{au['T_ID_UEBERW']}"))
        rows.append(("Überw.", "Id> Überw. SS", f"{de(dueb['id_ueb_ss'], 2)}", "x Ino",
                     f"Adr.{au['ID_UEBERW_SS']}"))
        rows.append(("Überw.", "Id> Überw. CZ", f"{de(dueb['id_ueb_cz'], 2)}", "x Ino",
                     f"Adr.{au['ID_UEBERW_CZ']}"))
        rows.append(("Überw.", "Reaktion Id-Überw. SS", dueb["reak_ss"], "—", f"Adr.{au['REAK_SS']}"))
        rows.append(("Überw.", "Reaktion Id-Überw. CZ", dueb["reak_cz"], "—", f"Adr.{au['REAK_CZ']}"))
        rows.append(("Überw.", "TR-Laufzeit", f"{de(dueb['tr_laufzeit'], 2)}", "s", f"Adr.{au['TR_LAUFZEIT']}"))
        rows.append(("Überw.", "LS-Überw.-Zeit", f"{de(dueb['ls_ueberw_zeit'], 2)}", "s",
                     f"Adr.{au['LS_UEBERW_ZEIT']}"))
        # Anlagendaten
        rows.append(("Anlage", "TAUSKOM", f"{de(KS.tauskom_def, 2)}", "s", f"Adr.{KS.ADR_get('TAUSKOM')}"))
        rows.append(("Anlage", "Nennfrequenz", f"{f_netz}", "Hz", f"Adr.{KS.ADR_get('NENNFREQUENZ')}"))

        dft = pd.DataFrame(rows, columns=["ANSI", "Parameter", "Sollwert", "Einheit", "DIGSI-Adresse"])
        st.dataframe(dft, width="stretch", hide_index=True)
        st.caption("Primärwerte beziehen sich auf den Bezugsstrom Ino (87B) bzw. den "
                   "Abzweig-Nennstrom In (SVS, Reserve, 50/51); Sekundärwerte gelten für den "
                   "Referenzwandler. Physikalische IEC-Größen (A, s) sind auf andere "
                   "Relaisfamilien übertragbar, die SIPROTEC-Adressen dienen als nachvollziehbare "
                   "Berechnungsgrundlage. 50BF* kennzeichnet den autarken Reserve-SVS der "
                   "Feldeinheit.")
