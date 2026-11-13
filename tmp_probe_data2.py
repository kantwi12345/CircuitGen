"""Throwaway: find a working way to get the S-parameter numbers out."""

import os

import pythoncom
import win32com.client

from tools import hfss_sim

OUT = r"C:\CircuitGen\tmp_results_probe2"

pythoncom.CoInitialize()
try:
    app = win32com.client.Dispatch("Ansoft.ElectronicsDesktop")
    desktop = app.GetAppDesktop()

    design = None
    for project in desktop.GetProjects():
        try:
            designs = project.GetDesigns()
        except Exception:
            continue
        for candidate in designs:
            try:
                if candidate.GetName() != "MonopoleAntenna":
                    continue
                solutions = list(
                    candidate.GetModule("Solutions").GetValidISolutionList(True)
                )
            except Exception:
                continue
            if "Setup1 : Sweep1" in solutions:
                design = candidate

    if design is None:
        print("no solved design")
        raise SystemExit(1)

    module = design.GetModule("ReportSetup")
    os.makedirs(OUT, exist_ok=True)

    name = "CircuitGen_S11"

    # 1. five argument export
    path = os.path.join(OUT, "five.tab")
    try:
        module.ExportToFile(name, path, False, "", False)
        print("5-arg export exists:", os.path.exists(path))
    except Exception as exc:
        print("5-arg export failed:", repr(exc))

    # 2. rdat export
    path = os.path.join(OUT, "data.rdat")
    try:
        module.ExportReportDataToFile(name, path)
        print("rdat export exists:", os.path.exists(path))
        if os.path.exists(path):
            print(open(path).read()[:400])
    except Exception as exc:
        print("rdat export failed:", repr(exc))

    # 3. inspect the solution data object
    print("\n--- solution data object ---")
    data = module.GetSolutionDataPerVariation(
        "Modal Solution Data", "Setup1 : Sweep1", "Sweep", ["Freq:=", "All"], "S(1,1)",
    )[0]

    ti = data._oleobj_.GetTypeInfo(0)
    attr = ti.GetTypeAttr()
    for i in range(attr[6]):
        fd = ti.GetFuncDesc(i)
        names = ti.GetNames(fd[0])
        print("  ", names[0], names[1:])

    # 4. try reading the numbers directly
    for method in ("GetRealDataValues", "GetRealDataValues1", "GetPrimarySweepValues"):
        try:
            if method == "GetRealDataValues":
                values = data.GetRealDataValues(["S(1,1)"], True)
            elif method == "GetRealDataValues1":
                values = data.GetRealDataValues1(["S(1,1)"], True)
            else:
                values = data.GetPrimarySweepValues()
            print(f"{method}: {type(values)} {str(values)[:300]}")
        except Exception as exc:
            print(f"{method}: FAIL {exc!r}")
finally:
    pythoncom.CoUninitialize()
