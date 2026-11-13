"""
CircuitGen - LNA schematic diagram generator (visual substitute for ADS).

Generates a readable schematic diagram (PNG) of the 2.4 GHz LNA using
only matplotlib (no EDA tool required). Values come from the verified
synthesis in lna_synthesis.py / lna_optimize.py.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = r"C:\CircuitGen\projects\LNA"
PNG_PATH = os.path.join(OUT_DIR, "schematic.png")


def draw_resistor(ax, x0, y0, x1, y1, label=None):
    import numpy as np

    n_zig = 5
    xs = np.linspace(x0, x1, 2 * n_zig + 1)
    ys = np.full_like(xs, y0)
    for i in range(1, 2 * n_zig, 2):
        ys[i] = y0 - 0.15
        if i + 1 < len(ys):
            ys[i + 1] = y0 + 0.15
    ax.plot(xs, ys, "k-", lw=1.2)
    if label:
        ax.text((x0 + x1) / 2, y0 + 0.35, label,
                ha="center", va="bottom", fontsize=8)


def draw_capacitor(ax, x, y0, y1, label=None, horizontal=False):
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


def draw_inductor(ax, x0, y0, x1, y1, label=None):
    """Draw an inductor symbol (loop series)."""
    import numpy as np

    n_loops = 4
    xs = np.linspace(x0, x1, n_loops * 20 + 1)
    ys = np.full_like(xs, y0)
    for i in range(1, len(xs) - 1):
        t = (i % (20)) / 20.0
        ys[i] = y0 + 0.12 * np.sin(2 * np.pi * t)
    ax.plot(xs, ys, "k-", lw=1.2)
    if label:
        ax.text((x0 + x1) / 2, y0 + 0.35, label,
                ha="center", va="bottom", fontsize=8)


def draw_bjt(ax, x, y, label):
    """Draw a simple NPN BJT symbol."""
    circle = plt.Circle((x, y), 0.35, fill=False, ec="k", lw=1.2)
    ax.add_patch(circle)
    ax.plot([x - 0.7, x - 0.35], [y, y], "k-", lw=1.2)   # base
    ax.plot([x, x + 0.5], [y + 0.35, y + 0.7], "k-", lw=1.2)  # collector
    ax.plot([x, x + 0.5], [y - 0.35, y - 0.7], "k-", lw=1.2)  # emitter
    ax.text(x + 0.5, y + 0.75, label, ha="center", va="bottom", fontsize=8)


def main():
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.set_xlim(-1, 13)
    ax.set_ylim(-2, 5)
    ax.set_aspect("equal")
    ax.axis("off")

    # --- supply rail (VCC = 3.3 V) ---
    ax.plot([0, 12], [4.5, 4.5], "k-", lw=1.5)
    ax.text(-0.4, 4.5, "VCC\n3.3 V", ha="right", va="center",
            fontsize=10, fontweight="bold")

    # --- input source (50 ohm) ---
    ax.plot([0, 1.0], [2.0, 2.0], "k-", lw=1.2)
    ax.plot([1.0, 1.0], [1.6, 2.4], "k-", lw=1.2)
    ax.plot([0.8, 1.0], [2.0, 1.6], "k-", lw=1.2)
    ax.plot([1.0, 1.2], [2.0, 1.6], "k-", lw=1.2)
    ax.text(1.0, 2.6, "VIN\n50 Ohm", ha="center", va="bottom", fontsize=8)

    # --- input matching: C_pad (0.95 pF, shunt) + L_sig (8.56 nH, series) ---
    draw_capacitor(ax, 1.8, 1.6, 2.4, "C_pad\n0.95 pF")
    ax.plot([1.2, 1.55], [2.0, 2.0], "k-", lw=1.2)
    ax.plot([2.05, 2.5], [2.0, 2.0], "k-", lw=1.2)
    draw_inductor(ax, 2.5, 2.0, 3.5, 2.0, "L_sig\n8.56 nH")
    ax.plot([3.5, 4.0], [2.0, 2.0], "k-", lw=1.2)

    # --- bias network at base ---
    draw_resistor(ax, 4.0, 4.5, 4.0, 2.0, "R_B1\n16 kOhm")
    draw_resistor(ax, 4.0, 2.0, 4.0, -0.5, "R_B2\n11 kOhm")
    ax.plot([4.0, 4.0], [-0.5, -1.2], "k-", lw=1.2)
    ax.text(4.0, -1.4, "GND", ha="center", va="top", fontsize=9,
            fontweight="bold")
    ax.plot([4.0, 4.0], [4.5, 4.5], "k-", lw=1.2)
    ax.plot([4.0, 4.0], [2.0, 2.0], "k-", lw=1.2)

    # --- LNA device (BFP420-class NPN) ---
    draw_bjt(ax, 4.8, 2.0, "Q1 (NPN)")
    ax.plot([4.0, 4.15], [2.0, 2.0], "k-", lw=1.2)
    # emitter degeneration
    draw_resistor(ax, 4.8, 1.65, 4.8, 0.5, "R_E\n330 Ohm")
    ax.plot([4.8, 4.8], [1.65, 2.0], "k-", lw=1.2)
    ax.plot([4.8, 4.8], [0.5, -0.5], "k-", lw=1.2)
    ax.text(4.8, -0.7, "GND", ha="center", va="top", fontsize=9,
            fontweight="bold")
    # emitter bypass
    draw_capacitor(ax, 5.3, 0.5, -0.5, "C_E\n10 uF")
    ax.plot([4.8, 5.05], [0.5, 0.5], "k-", lw=1.2)
    ax.plot([5.55, 5.55], [0.5, -0.5], "k-", lw=1.2)
    ax.plot([4.8, 5.05], [-0.5, -0.5], "k-", lw=1.2)
    # collector to output
    ax.plot([5.3, 5.3], [2.7, 2.7], "k-", lw=1.2)
    ax.plot([5.3, 6.0], [2.7, 2.7], "k-", lw=1.2)
    ax.plot([4.8, 4.8], [2.7, 2.35], "k-", lw=1.2)
    ax.plot([4.8, 5.3], [2.7, 2.7], "k-", lw=1.2)
    # supply decoupling at collector
    draw_capacitor(ax, 5.3, 3.5, 4.0, "C_dec\n100 nF")
    ax.plot([5.3, 5.3], [2.7, 3.5], "k-", lw=1.2)
    ax.plot([5.3, 4.8], [4.0, 4.5], "k-", lw=1.2)

    # --- output gain-match PI network ---
    # C_o1 (0.97 pF) shunt at collector
    draw_capacitor(ax, 6.0, 2.0, 3.0, "C_o1\n0.97 pF")
    ax.plot([6.0, 6.0], [2.0, 2.7], "k-", lw=1.2)
    ax.plot([6.0, 6.0], [3.0, 3.5], "k-", lw=1.2)
    # L_out (5.44 nH) series
    draw_inductor(ax, 6.0, 2.7, 7.5, 2.7, "L_out\n5.44 nH")
    ax.plot([7.5, 7.5], [2.7, 2.7], "k-", lw=1.2)
    # C_o2 (4.93 pF) shunt at load
    draw_capacitor(ax, 8.0, 2.0, 3.0, "C_o2\n4.93 pF")
    ax.plot([7.5, 8.0], [2.7, 2.7], "k-", lw=1.2)
    ax.plot([8.0, 8.0], [2.0, 2.7], "k-", lw=1.2)
    ax.plot([8.0, 8.0], [3.0, 3.5], "k-", lw=1.2)

    # --- load (50 ohm antenna feed) ---
    draw_resistor(ax, 9.0, 2.0, 10.5, 2.0, "R_L\n50 Ohm")
    ax.plot([8.0, 9.0], [2.0, 2.0], "k-", lw=1.2)
    ax.plot([10.5, 10.5], [2.0, 0.5], "k-", lw=1.2)
    ax.plot([8.0, 10.5], [0.5, 0.5], "k-", lw=1.2)
    ax.text(9.25, 0.0, "GND", ha="center", va="top", fontsize=9,
            fontweight="bold")

    # --- annotations ---
    ax.text(4.8, 3.5, "Q1: BFP420-class\nNPN (ASSUMED)",
            ha="center", va="bottom", fontsize=8, style="italic")
    ax.text(4.8, -1.2, "re: 330 ohm", ha="center", va="top",
            fontsize=8, style="italic", color="gray")

    ax.set_title("2.4 GHz Low-Noise Amplifier (LNA) - gain-matched, "
                 "input noise-matched", fontsize=12, fontweight="bold")
    ax.text(12, -1.8, "CircuitGen - simulated: "
           "Av = 16.11 dB, S11 = -20.20 dB, NF est 1.34 dB, BW 82.3 MHz",
           ha="right", va="top", fontsize=9, style="italic", color="gray")

    os.makedirs(OUT_DIR, exist_ok=True)
    fig.tight_layout()
    fig.savefig(PNG_PATH, dpi=140, bbox_inches="tight")
    print(f"schematic saved to: {PNG_PATH}")


if __name__ == "__main__":
    main()
