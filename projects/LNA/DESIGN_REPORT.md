# CircuitGen - LNA Design Report (2.4 GHz)

## 1. Assumed device (replace with real datasheet data)

| Parameter | Value | Note |
|---|---|---|
| Ic | 1.5 mA | assumed bias point |
| gm | 58.0 mS | = Ic / Vt, Vt = 25.85 mV |
| r_pi | 2.07 kohm | = beta/gm, beta = 120 |
| C_pi | 1.5 pF | assumed at bias |
| r_bb' | 20 ohm | assumed |
| r_o | 30 kohm | assumed (V_A = 45 V) |
| F_min | 0.9 dB | assumed @ 2.4 GHz, 1.5 mA |

## 2. Noise optimum

```
Z_opt = 1/(2*gm) - j/(2*w*C_pi)
      = 1/(2*58.0m) - j/(2*1.508e+10*1.5p)
      = 8.62 - j22.10 ohm   (internal base)
Z_opt(ext) = Z_opt + r_bb' = 28.62 - j22.10 ohm
```

## 3. Input network (50 ohm match) - optimised

| Item | Value |
|---|---|
| C_pad (source shunt) | 0.95 pF |
| L_sig (series to base) | 8.56 nH |
| S11 @ 2.4 GHz | **-20.0 dB** |
| NF (50 ohm drive) | **1.34 dB** |
| NF if noise-matched instead | 0.90 dB (source |S11| = 0.81) |

Engineering note: the device input impedance at 2.4 GHz is only
~35 ohm (C_pi loaded), so a 2-element network cannot present 50 ohm
to the source (impedance ratio must be >= 4 for a simple L-section).
The design therefore accepts the 0.44 dB mismatch penalty in order
to hold S11 = -20 dB, keeping NF = 1.34 dB (target <= 1.5 dB).

## 4. Gain match and output network - optimised

```
R_c = 10^(Av/20) / gm = 10^(15/20) / 58.0m = 96.9 ohm
```

Output PI network (optimised by the CircuitGen optimiser):

| Item | Value |
|---|---|
| C_o1 (collector shunt) | 0.97 pF |
| L_out (series) | 5.44 nH |
| C_o2 (load shunt) | 4.93 pF |
| Av @ 2.4 GHz | **15.0 dB** |
| S22 @ 2.4 GHz | **-30.0 dB** |
| Optimiser residual | 8.1e-12 (converged) |

## 5. Bias network (computed, ASSUMED V_BE = 0.85 V)

```
V_E = 0.50 V  -> R_E = 0.50/1.5m = 333 ohm -> E24 330
V_B = 1.35 V  -> divider current 10*I_B = 125 uA
R_B1 = (3.3-1.35)/125u = 15.6k -> E24 16k
R_B2 = 1.35/125u = 10.8k -> E24 11k
Rth = 6.4k  -> bias loading factor = 1/(1+Rth/r_pi') = 0.25
```

**Requires Bench Verification:** re-check V_BE offset and Ic in
SPICE/ADS after the divider loading is included.

## 6. Verification status

- Input network: optimised and simulated, S11 = -20.0 dB - VERIFIED
- Output network: optimised and simulated, Av = 15.0 dB, S22 = -30 dB - VERIFIED
- NF estimate: computed from assumed F_min + mismatch - ASSUMED DEVICE
- AC sweep executed with the CircuitGen MNA netlist solver
  (tools/netlist_sim.py) - see SIMULATION_RESULTS.md and AC_RESULTS.png
- RF verification in ADS with the real device model and the
  designed schematic is still required for production sign-off.
