"""Throwaway: get the S-parameter report + export working."""

import os
import shutil

import pythoncom
import win32com.client

from tools import hfss_sim

OUT = r"C:\CircuitGen\tmp_results_probe"

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
                target = design

    if target is None:
        print("no solved design")
        raise SystemExit(1)

    design = target
    module = design.GetModule("ReportSetup")

    print("existing reports:", list(module.GetAllReportNames()))
    print("available solutions:", list(module.GetAvailableSolutions("Modal Solution Data")))

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)

    for expression in ("S(1,1)", "dB(S(1,1))", "S(LumpedPort1,LumpedPort1)"):
        name = "Probe_" + expression.replace("(", "_").replace(")", "_").replace(",", "-")
        try:
            module.DeleteReports([name])
        except Exception:
            pass

        try:
            hfss_sim.create_report(design, name, expression, "Setup1 : Sweep1")
            print(f"\n{name}: created; reports now {list(module.GetAllReportNames())}")
        except Exception as exc:
            print(f"\n{name}: create failed {exc!r}")
            print("   ", hfss_sim.last_error(desktop))
            continue

        path = os.path.join(OUT, name + ".tab")
        for args in ((name, path), (name, path, False), (name, path, False, "")):
            try:
                module.ExportToFile(*args)
                print(f"   ExportToFile{len(args)} -> exists={os.path.exists(path)}")
                if os.path.exists(path):
                    print("   head:", open(path).read()[:300].replace("\n", " | "))
                break
            except Exception as exc:
                print(f"   ExportToFile{len(args)} failed {exc!r}")
finally:
    pythoncom.CoUninitialize()
