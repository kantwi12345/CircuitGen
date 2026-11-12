# CircuitGen - Design Report

- Design: PA
- Family: active
- Frequency: 2.4 GHz

## Verified design math

```
P_RMS = 50 W, R_L = 8 ohm
V_RMS  = sqrt(P*R_L) = sqrt(50*8) = 20 V
V_PEAK = 20*sqrt(2) = 28.28 V
I_PEAK = 28.28/8 = 3.54 A
I_RMS  = 3.54/sqrt(2) = 2.50 A
A_v    = 1 + R_f/R_i = 1 + 100k/1k = 101
V_in   = V_RMS/A_v = 0.198 V RMS
```

## Verification status

- Design math: computed and checked
- Component values: E24 standard, calculated
- THD, bias set points and device models: REQUIRES SPICE/ADS
  ITERATION and bench verification
