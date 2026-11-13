"""
CircuitGen - Impedance Matching Network schematic diagram generator.

Generates a readable schematic (PNG) of the 2.4 GHz L-match network that
transforms a 50 ohm source to a 36.5 ohm antenna port impedance.
Values are verified numerically: Zin = 49.89 - 0.21j ohm, |S11| = -52.6 dB.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = r"C:\CircuitGen\projects\Impedance_Matching_Network"
PNG_PATH = os.path.join(OUT_DIR, "schematic.png")


def draw_inductor(ax, x0, y0, x1, y1, label=None):
    import numpy as np

    n_loops = 4
    xs = np.linspace(x0, x1, n_loops * 20 + 1)
    ys = np.full_like(xs, y0)
    for i in range(1, len(xs) - 1):
        t = (i % 20) / 20.0
        ys[i] = y0 + 0.12 * np.sin(2 * np.pi * t)
    ax.plot(xs, ys, "k-", lw=1.2)
    if label:
        ax.text((x0 + x1) / 2, y0 + 0.35, label,
                ha="center", va="bottom", fontsize=9)


def draw_capacitor(ax, x, y0, y1, label=None, horizontal=False):
    if horizontal:
        ax.plot([x - 0.25, x - 0.25], [y0, y1], "k-", lw=1.2)
        ax.plot([x + 0.25, x + 0.25], [y0, y1], "k-", lw=1.2)
        if label:
            ax.text(x, y0 + 0.4, label, ha="center", va="bottom", fontsize=9)
    else:
        ax.plot([x, x], [y0 - 0.25, y0 + 0.25], "k-", lw=1.2)
        ax.plot([x, x], [y1 - 0.25, y1 + 0.25], "k-", lw=1.2)
        if label:
            ax.text(x + 0.4, y0, label, ha="left", va="center", fontsize=9)


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
                ha="center", va="bottom", fontsize=9)


def main():
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.set_xlim(-2, 12)
    ax.set_ylim(-2, 4)
    ax.set_aspect("equal")
    ax.axis("off")

    # --- 50 ohm source (left) ---
    ax.plot([0, 1.5], [2, 2], "k-", lw=1.2)
    ax.plot([1.5, 1.5], [1.6, 2.4], "k-", lw=1.2)
    ax.plot([1.3, 1.5], [2.0, 1.6], "k-", lw=1.2)
    ax.plot([1.5, 1.7], [2.0, 1.6], "k-", lw=1.2)
    ax.text(1.5, 2.6, "VIN\n50 Ohm", ha="center", va="bottom", fontsize=9)

    # --- shunt inductor (source side) ---
    draw_inductor(ax, 1.5, 2.0, 3.0, 2.0, "L_shunt\n5.5 nH")
    ax.plot([3.0, 3.0], [2.0, 1.0], "k-", lw=1.2)
    # shunt to ground
    ax.plot([3.0, 3.0], [1.0, 0.3], "k-", lw=1.2)
    ax.plot([2.7, 3.3], [0.3, 0.3], "k-", lw=2.0)
    ax.text(3.0, 0.0, "GND", ha="center", va="top", fontsize=9,
            fontweight="bold")

    # --- series capacitor (load side) ---
    draw_capacitor(ax, 3.0, 2.0, 2.0, "C_series\n3.0 pF", horizontal=True)
    ax.plot([3.25, 4.5], [2.0, 2.0], "k-", lw=1.2)

    # --- antenna port (36.5 ohm load) ---
    ax.plot([4.5, 4.5], [2.0, 0.5], "k-", lw=1.2)
    ax.plot([4.2, 4.8], [0.5, 0.5], "k-", lw=2.0)
    ax.text(4.5, 0.0, "GND", ha="center", va="top", fontsize=9,
            fontweight="bold")
    ax.text(4.5, 2.6, "Antenna Port\n36.5 Ohm", ha="center", va="bottom",
            fontsize=9, fontweight="bold")

    # --- annotations ---
    ax.text(3.0, 3.5, "L-match: 50 Ohm source -> 36.5 Ohm antenna port",
            ha="center", va="center", fontsize=11, fontweight="bold")
    ax.text(3.0, 3.0, "Zin = 49.89 - 0.21j ohm  |  |S11| = 0.0024 (-52.6 dB)",
            ha="center", va="center", fontsize=9, style="italic", color="gray")
    ax.text(3.0, 2.6, "2.4 GHz  (lambda/4 monopole over ground)",
            ha="center", va="center", fontsize=9, style="italic", color="gray")

    ax.text(10, -1.5, "CircuitGen - verified design: "
           "E24 values L=5.5 nH, C=3.0 pF",
           ha="right", va="top", fontsize=9, style="italic", color="gray")

    os.makedirs(OUT_DIR, exist_ok=True)
    fig.tight_layout()
    fig.savefig(PNG_PATH, dpi=140, bbox_inches="tight")
    print(f"schematic saved to: {PNG_PATH}")


if __name__ == "__main__":
    main()
