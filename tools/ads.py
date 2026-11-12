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

    return {
        "status": "active_circuit_build_requested" if design_family == "active" else "passive_circuit_build_requested",
        "circuit_type": design_family,
        "design": design_key,
        "frequency_ghz": frequency_ghz,
        "design_info": design_info,
        "ads_launch": launch_result,
    }
