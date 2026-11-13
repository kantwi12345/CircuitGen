"""Throwaway: find the working call shape for reading sweep data."""

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

    result = module.GetSolutionDataPerVariation(
        "Modal Solution Data", "Setup1 : Sweep1", "Sweep", ["Freq:=", "All"], "S(1,1)",
    )
    data = result[0] if isinstance(result, (list, tuple)) else result

    expressions = [str(e) for e in data.GetDataExpressions()]
    sweeps = [str(s) for s in data.GetSweepNames()]
    print("expressions:", expressions)
    print("sweeps:", sweeps)

    for si in (False, True):
        try:
            values = list(data.GetSweepValues(sweeps[0], si))
            print(f"sweep values (si={si}): n={len(values)} {values[:3]}")
        except Exception as exc:
            print(f"sweep values (si={si}) failed: {exc!r}")

    for expression in expressions:
        for shape in ("list", "string"):
            for si in (False, True):
                arg = [expression] if shape == "list" else expression
                try:
                    values = list(data.GetRealDataValues(arg, si))
                    print(f"real {shape} si={si}: n={len(values)} {str(values)[:120]}")
                except Exception as exc:
                    code = exc.args[2][4] if exc.args[2] else exc
                    print(f"real {shape} si={si}: FAIL {code}")

    for expression in expressions:
        try:
            values = list(data.GetImagDataValues([expression], False))
            print(f"imag list: n={len(values)} {str(values)[:120]}")
        except Exception as exc:
            code = exc.args[2][4] if exc.args[2] else exc
            print(f"imag list: FAIL {code}")

    try:
        values = list(data.GetPerQuantityPrimarySweepValues(expressions, False))
        print("per quantity:", len(values), str(values)[:200])
    except Exception as exc:
        print("per quantity failed:", repr(exc))

    try:
        print("units:", list(data.GetDataUnits(expressions)))
        print("complex:", list(data.IsDataComplex(expressions)))
    except Exception as exc:
        print("units/complex failed:", repr(exc))

    # alternative: the solutions module may expose the data directly
    solutions = design.GetModule("Solutions")
    for method, args in (
        ("GetNetworkDataSolution", ("Setup1 : LastAdaptive",)),
    ):
        try:
            out = getattr(solutions, method)(*args)
            print(f"{method}: {str(out)[:300]}")
        except Exception as exc:
            print(f"{method}: FAIL {repr(exc)}")
finally:
    pythoncom.CoUninitialize()
