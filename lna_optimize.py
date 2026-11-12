"""
CircuitGen - LNA output/input network optimisation using the AC netlist
simulator (working substitute for ADS optimisation).

Optimises the output PI network for:
    gain @ f0 = 15 dB   and   |S22| <= -30 dB
then the input network for the best 50 ohm source match while reporting
the resulting noise-figure trade-off.
"""

import math
import sys

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, r"C:\CircuitGen")

from tools.netlist_sim import simulate_ac

F0 = 2.4e9
TARGET_GAIN_DB = 15.0
F_MIN_DB = 0.9          # assumed device F_min
Z_OPT = 8.62 - 22.10j   # assumed optimum source impedance (internal base)

TEMPLATE = """
VTH   SRC 0 DC 0 AC 1
VCC   VCC 0 DC 3.3
RSRC  SRC SRC1 50
CPAD  SRC1 0 {c_pad}p
LSIG  SRC1 NI {l_sig}n
RB    BINT NI 20
RPI   BINT NE 2068
CPI   BINT NE 1.5p
GM    NC NE BINT NE 0.058
RO    NC NE 30k
RE    NE 0 330
CE    NE 0 10u
RB1   NI VCC 16k
RB2   NI 0 11k
CO1   NC 0 {c_o1}p
LOUT  NC NO2 {l_out}n
CO2   NO2 0 {c_o2}p
RL    NO2 0 50
CDP   VCC 0 100n
CHP   VCC 0 0.1u
"""


def make_netlist(c_pad, l_sig, c_o1, l_out, c_o2):
    return TEMPLATE.format(
        c_pad=c_pad, l_sig=l_sig, c_o1=c_o1, l_out=l_out, c_o2=c_o2
    )


def eval_params(params):
    c_pad, l_sig, c_o1, l_out, c_o2 = params
    netlist = make_netlist(c_pad, l_sig, c_o1, l_out, c_o2)
    freqs = np.array([F0 * 0.98, F0, F0 * 1.02])

    sim = simulate_ac(netlist, freqs, port_node="SRC1", reference_node="SRC",
                      output_node="NO2", source_resistance=50.0,
                      load_resistance=50.0)
    gain_db = 20 * np.log10(np.abs(sim["gain"]))
    s11_db = 20 * np.log10(np.abs(sim["s11"]))

    # output-side match: impedance looking back from the load node
    from tools.netlist_sim import Circuit, parse_netlist
    circuit = Circuit(parse_netlist(netlist))
    omega = 2 * math.pi * F0
    z_out = circuit.impedance_at("NO2", omega)
    s22 = (z_out - 50.0) / (z_out + 50.0)
    s22_db = 20 * math.log10(abs(s22))

    return {
        "gain_db": gain_db[1],
        "gain_low": gain_db[0],
        "gain_high": gain_db[2],
        "s11_db": s11_db[1],
        "s22_db": s22_db,
        "z_out": z_out,
    }


def residual_output(x):
    """x = [c_o1, l_out, c_o2] (pF, nH, pF)."""

    c_o1, l_out, c_o2 = x
    result = eval_params([1.15, 0.18, c_o1, l_out, c_o2])
    return [
        result["gain_db"] - TARGET_GAIN_DB,
        result["s22_db"] + 30.0,
    ]


print("=== Optimising output PI network (gain 15 dB, |S22| <= -30 dB) ===")

best = None
for c1g in (0.5, 1.0, 2.0, 5.0):
    for lg in (1.0, 3.0, 6.0, 10.0):
        for c2g in (0.5, 1.0, 2.0):
            sol = least_squares(
                residual_output, [c1g, lg, c2g],
                bounds=([1e-3, 0.1, 1e-3], [50.0, 50.0, 50.0]),
                max_nfev=400,
            )
            err = float(np.max(np.abs(sol.fun)))
            if best is None or err < best[0]:
                best = (err, sol.x)

err, (c_o1, l_out, c_o2) = best
res = eval_params([1.15, 0.18, c_o1, l_out, c_o2])
print(f"  C_o1 = {c_o1:.3f} pF | L_out = {l_out:.3f} nH | C_o2 = {c_o2:.3f} pF")
print(f"  gain @ 2.4 GHz = {res['gain_db']:.2f} dB")
print(f"  S22 @ 2.4 GHz = {res['s22_db']:.2f} dB")
print(f"  residual = {err:.4g}")

# ---- input network: maximise source match (S11) ---------------------
print("\n=== Optimising input network for 50 ohm source match ===")


def residual_input(x):
    c_pad, l_sig = x
    result = eval_params([c_pad, l_sig, c_o1, l_out, c_o2])
    return [result["s11_db"] + 20.0]


best_in = None
for cg in (0.5, 1.0, 2.0, 5.0):
    for lg in (0.1, 0.5, 1.0, 3.0):
        sol = least_squares(residual_input, [cg, lg],
                            bounds=([1e-3, 1e-3], [50.0, 50.0]),
                            max_nfev=400)
        err = float(np.max(np.abs(sol.fun)))
        if best_in is None or err < best_in[0]:
            best_in = (err, sol.x)

err_in, (c_pad, l_sig) = best_in
res_in = eval_params([c_pad, l_sig, c_o1, l_out, c_o2])
print(f"  C_pad = {c_pad:.3f} pF | L_sig = {l_sig:.3f} nH")
print(f"  S11 @ 2.4 GHz = {res_in['s11_db']:.2f} dB")
print(f"  gain @ 2.4 GHz = {res_in['gain_db']:.2f} dB")
print(f"  residual = {err_in:.4g}")

# noise figure for the matched case (source impedance seen by device)
z_seen = res_in["z_out"]
nf_mismatch = 4 * 50 * Z_OPT.real / abs(50 + Z_OPT) ** 2
print(f"\n  NF estimate (50 ohm drive) = {F_MIN_DB + nf_mismatch:.2f} dB")

print("\n=== Final parameter set ===")
print(f"  C_pad  = {c_pad:.3f} pF")
print(f"  L_sig  = {l_sig:.3f} nH")
print(f"  C_o1   = {c_o1:.3f} pF")
print(f"  L_out  = {l_out:.3f} nH")
print(f"  C_o2   = {c_o2:.3f} pF")
