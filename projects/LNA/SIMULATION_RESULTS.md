# CircuitGen - AC Simulation Results

Design: LNA
Netlist: LNA.net (linearized small-signal device model, ASSUMED params)

| Metric | Value |
|---|---|
| Gain @ 2.4 GHz | 16.11 dB |
| Peak gain | 16.11 dB @ 2.390 GHz |
| S11 @ 2.4 GHz | -20.20 dB |
| Best S11 | -27.79 dB @ 0.100 GHz |
| P into 50 ohm @ 2.4 GHz | 408.101 mW (1 V peak drive) |
| -3 dB bandwidth | 82.3 MHz (2.336 - 2.418 GHz) |
| NF estimate | 1.34 dB (F_min 0.90 dB assumed + 0.44 dB mismatch) |

Plot: AC_RESULTS.png (gain / S11 / load power vs frequency)

## Notes

- Simulation performed with the CircuitGen AC netlist solver
  (tools/netlist_sim.py) - the working substitute for ADS circuit
  simulation in this environment.
- The device is a linearized small-signal model with ASSUMED
  parameters; results shift once real datasheet S-parameters are used.
- The input network is noise-matched, so S11 is expected to be poor
  (NF optimisation wins over source matching).
- RF verification in ADS with the real device model is still required.
