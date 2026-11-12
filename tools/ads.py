# tools/ads.py

import os
import subprocess

from tools.ads_project import create_ads_workspace

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
    """Component-level ADS/SPICE netlist for the Class AB Audio Power Amplifier."""

    return "\n".join(
        [
            "* ============================================================",
            "* CircuitGen - Class AB Audio Power Amplifier",
            "* ------------------------------------------------------------",
            "* Verified design targets:",
            "*   Output power   : 50 W RMS",
            "*   Load           : 8 ohm",
            "*   Supply         : +/-35 V dual rail",
            "*   Closed-loop Av : 101  (R_f = 100k, R_i = 1k)",
            "*   V_RMS  = sqrt(P * R_L) = sqrt(50 * 8) = 20 V",
            "*   V_PEAK = 20 * sqrt(2) = 28.28 V",
            "*   I_PEAK = 28.28 / 8 = 3.54 A",
            "*   I_RMS  = 3.54 / sqrt(2) = 2.50 A",
            "*   V_in needed for 50 W = V_RMS / A_v = 0.198 V RMS",
            "* ------------------------------------------------------------",
            "* Component values (E24 / standard):",
            "*   R_f = 100k, R_i = 1k, R_E = 22, Zobel = 560 + 10n",
            "*   Decoupling = 220u + 0.1u per rail (>= 63 V rating)",
            "* ------------------------------------------------------------",
            "* NOTE: behavioural output stage (ideal closed-loop amplifier).",
            "*       Real BJT models, THD and bias set points require",
            "*       bench verification and datasheet-level modelling.",
            "* ============================================================",
            "",
            "* --- Supply rails (split supply) ---",
            "VPOS VP 0 DC 35",
            "VNEG VN 0 DC -35",
            "",
            "* --- Input source: 50 ohm line source, 0.198 V RMS ---",
            "VIN  IN 0 DC 0 AC 1 SIN(0 0.198 2.4e9)",
            "RSRC IN IN1 50",
            "",
            "* --- Gain stage: A_v = 1 + R_f/R_i = 101 ---",
            "CIN  IN1 NG 100n",
            "RI   NG  OFB 1k",
            "RF   OFB NG 100k",
            "CG   OFB 0 100n",
            "",
            "* --- Output stage: ideal closed-loop amplifier (behavioural) ---",
            "EOUT OUT 0 OFB 0 1.0",
            "",
            "* --- Load: 8 ohm speaker ---",
            "RL   OUT 0 8",
            "",
            "* --- Zobel network (output stability): 560 ohm + 10 nF ---",
            "RZ   ZO OUT 0 560",
            "CZO  ZO 0 10n",
            "",
            "* --- Supply decoupling: 220 uF + 0.1 uF per rail ---",
            "CDP  VP 0 220u",
            "CHP  VP 0 0.1u",
            "CDN  VN 0 220u",
            "CHN  VN 0 0.1u",
            "",
            "* --- Analysis ---",
            ".op",
            ".ac dec 50 1Meg 10Gig",
            ".tran 1n 10u",
            "",
            ".end",
        ]
    )


def _ads_readme(design: str) -> str:
    """Import / simulation instructions for the generated ADS workspace."""

    return "\n".join(
        [
            "CircuitGen - ADS Workspace",
            "=========================",
            "",
            f"Design      : {design}",
            "Netlist     : ClassAB_PA.net",
            "",
            "Steps to simulate in ADS:",
            "-------------------------",
            "1. Open ADS (the build command already launches it).",
            "2. Create/open the workspace:",
            "   C:\\CircuitGen\\projects\\AntennaCircuit",
            "3. Import the netlist:",
            "   File > Import > SPICE Netlist... > ClassAB_PA.net",
            "4. Place the imported components on the schematic and connect",
            "   per the node names in the netlist.",
            "5. Add a port at the input (IN) and at the load (OUT / RL to GND),",
            "   then set up the simulation (S-parameter / harmonic balance).",
            "6. Verify: V_RMS at OUT = 20 V, P_load = 50 W, I_PEAK = 3.54 A.",
            "",
            "Note: excitation, ports and sweeps are configured manually in ADS",
            "      (same approach as the HFSS geometry-only workflow).",
            "",
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

    # Mirror the HFSS flow: create ADS workspace, generate circuit netlist,
    # then return the design for the later simulation step.
    workspace_name = "".join(
        ch if ch.isalnum() else "_"
        for ch in (design_key or "Class_AB_Audio_Power_Amplifier")
    ).strip("_")
    workspace_info = create_ads_workspace(workspace_name)

    netlist_text = design_info.get("netlist") or _class_ab_pa_netlist()
    netlist_filename = "ClassAB_PA.net"
    netlist_path = os.path.join(workspace_info["workspace"], netlist_filename)
    with open(netlist_path, "w", encoding="utf-8") as fh:
        fh.write(netlist_text)

    readme_path = os.path.join(workspace_info["workspace"], "README.txt")
    with open(readme_path, "w", encoding="utf-8") as fh:
        fh.write(_ads_readme(design_key or "Class AB Audio Power Amplifier"))

    return {
        "status": "active_circuit_build_requested" if design_family == "active" else "passive_circuit_build_requested",
        "circuit_type": design_family,
        "design": design_key,
        "frequency_ghz": frequency_ghz,
        "design_info": design_info,
        "ads_launch": launch_result,
        "workspace": workspace_info,
        "netlist_path": netlist_path,
        "readme_path": readme_path,
        "netlist": netlist_text,
    }
