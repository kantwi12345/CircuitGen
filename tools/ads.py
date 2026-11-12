# tools/ads.py

import os
import subprocess

ADS_EXE = r"C:\Program Files\Keysight\ADS2023_Update1\bin\ads.exe"


def ads_status():
    return {
        "installed": os.path.exists(ADS_EXE),
        "path": ADS_EXE
    }


def launch_ads():

    if os.path.exists(ADS_EXE):
        subprocess.Popen([ADS_EXE])

        return {
            "status": "ADS launched"
        }

    return {
        "status": "ADS executable not found"
    }


def _class_ab_pa_netlist() -> str:
    """Design-level ADS netlist for the Class AB Audio Power Amplifier."""

    return "\n".join(
        [
            "* ============================================================",
            "* CircuitGen - Class AB Audio Power Amplifier",
            "* Design: Class AB Audio Power Amplifier",
            "* Frequency: 2.4 GHz (design-stage verification)",
            "* Output Power: 50 W RMS",
            "* Load: 8 ohm",
            "* Supply: +/-35 V dual rail",
            "* Closed-Loop Gain: 101 (R_f=100k, R_i=1k)",
            "* ============================================================",
            "* Design Equations",
            "*   V_RMS = sqrt(P * R_L) = sqrt(50 * 8) = 20 V",
            "*   V_PEAK = V_RMS * sqrt(2) = 28.28 V",
            "*   I_PEAK = V_PEAK / R_L = 3.54 A",
            "*   I_RMS = I_PEAK / sqrt(2) = 2.5 A",
            "*   A_v = 1 + R_f / R_i = 1 + 100k/1k = 101",
            "*   V_in (needed) = V_RMS / A_v = 0.198 V RMS",
            "*",
            "* Design Values",
            "*   Q1 = 2SC5200 (dual PNP), Q2 = 2SA1943 (NPN)",
            "*   R_E = 22 ohm (E24)",
            "*   Zobel: R_z = 560 ohm (E24), C_z = 10 nF (C0G/NP0)",
            "*   Supply Decoupling: C_C+/C_C- = 220 uF (electrolytic >= 63 V) + 0.1 uF (ceramic)",
            "* ============================================================",
        ]
    )


def build_ads_circuit(
    circuit_type: str = "passive",
    design: str = "Class AB Audio Power Amplifier",
    frequency_ghz: float = 2.4,
) -> dict:

    # ADS circuit build command handler.
    # NOTE: programmatic ADS COM editor automation is not currently
    # available in this environment; design math is performed with the
    # working substitute tool (MATLAB) while the ADS build is prepared.

    launch_result = launch_ads()

    design_key = (design or "").strip()
    design_lower = design_key.lower()

    design_family = "passive"
    if circuit_type.lower() == "active" or design_lower in (
        "lna",
        "pa",
        "class ab audio power amplifier",
        "classab",
        "class-ab audio power amplifier",
    ):
        design_family = "active"

    design_info = {
        "design": design_key or "Class AB Audio Power Amplifier",
        "circuit_type": design_family,
        "frequency_ghz": frequency_ghz,
    }

    if design_family == "active":
        design_info["design_payload"] = {
            "amplifier": design_key or "Class AB Audio Power Amplifier",
            "frequency_ghz": frequency_ghz,
            "design_family": "active",
        }
        design_info["design_payload"].update({
            "output_power_w": 50,
            "load_ohm": 8,
            "supply_v": "+/-35",
            "closed_loop_gain": 101,
        })

        design_info["netlist"] = _class_ab_pa_netlist()

    return {
        "status": "active_circuit_build_requested" if design_family == "active" else "passive_circuit_build_requested",
        "circuit_type": design_family,
        "design": design_key,
        "frequency_ghz": frequency_ghz,
        "design_info": design_info,
        "ads_launch": launch_result,
    }
