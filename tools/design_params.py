"""
CircuitGen - design parameters.

Everything about an antenna is decided BEFORE the model is built:
target frequency, substrate and thickness, feed type and any manual
overrides. The parameter set is then derived into the complete geometry
(patch size, 50 ohm feed width and length, board size, radiation box),
validated, and can be saved / reloaded so a design can be reviewed,
edited and rebuilt reproducibly.
"""

import json
import os

from tools.antenna_calcs import (
    patch_layout,
    monopole_layout,
    dipole_layout,
    microstrip_width_50ohm,
    e24_round,
)
from tools.antenna_library import SUBSTRATES

DESIGN_ROOT = r"C:\CircuitGen\projects\designs"

FEED_TYPES = ["edge_inset", "inset"]


def design_path(name: str) -> str:
    return os.path.join(DESIGN_ROOT, f"{_slug(name)}.json")


def _slug(name: str) -> str:
    cleaned = "".join(
        ch if (ch.isalnum() or ch in "._-") else "_"
        for ch in str(name).strip()
    )
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "design"


def make_design_params(
    name: str,
    antenna_type: str = "patch",
    frequency_ghz: float = 2.4,
    substrate: str = "FR4",
    thickness_mm: float = None,
    feed_type: str = "edge_inset",
    patch_width_mm: float = None,
    patch_length_mm: float = None,
    radiator_radius_mm: float = None,
):
    """
    Create a validated design parameter set for an antenna.

    thickness_mm defaults to the substrate's nominal thickness.
    patch_width_mm / patch_length_mm / radiator_radius_mm are optional
    manual overrides - when omitted they are derived from the physics.
    """

    if antenna_type.lower() not in ("patch", "monopole", "dipole"):
        raise ValueError(f"unsupported antenna type: {antenna_type}")

    if substrate not in SUBSTRATES:
        raise ValueError(
            f"unknown substrate '{substrate}' "
            f"(available: {', '.join(SUBSTRATES)})"
        )

    if feed_type not in FEED_TYPES:
        raise ValueError(
            f"unknown feed type '{feed_type}' (available: {', '.join(FEED_TYPES)})"
        )

    sub = SUBSTRATES[substrate]
    if thickness_mm is None:
        thickness_mm = sub["thickness_mm"]

    params = {
        "name": name,
        "antenna_type": antenna_type.lower(),
        "frequency_ghz": float(frequency_ghz),
        "substrate": substrate,
        "er": sub["er"],
        "loss_tangent": sub["loss_tan"],
        "thickness_mm": float(thickness_mm),
        "feed_type": feed_type,
        "overrides": {
            "patch_width_mm": patch_width_mm,
            "patch_length_mm": patch_length_mm,
            "radiator_radius_mm": radiator_radius_mm,
        },
    }

    params["derived"] = derive(params)
    params["checks"] = validate(params)

    return params


def derive(params: dict) -> dict:
    """Compute the complete geometry from the design parameters."""

    antenna_type = params["antenna_type"]
    overrides = params.get("overrides") or {}

    if antenna_type == "patch":

        layout = patch_layout(
            params["frequency_ghz"],
            er=params["er"],
            h_mm=params["thickness_mm"],
            width_mm=overrides.get("patch_width_mm"),
            length_mm=overrides.get("patch_length_mm"),
        )
        layout["feed_impedance_ohm"] = 50.0
        layout["feed_width_50ohm_calculated_mm"] = round(
            microstrip_width_50ohm(params["er"], params["thickness_mm"]), 3)
        return layout

    if antenna_type == "monopole":

        radius = overrides.get("radiator_radius_mm")
        if radius is None:
            radius = 0.5
        layout = monopole_layout(params["frequency_ghz"], radius_mm=radius)
        layout["feed_width_50ohm_calculated_mm"] = None
        return layout

    radius = overrides.get("radiator_radius_mm")
    if radius is None:
        radius = 1.0
    layout = dipole_layout(params["frequency_ghz"], radius_mm=radius)
    layout["feed_width_50ohm_calculated_mm"] = None
    return layout


def validate(params: dict) -> list:
    """Design-level checks (independent of the geometry layout checks)."""

    problems = []

    if params["frequency_ghz"] <= 0:
        problems.append("frequency must be positive")

    if params["thickness_mm"] <= 0:
        problems.append("substrate thickness must be positive")

    derived = params.get("derived") or {}
    problems.extend(derived.get("checks") or [])

    # feed width sanity for the patch
    if params["antenna_type"] == "patch":
        w = derived.get("feed_width_mm")
        calc = derived.get("feed_width_50ohm_calculated_mm")
        if w is not None and calc is not None:
            if abs(w - calc) > 0.35:
                problems.append(
                    f"feed width {w} mm deviates from the 50 ohm width "
                    f"{calc:.2f} mm - the match will be off"
                )

    return problems


def update_params(params: dict, **changes) -> dict:
    """Apply changes to a parameter set and re-derive it."""

    updated = dict(params)
    updated.update({k: v for k, v in changes.items() if v is not None})

    if "substrate" in changes and changes["substrate"]:
        sub = SUBSTRATES[changes["substrate"]]
        updated["er"] = sub["er"]
        updated["loss_tangent"] = sub["loss_tan"]

    updated["derived"] = derive(updated)
    updated["checks"] = validate(updated)

    return updated


def save_design(params: dict) -> str:
    os.makedirs(DESIGN_ROOT, exist_ok=True)

    path = design_path(params["name"])
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(params, fh, indent=2)

    return path


def load_design(name: str) -> dict:
    path = design_path(name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"design parameters not found: {name}")

    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def list_designs() -> list:
    if not os.path.isdir(DESIGN_ROOT):
        return []

    designs = []
    for filename in sorted(os.listdir(DESIGN_ROOT)):
        if not filename.endswith(".json"):
            continue
        try:
            with open(os.path.join(DESIGN_ROOT, filename), "r",
                      encoding="utf-8") as fh:
                data = json.load(fh)
            designs.append({
                "name": data.get("name"),
                "antenna_type": data.get("antenna_type"),
                "frequency_ghz": data.get("frequency_ghz"),
                "substrate": data.get("substrate"),
                "checks": data.get("checks", []),
            })
        except (OSError, ValueError):
            continue

    return designs


def build_from_params(params: dict) -> dict:
    """Build the HFSS model from a validated design parameter set."""

    if params.get("checks"):
        raise ValueError(
            "design parameters failed validation: "
            + "; ".join(params["checks"])
        )

    from tools.hfss_com import (
        create_patch_antenna,
        create_monopole_antenna,
        create_dipole_antenna,
    )

    antenna_type = params["antenna_type"]

    if antenna_type == "patch":

        overrides = params.get("overrides") or {}

        return create_patch_antenna(
            width_mm=overrides.get("patch_width_mm"),
            length_mm=overrides.get("patch_length_mm"),
            frequency_ghz=params["frequency_ghz"],
            thickness_mm=params["thickness_mm"],
            er=params["er"],
            substrate=params["substrate"],
        )

    if antenna_type == "monopole":

        return create_monopole_antenna(
            frequency_ghz=params["frequency_ghz"],
        )

    return create_dipole_antenna(
        frequency_ghz=params["frequency_ghz"],
    )
