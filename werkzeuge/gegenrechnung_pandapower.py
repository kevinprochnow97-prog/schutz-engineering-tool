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
Hinweise zum Nachbau: Motor als Asynchronmaschine nur ueber lrc_pu (k = 0, sonst rechnet pandapower
zusaetzlich eine Stromquelle), Leitung mit endtemp_degree = 90 fuer Ik min, lv_tol_percent = 10.
"""
import sys, warnings, math, os
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "."))
import pandapower as pp, pandapower.shortcircuit as sc
import netz_kurzschluss as K
from netz_modell import Netz

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
            c_nf_per_km=0, max_i_ka=0.3, endtemp_degree=90.0, name=n)
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
t = K.berechne(n).knoten
mx = pp_ik(False, "max", "3ph"); mn = pp_ik(False, "min", "2ph")
try: mm = pp_ik(True, "max", "3ph")
except Exception as e: mm = None; print("Motor:", e)
print(f"{'Knoten':6} {'Tool max':>9} {'pp max':>9} {'Abw':>7} | {'Tool min':>9} {'pp min':>9} {'Abw':>7} | {'Tool mM':>8} {'pp mM':>8} {'Abw':>7}")
for k in mx:
    a, c = t[k].Ik_max_kA, mx[k]; d, e = t[k].Ik_min_kA, mn[k]
    s = f"{k:6} {a:9.3f} {c:9.3f} {100*(a/c-1):6.2f}% | {d:9.3f} {e:9.3f} {100*(d/e-1):6.2f}%"
    if mm: s += f" | {t[k].Ik_max_mit_Motor_kA:8.3f} {mm[k]:8.3f} {100*(t[k].Ik_max_mit_Motor_kA/mm[k]-1):6.2f}%"
    print(s)
