"""
gegenrechnung_pandapower.py - Gegenrechnung der Kurzschlussstroeme mit pandapower (IEC 60909)
Herstellerneutrales Schutz-Engineering-Tool | HSU Hamburg

Baut das Referenznetz "Industrie 10 kV" in pandapower nach und vergleicht Ik max (dreipolig),
Ik min (zweipolig) und Ik max mit Motoren mit netz_kurzschluss.berechne().
Nicht Teil der App, nur fuer die Pruefung (pandapower ist keine Abhaengigkeit des Tools).

Aufruf aus dem Repo-Ordner:
    pip install pandapower
    python werkzeuge/gegenrechnung_pandapower.py .

Stand 17.11.2026 (pandapower 3.5.6): Abweichung an allen fuenf Knoten 0,00 % in allen drei Faellen.

Erdfehler (ab 25.11.2026): zusaetzlich Ik1 max und Ik1 min (fault = "1ph") fuer das Referenznetz und
das Beispielnetz industrie_10kV_noe.json (niederohmig, Sternpunktbildner an K2, 2000 A). Stand
25.11.2026: Abweichung an allen Knoten 0,00 %. Nachbau: Einspeisung x0x = 1, r0x0 = 0,1; Trafos mit
vector_group, vk0 = vk; Leitung R0' = 4 R1', X0' = 4 X1' (RE/RL = XE/XL = 1); Sternpunktbildner als
YNd-Trafo an K2 auf einen leeren Hilfsknoten (vk 1e-4 %) mit rn_ohm = R_E. Der Motor M2 des
Beispielnetzes hat im Nullsystem keinen Beitrag und fehlt deshalb im Nachbau.
Hinweise zum Nachbau: Motor als Asynchronmaschine nur ueber lrc_pu (k = 0, sonst rechnet pandapower
zusaetzlich eine Stromquelle), lv_tol_percent = 10.

Ab 25.11.2026 (Pruefung gegen DIN EN 60909-0:2016-12): Ik max enthaelt die Motoren, der Wert ohne
Motoren steht in Ik_max_ohne_Motor_kA. Ik min rechnet mit der Endtemperatur je Leitung aus der
adiabatischen Erwaermung (KurzschlussErgebnis.theta_e). pandapower bekommt diese Temperatur als
endtemp_degree je Leitung, die Gegenrechnung prueft also die Umsetzung von Gl. (32), nicht die
Erwaermungsrechnung selbst (die steht in test_netz_kurzschluss.py als Handrechnung).
"""
import sys, warnings, math, os
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "."))
import pandapower as pp, pandapower.shortcircuit as sc
import netz_kurzschluss as K
from netz_modell import Netz

THETA = {}          # Leitung -> Endtemperatur aus dem Tool, wird unten gesetzt


def bau(motor=False):
    net = pp.create_empty_network(sn_mva=100)
    b = {k: pp.create_bus(net, vn_kv=u, name=k) for k, u in
         (("K1",110),("K2",10),("K3",10),("K4",10),("K5",0.4))}
    pp.create_ext_grid(net, b["K1"], s_sc_max_mva=3000, s_sc_min_mva=1500, rx_max=0.1, rx_min=0.1)
    for n,(hv,lv,s,uh,ul,vk) in {"T1":("K1","K2",20,110,10,12),"T2":("K4","K5",1.6,10,0.4,6)}.items():
        pp.create_transformer_from_parameters(net, b[hv], b[lv], sn_mva=s, vn_hv_kv=uh, vn_lv_kv=ul,
            vkr_percent=0.0, vk_percent=vk, pfe_kw=0, i0_percent=0, name=n)
    r = 0.11/math.tan(math.radians(28.1))
    for n,(a,c,l) in {"L1":("K2","K3",0.5),"L2":("K2","K4",1.2)}.items():
        pp.create_line_from_parameters(net, b[a], b[c], length_km=l, r_ohm_per_km=r, x_ohm_per_km=0.11,
            c_nf_per_km=0, max_i_ka=0.3, endtemp_degree=THETA.get(n, 90.0), name=n)
    if motor:
        Sn = 2.0/(0.88*0.96)
        pp.create_sgen(net, b["K3"], p_mw=0, sn_mva=Sn, k=5.5, lrc_pu=5.5, rx=0.1, generator_type="async", name="M1")
        net.sgen["k"] = 0.0; net.sgen["lrc_pu"] = 5.5; net.sgen["rx"] = 0.1
    return net, b

def pp_ik(motor, fall, fault):
    net, b = bau(motor)
    sc.calc_sc(net, case=fall, fault=fault, lv_tol_percent=10, branch_results=False,
               ip=False, ith=False, tk_s=1.0)
    return {k: net.res_bus_sc.ikss_ka.at[v] for k, v in b.items()}

n = Netz.laden(os.path.join(sys.path[0], "beispielnetze", "industrie_10kV.json"))
erg = K.berechne(n)
t = erg.knoten
THETA.update(erg.theta_e)
print("Endtemperaturen bei Ik min:", {k: round(v, 1) for k, v in THETA.items()})
mx = pp_ik(False, "max", "3ph"); mn = pp_ik(False, "min", "2ph")
try: mm = pp_ik(True, "max", "3ph")
except Exception as e: mm = None; print("Motor:", e)
print(f"{'Knoten':6} {'Tool max':>9} {'pp max':>9} {'Abw':>7} | {'Tool min':>9} {'pp min':>9} {'Abw':>7} | {'Tool mM':>8} {'pp mM':>8} {'Abw':>7}")
for k in mx:
    a, c = t[k].Ik_max_ohne_Motor_kA, mx[k]; d, e = t[k].Ik_min_kA, mn[k]
    s = f"{k:6} {a:9.3f} {c:9.3f} {100*(a/c-1):6.2f}% | {d:9.3f} {e:9.3f} {100*(d/e-1):6.2f}%"
    if mm: s += f" | {t[k].Ik_max_kA:8.3f} {mm[k]:8.3f} {100*(t[k].Ik_max_kA/mm[k]-1):6.2f}%"
    print(s)


# ── Erdfehler (einpolig) ─────────────────────────────────────────────────────
def bau_null(noe=False, IE=2000.0, motor=False):
    net = pp.create_empty_network(sn_mva=100)
    b = {k: pp.create_bus(net, vn_kv=u, name=k) for k, u in
         (("K1",110),("K2",10),("K3",10),("K4",10),("K5",0.4))}
    pp.create_ext_grid(net, b["K1"], s_sc_max_mva=3000, s_sc_min_mva=1500, rx_max=0.1, rx_min=0.1,
                       x0x_max=1.0, r0x0_max=0.1, x0x_min=1.0, r0x0_min=0.1)
    for n,(hv,lv,s,uh,ul,vk,vg) in {"T1":("K1","K2",20,110,10,12,"YNd"),
                                     "T2":("K4","K5",1.6,10,0.4,6,"Dyn")}.items():
        pp.create_transformer_from_parameters(net, b[hv], b[lv], sn_mva=s, vn_hv_kv=uh, vn_lv_kv=ul,
            vkr_percent=0.0, vk_percent=vk, pfe_kw=0, i0_percent=0, name=n, vector_group=vg,
            vk0_percent=vk, vkr0_percent=0.0, mag0_percent=100, mag0_rx=0, si0_hv_partial=0.9)
    if noe:
        h = pp.create_bus(net, vn_kv=0.4, name="Hilf")
        pp.create_transformer_from_parameters(net, b["K2"], h, sn_mva=1000, vn_hv_kv=10, vn_lv_kv=0.4,
            vkr_percent=0.0, vk_percent=1e-4, pfe_kw=0, i0_percent=0, name="SB", vector_group="YNd",
            vk0_percent=1e-4, vkr0_percent=0.0, mag0_percent=100, mag0_rx=0, si0_hv_partial=0.9)
        net.trafo["rn_ohm"] = 0.0
        net.trafo["xn_ohm"] = 0.0
        net.trafo.loc[net.trafo.name == "SB", "rn_ohm"] = 10.0 * 1000 / (math.sqrt(3) * IE)
    r = 0.11/math.tan(math.radians(28.1))
    for n,(a,c,l) in {"L1":("K2","K3",0.5),"L2":("K2","K4",1.2)}.items():
        pp.create_line_from_parameters(net, b[a], b[c], length_km=l, r_ohm_per_km=r, x_ohm_per_km=0.11,
            c_nf_per_km=0, max_i_ka=0.3, endtemp_degree=THETA.get(n, 90.0), name=n,
            r0_ohm_per_km=4*r, x0_ohm_per_km=4*0.11, c0_nf_per_km=0)
    if motor:
        mot = [("M1", "K3", 2.0/(0.88*0.96), 5.5)]
        if noe:
            mot.append(("M2", "K4", 0.8/(0.87*0.95), 6.0))
        for name, kn, Sn, lrc in mot:
            pp.create_sgen(net, b[kn], p_mw=0, sn_mva=Sn, k=lrc, lrc_pu=lrc, rx=0.1,
                           generator_type="async", name=name)
        net.sgen["k"] = 0.0
    return net, b

def pp_ik1(noe, fall):
    net, b = bau_null(noe, motor=(fall == "max"))
    sc.calc_sc(net, case=fall, fault="1ph", lv_tol_percent=10, branch_results=False)
    return {k: net.res_bus_sc.ikss_ka.at[v] for k, v in b.items()}

print()
print("Erdfehler Ik1 (einpolig)")
for datei, noe in (("industrie_10kV.json", False), ("industrie_10kV_noe.json", True)):
    erg1 = K.berechne(Netz.laden(os.path.join(sys.path[0], "beispielnetze", datei)))
    t = erg1.knoten
    THETA.clear(); THETA.update(erg1.theta_e)
    mx, mn = pp_ik1(noe, "max"), pp_ik1(noe, "min")
    print(f"  {datei}")
    for k in mx:
        a, d = t[k].Ik1_max_kA, t[k].Ik1_min_kA
        if a is None:
            print(f"    {k:4} nicht geerdet (pandapower {mx[k]:.3f} kA)")
            continue
        print(f"    {k:4} max {a:8.4f} pp {mx[k]:8.4f} {100*(a/mx[k]-1):6.2f}% | "
              f"min {d:8.4f} pp {mn[k]:8.4f} {100*(d/mn[k]-1):6.2f}%")
