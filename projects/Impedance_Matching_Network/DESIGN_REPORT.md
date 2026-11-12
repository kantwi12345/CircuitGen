# CircuitGen - Impedance Matching Network Report

## 1. Targets

- Frequency: 2.4 GHz
- Source: 50 ohm
- Load: 36.5 ohm (quarter-wave monopole over ground - ASSUMED)

## 2. Topology and solution

```
Zc = 22.20 ohm  -> C = 3.0 pF   (series, load side)
Zl = 82.22 ohm  -> L = 5.5 nH   (shunt, source side)
```

## 3. Verification (computed)

```
Zin  = 49.89 - j0.21 ohm
|S11| = 0.0024  (-52.6 dB)
```

**Requires Bench Verification:** re-run with the simulated
antenna port impedance from HFSS before production use.
