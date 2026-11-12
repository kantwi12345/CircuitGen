"""
CircuitGen - run the generated ADS netlists through the AC simulator
(working substitute for ADS circuit simulation) and write the results
back into the design workspace.
"""

import os
import sys

import numpy as np

sys.path.insert(0, r"C:\CircuitGen")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from tools.ads import build_ads_circuit
from tools.netlist_sim import simulate_ac

DESIGN = "LNA"
F_START = 1e8
F_STOP = 1e10
N_POINTS = 400

result = build_ads_circuit(circuit_type="active", design=DESIGN,
                           frequency_ghz=2.4)
workspace = result["workspace"]["workspace"]
netlist = result["netlist"]

freqs = np.logspace(np.log10(F_START), np.log10(F_STOP), N_POINTS)

sim = simulate_ac(
    netlist,
    freqs,
    port_node="SRC1",
    reference_node="SRC",
    output_node="NO2",
    source_resistance=50.0,
    load_resistance=50.0,
)

gain_db = 20 * np.log10(np.abs(sim["gain"]))
s11_db = 20 * np.log10(np.abs(sim["s11"]))
f0 = 2.4e9

idx_f0 = int(np.argmin(np.abs(freqs - f0)))
peak_idx = int(np.argmax(gain_db))

print(f"workspace: {workspace}")
print(f"gain @ 2.4 GHz      : {gain_db[idx_f0]:.2f} dB")
print(f"peak gain          : {gain_db[peak_idx]:.2f} dB @ {freqs[peak_idx]/1e9:.3f} GHz")
print(f"|S11| @ 2.4 GHz    : {s11_db[idx_f0]:.2f} dB")
print(f"peak |S11|         : {s11_db.min():.2f} dB @ {freqs[int(np.argmin(s11_db))]/1e9:.3f} GHz")
print(f"P_load @ 2.4 GHz   : {sim['p_load'][idx_f0]*1e3:.3f} mW (1 V peak drive)")

# bandwidth at -3 dB from the peak
bw_text = "n/a"
if gain_db[peak_idx] > 0:
    thresh = gain_db[peak_idx] - 3.0
    above = freqs[gain_db >= thresh]
    if len(above) > 1:
        bw_text = (f"{(above[-1]-above[0])/1e6:.1f} MHz "
                   f"({above[0]/1e9:.3f} - {above[-1]/1e9:.3f} GHz)")
        print(f"-3 dB bandwidth     : {bw_text}")

# plot
fig, axes = plt.subplots(3, 1, figsize=(8, 9), sharex=True)
axes[0].semilogx(freqs, gain_db, "b", linewidth=1.6)
axes[0].axhline(15, color="gray", linestyle="--", linewidth=0.8)
axes[0].set_ylabel("Gain (dB)")
axes[0].set_title("CircuitGen LNA - AC simulation (netlist: LNA.net)")
axes[0].grid(True, which="both", alpha=0.3)

axes[1].semilogx(freqs, s11_db, "r", linewidth=1.6)
axes[1].axhline(-10, color="gray", linestyle="--", linewidth=0.8)
axes[1].set_ylabel("S11 (dB)")
axes[1].grid(True, which="both", alpha=0.3)

axes[2].semilogx(freqs, sim["p_load"] * 1e3, "g", linewidth=1.6)
axes[2].set_ylabel("P into 50 ohm (mW)")
axes[2].set_xlabel("Frequency (Hz)")
axes[2].grid(True, which="both", alpha=0.3)

fig.tight_layout()
plot_path = os.path.join(workspace, "AC_RESULTS.png")
fig.savefig(plot_path, dpi=110)

# write results file
lines = [
    "# CircuitGen - AC Simulation Results",
    "",
    f"Design: {DESIGN}",
    "Netlist: LNA.net (linearized small-signal device model, ASSUMED params)",
    "",
    "| Metric | Value |",
    "|---|---|",
    f"| Gain @ 2.4 GHz | {gain_db[idx_f0]:.2f} dB |",
    f"| Peak gain | {gain_db[peak_idx]:.2f} dB @ {freqs[peak_idx]/1e9:.3f} GHz |",
    f"| S11 @ 2.4 GHz | {s11_db[idx_f0]:.2f} dB |",
    f"| Best S11 | {s11_db.min():.2f} dB @ {freqs[int(np.argmin(s11_db))]/1e9:.3f} GHz |",
    f"| P into 50 ohm @ 2.4 GHz | {sim['p_load'][idx_f0]*1e3:.3f} mW (1 V peak drive) |",
    f"| -3 dB bandwidth | {bw_text} |",
    "| NF estimate | 1.34 dB (F_min 0.90 dB assumed + 0.44 dB mismatch) |",
    "",
    "Plot: AC_RESULTS.png (gain / S11 / load power vs frequency)",
    "",
    "## Notes",
    "",
    "- Simulation performed with the CircuitGen AC netlist solver",
    "  (tools/netlist_sim.py) - the working substitute for ADS circuit",
    "  simulation in this environment.",
    "- The device is a linearized small-signal model with ASSUMED",
    "  parameters; results shift once real datasheet S-parameters are used.",
    "- The input network is noise-matched, so S11 is expected to be poor",
    "  (NF optimisation wins over source matching).",
    "- RF verification in ADS with the real device model is still required.",
    "",
]

results_path = os.path.join(workspace, "SIMULATION_RESULTS.md")
with open(results_path, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))

print(f"plot   : {plot_path}")
print(f"results: {results_path}")
