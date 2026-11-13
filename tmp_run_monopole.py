"""Throwaway end-to-end check of the HFSS simulation stack (monopole)."""

import json
import os
import shutil
import time

import pythoncom
import win32com.client

from tools import hfss_sim
from tools.hfss_com import create_monopole_antenna

RESULTS = r"C:\CircuitGen\tmp_results_monopole"

pythoncom.CoInitialize()
try:
    print("building monopole ...")
    result = create_monopole_antenna(frequency_ghz=2.4)
    print("build result keys:", sorted(result.keys()))

    # the builder calls CoUninitialize() on the way out - re-arm COM
    pythoncom.CoInitialize()

    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()
    project, design = hfss_sim.find_design("MonopoleAntenna", desktop)
    print("found project:", project.GetName())

    print("\nassigning port ...")
    port = hfss_sim.assign_lumped_port(design, name="LumpedPort1")
    print("port:", port)
    print("excitations:", list(design.GetModule("BoundarySetup").GetExcitations()))

    print("\ncreating setup ...")
    setup = hfss_sim.create_driven_setup(design, "Setup1", frequency_ghz=2.4)
    print("setup:", setup)

    print("\ncreating sweep ...")
    sweep = hfss_sim.create_frequency_sweep(
        design, "Setup1", "Sweep1", start_ghz=2.2, stop_ghz=2.6, count=41
    )
    print("sweep:", sweep)

    if os.path.isdir(RESULTS):
        shutil.rmtree(RESULTS)

    print("\nsolving (this takes a while) ...")
    start = time.time()
    try:
        solve = hfss_sim.solve_setup(design, "Setup1")
        print("solved in %.1f s" % (time.time() - start), solve)
    except Exception as exc:
        print("solve failed:", repr(exc))
        print("AEDT says:", hfss_sim.last_error(desktop))
        raise

    print("\nextracting S11 ...")
    data = hfss_sim.extract_s_parameters(
        design, "Setup1 : Sweep1", RESULTS, port_count=1
    )
    label = data["S11"]
    print("traces:", list(label["traces"].keys()))
    freqs = label["frequencies_hz"]
    values = list(label["traces"].values())[0] if label["traces"] else []
    print("n points:", len(freqs))
    for f, v in list(zip(freqs, values))[:6]:
        print("   %.4f GHz  %.2f dB" % (f / 1e9, v))
    if freqs:
        print("   ...")
        for f, v in list(zip(freqs, values))[-6:]:
            print("   %.4f GHz  %.2f dB" % (f / 1e9, v))

    print("\nsummary:", hfss_sim.summarise_s_parameters(data, 2.4e9))
    print("resonance:", hfss_sim.resonant_frequency(data, "S11"))

    try:
        print("antenna params:",
              hfss_sim.extract_antenna_parameters(design, "Setup1"))
    except Exception as exc:
        print("antenna params failed:", repr(exc))
finally:
    pythoncom.CoUninitialize()
