"""Throwaway: full pipeline run - build, excite, setup, sweep, solve, extract."""

import os
import time

import pythoncom
import win32com.client

from tools import hfss_sim
from tools.hfss_com import create_monopole_antenna

SAVE = r"C:\CircuitGen\tmp_saved\hfss_monopole.aedt"
RESULTS = r"C:\CircuitGen\tmp_results_monopole"

pythoncom.CoInitialize()
try:
    print("building monopole ...")
    create_monopole_antenna(frequency_ghz=2.4)
    pythoncom.CoInitialize()

    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()
    project, design = hfss_sim.find_design("MonopoleAntenna", desktop)
    print("project:", project.GetName())

    port = hfss_sim.assign_lumped_port(design, name="LumpedPort1")
    print("port:", port)

    hfss_sim.create_driven_setup(design, "Setup1", frequency_ghz=2.4)
    hfss_sim.create_frequency_sweep(
        design, "Setup1", "Sweep1", start_ghz=2.3, stop_ghz=2.5, count=21
    )
    print("setup + sweep created")

    os.makedirs(os.path.dirname(SAVE), exist_ok=True)
    try:
        project.SaveAs(SAVE, True)
        print("saved before solve:", SAVE)
    except Exception as exc:
        print("save failed:", repr(exc))

    print("solving ...")
    start = time.time()
    solve = hfss_sim.solve_setup(design, "Setup1")
    print("solved in %.1f s" % (time.time() - start), solve)

    try:
        project.SaveAs(SAVE, True)
        print("saved after solve")
    except Exception as exc:
        print("save after solve failed:", repr(exc))

    print("\nreading solution data ...")
    data = hfss_sim.read_solution_data(design, "S(1,1)", "Setup1 : Sweep1")
    print("expression:", data["expression"], "units:", data["units"])
    freqs = data["frequencies_hz"]
    values = data["values"]
    print("points:", len(freqs), len(values))
    for f, v in list(zip(freqs, values))[:6]:
        print("   %.4f GHz  %.4f" % (f / 1e9, v))
    if freqs:
        print("   ...")
        for f, v in list(zip(freqs, values))[-6:]:
            print("   %.4f GHz  %.4f" % (f / 1e9, v))
        print("min at %.4f GHz" % (freqs[values.index(min(values))] / 1e9))

    print("\ndB trace ...")
    db = hfss_sim.read_solution_data(design, "dB(S(1,1))", "Setup1 : Sweep1")
    for f, v in list(zip(db["frequencies_hz"], db["values"]))[:6]:
        print("   %.4f GHz  %.2f dB" % (f / 1e9, v))

    print("\nfull extraction ...")
    full = hfss_sim.extract_s_parameters(
        design, "Setup1 : Sweep1", RESULTS, port_count=1
    )
    print("labels:", list(full.keys()))
    print("summary:", hfss_sim.summarise_s_parameters(full, 2.4e9))
    print("resonance:", hfss_sim.resonant_frequency(full, "S11"))

    try:
        print("antenna params:",
              hfss_sim.extract_antenna_parameters(design, "Setup1"))
    except Exception as exc:
        print("antenna params failed:", repr(exc))
finally:
    pythoncom.CoUninitialize()
