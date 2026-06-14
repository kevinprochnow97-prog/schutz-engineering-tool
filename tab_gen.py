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
    adr = h.get("adr")
    adr_html = (f'<br>📍 <b>Eintragen unter:</b> {adr}' if adr else "")
    st.markdown(
        f'<div style="font-size:0.72rem;color:#5d6b82;margin:-6px 0 10px;line-height:1.25;">'
        f'<b>Hersteller:</b> {h["range"]}<br>{h["grund"]}{adr_html}</div>',
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
            Ik_min    = st.number_input("Ik min am Schutzgebiet-Ende [kA]", 0.0, value=0.0, step=0.1, format="%.2f", key="gen_30b",
                                        help="Minimaler Kurzschlussstrom nach DIN EN 60909-0 (c=0,95). 0 = nicht vorhanden, dann Näherung 0,3·Ik,max.")

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

            st.markdown("**24 Übererregung U/f**")
            ufw = st.slider("U/f > (Warnung)", 1.00, 1.20, KG.Uf_Warn_def, 0.01, key="gen_08")
            _hreg("Uf_Warn")
            ufa = st.slider("U/f >> (Auslösung)", 1.00, 1.40, KG.Uf_Aus_def, 0.01, key="gen_07")
            _hreg("Uf_Aus")

            st.markdown("**27/59 Spannung [V]**")
            uk  = st.slider("U< [V]", 10.0, 125.0, KG.U_klein_def, 1.0, key="gen_06")
            _hreg("U_klein")  # ← Neu!
            ukk = st.slider("U<< [V]", 10.0, 125.0, KG.U_kleinklein_def, 1.0, key="gen_05")
            _hreg("U_kleinklein")  # ← Neu!
            ug  = st.slider("U> [V]", 30.0, 170.0, KG.U_gross_def, 1.0, key="gen_04")
            _hreg("U_gross")  # ← Neu!
            ugg = st.slider("U>> [V]", 30.0, 170.0, KG.U_grossgross_def, 1.0, key="gen_03")
            _hreg("U_grossgross")  # ← Neu!

            st.markdown("**59N Ständererdschluss**")
            u0  = st.slider("U0> [V]", 2.0, 125.0, KG.U0_def, 0.5, key="gen_02")
            _hreg("U0")

            st.markdown("**64R Läufererdschluss**")
            re_aus = st.slider("RE AUS [kΩ]", 1.0, 5.0, KG.RE_Aus_def, 0.1, key="gen_01")
            _hreg("RE_Aus")

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
        Prueck=prueck, Uf_Warn=ufw, Uf_Aus=ufa,
        U_klein=uk, U_kleinklein=ukk, U_gross=ug, U_grossgross=ugg,
        U0=u0, RE_Aus=re_aus,
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
        # Tabelle 1: einstellbare Hauptparameter (entsprechen den Reglern oben)
        st.markdown("**Einstellbare Hauptparameter** (über die Regler veränderbar)")
        df87a = pd.DataFrame([{
            "Parameter": x["name"], "Eingabe": f"{x['faktor']:g}", "Einheit": x["einheit"],
            "A sek.": f"{x['wert_sek']:.4f}" if x["wert_sek"] is not None else "—",
            "A prim.": f"{x['wert_prim']:.2f}" if x["wert_prim"] is not None else "—",
            "Empfehlung": f"{x['empfehlung']:g}" if x["empfehlung"] is not None else "—",
            "Status": f"{_AMPEL_EMOJI.get(x['status'],'')} {x['status']}",
            "Adresse": x["adresse"],
        } for x in r["rows"] if x.get("einstellbar")])
        st.dataframe(df87a, width="stretch", hide_index=True)

        # Tabelle 2: feste/abgeleitete Voreinstellungen (im Tool nicht als Regler)
        st.markdown("**Feste Voreinstellungen** (nicht über Regler; Werkswerte des 7UM62)")
        df87b = pd.DataFrame([{
            "Parameter": x["name"],
            "Wert": (f"{x['wert_sek']:.4f} A" if x["wert_sek"] is not None else f"{x['faktor']:g} {x['einheit']}"),
            "Adresse": x["adresse"],
        } for x in r["rows"] if not x.get("einstellbar")])
        st.dataframe(df87b, width="stretch", hide_index=True)
        st.caption("I-DIFF>> (unstabilisiert) aus transienter Reaktanz: ≈ 1/x′d, typ. (3…7)·IN "
                   "(7UM62 Hdb. 2.9). Differentialmethodik identisch zum 7UT613 → Herstellerneutralität. "
                   "Die festen Werte (Anlauf-/EXF-Stabilisierung, Verzögerungen) bleiben auf den 7UM62-Werks"
                   "voreinstellungen und werden hier nur zur Vollständigkeit ausgewiesen.")

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

    # ══════════════════════ 24 + 27/59 + 81 ══════════════════════
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

    # ══════════════════════ 59N + 64R ERDSCHLUSS ══════════════════════
    f59n, f64r = e["59N"], e["64R"]
    with _section("ANSI 59N/64G — Ständererdschluss 90 % · ANSI 64R — Läufererdschluss"):
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

    # ══════════════════════ BEMESSUNGS-ENGINEERING ══════════════════════
    b = e["bemessung"]
    with _section("Bemessungs-Engineering — Reserve-Überstromstufe + Empfindlichkeit"):
        st.caption("Kein Ersatz für eine Kurzschlussberechnung — verifiziert die Reservestufe I> gegen "
                   "Maximallast und minimalen Fehlerstrom. Bezug: Generatorklemmen (primär).")
        dfb = pd.DataFrame([
            ("I_max_Last", f"{b['I_max_Last_prim']:.1f} A prim.", "—", "Default 1,0 × IN (Generator-Dauerlast)"),
            ("Ik,min (Schutzgebiet-Ende)", f"{b['I_k_min_prim']:.0f} A prim.", "—", b['I_k_min_quelle']),
            ("I″k Maschine = IN / x″d", f"{b['Ik_masch_sub_prim']:.0f} A prim." if b['Ik_masch_sub_prim'] else "—",
                "—", "Größter subtransienter Eigenstrom (Anfangskurzschlussstrom)"),
            ("Ik,stat Maschine = IN / xd", f"{b['Ik_masch_stat_prim']:.0f} A prim." if b['Ik_masch_stat_prim'] else "—",
                "—", "Stationärer Endwert des abklingenden Eigenstroms"),
            ("I> Empfehlung = k_S · I_max_Last", f"{b['I_emp_prim']:.1f} A prim.",
                f"{_AMPEL_EMOJI[b['I_status']]} {b['I_status']}",
                b['korr_I'] if b['korr_I'] else f"gewählt {b['I_gewaehlt_prim']:.1f} A ≥ Empfehlung ✓"),
            ("I>> unter I″k Maschine", f"{b['I_HH_gewaehlt_prim']:.0f} / {b['Ik_masch_sub_prim']:.0f} A prim." if b['Ik_masch_sub_prim'] else "—",
                f"{_AMPEL_EMOJI[b['hh_status']]} {b['hh_status']}",
                b['korr_hh'] if b['korr_hh'] else "Hochstromstufe spricht bei klemmennahem Fehler an ✓"),
            ("Empfindlichkeit Ik,min / I> ≥ γ", f"{b['empfind']:.2f}  (γ = {b['gamma']})",
                f"{_AMPEL_EMOJI[b['empfind_status']]} {b['empfind_status']}",
                b['korr_emp'] if b['korr_emp'] else "Ik,min regt I> sicher an ✓"),
        ], columns=["Größe", "Wert", "Status", "Korrektur / Kommentar"])
        st.dataframe(dfb, width="stretch", hide_index=True)
        if b["v51_noetig"]:
            st.caption(f"Hinweis 51V: Ik,stat ({b['Ik_masch_stat_prim']:.0f} A) liegt unter I> "
                       f"({b['I_gewaehlt_prim']:.0f} A). Die reine Überstromstufe würde zurückfallen; "
                       "U<-Haltung (Adr.1205) und die spannungsabhängige Stufe 51V (Adr.1401) fangen dies ab.")

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
    with _section("📋  Herstellerneutrale Sollwert-Tabelle (DIGSI-Eingabeliste 7UM62)"):
        rows = []
        # 87G: jede Zeile hat bereits genau eine Adresse
        for x in r["rows"]:
            sek = f"{x['wert_sek']:.4f}" if x["wert_sek"] is not None else f"{x['faktor']:g}"
            rows.append(("87G", x["name"], sek, x["einheit"], x["adresse"]))
        # Alle weiteren Funktionen: ein Parameter = eine Zeile = eine Adresse
        rows += [
            ("50/51", "I> Anregewert",      f"{umz['I_sek']:.4f}", "A sek.", "Adr.1202"),
            ("50/51", "t I>",               f"{umz['t_I']:.2f}",   "s",      "Adr.1203"),
            ("50/51", "U< Haltung",         f"{umz['U_Haltung']:.0f}", "V",  "Adr.1205"),
            ("50",    "I>> Anregewert",     f"{umz['IHH_sek']:.4f}", "A sek.", "Adr.1302"),
            ("50",    "t I>>",              f"{umz['t_IHH']:.2f}", "s",      "Adr.1303"),
            ("51V",   "Ip spannungsabh.",   f"{v51['Ip_sek']:.4f}", "A sek.", "Adr.1402"),
            ("51V",   "T Ip",               f"{v51['T_Ip']:.2f}",  "s",      "Adr.1403"),
            ("51V",   "U< Steuerung",       f"{v51['U_AMZ']:.0f}", "V",      "Adr.1408"),
            ("49",    "k-Faktor",           f"{b49['k_Faktor']:.2f}", "x IN", "Adr.1602"),
            ("49",    "τ thermisch (Sekunden!)", f"{b49['tau_s']:.0f}", "s",  "Adr.1603"),
            ("49",    "Θ-Warnstufe",        f"{b49['Theta_Warn_pct']:.0f}", "%", "Adr.1604"),
            ("46",    "I2 zulässig",        f"{b46['I2_zul_faktor']*100:.1f}", "%", "Adr.1702"),
            ("46",    "I2>>",               f"{b46['I2_HH_faktor']*100:.0f}", "%", "Adr.1706"),
            ("40",    "1/xd KL.1",          f"{f40['xd_KL1']:.2f}", "-",     "Adr.3002"),
            ("40",    "Winkel 1 (α)",       f"{f40['winkel_1']}",  "°",      "Adr.3003"),
            ("40",    "1/xd KL.3",          f"{f40['xd_KL3']:.2f}", "-",     "Adr.3008"),
            ("32",    "Prück> (negativ)",   f"{f32['Prueck_pct']:.2f}", "%", "Adr.3102"),
            ("24",    "U/f > (Warnung)",    f"{f24['Uf_Warn']:.2f}", "-",    "Adr.4302"),
            ("24",    "U/f >> (Auslösung)", f"{f24['Uf_Aus']:.2f}", "-",     "Adr.4304"),
            ("27",    "U<",                 f"{f2759['U_klein']:.0f}", "V",  "Adr.4002"),
            ("59",    "U>",                 f"{f2759['U_gross']:.0f}", "V",  "Adr.4102"),
            ("81",    "f1 (Netztrennung)",  f"{f81['stufen'][0]['f']:.2f}", "Hz", "Adr.4203"),
            ("59N",   "U0>",                f"{f59n['U0']:.1f}",   "V",      "Adr.5002"),
            ("59N",   "3I0>",               f"{f59n['I3I0']:.0f}", "mA",     "Adr.5003"),
            ("64R",   "RE AUS",             f"{f64r['RE_Aus']:.1f}", "kΩ",   "Adr.6003"),
        ]
        dft = pd.DataFrame(rows, columns=["ANSI", "Parameter", "Sollwert", "Einheit", "Adresse (7UM62)"])
        st.dataframe(dft, width="stretch", hide_index=True)
        st.caption("Jede Zeile entspricht genau einem DIGSI-Eingabefeld (eine Adresse). Sekundärwerte "
                   "gelten für die gewählten Wandler. Alle Größen sind IEC-normiert (A, s, %, V, Hz, kΩ, °) "
                   "und damit auf andere Relaisfamilien (ABB, GE, SEL) übertragbar; die 7UM62-Adressen "
                   "dienen als nachvollziehbare Berechnungsgrundlage. Hinweis: τ (Adr.1603) in Sekunden.")
