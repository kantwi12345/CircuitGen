"""Throwaway: extract S11 from an already solved monopole design."""

import os
import shutil

import pythoncom
import win32com.client

from tools import hfss_sim

RESULTS = r"C:\CircuitGen\tmp_results_monopole"

pythoncom.CoInitialize()
try:
    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()

    target = None
    for project in desktop.GetProjects():
        try:
            designs = project.GetDesigns()
        except Exception:
            continue
        for design in designs:
            try:
                if design.GetName() != "MonopoleAntenna":
                    continue
                solutions = list(
                    design.GetModule("Solutions").GetValidISolutionList(True)
                )
            except Exception:
                continue
            if "Setup1 : Sweep1" in solutions:
                target = (project, design)
                print("using", project.GetName(), solutions)

    if target is None:
        print("no solved monopole found")
    else:
        project, design = target

        if os.path.isdir(RESULTS):
            shutil.rmtree(RESULTS)

        data = hfss_sim.extract_s_parameters(
            design, "Setup1 : Sweep1", RESULTS, port_count=1
        )

        label = data["S11"]
        print("traces:", list(label["traces"].keys()))
        freqs = label["frequencies_hz"]
        values = list(label["traces"].values())[0] if label["traces"] else []
        print("n points:", len(freqs))
        for f, v in list(zip(freqs, values))[:8]:
            print("   %.4f GHz  %.2f dB" % (f / 1e9, v))
        if freqs:
            print("   ...")
            for f, v in list(zip(freqs, values))[-8:]:
                print("   %.4f GHz  %.2f dB" % (f / 1e9, v))

        print("summary:", hfss_sim.summarise_s_parameters(data, 2.4e9))
        print("resonance:", hfss_sim.resonant_frequency(data, "S11"))

        try:
            print("antenna params:",
                  hfss_sim.extract_antenna_parameters(design, "Setup1"))
        except Exception as exc:
            print("antenna params failed:", repr(exc))
finally:
    pythoncom.CoUninitialize()
