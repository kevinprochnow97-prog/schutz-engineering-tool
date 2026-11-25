"""
netz_formular.py - Logik der Netz-Formulare (Anlegen und Bearbeiten), ohne Streamlit
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reines Python-Modul (isoliert testbar). tab_netz.py reicht die Formularwerte hierher
durch und zeigt nur an, was zurueckkommt. Geschrieben wird ausschliesslich ueber die
Methoden von netz_modell.Netz. Das Modell bleibt die einzige Wahrheit, ein Formular ist
nur ein Entwurf, der erst mit "anlegen" bzw. "speichern" ins Modell geschrieben wird.

Vertrag aller Funktionen "anlegen" und "aendern":
  - Rueckgabe: kurze Erfolgsmeldung (Text).
  - Fehler: ModellFehler mit deutscher Meldung. Das Netz bleibt dann unveraendert,
    weil Netz.* erst komplett prueft und dann ersetzt. tab_netz.py laesst in diesem
    Fall die Eingaben im Formular stehen.

Vorbelegung (KNOTEN_LEER, ELEMENT_LEER): so sieht ein Anlegen-Formular nach dem
Oeffnen und nach jedem erfolgreichen Anlegen aus.
"""

from __future__ import annotations

from netz_modell import ELEMENTTYPEN, STERNPUNKTE, ModellFehler, Netz

# Auswahlwert "kein Knoten" in den Selectboxen (Einspeisung/Generator ohne von, Motor ohne nach)
OHNE = "—"

# Schluessel im Parametersatz der Einspeisung (Schutz des Netzbetreibers am Uebergabepunkt)
NB_STROM = "I_gt_NB_A"
NB_ZEIT = "t_gt_NB_s"

KNOTEN_LEER = {
    "id": "", "name": "", "UN_kV": None, "sternpunkt": STERNPUNKTE[0],
    "Ik_max_kA": None, "Ik_min_kA": None, "I_E_begr_A": None,
}

ELEMENT_LEER = {
    "id": "", "name": "", "typ": next(iter(ELEMENTTYPEN)), "von": OHNE, "nach": OHNE,
    "zustand": "ein", "uebernehmen": True, "I_nb_A": None, "t_nb_s": None,
}


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────
def _text(x) -> str:
    return "" if x is None else str(x).strip()


def _zahl(x):
    return None if x is None else float(x)


def _knoten_oder_none(x):
    return None if x in (None, "", OHNE) else x


def _g(x) -> str:
    """Zahl fuer Meldungen: ohne Nachkomma, wenn ganzzahlig."""
    return f"{x:g}" if isinstance(x, (int, float)) else str(x)


def _knoten_dict(netz: Netz, kid: str) -> dict:
    k = netz.knoten.get(kid)
    if k is None:
        raise ModellFehler(f"Knoten {kid} existiert nicht.")
    return k.to_dict()


# ── Anlegen ──────────────────────────────────────────────────────────────────
def knoten_anlegen(netz: Netz, kid, name, UN_kV, sternpunkt,
                   Ik_max_kA=None, Ik_min_kA=None, I_E_begr_A=None) -> str:
    """
    Knoten anlegen. Ik 0 gilt wie leer (die Felder sind optional). Die Erdfehlerstrom-
    Begrenzung gilt nur bei niederohmiger Erdung, sonst wird sie verworfen und gemeldet.
    """
    kid = _text(kid)
    I_E, hinweis = _begrenzung(sternpunkt, I_E_begr_A)
    netz.knoten_hinzufuegen(kid, _text(name), _zahl(UN_kV), sternpunkt,
                            _zahl(Ik_max_kA) or None, _zahl(Ik_min_kA) or None, I_E)
    return f"Knoten {kid} angelegt.{hinweis}"


def _begrenzung(sternpunkt, I_E) -> tuple:
    """(Wert fuers Modell, Hinweistext). Nur bei niederohmig, 0 gilt wie leer."""
    I_E = _zahl(I_E) or None
    if I_E is not None and sternpunkt != "niederohmig":
        return None, (" Die Erdfehlerstrom-Begrenzung gilt nur bei niederohmiger Erdung "
                      "und wurde nicht übernommen.")
    return I_E, ""


def element_anlegen(netz: Netz, eid, name, typ, von, nach, zustand="ein",
                    p_tab: dict | None = None, tab_name: str | None = None,
                    uebernehmen: bool = True, I_nb_A=None, t_nb_s=None) -> str:
    """
    Element anlegen. Nicht benoetigte Knotenfelder werden ignoriert (Einspeisung und
    Generator nutzen nur nach, der Motor nur von).
    p_tab:    Parametersatz des passenden Betriebsmittel-Tabs (oder None)
    tab_name: Anzeigename dieses Tabs, None wenn der Typ keinen Tab hat
    """
    eid = _text(eid)
    if typ not in ELEMENTTYPEN:
        raise ModellFehler(f"Element {eid}: Typ {typ!r} ist nicht zulässig.")
    braucht_von, braucht_nach = ELEMENTTYPEN[typ]
    v = _knoten_oder_none(von) if braucht_von else None
    n = _knoten_oder_none(nach) if braucht_nach else None
    p, hinweis = {}, ""
    if uebernehmen and tab_name is not None:
        p = dict(p_tab or {})
        hinweis = (f" Parameter aus dem Tab {tab_name} übernommen." if p else
                   f" Im Tab {tab_name} sind noch keine Grunddaten berechnet, "
                   f"Parameter bleiben leer.")
    if typ == "leitung" and p.get("uebs_betriebsart") != "Aus":
        # Staffelung im Strahlennetz braucht die immer aktive UMZ-Stufe (Entscheidung 17.11.2026);
        # der Not-UMZ ist nur bei Spannungsausfall wirksam. "Aus" bleibt, wie vom Nutzer gesetzt.
        if p.get("uebs_betriebsart") not in (None, "Ein: immer aktiv"):
            hinweis += " Betriebsart Not-UMZ auf „Ein: immer aktiv“ gesetzt (Staffelung)."
        p["uebs_betriebsart"] = "Ein: immer aktiv"
    if typ == "einspeisung":
        if I_nb_A:
            p[NB_STROM] = float(I_nb_A)
        if t_nb_s:
            p[NB_ZEIT] = float(t_nb_s)
    netz.element_hinzufuegen(eid, _text(name), typ, v, n, p, zustand)
    return f"Element {eid} angelegt.{hinweis}"


# ── Bearbeiten: Werte fuer die Vorbelegung ───────────────────────────────────
def knoten_werte(netz: Netz, kid: str) -> dict:
    """Aktuelle Werte eines Knotens in den Feldnamen von KNOTEN_LEER (ohne id)."""
    d = _knoten_dict(netz, kid)
    return {f: d[f] for f in ("name", "UN_kV", "sternpunkt", "Ik_max_kA", "Ik_min_kA", "I_E_begr_A")}


def element_werte(netz: Netz, eid: str) -> dict:
    """Aktuelle Werte eines Elements fuer das Bearbeiten-Formular."""
    e = netz.elemente.get(eid)
    if e is None:
        raise ModellFehler(f"Element {eid} existiert nicht.")
    return {"name": e.name, "typ": e.typ, "von": e.von or OHNE, "nach": e.nach or OHNE,
            "I_nb_A": e.p.get(NB_STROM), "t_nb_s": e.p.get(NB_ZEIT)}


# ── Bearbeiten: ins Modell schreiben ─────────────────────────────────────────
def knoten_aendern(netz: Netz, kid: str, name, UN_kV, sternpunkt,
                   Ik_max_kA=None, Ik_min_kA=None, I_E_begr_A=None) -> str:
    """
    Alle aenderbaren Felder eines Knotens setzen. Die ID bleibt, damit die Verbindungen
    der Elemente erhalten bleiben. Ik 0 gilt wie leer. Die Erdfehlerstrom-Begrenzung gilt
    nur bei niederohmiger Erdung (sonst verworfen, mit Hinweis).
    """
    alt = _knoten_dict(netz, kid)
    I_E, hinweis = _begrenzung(sternpunkt, I_E_begr_A)
    netz.knoten_aendern(kid, name=_text(name), UN_kV=_zahl(UN_kV), sternpunkt=sternpunkt,
                        Ik_max_kA=_zahl(Ik_max_kA) or None, Ik_min_kA=_zahl(Ik_min_kA) or None,
                        I_E_begr_A=I_E)
    neu = _knoten_dict(netz, kid)
    namen = {"name": "Bezeichnung", "UN_kV": "UN", "sternpunkt": "Sternpunkt",
             "Ik_max_kA": "Ik″ max", "Ik_min_kA": "Ik min", "I_E_begr_A": "Erdfehlerstrom-Begrenzung"}
    diff = [f"{namen[f]} {_g(alt[f])} → {_g(neu[f])}" for f in namen
            if alt[f] != neu[f] and f != "name"]
    if alt["name"] != neu["name"]:
        diff.insert(0, "Bezeichnung geändert")
    if diff:
        return f"Knoten {kid} geändert: {'; '.join(diff)}.{hinweis}"
    return f"Knoten {kid}: keine Änderung.{hinweis}"


def element_aendern(netz: Netz, eid: str, name, von=None, nach=None,
                    I_nb_A=None, t_nb_s=None) -> str:
    """
    Bezeichnung, von- und nach-Knoten (und beim Netzbetreiber-Schutz der Einspeisung
    I> und t) eines Elements aendern. ID, Typ und Zustand bleiben, ebenso der
    Parametersatz (Trafo: CT, Sn, uk usw.). Zustand schaltet der Knopf Ein/Aus.
    Erst Modell-Pruefung, dann Ersetzen: bei Fehler bleibt das Element wie es war.
    Bei einem Trafo steht von fuer die Oberspannungsseite (OS). Wer die Richtung
    korrigiert, tauscht nur die beiden Knoten, die Seitenangaben im Parametersatz
    (CT OS/US) gehoeren zu den physischen Seiten und stimmen danach.
    """
    e = netz.elemente.get(eid)
    if e is None:
        raise ModellFehler(f"Element {eid} existiert nicht.")
    braucht_von, braucht_nach = ELEMENTTYPEN[e.typ]
    v = _knoten_oder_none(von) if braucht_von else None
    n = _knoten_oder_none(nach) if braucht_nach else None
    p = dict(e.p)
    if e.typ == "einspeisung":
        for schluessel, wert in ((NB_STROM, I_nb_A), (NB_ZEIT, t_nb_s)):
            if wert:
                p[schluessel] = float(wert)
            else:
                p.pop(schluessel, None)
    netz.element_aendern(eid, name=_text(name), von=v, nach=n, p=p)
    neu = netz.elemente[eid]
    diff = []
    if e.name != neu.name:
        diff.append("Bezeichnung geändert")
    if e.von != neu.von:
        diff.append(f"von {e.von} → {neu.von}")
    if e.nach != neu.nach:
        diff.append(f"nach {e.nach} → {neu.nach}")
    if e.p != neu.p:
        diff.append("Netzbetreiber-Schutz geändert")
    ende = " Parameter und Verbindungen zu den übrigen Elementen bleiben erhalten." if diff else ""
    return (f"Element {eid} geändert: {'; '.join(diff)}.{ende}" if diff
            else f"Element {eid}: keine Änderung.")
