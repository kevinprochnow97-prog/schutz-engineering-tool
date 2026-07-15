"""
tab_trafo.py — Streamlit-UI für Transformatorschutz
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg
"""

import pandas as pd
import streamlit as st

import konstanten_trafo as K
from calc_trafo import berechne_alle, empfehlung_IHH_OS

from utils import AMPEL_EMOJI as _AMPEL_EMOJI, de, deg
from ui import inject_css, metric as _metric, section as _section, pill as _pill, hreg
from ui import grphead as _grphead, pin as _pin


def _hreg(key):
    """Hersteller-Hinweis unter einem Regler (nutzt das modul-lokale HERST-Dict)."""
    hreg(K.HERST, key)


# ── Hauptfunktion ─────────────────────────────────────────────────────────────

def show():
    inject_css()

    # ══════════════════════ EINGABEN (einklappbar) ══════════════════════
    with _section("Eingaben — Grunddaten, Stromwandler, Netzparameter"):
        ci1, ci2, ci3 = st.columns(3, gap="medium")
        with ci1:
            st.caption("**Transformator-Grunddaten**")
            Sn    = st.number_input("Sn — Bemessungsleistung [MVA]", 0.1, value=None, step=0.5, format="%.1f", placeholder="z. B. 16,0")
            UN_OS = st.number_input("UN OS — Oberspannung [kV]", 1.0, value=None, step=1.0, format="%.1f", placeholder="z. B. 110")
            UN_US = st.number_input("UN US — Unterspannung [kV]", 0.4, value=None, step=0.1, format="%.1f", placeholder="z. B. 10")
            uk    = st.number_input("uk — Kurzschlussspannung [%]", 1.0, 25.0, value=None, step=0.1, format="%.1f", placeholder="z. B. 11,5")
            vg    = st.selectbox("Schaltgruppe", K.SCHALTGRUPPEN, index=0)
            stp_pm = st.number_input("Stufensteller +/- [%]", 0, 40, value=None, step=1, placeholder="z. B. 10")
        with ci2:
            st.caption("**Stromwandler (primär / sekundär)**")
            c1, c2 = st.columns(2)
            with c1:
                CT_OS_P = st.number_input("CT OS prim. [A]", 1, value=None, step=1, placeholder="z. B. 100")
                CT_US_P = st.number_input("CT US prim. [A]", 1, value=None, step=1, placeholder="z. B. 1000")
            with c2:
                CT_OS_S = st.selectbox("CT OS sek. [A]", [1, 5], index=0)
                CT_US_S = st.selectbox("CT US sek. [A]", [1, 5], index=0)
            # Erder-Wandler zuerst auswählen, danach (nur falls vorhanden) die Wandlerdaten abfragen.
            ie_wdl = st.checkbox("Sternpunkt-Wandler (IE-CT) vorhanden", value=True)
            if ie_wdl:
                ce1, ce2 = st.columns(2)
                with ce1:
                    CT_E_P = st.number_input("CT Erder prim. [A]", 1, value=None, step=1, placeholder="z. B. 400")
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
                    VT_P = st.number_input("VT prim. [kV]", 0.0, value=None,
                                           step=0.1, format="%.2f", placeholder="meist = UN US")
                with cv2:
                    VT_S = st.selectbox("VT sek. [V]", K.VT_Sek_Optionen, index=1)
            else:
                VT_P, VT_S = 0.0, 110
        with ci3:
            st.caption("**Netzparameter**")
            stp_OS = st.selectbox("Sternpunktbehandlung OS", K.STERNPUNKT_OPTIONEN, index=2)
            stp_US = st.selectbox("Sternpunktbehandlung US", K.STERNPUNKT_OPTIONEN, index=1)
            Ik_OS  = st.number_input("Ik″ max OS [kA]", 0.0, value=None, step=0.5, format="%.1f", placeholder="z. B. 10")
            Ik_US  = st.number_input("Ik″ max US [kA]", 0.0, value=None, step=0.5, format="%.1f", placeholder="z. B. 8")
            Ik_min_OS = st.number_input(
                "Ik min OS (Schutzgebiet-Ende) [kA]", 0.0, value=None, step=0.1, format="%.2f",
                placeholder="optional",
                help="Minimaler Kurzschlussstrom nach DIN EN 60909-0 (c=0,95). "
                     "Leer = nicht vorhanden, dann Näherung 0,3·Ik″max OS.")
            bf_aktiv = st.checkbox(
                "Leistungsschalterversagerschutz (50BF) projektiert", value=True,
                help="Adr.170 SCHALTERVERSAG. Stromflussbasiert, benötigt keine Spannung.")
            bf_zwei = st.checkbox(
                "50BF zweistufig (T1 lokal + T2 Sammelschiene)", value=False,
                help="Aus = einstufig, nur T2 (Adr.7016). Ein = zusätzlich T1 (Adr.7015).",
                disabled=not bf_aktiv)

    # ── Vollständigkeitsprüfung der Grunddaten ────────────────────────────────
    # Ohne ausgefüllte Grunddaten wird nicht gerechnet (kein Handlungsbedarf,
    # nur ein neutraler Hinweis). Erst wenn alles vorhanden ist, erscheinen
    # Erweiterte Parameter, Ergebnisse und Plausibilitätsprüfung.
    _pflicht = {"Sn": Sn, "UN OS": UN_OS, "UN US": UN_US, "uk": uk,
                "Stufensteller": stp_pm, "CT OS prim.": CT_OS_P, "CT US prim.": CT_US_P,
                "Ik\u2033 max OS": Ik_OS, "Ik\u2033 max US": Ik_US}
    if ie_wdl:
        _pflicht["CT Erder prim."] = CT_E_P
    if vt_vorhanden:
        _pflicht["VT prim."] = VT_P
    _fehlt = [k for k, v in _pflicht.items() if v is None]
    if _fehlt:
        st.info("\u25ab\ufe0f **Bitte zun\u00e4chst die Grunddaten ausf\u00fcllen.** Sobald die "
                "Pflichtfelder gef\u00fcllt sind, erscheinen automatisch die erweiterten "
                "Parameter, die Sollwerte und die Plausibilit\u00e4tspr\u00fcfung.\n\nNoch offen: "
                + ", ".join(_fehlt) + ".")
        return
    Ik_min_OS = Ik_min_OS or 0.0

    # Erweiterte Parameter — eigenständige (NICHT verschachtelte) Sektion
    with _section("Erweiterte Parameter (Voreinstellungen nach SIPROTEC 7UT6xx — frei änderbar)", expanded=False):
        st.caption("ℹ️ Unter jedem Regler steht der vom Hersteller empfohlene Wert/Range "
                   "und die Begründung. So ist nachvollziehbar, was die Voreinstellung bezweckt.")
        e1, e2, e3 = st.columns(3)
        with e1:
            _grphead("87T Differential")
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
            _grphead("50/51 + 49 + 46")
            f_I    = st.slider("I> Phase [I/InS]", 1.0, 3.0, K.f_I_Ph_def, 0.1)
            _hreg("f_I_Ph")
            t_I    = st.number_input("t I> [s]", 0.05, 2.0, K.t_I_Ph_def, 0.05, format="%.2f")
            _hreg("t_I_Ph")

            # I>> OS: Auto aus 1,2/uk bzw. Ik″ max US (mit Override)
            f_IHH_OS_emp = empfehlung_IHH_OS(
                dict(nT=(UN_OS/UN_US if UN_US else 0),
                     IN_OS_prim=(Sn*1e6/(1.7320508*UN_OS*1e3) if UN_OS else 0)),
                dict(k_S_IGG=K.k_S_IGG, Ik_max_US_kA=Ik_US, uk_pct=uk))
            auto_OS = st.checkbox(f"I>> OS automatisch ({deg(f_IHH_OS_emp)} ×IN)", value=True,
                                  help="Speiseseite: Empfehlung 1,2·Ik″ max US (auf OS bezogen).")
            if auto_OS:
                f_IHH_OS = f_IHH_OS_emp
                st.caption(f"➜ I>> OS = **{deg(f_IHH_OS_emp)} ×IN** (auto). "
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
            _grphead("Engineering-Margen")
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
                _grphead("27/59 Spannung [× UnS] + t [s]")
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
                _grphead("81 Frequenz [Hz] + t [s]")
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
                _grphead("24 Übererregung [× (U/f)N] + t [s]")
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
            st.caption("Leistungsschalterversagerschutz 50BF: Zeitbilanz für T2 (Adr.7016).")
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
            st.caption(f"➜ T2 = {de(tLS_v + tRF_v + tSi_v, 3)} s"
                       + (f" · T1 = {de(tLS_v + tRF_v + tSi_v, 3)} s (zweistufig)" if bf_zwei else " (einstufig, T1 = ∞)"))

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
        f'{_pill("OK", n_ok)} &nbsp; {_pill("Hinweis", n_hin)} &nbsp; '
        f'{_pill("Prüfen!", n_bad)}</div>', unsafe_allow_html=True)

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
            _metric("IN OS primär",   f"{de(g['IN_OS_prim'], 2)} A")
            _metric("IN OS sekundär", f"{de(g['IN_OS_sek'], 4)} A", f"÷ kCT_OS = {de(g['kCT_OS'], 0)}")
            _metric("STW-Anpassung OS", f"{de(g['I_an_OS'], 3)}", "I_an = CT_sek / IN_sek  (Soll 0,5–2,0)")
        with g2:
            _metric("IN US primär",   f"{de(g['IN_US_prim'], 2)} A")
            _metric("IN US sekundär", f"{de(g['IN_US_sek'], 4)} A", f"÷ kCT_US = {de(g['kCT_US'], 0)}")
            _metric("STW-Anpassung US", f"{de(g['I_an_US'], 3)}", "I_an = CT_sek / IN_sek  (Soll 0,5–2,0)")
        with g3:
            _metric("Übersetzung nT",   f"{de(g['nT'], 3)}", "= UN_OS / UN_US")
            _metric("kCT Erder",        f"{de(g['kCT_E'], 0)}")
            _metric("Bezugsstrom IN_Obj sek.", f"{de(g['IN_Obj_sek'], 4)} A", "= max(IN_OS_sek, IN_US_sek) → 87T")

    # ══════════════════════ ANSI 87T — DIFFERENTIALSCHUTZ ══════════════════════
    r = e["87T"]
    with _section("ANSI 87T — Differentialschutz"):
        d1, d2 = st.columns(2)
        with d1: _metric("I-DIFF> sekundär", f"{de(r['I_DIFF_Anspr_sek_A'], 4)} A", f"= {de(p['I_DIFF']*100, 0)}% × IN_Obj")
        with d2: _metric("I-DIFF> primär OS", f"{de(r['I_DIFF_Anspr_prim_A'], 2)} A", "= Faktor × IN_OS_prim")
        df87 = pd.DataFrame([{
            "Parameter": x["name"],
            "Einstellwert": f"{deg(x['faktor'])}",
            "Einheit": x["einheit"],
            "DIGSI-Adresse": x["adresse"],
            "Kontrolle A sek.": f"{de(x['wert_sek'], 4)}" if x["wert_sek"] is not None else "—",
            "Kontrolle A prim. OS": f"{de(x['wert_prim'], 2)}" if x["wert_prim"] is not None else "—",
            "Empfehlung": f"{deg(x['empfehlung'])}" if x["empfehlung"] is not None else "—",
            "Status": f"{_AMPEL_EMOJI.get(x['status'],'')} {x['status']}",
        } for x in r["rows"]])
        st.dataframe(df87, width="stretch", hide_index=True)
        st.caption("In DIGSI wird ausschließlich der bezogene **Einstellwert** (Spalte 2, Einheit "
                   "I/InO bzw. s / % / dimensionslos) unter der genannten Adresse eingetragen. "
                   "Die Ampere-Spalten sind reine **Kontrollwerte** (sekundär / primär OS) für die "
                   "Prüfung vor Ort und werden nirgends eingegeben (7UT613 Hdb. 2.2.2, Adr.1221 ff. "
                   "in I/InO). Empfehlung dynamisch aus Stufensteller / uk / Sn. "
                   "Status: 🟢 identisch · 🟡 Abweichung < 20 % · 🔴 Abweichung ≥ 20 %. "
                   "Bewusste Abweichung nach Schutzphilosophie zulässig (7UT613 Hdb. 2.2.7).")

    # ══════════════════════ ERDSCHLUSS- / ERDFEHLERSCHUTZ ══════════════════════
    f87n = e["87N"]
    erde = e["50N51N"]
    u0 = e["U0"]
    with _section("Erdschluss- / Erdfehlerschutz (87N · 50N/51N · U0)"):
        if f87n["aktiv"]:
            _grphead("ANSI 87N — Erdfehler-Differentialschutz (EDS)")
            df87n = pd.DataFrame([
                ("I-EDS> (Ansprechwert)", f"{de(f87n['I_EDS_faktor'], 2)}", "I/InS",
                 f"{de(f87n['I_EDS_sek_A'], 4)} A sek. · {de(f87n['I_EDS_prim_A'], 2)} A prim.",
                 "Adr.1311"),
                ("T I-EDS> (Verzögerung)", f"{de(f87n['T_I_EDS_s'], 2)}", "s", "—",
                 "Adr.1312A"),
                ("Steigung I-EDS> = f(I-SUM)", f"{de(f87n['Steigung_EDS'], 2)}", "—", "—",
                 "Adr.1313A"),
            ], columns=["Parameter", "Einstellwert", "Einheit", "Kontrolle (A)", "DIGSI-Adresse"])
            st.dataframe(df87n, width="stretch", hide_index=True)
            st.caption("Eingetragen wird der bezogene Einstellwert (I/InS, bezogen auf den "
                       "Nennstrom der zugeordneten Seite, hier OS) unter Adr.1311; die "
                       "Ampere-Angaben sind Kontrollwerte (7UT613 Hdb. 2.3.2).")
        else:
            st.markdown(f'<div class="off-box">🔴 <b>87N (EDS) deaktiviert</b><br>{f87n["grund"]}</div>',
                        unsafe_allow_html=True)

        if erde["anwendbar"]:
            c1, c2 = st.columns(2)
            with c1: _metric("50N/51N  IE>",  f"{de(erde['IE_sek'], 2)} A sek.", f"= {de(erde['IE_prim'], 1)} A prim · t = {de(erde['t_IE'], 2)} s")
            with c2: _metric("50N/51N  IE>>", f"{de(erde['IEHH_sek'], 2)} A sek.", f"= {de(erde['IEHH_prim'], 1)} A prim · t = {de(erde['t_IEHH'], 2)} s")

        if u0["aktiv"]:
            net = "kompensiert" if u0["kompensiert"] else "isoliert"
            cos = (f"<br>cos-φ-Stufe (wattmetrisch): {de(u0['cos_phi_pct'], 0)}% IE_kap · "
                   f"t = {de(u0['t_cos_phi'], 1)} s — nur kompensiert" if u0["kompensiert"] else "")
            st.markdown(
                f'<div class="info-box">🟢 <b>U0-Erdschlusserfassung aktiv ({net}es Netz)</b><br>'
                f'U0&gt; Meldestufe: {de(u0["U0_Meld_pu"]*100, 0)}% UN/√3 = {de(u0["U0_Meld_V"], 0)} V · t = {de(u0["t_Meld"], 0)} s<br>'
                f'U0&gt;&gt; Abschaltstufe: {de(u0["U0_Absch_pu"]*100, 0)}% UN/√3 = {de(u0["U0_Absch_V"], 0)} V · t = {de(u0["t_Absch"], 0)} s'
                f'{cos}<br><span style="font-size:0.78rem;color:#3a6b48">Hinweis: nicht im 7UT613 enthalten → '
                f'separates 7SJ64 / zentrale Erdschlusserfassung. Quelle: FNN-Leitfaden.</span></div>',
                unsafe_allow_html=True)

    # ══════════════════════ ANSI 50/51 — ÜBERSTROMZEITSCHUTZ PHASEN ══════════════════════
    umz = e["5051"]
    with _section("ANSI 50/51 — Überstromzeitschutz Phasen (OS + US)"):
        dfu = pd.DataFrame([
            ("I> OS (51)",  f"{deg(umz['f_I'])}",       "I/InS", f"{de(umz['OS']['I_sek'], 4)}",   f"{de(umz['OS']['I_prim'], 1)}",   f"{de(umz['t_I'], 2)}",   "2015 (I/InS) bzw. 2014 (A) · t 2016"),
            ("I>> OS (50)", f"{deg(umz['f_IHH_OS'])}",   "I/InS", f"{de(umz['OS']['IHH_sek'], 4)}", f"{de(umz['OS']['IHH_prim'], 1)}", f"{de(umz['t_IHH'], 2)}", "2012 (I/InS) bzw. 2011 (A) · t 2013"),
            ("I> US (51)",  f"{deg(umz['f_I'])}",        "I/InS", f"{de(umz['US']['I_sek'], 4)}",   f"{de(umz['US']['I_prim'], 1)}",   f"{de(umz['t_I'], 2)}",   "2115 (I/InS) bzw. 2114 (A) · t 2116"),
            ("I>> US (50)", f"{deg(umz['f_IHH_US'])}",   "I/InS", f"{de(umz['US']['IHH_sek'], 4)}", f"{de(umz['US']['IHH_prim'], 1)}", f"{de(umz['t_IHH'], 2)}", "2112 (I/InS) bzw. 2111 (A) · t 2113"),
        ], columns=["Funktion", "Faktor", "Einheit", "I_Soll [A sek.]", "I_Soll [A prim.]", "t [s]", "DIGSI-Adresse"])
        st.dataframe(dfu, width="stretch", hide_index=True)
        st.caption("Je Stufe genau einen Ansprechwert eintragen: Bei Zuordnung des UMZ zu einer "
                   "**Seite** des Hauptschutzobjekts (wie hier: UAMZ-PH 1 → OS-Seite, "
                   "UAMZ-PH 2 → US-Seite) gilt der bezogene **Faktor** unter der I/InS-Adresse; "
                   "bei Zuordnung zu einer Messstelle der **A-sek.-Wert** unter der A-Adresse "
                   "(7UT613 Hdb. 2.4.2). Zeit jeweils unter Adr. t.")
        st.caption(f"I>> OS automatisch aus 1,2·Ik″ max US (Speiseseite, Empfehlung {deg(umz['f_IHH_OS_emp'])} ×IN). "
                   "I>> US wird gegen die nachgelagerte Staffelung bemessen, beide Seiten sind getrennt einstellbar.")
        st.caption(f"Rush-Stabilisierung Phasen (2. Harm.): {de(umz['rush_2H_pct'], 0)}% · "
                   "UMZ = definite time (feste Verzögerung). AMZ-Kennlinie nach IEC 60255 als Erweiterung vorgesehen.")

    # ══════════════════════ BEMESSUNGS-ENGINEERING ══════════════════════
    b = e["bemessung"]
    with _section("Bemessungs-Engineering — Stufenwahl + Empfindlichkeit"):
        st.caption("Kein Ersatz für eine vollständige Kurzschlussberechnung: verifiziert die "
                   "Stufenwahl gegen max. Last, Inrush und minimalen Fehlerstrom. Bezugsseite OS.")
        dfb = pd.DataFrame([
            ("I_max_Last (OS)",            f"{de(b['I_max_Last_prim'], 1)} A prim.", "▫️ Eingangsgröße", "Default 1,2 × IN_OS"),
            ("I_k_min (Schutzgebiet-Ende)",f"{de(b['I_k_min_prim'], 0)} A prim.", "▫️ Eingangsgröße", b['I_k_min_quelle']),
            ("I> Empfehlung = k_S · I_max_Last", f"{de(b['I_emp_prim'], 1)} A prim.",
                f"{_AMPEL_EMOJI[b['I_status']]} {b['I_status']}",
                b['korr_I'] if b['korr_I'] else f"gewählt {de(b['I_gewaehlt_prim'], 1)} A ≥ Empfehlung ✓"),
            ("I>> Empfehlung = max(k_S·Ik″ max US@OS ; Inrush·IN)", f"{de(b['IHH_emp_prim'], 0)} A prim.",
                f"{_AMPEL_EMOJI[b['IHH_status']]} {b['IHH_status']}",
                b['korr_IHH'] if b['korr_IHH'] else f"gewählt {de(b['IHH_gewaehlt_prim'], 0)} A ≥ Empfehlung ✓ · maßgebend: {b['massgebend']}"),
            ("Empfindlichkeit I_k_min / I> ≥ γ", f"{de(b['empfind'], 2)}  (γ = {deg(b['gamma'])})",
                f"{_AMPEL_EMOJI[b['empfind_status']]} {b['empfind_status']}",
                b['korr_emp'] if b['korr_emp'] else "I_k_min regt I> sicher an ✓"),
        ], columns=["Größe", "Wert", "Status", "Korrektur / Kommentar"])
        st.dataframe(dfb, width="stretch", hide_index=True)
        st.caption("Die ersten beiden Zeilen sind Eingangs- bzw. Bezugsgrößen ohne "
                   "Prüfcharakter (▫️). Bewertet werden die daraus abgeleitete Stufenwahl "
                   "I>, I>> und die Empfindlichkeit (🟢/🟡/🔴).")

    # ══════════════════════ ANSI 49 (THERMISCH) + ANSI 46 (SCHIEFLAST) ══════════════════════
    b49, b46 = e["49"], e["46"]
    with _section("ANSI 49 (thermisch) + ANSI 46 (Schieflast)"):
        t1, t2, t3 = st.columns(3)
        with t1:
            _metric("49  I_max_zul sek.", f"{de(b49['I_max_zul_sek'], 4)} A", f"= k × IN_OS_sek · k = {de(b49['k_Faktor'], 2)} {_AMPEL_EMOJI[b49['k_status']]}")
            _metric("49  I_max_zul prim.", f"{de(b49['I_max_zul_prim'], 2)} A")
        with t2:
            _metric("49  τ_th", f"{de(b49['tau_min'], 0)} min", f"= {de(b49['tau_s'], 0)} s  ← Einheit: MINUTEN!")
            _metric("49  Θ-Warnstufe", f"{de(b49['Theta_Warn_pct'], 0)} %", f"I-Warn = {de(b49['I_Warn_sek'], 4)} A sek.")
        with t3:
            _metric("46  I2 zulässig sek.", f"{de(b46['I2_zul_sek'], 4)} A", f"= {de(b46['I2_zul_faktor'], 2)} × IN_OS_sek")
            _metric("46  T-Warn I2", f"{de(b46['t_Warn_I2'], 0)} s", f"I2 prim. = {de(b46['I2_zul_prim'], 2)} A")
        df4946 = pd.DataFrame([
            ("49", "k-Faktor",     f"{de(b49['k_Faktor'], 2)}",       "× IN",  "Adr.4202"),
            ("49", "τ thermisch",  f"{de(b49['tau_min'], 0)}",        "min",   "Adr.4203  ← MINUTEN!"),
            ("49", "Θ-Warnstufe",  f"{de(b49['Theta_Warn_pct'], 0)}", "%",     "Adr.4204"),
            ("49", "I-Warnstufe",  f"{de(b49['I_Warn_faktor'], 2)}",  "I/InS", "Adr.4205"),
            ("46", "I2 zulässig",  f"{de(b46['I2_zul_faktor'], 2)}",  "I/InS", "Adr.4032 (bzw. 4031 in A sek.)"),
            ("46", "T Warn",       f"{de(b46['t_Warn_I2'], 0)}",      "s",     "Adr.4033"),
        ], columns=["ANSI", "Parameter", "Einstellwert", "Einheit", "DIGSI-Adresse"])
        st.dataframe(df4946, width="stretch", hide_index=True)
        st.caption("Eingetragen werden die bezogenen Einstellwerte der Tabelle; die "
                   "Ampere-Angaben in den Kacheln sind Kontrollwerte. 46: bei Zuordnung zu "
                   "einer Seite gilt Adr.4032 (I/InS), sonst Adr.4031 in A sek. "
                   "(7UT613 Hdb. 2.8.2 und 2.9.2).")

    # ══════════════ ANSI 27/59/81/24 — SPANNUNGS- & FREQUENZSCHUTZ ══════════════
    f2759, f81, f24 = e["27_59"], e["81"], e["24"]
    with _section("ANSI 27/59/81/24 — Spannungs- und Frequenzschutz (nur VT-Variante)"):
        if not vt_vorhanden:
            st.markdown('<div class="info-box">ℹ️ <b>Basisvariante ohne Spannungsmesseingänge (VT)</b><br>'
                        'Die Funktionen 27, 59, 81 und 24 benötigen den Spannungseingang und sind '
                        'in dieser Variante nicht aktiv. Falls die 7UT613-Variante mit Spannungseingang '
                        'eingesetzt wird, oben den Haken „Spannungsmesseingänge (VT) vorhanden" setzen, '
                        'dann werden diese Stufen berechnet.</div>',
                        unsafe_allow_html=True)
        else:
            if f2759["aktiv"]:
                st.markdown("**ANSI 27/59 — Unter-/Überspannung** (verkettet, bez. auf UnS)")
                st.dataframe(pd.DataFrame([{
                    "Stufe": s["name"],
                    "Ansprechwert": f"{de(s['faktor'], 2)} × UnS",
                    "= V sek.": f"{de(s['U_sek_V'], 1)} V",
                    "Adr. Ansprechwert": f"{s['adr_bez']} (bez.) / {s['adr_volt']} (V)",
                    "t [s]": f"{de(s['t_s'], 2)}",
                    "Adr. t": s["adr_t"],
                } for s in f2759["stufen"]]), width="stretch", hide_index=True)
                st.caption(f"Pro Stufe genau einen Ansprechwert eintragen: entweder den bezogenen "
                           f"Wert (× UnS) unter der bez.-Adresse ODER den V-sek.-Wert unter der "
                           f"V-Adresse, je nach Zuordnung (Seite → bezogen, Messstelle → Volt). "
                           f"UnS = {de(f2759['UnS_V'], 0)} V. Zeit jeweils unter eigener Adr. t. "
                           f"Rückfallverhältnis {de(f2759['rueckfall'], 2)} (Adr.5217 bzw. 5317).")
            else:
                st.markdown(f'<div class="off-box">🔴 <b>27/59 deaktiviert</b><br>{f2759["grund"]}</div>',
                            unsafe_allow_html=True)

            if f81["aktiv"]:
                st.markdown(f"**ANSI 81 — Frequenzschutz** (fN = {de(f81['fN_Hz'], 0)} Hz, 3×f< + 1×f>)")
                st.dataframe(pd.DataFrame([{
                    "Stufe": s["name"], "f [Hz]": f"{de(s['f_Hz'], 2)}", "Adr. f": s["adr_f"],
                    "t [s]": f"{de(s['t_s'], 2)}", "Adr. t": s["adr_t"],
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
                    _metric("U/f > (Warnstufe)", f"{de(f24['Uf_gt'], 2)}",
                            f"dimensionslos · Adr.4302 · t = {de(f24['t_Uf_gt'], 0)} s (Adr.4303)")
                with cu2:
                    _metric("U/f >> (Schnellstufe)", f"{de(f24['Uf_gtgt'], 2)}",
                            f"dimensionslos · Adr.4304 · t = {de(f24['t_Uf_gtgt'], 1)} s (Adr.4305)")
                st.caption(f"U/f ist das auf den Nennwert bezogene Verhältnis (U/UN)/(f/fN) und ein "
                           f"direktes Maß für die Eiseninduktion B/BN. Der Wert {de(f24['Uf_gt'], 2)} "
                           f"bedeutet Auslösung bei {de(f24['Uf_gt']*100, 0)} % der Nenninduktion und "
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
                _metric("Stromschwelle I>", f"{de(bf['I_BF_faktor'], 2)} × IN",
                        f"OS {de(bf['I_BF_OS_prim_A'], 1)} A · US {de(bf['I_BF_US_prim_A'], 1)} A prim.")
            with cb2:
                t1txt = f"{de(bf['T1_s'], 3)} s" if bf["T1_s"] is not None else "∞ (nicht genutzt)"
                _metric("T1 (AUS-lokal)", t1txt, "Adr.7015")
            with cb3:
                _metric("T2 (AUS-Sammelschiene)", f"{de(bf['T2_s'], 3)} s", "Adr.7016")
            zb = bf["zeitbilanz"]
            st.caption(f"Zeitbilanz T2: t LS-Aus {de(zb['t_LS_aus'], 3)} s + t Rückfall "
                       f"{de(zb['t_Rueckfall'], 3)} s + t Sicherheit {de(zb['t_Sicherheit'], 3)} s. "
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
            "DIGSI-Adresse": x["adresse"],
        } for x in rsv])
        st.dataframe(dfr, width="stretch", hide_index=True)
        st.caption("Hinweis: bei 'Überlast 49' ist die Spalte t> die Zeitkonstante τ in MINUTEN (nicht Sekunden).")

    # ══════════════════════ GERÄTE-EMPFEHLUNG ERDSCHLUSSERFASSUNG ══════════════════════
    with _section("Geräte-Empfehlung Erdschlusserfassung"):
        eg = e["erdschluss_geraet"]
        st.markdown(f"**Empfohlenes Gerät:** {eg['geraet']}")
        st.markdown(f"**Begründung:** {eg['grund']}")
        if eg.get("schaltgruppe"):
            st.markdown(f"**Schaltgruppe:** {eg['schaltgruppe']}")

    # ══════════════════════ HERSTELLERNEUTRALE SOLLWERT-TABELLE ══════════════════════
    with _section("📋  Herstellerneutrale Sollwert-Tabelle (DIGSI-Adressen)"):
        rows = [("—", "Schaltgruppe (Anlagendatum)", vg, "—",
                 "SCHALT.ART Adr.314 (S1) / 324 (S2) · SCHALTGRUPPE Adr.325 (S2)")]
        for x in r["rows"]:
            kontrolle = f" · = {de(x['wert_sek'], 4)} A sek." if x["wert_sek"] is not None else ""
            rows.append(("87T", x["name"], f"{deg(x['faktor'])}", x["einheit"],
                         f"7UT613: {x['adresse']}{kontrolle}"))
        rows += [
            ("50/51", "I> Phase OS",  f"{de(umz['OS']['I_sek'], 4)}",  "A sek.", "Adr.2014 (A) bzw. 2015 (I/InS) / t 2016"),
            ("50/51", "I>> Phase OS", f"{de(umz['OS']['IHH_sek'], 4)}", "A sek.", "Adr.2011 (A) bzw. 2012 (I/InS) / t 2013"),
            ("50/51", "I> Phase US",  f"{de(umz['US']['I_sek'], 4)}",  "A sek.", "Adr.2114 (A) bzw. 2115 (I/InS) / t 2116 (U/AMZ-Phase 2)"),
            ("50/51", "I>> Phase US", f"{de(umz['US']['IHH_sek'], 4)}", "A sek.", "Adr.2111 (A) bzw. 2112 (I/InS) / t 2113 (U/AMZ-Phase 2)"),
            ("49", "k-Faktor",  f"{de(b49['k_Faktor'], 2)}", "x IN", "Adr.4202"),
            ("49", "τ thermisch", f"{de(b49['tau_min'], 0)}", "min", "Adr.4203  ← MINUTEN!"),
            ("49", "Θ-Warnstufe", f"{de(b49['Theta_Warn_pct'], 0)}", "%", "Adr.4204"),
            ("46", "I2 zulässig", f"{de(b46['I2_zul_faktor'], 2)}", "I/InS", "Adr.4032 / t 4033"),
        ]
        if erde["anwendbar"]:
            rows += [
                ("50N/51N", "IE>",  f"{de(erde['IE_sek'], 2)}",  "A sek.", "Adr.2413 / t 2414"),
                ("50N/51N", "IE>>", f"{de(erde['IEHH_sek'], 2)}", "A sek.", "Adr.2411 / t 2412"),
            ]
        if f87n["aktiv"]:
            rows.append(("87N", "I-EDS>", f"{de(f87n['I_EDS_faktor'], 2)}", "I/InS",
                         f"Adr.1311 · = {de(f87n['I_EDS_sek_A'], 4)} A sek."))
        else:
            rows.append(("87N", "EDS", "— DEAKTIVIERT —", "–", "isoliert/kompensiert → U0-Verfahren"))
        if u0["aktiv"]:
            rows += [
                ("U0", "U0> Meldung",   f"{de(u0['U0_Meld_V'], 0)}",  "V", f"7SJ64 · t = {de(u0['t_Meld'], 0)} s"),
                ("U0", "U0>> Abschalt", f"{de(u0['U0_Absch_V'], 0)}", "V", f"7SJ64 · t = {de(u0['t_Absch'], 0)} s"),
            ]
        # 27/59 Spannung: pro Stufe der bezogene Sollwert + Volt-Äquivalent, beide Adressen
        if f2759["aktiv"]:
            for s in f2759["stufen"]:
                ansi = s["name"].split()[0]
                rows.append((ansi, s["name"].split(maxsplit=1)[1],
                             f"{de(s['faktor'], 2)}  ({de(s['U_sek_V'], 0)} V sek.)", "× UnS",
                             f"Adr.{s['adr_bez']} bez. / {s['adr_volt']} V · t {s['adr_t']} = {de(s['t_s'], 2)} s"))
        # 81 Frequenz: pro Stufe Hz-Wert + Adressen
        if f81["aktiv"]:
            for s in f81["stufen"]:
                ansi = s["name"].split()[0]
                rows.append((ansi, s["name"].split(maxsplit=1)[1], f"{de(s['f_Hz'], 1)}", "Hz",
                             f"Adr.{s['adr_f']} · t {s['adr_t']} = {de(s['t_s'], 2)} s"))
        # 24 Übererregung: dimensionsloser Direkteinstellwert
        if f24["aktiv"]:
            rows += [
                ("24", "U/f >",  f"{de(f24['Uf_gt'], 2)}",  "dimensionslos",
                 f"Adr.4302 · t 4303 = {de(f24['t_Uf_gt'], 0)} s · = {de(f24['Uf_gt']*100, 0)} % Nenninduktion"),
                ("24", "U/f >>", f"{de(f24['Uf_gtgt'], 2)}", "dimensionslos",
                 f"Adr.4304 · t 4305 = {de(f24['t_Uf_gtgt'], 1)} s"),
            ]
        # 50BF: Stromschwelle je Seite + Zeitstufen
        if bf["aktiv"]:
            rows += [
                ("50BF", "I> Stromfluss OS", f"{de(bf['I_BF_OS_sek_A'], 3)}", "A sek.",
                 f"LS-I> Stromflussüberw. ({de(bf['I_BF_faktor'], 2)} × IN)"),
                ("50BF", "I> Stromfluss US", f"{de(bf['I_BF_US_sek_A'], 3)}", "A sek.",
                 f"LS-I> Stromflussüberw. ({de(bf['I_BF_faktor'], 2)} × IN)"),
            ]
            if bf["T1_s"] is not None:
                rows.append(("50BF", "T1 (AUS-lokal)", f"{de(bf['T1_s'], 3)}", "s", "Adr.7015"))
            rows.append(("50BF", "T2 (AUS-Sammelschiene)", f"{de(bf['T2_s'], 3)}", "s", "Adr.7016"))
        dft = pd.DataFrame(rows, columns=["ANSI", "Parameter", "Sollwert", "Einheit", "Hinweis / DIGSI-Adresse"])
        st.dataframe(dft, width="stretch", hide_index=True)
