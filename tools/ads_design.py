"""
CircuitGen - ADS circuit design parameters.

The ADS mirror of the HFSS design-parameter stage: the circuit is
specified (type, design, frequency, targets) before anything is built,
the parameters are derived and validated, saved for reuse, and the build
then produces:

    <workspace>            ADS workspace (real ADS 2023 format)
    <workspace>_lib/       local design library
      netlists/<cell>.net  circuit netlist (SPICE style)
      <cell>_build_sheet   parts / values / nets / grounds for the GUI
      <cell>.mac           AEL macro (played back with Tools > Playback Macro)
    DESIGN_REPORT.md       design math, verification status, flags
"""

import json
import math
import os

from tools.ads import (
    _class_ab_pa_netlist,
    _pa_netlist,
    _lna_netlist,
    _impedance_matching_netlist,
)
from tools.ads_ael import write_macro
from tools.ads_project import create_ads_workspace
from tools.ads_schematic import write_schematic_build_sheet

DESIGN_ROOT = r"C:\CircuitGen\projects\designs"

CIRCUIT_TYPES = ["passive", "active"]

DESIGNS = {
    "Class AB Audio Power Amplifier": {
        "family": "active",
        "description": "50 W RMS into 8 ohm from +/-35 V dual rail",
    },
    "PA": {
        "family": "active",
        "description": "Class AB push-pull PA output stage",
    },
    "LNA": {
        "family": "active",
        "description": "2.4 GHz low-noise amplifier (noise + gain match)",
    },
    "Impedance Matching Network": {
        "family": "passive",
        "description": "50 ohm to antenna impedance L-match",
    },
}


def _slug(name: str) -> str:
    cleaned = "".join(
        ch if (ch.isalnum() or ch in "._-") else "_"
        for ch in str(name).strip()
    )
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "design"


def design_path(name: str) -> str:
    return os.path.join(DESIGN_ROOT, f"ads_{_slug(name)}.json")


def make_circuit_params(
    name: str,
    circuit_type: str = "active",
    design: str = "Class AB Audio Power Amplifier",
    frequency_ghz: float = 2.4,
    load_ohm: float = 8.0,
    output_power_w: float = 50.0,
    supply_v: float = 35.0,
    closed_loop_gain: float = 101.0,
):
    """
    Create a validated ADS circuit parameter set.

    The design is specified first; the derived values (output swing,
    currents, matching network) are computed from it.
    """

    if circuit_type.lower() not in CIRCUIT_TYPES:
        raise ValueError(
            f"unknown circuit type '{circuit_type}' "
            f"(available: {', '.join(CIRCUIT_TYPES)})"
        )

    if design not in DESIGNS:
        raise ValueError(
            f"unknown design '{design}' (available: {', '.join(DESIGNS)})"
        )

    if frequency_ghz <= 0:
        raise ValueError("frequency must be positive")

    params = {
        "tool": "ads",
        "name": name,
        "circuit_type": circuit_type.lower(),
        "design": design,
        "frequency_ghz": float(frequency_ghz),
        "load_ohm": float(load_ohm),
        "output_power_w": float(output_power_w),
        "supply_v": float(supply_v),
        "closed_loop_gain": float(closed_loop_gain),
    }

    params["derived"] = derive(params)
    params["checks"] = validate(params)

    return params


def derive(params: dict) -> dict:
    """Compute the design values from the parameters."""

    power = params["output_power_w"]
    load = params["load_ohm"]
    gain = params["closed_loop_gain"]
    v_rms = math.sqrt(power * load)
    v_peak = v_rms * math.sqrt(2.0)
    i_peak = v_peak / load
    i_rms = i_peak / math.sqrt(2.0)

    derived = {
        "v_rms": round(v_rms, 3),
        "v_peak": round(v_peak, 3),
        "i_peak": round(i_peak, 3),
        "i_rms": round(i_rms, 3),
        "v_in_rms": round(v_rms / gain, 4),
        "supply_v": params["supply_v"],
        "supply_headroom_v": round(params["supply_v"] - v_peak, 3),
    }

    if params["design"] == "Impedance Matching Network":
        # L-match: shunt inductor (source side) + series capacitor (load side)
        z_opt = 22.20      # ohm
        z_shunt = 82.22     # ohm
        f = params["frequency_ghz"] * 1e9
        derived["match_c_pf"] = round(1e12 / (2 * math.pi * f * z_opt), 3)
        derived["match_l_nh"] = round(1e9 * z_shunt / (2 * math.pi * f), 3)
        derived["match_source_ohm"] = 50.0
        derived["match_load_ohm"] = 36.5

    if params["design"] == "LNA":
        # optimised 2.4 GHz LNA values (see lna_synthesis.py / lna_optimize.py)
        derived.update({
            "c_pad_pf": 0.95,
            "l_sig_nh": 8.56,
            "c_o1_pf": 0.97,
            "l_out_nh": 5.44,
            "c_o2_pf": 4.93,
            "r_e_ohm": 330,
            "r_b1_ohm": 16000,
            "r_b2_ohm": 11000,
            "gm_s": 0.058,
            "r_pi_ohm": 2068,
            "c_pi_pf": 1.5,
            "r_o_ohm": 30000,
            "gain_db": 16.11,
            "s11_db": -20.20,
            "bandwidth_mhz": 82.3,
            "nf_db": 1.34,
        })

    return derived


def validate(params: dict) -> list:
    """Design-level checks."""

    problems = []

    derived = params.get("derived") or {}

    if derived.get("supply_headroom_v", 0) < 0:
        problems.append(
            f"supply {params['supply_v']} V cannot swing "
            f"{derived['v_peak']} V peak"
        )

    if params["design"] == "Impedance Matching Network":
        if derived.get("match_load_ohm") and derived.get("match_source_ohm"):
            if abs(derived["match_source_ohm"]
                   - derived["match_load_ohm"]) < 1e-6:
                problems.append("match network has no impedance step")

    return problems


def save_design(params: dict) -> str:
    os.makedirs(DESIGN_ROOT, exist_ok=True)

    path = design_path(params["name"])
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(params, fh, indent=2)

    return path


def load_design(name: str) -> dict:
    path = design_path(name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"ADS design parameters not found: {name}")

    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def list_designs() -> list:
    if not os.path.isdir(DESIGN_ROOT):
        return []

    designs = []
    for filename in sorted(os.listdir(DESIGN_ROOT)):
        if not filename.startswith("ads_") or not filename.endswith(".json"):
            continue
        try:
            with open(os.path.join(DESIGN_ROOT, filename), "r",
                      encoding="utf-8") as fh:
                data = json.load(fh)
            designs.append({
                "name": data.get("name"),
                "design": data.get("design"),
                "circuit_type": data.get("circuit_type"),
                "frequency_ghz": data.get("frequency_ghz"),
                "checks": data.get("checks", []),
            })
        except (OSError, ValueError):
            continue

    return designs


def netlist_for(params: dict) -> str:
    """The circuit netlist for the selected design."""

    design = params["design"]

    if design == "LNA":
        return _lna_netlist(params["frequency_ghz"])
    if design == "PA":
        return _pa_netlist()
    if design == "Impedance Matching Network":
        return _impedance_matching_netlist(params["frequency_ghz"])
    return _class_ab_pa_netlist()


def build_circuit(params: dict, open_in_ads: bool = False):
    """
    Build the ADS artefacts for a parameter set:
    workspace, local library, netlist, build sheet, AEL macro, report.
    """

    if params.get("checks"):
        raise ValueError(
            "design parameters failed validation: "
            + "; ".join(params["checks"])
        )

    design = params["design"]
    netlist = netlist_for(params)

    workspace_info = create_ads_workspace(design, units="mm")
    schematic_info = write_schematic_build_sheet(
        workspace_info, design, netlist)

    macro_path = os.path.join(
        os.path.dirname(schematic_info["netlist_path"]),
        f"{schematic_info['cell']}.mac",
    )
    write_macro(
        macro_path,
        workspace_info["library_name"],
        schematic_info["cell"],
        netlist,
    )

    report_path = os.path.join(
        workspace_info["workspace"], "DESIGN_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(_report(params))

    result = {
        "status": "ads_circuit_ready",
        "design": design,
        "workspace": workspace_info["workspace"],
        "library": workspace_info["library"],
        "cell": schematic_info["cell"],
        "netlist_path": schematic_info["netlist_path"],
        "build_sheet_path": schematic_info["build_sheet_path"],
        "macro_path": macro_path,
        "report_path": report_path,
        "parameters": params,
    }

    if open_in_ads:
        try:
            from tools.ads_attach import attach, play_macro

            result["attach"] = attach(
                workspace_info["workspace"],
                schematic_info["cell"],
                library_name=workspace_info["library_name"],
            )
            result["macro_play"] = play_macro(macro_path)
        except Exception as exc:
            result["attach"] = {"status": "failed", "error": str(exc)}

    return result


def _report(params: dict) -> str:
    derived = params["derived"]
    lines = [
        f"# CircuitGen - ADS Design Report: {params['design']}",
        "",
        "## 1. Parameters",
        "",
        "| Parameter | Value |",
        "|---|---|",
        f"| Circuit type | {params['circuit_type']} |",
        f"| Design | {params['design']} |",
        f"| Frequency | {params['frequency_ghz']} GHz |",
        f"| Output power | {params['output_power_w']} W RMS |",
        f"| Load | {params['load_ohm']} ohm |",
        f"| Supply | +/-{params['supply_v']} V |",
        f"| Closed-loop gain | {params['closed_loop_gain']} |",
        "",
        "## 2. Derived",
        "",
        "| Quantity | Value |",
        "|---|---|",
    ]

    for key, value in derived.items():
        lines.append(f"| {key} | {value} |")

    lines += [
        "",
        "## 3. Verification status",
        "",
    ]

    for problem in params.get("checks") or []:
        lines.append(f"- WARNING: {problem}")

    if not params.get("checks"):
        lines.append("- All design checks passed")

    lines += [
        "- Circuit simulation: run the generated netlist in the workspace "
        "(or use the CircuitGen AC solver).",
        "- Component placement inside the cell is done from the build sheet "
        "or by importing the netlist (ADS COM automation is unavailable).",
        "",
    ]

    return "\n".join(lines)
