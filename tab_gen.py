"""
tab_gen.py — Streamlit-UI fuer Generatorschutz (SIPROTEC 7UM62)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg
"""

import pandas as pd
import streamlit as st

import konstanten_gen as KG
from calc_gen import berechne_alle


# ── Farbkodierung (identisch zum Trafo-Tab fuer einheitliches Look&Feel) ──────
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


def _pill(status):
    return f'<span class="pill {_PILL_CLASS.get(status,"pill-na")}">{status}</span>'


def _hreg(key):
    h = KG.HERST.get(key)
    if not h:
        return
    adr_pin = (f'<br>📍 <b>Eintragen unter:</b> {h["adr"]}'
               if h.get("adr") else '')
    st.markdown(
        f'<div style="font-size:0.72rem;color:#5d6b82;margin:-6px 0 10px;line-height:1.25;">'
        f'<b>Hersteller:</b> {h["range"]}<br>{h["grund"]}{adr_pin}</div>',
        unsafe_allow_html=True)


# ── Hauptfunktion ─────────────────────────────────────────────────────────────

def show():
    st.markdown(_CSS, unsafe_allow_html=True)

    # ══════════════════════ EINGABEN ══════════════════════
    with _section("Eingaben — Maschinen-Grunddaten, Stromwandler, Spannungswandler, Netz"):
        ci1, ci2, ci3 = st.columns(3, gap="medium")
        with ci1:
            st.caption("**Generator-Grunddaten**")
            Sn  = st.number_input("Sn — Bemessungsleistung [MVA]", 0.1, value=16.0, step=0.5, format="%.1f", key="gen_46")
            UN  = st.number_input("UN — Bemessungsspannung [kV]", 0.4, value=10.5, step=0.1, format="%.1f", key="gen_45")
            cosphi = st.number_input("cos φN — Leistungsfaktor [-]", 0.5, 1.0, value=0.8, step=0.01, format="%.2f", key="gen_44")
            fN  = st.selectbox("fN — Bemessungsfrequenz [Hz]", KG.FN_OPTIONEN, index=0, key="gen_43")
            st.caption("**Reaktanzen (p.u., vom Maschinendatenblatt)**")
            xds = st.number_input("x″d — subtransient [p.u.]", 0.05, 0.5, value=0.14, step=0.01, format="%.2f", key="gen_42")
            xstr= st.number_input("x′d — transient [p.u.]", 0.10, 0.5, value=0.20, step=0.01, format="%.2f", key="gen_41")
            xd  = st.number_input("xd — synchron [p.u.]", 0.8, 3.5, value=2.0, step=0.1, format="%.1f", key="gen_40")
        with ci2:
            st.caption("**Stromwandler (87G: zwei Saetze)**")
            c1, c2 = st.columns(2)
            with c1:
                CT_K_P = st.number_input("CT Klemme prim. [A]", 1, value=1000, step=1, key="gen_39")
                CT_S_P = st.number_input("CT Sternpkt. prim. [A]", 1, value=1000, step=1, key="gen_38")
            with c2:
                CT_K_S = st.selectbox("CT Klemme sek. [A]", [1, 5], index=0, key="gen_37")
                CT_S_S = st.selectbox("CT Sternpkt. sek. [A]", [1, 5], index=0, key="gen_36")
            st.caption("**Spannungswandler**")
            v1, v2 = st.columns(2)
            with v1:
                VT_P = st.number_input("VT prim. [kV]", 0.1, value=10.5, step=0.1, format="%.2f", key="gen_35")
            with v2:
                VT_S = st.number_input("VT sek. [V]", 50.0, 230.0, value=100.0, step=1.0, format="%.1f", key="gen_34")
        with ci3:
            st.caption("**Anschluss & Netz**")
            anschluss = st.selectbox("Generator-Anschluss", KG.ANSCHLUSS_OPTIONEN, index=0, key="gen_33")
            stp_Gen   = st.selectbox("Sternpunktbehandlung Generator", KG.STERNPUNKT_GEN_OPTIONEN, index=1, key="gen_32")
            turbine   = st.selectbox("Antrieb (für 32 Rückleistung)", KG.TURBINEN_OPTIONEN, index=0, key="gen_31")
            Ik_max    = st.number_input("Ik″ max am Anschlusspunkt [kA]", 0.0, value=8.0, step=0.5, format="%.1f", key="gen_30")
            Ik_min    = st.number_input(
                "Ik min am Schutzgebiet-Ende [kA]", 0.0, value=0.0, step=0.1, format="%.2f", key="gen_30b",
                help="Minimaler Kurzschlussstrom nach DIN EN 60909-0 (c=0,95). "
                     "0 = nicht vorhanden, dann Näherung 0,3·Ik″max.")

    # ── Erweiterte Parameter ──────────────────────────────────────────────────
    with _section("Erweiterte Parameter (Voreinstellungen nach SIPROTEC 7UM62 — frei änderbar)", expanded=False):
        st.caption("ℹ️ Unter jedem Regler stehen der Hersteller-Range und die Begründung. "
                   "Adressen beziehen sich auf das 7UM62-Handbuch (C53000-G1100-C149-C).")
        e1, e2, e3 = st.columns(3)
        with e1:
            st.markdown("**87G Differential**")
            k_DIFF  = st.slider("I-DIFF> [I/InO]", 0.05, 1.00, KG.I_DIFF_def, 0.05, key="gen_29")
            _hreg("I_DIFF")
            k_DIFFH = st.slider("I-DIFF>> [I/InO]", 0.5, 12.0, KG.I_DIFF_HH_def, 0.5, key="gen_28")
            _hreg("I_DIFF_HH")
            steig1  = st.slider("Steigung 1", 0.10, 0.50, KG.Steigung_1_def, 0.05, key="gen_27")
            _hreg("Steigung_1")
            steig2  = st.slider("Steigung 2", 0.25, 0.95, KG.Steigung_2_def, 0.05, key="gen_26")
            _hreg("Steigung_2")
            fp2     = st.slider("Fußpunkt 2 [I/InO]", 0.0, 10.0, KG.Fusspunkt_2_def, 0.5, key="gen_25")
            _hreg("Fusspunkt_2")
            harm2   = st.slider("2. Harmonische [%]", 10, 80, int(KG.Harm_2_def*100), 1, key="gen_24") / 100
            _hreg("Harm_2")

            st.markdown("**40 Untererregung**")
            auto_xd = st.checkbox("1/xd KL.1 automatisch aus xd", value=True,
                                  help="1/xd KL.1 = (1/xd)·(CT_prim/IN)·(UN/VT_prim)·1,05", key="gen_23")
            winkel1 = st.slider("WINKEL 1 [°]", 50, 120, KG.Winkel_1_def, 1, key="gen_22")
            _hreg("Winkel_1")
            xd_KL3  = st.slider("1/xd KL.3 (dyn.) [-]", 0.20, 3.00, KG.xd_KL3_def, 0.05, key="gen_21")
            _hreg("xd_KL3")
        with e2:
            st.markdown("**50/51 I> + 51V + I>>**")
            f_I    = st.slider("I> Phase [I/InS]", 1.0, 3.0, KG.f_I_Ph_def, 0.1, key="gen_20")
            _hreg("f_I_Ph")
            t_I    = st.number_input("t I> [s]", 0.0, 60.0, KG.t_I_Ph_def, 0.1, format="%.2f", key="gen_19")
            _hreg("t_I_Ph")
            u_halt = st.slider("U< Haltung [V]", 10.0, 125.0, KG.U_Haltung_def, 1.0, key="gen_18")
            _hreg("U_Haltung")
            f_IHH  = st.slider("I>> Phase [I/InS]", 0.5, 12.0, KG.f_I_Ph_HH_def, 0.5, key="gen_17")
            _hreg("f_I_Ph_HH")
            t_IHH  = st.number_input("t I>> [s]", 0.0, 60.0, KG.t_I_Ph_HH_def, 0.05, format="%.2f", key="gen_16")
            _hreg("t_I_Ph_HH")
            f_Ip   = st.slider("51V Ip [I/InS]", 0.1, 4.0, KG.f_Ip_def, 0.1, key="gen_15")
            _hreg("f_Ip")
            u_amz  = st.slider("51V U< Steuerung [V]", 10.0, 125.0, KG.U_AMZ_def, 1.0, key="gen_14")
            _hreg("U_AMZ")

            st.markdown("**49 Thermisch + 46 Schieflast**")
            kfak   = st.slider("49  k-Faktor [x IN]", 0.5, 2.0, KG.k_Faktor_def, 0.01, key="gen_13")
            _hreg("k_Faktor")
            tau    = st.slider("49  τ_th [s] (Sekunden!)", 30, 32000, int(KG.tau_Gen_def), 10, key="gen_12")
            _hreg("tau_s")
            i2zul  = st.slider("46  I2 zul. [I/InS]", 0.03, 0.30, KG.I2_zul_def, 0.005, format="%.3f", key="gen_11")
            _hreg("I2_zul")
            i2hh   = st.slider("46  I2>> [I/InS]", 0.10, 2.00, KG.I2_HH_def, 0.05, key="gen_10")
            _hreg("I2_HH")
        with e3:
            st.markdown("**32 Rückleistung**")
            prueck = st.slider("Prück> [%] (negativ)", -30.0, -0.5, KG.Prueck_def, 0.1, key="gen_09")
            _hreg("Prueck")

            st.markdown("**32P Vorwärtsleistung**")
            pvorw_aktiv = st.checkbox("32P aktivieren", value=KG.PVorw_aktiv_def, key="gen_pvorw_aktiv")
            pvorw_un = st.slider("P< VORW. [% SN_sek]", 0.5, 120.0, KG.PVorw_un_def, 0.5,
                                 key="gen_pvorw_un")
            _hreg("PVorw_un")
            t_pvorw_un = st.number_input("T P< [s]", 0.0, 60.0, KG.t_PVorw_un_def, 0.5,
                                         format="%.2f", key="gen_t_pvorw_un")
            pvorw_ue = st.slider("P> VORW. [% SN_sek]", 1.0, 120.0, KG.PVorw_ue_def, 0.5,
                                 key="gen_pvorw_ue")
            _hreg("PVorw_ue")
            t_pvorw_ue = st.number_input("T P> [s]", 0.0, 60.0, KG.t_PVorw_ue_def, 0.5,
                                         format="%.2f", key="gen_t_pvorw_ue")

            st.markdown("**24 Übererregung U/f**")
            ufw = st.slider("U/f > (Warnung)", 1.00, 1.20, KG.Uf_Warn_def, 0.01, key="gen_08")
            _hreg("Uf_Warn")
            ufa = st.slider("U/f >> (Auslösung)", 1.00, 1.40, KG.Uf_Aus_def, 0.01, key="gen_07")
            _hreg("Uf_Aus")

    # ── Erweiterte Parameter: Spannungsschutz & Erdschluss ───────────────────────
    with _section("Erweiterte Parameter — Spannungsschutz & Erdschluss (27/59 · 59N · 64R · IEE)",
                  expanded=False):
        st.caption(
            "ℹ️ Alle Funktionen in dieser Gruppe beziehen sich auf Spannungsmessung oder "
            "Erdschlusserfassung und erfordern Spannungswandler- bzw. empfindliche Stromeingangsdaten."
        )
        ev1, ev2 = st.columns(2)
        with ev1:
            st.markdown("**27 Unterspannungsschutz [V]**")
            uk  = st.slider("U< [V]",  10.0, 125.0, KG.U_klein_def,       1.0, key="gen_06")
            _hreg("U_klein")
            ukk = st.slider("U<< [V]", 10.0, 125.0, KG.U_kleinklein_def,  1.0, key="gen_05")
            _hreg("U_kleinklein")
            st.markdown("**59 Überspannungsschutz [V]**")
            ug  = st.slider("U> [V]",  30.0, 170.0, KG.U_gross_def,        1.0, key="gen_04")
            _hreg("U_gross")
            ugg = st.slider("U>> [V]", 30.0, 170.0, KG.U_grossgross_def,   1.0, key="gen_03")
            _hreg("U_grossgross")
        with ev2:
            st.markdown("**59N Ständererdschluss**")
            u0  = st.slider("U0> [V]", 2.0, 125.0, KG.U0_def, 0.5, key="gen_02")
            _hreg("U0")
            st.markdown("**64R Läufererdschluss**")
            re_aus = st.slider("RE AUS [kΩ]", 1.0, 5.0, KG.RE_Aus_def, 0.1, key="gen_01")
            _hreg("RE_Aus")
            st.markdown("**IEE Empfindlicher Erdstromschutz**")
            iee_aktiv = st.checkbox("IEE aktivieren", value=KG.IEE_aktiv_def, key="gen_iee_aktiv",
                                    help="Zweistufige Erfassung am empfindlichen IEE-Eingang (mA). "
                                         "Kann denselben Messeingang wie 59N belegen — "
                                         "Konfliktregel im Handbuch Adr. 151 beachten.")
            iee_an  = st.slider("IEE> Anregung [mA]", 2.0, 200.0, KG.IEE_an_def, 1.0,
                                key="gen_iee_an")
            _hreg("IEE_an")
            t_iee_an = st.number_input("T IEE> [s]", 0.0, 60.0, KG.t_IEE_an_def, 0.5,
                                       format="%.2f", key="gen_t_iee_an")
            iee_aus = st.slider("IEE>> Auslösung [mA]", 2.0, 200.0, KG.IEE_aus_def, 1.0,
                                key="gen_iee_aus")
            _hreg("IEE_aus")
            t_iee_aus = st.number_input("T IEE>> [s]", 0.0, 60.0, KG.t_IEE_aus_def, 0.5,
                                        format="%.2f", key="gen_t_iee_aus")
            iee_ueb = st.slider("IEE< Überwachung [mA] (0 = inaktiv)", 0.0, 50.0,
                                KG.IEE_ueb_def, 0.5, key="gen_iee_ueb")
            _hreg("IEE_ueb")

    # ── Erweiterte Parameter: Reserve- & Spezialfunktionen (21, 78) ───────────
    with _section("Erweiterte Parameter — Impedanzschutz (21) & Außertrittfallschutz (78)",
                  expanded=False):
        st.caption("ℹ️ Beide Funktionen sind im 7UM62 enthalten (Kap. 2.14 / 2.15) und werksseitig "
                   "deaktiviert. Zonen-/Polygon-Impedanzen sind Sekundärwerte; die zugehörige "
                   "Primärreichweite (Z_prim = Z_sek · nVT/kCT) wird im Ergebnis mit angezeigt.")
        ci, ca = st.columns(2)
        with ci:
            st.markdown("**21 Impedanzschutz (Reserve, Seite 2)**")
            imp_aktiv = st.checkbox("21 aktivieren", value=KG.Imp_aktiv_def, key="gen_imp_aktiv")
            imp_fI    = st.slider("IMP I> Anregung [x IN]", 0.5, 2.0, KG.Imp_I_anr_Faktor, 0.05,
                                  key="gen_imp_fI")
            _hreg("Imp_I")
            imp_uhalt = st.checkbox("U<-Haltung (Unterspannungsselbsthaltung)",
                                    value=KG.Imp_Uhalt_def, key="gen_imp_uhalt")
            imp_z1    = st.number_input("ZONE Z1 [Ω sek.]", 0.05, 130.0, KG.Imp_Z1_def, 0.05,
                                        format="%.2f", key="gen_imp_z1")
            _hreg("Imp_Z1")
            imp_tz1   = st.number_input("ZONE1 T1 [s]", 0.0, 60.0, KG.Imp_T_Z1_def, 0.05,
                                        format="%.2f", key="gen_imp_tz1")
            imp_z2    = st.number_input("ZONE Z2 [Ω sek.]", 0.05, 65.0, KG.Imp_Z2_def, 0.05,
                                        format="%.2f", key="gen_imp_z2")
            _hreg("Imp_Z2")
            imp_tz2   = st.number_input("ZONE2 T2 [s]", 0.0, 60.0, KG.Imp_T_Z2_def, 0.05,
                                        format="%.2f", key="gen_imp_tz2")
        with ca:
            st.markdown("**78 Außertrittfallschutz (Polschlupf)**")
            aus_aktiv = st.checkbox("78 aktivieren", value=KG.Aus_aktiv_def, key="gen_aus_aktiv")
            aus_i1    = st.slider("I1> Freigabe [% IN]", 20.0, 400.0, KG.Aus_I1_frei_def, 5.0,
                                  key="gen_aus_i1")
            _hreg("Aus_I1")
            aus_i2    = st.slider("I2< Freigabe [% IN]", 5.0, 100.0, KG.Aus_I2_frei_def, 1.0,
                                  key="gen_aus_i2")
            _hreg("Aus_I2")
            aus_za    = st.number_input("Za (Breite) [Ω sek.]", 0.2, 130.0, KG.Aus_Za_def, 0.1,
                                        format="%.2f", key="gen_aus_za")
            _hreg("Aus_Za")
            aus_zb    = st.number_input("Zb (rückw.) [Ω sek.]", 0.1, 130.0, KG.Aus_Zb_def, 0.1,
                                        format="%.2f", key="gen_aus_zb")
            _hreg("Aus_Zb")
            aus_zc    = st.number_input("Zc (vorw. KL.1) [Ω sek.]", 0.1, 130.0, KG.Aus_Zc_def, 0.1,
                                        format="%.2f", key="gen_aus_zc")
            _hreg("Aus_Zc")
            cphi, ck1, ck2 = st.columns(3)
            with cphi: aus_phi  = st.number_input("PHI [°]", 60.0, 90.0, KG.Aus_Phi_def, 1.0,
                                                  format="%.1f", key="gen_aus_phi")
            with ck1:  aus_nkl1 = st.number_input("KL.1", 1, 10, KG.Aus_n_KL1_def, 1, key="gen_aus_nkl1")
            with ck2:  aus_nkl2 = st.number_input("KL.2", 1, 20, KG.Aus_n_KL2_def, 1, key="gen_aus_nkl2")

    # ── Erweiterte Parameter: 50BF Leistungsschalterversagerschutz ───────────────
    with _section("Erweiterte Parameter — Leistungsschalterversagerschutz (50BF)",
                  expanded=False):
        st.caption(
            "ℹ️ Der Schalterversagerschutz überwacht, ob der Leistungsschalter nach einem Auskommando "
            "innerhalb der Auslösezeit SVS-Taus abschaltet. Tut er es nicht, löst ein übergeordneter "
            "Schalter aus. Nur zwei numerische Einstellgrößen; Adr.7002 AUS INTERN "
            "(BA12 / CFC / Aus) ist eine DIGSI-Konfigurationsoption ohne Zahlenwert."
        )
        cb1, cb2 = st.columns(2)
        with cb1:
            bf_aktiv = st.checkbox("50BF aktivieren", value=KG.BF_aktiv_def, key="gen_bf_aktiv")
            # SVS I>: Range und Default hängen vom CT-Sekundärwert ab
            _ct_sek = CT_K_S   # aus dem Grunddaten-Block (oben bereits eingelesen)
            _i_def  = KG.BF_I_sek_5A_def if _ct_sek == 5 else KG.BF_I_sek_1A_def
            _i_min  = KG.BF_I_sek_5A_min if _ct_sek == 5 else KG.BF_I_sek_1A_min
            _i_max  = KG.BF_I_sek_5A_max if _ct_sek == 5 else KG.BF_I_sek_1A_max
            bf_I = st.slider(
                f"SVS I> [A sek.] (CT {_ct_sek} A)",
                float(_i_min), float(_i_max), float(_i_def), 0.01,
                format="%.2f", key="gen_bf_I")
            _hreg("BF_I")
        with cb2:
            bf_Taus = st.number_input(
                "SVS-Taus [s]", KG.BF_Taus_min, 60.0, KG.BF_Taus_def, 0.01,
                format="%.3f", key="gen_bf_Taus")
            _hreg("BF_Taus")
            st.caption(
                f"Zusammensetzung: t_LS_max (~{KG.BF_t_LS_typ*1000:.0f} ms) "
                f"+ t_RF (~{KG.BF_t_RF_typ*1000:.0f} ms) "
                f"+ t_Marge (~{KG.BF_t_Marge_typ*1000:.0f} ms) "
                f"→ Minimum {(KG.BF_t_LS_typ+KG.BF_t_RF_typ+KG.BF_t_Marge_typ)*1000:.0f} ms."
            )


    with _section("Erweiterte Parameter — Netz-Entkupplung: df/dt (81R) · Vektorsprung",
                  expanded=False):
        st.caption(
            "ℹ️ Beide Funktionen dienen der Netzentkupplung und erfordern Spannungswandler-Daten. "
            "Sie sind im 7UM62 werksseitig deaktiviert. df/dt erfasst Frequenzgradienten; "
            "der Vektorsprung erkennt sprunghafte Phasenwinkeländerungen nach Lastunterbrechung. "
            "Einstellwerte sind anlagenspezifisch — eine Netzuntersuchung wird empfohlen."
        )
        cd, cv = st.columns(2)
        with cd:
            st.markdown("**81R df/dt — Frequenzänderungsschutz**")
            dfdt_aktiv = st.checkbox("81R aktivieren", value=KG.dfdt_aktiv_def,
                                     key="gen_dfdt_aktiv")
            st.caption("Richtung: −df/dt< = Frequenzabfall (Generatorausfall), "
                       "+df/dt> = Frequenzanstieg (Lastabwurf)")
            # 4 Stufen kompakt: je eine Zeile mit Richtung | Ansprechwert | Verzögerung
            dfdt_rich, dfdt_stufe, dfdt_t = [], [], []
            rich_defs  = [KG.dfdt_1_rich_def,  KG.dfdt_2_rich_def,
                          KG.dfdt_3_rich_def,  KG.dfdt_4_rich_def]
            stufe_defs = [KG.dfdt_1_stufe_def, KG.dfdt_2_stufe_def,
                          KG.dfdt_3_stufe_def, KG.dfdt_4_stufe_def]
            t_defs     = [KG.dfdt_1_t_def, KG.dfdt_2_t_def,
                          KG.dfdt_3_t_def, KG.dfdt_4_t_def]
            for i in range(4):
                st.markdown(f"*Stufe df{i+1}/dt*")
                col_r, col_s, col_t = st.columns([1.4, 1.2, 1.2])
                with col_r:
                    r_val = st.selectbox(
                        "Richtung", KG.DFDT_RICHTUNG_OPTIONEN,
                        index=KG.DFDT_RICHTUNG_OPTIONEN.index(rich_defs[i]),
                        key=f"gen_dfdt_{i+1}_rich", label_visibility="collapsed")
                with col_s:
                    s_val = st.number_input(
                        "Hz/s", 0.1, 10.0, stufe_defs[i], 0.1,
                        format="%.1f", key=f"gen_dfdt_{i+1}_stufe",
                        label_visibility="collapsed")
                with col_t:
                    t_val = st.number_input(
                        "t [s]", 0.0, 60.0, t_defs[i], 0.05,
                        format="%.2f", key=f"gen_dfdt_{i+1}_t",
                        label_visibility="collapsed")
                dfdt_rich.append(r_val)
                dfdt_stufe.append(s_val)
                dfdt_t.append(t_val)
            if i == 3:
                _hreg("dfdt_stufe")
            dfdt_Umin = st.slider("U_MIN [V] (Blockiergrenze)", 10.0, 125.0,
                                  KG.dfdt_Umin_def, 1.0, key="gen_dfdt_Umin")
            _hreg("dfdt_Umin")
        with cv:
            st.markdown("**Vektorsprung — Phasenwinkelsprung-Erkennung**")
            vs_aktiv = st.checkbox("Vektorsprung aktivieren", value=KG.VS_aktiv_def,
                                   key="gen_vs_aktiv")
            vs_dphi = st.slider("DELTA PHI [°]", 2, 30, int(KG.VS_dphi_def), 1,
                                key="gen_vs_dphi")
            _hreg("VS_dphi")
            vs_t_dphi = st.number_input("T DELTA PHI [s]", 0.0, 60.0, KG.VS_t_dphi_def, 0.05,
                                        format="%.2f", key="gen_vs_t_dphi")
            vs_t_reset = st.number_input("T RESET [s]", 0.1, 60.0, KG.VS_t_reset_def, 0.5,
                                         format="%.2f", key="gen_vs_t_reset")
            _hreg("VS_t_reset")
            st.caption("Spannungsarbeitsbereich (Advanced-Parameter Adr.4605A/4606A):")
            cv1, cv2 = st.columns(2)
            with cv1:
                vs_Umin = st.number_input("U_MIN [V]", 10.0, 125.0, KG.VS_Umin_def, 1.0,
                                          format="%.0f", key="gen_vs_Umin")
            with cv2:
                vs_Umax = st.number_input("U_MAX [V]", 10.0, 170.0, KG.VS_Umax_def, 1.0,
                                          format="%.0f", key="gen_vs_Umax")

    # ══════════════════════ BERECHNUNG ══════════════════════
    p = dict(
        Sn_MVA=Sn, UN_kV=UN, cos_phi=cosphi, fN=fN,
        xd_strich=xstr, xd_subtrans=xds, xd=xd,
        anschluss=anschluss, stp_Gen=stp_Gen, turbine=turbine,
        CT_K_Prim=CT_K_P, CT_K_Sek=CT_K_S, CT_S_Prim=CT_S_P, CT_S_Sek=CT_S_S,
        VT_Prim_kV=VT_P, VT_Sek_V=VT_S, Ik_max_kA=Ik_max, Ik_min_kA=Ik_min,
        I_DIFF=k_DIFF, I_DIFF_HH=k_DIFFH, Steigung_1=steig1, Steigung_2=steig2,
        Fusspunkt_2=fp2, Harm_2=harm2,
        f_I_Ph=f_I, t_I_Ph=t_I, U_Haltung=u_halt, f_I_Ph_HH=f_IHH, t_I_Ph_HH=t_IHH,
        f_Ip=f_Ip, U_AMZ=u_amz,
        k_Faktor=kfak, tau_s=tau, I2_zul=i2zul, I2_HH=i2hh,
        auto_xd_KL1=auto_xd, winkel_1=winkel1, xd_KL3=xd_KL3,
        Prueck=prueck,
        PVorw_aktiv=pvorw_aktiv, PVorw_un=pvorw_un, t_PVorw_un=t_pvorw_un,
        PVorw_ue=pvorw_ue, t_PVorw_ue=t_pvorw_ue,
        Uf_Warn=ufw, Uf_Aus=ufa,
        U_klein=uk, U_kleinklein=ukk, U_gross=ug, U_grossgross=ugg,
        U0=u0,
        IEE_aktiv=iee_aktiv, IEE_an=iee_an, t_IEE_an=t_iee_an,
        IEE_aus=iee_aus, t_IEE_aus=t_iee_aus, IEE_ueb=iee_ueb,
        RE_Aus=re_aus,
        dfdt_aktiv=dfdt_aktiv,
        dfdt_1_rich=dfdt_rich[0], dfdt_1_stufe=dfdt_stufe[0], dfdt_1_t=dfdt_t[0],
        dfdt_2_rich=dfdt_rich[1], dfdt_2_stufe=dfdt_stufe[1], dfdt_2_t=dfdt_t[1],
        dfdt_3_rich=dfdt_rich[2], dfdt_3_stufe=dfdt_stufe[2], dfdt_3_t=dfdt_t[2],
        dfdt_4_rich=dfdt_rich[3], dfdt_4_stufe=dfdt_stufe[3], dfdt_4_t=dfdt_t[3],
        dfdt_Umin=dfdt_Umin,
        VS_aktiv=vs_aktiv, VS_dphi=float(vs_dphi), VS_t_dphi=vs_t_dphi,
        VS_t_reset=vs_t_reset, VS_Umin=vs_Umin, VS_Umax=vs_Umax,
        BF_aktiv=bf_aktiv, BF_I_sek=bf_I, BF_Taus=bf_Taus,
        Imp_aktiv=imp_aktiv, Imp_I_Faktor=imp_fI, Imp_Uhalt=imp_uhalt,
        Imp_Z1=imp_z1, Imp_T_Z1=imp_tz1, Imp_Z2=imp_z2, Imp_T_Z2=imp_tz2,
        Aus_aktiv=aus_aktiv, Aus_I1_frei=aus_i1, Aus_I2_frei=aus_i2,
        Aus_Za=aus_za, Aus_Zb=aus_zb, Aus_Zc=aus_zc,
        Aus_Phi=aus_phi, Aus_n_KL1=aus_nkl1, Aus_n_KL2=aus_nkl2,
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

    todo = [c for c in plaus if c["status"] in ("Prüfen!", "Fehlt") and c["korrektur"]]
    hinw = [c for c in plaus if c["status"] == "Hinweis" and c["korrektur"]]
    if todo:
        items = "".join(
            f'<li style="margin-bottom:6px;"><b>{c["pruefung"]}</b> '
            f'(Ergebnis: {c["ergebnis"]})<br>'
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
                    'Die berechneten Werte sind konsistent und entsprechen der 7UM62-/FNN-Methodik. '
                    'Bewusste Abweichungen bleiben dir überlassen.</div>', unsafe_allow_html=True)

    # ══════════════════════ BERECHNETE GRUNDGRÖSSEN ══════════════════════
    with _section("Berechnete Grundgrößen"):
        g1, g2, g3 = st.columns(3)
        with g1:
            _metric("IN Maschine primär", f"{g['IN_prim']:.2f} A", "= Sn / (√3 · UN)")
            _metric("IN Klemmenseite sek.", f"{g['IN_K_sek']:.4f} A", f"÷ kCT_K = {g['kCT_K']:.0f}")
            _metric("STW-Anpassung Klemme", f"{g['I_an_K']:.3f}", "I_an = CT_sek / IN_sek (Soll 0,5–2,0)")
        with g2:
            _metric("IN Sternpunktseite sek.", f"{g['IN_S_sek']:.4f} A", f"÷ kCT_S = {g['kCT_S']:.0f}")
            _metric("STW-Anpassung Sternpunkt", f"{g['I_an_S']:.3f}", "I_an = CT_sek / IN_sek (Soll 0,5–2,0)")
            _metric("Übersetzung nVT", f"{g['nVT']:.1f}", "= UN_prim / UN_sek")
        with g3:
            _metric("UN sekundär", f"{g['UN_sek']:.1f} V")
            _metric("SN sekundär", f"{g['SN_sek']:.2f} VA", "= √3 · UN_sek · IN_sek → 32")
            _metric("Bezugsstrom IN_Obj sek.", f"{g['IN_Obj_sek']:.4f} A", "= IN Klemmenseite → 87G")

    # ══════════════════════ 87G DIFFERENTIALSCHUTZ ══════════════════════
    r = e["87G"]
    with _section("ANSI 87G — Ständerdifferentialschutz"):
        d1, d2 = st.columns(2)
        with d1: _metric("I-DIFF> sekundär", f"{r['I_DIFF_Anspr_sek_A']:.4f} A", f"= {p['I_DIFF']*100:.0f}% × IN_Obj")
        with d2: _metric("I-DIFF>> sekundär", f"{r['I_DIFF_HH_sek_A']:.4f} A", f"Empfehlung ≈ 1/x′d = {r['emp_IDIFFHH']:g} ×IN")
        df87 = pd.DataFrame([{
            "Parameter": x["name"], "Eingabe": f"{x['faktor']:g}", "Einheit": x["einheit"],
            "A sek.": f"{x['wert_sek']:.4f}" if x["wert_sek"] is not None else "—",
            "A prim.": f"{x['wert_prim']:.2f}" if x["wert_prim"] is not None else "—",
            "Empfehlung": f"{x['empfehlung']:g}" if x["empfehlung"] is not None else "—",
            "Status": f"{_AMPEL_EMOJI.get(x['status'],'')} {x['status']}",
            "Adresse": x["adresse"],
        } for x in r["rows"]])
        st.dataframe(df87, width="stretch", hide_index=True)
        st.caption("I-DIFF>> (unstabilisiert) aus transienter Reaktanz: ≈ 1/x′d, typ. (3…7)·IN "
                   "(7UM62 Hdb. 2.9). Differentialmethodik identisch zum 7UT613 → Herstellerneutralität.")

    # ══════════════════════ 50/51 + 51V ÜBERSTROM ══════════════════════
    umz, v51 = e["5051"], e["51V"]
    with _section("ANSI 50/51 + 51V — Überstromzeitschutz (Reserveschutz)"):
        dfu = pd.DataFrame([
            ("I> (50/51) + U<-Haltung", f"{umz['f_I']:g}", "I/InS", f"{umz['I_sek']:.4f}", f"{umz['I_prim']:.1f}", f"{umz['t_I']:.2f}"),
            ("I>> (50)",               f"{umz['f_IHH']:g}", "I/InS", f"{umz['IHH_sek']:.4f}", f"{umz['IHH_prim']:.1f}", f"{umz['t_IHH']:.2f}"),
            ("Ip (51V spannungsabh.)", f"{v51['f_Ip']:g}", "I/InS", f"{v51['Ip_sek']:.4f}", f"{v51['Ip_prim']:.1f}", f"{v51['T_Ip']:.2f}"),
        ], columns=["Funktion", "Faktor", "Einheit", "I [A sek.]", "I [A prim.]", "t / T_Ip [s]"])
        st.dataframe(dfu, width="stretch", hide_index=True)
        st.caption(f"U<-Haltung: {umz['U_Haltung']:.0f} V (Adr.1205) — speichert die I>-Anregung bei "
                   f"Spannungseinbruch, sodass der abklingende Generator-KS-Strom (1/xd) sicher erfasst wird. "
                   f"51V-Steuerung: U< = {v51['U_AMZ']:.0f} V ≈ {v51['U_AMZ_pct']:.0f}% UN_sek (Adr.1408), "
                   f"Kennlinie {v51['kennlinie']}.")

    # ══════════════════════ 49 + 46 ══════════════════════
    b49, b46 = e["49"], e["46"]
    with _section("ANSI 49 (thermisch) + ANSI 46 (Schieflast)"):
        t1, t2, t3 = st.columns(3)
        with t1:
            _metric("49  I_max_zul sek.", f"{b49['I_max_zul_sek']:.4f} A", f"= {b49['k_Faktor']:.2f} × IN_sek")
            _metric("49  Θ-Warnstufe", f"{b49['Theta_Warn_pct']:.0f} %", f"I-Warn = {b49['I_Warn_sek']:.4f} A sek.")
        with t2:
            _metric("49  τ thermisch", f"{b49['tau_s']:.0f} s", "Adr.1603")
            _metric("49  I_max_zul prim.", f"{b49['I_max_zul_prim']:.2f} A")
        with t3:
            _metric("46  I2 zulässig sek.", f"{b46['I2_zul_sek']:.4f} A", f"= {b46['I2_zul_faktor']*100:.1f}% × IN_sek")
            _metric("46  I2>> Anregung sek.", f"{b46['I2_HH_sek']:.4f} A", f"= {b46['I2_HH_faktor']*100:.0f}% × IN_sek · t = {b46['t_I2_HH']:.1f} s")
            _metric("46  K / Abkühlzeit", f"{b46['Faktor_K']:.1f} s / {b46['t_Abkuehl']:.0f} s", "Adr.1704 / 1705")
        st.caption("Hinweis: Zeitkonstante τ wird im 7UM62 in **SEKUNDEN** eingegeben (Adr. 1603). ")

    # ══════════════════════ 40 UNTERERREGUNG ══════════════════════
    f40 = e["40"]
    with _section("ANSI 40 — Untererregungsschutz (Admittanzkennlinien)"):
        df40 = pd.DataFrame([
            ("Kennlinie 1 (statische Stab.)", f"{f40['xd_KL1']:.2f}", f"{f40['winkel_1']}°", f"{f40['t_KL1']:.1f}", "Adr.3002 / 3003 / 3004"),
            ("Kennlinie 2 (Mindesterregung)", f"{f40['xd_KL2']:.2f}", f"{f40['winkel_2']}°", f"{f40['t_KL2']:.1f}", "Adr.3005 / 3006 / 3007"),
            ("Kennlinie 3 (dynam. Stab.)",    f"{f40['xd_KL3']:.2f}", f"{f40['winkel_3']}°", f"{f40['t_KL3']:.1f}", "Adr.3008 / 3009 / 3010"),
        ], columns=["Kennlinie", "1/xd [-]", "Winkel α", "t [s]", "Adresse"])
        st.dataframe(df40, width="stretch", hide_index=True)
        modus = "automatisch aus xd" if f40["auto"] else "manuell"
        st.caption(f"1/xd KL.1 = {f40['xd_KL1']:.2f} ({modus}): (1/xd)·(CT_prim/IN)·(UN/VT_prim)·1,05. "
                   f"KL.2 = 0,9·KL.1 (Mindesterregung), KL.3 zwischen xd und x′d (>1, dynamische Stabilität). "
                   f"T KURZ U< = {f40['t_kurz_Uerr']:.2f} s bei Erregerspannungsausfall (7UM62 Hdb. 2.11).")

    # ══════════════════════ 21 IMPEDANZ + 78 AUSSERTRITT ══════════════════════
    f21, f78 = e["21"], e["78"]
    with _section("ANSI 21 — Impedanzschutz (Reserve) · ANSI 78 — Außertrittfallschutz"):
        st.caption(f"Sekundär→Primär-Umrechnung: Z_prim = Z_sek · nVT/kCT = Z_sek / {f21['k_Z']:.3f} "
                   f"(kCT_K = {g['kCT_K']:.0f}, nVT = {g['nVT']:.1f}). "
                   "Beide Funktionen sind werksseitig deaktiviert; die Werte dienen als Auslegungshilfe.")

        # ── 21 Impedanzschutz ──
        st.markdown("**ANSI 21 — Impedanzschutz** " +
                    ("🟢 aktiviert" if f21["aktiv"] else "⚫ deaktiviert (Voreinstellung)"))
        c1, c2, c3 = st.columns(3)
        with c1: _metric("IMP I> Anregung sek.", f"{f21['I_anr_sek']:.4f} A", f"= {f21['f_I_anr']:g} × IN · Adr.3302")
        with c2: _metric("IMP I> Anregung prim.", f"{f21['I_anr_prim']:.1f} A", "über max. Last")
        with c3: _metric("U<-Haltung", "Ein" if f21["U_halt_aktiv"] else "Aus",
                         f"U< = {f21['U_halt']:.0f} V · T = {f21['T_halt']:.1f} s · Adr.3303–3305")
        df21 = pd.DataFrame([
            ("Zone Z1",          f"{f21['Z1_sek']:.2f}",  f"{f21['Z1_prim']:.3f}",  f"{f21['t_Z1']:.2f}",  "Adr.3306 / 3307"),
            ("Übergreifst. Z1B", f"{f21['Z1B_sek']:.2f}", f"{f21['Z1B_prim']:.3f}", f"{f21['t_Z1B']:.2f}", "Adr.3308 / 3309"),
            ("Zone Z2",          f"{f21['Z2_sek']:.2f}",  f"{f21['Z2_prim']:.3f}",  f"{f21['t_Z2']:.2f}",  "Adr.3310 / 3311"),
            ("Endzeitstufe T END", "—", "—", f"{f21['T_End']:.2f}", "Adr.3312"),
        ], columns=["Stufe", "Z [Ω sek.]", "Z [Ω prim.]", "t [s]", "Adresse"])
        st.dataframe(df21, width="stretch", hide_index=True)
        st.caption("Reserve-/Zeitstaffelschutz für Kurzschlüsse in Maschine, Ableitung und Maschinentrafo "
                   "(arbeitet mit den Strömen der Seite 2). Die Zonen-Reichweite ist aus der zu schützenden "
                   "Impedanz zu bemessen (in Blockschaltung Z1 typ. bis ~70 % in den Maschinentrafo); die "
                   "Hersteller-Voreinstellungen sind generische DIGSI-Werte (7UM62 Hdb. 2.14).")

        # ── 78 Außertrittfallschutz ──
        st.markdown("**ANSI 78 — Außertrittfallschutz (Polschlupf)** " +
                    ("🟢 aktiviert" if f78["aktiv"] else "⚫ deaktiviert (Voreinstellung)"))
        c1, c2, c3 = st.columns(3)
        with c1: _metric("I1> Freigabe", f"{f78['I1_frei_pct']:.0f} %", f"= {f78['I1_frei_sek']:.4f} A sek · Adr.3502")
        with c2: _metric("I2< Freigabe (Sperre)", f"{f78['I2_frei_pct']:.0f} %", f"= {f78['I2_frei_sek']:.4f} A sek · Adr.3503")
        with c3: _metric("Polygon / Zählung", f"φ = {f78['phi']:.0f}°", f"KL.1 = {f78['n_KL1']} · KL.2 = {f78['n_KL2']} Pendelungen")
        df78 = pd.DataFrame([
            ("Za (Resistanz/Breite)",   f"{f78['Za_sek']:.2f}",   f"{f78['Za_prim']:.3f}",   "Adr.3504"),
            ("Zb (Reaktanz rückw.)",    f"{f78['Zb_sek']:.2f}",   f"{f78['Zb_prim']:.3f}",   "Adr.3505"),
            ("Zc (Reaktanz vorw. KL.1)",f"{f78['Zc_sek']:.2f}",   f"{f78['Zc_prim']:.3f}",   "Adr.3506"),
            ("Zd−Zc (Reaktanzdiff. KL.2)",f"{f78['ZdZc_sek']:.2f}",f"{f78['ZdZc_prim']:.3f}", "Adr.3507"),
        ], columns=["Polygon-Größe", "Z [Ω sek.]", "Z [Ω prim.]", "Adresse"])
        st.dataframe(df78, width="stretch", hide_index=True)
        st.caption(f"Erkennt Polschlupf über den Verlauf des Mitsystem-Impedanzzeigers im Polygon. "
                   f"I1> gibt erst oberhalb Nennstrom frei, I2< sperrt bei Unsymmetrie (symmetrischer Vorgang). "
                   f"Haltezeit T = {f78['T_halt']:.0f} s (Adr.3511), Meldezeit {f78['T_meld']:.2f} s (Adr.3512). "
                   "Das Polygon ist aus x′d der Maschine und der Netz-/Trafoimpedanz zu bemessen (7UM62 Hdb. 2.15).")

    # ══════════════════════ 32 RÜCKLEISTUNG ══════════════════════
    f32 = e["32"]
    with _section("ANSI 32 — Rückleistungsschutz"):
        c1, c2, c3 = st.columns(3)
        with c1: _metric("Prück> Einstellwert", f"{f32['Prueck_pct']:.2f} %", f"{_AMPEL_EMOJI[f32['status']]} bzgl. SN_sek (negativ)")
        with c2: _metric("Prück> sekundär", f"{f32['Prueck_W']:.2f} W", f"= {f32['Prueck_pct']:.2f}% × SN_sek")
        with c3: _metric("Verzögerungen", f"{f32['t_o_SSchl']:.0f} / {f32['t_m_SSchl']:.1f} s", "ohne / mit Schnellschluss")
        st.caption(f"Antrieb **{f32['turbine']}** → Empfehlung ≈ {f32['emp_pct']:.1f}% von SN "
                   "(Dampf 1–3 %, Gas 3–30 %, Diesel >5 %). Einstellwert ≈ 0,5 × gemessene Schleppleistung "
                   "(7UM62 Hdb. 2.12, Adr.3102). Bei Gasturbinen T m.S-SCHL. ≈ 0,5 s.")

    # ══════════════════════ 32P VORWÄRTSLEISTUNG ══════════════════════
    f32P = e["32P"]
    with _section("ANSI 32P — Vorwärtsleistungsüberwachung"):
        if not f32P["vt_ok"]:
            st.markdown('<div class="warn-box">⚠️ <b>VT-Daten fehlen:</b> Spannungswandler prim./sek. '
                        'eingeben, damit SN_sek berechnet und die Wattwerte umgerechnet werden können.</div>',
                        unsafe_allow_html=True)
        aktiv_str = "🟢 aktiviert" if f32P["aktiv"] else "⚫ deaktiviert (Voreinstellung)"
        st.markdown(f"**ANSI 32P — Vorwärtsleistungsüberwachung** {aktiv_str}")
        c1, c2 = st.columns(2)
        with c1:
            _metric("P< VORW. (Unterschreitung)",
                    f"{f32P['P_un_pct']:.1f} % · {f32P['P_un_W']:.1f} W",
                    f"t = {f32P['t_un']:.2f} s · Adr.3202 / 3203")
        with c2:
            _metric("P> VORW. (Überschreitung)",
                    f"{f32P['P_ue_pct']:.1f} % · {f32P['P_ue_W']:.1f} W",
                    f"t = {f32P['t_ue']:.2f} s · Adr.3204 / 3205")
        st.caption(
            f"Bezugsgröße: SN_sek = {f32P['SN_sek']:.1f} VA = √3 · UN_sek · IN_sek. "
            "P< erfasst Schwachlast vor der Rückleistungsgrenze (Einstellwert > |Prück>|). "
            "P> überwacht die maximale Wirkleistung (z. B. für Lastabwurf oder Netzentkupplung). "
            "Messverfahren (Adr.3206A): genau (16-Perioden-Mittelung, Normalbetrieb) oder "
            "schnell (ohne Mittelung, für Netzentkupplungsanwendungen).")


    f24, f2759, f81 = e["24"], e["2759"], e["81"]
    with _section("ANSI 24 (U/f) · 27/59 (Spannung) · 81 (Frequenz)"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**24 Übererregung U/f**")
            df24 = pd.DataFrame([
                ("U/f > (Warnung)", f"{f24['Uf_Warn']:.2f}", f"{f24['t_Uf_Warn']:.1f}", "Adr.4302 / 4303"),
                ("U/f >> (Auslösung)", f"{f24['Uf_Aus']:.2f}", f"{f24['t_Uf_Aus']:.1f}", "Adr.4304 / 4305"),
            ], columns=["Stufe", "U/f [-]", "t [s]", "Adresse"])
            st.dataframe(df24, width="stretch", hide_index=True)
            st.markdown("**81 Frequenz (fN = %d Hz)**" % f81["fN"])
            df81 = pd.DataFrame([
                (s["name"], f"{s['f']:.2f}", f"{s['t']:.1f}", s["adr"]) for s in f81["stufen"]
            ], columns=["Stufe", "f [Hz]", "t [s]", "Adresse"])
            st.dataframe(df81, width="stretch", hide_index=True)
        with c2:
            st.markdown("**27/59 Unter-/Überspannung**")
            df27 = pd.DataFrame([
                ("U<  (27)",  f"{f2759['U_klein']:.0f}", f"{f2759['U_klein_pct']:.0f}", f"{f2759['t_U_klein']:.1f}", "Adr.4002 / 4003"),
                ("U<< (27)",  f"{f2759['U_kleinklein']:.0f}", f"{f2759['U_kleinklein_pct']:.0f}", f"{f2759['t_U_kleinklein']:.1f}", "Adr.4004 / 4005"),
                ("U>  (59)",  f"{f2759['U_gross']:.0f}", f"{f2759['U_gross_pct']:.0f}", f"{f2759['t_U_gross']:.1f}", "Adr.4102 / 4103"),
                ("U>> (59)",  f"{f2759['U_grossgross']:.0f}", f"{f2759['U_grossgross_pct']:.0f}", f"{f2759['t_U_grossgross']:.1f}", "Adr.4104 / 4105"),
            ], columns=["Stufe", "U [V]", "% UN", "t [s]", "Adresse"])
            st.dataframe(df27, width="stretch", hide_index=True)
            st.caption("Turbogeneratoren dauerhaft bis ~95 % fN (bei reduzierter Leistung), kurzzeitig "
                       "bis ~48 Hz (7UM62 Hdb. 2.18).")

    # ══════════════════════ 81R df/dt + VEKTORSPRUNG ══════════════════════
    f81R, fVS = e["81R"], e["VS"]
    with _section("ANSI 81R — df/dt-Schutz · Vektorsprung — Netz-Entkupplung"):
        st.caption(
            "Beide Funktionen ergänzen den statischen Frequenzschutz (81) für schnelle "
            "Netzentkupplungsanwendungen. Einstellwerte sind anlagenspezifisch — "
            "eine Netzberechnung wird empfohlen (7UM62 Hdb. Kap. 2.21 / 2.22)."
        )
        aktiv81R = "🟢 aktiviert" if f81R["aktiv"] else "⚫ deaktiviert (Voreinstellung)"
        st.markdown(f"**ANSI 81R — Frequenzänderungsschutz df/dt** {aktiv81R}")
        if not f81R["vt_ok"]:
            st.markdown('<div class="warn-box">⚠️ <b>VT-Daten fehlen:</b> df/dt erfordert '
                        'Spannungswandler-Daten für die Frequenzmessung.</div>',
                        unsafe_allow_html=True)
        df_dfdt = pd.DataFrame([
            (s["name"], s["richtung"], f"{s['stufe']:.1f}",
             f"{s['t']:.2f}",
             f"{s['adr_r']} / {s['adr_s']} / {s['adr_t']}")
            for s in f81R["stufen"]
        ], columns=["Stufe", "Richtung", "|df/dt| [Hz/s]", "t [s]", "Adressen"])
        st.dataframe(df_dfdt, width="stretch", hide_index=True)
        umin_icon = "🟢" if f81R["umin_ok"] else "🟡"
        st.caption(
            f"U_MIN = {f81R['Umin']:.0f} V = {f81R['Umin_pct']:.0f} % UN_sek {umin_icon} "
            f"(Empfehlung ~65 %, Adr.4518). "
            "Näherungsformel: |df/dt| = fN / (2H) · |ΔP/SN|, H = Trägheitskonstante [s]. "
            "Stufen 1/2 für langsame Gradienten (≤1 Hz/s, verzögert), "
            "Stufen 3/4 für schnelle Gradienten (≥4 Hz/s, unverzögert) — symmetrisch voreingestellt."
        )
        st.markdown("---")
        aktiv_vs = "🟢 aktiviert" if fVS["aktiv"] else "⚫ deaktiviert (Voreinstellung)"
        st.markdown(f"**Vektorsprung** {aktiv_vs}")
        if not fVS["vt_ok"]:
            st.markdown('<div class="warn-box">⚠️ <b>VT-Daten fehlen:</b> Vektorsprung '
                        'erfordert Spannungswandler-Daten.</div>', unsafe_allow_html=True)
        cv1, cv2, cv3 = st.columns(3)
        with cv1:
            _metric("DELTA PHI",
                    f"{fVS['dphi']:.0f} °",
                    f"Adr.4602 · T = {fVS['t_dphi']:.2f} s (Adr.4603)")
        with cv2:
            _metric("T RESET (Selbstreset)",
                    f"{fVS['t_reset']:.2f} s",
                    "Adr.4604 — vor Wiedereinschaltung abwarten")
        with cv3:
            uband_icon = "🟢" if fVS["uband_ok"] else "🔴"
            _metric("Spannungsband",
                    f"{fVS['Umin']:.0f} … {fVS['Umax']:.0f} V",
                    f"{fVS['Umin_pct']:.0f} … {fVS['Umax_pct']:.0f} % UN_sek "
                    f"{uband_icon} · Adr.4605A / 4606A")
        st.caption(
            "Erkennt sprunghafte Phasenwinkeländerung der Mitsystemspannung (Δφ) nach Stromunterbrechung. "
            "DELTA PHI anlagenspezifisch aus Netz-Kurzschlussimpedanz und typischer Lastsprungsgröße bestimmen. "
            f"Voreinstellung {int(KG.VS_dphi_def)}° ist ein konservativer Ausgangswert; "
            "zu empfindlich eingestellt → Fehlauslösung bei normalen Lastschaltvorgängen (7UM62 Hdb. 2.22)."
        )


    f59n, f64r, fIEE = e["59N"], e["64R"], e["IEE"]
    with _section("ANSI 59N/64G — Ständererdschluss 90 % · ANSI 64R — Läufererdschluss · IEE — Empfindlicher Erdstromschutz"):
        c1, c2 = st.columns(2)
        with c1:
            _metric("59N  U0> Verlagerungsspannung", f"{f59n['U0']:.1f} V", f"= {f59n['U0_pct']:.0f}% voller Verlagerung")
            _metric("59N  Schutzbereich Ständer", f"{f59n['schutzbereich_pct']:.0f} %", f"3I0> = {f59n['I3I0']:.0f} mA · Winkel {f59n['winkel']}° · t = {f59n['t_SES']:.2f} s")
            st.caption("100 % Ständererdschluss zusätzlich über 3. Harmonische bzw. 20-Hz-Verspannung "
                       "(7UM62 Hdb. 2.24/2.25) — gemeinsam mit 90 % = vollständiger Wicklungsschutz.")
        with c2:
            _metric("64R  RE-Warnstufe", f"{f64r['RE_Warn']:.1f} kΩ", f"t = {f64r['t_RE_Warn']:.1f} s · Adr.6002")
            _metric("64R  RE-Auslösestufe", f"{f64r['RE_Aus']:.1f} kΩ", f"t = {f64r['t_RE_Aus']:.2f} s · Adr.6003")
            st.caption("Läufererdschluss (R, fn) über Bürsten-Ankopplung. Alternativ 1–3-Hz-Verfahren "
                       "(7UM62 Hdb. 2.31) für empfindliche/bürstenlose Anwendungen.")
        if f59n["stp"] == "Isoliert":
            st.markdown('<div class="info-box">🟢 <b>Isolierter Sternpunkt:</b> 90 %-Erfassung über '
                        'U0/3I0-Richtung (sin-φ-Schaltung, Winkel ~90°), bei ausreichender Kabelkapazität '
                        'auch ohne Erdungstransformator (7UM62 Hdb. 2.23).</div>', unsafe_allow_html=True)

        # ── IEE empfindlicher Erdstromschutz ──
        st.markdown("---")
        aktiv_str = "🟢 aktiviert" if fIEE["aktiv"] else "⚫ deaktiviert (Voreinstellung)"
        st.markdown(f"**IEE — Empfindlicher Erdstromschutz** (Adr. 5101–5106) {aktiv_str}")
        df_iee = pd.DataFrame([
            ("IEE>  (Anregung / Warnstufe)", f"{fIEE['IEE_an']:.1f}",  f"{fIEE['t_IEE_an']:.2f}",  "Adr.5102 / 5103"),
            ("IEE>> (Auslösung)",            f"{fIEE['IEE_aus']:.1f}", f"{fIEE['t_IEE_aus']:.2f}", "Adr.5104 / 5105"),
        ], columns=["Stufe", "I [mA]", "t [s]", "Adresse"])
        st.dataframe(df_iee, width="stretch", hide_index=True)
        if fIEE["ueb_aktiv"]:
            st.caption(f"IEE< Überwachungsstufe: {fIEE['IEE_ueb']:.1f} mA (Adr.5106) — "
                       "Messkreisüberwachung aktiv (typisch bei Läufererdschluss-Verspannung).")
        else:
            st.caption("IEE< Überwachungsstufe: inaktiv (0 mA, Adr.5106). "
                       "Aktivieren, wenn der Läuferkreis mit Netzfrequenz verspannt wird (~2 mA typisch).")
        st.caption(
            "Alle Werte direkt in mA am empfindlichen IEE-Eingang — keine CT-Umrechnung erforderlich. "
            "IEE> bemessen für RE ≈ 3–5 kΩ, IEE>> für RE ≈ 1,5 kΩ. "
            "WICHTIG: Kann denselben IEE2-Messeingang wie 59N belegen → Konfliktregel Adr.151 im "
            "DIGSI-Projektierungsmenü beachten (7UM62 Hdb. 2.26)."
        )

    # ══════════════════════ 50BF LEISTUNGSSCHALTERVERSAGERSCHUTZ ══════════════════════
    fBF = e["50BF"]
    with _section("ANSI 50BF — Leistungsschalterversagerschutz"):
        aktiv_bf = "🟢 aktiviert" if fBF["aktiv"] else "⚫ deaktiviert (Voreinstellung)"
        st.markdown(f"**ANSI 50BF — Leistungsschalterversagerschutz** {aktiv_bf}")
        c1, c2, c3 = st.columns(3)
        with c1:
            i_icon = "🟢" if fBF["I_ok"] else "🔴"
            _metric("SVS I> Stromansprechschwelle",
                    f"{fBF['I_sek']:.3f} A sek. {i_icon}",
                    f"= {fBF['I_prim']:.1f} A prim. · CT {fBF['CT_sek']} A · Adr.7003")
        with c2:
            t_icon = "🟢" if fBF["Taus_ok"] else "🟡"
            _metric("SVS-Taus Auslösezeit",
                    f"{fBF['Taus']:.3f} s {t_icon}",
                    f"Minimum {fBF['Taus_min_emp']:.3f} s · Adr.7004")
        with c3:
            _metric("Empfehlung SVS I> (DIGSI-Default-Ratio)",
                    f"{fBF['emp_I_sek']:.4f} A sek.",
                    f"≈ 20 % IN_sek · 10 % unter I_min_Betrieb einstellen")
        st.caption(
            "**SVS I>** (Adr.7003): Stromansprechschwelle für alle drei Phasen. "
            "Mindestens 10 % unterhalb des kleinsten erwarteten Betriebsstroms — "
            "aber nicht zu niedrig, da CT-Ausgleichsvorgänge die Rückfallzeit verlängern können. "
            "Voreinstellung abhängig vom CT-Sekundärstrom "
            f"({'0,20 A' if fBF['CT_sek']==1 else '1,00 A'} für {fBF['CT_sek']} A-CT). "
            "**SVS-Taus** (Adr.7004): Zusammensetzung "
            f"t_LS_max (~{KG.BF_t_LS_typ*1000:.0f} ms) + "
            f"t_RF (~{KG.BF_t_RF_typ*1000:.0f} ms) + "
            f"t_Marge (~{KG.BF_t_Marge_typ*1000:.0f} ms) = "
            f"Minimum ~{fBF['Taus_min_emp']*1000:.0f} ms. "
            "**Adr.7002 AUS INTERN** (BA12/CFC/Aus): DIGSI-Konfigurationsoption ohne Zahlenwert — "
            "BA12 empfohlen, wenn der Auslöseausgang auf BA12 rangiert ist (7UM62 Hdb. 2.36)."
        )

    # ══════════════════════ BEMESSUNGS-ENGINEERING ══════════════════════
    b = e["bemessung"]
    with _section("Bemessungs-Engineering — Reserve-Überstromstufe + Empfindlichkeit"):
        st.caption("Kein Ersatz für eine Kurzschlussberechnung — verifiziert die Reservestufe I> gegen "
                   "Maximallast und minimalen Fehlerstrom. Bezug: Generatorklemmen (primär).")
        dfb = pd.DataFrame([
            ("I_max_Last", f"{b['I_max_Last_prim']:.1f} A prim.", "—", "Default 1,0 × IN (Generator-Dauerlast)"),
            ("I_k_min (Schutzgebiet-Ende)", f"{b['I_k_min_prim']:.0f} A prim.", "—", b['I_k_min_quelle']),
            ("I> Empfehlung = k_S · I_max_Last", f"{b['I_emp_prim']:.1f} A prim.",
                f"{_AMPEL_EMOJI[b['I_status']]} {b['I_status']}",
                b['korr_I'] if b['korr_I'] else f"gewählt {b['I_gewaehlt_prim']:.1f} A ≥ Empfehlung ✓"),
            ("Empfindlichkeit I_k_min / I> ≥ γ", f"{b['empfind']:.2f}  (γ = {b['gamma']})",
                f"{_AMPEL_EMOJI[b['empfind_status']]} {b['empfind_status']}",
                b['korr_emp'] if b['korr_emp'] else "I_k_min regt I> sicher an ✓"),
        ], columns=["Größe", "Wert", "Status", "Korrektur / Kommentar"])
        st.dataframe(dfb, width="stretch", hide_index=True)

    # ══════════════════════ PLAUSIBILITÄT ══════════════════════
    with _section("Plausibilitätsprüfung (Ampel)"):
        dfp = pd.DataFrame([{
            "Status": f"{_AMPEL_EMOJI.get(c['status'],'')} {c['status']}",
            "Prüfung": c["pruefung"], "Ergebnis": c["ergebnis"],
            "Konkrete Korrektur": c["korrektur"] if c["korrektur"] else "—",
            "Hinweis / Quelle": c["hinweis"],
        } for c in plaus])
        st.dataframe(dfp, width="stretch", hide_index=True)

    # ══════════════════════ RESERVESCHUTZ-ZUORDNUNG ══════════════════════
    with _section("Reserveschutz-Zuordnung / DIGSI-Adressen"):
        dfr = pd.DataFrame([{
            "Funktion": x["funktion"], "Ziel-Objekt": x["ziel"],
            "I> [A sek.]": x["I_sek"], "t> [s]": x["t"],
            "I>> [A sek.]": x["IHH_sek"], "t>> [s]": x["tHH"],
            "Siemens-Adresse": x["adresse"],
        } for x in e["reserveschutz"]])
        st.dataframe(dfr, width="stretch", hide_index=True)
        st.caption("Hinweis: bei 'Überlast 49' ist t> die Zeitkonstante τ in SEKUNDEN (7UM62 Adr.1603) — "
                   "im Gegensatz zum 7UT613 (Minuten).")

    # ══════════════════════ ARCHITEKTUR-/ERDSCHLUSS-EMPFEHLUNG ══════════════════════
    with _section("Architektur- & Erdschluss-Empfehlung"):
        eg = e["empfehlung"]
        st.markdown(f"**Anschluss-Architektur:** {eg['architektur']}")
        st.markdown(f"**Erdschlusserfassung:** {eg['erdschluss']}")

    # ══════════════════════ HERSTELLERNEUTRALE SOLLWERT-TABELLE ══════════════════════
    with _section("📋  Herstellerneutrale Sollwert-Tabelle (DIGSI-Adressen 7UM62)"):
        rows = []
        for x in r["rows"]:
            sek = f"{x['wert_sek']:.4f}" if x["wert_sek"] is not None else f"{x['faktor']:g}"
            rows.append(("87G", x["name"], sek, x["einheit"], f"7UM62: {x['adresse']}"))
        rows += [
            ("50/51", "I> + U<-Haltung", f"{umz['I_sek']:.4f}", "A sek.", "Adr.1202 / t 1203 / U< 1205"),
            ("50",    "I>>",            f"{umz['IHH_sek']:.4f}", "A sek.", "Adr.1302 / t 1303"),
            ("51V",   "Ip spannungsabh.", f"{v51['Ip_sek']:.4f}", "A sek.", "Adr.1402 / TIp 1403 / U< 1408"),
            ("49",    "k-Faktor",       f"{b49['k_Faktor']:.2f}", "x IN", "Adr.1602"),
            ("49",    "τ thermisch",    f"{b49['tau_s']:.0f}", "s", "Adr.1603  ← SEKUNDEN!"),
            ("49",    "Θ-Warnstufe",    f"{b49['Theta_Warn_pct']:.0f}", "%", "Adr.1604"),
            ("46",    "I2 zulässig",    f"{b46['I2_zul_faktor']*100:.1f}", "%", "Adr.1702 / t 1703"),
            ("46",    "I2>>",           f"{b46['I2_HH_faktor']*100:.0f}", "%", "Adr.1706 / t 1707"),
            ("40",    "1/xd KL.1",      f"{f40['xd_KL1']:.2f}", "-", f"Adr.3002 / α {f40['winkel_1']}° 3003"),
            ("40",    "1/xd KL.3",      f"{f40['xd_KL3']:.2f}", "-", "Adr.3008 / 3009 / 3010"),
            ("32",    "Prück>",         f"{f32['Prueck_pct']:.2f}", "%", "Adr.3102 (negativ)"),
            ("32P",   "P< VORW.",       f"{f32P['P_un_pct']:.1f}", "% SN_sek", "Adr.3202 / t 3203" + ("" if f32P["aktiv"] else " (aus)")),
            ("32P",   "P> VORW.",       f"{f32P['P_ue_pct']:.1f}", "% SN_sek", "Adr.3204 / t 3205" + ("" if f32P["aktiv"] else " (aus)")),
            ("24",    "U/f >>",         f"{f24['Uf_Aus']:.2f}", "-", "Adr.4304 / t 4305"),
            ("27",    "U<",             f"{f2759['U_klein']:.0f}", "V", "Adr.4002 / t 4003"),
            ("59",    "U>",             f"{f2759['U_gross']:.0f}", "V", "Adr.4102 / t 4103"),
            ("81",    "f1",             f"{f81['stufen'][0]['f']:.2f}", "Hz", f81['stufen'][0]['adr']),
            ("81R",   "df1/dt",         f"{f81R['stufen'][0]['stufe']:.1f}", "Hz/s",
             f"Adr.4503 ({f81R['stufen'][0]['richtung']}) / t 4504" + ("" if f81R["aktiv"] else " (aus)")),
            ("81R",   "df3/dt",         f"{f81R['stufen'][2]['stufe']:.1f}", "Hz/s",
             f"Adr.4511 ({f81R['stufen'][2]['richtung']}) / t 4512" + ("" if f81R["aktiv"] else " (aus)")),
            ("VS",    "DELTA PHI",      f"{fVS['dphi']:.0f}", "°",
             "Adr.4602 / t 4603" + ("" if fVS["aktiv"] else " (aus)")),
            ("59N",   "U0>",            f"{f59n['U0']:.1f}", "V", "Adr.5002 / 3I0 5003 / t 5005"),
            ("IEE",   "IEE>  Anregung", f"{fIEE['IEE_an']:.1f}", "mA", "Adr.5102 / t 5103" + ("" if fIEE["aktiv"] else " (aus)")),
            ("IEE",   "IEE>> Auslösung",f"{fIEE['IEE_aus']:.1f}", "mA", "Adr.5104 / t 5105" + ("" if fIEE["aktiv"] else " (aus)")),
            ("64R",   "RE AUS",         f"{f64r['RE_Aus']:.1f}", "kΩ", "Adr.6003 / t 6005"),
            ("21",    "IMP I> Anregung", f"{f21['I_anr_sek']:.4f}", "A sek.", "Adr.3302" + ("" if f21["aktiv"] else " (aus)")),
            ("21",    "Zone Z1",         f"{f21['Z1_sek']:.2f}", "Ω sek.", "Adr.3306 / t 3307"),
            ("21",    "Zone Z2",         f"{f21['Z2_sek']:.2f}", "Ω sek.", "Adr.3310 / t 3311"),
            ("78",    "I1> Freigabe",    f"{f78['I1_frei_pct']:.0f}", "% IN", "Adr.3502" + ("" if f78["aktiv"] else " (aus)")),
            ("78",    "I2< Freigabe",    f"{f78['I2_frei_pct']:.0f}", "% IN", "Adr.3503"),
            ("78",    "Polygon Za",      f"{f78['Za_sek']:.2f}", "Ω sek.", "Adr.3504"),
            ("50BF",  "SVS I>",          f"{fBF['I_sek']:.3f}", "A sek.",
             "Adr.7003" + ("" if fBF["aktiv"] else " (aus)")),
            ("50BF",  "SVS-Taus",        f"{fBF['Taus']:.3f}", "s",
             "Adr.7004" + ("" if fBF["aktiv"] else " (aus)")),
        ]
        dft = pd.DataFrame(rows, columns=["ANSI", "Parameter", "Sollwert", "Einheit", "Hinweis / Adresse"])
        st.dataframe(dft, width="stretch", hide_index=True)
        st.caption("Sekundärwerte gelten für die gewählten Wandler. Alle Werte sind IEC-normierte "
                   "physikalische Größen (A, s, %, V, Hz, kΩ) → auf andere Relaisfamilien (ABB, GE, SEL) "
                   "übertragbar; die 7UM62-Adressen dienen als nachvollziehbare Berechnungsgrundlage.")
