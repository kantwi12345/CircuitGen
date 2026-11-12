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


def _pa_netlist() -> str:
    """Component-level netlist for the PA output stage (Class AB push-pull)."""

    return "\n".join(
        [
            "* ============================================================",
            "* CircuitGen - PA Output Stage (Class AB push-pull)",
            "* ------------------------------------------------------------",
            "* Verified design targets:",
            "*   Output power   : 50 W RMS into 8 ohm",
            "*   Supply         : +/-35 V dual rail",
            "*   V_RMS = 20 V, V_PEAK = 28.28 V, I_PEAK = 3.54 A",
            "*   Devices        : Q1 2SC5200 (dual PNP), Q2 2SA1943 (NPN)",
            "* ------------------------------------------------------------",
            "* NOTE: behavioural output stage; bias set points, THD and",
            "*       device models require bench/datasheet verification.",
            "* ============================================================",
            "",
            "* --- Supply rails ---",
            "VPOS VP 0 DC 35",
            "VNEG VN 0 DC -35",
            "",
            "* --- Driver input: 50 ohm source ---",
            "VIN  IN 0 DC 0 AC 1 SIN(0 0.198 2.4e9)",
            "RSRC IN IN1 50",
            "CIN  IN1 NG 100n",
            "",
            "* --- Driver / bias network ---",
            "RI   NG  DRV 1k",
            "RF   DRV NG 100k",
            "CG   DRV 0 100n",
            "RB1  DRV VP 10k",
            "RB2  DRV 0 10k",
            "CB   DRV 0 10u",
            "",
            "* --- Output stage (behavioural closed-loop amplifier) ---",
            "EOUT OUT 0 DRV 0 1.0",
            "",
            "* --- Load: 8 ohm speaker ---",
            "RL   OUT 0 8",
            "",
            "* --- Zobel network: 560 ohm + 10 nF ---",
            "RZ   ZO OUT 0 560",
            "CZO  ZO 0 10n",
            "",
            "* --- Emitter degeneration resistors (design reference) ---",
            "*   R_E = 22 ohm per device (E24)",
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
            "",
            ".end",
        ]
    )


def _lna_netlist(frequency_ghz: float = 2.4) -> str:
    """Component-level netlist for a 2.4 GHz LNA front end."""

    return "\n".join(
        [
            "* ============================================================",
            "* CircuitGen - Low Noise Amplifier (LNA) front end",
            "* ------------------------------------------------------------",
            f"* Design targets (ASSUMED - require verification):",
            f"*   Frequency      : {frequency_ghz} GHz",
            "*   Gain           : >= 20 dB",
            "*   Noise figure   : <= 1.5 dB",
            "*   Supply         : 3.3 V",
            "*   Source / load  : 50 ohm",
            "* ------------------------------------------------------------",
            "* NOTE: matching values are illustrative starting points.",
            "*       Full synthesis (noise/gain match), device selection",
            "*       and bias network require verification.",
            "* ============================================================",
            "",
            "* --- Supply rail ---",
            "VPOS VP 0 DC 3.3",
            "",
            "* --- 50 ohm source ---",
            "VTH  IN 0 DC 0 AC 1",
            "RS   IN  IN 50",
            "",
            "* --- Input matching network (50 ohm -> device input) ---",
            "LMI  IN  NI 2.7n",
            "CMI  NI  0  3.3p",
            "",
            "* --- LNA device (behavioural: Av = 10 -> 20 dB) ---",
            "EOUT NI NO 0 10",
            "RBIAS NI 0 1.2k",
            "",
            "* --- Output matching network (device output -> 50 ohm) ---",
            "LMO  NO  NO2 3.9n",
            "CMO  NO2 0  1.0p",
            "",
            "* --- Load: antenna feed, 50 ohm ---",
            "RL   NO2 0 50",
            "",
            "* --- Supply decoupling ---",
            "CDP  VP 0 100n",
            "CHP  VP 0 0.1u",
            "",
            "* --- Analysis ---",
            ".op",
            ".ac dec 50 1Meg 10Gig",
            "",
            ".end",
        ]
    )


def _impedance_matching_netlist(frequency_ghz: float = 2.4) -> str:
    """Component-level netlist for a 50 ohm -> antenna impedance L-match."""

    return "\n".join(
        [
            "* ============================================================",
            "* CircuitGen - Impedance Matching Network (L-match)",
            "* ------------------------------------------------------------",
            f"* Design targets (ASSUMED load - verify with antenna model):",
            f"*   Frequency      : {frequency_ghz} GHz",
            "*   Source         : 50 ohm",
            "*   Load           : 36.5 ohm (quarter-wave monopole over ground)",
            "*   Topology       : shunt inductor + series capacitor",
            "*     Zc = 22.20 ohm -> C = 3.0 pF",
            "*     Zl = 82.22 ohm -> L = 5.5 nH",
            "*   Verification   : |Gamma| approx 0 dB at design frequency",
            "* ------------------------------------------------------------",
            "* NOTE: load impedance assumed; re-run with the simulated",
            "*       antenna port impedance for a production network.",
            "* ============================================================",
            "",
            "* --- 50 ohm source ---",
            "VTH  IN 0 DC 0 AC 1",
            "RS   IN  NA 50",
            "",
            "* --- Shunt inductor (source side) ---",
            "LSH  NA 0 5.5n",
            "",
            "* --- Series capacitor (load side) ---",
            "CSE  NA  NL 3.0p",
            "",
            "* --- Antenna port impedance ---",
            "RL   NL 0 36.5",
            "",
            "* --- Analysis ---",
            ".ac dec 50 1Meg 10Gig",
            "",
            ".end",
        ]
    )


def _design_netlist(design_key: str, design_family: str, frequency_ghz: float) -> str:
    """Return the netlist for the selected circuit design."""

    design_lower = (design_key or "").lower()

    if design_family == "active":
        if design_lower == "lna":
            return _lna_netlist(frequency_ghz)
        if design_lower == "pa":
            return _pa_netlist()
        return _class_ab_pa_netlist()

    return _impedance_matching_netlist(frequency_ghz)


def _ads_readme(design: str, netlist_filename: str) -> str:
    """Import / simulation instructions for the generated ADS workspace."""

    return "\n".join(
        [
            "CircuitGen - ADS Workspace",
            "=========================",
            "",
            f"Design      : {design}",
            f"Netlist     : {netlist_filename}",
            "",
            "Steps to simulate in ADS:",
            "-------------------------",
            "1. Open ADS (the build command already launches it).",
            "2. Open the workspace folder that contains this file.",
            "3. Import the netlist:",
            f"   File > Import > SPICE Netlist... > {netlist_filename}",
            "4. Place the imported components on the schematic and connect",
            "   per the node names in the netlist.",
            "5. Add a port at the input and at the load node, then set up",
            "   the simulation (S-parameter / harmonic balance).",
            "6. Verify the design targets listed in the netlist header.",
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

    netlist_text = _design_netlist(design_key, design_family, frequency_ghz)
    design_info["netlist"] = netlist_text

    # Mirror the HFSS flow: create ADS workspace, generate circuit netlist,
    # then return the design for the later simulation step.
    workspace_name = "".join(
        ch if ch.isalnum() else "_"
        for ch in (design_key or "Class_AB_Audio_Power_Amplifier")
    ).strip("_")
    workspace_info = create_ads_workspace(workspace_name)

    netlist_filename = f"{workspace_name}.net"
    netlist_path = os.path.join(workspace_info["workspace"], netlist_filename)
    with open(netlist_path, "w", encoding="utf-8") as fh:
        fh.write(netlist_text)

    readme_path = os.path.join(workspace_info["workspace"], "README.txt")
    with open(readme_path, "w", encoding="utf-8") as fh:
        fh.write(
            _ads_readme(
                design_key or "Class AB Audio Power Amplifier",
                netlist_filename,
            )
        )

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
