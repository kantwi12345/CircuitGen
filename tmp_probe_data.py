"""Throwaway: inspect why the S-parameter report has no data."""

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

    for name in list(module.GetAllReportNames()):
        try:
            traces = list(module.GetReportTraceNames(name))
        except Exception as exc:
            traces = f"err {exc!r}"
        print(f"report {name}: traces={traces}")

    print("\n--- GetSolutionDataPerVariation ---")
    for expr in ("S(1,1)", "dB(S(1,1))", "S(LumpedPort1,LumpedPort1)"):
        try:
            data = module.GetSolutionDataPerVariation(
                "Modal Solution Data",
                "Setup1 : Sweep1",
                "Sweep",
                ["Freq:=", "All"],
                expr,
            )
            print(f"{expr}: {type(data)} {str(data)[:400]}")
        except Exception as exc:
            print(f"{expr}: FAIL {exc!r}")
            print("   ", hfss_sim.last_error(desktop))
finally:
    pythoncom.CoUninitialize()
