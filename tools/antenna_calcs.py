import math

def patch_dimensions(freq_ghz, er, h_mm):

    f = freq_ghz * 1e9
    c = 3e8
    h = h_mm / 1000

    W = c / (2 * f) * math.sqrt(2 / (er + 1))

    eeff = ((er + 1) / 2) + (
        (er - 1) / 2
    ) * (
        1 + 12 * h / W
    ) ** (-0.5)

    L = c / (
        2 * f * math.sqrt(eeff)
    )

    return {
        "width_mm": round(W * 1000, 2),
        "length_mm": round(L * 1000, 2)
    }