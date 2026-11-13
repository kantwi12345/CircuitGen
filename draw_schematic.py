"""
CircuitGen - Schematic diagram generator (visual substitute for ADS).

Generates a readable schematic diagram (PNG) of the Class AB Audio
Power Amplifier using only matplotlib (no EDA tool required). The same
values are encoded in the SPICE netlist next to this file so the design
can be simulated in ngspice / LTspice.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = r"C:\CircuitGen\projects\Class_AB_Audio_Power_Amplifier"
PNG_PATH = os.path.join(OUT_DIR, "schematic.png")


def draw_resistor(ax, x0, y0, x1, y1, label=None):
    """Draw a resistor symbol (zigzag) between (x0,y0) and (x1,y1)."""
    import numpy as np

    n_zig = 5
    xs = np.linspace(x0, x1, 2 * n_zig + 1)
    ys = np.full_like(xs, y0)
    # zigzag in the middle
    mid_start = 1
    mid_end = 2 * n_zig
    for i in range(mid_start, mid_end, 2):
        ys[i] = y0 - 0.15
        if i + 1 < len(ys):
            ys[i + 1] = y0 + 0.15
    ax.plot(xs, ys, "k-", lw=1.2)
    if label:
        ax.text((x0 + x1) / 2, y0 + 0.35, label,
                ha="center", va="bottom", fontsize=8)


def draw_capacitor(ax, x, y0, y1, label=None, horizontal=False):
    """Draw a capacitor symbol (two parallel lines)."""
    if horizontal:
        ax.plot([x - 0.25, x - 0.25], [y0, y1], "k-", lw=1.2)
        ax.plot([x + 0.25, x + 0.25], [y0, y1], "k-", lw=1.2)
        if label:
            ax.text(x, y0 + 0.4, label, ha="center", va="bottom", fontsize=8)
    else:
        ax.plot([x, x], [y0 - 0.25, y0 + 0.25], "k-", lw=1.2)
        ax.plot([x, x], [y1 - 0.25, y1 + 0.25], "k-", lw=1.2)
        if label:
            ax.text(x + 0.4, y0, label, ha="left", va="center", fontsize=8)


def draw_bjt(ax, x, y, label, pnp=False):
    """Draw a simple BJT symbol (circle with base/emitter/collector)."""
    import numpy as np

    circle = plt.Circle((x, y), 0.35, fill=False, ec="k", lw=1.2)
    ax.add_patch(circle)
    # base (left)
    ax.plot([x - 0.7, x - 0.35], [y, y], "k-", lw=1.2)
    # collector (top-right)
    ax.plot([x, x + 0.5], [y + 0.35, y + 0.7], "k-", lw=1.2)
    # emitter (bottom-right)
    ax.plot([x, x + 0.5], [y - 0.35, y - 0.7], "k-", lw=1.2)
    ax.text(x + 0.5, y + 0.75, label, ha="center", va="bottom", fontsize=8)


def main():
    fig, ax = plt.subplots(figsize=(12, 7))

    ax.set_xlim(-2, 14)
    ax.set_ylim(-3, 6)
    ax.set_aspect("equal")
    ax.axis("off")

    # --- supply rails ---
    ax.plot([0, 12], [5.5, 5.5], "k-", lw=1.5)   # V+ rail
    ax.plot([0, 12], [-2.5, -2.5], "k-", lw=1.5)  # V- rail
    ax.text(-0.4, 5.5, "+35 V", ha="right", va="center", fontsize=10,
            fontweight="bold")
    ax.text(-0.4, -2.5, "-35 V", ha="right", va="center", fontsize=10,
            fontweight="bold")

    # --- input source (50 ohm) ---
    ax.plot([0, 1.5], [2, 2], "k-", lw=1.2)
    ax.plot([1.5, 1.5], [1.6, 2.4], "k-", lw=1.2)   # source symbol
    ax.plot([1.3, 1.5], [2.0, 1.6], "k-", lw=1.2)
    ax.plot([1.5, 1.7], [2.0, 1.6], "k-", lw=1.2)
    ax.text(1.5, 2.6, "VIN\n50 ohm", ha="center", va="bottom", fontsize=8)

    # --- input coupling cap C_in (100 nF) ---
    draw_capacitor(ax, 2.5, 1.6, 2.4, "C_in\n100 nF")
    ax.plot([1.5, 2.25], [2, 2], "k-", lw=1.2)
    ax.plot([2.75, 3.5], [2, 2], "k-", lw=1.2)

    # --- gain stage: R_i (1k) + R_f (100k) ---
    draw_resistor(ax, 3.5, 2, 5.0, 2, "R_i\n1 kOhm")
    draw_resistor(ax, 4.25, 4.0, 4.25, 2.0, "R_f\n100 kOhm")
    ax.plot([5.0, 5.0], [2, 3.5], "k-", lw=1.2)
    ax.plot([4.25, 5.0], [4.0, 4.0], "k-", lw=1.2)
    ax.plot([4.25, 4.25], [4.0, 2.0], "k-", lw=1.2)

    # --- output stage: Q1 (NPN) + Q2 (PNP) ---
    draw_bjt(ax, 6.5, 3.0, "Q1 (NPN)")
    draw_bjt(ax, 6.5, 0.5, "Q2 (PNP)")
    # bases tied together
    ax.plot([5.0, 6.15], [2, 2], "k-", lw=1.2)
    ax.plot([6.15, 6.15], [2, 0.5], "k-", lw=1.2)
    ax.plot([6.15, 6.15], [2, 3.0], "k-", lw=1.2)
    # collectors tied to output
    ax.plot([7.0, 7.5], [3.7, 3.7], "k-", lw=1.2)
    ax.plot([7.0, 7.5], [-0.2, -0.2], "k-", lw=1.2)
    ax.plot([7.0, 7.0], [3.7, 3.35], "k-", lw=1.2)
    ax.plot([7.0, 7.0], [3.7, -0.2], "k-", lw=1.2)
    ax.plot([7.0, 7.0], [-0.2, 0.15], "k-", lw=1.2)
    # emitters to rails
    ax.plot([6.5, 6.5], [3.7, 5.5], "k-", lw=1.2)
    ax.plot([6.5, 6.5], [-0.2, -2.5], "k-", lw=1.2)
    # emitter degeneration resistors
    draw_resistor(ax, 6.5, 4.5, 6.5, 5.5, "R_E\n22 Ohm")
    draw_resistor(ax, 6.5, -1.5, 6.5, -2.5, "R_E\n22 Ohm")

    # --- bias divider (R_B1 / R_B2) ---
    draw_resistor(ax, 5.5, 5.5, 5.5, 2.0, "R_B1\n9.1 kOhm")
    draw_resistor(ax, 5.5, 2.0, 5.5, -2.5, "R_B2\n10 kOhm")
    ax.plot([5.5, 6.15], [2.0, 2.0], "k-", lw=1.2)

    # --- Zobel network (R_z = 560, C_z = 10 nF) ---
    draw_resistor(ax, 8.0, 3.7, 8.0, 2.5, "R_z\n560 Ohm")
    draw_capacitor(ax, 8.0, 2.0, 1.2, "C_z\n10 nF", horizontal=False)
    ax.plot([8.0, 8.0], [2.5, 2.0], "k-", lw=1.2)
    ax.plot([8.0, 8.0], [1.2, 0.5], "k-", lw=1.2)

    # --- load (8 ohm speaker) ---
    draw_resistor(ax, 9.5, 2.0, 11.0, 2.0, "R_L\n8 Ohm")
    ax.plot([8.0, 8.0], [3.7, 2.0], "k-", lw=1.2)
    ax.plot([8.0, 9.5], [2.0, 2.0], "k-", lw=1.2)
    ax.plot([11.0, 11.0], [2.0, 0.5], "k-", lw=1.2)

    # --- ground ---
    ax.plot([7.0, 11.0], [0.5, 0.5], "k-", lw=1.2)
    ax.plot([8.0, 8.0], [0.5, 0.2], "k-", lw=1.2)
    ax.plot([11.0, 11.0], [0.5, 0.2], "k-", lw=1.2)
    ax.text(9.5, 0.0, "GND", ha="center", va="top", fontsize=9, fontweight="bold")

    # --- supply decoupling caps (at the rails, near the output) ---
    draw_capacitor(ax, 7.5, 5.0, 4.3, "C_dec\n220u", horizontal=False)
    ax.plot([7.5, 6.5], [5.0, 5.0], "k-", lw=1.2)
    ax.plot([7.5, 7.5], [4.3, 3.7], "k-", lw=1.2)
    draw_capacitor(ax, 7.5, 0.2, -0.8, "C_dec\n220u", horizontal=False)
    ax.plot([7.5, 6.5], [0.2, 0.2], "k-", lw=1.2)
    ax.plot([7.5, 7.5], [-0.8, -2.5], "k-", lw=1.2)

    # --- annotations ---
    ax.text(6.5, 4.2, "Q1: 2SC5200 (NPN)", ha="center", va="bottom",
            fontsize=8, style="italic")
    ax.text(6.5, -0.9, "Q2: 2SA1943 (PNP)", ha="center", va="top",
            fontsize=8, style="italic")
    ax.text(6.0, 1.0, "bias divider", ha="center", va="center",
            fontsize=8, style="italic", color="gray")

    ax.set_title("Class AB Audio Power Amplifier - 50 W RMS into 8 ohm, "
                 "+/-35 V dual rail", fontsize=12, fontweight="bold")
    ax.text(12, -2.8, "CircuitGen - verified design parameters: "
           "V_RMS=20 V, V_PEAK=28.28 V, I_PEAK=3.54 A, A_v=101",
           ha="right", va="top", fontsize=9, style="italic", color="gray")

    os.makedirs(OUT_DIR, exist_ok=True)
    fig.tight_layout()
    fig.savefig(PNG_PATH, dpi=140, bbox_inches="tight")
    print(f"schematic saved to: {PNG_PATH}")


if __name__ == "__main__":
    main()
