"""Throwaway: end-to-end test of the simulate_antenna entry point."""

import json
import time

from tools.hfss_com import simulate_antenna

start = time.time()

result = simulate_antenna(
    antenna_type="monopole",
    frequency_ghz=2.4,
    span_ghz=0.4,
    sweep_count=21,
    project_path=r"C:\CircuitGen\tmp_saved\hfss_monopole_api.aedt",
)

print("elapsed %.1f s" % (time.time() - start))

simulation = result["simulation"]
print("setup:", simulation["setup"])
print("sweep:", simulation["sweep"])
print("solved:", simulation["solved"])
print("port:", simulation["port"])
print("summary:", json.dumps(simulation["summary"], indent=2))
print("resonance_ghz:", (simulation["resonance_hz"] or 0) / 1e9)
print("antenna parameters:", simulation["antenna_parameters"])

raw = simulation.get("s_parameters", {})
for label, data in raw.items():
    print(f"\n{label}: {data.get('traces')}")
