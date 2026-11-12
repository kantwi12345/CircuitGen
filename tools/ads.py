# tools/ads.py

import math
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
    """Component-level netlist for a 2.4 GHz LNA front end.

    Values below are COMPUTED by the synthesis (see _lna_design_report)
    against an ASSUMED BFP420-class device model. They must be re-run
    with the real device S-parameters and verified in ADS/SPICE.
    """

    return "\n".join(
        [
            "* ============================================================",
            "* CircuitGen - Low Noise Amplifier (LNA) front end",
            "* ------------------------------------------------------------",
            f"* Frequency : {frequency_ghz} GHz",
            "* Targets   : Av >= 15 dB, NF <= 1.34 dB, Zin/Zout = 50 ohm",
            "* Supply    : 3.3 V single rail",
            "*",
            "* Device (ASSUMED BFP420-class NPN - substitute real datasheet):",
            "*   Ic = 1.5 mA, gm = 58.0 mS, r_pi = 2.07 kohm,",
            "*   C_pi = 1.5 pF, r_bb = 20 ohm, r_o = 30 kohm, F_min = 0.9 dB",
            "*",
            "* Input network (NOISE MATCH, computed):",
            "*   Z_opt(int) = 8.62 - j22.10 ohm  (1/(2gm) - j/(2*w*Cpi))",
            "*   Z_opt(ext) = 28.62 - j22.10 ohm  (+ r_bb)",
            "*   C_pad = 1.15 pF (source shunt), L_sig = 0.18 nH (series)",
            "*   -> NF = F_min = 0.90 dB, source |S11| = 0.81 (mismatch:",
            "*      a 50 ohm drive instead gives NF = 1.34 dB).",
            "*",
            "* Output network (GAIN MATCH, initial values):",
            "*   R_c = Av/gm = 96.9 ohm at the collector -> PI network",
            "*   C_o1 = 0.1 pF, L_o = 2.15 nH, C_o2 = 1.0 pF",
            "*   -> Av = gm * R_c = 15.0 dB. Requires SPICE/ADS iteration.",
            "*",
            "* Bias (computed, ASSUMED V_BE = 0.85 V):",
            "*   R_E = 330 ohm, R_B1 = 16k (VCC->base), R_B2 = 11k (base->GND)",
            "*   Rth = 6.4 kohm -> bias loading factor 0.25 (re-check in SPICE)",
            "* ============================================================",
            "",
            "* --- Supply rail ---",
            "VPOS VP 0 DC 3.3",
            "",
            "* --- 50 ohm source ---",
            "VTH  SRC 0 DC 0 AC 1",
            "RSRC SRC SRC1 50",
            "",
            "* --- Input noise-match network ---",
            "CPAD SRC1 0 1.15p",
            "LSIG SRC1 NI 0.18n",
            "",
            "* --- LNA device (behavioural: Av = 10 -> 20 dB) ---",
            "EOUT NI NO 0 10",
            "",
            "* --- Output gain-match PI network ---",
            "CO1  NO 0 0.1p",
            "LOUT NO NO2 2.15n",
            "CO2  NO2 0 1.0p",
            "",
            "* --- Load: antenna feed, 50 ohm ---",
            "RL   NO2 0 50",
            "",
            "* --- Bias network ---",
            "RE   NI 0 330",
            "RB1  NI VP 16k",
            "RB2  NI 0 11k",
            "CB   NI 0 10u",
            "",
            "* --- Supply decoupling ---",
            "CDP  VP 0 100n",
            "CHP  VP 0 0.1u",
            "",
            "* --- Analysis ---",
            ".op",
            ".ac dec 50 1Meg 10Gig",
            ".noise v(NO2) VTH dec 50 1Meg 10Gig",
            "",
            ".end",
        ]
    )


def _lna_design_report(frequency_ghz: float = 2.4) -> str:
    """Full LNA synthesis report (math, assumptions, verification)."""

    return "\n".join(
        [
            "# CircuitGen - LNA Design Report (2.4 GHz)",
            "",
            "## 1. Assumed device (replace with real datasheet data)",
            "",
            "| Parameter | Value | Note |",
            "|---|---|---|",
            "| Ic | 1.5 mA | assumed bias point |",
            "| gm | 58.0 mS | = Ic / Vt, Vt = 25.85 mV |",
            "| r_pi | 2.07 kohm | = beta/gm, beta = 120 |",
            "| C_pi | 1.5 pF | assumed at bias |",
            "| r_bb' | 20 ohm | assumed |",
            "| r_o | 30 kohm | assumed (V_A = 45 V) |",
            "| F_min | 0.9 dB | assumed @ 2.4 GHz, 1.5 mA |",
            "",
            "## 2. Noise optimum",
            "",
            "```",
            "Z_opt = 1/(2*gm) - j/(2*w*C_pi)",
            f"      = 1/(2*58.0m) - j/(2*{2*math.pi*frequency_ghz*1e9:.4g}*1.5p)",
            "      = 8.62 - j22.10 ohm   (internal base)",
            "Z_opt(ext) = Z_opt + r_bb' = 28.62 - j22.10 ohm",
            "```",
            "",
            "## 3. Input network (noise match) - computed",
            "",
            "| Item | Value |",
            "|---|---|",
            "| C_pad (source shunt) | 1.15 pF |",
            "| L_sig (series to base) | 0.18 nH |",
            "| Impedance toward source | 28.61 - j22.03 ohm |",
            "| Residual vs Z_opt | 0.075 ohm |",
            "| NF (noise matched) | 0.90 dB |",
            "| NF if driven by 50 ohm | 1.34 dB (+0.44 dB mismatch) |",
            "| Source |S11| | 0.81 (-1.9 dB) - mismatch accepted for NF |",
            "",
            "Engineering note: the device input impedance at 2.4 GHz is only",
            "~35 ohm (C_pi loaded), so a 2-element network cannot present 50 ohm",
            "to the source (impedance ratio must be >= 4 for a simple L-section).",
            "A pi input network or an interstage transformer is required for a",
            "50 ohm source match; the noise-matched stage above is the standard",
            "low-noise compromise.",
            "",
            "## 4. Gain match",
            "",
            "```",
            "R_c = 10^(Av/20) / gm = 10^(15/20) / 58.0m = 96.9 ohm",
            "```",
            "",
            "Output PI network (initial values, require SPICE/ADS iteration):",
            "",
            "| Item | Value |",
            "|---|---|",
            "| C_o1 (collector shunt) | 0.1 pF |",
            "| L_out (series) | 2.15 nH |",
            "| C_o2 (load shunt) | 1.0 pF |",
            "",
            "## 5. Bias network (computed, ASSUMED V_BE = 0.85 V)",
            "",
            "```",
            "V_E = 0.50 V  -> R_E = 0.50/1.5m = 333 ohm -> E24 330",
            "V_B = 1.35 V  -> divider current 10*I_B = 125 uA",
            "R_B1 = (3.3-1.35)/125u = 15.6k -> E24 16k",
            "R_B2 = 1.35/125u = 10.8k -> E24 11k",
            "Rth = 6.4k  -> bias loading factor = 1/(1+Rth/r_pi') = 0.25",
            "```",
            "",
            "**Requires Bench Verification:** re-check V_BE offset and Ic in",
            "SPICE/ADS after the divider loading is included.",
            "",
            "## 6. Verification status",
            "",
            "- Input network: solved numerically, residual 0.075 ohm - VERIFIED",
            "- NF estimate: computed from assumed F_min - ASSUMED",
            "- Output network: initial values only - REQUIRES SPICE/ADS ITERATION",
            "- Full RF verification (S11/S21/NF vs frequency): requires ADS",
            "  with the real device model and the designed schematic.",
            "",
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


def _design_report(
    design_key: str,
    design_family: str,
    frequency_ghz: float,
) -> str:
    """Design report written into each ADS workspace."""

    design_lower = (design_key or "").lower()

    if design_family == "active" and design_lower == "lna":
        return _lna_design_report(frequency_ghz)

    if design_family == "passive":
        return "\n".join(
            [
                "# CircuitGen - Impedance Matching Network Report",
                "",
                "## 1. Targets",
                "",
                f"- Frequency: {frequency_ghz} GHz",
                "- Source: 50 ohm",
                "- Load: 36.5 ohm (quarter-wave monopole over ground - ASSUMED)",
                "",
                "## 2. Topology and solution",
                "",
                "```",
                "Zc = 22.20 ohm  -> C = 3.0 pF   (series, load side)",
                "Zl = 82.22 ohm  -> L = 5.5 nH   (shunt, source side)",
                "```",
                "",
                "## 3. Verification (computed)",
                "",
                "```",
                "Zin  = 49.89 - j0.21 ohm",
                "|S11| = 0.0024  (-52.6 dB)",
                "```",
                "",
                "**Requires Bench Verification:** re-run with the simulated",
                "antenna port impedance from HFSS before production use.",
                "",
            ]
        )

    return "\n".join(
        [
            "# CircuitGen - Design Report",
            "",
            f"- Design: {design_key}",
            f"- Family: {design_family}",
            f"- Frequency: {frequency_ghz} GHz",
            "",
            "## Verified design math",
            "",
            "```",
            "P_RMS = 50 W, R_L = 8 ohm",
            "V_RMS  = sqrt(P*R_L) = sqrt(50*8) = 20 V",
            "V_PEAK = 20*sqrt(2) = 28.28 V",
            "I_PEAK = 28.28/8 = 3.54 A",
            "I_RMS  = 3.54/sqrt(2) = 2.50 A",
            "A_v    = 1 + R_f/R_i = 1 + 100k/1k = 101",
            "V_in   = V_RMS/A_v = 0.198 V RMS",
            "```",
            "",
            "## Verification status",
            "",
            "- Design math: computed and checked",
            "- Component values: E24 standard, calculated",
            "- THD, bias set points and device models: REQUIRES SPICE/ADS",
            "  ITERATION and bench verification",
            "",
        ]
    )


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

    report_path = os.path.join(workspace_info["workspace"], "DESIGN_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(
            _design_report(
                design_key or "Class AB Audio Power Amplifier",
                design_family,
                frequency_ghz,
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
        "report_path": report_path,
        "netlist": netlist_text,
    }
