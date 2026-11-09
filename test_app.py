"""
test_app.py — Automatisierte Verifikation des Gesamtsystems
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Setzt die in Abschnitt 9.2 der Masterarbeit beschriebene automatisierte
Verifikation um (vgl. Anforderung NF4, Testbarkeit):

1. Strukturtest: Die Anwendung wird über das Testmodul AppTest des
   Streamlit-Frameworks ohne Browser ausgeführt. Referenzkriterium ist ein
   vollstaendiger Durchlauf ohne Ausnahme im Berechnungskern sowie die
   Referenzinventur der Oberflaeche (6 Tabs, 86 Aufklappbereiche,
   53 Ergebnistabellen).
2. Validierungstestfall: Der Berechnungskern reproduziert das durchgerechnete
   Zahlenbeispiel aus Kapitel 2.4 des 7UT613-Handbuchs (35 MVA, 110/20 kV,
   uk = 15 %, Wandler 200 A/5 A).
3. Parametervariation: Die Empfehlungsformel der Hochstromstufe wird ueber den
   zulaessigen uk-Bereich gefuehrt und auf Ausnahmefreiheit und Plausibilitaet
   geprueft (Deckelung auf 15 x IN bei kleinen uk).

Ausfuehren mit:  python test_app.py   (oder: pytest test_app.py)
Hinweis: Aendert sich die Oberflaeche (neue Expander oder Tabellen), sind die
Referenzzahlen hier UND in Abschnitt 9.2 der Masterarbeit nachzuziehen.
"""

from streamlit.testing.v1 import AppTest

import calc_trafo

# ── Referenzinventur (Stand Masterarbeit, Abschnitt 9.2) ─────────────────────
REF_TABS      = 7   # 6 aus der Masterarbeit + Netz-Tab (Selektivitaet)
REF_EXPANDER  = 86
REF_TABELLEN  = 53


def _inventur(at: AppTest) -> dict:
    """Zaehlt Elementtypen im gerenderten Elementbaum der Anwendung."""
    counts = {}

    def walk(node):
        typ = getattr(node, "type", None)
        if typ:
            counts[typ] = counts.get(typ, 0) + 1
        for kind in getattr(node, "children", {}).values():
            walk(kind)

    walk(at._tree)
    return counts


def _fill_grunddaten(at):
    """Traegt fuer alle fuenf Betriebsmittel repraesentative Grunddaten ein.

    Seit der Umstellung auf den Leerstart (keine Beispielwerte in den Grunddaten)
    zeigt jeder Tab ohne ausgefuellte Pflichtfelder nur einen Hinweis. Fuer die
    Struktur-/Inventurpruefung werden die Grunddaten daher zunaechst gesetzt.
    Referenzwerte entsprechen den frueheren Voreinstellungen (u. a. dem 7UT613-
    Validierungsfall) und sind bewusst identisch zu Abschnitt 9.2 der Masterarbeit.
    """
    by_label = {
        # Transformator (Grunddaten ohne Widget-Key -> ueber das Label setzen)
        "Sn — Bemessungsleistung [MVA]": 16.0,
        "UN OS — Oberspannung [kV]": 110.0, "UN US — Unterspannung [kV]": 10.0,
        "uk — Kurzschlussspannung [%]": 11.5, "Stufensteller +/- [%]": 10,
        "CT OS prim. [A]": 100, "CT US prim. [A]": 1000, "CT Erder prim. [A]": 400,
        "Ik\u2033 max OS [kA]": 10.0, "Ik\u2033 max US [kA]": 8.0,
    }
    by_key = {
        # Generator
        "gen_46": 16.0, "gen_45": 10.5, "gen_44": 0.8, "gen_42": 0.14,
        "gen_41": 0.20, "gen_40": 2.0, "gen_39": 1000, "gen_38": 1000,
        "gen_35": 10.5, "gen_34": 100.0, "gen_30": 8.0,
        # Motor
        "mot_50": 1500.0, "mot_49": 6.0, "mot_48": 0.88, "mot_47": 0.95,
        "mot_45": 300, "mot_43": 6.0, "mot_42": 1.10, "mot_41": 8.0,
        "mot_40": 10.0, "mot_36": 4.0,
        # Leitung
        "ltg_un": 110.0, "ltg_l": 25.0, "ltg_xbel": 0.4, "ltg_cbel": 0.009,
        "ltg_phi": 75, "ltg_in": 600.0, "ltg_ctp": 600, "ltg_vtp": 110.0,
        "ltg_vts": 100.0, "ltg_ikmax": 12.0,
        # Sammelschiene
        "sb_un": 20.0, "sb_nabz": 8, "sb_inref": 2000.0, "sb_ctp": 2000,
        "sb_imaxlast": 1800.0, "sb_imaxabz": 600.0, "sb_isccmin": 8.0,
        "sb_isccmax": 25.0, "sb_tls": 0.06,
    }
    for w in at.number_input:
        if w.key in by_key:
            w.set_value(by_key[w.key])
        elif (w.label or "") in by_label:
            w.set_value(by_label[w.label or ""])
    at.run()
    return at


def test_leerstart():
    """Leerstart: ohne Grunddaten oeffnet jeder Tab ausnahmefrei mit einem Hinweis.

    Sicherstellt, dass der 'Auf-Null'-Zustand sauber ist (keine Fehlermeldungen,
    keine Ampel-Warnungen) und pro Betriebsmittel genau ein Ausfuell-Hinweis
    erscheint.
    """
    at = AppTest.from_file("app.py", default_timeout=240)
    at.run()
    assert len(at.exception) == 0, (
        f"{len(at.exception)} Ausnahme(n) beim Leerstart: "
        + "; ".join(str(e.value)[:120] for e in at.exception))
    assert len(at.info) == 6, (
        f"Erwartet 1 Ausfuell-Hinweis je Betriebsmittel (5) plus Netz-Tab (1), "
        f"gefunden {len(at.info)}.")
    counts = _inventur(at)
    assert counts.get("dataframe", 0) == 0, (
        "Im Leerstart darf keine Ergebnistabelle gerendert werden, gefunden "
        f"{counts.get('dataframe', 0)}.")
    print(f"Leerstart OK: 6 Ausfuell-Hinweise (5 Betriebsmittel + Netz), 0 Tabellen, 0 Ausnahmen.")


def test_struktur():
    """Strukturtest: Grunddaten befuellen, dann Ausnahmefreiheit und Inventur pruefen."""
    at = AppTest.from_file("app.py", default_timeout=240)
    at.run()
    _fill_grunddaten(at)

    assert len(at.exception) == 0, (
        f"{len(at.exception)} Ausnahme(n) im Berechnungskern: "
        + "; ".join(str(e.value)[:120] for e in at.exception))

    counts = _inventur(at)
    ist = (counts.get("tab", 0), counts.get("expander", 0),
           counts.get("dataframe", 0))
    soll = (REF_TABS, REF_EXPANDER, REF_TABELLEN)
    assert ist == soll, (
        f"Oberflaechen-Inventur abweichend: Tabs/Expander/Tabellen ist {ist}, "
        f"Referenz {soll}. Referenzzahlen hier und in Abschnitt 9.2 der "
        f"Masterarbeit anpassen.")
    print(f"Strukturtest OK: {ist[0]} Tabs, {ist[1]} Expander, "
          f"{ist[2]} Tabellen, 0 Ausnahmen (nach Befuellen der Grunddaten).")


def test_validierung_handbuch():
    """Validierungstestfall aus Kapitel 9 der Masterarbeit (7UT613 Hdb. 2.4)."""
    p = {"Sn_MVA": 35.0, "UN_OS_kV": 110.0, "UN_US_kV": 20.0,
         "CT_OS_Prim": 200.0, "CT_OS_Sek": 5.0,
         "CT_US_Prim": 1200.0, "CT_US_Sek": 5.0,
         "CT_E_Prim": 200.0, "CT_E_Sek": 5.0,
         "uk_pct": 15.0}
    g = calc_trafo.grundgroessen(p)
    umz = calc_trafo.schutz_5051_phase(g, p)

    assert abs(g["IN_OS_prim"] - 183.7) < 0.05, g["IN_OS_prim"]
    assert abs(g["kCT_OS"] - 40.0) < 1e-9, g["kCT_OS"]
    assert abs(umz["f_IHH_OS_emp"] - 8.0) < 1e-9, umz["f_IHH_OS_emp"]
    assert abs(umz["OS"]["IHH_prim"] - 1469.6) < 0.1, umz["OS"]["IHH_prim"]
    assert abs(umz["OS"]["IHH_sek"] - 36.7) < 0.05, umz["OS"]["IHH_sek"]
    print("Validierungstestfall OK: 183,7 A / 1469,6 A / 36,7 A / Faktor 8,0.")


def test_parametersweep_uk():
    """Empfehlungen ueber den uk-Bereich: ausnahmefrei und formeltreu.

    50/51 (Speiseseite): Empfehlung 1,2/uk ohne Deckelung (Hdb.-Regel).
    87T Idiff>>: Empfehlung MIN(15, ROUND(120/uk, 1)) mit Deckelung auf 15 x IN
    (vgl. Masterarbeit, Abschnitt Differenzialschutz 87T).
    """
    p_basis = {"Sn_MVA": 16.0, "UN_OS_kV": 110.0, "UN_US_kV": 10.5,
               "CT_OS_Prim": 100.0, "CT_OS_Sek": 1.0,
               "CT_US_Prim": 1000.0, "CT_US_Sek": 1.0,
               "CT_E_Prim": 100.0, "CT_E_Sek": 1.0,
               "Stufensteller_pm": 10.0}
    for uk_zehntel in range(40, 205, 5):          # uk = 4,0 ... 20,0 %
        uk = uk_zehntel / 10.0
        p = dict(p_basis, uk_pct=uk)
        g = calc_trafo.grundgroessen(p)

        emp_umz = calc_trafo.empfehlung_IHH_OS(g, p)
        erwartet_umz = round(1.2 / (uk / 100.0), 2)
        assert emp_umz > 0, (uk, emp_umz)
        assert abs(emp_umz - erwartet_umz) < 0.011, (uk, emp_umz, erwartet_umz)

        b87 = calc_trafo.schutz_87T(g, p)
        emp_diff = b87["rows"][1]["empfehlung"]   # Zeile I-DIFF>>
        erwartet_diff = min(15.0, round(120.0 / uk, 1))
        assert abs(emp_diff - erwartet_diff) < 0.011, (uk, emp_diff, erwartet_diff)
        assert emp_diff <= 15.0 + 1e-9, (uk, emp_diff)
    print("Parametervariation OK: uk = 4 ... 20 %, 50/51 nach 1,2/uk, "
          "87T gedeckelt auf 15 x IN.")


if __name__ == "__main__":
    test_leerstart()
    test_struktur()
    test_validierung_handbuch()
    test_parametersweep_uk()
    print("\nAlle Pruefungen bestanden.")
