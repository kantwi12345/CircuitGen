"""Throwaway: read the solution data object directly."""

import os

import pythoncom
import win32com.client

from tools import hfss_sim

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

    data = module.GetSolutionDataPerVariation(
        "Modal Solution Data", "Setup1 : Sweep1", "Sweep", ["Freq:=", "All"], "S(1,1)",
    )[0]

    print("sweep names:", list(data.GetSweepNames()))
    expressions = list(data.GetDataExpressions())
    print("data expressions:", expressions)

    for expression in expressions:
        try:
            print("units:", list(data.GetDataUnits([expression])))
        except Exception as exc:
            print("units failed:", repr(exc))
        try:
            print("complex:", list(data.IsDataComplex([expression])))
        except Exception as exc:
            print("complex failed:", repr(exc))

    for si in (True, False):
        try:
            values = list(data.GetRealDataValues(expressions, si))
            print(f"real(si={si}): n={len(values)} first={values[:3]}")
        except Exception as exc:
            print(f"real(si={si}): FAIL {exc!r}")

    for si in (True, False):
        try:
            values = list(data.GetRealDataValues([expressions[0]], si))
            print(f"real single(si={si}): n={len(values)} first={values[:3]}")
        except Exception as exc:
            print(f"real single(si={si}): FAIL {exc!r}")

    try:
        sweeps = list(data.GetSweepValues(data.GetSweepNames()[0], False))
        print("sweep values:", len(sweeps), sweeps[:3])
    except Exception as exc:
        print("sweep values failed:", repr(exc))

    try:
        per = list(data.GetPerQuantityPrimarySweepValues(expressions, False))
        print("per quantity sweep:", len(per), str(per)[:200])
    except Exception as exc:
        print("per quantity failed:", repr(exc))
finally:
    pythoncom.CoUninitialize()
