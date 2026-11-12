import math

import numpy as np

from tools.netlist_sim import Circuit, parse_netlist, simulate_ac

print("=== TEST 1: resistive divider + VCVS x2 ===")
nl = """
V1 in 0 AC 1
R1 in out 1k
R2 out 0 1k
E1 o2 0 out 0 2
"""
sim = simulate_ac(nl, [1e9], port_node="out", reference_node="in",
                  output_node="o2")
print("  gain (expect 0 dB):",
      round(20 * math.log10(abs(sim["gain"][0])), 3), "dB")

print("\n=== TEST 2: series RLC at resonance ===")
nl = """
V1 in 0 AC 1
R1 in a 50
L1 a b 10n
C1 b 0 100p
RL b 0 50
"""
f0 = 1.0 / (2 * math.pi * math.sqrt(10e-9 * 100e-12))
sim = simulate_ac(nl, [f0], port_node="a", reference_node="in",
                  output_node="b", source_resistance=50, load_resistance=50)
print(f"  f0 = {f0/1e6:.2f} MHz")
print("  gain at f0 (expect ~0 dB):",
      round(20 * math.log10(abs(sim["gain"][0])), 3), "dB")
print("  |S11| at f0 (expect very low):",
      round(20 * math.log10(abs(sim["s11"][0])), 2), "dB")

print("\n=== TEST 3: RC low-pass, cutoff check ===")
nl = """
V1 in 0 AC 1
R1 in out 1k
C1 out 0 159.1549n
"""
fc = 1.0 / (2 * math.pi * 1e3 * 159.1549e-9)
sim = simulate_ac(nl, [fc], port_node="out", reference_node="in",
                  output_node="out")
print(f"  fc = {fc/1e6:.2f} MHz")
print("  |v_out/v_in| at fc (expect -3.01 dB):",
      round(20 * math.log10(abs(sim["gain"][0])), 3), "dB")

print("\n=== TEST 4: BJT small-signal gain sanity ===")
nl = """
VCC vcc 0 DC 3.3
VIN in 0 AC 1
RB  bint in 20
RPI bint ne 2068
CPI bint ne 1.5p
GM  nc ne bint ne 0.058
RO  nc ne 30k
RE  ne 0 330
CE  ne 0 10u
RL  nc 0 50
"""
sim = simulate_ac(nl, [1e8], port_node="bint", reference_node="in",
                  output_node="nc", source_resistance=50, load_resistance=50)
print("  gain at 100 MHz (expect ~gm*R_c = 9.2 dB minus divider):",
      round(20 * math.log10(abs(sim["gain"][0])), 3), "dB")
