"""
tab_trafo.py — Streamlit-UI für Transformatorschutz
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg
"""

import pandas as pd
import streamlit as st

import konstanten as K
from calc_trafo import berechne_alle, empfehlung_IHH_OS


# ── Farbkodierung (explizite Textfarben -> auch im Dark-Theme lesbar) ─────────
_CSS = """
<style>
/* Einklappbare Sektionen (st.expander) durchgehend HSU-blau */
[data-testid="stExpander"] summary {
    background: #2E5A87 !important;
    border-radius: 6px !important;
    padding: 5px 12px !important;
}
[data-testid="stExpander"] summary:hover { background: #27496e !important; }
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: #ffffff !important; font-weight: 600 !important; font-size: 0.92rem !important;
}
[data-testid="stExpander"] summary svg { fill: #ffffff !important; color: #ffffff !important; }
[data-testid="stExpander"] details { border: none !important; }

.result-box {
    background: #eef3f8; color: #14203a;
    border-left: 4px solid #2E5A87; border-radius: 6px;
    padding: 10px 14px; margin-bottom: 8px;
}
.result-box .val { font-size: 1.2rem; font-weight: 700; color: #14203a; font-family: monospace; }
.result-box .lbl { font-size: 0.76rem; color: #43526b; }
.result-box .sub { font-size: 0.74rem; color: #5d6b82; margin-top: 2px; }
.warn-box {
    background: #fff4d6; color: #5b4a00;
    border-left: 4px solid #f4a800; border-radius: 6px;
    padding: 10px 14px; font-size: 0.86rem; margin-bottom: 8px;
}
.off-box {
    background: #fbe3ea; color: #7a0024;
    border-left: 4px solid #A50034; border-radius: 6px;
    padding: 10px 14px; font-size: 0.86rem; margin-bottom: 8px;
}
.off-box b { color: #A50034; }
.info-box {
    background: #e7f3ec; color: #14502b;
    border-left: 4px solid #2e7d32; border-radius: 6px;
    padding: 10px 14px; font-size: 0.86rem; margin-bottom: 8px;
}
.pill { display:inline-block; padding:2px 9px; border-radius:11px;
        font-size:0.75rem; font-weight:700; }
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
        unsafe_allow_html=True,
    )


def _section(title, expanded=True):
    """Einklappbare, blau gestylte Sektion. Verwendung: with _section('...'):"""
    return st.expander(title, expanded=expanded)


def _pill(status):
    return f'<span class="pill {_PILL_CLASS.get(status,"pill-na")}">{status}</span>'


def _hreg(key):
    """Hersteller-Hinweis (Range + Begründung + Eintrag-Adresse) unter einem Regler."""
    h = K.HERST.get(key)
    if not h:
        return
    adr = h.get("adr")
    pin = (f'<br>📍 <b>Eintragen unter:</b> {adr}' if adr
           else '<br>📍 <b>Rechengröße</b> (kein direkter DIGSI-Parameter, fließt in die Sollwerte ein)')
    st.markdown(
        f'<div style="font-size:0.72rem;color:#5d6b82;margin:-6px 0 10px;line-height:1.25;">'
        f'<b>Hersteller:</b> {h["range"]}<br>{h["grund"]}{pin}</div>',
        unsafe_allow_html=True)


# ── Hauptfunktion ─────────────────────────────────────────────────────────────

def show():
    st.markdown(_CSS, unsafe_allow_html=True)

    # ══════════════════════ EINGABEN (einklappbar) ══════════════════════
    with _section("Eingaben — Grunddaten, Stromwandler, Netzparameter"):
        ci1, ci2, ci3 = st.columns(3, gap="medium")
        with ci1:
            st.caption("**Transformator-Grunddaten**")
            Sn    = st.number_input("Sn — Bemessungsleistung [MVA]", 0.1, value=16.0, step=0.5, format="%.1f")
            UN_OS = st.number_input("UN OS — Oberspannung [kV]", 1.0, value=110.0, step=1.0, format="%.1f")
            UN_US = st.number_input("UN US — Unterspannung [kV]", 0.4, value=10.0, step=0.1, format="%.1f")
            uk    = st.number_input("uk — Kurzschlussspannung [%]", 1.0, 25.0, value=11.5, step=0.1, format="%.1f")
            vg    = st.selectbox("Schaltgruppe", K.SCHALTGRUPPEN, index=0)
            stp_pm = st.number_input("Stufensteller +/- [%]", 0, 40, value=10, step=1)
        with ci2:
            st.caption("**Stromwandler (primär / sekundär)**")
            c1, c2 = st.columns(2)
            with c1:
                CT_OS_P = st.number_input("CT OS prim. [A]", 1, value=100, step=1)
                CT_US_P = st.number_input("CT US prim. [A]", 1, value=1000, step=1)
            with c2:
                CT_OS_S = st.selectbox("CT OS sek. [A]", [1, 5], index=0)
                CT_US_S = st.selectbox("CT US sek. [A]", [1, 5], index=0)
            # Erder-Wandler zuerst auswählen, danach (nur falls vorhanden) die Wandlerdaten abfragen.
            ie_wdl = st.checkbox("Sternpunkt-Wandler (IE-CT) vorhanden", value=True)
            if ie_wdl:
                ce1, ce2 = st.columns(2)
                with ce1:
                    CT_E_P = st.number_input("CT Erder prim. [A]", 1, value=400, step=1)
                with ce2:
                    CT_E_S = st.selectbox("CT Erder sek. [A]", [1, 5], index=0)
            else:
                CT_E_P, CT_E_S = 0, 1
            # Spannungsmesseingänge (Gerätevariante mit VT) — analog IE-Wandler.
            vt_vorhanden = st.checkbox(
                "Spannungsmesseingänge (VT) vorhanden", value=False,
                help="7UT613 nur mit Spannungseingang-Variante. Voraussetzung für "
                     "27/59, Frequenzschutz (81) und Übererregungsschutz (24).")
            if vt_vorhanden:
                cv1, cv2 = st.columns(2)
                with cv1:
                    VT_P = st.number_input("VT prim. [kV]", 0.0, value=float(UN_US),
                                           step=0.1, format="%.2f")
                with cv2:
                    VT_S = st.selectbox("VT sek. [V]", K.VT_Sek_Optionen, index=1)
            else:
                VT_P, VT_S = 0.0, 110
        with ci3:
            st.caption("**Netzparameter**")
            stp_OS = st.selectbox("Sternpunktbehandlung OS", K.STERNPUNKT_OPTIONEN, index=2)
            stp_US = st.selectbox("Sternpunktbehandlung US", K.STERNPUNKT_OPTIONEN, index=1)
            Ik_OS  = st.number_input("Ik″ max OS [kA]", 0.0, value=10.0, step=0.5, format="%.1f")
            Ik_US  = st.number_input("Ik″ max US [kA]", 0.0, value=8.0, step=0.5, format="%.1f")
            Ik_min_OS = st.number_input(
                "Ik min OS (Schutzgebiet-Ende) [kA]", 0.0, value=0.0, step=0.1, format="%.2f",
                help="Minimaler Kurzschlussstrom nach DIN EN 60909-0 (c=0,95). "
                     "0 = nicht vorhanden, dann Näherung 0,3·Ik″max OS.")
            bf_aktiv = st.checkbox(
                "Leistungsschalterversagerschutz (50BF) projektiert", value=True,
                help="Adr.170 SCHALTERVERSAG. Stromflussbasiert, benötigt keine Spannung.")
            bf_zwei = st.checkbox(
                "50BF zweistufig (T1 lokal + T2 Sammelschiene)", value=False,
                help="Aus = einstufig, nur T2 (Adr.7016). Ein = zusätzlich T1 (Adr.7015).",
                disabled=not bf_aktiv)

    # Erweiterte Parameter — eigenständige (NICHT verschachtelte) Sektion
    with _section("Erweiterte Parameter (Voreinstellungen nach SIPROTEC 7UT6xx — frei änderbar)", expanded=False):
        st.caption("ℹ️ Unter jedem Regler steht der vom Hersteller empfohlene Wert/Range "
                   "und die Begründung. So ist nachvollziehbar, was die Voreinstellung bezweckt.")
        e1, e2, e3 = st.columns(3)
        with e1:
            st.markdown("**87T Differential**")
            k_DIFF  = st.slider("I-DIFF> [I/InO]", 0.10, 0.40, K.I_DIFF_def, 0.05)
            _hreg("I_DIFF")
            k_DIFFH = st.slider("I-DIFF>> [I/InO]", 5.0, 15.0, K.I_DIFF_HH_def, 0.1)
            _hreg("I_DIFF_HH")
            steig1  = st.slider("Steigung 1", 0.20, 0.40, K.Steigung_1_def, 0.05)
            _hreg("Steigung_1")
            steig2  = st.slider("Steigung 2", 0.40, 0.60, K.Steigung_2_def, 0.05)
            _hreg("Steigung_2")
            fp2     = st.slider("Fußpunkt 2 [I/InO]", 2.0, 3.5, K.Fusspunkt_2_def, 0.1)
            _hreg("Fusspunkt_2")
            harm2   = st.slider("2. Harmonische [%]", 10, 30, int(K.Harm_2_def*100), 1) / 100
            _hreg("Harm_2")
        with e2:
            st.markdown("**50/51 + 49 + 46**")
            f_I    = st.slider("I> Phase [I/InS]", 1.0, 3.0, K.f_I_Ph_def, 0.1)
            _hreg("f_I_Ph")
            t_I    = st.number_input("t I> [s]", 0.05, 2.0, K.t_I_Ph_def, 0.05, format="%.2f")
            _hreg("t_I_Ph")

            # I>> OS: Auto aus 1,2/uk bzw. Ik″ max US (mit Override)
            f_IHH_OS_emp = empfehlung_IHH_OS(
                dict(nT=(UN_OS/UN_US if UN_US else 0),
                     IN_OS_prim=(Sn*1e6/(1.7320508*UN_OS*1e3) if UN_OS else 0)),
                dict(k_S_IGG=K.k_S_IGG, Ik_max_US_kA=Ik_US, uk_pct=uk))
            auto_OS = st.checkbox(f"I>> OS automatisch ({f_IHH_OS_emp:g} ×IN)", value=True,
                                  help="Speiseseite: Empfehlung 1,2·Ik″ max US (auf OS bezogen).")
            if auto_OS:
                f_IHH_OS = f_IHH_OS_emp
                st.caption(f"➜ I>> OS = **{f_IHH_OS_emp:g} ×IN** (auto). "
                           f"{K.HERST['f_I_Ph_HH_OS']['grund']}")
            else:
                f_IHH_OS = st.slider("I>> Phase OS [I/InS]", 4.0, 16.0,
                                     float(round(f_IHH_OS_emp, 1)), 0.5)
                _hreg("f_I_Ph_HH_OS")
            f_IHH_US = st.slider("I>> Phase US [I/InS]", 4.0, 12.0, K.f_I_Ph_HH_def, 0.5)
            _hreg("f_I_Ph_HH_US")
            t_IHH  = st.number_input("t I>> [s]", 0.0, 1.0, K.t_I_Ph_HH_def, 0.05, format="%.2f")
            _hreg("t_I_Ph_HH")

            kfak   = st.slider("49  k-Faktor [x IN]", 1.0, 1.5, K.k_Faktor_def, 0.05)
            _hreg("k_Faktor")
            tau    = st.slider("49  τ_th [min]", 2, 240, int(K.tau_Trafo_def), 1)
            _hreg("tau_min")
            i2zul  = st.slider("46  I2 zul. [I/InS]", 0.08, 0.30, K.I2_zul_def, 0.01)
            _hreg("I2_zul")
        with e3:
            st.markdown("**Engineering-Margen**")
            kSI    = st.slider("k_S (I>)  [-]", 1.1, 1.4, K.k_S_I, 0.05)
            _hreg("k_S_I")
            kSIGG  = st.slider("k_S (I>>) [-]", 1.1, 1.4, K.k_S_IGG, 0.05)
            _hreg("k_S_IGG")
            gamma  = st.slider("γ Empfindlichkeit [-]", 1.2, 2.0, K.gamma_Ikmin, 0.1)
            _hreg("gamma")
            inrush = st.slider("Inrush-Faktor [x IN]", 6, 12, int(K.Inrush_Faktor), 1)
            _hreg("Inrush_Faktor")

        # Spannungs-/Frequenz-/Übererregungsschutz (nur relevant mit VT-Variante)
        U_lt_v, U_ltlt_v = K.U_lt_def, K.U_ltlt_def
        U_gt_v, U_gtgt_v = K.U_gt_def, K.U_gtgt_def
        f_lt_v, f_ltlt_v   = K.f_lt_def, K.f_ltlt_def
        f_ltltlt_v, f_gt_v = K.f_ltltlt_def, K.f_gt_def
        Uf_gt_v, Uf_gtgt_v = K.Uf_gt_def, K.Uf_gtgt_def
        tU_lt_v, tU_ltlt_v, tU_gt_v, tU_gtgt_v = (K.t_U_lt_def, K.t_U_ltlt_def,
                                                  K.t_U_gt_def, K.t_U_gtgt_def)
        tf_lt_v, tf_ltlt_v, tf_ltltlt_v, tf_gt_v = (K.t_f_lt_def, K.t_f_ltlt_def,
                                                    K.t_f_ltltlt_def, K.t_f_gt_def)
        tUf_gt_v, tUf_gtgt_v = K.t_Uf_gt_def, K.t_Uf_gtgt_def
        rueckf_v = K.U_Rueckfall_def
        if vt_vorhanden:
            st.markdown("---")
            st.caption("Spannungs-, Frequenz- und Übererregungsschutz (nur VT-Variante). "
                       "Je Stufe Ansprechwert und Verzögerungszeit.")
            v1, v2, v3 = st.columns(3)
            with v1:
                st.markdown("**27/59 Spannung [× UnS] + t [s]**")
                U_lt_v   = st.slider("U<", 0.50, 0.95, K.U_lt_def, 0.01)
                tU_lt_v  = st.number_input("t U< [s]", 0.0, 100.0, K.t_U_lt_def, 0.1, format="%.2f")
                _hreg("U_lt")
                U_ltlt_v = st.slider("U<<", 0.40, 0.90, K.U_ltlt_def, 0.01)
                tU_ltlt_v = st.number_input("t U<< [s]", 0.0, 100.0, K.t_U_ltlt_def, 0.1, format="%.2f")
                U_gt_v   = st.slider("U>", 1.05, 1.30, K.U_gt_def, 0.01)
                tU_gt_v  = st.number_input("t U> [s]", 0.0, 100.0, K.t_U_gt_def, 0.1, format="%.2f")
                _hreg("U_gt")
                U_gtgt_v = st.slider("U>>", 1.20, 1.50, K.U_gtgt_def, 0.01)
                tU_gtgt_v = st.number_input("t U>> [s]", 0.0, 100.0, K.t_U_gtgt_def, 0.1, format="%.2f")
                _hreg("U_gtgt")
                rueckf_v = st.number_input("Rückfallverh. (Adr.5217/5317)", 0.90, 1.00,
                                           K.U_Rueckfall_def, 0.01, format="%.2f")
            with v2:
                st.markdown("**81 Frequenz [Hz] + t [s]**")
                f_lt_v     = st.slider("f<", 47.0, 49.9, K.f_lt_def, 0.1)
                tf_lt_v    = st.number_input("t f< [s]", 0.0, 100.0, K.t_f_lt_def, 0.1, format="%.2f")
                _hreg("f_lt")
                f_ltlt_v   = st.slider("f<<", 46.0, 49.0, K.f_ltlt_def, 0.1)
                tf_ltlt_v  = st.number_input("t f<< [s]", 0.0, 100.0, K.t_f_ltlt_def, 0.1, format="%.2f")
                f_ltltlt_v = st.slider("f<<<", 45.0, 48.5, K.f_ltltlt_def, 0.1)
                tf_ltltlt_v = st.number_input("t f<<< [s]", 0.0, 100.0, K.t_f_ltltlt_def, 0.1, format="%.2f")
                f_gt_v     = st.slider("f>", 50.1, 53.0, K.f_gt_def, 0.1)
                tf_gt_v    = st.number_input("t f> [s]", 0.0, 100.0, K.t_f_gt_def, 0.1, format="%.2f")
            with v3:
                st.markdown("**24 Übererregung [× (U/f)N] + t [s]**")
                _uf_off = VT_P <= 0
                Uf_gt_v   = st.slider("U/f >", 1.00, 1.20, K.Uf_gt_def, 0.01, disabled=_uf_off)
                tUf_gt_v  = st.number_input("t U/f > [s]", 0.0, 60.0, K.t_Uf_gt_def, 0.5, format="%.1f", disabled=_uf_off)
                _hreg("Uf_gt")
                Uf_gtgt_v = st.slider("U/f >>", 1.20, 1.60, K.Uf_gtgt_def, 0.01, disabled=_uf_off)
                tUf_gtgt_v = st.number_input("t U/f >> [s]", 0.0, 20.0, K.t_Uf_gtgt_def, 0.5, format="%.1f", disabled=_uf_off)
                if _uf_off:
                    st.caption("⚠️ 24 benötigt VT prim. > 0.")

        # 50BF Stromschwelle und Zeitbilanz
        I_BF_v   = K.I_BF_def
        tLS_v, tRF_v, tSi_v = K.t_LS_aus_def, K.t_RF_strom_def, K.t_sich_BF_def
        if bf_aktiv:
            st.markdown("---")
            st.caption("Leistungsschalterversagerschutz 50BF — Zeitbilanz für T2 (Adr.7016).")
            b1, b2, b3, b4 = st.columns(4)
            with b1:
                I_BF_v = st.slider("50BF  I> [x IN]", 0.05, 0.30, K.I_BF_def, 0.01)
                _hreg("I_BF")
            with b2:
                tLS_v = st.number_input("t LS-Aus [s]", 0.02, 0.20, K.t_LS_aus_def, 0.005, format="%.3f")
            with b3:
                tRF_v = st.number_input("t Rückfall [s]", 0.01, 0.10, K.t_RF_strom_def, 0.005, format="%.3f")
            with b4:
                tSi_v = st.number_input("t Sicherheit [s]", 0.02, 0.20, K.t_sich_BF_def, 0.005, format="%.3f")
            st.caption(f"➜ T2 = {tLS_v + tRF_v + tSi_v:.3f} s"
                       + (f" · T1 = {tLS_v + tRF_v + tSi_v:.3f} s (zweistufig)" if bf_zwei else " (einstufig, T1 = ∞)"))

    # ══════════════════════ BERECHNUNG ══════════════════════
    p = dict(
        Sn_MVA=Sn, UN_OS_kV=UN_OS, UN_US_kV=UN_US, uk_pct=uk,
        Schaltgruppe=vg, Stufensteller_pm=stp_pm,
        CT_OS_Prim=CT_OS_P, CT_OS_Sek=CT_OS_S,
        CT_US_Prim=CT_US_P, CT_US_Sek=CT_US_S,
        CT_E_Prim=CT_E_P, CT_E_Sek=CT_E_S, IE_Wandler=ie_wdl,
        stp_OS=stp_OS, stp_US=stp_US, Ik_max_OS_kA=Ik_OS, Ik_max_US_kA=Ik_US,
        Ik_min_OS_kA=Ik_min_OS,
        I_DIFF=k_DIFF, I_DIFF_HH=k_DIFFH, Steigung_1=steig1, Steigung_2=steig2,
        Fusspunkt_2=fp2, Harm_2=harm2,
        f_I_Ph=f_I, t_I_Ph=t_I, f_I_Ph_HH_OS=f_IHH_OS, f_I_Ph_HH_US=f_IHH_US,
        t_I_Ph_HH=t_IHH,
        k_Faktor=kfak, tau_min=tau, I2_zul=i2zul,
        k_S_I=kSI, k_S_IGG=kSIGG, gamma=gamma, Inrush_Faktor=inrush,
        # Spannungsmesseingänge + 27/59/81/24
        VT_vorhanden=vt_vorhanden, VT_Prim_kV=VT_P, VT_Sek_V=VT_S,
        U_lt=U_lt_v, U_ltlt=U_ltlt_v, U_gt=U_gt_v, U_gtgt=U_gtgt_v,
        t_U_lt=tU_lt_v, t_U_ltlt=tU_ltlt_v, t_U_gt=tU_gt_v, t_U_gtgt=tU_gtgt_v,
        U_Rueckfall=rueckf_v,
        f_lt=f_lt_v, f_ltlt=f_ltlt_v, f_ltltlt=f_ltltlt_v, f_gt=f_gt_v,
        t_f_lt=tf_lt_v, t_f_ltlt=tf_ltlt_v, t_f_ltltlt=tf_ltltlt_v, t_f_gt=tf_gt_v,
        Uf_gt=Uf_gt_v, Uf_gtgt=Uf_gtgt_v,
        t_Uf_gt=tUf_gt_v, t_Uf_gtgt=tUf_gtgt_v,
        # Leistungsschalterversagerschutz 50BF
        BF_aktiv=bf_aktiv, BF_zweistufig=bf_zwei,
        I_BF=I_BF_v, t_LS_aus=tLS_v, t_RF_strom=tRF_v, t_sich_BF=tSi_v,
    )
    e = berechne_alle(p)
    g = e["grund"]

    # ══════════════════════ AMPEL-ZUSAMMENFASSUNG ══════════════════════
    plaus = e["plausibilitaet"]
    n_ok  = sum(1 for c in plaus if c["status"] == "OK")
    n_hin = sum(1 for c in plaus if c["status"] == "Hinweis")
    n_bad = sum(1 for c in plaus if c["status"] in ("Prüfen!", "Fehlt"))
    st.markdown(
        f'<div style="margin:0.6rem 0;">Plausibilität: '
        f'{_pill("OK")} {n_ok} &nbsp; {_pill("Hinweis")} {n_hin} &nbsp; '
        f'{_pill("Prüfen!")} {n_bad}</div>', unsafe_allow_html=True)

    # ══════════════════════ HANDLUNGSEMPFEHLUNGEN (zentral) ══════════════════════
    todo = [c for c in plaus if c["status"] in ("Prüfen!", "Fehlt") and c["korrektur"]]
    hinw = [c for c in plaus if c["status"] == "Hinweis" and c["korrektur"]]
    if todo:
        items = "".join(
            f'<li style="margin-bottom:6px;"><b>{c["pruefung"]}</b> '
            f'(Ergebnis: {c["ergebnis"]})<br>'
            f'<span style="color:#7a0024;">➜ {c["korrektur"]}</span></li>'
            for c in todo)
        st.markdown(
            f'<div class="off-box"><b>🔴 Handlungsbedarf — konkret zu verstellen:</b>'
            f'<ul style="margin:6px 0 0 0;padding-left:18px;">{items}</ul></div>',
            unsafe_allow_html=True)
    if hinw:
        items = "".join(
            f'<li style="margin-bottom:6px;"><b>{c["pruefung"]}</b><br>'
            f'<span style="color:#8a5b00;">➜ {c["korrektur"]}</span></li>'
            for c in hinw)
        st.markdown(
            f'<div class="warn-box"><b>🟡 Hinweise (prüfen, ggf. anpassen):</b>'
            f'<ul style="margin:6px 0 0 0;padding-left:18px;">{items}</ul></div>',
            unsafe_allow_html=True)
    if not todo and not hinw:
        st.markdown(
            '<div class="info-box">🟢 <b>Alle Plausibilitätsprüfungen bestanden.</b> '
            'Die berechneten Werte sind in sich konsistent und entsprechen der '
            'Hersteller-/FNN-Methodik. Bewusste Abweichungen bleiben dir überlassen.</div>',
            unsafe_allow_html=True)

    # ── Funktions-Aktivierung je Sternpunktbehandlung (auf einen Blick) ──────────
    fn87, fnerde, fnu0 = e["87N"], e["50N51N"], e["U0"]
    def _fnpill(on, title=""):
        cls = "pill-ok" if on else "pill-na"
        txt = "aktiv" if on else "aus"
        t = f' title="{title}"' if title else ""
        return f'<span class="pill {cls}"{t}>{txt}</span>'
    grund87 = "" if fn87["aktiv"] else fn87.get("grund", "")
    st.markdown(
        '<div style="margin:0.1rem 0 0.7rem;font-size:0.82rem;color:#43526b;">'
        'Erdschluss-Funktionen je Sternpunktbehandlung: &nbsp; '
        '87N ' + _fnpill(fn87["aktiv"], grund87) + ' &nbsp;·&nbsp; '
        '50N/51N ' + _fnpill(fnerde["anwendbar"]) + ' &nbsp;·&nbsp; '
        'U0-Erfassung ' + _fnpill(fnu0["aktiv"])
        + ' &nbsp;<span style="color:#8a93a3;">(Details im Abschnitt „Erdschluss-/Erdfehlerschutz“)</span>'
        '</div>', unsafe_allow_html=True)

    # ══════════════════════ BERECHNETE GRUNDGRÖSSEN ══════════════════════
    with _section("Berechnete Grundgrößen"):
        g1, g2, g3 = st.columns(3)
        with g1:
            _metric("IN OS primär",   f"{g['IN_OS_prim']:.2f} A")
            _metric("IN OS sekundär", f"{g['IN_OS_sek']:.4f} A", f"÷ kCT_OS = {g['kCT_OS']:.0f}")
            _metric("STW-Anpassung OS", f"{g['I_an_OS']:.3f}", "I_an = CT_sek / IN_sek  (Soll 0,5–2,0)")
        with g2:
            _metric("IN US primär",   f"{g['IN_US_prim']:.2f} A")
            _metric("IN US sekundär", f"{g['IN_US_sek']:.4f} A", f"÷ kCT_US = {g['kCT_US']:.0f}")
            _metric("STW-Anpassung US", f"{g['I_an_US']:.3f}", "I_an = CT_sek / IN_sek  (Soll 0,5–2,0)")
        with g3:
            _metric("Übersetzung nT",   f"{g['nT']:.3f}", "= UN_OS / UN_US")
            _metric("kCT Erder",        f"{g['kCT_E']:.0f}")
            _metric("Bezugsstrom IN_Obj sek.", f"{g['IN_Obj_sek']:.4f} A", "= max(IN_OS_sek, IN_US_sek) → 87T")

    # ══════════════════════ ANSI 87T — DIFFERENTIALSCHUTZ ══════════════════════
    r = e["87T"]
    with _section("ANSI 87T — Differentialschutz"):
        d1, d2 = st.columns(2)
        with d1: _metric("I-DIFF> sekundär", f"{r['I_DIFF_Anspr_sek_A']:.4f} A", f"= {p['I_DIFF']*100:.0f}% × IN_Obj")
        with d2: _metric("I-DIFF> primär OS", f"{r['I_DIFF_Anspr_prim_A']:.2f} A", "= Faktor × IN_OS_prim")
        df87 = pd.DataFrame([{
            "Parameter": x["name"],
            "Eingabe": f"{x['faktor']:g}",
            "Einheit": x["einheit"],
            "A sek.": f"{x['wert_sek']:.4f}" if x["wert_sek"] is not None else "—",
            "A prim. OS": f"{x['wert_prim']:.2f}" if x["wert_prim"] is not None else "—",
            "Empfehlung": f"{x['empfehlung']:g}" if x["empfehlung"] is not None else "—",
            "Status": f"{_AMPEL_EMOJI.get(x['status'],'')} {x['status']}",
            "Adresse": x["adresse"],
        } for x in r["rows"]])
        st.dataframe(df87, width="stretch", hide_index=True)
        st.caption("Empfehlung (Spalte) dynamisch aus Stufensteller / uk / Sn. "
                   "Status: 🟢 identisch · 🟡 Abweichung < 20 % · 🔴 Abweichung ≥ 20 %. "
                   "Bewusste Abweichung nach Schutzphilosophie zulässig (7UT613 Hdb. 2.2.7).")

    # ══════════════════════ ERDSCHLUSS- / ERDFEHLERSCHUTZ ══════════════════════
    f87n = e["87N"]
    erde = e["50N51N"]
    u0 = e["U0"]
    with _section("Erdschluss- / Erdfehlerschutz (87N · 50N/51N · U0)"):
        if f87n["aktiv"]:
            c1, c2, c3 = st.columns(3)
            with c1: _metric("87N I-EDS> sek.", f"{f87n['I_EDS_sek_A']:.4f} A", f"= {f87n['I_EDS_faktor']*100:.0f}% × IN_OS_sek")
            with c2: _metric("87N I-EDS> prim.", f"{f87n['I_EDS_prim_A']:.2f} A", "Adr.1311")
            with c3: _metric("T I-EDS>", f"{f87n['T_I_EDS_s']:.2f} s", "Adr.1312A")
        else:
            st.markdown(f'<div class="off-box">🔴 <b>87N (EDS) deaktiviert</b><br>{f87n["grund"]}</div>',
                        unsafe_allow_html=True)

        if erde["anwendbar"]:
            c1, c2 = st.columns(2)
            with c1: _metric("50N/51N  IE>",  f"{erde['IE_sek']:.2f} A sek.", f"= {erde['IE_prim']:.1f} A prim · t = {erde['t_IE']:.2f} s")
            with c2: _metric("50N/51N  IE>>", f"{erde['IEHH_sek']:.2f} A sek.", f"= {erde['IEHH_prim']:.1f} A prim · t = {erde['t_IEHH']:.2f} s")

        if u0["aktiv"]:
            net = "kompensiert" if u0["kompensiert"] else "isoliert"
            cos = (f"<br>cos-φ-Stufe (wattmetrisch): {u0['cos_phi_pct']:.0f}% IE_kap · "
                   f"t = {u0['t_cos_phi']:.1f} s — nur kompensiert" if u0["kompensiert"] else "")
            st.markdown(
                f'<div class="info-box">🟢 <b>U0-Erdschlusserfassung aktiv ({net}es Netz)</b><br>'
                f'U0&gt; Meldestufe: {u0["U0_Meld_pu"]*100:.0f}% UN/√3 = {u0["U0_Meld_V"]:.0f} V · t = {u0["t_Meld"]:.0f} s<br>'
                f'U0&gt;&gt; Abschaltstufe: {u0["U0_Absch_pu"]*100:.0f}% UN/√3 = {u0["U0_Absch_V"]:.0f} V · t = {u0["t_Absch"]:.0f} s'
                f'{cos}<br><span style="font-size:0.78rem;color:#3a6b48">Hinweis: nicht im 7UT613 enthalten → '
                f'separates 7SJ64 / zentrale Erdschlusserfassung. Quelle: FNN-Leitfaden.</span></div>',
                unsafe_allow_html=True)

    # ══════════════════════ ANSI 50/51 — ÜBERSTROMZEITSCHUTZ PHASEN ══════════════════════
    umz = e["5051"]
    with _section("ANSI 50/51 — Überstromzeitschutz Phasen (OS + US)"):
        dfu = pd.DataFrame([
            ("I> OS (51)",  f"{umz['f_I']:g}",       "I/InS", f"{umz['OS']['I_sek']:.4f}",   f"{umz['OS']['I_prim']:.1f}",   f"{umz['t_I']:.2f}"),
            ("I>> OS (50)", f"{umz['f_IHH_OS']:g}",   "I/InS", f"{umz['OS']['IHH_sek']:.4f}", f"{umz['OS']['IHH_prim']:.1f}", f"{umz['t_IHH']:.2f}"),
            ("I> US (51)",  f"{umz['f_I']:g}",        "I/InS", f"{umz['US']['I_sek']:.4f}",   f"{umz['US']['I_prim']:.1f}",   f"{umz['t_I']:.2f}"),
            ("I>> US (50)", f"{umz['f_IHH_US']:g}",   "I/InS", f"{umz['US']['IHH_sek']:.4f}", f"{umz['US']['IHH_prim']:.1f}", f"{umz['t_IHH']:.2f}"),
        ], columns=["Funktion", "Faktor", "Einheit", "I_Soll [A sek.]", "I_Soll [A prim.]", "t [s]"])
        st.dataframe(dfu, width="stretch", hide_index=True)
        st.caption(f"I>> OS automatisch aus 1,2·Ik″ max US (Speiseseite, Empfehlung {umz['f_IHH_OS_emp']:g} ×IN). "
                   "I>> US wird gegen die nachgelagerte Staffelung bemessen — beide Seiten getrennt einstellbar.")
        st.caption(f"Rush-Stabilisierung Phasen (2. Harm.): {umz['rush_2H_pct']:.0f}% · "
                   "UMZ = definite time (feste Verzögerung). AMZ-Kennlinie nach IEC 60255 als Erweiterung vorgesehen.")

    # ══════════════════════ BEMESSUNGS-ENGINEERING ══════════════════════
    b = e["bemessung"]
    with _section("Bemessungs-Engineering — Stufenwahl + Empfindlichkeit"):
        st.caption("Kein Ersatz für eine vollständige Kurzschlussberechnung — verifiziert die "
                   "Stufenwahl gegen max. Last, Inrush und minimalen Fehlerstrom. Bezugsseite OS.")
        dfb = pd.DataFrame([
            ("I_max_Last (OS)",            f"{b['I_max_Last_prim']:.1f} A prim.", "—", "Default 1,2 × IN_OS"),
            ("I_k_min (Schutzgebiet-Ende)",f"{b['I_k_min_prim']:.0f} A prim.", "—", b['I_k_min_quelle']),
            ("I> Empfehlung = k_S · I_max_Last", f"{b['I_emp_prim']:.1f} A prim.",
                f"{_AMPEL_EMOJI[b['I_status']]} {b['I_status']}",
                b['korr_I'] if b['korr_I'] else f"gewählt {b['I_gewaehlt_prim']:.1f} A ≥ Empfehlung ✓"),
            ("I>> Empfehlung = max(k_S·Ik″ max US@OS ; Inrush·IN)", f"{b['IHH_emp_prim']:.0f} A prim.",
                f"{_AMPEL_EMOJI[b['IHH_status']]} {b['IHH_status']}",
                b['korr_IHH'] if b['korr_IHH'] else f"gewählt {b['IHH_gewaehlt_prim']:.0f} A ≥ Empfehlung ✓ · maßgebend: {b['massgebend']}"),
            ("Empfindlichkeit I_k_min / I> ≥ γ", f"{b['empfind']:.2f}  (γ = {b['gamma']})",
                f"{_AMPEL_EMOJI[b['empfind_status']]} {b['empfind_status']}",
                b['korr_emp'] if b['korr_emp'] else "I_k_min regt I> sicher an ✓"),
        ], columns=["Größe", "Wert", "Status", "Korrektur / Kommentar"])
        st.dataframe(dfb, width="stretch", hide_index=True)

    # ══════════════════════ ANSI 49 (THERMISCH) + ANSI 46 (SCHIEFLAST) ══════════════════════
    b49, b46 = e["49"], e["46"]
    with _section("ANSI 49 (thermisch) + ANSI 46 (Schieflast)"):
        t1, t2, t3 = st.columns(3)
        with t1:
            _metric("49  I_max_zul sek.", f"{b49['I_max_zul_sek']:.4f} A", f"= k × IN_OS_sek · k = {b49['k_Faktor']:.2f} {_AMPEL_EMOJI[b49['k_status']]}")
            _metric("49  I_max_zul prim.", f"{b49['I_max_zul_prim']:.2f} A")
        with t2:
            _metric("49  τ_th", f"{b49['tau_min']:.0f} min", f"= {b49['tau_s']:.0f} s  ← Einheit: MINUTEN!")
            _metric("49  Θ-Warnstufe", f"{b49['Theta_Warn_pct']:.0f} %", f"I-Warn = {b49['I_Warn_sek']:.4f} A sek.")
        with t3:
            _metric("46  I2 zulässig sek.", f"{b46['I2_zul_sek']:.4f} A", f"= {b46['I2_zul_faktor']:.2f} × IN_OS_sek")
            _metric("46  T-Warn I2", f"{b46['t_Warn_I2']:.0f} s", f"I2 prim. = {b46['I2_zul_prim']:.2f} A")

    # ══════════════ ANSI 27/59/81/24 — SPANNUNGS- & FREQUENZSCHUTZ ══════════════
    f2759, f81, f24 = e["27_59"], e["81"], e["24"]
    with _section("ANSI 27/59/81/24 — Spannungs- und Frequenzschutz (nur VT-Variante)"):
        if not vt_vorhanden:
            st.markdown('<div class="off-box">🔴 <b>Keine Spannungsmesseingänge (VT) aktiviert</b><br>'
                        'Setze oben den Haken „Spannungsmesseingänge (VT) vorhanden". Ohne '
                        'Spannungseingang sind 27, 59, 81 und 24 gerätetechnisch nicht möglich '
                        '(7UT613 nur in der Variante mit Spannungseingang).</div>',
                        unsafe_allow_html=True)
        else:
            if f2759["aktiv"]:
                st.markdown("**ANSI 27/59 — Unter-/Überspannung** (verkettet, bez. auf UnS)")
                st.dataframe(pd.DataFrame([{
                    "Stufe": s["name"],
                    "Ansprechwert": f"{s['faktor']:.2f} × UnS",
                    "= V sek.": f"{s['U_sek_V']:.1f} V",
                    "Adr. Ansprechwert": f"{s['adr_bez']} (bez.) / {s['adr_volt']} (V)",
                    "t [s]": f"{s['t_s']:.2f}",
                    "Adr. t": s["adr_t"],
                } for s in f2759["stufen"]]), width="stretch", hide_index=True)
                st.caption(f"Pro Stufe genau einen Ansprechwert eintragen: entweder den bezogenen "
                           f"Wert (× UnS) unter der bez.-Adresse ODER den V-sek.-Wert unter der "
                           f"V-Adresse, je nach Zuordnung (Seite → bezogen, Messstelle → Volt). "
                           f"UnS = {f2759['UnS_V']:.0f} V. Zeit jeweils unter eigener Adr. t. "
                           f"Rückfallverhältnis {f2759['rueckfall']:.2f} (Adr.5217 bzw. 5317).")
            else:
                st.markdown(f'<div class="off-box">🔴 <b>27/59 deaktiviert</b><br>{f2759["grund"]}</div>',
                            unsafe_allow_html=True)

            if f81["aktiv"]:
                st.markdown(f"**ANSI 81 — Frequenzschutz** (fN = {f81['fN_Hz']:.0f} Hz, 3×f< + 1×f>)")
                st.dataframe(pd.DataFrame([{
                    "Stufe": s["name"], "f [Hz]": f"{s['f_Hz']:.2f}", "Adr. f": s["adr_f"],
                    "t [s]": f"{s['t_s']:.2f}", "Adr. t": s["adr_t"],
                } for s in f81["stufen"]]), width="stretch", hide_index=True)
                st.caption("Frequenzwert in Hz unter Adr. f, Zeit unter Adr. t. Frequenz aus der "
                           "Messspannung. Unterfrequenzstufe auf 0 = unwirksam, Überfrequenzstufe "
                           "auf ∞ = unwirksam (7UT613 Hdb. 2.16.2).")
            else:
                st.markdown(f'<div class="off-box">🔴 <b>81 deaktiviert</b><br>{f81["grund"]}</div>',
                            unsafe_allow_html=True)

            if f24["aktiv"]:
                st.markdown("**ANSI 24 — Übererregungsschutz U/f** (Schutz vor Eisensättigung)")
                cu1, cu2 = st.columns(2)
                with cu1:
                    _metric("U/f > (Warnstufe)", f"{f24['Uf_gt']:.2f}",
                            f"dimensionslos · Adr.4302 · t = {f24['t_Uf_gt']:.0f} s (Adr.4303)")
                with cu2:
                    _metric("U/f >> (Schnellstufe)", f"{f24['Uf_gtgt']:.2f}",
                            f"dimensionslos · Adr.4304 · t = {f24['t_Uf_gtgt']:.1f} s (Adr.4305)")
                st.caption(f"U/f ist das auf den Nennwert bezogene Verhältnis (U/UN)/(f/fN) und ein "
                           f"direktes Maß für die Eiseninduktion B/BN. Der Wert {f24['Uf_gt']:.2f} "
                           f"bedeutet Auslösung bei {f24['Uf_gt']*100:.0f} % der Nenninduktion und "
                           f"wird ohne weitere Umrechnung direkt unter Adr.4302 eingetippt "
                           f"(7UT613 Hdb. 2.11.2). {f24['hinweis_kennlinie']}")
            else:
                st.markdown(f'<div class="off-box">🔴 <b>24 deaktiviert</b><br>{f24["grund"]}</div>',
                            unsafe_allow_html=True)

    # ══════════════ ANSI 50BF — LEISTUNGSSCHALTERVERSAGERSCHUTZ ══════════════
    bf = e["50BF"]
    with _section("ANSI 50BF — Leistungsschalterversagerschutz"):
        if not bf["aktiv"]:
            st.markdown(f'<div class="off-box">🔴 <b>50BF nicht projektiert</b><br>{bf["grund"]}</div>',
                        unsafe_allow_html=True)
        else:
            modus = "zweistufig (T1 lokal + T2 Sammelschiene)" if bf["zweistufig"] else "einstufig (nur T2)"
            st.markdown(f"**Stromflussbasiert · {modus}**")
            cb1, cb2, cb3 = st.columns(3)
            with cb1:
                _metric("Stromschwelle I>", f"{bf['I_BF_faktor']:.2f} × IN",
                        f"OS {bf['I_BF_OS_prim_A']:.1f} A · US {bf['I_BF_US_prim_A']:.1f} A prim.")
            with cb2:
                t1txt = f"{bf['T1_s']:.3f} s" if bf["T1_s"] is not None else "∞ (nicht genutzt)"
                _metric("T1 (AUS-lokal)", t1txt, "Adr.7015")
            with cb3:
                _metric("T2 (AUS-Sammelschiene)", f"{bf['T2_s']:.3f} s", "Adr.7016")
            zb = bf["zeitbilanz"]
            st.caption(f"Zeitbilanz T2: t LS-Aus {zb['t_LS_aus']:.3f} s + t Rückfall "
                       f"{zb['t_Rueckfall']:.3f} s + t Sicherheit {zb['t_Sicherheit']:.3f} s. "
                       "Stromschwelle sicher über Laststrom-Rückfall (7UT613 Hdb. 2.17).")

    # ══════════════════════ PLAUSIBILITÄTSPRÜFUNG (AMPEL) ══════════════════════
    with _section("Plausibilitätsprüfung (Ampel)"):
        dfp = pd.DataFrame([{
            "Status": f"{_AMPEL_EMOJI.get(c['status'],'')} {c['status']}",
            "Prüfung": c["pruefung"],
            "Ergebnis": c["ergebnis"],
            "Konkrete Korrektur": c["korrektur"] if c["korrektur"] else "—",
            "Hinweis / Quelle": c["hinweis"],
        } for c in plaus])
        st.dataframe(dfp, width="stretch", hide_index=True)
        st.caption("Spalte „Konkrete Korrektur“ nennt bei 🟡/🔴 den genauen Regler und Zielwert. "
                   "Die wichtigsten Punkte stehen zusätzlich oben in der Handlungsempfehlungs-Box.")

    # ══════════════════════ RESERVESCHUTZ-ZUORDNUNG / DIGSI-ADRESSEN ══════════════════════
    with _section("Reserveschutz-Zuordnung / DIGSI-Adressen"):
        rsv = e["reserveschutz"]
        dfr = pd.DataFrame([{
            "Funktion": x["funktion"], "Ziel-Objekt": x["ziel"],
            "I> [A sek.]": x["I_sek"], "t> [s]": x["t"],
            "I>> [A sek.]": x["IHH_sek"], "t>> [s]": x["tHH"],
            "Siemens-Adresse": x["adresse"],
        } for x in rsv])
        st.dataframe(dfr, width="stretch", hide_index=True)
        st.caption("Hinweis: bei 'Überlast 49' ist die Spalte t> die Zeitkonstante τ in MINUTEN (nicht Sekunden).")

    # ══════════════════════ GERÄTE-EMPFEHLUNG ERDSCHLUSSERFASSUNG ══════════════════════
    with _section("Geräte-Empfehlung Erdschlusserfassung"):
        eg = e["erdschluss_geraet"]
        st.markdown(f"**Empfohlenes Gerät:** {eg['geraet']}")
        st.markdown(f"**Begründung:** {eg['grund']}")

    # ══════════════════════ HERSTELLERNEUTRALE SOLLWERT-TABELLE ══════════════════════
    with _section("📋  Herstellerneutrale Sollwert-Tabelle (DIGSI-Adressen)"):
        rows = []
        for x in r["rows"]:
            sek = f"{x['wert_sek']:.4f}" if x["wert_sek"] is not None else f"{x['faktor']:g}"
            rows.append(("87T", x["name"], sek, x["einheit"], f"7UT613: {x['adresse']}"))
        rows += [
            ("50/51", "I> Phase OS",  f"{umz['OS']['I_sek']:.4f}",  "A sek.", "Adr.2011 / t 2013"),
            ("50/51", "I>> Phase OS", f"{umz['OS']['IHH_sek']:.4f}", "A sek.", "Adr.2014 / t 2016"),
            ("50/51", "I> Phase US",  f"{umz['US']['I_sek']:.4f}",  "A sek.", "Adr.2011 / t 2013 (Seite 2)"),
            ("50/51", "I>> Phase US", f"{umz['US']['IHH_sek']:.4f}", "A sek.", "Adr.2014 / t 2016 (Seite 2)"),
            ("49", "k-Faktor",  f"{b49['k_Faktor']:.2f}", "x IN", "Adr.4202"),
            ("49", "τ thermisch", f"{b49['tau_min']:.0f}", "min", "Adr.4203  ← MINUTEN!"),
            ("49", "Θ-Warnstufe", f"{b49['Theta_Warn_pct']:.0f}", "%", "Adr.4204"),
            ("46", "I2 zulässig", f"{b46['I2_zul_faktor']:.2f}", "I/InS", "Adr.4032 / t 4033"),
        ]
        if erde["anwendbar"]:
            rows += [
                ("50N/51N", "IE>",  f"{erde['IE_sek']:.2f}",  "A sek.", "Adr.2413 / t 2414"),
                ("50N/51N", "IE>>", f"{erde['IEHH_sek']:.2f}", "A sek.", "Adr.2411 / t 2412"),
            ]
        if f87n["aktiv"]:
            rows.append(("87N", "I-EDS>", f"{f87n['I_EDS_sek_A']:.4f}", "A sek.", "Adr.1311"))
        else:
            rows.append(("87N", "EDS", "— DEAKTIVIERT —", "–", "isoliert/kompensiert → U0-Verfahren"))
        if u0["aktiv"]:
            rows += [
                ("U0", "U0> Meldung",   f"{u0['U0_Meld_V']:.0f}",  "V", f"7SJ64 · t = {u0['t_Meld']:.0f} s"),
                ("U0", "U0>> Abschalt", f"{u0['U0_Absch_V']:.0f}", "V", f"7SJ64 · t = {u0['t_Absch']:.0f} s"),
            ]
        # 27/59 Spannung: pro Stufe der bezogene Sollwert + Volt-Äquivalent, beide Adressen
        if f2759["aktiv"]:
            for s in f2759["stufen"]:
                ansi = s["name"].split()[0]
                rows.append((ansi, s["name"].split(maxsplit=1)[1],
                             f"{s['faktor']:.2f}  ({s['U_sek_V']:.0f} V sek.)", "× UnS",
                             f"Adr.{s['adr_bez']} bez. / {s['adr_volt']} V · t {s['adr_t']} = {s['t_s']:.2f} s"))
        # 81 Frequenz: pro Stufe Hz-Wert + Adressen
        if f81["aktiv"]:
            for s in f81["stufen"]:
                ansi = s["name"].split()[0]
                rows.append((ansi, s["name"].split(maxsplit=1)[1], f"{s['f_Hz']:.1f}", "Hz",
                             f"Adr.{s['adr_f']} · t {s['adr_t']} = {s['t_s']:.2f} s"))
        # 24 Übererregung: dimensionsloser Direkteinstellwert
        if f24["aktiv"]:
            rows += [
                ("24", "U/f >",  f"{f24['Uf_gt']:.2f}",  "dimensionslos",
                 f"Adr.4302 · t 4303 = {f24['t_Uf_gt']:.0f} s · = {f24['Uf_gt']*100:.0f} % Nenninduktion"),
                ("24", "U/f >>", f"{f24['Uf_gtgt']:.2f}", "dimensionslos",
                 f"Adr.4304 · t 4305 = {f24['t_Uf_gtgt']:.1f} s"),
            ]
        # 50BF: Stromschwelle je Seite + Zeitstufen
        if bf["aktiv"]:
            rows += [
                ("50BF", "I> Stromfluss OS", f"{bf['I_BF_OS_sek_A']:.3f}", "A sek.",
                 f"LS-I> Stromflussüberw. ({bf['I_BF_faktor']:.2f} × IN)"),
                ("50BF", "I> Stromfluss US", f"{bf['I_BF_US_sek_A']:.3f}", "A sek.",
                 f"LS-I> Stromflussüberw. ({bf['I_BF_faktor']:.2f} × IN)"),
            ]
            if bf["T1_s"] is not None:
                rows.append(("50BF", "T1 (AUS-lokal)", f"{bf['T1_s']:.3f}", "s", "Adr.7015"))
            rows.append(("50BF", "T2 (AUS-Sammelschiene)", f"{bf['T2_s']:.3f}", "s", "Adr.7016"))
        dft = pd.DataFrame(rows, columns=["ANSI", "Parameter", "Sollwert", "Einheit", "Hinweis / Adresse"])
        st.dataframe(dft, width="stretch", hide_index=True)
