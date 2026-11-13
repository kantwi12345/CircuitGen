"""Throwaway: reopen the saved project, solve and extract."""

import os
import time

import pythoncom
import win32com.client

from tools import hfss_sim

SAVE = r"C:\CircuitGen\tmp_saved\hfss_monopole.aedt"
RESULTS = r"C:\CircuitGen\tmp_results_monopole"

pythoncom.CoInitialize()
try:
    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()

    print("opening", SAVE)
    project = hfss_sim.open_project(SAVE, desktop)
    design = project.SetActiveDesign("MonopoleAntenna")
    print("opened:", project.GetName(), design.GetName())

    module = design.GetModule("AnalysisSetup")
    print("setups:", list(module.GetSetups() or []))
    print("excitations:", list(design.GetModule("BoundarySetup").GetExcitations()))

    if "Setup1" not in list(module.GetSetups() or []):
        hfss_sim.create_driven_setup(design, "Setup1", frequency_ghz=2.4)
        hfss_sim.create_frequency_sweep(
            design, "Setup1", "Sweep1", start_ghz=2.3, stop_ghz=2.5, count=21
        )
        print("setup + sweep created")

    print("solving ...")
    start = time.time()
    solve = hfss_sim.solve_setup(design, "Setup1")
    print("solved in %.1f s" % (time.time() - start), solve)

    print("\nreading solution data ...")
    data = hfss_sim.read_solution_data(design, "S(1,1)", "Setup1 : Sweep1")
    print("expression:", data["expression"])
    freqs = data["frequencies_hz"]
    values = data["values"]
    print("points:", len(freqs), len(values))
    for f, v in list(zip(freqs, values)):
        print("   %.4f GHz  %.4f" % (f / 1e9, v))

    db = hfss_sim.read_solution_data(design, "dB(S(1,1))", "Setup1 : Sweep1")
    print("\ndB(S11):")
    for f, v in list(zip(db["frequencies_hz"], db["values"])):
        print("   %.4f GHz  %.2f dB" % (f / 1e9, v))

    full = hfss_sim.extract_s_parameters(
        design, "Setup1 : Sweep1", RESULTS, port_count=1
    )
    print("\nsummary:", hfss_sim.summarise_s_parameters(full, 2.4e9))
    print("resonance:", hfss_sim.resonant_frequency(full, "S11"))
finally:
    pythoncom.CoUninitialize()
