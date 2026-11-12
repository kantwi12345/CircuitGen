"""
CircuitGen - 2.4 GHz LNA synthesis (noise/gain match), verified topologies.

  input : shunt C (source side) + series L (to base)   -> 50 ohm at source
  output: PI network (C1 collector shunt, L series, C2 load shunt) -> R_c

Device parameters are ASSUMED (BFP420-class NPN) and must be replaced with
real datasheet S-parameters / noise data before production use.
"""

import json
import math

from scipy.optimize import least_squares

F0 = 2.4e9
W = 2 * math.pi * F0
VT = 25.85e-3

IC = 1.5e-3
BETA = 120
C_PI = 1.5e-12
R_BB = 20.0
R_O = 30e3
F_MIN = 0.9
VBE = 0.85
VCC = 3.3
RS = 50.0
RL = 50.0

GM = IC / VT
R_PI = BETA / GM
Z_OPT_INT = 1.0 / (2 * GM) - 1j / (2 * W * C_PI)
Z_OPT_EXT = Z_OPT_INT + R_BB
F_MISMATCH = 4 * RS * Z_OPT_INT.real / abs(RS + Z_OPT_INT) ** 2
Z_PATH = R_BB + R_PI / (1 + 1j * W * C_PI * R_PI)

print("=== 1. Device (ASSUMED) ===")
print(f"  gm = {GM*1e3:.2f} mS | r_pi = {R_PI:.0f} ohm")
print(f"  Z_opt(int) = {Z_OPT_INT.real:.2f} {Z_OPT_INT.imag:+.2f}j ohm")
print(f"  base path  = {Z_PATH.real:.2f} {Z_PATH.imag:+.2f}j ohm")


def z_in_net(c_shunt, l_series):
    """source --[shunt C]-- node --[series L]-- base(path)."""
    z_c = 1.0 / (1j * W * c_shunt)
    return 1.0 / (1.0 / z_c + 1.0 / (1j * W * l_series + Z_PATH))


def res_input(x):
    c, l = x
    z = z_in_net(c, l)
    return [z.real - RS, z.imag]


best = None
for cg in (5e-12, 2e-12, 1e-12, 5e-13, 2e-13):
    for lg in (1e-9, 3e-9, 6e-9, 10e-9):
        s = least_squares(res_input, [cg, lg],
                          bounds=([1e-14, 1e-12], [1e-9, 1e-6]))
        err = max(abs(v) for v in s.fun)
        if best is None or err < best[0]:
            best = (err, s.x)
err_in, (C_in, L_in) = best
Z_in = z_in_net(C_in, L_in)
gamma_in = (Z_in - RS) / (Z_in + RS)

print("\n=== 2. Input network: 50 ohm match ===")
print(f"  C_shunt (source side) = {C_in*1e12:.3f} pF")
print(f"  L_series (to base)    = {L_in*1e9:.3f} nH")
print(f"  Z_in  = {Z_in.real:.3f} {Z_in.imag:+.3f}j ohm")
print(f"  |S11| = {abs(gamma_in):.4f} ({20*math.log10(abs(gamma_in)):.1f} dB)")
print(f"  residual = {err_in:.3g}")
print(f"  NF = {F_MIN + F_MISMATCH:.2f} dB (F_min {F_MIN} + {F_MISMATCH:.2f} mismatch)")


# noise-match variant: impedance toward source seen by the base = Z_opt(ext)
def res_nm(x):
    c, l = x
    z_c = 1.0 / (1j * W * c)
    z_toward_src = 1j * W * l + 1.0 / (1.0 / z_c + 1.0 / RS)
    return [z_toward_src.real - Z_OPT_EXT.real,
            z_toward_src.imag - Z_OPT_EXT.imag]


best_nm = None
for cg in (5e-12, 2e-12, 1e-12, 5e-13):
    for lg in (1e-9, 3e-9, 6e-9):
        s = least_squares(res_nm, [cg, lg],
                          bounds=([1e-14, 1e-12], [1e-9, 1e-6]))
        err = max(abs(v) for v in s.fun)
        if best_nm is None or err < best_nm[0]:
            best_nm = (err, s.x)
err_nm, (C_nm, L_nm) = best_nm
z_c = 1.0 / (1j * W * C_nm)
Z_toward_src = 1j * W * L_nm + 1.0 / (1.0 / z_c + 1.0 / RS)
Z_in_nm = 1.0 / (1.0 / z_c + 1.0 / (1j * W * L_nm + Z_PATH))
gamma_nm = (Z_in_nm - RS) / (Z_in_nm + RS)

print("\n=== 2b. Noise-match variant ===")
print(f"  C_shunt = {C_nm*1e12:.3f} pF | L_series = {L_nm*1e9:.3f} nH")
print(f"  toward source = {Z_toward_src.real:.2f} {Z_toward_src.imag:+.2f}j ohm")
print(f"  |S11| at source = {abs(gamma_nm):.4f} "
      f"({20*math.log10(abs(gamma_nm)):.1f} dB)")
print(f"  NF = {F_MIN:.2f} dB | residual = {err_nm:.3g}")

# ---------------- gain match ---------------------------------------
AV_DB = 15.0
R_C = (10 ** (AV_DB / 20.0)) / GM
print("\n=== 3. Gain match ===")
print(f"  Av = {AV_DB} dB -> R_c = Av/gm = {R_C:.1f} ohm")


def out_net(c1, l3, c2):
    z_c1 = 1.0 / (1j * W * c1)
    z_c2 = 1.0 / (1j * W * c2)
    z_load = 1.0 / (1.0 / RL + 1.0 / z_c2)
    return 1.0 / (1.0 / z_c1 + 1.0 / (1j * W * l3 + z_load))


def res_out(x):
    c1, l3 = x
    z = out_net(c1, l3, 1.0e-12)
    return [z.real - R_C, z.imag]


best_out = None
for c2v in (1.0e-12, 2.0e-12, 5.0e-12):
    for c1g in (5e-12, 2e-12, 1e-12, 5e-13):
        for lg in (1e-9, 3e-9, 6e-9):
            s = least_squares(res_out, [c1g, lg],
                              bounds=([1e-13, 1e-12], [1e-9, 1e-6]))
            z = out_net(s.x[0], s.x[1], c2v)
            err = max(abs(v) for v in [z.real - R_C, z.imag])
            if best_out is None or err < best_out[0]:
                best_out = (err, s.x[0], s.x[1], c2v)

err_out, C1_out, L3_out, C2_out = best_out
Z_at_coll = out_net(C1_out, L3_out, C2_out)
R_eff = 1.0 / (1.0 / Z_at_coll + 1.0 / R_O)
AV_REAL = GM * abs(R_eff)

print("\n=== 4. Output PI network ===")
print(f"  C1 (collector shunt) = {C1_out*1e12:.3f} pF")
print(f"  L3 (series)          = {L3_out*1e9:.3f} nH")
print(f"  C2 (load shunt)      = {C2_out*1e12:.3f} pF")
print(f"  Z at collector = {Z_at_coll.real:.2f} {Z_at_coll.imag:+.2f}j ohm")
print(f"  R_eff (with r_o) = {abs(R_eff):.1f} ohm")
print(f"  Av = gm*R_eff = {AV_REAL:.2f} ({20*math.log10(AV_REAL):.2f} dB)")
print(f"  residual = {err_out:.3g}")

# ---------------- bias ---------------------------------------------
VE = 0.50
RE = VE / IC
V_B = VBE + VE
I_DIV = 10 * IC / BETA
R_B1 = (VCC - V_B) / I_DIV
R_B2 = V_B / I_DIV
RTH = R_B1 * R_B2 / (R_B1 + R_B2)
LOAD = 1.0 / (1.0 + RTH / (R_PI + R_BB))
print("\n=== 5. Bias (ASSUMED) ===")
print(f"  R_E  = {RE:.0f} ohm -> E24 330")
print(f"  R_B1 = {R_B1:.0f} ohm -> E24 16k (VCC->B)")
print(f"  R_B2 = {R_B2:.0f} ohm -> E24 11k (B->GND)")
print(f"  Rth = {RTH:.0f} ohm, bias loading = {LOAD:.2f} (re-check in SPICE)")

res = {
    "f0_ghz": 2.4, "gm_ms": GM * 1e3, "r_pi": R_PI,
    "z_opt_real": Z_OPT_INT.real, "z_opt_imag": Z_OPT_INT.imag,
    "c_in_pf": C_in * 1e12, "l_in_nh": L_in * 1e9,
    "s11_db": 20 * math.log10(abs(gamma_in)), "nf_db": F_MIN + F_MISMATCH,
    "c_nm_pf": C_nm * 1e12, "l_nm_nh": L_nm * 1e9,
    "s11_nm_db": 20 * math.log10(abs(gamma_nm)), "nf_min_db": F_MIN,
    "av_db": 20 * math.log10(AV_REAL), "r_c": R_C,
    "c1_out_pf": C1_out * 1e12, "l3_out_nh": L3_out * 1e9,
    "c2_out_pf": C2_out * 1e12,
    "re": RE, "rb1": R_B1, "rb2": R_B2, "bias_loading": LOAD,
}
with open("lna_results.json", "w") as fh:
    json.dump(res, fh, indent=2)
print("\nwrote lna_results.json")
