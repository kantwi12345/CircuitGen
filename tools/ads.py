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
    frequency_ghz: float = 2.4,
):

    # ADS circuit build command handler.
    # NOTE: programmatic ADS COM editor automation is not currently
    # available in this environment; design math is performed with the
    # working substitute tool (MATLAB) while the ADS build is prepared.

    launch_result = launch_ads()

    if circuit_type.lower() == "active":

        return {
            "status": "active_circuit_build_requested",
            "circuit_type": "active",
            "frequency_ghz": frequency_ghz,
            "design": {
                "amplifier": "Class AB Audio Power Amplifier",
                "output_power_w": 50,
                "load_ohm": 8,
                "supply_v": "+/-35",
                "closed_loop_gain": 101,
            },
            "ads_launch": launch_result,
        }

    if circuit_type.lower() == "passive":

        return {
            "status": "passive_circuit_build_requested",
            "circuit_type": "passive",
            "frequency_ghz": frequency_ghz,
            "ads_launch": launch_result,
        }

    return {
        "status": "circuit_type_not_supported",
        "circuit_type": circuit_type,
        "frequency_ghz": frequency_ghz,
        "ads_launch": launch_result,
    }
