"""
konstanten_netz.py - Vorgaben fuer die netzweite Selektivitaetsplanung
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Reines Python-Modul OHNE Streamlit.

Alle Werte in dieser Datei sind TOOL-VORGABEN, keine Werksvoreinstellungen
eines Geraets. Herleitung und Quellen: docs/tool_vorgabe_staffelabstand.md.
Die Einzelwerte sind dort als "gegen Handbuch pruefen" markiert, solange sie
nicht gegen die Technischen Daten der eingesetzten Geraete und Schalter
bestaetigt sind.
"""

# ── Staffelabstand fuer UMZ-Stufen numerischer Schutzgeraete ─────────────────
# Zusammensetzung: dt = t_LS + t_Rueck + 2 * t_Tol + t_Sich
# (Form nach ABB Distribution Automation Handbook, Abschnitt 8.2, Gl. 8.2.2)
dt_t_LS     = 0.080   # Ausschaltzeit Leistungsschalter inkl. Lichtbogenzeit   [s]
dt_t_Rueck  = 0.030   # Rueckfallzeit (Ueberlaufzeit) des oberen Schutzes      [s]
dt_t_Tol    = 0.025   # Zeittoleranz je Geraet, geht fuer zwei Geraete ein     [s]
dt_t_Sich   = 0.020   # Sicherheitszuschlag, ca. eine Netzperiode bei 50 Hz    [s]
dt_Raster   = 0.050   # Einstellraster, auf das der Mindestwert aufgerundet wird [s]


def dt_summe() -> float:
    """Rechnerische Summe der Einzelanteile (ohne Rundung)."""
    return dt_t_LS + dt_t_Rueck + 2 * dt_t_Tol + dt_t_Sich


def _aufrunden(wert: float, raster: float) -> float:
    schritte = int(wert / raster + 1e-9)
    if schritte * raster < wert - 1e-9:
        schritte += 1
    return round(schritte * raster, 6)


# Technischer Mindestabstand: Summe der Einzelanteile, auf das Raster aufgerundet.
# Darunter ist Selektivitaet auch mit schnellen Schaltern nicht mehr gesichert.
dt_Staffel_min = _aufrunden(dt_summe(), dt_Raster)      # 0,18 s -> 0,20 s

# Soll-Staffelabstand (Tool-Vorgabe). Enthaelt gegenueber dem Mindestwert eine
# Reserve fuer Wandlersaettigung durch das Gleichstromglied und fuer langsamere
# Schalter. Gleicher Wert wie konstanten_trafo.dt_Staffel (ein Test prueft das).
dt_Staffel_soll = 0.30

# ── Zahlentoleranzen der Auswertung ──────────────────────────────────────────
EPS_ZEIT  = 1e-6      # Zeitvergleich: 0,8 - 0,5 ist in Gleitkomma nicht exakt 0,3  [s]
EPS_STROM = 1e-3      # Stromvergleich relativ: gleiche Ansprechwerte auf OS und US
                      # eines Trafos unterscheiden sich nach der Umrechnung nur
                      # durch die Rundung im Rechenkern (4 Nachkommastellen)

# ── AMZ-Kennlinien nach IEC 60255-151: t = T * k / ((I/Ip)^alpha - 1) ────────
# Schluessel sind die Kennliniennamen, wie sie die Rechenkerne liefern.
# Unbekannte Namen werden in der Staffelpruefung nicht bewertet und gemeldet.
AMZ_KENNLINIEN = {
    "Invers (IEC, normal inverse)": (0.14, 0.02),     # konstanten_motor.Kennlinie_51_def
    "Normal Invers (IEC)":          (0.14, 0.02),
    "Stark invers (IEC)":           (13.5, 1.0),
    "Extrem invers (IEC)":          (80.0, 2.0),
}
# Eine AMZ-Stufe regt erst oberhalb ihres Einstellwerts Ip an. Tool-Vorgabe 1,1 * Ip
# (uebliche Anregeschwelle numerischer Geraete, gegen 7SJ66 Techn. Daten pruefen).
AMZ_Anregefaktor = 1.10
# Stuetzstellen je Pruefung, wenn eine AMZ-Stufe beteiligt ist (logarithmisch verteilt)
AMZ_Stuetzstellen = 60
