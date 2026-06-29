"""
tab_motor.py — Streamlit-UI fuer Motorschutz (SIPROTEC 7SJ66)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg
"""

import pandas as pd
import streamlit as st

import konstanten_motor as KM
from calc_motor import berechne_alle, grundgroessen


# ── Farbkodierung (identisch zu Trafo-/Generator-Tab fuer einheitliches Look&Feel) ──
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
    h = KM.HERST.get(key)
    if not h:
        return
    adr = h.get("adr")
    adr_html = (f'<br>📍 <b>Eintragen unter:</b> {adr}' if adr
                else '<br>📍 <b>Rechengröße</b> (kein direkter DIGSI-Parameter, fließt in die Sollwerte ein)')
    st.markdown(
        f'<div style="font-size:0.72rem;color:#5d6b82;margin:-6px 0 10px;line-height:1.25;">'
        f'<b>Hersteller:</b> {h["range"]}<br>{h["grund"]}{adr_html}</div>',
        unsafe_allow_html=True)


# ── Hauptfunktion ─────────────────────────────────────────────────────────────

def show():
    st.markdown(_CSS, unsafe_allow_html=True)

    # ══════════════════════ EINGABEN ══════════════════════
    with _section("Eingaben — Motor-Grunddaten, Stromwandler, Anlauf, Antrieb & Netz"):
        ci1, ci2, ci3 = st.columns(3, gap="medium")
        with ci1:
            st.caption("**Motor-Grunddaten (Asynchronmaschine MS)**")
            Pn  = st.number_input("Pn — mechanische Bemessungsleistung [kW]", 1.0, value=1500.0,
                                  step=10.0, format="%.1f", key="mot_50")
            UN  = st.number_input("UN — Bemessungsspannung [kV]", 0.4, value=6.0, step=0.1,
                                  format="%.1f", key="mot_49")
            cosphi = st.number_input("cos φN — Leistungsfaktor [-]", 0.5, 1.0, value=KM.cos_phi_def,
                                     step=0.01, format="%.2f", key="mot_48")
            eta = st.number_input("η — Wirkungsgrad [-]", 0.5, 1.0, value=KM.eta_def,
                                  step=0.01, format="%.2f", key="mot_47")
            IN_direkt = st.number_input("IN direkt [A prim.] (0 = aus Pn berechnen)", 0.0, value=0.0,
                                        step=1.0, format="%.1f", key="mot_46",
                                        help="Direkter Motornennstrom vom Typenschild. > 0 hat Vorrang vor der "
                                             "Berechnung aus Pn / (√3·UN·cosφ·η).")
        with ci2:
            st.caption("**Stromwandler (ein Satz im Motorabgang)**")
            c1, c2 = st.columns(2)
            with c1:
                CT_P = st.number_input("CT prim. [A]", 1, value=300, step=1, key="mot_45")
            with c2:
                CT_S = st.selectbox("CT sek. [A]", [1, 5], index=0, key="mot_44")
            st.caption("**Anlauf-Kenndaten (Datenblatt)**")
            I_Anlauf_Verh = st.number_input("I_A/IN — Anlaufstromverhältnis [-]", 1.0, 12.0,
                                            value=KM.I_Anlauf_Verh_def, step=0.1, format="%.1f", key="mot_43",
                                            help="Verhältnis Anlauf- zu Nennstrom (Anzugstrom). MS-Asynchron typ. 5 … 7.")
            I_max_Verh = st.number_input("I_max/IN — Dauer-Überlastfaktor [-]", 1.0, 1.5,
                                         value=KM.I_max_Verh_def, step=0.01, format="%.2f", key="mot_42",
                                         help="Dauernd zulässiger Strom bezogen auf IN (= k-Faktor 49).")
            t_Anlauf = st.number_input("t_Anlauf — Hochlaufzeit [s]", 0.5, 180.0,
                                       value=KM.t_Anlauf_def, step=0.5, format="%.1f", key="mot_41")
            t_LR_zul = st.number_input("zul. Blockierzeit t_LR (warm) [s]", 0.5, 180.0,
                                       value=KM.t_LR_zul_def, step=0.5, format="%.1f", key="mot_40",
                                       help="Permissible locked-rotor time. Anlauf muss kürzer sein als diese Zeit.")
        with ci3:
            st.caption("**Antrieb & Netz**")
            stp_Netz = st.selectbox("Sternpunktbehandlung Netz", KM.STERNPUNKT_NETZ_OPTIONEN,
                                    index=0, key="mot_39")
            antrieb  = st.selectbox("Antriebsart (Lastmoment)", KM.ANTRIEBSART_OPTIONEN,
                                    index=0, key="mot_38")
            kuehlung = st.selectbox("Kühlung", KM.KUEHLUNG_OPTIONEN, index=0, key="mot_37")
            Ik_2pol  = st.number_input("Ik,2-pol,min am Motor [kA]", 0.0, value=4.0, step=0.1,
                                       format="%.2f", key="mot_36",
                                       help="Kleinster 2-poliger Fehlerstrom (Motorklemmen). Obergrenze des "
                                            "50-2-Hochstromfensters.")
            Ik_min   = st.number_input("Ik,min am Schutzgebiet-Ende [kA]", 0.0, value=0.0, step=0.1,
                                       format="%.2f", key="mot_35",
                                       help="Minimaler Kurzschlussstrom nach DIN EN 60909-0 für die "
                                            "Empfindlichkeitsprüfung der 51-Stufe. 0 = ersatzweise Ik,2-pol,min.")
            # Spannungsmesseingänge (Gerätevariante mit VT) — einheitlich zum Trafo-Tab.
            vt_vorhanden = st.checkbox(
                "Spannungsmesseingänge (VT) vorhanden", value=False, key="mot_34",
                help="7SJ66 nur mit Spannungseingang-Variante. Voraussetzung für Unterspannung 27, "
                     "Überspannung 59 und die Spannungsunsymmetrie 47 (Gegensystem V2). Ohne VT "
                     "bleibt nur die stromseitige Phasenfolgeprüfung wirksam.")
            if vt_vorhanden:
                v1, v2 = st.columns(2)
                with v1:
                    VT_Prim = st.number_input("VT prim. [kV]", 0.0, value=float(UN), step=0.1,
                                              format="%.2f", key="mot_33",
                                              help="Primäre VT-Nennspannung (verkettet), typ. = UN des Netzes.")
                with v2:
                    VT_Sek = st.selectbox("VT sek. [V]", KM.VT_Sek_Optionen, index=0, key="mot_32",
                                          help="Sekundäre VT-Nennspannung (verkettet), Bezugsgröße der "
                                               "Spannungsschutz-Schwellen.")
            else:
                VT_Prim, VT_Sek = 0.0, 100

    # ── Geräte-Einstellbereiche (7SJ66) an Wandler koppeln ───────────────────
    # Alle Stromstufen werden — wie im DIGSI-Feld — sekundär in Ampere eingegeben
    # (z. B. 50-2 PICKUP 0,10 .. 35,00 A bei 1-A-Wandlern, 0,50 .. 175,00 A bei
    # 5-A-Wandlern, Adr.1202). Die Bereichsgrenzen folgen dem realen Einstellbereich,
    # mit dem Wandler-Sekundaernennstrom skaliert. Fuer die Berechnung werden die
    # Phasenstufen intern auf das Vielfache x IN_Motor zurueckgerechnet (IN_sek).
    _g0   = grundgroessen(dict(
        Pn_kW=Pn, UN_kV=UN, cos_phi=cosphi, eta=eta, IN_direkt=IN_direkt,
        CT_Prim=CT_P, CT_Sek=CT_S, I_Anlauf_Verh=I_Anlauf_Verh, I_max_Verh=I_max_Verh,
        VT_vorhanden=vt_vorhanden, VT_Prim_kV=VT_Prim, VT_Sek_V=VT_Sek))
    _INs  = _g0["IN_sek"] or 0.0

    def _A_range(dev_min_1A, dev_max_1A, default_val):
        """Absoluter A-sek.-Bereich, mit Wandler skaliert (5A = 1A-Bereich x5)."""
        lo = round(dev_min_1A * CT_S, 4)
        hi = round(dev_max_1A * CT_S, 2)
        val = float(min(max(default_val, lo), hi))
        return float(lo), float(hi), val

    def _A_def(faktor):
        """Motortechnisch sinnvoller A-sek.-Default aus einem x-IN-Faktor (= faktor * IN_sek)."""
        return round(faktor * _INs, 3) if _INs > 0 else round(faktor, 3)

    def _faktor(a_sek, faktor_default):
        """A-sek.-Slidereingabe zuruck auf x IN (fuer die Berechnung): a_sek / IN_sek.
        6 Nachkommastellen, damit f * IN_sek den eingestellten A-Wert exakt reproduziert
        (keine Rundungsdrift an den Bereichsgrenzen)."""
        return round(a_sek / _INs, 6) if _INs > 0 else faktor_default

    # ── Erweiterte Parameter ──────────────────────────────────────────────────
    with _section("Erweiterte Parameter (Voreinstellungen nach SIPROTEC 7SJ66 — frei änderbar)",
                  expanded=False):
        st.caption("ℹ️ Unter jedem Regler stehen der Hersteller-Range und die Begründung. "
                   "Adressen beziehen sich auf das 7SJ66-Handbuch (C53000-B1140-C383-D). "
                   "Achtung: τ (Adr.4203) in **Minuten** — wie 7UT613, nicht wie 7UM62 (Sekunden).")
        e1, e2, e3 = st.columns(3)
        with e1:
            st.markdown("**49 Thermischer Überlastschutz**")
            kfak  = st.slider("49  k-Faktor [x IN]", 0.10, 4.00, KM.k_Faktor_def, 0.01, key="mot_29")
            _hreg("k_Faktor")
            tau   = st.slider("49  τ thermisch [min] (Minuten!)", 1, 999, int(KM.tau_Mot_def), 1, key="mot_28")
            _hreg("tau_min")
            thetaW = st.slider("49  Θ-Warnstufe [-]", 0.50, 1.00, KM.Theta_Warn_def, 0.01, key="mot_27")
            _iw_lo, _iw_hi, _iw_val = _A_range(0.10, 4.00, KM.I_Warn_def)
            i_warn = st.number_input("49  I ALARM (Stromwarnstufe) [A sek.]", _iw_lo, _iw_hi,
                                     _iw_val, step=0.05, format="%.2f", key="mot_26")
            _hreg("I_Warn")
            ktau   = st.slider("49  Kτ bei Stillstand [-]", 1.0, 10.0, KM.Ktau_Stop_def, 0.5, key="mot_25")
            _hreg("Ktau_Stop")

            st.markdown("**46 Schieflast (Gegensystem)**")
            i2d = st.slider("46-1  I2 dauernd zul. [-]", 0.05, 0.30, KM.I2_dauer_def, 0.005,
                            format="%.3f", key="mot_24")
            _hreg("I2_dauer")
            i2k = st.slider("46-2  I2 kurzzeitig zul. [-]", 0.10, 1.00, KM.I2_kurz_def, 0.05, key="mot_23")
            _hreg("I2_kurz")
            st.caption("46 wird als Gegensystemanteil I2/IN parametriert (IEC 60034-1, herstellerneutral). "
                       "Im Gerät entspricht das dem Sekundärstrom 46-1/46-2 PICKUP (0,05 .. 3,00 A bei 1A, "
                       "Adr.4002/4004), den das Tool über IN_sek aus dem Anteil errechnet.")
        with e2:
            st.markdown("**48 Anlaufüberwachung**")
            _sc_lo, _sc_hi, _sc_val = _A_range(0.50, 16.00, KM.Startup_Current_def)
            su_curr = st.number_input("48  STARTUP CURRENT [A sek.]", _sc_lo, _sc_hi,
                                      _sc_val, step=0.10, format="%.2f", key="mot_22")
            su_time = st.slider("48  STARTUP TIME [s]", 1.0, 180.0, KM.Startup_Time_def, 0.5, key="mot_21")
            _hreg("Startup_Time")
            lr_time = st.number_input("48  LOCK ROTOR TIME [s]", 0.5, 180.0,
                                      KM.Lock_Rotor_Time_def, step=0.5, format="%.1f", key="mot_20")
            _hreg("Lock_Rotor_Time")
            _ms_lo, _ms_hi, _ms_val = _A_range(0.40, 10.00, KM.I_Motor_Start_def)
            i_mstart = st.number_input("48  I MOTOR START [A sek.] (Adr.1107)", _ms_lo, _ms_hi,
                                       _ms_val, step=0.10, format="%.2f", key="mot_19")
            st.caption("48 STARTUP CURRENT 0,50 .. 16,00 A (1A) bzw. 2,50 .. 80,00 A (5A), Adr.4102; "
                       "STARTUP TIME 1,0 .. 180,0 s, Adr.4103; LOCK ROTOR TIME 0,5 .. 180,0 s, Adr.4104; "
                       "I MOTOR START 0,40 .. 10,00 A (1A), Adr.1107 (wandlerskaliert).")

            st.markdown("**66 Wiedereinschaltsperre / Anlaufzähler**")
            istart_nom = st.slider("66  IStart/IMOTnom [-]", 1.10, 10.00, KM.IStart_IMOTnom_def, 0.10, key="mot_18")
            _hreg("IStart_IMOTnom")
            tstart_max = st.slider("66  T START MAX [s]", 1, 320, int(KM.T_Start_Max_def), 1, key="mot_17")
            _hreg("T_Start_Max")
            warm_starts = st.slider("66  MAX. WARM STARTS [-]", 1, 4, int(KM.Max_Warm_Starts_def), 1, key="mot_16")
            _hreg("Max_Warm_Starts")

            st.markdown("**51M Lastsprung / Load-Jam**")
            _lj_lo, _lj_hi, _lj_val = _A_range(0.50, 12.00, _A_def(KM.LoadJam_Faktor))
            lj_A = st.number_input("51M  Load Jam I> [A sek.]", _lj_lo, _lj_hi, _lj_val,
                                   step=0.05, format="%.3f", key="mot_15")
            _hreg("LoadJam_I")
            lj_fak = _faktor(lj_A, KM.LoadJam_Faktor)
            st.caption("Eingabe in Sekundärampere (Load Jam I> 0,50 .. 12,00 A bei 1A, Adr.4402); "
                       "das Vielfache x IN steht in der Ergebnisanzeige.")
        with e3:
            st.markdown("**50/51 Phasen-Überstromzeitschutz**")
            _f2_lo, _f2_hi, _f2_val = _A_range(0.10, 35.00, _A_def(KM.f_50_2_def))
            f502_A = st.number_input("50-2  I>> [A sek.]", _f2_lo, _f2_hi, _f2_val,
                                     step=0.05, format="%.3f", key="mot_14")
            _hreg("f_50_2")
            t502 = st.number_input("50-2  t [s]", 0.00, 60.00, KM.t_50_2_def, step=0.05,
                                   format="%.2f", key="mot_13")
            _hreg("t_50_2")
            _f1_lo, _f1_hi, _f1_val = _A_range(0.10, 35.00, _A_def(KM.f_50_1_def))
            f501_A = st.number_input("50-1  I> [A sek.]", _f1_lo, _f1_hi, _f1_val,
                                     step=0.05, format="%.3f", key="mot_12")
            _hreg("f_50_1")
            t501 = st.number_input("50-1  t [s]", 0.00, 60.00, KM.t_50_1_def, step=0.05,
                                   format="%.2f", key="mot_11")
            _hreg("t_50_1")
            _f51_lo, _f51_hi, _f51_val = _A_range(0.10, 4.00, _A_def(KM.f_51_def))
            f51_A = st.number_input("51  Ip (AMZ) [A sek.]", _f51_lo, _f51_hi, _f51_val,
                                    step=0.01, format="%.3f", key="mot_10")
            _hreg("f_51")
            t51  = st.number_input("51  TIME DIAL [s]", 0.05, 3.20, KM.T_51_def, step=0.05,
                                   format="%.2f", key="mot_09")
            # A-sek.-Eingaben zurueck auf x IN fuer die Berechnung
            f502 = _faktor(f502_A, KM.f_50_2_def)
            f501 = _faktor(f501_A, KM.f_50_1_def)
            f51  = _faktor(f51_A,  KM.f_51_def)
            st.caption("Eingabe in Sekundärampere wie im DIGSI-Feld (50-2/50-1 0,10 .. 35,00 A bei 1A "
                       "bzw. 0,50 .. 175,00 A bei 5A, Adr.1202/1204; 51 0,10 .. 4,00 A bei 1A, Adr.1207). "
                       "Das zugehörige Vielfache x IN steht in der Ergebnisanzeige. "
                       "51 TIME DIAL 0,05 .. 3,20 s (IEC, Adr.1208).")

            st.markdown("**37 Unterstrom / Lastverlust**")
            i_unter = st.slider("37-1<  Ansprechwert [% von IN]", 10, 80, int(KM.I_unter_pct_def), 1, key="mot_08")
            _hreg("I_unter")

    # ── Erweiterte Parameter — Erdfehler- & Spannungsschutz ───────────────────
    with _section("Erweiterte Parameter — Erdfehler- & Spannungsschutz (50N/51N · 27/59 · 47)",
                  expanded=False):
        st.caption("ℹ️ Die Erdfehlerstufen folgen der Sternpunktbehandlung des Netzes: niederohmig "
                   "geerdet → Stromkriterium 50N/51N (Adr.13xx); isoliert/kompensiert → empfindliche "
                   "Stufe 50Ns/51Ns/67Ns über den INs-Eingang (Adr.31xx). Spannungsschutz 27/59 und "
                   "Spannungsunsymmetrie 47 (Gegensystem V2) benötigen einen Spannungswandler.")
        ee1, ee2, ee3 = st.columns(3)
        with ee1:
            st.markdown("**50N/51N Erdüberstrom (niederohmig)**")
            _n2_lo, _n2_hi, _n2_val = _A_range(0.05, 35.00, KM.f_50N2_def)
            f50N2 = st.number_input("50N-2  I_E>> [A sek.]", _n2_lo, _n2_hi, _n2_val,
                                    step=0.05, format="%.3f", key="mot_07")
            _hreg("f_50N2")
            _n1_lo, _n1_hi, _n1_val = _A_range(0.05, 35.00, KM.f_50N1_def)
            f50N1 = st.number_input("50N-1  I_E> [A sek.]", _n1_lo, _n1_hi, _n1_val,
                                    step=0.05, format="%.3f", key="mot_06")
            _hreg("f_50N1")
            _51n_lo, _51n_hi, _51n_val = _A_range(0.05, 4.00, KM.f_51N_def)
            f51N = st.number_input("51N  I_Ep (AMZ) [A sek.]", _51n_lo, _51n_hi, _51n_val,
                                   step=0.05, format="%.3f", key="mot_05")
            _hreg("f_51N")
            st.caption("Erdstrom-Bereich 50N-2/50N-1 0,05 .. 35,00 A (1A) bzw. 0,25 .. 175,00 A (5A), "
                       "51N 0,05 .. 4,00 A (1A), wandlerskaliert (Adr.1302/1304/1307).")
            st.markdown("**50Ns/51Ns empfindlich (isoliert/komp.)**")
            vn50ns = st.slider("64-1  U0-Schwelle VN [V sek.]", 1.8, 170.0, KM.VN_50Ns_def, 0.1,
                               format="%.1f", key="mot_04")
            _hreg("VN_50Ns")
            f50ns2 = st.number_input("50Ns-2  I_EE>> [A sek.]", 0.001, 1.500, KM.f_50Ns2_def,
                                     step=0.001, format="%.3f", key="mot_03")
            _hreg("f_50Ns2")
            f50ns1 = st.number_input("50Ns-1  I_EE> [A sek.]", 0.001, 1.500, KM.f_50Ns1_def,
                                     step=0.001, format="%.3f", key="mot_02")
            _hreg("f_50Ns1")
        with ee2:
            st.markdown("**59 Überspannung (nur VT)**")
            u59_1 = st.slider("59-1  U> [V sek.]", 40.0, 260.0, KM.U59_1_def, 1.0,
                              format="%.1f", key="mot_01")
            _hreg("U59_1")
            u59_2 = st.slider("59-2  U>> [V sek.]", 40.0, 260.0, KM.U59_2_def, 1.0,
                              format="%.1f", key="mot_59b")
            _hreg("U59_2")
            st.markdown("**27 Unterspannung (nur VT)**")
            u27_1 = st.slider("27-1  U< (Warnstufe) [V sek.]", 10.0, 210.0, KM.U27_1_def, 1.0,
                              format="%.1f", key="mot_27a")
            _hreg("U27_1")
            u27_2 = st.slider("27-2  U<< (Auslösung) [V sek.]", 10.0, 210.0, KM.U27_2_def, 1.0,
                              format="%.1f", key="mot_27b")
            _hreg("U27_2")
            st.caption("Spannungsbereich verkettet: 59 40 .. 260 V (Adr.5002/5005), 27 10 .. 210 V "
                       "(Adr.5102/5110). Bei Stern-/Phasenspannungs-Messung gelten die ph-n-Bereiche "
                       "(59 40 .. 150 V, 27 10 .. 120 V).")
        with ee3:
            st.markdown("**47 Phasenfolge / Spannungsunsymmetrie**")
            phase_seq = st.selectbox("Erwartete Phasenfolge (Drehfeld)", KM.PHASE_SEQ_OPTIONEN,
                                     index=0, key="mot_47ps")
            _hreg("phase_seq")
            u59v2_1 = st.slider("59-1-V2  U2> (Gegensystem) [V sek.]", 2.0, 150.0, KM.U59_V2_1_def, 1.0,
                                format="%.1f", key="mot_47a")
            _hreg("U59_V2_1")
            u59v2_2 = st.slider("59-2-V2  U2>> (Gegensystem) [V sek.]", 2.0, 150.0, KM.U59_V2_2_def, 1.0,
                                format="%.1f", key="mot_47b")
            _hreg("U59_V2_2")
            st.caption("Die stromseitige Phasenfolgeprüfung (|I| > 0,5·IN, Adr.209) ist auch ohne "
                       "Spannungswandler wirksam. Die Gegensystem-Überspannung V2 erfasst verdrehte oder "
                       "fehlende Phasenspannungen und benötigt einen VT.")

    # ══════════════════════ BERECHNUNG ══════════════════════
    p = dict(
        Pn_kW=Pn, UN_kV=UN, cos_phi=cosphi, eta=eta, IN_direkt=IN_direkt,
        CT_Prim=CT_P, CT_Sek=CT_S,
        I_Anlauf_Verh=I_Anlauf_Verh, I_max_Verh=I_max_Verh,
        t_Anlauf=t_Anlauf, t_LR_zul=t_LR_zul,
        stp_Netz=stp_Netz, antrieb=antrieb, kuehlung=kuehlung,
        Ik_2pol_min_kA=Ik_2pol, Ik_min_kA=Ik_min,
        k_Faktor=kfak, tau_min=tau, Theta_Warn=thetaW, I_Warn=i_warn, Ktau_Stop=ktau,
        I2_dauer=i2d, I2_kurz=i2k,
        Startup_Current=su_curr, Startup_Time=su_time, Lock_Rotor_Time=lr_time,
        I_Motor_Start=i_mstart,
        IStart_IMOTnom=istart_nom, T_Start_Max=tstart_max, Max_Warm_Starts=warm_starts,
        LoadJam_Faktor=lj_fak,
        f_50_2=f502, t_50_2=t502, f_50_1=f501, t_50_1=t501, f_51=f51, T_51=t51,
        I_unter_pct=i_unter,
        VT_vorhanden=vt_vorhanden, VT_Prim_kV=VT_Prim, VT_Sek_V=VT_Sek,
        f_50N2=f50N2, f_50N1=f50N1, f_51N=f51N,
        VN_50Ns=vn50ns, f_50Ns2=f50ns2, f_50Ns1=f50ns1,
        U59_1=u59_1, U59_2=u59_2, U27_1=u27_1, U27_2=u27_2,
        phase_seq=phase_seq, U59_V2_1=u59v2_1, U59_V2_2=u59v2_2,
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
                    'Die berechneten Sollwerte sind in sich konsistent. '
                    'Bewusste Abweichungen bleiben dir überlassen.</div>', unsafe_allow_html=True)

    # ══════════════════════ BERECHNETE GRUNDGRÖSSEN ══════════════════════
    with _section("Berechnete Grundgrößen"):
        gg1, gg2, gg3 = st.columns(3)
        with gg1:
            _metric("IN Motor primär", f"{g['IN_prim']:.2f} A", f"= Pn / (√3·UN·cosφ·η) · {g['in_quelle']}")
            _metric("IN sekundär", f"{g['IN_sek']:.4f} A", f"÷ kCT = {g['kCT']:.0f}")
            _metric("STW-Anpassung", f"{g['I_an']:.3f}", "I_an = CT_sek / IN_sek (Soll 0,5–2,0)")
        with gg2:
            _metric("Anlaufstrom I_A primär", f"{g['I_Anlauf_prim']:.1f} A", f"= {g['I_Anlauf_Verh']:.1f} × IN")
            _metric("Anlaufstrom I_A sekundär", f"{g['I_Anlauf_sek']:.4f} A")
            _metric("max. Betriebsstrom prim.", f"{g['I_max_prim']:.2f} A", f"= {g['I_max_Verh']:.2f} × IN")
        with gg3:
            _metric("max. Betriebsstrom sek.", f"{g['I_max_sek']:.4f} A")
            _metric("Scheinleistung Sn (informativ)", f"{g['Sn_MVA']:.3f} MVA", "= √3·UN·IN")
            _metric("Wandlerverhältnis kCT", f"{g['kCT']:.0f}", "= CT_prim / CT_sek")

    # ══════════════════════ 49 + 46 ══════════════════════
    b49, b46 = e["49"], e["46"]
    with _section("ANSI 49 (Thermischer Überlastschutz) + ANSI 46 (Schieflast)"):
        t1, t2, t3 = st.columns(3)
        with t1:
            _metric("49  I_max_zul sek.", f"{b49['I_max_zul_sek']:.4f} A", f"= {b49['k_Faktor']:.2f} × IN_sek")
            _metric("49  Θ-Warnstufe", f"{b49['Theta_Warn_pct']:.0f} %", f"I ALARM = {b49['I_Warn_sek']:.4f} A sek.")
        with t2:
            _metric("49  τ thermisch", f"{b49['tau_min']:.0f} min", f"= {b49['tau_s']:.0f} s · Adr.4203 (MINUTEN!)")
            _metric("49  Kτ bei Stillstand", f"{b49['Ktau_Stop']:.1f}", "Adr.4207A · Abkühlung im Stillstand")
        with t3:
            _metric("46  I2 dauernd zul. sek.", f"{b46['I2_dauer_sek']:.4f} A",
                    f"= {b46['I2_dauer_faktor']*100:.0f}% × IN_sek · t = {b46['t_46_1']:.1f} s")
            _metric("46  I2 kurzzeitig zul. sek.", f"{b46['I2_kurz_sek']:.4f} A",
                    f"= {b46['I2_kurz_faktor']*100:.0f}% × IN_sek · t = {b46['t_46_2']:.1f} s")
        st.caption("τ wird im 7SJ66 in **Minuten** eingegeben (Adr.4203) — wie beim 7UT613, im Gegensatz zum "
                   "7UM62 (Sekunden). Gegensystem-Grenzwerte für Asynchronmaschinen nach IEC 60034-1 "
                   f"(dauernd ~{b46['I2_dauer_faktor']*100:.0f} %). Kennlinie 46: {b46['kennlinie']}.")

    # ══════════════════════ 48 + 66 ══════════════════════
    b48, b66 = e["48"], e["66"]
    with _section("ANSI 48 (Anlaufüberwachung / Läuferblockierung) + ANSI 66 (Wiedereinschaltsperre)"):
        df48 = pd.DataFrame([
            ("STARTUP CURRENT", f"{b48['Startup_Current_sek']:.4f} A sek.",
             "Stromschwelle, ab der ein Anlauf erkannt wird", "Adr.4102"),
            ("STARTUP TIME", f"{b48['Startup_Time']:.1f} s",
             "Zul. Anlaufzeit-Schwelle (> reale Anlaufzeit, < Blockierzeit)", "Adr.4103"),
            ("LOCK ROTOR TIME", f"{b48['Lock_Rotor_Time']:.1f} s",
             "Zul. Blockierzeit (Drehzahlwächter über Binäreingang)", "Adr.4104"),
            ("I MOTOR START", f"{b48['I_Motor_Start_sek']:.4f} A sek.",
             "Anlauferkennung — friert thermisches Abbild während des Anlaufs ein", "Adr.1107"),
        ], columns=["Parameter (48)", "Wert", "Bedeutung", "Adresse"])
        st.dataframe(df48, width="stretch", hide_index=True)

        df66 = pd.DataFrame([
            ("IStart/IMOTnom", f"{b66['IStart_IMOTnom']:.2f}", "Anlaufstromverhältnis (Läuferabbild)", "Adr.4302"),
            ("T START MAX", f"{b66['T_Start_Max']:.0f} s", "Max. zul. Anlaufzeit (thermisches Läuferabbild)", "Adr.4303"),
            ("MAX. WARM STARTS", f"{b66['Max_Warm_Starts']:.0f}", "Zul. Warmstarts vor Sperre", "Adr.4306"),
            ("#COLD − #WARM", f"{b66['Cold_minus_Warm']:.0f}", "Zusätzlich zul. Kaltstarts", "Adr.4307"),
            ("Kτ Stillstand / Betrieb", f"{b66['Ktau_Stop']:.1f} / {b66['Ktau_Run']:.1f}",
             "Zeitkonstanten-Faktoren Läuferabbild", "Adr.4308 / 4309"),
            ("T MIN. INHIBIT", f"{b66['T_Min_Inhibit']:.1f} min", "Mindestsperrzeit nach Sperre", "Adr.4310"),
        ], columns=["Parameter (66)", "Wert", "Bedeutung", "Adresse"])
        st.dataframe(df66, width="stretch", hide_index=True)
        st.caption("48 schützt vor zu langem Hochlauf und blockiertem Läufer, 66 begrenzt die Häufigkeit der "
                   "Anläufe über ein thermisches Läuferabbild (7SJ66 Hdb. 2.8). Beide nutzen die Anlauf-"
                   "erkennung über I MOTOR START (Adr.1107).")
        st.markdown('<div class="info-box"><b>Läuferblockierschutz:</b> Eine Blockade <i>beim Anlauf</i> '
                    'erfasst die LOCK ROTOR TIME (Adr.4104) — bleibt der Anlaufstrom über diese Zeit stehen, '
                    'löst 48 aus (sicherer, wenn ein Drehzahlwächter über Binäreingang zugeschaltet ist). '
                    'Eine Blockade <i>im laufenden Betrieb</i> deckt der Lastsprung-/Load-Jam-Schutz 51M '
                    '(Abschnitt 50/51 + 51M) ab. Ein eigener ANSI-Funktionsblock ist dafür nicht nötig.</div>',
                    unsafe_allow_html=True)

    # ══════════════════════ 50/51 + 51M ══════════════════════
    umz, b51M = e["5051"], e["51M"]
    with _section("ANSI 50/51 (Phasen-Überstromzeitschutz) + ANSI 51M (Lastsprung / Load-Jam)"):
        dfu = pd.DataFrame([
            ("I>> (50-2 Hochstromstufe)", f"{umz['f_50_2']:.2f}", "x IN",
             f"{umz['I_50_2_sek']:.4f}", f"{umz['I_50_2_prim']:.1f}", f"{umz['t_50_2']:.2f}"),
            ("I> (50-1 Reserve UMZ)", f"{umz['f_50_1']:.2f}", "x IN",
             f"{umz['I_50_1_sek']:.4f}", f"{umz['I_50_1_prim']:.1f}", f"{umz['t_50_1']:.2f}"),
            ("Ip (51 AMZ)", f"{umz['f_51']:.2f}", "x IN",
             f"{umz['I_51_sek']:.4f}", f"{umz['I_51_prim']:.1f}", f"{umz['T_51']:.2f}"),
        ], columns=["Funktion", "Faktor", "Einheit", "I [A sek.]", "I [A prim.]", "t / TD [s]"])
        st.dataframe(dfu, width="stretch", hide_index=True)
        st.caption(f"Motorseitig löst die Hochstromstufe 50-2 unverzögert aus (t = {umz['t_50_2']:.2f} s) — anders als "
                   f"beim Transformator ist keine Inrush-Stabilisierung nötig. AMZ-Kennlinie 51: {umz['kennlinie']}.")

        dfj = pd.DataFrame([
            ("Load Jam I> (Auslösung)", f"{b51M['LoadJam_I_sek']:.4f} A sek.",
             f"{b51M['LoadJam_I_prim']:.1f} A prim. = {b51M['LoadJam_Faktor']:.2f} × IN", f"{b51M['t_TRIP']:.2f} s", "Adr.4402 / 4403"),
            ("I Alarm (Warnung)", f"{b51M['I_Alarm_sek']:.4f} A sek.",
             "≈ 75 % der Auslösestufe", f"{b51M['t_ALARM']:.2f} s", "Adr.4404 / 4405"),
            ("T Start Blk. (Anlaufblockierung)", f"{b51M['T_Start_Blk']:.2f} s",
             "= 2 × Anlaufzeit — sperrt 51M während des Hochlaufs", "—", "Adr.4406"),
        ], columns=["Parameter (51M)", "Wert", "Bezug", "t [s]", "Adresse"])
        st.dataframe(dfj, width="stretch", hide_index=True)
        st.caption("Der Lastsprung-/Load-Jam-Schutz erkennt eine plötzliche Läuferblockierung im laufenden "
                   "Betrieb (Ansprechwert unterhalb des Anlaufstroms, während des Anlaufs blockiert; 7SJ66 Hdb. 2.8).")

    # ══════════════════════ 37 UNTERSTROM ══════════════════════
    b37 = e["37"]
    with _section("ANSI 37 — Unterstrom / Lastverlust"):
        c1, c2, c3 = st.columns(3)
        with c1: _metric("37-1<  Ansprechwert", f"{b37['I_unter_pct']:.0f} % IN", "Setpoint in % von IN_Motor")
        with c2: _metric("37-1<  sekundär", f"{b37['I_unter_sek']:.4f} A", f"= {b37['I_unter_pct']:.0f}% × IN_sek")
        with c3: _metric("37-1<  Verzögerung", f"{b37['t_unter']:.2f} s", "Lastverlust-Erkennung")
        st.caption("Unterstrom-/Lastverlust-Erkennung (z. B. Trockenlauf einer Pumpe, Kupplungsbruch). "
                   "Kein 4xxx-Parameter, sondern ein Messwert-Setpoint in der DIGSI-Matrix (7SJ66 Hdb. 2.27).")

    # ══════════════════════ 50N/51N ERDFEHLER- / ERDÜBERSTROMSCHUTZ ══════════════════════
    b50N = e["50N51N"]
    with _section("ANSI 50N/51N — Erdfehler-/Erdüberstromschutz (sternpunktabhängig)"):
        st.markdown(f"**Betriebsmodus:** {b50N['modus']} &nbsp;·&nbsp; Sternpunktbehandlung Netz: "
                    f"*{b50N['stp']}*")
        if b50N["niederohmig"]:
            dfe = pd.DataFrame([
                ("I_E>> (50N-2 Hochstromstufe)", f"{b50N['f_50N2_sek']:.4f}", f"{b50N['f_50N2_prim']:.1f}",
                 f"{b50N['t_50N2']:.2f}", "Adr.1302 / 1303"),
                ("I_E> (50N-1 Reserve)", f"{b50N['f_50N1_sek']:.4f}", f"{b50N['f_50N1_prim']:.1f}",
                 f"{b50N['t_50N1']:.2f}", "Adr.1304 / 1305"),
                ("I_Ep (51N AMZ)", f"{b50N['f_51N_sek']:.4f}", f"{b50N['f_51N_prim']:.1f}",
                 f"{b50N['T_51N']:.2f}", "Adr.1307 / 1308"),
            ], columns=["Stufe (50N/51N)", "I [A sek.]", "I [A prim.]", "t / TD [s]", "Adresse"])
            st.dataframe(dfe, width="stretch", hide_index=True)
            st.caption(f"Niederohmig geerdetes Netz: definierter Erdfehlerstrom — Erfassung über das "
                       f"Stromkriterium 50N/51N am Phasenwandlersatz (Holmgreen-Schaltung). "
                       f"Kennlinie 51N: {b50N['kennlinie_51N']}. Primärwerte über kCT = {g['kCT']:.0f}. "
                       f"Ein separater Kabelumbauwandler kann ein eigenes Übersetzungsverhältnis haben.")
        else:
            st.markdown('<div class="info-box">🟢 <b>Empfindliche Erdschlusserfassung aktiv:</b> '
                        'Im isolierten bzw. kompensierten Netz fließt kein nennenswerter Erdfehlerstrom. '
                        'Erfassung über den empfindlichen INs-Eingang (50Ns/51Ns) und die '
                        'Verlagerungsspannung U0; die Richtungsbestimmung 67Ns trennt Vorwärts- und '
                        'Rückwärtsfehler. Das reine Stromkriterium 50N/51N hätte hier zu geringe '
                        'Empfindlichkeit.</div>', unsafe_allow_html=True)
            dfe = pd.DataFrame([
                ("U0-Schwelle VN (64-1)", f"{b50N['VN_sek']:.1f} V",
                 f"≈ {b50N['VN_pct']:.0f} % von {KM.VN_voll_V:.0f} V", f"{b50N['t_64_1']:.2f}", "Adr.3109 / 3112"),
                ("I_EE>> (50Ns-2)", f"{b50N['f_50Ns2_sek']:.4f} A", "empfindlicher INs-Eingang",
                 f"{b50N['t_50Ns2']:.2f}", "Adr.3113 / 3114"),
                ("I_EE> (50Ns-1)", f"{b50N['f_50Ns1_sek']:.4f} A", "empfindlicher INs-Eingang",
                 "—", "Adr.3117"),
                ("Richtung 67Ns-2", b50N['richtung'], "Forward (zum Schutzobjekt)", "—", "Adr.3115"),
            ], columns=["Größe (50Ns/67Ns)", "Wert", "Bezug", "t [s]", "Adresse"])
            st.dataframe(dfe, width="stretch", hide_index=True)
            st.caption("Empfindliche, gerichtete Erdschlusserfassung über U0 (Verlagerungsspannung) und "
                       "den kapazitiven bzw. wattmetrischen Erdreststrom (7SJ66 Hdb. 2.6). "
                       "Isoliert: sin-φ-Auswertung; kompensiert: cos-φ-Auswertung (Wirkreststrom).")

    # ══════════════════════ 27/59 + 47 SPANNUNGS- & PHASENFOLGESCHUTZ ══════════════════════
    f2759, f47 = e["2759"], e["47"]
    with _section("ANSI 27/59 (Unter-/Überspannung) + ANSI 47 (Phasenfolge / Spannungsunsymmetrie)"):
        if not f2759["aktiv"]:
            st.markdown(
                '<div style="font-size:0.84rem;color:#5d6b82;background:#f3f5f8;'
                'border-radius:6px;padding:8px 12px;margin-bottom:8px;">'
                'ANSI 27/59 ist nicht projektiert, da kein Spannungswandler eingetragen ist. '
                'Bei Bedarf im Eingabebereich „Spannungswandler vorhanden" aktivieren.</div>',
                unsafe_allow_html=True)
        else:
            dfv = pd.DataFrame([
                ("59-2  U>> (Schnellstufe)", f"{f2759['U59_2']:.1f}", f"{f2759['U59_2_pct']:.0f}",
                 f"{f2759['t_59_2']:.2f}", "Adr.5005 / 5007"),
                ("59-1  U> (Meldestufe)", f"{f2759['U59_1']:.1f}", f"{f2759['U59_1_pct']:.0f}",
                 f"{f2759['t_59_1']:.2f}", "Adr.5002 / 5004"),
                ("27-1  U< (Meldestufe)", f"{f2759['U27_1']:.1f}", f"{f2759['U27_1_pct']:.0f}",
                 f"{f2759['t_27_1']:.2f}", "Adr.5102 / 5106"),
                ("27-2  U<< (Auslösung)", f"{f2759['U27_2']:.1f}", f"{f2759['U27_2_pct']:.0f}",
                 f"{f2759['t_27_2']:.2f}", "Adr.5110 / 5112"),
            ], columns=["Stufe (27/59)", "U [V sek.]", "% UnS", "t [s]", "Adresse"])
            st.dataframe(dfv, width="stretch", hide_index=True)
            st.caption(f"Bezug: VT-Sekundärnennspannung UnS = {f2759['UnS']:.0f} V (verkettet), "
                       f"VT-Übersetzung nVT = {g['nVT']:.1f}. Zweistufig je Funktion; die untere "
                       f"27-2-Stufe löst aus, die obere 27-1 meldet. Rücksetzverhältnis 27 = "
                       f"{f2759['DOUT_27']:.2f} (Adr.5113A). Spannungsschutz nach 7SJ66 Hdb. 2.6.")

        st.markdown("**ANSI 47 — Phasenfolge / Spannungsunsymmetrie**")
        rows47 = [
            ("Erwartete Phasenfolge (Drehfeld)", f47['phase_seq'], "Meldung 'Fail Ph. Seq.' bei Abweichung",
             "Adr.209"),
            ("Phasenfolge-Prüfschwelle (Strom)", f"|I| > {f47['I_phseq_min_sek']:.4f} A sek.",
             f"= {f47['I_phseq_min_faktor']:.1f} × IN_sek — wirksam auch ohne VT", "Adr.209"),
        ]
        if f47["aktiv_unsym"]:
            rows47 += [
                ("59-1-V2  U2> (Gegensystem)", f"{f47['U59_V2_1']:.1f} V ({f47['U59_V2_1_pct']:.0f} % UnS)",
                 f"t = {f47['t_59_V2_1']:.2f} s — OP.QUANTITY 59 = V2", "Adr.5015"),
                ("59-2-V2  U2>> (Gegensystem)", f"{f47['U59_V2_2']:.1f} V ({f47['U59_V2_2_pct']:.0f} % UnS)",
                 f"t = {f47['t_59_V2_2']:.2f} s — OP.QUANTITY 59 = V2", "Adr.5016"),
            ]
        df47 = pd.DataFrame(rows47, columns=["Größe (47)", "Wert", "Bezug", "Adresse"])
        st.dataframe(df47, width="stretch", hide_index=True)
        if not f47["aktiv_unsym"]:
            st.markdown(
                '<div style="font-size:0.84rem;color:#5d6b82;background:#f3f5f8;'
                'border-radius:6px;padding:8px 12px;margin-top:4px;">'
                'Die stromseitige Phasenfolgeprüfung ist aktiv. Die Spannungsunsymmetrie '
                '(Gegensystem-Überspannung V2) ist nicht projektiert, da kein Spannungswandler '
                'eingetragen ist.</div>',
                unsafe_allow_html=True)

    # ══════════════════════ BEMESSUNGS-ENGINEERING ══════════════════════
    b = e["bemessung"]
    with _section("Bemessungs-Engineering — Stufenwahl gegen Anlauf, Maximallast und Fehlerstrom"):
        st.caption("Kein Ersatz für eine Kurzschlussberechnung nach DIN EN 60909-0 — verifiziert die "
                   "motorseitige Stufenauslegung gegen Anlaufstrom, Maximallast und minimalen Fehlerstrom. "
                   "Bezug: Motorklemmen (primär).")
        dfb = pd.DataFrame([
            ("I_max_Last", f"{b['I_max_Last_prim']:.1f} A prim.", "—",
             f"= {p['I_max_Verh']:.2f} × IN (Motor-Dauerlast)"),
            ("Anlaufstrom I_A", f"{b['I_Anlauf_prim']:.1f} A prim.", "—",
             f"= {p['I_Anlauf_Verh']:.1f} × IN"),
            ("Ik,min (Schutzgebiet-Ende)", f"{b['I_k_min_prim']:.0f} A prim.", "—", b['I_k_min_quelle']),
            ("50-2 im Fenster 1,6·I_A < 50-2 < Ik,2pol,min",
             f"{b['f502_gewaehlt_prim']:.0f} A in [{b['f502_untere_prim']:.0f} … {b['f502_obere_prim']:.0f}] A"
             if b['f502_obere_prim'] else "Ik,2pol,min fehlt",
             f"{_AMPEL_EMOJI[b['hh_status']]} {b['hh_status']}",
             b['korr_hh'] if b['korr_hh'] else "Hochstromstufe trennt Anlauf und Kurzschluss ✓"),
            ("51 ≥ k_S · I_max_Last", f"{b['I51_gewaehlt_prim']:.0f} / {b['I51_emp_prim']:.0f} A prim. (k_S={b['k_S']:g})",
             f"{_AMPEL_EMOJI[b['I51_status']]} {b['I51_status']}",
             b['korr_51'] if b['korr_51'] else "Anregung durch Betriebslast ausgeschlossen ✓"),
            ("Empfindlichkeit Ik,min / 51 ≥ γ", f"{b['empfind']:.2f}  (γ = {b['gamma']})",
             f"{_AMPEL_EMOJI[b['empfind_status']]} {b['empfind_status']}",
             b['korr_emp'] if b['korr_emp'] else "Ik,min regt die 51-Stufe sicher an ✓"),
            ("48 Anlaufkorridor t_A < STARTUP TIME < t_LR",
             f"t_A={b['t_Anlauf']:.1f} · STARTUP={b['Startup_Time']:.1f} · t_LR={b['t_LR_zul']:.1f} s",
             f"{_AMPEL_EMOJI[b['anlauf_status']]} {b['anlauf_status']}",
             b['korr_anl'] if b['korr_anl'] else "Motor läuft thermisch sicher hoch ✓"),
            ("I MOTOR START zwischen Last- und Anlaufstrom",
             f"{b['I_ms_sek']:.3f} A in [{b['I_ms_unten_sek']:.3f} … {b['I_ms_oben_sek']:.3f}] A sek.",
             f"{_AMPEL_EMOJI[b['ms_status']]} {b['ms_status']}",
             b['korr_ms'] if b['korr_ms'] else "Anlauferkennung korrekt positioniert ✓"),
        ], columns=["Größe", "Wert", "Status", "Korrektur / Kommentar"])
        st.dataframe(dfb, width="stretch", hide_index=True)
        if not b["fenster_vorhanden"] and b["f502_obere_prim"]:
            st.caption("Hinweis: Liegt der 1,6-fache Anlaufstrom über dem kleinsten 2-poligen Fehlerstrom, "
                       "existiert kein gültiges 50-2-Fenster — eine unverzögerte Hochstromstufe kann Anlauf und "
                       "Kurzschluss dann nicht trennen. In diesem Fall verzögerte 50-2 oder Motordifferential"
                       "schutz (87M) vorsehen.")

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
            "I [A sek.]": x["I_sek"], "t [s]": x["t"],
            "Siemens-Adresse": x["adresse"],
        } for x in e["reserveschutz"]])
        st.dataframe(dfr, width="stretch", hide_index=True)
        st.caption("Hinweis: bei 'Überlast 49' ist t die Zeitkonstante τ in MINUTEN (7SJ66 Adr.4203) — "
                   "wie beim 7UT613, im Gegensatz zum 7UM62 (Sekunden).")

    # ══════════════════════ ARCHITEKTUR-/ERDSCHLUSS-EMPFEHLUNG ══════════════════════
    with _section("Antriebs-, Kühlungs- & Erdschluss-Empfehlung"):
        eg = e["empfehlung"]
        st.markdown(f"**Erdschlusserfassung:** {eg['erdschluss']}")
        st.markdown(f"**Antrieb:** {eg['antrieb']}")
        st.markdown(f"**Kühlung:** {eg['kuehlung']}")

    # ══════════════════════ HERSTELLERNEUTRALE SOLLWERT-TABELLE ══════════════════════
    with _section("📋  Herstellerneutrale Sollwert-Tabelle (DIGSI-Eingabeliste 7SJ66)"):
        rows = [
            ("49",  "k-Faktor",                f"{b49['k_Faktor']:.2f}",          "x IN",   "Adr.4202"),
            ("49",  "τ thermisch (Minuten!)",  f"{b49['tau_min']:.0f}",           "min",    "Adr.4203"),
            ("49",  "Θ-Warnstufe",             f"{b49['Theta_Warn_pct']:.0f}",    "%",      "Adr.4204"),
            ("49",  "I ALARM",                 f"{b49['I_Warn_sek']:.4f}",        "A sek.", "Adr.4205"),
            ("49",  "Kτ bei Stillstand",       f"{b49['Ktau_Stop']:.1f}",         "-",      "Adr.4207A"),
            ("48",  "STARTUP CURRENT",         f"{b48['Startup_Current_sek']:.4f}", "A sek.", "Adr.4102"),
            ("48",  "STARTUP TIME",            f"{b48['Startup_Time']:.1f}",      "s",      "Adr.4103"),
            ("48",  "LOCK ROTOR TIME",         f"{b48['Lock_Rotor_Time']:.1f}",   "s",      "Adr.4104"),
            ("48",  "I MOTOR START",           f"{b48['I_Motor_Start_sek']:.4f}", "A sek.", "Adr.1107"),
            ("66",  "IStart/IMOTnom",          f"{b66['IStart_IMOTnom']:.2f}",    "-",      "Adr.4302"),
            ("66",  "T START MAX",             f"{b66['T_Start_Max']:.0f}",       "s",      "Adr.4303"),
            ("66",  "MAX. WARM STARTS",        f"{b66['Max_Warm_Starts']:.0f}",   "-",      "Adr.4306"),
            ("51M", "Load Jam I>",             f"{b51M['LoadJam_I_sek']:.4f}",    "A sek.", "Adr.4402"),
            ("51M", "T TRIP",                  f"{b51M['t_TRIP']:.2f}",           "s",      "Adr.4403"),
            ("51M", "T Start Blk.",            f"{b51M['T_Start_Blk']:.2f}",      "s",      "Adr.4406"),
            ("46",  "I2-1 dauernd zul.",       f"{b46['I2_dauer_faktor']*100:.0f}", "%",    "Adr.4002"),
            ("46",  "t 46-1",                  f"{b46['t_46_1']:.2f}",            "s",      "Adr.4003"),
            ("46",  "I2-2 kurzzeitig zul.",    f"{b46['I2_kurz_faktor']*100:.0f}", "%",     "Adr.4004"),
            ("46",  "t 46-2",                  f"{b46['t_46_2']:.2f}",            "s",      "Adr.4005"),
            ("50",  "I>> (50-2)",              f"{umz['I_50_2_sek']:.4f}",        "A sek.", "Adr.1202"),
            ("50",  "t I>> (50-2)",            f"{umz['t_50_2']:.2f}",            "s",      "Adr.1203"),
            ("50",  "I> (50-1)",               f"{umz['I_50_1_sek']:.4f}",        "A sek.", "Adr.1204"),
            ("50",  "t I> (50-1)",             f"{umz['t_50_1']:.2f}",            "s",      "Adr.1205"),
            ("51",  "Ip (AMZ)",                f"{umz['I_51_sek']:.4f}",          "A sek.", "Adr.1207"),
            ("51",  "TIME DIAL",               f"{umz['T_51']:.2f}",              "s",      "Adr.1208"),
            ("37",  "I< (Unterstrom)",         f"{b37['I_unter_sek']:.4f}",       "A sek.", "Setpoint (MV)"),
            ("37",  "t I<",                    f"{b37['t_unter']:.2f}",           "s",      "Setpoint (MV)"),
        ]
        # Erdfehlerschutz — variantenabhaengig (eine Adresse je Zeile)
        if b50N["niederohmig"]:
            rows += [
                ("50N", "I_E>> (50N-2)",       f"{b50N['f_50N2_sek']:.4f}",       "A sek.", "Adr.1302"),
                ("50N", "t 50N-2",             f"{b50N['t_50N2']:.2f}",           "s",      "Adr.1303"),
                ("50N", "I_E> (50N-1)",        f"{b50N['f_50N1_sek']:.4f}",       "A sek.", "Adr.1304"),
                ("50N", "t 50N-1",             f"{b50N['t_50N1']:.2f}",           "s",      "Adr.1305"),
                ("51N", "I_Ep (AMZ)",          f"{b50N['f_51N_sek']:.4f}",        "A sek.", "Adr.1307"),
                ("51N", "TIME DIAL",           f"{b50N['T_51N']:.2f}",            "s",      "Adr.1308"),
                ("51N", "IEC CURVE",           f"{b50N['kennlinie_51N']}",        "-",      "Adr.1311"),
            ]
        else:
            rows += [
                ("64-1",  "U0-Schwelle VN",    f"{b50N['VN_sek']:.1f}",           "V sek.", "Adr.3109"),
                ("64-1",  "t 64-1",            f"{b50N['t_64_1']:.2f}",           "s",      "Adr.3112"),
                ("50Ns",  "I_EE>> (50Ns-2)",   f"{b50N['f_50Ns2_sek']:.4f}",      "A sek.", "Adr.3113"),
                ("50Ns",  "t 50Ns-2",          f"{b50N['t_50Ns2']:.2f}",          "s",      "Adr.3114"),
                ("50Ns",  "I_EE> (50Ns-1)",    f"{b50N['f_50Ns1_sek']:.4f}",      "A sek.", "Adr.3117"),
                ("67Ns",  "Richtung",          f"{b50N['richtung']}",             "-",      "Adr.3115"),
            ]
        # Spannungsschutz 27/59 — nur bei vorhandenem VT
        if f2759["aktiv"]:
            rows += [
                ("59",  "U> (59-1)",           f"{f2759['U59_1']:.1f}",           "V sek.", "Adr.5002"),
                ("59",  "t 59-1",              f"{f2759['t_59_1']:.2f}",          "s",      "Adr.5004"),
                ("59",  "U>> (59-2)",          f"{f2759['U59_2']:.1f}",           "V sek.", "Adr.5005"),
                ("59",  "t 59-2",              f"{f2759['t_59_2']:.2f}",          "s",      "Adr.5007"),
                ("27",  "U< (27-1)",           f"{f2759['U27_1']:.1f}",           "V sek.", "Adr.5102"),
                ("27",  "t 27-1",              f"{f2759['t_27_1']:.2f}",          "s",      "Adr.5106"),
                ("27",  "U<< (27-2)",          f"{f2759['U27_2']:.1f}",           "V sek.", "Adr.5110"),
                ("27",  "t 27-2",              f"{f2759['t_27_2']:.2f}",          "s",      "Adr.5112"),
                ("27",  "DOUT RATIO",          f"{f2759['DOUT_27']:.2f}",         "-",      "Adr.5113A"),
            ]
        # Phasenfolge / Spannungsunsymmetrie 47
        rows.append(("47", "PHASE SEQ.",       f"{f47['phase_seq']}",             "-",      "Adr.209"))
        if f47["aktiv_unsym"]:
            rows += [
                ("47",  "U2> (59-1-V2)",        f"{f47['U59_V2_1']:.1f}",          "V sek.", "Adr.5015"),
                ("47",  "U2>> (59-2-V2)",       f"{f47['U59_V2_2']:.1f}",          "V sek.", "Adr.5016"),
            ]
        dft = pd.DataFrame(rows, columns=["ANSI", "Parameter", "Sollwert", "Einheit", "Adresse (7SJ66)"])
        st.dataframe(dft, width="stretch", hide_index=True)
        st.caption("Jede Zeile entspricht genau einem DIGSI-Eingabefeld (eine Adresse). Sekundärwerte gelten "
                   "für die gewählten Wandler. Alle Größen sind IEC-normiert (A, s, %, min) und damit auf andere "
                   "Relaisfamilien (ABB, GE, SEL) übertragbar; die 7SJ66-Adressen dienen als nachvollziehbare "
                   "Berechnungsgrundlage. Hinweis: τ (Adr.4203) in Minuten — wie 7UT613, nicht wie 7UM62.")
