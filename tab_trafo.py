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
    """Hersteller-Hinweis (Range + Begründung) als kompakte Caption unter einem Regler."""
    h = K.HERST.get(key)
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

    # ══════════════════════ EINGABEN (einklappbar) ══════════════════════
    with _section("Eingaben — Grunddaten, Stromwandler, Netzparameter"):
        ci1, ci2, ci3 = st.columns(3, gap="medium")
        with ci1:
            st.caption("**Transformator-Grunddaten**")
            Sn    = st.number_input("Sn — Bemessungsleistung [MVA]", 0.1, value=16.0, step=0.5, format="%.1f")
            UN_OS = st.number_input("UN OS — Oberspannung [kV]", 1.0, value=110.0, step=1.0, format="%.1f")
            UN_US = st.number_input("UN US — Unterspannung [kV]", 0.4, value=10.0, step=0.1, format="%.1f")
            uk    = st.number_input("uk — Kurzschlussspannung [%]", 1.0, 25.0, value=11.5, step=0.1, format="%.1f")
            vg    = st.selectbox("Vektorgruppe", K.VEKTORGRUPPEN, index=0)
            stp_pm = st.number_input("Stufensteller +/- [%]", 0, 40, value=10, step=1)
        with ci2:
            st.caption("**Stromwandler (primär / sekundär)**")
            c1, c2 = st.columns(2)
            with c1:
                CT_OS_P = st.number_input("CT OS prim. [A]", 1, value=100, step=1)
                CT_US_P = st.number_input("CT US prim. [A]", 1, value=1000, step=1)
                CT_E_P  = st.number_input("CT Erder prim. [A]", 0, value=400, step=1)
            with c2:
                CT_OS_S = st.selectbox("CT OS sek. [A]", [1, 5], index=0)
                CT_US_S = st.selectbox("CT US sek. [A]", [1, 5], index=0)
                CT_E_S  = st.selectbox("CT Erder sek. [A]", [1, 5], index=0)
            ie_wdl = st.checkbox("Sternpunkt-Wandler (IE-CT) vorhanden", value=True)
        with ci3:
            st.caption("**Netzparameter**")
            stp_OS = st.selectbox("Sternpunktbehandlung OS", K.STERNPUNKT_OPTIONEN, index=2)
            stp_US = st.selectbox("Sternpunktbehandlung US", K.STERNPUNKT_OPTIONEN, index=1)
            Ik_OS  = st.number_input("Ik'' max OS [kA]", 0.0, value=10.0, step=0.5, format="%.1f")
            Ik_US  = st.number_input("Ik'' max US [kA]", 0.0, value=8.0, step=0.5, format="%.1f")
            Ik_min_OS = st.number_input("Ik min OS (Schutzgebiet-Ende) [kA]", 0.0, value=0.0, step=0.1, format="%.2f",
                                        help="Minimaler Kurzschlussstrom nach DIN EN 60909-0 (c=0,95). 0 = nicht vorhanden, dann Näherung 0,3·Ik,max OS.")

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

            # I>> OS: Auto aus 1,2/uk bzw. Ik_max_US (mit Override)
            f_IHH_OS_emp = empfehlung_IHH_OS(
                dict(nT=(UN_OS/UN_US if UN_US else 0),
                     IN_OS_prim=(Sn*1e6/(1.7320508*UN_OS*1e3) if UN_OS else 0)),
                dict(k_S_IGG=K.k_S_IGG, Ik_max_US_kA=Ik_US, uk_pct=uk))
            auto_OS = st.checkbox(f"I>> OS automatisch ({f_IHH_OS_emp:g} ×IN)", value=True,
                                  help="Speiseseite: Empfehlung 1,2·Ik_max_US (auf OS bezogen).")
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

            st.markdown("**24 Übererregung U/f**")
            ufw = st.slider("U/f > (Warnung)", 1.00, 1.20, K.Uf_Warn_def, 0.01)
            _hreg("Uf_Warn")
            ufa = st.slider("U/f >> (Auslösung)", 1.00, 1.40, K.Uf_Aus_def, 0.01)
            _hreg("Uf_Aus")

    # ══════════════════════ BERECHNUNG ══════════════════════
    p = dict(
        Sn_MVA=Sn, UN_OS_kV=UN_OS, UN_US_kV=UN_US, uk_pct=uk,
        Vektorgruppe=vg, Stufensteller_pm=stp_pm,
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
        Uf_Warn=ufw, Uf_Aus=ufa,
        k_S_I=kSI, k_S_IGG=kSIGG, gamma=gamma, Inrush_Faktor=inrush,
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
                f'separates 7SJ66 / zentrale Erdschlusserfassung. Quelle: FNN-Leitfaden.</span></div>',
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
        st.caption(f"I>> OS automatisch aus 1,2·Ik_max_US (Speiseseite, Empfehlung {umz['f_IHH_OS_emp']:g} ×IN). "
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
            ("Ik,min (Schutzgebiet-Ende)",f"{b['I_k_min_prim']:.0f} A prim.", "—", b['I_k_min_quelle']),
            ("I> Empfehlung = k_S · I_max_Last", f"{b['I_emp_prim']:.1f} A prim.",
                f"{_AMPEL_EMOJI[b['I_status']]} {b['I_status']}",
                b['korr_I'] if b['korr_I'] else f"gewählt {b['I_gewaehlt_prim']:.1f} A ≥ Empfehlung ✓"),
            ("I>> Empfehlung = max(k_S·Ik_max_US@OS ; Inrush·IN)", f"{b['IHH_emp_prim']:.0f} A prim.",
                f"{_AMPEL_EMOJI[b['IHH_status']]} {b['IHH_status']}",
                b['korr_IHH'] if b['korr_IHH'] else f"gewählt {b['IHH_gewaehlt_prim']:.0f} A ≥ Empfehlung ✓ · maßgebend: {b['massgebend']}"),
            ("Empfindlichkeit I_k_min / I> ≥ γ", f"{b['empfind']:.2f}  (γ = {b['gamma']})",
                f"{_AMPEL_EMOJI[b['empfind_status']]} {b['empfind_status']}",
                b['korr_emp'] if b['korr_emp'] else "I_k_min regt I> sicher an ✓"),
        ], columns=["Größe", "Wert", "Status", "Korrektur / Kommentar"])
        st.dataframe(dfb, width="stretch", hide_index=True)

    # ══════════════════════ ANSI 49 (THERMISCH) + ANSI 46 (SCHIEFLAST) ══════════════════════
    b49, b46 = e["49"], e["46"]
    b24 = e["24"]
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

    # ══════════════════════ ANSI 24 (ÜBERERREGUNG U/f) ══════════════════════
    with _section("ANSI 24 — Übererregungsschutz U/f"):
        df24 = pd.DataFrame([
            ("U/f > (Warnung)",   f"{b24['Uf_Warn']:.2f}", f"{b24['t_Uf_Warn']:.1f}", "Adr.4302 / T 4303"),
            ("U/f >> (Auslösung)", f"{b24['Uf_Aus']:.2f}",  f"{b24['t_Uf_Aus']:.1f}",  "Adr.4304 / T 4305"),
        ], columns=["Stufe", "U/f [-]", "t [s]", "Adresse"])
        st.dataframe(df24, width="stretch", hide_index=True)
        st.caption("Schützt den Kern vor Sättigung durch zu hohe Induktion (Verhältnis U/f, "
                   "bezogen auf den Nennwert U/f = 1,0). Tritt typisch bei Spannungsanstieg nach "
                   "Lastabwurf oder bei Frequenzeinbruch im Inselbetrieb auf. Voraussetzung: 7UT613/633 "
                   "mit Spannungseingang, Projektierung Adr.143 = vorhanden (7UT613 Hdb. 2.11).")

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
    with _section("📋  Herstellerneutrale Sollwert-Tabelle (DIGSI-Eingabeliste)"):
        rows = []
        # 87T: jede Zeile hat bereits genau eine Adresse
        for x in r["rows"]:
            sek = f"{x['wert_sek']:.4f}" if x["wert_sek"] is not None else f"{x['faktor']:g}"
            rows.append(("87T", x["name"], sek, x["einheit"], x["adresse"]))
        # Alle weiteren Funktionen: ein Parameter = eine Zeile = eine Adresse
        rows += [
            ("50/51", "I> Phase OS",   f"{umz['OS']['I_sek']:.4f}",   "A sek.", "Adr.2011 (Seite OS)"),
            ("50/51", "t I> OS",       f"{umz['t_I']:.2f}",           "s",      "Adr.2013 (Seite OS)"),
            ("50/51", "I>> Phase OS",  f"{umz['OS']['IHH_sek']:.4f}", "A sek.", "Adr.2014 (Seite OS)"),
            ("50/51", "t I>> OS",      f"{umz['t_IHH']:.2f}",         "s",      "Adr.2016 (Seite OS)"),
            ("50/51", "I> Phase US",   f"{umz['US']['I_sek']:.4f}",   "A sek.", "Adr.2011 (Seite US)"),
            ("50/51", "I>> Phase US",  f"{umz['US']['IHH_sek']:.4f}", "A sek.", "Adr.2014 (Seite US)"),
            ("49", "k-Faktor",              f"{b49['k_Faktor']:.2f}", "x IN", "Adr.4202"),
            ("49", "τ thermisch (Minuten!)", f"{b49['tau_min']:.0f}",  "min",  "Adr.4203"),
            ("49", "Θ-Warnstufe",           f"{b49['Theta_Warn_pct']:.0f}", "%", "Adr.4204"),
            ("46", "I2 zulässig",           f"{b46['I2_zul_faktor']:.2f}", "I/InS", "Adr.4032"),
            ("24", "U/f > (Warnung)",       f"{b24['Uf_Warn']:.2f}", "-", "Adr.4302"),
            ("24", "U/f >> (Auslösung)",    f"{b24['Uf_Aus']:.2f}", "-", "Adr.4304"),
        ]
        if erde["anwendbar"]:
            rows += [
                ("50N/51N", "IE>",    f"{erde['IE_sek']:.2f}",   "A sek.", "Adr.2413"),
                ("50N/51N", "t IE>",  f"{erde['t_IE']:.2f}",     "s",      "Adr.2414"),
                ("50N/51N", "IE>>",   f"{erde['IEHH_sek']:.2f}", "A sek.", "Adr.2411"),
                ("50N/51N", "t IE>>", f"{erde['t_IEHH']:.2f}",   "s",      "Adr.2412"),
            ]
        if f87n["aktiv"]:
            rows.append(("87N", "I-EDS>", f"{f87n['I_EDS_sek_A']:.4f}", "A sek.", "Adr.1311"))
        else:
            rows.append(("87N", "EDS (deaktiviert: isoliert/komp. → U0-Verfahren)", "—", "–", "—"))
        if u0["aktiv"]:
            rows += [
                ("U0", "U0> Meldung",     f"{u0['U0_Meld_V']:.0f}",  "V", "7SJ66 (sep. Gerät)"),
                ("U0", "t U0> Meldung",   f"{u0['t_Meld']:.0f}",     "s", "7SJ66 (sep. Gerät)"),
                ("U0", "U0>> Abschalt",   f"{u0['U0_Absch_V']:.0f}", "V", "7SJ66 (sep. Gerät)"),
                ("U0", "t U0>> Abschalt", f"{u0['t_Absch']:.0f}",    "s", "7SJ66 (sep. Gerät)"),
            ]
        dft = pd.DataFrame(rows, columns=["ANSI", "Parameter", "Sollwert", "Einheit", "Adresse"])
        st.dataframe(dft, width="stretch", hide_index=True)
        st.caption("Jede Zeile entspricht genau einem DIGSI-Eingabefeld (eine Adresse). Die "
                   "U0-Erdschlusserfassung läuft im isolierten/kompensierten Netz auf einem separaten "
                   "7SJ66. Alle Werte sind IEC-normiert und auf andere Relaisfamilien übertragbar. "
                   "Hinweis: τ (Adr.4203) in Minuten.")
