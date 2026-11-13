import math

# E24 standard values (1% series) for rounding component values
E24 = [
    1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6,
    3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1,
]

C_LIGHT = 299792458.0  # m/s


def e24_round(value):
    """Round a positive value to the nearest E24 standard value."""

    if value is None or value <= 0:
        raise ValueError(f"cannot round value: {value}")

    decade = 10 ** math.floor(math.log10(value))
    mantissa = value / decade

    best = min(E24, key=lambda m: abs(m - mantissa))

    return round(best * decade, 6)


def patch_dimensions(freq_ghz, er, h_mm):

    if freq_ghz <= 0:
        raise ValueError(
            f"Invalid frequency: {freq_ghz}"
        )

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


def microstrip_width_50ohm(er, h_mm):
    """50 ohm microstrip width (Hammerstad closed-form synthesis)."""

    if er <= 1 or h_mm <= 0:
        raise ValueError("invalid substrate parameters")

    h = h_mm / 1000.0
    z0 = 50.0

    a = (z0 / 60.0) * math.sqrt((er + 1.0) / 2.0) + \
        ((er - 1.0) / (er + 1.0)) * (0.23 + 0.11 / er)
    b = 377.0 * math.pi / (2.0 * z0 * math.sqrt(er))

    w_over_h = (2.0 / math.pi) * (
        b - 1.0 - math.log(2.0 * b - 1.0)
        + ((er - 1.0) / (2.0 * er))
        * (math.log(b - 1.0) + 0.39 - 0.61 / er)
    )

    return w_over_h * h * 1000.0


def monopole_layout(freq_ghz, radius_mm=0.5):
    """
    Parametric layout of the quarter-wave monopole.

    Radiator length follows lambda0/4 and every other dimension (ground
    plane, radiation box) scales with the wavelength so the model stays
    electrically and geometrically valid at any frequency.
    """

    if freq_ghz <= 0:
        raise ValueError(f"Invalid frequency: {freq_ghz}")

    lam0_mm = 3e8 / (freq_ghz * 1e9) * 1000.0

    layout = {
        "frequency_ghz": freq_ghz,
        "lambda0_mm": round(lam0_mm, 3),
        "monopole_length_mm": round(lam0_mm / 4.0, 3),
        "monopole_radius_mm": radius_mm,
        "ground_half_mm": round(max(50.0, lam0_mm / 4.0), 3),
        "air_x_mm": round(-max(100.0, lam0_mm / 2.0), 3),
        "air_y_mm": round(-max(100.0, lam0_mm / 2.0), 3),
        "air_z_mm": round(-max(100.0, lam0_mm / 4.0), 3),
        "air_size_xy_mm": round(2.0 * max(100.0, lam0_mm / 2.0), 3),
        "air_size_z_mm": round(max(100.0, lam0_mm / 4.0)
                               + max(150.0, lam0_mm), 3),
    }

    layout["checks"] = []

    if layout["monopole_length_mm"] <= 0:
        layout["checks"].append("monopole has no length")

    if layout["ground_half_mm"] < layout["monopole_length_mm"]:
        layout["checks"].append("ground plane is smaller than the radiator")

    return layout


def dipole_layout(freq_ghz, radius_mm=1.0, gap_length_mm=1.0):
    """
    Parametric layout of the half-wave dipole with a feed gap.
    """

    if freq_ghz <= 0:
        raise ValueError(f"Invalid frequency: {freq_ghz}")

    lam0_mm = 3e8 / (freq_ghz * 1e9) * 1000.0

    layout = {
        "frequency_ghz": freq_ghz,
        "lambda0_mm": round(lam0_mm, 3),
        "dipole_length_mm": round(lam0_mm / 2.0, 3),
        "dipole_radius_mm": radius_mm,
        "gap_length_mm": gap_length_mm,
        "gap_radius_mm": radius_mm,
        "air_x_mm": round(-max(100.0, lam0_mm / 2.0), 3),
        "air_y_mm": round(-max(100.0, lam0_mm / 2.0), 3),
        "air_z_mm": round(-max(100.0, lam0_mm / 4.0), 3),
        "air_size_xy_mm": round(2.0 * max(100.0, lam0_mm / 2.0), 3),
        "air_size_z_mm": round(max(100.0, lam0_mm / 4.0)
                               + max(150.0, lam0_mm), 3),
    }

    layout["checks"] = []

    if layout["dipole_length_mm"] <= layout["gap_length_mm"]:
        layout["checks"].append("dipole is shorter than its feed gap")

    return layout


def patch_layout(
    freq_ghz,
    er=4.4,
    h_mm=1.6,
    width_mm=None,
    length_mm=None,
):
    """
    Full parametric layout of the microstrip patch antenna.

    Everything is derived from the operating frequency and the substrate so
    the geometry stays valid (and self-consistent) at any frequency:

      feed width    : 50 ohm microstrip width for the substrate (E24)
      feed length   : lambda0/8 from the board edge to the patch edge
      board size    : patch + margins (scales with frequency)
      patch         : centred in X, fed from the -Y edge
      port sheet    : on the board edge, under the feed line
      air box       : >= lambda0/4 above the radiator, lambda0/8 around
    """

    if freq_ghz <= 0:
        raise ValueError(f"Invalid frequency: {freq_ghz}")

    lam0_mm = C_LIGHT / (freq_ghz * 1e9) * 1000.0

    if width_mm is None or length_mm is None:
        dims = patch_dimensions(freq_ghz, er, h_mm)
        width_mm = dims["width_mm"]
        length_mm = dims["length_mm"]

    feed_width = e24_round(microstrip_width_50ohm(er, h_mm))
    feed_length = e24_round(lam0_mm / 8.0)

    margin = max(8.0, lam0_mm / 8.0)

    board_x = width_mm + 2.0 * margin
    board_y = feed_length + length_mm + margin

    patch_x = (board_x - width_mm) / 2.0
    patch_y = feed_length

    feed_x = (board_x - feed_width) / 2.0

    box_side = max(10.0, lam0_mm / 8.0)
    box_below = max(5.0, lam0_mm / 10.0)
    box_above = max(15.0, lam0_mm / 4.0)

    layout = {
        "frequency_ghz": freq_ghz,
        "er": er,
        "thickness_mm": h_mm,
        "lambda0_mm": round(lam0_mm, 3),
        "patch_width_mm": width_mm,
        "patch_length_mm": length_mm,
        "patch_x_mm": round(patch_x, 3),
        "patch_y_mm": round(patch_y, 3),
        "feed_width_mm": feed_width,
        "feed_length_mm": feed_length,
        "feed_x_mm": round(feed_x, 3),
        "board_x_mm": round(board_x, 3),
        "board_y_mm": round(board_y, 3),
        "port_x_mm": round(feed_x, 3),
        "port_z_mm": h_mm,
        "air_x_mm": round(-box_side, 3),
        "air_y_mm": round(-box_side, 3),
        "air_z_mm": round(-box_below, 3),
        "air_size_x_mm": round(board_x + 2.0 * box_side, 3),
        "air_size_y_mm": round(board_y + 2.0 * box_side, 3),
        "air_size_z_mm": round(box_below + h_mm + box_above, 3),
    }

    layout["checks"] = validate_patch_layout(layout)

    return layout


def validate_patch_layout(layout):
    """Geometric consistency checks - returns a list of failure strings."""

    problems = []

    lam0 = layout["lambda0_mm"]
    bw = layout["board_x_mm"]
    bh = layout["board_y_mm"]
    pw = layout["patch_width_mm"]
    pl = layout["patch_length_mm"]
    px = layout["patch_x_mm"]
    py = layout["patch_y_mm"]
    fw = layout["feed_width_mm"]
    fl = layout["feed_length_mm"]
    fx = layout["feed_x_mm"]

    # patch must sit fully on the board
    if px < 0 or px + pw > bw:
        problems.append("patch overflows the board in X")
    if py < 0 or py + pl > bh:
        problems.append("patch overflows the board in Y")

    # patch must be centred on the feed line in X
    patch_center = px + pw / 2.0
    feed_center = fx + fw / 2.0
    if abs(patch_center - feed_center) > 1e-6:
        problems.append("feed line is not centred on the patch")

    # feed line must reach the patch edge and start at the board edge
    if abs(fl - py) > 1e-6:
        problems.append("feed line does not end at the patch edge")
    if fl <= 0:
        problems.append("feed line has no length")
    if fx + fw > px + pw + 1e-6 or fx + fw < px - 1e-6:
        problems.append("feed line is not under the patch")

    # port sheet must match the feed line
    if abs(layout["port_x_mm"] - fx) > 1e-6:
        problems.append("port sheet is not aligned with the feed line")
    if abs(layout["port_z_mm"] - layout["thickness_mm"]) > 1e-6:
        problems.append("port sheet does not span the substrate thickness")

    # clearance to the radiation boundary
    if layout["air_size_z_mm"] - layout["thickness_mm"] < lam0 / 4.0 - 1e-6:
        problems.append("air box is less than lambda/4 above the radiator")
    if layout["air_x_mm"] + bw + layout["air_size_x_mm"] - bw - px < lam0 / 4.0 - 1e-6:
        problems.append("air box is less than lambda/4 from the patch in X")

    return problems
